"""REQ-ECONOMICS-ACCOUNTING: Inventory corrections need fresh idle samples."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.sax_power.coordinator import SaxPowerCoordinator

from .test_coordinator import (
    _FIXED_TARIFF_OPTIONS,
    _make_client,
    _make_coordinator,
)


def _sample(
    coordinator: SaxPowerCoordinator,
    at: float,
    *,
    power: float = 0,
    soc: float = 5,
    fresh: bool = True,
) -> dict[str, Any]:
    moment = datetime(2026, 9, 14, 12, tzinfo=UTC) + timedelta(seconds=at)
    data = {
        "storage_power_active": power,
        "smartmeter_power": 0,
        "battery_soc": soc,
        "battery_soc_min": 5,
        "battery_capacity": 10000,
    }
    if fresh:
        coordinator._high_sample_time = at
        coordinator._high_sample_revision += 1
    with (
        patch("custom_components.sax_power.coordinator.monotonic", return_value=at),
        patch(
            "custom_components.sax_power.coordinator.dt_util.now", return_value=moment
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=moment,
        ),
    ):
        coordinator._accumulate_energy(data)
    return data


@pytest.fixture
def inventory(hass: HomeAssistant) -> SaxPowerCoordinator:
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.options = _FIXED_TARIFF_OPTIONS
    _sample(coordinator, 100, power=1000)
    coordinator._economics_unvalued_inventory_kwh = 0.5
    return coordinator


def test_cached_idle_sample_cannot_delete_inventory_or_create_savings(
    inventory: SaxPowerCoordinator,
) -> None:
    """A service refresh between HIGH reads cannot confirm a second idle tick."""
    _sample(inventory, 102)
    for at in (102.1, 102.5, 103):
        _sample(inventory, at, fresh=False)
        assert inventory._economics_unvalued_inventory_kwh == pytest.approx(0.5)

    data = _sample(inventory, 104, power=1000)
    assert data["economics_avoided_grid_cost"] == 0
    assert inventory._economics_unvalued_inventory_kwh == pytest.approx(0.5 - 2 / 3600)


@pytest.mark.parametrize("stale_refresh", [False, True], ids=["pause", "stale"])
@pytest.mark.parametrize(
    ("soc", "initial", "corrected"), [(5, 0.5, 0.0), (50, 9.0, 5.1)]
)
def test_measurement_gap_requires_two_new_idle_samples(
    inventory: SaxPowerCoordinator,
    stale_refresh: bool,
    soc: float,
    initial: float,
    corrected: float,
) -> None:
    """Neither stale values nor an idle sample before a gap confirm recovery."""
    inventory._economics_unvalued_inventory_kwh = initial
    _sample(inventory, 102, soc=soc)
    if stale_refresh:
        _sample(inventory, 108, soc=soc, fresh=False)
        assert inventory._economics_unvalued_inventory_kwh == pytest.approx(initial)

    _sample(inventory, 110, soc=soc)
    assert inventory._economics_unvalued_inventory_kwh == pytest.approx(initial)
    _sample(inventory, 112, soc=soc)
    assert inventory._economics_unvalued_inventory_kwh == pytest.approx(corrected)


def test_capacity_correction_waits_for_a_second_fresh_idle_sample(
    inventory: SaxPowerCoordinator,
) -> None:
    inventory._economics_unvalued_inventory_kwh = 9.0
    _sample(inventory, 102, soc=50)
    _sample(inventory, 102.5, soc=50, fresh=False)
    assert inventory._economics_unvalued_inventory_kwh == pytest.approx(9.0)
    _sample(inventory, 104, soc=50)
    assert inventory._economics_unvalued_inventory_kwh == pytest.approx(5.1)
