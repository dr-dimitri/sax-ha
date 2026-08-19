"""Base entity for the SAX Power integration."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SaxPowerCoordinator


def initial_config_value(hass: HomeAssistant, entry_id: str, key: str) -> Any | None:
    """Liest einen optionalen Vorgabewert aus den Config-Entry-Daten (siehe
    z. B. CONF_TIMED_CHARGE_START in const.py, abgefragt im zweiten Schritt
    der Ersteinrichtung in config_flow.py).

    Nur als letzte Fallback-Stufe gedacht, NACHDEM eine RestoreEntity bereits
    erfolglos nach einem zuvor gespeicherten echten Zustand gefragt wurde
    (siehe z. B. SaxPowerTimedChargeStartTime.async_added_to_hass) - wirkt
    sich dadurch effektiv nur auf den allerersten Start eines neu
    eingerichteten Eintrags aus. Gibt None zurück, wenn kein Config Entry
    gefunden wird oder der Schlüssel fehlt (z. B. bei über Reconfigure
    aktualisierten oder vor Einführung dieses Schritts angelegten Einträgen).
    """
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None:
        return None
    return entry.data.get(key)


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
