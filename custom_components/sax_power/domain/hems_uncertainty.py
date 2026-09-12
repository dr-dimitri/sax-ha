"""Prospective display-only load ranges (REQ-HEMS-FORECAST-UNCERTAINTY)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from .hems_evaluation import (
    EvaluationPair,
    ForecastBand,
    Horizon,
    Phase,
    canonical_json,
    finite,
    quantile,
    stable_id,
    utc,
)

METHOD_VERSION = "signed-target-error:p10-p90:hyndman-fan-7:v1"


@dataclass(frozen=True, slots=True)
class UncertaintyClass:
    model_key: str
    horizon: Horizon = "60m"
    phase: Phase = "night"
    output_group: str = "default"
    basis: str = "sax_discharge_ac"

    @property
    def identifier(self) -> str:
        return canonical_json(asdict(self))


@dataclass(frozen=True, slots=True)
class UncertaintyModel:
    target_class: UncertaintyClass
    trained_until: datetime
    training_nights: int
    lower_error_kwh: float
    upper_error_kwh: float
    method_id: str
    training_pair_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class UncertaintyResult:
    status: str
    reason: str
    expected_kwh: float | None = None
    lower_kwh: float | None = None
    upper_kwh: float | None = None
    start: datetime | None = None
    end: datetime | None = None
    training_nights: int = 0
    validation_nights: int = 0
    hits: int = 0
    hit_rate: float | None = None
    mean_width_kwh: float | None = None
    last_validation_at: datetime | None = None
    candidate_band: ForecastBand | None = None
    selection_bias: str = "observed_free_sax_discharge_only"


def _class_pairs(
    pairs: tuple[EvaluationPair, ...], target_class: UncertaintyClass, as_of: datetime
) -> tuple[EvaluationPair, ...]:
    """The first canonical target of a preselected output class per local night."""
    selected: dict[str, EvaluationPair] = {}
    for pair in sorted(pairs, key=lambda p: (p.start, p.issued_at, p.pair_id)):
        if (
            pair.horizon != target_class.horizon
            or pair.phase != target_class.phase
            or pair.output_group != target_class.output_group
            or pair.basis != target_class.basis
            or pair.prediction(target_class.model_key) is None
            or pair.end > as_of
        ):
            continue
        # Select first, then test quality. Picking the first *successful* target
        # would silently optimize the sample selection after seeing observations.
        selected.setdefault(pair.night_id, pair)
    return tuple(p for p in selected.values() if p.complete)


def train_uncertainty(
    pairs: tuple[EvaluationPair, ...],
    target_class: UncertaintyClass,
    as_of: datetime,
) -> UncertaintyModel | None:
    """Freeze a range after 60 full nights; later validation cannot train it."""
    if target_class.horizon not in ("60m", "rest_night"):
        return None
    values = _class_pairs(pairs, target_class, utc(as_of))
    if len(values) < 60:
        return None
    training = values[-60:]
    errors = [p.observed_kwh - p.prediction(target_class.model_key) for p in training]
    lower, upper = quantile(errors, 0.1), quantile(errors, 0.9)
    method_id = (
        f"{METHOD_VERSION}:{stable_id((target_class.identifier, as_of, lower, upper))}"
    )
    return UncertaintyModel(
        target_class,
        utc(as_of),
        60,
        lower,
        upper,
        method_id,
        tuple(pair.pair_id for pair in training),
    )


def training_count(
    pairs: tuple[EvaluationPair, ...], target_class: UncertaintyClass, as_of: datetime
) -> int:
    return len(_class_pairs(pairs, target_class, as_of))


def issue_band(
    model: UncertaintyModel,
    expected_kwh: float,
    start: datetime,
    end: datetime,
    issued_at: datetime,
) -> ForecastBand:
    """The band is a diagnostic snapshot, never a planner target or reserve."""
    if (
        not finite(expected_kwh)
        or expected_kwh < 0
        or not model.trained_until < utc(issued_at) < utc(start) < utc(end)
        or (model.target_class.horizon == "60m" and end - start != timedelta(hours=1))
    ):
        raise ValueError("Invalid prospective uncertainty target")
    return ForecastBand(
        model.target_class.identifier,
        model.target_class.model_key,
        start,
        end,
        max(0.0, expected_kwh + model.lower_error_kwh),
        max(0.0, expected_kwh + model.upper_error_kwh),
        model.method_id,
        model.trained_until,
    )


def assess_uncertainty(
    model: UncertaintyModel | None,
    pairs: tuple[EvaluationPair, ...],
    target_class: UncertaintyClass,
    *,
    expected_kwh: float | None,
    start: datetime,
    end: datetime,
    as_of: datetime,
) -> UncertaintyResult:
    """Require 24/30 later frozen targets; revoke on drift or staleness."""
    if model is None or model.target_class != target_class:
        return UncertaintyResult(
            "unavailable",
            "insufficient_training_nights",
            expected_kwh,
            start=start,
            end=end,
            training_nights=training_count(pairs, target_class, as_of),
        )
    training = {
        pair.pair_id: pair
        for pair in _class_pairs(pairs, target_class, model.trained_until)
    }
    if (
        len(model.training_pair_ids) != 60
        or not set(model.training_pair_ids) <= training.keys()
    ):
        return UncertaintyResult(
            "unavailable",
            "training_evidence_missing",
            expected_kwh,
            start=start,
            end=end,
            training_nights=len(set(model.training_pair_ids) & training.keys()),
        )
    qualified: list[tuple[EvaluationPair, ForecastBand]] = []
    for pair in _class_pairs(pairs, target_class, as_of):
        if pair.issued_at <= model.trained_until:
            continue
        expected_band = issue_band(
            model,
            pair.prediction(target_class.model_key),
            pair.start,
            pair.end,
            pair.issued_at,
        )
        for band in pair.bands:
            if (
                band.class_key == target_class.identifier
                and band.model_key == target_class.model_key
                and band.method_id == model.method_id
                and band.trained_until == model.trained_until
                and band.start == pair.start
                and band.end == pair.end
                and model.trained_until < pair.issued_at < pair.start
                and abs(band.lower_kwh - expected_band.lower_kwh) < 1e-9
                and abs(band.upper_kwh - expected_band.upper_kwh) < 1e-9
            ):
                qualified.append((pair, band))
                break
    latest = qualified[-30:]
    hits = sum(b.lower_kwh <= p.observed_kwh <= b.upper_kwh for p, b in latest)
    last_at = latest[-1][0].end if latest else None
    status, reason = "observing", "insufficient_validation_nights"
    if len(latest) >= 30:
        status, reason = (
            ("reliable", "validated")
            if hits >= 24
            else ("unavailable", "coverage_below_threshold")
        )
    if last_at is not None and as_of - last_at >= timedelta(days=30):
        status, reason = "stale", "validation_stale"
    if expected_kwh is None:
        status, reason = "unavailable", "forecast_coverage_missing"
    band = None
    if expected_kwh is not None and model.trained_until < as_of < start:
        band = issue_band(model, expected_kwh, start, end, as_of)
    return UncertaintyResult(
        status,
        reason,
        expected_kwh,
        lower_kwh=band.lower_kwh if band and status == "reliable" else None,
        upper_kwh=band.upper_kwh if band and status == "reliable" else None,
        start=start,
        end=end,
        training_nights=model.training_nights,
        validation_nights=len(latest),
        hits=hits,
        hit_rate=hits / len(latest) if latest else None,
        mean_width_kwh=(
            sum(b.upper_kwh - b.lower_kwh for _, b in latest) / len(latest)
            if latest
            else None
        ),
        last_validation_at=last_at,
        candidate_band=band,
    )
