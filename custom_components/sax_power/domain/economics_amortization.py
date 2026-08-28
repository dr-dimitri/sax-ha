"""Pure ROI- und Amortisationsprognose-Berechnung.

Siehe anforderung.yaml, REQ-ECONOMICS-AMORTIZATION. Baut auf der
persistierten Netto-Ersparnis sowie auf lokalen Kalendertag-Buckets ihrer
Höchststandszuwächse auf, die der Coordinator aus denselben
EconomicsDelta-Objekten befüllt wie die Gesamtbilanz - keine eigene Uhr,
kein eigener Preisbegriff. Die lokale
Datumsermittlung selbst (Zeitzone, DST) liegt außerhalb dieses Moduls beim
Coordinator; hier wird nur mit bereits bestimmten `date`-Werten gerechnet.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

#: Exakt so viele der jüngsten vollständigen Tage fließen in die Prognose
#: ein - weder mehr (auch wenn mehr gespeichert sind) noch weniger.
FORECAST_WINDOW_DAYS = 30

#: Höchstens so viele abgeschlossene Tages-Buckets werden persistiert.
MAX_STORED_DAYS = 60

#: Mindest-Preisabdeckung, die JEDER Tag im Beobachtungsfenster erreichen
#: muss - unterschreitet auch nur ein Tag diese Schwelle, ist die gesamte
#: Prognose unavailable (siehe compute_amortization_forecast).
DAY_COVERAGE_THRESHOLD_PERCENT = 95.0

#: Regellänge eines Kalendertages in Sekunden - reiner Vorgabewert für
#: DayEconomicsResult.day_length_seconds. Die tatsächliche Länge des
#: lokalen Kalendertages (23/24/25 h an einer DST-Umstellung) bestimmt der
#: Coordinator beim Tagesabschluss, nicht dieses Modul.
SECONDS_PER_DAY = 86_400.0

#: Mindest-Zeitabdeckung, die JEDER Tag im Beobachtungsfenster erreichen
#: muss. Ein nur teilweise beobachteter Kalendertag (Home Assistant war
#: aus, Update, Stromausfall) enthält trotz einwandfreier Preisabdeckung
#: nur einen Teil seines Ergebnisses und würde den 30-Tage-Durchschnitt,
#: die Jahreshochrechnung und das Rückzahlungsdatum systematisch zu
#: pessimistisch machen - fachlich derselbe Fall wie eine zu geringe
#: Preisabdeckung (siehe compute_amortization_forecast, Issue #131).
DAY_TIME_COVERAGE_THRESHOLD_PERCENT = 95.0

#: Mittleres Kalenderjahr inkl. Schaltjahren, für die Hochrechnung auf ein
#: Jahr aus dem 30-Tage-Durchschnitt.
DAYS_PER_YEAR = 365.2425

#: Längste Amortisationsdauer (Tage, ~100 Jahre), für die noch ein
#: Rückzahlungsdatum gemeldet wird. Ein winziger, aber positiver
#: Tagesdurchschnitt (Ladekosten und vermiedene Kosten heben sich fast auf)
#: ergibt sonst eine Tagesanzahl, die `date`/`timedelta` nicht mehr
#: darstellen können - der resultierende OverflowError würde über den
#: Coordinator die gesamte Integration unavailable machen (siehe Issue #130).
MAX_FORECAST_PAYBACK_DAYS = 36_524


class ForecastUnavailable(StrEnum):
    """Maschinenlesbarer Grund, warum keine Prognose möglich ist."""

    NO_INVESTMENT_COST = "no_investment_cost"
    INSUFFICIENT_HISTORY = "insufficient_history"
    INCOMPLETE_DAYS = "incomplete_days"
    LOW_PRICE_COVERAGE = "low_price_coverage"


@dataclass(frozen=True, slots=True)
class DayEconomicsResult:
    """Ein bereits abgeschlossener Kalendertag (lokale Zeitzone).

    `priced_*`/`unpriced_*` sind Energiemengen (kWh), keine Beträge - sie
    bilden ausschließlich die Preisabdeckung des Tages. Herkunft-unbekannt
    geladene Energie zählt zu `unpriced_charge_kwh` (siehe
    domain.economics_accounting.compute_economics_delta); von
    unbewertetem Bestand entladene Energie zählt zu KEINEM der vier Felder,
    weil sie für die Bilanz nicht "relevant" ist (kein Preisbegriff nötig,
    kein Geldwert entstanden) - nur tatsächlich monetarisierbare Energie
    braucht überhaupt einen Preis.

    `observed_seconds`/`day_length_seconds` beschreiben eine zweite,
    davon unabhängige Qualitätsdimension: wie viel dieses Kalendertages
    überhaupt beobachtet wurde (Issue #131). Beide sind bewusst absichernd
    vorbelegt - ein Aufrufer, der sie nicht setzt, erzeugt einen als
    unvollständig geltenden Tag, nie einen fälschlich vollwertigen.
    """

    day: date
    operating_result_eur: float
    priced_charge_kwh: float
    unpriced_charge_kwh: float
    priced_discharge_kwh: float
    unpriced_discharge_kwh: float
    #: Tatsächlich mit Datenpunkten belegte Zeit dieses Tages (Sekunden).
    observed_seconds: float = 0.0
    #: Länge dieses lokalen Kalendertages (Sekunden) - an einer
    #: DST-Umstellung 23 bzw. 25 Stunden, siehe Regel 1.
    day_length_seconds: float = SECONDS_PER_DAY

    @property
    def relevant_kwh(self) -> float:
        """Für die Preisabdeckung relevante Energiemenge dieses Tages."""
        return (
            self.priced_charge_kwh
            + self.unpriced_charge_kwh
            + self.priced_discharge_kwh
            + self.unpriced_discharge_kwh
        )

    @property
    def price_coverage_percent(self) -> float:
        """Anteil (%) der relevanten Energie, die tatsächlich bepreist war.

        Ein Tag ganz ohne relevante Energiebewegung gilt als vollständig
        abgedeckt (100 %) - es gibt schlicht nichts, das hätte unbepreist
        bleiben können.
        """
        relevant = self.relevant_kwh
        if relevant <= 0:
            return 100.0
        priced = self.priced_charge_kwh + self.priced_discharge_kwh
        return priced / relevant * 100

    @property
    def meets_coverage_threshold(self) -> bool:
        return self.price_coverage_percent >= DAY_COVERAGE_THRESHOLD_PERCENT

    @property
    def time_coverage_percent(self) -> float:
        """Anteil (%) des lokalen Kalendertages mit Datenpunkten.

        Nenner ist die tatsächliche Länge dieses Kalendertages, nicht
        pauschal 24 h - ein DST-Tag mit 23 oder 25 Stunden wird dadurch
        weder benachteiligt noch bevorzugt (Regel 1). Auf 100 % geklemmt,
        damit eine Zeitmessung minimal über der Tageslänge (Ticks über
        Mitternacht hinweg zählen vollständig zum neuen Tag) keinen Wert
        über 100 % ergibt.
        """
        if self.day_length_seconds <= 0:
            return 0.0
        return min(self.observed_seconds / self.day_length_seconds * 100, 100.0)

    @property
    def is_fully_observed(self) -> bool:
        return self.time_coverage_percent >= DAY_TIME_COVERAGE_THRESHOLD_PERCENT


@dataclass(frozen=True, slots=True)
class AmortizationForecast:
    """Ergebnis der 30-Tage-Prognose, oder ein Grund, warum keine existiert.

    `estimated_payback_date` ist hier IMMER eine zukünftige Projektion aus
    dem 30-Tage-Durchschnitt - ein bereits erreichtes Payback (Regel 8,
    fixes historisches Datum) verwaltet der Coordinator separat und
    überschreibt dieses Feld dafür, statt es hier zu berechnen. Es kann
    auch bei gesetztem `payback_days` None sein, sobald die Dauer
    MAX_FORECAST_PAYBACK_DAYS überschreitet.
    """

    average_daily_result_eur: float | None = None
    projected_annual_result_eur: float | None = None
    payback_days: float | None = None
    estimated_payback_date: date | None = None
    complete_days_available: int = 0
    accepted_days: int = 0
    #: Tage des Fensters, die DAY_TIME_COVERAGE_THRESHOLD_PERCENT
    #: erreichen - Gegenstück zu accepted_days für die Zeitabdeckung.
    fully_observed_days: int = 0
    window_start: date | None = None
    window_end: date | None = None
    #: Durchschnittliche Preisabdeckung (%) über das Beobachtungsfenster -
    #: gesetzt, sobald ein lückenloses 30-Tage-Fenster vorliegt (auch bei
    #: LOW_PRICE_COVERAGE, als Diagnosewert, wie nah das Fenster an der
    #: Schwelle liegt).
    average_price_coverage_percent: float | None = None
    #: Durchschnittliche Zeitabdeckung (%) über das Beobachtungsfenster -
    #: wie average_price_coverage_percent ein Diagnosewert, der auch bei
    #: einer abgelehnten Prognose gesetzt bleibt.
    average_time_coverage_percent: float | None = None
    reason: ForecastUnavailable | None = None


def compute_roi_percent(
    operating_result_eur: float | None, investment_cost_eur: float | None
) -> float | None:
    """ROI in % der Anschaffungskosten - bewusst ohne Klemmen.

    Negativ (Verlust bislang) und über 100 % (bereits mehrfach
    amortisiert) sind gültige, aussagekräftige Zustände; nur der separate
    Fortschritts-Sensor (compute_amortization_progress_percent) wird für
    eine Gauge auf 0..100 geklemmt.
    """
    if investment_cost_eur is None or investment_cost_eur <= 0:
        return None
    if operating_result_eur is None:
        return None
    return operating_result_eur / investment_cost_eur * 100


def compute_amortization_progress_percent(roi_percent: float | None) -> float | None:
    if roi_percent is None:
        return None
    return max(0.0, min(100.0, roi_percent))


def compute_remaining_to_payback_eur(
    investment_cost_eur: float | None, operating_result_eur: float | None
) -> float | None:
    if investment_cost_eur is None or operating_result_eur is None:
        return None
    return max(investment_cost_eur - operating_result_eur, 0.0)


def compute_amortization_forecast(
    day_results: Sequence[DayEconomicsResult],
    today_local: date,
    investment_cost_eur: float | None,
    remaining_to_payback_eur: float | None,
) -> AmortizationForecast:
    """30-Tage-Prognose aus abgeschlossenen Kalendertagen.

    `day_results` darf den aktuellen, noch laufenden Tag NICHT enthalten
    (Regel 2) - als zusätzliche Absicherung wird trotzdem jeder Eintrag mit
    `day >= today_local` hier verworfen. Das Fenster ist exakt der
    lückenlose Kalenderbereich von `today_local - FORECAST_WINDOW_DAYS` bis
    `today_local - 1 Tag` (Regel 3) - fehlt auch nur einer dieser 30
    konkreten Kalendertage in `day_results` (z. B. nach einer längeren
    Ausfallzeit von Home Assistant), ist das INSUFFICIENT_HISTORY, statt
    stattdessen ältere, außerhalb des Fensters liegende Tage als Lückenfüller
    zu verwenden. Erreicht auch nur einer dieser 30 Tage nicht
    DAY_COVERAGE_THRESHOLD_PERCENT (Regel 4), ist die gesamte Prognose
    LOW_PRICE_COVERAGE - einzelne schlechte Tage werden nicht
    stillschweigend übersprungen. Dieselbe harte Regel gilt für die
    Zeitabdeckung: Wurde auch nur einer der 30 Tage weniger als
    DAY_TIME_COVERAGE_THRESHOLD_PERCENT seiner tatsächlichen Länge
    beobachtet, ist die gesamte Prognose INCOMPLETE_DAYS. Dieser Fall wird
    VOR der Preisabdeckung geprüft, weil die Preisabdeckung eines nur
    teilweise beobachteten Tages selbst nicht aussagekräftig ist (sie misst
    nur den beobachteten Ausschnitt) - der Grund benennt damit die
    ursächliche Lücke, nicht ihre Folge.

    Ein nicht positiver Durchschnitt lässt ausschließlich das
    Rückzahlungsdatum unbekannt (Regel 9); average_daily_result_eur und
    projected_annual_result_eur bleiben trotzdem gesetzt, solange die
    30-Tage-Bedingung erfüllt ist - ein negativer Durchschnitt ist eine
    gültige, aussagekräftige Information. Fachlich derselbe Fall ist eine
    Amortisationsdauer jenseits von MAX_FORECAST_PAYBACK_DAYS: auch dort
    bleibt nur das Datum unbekannt, payback_days selbst bleibt als
    Diagnosewert erhalten.
    """
    if investment_cost_eur is None:
        return AmortizationForecast(reason=ForecastUnavailable.NO_INVESTMENT_COST)

    complete_days = [day for day in day_results if day.day < today_local]
    window_start = today_local - timedelta(days=FORECAST_WINDOW_DAYS)
    window_end = today_local - timedelta(days=1)
    by_day = {day.day: day for day in complete_days}
    window_dates = [
        window_start + timedelta(days=offset) for offset in range(FORECAST_WINDOW_DAYS)
    ]
    if any(day not in by_day for day in window_dates):
        return AmortizationForecast(
            complete_days_available=len(complete_days),
            reason=ForecastUnavailable.INSUFFICIENT_HISTORY,
        )

    window = [by_day[day] for day in window_dates]
    accepted_days = sum(1 for day in window if day.meets_coverage_threshold)
    fully_observed_days = sum(1 for day in window if day.is_fully_observed)
    average_coverage = sum(day.price_coverage_percent for day in window) / len(window)
    average_time_coverage = sum(day.time_coverage_percent for day in window) / len(
        window
    )
    rejected = _window_rejection(fully_observed_days, accepted_days)
    if rejected is not None:
        return AmortizationForecast(
            complete_days_available=len(complete_days),
            accepted_days=accepted_days,
            fully_observed_days=fully_observed_days,
            window_start=window_start,
            window_end=window_end,
            average_price_coverage_percent=average_coverage,
            average_time_coverage_percent=average_time_coverage,
            reason=rejected,
        )

    average = sum(day.operating_result_eur for day in window) / FORECAST_WINDOW_DAYS
    projected_annual = average * DAYS_PER_YEAR

    payback_days: float | None = None
    estimated_payback_date: date | None = None
    if (
        average > 0
        and remaining_to_payback_eur is not None
        and remaining_to_payback_eur > 0
    ):
        payback_days = remaining_to_payback_eur / average
        if payback_days <= MAX_FORECAST_PAYBACK_DAYS:
            estimated_payback_date = today_local + timedelta(
                days=math.ceil(payback_days)
            )

    return AmortizationForecast(
        average_daily_result_eur=average,
        projected_annual_result_eur=projected_annual,
        payback_days=payback_days,
        estimated_payback_date=estimated_payback_date,
        complete_days_available=len(complete_days),
        accepted_days=accepted_days,
        fully_observed_days=fully_observed_days,
        window_start=window_start,
        window_end=window_end,
        average_price_coverage_percent=average_coverage,
        average_time_coverage_percent=average_time_coverage,
    )


def _window_rejection(
    fully_observed_days: int, accepted_days: int
) -> ForecastUnavailable | None:
    """Ablehnungsgrund eines vollständigen 30-Tage-Fensters, oder None.

    Reihenfolge siehe compute_amortization_forecast: die Zeitabdeckung ist
    die ursächlichere Lücke und schlägt deshalb die Preisabdeckung.
    """
    if fully_observed_days < FORECAST_WINDOW_DAYS:
        return ForecastUnavailable.INCOMPLETE_DAYS
    if accepted_days < FORECAST_WINDOW_DAYS:
        return ForecastUnavailable.LOW_PRICE_COVERAGE
    return None
