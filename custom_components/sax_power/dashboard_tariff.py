"""Atomarer Dashboard-Tarifeditor für REQ-VUE-CHARGING/-SAVINGS."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, TypedDict

import voluptuous as vol
from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .application.economics import parse_price, parse_time, tariff_config_from_options
from .const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_ECONOMICS_WINDOW_END,
    CONF_ECONOMICS_WINDOW_PRICE,
    CONF_ECONOMICS_WINDOW_START,
    DOMAIN,
    ECONOMICS_OPTION_KEYS,
    ECONOMICS_PRICE_DECIMALS,
    ECONOMICS_TOU_WINDOW_KEYS,
    MAX_ECONOMICS_FEED_IN_PRICE,
    MAX_ECONOMICS_IMPORT_PRICE,
    MIN_ECONOMICS_FEED_IN_PRICE,
    MIN_ECONOMICS_IMPORT_PRICE,
)
from .domain.tariff import DailyPriceWindow, TariffType, find_overlapping_window

GET_COMMAND = "sax_power/dashboard/tariff/get"
SAVE_COMMAND = "sax_power/dashboard/tariff/save"
_ENTRY_ID_SCHEMA = vol.All(str, vol.Length(min=1, max=128))
_TIME_PATTERN = re.compile(r"\A\d{2}:\d{2}(?::\d{2})?\Z")


class _Window(TypedDict):
    start: str
    end: str
    price_ct_kwh: float


class _Tariff(TypedDict):
    tariff_type: str
    base_price_ct_kwh: float | None
    feed_in_price_ct_kwh: float | None
    windows: list[_Window]
    revision: str
    can_edit: bool


@callback
def async_register_dashboard_tariff(hass: HomeAssistant) -> None:
    """Registriere Lesen und atomisches Speichern einmalig."""
    for name, command in (
        (GET_COMMAND, websocket_get_tariff),
        (SAVE_COMMAND, websocket_save_tariff),
    ):
        if name not in hass.data.get(websocket_api.DOMAIN, {}):
            websocket_api.async_register_command(hass, command)


def _revision(entry: ConfigEntry) -> str:
    """Nur Tarifänderungen erzeugen Konflikte; andere Options bleiben erhalten."""
    profile = {
        key: entry.options[key] for key in ECONOMICS_OPTION_KEYS if key in entry.options
    }
    return hashlib.sha256(
        json.dumps(profile, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _cent(price: float | None) -> float | None:
    if price is None or not math.isfinite(price * 100):
        return None
    return round(price * 100, ECONOMICS_PRICE_DECIMALS - 2)


def _result(entry: ConfigEntry, connection: websocket_api.ActiveConnection) -> _Tariff:
    config = tariff_config_from_options(entry.options)
    return {
        "tariff_type": config.tariff_type.value,
        "base_price_ct_kwh": _cent(config.tou_base_price_eur_kwh),
        "feed_in_price_ct_kwh": _cent(config.feed_in_price_eur_kwh),
        "windows": [
            {
                "start": window.start.isoformat(),
                "end": window.end.isoformat(),
                "price_ct_kwh": price,
            }
            for window in config.windows
            if (price := _cent(window.price_eur_kwh)) is not None
        ],
        "revision": _revision(entry),
        "can_edit": connection.user.is_active
        and connection.user.is_admin
        and config.tariff_type is TariffType.TIME_OF_USE,
    }


def _read_allowed(
    hass: HomeAssistant, entry: ConfigEntry, connection: websocket_api.ActiveConnection
) -> bool:
    if not connection.user.is_active:
        return False
    # Ein Admin muss auch einen unvollständigen Tarif ohne geladene Sensoren
    # reparieren können. Leserechte sonst anhand der beiden Preisentities prüfen.
    if connection.user.is_admin:
        return True
    registry = er.async_get(hass)
    for key in ("economics_current_import_price", "economics_feed_in_price"):
        entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_{key}"
        )
        entity = registry.async_get(entity_id) if entity_id else None
        if (
            entity is None
            or entity.config_entry_id != entry.entry_id
            or entity.disabled
            or not connection.user.permissions.check_entity(
                entity.entity_id, POLICY_READ
            )
        ):
            return False
    return True


def _entry(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> ConfigEntry | None:
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_found", "Entry not found")
        return None
    if not _read_allowed(hass, entry, connection):
        connection.send_error(msg["id"], "forbidden", "Tariff access denied")
        return None
    return entry


def _price(value: Any, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("A numeric cent price is required")
    try:
        price = parse_price(value)
    except OverflowError as err:
        raise ValueError("Price outside the allowed cent range") from err
    if price is None or not minimum * 100 <= price <= maximum * 100:
        raise ValueError("Price outside the allowed cent range")
    return round(price / 100, ECONOMICS_PRICE_DECIMALS)


def _profile(msg: dict[str, Any]) -> dict[str, Any]:
    profile: dict[str, Any] = {
        CONF_ECONOMICS_TOU_BASE_PRICE: _price(
            msg["base_price_ct_kwh"],
            MIN_ECONOMICS_IMPORT_PRICE,
            MAX_ECONOMICS_IMPORT_PRICE,
        ),
        CONF_ECONOMICS_FEED_IN_PRICE: _price(
            msg["feed_in_price_ct_kwh"],
            MIN_ECONOMICS_FEED_IN_PRICE,
            MAX_ECONOMICS_FEED_IN_PRICE,
        ),
    }
    groups = msg["windows"]
    if not isinstance(groups, list) or len(groups) > len(ECONOMICS_TOU_WINDOW_KEYS):
        raise ValueError("At most eight windows are allowed")
    windows: list[tuple[int, DailyPriceWindow]] = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict) or set(group) != {
            "start",
            "end",
            "price_ct_kwh",
        }:
            raise ValueError("Every window needs start, end and price")
        if any(
            not isinstance(group[key], str) or not _TIME_PATTERN.fullmatch(group[key])
            for key in ("start", "end")
        ):
            raise ValueError("Invalid local time")
        start, end = parse_time(group["start"]), parse_time(group["end"])
        if start is None or end is None or start == end:
            raise ValueError("The window must have distinct valid times")
        price = _price(
            group["price_ct_kwh"],
            MIN_ECONOMICS_IMPORT_PRICE,
            MAX_ECONOMICS_IMPORT_PRICE,
        )
        windows.append((index, DailyPriceWindow(start, end, price)))
        profile[ECONOMICS_TOU_WINDOW_KEYS[index]] = {
            CONF_ECONOMICS_WINDOW_START: start.isoformat(),
            CONF_ECONOMICS_WINDOW_END: end.isoformat(),
            CONF_ECONOMICS_WINDOW_PRICE: price,
        }
    if find_overlapping_window(windows) is not None:
        raise ValueError("Tariff windows must not overlap")
    return profile


@websocket_api.websocket_command(
    {vol.Required("type"): GET_COMMAND, vol.Required("entry_id"): _ENTRY_ID_SCHEMA}
)
@callback
def websocket_get_tariff(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Liefere das bearbeitbare Profil unabhängig vom Coordinator-Ladezustand."""
    if (entry := _entry(hass, connection, msg)) is not None:
        connection.send_result(msg["id"], _result(entry, connection))


