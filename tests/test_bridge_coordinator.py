"""Device control boundaries for REQ-BRIDGE-CHARGE."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.sax_power.application.timed_discharge import TimedDischargeState
from custom_components.sax_power.const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    MIN_SETPOINT_POWER,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

NOW = datetime(2026, 9, 13, tzinfo=UTC)
_CLOCK = "custom_components.sax_power.coordinator.monotonic"


@pytest.fixture
async def coordinator(hass: HomeAssistant) -> AsyncIterator[SaxPowerCoordinator]:
    instance = SaxPowerCoordinator(
        hass,
        MagicMock(),
        64,
        100,
        10,
        "bridge-test",
        options={
            CONF_BRIDGE_CHARGE_ENABLED: True,
            "economics_tariff_type": "time_of_use",
            "economics_feed_in_price_eur_kwh": 0.08,
            "economics_tou_base_price_eur_kwh": 0.4,
            "economics_tou_window_1": {
                "start": "00:00:00",
                "end": "06:00:00",
                "price_eur_kwh": 0.1,
            },
        },
    )
    instance._pv_bridge_forecast = MagicMock()
    instance._pv_bridge_forecast.pv_start.return_value = NOW + timedelta(hours=1)
    instance._pv_bridge_forecast.async_refresh = AsyncMock()
    instance._control_bootstrap_pending = False
    instance._timed_charge_enabled = True
    instance._timed_charge_start = dt_time(0)
    instance._timed_charge_end = dt_time(6)
    instance._timed_charge_min_soc = 0
    instance._timed_charge_max_soc = 80
    instance._max_soc = 80
    instance.async_start_sun_charge = AsyncMock()
    instance.async_stop_sun_charge = AsyncMock()
    instance.async_write_extended_register = AsyncMock()
    yield instance
    await instance.async_shutdown()


def _data(
    now: datetime, *, soc: float = 10, observation: bool = True
) -> dict[str, Any]:
    return {
        "soc": round(soc),
        "battery_soc": soc,
        "battery_soc_min": 10,
        "battery_capacity": 10000,
        "ic_max_power_reference": 1000,
        "smartmeter_power": 500,
        "storage_power_active": 1000,
        "discharge_forecast_attributes": (
            {
                "observed_at": now.isoformat(),
                "observation_minutes": 30,
                "average_discharge_w": 1000,
            }
            if observation
            else {}
        ),
    }


async def _evaluate(
    coordinator: SaxPowerCoordinator, now: datetime, data: dict[str, Any]
) -> None:
    coordinator.data = data
    coordinator._high_data = dict(data)
    coordinator._high_sample_time = 100
    with (
        patch(_CLOCK, return_value=100),
        patch("custom_components.sax_power.coordinator.dt_util.now", return_value=now),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow", return_value=now
        ),
    ):
        await coordinator._async_enforce_grid_charge_locked(data)
        coordinator._publish_charge_state(data)


async def test_planned_charge_replaces_min_soc_trigger_and_survives_forecast_reset(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator, NOW, _data(NOW))
    assert coordinator._timed_charge_active
    coordinator.async_start_sun_charge.assert_awaited_with(
        MIN_SETPOINT_POWER, data=coordinator.data
    )
    deadline = coordinator._bridge_charge_deadline
    assert deadline == NOW + timedelta(minutes=30)
    later = NOW + timedelta(minutes=2)
    await _evaluate(coordinator, later, _data(later, soc=11, observation=False))
    assert coordinator._timed_charge_active
    assert coordinator._bridge_charge_deadline == deadline
    assert coordinator.data["bridge_charge_plan"] == "charging"
    assert (
        coordinator.data["bridge_charge_plan_attributes"]["observation_minutes"] == 30
    )


@pytest.mark.parametrize("gap", ["pv", "measurements", "stale_measurements"])
@pytest.mark.parametrize("changed_pv_start", [False, True])
async def test_transient_data_gap_pauses_and_resumes_frozen_bridge_plan(
    coordinator: SaxPowerCoordinator, gap: str, changed_pv_start: bool
) -> None:
    """REQ-BRIDGE-CHARGE: Missing inputs stop writes without losing demand (#247)."""
    await _evaluate(coordinator, NOW, _data(NOW))
    plan = coordinator._bridge_session.plan
    attributes = dict(coordinator._bridge_session.attributes)
    interrupted = NOW + timedelta(minutes=2)
    data = _data(interrupted, soc=11, observation=False)
    if gap == "pv":
        coordinator._pv_bridge_forecast.pv_start.return_value = None
    elif gap == "measurements":
        data["battery_capacity"] = None
    with patch.object(
        coordinator,
        "_timed_discharge_measurements_fresh",
        return_value=gap != "stale_measurements",
    ):
        await _evaluate(coordinator, interrupted, data)
    assert not coordinator._timed_charge_active
    assert coordinator._bridge_charge_deadline is None
    coordinator.async_stop_sun_charge.assert_awaited()
    assert coordinator._bridge_session.plan is plan
    assert coordinator._bridge_session.started
    assert coordinator.data["bridge_charge_plan"] == "paused"
    assert coordinator._bridge_session.attributes == attributes | {
        "reason": "pv_start_missing" if gap == "pv" else "measurements_missing",
        "data_gap_reason": (
            "pv_start_missing" if gap == "pv" else "measurements_missing"
        ),
    }

    recovered = interrupted + timedelta(seconds=2)
    coordinator._pv_bridge_forecast.pv_start.return_value = NOW + timedelta(
        hours=2 if changed_pv_start else 1
    )
    await _evaluate(coordinator, recovered, _data(recovered, soc=11, observation=False))
    assert coordinator._timed_charge_active
    assert coordinator._bridge_session.plan is plan
    assert coordinator._bridge_charge_deadline == NOW + timedelta(minutes=30)
    assert coordinator._bridge_session.attributes == attributes


@pytest.mark.parametrize("invalidate", ["deadline", "target", "configuration"])
async def test_data_gap_cannot_resume_expired_or_invalidated_bridge_plan(
    coordinator: SaxPowerCoordinator, invalidate: str
) -> None:
    """REQ-BRIDGE-CHARGE: A pause never extends a plan or its authorization."""
    await _evaluate(coordinator, NOW, _data(NOW))
    plan = coordinator._bridge_session.plan
    assert plan is not None and plan.end is not None
    interrupted = NOW + timedelta(minutes=2)
    coordinator._pv_bridge_forecast.pv_start.return_value = None
    await _evaluate(
        coordinator, interrupted, _data(interrupted, soc=11, observation=False)
    )
    assert coordinator._bridge_session.plan is plan
    if invalidate == "configuration":
        coordinator._max_soc = 12
    recovered = (
        plan.end if invalidate == "deadline" else interrupted + timedelta(seconds=2)
    )
    coordinator._pv_bridge_forecast.pv_start.return_value = NOW + timedelta(hours=1)
    coordinator.async_start_sun_charge.reset_mock()
    await _evaluate(
        coordinator,
        recovered,
        _data(
            recovered,
            soc=plan.target_soc if invalidate == "target" else 11,
            observation=False,
        ),
    )
    assert not coordinator._timed_charge_active
    assert coordinator._bridge_charge_deadline is None
    assert not coordinator._bridge_session.started
    coordinator.async_start_sun_charge.assert_not_awaited()


async def test_configuration_change_during_gap_discards_frozen_plan_immediately(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator, NOW, _data(NOW))
    coordinator._pv_bridge_forecast.pv_start.return_value = None
    coordinator._max_soc = 12
    interrupted = NOW + timedelta(minutes=2)
    await _evaluate(
        coordinator, interrupted, _data(interrupted, soc=11, observation=False)
    )
    assert not coordinator._bridge_session.started
    assert coordinator._bridge_session.plan is None
    coordinator._max_soc = 80
    coordinator._pv_bridge_forecast.pv_start.return_value = NOW + timedelta(hours=1)
    recovered = interrupted + timedelta(seconds=2)
    await _evaluate(coordinator, recovered, _data(recovered, soc=11, observation=False))
    assert not coordinator._timed_charge_active


@pytest.mark.parametrize("setting", ["enabled", "max_soc"])
@pytest.mark.parametrize("defer_device_update", [False, True])
async def test_configuration_round_trip_during_basic_outage_discards_frozen_plan(
    coordinator: SaxPowerCoordinator, setting: str, defer_device_update: bool
) -> None:
    """REQ-BRIDGE-CHARGE: Basic outage cannot hide revoked charge permissions."""
    await _evaluate(coordinator, NOW, _data(NOW))
    coordinator._basic_read_failed = True
    interrupted = NOW + timedelta(minutes=2)
    await _evaluate(
        coordinator, interrupted, _data(interrupted, soc=11, observation=False)
    )
    assert not coordinator._timed_charge_active
    assert coordinator._bridge_session.started
    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=interrupted,
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=interrupted,
        ),
    ):
        if setting == "enabled":
            await coordinator.async_set_timed_charge_enabled(
                False, defer_device_update=defer_device_update
            )
            await coordinator.async_set_timed_charge_enabled(
                True, defer_device_update=defer_device_update
            )
        else:
            await coordinator.async_set_max_soc(
                12, defer_device_update=defer_device_update
            )
            await coordinator.async_set_max_soc(
                80, defer_device_update=defer_device_update
            )
    assert not coordinator._bridge_session.started
    assert coordinator._bridge_session.plan is None
    recovered = interrupted + timedelta(seconds=2)
    coordinator._basic_read_failed = False
    coordinator.async_start_sun_charge.reset_mock()
    await _evaluate(coordinator, recovered, _data(recovered, soc=11, observation=False))
    assert not coordinator._timed_charge_active
    assert coordinator._bridge_session.attributes["reason"] == "consumption_missing"
    coordinator.async_start_sun_charge.assert_not_awaited()


