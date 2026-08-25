"""Regression tests for REQ-ENERGY-DASHBOARD counter persistence."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.core import State

from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.energy_store import (
    EnergyState,
    EnergyStateStore,
)
from custom_components.sax_power.sensor import SaxPowerEnergySensor


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


def test_store_throttles_frequent_updates_and_keeps_newest_state(hass) -> None:
    """Mehrere 2-s-Polls erzeugen nur einen verzögerten Store-Schreibauftrag."""
    store = EnergyStateStore(hass, "throttled")
    store._store.async_delay_save = MagicMock()

    assert store.async_delay_save(EnergyState(1.0, 2.0)) is True
    assert store.async_delay_save(EnergyState(1.1, 2.0)) is True

    store._store.async_delay_save.assert_called_once()
    data_func = store._store.async_delay_save.call_args.args[0]
    assert data_func() == {"charged_kwh": 1.1, "discharged_kwh": 2.0}


async def test_store_final_flush_writes_newest_state_immediately(hass) -> None:
    """Der Unload-Flush überholt einen noch ausstehenden verzögerten Write."""
    store = EnergyStateStore(hass, "flush")
    store._store.async_delay_save = MagicMock()
    store._store.async_save = AsyncMock()
    store.async_delay_save(EnergyState(1.0, 2.0))

    assert await store.async_save(EnergyState(1.5, 2.25)) is True
    store._store.async_save.assert_awaited_once_with(
        {"charged_kwh": 1.5, "discharged_kwh": 2.25}
    )


async def test_store_rejects_regressive_snapshot(hass, caplog) -> None:
    store = EnergyStateStore(hass, "regressive")
    store._store.async_save = AsyncMock()
    assert await store.async_save(EnergyState(10.0, 5.0)) is True

    assert await store.async_save(EnergyState(9.0, 5.0)) is False
    assert store._store.async_save.await_count == 1
    assert "Rückläufigen Energiezähler-Snapshot" in caplog.text


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
    coordinator = _coordinator(hass)
    coordinator._energy_store.async_load = AsyncMock(return_value=None)
    coordinator._energy_store.async_delay_save = MagicMock(return_value=True)
    await coordinator.async_load_energy_state()
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
        EnergyState(charged_kwh=42.125)
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
    """Unavailable beim Shutdown darf den letzten RAM-Zähler nicht ersetzen."""
    coordinator = _coordinator(hass)
    coordinator._energy_store.async_load = AsyncMock(
        return_value=EnergyState(15.75, 7.25)
    )
    coordinator._energy_store.async_save = AsyncMock(return_value=True)
    await coordinator.async_load_energy_state()
    coordinator.last_update_success = False

    await coordinator.async_shutdown()

    coordinator._energy_store.async_save.assert_awaited_once_with(
        EnergyState(15.75, 7.25)
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
    await restarted.async_shutdown()


def test_energy_sensor_statistics_properties_are_unchanged(hass) -> None:
    entity = _energy_entity(hass, _coordinator(hass), last_state=None)

    assert entity.device_class is SensorDeviceClass.ENERGY
    assert entity.state_class is SensorStateClass.TOTAL_INCREASING
    assert entity.native_unit_of_measurement is UnitOfEnergy.KILO_WATT_HOUR
