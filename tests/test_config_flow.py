"""Tests for the SAX Power config flow."""

from __future__ import annotations

from importlib import import_module
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
import voluptuous_serialize
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power import PLATFORMS, config_flow
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
    CONF_GRID_SERVING_PV_FORECAST_SENSOR,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    CONF_VUE_DASHBOARD_DISMISSED_VERSION,
    CONF_VUE_DASHBOARD_ENABLED,
    CONF_VUE_DASHBOARD_VERSION,
    DATA_COORDINATOR,
    DOMAIN,
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


@pytest.mark.parametrize("reconfigure", [False, True])
@pytest.mark.parametrize("registers", [[], [65535], [101], [-1], [True], [50.5]])
async def test_connection_rejects_unusable_soc_response(
    hass: HomeAssistant, reconfigure: bool, registers: list[object]
) -> None:
    """REQ-IP-CONFIGURABLE-UI: Defekte Testreads speichern keine Verbindung."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT)
    if reconfigure:
        entry.add_to_hass(hass)
        result = await entry.start_reconfigure_flow(hass)
    else:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    response = MagicMock()
    response.isError.return_value = False
    response.registers = registers
    client.read_holding_registers = AsyncMock(return_value=response)

    with patch(
        "custom_components.sax_power.config_flow.AsyncModbusTcpClient",
        return_value=client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**VALID_INPUT, "host": "192.168.1.99"}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_response"}
    assert entry.data == VALID_INPUT
    assert len(hass.config_entries.async_entries(DOMAIN)) == int(reconfigure)
    client.close.assert_called_once_with()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("port", 0),
        ("port", 65536),
        ("slave_id_basic", -1),
        ("slave_id_basic", 256),
        ("slave_id_extended", -1),
        ("slave_id_extended", 256),
    ],
)
def test_connection_schema_rejects_invalid_protocol_address(
    field: str, value: int
) -> None:
    """REQ-IP-CONFIGURABLE-UI: Transportgrenzen gelten bereits im Formular."""
    with pytest.raises(vol.Invalid):
        config_flow.STEP_CONNECTION_SCHEMA({**VALID_INPUT, field: value})


async def test_user_flow_success(hass) -> None:
    """Ersteinrichtung: Nach erfolgreicher Verbindungsvalidierung folgt der
    zweite, optionale Schritt "grid_charge" - wird er unverändert (leer)
    abgeschickt, gelten die Hard-Defaults aus const.py (deaktiviert,
    Zeitfenster 00:00-00:05), siehe anforderung.yaml REQ-TIMED-SOC-CHARGE.
    Danach folgt der dritte, optionale Schritt "dashboard" (siehe
    anforderung.yaml REQ-VUE-DASHBOARD) - unverändert abgeschickt bleibt
    das Dashboard deaktiviert."""
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
        assert "create_dashboard" not in result5["data"]
        assert result5["data"][CONF_VUE_DASHBOARD_ENABLED] is False


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
    REQ-VUE-DASHBOARD."""
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
            result3["flow_id"], {CONF_VUE_DASHBOARD_ENABLED: False}
        )
        assert result4["type"] == FlowResultType.FORM
        assert result4["step_id"] == "finish"

        result5 = await hass.config_entries.flow.async_configure(result4["flow_id"], {})
        assert result5["type"] == FlowResultType.CREATE_ENTRY
        assert result5["data"][CONF_VUE_DASHBOARD_ENABLED] is False


