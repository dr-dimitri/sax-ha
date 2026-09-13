"""Configured low-tariff windows for REQ-BRIDGE-CHARGE."""

from __future__ import annotations

from collections.abc import Set
from datetime import UTC, date, datetime, timedelta
from datetime import time as dt_time

from ..domain.bridge_charge import ChargeWindow
from ..domain.tariff import (
    TariffConfig,
    TariffType,
    evaluate_static_tariff,
    find_overlapping_window,
    validate_tariff,
)

MAX_BRIDGE_HORIZON = timedelta(hours=26)


def _aware(value: object) -> bool:
    return isinstance(value, datetime) and value.utcoffset() is not None


def _window_tariff(tariff: TariffConfig | None) -> TariffConfig | None:
    if (
        tariff is None
        or tariff.tariff_type is not TariffType.TIME_OF_USE
        or validate_tariff(tariff) is not None
        or any(
            window.start == window.end
            or window.start.tzinfo is not None
            or window.end.tzinfo is not None
            for window in tariff.windows
        )
        or find_overlapping_window(tuple(enumerate(tariff.windows))) is not None
    ):
        return None
    return tariff


def _next_midnight(moment: datetime) -> datetime:
    return datetime.combine(
        moment.date() + timedelta(days=1), dt_time(), moment.tzinfo
    ).astimezone(UTC)


def charge_windows(
    *,
    now: datetime,
    pv_start: datetime,
    active_months: Set[int],
    tariff: TariffConfig | None,
) -> tuple[ChargeWindow, ...]:
    """Return cheapest allowed UTC segments, clipped to days and PV deadline.

    Cheap means the lowest configured daily price, even when that price
    has no occurrence before PV starts. Choosing a merely cheaper remaining
    interval would silently authorize charging outside the low tariff.
    """
    if not _aware(now) or not _aware(pv_start):
        return ()
    config = _window_tariff(tariff)
    if config is None:
        return ()
    assert config.tou_base_price_eur_kwh is not None
    prices = [window.price_eur_kwh for window in config.windows]
    coverage = sum(
        (
            datetime.combine(date.min, window.end)
            - datetime.combine(date.min, window.start)
        ).total_seconds()
        % 86400
        for window in config.windows
    )
    if coverage < 86400:
        prices.append(config.tou_base_price_eur_kwh)
    cheapest = min(prices)
    cursor = now.astimezone(UTC)
    try:
        horizon = min(pv_start.astimezone(UTC), cursor + MAX_BRIDGE_HORIZON)
        windows: list[ChargeWindow] = []
        while cursor < horizon:
            local = cursor.astimezone(now.tzinfo)
            quote = evaluate_static_tariff(config, local).quote
            if quote is None or quote.valid_until is None:
                return ()
            end = min(
                horizon,
                quote.valid_until.astimezone(UTC),
                _next_midnight(local),
            )
            if end <= cursor:
                return ()
            if local.month in active_months and quote.price_eur_kwh == cheapest:
                windows.append(
                    ChargeWindow(
                        cursor,
                        end,
                        price=quote.price_eur_kwh,
                    )
                )
            cursor = end
        return tuple(windows)
    except OverflowError, ValueError:
        return ()
