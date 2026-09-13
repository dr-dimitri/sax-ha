"""REQ-VUE-ELECTRICITY-TARIFF / REQ-BRIDGE-CHARGE: keep the required PV source."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power.application.tariff_profiles import options_for_tariff
from custom_components.sax_power.const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_DASHBOARD_TARIFF_PROFILES,
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_PRICE_SENSOR,
    CONF_PV_FORECAST_SENSOR,
    DATA_COORDINATOR,
    DOMAIN,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.dashboard_api import async_register_dashboard_api
from custom_components.sax_power.dashboard_tariff import CONFIGURE_COMMAND, GET_COMMAND


@pytest.fixture
async def setup(
    hass: HomeAssistant,
) -> AsyncIterator[tuple[MockConfigEntry, SaxPowerCoordinator]]:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_ECONOMICS_TARIFF_TYPE: "time_of_use",
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
            CONF_PV_FORECAST_SENSOR: "sensor.pv",
            CONF_BRIDGE_CHARGE_ENABLED: True,
        },
    )
    entry.add_to_hass(hass)
    for entity in ("sensor.pv", "sensor.pv_other"):
        hass.states.async_set(entity, "10", {"unit_of_measurement": "kWh"})
    hass.states.async_set("sensor.price", "20", {"unit_of_measurement": "ct/kWh"})
    coordinator = SaxPowerCoordinator(
        hass, MagicMock(), 64, 100, 10, entry.entry_id, options=dict(entry.options)
    )
    coordinator._timed_charge_enabled = True
    coordinator.price_planner.async_setup = MagicMock()
    coordinator.tariff_provider.async_setup = MagicMock()
    coordinator._async_enforce_grid_charge_locked = AsyncMock()
    coordinator.async_write_extended_register = AsyncMock()
    coordinator.data = {"soc": 40}
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}
    async_register_dashboard_api(hass)
    yield entry, coordinator
    await coordinator.async_shutdown()


def _profile(source: str | None) -> dict[str, Any]:
    return {
        "base_price_ct_kwh": 34,
        "feed_in_price_ct_kwh": 8,
        "windows": [],
        "pv_sensor": source,
    }


async def _configure(client: Any, entry: MockConfigEntry, **changes: Any) -> dict:
    await client.send_json_auto_id({"type": GET_COMMAND, "entry_id": entry.entry_id})
    current = await client.receive_json()
    assert current["success"]
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": current["result"]["revision"],
            "tariff_type": "time_of_use",
            **changes,
        }
    )
    return await client.receive_json()


@pytest.mark.parametrize("loaded", [False, True])
@pytest.mark.parametrize("source", [None, ""])
@pytest.mark.parametrize("master", [None, False])
async def test_clearing_required_source_never_changes_options_or_charging(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    setup,
    loaded: bool,
    source: str | None,
    master: bool | None,
) -> None:
    entry, coordinator = setup
    if not loaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    before = deepcopy(dict(entry.options))
    client = await hass_ws_client(hass)
    result = await _configure(
        client,
        entry,
        profile=_profile(source),
        **({"automation_enabled": master} if master is not None else {}),
    )
    assert result["error"]["code"] == "bridge_pv_start_required"
    assert entry.options == coordinator.options == before
    assert coordinator.timed_charge_enabled
    assert not coordinator.price_charge_enabled
    coordinator._async_enforce_grid_charge_locked.assert_not_called()


async def test_source_can_be_cleared_after_bridge_switch_is_off(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, setup
) -> None:
    entry, coordinator = setup
    # The native switch has persisted its choice; its listener can still be queued.
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_BRIDGE_CHARGE_ENABLED: False}
    )
    assert coordinator.bridge_charge_enabled
    result = await _configure(await hass_ws_client(hass), entry, profile=_profile(None))
    assert result["success"]
    assert entry.options[CONF_PV_FORECAST_SENSOR] is None
    assert not coordinator.bridge_charge_enabled
    assert coordinator.timed_charge_enabled


@pytest.mark.parametrize("state", ["10", "unavailable"])
async def test_required_source_can_be_replaced_without_disabling_the_bridge(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, setup, state: str
) -> None:
    entry, coordinator = setup
    hass.states.async_set("sensor.pv_other", state, {"unit_of_measurement": "kWh"})
    result = await _configure(
        await hass_ws_client(hass), entry, profile=_profile("sensor.pv_other")
    )
    assert result["success"]
    assert coordinator.options[CONF_PV_FORECAST_SENSOR] == "sensor.pv_other"
    assert coordinator.bridge_charge_enabled
    assert coordinator.timed_charge_enabled


async def test_dynamic_pv_source_remains_optional_while_tou_profile_is_archived(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, setup
) -> None:
    entry, coordinator = setup
    result = await _configure(
        await hass_ws_client(hass),
        entry,
        tariff_type="dynamic",
        profile={
            "feed_in_price_ct_kwh": 8,
            "price_sensor": "sensor.price",
            "price_attribute": None,
            "price_unit": "auto",
            "pv_sensor": None,
            "pv_factor": 60,
        },
    )
    assert result["success"]
    assert not coordinator.bridge_charge_enabled
    assert coordinator.price_charge_enabled
    assert entry.options[CONF_PV_FORECAST_SENSOR] is None
    archived = entry.options[CONF_DASHBOARD_TARIFF_PROFILES]["time_of_use"]
    assert archived[CONF_PV_FORECAST_SENSOR] == "sensor.pv"
    assert archived[CONF_BRIDGE_CHARGE_ENABLED] is True


@pytest.mark.parametrize("loaded", [False, True])
async def test_restore_cannot_activate_an_archived_bridge_without_a_source(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, setup, loaded: bool
) -> None:
    entry, coordinator = setup
    options = options_for_tariff(
        {**entry.options, CONF_PV_FORECAST_SENSOR: None},
        "dynamic",
        {CONF_ECONOMICS_FEED_IN_PRICE: 0.08, CONF_PRICE_SENSOR: "sensor.price"},
    )
    hass.config_entries.async_update_entry(entry, options=options)
    coordinator.options = dict(options)
    coordinator._timed_charge_enabled = False
    coordinator._price_charge_enabled = False
    if not loaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    before = deepcopy(dict(entry.options))
    result = await _configure(await hass_ws_client(hass), entry)
    assert result["error"]["code"] == "bridge_pv_start_required"
    assert entry.options == coordinator.options == before
    assert not coordinator.bridge_charge_enabled


async def test_runtime_hook_also_rejects_invalid_bridge_before_any_mutation(
    setup,
) -> None:
    entry, coordinator = setup
    before = deepcopy(dict(entry.options))
    with pytest.raises(ServiceValidationError) as error:
        await coordinator.async_apply_dashboard_tariff(
            {**before, CONF_PV_FORECAST_SENSOR: None},
            enabled=False,
            expected_options=before,
        )
    assert error.value.translation_key == "bridge_pv_start_required"
    assert entry.options == coordinator.options == before
    assert coordinator.timed_charge_enabled


async def test_queued_request_cannot_undo_a_native_bridge_activation(
    hass: HomeAssistant, setup
) -> None:
    entry, coordinator = setup
    before = {**entry.options, CONF_BRIDGE_CHARGE_ENABLED: False}
    hass.config_entries.async_update_entry(entry, options=before)
    coordinator.options = before
    await coordinator._charge_control_lock.acquire()
    request = asyncio.create_task(
        coordinator.async_apply_dashboard_tariff(
            {**before, CONF_PV_FORECAST_SENSOR: None},
            enabled=None,
            expected_options=before,
        )
    )
    latest = {**before, CONF_BRIDGE_CHARGE_ENABLED: True}
    hass.config_entries.async_update_entry(entry, options=latest)
    try:
        with pytest.raises(ServiceValidationError) as error:
            await asyncio.wait_for(request, 0.2)
    finally:
        coordinator._charge_control_lock.release()
    assert error.value.translation_key == "dashboard_tariff_conflict"
    assert entry.options == latest
    assert entry.options[CONF_PV_FORECAST_SENSOR] == "sensor.pv"
