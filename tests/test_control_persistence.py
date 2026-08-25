"""Regression tests for REQ-CONTROL-CONFIG-BOOTSTRAP.

Gedeckt werden die drei Bausteine der Zielarchitektur: der versionierte
Store selbst, das Bootstrap-Fenster im Coordinator (Reads erlaubt, Steuern
gesperrt) und der einmalige RestoreEntity-Migrationspfad der Plattformen.
"""

from __future__ import annotations

from datetime import datetime
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import State

from custom_components.sax_power.const import (
    ALL_MONTHS,
    DEFAULT_PRICE_HOURS,
    DEFAULT_PRICE_LIMIT,
    DEFAULT_PRICE_NEUTRAL,
    DEFAULT_PRICE_STRATEGY,
    DEFAULT_TIMED_CHARGE_MIN_SOC,
    MAX_SOC,
    PRICE_STRATEGY_RELATIVE,
    REG_SUN_IC_CONTROL_MODE,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.control_store import (
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
    ControlConfig,
    ControlConfigStore,
)
from custom_components.sax_power.number import SaxPowerMaxSocNumber
from custom_components.sax_power.switch import SaxPowerTimedChargeSwitch

ACTIVE_WINDOW_PAYLOAD = {
    "max_soc": 90,
    "timed_charge_enabled": True,
    "timed_charge_start": "01:00:00",
    "timed_charge_end": "05:00:00",
    "timed_charge_months": sorted(ALL_MONTHS),
    "timed_charge_min_soc": 100,
    "grid_serving_enabled": False,
    "grid_serving_start": "12:00:00",
    "grid_serving_end": "14:00:00",
    "grid_serving_months": sorted(ALL_MONTHS),
    "grid_serving_forecast_threshold_kwh": 0.0,
    "price_charge_enabled": False,
    "price_charge_strategy": DEFAULT_PRICE_STRATEGY,
    "price_charge_max_price": DEFAULT_PRICE_LIMIT,
    "price_charge_neutral_price": DEFAULT_PRICE_NEUTRAL,
    "price_charge_hours": DEFAULT_PRICE_HOURS,
}

READ_DATA = {
    "soc": 50,
    "smartmeter_power": 0,
    "storage_power_active": 0.0,
    "ic_max_power_reference": 4600,
    "ic_timeout": 300,
    "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
}


def _seed_store(hass_storage, entry_id: str, payload: dict | list) -> None:
    """Legt einen vorhandenen Store an, wie ihn ein früherer Lauf hinterlässt."""
    hass_storage[f"{STORAGE_KEY_PREFIX}.{entry_id}"] = {
        "version": STORAGE_VERSION,
        "minor_version": 1,
        "key": f"{STORAGE_KEY_PREFIX}.{entry_id}",
        "data": payload,
    }


def _make_client() -> MagicMock:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)
    return client


def _make_coordinator(hass, client: MagicMock, entry_id: str) -> SaxPowerCoordinator:
    return SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=entry_id,
    )


def _patched_reads(coordinator: SaxPowerCoordinator) -> None:
    """Ersetzt beide Modbus-Leseblöcke - Reads bleiben im Bootstrap erlaubt."""
    coordinator._async_read_basic = AsyncMock(return_value=dict(READ_DATA))
    coordinator._async_read_extended = AsyncMock(return_value={})


def _patched_now(hour: int, month: int = 2):
    return patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, month, 1, hour, 0),
    )


# -- Store -----------------------------------------------------------------


async def test_store_returns_none_without_existing_data(hass) -> None:
    """Nur ein fehlender Store darf den Migrationspfad öffnen."""
    assert await ControlConfigStore(hass, "entry").async_load() is None


async def test_store_round_trip_preserves_every_field(hass, hass_storage) -> None:
    """Alle softwareseitigen Steuerwerte überleben einen Speicherzyklus."""
    store = ControlConfigStore(hass, "entry")
    config = ControlConfig(
        max_soc=80,
        timed_charge_enabled=True,
        timed_charge_start=dt_time(1, 30),
        timed_charge_end=dt_time(5, 45),
        timed_charge_months=frozenset({1, 11, 12}),
        timed_charge_min_soc=35,
        grid_serving_enabled=True,
        grid_serving_start=dt_time(11, 0),
        grid_serving_end=dt_time(14, 0),
        grid_serving_months=frozenset({5, 6, 7}),
        grid_serving_forecast_threshold_kwh=12.5,
        price_charge_enabled=False,
        price_charge_strategy=PRICE_STRATEGY_RELATIVE,
        price_charge_max_price=0.18,
        price_charge_neutral_price=0.33,
        price_charge_hours=6,
    )

    await store.async_save(config)

    assert await ControlConfigStore(hass, "entry").async_load() == config


