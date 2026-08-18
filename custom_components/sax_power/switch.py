"""Switch platform for SAX Power."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

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
    async_add_entities(
        [
            SaxPowerStorageSwitch(coordinator, entry.entry_id),
            SaxPowerTimedChargeSwitch(coordinator, entry.entry_id),
            SaxPowerManualGridChargeSwitch(coordinator, entry.entry_id),
        ]
    )


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


class SaxPowerTimedChargeSwitch(RestoreEntity, SaxPowerEntity, SwitchEntity):
    """Aktiviert/deaktiviert das zeitgesteuerte Laden (Software-Logik).

    Siehe SaxPowerCoordinator._async_enforce_grid_charge sowie die
    zugehörigen Number-/Time-Entities (Ziel-SOC, Zeitfenster, Ladeleistung).
    """

    _attr_translation_key = "timed_charge_enabled"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_timed_charge_enabled"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.timed_charge_enabled:
            return
        if (last_state := await self.async_get_last_state()) is None:
            return
        await self.coordinator.async_set_timed_charge_enabled(last_state.state == "on")

    @property
    def is_on(self) -> bool:
        return self.coordinator.timed_charge_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_timed_charge_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_timed_charge_enabled(False)
        self.async_write_ha_state()


class SaxPowerManualGridChargeSwitch(RestoreEntity, SaxPowerEntity, SwitchEntity):
    """Manuelle Netzladung: lädt den Speicher direkt aus dem Netz, ohne dass
    das zeitgesteuerte Laden aktiviert sein muss.

    Nutzt denselben SunSpec-Modus-Schreibpfad (Register 40049/40051) und
    denselben zentralen Ladeleistungsgrenzwert wie das zeitgesteuerte Laden
    (siehe SaxPowerCoordinator._async_enforce_grid_charge) - keine eigene
    Leistungseinstellung, keine Zeitfenster-/Ziel-SOC-Prüfung.
    """

    _attr_translation_key = "manual_grid_charge_enabled"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_manual_grid_charge_enabled"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.manual_grid_charge_enabled:
            return
        if (last_state := await self.async_get_last_state()) is None:
            return
        await self.coordinator.async_set_manual_grid_charge_enabled(
            last_state.state == "on"
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.manual_grid_charge_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_manual_grid_charge_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_manual_grid_charge_enabled(False)
        self.async_write_ha_state()
