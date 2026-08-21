"""Tests für die gemeinsame Geräte-/Entity-Identität (entity.py, siehe
anforderung.yaml, REQ-STABLE-DEVICE-IDENTITY).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    MockEntityPlatform,
)

from custom_components.sax_power.const import DOMAIN
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.entity import SaxPowerEntity

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

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, ENTRY_ID)})
    assert device is not None
    device_registry.async_update_device(device.id, name_by_user="Keller Speicher")

    entity_registry = er.async_get(hass)
    registry_entry = entity_registry.async_get(entity.entity_id)
    assert registry_entry is not None

    regenerated_entity_id = entity_registry.async_regenerate_entity_id(registry_entry)

    assert regenerated_entity_id == "sensor.sax_power_soc"
