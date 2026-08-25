"""Number platform for SAX Power."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DATA_COORDINATOR,
    DEFAULT_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    DEFAULT_PRICE_HOURS,
    DEFAULT_PRICE_LIMIT,
    DEFAULT_PRICE_NEUTRAL,
    DEFAULT_TIMED_CHARGE_MIN_SOC,
    DOMAIN,
    GRID_SERVING_FORECAST_THRESHOLD_STEP_KWH,
    MAX_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    MAX_PRICE_HOURS,
    MAX_PRICE_LIMIT,
    MAX_SOC,
    MIN_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    MIN_PRICE_HOURS,
    MIN_PRICE_LIMIT,
    MIN_SOC,
    PRICE_LIMIT_STEP,
)
from .coordinator import SaxPowerCoordinator
from .entity import SaxPowerConfigEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        [
            SaxPowerMaxSocNumber(coordinator, entry.entry_id),
            SaxPowerTimedChargeMinSocNumber(coordinator, entry.entry_id),
            SaxPowerGridServingForecastThresholdNumber(coordinator, entry.entry_id),
            SaxPowerPriceLimitNumber(coordinator, entry.entry_id),
            SaxPowerPriceNeutralPriceNumber(coordinator, entry.entry_id),
            SaxPowerPriceChargeHoursNumber(coordinator, entry.entry_id),
        ]
    )


class SaxPowerMaxSocNumber(RestoreEntity, SaxPowerConfigEntity, NumberEntity):
    """Software-seitiges Maximal-SOC für die Ladung.

    Der SAX Speicher besitzt kein natives Max-SOC-Register. Der Coordinator
    erzwingt den Zielwert stattdessen über den SunSpec-Modus (Register
    40051/40049), sowohl während des zeitgesteuerten Ladens als auch
    unabhängig davon - z. B. auch bei einem durch PV-Überschuss vollen
    Speicher (siehe coordinator.SaxPowerCoordinator._async_enforce_grid_charge).
    Dient zusätzlich als Ziel-SOC für das zeitgesteuerte und das
    preisoptimierte Laden (keine eigenen Einstellungen dafür, siehe
    anforderung.yaml REQ-TIMED-SOC-CHARGE und REQ-DYNAMIC-PRICE-CHARGE).

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

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.control_config_restored:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Der Store hat den Wert bereits
            # gesetzt; der RestoreEntity-Pfad ist nur noch der einmalige
            # Migrationsweg für Einträge ohne Store.
            return
        if self.coordinator.max_soc is not None:
            return
        restored_value: int | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = int(float(last_state.state))
            except TypeError, ValueError:
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


