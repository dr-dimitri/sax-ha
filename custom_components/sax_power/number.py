"""Number platform for SAX Power."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    EntityCategory,
    UnitOfEnergy,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BRIDGE_CHARGE_MIN_ENERGY_STEP_KWH,
    CONF_BRIDGE_CHARGE_MIN_ENERGY_KWH,
    DATA_COORDINATOR,
    DEFAULT_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    DEFAULT_PRICE_HOURS,
    DEFAULT_PRICE_LIMIT,
    DEFAULT_PRICE_NEUTRAL,
    DEFAULT_TIMED_CHARGE_MIN_SOC,
    DOMAIN,
    GRID_SERVING_FORECAST_THRESHOLD_STEP_KWH,
    MAX_BRIDGE_CHARGE_MIN_ENERGY_KWH,
    MAX_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    MAX_PRICE_HOURS,
    MAX_PRICE_LIMIT,
    MAX_SOC,
    MIN_BRIDGE_CHARGE_MIN_ENERGY_KWH,
    MIN_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    MIN_PRICE_HOURS,
    MIN_PRICE_LIMIT,
    MIN_SOC,
    PRICE_LIMIT_STEP,
)
from .coordinator import SaxPowerCoordinator
from .entity import (
    SaxPowerConfigEntity,
    SaxPowerRestoreConfigEntity,
    log_unmigratable_state,
    restorable_number,
)


def _restorable_price_eur_kwh(last_state: State) -> float | None:
    """REQ-DYNAMIC-PRICE-CHARGE: Altzustände waren Euro, neue Zustände Cent."""
    value = restorable_number(last_state)
    if value is None:
        return None
    unit = last_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
    if unit == "ct/kWh":
        return value / 100
    if unit in (None, "EUR/kWh"):
        return value
    return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        [
            SaxPowerMaxSocNumber(coordinator, entry.entry_id),
            SaxPowerTimedChargeMaxSocNumber(coordinator, entry.entry_id),
            SaxPowerTimedChargeMinSocNumber(coordinator, entry.entry_id),
            SaxPowerBridgeChargeMinEnergyNumber(coordinator, entry.entry_id),
            SaxPowerGridServingForecastThresholdNumber(coordinator, entry.entry_id),
            SaxPowerPriceLimitNumber(coordinator, entry.entry_id),
            SaxPowerPriceNeutralPriceNumber(coordinator, entry.entry_id),
            SaxPowerPriceChargeHoursNumber(coordinator, entry.entry_id),
        ]
    )


class SaxPowerMaxSocNumber(SaxPowerRestoreConfigEntity, NumberEntity):
    """Software-seitiges Maximal-SOC für die Ladung.

    Der SAX Speicher besitzt kein natives Max-SOC-Register. Der Coordinator
    erzwingt den Zielwert stattdessen über den SunSpec-Modus (Register
    40051/40049), sowohl während des zeitgesteuerten Ladens als auch
    unabhängig davon - z. B. auch bei einem durch PV-Überschuss vollen
    Speicher (siehe coordinator.SaxPowerCoordinator._async_enforce_grid_charge).
    Begrenzt zusätzlich den eigenen Zielwert des zeitgesteuerten Ladens
    und dient als Ziel-SOC für das preisoptimierte Laden, siehe
    anforderung.yaml REQ-TIMED-SOC-CHARGE und REQ-DYNAMIC-PRICE-CHARGE.

    Der Wert liegt im Konfigurations-Store des Coordinators (siehe
    anforderung.yaml, REQ-CONTROL-CONFIG-BOOTSTRAP) und ist dort bereits
    gesetzt, bevor diese Entity überhaupt existiert. Der RestoreEntity-Pfad
    unten greift nur noch für Einträge ohne Store (einmalige Migration);
    ohne beides gilt MAX_SOC (100 %) statt "unbekannt" - andernfalls würde
    der Schieberegler optisch bei 0 stehen.
    """

    _attr_translation_key = "max_soc"
    _attr_native_min_value = MIN_SOC
    _attr_native_max_value = MAX_SOC
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("number", "max_soc")

    async def _async_restore_control_value(self) -> None:
        if self.coordinator.max_soc is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (restored := restorable_number(last_state)) is not None:
                await self.coordinator.async_set_max_soc(int(restored))
            else:
                log_unmigratable_state(self.entity_id, last_state)
                self.coordinator.mark_control_field_unresolved("max_soc")
            return
        await self.coordinator.async_set_max_soc(MAX_SOC)

    @property
    def native_value(self) -> int | None:
        return self.coordinator.max_soc

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_max_soc(int(value), defer_device_update=True)
        self.async_write_ha_state()


class SaxPowerTimedChargeMaxSocNumber(SaxPowerConfigEntity, NumberEntity):
    """Ziel-SOC der Netzladung unterhalb der geräteweiten Max-SOC-Grenze.

    Initialisierung und Persistenz übernimmt ausschließlich der zentrale
    Konfigurations-Store, damit beim Upgrade der wiederhergestellte
    Max-SOC unabhängig von der Entity-Startreihenfolge übernommen wird
    (REQ-TIMED-SOC-CHARGE, REQ-CONTROL-CONFIG-BOOTSTRAP).
    """

    _attr_translation_key = "timed_charge_max_soc"
    _attr_native_min_value = MIN_SOC
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("number", "timed_charge_max_soc")

    @property
    def native_max_value(self) -> int:
        return (
            self.coordinator.max_soc
            if self.coordinator.max_soc is not None
            else MAX_SOC
        )

    @property
    def native_value(self) -> int:
        return self.coordinator.timed_charge_max_soc

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_timed_charge_max_soc(
            int(value), defer_device_update=True
        )
        self.async_write_ha_state()


class SaxPowerTimedChargeMinSocNumber(SaxPowerRestoreConfigEntity, NumberEntity):
    """Unterer SOC-Schwellwert ("Min. SOC"), unterhalb dessen die Netzladung
    starten darf (bei 0 % genau bei 0 % SOC) - siehe anforderung.yaml,
    REQ-TIMED-SOC-CHARGE und
    coordinator.SaxPowerCoordinator._async_enforce_grid_charge
    (_timed_charge_armed) für die Hysterese-Logik: im selben Fenster einmal
    unterschritten, lädt die Netzladung darin bis "Netzladen Max. SOC" durch,
    statt bei jedem erneuten
    Überschreiten von "Min. SOC" sofort wieder abzubrechen.

    Persistiert im Konfigurations-Store (REQ-CONTROL-CONFIG-BOOTSTRAP),
    RestoreEntity nur noch als einmaliger Migrationspfad. Ohne beides gilt
    DEFAULT_TIMED_CHARGE_MIN_SOC (20 %) statt "unbekannt"/0 - ein bereits
    sinnvoll nutzbarer Schwellwert statt eines faktisch inaktiven
    100-%-Defaults, mit dem Netzladung bei der Ersteinrichtung nie von
    selbst armt.
    """

    _attr_translation_key = "timed_charge_min_soc"
    _attr_native_min_value = MIN_SOC
    _attr_native_max_value = MAX_SOC
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("number", "timed_charge_min_soc")

    async def _async_restore_control_value(self) -> None:
        if self.coordinator.timed_charge_min_soc is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (restored := restorable_number(last_state)) is not None:
                await self.coordinator.async_set_timed_charge_min_soc(int(restored))
            else:
                log_unmigratable_state(self.entity_id, last_state)
                self.coordinator.mark_control_field_unresolved("timed_charge_min_soc")
            return
        await self.coordinator.async_set_timed_charge_min_soc(
            DEFAULT_TIMED_CHARGE_MIN_SOC
        )

    @property
    def native_value(self) -> int | None:
        return self.coordinator.timed_charge_min_soc

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_timed_charge_min_soc(
            int(value), defer_device_update=True
        )
        self.async_write_ha_state()


class SaxPowerBridgeChargeMinEnergyNumber(SaxPowerConfigEntity, NumberEntity):
    """Share the minimum stored energy per bridge charge with the options flow."""

    _attr_translation_key = CONF_BRIDGE_CHARGE_MIN_ENERGY_KWH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = MIN_BRIDGE_CHARGE_MIN_ENERGY_KWH
    _attr_native_max_value = MAX_BRIDGE_CHARGE_MIN_ENERGY_KWH
    _attr_native_step = BRIDGE_CHARGE_MIN_ENERGY_STEP_KWH
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("number", CONF_BRIDGE_CHARGE_MIN_ENERGY_KWH)

    @property
    def native_value(self) -> float:
        return self.coordinator.bridge_charge_min_energy_kwh

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_bridge_charge_min_energy_kwh(value)
        self.async_write_ha_state()


class SaxPowerGridServingForecastThresholdNumber(
    SaxPowerRestoreConfigEntity, NumberEntity
):
    """Optional minimum PV forecast for grid-serving charge pauses.

    Zero disables the forecast condition and preserves the static schedule.
    Restore values are validated again by the Coordinator because restoring
    bypasses the normal NumberEntity service validation.
    """

    _attr_translation_key = "grid_serving_forecast_threshold"
    _attr_native_min_value = MIN_GRID_SERVING_FORECAST_THRESHOLD_KWH
    _attr_native_max_value = MAX_GRID_SERVING_FORECAST_THRESHOLD_KWH
    _attr_native_step = GRID_SERVING_FORECAST_THRESHOLD_STEP_KWH
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("number", "grid_serving_forecast_threshold")

    async def _async_restore_control_value(self) -> None:
        if self.coordinator.grid_serving_forecast_threshold_kwh_raw is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (restored := restorable_number(last_state)) is not None:
                await self.coordinator.async_set_grid_serving_forecast_threshold_kwh(
                    restored
                )
            else:
                log_unmigratable_state(self.entity_id, last_state)
                self.coordinator.mark_control_field_unresolved(
                    "grid_serving_forecast_threshold_kwh"
                )
            return
        await self.coordinator.async_set_grid_serving_forecast_threshold_kwh(
            DEFAULT_GRID_SERVING_FORECAST_THRESHOLD_KWH
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.grid_serving_forecast_threshold_kwh_raw

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_grid_serving_forecast_threshold_kwh(
            value, defer_device_update=True
        )
        self.async_write_ha_state()


class SaxPowerPriceLimitNumber(SaxPowerRestoreConfigEntity, NumberEntity):
    """Preisgrenze für den Modus "Absoluter Preis" des preisoptimierten
    Ladens, in ct/kWh - siehe anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE.

    Unterhalb dieses Arbeitspreises wird aus dem Netz geladen. Negative
    Werte sind zugelassen, weil börsenpreisgekoppelte Tarife zeitweise
    negative Arbeitspreise ausweisen - genau dann ist Laden am
    attraktivsten. In den Modi "Relativ" und "Smart" wird dieser Wert nicht
    ausgewertet.

    Persistiert im Konfigurations-Store (REQ-CONTROL-CONFIG-BOOTSTRAP),
    RestoreEntity nur noch als einmaliger Migrationspfad; ohne beides gilt
    DEFAULT_PRICE_LIMIT.
    """

    _attr_translation_key = "price_charge_max_price"
    _attr_native_min_value = MIN_PRICE_LIMIT * 100
    _attr_native_max_value = MAX_PRICE_LIMIT * 100
    _attr_native_step = PRICE_LIMIT_STEP * 100
    _attr_native_unit_of_measurement = "ct/kWh"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("number", "price_charge_max_price")

    async def _async_restore_control_value(self) -> None:
        if self.coordinator.price_charge_max_price is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (restored := _restorable_price_eur_kwh(last_state)) is not None:
                await self.coordinator.async_set_price_charge_max_price(restored)
            else:
                log_unmigratable_state(self.entity_id, last_state)
                self.coordinator.mark_control_field_unresolved("price_charge_max_price")
            return
        await self.coordinator.async_set_price_charge_max_price(DEFAULT_PRICE_LIMIT)

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.price_charge_max_price
        return None if value is None else value * 100

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_price_charge_max_price(
            value / 100, defer_device_update=True
        )
        self.async_write_ha_state()


class SaxPowerPriceNeutralPriceNumber(SaxPowerRestoreConfigEntity, NumberEntity):
    """Neutralpreis für das preisoptimierte Laden, in ct/kWh - siehe
    anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE.

    Bei Relativ/Smart pausieren nicht zum Laden ausgewählte Slots unterhalb
    dieses Preises. Nur Absoluter Preis benötigt ein offenes Band oberhalb
    der Preisgrenze; widersprüchliche Grenzen meldet SelfDiagnostics.
    REQ-DYNAMIC-PRICE-CHARGE beschreibt Vorränge und Freigabe der Entladung.

    Persistiert im Konfigurations-Store (REQ-CONTROL-CONFIG-BOOTSTRAP),
    RestoreEntity nur noch als einmaliger Migrationspfad; ohne beides gilt
    DEFAULT_PRICE_NEUTRAL.
    """

    _attr_translation_key = "price_charge_neutral_price"
    _attr_native_min_value = MIN_PRICE_LIMIT * 100
    _attr_native_max_value = MAX_PRICE_LIMIT * 100
    _attr_native_step = PRICE_LIMIT_STEP * 100
    _attr_native_unit_of_measurement = "ct/kWh"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("number", "price_charge_neutral_price")

    async def _async_restore_control_value(self) -> None:
        if self.coordinator.price_charge_neutral_price is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (restored := _restorable_price_eur_kwh(last_state)) is not None:
                await self.coordinator.async_set_price_charge_neutral_price(restored)
            else:
                log_unmigratable_state(self.entity_id, last_state)
                self.coordinator.mark_control_field_unresolved(
                    "price_charge_neutral_price"
                )
            return
        await self.coordinator.async_set_price_charge_neutral_price(
            DEFAULT_PRICE_NEUTRAL
        )

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.price_charge_neutral_price
        return None if value is None else value * 100

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_price_charge_neutral_price(
            value / 100, defer_device_update=True
        )
        self.async_write_ha_state()


class SaxPowerPriceChargeHoursNumber(SaxPowerRestoreConfigEntity, NumberEntity):
    """Anzahl der günstigsten Stunden, in denen preisoptimiert geladen wird.

    Wirksam in den Modi "Relativ" (exakt so viele Stunden werden
    ausgewählt) und "Smart" (Obergrenze für die aus dem Energiebedarf
    errechnete Stundenzahl). Im Modus "Absoluter Preis" ohne Wirkung.

    Persistiert im Konfigurations-Store (REQ-CONTROL-CONFIG-BOOTSTRAP),
    RestoreEntity nur noch als einmaliger Migrationspfad; ohne beides gilt
    DEFAULT_PRICE_HOURS.
    """

    _attr_translation_key = "price_charge_hours"
    _attr_native_min_value = MIN_PRICE_HOURS
    _attr_native_max_value = MAX_PRICE_HOURS
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("number", "price_charge_hours")

    async def _async_restore_control_value(self) -> None:
        if self.coordinator.price_charge_hours_raw is not None:
            return
        if (last_state := await self.async_get_last_state()) is not None:
            if (restored := restorable_number(last_state)) is not None:
                await self.coordinator.async_set_price_charge_hours(int(restored))
            else:
                log_unmigratable_state(self.entity_id, last_state)
                self.coordinator.mark_control_field_unresolved("price_charge_hours")
            return
        await self.coordinator.async_set_price_charge_hours(DEFAULT_PRICE_HOURS)

    @property
    def native_value(self) -> int | None:
        return self.coordinator.price_charge_hours_raw

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_price_charge_hours(
            int(value), defer_device_update=True
        )
        self.async_write_ha_state()
