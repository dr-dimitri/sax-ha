"""REQ-HEMS-CONFIGURATION: opt-in migration and responsive entity services."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.const import DOMAIN
from custom_components.sax_power.infrastructure.control_store import (
    ControlConfig,
    ControlConfigStore,
)
from custom_components.sax_power.select import SaxPowerTimedChargeModeSelect

from .test_config_flow import _options_step
from .test_month_switch_response import coordinator as coordinator


async def _source_step(hass, entry: MockConfigEntry, provider: str) -> dict:
    flow = await _options_step(hass, entry, "hems")
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"hems_pv_provider": provider}
    )
    assert flow["step_id"] == "hems_source"
    return flow


async def _settings_step(hass, entry: MockConfigEntry) -> dict:
    source = MockConfigEntry(domain="pv_forecast")
    source.add_to_hass(hass)
    flow = await _source_step(hass, entry, "pv_forecast")
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"hems_pv_entry": source.entry_id}
    )
    assert flow["step_id"] == "hems_settings"
    return flow


@pytest.mark.parametrize("saved", [None, "unknown", "standard", "adaptive", 123])
async def test_old_store_never_activates_adaptive_implicitly(hass, saved) -> None:
    store = ControlConfigStore(hass, "hems_config")
    raw = {"max_soc": 80, "timed_charge_min_soc": 20}
    if saved is not None:
        raw["timed_charge_mode"] = saved
    with patch(
        "custom_components.sax_power.infrastructure.control_store.async_load_checked",
        AsyncMock(return_value=raw),
    ):
        result = await store.async_load()
    assert result.config.sanitized().timed_charge_mode == (
        "adaptive" if saved == "adaptive" else "standard"
    )
    assert result.config.sanitized().timed_charge_min_soc == 20
    assert result.config.sanitized().timed_charge_max_soc == 80


async def test_mode_acceptance_does_not_wait_for_device_ack(coordinator) -> None:
    async with coordinator._charge_control_lock:
        await asyncio.wait_for(coordinator.async_set_timed_charge_mode("adaptive"), 0.2)
        assert coordinator.timed_charge_mode == "adaptive"
        assert coordinator._control_store._pending["timed_charge_mode"] == "adaptive"
        coordinator.client.write_register.assert_not_awaited()
    await coordinator._month_control_task


async def test_mode_rejects_unknown_and_shutdown_before_mutating(coordinator) -> None:
    with pytest.raises(ValueError):
        await coordinator.async_set_timed_charge_mode("smart")
    assert coordinator.timed_charge_mode == "standard"
    await coordinator.async_shutdown(reset_device=False)
    with pytest.raises(HomeAssistantError):
        await coordinator.async_set_timed_charge_mode("adaptive")
    assert coordinator.timed_charge_mode == "standard"


async def test_select_reads_persisted_mode_without_restore_override(
    coordinator,
) -> None:
    coordinator._apply_control_config(
        ControlConfig(timed_charge_mode="adaptive").sanitized()
    )
    entity = SaxPowerTimedChargeModeSelect(coordinator, coordinator.entry_id)
    assert entity.current_option == "adaptive"
    assert entity.options == ["standard", "adaptive"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("hems_charge_efficiency", 0),
        ("hems_charge_efficiency", 1.1),
        ("hems_discharge_efficiency", -1),
        ("hems_solcast_max_age_hours", 25),
        ("hems_solcast_max_age_hours", 0),
        ("hems_pv_provider", "unsupported"),
    ],
)
async def test_source_settings_reject_invalid_ranges(hass, field, value) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "127.0.0.1"})
    entry.add_to_hass(hass)
    if field == "hems_pv_provider":
        flow = await _options_step(hass, entry, "hems")
        data = {field: value}
    elif field == "hems_solcast_max_age_hours":
        source = MockConfigEntry(domain="solcast_solar")
        source.add_to_hass(hass)
        flow = await _source_step(hass, entry, "solcast_solar")
        data = {"hems_pv_entry": source.entry_id, field: value}
    else:
        flow = await _settings_step(hass, entry)
        data = {"efficiency": {field: value}}
    with pytest.raises((vol.Invalid, InvalidData)):
        await hass.config_entries.options.async_configure(flow["flow_id"], data)
    assert entry.options == {}


@pytest.mark.parametrize("provider", ["pv_forecast", "solcast_solar"])
async def test_options_validate_provider_entry_and_accept_matching_source(
    hass, provider
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "127.0.0.1"})
    entry.add_to_hass(hass)
    source = MockConfigEntry(domain=provider)
    source.add_to_hass(hass)
    flow = await _source_step(hass, entry, provider)
    invalid = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"hems_pv_entry": entry.entry_id}
    )
    assert invalid["type"] == FlowResultType.FORM
    assert invalid["errors"] == {"hems_pv_entry": "hems_pv_entry_invalid"}
    valid = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"hems_pv_entry": source.entry_id}
    )
    assert valid["step_id"] == "hems_settings"
    assert entry.options == {}
    valid = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {"efficiency": {"hems_charge_efficiency": 1, "hems_discharge_efficiency": 0.9}},
    )
    assert valid["type"] == FlowResultType.CREATE_ENTRY
    assert valid["data"]["hems_charge_efficiency"] == 1
    assert valid["data"]["hems_pv_entry"] == source.entry_id
    assert "forecast" not in valid["data"]
    assert "efficiency" not in valid["data"]


async def test_nan_efficiency_is_rejected_before_options_are_saved(hass) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "127.0.0.1"})
    entry.add_to_hass(hass)
    flow = await _settings_step(hass, entry)
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            flow["flow_id"], {"efficiency": {"hems_charge_efficiency": float("nan")}}
        )
    assert entry.options == {}


@pytest.mark.parametrize("kind", ["peak_time", "foreign_platform", "disabled"])
async def test_options_reject_non_usable_solcast_timestamp_identity(hass, kind):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "127.0.0.1"})
    source = MockConfigEntry(domain="solcast_solar")
    entry.add_to_hass(hass)
    source.add_to_hass(hass)
    registry = er.async_get(hass)
    timestamp = registry.async_get_or_create(
        "sensor",
        "other" if kind == "foreign_platform" else "solcast_solar",
        "peak_time_tomorrow" if kind == "peak_time" else "lastupdated",
        config_entry=source,
    )
    if kind == "disabled":
        registry.async_update_entity(
            timestamp.entity_id, disabled_by=er.RegistryEntryDisabler.USER
        )
    flow = await _source_step(hass, entry, "solcast_solar")
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {
            "hems_pv_entry": source.entry_id,
            "hems_solcast_timestamp": timestamp.entity_id,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"hems_solcast_timestamp": "hems_pv_entry_invalid"}
    assert not entry.options


@pytest.mark.parametrize("persisted_identity", [False, True])
async def test_options_resolve_rename_and_persist_registry_identity(
    hass, persisted_identity
):
    """Legacy entity IDs migrate; saved registry IDs survive name reuse."""
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "127.0.0.1"})
    source = MockConfigEntry(domain="solcast_solar")
    entry.add_to_hass(hass)
    source.add_to_hass(hass)
    registry = er.async_get(hass)
    timestamp = registry.async_get_or_create(
        "sensor", "solcast_solar", "lastupdated", config_entry=source
    )
    previous = timestamp.entity_id
    saved = {
        "hems_pv_provider": "solcast_solar",
        "hems_pv_entry": source.entry_id,
        "hems_solcast_timestamp": previous,
    }
    if persisted_identity:
        saved["hems_solcast_timestamp_registry_id"] = timestamp.id
    hass.config_entries.async_update_entry(entry, options=saved)
    registry.async_update_entity(previous, new_entity_id="sensor.renamed_polled")
    if persisted_identity:
        reused = registry.async_get_or_create(
            "sensor",
            "solcast_solar",
            "peak_time_tomorrow",
            config_entry=source,
            suggested_object_id=previous.split(".", 1)[1],
        )
        assert reused.entity_id == previous
    flow = await _source_step(hass, entry, "solcast_solar")
    field = next(
        key for key in flow["data_schema"].schema if key == "hems_solcast_timestamp"
    )
    assert field.description["suggested_value"] == "sensor.renamed_polled"
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {
            "hems_pv_entry": source.entry_id,
            "hems_solcast_timestamp": "sensor.renamed_polled",
        },
    )
    assert result["step_id"] == "hems_settings"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["hems_solcast_timestamp_registry_id"] == timestamp.id
    assert result["data"]["hems_solcast_timestamp"] == "sensor.renamed_polled"


async def test_clearing_explicit_solcast_timestamp_removes_saved_identity(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "127.0.0.1"},
        options={
            "hems_pv_provider": "solcast_solar",
            "hems_solcast_timestamp": "sensor.removed",
            "hems_solcast_timestamp_registry_id": "removed-registry-id",
        },
    )
    source = MockConfigEntry(domain="solcast_solar")
    entry.add_to_hass(hass)
    source.add_to_hass(hass)
    flow = await _source_step(hass, entry, "solcast_solar")
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {"hems_pv_entry": source.entry_id},
    )
    assert result["step_id"] == "hems_settings"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert "hems_solcast_timestamp_registry_id" not in result["data"]
