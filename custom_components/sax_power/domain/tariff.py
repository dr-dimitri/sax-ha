"""Framework-independent tariff model for the economics evaluation.

Siehe anforderung.yaml, REQ-ECONOMICS-TARIFFS. Dieses Modul kennt weder
Home Assistant noch pymodbus: es beschreibt nur, welcher Netzbezugspreis
zu einer gegebenen Ortszeit gilt. Den Zugriff auf Options- und
Sensorzustände übernimmt der Adapter economics.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, tzinfo
from datetime import time as dt_time
from enum import StrEnum

from ..const import (
    MAX_ECONOMICS_FEED_IN_PRICE,
    MAX_ECONOMICS_IMPORT_PRICE,
    MIN_ECONOMICS_FEED_IN_PRICE,
    MIN_ECONOMICS_IMPORT_PRICE,
)
from .scheduling import is_time_in_window, windows_overlap


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

    `windows_valid` ist False, wenn beim Einlesen mindestens eine
    Zeitfenstergruppe vorhanden, aber unvollständig oder unlesbar war
    (application.economics.window_from_section) - anders als eine schlicht
    leere Gruppe (kein Anwenderfehler) darf ein solcher Zustand nicht
    stillschweigend zu weniger Fenstern führen: validate_tariff() lehnt
    dann mit TARIFF_INCOMPLETE ab, statt nur mit den übrigen, zufällig noch
    lesbaren Fenstern weiterzurechnen.
    """

    tariff_type: TariffType = TariffType.DISABLED
    feed_in_price_eur_kwh: float | None = None
    fixed_import_price_eur_kwh: float | None = None
    tou_base_price_eur_kwh: float | None = None
    windows: tuple[DailyPriceWindow, ...] = ()
    windows_valid: bool = True

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
        config.windows_valid
        and is_valid_import_price(config.tou_base_price_eur_kwh)
        and all(
            isinstance(window, DailyPriceWindow)
            and isinstance(window.start, dt_time)
            and isinstance(window.end, dt_time)
            and window.start.tzinfo is None
            and window.end.tzinfo is None
            and window.start != window.end
            and is_valid_import_price(window.price_eur_kwh)
            for window in config.windows
        )
        and find_overlapping_window(tuple(enumerate(config.windows))) is None
    ):
        return QuoteUnavailable.TARIFF_INCOMPLETE
    return None


def daily_base_price_applies(config: TariffConfig | None) -> bool:
    """Ob ein gültiges Tagesprofil eine Lücke mit Basispreis enthält."""
    if (
        config is None
        or config.tariff_type is not TariffType.TIME_OF_USE
        or validate_tariff(config) is not None
    ):
        return False
    coverage = sum(
        (
            datetime.combine(date.min, window.end)
            - datetime.combine(date.min, window.start)
        ).total_seconds()
        % 86400
        for window in config.windows
    )
    return coverage < 86400


def lowest_daily_price(config: TariffConfig | None) -> float | None:
    """Niedrigster tatsächlich vorkommender Preis, REQ-TIME-OF-USE-CHARGE-SOURCE."""
    if (
        config is None
        or config.tariff_type is not TariffType.TIME_OF_USE
        or validate_tariff(config) is not None
    ):
        return None
    prices = [window.price_eur_kwh for window in config.windows]
    if daily_base_price_applies(config):
        assert config.tou_base_price_eur_kwh is not None
        prices.append(config.tou_base_price_eur_kwh)
    return min(prices)


def low_tariff_window(
    config: TariffConfig | None, moment: datetime
) -> PriceQuote | None:
    """Die zusammenhängende aktuelle Niedertarifphase mit echten Zeitgrenzen.

    Gleich billige Fenster und Basispreis-Lücken gehören zur selben Phase,
    auch über Mitternacht hinweg. Nur ein ganztägig konstanter Tarif erhält
    lokale Tagesgrenzen; Monatsfreigaben wendet die Ladepolicy darauf an.
    Siehe REQ-TIME-OF-USE-CHARGE-SOURCE.
    """
    cheapest = lowest_daily_price(config)
    if cheapest is None:
        return None
    assert config is not None
    try:
        quote = evaluate_static_tariff(config, moment).quote
        if quote is None or quote.price_eur_kwh != cheapest:
            return None

        def is_low(instant: datetime) -> bool:
            window = active_window(config, instant.astimezone(moment.tzinfo))
            price = (
                config.tou_base_price_eur_kwh
                if window is None
                else window.price_eur_kwh
            )
            return price == cheapest

        changes = sorted(
            instant
            for instant in _boundary_instants(moment, config.windows)
            if is_low(instant - timedelta(microseconds=1)) != is_low(instant)
        )
        if changes:
            start, end = _bounds_around(moment, changes)
        else:
            start, end = _day_bounds(moment)
        return PriceQuote(cheapest, quote.source, start, end)
    except OverflowError, ValueError:
        return None


