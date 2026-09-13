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
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er

from .application.economics import parse_price, parse_time, tariff_config_from_options
from .application.tariff_profiles import (
    TARIFF_PROFILE_KEYS,
    options_for_tariff,
    tariff_profiles_from_options,
)
from .const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_DASHBOARD_TARIFF_PROFILES,
    CONF_ECONOMICS_FEED_IN_PRICE,
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
    DATA_COORDINATOR,
    DEFAULT_PRICE_UNIT,
    DEFAULT_PV_FORECAST_FACTOR,
    DOMAIN,
    ECONOMICS_OPTION_KEYS,
    ECONOMICS_PRICE_DECIMALS,
    ECONOMICS_TOU_WINDOW_KEYS,
    MAX_ECONOMICS_FEED_IN_PRICE,
    MAX_ECONOMICS_IMPORT_PRICE,
    MIN_ECONOMICS_FEED_IN_PRICE,
    MIN_ECONOMICS_IMPORT_PRICE,
    PRICE_UNITS,
)
from .dashboard_price_series import price_series
from .domain.price_units import unit_factor
from .domain.tariff import (
    DailyPriceWindow,
    TariffType,
    find_overlapping_window,
    validate_tariff,
)

GET_COMMAND = "sax_power/dashboard/tariff/get"
SAVE_COMMAND = "sax_power/dashboard/tariff/save"
CONFIGURE_COMMAND = "sax_power/dashboard/tariff/configure"
SERIES_COMMAND = "sax_power/dashboard/tariff/series"
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
    can_configure: bool
    automation_enabled: bool | None
    profiles: dict[str, dict[str, Any]]


@callback
def async_register_dashboard_tariff(hass: HomeAssistant) -> None:
    """Registriere Lesen und atomisches Speichern einmalig."""
    for name, command in (
        (GET_COMMAND, websocket_get_tariff),
        (SAVE_COMMAND, websocket_save_tariff),
        (CONFIGURE_COMMAND, websocket_configure_tariff),
        (SERIES_COMMAND, websocket_tariff_series),
    ):
        if name not in hass.data.get(websocket_api.DOMAIN, {}):
            websocket_api.async_register_command(hass, command)


