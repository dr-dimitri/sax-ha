"""Read the public pv_forecast window contract for REQ-BRIDGE-CHARGE."""

from __future__ import annotations

import asyncio
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from itertools import pairwise
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

_STEP = timedelta(minutes=15)
_REFRESH_INTERVAL = timedelta(seconds=60)
_RETRY_INTERVAL = timedelta(seconds=10)
_MAX_RESPONSE_AGE = timedelta(seconds=60)
# REQ-BRIDGE-CHARGE: an accepted result must span the next refresh, its
# service timeout and polling jitter even if as_of was already 60 seconds old.
_CACHE_LIFETIME = timedelta(seconds=75)
_MAX_CACHED_RESPONSE_AGE = _MAX_RESPONSE_AGE + _CACHE_LIFETIME
_MAX_FORECAST_AGE = timedelta(minutes=60)
_SERVICE_TIMEOUT = 2


def _timestamp(value: object) -> datetime | None:
    try:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if not isinstance(value, datetime) or value.utcoffset() is None:
            return None
        return value.astimezone(UTC)
    except OverflowError, ValueError:
        return None


def _number(value: object) -> bool:
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _quarter(value: datetime) -> datetime:
    return value.replace(minute=value.minute // 15 * 15, second=0, microsecond=0)


@dataclass(frozen=True, slots=True)
class _Snapshot:
    as_of: datetime
    fetched_at: datetime
    accepted_at: datetime
    intervals: tuple[tuple[datetime, datetime, float], ...]


def _parse_snapshot(
    response: object,
    *,
    now: datetime,
    start: datetime,
    end: datetime,
    timezone: str,
) -> _Snapshot | None:
    if (
        not isinstance(response, Mapping)
        or type(response.get("schema_version")) is not int
        or response.get("schema_version") != 1
        or response.get("last_update_success") is not True
        or response.get("origin") != "live"
    ):
        return None
    window = response.get("window")
    if (
        not isinstance(window, Mapping)
        or type(window.get("schema_version")) is not int
        or window.get("schema_version") != 1
        or window.get("scope") != "total"
        or window.get("status") != "available"
        or window.get("reason") is not None
        or window.get("timezone") != timezone
        or window.get("quality_flags") != []
        or window.get("step_minutes") != 15
        or window.get("assumption") != "constant_interval_mean_power"
        or _timestamp(window.get("start")) != start
        or _timestamp(window.get("end")) != end
    ):
        return None
    coverage = window.get("coverage")
    if (
        not isinstance(coverage, Mapping)
        or coverage.get("complete") is not True
        or _timestamp(coverage.get("start")) != start
        or _timestamp(coverage.get("end")) != end
    ):
        return None
    as_of = _timestamp(window.get("as_of"))
    fetched_at = _timestamp(window.get("fetched_at"))
    if (
        as_of is None
        or fetched_at is None
        or not timedelta(0) <= now - as_of <= _MAX_RESPONSE_AGE
        or not timedelta(0) <= now - fetched_at <= _MAX_FORECAST_AGE - _CACHE_LIFETIME
        or fetched_at > as_of
    ):
        return None
    rows = window.get("intervals")
    if not isinstance(rows, list) or len(rows) != (end - start) // _STEP:
        return None
    intervals: list[tuple[datetime, datetime, float]] = []
    energies: list[float] = []
    cursor = start
    for row in rows:
        if not isinstance(row, Mapping):
            return None
        left, right = _timestamp(row.get("start")), _timestamp(row.get("end"))
        power, energy = row.get("mean_ac_power_kw"), row.get("energy_kwh")
        if (
            left != cursor
            or right is None
            or right - cursor != _STEP
            or not _number(power)
            or not _number(power * 1000)
            or not _number(energy)
            or not math.isclose(energy, power / 4, rel_tol=1e-12, abs_tol=1e-9)
        ):
            return None
        intervals.append((cursor, right, float(power) * 1000))
        energies.append(float(energy))
        cursor = right
    total = window.get("energy_kwh")
    mean = window.get("mean_ac_power_kw")
    if (
        cursor != end
        or not _number(total)
        or not _number(mean)
        or not math.isclose(math.fsum(energies), total, rel_tol=1e-12, abs_tol=1e-9)
        or not math.isclose(
            total,
            mean * (end - start).total_seconds() / 3600,
            rel_tol=1e-12,
            abs_tol=1e-9,
        )
    ):
        return None
    return _Snapshot(as_of, fetched_at, now, tuple(intervals))


class PvBridgeForecast:
    """Resolve the chosen energy sensor to its PV plant and cache safe windows."""

    def __init__(
        self, hass: HomeAssistant, source_entity_id: Callable[[], str | None]
    ) -> None:
        self._hass = hass
        self._source_entity_id = source_entity_id
        self._source: tuple[str, str, str] | None = None
        self._last_attempt: datetime | None = None
        self._retry_pending = False
        self._snapshot: _Snapshot | None = None
        self._lock = asyncio.Lock()

    def _current_source(self) -> tuple[str, str, str] | None:
        entity_id = self._source_entity_id()
        if not isinstance(entity_id, str) or not entity_id.startswith("sensor."):
            return None
        registered = er.async_get(self._hass).async_get(entity_id)
        if (
            registered is None
            or registered.platform != "pv_forecast"
            or registered.config_entry_id is None
            or registered.disabled_by is not None
        ):
            return None
        entry = self._hass.config_entries.async_get_entry(registered.config_entry_id)
        if (
            entry is None
            or entry.domain != "pv_forecast"
            or entry.state is not ConfigEntryState.LOADED
        ):
            return None
        timezone = entry.data.get("time_zone")
        if not isinstance(timezone, str):
            return None
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError, ValueError:
            return None
        return entity_id, entry.entry_id, timezone

    def _sync_source(self) -> tuple[str, str, str] | None:
        source = self._current_source()
        if source != self._source:
            self._source = source
            self._last_attempt = None
            self._retry_pending = False
            self._snapshot = None
        return source

    async def async_refresh(self, now: datetime | None = None) -> None:
        """Refresh once a minute, retry failures sooner, and expire cached results."""
        async with self._lock:
            instant = _timestamp(now if now is not None else dt_util.utcnow())
            if instant is None:
                self._snapshot = None
                return
            source = self._sync_source()
            if source is None or not self._hass.services.has_service(
                "pv_forecast", "get_forecast"
            ):
                self._snapshot = None
                self._last_attempt = None
                return
            refresh_interval = (
                _RETRY_INTERVAL if self._retry_pending else _REFRESH_INTERVAL
            )
            if (
                self._last_attempt is not None
                and timedelta(0) <= instant - self._last_attempt < refresh_interval
            ):
                return
            self._last_attempt = instant
            self._retry_pending = True
            # #130 anchors its raster to the supplied start. Whole future
            # quarters avoid presenting an already elapsed interval as PV start.
            start = _quarter(instant)
            if start < instant:
                start += _STEP
            zone = ZoneInfo(source[2])
            try:
                available_end = datetime.combine(
                    instant.astimezone(zone).date() + timedelta(days=2),
                    dt_time(),
                    zone,
                ).astimezone(UTC)
                end = _quarter(min(instant + timedelta(hours=26), available_end))
                if end - start < 2 * _STEP:
                    self._snapshot = None
                    return
                async with asyncio.timeout(_SERVICE_TIMEOUT):
                    response = await self._hass.services.async_call(
                        "pv_forecast",
                        "get_forecast",
                        {
                            "config_entry_id": source[1],
                            "window": {
                                "start": start.isoformat(),
                                "end": end.isoformat(),
                                "step_minutes": 15,
                            },
                        },
                        blocking=True,
                        return_response=True,
                    )
                if self._sync_source() == source:
                    self._snapshot = _parse_snapshot(
                        response,
                        now=instant if now is not None else dt_util.utcnow(),
                        start=start,
                        end=end,
                        timezone=source[2],
                    )
                    if self._snapshot is not None:
                        self._last_attempt = self._snapshot.accepted_at
                        self._retry_pending = False
            except HomeAssistantError, TimeoutError:
                # REQ-BRIDGE-CHARGE: a transient read failure cannot extend the
                # accepted snapshot's deadline or hide a source change.
                self._sync_source()
            except OverflowError, TypeError, ValueError:
                self._snapshot = None

    def pv_start(
        self, now: datetime, average_discharge_w: float | None
    ) -> datetime | None:
        """Find two adjacent future quarters whose PV means cover measured demand."""
        self._sync_source()
        instant = _timestamp(now)
        snapshot = self._snapshot
        if (
            instant is None
            or snapshot is None
            or not self._hass.services.has_service("pv_forecast", "get_forecast")
            or not _number(average_discharge_w)
            or average_discharge_w <= 0
            or not timedelta(0) <= instant - snapshot.accepted_at <= _CACHE_LIFETIME
            or not timedelta(0) <= instant - snapshot.as_of <= _MAX_CACHED_RESPONSE_AGE
            or not timedelta(0) <= instant - snapshot.fetched_at <= _MAX_FORECAST_AGE
        ):
            return None
        for first, second in pairwise(snapshot.intervals):
            if (
                first[0] >= instant
                and first[2] >= average_discharge_w
                and second[2] >= average_discharge_w
            ):
                return first[0]
        return None
