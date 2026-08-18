"""End-to-end test against a real local Modbus TCP simulator.

Anders als test_coordinator.py/test_config_flow.py (die den pymodbus Client
mocken) startet dieser Test einen echten Modbus-TCP-Server auf localhost und
lässt die Integration über einen echten Socket mit ihm sprechen. Das deckt
Fehler ab, die reine Mock-Tests nicht finden würden (z.B. falsches
Keyword-Argument für die Device-/Slave-ID, falsche Registeradressierung,
falsche Vorzeichenkonvertierung auf dem Wire-Format).

Simuliert werden sowohl Basic Mode (Slave-ID 64) als auch Extended Mode
(Slave-ID 40, Speicher + Smart Meter), siehe anforderung.yaml,
Anforderung REQ-ALL-REGISTERS-READABLE.
"""

from __future__ import annotations

import asyncio
import warnings

import pytest
from homeassistant.helpers import entity_registry as er
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import ModbusTcpServer
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.const import DATA_COORDINATOR, DOMAIN
from custom_components.sax_power.coordinator import to_signed16, to_unsigned16

SLAVE_ID_BASIC = 64
SLAVE_ID_EXTENDED = 40
TEST_PORT = 15502

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _build_basic_registers(**overrides: int) -> list[int]:
    values = [0] * 100
    defaults = {
        41: 0,  # Sollwert Leistung P
        42: 0,  # Sollwert cos(phi)
        43: 3000,  # Leistungsgrenzwert Entladung
        44: 3000,  # Leistungsgrenzwert Ladung
        45: 2,  # Schaltzustand: Ein
        46: 55,  # SOC %
        47: 1200,  # Leistung P (positiv = Entladung)
        48: to_unsigned16(-300),  # Leistung Smart Meter
    }
    defaults.update(overrides)
    for addr, value in defaults.items():
        values[addr] = value
    return values


def _build_extended_registers(**overrides: int) -> list[int]:
    values = [0] * 120
    defaults = {
        # -- Speicher (Register 40071-40094) --
        70: 1,  # SunSpec ID
        71: 2,  # SunSpec Length
        72: 99,  # Summe Phasenströme (Herstellerwert, bewusst != Summe der L1-L3 unten)
        73: 5,  # Strom L1
        74: 6,  # Strom L2
        75: 7,  # Strom L3
        76: 0,  # Strom Skalierung (sf=0)
        80: 2300,  # Spannung L1 (roh)
        81: 2310,  # Spannung L2
        82: 2290,  # Spannung L3
        83: to_unsigned16(-1),  # Spannung Skalierung (sf=-1 -> Faktor 0.1)
        84: 1000,  # Wirkleistung Summe (sf=0)
        85: 0,
        86: 500,  # Netzfrequenz (roh, sf=-1 -> 50.0 Hz)
        87: to_unsigned16(-1),
        88: 1100,  # Scheinleistung Summe (sf=0)
        89: 0,
        90: 100,  # Blindleistung Summe (sf=0)
        91: 0,
        92: 950,  # Leistungsfaktor (roh, sf=-1 -> 95.0 %)
        93: to_unsigned16(-1),
        # -- Smart Meter (Register 40095-40110) --
        95: 1000,  # Energie eingespeist (sf=0)
        96: 2000,  # Energie bezogen (sf=0)
        97: 0,
        98: 2,  # Schaltzustand des Speichers (Spiegel): Ein
        99: 500,  # Strom L1 (fester Faktor -2 -> 5.0 A)
        100: 600,  # Strom L2 -> 6.0 A
        101: 700,  # Strom L3 -> 7.0 A
        102: 300,  # Wirkleistung L1
        103: 400,  # Wirkleistung L2
        104: 500,  # Wirkleistung L3
        105: 0,  # Skalierung Leistung (sf=0)
        106: 231,  # Spannung L1 (unskaliert)
        107: 232,  # Spannung L2
        108: 233,  # Spannung L3
        109: 1200,  # Summenleistung (Wirk)
    }
    defaults.update(overrides)
    for addr, value in defaults.items():
        values[addr] = value
    return values


def _entity_id(registry: er.EntityRegistry, entry_id: str, suffix: str) -> str:
    unique_id = f"{entry_id}_{suffix}"
    for platform in ("sensor", "number", "switch"):
        found = registry.async_get_entity_id(platform, DOMAIN, unique_id)
        if found:
            return found
    raise AssertionError(f"Keine Entity mit unique_id {unique_id!r} gefunden")


def _state_float(hass, entity_id: str) -> float:
    return float(hass.states.get(entity_id).state)