def active_window(config: TariffConfig, moment: datetime) -> DailyPriceWindow | None:
    """Das zu `moment` geltende Zeitfenster, sonst None (= Grundpreis).

    Dieselbe Zuordnung, die auch evaluate_static_tariff verwendet -
    bewusst als eigene Funktion, damit die Anzeige des aktiven Fensters
    (REQ-VUE-SAVINGS) nicht mit einer zweiten, irgendwann
    abweichenden Suche arbeitet. `moment` muss eine zeitzonenbehaftete
    Ortszeit sein.
    """
    if config.tariff_type is not TariffType.TIME_OF_USE:
        return None
    local_time = moment.time()
    for window in config.windows:
        if window.contains(local_time):
            return window
    return None


def sorted_windows(config: TariffConfig) -> tuple[DailyPriceWindow, ...]:
    """Zeitfenster nach Beginn sortiert.

    Die Reihenfolge in den Options ist die der acht Eingabegruppen und
    damit beliebig; für eine Anzeige als Tagesplan ist die zeitliche
    Reihenfolge die einzig sinnvolle. Ein über Mitternacht laufendes
    Fenster steht dabei an der Stelle seines Beginns.
    """
    return tuple(sorted(config.windows, key=lambda window: window.start))


def window_as_mapping(window: DailyPriceWindow) -> dict[str, object]:
    """Ein Zeitfenster als reines Mapping für Sensorattribute."""
    return {
        "start": window.start.isoformat(),
        "end": window.end.isoformat(),
        "price_eur_kwh": window.price_eur_kwh,
    }


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

    if moment.utcoffset() is None or (
        moment.astimezone(UTC).astimezone(moment.tzinfo).replace(tzinfo=None)
        != moment.replace(tzinfo=None)
    ):
        return QuoteResult(reason=QuoteUnavailable.TARIFF_INCOMPLETE)

    window = active_window(config, moment)
    if window is None:
        price = float(config.tou_base_price_eur_kwh)
        source = QuoteSource.TIME_OF_USE_BASE
    else:
        price = window.price_eur_kwh
        source = QuoteSource.TIME_OF_USE_WINDOW

    valid_from, valid_until = _segment_bounds(moment, config.windows)
    return QuoteResult(PriceQuote(price, source, valid_from, valid_until))


def _segment_bounds(
    moment: datetime, windows: Sequence[DailyPriceWindow]
) -> tuple[datetime, datetime]:
    """Echte Zeitgrenzen des lokalen Preisabschnitts, einschließlich DST."""
    if not windows:
        return _day_bounds(moment)

    def window_at(instant: datetime) -> int | None:
        local_time = instant.astimezone(moment.tzinfo).time()
        return next(
            (
                index
                for index, window in enumerate(windows)
                if window.contains(local_time)
            ),
            None,
        )

    changes = sorted(
        instant
        for instant in _boundary_instants(moment, windows)
        if window_at(instant - timedelta(microseconds=1)) != window_at(instant)
    )
    return _bounds_around(moment, changes)


def _day_bounds(moment: datetime) -> tuple[datetime, datetime]:
    start = datetime.combine(moment.date(), dt_time(), moment.tzinfo)
    return start, start + timedelta(days=1)


def _boundary_instants(
    moment: datetime, windows: Sequence[DailyPriceWindow]
) -> set[datetime]:
    """Mögliche reale Tarifwechsel aus Wandzeitgrenzen und Uhrumstellungen."""

    zone = moment.tzinfo
    boundaries = {window.start for window in windows} | {
        window.end for window in windows
    }
    candidates: set[datetime] = set()
    # Zwei Nachbartage decken auch einen vollständig übersprungenen
    # Kalendertag ab; feste UTC-Abstände würden lokale Tarife verschieben.
    for day_offset in range(-2, 3):
        day = moment.date() + timedelta(days=day_offset)
        for boundary_time in boundaries:
            wall = datetime.combine(day, boundary_time)
            folds = {
                wall.replace(tzinfo=zone, fold=fold).astimezone(UTC) for fold in (0, 1)
            }
            candidates.update(
                instant
                for instant in folds
                if instant.astimezone(zone).replace(tzinfo=None) == wall
            )
            if len(folds) == 2:
                # REQ-ECONOMICS-TARIFFS: Der Uhrsprung selbst kann das
                # aktive Fenster wechseln, auch ohne Grenze um 02:00/03:00.
                candidates.add(_offset_transition(min(folds), max(folds), zone))

    return candidates


def _bounds_around(
    moment: datetime, changes: Sequence[datetime]
) -> tuple[datetime, datetime]:
    now = moment.astimezone(UTC)
    return (
        max(instant for instant in changes if instant <= now).astimezone(moment.tzinfo),
        min(instant for instant in changes if instant > now).astimezone(moment.tzinfo),
    )


def _offset_transition(
    first: datetime, last: datetime, zone: tzinfo | None
) -> datetime:
    """UTC-Offsetwechsel zwischen den zwei Deutungen einer lokalen Grenze."""
    first = first.replace(microsecond=0)
    last = last.replace(microsecond=0)
    original_offset = first.astimezone(zone).utcoffset()
    while (last - first).total_seconds() > 1:
        middle = first + timedelta(seconds=int((last - first).total_seconds() // 2))
        if middle.astimezone(zone).utcoffset() == original_offset:
            first = middle
        else:
            last = middle
    return last
