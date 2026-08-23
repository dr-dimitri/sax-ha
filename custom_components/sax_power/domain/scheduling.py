"""Pure time-window rules shared by the charging use cases."""

from __future__ import annotations

from datetime import time as dt_time


def is_time_in_window(
    now: dt_time,
    start: dt_time | None,
    end: dt_time | None,
) -> bool:
    """Return whether ``now`` is inside a half-open, possibly overnight window."""
    if start is None or end is None or start == end:
        return False
    if start < end:
        return start <= now < end
    return now >= start or now < end


def windows_overlap(
    start_a: dt_time | None,
    end_a: dt_time | None,
    start_b: dt_time | None,
    end_b: dt_time | None,
) -> bool:
    """Return whether two half-open, possibly overnight windows overlap."""
    if start_a is None or end_a is None or start_b is None or end_b is None:
        return False
    return any(
        a_start < b_end and b_start < a_end
        for a_start, a_end in _window_intervals(start_a, end_a)
        for b_start, b_end in _window_intervals(start_b, end_b)
    )


def _window_intervals(start: dt_time, end: dt_time) -> list[tuple[int, int]]:
    start_seconds = _time_to_seconds(start)
    end_seconds = _time_to_seconds(end)
    if start_seconds == end_seconds:
        return []
    if start_seconds < end_seconds:
        return [(start_seconds, end_seconds)]
    return [(start_seconds, 24 * 3600), (0, end_seconds)]


def _time_to_seconds(value: dt_time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second
