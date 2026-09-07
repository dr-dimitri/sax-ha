"""Framework-independent grid import and export accounting (REQ-GRID-ENERGY)."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GridEnergyDelta:
    """Separate, non-negative kWh increments at the grid connection point."""

    imported_kwh: float
    exported_kwh: float


def compute_grid_energy_delta(
    smartmeter_power: float | None, elapsed_hours: float
) -> GridEnergyDelta | None:
    """Integrate positive import and negative export without netting them.

    Invalid measurements or durations leave a gap in accounting; treating
    them as zero would conceal missing data (REQ-GRID-ENERGY).
    """
    for value in (smartmeter_power, elapsed_hours):
        if isinstance(value, bool) or not isinstance(value, int | float):
            return None
        try:
            if not math.isfinite(value):
                return None
        except OverflowError:
            return None
    if elapsed_hours < 0:
        return None

    energy_kwh = smartmeter_power / 1000 * elapsed_hours
    if not math.isfinite(energy_kwh):
        return None
    return GridEnergyDelta(max(energy_kwh, 0.0), max(-energy_kwh, 0.0))
