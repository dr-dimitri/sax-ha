"""Home Assistant persistence for a timed-charge latch."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import UTC, datetime
from datetime import time as dt_time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from ..application.timed_charge import TimedChargeState, is_tariff_source
from ..const import DOMAIN, MAX_SOC, MIN_SOC

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.timed_charge"


class TimedChargeStateStore:
    """Keep the armed window separate from settings and measured grid charging."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry_id}",
            atomic_writes=True,
        )

    async def async_load(self) -> TimedChargeState | None:
        """Return only a complete window identity, without inventing a latch."""
        try:
            raw = await self._store.async_load()
            if raw is None:
                return None
            if not isinstance(raw, dict):
                raise ValueError("Zustand ist kein Objekt")
            if raw.get("armed") is False and len(raw) == 1:
                return None
            if raw.get("armed") is not True:
                raise ValueError("Ungültige Freigabe der Netzlade-Hysterese")
            state = TimedChargeState(
                start=dt_time.fromisoformat(raw["start"]),
                end=dt_time.fromisoformat(raw["end"]),
                expires_at=datetime.fromisoformat(raw["expires_at"]),
                source=raw.get("source"),
                completed_target_soc=raw.get("completed_target_soc"),
            )
            _serialize(state)
            return replace(state, expires_at=state.expires_at.astimezone(UTC))
        except (
            HomeAssistantError,
            KeyError,
            NotImplementedError,
            OSError,
            OverflowError,
            TypeError,
            ValueError,
        ) as err:
            _LOGGER.warning(
                "Ungültige gespeicherte Netzlade-Hysterese verworfen: %s", err
            )
            return None

    async def async_save(self, state: TimedChargeState | None) -> None:
        """Persist an armed window immediately, or remove a released latch."""
        expected = {"armed": False} if state is None else _serialize(state)
        try:
            await self._store.async_save(expected)
            # Core catches WriteError internally. Only a readback lets the
            # coordinator retry until the state actually reaches disk.
            written = await self._store.async_load()
        except (
            HomeAssistantError,
            NotImplementedError,
            OSError,
            OverflowError,
            TypeError,
            ValueError,
        ) as err:
            raise HomeAssistantError(
                "Netzlade-Hysterese nicht sicher gespeichert"
            ) from err
        if written != expected:
            raise HomeAssistantError("Netzlade-Hysterese nach dem Speichern abweichend")


def _serialize(state: TimedChargeState) -> dict[str, str | bool | int]:
    if not isinstance(state, TimedChargeState):
        raise ValueError("Ungültige Netzlade-Hysterese")
    if any(
        not isinstance(value, dt_time) or value.tzinfo is not None
        for value in (state.start, state.end)
    ) or (state.start == state.end and state.source is None):
        raise ValueError("Ungültige lokale Fenstergrenzen")
    timestamp = state.expires_at
    if (
        not isinstance(timestamp, datetime)
        or timestamp.tzinfo is None
        or timestamp.utcoffset() is None
    ):
        raise ValueError("Fensterende ist kein Zeitpunkt mit Zeitzone")
    if state.source is not None and not is_tariff_source(state.source):
        raise ValueError("Ungültige Tarifidentität")
    result: dict[str, str | bool | int] = {
        "armed": True,
        "start": state.start.isoformat(),
        "end": state.end.isoformat(),
        "expires_at": timestamp.astimezone(UTC).isoformat(),
    }
    if state.source is not None:
        result["source"] = state.source
    target = state.completed_target_soc
    if target is not None:
        if (
            state.source is None
            or type(target) is not int
            or not MIN_SOC <= target <= MAX_SOC
        ):
            raise ValueError("Ungültiges abgeschlossenes Netzladeziel")
        result["completed_target_soc"] = target
    return result