@pytest.mark.parametrize("vue_enabled", [False, True])
async def test_dashboard_choice_is_persisted(
    hass: HomeAssistant, vue_enabled: bool
) -> None:
    """REQ-VUE-DASHBOARD: Die einzige Dashboard-Auswahl wird dauerhaft gespeichert."""
    with (
        patch("custom_components.sax_power.config_flow._async_validate_connection"),
        patch(
            "custom_components.sax_power.config_flow._async_read_finish_summary",
            return_value={"sunspec_available": False},
        ),
        patch("custom_components.sax_power.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_VUE_DASHBOARD_ENABLED: vue_enabled,
            },
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert "create_dashboard" not in result["data"]
    assert result["data"][CONF_VUE_DASHBOARD_ENABLED] is vue_enabled
    assert result["data"][CONF_VUE_DASHBOARD_VERSION] == ""


@pytest.mark.parametrize(
    ("initial_data", "initial_options", "submitted", "expected"),
    [
        ({}, {}, {}, False),
        ({CONF_VUE_DASHBOARD_ENABLED: True}, {}, {}, True),
        ({}, {CONF_VUE_DASHBOARD_ENABLED: True}, {}, True),
        ({}, {}, {CONF_VUE_DASHBOARD_ENABLED: True}, True),
        (
            {CONF_VUE_DASHBOARD_ENABLED: True},
            {},
            {CONF_VUE_DASHBOARD_ENABLED: False},
            False,
        ),
    ],
)
async def test_vue_options_preserve_or_override_onboarding_choice(
    hass: HomeAssistant,
    initial_data: dict,
    initial_options: dict,
    submitted: dict,
    expected: bool,
) -> None:
    """REQ-VUE-DASHBOARD: Abwahl bleibt dauerhaft vor dem Setup-Opt-in wirksam."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**VALID_INPUT, **initial_data},
        options=initial_options,
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    suggested = {
        key.schema: key.description["suggested_value"]
        for key in result["data_schema"].schema
        if isinstance(key.description, dict) and "suggested_value" in key.description
    }
    assert suggested[CONF_VUE_DASHBOARD_ENABLED] is initial_options.get(
        CONF_VUE_DASHBOARD_ENABLED, initial_data.get(CONF_VUE_DASHBOARD_ENABLED, False)
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], submitted
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_VUE_DASHBOARD_ENABLED] is expected


@pytest.mark.parametrize("tariff_type", [TariffType.DISABLED, TariffType.FIXED])
@pytest.mark.parametrize("existing_version", [None, "last-confirmed-bundle"])
async def test_vue_first_activation_marker_preserves_reactivation_history(
    hass: HomeAssistant, tariff_type: TariffType, existing_version: str | None
) -> None:
    """REQ-VUE-DASHBOARD-REPAIR: Nur das erste Aktivieren setzt eine neue Baseline."""
    data = dict(VALID_INPUT)
    if existing_version is not None:
        data[CONF_VUE_DASHBOARD_VERSION] = existing_version
        data[CONF_VUE_DASHBOARD_DISMISSED_VERSION] = "last-ignored-bundle"
    entry = MockConfigEntry(
        domain=DOMAIN, data=data, options={CONF_VUE_DASHBOARD_ENABLED: False}
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_VUE_DASHBOARD_ENABLED: True,
            CONF_ECONOMICS_TARIFF_TYPE: tariff_type.value,
        },
    )
    if tariff_type is TariffType.FIXED:
        assert result["type"] == FlowResultType.FORM
        assert entry.data == data
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_ECONOMICS_FIXED_IMPORT_PRICE: 30.0,
                CONF_ECONOMICS_FEED_IN_PRICE: 8.0,
            },
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_VUE_DASHBOARD_ENABLED] is True
    assert entry.data[CONF_VUE_DASHBOARD_VERSION] == (existing_version or "")
    if existing_version is not None:
        assert entry.data[CONF_VUE_DASHBOARD_DISMISSED_VERSION] == "last-ignored-bundle"


async def test_vue_legacy_enabled_options_do_not_invent_confirmed_baseline(
    hass: HomeAssistant,
) -> None:
    """REQ-VUE-DASHBOARD-REPAIR: Alte Snapshots behalten ihren Reload-Hinweis."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        options={CONF_VUE_DASHBOARD_ENABLED: True},
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert CONF_VUE_DASHBOARD_VERSION not in entry.data


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
        entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
            DATA_COORDINATOR: MagicMock()
        }
        entities = []
        for platform in PLATFORMS:
            module = import_module(f"custom_components.sax_power.{platform}")
            await module.async_setup_entry(hass, entry, entities.extend)
        assert placeholders["entity_count"] == str(len(entities))


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


@pytest.mark.parametrize(
    ("source", "unique_id"),
    [
        (config_entries.SOURCE_DHCP, "aa:bb:cc:dd:ee:ff"),
        (config_entries.SOURCE_USER, "192.168.1.50:502"),
    ],
)
async def test_user_flow_rejects_second_entry_before_showing_form(
    hass: HomeAssistant, source: str, unique_id: str
) -> None:
    """REQ-IP-CONFIGURABLE-UI: Ein zweiter Speicher wird vor der Eingabe gesperrt."""
    options = {CONF_PRICE_SENSOR: "sensor.strompreis"}
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        options=options,
        unique_id=unique_id,
        source=source,
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.sax_power.config_flow._async_validate_connection"
    ) as validate:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
    validate.assert_not_awaited()
    assert hass.config_entries.async_entries(DOMAIN) == [entry]
    assert entry.unique_id == unique_id
    assert entry.data == VALID_INPUT
    assert entry.options == options
    assert entry.source == source


