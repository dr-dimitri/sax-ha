"""Empirical whole-target ranges remain a display-only prospective contract."""

from dataclasses import replace
from datetime import timedelta

import pytest

from custom_components.sax_power.domain.hems_uncertainty import (
    UncertaintyClass,
    assess_uncertainty,
    issue_band,
    train_uncertainty,
)
from tests.test_hems_evaluation import NOW, pair_for_night

CLASS = UncertaintyClass("baseline", output_group="issued:00|target:01")


def training():
    return tuple(
        pair_for_night(day, base=1, actual=0.5 + day / 59) for day in range(60)
    )


def validation(model, *, hits=24, count=30, offset=61):
    result = []
    for day in range(offset, offset + count):
        pair = pair_for_night(day, base=1, actual=1 if day - offset < hits else 2)
        band = issue_band(model, 1, pair.start, pair.end, pair.issued_at)
        result.append(replace(pair, bands=(band,)))
    return tuple(result)


def assess(model, pairs, day=92):
    as_of = NOW + timedelta(days=day)
    return assess_uncertainty(
        model,
        (*training(), *pairs),
        CLASS,
        expected_kwh=1,
        start=as_of + timedelta(hours=1),
        end=as_of + timedelta(hours=2),
        as_of=as_of,
    )


def test_requires_60_distinct_full_training_nights_and_signed_total_errors():
    pairs = training()
    as_of = NOW + timedelta(days=60)
    assert train_uncertainty(pairs[:-1], CLASS, as_of) is None
    assert train_uncertainty((pairs[0],) * 100, CLASS, as_of) is None
    assert (
        train_uncertainty(
            tuple(replace(p, complete=False) for p in pairs), CLASS, as_of
        )
        is None
    )
    model = train_uncertainty(pairs, CLASS, as_of)
    assert model.training_nights == 60
    assert model.lower_error_kwh == pytest.approx(-0.4)
    assert model.upper_error_kwh == pytest.approx(0.4)
    assert "hyndman-fan-7" in model.method_id


def test_29_30_validation_nights_and_23_24_hits():
    model = train_uncertainty(training(), CLASS, NOW + timedelta(days=60))
    assert assess(model, validation(model, count=29)).status == "observing"
    assert assess(model, validation(model, hits=23)).status == "unavailable"
    result = assess(model, validation(model, hits=24))
    assert result.status == "reliable"
    assert result.hit_rate == 0.8
    assert result.lower_kwh == pytest.approx(0.6)
    assert result.upper_kwh == pytest.approx(1.4)
    assert result.mean_width_kwh == pytest.approx(0.8)


def test_validation_requires_original_frozen_band_and_later_nights():
    model = train_uncertainty(training(), CLASS, NOW + timedelta(days=60))
    pairs = validation(model)
    assert (
        assess(model, tuple(replace(p, bands=()) for p in pairs)).validation_nights == 0
    )
    assert (
        assess(
            model,
            tuple(
                replace(p, bands=(replace(p.bands[0], method_id="other"),))
                for p in pairs
            ),
        ).validation_nights
        == 0
    )
    assert (
        assess(
            model, tuple(replace(p, issued_at=model.trained_until) for p in pairs)
        ).validation_nights
        == 0
    )
    assert assess(model, (pairs[0],) * 50).validation_nights == 1


def test_staleness_and_rolling_coverage_revoke_without_changing_point_forecast():
    model = train_uncertainty(training(), CLASS, NOW + timedelta(days=60))
    pairs = validation(model, hits=30)
    assert assess(model, pairs, day=121).status == "stale"
    next_pairs = validation(model, hits=0, count=7, offset=91)
    result = assess(model, (*pairs, *next_pairs), day=99)
    assert result.status == "unavailable"
    assert result.expected_kwh == 1
    assert result.lower_kwh is None
    assert result.hits == 23


def test_zero_clipping_is_real_zero_and_no_slot_quantiles_are_summed():
    model = train_uncertainty(training(), CLASS, NOW + timedelta(days=60))
    band = issue_band(
        model,
        0.1,
        NOW + timedelta(days=61, hours=1),
        NOW + timedelta(days=61, hours=2),
        NOW + timedelta(days=61),
    )
    assert band.lower_kwh == 0
    assert band.upper_kwh == pytest.approx(0.5)
    assert assess(model, ()).lower_kwh is None


def test_classes_and_first_canonical_target_do_not_mix():
    pairs = training()
    as_of = NOW + timedelta(days=60)
    for other in (
        replace(CLASS, phase="dawn"),
        replace(CLASS, horizon="rest_night"),
        replace(CLASS, model_key="other"),
        replace(CLASS, output_group="issued:22|target:01"),
    ):
        assert train_uncertainty(pairs, other, as_of) is None
    # An earlier censored target disqualifies its night. A later good target may
    # not be chosen retroactively to fill the 60-night requirement.
    earlier = replace(
        pairs[0],
        pair_id="earlier",
        start=pairs[0].start - timedelta(minutes=1),
        complete=False,
    )
    assert train_uncertainty((earlier, *pairs), CLASS, as_of) is None


def test_band_cannot_be_issued_at_or_after_target():
    model = train_uncertainty(training(), CLASS, NOW + timedelta(days=60))
    start = NOW + timedelta(days=61)
    with pytest.raises(ValueError):
        issue_band(model, 1, start, start + timedelta(hours=1), start)


def test_pruned_or_reclassified_training_evidence_retracts_band():
    pairs = training()
    model = train_uncertainty(pairs, CLASS, NOW + timedelta(days=60))
    as_of = NOW + timedelta(days=92)
    result = assess_uncertainty(
        model,
        (*pairs[1:], *validation(model)),
        CLASS,
        expected_kwh=1,
        start=as_of + timedelta(hours=1),
        end=as_of + timedelta(hours=2),
        as_of=as_of,
    )
    assert result.reason == "training_evidence_missing"
    assert result.lower_kwh is None


def test_arbitrarily_widened_bands_cannot_masquerade_as_frozen_method():
    model = train_uncertainty(training(), CLASS, NOW + timedelta(days=60))
    pairs = tuple(
        replace(pair, bands=(replace(pair.bands[0], upper_kwh=999),))
        for pair in validation(model)
    )
    assert assess(model, pairs).validation_nights == 0
