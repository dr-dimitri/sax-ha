"""Switch platform for SAX Power."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    REG_SWITCH_STATE,
    SWITCH_STATE_CONNECTED,
    SWITCH_STATE_OFF,
    SWITCH_STATE_ON,
)
from .coordinator import SaxPowerCoordinator
from .entity import SaxPowerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([SaxPowerStorageSwitch(coordinator, entry.entry_id)])


class SaxPowerStorageSwitch(SaxPowerEntity, SwitchEntity):
    """Ein-/Ausschalten des Speichers (Register 45)."""

    _attr_translation_key = "storage"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_storage_switch"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data["switch_state"] in (
            SWITCH_STATE_ON,
            SWITCH_STATE_CONNECTED,
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_register(REG_SWITCH_STATE, SWITCH_STATE_ON)
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_register(REG_SWITCH_STATE, SWITCH_STATE_OFF)
        await self.coordinator.async_refresh()
