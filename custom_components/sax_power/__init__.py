"""The SAX Power integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from pymodbus.client import AsyncModbusTcpClient

from .const import (
    ATTR_CONFIRM,
    ATTR_DEVICE_ID,
    ATTR_ENABLED,
    ATTR_END,
    ATTR_FORCE,
    ATTR_POWER,
    ATTR_REASON,
    ATTR_START,
    CONF_CREATE_DASHBOARD,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID_BASIC,
    CONF_SLAVE_ID_EXTENDED,
    DATA_COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID_EXTENDED,
    DOMAIN,
    MAX_ECONOMICS_RESTART_REASON_LENGTH,
    SERVICE_CREATE_DASHBOARD,
    SERVICE_REFRESH_PRICE_PLAN,
    SERVICE_REINSTALL_DASHBOARD,
    SERVICE_RESTART_ECONOMICS_ACCOUNTING,
    SERVICE_SET_GRID_SERVING_WINDOW,
    SERVICE_SET_PRICE_CHARGE_ENABLED,
    SERVICE_SET_TIMED_CHARGE_WINDOW,
    SERVICE_START_GRID_CHARGE,
    SERVICE_STOP_GRID_CHARGE,
)
from .coordinator import SaxPowerCoordinator
from .dashboard import async_check_dashboard_up_to_date, async_create_dashboard

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.TIME,
]


def _require_confirm_true(value: Any) -> Any:
    """`confirm` muss exakt True sein - eine fehlende oder falsch
    geschriebene Bestätigung darf niemals als "ja" durchgehen."""
    coerced = cv.boolean(value)
    if coerced is not True:
        raise vol.Invalid("confirm muss genau 'true' sein")
    return coerced


def _coerce_grid_charge_power(value: Any) -> Any:
    """Erhalte Validierungsfehler im übersetzbaren Coordinator-Pfad.

    Ganzzahlige Strings bleiben aus Kompatibilitätsgründen erlaubt. Alle
    anderen Typen werden unverändert weitergereicht, damit der Coordinator
    sie mit ServiceValidationError statt Voluptuous generisch ablehnt.
    """
    if not isinstance(value, str):
        return value
    try:
        return int(value)
    except ValueError:
        return value


SERVICE_GRID_CHARGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        # Wertebereich und Vorzeichen prüft bewusst der Coordinator, damit
        # ungültige numerische Werte als übersetzbare ServiceValidationError
        # statt als generischer Schemafehler beim Anwender ankommen.
        vol.Required(ATTR_POWER): _coerce_grid_charge_power,
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
# `confirm` muss exakt True sein (REQ-ECONOMICS-OBSERVABILITY) - eine
# Automation, die den Bilanzneustart versehentlich ohne bewusste
# Bestätigung aufruft, darf keine Geldsummen zurücksetzen. `reason` ist
# rein diagnostisch (lokaler Diagnose-Download) und auf eine sinnvolle
# Länge begrenzt.
SERVICE_RESTART_ECONOMICS_ACCOUNTING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_CONFIRM): _require_confirm_true,
        vol.Optional(ATTR_REASON): vol.All(
            cv.string, vol.Length(max=MAX_ECONOMICS_RESTART_REASON_LENGTH)
        ),
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
    await coordinator.async_load_calibration_state()
    await coordinator.async_load_energy_state()
    # Wie async_load_energy_state: muss vor dem ersten Refresh stehen, da
    # dessen Bootstrap (siehe SaxPowerCoordinator._bootstrap_economics_if_ready)
    # bereits im ersten Refresh laufen kann (REQ-ECONOMICS-ACCOUNTING).
    await coordinator.async_load_economics_state()
    # Muss vor dem ersten Refresh stehen: der Coordinator kennt danach die
    # vollständige gespeicherte Ladekonfiguration und sperrt bis
    # async_finish_bootstrap() unten jede steuernde Entscheidung. Sonst
    # würde der erste Refresh aus reinen Defaults heraus auswerten und z. B.
    # Register 40051 auf Modus 0 setzen, obwohl ein gespeichertes
    # Ladefenster gerade aktiv ist (anforderung.yaml,
    # REQ-CONTROL-CONFIG-BOOTSTRAP).
    await coordinator.async_load_control_state()
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
    else:
        # Genau der Fall, den das Flag oben erzeugt: Ab jetzt wird das
        # Dashboard nie wieder gebaut. Ergänzt eine neuere Version einen
        # Tab, fehlt er einem bestehenden Dashboard stillschweigend - der
        # Hinweis darauf ist die einzige Stelle, an der der Anwender davon
        # überhaupt erfährt (siehe dashboard.py, #138).
        await async_check_dashboard_up_to_date(hass, entry)

    # Erst nach dem Plattform-Setup: der Planner wertet beim Registrieren
    # sofort einmal aus und braucht dafür die vollständige Konfiguration -
    # entweder aus dem Store (Regelfall) oder aus dem einmaligen
    # RestoreEntity-Migrationspfad der Plattformen (select.py/number.py).
    coordinator.price_planner.async_setup()
    # Wirtschaftlichkeitsauswertung (REQ-ECONOMICS-TARIFFS): registriert
    # den Zustandsbeobachter des dynamischen Preis-Sensors. Ohne
    # konfigurierten Tarif passiert hier nichts.
    coordinator.tariff_provider.async_setup()
    # Schließt das Bootstrap-Fenster: ab hier ist die Konfiguration
    # vollständig, und genau eine Ladeentscheidung wird angewendet - statt
    # während des Entity-Setups eine Kette von Teilkonfigurationen
    # (REQ-CONTROL-CONFIG-BOOTSTRAP).
    await coordinator.async_finish_bootstrap()
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _async_register_services(hass)
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wendet eine Options-Flow-Änderung (Strompreis-/PV-Prognose-Sensor)
    live auf den laufenden Coordinator an, statt den kompletten Config Entry
    neu zu laden (ursprünglich gemeldeter Bug, siehe anforderung.yaml,
    REQ-GRID-SERVING-CHARGE): Ein voller Reload räumt SaxPowerCoordinator
    komplett ab und baut ihn neu auf - SaxPowerCoordinator.async_shutdown
    ruft dabei async_stop_sun_charge auf, das Register 40051 aktiv auf
    SmartMeter-Nullregelung zurücksetzt, selbst wenn netzdienliches Laden
    gerade aktiv den Sollwert bei 0 % hält. Bei echtem PV-Überschuss beginnt
    der Speicher dadurch sofort wieder zu laden, bis die frisch erzeugte
    Coordinator-Instanz die PV_SURPLUS_HYSTERESIS_CYCLES-Bestätigung erneut
    durchlaufen hat - ein für den Anwender sichtbarer, aber unnötiger
    Kurz-Ladevorgang, ausgelöst durch reines Speichern der Options-Flow-Seite
    (z. B. beim Hinzufügen des Strompreis-/PV-Prognose-Sensors), unabhängig
    von den eigentlichen Lade-Automatiken.

    Der Options Flow betrifft ausschließlich Quell-Sensoren und deren
    Interpretation im price_optimizer.SaxPricePlanner - nie den Modbus-
    Client, die Slave-IDs oder das Scan-Intervall (die stehen unveränderlich
    in entry.data, siehe config_flow.async_step_reconfigure für deren einzigen
    Änderungsweg). Die gemeinsam ausgewertete PV-Prognose kann dabei auch die
    Freigabe des netzdienlichen Ladens ändern. Ein Reload ist für eine reine
    Options-Änderung trotzdem nicht nötig: Die neuen Werte werden direkt in
    den laufenden Coordinator übernommen, der Planner wird erneut aufgesetzt
    und das Ergebnis sofort angewendet -
    SaxPricePlanner.async_setup ist bewusst idempotent (räumt seine alten
    Zustandsbeobachter ab und registriert sie mit den aktuellen Optionen
    neu), ohne Entities, Modbus-Verbindung oder eine laufende
    Lade-Automatik anzutasten. Für die Tarifkonfiguration der
    Wirtschaftlichkeitsauswertung (REQ-ECONOMICS-TARIFFS) gilt dasselbe:
    SaxTariffProvider.async_setup registriert den Zustandsbeobachter des
    dynamischen Preis-Sensors nach demselben idempotenten Muster neu, sodass
    ein Tarif- oder Sensorwechsel weder einen Listener auf der alten Quelle
    zurücklässt noch einen zweiten auf derselben anlegt."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if entry_data is None:
        return
    coordinator: SaxPowerCoordinator = entry_data[DATA_COORDINATOR]
    coordinator.options = dict(entry.options)
    coordinator.price_planner.async_setup()
    coordinator.tariff_provider.async_setup()
    # REQ-ECONOMICS-ACCOUNTING: rein diagnostischer Zeitstempel der letzten
    # Tarifrevision - beeinflusst keine bereits verbuchten Beträge.
    coordinator.notify_tariff_revision()
    await coordinator.async_apply_price_plan()


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

    async def _async_restart_economics_accounting(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        await coordinator.async_restart_economics_accounting(
            reason=call.data.get(ATTR_REASON)
        )

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
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTART_ECONOMICS_ACCOUNTING,
        _async_restart_economics_accounting,
        schema=SERVICE_RESTART_ECONOMICS_ACCOUNTING_SCHEMA,
    )