async def test_store_keeps_empty_month_set_distinct_from_missing(
    hass, hass_storage
) -> None:
    """Ein bewusst leeres Monats-Set darf nicht als "nicht gespeichert" und
    damit als "alle Monate" zurückkommen."""
    store = ControlConfigStore(hass, "entry")
    await store.async_save(ControlConfig(timed_charge_months=frozenset()))

    loaded = await ControlConfigStore(hass, "entry").async_load()

    assert loaded is not None
    assert loaded.timed_charge_months == frozenset()
    assert loaded.with_defaults().timed_charge_months == frozenset()


async def test_store_drops_only_the_invalid_fields(hass, hass_storage) -> None:
    """Ein korrupter Einzelwert verwirft nicht die ganze Konfiguration."""
    _seed_store(
        hass_storage,
        "entry",
        {
            **ACTIVE_WINDOW_PAYLOAD,
            "max_soc": 250,  # außerhalb [MIN_SOC, MAX_SOC]
            "timed_charge_start": "kaputt",
            "price_charge_strategy": "gibt-es-nicht",
            "price_charge_hours": True,  # bool ist kein gültiger int-Wert
            "timed_charge_months": [0, 13],
        },
    )

    loaded = await ControlConfigStore(hass, "entry").async_load()

    assert loaded is not None
    assert loaded.max_soc is None
    assert loaded.timed_charge_start is None
    assert loaded.price_charge_strategy is None
    assert loaded.price_charge_hours is None
    assert loaded.timed_charge_months is None
    # Der gültige Rest bleibt erhalten.
    assert loaded.timed_charge_enabled is True
    assert loaded.timed_charge_end == dt_time(5, 0)


async def test_store_non_dict_payload_is_fail_safe(hass, hass_storage) -> None:
    """Ein vollständig unbrauchbarer Store liefert Defaults, nie None -
    sonst würde ein veralteter Entity-Zustand ihn wieder überschreiben."""
    _seed_store(hass_storage, "entry", ["kein", "objekt"])

    loaded = await ControlConfigStore(hass, "entry").async_load()

    assert loaded == ControlConfig()
    assert loaded.with_defaults().max_soc == MAX_SOC


def test_with_defaults_fills_fields_missing_from_an_older_store() -> None:
    """Felder, die ein älterer Store noch nicht kannte, bekommen den
    dokumentierten Hard-Default - Zeitfenster bleiben dagegen leer."""
    filled = ControlConfig(timed_charge_enabled=True).with_defaults()

    assert filled.max_soc == MAX_SOC
    assert filled.timed_charge_min_soc == DEFAULT_TIMED_CHARGE_MIN_SOC
    assert filled.timed_charge_months == ALL_MONTHS
    assert filled.price_charge_strategy == DEFAULT_PRICE_STRATEGY
    assert filled.price_charge_hours == DEFAULT_PRICE_HOURS
    assert filled.timed_charge_start is None
    assert filled.timed_charge_end is None


def test_with_defaults_resolves_mutually_exclusive_automations() -> None:
    """Netzladung und preisoptimiertes Laden können nie gemeinsam aktiv
    gespeichert werden; ein solcher Store ist beschädigt."""
    resolved = ControlConfig(
        timed_charge_enabled=True, price_charge_enabled=True
    ).with_defaults()

    assert resolved.timed_charge_enabled is True
    assert resolved.price_charge_enabled is False


async def test_delay_save_skips_an_unchanged_snapshot(hass) -> None:
    """Jede Ladeentscheidung merkt den Snapshot vor - unverändert darf das
    keinen Schreibvorgang auslösen."""
    store = ControlConfigStore(hass, "entry")
    config = ControlConfig(max_soc=80)

    assert store.async_delay_save(config) is True
    assert store.async_delay_save(config) is False
    assert store.async_delay_save(ControlConfig(max_soc=70)) is True


async def test_two_config_entries_use_separate_stores(hass, hass_storage) -> None:
    """Mehrere Config Entries dürfen sich ihre Konfiguration nicht teilen."""
    await ControlConfigStore(hass, "first").async_save(ControlConfig(max_soc=70))
    await ControlConfigStore(hass, "second").async_save(ControlConfig(max_soc=95))

    first = await ControlConfigStore(hass, "first").async_load()
    second = await ControlConfigStore(hass, "second").async_load()

    assert first is not None and first.max_soc == 70
    assert second is not None and second.max_soc == 95


