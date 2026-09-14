"""Real Modbus regressions for HIGH polling jitter (issue #246)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.const import READ_BLOCK_EXT_START
from custom_components.sax_power.coordinator import SaxPowerCoordinator

from .test_integration_live import (
    _build_basic_registers,
    _build_extended_registers,
    _modbus_server,
)

_CLOCK = "custom_components.sax_power.coordinator.monotonic"
_START = 100.0
_DELAYS = (0.04, 0.01, 0.05, 0.02)


@pytest.fixture
async def live_coordinator(
    hass: HomeAssistant, socket_enabled: None, unused_tcp_port: int
) -> AsyncIterator[SaxPowerCoordinator]:
    server = _modbus_server(
        unused_tcp_port, _build_basic_registers(), _build_extended_registers()
    )
    await server.serve_forever(background=True)
    client = AsyncModbusTcpClient("127.0.0.1", port=unused_tcp_port)
    coordinator = SaxPowerCoordinator(hass, client, 64, 100, 10, "high-jitter")
    coordinator._control_bootstrap_pending = True
    await coordinator.async_load_energy_state()
    try:
        yield coordinator
    finally:
        await coordinator.async_shutdown()
        client.close()
        await server.shutdown()


async def _tick(coordinator: SaxPowerCoordinator, time: float) -> dict[str, Any]:
    with patch(_CLOCK, return_value=time):
        return await coordinator._async_update_data()


async def _jittered_minute(coordinator: SaxPowerCoordinator) -> dict[str, Any]:
    # HA schedules a two-second cadence; Basic/LOW reads and the event loop
    # introduce different delays before the HIGH-block check on each tick.
    for tick in range(33):
        data = await _tick(coordinator, _START + 2 * tick + _DELAYS[tick % 4])
        if tick < 30:
            assert data["discharge_forecast"] is None
    return data


async def test_jittered_ha_ticks_read_each_due_high_sample(
    live_coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-HIGH-INTERVAL-REGISTERS: Small tick jitter must not halve polling."""
    data = await _jittered_minute(live_coordinator)
    assert data["storage_power_active"] == 1200
    assert data["smartmeter_power"] == 300
    assert live_coordinator._high_sample_revision == 33


