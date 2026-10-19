"""Read-only runtime evidence for REQ-DIAGNOSTICS charge investigations."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.sax_power.application.timed_discharge import TimedDischargeState
from custom_components.sax_power.const import (
    READ_BLOCK_EXT_HIGH_MAX_AGE,
    READ_BLOCK_EXT_LOW_INTERVAL,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

_CLOCK = "custom_components.sax_power.coordinator.monotonic"
_NOW_PATH = "custom_components.sax_power.coordinator.dt_util.now"
_NOW = datetime(2026, 10, 19, 2, tzinfo=UTC)


@pytest.fixture
async def coordinator(hass: HomeAssistant) -> SaxPowerCoordinator:
    """Build a coordinator whose device calls must remain untouched."""
    await hass.config.async_set_time_zone("UTC")
    client = MagicMock()
    client.read_holding_registers = AsyncMock()
    client.write_register = AsyncMock()
    client.connect = AsyncMock()
    return SaxPowerCoordinator(hass, client, 64, 100, 10, "control-diagnostics")


def test_missing_samples_and_configuration_remain_visible(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-DIAGNOSTICS: an uninitialized download invents no fresh evidence."""
    snapshot = coordinator.charge_control_diagnostics

    telemetry = snapshot["telemetry"]
    assert telemetry["basic_sample_age_seconds"] is None
    assert telemetry["high_sample_age_seconds"] is None
    assert telemetry["low_sample_age_seconds"] is None
    assert telemetry["high_measurements_fresh"] is False
    assert telemetry["low_refresh_due"] is True
    assert snapshot["timed_charge"]["window"] is None
    assert snapshot["timed_charge"]["restore_window"] is None
    assert snapshot["timed_charge"]["discharge_hold"] is None
    assert snapshot["timed_charge"]["discharge_hold_active"] is False
    assert snapshot["timed_charge"]["window_completed"] is False
    assert snapshot["writer"]["active_deadline"] is None
    assert snapshot["writer"]["commanded_mode"] is None
    assert json.loads(json.dumps(snapshot, allow_nan=False)) == snapshot
    coordinator.client.read_holding_registers.assert_not_called()
    coordinator.client.write_register.assert_not_called()
    coordinator.client.connect.assert_not_called()


@pytest.mark.parametrize(
    ("sample_age", "available", "fresh"),
    [
        (None, True, False),
        (0.0, True, True),
        (READ_BLOCK_EXT_HIGH_MAX_AGE, True, True),
        (READ_BLOCK_EXT_HIGH_MAX_AGE + 0.01, True, False),
        (-0.01, True, False),
        (1.0, False, False),
    ],
)
def test_high_freshness_matches_control_sample_limits(
    coordinator: SaxPowerCoordinator,
    sample_age: float | None,
    available: bool,
    fresh: bool,
) -> None:
    """REQ-DIAGNOSTICS: retained readings cannot appear usable after failure."""
    coordinator._high_sample_time = None if sample_age is None else 100 - sample_age
    coordinator._extended_available = available
    coordinator._basic_read_failed = True
    coordinator.last_update_success = False
    with patch(_CLOCK, return_value=100):
        telemetry = coordinator.charge_control_diagnostics["telemetry"]

    assert telemetry["high_sample_age_seconds"] == (
        None if sample_age is None else pytest.approx(sample_age)
    )
    assert telemetry["high_measurements_fresh"] is fresh
    assert telemetry["basic_read_failed"] is True
    assert telemetry["last_update_success"] is False


@pytest.mark.parametrize("low_age", [1.0, READ_BLOCK_EXT_LOW_INTERVAL + 1])
def test_basic_and_low_cache_ages_explain_their_refresh_schedule(
    coordinator: SaxPowerCoordinator, low_age: float
) -> None:
    """REQ-LOW-INTERVAL-REGISTERS: overdue static data remains identifiable."""
    now = READ_BLOCK_EXT_LOW_INTERVAL + 100.0
    coordinator._basic_last_read = now - 4.5
    coordinator._low_block_last_read = now - low_age
    with patch(_CLOCK, return_value=now):
        telemetry = coordinator.charge_control_diagnostics["telemetry"]

    assert telemetry["basic_sample_age_seconds"] == 4.5
    assert telemetry["basic_poll_interval_seconds"] == 10
    assert telemetry["low_sample_age_seconds"] == low_age
    assert telemetry["low_refresh_due"] is (low_age >= READ_BLOCK_EXT_LOW_INTERVAL)


