"""Tests for the SAX Power coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.sax_power.coordinator import (
    SaxPowerCoordinator,
    to_signed16,
    to_unsigned16,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(0, 0), (100, 100), (32767, 32767), (32768, -32768), (65535, -1)],
)
def test_to_signed16(raw: int, expected: int) -> None:
    assert to_signed16(raw) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, 0), (100, 100), (-1, 65535), (-32768, 32768)],
)
def test_to_unsigned16(value: int, expected: int) -> None:
    assert to_unsigned16(value) == expected


def _make_client() -> MagicMock:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    return client


async def test_enforce_max_soc_clamps_charge_limit(hass) -> None:
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = SaxPowerCoordinator(hass, client, slave_id=64, scan_interval=10)
    await coordinator.async_set_max_soc(80)

    data = {"soc": 85, "charge_limit": 3000}
    await coordinator._async_enforce_max_soc(data)

    assert data["charge_limit"] == 0
    client.write_register.assert_awaited_once()
    assert coordinator._max_soc_clamped is True


async def test_enforce_max_soc_restores_charge_limit(hass) -> None:
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = SaxPowerCoordinator(hass, client, slave_id=64, scan_interval=10)
    coordinator._max_soc = 80
    coordinator._max_soc_clamped = True
    coordinator._pre_clamp_charge_limit = 3000

    data = {"soc": 70, "charge_limit": 0}
    await coordinator._async_enforce_max_soc(data)

    assert data["charge_limit"] == 3000
    assert coordinator._max_soc_clamped is False


async def test_async_write_register_raises_on_modbus_error(hass) -> None:
    from homeassistant.exceptions import HomeAssistantError

    client = _make_client()
    error_result = MagicMock()
    error_result.isError.return_value = True
    client.write_register = AsyncMock(return_value=error_result)

    coordinator = SaxPowerCoordinator(hass, client, slave_id=64, scan_interval=10)

    with pytest.raises(HomeAssistantError):
        await coordinator.async_write_register(41, 1000)
