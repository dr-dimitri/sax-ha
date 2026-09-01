"""Tests for the SAX Power config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
import voluptuous_serialize
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power import config_flow
from custom_components.sax_power.config_flow import _expected_entity_count
from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_INVESTMENT_COST,
    CONF_ECONOMICS_PRIOR_RESULT,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_ECONOMICS_WINDOW_END,
    CONF_ECONOMICS_WINDOW_PRICE,
    CONF_ECONOMICS_WINDOW_START,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    DOMAIN,
    ECONOMICS_TOU_WINDOW_KEYS,
    PRICE_UNIT_CT_KWH,
    REG_SOC,
    REG_SUN_SERIAL_HI,
    REG_SUN_SERIAL_LO,
    REG_SUN_VERSION_GATEWAY,
    REG_SUN_VERSION_MASTER,
    economics_tou_window_key,
)
from custom_components.sax_power.domain.tariff import TariffType

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
    client.write_register = AsyncMock(return_value=read_result)
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
    client.write_register = AsyncMock(return_value=read_result)
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
    client.write_register = AsyncMock(return_value=read_result)
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


async def test_finish_step_handles_identity_sentinels(hass) -> None:
    """REQ-SUNSPEC-DATATYPES: meldet das Gerät für Firmware-/Seriennummern-
    register den "not implemented"-Sentinel 0xFFFF, zeigt die Abschlussseite
    "unbekannt" statt "V65535" oder "VNone". Der Config Flow nutzt dafür
    denselben Decoder wie der Coordinator (domain.sunspec.decode_identity)."""
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.connected = True
    read_result = MagicMock()
    read_result.isError.return_value = False
    registers = [50] * 115
    registers[REG_SUN_VERSION_MASTER] = 0xFFFF
    registers[REG_SUN_VERSION_GATEWAY] = 0xFFFF
    registers[REG_SUN_SERIAL_HI] = 0xFFFF
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

        placeholders = result4["description_placeholders"]
        assert placeholders["sunspec_status"] == "Erreichbar"
        assert placeholders["firmware"] == "Master unbekannt / Gateway unbekannt"
        assert placeholders["serial_number"] == "unbekannt"


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


async def test_dhcp_discovery_prefills_host(hass) -> None:
    """DHCP-Discovery (siehe anforderung.yaml REQ-DHCP-DISCOVERY) leitet in
    den normalen "user"-Schritt weiter und belegt dessen Host-Feld mit der
    entdeckten IP vor; die restliche Ersteinrichtung (Verbindungsprüfung,
    grid_charge/dashboard/finish) läuft danach unverändert weiter."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.77",
            hostname="sax-1234",
            macaddress="aabbccddeeff",
        ),
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    host_key = next(key for key in result["data_schema"].schema if key == "host")
    assert host_key.description == {"suggested_value": "192.168.1.77"}

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
        discovered_input = {**VALID_INPUT, "host": "192.168.1.77"}
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], discovered_input
        )
        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] == "grid_charge"


