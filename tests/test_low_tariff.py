"""Gemeinsame Niedertarifdefinition: REQ-TIME-OF-USE-CHARGE-SOURCE."""

from __future__ import annotations

from datetime import UTC, datetime
from datetime import time as dt_time
from zoneinfo import ZoneInfo

import pytest

from custom_components.sax_power.domain.tariff import (
    DailyPriceWindow,
    QuoteUnavailable,
    TariffConfig,
    TariffType,
    daily_base_price_applies,
    evaluate_static_tariff,
    low_tariff_window,
    lowest_daily_price,
    validate_tariff,
)

BERLIN = ZoneInfo("Europe/Berlin")


def _config(*windows: DailyPriceWindow, base: float = 0.3) -> TariffConfig:
    return TariffConfig(
        tariff_type=TariffType.TIME_OF_USE,
        feed_in_price_eur_kwh=0.08,
        tou_base_price_eur_kwh=base,
        windows=windows,
    )


def _local(value: str) -> datetime:
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        return moment.replace(tzinfo=BERLIN)
    return moment.astimezone(BERLIN)


def test_only_the_daily_minimum_authorizes_charging() -> None:
    config = _config(
        DailyPriceWindow(dt_time(0), dt_time(6), 0.1),
        DailyPriceWindow(dt_time(12), dt_time(14), 0.2),
    )

    assert lowest_daily_price(config) == 0.1
    assert low_tariff_window(config, _local("2026-09-14T02:00:00")) is not None
    assert low_tariff_window(config, _local("2026-09-14T13:00:00")) is None
    assert low_tariff_window(config, _local("2026-09-14T20:00:00")) is None


def test_unused_base_price_is_excluded_from_the_daily_minimum() -> None:
    config = _config(
        DailyPriceWindow(dt_time(22), dt_time(6), 0.2),
        DailyPriceWindow(dt_time(6), dt_time(22), 0.3),
        base=0.1,
    )

    assert not daily_base_price_applies(config)
    assert lowest_daily_price(config) == 0.2
    assert low_tariff_window(config, _local("2026-09-14T23:00:00")) is not None


def test_smallest_base_gap_is_part_of_the_daily_minimum() -> None:
    config = _config(DailyPriceWindow(dt_time(0, 0, 0, 1), dt_time(0), 0.2), base=0.1)

    assert daily_base_price_applies(config)
    assert lowest_daily_price(config) == 0.1
    quote = low_tariff_window(config, _local("2026-09-14T00:00:00"))
    assert quote is not None
    assert quote.valid_until == _local("2026-09-14T00:00:00.000001")
    assert low_tariff_window(config, quote.valid_until) is None


@pytest.mark.parametrize("hour", [0, 2, 4, 5])
def test_equal_windows_and_base_gaps_form_one_phase(hour: int) -> None:
    config = _config(
        DailyPriceWindow(dt_time(6), dt_time(22), 0.3),
        DailyPriceWindow(dt_time(0), dt_time(2), 0.1),
        DailyPriceWindow(dt_time(2), dt_time(4), 0.1),
        base=0.1,
    )

    quote = low_tariff_window(config, _local(f"2026-10-01T{hour:02d}:00:00"))

    assert quote is not None
    assert quote.price_eur_kwh == 0.1
    assert quote.valid_from == _local("2026-09-30T22:00:00")
    assert quote.valid_until == _local("2026-10-01T06:00:00")


@pytest.mark.parametrize(
    ("moment", "available"),
    [
        ("2026-09-14T21:59:59.999999", False),
        ("2026-09-14T22:00:00", True),
        ("2026-09-15T05:59:59.999999", True),
        ("2026-09-15T06:00:00", False),
    ],
)
def test_low_tariff_boundaries_are_half_open(moment: str, available: bool) -> None:
    config = _config(DailyPriceWindow(dt_time(22), dt_time(6), 0.1))

    assert (low_tariff_window(config, _local(moment)) is not None) is available


@pytest.mark.parametrize("explicit_windows", [False, True])
@pytest.mark.parametrize(("date", "hours"), [("2026-03-29", 23), ("2026-10-25", 25)])
def test_constant_daily_price_has_real_local_day_bounds(
    explicit_windows: bool, date: str, hours: int
) -> None:
    windows = (
        (
            DailyPriceWindow(dt_time(0), dt_time(12), 0.1),
            DailyPriceWindow(dt_time(12), dt_time(0), 0.1),
        )
        if explicit_windows
        else ()
    )
    config = _config(*windows, base=0.2 if explicit_windows else 0.1)

    quote = low_tariff_window(config, _local(f"{date}T12:00:00"))

    assert quote is not None
    assert quote.valid_from == _local(f"{date}T00:00:00")
    assert quote.valid_until.hour == 0
    assert (
        quote.valid_until.astimezone(UTC) - quote.valid_from.astimezone(UTC)
    ).total_seconds() == hours * 3600


