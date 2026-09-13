"""Configuration and public sensor contract for REQ-BRIDGE-CHARGE."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.config_flow import STEP_OPTIONS_SCHEMA
from custom_components.sax_power.const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_GRID_SERVING_PV_FORECAST_SENSOR,
    CONF_PRICE_SENSOR,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    DOMAIN,
)
from custom_components.sax_power.domain.tariff import TariffType
from custom_components.sax_power.sensor import SENSOR_DESCRIPTIONS, SaxPowerSensor

BRIDGE_FIELDS = (CONF_BRIDGE_CHARGE_ENABLED,)
BRIDGE_STATES = (
    "off",
    "waiting_for_data",
    "planned",
    "charging",
    "not_needed",
    "insufficient",
    "paused",
    "complete",
)
COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "sax_power"


def _entry(
    hass: HomeAssistant, options: dict[str, Any] | None = None
) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.50"},
        options=options or {},
        unique_id="bridge-configuration-test",
    )
    entry.add_to_hass(hass)
    return entry


def _suggested(schema: Any) -> dict[str, Any]:
    return {
        key.schema: key.description["suggested_value"]
        for key in schema.schema
        if isinstance(key.description, dict) and "suggested_value" in key.description
    }


async def test_unchanged_options_keep_bridge_disabled_without_a_pv_assumption(
    hass: HomeAssistant,
) -> None:
    entry = _entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_BRIDGE_CHARGE_ENABLED] is False
    assert CONF_PV_FORECAST_SENSOR not in entry.options
    assert entry.options[CONF_ECONOMICS_TARIFF_TYPE] == TariffType.DISABLED.value


async def test_enabling_requires_explicit_pv_start_and_preserves_edits_after_error(
    hass: HomeAssistant,
) -> None:
    entry = _entry(hass)
    submitted = {
        CONF_BRIDGE_CHARGE_ENABLED: True,
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
        CONF_PV_FORECAST_FACTOR: 70,
    }
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], submitted
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {CONF_PV_FORECAST_SENSOR: "bridge_pv_start_required"}
    assert entry.options == {}
    suggested = _suggested(result["data_schema"])
    for key, value in submitted.items():
        assert suggested[key] == value

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**submitted, CONF_PV_FORECAST_SENSOR: "sensor.pv_forecast"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert CONF_ECONOMICS_FEED_IN_PRICE not in entry.options
    assert CONF_ECONOMICS_TOU_BASE_PRICE not in entry.options
    assert entry.options[CONF_BRIDGE_CHARGE_ENABLED] is True
    assert entry.options[CONF_PV_FORECAST_SENSOR] == "sensor.pv_forecast"
    assert entry.options[CONF_PV_FORECAST_FACTOR] == 70


@pytest.mark.parametrize(
    "tariff_type", [TariffType.DISABLED, TariffType.FIXED, TariffType.DYNAMIC]
)
async def test_tariff_source_requires_time_of_use_before_saving(
    hass: HomeAssistant, tariff_type: TariffType
) -> None:
    entry = _entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_BRIDGE_CHARGE_ENABLED: True,
            CONF_PV_FORECAST_SENSOR: "sensor.pv_forecast",
            CONF_ECONOMICS_TARIFF_TYPE: tariff_type.value,
            CONF_PRICE_SENSOR: "sensor.energy_price",
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {CONF_ECONOMICS_TARIFF_TYPE: "bridge_tariff_required"}
    assert entry.options == {}


@pytest.mark.parametrize(
    "pv_sensor",
    [
        "sensor.pv_forecast_today",
        "sensor.pv_forecast_remaining_today",
    ],
)
async def test_explicit_sources_survive_save_and_reopening(
    hass: HomeAssistant, pv_sensor: str
) -> None:
    """REQ-BRIDGE-CHARGE: Die separate Ladepausenquelle bleibt unabhängig."""
    tariff_options = {
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.3,
    }
    entry = _entry(hass, tariff_options)
    bridge_options = {
        CONF_BRIDGE_CHARGE_ENABLED: True,
        CONF_PV_FORECAST_SENSOR: pv_sensor,
        CONF_GRID_SERVING_PV_FORECAST_SENSOR: "sensor.pv_pause_remaining_today",
    }
    result = await hass.config_entries.options.async_init(entry.entry_id)
    first_page = {
        **bridge_options,
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], first_page
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    for key, value in tariff_options.items():
        assert entry.options[key] == value
    for key, value in bridge_options.items():
        assert entry.options[key] == value

    reopened = await hass.config_entries.options.async_init(entry.entry_id)
    suggested = _suggested(reopened["data_schema"])
    for key, value in bridge_options.items():
        assert suggested[key] == value


async def test_disabling_allows_removing_pv_source_and_changing_tariff(
    hass: HomeAssistant,
) -> None:
    entry = _entry(
        hass,
        {
            CONF_BRIDGE_CHARGE_ENABLED: True,
            CONF_PV_FORECAST_SENSOR: "sensor.pv_forecast",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
        },
    )
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_BRIDGE_CHARGE_ENABLED: False,
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DISABLED.value,
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_BRIDGE_CHARGE_ENABLED] is False
    assert CONF_PV_FORECAST_SENSOR not in entry.options


def test_bridge_reuses_pv_sensor_selection_without_alternative_deadline_sources() -> (
    None
):
    fields = {key.schema: value for key, value in STEP_OPTIONS_SCHEMA.schema.items()}
    selector = fields[CONF_PV_FORECAST_SENSOR]
    assert selector.config["domain"] == ["sensor"]
    assert selector.config["multiple"] is False
    assert (
        not {
            "bridge_charge_window_source",
            "bridge_pv_start_sensor",
            "bridge_pv_start_time",
        }
        & fields.keys()
    )


@pytest.mark.parametrize("status", [*BRIDGE_STATES, None])
def test_bridge_sensor_exposes_short_state_and_full_explanation(
    status: str | None,
) -> None:
    description = next(
        item for item in SENSOR_DESCRIPTIONS if item.key == "bridge_charge_plan"
    )
    coordinator = MagicMock()
    attributes = {
        "message": "Die Planung erläutert alle Zeitpunkte ausführlich. " * 8,
        "observation_minutes": 25.5,
        "charge_start": "2026-09-14T01:00:00+00:00",
        "charge_end": "2026-09-14T02:00:00+00:00",
        "pv_start": "2026-09-14T05:00:00+00:00",
    }
    coordinator.data = {
        "bridge_charge_plan": status,
        "bridge_charge_plan_attributes": attributes,
    }
    entity = SaxPowerSensor(coordinator, "bridge-test", description)

    assert entity.unique_id == "bridge-test_bridge_charge_plan"
    assert entity.device_class == SensorDeviceClass.ENUM
    assert entity.options == list(BRIDGE_STATES)
    assert description.state_class is None
    assert description.native_unit_of_measurement is None
    assert description.entity_category is None
    assert entity.native_value == status
    assert entity.extra_state_attributes == attributes
    assert len(entity.extra_state_attributes["message"]) > 255
    assert entity.extra_state_attributes is not attributes
    coordinator.data = None
    assert entity.native_value is None
    assert entity.extra_state_attributes == {}


@pytest.mark.parametrize(
    "filename", ["strings.json", "translations/de.json", "translations/en.json"]
)
def test_bridge_translations_cover_configuration_errors_and_sensor_states(
    filename: str,
) -> None:
    translated = json.loads((COMPONENT_DIR / filename).read_text(encoding="utf-8"))
    sensor = translated["entity"]["sensor"]["bridge_charge_plan"]
    assert sensor["name"].strip()
    assert set(sensor["state"]) == set(BRIDGE_STATES)
    assert all(value.strip() for value in sensor["state"].values())
    form = translated["options"]["step"]["init"]
    assert all(form["data"][key].strip() for key in BRIDGE_FIELDS)
    assert all(form["data_description"][key].strip() for key in BRIDGE_FIELDS)
    errors = translated["options"]["error"]
    assert errors["bridge_pv_start_required"].strip()
    assert errors["bridge_tariff_required"].strip()
