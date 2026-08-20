"""End-to-end test against a real local Modbus TCP simulator.

Anders als test_coordinator.py/test_config_flow.py (die den pymodbus Client
mocken) startet dieser Test einen echten Modbus-TCP-Server auf localhost und
lässt die Integration über einen echten Socket mit ihm sprechen. Das deckt
Fehler ab, die reine Mock-Tests nicht finden würden (z.B. falsches
Keyword-Argument für die Device-/Slave-ID, falsche Registeradressierung,
falsche Vorzeichenkonvertierung auf dem Wire-Format).

Simuliert werden sowohl Basic Mode (Slave-ID 64) als auch der SunSpec-Modus
(Slave-ID 100, siehe modbus.pdf), verifiziert gegen eine echte SAX Power
Home Plus. Siehe anforderung.yaml, REQ-SUNSPEC-MODE-CORRECTION.
"""

from __future__ import annotations

import asyncio
import warnings
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import ModbusTcpServer
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.const import (
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    DATA_COORDINATOR,
    DOMAIN,
    ISSUE_PRICE_CHARGE_CONFLICT,
    PRICE_STATUS_CHARGING,
    PRICE_STATUS_OFF,
    PRICE_STRATEGY_RELATIVE,
    PRICE_UNIT_AUTO,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import to_signed16, to_unsigned16

SLAVE_ID_BASIC = 64
SLAVE_ID_EXTENDED = 100
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
    }
    defaults.update(overrides)
    for addr, value in defaults.items():
        values[addr] = value
    return values


def _build_extended_registers(**overrides: int) -> list[int]:
    """Registerinhalt für den SunSpec-Modus (Slave-ID 100), siehe
    modbus.pdf. Adresse 0 = Protokolladresse 40000 (Offset -40000, nicht
    -40001 wie im Basic Mode!), verifiziert gegen eine echte SAX Power Home
    Plus (siehe anforderung.yaml, REQ-SUNSPEC-MODE-CORRECTION)."""
    values = [0] * 200
    defaults = {
        0: 21365,  # SunSpecID (Hi) - "Su"
        1: 28243,  # SunSpecID (Lo) - "nS"
        2: 1,  # SunSpec Model ID: Common
        3: 15,  # Länge
        4: 21313,  # Hersteller "SA"
        5: 22608,  # "XP"
        6: 20311,  # "OW"
        7: 17746,  # "ER" -> "SAXPOWER"
        8: 18511,  # Gerätemodell "HO"
        9: 19781,  # "ME" -> "HOME"
        10: 0,  # kein "PL"-Suffix
        11: 23,  # Version Master
        12: 56,  # Version Gateway
        13: 15448,  # Seriennummer (Hi)
        14: 97,  # Seriennummer (Lo)
        15: 103,  # Model Identifier: 3Ph Inverter
        16: 32,  # Model Länge
        17: 30,  # AC Strom Summe (Speicher)
        18: 5,  # AC Strom Speicher A
        19: 6,  # AC Strom Speicher B
        20: 7,  # AC Strom Speicher C
        21: 0,  # Scalefaktor AC Strom
        25: 230,  # Spannung Speicher A
        26: 231,  # Spannung Speicher B
        27: 229,  # Spannung Speicher C
        28: 0,  # Scalefaktor Spannung
        29: 1200,  # Wirkleistung Speicher Summe (positiv = Entladung)
        30: 0,  # Scalefaktor Leistung
        31: 500,  # Netzfrequenz (Speicher), roh -> 50.0 Hz
        32: to_unsigned16(-1),  # Scalefaktor Netzfrequenz
        33: 1100,  # Scheinleistung Speicher Summe
        34: 0,
        35: 100,  # Blindleistung Speicher Summe
        36: 0,
        37: 950,  # Leistungsfaktor Speicher Summe
        38: 0,
        41: 350,  # Maximale Zelltemperatur, roh -> 35.0 °C
        42: to_unsigned16(-1),  # Scalefaktor Temperatur
        43: 4,  # Zustand: Ein
        44: 0,  # Event: Normalbetrieb
        45: 0,  # PV-Leistung
        46: 1,  # Scalefaktor PV-Leistung
        47: 123,  # Sunspec Model ID: Immediate Controls
        48: 7,  # Sunspec Length
        49: 0,  # Leistungsvorgabe %
        50: 300,  # Timeout
        51: 0,  # Steuermodus: SmartMeter-Nullregelung
        52: to_unsigned16(-2),  # Scalefaktor Leistungsvorgabe
        53: 4600,  # Referenzwert Maximalleistung
        54: 203,  # Sunspec Model ID: Meter
        55: 41,  # Sunspec Length
        56: 20,  # AC Strom Summe (Netz)
        57: 6,  # AC Strom Netz L1
        58: 7,  # AC Strom Netz L2
        59: 7,  # AC Strom Netz L3
        60: 0,  # Scalefaktor Strom
        61: 230,  # Durchschnitt Spannung Netz L-N
        62: 231,  # Netzspannung L1
        63: 232,  # Netzspannung L2
        64: 233,  # Netzspannung L3
        69: 0,  # Scalefaktor Spannung
        70: 500,  # Netzfrequenz, roh -> 50.0 Hz
        71: to_unsigned16(-1),  # Scalefaktor Frequenz
        72: to_unsigned16(-300),  # Summenwirkleistung Netz -> smartmeter_power
        73: 68,  # Netzleistung L1
        74: 90,  # Netzleistung L2
        75: 87,  # Netzleistung L3
        76: 0,  # Scalefaktor Netzleistung
        77: 1100,  # Summenscheinleistung Netz
        81: 0,
        82: 100,  # Summenblindleistung Netz
        86: 0,
        87: 950,  # Leistungsfaktor Netz Summe
        91: 0,
        95: 802,  # Sunspec Model ID: Battery
        96: 20,  # Sunspec Length
        97: 5700,  # Kapazität Speichersystem
        98: 0,  # Verfügbare Ladeleistung
        99: 3000,  # Verfügbare Entladeleistung
        100: 100,  # Maximaler SoC
        101: 0,  # Minimaler SoC
        102: 55,  # Aktueller SoC
        103: 45,  # Entladetiefe
        106: 1,  # Ladestatus Akku: Leistung anliegend
        108: 0,  # Event: Normalbetrieb
        109: 3300,  # Durchschnittliche Zellspannung
        110: 0,
        111: 0,
        112: 0,
        113: 0,
        114: 0,
    }
    defaults.update(overrides)
    for addr, value in defaults.items():
        values[addr] = value
    return values


