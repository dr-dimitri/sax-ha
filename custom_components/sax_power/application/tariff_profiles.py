"""Preserve inactive dashboard tariff profiles without changing stored price units."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from ..const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_DASHBOARD_TARIFF_PROFILES,
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_PRICE_ATTRIBUTE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    ECONOMICS_OPTION_KEYS,
    ECONOMICS_TOU_WINDOW_KEYS,
)
from ..domain.tariff import TariffType

TARIFF_PROFILE_KEYS: dict[str, tuple[str, ...]] = {
    TariffType.TIME_OF_USE.value: (
        CONF_ECONOMICS_FEED_IN_PRICE,
        CONF_ECONOMICS_TOU_BASE_PRICE,
        *ECONOMICS_TOU_WINDOW_KEYS,
        CONF_PV_FORECAST_SENSOR,
        CONF_BRIDGE_CHARGE_ENABLED,
    ),
    TariffType.DYNAMIC.value: (
        CONF_ECONOMICS_FEED_IN_PRICE,
        CONF_PRICE_SENSOR,
        CONF_PRICE_ATTRIBUTE,
        CONF_PRICE_UNIT,
        CONF_PV_FORECAST_SENSOR,
        CONF_PV_FORECAST_FACTOR,
    ),
}


def bridge_configuration_error(options: Mapping[str, Any]) -> str | None:
    """REQ-BRIDGE-CHARGE: an enabled bridge must retain its configured source."""
    if options.get(CONF_BRIDGE_CHARGE_ENABLED) is not True:
        return None
    if not options.get(CONF_PV_FORECAST_SENSOR):
        return "bridge_pv_start_required"
    if options.get(CONF_ECONOMICS_TARIFF_TYPE) != TariffType.TIME_OF_USE:
        return "bridge_tariff_required"
    return None


def tariff_profiles_from_options(
    options: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Active flat options always supersede their saved inactive snapshot."""
    stored = options.get(CONF_DASHBOARD_TARIFF_PROFILES)
    profiles: dict[str, dict[str, Any]] = {}
    for tariff_type, keys in TARIFF_PROFILE_KEYS.items():
        source = stored.get(tariff_type, {}) if isinstance(stored, Mapping) else {}
        profiles[tariff_type] = {
            key: deepcopy(source[key])
            for key in keys
            if isinstance(source, Mapping) and key in source
        }
    active = options.get(CONF_ECONOMICS_TARIFF_TYPE)
    if active in TARIFF_PROFILE_KEYS:
        profiles[active] = {
            key: deepcopy(options[key])
            for key in TARIFF_PROFILE_KEYS[active]
            if key in options
        }
    if not profiles[TariffType.DYNAMIC.value]:
        # Legacy price sources can exist alongside any economics tariff type.
        profiles[TariffType.DYNAMIC.value] = {
            key: deepcopy(options[key])
            for key in TARIFF_PROFILE_KEYS[TariffType.DYNAMIC.value]
            if key != CONF_ECONOMICS_FEED_IN_PRICE and key in options
        }
    return profiles


def options_for_tariff(
    options: Mapping[str, Any],
    tariff_type: str,
    profile: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Activate one preserved profile while retaining unrelated integration options."""
    profiles = tariff_profiles_from_options(options)
    if tariff_type not in TARIFF_PROFILE_KEYS:
        raise ValueError("Unsupported dashboard tariff")
    if profile is not None:
        profiles[tariff_type] = {
            key: deepcopy(profile[key])
            for key in TARIFF_PROFILE_KEYS[tariff_type]
            if key in profile
        }
    managed = {
        *ECONOMICS_OPTION_KEYS,
        *(key for keys in TARIFF_PROFILE_KEYS.values() for key in keys),
    }
    result = {key: value for key, value in options.items() if key not in managed}
    result.update(profiles[tariff_type])
    result[CONF_ECONOMICS_TARIFF_TYPE] = tariff_type
    result[CONF_DASHBOARD_TARIFF_PROFILES] = profiles
    if tariff_type != TariffType.TIME_OF_USE:
        result[CONF_BRIDGE_CHARGE_ENABLED] = False
    return result
