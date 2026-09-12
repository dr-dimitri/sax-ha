"""Translate existing permissions without changing their local-time semantics."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta, tzinfo

from ..domain.hems import TariffConstraints, TariffWindow
from ..domain.scheduling import is_time_in_window


def merge_windows(windows: tuple[TariffWindow, ...]) -> tuple[TariffWindow, ...]:
    """Preserve physical cheap-window ends independently of price or cycle cuts."""
    result: list[TariffWindow] = []
    for window in sorted(windows, key=lambda item: item.start):
        if result and window.start <= result[-1].end:
            result[-1] = TariffWindow(result[-1].start, max(result[-1].end, window.end))
        else:
            result.append(TariffWindow(window.start, window.end))
    return tuple(result)


def timed_constraints(
    now: datetime,
    *,
    start: time | None,
    end: time | None,
    months: set[int],
    time_zone: tzinfo,
    hold_until: datetime | None = None,
    completed_until: datetime | None = None,
) -> TariffConstraints:
    """REQ-HEMS-TIMED-CHARGE: current month and both DST folds stay binding."""
    now = now.astimezone(UTC)
    horizon = now + timedelta(hours=48)
    if start is None or end is None or start == end:
        return TariffConstraints(quality_reason="no_charge_window")
    # Minute cuts also expose offset jumps with no tariff boundary at the jump.
    boundaries = {now, horizon}
    cursor = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    while cursor < horizon:
        boundaries.add(cursor)
        cursor += timedelta(minutes=1)
    for offset in range(-1, 4):
        day = now.astimezone(time_zone).date() + timedelta(days=offset)
        for clock in (start, end, time()):
            for fold in (0, 1):
                boundary = datetime.combine(day, clock, time_zone).replace(fold=fold)
                instant = boundary.astimezone(UTC)
                if now < instant < horizon:
                    boundaries.add(instant)
    ordered = sorted(boundaries)
    windows = merge_windows(
        tuple(
            TariffWindow(left, right)
            for left, right in zip(ordered, ordered[1:], strict=False)
            if (local := left.astimezone(time_zone)).month in months
            and is_time_in_window(local.time(), start, end)
            and (completed_until is None or left >= completed_until)
        )
    )
    holds = (
        (TariffWindow(now, hold_until.astimezone(UTC)),)
        if hold_until is not None and now < hold_until
        else ()
    )
    return TariffConstraints(
        charge_windows=windows,
        cheap_windows=windows,
        discharge_blocked_windows=holds,
        hold_after_charge=True,
        quality_reason=None if windows else "no_charge_window",
    )
