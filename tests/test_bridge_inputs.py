"""Configured tariff and local-time boundaries for REQ-BRIDGE-CHARGE."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from zoneinfo import ZoneInfo

import pytest

from custom_components.sax_power.application.bridge_inputs import charge_windows
from custom_components.sax_power.domain.bridge_charge import ChargeWindow
from custom_components.sax_power.domain.tariff import (
    DailyPriceWindow,
    TariffConfig,
    TariffType,
    low_tariff_window,
)

BERLIN = ZoneInfo("Europe/Berlin")
NOW = datetime(2026, 9, 13, 22, tzinfo=BERLIN)
MONTHS = frozenset(range(1, 13))


def _moment(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    return (
        result.replace(tzinfo=BERLIN)
        if result.tzinfo is None
        else result.astimezone(BERLIN)
    )


def _window(start: str, end: str, price: float = 0.1) -> ChargeWindow:
    return ChargeWindow(
        _moment(start).astimezone(UTC), _moment(end).astimezone(UTC), price
    )


def _tariff(*windows: DailyPriceWindow, base: float = 0.3) -> TariffConfig:
    return TariffConfig(
        tariff_type=TariffType.TIME_OF_USE,
        feed_in_price_eur_kwh=0.08,
        tou_base_price_eur_kwh=base,
        windows=windows,
    )


def test_tariff_night_window_is_clipped_to_now_days_and_pv_start() -> None:
    windows = charge_windows(
        now=NOW,
        pv_start=_moment("2026-09-14T05:00:00"),
        active_months=MONTHS,
        tariff=_tariff(DailyPriceWindow(dt_time(21), dt_time(6), 0.1)),
    )
    assert windows == (
        _window("2026-09-13T22:00:00", "2026-09-14T00:00:00", 0.1),
        _window("2026-09-14T00:00:00", "2026-09-14T05:00:00", 0.1),
    )


@pytest.mark.parametrize(
    ("months", "expected"),
    [
        ({9}, (_window("2026-09-30T22:00:00", "2026-10-01T00:00:00"),)),
        ({10}, (_window("2026-10-01T00:00:00", "2026-10-01T06:00:00"),)),
        (set(), ()),
    ],
)
def test_month_activation_applies_to_each_local_day(
    months: set[int], expected: tuple[ChargeWindow, ...]
) -> None:
    windows = charge_windows(
        now=_moment("2026-09-30T21:00:00"),
        pv_start=_moment("2026-10-01T07:00:00"),
        active_months=months,
        tariff=_tariff(DailyPriceWindow(dt_time(22), dt_time(6), 0.1)),
    )
    assert windows == expected


def test_cheapest_tariff_segments_include_the_base_price() -> None:
    windows = charge_windows(
        now=_moment("2026-09-14T00:00:00"),
        pv_start=_moment("2026-09-14T07:00:00"),
        active_months=MONTHS,
        tariff=_tariff(
            DailyPriceWindow(dt_time(1), dt_time(2), 0.3),
            DailyPriceWindow(dt_time(3), dt_time(4), 0.1),
            base=0.1,
        ),
    )
    assert windows == (
        _window("2026-09-14T00:00:00", "2026-09-14T01:00:00", 0.1),
        _window("2026-09-14T02:00:00", "2026-09-14T07:00:00", 0.1),
    )


def test_unused_base_does_not_hide_cheapest_windows_covering_the_whole_day() -> None:
    assert charge_windows(
        now=_moment("2026-09-14T00:00:00"),
        pv_start=_moment("2026-09-14T07:00:00"),
        active_months=MONTHS,
        tariff=_tariff(
            DailyPriceWindow(dt_time(0), dt_time(6), 0.2),
            DailyPriceWindow(dt_time(6), dt_time(0), 0.3),
            base=0.1,
        ),
    ) == (_window("2026-09-14T00:00:00", "2026-09-14T06:00:00", 0.2),)


def test_missing_cheap_period_before_pv_does_not_authorize_a_higher_price() -> None:
    assert (
        charge_windows(
            now=NOW,
            pv_start=_moment("2026-09-14T07:00:00"),
            active_months=MONTHS,
            tariff=_tariff(DailyPriceWindow(dt_time(12), dt_time(14), 0.1)),
        )
        == ()
    )


def test_empty_tariff_windows_use_the_configured_base_for_the_horizon() -> None:
    assert charge_windows(
        now=NOW,
        pv_start=NOW + timedelta(hours=1),
        active_months=MONTHS,
        tariff=_tariff(),
    ) == (_window("2026-09-13T22:00:00", "2026-09-13T23:00:00", 0.3),)


@pytest.mark.parametrize(
    "tariff",
    [
        None,
        TariffConfig(),
        TariffConfig(tariff_type=TariffType.FIXED, fixed_import_price_eur_kwh=0.3),
        TariffConfig(tariff_type=TariffType.DYNAMIC, feed_in_price_eur_kwh=0.1),
        TariffConfig(tariff_type=TariffType.TIME_OF_USE),
        _tariff(DailyPriceWindow(dt_time(1), dt_time(1), 0.1)),
        _tariff(
            DailyPriceWindow(dt_time(1), dt_time(3), 0.1),
            DailyPriceWindow(dt_time(2), dt_time(4), 0.2),
        ),
    ],
)
def test_unusable_tariff_has_no_charge_windows(tariff: TariffConfig | None) -> None:
    assert (
        charge_windows(
            now=NOW,
            pv_start=NOW + timedelta(hours=12),
            active_months=MONTHS,
            tariff=tariff,
        )
        == ()
    )


def test_window_horizon_is_capped_at_twenty_six_real_hours() -> None:
    windows = charge_windows(
        now=NOW,
        pv_start=NOW + timedelta(days=2),
        active_months=MONTHS,
        tariff=_tariff(),
    )
    assert windows[0].start == NOW.astimezone(UTC)
    assert windows[-1].end == NOW.astimezone(UTC) + timedelta(hours=26)
    assert sum((window.end - window.start).total_seconds() for window in windows) == (
        26 * 3600
    )


@pytest.mark.parametrize(
    ("date", "start", "end", "expected"),
    [
        (
            "2026-03-29",
            dt_time(1, 30),
            dt_time(3, 30),
            (_window("2026-03-29T01:30:00+01:00", "2026-03-29T03:30:00+02:00"),),
        ),
        ("2026-03-29", dt_time(2, 15), dt_time(2, 45), ()),
        (
            "2026-10-25",
            dt_time(2, 15),
            dt_time(2, 45),
            (
                _window("2026-10-25T02:15:00+02:00", "2026-10-25T02:45:00+02:00"),
                _window("2026-10-25T02:15:00+01:00", "2026-10-25T02:45:00+01:00"),
            ),
        ),
    ],
)
def test_tariff_windows_follow_actual_dst_occurrences(
    date: str,
    start: dt_time,
    end: dt_time,
    expected: tuple[ChargeWindow, ...],
) -> None:
    assert (
        charge_windows(
            now=_moment(f"{date}T00:00:00"),
            pv_start=_moment(f"{date}T07:00:00"),
            active_months=MONTHS,
            tariff=_tariff(DailyPriceWindow(start, end, 0.1)),
        )
        == expected
    )


def test_seconds_in_tariff_boundaries_are_not_rounded_to_slots() -> None:
    assert charge_windows(
        now=_moment("2026-09-14T00:00:00"),
        pv_start=_moment("2026-09-14T07:00:00"),
        active_months=MONTHS,
        tariff=_tariff(DailyPriceWindow(dt_time(1, 2, 3), dt_time(1, 4, 5), 0.1)),
    ) == (_window("2026-09-14T01:02:03", "2026-09-14T01:04:05", 0.1),)


@pytest.mark.parametrize(
    "deadline", [NOW, NOW - timedelta(hours=1), datetime(2026, 9, 14)]
)
def test_invalid_window_deadline_never_authorizes_charging(deadline: datetime) -> None:
    assert (
        charge_windows(
            now=NOW,
            pv_start=deadline,
            active_months=MONTHS,
            tariff=_tariff(),
        )
        == ()
    )


def test_naive_current_time_never_authorizes_charging() -> None:
    assert (
        charge_windows(
            now=NOW.replace(tzinfo=None),
            pv_start=NOW + timedelta(hours=12),
            active_months=MONTHS,
            tariff=_tariff(),
        )
        == ()
    )


def test_negative_low_tariff_remains_the_selected_price() -> None:
    assert charge_windows(
        now=NOW,
        pv_start=NOW + timedelta(hours=1),
        active_months=MONTHS,
        tariff=_tariff(DailyPriceWindow(dt_time(21), dt_time(23), -0.1), base=0),
    ) == (_window("2026-09-13T22:00:00", "2026-09-13T23:00:00", -0.1),)


def test_bridge_windows_share_the_current_low_tariff_phase() -> None:
    """REQ-TIME-OF-USE-CHARGE-SOURCE: Alle Lader verwenden dieselbe Freigabe."""
    tariff = _tariff(
        DailyPriceWindow(dt_time(0), dt_time(2), 0.1),
        DailyPriceWindow(dt_time(2), dt_time(4), 0.1),
        DailyPriceWindow(dt_time(8), dt_time(10), 0.2),
        DailyPriceWindow(dt_time(12), dt_time(14), 0.1),
    )
    windows = charge_windows(
        now=_moment("2026-09-14T00:00:00"),
        pv_start=_moment("2026-09-14T15:00:00"),
        active_months=MONTHS,
        tariff=tariff,
    )

    assert windows == (
        _window("2026-09-14T00:00:00", "2026-09-14T04:00:00"),
        _window("2026-09-14T12:00:00", "2026-09-14T14:00:00"),
    )
    for window in windows:
        quote = low_tariff_window(tariff, window.start.astimezone(BERLIN))
        assert quote is not None
        assert quote.valid_from.astimezone(UTC) == window.start
        assert quote.valid_until.astimezone(UTC) == window.end
        assert quote.price_eur_kwh == window.price


def test_merged_low_tariff_phase_still_respects_month_activation() -> None:
    tariff = _tariff(
        DailyPriceWindow(dt_time(22), dt_time(0), 0.1),
        DailyPriceWindow(dt_time(0), dt_time(3), 0.1),
        DailyPriceWindow(dt_time(3), dt_time(6), 0.1),
    )

    assert charge_windows(
        now=_moment("2026-09-30T22:00:00"),
        pv_start=_moment("2026-10-01T08:00:00"),
        active_months={10},
        tariff=tariff,
    ) == (_window("2026-10-01T00:00:00", "2026-10-01T06:00:00"),)
