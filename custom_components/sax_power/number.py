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
    DEFAULT_TIMED_CHARGE_TARGET_SOC,
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
            SaxPowerTimedChargeTargetSocNumber(coordinator, entry.entry_id),
        ]
    )


class SaxPowerMaxSocNumber(SaxPowerEntity, NumberEntity):
    """Software-seitiges Maximal-SOC für die Ladung.

    Der SAX Speicher besitzt kein natives Max-SOC-Register. Der Coordinator
    setzt stattdessen bei Erreichen dieses Werts das Ladelimit-Register (44)
    auf 0 und gibt es beim Unterschreiten wieder frei (siehe
    coordinator.SaxPowerCoordinator._async_enforce_max_soc).
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


class SaxPowerTimedChargeTargetSocNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Ziel-SOC für das zeitgesteuerte Laden (Software-Logik, kein Register).

    Siehe SaxPowerCoordinator._async_enforce_timed_charge.
    """

    _attr_translation_key = "timed_charge_target_soc"
    _attr_native_min_value = MIN_SOC
    _attr_native_max_value = MAX_SOC
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_timed_charge_target_soc"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.timed_charge_target_soc != DEFAULT_TIMED_CHARGE_TARGET_SOC:
            return
        if (last_state := await self.async_get_last_state()) is None:
            return
        try:
            value = int(float(last_state.state))
        except (ValueError, TypeError):
            return
        await self.coordinator.async_set_timed_charge_target_soc(value)

    @property
    def native_value(self) -> int:
        return self.coordinator.timed_charge_target_soc

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_timed_charge_target_soc(int(value))
        self.async_write_ha_state()
