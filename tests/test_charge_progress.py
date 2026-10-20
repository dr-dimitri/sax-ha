"""Measured display estimates do not alter control (REQ-BRIDGE-CHARGE)."""

from __future__ import annotations

from typing import Any

import pytest

from custom_components.sax_power.domain.charge_progress import (
    ChargeProgress,
    assess_charge_demand,
    estimate_charge_progress,
)


def _progress(**values: Any) -> ChargeProgress:
    return estimate_charge_progress(
        **(
            {
                "active": True,
                "storage_power_w": -2000,
                "capacity_wh": 10000,
                "soc": 20,
                "target_soc": 80,
                "max_soc": 90,
            }
            | values
        )
    )


@pytest.mark.parametrize("capacity_wh", [7680, 10000, 15360])
def test_estimate_uses_device_capacity_and_actual_power(capacity_wh: int) -> None:
    result = _progress(capacity_wh=capacity_wh)
    assert result.active
    assert result.power_w == 2000
    assert result.target_soc == 80
    assert result.max_soc == 90
    assert result.remaining_seconds == pytest.approx(capacity_wh * 0.6 / 2000 * 3600)


def test_actual_target_and_global_ceiling_both_bound_remaining_energy() -> None:
    assert _progress(target_soc=40).remaining_seconds == 3600
    result = _progress(target_soc=80, max_soc=60)
    assert result.target_soc == 60
    assert result.remaining_seconds == 7200


@pytest.mark.parametrize("window_seconds", [0, 900, 1800])
def test_authorized_bridge_end_bounds_the_duration(window_seconds: float) -> None:
    assert _progress(window_seconds=window_seconds).remaining_seconds == window_seconds


@pytest.mark.parametrize("soc", [80, 85])
def test_target_already_reached_has_no_remaining_energy(soc: float) -> None:
    assert _progress(soc=soc).remaining_seconds == 0


@pytest.mark.parametrize("power", [0, 1000, None, True, "-1000", float("nan")])
def test_only_real_measured_charging_can_be_active(power: Any) -> None:
    assert _progress(storage_power_w=power) == ChargeProgress()
    assert _progress(active=False) == ChargeProgress()


@pytest.mark.parametrize(
    "values",
    [
        {"capacity_wh": None},
        {"capacity_wh": 0},
        {"capacity_wh": True},
        {"capacity_wh": float("inf")},
        {"capacity_wh": 1e308},
        {"soc": None},
        {"soc": -1},
        {"soc": 101},
        {"target_soc": None},
        {"target_soc": 101},
        {"max_soc": -1},
        {"max_soc": float("nan")},
        {"window_seconds": -1},
        {"window_seconds": float("inf")},
    ],
)
def test_invalid_inputs_preserve_measured_activity_without_inventing_eta(
    values: dict[str, Any],
) -> None:
    result = _progress(**values)
    assert result.active
    assert result.power_w == 2000
    assert result.remaining_seconds is None


@pytest.mark.parametrize(
    "soc,horizon,expected", [(20, 3600, "not_needed"), (15, 3600, "needed")]
)
def test_current_energy_verdict_uses_current_soc_and_pv_horizon(
    soc: float, horizon: float, expected: str
) -> None:
    assert (
        assess_charge_demand(
            capacity_wh=10000,
            soc=soc,
            min_soc=10,
            average_discharge_w=1000,
            until_pv_seconds=horizon,
        )
        == expected
    )


@pytest.mark.parametrize(
    "values",
    [
        {"capacity_wh": 0},
        {"soc": None},
        {"soc": 9},
        {"min_soc": True},
        {"average_discharge_w": 0},
        {"average_discharge_w": float("nan")},
        {"until_pv_seconds": -1},
        {"until_pv_seconds": float("inf")},
    ],
)
def test_missing_current_energy_basis_keeps_the_verdict_unknown(
    values: dict[str, Any],
) -> None:
    assert (
        assess_charge_demand(
            **(
                {
                    "capacity_wh": 10000,
                    "soc": 20,
                    "min_soc": 10,
                    "average_discharge_w": 1000,
                    "until_pv_seconds": 3600,
                }
                | values
            )
        )
        == "unknown"
    )
