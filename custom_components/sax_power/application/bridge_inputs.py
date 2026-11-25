"""Configured low-tariff windows for REQ-BRIDGE-CHARGE."""

from __future__ import annotations

import math
from collections.abc import Mapping, Set
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time

from ..const import (
    BRIDGE_CHARGE_MIN_ENERGY_STEP_KWH,
    CONF_BRIDGE_CHARGE_MIN_ENERGY_KWH,
    DEFAULT_BRIDGE_CHARGE_MIN_ENERGY_KWH,
    MAX_BRIDGE_CHARGE_MIN_ENERGY_KWH,
    MIN_BRIDGE_CHARGE_MIN_ENERGY_KWH,
)
from ..domain.bridge_charge import ChargeWindow
from ..domain.tariff import (
    TariffConfig,
    evaluate_static_tariff,
    low_tariff_window,
    lowest_daily_price,
)

MAX_BRIDGE_HORIZON = timedelta(hours=26)


def require_bridge_charge_min_energy_kwh(value: object) -> float:
    """Validate and normalize the shared tariff-bridge setting."""
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not MIN_BRIDGE_CHARGE_MIN_ENERGY_KWH
        <= value
        <= MAX_BRIDGE_CHARGE_MIN_ENERGY_KWH
        or not math.isclose(
            value / BRIDGE_CHARGE_MIN_ENERGY_STEP_KWH,
            round(value / BRIDGE_CHARGE_MIN_ENERGY_STEP_KWH),
            rel_tol=0,
            abs_tol=1e-9,
        )
    ):
        raise ValueError("Ungültige Mindestlademenge für die Netzladung")
    return round(float(value), 1)


def bridge_charge_min_energy_kwh_from_options(options: Mapping[str, object]) -> float:
    """Keep the established minimum when loading older or invalid options."""
    value = options.get(
        CONF_BRIDGE_CHARGE_MIN_ENERGY_KWH, DEFAULT_BRIDGE_CHARGE_MIN_ENERGY_KWH
    )
    try:
        return require_bridge_charge_min_energy_kwh(value)
    except ValueError:
        return DEFAULT_BRIDGE_CHARGE_MIN_ENERGY_KWH


def _aware(value: object) -> bool:
    return isinstance(value, datetime) and value.utcoffset() is not None


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

    Cheap means the lowest occurring daily price, even when that price
    has no occurrence before PV starts. Choosing a merely cheaper remaining
    interval would silently authorize charging outside the low tariff.
    """
    if not _aware(now) or not _aware(pv_start):
        return ()
    if lowest_daily_price(tariff) is None:
        return ()
    assert tariff is not None
    cursor = now.astimezone(UTC)
    try:
        horizon = min(pv_start.astimezone(UTC), cursor + MAX_BRIDGE_HORIZON)
        windows: list[ChargeWindow] = []
        while cursor < horizon:
            local = cursor.astimezone(now.tzinfo)
            low_quote = low_tariff_window(tariff, local)
            quote = low_quote or evaluate_static_tariff(tariff, local).quote
            if quote is None or quote.valid_until is None:
                return ()
            end = min(
                horizon,
                quote.valid_until.astimezone(UTC),
                _next_midnight(local),
            )
            if end <= cursor:
                return ()
            if local.month in active_months and low_quote is not None:
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
