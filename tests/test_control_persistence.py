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
    DEFAULT_GRID_SERVING_ENABLED,
    DEFAULT_PRICE_HOURS,
    DEFAULT_PRICE_LIMIT,
    DEFAULT_PRICE_NEUTRAL,
    DEFAULT_PRICE_STRATEGY,
    DEFAULT_TIMED_CHARGE_MIN_SOC,
    MAX_SOC,
    PRICE_STRATEGY_RELATIVE,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.control_store import (
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
    ControlConfig,
    ControlConfigLoadStatus,
    ControlConfigStore,
)
from custom_components.sax_power.number import (
    SaxPowerMaxSocNumber,
    SaxPowerTimedChargeMinSocNumber,
)
from custom_components.sax_power.select import SaxPowerPriceStrategySelect
from custom_components.sax_power.switch import (
    SaxPowerGridServingSwitch,
    SaxPowerMonthSwitch,
    SaxPowerTimedChargeSwitch,
)
from custom_components.sax_power.time import SaxPowerTimedChargeStartTime

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


def _setpoint_mode_writes(client: MagicMock) -> list[int]:
    """Writes, die Register 40051 auf Sollwertvorgabe setzen.

    Genau die dürfen ausbleiben, wenn keine Automatik greifen darf. Der
    einmalige Abgleich auf die SmartMeter-Nullregelung (Modus 0) beim
    Bootstrap-Abschluss ist dagegen erwünscht: Eine frisch gestartete
    Instanz kennt den Gerätezustand nicht und schreibt ihn deshalb genau
    einmal fest (siehe SaxPowerCoordinator._sun_charge_commanded_mode)."""
    return [
        write.kwargs["value"]
        for write in client.write_register.await_args_list
        if write.kwargs["address"] == REG_SUN_IC_CONTROL_MODE
        and write.kwargs["value"] == SUN_IC_CONTROL_MODE_SETPOINT
    ]


def _patched_now(hour: int, month: int = 2):
    return patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, month, 1, hour, 0),
    )


# -- Store -----------------------------------------------------------------


async def test_store_reports_missing_without_existing_data(hass) -> None:
    """Nur ein fehlender Store darf den Migrationspfad öffnen."""
    result = await ControlConfigStore(hass, "entry").async_load()

    assert result.status is ControlConfigLoadStatus.MISSING
    assert result.config is None


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

    result = await ControlConfigStore(hass, "entry").async_load()

    assert result.status is ControlConfigLoadStatus.LOADED
    assert result.config == config


async def test_store_keeps_empty_month_set_distinct_from_missing(
    hass, hass_storage
) -> None:
    """Ein bewusst leeres Monats-Set darf nicht als "nicht gespeichert" und
    damit als "alle Monate" zurückkommen."""
    store = ControlConfigStore(hass, "entry")
    await store.async_save(ControlConfig(timed_charge_months=frozenset()))

    loaded = (await ControlConfigStore(hass, "entry").async_load()).config

    assert loaded is not None
    assert loaded.timed_charge_months == frozenset()
    assert loaded.sanitized().timed_charge_months == frozenset()


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

    loaded = (await ControlConfigStore(hass, "entry").async_load()).config

    assert loaded is not None
    assert loaded.max_soc is None
    assert loaded.timed_charge_start is None
    assert loaded.price_charge_strategy is None
    assert loaded.price_charge_hours is None
    assert loaded.timed_charge_months is None
    # Der gültige Rest bleibt erhalten.
    assert loaded.timed_charge_enabled is True
    assert loaded.timed_charge_end == dt_time(5, 0)


async def test_store_non_dict_payload_reports_failed(hass, hass_storage) -> None:
    """Ein vorhandener, aber unbrauchbarer Store ist NICHT dasselbe wie ein
    fehlender: Er darf weder den Migrationspfad öffnen noch überschrieben
    werden."""
    _seed_store(hass_storage, "entry", ["kein", "objekt"])

    result = await ControlConfigStore(hass, "entry").async_load()

    assert result.status is ControlConfigLoadStatus.FAILED
    assert result.config is None


