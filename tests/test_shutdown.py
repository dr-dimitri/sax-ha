"""REQ-SETUP-ROLLBACK: Ein entladener Coordinator verliert den Schreibbesitz."""

from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.sax_power.const import (
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator


def _coordinator(hass) -> SaxPowerCoordinator:
    client = MagicMock()
    client.connected = True
    result = MagicMock()
    result.isError.return_value = False
    client.write_register = AsyncMock(return_value=result)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="shutdown_test",
    )
    coordinator._max_soc = 100
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(0)
    coordinator._timed_charge_end = dt_time(6)
    coordinator._timed_charge_min_soc = 80
    coordinator._timed_charge_armed = True
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "storage_power_active": 0,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
    }
    return coordinator


@pytest.mark.parametrize("reset_device", [False, True])
async def test_shutdown_blocks_late_price_and_poll_decisions(
    hass, reset_device
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: Verspätete Auswertungen starten keinen Writer."""
    coordinator = _coordinator(hass)
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, 2),
    ):
        await coordinator.async_apply_price_plan()
        writer = coordinator._sun_charge_task
        assert writer is not None
        coordinator.client.write_register.reset_mock()

        await coordinator.async_shutdown(reset_device=reset_device)

        if reset_device:
            coordinator.client.write_register.assert_awaited_once_with(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SMARTMETER,
                device_id=100,
            )
        else:
            coordinator.client.write_register.assert_not_awaited()
        coordinator.client.write_register.reset_mock()
        await coordinator.async_apply_price_plan()
        await coordinator._async_enforce_grid_charge(coordinator.data)
        coordinator._basic_read_failed = True
        await coordinator._async_suspend_charge_for_missing_soc()

    coordinator.client.write_register.assert_not_awaited()
    assert writer.done()
    assert coordinator._sun_charge_task is None
    assert coordinator.sun_charge_active is False
    assert coordinator._timed_charge_active is False


@pytest.mark.parametrize(
    ("method", "args"),
    [
        ("async_set_timed_charge_enabled", (True,)),
        ("async_start_grid_charge", (-1500,)),
        ("async_stop_grid_charge", ()),
        ("async_start_sun_charge", (-1500,)),
        ("async_write_register", (0, 1)),
        ("async_write_extended_register", (REG_SUN_IC_CONTROL_MODE, 1)),
    ],
)
async def test_shutdown_rejects_user_commands(hass, method, args) -> None:
    """REQ-SETUP-ROLLBACK: Services und Entity-Writes melden den Unload klar."""
    coordinator = _coordinator(hass)
    await coordinator.async_shutdown(reset_device=False)

    with pytest.raises(HomeAssistantError, match="entladen oder ist bereits beendet"):
        await getattr(coordinator, method)(*args)

    coordinator.client.write_register.assert_not_awaited()
    assert coordinator._sun_charge_task is None
    assert coordinator.grid_charge_active is False


async def test_shutdown_rejects_user_price_refresh(hass) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: Ein manueller Refresh meldet den Unload."""
    coordinator = _coordinator(hass)
    await coordinator.async_shutdown(reset_device=False)

    with pytest.raises(HomeAssistantError, match="entladen oder ist bereits beendet"):
        await coordinator.async_apply_price_plan(background=False)

    coordinator.client.write_register.assert_not_awaited()


async def test_shutdown_blocks_commands_already_waiting_for_control_lock(hass) -> None:
    """REQ-GRID-SERVING-CHARGE: Die Schranke wird nach Lock-Erwerb geprüft."""
    coordinator = _coordinator(hass)
    await coordinator._charge_control_lock.acquire()
    price_task = asyncio.create_task(coordinator.async_apply_price_plan())
    user_task = asyncio.create_task(coordinator.async_start_grid_charge(-1500))
    await asyncio.sleep(0)
    shutdown_task = asyncio.create_task(coordinator.async_shutdown(reset_device=False))
    await asyncio.sleep(0)
    coordinator._charge_control_lock.release()

    await price_task
    with pytest.raises(HomeAssistantError, match="entladen oder ist bereits beendet"):
        await user_task
    await shutdown_task

    coordinator.client.write_register.assert_not_awaited()
    assert coordinator._sun_charge_task is None


@pytest.mark.parametrize(
    "method", ["async_write_register", "async_write_extended_register"]
)
async def test_shutdown_rejects_queued_register_write_before_final_reset(
    hass, method
) -> None:
    """REQ-SETUP-ROLLBACK: Wartende Raw-Writes verlieren ihren Schreibbesitz."""
    coordinator = _coordinator(hass)
    await coordinator.async_start_sun_charge(-1500)
    coordinator.client.write_register.reset_mock()
    await coordinator._write_lock.acquire()
    write_task = asyncio.create_task(
        getattr(coordinator, method)(REG_SUN_IC_CONTROL_MODE, 1)
    )
    await asyncio.sleep(0)
    shutdown_task = asyncio.create_task(coordinator.async_shutdown())
    await asyncio.sleep(0)
    coordinator._write_lock.release()

    with pytest.raises(HomeAssistantError, match="entladen oder ist bereits beendet"):
        await write_task
    await shutdown_task

    coordinator.client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )
    assert coordinator._sun_charge_task is None