def _entity_id(registry: er.EntityRegistry, entry_id: str, suffix: str) -> str:
    unique_id = f"{entry_id}_{suffix}"
    for platform in ("sensor", "number", "select", "switch", "time"):
        found = registry.async_get_entity_id(platform, DOMAIN, unique_id)
        if found:
            return found
    raise AssertionError(f"Keine Entity mit unique_id {unique_id!r} gefunden")


def _state_float(hass, entity_id: str) -> float:
    return float(hass.states.get(entity_id).state)


async def test_live_modbus_end_to_end(hass, socket_enabled) -> None:
    """Setzt die Integration gegen einen echten Modbus-Server auf und prüft
    Lese- und Schreibpfade (inkl. Max-SOC-Klemmung, Netzladung und die
    SunSpec-Modus-Register mit Skalierung) end-to-end."""
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
        assert hass.states.get(switch_id).state == "on"

        # -- Entlade-/Ladeleistung stammen jetzt aus dem SunSpec-Modus
        #    (Register 40029 "Wirkleistung Speicher Summe"), nicht mehr aus
        #    dem unzuverlässigen Basic-Mode-Register 47, siehe
        #    anforderung.yaml REQ-SUNSPEC-MODE-CORRECTION --
        assert hass.states.get(discharge_id).state == "1200"
        assert hass.states.get(charge_id).state == "0"

        # -- SunSpec-Modus: Skalierung über echtes TCP --
        storage_current_a_id = _entity_id(registry, entry.entry_id, "storage_current_a")
        storage_voltage_a_id = _entity_id(registry, entry.entry_id, "storage_voltage_a")
        storage_frequency_id = _entity_id(registry, entry.entry_id, "storage_frequency")
        storage_temp_id = _entity_id(registry, entry.entry_id, "storage_max_cell_temp")
        storage_state_id = _entity_id(registry, entry.entry_id, "storage_state_text")

        assert _state_float(hass, storage_current_a_id) == 5
        assert _state_float(hass, storage_voltage_a_id) == 230
        assert _state_float(hass, storage_frequency_id) == pytest.approx(50.0)
        assert _state_float(hass, storage_temp_id) == pytest.approx(35.0)
        assert hass.states.get(storage_state_id).state == "Ein"

        # -- SunSpec-Modus: Netz/Smart Meter --
        smartmeter_power_id = _entity_id(registry, entry.entry_id, "smartmeter_power")
        grid_current_sum_id = _entity_id(registry, entry.entry_id, "grid_current_sum")
        grid_frequency_id = _entity_id(registry, entry.entry_id, "grid_frequency")
        assert hass.states.get(smartmeter_power_id).state == "-300"
        assert _state_float(hass, grid_current_sum_id) == 20
        assert _state_float(hass, grid_frequency_id) == pytest.approx(50.0)

        # -- SunSpec-Modus: Battery-Modell --
        battery_soc_id = _entity_id(registry, entry.entry_id, "battery_soc")
        battery_capacity_id = _entity_id(registry, entry.entry_id, "battery_capacity")
        battery_charging_id = _entity_id(
            registry, entry.entry_id, "battery_charging_active_text"
        )
        assert _state_float(hass, battery_soc_id) == 55
        assert _state_float(hass, battery_capacity_id) == 5700
        assert hass.states.get(battery_charging_id).state == "Leistung anliegend"

        # -- Identitäts-Sensoren (SunSpec Common Model) --
        manufacturer_id = _entity_id(registry, entry.entry_id, "sun_manufacturer")
        assert hass.states.get(manufacturer_id).state == "SAXPOWER"

        # -- Bisher ungenutzte Basic-Mode-Register jetzt ebenfalls sichtbar --
        setpoint_power_id = _entity_id(registry, entry.entry_id, "setpoint_power")
        assert hass.states.get(setpoint_power_id).state == "0"

        # -- Max. SOC zeigt ohne vorherige Einstellung/Config-Flow-Vorgabe
        #    100 statt 0/unbekannt (siehe SaxPowerMaxSocNumber.async_added_to_hass) --
        assert hass.states.get(max_soc_id).state == "100"

        # -- Speicher ausschalten (echter Write über TCP) --
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": switch_id}, blocking=True
        )
        await hass.async_block_till_done()
        assert hass.states.get(switch_id).state == "off"

        # -- Max. Netzladeleistung setzen: reiner Software-Zustand, kein
        #    Register-Write mehr (siehe SaxPowerChargeLimitNumber) --
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": charge_limit_id, "value": 1500},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert hass.states.get(charge_limit_id).state == "1500"

        coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

        # -- Max-SOC unterhalb des aktuellen SOC (55%) setzen: Coordinator
        #    muss die Max-SOC-Sperre aktivieren - Register 40051 auf
        #    Sollwertvorgabe, Register 40049 auf 0 % (siehe anforderung.yaml,
        #    REQ-TIMED-SOC-CHARGE) --
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": max_soc_id, "value": 50},
            blocking=True,
        )
        await hass.async_block_till_done()
        await asyncio.sleep(0.2)
        assert coordinator.max_soc_clamped is True
        assert coordinator.sun_charge_active is True

        verify_client = AsyncModbusTcpClient(host="127.0.0.1", port=TEST_PORT)
        await verify_client.connect()
        control_mode_result = await verify_client.read_holding_registers(
            address=REG_SUN_IC_CONTROL_MODE, count=1, device_id=SLAVE_ID_EXTENDED
        )
        setpoint_result = await verify_client.read_holding_registers(
            address=REG_SUN_IC_POWER_SETPOINT_PCT, count=1, device_id=SLAVE_ID_EXTENDED
        )
        verify_client.close()
        assert control_mode_result.registers[0] == SUN_IC_CONTROL_MODE_SETPOINT
        assert setpoint_result.registers[0] == 0

        await coordinator.async_stop_sun_charge()
        # Ziel-SOC wieder über den aktuellen SOC setzen, damit die
        # Max-SOC-Sperre den nachfolgenden Netzladung-Test nicht erneut
        # auslöst.
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": max_soc_id, "value": 90},
            blocking=True,
        )
        await hass.async_block_till_done()

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


