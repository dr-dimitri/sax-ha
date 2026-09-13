"""REQ-VUE-TARIFF-EDITOR: Existing tariff statistics retain their value in cents."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.recorder import Recorder, statistics
from homeassistant.components.recorder.db_schema import Statistics, StatisticsShortTerm
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.tasks import StatisticsTask
from homeassistant.components.recorder.util import session_scope
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.recorder import DATA_INSTANCE
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_recorder_block_till_done,
)

from custom_components.sax_power.const import DOMAIN
from custom_components.sax_power.infrastructure.price_statistics import (
    PRICE_SENSOR_KEYS,
    async_migrate_price_statistics,
)
from custom_components.sax_power.sensor import SENSOR_DESCRIPTIONS, SaxPowerSensor


@pytest.fixture
def mock_recorder_before_hass(recorder_db_url: str) -> None:
    """Use the real fixture database, never the user's Recorder."""


def _register(hass: HomeAssistant, key: str) -> tuple[str, str]:
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    entity = er.async_get(hass).async_get_or_create(
        "sensor",
        DOMAIN,
        f"{entry.entry_id}_{key}",
        config_entry=entry,
        suggested_object_id="renamed_tariff_price",
    )
    return entry.entry_id, entity.entity_id


async def _seed(
    recorder: Recorder,
    entity_id: str,
    *,
    unit: str = "EUR/kWh",
    source: str = "recorder",
) -> None:
    metadata = {
        "source": source,
        "statistic_id": entity_id,
        "name": None,
        "unit_class": None,
        "unit_of_measurement": unit,
        "mean_type": StatisticMeanType.ARITHMETIC,
        "has_sum": False,
    }
    rows = [
        {
            "start": datetime(2026, 8, 1, 10, tzinfo=UTC),
            "mean": -0.01,
            "mean_weight": 300.0,
            "min": -0.05,
            "max": 0.03,
            "state": 0.2,
            "sum": -0.1,
        },
        {
            "start": datetime(2026, 8, 1, 11, tzinfo=UTC),
            "mean": 0.0,
            "mean_weight": 300.0,
            "min": 0.0,
            "max": 0.0,
        },
    ]
    for table in (Statistics, StatisticsShortTerm):
        recorder.async_import_statistics(metadata, rows, table)
    await async_recorder_block_till_done(recorder.hass)


def _read(recorder: Recorder, entity_id: str) -> dict[str, Any]:
    with session_scope(session=recorder.get_session(), read_only=True) as session:
        metadata = statistics.get_metadata_with_session(
            recorder, session, statistic_ids={entity_id}
        )[entity_id]
        result: dict[str, Any] = {"metadata": metadata[1]}
        for table in (Statistics, StatisticsShortTerm):
            rows = (
                session.query(table)
                .filter(table.metadata_id == metadata[0])
                .order_by(table.start_ts)
                .all()
            )
            result[table.__tablename__] = [
                {
                    key: getattr(row, key)
                    for key in (
                        "id",
                        "start_ts",
                        "mean",
                        "mean_weight",
                        "min",
                        "max",
                        "state",
                        "sum",
                    )
                }
                for row in rows
            ]
        return result


@pytest.mark.parametrize("key", sorted(PRICE_SENSOR_KEYS))
async def test_price_statistics_scale_both_tables_and_preserve_ids(
    recorder_mock: Recorder, key: str
) -> None:
    hass = recorder_mock.hass
    entry_id, entity_id = _register(hass, key)
    await _seed(recorder_mock, entity_id)
    await _seed(recorder_mock, "sensor.other_integration_price")
    before = await recorder_mock.async_add_executor_job(_read, recorder_mock, entity_id)

    async_migrate_price_statistics(hass, entry_id, key)
    await async_recorder_block_till_done(hass)

    after = await recorder_mock.async_add_executor_job(_read, recorder_mock, entity_id)
    assert after["metadata"]["unit_of_measurement"] == "ct/kWh"
    for table in ("statistics", "statistics_short_term"):
        assert len(after[table]) == len(before[table]) == 2
        for original, converted in zip(before[table], after[table], strict=True):
            for field in ("mean", "min", "max", "state", "sum"):
                if original[field] is None:
                    assert converted[field] is None
                else:
                    assert converted[field] == pytest.approx(original[field] * 100)
            for field in ("id", "start_ts", "mean_weight"):
                assert converted[field] == original[field]

    # A second startup must not scale already-converted history again.
    async_migrate_price_statistics(hass, entry_id, key)
    await async_recorder_block_till_done(hass)
    assert (
        await recorder_mock.async_add_executor_job(_read, recorder_mock, entity_id)
        == after
    )
    other = await recorder_mock.async_add_executor_job(
        _read, recorder_mock, "sensor.other_integration_price"
    )
    assert other["metadata"]["unit_of_measurement"] == "EUR/kWh"
    assert other["statistics"][0]["mean"] == -0.01


