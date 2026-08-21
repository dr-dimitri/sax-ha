"""Tests für die gemeinsame Geräte-/Entity-Identität (entity.py, siehe
anforderung.yaml, REQ-STABLE-DEVICE-IDENTITY).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

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