async def test_live_modbus_extended_mode_unavailable_keeps_basic_sensors(
    hass, socket_enabled
) -> None:
    """Regressionstest für den Bug 'keine Sensoren in Home Assistant':

    Ist der SunSpec-Modus-Block (Slave-ID 100) auf dem Gateway nicht
    erreichbar - was bei echter Hardware vorkommen kann - darf das die
    Integration nicht mehr komplett am Start hindern (vorher:
    ConfigEntryNotReady -> gar keine Entities). Basic-Mode-Sensoren müssen
    weiterhin echte Werte liefern, SunSpec-Sensoren dürfen lediglich
    "unbekannt" zeigen. Siehe anforderung.yaml, REQ-EXTENDED-MODE-RESILIENCE."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        basic_hr = ModbusSequentialDataBlock(1, _build_basic_registers())
        # Bewusst nur Slave-ID 64 (Basic Mode) im Server-Context - simuliert
        # ein Gateway, auf dem der SunSpec-Modus (Slave-ID 100) nicht
        # verfügbar ist.
        context = ModbusServerContext(
            devices={SLAVE_ID_BASIC: ModbusDeviceContext(hr=basic_hr)},
            single=False,
        )

    server = ModbusTcpServer(context, address=("127.0.0.1", TEST_PORT + 1))
    await server.serve_forever(background=True)

    try:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "127.0.0.1",
                "port": TEST_PORT + 1,
                "slave_id_basic": SLAVE_ID_BASIC,
                "slave_id_extended": SLAVE_ID_EXTENDED,
                "scan_interval": 3600,
            },
        )
        entry.add_to_hass(hass)

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED

        registry = er.async_get(hass)

        # -- Basic-Mode-Sensoren liefern trotz fehlendem SunSpec-Modus
        #    weiterhin echte Werte --
        soc_id = _entity_id(registry, entry.entry_id, "soc")
        switch_id = _entity_id(registry, entry.entry_id, "storage_switch")
        assert hass.states.get(soc_id).state == "55"
        assert hass.states.get(switch_id).state == "on"

        # -- SunSpec-Sensoren existieren weiterhin als Entity, zeigen aber
        #    "unbekannt" statt die Integration am Laden zu hindern --
        storage_current_a_id = _entity_id(registry, entry.entry_id, "storage_current_a")
        assert hass.states.get(storage_current_a_id).state == STATE_UNKNOWN
    finally:
        await server.shutdown()


async def test_live_timed_charge_writes_setpoint_when_in_window(
    hass, socket_enabled
) -> None:
    """End-to-End-Test für das zeitgesteuerte Laden: Zeitfenster über die
    entsprechenden Time-Entities setzen, dann per Switch aktivieren - das
    muss innerhalb des Zeitfensters bei SOC < Ziel-SOC einen echten Write
    über den SunSpec-Modus (Slave-ID 100, "Immediate Controls") auslösen:
    erst Register 40051 (Steuermodus) auf Sollwertvorgabe, dann Register
    40049 (Leistungsvorgabe %, negativ = Laden). "Max. Netzladeleistung"
    wird hier absichtlich NICHT explizit gesetzt, um zusätzlich den
    einmaligen Vorgabewert aus dem beim Start gelesenen Register 44
    (_build_basic_registers()-Default 3000W) zu verifizieren (siehe
    SaxPowerChargeLimitNumber.async_added_to_hass). Der Ziel-SOC (zentrales
    "Max. SOC", Register 46 als Vergleichswert) ist bewusst keine eigene
    Einstellung, siehe anforderung.yaml REQ-TIMED-SOC-CHARGE."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        basic_registers = _build_basic_registers()
        basic_registers[46] = 50  # SOC 50%, unterhalb des unten gesetzten Ziel-SOC
        basic_hr = ModbusSequentialDataBlock(1, basic_registers)
        extended_hr = ModbusSequentialDataBlock(1, _build_extended_registers())
        context = ModbusServerContext(
            devices={
                SLAVE_ID_BASIC: ModbusDeviceContext(hr=basic_hr),
                SLAVE_ID_EXTENDED: ModbusDeviceContext(hr=extended_hr),
            },
            single=False,
        )

    server = ModbusTcpServer(context, address=("127.0.0.1", TEST_PORT + 2))
    await server.serve_forever(background=True)

    try:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "127.0.0.1",
                "port": TEST_PORT + 2,
                "slave_id_basic": SLAVE_ID_BASIC,
                "slave_id_extended": SLAVE_ID_EXTENDED,
                "scan_interval": 3600,
            },
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        max_soc_id = _entity_id(registry, entry.entry_id, "max_soc")
        start_id = _entity_id(registry, entry.entry_id, "timed_charge_start")
        end_id = _entity_id(registry, entry.entry_id, "timed_charge_end")
        enabled_id = _entity_id(registry, entry.entry_id, "timed_charge_enabled")
        active_text_id = _entity_id(
            registry, entry.entry_id, "timed_charge_active_text"
        )

        assert hass.states.get(active_text_id).state == "Inaktiv"

        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": max_soc_id, "value": 90},
            blocking=True,
        )
        await hass.services.async_call(
            "time",
            "set_value",
            {"entity_id": start_id, "time": "01:00:00"},
            blocking=True,
        )
        await hass.services.async_call(
            "time",
            "set_value",
            {"entity_id": end_id, "time": "05:00:00"},
            blocking=True,
        )

        coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
        try:
            # Nur der Moment des Aktivierens muss "im Fenster" liegen - der
            # anschließende periodische Schreib-Task läuft unabhängig davon.
            with patch(
                "custom_components.sax_power.coordinator.dt_util.now",
                return_value=datetime(2024, 1, 1, 2, 0),
            ):
                await hass.services.async_call(
                    "switch", "turn_on", {"entity_id": enabled_id}, blocking=True
                )
                await hass.async_block_till_done()

            assert hass.states.get(enabled_id).state == "on"
            assert coordinator.sun_charge_active is True
            await asyncio.sleep(0.2)

            verify_client = AsyncModbusTcpClient(host="127.0.0.1", port=TEST_PORT + 2)
            await verify_client.connect()
            control_mode_result = await verify_client.read_holding_registers(
                address=REG_SUN_IC_CONTROL_MODE, count=1, device_id=SLAVE_ID_EXTENDED
            )
            setpoint_result = await verify_client.read_holding_registers(
                address=REG_SUN_IC_POWER_SETPOINT_PCT,
                count=1,
                device_id=SLAVE_ID_EXTENDED,
            )
            verify_client.close()
            assert control_mode_result.registers[0] == SUN_IC_CONTROL_MODE_SETPOINT
            # -3000 W (negative "Max. Netzladeleistung", einmalig aus Register 44
            # vorbelegt) / 4600 W Referenz-Maximalleistung (Register 40053,
            # _build_extended_registers()-Default) * 100 = -65.217...%, skaliert
            # mit sunssf -2 -> -6522.
            assert to_signed16(setpoint_result.registers[0]) == -6522

            await hass.async_block_till_done()
            assert hass.states.get(active_text_id).state == "Aktiv"
        finally:
            await coordinator.async_stop_sun_charge()

        # Beim Stoppen wird der Steuermodus aktiv auf SmartMeter-Nullregelung
        # zurückgesetzt (Register 40051), statt nur passiv auf den geräteseitigen
        # Timeout (Register 40050) zu warten.
        verify_client = AsyncModbusTcpClient(host="127.0.0.1", port=TEST_PORT + 2)
        await verify_client.connect()
        control_mode_result = await verify_client.read_holding_registers(
            address=REG_SUN_IC_CONTROL_MODE, count=1, device_id=SLAVE_ID_EXTENDED
        )
        verify_client.close()
        assert control_mode_result.registers[0] == SUN_IC_CONTROL_MODE_SMARTMETER
    finally:
        await server.shutdown()


