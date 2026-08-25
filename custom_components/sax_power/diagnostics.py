"""Diagnostics support for the SAX Power integration.

Siehe anforderung.yaml, REQ-DIAGNOSTICS. Home Assistant bietet den
Diagnose-Download über die Geräteseite automatisch an, sobald diese Datei
existiert - keine weitere Registrierung nötig.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import SaxPowerCoordinator

# IP-Adresse ist die einzige potenziell identifizierende Information in
# entry.data (lokales Modbus TCP ohne Cloud-Auth, siehe AGENTS.md "Security
# considerations") - Port/Slave-IDs sind keine Geheimnisse.
TO_REDACT = {CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: SaxPowerCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "entry_options": dict(entry.options),
        "coordinator_data": coordinator.data,
        "state": {
            # REQ-CONTROL-CONFIG-BOOTSTRAP: zeigt, woher die folgenden Werte
            # stammen (loaded/missing/failed) - und ob der Bootstrap
            # überhaupt abgeschlossen ist (sonst steuert die Integration
            # bewusst nicht).
            "control_config_status": coordinator.control_config_status,
            "control_bootstrap_pending": coordinator.control_bootstrap_pending,
            "max_soc": coordinator.max_soc,
            "effective_max_soc": coordinator.effective_max_soc,
            "max_soc_clamped": coordinator.max_soc_clamped,
            "cell_calibration_active": coordinator.cell_calibration_active,
            "last_full_charge_at": coordinator.last_full_charge_at,
            "next_cell_calibration_at": coordinator.next_cell_calibration_at,
            "grid_charge_active": coordinator.grid_charge_active,
            "sun_charge_active": coordinator.sun_charge_active,
            "extended_available": coordinator.extended_available,
            "timed_charge_enabled": coordinator.timed_charge_enabled,
            "timed_charge_active": (coordinator.data or {}).get("timed_charge_active"),
            "grid_serving_enabled": coordinator.grid_serving_enabled,
            "grid_serving_active": (coordinator.data or {}).get("grid_serving_active"),
            "grid_serving_window_active": coordinator.grid_serving_window_active,
            "grid_serving_forecast_threshold_kwh": (
                coordinator.grid_serving_forecast_threshold_kwh
            ),
            "grid_serving_forecast_kwh": coordinator.grid_serving_forecast_kwh,
            "grid_serving_forecast_allowed": coordinator.grid_serving_forecast_allowed,
            "price_charge_enabled": coordinator.price_charge_enabled,
            "price_charge_strategy": coordinator.price_charge_strategy,
            "price_charge_active": coordinator.price_charge_active,
            "price_charge_status": coordinator.price_charge_status,
            "price_charge_max_price": coordinator.price_charge_max_price,
            "price_charge_hours": coordinator.price_charge_hours_raw,
        },
        # Ladeplan inkl. der ausgewerteten Preis-/Prognosewerte - der
        # häufigste Grund für Rückfragen zum preisoptimierten Laden ist ein
        # Preis-Sensor, dessen Attributformat nicht erkannt wurde (siehe
        # price_optimizer.parse_price_slots).
        "price_plan": coordinator.price_planner.plan_attributes,
    }
