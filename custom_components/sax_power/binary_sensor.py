"""Binary sensor platform for SAX Power.

Ergänzt die bestehenden Klartext-Sensoren (`*_active_text` in sensor.py) um
HA-native binary_sensor-Entities mit echter device_class-Semantik (Icons,
Zustandsfarben, maschinenlesbarer on/off-Zustand statt deutscher Klartexte),
siehe anforderung.yaml, REQ-BINARY-SENSORS. Rein additiv: die Text-Sensoren
bleiben unverändert bestehen, siehe dort für den Hintergrund.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import SaxPowerCoordinator
from .entity import SaxPowerEntity


@dataclass(frozen=True, kw_only=True)
class SaxPowerBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Binary-Sensor-Beschreibung mit Zugriffsfunktion auf den Coordinator.

    Bekommt anders als SaxPowerSensorEntityDescription.value_fn (sensor.py)
    den ganzen Coordinator statt nur coordinator.data: ein Teil der hier
    abgebildeten Zustände (max_soc_clamped, extended_available) existiert
    nur als Coordinator-Property und wird nicht in coordinator.data
    veröffentlicht.
    """

    is_on_fn: Callable[[SaxPowerCoordinator], bool | None]


def _data_flag(key: str) -> Callable[[SaxPowerCoordinator], bool | None]:
    """Liest ein bereits in coordinator.data veröffentlichtes bool-Flag
    (siehe SaxPowerCoordinator._publish_charge_state)."""

    def is_on_fn(coordinator: SaxPowerCoordinator) -> bool | None:
        if coordinator.data is None:
            return None
        return coordinator.data.get(key)

    return is_on_fn


def _coordinator_property(
    accessor: Callable[[SaxPowerCoordinator], bool],
) -> Callable[[SaxPowerCoordinator], bool | None]:
    """Liest eine Coordinator-Property, die unabhängig von coordinator.data
    existiert (max_soc_clamped, extended_available)."""

    def is_on_fn(coordinator: SaxPowerCoordinator) -> bool | None:
        if coordinator.data is None:
            return None
        return accessor(coordinator)

    return is_on_fn


def _battery_charging(coordinator: SaxPowerCoordinator) -> bool | None:
    if coordinator.data is None:
        return None
    power = coordinator.data.get("storage_power_active")
    if power is None:
        return None
    return power < 0


def _battery_problem(coordinator: SaxPowerCoordinator) -> bool | None:
    """True, sobald Speicher oder Akku ein Ereignis != Normalbetrieb (Code 0)
    melden. Vergleicht bewusst die rohen Ereignis-Codes (storage_event/
    battery_event) statt der übersetzten *_text-Werte - robuster gegen
    künftige Label-Änderungen (siehe STORAGE_EVENT_LABELS/BATTERY_EVENT_LABELS
    in const.py). Beide Codes stammen aus demselben SunSpec-Block und sind
    deshalb entweder beide oder keiner vorhanden (siehe
    REQ-EXTENDED-MODE-RESILIENCE)."""
    if coordinator.data is None:
        return None
    storage_event = coordinator.data.get("storage_event")
    battery_event = coordinator.data.get("battery_event")
    if storage_event is None and battery_event is None:
        return None
    return bool(storage_event) or bool(battery_event)


BINARY_SENSOR_DESCRIPTIONS: tuple[SaxPowerBinarySensorEntityDescription, ...] = (
    SaxPowerBinarySensorEntityDescription(
        key="battery_charging",
        translation_key="battery_charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        is_on_fn=_battery_charging,
    ),
    SaxPowerBinarySensorEntityDescription(
        key="timed_charge_active",
        translation_key="timed_charge_active",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_data_flag("timed_charge_active"),
    ),
    SaxPowerBinarySensorEntityDescription(
        key="price_charge_active",
        translation_key="price_charge_active",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_data_flag("price_charge_active"),
    ),
    SaxPowerBinarySensorEntityDescription(
        key="grid_serving_active",
        translation_key="grid_serving_active",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_data_flag("grid_serving_active"),
    ),
    SaxPowerBinarySensorEntityDescription(
        key="discharge_block_active",
        translation_key="discharge_block_active",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_data_flag("discharge_block_active"),
    ),
    SaxPowerBinarySensorEntityDescription(
        key="max_soc_clamped",
        translation_key="max_soc_clamped",
        is_on_fn=_coordinator_property(lambda coordinator: coordinator.max_soc_clamped),
    ),
    SaxPowerBinarySensorEntityDescription(
        key="extended_mode_available",
        translation_key="extended_mode_available",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_coordinator_property(
            lambda coordinator: coordinator.extended_available
        ),
    ),
    SaxPowerBinarySensorEntityDescription(
        key="battery_problem",
        translation_key="battery_problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_battery_problem,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        SaxPowerBinarySensor(coordinator, entry.entry_id, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class SaxPowerBinarySensor(SaxPowerEntity, BinarySensorEntity):
    """Generischer Binary-Sensor: Zustand wird per is_on_fn ermittelt."""

    entity_description: SaxPowerBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: SaxPowerCoordinator,
        entry_id: str,
        description: SaxPowerBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.is_on_fn(self.coordinator)
