"""Config flow for SAX Power."""

from __future__ import annotations

import logging
import math
import re
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_DHCP,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CURRENCY_EURO
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow, section
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .application.economics import parse_price, parse_time
from .binary_sensor import BINARY_SENSOR_DESCRIPTIONS
from .const import (
    ALL_MONTHS,
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_INVESTMENT_COST,
    CONF_ECONOMICS_PRIOR_RESULT,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_ECONOMICS_WINDOW_END,
    CONF_ECONOMICS_WINDOW_PRICE,
    CONF_ECONOMICS_WINDOW_START,
    CONF_HEMS_ARCHIVE_ENABLED,
    CONF_HEMS_CHARGE_EFFICIENCY,
    CONF_HEMS_DISCHARGE_EFFICIENCY,
    CONF_HEMS_FORECAST_MODE,
    CONF_HEMS_HISTORY_DAYS,
    CONF_HEMS_LIVE_ADJUSTMENT,
    CONF_HEMS_PV_ENTRY,
    CONF_HEMS_PV_PROVIDER,
    CONF_HEMS_SOLCAST_MAX_AGE,
    CONF_HEMS_SOLCAST_TIMESTAMP,
    CONF_HEMS_SOLCAST_TIMESTAMP_REGISTRY_ID,
    CONF_PRICE_ATTRIBUTE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID_BASIC,
    CONF_SLAVE_ID_EXTENDED,
    CONF_TIMED_CHARGE_ENABLED,
    CONF_TIMED_CHARGE_END,
    CONF_TIMED_CHARGE_START,
    CONF_VUE_DASHBOARD_DISMISSED_VERSION,
    CONF_VUE_DASHBOARD_ENABLED,
    CONF_VUE_DASHBOARD_VERSION,
    DEFAULT_PORT,
    DEFAULT_PRICE_UNIT,
    DEFAULT_PV_FORECAST_FACTOR,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID_BASIC,
    DEFAULT_SLAVE_ID_EXTENDED,
    DEFAULT_TIMED_CHARGE_ENABLED,
    DEFAULT_TIMED_CHARGE_END,
    DEFAULT_TIMED_CHARGE_START,
    DEFAULT_VUE_DASHBOARD_ENABLED,
    DOMAIN,
    ECONOMICS_INVESTMENT_COST_STEP,
    ECONOMICS_OPTION_KEYS,
    ECONOMICS_PRICE_DECIMALS,
    ECONOMICS_PRIOR_RESULT_STEP,
    ECONOMICS_TOU_WINDOW_KEYS,
    MAX_ECONOMICS_FEED_IN_PRICE,
    MAX_ECONOMICS_IMPORT_PRICE,
    MAX_ECONOMICS_INVESTMENT_COST,
    MAX_ECONOMICS_PRIOR_RESULT,
    MAX_PV_FORECAST_FACTOR,
    MAX_SOC,
    MIN_ECONOMICS_FEED_IN_PRICE,
    MIN_ECONOMICS_IMPORT_PRICE,
    MIN_ECONOMICS_INVESTMENT_COST,
    MIN_ECONOMICS_PRIOR_RESULT,
    MIN_PV_FORECAST_FACTOR,
    MIN_SOC,
    PRICE_UNITS,
    READ_BLOCK_EXT_LOW1_COUNT,
    READ_BLOCK_EXT_LOW1_START,
    REG_SOC,
)
from .domain.sunspec import SunSpecDecodeError, decode_identity
from .domain.tariff import (
    DailyPriceWindow,
    TariffType,
    TariffWindowError,
    TariffWindowIssue,
    find_overlapping_window,
    validate_window_fields,
)
from .infrastructure.hems_pv import resolve_solcast_timestamp
from .sensor import SENSOR_DESCRIPTIONS

_LOGGER = logging.getLogger(__name__)

_MAC_UNIQUE_ID_PATTERN = re.compile(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}")

# Feste Entity-Anzahl je Plattform für die Zusammenfassung auf der
# Abschlussseite der Ersteinrichtung (async_step_finish). sensor.py/
# binary_sensor.py und die zwölf Monats-Schalter je Mechanismus in switch.py
# wachsen am ehesten künftig weiter und werden deshalb dynamisch über die
# jeweiligen Beschreibungslisten/ALL_MONTHS gezählt; number.py, select.py,
# time.py sowie die vier nicht-monatsbezogenen Schalter in switch.py legen
# dagegen eine feste, hier nachgeführte Anzahl an - siehe die jeweiligen
# async_setup_entry-Funktionen.
_ENTITY_COUNT_SENSOR_FIXED = 2  # SaxPowerEnergySensor: geladen/entladen
_ENTITY_COUNT_NUMBER = 7
_ENTITY_COUNT_SELECT = 2
_ENTITY_COUNT_TIME = 4
_ENTITY_COUNT_SWITCH_FIXED = 4
# Monats-Schalter-Sätze in switch.py: zeitgesteuertes Laden, netzdienliches
# Laden (siehe REQ-GRID-SERVING-CHARGE).
_ENTITY_COUNT_MONTH_SWITCH_SETS = 2


def _expected_entity_count() -> int:
    return (
        len(SENSOR_DESCRIPTIONS)
        + _ENTITY_COUNT_SENSOR_FIXED
        + len(BINARY_SENSOR_DESCRIPTIONS)
        + _ENTITY_COUNT_NUMBER
        + _ENTITY_COUNT_SELECT
        + _ENTITY_COUNT_TIME
        + _ENTITY_COUNT_SWITCH_FIXED
        + _ENTITY_COUNT_MONTH_SWITCH_SETS * len(ALL_MONTHS)
    )


def _is_mac_unique_id(unique_id: str | None) -> bool:
    """Return whether an entry ID is a normalized network MAC address."""
    return (
        unique_id is not None
        and _MAC_UNIQUE_ID_PATTERN.fullmatch(unique_id) is not None
    )


