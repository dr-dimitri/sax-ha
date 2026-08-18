"""Sensor platform for SAX Power."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
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
            SaxPowerSocSensor(coordinator, entry.entry_id),
            SaxPowerDischargePowerSensor(coordinator, entry.entry_id),
            SaxPowerChargePowerSensor(coordinator, entry.entry_id),
        ]
    )


class SaxPowerSocSensor(SaxPowerEntity, SensorEntity):
    """State of charge of the storage system (Register 46)."""

    _attr_translation_key = "soc"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_soc"

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data["soc"]


class SaxPowerDischargePowerSensor(SaxPowerEntity, SensorEntity):
    """Entladeleistung ins Hausnetz.

    Register 47 (Leistung P des Speichers) liefert einen einzelnen
    vorzeichenbehafteten Wert für Lade-/Entladeleistung. Positive Werte
    werden hier als Entladung interpretiert - die Vorzeichenkonvention ist
    in modbus_llm.yaml nicht dokumentiert und sollte am realen Gerät
    verifiziert werden.
    """

    _attr_translation_key = "discharge_power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_discharge_power"

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data is None:
            return None
        power = self.coordinator.data["power"]
        return power if power > 0 else 0


class SaxPowerChargePowerSensor(SaxPowerEntity, SensorEntity):
    """Ladeleistung des Speichers (siehe Vorzeichen-Hinweis oben)."""

    _attr_translation_key = "charge_power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_charge_power"

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data is None:
            return None
        power = self.coordinator.data["power"]
        return -power if power < 0 else 0
