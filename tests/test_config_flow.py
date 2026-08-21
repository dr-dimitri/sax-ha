"""Tests for the SAX Power config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.config_flow import _expected_entity_count
from custom_components.sax_power.const import (
    CONF_PRICE_SENSOR,
    CONF_PRICE_STRATEGY,
    CONF_PRICE_UNIT,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    DOMAIN,
    PRICE_STRATEGY_SMART,
    PRICE_UNIT_CT_KWH,
    REG_SOC,
    REG_SUN_SERIAL_HI,
    REG_SUN_SERIAL_LO,
    REG_SUN_VERSION_GATEWAY,
    REG_SUN_VERSION_MASTER,
)

VALID_INPUT = {
    "host": "192.168.1.50",
    "port": 502,
    "slave_id_basic": 64,
    "slave_id_extended": 100,
    "scan_interval": 10,
}


async def test_user_flow_success(hass) -> None:
    """Ersteinrichtung: Nach erfolgreicher Verbindungsvalidierung folgt der
    zweite, optionale Schritt "grid_charge" - wird er unverändert (leer)
    abgeschickt, gelten die Hard-Defaults aus const.py (deaktiviert,
    Zeitfenster 00:00-00:05), siehe anforderung.yaml REQ-TIMED-SOC-CHARGE.
    Danach folgt der dritte, optionale Schritt "dashboard" (siehe
    anforderung.yaml REQ-BUNDLED-DASHBOARD) - unverändert abgeschickt bleibt
    dessen Default (Dashboard anlegen) aktiv."""
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
        assert result["step_id"] == "user"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] == "grid_charge"

        result3 = await hass.config_entries.flow.async_configure(result2["flow_id"], {})
        assert result3["type"] == FlowResultType.FORM
        assert result3["step_id"] == "dashboard"

        result4 = await hass.config_entries.flow.async_configure(result3["flow_id"], {})
        assert result4["type"] == FlowResultType.FORM
        assert result4["step_id"] == "finish"

        result5 = await hass.config_entries.flow.async_configure(result4["flow_id"], {})
        assert result5["type"] == FlowResultType.CREATE_ENTRY
        assert result5["title"] == "SAX Power Home"
        assert result5["data"]["host"] == "192.168.1.50"
        assert result5["data"]["timed_charge_enabled"] is False
        assert result5["data"]["timed_charge_start"] == "00:00:00"
        assert result5["data"]["timed_charge_end"] == "00:05:00"
        assert result5["data"]["create_dashboard"] is True


async def test_user_flow_grid_charge_step_accepts_explicit_values(hass) -> None:
    """Werden im zweiten Schritt explizite Werte angegeben, landen sie
    unverändert in den Config-Entry-Daten."""
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.connected = True
    read_result = MagicMock()
    read_result.isError.return_value = False
    read_result.registers = [50] * 115
    client.read_holding_registers = AsyncMock(return_value=read_result)
    client.close = MagicMock()

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
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                "timed_charge_enabled": True,
                "timed_charge_start": "22:00:00",
                "timed_charge_end": "06:00:00",
            },
        )
        assert result3["type"] == FlowResultType.FORM
        assert result3["step_id"] == "dashboard"

        result4 = await hass.config_entries.flow.async_configure(result3["flow_id"], {})
        assert result4["type"] == FlowResultType.FORM
        assert result4["step_id"] == "finish"

        result5 = await hass.config_entries.flow.async_configure(result4["flow_id"], {})
        assert result5["type"] == FlowResultType.CREATE_ENTRY
        assert result5["data"]["timed_charge_enabled"] is True
        assert result5["data"]["timed_charge_start"] == "22:00:00"
        assert result5["data"]["timed_charge_end"] == "06:00:00"


async def test_user_flow_dashboard_step_can_be_declined(hass) -> None:
    """Der dritte Schritt ("dashboard") lässt sich abwählen - der Wert landet
    dann als False im Config Entry, siehe anforderung.yaml
    REQ-BUNDLED-DASHBOARD."""
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.connected = True
    read_result = MagicMock()
    read_result.isError.return_value = False
    read_result.registers = [50] * 115
    client.read_holding_registers = AsyncMock(return_value=read_result)
    client.close = MagicMock()

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
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        result3 = await hass.config_entries.flow.async_configure(result2["flow_id"], {})
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"], {"create_dashboard": False}
        )
        assert result4["type"] == FlowResultType.FORM
        assert result4["step_id"] == "finish"

        result5 = await hass.config_entries.flow.async_configure(result4["flow_id"], {})
        assert result5["type"] == FlowResultType.CREATE_ENTRY
        assert result5["data"]["create_dashboard"] is False


async def test_finish_step_shows_summary_placeholders(hass) -> None:
    """Vierter, abschließender Schritt der Ersteinrichtung ("finish", siehe
    anforderung.yaml REQ-SETUP-FINISH-SUMMARY): fasst Firmware, Seriennummer,
    SunSpec-Erreichbarkeit und Entity-Anzahl als description_placeholders
    zusammen, bevor der Config Entry angelegt wird."""
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.connected = True
    read_result = MagicMock()
    read_result.isError.return_value = False
    registers = [50] * 115
    registers[REG_SUN_VERSION_MASTER] = 61
    registers[REG_SUN_VERSION_GATEWAY] = 54
    registers[REG_SUN_SERIAL_HI] = 0
    registers[REG_SUN_SERIAL_LO] = 12345
    read_result.registers = registers
    client.read_holding_registers = AsyncMock(return_value=read_result)
    client.close = MagicMock()

    with patch(
        "custom_components.sax_power.config_flow.AsyncModbusTcpClient",
        return_value=client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        result3 = await hass.config_entries.flow.async_configure(result2["flow_id"], {})
        result4 = await hass.config_entries.flow.async_configure(result3["flow_id"], {})

        assert result4["type"] == FlowResultType.FORM
        assert result4["step_id"] == "finish"
        placeholders = result4["description_placeholders"]
        assert placeholders["firmware"] == "Master V61 / Gateway V54"
        assert placeholders["serial_number"] == "12345"
        assert placeholders["sunspec_status"] == "Erreichbar"
        assert placeholders["entity_count"] == str(_expected_entity_count())


async def test_finish_step_marks_sunspec_unavailable(hass) -> None:
    """Ist der SunSpec-Modus-Block beim Abschluss-Read nicht erreichbar (z. B.
    weil das Gerät die Slave-ID 100 ablehnt), zeigt die Abschlussseite
    "Nicht erreichbar" statt den Flow abzubrechen - analog zu
    REQ-EXTENDED-MODE-RESILIENCE, das dieselbe Toleranz für den laufenden
    Betrieb vorschreibt."""
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.connected = True

    soc_result = MagicMock()
    soc_result.isError.return_value = False
    soc_result.registers = [50]

    extended_result = MagicMock()
    extended_result.isError.return_value = True

    async def _read_holding_registers(*, address, count, device_id):
        if address == REG_SOC:
            return soc_result
        return extended_result

    client.read_holding_registers = AsyncMock(side_effect=_read_holding_registers)
    client.close = MagicMock()

    with patch(
        "custom_components.sax_power.config_flow.AsyncModbusTcpClient",
        return_value=client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        result3 = await hass.config_entries.flow.async_configure(result2["flow_id"], {})
        result4 = await hass.config_entries.flow.async_configure(result3["flow_id"], {})

        assert result4["type"] == FlowResultType.FORM
        assert result4["step_id"] == "finish"
        placeholders = result4["description_placeholders"]
        assert placeholders["sunspec_status"] == "Nicht erreichbar"
        assert "Nicht verfügbar" in placeholders["firmware"]
        assert "Nicht verfügbar" in placeholders["serial_number"]


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


async def test_options_flow_stores_price_configuration(hass) -> None:
    """Options Flow: Auswahl von Strompreis-/PV-Prognose-Sensor und deren
    Interpretation, siehe anforderung.yaml REQ-DYNAMIC-PRICE-CHARGE."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=VALID_INPUT, unique_id="192.168.1.50:502"
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_PRICE_UNIT: PRICE_UNIT_CT_KWH,
            CONF_PRICE_STRATEGY: PRICE_STRATEGY_SMART,
            CONF_PV_FORECAST_SENSOR: "sensor.pv_prognose_morgen",
            CONF_PV_FORECAST_FACTOR: 70,
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_PRICE_SENSOR] == "sensor.strompreis"
    assert entry.options[CONF_PRICE_UNIT] == PRICE_UNIT_CT_KWH
    assert entry.options[CONF_PRICE_STRATEGY] == PRICE_STRATEGY_SMART
    assert entry.options[CONF_PV_FORECAST_FACTOR] == 70


async def test_options_flow_is_prefilled_with_current_options(hass) -> None:
    """Beim erneuten Öffnen sind die gespeicherten Werte vorbelegt, damit
    eine kleine Änderung nicht das ganze Formular neu ausfüllen muss."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        options={CONF_PRICE_SENSOR: "sensor.strompreis"},
        unique_id="192.168.1.50:502",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    suggested = {
        key.schema: key.description["suggested_value"]
        for key in result["data_schema"].schema
        if isinstance(key.description, dict) and "suggested_value" in key.description
    }
    assert suggested[CONF_PRICE_SENSOR] == "sensor.strompreis"
