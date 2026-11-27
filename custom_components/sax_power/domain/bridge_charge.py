"""Tariff-independent charging to bridge consumption until PV production."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from .charge_curve import GridChargeCurve

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


@dataclass(frozen=True, slots=True)
class _ChargeBlock:
    start: float
    duration: float
    before_wh: float
    gain_wh: float


@dataclass(frozen=True, slots=True)
class _BridgeDemand:
    discharge_w: float
    available_wh: float
    maximum_wh: float
    reserve_wh: float
    required_wh: float
    minimum_wh: float
    hours_to_buffer: float
    horizon: float
    start_at_open: bool

    def fit_window(
        self,
        start: float,
        end: float,
        min_soc: float,
        max_soc: float,
        curve: GridChargeCurve,
    ) -> _ChargeBlock | None:
        """Fit one continuous charge between tariff opening and deadline."""
        discharge = self.discharge_w
        if self.minimum_wh:
            at_open_wh = max(0.0, self.available_wh - discharge * start)
            wait = curve.wait_for_minimum(
                start_soc=min_soc + at_open_wh / curve.capacity_wh * 100,
                floor_soc=min_soc,
                max_soc=max_soc,
                gain_wh=self.minimum_wh,
                discharge_w=0.0 if self.start_at_open else discharge,
                window_hours=end - start,
            )
            if wait is None:
                return None
            start += wait
        headroom_limit = self.maximum_wh
        preferred = start if self.start_at_open else max(start, self.hours_to_buffer)
        if self.start_at_open or self.reserve_wh:
            # Waiting for more headroom must not drain the requested reserve.
            before = max(0.0, self.available_wh - discharge * preferred)
            headroom = self.maximum_wh - before
            if self.start_at_open or headroom > _ENERGY_EPSILON:
                headroom_limit = headroom
        headroom_by_end = self.maximum_wh - self.available_wh + discharge * end
        if min(headroom_limit, headroom_by_end) <= 0:
            return None
        useful_wh = min(
            self.required_wh, discharge * (self.horizon - start) + self.reserve_wh
        )

        def block_at_power(power: float) -> _ChargeBlock:
            # The grid also covers the house load while the battery charges.
            combined = power + discharge
            duration = min(
                max(self.minimum_wh / power, useful_wh / combined),
                end - start,
                headroom_limit / power,
                headroom_by_end / combined,
            )
            gain = power * duration
            room_at = (
                (self.available_wh - (self.maximum_wh - gain)) / discharge
                if discharge
                else start
            )
            desired = preferred
            if not self.start_at_open and not self.reserve_wh and discharge:
                # A partial charge can wait until its energy covers the rest.
                desired = max(desired, self.horizon - combined * duration / discharge)
            latest = min(end - duration, max(room_at, desired))
            begin = min(latest, max(start, room_at, latest - _START_BUFFER_HOURS))
            return _ChargeBlock(
                begin, duration, max(self.available_wh - discharge * begin, 0.0), gain
            )

        # Moving the start changes the initial SOC and hence the mean power.
        # Balance both together so the reported energy fits the actual window.
        lower, upper = 0.0, curve.fastest_power_w
        power = upper
        for _ in range(50):
            block = block_at_power(power)
            start_soc = min_soc + block.before_wh / curve.capacity_wh * 100
            target_soc = start_soc + block.gain_wh / curve.capacity_wh * 100
            curve_hours = curve.hours_between(start_soc, target_soc)
            if math.isclose(curve_hours, block.duration, rel_tol=1e-13, abs_tol=1e-14):
                break
            if curve_hours > block.duration:
                upper = power
            else:
                lower = power
            power = lower + (upper - lower) / 2

        if block.duration <= 0 or (
            block.gain_wh < self.minimum_wh - _ENERGY_EPSILON
            and self.maximum_wh - block.before_wh - block.gain_wh > _ENERGY_EPSILON
        ):
            return None
        return block


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
    reported_soc: float | None = None,
) -> BridgeChargePlan:
    """Choose a charge and buffer its latest feasible start.

    The caller supplies the measured, time-weighted average and the allowed
    tariff intervals. While charging, the grid supplies house consumption and
    the battery follows its SOC curve up to ``charge_power_w``. Otherwise it
    discharges at the measured average down to the physical ``min_soc``.
    Aim to retain the absolute ``soc_buffer`` through PV start.

    A charge adds at least ``minimum_charge_energy_wh`` unless the SOC ceiling
    is reached first. A reported SOC of zero selects the earliest executable
    window at its opening. The more precise energy measurement ``soc`` can
    differ from the reported level. Otherwise, at equal coverage, prefer the
    SOC buffer, full minimum, price and latest start. The SOC ceiling, tariff
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
    if reported_soc is None:
        reported_soc = soc
    values = (
        average_discharge_w,
        capacity_wh,
        soc,
        reported_soc,
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
        and 0 <= reported_soc <= 100
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

    start_at_window_open = reported_soc == 0
    hours_to_buffer = max(above_buffer, 0.0) / discharge if discharge else 0.0
    curve = GridChargeCurve(capacity_wh, power)
    bridge = _BridgeDemand(
        discharge_w=discharge,
        available_wh=available,
        maximum_wh=maximum,
        reserve_wh=reserve,
        required_wh=required,
        minimum_wh=minimum_charge_energy_wh,
        hours_to_buffer=hours_to_buffer,
        horizon=horizon,
        start_at_open=start_at_window_open,
    )
    candidates: list[BridgeChargePlan] = []
    for window in _merged_windows(windows):
        start = max(0.0, (window.start.astimezone(UTC) - now).total_seconds() / 3600)
        end = min(horizon, (window.end.astimezone(UTC) - now).total_seconds() / 3600)
        if start >= end:
            continue
        block = bridge.fit_window(start, end, min_soc, max_soc, curve)
        if block is None:
            continue
        charged = block.gain_wh
        before_charge = block.before_wh
        # Surplus from the minimum charge cannot cover a gap before charging.
        missing = max(
            discharge * block.start - available,
            required - charged - discharge * block.duration,
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
                start=now + timedelta(hours=block.start),
                end=now + timedelta(hours=block.start + block.duration),
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
            plan.start if start_at_window_open else now,
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
