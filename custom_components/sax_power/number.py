"""Number platform for SAX Power."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    MAX_POWER_LIMIT,
    MAX_SOC,
    MIN_POWER_LIMIT,
    MIN_SOC,
)
from .coordinator import SaxPowerCoordinator
from .entity import SaxPowerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        [
            SaxPowerMaxSocNumber(coordinator, entry.entry_id),
            SaxPowerChargeLimitNumber(coordinator, entry.entry_id),
        ]
    )


class SaxPowerMaxSocNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Software-seitiges Maximal-SOC für die Ladung.

    Der SAX Speicher besitzt kein natives Max-SOC-Register. Der Coordinator
    erzwingt den Zielwert stattdessen über den SunSpec-Modus (Register
    40051/40049), sowohl während des zeitgesteuerten Ladens als auch
    unabhängig davon - z. B. auch bei einem durch PV-Überschuss vollen
    Speicher (siehe coordinator.SaxPowerCoordinator._async_enforce_grid_charge).
    Dient zusätzlich als Ziel-SOC für das zeitgesteuerte Laden (keine eigene
    Einstellung dafür, siehe anforderung.yaml REQ-TIMED-SOC-CHARGE).

    Zustand wird über RestoreEntity über Neustarts hinweg persistiert. Gibt
    es (z. B. direkt nach der Ersteinrichtung) noch keinen gespeicherten
    Zustand, wird MAX_SOC (100 %) als Vorgabewert gesetzt statt "unbekannt"
    zu bleiben - andernfalls würde der Schieberegler optisch bei 0 stehen.
    """

    _attr_translation_key = "max_soc"
    _attr_native_min_value = MIN_SOC
    _attr_native_max_value = MAX_SOC
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_max_soc"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.max_soc is not None:
            return
        restored_value: int | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = int(float(last_state.state))
            except (TypeError, ValueError):
                restored_value = None
        await self.coordinator.async_set_max_soc(
            restored_value if restored_value is not None else MAX_SOC
        )

    @property
    def native_value(self) -> int | None:
        return self.coordinator.max_soc

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_max_soc(int(value))
        self.async_write_ha_state()


class SaxPowerChargeLimitNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Ziel-Leistung für die Netzladung ("Max. Netzladeleistung"), in Watt.

    Reiner Software-Zustand (kein direkter Register-Write mehr auf das
    Basic-Mode-Leistungsgrenzwert-Register 44) - wird vom Speicher nur
    berücksichtigt, während Register 40051 (Steuermodus) auf 1
    (Sollwertvorgabe) steht, siehe
    coordinator.SaxPowerCoordinator._async_enforce_grid_charge/
    ._async_sun_charge_loop.

    Zustand wird über RestoreEntity über Neustarts hinweg persistiert. Gibt
    es (z. B. direkt nach der Ersteinrichtung) noch keinen gespeicherten
    Zustand, wird der zu diesem Zeitpunkt vom Gerät gelesene Wert von
    Register 44 als einmaliger Vorgabewert übernommen.
    """

    _attr_translation_key = "charge_limit"
    _attr_native_min_value = MIN_POWER_LIMIT
    _attr_native_max_value = MAX_POWER_LIMIT
    _attr_native_step = 50
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_charge_limit"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.max_charge_power is not None:
            return
        restored_value: int | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = int(float(last_state.state))
            except (TypeError, ValueError):
                restored_value = None
        if restored_value is None and self.coordinator.data is not None:
            # Kein zuvor gespeicherter Zustand (allererster Start) - mit dem
            # aktuell vom Gerät gelesenen Register-44-Wert vorbelegen.
            restored_value = self.coordinator.data.get("charge_limit")
        await self.coordinator.async_set_max_charge_power(restored_value or 0)

    @property
    def native_value(self) -> int | None:
        return self.coordinator.max_charge_power

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_max_charge_power(int(value))
        self.async_write_ha_state()
