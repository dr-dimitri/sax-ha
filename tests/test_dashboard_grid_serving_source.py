"""REQ-GRID-SERVING-CHARGE: independent dashboard source and responsive options."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import time as dt_time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pymodbus.exceptions import ModbusException
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power import async_update_options
from custom_components.sax_power.const import (
    CONF_DASHBOARD_TARIFF_PROFILES,
    CONF_GRID_SERVING_PV_FORECAST_SENSOR,
    CONF_PV_FORECAST_SENSOR,
    DOMAIN,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.dashboard_api import async_register_dashboard_api
from custom_components.sax_power.dashboard_grid_serving import GET_COMMAND, SAVE_COMMAND
from custom_components.sax_power.sensor import (
    SENSOR_DESCRIPTIONS,
    SaxPowerForecastSensor,
)

from .test_dashboard_tariff_response import _control_clock, _prepare, _toggle
from .test_dashboard_tariff_response import _get as _get_tariff
from .test_month_switch_response import coordinator as coordinator


@pytest.fixture
def entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_GRID_SERVING_PV_FORECAST_SENSOR: "sensor.remaining",
            CONF_PV_FORECAST_SENSOR: "sensor.tomorrow",
            CONF_DASHBOARD_TARIFF_PROFILES: {
                "dynamic": {"pv_forecast_sensor": "sensor.smart"}
            },
        },
    )
    entry.add_to_hass(hass)
    for source, unit in (
        ("remaining", "kWh"),
        ("other", "Wh"),
        ("tomorrow", "kWh"),
        ("power", "W"),
    ):
        hass.states.async_set(f"sensor.{source}", "12", {"unit_of_measurement": unit})
    async_register_dashboard_api(hass)
    return entry


async def _get(client: Any, entry: MockConfigEntry) -> dict[str, Any]:
    await client.send_json_auto_id({"type": GET_COMMAND, "entry_id": entry.entry_id})
    response = await client.receive_json()
    assert response["success"], response
    return response["result"]


async def _save(
    client: Any, entry: MockConfigEntry, current: dict[str, Any], source: Any
) -> dict[str, Any]:
    await client.send_json_auto_id(
        {
            "type": SAVE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": current["revision"],
            "pv_sensor": source,
        }
    )
    return await client.receive_json()


@pytest.mark.parametrize("source", ["sensor.other", None, ""])
async def test_source_is_independent_and_preserves_latest_unrelated_options(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    source: str | None,
) -> None:
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    before = deepcopy(dict(entry.options))
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, "unrelated": "newer"}
    )
    result = await _save(client, entry, current, source)
    assert result["success"]
    assert result["result"]["pv_sensor"] == (source or None)
    assert result["result"]["can_edit"] is True
    assert result["result"]["revision"] != current["revision"]
    assert entry.options == {
        **before,
        "unrelated": "newer",
        CONF_GRID_SERVING_PV_FORECAST_SENSOR: source or None,
    }


async def test_stale_source_save_cannot_overwrite_newer_selection(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, entry: MockConfigEntry
) -> None:
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    assert (await _save(client, entry, current, "sensor.other"))["success"]
    result = await _save(client, entry, current, None)
    assert result["error"]["code"] == "conflict"
    assert entry.options[CONF_GRID_SERVING_PV_FORECAST_SENSOR] == "sensor.other"


async def test_derived_forecast_cannot_reference_itself(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    own = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{entry.entry_id}_grid_serving_forecast",
        config_entry=entry,
        unit_of_measurement="kWh",
    )
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    response = await _save(client, entry, current, own.entity_id)
    assert response["error"]["code"] == "invalid_sensor"
    assert (await _get(client, entry)) == current


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("sensor.absent", "invalid_sensor"),
        ("switch.bad", "invalid_sensor"),
        ("sensor.other\n", "invalid_sensor"),
        ("sensor.power", "invalid_unit"),
        (42, "invalid_format"),
    ],
)
async def test_invalid_source_is_rejected_without_mutation(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    source: Any,
    code: str,
) -> None:
    client = await hass_ws_client(hass)
    before = deepcopy(dict(entry.options))
    result = await _save(client, entry, await _get(client, entry), source)
    assert result["error"]["code"] == code
    assert entry.options == before


@pytest.mark.parametrize("unit", ["Wh", "kWh", "MWh"])
@pytest.mark.parametrize("loaded", [False, True])
async def test_registered_or_temporarily_unavailable_energy_source_is_selectable(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    unit: str,
    loaded: bool,
) -> None:
    registered = entity_registry.async_get_or_create(
        "sensor", "demo", "forecast", unit_of_measurement=unit
    )
    if loaded:
        hass.states.async_set(
            registered.entity_id, "unavailable", {"unit_of_measurement": unit}
        )
    client = await hass_ws_client(hass)
    result = await _save(client, entry, await _get(client, entry), registered.entity_id)
    assert result["success"]
    assert entry.options[CONF_GRID_SERVING_PV_FORECAST_SENSOR] == registered.entity_id


async def test_read_only_permissions_cover_grid_forecast_and_selected_source(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    hass_read_only_access_token: str,
    hass_read_only_user: MockUser,
) -> None:
    sensor = entity_registry.async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_grid_serving_forecast", config_entry=entry
    )
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    current = await _get(client, entry)
    assert not current["can_edit"]
    assert (await _save(client, entry, current, None))["error"]["code"] == "forbidden"
    hass_read_only_user.mock_policy(
        {"entities": {"entity_ids": {sensor.entity_id: {"read": True}}}}
    )
    await client.send_json_auto_id({"type": GET_COMMAND, "entry_id": entry.entry_id})
    assert (await client.receive_json())["error"]["code"] == "forbidden"


def _live_options(
    hass: HomeAssistant, coordinator: SaxPowerCoordinator
) -> tuple[MockConfigEntry, asyncio.Event]:
    entry = _prepare(hass, coordinator, "dynamic")
    hass.config_entries.async_update_entry(
        entry,
        options={
            **entry.options,
            CONF_GRID_SERVING_PV_FORECAST_SENSOR: "sensor.remaining",
            CONF_PV_FORECAST_SENSOR: "sensor.tomorrow",
        },
    )
    coordinator.options = dict(entry.options)
    for name, value in (
        ("remaining", "8"),
        ("other", "15"),
        ("last", "3"),
        ("tomorrow", "25"),
    ):
        hass.states.async_set(f"sensor.{name}", value, {"unit_of_measurement": "kWh"})
    applied = asyncio.Event()

    async def apply_options(hass: HomeAssistant, changed: MockConfigEntry) -> None:
        await async_update_options(hass, changed)
        applied.set()

    entry.add_update_listener(apply_options)
    return entry, applied


async def test_real_options_listener_accepts_and_coalesces_sources_before_device_lock(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    entry, applied = _live_options(hass, coordinator)
    description = next(
        item for item in SENSOR_DESCRIPTIONS if item.key == "grid_serving_forecast"
    )
    sensor = SaxPowerForecastSensor(coordinator, entry.entry_id, description)
    coordinator._grid_serving_forecast_kwh = 8
    coordinator.data["grid_serving_forecast_kwh"] = 8
    assert sensor.native_value == 8
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    with (
        patch(
            "custom_components.sax_power.async_sync_vue_dashboard",
            new_callable=AsyncMock,
        ),
        patch.object(coordinator, "_async_enforce_grid_charge_locked") as enforce,
    ):
        async with coordinator._charge_control_lock:
            task = None
            for source in ("sensor.other", "sensor.last"):
                applied.clear()
                result = await asyncio.wait_for(
                    _save(client, entry, current, source), 0.2
                )
                assert result["success"]
                current = result["result"]
                await asyncio.wait_for(applied.wait(), 0.2)
                assert coordinator.options == entry.options
                assert sensor.native_value == (15 if source == "sensor.other" else 3)
                assert sensor.extra_state_attributes["source_entity_id"] == source
                assert (
                    coordinator.price_planner.grid_serving_pv_forecast_entity_id
                    == source
                )
                assert (
                    coordinator.price_planner.pv_forecast_entity_id == "sensor.tomorrow"
                )
                task = task or coordinator._month_control_task
                assert task is coordinator._month_control_task
                coordinator.client.write_register.assert_not_awaited()
                enforce.assert_not_awaited()
        await task
        enforce.assert_awaited_once()
    assert coordinator.price_planner.grid_serving_forecast_kwh() == 3
    assert description.attributes_fn(coordinator) == {"source_entity_id": "sensor.last"}


async def test_changed_source_recalculates_the_live_pause_forecast_condition(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    """The new today source changes pause eligibility, independently of tomorrow."""
    entry, applied = _live_options(hass, coordinator)
    coordinator._grid_serving_enabled = True
    coordinator._grid_serving_start = dt_time(0)
    coordinator._grid_serving_end = dt_time(6)
    coordinator._grid_serving_forecast_threshold_kwh = 10
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    with (
        patch(
            "custom_components.sax_power.async_sync_vue_dashboard",
            new_callable=AsyncMock,
        ),
        _control_clock(),
    ):
        for source, forecast, allowed in (
            ("sensor.other", 15, True),
            ("sensor.last", 3, False),
        ):
            applied.clear()
            result = await _save(client, entry, current, source)
            assert result["success"]
            current = result["result"]
            await asyncio.wait_for(applied.wait(), 0.2)
            if coordinator._month_control_task is not None:
                await asyncio.wait_for(coordinator._month_control_task, 1)
            assert coordinator._grid_serving_forecast_kwh == forecast
            assert coordinator._grid_serving_forecast_allowed is allowed
            assert coordinator.options[CONF_PV_FORECAST_SENSOR] == "sensor.tomorrow"


@pytest.mark.parametrize("periodic", [False, True])
@pytest.mark.parametrize(
    "held_register", [REG_SUN_IC_CONTROL_MODE, REG_SUN_IC_POWER_SETPOINT_PCT]
)
@pytest.mark.parametrize("failed_ack", [False, True])
async def test_source_changes_during_start_and_periodic_ack_keep_sequence_intact(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    periodic: bool,
    held_register: int,
    failed_ack: bool,
) -> None:
    """Accept the latest pause source without interrupting either ACK phase."""
    entry, applied = _live_options(hass, coordinator)
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    tariff = await _get_tariff(client, entry)
    started, finish = asyncio.Event(), asyncio.Event()
    cancelled = False
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        nonlocal cancelled
        matches = (asyncio.current_task() is coordinator._sun_charge_task) is periodic
        if (
            not started.is_set()
            and matches
            and address == held_register
            and (address != REG_SUN_IC_CONTROL_MODE or value == 1)
        ):
            started.set()
            try:
                await finish.wait()
            except asyncio.CancelledError:
                cancelled = True
                raise
            if failed_ack:
                raise ModbusException("delayed forecast-source test failure")
        return success

    coordinator.client.write_register.side_effect = write
    with (
        patch(
            "custom_components.sax_power.async_sync_vue_dashboard",
            new_callable=AsyncMock,
        ),
        _control_clock(),
        patch.object(coordinator, "_sun_ic_write_interval", return_value=0.01),
    ):
        assert (await _toggle(client, entry, tariff, True))["success"]
        try:
            await asyncio.wait_for(started.wait(), 1)
            response = await asyncio.wait_for(
                _save(client, entry, current, "sensor.other"), 0.2
            )
            assert response["success"]
            assert entry.options[CONF_GRID_SERVING_PV_FORECAST_SENSOR] == "sensor.other"
            await asyncio.wait_for(applied.wait(), 0.2)
            assert not cancelled
        finally:
            finish.set()
        await hass.async_block_till_done()
        if coordinator._month_control_task is not None:
            await asyncio.wait_for(coordinator._month_control_task, 1)
    assert not cancelled
    assert coordinator.options == entry.options
    assert coordinator.price_planner.grid_serving_forecast_kwh() == 15
    assert coordinator.price_planner.pv_forecast_entity_id == "sensor.tomorrow"
    assert coordinator.price_charge_enabled
    assert coordinator._tariff_source_revision == coordinator._tariff_control_revision
