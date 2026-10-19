"""REQ-DIAGNOSTICS: vollständige, nebenwirkungsfreie Lade- und Tarifdiagnose."""

from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from datetime import UTC, date, datetime
from datetime import time as dt_time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_DASHBOARD_TARIFF_PROFILES,
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_GRID_SERVING_PV_FORECAST_SENSOR,
    CONF_PRICE_ATTRIBUTE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    CONF_VUE_DASHBOARD_VERSION,
    DATA_COORDINATOR,
    DOMAIN,
    economics_tou_window_key,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.diagnostics import async_get_config_entry_diagnostics
from custom_components.sax_power.domain.economics_amortization import DayEconomicsResult
from custom_components.sax_power.infrastructure.control_store import ControlConfig


def _make_coordinator(
    hass: HomeAssistant, *, data: dict[str, Any] | None = None
) -> tuple[MockConfigEntry, SaxPowerCoordinator, MagicMock]:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    client.read_holding_registers = AsyncMock()
    client.write_register = AsyncMock()
    client.write_registers = AsyncMock()
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="diagnostics_configuration",
    )
    coordinator.data = {"soc": 42, "storage_power_active": -500}
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="diagnostics_configuration",
        data={"host": "192.168.1.42", "port": 502, **(data or {})},
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}
    return entry, coordinator, client