@pytest.mark.parametrize(
    "connection_change", [{}, {"port": 1502}, {"host": "192.168.1.99"}]
)
async def test_open_user_flow_rejects_second_entry_for_any_endpoint(
    hass: HomeAssistant, connection_change: dict[str, str | int]
) -> None:
    """REQ-IP-CONFIGURABLE-UI: Auch offene Dialoge sperren andere Hosts/Ports."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        unique_id="aa:bb:cc:dd:ee:ff",
        source=config_entries.SOURCE_DHCP,
    )
    entry.add_to_hass(hass)
    user_input = {**VALID_INPUT, **connection_change}

    with patch(
        "custom_components.sax_power.config_flow._async_validate_connection"
    ) as validate:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
    validate.assert_not_awaited()
    assert hass.config_entries.async_entries(DOMAIN) == [entry]
    assert entry.unique_id == "aa:bb:cc:dd:ee:ff"
    assert entry.data == VALID_INPUT
    assert entry.source == config_entries.SOURCE_DHCP


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
    client.write_register = AsyncMock(return_value=read_result)
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

        result3 = await hass.config_entries.flow.async_configure(result2["flow_id"], {})
        result4 = await hass.config_entries.flow.async_configure(result3["flow_id"], {})
        result5 = await hass.config_entries.flow.async_configure(result4["flow_id"], {})

        assert result5["type"] == FlowResultType.CREATE_ENTRY
        assert result5["result"].unique_id == "aa:bb:cc:dd:ee:ff"
        assert result5["result"].data["host"] == "192.168.1.77"


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


async def test_dhcp_discovery_updates_host_for_configured_mac(hass) -> None:
    """Ein neuer DHCP-Lease derselben MAC führt die IP des vorhandenen
    Eintrags nach und plant genau einen Reload statt einer Discovery-Karte."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        unique_id="aa:bb:cc:dd:ee:ff",
        source=config_entries.SOURCE_DHCP,
    )
    entry.add_to_hass(hass)
    entry.mock_state(hass, config_entries.ConfigEntryState.LOADED)

    try:
        with patch.object(
            hass.config_entries, "async_schedule_reload"
        ) as schedule_reload:
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_DHCP},
                data=DhcpServiceInfo(
                    ip="192.168.1.77",
                    hostname="sax-1234",
                    macaddress="aabbccddeeff",
                ),
            )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"
        assert entry.data["host"] == "192.168.1.77"
        assert entry.unique_id == "aa:bb:cc:dd:ee:ff"
        schedule_reload.assert_called_once_with(entry.entry_id)
    finally:
        # Der Eintrag ist nur für die Reload-Entscheidung als geladen markiert;
        # ein echter Setup-Lauf, den das Fixture entladen müsste, fand nicht statt.
        entry.mock_state(hass, config_entries.ConfigEntryState.NOT_LOADED)


@pytest.mark.parametrize(
    ("unique_id", "expected_unique_id"),
    [
        ("192.168.1.50:502", "192.168.1.99:502"),
        ("aa:bb:cc:dd:ee:ff", "aa:bb:cc:dd:ee:ff"),
    ],
)
async def test_reconfigure_flow_updates_host(
    hass, unique_id: str, expected_unique_id: str
) -> None:
    """IP-Adresse (und andere Verbindungsdaten) müssen nach der
    Ersteinrichtung über die Oberfläche änderbar sein und persistiert
    werden (Config-Entry-Reconfigure-Flow, Kontextmenü "Neu konfigurieren")."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, unique_id=unique_id)
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
        assert entry.unique_id == expected_unique_id


@pytest.mark.parametrize("vue_enabled", [False, True])
async def test_reconfigure_preserves_vue_onboarding_choice(
    hass: HomeAssistant, vue_enabled: bool
) -> None:
    """REQ-VUE-DASHBOARD: Neue Verbindungsdaten ändern keine Dashboard-Auswahl."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **VALID_INPUT,
            CONF_VUE_DASHBOARD_ENABLED: vue_enabled,
            CONF_VUE_DASHBOARD_VERSION: "confirmed-hash",
            CONF_VUE_DASHBOARD_DISMISSED_VERSION: "ignored-hash",
        },
        unique_id="192.168.1.50:502",
    )
    entry.add_to_hass(hass)
    with (
        patch("custom_components.sax_power.config_flow._async_validate_connection"),
        patch.object(hass.config_entries, "async_reload", return_value=True),
    ):
        result = await entry.start_reconfigure_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**VALID_INPUT, "host": "192.168.1.99"}
        )
        await hass.async_block_till_done()

    assert result["reason"] == "reconfigure_successful"
    assert entry.data["host"] == "192.168.1.99"
    assert entry.data[CONF_VUE_DASHBOARD_ENABLED] is vue_enabled
    assert entry.data[CONF_VUE_DASHBOARD_VERSION] == "confirmed-hash"
    assert entry.data[CONF_VUE_DASHBOARD_DISMISSED_VERSION] == "ignored-hash"


