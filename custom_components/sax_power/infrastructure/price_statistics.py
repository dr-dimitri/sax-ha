"""Migrate tariff statistics from Euro to cents (REQ-VUE-TARIFF-EDITOR)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.recorder import Recorder
from homeassistant.components.recorder.db_schema import Statistics, StatisticsShortTerm
from homeassistant.components.recorder.tasks import RecorderTask
from homeassistant.components.recorder.util import session_scope
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.recorder import DATA_INSTANCE

from ..const import DOMAIN

PRICE_SENSOR_KEYS = frozenset(
    {
        "price_charge_current_price",
        "economics_current_import_price",
        "economics_feed_in_price",
    }
)


@dataclass(slots=True)
class _MigratePriceStatisticsTask(RecorderTask):
    """Use the Recorder thread so compilation cannot interleave with migration."""

    statistic_id: str

    def run(self, instance: Recorder) -> None:
        manager = instance.statistics_meta_manager
        with session_scope(session=instance.get_session()) as session:
            metadata = manager.get(session, self.statistic_id)
            if (
                metadata is None
                or metadata[1]["source"] != "recorder"
                or metadata[1]["unit_of_measurement"] != "EUR/kWh"
            ):
                return
            # HA has no tariff-price converter. Relabelling without scaling
            # would silently reinterpret the existing Euro history as cents.
            for table in (Statistics, StatisticsShortTerm):
                session.query(table).filter(table.metadata_id == metadata[0]).update(
                    {
                        table.mean: table.mean * 100,
                        table.min: table.min * 100,
                        table.max: table.max * 100,
                        table.state: table.state * 100,
                        table.sum: table.sum * 100,
                    },
                    synchronize_session=False,
                )
            # This also invalidates HA's metadata cache; values and unit commit
            # atomically. The old-unit guard makes restarts idempotent.
            manager.update_unit_of_measurement(
                session, self.statistic_id, None, "ct/kWh"
            )


@callback
def async_migrate_price_statistics(
    hass: HomeAssistant, entry_id: str, key: str
) -> None:
    """Migrate only the entry's registered tariff sensors, including renamed IDs."""
    if (
        key not in PRICE_SENSOR_KEYS
        or (instance := hass.data.get(DATA_INSTANCE)) is None
    ):
        return
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry_id}_{key}")
    if (
        entity_id is not None
        and (registered := registry.async_get(entity_id)) is not None
        and registered.config_entry_id == entry_id
    ):
        instance.queue_task(_MigratePriceStatisticsTask(entity_id))
