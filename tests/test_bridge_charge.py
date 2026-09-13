"""Consumption-driven, tariff-neutral bridge planning (REQ-BRIDGE-CHARGE)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from custom_components.sax_power.domain.bridge_charge import (
    BridgeChargePlan,
    BridgeChargeStatus,
    ChargeWindow,
    plan_bridge_charge,
)

NOW = datetime(2026, 9, 13, tzinfo=UTC)


def _at(hours: float) -> datetime:
    return NOW + timedelta(hours=hours)


def _window(start: float, end: float, price: float | None = None) -> ChargeWindow:
    return ChargeWindow(_at(start), _at(end), price)


def _plan(**values: Any) -> BridgeChargePlan:
    return plan_bridge_charge(
        **(
            {
                "now": NOW,
                "pv_start": _at(8),
                "average_discharge_w": 500,
                "capacity_wh": 10000,
                "soc": 25,
                "min_soc": 10,
                "max_soc": 80,
                "charge_power_w": 2000,
                "windows": [_window(0, 6)],
            }
            | values
        )
    )


def test_charge_accounts_for_grid_supplied_consumption_during_charging() -> None:
    plan = _plan()
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.discharge_until == _at(3)
    assert plan.start == _at(3)
    assert plan.end == _at(4)
    assert plan.target_soc == pytest.approx(30)
    assert plan.required_energy_wh == 2500
    assert plan.charge_energy_wh == 2000
    assert plan.missing_energy_wh == 0
    # Four hours after charging consume exactly the newly stored energy.
    assert 500 * (8 - 4) == plan.charge_energy_wh


def test_weighted_average_is_used_without_reaveraging_observations() -> None:
    average = (1000 * 10 + 2000 * 50) / 60
    plan = _plan(average_discharge_w=average)
    expected_hours = (average * 8 - 1500) / (2000 + average)
    assert plan.end is not None and plan.start is not None
    assert (plan.end - plan.start).total_seconds() == pytest.approx(
        expected_hours * 3600
    )
    assert plan.start == NOW + timedelta(hours=1500 / average)
    assert plan.missing_energy_wh == 0


@pytest.mark.parametrize("soc", [50, 60, 100])
def test_existing_energy_covering_pv_requires_no_charge(soc: float) -> None:
    plan = _plan(soc=soc, windows=[])
    assert plan.status == BridgeChargeStatus.NOT_NEEDED
    assert plan.start is None and plan.end is None and plan.target_soc is None
    assert (
        plan.required_energy_wh == plan.charge_energy_wh == plan.missing_energy_wh == 0
    )


def test_zero_consumption_needs_no_charge_and_has_no_empty_time() -> None:
    plan = _plan(average_discharge_w=0, soc=10)
    assert plan.status == BridgeChargeStatus.NOT_NEEDED
    assert plan.discharge_until is None


def test_window_end_can_require_charging_before_empty_time() -> None:
    plan = _plan(windows=[_window(0, 2)])
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == _at(1) and plan.end == _at(2)
    assert plan.target_soc == pytest.approx(40)


def test_cheapest_sufficient_window_wins_even_when_earlier() -> None:
    plan = _plan(windows=[_window(0, 2, 0.1), _window(2, 6, 0.2)])
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == _at(1) and plan.end == _at(2)
    assert plan.price == 0.1


@pytest.mark.parametrize("price", [None, 0, -0.05, 0.2])
def test_equally_priced_sufficient_windows_choose_latest(price: float | None) -> None:
    plan = _plan(windows=[_window(0, 2, price), _window(2, 6, price)])
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == _at(3) and plan.end == _at(4)


def test_known_prices_rank_before_unknown_prices() -> None:
    plan = _plan(windows=[_window(0, 2, 0.2), _window(2, 6)])
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == _at(1) and plan.price == 0.2


def test_short_cheap_window_cannot_displace_sufficient_expensive_window() -> None:
    plan = _plan(windows=[_window(0, 0.5, 0.1), _window(2, 6, 0.2)])
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == _at(3) and plan.price == 0.2


def test_capacity_ceiling_limits_partial_charge_and_reports_deficit() -> None:
    plan = _plan(max_soc=20)
    assert plan.status == BridgeChargeStatus.INSUFFICIENT
    assert plan.start == _at(5.5) and plan.end == _at(6)
    assert plan.target_soc == pytest.approx(20)
    assert plan.charge_energy_wh == 1000
    assert plan.missing_energy_wh == 1250


def test_initial_soc_above_ceiling_waits_for_actual_headroom() -> None:
    plan = _plan(max_soc=25, windows=[_window(0, 1)])
    assert plan.status == BridgeChargeStatus.INSUFFICIENT
    assert plan.start == _at(0.8) and plan.end == _at(1)
    assert plan.target_soc == pytest.approx(25)
    assert plan.charge_energy_wh == pytest.approx(400)


def test_below_current_soc_ceiling_makes_early_window_unusable() -> None:
    plan = _plan(max_soc=15, windows=[_window(0, 1)])
    assert plan.status == BridgeChargeStatus.INSUFFICIENT
    assert plan.start is None and plan.end is None
    assert plan.missing_energy_wh == 2500


def test_short_window_returns_only_executable_partial_energy() -> None:
    plan = _plan(windows=[_window(1, 1.5)])
    assert plan.status == BridgeChargeStatus.INSUFFICIENT
    assert plan.start == _at(1) and plan.end == _at(1.5)
    assert plan.charge_energy_wh == 1000
    assert plan.missing_energy_wh == 1250


def test_gap_before_late_window_is_not_hidden_by_subsequent_charge() -> None:
    plan = _plan(windows=[_window(7, 8)])
    assert plan.status == BridgeChargeStatus.INSUFFICIENT
    assert plan.start == _at(7) and plan.end == _at(7.2)
    assert plan.charge_energy_wh == pytest.approx(400)
    assert plan.missing_energy_wh == pytest.approx(2000)
    assert plan.target_soc == pytest.approx(14)


def test_partial_plan_maximizes_coverage_before_comparing_prices() -> None:
    plan = _plan(windows=[_window(1, 1.1, 0.1), _window(2, 2.5, 0.2)])
    assert plan.status == BridgeChargeStatus.INSUFFICIENT
    assert plan.start == _at(2) and plan.end == _at(2.5)
    assert plan.price == 0.2


@pytest.mark.parametrize("windows", [[], [_window(-3, -1)], [_window(8, 12)]])
def test_no_window_before_pv_has_no_invented_charge_times(
    windows: list[ChargeWindow],
) -> None:
    plan = _plan(windows=windows)
    assert plan.status == BridgeChargeStatus.INSUFFICIENT
    assert plan.start is None and plan.end is None and plan.target_soc is None
    assert plan.missing_energy_wh == 2500
    assert plan.charge_energy_wh == 0


def test_window_is_clipped_at_now_and_pv_start() -> None:
    plan = _plan(soc=10, windows=[_window(-3, 12)])
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == NOW
    assert plan.end == _at(1.6)
    assert plan.target_soc == pytest.approx(42)


def test_zero_usable_capacity_never_produces_charge() -> None:
    plan = _plan(soc=10, min_soc=10, max_soc=10)
    assert plan.status == BridgeChargeStatus.INSUFFICIENT
    assert plan.start is None
    assert plan.missing_energy_wh == 4000


def test_adjacent_equal_price_segments_allow_continuous_charge() -> None:
    plan = _plan(windows=[_window(2.5, 3.5, 0.1), _window(3.5, 5, 0.1)])
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == _at(3) and plan.end == _at(4)


def test_overlapping_equal_prices_merge_even_with_other_price_between() -> None:
    plan = _plan(
        windows=[_window(2.5, 3.5, 0.1), _window(3, 4.1, 0.3), _window(3.5, 5, 0.1)]
    )
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == _at(3) and plan.end == _at(4) and plan.price == 0.1


def test_differently_priced_segments_do_not_create_fictitious_flat_price() -> None:
    plan = _plan(windows=[_window(2.5, 3, 0.1), _window(3, 3.5, 0.2)])
    assert plan.status == BridgeChargeStatus.INSUFFICIENT
    assert plan.start == _at(2.5) and plan.end == _at(3)
    assert plan.missing_energy_wh == 1250


def test_midnight_window_uses_elapsed_time() -> None:
    now = datetime(2026, 9, 13, 22, tzinfo=UTC)
    plan = _plan(
        now=now,
        pv_start=now + timedelta(hours=8),
        windows=[ChargeWindow(now, now + timedelta(hours=6))],
    )
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == datetime(2026, 9, 14, 1, tzinfo=UTC)
    assert plan.end == datetime(2026, 9, 14, 2, tzinfo=UTC)


@pytest.mark.parametrize("month,day,elapsed", [(3, 29, 7), (10, 25, 9)])
def test_dst_horizon_uses_utc_elapsed_hours(month: int, day: int, elapsed: int) -> None:
    zone = ZoneInfo("Europe/Berlin")
    now = datetime(2026, month, day, 0, tzinfo=zone)
    pv_start = datetime(2026, month, day, 8, tzinfo=zone)
    plan = _plan(now=now, pv_start=pv_start, windows=[ChargeWindow(now, pv_start)])
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == now.astimezone(UTC) + timedelta(hours=3)
    duration = (500 * elapsed - 1500) / 2500
    assert plan.end == plan.start + timedelta(hours=duration)
    assert plan.start.tzinfo is UTC and plan.end.tzinfo is UTC


def test_folded_local_interval_is_valid_even_with_equal_wall_clock_time() -> None:
    zone = ZoneInfo("Europe/Berlin")
    start = datetime(2026, 10, 25, 2, tzinfo=zone, fold=0)
    end = datetime(2026, 10, 25, 2, tzinfo=zone, fold=1)
    plan = _plan(now=start, pv_start=end, soc=10, windows=[ChargeWindow(start, end)])
    assert plan.status == BridgeChargeStatus.PLANNED
    assert plan.start == start.astimezone(UTC)
    assert plan.end == start.astimezone(UTC) + timedelta(minutes=12)


@pytest.mark.parametrize("key", ["now", "pv_start"])
def test_naive_times_are_unavailable(key: str) -> None:
    plan = _plan(**{key: datetime(2026, 9, 13)})
    assert plan.status == BridgeChargeStatus.UNAVAILABLE
    assert plan.reason == "invalid_time"


@pytest.mark.parametrize("pv_start", [NOW, _at(-1)])
def test_past_or_current_pv_start_is_unavailable(pv_start: datetime) -> None:
    assert _plan(pv_start=pv_start).status == BridgeChargeStatus.UNAVAILABLE


@pytest.mark.parametrize(
    "key",
    [
        "average_discharge_w",
        "capacity_wh",
        "soc",
        "min_soc",
        "max_soc",
        "charge_power_w",
    ],
)
@pytest.mark.parametrize(
    "invalid", [None, True, "10", float("nan"), float("inf"), 10**1000]
)
def test_non_numeric_inputs_are_unavailable(key: str, invalid: Any) -> None:
    plan = _plan(**{key: invalid})
    assert plan.status == BridgeChargeStatus.UNAVAILABLE
    assert plan.start is None and plan.required_energy_wh is None


@pytest.mark.parametrize(
    "values",
    [
        {"soc": 5},
        {"soc": 101},
        {"min_soc": -1},
        {"min_soc": 90},
        {"max_soc": 101},
        {"capacity_wh": 0},
        {"capacity_wh": -1},
        {"charge_power_w": 0},
        {"charge_power_w": -1},
        {"average_discharge_w": -1},
        {"average_discharge_w": 1e308},
    ],
)
def test_invalid_ranges_and_overflow_are_unavailable(values: dict[str, float]) -> None:
    assert _plan(**values).status == BridgeChargeStatus.UNAVAILABLE


@pytest.mark.parametrize(
    "windows",
    [
        None,
        [None],
        [ChargeWindow(NOW.replace(tzinfo=None), _at(6))],
        [_window(2, 1)],
        [_window(1, 1)],
        [_window(0, 6, float("nan"))],
        [_window(0, 6, True)],
    ],
)
def test_invalid_window_inputs_are_unavailable(windows: Any) -> None:
    assert _plan(windows=windows).status == BridgeChargeStatus.UNAVAILABLE


@pytest.mark.parametrize("discharge", [100, 500, 3000])
@pytest.mark.parametrize("power", [100, 2000, 7000])
@pytest.mark.parametrize("soc", [10, 25, 95])
@pytest.mark.parametrize("max_soc", [10, 20, 80])
def test_charge_obeys_physical_energy_balance(
    discharge: float, power: float, soc: float, max_soc: float
) -> None:
    """Independently account for both gaps and battery energy after execution."""
    windows = [_window(0, 1, 0.1), _window(2, 6, 0.2), _window(7, 8, 0.3)]
    plan = _plan(
        average_discharge_w=discharge,
        charge_power_w=power,
        soc=soc,
        max_soc=max_soc,
        windows=windows,
    )
    if plan.start is None:
        assert plan.end is None and plan.charge_energy_wh == 0
        return
    assert plan.end is not None and plan.target_soc is not None
    assert any(
        window.start <= plan.start < plan.end <= window.end for window in windows
    )
    assert NOW <= plan.start < plan.end <= _at(8)
    assert 10 <= plan.target_soc <= max_soc
    before_hours = (plan.start - NOW).total_seconds() / 3600
    charging_hours = (plan.end - plan.start).total_seconds() / 3600
    after_hours = (_at(8) - plan.end).total_seconds() / 3600
    initial_energy = 100 * (soc - 10)
    gap_before = max(discharge * before_hours - initial_energy, 0)
    remaining_before = max(initial_energy - discharge * before_hours, 0)
    energy_after = remaining_before + power * charging_hours
    gap_after = max(discharge * after_hours - energy_after, 0)
    assert plan.charge_energy_wh == pytest.approx(power * charging_hours, abs=1e-5)
    assert plan.target_soc == pytest.approx(10 + energy_after / 100, abs=1e-5)
    assert plan.missing_energy_wh == pytest.approx(gap_before + gap_after, abs=1e-5)
    assert energy_after <= discharge * after_hours + 1e-5
    if plan.status == BridgeChargeStatus.PLANNED:
        assert gap_before + gap_after <= 1e-5
