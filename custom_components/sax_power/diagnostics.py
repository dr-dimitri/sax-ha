"""Read-only support snapshot for REQ-DIAGNOSTICS."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import asdict
from datetime import date, datetime
from datetime import time as dt_time
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_ECONOMICS_INVESTMENT_COST,
    CONF_ECONOMICS_PRIOR_RESULT,
    CONF_GRID_SERVING_PV_FORECAST_SENSOR,
    CONF_PRICE_ATTRIBUTE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID_BASIC,
    CONF_SLAVE_ID_EXTENDED,
    DATA_COORDINATOR,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ECONOMICS_OPTION_KEYS,
)
from .coordinator import SaxPowerCoordinator
from .price_optimizer import ATTRIBUTE_GROUPS

TO_REDACT = {CONF_HOST}
_OPTION_KEYS = (
    *ECONOMICS_OPTION_KEYS,
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_PRICE_SENSOR,
    CONF_PRICE_ATTRIBUTE,
    CONF_PRICE_UNIT,
    CONF_PV_FORECAST_SENSOR,
    CONF_PV_FORECAST_FACTOR,
    CONF_GRID_SERVING_PV_FORECAST_SENSOR,
)


def _json_value(value: Any) -> Any:
    """Keep missing/invalid settings distinguishable in a detached JSON snapshot."""
    if isinstance(value, datetime | date | dt_time):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, set | frozenset):
        return [_json_value(item) for item in sorted(value)]
    if isinstance(value, list | tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def _source_state(
    hass: HomeAssistant, entity_id: str | None, attributes: tuple[str, ...] = ()
) -> dict[str, Any]:
    state = hass.states.get(entity_id) if isinstance(entity_id, str) else None
    return {
        "entity_id": entity_id,
        "state": state.state if state is not None else None,
        "available": state is not None
        and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, ""),
        "unit_of_measurement": (
            state.attributes.get("unit_of_measurement") if state is not None else None
        ),
        "last_updated": state.last_updated if state is not None else None,
        "last_changed": state.last_changed if state is not None else None,
        "attributes": (
            {
                key: state.attributes[key]
                for key in attributes
                if key in state.attributes
            }
            if state is not None
            else {}
        ),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Export effective settings and existing runtime evidence without device I/O."""
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    planner = coordinator.price_planner
    price_attribute = planner.price_attribute
    price_attributes = tuple(key for group in ATTRIBUTE_GROUPS for key in group)
    if price_attribute:
        price_attributes = (
            (price_attribute,) if isinstance(price_attribute, str) else ()
        )
    tariff = coordinator.tariff_provider.diagnostics
    # REQ-DIAGNOSTICS: parsed windows alone hide malformed input; inactive
    # dashboard profiles and legacy entry.data settings do not control charging.
    tariff["configuration"] = {
        key: coordinator.options[key]
        for key in _OPTION_KEYS
        if key in coordinator.options
    }
    tariff["price_unit"] = planner.price_unit
    tariff["price_attribute"] = planner.price_attribute
    tariff["pv_forecast_factor"] = planner.pv_factor
    economics = {
        key: value
        for key, value in coordinator.economics_diagnostics.items()
        if key != "day_results"
    }
    economics["configuration"] = {
        key: coordinator.options[key]
        for key in (CONF_ECONOMICS_INVESTMENT_COST, CONF_ECONOMICS_PRIOR_RESULT)
        if key in coordinator.options
    }
    return _json_value(
        {
            "schema_version": 2,
            "captured_at": dt_util.utcnow(),
            "timezone": hass.config.time_zone,
            "connection": async_redact_data(
                {
                    CONF_HOST: entry.data.get(CONF_HOST),
                    CONF_PORT: entry.data.get(CONF_PORT, DEFAULT_PORT),
                    CONF_SCAN_INTERVAL: entry.data.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                    CONF_SLAVE_ID_BASIC: coordinator.slave_id,
                    CONF_SLAVE_ID_EXTENDED: coordinator.slave_id_extended,
                },
                TO_REDACT,
            ),
            "control_config": asdict(coordinator.control_config()),
            "coordinator_data": {
                key: value
                for key, value in (coordinator.data or {}).items()
                if key != "sun_serial_number"
            },
            "state": {
                "control_config_status": coordinator.control_config_status,
                "control_bootstrap_pending": coordinator.control_bootstrap_pending,
                "control_config_migration_pending": (
                    coordinator.control_config_migration_pending
                ),
                "effective_max_soc": coordinator.effective_max_soc,
                "effective_timed_charge_max_soc": (
                    coordinator.effective_timed_charge_max_soc
                ),
                "max_soc_clamped": coordinator.max_soc_clamped,
                "cell_calibration_active": coordinator.cell_calibration_active,
                "last_full_charge_at": coordinator.last_full_charge_at,
                "next_cell_calibration_at": coordinator.next_cell_calibration_at,
                "grid_charge_active": coordinator.grid_charge_active,
                "sun_charge_active": coordinator.sun_charge_active,
                "extended_available": coordinator.extended_available,
                "timed_charge_uses_tariff": coordinator.timed_charge_uses_tariff,
                "bridge_charge_enabled": coordinator.bridge_charge_enabled,
                "grid_serving_forecast_threshold_kwh": (
                    coordinator.grid_serving_forecast_threshold_kwh
                ),
                "grid_serving_forecast_kwh": coordinator.grid_serving_forecast_kwh,
                "grid_serving_forecast_allowed": (
                    coordinator.grid_serving_forecast_allowed
                ),
                "price_charge_hours": coordinator.price_charge_hours,
            },
            "charge_control": coordinator.charge_control_diagnostics,
            "price_plan": planner.plan_attributes,
            "tariff": tariff,
            "source_states": {
                "price": _source_state(hass, planner.price_entity_id, price_attributes),
                "pv_forecast": _source_state(hass, planner.pv_forecast_entity_id),
                "grid_serving_pv_forecast": _source_state(
                    hass, planner.grid_serving_pv_forecast_entity_id
                ),
            },
            "energy": coordinator.energy_diagnostics,
            "economics": economics,
        }
    )
