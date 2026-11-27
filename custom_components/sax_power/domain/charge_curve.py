"""Elapsed time for maximum grid charging (REQ-BRIDGE-CHARGE)."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

# SOC and elapsed minutes on 2026-11-27. The trace peaked at 99%;
# only the last percentage point extrapolates the measured 97–99% slope.
_MEASURED_POINTS = (
    (0, 0),
    (10, 20),
    (50, 89),
    (75, 127),
    (90, 163),
    (95, 186),
    (97, 196),
    (99, 221),
)
_BANDS = tuple(
    (start, end, (end_minutes - start_minutes) / (end - start) / 60)
    for (start, start_minutes), (end, end_minutes) in pairwise(_MEASURED_POINTS)
)
_BANDS += ((99, 100, _BANDS[-1][2]),)
_FASTEST_HOURS_PER_PERCENT = min(hours for _, _, hours in _BANDS)


@dataclass(frozen=True, slots=True)
class GridChargeCurve:
    """SOC-dependent charging time, capped by the available battery power."""

    capacity_wh: float
    power_limit_w: float

    @property
    def fastest_power_w(self) -> float:
        """Upper bound on the mean power of any charge on this battery."""
        return min(
            self.power_limit_w, self.capacity_wh / 100 / _FASTEST_HOURS_PER_PERCENT
        )

    def hours_between(self, start_soc: float, target_soc: float) -> float:
        """Accumulate only the part of each SOC band traversed by this charge."""
        hours = 0.0
        for lower, upper, hours_per_percent in _BANDS:
            gain = min(target_soc, upper) - max(start_soc, lower)
            if gain > 0:
                power_limited = self.capacity_wh * gain / 100 / self.power_limit_w
                hours += max(gain * hours_per_percent, power_limited)
        return hours

    def seconds_between(self, start_soc: float, target_soc: float) -> float:
        """Match schedule precision before the dashboard rounds up minutes or hours."""
        return round(self.hours_between(start_soc, target_soc) * 3600, 6)

    def wait_for_minimum(
        self,
        *,
        start_soc: float,
        floor_soc: float,
        max_soc: float,
        gain_wh: float,
        discharge_w: float,
        window_hours: float,
    ) -> float | None:
        """Earliest offset where waiting plus the minimum charge fits the window."""
        gain_soc = gain_wh / self.capacity_wh * 100
        hours_short = (
            self.hours_between(start_soc, min(max_soc, start_soc + gain_soc))
            - window_hours
        )
        if hours_short <= 1e-12:
            return 0.0
        if discharge_w <= 0 or start_soc <= floor_soc:
            return None

        # A lower SOC can accept the minimum faster despite the shorter window.
        # Finish time is linear between crossings of either end of the charge
        # through a curve knot or the ceiling. At the floor, waiting only costs time.
        soc_per_hour = discharge_w / self.capacity_wh * 100
        lowest = max(floor_soc, start_soc - soc_per_hour * window_hours)
        if lowest >= start_soc:
            return None
        levels = {lowest}
        boundaries = {upper for _, upper, _ in _BANDS} | {max_soc}
        for boundary in boundaries:
            for level in (boundary, boundary - gain_soc):
                if lowest < level < start_soc:
                    levels.add(level)
        previous_wait = 0.0
        for level in sorted(levels, reverse=True):
            wait = (start_soc - level) / soc_per_hour
            finish = wait + self.hours_between(level, min(max_soc, level + gain_soc))
            short = finish - window_hours
            if short <= 1e-12:
                return previous_wait + (wait - previous_wait) * hours_short / (
                    hours_short - min(short, 0.0)
                )
            previous_wait, hours_short = wait, short
        return None
