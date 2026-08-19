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
    DEFAULT_DISCHARGE_POWER,
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
            SaxPowerDischargePowerNumber(coordinator, entry.entry_id),
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

    Ein restaurierter Wert von genau 0 W wird dabei wie "kein gespeicherter
    Zustand" behandelt (fällt also ebenfalls auf den Register-44-Wert
    zurück): 0 W ist als bewusste Nutzereinstellung für diese Größe
    sinnlos (Netzladung wäre dann wirkungslos) und tritt in der Praxis nur
    auf, wenn RestoreEntity einen alten, vor Einführung dieser Vorbelegung
    gespeicherten Zustand findet (z. B. nach einem Update der Integration
    auf einem bestehenden Config Entry) - ohne diesen Fallback würde die
    Entity dauerhaft bei 0 W hängen bleiben, statt den tatsächlichen
    Geräte-Registerwert zu übernehmen.
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
        if not restored_value and self.coordinator.data is not None:
            # Kein (sinnvoller) zuvor gespeicherter Zustand (allererster
            # Start, oder ein restaurierter 0-Wert, siehe Klassen-Docstring)
            # - mit dem aktuell vom Gerät gelesenen Register-44-Wert
            # vorbelegen.
            restored_value = self.coordinator.data.get("charge_limit")
        await self.coordinator.async_set_max_charge_power(restored_value or 0)

    @property
    def native_value(self) -> int | None:
        return self.coordinator.max_charge_power

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_max_charge_power(int(value))
        self.async_write_ha_state()


class SaxPowerDischargePowerNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Sollwert-Leistung für die "Manuelle Entladung" (switch.py), in Watt.

    Reiner Software-Zustand, analog zu SaxPowerChargeLimitNumber - wird vom
    Speicher nur berücksichtigt, während die "Manuelle Entladung"
    eingeschaltet ist (siehe
    coordinator.SaxPowerCoordinator._async_enforce_grid_charge). Anders als
    "Max. Netzladeleistung" gibt es hierfür kein analoges Basic-Mode-
    Register, das als Vorgabewert dienen könnte - daher ein fester
    Hard-Default (DEFAULT_DISCHARGE_POWER, 100 W), analog zu "Max. SOC".

    Zustand wird über RestoreEntity über Neustarts hinweg persistiert.
    """

    _attr_translation_key = "discharge_power_setpoint"
    _attr_native_min_value = MIN_POWER_LIMIT
    _attr_native_max_value = MAX_POWER_LIMIT
    _attr_native_step = 50
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_discharge_power_setpoint"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.discharge_power is not None:
            return
        restored_value: int | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = int(float(last_state.state))
            except (TypeError, ValueError):
                restored_value = None
        await self.coordinator.async_set_discharge_power(
            restored_value if restored_value is not None else DEFAULT_DISCHARGE_POWER
        )

    @property
    def native_value(self) -> int | None:
        return self.coordinator.discharge_power

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_discharge_power(int(value))
        self.async_write_ha_state()
