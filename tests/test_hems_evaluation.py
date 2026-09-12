"""Causal, paired evidence for REQ-HEMS-FORECAST-EVALUATION."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.sax_power.domain.hems import EnergySlot
from custom_components.sax_power.domain.hems_evaluation import (
    ForecastRecord,
    ForecastSeries,
    archived_baselines,
    canonical_targets,
    evaluate_gate,
    evaluate_records,
    evaluate_target,
    evaluation_summary,
    target_output_group,
    validate_record,
)
from custom_components.sax_power.domain.hems_load import DischargeObservation

NOW = datetime(2026, 1, 1, 0, tzinfo=UTC)


def forecast(at=NOW, *, base=2.0, candidate=1.0, key="candidate", night=None):
    start = at + timedelta(minutes=5)
    end = start + timedelta(hours=2)
    baseline = ForecastSeries("baseline", (EnergySlot(start, end, base * 2),))
    other = ForecastSeries(key, (EnergySlot(start, end, candidate * 2),))
    return ForecastRecord(
        str(at),
        at,
        at,
        night or str(at.date()),
        at - timedelta(hours=4),
        end,
        end + timedelta(hours=1),
        baseline,
        baseline,
        other,
    )


def observed(start, end, energy=1.0, quality="valid"):
    return DischargeObservation(start, end, energy, quality)


def pair_for_night(day, *, base=2.0, candidate=1.0, actual=1.0):
    record = forecast(NOW + timedelta(days=day), base=base, candidate=candidate)
    start = record.issued_at + timedelta(hours=1)
    end = start + timedelta(hours=1)
    return evaluate_target(
        record, (observed(start, end, actual),), start, end, "60m", "night"
    )


def test_only_common_observed_parts_and_true_zero_are_evidence():
    record = forecast()
    start, end = NOW + timedelta(hours=1), NOW + timedelta(hours=2)
    middle = start + timedelta(minutes=30)
    pair = evaluate_target(
        record,
        (observed(start, middle, 0), observed(middle, end, 0, "censored")),
        start,
        end,
        "60m",
        "night",
    )
    assert pair.observed_kwh == 0
    assert pair.observed_hours == 0.5
    assert pair.baseline_kwh == 1
    assert pair.candidate_kwh == 0.5
    assert not pair.complete
    assert pair.excluded_seconds == (("censored", 1800),)
    summary = evaluation_summary((pair,), "baseline")
    assert summary["bias_kwh"] == summary["over_kwh"] == 1
    assert summary["under_kwh"] == 0


def test_candidate_missing_coverage_cannot_hide_bad_forecasts():
    record = forecast()
    start, end = NOW + timedelta(hours=1), NOW + timedelta(hours=2)
    candidate = replace(
        record.candidate,
        intervals=(EnergySlot(start, start + timedelta(minutes=30), 0.5),),
    )
    pair = evaluate_target(
        replace(record, candidate=candidate),
        (observed(start, end),),
        start,
        end,
        "60m",
        "night",
    )
    assert pair.candidate_kwh is None
    assert pair.observed_hours == 1
    assert pair.baseline_kwh == 2
    assert pair.complete  # The baseline's full observed target is still usable.


def test_overlapping_unknown_observations_never_double_count():
    record = forecast()
    start, end = NOW + timedelta(hours=1), NOW + timedelta(hours=2)
    pair = evaluate_target(
        record, (observed(start, end), observed(start, end)), start, end, "60m", "night"
    )
    assert pair.observed_hours == 0
    assert pair.excluded_seconds == (("overlapping_observations", 3600),)


def test_canonical_latest_preceding_and_rest_first_no_hindsight():
    first = forecast(NOW + timedelta(minutes=1))
    second = replace(
        forecast(NOW + timedelta(minutes=10)),
        night_id=first.night_id,
        sunrise=first.sunrise,
        model_end=first.model_end,
    )
    exact = replace(
        second,
        record_id="at-start",
        issued_at=NOW + timedelta(hours=1),
        data_as_of=NOW + timedelta(hours=1),
    )
    targets = canonical_targets((first, second, exact), NOW + timedelta(hours=3))
    chosen = [
        r
        for r, start, _, horizon, _ in targets
        if start == NOW + timedelta(hours=1) and horizon == "60m"
    ]
    assert chosen == [second]
    assert [r for r, _, _, horizon, _ in targets if horizon == "rest_night"] == [first]
    assert all(r.issued_at < start for r, start, *_ in targets)


def test_future_measurements_and_future_targets_do_not_leak():
    record = forecast()
    future = observed(NOW + timedelta(hours=1), NOW + timedelta(hours=2), 999)
    pairs = evaluate_records((record,), (future,), NOW + timedelta(hours=1, minutes=30))
    assert all(pair.end <= NOW + timedelta(hours=1, minutes=30) for pair in pairs)
    assert all(pair.observed_kwh == 0 for pair in pairs)


def test_gate_requires_14_distinct_nights_and_one_hour_each():
    pairs = tuple(pair_for_night(day) for day in range(14))
    kwargs = dict(
        baseline_key="baseline",
        candidate_key="candidate",
        phase="night",
        horizon="60m",
        frozen_at=NOW - timedelta(days=1),
        as_of=NOW + timedelta(days=15),
    )
    assert not evaluate_gate(pairs[:-1], **kwargs).approved
    result = evaluate_gate(pairs, **kwargs)
    assert result.approved
    assert result.nights == 14
    assert result.observed_hours == 14
    assert result.baseline_mae_per_hour == 1
    assert result.candidate_mae_per_hour == 0
    assert not evaluate_gate((pairs[0],) * 100, **kwargs).approved
    assert not evaluate_gate(pairs, **{**kwargs, "phase": "dawn"}).approved
    assert not evaluate_gate(
        pairs, **{**kwargs, "frozen_at": NOW + timedelta(days=1)}
    ).approved


def test_perfect_baseline_and_worse_underestimate_prevent_approval():
    kwargs = dict(
        baseline_key="baseline",
        candidate_key="candidate",
        phase="night",
        horizon="60m",
        frozen_at=NOW - timedelta(days=1),
        as_of=NOW + timedelta(days=15),
    )
    perfect = tuple(pair_for_night(day, base=1, candidate=1) for day in range(14))
    assert evaluate_gate(perfect, **kwargs).reason == "perfect_baseline"
    under = tuple(pair_for_night(day, base=2, candidate=0.9) for day in range(14))
    assert evaluate_gate(under, **kwargs).reason == "candidate_not_better"


def test_raw_live_basis_never_uses_corrected_applied_output():
    record = forecast()
    raw = replace(record.candidate, model_key="raw")
    record = replace(record, applied=record.candidate, raw_profiles=(raw,))
    assert (
        archived_baselines((record,), NOW, NOW + timedelta(hours=2), "raw")[0].intervals
        == raw.intervals
    )
    assert (
        archived_baselines((record,), NOW, NOW + timedelta(hours=2), "candidate") == ()
    )


def test_dst_real_duration_and_explicit_issuance_target_classes():
    first = datetime(2026, 10, 25, 0, 55, tzinfo=UTC)
    target = datetime(2026, 10, 25, 1, tzinfo=UTC)
    assert target_output_group(first, target, "Europe/Berlin") == "issued:02|target:02"
    assert (
        target_output_group(first - timedelta(hours=1), target, "Europe/Berlin")
        == "issued:01|target:02"
    )


def test_invalid_future_data_or_nonfinite_forecast_rejected():
    record = forecast()
    with pytest.raises(ValueError):
        validate_record(replace(record, data_as_of=NOW + timedelta(seconds=1)))
    with pytest.raises(ValueError):
        validate_record(
            replace(
                record,
                baseline=ForecastSeries(
                    "broken", (EnergySlot(NOW, NOW + timedelta(hours=1), float("nan")),)
                ),
            )
        )


def test_dawn_free_discharge_does_not_prove_gross_load_before_pv_subtraction():
    record = forecast()
    start, end = record.sunrise, record.model_end
    pair = evaluate_target(record, (observed(start, end),), start, end, "60m", "dawn")
    assert pair.observed_hours == 0
    assert not pair.complete
    assert pair.excluded_seconds == (("dawn_load_unobservable", 3600),)


def test_skipping_a_difficult_target_cannot_approve_reduced_candidate_coverage():
    pairs = tuple(pair_for_night(day) for day in range(14))
    missing = replace(pair_for_night(15), candidate_kwh=None)
    result = evaluate_gate(
        (*pairs, missing),
        baseline_key="baseline",
        candidate_key="candidate",
        phase="night",
        horizon="60m",
        frozen_at=NOW - timedelta(days=1),
        as_of=NOW + timedelta(days=17),
    )
    assert not result.approved
    assert result.reason == "candidate_coverage_mismatch"
