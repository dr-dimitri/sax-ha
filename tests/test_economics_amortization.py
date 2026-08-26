"""Tests für die reine ROI-/Amortisationsprognose.

Siehe anforderung.yaml, REQ-ECONOMICS-AMORTIZATION. Reine Funktionstests
ohne Home Assistant - die Coordinator-seitige Tagesbuchhaltung (Tageswechsel,
DST, Neustart, Payback-Erkennung) liegt in tests/test_coordinator.py bzw.
tests/test_economics_persistence.py.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from custom_components.sax_power.domain.economics_amortization import (
    DAY_COVERAGE_THRESHOLD_PERCENT,
    DAY_TIME_COVERAGE_THRESHOLD_PERCENT,
    FORECAST_WINDOW_DAYS,
    MAX_FORECAST_PAYBACK_DAYS,
    SECONDS_PER_DAY,
    DayEconomicsResult,
    ForecastUnavailable,
    compute_amortization_forecast,
    compute_amortization_progress_percent,
    compute_remaining_to_payback_eur,
    compute_roi_percent,
)

TODAY = date(2026, 8, 26)


def _day(
    day: date,
    result: float,
    *,
    priced_charge: float = 1.0,
    unpriced_charge: float = 0.0,
    priced_discharge: float = 1.0,
    unpriced_discharge: float = 0.0,
    observed_seconds: float = SECONDS_PER_DAY,
    day_length_seconds: float = SECONDS_PER_DAY,
) -> DayEconomicsResult:
    return DayEconomicsResult(
        day=day,
        operating_result_eur=result,
        priced_charge_kwh=priced_charge,
        unpriced_charge_kwh=unpriced_charge,
        priced_discharge_kwh=priced_discharge,
        unpriced_discharge_kwh=unpriced_discharge,
        observed_seconds=observed_seconds,
        day_length_seconds=day_length_seconds,
    )


def _full_coverage_window(
    *, count: int = FORECAST_WINDOW_DAYS, result: float = 1.0, end: date = TODAY
) -> list[DayEconomicsResult]:
    return [
        _day(end - timedelta(days=offset), result) for offset in range(1, count + 1)
    ]


# --------------------------------------------------------------------------
# ROI / Fortschritt / Restbetrag
# --------------------------------------------------------------------------
def test_roi_is_none_without_a_positive_investment_cost() -> None:
    assert compute_roi_percent(100.0, None) is None
    assert compute_roi_percent(100.0, 0.0) is None
    assert compute_roi_percent(100.0, -5.0) is None


def test_roi_is_none_without_a_known_operating_result() -> None:
    assert compute_roi_percent(None, 1000.0) is None


def test_roi_stays_negative_and_above_100_unclamped() -> None:
    assert compute_roi_percent(-50.0, 1000.0) == pytest.approx(-5.0)
    assert compute_roi_percent(2500.0, 1000.0) == pytest.approx(250.0)


def test_amortization_progress_clamps_to_0_100() -> None:
    assert compute_amortization_progress_percent(-5.0) == 0.0
    assert compute_amortization_progress_percent(250.0) == 100.0
    assert compute_amortization_progress_percent(42.0) == 42.0
    assert compute_amortization_progress_percent(None) is None


def test_remaining_to_payback_floors_at_zero_once_achieved() -> None:
    assert compute_remaining_to_payback_eur(1000.0, 400.0) == pytest.approx(600.0)
    assert compute_remaining_to_payback_eur(1000.0, 2500.0) == 0.0
    assert compute_remaining_to_payback_eur(None, 400.0) is None
    assert compute_remaining_to_payback_eur(1000.0, None) is None


# --------------------------------------------------------------------------
# Tagesabdeckung
# --------------------------------------------------------------------------
def test_a_day_without_any_relevant_energy_is_fully_covered() -> None:
    day = _day(
        TODAY,
        0.0,
        priced_charge=0.0,
        unpriced_charge=0.0,
        priced_discharge=0.0,
        unpriced_discharge=0.0,
    )

    assert day.price_coverage_percent == 100.0
    assert day.meets_coverage_threshold is True


def test_a_day_at_exactly_the_coverage_threshold_is_accepted() -> None:
    day = _day(
        TODAY, 1.0, priced_charge=95.0, unpriced_charge=5.0, priced_discharge=0.0
    )

    assert day.price_coverage_percent == pytest.approx(DAY_COVERAGE_THRESHOLD_PERCENT)
    assert day.meets_coverage_threshold is True


def test_a_day_just_below_the_coverage_threshold_is_rejected() -> None:
    day = _day(
        TODAY, 1.0, priced_charge=94.9, unpriced_charge=5.1, priced_discharge=0.0
    )

    assert day.meets_coverage_threshold is False


# --------------------------------------------------------------------------
# Prognose: fehlende Investitionskosten / Historie
# --------------------------------------------------------------------------
def test_forecast_unavailable_without_investment_cost() -> None:
    forecast = compute_amortization_forecast(_full_coverage_window(), TODAY, None, None)

    assert forecast.reason is ForecastUnavailable.NO_INVESTMENT_COST
    assert forecast.average_daily_result_eur is None


def test_forecast_excludes_the_current_incomplete_day() -> None:
    """Regel 2: der laufende, unvollständige Tag zählt nicht mit - auch
    wenn er versehentlich mitgeliefert wird."""
    days = _full_coverage_window() + [_day(TODAY, 999.0)]

    forecast = compute_amortization_forecast(days, TODAY, 1000.0, 500.0)

    assert forecast.reason is None
    assert forecast.complete_days_available == FORECAST_WINDOW_DAYS


@pytest.mark.parametrize("count", [0, 1, 29])
def test_forecast_unavailable_with_fewer_than_30_complete_days(count) -> None:
    forecast = compute_amortization_forecast(
        _full_coverage_window(count=count), TODAY, 1000.0, 500.0
    )

    assert forecast.reason is ForecastUnavailable.INSUFFICIENT_HISTORY
    assert forecast.complete_days_available == count


def test_forecast_available_with_exactly_30_complete_days() -> None:
    forecast = compute_amortization_forecast(
        _full_coverage_window(count=30, result=2.0), TODAY, 1000.0, 500.0
    )

    assert forecast.reason is None
    assert forecast.average_daily_result_eur == pytest.approx(2.0)


def test_forecast_uses_only_the_most_recent_30_of_31_days() -> None:
    """31 gespeicherte Tage: nur die jüngsten 30 fließen ein, nicht der
    älteste."""
    days = _full_coverage_window(count=30, result=2.0)
    oldest = _day(TODAY - timedelta(days=31), 100.0)  # würde den Schnitt verfälschen

    forecast = compute_amortization_forecast([oldest, *days], TODAY, 1000.0, 500.0)

    assert forecast.complete_days_available == 31
    assert forecast.average_daily_result_eur == pytest.approx(2.0)
    assert forecast.window_start == TODAY - timedelta(days=30)
    assert forecast.window_end == TODAY - timedelta(days=1)


def test_forecast_rejects_a_gap_even_with_30_buckets_present() -> None:
    """Regel 3: das Fenster ist der lückenlose Kalenderbereich der letzten
    30 Tage - 30 vorhandene, aber über einen größeren Zeitraum verstreute
    Buckets (z. B. nach einer längeren HA-Ausfallzeit nur jeder zweite Tag)
    dürfen keine gültige Prognose ergeben."""
    days = [_day(TODAY - timedelta(days=offset), 5.0) for offset in range(2, 62, 2)]
    assert len(days) == 30

    forecast = compute_amortization_forecast(days, TODAY, 1000.0, 500.0)

    assert forecast.reason is ForecastUnavailable.INSUFFICIENT_HISTORY
    assert forecast.average_daily_result_eur is None


# --------------------------------------------------------------------------
# Prognose: Preisabdeckung
# --------------------------------------------------------------------------
def test_forecast_unavailable_if_a_single_day_misses_the_coverage_threshold() -> None:
    days = _full_coverage_window(count=29)
    bad_day = _day(
        TODAY - timedelta(days=30),
        1.0,
        priced_charge=50.0,
        unpriced_charge=50.0,
        priced_discharge=0.0,
    )

    forecast = compute_amortization_forecast([bad_day, *days], TODAY, 1000.0, 500.0)

    assert forecast.reason is ForecastUnavailable.LOW_PRICE_COVERAGE
    assert forecast.accepted_days == 29
    # Diagnosewert bleibt auch bei einer unzureichenden Prognose gesetzt.
    assert forecast.average_price_coverage_percent is not None
    assert forecast.average_price_coverage_percent < 100.0


def test_forecast_reports_the_average_price_coverage_when_available() -> None:
    forecast = compute_amortization_forecast(
        _full_coverage_window(), TODAY, 1000.0, 500.0
    )

    assert forecast.average_price_coverage_percent == pytest.approx(100.0)


# --------------------------------------------------------------------------
# Prognose: Zeitabdeckung der Tage (Issue #131)
# --------------------------------------------------------------------------
def test_a_fully_observed_day_reports_a_full_time_coverage() -> None:
    day = _day(TODAY - timedelta(days=1), 1.0)

    assert day.time_coverage_percent == pytest.approx(100.0)
    assert day.is_fully_observed is True


def test_time_coverage_uses_the_actual_local_day_length() -> None:
    """Regel 1: Nenner ist die tatsächliche Länge des lokalen
    Kalendertages. Dieselben 24 beobachteten Stunden sind an einem 25h-Tag
    eine Lücke von einer Stunde, an einem 23h-Tag dagegen vollständig."""
    winter_switch = _day(
        TODAY - timedelta(days=1),
        1.0,
        observed_seconds=24 * 3600,
        day_length_seconds=25 * 3600,
    )
    summer_switch = _day(
        TODAY - timedelta(days=1),
        1.0,
        observed_seconds=24 * 3600,
        day_length_seconds=23 * 3600,
    )

    assert winter_switch.time_coverage_percent == pytest.approx(96.0)
    assert winter_switch.is_fully_observed is True
    # Geklemmt: ein Tick über Mitternacht hinaus zählt vollständig zum
    # neuen Tag und darf keine Abdeckung über 100 % erzeugen.
    assert summer_switch.time_coverage_percent == pytest.approx(100.0)


def test_time_coverage_at_the_threshold_still_counts_as_fully_observed() -> None:
    exactly_at = _day(
        TODAY - timedelta(days=1),
        1.0,
        observed_seconds=SECONDS_PER_DAY * DAY_TIME_COVERAGE_THRESHOLD_PERCENT / 100,
    )
    just_below = _day(
        TODAY - timedelta(days=1),
        1.0,
        observed_seconds=SECONDS_PER_DAY
        * (DAY_TIME_COVERAGE_THRESHOLD_PERCENT - 0.1)
        / 100,
    )

    assert exactly_at.is_fully_observed is True
    assert just_below.is_fully_observed is False


def test_forecast_unavailable_if_a_single_day_was_only_partially_observed() -> None:
    """Issue #131: War Home Assistant einen halben Tag lang aus, enthält
    dieser Tag nur einen Teil seines Ergebnisses - er darf den
    30-Tage-Durchschnitt und damit die Jahreshochrechnung und das
    Rückzahlungsdatum nicht als vollwertiger Tag zu pessimistisch machen.
    Wie bei einer zu geringen Preisabdeckung fällt die GESAMTE Prognose
    aus, statt den Tag stillschweigend zu überspringen."""
    days = _full_coverage_window(count=FORECAST_WINDOW_DAYS - 1)
    half_observed = _day(
        TODAY - timedelta(days=FORECAST_WINDOW_DAYS),
        1.0,
        observed_seconds=SECONDS_PER_DAY / 2,
    )

    forecast = compute_amortization_forecast(
        [half_observed, *days], TODAY, 1000.0, 500.0
    )

    assert forecast.reason is ForecastUnavailable.INCOMPLETE_DAYS
    assert forecast.fully_observed_days == FORECAST_WINDOW_DAYS - 1
    assert forecast.average_daily_result_eur is None
    assert forecast.projected_annual_result_eur is None
    assert forecast.estimated_payback_date is None
    # Diagnosewerte bleiben auch bei der abgelehnten Prognose gesetzt.
    assert forecast.average_time_coverage_percent == pytest.approx((29 * 100 + 50) / 30)
    assert forecast.window_start == TODAY - timedelta(days=FORECAST_WINDOW_DAYS)
    assert forecast.window_end == TODAY - timedelta(days=1)


def test_incomplete_days_outrank_a_low_price_coverage() -> None:
    """Die Preisabdeckung eines nur teilweise beobachteten Tages misst nur
    den beobachteten Ausschnitt - der Grund benennt deshalb die
    ursächliche Lücke (Zeit), nicht ihre Folge (Preis)."""
    days = _full_coverage_window(count=FORECAST_WINDOW_DAYS - 1)
    bad_day = _day(
        TODAY - timedelta(days=FORECAST_WINDOW_DAYS),
        1.0,
        priced_charge=0.0,
        unpriced_charge=1.0,
        observed_seconds=SECONDS_PER_DAY / 2,
    )

    forecast = compute_amortization_forecast([bad_day, *days], TODAY, 1000.0, 500.0)

    assert forecast.reason is ForecastUnavailable.INCOMPLETE_DAYS
    assert forecast.accepted_days == FORECAST_WINDOW_DAYS - 1
    assert forecast.fully_observed_days == FORECAST_WINDOW_DAYS - 1


def test_forecast_reports_the_average_time_coverage_when_available() -> None:
    forecast = compute_amortization_forecast(
        _full_coverage_window(), TODAY, 1000.0, 500.0
    )

    assert forecast.reason is None
    assert forecast.fully_observed_days == FORECAST_WINDOW_DAYS
    assert forecast.average_time_coverage_percent == pytest.approx(100.0)


def test_a_day_without_a_known_length_is_never_fully_observed() -> None:
    """Verteidigung gegen einen von Hand auf 0 gesetzten Nenner - lieber
    eine ausgefallene Prognose als eine Division durch 0."""
    day = _day(TODAY - timedelta(days=1), 1.0, day_length_seconds=0.0)

    assert day.time_coverage_percent == 0.0
    assert day.is_fully_observed is False


# --------------------------------------------------------------------------
# Prognose: Durchschnitt, Hochrechnung, Rückzahlungsdatum
# --------------------------------------------------------------------------
def test_forecast_computes_average_and_annual_projection() -> None:
    forecast = compute_amortization_forecast(
        _full_coverage_window(result=3.0), TODAY, 1000.0, 500.0
    )

    assert forecast.average_daily_result_eur == pytest.approx(3.0)
    assert forecast.projected_annual_result_eur == pytest.approx(3.0 * 365.2425)


def test_forecast_computes_a_payback_date_from_a_positive_average() -> None:
    forecast = compute_amortization_forecast(
        _full_coverage_window(result=2.0), TODAY, 1000.0, 100.0
    )

    assert forecast.payback_days == pytest.approx(50.0)
    assert forecast.estimated_payback_date == TODAY + timedelta(days=50)


def test_forecast_rounds_the_payback_date_up() -> None:
    forecast = compute_amortization_forecast(
        _full_coverage_window(result=3.0), TODAY, 1000.0, 100.0
    )

    assert forecast.payback_days == pytest.approx(100 / 3)
    assert forecast.estimated_payback_date == TODAY + timedelta(days=34)  # ceil(33.3)


def test_forecast_leaves_the_payback_date_unknown_for_a_non_positive_average() -> None:
    """Regel 9: nur das Datum bleibt unbekannt, Durchschnitt/Hochrechnung
    werden trotzdem gemeldet - niemals "unendlich" oder ein erfundenes
    Datum."""
    forecast = compute_amortization_forecast(
        _full_coverage_window(result=-1.0), TODAY, 1000.0, 1500.0
    )

    assert forecast.average_daily_result_eur == pytest.approx(-1.0)
    assert forecast.projected_annual_result_eur == pytest.approx(-365.2425)
    assert forecast.payback_days is None
    assert forecast.estimated_payback_date is None


def test_forecast_leaves_the_payback_date_unknown_once_already_achieved() -> None:
    """remaining_to_payback_eur == 0: kein Rückzahlungsdatum aus der
    Prognose - das erledigt der Coordinator separat mit dem persistierten,
    fixen Erreichungszeitpunkt."""
    forecast = compute_amortization_forecast(
        _full_coverage_window(result=5.0), TODAY, 1000.0, 0.0
    )

    assert forecast.payback_days is None
    assert forecast.estimated_payback_date is None


def test_forecast_leaves_the_payback_date_unknown_beyond_the_horizon() -> None:
    """Ein positiver, aber verschwindend kleiner Durchschnitt (Ladekosten
    und vermiedene Kosten heben sich fast auf) ergibt eine Amortisations-
    dauer jenseits von MAX_FORECAST_PAYBACK_DAYS: fachlich derselbe Fall
    wie Regel 9 - nur das Datum bleibt unbekannt, niemals ein
    OverflowError, der über den Coordinator die gesamte Integration
    unavailable machen würde."""
    forecast = compute_amortization_forecast(
        _full_coverage_window(result=0.001), TODAY, 9000.0, 9000.0
    )

    assert forecast.average_daily_result_eur == pytest.approx(0.001)
    assert forecast.projected_annual_result_eur == pytest.approx(0.001 * 365.2425)
    assert forecast.payback_days == pytest.approx(9_000_000.0)
    assert forecast.estimated_payback_date is None


def test_forecast_survives_a_payback_duration_beyond_the_timedelta_range() -> None:
    """Unterhalb von remaining / 1e9 scheitert bereits timedelta() selbst
    ("Python int too large to convert to C int") - auch dieser Fall bleibt
    eine Prognose ohne Datum statt einer Exception."""
    forecast = compute_amortization_forecast(
        _full_coverage_window(result=1e-12), TODAY, 9000.0, 9000.0
    )

    assert forecast.payback_days == pytest.approx(9e15)
    assert forecast.estimated_payback_date is None


def test_forecast_still_reports_a_payback_date_exactly_at_the_horizon() -> None:
    """Die Grenze selbst ist inklusiv - erst darüber entfällt das Datum."""
    remaining = float(MAX_FORECAST_PAYBACK_DAYS)
    forecast = compute_amortization_forecast(
        _full_coverage_window(result=1.0), TODAY, 100_000.0, remaining
    )

    assert forecast.payback_days == pytest.approx(MAX_FORECAST_PAYBACK_DAYS)
    assert forecast.estimated_payback_date == TODAY + timedelta(
        days=MAX_FORECAST_PAYBACK_DAYS
    )

    beyond = compute_amortization_forecast(
        _full_coverage_window(result=1.0), TODAY, 100_000.0, remaining + 1.0
    )

    assert beyond.estimated_payback_date is None