async def test_reconfigure_flow_rejects_another_entries_target(hass) -> None:
    """Auch eine erhaltene MAC-ID darf nicht auf die Verbindung eines
    anderen, manuell angelegten Eintrags umkonfiguriert werden."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        unique_id="aa:bb:cc:dd:ee:ff",
        source=config_entries.SOURCE_DHCP,
    )
    entry.add_to_hass(hass)
    other_entry = MockConfigEntry(
        domain=DOMAIN,
        data={**VALID_INPUT, "host": "192.168.1.99"},
        unique_id="192.168.1.99:502",
    )
    other_entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**VALID_INPUT, "host": "192.168.1.99"}
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == "192.168.1.50"
    assert entry.unique_id == "aa:bb:cc:dd:ee:ff"


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
            CONF_GRID_SERVING_PV_FORECAST_SENSOR: "sensor.pv_rest_heute",
            CONF_PV_FORECAST_FACTOR: 70,
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_PRICE_SENSOR] == "sensor.strompreis"
    assert entry.options[CONF_PRICE_UNIT] == PRICE_UNIT_CT_KWH
    assert entry.options[CONF_PV_FORECAST_FACTOR] == 70
    assert entry.options[CONF_PV_FORECAST_SENSOR] == "sensor.pv_prognose_morgen"
    assert entry.options[CONF_GRID_SERVING_PV_FORECAST_SENSOR] == "sensor.pv_rest_heute"


async def test_options_preserve_legacy_forecast_only_for_smart(hass) -> None:
    """REQ-GRID-SERVING-CHARGE: Die Migration erfindet keine Heute-Auswahl."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_INPUT,
        options={CONF_PV_FORECAST_SENSOR: "sensor.pv_morgen"},
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    suggested = {
        key.schema: key.description["suggested_value"]
        for key in result["data_schema"].schema
        if isinstance(key.description, dict) and "suggested_value" in key.description
    }
    assert suggested[CONF_PV_FORECAST_SENSOR] == "sensor.pv_morgen"
    assert not suggested.get(CONF_GRID_SERVING_PV_FORECAST_SENSOR)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_PV_FORECAST_SENSOR: "sensor.pv_morgen"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_PV_FORECAST_SENSOR] == "sensor.pv_morgen"
    assert not entry.options.get(CONF_GRID_SERVING_PV_FORECAST_SENSOR)


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
            CONF_ECONOMICS_FEED_IN_PRICE: 7.86,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 34.21,
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
            {CONF_ECONOMICS_FIXED_IMPORT_PRICE: 34.21},
            id="fixed",
        ),
        pytest.param(TariffType.DYNAMIC, "economics_dynamic", {}, id="dynamic"),
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
        result["flow_id"], {**second_page, CONF_ECONOMICS_FEED_IN_PRICE: 7.86}
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


@pytest.mark.parametrize("existing", [False, True])
async def test_time_of_use_finishes_without_a_price_step(hass, existing: bool) -> None:
    """REQ-ECONOMICS-TARIFFS: Das Dashboard besitzt Preise und Fenster vollständig."""
    profile = {
        CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
        economics_tou_window_key(1): {
            CONF_ECONOMICS_WINDOW_START: "22:00:00",
            CONF_ECONOMICS_WINDOW_END: "06:00:00",
            CONF_ECONOMICS_WINDOW_PRICE: 0.21,
        },
    }
    entry = _economics_entry(
        hass,
        (
            {CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value, **profile}
            if existing
            else {}
        ),
    )
    result = await hass.config_entries.options.async_init(entry.entry_id)
    if existing:
        # Ein offener Options-Dialog darf neuere Dashboard-Preise nicht ersetzen.
        profile[CONF_ECONOMICS_TOU_BASE_PRICE] = 0.3456
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, **profile}
        )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
            CONF_PV_FORECAST_FACTOR: 70,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_PV_FORECAST_FACTOR] == 70
    assert not hasattr(
        config_flow.SaxPowerOptionsFlow, "async_step_economics_time_of_use"
    )
    if existing:
        assert all(entry.options[key] == value for key, value in profile.items())
    else:
        assert all(key not in entry.options for key in profile)


