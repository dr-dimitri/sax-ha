"""Framework-independent normalization of PV energy forecasts."""

from __future__ import annotations

import math
from typing import Any


def normalize_energy_kwh(value: Any, unit: Any) -> float | None:
    """Return a finite energy value normalized to kWh.

    Unknown/unavailable Home Assistant states are filtered at the boundary;
    this helper deliberately only handles numeric parsing and energy units.
    """
    try:
        normalized = float(value)
    except TypeError, ValueError:
        return None
    if not math.isfinite(normalized):
        return None

    normalized_unit = str(unit or "").strip().lower()
    if normalized_unit == "wh":
        normalized /= 1000
    elif normalized_unit == "mwh":
        normalized *= 1000
    return normalized