async def test_store_read_error_reports_failed(hass) -> None:
    """Ein Lesefehler wird abgefangen und als FAILED gemeldet."""
    store = ControlConfigStore(hass, "entry")
    store._store.async_load = AsyncMock(side_effect=OSError("kaputt"))

    result = await store.async_load()

    assert result.status is ControlConfigLoadStatus.FAILED
    assert result.config is None


async def test_store_unknown_future_version_reports_failed(hass) -> None:
    """Home Assistant meldet eine unbekannte Hauptversion per
    NotImplementedError - ein solcher Store darf nie durch Version
    STORAGE_VERSION ersetzt werden."""
    store = ControlConfigStore(hass, "entry")
    store._store.async_load = AsyncMock(side_effect=NotImplementedError)

    result = await store.async_load()

    assert result.status is ControlConfigLoadStatus.FAILED


def test_sanitized_fills_fields_missing_from_an_older_store() -> None:
    """Felder, die ein älterer Store noch nicht kannte, bekommen den
    dokumentierten Hard-Default - Zeitfenster bleiben dagegen leer."""
    filled = ControlConfig(timed_charge_enabled=True).sanitized()

    assert filled.max_soc == MAX_SOC
    assert filled.timed_charge_min_soc == DEFAULT_TIMED_CHARGE_MIN_SOC
    assert filled.timed_charge_months == ALL_MONTHS
    assert filled.price_charge_strategy == DEFAULT_PRICE_STRATEGY
    assert filled.price_charge_hours == DEFAULT_PRICE_HOURS
    assert filled.timed_charge_start is None
    assert filled.timed_charge_end is None


def test_sanitized_resolves_mutually_exclusive_automations() -> None:
    """Netzladung und preisoptimiertes Laden können nie gemeinsam aktiv
    gespeichert werden; ein solcher Store ist beschädigt."""
    resolved = ControlConfig(
        timed_charge_enabled=True, price_charge_enabled=True
    ).sanitized()

    assert resolved.timed_charge_enabled is True
    assert resolved.price_charge_enabled is False


def test_sanitized_clears_overlapping_timed_charge_window() -> None:
    """Jedes Feld für sich gültig, die Kombination aber nicht: Ein solcher
    Store hätte von keinem Setter erzeugt werden können. Geleert wird das
    Netzladefenster, weil nur die Netzladung aktiv Strom aus dem Netz
    zieht."""
    resolved = ControlConfig(
        timed_charge_start=dt_time(1, 0),
        timed_charge_end=dt_time(5, 0),
        grid_serving_start=dt_time(4, 0),
        grid_serving_end=dt_time(6, 0),
    ).sanitized()

    assert resolved.timed_charge_start is None
    assert resolved.timed_charge_end is None
    assert resolved.grid_serving_start == dt_time(4, 0)
    assert resolved.grid_serving_end == dt_time(6, 0)


def test_sanitized_keeps_windows_overlapping_only_in_disjoint_months() -> None:
    """Überschneiden sich nur die Tageszeiten, nicht aber die aktiven
    Monate, können beide Fenster nie gleichzeitig gelten - das ist eine
    zulässige Konfiguration."""
    resolved = ControlConfig(
        timed_charge_start=dt_time(1, 0),
        timed_charge_end=dt_time(5, 0),
        timed_charge_months=frozenset({11, 12, 1}),
        grid_serving_start=dt_time(4, 0),
        grid_serving_end=dt_time(6, 0),
        grid_serving_months=frozenset({5, 6, 7}),
    ).sanitized()

    assert resolved.timed_charge_start == dt_time(1, 0)
    assert resolved.timed_charge_end == dt_time(5, 0)


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

    first = (await ControlConfigStore(hass, "first").async_load()).config
    second = (await ControlConfigStore(hass, "second").async_load()).config

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

    assert coordinator.control_config_status is ControlConfigLoadStatus.LOADED
    assert coordinator.control_config_migration_pending is False
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


