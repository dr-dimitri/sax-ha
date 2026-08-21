"""Button platform for SAX Power."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import SaxPowerCoordinator
from .dashboard import async_create_dashboard
from .entity import SaxPowerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([SaxPowerReinstallDashboardButton(coordinator, entry.entry_id)])


class SaxPowerReinstallDashboardButton(SaxPowerEntity, ButtonEntity):
    """Setzt das mitgelieferte Lovelace-Dashboard (dashboard.py) auf den
    Auslieferungszustand zurück - auch wenn es bereits existiert und der
    Anwender es zwischenzeitlich manuell verändert hat.

    Erscheint auf derselben Geräteseite (Einstellungen -> Geräte & Dienste
    -> SAX Power Home), auf der auch die Diagnosedaten heruntergeladen
    werden können: Home Assistant bietet keine Möglichkeit, dessen
    eingebautes Diagnose-Download-Menü um eigene Einträge zu erweitern,
    ein eigener Button auf der Geräteseite ist der dafür vorgesehene Weg.
    """

    _attr_translation_key = "reinstall_dashboard"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:view-dashboard-edit-outline"

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_reinstall_dashboard"

    async def async_press(self) -> None:
        entry = self.hass.config_entries.async_get_entry(self._entry_id)
        if entry is None:
            raise HomeAssistantError(f"Kein Config Entry {self._entry_id} gefunden")
        await async_create_dashboard(self.hass, entry, force=True)
