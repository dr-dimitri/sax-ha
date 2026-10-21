"""Daily charge permission for REQ-FIXED-TIME-GRID-CHARGE."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from datetime import time as dt_time


@dataclass(frozen=True, slots=True)
class FixedTimeChargeState:
    """Remember completion independently of subsequent changes in the SOC."""

    start: dt_time
    day: date
    completed: bool = False


def fixed_time_charge_state(
    previous: FixedTimeChargeState | None,
    *,
    now: datetime,
    start: dt_time,
    target_reached: bool,
) -> FixedTimeChargeState | None:
    """Resume yesterday only with proof; a fresh setup never backfills it."""
    if previous is not None and (previous.start != start or previous.day > now.date()):
        previous = None
    # Resolve a repeated local hour to its first occurrence. On spring-forward
    # days the UTC roundtrip moves a nonexistent time forward by the DST gap.
    occurrence = datetime.combine(now.date(), start, now.tzinfo).astimezone(UTC)
    if now.astimezone(UTC) >= occurrence:
        if previous is None or previous.day != now.date():
            previous = FixedTimeChargeState(start, now.date())
    if previous is not None and target_reached:
        previous = replace(previous, completed=True)
    return previous
