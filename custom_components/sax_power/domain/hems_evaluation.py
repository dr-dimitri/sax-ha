"""Immutable, causal SAX forecast evaluation (REQ-HEMS-FORECAST-EVALUATION)."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from zoneinfo import ZoneInfo

from .hems import EnergySlot, PvForecast
from .hems_load import DischargeObservation

type Horizon = Literal["15m", "60m", "rest_night"]
type Phase = Literal["night", "dawn"]


def utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("A timezone-aware timestamp is required")
    return value.astimezone(UTC)


def finite(value: object) -> bool:
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def canonical_json(value: object) -> str:
    """Copy metadata into a bounded immutable representation, without NaN."""
    result = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(result.encode()) > 65536:
        raise ValueError("Forecast metadata exceeds its bounded contract")
    return result


@dataclass(frozen=True, slots=True)
class ModelKey:
    profile_version: str
    parameter_version: str
    history_days: int = 7
    live_version: str = "off"
    live_parameters: str = "none"
    live_policy: str = "off"
    basis: str = "sax_discharge_ac"

    @property
    def identifier(self) -> str:
        return canonical_json(asdict(self))


@dataclass(frozen=True, slots=True)
class ForecastSeries:
    model_key: str
    intervals: tuple[EnergySlot, ...]
    metadata_json: str = "{}"
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ForecastSeriesRecord:
    issued_at: datetime
    intervals: tuple[EnergySlot, ...]
    model_key: str


@dataclass(frozen=True, slots=True)
class ForecastBand:
    """A prospectively issued range, attached to one exact target/class."""

    class_key: str
    model_key: str
    start: datetime
    end: datetime
    lower_kwh: float
    upper_kwh: float
    method_id: str
    trained_until: datetime


@dataclass(frozen=True, slots=True)
class ForecastRecord:
    record_id: str
    issued_at: datetime
    data_as_of: datetime
    night_id: str
    night_start: datetime
    sunrise: datetime
    model_end: datetime
    baseline: ForecastSeries
    applied: ForecastSeries
    candidate: ForecastSeries | None = None
    raw_profiles: tuple[ForecastSeries, ...] = ()
    pv: PvForecast = PvForecast()
    planning_parameters_json: str = "{}"
    live_metadata_json: str = "{}"
    current_usable_kwh: float | None = None
    predecessor_id: str | None = None
    output_group: str = "default"
    basis: str = "sax_discharge_ac"
    bands: tuple[ForecastBand, ...] = ()
    time_zone: str = "UTC"


@dataclass(frozen=True, slots=True)
class TimeSpan:
    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True)
class EvaluationPair:
    pair_id: str
    record_id: str
    issued_at: datetime
    night_id: str
    phase: Phase
    horizon: Horizon
    start: datetime
    end: datetime
    output_group: str
    baseline_key: str
    baseline_kwh: float
    applied_key: str
    applied_kwh: float | None
    candidate_key: str | None
    candidate_kwh: float | None
    observed_kwh: float
    valid_spans: tuple[TimeSpan, ...]
    excluded_seconds: tuple[tuple[str, float], ...]
    complete: bool
    basis: str = "sax_discharge_ac"
    bands: tuple[ForecastBand, ...] = ()

    @property
    def observed_hours(self) -> float:
        return sum((s.end - s.start).total_seconds() for s in self.valid_spans) / 3600

    def prediction(self, model_key: str) -> float | None:
        for key, value in (
            (self.applied_key, self.applied_kwh),
            (self.baseline_key, self.baseline_kwh),
            (self.candidate_key, self.candidate_kwh),
        ):
            if key == model_key:
                return value
        return None


@dataclass(frozen=True, slots=True)
class GateResult:
    approved: bool
    reason: str
    baseline_key: str
    candidate_key: str
    phase: Phase
    horizon: Horizon
    frozen_at: datetime
    evaluated_at: datetime
    nights: int = 0
    observed_hours: float = 0.0
    baseline_mae_per_hour: float | None = None
    candidate_mae_per_hour: float | None = None
    baseline_p90_under_per_hour: float | None = None
    candidate_p90_under_per_hour: float | None = None
    retained: bool = False


def _valid_slots(slots: tuple[EnergySlot, ...]) -> bool:
    previous: datetime | None = None
    for slot in slots:
        start, end = utc(slot.start), utc(slot.end)
        if (
            start >= end
            or not finite(slot.energy_kwh)
            or slot.energy_kwh < 0
            or (previous is not None and start < previous)
        ):
            return False
        previous = end
    return True


def validate_record(record: ForecastRecord) -> None:
    """Reject a snapshot before it can become immutable evaluation evidence."""
    issued = utc(record.issued_at)
    ZoneInfo(record.time_zone)
    if not utc(record.data_as_of) <= issued < utc(record.model_end):
        raise ValueError("Invalid issue/data/horizon chronology")
    if not utc(record.night_start) < utc(record.sunrise) <= utc(record.model_end):
        raise ValueError("Invalid night geometry")
    if (
        not record.record_id
        or not record.night_id
        or record.basis != "sax_discharge_ac"
    ):
        raise ValueError("Missing forecast identity or unsupported basis")
    for series in (
        record.baseline,
        record.applied,
        record.candidate,
        *record.raw_profiles,
    ):
        if series is not None:
            if not series.model_key or not _valid_slots(series.intervals):
                raise ValueError("Invalid forecast series")
            canonical_json(json.loads(series.metadata_json))
    canonical_json(json.loads(record.planning_parameters_json))
    canonical_json(json.loads(record.live_metadata_json))
    if record.current_usable_kwh is not None and (
        not finite(record.current_usable_kwh) or record.current_usable_kwh < 0
    ):
        raise ValueError("Invalid usable energy")
    for band in record.bands:
        if (
            not utc(band.trained_until) < issued < utc(band.start) < utc(band.end)
            or not finite(band.lower_kwh)
            or not finite(band.upper_kwh)
            or not 0 <= band.lower_kwh <= band.upper_kwh
        ):
            raise ValueError("Invalid prospective uncertainty range")


def energy_between(
    slots: tuple[EnergySlot, ...], start: datetime, end: datetime
) -> float | None:
    """Integrate only completely covered time; a hole is not zero energy."""
    start, end = utc(start), utc(end)
    cursor, energy = start, 0.0
    for slot in slots:
        left, right = max(start, utc(slot.start)), min(end, utc(slot.end))
        if right <= left:
            continue
        if left != cursor:
            return None
        energy += (
            slot.energy_kwh
            * (right - left).total_seconds()
            / (utc(slot.end) - utc(slot.start)).total_seconds()
        )
        cursor = right
    return energy if cursor == end else None


def quantile(values: list[float], probability: float) -> float:
    """Hyndman/Fan type 7: linear interpolation at (n-1)*p."""
    if not values or not 0 <= probability <= 1:
        raise ValueError("Invalid quantile input")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def union_spans(spans: tuple[TimeSpan, ...]) -> tuple[TimeSpan, ...]:
    result: list[TimeSpan] = []
    for span in sorted(spans, key=lambda s: (s.start, s.end)):
        if result and span.start <= result[-1].end:
            previous = result.pop()
            result.append(TimeSpan(previous.start, max(previous.end, span.end)))
        else:
            result.append(span)
    return tuple(result)


def stable_id(value: Any) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()[:24]


def target_output_group(issued_at: datetime, start: datetime, time_zone: str) -> str:
    """Keep local issuance and target hours separate, including repeated DST hours."""
    zone = ZoneInfo(time_zone)
    issued_hour = issued_at.astimezone(zone).hour
    target_hour = start.astimezone(zone).hour
    return f"issued:{issued_hour:02d}|target:{target_hour:02d}"


def archived_baselines(
    records: tuple[ForecastRecord, ...], start: datetime, end: datetime, model_key: str
) -> tuple[ForecastSeriesRecord, ...]:
    """Return ex-ante uncorrected snapshots; the live consumer selects per segment."""
    return tuple(
        ForecastSeriesRecord(record.issued_at, series.intervals, model_key)
        for record in sorted(records, key=lambda item: (item.issued_at, item.record_id))
        if record.issued_at < end
        for series in (record.baseline, *record.raw_profiles)
        if series.model_key == model_key
        and any(slot.end > start and slot.start < end for slot in series.intervals)
    )


def evaluate_target(
    record: ForecastRecord,
    observations: tuple[DischargeObservation, ...],
    start: datetime,
    end: datetime,
    horizon: Horizon,
    phase: Phase,
) -> EvaluationPair:
    """Compare exactly identical observed partial times, never filling censored gaps."""
    start, end = utc(start), utc(end)
    if not utc(record.issued_at) < start < end:
        raise ValueError("Targets must follow the immutable forecast")
    if (
        phase == "night" and not record.night_start <= start < end <= record.sunrise
    ) or (phase == "dawn" and not record.sunrise <= start < end <= record.model_end):
        raise ValueError("Target crosses its astronomical class")
    relevant = [
        obs for obs in observations if utc(obs.start) < end and utc(obs.end) > start
    ]
    boundaries = sorted(
        {start, end}
        | {max(start, utc(obs.start)) for obs in relevant}
        | {min(end, utc(obs.end)) for obs in relevant}
    )
    if phase == "dawn":
        # SAX discharge in sunlight is net of PV, unlike extrapolated night load.
        relevant = []
        boundaries = [start, end]
    totals = [0.0, 0.0, 0.0, 0.0]
    spans: list[TimeSpan] = []
    excluded: defaultdict[str, float] = defaultdict(float)
    candidate_complete = True
    applied_complete = True
    for left, right in zip(boundaries, boundaries[1:], strict=False):
        covering = [obs for obs in relevant if obs.start <= left and obs.end >= right]
        seconds = (right - left).total_seconds()
        if len(covering) != 1:
            reason = (
                "dawn_load_unobservable"
                if phase == "dawn"
                else ("unknown" if not covering else "overlapping_observations")
            )
            excluded[reason] += seconds
            continue
        obs = covering[0]
        if obs.quality != "valid" or not finite(obs.energy_kwh) or obs.energy_kwh < 0:
            excluded[
                obs.quality if obs.quality in ("censored", "unknown") else "invalid"
            ] += seconds
            continue
        baseline = energy_between(record.baseline.intervals, left, right)
        applied = energy_between(record.applied.intervals, left, right)
        candidate = (
            energy_between(record.candidate.intervals, left, right)
            if record.candidate is not None
            else None
        )
        if record.candidate is not None and candidate is None and baseline is not None:
            candidate_complete = False
        if applied is None:
            applied_complete = False
        if baseline is None:
            excluded["forecast_coverage"] += seconds
            continue
        # Candidate holes invalidate its comparison, rather than improve its score
        # by hiding difficult observations from the baseline.
        if record.candidate is not None and candidate is None:
            candidate_complete = False
        totals[0] += baseline
        totals[1] += applied or 0.0
        totals[2] += candidate or 0.0
        totals[3] += obs.energy_kwh * seconds / (obs.end - obs.start).total_seconds()
        spans.append(TimeSpan(left, right))
    valid = union_spans(tuple(spans))
    complete = valid == (TimeSpan(start, end),) and not excluded
    return EvaluationPair(
        pair_id=stable_id((record.record_id, start, end, horizon, phase)),
        record_id=record.record_id,
        issued_at=record.issued_at,
        night_id=record.night_id,
        phase=phase,
        horizon=horizon,
        start=start,
        end=end,
        output_group=target_output_group(record.issued_at, start, record.time_zone),
        baseline_key=record.baseline.model_key,
        baseline_kwh=totals[0],
        applied_key=record.applied.model_key,
        applied_kwh=totals[1] if applied_complete else None,
        candidate_key=record.candidate.model_key if record.candidate else None,
        candidate_kwh=totals[2] if record.candidate and candidate_complete else None,
        observed_kwh=totals[3],
        valid_spans=valid,
        excluded_seconds=tuple(sorted(excluded.items())),
        complete=complete,
        basis=record.basis,
        bands=tuple(
            band for band in record.bands if band.start == start and band.end == end
        ),
    )


def canonical_targets(
    records: tuple[ForecastRecord, ...], as_of: datetime
) -> tuple[tuple[ForecastRecord, datetime, datetime, Horizon, Phase], ...]:
    """Fixed UTC targets; latest preceding issuance, rest-night first issuance only."""
    selected: dict[tuple, tuple[ForecastRecord, datetime, datetime, Horizon, Phase]] = (
        {}
    )
    for record in sorted(records, key=lambda item: (item.issued_at, item.record_id)):
        issued = utc(record.issued_at)
        if issued >= as_of:
            continue
        # Group independent configurations, never select whichever variant won.
        identity = (
            record.night_id,
            record.baseline.model_key,
            record.candidate.model_key if record.candidate else None,
            record.output_group,
            record.basis,
        )
        for minutes, horizon in ((15, "15m"), (60, "60m")):
            seconds = minutes * 60
            timestamp = (int(issued.timestamp()) // seconds + 1) * seconds
            start = datetime.fromtimestamp(timestamp, UTC)
            while start + timedelta(minutes=minutes) <= min(record.model_end, as_of):
                end = start + timedelta(minutes=minutes)
                phase = "night" if end <= record.sunrise else "dawn"
                if start >= record.night_start and (
                    phase == "night" or start >= record.sunrise
                ):
                    selected[(*identity, horizon, start)] = (
                        record,
                        start,
                        end,
                        horizon,
                        phase,
                    )
                start = end
        rest_key = (*identity, "rest_night")
        rest_start = max(record.night_start, issued + timedelta(microseconds=1))
        if rest_key not in selected and rest_start < record.sunrise <= as_of:
            selected[rest_key] = (
                record,
                rest_start,
                record.sunrise,
                "rest_night",
                "night",
            )
    return tuple(
        sorted(
            selected.values(), key=lambda item: (item[1], item[3], item[0].record_id)
        )
    )


def evaluate_records(
    records: tuple[ForecastRecord, ...],
    observations: tuple[DischargeObservation, ...],
    as_of: datetime,
    after: datetime | None = None,
) -> tuple[EvaluationPair, ...]:
    """Resolve only completed canonical targets using observations already available."""
    observations = tuple(obs for obs in observations if obs.end <= as_of)
    return tuple(
        evaluate_target(record, observations, start, end, horizon, phase)
        for record, start, end, horizon, phase in canonical_targets(records, as_of)
        if after is None or end > after
    )


def evaluate_gate(
    pairs: tuple[EvaluationPair, ...],
    *,
    baseline_key: str,
    candidate_key: str,
    phase: Phase,
    horizon: Horizon,
    frozen_at: datetime,
    as_of: datetime,
) -> GateResult:
    """Version 1: 14 prospective nights, mean MAE -5%, P90 undershoot <=+5%."""
    nights: defaultdict[str, list[EvaluationPair]] = defaultdict(list)
    coverage_mismatch = False
    for pair in pairs:
        matching = (
            pair.baseline_key == baseline_key
            and pair.candidate_key == candidate_key
            and pair.phase == phase
            and pair.horizon == horizon
            and pair.basis == "sax_discharge_ac"
            and frozen_at <= pair.issued_at < pair.start < pair.end <= as_of
            and pair.observed_hours > 0
        )
        if matching and pair.candidate_kwh is None:
            coverage_mismatch = True
        if (
            matching
            and pair.candidate_kwh is not None
            and (horizon != "rest_night" or pair.complete)
        ):
            nights[pair.night_id].append(pair)
    base_mae: list[float] = []
    cand_mae: list[float] = []
    base_under: list[float] = []
    cand_under: list[float] = []
    total_hours = 0.0
    for values in nights.values():
        values.sort(key=lambda item: (item.start, item.issued_at, item.pair_id))
        # Defensive against imported duplicates and accidental mixed raster classes.
        canonical: list[EvaluationPair] = []
        for pair in values:
            if not canonical or pair.start >= canonical[-1].end:
                canonical.append(pair)
        hours = sum(
            (span.end - span.start).total_seconds() / 3600
            for span in union_spans(
                tuple(s for pair in canonical for s in pair.valid_spans)
            )
        )
        if hours < 1.0 - 1e-9:
            continue
        total_hours += hours
        base_mae.append(
            sum(abs(p.observed_kwh - p.baseline_kwh) for p in canonical) / hours
        )
        cand_mae.append(
            sum(abs(p.observed_kwh - p.candidate_kwh) for p in canonical) / hours
        )
        base_under.append(
            sum(max(p.observed_kwh - p.baseline_kwh, 0) for p in canonical) / hours
        )
        cand_under.append(
            sum(max(p.observed_kwh - p.candidate_kwh, 0) for p in canonical) / hours
        )
    count = len(base_mae)
    base = sum(base_mae) / count if count else None
    candidate = sum(cand_mae) / count if count else None
    under_base = quantile(base_under, 0.9) if count else None
    under_candidate = quantile(cand_under, 0.9) if count else None
    reason = "insufficient_comparable_nights"
    approved = False
    if coverage_mismatch:
        reason = "candidate_coverage_mismatch"
    elif count >= 14 and total_hours >= 14 - 1e-9:
        if base == 0:
            reason = "perfect_baseline"
        elif candidate <= base * 0.95 and under_candidate <= under_base * 1.05:
            reason, approved = "approved", True
        else:
            reason = "candidate_not_better"
    return GateResult(
        approved,
        reason,
        baseline_key,
        candidate_key,
        phase,
        horizon,
        frozen_at,
        as_of,
        count,
        total_hours,
        base,
        candidate,
        under_base,
        under_candidate,
    )


def evaluation_summary(
    pairs: tuple[EvaluationPair, ...], model_key: str
) -> dict[str, Any]:
    """A compact diagnostic for a caller-selected single horizon/phase/model class."""
    values = [
        p for p in pairs if p.prediction(model_key) is not None and p.observed_hours > 0
    ]
    errors = [p.prediction(model_key) - p.observed_kwh for p in values]
    excluded: defaultdict[str, float] = defaultdict(float)
    for pair in values:
        for reason, seconds in pair.excluded_seconds:
            excluded[reason] += seconds / 3600
    return {
        "model_key": model_key,
        "basis": "sax_discharge_ac",
        "targets": len(values),
        "nights": len({p.night_id for p in values}),
        "observed_hours": sum(
            (s.end - s.start).total_seconds() / 3600
            for s in union_spans(tuple(s for p in values for s in p.valid_spans))
        ),
        "mae_kwh": sum(abs(e) for e in errors) / len(errors) if errors else None,
        "bias_kwh": sum(errors) / len(errors) if errors else None,
        "under_kwh": sum(max(-e, 0) for e in errors),
        "over_kwh": sum(max(e, 0) for e in errors),
        "excluded_hours": dict(excluded),
    }
