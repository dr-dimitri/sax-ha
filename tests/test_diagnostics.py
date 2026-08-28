"""Tests für die Diagnosefunktion (diagnostics.py, siehe anforderung.yaml,
REQ-DIAGNOSTICS).

Baut Coordinator + Config Entry direkt zusammen (wie test_coordinator.py),
statt über einen echten Modbus-Server (test_integration_live.py) - die
Diagnosefunktion selbst enthält keine Modbus-Logik, sondern aggregiert nur
bereits vorhandene Coordinator-Properties.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.application.calibration import CalibrationState
from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    DATA_COORDINATOR,
    DOMAIN,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.diagnostics import (
    TO_REDACT,
    async_get_config_entry_diagnostics,
)


def _make_entry_with_coordinator(hass) -> tuple[MockConfigEntry, SaxPowerCoordinator]:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
    )
    coordinator.data = {"soc": 42, "storage_power_active": -500}

    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_entry_id",
        data={
            "host": "192.168.1.42",
            "port": 502,
            "slave_id_basic": 64,
            "slave_id_extended": 100,
        },
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}
    return entry, coordinator


async def test_diagnostics_redacts_host(hass) -> None:
    """Die IP-Adresse (CONF_HOST) ist die einzige potenziell
    identifizierende Information in entry.data und muss redigiert werden."""
    entry, _coordinator = _make_entry_with_coordinator(hass)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry_data"]["host"] == "**REDACTED**"
    assert "host" in TO_REDACT
    # Port ist kein Geheimnis und bleibt unverändert sichtbar.
    assert diagnostics["entry_data"]["port"] == 502


async def test_diagnostics_includes_coordinator_data_and_state(hass) -> None:
    """Diagnostics müssen sowohl die aktuellen Messwerte (coordinator.data)
    als auch den relevanten internen Zustand (Max-SOC-Sperre,
    zeitgesteuertes/netzdienliches Laden, SunSpec-Erreichbarkeit) enthalten
    - das ist der eigentliche Mehrwert gegenüber einem reinen
    Sensor-Snapshot für Support-/Bugreport-Zwecke."""
    entry, coordinator = _make_entry_with_coordinator(hass)
    await coordinator.async_set_max_soc(80)
    last_full = datetime(2026, 8, 24, 8, 0, tzinfo=UTC)
    coordinator._cell_calibration_state = CalibrationState(
        last_full,
        was_full=False,
    )
    coordinator._cell_calibration_active = True

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    # async_set_max_soc löst intern _async_apply_grid_charge_change aus, das
    # coordinator.data um timed_charge_active/grid_serving_active ergänzt -
    # hier interessieren nur die ursprünglich gesetzten Messwerte.
    assert diagnostics["coordinator_data"]["soc"] == 42
    assert diagnostics["coordinator_data"]["storage_power_active"] == -500
    assert diagnostics["state"]["max_soc"] == 80
    assert diagnostics["state"]["effective_max_soc"] == 100
    assert diagnostics["state"]["cell_calibration_active"] is True
    assert diagnostics["state"]["last_full_charge_at"] == last_full
    assert diagnostics["state"]["next_cell_calibration_at"] > last_full
    assert diagnostics["state"]["extended_available"] is True
    assert diagnostics["state"]["grid_charge_active"] is False
    assert diagnostics["state"]["sun_charge_active"] is False
    assert diagnostics["state"]["grid_serving_forecast_threshold_kwh"] == 0
    assert diagnostics["state"]["grid_serving_forecast_kwh"] is None
    assert diagnostics["state"]["grid_serving_forecast_allowed"] is True


async def test_diagnostics_includes_the_tariff_state(hass) -> None:
    """Der Diagnose-Download weist den Tarifzustand aus - inklusive des
    maschinenlesbaren Grundes, wenn kein Preis bestimmbar ist (siehe
    anforderung.yaml, REQ-ECONOMICS-TARIFFS)."""
    entry, coordinator = _make_entry_with_coordinator(hass)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["tariff"]["tariff_type"] == "disabled"
    assert diagnostics["tariff"]["quote_price_eur_kwh"] is None
    assert diagnostics["tariff"]["quote_unavailable_reason"] == "tariff_disabled"

    coordinator.options = {
        CONF_ECONOMICS_TARIFF_TYPE: "fixed",
        CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
        CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.3421,
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["tariff"]["feed_in_price_eur_kwh"] == 0.0786
    assert diagnostics["tariff"]["quote_price_eur_kwh"] == 0.3421
    assert diagnostics["tariff"]["quote_source"] == "fixed"
    assert diagnostics["tariff"]["quote_unavailable_reason"] is None
    # Ein Fest-/Zeitfenstertarif hat keine Sensor-Quelle.
    assert diagnostics["tariff"]["price_sensor_entity_id"] is None


async def test_diagnostics_includes_the_dynamic_price_sensor_entity_id(hass) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: eine Entity-ID ist keine identifizierende
    Information (anders als Host/Seriennummer) und wird deshalb
    unredigiert gezeigt."""
    entry, coordinator = _make_entry_with_coordinator(hass)
    coordinator.options = {
        CONF_ECONOMICS_TARIFF_TYPE: "dynamic",
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        "price_sensor": "sensor.strompreis",
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["tariff"]["price_sensor_entity_id"] == "sensor.strompreis"


async def test_diagnostics_includes_the_economics_balance(hass) -> None:
    """Der Diagnose-Download weist den internen Bilanzzustand aus -
    Zeitstempel und ungerundete Rohsummen, die in coordinator_data nicht
    stehen (siehe anforderung.yaml, REQ-ECONOMICS-ACCOUNTING)."""
    entry, coordinator = _make_entry_with_coordinator(hass)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["economics"]["started_at"] is None
    assert diagnostics["economics"]["grid_charge_cost_eur"] is None

    started_at = datetime(2026, 8, 26, 8, 0, tzinfo=UTC)
    coordinator._economics_started_at = started_at
    coordinator._economics_grid_charge_cost_eur = 1.23456

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["economics"]["started_at"] == started_at.isoformat()
    assert diagnostics["economics"]["grid_charge_cost_eur"] == 1.23456


async def test_diagnostics_includes_the_energy_origin_start(hass) -> None:
    """REQ-ENERGY-ORIGIN: Ohne den Startzeitpunkt der Herkunftszählung ist
    aus einem Download nicht zu entscheiden, ob eine Differenz zwischen
    Herkunftszählern und Geldbilanz ein Rechenfehler ist oder nur zwei
    verschieden alte Zählzeiträume."""
    entry, coordinator = _make_entry_with_coordinator(hass)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["energy"]["origin_accounting_started_at"] is None
    assert diagnostics["energy"]["pv_charged_kwh"] is None

    started_at = datetime(2026, 8, 26, 8, 0, tzinfo=UTC)
    coordinator._origin_accounting_started_at = started_at
    coordinator._energy_pv_charged_kwh = 2.4421234

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["energy"]["origin_accounting_started_at"] == (
        started_at.isoformat()
    )
    assert diagnostics["energy"]["pv_charged_kwh"] == 2.4421234


async def test_diagnostics_includes_the_economics_data_quality_state(hass) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: Status, Store-Zustand und
    Preisabdeckungszähler landen ebenfalls im Diagnose-Download."""
    entry, coordinator = _make_entry_with_coordinator(hass)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["economics"]["store_write_blocked"] is False
    assert diagnostics["economics"]["store_minor_version"] >= 3
    assert diagnostics["economics"]["priced_charge_kwh"] is None
    assert diagnostics["economics"]["price_unavailable"] is False

    coordinator._economics_store_write_blocked = True

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["economics"]["store_write_blocked"] is True
