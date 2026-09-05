"""Home Assistant storage adapter for timed charging discharge protection."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from ..application.timed_discharge import TimedDischargeState
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.timed_discharge"


class TimedDischargeStateStore:
    """Persist confirmed timed charging independently for each config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry_id}",
        )

    async def async_load(self) -> TimedDischargeState | None:
        """Load a valid UTC expiry without inventing or rewriting invalid state."""
        try:
            raw = await self._store.async_load()
            if raw is None:
                return None
            if not isinstance(raw, dict):
                raise ValueError("Zustand ist kein Objekt")
            timestamp_raw = raw["expires_at"]
            if not isinstance(timestamp_raw, str):
                raise ValueError("Ablaufzeit ist kein Text")
            timestamp = datetime.fromisoformat(timestamp_raw)
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("Ablaufzeit hat keine Zeitzone")
            return TimedDischargeState(expires_at=timestamp.astimezone(UTC))
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
                "Ungültigen gespeicherten Netzlade-Entladeschutz verworfen: %s", err
            )
            return None

    async def async_save(self, state: TimedDischargeState | None) -> None:
        """Persist the confirmed expiry, or remove released protection."""
        if state is None:
            await self._store.async_remove()
            return
        if not isinstance(state, TimedDischargeState):
            raise ValueError("Ungültiger Netzlade-Entladeschutzzustand")
        timestamp = state.expires_at
        if not isinstance(timestamp, datetime):
            raise ValueError("Ablaufzeit ist kein Zeitpunkt")
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Ablaufzeit ohne Zeitzone")
        await self._store.async_save(
            {"expires_at": timestamp.astimezone(UTC).isoformat()}
        )
