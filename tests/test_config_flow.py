"""Tests for the SAX Power config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.const import DOMAIN

VALID_INPUT = {
    "host": "192.168.1.50",
    "port": 502,
    "slave_id_basic": 64,
    "slave_id_extended": 100,
    "scan_interval": 10,
}


async def test_user_flow_success(hass) -> None:
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.connected = True
    read_result = MagicMock()
    read_result.isError.return_value = False
    # 115 Register genügen sowohl für den Basic-Mode-Block (6 Register) als
    # auch den SunSpec-Modus-Block (115 Register), die async_setup_entry
    # nach der Config-Flow-Validierung ausliest.
    read_result.registers = [50] * 115
    client.read_holding_registers = AsyncMock(return_value=read_result)
    client.close = MagicMock()

    # Sowohl config_flow (Verbindungsvalidierung) als auch __init__
    # (async_setup_entry nach Anlage des Eintrags) instanziieren einen Client.
    with (
        patch(
            "custom_components.sax_power.config_flow.AsyncModbusTcpClient",
            return_value=client,
        ),
        patch("custom_components.sax_power.AsyncModbusTcpClient", return_value=client),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2["title"] == "SAX Power Home"
        assert result2["data"]["host"] == "192.168.1.50"


async def test_user_flow_cannot_connect(hass) -> None:
    with patch(
        "custom_components.sax_power.config_flow.AsyncModbusTcpClient"
    ) as mock_client_cls:
        client = MagicMock()
        client.connect = AsyncMock(return_value=False)
        client.close = MagicMock()
        mock_client_cls.return_value = client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_flow_updates_host(hass) -> None:
    """IP-Adresse (und andere Verbindungsdaten) müssen nach der
    Ersteinrichtung über die Oberfläche änderbar sein und persistiert
    werden (Config-Entry-Reconfigure-Flow, Kontextmenü "Neu konfigurieren")."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=VALID_INPUT, unique_id="192.168.1.50:502"
    )
    entry.add_to_hass(hass)

    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.connected = True
    read_result = MagicMock()
    read_result.isError.return_value = False
    read_result.registers = [50] * 40
    client.read_holding_registers = AsyncMock(return_value=read_result)
    client.close = MagicMock()

    with (
        patch(
            "custom_components.sax_power.config_flow.AsyncModbusTcpClient",
            return_value=client,
        ),
        patch("custom_components.sax_power.AsyncModbusTcpClient", return_value=client),
    ):
        result = await entry.start_reconfigure_flow(hass)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        new_input = {**VALID_INPUT, "host": "192.168.1.99"}
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], new_input
        )
        await hass.async_block_till_done()

        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "reconfigure_successful"
        assert entry.data["host"] == "192.168.1.99"
        assert entry.unique_id == "192.168.1.99:502"


async def test_reconfigure_flow_cannot_connect(hass) -> None:
    """Bei fehlgeschlagener Validierung müssen die bisherigen
    Verbindungsdaten des Eintrags unverändert bleiben."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=VALID_INPUT, unique_id="192.168.1.50:502"
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.sax_power.config_flow.AsyncModbusTcpClient"
    ) as mock_client_cls:
        client = MagicMock()
        client.connect = AsyncMock(return_value=False)
        client.close = MagicMock()
        mock_client_cls.return_value = client

        result = await entry.start_reconfigure_flow(hass)
        new_input = {**VALID_INPUT, "host": "192.168.1.99"}
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], new_input
        )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_connect"}
        assert entry.data["host"] == "192.168.1.50"