def _revision(entry: ConfigEntry) -> str:
    """Nur Tarifänderungen erzeugen Konflikte; andere Options bleiben erhalten."""
    keys = {
        CONF_DASHBOARD_TARIFF_PROFILES,
        *ECONOMICS_OPTION_KEYS,
        *(key for group in TARIFF_PROFILE_KEYS.values() for key in group),
    }
    profile = {key: entry.options[key] for key in keys if key in entry.options}
    return hashlib.sha256(
        json.dumps(profile, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _cent(price: float | None) -> float | None:
    if price is None or not math.isfinite(price * 100):
        return None
    return round(price * 100, ECONOMICS_PRICE_DECIMALS - 2)


def _result(
    hass: HomeAssistant, entry: ConfigEntry, connection: websocket_api.ActiveConnection
) -> _Tariff:
    config = tariff_config_from_options(entry.options)
    return {
        "can_configure": connection.user.is_active and connection.user.is_admin,
        "automation_enabled": _automation_enabled(hass, entry),
        "profiles": _dashboard_profiles(entry),
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


def _automation_enabled(hass: HomeAssistant, entry: ConfigEntry) -> bool | None:
    coordinator = (
        hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get(DATA_COORDINATOR)
    )
    if coordinator is None:
        return None
    tariff_type = entry.options.get(CONF_ECONOMICS_TARIFF_TYPE)
    if tariff_type == TariffType.TIME_OF_USE:
        return bool(coordinator.timed_charge_enabled)
    if tariff_type == TariffType.DYNAMIC:
        return bool(coordinator.price_charge_enabled)
    return False


def _dashboard_profiles(entry: ConfigEntry) -> dict[str, dict[str, Any]]:
    profiles = tariff_profiles_from_options(entry.options)
    tou = profiles[TariffType.TIME_OF_USE]
    config = tariff_config_from_options(
        {**tou, CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE}
    )
    dynamic = profiles[TariffType.DYNAMIC]
    return {
        "time_of_use": {
            "base_price_ct_kwh": _cent(config.tou_base_price_eur_kwh),
            "feed_in_price_ct_kwh": _cent(config.feed_in_price_eur_kwh),
            "windows": [
                {
                    "start": w.start.isoformat(),
                    "end": w.end.isoformat(),
                    "price_ct_kwh": price,
                }
                for w in config.windows
                if (price := _cent(w.price_eur_kwh)) is not None
            ],
            "pv_sensor": tou.get(CONF_PV_FORECAST_SENSOR) or None,
        },
        "dynamic": {
            "feed_in_price_ct_kwh": _cent(
                parse_price(dynamic.get(CONF_ECONOMICS_FEED_IN_PRICE))
            ),
            "price_sensor": dynamic.get(CONF_PRICE_SENSOR) or None,
            "price_attribute": dynamic.get(CONF_PRICE_ATTRIBUTE) or None,
            "price_unit": dynamic.get(CONF_PRICE_UNIT, DEFAULT_PRICE_UNIT),
            "pv_sensor": dynamic.get(CONF_PV_FORECAST_SENSOR) or None,
            "pv_factor": dynamic.get(
                CONF_PV_FORECAST_FACTOR, DEFAULT_PV_FORECAST_FACTOR
            ),
        },
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
        connection.send_result(msg["id"], _result(hass, entry, connection))


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
    connection.send_result(msg["id"], _result(hass, entry, connection))


def _sensor(hass: HomeAssistant, value: Any, *, optional: bool = False) -> str | None:
    if optional and value in (None, ""):
        return None
    if not isinstance(value, str) or not re.fullmatch(r"sensor\.[a-z0-9_]+", value):
        raise ValueError("Select a sensor entity")
    if hass.states.get(value) is None and er.async_get(hass).async_get(value) is None:
        raise ValueError("The sensor entity does not exist")
    return value


def _configuration_profile(
    hass: HomeAssistant, entry: ConfigEntry, tariff_type: str, submitted: Any
) -> dict[str, Any]:
    if not isinstance(submitted, dict):
        raise ValueError("A complete profile is required")
    if tariff_type == TariffType.TIME_OF_USE:
        if set(submitted) != {
            "base_price_ct_kwh",
            "feed_in_price_ct_kwh",
            "windows",
            "pv_sensor",
        }:
            raise ValueError("A complete time-of-use profile is required")
        profile = _profile(submitted)
        profile[CONF_PV_FORECAST_SENSOR] = _sensor(
            hass, submitted["pv_sensor"], optional=True
        )
        previous = tariff_profiles_from_options(entry.options)[TariffType.TIME_OF_USE]
        profile[CONF_BRIDGE_CHARGE_ENABLED] = previous.get(
            CONF_BRIDGE_CHARGE_ENABLED, False
        )
        return profile
    if set(submitted) != {
        "feed_in_price_ct_kwh",
        "price_sensor",
        "price_attribute",
        "price_unit",
        "pv_sensor",
        "pv_factor",
    }:
        raise ValueError("A complete dynamic profile is required")
    sensor = _sensor(hass, submitted["price_sensor"])
    unit = submitted["price_unit"]
    if not isinstance(unit, str) or unit not in PRICE_UNITS:
        raise ValueError("Unsupported price unit")
    sensor_state = hass.states.get(sensor)
    if (
        sensor_state is not None
        and unit_factor(unit, sensor_state.attributes.get("unit_of_measurement"))
        is None
    ):
        raise ValueError("The sensor does not report a supported price unit")
    attribute = submitted["price_attribute"]
    if attribute is not None and (
        not isinstance(attribute, str) or len(attribute) > 128
    ):
        raise ValueError("Invalid forecast attribute")
    factor = submitted["pv_factor"]
    if (
        isinstance(factor, bool)
        or not isinstance(factor, (int, float))
        or not 0 <= factor <= 100
        or not float(factor).is_integer()
    ):
        raise ValueError("PV factor must be a whole percentage from 0 to 100")
    return {
        CONF_ECONOMICS_FEED_IN_PRICE: _price(
            submitted["feed_in_price_ct_kwh"],
            MIN_ECONOMICS_FEED_IN_PRICE,
            MAX_ECONOMICS_FEED_IN_PRICE,
        ),
        CONF_PRICE_SENSOR: sensor,
        CONF_PRICE_UNIT: unit,
        CONF_PRICE_ATTRIBUTE: (
            attribute.strip() or None if attribute is not None else None
        ),
        CONF_PV_FORECAST_SENSOR: _sensor(hass, submitted["pv_sensor"], optional=True),
        CONF_PV_FORECAST_FACTOR: int(factor),
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): CONFIGURE_COMMAND,
        vol.Required("entry_id"): _ENTRY_ID_SCHEMA,
        vol.Required("revision"): vol.All(str, vol.Length(min=1, max=128)),
        vol.Required("tariff_type"): vol.In(
            [TariffType.TIME_OF_USE.value, TariffType.DYNAMIC.value]
        ),
        vol.Optional("profile"): object,
        vol.Optional("automation_enabled"): bool,
    }
)
@websocket_api.async_response
async def websocket_configure_tariff(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Apply a complete tariff and its exclusive activation through one control hook."""
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
    expected_options = dict(entry.options)
    enabled = msg.get("automation_enabled")
    try:
        profile = (
            _configuration_profile(hass, entry, msg["tariff_type"], msg["profile"])
            if "profile" in msg
            else None
        )
        options = options_for_tariff(entry.options, msg["tariff_type"], profile)
        if enabled is True or enabled is None and _automation_enabled(hass, entry):
            if validate_tariff(tariff_config_from_options(options)) is not None:
                raise ValueError("Configure the tariff before enabling charging")
            if msg["tariff_type"] == TariffType.DYNAMIC and not options.get(
                CONF_PRICE_SENSOR
            ):
                raise ValueError("Select a price sensor before enabling charging")
    except (ValueError, OverflowError) as err:
        connection.send_error(msg["id"], "invalid_tariff", str(err))
        return
    coordinator = (
        hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get(DATA_COORDINATOR)
    )
    if coordinator is None:
        if enabled is not None:
            connection.send_error(
                msg["id"], "unavailable", "The integration is not loaded"
            )
            return
        hass.config_entries.async_update_entry(entry, options=options)
    else:
        try:
            await coordinator.async_apply_dashboard_tariff(
                options, enabled=enabled, expected_options=expected_options
            )
        except ServiceValidationError as err:
            code = (
                "conflict"
                if err.translation_key == "dashboard_tariff_conflict"
                else "invalid_tariff"
            )
            connection.send_error(msg["id"], code, str(err))
            return
        except HomeAssistantError as err:
            connection.send_error(msg["id"], "failed", str(err))
            return
    connection.send_result(msg["id"], _result(hass, entry, connection))


@websocket_api.websocket_command(
    {
        vol.Required("type"): SERIES_COMMAND,
        vol.Required("entry_id"): _ENTRY_ID_SCHEMA,
        vol.Required("day"): vol.In(["today", "tomorrow"]),
    }
)
@callback
def websocket_tariff_series(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Expose the full price source only to users who may read that source."""
    if (entry := _entry(hass, connection, msg)) is None:
        return
    source = entry.options.get(CONF_PRICE_SENSOR)
    if (
        entry.options.get(CONF_ECONOMICS_TARIFF_TYPE) == TariffType.DYNAMIC
        and source
        and not connection.user.permissions.check_entity(source, POLICY_READ)
    ):
        connection.send_error(msg["id"], "forbidden", "Price source access denied")
        return
    connection.send_result(
        msg["id"],
        price_series(
            hass, dict(entry.options), day=msg["day"], revision=_revision(entry)
        ),
    )
