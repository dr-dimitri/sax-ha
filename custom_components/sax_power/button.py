"""Button platform for SAX Power."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import SaxPowerCoordinator
from .entity import SaxPowerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([SaxPowerStartDischargeButton(coordinator, entry.entry_id)])


class SaxPowerStartDischargeButton(SaxPowerEntity, ButtonEntity):
    """Startet die Entladung mit dem zentralen Entladeleistungsgrenzwert,
    oder stoppt sie bei erneutem Drücken wieder (Umschalt-Verhalten).

    Nutzt bewusst keine eigene Leistungseinstellung, sondern den bereits
    vorhandenen "Entladeleistungsgrenzwert" (Register 43), um keine
    redundante Einstellmöglichkeit zu erzeugen (siehe anforderung.yaml,
    REQ-DISCHARGE-BUTTON-DEDUP-SETTINGS). Siehe
    SaxPowerCoordinator.async_toggle_discharge.
    """

    _attr_translation_key = "start_discharge"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_start_discharge"

    async def async_press(self) -> None:
        await self.coordinator.async_toggle_discharge()
