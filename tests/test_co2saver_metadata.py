"""REQ-CO2SAVER-ESTIMATED-INPUT: truthful sampling and gap metadata."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.sensor import DATA_COMPONENT
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.sensor import SENSOR_DESCRIPTIONS, SaxPowerSensor

STARTED = datetime(2026, 9, 7, 12, tzinfo=UTC)
CLOCK = "custom_components.sax_power.coordinator.monotonic"
UTC_CLOCK = "custom_components.sax_power.coordinator.dt_util.utcnow"


@pytest.fixture
async def coordinator(hass: HomeAssistant) -> AsyncIterator[SaxPowerCoordinator]:
    instance = SaxPowerCoordinator(hass, MagicMock(), 64, 100, 10, "co2-metadata")
    await instance.async_load_energy_state()
    yield instance
    await instance.async_shutdown()


def _sample(
    coordinator: SaxPowerCoordinator,
    seconds: float,
    power: Any = 1000,
    *,
    utc: datetime | None = None,
) -> dict[str, Any]:
    coordinator._high_sample_revision += 1
    coordinator._high_sample_time = seconds
    coordinator._high_data = {"smartmeter_power": power}
    data: dict[str, Any] = {}
    with (
        patch(CLOCK, return_value=seconds),
        patch(UTC_CLOCK, return_value=utc or STARTED + timedelta(seconds=seconds)),
    ):
        coordinator._accumulate_grid_energy(data)
    coordinator.data = data
    return data["grid_energy_attributes"]


def test_startup_does_not_claim_a_fresh_measurement(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Stored kWh are not a measurement of the offline/startup period."""
    data: dict[str, Any] = {}
    coordinator._accumulate_grid_energy(data)
    attributes = data["grid_energy_attributes"]
    assert attributes["co2saver_source_type"] == "power_integration"
    assert attributes["co2saver_sample_valid"] is False
    assert attributes["co2saver_sample_time"] is None
    assert attributes["co2saver_segment_id"]
    assert "co2saver_period_end" not in attributes


def test_zero_power_updates_sample_time_without_inventing_energy(
    coordinator: SaxPowerCoordinator,
) -> None:
    first = _sample(coordinator, 0, 0)
    second = _sample(coordinator, 2, 0)
    assert first["co2saver_segment_id"] == second["co2saver_segment_id"]
    assert (
        second["co2saver_sample_time"] == (STARTED + timedelta(seconds=2)).isoformat()
    )
    assert second["co2saver_sample_valid"] is True
    assert coordinator.data["energy_imported_from_grid"] == 0
    assert coordinator.data["energy_exported_to_grid"] == 0
    assert "co2saver_period_end" not in second


def test_cached_refresh_preserves_the_original_sample_time(
    coordinator: SaxPowerCoordinator,
) -> None:
    attributes = _sample(coordinator, 0)
    data: dict[str, Any] = {}
    with (
        patch(CLOCK, return_value=1),
        patch(UTC_CLOCK, return_value=STARTED + timedelta(seconds=1)),
    ):
        coordinator._accumulate_grid_energy(data)
    assert data["grid_energy_attributes"] == attributes


@pytest.mark.parametrize("invalid", [None, float("nan"), True, "1000"])
def test_a_gap_between_co2_polls_changes_segment_after_recovery(
    coordinator: SaxPowerCoordinator, invalid: Any
) -> None:
    before_gap = _sample(coordinator, 0)
    _sample(coordinator, 2)
    stored = coordinator.data["energy_imported_from_grid"]
    invalid_sample = _sample(coordinator, 4, invalid)
    assert invalid_sample["co2saver_sample_valid"] is False
    assert invalid_sample["co2saver_sample_time"] is None
    assert invalid_sample["co2saver_segment_id"] != before_gap["co2saver_segment_id"]
    recovered = _sample(coordinator, 6)
    assert recovered["co2saver_segment_id"] == invalid_sample["co2saver_segment_id"]
    assert recovered["co2saver_sample_valid"] is True
    assert coordinator.data["energy_imported_from_grid"] == stored
    assert (
        recovered["co2saver_sample_time"]
        == (STARTED + timedelta(seconds=6)).isoformat()
    )