# -- Bootstrap im Coordinator ----------------------------------------------


async def test_first_refresh_knows_the_complete_stored_configuration(
    hass, hass_storage
) -> None:
    """Akzeptanzkriterium 1: Vor dem ersten Refresh steht die vollständige
    gespeicherte Konfiguration."""
    _seed_store(hass_storage, "entry", ACTIVE_WINDOW_PAYLOAD)
    coordinator = _make_coordinator(hass, _make_client(), "entry")

    await coordinator.async_load_control_state()

    assert coordinator.control_config_restored is True
    assert coordinator.control_bootstrap_pending is True
    assert coordinator.max_soc == 90
    assert coordinator.timed_charge_enabled is True
    assert coordinator.timed_charge_start == dt_time(1, 0)
    assert coordinator.timed_charge_end == dt_time(5, 0)
    assert coordinator.timed_charge_min_soc == 100
    assert coordinator.timed_charge_months == ALL_MONTHS


async def test_restart_in_an_active_window_never_writes_mode_zero(
    hass, hass_storage
) -> None:
    """Akzeptanzkriterien 2+3: Der erste Refresh liest, steuert aber nicht -
    der erste Schreibvorgang überhaupt ist die Sollwertvorgabe des
    gespeicherten, gerade aktiven Fensters, nie die Nullregelung."""
    _seed_store(hass_storage, "entry", ACTIVE_WINDOW_PAYLOAD)
    client = _make_client()
    coordinator = _make_coordinator(hass, client, "entry")
    _patched_reads(coordinator)

    await coordinator.async_load_control_state()
    with _patched_now(2):
        await coordinator.async_refresh()

        assert coordinator.last_update_success is True
        client.write_register.assert_not_awaited()

        try:
            await coordinator.async_finish_bootstrap()

            assert coordinator.control_bootstrap_pending is False
            assert coordinator._timed_charge_active is True
            assert client.write_register.await_args_list[0].kwargs == {
                "address": REG_SUN_IC_CONTROL_MODE,
                "value": SUN_IC_CONTROL_MODE_SETPOINT,
                "device_id": 100,
            }
            assert not [
                write
                for write in client.write_register.await_args_list
                if write.kwargs["address"] == REG_SUN_IC_CONTROL_MODE
                and write.kwargs["value"] == SUN_IC_CONTROL_MODE_SMARTMETER
            ]
        finally:
            await coordinator.async_stop_sun_charge()