async def test_plan_expiring_during_gap_requires_a_minute_before_replanning(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-BRIDGE-CHARGE: An outage cannot bypass the post-charge observation wait."""
    coordinator._pv_bridge_forecast.pv_start.return_value = NOW + timedelta(minutes=1)
    await _evaluate(coordinator, NOW, _data(NOW))
    plan = coordinator._bridge_session.plan
    assert plan is not None and plan.end == NOW + timedelta(seconds=30)
    coordinator._pv_bridge_forecast.pv_start.return_value = None
    await _evaluate(coordinator, plan.end, _data(plan.end))
    assert not coordinator._bridge_session.started
    coordinator._pv_bridge_forecast.pv_start.return_value = NOW + timedelta(minutes=1)
    recovered = plan.end + timedelta(seconds=2)
    coordinator.async_start_sun_charge.reset_mock()
    await _evaluate(coordinator, recovered, _data(recovered))
    assert not coordinator._timed_charge_active
    assert coordinator._bridge_session.plan is plan
    assert coordinator._bridge_session.completed_at == plan.end
    coordinator.async_start_sun_charge.assert_not_awaited()


async def test_basic_read_failure_preserves_bounded_plan_for_recovery(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-BRIDGE-CHARGE: The poll exception path must preserve the same pause."""
    await _evaluate(coordinator, NOW, _data(NOW))
    plan = coordinator._bridge_session.plan
    interrupted = NOW + timedelta(minutes=2)
    with (
        patch.object(coordinator, "_async_read_basic", side_effect=UpdateFailed),
        patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=interrupted,
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=interrupted,
        ),
    ):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
    assert not coordinator._timed_charge_active
    assert coordinator._bridge_charge_deadline is None
    assert coordinator._bridge_session.plan is plan
    assert coordinator._bridge_session.started
    assert coordinator._bridge_session.status == "paused"
    coordinator.async_stop_sun_charge.assert_awaited()
    recovered = interrupted + timedelta(seconds=2)
    data = _data(recovered, soc=11, observation=False)

    async def read_extended() -> dict[str, Any]:
        coordinator._high_sample_time = 100
        coordinator._high_data = dict(data)
        return data

    with (
        patch.object(coordinator, "_async_read_basic", return_value={"soc": 11}),
        patch.object(coordinator, "_async_read_extended", side_effect=read_extended),
        patch(_CLOCK, return_value=100),
        patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=recovered,
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=recovered,
        ),
    ):
        await coordinator._async_update_data()
    assert coordinator._timed_charge_active
    assert coordinator._bridge_session.plan is plan
    assert coordinator._bridge_charge_deadline == NOW + timedelta(minutes=30)


