"""Number platform for SAX Power."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DATA_COORDINATOR,
    DEFAULT_DISCHARGE_BLOCK_MAX_PRICE,
    DEFAULT_DISCHARGE_BLOCK_MIN_SOC,
    DEFAULT_PRICE_HOURS,
    DEFAULT_PRICE_LIMIT,
    DOMAIN,
    MAX_PRICE_HOURS,
    MAX_PRICE_LIMIT,
    MAX_SOC,
    MIN_PRICE_HOURS,
    MIN_PRICE_LIMIT,
    MIN_SOC,
    PRICE_LIMIT_STEP,
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
            SaxPowerTimedChargeMinSocNumber(coordinator, entry.entry_id),
            SaxPowerPriceLimitNumber(coordinator, entry.entry_id),
            SaxPowerPriceChargeHoursNumber(coordinator, entry.entry_id),
            SaxPowerDischargeBlockMinSocNumber(coordinator, entry.entry_id),
            SaxPowerDischargeBlockMaxPriceNumber(coordinator, entry.entry_id),
        ]
    )


class SaxPowerMaxSocNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Software-seitiges Maximal-SOC für die Ladung.

    Der SAX Speicher besitzt kein natives Max-SOC-Register. Der Coordinator
    erzwingt den Zielwert stattdessen über den SunSpec-Modus (Register
    40051/40049), sowohl während des zeitgesteuerten Ladens als auch
    unabhängig davon - z. B. auch bei einem durch PV-Überschuss vollen
    Speicher (siehe coordinator.SaxPowerCoordinator._async_enforce_grid_charge).
    Dient zusätzlich als Ziel-SOC für das zeitgesteuerte und das
    preisoptimierte Laden (keine eigenen Einstellungen dafür, siehe
    anforderung.yaml REQ-TIMED-SOC-CHARGE und REQ-DYNAMIC-PRICE-CHARGE).

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


class SaxPowerTimedChargeMinSocNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Unterer SOC-Schwellwert ("Min. SOC"), unterhalb dessen die Netzladung
    starten darf - siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE und
    coordinator.SaxPowerCoordinator._async_enforce_grid_charge
    (_timed_charge_armed) für die Hysterese-Logik: einmal unterschritten,
    lädt die Netzladung bis "Max. SOC" durch, statt bei jedem erneuten
    Überschreiten von "Min. SOC" sofort wieder abzubrechen.

    Zustand wird über RestoreEntity über Neustarts hinweg persistiert. Gibt
    es (z. B. direkt nach der Ersteinrichtung) noch keinen gespeicherten
    Zustand, wird MAX_SOC (100 %) als Vorgabewert gesetzt - dadurch verhält
    sich die Netzladung für bestehende Konfigurationen nach diesem Update
    unverändert (SOC ist praktisch immer < 100 %, "Min. SOC" blockiert also
    zunächst nichts), bis der Anwender bewusst einen niedrigeren Schwellwert
    setzt.
    """

    _attr_translation_key = "timed_charge_min_soc"
    _attr_native_min_value = MIN_SOC
    _attr_native_max_value = MAX_SOC
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_timed_charge_min_soc"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.timed_charge_min_soc is not None:
            return
        restored_value: int | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = int(float(last_state.state))
            except (TypeError, ValueError):
                restored_value = None
        await self.coordinator.async_set_timed_charge_min_soc(
            restored_value if restored_value is not None else MAX_SOC
        )

    @property
    def native_value(self) -> int | None:
        return self.coordinator.timed_charge_min_soc

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_timed_charge_min_soc(int(value))
        self.async_write_ha_state()


class SaxPowerPriceLimitNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Preisgrenze für den Modus "Absoluter Preis" des preisoptimierten
    Ladens, in EUR/kWh - siehe anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE.

    Unterhalb dieses Arbeitspreises wird aus dem Netz geladen. Negative
    Werte sind zugelassen, weil börsenpreisgekoppelte Tarife zeitweise
    negative Arbeitspreise ausweisen - genau dann ist Laden am
    attraktivsten. In den Modi "Relativ" und "Smart" wird dieser Wert nicht
    ausgewertet.

    Zustand wird über RestoreEntity über Neustarts hinweg persistiert; ohne
    gespeicherten Zustand gilt DEFAULT_PRICE_LIMIT.
    """

    _attr_translation_key = "price_charge_max_price"
    _attr_native_min_value = MIN_PRICE_LIMIT
    _attr_native_max_value = MAX_PRICE_LIMIT
    _attr_native_step = PRICE_LIMIT_STEP
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_price_charge_max_price"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.price_charge_max_price is not None:
            return
        restored_value: float | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = float(last_state.state)
            except (TypeError, ValueError):
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


class SaxPowerPriceChargeHoursNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Anzahl der günstigsten Stunden, in denen preisoptimiert geladen wird.

    Wirksam in den Modi "Relativ" (exakt so viele Stunden werden
    ausgewählt) und "Smart" (Obergrenze für die aus dem Energiebedarf
    errechnete Stundenzahl). Im Modus "Absoluter Preis" ohne Wirkung.

    Zustand wird über RestoreEntity über Neustarts hinweg persistiert; ohne
    gespeicherten Zustand gilt DEFAULT_PRICE_HOURS.
    """

    _attr_translation_key = "price_charge_hours"
    _attr_native_min_value = MIN_PRICE_HOURS
    _attr_native_max_value = MAX_PRICE_HOURS
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_price_charge_hours"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.price_charge_hours_raw is not None:
            return
        restored_value: int | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = int(float(last_state.state))
            except (TypeError, ValueError):
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


class SaxPowerDischargeBlockMinSocNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Reserve der Entladesperre: unterhalb dieses SOC wird nie gesperrt.

    Verhindert, dass ein fast leerer Speicher sinnlos auf 0 W gehalten wird -
    seine Restenergie bleibt nutzbar, statt ebenfalls aus dem Netz ersetzt zu
    werden. Siehe anforderung.yaml, REQ-DISCHARGE-BLOCK, sowie
    coordinator.SaxPowerCoordinator._discharge_block_eligible.

    Zustand wird über RestoreEntity über Neustarts hinweg persistiert; ohne
    gespeicherten Zustand gilt DEFAULT_DISCHARGE_BLOCK_MIN_SOC.
    """

    _attr_translation_key = "discharge_block_min_soc"
    _attr_native_min_value = MIN_SOC
    _attr_native_max_value = MAX_SOC
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_discharge_block_min_soc"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.discharge_block_min_soc is not None:
            return
        restored_value: int | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = int(float(last_state.state))
            except (TypeError, ValueError):
                restored_value = None
        await self.coordinator.async_set_discharge_block_min_soc(
            restored_value
            if restored_value is not None
            else DEFAULT_DISCHARGE_BLOCK_MIN_SOC
        )

    @property
    def native_value(self) -> int | None:
        return self.coordinator.discharge_block_min_soc

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_discharge_block_min_soc(int(value))
        self.async_write_ha_state()


class SaxPowerDischargeBlockMaxPriceNumber(RestoreEntity, SaxPowerEntity, NumberEntity):
    """Preisschwelle der Entladesperre im Modus "price", in EUR/kWh.

    Unterhalb dieses Arbeitspreises wird das Entladen gesperrt: die billigen
    Stunden deckt das Netz, die gespeicherte Energie bleibt für die teuren
    übrig. In den Modi "off" und "window" wird der Wert nicht ausgewertet;
    bei einem Festpreistarif ist der Modus "price" wirkungslos (siehe
    anforderung.yaml, REQ-DISCHARGE-BLOCK).

    Teilt sich Wertebereich und Schrittweite mit der Preisgrenze des
    preisoptimierten Ladens - negative Werte sind aus demselben Grund
    zugelassen (börsenpreisgekoppelte Tarife). Zustand wird über
    RestoreEntity persistiert; ohne gespeicherten Zustand gilt
    DEFAULT_DISCHARGE_BLOCK_MAX_PRICE.
    """

    _attr_translation_key = "discharge_block_max_price"
    _attr_native_min_value = MIN_PRICE_LIMIT
    _attr_native_max_value = MAX_PRICE_LIMIT
    _attr_native_step = PRICE_LIMIT_STEP
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_discharge_block_max_price"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.discharge_block_max_price is not None:
            return
        restored_value: float | None = None
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                restored_value = float(last_state.state)
            except (TypeError, ValueError):
                restored_value = None
        await self.coordinator.async_set_discharge_block_max_price(
            restored_value
            if restored_value is not None
            else DEFAULT_DISCHARGE_BLOCK_MAX_PRICE
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.discharge_block_max_price

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_discharge_block_max_price(value)
        self.async_write_ha_state()
