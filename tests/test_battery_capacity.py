"""Device-reported capacity in price planning and discharge forecasts."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.sax_power.const import (
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    PRICE_STRATEGY_SMART,
    REG_SOC,
    REG_SUN_BATTERY_CAPACITY,
    REG_SUN_BATTERY_CAPACITY_SF,
    REG_SUN_BATTERY_SOC,
    REG_SUN_BATTERY_SOC_MIN,
    REG_SUN_IC_MAX_POWER_REFERENCE,
    REG_SUN_STORAGE_POWER_ACTIVE,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator, to_unsigned16
from custom_components.sax_power.price_optimizer import PriceSlot, compute_plan

_NOW = datetime(2026, 9, 13, 12, tzinfo=UTC)
_CLOCK = "custom_components.sax_power.coordinator.monotonic"


@pytest.fixture(
    params=[
        (5000, 0, 5000),
        (750, 1, 7500),
        (1000, 1, 10000),
        (50000, -1, 5000),
    ],
    ids=["5kWh-sf0", "7.5kWh-sf1", "10kWh-sf1", "5kWh-sf-negative"],
)
async def capacity_coordinator(
    hass: HomeAssistant, request: pytest.FixtureRequest
) -> AsyncIterator[tuple[SaxPowerCoordinator, int]]:
    raw_capacity, scale_factor, capacity_wh = request.param
    basic = [0] * 100
    basic[REG_SOC] = 40
    extended = [0] * 115
    extended[REG_SUN_BATTERY_CAPACITY] = raw_capacity
    extended[REG_SUN_BATTERY_CAPACITY_SF] = to_unsigned16(scale_factor)
    extended[REG_SUN_BATTERY_SOC] = 40
    extended[REG_SUN_BATTERY_SOC_MIN] = 10
    extended[REG_SUN_IC_MAX_POWER_REFERENCE] = 1000
    extended[REG_SUN_STORAGE_POWER_ACTIVE] = 1000

    def read(*, address: int, count: int, device_id: int) -> MagicMock:
        result = MagicMock()
        result.isError.return_value = False
        registers = basic if device_id == 64 else extended
        result.registers = registers[address : address + count]
        return result

    client = MagicMock()
    client.connected = True
    client.read_holding_registers = AsyncMock(side_effect=read)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        64,
        100,
        10,
        "capacity-test",
        options={
            CONF_PV_FORECAST_SENSOR: "sensor.pv_forecast",
            CONF_PV_FORECAST_FACTOR: 100,
        },
    )
    coordinator._control_bootstrap_pending = True
    coordinator._max_soc = 80
    coordinator._price_charge_enabled = True
    coordinator._price_charge_strategy = PRICE_STRATEGY_SMART
    coordinator._price_charge_hours = 8
    yield coordinator, capacity_wh
    await coordinator.async_shutdown()


async def test_smart_plan_uses_scaled_device_capacity(
    hass: HomeAssistant,
    capacity_coordinator: tuple[SaxPowerCoordinator, int],
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: Wh and sunssf reach the actual energy budget."""
    coordinator, capacity_wh = capacity_coordinator
    hass.states.async_set("sensor.pv_forecast", "1", {"unit_of_measurement": "kWh"})
    with (
        patch(_CLOCK, return_value=0),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow", return_value=_NOW
        ),
    ):
        coordinator.data = await coordinator._async_update_data()

    assert coordinator.data["battery_capacity"] == capacity_wh
    context = coordinator.price_planner._context()
    assert context.capacity_kwh == capacity_wh / 1000
    slots = [
        PriceSlot(
            start=_NOW + timedelta(hours=hour),
            end=_NOW + timedelta(hours=hour + 1),
            price=0.1 + hour / 100,
        )
        for hour in range(8)
    ]
    plan = compute_plan(_NOW, slots, context)

    expected_hours = capacity_wh / 1000 * 0.4 - 1
    assert plan.needed_hours == pytest.approx(expected_hours)
    assert plan.pv_forecast_kwh == 1
    assert sum(
        (slot.end - slot.start for slot in plan.slots), timedelta()
    ) == timedelta(hours=expected_hours)
    coordinator.client.write_register.assert_not_called()


async def test_discharge_forecast_uses_scaled_device_capacity(
    capacity_coordinator: tuple[SaxPowerCoordinator, int],
) -> None:
    """REQ-DISCHARGE-FORECAST: each capacity determines its usable SOC energy."""
    coordinator, capacity_wh = capacity_coordinator
    for seconds in range(0, 61, 2):
        with (
            patch(_CLOCK, return_value=seconds),
            patch(
                "custom_components.sax_power.coordinator.dt_util.utcnow",
                return_value=_NOW + timedelta(seconds=seconds),
            ),
        ):
            coordinator.data = await coordinator._async_update_data()

    assert coordinator.data["battery_capacity"] == capacity_wh
    expected_hours = capacity_wh / 1000 * 0.3
    assert coordinator.data["discharge_forecast"] == _NOW + timedelta(
        seconds=60, hours=expected_hours
    )
    assert coordinator.data["discharge_forecast_attributes"] == {
        "average_discharge_w": 1000,
        "observation_minutes": 1,
        "observed_at": (_NOW + timedelta(seconds=60)).isoformat(),
    }
    coordinator.client.write_register.assert_not_called()
