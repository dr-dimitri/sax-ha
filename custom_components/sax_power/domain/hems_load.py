"""SAX-only night discharge profiles (REQ-HEMS-LOAD-PROFILE)."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Literal

HISTORY_WINDOW = timedelta(hours=168)
HISTORY_MAX_DELAY = timedelta(minutes=15)
MIN_NIGHTS = 3
MIN_NIGHT_SECONDS = 3600
MIN_TOTAL_SECONDS = 21600
DAWN_DURATION = timedelta(hours=4)

type ObservationQuality = Literal["valid", "censored", "unknown"]


def finite_number(value: object) -> bool:
    """Reject booleans and nonfinite telemetry before arithmetic."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def aware(value: object) -> bool:
    """Check timestamps without silently accepting host-local naive dates."""
    return isinstance(value, datetime) and value.utcoffset() is not None


@dataclass(frozen=True, slots=True)
class NightSpan:
    """One astronomical sunset-to-sunrise interval."""

    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True)
class DischargeObservation:
    """An observed interval; censored/unknown energy is never a training zero."""

    start: datetime
    end: datetime
    energy_kwh: float
    quality: ObservationQuality


@dataclass(frozen=True, slots=True)
class LoadPiece:
    """Forecast energy and evidence for one real future interval."""

    start: datetime
    end: datetime
    energy_kwh: float
    method: str
    sample_nights: int


@dataclass(frozen=True, slots=True)
class NightLoadProfile:
    """Pure profile result, including quality even when no forecast is allowed."""

    as_of: datetime
    evaluated_through: datetime | None
    reason: str
    nights: int = 0
    observed_hours: float = 0.0
    coverage: float = 0.0
    pooled_kw: float | None = None
    slots: tuple[tuple[int, float, int], ...] = ()
    dawn_kw: float | None = None
    dawn_nights: int = 0


def _slice_energy(
    observation: DischargeObservation, start: datetime, end: datetime
) -> tuple[float, float]:
    lo = max(observation.start.astimezone(UTC), start.astimezone(UTC))
    hi = min(observation.end.astimezone(UTC), end.astimezone(UTC))
    seconds = max(0.0, (hi - lo).total_seconds())
    duration = (
        observation.end.astimezone(UTC) - observation.start.astimezone(UTC)
    ).total_seconds()
    return observation.energy_kwh * seconds / duration, seconds


