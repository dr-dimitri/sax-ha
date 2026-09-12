"""Analytical night-profile tests for REQ-HEMS-LOAD-PROFILE."""

import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.sax_power.domain.hems_load import (
    DischargeObservation,
    NightSpan,
    build_night_profile,
    build_weighted_profile,
    forecast_night_load,
    forecast_weighted_load,
)

NOW = datetime(2026, 9, 12, 22, tzinfo=UTC)
NIGHTS = tuple(
    NightSpan(
        datetime(2026, 9, day, 18, tzinfo=UTC),
        datetime(2026, 9, day + 1, 6, tzinfo=UTC),
    )
    for day in range(9, 13)
)


def observations(hours=(2, 2, 2), powers=(0.5, 0.5, 0.5), quality="valid"):
    return tuple(
        DischargeObservation(
            night.start, night.start + timedelta(hours=h), h * p, quality
        )
        for night, h, p in zip(NIGHTS, hours, powers, strict=False)
    )


def profile(values=None, **kwargs):
    return build_night_profile(
        observations() if values is None else values,
        kwargs.pop("nights", NIGHTS),
        as_of=kwargs.pop("as_of", NOW),
        evaluated_through=kwargs.pop("evaluated_through", NOW),
        zone=kwargs.pop("zone", UTC),
        **kwargs,
    )


def test_constant_load_and_explicit_pooled_dawn():
    """REQ-HEMS-LOAD-PROFILE: 500 W yields 0.125 kWh per real quarter."""
    learned = profile()
    assert learned.reason == "ok"
    assert learned.nights == 3
    assert learned.observed_hours == 6
    assert learned.coverage == pytest.approx(1 / 6)
    pieces = forecast_night_load(learned, NIGHTS[-1], zone=UTC)
    assert pieces[0].energy_kwh == pytest.approx(0.125)
    assert pieces[0].method == "pooled_night_estimate"
    assert pieces[-1].method == "pooled_dawn_estimate"
    assert pieces[-1].end == NIGHTS[-1].end + timedelta(hours=4)
    assert sum(piece.energy_kwh for piece in pieces) == pytest.approx(6)


@pytest.mark.parametrize(
    ("hours", "expected"),
    [
        ((2, 2, 2), "ok"),
        ((1, 1, 4), "ok"),
        ((1, 1, 3.999), "insufficient_history"),
        ((0.999, 3, 3), "insufficient_history"),
        ((3, 3), "insufficient_history"),
    ],
)
def test_independent_global_quality_boundaries(hours, expected):
    """REQ-HEMS-LOAD-PROFILE: three nights, one hour each, six hours total."""
    assert profile(observations(hours=hours)).reason == expected


def test_nights_have_equal_weight_in_pooled_estimate():
    """Long observed nights must not silently dominate the pooled night mean."""
    learned = profile(observations(hours=(1, 1, 4), powers=(0.1, 1.0, 0.4)))
    assert learned.pooled_kw == pytest.approx(0.5)
    assert learned.pooled_kw != pytest.approx(2.7 / 6)


def test_free_zero_is_valid_but_censored_zero_never_counts():
    """REQ-HEMS-LOAD-PROFILE: no load differs from inability to serve load."""
    assert profile(observations(powers=(0, 0, 0))).pooled_kw == 0
    censored = profile(observations(quality="censored"))
    assert censored.reason == "insufficient_history"
    assert censored.observed_hours == 0


def test_daily_control_pause_does_not_require_whole_night_coverage():
    """Own charging cannot permanently lock the model out of learning."""
    records = []
    for night in NIGHTS[:3]:
        records.extend(
            (
                DischargeObservation(
                    night.start, night.start + timedelta(hours=2), 0, "censored"
                ),
                DischargeObservation(
                    night.start + timedelta(hours=2), night.end, 5, "valid"
                ),
            )
        )
    assert profile(tuple(records)).reason == "ok"


@pytest.mark.parametrize("lag", [0, 899, 900])
def test_recent_quality_watermark_keeps_old_training_valid(lag):
    """Freshness concerns quality evaluation, not the last free discharge."""
    assert profile(evaluated_through=NOW - timedelta(seconds=lag)).reason == "ok"


