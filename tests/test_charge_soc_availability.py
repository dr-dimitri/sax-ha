"""REQ-TIMED-SOC-CHARGE: lost Basic SOC cannot authorize network charging."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.const import (
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    PRICE_STRATEGY_ABSOLUTE,
    PRICE_UNIT_EUR_KWH,
    READ_BLOCK_COUNT,
    READ_BLOCK_START,
    REG_SOC,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

NOW = datetime(2026, 9, 5, 2, tzinfo=UTC)


@pytest.fixture
async def charge_system(
    hass: HomeAssistant,
) -> AsyncIterator[tuple[SaxPowerCoordinator, MagicMock]]:
    client = MagicMock()
    client.connected = True
    success = MagicMock()
    success.isError.return_value = False
    success.registers = [0] * READ_BLOCK_COUNT
    success.registers[REG_SOC - READ_BLOCK_START] = 39
    client.read_holding_registers = AsyncMock(return_value=success)
    client.write_register = AsyncMock(return_value=success)
    coordinator = SaxPowerCoordinator(
        hass, client, 64, 100, 10, "soc_availability_entry"
    )
    coordinator._max_soc = 80
    coordinator._timed_charge_max_soc = 70
    coordinator._timed_charge_min_soc = 40
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(5)
    coordinator._async_read_extended = AsyncMock(
        return_value={
            "smartmeter_power": 0,
            "storage_power_active": 0,
            "ic_max_power_reference": 4600,
            "ic_timeout": 300,
            "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        }
    )
    with (
        patch("custom_components.sax_power.coordinator.dt_util.now", return_value=NOW),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow", return_value=NOW
        ),
        patch("custom_components.sax_power.coordinator.monotonic", return_value=1000),
    ):
        try:
            await coordinator.async_refresh()
            assert coordinator.last_update_success
            yield coordinator, client
        finally:
            await coordinator.async_shutdown()


async def _fail_basic_read(coordinator: SaxPowerCoordinator, client: MagicMock) -> None:
    coordinator._basic_last_read = None
    client.read_holding_registers.side_effect = ModbusException(
        "Basic nicht erreichbar"
    )
    await coordinator.async_refresh()
    assert not coordinator.last_update_success


@pytest.mark.parametrize("mode", ["timed", "price", "manual"])
@pytest.mark.parametrize("recovered_soc", [39, 90])
async def test_outage_stops_charge_and_timer_cannot_reuse_soc(
    hass: HomeAssistant,
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
    mode: str,
    recovered_soc: int,
) -> None:
    """Issue #167: retry only after a real read, using its SOC and limits."""
    coordinator, client = charge_system
    if mode == "timed":
        await coordinator.async_set_timed_charge_enabled(True)
    elif mode == "manual":
        await coordinator.async_start_grid_charge(-1200)
    else:
        coordinator.options = {
            CONF_PRICE_SENSOR: "sensor.test_price",
            CONF_PRICE_UNIT: PRICE_UNIT_EUR_KWH,
        }
        hass.states.async_set(
            "sensor.test_price",
            "0.10",
            {
                "raw_today": [
                    {"start": NOW, "end": NOW + timedelta(hours=1), "value": 0.10}
                ]
            },
        )
        coordinator._price_charge_max_price = 0.20
        coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
        await coordinator.async_set_price_charge_enabled(True)
    coordinator.price_planner.async_setup()
    assert coordinator.sun_charge_active and coordinator._sun_charge_power < 0

    client.write_register.reset_mock()
    await _fail_basic_read(coordinator, client)

    assert not coordinator.sun_charge_active
    assert not coordinator._timed_charge_active
    assert not coordinator.price_charge_active
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )
    exception = coordinator.last_exception
    client.write_register.reset_mock()
    await coordinator.price_planner._async_interval_evaluate(NOW)
    await coordinator.async_set_max_soc(85)

    assert not coordinator.sun_charge_active
    assert not coordinator.last_update_success
    assert coordinator.last_exception is exception
    client.write_register.assert_not_awaited()
    with pytest.raises(HomeAssistantError, match="aktuellem SOC"):
        await coordinator.async_start_grid_charge(-1500)
    with pytest.raises(HomeAssistantError, match="ohne gültigen Basic-Mode-SOC"):
        await coordinator._async_write_sun_charge_setpoint(-1200)
    client.write_register.assert_not_awaited()

    client.read_holding_registers.side_effect = None
    client.read_holding_registers.return_value.registers[REG_SOC - READ_BLOCK_START] = (
        recovered_soc
    )
    await coordinator.async_refresh()

    assert coordinator.last_update_success
    assert coordinator.data["soc"] == recovered_soc
    assert coordinator.sun_charge_active
    assert (coordinator._sun_charge_power < 0) is (recovered_soc < 85)
    if recovered_soc >= 85:
        assert coordinator.max_soc_clamped
        assert all(
            write.kwargs["value"] == 0
            for write in client.write_register.await_args_list
            if write.kwargs["address"] == REG_SUN_IC_POWER_SETPOINT_PCT
        )


async def test_basic_cache_remains_valid_until_a_real_read_fails(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """A high-frequency tick must not reject the normal Basic poll cache."""
    coordinator, client = charge_system
    client.read_holding_registers.side_effect = ModbusException("noch nicht abfragen")
    with patch("custom_components.sax_power.coordinator.monotonic", return_value=1002):
        await coordinator.async_refresh()
        await coordinator.async_start_grid_charge(-1200)

    assert coordinator.last_update_success
    assert coordinator.sun_charge_active
    assert coordinator._sun_charge_power == -1200
    client.read_holding_registers.assert_awaited_once()


async def test_writer_rejects_stale_soc_while_outage_cleanup_waits_for_lock(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """The failure latch must be set before waiting for another controller."""
    coordinator, client = charge_system
    coordinator._basic_last_read = None
    client.read_holding_registers.side_effect = ModbusException("offline")
    client.write_register.reset_mock()
    async with coordinator._charge_control_lock:
        refresh = asyncio.create_task(coordinator._async_update_data())
        await asyncio.sleep(0)
        with pytest.raises(HomeAssistantError, match="ohne gültigen Basic-Mode-SOC"):
            await coordinator._async_write_sun_charge_setpoint(-1200)
        client.write_register.assert_not_awaited()
    with pytest.raises(UpdateFailed):
        await refresh


async def test_failed_outage_reset_cancels_writer_and_retries_without_charging(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """A failed mode-zero write cannot keep renewing the preceding charge."""
    coordinator, client = charge_system
    await coordinator.async_start_grid_charge(-1200)
    client.write_register.side_effect = ModbusException("Reset nicht quittiert")

    await _fail_basic_read(coordinator, client)

    assert not coordinator.sun_charge_active
    assert coordinator._sun_charge_reset_required
    assert coordinator.data["timed_charge_discharge_status"] is None
    client.write_register.side_effect = None
    client.write_register.reset_mock()
    await coordinator.price_planner._async_interval_evaluate(NOW)

    assert not coordinator.sun_charge_active
    assert not coordinator._sun_charge_reset_required
    assert not coordinator.last_update_success
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )
