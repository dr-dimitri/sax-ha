"""Pure priority policy for the charging use cases.

The policy only decides which use cases are eligible. Stateful hysteresis and
all physical device writes remain in ``SaxPowerCoordinator``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import time as dt_time

from ..domain.scheduling import is_time_in_window


@dataclass(frozen=True, slots=True)
class ChargePolicyInput:
    """Inputs needed to evaluate the charging priority rules."""

    now: datetime
    current_soc: int
    target_soc: int
    pv_surplus_active: bool
    timed_enabled: bool
    timed_start: dt_time | None
    timed_end: dt_time | None
    timed_months: set[int]
    timed_min_soc: int | None
    timed_armed: bool
    grid_serving_enabled: bool
    grid_serving_start: dt_time | None
    grid_serving_end: dt_time | None
    grid_serving_months: set[int]
    grid_serving_forecast_allowed: bool
    price_enabled: bool
    price_strategy_active: bool
    price_charge_now: bool
    current_price: float | None
    price_limit: float | None
    neutral_price: float | None


@dataclass(frozen=True, slots=True)
class ChargePolicyDecision:
    """Eligibility flags after applying the documented feature priority."""

    soc_reached: bool
    timed_window_active: bool
    timed_should_charge: bool
    grid_serving_window_active: bool
    grid_serving_eligible: bool
    price_should_charge: bool
    price_should_pause: bool


def evaluate_charge_policy(inputs: ChargePolicyInput) -> ChargePolicyDecision:
    """Evaluate charging eligibility without accessing Home Assistant or Modbus."""
    soc_reached = inputs.current_soc >= inputs.target_soc
    timed_window_active = (
        inputs.timed_enabled
        and inputs.now.month in inputs.timed_months
        and is_time_in_window(inputs.now.time(), inputs.timed_start, inputs.timed_end)
    )
    timed_should_charge = (
        not soc_reached
        and not inputs.pv_surplus_active
        and timed_window_active
        and inputs.timed_min_soc is not None
        and inputs.timed_armed
    )
    grid_serving_window_active = (
        inputs.grid_serving_enabled
        and inputs.grid_serving_forecast_allowed
        and inputs.now.month in inputs.grid_serving_months
        and is_time_in_window(
            inputs.now.time(), inputs.grid_serving_start, inputs.grid_serving_end
        )
    )
    grid_serving_eligible = (
        not soc_reached and grid_serving_window_active and not timed_should_charge
    )
    price_should_charge = (
        not soc_reached
        and not inputs.pv_surplus_active
        and not timed_should_charge
        and not grid_serving_window_active
        and inputs.price_enabled
        and inputs.price_strategy_active
        and inputs.price_charge_now
    )
    price_should_pause = (
        not soc_reached
        and not inputs.pv_surplus_active
        and not timed_should_charge
        and not grid_serving_window_active
        and not price_should_charge
        and inputs.price_enabled
        and inputs.price_strategy_active
        and inputs.current_price is not None
        and inputs.price_limit is not None
        and inputs.neutral_price is not None
        and inputs.price_limit < inputs.neutral_price
        and inputs.price_limit < inputs.current_price < inputs.neutral_price
    )
    return ChargePolicyDecision(
        soc_reached=soc_reached,
        timed_window_active=timed_window_active,
        timed_should_charge=timed_should_charge,
        grid_serving_window_active=grid_serving_window_active,
        grid_serving_eligible=grid_serving_eligible,
        price_should_charge=price_should_charge,
        price_should_pause=price_should_pause,
    )
