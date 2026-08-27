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
from homeassistant.const import CONF_HOST, CONF_PORT, CURRENCY_EURO
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .application.economics import parse_price, parse_time
from .binary_sensor import BINARY_SENSOR_DESCRIPTIONS
from .const import (
    ALL_MONTHS,
    CONF_CREATE_DASHBOARD,
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_INVESTMENT_COST,
    CONF_ECONOMICS_PRIOR_RESULT,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_ECONOMICS_WINDOW_END,
    CONF_ECONOMICS_WINDOW_PRICE,
    CONF_ECONOMICS_WINDOW_START,
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
    MIN_ECONOMICS_FEED_IN_PRICE,
    MIN_ECONOMICS_IMPORT_PRICE,
    MIN_ECONOMICS_INVESTMENT_COST,
    MIN_ECONOMICS_PRIOR_RESULT,
    MIN_PV_FORECAST_FACTOR,
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
        vol.Required(
            CONF_ECONOMICS_TARIFF_TYPE, default=TariffType.DISABLED.value
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[tariff_type.value for tariff_type in TariffType],
                translation_key="economics_tariff_type",
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        # REQ-ECONOMICS-AMORTIZATION: unabhängig von der Tarifart (siehe
        # const.ECONOMICS_OPTION_KEYS) - ein Tarifwechsel darf die
        # Investitionskosten nicht löschen. Leer lassen deaktiviert
        # sämtliche Investitions-/Amortisationssensoren.
        vol.Optional(CONF_ECONOMICS_INVESTMENT_COST): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=MIN_ECONOMICS_INVESTMENT_COST,
                max=MAX_ECONOMICS_INVESTMENT_COST,
                step=ECONOMICS_INVESTMENT_COST_STEP,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement=CURRENCY_EURO,
            )
        ),
        # REQ-ECONOMICS-AMORTIZATION: Ertrag aus der Zeit VOR dieser
        # Integration. Wirkt nur auf die Amortisationssensoren, nicht auf
        # das operative Ergebnis (siehe const.CONF_ECONOMICS_PRIOR_RESULT).
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


# --------------------------------------------------------------------------
# Wirtschaftlichkeitsauswertung (siehe anforderung.yaml,
# REQ-ECONOMICS-TARIFFS): Der Tariftyp wird bereits auf der ersten
# Options-Seite gewählt, die tarifspezifischen Preise stehen anschließend in
# einem eigenen Schritt - so sieht der Anwender nie Felder, die für seinen
# Tarif keine Bedeutung haben, und ein deaktivierter Tarif fragt gar keine
# Preise ab.
# --------------------------------------------------------------------------


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

