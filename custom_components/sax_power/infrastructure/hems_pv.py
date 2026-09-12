"""Lokale HA-Leseadapter für REQ-HEMS-PV-INPUT."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from math import isfinite
from typing import Literal

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from ..domain.hems import PvForecast
from ..domain.hems_pv import (
    empty_forecast,
    normalize_pv_forecast,
    normalize_solcast_forecast,
    request_bounds,
    utc_datetime,
)

type PvProvider = Literal["pv_forecast", "solcast_solar"]
_SOLCAST_TIMESTAMP_KEYS = frozenset(("lastupdated", "last_updated"))


def resolve_solcast_timestamp(
    registry: er.EntityRegistry,
    config_entry_id: str,
    *,
    entity_id: str | None = None,
    registry_id: str | None = None,
    allow_legacy_rename: bool = False,
) -> er.RegistryEntry | None:
    """Share the documented timestamp identity between setup and runtime.

    Persisted registry identity wins over a renamed or reused entity ID. Older
    options have no registry identity: only a missing old name may migrate to
    the unique documented timestamp belonging to the same selected source.
    """
    if registry_id is not None:
        candidate = registry.async_get(registry_id)
        candidates = (
            [candidate] if candidate is not None and candidate.id == registry_id else []
        )
    elif entity_id is not None and (
        (candidate := registry.async_get(entity_id)) is not None
        or not allow_legacy_rename
    ):
        candidates = [candidate] if candidate is not None else []
    else:
        candidates = er.async_entries_for_config_entry(registry, config_entry_id)
    matching = [
        item
        for item in candidates
        if item.config_entry_id == config_entry_id
        and item.domain == "sensor"
        and item.platform == "solcast_solar"
        and not item.disabled
        and (
            item.unique_id in _SOLCAST_TIMESTAMP_KEYS
            or item.translation_key == "last_updated"
        )
    ]
    return matching[0] if len(matching) == 1 else None


@dataclass(frozen=True)
class _Timestamp:
    registry_id: str
    fetched_at: datetime
    update_failed: bool


class HemsPvAdapter:
    """Eine explizite Quelle lesen, ohne ihren Wetterabruf zu beeinflussen."""

    def __init__(
        self,
        hass: HomeAssistant,
        provider: PvProvider,
        config_entry_id: str,
        *,
        solcast_timestamp_entity_id: str | None = None,
        solcast_timestamp_registry_id: str | None = None,
        solcast_max_age_hours: float = 24,
        timeout_seconds: float = 10,
    ) -> None:
        if provider not in ("pv_forecast", "solcast_solar"):
            raise ValueError("Nicht unterstützte PV-Schnittstelle")
        if (
            isinstance(solcast_max_age_hours, bool)
            or not 1 <= solcast_max_age_hours <= 24
        ):
            raise ValueError("Solcast-Prognosenalter muss 1 bis 24 Stunden betragen")
        if not isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("Die PV-Abfrage benötigt ein positives Zeitlimit")
        self._hass = hass
        self.provider = provider
        self.config_entry_id = config_entry_id
        self._timestamp_entity_id = solcast_timestamp_entity_id
        self._timestamp_registry_id = solcast_timestamp_registry_id
        self._max_age_hours = solcast_max_age_hours
        self._timeout = timeout_seconds
        self._generation = 0
        self._closed = False
        self._task: asyncio.Task[PvForecast] | None = None

    def invalidate(self) -> None:
        """Quellenwechsel entzieht auch einer schon laufenden Antwort die Freigabe."""
        self._generation += 1
        if self._task is not None:
            self._task.cancel()

    def shutdown(self) -> None:
        """Laufende Leseaktionen beim Entladen beenden."""
        self._closed = True
        self.invalidate()

    def _empty(self, start: datetime, end: datetime, reason: str) -> PvForecast:
        return empty_forecast(
            self.provider,
            self.config_entry_id,
            start,
            end,
            reason,
            max_age_seconds=(
                3600 if self.provider == "pv_forecast" else self._max_age_hours * 3600
            ),
        )

    async def async_read(
        self, as_of: datetime, end: datetime | None = None
    ) -> PvForecast:
        """Genau einen lokalen Leseaufruf mit begrenzter Lebensdauer ausführen."""
        start, finish = request_bounds(as_of, end)
        if self._closed:
            return self._empty(start, finish, "pv_adapter_closed")
        if self._task is not None:
            return self._empty(start, finish, "pv_query_in_progress")
        generation = self._generation
        task = self._hass.async_create_task(
            self._async_read(start, finish), "sax_power_hems_pv"
        )
        self._task = task
        try:
            result = await task
            if self._closed or generation != self._generation:
                return self._empty(start, finish, "pv_source_changed")
            return result
        except asyncio.CancelledError:
            if self._closed or generation != self._generation:
                return self._empty(start, finish, "pv_source_changed")
            raise
        finally:
            if self._task is task:
                self._task = None

    def _entry(self) -> ConfigEntry | None:
        entry = self._hass.config_entries.async_get_entry(self.config_entry_id)
        if (
            entry is None
            or entry.domain != self.provider
            or entry.state is not ConfigEntryState.LOADED
        ):
            return None
        if self.provider == "solcast_solar":
            # Solcasts öffentliche Aktion hat kein Anlagenauswahlfeld.
            # Bei mehreren geladenen Entries ist ihre Bindung nicht nachweisbar.
            entries = self._hass.config_entries.async_entries("solcast_solar")
            if sum(item.state is ConfigEntryState.LOADED for item in entries) != 1:
                return None
        return entry

    def _timestamp(self) -> _Timestamp | None:
        registry = er.async_get(self._hass)
        entity = resolve_solcast_timestamp(
            registry,
            self.config_entry_id,
            entity_id=self._timestamp_entity_id,
            registry_id=self._timestamp_registry_id,
            allow_legacy_rename=True,
        )
        if entity is None:
            return None
        state: State | None = self._hass.states.get(entity.entity_id)
        if state is None:
            return None
        try:
            fetched = utc_datetime(state.state)
        except ValueError, TypeError, OverflowError:
            return None
        self._timestamp_registry_id = entity.id
        return _Timestamp(
            entity.id, fetched, state.attributes.get("last_update_success") is False
        )

    async def _async_read(self, start: datetime, end: datetime) -> PvForecast:
        entry = self._entry()
        if entry is None:
            return self._empty(start, end, "pv_source_unavailable")
        entry_data, entry_options = entry.data, entry.options
        before = None
        if self.provider == "solcast_solar":
            before = self._timestamp()
            if before is None:
                return self._empty(start, end, "pv_missing_fetched_at")
            # Die laufende halbe Stunde wird mitgelesen, statt ihren bereits
            # vergangenen Beginn vom Anbieter wegfiltern zu lassen.
            left = start.replace(
                minute=start.minute // 30 * 30, second=0, microsecond=0
            )
            right = end.replace(minute=end.minute // 30 * 30, second=0, microsecond=0)
            if right < end:
                right += timedelta(minutes=30)
            service = "query_forecast_data"
            data = {
                "start_date_time": left,
                "end_date_time": right,
                "undampened": False,
            }
        else:
            service = "get_forecast"
            data = {"config_entry_id": self.config_entry_id}
        try:
            async with asyncio.timeout(self._timeout):
                response = await self._hass.services.async_call(
                    self.provider, service, data, blocking=True, return_response=True
                )
        except TimeoutError:
            return self._empty(start, end, "pv_query_timeout")
        except HomeAssistantError:
            return self._empty(start, end, "pv_query_failed")
        if (
            self._entry() is not entry
            or entry.data != entry_data
            or entry.options != entry_options
        ):
            return self._empty(start, end, "pv_source_changed")
        if self.provider == "pv_forecast":
            return normalize_pv_forecast(
                response, as_of=start, end=end, source_id=self.config_entry_id
            )
        after = self._timestamp()
        if before is None or after != before:
            return self._empty(start, end, "pv_source_changed")
        result = normalize_solcast_forecast(
            response,
            as_of=start,
            end=end,
            source_id=self.config_entry_id,
            fetched_at=before.fetched_at,
            max_age_hours=self._max_age_hours,
        )
        if before.update_failed:
            return replace(
                result,
                intervals=(),
                coverage_start=None,
                coverage_end=None,
                coverage_complete=False,
                quality_reason="pv_update_failed",
                update_success=False,
            )
        return result