async def test_jittered_high_samples_integrate_the_whole_measured_minute(
    live_coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-GRID-ENERGY: Real decoded samples account for the full elapsed time."""
    data = await _jittered_minute(live_coordinator)
    assert live_coordinator._grid_imported_kwh == pytest.approx(300 * 64 / 3600000)
    assert data["energy_exported_to_grid"] == 0


async def test_jittered_high_samples_build_a_discharge_forecast(
    live_coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-DISCHARGE-FORECAST: A minute of valid TCP samples builds history."""
    data = await _jittered_minute(live_coordinator)
    assert data["discharge_forecast"] is not None
    assert data["discharge_forecast_attributes"]["average_discharge_w"] == 1200
    assert data["discharge_forecast_attributes"][
        "observation_minutes"
    ] == pytest.approx(64 / 60)


async def test_four_second_gap_with_response_jitter_preserves_measurements(
    live_coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-GRID-ENERGY/REQ-DISCHARGE-FORECAST: RTT jitter is not an outage."""
    for tick in range(16):
        data = await _tick(live_coordinator, _START + tick * 4.05)
    assert live_coordinator._grid_imported_kwh == pytest.approx(300 * 60.75 / 3600000)
    assert data["discharge_forecast"] is not None
    assert data["discharge_forecast_attributes"][
        "observation_minutes"
    ] == pytest.approx(60.75 / 60)


@pytest.mark.parametrize("gap", [5.01, 30, 3600])
async def test_real_measurement_gap_resets_energy_baseline_and_forecast(
    live_coordinator: SaxPowerCoordinator, gap: float
) -> None:
    """REQ-GRID-ENERGY/REQ-DISCHARGE-FORECAST: Unobserved gaps stay uncounted."""
    for tick in range(31):
        data = await _tick(live_coordinator, _START + tick * 2)
    assert data["discharge_forecast"] is not None
    total = live_coordinator._grid_imported_kwh
    data = await _tick(live_coordinator, _START + 60 + gap)
    assert live_coordinator._grid_imported_kwh == total
    assert data["discharge_forecast"] is None
    assert data["discharge_forecast_attributes"] == {}
    await _tick(live_coordinator, _START + 62 + gap)
    assert live_coordinator._grid_imported_kwh == pytest.approx(
        total + 300 * 2 / 3600000
    )


async def test_cached_refresh_neither_counts_energy_nor_completes_a_minute(
    live_coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-GRID-ENERGY/REQ-DISCHARGE-FORECAST: Cache is not a new observation."""
    for tick in range(30):
        await _tick(live_coordinator, _START + tick * 2)
    total = live_coordinator._grid_imported_kwh
    revision = live_coordinator._high_sample_revision
    sample_time = live_coordinator._high_sample_time
    for refresh in (58.1, 58.2, 59, 59.5):
        data = await _tick(live_coordinator, _START + refresh)
        assert live_coordinator._grid_imported_kwh == total
        assert live_coordinator._high_sample_revision == revision
        assert live_coordinator._high_sample_time == sample_time
        assert data["discharge_forecast"] is None
    data = await _tick(live_coordinator, _START + 60)
    assert data["discharge_forecast"] is not None
    assert data["discharge_forecast_attributes"]["observation_minutes"] == 1


@pytest.mark.parametrize("age, fresh", [(4.05, True), (5.0, True), (5.01, False)])
async def test_cached_sample_freshness_tolerates_jitter_but_expires(
    live_coordinator: SaxPowerCoordinator, age: float, fresh: bool
) -> None:
    """REQ-GRID-ENERGY/REQ-DISCHARGE-FORECAST: Cache never renews sample age."""
    for tick in range(31):
        data = await _tick(live_coordinator, _START + tick * 2)
    forecast = data["discharge_forecast"]
    attributes = data["discharge_forecast_attributes"]
    total = live_coordinator._grid_imported_kwh
    sample_time = live_coordinator._high_sample_time
    with patch(_CLOCK, return_value=_START + 60 + age):
        live_coordinator._accumulate_grid_energy(data)
        live_coordinator._update_discharge_forecast(data)
    assert live_coordinator._grid_imported_kwh == total
    assert live_coordinator._high_sample_time == sample_time
    if fresh:
        assert data["discharge_forecast"] == forecast
        assert data["discharge_forecast_attributes"] == attributes
        assert live_coordinator._grid_energy_last_sample is not None
    else:
        assert data["discharge_forecast"] is None
        assert data["discharge_forecast_attributes"] == {}
        assert live_coordinator._grid_energy_last_sample is None


async def test_failed_read_cannot_be_used_as_a_fresh_sample(
    live_coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-GRID-ENERGY/REQ-DISCHARGE-FORECAST: Recovery never fills an outage."""
    for tick in range(31):
        await _tick(live_coordinator, _START + tick * 2)
    total = live_coordinator._grid_imported_kwh
    revision = live_coordinator._high_sample_revision
    read = live_coordinator.client.read_holding_registers

    async def failed_high_read(**kwargs: Any) -> Any:
        if kwargs["address"] == READ_BLOCK_EXT_START:
            raise ModbusException("simulated HIGH failure")
        return await read(**kwargs)

    with patch.object(
        live_coordinator.client, "read_holding_registers", side_effect=failed_high_read
    ):
        data = await _tick(live_coordinator, _START + 62)
    assert live_coordinator._high_sample_revision == revision
    assert live_coordinator._high_sample_time is None
    assert live_coordinator._grid_imported_kwh == total
    assert data["discharge_forecast"] is None
    data = await _tick(live_coordinator, _START + 64)
    assert live_coordinator._grid_imported_kwh == total
    assert data["discharge_forecast"] is None
    await _tick(live_coordinator, _START + 66)
    assert live_coordinator._grid_imported_kwh == pytest.approx(
        total + 300 * 2 / 3600000
    )