@pytest.mark.parametrize(
    ("key", "unit", "source"),
    [
        ("economics_current_import_price", "ct/kWh", "recorder"),
        ("economics_current_import_price", "EUR/kWh", "another_provider"),
        ("economics_current_import_price", "EUR/MWh", "recorder"),
        ("economics_net_savings", "EUR", "recorder"),
    ],
)
async def test_price_migration_leaves_other_units_sources_and_money_untouched(
    recorder_mock: Recorder, key: str, unit: str, source: str
) -> None:
    hass = recorder_mock.hass
    entry_id, entity_id = _register(hass, key)
    await _seed(recorder_mock, entity_id, unit=unit, source=source)
    before = await recorder_mock.async_add_executor_job(_read, recorder_mock, entity_id)

    async_migrate_price_statistics(hass, entry_id, key)
    await async_recorder_block_till_done(hass)

    assert (
        await recorder_mock.async_add_executor_job(_read, recorder_mock, entity_id)
        == before
    )


async def test_new_cent_statistics_continue_after_migration(
    recorder_mock: Recorder, freezer: Any
) -> None:
    hass = recorder_mock.hass
    assert await async_setup_component(hass, "sensor", {})
    key = "economics_current_import_price"
    entry_id, entity_id = _register(hass, key)
    await _seed(recorder_mock, entity_id)
    async_migrate_price_statistics(hass, entry_id, key)
    await async_recorder_block_till_done(hass)
    start = datetime(2026, 8, 2, 12, tzinfo=UTC)
    freezer.move_to(start)
    hass.states.async_set(
        entity_id,
        "34.21",
        {"unit_of_measurement": "ct/kWh", "state_class": "measurement"},
    )
    await async_recorder_block_till_done(hass)
    freezer.move_to(start + timedelta(minutes=6))
    recorder_mock.queue_task(StatisticsTask(start, False))
    await async_recorder_block_till_done(hass)

    after = await recorder_mock.async_add_executor_job(_read, recorder_mock, entity_id)
    assert after["metadata"]["unit_of_measurement"] == "ct/kWh"
    assert after["statistics_short_term"][-1]["mean"] == pytest.approx(34.21)
    assert after["statistics_short_term"][-1]["start_ts"] == start.timestamp()


async def test_failed_price_metadata_update_rolls_back_values_and_can_retry(
    recorder_mock: Recorder,
) -> None:
    """REQ-VUE-TARIFF-EDITOR: Failed migrations cannot relabel scaled values Euro."""
    hass = recorder_mock.hass
    key = "economics_current_import_price"
    entry_id, entity_id = _register(hass, key)
    await _seed(recorder_mock, entity_id)
    before = await recorder_mock.async_add_executor_job(_read, recorder_mock, entity_id)

    with patch.object(
        type(recorder_mock.statistics_meta_manager),
        "update_unit_of_measurement",
        side_effect=RuntimeError("simulated metadata failure"),
    ):
        async_migrate_price_statistics(hass, entry_id, key)
        await async_recorder_block_till_done(hass)

    assert (
        await recorder_mock.async_add_executor_job(_read, recorder_mock, entity_id)
        == before
    )
    async_migrate_price_statistics(hass, entry_id, key)
    await async_recorder_block_till_done(hass)
    after = await recorder_mock.async_add_executor_job(_read, recorder_mock, entity_id)
    assert after["metadata"]["unit_of_measurement"] == "ct/kWh"
    assert after["statistics"][0]["mean"] == -1.0


async def test_unregistered_price_and_missing_recorder_need_no_migration(hass) -> None:
    async_migrate_price_statistics(
        hass, "missing_entry", "economics_current_import_price"
    )
    recorder = MagicMock()
    hass.data[DATA_INSTANCE] = recorder
    async_migrate_price_statistics(
        hass, "missing_entry", "economics_current_import_price"
    )
    recorder.queue_task.assert_not_called()


async def test_registry_entity_from_a_different_entry_is_never_migrated(hass) -> None:
    key = "economics_current_import_price"
    entry_id, entity_id = _register(hass, key)
    other_entry = MockConfigEntry(domain=DOMAIN)
    other_entry.add_to_hass(hass)
    er.async_get(hass).async_update_entity(
        entity_id, config_entry_id=other_entry.entry_id
    )
    recorder = MagicMock()
    hass.data[DATA_INSTANCE] = recorder

    async_migrate_price_statistics(hass, entry_id, key)

    recorder.queue_task.assert_not_called()


async def test_price_sensor_addition_schedules_registered_statistic_migration(
    hass,
) -> None:
    key = "economics_current_import_price"
    entry_id, entity_id = _register(hass, key)
    recorder = MagicMock()
    hass.data[DATA_INSTANCE] = recorder
    description = next(item for item in SENSOR_DESCRIPTIONS if item.key == key)
    entity = SaxPowerSensor(MagicMock(), entry_id, description)
    entity.hass = hass

    with patch(
        "custom_components.sax_power.sensor.SaxPowerEntity.async_added_to_hass",
        new_callable=AsyncMock,
    ):
        await entity.async_added_to_hass()

    assert recorder.queue_task.call_args[0][0].statistic_id == entity_id
