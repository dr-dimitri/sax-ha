"""The SAX Power integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from pymodbus.client import AsyncModbusTcpClient

from .const import (
    ATTR_DEVICE_ID,
    ATTR_POWER,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID_BASIC,
    CONF_SLAVE_ID_EXTENDED,
    DATA_COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID_EXTENDED,
    DOMAIN,
    MAX_SETPOINT_POWER,
    MIN_SETPOINT_POWER,
    SERVICE_START_GRID_CHARGE,
    SERVICE_STOP_GRID_CHARGE,
)
from .coordinator import SaxPowerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER, Platform.SWITCH]

SERVICE_GRID_CHARGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_POWER): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_SETPOINT_POWER, max=MAX_SETPOINT_POWER)
        ),
    }
)
SERVICE_STOP_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SAX Power from a config entry."""
    client = AsyncModbusTcpClient(
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_PORT, 502),
    )
    try:
        connected = await client.connect()
    except OSError as err:
        raise ConfigEntryNotReady(
            f"Kann nicht mit {entry.data[CONF_HOST]} verbinden: {err}"
        ) from err
    if not connected:
        raise ConfigEntryNotReady(f"Kann nicht mit {entry.data[CONF_HOST]} verbinden")

    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=entry.data[CONF_SLAVE_ID_BASIC],
        slave_id_extended=entry.data.get(
            CONF_SLAVE_ID_EXTENDED, DEFAULT_SLAVE_ID_EXTENDED
        ),
        scan_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {DATA_COORDINATOR: coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator: SaxPowerCoordinator = entry_data[DATA_COORDINATOR]
        await coordinator.async_shutdown()
        coordinator.client.close()
    return unload_ok


def _coordinator_for_device(hass: HomeAssistant, device_id: str) -> SaxPowerCoordinator:
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if device is None:
        raise HomeAssistantError(f"Unbekanntes Gerät: {device_id}")
    for entry_id in device.config_entries:
        entry_data = hass.data.get(DOMAIN, {}).get(entry_id)
        if entry_data is not None:
            return entry_data[DATA_COORDINATOR]
    raise HomeAssistantError(
        f"Kein SAX Power Coordinator für Gerät {device_id} gefunden"
    )


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_START_GRID_CHARGE):
        return

    async def _async_start_grid_charge(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        await coordinator.async_start_grid_charge(call.data[ATTR_POWER])

    async def _async_stop_grid_charge(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        await coordinator.async_stop_grid_charge()

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_GRID_CHARGE,
        _async_start_grid_charge,
        schema=SERVICE_GRID_CHARGE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_GRID_CHARGE,
        _async_stop_grid_charge,
        schema=SERVICE_STOP_SCHEMA,
    )
