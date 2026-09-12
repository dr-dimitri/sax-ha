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
