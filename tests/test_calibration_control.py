"""Kalibrierung am lokalen Tagesbeginn vor Timer-/Service-Ladeentscheidungen."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, time, timedelta
from time import monotonic
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.sax_power.application.calibration import CalibrationState
from custom_components.sax_power.application.timed_discharge import TimedDischargeState
from custom_components.sax_power.const import (
    REG_SUN_IC_CONTROL_MODE,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)

from .test_coordinator import _make_client, _make_coordinator

_MODULE = "custom_components.sax_power.coordinator"
_BERLIN = ZoneInfo("Europe/Berlin")
_LAST_FULL = datetime(2026, 9, 9, 16, 37, tzinfo=UTC)
_DUE_START = datetime(2026, 9, 11, 22, 5, tzinfo=UTC)


@pytest.mark.parametrize("blocked", [None, "basic", "bootstrap"])
async def test_running_pv_writer_refreshes_due_calibration_before_new_setpoint(
    hass: HomeAssistant, blocked: str | None
) -> None:
    """REQ-PERIODIC-FULL-CALIBRATION: PV beginnt vor dem nächsten Poll mit 100 %."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    coordinator = _make_coordinator(hass, _make_client())
    coordinator._max_soc = 80
    coordinator._cell_calibration_state = CalibrationState(_LAST_FULL)
    coordinator._sun_charge_timed_discharge = True
    coordinator._timed_charge_enabled = True
    coordinator._timed_discharge_state = TimedDischargeState(
        _DUE_START + timedelta(hours=2)
    )
    coordinator._basic_read_failed = blocked == "basic"
    coordinator._control_bootstrap_pending = blocked == "bootstrap"
    coordinator.data = {"soc": 85}
    coordinator._high_sample_time = monotonic()
    coordinator._high_data = {
        "storage_power_active": 0,
        "smartmeter_power": -800,
    }
    coordinator._async_write_sun_charge_setpoint = AsyncMock()
    coordinator.price_planner.evaluate = MagicMock()
    coordinator.async_update_listeners = MagicMock()
    try:
        with (
            patch(f"{_MODULE}.dt_util.utcnow", return_value=_DUE_START),
            patch(
                f"{_MODULE}.asyncio.sleep",
                new=AsyncMock(side_effect=[None, asyncio.CancelledError]),
            ),
        ):
            if blocked == "bootstrap":
                await coordinator._async_sun_charge_loop()
                coordinator._async_write_sun_charge_setpoint.assert_not_awaited()
            else:
                with pytest.raises(asyncio.CancelledError):
                    await coordinator._async_sun_charge_loop()
                coordinator._async_write_sun_charge_setpoint.assert_awaited_once_with(
                    0 if blocked else -800, timed_discharge_hold=True
                )
        assert coordinator.cell_calibration_active is (blocked is None)
        if blocked is None:
            coordinator.price_planner.evaluate.assert_called_once()
            coordinator.async_update_listeners.assert_called_once()
            assert coordinator.data["next_cell_calibration"] == date(2026, 9, 12)
        else:
            coordinator.price_planner.evaluate.assert_not_called()
    finally:
        await hass.config.async_set_time_zone("UTC")


@pytest.mark.parametrize("trigger", ["service", "timer"])
async def test_first_regular_cycle_uses_full_target_before_old_full_charge_time(
    hass: HomeAssistant, trigger: str
) -> None:
    """REQ-PERIODIC-FULL-CALIBRATION: Vor dem ersten Mode-Write gilt bereits 100 %."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator._max_soc = 80
    coordinator._timed_charge_max_soc = 60
    coordinator._timed_charge_min_soc = 40
    coordinator._timed_charge_start = time(0)
    coordinator._timed_charge_end = time(6)
    coordinator._cell_calibration_state = CalibrationState(_LAST_FULL)
    coordinator._calibration_store.async_save = AsyncMock()
    coordinator.data = {
        "soc": 39,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": 0,
    }
    write_result = client.write_register.return_value
    observed_targets = []

    async def record_write(**kwargs: Any) -> Any:
        observed_targets.append(
            (coordinator.effective_max_soc, coordinator.effective_timed_charge_max_soc)
        )
        return write_result

    client.write_register.side_effect = record_write
    try:
        with (
            patch(f"{_MODULE}.dt_util.utcnow", return_value=_DUE_START),
            patch(
                f"{_MODULE}.dt_util.now", return_value=_DUE_START.astimezone(_BERLIN)
            ),
        ):
            assert coordinator.cell_calibration_active is False
            if trigger == "service":
                await coordinator.async_set_timed_charge_enabled(True)
            else:
                coordinator._timed_charge_enabled = True
                await coordinator.async_apply_price_plan()
            assert observed_targets and set(observed_targets) == {(100, 100)}
            assert coordinator._timed_charge_active is True
            assert coordinator._sun_charge_power < 0
            assert coordinator.cell_calibration_active is True
            assert coordinator.next_cell_calibration_date == date(2026, 9, 12)
            assert coordinator.data["next_cell_calibration"] == date(2026, 9, 12)
            assert coordinator.max_soc == 80
            assert coordinator.timed_charge_max_soc == 60
            coordinator._calibration_store.async_save.assert_not_awaited()

            coordinator.data["soc"] = 85
            await coordinator.async_apply_price_plan()
            assert coordinator._timed_charge_active is True
            assert coordinator.effective_timed_charge_max_soc == 100

            coordinator.data["soc"] = 100
            await coordinator.async_apply_price_plan()
            assert coordinator.cell_calibration_active is False
            assert coordinator._timed_charge_active is False
            assert coordinator.max_soc == 80
            assert coordinator.effective_timed_charge_max_soc == 60
            assert coordinator.next_cell_calibration_date == date(2026, 9, 15)
            coordinator._calibration_store.async_save.assert_awaited_once_with(
                CalibrationState(_DUE_START, was_full=True)
            )
    finally:
        await coordinator.async_shutdown()
        await hass.config.async_set_time_zone("UTC")


async def test_due_timer_releases_existing_cap_without_starting_grid_charge(
    hass: HomeAssistant,
) -> None:
    """Ein Kalenderwechsel erlaubt PV, erzeugt aber keinen eigenen Netzladeauftrag."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator._max_soc = 80
    coordinator._max_soc_clamped = True
    coordinator._sun_charge_reset_required = True
    coordinator._cell_calibration_state = CalibrationState(_LAST_FULL)
    coordinator.data = {"soc": 85, "smartmeter_power": 0, "ic_control_mode": 1}
    try:
        with patch(f"{_MODULE}.dt_util.utcnow", return_value=_DUE_START):
            await coordinator.async_apply_price_plan()
        assert coordinator.cell_calibration_active is True
        assert coordinator.max_soc_clamped is False
        assert coordinator.sun_charge_active is False
        client.write_register.assert_awaited_once_with(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        )
    finally:
        await coordinator.async_shutdown()
        await hass.config.async_set_time_zone("UTC")


