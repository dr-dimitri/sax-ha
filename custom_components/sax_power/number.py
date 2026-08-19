"""Number platform for SAX Power."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    MAX_POWER_LIMIT,
    MAX_SOC,
    MIN_POWER_LIMIT,
    MIN_SOC,
    REG_LIMIT_CHARGE,
    REG_LIMIT_DISCHARGE,
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
            SaxPowerMaxSocNumber(coordinator, entry.entry_id),
            SaxPowerChargeLimitNumber(coordinator, entry.entry_id),
            SaxPowerDischargeLimitNumber(coordinator, entry.entry_id),
        ]
    )


class SaxPowerMaxSocNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Software-seitiges Maximal-SOC für die Ladung.

    Der SAX Speicher besitzt kein natives Max-SOC-Register. Der Coordinator
    setzt stattdessen bei Erreichen dieses Werts das Ladelimit-Register (44)
    auf 0 und gibt es beim Unterschreiten wieder frei (siehe
    coordinator.SaxPowerCoordinator._async_enforce_max_soc). Dient
    zusätzlich als Ziel-SOC für das zeitgesteuerte Laden (keine eigene
    Einstellung dafür, siehe anforderung.yaml REQ-TIMED-SOC-CHARGE).

    Zustand wird über RestoreEntity über Neustarts hinweg persistiert. Gibt
    es (z. B. direkt nach der Ersteinrichtung) noch keinen gespeicherten
    Zustand, wird MAX_SOC (100 %) als Vorgabewert gesetzt statt "unbekannt"
    zu bleiben - andernfalls würde der Schieberegler optisch bei 0 stehen.
    """

    _attr_translation_key = "max_soc"
    _attr_native_min_value = MIN_SOC
    _attr_native_max_value = MAX_SOC
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_max_soc"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.max_soc is not None:
            return
        restored_value: int | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = int(float(last_state.state))
            except (TypeError, ValueError):
                restored_value = None
        await self.coordinator.async_set_max_soc(
            restored_value if restored_value is not None else MAX_SOC
        )

    @property
    def native_value(self) -> int | None:
        return self.coordinator.max_soc

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_max_soc(int(value))
        self.async_write_ha_state()


class SaxPowerChargeLimitNumber(SaxPowerEntity, NumberEntity):
    """Leistungsgrenzwert für Ladung (Register 44)."""

    _attr_translation_key = "charge_limit"
    _attr_native_min_value = MIN_POWER_LIMIT
    _attr_native_max_value = MAX_POWER_LIMIT
    _attr_native_step = 50
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_charge_limit"

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data["charge_limit"]

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_register(REG_LIMIT_CHARGE, int(value))
        await self.coordinator.async_refresh()


class SaxPowerDischargeLimitNumber(SaxPowerEntity, NumberEntity):
    """Leistungsgrenzwert für Entladung (Register 43)."""

    _attr_translation_key = "discharge_limit"
    _attr_native_min_value = MIN_POWER_LIMIT
    _attr_native_max_value = MAX_POWER_LIMIT
    _attr_native_step = 50
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_discharge_limit"

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data["discharge_limit"]

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_register(REG_LIMIT_DISCHARGE, int(value))
        await self.coordinator.async_refresh()
