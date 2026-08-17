"""Base entity for the SAX Power integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SaxPowerCoordinator


class SaxPowerEntity(CoordinatorEntity[SaxPowerCoordinator]):
    """Base entity providing shared device info for all SAX Power entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="SAX Power Home",
            manufacturer="SAX Power",
            model="Home (Plus)",
        )
