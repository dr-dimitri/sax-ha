"""Causal SAX live corrections, not device-control permissions (#233)."""

import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.sax_power.domain.hems import EnergySlot, LoadForecast
from custom_components.sax_power.domain.hems_live import (
    LIVE_FLAG,
    ArchivedLoadBasis,
    LiveAdjuster,
)
from custom_components.sax_power.domain.hems_load import DischargeObservation, NightSpan

NOW = datetime(2026, 9, 12, 22, tzinfo=UTC)
NIGHT = NightSpan(NOW - timedelta(hours=4), NOW + timedelta(hours=8))
KEY = "weighted-v1:7d"


def basis(at=NOW, power=0.5, night=NIGHT):
    end = night.end + timedelta(hours=4)
    return LoadForecast(
        intervals=(EnergySlot(at, end, power * (end - at).total_seconds() / 3600),),
        generated_at=at,
        evaluated_through=at,
        model_start=night.start,
        model_end=end,
    )


def observations(end=NOW, minutes=45, power=1.0, quality="valid"):
    start = end - timedelta(minutes=minutes)
    result = []
    while start < end:
        stop = min(start + timedelta(minutes=5), end)
        result.append(
            DischargeObservation(
                start, stop, power * (stop - start).total_seconds() / 3600, quality
            )
        )
        start = stop
    return tuple(result)


def archives(at=NOW, power=0.5, key=KEY):
    start = at - timedelta(minutes=45)
    return (
        ArchivedLoadBasis(
            start - timedelta(minutes=1), (EnergySlot(start, at, power * 0.75),), key
        ),
    )


def evaluate(adjuster, at=NOW, **changes):
    values = dict(
        basis=basis(at),
        observations=observations(at),
        archived_bases=archives(at),
        as_of=at,
        night=NIGHT,
        model_key=KEY,
        max_discharge_power_w=4600,
        archive_enabled=True,
        free_discharge=True,
    )
    values.update(changes)
    return adjuster.evaluate(**values)


@pytest.fixture
def adjuster():
    instance = LiveAdjuster()
    evaluate(instance, NOW - timedelta(minutes=45))
    return instance


def test_new_instance_waits_for_thirty_minutes_new_evidence():
    instance = LiveAdjuster()
    assert evaluate(instance).anchor is None
    assert evaluate(instance, NOW + timedelta(minutes=29)).anchor is None
    result = evaluate(instance, NOW + timedelta(minutes=30))
    assert result.anchor == NOW + timedelta(minutes=30)
    assert result.valid_minutes == 30


@pytest.mark.parametrize(
    "power,correction", [(1, 0.25), (0.5, 0), (0, -0.25), (4.6, 0.25)]
)
def test_measured_residual_is_damped_and_capped(adjuster, power, correction):
    result = evaluate(adjuster, observations=observations(power=power))
    assert result.reason == "adjusted"
    assert result.measured_kwh == pytest.approx(power * 0.75)
    assert result.expected_kwh == pytest.approx(0.375)
    assert result.correction_kw == pytest.approx(correction)
    assert result.expires_at == NOW + timedelta(hours=1)
    decay = math.log(2) / 1800
    expected_delta = correction / decay * (1 - 0.25) / 3600
    assert result.forecast.intervals[0].energy_kwh == pytest.approx(6 + expected_delta)


def test_zero_basis_can_receive_small_positive_correction(adjuster):
    result = evaluate(
        adjuster,
        basis=basis(power=0),
        archived_bases=archives(power=0),
        observations=observations(power=0.6),
    )
    assert result.correction_kw == pytest.approx(0.1)
    assert result.forecast.intervals[0].energy_kwh > 0


@pytest.mark.parametrize("minutes,qualified", [(29, False), (30, True), (45, True)])
def test_pairwise_minimum_observation_boundary(adjuster, minutes, qualified):
    result = evaluate(adjuster, observations=observations(minutes=minutes))
    assert (result.anchor is not None) is qualified
    if qualified:
        assert result.valid_minutes == minutes


