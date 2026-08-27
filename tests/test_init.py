"""Tests for custom_components/sax_power/__init__.py (Setup/Options-Update)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power import (
    _async_register_services,
    _async_remove_stale_entities,
    async_setup_entry,
    async_update_options,
)
from custom_components.sax_power.const import (
    ATTR_CONFIRM,
    ATTR_DEVICE_ID,
    ATTR_POWER,
    ATTR_REASON,
    CONF_PRICE_SENSOR,
    DATA_COORDINATOR,
    DOMAIN,
    MAX_SETPOINT_POWER,
    MIN_SETPOINT_POWER,
    SERVICE_RESTART_ECONOMICS_ACCOUNTING,
    SERVICE_START_GRID_CHARGE,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

VALID_INPUT = {
    "host": "192.168.1.50",
    "port": 502,
    "slave_id_basic": 64,
    "slave_id_extended": 100,
    "scan_interval": 10,
}


@pytest.mark.parametrize(
    "power",
    [True, 1.5, "ungültig", MIN_SETPOINT_POWER - 1, 0, 1, MAX_SETPOINT_POWER + 1],
)
async def test_start_grid_charge_service_translates_unsafe_power(
    hass, power: object
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Unsichere Schemawerte erreichen die
    Coordinator-Validierung und werden als übersetzbarer Servicefehler
    abgelehnt, bevor ein Geräte-Write stattfinden kann."""
    client = MagicMock()
    client.connected = True
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
    )
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}

    with patch(
        "custom_components.sax_power._coordinator_for_device",
        return_value=coordinator,
    ):
        _async_register_services(hass)
        with pytest.raises(ServiceValidationError) as raised:
            await hass.services.async_call(
                DOMAIN,
                SERVICE_START_GRID_CHARGE,
                {ATTR_DEVICE_ID: "device", ATTR_POWER: power},
                blocking=True,
            )

    assert raised.value.translation_domain == DOMAIN
    assert raised.value.translation_key == "invalid_grid_charge_power"
    client.write_register.assert_not_awaited()


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
    coordinator.tariff_provider.async_setup = MagicMock()
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
    # Auch die Tarifkonfiguration der Wirtschaftlichkeitsauswertung wird
    # live übernommen (REQ-ECONOMICS-TARIFFS): async_setup registriert die
    # Zustandsbeobachter des dynamischen Preis-Sensors idempotent neu.
    coordinator.tariff_provider.async_setup.assert_called_once()
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


# -- restart_economics_accounting (REQ-ECONOMICS-OBSERVABILITY) -------------
async def test_restart_economics_accounting_service_requires_confirm_true(
    hass,
) -> None:
    coordinator = MagicMock()
    coordinator.async_restart_economics_accounting = AsyncMock()

    with patch(
        "custom_components.sax_power._coordinator_for_device",
        return_value=coordinator,
    ):
        _async_register_services(hass)
        with pytest.raises(vol.Invalid):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RESTART_ECONOMICS_ACCOUNTING,
                {ATTR_DEVICE_ID: "device", ATTR_CONFIRM: False},
                blocking=True,
            )

    coordinator.async_restart_economics_accounting.assert_not_awaited()


async def test_restart_economics_accounting_service_delegates_to_coordinator(
    hass,
) -> None:
    coordinator = MagicMock()
    coordinator.async_restart_economics_accounting = AsyncMock()

    with patch(
        "custom_components.sax_power._coordinator_for_device",
        return_value=coordinator,
    ):
        _async_register_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RESTART_ECONOMICS_ACCOUNTING,
            {
                ATTR_DEVICE_ID: "device",
                ATTR_CONFIRM: True,
                ATTR_REASON: "Tarifwechsel",
            },
            blocking=True,
        )

    coordinator.async_restart_economics_accounting.assert_awaited_once_with(
        reason="Tarifwechsel"
    )


async def test_restart_economics_accounting_service_reason_is_optional(hass) -> None:
    coordinator = MagicMock()
    coordinator.async_restart_economics_accounting = AsyncMock()

    with patch(
        "custom_components.sax_power._coordinator_for_device",
        return_value=coordinator,
    ):
        _async_register_services(hass)
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RESTART_ECONOMICS_ACCOUNTING,
            {ATTR_DEVICE_ID: "device", ATTR_CONFIRM: True},
            blocking=True,
        )

    coordinator.async_restart_economics_accounting.assert_awaited_once_with(reason=None)


# --------------------------------------------------------------------------
# Entfallene Entities früherer Versionen (REQ-ENERGY-ORIGIN)
# --------------------------------------------------------------------------
async def test_removed_origin_entities_are_purged_from_the_registry(hass) -> None:
    """Die beiden mit der Herkunftskategorie entfallenen Sensoren räumt
    Home Assistant nicht selbst weg - sie blieben sonst dauerhaft als
    "nicht verfügbar" in der Registry und damit in jedem Dashboard und
    jeder Automation stehen, die sie verwendet."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, entry_id="entry")
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    stale = [
        registry.async_get_or_create(
            "sensor",
            DOMAIN,
            f"{entry.entry_id}_{suffix}",
            config_entry=entry,
        ).entity_id
        for suffix in ("energy_charged_origin_unknown", "energy_origin_coverage")
    ]
    kept = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{entry.entry_id}_energy_charged_from_grid",
        config_entry=entry,
    ).entity_id

    _async_remove_stale_entities(hass, entry)

    for entity_id in stale:
        assert registry.async_get(entity_id) is None
    assert registry.async_get(kept) is not None


async def test_removing_stale_entities_is_a_noop_without_them(hass) -> None:
    """Der Regelfall - eine frische Installation, die diese Entities nie
    hatte - darf dabei nichts anfassen."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, entry_id="fresh")
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    before = set(registry.entities)

    _async_remove_stale_entities(hass, entry)

    assert set(registry.entities) == before


async def test_update_options_is_a_noop_when_only_entry_data_changed(hass) -> None:
    """async_update_entry löst diesen Listener auch bei einer reinen
    entry.data-Änderung aus (etwa beim Wegklicken des Dashboard-Hinweises).
    Ohne unveränderte Options darf dabei weder der diagnostische
    Tarifrevisions-Zeitstempel zurückgesetzt noch ein Modbus-Schreibpfad
    angestoßen werden."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=VALID_INPUT, options={CONF_PRICE_SENSOR: "sensor.preis"}
    )
    entry.add_to_hass(hass)
    coordinator = MagicMock()
    coordinator.options = dict(entry.options)
    coordinator.async_apply_price_plan = AsyncMock()
    hass.data[DOMAIN] = {entry.entry_id: {DATA_COORDINATOR: coordinator}}

    await async_update_options(hass, entry)

    coordinator.notify_tariff_revision.assert_not_called()
    coordinator.async_apply_price_plan.assert_not_called()
    coordinator.price_planner.async_setup.assert_not_called()

    # Gegenprobe: Eine echte Options-Änderung wird weiterhin angewendet.
    hass.config_entries.async_update_entry(
        entry, options={CONF_PRICE_SENSOR: "sensor.anderer_preis"}
    )
    await async_update_options(hass, entry)

    coordinator.notify_tariff_revision.assert_called_once()
    coordinator.async_apply_price_plan.assert_awaited_once()
