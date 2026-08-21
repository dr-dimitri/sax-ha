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
    ATTR_ENABLED,
    ATTR_END,
    ATTR_FORCE,
    ATTR_POWER,
    ATTR_START,
    CONF_CREATE_DASHBOARD,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID_BASIC,
    CONF_SLAVE_ID_EXTENDED,
    DATA_COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID_EXTENDED,
    DOMAIN,
    MAX_SETPOINT_POWER,
    MIN_SETPOINT_POWER,
    SERVICE_CREATE_DASHBOARD,
    SERVICE_REFRESH_PRICE_PLAN,
    SERVICE_REINSTALL_DASHBOARD,
    SERVICE_SET_GRID_SERVING_WINDOW,
    SERVICE_SET_PRICE_CHARGE_ENABLED,
    SERVICE_SET_TIMED_CHARGE_WINDOW,
    SERVICE_START_GRID_CHARGE,
    SERVICE_STOP_GRID_CHARGE,
)
from .coordinator import SaxPowerCoordinator
from .dashboard import async_create_dashboard

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.TIME,
]

SERVICE_GRID_CHARGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_POWER): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_SETPOINT_POWER, max=MAX_SETPOINT_POWER)
        ),
    }
)
SERVICE_STOP_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})
SERVICE_SET_WINDOW_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_START): cv.time,
        vol.Required(ATTR_END): cv.time,
    }
)
# `force` überspringt den Bestätigungsdialog für den Konflikt zwischen
# Netzladung und preisoptimiertem Laden (siehe repairs.py) - Automationen
# haben keine Möglichkeit, auf einen Repair-Dialog zu antworten.
SERVICE_SET_PRICE_CHARGE_ENABLED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_ENABLED): cv.boolean,
        vol.Optional(ATTR_FORCE, default=False): cv.boolean,
    }
)


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
        entry_id=entry.entry_id,
        options=entry.options,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {DATA_COORDINATOR: coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if entry.data.get(CONF_CREATE_DASHBOARD):
        # Braucht die soeben registrierten Entities, deshalb erst nach dem
        # Plattform-Setup möglich. Absichtlich VOR der Registrierung des
        # Update-Listeners direkt unten: hass.config_entries.async_update_entry
        # löst dessen Reload-Listener aus, sobald er registriert ist - hier
        # ist er das noch nicht, der Reset dieses einmaligen Flags soll aber
        # gerade keinen zusätzlichen Reload direkt nach der Ersteinrichtung
        # auslösen. Siehe const.py, CONF_CREATE_DASHBOARD.
        await async_create_dashboard(hass, entry)
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_CREATE_DASHBOARD: False}
        )

    # Erst nach dem Plattform-Setup: der Planner wertet beim Registrieren
    # sofort einmal aus und braucht dafür die von den Entities (select.py/
    # number.py, RestoreEntity) wiederhergestellten Einstellungen.
    coordinator.price_planner.async_setup()
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _async_register_services(hass)
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Config Entry nach einer Änderung im Options Flow neu laden.

    Die Optionen (Strompreis-/PV-Prognose-Sensor) bestimmen, welche
    Entities der Planner beobachtet - ein Neuladen ist der einfachste Weg,
    diese Beobachter sauber neu aufzusetzen, statt sie zur Laufzeit
    umzuhängen."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator: SaxPowerCoordinator = entry_data[DATA_COORDINATOR]
        await coordinator.async_shutdown()
        coordinator.client.close()
    return unload_ok


def _entry_id_for_device(hass: HomeAssistant, device_id: str) -> str:
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if device is None:
        raise HomeAssistantError(f"Unbekanntes Gerät: {device_id}")
    for entry_id in device.config_entries:
        if entry_id in hass.data.get(DOMAIN, {}):
            return entry_id
    raise HomeAssistantError(
        f"Kein geladener SAX Power Config Entry für Gerät {device_id} gefunden"
    )


def _coordinator_for_device(hass: HomeAssistant, device_id: str) -> SaxPowerCoordinator:
    entry_id = _entry_id_for_device(hass, device_id)
    return hass.data[DOMAIN][entry_id][DATA_COORDINATOR]


def _entry_for_device(hass: HomeAssistant, device_id: str) -> ConfigEntry:
    entry_id = _entry_id_for_device(hass, device_id)
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None:
        raise HomeAssistantError(f"Kein Config Entry {entry_id} gefunden")
    return entry


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_START_GRID_CHARGE):
        return

    async def _async_start_grid_charge(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        await coordinator.async_start_grid_charge(call.data[ATTR_POWER])

    async def _async_stop_grid_charge(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        await coordinator.async_stop_grid_charge()

    async def _async_set_timed_charge_window(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        await coordinator.async_set_timed_charge_window(
            call.data[ATTR_START], call.data[ATTR_END]
        )

    async def _async_set_grid_serving_window(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        await coordinator.async_set_grid_serving_window(
            call.data[ATTR_START], call.data[ATTR_END]
        )

    async def _async_refresh_price_plan(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        coordinator.price_planner.evaluate()
        await coordinator.async_apply_price_plan()

    async def _async_set_price_charge_enabled(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        applied = await coordinator.async_set_price_charge_enabled(
            call.data[ATTR_ENABLED], force=call.data[ATTR_FORCE]
        )
        if not applied:
            raise HomeAssistantError(
                "Preisoptimiertes Laden konnte nicht eingeschaltet werden, weil "
                "die Netzladung (zeitgesteuertes Laden) aktiv ist. Entweder die "
                "Rückfrage unter Einstellungen -> Reparaturen bestätigen oder "
                "den Service mit force: true aufrufen."
            )

    async def _async_create_dashboard_service(call: ServiceCall) -> None:
        entry = _entry_for_device(hass, call.data[ATTR_DEVICE_ID])
        await async_create_dashboard(hass, entry)

    async def _async_reinstall_dashboard_service(call: ServiceCall) -> None:
        entry = _entry_for_device(hass, call.data[ATTR_DEVICE_ID])
        await async_create_dashboard(hass, entry, force=True)

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
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TIMED_CHARGE_WINDOW,
        _async_set_timed_charge_window,
        schema=SERVICE_SET_WINDOW_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_GRID_SERVING_WINDOW,
        _async_set_grid_serving_window,
        schema=SERVICE_SET_WINDOW_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_PRICE_PLAN,
        _async_refresh_price_plan,
        schema=SERVICE_STOP_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_PRICE_CHARGE_ENABLED,
        _async_set_price_charge_enabled,
        schema=SERVICE_SET_PRICE_CHARGE_ENABLED_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_DASHBOARD,
        _async_create_dashboard_service,
        schema=SERVICE_STOP_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REINSTALL_DASHBOARD,
        _async_reinstall_dashboard_service,
        schema=SERVICE_STOP_SCHEMA,
    )