async def test_dhcp_discovery_aborts_if_host_already_configured(hass) -> None:
    """Ein bereits konfigurierter Speicher darf nicht erneut als "Erkannt"
    angezeigt werden, auch wenn Port oder Slave-IDs vom Discovery-Kontext
    abweichen - der Abgleich erfolgt allein über den Host."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=VALID_INPUT, unique_id="192.168.1.50:502"
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.50",
            hostname="sax-1234",
            macaddress="aabbccddeeff",
        ),
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_dhcp_discovery_deduplicates_repeated_broadcasts(hass) -> None:
    """SAX Speicher senden ihren DHCP-Lease wiederholt; ein zweiter
    Broadcast desselben Geräts (gleiche MAC-Adresse) darf keine zweite
    "Erkannt"-Karte erzeugen, solange der erste Discovery-Flow noch läuft."""
    first = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.77",
            hostname="sax-1234",
            macaddress="aabbccddeeff",
        ),
    )
    assert first["type"] == FlowResultType.FORM

    second = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.78",
            hostname="sax-1234",
            macaddress="aabbccddeeff",
        ),
    )
    assert second["type"] == FlowResultType.ABORT
    assert second["reason"] == "already_in_progress"


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
            CONF_PV_FORECAST_SENSOR: "sensor.pv_prognose_morgen",
            CONF_PV_FORECAST_FACTOR: 70,
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_PRICE_SENSOR] == "sensor.strompreis"
    assert entry.options[CONF_PRICE_UNIT] == PRICE_UNIT_CT_KWH
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


# --------------------------------------------------------------------------
# Wirtschaftlichkeit: Tarifkonfiguration (siehe anforderung.yaml,
# REQ-ECONOMICS-TARIFFS)
# --------------------------------------------------------------------------
def _economics_entry(hass, options: dict | None = None) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        options=options or {},
        unique_id="192.168.1.50:502",
    )
    entry.add_to_hass(hass)
    return entry


def _empty_windows() -> dict:
    return {key: {} for key in ECONOMICS_TOU_WINDOW_KEYS}


async def test_options_flow_defaults_to_a_disabled_tariff(hass) -> None:
    """Ohne Angabe bleibt die Wirtschaftlichkeitsauswertung aus und der
    Flow endet wie bisher nach einem einzigen Schritt."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_PRICE_SENSOR: "sensor.strompreis"}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_TARIFF_TYPE] == TariffType.DISABLED.value
    assert CONF_ECONOMICS_FEED_IN_PRICE not in entry.options


async def test_options_flow_stores_a_fixed_tariff(hass) -> None:
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value},
    )
    assert result["step_id"] == "economics_fixed"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.3421,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_TARIFF_TYPE] == TariffType.FIXED.value
    assert entry.options[CONF_ECONOMICS_FEED_IN_PRICE] == 0.0786
    assert entry.options[CONF_ECONOMICS_FIXED_IMPORT_PRICE] == 0.3421


@pytest.mark.parametrize(
    ("tariff_type", "step_id", "second_page"),
    [
        pytest.param(
            TariffType.FIXED,
            "economics_fixed",
            {CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.3421},
            id="fixed",
        ),
        pytest.param(TariffType.DYNAMIC, "economics_dynamic", {}, id="dynamic"),
        pytest.param(
            TariffType.TIME_OF_USE,
            "economics_time_of_use",
            {CONF_ECONOMICS_TOU_BASE_PRICE: 0.34, **_empty_windows()},
            id="time_of_use",
        ),
    ],
)
async def test_repeated_first_page_does_not_show_raw_schema_errors(
    hass, tariff_type: TariffType, step_id: str, second_page: dict
) -> None:
    """Schickt das Frontend die erste Seite ein zweites Mal ab (Doppelklick
    bzw. Enter im Eingabefeld plus Klick auf "Absenden"), prüft Home
    Assistant diese Werte gegen das Schema der bereits erreichten
    Folgeseite. Ohne Behandlung sah der Anwender eine Wand aus "extra keys
    not allowed @ data[...]"-Rohmeldungen (Anwenderbericht zu #129)."""
    entry = _economics_entry(hass)
    first_page = {
        CONF_PRICE_UNIT: PRICE_UNIT_CT_KWH,
        CONF_PV_FORECAST_SENSOR: "sensor.pv_prognose",
        CONF_PV_FORECAST_FACTOR: 100,
        CONF_ECONOMICS_TARIFF_TYPE: tariff_type.value,
        CONF_ECONOMICS_INVESTMENT_COST: 8500.0,
    }
    if tariff_type is TariffType.DYNAMIC:
        first_page[CONF_PRICE_SENSOR] = "sensor.strompreis"

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], first_page
    )
    assert result["step_id"] == step_id

    # Zweiter Versand derselben ersten Seite: derselbe Schritt, kein Fehler.
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], first_page
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == step_id
    assert not result["errors"]

    # Danach lässt sich der Flow normal zu Ende führen.
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**second_page, CONF_ECONOMICS_FEED_IN_PRICE: 0.0786}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_INVESTMENT_COST] == 8500.0
    assert entry.options[CONF_ECONOMICS_FEED_IN_PRICE] == 0.0786
    assert entry.options[CONF_ECONOMICS_TARIFF_TYPE] == tariff_type.value
    # Fremde Schlüssel der ersten Seite landen nicht doppelt im Eintrag.
    assert entry.options[CONF_PV_FORECAST_FACTOR] == 100