def test_censored_and_unknown_segments_never_enter_residual_denominator(adjuster):
    items = list(observations())
    items[0] = replace(items[0], quality="censored", energy_kwh=0)
    items[1] = replace(items[1], quality="unknown", energy_kwh=0)
    result = evaluate(adjuster, observations=tuple(items))
    assert result.valid_minutes == 35
    assert result.measured_kwh == pytest.approx(35 / 60)
    assert result.correction_kw == pytest.approx(0.25)
    items[2] = replace(items[2], quality="censored", energy_kwh=0)
    items[3] = replace(items[3], quality="censored", energy_kwh=0)
    other = LiveAdjuster()
    evaluate(other, NOW - timedelta(minutes=45))
    assert evaluate(other, observations=tuple(items)).anchor is None


def test_single_real_peak_remains_measured_but_does_not_project_unbounded(adjuster):
    items = list(observations(power=0.5))
    items[4] = replace(items[4], energy_kwh=4.6 / 12)
    result = evaluate(adjuster, observations=tuple(items))
    assert result.measured_kwh == pytest.approx(0.5 * 40 / 60 + 4.6 * 5 / 60)
    assert result.correction_kw == pytest.approx((4.6 - 0.5) * 5 / 45 / 2)


def test_only_ex_ante_latest_uncorrected_matching_basis_is_used(adjuster):
    old = archives(power=0.1)[0]
    newer = replace(
        archives(power=0.8)[0], issued_at=old.issued_at + timedelta(seconds=1)
    )
    future = replace(archives(power=5)[0], issued_at=NOW + timedelta(seconds=1))
    wrong = replace(archives(power=5)[0], model_key="other")
    result = evaluate(adjuster, archived_bases=(future, newer, old, wrong))
    assert result.expected_kwh == pytest.approx(0.8 * 0.75)
    assert result.correction_kw == pytest.approx(0.1)


def test_later_forecast_cannot_change_already_elapsed_targets(adjuster):
    old = archives(power=0.2)[0]
    later = replace(archives(power=0.8)[0], issued_at=NOW - timedelta(minutes=20))
    result = evaluate(adjuster, archived_bases=(later, old))
    assert result.expected_kwh == pytest.approx(0.2 * 30 / 60 + 0.8 * 15 / 60)


def test_conflicting_same_time_or_missing_bases_do_not_manufacture_pairs(adjuster):
    ambiguous = (archives(power=0.2)[0], archives(power=0.8)[0])
    assert evaluate(adjuster, archived_bases=ambiguous).anchor is None
    assert evaluate(adjuster, archived_bases=()).anchor is None


def test_short_archive_coverage_uses_only_common_seconds(adjuster):
    source = ArchivedLoadBasis(
        NOW - timedelta(hours=1),
        (EnergySlot(NOW - timedelta(minutes=30), NOW, 0.25),),
        KEY,
    )
    result = evaluate(adjuster, archived_bases=(source,))
    assert result.valid_minutes == 30
    assert result.measured_kwh == pytest.approx(0.5)
    assert result.expected_kwh == pytest.approx(0.25)


@pytest.mark.parametrize("age,qualified", [(300, True), (301, False)])
def test_last_paired_evidence_freshness(adjuster, age, qualified):
    end = NOW - timedelta(seconds=age)
    result = evaluate(adjuster, observations=observations(end))
    assert (result.anchor is not None) is qualified


