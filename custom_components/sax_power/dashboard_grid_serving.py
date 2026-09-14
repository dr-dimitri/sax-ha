"""Separate PV source editor for REQ-GRID-SERVING-CHARGE / REQ-VUE-CHARGING."""

from __future__ import annotations

import hashlib
import re
from typing import Any, TypedDict

import voluptuous as vol
from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import CONF_GRID_SERVING_PV_FORECAST_SENSOR, DOMAIN

GET_COMMAND = "sax_power/dashboard/grid_serving/get"
SAVE_COMMAND = "sax_power/dashboard/grid_serving/save"
_ENTRY_ID_SCHEMA = vol.All(str, vol.Length(min=1, max=128))


class _Source(TypedDict):
    pv_sensor: str | None
    revision: str
    can_edit: bool


@callback
def async_register_dashboard_grid_serving(hass: HomeAssistant) -> None:
    """Register the independent forecast configuration once."""
    for name, command in (
        (GET_COMMAND, websocket_get_source),
        (SAVE_COMMAND, websocket_save_source),
    ):
        if name not in hass.data.get(websocket_api.DOMAIN, {}):
            websocket_api.async_register_command(hass, command)


def _source(entry: ConfigEntry) -> str | None:
    return entry.options.get(CONF_GRID_SERVING_PV_FORECAST_SENSOR) or None


def _revision(entry: ConfigEntry) -> str:
    return hashlib.sha256((_source(entry) or "").encode()).hexdigest()


def _entry(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> ConfigEntry | None:
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_found", "Entry not found")
        return None
    allowed = connection.user.is_active
    if allowed and not connection.user.is_admin:
        registry = er.async_get(hass)
        entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_grid_serving_forecast"
        )
        entity = registry.async_get(entity_id) if entity_id else None
        allowed = bool(
            entity
            and entity.config_entry_id == entry.entry_id
            and not entity.disabled
            and connection.user.permissions.check_entity(entity.entity_id, POLICY_READ)
            and (
                not _source(entry)
                or connection.user.permissions.check_entity(_source(entry), POLICY_READ)
            )
        )
    if not allowed:
        connection.send_error(msg["id"], "forbidden", "Forecast access denied")
        return None
    return entry


def _result(entry: ConfigEntry, connection: websocket_api.ActiveConnection) -> _Source:
    return {
        "pv_sensor": _source(entry),
        "revision": _revision(entry),
        "can_edit": connection.user.is_active and connection.user.is_admin,
    }


@websocket_api.websocket_command(
    {vol.Required("type"): GET_COMMAND, vol.Required("entry_id"): _ENTRY_ID_SCHEMA}
)
@callback
def websocket_get_source(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Read the confirmed source independently of the active electricity tariff."""
    if (entry := _entry(hass, connection, msg)) is not None:
        connection.send_result(msg["id"], _result(entry, connection))


@websocket_api.websocket_command(
    {
        vol.Required("type"): SAVE_COMMAND,
        vol.Required("entry_id"): _ENTRY_ID_SCHEMA,
        vol.Required("revision"): vol.All(str, vol.Length(min=1, max=128)),
        vol.Required("pv_sensor"): vol.Any(None, str),
    }
)
@callback
def websocket_save_source(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Accept only the separate source; the existing options listener applies it."""
    if (entry := _entry(hass, connection, msg)) is None:
        return
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "forbidden", "Administrator access required")
        return
    if msg["revision"] != _revision(entry):
        connection.send_error(msg["id"], "conflict", "The forecast source has changed")
        return
    source = msg["pv_sensor"] or None
    if source is not None:
        if not re.fullmatch(r"sensor\.[a-z0-9_]+", source):
            connection.send_error(msg["id"], "invalid_sensor", "Select a sensor entity")
            return
        state = hass.states.get(source)
        registered = er.async_get(hass).async_get(source)
        if state is None and registered is None:
            connection.send_error(msg["id"], "invalid_sensor", "The sensor is missing")
            return
        if (
            registered is not None
            and registered.platform == DOMAIN
            and registered.unique_id == f"{entry.entry_id}_grid_serving_forecast"
        ):
            connection.send_error(
                msg["id"], "invalid_sensor", "Select the original forecast source"
            )
            return
        unit = (
            state.attributes.get("unit_of_measurement")
            if state is not None
            else registered.unit_of_measurement
        )
        if str(unit or "").strip().lower() not in ("wh", "kwh", "mwh"):
            connection.send_error(
                msg["id"], "invalid_unit", "Select an energy sensor in Wh, kWh or MWh"
            )
            return
    # REQ-VUE-ENTITY-BINDING: No await between revision check and persistence.
    # The existing options listener coalesces device work without delaying this ACK.
    options = {**entry.options, CONF_GRID_SERVING_PV_FORECAST_SENSOR: source}
    if dict(entry.options) != options:
        hass.config_entries.async_update_entry(entry, options=options)
    connection.send_result(msg["id"], _result(entry, connection))
