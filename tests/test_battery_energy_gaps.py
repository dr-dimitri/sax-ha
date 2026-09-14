"""REQ-ENERGY-DASHBOARD/REQ-ECONOMICS-ACCOUNTING: TCP gaps stay unbilled."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    READ_BLOCK_EXT_START,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

from .test_integration_live import (
    _build_basic_registers,
    _build_extended_registers,
    _modbus_server,
)

_EPOCH = datetime(2026, 9, 14, 12, tzinfo=UTC)
_TOTALS = (
    "_energy_charged_kwh",
    "_energy_discharged_kwh",
    "_energy_grid_charged_kwh",
    "_energy_pv_charged_kwh",
    "_economics_grid_charge_cost_eur",
    "_economics_pv_opportunity_cost_eur",
    "_economics_avoided_grid_cost_eur",
    "_economics_unvalued_inventory_kwh",
    "_economics_unpriced_charge_kwh",
    "_economics_unpriced_discharge_kwh",
    "_economics_current_day_observed_seconds",
)


@pytest.fixture(params=[1200, -1200], ids=["discharge", "mixed_charge"])
async def battery(
    hass: HomeAssistant,
    socket_enabled: None,
    unused_tcp_port: int,
    request: pytest.FixtureRequest,
) -> AsyncIterator[SaxPowerCoordinator]:
    registers = _build_extended_registers()
    registers[29] = request.param
    server = _modbus_server(unused_tcp_port, _build_basic_registers(), registers)
    await server.serve_forever(background=True)
    client = AsyncModbusTcpClient("127.0.0.1", port=unused_tcp_port)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        64,
        100,
        10,
        "battery-gaps",
        options={
            CONF_ECONOMICS_TARIFF_TYPE: "fixed",
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.30,
        },
    )
    coordinator._control_bootstrap_pending = True
    await coordinator.async_load_energy_state()
    coordinator.restore_energy_charged(0.0)
    coordinator.restore_energy_discharged(0.0)
    await coordinator.async_load_economics_state()
    try:
        yield coordinator
    finally:
        await coordinator.async_shutdown(reset_device=False)
        client.close()
        await server.shutdown()


async def _tick(coordinator: SaxPowerCoordinator, at: float) -> dict[str, Any]:
    moment = _EPOCH + timedelta(seconds=at)
    with (
        patch("custom_components.sax_power.coordinator.monotonic", return_value=at),
        patch(
            "custom_components.sax_power.coordinator.dt_util.now", return_value=moment
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=moment,
        ),
    ):
        return await coordinator._async_update_data()


def _totals(coordinator: SaxPowerCoordinator) -> tuple[float, ...]:
    return tuple(getattr(coordinator, key) for key in _TOTALS)


@pytest.mark.parametrize("gap", [5.01, 30, 3600])
async def test_successful_read_after_pause_sets_baseline_without_billing_gap(
    battery: SaxPowerCoordinator, gap: float
) -> None:
    await _tick(battery, 100)
    await _tick(battery, 102)
    before = _totals(battery)
    await _tick(battery, 102 + gap)
    assert _totals(battery) == before
    await _tick(battery, 104 + gap)
    assert _totals(battery) == pytest.approx(tuple(value * 2 for value in before))


@pytest.mark.parametrize("recovery_after", [2, 30])
async def test_missing_high_read_does_not_bill_until_two_valid_samples(
    battery: SaxPowerCoordinator, recovery_after: float
) -> None:
    await _tick(battery, 100)
    await _tick(battery, 102)
    before = _totals(battery)
    read = battery.client.read_holding_registers

    async def failed_high_read(**kwargs: Any) -> Any:
        if kwargs["address"] == READ_BLOCK_EXT_START:
            raise ModbusException("simulated HIGH failure")
        return await read(**kwargs)

    with patch.object(
        battery.client, "read_holding_registers", side_effect=failed_high_read
    ):
        await _tick(battery, 104)
    assert _totals(battery) == before
    await _tick(battery, 104 + recovery_after)
    assert _totals(battery) == before
    await _tick(battery, 106 + recovery_after)
    assert _totals(battery) == pytest.approx(tuple(value * 2 for value in before))


async def test_cached_refresh_does_not_bill_or_move_battery_sample_baseline(
    battery: SaxPowerCoordinator,
) -> None:
    await _tick(battery, 100)
    await _tick(battery, 102)
    before = _totals(battery)
    for at in (102.1, 102.2, 103, 103.5):
        data = await _tick(battery, at)
        assert _totals(battery) == before
        assert data["economics_current_import_price"] == 0.3
    await _tick(battery, 104)
    assert _totals(battery) == pytest.approx(tuple(value * 2 for value in before))


@pytest.mark.parametrize("age", [5.0, 5.01])
async def test_cached_sample_age_cannot_extend_the_measurement_baseline(
    battery: SaxPowerCoordinator, age: float
) -> None:
    await _tick(battery, 100)
    data = await _tick(battery, 102)
    before = _totals(battery)
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=102 + age
    ):
        battery._accumulate_energy(data)
    assert _totals(battery) == before
    assert battery._energy_last_ts == (102 if age == 5 else None)
    await _tick(battery, 110)
    assert _totals(battery) == before
    await _tick(battery, 112)
    assert _totals(battery) == pytest.approx(tuple(value * 2 for value in before))


async def test_tariff_change_between_cached_refreshes_keeps_both_prices(
    battery: SaxPowerCoordinator,
) -> None:
    await _tick(battery, 100)
    data = await _tick(battery, 102)
    cost_before = battery._economics_grid_charge_cost_eur
    savings_before = battery._economics_avoided_grid_cost_eur
    await _tick(battery, 102.5)
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=_EPOCH + timedelta(seconds=103),
    ):
        battery.options = {
            **battery.options,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.5,
        }
        battery.tariff_provider.async_setup()
    cached = await _tick(battery, 103)
    assert cached["economics_current_import_price"] == 0.5
    await _tick(battery, 103.5)
    await _tick(battery, 104)
    if data["storage_power_active"] > 0:
        assert (
            battery._economics_avoided_grid_cost_eur - savings_before
            == pytest.approx(1.2 * (0.3 + 0.5) / 3600)
        )
    else:
        assert battery._economics_grid_charge_cost_eur - cost_before == pytest.approx(
            0.3 * (0.3 + 0.5) / 3600
        )
    assert battery._economics_unpriced_charge_kwh == 0
    assert battery._economics_unpriced_discharge_kwh == 0
    assert battery._economics_current_day_observed_seconds == 4


@pytest.mark.parametrize("step", [2, 4.05, 5])
async def test_valid_sample_jitter_keeps_battery_energy_origin_and_costs(
    battery: SaxPowerCoordinator, step: float
) -> None:
    for tick in range(16):
        data = await _tick(battery, 100 + step * tick)
    hours = 15 * step / 3600
    assert battery._economics_current_day_observed_seconds == pytest.approx(15 * step)
    if data["storage_power_active"] > 0:
        assert battery._energy_discharged_kwh == pytest.approx(1.2 * hours)
        assert battery._economics_avoided_grid_cost_eur == pytest.approx(
            1.2 * hours * 0.3
        )
    else:
        assert battery._energy_charged_kwh == pytest.approx(1.2 * hours)
        assert battery._energy_grid_charged_kwh == pytest.approx(0.3 * hours)
        assert battery._energy_pv_charged_kwh == pytest.approx(0.9 * hours)
        assert battery._economics_grid_charge_cost_eur == pytest.approx(
            0.3 * hours * 0.3
        )
        assert battery._economics_pv_opportunity_cost_eur == pytest.approx(
            0.9 * hours * 0.08
        )