class SaxPowerTimedChargeMinSocNumber(
    RestoreEntity, SaxPowerConfigEntity, NumberEntity
):
    """Unterer SOC-Schwellwert ("Min. SOC"), unterhalb dessen die Netzladung
    starten darf - siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE und
    coordinator.SaxPowerCoordinator._async_enforce_grid_charge
    (_timed_charge_armed) für die Hysterese-Logik: einmal unterschritten,
    lädt die Netzladung bis "Max. SOC" durch, statt bei jedem erneuten
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

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.control_config_restored:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Der Store hat den Wert bereits
            # gesetzt; der RestoreEntity-Pfad ist nur noch der einmalige
            # Migrationsweg für Einträge ohne Store.
            return
        if self.coordinator.timed_charge_min_soc is not None:
            return
        restored_value: int | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = int(float(last_state.state))
            except TypeError, ValueError:
                restored_value = None
        await self.coordinator.async_set_timed_charge_min_soc(
            restored_value
            if restored_value is not None
            else DEFAULT_TIMED_CHARGE_MIN_SOC
        )

    @property
    def native_value(self) -> int | None:
        return self.coordinator.timed_charge_min_soc

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_timed_charge_min_soc(int(value))
        self.async_write_ha_state()


class SaxPowerGridServingForecastThresholdNumber(
    RestoreEntity, SaxPowerConfigEntity, NumberEntity
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

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.control_config_restored:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Der Store hat den Wert bereits
            # gesetzt; der RestoreEntity-Pfad ist nur noch der einmalige
            # Migrationsweg für Einträge ohne Store.
            return
        if self.coordinator.grid_serving_forecast_threshold_kwh_raw is not None:
            return
        restored_value: float | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = float(last_state.state)
            except TypeError, ValueError:
                restored_value = None
        await self.coordinator.async_set_grid_serving_forecast_threshold_kwh(
            restored_value
            if restored_value is not None
            else DEFAULT_GRID_SERVING_FORECAST_THRESHOLD_KWH
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.grid_serving_forecast_threshold_kwh_raw

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_grid_serving_forecast_threshold_kwh(value)
        self.async_write_ha_state()


class SaxPowerPriceLimitNumber(RestoreEntity, SaxPowerConfigEntity, NumberEntity):
    """Preisgrenze für den Modus "Absoluter Preis" des preisoptimierten
    Ladens, in EUR/kWh - siehe anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE.

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
    _attr_native_min_value = MIN_PRICE_LIMIT
    _attr_native_max_value = MAX_PRICE_LIMIT
    _attr_native_step = PRICE_LIMIT_STEP
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("number", "price_charge_max_price")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.control_config_restored:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Der Store hat den Wert bereits
            # gesetzt; der RestoreEntity-Pfad ist nur noch der einmalige
            # Migrationsweg für Einträge ohne Store.
            return
        if self.coordinator.price_charge_max_price is not None:
            return
        restored_value: float | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = float(last_state.state)
            except TypeError, ValueError:
                restored_value = None
        await self.coordinator.async_set_price_charge_max_price(
            restored_value if restored_value is not None else DEFAULT_PRICE_LIMIT
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.price_charge_max_price

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_price_charge_max_price(value)
        self.async_write_ha_state()


class SaxPowerPriceNeutralPriceNumber(
    RestoreEntity, SaxPowerConfigEntity, NumberEntity
):
    """Neutralpreis für das preisoptimierte Laden, in EUR/kWh - siehe
    anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE.

    Muss über der Preisgrenze liegen (sonst reparierbares Issue
    ISSUE_PRICE_NEUTRAL_BELOW_LIMIT, siehe
    coordinator._check_price_neutral_below_limit). Liegt der aktuelle Preis
    zwischen Preisgrenze und Neutralpreis, schaltet der Coordinator den
    Speicher in den manuellen Sollwertmodus mit Sollwert 0 (Laden UND
    Entladen gestoppt) statt ihn der SmartMeter-Nullregelung zu überlassen -
    ab dem Neutralpreis lohnt sich die Entladung wieder trotz
    Speicherverlusten, siehe coordinator._async_enforce_grid_charge.

    Persistiert im Konfigurations-Store (REQ-CONTROL-CONFIG-BOOTSTRAP),
    RestoreEntity nur noch als einmaliger Migrationspfad; ohne beides gilt
    DEFAULT_PRICE_NEUTRAL.
    """

    _attr_translation_key = "price_charge_neutral_price"
    _attr_native_min_value = MIN_PRICE_LIMIT
    _attr_native_max_value = MAX_PRICE_LIMIT
    _attr_native_step = PRICE_LIMIT_STEP
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._assign_ids("number", "price_charge_neutral_price")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.control_config_restored:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Der Store hat den Wert bereits
            # gesetzt; der RestoreEntity-Pfad ist nur noch der einmalige
            # Migrationsweg für Einträge ohne Store.
            return
        if self.coordinator.price_charge_neutral_price is not None:
            return
        restored_value: float | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = float(last_state.state)
            except TypeError, ValueError:
                restored_value = None
        await self.coordinator.async_set_price_charge_neutral_price(
            restored_value if restored_value is not None else DEFAULT_PRICE_NEUTRAL
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.price_charge_neutral_price

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_price_charge_neutral_price(value)
        self.async_write_ha_state()


class SaxPowerPriceChargeHoursNumber(RestoreEntity, SaxPowerConfigEntity, NumberEntity):
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

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.control_config_restored:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Der Store hat den Wert bereits
            # gesetzt; der RestoreEntity-Pfad ist nur noch der einmalige
            # Migrationsweg für Einträge ohne Store.
            return
        if self.coordinator.price_charge_hours_raw is not None:
            return
        restored_value: int | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = int(float(last_state.state))
            except TypeError, ValueError:
                restored_value = None
        await self.coordinator.async_set_price_charge_hours(
            restored_value if restored_value is not None else DEFAULT_PRICE_HOURS
        )

    @property
    def native_value(self) -> int | None:
        return self.coordinator.price_charge_hours_raw

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_price_charge_hours(int(value))
        self.async_write_ha_state()
