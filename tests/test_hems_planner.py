"""Analytical and adversarial scenarios for REQ-HEMS-ENERGY-PLANNER."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.sax_power.domain.hems import (
    EnergySlot,
    LoadForecast,
    PlanningSnapshot,
    PlanStatus,
    PvForecast,
    TariffConstraints,
    TariffWindow,
)
from custom_components.sax_power.domain.hems_planner import compute_energy_plan

NOW = datetime(2026, 9, 13, tzinfo=UTC)


def moment(hours: float) -> datetime:
    return NOW + timedelta(hours=hours)


def slot(start: float, end: float, energy: float) -> EnergySlot:
    return EnergySlot(moment(start), moment(end), energy)


def window(start: float, end: float, price: float | None = None) -> TariffWindow:
    return TariffWindow(moment(start), moment(end), price)


def snapshot(**changes: object) -> PlanningSnapshot:
    """Three kWh after delivery, with an unconsumed cheap charging window."""
    charging = window(0, 1)
    base = PlanningSnapshot(
        as_of=NOW,
        revision="r1",
        load=LoadForecast(
            intervals=(slot(0, 1, 0), slot(1, 4, 3), slot(4, 5, 1)),
            generated_at=NOW,
            evaluated_through=NOW,
            model_start=NOW,
            model_end=moment(5),
            nights_count=3,
            observed_hours=6,
        ),
        pv=PvForecast(
            intervals=(slot(0, 4, 0), slot(4, 5, 2)),
            generated_at=NOW,
            fetched_at=NOW,
            valid_until=moment(1),
        ),
        tariff=TariffConstraints((charging,), (charging,), (charging,)),
        current_soc=20,
        soc_measured_at=NOW,
        capacity_kwh=10,
        charge_power_w=4000,
        reserve_soc=10,
        max_soc=90,
        eta_charge=1,
        eta_discharge=1,
    )
    return replace(base, **changes)


@pytest.mark.parametrize(
    ("soc", "load", "expected_grid", "expected_target"),
    [(20, 3, 2, 40), (50, 3, 0, 50), (0, 1.5, 2.5, 25), (10, 3, 3, 40)],
)
def test_analytical_reserve_examples(soc, load, expected_grid, expected_target):
    """Reserve is included once, also below reserve and at exact equality."""
    state = snapshot(current_soc=soc)
    state = replace(
        state,
        load=replace(
            state.load, intervals=(slot(0, 1, 0), slot(1, 4, load), slot(4, 5, 1))
        ),
    )
    plan = compute_energy_plan(state)
    assert plan.planned_grid_kwh == pytest.approx(expected_grid, abs=1e-7)
    assert plan.required_grid_kwh == pytest.approx(expected_grid, abs=1e-7)
    assert plan.target_soc == pytest.approx(expected_target, abs=1e-6)
    assert plan.unmet_grid_kwh == 0
    assert plan.pv_supply_at == moment(4)
    assert max(point.stored_kwh for point in plan.trajectory) <= 9


def test_separate_charge_and_discharge_losses():
    plan = compute_energy_plan(snapshot(eta_charge=0.95, eta_discharge=0.95))
    assert plan.planned_grid_kwh == pytest.approx(2.271468144, abs=1e-6)
    assert plan.target_soc == pytest.approx(41.578947368, abs=1e-6)
    assert plan.trajectory[-1].stored_kwh == pytest.approx(1, abs=1e-7)


@pytest.mark.parametrize("soc", [0, 10])
def test_pv_waits_with_supply_start_inside_cheap_window(soc):
    state = snapshot(current_soc=soc)
    state = replace(
        state, tariff=replace(state.tariff, cheap_windows=(window(0, 4.25),))
    )
    plan = compute_energy_plan(state)
    assert plan.status == PlanStatus.NO_NEED
    assert plan.reason_codes == ("waiting_for_pv_in_cheap_window",)
    assert plan.planned_grid_kwh == 0
    assert not plan.intervals


def test_pv_start_at_window_end_does_not_qualify_for_waiting():
    state = snapshot(current_soc=0)
    state = replace(state, tariff=replace(state.tariff, cheap_windows=(window(0, 4),)))
    plan = compute_energy_plan(state)
    assert plan.reason_codes != ("waiting_for_pv_in_cheap_window",)
    assert plan.planned_grid_kwh > 0


def test_budget_anchor_does_not_cut_physical_cheap_window():
    state = snapshot(current_soc=0)
    state = replace(
        state,
        tariff=TariffConstraints(
            (window(0, 1),), (window(0, 4.25),), max_charge_seconds=0
        ),
    )
    assert compute_energy_plan(state).reason_codes == (
        "waiting_for_pv_in_cheap_window",
    )


def test_single_solar_spike_does_not_qualify():
    state = snapshot()
    state = replace(
        state,
        pv=replace(
            state.pv,
            intervals=(slot(0, 2, 0), slot(2, 2.5, 2), slot(2.5, 4, 0), slot(4, 5, 2)),
        ),
    )
    plan = compute_energy_plan(state)
    assert plan.pv_supply_at == moment(4)
    assert plan.status in (PlanStatus.PLANNED, PlanStatus.NO_NEED)


def test_missing_trailing_forecast_does_not_reject_proven_supply():
    state = snapshot()
    state = replace(state, load=replace(state.load, model_end=moment(10)))
    assert compute_energy_plan(state).pv_supply_at == moment(4)


def test_hole_before_supply_is_not_zero():
    state = snapshot()
    state = replace(
        state,
        pv=replace(state.pv, intervals=(slot(0, 1, 0), slot(2, 4, 0), slot(4, 5, 2))),
    )
    plan = compute_energy_plan(state)
    assert plan.status == PlanStatus.FALLBACK
    assert plan.reason_codes == ("pv_coverage_missing",)
    assert plan.planned_grid_kwh is None


def test_hole_in_confirmation_window_invalidates_supply():
    state = snapshot()
    state = replace(
        state,
        pv=replace(
            state.pv, intervals=(slot(0, 4, 0), slot(4, 4.5, 1), slot(4.75, 5, 1))
        ),
    )
    assert compute_energy_plan(state).status == PlanStatus.FALLBACK


def test_confirmation_must_end_inside_model_scope():
    state = snapshot()
    state = replace(state, load=replace(state.load, model_end=moment(4.75)))
    assert compute_energy_plan(state).reason_codes == ("pv_supply_unconfirmed",)


def test_valid_zero_pv_is_insufficient_supply_not_zero_need():
    state = snapshot()
    state = replace(state, pv=replace(state.pv, intervals=(slot(0, 5, 0),)))
    assert compute_energy_plan(state).reason_codes == ("pv_supply_unconfirmed",)


def test_outside_model_scope_is_inactive_even_when_data_failed():
    state = snapshot()
    state = replace(
        state, load=replace(state.load, model_end=NOW, quality_reason="history_missing")
    )
    plan = compute_energy_plan(state)
    assert plan.status == PlanStatus.INACTIVE
    assert plan.reason_codes == ("outside_model_scope",)


def test_explicit_daytime_result_without_geometry_is_inactive():
    state = snapshot()
    plan = compute_energy_plan(
        replace(
            state,
            load=LoadForecast(quality_reason="outside_model_scope"),
        )
    )
    assert plan.status is PlanStatus.INACTIVE
    assert plan.reason_codes == ("outside_model_scope",)


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"current_soc": None}, "soc_unavailable"),
        ({"current_soc": float("nan")}, "soc_unavailable"),
        ({"current_soc": True}, "soc_unavailable"),
        ({"current_soc": -1}, "soc_unavailable"),
        ({"current_soc": 101}, "soc_unavailable"),
        ({"soc_measured_at": moment(-1)}, "soc_unavailable"),
        ({"soc_measured_at": moment(1)}, "soc_unavailable"),
        ({"device_available": False}, "device_unavailable"),
        ({"capacity_kwh": None}, "capacity_unavailable"),
        ({"capacity_kwh": 0}, "capacity_unavailable"),
        ({"charge_power_w": 0}, "charge_power_unavailable"),
        ({"eta_charge": 0}, "invalid_efficiency"),
        ({"eta_discharge": 1.1}, "invalid_efficiency"),
        ({"reserve_soc": 91}, "invalid_soc_limits"),
        ({"physical_min_soc": 91}, "invalid_soc_limits"),
    ],
)
def test_safety_errors_never_enable_min_max_fallback(changes, reason):
    state = snapshot(**changes)
    state = replace(state, pv=replace(state.pv, quality_reason="pv_stale"))
    plan = compute_energy_plan(state)
    assert plan.status == PlanStatus.BLOCKED
    assert plan.reason_codes == (reason,)
    assert not plan.intervals


@pytest.mark.parametrize("elapsed", [timedelta(minutes=16), timedelta(seconds=-1)])
def test_history_progress_cannot_be_stale_or_future(elapsed):
    state = snapshot()
    state = replace(state, load=replace(state.load, evaluated_through=NOW - elapsed))
    assert compute_energy_plan(state).reason_codes == ("history_stale",)


def test_forecast_global_failure_allows_only_data_fallback():
    state = snapshot()
    state = replace(state, pv=replace(state.pv, quality_reason="pv_source_unavailable"))
    plan = compute_energy_plan(state)
    assert plan.status == PlanStatus.FALLBACK
    assert plan.reason_codes == ("pv_source_unavailable",)


@pytest.mark.parametrize("energy", [-1, float("inf"), float("nan"), True])
def test_invalid_forecast_energy_is_rejected(energy):
    state = snapshot()
    state = replace(state, pv=replace(state.pv, intervals=(slot(0, 5, energy),)))
    assert compute_energy_plan(state).reason_codes == ("invalid_forecast_intervals",)


def test_overlapping_forecasts_do_not_double_count_energy():
    state = snapshot()
    state = replace(
        state, pv=replace(state.pv, intervals=(slot(0, 5, 4), slot(1, 3, 2)))
    )
    assert compute_energy_plan(state).reason_codes == ("invalid_forecast_intervals",)


def test_tariff_rejection_is_not_data_fallback():
    state = snapshot(tariff=TariffConstraints(quality_reason="prices_missing"))
    plan = compute_energy_plan(state)
    assert plan.status == PlanStatus.BLOCKED
    assert plan.reason_codes == ("prices_missing",)


def test_no_charge_permissions_expose_shortfall():
    plan = compute_energy_plan(snapshot(tariff=TariffConstraints()))
    assert plan.status == PlanStatus.LIMITED
    assert plan.planned_grid_kwh == 0
    assert plan.unmet_grid_kwh == pytest.approx(2)


def test_time_budget_limits_exact_energy_and_partial_slot():
    state = snapshot()
    state = replace(state, tariff=replace(state.tariff, max_charge_seconds=900))
    plan = compute_energy_plan(state)
    assert plan.status == PlanStatus.LIMITED
    assert plan.planned_grid_kwh == pytest.approx(1)
    assert plan.unmet_grid_kwh == pytest.approx(1)
    assert sum(
        (item.end - item.start).total_seconds() for item in plan.intervals
    ) == pytest.approx(900, abs=1e-4)


def test_soc_ceiling_exposes_unmet_need_without_overcharging():
    plan = compute_energy_plan(snapshot(max_soc=30))
    assert plan.planned_grid_kwh == pytest.approx(1, abs=1e-7)
    assert plan.unmet_grid_kwh == pytest.approx(1, abs=1e-7)
    assert plan.target_soc <= 30


def test_cheapest_feasible_energy_not_cheapest_late_deficit():
    state = snapshot(current_soc=10)
    state = replace(
        state,
        tariff=TariffConstraints(
            (window(0, 1, 0.2), window(3, 4, 0.05)),
            (window(0, 1, 0.2), window(3, 4, 0.05)),
            (window(0, 1),),
        ),
    )
    plan = compute_energy_plan(state)
    assert plan.unmet_grid_kwh == 0
    assert any(item.start < moment(1) for item in plan.intervals)
    assert any(item.start >= moment(3) for item in plan.intervals)


def test_negative_price_does_not_buy_more_than_required():
    state = snapshot(current_soc=50)
    state = replace(
        state, tariff=TariffConstraints((window(0, 1, -100),), (window(0, 1, -100),))
    )
    plan = compute_energy_plan(state)
    assert plan.status == PlanStatus.NO_NEED
    assert plan.planned_grid_kwh == 0
    assert not plan.intervals


def test_grid_price_optimization_preserves_minimal_energy():
    state = snapshot()
    state = replace(
        state,
        tariff=TariffConstraints(
            (window(0, 0.5, 0.3), window(0.5, 1, 0.1)), (window(0, 1),), (window(0, 1),)
        ),
    )
    plan = compute_energy_plan(state)
    assert plan.planned_grid_kwh == pytest.approx(2, abs=1e-7)
    assert all(item.price_eur_kwh == 0.1 for item in plan.intervals)


def test_same_input_is_immutable_and_deterministic():
    state = snapshot()
    first = compute_energy_plan(state)
    assert compute_energy_plan(state) == first
    assert first.valid_until == NOW + timedelta(minutes=10)
    with pytest.raises(FrozenInstanceError):
        state.current_soc = 50


def test_real_partial_charge_reduces_remaining_plan():
    first = compute_energy_plan(snapshot())
    second = compute_energy_plan(snapshot(current_soc=30))
    assert first.planned_grid_kwh - second.planned_grid_kwh == pytest.approx(
        1, abs=1e-7
    )


def test_shorter_source_and_tariff_leases_are_respected():
    state = snapshot()
    end = NOW + timedelta(minutes=3)
    state = replace(state, pv=replace(state.pv, valid_until=end))
    assert compute_energy_plan(state).valid_until == end


def test_dst_aware_intervals_use_real_duration():
    state = snapshot()
    zone = ZoneInfo("Europe/Berlin")
    translated = replace(
        state,
        load=replace(
            state.load,
            intervals=tuple(
                replace(
                    item,
                    start=item.start.astimezone(zone),
                    end=item.end.astimezone(zone),
                )
                for item in state.load.intervals
            ),
        ),
        pv=replace(
            state.pv,
            intervals=tuple(
                replace(
                    item,
                    start=item.start.astimezone(zone),
                    end=item.end.astimezone(zone),
                )
                for item in state.pv.intervals
            ),
        ),
    )
    plan = compute_energy_plan(translated)
    assert plan.planned_grid_kwh == pytest.approx(
        compute_energy_plan(state).planned_grid_kwh
    )
    assert all(item.start.tzinfo is UTC for item in plan.intervals)


def test_physical_reserve_does_not_create_energy_below_device_minimum():
    state = snapshot(current_soc=0, physical_min_soc=10, reserve_soc=20)
    plan = compute_energy_plan(state)
    assert plan.required_grid_kwh == pytest.approx(5, abs=1e-7)
    assert plan.planned_grid_kwh == pytest.approx(4, abs=1e-7)
    assert plan.unmet_grid_kwh == pytest.approx(1, abs=1e-7)
    assert plan.trajectory[0].stored_kwh == 0


def test_empty_battery_direct_import_during_window_is_not_stored_twice():
    state = snapshot(current_soc=0)
    state = replace(
        state,
        load=replace(
            state.load, intervals=(slot(0, 1, 1), slot(1, 4, 1.5), slot(4, 5, 1))
        ),
    )
    plan = compute_energy_plan(state)
    assert plan.planned_grid_kwh == pytest.approx(2.5, abs=1e-7)
    assert plan.trajectory[-1].stored_kwh == pytest.approx(1, abs=1e-7)


def test_actual_hold_is_not_assumed_before_first_planned_charge():
    state = snapshot(current_soc=15)
    state = replace(
        state,
        load=replace(
            state.load, intervals=(slot(0, 1, 1), slot(1, 4, 3), slot(4, 5, 1))
        ),
        tariff=TariffConstraints(
            (window(0, 1),), (window(0, 1),), hold_after_charge=True
        ),
    )
    plan = compute_energy_plan(state)
    assert plan.status == PlanStatus.PLANNED
    assert plan.trajectory[-1].stored_kwh >= 1 - 1e-7
    assert all(point.stored_kwh >= 0 for point in plan.trajectory)


def test_no_tiny_charge_created_only_to_obtain_a_hold():
    state = snapshot(current_soc=50)
    state = replace(state, tariff=replace(state.tariff, hold_after_charge=True))
    assert not compute_energy_plan(state).intervals


def test_forecast_pv_is_captured_before_the_confirmed_supply_when_possible():
    state = snapshot(current_soc=20)
    state = replace(
        state,
        pv=replace(
            state.pv,
            intervals=(slot(0, 1, 0), slot(1, 1.5, 2), slot(1.5, 4, 0), slot(4, 5, 2)),
        ),
    )
    plan = compute_energy_plan(state)
    assert plan.pv_supply_at == moment(4)
    assert plan.planned_grid_kwh == pytest.approx(0, abs=1e-7)
    assert plan.pv_used_kwh == pytest.approx(2, abs=1e-7)


def test_price_timing_does_not_displace_free_pv():
    state = snapshot(current_soc=10, max_soc=30)
    state = replace(
        state,
        tariff=TariffConstraints(
            (window(0, 1, -0.2), window(2, 3, 0.2)),
            (window(0, 1), window(2, 3)),
            (window(0, 1),),
        ),
        pv=replace(
            state.pv,
            intervals=(slot(0, 1, 0), slot(1, 1.5, 2), slot(1.5, 4, 0), slot(4, 5, 2)),
        ),
    )
    plan = compute_energy_plan(state)
    # During the late charge the house uses direct grid power: 0.8 kWh
    # stored grid energy also avoids 0.2 kWh of discharge. The negative
    # earlier price must not buy a larger battery quantity instead.
    assert plan.planned_grid_kwh == pytest.approx(0.8, abs=1e-7)
    assert plan.unmet_grid_kwh == 0
    assert all(item.price_eur_kwh == 0.2 for item in plan.intervals)
    assert all(point.stored_kwh <= 3 + 1e-7 for point in plan.trajectory)


def test_replanning_at_selected_start_does_not_postpone_charging_by_microseconds():
    """LP tolerances must not indefinitely move an immediately due command."""
    state = snapshot(current_soc=0, capacity_kwh=5.7, charge_power_w=4600)
    state = replace(
        state,
        load=replace(state.load, intervals=(slot(0, 4, 2), slot(4, 5, 0.5))),
        tariff=replace(
            state.tariff, discharge_blocked_windows=(), hold_after_charge=True
        ),
    )
    initial = compute_energy_plan(state)
    assert initial.next_start is not None and initial.next_start > NOW
    now = initial.next_start
    due = compute_energy_plan(
        replace(
            state,
            as_of=now,
            soc_measured_at=now,
            load=replace(state.load, evaluated_through=now),
        )
    )
    assert due.next_start == now
    assert due.charge_now
    assert due.planned_grid_kwh == pytest.approx(2.07, abs=1e-7)


def test_numerical_start_snap_does_not_advance_a_real_tariff_boundary():
    """A cheap slot beginning less than one millisecond later is still future."""
    state = snapshot(current_soc=0)
    boundary = NOW + timedelta(microseconds=500)
    charging = TariffWindow(boundary, moment(1))
    state = replace(
        state,
        load=replace(
            state.load, intervals=(slot(0, 1, 0), slot(1, 4, 3), slot(4, 5, 1))
        ),
        tariff=TariffConstraints((charging,), (charging,), (charging,)),
    )
    plan = compute_energy_plan(state)
    assert plan.next_start == boundary
    assert not plan.charge_now


def test_interval_merging_preserves_even_a_microsecond_price_gap():
    state = snapshot(current_soc=0)
    after_gap = moment(0.5) + timedelta(microseconds=5)
    windows = (window(0, 0.5), TariffWindow(after_gap, moment(1)))
    plan = compute_energy_plan(
        replace(state, tariff=TariffConstraints(windows, windows, windows))
    )
    assert len(plan.intervals) == 2
    assert plan.intervals[0].end <= moment(0.5)
    assert plan.intervals[1].start >= after_gap


@pytest.mark.parametrize(
    ("soc", "efficiency", "expected_grid", "expected_target"),
    [
        (0, 1, 1.25, 12.5),
        (10, 1, 4 / 9, 12.5),
        (10, 0.95, (0.5 / 0.95) / (0.95 + 0.5 / (4 * 0.95)), 12.631578947),
        (20, 1, 0, 20),
    ],
)
def test_one_hour_bridge_has_independently_calculated_physics(
    soc, efficiency, expected_grid, expected_target
):
    """Charging serves house power directly; reserve remains exactly once."""
    state = snapshot(current_soc=soc, eta_charge=efficiency, eta_discharge=efficiency)
    charging = window(0, 0.5)
    state = replace(
        state,
        load=replace(
            state.load,
            intervals=(slot(0, 1, 0.5), slot(1, 2, 0.5)),
            model_end=moment(2),
        ),
        pv=replace(state.pv, intervals=(slot(0, 1, 0), slot(1, 2, 1))),
        tariff=TariffConstraints((charging,), (charging,)),
    )
    plan = compute_energy_plan(state)
    assert plan.pv_supply_at == moment(1)
    assert plan.planned_grid_kwh == pytest.approx(expected_grid, abs=1e-7)
    assert plan.target_soc == pytest.approx(expected_target, abs=1e-6)
    assert plan.unmet_grid_kwh == 0
    if expected_grid:
        assert plan.trajectory[-1].stored_kwh == pytest.approx(1, abs=1e-7)


def test_one_hour_pv_wait_exception_does_not_buy_the_missing_reserve():
    state = snapshot(current_soc=0)
    charging = window(0, 1)
    state = replace(
        state,
        load=replace(
            state.load,
            intervals=(slot(0, 0.5, 0.25), slot(0.5, 1.5, 0.5)),
            model_end=moment(1.5),
        ),
        pv=replace(state.pv, intervals=(slot(0, 0.5, 0), slot(0.5, 1.5, 1))),
        tariff=TariffConstraints((charging,), (charging,)),
    )
    plan = compute_energy_plan(state)
    assert plan.reason_codes == ("waiting_for_pv_in_cheap_window",)
    assert plan.pv_supply_at == moment(0.5)
    assert plan.planned_grid_kwh == 0
    assert not plan.intervals
