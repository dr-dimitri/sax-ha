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
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    CONF_PRICE_ATTRIBUTE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_STRATEGY,
    CONF_PRICE_UNIT,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID_BASIC,
    CONF_SLAVE_ID_EXTENDED,
    CONF_TIMED_CHARGE_ENABLED,
    CONF_TIMED_CHARGE_END,
    CONF_TIMED_CHARGE_START,
    DEFAULT_PORT,
    DEFAULT_PRICE_STRATEGY,
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
    PRICE_STRATEGIES,
    PRICE_UNITS,
    REG_SOC,
)

_LOGGER = logging.getLogger(__name__)

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


class SaxPowerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SAX Power."""

    VERSION = 1

    _connection_data: dict[str, Any]

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SaxPowerOptionsFlow:
        return SaxPowerOptionsFlow()

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
            reconfigure_entry.data if reconfigure_entry is not None else None
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
            return self.async_create_entry(
                title="SAX Power Home",
                data={**self._connection_data, **user_input},
            )
        return self.async_show_form(
            step_id="grid_charge", data_schema=STEP_GRID_CHARGE_SCHEMA
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
        vol.Required(CONF_PRICE_STRATEGY, default=DEFAULT_PRICE_STRATEGY): (
            selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=list(PRICE_STRATEGIES),
                    translation_key="price_charge_strategy",
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
    """Konfiguration des preisoptimierten Ladens über die Oberfläche.

    Hier stehen nur die Dinge, die sich nicht sinnvoll als Entity abbilden
    lassen (Auswahl der Quell-Sensoren und deren Interpretation). Die im
    Alltag veränderlichen Stellgrößen - Strategie, Preisgrenze, Anzahl
    Stunden, Ziel-SOC - sind dagegen echte Entities am SAX-Gerät
    (select.py/number.py) und damit automatisierbar und in Dashboards
    nutzbar.

    CONF_PRICE_STRATEGY ist hier nur die Vorgabe für den allerersten Start;
    sobald die Select-Entity einmal einen Zustand gespeichert hat, hat
    dieser Vorrang (analog zu CONF_TIMED_CHARGE_* in der Ersteinrichtung,
    siehe entity.initial_config_value).
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