async def test_repeated_first_page_is_validated_against_its_own_schema(hass) -> None:
    """Auf diesem Weg wendet Home Assistant STEP_OPTIONS_SCHEMA nicht mehr
    an - der Schritt prüft deshalb selbst. Ungültige Werte dürfen weder
    ungeprüft in entry.options landen noch den Flow mit einem ValueError
    aus einem unbekannten Tarifmodell abbrechen (Review-Befund)."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value},
    )
    assert result["step_id"] == "economics_fixed"

    # Von Hand geschickte "erste Seite" mit unbekanntem Tarifmodell und
    # fremdem Schlüssel: wird nicht als Wiederholung akzeptiert, sondern
    # wie eine unvollständige Eingabe dieser Seite behandelt.
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_TARIFF_TYPE: "kein_tarif",
            CONF_PV_FORECAST_FACTOR: "keine-zahl",
            "voellig_fremd": "x",
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "economics_fixed"
    assert result["errors"] == {
        CONF_ECONOMICS_FEED_IN_PRICE: "economics_price_required",
        CONF_ECONOMICS_FIXED_IMPORT_PRICE: "economics_price_required",
    }
    assert entry.options == {}


@pytest.mark.parametrize(
    ("tariff_type", "step_id", "user_input", "expected_errors"),
    [
        pytest.param(
            TariffType.FIXED,
            "economics_fixed",
            {CONF_ECONOMICS_FEED_IN_PRICE: 0.0786},
            {CONF_ECONOMICS_FIXED_IMPORT_PRICE: "economics_price_required"},
            id="fixed_without_import_price",
        ),
        pytest.param(
            TariffType.FIXED,
            "economics_fixed",
            {},
            {
                CONF_ECONOMICS_FEED_IN_PRICE: "economics_price_required",
                CONF_ECONOMICS_FIXED_IMPORT_PRICE: "economics_price_required",
            },
            id="fixed_without_any_price",
        ),
        pytest.param(
            TariffType.TIME_OF_USE,
            "economics_time_of_use",
            {CONF_ECONOMICS_FEED_IN_PRICE: 0.0786, **_empty_windows()},
            {CONF_ECONOMICS_TOU_BASE_PRICE: "economics_price_required"},
            id="time_of_use_without_base_price",
        ),
    ],
)
async def test_missing_tariff_price_is_reported_on_its_field(
    hass,
    tariff_type: TariffType,
    step_id: str,
    user_input: dict,
    expected_errors: dict,
) -> None:
    """Die Preisfelder sind im Schema optional, damit ein fehlender Wert
    als erklärter Feldfehler erscheint statt als unübersetztes "required
    key not provided" - Pflicht bleiben sie trotzdem."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ECONOMICS_TARIFF_TYPE: tariff_type.value}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == step_id
    assert result["errors"] == expected_errors
    assert CONF_ECONOMICS_TARIFF_TYPE not in entry.options


async def test_options_flow_stores_time_of_use_windows(hass) -> None:
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value},
    )
    assert result["step_id"] == "economics_time_of_use"

    windows = _empty_windows()
    windows[economics_tou_window_key(1)] = {
        CONF_ECONOMICS_WINDOW_START: "22:00:00",
        CONF_ECONOMICS_WINDOW_END: "06:00:00",
        CONF_ECONOMICS_WINDOW_PRICE: 0.21,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
            **windows,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_TOU_BASE_PRICE] == 0.32
    stored = entry.options[economics_tou_window_key(1)]
    assert stored[CONF_ECONOMICS_WINDOW_START] == "22:00:00"
    assert stored[CONF_ECONOMICS_WINDOW_PRICE] == 0.21


