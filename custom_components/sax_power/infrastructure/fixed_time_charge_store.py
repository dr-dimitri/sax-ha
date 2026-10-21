"""Persist daily completion for REQ-FIXED-TIME-GRID-CHARGE."""

from __future__ import annotations

import logging
from datetime import date
from datetime import time as dt_time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from ..application.fixed_time_charge import FixedTimeChargeState
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class FixedTimeChargeStateStore:
    """Retain an unfinished occurrence and its completed latch across reloads."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass, 1, f"{DOMAIN}.fixed_time_charge.{entry_id}", atomic_writes=True
        )

    async def async_load(self) -> FixedTimeChargeState | None:
        """Discard incomplete or malformed persisted permissions."""
        try:
            raw = await self._store.async_load()
            if raw is None or raw == {"active": False}:
                return None
            if not isinstance(raw, dict) or type(raw.get("completed")) is not bool:
                raise ValueError("Ungültige tägliche Netzladefreigabe")
            state = FixedTimeChargeState(
                start=dt_time.fromisoformat(raw["start"]),
                day=date.fromisoformat(raw["day"]),
                completed=raw["completed"],
            )
            _serialize(state)
            return state
        except (
            HomeAssistantError,
            KeyError,
            NotImplementedError,
            OSError,
            OverflowError,
            TypeError,
            ValueError,
        ) as err:
            _LOGGER.warning("Gespeicherte tägliche Netzladefreigabe verworfen: %s", err)
            return None

    async def async_save(self, state: FixedTimeChargeState | None) -> None:
        """Read back writes so a failed disk write can be retried."""
        expected = {"active": False} if state is None else _serialize(state)
        try:
            await self._store.async_save(expected)
            written = await self._store.async_load()
            if written != expected:
                raise ValueError("Gespeicherter Zustand weicht ab")
        except (
            HomeAssistantError,
            NotImplementedError,
            OSError,
            OverflowError,
            TypeError,
            ValueError,
        ) as err:
            raise HomeAssistantError(
                "Tägliche Netzladefreigabe nicht sicher gespeichert"
            ) from err


def _serialize(state: FixedTimeChargeState) -> dict[str, str | bool]:
    if (
        not isinstance(state, FixedTimeChargeState)
        or not isinstance(state.start, dt_time)
        or state.start.tzinfo is not None
        or not isinstance(state.day, date)
        or type(state.completed) is not bool
    ):
        raise ValueError("Ungültige tägliche Netzladefreigabe")
    return {
        "start": state.start.isoformat(),
        "day": state.day.isoformat(),
        "completed": state.completed,
    }