async def test_export_uses_current_control_configuration_instead_of_legacy_entry(
    hass: HomeAssistant,
) -> None:
    """REQ-DIAGNOSTICS: Nachtladegrenzen und Monate stammen aus dem Store."""
    entry, coordinator, _client = _make_coordinator(
        hass,
        data={
            "timed_charge_min_soc": 0,
            "timed_charge_max_soc": 100,
            "timed_charge_months": [1],
            "grid_serving_start": "00:00:00",
        },
    )
    coordinator._apply_control_config(
        ControlConfig(
            max_soc=85,
            timed_charge_enabled=True,
            timed_charge_start=dt_time(1),
            timed_charge_end=dt_time(5),
            timed_charge_months=frozenset({12, 10, 11}),
            timed_charge_min_soc=25,
            timed_charge_max_soc=75,
            grid_serving_enabled=True,
            grid_serving_start=dt_time(11, 30),
            grid_serving_end=dt_time(14, 45),
            grid_serving_months=frozenset({8, 6, 7}),
            grid_serving_forecast_threshold_kwh=7.5,
            price_charge_enabled=False,
            price_charge_strategy="relative",
            price_charge_max_price=0.2,
            price_charge_neutral_price=0.1234,
            price_charge_hours=4,
            unresolved_fields=frozenset({"timed_charge_end", "max_soc"}),
        )
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["schema_version"] == 2
    assert (
        datetime.fromisoformat(diagnostics["captured_at"]).utcoffset().total_seconds()
        == 0
    )
    assert diagnostics["timezone"] == hass.config.time_zone
    assert diagnostics["control_config"] == {
        "max_soc": 85,
        "timed_charge_enabled": True,
        "timed_charge_start": "01:00:00",
        "timed_charge_end": "05:00:00",
        "timed_charge_months": [10, 11, 12],
        "timed_charge_min_soc": 25,
        "timed_charge_max_soc": 75,
        "grid_serving_enabled": True,
        "grid_serving_start": "11:30:00",
        "grid_serving_end": "14:45:00",
        "grid_serving_months": [6, 7, 8],
        "grid_serving_forecast_threshold_kwh": 7.5,
        "price_charge_enabled": False,
        "price_charge_strategy": "relative",
        "price_charge_max_price": 0.2,
        "price_charge_neutral_price": 0.1234,
        "price_charge_hours": 4,
        "unresolved_fields": ["max_soc", "timed_charge_end"],
    }
    assert diagnostics["state"]["effective_timed_charge_max_soc"] == 75
    assert diagnostics["state"]["timed_charge_uses_tariff"] is False
    assert diagnostics["state"]["bridge_charge_enabled"] is False
    assert "entry_data" not in diagnostics
    assert "entry_options" not in diagnostics
    assert diagnostics["connection"]["host"] == "**REDACTED**"
    assert diagnostics["connection"]["port"] == 502
    json.dumps(diagnostics, allow_nan=False)


async def test_export_preserves_all_raw_tariff_windows_including_invalid_input(
    hass: HomeAssistant,
) -> None:
    """REQ-DIAGNOSTICS: Fehlkonfigurationen bleiben neben dem Tarifmodell sichtbar."""
    entry, coordinator, _client = _make_coordinator(hass)
    windows = {
        economics_tou_window_key(1): {
            "start": "01:00:00",
            "end": "05:00:00",
            "price_eur_kwh": 0.1909,
        },
        economics_tou_window_key(2): {
            "start": "13:15:00",
            "end": "14:45:00",
            "price_eur_kwh": 0.21,
        },
        economics_tou_window_key(3): {
            "start": "25:00",
            "end": "26:00",
            "price_eur_kwh": "ungültig",
        },
    }
    coordinator.options = {
        CONF_ECONOMICS_TARIFF_TYPE: "time_of_use",
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.35,
        CONF_BRIDGE_CHARGE_ENABLED: True,
        CONF_PV_FORECAST_SENSOR: "sensor.pv_start",
        **windows,
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    configuration = diagnostics["tariff"]["configuration"]
    assert configuration[CONF_ECONOMICS_TARIFF_TYPE] == "time_of_use"
    assert configuration[CONF_ECONOMICS_FEED_IN_PRICE] == 0.08
    assert configuration[CONF_ECONOMICS_TOU_BASE_PRICE] == 0.35
    for key, raw_window in windows.items():
        assert configuration[key] == raw_window
    assert diagnostics["state"]["timed_charge_uses_tariff"] is True
    assert diagnostics["state"]["bridge_charge_enabled"] is True


async def test_export_exposes_selected_price_attribute_units_and_forecast_sources(
    hass: HomeAssistant,
) -> None:
    """REQ-DIAGNOSTICS: Quellen und Skalierung erklären fehlende Preis-/PV-Werte."""
    entry, coordinator, _client = _make_coordinator(hass)
    coordinator.options = {
        CONF_ECONOMICS_TARIFF_TYPE: "dynamic",
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_PRICE_SENSOR: "sensor.preis",
        CONF_PRICE_ATTRIBUTE: "selected_prices",
        CONF_PRICE_UNIT: "ct_kwh",
        CONF_PV_FORECAST_SENSOR: "sensor.pv_prognose",
        CONF_PV_FORECAST_FACTOR: 0.75,
        CONF_GRID_SERVING_PV_FORECAST_SENSOR: "sensor.pv_tag",
    }
    slots = [{"start": "2026-10-19T01:00:00+02:00", "value": 19.09}]
    hass.states.async_set(
        "sensor.preis",
        "19.09",
        {
            "unit_of_measurement": "ct/kWh",
            "selected_prices": slots,
            "raw_today": [{"value": 99}],
            "friendly_name": "Privater Anzeigename",
            "latitude": 48.123,
        },
    )
    hass.states.async_set("sensor.pv_prognose", "8.5", {"unit_of_measurement": "kWh"})
    hass.states.async_set("sensor.pv_tag", "12.3", {"unit_of_measurement": "kWh"})

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    config = diagnostics["tariff"]["configuration"]
    for key, value in coordinator.options.items():
        assert config[key] == value
    sources = diagnostics["source_states"]
    price = sources["price"]
    price_state = hass.states.get("sensor.preis")
    assert price["entity_id"] == "sensor.preis"
    assert price["state"] == "19.09"
    assert price["available"] is True
    assert price["unit_of_measurement"] == "ct/kWh"
    assert price["last_updated"] == price_state.last_updated.isoformat()
    assert price["last_changed"] == price_state.last_changed.isoformat()
    assert price["attributes"] == {"selected_prices": slots}
    assert sources["pv_forecast"]["entity_id"] == "sensor.pv_prognose"
    assert sources["pv_forecast"]["state"] == "8.5"
    assert sources["pv_forecast"]["unit_of_measurement"] == "kWh"
    assert sources["grid_serving_pv_forecast"]["entity_id"] == "sensor.pv_tag"
    assert sources["grid_serving_pv_forecast"]["state"] == "12.3"
    assert "Privater Anzeigename" not in json.dumps(diagnostics)


async def test_export_automatic_price_attributes_omit_unrelated_sensor_metadata(
    hass: HomeAssistant,
) -> None:
    """REQ-DIAGNOSTICS: Nur vom Preisparser unterstützte Attribute exportieren."""
    entry, coordinator, _client = _make_coordinator(hass)
    coordinator.options = {CONF_PRICE_SENSOR: "sensor.preis"}
    relevant = {
        "raw_today": [{"value": 0.19}],
        "raw_tomorrow": [],
        "prices": [{"price": 0.22}],
    }
    hass.states.async_set(
        "sensor.preis",
        "0.19",
        {**relevant, "attribution": "unnötig", "device_serial_number": "geheim"},
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["source_states"]["price"]["attributes"] == relevant


async def test_export_omits_identifiers_profiles_and_daily_history(
    hass: HomeAssistant,
) -> None:
    """REQ-DIAGNOSTICS: Identifikatoren und nicht aktive UI-Daten helfen nicht."""
    entry, coordinator, _client = _make_coordinator(
        hass,
        data={CONF_VUE_DASHBOARD_VERSION: "asset-hash-irrelevant"},
    )
    coordinator.data["sun_serial_number"] = "SAX-SERIAL-PRIVATE"
    coordinator.options = {
        CONF_ECONOMICS_TARIFF_TYPE: "fixed",
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.3,
        CONF_DASHBOARD_TARIFF_PROFILES: {
            "dynamic": {CONF_PRICE_SENSOR: "sensor.alte_inaktive_quelle"}
        },
        "unrelated_ui_setting": "ui-private-marker",
    }
    coordinator._economics_day_results = (
        DayEconomicsResult(date(2026, 10, 18), 1.2, 3, 0, 2, 0),
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    encoded = json.dumps(diagnostics)
    for private in (
        "SAX-SERIAL-PRIVATE",
        "asset-hash-irrelevant",
        "sensor.alte_inaktive_quelle",
        "ui-private-marker",
        "day_results",
    ):
        assert private not in encoded
    assert diagnostics["coordinator_data"]["soc"] == 42
    assert "store_write_blocked" in diagnostics["economics"]
    assert "priced_charge_kwh" in diagnostics["economics"]


async def test_export_is_detached_and_does_not_change_tariff_or_coordinator(
    hass: HomeAssistant,
) -> None:
    """REQ-DIAGNOSTICS: Diagnose verändert weder Messdaten noch Tarifcache."""
    entry, coordinator, _client = _make_coordinator(hass)
    moment = datetime(2026, 10, 19, 0, 0, tzinfo=UTC)
    coordinator.data["nested"] = {"samples": [{"at": moment, "soc": 42}]}
    coordinator.options = {
        CONF_ECONOMICS_TARIFF_TYPE: "fixed",
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.3,
    }
    before = deepcopy(coordinator.data)
    before_tariff_result = coordinator.tariff_provider.last_result

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert coordinator.data == before
    assert coordinator.tariff_provider.last_result is before_tariff_result
    assert diagnostics["coordinator_data"]["nested"]["samples"][0]["at"] == (
        moment.isoformat()
    )
    diagnostics["coordinator_data"]["nested"]["samples"][0]["soc"] = 0
    diagnostics["tariff"]["configuration"][CONF_ECONOMICS_FEED_IN_PRICE] = 0
    assert coordinator.data == before
    assert coordinator.options[CONF_ECONOMICS_FEED_IN_PRICE] == 0.08
    json.dumps(diagnostics, allow_nan=False)


async def test_export_stays_responsive_without_modbus_or_service_calls_under_lock(
    hass: HomeAssistant,
) -> None:
    """REQ-DIAGNOSTICS: Export wartet nicht auf den Geräteschreibpfad."""
    entry, coordinator, client = _make_coordinator(hass)
    async with coordinator._charge_control_lock:
        async with coordinator._write_lock:
            with patch.object(
                type(hass.services), "async_call", new_callable=AsyncMock
            ) as service:
                diagnostics = await asyncio.wait_for(
                    async_get_config_entry_diagnostics(hass, entry), timeout=0.5
                )
                service.assert_not_called()

    assert diagnostics["charge_control"]["writer"]["control_lock_locked"] is True
    assert diagnostics["charge_control"]["writer"]["modbus_lock_locked"] is True
    client.connect.assert_not_called()
    client.read_holding_registers.assert_not_called()
    client.write_register.assert_not_called()
    client.write_registers.assert_not_called()


@pytest.mark.parametrize("source_state", [None, "unknown", "unavailable"])
async def test_export_handles_unconfigured_control_and_missing_sources(
    hass: HomeAssistant, source_state: str | None
) -> None:
    """REQ-DIAGNOSTICS: Fehlende Konfiguration bleibt als solche erkennbar."""
    entry, coordinator, _client = _make_coordinator(hass)
    coordinator.data = None
    coordinator.options = {
        CONF_PRICE_SENSOR: "sensor.preis_fehlt",
        CONF_PV_FORECAST_SENSOR: "sensor.pv_fehlt",
    }
    if source_state is not None:
        hass.states.async_set("sensor.preis_fehlt", source_state)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["control_config"]["timed_charge_min_soc"] is None
    assert diagnostics["control_config"]["timed_charge_months"] == list(range(1, 13))
    assert diagnostics["source_states"]["price"]["state"] == source_state
    assert diagnostics["source_states"]["price"]["available"] is False
    assert diagnostics["source_states"]["pv_forecast"]["state"] is None
    assert diagnostics["source_states"]["pv_forecast"]["available"] is False
    assert diagnostics["source_states"]["grid_serving_pv_forecast"]["entity_id"] is None
    assert diagnostics["state"]["control_config_status"] == "missing"
    json.dumps(diagnostics, allow_nan=False)


@pytest.mark.parametrize("tariff_type", ["fixed", "dynamic"])
@pytest.mark.parametrize(
    ("option_key", "invalid_value"),
    [
        (CONF_PRICE_ATTRIBUTE, ["raw_today"]),
        (CONF_PRICE_UNIT, {"unit": "ct_kwh"}),
        (CONF_PRICE_UNIT, ["ct_kwh"]),
        (CONF_PRICE_SENSOR, ["sensor.preis"]),
    ],
    ids=["attribute_list", "unit_dict", "unit_list", "sensor_list"],
)
async def test_export_reports_invalid_source_option_types_without_side_effects(
    hass: HomeAssistant,
    tariff_type: str,
    option_key: str,
    invalid_value: Any,
) -> None:
    """REQ-DIAGNOSTICS: Auch defekte Quelloptionen müssen diagnostizierbar sein."""
    entry, coordinator, client = _make_coordinator(hass)
    coordinator.options = {
        CONF_ECONOMICS_TARIFF_TYPE: tariff_type,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.3,
        CONF_PRICE_SENSOR: "sensor.preis",
        CONF_PRICE_ATTRIBUTE: "raw_today",
        CONF_PRICE_UNIT: "ct_kwh",
        option_key: invalid_value,
    }
    hass.states.async_set(
        "sensor.preis",
        "19.09",
        {
            "unit_of_measurement": "ct/kWh",
            "raw_today": [{"start": "2026-10-19T01:00:00+02:00", "value": 19.09}],
        },
    )
    before_options = deepcopy(coordinator.options)
    before_data = deepcopy(coordinator.data)
    before_tariff_result = coordinator.tariff_provider.last_result

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    tariff = diagnostics["tariff"]
    assert tariff["source_configuration_errors"] == {option_key: "expected_string"}
    assert tariff["configuration"][option_key] == invalid_value
    if tariff_type == "fixed":
        assert tariff["quote_price_eur_kwh"] == 0.3
        assert tariff["quote_unavailable_reason"] is None
    else:
        assert tariff["quote_price_eur_kwh"] is None
        assert tariff["quote_unavailable_reason"] == "tariff_incomplete"
    if option_key == CONF_PRICE_SENSOR:
        assert diagnostics["source_states"]["price"]["state"] is None
        assert diagnostics["source_states"]["price"]["available"] is False
    assert coordinator.options == before_options
    assert coordinator.data == before_data
    assert coordinator.tariff_provider.last_result is before_tariff_result
    client.connect.assert_not_called()
    client.read_holding_registers.assert_not_called()
    client.write_register.assert_not_called()
    client.write_registers.assert_not_called()
    json.dumps(diagnostics, allow_nan=False)
