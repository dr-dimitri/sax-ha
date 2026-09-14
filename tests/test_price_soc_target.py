"""REQ-DYNAMIC-PRICE-CHARGE: Preisfenster-Hysterese gehört zum erreichten Ziel."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.application.calibration import CalibrationState
from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_PRICE_SENSOR,
    PRICE_STATUS_PAUSED_MAX_SOC,
    PV_SURPLUS_HYSTERESIS_CYCLES,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

from .test_price_optimizer import _make_client, _make_coordinator

_BERLIN = ZoneInfo("Europe/Berlin")


@pytest.fixture
async def price_hold(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[tuple[SaxPowerCoordinator, list[datetime]]]:
    await hass.config.async_set_time_zone("Europe/Berlin")
    clock = [datetime(2026, 9, 14, 23, 58, tzinfo=_BERLIN)]
    monkeypatch.setattr(dt_util, "now", lambda: clock[0])
    monkeypatch.setattr(dt_util, "utcnow", lambda: clock[0].astimezone(UTC))
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.options = {
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_ECONOMICS_TARIFF_TYPE: "dynamic",
        CONF_PRICE_SENSOR: "sensor.price",
    }
    coordinator._max_soc = 60
    coordinator._price_charge_enabled = True
    coordinator._price_charge_strategy = "absolute"
    coordinator._price_charge_max_price = 0.2
    coordinator.data = {
        "soc": 59,
        "smartmeter_power": 0,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    hass.states.async_set(
        "sensor.price",
        "0.1",
        {
            "unit_of_measurement": "EUR/kWh",
            "prices": [
                {
                    "start": (clock[0] - timedelta(hours=1)).isoformat(),
                    "end": (clock[0] + timedelta(hours=2)).isoformat(),
                    "price": 0.1,
                }
            ],
        },
    )
    try:
        assert coordinator.price_planner.evaluate().charge_now
        await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator.price_charge_active
        coordinator.data["soc"] = 60
        await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator.max_soc_clamped
        assert coordinator._sun_charge_power == 0
        coordinator.client.write_register.reset_mock()
        yield coordinator, clock
    finally:
        await coordinator.async_shutdown(reset_device=False)
        await hass.config.async_set_time_zone("UTC")


async def test_raised_target_releases_price_hold_and_stops_at_new_target(
    price_hold: tuple[SaxPowerCoordinator, list[datetime]],
) -> None:
    """Ein realer neuer Preisplan lädt nach 60→80 wieder und hält bei 80 %."""
    coordinator, _ = price_hold
    await coordinator.async_set_max_soc(80)
    assert coordinator.price_charge_active
    assert not coordinator.max_soc_clamped
    assert coordinator._sun_charge_power < 0
    coordinator.data["soc"] = 80
    await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator.max_soc_clamped
    assert not coordinator.price_charge_active
    assert coordinator._sun_charge_power == 0


async def test_midnight_calibration_releases_old_price_hold(
    price_hold: tuple[SaxPowerCoordinator, list[datetime]],
) -> None:
    """REQ-PERIODIC-FULL-CALIBRATION: Das fällige 100-%-Ziel löst die 60-%-Sperre."""
    coordinator, clock = price_hold
    coordinator._cell_calibration_state = CalibrationState(
        datetime(2026, 9, 12, 15, tzinfo=_BERLIN).astimezone(UTC)
    )
    clock[0] = datetime(2026, 9, 15, 0, 0, 2, tzinfo=_BERLIN)
    await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator.cell_calibration_active
    assert coordinator.effective_max_soc == 100
    assert coordinator.max_soc == 60
    assert coordinator.price_charge_active
    assert not coordinator.max_soc_clamped
    assert coordinator._sun_charge_power < 0


@pytest.mark.parametrize("target,soc", [(60, 59), (50, 60), (65, 70)])
async def test_unchanged_or_insufficient_target_keeps_price_hold(
    price_hold: tuple[SaxPowerCoordinator, list[datetime]], target: int, soc: int
) -> None:
    """SOC-Abfall, Netzbezug und ein weiterhin überschrittenes Ziel laden nicht."""
    coordinator, _ = price_hold
    coordinator.data.update(soc=soc, smartmeter_power=500)
    await coordinator.async_set_max_soc(target)
    for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES + 1):
        coordinator._high_sample_revision += 1
        await coordinator._async_enforce_grid_charge(coordinator.data)
    coordinator.data["soc"] = target - 1
    await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator.max_soc_clamped
    assert not coordinator.price_charge_active
    assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_MAX_SOC
    assert coordinator._sun_charge_power == 0
    assert all(
        call.kwargs["value"] == 0
        for call in coordinator.client.write_register.await_args_list
        if call.kwargs["address"] == REG_SUN_IC_POWER_SETPOINT_PCT
    )


@pytest.mark.parametrize("block", ["expired", "pv_surplus", "disabled"])
async def test_raised_target_respects_remaining_policy_blocks(
    price_hold: tuple[SaxPowerCoordinator, list[datetime]], block: str
) -> None:
    """Eine Zielerhöhung erteilt keine eigene Ladeberechtigung."""
    coordinator, clock = price_hold
    if block == "expired":
        clock[0] += timedelta(hours=3)
    elif block == "pv_surplus":
        coordinator.data["smartmeter_power"] = -1000
        for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES):
            coordinator._high_sample_revision += 1
            await coordinator._async_enforce_grid_charge(coordinator.data)
    else:
        await coordinator.async_set_price_charge_enabled(False)
    coordinator.client.write_register.reset_mock()
    await coordinator.async_set_max_soc(80)
    assert not coordinator.price_charge_active
    assert all(
        call.kwargs["value"] == 0
        for call in coordinator.client.write_register.await_args_list
        if call.kwargs["address"] == REG_SUN_IC_POWER_SETPOINT_PCT
    )


async def test_target_ack_under_held_lock_applies_latest_target(
    price_hold: tuple[SaxPowerCoordinator, list[datetime]],
) -> None:
    """REQ-VUE-ENTITY-BINDING: Software-ACK wartet nicht auf die alte Sperre."""
    coordinator, _ = price_hold
    async with coordinator._charge_control_lock:
        await asyncio.wait_for(
            coordinator.async_set_max_soc(80, defer_device_update=True), 0.2
        )
        assert coordinator.max_soc == 80
        assert coordinator.max_soc_clamped
        coordinator.client.write_register.assert_not_awaited()
        task = coordinator._month_control_task
        await asyncio.wait_for(
            coordinator.async_set_max_soc(90, defer_device_update=True), 0.2
        )
        assert coordinator._month_control_task is task
    await task
    assert coordinator.price_charge_active
    assert not coordinator.max_soc_clamped
    assert coordinator.effective_max_soc == 90


@pytest.mark.parametrize(
    "address", [REG_SUN_IC_CONTROL_MODE, REG_SUN_IC_POWER_SETPOINT_PCT]
)
@pytest.mark.parametrize("failed", [False, True])
async def test_target_ack_precedes_delayed_device_result(
    price_hold: tuple[SaxPowerCoordinator, list[datetime]], address: int, failed: bool
) -> None:
    """Verzögerte/fehlende Quittierungen bestätigen keinen Ladebeginn optimistisch."""
    coordinator, _ = price_hold
    entered = asyncio.Event()
    release = asyncio.Event()
    success = coordinator.client.write_register.return_value

    async def write(**kwargs: Any) -> Any:
        if kwargs["address"] == address:
            entered.set()
            await release.wait()
            if failed:
                raise ModbusException("delayed failure")
        return success

    coordinator.client.write_register.side_effect = write
    try:
        await asyncio.wait_for(
            coordinator.async_set_max_soc(80, defer_device_update=True), 0.2
        )
        task = coordinator._month_control_task
        await asyncio.wait_for(entered.wait(), 0.5)
        assert coordinator.max_soc == 80
        assert not coordinator.price_charge_active
        assert not task.done()
        release.set()
        await task
        assert coordinator.price_charge_active is not failed
        if failed:
            assert coordinator._grid_charge_power is None
            assert not coordinator.sun_charge_active
            coordinator.client.write_register.side_effect = None
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator.price_charge_active
    finally:
        release.set()
