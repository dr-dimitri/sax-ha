"""Netzenergie-Sensoren für das Energie-Dashboard (REQ-GRID-ENERGY)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy

from custom_components.sax_power.sensor import (
    SENSOR_DESCRIPTIONS,
    SaxPowerSensor,
    SaxPowerSensorEntityDescription,
)

GRID_ENERGY_KEYS = ("energy_imported_from_grid", "energy_exported_to_grid")
COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "sax_power"


@pytest.fixture(params=GRID_ENERGY_KEYS)
def description(request: pytest.FixtureRequest) -> SaxPowerSensorEntityDescription:
    return next(item for item in SENSOR_DESCRIPTIONS if item.key == request.param)


def test_grid_energy_sensor_is_eligible_for_energy_dashboard(
    description: SaxPowerSensorEntityDescription,
) -> None:
    """REQ-GRID-ENERGY: Netzenergie ist als kumulativer kWh-Kernsensor verfügbar."""
    entity = SaxPowerSensor(MagicMock(), "entry_a", description)

    assert entity.device_class == SensorDeviceClass.ENERGY
    assert entity.state_class == SensorStateClass.TOTAL_INCREASING
    assert entity.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
    assert entity.entity_category is None
    assert entity.entity_registry_enabled_default is True
    assert entity.last_reset is None


def test_grid_energy_reads_totals_independently_of_battery_energy(
    description: SaxPowerSensorEntityDescription,
) -> None:
    """REQ-GRID-ENERGY: Gesamtnetzzähler haben eigene Werte und Entity-IDs."""
    coordinator = MagicMock()
    coordinator.data = {
        "energy_imported_from_grid": 12.345,
        "energy_exported_to_grid": 6.789,
        "energy_charged_from_grid": 2.0,
        "energy_charged_from_pv": 3.0,
        "storage_power_active": 0,
    }
    entity = SaxPowerSensor(coordinator, "entry_a", description)
    other_entry = SaxPowerSensor(coordinator, "entry_b", description)

    assert entity.native_value == coordinator.data[description.key]
    assert entity.unique_id == f"entry_a_{description.key}"
    assert other_entry.unique_id == f"entry_b_{description.key}"

    coordinator.data[description.key] += 1.0
    assert entity.native_value == coordinator.data[description.key]


@pytest.mark.parametrize("data", [None, {}, {key: None for key in GRID_ENERGY_KEYS}])
def test_grid_energy_sensor_preserves_unknown_totals(
    description: SaxPowerSensorEntityDescription,
    data: dict[str, None] | None,
) -> None:
    """REQ-GRID-ENERGY: Ein unbekannter Store-Stand wird nicht als Null angezeigt."""
    coordinator = MagicMock()
    coordinator.data = data
    entity = SaxPowerSensor(coordinator, "entry_a", description)

    assert entity.native_value is None
    assert entity.extra_state_attributes == {}


def test_grid_energy_sensor_exposes_its_own_accounting_period(
    description: SaxPowerSensorEntityDescription,
) -> None:
    """REQ-GRID-ENERGY: Beide Netzzähler zeigen Zählbeginn und Rechenverfahren."""
    started_at = datetime(2026, 9, 7, 10, tzinfo=UTC).isoformat()
    coordinator = MagicMock()
    coordinator.data = {
        "grid_energy_attributes": {
            "accounting_started_at": started_at,
            "integration_method": "left_riemann_sum",
        },
        "energy_origin_attributes": {
            "origin_accounting_started_at": "2026-01-01T00:00:00+00:00",
        },
    }
    entity = SaxPowerSensor(coordinator, "entry_a", description)

    assert entity.extra_state_attributes == {
        "accounting_started_at": started_at,
        "integration_method": "left_riemann_sum",
    }


@pytest.mark.parametrize("filename", ["strings.json", "translations/de.json"])
def test_german_grid_energy_names_distinguish_total_grid_energy(filename: str) -> None:
    """REQ-GRID-ENERGY: Gesamtnetzbezug und Batterieladung sind unterscheidbar."""
    data = json.loads((COMPONENT_DIR / filename).read_text(encoding="utf-8"))
    sensors = data["entity"]["sensor"]

    assert sensors["energy_imported_from_grid"]["name"] == "Netzbezug gesamt"
    assert sensors["energy_exported_to_grid"]["name"] == "Netzeinspeisung gesamt"
    assert (
        sensors["energy_charged_from_grid"]["name"] == "Geladene Energie aus dem Netz"
    )


def test_english_grid_energy_names_distinguish_total_grid_energy() -> None:
    """REQ-GRID-ENERGY: Beide Netzsensoren sind auch auf Englisch übersetzt."""
    data = json.loads(
        (COMPONENT_DIR / "translations/en.json").read_text(encoding="utf-8")
    )
    sensors = data["entity"]["sensor"]

    assert sensors["energy_imported_from_grid"]["name"] == "Total grid import"
    assert sensors["energy_exported_to_grid"]["name"] == "Total grid export"
    assert sensors["energy_charged_from_grid"]["name"] == "Charged energy from grid"
