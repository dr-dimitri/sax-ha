"""Versioned persistence for the derived energy counters."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.energy"
ENERGY_SAVE_DELAY = 300


@dataclass(frozen=True)
class EnergyState:
    """Persisted, independently initialised energy counters."""

    charged_kwh: float | None = None
    discharged_kwh: float | None = None

    @property
    def initialized(self) -> bool:
        """Return whether at least one counter has a numeric baseline."""
        return self.charged_kwh is not None or self.discharged_kwh is not None


class EnergyStateStore:
    """Persist both monotonically increasing counters per config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry_id}",
        )
        self._last_persisted = EnergyState()
        self._pending: EnergyState | None = None
        self._save_scheduled = False

    async def async_load(self) -> EnergyState | None:
        """Load both counters, rejecting invalid fields independently."""
        raw = await self._store.async_load()
        if raw is None:
            return None
        if not isinstance(raw, dict):
            _LOGGER.warning(
                "Ungültigen gespeicherten Energiezählerzustand verworfen: "
                "kein Objekt"
            )
            return EnergyState()

        state = EnergyState(
            charged_kwh=self._validated_counter(raw.get("charged_kwh"), "Laden"),
            discharged_kwh=self._validated_counter(
                raw.get("discharged_kwh"), "Entladen"
            ),
        )
        self._last_persisted = state
        return state

    @callback
    def async_delay_save(
        self, state: EnergyState, delay: float = ENERGY_SAVE_DELAY
    ) -> bool:
        """Coalesce frequent counter changes into one delayed write."""
        if not self._accept_monotonic(state):
            return False
        self._pending = state
        if not self._save_scheduled:
            self._save_scheduled = True
            self._store.async_delay_save(self._consume_pending, delay)
        return True

    async def async_save(self, state: EnergyState) -> bool:
        """Immediately persist a final snapshot, cancelling a delayed write."""
        if not self._accept_monotonic(state):
            return False
        self._pending = None
        self._save_scheduled = False
        await self._store.async_save(self._serialize(state))
        self._last_persisted = state
        return True

    def _consume_pending(self) -> dict[str, float | None]:
        """Return the newest coalesced state when Home Assistant writes it."""
        state = self._pending or self._last_persisted
        self._pending = None
        self._save_scheduled = False
        self._last_persisted = state
        return self._serialize(state)

    def _accept_monotonic(self, state: EnergyState) -> bool:
        baseline = self._pending or self._last_persisted
        for label, value, previous in (
            ("Laden", state.charged_kwh, baseline.charged_kwh),
            ("Entladen", state.discharged_kwh, baseline.discharged_kwh),
        ):
            if value is not None and (
                not math.isfinite(value) or value < 0 or isinstance(value, bool)
            ):
                _LOGGER.warning(
                    "Ungültigen Energiezähler-Snapshot für %s verworfen: %r",
                    label,
                    value,
                )
                return False
            if previous is not None and (value is None or value < previous):
                _LOGGER.warning(
                    "Rückläufigen Energiezähler-Snapshot für %s verworfen: "
                    "%r statt mindestens %r",
                    label,
                    value,
                    previous,
                )
                return False
        return True

    @staticmethod
    def _validated_counter(value: Any, label: str) -> float | None:
        if value is None:
            return None
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(value)
            or value < 0
        ):
            _LOGGER.warning(
                "Ungültigen gespeicherten Energiezähler für %s verworfen: %r",
                label,
                value,
            )
            return None
        return float(value)

    @staticmethod
    def _serialize(state: EnergyState) -> dict[str, float | None]:
        return {
            "charged_kwh": state.charged_kwh,
            "discharged_kwh": state.discharged_kwh,
        }
