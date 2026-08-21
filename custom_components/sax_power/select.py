"""Select platform for SAX Power.

Strategie-Auswahl für das preisoptimierte Laden (Software-Logik, kein
Register) - siehe coordinator.SaxPowerCoordinator (Abschnitt
"Preisoptimiertes Laden"), price_optimizer.compute_plan sowie
anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE.
"""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_PRICE_STRATEGY,
    DATA_COORDINATOR,
    DEFAULT_PRICE_STRATEGY,
    DOMAIN,
    PRICE_STRATEGIES,
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
            SaxPowerPriceStrategySelect(coordinator, entry.entry_id),
        ]
    )


class SaxPowerPriceStrategySelect(RestoreEntity, SaxPowerEntity, SelectEntity):
    """Ladestrategie des preisoptimierten Ladens.

    - `off`      - Automatik stillgelegt, ohne die übrigen Einstellungen
                   (Preisgrenze, Stunden, Ziel-SOC) zu verlieren.
    - `absolute` - lädt, solange der Arbeitspreis unter der Preisgrenze
                   ("Preisoptimiertes Laden Preisgrenze") liegt.
    - `relative` - lädt in den X günstigsten Stunden des Planungshorizonts
                   ("Preisoptimiertes Laden Anzahl Stunden").
    - `smart`    - wie `relative`, rechnet die Stundenzahl aber aus dem
                   tatsächlich noch fehlenden Energiebedarf abzüglich der
                   erwarteten PV-Erzeugung (Options Flow) - lädt also
                   nachts nichts teuer nach, wenn morgen genug Sonne kommt.

    Zustand wird über RestoreEntity über Neustarts hinweg persistiert. Gibt
    es noch keinen gespeicherten Zustand, gilt die im Options Flow
    hinterlegte Vorgabestrategie, sonst DEFAULT_PRICE_STRATEGY.
    """

    _attr_translation_key = "price_charge_strategy"
    _attr_options = list(PRICE_STRATEGIES)

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_price_charge_strategy"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state in PRICE_STRATEGIES:
                await self.coordinator.async_set_price_charge_strategy(last_state.state)
                return
        configured = self.coordinator.options.get(CONF_PRICE_STRATEGY)
        await self.coordinator.async_set_price_charge_strategy(
            configured if configured in PRICE_STRATEGIES else DEFAULT_PRICE_STRATEGY
        )

    @property
    def current_option(self) -> str:
        return self.coordinator.price_charge_strategy

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_price_charge_strategy(option)
        self.async_write_ha_state()