async def test_no_charge_if_existing_energy_covers_until_pv(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator, NOW, _data(NOW, soc=60))
    assert coordinator.data["bridge_charge_plan"] == "not_needed"
    assert not coordinator._timed_charge_active
    coordinator.async_start_sun_charge.assert_not_awaited()


@pytest.mark.parametrize("stop", ["end", "target"])
async def test_stop_at_deadline_or_precise_target_and_release_discharge(
    coordinator: SaxPowerCoordinator, stop: str
) -> None:
    await _evaluate(coordinator, NOW, _data(NOW))
    plan = coordinator._bridge_session.plan
    assert plan is not None
    when = plan.end if stop == "end" else NOW + timedelta(minutes=20)
    assert when is not None
    await _evaluate(
        coordinator, when, _data(when, soc=plan.target_soc, observation=False)
    )
    assert not coordinator._timed_charge_active
    assert coordinator._bridge_charge_deadline is None
    coordinator.async_stop_sun_charge.assert_awaited()
    assert coordinator._timed_discharge_state is None


async def test_basic_soc_rounding_does_not_replace_precise_plan_target(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator, NOW, _data(NOW))
    later = NOW + timedelta(minutes=29)
    await _evaluate(coordinator, later, _data(later, soc=14.9, observation=False))
    assert coordinator._bridge_session.plan.target_soc == 15
    assert coordinator.data["soc"] == 15
    assert coordinator._timed_charge_active