async def test_switch_to_time_of_use_does_not_reuse_other_tariff_prices(hass) -> None:
    """REQ-ECONOMICS-TARIFFS: Neuauswahl wartet auf explizite Dashboard-Eingaben."""
    entry = _economics_entry(
        hass,
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.3,
        },
    )
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert CONF_ECONOMICS_FEED_IN_PRICE not in entry.options
    assert CONF_ECONOMICS_FIXED_IMPORT_PRICE not in entry.options
    assert CONF_ECONOMICS_TOU_BASE_PRICE not in entry.options


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
        result["flow_id"], {CONF_ECONOMICS_FEED_IN_PRICE: 7.86}
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
            CONF_ECONOMICS_FEED_IN_PRICE: 9.0,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 34.0,
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
            CONF_ECONOMICS_FEED_IN_PRICE: 7.86,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 34.0,
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
    [TariffType.FIXED, TariffType.DYNAMIC],
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
    """REQ-ECONOMICS-TARIFFS: Cent-Eingaben einmalig gerundet als EUR speichern."""
    entry = _economics_entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 7.8649999,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 32.00000000000003,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_FEED_IN_PRICE] == 0.0786
    assert entry.options[CONF_ECONOMICS_FIXED_IMPORT_PRICE] == 0.32


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
                CONF_ECONOMICS_FEED_IN_PRICE: 7.86,
                CONF_ECONOMICS_FIXED_IMPORT_PRICE: 9900.0,
            },
        )
    assert entry.options == {}


@pytest.mark.parametrize("tariff_type", [TariffType.FIXED, TariffType.DYNAMIC])
async def test_stored_prices_are_suggested_in_cents_without_roundtrip_drift(
    hass: HomeAssistant, tariff_type: TariffType
) -> None:
    """REQ-ECONOMICS-TARIFFS: EUR-Altbestand erscheint als Cent ohne Wertänderung."""
    options = {
        CONF_ECONOMICS_TARIFF_TYPE: tariff_type.value,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
        CONF_PRICE_SENSOR: "sensor.strompreis",
    }
    if tariff_type is TariffType.FIXED:
        options[CONF_ECONOMICS_FIXED_IMPORT_PRICE] = 0.3421
    entry = _economics_entry(hass, options)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_TARIFF_TYPE: tariff_type.value,
            CONF_PRICE_SENSOR: "sensor.strompreis",
        },
    )
    suggested = {
        key.schema: key.description["suggested_value"]
        for key in result["data_schema"].schema
        if isinstance(key.description, dict) and "suggested_value" in key.description
    }
    assert suggested[CONF_ECONOMICS_FEED_IN_PRICE] == 7.86
    for price_selector in result["data_schema"].schema.values():
        assert price_selector.config["unit_of_measurement"] == "ct/kWh"
    if tariff_type is TariffType.FIXED:
        assert suggested[CONF_ECONOMICS_FIXED_IMPORT_PRICE] == 34.21
        # Ein Feldfehler erhält die letzte Cent-Eingabe statt EUR oder Defaults.
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_ECONOMICS_FEED_IN_PRICE: 9.25}
        )
        retry = {
            key.schema: key.description["suggested_value"]
            for key in result["data_schema"].schema
            if isinstance(key.description, dict)
            and "suggested_value" in key.description
        }
        assert retry[CONF_ECONOMICS_FEED_IN_PRICE] == 9.25
        assert retry[CONF_ECONOMICS_FIXED_IMPORT_PRICE] == 34.21
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], suggested
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_FEED_IN_PRICE] == 0.0786
    if tariff_type is TariffType.FIXED:
        assert entry.options[CONF_ECONOMICS_FIXED_IMPORT_PRICE] == 0.3421


async def test_non_finite_price_is_not_stored(hass: HomeAssistant) -> None:
    """REQ-ECONOMICS-TARIFFS: Nicht endliche Preise werden abgewiesen."""
    entry = _economics_entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 8.0,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: float("nan"),
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {
        CONF_ECONOMICS_FIXED_IMPORT_PRICE: "economics_price_invalid"
    }
    assert entry.options == {}