@websocket_api.websocket_command(
    {
        vol.Required("type"): SAVE_COMMAND,
        vol.Required("entry_id"): _ENTRY_ID_SCHEMA,
        vol.Required("revision"): vol.All(str, vol.Length(min=1, max=128)),
        vol.Required("base_price_ct_kwh"): object,
        vol.Required("feed_in_price_ct_kwh"): object,
        vol.Required("windows"): object,
    }
)
@callback
def websocket_save_tariff(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Validiere das gesamte Profil, dann aktualisiere die Options ohne await-Lücke."""
    if (entry := _entry(hass, connection, msg)) is None:
        return
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "forbidden", "Administrator access required")
        return
    if msg["revision"] != _revision(entry):
        connection.send_error(
            msg["id"], "conflict", "The tariff has changed; reload it"
        )
        return
    if (
        tariff_config_from_options(entry.options).tariff_type
        is not TariffType.TIME_OF_USE
    ):
        connection.send_error(msg["id"], "invalid_tariff", "Select time_of_use first")
        return
    try:
        profile = _profile(msg)
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_tariff", str(err))
        return
    options = {
        key: value
        for key, value in entry.options.items()
        if key not in ECONOMICS_TOU_WINDOW_KEYS
    }
    options.update(profile)
    hass.config_entries.async_update_entry(entry, options=options)
    connection.send_result(msg["id"], _result(entry, connection))
