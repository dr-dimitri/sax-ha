"""REQ-VUE-ENTITY-BINDING: Konfigurationsannahme wartet nicht auf Geräte-I/O."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from datetime import time as dt_time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.const import (
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

from .test_month_switch_response import coordinator as coordinator

SETTINGS = [
    ("max_soc", (85,), ("max_soc",), (85,)),
    ("timed_charge_enabled", (True,), ("timed_charge_enabled",), (True,)),
    ("price_charge_enabled", (True,), ("price_charge_enabled",), (True,)),
    ("grid_serving_enabled", (True,), ("grid_serving_enabled",), (True,)),
    ("timed_charge_max_soc", (80,), ("timed_charge_max_soc",), (80,)),
    ("timed_charge_min_soc", (30,), ("timed_charge_min_soc",), (30,)),
    ("price_charge_strategy", ("relative",), ("price_charge_strategy",), ("relative",)),
    ("price_charge_max_price", (-0.1,), ("price_charge_max_price",), (-0.1,)),
    ("price_charge_neutral_price", (0.2,), ("price_charge_neutral_price",), (0.2,)),
    ("price_charge_hours", (3,), ("price_charge_hours",), (3,)),
    (
        "grid_serving_forecast_threshold_kwh",
        (20,),
        ("grid_serving_forecast_threshold_kwh",),
        (20,),
    ),
    ("timed_charge_start", (dt_time(1),), ("timed_charge_start",), (dt_time(1),)),
    ("timed_charge_end", (dt_time(5),), ("timed_charge_end",), (dt_time(5),)),
    ("grid_serving_start", (dt_time(6),), ("grid_serving_start",), (dt_time(6),)),
    ("grid_serving_end", (dt_time(10),), ("grid_serving_end",), (dt_time(10),)),
    (
        "timed_charge_window",
        (dt_time(1), dt_time(5)),
        ("timed_charge_start", "timed_charge_end"),
        (dt_time(1), dt_time(5)),
    ),
    (
        "grid_serving_window",
        (dt_time(6), dt_time(10)),
        ("grid_serving_start", "grid_serving_end"),
        (dt_time(6), dt_time(10)),
    ),
]


@pytest.mark.parametrize("setting,args,fields,expected", SETTINGS)
async def test_configuration_confirms_and_saves_before_device_lock(
    coordinator: SaxPowerCoordinator,
    setting: str,
    args: tuple[Any, ...],
    fields: tuple[str, ...],
    expected: tuple[Any, ...],
) -> None:
    """Alle betroffenen Software-Einstellungen bestätigen trotz belegtem Lock."""
    async with coordinator._charge_control_lock:
        with patch.object(coordinator, "async_update_listeners") as notify:
            await asyncio.wait_for(
                getattr(coordinator, f"async_set_{setting}")(
                    *args, defer_device_update=True
                ),
                0.2,
            )
            assert tuple(getattr(coordinator, field) for field in fields) == expected
            assert coordinator._control_store._pending is not None
            assert coordinator._month_control_task is not None
            assert not coordinator._month_control_task.done()
            notify.assert_called()
            coordinator.client.write_register.assert_not_awaited()
    await coordinator._month_control_task


@pytest.mark.parametrize("setting,args,fields,expected", SETTINGS)
async def test_shutdown_rejects_configuration_before_mutation(
    coordinator: SaxPowerCoordinator,
    setting: str,
    args: tuple[Any, ...],
    fields: tuple[str, ...],
    expected: tuple[Any, ...],
) -> None:
    """Ein verspäteter UI-Aufruf verändert nach Shutdown keine Einstellung."""
    before = tuple(getattr(coordinator, field) for field in fields)
    await coordinator.async_shutdown(reset_device=False)
    with pytest.raises(HomeAssistantError, match="entladen"):
        await getattr(coordinator, f"async_set_{setting}")(
            *args, defer_device_update=True
        )
    assert tuple(getattr(coordinator, field) for field in fields) == before
    assert coordinator._month_control_task is None
    coordinator.client.write_register.assert_not_awaited()


async def test_mixed_changes_share_worker_and_apply_latest_configuration(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Monate, Schalter, Preis und Zeitfenster verursachen keinen Task-Wartestau."""
    evaluations = []

    async def enforce(data: dict[str, Any]) -> None:
        evaluations.append(
            (
                coordinator.price_charge_enabled,
                coordinator.timed_charge_enabled,
                coordinator.price_charge_max_price,
                coordinator.timed_charge_months,
                coordinator.timed_charge_start,
                coordinator.timed_charge_end,
            )
        )

    with patch.object(coordinator, "_async_enforce_grid_charge_locked", enforce):
        async with coordinator._charge_control_lock:
            await coordinator.async_set_timed_charge_enabled(
                True, defer_device_update=True
            )
            task = coordinator._month_control_task
            await asyncio.sleep(0)
            await coordinator.async_set_price_charge_enabled(
                True, force=True, defer_device_update=True
            )
            await coordinator.async_set_price_charge_max_price(
                0.12, defer_device_update=True
            )
            await coordinator.async_set_timed_charge_month(4, False)
            await coordinator.async_set_timed_charge_window(
                dt_time(1), dt_time(5), defer_device_update=True
            )
            assert coordinator._month_control_task is task
            assert not evaluations
            assert coordinator._control_store._pending["timed_charge_enabled"] is False
            assert coordinator._control_store._pending["price_charge_enabled"] is True
        await task
    assert evaluations == [
        (True, False, 0.12, frozenset(set(range(1, 13)) - {4}), dt_time(1), dt_time(5))
    ]