async def test_live_grid_charge_seeded_from_config_entry_on_first_setup(
    hass, socket_enabled
) -> None:
    """Werte aus dem optionalen zweiten Ersteinrichtungs-Schritt
    (config_flow.async_step_grid_charge) müssen beim allerersten Start eines
    neu eingerichteten Eintrags die "Netzladung Start"/"Netzladung
    Ende"/"Netzladung aktiv"-Entities vorbelegen, siehe
    entity.initial_config_value."""
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

    server = ModbusTcpServer(context, address=("127.0.0.1", TEST_PORT + 4))
    await server.serve_forever(background=True)

    try:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "127.0.0.1",
                "port": TEST_PORT + 4,
                "slave_id_basic": SLAVE_ID_BASIC,
                "slave_id_extended": SLAVE_ID_EXTENDED,
                "scan_interval": 3600,
                "timed_charge_enabled": True,
                "timed_charge_start": "22:00:00",
                "timed_charge_end": "06:00:00",
            },
        )
        entry.add_to_hass(hass)
        # Zeit außerhalb des unten gesetzten 22:00-06:00-Fensters patchen,
        # damit das Seeding selbst nicht bereits eine echte Netzladung
        # auslöst - hier geht es nur um die vorbelegten Entity-Zustände.
        with patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=datetime(2024, 1, 1, 12, 0),
        ):
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

        registry = er.async_get(hass)
        start_id = _entity_id(registry, entry.entry_id, "timed_charge_start")
        end_id = _entity_id(registry, entry.entry_id, "timed_charge_end")
        enabled_id = _entity_id(registry, entry.entry_id, "timed_charge_enabled")

        assert hass.states.get(start_id).state == "22:00:00"
        assert hass.states.get(end_id).state == "06:00:00"
        assert hass.states.get(enabled_id).state == "on"

        coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
        assert coordinator.sun_charge_active is False
        await coordinator.async_stop_sun_charge()
    finally:
        await server.shutdown()


