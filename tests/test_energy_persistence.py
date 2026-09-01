"""Regression tests for REQ-ENERGY-DASHBOARD/REQ-ENERGY-ORIGIN counter
persistence."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.core import State
from homeassistant.util import dt as dt_util

from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.energy_store import (
    STORAGE_KEY_PREFIX,
    EnergyState,
    EnergyStateStore,
)
from custom_components.sax_power.sensor import SaxPowerEnergySensor


def _seed_real_store(
    hass_storage, entry_id: str, payload: dict, *, version: int, minor_version: int
) -> None:
    """Legt einen echten, unentpackten Store-Envelope an, wie ihn ein
    früherer Home-Assistant-Lauf tatsächlich auf der Platte hinterlässt -
    im Unterschied zu einem gemockten `_store.async_load`, das die
    HA-eigene Versions-/Migrationslogik von `homeassistant.helpers.storage.
    Store` komplett umgeht (siehe test_a_real_version_one_store_loads_
    without_a_migration_crash). `version`/`minor_version` sind bewusst
    literale Werte statt des aktuellen STORAGE_VERSION-Imports: Der Test
    simuliert einen VOR dieser Funktion geschriebenen, also historisch
    festen Envelope-Stand - würde er stattdessen die jeweils aktuelle
    Konstante verwenden, prüfte er nach einer künftigen Versionsänderung
    stillschweigend nicht mehr den ursprünglichen Migrationsfall."""
    hass_storage[f"{STORAGE_KEY_PREFIX}.{entry_id}"] = {
        "version": version,
        "minor_version": minor_version,
        "key": f"{STORAGE_KEY_PREFIX}.{entry_id}",
        "data": payload,
    }


def _coordinator(hass, entry_id: str = "entry") -> SaxPowerCoordinator:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    return SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=entry_id,
    )


def _energy_entity(
    hass,
    coordinator: SaxPowerCoordinator,
    *,
    last_state: State | None,
) -> SaxPowerEnergySensor:
    entity = SaxPowerEnergySensor(
        coordinator,
        coordinator.entry_id,
        key="energy_charged",
        translation_key="energy_charged",
        data_key="energy_charged",
        restore_fn=coordinator.restore_energy_charged,
    )
    entity.hass = hass
    entity.entity_id = "sensor.sax_power_energy_charged"
    entity.async_write_ha_state = MagicMock()
    entity.async_get_last_state = AsyncMock(return_value=last_state)
    return entity


# -- Store-Versionierung (REQ-ENERGY-ORIGIN) ---------------------------------
# Regressionstest gegen eine erhöhte Store-HAUPTversion: Home Assistant ruft
# beim Laden eines vorhandenen Envelopes intern _async_migrate_func auf,
# sobald sich Haupt- ODER Minor-Version unterscheiden. Deren
# Standardimplementierung wirft NotImplementedError; bei UNVERÄNDERTER
# Hauptversion fängt Store diesen Fehler selbst ab und behält die Rohdaten
# bei, bei einer geänderten Hauptversion schlägt er ungefangen durch (siehe
# infrastructure/energy_store.py, STORAGE_VERSION-Kommentar). Ein gemocktes
# `_store.async_load` (wie in den übrigen Tests dieser Datei) umgeht diese
# Home-Assistant-interne Logik komplett und hätte den ursprünglichen Fehler
# nicht aufgedeckt - deshalb hier ein echter, unentpackter Envelope über die
# `hass_storage`-Fixture.


async def test_a_real_version_one_store_loads_without_a_migration_crash(
    hass, hass_storage
) -> None:
    """Ein auf der Platte liegender Store mit derselben Hauptversion, aber
    älterer Minor-Version (vor Einführung der Herkunftsfelder) darf das
    Setup nicht mit NotImplementedError zum Absturz bringen."""
    _seed_real_store(
        hass_storage,
        "entry",
        {"charged_kwh": 50.0, "discharged_kwh": 20.0},
        version=1,
        minor_version=1,
    )
    coordinator = _coordinator(hass)

    await coordinator.async_load_energy_state()

    assert coordinator._energy_charged_kwh == 50.0
    assert coordinator._energy_discharged_kwh == 20.0
    # Historische Ladeenergie wird nicht rückwirkend zugeordnet - die
    # Herkunft startet transparent bei 0 ab der Migration.
    assert coordinator._energy_grid_charged_kwh == 0.0
    assert coordinator._energy_pv_charged_kwh == 0.0
    assert coordinator._origin_accounting_started_at is not None
    await coordinator.async_shutdown()


async def test_a_version_two_store_with_unknown_origin_restarts_the_counting(
    hass, hass_storage, caplog
) -> None:
    """Ein Snapshot mit echtem Restbestand der entfallenen Kategorie
    "Herkunft unbekannt" startet die Herkunftszählung neu, statt den
    Bestand auf den Netzzähler zu addieren: energy_charged_from_grid ist
    TOTAL_INCREASING, ein Aufschlag erschiene in der Langzeitstatistik als
    am Upgrade-Tag zugeflossene Netzenergie. Der Rücksprung auf 0 ist
    dagegen ein regulärer Zählerreset (REQ-ENERGY-ORIGIN)."""
    started_at = dt_util.utcnow() - timedelta(days=7)
    _seed_real_store(
        hass_storage,
        "entry",
        {
            "charged_kwh": 50.0,
            "discharged_kwh": 20.0,
            "grid_charged_kwh": 12.0,
            "pv_charged_kwh": 30.0,
            "unknown_charged_kwh": 8.0,
            "origin_accounting_started_at": started_at.isoformat(),
        },
        version=1,
        minor_version=2,
    )
    coordinator = _coordinator(hass)

    await coordinator.async_load_energy_state()

    assert coordinator._energy_grid_charged_kwh == 0.0
    assert coordinator._energy_pv_charged_kwh == 0.0
    assert coordinator._origin_accounting_started_at != started_at
    # Die Gesamtzähler bleiben davon unberührt.
    assert coordinator._energy_charged_kwh == 50.0
    assert coordinator._energy_discharged_kwh == 20.0
    assert "Herkunftszählung wird neu gestartet" in caplog.text
    await coordinator.async_shutdown()


async def test_a_version_two_store_without_unknown_origin_keeps_its_counters(
    hass, hass_storage
) -> None:
    """Der Regelfall - ein Snapshot, in dem die entfallene Kategorie leer
    blieb - behält seine Herkunftszähler und seinen Startzeitpunkt
    vollständig: Ohne echten Altbestand gibt es nichts umzudeuten."""
    started_at = dt_util.utcnow() - timedelta(days=7)
    _seed_real_store(
        hass_storage,
        "entry",
        {
            "charged_kwh": 50.0,
            "discharged_kwh": 20.0,
            "grid_charged_kwh": 12.0,
            "pv_charged_kwh": 38.0,
            "unknown_charged_kwh": 0.0,
            "origin_accounting_started_at": started_at.isoformat(),
        },
        version=1,
        minor_version=2,
    )
    coordinator = _coordinator(hass)

    await coordinator.async_load_energy_state()

    assert coordinator._energy_grid_charged_kwh == 12.0
    assert coordinator._energy_pv_charged_kwh == 38.0
    assert coordinator._origin_accounting_started_at == started_at
    await coordinator.async_shutdown()


async def test_store_restores_two_config_entries_independently(hass) -> None:
    """Lade- und Entladezähler sind gemeinsam, aber pro Entry gespeichert."""
    first = EnergyStateStore(hass, "first")
    second = EnergyStateStore(hass, "second")
    assert await first.async_save(EnergyState(12.5, 4.25)) is True
    assert await second.async_save(EnergyState(3.0, 9.75)) is True

    assert await EnergyStateStore(hass, "first").async_load() == EnergyState(12.5, 4.25)
    assert await EnergyStateStore(hass, "second").async_load() == EnergyState(3.0, 9.75)


async def test_store_rejects_corrupt_fields_independently(hass, caplog) -> None:
    """Ein kaputter Ladezähler darf den gültigen Entladezähler nicht löschen."""
    store = EnergyStateStore(hass, "corrupt")
    store._store.async_load = AsyncMock(
        return_value={"charged_kwh": -1, "discharged_kwh": 8.5}
    )

    assert await store.async_load() == EnergyState(None, 8.5)
    assert "Ungültigen gespeicherten Energiezähler für Laden" in caplog.text


_NO_ORIGIN = {
    "grid_charged_kwh": None,
    "pv_charged_kwh": None,
    "origin_accounting_started_at": None,
}


def test_store_throttles_frequent_updates_and_keeps_newest_state(hass) -> None:
    """Mehrere 2-s-Polls erzeugen nur einen verzögerten Store-Schreibauftrag."""
    store = EnergyStateStore(hass, "throttled")
    store._store.async_delay_save = MagicMock()

    assert store.async_delay_save(EnergyState(1.0, 2.0)) is True
    assert store.async_delay_save(EnergyState(1.1, 2.0)) is True

    store._store.async_delay_save.assert_called_once()
    data_func = store._store.async_delay_save.call_args.args[0]
    assert data_func() == {"charged_kwh": 1.1, "discharged_kwh": 2.0, **_NO_ORIGIN}


async def test_store_final_flush_writes_newest_state_immediately(hass) -> None:
    """Der Unload-Flush überholt einen noch ausstehenden verzögerten Write."""
    store = EnergyStateStore(hass, "flush")
    store._store.async_delay_save = MagicMock()
    store._store.async_save = AsyncMock()
    store.async_delay_save(EnergyState(1.0, 2.0))

    assert await store.async_save(EnergyState(1.5, 2.25)) is True
    store._store.async_save.assert_awaited_once_with(
        {"charged_kwh": 1.5, "discharged_kwh": 2.25, **_NO_ORIGIN}
    )


async def test_store_rejects_regressive_snapshot(hass, caplog) -> None:
    store = EnergyStateStore(hass, "regressive")
    store._store.async_save = AsyncMock()
    assert await store.async_save(EnergyState(10.0, 5.0)) is True

    assert await store.async_save(EnergyState(9.0, 5.0)) is False
    assert store._store.async_save.await_count == 1
    assert "Rückläufigen Energiezähler-Snapshot" in caplog.text


# -- Herkunftszähler (REQ-ENERGY-ORIGIN) -------------------------------------


async def test_store_round_trips_origin_counters_and_start_timestamp(hass) -> None:
    started_at = dt_util.utcnow().replace(microsecond=0)
    store = EnergyStateStore(hass, "origin-roundtrip")
    state = EnergyState(
        charged_kwh=12.5,
        discharged_kwh=4.25,
        grid_charged_kwh=8.0,
        pv_charged_kwh=4.5,
        origin_accounting_started_at=started_at,
    )

    assert await store.async_save(state) is True
    loaded = await EnergyStateStore(hass, "origin-roundtrip").async_load()

    assert loaded == state
    assert loaded.origin_initialized is True


async def test_store_rejects_a_corrupt_origin_counter_independently(
    hass, caplog
) -> None:
    """Ein kaputter Herkunftszähler darf weder die übrigen Herkunftsfelder
    noch die bestehenden Lade-/Entladezähler löschen (unabhängige
    Feldvalidierung, siehe anforderung.yaml REQ-ENERGY-ORIGIN)."""
    store = EnergyStateStore(hass, "origin-corrupt")
    started_at = dt_util.utcnow()
    store._store.async_load = AsyncMock(
        return_value={
            "charged_kwh": 12.5,
            "discharged_kwh": 4.25,
            "grid_charged_kwh": -1,
            "pv_charged_kwh": 4.5,
            "origin_accounting_started_at": started_at.isoformat(),
        }
    )

    loaded = await store.async_load()

    assert loaded.charged_kwh == 12.5
    assert loaded.grid_charged_kwh is None
    assert loaded.pv_charged_kwh == 4.5
    assert loaded.origin_accounting_started_at == started_at
    assert loaded.origin_initialized is False
    assert "Ungültigen gespeicherten Energiezähler für Netzladung" in caplog.text


async def test_store_accepts_a_fresh_restart_after_a_partially_corrupt_bundle(
    hass,
) -> None:
    """Nach einem unvollständigen Herkunfts-Bündel darf der nächste, vom
    Coordinator neu gestartete Snapshot (beide Zähler auf 0, neuer
    Startzeitpunkt - siehe SaxPowerCoordinator._bootstrap_energy_origin)
    nicht an der alten Teil-Baseline scheitern. Andernfalls bliebe die
    Herkunftszählung über jeden Neustart hinweg dauerhaft unpersistiert,
    weil jeder Speicherversuch gegen die stehen gebliebenen alten
    Teilwerte bzw. den alten Startzeitpunkt als "rückläufig" bzw.
    "abweichend" abgelehnt würde."""
    store = EnergyStateStore(hass, "origin-partial-recovery")
    old_started_at = dt_util.utcnow() - timedelta(days=1)
    store._store.async_load = AsyncMock(
        return_value={
            "charged_kwh": 12.5,
            "discharged_kwh": 4.25,
            "grid_charged_kwh": -1,  # korrupt -> gesamtes Bündel unvollständig
            "pv_charged_kwh": 4.5,
            "origin_accounting_started_at": old_started_at.isoformat(),
        }
    )
    store._store.async_save = AsyncMock()

    loaded = await store.async_load()
    assert loaded.origin_initialized is False

    # Genau das Verhalten von SaxPowerCoordinator._bootstrap_energy_origin
    # nach einem unvollständigen Bündel: charged_kwh/discharged_kwh bleiben
    # erhalten, die Herkunft startet komplett neu bei 0.
    restarted = EnergyState(
        charged_kwh=loaded.charged_kwh,
        discharged_kwh=loaded.discharged_kwh,
        grid_charged_kwh=0.0,
        pv_charged_kwh=0.0,
        origin_accounting_started_at=dt_util.utcnow(),
    )
    assert await store.async_save(restarted) is True
    store._store.async_save.assert_awaited_once()


async def test_store_rejects_a_regressive_origin_counter(hass, caplog) -> None:
    started_at = dt_util.utcnow()
    store = EnergyStateStore(hass, "origin-regressive")
    store._store.async_save = AsyncMock()
    base = EnergyState(
        10.0,
        5.0,
        grid_charged_kwh=6.0,
        pv_charged_kwh=4.0,
        origin_accounting_started_at=started_at,
    )
    assert await store.async_save(base) is True

    regressive = EnergyState(
        11.0,
        5.0,
        grid_charged_kwh=5.0,
        pv_charged_kwh=4.0,
        origin_accounting_started_at=started_at,
    )
    assert await store.async_save(regressive) is False
    assert store._store.async_save.await_count == 1
    assert "Rückläufigen Energiezähler-Snapshot für Netzladung" in caplog.text


async def test_store_rejects_a_changed_origin_start_timestamp(hass, caplog) -> None:
    """origin_accounting_started_at ist eine einmalig gesetzte Konstante -
    ein abweichender Wert kann nur aus einem beschädigten Snapshot stammen."""
    first = dt_util.utcnow()
    second = first + timedelta(hours=1)
    store = EnergyStateStore(hass, "origin-timestamp-drift")
    store._store.async_save = AsyncMock()
    base = EnergyState(
        10.0,
        5.0,
        grid_charged_kwh=6.0,
        pv_charged_kwh=4.0,
        origin_accounting_started_at=first,
    )
    assert await store.async_save(base) is True

    drifted = EnergyState(
        11.0,
        5.0,
        grid_charged_kwh=7.0,
        pv_charged_kwh=4.0,
        origin_accounting_started_at=second,
    )
    assert await store.async_save(drifted) is False
    assert store._store.async_save.await_count == 1
    assert "Abweichenden Startzeitpunkt der Herkunftszählung" in caplog.text


@pytest.mark.parametrize("value", ["nicht-parsebar", "2026-08-26T10:00:00", 42, True])
async def test_store_rejects_an_unusable_start_timestamp(hass, caplog, value) -> None:
    """Weder ein unparsebarer String noch eine naive (zeitzonenlose)
    Zeitangabe noch ein Fremdtyp gelten als gültiger Startzeitpunkt -
    "2026-08-26T10:00:00" ist absichtlich ohne Zeitzone."""
    store = EnergyStateStore(hass, "origin-bad-timestamp")
    store._store.async_load = AsyncMock(
        return_value={
            "charged_kwh": 1.0,
            "discharged_kwh": 0.0,
            "grid_charged_kwh": 1.0,
            "pv_charged_kwh": 0.0,
            "origin_accounting_started_at": value,
        }
    )

    loaded = await store.async_load()

    assert loaded.origin_accounting_started_at is None
    assert loaded.origin_initialized is False
    assert "Ungültigen gespeicherten Startzeitpunkt" in caplog.text


async def test_store_restores_origin_counters_for_two_entries_independently(
    hass,
) -> None:
    first_started = dt_util.utcnow()
    second_started = first_started + timedelta(days=1)
    first = EnergyStateStore(hass, "origin-first")
    second = EnergyStateStore(hass, "origin-second")
    await first.async_save(
        EnergyState(
            5.0,
            2.0,
            grid_charged_kwh=3.0,
            pv_charged_kwh=2.0,
            origin_accounting_started_at=first_started,
        )
    )
    await second.async_save(
        EnergyState(
            8.0,
            1.0,
            grid_charged_kwh=1.0,
            pv_charged_kwh=7.0,
            origin_accounting_started_at=second_started,
        )
    )

    loaded_first = await EnergyStateStore(hass, "origin-first").async_load()
    loaded_second = await EnergyStateStore(hass, "origin-second").async_load()

    assert loaded_first.grid_charged_kwh == 3.0
    assert loaded_first.origin_accounting_started_at == first_started
    assert loaded_second.pv_charged_kwh == 7.0
    assert loaded_second.origin_accounting_started_at == second_started


@pytest.mark.parametrize("legacy_state", ["unknown", "unavailable", "nan", "-1"])
async def test_non_numeric_or_invalid_legacy_state_stays_uninitialized(
    hass, legacy_state: str
) -> None:
    """Ein ausgefallener sichtbarer Sensor darf keinen Reset auf 0 migrieren."""
    coordinator = _coordinator(hass)
    coordinator._energy_store.async_load = AsyncMock(return_value=None)
    await coordinator.async_load_energy_state()
    entity = _energy_entity(
        hass,
        coordinator,
        last_state=State(
            entity_id="sensor.sax_power_energy_charged", state=legacy_state
        ),
    )

    await entity.async_added_to_hass()
    data = {"storage_power_active": 0}
    coordinator._accumulate_energy(data)

    assert data["energy_charged"] is None
    await coordinator.async_shutdown()


async def test_fresh_install_seeds_counter_with_zero(hass) -> None:
    """Nur ein wirklich neuer Eintrag ohne Altzustand erhält die 0-Baseline."""
    coordinator = _coordinator(hass)
    coordinator._energy_store.async_load = AsyncMock(return_value=None)
    coordinator._energy_store.async_delay_save = MagicMock(return_value=True)
    await coordinator.async_load_energy_state()
    entity = _energy_entity(hass, coordinator, last_state=None)

    await entity.async_added_to_hass()
    data = {"storage_power_active": 0}
    coordinator._accumulate_energy(data)

    assert data["energy_charged"] == 0.0
    await coordinator.async_shutdown()


async def test_numeric_legacy_state_migrates_without_new_snapshot(hass) -> None:
    """Die RestoreEntity-Migration betrifft ausschließlich energy_charged;
    die Herkunftszählung (REQ-ENERGY-ORIGIN) ist davon unabhängig bereits
    beim Laden auf 0 gestartet, siehe test_fresh_install_seeds_counter_with_zero
    und test_load_starts_origin_accounting_for_a_brand_new_entry."""
    coordinator = _coordinator(hass)
    coordinator._energy_store.async_load = AsyncMock(return_value=None)
    coordinator._energy_store.async_delay_save = MagicMock(return_value=True)
    await coordinator.async_load_energy_state()
    started_at = coordinator._origin_accounting_started_at
    entity = _energy_entity(
        hass,
        coordinator,
        last_state=State("sensor.sax_power_energy_charged", "42.125"),
    )

    await entity.async_added_to_hass()
    data = {"storage_power_active": 0}
    coordinator._accumulate_energy(data)

    assert data["energy_charged"] == 42.125
    coordinator._energy_store.async_delay_save.assert_called_once_with(
        EnergyState(
            charged_kwh=42.125,
            grid_charged_kwh=0.0,
            pv_charged_kwh=0.0,
            origin_accounting_started_at=started_at,
        )
    )
    await coordinator.async_shutdown()


async def test_new_store_snapshot_wins_over_regressive_legacy_state(
    hass, caplog
) -> None:
    coordinator = _coordinator(hass)
    coordinator._energy_store.async_load = AsyncMock(
        return_value=EnergyState(100.0, 50.0)
    )
    await coordinator.async_load_energy_state()
    entity = _energy_entity(
        hass,
        coordinator,
        last_state=State("sensor.sax_power_energy_charged", "20"),
    )

    await entity.async_added_to_hass()
    data = {"storage_power_active": 0}
    coordinator._accumulate_energy(data)

    assert data["energy_charged"] == 100.0
    assert "Rückläufigen RestoreEntity-Altzustand" in caplog.text
    await coordinator.async_shutdown()


async def test_shutdown_flushes_exact_counter_during_basic_mode_outage(hass) -> None:
    """Unavailable beim Shutdown darf den letzten RAM-Zähler nicht ersetzen.

    Der geladene Snapshot ist bewusst ein Version-1-Stand ohne
    Herkunftsfelder (EnergyState(15.75, 7.25)) - der Shutdown-Flush muss
    ihn samt der beim Laden gestarteten Herkunftszählung (0/0/0 + jetzt)
    persistieren, siehe REQ-ENERGY-ORIGIN."""
    coordinator = _coordinator(hass)
    coordinator._energy_store.async_load = AsyncMock(
        return_value=EnergyState(15.75, 7.25)
    )
    coordinator._energy_store.async_save = AsyncMock(return_value=True)
    await coordinator.async_load_energy_state()
    started_at = coordinator._origin_accounting_started_at
    assert started_at is not None
    coordinator.last_update_success = False

    await coordinator.async_shutdown()

    coordinator._energy_store.async_save.assert_awaited_once_with(
        EnergyState(
            15.75,
            7.25,
            grid_charged_kwh=0.0,
            pv_charged_kwh=0.0,
            origin_accounting_started_at=started_at,
        )
    )

    restarted = _coordinator(hass, "entry-restarted")
    restarted._energy_store.async_load = AsyncMock(
        return_value=coordinator._energy_store.async_save.await_args.args[0]
    )
    await restarted.async_load_energy_state()
    data = {"storage_power_active": 0}
    restarted._accumulate_energy(data)
    assert data["energy_charged"] == 15.75
    assert data["energy_discharged"] == 7.25
    assert data["energy_charged_from_grid"] == 0.0
    assert data["energy_charged_from_pv"] == 0.0
    assert restarted._origin_accounting_started_at == started_at
    await restarted.async_shutdown()


def test_energy_sensor_statistics_properties_are_unchanged(hass) -> None:
    entity = _energy_entity(hass, _coordinator(hass), last_state=None)

    assert entity.device_class is SensorDeviceClass.ENERGY
    assert entity.state_class is SensorStateClass.TOTAL_INCREASING
    assert entity.native_unit_of_measurement is UnitOfEnergy.KILO_WATT_HOUR
