"""Tests für die gemeinsame Geräte-/Entity-Identität (entity.py, siehe
anforderung.yaml, REQ-STABLE-DEVICE-IDENTITY).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import async_get_platforms

from custom_components.sax_power.const import DOMAIN
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.entity import SaxPowerEntity
from tests.ha import (
    MockConfigEntry,
    MockEntityPlatform,
)
from tests.test_integration_live import (
    _build_basic_registers,
    _build_extended_registers,
    _modbus_server,
)

ENTRY_ID = "test_entry_id"


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
        entry_id=ENTRY_ID,
    )
    yield coord
    await coord.async_shutdown()


async def test_device_info_ignores_a_renamed_config_entry_title(
    hass, coordinator
) -> None:
    """Ein über "Umbenennen" geänderter Entry-Titel darf weder den
    Gerätenamen noch die device_registry-identifiers beeinflussen - beide
    werden ausschließlich aus der internen, unveränderlichen entry_id bzw.
    einer festen Konstante gebildet, nie aus einem vom Anwender änderbaren
    Namen (siehe REQ-STABLE-DEVICE-IDENTITY)."""
    entry = MockConfigEntry(
        domain=DOMAIN, entry_id=ENTRY_ID, title="Mein Speicher im Keller"
    )
    entry.add_to_hass(hass)

    entity = SaxPowerEntity(coordinator, ENTRY_ID)

    assert entity._attr_device_info["name"] == "SAX Power Home"
    assert entity._attr_device_info["identifiers"] == {(DOMAIN, ENTRY_ID)}


async def test_entity_id_survives_a_device_rename_with_entity_id_update(
    hass, coordinator
) -> None:
    """Home Assistant bietet nach der Ersteinrichtung an, das neu angelegte
    Gerät umzubenennen und einem Bereich zuzuordnen; aktiviert der Anwender
    dabei zusätzlich "Entity-IDs aktualisieren", regeneriert Home Assistant
    (async_regenerate_entity_id, der Mechanismus hinter dieser Option) sonst
    jede entity_id ohne explizit gesetzte suggested_object_id neu aus dem
    (jetzt geänderten) Gerätenamen - das bereits angelegte, mitgelieferte
    Dashboard referenziert zu diesem Zeitpunkt aber schon die ursprüngliche
    entity_id fest und würde die Entity nicht mehr finden. Über
    SaxPowerEntity._assign_ids explizit vorgegebene entity_ids müssen daher
    auch diese Regeneration unverändert überstehen (siehe
    REQ-STABLE-DEVICE-IDENTITY)."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, title="SAX Power Home")
    entry.add_to_hass(hass)

    entity = SaxPowerEntity(coordinator, ENTRY_ID)
    entity._assign_ids("sensor", "soc")

    platform = MockEntityPlatform(hass, domain="sensor", platform_name=DOMAIN)
    platform.config_entry = entry
    await platform.async_add_entities([entity])

    assert entity.entity_id == "sensor.sax_power_soc"

    entity_registry = er.async_get(hass)
    registry_entry = entity_registry.async_get(entity.entity_id)
    assert registry_entry is not None
    assert registry_entry.device_id is not None
    dr.async_get(hass).async_update_device(
        registry_entry.device_id, name_by_user="Keller Speicher"
    )

    regenerated_entity_id = entity_registry.async_regenerate_entity_id(registry_entry)

    assert regenerated_entity_id == "sensor.sax_power_soc"


async def test_explicit_entity_id_change_preserves_state_and_subscriptions(
    hass: HomeAssistant, socket_enabled: None, unused_tcp_port: int
) -> None:
    """REQ-STABLE-DEVICE-IDENTITY: Seit HA 2026.11 läuft jede Entität weiter."""
    server = _modbus_server(
        unused_tcp_port, _build_basic_registers(), _build_extended_registers()
    )
    await server.serve_forever(background=True)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "127.0.0.1",
            "port": unused_tcp_port,
            "slave_id_basic": 64,
            "slave_id_extended": 100,
            "scan_interval": 3600,
        },
    )
    entry.add_to_hass(hass)
    try:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        platforms = {p.domain: p for p in async_get_platforms(hass, DOMAIN)}
        removed = MagicMock()
        for domain, suffix in (
            ("sensor", "soc"),
            ("sensor", "energy_charged"),
            ("switch", "bridge_charge_enabled"),
            ("time", "timed_charge_start"),
        ):
            entity_id = f"{domain}.sax_power_{suffix}"
            entity = platforms[domain].entities[entity_id]
            state = hass.states.get(entity_id).state
            entity.async_on_remove(removed)
            new_id = f"{domain}.mein_{suffix}"
            updated = registry.async_update_entity(entity_id, new_entity_id=new_id)
            await hass.async_block_till_done()
            assert updated.unique_id == entity.unique_id
            assert hass.states.get(entity_id) is None
            assert platforms[domain].entities[new_id] is entity
            assert hass.states.get(new_id).state == state
        if hasattr(Entity, "async_entity_id_changed"):
            removed.assert_not_called()
        await hass.services.async_call(
            "time",
            "set_value",
            {"entity_id": "time.mein_timed_charge_start", "time": "06:15:00"},
            blocking=True,
        )
        assert hass.states.get("time.mein_timed_charge_start").state == "06:15:00"
    finally:
        await hass.config_entries.async_unload(entry.entry_id)
        await server.shutdown()
