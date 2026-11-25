"""Daily charge permission for REQ-FIXED-TIME-GRID-CHARGE."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from datetime import time as dt_time


@dataclass(frozen=True, slots=True)
class FixedTimeChargeState:
    """Remember completion independently of subsequent changes in the SOC."""

    start: dt_time
    day: date
    completed: bool = False


def latest_charge_day(now: datetime, start: dt_time) -> date:
    """Local date of the most recent scheduled start, across both DST changes."""
    today = now.date()
    # The first fold and a forward shift over a spring gap are intentional.
    occurrence = datetime.combine(today, start, now.tzinfo).astimezone(UTC)
    return today if now.astimezone(UTC) >= occurrence else today - timedelta(days=1)


def fixed_time_charge_state(
    previous: FixedTimeChargeState | None,
    *,
    now: datetime,
    start: dt_time,
    target_reached: bool,
) -> FixedTimeChargeState | None:
    """Resume yesterday only with proof; a fresh setup never backfills it."""
    today = now.date()
    day = latest_charge_day(now, start)
    if previous is not None and (
        previous.start != start or previous.day not in (day, today)
    ):
        previous = None
    if day == today and (previous is None or previous.day != day):
        previous = FixedTimeChargeState(start, day)
    if previous is not None and previous.day == day and target_reached:
        previous = replace(previous, completed=True)
    return previous
