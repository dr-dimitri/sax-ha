"""REQ-VUE-ELECTRICITY-TARIFF: echte Tarifwechsel bestätigen vor Geräte-ACKs."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pymodbus.exceptions import ModbusException
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power import _async_register_services
from custom_components.sax_power.const import (
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_PRICE_SENSOR,
    DOMAIN,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.dashboard_tariff import CONFIGURE_COMMAND

from .test_dashboard_tariff_response import _get, _prepare, _toggle
from .test_month_switch_response import coordinator as coordinator


async def _configure(
    client: Any,
    entry: MockConfigEntry,
    tariff: dict[str, Any],
    target: str,
    *,
    source: str | None = None,
) -> dict[str, Any]:
    profile = {**tariff["profiles"][target]}
    if profile["feed_in_price_ct_kwh"] is None:
        profile["feed_in_price_ct_kwh"] = 8
    if target == "time_of_use" and profile["base_price_ct_kwh"] is None:
        profile["base_price_ct_kwh"] = 32
    if target == "dynamic" and profile["price_sensor"] is None:
        profile["price_sensor"] = "sensor.price"
    if source is not None:
        profile["price_sensor"] = source
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": tariff["revision"],
            "tariff_type": target,
            "profile": profile,
            "automation_enabled": True,
        }
    )
    return await client.receive_json()


@pytest.mark.parametrize("initial", ["time_of_use", "dynamic"])
async def test_real_tariff_changes_coalesce_before_device_lock(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    initial: str,
) -> None:
    """Typ und Quellen werden atomar bestätigt; nur der letzte Stand steuert."""
    entry = _prepare(hass, coordinator, initial)
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    targets = ("dynamic", "time_of_use", "dynamic", "time_of_use")
    with patch.object(coordinator, "_async_enforce_grid_charge_locked") as enforce:
        async with coordinator._charge_control_lock:
            task = None
            for target in targets:
                result = await asyncio.wait_for(
                    _configure(client, entry, tariff, target), 0.2
                )
                assert result["success"], result
                tariff = result["result"]
                assert tariff["tariff_type"] == target
                assert tariff["automation_enabled"] is True
                assert coordinator.options == entry.options
                assert coordinator.options[CONF_ECONOMICS_TARIFF_TYPE] == target
                assert coordinator.price_charge_enabled is (target == "dynamic")
                assert coordinator.timed_charge_enabled is (target == "time_of_use")
                assert coordinator._control_store._pending is not None
                if task is None:
                    task = coordinator._month_control_task
                assert coordinator._month_control_task is task
                enforce.assert_not_awaited()
                coordinator.client.write_register.assert_not_awaited()
        await task
        enforce.assert_awaited_once()
    assert coordinator.timed_charge_enabled
    assert not coordinator.price_charge_enabled


@pytest.mark.parametrize("periodic", [False, True])
@pytest.mark.parametrize("change", ["tariff", "source"])
@pytest.mark.parametrize(
    "held_register", [REG_SUN_IC_CONTROL_MODE, REG_SUN_IC_POWER_SETPOINT_PCT]
)
@pytest.mark.parametrize("failed_ack", [False, True])
async def test_tariff_change_during_device_ack_drains_and_releases_old_charge(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    periodic: bool,
    change: str,
    held_register: int,
    failed_ack: bool,
) -> None:
    """WS bleibt bedienbar, ohne Start oder periodische Modbussequenz abzubrechen."""
    entry = _prepare(hass, coordinator, "dynamic")
    hass.states.async_set("sensor.expensive", "0.9", {"unit_of_measurement": "EUR/kWh"})
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    started, finish = asyncio.Event(), asyncio.Event()
    cancelled = False
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        nonlocal cancelled
        matches_writer = (
            asyncio.current_task() is coordinator._sun_charge_task
        ) is periodic
        if (
            not started.is_set()
            and matches_writer
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
                raise ModbusException("delayed tariff test failure")
        return success

    coordinator.client.write_register.side_effect = write
    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=datetime(2024, 1, 1, 2, tzinfo=UTC),
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=datetime(2024, 1, 1, 2, tzinfo=UTC),
        ),
        patch.object(coordinator, "_sun_ic_write_interval", return_value=0.01),
    ):
        assert (await _toggle(client, entry, tariff, True))["success"]
        try:
            await asyncio.wait_for(started.wait(), 1)
            old_writer = coordinator._sun_charge_task
            response = await asyncio.wait_for(
                _configure(
                    client,
                    entry,
                    tariff,
                    "dynamic" if change == "source" else "time_of_use",
                    source="sensor.expensive" if change == "source" else None,
                ),
                0.2,
            )
            assert response["success"], response
            task = coordinator._month_control_task
            assert task is not None and not task.done()
            assert coordinator.options == entry.options
            if periodic:
                assert old_writer is not None
                assert not old_writer.cancelling()
                assert not old_writer.done()
            else:
                assert not coordinator.price_charge_active
            if change == "source":
                assert entry.options[CONF_PRICE_SENSOR] == "sensor.expensive"
            else:
                assert entry.options[CONF_ECONOMICS_TARIFF_TYPE] == "time_of_use"
        finally:
            finish.set()
        await asyncio.wait_for(task, 1)
    assert not cancelled
    assert not coordinator.sun_charge_active
    assert not coordinator.price_charge_active
    assert not coordinator._timed_charge_active
    assert not coordinator._sun_charge_reset_required
    writes = [
        (call.kwargs["address"], call.kwargs["value"])
        for call in coordinator.client.write_register.await_args_list
    ]
    assert writes[0] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT)
    assert writes[-1] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER)
    assert coordinator._tariff_source_revision == coordinator._tariff_control_revision


async def test_pending_source_change_stops_periodic_repetition_before_control_lock(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    """Ein alter Sollwert wird auch bei länger belegtem Control-Lock nicht erneuert."""
    entry = _prepare(hass, coordinator, "dynamic")
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=datetime(2024, 1, 1, 2, tzinfo=UTC),
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=datetime(2024, 1, 1, 2, tzinfo=UTC),
        ),
        patch.object(coordinator, "_sun_ic_write_interval", return_value=0.01),
    ):
        assert (await _toggle(client, entry, tariff, True))["success"]
        if coordinator._month_control_task is not None:
            await coordinator._month_control_task
        writer = coordinator._sun_charge_task
        assert writer is not None
        coordinator.client.write_register.reset_mock()
        async with coordinator._charge_control_lock:
            result = await asyncio.wait_for(
                _configure(client, entry, tariff, "time_of_use"), 0.2
            )
            assert result["success"]
            await asyncio.wait_for(writer, 1)
            coordinator.client.write_register.assert_not_awaited()
        await coordinator._month_control_task
    assert not coordinator.sun_charge_active
    coordinator.client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_failed_tariff_reset_keeps_accepted_config_and_retries_on_poll(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    """Eine abgelehnte Rücksetzung verliert weder Tarifwahl noch Rücksetzauftrag."""
    entry = _prepare(hass, coordinator, "dynamic")
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    started, finish = asyncio.Event(), asyncio.Event()
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == REG_SUN_IC_POWER_SETPOINT_PCT:
            started.set()
            await finish.wait()
        if address == REG_SUN_IC_CONTROL_MODE and value == 0:
            raise ModbusException("test reset rejected")
        return success

    coordinator.client.write_register.side_effect = write
    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=datetime(2024, 1, 1, 2, tzinfo=UTC),
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=datetime(2024, 1, 1, 2, tzinfo=UTC),
        ),
    ):
        assert (await _toggle(client, entry, tariff, True))["success"]
        try:
            await asyncio.wait_for(started.wait(), 1)
            result = await asyncio.wait_for(
                _configure(client, entry, tariff, "time_of_use"), 0.2
            )
            assert result["success"]
            task = coordinator._month_control_task
        finally:
            finish.set()
        await asyncio.wait_for(task, 1)
        assert coordinator._sun_charge_reset_required
        assert not coordinator.sun_charge_active
        assert not coordinator.price_charge_active
        assert coordinator.options == entry.options
        assert entry.options[CONF_ECONOMICS_TARIFF_TYPE] == "time_of_use"
        assert coordinator.timed_charge_enabled
        coordinator.client.write_register.side_effect = None
        await coordinator._async_enforce_grid_charge(coordinator.data)
    assert not coordinator._sun_charge_reset_required
    coordinator.client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


@pytest.mark.parametrize("during_persistence", [False, True])
async def test_tariff_transition_preserves_unrelated_global_soc_hold(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    during_persistence: bool,
) -> None:
    """Eine neue Tarifquelle gibt eine geräteweite 0-%-Sperre nicht kurz frei."""
    entry = _prepare(hass, coordinator, "dynamic")
    coordinator._max_soc = 40
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator._max_soc_clamped
    coordinator.client.write_register.reset_mock()
    started, finish = asyncio.Event(), asyncio.Event()
    persist = coordinator._async_persist_timed_charge_state

    async def delayed_persist(state: Any) -> None:
        if not started.is_set():
            started.set()
            await finish.wait()
        await persist(state)

    with patch.object(
        coordinator, "_async_persist_timed_charge_state", side_effect=delayed_persist
    ):
        if during_persistence:
            poll = asyncio.create_task(
                coordinator._async_enforce_grid_charge(coordinator.data)
            )
            await asyncio.wait_for(started.wait(), 1)
        else:
            finish.set()
        try:
            result = await asyncio.wait_for(
                _configure(client, entry, tariff, "time_of_use"), 0.2
            )
            assert result["success"]
        finally:
            finish.set()
        if during_persistence:
            await asyncio.wait_for(poll, 1)
        if coordinator._month_control_task is not None:
            await asyncio.wait_for(coordinator._month_control_task, 1)
    assert coordinator._max_soc_clamped
    assert coordinator.sun_charge_active
    writes = [
        (call.kwargs["address"], call.kwargs["value"])
        for call in coordinator.client.write_register.await_args_list
    ]
    assert writes == [
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT),
        (REG_SUN_IC_POWER_SETPOINT_PCT, 0),
    ]


@pytest.mark.parametrize("failed_ack", [False, True])
async def test_manual_charge_service_still_requires_ack_after_a_source_change(
    hass: HomeAssistant,
    coordinator: SaxPowerCoordinator,
    failed_ack: bool,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Neue Softwarequelle ist keine Gerätequittung."""
    entry = _prepare(hass, coordinator, "dynamic")
    started, finish = asyncio.Event(), asyncio.Event()
    writing, acknowledge = asyncio.Event(), asyncio.Event()
    persist = coordinator._async_persist_timed_charge_state
    success = coordinator.client.write_register.return_value

    async def delayed_persist(state: Any) -> None:
        if not started.is_set():
            started.set()
            await finish.wait()
        await persist(state)

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if not writing.is_set():
            writing.set()
            await acknowledge.wait()
            if failed_ack:
                raise ModbusException("manual command test ACK failed")
        return success

    coordinator.client.write_register.side_effect = write
    with (
        patch.object(
            coordinator,
            "_async_persist_timed_charge_state",
            side_effect=delayed_persist,
        ),
        patch(
            "custom_components.sax_power._coordinator_for_device",
            return_value=coordinator,
        ),
    ):
        _async_register_services(hass)
        command = asyncio.create_task(
            hass.services.async_call(
                DOMAIN,
                "start_grid_charge",
                {"device_id": "battery", "power": -1000},
                blocking=True,
            )
        )
        await asyncio.wait_for(started.wait(), 1)
        try:
            await coordinator.async_apply_dashboard_tariff(
                {**dict(entry.options), CONF_PRICE_SENSOR: "sensor.changed_price"},
                enabled=None,
                expected_options=dict(entry.options),
            )
            finish.set()
            await asyncio.wait_for(writing.wait(), 1)
            done, pending = await asyncio.wait({command}, timeout=0.02)
            assert not done
            assert pending == {command}
        finally:
            finish.set()
            acknowledge.set()
        if failed_ack:
            with pytest.raises(HomeAssistantError):
                await command
            assert coordinator._grid_charge_power is None
        else:
            await command
            assert coordinator._grid_charge_power == -1000
            assert coordinator.sun_charge_active
        if coordinator._month_control_task is not None:
            await coordinator._month_control_task


async def test_manual_start_during_bootstrap_never_acknowledges_pending_source(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: Ungeladene Regeln sind keine Gerätefreigabe."""
    coordinator._control_bootstrap_pending = True
    coordinator._tariff_source_revision += 1

    with pytest.raises(HomeAssistantError, match="Ladeeinstellungen"):
        await asyncio.wait_for(coordinator.async_start_grid_charge(-1000), 0.2)

    assert coordinator._grid_charge_power is None
    coordinator.client.write_register.assert_not_awaited()