def _next_quarter(value: datetime) -> datetime:
    return datetime.fromtimestamp((int(value.timestamp()) // 900 + 1) * 900, UTC)


def _valid_observations(observations: tuple[DischargeObservation, ...]) -> bool:
    previous_end: datetime | None = None
    for item in observations:
        if (
            not aware(item.start)
            or not aware(item.end)
            or item.end.astimezone(UTC) <= item.start.astimezone(UTC)
            or not finite_number(item.energy_kwh)
            or item.energy_kwh < 0
            or item.quality not in ("valid", "censored", "unknown")
        ):
            return False
        if previous_end is not None and item.start.astimezone(UTC) < previous_end:
            return False
        previous_end = item.end.astimezone(UTC)
    return True


def build_night_profile(
    observations: tuple[DischargeObservation, ...],
    nights: tuple[NightSpan, ...],
    *,
    as_of: datetime,
    evaluated_through: datetime | None,
    zone: tzinfo,
) -> NightLoadProfile:
    """Learn only proven free discharge; keep all policy clocks explicit."""
    if not aware(as_of):
        raise ValueError("as_of must be timezone-aware")
    as_of = as_of.astimezone(UTC)
    base = {"as_of": as_of, "evaluated_through": evaluated_through}
    if not nights or any(
        not aware(n.start)
        or not aware(n.end)
        or n.end.astimezone(UTC) <= n.start.astimezone(UTC)
        for n in nights
    ):
        return NightLoadProfile(**base, reason="unsupported_night_geometry")
    if not aware(evaluated_through):
        return NightLoadProfile(**base, reason="history_unavailable")
    assert evaluated_through is not None
    if (
        not timedelta()
        <= as_of - evaluated_through.astimezone(UTC)
        <= HISTORY_MAX_DELAY
    ):
        return NightLoadProfile(**base, reason="history_stale")
    if not _valid_observations(observations):
        return NightLoadProfile(**base, reason="history_invalid")
    history_start = as_of - HISTORY_WINDOW
    completed = {
        (night.start.astimezone(UTC), night.end.astimezone(UTC))
        for night in nights
        if night.start.astimezone(UTC) >= history_start
        and night.end.astimezone(UTC) <= as_of
    }
    eligible: list[tuple[NightSpan, float, float]] = []
    night_slots: dict[int, list[float]] = defaultdict(list)
    dawn_means: list[float] = []
    for start, end in sorted(completed):
        observed = [
            item
            for item in observations
            if item.quality == "valid" and item.start < end and item.end > start
        ]
        totals = [_slice_energy(item, start, end) for item in observed]
        energy = sum(part[0] for part in totals)
        seconds = sum(part[1] for part in totals)
        if seconds < MIN_NIGHT_SECONDS:
            continue
        eligible.append((NightSpan(start, end), energy, seconds))
        slot_totals: dict[int, list[float]] = defaultdict(lambda: [0.0, 0.0])
        dawn_energy = dawn_seconds = 0.0
        for item in observed:
            lo = max(item.start.astimezone(UTC), start)
            hi = min(item.end.astimezone(UTC), end)
            cursor = lo
            while cursor < hi:
                stop = min(_next_quarter(cursor), hi)
                local = cursor.astimezone(zone)
                key = local.hour * 4 + local.minute // 15
                portion, duration = _slice_energy(item, cursor, stop)
                slot_totals[key][0] += portion
                slot_totals[key][1] += duration
                cursor = stop
            portion, duration = _slice_energy(item, end - timedelta(hours=2), end)
            dawn_energy += portion
            dawn_seconds += duration
        for key, (portion, duration) in slot_totals.items():
            night_slots[key].append(portion * 3600 / duration)
        if dawn_seconds > 0:
            dawn_means.append(dawn_energy * 3600 / dawn_seconds)
    observed_seconds = sum(item[2] for item in eligible)
    total_seconds = sum((end - start).total_seconds() for start, end in completed)
    metadata = {
        **base,
        "nights": len(eligible),
        "observed_hours": observed_seconds / 3600,
        "coverage": observed_seconds / total_seconds if total_seconds else 0.0,
    }
    if len(eligible) < MIN_NIGHTS or observed_seconds < MIN_TOTAL_SECONDS:
        return NightLoadProfile(**metadata, reason="insufficient_history")
    pooled = sum(energy * 3600 / seconds for _, energy, seconds in eligible) / len(
        eligible
    )
    if not finite_number(pooled) or any(
        not finite_number(value) for values in night_slots.values() for value in values
    ):
        return NightLoadProfile(**metadata, reason="history_invalid")
    return NightLoadProfile(
        **metadata,
        reason="ok",
        pooled_kw=pooled,
        slots=tuple(
            (key, sum(values) / len(values), len(values))
            for key, values in sorted(night_slots.items())
            if len(values) >= MIN_NIGHTS
        ),
        dawn_kw=(
            sum(dawn_means) / len(dawn_means) if len(dawn_means) >= MIN_NIGHTS else None
        ),
        dawn_nights=len(dawn_means),
    )


def forecast_night_load(
    profile: NightLoadProfile,
    night: NightSpan,
    *,
    zone: tzinfo,
    end: datetime | None = None,
) -> tuple[LoadPiece, ...]:
    """Project the current night and at most four real dawn hours."""
    if profile.reason != "ok" or profile.pooled_kw is None:
        return ()
    if not aware(night.start) or not aware(night.end):
        return ()
    sunrise = night.end.astimezone(UTC)
    model_end = sunrise + DAWN_DURATION
    cursor = profile.as_of.astimezone(UTC)
    if not night.start.astimezone(UTC) <= cursor < model_end:
        return ()
    limit = min(end.astimezone(UTC), model_end) if end else model_end
    slots = {key: (power, count) for key, power, count in profile.slots}
    result: list[LoadPiece] = []
    while cursor < limit:
        stop = min(_next_quarter(cursor), limit)
        if cursor < sunrise:
            stop = min(stop, sunrise)
            local = cursor.astimezone(zone)
            key = local.hour * 4 + local.minute // 15
            if key in slots:
                power, count = slots[key]
                method = "night_slot_mean"
            else:
                power, count = profile.pooled_kw, profile.nights
                method = "pooled_night_estimate"
        elif profile.dawn_kw is not None:
            power, count = profile.dawn_kw, profile.dawn_nights
            method = "dawn_extrapolation"
        else:
            power, count = profile.pooled_kw, profile.nights
            method = "pooled_dawn_estimate"
        result.append(
            LoadPiece(
                cursor,
                stop,
                power * (stop - cursor).total_seconds() / 3600,
                method,
                count,
            )
        )
        cursor = stop
    return tuple(result)
