"""REQ-VUE-CHARGING: Monatskonfiguration wird ohne Gerätewartezeit bestätigt."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from datetime import time as dt_time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.const import (
    ALL_MONTHS,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator


@pytest.fixture
async def coordinator(hass: HomeAssistant) -> AsyncIterator[SaxPowerCoordinator]:
    client = MagicMock()
    client.connected = True
    success = MagicMock()
    success.isError.return_value = False
    client.write_register = AsyncMock(return_value=success)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="month_response",
    )
    coordinator._max_soc = 100
    coordinator._timed_charge_max_soc = 90
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "storage_power_active": 0,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
    }
    yield coordinator
    await coordinator.async_shutdown(reset_device=False)


def _prepare_timed_charge(coordinator: SaxPowerCoordinator) -> None:
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(0)
    coordinator._timed_charge_end = dt_time(6)
    coordinator._timed_charge_min_soc = 80
    coordinator._timed_charge_armed = True
    coordinator._timed_charge_months = set()


@pytest.mark.parametrize("group", ["timed_charge", "grid_serving"])
async def test_month_acceptance_does_not_wait_for_control_lock(
    coordinator: SaxPowerCoordinator, group: str
) -> None:
    """Der bestätigte Konfigurationswert und Store-Snapshot brauchen keinen Write."""
    setter = getattr(coordinator, f"async_set_{group}_month")
    await coordinator._charge_control_lock.acquire()
    try:
        await asyncio.wait_for(setter(4, False), 0.2)
        assert 4 not in getattr(coordinator, f"{group}_months")
        assert 4 not in coordinator._control_store._pending[f"{group}_months"]
        coordinator.client.write_register.assert_not_awaited()
        assert coordinator._month_control_task is not None
    finally:
        coordinator._charge_control_lock.release()
    await coordinator._month_control_task


async def test_rapid_month_changes_share_worker_and_apply_latest_configuration(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Mehrere schnelle Änderungen behalten beide vollständigen Monatsmengen."""
    await coordinator._charge_control_lock.acquire()
    try:
        await coordinator.async_set_timed_charge_month(1, False)
        task = coordinator._month_control_task
        for month in ALL_MONTHS:
            await coordinator.async_set_timed_charge_month(month, False)
            await coordinator.async_set_grid_serving_month(month, False)
            assert coordinator._month_control_task is task
        await coordinator.async_set_timed_charge_month(5, True)
        await coordinator.async_set_grid_serving_month(9, True)
        assert coordinator.timed_charge_months == frozenset({5})
        assert coordinator.grid_serving_months == frozenset({9})
        assert coordinator._control_store._pending["timed_charge_months"] == [5]
        assert coordinator._control_store._pending["grid_serving_months"] == [9]
        coordinator.client.write_register.assert_not_awaited()
    finally:
        coordinator._charge_control_lock.release()
    await task
    assert coordinator._month_control_task is None
    assert coordinator.timed_charge_months == frozenset({5})
    assert coordinator.grid_serving_months == frozenset({9})


async def test_month_changes_while_worker_waits_for_lock_are_evaluated_once(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-GRID-SERVING-CHARGE: Ein Wartestau wertet nur den neuesten Stand aus."""
    lock = coordinator._charge_control_lock
    acquire = lock.acquire
    waiting_for_lock = asyncio.Event()
    evaluations: list[tuple[frozenset[int], frozenset[int]]] = []
    enforce = coordinator._async_enforce_grid_charge_locked

    async def acquire_for_worker() -> bool:
        if lock.locked():
            waiting_for_lock.set()
        return await acquire()

    async def record_enforcement(data: dict[str, Any]) -> None:
        evaluations.append(
            (coordinator.timed_charge_months, coordinator.grid_serving_months)
        )
        await enforce(data)

    await lock.acquire()
    with (
        patch.object(lock, "acquire", side_effect=acquire_for_worker),
        patch.object(
            coordinator,
            "_async_enforce_grid_charge_locked",
            side_effect=record_enforcement,
        ) as apply,
    ):
        try:
            await coordinator.async_set_timed_charge_month(1, False)
            task = coordinator._month_control_task
            await asyncio.wait_for(waiting_for_lock.wait(), 1)
            assert task is not None and not task.done()
            apply.assert_not_awaited()
            await coordinator.async_set_timed_charge_month(2, False)
            await coordinator.async_set_timed_charge_month(1, True)
            await coordinator.async_set_grid_serving_month(3, False)
        finally:
            lock.release()
        await task
        apply.assert_awaited_once()
    assert evaluations == [(frozenset(ALL_MONTHS - {2}), frozenset(ALL_MONTHS - {3}))]


async def test_month_acceptance_does_not_wait_for_transport_lock(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Auch ein blockierter Modbus-Write verzögert keine Konfigurationsannahme."""
    _prepare_timed_charge(coordinator)
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, 2),
    ):
        await coordinator._write_lock.acquire()
        try:
            await asyncio.wait_for(
                coordinator.async_set_timed_charge_month(1, True), 0.2
            )
            assert 1 in coordinator.timed_charge_months
            coordinator.client.write_register.assert_not_awaited()
            assert coordinator._timed_charge_active is False
        finally:
            coordinator._write_lock.release()
        await coordinator._month_control_task
    assert coordinator._timed_charge_active is True