async def test_live_grid_charge_falls_back_to_hard_defaults_without_config_entry_values(
    hass, socket_enabled
) -> None:
    """Fehlen die optionalen Netzladung-Werte im Config Entry (z. B. ein vor
    Einführung dieses Schritts angelegter Eintrag, oder weil das Formular
    unverändert abgeschickt wurde), müssen die Entities die Hard-Defaults aus
    const.py zeigen (deaktiviert, 00:00-00:05) statt "unbekannt"."""
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

    server = ModbusTcpServer(context, address=("127.0.0.1", TEST_PORT + 5))
    await server.serve_forever(background=True)

    try:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "127.0.0.1",
                "port": TEST_PORT + 5,
                "slave_id_basic": SLAVE_ID_BASIC,
                "slave_id_extended": SLAVE_ID_EXTENDED,
                "scan_interval": 3600,
                # Bewusst keine timed_charge_*-Schlüssel - simuliert einen
                # Eintrag, der vor Einführung des zweiten Ersteinrichtungs-
                # Schritts angelegt wurde.
            },
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        start_id = _entity_id(registry, entry.entry_id, "timed_charge_start")
        end_id = _entity_id(registry, entry.entry_id, "timed_charge_end")
        enabled_id = _entity_id(registry, entry.entry_id, "timed_charge_enabled")

        assert hass.states.get(start_id).state == "00:00:00"
        assert hass.states.get(end_id).state == "00:05:00"
        assert hass.states.get(enabled_id).state == "off"
    finally:
        await server.shutdown()