async def test_conflict_rejection_neither_saves_nor_schedules(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Die schnelle Bestätigung umgeht keine Tarif-Konfliktprüfung."""
    coordinator._timed_charge_enabled = True
    assert not await coordinator.async_set_price_charge_enabled(
        True, defer_device_update=True
    )
    assert coordinator.timed_charge_enabled
    assert not coordinator.price_charge_enabled
    assert coordinator._control_store._pending is None
    assert coordinator._month_control_task is None
    with pytest.raises(HomeAssistantError, match="Unbekannte Strategie"):
        await coordinator.async_set_price_charge_strategy(
            "invalid", defer_device_update=True
        )
    assert coordinator._month_control_task is None


async def test_deferred_bootstrap_changes_create_neither_worker_nor_save(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: Ein Teilstand steuert niemals das Gerät."""
    coordinator._control_bootstrap_pending = True
    await coordinator.async_set_timed_charge_enabled(True, defer_device_update=True)
    await coordinator.async_set_price_charge_max_price(0.12, defer_device_update=True)
    assert coordinator.timed_charge_enabled
    assert coordinator.price_charge_max_price == 0.12
    assert coordinator._month_control_task is None
    assert coordinator._control_store._pending is None
    coordinator.client.write_register.assert_not_awaited()


def _prepare_charging(coordinator: SaxPowerCoordinator) -> None:
    coordinator._timed_charge_start = dt_time(0)
    coordinator._timed_charge_end = dt_time(6)
    coordinator._timed_charge_min_soc = 80


async def test_disabling_during_device_write_preserves_sequence_and_rechecks(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Der Aus-Schalter bestätigt sofort; der laufende Write wird danach gestoppt."""
    _prepare_charging(coordinator)
    started = asyncio.Event()
    finish = asyncio.Event()
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == REG_SUN_IC_CONTROL_MODE and value == SUN_IC_CONTROL_MODE_SETPOINT:
            started.set()
            await finish.wait()
        return success

    coordinator.client.write_register.side_effect = write
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, 2, tzinfo=UTC),
    ):
        await coordinator.async_set_timed_charge_enabled(True, defer_device_update=True)
        task = coordinator._month_control_task
        try:
            await asyncio.wait_for(started.wait(), 1)
            assert not coordinator._timed_charge_active
            await asyncio.wait_for(
                coordinator.async_set_timed_charge_enabled(
                    False, defer_device_update=True
                ),
                0.2,
            )
            assert not coordinator.timed_charge_enabled
            assert coordinator._month_control_task is task
        finally:
            finish.set()
        await task
    writes = [
        (call.kwargs["address"], call.kwargs["value"])
        for call in coordinator.client.write_register.await_args_list
    ]
    assert writes[0] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT)
    assert writes[1][0] == REG_SUN_IC_POWER_SETPOINT_PCT
    assert writes[-1] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER)
    assert not coordinator.sun_charge_active
    assert coordinator.data["timed_charge_active"] is False


async def test_device_failure_retains_configuration_and_poll_can_retry(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Gerätefehler machen die angenommene Auswahl nicht rückgängig."""
    _prepare_charging(coordinator)
    coordinator.client.write_register.side_effect = ModbusException(
        "device unavailable"
    )
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, 2, tzinfo=UTC),
    ):
        assert await coordinator.async_set_timed_charge_enabled(
            True, defer_device_update=True
        )
        await coordinator._month_control_task
        assert coordinator.timed_charge_enabled
        assert coordinator._control_store._pending["timed_charge_enabled"] is True
        assert not coordinator.sun_charge_active
        coordinator.client.write_register.side_effect = None
        await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator.sun_charge_active


async def test_direct_setter_still_waits_for_device_application(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Explizite interne Geräteanwendung bleibt standardmäßig synchron."""
    async with coordinator._charge_control_lock:
        task = asyncio.create_task(coordinator.async_set_max_soc(85))
        await asyncio.sleep(0)
        assert not task.done()
        assert coordinator._month_control_task is None
    await task
