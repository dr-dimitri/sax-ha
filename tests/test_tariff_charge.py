"""Tarifgebundene Hysterese: REQ-TIME-OF-USE-CHARGE-SOURCE."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from datetime import time as dt_time
from zoneinfo import ZoneInfo

import pytest

from custom_components.sax_power.application.tariff_charge import tariff_charge_state
from custom_components.sax_power.application.timed_charge import is_tariff_source
from custom_components.sax_power.domain.tariff import (
    DailyPriceWindow,
    TariffConfig,
    TariffType,
)

BERLIN = ZoneInfo("Europe/Berlin")
ALL_MONTHS = frozenset(range(1, 13))


def _local(value: str) -> datetime:
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        return moment.replace(tzinfo=BERLIN)
    return moment.astimezone(BERLIN)


def _config(*windows: DailyPriceWindow, base: float = 0.3) -> TariffConfig:
    return TariffConfig(
        tariff_type=TariffType.TIME_OF_USE,
        feed_in_price_eur_kwh=0.08,
        tou_base_price_eur_kwh=base,
        windows=windows,
    )


def test_source_and_expiry_remain_stable_through_the_whole_tariff_phase() -> None:
    config = _config(
        DailyPriceWindow(dt_time(22), dt_time(0), 0.1),
        DailyPriceWindow(dt_time(0), dt_time(2), 0.1),
        DailyPriceWindow(dt_time(2), dt_time(6), 0.1),
    )

    states = [
        tariff_charge_state(config, _local(moment), ALL_MONTHS)
        for moment in (
            "2026-09-30T22:00:00",
            "2026-09-30T23:59:59",
            "2026-10-01T00:00:00",
            "2026-10-01T02:00:00",
            "2026-10-01T05:59:59",
        )
    ]

    assert states[0] is not None
    assert all(state == states[0] for state in states)
    assert states[0].start == dt_time(22)
    assert states[0].end == dt_time(6)
    assert states[0].expires_at == datetime(2026, 10, 1, 4, tzinfo=UTC)
    assert is_tariff_source(states[0].source)


@pytest.mark.parametrize(
    ("months", "moments", "start", "end", "expiry"),
    [
        (
            {9},
            ("2026-09-30T22:00:00", "2026-09-30T23:30:00"),
            dt_time(22),
            dt_time(0),
            "2026-10-01T00:00:00",
        ),
        (
            {10},
            ("2026-10-01T00:00:00", "2026-10-01T05:30:00"),
            dt_time(0),
            dt_time(6),
            "2026-10-01T06:00:00",
        ),
    ],
)
def test_active_months_clip_the_phase_without_changing_its_identity_mid_phase(
    months: set[int],
    moments: tuple[str, str],
    start: dt_time,
    end: dt_time,
    expiry: str,
) -> None:
    config = _config(DailyPriceWindow(dt_time(22), dt_time(6), 0.1))

    state = tariff_charge_state(config, _local(moments[0]), months)

    assert state is not None
    assert state == tariff_charge_state(config, _local(moments[1]), months)
    assert state.start == start
    assert state.end == end
    assert state.expires_at == _local(expiry).astimezone(UTC)


@pytest.mark.parametrize(
    ("moment", "months"),
    [
        ("2026-09-30T22:00:00", {10}),
        ("2026-10-01T00:00:00", {9}),
        ("2026-09-30T22:00:00", set()),
        ("2026-10-01T06:00:00", ALL_MONTHS),
    ],
)
def test_inactive_month_or_expired_phase_cannot_arm_hysteresis(
    moment: str, months: set[int]
) -> None:
    config = _config(DailyPriceWindow(dt_time(22), dt_time(6), 0.1))

    assert tariff_charge_state(config, _local(moment), months) is None


def test_tariff_edit_invalidates_source_even_when_current_price_and_end_match() -> None:
    config = _config(
        DailyPriceWindow(dt_time(22), dt_time(6), 0.1),
        DailyPriceWindow(dt_time(12), dt_time(14), 0.2),
    )
    changed = replace(
        config,
        windows=(config.windows[0], DailyPriceWindow(dt_time(12), dt_time(14), 0.25)),
    )
    now = _local("2026-09-14T23:00:00")

    before = tariff_charge_state(config, now, ALL_MONTHS)
    after = tariff_charge_state(changed, now, ALL_MONTHS)

    assert before is not None and after is not None
    assert before.start == after.start
    assert before.end == after.end
    assert before.expires_at == after.expires_at
    assert before.source != after.source


def test_next_daily_occurrence_cannot_reuse_previous_source() -> None:
    config = _config(DailyPriceWindow(dt_time(22), dt_time(6), 0.1))

    first = tariff_charge_state(config, _local("2026-09-14T23:00:00"), ALL_MONTHS)
    second = tariff_charge_state(config, _local("2026-09-15T23:00:00"), ALL_MONTHS)

    assert first is not None and second is not None
    assert first.start == second.start
    assert first.end == second.end
    assert first.expires_at != second.expires_at
    assert first.source != second.source


def test_separate_autumn_folds_cannot_restore_each_others_source() -> None:
    config = _config(DailyPriceWindow(dt_time(2, 15), dt_time(2, 45), 0.1))

    first = tariff_charge_state(config, _local("2026-10-25T02:30:00+02:00"), ALL_MONTHS)
    second = tariff_charge_state(
        config, _local("2026-10-25T02:30:00+01:00"), ALL_MONTHS
    )

    assert first is not None and second is not None
    assert first.start == second.start == dt_time(2, 15)
    assert first.end == second.end == dt_time(2, 45)
    assert first.expires_at == datetime(2026, 10, 25, 0, 45, tzinfo=UTC)
    assert second.expires_at == datetime(2026, 10, 25, 1, 45, tzinfo=UTC)
    assert first.source != second.source


def test_continuous_autumn_phase_keeps_source_during_both_folds() -> None:
    config = _config(
        DailyPriceWindow(dt_time(1, 30), dt_time(2, 30), 0.1),
        DailyPriceWindow(dt_time(2, 30), dt_time(3, 30), 0.1),
    )

    first = tariff_charge_state(config, _local("2026-10-25T02:30:00+02:00"), ALL_MONTHS)
    second = tariff_charge_state(
        config, _local("2026-10-25T02:30:00+01:00"), ALL_MONTHS
    )

    assert first is not None
    assert first == second
    assert first.expires_at == datetime(2026, 10, 25, 2, 30, tzinfo=UTC)


def test_spring_transition_keeps_source_and_real_expiry() -> None:
    config = _config(
        DailyPriceWindow(dt_time(1, 30), dt_time(2, 30), 0.1),
        DailyPriceWindow(dt_time(2, 30), dt_time(3, 30), 0.1),
    )

    before = tariff_charge_state(
        config, _local("2026-03-29T01:45:00+01:00"), ALL_MONTHS
    )
    after = tariff_charge_state(config, _local("2026-03-29T03:15:00+02:00"), ALL_MONTHS)

    assert before is not None
    assert before == after
    assert before.expires_at == datetime(2026, 3, 29, 1, 30, tzinfo=UTC)


@pytest.mark.parametrize(
    ("moment", "expiry"),
    [
        ("2026-03-29T12:00:00", "2026-03-30T00:00:00"),
        ("2026-10-25T12:00:00", "2026-10-26T00:00:00"),
    ],
)
def test_constant_tariff_uses_identified_full_day_state(
    moment: str, expiry: str
) -> None:
    state = tariff_charge_state(_config(), _local(moment), ALL_MONTHS)

    assert state is not None
    assert state.start == state.end == dt_time(0)
    assert is_tariff_source(state.source)
    assert state.expires_at == _local(expiry).astimezone(UTC)


@pytest.mark.parametrize(
    "moment", [datetime(2026, 9, 14, 2), _local("2026-03-29T02:30:00")]
)
def test_invalid_local_moment_has_no_tariff_latch(moment: datetime) -> None:
    assert tariff_charge_state(_config(), moment, ALL_MONTHS) is None


def test_incomplete_tariff_never_creates_a_source() -> None:
    config = replace(_config(), windows_valid=False)

    assert (
        tariff_charge_state(config, _local("2026-09-14T02:00:00"), ALL_MONTHS) is None
    )


def test_long_spring_phase_is_clipped_to_month_end_from_its_first_day() -> None:
    """REQ-TIME-OF-USE-CHARGE-SOURCE: Ein später Monatswechsel ändert keine Quelle."""
    config = _config(DailyPriceWindow(dt_time(2, 15), dt_time(2, 45), 0.1), base=0.05)
    moments = (
        "2024-03-30T03:00:00",
        "2024-03-31T00:00:00",
        "2024-03-31T04:00:00",
        "2024-03-31T23:59:59",
    )

    states = [tariff_charge_state(config, _local(moment), {3}) for moment in moments]

    assert states[0] is not None
    assert all(state == states[0] for state in states)
    assert states[0].start == dt_time(2, 45)
    assert states[0].end == dt_time(0)
    assert states[0].expires_at == datetime(2024, 3, 31, 22, tzinfo=UTC)
    assert tariff_charge_state(config, _local("2024-04-01T00:00:00"), {3}) is None


def test_long_spring_phase_keeps_disabled_previous_month_excluded() -> None:
    """REQ-TIME-OF-USE-CHARGE-SOURCE: Der abgeschnittene Phasenstart bleibt stabil."""
    config = _config(DailyPriceWindow(dt_time(2, 15), dt_time(2, 45), 0.1), base=0.05)
    sydney = ZoneInfo("Australia/Sydney")
    moments = (
        datetime(2023, 10, 1, 0, 30, tzinfo=sydney),
        datetime(2023, 10, 1, 4, tzinfo=sydney),
        datetime(2023, 10, 2, 1, 30, tzinfo=sydney),
    )

    states = [tariff_charge_state(config, moment, {10}) for moment in moments]

    assert states[0] is not None
    assert all(state == states[0] for state in states)
    assert states[0].start == dt_time(0)
    assert states[0].end == dt_time(2, 15)
    assert states[0].expires_at == datetime(2023, 10, 1, 15, 15, tzinfo=UTC)
    assert (
        tariff_charge_state(config, datetime(2023, 9, 30, 23, 59, tzinfo=sydney), {10})
        is None
    )
