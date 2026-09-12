"""REQ-HEMS-CONFIGURATION: zielgerichtete Bereiche und atomare Optionsänderungen."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import voluptuous as vol
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power import config_flow
from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_INVESTMENT_COST,
    CONF_ECONOMICS_PRIOR_RESULT,
    DOMAIN,
)

from .test_config_flow import _assert_frontend_can_render, _options_step
from .test_hems_configuration import _source_step


def _entry(hass, options: dict | None = None) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, data={"host": "127.0.0.1"}, options=options or {}
    )
    entry.add_to_hass(hass)
    return entry


@pytest.mark.parametrize(
    ("step_id", "submitted", "removed"),
    [
        ("dashboard", {"vue_dashboard_enabled": False}, set()),
        ("price", {"price_unit": "eur_kwh"}, {"price_sensor", "price_attribute"}),
        ("pv", {"pv_forecast_factor": 75}, {"pv_forecast_sensor"}),
        (
            "amortization",
            {},
            {CONF_ECONOMICS_INVESTMENT_COST, CONF_ECONOMICS_PRIOR_RESULT},
        ),
    ],
)
async def test_saving_one_area_preserves_other_options(
    hass, step_id, submitted, removed
):
    """Nur eigene leere Felder werden entfernt; andere Bereiche bleiben erhalten."""
    saved = {
        "vue_dashboard_enabled": True,
        "price_sensor": "sensor.strompreis",
        "price_attribute": "prices",
        "price_unit": "ct_kwh",
        "pv_forecast_sensor": "sensor.pv_morgen",
        "pv_forecast_factor": 80,
        "hems_pv_provider": "solcast_solar",
        "hems_pv_entry": "currently-unavailable",
        "hems_charge_efficiency": 0.91,
        "economics_tariff_type": "fixed",
        CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.3,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_ECONOMICS_INVESTMENT_COST: 8500.0,
        CONF_ECONOMICS_PRIOR_RESULT: 1200.0,
        "future_option": {"keep": True},
    }
    entry = _entry(hass, saved)
    result = await _options_step(hass, entry, step_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], submitted
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options == {
        key: value
        for key, value in {**saved, **submitted}.items()
        if key not in removed
    }


async def test_active_dynamic_tariff_prevents_removing_its_price_source(hass):
    saved = {
        "economics_tariff_type": "dynamic",
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        "price_sensor": "sensor.strompreis",
    }
    entry = _entry(hass, saved)
    result = await _options_step(hass, entry, "price")
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["step_id"] == "price"
    assert result["errors"] == {"price_sensor": "economics_price_sensor_required"}
    assert entry.options == saved


@pytest.mark.parametrize(
    "stage",
    ["hems_source", "hems_settings", "price", "economics_dynamic", "economics_fixed"],
)
async def test_cancelling_a_multistep_area_keeps_saved_options(hass, stage):
    saved = {"vue_dashboard_enabled": True, "economics_tariff_type": "disabled"}
    entry = _entry(hass, saved)
    if stage.startswith("hems"):
        source = MockConfigEntry(domain="pv_forecast")
        source.add_to_hass(hass)
        result = await _source_step(hass, entry, "pv_forecast")
        if stage == "hems_settings":
            result = await hass.config_entries.options.async_configure(
                result["flow_id"], {"hems_pv_entry": source.entry_id}
            )
    else:
        result = await _options_step(hass, entry, "economics")
        tariff = "fixed" if stage == "economics_fixed" else "dynamic"
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"economics_tariff_type": tariff}
        )
        if stage == "economics_dynamic":
            result = await hass.config_entries.options.async_configure(
                result["flow_id"], {"price_sensor": "sensor.neu"}
            )
    assert result["step_id"] == stage
    hass.config_entries.options.async_abort(result["flow_id"])
    assert entry.options == saved


@pytest.mark.parametrize("provider", ["pv_forecast", "solcast_solar"])
async def test_source_form_only_shows_fields_for_selected_provider(hass, provider):
    entry = _entry(hass)
    result = await _source_step(hass, entry, provider)
    schema = result["data_schema"]
    _assert_frontend_can_render(schema)
    fields = {str(key): (key, value) for key, value in schema.schema.items()}
    assert set(fields) == (
        {"hems_pv_entry", "hems_solcast_timestamp", "hems_solcast_max_age_hours"}
        if provider == "solcast_solar"
        else {"hems_pv_entry"}
    )
    marker, selector = fields["hems_pv_entry"]
    assert isinstance(marker, vol.Required)
    assert selector.config["integration"] == provider


async def test_disabling_forecast_source_clears_only_its_mapping(hass):
    unrelated = {
        "price_sensor": "sensor.price",
        "hems_solcast_max_age_hours": 3,
        "hems_history_days": "28",
        "hems_charge_efficiency": 0.91,
    }
    entry = _entry(
        hass,
        {
            **unrelated,
            "hems_pv_provider": "solcast_solar",
            "hems_pv_entry": "missing-entry",
            "hems_solcast_timestamp": "sensor.old_timestamp",
            "hems_solcast_timestamp_registry_id": "old-registry-id",
            "hems_solcast_max_age_hours": 3,
        },
    )
    result = await _options_step(hass, entry, "hems")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"hems_pv_provider": "none"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options == {**unrelated, "hems_pv_provider": "none"}


async def test_switching_from_solcast_clears_obsolete_timestamp_options(hass):
    entry = _entry(
        hass,
        {
            "hems_pv_provider": "solcast_solar",
            "hems_solcast_timestamp": "sensor.old_timestamp",
            "hems_solcast_timestamp_registry_id": "old-registry-id",
            "hems_solcast_max_age_hours": 3,
        },
    )
    source = MockConfigEntry(domain="pv_forecast")
    source.add_to_hass(hass)
    result = await _source_step(hass, entry, "pv_forecast")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"hems_pv_entry": source.entry_id}
    )
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options["hems_pv_provider"] == "pv_forecast"
    assert entry.options["hems_pv_entry"] == source.entry_id
    assert "hems_solcast_timestamp" not in entry.options
    assert "hems_solcast_timestamp_registry_id" not in entry.options
    assert entry.options["hems_solcast_max_age_hours"] == 3


@pytest.mark.parametrize("change_forecast", [False, True])
async def test_forecast_settings_sections_preserve_saved_values_and_flat_storage(
    hass, change_forecast
):
    settings = {
        "forecast": {
            "hems_archive_enabled": True,
            "hems_history_days": "28",
            "hems_forecast_mode": "auto",
            "hems_live_adjustment": True,
        },
        "efficiency": {
            "hems_charge_efficiency": 0.91,
            "hems_discharge_efficiency": 0.92,
        },
    }
    saved = {
        key: value for values in settings.values() for key, value in values.items()
    }
    entry = _entry(hass, saved)
    source = MockConfigEntry(domain="pv_forecast")
    source.add_to_hass(hass)
    result = await _source_step(hass, entry, "pv_forecast")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"hems_pv_entry": source.entry_id}
    )
    assert result["step_id"] == "hems_settings"
    _assert_frontend_can_render(result["data_schema"])
    suggested = {
        str(group): {
            str(field): field.description["suggested_value"]
            for field in section.schema.schema
        }
        for group, section in result["data_schema"].schema.items()
    }
    assert suggested == settings
    submitted = (
        {"forecast": {**settings["forecast"], "hems_archive_enabled": False}}
        if change_forecast
        else {}
    )
    if change_forecast:
        saved["hems_archive_enabled"] = False
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], submitted
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options == {
        **saved,
        "hems_pv_provider": "pv_forecast",
        "hems_pv_entry": source.entry_id,
    }


def test_options_translations_match_sections_and_fields():
    base = Path(config_flow.__file__).parent
    translations = [
        json.loads(path.read_text())
        for path in [
            base / "strings.json",
            base / "translations/de.json",
            base / "translations/en.json",
        ]
    ]
    schemas = {
        "dashboard": config_flow.STEP_DASHBOARD_OPTIONS_SCHEMA,
        "price": config_flow.STEP_PRICE_SCHEMA,
        "pv": config_flow.STEP_PV_SCHEMA,
        "hems": config_flow.STEP_HEMS_SCHEMA,
        "hems_settings": config_flow.STEP_HEMS_SETTINGS_SCHEMA,
        "economics": config_flow.STEP_ECONOMICS_SCHEMA,
        "amortization": config_flow.STEP_AMORTIZATION_SCHEMA,
    }
    for translation in translations:
        steps = translation["options"]["step"]
        assert set(steps["init"]["menu_options"]) == {
            "dashboard",
            "price",
            "pv",
            "hems",
            "economics",
            "amortization",
        }
        assert set(steps["hems_source"]["data"]) == {
            "hems_pv_entry",
            "hems_solcast_timestamp",
            "hems_solcast_max_age_hours",
        }
        for name, schema in schemas.items():
            if name == "hems_settings":
                for group, section in schema.schema.items():
                    translated = steps[name]["sections"][str(group)]
                    assert translated["name"]
                    assert set(translated["data"]) == {
                        str(key) for key in section.schema.schema
                    }
            else:
                assert set(steps[name]["data"]) == {str(key) for key in schema.schema}


async def test_dashboard_requires_an_explicit_choice(hass):
    entry = _entry(hass, {"vue_dashboard_enabled": True})
    result = await _options_step(hass, entry, "dashboard")
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert entry.options["vue_dashboard_enabled"] is True


async def test_zero_prior_result_remains_explicit(hass):
    entry = _entry(hass, {"price_sensor": "sensor.price"})
    result = await _options_step(hass, entry, "amortization")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_INVESTMENT_COST: 8500, CONF_ECONOMICS_PRIOR_RESULT: 0},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options == {
        "price_sensor": "sensor.price",
        CONF_ECONOMICS_INVESTMENT_COST: 8500,
        CONF_ECONOMICS_PRIOR_RESULT: 0,
    }


async def test_finishing_hems_preserves_a_parallel_price_change(hass):
    entry = _entry(hass, {"price_sensor": "sensor.old_price"})
    source = MockConfigEntry(domain="pv_forecast")
    source.add_to_hass(hass)
    hems = await _source_step(hass, entry, "pv_forecast")
    hems = await hass.config_entries.options.async_configure(
        hems["flow_id"], {"hems_pv_entry": source.entry_id}
    )
    price = await _options_step(hass, entry, "price")
    price = await hass.config_entries.options.async_configure(
        price["flow_id"], {"price_sensor": "sensor.new_price", "price_unit": "ct_kwh"}
    )
    assert price["type"] == FlowResultType.CREATE_ENTRY
    hems = await hass.config_entries.options.async_configure(hems["flow_id"], {})
    assert hems["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options["price_sensor"] == "sensor.new_price"
    assert entry.options["price_unit"] == "ct_kwh"
    assert entry.options["hems_pv_provider"] == "pv_forecast"
    assert entry.options["hems_pv_entry"] == source.entry_id


async def test_dynamic_tariff_rechecks_a_price_source_removed_in_parallel(hass):
    entry = _entry(hass, {"price_sensor": "sensor.old_price"})
    economics = await _options_step(hass, entry, "economics")
    economics = await hass.config_entries.options.async_configure(
        economics["flow_id"], {"economics_tariff_type": "dynamic"}
    )
    assert economics["step_id"] == "economics_dynamic"
    price = await _options_step(hass, entry, "price")
    price = await hass.config_entries.options.async_configure(price["flow_id"], {})
    assert price["type"] == FlowResultType.CREATE_ENTRY
    assert "price_sensor" not in entry.options
    economics = await hass.config_entries.options.async_configure(
        economics["flow_id"], {CONF_ECONOMICS_FEED_IN_PRICE: 0.08}
    )
    assert economics["step_id"] == "price"
    assert entry.options.get("economics_tariff_type") != "dynamic"
    economics = await hass.config_entries.options.async_configure(
        economics["flow_id"], {"price_sensor": "sensor.new_price"}
    )
    assert economics["step_id"] == "economics_dynamic"
    economics = await hass.config_entries.options.async_configure(
        economics["flow_id"], {CONF_ECONOMICS_FEED_IN_PRICE: 0.08}
    )
    assert economics["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options["price_sensor"] == "sensor.new_price"
    assert entry.options["economics_tariff_type"] == "dynamic"
