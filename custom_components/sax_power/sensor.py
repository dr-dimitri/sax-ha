"""Sensor platform for SAX Power.

Exponiert sämtliche in modbus_llm.yaml dokumentierten (und sinnvoll
benennbaren) Modbus-Register als SensorEntity, siehe anforderung.yaml,
Anforderung REQ-ALL-REGISTERS-READABLE. Die Sensoren sind
beschreibungsbasiert definiert (eine Entity-Klasse, eine Liste von
Descriptions) statt als eine Klasse pro Register, damit die ~48 Sensoren
wartbar bleiben.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfReactivePower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import SaxPowerCoordinator
from .entity import SaxPowerEntity


@dataclass(frozen=True, kw_only=True)
class SaxPowerSensorEntityDescription(SensorEntityDescription):
    """Sensor-Beschreibung mit Zugriffsfunktion auf coordinator.data."""

    value_fn: Callable[[dict[str, Any]], StateType]


def _direct(key: str) -> Callable[[dict[str, Any]], StateType]:
    """Liest den Wert unverändert unter demselben Schlüssel aus coordinator.data."""
    return lambda data: data.get(key)


SENSOR_DESCRIPTIONS: tuple[SaxPowerSensorEntityDescription, ...] = (
    # -- Basic Mode (Slave-ID 64, Register 40042-40049) ---------------------
    SaxPowerSensorEntityDescription(
        key="soc",
        translation_key="soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_direct("soc"),
    ),
    SaxPowerSensorEntityDescription(
        key="discharge_power",
        translation_key="discharge_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: data["power"] if data["power"] > 0 else 0,
    ),
    SaxPowerSensorEntityDescription(
        key="charge_power",
        translation_key="charge_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: -data["power"] if data["power"] < 0 else 0,
    ),
    SaxPowerSensorEntityDescription(
        key="smartmeter_power",
        translation_key="smartmeter_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_direct("smartmeter_power"),
    ),
    SaxPowerSensorEntityDescription(
        key="switch_state_text",
        translation_key="switch_state_text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("switch_state_text"),
    ),
    SaxPowerSensorEntityDescription(
        key="setpoint_power",
        translation_key="setpoint_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("setpoint_power"),
    ),
    SaxPowerSensorEntityDescription(
        key="setpoint_cosphi",
        translation_key="setpoint_cosphi",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("setpoint_cosphi"),
    ),
    # -- Extended Mode - Speicher (Slave-ID 40, Register 40071-40094) -------
    SaxPowerSensorEntityDescription(
        key="ext_sunspec_id",
        translation_key="ext_sunspec_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ext_sunspec_id"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_sunspec_length",
        translation_key="ext_sunspec_length",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ext_sunspec_length"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_current_sum_native",
        translation_key="ext_current_sum_native",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=_direct("ext_current_sum_native"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_current_l1",
        translation_key="ext_current_l1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=_direct("ext_current_l1"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_current_l2",
        translation_key="ext_current_l2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=_direct("ext_current_l2"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_current_l3",
        translation_key="ext_current_l3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=_direct("ext_current_l3"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_current_sf",
        translation_key="ext_current_sf",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ext_current_sf"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_current_sum",
        translation_key="ext_current_sum",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=_direct("ext_current_sum"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_voltage_l1",
        translation_key="ext_voltage_l1",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=_direct("ext_voltage_l1"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_voltage_l2",
        translation_key="ext_voltage_l2",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=_direct("ext_voltage_l2"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_voltage_l3",
        translation_key="ext_voltage_l3",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=_direct("ext_voltage_l3"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_voltage_sf",
        translation_key="ext_voltage_sf",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ext_voltage_sf"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_voltage_sum",
        translation_key="ext_voltage_sum",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=_direct("ext_voltage_sum"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_power_active",
        translation_key="ext_power_active",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_direct("ext_power_active"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_power_active_sf",
        translation_key="ext_power_active_sf",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ext_power_active_sf"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_frequency",
        translation_key="ext_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        value_fn=_direct("ext_frequency"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_frequency_sf",
        translation_key="ext_frequency_sf",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ext_frequency_sf"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_power_apparent",
        translation_key="ext_power_apparent",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        value_fn=_direct("ext_power_apparent"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_power_apparent_sf",
        translation_key="ext_power_apparent_sf",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ext_power_apparent_sf"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_power_reactive",
        translation_key="ext_power_reactive",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
        value_fn=_direct("ext_power_reactive"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_power_reactive_sf",
        translation_key="ext_power_reactive_sf",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ext_power_reactive_sf"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_power_factor",
        translation_key="ext_power_factor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_direct("ext_power_factor"),
    ),
    SaxPowerSensorEntityDescription(
        key="ext_power_factor_sf",
        translation_key="ext_power_factor_sf",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ext_power_factor_sf"),
    ),
    # -- Extended Mode - Smart Meter (Slave-ID 40, Register 40095-40110) ----
    SaxPowerSensorEntityDescription(
        key="sm_energy_fed_in",
        translation_key="sm_energy_fed_in",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=_direct("sm_energy_fed_in"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_energy_consumed",
        translation_key="sm_energy_consumed",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=_direct("sm_energy_consumed"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_energy_sf",
        translation_key="sm_energy_sf",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("sm_energy_sf"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_switch_state_text",
        translation_key="sm_switch_state_text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("sm_switch_state_text"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_current_l1",
        translation_key="sm_current_l1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=_direct("sm_current_l1"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_current_l2",
        translation_key="sm_current_l2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=_direct("sm_current_l2"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_current_l3",
        translation_key="sm_current_l3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=_direct("sm_current_l3"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_current_sum",
        translation_key="sm_current_sum",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=_direct("sm_current_sum"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_power_l1",
        translation_key="sm_power_l1",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_direct("sm_power_l1"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_power_l2",
        translation_key="sm_power_l2",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_direct("sm_power_l2"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_power_l3",
        translation_key="sm_power_l3",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_direct("sm_power_l3"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_power_sf",
        translation_key="sm_power_sf",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("sm_power_sf"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_power_sum",
        translation_key="sm_power_sum",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_direct("sm_power_sum"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_voltage_l1",
        translation_key="sm_voltage_l1",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=_direct("sm_voltage_l1"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_voltage_l2",
        translation_key="sm_voltage_l2",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=_direct("sm_voltage_l2"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_voltage_l3",
        translation_key="sm_voltage_l3",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=_direct("sm_voltage_l3"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_voltage_sum",
        translation_key="sm_voltage_sum",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=_direct("sm_voltage_sum"),
    ),
    SaxPowerSensorEntityDescription(
        key="sm_power_total",
        translation_key="sm_power_total",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_direct("sm_power_total"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        SaxPowerSensor(coordinator, entry.entry_id, description)
        for description in SENSOR_DESCRIPTIONS
    )


class SaxPowerSensor(SaxPowerEntity, SensorEntity):
    """Generischer Sensor: Wert wird per value_fn aus coordinator.data gelesen."""

    entity_description: SaxPowerSensorEntityDescription

    def __init__(
        self,
        coordinator: SaxPowerCoordinator,
        entry_id: str,
        description: SaxPowerSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
