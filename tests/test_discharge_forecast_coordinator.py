"""Coordinator and entity publication for REQ-DISCHARGE-FORECAST."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.sensor import SENSOR_DESCRIPTIONS, SaxPowerSensor

_CLOCK = "custom_components.sax_power.coordinator.monotonic"
_NOW = datetime(2026, 9, 13, 12, tzinfo=UTC)


@pytest.fixture
async def coordinator(hass: HomeAssistant) -> AsyncIterator[SaxPowerCoordinator]:
    instance = SaxPowerCoordinator(hass, MagicMock(), 64, 100, 10, "forecast-test")
    instance._control_bootstrap_pending = True
    yield instance
    await instance.async_shutdown()


def _sample(
    coordinator: SaxPowerCoordinator, time: float, power: float = 1000
) -> dict[str, Any]:
    coordinator._high_sample_revision += 1
    coordinator._high_sample_time = time
    data = {
        "storage_power_active": power,
        "battery_capacity": 10000,
        "battery_soc": 60,
        "battery_soc_min": 10,
    }
    with (
        patch(_CLOCK, return_value=time),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=_NOW + timedelta(seconds=time),
        ),
    ):
        coordinator._update_discharge_forecast(data)
    return data


async def test_timestamp_entity_and_cached_refresh(
    coordinator: SaxPowerCoordinator,
) -> None:
    for time in range(0, 61, 2):
        data = _sample(coordinator, time)
    expected = _NOW + timedelta(seconds=60, hours=5)
    assert data["discharge_forecast"] == expected
    expected_attributes = {
        "average_discharge_w": 1000,
        "observation_minutes": 1.0,
        "observed_at": (_NOW + timedelta(seconds=60)).isoformat(),
    }
    assert data["discharge_forecast_attributes"] == expected_attributes
    cached = {}
    with patch(_CLOCK, return_value=61):
        coordinator._update_discharge_forecast(cached)
        coordinator._update_discharge_forecast(cached)
    assert cached["discharge_forecast"] == expected
    assert cached["discharge_forecast_attributes"] == expected_attributes
    coordinator.data = cached
    description = next(
        item for item in SENSOR_DESCRIPTIONS if item.key == "discharge_forecast"
    )
    entity = SaxPowerSensor(coordinator, "forecast-test", description)
    assert description.device_class == SensorDeviceClass.TIMESTAMP
    assert description.state_class is None
    assert description.native_unit_of_measurement is None
    assert entity.native_value == expected
    assert entity.extra_state_attributes == expected_attributes


@pytest.mark.parametrize("failure", ["basic", "sunspec", "stale"])
async def test_poll_failures_clear_forecast_and_history(
    coordinator: SaxPowerCoordinator, failure: str
) -> None:
    for time in range(0, 61, 2):
        _sample(coordinator, time)
    if failure == "basic":
        coordinator._async_read_basic = AsyncMock(side_effect=UpdateFailed("offline"))
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
    else:
        coordinator._extended_available = failure != "sunspec"
        data = {}
        with patch(_CLOCK, return_value=65 if failure == "stale" else 62):
            coordinator._update_discharge_forecast(data)
        assert data["discharge_forecast"] is None
        assert data["discharge_forecast_attributes"] == {}
    coordinator._extended_available = True
    restarted = _sample(coordinator, 66)
    assert restarted["discharge_forecast"] is None
    assert restarted["discharge_forecast_attributes"] == {}


async def test_regular_poll_publishes_forecast_without_additional_io(
    coordinator: SaxPowerCoordinator,
) -> None:
    coordinator._async_read_basic = AsyncMock(return_value={"soc": 60})

    async def extended() -> dict[str, Any]:
        coordinator._high_sample_revision += 1
        coordinator._high_sample_time = coordinator._high_sample_revision * 2
        return {
            "storage_power_active": 1000,
            "battery_capacity": 10000,
            "battery_soc": 60,
            "battery_soc_min": 10,
        }

    coordinator._async_read_extended = AsyncMock(side_effect=extended)
    for time in range(2, 63, 2):
        with patch(_CLOCK, return_value=time):
            data = await coordinator._async_update_data()
    assert isinstance(data["discharge_forecast"], datetime)
    assert data["discharge_forecast_attributes"]["observation_minutes"] == 1.0
    assert coordinator._async_read_basic.await_count == 31
    assert coordinator._async_read_extended.await_count == 31
    coordinator.client.read_holding_registers.assert_not_called()
    coordinator.client.write_register.assert_not_called()


async def test_unrepresentable_timestamp_is_unknown(
    coordinator: SaxPowerCoordinator,
) -> None:
    for time in range(0, 61, 2):
        data = _sample(coordinator, time, 1e-10)
    assert data["discharge_forecast"] is None
    assert data["discharge_forecast_attributes"] == {}


async def test_charging_reset_clears_published_observation(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-DISCHARGE-FORECAST: no old plan basis survives sustained charging."""
    for time in range(0, 61, 2):
        _sample(coordinator, time)
    for time in range(62, 123, 2):
        data = _sample(coordinator, time, -1000)
    assert data["discharge_forecast"] is None
    assert data["discharge_forecast_attributes"] == {}


async def test_observation_minutes_preserve_fractional_window(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-DISCHARGE-FORECAST: displayed minutes retain actual elapsed time."""
    for time in range(0, 63, 2):
        data = _sample(coordinator, time)
    assert data["discharge_forecast_attributes"]["observation_minutes"] == 62 / 60
