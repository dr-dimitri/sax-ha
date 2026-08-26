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
    FORECAST_WINDOW_DAYS,
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
) -> DayEconomicsResult:
    return DayEconomicsResult(
        day=day,
        operating_result_eur=result,
        priced_charge_kwh=priced_charge,
        unpriced_charge_kwh=unpriced_charge,
        priced_discharge_kwh=priced_discharge,
        unpriced_discharge_kwh=unpriced_discharge,
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
