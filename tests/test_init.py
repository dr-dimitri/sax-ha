"""Tests for custom_components/sax_power/__init__.py (Setup/Options-Update)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power import async_setup_entry, async_update_options
from custom_components.sax_power.const import (
    CONF_PRICE_SENSOR,
    DATA_COORDINATOR,
    DOMAIN,
)

VALID_INPUT = {
    "host": "192.168.1.50",
    "port": 502,
    "slave_id_basic": 64,
    "slave_id_extended": 100,
    "scan_interval": 10,
}


async def test_async_update_options_applies_live_without_reload(hass) -> None:
    """Regressionstest: Eine Options-Flow-Änderung (Strompreis-/PV-Prognose-
    Sensor) darf den Config Entry NICHT mehr neu laden (siehe
    anforderung.yaml, REQ-GRID-SERVING-CHARGE, ursprünglich gemeldeter Bug) -
    ein Reload würde SaxPowerCoordinator.async_shutdown auslösen, das über
    async_stop_sun_charge Register 40051 aktiv auf SmartMeter-Nullregelung
    zurücksetzt, selbst wenn netzdienliches Laden gerade aktiv den Sollwert
    bei 0 % hält. Stattdessen übernimmt async_update_options die neuen
    Optionen direkt in den laufenden Coordinator, setzt den Planner neu auf
    und wendet die neue Prognose sofort an, ohne den Coordinator selbst (und
    damit eine laufende Lade-Automatik) neu zu starten."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        options={},
        unique_id="192.168.1.50:502",
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.options = {}
    coordinator.price_planner.async_setup = MagicMock()
    coordinator.async_apply_price_plan = AsyncMock()
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {DATA_COORDINATOR: coordinator}

    hass.config_entries.async_reload = AsyncMock(
        side_effect=AssertionError(
            "async_update_options darf den Config Entry nicht mehr neu laden"
        )
    )

    hass.config_entries.async_update_entry(
        entry, options={CONF_PRICE_SENSOR: "sensor.strompreis"}
    )
    await async_update_options(hass, entry)

    hass.config_entries.async_reload.assert_not_called()
    assert coordinator.options == {CONF_PRICE_SENSOR: "sensor.strompreis"}
    coordinator.price_planner.async_setup.assert_called_once()
    coordinator.async_apply_price_plan.assert_awaited_once()


async def test_async_update_options_noop_without_loaded_entry(hass) -> None:
    """Feuert der Update-Listener, bevor/nachdem der Coordinator in
    hass.data registriert ist (z. B. während des Entladens), passiert
    nichts - kein KeyError, kein Reload-Versuch."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        options={CONF_PRICE_SENSOR: "sensor.strompreis"},
        unique_id="192.168.1.50:502",
    )
    entry.add_to_hass(hass)

    await async_update_options(hass, entry)


async def test_setup_loads_persisted_state_before_first_refresh(hass) -> None:
    """Persistierte Kalibrierungs-, Energie- und Ladeeinstellungszustände
    gehen dem Poll voran; die eine Ladeentscheidung folgt erst nach dem
    Plattform-Setup (siehe anforderung.yaml, REQ-CONTROL-CONFIG-BOOTSTRAP)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        options={},
        unique_id="192.168.1.50:502",
    )
    entry.add_to_hass(hass)
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    order: list[str] = []
    hass.config_entries.async_forward_entry_setups = AsyncMock(
        side_effect=lambda *args, **kwargs: order.append("platforms")
    )

    with (
        patch(
            "custom_components.sax_power.AsyncModbusTcpClient",
            return_value=client,
        ),
        patch(
            "custom_components.sax_power.SaxPowerCoordinator."
            "async_load_calibration_state",
            new=AsyncMock(side_effect=lambda: order.append("calibration")),
        ),
        patch(
            "custom_components.sax_power.SaxPowerCoordinator."
            "async_load_energy_state",
            new=AsyncMock(side_effect=lambda: order.append("energy")),
        ),
        patch(
            "custom_components.sax_power.SaxPowerCoordinator."
            "async_load_control_state",
            new=AsyncMock(side_effect=lambda: order.append("control")),
        ),
        patch(
            "custom_components.sax_power.SaxPowerCoordinator."
            "async_config_entry_first_refresh",
            new=AsyncMock(side_effect=lambda: order.append("refresh")),
        ),
        patch(
            "custom_components.sax_power.SaxPowerCoordinator." "async_finish_bootstrap",
            new=AsyncMock(side_effect=lambda: order.append("bootstrap_done")),
        ),
        patch("custom_components.sax_power.coordinator.SaxPricePlanner.async_setup"),
    ):
        assert await async_setup_entry(hass, entry) is True

    assert order == [
        "calibration",
        "energy",
        "control",
        "refresh",
        "platforms",
        "bootstrap_done",
    ]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    await coordinator.async_shutdown()
