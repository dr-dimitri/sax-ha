"""Tests for the SAX Power coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.sax_power.coordinator import (
    SaxPowerCoordinator,
    apply_sunssf,
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


@pytest.mark.parametrize(
    ("raw_value", "raw_sf", "expected"),
    [
        (1200, 0, 1200),  # sf=0 -> unverändert
        (551, to_unsigned16(-1), 55.1),  # sf=-1 -> Kommastelle
        (5, 2, 500),  # sf=2 -> Zehnerpotenz
        (to_unsigned16(-300), to_unsigned16(-2), -3.0),  # negativ + negativer sf
    ],
)
def test_apply_sunssf(raw_value: int, raw_sf: int, expected: float) -> None:
    assert apply_sunssf(raw_value, raw_sf) == expected


def _make_client() -> MagicMock:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    return client


def _make_coordinator(hass, client: MagicMock) -> SaxPowerCoordinator:
    return SaxPowerCoordinator(
        hass, client, slave_id=64, slave_id_extended=40, scan_interval=10
    )


async def test_enforce_max_soc_clamps_charge_limit(hass) -> None:
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
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

    coordinator = _make_coordinator(hass, client)
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

    coordinator = _make_coordinator(hass, client)

    with pytest.raises(HomeAssistantError):
        await coordinator.async_write_register(41, 1000)


def test_parse_extended_computes_phase_sums(hass) -> None:
    """Jede Phasen-Trio-Gruppe muss zusätzlich einen berechneten Summenwert liefern
    (siehe anforderung.yaml, REQ-ALL-REGISTERS-READABLE)."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)

    # Register-Layout: internal_addr -> Rohwert. sf-Register = 0 (Faktor 1),
    # damit die erwarteten Werte den Rohwerten entsprechen.
    raw = {
        70: 1,  # SunSpec ID
        71: 2,  # SunSpec Length
        72: 30,  # Summe Phasenströme (Herstellerwert)
        73: 5,  # Strom L1
        74: 6,  # Strom L2
        75: 7,  # Strom L3
        76: 0,  # Strom Skalierung (sf=0)
        80: 230,  # Spannung L1
        81: 231,  # Spannung L2
        82: 229,  # Spannung L3
        83: 0,  # Spannung Skalierung
        84: 1000,  # Wirkleistung Summe
        85: 0,
        86: 50,  # Netzfrequenz
        87: 0,
        88: 1100,  # Scheinleistung Summe
        89: 0,
        90: 100,  # Blindleistung Summe
        91: 0,
        92: 95,  # Leistungsfaktor
        93: 0,
        95: 1000,  # Energie eingespeist
        96: 2000,  # Energie bezogen
        97: 0,
        98: 2,  # Schaltzustand (Ein)
        99: 500,  # Strom L1 (Faktor -2 fest)
        100: 600,
        101: 700,
        102: 300,  # Wirkleistung L1
        103: 400,
        104: 500,
        105: 0,
        106: 231,  # Spannung L1
        107: 232,
        108: 233,
        109: 1200,  # Summenleistung
    }

    def ext_reg(address: int) -> int:
        return raw[address]

    data = coordinator._parse_extended(ext_reg)

    assert data["ext_current_l1"] == 5
    assert data["ext_current_l2"] == 6
    assert data["ext_current_l3"] == 7
    assert data["ext_current_sum"] == 18
    assert data["ext_current_sum_native"] == 30  # Herstellerwert bleibt eigenständig

    assert data["ext_voltage_sum"] == 230 + 231 + 229

    assert data["sm_current_l1"] == 5.0  # 500 * 10**-2
    assert data["sm_current_sum"] == 5.0 + 6.0 + 7.0

    assert data["sm_power_sum"] == 300 + 400 + 500
    assert data["sm_voltage_sum"] == 231 + 232 + 233
    assert data["sm_switch_state_text"] == "Ein"