@pytest.mark.parametrize("soc", [None, True, -1, 101, float("nan"), float("inf"), "50"])
async def test_invalid_soc_cannot_activate_calibration_or_persist_an_edge(
    hass: HomeAssistant, soc: object
) -> None:
    """Ohne belastbaren SOC bleibt die Fälligkeit ohne Freigabe einer Ladesperre."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator._max_soc = 80
    original = CalibrationState(_LAST_FULL)
    coordinator._cell_calibration_state = original
    coordinator._calibration_store.async_save = AsyncMock()
    coordinator.async_start_sun_charge = AsyncMock()
    coordinator._async_suspend_charge_for_missing_soc = AsyncMock()
    coordinator.data = {"soc": soc}
    with patch(f"{_MODULE}.dt_util.utcnow", return_value=_DUE_START):
        await coordinator.async_apply_price_plan()
    assert coordinator._cell_calibration_state == original
    assert coordinator.cell_calibration_active is False
    coordinator._calibration_store.async_save.assert_not_awaited()
    coordinator.async_start_sun_charge.assert_not_awaited()
    coordinator._async_suspend_charge_for_missing_soc.assert_awaited_once()


async def test_failed_basic_read_does_not_treat_cached_full_soc_as_new_edge(
    hass: HomeAssistant,
) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    original = CalibrationState(_LAST_FULL)
    coordinator._cell_calibration_state = original
    coordinator._calibration_store.async_save = AsyncMock()
    coordinator._basic_read_failed = True
    coordinator._async_suspend_charge_for_missing_soc = AsyncMock()
    coordinator.data = {"soc": 100}
    with patch(f"{_MODULE}.dt_util.utcnow", return_value=_DUE_START):
        await coordinator.async_set_max_soc(80)
    assert coordinator._cell_calibration_state == original
    assert coordinator.cell_calibration_active is False
    coordinator._calibration_store.async_save.assert_not_awaited()
    coordinator._async_suspend_charge_for_missing_soc.assert_awaited_once()


@pytest.mark.parametrize("gate", ["bootstrap", "shutdown"])
async def test_timer_gate_prevents_calibration_and_device_writes(
    hass: HomeAssistant, gate: str
) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    original = CalibrationState(_LAST_FULL)
    coordinator._cell_calibration_state = original
    coordinator._calibration_store.async_save = AsyncMock()
    coordinator._max_soc = 80
    coordinator.data = {"soc": 50}
    if gate == "bootstrap":
        coordinator._control_bootstrap_pending = True
    else:
        coordinator._shutdown_started = True
    with patch(f"{_MODULE}.dt_util.utcnow", return_value=_DUE_START):
        await coordinator.async_apply_price_plan()
        if gate == "shutdown":
            with pytest.raises(HomeAssistantError):
                await coordinator.async_start_grid_charge(-1000)
    assert coordinator._cell_calibration_state == original
    assert coordinator.cell_calibration_active is False
    coordinator._calibration_store.async_save.assert_not_awaited()
    coordinator.client.write_register.assert_not_awaited()


async def test_bootstrap_completion_establishes_full_baseline_without_repeated_edge(
    hass: HomeAssistant,
) -> None:
    """Ein erstmaliger SOC 100 startet nach Bootstrap nur den Kalenderzähler."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator._control_bootstrap_pending = True
    coordinator._max_soc = 80
    coordinator._calibration_store.async_save = AsyncMock()
    coordinator.async_start_sun_charge = AsyncMock()
    coordinator.data = {"soc": 100, "smartmeter_power": 0}
    try:
        with patch(f"{_MODULE}.dt_util.utcnow", return_value=_DUE_START) as utcnow:
            await coordinator.async_apply_price_plan()
            assert coordinator.last_full_charge_at is None
            await coordinator.async_finish_bootstrap()
            assert coordinator._cell_calibration_state == CalibrationState(
                _DUE_START, was_full=True
            )
            assert coordinator.cell_calibration_active is False
            assert coordinator.effective_max_soc == 80
            utcnow.return_value = _DUE_START + timedelta(days=4)
            await coordinator.async_apply_price_plan()
            assert coordinator.last_full_charge_at == _DUE_START
            assert coordinator.cell_calibration_active is False
            coordinator._calibration_store.async_save.assert_awaited_once()
    finally:
        await coordinator.async_shutdown()
