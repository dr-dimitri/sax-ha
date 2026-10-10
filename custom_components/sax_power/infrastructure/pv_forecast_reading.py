"""Refresh the displayed PV source without changing charging eligibility."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import partial
from typing import Literal

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.util import dt as dt_util

from ..domain.forecast import normalize_energy_kwh

UPDATE_INTERVAL = timedelta(minutes=10)
RETRY_INTERVAL = timedelta(seconds=30)
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
        self._read_failed = False
        self._unsubscribe: Callable[[], None] | None = None
        self._unsubscribe_source: Callable[[], None] | None = None
        self._refreshing_revision: int | None = None
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
        if self._unsubscribe_source is not None and source == self.source_entity_id:
            return
        self._stop()
        self.source_entity_id = source
        self.value_kwh = None
        self.last_successful_update = None
        self._read_failed = False
        if source is not None:
            self._read(source)
            self._unsubscribe_source = async_track_state_change_event(
                self._hass,
                source,
                partial(self._source_changed, source, self._revision),
            )
            self._schedule_refresh()
        self._notify()

    @property
    def status(self) -> Literal["waiting", "available", "error"]:
        """Keep a valid cached yield visible during transient read failures."""
        if self.value_kwh is not None:
            return "available"
        return "error" if self._read_failed else "waiting"

    def _read(self, source: str) -> None:
        state = self._hass.states.get(source)
        if state is None or state.state == STATE_UNKNOWN:
            self._read_failed = False
            return
        value = normalize_energy_kwh(
            state.state, state.attributes.get("unit_of_measurement")
        )
        if value is None or value < 0:
            self._read_failed = True
            return
        self._read_failed = False
        self.value_kwh = value
        self.last_successful_update = dt_util.utcnow()

    @callback
    def _source_changed(
        self, source: str, revision: int, event: Event[EventStateChangedData]
    ) -> None:
        if not self._is_current(source, revision):
            return
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        # REQ-VUE-ELECTRICITY-TARIFF: metadata-only changes must not feed
        # notifications back through sources derived from SAX entities.
        if (
            old_state is not None
            and new_state is not None
            and old_state.state == new_state.state
            and old_state.attributes.get("unit_of_measurement")
            == new_state.attributes.get("unit_of_measurement")
        ):
            return
        was_missing = self.value_kwh is None
        self._read(source)
        self._notify()
        if was_missing and self.value_kwh is not None:
            self._schedule_next_refresh()

    def _is_current(self, source: str, revision: int) -> bool:
        return (
            not self._shutdown
            and revision == self._revision
            and source == self._source()
        )

    @callback
    def _cancel_timer(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    @callback
    def _schedule_next_refresh(self) -> None:
        self._cancel_timer()
        source = self.source_entity_id
        if (
            source is None
            or not self._is_current(source, self._revision)
            or self._refreshing_revision == self._revision
        ):
            return
        interval = RETRY_INTERVAL if self.value_kwh is None else UPDATE_INTERVAL
        self._unsubscribe = async_call_later(
            self._hass,
            interval,
            partial(self._async_interval, source, self._revision),
        )

    @callback
    def _async_interval(self, source: str, revision: int, _now: datetime) -> None:
        if not self._is_current(source, revision):
            return
        self._cancel_timer()
        self._schedule_refresh()

    @callback
    def _schedule_refresh(self) -> None:
        if (
            self._shutdown
            or self.source_entity_id is None
            or self._refreshing_revision == self._revision
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
        if (
            source is None
            or not self._is_current(source, revision)
            or self._refreshing_revision == revision
        ):
            return
        self._refreshing_revision = revision
        self._cancel_timer()
        try:
            async with asyncio.timeout(UPDATE_TIMEOUT):
                await async_update_entity(self._hass, source)
        except HomeAssistantError, TimeoutError, OSError, ValueError:
            if self._is_current(source, revision):
                self._read_failed = True
        else:
            if self._is_current(source, revision):
                self._read(source)
        finally:
            if self._refreshing_revision == revision:
                self._refreshing_revision = None
        # REQ-VUE-ELECTRICITY-TARIFF: A late response belongs to its old source.
        if not self._is_current(source, revision):
            return
        self._notify()
        self._schedule_next_refresh()

    @callback
    def _stop(self) -> None:
        self._revision += 1
        self._cancel_timer()
        if self._unsubscribe_source is not None:
            self._unsubscribe_source()
            self._unsubscribe_source = None
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