@pytest.mark.parametrize("lag", [-1, 901])
def test_stale_or_future_watermark_is_rejected(lag):
    assert (
        profile(evaluated_through=NOW - timedelta(seconds=lag)).reason
        == "history_stale"
    )


def test_strict_168_hours_and_completed_nights():
    shifted = tuple(
        NightSpan(n.start - timedelta(days=4), n.end - timedelta(days=4))
        for n in NIGHTS
    )
    records = tuple(
        replace(
            item, start=item.start - timedelta(days=4), end=item.end - timedelta(days=4)
        )
        for item in observations()
    )
    # The first whole night starts before the rolling lower boundary.
    assert profile(records, nights=shifted).nights == 2
    current_only = (DischargeObservation(NIGHTS[-1].start, NOW, 2, "valid"),)
    assert profile(current_only).nights == 0


def test_daytime_energy_cannot_increase_night_prediction():
    daytime = DischargeObservation(
        datetime(2026, 9, 12, 10, tzinfo=UTC),
        datetime(2026, 9, 12, 12, tzinfo=UTC),
        20,
        "valid",
    )
    assert profile((*observations(), daytime)).pooled_kw == 0.5


def test_direct_slot_and_dawn_have_distinct_evidence():
    records = tuple(
        DischargeObservation(n.end - timedelta(hours=2), n.end, 1, "valid")
        for n in NIGHTS[:3]
    )
    learned = profile(
        records,
        as_of=NIGHTS[-1].end - timedelta(hours=1),
        evaluated_through=NIGHTS[-1].end - timedelta(hours=1),
    )
    pieces = forecast_night_load(learned, NIGHTS[-1], zone=UTC)
    assert pieces[0].method == "night_slot_mean"
    assert pieces[-1].method == "dawn_extrapolation"


def test_cutting_partial_quarters_preserves_real_energy():
    as_of = NOW + timedelta(minutes=7)
    learned = profile(as_of=as_of, evaluated_through=as_of)
    pieces = forecast_night_load(
        learned, NIGHTS[-1], zone=UTC, end=as_of + timedelta(minutes=20)
    )
    assert sum(item.energy_kwh for item in pieces) == pytest.approx(0.5 / 3)
    assert pieces[0].start == as_of
    assert pieces[-1].end == as_of + timedelta(minutes=20)


@pytest.mark.parametrize(
    "day", [datetime(2026, 3, 29, 0, tzinfo=UTC), datetime(2026, 10, 25, 0, tzinfo=UTC)]
)
def test_dst_projection_preserves_utc_energy(day):
    zone = ZoneInfo("Europe/Berlin")
    night = NightSpan(day - timedelta(hours=5), day + timedelta(hours=6))
    learned = replace(profile(), as_of=day)
    pieces = forecast_night_load(learned, night, zone=zone)
    assert sum(item.energy_kwh for item in pieces) == pytest.approx(5)
    assert all(
        left.end == right.start for left, right in zip(pieces, pieces[1:], strict=False)
    )


@pytest.mark.parametrize("energy", [-1, float("nan"), float("inf"), True])
def test_invalid_energy_is_not_silently_a_zero(energy):
    records = observations()
    assert (
        profile((replace(records[0], energy_kwh=energy), *records[1:])).reason
        == "history_invalid"
    )


def test_overlap_is_rejected_and_missing_geometry_explained():
    records = observations()
    assert profile((records[0], records[0], *records[1:])).reason == "history_invalid"
    assert profile(nights=()).reason == "unsupported_night_geometry"
    assert profile(evaluated_through=None).reason == "history_unavailable"


def test_outside_model_scope_produces_no_forecast():
    learned = replace(profile(), as_of=NIGHTS[-1].end + timedelta(hours=4))
    assert forecast_night_load(learned, NIGHTS[-1], zone=UTC) == ()


