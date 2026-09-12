"""Analytical night-profile tests for REQ-HEMS-LOAD-PROFILE."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.sax_power.domain.hems_load import (
    DischargeObservation,
    NightSpan,
    build_night_profile,
    forecast_night_load,
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