@pytest.mark.parametrize(
    "key,value",
    [
        ("battery_soc", -1),
        ("battery_soc", 101),
        ("battery_capacity", 0),
        ("ic_max_power_reference", 0),
        ("battery_soc_min", None),
    ],
)
async def test_invalid_measurement_stops_active_plan(
    coordinator: SaxPowerCoordinator, key: str, value: Any
) -> None:
    await _evaluate(coordinator, NOW, _data(NOW))
    later = NOW + timedelta(minutes=2)
    data = _data(later, observation=False)
    data[key] = value
    await _evaluate(coordinator, later, data)
    assert not coordinator._timed_charge_active
    assert coordinator.data["bridge_charge_plan"] == "paused"
    coordinator.async_stop_sun_charge.assert_awaited()


@pytest.mark.parametrize(
    "setting", ["disabled", "months", "pv_missing", "window", "max_soc"]
)
async def test_changed_permissions_invalidate_running_plan(
    coordinator: SaxPowerCoordinator, setting: str
) -> None:
    await _evaluate(coordinator, NOW, _data(NOW))
    if setting == "disabled":
        coordinator._timed_charge_enabled = False
    elif setting == "months":
        coordinator._timed_charge_months = set()
    elif setting == "pv_missing":
        coordinator._pv_bridge_forecast.pv_start.return_value = None
    elif setting == "window":
        coordinator.options = dict(coordinator.options) | {
            "economics_tou_window_1": {
                "start": "03:00:00",
                "end": "06:00:00",
                "price_eur_kwh": 0.1,
            }
        }
    else:
        coordinator._max_soc = 12
    later = NOW + timedelta(minutes=2)
    await _evaluate(coordinator, later, _data(later, soc=11, observation=False))
    assert not coordinator._timed_charge_active
    assert coordinator._bridge_charge_deadline is None


