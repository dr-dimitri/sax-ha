"""Mapping between stored config entry options and the tariff domain model.

Rein rechnend und ohne Home-Assistant-Abhängigkeit: die Options sind hier
nur ein Mapping. Der Zugriff auf `hass` (Sensorzustände, Listener) liegt
allein im Adapter economics.py.

Siehe anforderung.yaml, REQ-ECONOMICS-TARIFFS.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import time as dt_time
from typing import Any

from ..const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_ECONOMICS_WINDOW_END,
    CONF_ECONOMICS_WINDOW_PRICE,
    CONF_ECONOMICS_WINDOW_START,
    ECONOMICS_TOU_WINDOW_KEYS,
)
from ..domain.tariff import DailyPriceWindow, TariffConfig, TariffType


def parse_price(value: Any) -> float | None:
    """Endlicher Preis als float, sonst None.

    Options kommen aus einem JSON-Store und können nach einer manuellen
    Bearbeitung alles enthalten - ein nicht auswertbarer Wert darf niemals
    stillschweigend zu 0 EUR/kWh werden.
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        price = float(value)
    except TypeError, ValueError:
        return None
    return price if math.isfinite(price) else None


def parse_time(value: Any) -> dt_time | None:
    """Uhrzeit aus dem TimeSelector-Format "HH:MM[:SS]" als time."""
    if isinstance(value, dt_time):
        return value
    if not isinstance(value, str):
        return None
    parts = value.split(":")
    if len(parts) not in (2, 3):
        return None
    try:
        numbers = [int(part) for part in parts]
    except ValueError:
        return None
    try:
        return dt_time(*numbers)
    except ValueError:
        return None


def parse_tariff_type(value: Any) -> TariffType:
    """Gespeicherte Tarifart; alles Unbekannte gilt als deaktiviert."""
    try:
        return TariffType(value)
    except ValueError:
        return TariffType.DISABLED


def tariff_config_from_options(options: Mapping[str, Any]) -> TariffConfig:
    """TariffConfig aus den gespeicherten Options eines Config Entry.

    Unvollständige oder unlesbare Einzelwerte bleiben None statt ersetzt zu
    werden; die Auswertung meldet daraus TARIFF_INCOMPLETE, statt mit einem
    erfundenen Preis weiterzurechnen.
    """
    tariff_type = parse_tariff_type(options.get(CONF_ECONOMICS_TARIFF_TYPE))
    return TariffConfig(
        tariff_type=tariff_type,
        feed_in_price_eur_kwh=parse_price(options.get(CONF_ECONOMICS_FEED_IN_PRICE)),
        fixed_import_price_eur_kwh=parse_price(
            options.get(CONF_ECONOMICS_FIXED_IMPORT_PRICE)
        ),
        tou_base_price_eur_kwh=parse_price(options.get(CONF_ECONOMICS_TOU_BASE_PRICE)),
        windows=(
            _windows_from_options(options)
            if tariff_type is TariffType.TIME_OF_USE
            else ()
        ),
    )


def _windows_from_options(
    options: Mapping[str, Any],
) -> tuple[DailyPriceWindow, ...]:
    windows: list[DailyPriceWindow] = []
    for key in ECONOMICS_TOU_WINDOW_KEYS:
        window = window_from_section(options.get(key))
        if window is not None:
            windows.append(window)
    return tuple(windows)


def window_from_section(section: Any) -> DailyPriceWindow | None:
    """Ein Zeitfenster aus einer Options-Section, oder None.

    None steht sowohl für "Gruppe nicht ausgefüllt" als auch für "Gruppe
    unbrauchbar": Der Options Flow lässt eine unvollständige Gruppe gar
    nicht erst speichern, ein von Hand bearbeiteter Store könnte sie aber
    enthalten.
    """
    if not isinstance(section, Mapping):
        return None
    start = parse_time(section.get(CONF_ECONOMICS_WINDOW_START))
    end = parse_time(section.get(CONF_ECONOMICS_WINDOW_END))
    price = parse_price(section.get(CONF_ECONOMICS_WINDOW_PRICE))
    if start is None or end is None or price is None or start == end:
        return None
    return DailyPriceWindow(start=start, end=end, price_eur_kwh=price)