async def test_unreadable_store_neither_migrates_nor_gets_overwritten(
    hass, hass_storage
) -> None:
    """Ein Lesefehler ist NICHT dasselbe wie "kein Store": Weder darf ein
    veralteter Entity-Zustand einspringen, noch darf der vorhandene Store
    automatisch durch die Vorgabewerte ersetzt werden - er kann die einzige
    Kopie der richtigen Konfiguration sein."""
    _seed_store(hass_storage, "entry", ACTIVE_WINDOW_PAYLOAD)
    original = dict(hass_storage[f"{STORAGE_KEY_PREFIX}.entry"])
    client = _make_client()
    coordinator = _make_coordinator(hass, client, "entry")
    _patched_reads(coordinator)
    coordinator._control_store._store.async_load = AsyncMock(
        side_effect=OSError("kaputt")
    )

    await coordinator.async_load_control_state()

    assert coordinator.control_config_status is ControlConfigLoadStatus.FAILED
    assert coordinator.control_config_migration_pending is False
    assert coordinator.timed_charge_enabled is False
    assert coordinator.grid_serving_enabled is False
    assert coordinator.price_charge_enabled is False

    # Der Migrationspfad einer Entity mit veraltetem "on" bleibt wirkungslos.
    entity = SaxPowerTimedChargeSwitch(coordinator, "entry")
    entity.hass = hass
    entity.async_get_last_state = AsyncMock(return_value=State("switch.x", "on"))
    entity.async_write_ha_state = MagicMock()
    await entity.async_added_to_hass()

    assert coordinator.timed_charge_enabled is False
    entity.async_get_last_state.assert_not_awaited()

    with _patched_now(2):
        await coordinator.async_refresh()
        client.write_register.assert_not_awaited()

        await coordinator.async_finish_bootstrap()

    # Ohne verwertbare Konfiguration greift keine Automatik - der Speicher
    # bleibt bei der SmartMeter-Nullregelung, das gespeicherte Ladefenster
    # wird nicht aus einem Ratewert heraus wiederhergestellt.
    assert _setpoint_mode_writes(client) == []
    assert hass_storage[f"{STORAGE_KEY_PREFIX}.entry"] == original

    # Auch das Entladen schreibt nichts zurück.
    await coordinator.async_shutdown()
    assert hass_storage[f"{STORAGE_KEY_PREFIX}.entry"] == original


async def test_deliberate_change_writes_again_after_a_store_read_error(
    hass, hass_storage
) -> None:
    """Die Schreibsperre gilt nur für automatische Writes: Ändert der
    Anwender eine Einstellung bewusst, ist das ein ausdrücklicher neuer Wert
    und wird persistiert."""
    _seed_store(hass_storage, "entry", ACTIVE_WINDOW_PAYLOAD)
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    _patched_reads(coordinator)
    coordinator._control_store._store.async_load = AsyncMock(
        side_effect=OSError("kaputt")
    )

    await coordinator.async_load_control_state()
    with _patched_now(8):
        await coordinator.async_refresh()
        await coordinator.async_finish_bootstrap()
        await coordinator.async_set_max_soc(65)

    await coordinator.async_shutdown()

    assert hass_storage[f"{STORAGE_KEY_PREFIX}.entry"]["data"]["max_soc"] == 65


