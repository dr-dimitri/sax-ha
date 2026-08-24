"""Pure policy for the periodic full-charge calibration cycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class CalibrationState:
    """Persisted state needed to detect a new full-SOC edge."""

    last_full_charge_at: datetime | None = None
    was_full: bool = False


@dataclass(frozen=True, slots=True)
class CalibrationDecision:
    """Result of one calibration policy evaluation."""

    state: CalibrationState
    calibration_active: bool
    effective_max_soc: int
    next_calibration_at: datetime
    state_changed: bool


def evaluate_calibration(
    *,
    now: datetime,
    current_soc: int | float,
    configured_max_soc: int | None,
    state: CalibrationState,
    interval: timedelta,
    maximum_soc: int,
) -> CalibrationDecision:
    """Evaluate calibration state without Home Assistant dependencies.

    The first valid SOC establishes a baseline. A full charge resets that
    baseline only on the edge from below full to full, so a battery staying
    at 100 percent does not move the due date on every poll.
    """
    is_full = current_soc >= maximum_soc
    updated_state = state

    if state.last_full_charge_at is None:
        updated_state = CalibrationState(
            last_full_charge_at=now,
            was_full=is_full,
        )
    elif is_full and not state.was_full:
        updated_state = CalibrationState(
            last_full_charge_at=now,
            was_full=True,
        )
    elif not is_full and state.was_full:
        updated_state = CalibrationState(
            last_full_charge_at=state.last_full_charge_at,
            was_full=False,
        )

    # The initialization branch above guarantees a timestamp here.
    last_full_charge_at = updated_state.last_full_charge_at
    if last_full_charge_at is None:  # pragma: no cover - type narrowing guard
        raise AssertionError("Kalibrierungs-Baseline fehlt")
    next_calibration_at = last_full_charge_at + interval
    calibration_active = (
        configured_max_soc is not None
        and configured_max_soc < maximum_soc
        and not is_full
        and now >= next_calibration_at
    )
    effective_max_soc = (
        maximum_soc
        if calibration_active or configured_max_soc is None
        else configured_max_soc
    )

    return CalibrationDecision(
        state=updated_state,
        calibration_active=calibration_active,
        effective_max_soc=effective_max_soc,
        next_calibration_at=next_calibration_at,
        state_changed=updated_state != state,
    )
