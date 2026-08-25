"""Time platform for SAX Power.

Start-/Endzeiten der beiden Software-Zeitfenster (kein Register):
zeitgesteuertes Laden und netzdienliches Laden. Siehe
coordinator.SaxPowerCoordinator._async_enforce_grid_charge.
"""

from __future__ import annotations

from datetime import time as dt_time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_TIMED_CHARGE_END,
    CONF_TIMED_CHARGE_START,
    DATA_COORDINATOR,
    DEFAULT_GRID_SERVING_END,
    DEFAULT_GRID_SERVING_START,
    DEFAULT_TIMED_CHARGE_END,
    DEFAULT_TIMED_CHARGE_START,
    DOMAIN,
)
from .coordinator import SaxPowerCoordinator
from .entity import (
    SaxPowerConfigEntity,
    initial_config_value,
    log_unmigratable_state,
    restorable_time,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        [
            SaxPowerTimedChargeStartTime(coordinator, entry.entry_id),
            SaxPowerTimedChargeEndTime(coordinator, entry.entry_id),
            SaxPowerGridServingStartTime(coordinator, entry.entry_id),
            SaxPowerGridServingEndTime(coordinator, entry.entry_id),
        ]
    )


class SaxPowerTimedChargeStartTime(RestoreEntity, SaxPowerConfigEntity, TimeEntity):
    """Beginn des Zeitfensters für das zeitgesteuerte Laden."""

    _attr_translation_key = "timed_charge_start"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("time", "timed_charge_start")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if not self.coordinator.control_config_migration_pending:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Es gibt bereits einen Store -
            # entweder hat er den Wert gesetzt, oder er war nicht lesbar und
            # es gelten sichere Defaults. In beiden Fällen darf ein
            # veralteter Entity-Zustand nicht einspringen; der
            # RestoreEntity-Pfad unten ist nur der einmalige Migrationsweg
            # für Einträge ganz ohne Store.
            return
        if self.coordinator.timed_charge_start is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := restorable_time(last_state)) is not None:
                await self.coordinator.async_set_timed_charge_start(value)
            else:
                log_unmigratable_state(self.entity_id, last_state)
            return
        # Kein zuvor gespeicherter Zustand (allererster Start eines neu
        # eingerichteten Eintrags) - Vorgabewert aus der Ersteinrichtung
        # nutzen, sonst den Hard-Default (siehe const.py).
        initial = initial_config_value(
            self.hass, self._entry_id, CONF_TIMED_CHARGE_START
        )
        value = dt_util.parse_time(initial or DEFAULT_TIMED_CHARGE_START)
        if value is not None:
            await self.coordinator.async_set_timed_charge_start(value)

    @property
    def native_value(self) -> dt_time | None:
        return self.coordinator.timed_charge_start

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_set_timed_charge_start(value)
        self.async_write_ha_state()


class SaxPowerTimedChargeEndTime(RestoreEntity, SaxPowerConfigEntity, TimeEntity):
    """Ende des Zeitfensters für das zeitgesteuerte Laden."""

    _attr_translation_key = "timed_charge_end"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("time", "timed_charge_end")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if not self.coordinator.control_config_migration_pending:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Es gibt bereits einen Store -
            # entweder hat er den Wert gesetzt, oder er war nicht lesbar und
            # es gelten sichere Defaults. In beiden Fällen darf ein
            # veralteter Entity-Zustand nicht einspringen; der
            # RestoreEntity-Pfad unten ist nur der einmalige Migrationsweg
            # für Einträge ganz ohne Store.
            return
        if self.coordinator.timed_charge_end is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := restorable_time(last_state)) is not None:
                await self.coordinator.async_set_timed_charge_end(value)
            else:
                log_unmigratable_state(self.entity_id, last_state)
            return
        initial = initial_config_value(self.hass, self._entry_id, CONF_TIMED_CHARGE_END)
        value = dt_util.parse_time(initial or DEFAULT_TIMED_CHARGE_END)
        if value is not None:
            await self.coordinator.async_set_timed_charge_end(value)

    @property
    def native_value(self) -> dt_time | None:
        return self.coordinator.timed_charge_end

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_set_timed_charge_end(value)
        self.async_write_ha_state()


class SaxPowerGridServingStartTime(RestoreEntity, SaxPowerConfigEntity, TimeEntity):
    """Beginn des Zeitfensters für das netzdienliche Laden.

    Darf sich nicht mit dem Zeitfenster des zeitgesteuerten Ladens
    überschneiden (Tageszeit UND aktive Monate) - ein Wert, der zu einer
    echten Überschneidung führen würde, wird von
    SaxPowerCoordinator.async_set_grid_serving_start NICHT abgelehnt,
    sondern über eine Persistent Notification gemeldet und anschließend
    geleert (siehe anforderung.yaml, REQ-GRID-SERVING-CHARGE,
    SaxPowerCoordinator._notify_time_window_overlap).
    """

    _attr_translation_key = "grid_serving_start"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("time", "grid_serving_start")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if not self.coordinator.control_config_migration_pending:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Es gibt bereits einen Store -
            # entweder hat er den Wert gesetzt, oder er war nicht lesbar und
            # es gelten sichere Defaults. In beiden Fällen darf ein
            # veralteter Entity-Zustand nicht einspringen; der
            # RestoreEntity-Pfad unten ist nur der einmalige Migrationsweg
            # für Einträge ganz ohne Store.
            return
        if self.coordinator.grid_serving_start is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := restorable_time(last_state)) is not None:
                await self.coordinator.async_set_grid_serving_start(value)
            else:
                log_unmigratable_state(self.entity_id, last_state)
            return
        value = dt_util.parse_time(DEFAULT_GRID_SERVING_START)
        if value is not None:
            await self.coordinator.async_set_grid_serving_start(value)

    @property
    def native_value(self) -> dt_time | None:
        return self.coordinator.grid_serving_start

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_set_grid_serving_start(value)
        self.async_write_ha_state()


class SaxPowerGridServingEndTime(RestoreEntity, SaxPowerConfigEntity, TimeEntity):
    """Ende des Zeitfensters für das netzdienliche Laden.

    Siehe SaxPowerGridServingStartTime zur Nicht-Überlappungs-Prüfung.
    """

    _attr_translation_key = "grid_serving_end"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("time", "grid_serving_end")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if not self.coordinator.control_config_migration_pending:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Es gibt bereits einen Store -
            # entweder hat er den Wert gesetzt, oder er war nicht lesbar und
            # es gelten sichere Defaults. In beiden Fällen darf ein
            # veralteter Entity-Zustand nicht einspringen; der
            # RestoreEntity-Pfad unten ist nur der einmalige Migrationsweg
            # für Einträge ganz ohne Store.
            return
        if self.coordinator.grid_serving_end is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := restorable_time(last_state)) is not None:
                await self.coordinator.async_set_grid_serving_end(value)
            else:
                log_unmigratable_state(self.entity_id, last_state)
            return
        value = dt_util.parse_time(DEFAULT_GRID_SERVING_END)
        if value is not None:
            await self.coordinator.async_set_grid_serving_end(value)

    @property
    def native_value(self) -> dt_time | None:
        return self.coordinator.grid_serving_end

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_set_grid_serving_end(value)
        self.async_write_ha_state()