async def test_change_during_device_write_rechecks_latest_month_selection(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Eine während Modbus geänderte Freigabe wird sofort erneut ausgewertet."""
    _prepare_timed_charge(coordinator)
    write_started = asyncio.Event()
    finish_write = asyncio.Event()
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == REG_SUN_IC_CONTROL_MODE and value == SUN_IC_CONTROL_MODE_SETPOINT:
            write_started.set()
            await finish_write.wait()
        return success

    coordinator.client.write_register.side_effect = write
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, 2),
    ):
        await coordinator.async_set_timed_charge_month(1, True)
        task = coordinator._month_control_task
        try:
            await asyncio.wait_for(write_started.wait(), 1)
            await asyncio.wait_for(
                coordinator.async_set_timed_charge_month(1, False), 0.2
            )
            assert coordinator._month_control_task is task
            assert coordinator._timed_charge_active is False
        finally:
            finish_write.set()
        await task
    writes = [
        (call.kwargs["address"], call.kwargs["value"])
        for call in coordinator.client.write_register.await_args_list
    ]
    assert writes[0] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT)
    assert writes[1][0] == REG_SUN_IC_POWER_SETPOINT_PCT
    assert writes[-1] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER)
    assert coordinator._timed_charge_active is False
    assert coordinator.sun_charge_active is False
    assert coordinator.data["timed_charge_active"] is False


@pytest.mark.parametrize("group", ["timed_charge", "grid_serving"])
async def test_rejected_month_overlap_changes_neither_config_nor_worker(
    coordinator: SaxPowerCoordinator, group: str
) -> None:
    """Überlappungen werden vor Annahme, Speicherung und Gerätesteuerung abgelehnt."""
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(5)
    coordinator._grid_serving_start = dt_time(3)
    coordinator._grid_serving_end = dt_time(6)
    coordinator._timed_charge_months = {1}
    coordinator._grid_serving_months = {7}
    month = 7 if group == "timed_charge" else 1
    with pytest.raises(HomeAssistantError, match="überschneidet"):
        await getattr(coordinator, f"async_set_{group}_month")(month, True)
    assert coordinator.timed_charge_months == frozenset({1})
    assert coordinator.grid_serving_months == frozenset({7})
    assert coordinator._control_store._pending is None
    assert coordinator._month_control_task is None
    coordinator.client.write_register.assert_not_awaited()


async def test_month_restore_during_bootstrap_has_no_worker_or_persistence(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Einzelne Restore-Werte dürfen keine Teilkonfiguration anwenden."""
    coordinator._control_bootstrap_pending = True
    await coordinator.async_set_timed_charge_month(4, False, validate=False)
    await coordinator.async_set_grid_serving_month(8, False, validate=False)
    assert 4 not in coordinator.timed_charge_months
    assert 8 not in coordinator.grid_serving_months
    assert coordinator._control_store._pending is None
    assert coordinator._month_control_task is None
    coordinator.client.write_register.assert_not_awaited()


async def test_shutdown_drains_inflight_month_write_without_cancelling_sequence(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Unload wartet die begonnene Modus-/Sollwertsequenz ab und setzt danach zurück."""
    _prepare_timed_charge(coordinator)
    write_started = asyncio.Event()
    finish_write = asyncio.Event()
    was_cancelled = False
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        nonlocal was_cancelled
        if address == REG_SUN_IC_CONTROL_MODE and value == SUN_IC_CONTROL_MODE_SETPOINT:
            write_started.set()
            try:
                await finish_write.wait()
            except asyncio.CancelledError:
                was_cancelled = True
                raise
        return success

    coordinator.client.write_register.side_effect = write
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, 2),
    ):
        await coordinator.async_set_timed_charge_month(1, True)
        task = coordinator._month_control_task
        await asyncio.wait_for(write_started.wait(), 1)
        shutdown = asyncio.create_task(coordinator.async_shutdown())
        try:
            await asyncio.sleep(0)
            assert coordinator._shutdown_started
            assert not shutdown.done()
            with pytest.raises(HomeAssistantError, match="entladen"):
                await coordinator.async_set_timed_charge_month(1, False)
            assert 1 in coordinator.timed_charge_months
        finally:
            finish_write.set()
        await asyncio.wait_for(shutdown, 1)
        await task
    assert was_cancelled is False
    assert coordinator._month_control_task is None
    assert coordinator._shutdown_complete
    coordinator.client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_shutdown_discards_month_decision_waiting_for_control_lock(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Eine vor dem Unload angenommene Konfiguration löst danach keinen Write aus."""
    _prepare_timed_charge(coordinator)
    await coordinator._charge_control_lock.acquire()
    try:
        await coordinator.async_set_timed_charge_month(1, True)
        task = coordinator._month_control_task
        await asyncio.sleep(0)
        shutdown = asyncio.create_task(coordinator.async_shutdown(reset_device=False))
        await asyncio.sleep(0)
        assert coordinator._shutdown_started
    finally:
        coordinator._charge_control_lock.release()
    await task
    await shutdown
    coordinator.client.write_register.assert_not_awaited()
    assert coordinator._month_control_task is None


@pytest.mark.parametrize(
    "failed_register", [REG_SUN_IC_CONTROL_MODE, REG_SUN_IC_POWER_SETPOINT_PCT]
)
async def test_month_write_failure_keeps_config_and_allows_poll_retry(
    coordinator: SaxPowerCoordinator,
    caplog: pytest.LogCaptureFixture,
    failed_register: int,
) -> None:
    """Ein fehlgeschlagener Geräte-Write verwirft keine angenommene Monatsauswahl."""
    _prepare_timed_charge(coordinator)
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == failed_register:
            raise ModbusException("test rejection")
        return success

    coordinator.client.write_register.side_effect = write
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, 2),
    ):
        await coordinator.async_set_timed_charge_month(1, True)
        await coordinator._month_control_task
        assert coordinator.timed_charge_months == frozenset({1})
        assert coordinator.data["timed_charge_active"] is False
        assert coordinator.sun_charge_active is False
        assert "test rejection" in caplog.text
        coordinator.client.write_register.side_effect = None
        await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator._timed_charge_active is True
    assert coordinator.sun_charge_active is True