async def test_options_flow_rejects_an_incomplete_window(hass) -> None:
    """Eine Gruppe ist entweder ganz leer oder vollständig befüllt."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value},
    )
    windows = _empty_windows()
    windows[economics_tou_window_key(2)] = {CONF_ECONOMICS_WINDOW_START: "22:00:00"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
            **windows,
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "economics_tou_window_incomplete"}
    assert entry.options == {}


async def test_options_flow_rejects_overlapping_windows(hass) -> None:
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value},
    )
    windows = _empty_windows()
    windows[economics_tou_window_key(1)] = {
        CONF_ECONOMICS_WINDOW_START: "06:00:00",
        CONF_ECONOMICS_WINDOW_END: "10:00:00",
        CONF_ECONOMICS_WINDOW_PRICE: 0.4,
    }
    windows[economics_tou_window_key(2)] = {
        CONF_ECONOMICS_WINDOW_START: "09:00:00",
        CONF_ECONOMICS_WINDOW_END: "12:00:00",
        CONF_ECONOMICS_WINDOW_PRICE: 0.5,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
            **windows,
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "economics_tou_window_overlap"}


async def test_options_flow_rejects_a_zero_length_window(hass) -> None:
    """`start == end` ist ungültig und bedeutet nicht "ganzer Tag"."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value},
    )
    windows = _empty_windows()
    windows[economics_tou_window_key(1)] = {
        CONF_ECONOMICS_WINDOW_START: "06:00:00",
        CONF_ECONOMICS_WINDOW_END: "06:00:00",
        CONF_ECONOMICS_WINDOW_PRICE: 0.4,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
            **windows,
        },
    )

    assert result["errors"] == {"base": "economics_tou_window_zero_length"}


async def test_dynamic_tariff_requires_the_price_sensor(hass) -> None:
    """Der dynamische Tarif hat bewusst keine eigene Preisquelle - ohne
    ausgewählten Strompreis-Sensor lehnt der Flow das Speichern ab."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {CONF_PRICE_SENSOR: "economics_price_sensor_required"}
    assert entry.options == {}


async def test_dynamic_tariff_reuses_the_configured_price_sensor(hass) -> None:
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_PRICE_UNIT: PRICE_UNIT_CT_KWH,
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
        },
    )
    assert result["step_id"] == "economics_dynamic"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ECONOMICS_FEED_IN_PRICE: 0.0786}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_PRICE_SENSOR] == "sensor.strompreis"
    assert entry.options[CONF_PRICE_UNIT] == PRICE_UNIT_CT_KWH
    assert CONF_ECONOMICS_FIXED_IMPORT_PRICE not in entry.options


async def test_switching_the_tariff_type_drops_stale_values(hass) -> None:
    """Beim Wechsel der Tarifart dürfen keine irrelevanten Altwerte in
    entry.options zurückbleiben - sonst würden sie bei einem späteren
    Rückwechsel unbemerkt wieder gelten."""
    entry = _economics_entry(
        hass,
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
            economics_tou_window_key(1): {
                CONF_ECONOMICS_WINDOW_START: "22:00:00",
                CONF_ECONOMICS_WINDOW_END: "06:00:00",
                CONF_ECONOMICS_WINDOW_PRICE: 0.21,
            },
        },
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 0.09,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.34,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert CONF_ECONOMICS_TOU_BASE_PRICE not in entry.options
    assert economics_tou_window_key(1) not in entry.options


async def test_disabling_the_tariff_drops_all_economics_values(hass) -> None:
    entry = _economics_entry(
        hass,
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.34,
            CONF_PRICE_SENSOR: "sensor.strompreis",
        },
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_PRICE_SENSOR: "sensor.strompreis",
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DISABLED.value,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_TARIFF_TYPE] == TariffType.DISABLED.value
    assert CONF_ECONOMICS_FEED_IN_PRICE not in entry.options
    assert CONF_ECONOMICS_FIXED_IMPORT_PRICE not in entry.options
    # Die übrige Options-Flow-Konfiguration bleibt unangetastet.
    assert entry.options[CONF_PRICE_SENSOR] == "sensor.strompreis"


# --------------------------------------------------------------------------
# ROI/Amortisation: Investitionskosten (siehe anforderung.yaml,
# REQ-ECONOMICS-AMORTIZATION)
# --------------------------------------------------------------------------
async def test_options_flow_stores_the_investment_cost(hass) -> None:
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DISABLED.value,
            CONF_ECONOMICS_INVESTMENT_COST: 8500.0,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_INVESTMENT_COST] == 8500.0


async def test_missing_price_sensor_error_keeps_the_other_edits(hass) -> None:
    """Der Fehler economics_price_sensor_required darf nur den fehlenden
    Sensor anmahnen, nicht die übrigen Änderungen derselben Seite
    verwerfen - sonst müsste der Anwender Tarifart, PV-Prognose,
    Investitionskosten und Vorlauf erneut eintragen."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC.value,
            CONF_PV_FORECAST_FACTOR: 80,
            CONF_ECONOMICS_INVESTMENT_COST: 8500.0,
            CONF_ECONOMICS_PRIOR_RESULT: 1250.0,
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {CONF_PRICE_SENSOR: "economics_price_sensor_required"}

    suggested = {
        key.schema: key.description["suggested_value"]
        for key in result["data_schema"].schema
        if isinstance(key.description, dict) and "suggested_value" in key.description
    }
    assert suggested[CONF_ECONOMICS_TARIFF_TYPE] == TariffType.DYNAMIC.value
    assert suggested[CONF_PV_FORECAST_FACTOR] == 80
    assert suggested[CONF_ECONOMICS_INVESTMENT_COST] == 8500.0
    assert suggested[CONF_ECONOMICS_PRIOR_RESULT] == 1250.0


