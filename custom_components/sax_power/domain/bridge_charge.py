"""Tariff-independent charging to bridge consumption until PV production."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

_ENERGY_EPSILON = 1e-6
_START_BUFFER_HOURS = 10 / 60
DEFAULT_MIN_BRIDGE_CHARGE_ENERGY_WH = 1000


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

    Times are UTC. ``required_energy_wh`` includes the reserve due at PV start.
    ``charge_energy_wh`` is battery energy added by this charge. Consumption
    supplied directly from the grid during charging also reduces the deficit.
    ``missing_energy_wh`` includes any gap before the charge starts. An
    insufficient plan can therefore contain a useful executable partial charge,
    but does not promise uninterrupted coverage. Unavailable plans have no
    energy estimates. Unknown prices rank after explicitly supplied prices.
    ``latest_end`` is the hard deadline for reaching the minimum SOC gain.
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
    latest_end: datetime | None = None
    minimum_target_soc: float | None = None


def _finite(value: object) -> bool:
    if not isinstance(value, int | float) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _aware(value: object) -> bool:
    return isinstance(value, datetime) and value.utcoffset() is not None


def energy_above_buffer_wh(
    capacity_wh: float, soc: float, min_soc: float, soc_buffer: float
) -> float:
    """A negative balance is energy needed to restore the requested reserve."""
    return capacity_wh / 100 * (soc - max(min_soc, soc_buffer))


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
    minimum_charge_energy_wh: float = DEFAULT_MIN_BRIDGE_CHARGE_ENERGY_WH,
    soc_buffer: float = 0,
) -> BridgeChargePlan:
    """Choose a charge and buffer its latest feasible start.

    The caller supplies the measured, time-weighted average and the allowed
    tariff intervals. While charging, the grid supplies house consumption and
    the battery gains ``charge_power_w``. Otherwise it discharges at the
    measured average down to the physical ``min_soc``. Aim to retain the
    absolute ``soc_buffer`` through PV start. No discharge lock is assumed.

    A charge adds at least ``minimum_charge_energy_wh`` unless the SOC ceiling
    is reached first. At equal coverage, prefer preserving the SOC buffer,
    then the full minimum, price and latest start. The SOC ceiling, tariff
    interval and PV start bound every charge.
    """
    unavailable = BridgeChargeStatus.UNAVAILABLE
    if not _aware(now) or not _aware(pv_start):
        return BridgeChargePlan(unavailable, reason="invalid_time")
    now = now.astimezone(UTC)
    pv_start = pv_start.astimezone(UTC)
    if pv_start <= now:
        return BridgeChargePlan(unavailable, reason="pv_start_not_future")
    if not _finite(minimum_charge_energy_wh) or minimum_charge_energy_wh < 0:
        return BridgeChargePlan(unavailable, reason="invalid_minimum_charge_energy")
    values = (
        average_discharge_w,
        capacity_wh,
        soc,
        min_soc,
        max_soc,
        soc_buffer,
        charge_power_w,
    )
    if not all(_finite(value) for value in values) or not (
        average_discharge_w >= 0
        and capacity_wh > 0
        and charge_power_w > 0
        and 0 <= min_soc <= max_soc <= 100
        and min_soc <= soc <= 100
        and 0 <= soc_buffer <= 100
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
    above_buffer = energy_above_buffer_wh(capacity_wh, soc, min_soc, soc_buffer)
    reserve = capacity_wh / 100 * max(0.0, soc_buffer - min_soc)
    maximum = capacity_wh / 100 * (max_soc - min_soc)
    discharge = average_discharge_w
    power = charge_power_w
    demand = discharge * horizon
    required = max(demand - above_buffer, 0.0)
    if not all(
        _finite(value) for value in (required, available, maximum, power + discharge)
    ):
        return BridgeChargePlan(unavailable, reason="invalid_battery_state")
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
    minimum_duration = minimum_charge_energy_wh / power
    hours_to_buffer = max(above_buffer, 0.0) / discharge if discharge else 0.0
    candidates: list[BridgeChargePlan] = []
    for window in _merged_windows(windows):
        start = max(0.0, (window.start.astimezone(UTC) - now).total_seconds() / 3600)
        end = min(horizon, (window.end.astimezone(UTC) - now).total_seconds() / 3600)
        if start >= end:
            continue
        # Headroom grows until the battery reaches its SOC floor. Equating
        # that lower start bound with end-duration gives the second limit.
        capacity_limit = min(
            maximum / power,
            (discharge * end + maximum - available) / (power + discharge),
        )
        if reserve:
            # Waiting for extra headroom could drain the very reserve this
            # charge should protect. A late tariff opens at the actual SOC.
            energy_at_buffer_start = max(
                0.0, available - discharge * max(start, hours_to_buffer)
            )
            headroom = maximum - energy_at_buffer_start
            if headroom > _ENERGY_EPSILON:
                capacity_limit = min(capacity_limit, headroom / power)
        time_limit = end - start
        if (
            power * time_limit < minimum_charge_energy_wh - _ENERGY_EPSILON
            and power * (capacity_limit - time_limit) > _ENERGY_EPSILON
        ):
            continue
        useful_duration = (discharge * (horizon - start) + reserve) / (
            power + discharge
        )
        duration = min(
            max(minimum_duration, min(duration_needed, useful_duration)),
            time_limit,
            capacity_limit,
        )
        if duration <= 0:
            continue
        charged = power * duration
        headroom_start = (
            (available - (maximum - charged)) / discharge if discharge else 0.0
        )
        preferred_start = hours_to_buffer
        if not reserve and discharge:
            # Without a reserve, a partial charge can wait until its energy
            # just covers the remaining consumption before PV starts.
            preferred_start = max(
                preferred_start, horizon - (power + discharge) * duration / discharge
            )
        latest_start = min(end - duration, max(start, headroom_start, preferred_start))
        buffered_start = min(
            latest_start,
            max(start, headroom_start, latest_start - _START_BUFFER_HOURS),
        )
        demand_before = discharge * buffered_start
        before_charge = max(available - demand_before, 0.0)
        # Surplus from the minimum charge cannot cover a gap before charging.
        missing = max(
            demand_before - available,
            required - (power + discharge) * duration,
            0.0,
        )
        complete = missing <= _ENERGY_EPSILON
        target_soc = min(
            max_soc, min_soc + (before_charge + charged) / capacity_wh * 100
        )
        candidates.append(
            BridgeChargePlan(
                (
                    BridgeChargeStatus.PLANNED
                    if complete
                    else BridgeChargeStatus.INSUFFICIENT
                ),
                discharge_until=discharge_until,
                start=now + timedelta(hours=buffered_start),
                end=now + timedelta(hours=buffered_start + duration),
                target_soc=target_soc,
                required_energy_wh=required,
                charge_energy_wh=charged,
                missing_energy_wh=0.0 if complete else missing,
                price=window.price,
                reason=None if complete else "window_or_capacity_insufficient",
                latest_end=min(pv_start, window.end),
                minimum_target_soc=(
                    min(
                        target_soc,
                        min_soc
                        + (before_charge + minimum_charge_energy_wh)
                        / capacity_wh
                        * 100,
                    )
                    if minimum_charge_energy_wh
                    else None
                ),
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
            (
                max(0.0, (plan.start - now).total_seconds() - hours_to_buffer * 3600)
                if reserve
                else 0.0
            ),
            plan.charge_energy_wh < minimum_charge_energy_wh - _ENERGY_EPSILON,
            float("inf") if plan.price is None else plan.price,
            -plan.start.timestamp(),
        ),
    )
