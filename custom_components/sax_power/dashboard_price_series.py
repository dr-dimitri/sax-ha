"""Complete local-day tariff series, independent of selected charging intervals."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any, TypedDict

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .application.economics import tariff_config_from_options
from .const import (
    CONF_PRICE_ATTRIBUTE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    DEFAULT_PRICE_UNIT,
    PRICE_UNITS,
)
from .domain.price_units import unit_factor
from .domain.tariff import (
    TariffType,
    evaluate_static_tariff,
    is_valid_import_price,
    validate_tariff,
)
from .price_optimizer import PriceSlot, has_price_forecast, parse_price_slots


class PriceInterval(TypedDict):
    start: str
    end: str
    price_ct_kwh: float


class Series(TypedDict):
    tariff_type: str
    day: str
    date: str
    time_zone: str
    start: str
    end: str
    now: str
    current_price_ct_kwh: float | None
    status: str
    reason: str | None
    slots: list[PriceInterval]
    gaps: list[dict[str, str]]
    revision: str


def _dynamic_slots(
    hass: HomeAssistant, options: dict[str, Any], now: datetime
) -> tuple[list[PriceSlot], str | None]:
    entity_id = options.get(CONF_PRICE_SENSOR)
    if not isinstance(entity_id, str) or not entity_id:
        return [], "price_sensor_not_configured"
    state = hass.states.get(entity_id)
    if state is None:
        return [], "price_sensor_missing"
    if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, ""):
        return [], "price_sensor_unavailable"
    unit = options.get(CONF_PRICE_UNIT, DEFAULT_PRICE_UNIT)
    if (
        unit not in PRICE_UNITS
        or unit_factor(unit, state.attributes.get("unit_of_measurement")) is None
    ):
        return [], "price_unit_unsupported"
    slots = parse_price_slots(
        state,
        attribute=options.get(CONF_PRICE_ATTRIBUTE) or None,
        unit=unit,
        now=state.last_updated.astimezone(now.tzinfo),
    )
    return slots, None if slots else "price_forecast_missing"


def price_series(
    hass: HomeAssistant,
    options: dict[str, Any],
    *,
    day: str,
    revision: str,
    now: datetime | None = None,
) -> Series:
    """Build coverage from real instants, including both folds of DST fallback."""
    zone = dt_util.get_time_zone(hass.config.time_zone)
    assert zone is not None
    local_now = (now or dt_util.utcnow()).astimezone(zone)
    target_day: date = local_now.date() + timedelta(days=day == "tomorrow")
    start = datetime.combine(target_day, time.min, zone).astimezone(UTC)
    end = datetime.combine(target_day + timedelta(days=1), time.min, zone).astimezone(
        UTC
    )
    config = tariff_config_from_options(options)
    reason = validate_tariff(config)
    source: list[PriceSlot] = []
    current: float | None = None
    if reason is None:
        if config.tariff_type is TariffType.DYNAMIC:
            source, reason = _dynamic_slots(hass, options, local_now)
            active = [slot for slot in source if slot.overlaps(local_now)]
            if len(active) == 1 and is_valid_import_price(active[0].price):
                current = active[0].price * 100
            elif not source and reason == "price_forecast_missing":
                state = hass.states.get(options.get(CONF_PRICE_SENSOR, ""))
                if state is not None and not has_price_forecast(
                    state, attribute=options.get(CONF_PRICE_ATTRIBUTE) or None
                ):
                    factor = unit_factor(
                        options.get(CONF_PRICE_UNIT, DEFAULT_PRICE_UNIT),
                        state.attributes.get("unit_of_measurement"),
                    )
                    try:
                        raw = float(state.state)
                    except ValueError, OverflowError:
                        raw = float("nan")
                    if factor is not None and is_valid_import_price(raw * factor):
                        current = raw * factor * 100
        else:
            current = evaluate_static_tariff(config, local_now).price_eur_kwh
            current = None if current is None else current * 100
            cursor = start
            while cursor < end:
                quote = evaluate_static_tariff(config, cursor.astimezone(zone)).quote
                if quote is None:
                    break
                right = (
                    min(end, quote.valid_until.astimezone(UTC))
                    if quote.valid_until
                    else end
                )
                if right <= cursor:
                    break
                source.append(PriceSlot(cursor, right, quote.price_eur_kwh))
                cursor = right
    boundaries = {start, end}
    for slot in source:
        left, right = slot.start.astimezone(UTC), slot.end.astimezone(UTC)
        if left < end and right > start:
            boundaries.update((max(start, left), min(end, right)))
    ordered = sorted(boundaries)
    slots: list[PriceInterval] = []
    gaps: list[dict[str, str]] = []
    for left, right in zip(ordered, ordered[1:], strict=False):
        matching = [slot for slot in source if slot.overlaps(left)]
        if len(matching) == 1 and is_valid_import_price(matching[0].price):
            slots.append(
                {
                    "start": left.isoformat(),
                    "end": right.isoformat(),
                    "price_ct_kwh": round(matching[0].price * 100, 5),
                }
            )
        elif gaps and gaps[-1]["end"] == left.isoformat():
            gaps[-1]["end"] = right.isoformat()
        else:
            gaps.append({"start": left.isoformat(), "end": right.isoformat()})
    return {
        "tariff_type": config.tariff_type.value,
        "day": day,
        "date": target_day.isoformat(),
        "time_zone": hass.config.time_zone,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "now": local_now.isoformat(),
        "current_price_ct_kwh": None if current is None else round(current, 5),
        "status": "available" if not gaps else "partial" if slots else "unavailable",
        "reason": (
            str(reason) if reason else "price_coverage_incomplete" if gaps else None
        ),
        "slots": slots,
        "gaps": gaps,
        "revision": revision,
    }