async def test_new_mode_clears_legacy_discharge_hold(
    coordinator: SaxPowerCoordinator,
) -> None:
    coordinator._timed_discharge_state = TimedDischargeState(NOW + timedelta(hours=6))
    await _evaluate(coordinator, NOW, _data(NOW, soc=60))
    assert coordinator._timed_discharge_state is None
    assert not coordinator._timed_discharge_is_active(NOW)


async def test_writer_enforces_expiry_without_poll(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator, NOW, _data(NOW))
    deadline = coordinator._bridge_charge_deadline
    with (
        patch("custom_components.sax_power.coordinator.asyncio.sleep", new=AsyncMock()),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=deadline,
        ),
    ):
        await coordinator._async_sun_charge_loop()
    coordinator.async_write_extended_register.assert_awaited_once_with(
        REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER
    )
    assert not coordinator._timed_charge_active
    assert coordinator._bridge_charge_deadline is None


async def test_writer_pauses_on_missing_forecast_without_poll(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-BRIDGE-CHARGE: A stale forecast cannot authorize a periodic write."""
    await _evaluate(coordinator, NOW, _data(NOW))
    plan = coordinator._bridge_session.plan
    coordinator._pv_bridge_forecast.pv_start.return_value = None
    with (
        patch("custom_components.sax_power.coordinator.asyncio.sleep", new=AsyncMock()),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow", return_value=NOW
        ),
        patch(_CLOCK, return_value=100),
        patch.object(
            coordinator,
            "_async_write_sun_charge_setpoint",
            side_effect=AssertionError("No periodic setpoint without PV forecast"),
        ),
    ):
        await coordinator._async_sun_charge_loop()
    coordinator.async_write_extended_register.assert_awaited_once_with(
        REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER
    )
    assert not coordinator._timed_charge_active
    assert coordinator._bridge_charge_deadline is None
    assert coordinator._bridge_session.plan is plan
    assert coordinator._bridge_session.started
    assert coordinator._bridge_session.status == "paused"
    assert coordinator._bridge_session.attributes["reason"] == "pv_start_missing"


@pytest.mark.parametrize("phase", ["before", "mode_ack", "setpoint_ack"])
async def test_forecast_gap_blocks_or_rolls_back_charge_ack(
    coordinator: SaxPowerCoordinator, phase: str
) -> None:
    """REQ-BRIDGE-CHARGE: Each ACK must still have a current forecast."""
    await _evaluate(coordinator, NOW, _data(NOW))

    async def write(address: int, value: int) -> None:
        if (
            (
                phase == "mode_ack"
                and address == REG_SUN_IC_CONTROL_MODE
                and value == SUN_IC_CONTROL_MODE_SETPOINT
            )
            or phase == "setpoint_ack"
            and address == REG_SUN_IC_POWER_SETPOINT_PCT
        ):
            coordinator._pv_bridge_forecast.pv_start.return_value = None

    coordinator.async_write_extended_register = AsyncMock(side_effect=write)
    if phase == "before":
        coordinator._pv_bridge_forecast.pv_start.return_value = None
    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow", return_value=NOW
        ),
        patch(_CLOCK, return_value=100),
    ):
        with pytest.raises(HomeAssistantError):
            await coordinator._async_write_sun_charge_setpoint(
                MIN_SETPOINT_POWER, data=coordinator.data
            )
    calls = [
        call.args for call in coordinator.async_write_extended_register.await_args_list
    ]
    if phase == "before":
        assert calls == []
    else:
        assert calls[0] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT)
        assert calls[-1] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER)
        assert len(calls) == (3 if phase == "setpoint_ack" else 2)


async def test_new_deadline_replaces_sleeping_legacy_writer(
    coordinator: SaxPowerCoordinator,
) -> None:
    sleeping = asyncio.create_task(asyncio.sleep(3600))
    coordinator._sun_charge_task = sleeping
    await _evaluate(coordinator, NOW, _data(NOW))
    assert sleeping.cancelled()
    assert coordinator._bridge_charge_deadline == NOW + timedelta(minutes=30)


async def test_deadline_expiring_during_mode_ack_rolls_back_without_setpoint(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-BRIDGE-CHARGE: An ACK cannot extend the finite charge permission."""
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.sax_power.const import SUN_IC_CONTROL_MODE_SETPOINT

    await _evaluate(coordinator, NOW, _data(NOW))
    coordinator._bridge_charge_deadline = NOW + timedelta(seconds=2)
    clock = NOW

    async def write(address: int, value: int) -> None:
        nonlocal clock
        if address == REG_SUN_IC_CONTROL_MODE and value == SUN_IC_CONTROL_MODE_SETPOINT:
            clock = NOW + timedelta(seconds=3)

    coordinator.async_write_extended_register = AsyncMock(side_effect=write)
    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            side_effect=lambda: clock,
        ),
        patch(_CLOCK, return_value=100),
    ):
        with pytest.raises(HomeAssistantError):
            await coordinator._async_write_sun_charge_setpoint(
                MIN_SETPOINT_POWER, data=coordinator.data
            )
    calls = [
        call.args for call in coordinator.async_write_extended_register.await_args_list
    ]
    assert calls == [
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT),
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER),
    ]