def weighted(values=None, **kwargs):
    return build_weighted_profile(
        observations() if values is None else values,
        kwargs.pop("nights", NIGHTS),
        as_of=kwargs.pop("as_of", NOW),
        evaluated_through=kwargs.pop("evaluated_through", NOW),
        zone=kwargs.pop("zone", UTC),
        **kwargs,
    )


def test_weighted_candidate_keeps_legacy_result_separate():
    records = observations(hours=(1, 1, 4), powers=(0.1, 1, 0.4))
    legacy = profile(records)
    candidate = weighted(records)
    weights = [
        math.exp(-(NOW - n.end).total_seconds() / (7 * 86400)) * hours / 12
        for n, hours in zip(NIGHTS, (1, 1, 4), strict=False)
    ]
    expected = sum(w * p for w, p in zip(weights, (0.1, 1, 0.4), strict=True)) / sum(
        weights
    )
    forecast, meta = forecast_weighted_load(candidate, NIGHTS[-1], zone=UTC)
    assert legacy.pooled_kw == pytest.approx(0.5)
    assert forecast.intervals[0].energy_kwh == pytest.approx(expected / 4)
    assert candidate.model_key == "weighted-v1:7d"
    assert meta[0].weight_sum == pytest.approx(sum(weights))
    assert meta[0].group == "pooled"


@pytest.mark.parametrize(
    "minutes,direct", [(1 / 60, False), (9.999, False), (10, True), (15, True)]
)
def test_weighted_slot_requires_ten_minutes_per_independent_night(minutes, direct):
    records = []
    for n in NIGHTS[:3]:
        records.extend(
            (
                DischargeObservation(n.start, n.start + timedelta(hours=2), 1, "valid"),
                DischargeObservation(
                    n.start + timedelta(hours=4),
                    n.start + timedelta(hours=4, minutes=minutes),
                    minutes / 60,
                    "valid",
                ),
            )
        )
    candidate = weighted(tuple(records))
    forecast, meta = forecast_weighted_load(candidate, NIGHTS[-1], zone=UTC)
    assert (meta[0].method == "weighted_slot") is direct
    if direct:
        assert forecast.intervals[0].energy_kwh == pytest.approx(0.25)
        assert meta[0].observed_minutes == pytest.approx(3 * minutes)


@pytest.mark.parametrize(
    "minutes,direct", [(1 / 60, False), (59.99, False), (60, True), (120, True)]
)
def test_weighted_dawn_requires_one_hour_per_night(minutes, direct):
    records = []
    for n in NIGHTS[:3]:
        records.extend(
            (
                DischargeObservation(n.start, n.start + timedelta(hours=2), 1, "valid"),
                DischargeObservation(
                    n.end - timedelta(minutes=minutes), n.end, minutes / 60, "valid"
                ),
            )
        )
    candidate = weighted(tuple(records))
    forecast, meta = forecast_weighted_load(candidate, NIGHTS[-1], zone=UTC)
    assert (meta[-1].method == "weighted_dawn") is direct
    if direct:
        assert forecast.intervals[-1].energy_kwh == pytest.approx(0.25)


@pytest.mark.parametrize(
    "days,allowed", [(7, True), (28, True), (14, False), (True, False), (7.0, False)]
)
def test_history_selection_is_explicit(days, allowed):
    if allowed:
        assert weighted(history_days=days).history_days == days
    else:
        with pytest.raises(ValueError):
            weighted(history_days=days)


def test_twenty_eight_days_do_not_manufacture_missing_history():
    candidate = weighted(history_days=28)
    assert candidate.nights == 3
    assert candidate.available_history_days == pytest.approx(3 + 4 / 24)
    assert candidate.model_key == "weighted-v1:28d"


def _weekly_cases(days):
    nights = tuple(
        NightSpan(
            NIGHTS[-1].start - timedelta(days=days_ago),
            NIGHTS[-1].end - timedelta(days=days_ago),
        )
        for days_ago in sorted(days, reverse=True)
    )
    records = tuple(
        DischargeObservation(n.start, n.end, 12 * (index + 1), "valid")
        for index, n in enumerate(nights)
    )
    return nights, records


