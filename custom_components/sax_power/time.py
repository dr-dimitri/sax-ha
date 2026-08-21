"""Time platform for SAX Power.

Start-/Endzeiten der drei Software-Zeitfenster (kein Register):
zeitgesteuertes Laden, netzdienliches Laden und Entladesperre. Siehe
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
    DEFAULT_DISCHARGE_BLOCK_END,
    DEFAULT_DISCHARGE_BLOCK_START,
    DEFAULT_GRID_SERVING_END,
    DEFAULT_GRID_SERVING_START,
    DEFAULT_TIMED_CHARGE_END,
    DEFAULT_TIMED_CHARGE_START,
    DOMAIN,
)
from .coordinator import SaxPowerCoordinator
from .entity import SaxPowerEntity, initial_config_value


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
            SaxPowerDischargeBlockStartTime(coordinator, entry.entry_id),
            SaxPowerDischargeBlockEndTime(coordinator, entry.entry_id),
        ]
    )


class SaxPowerTimedChargeStartTime(RestoreEntity, SaxPowerEntity, TimeEntity):
    """Beginn des Zeitfensters für das zeitgesteuerte Laden."""

    _attr_translation_key = "timed_charge_start"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_timed_charge_start"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.timed_charge_start is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := dt_util.parse_time(last_state.state)) is not None:
                await self.coordinator.async_set_timed_charge_start(value)
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


class SaxPowerTimedChargeEndTime(RestoreEntity, SaxPowerEntity, TimeEntity):
    """Ende des Zeitfensters für das zeitgesteuerte Laden."""

    _attr_translation_key = "timed_charge_end"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_timed_charge_end"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.timed_charge_end is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := dt_util.parse_time(last_state.state)) is not None:
                await self.coordinator.async_set_timed_charge_end(value)
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


class SaxPowerGridServingStartTime(RestoreEntity, SaxPowerEntity, TimeEntity):
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
        self._attr_unique_id = f"{entry_id}_grid_serving_start"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.grid_serving_start is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := dt_util.parse_time(last_state.state)) is not None:
                await self.coordinator.async_set_grid_serving_start(value)
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


class SaxPowerGridServingEndTime(RestoreEntity, SaxPowerEntity, TimeEntity):
    """Ende des Zeitfensters für das netzdienliche Laden.

    Siehe SaxPowerGridServingStartTime zur Nicht-Überlappungs-Prüfung.
    """

    _attr_translation_key = "grid_serving_end"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_grid_serving_end"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.grid_serving_end is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := dt_util.parse_time(last_state.state)) is not None:
                await self.coordinator.async_set_grid_serving_end(value)
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


class SaxPowerDischargeBlockStartTime(RestoreEntity, SaxPowerEntity, TimeEntity):
    """Beginn des Sperrfensters der Entladesperre (Modus "window").

    Anders als die beiden Ladefenster unterliegt dieses Fenster keiner
    Nichtüberlappungs-Prüfung: die Entladesperre steht als unterste Stufe
    der Vorrangkette hinter allen drei Lade-Automatiken und kann ihnen
    deshalb nicht in die Quere kommen (siehe anforderung.yaml,
    REQ-DISCHARGE-BLOCK).
    """

    _attr_translation_key = "discharge_block_start"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_discharge_block_start"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.discharge_block_start is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := dt_util.parse_time(last_state.state)) is not None:
                await self.coordinator.async_set_discharge_block_start(value)
                return
        value = dt_util.parse_time(DEFAULT_DISCHARGE_BLOCK_START)
        if value is not None:
            await self.coordinator.async_set_discharge_block_start(value)

    @property
    def native_value(self) -> dt_time | None:
        return self.coordinator.discharge_block_start

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_set_discharge_block_start(value)
        self.async_write_ha_state()


class SaxPowerDischargeBlockEndTime(RestoreEntity, SaxPowerEntity, TimeEntity):
    """Ende des Sperrfensters der Entladesperre (Modus "window") - siehe
    SaxPowerDischargeBlockStartTime."""

    _attr_translation_key = "discharge_block_end"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_discharge_block_end"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.discharge_block_end is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (value := dt_util.parse_time(last_state.state)) is not None:
                await self.coordinator.async_set_discharge_block_end(value)
                return
        value = dt_util.parse_time(DEFAULT_DISCHARGE_BLOCK_END)
        if value is not None:
            await self.coordinator.async_set_discharge_block_end(value)

    @property
    def native_value(self) -> dt_time | None:
        return self.coordinator.discharge_block_end

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_set_discharge_block_end(value)
        self.async_write_ha_state()
