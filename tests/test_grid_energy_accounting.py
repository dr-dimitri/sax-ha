"""REQ-GRID-ENERGY: independent integration at the grid connection point."""

from __future__ import annotations

import pytest

from custom_components.sax_power.domain.grid_energy_accounting import (
    GridEnergyDelta,
    compute_grid_energy_delta,
)


@pytest.mark.parametrize(
    ("power", "hours", "expected"),
    [
        (3000.0, 1.0, GridEnergyDelta(3.0, 0.0)),
        (-2000.0, 0.25, GridEnergyDelta(0.0, 0.5)),
        (0.0, 1.0, GridEnergyDelta(0.0, 0.0)),
        (3000.0, 0.0, GridEnergyDelta(0.0, 0.0)),
        (-2000.0, 0.0, GridEnergyDelta(0.0, 0.0)),
        (1500, 2, GridEnergyDelta(3.0, 0.0)),
    ],
)
def test_grid_energy_uses_full_grid_power_and_separate_directions(
    power: float, hours: float, expected: GridEnergyDelta
) -> None:
    """Der gesamte Netzanschlusspunkt zählt einschließlich Hausverbrauch."""
    assert compute_grid_energy_delta(power, hours) == expected


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        True,
        False,
        "1000",
        [],
        float("nan"),
        float("inf"),
        -float("inf"),
        pytest.param(10**1000, id="overflowing-integer"),
    ],
)
def test_invalid_grid_power_never_invents_energy(invalid: object) -> None:
    assert compute_grid_energy_delta(invalid, 1.0) is None


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        True,
        False,
        "1",
        [],
        -1.0,
        float("nan"),
        float("inf"),
        -float("inf"),
        pytest.param(10**1000, id="overflowing-integer"),
    ],
)
def test_invalid_duration_never_invents_energy(invalid: object) -> None:
    assert compute_grid_energy_delta(1000.0, invalid) is None


def test_overflowing_interval_is_rejected() -> None:
    assert compute_grid_energy_delta(1e308, 1e308) is None


def test_alternating_directions_are_accumulated_without_netting() -> None:
    """Gleicher Bezug und gleiche Einspeisung heben sich im Zähler nicht auf."""
    deltas = [
        compute_grid_energy_delta(power, 0.5) for power in (2000, -2000, 4000, -4000)
    ]

    assert sum(delta.imported_kwh for delta in deltas) == pytest.approx(3.0)
    assert sum(delta.exported_kwh for delta in deltas) == pytest.approx(3.0)
