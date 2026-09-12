"""Kein Nachbestellen bei quantisiertem SOC (REQ-HEMS-RUNTIME)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.sax_power.domain.hems_progress import SocProgressLedger

NOW = datetime(2026, 9, 13, tzinfo=UTC)


def ledger(
    *, eta_charge: float = 0.95, eta_discharge: float = 0.95
) -> SocProgressLedger:
    result = SocProgressLedger()
    assert result.configure(
        capacity_kwh=10, eta_charge=eta_charge, eta_discharge=eta_discharge
    )
    return result


def sample(book: SocProgressLedger, seconds: float, power: object, soc: object = 20):
    return book.observe(
        at=NOW + timedelta(seconds=seconds), raw_soc=soc, storage_power_w=power
    )


def charged() -> SocProgressLedger:
    result = ledger()
    sample(result, 0, -6000)
    sample(result, 20, -6000)
    return result


def test_charge_credit_survives_replanning_stop_and_source_changes() -> None:
    """Der Ledger kennt keine Lade-Intent-/Plan-Reset-Bedingung."""
    book = charged()
    expected = 6000 * 20 / 3_600_000 * 0.95
    before = book.estimate(as_of=NOW + timedelta(seconds=20), raw_soc=20)
    assert before.correction_kwh == pytest.approx(expected)
    assert before.effective_soc == pytest.approx(20 + expected * 10)
    for second in (21, 22, 23):
        assert (
            book.estimate(as_of=NOW + timedelta(seconds=second), raw_soc=20) == before
        )
    stopped = sample(book, 25, 0)
    idle = sample(book, 30, 0)
    assert stopped.correction_kwh == pytest.approx(expected)
    assert idle.correction_kwh == pytest.approx(expected)
    assert book.configure(capacity_kwh=10, eta_charge=0.95, eta_discharge=0.95)
    assert sample(book, 35, 0).correction_kwh == pytest.approx(expected)


def test_real_discharge_debits_credit_and_pv_charging_replenishes_it() -> None:
    book = charged()
    start = sample(book, 25, 0).correction_kwh
    discharge = sample(book, 30, 3600)
    assert discharge.correction_kwh == pytest.approx(start - 0.005 / 0.95)
    stopped = sample(book, 35, 0)
    assert stopped.correction_kwh == pytest.approx(start - 0.01 / 0.95)
    first_pv = sample(book, 40, -3600)
    assert first_pv.correction_kwh == stopped.correction_kwh
    second_pv = sample(book, 45, -3600)
    assert second_pv.correction_kwh == pytest.approx(
        stopped.correction_kwh + 0.005 * 0.95
    )


def test_separate_charge_and_discharge_efficiencies() -> None:
    book = ledger(eta_charge=0.8, eta_discharge=0.5)
    sample(book, 0, -3600)
    assert sample(book, 10, -3600).correction_kwh == pytest.approx(0.008)
    assert sample(book, 20, 3600).correction_kwh == pytest.approx(-0.012)


def test_duplicate_and_out_of_order_samples_never_double_count() -> None:
    book = charged()
    before = book.dump()
    sample(book, 20, -6000)
    sample(book, 20, -999999)
    sample(book, 19, -6000)
    sample(book, 19, -6000, 19)
    assert book.dump() == before
    assert sample(book, 25, -6000).correction_kwh == pytest.approx(
        6000 * 25 / 3_600_000 * 0.95
    )


@pytest.mark.parametrize("new_soc", [19, 21, 20.1])
def test_changed_raw_soc_reanchors_without_reapplying_old_progress(
    new_soc: float,
) -> None:
    book = charged()
    result = sample(book, 25, -6000, new_soc)
    assert result.effective_soc == new_soc
    assert result.correction_kwh == 0
    assert sample(book, 30, -6000, new_soc).correction_kwh > 0


def test_changed_soc_seen_during_planning_cannot_resurrect_old_credit() -> None:
    book = charged()
    assert (
        book.estimate(as_of=NOW + timedelta(seconds=21), raw_soc=21).effective_soc == 21
    )
    assert (
        book.estimate(as_of=NOW + timedelta(seconds=22), raw_soc=20).correction_kwh == 0
    )


@pytest.mark.parametrize("power, expected", [(-100000, 21), (100000, 19)])
def test_correction_is_bounded_by_one_soc_percentage_point(
    power: float, expected: float
) -> None:
    book = ledger()
    sample(book, 0, power)
    result = sample(book, 30, power)
    assert result.effective_soc == expected
    assert abs(result.correction_kwh) == pytest.approx(0.1)


@pytest.mark.parametrize("soc,power", [(100, -3600), (0, 3600)])
def test_soc_stays_within_physical_zero_and_one_hundred(
    soc: float, power: float
) -> None:
    book = ledger()
    sample(book, 0, power, soc)
    assert sample(book, 10, power, soc).effective_soc == soc


@pytest.mark.parametrize("gap", [30.001, 60, 3600])
def test_unknown_gaps_never_extrapolate_previous_power(gap: float) -> None:
    book = charged()
    result = sample(book, 20 + gap, -6000)
    assert result.effective_soc == 20
    assert result.correction_kwh == 0
    assert result.reason == "progress_gap"
    assert sample(book, 25 + gap, -6000).correction_kwh > 0


def test_exact_freshness_boundary_and_stale_estimate() -> None:
    book = charged()
    assert (
        book.estimate(as_of=NOW + timedelta(seconds=50), raw_soc=20).correction_kwh > 0
    )
    assert (
        book.estimate(
            as_of=NOW + timedelta(seconds=50, microseconds=1), raw_soc=20
        ).effective_soc
        == 20
    )
    assert (
        book.estimate(as_of=NOW + timedelta(seconds=19), raw_soc=20).effective_soc == 20
    )
    assert sample(book, 50, -6000).correction_kwh == pytest.approx(
        6000 * 50 / 3_600_000 * 0.95
    )


def test_negative_correction_reanchors_when_raw_soc_falls() -> None:
    book = ledger()
    sample(book, 0, 3600)
    assert sample(book, 10, 3600).correction_kwh < 0
    result = sample(book, 20, 3600, 19)
    assert result.correction_kwh == 0 and result.effective_soc == 19


@pytest.mark.parametrize("power", [None, "unknown", float("nan"), float("inf"), True])
def test_invalid_power_breaks_evidence_chain(power: object) -> None:
    book = charged()
    assert sample(book, 25, power).correction_kwh == 0
    assert sample(book, 30, -6000).correction_kwh == 0
    assert sample(book, 35, -6000).correction_kwh > 0


@pytest.mark.parametrize("soc", [None, -1, 101, float("nan"), True])
def test_invalid_raw_soc_never_becomes_estimated_energy(soc: object) -> None:
    book = charged()
    assert sample(book, 25, -6000, soc).effective_soc is None
    assert (
        book.estimate(as_of=NOW + timedelta(seconds=25), raw_soc=soc).effective_soc
        is None
    )


@pytest.mark.parametrize(
    "change",
    [
        {"capacity_kwh": 11},
        {"eta_charge": 0.9},
        {"eta_discharge": 0.9},
        {"eta_charge": 0},
        {"eta_discharge": None},
        {"capacity_kwh": -1},
    ],
)
def test_changed_or_invalid_assumptions_do_not_reuse_old_kwh(
    change: dict[str, object],
) -> None:
    book = charged()
    book.configure(
        **{"capacity_kwh": 10, "eta_charge": 0.95, "eta_discharge": 0.95, **change}
    )
    assert (
        book.estimate(as_of=NOW + timedelta(seconds=20), raw_soc=20).correction_kwh == 0
    )
    assert book.dump() is None


def test_short_restart_retains_only_credit_after_possible_discharge() -> None:
    payload = charged().dump()
    assert payload is not None
    book = ledger()
    assert book.restore(
        payload,
        as_of=NOW + timedelta(seconds=22),
        raw_soc=20,
        max_discharge_power_w=4000,
    )
    result = book.estimate(as_of=NOW + timedelta(seconds=22), raw_soc=20)
    expected = payload["correction_kwh"] - 4000 / 0.95 * 2 / 3_600_000
    assert result.correction_kwh == pytest.approx(expected)
    assert result.effective_soc > 20
    assert result.observed_at == NOW + timedelta(seconds=20)
    assert book.dump() is None
    first_live = sample(book, 24, 0)
    assert first_live.correction_kwh == pytest.approx(
        expected - 4000 / 0.95 * 2 / 3_600_000
    )
    assert sample(book, 29, 0).correction_kwh == first_live.correction_kwh


@pytest.mark.parametrize("age", [-1, 30.001, 600])
def test_future_or_old_restart_evidence_is_not_accepted(age: float) -> None:
    book = ledger()
    assert not book.restore(
        charged().dump(),
        as_of=NOW + timedelta(seconds=20 + age),
        raw_soc=20,
        max_discharge_power_w=4000,
    )
    assert book.dump() is None


@pytest.mark.parametrize(
    "key,value",
    [
        ("version", True),
        ("version", 2),
        ("raw_soc", 21),
        ("capacity_kwh", 11),
        ("eta_charge", 0.9),
        ("eta_discharge", 0.8),
        ("correction_kwh", float("nan")),
        ("correction_kwh", 0.10001),
        ("observed_at", "2026-09-13T00:00:20"),
    ],
)
def test_restart_payload_requires_matching_valid_fresh_evidence(
    key: str, value: object
) -> None:
    payload = charged().dump()
    assert payload is not None
    payload[key] = value
    assert not ledger().restore(
        payload,
        as_of=NOW + timedelta(seconds=22),
        raw_soc=20,
        max_discharge_power_w=4000,
    )


@pytest.mark.parametrize("limit", [None, 0, -1, float("nan"), True])
def test_restart_needs_a_known_technical_discharge_limit(limit: object) -> None:
    assert not ledger().restore(
        charged().dump(),
        as_of=NOW + timedelta(seconds=22),
        raw_soc=20,
        max_discharge_power_w=limit,
    )


def test_stored_plan_alone_has_no_valid_progress_or_charging_authority() -> None:
    book = ledger()
    assert not book.restore(
        {"planned_grid_kwh": 0.1, "charge": True, "raw_soc": 20},
        as_of=NOW,
        raw_soc=20,
        max_discharge_power_w=4000,
    )
    payload = charged().dump()
    assert payload is not None
    assert len(payload) == 7
    assert json.loads(json.dumps(payload)) == payload
    assert not any(
        "plan" in key or "enabled" in key or key == "charge" for key in payload
    )


def test_restore_does_not_refresh_evidence_age_without_a_live_sample() -> None:
    book = ledger()
    assert book.restore(
        charged().dump(),
        as_of=NOW + timedelta(seconds=45),
        raw_soc=20,
        max_discharge_power_w=100,
    )
    assert (
        book.estimate(as_of=NOW + timedelta(seconds=50), raw_soc=20).correction_kwh > 0
    )
    assert (
        book.estimate(as_of=NOW + timedelta(seconds=51), raw_soc=20).correction_kwh == 0
    )


def test_first_live_sample_at_restore_time_becomes_real_baseline_once() -> None:
    book = ledger()
    at = NOW + timedelta(seconds=22)
    assert book.restore(
        charged().dump(), as_of=at, raw_soc=20, max_discharge_power_w=4000
    )
    remainder = book.estimate(as_of=at, raw_soc=20).correction_kwh
    first = sample(book, 22, -6000)
    assert first.correction_kwh == remainder
    assert first.observed_at == at
    checkpoint = book.dump()
    assert checkpoint is not None and checkpoint["observed_at"] == at.isoformat()
    sample(book, 22, -999999, 19)
    assert book.dump() == checkpoint
    assert sample(book, 27, -6000).correction_kwh == pytest.approx(
        remainder + 6000 * 5 / 3_600_000 * 0.95
    )


def test_first_live_soc_change_at_restore_time_reanchors_without_credit() -> None:
    book = ledger()
    at = NOW + timedelta(seconds=22)
    assert book.restore(
        charged().dump(), as_of=at, raw_soc=20, max_discharge_power_w=4000
    )
    result = sample(book, 22, -6000, 21)
    assert result.effective_soc == 21 and result.correction_kwh == 0


def test_missing_first_live_power_at_restore_time_invalidates_credit() -> None:
    book = ledger()
    at = NOW + timedelta(seconds=22)
    assert book.restore(
        charged().dump(), as_of=at, raw_soc=20, max_discharge_power_w=4000
    )
    assert sample(book, 22, None).correction_kwh == 0
    assert book.dump() is None


def test_repeated_dst_hour_uses_real_elapsed_seconds() -> None:
    zone = ZoneInfo("Europe/Berlin")
    before = datetime(2026, 10, 25, 2, 59, 55, tzinfo=zone, fold=0)
    after = datetime(2026, 10, 25, 2, 0, 5, tzinfo=zone, fold=1)
    book = ledger()
    book.observe(at=before, raw_soc=20, storage_power_w=-3600)
    result = book.observe(at=after, raw_soc=20, storage_power_w=-3600)
    assert result.correction_kwh == pytest.approx(0.01 * 0.95)


def test_naive_time_is_rejected_without_leaving_old_credit() -> None:
    book = charged()
    result = book.observe(
        at=NOW.replace(tzinfo=None), raw_soc=20, storage_power_w=-6000
    )
    assert result.correction_kwh == 0 and book.dump() is None


@pytest.mark.parametrize(
    "name,value",
    [
        ("max_sample_gap_seconds", 0),
        ("max_restore_age_seconds", 31),
        ("max_restore_age_seconds", True),
    ],
)
def test_evidence_lifetime_cannot_be_extended_indefinitely(
    name: str, value: object
) -> None:
    with pytest.raises(ValueError):
        SocProgressLedger(**{name: value})
