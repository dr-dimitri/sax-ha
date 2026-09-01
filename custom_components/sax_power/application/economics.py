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
    CONF_ECONOMICS_INVESTMENT_COST,
    CONF_ECONOMICS_PRIOR_RESULT,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_ECONOMICS_WINDOW_END,
    CONF_ECONOMICS_WINDOW_PRICE,
    CONF_ECONOMICS_WINDOW_START,
    ECONOMICS_TOU_WINDOW_KEYS,
    MAX_ECONOMICS_INVESTMENT_COST,
    MAX_ECONOMICS_PRIOR_RESULT,
    MIN_ECONOMICS_INVESTMENT_COST,
    MIN_ECONOMICS_PRIOR_RESULT,
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


def investment_cost_eur_from_options(options: Mapping[str, Any]) -> float | None:
    """Investitionskosten (EUR) aus den Options, sonst None.

    Optional und unabhängig von der Tarifart (REQ-ECONOMICS-AMORTIZATION):
    leer/fehlend deaktiviert sämtliche Investitions-/Amortisationssensoren,
    ohne die übrige Wirtschaftlichkeitsbilanz zu berühren. Ein aus dem Bereich
    gelaufener oder von Hand verstellter Wert wird nicht stillschweigend
    geklammert, sondern behandelt wie "nicht konfiguriert".
    """
    cost = parse_price(options.get(CONF_ECONOMICS_INVESTMENT_COST))
    if cost is None:
        return None
    if not (MIN_ECONOMICS_INVESTMENT_COST <= cost <= MAX_ECONOMICS_INVESTMENT_COST):
        return None
    return cost


def prior_result_eur_from_options(options: Mapping[str, Any]) -> float:
    """Vor der Integration erwirtschafteter Ertrag (EUR); 0.0, wenn keiner.

    Ergänzt ausschließlich die Amortisationsrechnung
    (REQ-ECONOMICS-AMORTIZATION): Ohne ihn stünde ein seit Jahren
    laufender Speicher bei 0 % Fortschritt, obwohl ein Teil der
    Investition längst erwirtschaftet ist.

    Anders als die Investitionskosten liefert diese Funktion nie None:
    "nicht konfiguriert" und "kein Vorlauf" sind hier dasselbe, und ein
    Summand 0.0 lässt sich an der Aufrufstelle bedingungslos addieren.
    Ein aus dem Bereich gelaufener oder von Hand verstellter Wert gilt wie
    bei den Investitionskosten als nicht konfiguriert, statt geklammert zu
    werden - ein stillschweigend halbierter Vorlauf wäre schlechter als
    gar keiner.
    """
    prior = parse_price(options.get(CONF_ECONOMICS_PRIOR_RESULT))
    if prior is None:
        return 0.0
    if not (MIN_ECONOMICS_PRIOR_RESULT <= prior <= MAX_ECONOMICS_PRIOR_RESULT):
        return 0.0
    return prior


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
    windows: tuple[DailyPriceWindow, ...] = ()
    windows_valid = True
    if tariff_type is TariffType.TIME_OF_USE:
        windows, windows_valid = _windows_from_options(options)
    return TariffConfig(
        tariff_type=tariff_type,
        feed_in_price_eur_kwh=parse_price(options.get(CONF_ECONOMICS_FEED_IN_PRICE)),
        fixed_import_price_eur_kwh=parse_price(
            options.get(CONF_ECONOMICS_FIXED_IMPORT_PRICE)
        ),
        tou_base_price_eur_kwh=parse_price(options.get(CONF_ECONOMICS_TOU_BASE_PRICE)),
        windows=windows,
        windows_valid=windows_valid,
    )


def _windows_from_options(
    options: Mapping[str, Any],
) -> tuple[tuple[DailyPriceWindow, ...], bool]:
    windows: list[DailyPriceWindow] = []
    valid = True
    for key in ECONOMICS_TOU_WINDOW_KEYS:
        window, section_valid = window_from_section(options.get(key))
        if window is not None:
            windows.append(window)
        valid = valid and section_valid
    return tuple(windows), valid


def window_from_section(section: Any) -> tuple[DailyPriceWindow | None, bool]:
    """Ein Zeitfenster aus einer Options-Section, plus ob die Section
    selbst überhaupt gültig ist.

    Eine schlicht leere Gruppe (Schlüssel fehlt, oder alle drei Felder
    fehlen/sind None) ist ein gültiger Anwenderzustand und liefert
    (None, True). Eine VORHANDENE, aber unvollständige, unlesbare oder
    fremdtypige Section (z. B. `start`/`end` gesetzt, `price_eur_kwh` aber
    ungültig) liefert dagegen (None, False): Ein von Hand bearbeiteter
    Store kann genau das enthalten, und ein solcher Fehler darf nicht
    stillschweigend verschwinden - sonst sähe validate_tariff() nur die
    übrigen, zufällig noch lesbaren Fenster und würde trotz kaputter
    Konfiguration einen Quote erzeugen (siehe TariffConfig.windows_valid).
    """
    if section is None:
        return None, True
    if not isinstance(section, Mapping):
        return None, False

    raw_start = section.get(CONF_ECONOMICS_WINDOW_START)
    raw_end = section.get(CONF_ECONOMICS_WINDOW_END)
    raw_price = section.get(CONF_ECONOMICS_WINDOW_PRICE)
    if raw_start is None and raw_end is None and raw_price is None:
        return None, True

    start = parse_time(raw_start)
    end = parse_time(raw_end)
    price = parse_price(raw_price)
    if start is None or end is None or price is None or start == end:
        return None, False
    return DailyPriceWindow(start=start, end=end, price_eur_kwh=price), True
