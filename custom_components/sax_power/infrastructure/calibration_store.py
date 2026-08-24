"""Home Assistant storage adapter for the calibration schedule."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ..application.calibration import CalibrationState
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.calibration"


class CalibrationStateStore:
    """Persist one calibration schedule per config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry_id}",
        )

    async def async_load(self) -> CalibrationState | None:
        """Load and validate persisted calibration state."""
        raw = await self._store.async_load()
        if raw is None:
            return None
        try:
            timestamp_raw = raw["last_full_charge_at"]
            was_full = raw["was_full"]
            if not isinstance(timestamp_raw, str) or not isinstance(was_full, bool):
                raise ValueError("ungültige Feldtypen")
            timestamp = datetime.fromisoformat(timestamp_raw)
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("Zeitstempel hat keine Zeitzone")
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.warning(
                "Ungültigen gespeicherten Zellkalibrierungszustand verworfen: %s",
                err,
            )
            return None
        return CalibrationState(
            last_full_charge_at=timestamp.astimezone(UTC),
            was_full=was_full,
        )

    async def async_save(self, state: CalibrationState) -> None:
        """Save validated calibration state."""
        timestamp = state.last_full_charge_at
        if timestamp is None:
            raise ValueError("Kalibrierungszustand ohne Zeitstempel")
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Kalibrierungszeitstempel ohne Zeitzone")
        await self._store.async_save(
            {
                "last_full_charge_at": timestamp.astimezone(UTC).isoformat(),
                "was_full": state.was_full,
            }
        )