# ALLOW_EXTRA: Schickt das Frontend die erste Seite ein zweites Mal ab
# (Doppelklick bzw. Enter im Eingabefeld plus Klick auf "Absenden"),
# während der Flow bereits auf dieser Folgeseite steht, prüft Home
# Assistant diese Werte gegen DIESES Schema. Ohne ALLOW_EXTRA quittiert
# das der Dialog mit einer Wand aus "extra keys not allowed @
# data[...]"-Rohmeldungen; mit ALLOW_EXTRA erkennt der Schritt die
# wiederholte erste Seite und wiederholt sie einfach (siehe
# SaxPowerOptionsFlow._async_repeat_init).
STEP_ECONOMICS_FIXED_SCHEMA = vol.Schema(
    {
        **_FEED_IN_FIELD,
        vol.Optional(CONF_ECONOMICS_FIXED_IMPORT_PRICE): _price_selector(
            MIN_ECONOMICS_IMPORT_PRICE, MAX_ECONOMICS_IMPORT_PRICE
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

STEP_ECONOMICS_DYNAMIC_SCHEMA = vol.Schema(dict(_FEED_IN_FIELD), extra=vol.ALLOW_EXTRA)

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
            # Optional wie die Preisfelder darüber: eine erneut
            # abgeschickte erste Seite enthält keine Zeitfenstergruppen,
            # und _validate_windows behandelt eine fehlende Gruppe ohnehin
            # wie eine leere.
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
    },
    extra=vol.ALLOW_EXTRA,
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
    Exception aus dem Schritt fliegen zu lassen: das Schema hat die im
    Schema bekannten Preisfelder bereits als Zahl validiert, und ein aus
    einer wiederholten ersten Seite durchgereichter Fremdwert
    (extra=vol.ALLOW_EXTRA) wird ohnehin nicht gespeichert.
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

    #: Auf der ersten Seite abgeschickte Werte, bis der tarifspezifische
    #: Folgeschritt sie vervollständigt (siehe async_step_init).
    _base_options: dict[str, Any]

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            tariff_type = TariffType(user_input[CONF_ECONOMICS_TARIFF_TYPE])
            if tariff_type is TariffType.DYNAMIC and not user_input.get(
                CONF_PRICE_SENSOR
            ):
                # Der dynamische Tarif hat bewusst keine eigene
                # Sensor-Option: Wirtschaftlichkeit und Ladeplanung müssen
                # denselben Preis sehen (REQ-ECONOMICS-TARIFFS). Ohne
                # ausgewählten Sensor gäbe es also gar keine Preisquelle.
                errors[CONF_PRICE_SENSOR] = "economics_price_sensor_required"
            else:
                self._base_options = {
                    key: value
                    for key, value in user_input.items()
                    if key not in ECONOMICS_OPTION_KEYS
                }
                self._base_options[CONF_ECONOMICS_TARIFF_TYPE] = tariff_type.value
                return await self._async_step_for_tariff(tariff_type)

        # Bewusst _suggested statt add_suggested_values_to_schema auf den
        # gespeicherten Options: Nach dem Fehler
        # economics_price_sensor_required soll der Anwender nur den
        # fehlenden Sensor nachtragen müssen. Gegen die reinen Options
        # gerendert verlöre das Formular jede andere Änderung derselben
        # Seite (Tarifart, PV-Prognose, Investitionskosten, Vorlauf) - wie
        # bei allen Folgeschritten gewinnt deshalb die letzte Eingabe.
        return self.async_show_form(
            step_id="init",
            data_schema=self._suggested(STEP_OPTIONS_SCHEMA, user_input),
            errors=errors or None,
        )

    async def _async_step_for_tariff(self, tariff_type: TariffType) -> ConfigFlowResult:
        """Nach der Tarifart verzweigen.

        Ein deaktivierter Tarif braucht keine Einspeisevergütung und wird
        deshalb sofort gespeichert - inklusive Wegräumen aller
        tarifspezifischen Altwerte.
        """
        if tariff_type is TariffType.DISABLED:
            return self.async_create_entry(title="", data=self._base_options)
        if tariff_type is TariffType.FIXED:
            return await self.async_step_economics_fixed()
        if tariff_type is TariffType.TIME_OF_USE:
            return await self.async_step_economics_time_of_use()
        return await self.async_step_economics_dynamic()

    async def async_step_economics_fixed(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Festpreistarif: ein ganztägig konstanter Arbeitspreis."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if (repeated := await self._async_repeat_init(user_input)) is not None:
                return repeated
            errors = _missing_prices(
                user_input,
                (CONF_ECONOMICS_FEED_IN_PRICE, CONF_ECONOMICS_FIXED_IMPORT_PRICE),
            )
            if not errors:
                return self._create_entry(STEP_ECONOMICS_FIXED_SCHEMA, user_input)
        return self.async_show_form(
            step_id="economics_fixed",
            data_schema=self._suggested(STEP_ECONOMICS_FIXED_SCHEMA, user_input),
            errors=errors or None,
        )

    async def async_step_economics_dynamic(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dynamischer Tarif: Preis aus dem bereits gewählten Preis-Sensor."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if (repeated := await self._async_repeat_init(user_input)) is not None:
                return repeated
            errors = _missing_prices(user_input, (CONF_ECONOMICS_FEED_IN_PRICE,))
            if not errors:
                return self._create_entry(STEP_ECONOMICS_DYNAMIC_SCHEMA, user_input)
        return self.async_show_form(
            step_id="economics_dynamic",
            data_schema=self._suggested(STEP_ECONOMICS_DYNAMIC_SCHEMA, user_input),
            errors=errors or None,
        )

    async def async_step_economics_time_of_use(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Tageszeitabhängiger Tarif: Grundpreis + bis zu acht Fenster."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if (repeated := await self._async_repeat_init(user_input)) is not None:
                return repeated
            errors = _missing_prices(
                user_input,
                (CONF_ECONOMICS_FEED_IN_PRICE, CONF_ECONOMICS_TOU_BASE_PRICE),
            )
            issue = _validate_windows(user_input)
            if issue is not None:
                errors["base"] = _WINDOW_ERROR_KEYS[issue.error]
            if not errors:
                return self._create_entry(STEP_ECONOMICS_TOU_SCHEMA, user_input)

        return self.async_show_form(
            step_id="economics_time_of_use",
            data_schema=self._suggested(STEP_ECONOMICS_TOU_SCHEMA, user_input),
            errors=errors or None,
        )

    async def _async_repeat_init(
        self, user_input: dict[str, Any]
    ) -> ConfigFlowResult | None:
        """Wiederholt die erste Seite, falls sie erneut abgeschickt wurde.

        Schickt das Frontend die erste Seite ein zweites Mal ab
        (Doppelklick bzw. Enter im Eingabefeld plus Klick auf "Absenden"),
        prüft Home Assistant diese Werte gegen das Schema dieser
        Folgeseite - erkennbar am Tarifmodell, das es hier gar nicht gibt.
        Ohne diese Behandlung sähe der Anwender eine Wand aus "extra keys
        not allowed @ data[...]"-Rohmeldungen. Stattdessen wird die erste
        Seite einfach erneut ausgewertet: der Dialog landet wieder auf der
        passenden Folgeseite, als wäre nur einmal abgeschickt worden.
        Geprüft wird dabei gegen STEP_OPTIONS_SCHEMA, das Home Assistant
        auf diesem Weg gar nicht mehr anwendet: Ohne diese Prüfung landete
        eine per Websocket von Hand geschickte erste Seite ungeprüft in
        entry.options (fremde Schlüssel, unbrauchbare Werte), und ein
        unbekanntes Tarifmodell ließe async_step_init mit einem
        ValueError aus dem Schritt fliegen. Passt die Eingabe nicht auf
        dieses Schema, ist sie keine wiederholte erste Seite - dann
        liefert die Methode None und der aufrufende Schritt behandelt sie
        wie eine eigene (unvollständige) Eingabe. None ebenso, wenn es
        sich um eine echte Eingabe dieser Seite handelt.
        """
        if CONF_ECONOMICS_TARIFF_TYPE not in user_input:
            return None
        try:
            first_page = STEP_OPTIONS_SCHEMA(user_input)
        except vol.Invalid:
            return None
        return await self.async_step_init(first_page)

    def _create_entry(
        self, schema: vol.Schema, user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        """Speichert erste Seite + Folgeseite, ohne fremde Schlüssel.

        Die Folgeseiten-Schemata lassen zusätzliche Schlüssel zu (siehe
        _async_repeat_init) - gespeichert wird trotzdem ausschließlich, was
        das jeweilige Schema selbst kennt.
        """
        known = {str(marker) for marker in schema.schema}
        rounded = _round_price_fields(user_input)
        return self.async_create_entry(
            title="",
            data={
                **self._base_options,
                **{key: value for key, value in rounded.items() if key in known},
            },
        )

    def _suggested(
        self, schema: vol.Schema, user_input: dict[str, Any] | None = None
    ) -> vol.Schema:
        """Formular mit den zuletzt eingegebenen bzw. gespeicherten Werten.

        Nach einem Validierungsfehler gewinnt die letzte Eingabe: sonst
        müsste der Anwender acht Zeitfenster wegen eines einzigen falschen
        Feldes komplett neu ausfüllen.

        `add_suggested_values_to_schema` baut das Schema dafür neu auf und
        verliert dabei dessen `extra`-Einstellung - die wird hier wieder
        übernommen, sonst scheiterte eine erneut abgeschickte erste Seite
        weiterhin an der Schema-Validierung (siehe _async_repeat_init).
        """
        with_values = self.add_suggested_values_to_schema(
            schema, {**self.config_entry.options, **(user_input or {})}
        )
        return vol.Schema(with_values.schema, extra=schema.extra)


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
