"""Configured low-tariff windows for REQ-BRIDGE-CHARGE."""

from __future__ import annotations

import math
from collections.abc import Mapping, Set
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time

from ..const import (
    BRIDGE_CHARGE_MIN_ENERGY_STEP_KWH,
    CONF_BRIDGE_CHARGE_MIN_ENERGY_KWH,
    CONF_BRIDGE_CHARGE_SOC_BUFFER,
    DEFAULT_BRIDGE_CHARGE_MIN_ENERGY_KWH,
    DEFAULT_BRIDGE_CHARGE_SOC_BUFFER,
    MAX_BRIDGE_CHARGE_MIN_ENERGY_KWH,
    MAX_SOC,
    MIN_BRIDGE_CHARGE_MIN_ENERGY_KWH,
    MIN_SOC,
)
from ..domain.bridge_charge import ChargeWindow
from ..domain.tariff import (
    TariffConfig,
    evaluate_static_tariff,
    low_tariff_window,
    lowest_daily_price,
)

MAX_BRIDGE_HORIZON = timedelta(hours=26)


def empty_battery_consumption_power(storage: object, meter: object) -> float | None:
    """Measure uncovered house demand while an empty battery cannot discharge."""
    if (
        not isinstance(storage, int | float)
        or isinstance(storage, bool)
        or not isinstance(meter, int | float)
        or isinstance(meter, bool)
        or not math.isfinite(storage)
        or not math.isfinite(meter)
    ):
        return None
    # Charging has a negative sign, so the battery's own grid import
    # cancels out. Export contributes no uncovered demand.
    return max(0.0, meter + storage)


def require_bridge_charge_min_energy_kwh(value: object) -> float:
    """Validate and normalize the shared tariff-bridge setting."""
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or (
            value != 0
            and not MIN_BRIDGE_CHARGE_MIN_ENERGY_KWH
            <= value
            <= MAX_BRIDGE_CHARGE_MIN_ENERGY_KWH
        )
        or not math.isclose(
            value / BRIDGE_CHARGE_MIN_ENERGY_STEP_KWH,
            round(value / BRIDGE_CHARGE_MIN_ENERGY_STEP_KWH),
            rel_tol=0,
            abs_tol=1e-9,
        )
    ):
        raise ValueError(
            "Erlaubt sind 0 oder 0,5 bis 100 kWh in Schritten von 0,1 kWh."
        )
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


def require_bridge_charge_soc_buffer(value: object) -> int:
    """Validate the absolute SOC reserve before accepting a software setting."""
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not MIN_SOC <= value <= MAX_SOC
        or int(value) != value
    ):
        raise ValueError("Der SOC-Puffer muss eine ganze Zahl von 0 bis 100 sein.")
    return int(value)


def bridge_charge_soc_buffer_from_options(options: Mapping[str, object]) -> int:
    try:
        return require_bridge_charge_soc_buffer(
            options.get(CONF_BRIDGE_CHARGE_SOC_BUFFER, DEFAULT_BRIDGE_CHARGE_SOC_BUFFER)
        )
    except ValueError:
        return DEFAULT_BRIDGE_CHARGE_SOC_BUFFER


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
