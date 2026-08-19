"""Time platform for SAX Power.

Start-/Endzeit des Zeitfensters für das zeitgesteuerte Laden (Software-
Logik, kein Register). Siehe
coordinator.SaxPowerCoordinator._async_enforce_timed_charge.
"""

from __future__ import annotations

from datetime import time as dt_time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_TIMED_CHARGE_END,
    CONF_TIMED_CHARGE_START,
    DATA_COORDINATOR,
    DEFAULT_TIMED_CHARGE_END,
    DEFAULT_TIMED_CHARGE_START,
    DOMAIN,
)
from .coordinator import SaxPowerCoordinator
from .entity import SaxPowerEntity, initial_config_value


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        [
            SaxPowerTimedChargeStartTime(coordinator, entry.entry_id),
            SaxPowerTimedChargeEndTime(coordinator, entry.entry_id),
        ]
    )


class SaxPowerTimedChargeStartTime(RestoreEntity, SaxPowerEntity, TimeEntity):
    """Beginn des Zeitfensters für das zeitgesteuerte Laden."""

    _attr_translation_key = "timed_charge_start"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_timed_charge_start"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.timed_charge_start is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := dt_util.parse_time(last_state.state)) is not None:
                await self.coordinator.async_set_timed_charge_start(value)
                return
        # Kein zuvor gespeicherter Zustand (allererster Start eines neu
        # eingerichteten Eintrags) - Vorgabewert aus der Ersteinrichtung
        # nutzen, sonst den Hard-Default (siehe const.py).
        initial = initial_config_value(
            self.hass, self._entry_id, CONF_TIMED_CHARGE_START
        )
        value = dt_util.parse_time(initial or DEFAULT_TIMED_CHARGE_START)
        if value is not None:
            await self.coordinator.async_set_timed_charge_start(value)

    @property
    def native_value(self) -> dt_time | None:
        return self.coordinator.timed_charge_start

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_set_timed_charge_start(value)
        self.async_write_ha_state()


class SaxPowerTimedChargeEndTime(RestoreEntity, SaxPowerEntity, TimeEntity):
    """Ende des Zeitfensters für das zeitgesteuerte Laden."""

    _attr_translation_key = "timed_charge_end"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_timed_charge_end"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.timed_charge_end is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := dt_util.parse_time(last_state.state)) is not None:
                await self.coordinator.async_set_timed_charge_end(value)
                return
        initial = initial_config_value(self.hass, self._entry_id, CONF_TIMED_CHARGE_END)
        value = dt_util.parse_time(initial or DEFAULT_TIMED_CHARGE_END)
        if value is not None:
            await self.coordinator.async_set_timed_charge_end(value)

    @property
    def native_value(self) -> dt_time | None:
        return self.coordinator.timed_charge_end

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_set_timed_charge_end(value)
        self.async_write_ha_state()
