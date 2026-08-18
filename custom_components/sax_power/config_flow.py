"""Config flow for SAX Power."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import config_validation as cv
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID_BASIC,
    CONF_SLAVE_ID_EXTENDED,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID_BASIC,
    DEFAULT_SLAVE_ID_EXTENDED,
    DOMAIN,
    REG_SOC,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
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


class CannotConnect(Exception):
    """Error to indicate we cannot connect to the SAX storage system."""


async def _async_validate_connection(host: str, port: int, slave_id: int) -> None:
    """Try to connect and read the SOC register to validate the config."""
    client = AsyncModbusTcpClient(host=host, port=port)
    try:
        if not await client.connect():
            raise CannotConnect
        result = await client.read_holding_registers(
            address=REG_SOC, count=1, device_id=slave_id
        )
        if result.isError():
            raise CannotConnect
    except (ModbusException, OSError) as err:
        raise CannotConnect from err
    finally:
        client.close()


class SaxPowerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SAX Power."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            )
            self._abort_if_unique_id_configured()
            try:
                await _async_validate_connection(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_SLAVE_ID_BASIC],
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="SAX Power Home", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
