"""REQ-TIME-OF-USE-CHARGE-SOURCE: tariff boundaries own fixed SOC charging."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import issue_registry as ir

from custom_components.sax_power.application.timed_charge import TimedChargeState
from custom_components.sax_power.application.timed_discharge import TimedDischargeState
from custom_components.sax_power.const import (
    DOMAIN,
    ISSUE_CONTROL_CONFIG_UNRESOLVED,
    MIN_SETPOINT_POWER,
    REG_SUN_IC_CONTROL_MODE,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.time import (
    SaxPowerTimedChargeEndTime,
    SaxPowerTimedChargeStartTime,
)

NOW = datetime(2026, 9, 13, 2, tzinfo=UTC)
PREFIX = "custom_components.sax_power.coordinator."


def _options(start: str = "01:00:00", end: str = "06:00:00") -> dict[str, Any]:
    return {
        "economics_tariff_type": "time_of_use",
        "economics_feed_in_price_eur_kwh": 0.08,
        "economics_tou_base_price_eur_kwh": 0.4,
        "economics_tou_window_1": {
            "start": start,
            "end": end,
            "price_eur_kwh": 0.1,
        },
    }


@pytest.fixture
async def coordinator(hass: HomeAssistant) -> AsyncIterator[SaxPowerCoordinator]:
    await hass.config.async_set_time_zone("UTC")
    instance = SaxPowerCoordinator(
        hass, MagicMock(), 64, 100, 10, "tariff-test", options=_options()
    )
    instance._control_bootstrap_pending = False
    instance._timed_charge_enabled = True
    instance._timed_charge_start = dt_time(12)
    instance._timed_charge_end = dt_time(18)
    instance._timed_charge_min_soc = 20
    instance._timed_charge_max_soc = 60
    instance._max_soc = 80
    instance._async_update_cell_calibration = AsyncMock(return_value=False)
    instance.async_start_sun_charge = AsyncMock()
    instance.async_stop_sun_charge = AsyncMock()
    instance.async_write_extended_register = AsyncMock()
    yield instance
    await instance.async_shutdown()


async def _evaluate(
    coordinator: SaxPowerCoordinator, now: datetime = NOW, soc: int = 10
) -> None:
    coordinator.data = {
        "soc": soc,
        "smartmeter_power": 500,
        "storage_power_active": 0,
        "ic_max_power_reference": 4600,
    }
    with (
        patch(PREFIX + "dt_util.now", return_value=now),
        patch(PREFIX + "dt_util.utcnow", return_value=now.astimezone(UTC)),
    ):
        await coordinator._async_enforce_grid_charge_locked(coordinator.data)
        coordinator._publish_charge_state(coordinator.data)


async def test_tariff_replaces_contradictory_legacy_times_and_keeps_soc_latch(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator)
    assert coordinator._timed_charge_active
    assert coordinator._tariff_charge_deadline == NOW.replace(hour=6)
    assert coordinator.timed_charge_start == dt_time(12)
    await _evaluate(coordinator, NOW + timedelta(minutes=1), soc=30)
    assert coordinator._timed_charge_active
    await _evaluate(coordinator, NOW + timedelta(minutes=2), soc=60)
    assert not coordinator._timed_charge_active
    await _evaluate(coordinator, NOW.replace(hour=13))
    assert not coordinator._timed_charge_active
    assert coordinator._tariff_charge_deadline is None


@pytest.mark.parametrize(
    "change",
    [
        {"economics_tou_base_price_eur_kwh": None},
        {"economics_tou_window_1": {"start": "01:00:00"}},
        {
            "economics_tou_window_2": {
                "start": "02:00:00",
                "end": "08:00:00",
                "price_eur_kwh": 0.05,
            }
        },
    ],
)
async def test_invalid_tariff_never_uses_legacy_window(
    coordinator: SaxPowerCoordinator, change: dict[str, Any]
) -> None:
    coordinator._timed_charge_start = dt_time(0)
    coordinator._timed_charge_end = dt_time(23)
    coordinator.options |= change
    await _evaluate(coordinator)
    assert not coordinator._timed_charge_active
    assert coordinator._timed_charge_window is None


async def test_base_price_and_all_cheapest_windows_share_one_definition(
    coordinator: SaxPowerCoordinator,
) -> None:
    coordinator.options["economics_tou_base_price_eur_kwh"] = 0.05
    await _evaluate(coordinator)
    assert not coordinator._timed_charge_active
    await _evaluate(coordinator, NOW.replace(hour=6))
    assert coordinator._timed_charge_active
    coordinator.options = _options()
    coordinator.options["economics_tou_window_2"] = {
        "start": "06:00:00",
        "end": "08:00:00",
        "price_eur_kwh": 0.1,
    }
    await _evaluate(coordinator)
    state = coordinator._timed_charge_window
    await _evaluate(coordinator, NOW.replace(hour=6), soc=30)
    assert coordinator._timed_charge_active
    assert coordinator._timed_charge_window == state
    assert coordinator._tariff_charge_deadline == NOW.replace(hour=8)


async def test_month_change_ends_tariff_permission_at_midnight(
    coordinator: SaxPowerCoordinator,
) -> None:
    coordinator.options = _options("22:00:00", "06:00:00")
    coordinator._timed_charge_months = {9}
    now = datetime(2026, 9, 30, 23, tzinfo=UTC)
    await _evaluate(coordinator, now)
    assert coordinator._tariff_charge_deadline == datetime(2026, 10, 1, tzinfo=UTC)
    await _evaluate(coordinator, datetime(2026, 10, 1, tzinfo=UTC))
    assert not coordinator._timed_charge_active


async def test_tariff_edit_revokes_old_latch_and_hold(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator)
    window = coordinator._timed_charge_window
    assert window is not None
    coordinator._timed_discharge_state = TimedDischargeState(
        window.expires_at, window.source
    )
    coordinator.options = _options("01:00:00", "07:00:00")
    await _evaluate(coordinator, soc=30)
    assert not coordinator._timed_charge_active
    assert not coordinator._timed_charge_armed
    assert coordinator._timed_discharge_state is None
    await _evaluate(coordinator, soc=10)
    assert coordinator._timed_charge_active
    assert coordinator._tariff_charge_deadline == NOW.replace(hour=7)
    coordinator.options = _options("03:00:00", "07:00:00")
    await _evaluate(coordinator)
    assert not coordinator._timed_charge_active


@pytest.mark.parametrize("tariff_proof", [False, True])
async def test_restore_requires_exact_tariff_identity(
    coordinator: SaxPowerCoordinator, tariff_proof: bool
) -> None:
    state = coordinator._active_tariff_charge_state(NOW)
    assert state is not None
    coordinator._timed_charge_restore_state = (
        state
        if tariff_proof
        else TimedChargeState(state.start, state.end, state.expires_at)
    )
    coordinator._timed_discharge_state = TimedDischargeState(
        state.expires_at, state.source if tariff_proof else None
    )
    await _evaluate(coordinator, soc=30)
    assert coordinator._timed_charge_active is tariff_proof
    assert (coordinator._timed_discharge_state is not None) is tariff_proof


async def test_return_to_legacy_does_not_inherit_tariff_completion(
    coordinator: SaxPowerCoordinator,
) -> None:
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(5)
    coordinator._timed_discharge_last_window_end = NOW.replace(hour=3)
    coordinator._timed_discharge_last_source = "a" * 64
    coordinator.options = {"economics_tariff_type": "disabled"}
    await _evaluate(coordinator, NOW.replace(hour=4))
    assert coordinator._timed_charge_active


@pytest.mark.parametrize(
    "method",
    [
        "async_set_timed_charge_start",
        "async_set_timed_charge_end",
        "async_set_timed_charge_window",
    ],
)
async def test_legacy_time_writes_are_rejected_without_mutation(
    coordinator: SaxPowerCoordinator, method: str
) -> None:
    original = (coordinator.timed_charge_start, coordinator.timed_charge_end)
    args = (dt_time(1), dt_time(6)) if method.endswith("window") else (dt_time(1),)
    with pytest.raises(ServiceValidationError, match="Tarifpreisfenstern"):
        await getattr(coordinator, method)(*args)
    assert (coordinator.timed_charge_start, coordinator.timed_charge_end) == original
    assert not SaxPowerTimedChargeStartTime(coordinator, "test").available
    assert not SaxPowerTimedChargeEndTime(coordinator, "test").available


async def test_unused_legacy_overlap_does_not_block_months_or_pause(
    coordinator: SaxPowerCoordinator,
) -> None:
    coordinator._grid_serving_start = dt_time(12)
    coordinator._grid_serving_end = dt_time(18)
    await coordinator.async_set_timed_charge_month(10, True)
    await coordinator.async_set_grid_serving_window(
        dt_time(13), dt_time(17), defer_device_update=True
    )
    assert coordinator.grid_serving_start == dt_time(13)
    assert coordinator.timed_charge_start == dt_time(12)
    config = coordinator.control_config().sanitized(validate_legacy_windows=False)
    assert config.timed_charge_start == dt_time(12)


async def test_irrelevant_legacy_repairs_are_hidden_but_preserved(
    coordinator: SaxPowerCoordinator, hass: HomeAssistant
) -> None:
    coordinator._control_unresolved_fields = {"timed_charge_start", "timed_charge_end"}
    coordinator.reconcile_charge_time_source()
    issue_id = f"{ISSUE_CONTROL_CONFIG_UNRESOLVED}_{coordinator.entry_id}"
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None
    coordinator.options = {"economics_tariff_type": "disabled"}
    coordinator.reconcile_charge_time_source()
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is not None


async def test_deadline_stops_writer_without_poll(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator)
    deadline = coordinator._tariff_charge_deadline
    assert deadline is not None
    with (
        patch(PREFIX + "asyncio.sleep", new=AsyncMock()),
        patch(PREFIX + "dt_util.utcnow", return_value=deadline),
        patch(PREFIX + "dt_util.now", return_value=deadline),
    ):
        await coordinator._async_sun_charge_loop()
    coordinator.async_write_extended_register.assert_awaited_once_with(
        REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER
    )
    assert not coordinator._timed_charge_active
    assert coordinator._tariff_charge_deadline is None


@pytest.mark.parametrize("change", ["deadline", "tariff", "month", "disabled"])
async def test_late_mode_ack_cannot_extend_tariff_permission(
    coordinator: SaxPowerCoordinator, change: str
) -> None:
    await _evaluate(coordinator)
    clock = NOW

    async def write(address: int, value: int) -> None:
        nonlocal clock
        if value == SUN_IC_CONTROL_MODE_SETPOINT and address == REG_SUN_IC_CONTROL_MODE:
            if change == "deadline":
                clock = NOW.replace(hour=6)
            elif change == "tariff":
                coordinator.options = _options("03:00:00", "06:00:00")
            elif change == "month":
                coordinator._timed_charge_months = set()
            else:
                coordinator._timed_charge_enabled = False

    coordinator.async_write_extended_register = AsyncMock(side_effect=write)
    with (
        patch(PREFIX + "dt_util.now", side_effect=lambda: clock),
        patch(PREFIX + "dt_util.utcnow", side_effect=lambda: clock),
    ):
        with pytest.raises(HomeAssistantError):
            await coordinator._async_write_sun_charge_setpoint(
                MIN_SETPOINT_POWER, data=coordinator.data
            )
    assert [
        call.args for call in coordinator.async_write_extended_register.await_args_list
    ] == [
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT),
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER),
    ]


async def test_new_tariff_deadline_replaces_sleeping_writer(
    coordinator: SaxPowerCoordinator,
) -> None:
    sleeping = asyncio.create_task(asyncio.sleep(3600))
    coordinator._sun_charge_task = sleeping
    await _evaluate(coordinator)
    assert sleeping.cancelled()


async def test_outage_cannot_transfer_max_soc_hold_to_changed_tariff(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator, soc=80)
    assert coordinator._max_soc_clamped
    with patch(PREFIX + "dt_util.now", return_value=NOW):
        assert coordinator._max_soc_outage_hold_still_required()
        coordinator.options = _options("01:00:00", "07:00:00")
        assert not coordinator._max_soc_outage_hold_still_required()


async def test_missing_soc_preserves_confirmed_hold_until_its_own_deadline(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator)
    window = coordinator._timed_charge_window
    assert window is not None
    coordinator._timed_discharge_state = TimedDischargeState(
        window.expires_at, window.source
    )
    coordinator._basic_read_failed = True
    with (
        patch(PREFIX + "dt_util.utcnow", return_value=NOW),
        patch(PREFIX + "dt_util.now", return_value=NOW),
    ):
        await coordinator._async_suspend_charge_for_missing_soc()
    coordinator.async_start_sun_charge.assert_awaited_with(0, timed_discharge_hold=True)
    assert coordinator._active_charge_deadline() is None
    coordinator._sun_charge_timed_discharge = True
    coordinator._sun_charge_power = 0
    coordinator._async_write_sun_charge_setpoint = AsyncMock(
        side_effect=asyncio.CancelledError
    )
    with (
        patch(PREFIX + "asyncio.sleep", new=AsyncMock()),
        patch(PREFIX + "dt_util.utcnow", return_value=NOW),
        patch(PREFIX + "dt_util.now", return_value=NOW),
    ):
        with pytest.raises(asyncio.CancelledError):
            await coordinator._async_sun_charge_loop()
    coordinator._async_write_sun_charge_setpoint.assert_awaited_once_with(
        0, timed_discharge_hold=True
    )
    coordinator.async_write_extended_register.assert_not_awaited()


async def test_restore_long_low_tariff_phase_across_spring_gap(
    coordinator: SaxPowerCoordinator,
    hass: HomeAssistant,
) -> None:
    from zoneinfo import ZoneInfo

    await hass.config.async_set_time_zone("Europe/Berlin")
    now = datetime(2026, 3, 28, 3, tzinfo=ZoneInfo("Europe/Berlin"))
    coordinator.options = _options("02:15:00", "02:45:00")
    coordinator.options["economics_tou_base_price_eur_kwh"] = 0.05
    state = coordinator._active_tariff_charge_state(now)
    assert state is not None
    assert state.expires_at - now.astimezone(UTC) > timedelta(hours=25)
    proof = TimedDischargeState(state.expires_at, state.source)
    coordinator._timed_discharge_store.async_load = AsyncMock(return_value=proof)
    with patch(PREFIX + "dt_util.utcnow", return_value=now.astimezone(UTC)):
        await coordinator.async_load_timed_discharge_state()
    assert coordinator._timed_discharge_is_active(now)


async def test_return_to_legacy_revalidates_previously_unused_times(
    coordinator: SaxPowerCoordinator,
) -> None:
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(6)
    coordinator._grid_serving_start = dt_time(2)
    coordinator._grid_serving_end = dt_time(5)
    coordinator.reconcile_charge_time_source()
    assert coordinator.timed_charge_start == dt_time(1)
    coordinator.options = {"economics_tariff_type": "disabled"}
    coordinator.reconcile_charge_time_source()
    assert coordinator.timed_charge_start is None
    assert coordinator.timed_charge_end is None
    await _evaluate(coordinator)
    assert not coordinator._timed_charge_active


async def test_legacy_mode_ack_cannot_authorize_new_tariff_outside_low_price(
    coordinator: SaxPowerCoordinator,
) -> None:
    coordinator.options = {"economics_tariff_type": "disabled"}
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(6)
    await _evaluate(coordinator)
    assert coordinator._timed_charge_active
    assert coordinator._tariff_charge_deadline is None

    async def write(address: int, value: int) -> None:
        if address == REG_SUN_IC_CONTROL_MODE and value == SUN_IC_CONTROL_MODE_SETPOINT:
            coordinator.options = _options("03:00:00", "06:00:00")

    coordinator.async_write_extended_register = AsyncMock(side_effect=write)
    with (
        patch(PREFIX + "dt_util.now", return_value=NOW),
        patch(PREFIX + "dt_util.utcnow", return_value=NOW),
    ):
        with pytest.raises(HomeAssistantError, match="Tarifquelle"):
            await coordinator._async_write_sun_charge_setpoint(
                MIN_SETPOINT_POWER, data=coordinator.data
            )
    assert [
        call.args for call in coordinator.async_write_extended_register.await_args_list
    ] == [
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT),
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER),
    ]


@pytest.mark.parametrize("initial_tariff", [True, False])
async def test_source_change_during_persistence_cannot_rebind_old_decision(
    coordinator: SaxPowerCoordinator,
    initial_tariff: bool,
) -> None:
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(6)
    if not initial_tariff:
        coordinator.options = {"economics_tariff_type": "disabled"}
    await _evaluate(coordinator)
    assert coordinator._timed_charge_armed
    coordinator.async_start_sun_charge.reset_mock()

    async def change_source(now: datetime) -> None:
        coordinator.options = (
            {"economics_tariff_type": "disabled"} if initial_tariff else _options()
        )

    coordinator._async_update_timed_discharge_proof = AsyncMock(
        side_effect=change_source
    )
    await _evaluate(coordinator, soc=30)
    coordinator.async_start_sun_charge.assert_not_awaited()
    assert not coordinator._timed_charge_active
    assert coordinator._timed_charge_window is None
    assert not coordinator._timed_charge_armed
    assert coordinator._active_charge_deadline() is None
    coordinator.async_stop_sun_charge.assert_awaited()