async def test_setters_apply_no_partial_configuration_during_bootstrap(
    hass, hass_storage
) -> None:
    """Akzeptanzkriterium 3: Auch die Setter der migrierenden Entities
    steuern während des Bootstraps nicht - sie schreiben weder ins Gerät
    noch den unvollständigen Zwischenstand in den Store."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client, "entry")
    _patched_reads(coordinator)

    await coordinator.async_load_control_state()
    with _patched_now(2):
        await coordinator.async_refresh()

        await coordinator.async_set_max_soc(90)
        await coordinator.async_set_timed_charge_min_soc(100)
        await coordinator.async_set_timed_charge_start(dt_time(1, 0))
        await coordinator.async_set_timed_charge_end(dt_time(5, 0))
        await coordinator.async_set_timed_charge_enabled(True, force=True)

        client.write_register.assert_not_awaited()
        assert f"{STORAGE_KEY_PREFIX}.entry" not in hass_storage

        try:
            await coordinator.async_finish_bootstrap()

            assert coordinator._timed_charge_active is True
            # Migration ohne Store: der fertige Snapshot liegt sofort auf
            # der Platte, nicht erst nach dem Sammel-Timer.
            saved = hass_storage[f"{STORAGE_KEY_PREFIX}.entry"]["data"]
            assert saved["max_soc"] == 90
            assert saved["timed_charge_enabled"] is True
            assert saved["timed_charge_start"] == "01:00:00"
            assert saved["timed_charge_end"] == "05:00:00"
        finally:
            await coordinator.async_stop_sun_charge()


async def test_failed_first_refresh_keeps_the_stored_configuration(
    hass, hass_storage
) -> None:
    """Akzeptanzkriterium 4: Ein Basic-Mode-Ausfall lässt die gespeicherten
    Softwarewerte unangetastet - sie stammen aus keinem Register."""
    _seed_store(hass_storage, "entry", ACTIVE_WINDOW_PAYLOAD)
    client = _make_client()
    coordinator = _make_coordinator(hass, client, "entry")
    coordinator._async_read_basic = AsyncMock(side_effect=TimeoutError)

    await coordinator.async_load_control_state()
    await coordinator.async_refresh()

    assert coordinator.last_update_success is False
    assert coordinator.max_soc == 90
    assert coordinator.timed_charge_enabled is True
    assert coordinator.timed_charge_start == dt_time(1, 0)
    client.write_register.assert_not_awaited()


async def test_unreadable_store_falls_back_to_safe_defaults(hass) -> None:
    """Fail-safe: Ist der Store gar nicht lesbar, bleiben die Automatiken
    aus, statt aus einer geratenen Konfiguration heraus zu laden."""
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    coordinator._control_store.async_load = AsyncMock(side_effect=OSError("kaputt"))

    await coordinator.async_load_control_state()

    assert coordinator.control_config_restored is False
    assert coordinator.control_bootstrap_pending is True
    assert coordinator.timed_charge_enabled is False
    assert coordinator.grid_serving_enabled is False
    assert coordinator.price_charge_enabled is False


async def test_finish_bootstrap_is_idempotent(hass, hass_storage) -> None:
    """Ein zweiter Aufruf (z. B. aus einem Reload-Pfad) darf keine weitere
    Ladeentscheidung auslösen."""
    _seed_store(hass_storage, "entry", ACTIVE_WINDOW_PAYLOAD)
    client = _make_client()
    coordinator = _make_coordinator(hass, client, "entry")
    _patched_reads(coordinator)

    await coordinator.async_load_control_state()
    with _patched_now(8):  # außerhalb des gespeicherten Fensters
        await coordinator.async_refresh()
        await coordinator.async_finish_bootstrap()
        client.write_register.reset_mock()

        await coordinator.async_finish_bootstrap()

    client.write_register.assert_not_awaited()


async def test_setting_change_after_bootstrap_is_persisted(hass, hass_storage) -> None:
    """Nach dem Bootstrap landet jede Änderung im Store - beim Entladen
    sofort, nicht erst über den Sammel-Timer."""
    _seed_store(hass_storage, "entry", ACTIVE_WINDOW_PAYLOAD)
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    _patched_reads(coordinator)

    await coordinator.async_load_control_state()
    with _patched_now(8):
        await coordinator.async_refresh()
        await coordinator.async_finish_bootstrap()
        await coordinator.async_set_max_soc(65)

    await coordinator.async_shutdown()

    assert hass_storage[f"{STORAGE_KEY_PREFIX}.entry"]["data"]["max_soc"] == 65


# -- Migrationspfad der Plattform-Entities ---------------------------------


@pytest.mark.parametrize("last_state", [None, State("number.x", "unknown")])
async def test_number_restore_never_overrides_a_stored_value(
    hass, hass_storage, last_state: State | None
) -> None:
    """Akzeptanzkriterium 5: Steht der Wert im Store, ist ein
    unknown/unavailable gewordener Entity-Zustand bedeutungslos."""
    _seed_store(hass_storage, "entry", ACTIVE_WINDOW_PAYLOAD)
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    await coordinator.async_load_control_state()

    entity = SaxPowerMaxSocNumber(coordinator, "entry")
    entity.hass = hass
    entity.async_get_last_state = AsyncMock(return_value=last_state)
    entity.async_write_ha_state = MagicMock()

    await entity.async_added_to_hass()

    assert coordinator.max_soc == 90
    assert entity.native_value == 90
    entity.async_get_last_state.assert_not_awaited()
    await coordinator.async_shutdown()


async def test_switch_restore_migrates_once_without_a_store(hass) -> None:
    """Ohne Store bleibt der RestoreEntity-Zustand die einzige Quelle -
    genau dafür ist der Migrationspfad da."""
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    await coordinator.async_load_control_state()

    entity = SaxPowerTimedChargeSwitch(coordinator, "entry")
    entity.hass = hass
    entity.async_get_last_state = AsyncMock(return_value=State("switch.x", "on"))
    entity.async_write_ha_state = MagicMock()

    await entity.async_added_to_hass()

    assert coordinator.timed_charge_enabled is True
    await coordinator.async_shutdown()


async def test_config_entities_stay_available_during_a_modbus_failure(hass) -> None:
    """Akzeptanzkriterium 6 / Umsetzungspunkt 6: Software-Einstellungen
    hängen nicht mehr an coordinator.last_update_success."""
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    coordinator.last_update_success = False

    entity = SaxPowerMaxSocNumber(coordinator, "entry")
    entity.hass = hass

    assert entity.available is True
