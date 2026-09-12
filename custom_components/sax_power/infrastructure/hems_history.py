"""Bounded SAX observations and Recorder boundary for HEMS night profiles."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.recorder import DATA_INSTANCE
from homeassistant.helpers.storage import Store
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util import dt as dt_util

from ..const import DOMAIN
from ..domain.hems import EnergySlot, LoadForecast
from ..domain.hems_load import (
    DAWN_DURATION,
    DischargeObservation,
    LoadVariants,
    NightSpan,
    ObservationQuality,
    aware,
    build_night_profile,
    build_weighted_profile,
    finite_number,
    forecast_night_load,
    forecast_weighted_load,
    validate_history_days,
)

_LOGGER = logging.getLogger(__name__)
_MAX_RECORDS = 14000
_SAVE_DELAY = 300
_RECORDER_TIMEOUT = 10


class _HistoryStore(Store[dict[str, Any]]):
    """Preserve the existing interval quality across the history extension."""

    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict[str, Any]
    ) -> dict[str, Any]:
        if old_major_version != 1:
            raise NotImplementedError
        return {**old_data, "history_days": 7}


@dataclass(frozen=True, slots=True)
class _Sample:
    at: datetime
    power_w: float
    quality: ObservationQuality


class HemsHistory:
    """Collect quality independently of charging decisions and profile refreshes.

    REQ-HEMS-LOAD-PROFILE: Existing Recorder energy alone cannot prove free
    discharge. Persist the simultaneous SAX quality evidence; old unproven
    energy remains a cold start, never a fictional seven-day history.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        *,
        max_sample_gap_seconds: float = 30.0,
        history_days: int = 7,
    ) -> None:
        if (
            not finite_number(max_sample_gap_seconds)
            or not 0 < max_sample_gap_seconds <= 300
        ):
            raise ValueError("Invalid maximum sample gap")
        self.hass = hass
        self.entry_id = entry_id
        self.max_sample_gap_seconds = max_sample_gap_seconds
        self.history_days = validate_history_days(history_days)
        self.variants: LoadVariants | None = None
        self._store: Store[dict[str, Any]] = _HistoryStore(
            hass, 2, f"{DOMAIN}.hems_history.{entry_id}"
        )
        self._records: list[DischargeObservation] = []
        self._previous: _Sample | None = None
        self._evaluated_through: datetime | None = None
        self._started = False
        self._stopped = False
        self._save_scheduled = False
        self._generation = 0
        self._refresh_task: asyncio.Task[LoadForecast] | None = None
        self._recorder_read_through: datetime | None = None
        self._recorder_entity: str | None = None
        self._recorder_rows: dict[tuple[datetime, datetime], float] = {}

    @property
    def history_window(self) -> timedelta:
        return timedelta(days=self.history_days)

    @callback
    def configure(self, *, history_days: int = 7) -> None:
        """Changing the selection cannot reuse an in-flight profile or old key."""
        validate_history_days(history_days)
        if history_days == self.history_days:
            return
        self.history_days = history_days
        self._generation += 1
        self.variants = None
        self._recorder_read_through = None
        self._prune(dt_util.utcnow())

    def observations(
        self, as_of: datetime, *, lookback: timedelta | None = None
    ) -> tuple[DischargeObservation, ...]:
        """Expose bounded quality evidence without including measurements after now."""
        if not aware(as_of):
            raise ValueError("as_of must be timezone-aware")
        span = self.history_window if lookback is None else lookback
        if span <= timedelta():
            raise ValueError("lookback must be positive")
        as_of = as_of.astimezone(UTC)
        start = as_of - min(span, self.history_window)
        result = []
        for item in self._effective_observations():
            if item.end > as_of or item.end <= start:
                continue
            begin = max(start, item.start)
            fraction = (item.end - begin) / (item.end - item.start)
            result.append(
                DischargeObservation(
                    begin, item.end, item.energy_kwh * fraction, item.quality
                )
            )
        return tuple(result)

    def free_discharge(self, as_of: datetime) -> bool:
        """Use the same live quality proof as training, with the sample gap limit."""
        sample = self._previous
        return bool(
            self._started
            and not self._stopped
            and sample is not None
            and sample.quality == "valid"
            and aware(as_of)
            and 0
            <= (as_of.astimezone(UTC) - sample.at).total_seconds()
            <= self.max_sample_gap_seconds
        )

    async def async_start(self) -> None:
        """Restore bounded quality without integrating across a restart."""
        if self._started or self._stopped:
            return
        generation = self._generation
        try:
            raw = await self._store.async_load()
        except Exception:
            _LOGGER.exception("HEMS-Beobachtungshistorie konnte nicht geladen werden")
            raw = None
        if generation != self._generation or self._stopped:
            return
        self._records = self._decode(raw)
        self._previous = None
        self._started = True
        self._prune(dt_util.utcnow())

    async def async_stop(self) -> None:
        """Invalidate in-flight responses and persist the last proven intervals."""
        if self._stopped:
            return
        self._stopped = True
        self._generation += 1
        task = self._refresh_task
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        if self._started:
            try:
                await self._store.async_save(self._serialize())
            except Exception:
                _LOGGER.exception(
                    "HEMS-Beobachtungshistorie konnte nicht gesichert werden"
                )
        self._previous = None

    @callback
    def observe(
        self,
        at: datetime,
        *,
        storage_power_w: float | None,
        soc: float | None,
        device_min_soc: float | None,
        device_available: bool,
        control_known: bool,
        charge_active: bool,
        discharge_blocked: bool,
        calibration_active: bool,
        energy_discharged_kwh: float | None = None,
        max_discharge_power_w: float | None = None,
    ) -> None:
        """Accept one newly measured SAX sample, never a repeated cached poll."""
        if not self._started or self._stopped or not aware(at):
            return
        at = at.astimezone(UTC)
        if self._evaluated_through is not None and at <= self._evaluated_through:
            return
        quality = self._quality(
            storage_power_w,
            soc,
            device_min_soc,
            device_available,
            control_known,
            charge_active,
            discharge_blocked,
            calibration_active,
        )
        power = float(storage_power_w) if finite_number(storage_power_w) else 0.0
        if max_discharge_power_w is not None and (
            not finite_number(max_discharge_power_w)
            or max_discharge_power_w <= 0
            or power > max_discharge_power_w * 1.1
        ):
            quality = "unknown"
        sample = _Sample(at, power, quality)
        previous = self._previous
        if previous is not None:
            elapsed = (at - previous.at).total_seconds()
            interval_quality = quality
            if elapsed > self.max_sample_gap_seconds or "unknown" in (
                previous.quality,
                quality,
            ):
                interval_quality = "unknown"
            elif "censored" in (previous.quality, quality):
                interval_quality = "censored"
            energy = (
                max(previous.power_w, 0.0) * elapsed / 3600000
                if interval_quality == "valid"
                else 0.0
            )
            if not finite_number(energy):
                energy, interval_quality = 0.0, "unknown"
            self._append(
                DischargeObservation(
                    max(previous.at, at - self.history_window),
                    at,
                    energy,
                    interval_quality,
                )
            )
        self._previous = sample
        self._evaluated_through = at
        self._prune(at)
        if not self._save_scheduled:
            self._save_scheduled = True
            self._store.async_delay_save(self._serialize, _SAVE_DELAY)

    @staticmethod
    def _quality(
        power: float | None,
        soc: float | None,
        device_min_soc: float | None,
        available: bool,
        known: bool,
        charging: bool,
        blocked: bool,
        calibration: bool,
    ) -> ObservationQuality:
        if (
            any(
                type(flag) is not bool
                for flag in (available, known, charging, blocked, calibration)
            )
            or not available
            or not known
            or not finite_number(power)
            or not finite_number(soc)
            or not finite_number(device_min_soc)
        ):
            return "unknown"
        assert soc is not None and device_min_soc is not None and power is not None
        if not 0 <= soc <= 100 or not 0 <= device_min_soc < 100:
            return "unknown"
        if soc <= device_min_soc or charging or blocked or calibration or power < 0:
            return "censored"
        return "valid"

    def _append(self, item: DischargeObservation) -> None:
        cursor = item.start
        duration = (item.end - item.start).total_seconds()
        while cursor < item.end:
            boundary = datetime.fromtimestamp(
                (int(cursor.timestamp()) // 300 + 1) * 300, UTC
            )
            stop = min(boundary, item.end)
            self._append_piece(
                DischargeObservation(
                    cursor,
                    stop,
                    item.energy_kwh * (stop - cursor).total_seconds() / duration,
                    item.quality,
                )
            )
            cursor = stop

    def _append_piece(self, item: DischargeObservation) -> None:
        if self._records:
            last = self._records[-1]
            if (
                last.end == item.start
                and last.quality == item.quality
                and int(last.start.timestamp()) // 300
                == int(item.end.timestamp() - 1e-6) // 300
            ):
                self._records[-1] = DischargeObservation(
                    last.start,
                    item.end,
                    last.energy_kwh + item.energy_kwh,
                    item.quality,
                )
                return
        self._records.append(item)

    def _prune(self, as_of: datetime) -> None:
        cutoff = as_of - self.history_window
        self._records = [item for item in self._records if cutoff < item.end <= as_of][
            -(_MAX_RECORDS * self.history_days // 7) :
        ]
        self._recorder_rows = {
            key: value for key, value in self._recorder_rows.items() if key[1] > cutoff
        }

    def _serialize(self) -> dict[str, Any]:
        self._save_scheduled = False
        return {
            "entry_id": self.entry_id,
            "history_days": self.history_days,
            "intervals": [
                [
                    item.start.isoformat(),
                    item.end.isoformat(),
                    item.energy_kwh,
                    item.quality,
                ]
                for item in self._records
            ],
        }

    def _decode(self, raw: Any) -> list[DischargeObservation]:
        if not isinstance(raw, dict) or raw.get("entry_id") != self.entry_id:
            return []
        rows = raw.get("intervals")
        if not isinstance(rows, list) or len(rows) > _MAX_RECORDS * 4:
            return []
        result: list[DischargeObservation] = []
        for row in rows:
            try:
                if not isinstance(row, list) or len(row) != 4:
                    return []
                start, end = datetime.fromisoformat(row[0]), datetime.fromisoformat(
                    row[1]
                )
                if (
                    not aware(start)
                    or not aware(end)
                    or end <= start
                    or not finite_number(row[2])
                    or row[2] < 0
                    or row[3] not in ("valid", "censored", "unknown")
                ):
                    return []
                start, end = start.astimezone(UTC), end.astimezone(UTC)
                if result and start < result[-1].end:
                    return []
                result.append(DischargeObservation(start, end, float(row[2]), row[3]))
            except ValueError, TypeError, OverflowError:
                return []
        return result

    async def async_refresh(self, as_of: datetime) -> LoadForecast:
        """Coalesce refreshes; the caller owns the common five-minute timer."""
        if self._refresh_task is not None and not self._refresh_task.done():
            return await asyncio.shield(self._refresh_task)
        self._refresh_task = self.hass.async_create_task(
            self._async_refresh(as_of), "sax_power_hems_history"
        )
        return await asyncio.shield(self._refresh_task)

    async def _async_refresh(self, as_of: datetime) -> LoadForecast:
        generation = self._generation
        history_days = self.history_days
        observations = tuple(item for item in self._records if item.end <= as_of)
        evaluated_through = self._evaluated_through
        if self._stopped:
            return self._unavailable(as_of, "history_unavailable")
        await self._async_read_recorder(as_of, generation)
        if self._stopped or generation != self._generation:
            return LoadForecast(
                generated_at=as_of, quality_reason="history_unavailable"
            )
        try:
            zone = ZoneInfo(self.hass.config.time_zone)
            nights = self._night_spans(as_of, zone)
        except ValueError, ZoneInfoNotFoundError:
            return self._unavailable(as_of, "unsupported_night_geometry")
        current = next(
            (
                night
                for night in nights
                if night.start <= as_of < night.end + DAWN_DURATION
            ),
            None,
        )
        if current is None:
            return self._unavailable(
                as_of, "outside_model_scope" if nights else "unsupported_night_geometry"
            )
        variants = await self.hass.async_add_executor_job(
            self._build_variants,
            self._effective_observations(observations),
            nights,
            current,
            as_of,
            evaluated_through,
            zone,
            history_days,
        )
        if self._stopped or generation != self._generation:
            return LoadForecast(
                generated_at=as_of, quality_reason="history_unavailable"
            )
        self.variants = variants
        return variants.baseline

    def _unavailable(self, as_of: datetime, reason: str) -> LoadForecast:
        result = LoadForecast(generated_at=as_of, quality_reason=reason)
        self.variants = LoadVariants(
            result,
            result,
            history_days=self.history_days,
            candidate_key=f"weighted-v1:{self.history_days}d",
        )
        return result

    @staticmethod
    def _build_variants(
        observations: tuple[DischargeObservation, ...],
        nights: tuple[NightSpan, ...],
        current: NightSpan,
        as_of: datetime,
        evaluated_through: datetime | None,
        zone: ZoneInfo,
        history_days: int,
    ) -> LoadVariants:
        profile = build_night_profile(
            observations,
            nights,
            as_of=as_of,
            evaluated_through=evaluated_through,
            zone=zone,
        )
        pieces = forecast_night_load(profile, current, zone=zone)
        baseline = LoadForecast(
            intervals=tuple(
                EnergySlot(item.start, item.end, item.energy_kwh, (item.method,))
                for item in pieces
            ),
            generated_at=as_of,
            evaluated_through=evaluated_through,
            quality_reason=None if profile.reason == "ok" else profile.reason,
            nights_count=profile.nights,
            observed_hours=profile.observed_hours,
            coverage=profile.coverage,
            model_start=current.start,
            model_end=current.end + DAWN_DURATION,
            quality_flags=tuple(sorted({item.method for item in pieces})),
        )
        weighted = build_weighted_profile(
            observations,
            nights,
            as_of=as_of,
            evaluated_through=evaluated_through,
            zone=zone,
            history_days=history_days,
        )
        candidate, metadata = forecast_weighted_load(weighted, current, zone=zone)
        return LoadVariants(
            baseline,
            candidate,
            current,
            candidate_key=weighted.model_key,
            history_days=history_days,
            available_history_days=weighted.available_history_days,
            candidate_metadata=metadata,
        )

    def _night_spans(self, as_of: datetime, zone: ZoneInfo) -> tuple[NightSpan, ...]:
        local_day = as_of.astimezone(zone).date()

        def event_on(event: str, day: date) -> datetime | None:
            # HA's helper returns UTC events. Match the requested local date,
            # also west of Greenwich where sunset falls on the next UTC day.
            for offset in (0, -1, 1):
                value = get_astral_event_date(
                    self.hass, event, day + timedelta(days=offset)
                )
                if value is not None and value.astimezone(zone).date() == day:
                    return value.astimezone(UTC)
            return None

        if (
            event_on("sunrise", local_day) is None
            or event_on("sunset", local_day) is None
        ):
            return ()
        nights: list[NightSpan] = []
        for offset in range(-self.history_days - 2, 2):
            day = local_day + timedelta(days=offset)
            start = event_on("sunset", day)
            end = event_on("sunrise", day + timedelta(days=1))
            if start is not None and end is not None and start < end:
                nights.append(NightSpan(start, end))
        return tuple(nights)

    def _energy_entity(self) -> str | None:
        registry = er.async_get(self.hass)
        entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{self.entry_id}_energy_discharged"
        )
        entry = registry.async_get(entity_id) if entity_id else None
        if entry is None or entry.config_entry_id != self.entry_id or entry.disabled:
            return None
        return entity_id

    async def _async_read_recorder(self, as_of: datetime, generation: int) -> None:
        recorder = self.hass.data.get(DATA_INSTANCE)
        entity = self._energy_entity()
        if entity != self._recorder_entity:
            self._recorder_entity = entity
            self._recorder_read_through = None
            self._recorder_rows.clear()
        if entity is None or recorder is None or recorder.engine is None:
            return
        start = max(
            as_of - self.history_window,
            (
                self._recorder_read_through - timedelta(minutes=15)
                if self._recorder_read_through is not None
                else as_of - self.history_window
            ),
        )
        try:
            async with asyncio.timeout(_RECORDER_TIMEOUT):
                rows = await recorder.async_add_executor_job(
                    self._read_statistics, entity, start, as_of
                )
        except Exception:
            _LOGGER.debug(
                "Recorder-Historie fehlt; verwende belegte SAX-Leistung", exc_info=True
            )
            return
        if (
            self._stopped
            or generation != self._generation
            or entity != self._energy_entity()
        ):
            return
        self._recorder_rows = {
            key: value
            for key, value in self._recorder_rows.items()
            if key[0] < start or key[1] > as_of
        }
        for row in rows:
            if not finite_number(row.get("change")) or row["change"] < 0:
                continue
            try:
                begin = datetime.fromtimestamp(row["start"], UTC)
                end = datetime.fromtimestamp(row["end"], UTC)
                if start <= begin < end <= as_of:
                    self._recorder_rows[(begin, end)] = float(row["change"])
            except ValueError, TypeError, OverflowError, KeyError:
                continue
        self._recorder_read_through = as_of
        self._prune(max(as_of, self._evaluated_through or as_of))

    def _read_statistics(
        self, entity: str, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        from homeassistant.components.recorder.statistics import (
            statistics_during_period,  # noqa: PLC0415
        )

        return statistics_during_period(
            self.hass, start, end, {entity}, "5minute", {"energy": "kWh"}, {"change"}
        ).get(entity, [])

    def _effective_observations(
        self, observations: tuple[DischargeObservation, ...] | None = None
    ) -> tuple[DischargeObservation, ...]:
        records = tuple(self._records) if observations is None else observations
        rows_by_start = {
            start: (end, energy) for (start, end), energy in self._recorder_rows.items()
        }
        result: list[DischargeObservation] = []
        index = 0
        while index < len(records):
            item = records[index]
            row = rows_by_start.get(item.start)
            if row is not None and item.quality == "valid":
                end, energy = row
                last = index
                while (
                    records[last].end < end
                    and last + 1 < len(records)
                    and records[last].end == records[last + 1].start
                    and records[last + 1].quality == "valid"
                ):
                    last += 1
                if records[last].end == end:
                    result.append(
                        DischargeObservation(item.start, end, energy, "valid")
                    )
                    index = last + 1
                    continue
            result.append(item)
            index += 1
        return tuple(result)
