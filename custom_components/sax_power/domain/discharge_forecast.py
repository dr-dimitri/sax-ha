"""Rolling discharge estimate from measured power (REQ-DISCHARGE-FORECAST)."""

from __future__ import annotations

import math
from collections import deque
from itertools import pairwise


def _finite(value: object) -> bool:
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


class DischargeForecast:
    """Keep at most one hour of time-weighted discharge observations."""

    def __init__(self, *, max_sample_gap: float) -> None:
        self._max_sample_gap = max_sample_gap
        self._samples: deque[tuple[float, float]] = deque()
        self._charging_since: float | None = None
        self._last_time: float | None = None

    def reset(self) -> None:
        """Discard unobservable history on restart or a measurement outage."""
        self._samples.clear()
        self._charging_since = None
        self._last_time = None

    def update(
        self,
        *,
        time: float,
        power: float | None,
        capacity_wh: float | None,
        soc: float | None,
        min_soc: float | None,
    ) -> float | None:
        """Return seconds until the device SOC floor, or no usable estimate."""
        if not all(
            _finite(value) for value in (time, power, capacity_wh, soc, min_soc)
        ):
            self.reset()
            return None
        assert power is not None
        assert capacity_wh is not None
        assert soc is not None
        assert min_soc is not None
        if capacity_wh <= 0 or not 0 <= soc <= 100 or not 0 <= min_soc <= 100:
            self.reset()
            return None
        if self._last_time is not None and not (
            0 < time - self._last_time <= self._max_sample_gap
        ):
            self.reset()
        self._last_time = time

        if power < 0:
            if self._charging_since is None:
                self._charging_since = time
            if time - self._charging_since >= 60:
                self._samples.clear()
                return None
        else:
            self._charging_since = None

        # Start the window with actual discharge; brief charging and idle
        # intervals contribute zero discharge, but still count elapsed time.
        if not self._samples and power <= 0:
            return None
        self._samples.append((time, max(power, 0.0)))
        cutoff = time - 3600
        while len(self._samples) > 1 and self._samples[1][0] <= cutoff:
            self._samples.popleft()
        start = max(self._samples[0][0], cutoff)
        duration = time - start
        if duration < 60:
            return None
        watt_seconds = sum(
            power * (right[0] - max(left_time, cutoff))
            for (left_time, power), right in pairwise(self._samples)
        )
        average_power = watt_seconds / duration
        if average_power <= 0:
            return None
        remaining_wh = capacity_wh * max(soc - min_soc, 0.0) / 100
        return remaining_wh / average_power * 3600
