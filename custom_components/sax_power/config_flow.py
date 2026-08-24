"""Config flow for SAX Power."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .binary_sensor import BINARY_SENSOR_DESCRIPTIONS
from .const import (
    ALL_MONTHS,
    CONF_CREATE_DASHBOARD,
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
    DEFAULT_CREATE_DASHBOARD,
    DEFAULT_PORT,
    DEFAULT_PRICE_UNIT,
    DEFAULT_PV_FORECAST_FACTOR,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID_BASIC,
    DEFAULT_SLAVE_ID_EXTENDED,
    DEFAULT_TIMED_CHARGE_ENABLED,
    DEFAULT_TIMED_CHARGE_END,
    DEFAULT_TIMED_CHARGE_START,
    DOMAIN,
    MAX_PV_FORECAST_FACTOR,
    MIN_PV_FORECAST_FACTOR,
    PRICE_UNITS,
    READ_BLOCK_EXT_LOW1_COUNT,
    READ_BLOCK_EXT_LOW1_START,
    REG_SOC,
    REG_SUN_MANUFACTURER,
    REG_SUN_MODEL,
    REG_SUN_SERIAL_HI,
    REG_SUN_SERIAL_LO,
    REG_SUN_VERSION_GATEWAY,
    REG_SUN_VERSION_MASTER,
)
from .coordinator import decode_ascii_registers
from .sensor import SENSOR_DESCRIPTIONS

_LOGGER = logging.getLogger(__name__)

# Feste Entity-Anzahl je Plattform für die Zusammenfassung auf der
# Abschlussseite der Ersteinrichtung (async_step_finish). sensor.py/
# binary_sensor.py und die zwölf Monats-Schalter je Mechanismus in switch.py
# wachsen am ehesten künftig weiter und werden deshalb dynamisch über die
# jeweiligen Beschreibungslisten/ALL_MONTHS gezählt; number.py, select.py,
# time.py sowie die vier nicht-monatsbezogenen Schalter in switch.py legen
# dagegen eine feste, hier nachgeführte Anzahl an - siehe die jeweiligen
# async_setup_entry-Funktionen.
_ENTITY_COUNT_SENSOR_FIXED = 2  # SaxPowerEnergySensor: geladen/entladen
_ENTITY_COUNT_NUMBER = 6
_ENTITY_COUNT_SELECT = 1
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


# Gemeinsames Schema für Ersteinrichtung (async_step_user) und spätere
# IP-/Verbindungsänderung (async_step_reconfigure). Vorbelegungen für den
# Reconfigure-Fall werden per add_suggested_values_to_schema() injiziert,
# die hier hinterlegten `default`-Werte gelten nur für die Ersteinrichtung.
STEP_CONNECTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        vol.Required(CONF_SLAVE_ID_BASIC, default=DEFAULT_SLAVE_ID_BASIC): vol.Coerce(
            int
        ),
        vol.Required(
            CONF_SLAVE_ID_EXTENDED, default=DEFAULT_SLAVE_ID_EXTENDED
        ): vol.Coerce(int),
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
# bietet an, das mitgelieferte Lovelace-Dashboard anzulegen (dashboard.py).
STEP_DASHBOARD_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_CREATE_DASHBOARD, default=DEFAULT_CREATE_DASHBOARD
        ): cv.boolean,
    }
)


class CannotConnect(Exception):
    """TCP-Verbindung zum SAX Speicher (Basic Mode) konnte nicht hergestellt werden."""


class InvalidResponse(Exception):
    """Speicher hat mit einer Modbus-Fehlerantwort reagiert (z. B. falsche Slave-ID)."""


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

        def reg(address: int) -> int:
            return result.registers[address - READ_BLOCK_EXT_LOW1_START]

        summary["sunspec_available"] = True
        summary["sun_manufacturer"] = decode_ascii_registers(
            [reg(REG_SUN_MANUFACTURER + i) for i in range(4)]
        )
        summary["sun_model"] = decode_ascii_registers(
            [reg(REG_SUN_MODEL + i) for i in range(3)]
        )
        summary["sun_version_master"] = reg(REG_SUN_VERSION_MASTER)
        summary["sun_version_gateway"] = reg(REG_SUN_VERSION_GATEWAY)
        summary["sun_serial_number"] = (reg(REG_SUN_SERIAL_HI) << 16) | reg(
            REG_SUN_SERIAL_LO
        )
    finally:
        client.close()
    return summary


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

    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """DHCP-Discovery (siehe anforderung.yaml, REQ-DHCP-DISCOVERY).

        Bricht ab, wenn der Host bereits über einen bestehenden Eintrag
        konfiguriert ist (unabhängig von Port/Slave-IDs), sowie - über die
        MAC-Adresse als Flow-unique_id - wenn für dasselbe physische Gerät
        bereits ein anderer Discovery-Flow läuft. Letzteres ist nötig, weil
        Geräte ihren DHCP-Lease wiederholt broadcasten und Home Assistant
        dafür bei jedem Broadcast erneut async_step_dhcp aufruft - ohne
        diese Prüfung würde jede Wiederholung eine weitere
        "Erkannt"-Karte erzeugen.
        """
        self._async_abort_entries_match({CONF_HOST: discovery_info.ip})

        await self.async_set_unique_id(format_mac(discovery_info.macaddress))
        self._abort_if_unique_id_configured()

        self._discovered_ip = discovery_info.ip
        self.context["title_placeholders"] = {"host": discovery_info.ip}
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
            else:
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
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        data=user_input,
                        unique_id=f"{host}:{port}",
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
        if user_input is not None:
            self._grid_charge_data = user_input
            return await self.async_step_dashboard()
        return self.async_show_form(
            step_id="grid_charge", data_schema=STEP_GRID_CHARGE_SCHEMA
        )

    async def async_step_dashboard(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dritter, optionaler Schritt der Ersteinrichtung: bietet an, das
        mitgelieferte Lovelace-Dashboard anzulegen (siehe dashboard.py).

        Das Dashboard selbst kann hier noch nicht gebaut werden - dafür
        müssen die Entities erst existieren, was erst nach Anlage des
        Eintrags und Weiterleitung an die Plattformen der Fall ist. Dieser
        Schritt merkt nur die Entscheidung des Anwenders vor;
        __init__.async_setup_entry führt sie später aus. Der Eintrag selbst
        wird erst im nächsten, abschließenden Schritt angelegt (siehe
        async_step_finish).
        """
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
        if user_input is not None:
            return self.async_create_entry(
                title="SAX Power Home",
                data={
                    **self._connection_data,
                    **self._grid_charge_data,
                    **self._dashboard_data,
                },
            )

        summary = await _async_read_finish_summary(
            self._connection_data[CONF_HOST],
            self._connection_data[CONF_PORT],
            self._connection_data[CONF_SLAVE_ID_EXTENDED],
        )
        if summary["sunspec_available"]:
            firmware = (
                f"Master V{summary['sun_version_master']} / "
                f"Gateway V{summary['sun_version_gateway']}"
            )
            serial_number = str(summary["sun_serial_number"])
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


