"""Tests für die reine Status-/Abdeckungsableitung (REQ-ECONOMICS-
OBSERVABILITY). Coordinator-seitige Verdrahtung (Store-Fehler-Erkennung,
Preis-Karenzzeit, Herkunftsabdeckung aus echten Zählern) liegt in
tests/test_coordinator.py."""

from __future__ import annotations

import pytest

from custom_components.sax_power.domain.economics_status import (
    MIN_UNPRICED_KWH_FOR_PARTIAL,
    PRICE_COVERAGE_THRESHOLD_PERCENT,
    EconomicsStatus,
    compute_economics_status,
    compute_price_coverage_percent,
    is_price_coverage_partial,
)

_FULLY_HEALTHY = {
    "tariff_enabled": True,
    "storage_error": False,
    "price_unavailable": False,
    "origin_unavailable": False,
    "priced_charge_kwh_today": 10.0,
    "unpriced_charge_kwh_today": 0.0,
    "priced_discharge_kwh_today": 10.0,
    "unpriced_discharge_kwh_today": 0.0,
}

#: Ein Tag, an dem die Ladung praktisch vollständig unbepreist blieb.
_UNPRICED_DAY = {
    "priced_charge_kwh_today": 0.0,
    "unpriced_charge_kwh_today": 10.0,
}


def test_disabled_wins_over_every_other_problem() -> None:
    """disabled gilt ausschließlich bei deaktiviertem Tarif, schlägt dabei
    aber jeden anderen - auch gleichzeitig zutreffenden - Problemzustand."""
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            **_UNPRICED_DAY,
            "tariff_enabled": False,
            "storage_error": True,
            "price_unavailable": True,
            "origin_unavailable": True,
        }
    )
    assert status is EconomicsStatus.DISABLED


def test_storage_error_wins_over_lower_priority_problems() -> None:
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            **_UNPRICED_DAY,
            "storage_error": True,
            "price_unavailable": True,
            "origin_unavailable": True,
        }
    )
    assert status is EconomicsStatus.STORAGE_ERROR


def test_price_unavailable_wins_over_origin_and_coverage() -> None:
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            **_UNPRICED_DAY,
            "price_unavailable": True,
            "origin_unavailable": True,
        }
    )
    assert status is EconomicsStatus.PRICE_UNAVAILABLE


def test_origin_unavailable_wins_over_partial_coverage() -> None:
    status = compute_economics_status(
        **{**_FULLY_HEALTHY, **_UNPRICED_DAY, "origin_unavailable": True}
    )
    assert status is EconomicsStatus.ORIGIN_UNAVAILABLE


@pytest.mark.parametrize(
    "day",
    [
        pytest.param(_UNPRICED_DAY, id="charge_side"),
        pytest.param(
            {"priced_discharge_kwh_today": 0.0, "unpriced_discharge_kwh_today": 10.0},
            id="discharge_side",
        ),
        pytest.param(
            {"priced_charge_kwh_today": 10.0, "unpriced_charge_kwh_today": 1.0},
            id="just_below_the_relative_threshold",
        ),
    ],
)
def test_partial_price_coverage_from_either_side(day: dict[str, float]) -> None:
    status = compute_economics_status(**{**_FULLY_HEALTHY, **day})
    assert status is EconomicsStatus.PARTIAL_PRICE_COVERAGE


def test_active_when_everything_is_healthy() -> None:
    assert compute_economics_status(**_FULLY_HEALTHY) is EconomicsStatus.ACTIVE


@pytest.mark.parametrize(
    "day",
    [
        pytest.param(
            {"priced_charge_kwh_today": 0.0, "unpriced_charge_kwh_today": 0.01},
            id="tiny_gap_in_an_empty_day",
        ),
        pytest.param(
            {"priced_charge_kwh_today": 100.0, "unpriced_charge_kwh_today": 1.0},
            id="relatively_negligible_gap",
        ),
        pytest.param(
            {"priced_discharge_kwh_today": 0.0, "unpriced_discharge_kwh_today": 0.4},
            id="tiny_gap_on_the_discharge_side",
        ),
    ],
)
def test_a_negligible_gap_stays_active(day: dict[str, float]) -> None:
    """Eine einzelne unbepreiste Kilowattstunde ist im Normalbetrieb
    unvermeidbar und darf keinen Warnzustand auslösen - auch nicht kurz
    nach Mitternacht, wenn der Tagesbucket noch fast leer ist und die
    relative Quote deshalb auf 0 % steht (Issue #134)."""
    status = compute_economics_status(**{**_FULLY_HEALTHY, **day})
    assert status is EconomicsStatus.ACTIVE


def test_unknown_coverage_does_not_count_as_partial() -> None:
    """None (Zähler noch nicht initialisiert) ist kein Abdeckungsproblem -
    das wird bereits durch storage_error abgedeckt, bevor die Abdeckung
    überhaupt geprüft wird."""
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            "priced_charge_kwh_today": None,
            "unpriced_charge_kwh_today": None,
            "priced_discharge_kwh_today": None,
            "unpriced_discharge_kwh_today": None,
        }
    )
    assert status is EconomicsStatus.ACTIVE


def test_partial_needs_both_an_absolute_and_a_relative_gap() -> None:
    """Die absolute Untergrenze schützt den noch leeren Tagesbucket, die
    relative Schwelle einen energiereichen Tag - keine der beiden allein
    genügt."""
    assert is_price_coverage_partial(0.0, MIN_UNPRICED_KWH_FOR_PARTIAL) is True
    assert is_price_coverage_partial(0.0, MIN_UNPRICED_KWH_FOR_PARTIAL / 2) is False
    # Absolut nennenswert, relativ verschwindend (>= 95 % Abdeckung).
    assert is_price_coverage_partial(1000.0, 10.0) is False


def test_partial_is_unknown_safe() -> None:
    assert is_price_coverage_partial(None, 10.0) is False
    assert is_price_coverage_partial(10.0, None) is False


def test_price_coverage_threshold_matches_the_partial_decision() -> None:
    """Die veröffentlichte Quote und die Zustandsentscheidung dürfen nicht
    auseinanderlaufen: exakt auf der Schwelle gilt der Tag noch als
    unauffällig."""
    priced, unpriced = 95.0, 5.0
    assert compute_price_coverage_percent(priced, unpriced) == pytest.approx(
        PRICE_COVERAGE_THRESHOLD_PERCENT
    )
    assert is_price_coverage_partial(priced, unpriced) is False


def test_price_coverage_percent_is_100_without_any_relevant_energy() -> None:
    assert compute_price_coverage_percent(0.0, 0.0) == 100.0


def test_price_coverage_percent_is_none_without_initialized_counters() -> None:
    assert compute_price_coverage_percent(None, 1.0) is None
    assert compute_price_coverage_percent(1.0, None) is None


def test_price_coverage_percent_is_energy_based() -> None:
    assert compute_price_coverage_percent(75.0, 25.0) == pytest.approx(75.0)