@pytest.mark.parametrize(
    "days,group",
    [
        ((7, 14, 21), "same_weekday"),
        ((6, 7, 13), "weekend"),
        ((1, 2, 3), "all_nights"),
    ],
)
def test_weekday_group_fallback_uses_three_distinct_nights(days, group):
    nights, records = _weekly_cases(days)
    candidate = weighted(records, nights=nights, history_days=28)
    _, meta = forecast_weighted_load(candidate, NIGHTS[-1], zone=UTC)
    assert meta[0].group == group
    assert meta[0].sample_nights >= 3


def test_older_than_selected_window_cannot_supply_baseline_or_candidate():
    nights, records = _weekly_cases((8, 9, 10))
    assert weighted(records, nights=nights).reason == "insufficient_history"
    assert weighted(records, nights=nights, history_days=28).reason == "ok"
    assert profile(records, nights=nights).reason == "insufficient_history"


def test_dst_repeated_slot_counts_once_and_caps_duration_weight():
    zone = ZoneInfo("Europe/Berlin")
    start = datetime(2026, 10, 24, 18, tzinfo=UTC)
    nights = tuple(
        NightSpan(
            start - timedelta(days=d), start - timedelta(days=d) + timedelta(hours=12)
        )
        for d in (2, 1, 0)
    )
    as_of = datetime(2026, 10, 25, 22, tzinfo=UTC)
    records = tuple(DischargeObservation(n.start, n.end, 6, "valid") for n in nights)
    candidate = weighted(
        records, nights=nights, as_of=as_of, evaluated_through=as_of, zone=zone
    )
    samples = dict(candidate.slots)[8]
    assert len(samples) == 3
    repeated = samples[-1]
    assert repeated.observed_seconds == 1800
    assert repeated.power_kw == pytest.approx(0.5)
    assert repeated.weight == pytest.approx(
        math.exp(-(as_of - nights[-1].end).total_seconds() / (7 * 86400))
    )


def test_dst_partial_repeated_slot_weights_the_real_available_duration():
    zone = ZoneInfo("Europe/Berlin")
    night = NightSpan(
        datetime(2026, 10, 24, 18, tzinfo=UTC), datetime(2026, 10, 25, 6, tzinfo=UTC)
    )
    as_of = night.end + timedelta(hours=16)
    records = (
        DischargeObservation(night.start, night.start + timedelta(hours=2), 1, "valid"),
        DischargeObservation(
            datetime(2026, 10, 25, 0, tzinfo=UTC),
            datetime(2026, 10, 25, 0, 5, tzinfo=UTC),
            0.05,
            "valid",
        ),
        DischargeObservation(
            datetime(2026, 10, 25, 1, tzinfo=UTC),
            datetime(2026, 10, 25, 1, 5, tzinfo=UTC),
            0.05,
            "valid",
        ),
    )
    candidate = weighted(
        records, nights=(night,), as_of=as_of, evaluated_through=as_of, zone=zone
    )
    sample = dict(candidate.slots)[8][0]
    recency = math.exp(-(as_of - night.end).total_seconds() / (7 * 86400))
    assert sample.observed_seconds == 600
    assert sample.weight == pytest.approx(recency / 3)


@pytest.mark.parametrize(
    "quality,power,reason",
    [
        ("valid", 0, "ok"),
        ("censored", 0, "insufficient_history"),
        ("unknown", 1, "insufficient_history"),
        ("valid", 4.6, "ok"),
    ],
)
def test_weighted_quality_and_physical_high_load_are_preserved(quality, power, reason):
    candidate = weighted(observations(powers=(power,) * 3, quality=quality))
    assert candidate.reason == reason
    if reason == "ok":
        forecast, _ = forecast_weighted_load(candidate, NIGHTS[-1], zone=UTC)
        assert forecast.intervals[0].energy_kwh == pytest.approx(power / 4)


@pytest.mark.parametrize(
    "lag,reason", [(900, "ok"), (901, "history_stale"), (-1, "history_stale")]
)
def test_weighted_profile_preserves_freshness_boundary(lag, reason):
    assert weighted(evaluated_through=NOW - timedelta(seconds=lag)).reason == reason