async def test_options_flow_stores_the_prior_result(hass) -> None:
    """Der vor der Integration erwirtschaftete Ertrag steht auf derselben
    Seite wie die Investitionskosten und ist ebenso optional
    (REQ-ECONOMICS-AMORTIZATION)."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DISABLED.value,
            CONF_ECONOMICS_INVESTMENT_COST: 8500.0,
            CONF_ECONOMICS_PRIOR_RESULT: 1250.0,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_PRIOR_RESULT] == 1250.0


async def test_prior_result_survives_a_tariff_type_switch(hass) -> None:
    """Wie die Investitionskosten ist der Vorlauf unabhängig von der
    Tarifart und darf bei einem Tarifwechsel nicht verworfen werden."""
    entry = _economics_entry(
        hass,
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.34,
            CONF_ECONOMICS_PRIOR_RESULT: 1250.0,
        },
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DISABLED.value,
            CONF_ECONOMICS_PRIOR_RESULT: 1250.0,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_PRIOR_RESULT] == 1250.0


async def test_investment_cost_survives_a_tariff_type_switch(hass) -> None:
    """Die Investitionskosten sind unabhängig von der Tarifart und dürfen
    bei einem Tarifwechsel nicht wie die tarifspezifischen Felder aus
    ECONOMICS_OPTION_KEYS verworfen werden."""
    entry = _economics_entry(
        hass,
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.34,
            CONF_ECONOMICS_INVESTMENT_COST: 8500.0,
        },
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DISABLED.value,
            CONF_ECONOMICS_INVESTMENT_COST: 8500.0,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_INVESTMENT_COST] == 8500.0


async def test_investment_cost_can_be_removed_without_touching_the_tariff(
    hass,
) -> None:
    entry = _economics_entry(
        hass,
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.34,
            CONF_ECONOMICS_INVESTMENT_COST: 8500.0,
        },
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.34,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert CONF_ECONOMICS_INVESTMENT_COST not in entry.options
    assert entry.options[CONF_ECONOMICS_FIXED_IMPORT_PRICE] == 0.34


# --------------------------------------------------------------------------
# Frontend-Serialisierung (Issue #135)
# --------------------------------------------------------------------------
# Home Assistant übersetzt jedes Formularschema für das Frontend mit
# voluptuous_serialize. Scheitert das, fliegt der Fehler erst NACH dem
# eigentlichen Flow-Schritt in der Websocket-Schicht - der Dialog zeigt dann
# nur "Unknown error occurred", und der Schritt ist unerreichbar. Alle
# übrigen Tests dieser Datei rufen den Flow über die Python-API auf und
# überspringen diese Schicht; genau deshalb blieb #135 unbemerkt, obwohl
# keine einzige Tarifseite mehr darstellbar war.


def _assert_frontend_can_render(schema: vol.Schema) -> None:
    """Schema so übersetzen, wie Home Assistant es fürs Frontend tut."""
    voluptuous_serialize.convert(schema, custom_serializer=cv.custom_serializer)


def test_every_module_schema_is_serializable() -> None:
    """Jedes im Modul definierte Formularschema muss darstellbar sein.

    Bewusst über das Modul iteriert statt über eine gepflegte Liste: ein
    künftig ergänztes Schema ist damit automatisch mit abgedeckt und kann
    den Fehler aus #135 nicht unbemerkt wieder einschleppen."""
    schemas = {
        name: value
        for name, value in vars(config_flow).items()
        if isinstance(value, vol.Schema)
    }
    assert schemas, "Kein Schema gefunden - Test greift ins Leere"
    for name, schema in schemas.items():
        try:
            _assert_frontend_can_render(schema)
        except ValueError as err:  # pragma: no cover - nur im Fehlerfall
            pytest.fail(f"{name} ist für das Frontend nicht darstellbar: {err}")


