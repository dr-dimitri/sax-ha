"""Switch platform for SAX Power."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ALL_MONTHS,
    CONF_TIMED_CHARGE_ENABLED,
    DATA_COORDINATOR,
    DEFAULT_GRID_SERVING_ENABLED,
    DEFAULT_TIMED_CHARGE_ENABLED,
    DOMAIN,
    REG_SWITCH_STATE,
    SWITCH_STATE_CONNECTED,
    SWITCH_STATE_OFF,
    SWITCH_STATE_ON,
)
from .coordinator import SaxPowerCoordinator
from .entity import SaxPowerEntity, initial_config_value


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    entities: list[SwitchEntity] = [
        SaxPowerStorageSwitch(coordinator, entry.entry_id),
        SaxPowerTimedChargeSwitch(coordinator, entry.entry_id),
        SaxPowerGridServingSwitch(coordinator, entry.entry_id),
    ]
    entities.extend(
        SaxPowerMonthSwitch(
            coordinator,
            entry.entry_id,
            month=month,
            translation_key=f"timed_charge_month_{month}",
            is_month_active=lambda m: m in coordinator.timed_charge_months,
            async_set_month_active=coordinator.async_set_timed_charge_month,
        )
        for month in ALL_MONTHS
    )
    entities.extend(
        SaxPowerMonthSwitch(
            coordinator,
            entry.entry_id,
            month=month,
            translation_key=f"grid_serving_month_{month}",
            is_month_active=lambda m: m in coordinator.grid_serving_months,
            async_set_month_active=coordinator.async_set_grid_serving_month,
        )
        for month in ALL_MONTHS
    )
    async_add_entities(entities)


class SaxPowerStorageSwitch(SaxPowerEntity, SwitchEntity):
    """Ein-/Ausschalten des Speichers (Register 45)."""

    _attr_translation_key = "storage"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_storage_switch"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data["switch_state"] in (
            SWITCH_STATE_ON,
            SWITCH_STATE_CONNECTED,
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_register(REG_SWITCH_STATE, SWITCH_STATE_ON)
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_register(REG_SWITCH_STATE, SWITCH_STATE_OFF)
        await self.coordinator.async_refresh()


class SaxPowerTimedChargeSwitch(RestoreEntity, SaxPowerEntity, SwitchEntity):
    """Aktiviert/deaktiviert das zeitgesteuerte Laden (Software-Logik).

    Siehe SaxPowerCoordinator._async_enforce_timed_charge sowie die
    zugehörigen Number-/Time-Entities (Ziel-SOC, Zeitfenster, Ladeleistung).
    """

    _attr_translation_key = "timed_charge_enabled"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_timed_charge_enabled"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.timed_charge_enabled:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            await self.coordinator.async_set_timed_charge_enabled(
                last_state.state == "on"
            )
            return
        # Kein zuvor gespeicherter Zustand (allererster Start eines neu
        # eingerichteten Eintrags) - Vorgabewert aus der Ersteinrichtung
        # nutzen, sonst den Hard-Default (siehe const.py).
        initial = initial_config_value(
            self.hass, self._entry_id, CONF_TIMED_CHARGE_ENABLED
        )
        await self.coordinator.async_set_timed_charge_enabled(
            bool(initial) if initial is not None else DEFAULT_TIMED_CHARGE_ENABLED
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.timed_charge_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_timed_charge_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_timed_charge_enabled(False)
        self.async_write_ha_state()


class SaxPowerGridServingSwitch(RestoreEntity, SaxPowerEntity, SwitchEntity):
    """Aktiviert/deaktiviert das netzdienliche Laden (Software-Logik).

    Lädt - anders als "Netzladung aktiv" - ausschließlich mit PV-Überschuss,
    nie aus dem Netz, in einem eigenen, zur Netzladung nicht überlappenden
    Zeitfenster. Siehe SaxPowerCoordinator._async_enforce_grid_charge sowie
    die zugehörigen Time-Entities (time.py) und anforderung.yaml,
    REQ-GRID-SERVING-CHARGE.
    """

    _attr_translation_key = "grid_serving_enabled"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_grid_serving_enabled"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.grid_serving_enabled:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            await self.coordinator.async_set_grid_serving_enabled(
                last_state.state == "on"
            )
            return
        await self.coordinator.async_set_grid_serving_enabled(
            DEFAULT_GRID_SERVING_ENABLED
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.grid_serving_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_grid_serving_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_grid_serving_enabled(False)
        self.async_write_ha_state()


class SaxPowerMonthSwitch(RestoreEntity, SaxPowerEntity, SwitchEntity):
    """Legt fest, ob Netzladung bzw. netzdienliches Laden in einem
    bestimmten Kalendermonat überhaupt wirksam sein darf (siehe
    anforderung.yaml, REQ-GRID-SERVING-CHARGE) - z. B. Netzladung nur
    November-Januar, netzdienliches Laden nur Mai-August. Generische Klasse
    für beide Features und alle 12 Monate; welches Feature betroffen ist,
    steuern die im Konstruktor übergebenen Callables
    (SaxPowerCoordinator.timed_charge_months/async_set_timed_charge_month
    bzw. .grid_serving_months/async_set_grid_serving_month).

    Default (kein zuvor gespeicherter Zustand): aktiv - der Coordinator
    initialisiert beide Monats-Sets bereits mit allen 12 Monaten, sodass
    sich bestehende Konfigurationen nach einem Update unverändert verhalten,
    bis der Anwender einzelne Monate bewusst abwählt.
    """

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SaxPowerCoordinator,
        entry_id: str,
        *,
        month: int,
        translation_key: str,
        is_month_active: Callable[[int], bool],
        async_set_month_active: Callable[[int, bool, bool], Awaitable[None]],
    ) -> None:
        super().__init__(coordinator, entry_id)
        self._month = month
        self._is_month_active = is_month_active
        self._async_set_month_active = async_set_month_active
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry_id}_{translation_key}"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            # validate=False: siehe SaxPowerCoordinator.async_set_timed_charge_month
            # - vermeidet fälschliche Überlappungsfehler während des
            # sequentiellen Restaurierens mehrerer Monats-Entities.
            await self._async_set_month_active(
                self._month, last_state.state == "on", False
            )

    @property
    def is_on(self) -> bool:
        return self._is_month_active(self._month)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_month_active(self._month, True, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_month_active(self._month, False, True)
        self.async_write_ha_state()