@pytest.mark.parametrize("low_tariff", [True, False])
async def test_calibration_cannot_restore_hidden_legacy_window(
    coordinator: SaxPowerCoordinator, low_tariff: bool
) -> None:
    """REQ-BRIDGE-CHARGE: Calibration raises only the cap, not tariff permission."""
    coordinator._cell_calibration_active = True
    coordinator._async_update_cell_calibration = AsyncMock(return_value=False)
    coordinator._timed_charge_min_soc = 100
    coordinator._timed_charge_start = dt_time(12) if low_tariff else dt_time(0)
    coordinator._timed_charge_end = dt_time(18) if low_tariff else dt_time(6)
    if not low_tariff:
        coordinator.options = dict(coordinator.options) | {
            "economics_tou_window_1": {
                "start": "03:00:00",
                "end": "06:00:00",
                "price_eur_kwh": 0.1,
            }
        }
    await _evaluate(coordinator, NOW, _data(NOW))
    assert coordinator._timed_charge_active is low_tariff
    assert coordinator.effective_timed_charge_max_soc == 100


async def test_replanning_uses_same_new_consumption_for_pv_and_energy(
    coordinator: SaxPowerCoordinator,
) -> None:
    await _evaluate(coordinator, NOW, _data(NOW))
    end = coordinator._bridge_charge_deadline
    assert end is not None
    await _evaluate(coordinator, end, _data(end, soc=15, observation=False))
    next_time = end + timedelta(minutes=1)
    data = _data(next_time, soc=14)
    data["discharge_forecast_attributes"]["average_discharge_w"] = 2000
    await _evaluate(coordinator, next_time, data)
    coordinator._pv_bridge_forecast.pv_start.assert_called_with(next_time, 2000)
    assert coordinator._bridge_session.attributes["average_discharge_w"] == 2000


