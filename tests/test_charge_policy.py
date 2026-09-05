"""Unit tests for the framework-independent charging priority policy."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, time, timedelta

import pytest

from custom_components.sax_power.application.charge_policy import (
    ChargePolicyInput,
    evaluate_charge_policy,
    timed_discharge_hold_active,
    timed_discharge_pv_power,
)
from custom_components.sax_power.const import MIN_SETPOINT_POWER


@pytest.mark.parametrize(
    ("storage", "grid", "expected"),
    [
        (-2000, 0, -2000),
        (0, -1000, -1000),
        (-4600, 4600, 0),
        (-2000, 500, -1500),
        (500, -1000, -500),
        (500, 1000, 0),
        (-10.9, 0, -10),
        (-1e20, 0, MIN_SETPOINT_POWER),
        (None, -1000, 0),
        (-2000, None, 0),
        (float("nan"), -1000, 0),
        (-2000, float("inf"), 0),
        (False, -1000, 0),
        (-2000, "0", 0),
    ],
)
def test_timed_hold_only_requests_available_pv_power(storage, grid, expected) -> None:
    """REQ-TIMED-SOC-CHARGE: neither discharge nor household grid import is PV."""
    assert timed_discharge_pv_power(storage, grid) == expected


@pytest.mark.parametrize(
    ("enabled", "price_enabled", "seconds_left", "expected"),
    [
        (True, False, 1, True),
        (True, False, 0, False),
        (True, False, -1, False),
        (True, True, 60, False),
        (False, False, 60, False),
    ],
)
def test_timed_hold_eligibility_is_independent_of_price(
    enabled, price_enabled, seconds_left, expected
) -> None:
    """REQ-TIMED-SOC-CHARGE: price mode and disabling never retain this hold."""
    now = datetime(2026, 9, 5, tzinfo=UTC)
    assert (
        timed_discharge_hold_active(
            now=now,
            enabled=enabled,
            price_enabled=price_enabled,
            expires_at=now + timedelta(seconds=seconds_left),
        )
        is expected
    )


def _inputs() -> ChargePolicyInput:
    return ChargePolicyInput(
        now=datetime(2026, 1, 15, 12),
        current_soc=30,
        target_soc=80,
        timed_target_soc=80,
        pv_surplus_active=False,
        timed_enabled=False,
        timed_start=time(0),
        timed_end=time(23, 59),
        timed_months={1},
        timed_min_soc=40,
        timed_armed=True,
        grid_serving_enabled=False,
        grid_serving_start=time(10),
        grid_serving_end=time(14),
        grid_serving_months={1},
        grid_serving_forecast_allowed=True,
        price_enabled=False,
        price_strategy_active=False,
        price_charge_now=False,
        current_price=None,
        price_limit=None,
        neutral_price=None,
    )


def test_max_soc_takes_priority_over_all_charging_modes() -> None:
    decision = evaluate_charge_policy(
        replace(
            _inputs(),
            current_soc=80,
            timed_enabled=True,
            grid_serving_enabled=True,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )

    assert decision.soc_reached is True
    assert decision.timed_should_charge is False
    assert decision.grid_serving_eligible is False
    assert decision.price_should_charge is False


def test_timed_charge_takes_priority_over_price_charge() -> None:
    decision = evaluate_charge_policy(
        replace(
            _inputs(),
            timed_enabled=True,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )

    assert decision.timed_should_charge is True
    assert decision.price_should_charge is False


def test_completed_timed_window_does_not_restart_after_extension() -> None:
    """REQ-TIMED-SOC-CHARGE: a completed occurrence cannot claim another hour."""
    decision = evaluate_charge_policy(
        replace(_inputs(), timed_enabled=True, timed_window_completed=True)
    )
    assert decision.timed_window_active is False
    assert decision.timed_should_charge is False


def test_timed_charge_stops_at_its_own_target_before_global_max_soc() -> None:
    """REQ-TIMED-SOC-CHARGE: the timed target only ends timed grid charging."""
    inputs = replace(
        _inputs(),
        current_soc=59,
        target_soc=90,
        timed_target_soc=60,
        timed_enabled=True,
    )

    assert evaluate_charge_policy(inputs).timed_should_charge is True

    decision = evaluate_charge_policy(replace(inputs, current_soc=60))

    assert decision.soc_reached is False
    assert decision.timed_window_active is True
    assert decision.timed_should_charge is False


def test_timed_target_does_not_limit_grid_serving_charge() -> None:
    """REQ-TIMED-SOC-CHARGE: grid-serving control retains its global limit."""
    decision = evaluate_charge_policy(
        replace(
            _inputs(),
            current_soc=70,
            target_soc=90,
            timed_target_soc=60,
            grid_serving_enabled=True,
        )
    )

    assert decision.soc_reached is False
    assert decision.grid_serving_eligible is True


def test_timed_target_does_not_limit_price_charge() -> None:
    """REQ-TIMED-SOC-CHARGE: price charging retains its global limit."""
    decision = evaluate_charge_policy(
        replace(
            _inputs(),
            current_soc=70,
            target_soc=90,
            timed_target_soc=60,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )

    assert decision.soc_reached is False
    assert decision.price_should_charge is True


def test_timed_target_does_not_block_neutral_price_pause() -> None:
    """REQ-TIMED-SOC-CHARGE: the neutral price pause remains independent."""
    decision = evaluate_charge_policy(
        replace(
            _inputs(),
            current_soc=70,
            target_soc=90,
            timed_target_soc=60,
            price_enabled=True,
            price_strategy_active=True,
            current_price=0.25,
            price_limit=0.20,
            neutral_price=0.30,
        )
    )

    assert decision.soc_reached is False
    assert decision.price_should_charge is False
    assert decision.price_should_pause is True


def test_global_max_soc_overrides_an_excessive_timed_target() -> None:
    """REQ-TIMED-SOC-CHARGE: the global SOC limit remains authoritative."""
    decision = evaluate_charge_policy(
        replace(
            _inputs(),
            current_soc=80,
            target_soc=80,
            timed_target_soc=90,
            timed_enabled=True,
            grid_serving_enabled=True,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )

    assert decision.soc_reached is True
    assert decision.timed_should_charge is False
    assert decision.grid_serving_eligible is False
    assert decision.price_should_charge is False
    assert decision.price_should_pause is False


def test_grid_serving_window_reserves_control_from_price_charge() -> None:
    decision = evaluate_charge_policy(
        replace(
            _inputs(),
            grid_serving_enabled=True,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )

    assert decision.grid_serving_window_active is True
    assert decision.grid_serving_eligible is True
    assert decision.price_should_charge is False


def test_low_forecast_releases_grid_serving_priority_for_price_charge() -> None:
    decision = evaluate_charge_policy(
        replace(
            _inputs(),
            grid_serving_enabled=True,
            grid_serving_forecast_allowed=False,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )

    assert decision.grid_serving_window_active is False
    assert decision.grid_serving_eligible is False
    assert decision.price_should_charge is True


def test_pv_surplus_blocks_timed_and_price_charge() -> None:
    decision = evaluate_charge_policy(
        replace(
            _inputs(),
            pv_surplus_active=True,
            timed_enabled=True,
            price_enabled=True,
            price_strategy_active=True,
            price_charge_now=True,
        )
    )

    assert decision.timed_should_charge is False
    assert decision.price_should_charge is False


def test_neutral_price_band_pauses_storage() -> None:
    decision = evaluate_charge_policy(
        replace(
            _inputs(),
            price_enabled=True,
            price_strategy_active=True,
            current_price=0.25,
            price_limit=0.20,
            neutral_price=0.30,
        )
    )

    assert decision.price_should_charge is False
    assert decision.price_should_pause is True
