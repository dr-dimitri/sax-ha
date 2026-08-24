"""Sensor platform for SAX Power.

Exponiert die Basic-Mode-Register (Slave-ID 64) sowie die im SunSpec-Modus
(Slave-ID 100, siehe modbus.pdf) verfügbaren Werte als SensorEntity. Die
Sensoren sind beschreibungsbasiert definiert (eine Entity-Klasse, eine Liste
von Descriptions), siehe anforderung.yaml, REQ-SUNSPEC-MODE-CORRECTION.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
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
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import SaxPowerCoordinator
from .entity import SaxPowerEntity


@dataclass(frozen=True, kw_only=True)
class SaxPowerSensorEntityDescription(SensorEntityDescription):
    """Sensor-Beschreibung mit Zugriffsfunktion auf coordinator.data.

    `attributes_fn` ist optional und liefert zusätzliche Attribute für
    Sensoren, deren Zustand allein die Nachvollziehbarkeit nicht hergibt -
    aktuell der Statussensor des preisoptimierten Ladens, der damit die
    zugrundeliegenden Preise und die geplanten Ladefenster mitliefert.
    """

    value_fn: Callable[[dict[str, Any]], StateType | datetime]
    attributes_fn: Callable[[SaxPowerCoordinator], dict[str, Any]] | None = None


def _direct(key: str) -> Callable[[dict[str, Any]], StateType]:
    """Liest den Wert unverändert unter demselben Schlüssel aus coordinator.data."""
    return lambda data: data.get(key)


def _positive_part(key: str) -> Callable[[dict[str, Any]], StateType]:
    """Positiver Anteil eines vorzeichenbehafteten Werts, sonst 0.

    Gibt None zurück (-> Sensor "unbekannt"), solange der Quellwert selbst
    None ist (z. B. weil der SunSpec-Modus gerade nicht erreichbar ist).
    """

    def value_fn(data: dict[str, Any]) -> StateType:
        value = data.get(key)
        if value is None:
            return None
        return value if value > 0 else 0

    return value_fn


def _negative_part(key: str) -> Callable[[dict[str, Any]], StateType]:
    """Negativer Anteil (invertiert, positiv dargestellt), sonst 0.

    Siehe _positive_part.
    """

    def value_fn(data: dict[str, Any]) -> StateType:
        value = data.get(key)
        if value is None:
            return None
        return -value if value < 0 else 0

    return value_fn


def _bool_text(
    key: str, *, true_text: str, false_text: str
) -> Callable[[dict[str, Any]], StateType]:
    def value_fn(data: dict[str, Any]) -> StateType:
        value = data.get(key)
        if value is None:
            return None
        return true_text if value else false_text

    return value_fn


SENSOR_DESCRIPTIONS: tuple[SaxPowerSensorEntityDescription, ...] = (
    # -- Basic Mode (Slave-ID 64, Register 40042-40047) ---------------------
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
        value_fn=_positive_part("storage_power_active"),
    ),
    SaxPowerSensorEntityDescription(
        key="charge_power",
        translation_key="charge_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_negative_part("storage_power_active"),
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
        key="timed_charge_active_text",
        translation_key="timed_charge_active_text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_bool_text(
            "timed_charge_active", true_text="Aktiv", false_text="Inaktiv"
        ),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_serving_active_text",
        translation_key="grid_serving_active_text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_bool_text(
            "grid_serving_active", true_text="Aktiv", false_text="Inaktiv"
        ),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_serving_forecast",
        translation_key="grid_serving_forecast",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=_direct("grid_serving_forecast_kwh"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_serving_pause_status",
        translation_key="grid_serving_pause_status",
        value_fn=_direct("grid_serving_pause_status"),
    ),
    SaxPowerSensorEntityDescription(
        key="price_charge_active_text",
        translation_key="price_charge_active_text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_bool_text(
            "price_charge_active", true_text="Aktiv", false_text="Inaktiv"
        ),
    ),
    # Klartextstatus des preisoptimierten Ladens (siehe const.PRICE_STATUS_*
    # sowie anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE). Bewusst kein
    # entity_category=DIAGNOSTIC: das ist die Entity, an der der Anwender im
    # Alltag abliest, was die Automatik gerade tut.
    SaxPowerSensorEntityDescription(
        key="price_charge_status_text",
        translation_key="price_charge_status_text",
        value_fn=_direct("price_charge_status"),
        attributes_fn=lambda coordinator: coordinator.price_planner.plan_attributes,
    ),
    SaxPowerSensorEntityDescription(
        key="price_charge_next_start",
        translation_key="price_charge_next_start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_direct("price_charge_next_start"),
    ),
    SaxPowerSensorEntityDescription(
        key="next_cell_calibration",
        translation_key="next_cell_calibration",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("next_cell_calibration"),
    ),
    SaxPowerSensorEntityDescription(
        key="price_charge_current_price",
        translation_key="price_charge_current_price",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="EUR/kWh",
        suggested_display_precision=4,
        value_fn=_direct("price_charge_current_price"),
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
    # -- SunSpec-Modus: Common (Slave-ID 100, Identität, Diagnose) -----------
    SaxPowerSensorEntityDescription(
        key="sun_manufacturer",
        translation_key="sun_manufacturer",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("sun_manufacturer"),
    ),
    SaxPowerSensorEntityDescription(
        key="sun_model",
        translation_key="sun_model",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("sun_model"),
    ),
    SaxPowerSensorEntityDescription(
        key="sun_version_master",
        translation_key="sun_version_master",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("sun_version_master"),
    ),
    SaxPowerSensorEntityDescription(
        key="sun_version_gateway",
        translation_key="sun_version_gateway",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("sun_version_gateway"),
    ),
    SaxPowerSensorEntityDescription(
        key="sun_serial_number",
        translation_key="sun_serial_number",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("sun_serial_number"),
    ),
    # -- SunSpec-Modus: Modell 103 "3Ph Inverter" (Speicherelektronik) -------
    SaxPowerSensorEntityDescription(
        key="storage_current_sum",
        translation_key="storage_current_sum",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_current_sum"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_current_a",
        translation_key="storage_current_a",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_current_a"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_current_b",
        translation_key="storage_current_b",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_current_b"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_current_c",
        translation_key="storage_current_c",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_current_c"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_voltage_a",
        translation_key="storage_voltage_a",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_voltage_a"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_voltage_b",
        translation_key="storage_voltage_b",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_voltage_b"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_voltage_c",
        translation_key="storage_voltage_c",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_voltage_c"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_power_active",
        translation_key="storage_power_active",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_power_active"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_power_apparent",
        translation_key="storage_power_apparent",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_power_apparent"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_power_reactive",
        translation_key="storage_power_reactive",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_power_reactive"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_power_factor",
        translation_key="storage_power_factor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_power_factor"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_frequency",
        translation_key="storage_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_frequency"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_max_cell_temp",
        translation_key="storage_max_cell_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=_direct("storage_max_cell_temp"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_state_text",
        translation_key="storage_state_text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_state_text"),
    ),
    SaxPowerSensorEntityDescription(
        key="storage_event_text",
        translation_key="storage_event_text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("storage_event_text"),
    ),
    SaxPowerSensorEntityDescription(
        key="pv_power",
        translation_key="pv_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_direct("pv_power"),
    ),
    # -- SunSpec-Modus: Modell 123 "Immediate Controls" ----------------------
    SaxPowerSensorEntityDescription(
        key="ic_power_setpoint_pct",
        translation_key="ic_power_setpoint_pct",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ic_power_setpoint_pct"),
    ),
    SaxPowerSensorEntityDescription(
        key="ic_timeout",
        translation_key="ic_timeout",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ic_timeout"),
    ),
    SaxPowerSensorEntityDescription(
        key="ic_control_mode_text",
        translation_key="ic_control_mode_text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ic_control_mode_text"),
    ),
    SaxPowerSensorEntityDescription(
        key="ic_max_power_reference",
        translation_key="ic_max_power_reference",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("ic_max_power_reference"),
    ),
    # -- SunSpec-Modus: Modell 203 "WYE Connect 3Ph Meter" (Netz/Smart Meter) -
    SaxPowerSensorEntityDescription(
        key="grid_current_sum",
        translation_key="grid_current_sum",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_current_sum"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_current_l1",
        translation_key="grid_current_l1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_current_l1"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_current_l2",
        translation_key="grid_current_l2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_current_l2"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_current_l3",
        translation_key="grid_current_l3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_current_l3"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_voltage_ln_avg",
        translation_key="grid_voltage_ln_avg",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_voltage_ln_avg"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_voltage_l1",
        translation_key="grid_voltage_l1",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_voltage_l1"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_voltage_l2",
        translation_key="grid_voltage_l2",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_voltage_l2"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_voltage_l3",
        translation_key="grid_voltage_l3",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_voltage_l3"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_frequency",
        translation_key="grid_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_frequency"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_power_active_l1",
        translation_key="grid_power_active_l1",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_power_active_l1"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_power_active_l2",
        translation_key="grid_power_active_l2",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_power_active_l2"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_power_active_l3",
        translation_key="grid_power_active_l3",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_power_active_l3"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_power_apparent_sum",
        translation_key="grid_power_apparent_sum",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_power_apparent_sum"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_power_reactive_sum",
        translation_key="grid_power_reactive_sum",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_power_reactive_sum"),
    ),
    SaxPowerSensorEntityDescription(
        key="grid_power_factor_sum",
        translation_key="grid_power_factor_sum",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("grid_power_factor_sum"),
    ),
    # -- SunSpec-Modus: Modell 802 "Battery Base" (Akkuzellen) ---------------
    SaxPowerSensorEntityDescription(
        key="battery_capacity",
        translation_key="battery_capacity",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("battery_capacity"),
    ),
    SaxPowerSensorEntityDescription(
        key="battery_charge_power_available",
        translation_key="battery_charge_power_available",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("battery_charge_power_available"),
    ),
    SaxPowerSensorEntityDescription(
        key="battery_discharge_power_available",
        translation_key="battery_discharge_power_available",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("battery_discharge_power_available"),
    ),
    SaxPowerSensorEntityDescription(
        key="battery_soc_max",
        translation_key="battery_soc_max",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("battery_soc_max"),
    ),
    SaxPowerSensorEntityDescription(
        key="battery_soc_min",
        translation_key="battery_soc_min",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("battery_soc_min"),
    ),
    SaxPowerSensorEntityDescription(
        key="battery_soc",
        translation_key="battery_soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("battery_soc"),
    ),
    SaxPowerSensorEntityDescription(
        key="battery_discharge_depth",
        translation_key="battery_discharge_depth",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("battery_discharge_depth"),
    ),
    SaxPowerSensorEntityDescription(
        key="battery_charging_active_text",
        translation_key="battery_charging_active_text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_bool_text(
            "battery_charging_active",
            true_text="Leistung anliegend",
            false_text="Keine Leistung",
        ),
    ),
    SaxPowerSensorEntityDescription(
        key="battery_event_text",
        translation_key="battery_event_text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("battery_event_text"),
    ),
    SaxPowerSensorEntityDescription(
        key="battery_cell_voltage_avg",
        translation_key="battery_cell_voltage_avg",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_direct("battery_cell_voltage_avg"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    entities: list[SensorEntity] = [
        (
            SaxPowerForecastSensor(coordinator, entry.entry_id, description)
            if description.key == "grid_serving_forecast"
            else SaxPowerSensor(coordinator, entry.entry_id, description)
        )
        for description in SENSOR_DESCRIPTIONS
    ]
    entities.append(
        SaxPowerEnergySensor(
            coordinator,
            entry.entry_id,
            key="energy_charged",
            translation_key="energy_charged",
            data_key="energy_charged",
            restore_fn=coordinator.restore_energy_charged,
        )
    )
    entities.append(
        SaxPowerEnergySensor(
            coordinator,
            entry.entry_id,
            key="energy_discharged",
            translation_key="energy_discharged",
            data_key="energy_discharged",
            restore_fn=coordinator.restore_energy_discharged,
        )
    )
    async_add_entities(entities)


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
        self._assign_ids("sensor", description.key)

    @property
    def native_value(self) -> StateType | datetime:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if (attributes_fn := self.entity_description.attributes_fn) is None:
            return None
        return attributes_fn(self.coordinator)


class SaxPowerForecastSensor(SaxPowerSensor):
    """PV-Prognose mit täglich aktualisiertem Datum im Anzeigenamen."""

    # Der dynamische Text ist bereits der vollständige Anzeigename und kein
    # gerätebezogener Namensbestandteil (siehe REQ-BUNDLED-DASHBOARD).
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: SaxPowerCoordinator,
        entry_id: str,
        description: SaxPowerSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry_id, description)
        # Diese abgeleitete Anzeige beschreibt keinen Messwert des SAX-
        # Geräts. Ohne Gerätezuordnung übernimmt Home Assistant ihren
        # dynamischen Namen unverändert, statt "SAX Power Home" voranzustellen.
        self._attr_device_info = None

    @property
    def name(self) -> str | None:
        """Liefert den übersetzten Namen mit aktuellem Tag und Monat."""
        if self.platform_data is None:
            return None
        translation_key = self._name_translation_key
        if translation_key is None:
            return None
        translated_name = self.platform_data.platform_translations.get(translation_key)
        if translated_name is None:
            return None
        now = dt_util.now()
        return f"{translated_name} {now.day}.{now.month}."


class SaxPowerEnergySensor(RestoreEntity, SaxPowerEntity, SensorEntity):
    """Energy-Dashboard-kompatibler kWh-Zähler (geladen/entladen), siehe
    anforderung.yaml REQ-ENERGY-DASHBOARD.

    Anders als SaxPowerSensor oben nicht beschreibungsbasiert: der
    Zählerstand wird nicht nur gelesen, sondern muss über Neustarts hinweg
    per RestoreEntity in den Coordinator zurückgespielt werden (dieser
    akkumuliert selbst, siehe SaxPowerCoordinator._accumulate_energy) -
    analog zum RestoreEntity-Muster in number.py (z. B.
    SaxPowerMaxSocNumber.async_added_to_hass -> coordinator.
    async_set_max_soc(restored_value))."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(
        self,
        coordinator: SaxPowerCoordinator,
        entry_id: str,
        *,
        key: str,
        translation_key: str,
        data_key: str,
        restore_fn: Callable[[float], None],
    ) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_translation_key = translation_key
        self._assign_ids("sensor", key)
        self._data_key = data_key
        self._restore_fn = restore_fn

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        restored_value = 0.0
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = float(last_state.state)
            except TypeError, ValueError:
                restored_value = 0.0
        self._restore_fn(restored_value)

    @property
    def native_value(self) -> StateType:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._data_key)