async def test_live_modbus_end_to_end(hass, socket_enabled) -> None:
    """Setzt die Integration gegen einen echten Modbus-Server auf und prüft
    Lese- und Schreibpfade (inkl. Max-SOC-Klemmung, Netzladung und die
    Extended-Mode-Register mit SunSpec-Skalierung + Phasensummen) end-to-end."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        basic_hr = ModbusSequentialDataBlock(1, _build_basic_registers())
        extended_hr = ModbusSequentialDataBlock(1, _build_extended_registers())
        context = ModbusServerContext(
            devices={
                SLAVE_ID_BASIC: ModbusDeviceContext(hr=basic_hr),
                SLAVE_ID_EXTENDED: ModbusDeviceContext(hr=extended_hr),
            },
            single=False,
        )

    server = ModbusTcpServer(context, address=("127.0.0.1", TEST_PORT))
    await server.serve_forever(background=True)

    try:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "127.0.0.1",
                "port": TEST_PORT,
                "slave_id_basic": SLAVE_ID_BASIC,
                "slave_id_extended": SLAVE_ID_EXTENDED,
                "scan_interval": 3600,
            },
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)

        soc_id = _entity_id(registry, entry.entry_id, "soc")
        discharge_id = _entity_id(registry, entry.entry_id, "discharge_power")
        charge_id = _entity_id(registry, entry.entry_id, "charge_power")
        switch_id = _entity_id(registry, entry.entry_id, "storage_switch")
        max_soc_id = _entity_id(registry, entry.entry_id, "max_soc")
        charge_limit_id = _entity_id(registry, entry.entry_id, "charge_limit")

        # -- Initiale Basic-Mode-Werte, gelesen über echtes TCP --
        assert hass.states.get(soc_id).state == "55"
        assert hass.states.get(discharge_id).state == "1200"
        assert hass.states.get(charge_id).state == "0"
        assert hass.states.get(switch_id).state == "on"

        # -- Extended Mode: SunSpec-Skalierung über echtes TCP --
        ext_current_l1_id = _entity_id(registry, entry.entry_id, "ext_current_l1")
        ext_current_sum_id = _entity_id(registry, entry.entry_id, "ext_current_sum")
        ext_current_sum_native_id = _entity_id(
            registry, entry.entry_id, "ext_current_sum_native"
        )
        ext_voltage_sum_id = _entity_id(registry, entry.entry_id, "ext_voltage_sum")
        ext_frequency_id = _entity_id(registry, entry.entry_id, "ext_frequency")
        ext_power_factor_id = _entity_id(registry, entry.entry_id, "ext_power_factor")

        assert _state_float(hass, ext_current_l1_id) == 5
        # Phasen-Summe muss berechnet werden (L1+L2+L3 = 5+6+7) und sich vom
        # separat exponierten Herstellerwert (Register 40073) unterscheiden.
        assert _state_float(hass, ext_current_sum_id) == 18
        assert _state_float(hass, ext_current_sum_native_id) == 99
        assert _state_float(hass, ext_voltage_sum_id) == pytest.approx(690.0)
        assert _state_float(hass, ext_frequency_id) == pytest.approx(50.0)
        assert _state_float(hass, ext_power_factor_id) == pytest.approx(95.0)

        # -- Extended Mode: Smart Meter Phasen-Summen --
        sm_current_sum_id = _entity_id(registry, entry.entry_id, "sm_current_sum")
        sm_power_sum_id = _entity_id(registry, entry.entry_id, "sm_power_sum")
        sm_voltage_sum_id = _entity_id(registry, entry.entry_id, "sm_voltage_sum")
        sm_switch_state_text_id = _entity_id(
            registry, entry.entry_id, "sm_switch_state_text"
        )

        assert _state_float(hass, sm_current_sum_id) == pytest.approx(18.0)
        assert _state_float(hass, sm_power_sum_id) == 1200
        assert _state_float(hass, sm_voltage_sum_id) == 696
        assert hass.states.get(sm_switch_state_text_id).state == "Ein"

        # -- Bisher ungenutzte Basic-Mode-Register jetzt ebenfalls sichtbar --
        setpoint_power_id = _entity_id(registry, entry.entry_id, "setpoint_power")
        smartmeter_power_id = _entity_id(registry, entry.entry_id, "smartmeter_power")
        assert hass.states.get(setpoint_power_id).state == "0"
        assert hass.states.get(smartmeter_power_id).state == "-300"

        # -- Speicher ausschalten (echter Write über TCP) --
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": switch_id}, blocking=True
        )
        await hass.async_block_till_done()
        assert hass.states.get(switch_id).state == "off"

        # -- Ladeleistungsgrenzwert setzen --
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": charge_limit_id, "value": 1500},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert hass.states.get(charge_limit_id).state == "1500"

        # -- Max-SOC unterhalb des aktuellen SOC (55%) setzen:
        #    Coordinator muss das Ladelimit-Register auf 0 klemmen --
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": max_soc_id, "value": 50},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert hass.states.get(charge_limit_id).state == "0"

        # -- Netzladung starten: periodischer Sollwert-Write auf Register 41 --
        switch_entry = registry.async_get(switch_id)
        assert switch_entry is not None and switch_entry.device_id is not None
        device_id = switch_entry.device_id

        await hass.services.async_call(
            DOMAIN,
            "start_grid_charge",
            {"device_id": device_id, "power": -1500},
            blocking=True,
        )
        await asyncio.sleep(0.2)

        coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
        assert coordinator.grid_charge_active is True

        verify_client = AsyncModbusTcpClient(host="127.0.0.1", port=TEST_PORT)
        await verify_client.connect()
        result = await verify_client.read_holding_registers(
            address=41, count=1, device_id=SLAVE_ID_BASIC
        )
        verify_client.close()
        assert to_signed16(result.registers[0]) == -1500

        await hass.services.async_call(
            DOMAIN, "stop_grid_charge", {"device_id": device_id}, blocking=True
        )
        assert coordinator.grid_charge_active is False
    finally:
        await server.shutdown()