async def test_pending_writers_and_locks_can_be_inspected_without_waiting(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-DIAGNOSTICS: downloads remain readable during a held device lock."""
    release = asyncio.Event()
    pending = asyncio.create_task(release.wait())
    coordinator._month_control_task = pending
    coordinator._sun_charge_task = pending
    coordinator._sun_charge_write_task = pending
    coordinator._sun_charge_reset_required = True
    coordinator._sun_charge_power = -3200
    coordinator._sun_charge_commanded_mode = 2
    coordinator._tariff_source_revision = 4
    coordinator._tariff_control_revision = 3
    try:
        async with (
            coordinator._charge_control_lock,
            coordinator._write_lock,
            coordinator._sun_charge_write_lock,
        ):
            writer = coordinator.charge_control_diagnostics["writer"]
            assert writer["control_worker_running"] is True
            assert writer["periodic_writer_running"] is True
            assert writer["immediate_writer_running"] is True
            assert writer["control_lock_locked"] is True
            assert writer["modbus_lock_locked"] is True
            assert writer["sun_write_lock_locked"] is True
            assert writer["reset_required"] is True
            assert writer["requested_power_w"] == -3200
            assert writer["commanded_mode"] == 2
            assert writer["tariff_source_revision"] == 4
            assert writer["tariff_control_revision"] == 3
            assert coordinator._sun_charge_reset_required is True
            coordinator.client.read_holding_registers.assert_not_called()
            coordinator.client.write_register.assert_not_called()

        release.set()
        await pending
        writer = coordinator.charge_control_diagnostics["writer"]
        assert writer["control_worker_running"] is False
        assert writer["periodic_writer_running"] is False
        assert writer["immediate_writer_running"] is False
        assert writer["control_lock_locked"] is False
    finally:
        release.set()
        await pending
        coordinator._month_control_task = None
        coordinator._sun_charge_task = None
        coordinator._sun_charge_write_task = None


@pytest.mark.parametrize("same_source", [True, False])
def test_window_and_discharge_proof_preserve_their_tariff_binding(
    coordinator: SaxPowerCoordinator, same_source: bool
) -> None:
    """REQ-DIAGNOSTICS: old tariff proof must remain distinguishable from active."""
    coordinator.options = {
        "economics_tariff_type": "time_of_use",
        "economics_feed_in_price_eur_kwh": 0.08,
        "economics_tou_base_price_eur_kwh": 0.4,
        "economics_tou_window_1": {
            "start": "01:00:00",
            "end": "05:00:00",
            "price_eur_kwh": 0.1,
        },
    }
    coordinator._timed_charge_enabled = True
    state = coordinator._active_tariff_charge_state(_NOW)
    assert state is not None
    coordinator._timed_charge_armed = True
    coordinator._timed_charge_window = state
    coordinator._timed_charge_restore_state = state
    coordinator._timed_charge_persisted_state = state
    source = state.source if same_source else "a" * 64
    coordinator._timed_discharge_state = TimedDischargeState(state.expires_at, source)
    coordinator._timed_discharge_last_window_end = state.expires_at
    coordinator._timed_discharge_last_source = source
    coordinator._tariff_charge_deadline = state.expires_at
    coordinator._tariff_charge_source = state.source
    coordinator._grid_serving_setpoint_active = True
    coordinator._grid_serving_wait_cycles = 2
    coordinator._grid_serving_charge_confirm_cycles = 1
    with patch(_NOW_PATH, return_value=_NOW):
        snapshot = coordinator.charge_control_diagnostics

    timed = snapshot["timed_charge"]
    assert timed["armed"] is True
    assert timed["window"] == {
        "start": "01:00:00",
        "end": "05:00:00",
        "expires_at": state.expires_at.isoformat(),
        "source": state.source,
    }
    assert timed["restore_window"] == timed["window"]
    assert timed["persisted_window"] == timed["window"]
    assert timed["discharge_hold"]["source"] == source
    assert timed["discharge_hold_active"] is same_source
    assert timed["last_window_end"] == state.expires_at.isoformat()
    assert snapshot["writer"]["active_deadline"] == state.expires_at.isoformat()
    assert snapshot["grid_serving"]["setpoint_active"] is True
    assert snapshot["grid_serving"]["wait_cycles"] == 2
    assert snapshot["grid_serving"]["charge_confirmation_cycles"] == 1
    assert coordinator._timed_charge_window is state
    assert coordinator._timed_charge_armed is True
    assert json.loads(json.dumps(snapshot, allow_nan=False)) == snapshot


def test_completed_legacy_window_is_reported_without_resetting_proof(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-DIAGNOSTICS: a completed charge cannot resemble an unarmed start."""
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(6)
    previous_end = _NOW.replace(hour=2)
    coordinator._timed_discharge_last_window_end = previous_end
    with patch(_NOW_PATH, return_value=_NOW.replace(hour=3)):
        timed = coordinator.charge_control_diagnostics["timed_charge"]

    assert timed["window_completed"] is True
    assert timed["last_window_end"] == previous_end.isoformat()
    assert coordinator._timed_discharge_last_window_end == previous_end