@pytest.mark.parametrize(
    "soc,status,shortfall", [(11, "insufficient", 0.4), (15, "complete", 0)]
)
async def test_deadline_with_missing_pv_reports_measured_completion(
    coordinator: SaxPowerCoordinator, soc: float, status: str, shortfall: float
) -> None:
    """REQ-BRIDGE-CHARGE: Forecast gaps cannot hide a charge shortfall (#252)."""
    await _evaluate(coordinator, NOW, _data(NOW))
    plan = coordinator._bridge_session.plan
    assert plan is not None and plan.end is not None
    coordinator._pv_bridge_forecast.pv_start.return_value = None
    await _evaluate(coordinator, plan.end, _data(plan.end, soc=soc, observation=False))
    attributes = coordinator.data["bridge_charge_plan_attributes"]
    assert coordinator.data["bridge_charge_plan"] == status
    assert attributes["shortfall_kwh"] == pytest.approx(shortfall)
    assert attributes["reason"] == ("charge_shortfall" if shortfall else None)
    assert attributes["data_gap_reason"] == "pv_start_missing"
    assert attributes["completion_evaluated_at"] == plan.end.isoformat()
    assert not coordinator._bridge_session.started
    coordinator.async_start_sun_charge.reset_mock()
    recovered = plan.end + timedelta(minutes=2)
    coordinator._pv_bridge_forecast.pv_start.return_value = NOW + timedelta(hours=3)
    await _evaluate(
        coordinator, recovered, _data(recovered, soc=soc, observation=False)
    )
    assert coordinator.data["bridge_charge_plan"] == status
    assert coordinator.data["bridge_charge_plan_attributes"] == attributes
    coordinator.async_start_sun_charge.assert_not_awaited()


@pytest.mark.parametrize("gap", ["missing", "stale", "pv_and_stale"])
@pytest.mark.parametrize("recovery_soc", [11, 15])
async def test_expired_plan_defers_completion_until_measurements_recover(
    coordinator: SaxPowerCoordinator, gap: str, recovery_soc: float
) -> None:
    """REQ-BRIDGE-CHARGE: Unknown energy is never replaced by cached plan zero."""
    await _evaluate(coordinator, NOW, _data(NOW))
    plan = coordinator._bridge_session.plan
    assert plan is not None and plan.end is not None
    data = _data(plan.end, soc=50, observation=False)
    if gap == "missing":
        data["battery_capacity"] = None
    if gap == "pv_and_stale":
        coordinator._pv_bridge_forecast.pv_start.return_value = None
    with patch.object(
        coordinator,
        "_timed_discharge_measurements_fresh",
        return_value=gap == "missing",
    ):
        await _evaluate(coordinator, plan.end, data)
    attributes = coordinator.data["bridge_charge_plan_attributes"]
    assert coordinator.data["bridge_charge_plan"] == "waiting_for_data"
    assert attributes["shortfall_kwh"] is None
    assert attributes["completion_evaluated_at"] is None
    assert attributes["reason"] == "measurements_missing"
    assert attributes["data_gap_reason"] == (
        "pv_start_missing" if gap == "pv_and_stale" else "measurements_missing"
    )
    recovered = plan.end + timedelta(minutes=2)
    coordinator.async_start_sun_charge.reset_mock()
    await _evaluate(
        coordinator, recovered, _data(recovered, soc=recovery_soc, observation=False)
    )
    shortfall = max(0, 28 / 60 - (recovery_soc - 10) / 10)
    assert coordinator.data["bridge_charge_plan"] == (
        "insufficient" if shortfall else "complete"
    )
    attributes = coordinator.data["bridge_charge_plan_attributes"]
    assert attributes["shortfall_kwh"] == pytest.approx(shortfall)
    assert attributes["completion_evaluated_at"] == recovered.isoformat()
    assert attributes["reason"] == ("charge_shortfall" if shortfall else None)
    assert coordinator._bridge_session.plan is plan
    assert coordinator._bridge_session.completed_at == plan.end
    assert not coordinator._timed_charge_active
    coordinator.async_start_sun_charge.assert_not_awaited()


