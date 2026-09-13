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

from custom_components.sax_power.application.timed_discharge import TimedDischargeState
from custom_components.sax_power.const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    MIN_SETPOINT_POWER,
    REG_SUN_IC_CONTROL_MODE,
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
    assert coordinator.data["bridge_charge_plan"] == "waiting_for_data"
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