# Gemeinsames Schema für Ersteinrichtung (async_step_user) und spätere
# IP-/Verbindungsänderung (async_step_reconfigure). Vorbelegungen für den
# Reconfigure-Fall werden per add_suggested_values_to_schema() injiziert,
# die hier hinterlegten `default`-Werte gelten nur für die Ersteinrichtung.
STEP_CONNECTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Required(CONF_SLAVE_ID_BASIC, default=DEFAULT_SLAVE_ID_BASIC): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
        vol.Required(
            CONF_SLAVE_ID_EXTENDED, default=DEFAULT_SLAVE_ID_EXTENDED
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=3600)
        ),
    }
)

# Zweiter, optionaler Schritt der Ersteinrichtung (siehe async_step_grid_charge):
# Vorbelegung für das zeitgesteuerte Laden (switch.py/time.py). Alle Felder
# sind optional - wird das Formular ohne Änderungen abgeschickt, gelten die
# hier hinterlegten Defaults (deaktiviert, Zeitfenster 00:00-00:05). Nur für
# den allerersten Start eines neuen Eintrags relevant, siehe
# entity.initial_config_value.
STEP_GRID_CHARGE_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_TIMED_CHARGE_ENABLED, default=DEFAULT_TIMED_CHARGE_ENABLED
        ): cv.boolean,
        vol.Optional(
            CONF_TIMED_CHARGE_START, default=DEFAULT_TIMED_CHARGE_START
        ): selector.TimeSelector(),
        vol.Optional(
            CONF_TIMED_CHARGE_END, default=DEFAULT_TIMED_CHARGE_END
        ): selector.TimeSelector(),
    }
)

# Dritter, optionaler Schritt der Ersteinrichtung (siehe async_step_dashboard):
# bietet an, das Dashboard in der Seitenleiste zu aktivieren.
STEP_DASHBOARD_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_VUE_DASHBOARD_ENABLED, default=DEFAULT_VUE_DASHBOARD_ENABLED
        ): cv.boolean,
    }
)


class CannotConnect(Exception):
    """TCP-Verbindung zum SAX Speicher (Basic Mode) konnte nicht hergestellt werden."""


class InvalidResponse(Exception):
    """Modbus-Antwort enthält keinen gültigen SOC (z. B. falsche Slave-ID)."""


async def _async_validate_connection(host: str, port: int, slave_id: int) -> None:
    """Try to connect and read the SOC register to validate the config.

    Unterscheidet zwei Fehlerarten für gezieltere Rückmeldung im UI:
    CannotConnect (TCP-Verbindung scheitert, z. B. falsche IP/Port) vs.
    InvalidResponse (Verbindung steht, aber der Speicher lehnt die Anfrage
    ab, was meist auf eine falsche Slave-ID hindeutet).
    """
    client = AsyncModbusTcpClient(host=host, port=port)
    try:
        try:
            if not await client.connect():
                raise CannotConnect
        except (ModbusException, OSError) as err:
            raise CannotConnect from err

        try:
            result = await client.read_holding_registers(
                address=REG_SOC, count=1, device_id=slave_id
            )
        except (ModbusException, OSError) as err:
            raise CannotConnect from err
        if result.isError():
            raise InvalidResponse
        # REQ-IP-CONFIGURABLE-UI: Eine quittierte Antwort allein belegt
        # noch keinen lesbaren SAX-Speicher (z. B. falsche Slave-ID).
        if not result.registers:
            raise InvalidResponse
        soc = result.registers[0]
        if (
            isinstance(soc, bool)
            or not isinstance(soc, int)
            or not MIN_SOC <= soc <= MAX_SOC
        ):
            raise InvalidResponse
    finally:
        client.close()


async def _async_read_finish_summary(
    host: str, port: int, slave_id_extended: int
) -> dict[str, Any]:
    """Liest Hersteller/Modell/Firmware/Seriennummer für die Abschlussseite
    der Ersteinrichtung (async_step_finish).

    Rein informativ, siehe anforderung.yaml REQ-SETUP-FINISH-SUMMARY: die
    Basic-Mode-Verbindung wurde bereits in _async_step_connection validiert,
    ein hier fehlschlagender SunSpec-Modus-Block (analog zu
    REQ-EXTENDED-MODE-RESILIENCE) darf die Ersteinrichtung deshalb nicht
    blockieren - er wird nur als "nicht erreichbar" ausgewiesen.
    """
    summary: dict[str, Any] = {
        "sunspec_available": False,
        "sun_manufacturer": None,
        "sun_model": None,
        "sun_version_master": None,
        "sun_version_gateway": None,
        "sun_serial_number": None,
    }
    client = AsyncModbusTcpClient(host=host, port=port)
    try:
        try:
            if not await client.connect():
                return summary
        except ModbusException, OSError:
            return summary

        try:
            result = await client.read_holding_registers(
                address=READ_BLOCK_EXT_LOW1_START,
                count=READ_BLOCK_EXT_LOW1_COUNT,
                device_id=slave_id_extended,
            )
        except ModbusException, OSError:
            return summary
        if result.isError():
            return summary

        # Derselbe Decoder wie im Coordinator (siehe domain/sunspec.py):
        # Zusammenfassung und Sensoren beschreiben dasselbe Gerät und dürfen
        # sich nicht auseinanderentwickeln.
        try:
            identity = decode_identity(result.registers)
        except SunSpecDecodeError:
            return summary

        summary["sunspec_available"] = True
        summary.update(identity.as_data())
    finally:
        client.close()
    return summary


#: Anzeigetext für einen Identitätswert, den das Gerät nicht meldet.
UNKNOWN_IDENTITY_TEXT = "unbekannt"


def _format_firmware_part(label: str, version: int | None) -> str:
    """Ein Halbsatz der Firmware-Zeile ("Master V61"), robust gegen ein
    fehlendes Register."""
    if version is None:
        return f"{label} {UNKNOWN_IDENTITY_TEXT}"
    return f"{label} V{version}"


class SaxPowerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SAX Power."""

    VERSION = 1

    _connection_data: dict[str, Any]
    _grid_charge_data: dict[str, Any]
    _dashboard_data: dict[str, Any]
    _discovered_ip: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SaxPowerOptionsFlow:
        return SaxPowerOptionsFlow()

    @callback
    def _async_abort_if_configured(self) -> None:
        """Keep onboarding limited to one storage system (REQ-IP-CONFIGURABLE-UI)."""
        # Das Manifest-Flag single_config_entry würde auch DHCP-IP-Updates
        # vor async_step_dhcp sperren (REQ-DHCP-DISCOVERY).
        if self._async_current_entries(include_ignore=False):
            raise AbortFlow("single_instance_allowed")

    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """DHCP-Discovery (siehe anforderung.yaml, REQ-DHCP-DISCOVERY).

        Bricht ab, wenn der Host bereits über einen bestehenden Eintrag
        konfiguriert ist (unabhängig von Port/Slave-IDs). Die MAC-Adresse
        bleibt die dauerhafte unique_id eines per DHCP eingerichteten
        Speichers: bei einer späteren Lease mit neuer IP wird nur der Host
        des vorhandenen Eintrags aktualisiert und dessen Reload geplant.
        Dieselbe ID verhindert zugleich parallele Discovery-Flows für
        wiederholte Broadcasts desselben Geräts.
        """
        self._async_abort_entries_match({CONF_HOST: discovery_info.ip})

        await self.async_set_unique_id(format_mac(discovery_info.macaddress))
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})

        self._discovered_ip = discovery_info.ip
        self.context["title_placeholders"] = {"host": discovery_info.ip}
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._async_abort_if_configured()
        return await self._async_step_connection(user_input, step_id="user")

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Verbindungsdaten (u. a. IP-Adresse) eines bestehenden Eintrags ändern.

        Über das Kontextmenü des Geräts ("Neu konfigurieren") jederzeit
        aufrufbar. Die neuen Werte werden validiert und ersetzen bei Erfolg
        vollständig die bisherigen Verbindungsdaten; die Integration wird
        anschließend automatisch neu geladen.
        """
        return await self._async_step_connection(user_input, step_id="reconfigure")

    async def _async_step_connection(
        self, user_input: dict[str, Any] | None, *, step_id: str
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        reconfigure_entry = (
            self._get_reconfigure_entry() if step_id == "reconfigure" else None
        )

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            if reconfigure_entry is not None:
                # Schließt Kollisionen mit einem *anderen* bereits
                # konfigurierten Eintrag aus; der eigene (zu ändernde)
                # Eintrag wird dabei automatisch ausgenommen.
                self._async_abort_entries_match({CONF_HOST: host, CONF_PORT: port})
            elif self.source == SOURCE_DHCP:
                # Die vom DHCP-Schritt gesetzte MAC bleibt die Geräte-ID.
                # Der erneute Zielabgleich schützt auch dann vor Kollisionen,
                # wenn der Anwender die vorbelegte IP im Formular ändert.
                self._async_abort_entries_match({CONF_HOST: host, CONF_PORT: port})
                self._abort_if_unique_id_configured()
            else:
                self._async_abort_entries_match({CONF_HOST: host, CONF_PORT: port})
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()

            try:
                await _async_validate_connection(
                    host, port, user_input[CONF_SLAVE_ID_BASIC]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidResponse:
                errors["base"] = "invalid_response"
            else:
                if reconfigure_entry is not None:
                    unique_id = (
                        reconfigure_entry.unique_id
                        if _is_mac_unique_id(reconfigure_entry.unique_id)
                        else f"{host}:{port}"
                    )
                    updated_data = dict(user_input)
                    for dashboard_key in (
                        CONF_VUE_DASHBOARD_ENABLED,
                        CONF_VUE_DASHBOARD_VERSION,
                        CONF_VUE_DASHBOARD_DISMISSED_VERSION,
                    ):
                        # REQ-VUE-DASHBOARD: Das dauerhafte Setup-Opt-in
                        # muss einen Wechsel der Verbindungsdaten überleben.
                        if dashboard_key in reconfigure_entry.data:
                            updated_data[dashboard_key] = reconfigure_entry.data[
                                dashboard_key
                            ]
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        data=updated_data,
                        unique_id=unique_id,
                    )
                # Ersteinrichtung: Verbindungsdaten merken und weiter zum
                # optionalen Netzladung-Schritt, bevor der Eintrag angelegt
                # wird (siehe async_step_grid_charge).
                self._connection_data = user_input
                return await self.async_step_grid_charge()

        suggested_values = user_input or (
            reconfigure_entry.data
            if reconfigure_entry is not None
            else ({CONF_HOST: self._discovered_ip} if self._discovered_ip else None)
        )
        schema = self.add_suggested_values_to_schema(
            STEP_CONNECTION_SCHEMA, suggested_values
        )
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    async def async_step_grid_charge(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Optionale Vorbelegung für das zeitgesteuerte Laden (zweiter Schritt
        der Ersteinrichtung, nur nach erfolgreich validierter Verbindung
        erreichbar - siehe _async_step_connection).

        Alle Felder sind optional (siehe STEP_GRID_CHARGE_SCHEMA); wird das
        Formular unverändert abgeschickt, gelten die dort hinterlegten
        Defaults (deaktiviert, Zeitfenster 00:00-00:05). Die Werte wirken
        sich nur auf den allerersten Start dieses Eintrags aus - siehe
        entity.initial_config_value sowie anforderung.yaml,
        REQ-TIMED-SOC-CHARGE.
        """
        self._async_abort_if_configured()
        if user_input is not None:
            self._grid_charge_data = user_input
            return await self.async_step_dashboard()
        return self.async_show_form(
            step_id="grid_charge", data_schema=STEP_GRID_CHARGE_SCHEMA
        )

    async def async_step_dashboard(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Merke die dauerhafte Dashboard-Auswahl für das spätere Panel-Setup vor."""
        self._async_abort_if_configured()
        if user_input is not None:
            self._dashboard_data = user_input
            return await self.async_step_finish()
        return self.async_show_form(
            step_id="dashboard", data_schema=STEP_DASHBOARD_SCHEMA
        )

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Vierter, abschließender Schritt der Ersteinrichtung: reine
        Zusammenfassung ohne eigene Eingabefelder (siehe anforderung.yaml,
        REQ-SETUP-FINISH-SUMMARY). Der Config Entry wird erst hier angelegt,
        nachdem die Zusammenfassung feststeht - vorher (async_step_dashboard)
        existiert er noch nicht, ein zwischenzeitlicher Abbruch des Flows
        legt also keinen unvollständigen Eintrag an.
        """
        self._async_abort_if_configured()
        if user_input is not None:
            return self.async_create_entry(
                title="SAX Power Home",
                data={
                    **self._connection_data,
                    **self._grid_charge_data,
                    **self._dashboard_data,
                    CONF_VUE_DASHBOARD_VERSION: "",
                },
            )

        summary = await _async_read_finish_summary(
            self._connection_data[CONF_HOST],
            self._connection_data[CONF_PORT],
            self._connection_data[CONF_SLAVE_ID_EXTENDED],
        )
        if summary["sunspec_available"]:
            # decode_identity liefert None, sobald ein Register den SunSpec-
            # Sentinel "not implemented" meldet (REQ-SUNSPEC-DATATYPES) -
            # dann "unbekannt" anzeigen statt "V None"/"None".
            firmware = (
                f"{_format_firmware_part('Master', summary['sun_version_master'])} / "
                f"{_format_firmware_part('Gateway', summary['sun_version_gateway'])}"
            )
            serial_number = (
                UNKNOWN_IDENTITY_TEXT
                if summary["sun_serial_number"] is None
                else str(summary["sun_serial_number"])
            )
            sunspec_status = "Erreichbar"
        else:
            firmware = "Nicht verfügbar (SunSpec-Modus nicht erreichbar)"
            serial_number = "Nicht verfügbar (SunSpec-Modus nicht erreichbar)"
            sunspec_status = "Nicht erreichbar"

        return self.async_show_form(
            step_id="finish",
            data_schema=vol.Schema({}),
            description_placeholders={
                "firmware": firmware,
                "serial_number": serial_number,
                "sunspec_status": sunspec_status,
                "entity_count": str(_expected_entity_count()),
            },
        )


# REQ-DYNAMIC-PRICE-CHARGE: Quellen und Grundeinstellungen bleiben von den
# automatisierbaren Stellgrößen der Geräte-Entities getrennt.
STEP_DASHBOARD_OPTIONS_SCHEMA = vol.Schema(
    {vol.Required(CONF_VUE_DASHBOARD_ENABLED): cv.boolean}
)

STEP_PRICE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_PRICE_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
        vol.Optional(CONF_PRICE_ATTRIBUTE): selector.TextSelector(),
        vol.Required(CONF_PRICE_UNIT, default=DEFAULT_PRICE_UNIT): (
            selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=list(PRICE_UNITS),
                    translation_key="price_unit",
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        ),
    }
)

STEP_PV_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_PV_FORECAST_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
        vol.Required(
            CONF_PV_FORECAST_FACTOR, default=DEFAULT_PV_FORECAST_FACTOR
        ): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_PV_FORECAST_FACTOR, max=MAX_PV_FORECAST_FACTOR),
        ),
    }
)

STEP_HEMS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HEMS_PV_PROVIDER, default="none"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["none", "pv_forecast", "solcast_solar"],
                translation_key="hems_pv_provider",
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)

STEP_HEMS_SETTINGS_SCHEMA = vol.Schema(
    {
        vol.Optional("forecast"): section(
            vol.Schema(
                {
                    vol.Optional(CONF_HEMS_ARCHIVE_ENABLED, default=False): cv.boolean,
                    vol.Optional(CONF_HEMS_HISTORY_DAYS, default="7"): (
                        selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=["7", "28"],
                                translation_key="hems_history_days",
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        )
                    ),
                    vol.Optional(CONF_HEMS_FORECAST_MODE, default="observe"): (
                        selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=["observe", "auto"],
                                translation_key="hems_forecast_mode",
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        )
                    ),
                    vol.Optional(CONF_HEMS_LIVE_ADJUSTMENT, default=False): cv.boolean,
                }
            ),
            {"collapsed": True},
        ),
        vol.Optional("efficiency"): section(
            vol.Schema(
                {
                    vol.Optional(CONF_HEMS_CHARGE_EFFICIENCY, default=0.95): vol.All(
                        vol.Coerce(float), vol.Range(min=0, min_included=False, max=1)
                    ),
                    vol.Optional(CONF_HEMS_DISCHARGE_EFFICIENCY, default=0.95): vol.All(
                        vol.Coerce(float), vol.Range(min=0, min_included=False, max=1)
                    ),
                }
            ),
            {"collapsed": True},
        ),
    }
)

STEP_ECONOMICS_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_ECONOMICS_TARIFF_TYPE, default=TariffType.DISABLED.value
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[tariff_type.value for tariff_type in TariffType],
                translation_key="economics_tariff_type",
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)

STEP_AMORTIZATION_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ECONOMICS_INVESTMENT_COST): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=MIN_ECONOMICS_INVESTMENT_COST,
                max=MAX_ECONOMICS_INVESTMENT_COST,
                step=ECONOMICS_INVESTMENT_COST_STEP,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement=CURRENCY_EURO,
            )
        ),
        vol.Optional(CONF_ECONOMICS_PRIOR_RESULT): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=MIN_ECONOMICS_PRIOR_RESULT,
                max=MAX_ECONOMICS_PRIOR_RESULT,
                step=ECONOMICS_PRIOR_RESULT_STEP,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement=CURRENCY_EURO,
            )
        ),
    }
)


def _hems_source_schema(provider: str) -> vol.Schema:
    """Nur Quellen der ausgewählten Prognoseintegration anbieten."""
    fields: dict[Any, Any] = {
        vol.Required(CONF_HEMS_PV_ENTRY): selector.ConfigEntrySelector(
            selector.ConfigEntrySelectorConfig(integration=provider)
        ),
    }
    if provider == "solcast_solar":
        fields.update(
            {
                vol.Optional(CONF_HEMS_SOLCAST_TIMESTAMP): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_HEMS_SOLCAST_MAX_AGE, default=24): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=24)
                ),
            }
        )
    return vol.Schema(fields)


def _round_to_price_step(value: float) -> float:
    """Eingabe auf die Schrittweite ECONOMICS_PRICE_STEP festlegen.

    Der NumberSelector kann sie nicht selbst erzwingen (er lässt als
    kleinste Schrittweite 0,001 zu); ohne diese Rundung landeten
    Fließkomma-Artefakte einer freien Eingabe dauerhaft in entry.options.
    """
    return round(float(value), ECONOMICS_PRICE_DECIMALS)


def _price_selector(minimum: float, maximum: float) -> selector.NumberSelector:
    """Eingabefeld für einen Brutto-Arbeitspreis in EUR/kWh.

    Bewusst ein nackter NumberSelector ohne umschließendes vol.All: Home
    Assistant übersetzt jedes Formularschema für das Frontend mit
    voluptuous_serialize, und dabei muss JEDER Validator eines vol.All
    übersetzbar sein. Eine gewöhnliche Python-Funktion (hier früher
    _round_to_price_step) ist es nicht - die Serialisierung scheiterte mit
    "Unable to convert schema", und zwar erst NACH dem eigentlichen
    Flow-Schritt in der Websocket-Schicht. Das Frontend bekam damit kein
    Formular, sondern nur "Unknown error occurred", und keine einzige
    Tarifseite war mehr erreichbar (Issue #135). Gerundet wird deshalb
    jetzt im Schritt selbst (_round_price_fields); die Bereichsprüfung
    übernimmt der NumberSelector weiterhin selbst.
    """
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step="any",
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="EUR/kWh",
        )
    )


# Die Preisfelder der Folgeseiten sind im Schema bewusst vol.Optional und
# werden erst im Schritt selbst auf Vollständigkeit geprüft
# (_missing_prices): Ein vol.Required scheitert bereits in der
# Schema-Validierung von Home Assistant, also VOR dem Schritt - der
# Anwender sähe dann die unübersetzte Rohmeldung "required key not
# provided" statt eines erklärenden Feldfehlers. Pflicht bleiben sie
# dadurch trotzdem: ohne Preis wird kein Eintrag geschrieben.
_FEED_IN_FIELD = {
    vol.Optional(CONF_ECONOMICS_FEED_IN_PRICE): _price_selector(
        MIN_ECONOMICS_FEED_IN_PRICE, MAX_ECONOMICS_FEED_IN_PRICE
    ),
}

STEP_ECONOMICS_FIXED_SCHEMA = vol.Schema(
    {
        **_FEED_IN_FIELD,
        vol.Optional(CONF_ECONOMICS_FIXED_IMPORT_PRICE): _price_selector(
            MIN_ECONOMICS_IMPORT_PRICE, MAX_ECONOMICS_IMPORT_PRICE
        ),
    }
)

STEP_ECONOMICS_DYNAMIC_SCHEMA = vol.Schema(dict(_FEED_IN_FIELD))

# Jede der acht Zeitfenstergruppen ist eine eigene, eingeklappte Section:
# ohne die Gruppierung stünden 24 gleich aussehende Einzelfelder
# untereinander, und die Zuordnung Start/Ende/Preis wäre nicht mehr
# erkennbar. Alle Felder einer Gruppe sind optional - eine Gruppe ist
# entweder vollständig leer oder vollständig befüllt, geprüft in
# _validate_windows.
STEP_ECONOMICS_TOU_SCHEMA = vol.Schema(
    {
        **_FEED_IN_FIELD,
        vol.Optional(CONF_ECONOMICS_TOU_BASE_PRICE): _price_selector(
            MIN_ECONOMICS_IMPORT_PRICE, MAX_ECONOMICS_IMPORT_PRICE
        ),
        **{
            vol.Optional(key): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_ECONOMICS_WINDOW_START
                        ): selector.TimeSelector(),
                        vol.Optional(
                            CONF_ECONOMICS_WINDOW_END
                        ): selector.TimeSelector(),
                        vol.Optional(CONF_ECONOMICS_WINDOW_PRICE): _price_selector(
                            MIN_ECONOMICS_IMPORT_PRICE, MAX_ECONOMICS_IMPORT_PRICE
                        ),
                    }
                ),
                {"collapsed": True},
            )
            for key in ECONOMICS_TOU_WINDOW_KEYS
        },
    }
)

#: Preisfelder der Tarifseiten auf oberster Ebene. Die Preise der acht
#: Zeitfenstergruppen stecken je eine Ebene tiefer in ihrer Section und
#: werden in _round_price_fields getrennt behandelt.
_TOP_LEVEL_PRICE_KEYS = (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
)


def _round_price_fields(user_input: dict[str, Any]) -> dict[str, Any]:
    """Kopie der Eingabe mit allen Preisen auf ECONOMICS_PRICE_DECIMALS.

    Der Aufrufer rundet unmittelbar vor dem Speichern, weil die Rundung
    nicht mehr im Schema stattfinden darf (siehe _price_selector).
    Nicht auswertbare Werte bleiben unverändert stehen, statt hier eine
    Exception aus dem Schritt fliegen zu lassen. Die Vollständigkeitsprüfung
    kann dadurch für fehlende oder ungültige Preise einen Feldfehler melden.
    """
    rounded = dict(user_input)
    for key in _TOP_LEVEL_PRICE_KEYS:
        if (price := parse_price(rounded.get(key))) is not None:
            rounded[key] = _round_to_price_step(price)
    for key in ECONOMICS_TOU_WINDOW_KEYS:
        group = rounded.get(key)
        if not isinstance(group, dict):
            continue
        price = parse_price(group.get(CONF_ECONOMICS_WINDOW_PRICE))
        if price is None:
            continue
        rounded[key] = {
            **group,
            CONF_ECONOMICS_WINDOW_PRICE: _round_to_price_step(price),
        }
    return rounded


#: Übersetzungsschlüssel des fehlenden Pflichtpreises (options.error.* in
#: strings.json) - anders als die Zeitfensterfehler darunter wird er an
#: seinem eigenen Feld gemeldet.
_PRICE_REQUIRED_ERROR = "economics_price_required"

# Übersetzungsschlüssel der Zeitfensterfehler (options.error.* in
# strings.json). Der Fehler wird an "base" gemeldet: Home Assistant kann
# einen Feldfehler keiner Section zuordnen.
_WINDOW_ERROR_KEYS = {
    TariffWindowError.INCOMPLETE: "economics_tou_window_incomplete",
    TariffWindowError.ZERO_LENGTH: "economics_tou_window_zero_length",
    TariffWindowError.OVERLAP: "economics_tou_window_overlap",
}


class SaxPowerOptionsFlow(OptionsFlow):
    """Grundeinstellungen in unabhängigen, überschaubaren Bereichen ändern."""

    def __init__(self) -> None:
        """Mehrstufige Bereiche erst nach ihrem letzten Formular speichern."""
        self._base_options: dict[str, Any] | None = None
        self._edited_keys: set[str] = set()
        self._price_for_economics = False

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._begin_options()
        self._price_for_economics = False
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "dashboard",
                "price",
                "pv",
                "hems",
                "economics",
                "amortization",
            ],
        )

    async def async_step_dashboard(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Die Anzeige des SAX-Dashboards unabhängig von Quellen ändern."""
        self._begin_options()
        if user_input is not None:
            self._replace_options(STEP_DASHBOARD_OPTIONS_SCHEMA, user_input)
            return self._save_options()
        return self.async_show_form(
            step_id="dashboard",
            data_schema=self._suggested(STEP_DASHBOARD_OPTIONS_SCHEMA),
            last_step=True,
        )

    async def async_step_price(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Gemeinsame Preisquelle für Ladeplanung und Wirtschaftlichkeit wählen."""
        if not self._price_for_economics:
            self._begin_options()
        assert self._base_options is not None
        errors: dict[str, str] = {}
        if user_input is not None:
            if self._base_options.get(
                CONF_ECONOMICS_TARIFF_TYPE
            ) == TariffType.DYNAMIC.value and not user_input.get(CONF_PRICE_SENSOR):
                errors[CONF_PRICE_SENSOR] = "economics_price_sensor_required"
            else:
                self._replace_options(STEP_PRICE_SCHEMA, user_input)
                if self._price_for_economics:
                    return await self.async_step_economics_dynamic()
                return self._save_options()
        return self.async_show_form(
            step_id="price",
            data_schema=self._suggested(STEP_PRICE_SCHEMA, user_input),
            errors=errors or None,
            last_step=not self._price_for_economics,
        )

    async def async_step_pv(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Die Tagesprognose für netzdienliches Laden konfigurieren."""
        self._begin_options()
        if user_input is not None:
            self._replace_options(STEP_PV_SCHEMA, user_input)
            return self._save_options()
        return self.async_show_form(
            step_id="pv",
            data_schema=self._suggested(STEP_PV_SCHEMA),
            last_step=True,
        )

    async def async_step_hems(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Den Prognoseanbieter der bedarfsgesteuerten Nachtregelung wählen."""
        self._begin_options()
        if user_input is not None:
            provider = user_input[CONF_HEMS_PV_PROVIDER]
            previous_provider = self._base_options.get(CONF_HEMS_PV_PROVIDER, "none")
            self._replace_options(STEP_HEMS_SCHEMA, user_input)
            if provider == "none" or provider != previous_provider:
                self._remove_options(
                    CONF_HEMS_PV_ENTRY,
                    CONF_HEMS_SOLCAST_TIMESTAMP,
                    CONF_HEMS_SOLCAST_TIMESTAMP_REGISTRY_ID,
                )
            if provider == "none":
                return self._save_options()
            return await self.async_step_hems_source()
        return self.async_show_form(
            step_id="hems",
            data_schema=self._suggested(STEP_HEMS_SCHEMA),
        )

    async def async_step_hems_source(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Die konkrete Prognosequelle und optional Solcasts Zeitstempel prüfen."""
        assert self._base_options is not None
        provider = self._base_options[CONF_HEMS_PV_PROVIDER]
        schema = _hems_source_schema(provider)
        errors: dict[str, str] = {}
        if user_input is not None:
            pv_entry = self.hass.config_entries.async_get_entry(
                user_input.get(CONF_HEMS_PV_ENTRY, "")
            )
            if pv_entry is None or pv_entry.domain != provider:
                errors[CONF_HEMS_PV_ENTRY] = "hems_pv_entry_invalid"
            timestamp_registry_id: str | None = None
            source_input = dict(user_input)
            if provider == "solcast_solar":
                max_age = user_input.get(CONF_HEMS_SOLCAST_MAX_AGE, 24)
                if not math.isfinite(max_age):
                    errors[CONF_HEMS_SOLCAST_MAX_AGE] = "hems_invalid_number"
                timestamp = user_input.get(CONF_HEMS_SOLCAST_TIMESTAMP)
                if timestamp and pv_entry is not None:
                    stored_timestamp = self._base_options.get(
                        CONF_HEMS_SOLCAST_TIMESTAMP
                    )
                    same_source = self._base_options.get(CONF_HEMS_PV_ENTRY) == (
                        pv_entry.entry_id
                    )
                    entity = resolve_solcast_timestamp(
                        er.async_get(self.hass),
                        pv_entry.entry_id,
                        entity_id=timestamp,
                        registry_id=(
                            self._base_options.get(
                                CONF_HEMS_SOLCAST_TIMESTAMP_REGISTRY_ID
                            )
                            if same_source and timestamp == stored_timestamp
                            else None
                        ),
                        allow_legacy_rename=same_source
                        and timestamp == stored_timestamp,
                    )
                    if entity is None:
                        errors[CONF_HEMS_SOLCAST_TIMESTAMP] = "hems_pv_entry_invalid"
                    else:
                        source_input[CONF_HEMS_SOLCAST_TIMESTAMP] = entity.entity_id
                        timestamp_registry_id = entity.id
            if not errors:
                self._replace_options(schema, source_input)
                self._remove_options(CONF_HEMS_SOLCAST_TIMESTAMP_REGISTRY_ID)
                if provider != "solcast_solar":
                    self._remove_options(CONF_HEMS_SOLCAST_TIMESTAMP)
                if timestamp_registry_id is not None:
                    self._base_options[CONF_HEMS_SOLCAST_TIMESTAMP_REGISTRY_ID] = (
                        timestamp_registry_id
                    )
                return await self.async_step_hems_settings()
        return self.async_show_form(
            step_id="hems_source",
            data_schema=self._suggested(schema, user_input),
            errors=errors or None,
            last_step=False,
        )

    async def async_step_hems_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Prognoseverhalten und Speicherverluste als zusammengehörige Gruppen."""
        errors: dict[str, str] = {}
        if user_input is not None:
            for field in (
                CONF_HEMS_CHARGE_EFFICIENCY,
                CONF_HEMS_DISCHARGE_EFFICIENCY,
            ):
                value = user_input.get("efficiency", {}).get(field)
                if value is not None and not math.isfinite(value):
                    # Home Assistant kann Feldfehler keiner Section zuordnen.
                    errors["base"] = "hems_invalid_number"
            if not errors:
                for marker, group in STEP_HEMS_SETTINGS_SCHEMA.schema.items():
                    if str(marker) in user_input:
                        self._replace_options(group.schema, user_input[str(marker)])
                return self._save_options()
        return self.async_show_form(
            step_id="hems_settings",
            data_schema=self._suggested(STEP_HEMS_SETTINGS_SCHEMA, user_input),
            errors=errors or None,
            last_step=True,
        )

    async def async_step_economics(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Nur die zur gewählten Tarifart passenden Preisfelder abfragen."""
        self._begin_options()
        self._price_for_economics = False
        if user_input is not None:
            tariff_type = TariffType(user_input[CONF_ECONOMICS_TARIFF_TYPE])
            self._replace_options(STEP_ECONOMICS_SCHEMA, user_input)
            if tariff_type is TariffType.DISABLED:
                return self._save_tariff(vol.Schema({}), {})
            if tariff_type is TariffType.FIXED:
                return await self.async_step_economics_fixed()
            if tariff_type is TariffType.TIME_OF_USE:
                return await self.async_step_economics_time_of_use()
            if not self._base_options.get(CONF_PRICE_SENSOR):
                self._price_for_economics = True
                return await self.async_step_price()
            return await self.async_step_economics_dynamic()
        return self.async_show_form(
            step_id="economics",
            data_schema=self._suggested(STEP_ECONOMICS_SCHEMA),
        )

    async def async_step_economics_fixed(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Festpreistarif: ein ganztägig konstanter Arbeitspreis."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _missing_prices(
                user_input,
                (CONF_ECONOMICS_FEED_IN_PRICE, CONF_ECONOMICS_FIXED_IMPORT_PRICE),
            )
            if not errors:
                return self._save_tariff(STEP_ECONOMICS_FIXED_SCHEMA, user_input)
        return self.async_show_form(
            step_id="economics_fixed",
            data_schema=self._suggested(STEP_ECONOMICS_FIXED_SCHEMA, user_input),
            errors=errors or None,
            last_step=True,
        )

    async def async_step_economics_dynamic(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dynamischer Tarif: Preis aus dem gemeinsam genutzten Preis-Sensor."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _missing_prices(user_input, (CONF_ECONOMICS_FEED_IN_PRICE,))
            if not errors:
                self._base_options = self._merged_options()
                if not self._base_options.get(CONF_PRICE_SENSOR):
                    # Ein parallel geänderter Bereich kann die Preisquelle seit
                    # der Tarifwahl entfernt haben (REQ-ECONOMICS-TARIFFS).
                    self._replace_options(
                        STEP_ECONOMICS_DYNAMIC_SCHEMA, _round_price_fields(user_input)
                    )
                    self._price_for_economics = True
                    return await self.async_step_price()
                return self._save_tariff(STEP_ECONOMICS_DYNAMIC_SCHEMA, user_input)
        return self.async_show_form(
            step_id="economics_dynamic",
            data_schema=self._suggested(STEP_ECONOMICS_DYNAMIC_SCHEMA, user_input),
            errors=errors or None,
            last_step=True,
        )

    async def async_step_economics_time_of_use(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Tageszeitabhängiger Tarif: Grundpreis und bis zu acht Zeitfenster."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _missing_prices(
                user_input,
                (CONF_ECONOMICS_FEED_IN_PRICE, CONF_ECONOMICS_TOU_BASE_PRICE),
            )
            issue = _validate_windows(user_input)
            if issue is not None:
                errors["base"] = _WINDOW_ERROR_KEYS[issue.error]
            if not errors:
                return self._save_tariff(STEP_ECONOMICS_TOU_SCHEMA, user_input)
        return self.async_show_form(
            step_id="economics_time_of_use",
            data_schema=self._suggested(STEP_ECONOMICS_TOU_SCHEMA, user_input),
            errors=errors or None,
            last_step=True,
        )

    async def async_step_amortization(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Investitionskosten und bisheriges Ergebnis unabhängig vom Tarif ändern."""
        self._begin_options()
        if user_input is not None:
            self._replace_options(STEP_AMORTIZATION_SCHEMA, user_input)
            return self._save_options()
        return self.async_show_form(
            step_id="amortization",
            data_schema=self._suggested(STEP_AMORTIZATION_SCHEMA),
            last_step=True,
        )

    def _begin_options(self) -> None:
        """Einen Bereich auf dem aktuellen gespeicherten Zustand beginnen."""
        self._base_options = dict(self.config_entry.options)
        self._edited_keys = set()

    def _remove_options(self, *keys: str) -> None:
        """Explizite Löschungen auch beim abschließenden Zusammenführen erhalten."""
        assert self._base_options is not None
        for key in keys:
            self._base_options.pop(key, None)
            self._edited_keys.add(key)

    def _replace_options(self, schema: vol.Schema, user_input: dict[str, Any]) -> None:
        """Nur eigene Felder ersetzen; geleerte optionale Felder wirklich entfernen."""
        assert self._base_options is not None
        for marker in schema.schema:
            key = str(marker)
            self._remove_options(key)
            value = user_input.get(key)
            if value is not None and value != "" and value != {}:
                self._base_options[key] = value

    def _save_tariff(
        self, schema: vol.Schema, user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        """Alte Tarifpreise entfernen, unabhängige Amortisationswerte erhalten."""
        assert self._base_options is not None
        self._remove_options(
            *(key for key in ECONOMICS_OPTION_KEYS if key != CONF_ECONOMICS_TARIFF_TYPE)
        )
        self._replace_options(schema, _round_price_fields(user_input))
        return self._save_options()

    def _merged_options(self) -> dict[str, Any]:
        """Parallel gespeicherte Änderungen an anderen Bereichen beibehalten."""
        assert self._base_options is not None
        options = dict(self.config_entry.options)
        for key in self._edited_keys:
            options.pop(key, None)
            if key in self._base_options:
                options[key] = self._base_options[key]
        return options

    def _save_options(self) -> ConfigFlowResult:
        """Den vollständigen Bereich einschließlich aller vorigen Schritte speichern."""
        self._base_options = self._merged_options()
        self._mark_vue_activation()
        return self.async_create_entry(title="", data=self._base_options)

    def _mark_vue_activation(self) -> None:
        """REQ-VUE-DASHBOARD-REPAIR: Erstaktivierung braucht keine Reload-Erinnerung."""
        assert self._base_options is not None
        previously_enabled = self.config_entry.options.get(
            CONF_VUE_DASHBOARD_ENABLED,
            self.config_entry.data.get(
                CONF_VUE_DASHBOARD_ENABLED, DEFAULT_VUE_DASHBOARD_ENABLED
            ),
        )
        if (
            not previously_enabled
            and self._base_options.get(CONF_VUE_DASHBOARD_ENABLED)
            and CONF_VUE_DASHBOARD_VERSION not in self.config_entry.data
        ):
            data = {**self.config_entry.data, CONF_VUE_DASHBOARD_VERSION: ""}
            data.pop(CONF_VUE_DASHBOARD_DISMISSED_VERSION, None)
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)

    def _suggested(
        self, schema: vol.Schema, user_input: dict[str, Any] | None = None
    ) -> vol.Schema:
        """Entwurf vorfüllen und bei Fehlern auch geleerte Eingabefelder erhalten."""
        options = dict(
            self.config_entry.options
            if self._base_options is None
            else self._base_options
        )
        options.setdefault(
            CONF_VUE_DASHBOARD_ENABLED,
            self.config_entry.data.get(
                CONF_VUE_DASHBOARD_ENABLED, DEFAULT_VUE_DASHBOARD_ENABLED
            ),
        )
        if options.get(CONF_HEMS_PV_PROVIDER) == "solcast_solar" and options.get(
            CONF_HEMS_SOLCAST_TIMESTAMP
        ):
            timestamp = resolve_solcast_timestamp(
                er.async_get(self.hass),
                options.get(CONF_HEMS_PV_ENTRY, ""),
                entity_id=options[CONF_HEMS_SOLCAST_TIMESTAMP],
                registry_id=options.get(CONF_HEMS_SOLCAST_TIMESTAMP_REGISTRY_ID),
                allow_legacy_rename=True,
            )
            if timestamp is not None:
                options[CONF_HEMS_SOLCAST_TIMESTAMP] = timestamp.entity_id
        for marker, field_schema in schema.schema.items():
            key = str(marker)
            hems_group = isinstance(field_schema, section) and key in (
                "forecast",
                "efficiency",
            )
            if hems_group:
                options[key] = {
                    str(field): options[str(field)]
                    for field in field_schema.schema.schema
                    if str(field) in options
                }
            if user_input is not None and (not hems_group or key in user_input):
                options.pop(key, None)
        if user_input is not None:
            options.update(user_input)
        return self.add_suggested_values_to_schema(schema, options)


def _missing_prices(
    user_input: dict[str, Any], required_keys: tuple[str, ...]
) -> dict[str, str]:
    """Feldfehler für jeden fehlenden Pflichtpreis einer Tarifseite.

    Die Preisfelder sind im Schema optional (siehe _FEED_IN_FIELD), damit
    ein fehlender Wert als erklärter Feldfehler und nicht als
    unübersetzte Schema-Rohmeldung erscheint - Pflicht sind sie trotzdem.
    """
    return {
        key: _PRICE_REQUIRED_ERROR
        for key in required_keys
        if user_input.get(key) is None
    }


def _validate_windows(user_input: dict[str, Any]) -> TariffWindowIssue | None:
    """Erste Regelverletzung der acht Zeitfenstergruppen, oder None.

    Geprüft werden die Regeln aus REQ-ECONOMICS-TARIFFS: vollständig leer
    oder vollständig befüllt, `start == end` ist ungültig (und bedeutet
    ausdrücklich nicht "ganzer Tag"), und zwei Fenster dürfen sich auf der
    zyklischen 24-Stunden-Zeitleiste nicht überschneiden - angrenzende
    Grenzen dagegen schon, weil die Intervalle halboffen sind.
    """
    windows: list[tuple[int, DailyPriceWindow]] = []
    for index, key in enumerate(ECONOMICS_TOU_WINDOW_KEYS, start=1):
        group = user_input.get(key) or {}
        start = parse_time(group.get(CONF_ECONOMICS_WINDOW_START))
        end = parse_time(group.get(CONF_ECONOMICS_WINDOW_END))
        price = parse_price(group.get(CONF_ECONOMICS_WINDOW_PRICE))
        issue = validate_window_fields(index, start, end, price)
        if issue is not None:
            return issue
        if start is None or end is None or price is None:
            continue
        windows.append(
            (index, DailyPriceWindow(start=start, end=end, price_eur_kwh=price))
        )
    return find_overlapping_window(windows)