def test_long_gap_changes_segment_without_counting_the_missing_time(
    coordinator: SaxPowerCoordinator,
) -> None:
    before = _sample(coordinator, 0)
    after = _sample(coordinator, 60)
    assert after["co2saver_segment_id"] != before["co2saver_segment_id"]
    assert after["co2saver_sample_valid"] is True
    assert coordinator.data["energy_imported_from_grid"] == 0


def test_stale_cache_invalidates_once_and_preserves_totals(
    coordinator: SaxPowerCoordinator,
) -> None:
    before = _sample(coordinator, 0)
    data: dict[str, Any] = {}
    with patch(CLOCK, return_value=5):
        coordinator._accumulate_grid_energy(data)
        invalid = data["grid_energy_attributes"]
        coordinator._accumulate_grid_energy(data)
    assert invalid == data["grid_energy_attributes"]
    assert invalid["co2saver_segment_id"] != before["co2saver_segment_id"]
    assert invalid["co2saver_sample_valid"] is False


async def test_reload_preserves_energy_but_starts_a_new_segment(
    hass: HomeAssistant,
    coordinator: SaxPowerCoordinator,
) -> None:
    _sample(coordinator, 0)
    before = _sample(coordinator, 2)
    stored = coordinator.data["energy_imported_from_grid"]
    await coordinator._async_flush_energy_state()
    restarted = SaxPowerCoordinator(hass, MagicMock(), 64, 100, 10, "co2-metadata")
    await restarted.async_load_energy_state()
    try:
        after = _sample(restarted, 60)
        assert after["co2saver_segment_id"] != before["co2saver_segment_id"]
        assert restarted.data["energy_imported_from_grid"] == stored
        assert after["accounting_started_at"] == before["accounting_started_at"]
    finally:
        await restarted.async_shutdown()


def test_clock_rollback_starts_a_new_segment(
    coordinator: SaxPowerCoordinator,
) -> None:
    before = _sample(coordinator, 0)
    after = _sample(coordinator, 2, utc=STARTED - timedelta(seconds=10))
    assert after["co2saver_segment_id"] != before["co2saver_segment_id"]
    assert coordinator.data["energy_imported_from_grid"] == 0


def test_both_sensors_publish_identical_metadata_and_keep_counter_precision(
    coordinator: SaxPowerCoordinator,
) -> None:
    _sample(coordinator, 0, 1000)
    attributes = _sample(coordinator, 2, 1000)
    sensors = {
        description.key: SaxPowerSensor(coordinator, "co2-metadata", description)
        for description in SENSOR_DESCRIPTIONS
        if description.key in ("energy_imported_from_grid", "energy_exported_to_grid")
    }
    for entity in sensors.values():
        assert entity.extra_state_attributes == attributes
        assert "co2saver_sample_time" in entity._unrecorded_attributes
    assert sensors["energy_imported_from_grid"].native_value == 0.001
    assert sensors["energy_exported_to_grid"].native_value == 0


async def test_zero_energy_is_republished_with_fresh_metadata_in_ha(
    hass: HomeAssistant, coordinator: SaxPowerCoordinator, freezer: Any
) -> None:
    """CO2 Saver sees a new live report even when neither grid counter increases."""
    freezer.move_to(STARTED)
    assert await async_setup_component(hass, "sensor", {})
    _sample(coordinator, 0, 0)
    sensors = [
        SaxPowerSensor(coordinator, "co2-metadata", description)
        for description in SENSOR_DESCRIPTIONS
        if description.key in ("energy_imported_from_grid", "energy_exported_to_grid")
    ]
    await hass.data[DATA_COMPONENT].async_add_entities(sensors)
    try:
        initial = [hass.states.get(entity.entity_id) for entity in sensors]
        assert all(state is not None and state.state == "0.0" for state in initial)
        freezer.move_to(STARTED + timedelta(seconds=2))
        _sample(coordinator, 2, 0)
        coordinator.async_set_updated_data(dict(coordinator.data))
        await hass.async_block_till_done()
        for entity, previous in zip(sensors, initial, strict=True):
            state = hass.states.get(entity.entity_id)
            assert state is not None and previous is not None
            assert state.state == "0.0"
            assert state.last_reported > previous.last_reported
            assert (
                state.attributes["co2saver_sample_time"]
                == (STARTED + timedelta(seconds=2)).isoformat()
            )
            assert state.attributes["co2saver_sample_valid"] is True
    finally:
        for entity in sensors:
            await entity.async_remove()