def test_repeated_input_does_not_renew_or_accumulate(adjuster):
    first = evaluate(adjuster)
    second = evaluate(adjuster)
    assert second.anchor == first.anchor
    assert second.forecast == first.forecast
    assert second.reason == "unchanged_evidence"
    later = evaluate(
        adjuster,
        NOW + timedelta(minutes=30),
        observations=observations(),
        archived_bases=archives(),
    )
    assert later.anchor == NOW
    assert later.remaining_seconds == 1800
    decay = math.log(2) / 1800
    delta = 0.25 / decay * (0.5 - 0.25) / 3600
    assert later.forecast.intervals[0].energy_kwh == pytest.approx(5.75 + delta)
    expired = evaluate(adjuster, NOW + timedelta(hours=1), archive_enabled=False)
    assert expired.reason == "correction_expired"
    assert expired.forecast == basis(NOW + timedelta(hours=1))


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"archive_enabled": False}, "archive_disabled"),
        ({"free_discharge": False}, "discharge_not_free"),
    ],
)
def test_censoring_or_archive_off_only_decays_existing_anchor(
    adjuster, changes, reason
):
    evaluate(adjuster)
    result = evaluate(adjuster, NOW + timedelta(minutes=5), **changes)
    assert result.reason == reason
    assert result.anchor == NOW
    assert result.expires_at == NOW + timedelta(hours=1)
    assert result.remaining_seconds == 3300


def test_archive_off_cannot_establish_first_anchor(adjuster):
    assert evaluate(adjuster, archive_enabled=False).anchor is None


def test_dawn_only_returns_decaying_shadow_and_never_learns_daytime():
    night = replace(NIGHT, end=NOW + timedelta(minutes=10))
    instance = LiveAdjuster()
    evaluate(
        instance,
        NOW - timedelta(minutes=45),
        night=night,
        basis=basis(NOW - timedelta(minutes=45), night=night),
    )
    result = evaluate(instance, night=night, basis=basis(night=night))
    assert result.anchor == NOW
    dawn_at = NOW + timedelta(minutes=20)
    dawn = evaluate(
        instance,
        dawn_at,
        night=night,
        basis=basis(dawn_at, night=night),
        observations=observations(dawn_at, power=4),
    )
    assert dawn.reason == "dawn_no_new_evidence"
    assert dawn.anchor == NOW


def test_mode_key_change_and_reset_require_new_evidence(adjuster):
    evaluate(adjuster)
    assert evaluate(adjuster, model_key="weighted-v1:28d").anchor is None
    adjuster.reset()
    assert evaluate(adjuster).anchor is None


def test_backward_clock_does_not_reuse_future_anchor(adjuster):
    evaluate(adjuster)
    earlier = evaluate(adjuster, NOW - timedelta(minutes=5))
    assert earlier.anchor is None


@pytest.mark.parametrize(
    "changes",
    [
        {"basis": replace(basis(), quality_reason="insufficient_history")},
        {"max_discharge_power_w": None},
        {"max_discharge_power_w": float("nan")},
        {"max_discharge_power_w": 0},
    ],
)
def test_invalid_basis_or_physical_limit_cannot_be_repaired_by_live_data(
    adjuster, changes
):
    evaluate(adjuster)
    assert evaluate(adjuster, **changes).reason == "invalid_basis"


def test_already_corrected_forecast_is_not_accepted_as_new_basis(adjuster):
    first = evaluate(adjuster)
    assert LIVE_FLAG in first.forecast.quality_flags
    assert evaluate(adjuster, basis=first.forecast).reason == "invalid_basis"


def test_future_and_overlapping_observations_do_not_supply_evidence(adjuster):
    assert (
        evaluate(adjuster, observations=observations(NOW + timedelta(hours=1))).anchor
        is None
    )
    items = observations()
    assert (
        evaluate(adjuster, observations=(items[0], *items)).reason
        == "invalid_observations"
    )


def test_negative_correction_clips_at_zero_within_a_future_interval(adjuster):
    result = evaluate(
        adjuster, basis=basis(power=0.1), observations=observations(power=0)
    )
    assert result.correction_kw == pytest.approx(-0.25)
    # Throughout the first hour residual magnitude exceeds 0.0625 kW;
    # crossing 0.1 occurs at ~39.66 min and must be integrated, not averaged.
    assert 1.1 < result.forecast.intervals[0].energy_kwh < 1.12


def test_technical_power_limit_clips_instantaneous_future_load(adjuster):
    result = evaluate(adjuster, basis=basis(power=4.5))
    assert 54 < result.forecast.intervals[0].energy_kwh < 54.1
