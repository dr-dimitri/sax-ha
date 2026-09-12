"""REQ-HEMS-ACCEPTANCE: normalized providers through both tariffs to real TCP."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymodbus.client import AsyncModbusTcpClient

from custom_components.sax_power.coordinator import SaxPowerCoordinator, to_signed16
from custom_components.sax_power.domain.hems import EnergySlot, LoadForecast
from custom_components.sax_power.domain.hems_pv import (
    normalize_pv_forecast,
    normalize_solcast_forecast,
)

from .test_hems_pv import NOW, forecast, solcast
from .test_integration_live import (
    _build_basic_registers,
    _build_extended_registers,
    _modbus_server,
)


@contextmanager
def _simulation_clock() -> Iterator[Callable[[datetime], None]]:
    """HA's UTC scheduler and decision clock share time; TCP keeps real monotonic."""
    with (
        patch("homeassistant.util.dt.utcnow", return_value=NOW) as utc_clock,
        patch("homeassistant.util.dt.now", return_value=NOW) as local_clock,
        patch("time.time", return_value=NOW.timestamp()) as wall_clock,
        patch(
            "homeassistant.helpers.event.time_tracker_timestamp",
            return_value=NOW.timestamp(),
        ) as tracker_clock,
    ):

        def step(instant: datetime) -> None:
            utc_clock.return_value = local_clock.return_value = instant
            wall_clock.return_value = tracker_clock.return_value = instant.timestamp()

        yield step


@pytest.mark.parametrize("mode", ["timed", "dynamic"])
@pytest.mark.parametrize("provider", ["pv_forecast", "solcast_solar"])
@pytest.mark.parametrize("wait_for_pv", [False, True])
async def test_night_decision_reaches_local_modbus_and_stops_at_limit(
    hass, socket_enabled, unused_tcp_port, mode, provider, wait_for_pv
) -> None:
    """Empty SAX either bridges after cheap window or waits for PV inside it."""
    await hass.config.async_set_time_zone("UTC")
    basic_registers = _build_basic_registers()
    basic_registers[46] = 0
    server = _modbus_server(
        unused_tcp_port, basic_registers, _build_extended_registers()
    )
    await server.serve_forever(background=True)
    client = AsyncModbusTcpClient("127.0.0.1", port=unused_tcp_port)
    assert await client.connect()
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="hems_tcp",
    )
    end = NOW + timedelta(hours=5)
    powers = (0.0,) * 8 + (2.0, 2.0)
    if provider == "pv_forecast":
        pv = normalize_pv_forecast(
            forecast(powers), as_of=NOW, end=end, source_id="same-plant"
        )
    else:
        pv = normalize_solcast_forecast(
            solcast(powers), as_of=NOW, end=end, source_id="same-plant", fetched_at=NOW
        )
    load = LoadForecast(
        intervals=(
            EnergySlot(NOW, NOW + timedelta(hours=4), 2),
            EnergySlot(NOW + timedelta(hours=4), end, 0.5),
        ),
        generated_at=NOW,
        evaluated_through=NOW,
        model_start=NOW - timedelta(hours=8),
        model_end=end,
        nights_count=3,
        observed_hours=6,
    )
    cheap_end = NOW + timedelta(hours=4.25 if wait_for_pv else 1)
    adapter = MagicMock()
    adapter.async_read = AsyncMock(return_value=pv)
    current_time = NOW
    try:
        with (
            _simulation_clock() as step_clock,
            patch.object(
                coordinator.hems.history, "async_refresh", AsyncMock(return_value=load)
            ) as history_read,
            patch(
                "custom_components.sax_power.application.hems_runtime.HemsPvAdapter",
                return_value=adapter,
            ),
        ):
            coordinator.data = await coordinator._async_update_data()
            coordinator._max_soc = 90
            coordinator._timed_charge_max_soc = 80
            coordinator._timed_charge_min_soc = 10
            coordinator.options = {
                "hems_pv_provider": provider,
                "hems_pv_entry": "plant",
                "hems_charge_efficiency": 1,
                "hems_discharge_efficiency": 1,
                "price_sensor": "sensor.hems_price",
            }
            if mode == "timed":
                coordinator._timed_charge_enabled = True
                coordinator._timed_charge_mode = "adaptive"
                coordinator._timed_charge_start = dt_time(4)
                coordinator._timed_charge_end = cheap_end.time()
            else:
                coordinator._price_charge_enabled = True
                coordinator._price_charge_strategy = "adaptive"
                coordinator._price_charge_max_price = 0.2
                coordinator._price_charge_hours = 4
                # Same hold policy as the timed tariff's confirmed charging hold.
                coordinator._price_charge_neutral_price = 0.4
                hass.states.async_set(
                    "sensor.hems_price",
                    ".1",
                    {
                        "unit_of_measurement": "EUR/kWh",
                        "raw_today": [
                            {
                                "start": NOW.isoformat(),
                                "end": cheap_end.isoformat(),
                                "value": 0.1,
                            },
                            {
                                "start": cheap_end.isoformat(),
                                "end": end.isoformat(),
                                "value": 0.5,
                            },
                        ],
                    },
                )
            coordinator.hems._started = True
            coordinator.hems.configuration_changed()
            await hass.async_block_till_done()
            assert history_read.await_count == 1
            plan = coordinator.hems.plan
            assert plan is not None
            assert plan.pv_supply_at == NOW + timedelta(hours=4)
            assert coordinator.hems.next_evaluation_at == NOW + timedelta(minutes=5)
            if not wait_for_pv and plan.next_start and plan.next_start > NOW:
                current_time = plan.next_start
                step_clock(current_time)
                # Advance the scenario with a real fresh SOC read, then one
                # resumed backend tick; missed ticks are never replayed in bulk.
                coordinator._basic_data = {}
                coordinator.data.update(await coordinator._async_read_basic())
                history_read.return_value = replace(
                    load, evaluated_through=current_time
                )
                coordinator.hems._tick(current_time)
                await hass.async_block_till_done()
                assert history_read.await_count == 2
                assert coordinator.hems.next_evaluation_at == (
                    current_time + timedelta(minutes=5)
                )
                plan = coordinator.hems.plan
            response = await client.read_holding_registers(49, count=3, device_id=100)
            assert not response.isError()
            if wait_for_pv:
                assert plan.planned_grid_kwh == 0
                assert plan.reason_codes == ("waiting_for_pv_in_cheap_window",)
                assert response.registers[2] == (1 if mode == "dynamic" else 0)
                if mode == "dynamic":
                    assert response.registers[0] == 0
                assert not coordinator._timed_charge_active
                assert not coordinator._price_charge_active
            else:
                assert plan.planned_grid_kwh > 0
                assert plan.target_soc < 80
                assert coordinator.hems.execution(
                    current_time, coordinator.data
                ).charge, (
                    current_time,
                    plan.intervals,
                    plan.valid_until,
                    coordinator.hems.attributes,
                    coordinator._basic_read_failed,
                )
                assert response.registers[2] == 1
                assert to_signed16(response.registers[0]) < 0
                assert coordinator.hems.attributes["execution_charging"] is True
                # A measured full request ends in the fast control path,
                # without waiting for the next five-minute evaluation.
                coordinator.hems._delivered_kwh = plan.planned_grid_kwh
                next_check_before_stop = coordinator.hems.next_evaluation_at
                await coordinator._async_enforce_grid_charge(coordinator.data)
                response = await client.read_holding_registers(
                    49, count=3, device_id=100
                )
                assert (
                    response.registers[2] == 0
                    or to_signed16(response.registers[0]) == 0
                )
                assert not coordinator._timed_charge_active
                assert not coordinator._price_charge_active
                assert coordinator.hems.next_evaluation_at == next_check_before_stop
            assert coordinator.timed_charge_enabled is (mode == "timed")
    finally:
        await coordinator.async_shutdown()
        client.close()
        await server.shutdown()


