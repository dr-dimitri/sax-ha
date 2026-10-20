"""Measured charging progress and current demand (REQ-BRIDGE-CHARGE)."""

from __future__ import annotations

import math
from dataclasses import dataclass


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        return float(value) if math.isfinite(value) else None
    except OverflowError:
        return None


@dataclass(frozen=True, slots=True)
class ChargeProgress:
    """Display-only estimates never authorize or extend a device command."""

    active: bool = False
    power_w: float | None = None
    target_soc: float | None = None
    max_soc: float | None = None
    remaining_seconds: float | None = None


def estimate_charge_progress(
    *,
    active: bool,
    storage_power_w: object,
    capacity_wh: object,
    soc: object,
    target_soc: object,
    max_soc: object,
    window_seconds: float | None = None,
) -> ChargeProgress:
    """Estimate time to the actual target, bounded by its authorized window."""
    measured_power = _number(storage_power_w)
    if not active or measured_power is None or measured_power >= 0:
        return ChargeProgress()
    power = -measured_power
    maximum = _number(max_soc)
    maximum = maximum if maximum is not None and 0 <= maximum <= 100 else None
    target = _number(target_soc)
    target = (
        min(target, maximum)
        if target is not None and 0 <= target <= 100 and maximum is not None
        else None
    )
    capacity = _number(capacity_wh)
    current_soc = _number(soc)
    remaining = None
    if (
        capacity is not None
        and capacity > 0
        and current_soc is not None
        and 0 <= current_soc <= 100
        and target is not None
    ):
        seconds = capacity * max(target - current_soc, 0.0) / 100 / power * 3600
        if math.isfinite(seconds):
            remaining = seconds
            if window_seconds is not None:
                window = _number(window_seconds)
                remaining = (
                    min(seconds, window) if window is not None and window >= 0 else None
                )
    return ChargeProgress(True, power, target, maximum, remaining)


def assess_charge_demand(
    *,
    capacity_wh: object,
    soc: object,
    min_soc: object,
    average_discharge_w: object,
    until_pv_seconds: object,
) -> str:
    """Compare current energy with fresh consumption until the current PV start."""
    capacity = _number(capacity_wh)
    current_soc = _number(soc)
    minimum = _number(min_soc)
    average = _number(average_discharge_w)
    horizon = _number(until_pv_seconds)
    if (
        capacity is None
        or capacity <= 0
        or current_soc is None
        or minimum is None
        or not 0 <= minimum <= current_soc <= 100
        or average is None
        or average <= 0
        or horizon is None
        or horizon <= 0
    ):
        return "unknown"
    available = capacity * (current_soc - minimum) / 100
    required = average * horizon / 3600
    if not math.isfinite(available) or not math.isfinite(required):
        return "unknown"
    return "needed" if required - available > 1 else "not_needed"


def estimate_discharge_remaining_seconds(
    *,
    capacity_wh: object,
    soc: object,
    min_soc: object,
    average_discharge_w: object,
) -> float | None:
    """Use the same current energy snapshot as the demand verdict."""
    capacity = _number(capacity_wh)
    current_soc = _number(soc)
    minimum = _number(min_soc)
    average = _number(average_discharge_w)
    if (
        capacity is None
        or capacity <= 0
        or current_soc is None
        or minimum is None
        or not 0 <= minimum <= current_soc <= 100
        or average is None
        or average <= 0
    ):
        return None
    seconds = capacity * (current_soc - minimum) / 100 / average * 3600
    return seconds if math.isfinite(seconds) else None
