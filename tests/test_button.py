"""Tests für den Dashboard-Reinstall-Button (button.py, siehe
anforderung.yaml, REQ-BUNDLED-DASHBOARD).

Instanziiert die Entity direkt (wie tests/test_number.py) statt über den
vollen Config-Flow/Setup-Pfad - der reine Kern hier ist, dass der Button
async_create_dashboard mit force=True für den richtigen Entry aufruft.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.button import SaxPowerReinstallDashboardButton
from custom_components.sax_power.const import DOMAIN
from custom_components.sax_power.coordinator import SaxPowerCoordinator

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


async def test_press_reinstalls_dashboard_for_own_entry(hass, coordinator) -> None:
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)

    button = SaxPowerReinstallDashboardButton(coordinator, ENTRY_ID)
    button.hass = hass

    with patch(
        "custom_components.sax_power.button.async_create_dashboard",
        new=AsyncMock(),
    ) as mock_create:
        await button.async_press()

    mock_create.assert_awaited_once_with(hass, entry, force=True)


async def test_press_without_config_entry_raises(hass, coordinator) -> None:
    button = SaxPowerReinstallDashboardButton(coordinator, "unbekannter_entry")
    button.hass = hass

    with pytest.raises(HomeAssistantError):
        await button.async_press()
