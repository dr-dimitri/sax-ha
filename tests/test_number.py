"""Tests for the SAX Power number entities (software-side default/init logic).

Instanziiert die Entities direkt (mit einem echten SaxPowerCoordinator, aber
ohne echten Modbus-Client) statt über den vollen Config-Flow/Setup-Pfad -
das deckt die reine Vorbelegungslogik in async_added_to_hass ab, ohne die
Slug-/Entity-ID-Generierung der echten Plattform-Registrierung nachbilden zu
müssen (siehe tests/test_integration_live.py für den vollen End-to-End-Pfad).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import State

from custom_components.sax_power.const import MAX_POWER_LIMIT, MAX_SOC, MIN_SOC
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.number import (
    SaxPowerChargeLimitNumber,
    SaxPowerMaxSocNumber,
    SaxPowerTimedChargeMinSocNumber,
)


@pytest.fixture
async def coordinator(hass):
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    coord = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
    )
    coord.data = {"soc": 50}
    yield coord
    # async_added_to_hass() below subscribes the entity as a coordinator
    # listener, which starts the periodic poll timer - shut it down again so
    # no lingering timer trips up the test harness.
    await coord.async_shutdown()


def _prepare_entity(entity, hass, entity_id: str, last_state: State | None) -> None:
    entity.hass = hass
    entity.entity_id = entity_id
    # Nur direkt instanziiert (kein echtes EntityPlatform-Setup wie im
    # vollen Integrationstest) - async_write_ha_state würde daher an der
    # Übersetzung der Einheit scheitern; für diesen reinen Vorbelegungstest
    # irrelevant.
    entity.async_write_ha_state = MagicMock()
    entity.async_get_last_state = AsyncMock(return_value=last_state)


async def test_charge_limit_seeds_from_device_register_on_fresh_install(
    hass, coordinator
) -> None:
    """Allererster Start (kein RestoreEntity-Zustand): "Max. Netzladeleistung"
    muss mit dem beim Setup gelesenen Register-44-Wert vorbelegt werden,
    nicht mit 0."""
    coordinator.data["charge_limit"] = 3000
    entity = SaxPowerChargeLimitNumber(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "number.test_charge_limit", None)

    await entity.async_added_to_hass()

    assert coordinator.max_charge_power == 3000


async def test_charge_limit_falls_back_to_device_register_when_restored_value_is_zero(
    hass, coordinator
) -> None:
    """Regressionstest für den gemeldeten Bug: Nach einem Update der
    Integration (bestehender Config Entry, RestoreEntity liefert einen alten
    0-Zustand von vor Einführung dieser Vorbelegung) darf "Max.
    Netzladeleistung" nicht dauerhaft bei 0 hängen bleiben, sondern muss
    stattdessen mit dem tatsächlichen Geräte-Registerwert initialisiert
    werden (siehe SaxPowerChargeLimitNumber-Docstring)."""
    coordinator.data["charge_limit"] = 2500
    entity = SaxPowerChargeLimitNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity, hass, "number.test_charge_limit", State("number.test_charge_limit", "0")
    )

    await entity.async_added_to_hass()

    assert coordinator.max_charge_power == 2500


async def test_charge_limit_restores_a_genuine_nonzero_value(hass, coordinator) -> None:
    """Ein echter, zuvor vom Nutzer gesetzter Wert hat weiterhin Vorrang vor
    dem Geräte-Register."""
    coordinator.data["charge_limit"] = 9999
    entity = SaxPowerChargeLimitNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_charge_limit",
        State("number.test_charge_limit", "1500"),
    )

    await entity.async_added_to_hass()

    assert coordinator.max_charge_power == 1500


async def test_timed_charge_min_soc_seeds_to_max_soc_on_fresh_install(
    hass, coordinator
) -> None:
    """Allererster Start (kein RestoreEntity-Zustand): "Netzladung Min. SOC"
    muss mit MAX_SOC (100 %) vorbelegt werden statt bei "unbekannt"/0 zu
    bleiben - andernfalls würde diese neu eingeführte Einstellung
    bestehende Netzladung-Konfigurationen ohne bewusstes Zutun des Anwenders
    blockieren (SOC wäre praktisch nie < 0 %)."""
    entity = SaxPowerTimedChargeMinSocNumber(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "number.test_timed_charge_min_soc", None)

    await entity.async_added_to_hass()

    assert coordinator.timed_charge_min_soc == MAX_SOC


async def test_timed_charge_min_soc_restores_a_genuine_value(hass, coordinator) -> None:
    """Ein echter, zuvor vom Nutzer gesetzter Wert hat Vorrang vor dem
    100-%-Vorgabewert."""
    entity = SaxPowerTimedChargeMinSocNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_timed_charge_min_soc",
        State("number.test_timed_charge_min_soc", "40"),
    )

    await entity.async_added_to_hass()

    assert coordinator.timed_charge_min_soc == 40


async def test_timed_charge_min_soc_restore_clamps_out_of_range_value(
    hass, coordinator
) -> None:
    """Ein wiederhergestellter Wert außerhalb [MIN_SOC, MAX_SOC] (z. B. ein
    korrupter oder aus einer künftigen Version stammender Zustand) wird
    geklemmt statt ungeprüft übernommen zu werden - dieser Restaurierungspfad
    ruft den Coordinator-Setter direkt auf, ohne die sonst greifende
    NumberEntity-Min/Max-Validierung des regulären Service-Call-Pfads."""
    entity = SaxPowerTimedChargeMinSocNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_timed_charge_min_soc",
        State("number.test_timed_charge_min_soc", "150"),
    )

    await entity.async_added_to_hass()

    assert coordinator.timed_charge_min_soc == MAX_SOC


async def test_max_soc_restores_a_genuine_value(hass, coordinator) -> None:
    entity = SaxPowerMaxSocNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity, hass, "number.test_max_soc", State("number.test_max_soc", "80")
    )

    await entity.async_added_to_hass()

    assert coordinator.max_soc == 80


async def test_max_soc_restore_clamps_out_of_range_value(hass, coordinator) -> None:
    """Analog zu test_timed_charge_min_soc_restore_clamps_out_of_range_value,
    hier für "Max. SOC" - ein negativer wiederhergestellter Wert wird auf
    MIN_SOC geklemmt statt als ungültiger (negativer) Wert gespeichert und
    z. B. im Zahlenfeld angezeigt zu werden. current_soc (50) liegt bei
    diesem Beispiel sowohl über dem unklemmten als auch dem geklemmten Wert,
    die Max-SOC-Sperre greift dadurch in beiden Fällen - daher wird
    async_start_sun_charge hier real ausgelöst und der Modbus-Write gemockt."""
    write_result = MagicMock()
    write_result.isError.return_value = False
    coordinator.client.write_register = AsyncMock(return_value=write_result)
    coordinator.data["ic_max_power_reference"] = 4600
    coordinator.data["ic_timeout"] = 300
    entity = SaxPowerMaxSocNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity, hass, "number.test_max_soc", State("number.test_max_soc", "-20")
    )

    await entity.async_added_to_hass()

    assert coordinator.max_soc == MIN_SOC


async def test_charge_limit_restore_clamps_out_of_range_value(
    hass, coordinator
) -> None:
    """Ein wiederhergestellter Wert über MAX_POWER_LIMIT wird geklemmt statt
    ungeprüft übernommen zu werden (siehe
    test_timed_charge_min_soc_restore_clamps_out_of_range_value)."""
    coordinator.data["charge_limit"] = 3000
    entity = SaxPowerChargeLimitNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_charge_limit",
        State("number.test_charge_limit", "99999"),
    )

    await entity.async_added_to_hass()

    assert coordinator.max_charge_power == MAX_POWER_LIMIT
