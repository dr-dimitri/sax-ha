"""Tariff-independent charging to bridge consumption until PV production."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

_ENERGY_EPSILON = 1e-6


class BridgeChargeStatus(StrEnum):
    """Whether one bounded charge can cover the complete bridge."""

    PLANNED = "planned"
    NOT_NEEDED = "not_needed"
    INSUFFICIENT = "insufficient"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ChargeWindow:
    """An explicitly permitted interval with an optional comparable price."""

    start: datetime
    end: datetime
    price: float | None = None


@dataclass(frozen=True, slots=True)
class BridgeChargePlan:
    """One charge, or a reason it cannot cover the consumption before PV.

    Times are UTC. ``required_energy_wh`` is the deficit without charging;
    ``charge_energy_wh`` is battery energy added by this charge. Consumption
    supplied directly from the grid during charging also reduces the deficit.
    ``missing_energy_wh`` includes any gap before the charge starts. An
    insufficient plan can therefore contain a useful executable partial charge,
    but does not promise uninterrupted coverage. Unavailable plans have no
    energy estimates. Unknown prices rank after explicitly supplied prices.
    """

    status: BridgeChargeStatus
    discharge_until: datetime | None = None
    start: datetime | None = None
    end: datetime | None = None
    target_soc: float | None = None
    required_energy_wh: float | None = None
    charge_energy_wh: float | None = None
    missing_energy_wh: float | None = None
    price: float | None = None
    reason: str | None = None


def _finite(value: object) -> bool:
    if not isinstance(value, int | float) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _aware(value: object) -> bool:
    return isinstance(value, datetime) and value.utcoffset() is not None


def _merged_windows(windows: Sequence[ChargeWindow]) -> list[ChargeWindow]:
    """Join artificial boundaries without extending a permitted price interval."""
    by_price: dict[float | None, list[ChargeWindow]] = {}
    for window in windows:
        by_price.setdefault(window.price, []).append(
            ChargeWindow(
                window.start.astimezone(UTC), window.end.astimezone(UTC), window.price
            )
        )
    merged: list[ChargeWindow] = []
    for group in by_price.values():
        current = sorted(group, key=lambda window: window.start)[0]
        for window in sorted(group, key=lambda window: window.start)[1:]:
            if window.start <= current.end:
                current = ChargeWindow(
                    current.start, max(current.end, window.end), current.price
                )
            else:
                merged.append(current)
                current = window
        merged.append(current)
    return merged


def plan_bridge_charge(
    *,
    now: datetime,
    pv_start: datetime,
    average_discharge_w: float,
    capacity_wh: float,
    soc: float,
    min_soc: float,
    max_soc: float,
    charge_power_w: float,
    windows: Sequence[ChargeWindow],
) -> BridgeChargePlan:
    """Choose the cheapest sufficient charge, then the latest feasible start.

    The caller supplies the measured, time-weighted average and the allowed
    tariff intervals. While charging, the grid supplies house consumption and
    the battery gains ``charge_power_w``. Otherwise it discharges at the
    measured average down to ``min_soc``. No discharge lock is assumed.

    If no single interval suffices, maximize the covered energy first, then
    prefer the cheapest and latest partial charge. No charge may exceed the
    SOC ceiling or extend beyond its interval or PV start.
    """
    unavailable = BridgeChargeStatus.UNAVAILABLE
    if not _aware(now) or not _aware(pv_start):
        return BridgeChargePlan(unavailable, reason="invalid_time")
    now = now.astimezone(UTC)
    pv_start = pv_start.astimezone(UTC)
    if pv_start <= now:
        return BridgeChargePlan(unavailable, reason="pv_start_not_future")
    values = (
        average_discharge_w,
        capacity_wh,
        soc,
        min_soc,
        max_soc,
        charge_power_w,
    )
    if not all(_finite(value) for value in values) or not (
        average_discharge_w >= 0
        and capacity_wh > 0
        and charge_power_w > 0
        and 0 <= min_soc <= max_soc <= 100
        and min_soc <= soc <= 100
    ):
        return BridgeChargePlan(unavailable, reason="invalid_battery_state")
    if not isinstance(windows, Sequence) or any(
        not isinstance(window, ChargeWindow)
        or not _aware(window.start)
        or not _aware(window.end)
        or window.start.astimezone(UTC) >= window.end.astimezone(UTC)
        or (window.price is not None and not _finite(window.price))
        for window in windows
    ):
        return BridgeChargePlan(unavailable, reason="invalid_window")

    horizon = (pv_start - now).total_seconds() / 3600
    available = capacity_wh / 100 * (soc - min_soc)
    maximum = capacity_wh / 100 * (max_soc - min_soc)
    discharge = average_discharge_w
    power = charge_power_w
    demand = discharge * horizon
    if not all(
        _finite(value) for value in (demand, available, maximum, power + discharge)
    ):
        return BridgeChargePlan(unavailable, reason="invalid_battery_state")
    required = max(demand - available, 0.0)
    discharge_until = None
    if discharge > 0:
        # The useful forecast can extend beyond PV start; datetime's finite
        # range is not a reason to reject an otherwise valid no-charge result.
        try:
            discharge_until = now + timedelta(hours=available / discharge)
        except OverflowError:
            pass
    if required <= _ENERGY_EPSILON:
        return BridgeChargePlan(
            BridgeChargeStatus.NOT_NEEDED,
            discharge_until=discharge_until,
            required_energy_wh=0.0,
            charge_energy_wh=0.0,
            missing_energy_wh=0.0,
        )

    duration_needed = required / (power + discharge)
    candidates: list[BridgeChargePlan] = []
    for window in _merged_windows(windows):
        start = max(0.0, (window.start.astimezone(UTC) - now).total_seconds() / 3600)
        end = min(horizon, (window.end.astimezone(UTC) - now).total_seconds() / 3600)
        if start >= end:
            continue
        # Capacity headroom grows until the battery reaches its SOC floor.
        # Equating that lower start bound with end-duration gives the third
        # bound. The last bound prevents buying energy unusable before PV.
        duration = min(
            duration_needed,
            end - start,
            maximum / power,
            (discharge * end + maximum - available) / (power + discharge),
            discharge * (horizon - start) / (power + discharge),
        )
        if duration <= 0:
            continue
        latest_start = min(
            end - duration,
            horizon - (power + discharge) * duration / discharge,
        )
        before_charge = max(available - discharge * latest_start, 0.0)
        charged = power * duration
        missing = max(required - (power + discharge) * duration, 0.0)
        complete = missing <= _ENERGY_EPSILON
        candidates.append(
            BridgeChargePlan(
                (
                    BridgeChargeStatus.PLANNED
                    if complete
                    else BridgeChargeStatus.INSUFFICIENT
                ),
                discharge_until=discharge_until,
                start=now + timedelta(hours=latest_start),
                end=now + timedelta(hours=latest_start + duration),
                target_soc=min(
                    max_soc, min_soc + (before_charge + charged) / capacity_wh * 100
                ),
                required_energy_wh=required,
                charge_energy_wh=charged,
                missing_energy_wh=0.0 if complete else missing,
                price=window.price,
                reason=None if complete else "window_or_capacity_insufficient",
            )
        )
    if not candidates:
        return BridgeChargePlan(
            BridgeChargeStatus.INSUFFICIENT,
            discharge_until=discharge_until,
            required_energy_wh=required,
            charge_energy_wh=0.0,
            missing_energy_wh=required,
            reason="no_usable_window",
        )
    return min(
        candidates,
        key=lambda plan: (
            plan.missing_energy_wh,
            float("inf") if plan.price is None else plan.price,
            -plan.start.timestamp(),
        ),
    )
