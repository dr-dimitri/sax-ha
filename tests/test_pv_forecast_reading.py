"""Cached display readings for REQ-VUE-ELECTRICITY-TARIFF."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.pv_forecast_reading import (
    PvForecastReading,
)
from custom_components.sax_power.sensor import (
    SENSOR_DESCRIPTIONS,
    SaxPowerChargingForecastSensor,
)

MODULE = "custom_components.sax_power.infrastructure.pv_forecast_reading"
SOURCE = "sensor.pv_forecast"
ReadingFixture = tuple[PvForecastReading, list[str | None], MagicMock, AsyncMock]


@pytest.fixture
async def reading(hass: HomeAssistant) -> AsyncGenerator[ReadingFixture]:
    selected: list[str | None] = [SOURCE]
    notify = MagicMock()
    reader = PvForecastReading(hass, lambda: selected[0], notify)
    with patch(f"{MODULE}.async_update_entity", new_callable=AsyncMock) as update:
        yield reader, selected, notify, update
        await reader.async_shutdown()


@pytest.mark.parametrize(
    ("state", "unit", "expected"),
    [
        ("0", "kWh", 0),
        ("12.4", "kWh", 12.4),
        ("12400", "Wh", 12.4),
        ("0.0124", "MWh", 12.4),
    ],
)
async def test_energy_content_is_normalized(
    hass: HomeAssistant, reading: ReadingFixture, state: str, unit: str, expected: float
) -> None:
    reader, _, notify, update = reading
    hass.states.async_set(SOURCE, state, {"unit_of_measurement": unit})
    reader.async_setup()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert reader.value_kwh == expected
    assert reader.status == "available"
    assert reader.source_entity_id == SOURCE
    assert reader.last_successful_update is not None
    update.assert_awaited_once_with(hass, SOURCE)
    assert notify.called


@pytest.mark.parametrize(
    ("state", "unit"),
    [
        ("unknown", "kWh"),
        ("unavailable", "kWh"),
        ("", "kWh"),
        ("NaN", "kWh"),
        ("inf", "kWh"),
        ("-1", "kWh"),
        ("4", "W"),
        (None, None),
    ],
)
async def test_invalid_or_missing_source_preserves_last_good_value(
    hass: HomeAssistant, reading: ReadingFixture, state: str | None, unit: str | None
) -> None:
    reader, _, _, _ = reading
    hass.states.async_set(SOURCE, "12.4", {"unit_of_measurement": "kWh"})
    reader.async_setup()
    await hass.async_block_till_done(wait_background_tasks=True)
    last_success = reader.last_successful_update
    if state is None:
        hass.states.async_remove(SOURCE)
    else:
        hass.states.async_set(SOURCE, state, {"unit_of_measurement": unit})
    await reader.async_refresh()

    assert reader.value_kwh == 12.4
    assert reader.status == "available"
    assert reader.last_successful_update == last_success


@pytest.mark.parametrize(
    "error", [HomeAssistantError("source failed"), OSError(), TimeoutError()]
)
async def test_update_exception_retains_value_and_timestamp(
    hass: HomeAssistant, reading: ReadingFixture, error: Exception
) -> None:
    reader, _, _, update = reading
    hass.states.async_set(SOURCE, "12.4", {"unit_of_measurement": "kWh"})
    reader.async_setup()
    await hass.async_block_till_done(wait_background_tasks=True)
    last_success = reader.last_successful_update
    hass.states.async_set(SOURCE, "99", {"unit_of_measurement": "kWh"})
    update.side_effect = error
    await reader.async_refresh()

    assert reader.value_kwh == 12.4
    assert reader.status == "available"
    assert reader.last_successful_update == last_success


async def test_polling_refreshes_every_ten_minutes_without_dashboard(
    hass: HomeAssistant, reading: ReadingFixture, freezer: FrozenDateTimeFactory
) -> None:
    reader, _, _, update = reading
    start = dt_util.utcnow()
    hass.states.async_set(SOURCE, "12.4", {"unit_of_measurement": "kWh"})
    reader.async_setup()
    await hass.async_block_till_done(wait_background_tasks=True)
    hass.states.async_set(SOURCE, "14.8", {"unit_of_measurement": "kWh"})
    reader.async_setup()  # Reconfiguring an unchanged source must not add timers.
    freezer.move_to(start + timedelta(minutes=9, seconds=59))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)
    assert reader.value_kwh == 12.4
    assert update.await_count == 1

    freezer.move_to(start + timedelta(minutes=10))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)
    assert reader.value_kwh == 14.8
    assert update.await_count == 2
    await reader.async_shutdown()
    reader.async_setup()
    reader._async_interval(dt_util.utcnow())
    freezer.move_to(start + timedelta(minutes=20))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)
    assert update.await_count == 2


async def test_pending_refresh_prevents_duplicate_calls_and_shutdown_cancels(
    hass: HomeAssistant, reading: ReadingFixture
) -> None:
    reader, _, _, update = reading
    entered = asyncio.Event()
    blocked = asyncio.Event()

    async def wait(*_: object) -> None:
        entered.set()
        await blocked.wait()

    update.side_effect = wait
    reader.async_setup()
    await entered.wait()
    reader._async_interval(dt_util.utcnow())
    reader._async_interval(dt_util.utcnow())
    assert update.await_count == 1
    task = reader._task
    await reader.async_shutdown()
    assert task.cancelled()


async def test_changed_source_rejects_late_old_response(
    hass: HomeAssistant, reading: ReadingFixture
) -> None:
    reader, selected, _, update = reading
    entered = asyncio.Event()
    release = asyncio.Event()
    other = "sensor.other_forecast"

    async def refresh(_hass: HomeAssistant, source: str) -> None:
        if source == SOURCE:
            entered.set()
            try:
                await release.wait()
            except asyncio.CancelledError:
                await release.wait()
            hass.states.async_set(SOURCE, "99", {"unit_of_measurement": "kWh"})
        else:
            await release.wait()
            hass.states.async_set(other, "5", {"unit_of_measurement": "kWh"})

    update.side_effect = refresh
    hass.states.async_set(SOURCE, "12.4", {"unit_of_measurement": "kWh"})
    reader.async_setup()
    await entered.wait()
    selected[0] = other
    reader.async_setup()
    assert reader.value_kwh is None
    release.set()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert reader.source_entity_id == other
    assert reader.value_kwh == 5
    selected[0] = None
    reader.async_setup()
    assert reader.value_kwh is None
    assert reader.last_successful_update is None


async def test_missing_yield_is_unknown_and_zero_survives_modbus_failure(
    hass: HomeAssistant, reading: ReadingFixture
) -> None:
    reader, _, _, _ = reading
    reader.async_setup()
    await hass.async_block_till_done(wait_background_tasks=True)
    coordinator = MagicMock()
    coordinator.pv_forecast_reading = reader
    coordinator.price_planner.pv_forecast_entity_id = SOURCE
    coordinator.last_update_success = False
    description = next(
        item for item in SENSOR_DESCRIPTIONS if item.key == "charging_pv_forecast"
    )
    sensor = SaxPowerChargingForecastSensor(coordinator, "entry-id", description)
    assert sensor.available
    assert sensor.native_value is None
    assert sensor.extra_state_attributes["reading_status"] == "waiting"
    hass.states.async_set(SOURCE, "0", {"unit_of_measurement": "kWh"})
    await reader.async_refresh()
    assert sensor.available
    assert sensor.native_value == 0
    assert sensor.extra_state_attributes["reading_status"] == "available"
    assert sensor.extra_state_attributes["source_entity_id"] == SOURCE
    coordinator.price_planner.pv_forecast_entity_id = "sensor.new_source"
    assert sensor.native_value is None


@pytest.mark.parametrize("state", [None, "unknown", "unavailable", "NaN", "-1"])
async def test_missing_yield_waits_but_unavailable_or_invalid_yield_reports_error(
    hass: HomeAssistant, reading: ReadingFixture, state: str | None
) -> None:
    """REQ-VUE-ELECTRICITY-TARIFF: pending data and an actual failure differ."""
    reader, _, _, _ = reading
    if state is not None:
        hass.states.async_set(SOURCE, state, {"unit_of_measurement": "kWh"})
    reader.async_setup()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert reader.value_kwh is None
    assert reader.status == ("waiting" if state in (None, "unknown") else "error")


@pytest.mark.parametrize(
    "error", [HomeAssistantError("failed"), OSError(), TimeoutError()]
)
async def test_failed_initial_refresh_notifies_then_recovers_to_zero(
    hass: HomeAssistant, reading: ReadingFixture, error: Exception
) -> None:
    reader, _, notify, update = reading
    update.side_effect = error
    reader.async_setup()
    assert reader.status == "waiting"
    await hass.async_block_till_done(wait_background_tasks=True)
    assert reader.status == "error"
    assert notify.call_count == 2
    update.side_effect = None
    hass.states.async_set(SOURCE, "0", {"unit_of_measurement": "kWh"})
    await reader.async_refresh()
    assert reader.status == "available"
    assert reader.value_kwh == 0


@pytest.mark.parametrize("state", ["unknown", "5"])
async def test_late_failure_from_previous_source_does_not_change_new_status(
    hass: HomeAssistant, reading: ReadingFixture, state: str
) -> None:
    reader, selected, notify, update = reading
    entered = asyncio.Event()
    release = asyncio.Event()
    other = "sensor.other_forecast"

    async def refresh(_hass: HomeAssistant, source: str) -> None:
        if source == SOURCE:
            entered.set()
            try:
                await release.wait()
            except asyncio.CancelledError:
                await release.wait()
            raise HomeAssistantError("old source failed")

    update.side_effect = refresh
    reader.async_setup()
    await entered.wait()
    selected[0] = other
    hass.states.async_set(other, state, {"unit_of_measurement": "kWh"})
    reader.async_setup()
    await reader._task
    notifications = notify.call_count
    release.set()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert reader.status == ("waiting" if state == "unknown" else "available")
    assert notify.call_count == notifications


async def test_unknown_ha_entity_publishes_waiting_error_and_recovery(
    hass: HomeAssistant,
) -> None:
    """REQ-VUE-ELECTRICITY-TARIFF: HA transports the status even without kWh."""
    coordinator = SaxPowerCoordinator(
        hass,
        MagicMock(),
        64,
        100,
        10,
        "yield-status",
        options={"pv_forecast_sensor": SOURCE},
    )
    coordinator.update_interval = None
    reader = coordinator.pv_forecast_reading
    description = next(
        item for item in SENSOR_DESCRIPTIONS if item.key == "charging_pv_forecast"
    )
    sensor = SaxPowerChargingForecastSensor(coordinator, "yield-status", description)
    sensor._attr_device_info = None
    component = EntityComponent(logging.getLogger(__name__), "sensor", hass)
    with patch(f"{MODULE}.async_update_entity", new_callable=AsyncMock) as update:
        reader.async_setup()
        await hass.async_block_till_done(wait_background_tasks=True)
        await component.async_add_entities([sensor])
        try:
            state = hass.states.get(sensor.entity_id)
            assert state.state == "unknown"
            assert state.attributes["source_entity_id"] == SOURCE
            assert state.attributes["reading_status"] == "waiting"
            update.side_effect = HomeAssistantError("source failed")
            await reader.async_refresh()
            state = hass.states.get(sensor.entity_id)
            assert state.state == "unknown"
            assert state.attributes["reading_status"] == "error"
            update.side_effect = None
            hass.states.async_set(SOURCE, "0", {"unit_of_measurement": "kWh"})
            await reader.async_refresh()
            state = hass.states.get(sensor.entity_id)
            assert float(state.state) == 0
            assert state.attributes["reading_status"] == "available"
        finally:
            await reader.async_shutdown()
            await sensor.async_remove()


async def test_real_ha_entity_update_boundary_refreshes_source(
    hass: HomeAssistant,
) -> None:
    class ForecastSource(SensorEntity):
        _attr_should_poll = False
        _attr_native_unit_of_measurement = "kWh"
        _attr_native_value = 1
        entity_id = SOURCE

        async def async_update(self) -> None:
            self._attr_native_value = 12.4

    component = EntityComponent(logging.getLogger(__name__), "sensor", hass)
    await component.async_add_entities([ForecastSource()])
    reader = PvForecastReading(hass, lambda: SOURCE, lambda: None)
    try:
        reader.async_setup()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert hass.states.get(SOURCE).state == "12.4"
        assert reader.value_kwh == 12.4
    finally:
        await reader.async_shutdown()
        await component.get_entity(SOURCE).async_remove()


@pytest.mark.parametrize("initial", [None, 12.4])
async def test_stalled_update_times_out_and_a_later_read_recovers(
    hass: HomeAssistant, reading: ReadingFixture, initial: float | None
) -> None:
    reader, _, _, update = reading
    blocked = asyncio.Event()
    cancelled = asyncio.Event()
    if initial is not None:
        hass.states.async_set(SOURCE, str(initial), {"unit_of_measurement": "kWh"})

    async def wait(*_: object) -> None:
        try:
            await blocked.wait()
        finally:
            cancelled.set()

    update.side_effect = wait
    with patch(f"{MODULE}.UPDATE_TIMEOUT", 0.01):
        reader.async_setup()
        await hass.async_block_till_done(wait_background_tasks=True)
    assert reader.value_kwh == initial
    assert reader.status == ("error" if initial is None else "available")
    assert reader._task.done()
    assert cancelled.is_set()
    update.side_effect = None
    hass.states.async_set(SOURCE, "14.8", {"unit_of_measurement": "kWh"})
    await reader.async_refresh()
    assert reader.value_kwh == 14.8
    assert reader.status == "available"