async def test_shutdown_rejects_register_write_queued_behind_final_reset(hass) -> None:
    """REQ-SETUP-ROLLBACK: Zwischen Reset und Abschluss folgt kein Raw-Write."""
    coordinator = _coordinator(hass)
    await coordinator.async_start_sun_charge(-1500)
    coordinator.client.write_register.reset_mock()
    reset_started = asyncio.Event()
    finish_reset = asyncio.Event()

    async def reset_register(*, address: int, value: int, device_id: int) -> MagicMock:
        reset_started.set()
        await finish_reset.wait()
        result = MagicMock()
        result.isError.return_value = False
        return result

    coordinator.client.write_register.side_effect = reset_register
    shutdown_task = asyncio.create_task(coordinator.async_shutdown())
    await reset_started.wait()
    write_task = asyncio.create_task(
        coordinator.async_write_extended_register(REG_SUN_IC_CONTROL_MODE, 1)
    )
    await asyncio.sleep(0)
    assert not write_task.done()
    finish_reset.set()

    with pytest.raises(HomeAssistantError, match="entladen oder ist bereits beendet"):
        await write_task
    await shutdown_task

    coordinator.client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


@pytest.mark.parametrize("source", ["sensor", "interval"])
async def test_planner_shutdown_drains_callbacks(hass, source) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: Bereits laufende Planner-Tasks werden beendet."""
    coordinator = _coordinator(hass)
    planner = coordinator.price_planner
    started = asyncio.Event()
    finish = asyncio.Event()

    async def apply_plan() -> None:
        started.set()
        await finish.wait()

    with patch.object(coordinator, "async_apply_price_plan", side_effect=apply_plan):
        if source == "sensor":
            planner._async_source_changed(MagicMock())
            task = next(iter(planner._pending_tasks))
        else:
            task = asyncio.create_task(planner._async_interval_evaluate(datetime.now()))
        await started.wait()
        shutdown_task = asyncio.create_task(planner.async_shutdown())
        await asyncio.sleep(0)
        assert not shutdown_task.done()
        finish.set()
        await shutdown_task

    assert task.done()
    assert not planner._pending_tasks
    with patch.object(coordinator, "async_apply_price_plan") as apply:
        planner._async_source_changed(MagicMock())
        await planner._async_interval_evaluate(datetime.now())
        apply.assert_not_called()
    await coordinator.async_shutdown(reset_device=False)


@pytest.mark.parametrize("source", ["planner", "direct"])
async def test_shutdown_finishes_inflight_sequence_before_final_reset(
    hass, source
) -> None:
    """REQ-SETUP-ROLLBACK: Unload unterbricht keinen quittierten Moduswechsel."""
    coordinator = _coordinator(hass)
    mode_started = asyncio.Event()
    acknowledge_mode = asyncio.Event()

    async def write_register(*, address, value, device_id):
        if address == REG_SUN_IC_CONTROL_MODE and value == SUN_IC_CONTROL_MODE_SETPOINT:
            mode_started.set()
            await acknowledge_mode.wait()
        result = MagicMock()
        result.isError.return_value = False
        return result

    coordinator.client.write_register.side_effect = write_register
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, 2),
    ):
        if source == "planner":
            coordinator.price_planner._async_source_changed(MagicMock())
            command_task = next(iter(coordinator.price_planner._pending_tasks))
        else:
            command_task = asyncio.create_task(
                coordinator.async_start_sun_charge(-4600)
            )
        await mode_started.wait()
        shutdown_task = asyncio.create_task(coordinator.async_shutdown())
        await asyncio.sleep(0)
        assert not shutdown_task.done()
        acknowledge_mode.set()
        await shutdown_task
        await command_task

    writes = [call.kwargs for call in coordinator.client.write_register.await_args_list]
    assert [(write["address"], write["value"]) for write in writes] == [
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT),
        (REG_SUN_IC_POWER_SETPOINT_PCT, 55536),
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER),
    ]
    assert coordinator._sun_charge_task is None
    assert not coordinator.price_planner._pending_tasks
    assert coordinator.sun_charge_active is False