async def test_restart_applies_the_stored_max_soc_hold_without_mode_zero(
    hass, hass_storage
) -> None:
    """Max-SOC-Hold über den Neustart: Liegt der SOC bereits auf dem
    gespeicherten Ziel-SOC, muss der Speicher direkt in der Sollwertvorgabe
    mit 0 % gehalten werden - ohne den Umweg über einen Modus-0-Write, der
    ihn zwischenzeitlich der SmartMeter-Nullregelung überlassen würde."""
    _seed_store(
        hass_storage,
        "entry",
        {**ACTIVE_WINDOW_PAYLOAD, "max_soc": 50, "timed_charge_enabled": False},
    )
    client = _make_client()
    coordinator = _make_coordinator(hass, client, "entry")
    _patched_reads(coordinator)  # READ_DATA meldet SOC 50

    await coordinator.async_load_control_state()
    with _patched_now(8):  # außerhalb jedes Zeitfensters
        await coordinator.async_refresh()

        assert coordinator.max_soc == 50
        client.write_register.assert_not_awaited()

        try:
            await coordinator.async_finish_bootstrap()

            assert coordinator.sun_charge_active is True
            assert [
                (write.kwargs["address"], write.kwargs["value"])
                for write in client.write_register.await_args_list
            ] == [
                (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT),
                (REG_SUN_IC_POWER_SETPOINT_PCT, 0),
            ]
        finally:
            await coordinator.async_stop_sun_charge()


async def test_stored_overlapping_windows_are_resolved_before_the_first_decision(
    hass, hass_storage
) -> None:
    """Ein syntaktisch gültiger Store mit überlappenden Zeitfenstern darf
    keine Netzladung auslösen - die Kombination hätte kein Setter je
    erzeugt."""
    _seed_store(
        hass_storage,
        "entry",
        {
            **ACTIVE_WINDOW_PAYLOAD,
            "grid_serving_start": "04:00:00",
            "grid_serving_end": "06:00:00",
        },
    )
    client = _make_client()
    coordinator = _make_coordinator(hass, client, "entry")
    _patched_reads(coordinator)

    await coordinator.async_load_control_state()

    assert coordinator.timed_charge_start is None
    assert coordinator.timed_charge_end is None
    assert coordinator.grid_serving_start == dt_time(4, 0)

    with _patched_now(2):  # läge im ursprünglich gespeicherten Netzladefenster
        await coordinator.async_refresh()
        client.write_register.assert_not_awaited()

        await coordinator.async_finish_bootstrap()

    assert coordinator._timed_charge_active is False
    assert _setpoint_mode_writes(client) == []
    # Die Korrektur wird auch festgeschrieben, damit sie nicht bei jedem
    # Start erneut anfällt.
    await coordinator.async_shutdown()
    assert (
        hass_storage[f"{STORAGE_KEY_PREFIX}.entry"]["data"]["timed_charge_start"]
        is None
    )


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


# -- Migration ohne Store: unknown/unavailable ist kein Wert ---------------
#
# Genau beim ersten Start auf dieser Version gibt es noch keinen Store. Lag
# davor ein Modbus-Ausfall, können die RestoreEntity-Zustände auf "unknown"
# oder "unavailable" stehen. Solche Zustände dürfen weder als ausdrückliches
# "Aus" noch als Vorgabewert migriert und anschließend dauerhaft gespeichert
# werden (Akzeptanzkriterium 5).

UNRESTORABLE_STATES = ["unknown", "unavailable"]


def _prepare(entity, hass, last_state: State | None):
    entity.hass = hass
    entity.async_get_last_state = AsyncMock(return_value=last_state)
    entity.async_write_ha_state = MagicMock()
    return entity


@pytest.mark.parametrize("state", UNRESTORABLE_STATES)
async def test_migration_ignores_unrestorable_number_state(hass, state: str) -> None:
    """Ein nicht wiederherstellbarer Zahlenwert darf nicht auf den Default
    zurückfallen - der Anwender hatte hier womöglich 60 % stehen."""
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    await coordinator.async_load_control_state()
    entity = _prepare(
        SaxPowerTimedChargeMinSocNumber(coordinator, "entry"),
        hass,
        State("number.x", state),
    )

    await entity.async_added_to_hass()

    assert coordinator.timed_charge_min_soc is None
    assert coordinator.timed_charge_min_soc != DEFAULT_TIMED_CHARGE_MIN_SOC
    await coordinator.async_shutdown()


