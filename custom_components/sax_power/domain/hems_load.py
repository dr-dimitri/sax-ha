"""SAX-only night discharge profiles (REQ-HEMS-LOAD-PROFILE)."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Literal

from .hems import EnergySlot, LoadForecast

HISTORY_WINDOW = timedelta(hours=168)
HISTORY_MAX_DELAY = timedelta(minutes=15)
MIN_NIGHTS = 3
MIN_NIGHT_SECONDS = 3600
MIN_TOTAL_SECONDS = 21600
DAWN_DURATION = timedelta(hours=4)
BASELINE_MODEL_KEY = "legacy-v1:7d"
WEIGHTED_MODEL_VERSION = "weighted-v1"
HISTORY_DAYS_OPTIONS = (7, 28)

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


@dataclass(frozen=True, slots=True)
class WeightedSample:
    """One independent night contribution, including its actual evidence."""

    night_start: datetime
    weekday: int
    power_kw: float
    observed_seconds: float
    weight: float


@dataclass(frozen=True, slots=True)
class ProfileEvidence:
    """Compact per-target evidence, suitable for an immutable forecast archive."""

    start: datetime
    end: datetime
    method: str
    group: str
    sample_nights: int
    observed_minutes: float
    weight_sum: float


@dataclass(frozen=True, slots=True)
class WeightedNightProfile:
    """Versioned candidate; it never grants its own use in device control."""

    as_of: datetime
    evaluated_through: datetime | None
    history_days: int
    reason: str
    available_history_days: float = 0.0
    nights: int = 0
    observed_hours: float = 0.0
    coverage: float = 0.0
    pooled: tuple[WeightedSample, ...] = ()
    slots: tuple[tuple[int, tuple[WeightedSample, ...]], ...] = ()
    dawn: tuple[WeightedSample, ...] = ()

    @property
    def model_key(self) -> str:
        return f"{WEIGHTED_MODEL_VERSION}:{self.history_days}d"


@dataclass(frozen=True, slots=True)
class LoadVariants:
    """Separate production baseline and shadow candidate, with no activation."""

    baseline: LoadForecast
    candidate: LoadForecast
    current_night: NightSpan | None = None
    baseline_key: str = BASELINE_MODEL_KEY
    candidate_key: str = "weighted-v1:7d"
    history_days: int = 7
    available_history_days: float = 0.0
    candidate_metadata: tuple[ProfileEvidence, ...] = ()


def validate_history_days(value: int) -> int:
    if type(value) is not int or value not in HISTORY_DAYS_OPTIONS:
        raise ValueError("History must be 7 or 28 days")
    return value


def build_weighted_profile(
    observations: tuple[DischargeObservation, ...],
    nights: tuple[NightSpan, ...],
    *,
    as_of: datetime,
    evaluated_through: datetime | None,
    zone: tzinfo,
    history_days: int = 7,
) -> WeightedNightProfile:
    """REQ-HEMS-LOAD-PROFILE: candidate v1, not a claimed optimal weighting."""
    validate_history_days(history_days)
    if not aware(as_of):
        raise ValueError("as_of must be timezone-aware")
    as_of = as_of.astimezone(UTC)
    base = dict(
        as_of=as_of, evaluated_through=evaluated_through, history_days=history_days
    )
    if not nights or any(
        not aware(n.start) or not aware(n.end) or n.end <= n.start for n in nights
    ):
        return WeightedNightProfile(**base, reason="unsupported_night_geometry")
    if not aware(evaluated_through):
        return WeightedNightProfile(**base, reason="history_unavailable")
    assert evaluated_through is not None
    if not timedelta() <= as_of - evaluated_through <= HISTORY_MAX_DELAY:
        return WeightedNightProfile(**base, reason="history_stale")
    if not _valid_observations(observations):
        return WeightedNightProfile(**base, reason="history_invalid")
    cutoff = as_of - timedelta(days=history_days)
    completed = sorted(
        {
            (n.start.astimezone(UTC), n.end.astimezone(UTC))
            for n in nights
            if n.start >= cutoff and n.end <= as_of
        }
    )
    available = [o for o in observations if cutoff < o.end <= as_of]
    available_days = (
        (as_of - max(cutoff, available[0].start)).total_seconds() / 86400
        if available
        else 0.0
    )
    pooled: list[WeightedSample] = []
    slots: dict[int, list[WeightedSample]] = defaultdict(list)
    dawn: list[WeightedSample] = []
    for start, end in completed:
        observed = [
            o
            for o in available
            if o.quality == "valid" and o.start < end and o.end > start
        ]
        portions = [_slice_energy(o, start, end) for o in observed]
        energy = sum(e for e, _ in portions)
        seconds = sum(s for _, s in portions)
        if seconds < MIN_NIGHT_SECONDS:
            continue
        recency = math.exp(-(as_of - end).total_seconds() / (7 * 86400))

        def sample(
            kwh: float,
            duration: float,
            denominator: float,
            weekday: int,
            *,
            night_start: datetime = start,
            age_weight: float = recency,
        ) -> WeightedSample:
            return WeightedSample(
                night_start,
                weekday,
                kwh * 3600 / duration,
                duration,
                age_weight * min(1.0, duration / denominator),
            )

        pooled.append(
            sample(
                energy,
                seconds,
                (end - start).total_seconds(),
                start.astimezone(zone).weekday(),
            )
        )
        totals: dict[tuple[int, int], list[float]] = defaultdict(lambda: [0.0, 0.0])
        slot_durations: dict[tuple[int, int], float] = defaultdict(float)
        cursor = start
        while cursor < end:
            stop = min(_next_quarter(cursor), end)
            local = cursor.astimezone(zone)
            key = (local.hour * 4 + local.minute // 15, local.weekday())
            slot_durations[key] += (stop - cursor).total_seconds()
            cursor = stop
        dawn_energy = dawn_seconds = 0.0
        for item in observed:
            cursor, limit = max(item.start, start), min(item.end, end)
            while cursor < limit:
                stop = min(_next_quarter(cursor), limit)
                local = cursor.astimezone(zone)
                key = (local.hour * 4 + local.minute // 15, local.weekday())
                e, s = _slice_energy(item, cursor, stop)
                totals[key][0] += e
                totals[key][1] += s
                cursor = stop
            e, s = _slice_energy(item, end - timedelta(hours=2), end)
            dawn_energy += e
            dawn_seconds += s
        for (key, weekday), (energy, seconds) in totals.items():
            if seconds >= 600:
                slots[key].append(
                    sample(
                        energy,
                        seconds,
                        max(900, slot_durations[(key, weekday)]),
                        weekday,
                    )
                )
        if dawn_seconds >= 3600:
            dawn.append(
                sample(dawn_energy, dawn_seconds, 7200, end.astimezone(zone).weekday())
            )
    total_seconds = sum((end - start).total_seconds() for start, end in completed)
    observed_seconds = sum(s.observed_seconds for s in pooled)
    reason = (
        "ok"
        if len(pooled) >= MIN_NIGHTS and observed_seconds >= MIN_TOTAL_SECONDS
        else "insufficient_history"
    )
    if any(
        not finite_number(s.power_kw)
        for s in (*pooled, *dawn, *(s for values in slots.values() for s in values))
    ):
        reason = "history_invalid"
    return WeightedNightProfile(
        **base,
        reason=reason,
        available_history_days=available_days,
        nights=len(pooled),
        observed_hours=observed_seconds / 3600,
        coverage=observed_seconds / total_seconds if total_seconds else 0.0,
        pooled=tuple(pooled),
        slots=tuple((key, tuple(values)) for key, values in sorted(slots.items())),
        dawn=tuple(dawn),
    )


def _comparison_group(
    samples: tuple[WeightedSample, ...], weekday: int
) -> tuple[tuple[WeightedSample, ...], str]:
    for group, subset in (
        ("same_weekday", tuple(s for s in samples if s.weekday == weekday)),
        (
            "workday" if weekday < 5 else "weekend",
            tuple(s for s in samples if (s.weekday < 5) == (weekday < 5)),
        ),
        ("all_nights", samples),
    ):
        if len({s.night_start for s in subset}) >= MIN_NIGHTS:
            return subset, group
    return (), "pooled"


def forecast_weighted_load(
    profile: WeightedNightProfile,
    night: NightSpan,
    *,
    zone: tzinfo,
) -> tuple[LoadForecast, tuple[ProfileEvidence, ...]]:
    """Produce an explicitly separate candidate, including dawn shadow values."""
    base = dict(
        generated_at=profile.as_of,
        evaluated_through=profile.evaluated_through,
        quality_reason=None if profile.reason == "ok" else profile.reason,
        nights_count=profile.nights,
        observed_hours=profile.observed_hours,
        coverage=profile.coverage,
        model_start=night.start,
        model_end=night.end + DAWN_DURATION,
    )
    if profile.reason != "ok":
        return LoadForecast(**base), ()
    cursor = profile.as_of
    if not night.start <= cursor < night.end + DAWN_DURATION:
        return LoadForecast(**{**base, "quality_reason": "outside_model_scope"}), ()
    intervals: list[EnergySlot] = []
    evidence: list[ProfileEvidence] = []
    by_slot = dict(profile.slots)
    while cursor < night.end + DAWN_DURATION:
        stop = min(_next_quarter(cursor), night.end + DAWN_DURATION)
        local = cursor.astimezone(zone)
        is_dawn = cursor >= night.end
        if not is_dawn:
            stop = min(stop, night.end)
        samples, group = _comparison_group(
            (
                profile.dawn
                if is_dawn
                else by_slot.get(local.hour * 4 + local.minute // 15, ())
            ),
            local.weekday(),
        )
        method = "weighted_dawn" if is_dawn else "weighted_slot"
        if not samples:
            samples = profile.pooled
            method = "weighted_pooled_dawn" if is_dawn else "weighted_pooled_night"
        weights = sum(s.weight for s in samples)
        if not weights or not finite_number(weights):
            return LoadForecast(**{**base, "quality_reason": "history_invalid"}), ()
        power = sum(s.power_kw * s.weight for s in samples) / weights
        if not finite_number(power):
            return LoadForecast(**{**base, "quality_reason": "history_invalid"}), ()
        intervals.append(
            EnergySlot(
                cursor,
                stop,
                power * (stop - cursor).total_seconds() / 3600,
                (method, group),
            )
        )
        evidence.append(
            ProfileEvidence(
                cursor,
                stop,
                method,
                group,
                len({s.night_start for s in samples}),
                sum(s.observed_seconds for s in samples) / 60,
                weights,
            )
        )
        cursor = stop
    return (
        LoadForecast(
            **base,
            intervals=tuple(intervals),
            quality_flags=tuple(
                sorted({f for i in intervals for f in i.quality_flags})
            ),
        ),
        tuple(evidence),
    )
