"""Tests für die reine ROI-/Amortisationsberechnung."""

import pytest

from custom_components.sax_power.domain.economics_amortization import (
    compute_amortization_progress_percent,
    compute_remaining_to_payback_eur,
    compute_roi_percent,
)


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
