"""Tests für das Tarifmodell der Wirtschaftlichkeitsauswertung.

Siehe anforderung.yaml, REQ-ECONOMICS-TARIFFS. Deckt die reine Domäne
(domain/tariff.py), die Options-Abbildung (application/economics.py) und den
Home-Assistant-Adapter (economics.py) ab.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from homeassistant.util import dt as dt_util

from custom_components.sax_power.application.economics import (
    parse_price,
    parse_time,
    tariff_config_from_options,
)
from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_ECONOMICS_WINDOW_END,
    CONF_ECONOMICS_WINDOW_PRICE,
    CONF_ECONOMICS_WINDOW_START,
    CONF_PRICE_ATTRIBUTE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    ECONOMICS_TOU_WINDOW_COUNT,
    PRICE_UNIT_CT_KWH,
    economics_tou_window_key,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.price_units import unit_factor
from custom_components.sax_power.domain.tariff import (
    DailyPriceWindow,
    QuoteSource,
    QuoteUnavailable,
    TariffConfig,
    TariffType,
    TariffWindowError,
    evaluate_static_tariff,
    find_overlapping_window,
    validate_tariff,
    validate_window_fields,
)

BERLIN = ZoneInfo("Europe/Berlin")


def _local(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=BERLIN)


def _window(start: str, end: str, price: float) -> DailyPriceWindow:
    return DailyPriceWindow(
        start=parse_time(start), end=parse_time(end), price_eur_kwh=price
    )


def _config(**overrides) -> TariffConfig:
    """TariffConfig mit gültiger Einspeisevergütung.

    Sie ist bei jeder aktivierten Tarifart Pflicht (REQ-ECONOMICS-TARIFFS);
    ohne sie meldet die Auswertung TARIFF_INCOMPLETE, bevor sie überhaupt
    einen Preis bestimmt. Die Tests hier prüfen die Preisregeln und setzen
    sie deshalb zentral über diesen Helfer.
    """
    return TariffConfig(feed_in_price_eur_kwh=0.0786, **overrides)


# --------------------------------------------------------------------------
# Festpreis
# --------------------------------------------------------------------------
def test_fixed_tariff_returns_the_same_quote_at_every_moment() -> None:
    """Ein Festpreis ist ganztägig konstant - der Quote darf sich über die
    Zeit in keinem Feld unterscheiden."""
    config = _config(tariff_type=TariffType.FIXED, fixed_import_price_eur_kwh=0.3421)

    quotes = {
        evaluate_static_tariff(config, _local(2026, 3, day, hour)).quote
        for day in (1, 15, 29)
        for hour in (0, 3, 12, 23)
    }

    assert len(quotes) == 1
    quote = quotes.pop()
    assert quote.price_eur_kwh == 0.3421
    assert quote.source is QuoteSource.FIXED
    assert quote.valid_from is None and quote.valid_until is None


def test_fixed_tariff_without_price_reports_incomplete() -> None:
    """Ohne hinterlegten Arbeitspreis gibt es keinen Preis - und schon gar
    nicht 0 EUR/kWh."""
    result = evaluate_static_tariff(
        _config(tariff_type=TariffType.FIXED), _local(2026, 3, 1, 12)
    )

    assert result.quote is None
    assert result.reason is QuoteUnavailable.TARIFF_INCOMPLETE
    assert result.price_eur_kwh is None


# --------------------------------------------------------------------------
# Tageszeitabhängig
# --------------------------------------------------------------------------
def test_time_of_use_falls_back_to_the_base_price_outside_all_windows() -> None:
    config = _config(
        tariff_type=TariffType.TIME_OF_USE,
        tou_base_price_eur_kwh=0.30,
        windows=(_window("06:00:00", "09:00:00", 0.40),),
    )

    result = evaluate_static_tariff(config, _local(2026, 3, 1, 12))

    assert result.quote.price_eur_kwh == 0.30
    assert result.quote.source is QuoteSource.TIME_OF_USE_BASE
    assert result.quote.valid_from == _local(2026, 3, 1, 9)
    assert result.quote.valid_until == _local(2026, 3, 2, 6)


@pytest.mark.parametrize(
    ("hour", "minute", "expected"),
    [
        (5, 59, 0.30),  # kurz vor dem Fenster
        (6, 0, 0.40),  # Start inklusive
        (8, 59, 0.40),
        (9, 0, 0.30),  # Ende exklusive
    ],
)
def test_time_of_use_window_is_half_open(
    hour: int, minute: int, expected: float
) -> None:
    """Start inklusive, Ende exklusive - siehe REQ-ECONOMICS-TARIFFS."""
    config = _config(
        tariff_type=TariffType.TIME_OF_USE,
        tou_base_price_eur_kwh=0.30,
        windows=(_window("06:00:00", "09:00:00", 0.40),),
    )

    result = evaluate_static_tariff(config, _local(2026, 3, 1, hour, minute))

    assert result.quote.price_eur_kwh == expected


@pytest.mark.parametrize(
    ("hour", "expected"),
    [(21, 0.30), (22, 0.20), (23, 0.20), (0, 0.20), (5, 0.20), (6, 0.30)],
)
def test_time_of_use_window_may_cross_midnight(hour: int, expected: float) -> None:
    config = _config(
        tariff_type=TariffType.TIME_OF_USE,
        tou_base_price_eur_kwh=0.30,
        windows=(_window("22:00:00", "06:00:00", 0.20),),
    )

    result = evaluate_static_tariff(config, _local(2026, 3, 1, hour))

    assert result.quote.price_eur_kwh == expected


def test_time_of_use_supports_eight_windows() -> None:
    """Genau acht Gruppen sind vorgesehen; alle müssen greifen."""
    windows = tuple(
        _window(f"{index * 2:02d}:00:00", f"{index * 2 + 1:02d}:00:00", 0.1 * index)
        for index in range(1, ECONOMICS_TOU_WINDOW_COUNT + 1)
    )
    config = _config(
        tariff_type=TariffType.TIME_OF_USE,
        tou_base_price_eur_kwh=0.30,
        windows=windows,
    )

    prices = [
        evaluate_static_tariff(config, _local(2026, 3, 1, index * 2)).quote
        for index in range(1, ECONOMICS_TOU_WINDOW_COUNT + 1)
    ]

    assert [round(quote.price_eur_kwh, 5) for quote in prices] == [
        round(0.1 * index, 5) for index in range(1, ECONOMICS_TOU_WINDOW_COUNT + 1)
    ]
    assert all(quote.source is QuoteSource.TIME_OF_USE_WINDOW for quote in prices)


def test_time_of_use_without_base_price_reports_incomplete() -> None:
    result = evaluate_static_tariff(
        _config(
            tariff_type=TariffType.TIME_OF_USE,
            windows=(_window("06:00:00", "09:00:00", 0.40),),
        ),
        _local(2026, 3, 1, 7),
    )

    assert result.quote is None
    assert result.reason is QuoteUnavailable.TARIFF_INCOMPLETE


def test_time_of_use_validity_spans_the_whole_day_without_windows() -> None:
    config = _config(tariff_type=TariffType.TIME_OF_USE, tou_base_price_eur_kwh=0.30)

    result = evaluate_static_tariff(config, _local(2026, 3, 1, 12))

    assert result.quote.valid_from == _local(2026, 3, 1, 0)
    assert result.quote.valid_until == _local(2026, 3, 2, 0)


# --------------------------------------------------------------------------
# Sommerzeit
# --------------------------------------------------------------------------
def test_spring_forward_never_produces_the_skipped_local_hour() -> None:
    """Am 29.03.2026 springt Europa/Berlin von 02:00 auf 03:00. Die
    übersprungene Ortszeit existiert nicht und darf deshalb nie den Preis
    des 02:00-Fensters liefern."""
    config = _config(
        tariff_type=TariffType.TIME_OF_USE,
        tou_base_price_eur_kwh=0.30,
        windows=(_window("02:00:00", "03:00:00", 0.10),),
    )

    start = datetime(2026, 3, 29, 0, 30, tzinfo=BERLIN)
    prices = []
    for step in range(6):
        moment = dt_util.as_local(dt_util.as_utc(start) + timedelta(minutes=30 * step))
        prices.append((moment.hour, evaluate_static_tariff(config, moment).quote))

    assert not any(hour == 2 for hour, _quote in prices)
    assert all(quote.price_eur_kwh == 0.30 for _hour, quote in prices)


def test_fall_back_prices_both_occurrences_of_the_repeated_hour_alike() -> None:
    """Am 25.10.2026 tritt 02:30 Ortszeit zweimal auf - beide Male gilt
    derselbe lokale Zeitfensterpreis."""
    config = _config(
        tariff_type=TariffType.TIME_OF_USE,
        tou_base_price_eur_kwh=0.30,
        windows=(_window("02:00:00", "03:00:00", 0.10),),
    )

    first = datetime(2026, 10, 25, 2, 30, tzinfo=BERLIN, fold=0)
    second = datetime(2026, 10, 25, 2, 30, tzinfo=BERLIN, fold=1)

    assert dt_util.as_utc(first) != dt_util.as_utc(second)
    assert evaluate_static_tariff(config, first).quote.price_eur_kwh == 0.10
    assert evaluate_static_tariff(config, second).quote.price_eur_kwh == 0.10


# --------------------------------------------------------------------------
# Zeitfensterregeln
# --------------------------------------------------------------------------
def test_empty_window_group_is_valid() -> None:
    assert validate_window_fields(1, None, None, None) is None


@pytest.mark.parametrize(
    ("start", "end", "price"),
    [
        (dt_time(6), None, 0.4),
        (None, dt_time(9), 0.4),
        (dt_time(6), dt_time(9), None),
    ],
)
def test_partially_filled_window_group_is_incomplete(start, end, price) -> None:
    issue = validate_window_fields(3, start, end, price)

    assert issue.index == 3
    assert issue.error is TariffWindowError.INCOMPLETE


def test_identical_start_and_end_is_invalid() -> None:
    """`start == end` ist ungültig und bedeutet ausdrücklich nicht
    "ganzer Tag"."""
    issue = validate_window_fields(1, dt_time(6), dt_time(6), 0.4)

    assert issue.error is TariffWindowError.ZERO_LENGTH


def test_touching_windows_do_not_overlap() -> None:
    """Halboffene Intervalle: Ende des einen darf Start des nächsten sein."""
    windows = [
        (1, _window("06:00:00", "09:00:00", 0.4)),
        (2, _window("09:00:00", "12:00:00", 0.5)),
    ]

    assert find_overlapping_window(windows) is None


def test_overlapping_windows_are_rejected() -> None:
    windows = [
        (1, _window("06:00:00", "10:00:00", 0.4)),
        (2, _window("09:00:00", "12:00:00", 0.5)),
    ]

    issue = find_overlapping_window(windows)

    assert issue.index == 2
    assert issue.error is TariffWindowError.OVERLAP


def test_overlap_is_detected_across_midnight() -> None:
    """Die Überschneidungsprüfung läuft auf der zyklischen
    24-Stunden-Zeitleiste, nicht auf dem Kalendertag."""
    windows = [
        (1, _window("22:00:00", "06:00:00", 0.2)),
        (2, _window("05:00:00", "07:00:00", 0.5)),
    ]

    assert find_overlapping_window(windows).index == 2


# --------------------------------------------------------------------------
# Pflichtfelder und Wertebereiche
# --------------------------------------------------------------------------
def test_disabled_tariff_needs_no_feed_in_price() -> None:
    assert validate_tariff(TariffConfig()) is QuoteUnavailable.TARIFF_DISABLED


@pytest.mark.parametrize("feed_in", [None, -0.01, 2.01, float("nan")])
def test_enabled_tariff_requires_a_valid_feed_in_price(feed_in) -> None:
    """PV-Energie darf nie als kostenlos gelten: ohne gültige
    Einspeisevergütung entsteht auch dann kein Quote, wenn der Arbeitspreis
    hinterlegt ist. Der Options Flow verhindert das zwar, ein von Hand
    bearbeiteter Options-Eintrag nicht."""
    config = TariffConfig(
        tariff_type=TariffType.FIXED,
        feed_in_price_eur_kwh=feed_in,
        fixed_import_price_eur_kwh=0.34,
    )

    assert validate_tariff(config) is QuoteUnavailable.TARIFF_INCOMPLETE

    result = evaluate_static_tariff(config, _local(2026, 3, 1, 12))

    assert result.quote is None
    assert result.reason is QuoteUnavailable.TARIFF_INCOMPLETE


async def test_dynamic_tariff_also_requires_the_feed_in_price(hass) -> None:
    """Die Pflicht gilt für jede aktivierte Tarifart, nicht nur die
    statischen."""
    await _set_price(hass, "sensor.strompreis", "0.25")
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
        },
    )

    result = coordinator.tariff_provider.quote()

    assert result.quote is None
    assert result.reason is QuoteUnavailable.TARIFF_INCOMPLETE


@pytest.mark.parametrize("price", [-2.01, 5.01, 999.0])
def test_out_of_range_stored_prices_make_the_tariff_incomplete(price) -> None:
    """Ein gespeicherter Arbeitspreis außerhalb von -2 bis 5 EUR/kWh ist
    kein Arbeitspreis - er darf nicht als gültiger Preis durchgehen."""
    config = _config(tariff_type=TariffType.FIXED, fixed_import_price_eur_kwh=price)

    assert validate_tariff(config) is QuoteUnavailable.TARIFF_INCOMPLETE


def test_out_of_range_window_price_makes_the_tariff_incomplete() -> None:
    config = _config(
        tariff_type=TariffType.TIME_OF_USE,
        tou_base_price_eur_kwh=0.30,
        windows=(_window("06:00:00", "09:00:00", 999.0),),
    )

    assert validate_tariff(config) is QuoteUnavailable.TARIFF_INCOMPLETE


# --------------------------------------------------------------------------
# Options-Abbildung
# --------------------------------------------------------------------------
def test_options_without_economics_configuration_are_disabled() -> None:
    """Bestehende Installationen ohne Wirtschaftlichkeitskonfiguration
    bleiben deaktiviert - nichts wird automatisch aktiviert."""
    config = tariff_config_from_options({CONF_PRICE_SENSOR: "sensor.strompreis"})

    assert config.tariff_type is TariffType.DISABLED
    assert config.enabled is False
    assert config.feed_in_price_eur_kwh is None


def test_unknown_tariff_type_falls_back_to_disabled() -> None:
    config = tariff_config_from_options({CONF_ECONOMICS_TARIFF_TYPE: "kaputt"})

    assert config.tariff_type is TariffType.DISABLED


def test_options_are_mapped_to_windows_in_order() -> None:
    options = {
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
        economics_tou_window_key(1): {
            CONF_ECONOMICS_WINDOW_START: "22:00:00",
            CONF_ECONOMICS_WINDOW_END: "06:00:00",
            CONF_ECONOMICS_WINDOW_PRICE: 0.21,
        },
        # Lücke: Gruppe 2 bleibt leer, Gruppe 3 ist wieder befüllt.
        economics_tou_window_key(3): {
            CONF_ECONOMICS_WINDOW_START: "12:00:00",
            CONF_ECONOMICS_WINDOW_END: "14:00:00",
            CONF_ECONOMICS_WINDOW_PRICE: 0.15,
        },
    }

    config = tariff_config_from_options(options)

    assert config.feed_in_price_eur_kwh == 0.0786
    assert [window.price_eur_kwh for window in config.windows] == [0.21, 0.15]


def test_windows_of_other_tariff_types_are_ignored() -> None:
    """Ein Festpreistarif darf keine übrig gebliebenen Zeitfenster erben."""
    options = {
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value,
        CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.34,
        economics_tou_window_key(1): {
            CONF_ECONOMICS_WINDOW_START: "22:00:00",
            CONF_ECONOMICS_WINDOW_END: "06:00:00",
            CONF_ECONOMICS_WINDOW_PRICE: 0.21,
        },
    }

    assert tariff_config_from_options(options).windows == ()


def test_a_completely_empty_window_group_stays_valid() -> None:
    """Ein nie ausgefülltes Fenster ist ein gültiger Anwenderzustand, kein
    korrupter Store - windows_valid bleibt True."""
    options = {
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
        economics_tou_window_key(1): {},
    }

    config = tariff_config_from_options(options)

    assert config.windows == ()
    assert config.windows_valid is True


def test_a_window_group_with_a_missing_price_makes_the_tariff_incomplete() -> None:
    """Ein von Hand beschädigter Store kann Start/Ende ohne Preis enthalten
    - das darf nicht stillschweigend als "kein Fenster" verschwinden,
    sondern muss die Quote-Erzeugung blockieren (siehe
    TariffConfig.windows_valid)."""
    options = {
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
        economics_tou_window_key(1): {
            CONF_ECONOMICS_WINDOW_START: "22:00:00",
            CONF_ECONOMICS_WINDOW_END: "06:00:00",
            # CONF_ECONOMICS_WINDOW_PRICE fehlt.
        },
    }

    config = tariff_config_from_options(options)

    assert config.windows == ()
    assert config.windows_valid is False
    result = evaluate_static_tariff(config, _local(2026, 3, 1, 12))
    assert result.quote is None
    assert result.reason is QuoteUnavailable.TARIFF_INCOMPLETE


def test_a_window_group_of_the_wrong_type_makes_the_tariff_incomplete() -> None:
    """Eine Section, die kein Mapping ist (z. B. ein String statt eines
    Objekts), ist unlesbar und darf nicht als leer durchgehen."""
    options = {
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
        economics_tou_window_key(1): "kaputt",
    }

    config = tariff_config_from_options(options)

    assert config.windows_valid is False
    assert validate_tariff(config) is QuoteUnavailable.TARIFF_INCOMPLETE


def test_an_invalid_window_group_hides_other_valid_windows_behind_incomplete() -> None:
    """Ein kaputtes Fenster darf die Auswertung nicht einfach mit den
    übrigen, zufällig noch lesbaren Fenstern weiterrechnen lassen."""
    options = {
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
        economics_tou_window_key(1): {
            CONF_ECONOMICS_WINDOW_START: "06:00:00",
            CONF_ECONOMICS_WINDOW_END: "09:00:00",
            CONF_ECONOMICS_WINDOW_PRICE: 0.40,
        },
        economics_tou_window_key(2): {
            CONF_ECONOMICS_WINDOW_START: "20:00:00",
            # end/price fehlen - Gruppe 2 ist kaputt.
        },
    }

    config = tariff_config_from_options(options)

    assert len(config.windows) == 1
    assert config.windows_valid is False
    result = evaluate_static_tariff(config, _local(2026, 3, 1, 7))
    assert result.quote is None
    assert result.reason is QuoteUnavailable.TARIFF_INCOMPLETE


@pytest.mark.parametrize("value", [None, "", "abc", float("nan"), float("inf"), True])
def test_unusable_price_values_stay_none(value) -> None:
    assert parse_price(value) is None


@pytest.mark.parametrize("value", ["25:00:00", "abc", "12", None, 7])
def test_unusable_time_values_stay_none(value) -> None:
    assert parse_time(value) is None


def test_time_is_parsed_with_and_without_seconds() -> None:
    assert parse_time("06:30") == dt_time(6, 30)
    assert parse_time("06:30:15") == dt_time(6, 30, 15)


# --------------------------------------------------------------------------
# Einheiten
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("configured", "sensor_unit", "expected"),
    [
        ("auto", "ct/kWh", 0.01),
        ("auto", "Cent/kWh", 0.01),
        ("auto", "EUR/kWh", 1.0),
        ("auto", "€/kWh", 1.0),
        ("auto", None, 1.0),
        ("auto", "kWh", None),
        ("auto", "%", None),
        (PRICE_UNIT_CT_KWH, "EUR/kWh", 0.01),
    ],
)
def test_unit_factor(configured, sensor_unit, expected) -> None:
    """Dieselbe Einheitenlogik nutzen Ladeplanung und Wirtschaftlichkeit."""
    assert unit_factor(configured, sensor_unit) == expected


# --------------------------------------------------------------------------
# Home-Assistant-Adapter
# --------------------------------------------------------------------------
def _coordinator(hass, options: dict) -> SaxPowerCoordinator:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    return SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
        options=options,
    )


async def test_provider_is_disabled_without_configuration(hass) -> None:
    coordinator = _coordinator(hass, {})

    result = coordinator.tariff_provider.quote()

    assert result.quote is None
    assert result.reason is QuoteUnavailable.TARIFF_DISABLED
    assert coordinator.tariff_provider.feed_in_price_eur_kwh is None


async def test_provider_exposes_feed_in_price_when_enabled(hass) -> None:
    coordinator = _coordinator(
        hass,
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.34,
        },
    )

    assert coordinator.tariff_provider.feed_in_price_eur_kwh == 0.0786
    assert coordinator.tariff_provider.quote().quote.price_eur_kwh == 0.34


async def test_dynamic_tariff_uses_the_price_forecast_slot(hass) -> None:
    """Der dynamische Tarif nutzt denselben Sensor und dieselbe
    Attribut-/Einheitenlogik wie die Ladeplanung."""
    now = dt_util.now()
    start = now.replace(minute=0, second=0, microsecond=0)
    hass.states.async_set(
        "sensor.strompreis",
        "0.25",
        {
            "unit_of_measurement": "EUR/kWh",
            "raw_today": [
                {
                    "start": (start - timedelta(hours=1)).isoformat(),
                    "end": start.isoformat(),
                    "value": 0.11,
                },
                {
                    "start": start.isoformat(),
                    "end": (start + timedelta(hours=1)).isoformat(),
                    "value": 0.22,
                },
            ],
        },
    )
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    quote = coordinator.tariff_provider.quote(now).quote

    assert quote.price_eur_kwh == pytest.approx(0.22)
    assert quote.source is QuoteSource.DYNAMIC_FORECAST
    assert quote.valid_from == start
    assert quote.valid_until == start + timedelta(hours=1)


async def test_dynamic_tariff_converts_cent_state_without_forecast(hass) -> None:
    """Ohne Preisvorschau ist der Sensorzustand der aktuelle Preis - in der
    konfigurierten Einheit."""
    hass.states.async_set(
        "sensor.strompreis", "24.5", {"unit_of_measurement": "ct/kWh"}
    )
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_PRICE_UNIT: PRICE_UNIT_CT_KWH,
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    quote = coordinator.tariff_provider.quote().quote

    assert quote.price_eur_kwh == pytest.approx(0.245)
    assert quote.source is QuoteSource.DYNAMIC_STATE


@pytest.mark.parametrize(
    ("state", "attributes", "expected"),
    [
        ("unknown", {}, QuoteUnavailable.PRICE_SENSOR_UNAVAILABLE),
        ("unavailable", {}, QuoteUnavailable.PRICE_SENSOR_UNAVAILABLE),
        ("keine Ahnung", {}, QuoteUnavailable.PRICE_NOT_NUMERIC),
        ("nan", {}, QuoteUnavailable.PRICE_NOT_FINITE),
        ("inf", {}, QuoteUnavailable.PRICE_NOT_FINITE),
        (
            "0.25",
            {"unit_of_measurement": "kWh"},
            QuoteUnavailable.PRICE_UNIT_UNSUPPORTED,
        ),
    ],
)
async def test_dynamic_tariff_reports_a_reason_instead_of_zero(
    hass, state, attributes, expected
) -> None:
    """Fehlende oder unbrauchbare Werte ergeben None samt Grund - niemals
    0 EUR/kWh."""
    hass.states.async_set("sensor.strompreis", state, attributes)
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    result = coordinator.tariff_provider.quote()

    assert result.quote is None
    assert result.price_eur_kwh is None
    assert result.reason is expected


async def test_dynamic_tariff_rejects_a_stale_price_forecast(hass) -> None:
    """Eine Preisvorschau, die den Auswertungszeitpunkt nicht abdeckt, ist
    ein Fehlerfall - kein Grund, auf den Sensorzustand auszuweichen."""
    stale = dt_util.now() - timedelta(days=3)
    hass.states.async_set(
        "sensor.strompreis",
        "0.25",
        {
            "unit_of_measurement": "EUR/kWh",
            "raw_today": [
                {
                    "start": stale.isoformat(),
                    "end": (stale + timedelta(hours=1)).isoformat(),
                    "value": 0.11,
                }
            ],
        },
    )
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    result = coordinator.tariff_provider.quote()

    assert result.quote is None
    assert result.reason is QuoteUnavailable.PRICE_FORECAST_OUT_OF_RANGE


@pytest.mark.parametrize("state", ["999", "-2.5", "24.5"])
async def test_dynamic_state_outside_the_price_range_is_rejected(hass, state) -> None:
    """Ein Sensorwert außerhalb von -2 bis 5 EUR/kWh ist kein
    Arbeitspreis, sondern ein falsch skalierter oder schlicht falscher Wert
    - typisch ein in EUR/kWh gelesener ct/kWh-Wert."""
    hass.states.async_set(
        "sensor.strompreis", state, {"unit_of_measurement": "EUR/kWh"}
    )
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    result = coordinator.tariff_provider.quote()

    assert result.quote is None
    assert result.reason is QuoteUnavailable.PRICE_OUT_OF_RANGE


async def test_dynamic_forecast_outside_the_price_range_is_rejected(hass) -> None:
    now = dt_util.now()
    start = now.replace(minute=0, second=0, microsecond=0)
    hass.states.async_set(
        "sensor.strompreis",
        "0.25",
        {
            "unit_of_measurement": "EUR/kWh",
            "raw_today": [
                {
                    "start": start.isoformat(),
                    "end": (start + timedelta(hours=1)).isoformat(),
                    "value": 999,
                }
            ],
        },
    )
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    result = coordinator.tariff_provider.quote(now)

    assert result.quote is None
    assert result.reason is QuoteUnavailable.PRICE_OUT_OF_RANGE


async def test_unreadable_price_forecast_does_not_fall_back_to_the_state(hass) -> None:
    """Eine vorhandene, aber unlesbare Preisvorschau ist etwas anderes als
    gar keine Vorschau: Der Sensorzustand darf sie nicht stillschweigend
    ersetzen, sonst rechnet die Wirtschaftlichkeit mit einem Preis, dessen
    Gültigkeitszeitraum niemand kennt."""
    hass.states.async_set(
        "sensor.strompreis",
        "0.25",
        {
            "unit_of_measurement": "EUR/kWh",
            "raw_today": [
                {"beginn": "heute frueh", "betrag": "guenstig"},
                {"beginn": "heute mittag", "betrag": "teuer"},
            ],
        },
    )
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    result = coordinator.tariff_provider.quote()

    assert result.quote is None
    assert result.reason is QuoteUnavailable.PRICE_FORECAST_UNREADABLE


@pytest.mark.parametrize(
    "forecast",
    [
        {"08:00": 0.21, "09:00": 0.24},  # Mapping statt Liste
        "0.21, 0.24, 0.31",  # String statt Liste
        [{"beginn": "heute frueh", "betrag": "guenstig"}],  # Liste, aber unlesbar
        0,  # skalare Null: vorhanden, aber unlesbar - nicht "fehlt"
        False,
        0.0,
    ],
)
async def test_explicit_forecast_attribute_counts_even_with_a_foreign_type(
    hass, forecast
) -> None:
    """Wer ein Attribut ausdrücklich als Preisquelle benennt, bekommt es
    auch dann als verbindliche Vorschau gewertet, wenn der Sensor dessen
    Datentyp ändert - sonst fiele die Auswertung stillschweigend auf den
    Sensorzustand zurück."""
    hass.states.async_set(
        "sensor.strompreis",
        "0.25",
        {"unit_of_measurement": "EUR/kWh", "preisliste": forecast},
    )
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_PRICE_ATTRIBUTE: "preisliste",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    result = coordinator.tariff_provider.quote()

    assert result.quote is None
    assert result.reason is QuoteUnavailable.PRICE_FORECAST_UNREADABLE


@pytest.mark.parametrize("forecast", [[], {}, "", None])
async def test_explicit_forecast_attribute_without_a_value_allows_the_state(
    hass, forecast
) -> None:
    """Ein leeres oder fehlendes Attribut ist keine vorhandene Vorschau -
    dann bleibt der Sensorzustand die gültige Quelle."""
    attributes = {"unit_of_measurement": "EUR/kWh"}
    if forecast is not None:
        attributes["preisliste"] = forecast
    hass.states.async_set("sensor.strompreis", "0.25", attributes)
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_PRICE_ATTRIBUTE: "preisliste",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    quote = coordinator.tariff_provider.quote().quote

    assert quote.price_eur_kwh == pytest.approx(0.25)
    assert quote.source is QuoteSource.DYNAMIC_STATE


async def test_a_foreign_attribute_type_without_an_explicit_choice_is_ignored(
    hass,
) -> None:
    """Ohne ausdrückliche Angabe wird nur geraten: ein bekannter
    Attributname mit fremdem Datentyp darf nicht als Vorschau gelten, sonst
    blockiert ein gleichnamiges Attribut anderer Bedeutung die Auswertung."""
    hass.states.async_set(
        "sensor.strompreis",
        "0.25",
        {"unit_of_measurement": "EUR/kWh", "prices": "siehe Anbieter-App"},
    )
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    quote = coordinator.tariff_provider.quote().quote

    assert quote.price_eur_kwh == pytest.approx(0.25)
    assert quote.source is QuoteSource.DYNAMIC_STATE


async def test_an_empty_forecast_attribute_still_allows_the_state(hass) -> None:
    """Ein leeres Vorschau-Attribut ist keine vorhandene Vorschau - der
    Sensorzustand bleibt die gültige Quelle."""
    hass.states.async_set(
        "sensor.strompreis",
        "0.25",
        {"unit_of_measurement": "EUR/kWh", "raw_today": []},
    )
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    quote = coordinator.tariff_provider.quote().quote

    assert quote.price_eur_kwh == pytest.approx(0.25)
    assert quote.source is QuoteSource.DYNAMIC_STATE


async def test_dynamic_tariff_without_a_sensor_reports_a_reason(hass) -> None:
    coordinator = _coordinator(
        hass,
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    assert (
        coordinator.tariff_provider.quote().reason
        is QuoteUnavailable.PRICE_SENSOR_NOT_CONFIGURED
    )


async def test_dynamic_tariff_reports_a_missing_entity(hass) -> None:
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.gibt_es_nicht",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )

    assert (
        coordinator.tariff_provider.quote().reason
        is QuoteUnavailable.PRICE_SENSOR_MISSING
    )


# --------------------------------------------------------------------------
# Lebenszyklus der Zustandsbeobachter
# --------------------------------------------------------------------------
async def _set_price(hass, entity_id: str, value: str) -> None:
    hass.states.async_set(entity_id, value, {"unit_of_measurement": "EUR/kWh"})
    await hass.async_block_till_done()


async def test_setup_reacts_to_price_sensor_changes(hass) -> None:
    """Ein Zustandswechsel des dynamischen Sensors wirkt sofort - ohne
    Config-Entry-Reload."""
    await _set_price(hass, "sensor.strompreis", "0.25")
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )
    coordinator.tariff_provider.async_setup()

    assert coordinator.tariff_provider.last_result.price_eur_kwh == pytest.approx(0.25)

    await _set_price(hass, "sensor.strompreis", "0.31")

    assert coordinator.tariff_provider.last_result.price_eur_kwh == pytest.approx(0.31)

    coordinator.tariff_provider.async_shutdown()


async def test_repeated_setup_does_not_register_a_second_listener(hass) -> None:
    """async_setup ist idempotent: mehrfaches Aufsetzen darf denselben
    Sensor nicht doppelt beobachten."""
    await _set_price(hass, "sensor.strompreis", "0.25")
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )
    provider = coordinator.tariff_provider
    provider.async_setup()
    provider.async_setup()
    provider.async_setup()

    calls: list[str] = []
    original = provider.evaluate
    provider.evaluate = lambda moment=None: (  # type: ignore[method-assign]
        calls.append("evaluate"),
        original(moment),
    )[1]

    await _set_price(hass, "sensor.strompreis", "0.31")

    assert calls == ["evaluate"]

    provider.async_shutdown()


async def test_options_change_drops_the_listener_on_the_previous_sensor(hass) -> None:
    """Nach einem Sensorwechsel darf der alte Sensor die Auswertung nicht
    mehr beeinflussen."""
    await _set_price(hass, "sensor.alt", "0.25")
    await _set_price(hass, "sensor.neu", "0.40")
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.alt",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )
    provider = coordinator.tariff_provider
    provider.async_setup()

    coordinator.options = {
        CONF_PRICE_SENSOR: "sensor.neu",
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
    }
    provider.async_setup()
    assert provider.last_result.price_eur_kwh == pytest.approx(0.40)

    await _set_price(hass, "sensor.alt", "0.99")
    assert provider.last_result.price_eur_kwh == pytest.approx(0.40)

    await _set_price(hass, "sensor.neu", "0.41")
    assert provider.last_result.price_eur_kwh == pytest.approx(0.41)

    provider.async_shutdown()


async def test_coordinator_shutdown_removes_the_listener(hass) -> None:
    await _set_price(hass, "sensor.strompreis", "0.25")
    coordinator = _coordinator(
        hass,
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
    )
    provider = coordinator.tariff_provider
    provider.async_setup()

    await coordinator.async_shutdown()

    await _set_price(hass, "sensor.strompreis", "0.99")

    assert provider.last_result.price_eur_kwh == pytest.approx(0.25)


async def test_disabled_tariff_registers_no_listener(hass) -> None:
    """Ohne Wirtschaftlichkeitskonfiguration beobachtet der Provider gar
    nichts - eine bestehende Installation bleibt unverändert."""
    await _set_price(hass, "sensor.strompreis", "0.25")
    coordinator = _coordinator(hass, {CONF_PRICE_SENSOR: "sensor.strompreis"})
    provider = coordinator.tariff_provider
    provider.async_setup()

    await _set_price(hass, "sensor.strompreis", "0.31")

    assert provider.last_result.quote is None
    assert provider.last_result.reason is QuoteUnavailable.TARIFF_DISABLED

    provider.async_shutdown()
