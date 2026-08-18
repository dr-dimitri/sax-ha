"""End-to-end test against a real local Modbus TCP simulator.

Anders als test_coordinator.py/test_config_flow.py (die den pymodbus Client
mocken) startet dieser Test einen echten Modbus-TCP-Server auf localhost und
lässt die Integration über einen echten Socket mit ihm sprechen. Das deckt
Fehler ab, die reine Mock-Tests nicht finden würden (z.B. falsches
Keyword-Argument für die Device-/Slave-ID, falsche Registeradressierung,
falsche Vorzeichenkonvertierung auf dem Wire-Format).
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

SLAVE_ID = 64
TEST_PORT = 15502

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _build_registers(**overrides: int) -> list[int]:
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


def _entity_id(registry: er.EntityRegistry, entry_id: str, suffix: str) -> str:
    unique_id = f"{entry_id}_{suffix}"
    for platform in ("sensor", "number", "switch"):
        found = registry.async_get_entity_id(platform, DOMAIN, unique_id)
        if found:
            return found
    raise AssertionError(f"Keine Entity mit unique_id {unique_id!r} gefunden")


async def test_live_modbus_end_to_end(hass, socket_enabled) -> None:
    """Setzt die Integration gegen einen echten Modbus-Server auf und prüft
    Lese- und Schreibpfade (inkl. Max-SOC-Klemmung und Netzladung) end-to-end."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        hr = ModbusSequentialDataBlock(1, _build_registers())
        device_ctx = ModbusDeviceContext(hr=hr)
        context = ModbusServerContext(devices={SLAVE_ID: device_ctx}, single=False)

    server = ModbusTcpServer(context, address=("127.0.0.1", TEST_PORT))
    await server.serve_forever(background=True)

    try:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "127.0.0.1",
                "port": TEST_PORT,
                "slave_id_basic": SLAVE_ID,
                "slave_id_extended": 40,
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

        # -- Initiale Werte, gelesen vom simulierten Gerät über echtes TCP --
        assert hass.states.get(soc_id).state == "55"
        assert hass.states.get(discharge_id).state == "1200"
        assert hass.states.get(charge_id).state == "0"
        assert hass.states.get(switch_id).state == "on"

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
            address=41, count=1, device_id=SLAVE_ID
        )
        verify_client.close()
        assert to_signed16(result.registers[0]) == -1500

        await hass.services.async_call(
            DOMAIN, "stop_grid_charge", {"device_id": device_id}, blocking=True
        )
        assert coordinator.grid_charge_active is False
    finally:
        await server.shutdown()
