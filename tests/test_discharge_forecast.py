"""Measured window and reset boundaries for REQ-DISCHARGE-FORECAST."""

from __future__ import annotations

from typing import Any

import pytest

from custom_components.sax_power.domain.discharge_forecast import DischargeForecast


def _update(
    forecast: DischargeForecast, time: float, power: float = 1000, **values: Any
) -> float | None:
    return forecast.update(
        time=time,
        power=power,
        **({"capacity_wh": 10000, "soc": 60, "min_soc": 10} | values),
    )


def test_minimum_minute_and_remaining_capacity() -> None:
    forecast = DischargeForecast(max_sample_gap=4)
    for time in range(60):
        assert _update(forecast, time) is None
        assert forecast.average_discharge_w is None
        assert forecast.observation_seconds is None
    assert _update(forecast, 60) == 5 * 3600
    assert forecast.average_discharge_w == 1000
    assert forecast.observation_seconds == 60
    assert _update(forecast, 61, soc=10) == 0
    assert forecast.average_discharge_w == 1000
    assert forecast.observation_seconds == 61
    assert _update(forecast, 62, soc=5) == 0


def test_irregular_intervals_are_time_weighted() -> None:
    forecast = DischargeForecast(max_sample_gap=60)
    _update(forecast, 0, 1000)
    _update(forecast, 10, 2000)
    assert _update(forecast, 60, 9000) == pytest.approx(5000 / (110000 / 60) * 3600)
    assert forecast.average_discharge_w == pytest.approx(110000 / 60)
    assert forecast.observation_seconds == 60


def test_only_last_hour_counts_including_partial_boundary_interval() -> None:
    forecast = DischargeForecast(max_sample_gap=60)
    for time in range(0, 3601, 60):
        _update(forecast, time, 1000 if time < 60 else 2000)
    average = (30 * 1000 + 3570 * 2000) / 3600
    assert _update(forecast, 3630, 2000) == pytest.approx(5000 / average * 3600)
    assert forecast.average_discharge_w == pytest.approx(average)
    assert forecast.observation_seconds == 3600
    assert _update(forecast, 3660, 2000) == 9000
    assert _update(forecast, 3720, 2000) == 9000
    assert forecast.average_discharge_w == 2000
    assert forecast.observation_seconds == 3600


def test_charging_resets_at_sixty_seconds_and_requires_new_discharge() -> None:
    forecast = DischargeForecast(max_sample_gap=4)
    for time in range(61):
        _update(forecast, time)
    for time in range(61, 121):
        assert _update(forecast, time, -1000) is not None
    assert _update(forecast, 121, -1000) is None
    assert forecast.average_discharge_w is None
    assert forecast.observation_seconds is None
    for time in range(122, 240):
        assert _update(forecast, time, -1000 if time < 180 else 0) is None
    for time in range(240, 300):
        assert _update(forecast, time) is None
        assert forecast.average_discharge_w is None
        assert forecast.observation_seconds is None
    assert _update(forecast, 300) == 18000


def test_short_charges_and_idle_preserve_history_with_zero_discharge() -> None:
    forecast = DischargeForecast(max_sample_gap=4)
    for time in range(121):
        power = 1000 if time < 60 or time >= 120 else (-1000 if time < 119 else 0)
        value = _update(forecast, time, power)
    assert value == 36000
    assert forecast.average_discharge_w == 500
    assert forecast.observation_seconds == 120
    for time in range(121, 181):
        assert _update(forecast, time, -1000) is not None
    assert _update(forecast, 181, -1000) is None


def test_idle_before_discharge_does_not_count_as_history() -> None:
    forecast = DischargeForecast(max_sample_gap=60)
    for time in range(0, 361, 60):
        assert _update(forecast, time, 0) is None
    assert _update(forecast, 420) is None
    assert _update(forecast, 480) == 18000


def test_zero_average_has_no_forecast() -> None:
    forecast = DischargeForecast(max_sample_gap=60)
    _update(forecast, 0)
    for time in range(60, 3660, 60):
        assert _update(forecast, time, 0) is not None
    assert _update(forecast, 3660, 0) is None
    assert forecast.average_discharge_w is None
    assert forecast.observation_seconds is None


@pytest.mark.parametrize("gap", [0, -1, 4.01, 3600])
def test_measurement_gaps_or_nonadvancing_time_restart_window(gap: float) -> None:
    forecast = DischargeForecast(max_sample_gap=4)
    for time in range(61):
        _update(forecast, time)
    assert _update(forecast, 60 + gap) is None
    assert forecast.average_discharge_w is None
    assert forecast.observation_seconds is None


@pytest.mark.parametrize("key", ["power", "capacity_wh", "soc", "min_soc"])
@pytest.mark.parametrize("invalid", [None, True, "50", float("nan"), float("inf")])
def test_invalid_measurements_restart_window(key: str, invalid: Any) -> None:
    forecast = DischargeForecast(max_sample_gap=4)
    for time in range(61):
        _update(forecast, time)
    assert _update(forecast, 61, **{key: invalid}) is None
    assert forecast.average_discharge_w is None
    assert forecast.observation_seconds is None
    assert _update(forecast, 62) is None


@pytest.mark.parametrize(
    "values",
    [
        {"soc": -1},
        {"soc": 101},
        {"min_soc": -1},
        {"min_soc": 101},
        {"capacity_wh": 0},
        {"capacity_wh": -1},
    ],
)
def test_invalid_battery_ranges_are_unknown(values: dict[str, float]) -> None:
    forecast = DischargeForecast(max_sample_gap=60)
    _update(forecast, 0)
    assert _update(forecast, 60, **values) is None
    assert forecast.average_discharge_w is None
    assert forecast.observation_seconds is None


def test_explicit_reset_clears_observation_metadata() -> None:
    """REQ-DISCHARGE-FORECAST: a reset invalidates the forecast and its basis."""
    forecast = DischargeForecast(max_sample_gap=60)
    _update(forecast, 0)
    assert _update(forecast, 60) is not None
    forecast.reset()
    assert forecast.average_discharge_w is None
    assert forecast.observation_seconds is None
    assert _update(forecast, 61) is None
