"""Bridge eligibility retains central device safeguards (REQ-BRIDGE-CHARGE)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, time
from typing import Any

import pytest

from custom_components.sax_power.application.charge_policy import (
    ChargePolicyInput,
    evaluate_charge_policy,
)


def _inputs(**values: Any) -> ChargePolicyInput:
    return replace(
        ChargePolicyInput(
            now=datetime(2026, 9, 13, 2, tzinfo=UTC),
            current_soc=30,
            target_soc=90,
            timed_target_soc=80,
            pv_surplus_active=False,
            timed_enabled=True,
            timed_start=time(22),
            timed_end=time(23),
            timed_months={9},
            timed_min_soc=None,
            timed_armed=False,
            grid_serving_enabled=False,
            grid_serving_start=time(0),
            grid_serving_end=time(6),
            grid_serving_months={9},
            grid_serving_forecast_allowed=True,
            price_enabled=False,
            price_strategy_active=False,
            price_charge_now=False,
            current_price=None,
            price_limit=None,
            neutral_price=None,
            timed_plan_charge_now=True,
        ),
        **values,
    )


def test_due_bridge_replaces_legacy_time_pair_and_minimum_soc_latch() -> None:
    decision = evaluate_charge_policy(_inputs())
    assert decision.timed_window_active
    assert decision.timed_should_charge


def test_previously_completed_legacy_window_does_not_cancel_new_bridge() -> None:
    assert evaluate_charge_policy(
        _inputs(timed_window_completed=True)
    ).timed_should_charge


def test_not_due_bridge_cannot_fall_back_to_legacy_armed_window() -> None:
    decision = evaluate_charge_policy(
        _inputs(
            timed_plan_charge_now=False,
            timed_start=time(0),
            timed_end=time(6),
            timed_min_soc=50,
            timed_armed=True,
        )
    )
    assert not decision.timed_window_active
    assert not decision.timed_should_charge


@pytest.mark.parametrize(
    "values",
    [
        {"timed_enabled": False},
        {"timed_months": set()},
        {"timed_months": {10}},
        {"pv_surplus_active": True},
        {"current_soc": 90},
        {"current_soc": 80},
    ],
)
def test_due_bridge_cannot_bypass_enable_month_pv_or_soc_limits(
    values: dict[str, Any],
) -> None:
    assert not evaluate_charge_policy(_inputs(**values)).timed_should_charge


def test_global_soc_limit_blocks_all_competing_modes() -> None:
    decision = evaluate_charge_policy(
        _inputs(
            current_soc=90,
            grid_serving_enabled=True,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )
    assert decision.soc_reached
    assert not decision.timed_should_charge
    assert not decision.grid_serving_eligible
    assert not decision.price_should_charge


def test_due_bridge_retains_timed_priority_over_grid_serving_and_price() -> None:
    decision = evaluate_charge_policy(
        _inputs(
            grid_serving_enabled=True,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )
    assert decision.timed_should_charge
    assert not decision.grid_serving_eligible
    assert not decision.price_should_charge
    assert not decision.price_should_pause


def test_not_due_bridge_leaves_existing_price_policy_available() -> None:
    decision = evaluate_charge_policy(
        _inputs(
            timed_plan_charge_now=False,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )
    assert not decision.timed_should_charge
    assert decision.price_should_charge


def test_due_bridge_is_not_replaced_by_neutral_price_pause() -> None:
    decision = evaluate_charge_policy(
        _inputs(
            price_enabled=True,
            price_strategy_active=True,
            current_price=0.25,
            price_limit=0.2,
            neutral_price=0.3,
        )
    )
    assert decision.timed_should_charge
    assert not decision.price_should_pause


def test_pv_surplus_blocks_bridge_and_competing_price_charge() -> None:
    decision = evaluate_charge_policy(
        _inputs(
            pv_surplus_active=True,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )
    assert not decision.timed_should_charge
    assert not decision.price_should_charge
    assert not decision.price_should_pause


def test_absent_bridge_input_retains_legacy_minimum_soc_requirement() -> None:
    inputs = _inputs(timed_plan_charge_now=None, timed_start=time(0), timed_end=time(6))
    assert not evaluate_charge_policy(inputs).timed_should_charge
    assert evaluate_charge_policy(
        replace(inputs, timed_min_soc=50, timed_armed=True)
    ).timed_should_charge