@pytest.mark.parametrize("state", UNRESTORABLE_STATES)
async def test_migration_ignores_unrestorable_switch_state(hass, state: str) -> None:
    """ "unavailable" ist kein ausdrückliches Aus - der Setter darf gar nicht
    erst laufen."""
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    await coordinator.async_load_control_state()
    coordinator.async_set_grid_serving_enabled = AsyncMock()
    entity = _prepare(
        SaxPowerGridServingSwitch(coordinator, "entry"),
        hass,
        State("switch.x", state),
    )

    await entity.async_added_to_hass()

    coordinator.async_set_grid_serving_enabled.assert_not_awaited()
    assert coordinator.grid_serving_enabled is DEFAULT_GRID_SERVING_ENABLED
    await coordinator.async_shutdown()


@pytest.mark.parametrize("state", UNRESTORABLE_STATES)
async def test_migration_ignores_unrestorable_month_state(hass, state: str) -> None:
    """Regression: Ohne Prüfung entfernte "unavailable" den Monat aus dem
    Default "alle Monate" und legte die Automatik dort dauerhaft still."""
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    await coordinator.async_load_control_state()
    entity = _prepare(
        SaxPowerMonthSwitch(
            coordinator,
            "entry",
            month=3,
            translation_key="timed_charge_month_3",
            is_month_active=lambda m: m in coordinator.timed_charge_months,
            async_set_month_active=coordinator.async_set_timed_charge_month,
        ),
        hass,
        State("switch.x", state),
    )

    await entity.async_added_to_hass()

    assert coordinator.timed_charge_months == ALL_MONTHS
    await coordinator.async_shutdown()


@pytest.mark.parametrize("state", UNRESTORABLE_STATES)
async def test_migration_ignores_unrestorable_time_state(hass, state: str) -> None:
    """Eine nicht parsebare Uhrzeit darf nicht auf den Hard-Default
    zurückfallen und damit ein fremdes Ladefenster erzeugen."""
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    await coordinator.async_load_control_state()
    entity = _prepare(
        SaxPowerTimedChargeStartTime(coordinator, "entry"),
        hass,
        State("time.x", state),
    )

    await entity.async_added_to_hass()

    assert coordinator.timed_charge_start is None
    await coordinator.async_shutdown()


@pytest.mark.parametrize("state", [*UNRESTORABLE_STATES, "gibt-es-nicht"])
async def test_migration_ignores_unrestorable_strategy_state(hass, state: str) -> None:
    """Eine unbekannte Strategie ruft keinen Setter auf."""
    coordinator = _make_coordinator(hass, _make_client(), "entry")
    await coordinator.async_load_control_state()
    coordinator.async_set_price_charge_strategy = AsyncMock()
    entity = _prepare(
        SaxPowerPriceStrategySelect(coordinator, "entry"),
        hass,
        State("select.x", state),
    )

    await entity.async_added_to_hass()

    coordinator.async_set_price_charge_strategy.assert_not_awaited()
    assert coordinator.price_charge_strategy == DEFAULT_PRICE_STRATEGY
    await coordinator.async_shutdown()


async def test_unrestorable_states_are_not_persisted_as_values(hass, hass_storage):
    """Der Bootstrap schreibt danach keinen Ratewert fest: Die nicht
    migrierbaren Felder bleiben leer, statt als ausdrückliche Einstellung im
    Store zu landen."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client, "entry")
    _patched_reads(coordinator)
    await coordinator.async_load_control_state()

    for entity in (
        SaxPowerTimedChargeMinSocNumber(coordinator, "entry"),
        SaxPowerTimedChargeStartTime(coordinator, "entry"),
        SaxPowerTimedChargeSwitch(coordinator, "entry"),
    ):
        await _prepare(entity, hass, State("x.y", "unavailable")).async_added_to_hass()

    with _patched_now(2):
        await coordinator.async_refresh()
        await coordinator.async_finish_bootstrap()

    saved = hass_storage[f"{STORAGE_KEY_PREFIX}.entry"]["data"]
    assert saved["timed_charge_min_soc"] is None
    assert saved["timed_charge_start"] is None
    assert saved["timed_charge_enabled"] is False
    assert _setpoint_mode_writes(client) == []
    await coordinator.async_shutdown()
