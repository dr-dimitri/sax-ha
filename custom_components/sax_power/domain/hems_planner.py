"""Chronological, tariff-independent night bridge (REQ-HEMS-ENERGY-PLANNER)."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from .hems import (
    ChargeInterval,
    EnergyPlan,
    EnergyPoint,
    EnergySlot,
    PlanningSnapshot,
    PlanStatus,
    TariffWindow,
)

_EPS = 1e-9
_LEASE = timedelta(minutes=10)
_HORIZON = timedelta(hours=48)
_PV_CONFIRMATION = timedelta(hours=1)
_START_SNAP_SECONDS = 0.001


def _finite(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, int | float)
        and math.isfinite(value)
    )


def _aware(value: object) -> bool:
    return isinstance(value, datetime) and value.utcoffset() is not None


def _utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


def _valid_slots(slots: tuple[EnergySlot, ...]) -> bool:
    previous_end: datetime | None = None
    for slot in slots:
        if (
            not _aware(slot.start)
            or not _aware(slot.end)
            or _utc(slot.end) <= _utc(slot.start)
            or not _finite(slot.energy_kwh)
            or slot.energy_kwh < 0
            or (previous_end is not None and _utc(slot.start) < previous_end)
        ):
            return False
        previous_end = _utc(slot.end)
    return True


def _valid_windows(windows: tuple[TariffWindow, ...]) -> bool:
    previous_end: datetime | None = None
    for window in windows:
        if (
            not _aware(window.start)
            or not _aware(window.end)
            or _utc(window.end) <= _utc(window.start)
            or (window.price_eur_kwh is not None and not _finite(window.price_eur_kwh))
            or (previous_end is not None and _utc(window.start) < previous_end)
        ):
            return False
        previous_end = _utc(window.end)
    return True


def _covering(
    slots: tuple[EnergySlot, ...], start: datetime, end: datetime
) -> EnergySlot | None:
    return next(
        (slot for slot in slots if _utc(slot.start) <= start and end <= _utc(slot.end)),
        None,
    )


def _power(slot: EnergySlot) -> float:
    return slot.energy_kwh * 3600 / (_utc(slot.end) - _utc(slot.start)).total_seconds()


def _window_at(
    windows: tuple[TariffWindow, ...], start: datetime, end: datetime
) -> TariffWindow | None:
    return next(
        (
            window
            for window in windows
            if _utc(window.start) <= start and end <= _utc(window.end)
        ),
        None,
    )


def _result(
    snapshot: PlanningSnapshot,
    status: PlanStatus,
    reasons: tuple[str, ...],
    **values: object,
) -> EnergyPlan:
    now = (
        _utc(snapshot.as_of)
        if _aware(snapshot.as_of)
        else datetime.min.replace(tzinfo=UTC)
    )
    deadline = now + _LEASE
    for value in (snapshot.pv.valid_until, snapshot.load.model_end):
        if _aware(value) and _utc(value) > now:
            deadline = min(deadline, _utc(value))
    if _aware(snapshot.load.evaluated_through):
        freshness_end = _utc(snapshot.load.evaluated_through) + timedelta(minutes=15)
        if freshness_end > now:
            deadline = min(deadline, freshness_end)
    for windows in (
        snapshot.tariff.charge_windows,
        snapshot.tariff.cheap_windows,
        snapshot.tariff.discharge_blocked_windows,
    ):
        for window in windows:
            for boundary in (window.start, window.end):
                if _aware(boundary) and _utc(boundary) > now:
                    deadline = min(deadline, _utc(boundary))
    identity = hashlib.sha256(
        repr((snapshot, status, reasons, values)).encode()
    ).hexdigest()[:20]
    return EnergyPlan(
        decision_id=identity,
        revision=snapshot.revision,
        evaluated_at=now,
        valid_until=deadline,
        status=status,
        reason_codes=reasons,
        load_basis=snapshot.load.basis,
        quality_flags=tuple(
            dict.fromkeys(snapshot.load.quality_flags + snapshot.pv.quality_flags)
        ),
        **values,
    )


def _safety_reason(snapshot: PlanningSnapshot) -> str | None:
    if not _aware(snapshot.as_of):
        return "invalid_planning_time"
    if not snapshot.device_available:
        return "device_unavailable"
    if (
        not _finite(snapshot.current_soc)
        or not 0 <= snapshot.current_soc <= 100
        or not _aware(snapshot.soc_measured_at)
        or not _finite(snapshot.max_soc_age_seconds)
        or snapshot.max_soc_age_seconds <= 0
        or not 0
        <= (_utc(snapshot.as_of) - _utc(snapshot.soc_measured_at)).total_seconds()
        <= snapshot.max_soc_age_seconds
    ):
        return "soc_unavailable"
    if not _finite(snapshot.capacity_kwh) or snapshot.capacity_kwh <= 0:
        return "capacity_unavailable"
    if not _finite(snapshot.charge_power_w) or snapshot.charge_power_w <= 0:
        return "charge_power_unavailable"
    if snapshot.discharge_power_w is not None and (
        not _finite(snapshot.discharge_power_w) or snapshot.discharge_power_w <= 0
    ):
        return "discharge_power_unavailable"
    if any(
        not _finite(value) or not 0 < value <= 1
        for value in (snapshot.eta_charge, snapshot.eta_discharge)
    ):
        return "invalid_efficiency"
    if (
        any(
            not _finite(value) or not 0 <= value <= 100
            for value in (
                snapshot.reserve_soc,
                snapshot.max_soc,
                snapshot.physical_min_soc,
            )
        )
        or max(snapshot.reserve_soc, snapshot.physical_min_soc) > snapshot.max_soc
    ):
        return "invalid_soc_limits"
    return None


@dataclass(frozen=True, slots=True)
class _Cell:
    start: datetime
    end: datetime
    load_kw: float
    pv_kw: float
    window: TariffWindow | None
    cheap: bool
    blocked: bool

    @property
    def hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600


def _cells(snapshot: PlanningSnapshot) -> tuple[list[_Cell], str | None]:
    now = _utc(snapshot.as_of)
    end = min(_utc(snapshot.load.model_end), now + _HORIZON)
    boundaries = {now, end}
    for slots in (
        snapshot.load.intervals,
        snapshot.pv.intervals,
        snapshot.tariff.charge_windows,
        snapshot.tariff.cheap_windows,
        snapshot.tariff.discharge_blocked_windows,
    ):
        for slot in slots:
            boundaries.update(
                _utc(value)
                for value in (slot.start, slot.end)
                if now < _utc(value) < end
            )
    boundary = now
    while boundary < end:
        boundaries.add(boundary)
        boundary += timedelta(minutes=15)
    ordered = sorted(boundaries)
    cells: list[_Cell] = []
    for start, finish in zip(ordered, ordered[1:], strict=False):
        load = _covering(snapshot.load.intervals, start, finish)
        pv = _covering(snapshot.pv.intervals, start, finish)
        if load is None or pv is None:
            # Later gaps cannot invalidate an already fully evidenced supply.
            return cells, (
                "load_coverage_missing" if load is None else "pv_coverage_missing"
            )
        if not _finite(_power(load)) or not _finite(_power(pv)):
            return cells, "invalid_forecast_power"
        cells.append(
            _Cell(
                start,
                finish,
                _power(load),
                _power(pv),
                _window_at(snapshot.tariff.charge_windows, start, finish),
                _window_at(snapshot.tariff.cheap_windows, start, finish) is not None,
                _window_at(snapshot.tariff.discharge_blocked_windows, start, finish)
                is not None,
            )
        )
    return cells, None


def _pv_supply(cells: list[_Cell]) -> datetime | None:
    beginning: datetime | None = None
    for cell in cells:
        if cell.pv_kw > 0 and cell.pv_kw + _EPS >= cell.load_kw:
            if beginning is None:
                beginning = cell.start
            if cell.end - beginning >= _PV_CONFIRMATION:
                return beginning
        else:
            beginning = None
    return None


def compute_energy_plan(snapshot: PlanningSnapshot) -> EnergyPlan:
    """Return the least required grid energy, then the cheapest feasible plan.

    Safety is checked before data fallback. Source quality is owned by the
    adapters; this boundary independently validates units, time and coverage.
    """
    if reason := _safety_reason(snapshot):
        return _result(snapshot, PlanStatus.BLOCKED, (reason,))
    now = _utc(snapshot.as_of)
    if snapshot.load.quality_reason == "outside_model_scope":
        return _result(snapshot, PlanStatus.INACTIVE, ("outside_model_scope",))
    if not _aware(snapshot.load.model_start) or not _aware(snapshot.load.model_end):
        return _result(
            snapshot,
            PlanStatus.FALLBACK,
            (snapshot.load.quality_reason or "night_geometry_unavailable",),
        )
    if not _utc(snapshot.load.model_start) <= now < _utc(snapshot.load.model_end):
        return _result(snapshot, PlanStatus.INACTIVE, ("outside_model_scope",))
    if snapshot.load.quality_reason or snapshot.pv.quality_reason:
        return _result(
            snapshot,
            PlanStatus.FALLBACK,
            tuple(
                reason
                for reason in (snapshot.load.quality_reason, snapshot.pv.quality_reason)
                if reason
            ),
        )
    if snapshot.load.basis != "battery_discharge_night":
        return _result(snapshot, PlanStatus.FALLBACK, ("unsupported_load_basis",))
    if (
        not _aware(snapshot.load.evaluated_through)
        or not 0 <= (now - _utc(snapshot.load.evaluated_through)).total_seconds() <= 900
    ):
        return _result(snapshot, PlanStatus.FALLBACK, ("history_stale",))
    if not _aware(snapshot.pv.valid_until) or now >= _utc(snapshot.pv.valid_until):
        return _result(snapshot, PlanStatus.FALLBACK, ("pv_stale",))
    if not _valid_slots(snapshot.load.intervals) or not _valid_slots(
        snapshot.pv.intervals
    ):
        return _result(snapshot, PlanStatus.FALLBACK, ("invalid_forecast_intervals",))
    if snapshot.tariff.quality_reason:
        return _result(snapshot, PlanStatus.BLOCKED, (snapshot.tariff.quality_reason,))
    if any(
        not _valid_windows(windows)
        for windows in (
            snapshot.tariff.charge_windows,
            snapshot.tariff.cheap_windows,
            snapshot.tariff.discharge_blocked_windows,
        )
    ) or (
        snapshot.tariff.max_charge_seconds is not None
        and (
            not _finite(snapshot.tariff.max_charge_seconds)
            or snapshot.tariff.max_charge_seconds < 0
        )
    ):
        return _result(snapshot, PlanStatus.BLOCKED, ("invalid_tariff_constraints",))
    cells, coverage_reason = _cells(snapshot)
    supply = _pv_supply(cells)
    if supply is None:
        return _result(
            snapshot,
            PlanStatus.FALLBACK,
            (coverage_reason or "pv_supply_unconfirmed",),
        )
    assert snapshot.capacity_kwh is not None and snapshot.current_soc is not None
    reserve_soc = max(snapshot.reserve_soc, snapshot.physical_min_soc)
    reserve = snapshot.capacity_kwh * reserve_soc / 100
    available = max(snapshot.capacity_kwh * snapshot.current_soc / 100 - reserve, 0)
    window = next(
        (
            item
            for item in snapshot.tariff.cheap_windows
            if _utc(item.start) <= now < supply < _utc(item.end)
        ),
        None,
    )
    if snapshot.current_soc <= reserve_soc and window:
        return _result(
            snapshot,
            PlanStatus.NO_NEED,
            ("waiting_for_pv_in_cheap_window",),
            pv_supply_at=supply,
            required_grid_kwh=0.0,
            planned_grid_kwh=0.0,
            unmet_grid_kwh=0.0,
            reserve_kwh=reserve,
            available_battery_kwh=available * snapshot.eta_discharge,
            target_soc=min(snapshot.current_soc, snapshot.max_soc),
            expected_load_kwh=sum(
                c.load_kw * c.hours for c in cells if c.end <= supply
            ),
            pv_used_kwh=sum(
                min(c.load_kw, c.pv_kw) * c.hours for c in cells if c.end <= supply
            ),
        )
    bridge = [cell for cell in cells if cell.end <= supply]
    return _plan_bridge(snapshot, bridge, supply)


class _LinearProgram:
    """Small deterministic two-phase simplex, with bounded nonnegative inputs.

    This solves the time-expanded storage constraints without introducing a
    runtime optimization dependency. A pivot limit fails closed.
    """

    def __init__(
        self, rows: list[list[float]], bounds: list[float], costs: list[float]
    ) -> None:
        self.m, self.n = len(bounds), len(costs)
        m, n = self.m, self.n
        self.basis = [n + i for i in range(m)]
        self.nonbasis = [*range(n), -1]
        self.table = [[0.0] * (n + 2) for _ in range(m + 2)]
        for index, (row, bound) in enumerate(zip(rows, bounds, strict=True)):
            self.table[index][:n] = row
            self.table[index][n] = -1.0
            self.table[index][n + 1] = bound
        self.table[m][:n] = costs
        self.table[m + 1][n] = 1.0
        self.pivots = 0

    def _pivot(self, row: int, column: int) -> None:
        self.pivots += 1
        if self.pivots > 10000:
            raise ArithmeticError("hems_solver_iteration_limit")
        table = self.table
        pivot = table[row]
        inverse = 1.0 / pivot[column]
        for i, target in enumerate(table):
            if i == row:
                continue
            factor = target[column] * inverse
            if abs(factor) > 1e-15:
                for j in range(self.n + 2):
                    if j != column:
                        target[j] -= pivot[j] * factor
            target[column] *= -inverse
        for j in range(self.n + 2):
            if j != column:
                pivot[j] *= inverse
        pivot[column] = inverse
        self.basis[row], self.nonbasis[column] = self.nonbasis[column], self.basis[row]

    def _simplex(self, phase: int) -> bool:
        objective = self.m + 1 if phase == 1 else self.m
        while True:
            candidates = [
                j
                for j in range(self.n + 1)
                if not (phase == 2 and self.nonbasis[j] == -1)
            ]
            column = min(
                candidates, key=lambda j: (self.table[objective][j], self.nonbasis[j])
            )
            if self.table[objective][column] >= -_EPS:
                return True
            rows = [i for i in range(self.m) if self.table[i][column] > _EPS]
            if not rows:
                return False
            row = min(
                rows,
                key=lambda i: (
                    self.table[i][self.n + 1] / self.table[i][column],
                    self.basis[i],
                ),
            )
            self._pivot(row, column)

    def solve(self) -> list[float] | None:
        row = min(range(self.m), key=lambda i: self.table[i][self.n + 1])
        if self.table[row][self.n + 1] < -_EPS:
            self._pivot(row, self.n)
            if not self._simplex(1) or abs(self.table[self.m + 1][self.n + 1]) > _EPS:
                return None
            if -1 in self.basis:
                row = self.basis.index(-1)
                columns = [
                    j for j in range(self.n + 1) if abs(self.table[row][j]) > _EPS
                ]
                if columns:
                    self._pivot(row, min(columns, key=lambda j: self.nonbasis[j]))
        if not self._simplex(2):
            return None
        result = [0.0] * self.n
        for i, basic in enumerate(self.basis):
            if basic < self.n and basic >= 0:
                result[basic] = max(0.0, self.table[i][self.n + 1])
        return result


@dataclass(frozen=True, slots=True)
class _Solution:
    grid: tuple[float, ...]
    missed: float
    terminal_shortfall: float


def _solve_bridge(snapshot: PlanningSnapshot, cells: list[_Cell]) -> _Solution | None:
    """Minimize shortfall, grid kWh, then price, under chronological bounds."""
    assert snapshot.capacity_kwh is not None and snapshot.current_soc is not None
    assert snapshot.charge_power_w is not None
    charge_kw = snapshot.charge_power_w / 1000
    capacity = snapshot.capacity_kwh * snapshot.max_soc / 100
    stored = snapshot.capacity_kwh * snapshot.current_soc / 100
    physical = min(stored, snapshot.capacity_kwh * snapshot.physical_min_soc / 100)
    initial = stored - physical
    capacity = max(0.0, capacity - physical)
    reserve = (
        snapshot.capacity_kwh
        * max(snapshot.reserve_soc, snapshot.physical_min_soc)
        / 100
        - physical
    )
    count = len(cells)
    # Per-cell variables: battery grid energy, unserved DC demand, PV spill;
    # the final variable is an unmet terminal reserve, never fictional energy.
    size = 3 * count + 1
    rows: list[list[float]] = []
    bounds: list[float] = []
    shortage_cost = [0.0] * size
    grid_cost = [0.0] * size
    price_cost = [0.0] * size
    time_cost = [0.0] * size
    cumulative = [0.0] * size
    base = initial
    natural = initial
    free_decline = 0.0

    def constrain(coefficients: list[float], limit: float) -> None:
        rows.append(coefficients)
        bounds.append(limit)

    def bound(index: int, maximum: float) -> None:
        row = [0.0] * size
        row[index] = 1.0
        constrain(row, max(0.0, maximum))

    for i, cell in enumerate(cells):
        grid, missing, spill = 3 * i, 3 * i + 1, 3 * i + 2
        residual_kw = max(0.0, cell.load_kw - cell.pv_kw)
        demand = (
            0.0 if cell.blocked else residual_kw * cell.hours / snapshot.eta_discharge
        )
        pv_gain = max(0.0, cell.pv_kw - cell.load_kw) * cell.hours * snapshot.eta_charge
        # Do not request grid charging in a forecast PV-surplus interval.
        maximum = (
            min(charge_kw * cell.hours, capacity / snapshot.eta_charge)
            if cell.window and cell.pv_kw <= cell.load_kw
            else 0.0
        )
        bound(grid, maximum)
        bound(spill, pv_gain)
        natural_shortfall = max(0.0, demand - natural)
        natural = min(max(capacity, natural), max(0.0, natural + pv_gain - demand))
        # Empty batteries may buy house power directly in cheap windows;
        # no unobserved discharge hold is assumed for remaining energy.
        free_shortfall = natural_shortfall if cell.cheap else 0.0
        bound(missing, demand)
        shortage_cost[missing] = 1.0
        if free_shortfall:
            # A fixed no-charge shortage is outside the bridge to be stored.
            demand -= free_shortfall
        avoided = demand / (charge_kw * cell.hours)
        if snapshot.discharge_power_w is not None and not cell.blocked:
            unavoidable = (
                max(0.0, residual_kw - snapshot.discharge_power_w / 1000)
                * cell.hours
                / snapshot.eta_discharge
            )
            row = [0.0] * size
            row[missing] = -1.0
            row[grid] = -unavoidable / (charge_kw * cell.hours)
            constrain(row, -max(0.0, unavoidable - free_shortfall))
        row = [0.0] * size
        row[missing] = 1.0
        row[grid] = avoided
        constrain(row, demand)
        cumulative[grid] = snapshot.eta_charge + avoided
        cumulative[missing] = 1.0
        cumulative[spill] = -1.0
        base += pv_gain - demand
        free_decline += demand
        constrain(cumulative.copy(), max(capacity, initial - free_decline) - base)
        constrain([-value for value in cumulative], base)
        grid_cost[grid] = 1.0
        price_cost[grid] = cell.window.price_eur_kwh or 0.0 if cell.window else 0.0
        # Prefer late contiguous portions when price is exactly equal.
        time_cost[grid] = float(count - i)
    reserve_shortfall = size - 1
    shortage_cost[reserve_shortfall] = 1.0
    bound(reserve_shortfall, reserve)
    terminal = [-value for value in cumulative]
    terminal[reserve_shortfall] = -1.0
    constrain(terminal, base - reserve)
    if snapshot.tariff.max_charge_seconds is not None:
        constrain(
            grid_cost.copy(), charge_kw * snapshot.tariff.max_charge_seconds / 3600
        )
    solution: list[float] | None = None
    try:
        for costs in (shortage_cost, grid_cost, price_cost, time_cost):
            solution = _LinearProgram(rows, bounds, costs).solve()
            if solution is None:
                return None
            optimum = sum(
                cost * value for cost, value in zip(costs, solution, strict=True)
            )
            constrain(costs.copy(), optimum + _EPS)
    except ArithmeticError, OverflowError:
        return None
    assert solution is not None
    return _Solution(
        tuple(solution[3 * i] for i in range(count)),
        sum(solution[3 * i + 1] for i in range(count)),
        solution[-1],
    )


def _plan_bridge(
    snapshot: PlanningSnapshot, cells: list[_Cell], supply: datetime
) -> EnergyPlan:
    assert snapshot.capacity_kwh is not None and snapshot.current_soc is not None
    assert snapshot.charge_power_w is not None
    if not cells:
        return _result(
            snapshot,
            PlanStatus.NO_NEED,
            ("pv_supplies_load",),
            pv_supply_at=supply,
            required_grid_kwh=0.0,
            planned_grid_kwh=0.0,
            unmet_grid_kwh=0.0,
            target_soc=min(snapshot.current_soc, snapshot.max_soc),
            reserve_kwh=snapshot.capacity_kwh
            * max(snapshot.reserve_soc, snapshot.physical_min_soc)
            / 100,
            available_battery_kwh=max(
                0.0,
                snapshot.capacity_kwh
                * (
                    snapshot.current_soc
                    - max(snapshot.reserve_soc, snapshot.physical_min_soc)
                )
                / 100,
            )
            * snapshot.eta_discharge,
            expected_load_kwh=0.0,
            pv_used_kwh=0.0,
        )
    cells = _split_depletion(snapshot, cells)
    solution = _solve_bridge(snapshot, cells)
    if solution is None:
        return _result(
            snapshot,
            PlanStatus.BLOCKED,
            ("planning_solver_failed",),
            pv_supply_at=supply,
        )
    if snapshot.tariff.hold_after_charge and any(
        value > 1e-7 for value in solution.grid
    ):
        held: list[_Cell] = []
        hold_until: datetime | None = None
        for cell, grid in zip(cells, solution.grid, strict=True):
            already_held = hold_until is not None and cell.start < hold_until
            held.append(replace(cell, blocked=cell.blocked or already_held))
            if grid > 1e-7:
                window = _window_at(snapshot.tariff.cheap_windows, cell.start, cell.end)
                if window is not None:
                    hold_until = _utc(window.end)
        revised = _solve_bridge(snapshot, held)
        # REQ-HEMS-ENERGY-PLANNER: never manufacture a tiny command merely
        # to obtain the timed discharge hold. Zero need retains normal mode.
        consistent_hold = False
        if revised is not None:
            expected_until: datetime | None = None
            consistent_hold = True
            for original, proposed, grid in zip(cells, held, revised.grid, strict=True):
                expected_blocked = original.blocked or (
                    expected_until is not None and original.start < expected_until
                )
                if proposed.blocked != expected_blocked:
                    consistent_hold = False
                    break
                if grid > 1e-7:
                    window = _window_at(
                        snapshot.tariff.cheap_windows, original.start, original.end
                    )
                    if window is not None:
                        expected_until = _utc(window.end)
        if revised is not None and consistent_hold and sum(revised.grid) > 1e-7:
            cells, solution = held, revised
    charge_kw = snapshot.charge_power_w / 1000
    stored = snapshot.capacity_kwh * snapshot.current_soc / 100
    physical_floor = snapshot.capacity_kwh * snapshot.physical_min_soc / 100
    floor = min(stored, physical_floor)
    ceiling = snapshot.capacity_kwh * snapshot.max_soc / 100
    trajectory = [EnergyPoint(_utc(snapshot.as_of), stored)]
    intervals: list[ChargeInterval] = []
    maximum_charge_end = 0.0
    stored_pv_ac = 0.0
    missed_trace_dc = 0.0
    for cell, energy in zip(cells, solution.grid, strict=True):
        demand_kw = (
            0.0
            if cell.blocked
            else max(0.0, cell.load_kw - cell.pv_kw) / snapshot.eta_discharge
        )
        pv_kw = max(0.0, cell.pv_kw - cell.load_kw) * snapshot.eta_charge
        if energy > 1e-7:
            duration_hours = min(cell.hours, energy / charge_kw)
            wait_hours = cell.hours - duration_hours
            if demand_kw > 0 and not cell.cheap:
                wait_hours = min(wait_hours, max(0.0, stored - floor) / demand_kw)
            # LP tolerance can leave a microsecond of fictional waiting at
            # every replan. A cell starts no earlier than as_of and all real
            # source/tariff boundaries, so snapping here preserves permission.
            if wait_hours * 3600 < _START_SNAP_SECONDS:
                wait_hours = 0.0
            start = cell.start + timedelta(hours=max(0.0, wait_hours))
            end = min(cell.end, start + timedelta(hours=duration_hours))
            if not cell.cheap:
                missed_trace_dc += max(0.0, floor - stored + demand_kw * wait_hours)
            stored = max(floor, stored - demand_kw * wait_hours)
            stored = min(ceiling, stored + energy * snapshot.eta_charge)
            floor = min(stored, physical_floor)
            maximum_charge_end = max(maximum_charge_end, stored)
            trajectory.append(EnergyPoint(end, stored))
            intervals.append(
                ChargeInterval(
                    start,
                    end,
                    energy,
                    cell.window.price_eur_kwh if cell.window else None,
                )
            )
            remaining_demand = demand_kw * max(
                0.0, cell.hours - wait_hours - duration_hours
            )
            if not cell.cheap:
                missed_trace_dc += max(0.0, floor - stored + remaining_demand)
            stored = max(floor, stored - remaining_demand)
        else:
            before_pv = stored
            if not cell.cheap:
                missed_trace_dc += max(
                    0.0, floor - stored + (demand_kw - pv_kw) * cell.hours
                )
            stored = max(
                floor,
                min(max(ceiling, stored), stored + (pv_kw - demand_kw) * cell.hours),
            )
            if pv_kw > 0:
                stored_pv_ac += max(0.0, stored - before_pv) / snapshot.eta_charge
            floor = min(stored, physical_floor)
        trajectory.append(EnergyPoint(cell.end, stored))
    planned = sum(item.energy_kwh for item in intervals)
    unmet = (
        max(0.0, solution.missed + solution.terminal_shortfall) / snapshot.eta_charge
    )
    terminal_reserve = (
        snapshot.capacity_kwh
        * max(snapshot.reserve_soc, snapshot.physical_min_soc)
        / 100
    )
    unmet = max(
        unmet,
        (missed_trace_dc + max(0.0, terminal_reserve - stored)) / snapshot.eta_charge,
    )
    if unmet < 1e-7:
        unmet = 0.0
    status = (
        PlanStatus.LIMITED
        if unmet
        else PlanStatus.PLANNED if planned > 1e-7 else PlanStatus.NO_NEED
    )
    reason = (
        "unmet_need"
        if unmet
        else "night_bridge_required" if planned > 1e-7 else "battery_covers_bridge"
    )
    merged: list[ChargeInterval] = []
    for interval in intervals:
        if (
            merged
            and abs((merged[-1].end - interval.start).total_seconds()) < 1e-5
            and merged[-1].price_eur_kwh == interval.price_eur_kwh
            and (
                merged[-1].end >= interval.start
                or _window_at(
                    snapshot.tariff.charge_windows, merged[-1].end, interval.start
                )
                is not None
            )
        ):
            previous = merged.pop()
            merged.append(
                replace(
                    previous,
                    end=interval.end,
                    energy_kwh=previous.energy_kwh + interval.energy_kwh,
                )
            )
        else:
            merged.append(interval)
    return _result(
        snapshot,
        status,
        (reason,),
        intervals=tuple(merged),
        pv_supply_at=supply,
        required_grid_kwh=planned + unmet,
        planned_grid_kwh=planned,
        unmet_grid_kwh=unmet,
        available_battery_kwh=max(
            0.0,
            snapshot.capacity_kwh
            * (
                snapshot.current_soc
                - max(snapshot.reserve_soc, snapshot.physical_min_soc)
            )
            / 100,
        )
        * snapshot.eta_discharge,
        reserve_kwh=snapshot.capacity_kwh
        * max(snapshot.reserve_soc, snapshot.physical_min_soc)
        / 100,
        target_soc=(
            min(snapshot.max_soc, maximum_charge_end / snapshot.capacity_kwh * 100)
            if intervals
            else min(snapshot.max_soc, snapshot.current_soc)
        ),
        expected_load_kwh=sum(cell.load_kw * cell.hours for cell in cells),
        pv_used_kwh=stored_pv_ac
        + sum(min(cell.load_kw, cell.pv_kw) * cell.hours for cell in cells),
        trajectory=tuple(trajectory),
    )


def _split_depletion(snapshot: PlanningSnapshot, cells: list[_Cell]) -> list[_Cell]:
    """Separate observed stock from later direct import in a cheap window."""
    assert snapshot.capacity_kwh is not None and snapshot.current_soc is not None
    stored = (
        snapshot.capacity_kwh
        * max(0.0, snapshot.current_soc - snapshot.physical_min_soc)
        / 100
    )
    capacity = (
        snapshot.capacity_kwh
        * max(0.0, snapshot.max_soc - snapshot.physical_min_soc)
        / 100
    )
    result: list[_Cell] = []
    for cell in cells:
        drain = (
            0.0
            if cell.blocked
            else max(0.0, cell.load_kw - cell.pv_kw) / snapshot.eta_discharge
        )
        if cell.cheap and drain > 0 and _EPS < stored < drain * cell.hours - _EPS:
            boundary = cell.start + timedelta(hours=stored / drain)
            if cell.start < boundary < cell.end:
                result.extend(
                    (replace(cell, end=boundary), replace(cell, start=boundary))
                )
            else:
                result.append(cell)
        else:
            result.append(cell)
        surplus = max(0.0, cell.pv_kw - cell.load_kw) * snapshot.eta_charge
        stored = min(
            max(capacity, stored), max(0.0, stored + (surplus - drain) * cell.hours)
        )
    return result
