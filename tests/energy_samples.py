"""Explicit measurement and accounting inputs for coordinator tests."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import patch

from homeassistant.util import dt as dt_util

from custom_components.sax_power import coordinator as coordinator_module
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.energy_accounting import compute_charge_delta


def accumulate_energy_sample(
    coordinator: SaxPowerCoordinator, data: dict[str, Any]
) -> None:
    """Deliver one decoded HIGH sample at the test's current monotonic time."""
    coordinator._high_sample_time = coordinator_module.monotonic()
    coordinator._high_sample_revision += 1
    coordinator._extended_available = True
    coordinator._accumulate_energy(data)


def accumulate_energy_samples(
    coordinator: SaxPowerCoordinator, data: dict[str, Any]
) -> None:
    """Observe a constant test load every two seconds through the target time."""
    target = coordinator_module.monotonic()
    target_wall = dt_util.now()
    previous = coordinator._energy_last_ts
    if previous is None or data.get("storage_power_active") is None:
        accumulate_energy_sample(coordinator, data)
        return
    at = previous + 2
    while at < target:
        moment = target_wall - timedelta(seconds=target - at)
        with (
            patch("custom_components.sax_power.coordinator.monotonic", return_value=at),
            patch(
                "custom_components.sax_power.coordinator.dt_util.now",
                return_value=moment,
            ),
            patch(
                "custom_components.sax_power.coordinator.dt_util.utcnow",
                return_value=dt_util.as_utc(moment),
            ),
        ):
            accumulate_energy_sample(coordinator, data)
        at += 2
    accumulate_energy_sample(coordinator, data)


def accumulate_economics_interval(
    coordinator: SaxPowerCoordinator, data: dict[str, Any]
) -> None:
    """Feed an already observed interval to the money-accounting boundary.

    Money/ROI tests aggregate hours or days of known observations. Their
    monotonic endpoints describe that aggregate, not two isolated HIGH reads;
    polling freshness is covered by the real TCP measurement regressions.
    """
    at = coordinator_module.monotonic()
    previous = coordinator._energy_last_ts
    power = data.get("storage_power_active")
    coordinator._energy_last_ts = at if power is not None else None
    seconds = at - previous if previous is not None and power is not None else 0.0
    charge = (
        compute_charge_delta(power, data.get("smartmeter_power"), seconds / 3600)
        if seconds > 0
        else None
    )
    discharged = max(power, 0) * seconds / 3600000 if charge is not None else 0.0
    coordinator._accumulate_economics(data, charge, discharged, seconds)
