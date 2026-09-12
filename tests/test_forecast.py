"""Tests for framework-independent PV forecast normalization."""

from __future__ import annotations

import pytest

from custom_components.sax_power.domain.forecast import normalize_energy_kwh


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        ("8500", "Wh", 8.5),
        ("8.5", "kWh", 8.5),
        ("0.0085", "MWh", 8.5),
        (8.5, None, 8.5),
    ],
)
def test_normalize_energy_kwh(value, unit, expected: float) -> None:
    assert normalize_energy_kwh(value, unit) == pytest.approx(expected)


@pytest.mark.parametrize("value", ["unbekannt", "nan", "inf", None, True, False])
def test_normalize_energy_kwh_rejects_invalid_values(value) -> None:
    assert normalize_energy_kwh(value, "kWh") is None


@pytest.mark.parametrize("unit", ["W", "kW", "%", "EUR/kWh"])
def test_normalize_energy_kwh_rejects_non_energy_units(unit: str) -> None:
    """REQ-GRID-SERVING-CHARGE: Leistung ist keine nutzbare Energieprognose."""
    assert normalize_energy_kwh("8500", unit) is None


def test_normalize_energy_kwh_rejects_overflow_after_unit_conversion() -> None:
    """REQ-GRID-SERVING-CHARGE: Auch normalisierte Prognosen bleiben endlich."""
    assert normalize_energy_kwh("1e308", "MWh") is None