async def test_target_soc_with_missing_pv_finishes_frozen_plan_before_deadline(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-BRIDGE-CHARGE: Fresh target feedback also ends a paused charge."""
    await _evaluate(coordinator, NOW, _data(NOW))
    coordinator._pv_bridge_forecast.pv_start.return_value = None
    finished = NOW + timedelta(minutes=20)
    await _evaluate(coordinator, finished, _data(finished, soc=15, observation=False))
    assert not coordinator._bridge_session.started
    assert coordinator._bridge_session.completed_at == finished
    assert coordinator.data["bridge_charge_plan"] == "insufficient"
    assert coordinator.data["bridge_charge_plan_attributes"][
        "shortfall_kwh"
    ] == pytest.approx(1 / 6)


@pytest.mark.parametrize("pv_available", [True, False])
async def test_completion_needs_no_charge_power_reference(
    coordinator: SaxPowerCoordinator, pv_available: bool
) -> None:
    """REQ-BRIDGE-CHARGE: Actual remaining energy does not need a charging rate."""
    await _evaluate(coordinator, NOW, _data(NOW))
    plan = coordinator._bridge_session.plan
    assert plan is not None and plan.end is not None
    if not pv_available:
        coordinator._pv_bridge_forecast.pv_start.return_value = None
    data = _data(plan.end, soc=11, observation=False)
    data["ic_max_power_reference"] = None
    await _evaluate(coordinator, plan.end, data)
    assert coordinator.data["bridge_charge_plan"] == "insufficient"
    assert coordinator.data["bridge_charge_plan_attributes"][
        "shortfall_kwh"
    ] == pytest.approx(0.4)


@pytest.mark.parametrize("measurements_fresh", [True, False])
async def test_writer_expiry_uses_only_fresh_measurements_for_completion(
    coordinator: SaxPowerCoordinator, measurements_fresh: bool
) -> None:
    """REQ-BRIDGE-CHARGE: Deadline enforcement and polls share the same verdict."""
    await _evaluate(coordinator, NOW, _data(NOW))
    deadline = coordinator._bridge_charge_deadline
    assert deadline is not None
    coordinator.data = _data(deadline, soc=50, observation=False)
    coordinator._high_data = _data(deadline, soc=11, observation=False)
    with (
        patch("custom_components.sax_power.coordinator.asyncio.sleep", new=AsyncMock()),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=deadline,
        ),
        patch.object(
            coordinator,
            "_timed_discharge_measurements_fresh",
            return_value=measurements_fresh,
        ),
    ):
        await coordinator._async_sun_charge_loop()
    attributes = coordinator.data["bridge_charge_plan_attributes"]
    assert attributes["completed_at"] == deadline.isoformat()
    if measurements_fresh:
        assert coordinator.data["bridge_charge_plan"] == "insufficient"
        assert attributes["shortfall_kwh"] == pytest.approx(0.4)
        assert "data_gap_reason" not in attributes
    else:
        assert coordinator.data["bridge_charge_plan"] == "waiting_for_data"
        assert attributes["shortfall_kwh"] is None
        assert attributes["data_gap_reason"] == "measurements_missing"
    assert not coordinator._timed_charge_active
    coordinator.async_write_extended_register.assert_awaited_once_with(
        REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER
    )


async def test_invalid_new_consumption_cannot_erase_completed_plan(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-BRIDGE-CHARGE: Invalid new demand leaves the prior verdict reviewable."""
    await _evaluate(coordinator, NOW, _data(NOW))
    deadline = coordinator._bridge_charge_deadline
    assert deadline is not None
    await _evaluate(coordinator, deadline, _data(deadline, soc=11, observation=False))
    later = deadline + timedelta(minutes=2)
    data = _data(later)
    data["discharge_forecast_attributes"]["average_discharge_w"] = None
    await _evaluate(coordinator, later, data)
    assert coordinator.data["bridge_charge_plan"] == "insufficient"
    assert coordinator.data["bridge_charge_plan_attributes"][
        "shortfall_kwh"
    ] == pytest.approx(0.4)
    assert coordinator._bridge_session.completed_at == deadline