@pytest.mark.parametrize("offset", ["+02:00", "+01:00"])
def test_autumn_repeated_hour_has_two_distinct_short_phases(offset: str) -> None:
    config = _config(DailyPriceWindow(dt_time(2, 15), dt_time(2, 45), 0.1))

    quote = low_tariff_window(config, _local(f"2026-10-25T02:30:00{offset}"))

    assert quote is not None
    assert quote.valid_from.astimezone(UTC) == _local(
        f"2026-10-25T02:15:00{offset}"
    ).astimezone(UTC)
    assert quote.valid_until.astimezone(UTC) == _local(
        f"2026-10-25T02:45:00{offset}"
    ).astimezone(UTC)


@pytest.mark.parametrize(
    ("date", "start_offset", "end_offset", "hours"),
    [
        ("2026-03-29", "+01:00", "+02:00", 1),
        ("2026-10-25", "+02:00", "+01:00", 3),
    ],
)
def test_equal_price_windows_remain_one_phase_across_clock_change(
    date: str, start_offset: str, end_offset: str, hours: int
) -> None:
    config = _config(
        DailyPriceWindow(dt_time(1, 30), dt_time(2, 30), 0.1),
        DailyPriceWindow(dt_time(2, 30), dt_time(3, 30), 0.1),
    )

    quote = low_tariff_window(config, _local(f"{date}T03:00:00{end_offset}"))

    assert quote is not None
    assert quote.valid_from.astimezone(UTC) == _local(
        f"{date}T01:30:00{start_offset}"
    ).astimezone(UTC)
    assert quote.valid_until.astimezone(UTC) == _local(
        f"{date}T03:30:00{end_offset}"
    ).astimezone(UTC)
    assert (
        quote.valid_until.astimezone(UTC) - quote.valid_from.astimezone(UTC)
    ).total_seconds() == hours * 3600


def test_skipped_expensive_window_does_not_interrupt_the_low_phase() -> None:
    config = _config(DailyPriceWindow(dt_time(2, 15), dt_time(2, 45), 0.3), base=0.1)

    quote = low_tariff_window(config, _local("2026-03-29T03:00:00"))

    assert quote is not None
    assert quote.valid_from == _local("2026-03-28T02:45:00")
    assert quote.valid_until == _local("2026-03-30T02:15:00")


@pytest.mark.parametrize(
    "config",
    [
        _config(DailyPriceWindow(dt_time(1), dt_time(1), 0.1)),
        _config(DailyPriceWindow(dt_time(1, tzinfo=UTC), dt_time(2), 0.1)),
        _config(
            DailyPriceWindow(dt_time(1), dt_time(3), 0.1),
            DailyPriceWindow(dt_time(2), dt_time(4), 0.1),
        ),
        _config(
            DailyPriceWindow(dt_time(22), dt_time(3), 0.1),
            DailyPriceWindow(dt_time(2), dt_time(4), 0.2),
        ),
        _config(DailyPriceWindow(dt_time(1), dt_time(2), float("nan"))),
        _config(base=float("inf")),
        TariffConfig(
            tariff_type=TariffType.TIME_OF_USE,
            feed_in_price_eur_kwh=0.1,
            tou_base_price_eur_kwh=0.1,
            windows_valid=False,
        ),
        TariffConfig(tariff_type=TariffType.TIME_OF_USE, tou_base_price_eur_kwh=0.1),
    ],
)
def test_invalid_profile_fails_closed_for_all_tariff_consumers(
    config: TariffConfig,
) -> None:
    moment = _local("2026-09-14T02:30:00")

    assert validate_tariff(config) is QuoteUnavailable.TARIFF_INCOMPLETE
    assert lowest_daily_price(config) is None
    assert not daily_base_price_applies(config)
    assert low_tariff_window(config, moment) is None
    assert evaluate_static_tariff(config, moment).quote is None


@pytest.mark.parametrize(
    "config",
    [
        None,
        TariffConfig(),
        TariffConfig(
            tariff_type=TariffType.FIXED,
            feed_in_price_eur_kwh=0.1,
            fixed_import_price_eur_kwh=0.1,
        ),
        TariffConfig(tariff_type=TariffType.DYNAMIC, feed_in_price_eur_kwh=0.1),
    ],
)
def test_other_tariff_types_do_not_authorize_time_of_use_charging(
    config: TariffConfig | None,
) -> None:
    assert lowest_daily_price(config) is None
    assert not daily_base_price_applies(config)
    assert low_tariff_window(config, _local("2026-09-14T02:30:00")) is None


@pytest.mark.parametrize(
    "moment",
    [datetime(2026, 9, 14, 2, 30), _local("2026-03-29T02:30:00")],
)
def test_naive_or_nonexistent_local_time_never_authorizes_charging(
    moment: datetime,
) -> None:
    config = _config()

    assert low_tariff_window(config, moment) is None
    assert evaluate_static_tariff(config, moment).quote is None


def test_negative_and_zero_prices_remain_valid_low_tariffs() -> None:
    config = _config(DailyPriceWindow(dt_time(1), dt_time(2), -0.1), base=0)

    assert lowest_daily_price(config) == -0.1
    quote = low_tariff_window(config, _local("2026-09-14T01:30:00"))
    assert quote is not None
    assert quote.price_eur_kwh == -0.1
