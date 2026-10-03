"""Home Assistant storage adapter for timed charging discharge protection."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.const import EVENT_HOMEASSISTANT_FINAL_WRITE
from homeassistant.core import CALLBACK_TYPE, CoreState, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from ..application.timed_charge import is_tariff_source
from ..application.timed_discharge import TimedDischargeState
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.timed_discharge"


class TimedDischargeStateStore:
    """Persist confirmed timed charging independently for each config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry_id}",
            atomic_writes=True,
        )
        self._pending: dict[str, Any] | None = None
        self._last_persisted: dict[str, Any] | None = None
        self._write_lock = asyncio.Lock()
        self._unsub_final_write: CALLBACK_TYPE | None = None

    @property
    def save_pending(self) -> bool:
        """Whether a requested state still lacks a confirmed storage write."""
        return self._pending is not None

    async def async_load(self) -> TimedDischargeState | None:
        """Load a valid UTC expiry without inventing or rewriting invalid state."""
        try:
            raw = await self._store.async_load()
            if raw is None:
                return None
            if not isinstance(raw, dict):
                raise ValueError("Zustand ist kein Objekt")
            if raw == {"active": False}:
                self._last_persisted = raw
                return None
            timestamp_raw = raw["expires_at"]
            if not isinstance(timestamp_raw, str):
                raise ValueError("Ablaufzeit ist kein Text")
            timestamp = datetime.fromisoformat(timestamp_raw)
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("Ablaufzeit hat keine Zeitzone")
            source = raw.get("source")
            if source is not None and not is_tariff_source(source):
                raise ValueError("Ungültige Tarifidentität")
            state = TimedDischargeState(timestamp.astimezone(UTC), source)
            self._last_persisted = _serialize(state)
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
            _LOGGER.warning(
                "Ungültigen gespeicherten Netzlade-Entladeschutz verworfen: %s", err
            )
            return None

    async def async_save(self, state: TimedDischargeState | None) -> None:
        """Persist the latest requested state, retaining failures for retry."""
        payload = _serialize(state)
        if self._pending is None and payload == self._last_persisted:
            return
        self._pending = payload
        await self.async_flush()

    async def async_flush(self, *, final: bool = False) -> None:
        """Flush pending protection without leaving an old owner's callbacks."""
        self._cancel_final_write_listener()
        try:
            async with self._write_lock:
                payload = self._pending
                if payload is None:
                    return
                if payload == self._last_persisted:
                    self._pending = None
                    return
                if self._hass.state is CoreState.stopping:
                    # Core readbacks during stopping can confirm RAM only;
                    # REQ-TIMED-SOC-CHARGE requires the final disk write.
                    self._ensure_final_write_listener()
                    return
                await self._store.async_save(payload)
                if self._hass.state is CoreState.stopping:
                    self._ensure_final_write_listener()
                    return
                # Core swallows WriteError; the proof is confirmed only once
                # its active or inactive snapshot is readable from storage.
                if await self._store.async_load() != payload:
                    raise HomeAssistantError(
                        "Netzlade-Entladesperre nach dem Speichern abweichend"
                    )
                self._last_persisted = payload
                if self._pending is payload:
                    self._pending = None
        except HomeAssistantError, OSError, ValueError:
            if self._hass.state is CoreState.stopping:
                self._ensure_final_write_listener()
            elif final:
                self._cancel_final_write_listener()
            raise

    @callback
    def _ensure_final_write_listener(self) -> None:
        if self._unsub_final_write is None:
            self._unsub_final_write = self._hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_FINAL_WRITE, self._async_final_write
            )

    @callback
    def _cancel_final_write_listener(self) -> None:
        if self._unsub_final_write is not None:
            self._unsub_final_write()
            self._unsub_final_write = None

    async def _async_final_write(self, _event: Any) -> None:
        self._unsub_final_write = None
        try:
            await self.async_flush(final=True)
        except (HomeAssistantError, OSError, ValueError) as err:
            _LOGGER.warning(
                "Netzlade-Entladesperre beim Beenden nicht gespeichert: %s", err
            )


def _serialize(state: TimedDischargeState | None) -> dict[str, Any]:
    if state is None:
        return {"active": False}
    if not isinstance(state, TimedDischargeState):
        raise ValueError("Ungültiger Netzlade-Entladeschutzzustand")
    timestamp = state.expires_at
    if not isinstance(timestamp, datetime):
        raise ValueError("Ablaufzeit ist kein Zeitpunkt")
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Ablaufzeit ohne Zeitzone")
    result = {"expires_at": timestamp.astimezone(UTC).isoformat()}
    if state.source is not None:
        if not is_tariff_source(state.source):
            raise ValueError("Ungültige Tarifidentität")
        result["source"] = state.source
    return result
