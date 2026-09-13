"""Pure priority policy for the charging use cases.

The policy only decides which use cases are eligible. Stateful hysteresis and
all physical device writes remain in ``SaxPowerCoordinator``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from datetime import time as dt_time

from ..const import (
    MIN_SETPOINT_POWER,
    PRICE_STRATEGY_ABSOLUTE,
    PRICE_STRATEGY_OFF,
    PRICE_STRATEGY_RELATIVE,
    PRICE_STRATEGY_SMART,
)
from ..domain.scheduling import is_time_in_window
from ..domain.tariff import TariffType


def tariff_automation_controls(
    tariff_type: TariffType,
    timed_enabled: bool,
    price_enabled: bool,
    *,
    previous_tariff_type: TariffType | None = None,
    enabled: bool | None = None,
) -> tuple[bool, bool]:
    """REQ-VUE-ELECTRICITY-TARIFF: one selected source owns automatic charging."""
    if tariff_type not in (TariffType.TIME_OF_USE, TariffType.DYNAMIC):
        return timed_enabled, price_enabled
    if enabled is None:
        if previous_tariff_type is not None and previous_tariff_type != tariff_type:
            enabled = timed_enabled or price_enabled
        else:
            enabled = (
                timed_enabled
                if tariff_type is TariffType.TIME_OF_USE
                else price_enabled
            )
    return (
        bool(enabled and tariff_type is TariffType.TIME_OF_USE),
        bool(enabled and tariff_type is TariffType.DYNAMIC),
    )


def timed_discharge_hold_active(
    *, now: datetime, enabled: bool, price_enabled: bool, expires_at: datetime | None
) -> bool:
    """Keep the measured timed-charge hold separate from every price strategy."""
    return enabled and not price_enabled and expires_at is not None and now < expires_at


def timed_discharge_pv_power(storage_power: object, grid_power: object) -> int:
    """REQ-TIMED-SOC-CHARGE: S + M is house demand minus generation."""
    if any(
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(value)
        for value in (storage_power, grid_power)
    ):
        return 0
    # int rounds toward zero, so quantization cannot request extra charging.
    return int(max(MIN_SETPOINT_POWER, min(0, storage_power + grid_power)))


@dataclass(frozen=True, slots=True)
class ChargePolicyInput:
    """Inputs needed to evaluate the charging priority rules."""

    now: datetime
    current_soc: int
    target_soc: int
    timed_target_soc: int
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
    price_strategy: str
    price_charge_now: bool
    current_price: float | None
    price_limit: float | None
    neutral_price: float | None
    timed_window_completed: bool = False
    timed_plan_charge_now: bool | None = None
    timed_tariff_window_active: bool | None = None


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
        and (
            inputs.timed_plan_charge_now
            if inputs.timed_plan_charge_now is not None
            else not inputs.timed_window_completed
            and (
                inputs.timed_tariff_window_active
                if inputs.timed_tariff_window_active is not None
                else is_time_in_window(
                    inputs.now.time(), inputs.timed_start, inputs.timed_end
                )
            )
        )
    )
    timed_should_charge = (
        not soc_reached
        and inputs.current_soc < inputs.timed_target_soc
        and not inputs.pv_surplus_active
        and timed_window_active
        and (
            inputs.timed_plan_charge_now is not None
            or inputs.timed_min_soc is not None
            and inputs.timed_armed
        )
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
        and inputs.price_strategy != PRICE_STRATEGY_OFF
        and inputs.price_charge_now
    )
    price_should_pause = (
        not soc_reached
        and not inputs.pv_surplus_active
        and not timed_should_charge
        and not grid_serving_window_active
        and not price_should_charge
        and inputs.price_enabled
        and inputs.current_price is not None
        and inputs.neutral_price is not None
        and inputs.current_price < inputs.neutral_price
        and (
            inputs.price_strategy in (PRICE_STRATEGY_RELATIVE, PRICE_STRATEGY_SMART)
            or (
                inputs.price_strategy == PRICE_STRATEGY_ABSOLUTE
                and inputs.price_limit is not None
                and inputs.price_limit < inputs.current_price
            )
        )
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
