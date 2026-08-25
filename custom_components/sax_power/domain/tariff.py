"""Framework-independent tariff model for the economics evaluation.

Siehe anforderung.yaml, REQ-ECONOMICS-TARIFFS. Dieses Modul kennt weder
Home Assistant noch pymodbus: es beschreibt nur, welcher Netzbezugspreis
zu einer gegebenen Ortszeit gilt. Den Zugriff auf Options- und
Sensorzustände übernimmt der Adapter economics.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from datetime import time as dt_time
from enum import StrEnum

from ..const import (
    MAX_ECONOMICS_FEED_IN_PRICE,
    MAX_ECONOMICS_IMPORT_PRICE,
    MIN_ECONOMICS_FEED_IN_PRICE,
    MIN_ECONOMICS_IMPORT_PRICE,
)
from .scheduling import is_time_in_window, windows_overlap

_SECONDS_PER_DAY = 24 * 3600


class TariffType(StrEnum):
    """Unterstützte Tarifarten (stabile Options-Werte, siehe config_flow)."""

    DISABLED = "disabled"
    FIXED = "fixed"
    TIME_OF_USE = "time_of_use"
    DYNAMIC = "dynamic"


class QuoteSource(StrEnum):
    """Woher ein PriceQuote stammt - für Diagnose und Nachvollziehbarkeit."""

    FIXED = "fixed"
    TIME_OF_USE_BASE = "time_of_use_base"
    TIME_OF_USE_WINDOW = "time_of_use_window"
    DYNAMIC_FORECAST = "dynamic_forecast"
    DYNAMIC_STATE = "dynamic_state"


class QuoteUnavailable(StrEnum):
    """Maschinenlesbarer Grund, warum kein Preis bestimmbar ist.

    Ein fehlender Preis ist immer None plus einer dieser Gründe - nie
    0 EUR/kWh: ein stillschweigender Nullpreis würde Netzbezug als
    kostenlos bewerten und jede spätere Wirtschaftlichkeitsrechnung
    unbemerkt verfälschen.
    """

    TARIFF_DISABLED = "tariff_disabled"
    TARIFF_INCOMPLETE = "tariff_incomplete"
    PRICE_SENSOR_NOT_CONFIGURED = "price_sensor_not_configured"
    PRICE_SENSOR_MISSING = "price_sensor_missing"
    PRICE_SENSOR_UNAVAILABLE = "price_sensor_unavailable"
    PRICE_NOT_NUMERIC = "price_not_numeric"
    PRICE_NOT_FINITE = "price_not_finite"
    PRICE_UNIT_UNSUPPORTED = "price_unit_unsupported"
    PRICE_FORECAST_UNREADABLE = "price_forecast_unreadable"
    PRICE_FORECAST_OUT_OF_RANGE = "price_forecast_out_of_range"
    PRICE_OUT_OF_RANGE = "price_out_of_range"


class TariffWindowError(StrEnum):
    """Regelverstoß einer Zeitfenstergruppe im Options Flow."""

    INCOMPLETE = "incomplete"
    ZERO_LENGTH = "zero_length"
    OVERLAP = "overlap"


@dataclass(frozen=True, slots=True)
class DailyPriceWindow:
    """Ein täglich wiederkehrendes Preisfenster in lokaler Zeit.

    Halboffen (Start inklusive, Ende exklusive) und ausdrücklich auch über
    Mitternacht hinweg gültig. `start == end` ist kein "ganzer Tag",
    sondern ungültig - siehe validate_window_fields.
    """

    start: dt_time
    end: dt_time
    price_eur_kwh: float

    def contains(self, moment: dt_time) -> bool:
        return is_time_in_window(moment, self.start, self.end)

    def overlaps(self, other: DailyPriceWindow) -> bool:
        return windows_overlap(self.start, self.end, other.start, other.end)


@dataclass(frozen=True, slots=True)
class TariffConfig:
    """Vollständige Tarifkonfiguration eines Config Entry.

    Alle Preise sind variable Brutto-Arbeitspreise in EUR/kWh. Monatlicher
    Grundpreis, Boni, außerhalb des Arbeitspreises ausgewiesene Steuern und
    sonstige Fixkosten sind ausdrücklich nicht Teil dieser Rechnung.
    """

    tariff_type: TariffType = TariffType.DISABLED
    feed_in_price_eur_kwh: float | None = None
    fixed_import_price_eur_kwh: float | None = None
    tou_base_price_eur_kwh: float | None = None
    windows: tuple[DailyPriceWindow, ...] = ()

    @property
    def enabled(self) -> bool:
        return self.tariff_type is not TariffType.DISABLED


@dataclass(frozen=True, slots=True)
class PriceQuote:
    """Der zu einem Zeitpunkt gültige Netzbezugspreis.

    `valid_from`/`valid_until` beschreiben das Intervall, für das genau
    dieser Preis gilt. Beim Festpreis sind beide None: er gilt unbegrenzt,
    und nur so ist jeder Quote eines Festpreistarifs identisch.
    """

    price_eur_kwh: float
    source: QuoteSource
    valid_from: datetime | None = None
    valid_until: datetime | None = None


@dataclass(frozen=True, slots=True)
class QuoteResult:
    """Entweder ein Quote oder ein maschinenlesbarer Grund - nie beides."""

    quote: PriceQuote | None = None
    reason: QuoteUnavailable | None = None

    @property
    def price_eur_kwh(self) -> float | None:
        return None if self.quote is None else self.quote.price_eur_kwh


@dataclass(frozen=True, slots=True)
class TariffWindowIssue:
    """Ein Regelverstoß samt der (1-basierten) Nummer seiner Gruppe."""

    index: int
    error: TariffWindowError


def validate_window_fields(
    index: int,
    start: dt_time | None,
    end: dt_time | None,
    price_eur_kwh: float | None,
) -> TariffWindowIssue | None:
    """Prüft eine einzelne Zeitfenstergruppe des Options Flow.

    Eine Gruppe ist entweder vollständig leer (dann existiert das Fenster
    schlicht nicht) oder vollständig befüllt. Alles dazwischen ist ein
    Eingabefehler und darf nicht stillschweigend zu einem halben Fenster
    werden.
    """
    values = (start, end, price_eur_kwh)
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        return TariffWindowIssue(index, TariffWindowError.INCOMPLETE)
    if start == end:
        return TariffWindowIssue(index, TariffWindowError.ZERO_LENGTH)
    return None


def find_overlapping_window(
    windows: Sequence[tuple[int, DailyPriceWindow]],
) -> TariffWindowIssue | None:
    """Erste Gruppe, die sich mit einer vorherigen überschneidet.

    Angrenzende Grenzen (Ende des einen == Start des nächsten) sind
    erlaubt, weil die Intervalle halboffen sind.
    """
    for position, (index, window) in enumerate(windows):
        for _earlier_index, earlier in windows[:position]:
            if window.overlaps(earlier):
                return TariffWindowIssue(index, TariffWindowError.OVERLAP)
    return None


def is_valid_import_price(price: float | None) -> bool:
    """Ob `price` ein zulässiger Arbeitspreis für Netzbezug ist.

    Der negative Bereich ist bewusst zugelassen (börsengekoppelte Tarife
    weisen zeitweise negative Arbeitspreise aus); die Obergrenze fängt
    dagegen falsch skalierte Werte ab - ein als EUR/kWh gelesener
    ct/kWh-Wert liegt weit außerhalb.
    """
    return (
        price is not None
        and MIN_ECONOMICS_IMPORT_PRICE <= price <= MAX_ECONOMICS_IMPORT_PRICE
    )


def is_valid_feed_in_price(price: float | None) -> bool:
    """Ob `price` eine zulässige Einspeisevergütung ist."""
    return (
        price is not None
        and MIN_ECONOMICS_FEED_IN_PRICE <= price <= MAX_ECONOMICS_FEED_IN_PRICE
    )


def validate_tariff(config: TariffConfig) -> QuoteUnavailable | None:
    """Grund, warum aus `config` überhaupt kein Quote entstehen darf.

    Läuft vor jeder Quote-Erzeugung - auch beim dynamischen Tarif. Der
    Options Flow lässt eine unvollständige Konfiguration zwar nicht
    speichern, ein von Hand bearbeiteter oder aus einer früheren Version
    stammender Options-Eintrag kann aber trotzdem einen fehlenden oder
    unsinnigen Wert enthalten.

    Die Einspeisevergütung ist dabei genauso Pflicht wie der Arbeitspreis:
    ohne sie wäre die PV-Kilowattstunde im Speicher unbewertet, und
    PV-Energie darf niemals als kostenlos gelten.
    """
    if not config.enabled:
        return QuoteUnavailable.TARIFF_DISABLED
    if not is_valid_feed_in_price(config.feed_in_price_eur_kwh):
        return QuoteUnavailable.TARIFF_INCOMPLETE
    if config.tariff_type is TariffType.FIXED and not is_valid_import_price(
        config.fixed_import_price_eur_kwh
    ):
        return QuoteUnavailable.TARIFF_INCOMPLETE
    if config.tariff_type is TariffType.TIME_OF_USE and not (
        is_valid_import_price(config.tou_base_price_eur_kwh)
        and all(
            is_valid_import_price(window.price_eur_kwh) for window in config.windows
        )
    ):
        return QuoteUnavailable.TARIFF_INCOMPLETE
    return None


def evaluate_static_tariff(config: TariffConfig, moment: datetime) -> QuoteResult:
    """Quote für die nicht-dynamischen Tarifarten.

    `moment` muss eine zeitzonenbehaftete Ortszeit sein. Die Zuordnung
    erfolgt ausschließlich über die lokale Wanduhrzeit - dadurch braucht
    die Sommerzeitumstellung keinen Sonderfall: die im Frühjahr
    übersprungene Ortszeit tritt nie auf, und beide Vorkommen der im Herbst
    doppelten Stunde treffen dasselbe Fenster.
    """
    reason = validate_tariff(config)
    if reason is not None:
        return QuoteResult(reason=reason)

    # Ab hier hat validate_tariff jeden benötigten Preis als vorhanden und
    # im zulässigen Bereich bestätigt.
    if config.tariff_type is TariffType.FIXED:
        return QuoteResult(
            PriceQuote(float(config.fixed_import_price_eur_kwh), QuoteSource.FIXED)
        )

    if config.tariff_type is not TariffType.TIME_OF_USE:
        return QuoteResult(reason=QuoteUnavailable.TARIFF_DISABLED)

    local_time = moment.time()
    price = float(config.tou_base_price_eur_kwh)
    source = QuoteSource.TIME_OF_USE_BASE
    for window in config.windows:
        if window.contains(local_time):
            price = window.price_eur_kwh
            source = QuoteSource.TIME_OF_USE_WINDOW
            break

    valid_from, valid_until = _segment_bounds(moment, config.windows)
    return QuoteResult(PriceQuote(price, source, valid_from, valid_until))


def _segment_bounds(
    moment: datetime, windows: Sequence[DailyPriceWindow]
) -> tuple[datetime, datetime]:
    """Grenzen des Preisabschnitts, in dem `moment` liegt.

    Gerechnet wird bewusst auf der lokalen Wanduhr (Addition auf eine
    zeitzonenbehaftete datetime ist in Python Wanduhr-Arithmetik): Die
    Grenzen sind Ortszeiten, keine festen UTC-Abstände.
    """
    boundaries = sorted(
        {_seconds(window.start) for window in windows}
        | {_seconds(window.end) for window in windows}
    )
    start_of_day = moment.replace(hour=0, minute=0, second=0, microsecond=0)
    if not boundaries:
        return start_of_day, start_of_day + timedelta(days=1)

    now_seconds = _seconds(moment.time())
    earlier = [value for value in boundaries if value <= now_seconds]
    later = [value for value in boundaries if value > now_seconds]
    previous = max(earlier) if earlier else max(boundaries) - _SECONDS_PER_DAY
    following = min(later) if later else min(boundaries) + _SECONDS_PER_DAY
    return (
        start_of_day + timedelta(seconds=previous),
        start_of_day + timedelta(seconds=following),
    )


def _seconds(value: dt_time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second
