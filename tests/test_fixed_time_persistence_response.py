"""REQ-FIXED-TIME-GRID-CHARGE: Dateisystem-I/O darf sicheren Stop nicht verzögern."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.sax_power.application.fixed_time_charge import (
    FixedTimeChargeState,
)
from custom_components.sax_power.const import (
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)

from .test_fixed_time_charge import _at, _coordinator


async def test_missing_soc_stops_before_retrying_a_delayed_daily_state_save(
    hass: HomeAssistant,
) -> None:
    """Ein Speicherfehler lässt den Writer nicht mit unbekanntem SOC weiterladen."""
    coordinator = _coordinator(hass)
    saving, finish = asyncio.Event(), asyncio.Event()
    save = coordinator._fixed_time_charge_store.async_save
    calls = 0

    async def fail_then_delay(state: FixedTimeChargeState | None) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise HomeAssistantError("fixed-time state disk write failed once")
        saving.set()
        await finish.wait()
        await save(state)

    task = None
    try:
        with (
            _at("2026-10-21T02:00:00"),
            patch.object(
                coordinator._fixed_time_charge_store,
                "async_save",
                side_effect=fail_then_delay,
            ),
            patch.object(coordinator, "_sun_ic_write_interval", return_value=0.01),
        ):
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._timed_charge_active
            assert coordinator._fixed_time_charge_persisted_state is None
            coordinator.client.write_register.reset_mock()
            coordinator.data["soc"] = None
            task = asyncio.create_task(
                coordinator._async_enforce_grid_charge(coordinator.data)
            )
            await asyncio.wait_for(saving.wait(), 1)
            await asyncio.sleep(0.04)
            writes = [
                (call.kwargs["address"], call.kwargs["value"])
                for call in coordinator.client.write_register.await_args_list
            ]
            assert writes == [(REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER)]
            assert not coordinator.sun_charge_active
            assert not coordinator._timed_charge_active
            assert not task.done()
    finally:
        finish.set()
        if task is not None:
            await task
        await coordinator.async_shutdown()


async def test_completion_save_failure_retries_without_rearming_the_same_day(
    hass: HomeAssistant,
) -> None:
    """Ein transienter Schreibfehler verändert den bestätigten Abschluss nicht."""
    coordinator = _coordinator(hass)
    restored = _coordinator(hass)
    save = coordinator._fixed_time_charge_store.async_save

    async def fail_save(state: FixedTimeChargeState | None) -> None:
        raise HomeAssistantError("fixed-time completion disk write failed once")

    try:
        with _at("2026-10-21T02:00:00"):
            await coordinator._async_enforce_grid_charge(coordinator.data)
            coordinator.data["soc"] = 80
            with patch.object(
                coordinator._fixed_time_charge_store,
                "async_save",
                side_effect=fail_save,
            ):
                await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._fixed_time_charge_state.completed
            assert not coordinator._fixed_time_charge_persisted_state.completed
            assert not coordinator.sun_charge_active
            coordinator.data["soc"] = 55
            with patch.object(
                coordinator._fixed_time_charge_store, "async_save", wraps=save
            ) as retry:
                await coordinator._async_enforce_grid_charge(coordinator.data)
            retry.assert_awaited_once()
            assert coordinator._fixed_time_charge_persisted_state.completed
            assert not coordinator._timed_charge_active
        await coordinator.async_shutdown()
        await restored.async_load_timed_charge_state()
        with _at("2026-10-21T12:00:00"):
            await restored._async_enforce_grid_charge(restored.data)
        assert restored._fixed_time_charge_state.completed
        assert not restored._timed_charge_active
        restored.client.write_register.assert_not_awaited()
    finally:
        await coordinator.async_shutdown()
        await restored.async_shutdown()


@pytest.mark.parametrize("global_cap", [False, True])
async def test_reached_target_stops_negative_power_before_delayed_completion_save(
    hass: HomeAssistant, global_cap: bool
) -> None:
    """Ein langsamer Abschluss-Save behält keinen negativen Gerätesollwert."""
    coordinator = _coordinator(hass)
    if global_cap:
        coordinator._max_soc = 40
        coordinator.data["soc"] = 39
    saving, finish = asyncio.Event(), asyncio.Event()
    save = coordinator._fixed_time_charge_store.async_save

    async def delayed_save(state: FixedTimeChargeState | None) -> None:
        saving.set()
        await finish.wait()
        await save(state)

    task = None
    try:
        with (
            _at("2026-10-21T02:00:00"),
            patch.object(coordinator, "_sun_ic_write_interval", return_value=0.01),
        ):
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._timed_charge_active
            coordinator.client.write_register.reset_mock()
            coordinator.data["soc"] = 40 if global_cap else 80
            with patch.object(
                coordinator._fixed_time_charge_store,
                "async_save",
                side_effect=delayed_save,
            ):
                task = asyncio.create_task(
                    coordinator._async_enforce_grid_charge(coordinator.data)
                )
                await asyncio.wait_for(saving.wait(), 1)
                await asyncio.sleep(0.04)
                assert coordinator._fixed_time_charge_state.completed
                assert not task.done()
                writes = [
                    (call.kwargs["address"], call.kwargs["value"])
                    for call in coordinator.client.write_register.await_args_list
                ]
                if global_cap:
                    assert (REG_SUN_IC_POWER_SETPOINT_PCT, 0) in writes
                    assert all(
                        address != REG_SUN_IC_POWER_SETPOINT_PCT or value == 0
                        for address, value in writes
                    )
                    assert coordinator.sun_charge_active
                    assert coordinator._sun_charge_power == 0
                else:
                    assert writes == [
                        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER)
                    ]
                    assert not coordinator.sun_charge_active
    finally:
        finish.set()
        if task is not None:
            await task
        await coordinator.async_shutdown()
