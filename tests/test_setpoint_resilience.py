"""REQ-EXTENDED-MODE-RESILIENCE: safe holds and current control references."""

from __future__ import annotations

from datetime import datetime
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.const import (
    MIN_SETPOINT_POWER,
    PRICE_STATUS_PAUSED_NEUTRAL_BAND,
    PRICE_STATUS_WAITING,
    PRICE_STRATEGY_ABSOLUTE,
    PV_SURPLUS_HYSTERESIS_CYCLES,
    READ_BLOCK_COUNT,
    READ_BLOCK_START,
    REG_SOC,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator, to_unsigned16
from custom_components.sax_power.price_optimizer import PricePlan


@pytest.fixture
def coordinator(hass: HomeAssistant) -> SaxPowerCoordinator:
    client = MagicMock()
    client.connected = True
    result = MagicMock()
    result.isError.return_value = False
    client.write_register = AsyncMock(return_value=result)
    return SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="setpoint_resilience",
    )


@pytest.mark.parametrize("hold", ["max_soc", "neutral_price"])
async def test_zero_hold_survives_failed_sunspec_read(
    coordinator: SaxPowerCoordinator, hold: str
) -> None:
    """REQ-TIMED-SOC-CHARGE / REQ-DYNAMIC-PRICE-CHARGE: 0 W needs no read."""
    soc = 85 if hold == "max_soc" else 50

    async def read(*, address: int, count: int, device_id: int) -> MagicMock:
        if device_id != 64:
            raise ModbusException("SunSpec nicht erreichbar")
        result = MagicMock()
        result.isError.return_value = False
        result.registers = [0] * READ_BLOCK_COUNT
        result.registers[REG_SOC - READ_BLOCK_START] = soc
        return result

    coordinator.client.read_holding_registers = AsyncMock(side_effect=read)
    coordinator._max_soc = 80
    coordinator._ic_power_setpoint_sf_raw = 0x8000
    if hold == "neutral_price":
        coordinator._price_charge_enabled = True
        coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
        coordinator._price_charge_max_price = 0.20
        coordinator._price_charge_neutral_price = 0.40
        coordinator.price_planner.plan = PricePlan(
            status=PRICE_STATUS_WAITING, charge_now=False, current_price=0.30
        )

    try:
        with patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=datetime(2024, 1, 1, 12),
        ):
            await coordinator.async_refresh()
        assert coordinator.last_update_success is True
        assert coordinator.data["soc"] == soc
        assert coordinator.extended_available is False
        assert coordinator.sun_charge_active is True
        if hold == "max_soc":
            assert coordinator.max_soc_clamped is True
        else:
            assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_NEUTRAL_BAND
        coordinator.client.write_register.assert_any_await(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        )
        coordinator.client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=0,
            device_id=100,
        )
        coordinator.client.write_register.reset_mock()
        await coordinator._async_write_sun_charge_setpoint()
        coordinator.client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=0,
            device_id=100,
        )
    finally:
        await coordinator.async_shutdown(reset_device=False)


async def test_grid_serving_hold_needs_no_power_reference(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-GRID-SERVING-CHARGE: Schritt a requires power, not its reference."""
    coordinator._grid_serving_enabled = True
    coordinator._grid_serving_start = dt_time(10)
    coordinator._grid_serving_end = dt_time(18)
    coordinator._ic_power_setpoint_sf_raw = 0x8000
    data = {"soc": 50, "storage_power_active": -800, "smartmeter_power": -800}
    try:
        with patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=datetime(2024, 1, 1, 12),
        ):
            for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES):
                coordinator._high_sample_revision += 1
                await coordinator._async_enforce_grid_charge(data)
        assert coordinator._grid_serving_setpoint_active is True
        coordinator.client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=0,
            device_id=100,
        )
    finally:
        await coordinator.async_shutdown(reset_device=False)


@pytest.mark.parametrize("old_reference", [None, 4600])
async def test_manual_charge_uses_current_decision_reference(
    coordinator: SaxPowerCoordinator,
    old_reference: int | None,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: initial and later ticks use their own data."""
    if old_reference is not None:
        coordinator.data = {"soc": 50, "ic_max_power_reference": old_reference}
    coordinator._grid_charge_power = -1000
    coordinator._ic_power_setpoint_sf_raw = to_unsigned16(-2)
    try:
        await coordinator._async_enforce_grid_charge(
            {"soc": 50, "ic_max_power_reference": 2000}
        )
        coordinator.client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=to_unsigned16(-5000),
            device_id=100,
        )
    finally:
        await coordinator.async_shutdown(reset_device=False)


@pytest.mark.parametrize("reference", [None, 0])
async def test_negative_charge_rejects_current_invalid_reference(
    coordinator: SaxPowerCoordinator,
    reference: int | None,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: stale valid references cannot authorize writes."""
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}
    coordinator._grid_charge_power = MIN_SETPOINT_POWER
    with pytest.raises(HomeAssistantError, match="Referenzwert Maximalleistung"):
        await coordinator._async_enforce_grid_charge(
            {"soc": 50, "ic_max_power_reference": reference}
        )
    coordinator.client.write_register.assert_not_awaited()
    assert coordinator.sun_charge_active is False
