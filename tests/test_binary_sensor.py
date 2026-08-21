"""Tests für die binary_sensor-Plattform (siehe anforderung.yaml,
REQ-BINARY-SENSORS).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from custom_components.sax_power.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    SaxPowerBinarySensor,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "sax_power"


def _make_coordinator(hass) -> SaxPowerCoordinator:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    return SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
    )


def _description(key: str):
    return next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == key)


def test_binary_sensor_keys_are_unique() -> None:
    keys = [description.key for description in BINARY_SENSOR_DESCRIPTIONS]
    assert len(keys) == len(set(keys))


def _load(filename: str) -> dict:
    with (COMPONENT_DIR / filename).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_every_binary_sensor_has_translations_in_all_locales() -> None:
    keys = {description.key for description in BINARY_SENSOR_DESCRIPTIONS}
    for filename in ("strings.json", "translations/de.json", "translations/en.json"):
        data = _load(filename)
        translated_keys = set(data.get("entity", {}).get("binary_sensor", {}).keys())
        missing = keys - translated_keys
        assert not missing, f"{filename} fehlt Übersetzung für: {sorted(missing)}"


def test_is_on_fn_returns_none_before_first_update(hass) -> None:
    """Solange coordinator.data noch nie befüllt wurde (vor dem ersten
    erfolgreichen Update), muss jede Entity "nicht verfügbar" (None) statt
    eines irreführenden Zustands liefern."""
    coordinator = _make_coordinator(hass)
    assert coordinator.data is None

    for description in BINARY_SENSOR_DESCRIPTIONS:
        assert description.is_on_fn(coordinator) is None


async def test_battery_charging_reflects_storage_power_sign(hass) -> None:
    coordinator = _make_coordinator(hass)
    is_on_fn = _description("battery_charging").is_on_fn

    coordinator.data = {"storage_power_active": -500}
    assert is_on_fn(coordinator) is True

    coordinator.data = {"storage_power_active": 500}
    assert is_on_fn(coordinator) is False

    coordinator.data = {"storage_power_active": 0}
    assert is_on_fn(coordinator) is False


async def test_battery_charging_unavailable_without_extended_mode(hass) -> None:
    """Fehlt storage_power_active (SunSpec-Modus nicht erreichbar, siehe
    REQ-EXTENDED-MODE-RESILIENCE), muss der Sensor "nicht verfügbar" zeigen,
    nicht fälschlich "Aus"."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {}
    assert _description("battery_charging").is_on_fn(coordinator) is None


async def test_data_flag_entities_read_published_charge_state(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.data = {
        "timed_charge_active": True,
        "price_charge_active": False,
        "grid_serving_active": True,
    }

    assert _description("timed_charge_active").is_on_fn(coordinator) is True
    assert _description("price_charge_active").is_on_fn(coordinator) is False
    assert _description("grid_serving_active").is_on_fn(coordinator) is True


async def test_max_soc_clamped_reflects_coordinator_property(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.data = {}
    is_on_fn = _description("max_soc_clamped").is_on_fn

    assert is_on_fn(coordinator) is False
    coordinator._max_soc_clamped = True
    assert is_on_fn(coordinator) is True


async def test_extended_mode_available_reflects_coordinator_property(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.data = {}
    is_on_fn = _description("extended_mode_available").is_on_fn

    assert is_on_fn(coordinator) is True  # Default vor dem ersten Read
    coordinator._extended_available = False
    assert is_on_fn(coordinator) is False


async def test_battery_problem_true_on_nonzero_event_codes(hass) -> None:
    coordinator = _make_coordinator(hass)
    is_on_fn = _description("battery_problem").is_on_fn

    coordinator.data = {"storage_event": 0, "battery_event": 0}
    assert is_on_fn(coordinator) is False

    coordinator.data = {"storage_event": 8, "battery_event": 0}
    assert is_on_fn(coordinator) is True

    coordinator.data = {"storage_event": 0, "battery_event": 3}
    assert is_on_fn(coordinator) is True


async def test_battery_problem_unavailable_without_extended_mode(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.data = {}
    assert _description("battery_problem").is_on_fn(coordinator) is None


async def test_entity_is_on_delegates_to_description(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.data = {"timed_charge_active": True}
    entity = SaxPowerBinarySensor(
        coordinator, "test_entry_id", _description("timed_charge_active")
    )

    assert entity.is_on is True
    assert entity.unique_id == "test_entry_id_timed_charge_active"


async def test_async_setup_entry_adds_one_entity_per_description(hass) -> None:
    from unittest.mock import MagicMock as _MagicMock

    from homeassistant.config_entries import ConfigEntry

    from custom_components.sax_power.binary_sensor import async_setup_entry
    from custom_components.sax_power.const import DATA_COORDINATOR, DOMAIN

    coordinator = _make_coordinator(hass)
    coordinator.data = {}
    entry = _MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}

    added: list = []
    await async_setup_entry(hass, entry, added.extend)

    assert len(added) == len(BINARY_SENSOR_DESCRIPTIONS)
    assert all(isinstance(entity, SaxPowerBinarySensor) for entity in added)
