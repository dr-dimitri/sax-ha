"""Recorder-Regression für kontrollierte Economics-Bilanzneustarts (#151)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from homeassistant.components.recorder import statistics
from homeassistant.components.recorder.tasks import StatisticsTask
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_recorder_block_till_done,
)

ENTITY_IDS = (
    "sensor.economics_grid_charge_cost",
    "sensor.economics_pv_opportunity_cost",
    "sensor.economics_avoided_grid_cost",
    "sensor.economics_operating_result",
)


@pytest.fixture
def mock_recorder_before_hass(recorder_db_url: str) -> None:
    """Initialisiert die echte Recorder-Datenbank vor der hass-Fixture."""


def _set_totals(hass, values: tuple[float, ...], last_reset: datetime) -> None:
    attributes = {
        "device_class": "monetary",
        "state_class": "total",
        "unit_of_measurement": "EUR",
        "last_reset": last_reset.isoformat(),
    }
    for entity_id, value in zip(ENTITY_IDS, values, strict=True):
        hass.states.async_set(entity_id, str(value), attributes)


async def test_recorder_separates_all_raw_totals_at_balance_restart(
    recorder_mock, freezer
) -> None:
    """Der echte Recorder darf den Sprung auf 0 nicht als Geld-Delta buchen."""
    hass = recorder_mock.hass
    assert await async_setup_component(hass, "sensor", {})
    first_period = datetime(2026, 8, 29, 10, 0, tzinfo=UTC)
    first_reset = first_period - timedelta(days=1)
    second_reset = first_period + timedelta(minutes=6)

    freezer.move_to(first_period + timedelta(seconds=10))
    _set_totals(hass, (0.0, 0.0, 0.0, 0.0), first_reset)
    freezer.move_to(first_period + timedelta(minutes=1))
    _set_totals(hass, (10.0, 10.0, 10.0, -10.0), first_reset)
    await async_recorder_block_till_done(hass)
    recorder_mock.queue_task(StatisticsTask(first_period, False))
    await async_recorder_block_till_done(hass)

    freezer.move_to(second_reset)
    _set_totals(hass, (0.0, 0.0, 0.0, 0.0), second_reset)
    freezer.move_to(first_period + timedelta(minutes=7))
    _set_totals(hass, (2.0, 2.0, 2.0, 2.0), second_reset)
    await async_recorder_block_till_done(hass)
    recorder_mock.queue_task(StatisticsTask(first_period + timedelta(minutes=5), False))
    await async_recorder_block_till_done(hass)

    result = await recorder_mock.async_add_executor_job(
        statistics.statistics_during_period,
        hass,
        first_period,
        first_period + timedelta(minutes=10),
        set(ENTITY_IDS),
        "5minute",
        None,
        {"sum", "state", "last_reset"},
    )

    for entity_id in ENTITY_IDS:
        rows = result[entity_id]
        assert len(rows) == 2
        assert rows[-1]["last_reset"] == second_reset.timestamp()
        assert rows[-1]["state"] == 2.0
    # Die drei positiven Rohsummen bilden zwei Abschnitte mit 10 + 2 EUR.
    for entity_id in ENTITY_IDS[:3]:
        assert result[entity_id][-1]["sum"] == 12.0
    # Auch ein vor dem Neustart negatives Ergebnis beginnt danach sauber bei 2.
    assert result[ENTITY_IDS[3]][-1]["sum"] == -8.0
