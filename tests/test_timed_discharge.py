"""REQ-TIMED-SOC-CHARGE: fixed discharge-protection window expiry."""

from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from zoneinfo import ZoneInfo

import pytest

from custom_components.sax_power.application.timed_discharge import window_end

BERLIN = ZoneInfo("Europe/Berlin")


@pytest.mark.parametrize(
    ("now", "start", "end", "expected"),
    [
        ("2026-09-05T00:59:59", dt_time(1), dt_time(4), None),
        ("2026-09-05T01:00:00", dt_time(1), dt_time(4), "2026-09-05T02:00:00"),
        ("2026-09-05T03:59:59", dt_time(1), dt_time(4), "2026-09-05T02:00:00"),
        ("2026-09-05T04:00:00", dt_time(1), dt_time(4), None),
        ("2026-09-05T22:00:00", dt_time(22), dt_time(4), "2026-09-06T02:00:00"),
        ("2026-09-06T00:00:00", dt_time(22), dt_time(4), "2026-09-06T02:00:00"),
        ("2026-09-06T04:00:00", dt_time(22), dt_time(4), None),
        ("2026-09-06T12:00:00", dt_time(22), dt_time(4), None),
        ("2026-12-31T23:00:00", dt_time(22), dt_time(4), "2027-01-01T03:00:00"),
        ("2026-09-05T02:00:00", dt_time(1), dt_time(1), None),
        ("2026-09-05T02:00:00", None, dt_time(4), None),
        ("2026-09-05T02:00:00", dt_time(1), None, None),
    ],
)
def test_window_expiry_respects_half_open_local_occurrence(
    now: str, start: dt_time | None, end: dt_time | None, expected: str | None
) -> None:
    """The confirmed hold belongs to one concrete window, never tomorrow's."""
    result = window_end(datetime.fromisoformat(now).replace(tzinfo=BERLIN), start, end)

    assert result == (
        datetime.fromisoformat(expected).replace(tzinfo=UTC) if expected else None
    )
    if result is not None:
        assert result.tzinfo is UTC


@pytest.mark.parametrize(
    ("now", "expected", "hours"),
    [
        ("2026-03-28T22:00:00", "2026-03-29T05:00:00", 8),
        ("2026-10-24T22:00:00", "2026-10-25T06:00:00", 10),
    ],
)
def test_overnight_expiry_uses_actual_elapsed_time_across_dst(
    now: str, expected: str, hours: int
) -> None:
    """DST changes adjust the real expiry without extending to another day."""
    local_now = datetime.fromisoformat(now).replace(tzinfo=BERLIN)

    result = window_end(local_now, dt_time(22), dt_time(7))

    assert result == datetime.fromisoformat(expected).replace(tzinfo=UTC)
    assert result - local_now.astimezone(UTC) == timedelta(hours=hours)


def test_nonexistent_spring_end_expires_at_clock_jump() -> None:
    """A nonexistent 02:30 end has elapsed immediately at the jump to 03:00."""
    now = datetime(2026, 3, 29, 1, 15, tzinfo=BERLIN)

    assert window_end(now, dt_time(1), dt_time(2, 30)) == datetime(
        2026, 3, 29, 1, tzinfo=UTC
    )
    assert (
        window_end(datetime(2026, 3, 29, 3, tzinfo=BERLIN), dt_time(1), dt_time(2, 30))
        is None
    )


@pytest.mark.parametrize("fold", [0, 1])
def test_repeated_autumn_end_uses_next_occurrence(fold: int) -> None:
    """A confirmed charge expires at the next actual crossing of its end."""
    now = datetime(2026, 10, 25, 2, 15, tzinfo=BERLIN, fold=fold)

    assert window_end(now, dt_time(1), dt_time(2, 30)) == datetime(
        2026, 10, 25, fold, 30, tzinfo=UTC
    )
    assert (
        window_end(
            datetime(2026, 10, 25, 2, 30, tzinfo=BERLIN, fold=fold),
            dt_time(1),
            dt_time(2, 30),
        )
        is None
    )


def test_autumn_window_can_last_almost_twenty_five_hours() -> None:
    now = datetime(2026, 10, 24, 3, 1, tzinfo=BERLIN)

    result = window_end(now, dt_time(3, 1), dt_time(3))

    assert result == datetime(2026, 10, 25, 2, tzinfo=UTC)
    assert result - now.astimezone(UTC) == timedelta(hours=24, minutes=59)


def test_timezone_rollback_never_creates_a_hold_over_twenty_five_hours() -> None:
    """Even a historical date-line change must not create a multi-day hold."""
    now = datetime(1969, 9, 30, 1, tzinfo=ZoneInfo("Pacific/Kwajalein"))

    assert window_end(now, dt_time(1), dt_time(0)) is None


def test_window_expiry_rejects_naive_current_time() -> None:
    with pytest.raises(ValueError, match="Zeitzone"):
        window_end(datetime(2026, 9, 5, 2), dt_time(1), dt_time(4))
