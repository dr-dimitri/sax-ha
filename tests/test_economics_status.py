"""Tests für die reine Status-/Abdeckungsableitung (REQ-ECONOMICS-
OBSERVABILITY). Coordinator-seitige Verdrahtung (Store-Fehler-Erkennung,
Preis-Karenzzeit, Herkunftsabdeckung aus echten Zählern) liegt in
tests/test_coordinator.py."""

from __future__ import annotations

import pytest

from custom_components.sax_power.domain.economics_status import (
    EconomicsStatus,
    compute_economics_status,
    compute_price_coverage_percent,
)

_FULLY_HEALTHY = {
    "tariff_enabled": True,
    "storage_error": False,
    "started": True,
    "price_unavailable": False,
    "origin_unavailable": False,
    "charge_price_coverage_percent": 100.0,
    "discharge_price_coverage_percent": 100.0,
}


def test_disabled_wins_over_every_other_problem() -> None:
    """disabled gilt ausschließlich bei deaktiviertem Tarif, schlägt dabei
    aber jeden anderen - auch gleichzeitig zutreffenden - Problemzustand."""
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            "tariff_enabled": False,
            "storage_error": True,
            "started": False,
            "price_unavailable": True,
            "origin_unavailable": True,
            "charge_price_coverage_percent": 0.0,
        }
    )
    assert status is EconomicsStatus.DISABLED


def test_storage_error_wins_over_lower_priority_problems() -> None:
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            "storage_error": True,
            "started": False,
            "price_unavailable": True,
            "origin_unavailable": True,
            "charge_price_coverage_percent": 0.0,
        }
    )
    assert status is EconomicsStatus.STORAGE_ERROR


def test_waiting_for_initial_state_wins_over_lower_priority_problems() -> None:
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            "started": False,
            "price_unavailable": True,
            "origin_unavailable": True,
            "charge_price_coverage_percent": 0.0,
        }
    )
    assert status is EconomicsStatus.WAITING_FOR_INITIAL_STATE


def test_price_unavailable_wins_over_origin_and_coverage() -> None:
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            "price_unavailable": True,
            "origin_unavailable": True,
            "charge_price_coverage_percent": 0.0,
        }
    )
    assert status is EconomicsStatus.PRICE_UNAVAILABLE


def test_origin_unavailable_wins_over_partial_coverage() -> None:
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            "origin_unavailable": True,
            "charge_price_coverage_percent": 0.0,
        }
    )
    assert status is EconomicsStatus.ORIGIN_UNAVAILABLE


@pytest.mark.parametrize(
    ("charge_coverage", "discharge_coverage"),
    [(50.0, 100.0), (100.0, 50.0), (0.0, 0.0)],
)
def test_partial_price_coverage_from_either_side(
    charge_coverage: float, discharge_coverage: float
) -> None:
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            "charge_price_coverage_percent": charge_coverage,
            "discharge_price_coverage_percent": discharge_coverage,
        }
    )
    assert status is EconomicsStatus.PARTIAL_PRICE_COVERAGE


def test_active_when_everything_is_healthy() -> None:
    assert compute_economics_status(**_FULLY_HEALTHY) is EconomicsStatus.ACTIVE


def test_unknown_coverage_does_not_count_as_partial() -> None:
    """None (Zähler noch nicht initialisiert) ist kein Abdeckungsproblem -
    das wird bereits durch waiting_for_initial_state/storage_error
    abgedeckt, bevor die Abdeckung überhaupt geprüft wird."""
    status = compute_economics_status(
        **{
            **_FULLY_HEALTHY,
            "charge_price_coverage_percent": None,
            "discharge_price_coverage_percent": None,
        }
    )
    assert status is EconomicsStatus.ACTIVE


def test_price_coverage_percent_is_100_without_any_relevant_energy() -> None:
    assert compute_price_coverage_percent(0.0, 0.0) == 100.0


def test_price_coverage_percent_is_none_without_initialized_counters() -> None:
    assert compute_price_coverage_percent(None, 1.0) is None
    assert compute_price_coverage_percent(1.0, None) is None


def test_price_coverage_percent_is_energy_based() -> None:
    assert compute_price_coverage_percent(75.0, 25.0) == pytest.approx(75.0)
