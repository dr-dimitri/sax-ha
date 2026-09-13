"""Window identity for restoring an unfinished timed-charge hysteresis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import time as dt_time


@dataclass(frozen=True, slots=True)
class TimedChargeState:
    """An armed hysteresis belonging to one occurrence of an unchanged window."""

    start: dt_time
    end: dt_time
    expires_at: datetime
    source: str | None = None


def is_tariff_source(value: object) -> bool:
    """A persisted tariff identity is a SHA-256 digest, never inferred data."""
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