async def test_every_setup_step_renders_for_the_frontend(hass) -> None:
    """Ersteinrichtung: jeder Schritt muss ein darstellbares Formular
    liefern."""
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.connected = True
    read_result = MagicMock()
    read_result.isError.return_value = False
    read_result.registers = [50] * 115
    client.read_holding_registers = AsyncMock(return_value=read_result)
    client.write_register = AsyncMock(return_value=read_result)
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
        for user_input in (VALID_INPUT, {}, {}, {}):
            assert result["type"] == FlowResultType.FORM
            _assert_frontend_can_render(result["data_schema"])
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input
            )
        assert result["type"] == FlowResultType.CREATE_ENTRY


@pytest.mark.parametrize(
    "tariff_type",
    [TariffType.FIXED, TariffType.TIME_OF_USE, TariffType.DYNAMIC],
)
async def test_every_tariff_step_renders_for_the_frontend(
    hass, tariff_type: TariffType
) -> None:
    """Jede Tarif-Folgeseite muss ein darstellbares Formular liefern -
    beim ersten Aufruf wie nach einem Validierungsfehler (dort baut
    _suggested das Schema neu auf)."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    _assert_frontend_can_render(result["data_schema"])

    first_page = {CONF_ECONOMICS_TARIFF_TYPE: tariff_type.value}
    if tariff_type is TariffType.DYNAMIC:
        first_page[CONF_PRICE_SENSOR] = "sensor.strompreis"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], first_page
    )
    assert result["type"] == FlowResultType.FORM
    _assert_frontend_can_render(result["data_schema"])

    # Unvollständig abschicken: derselbe Schritt, aber mit den zuletzt
    # eingegebenen Werten neu aufgebautem Schema.
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]
    _assert_frontend_can_render(result["data_schema"])


async def test_prices_are_rounded_to_the_configured_step(hass) -> None:
    """Die Rundung auf ECONOMICS_PRICE_DECIMALS sitzt seit #135 nicht mehr
    im Schema (dort war sie nicht serialisierbar), sondern im Schritt - sie
    muss weiterhin für alle Preisfelder greifen, auch für die Preise in den
    Zeitfenstergruppen."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value},
    )
    windows = _empty_windows()
    windows[economics_tou_window_key(1)] = {
        CONF_ECONOMICS_WINDOW_START: "22:00:00",
        CONF_ECONOMICS_WINDOW_END: "06:00:00",
        CONF_ECONOMICS_WINDOW_PRICE: 0.2100000000000002,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 0.078649999,
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.3200000000000003,
            **windows,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_FEED_IN_PRICE] == 0.0786
    assert entry.options[CONF_ECONOMICS_TOU_BASE_PRICE] == 0.32
    stored = entry.options[economics_tou_window_key(1)]
    assert stored[CONF_ECONOMICS_WINDOW_PRICE] == 0.21
    # Die übrigen Felder der Gruppe bleiben unangetastet.
    assert stored[CONF_ECONOMICS_WINDOW_START] == "22:00:00"
    assert stored[CONF_ECONOMICS_WINDOW_END] == "06:00:00"


async def test_out_of_range_price_is_still_rejected(hass) -> None:
    """Ohne das umschließende vol.All prüft der NumberSelector den
    Wertebereich weiterhin selbst - ein unplausibler Preis darf nicht in
    entry.options landen (Sicherheitsanforderung: keine ungeprüften
    Werte)."""
    entry = _economics_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value},
    )
    with pytest.raises(vol.Invalid):
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
                CONF_ECONOMICS_FIXED_IMPORT_PRICE: 99.0,
            },
        )
    assert entry.options == {}
