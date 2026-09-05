"""Tests for custom_components/sax_power/__init__.py (Setup/Options-Update)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power import (
    PLATFORMS,
    _async_register_services,
    _async_remove_stale_entities,
    async_setup_entry,
    async_unload_entry,
    async_update_options,
)
from custom_components.sax_power.const import (
    ATTR_CONFIRM,
    ATTR_DEVICE_ID,
    ATTR_POWER,
    ATTR_REASON,
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_PRICE_SENSOR,
    DATA_COORDINATOR,
    DOMAIN,
    MAX_SETPOINT_POWER,
    MIN_SETPOINT_POWER,
    SERVICE_RESTART_ECONOMICS_ACCOUNTING,
    SERVICE_START_GRID_CHARGE,
    SUN_IC_CONTROL_MODE_SETPOINT,
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
            "async_load_timed_discharge_state",
            new=AsyncMock(side_effect=lambda: order.append("timed_discharge")),
        ),
        patch(
            "custom_components.sax_power.coordinator.SaxPricePlanner."
            "async_load_cycle_state",
            new=AsyncMock(side_effect=lambda: order.append("price_cycle")),
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
        "timed_discharge",
        "price_cycle",
        "refresh",
        "platforms",
        "bootstrap_done",
    ]
    client.close.assert_not_called()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    assert await async_unload_entry(hass, entry) is True
    client.close.assert_called_once_with()


async def test_failed_first_refresh_closes_unpublished_resources(hass) -> None:
    """REQ-SETUP-ROLLBACK: Nach erfolgreichem TCP-Connect muss auch ein
    fehlgeschlagener erster Refresh Client und Coordinator genau einmal
    aufräumen, ohne den Coordinator in hass.data zu veröffentlichen."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, entry_id="entry")
    entry.add_to_hass(hass)
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.close = MagicMock()
    coordinator = MagicMock()
    coordinator.async_load_calibration_state = AsyncMock()
    coordinator.async_load_energy_state = AsyncMock()
    coordinator.async_load_economics_state = AsyncMock()
    coordinator.async_load_control_state = AsyncMock()
    coordinator.async_load_timed_discharge_state = AsyncMock()
    coordinator.price_planner.async_load_cycle_state = AsyncMock()
    coordinator.async_config_entry_first_refresh = AsyncMock(
        side_effect=ConfigEntryNotReady("erster Refresh fehlgeschlagen")
    )
    coordinator.async_shutdown = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    with (
        patch("custom_components.sax_power.AsyncModbusTcpClient", return_value=client),
        patch(
            "custom_components.sax_power.SaxPowerCoordinator",
            return_value=coordinator,
        ),
        pytest.raises(ConfigEntryNotReady, match="erster Refresh fehlgeschlagen"),
    ):
        await async_setup_entry(hass, entry)

    coordinator.async_shutdown.assert_awaited_once_with(reset_device=False)
    client.close.assert_called_once_with()
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
    hass.config_entries.async_unload_platforms.assert_not_awaited()


async def test_late_setup_failure_rolls_back_platforms_and_listeners(hass) -> None:
    """REQ-SETUP-ROLLBACK: Scheitert der Bootstrap erst nach Plattformen,
    Planner und Tarif-Listenern, verschwinden sämtliche Laufzeitressourcen.
    Das Cleanup darf insbesondere keinen Modbus-Steuerwrite auslösen."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        options={
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: "dynamic",
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        },
        entry_id="entry",
    )
    entry.add_to_hass(hass)
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    client.close = MagicMock()
    client.write_register = AsyncMock()
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=entry.entry_id,
        options=entry.options,
    )
    coordinator.async_load_calibration_state = AsyncMock()
    coordinator.async_load_energy_state = AsyncMock()
    coordinator.async_load_economics_state = AsyncMock()
    coordinator.async_load_control_state = AsyncMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    # Ein regulärer Shutdown würde bei diesem beobachteten Gerätezustand
    # Register 40051 zurücksetzen. Der Setup-Rollback darf das nicht tun.
    coordinator._last_observed_ic_control_mode = SUN_IC_CONTROL_MODE_SETPOINT

    async def _fail_after_runtime_resources_started() -> None:
        assert coordinator.price_planner._unsub
        assert coordinator.tariff_provider._unsub
        coordinator._control_store.async_delay_save(
            coordinator.control_config(), delay=3600
        )
        assert coordinator._control_store._save_scheduled is True
        raise RuntimeError("Bootstrap fehlgeschlagen")

    coordinator.async_finish_bootstrap = AsyncMock(
        side_effect=_fail_after_runtime_resources_started
    )
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    with (
        patch("custom_components.sax_power.AsyncModbusTcpClient", return_value=client),
        patch(
            "custom_components.sax_power.SaxPowerCoordinator",
            return_value=coordinator,
        ),
        patch(
            "custom_components.sax_power.async_check_dashboard_up_to_date",
            new=AsyncMock(),
        ),
        pytest.raises(RuntimeError, match="Bootstrap fehlgeschlagen"),
    ):
        await async_setup_entry(hass, entry)

    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        entry, PLATFORMS
    )
    assert not coordinator.price_planner._unsub
    assert not coordinator.tariff_provider._unsub
    assert coordinator._control_store._pending is None
    assert coordinator._control_store._save_scheduled is False
    assert coordinator._control_store._store._delay_handle is None
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
    client.write_register.assert_not_awaited()
    client.close.assert_called_once_with()


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
# Entfallene Entities früherer Versionen
# --------------------------------------------------------------------------
async def test_removed_entities_are_purged_from_the_registry(hass) -> None:
    """Entfallene Herkunfts-, Wirtschafts- und Prognosesensoren werden entfernt.

    Home Assistant räumt sie nicht selbst weg; sie blieben sonst dauerhaft
    als "nicht verfügbar" in Registry, Dashboards und Automationen stehen.
    """
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
        for suffix in (
            "energy_charged_origin_unknown",
            "energy_origin_coverage",
            "economics_result_today",
            "economics_average_daily_result_30d",
            "economics_projected_annual_result",
            "economics_estimated_payback_date",
            "economics_unvalued_inventory",
            "economics_unpriced_charge",
            "economics_unpriced_discharge",
        )
    ]
    kept = [
        registry.async_get_or_create(
            "sensor",
            DOMAIN,
            f"{entry.entry_id}_{suffix}",
            config_entry=entry,
        ).entity_id
        for suffix in ("energy_charged_from_grid", "economics_net_savings_today")
    ]

    _async_remove_stale_entities(hass, entry)

    for entity_id in stale:
        assert registry.async_get(entity_id) is None
    for entity_id in kept:
        assert registry.async_get(entity_id) is not None


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
