"""Pure expiry state for discharge protection after confirmed timed charging."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time

from ..domain.scheduling import is_time_in_window


@dataclass(frozen=True, slots=True)
class TimedDischargeState:
    """The fixed end of a window with confirmed charging from the grid."""

    expires_at: datetime


def completed_window_extended(
    now: datetime,
    start: dt_time | None,
    end: dt_time | None,
    previous_end: datetime | None,
) -> bool:
    """An edited window cannot resurrect its already completed charge cycle."""
    if (
        previous_end is None
        or now < previous_end
        or not is_time_in_window(now.time(), start, end)
    ):
        return False
    assert start is not None and end is not None
    start_date = now.date()
    if start > end and now.time() < end:
        start_date -= timedelta(days=1)
    current_start = datetime.combine(start_date, start, tzinfo=now.tzinfo)
    return current_start.astimezone(UTC) < previous_end


def window_end(
    now: datetime,
    start: dt_time | None,
    end: dt_time | None,
) -> datetime | None:
    """Return the active local window's absolute expiry in UTC.

    REQ-TIMED-SOC-CHARGE: a confirmed charge protects only this occurrence
    of the half-open window, including windows across midnight and DST.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Zeitfenster benötigt einen Zeitpunkt mit Zeitzone")
    if not is_time_in_window(now.time(), start, end):
        return None
    assert start is not None and end is not None
    end_date = now.date()
    if start > end and now.time() >= start:
        end_date += timedelta(days=1)
    local_end = datetime.combine(end_date, end, tzinfo=now.tzinfo)
    now_utc = now.astimezone(UTC)
    candidates = _end_candidates(local_end)
    return next(
        (
            candidate
            for candidate in candidates
            if now_utc < candidate <= now_utc + timedelta(hours=25)
        ),
        None,
    )


def _end_candidates(local_end: datetime) -> list[datetime]:
    """Resolve repeated wall times and stop at the first instant after a gap."""
    zone = local_end.tzinfo
    wall_end = local_end.replace(tzinfo=None)
    candidates = sorted(
        {local_end.replace(fold=fold).astimezone(UTC) for fold in (0, 1)}
    )
    valid = [
        candidate
        for candidate in candidates
        if candidate.astimezone(zone).replace(tzinfo=None) == wall_end
    ]
    if valid:
        return valid

    # A missing spring-time boundary is crossed by the clock jump itself,
    # not by adding the gap duration to the user's configured end time.
    lower, upper = candidates[0], candidates[-1]
    if not (
        lower.astimezone(zone).replace(tzinfo=None)
        < wall_end
        < upper.astimezone(zone).replace(tzinfo=None)
    ):
        return []
    while upper - lower > timedelta(microseconds=1):
        midpoint = lower + (upper - lower) // 2
        if midpoint.astimezone(zone).replace(tzinfo=None) < wall_end:
            lower = midpoint
        else:
            upper = midpoint
    return [upper]
