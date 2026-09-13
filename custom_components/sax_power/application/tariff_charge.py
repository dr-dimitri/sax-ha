"""Fixed SOC charging from REQ-TIME-OF-USE-CHARGE-SOURCE."""

from __future__ import annotations

import hashlib
from collections.abc import Set
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time

from ..domain.tariff import TariffConfig, low_tariff_window
from .timed_charge import TimedChargeState


def tariff_charge_state(
    config: TariffConfig, now: datetime, active_months: Set[int]
) -> TimedChargeState | None:
    """Bind a latch to the tariff and the actual occurrence, never legacy times."""
    if now.month not in active_months:
        return None
    quote = low_tariff_window(config, now)
    if quote is None or quote.valid_from is None or quote.valid_until is None:
        return None
    start = quote.valid_from.astimezone(UTC)
    end = quote.valid_until.astimezone(UTC)
    midnight = datetime.combine(now.date(), dt_time(), now.tzinfo)
    # A skipped expensive DST window can join low phases across several
    # local days. Month clipping must therefore inspect the full phase.
    boundary = midnight
    while boundary.astimezone(UTC) > start:
        previous_day = boundary - timedelta(days=1)
        if previous_day.month not in active_months:
            start = boundary.astimezone(UTC)
            break
        boundary = previous_day
    boundary = midnight + timedelta(days=1)
    while boundary.astimezone(UTC) < end:
        if boundary.month not in active_months:
            end = boundary.astimezone(UTC)
            break
        boundary += timedelta(days=1)
    # Persist the exact tariff occurrence so a former manual window, tariff
    # edit, or repeated DST hour cannot restore unrelated permission.
    source = hashlib.sha256(repr((config, start, end)).encode()).hexdigest()
    return TimedChargeState(
        start.astimezone(now.tzinfo).time(),
        end.astimezone(now.tzinfo).time(),
        end,
        source,
    )
