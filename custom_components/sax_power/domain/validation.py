"""Framework-independent validation helpers for integration settings."""

from __future__ import annotations

import math


def clamp_int(value: int | None, minimum: int, maximum: int) -> int | None:
    """Clamp an optional integer to an inclusive range."""
    if value is None:
        return None
    return max(minimum, min(maximum, value))


def clamp_float(value: float | None, minimum: float, maximum: float) -> float | None:
    """Clamp an optional float to an inclusive range."""
    if value is None:
        return None
    return max(minimum, min(maximum, float(value)))


def round_half_up(value: float | None) -> int | None:
    """Round to an integer with halves away from zero."""
    if value is None:
        return None
    numeric = float(value)
    if not math.isfinite(numeric):
        return None
    if numeric >= 0:
        return math.floor(numeric + 0.5)
    return math.ceil(numeric - 0.5)