def test_identical_provider_physics_produces_identical_energy_decision() -> None:
    """Provider freshness policies differ, but the same valid energy does not."""
    from custom_components.sax_power.domain.hems_planner import compute_energy_plan

    from .test_hems_planner import snapshot

    powers = (0.0,) * 8 + (2.0, 2.0)
    end = NOW + timedelta(hours=5)
    pv = normalize_pv_forecast(
        forecast(powers), as_of=NOW, end=end, source_id="same-plant"
    )
    other = normalize_solcast_forecast(
        solcast(powers), as_of=NOW, end=end, source_id="same-plant", fetched_at=NOW
    )
    # The reference fixture has its own fixed date; shift its full input clock.
    base = snapshot()
    delta = NOW - base.as_of
    shifted = replace(
        base,
        as_of=NOW,
        soc_measured_at=NOW,
        load=replace(
            base.load,
            model_start=NOW,
            model_end=end,
            evaluated_through=NOW,
            intervals=tuple(
                replace(i, start=i.start + delta, end=i.end + delta)
                for i in base.load.intervals
            ),
        ),
        tariff=replace(
            base.tariff,
            charge_windows=tuple(
                replace(w, start=w.start + delta, end=w.end + delta)
                for w in base.tariff.charge_windows
            ),
            cheap_windows=tuple(
                replace(w, start=w.start + delta, end=w.end + delta)
                for w in base.tariff.cheap_windows
            ),
            discharge_blocked_windows=tuple(
                replace(w, start=w.start + delta, end=w.end + delta)
                for w in base.tariff.discharge_blocked_windows
            ),
        ),
    )
    first = compute_energy_plan(replace(shifted, pv=pv))
    second = compute_energy_plan(replace(shifted, pv=other))
    assert first.required_grid_kwh == pytest.approx(2)
    assert first.required_grid_kwh == second.required_grid_kwh
    assert first.target_soc == second.target_soc
    assert first.intervals == second.intervals
