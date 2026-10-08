"""Refresh the displayed PV source without changing charging eligibility."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from ..domain.forecast import normalize_energy_kwh

UPDATE_INTERVAL = timedelta(minutes=10)
UPDATE_TIMEOUT = 30


class PvForecastReading:
    """Keep the source's last valid value (REQ-VUE-ELECTRICITY-TARIFF)."""

    def __init__(
        self,
        hass: HomeAssistant,
        source: Callable[[], str | None],
        notify: Callable[[], None],
    ) -> None:
        self._hass = hass
        self._source = source
        self._notify = notify
        self.source_entity_id: str | None = None
        self.value_kwh: float | None = None
        self.last_successful_update: datetime | None = None
        self._unsubscribe: Callable[[], None] | None = None
        self._task: asyncio.Task[None] | None = None
        self._tasks: set[asyncio.Task[None]] = set()
        self._revision = 0
        self._shutdown = False

    @callback
    def async_setup(self) -> None:
        """Accept a source change immediately; refresh it outside device locks."""
        if self._shutdown:
            return
        source = self._source()
        if self._unsubscribe is not None and source == self.source_entity_id:
            return
        self._stop()
        self.source_entity_id = source
        self.value_kwh = None
        self.last_successful_update = None
        if source is not None:
            self._read(source)
            self._unsubscribe = async_track_time_interval(
                self._hass, self._async_interval, UPDATE_INTERVAL
            )
            self._schedule_refresh()
        self._notify()

    def _read(self, source: str) -> None:
        state = self._hass.states.get(source)
        if state is None:
            return
        value = normalize_energy_kwh(
            state.state, state.attributes.get("unit_of_measurement")
        )
        if value is None or value < 0:
            return
        self.value_kwh = value
        self.last_successful_update = dt_util.utcnow()

    @callback
    def _async_interval(self, _now: datetime) -> None:
        self._schedule_refresh()

    @callback
    def _schedule_refresh(self) -> None:
        if (
            self._shutdown
            or self.source_entity_id is None
            or (self._task is not None and not self._task.done())
        ):
            return
        self._task = self._hass.async_create_background_task(
            self.async_refresh(), "sax_power PV forecast reading", eager_start=False
        )
        self._tasks.add(self._task)
        self._task.add_done_callback(self._tasks.discard)

    async def async_refresh(self) -> None:
        """Force a HA source refresh, preserving the cache on any read failure."""
        source = self.source_entity_id
        revision = self._revision
        if source is None or self._shutdown:
            return
        try:
            async with asyncio.timeout(UPDATE_TIMEOUT):
                await async_update_entity(self._hass, source)
        except HomeAssistantError, TimeoutError, OSError, ValueError:
            return
        # REQ-VUE-ELECTRICITY-TARIFF: A late response belongs to its old source.
        if revision != self._revision or source != self._source():
            return
        self._read(source)
        self._notify()

    @callback
    def _stop(self) -> None:
        self._revision += 1
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()

    async def async_shutdown(self) -> None:
        """Stop polling and await any pending source request before unloading."""
        self._shutdown = True
        self._stop()
        tasks = tuple(self._tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