# Options Flow (siehe SaxPowerOptionsFlow): Konfiguration des
# preisoptimierten Ladens. Bewusst NICHT Teil der Ersteinrichtung - die
# Integration ist ohne Strompreis-Sensor voll funktionsfähig, und der
# passende Sensor existiert bei einer frischen Home-Assistant-Installation
# oft noch gar nicht. Siehe anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE.
STEP_OPTIONS_SCHEMA = vol.Schema(
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


class SaxPowerOptionsFlow(OptionsFlow):
    """Konfiguration von Preisautomatik und gemeinsamer PV-Prognose.

    Hier stehen nur die Dinge, die sich nicht sinnvoll als Entity abbilden
    lassen (Auswahl der Quell-Sensoren und deren Interpretation). Die im
    Alltag veränderlichen Stellgrößen - Strategie, Preisgrenze, Anzahl
    Stunden, Ziel-SOC und Mindestprognose - sind dagegen echte Entities am SAX-Gerät
    (select.py/number.py) und damit automatisierbar und in Dashboards
    nutzbar. Die Strategie hat deshalb bewusst KEIN eigenes Feld hier: eine
    im Options Flow hinterlegte Vorgabe hätte ohnehin nur beim allerersten
    Start (vor dem ersten gespeicherten Zustand der Select-Entity)
    überhaupt eine Wirkung gehabt und würde dem Anwender fälschlich
    suggerieren, sie ließe sich hier jederzeit ändern - siehe
    select.SaxPowerPriceStrategySelect.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        schema = self.add_suggested_values_to_schema(
            STEP_OPTIONS_SCHEMA, dict(self.config_entry.options)
        )
        return self.async_show_form(step_id="init", data_schema=schema)