async def test_live_price_charge_writes_setpoint_in_cheapest_hour(
    hass, socket_enabled
) -> None:
    """End-to-End-Test für das preisoptimierte Laden (anforderung.yaml,
    REQ-DYNAMIC-PRICE-CHARGE): Strompreis-Sensor per Options Flow
    hinterlegen, Strategie "Günstigste Stunden" wählen, Hauptschalter
    einschalten - liegt die aktuelle Stunde in den günstigsten, muss das
    einen echten Write über den SunSpec-Modus auslösen (Register 40051
    Steuermodus, Register 40049 Leistungsvorgabe).

    Der Preis-Sensor ist bewusst ein simpler Zustand mit `raw_today`-Attribut
    (Nordpool-/EPEX-Format) statt einer echten Preis-Integration - genau so
    sieht die Integration ihn im Betrieb auch.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        basic_registers = _build_basic_registers()
        basic_registers[46] = 50  # SOC 50 %, unter dem Ziel-SOC
        basic_hr = ModbusSequentialDataBlock(1, basic_registers)
        extended_hr = ModbusSequentialDataBlock(1, _build_extended_registers())
        context = ModbusServerContext(
            devices={
                SLAVE_ID_BASIC: ModbusDeviceContext(hr=basic_hr),
                SLAVE_ID_EXTENDED: ModbusDeviceContext(hr=extended_hr),
            },
            single=False,
        )

    server = ModbusTcpServer(context, address=("127.0.0.1", TEST_PORT + 5))
    await server.serve_forever(background=True)

    try:
        now = dt_util.now()
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        hass.states.async_set(
            "sensor.strompreis",
            "0.05",
            {
                "unit_of_measurement": "EUR/kWh",
                "raw_today": [
                    {
                        "start": hour_start.isoformat(),
                        "end": (hour_start + timedelta(hours=1)).isoformat(),
                        "value": 0.05,
                    },
                    {
                        "start": (hour_start + timedelta(hours=1)).isoformat(),
                        "end": (hour_start + timedelta(hours=2)).isoformat(),
                        "value": 0.42,
                    },
                ],
            },
        )

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "127.0.0.1",
                "port": TEST_PORT + 5,
                "slave_id_basic": SLAVE_ID_BASIC,
                "slave_id_extended": SLAVE_ID_EXTENDED,
                "scan_interval": 3600,
            },
            options={
                CONF_PRICE_SENSOR: "sensor.strompreis",
                CONF_PRICE_UNIT: PRICE_UNIT_AUTO,
            },
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        strategy_id = _entity_id(registry, entry.entry_id, "price_charge_strategy")
        target_soc_id = _entity_id(registry, entry.entry_id, "price_charge_target_soc")
        enabled_id = _entity_id(registry, entry.entry_id, "price_charge_enabled")
        status_id = _entity_id(registry, entry.entry_id, "price_charge_status_text")
        next_start_id = _entity_id(registry, entry.entry_id, "price_charge_next_start")

        assert hass.states.get(status_id).state == PRICE_STATUS_OFF

        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": strategy_id, "option": PRICE_STRATEGY_RELATIVE},
            blocking=True,
        )
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": target_soc_id, "value": 80},
            blocking=True,
        )

        coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
        try:
            await hass.services.async_call(
                "switch", "turn_on", {"entity_id": enabled_id}, blocking=True
            )
            await hass.async_block_till_done()

            assert hass.states.get(enabled_id).state == "on"
            assert coordinator.sun_charge_active is True
            await asyncio.sleep(0.2)

            verify_client = AsyncModbusTcpClient(host="127.0.0.1", port=TEST_PORT + 5)
            await verify_client.connect()
            control_mode_result = await verify_client.read_holding_registers(
                address=REG_SUN_IC_CONTROL_MODE, count=1, device_id=SLAVE_ID_EXTENDED
            )
            setpoint_result = await verify_client.read_holding_registers(
                address=REG_SUN_IC_POWER_SETPOINT_PCT,
                count=1,
                device_id=SLAVE_ID_EXTENDED,
            )
            verify_client.close()
            assert control_mode_result.registers[0] == SUN_IC_CONTROL_MODE_SETPOINT
            # "Max. Netzladeleistung" ist einmalig aus Register 44 (3000 W)
            # vorbelegt; -3000 W / 4600 W * 100 = -65.217 %, sunssf -2.
            assert to_signed16(setpoint_result.registers[0]) == -6522

            await hass.async_block_till_done()
            assert hass.states.get(status_id).state == PRICE_STATUS_CHARGING
            # Timestamp-Sensoren werden von Home Assistant grundsätzlich in
            # UTC dargestellt, unabhängig von der lokalen Zeitzone.
            assert (
                hass.states.get(next_start_id).state
                == dt_util.as_utc(hour_start).isoformat()
            )
        finally:
            await coordinator.async_stop_sun_charge()
    finally:
        await server.shutdown()


async def test_live_price_charge_conflicts_with_timed_charge(
    hass, socket_enabled
) -> None:
    """Netzladung und preisoptimiertes Laden schließen sich aus: Der Schalter
    springt zurück und es erscheint ein reparierbarer Bestätigungsdialog,
    statt beide Automatiken gleichzeitig laufen zu lassen."""
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

    server = ModbusTcpServer(context, address=("127.0.0.1", TEST_PORT + 6))
    await server.serve_forever(background=True)

    try:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "127.0.0.1",
                "port": TEST_PORT + 6,
                "slave_id_basic": SLAVE_ID_BASIC,
                "slave_id_extended": SLAVE_ID_EXTENDED,
                "scan_interval": 3600,
            },
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        timed_id = _entity_id(registry, entry.entry_id, "timed_charge_enabled")
        price_id = _entity_id(registry, entry.entry_id, "price_charge_enabled")

        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": timed_id}, blocking=True
        )
        await hass.async_block_till_done()
        assert hass.states.get(timed_id).state == "on"

        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": price_id}, blocking=True
        )
        await hass.async_block_till_done()

        assert hass.states.get(price_id).state == "off"
        assert hass.states.get(timed_id).state == "on"
        assert (
            ir.async_get(hass).async_get_issue(
                DOMAIN, f"{ISSUE_PRICE_CHARGE_CONFLICT}_{entry.entry_id}"
            )
            is not None
        )
    finally:
        await server.shutdown()
