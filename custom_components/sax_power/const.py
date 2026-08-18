"""Constants for the SAX Power integration."""

from __future__ import annotations

DOMAIN = "sax_power"

CONF_SLAVE_ID_BASIC = "slave_id_basic"
CONF_SLAVE_ID_EXTENDED = "slave_id_extended"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 502
DEFAULT_SLAVE_ID_BASIC = 64
# SunSpec-Modus (siehe modbus.pdf, offizielle sax-power.net-Dokumentation):
# feste Slave-ID 100, unabhängig vom Basic-Mode-Gerät. Die zuvor angenommene
# Slave-ID 40 ("Extended Mode" laut modbus_llm.yaml) existiert auf realer
# Hardware nicht - ein Read darauf liefert eine Modbus-Exception ("Gateway
# Target Device Failed to Respond"). Siehe anforderung.yaml,
# REQ-SUNSPEC-MODE-CORRECTION.
DEFAULT_SLAVE_ID_EXTENDED = 100
DEFAULT_SCAN_INTERVAL = 10

# Basic Mode (Slave-ID 64) Holding-Register.
# Interne Adresse = Protokolladresse - 40001 (siehe modbus_llm.yaml).
# Alle benötigten Register liegen zusammenhängend in einem Block (41-46),
# sodass ein einzelner read_holding_registers-Aufruf genügt.
#
# Register 47 ("Leistung P des Speichers") und 48 ("Leistung des Smart
# Meters") wurden bewusst entfernt: Ein Live-Test gegen echte Hardware ergab
# dort wiederholt physikalisch unplausible Werte (~16000W bei einem 4600W-
# Gerät im Leerlauf). Die entsprechenden physikalischen Größen werden
# stattdessen zuverlässig aus dem SunSpec-Modus gelesen (REG_SUN_STORAGE_
# POWER_ACTIVE bzw. REG_SUN_METER_POWER_ACTIVE_SUM unten), siehe
# anforderung.yaml, REQ-SUNSPEC-MODE-CORRECTION.
REG_SETPOINT_POWER = 41  # Write - W - Sollwert Leistung P (P-Sollwert-Modus)
REG_SETPOINT_COSPHI = 42  # Write - Sollwert cos(phi)
REG_LIMIT_DISCHARGE = 43  # Write - W - Leistungsgrenzwert Entladung
REG_LIMIT_CHARGE = 44  # Write - W - Leistungsgrenzwert Ladung
REG_SWITCH_STATE = 45  # Read/Write - Schaltzustand des Speichers
REG_SOC = 46  # Read - % - SOC des Speichers

READ_BLOCK_START = REG_SETPOINT_POWER
READ_BLOCK_COUNT = REG_SOC - REG_SETPOINT_POWER + 1

# ==========================================================================
# SunSpec-Modus (Slave-ID 100, siehe modbus.pdf / DEFAULT_SLAVE_ID_EXTENDED)
# ==========================================================================
# Adressierung: Interne Adresse = Protokolladresse - 40000 (NICHT -40001 wie
# im Basic Mode!). Verifiziert anhand der SunSpec-Kennung "SunS"
# (0x53756E53) an Adresse 0/1 sowie sämtlicher "wellknown"-Scalefaktoren aus
# modbus.pdf gegen echte Hardware (siehe anforderung.yaml,
# REQ-SUNSPEC-MODE-CORRECTION). Der komplette Block 40000-40114 (115
# Register: Common + 3Ph Inverter + Immediate Controls + Meter + Battery)
# liegt zusammenhängend, ein einzelner read_holding_registers-Aufruf genügt.

# -- SunSpec Common Model (ID 1) -------------------------------------------
REG_SUN_ID = 0  # Read - SunSpec-Kennung Hi-Word, wellknown 21365
REG_SUN_ID_LO = 1  # Read - SunSpec-Kennung Lo-Word, wellknown 28243
REG_SUN_COMMON_MODEL_ID = 2  # Read - wellknown 1
REG_SUN_COMMON_LENGTH = 3  # Read - wellknown 15
REG_SUN_MANUFACTURER = 4  # Read - str (4 Register, je 2 ASCII-Zeichen)
REG_SUN_MODEL = 8  # Read - str (3 Register, je 2 ASCII-Zeichen)
REG_SUN_VERSION_MASTER = 11  # Read - Softwareversion Master
REG_SUN_VERSION_GATEWAY = 12  # Read - Softwareversion Gateway
REG_SUN_SERIAL_HI = 13  # Read - Seriennummer, High Word
REG_SUN_SERIAL_LO = 14  # Read - Seriennummer, Low Word

# -- SunSpec Model 103 "3Ph Inverter" (Speicherelektronik) ------------------
REG_SUN_INVERTER_MODEL_ID = 15  # Read - wellknown 103
REG_SUN_INVERTER_LENGTH = 16  # Read - wellknown 32
REG_SUN_STORAGE_CURRENT_SUM = 17  # Read - A - Summe Phasenströme Speicher
REG_SUN_STORAGE_CURRENT_A = 18  # Read - A
REG_SUN_STORAGE_CURRENT_B = 19  # Read - A
REG_SUN_STORAGE_CURRENT_C = 20  # Read - A
REG_SUN_STORAGE_CURRENT_SF = 21  # Read - sunssf, wellknown -2
REG_SUN_STORAGE_VOLTAGE_L1L2 = 22  # Read - V
REG_SUN_STORAGE_VOLTAGE_L2L3 = 23  # Read - V
REG_SUN_STORAGE_VOLTAGE_L3L1 = 24  # Read - V
REG_SUN_STORAGE_VOLTAGE_A = 25  # Read - V
REG_SUN_STORAGE_VOLTAGE_B = 26  # Read - V
REG_SUN_STORAGE_VOLTAGE_C = 27  # Read - V
REG_SUN_STORAGE_VOLTAGE_SF = 28  # Read - sunssf, wellknown -1
REG_SUN_STORAGE_POWER_ACTIVE = 29  # Read - W - Wirkleistung Speicher Summe
REG_SUN_STORAGE_POWER_ACTIVE_SF = 30  # Read - sunssf, wellknown 0
REG_SUN_STORAGE_FREQUENCY = 31  # Read - Hz - Netzfrequenz (am Speicher)
REG_SUN_STORAGE_FREQUENCY_SF = 32  # Read - sunssf, wellknown -2
REG_SUN_STORAGE_POWER_APPARENT = 33  # Read - VA
REG_SUN_STORAGE_POWER_APPARENT_SF = 34  # Read - sunssf, wellknown 0
REG_SUN_STORAGE_POWER_REACTIVE = 35  # Read - Var
REG_SUN_STORAGE_POWER_REACTIVE_SF = 36  # Read - sunssf, wellknown 0
REG_SUN_STORAGE_POWER_FACTOR = 37  # Read
REG_SUN_STORAGE_POWER_FACTOR_SF = 38  # Read - sunssf, wellknown -3
# 39-40: Reserve
REG_SUN_STORAGE_MAX_CELL_TEMP = 41  # Read - °C - Maximale Zelltemperatur
REG_SUN_STORAGE_TEMP_SF = 42  # Read - sunssf, wellknown 0
REG_SUN_STORAGE_STATE = 43  # Read - 1:Aus 2:Standby 3:Wartezeit 4:Ein 7:SM-Fehler
REG_SUN_STORAGE_EVENT = (
    44  # Read - 0:Normalbetrieb 4:Insel-Fehler 8/9/10/11:NA 15:HW-Fehler
)
REG_SUN_PV_POWER = 45  # Read - W - nur mit Smartmeter ADW200 verfügbar
REG_SUN_PV_POWER_SF = 46  # Read - sunssf, wellknown 1

# -- SunSpec Model 123 "Immediate Controls" ----------------------------------
REG_SUN_IC_MODEL_ID = 47  # Read - wellknown 123
REG_SUN_IC_LENGTH = 48  # Read - wellknown 7
REG_SUN_IC_POWER_SETPOINT_PCT = 49  # Read/Write - % - Leistungsvorgabe
REG_SUN_IC_TIMEOUT = 50  # Read/Write - s - Timeout Leistungsvorgabe, max. 300
REG_SUN_IC_CONTROL_MODE = 51  # Read/Write - 0:SmartMeter-Nullregelung 1:Sollwertvorgabe
REG_SUN_IC_POWER_SETPOINT_SF = 52  # Read - sunssf, wellknown -2 (10000 = 100%)
REG_SUN_IC_MAX_POWER_REFERENCE = 53  # Read - W - Bezugspunkt 100% (4600/9200/13800)

# -- SunSpec Model 203 "WYE Connect 3Ph Meter ABC" (Smart Meter/Netz) -------
# Hinweis (modbus.pdf): "Die Register aus Modell 203 werden alle durch das
# ADW200 gemessen." Auf einem gegen echte Hardware mit angeschlossenem
# ADL400 verifizierten Gerät waren diese Register dennoch mit plausiblen
# Werten befüllt - die Einschränkung scheint zumindest für den Netz-Teil
# nicht (mehr) zu gelten. Einzig REG_SUN_PV_POWER (s. o.) war dabei
# durchgehend 0 und dürfte tatsächlich ADW200 voraussetzen.
REG_SUN_METER_MODEL_ID = 54  # Read - wellknown 203
REG_SUN_METER_LENGTH = 55  # Read - wellknown 41
REG_SUN_METER_CURRENT_SUM = 56  # Read - A - Summe AC-Strom Netz
REG_SUN_METER_CURRENT_L1 = 57  # Read - A
REG_SUN_METER_CURRENT_L2 = 58  # Read - A
REG_SUN_METER_CURRENT_L3 = 59  # Read - A
REG_SUN_METER_CURRENT_SF = 60  # Read - sunssf, wellknown -1
REG_SUN_METER_VOLTAGE_LN_AVG = 61  # Read - V - Durchschnitt Spannung Netz L-N
REG_SUN_METER_VOLTAGE_L1 = 62  # Read - V
REG_SUN_METER_VOLTAGE_L2 = 63  # Read - V
REG_SUN_METER_VOLTAGE_L3 = 64  # Read - V
REG_SUN_METER_VOLTAGE_LL_AVG = 65  # Read - V - Durchschnitt Spannung L-L
REG_SUN_METER_VOLTAGE_L1L2 = 66  # Read - V
REG_SUN_METER_VOLTAGE_L2L3 = 67  # Read - V
REG_SUN_METER_VOLTAGE_L1L3 = 68  # Read - V
REG_SUN_METER_VOLTAGE_SF = 69  # Read - sunssf, wellknown -1
REG_SUN_METER_FREQUENCY = 70  # Read - Hz - Netzfrequenz
REG_SUN_METER_FREQUENCY_SF = 71  # Read - sunssf, wellknown -2
REG_SUN_METER_POWER_ACTIVE_SUM = 72  # Read - W - Summenwirkleistung Netz
REG_SUN_METER_POWER_ACTIVE_L1 = 73  # Read - W
REG_SUN_METER_POWER_ACTIVE_L2 = 74  # Read - W
REG_SUN_METER_POWER_ACTIVE_L3 = 75  # Read - W
REG_SUN_METER_POWER_ACTIVE_SF = 76  # Read - sunssf, wellknown 1
REG_SUN_METER_POWER_APPARENT_SUM = 77  # Read - VA
REG_SUN_METER_POWER_APPARENT_L1 = 78  # Read - VA
REG_SUN_METER_POWER_APPARENT_L2 = 79  # Read - VA
REG_SUN_METER_POWER_APPARENT_L3 = 80  # Read - VA
REG_SUN_METER_POWER_APPARENT_SF = 81  # Read - sunssf, wellknown 1
REG_SUN_METER_POWER_REACTIVE_SUM = 82  # Read - Var
REG_SUN_METER_POWER_REACTIVE_L1 = 83  # Read - Var
REG_SUN_METER_POWER_REACTIVE_L2 = 84  # Read - Var
REG_SUN_METER_POWER_REACTIVE_L3 = 85  # Read - Var
REG_SUN_METER_POWER_REACTIVE_SF = 86  # Read - sunssf, wellknown 1
REG_SUN_METER_POWER_FACTOR_SUM = 87  # Read
REG_SUN_METER_POWER_FACTOR_L1 = 88  # Read
REG_SUN_METER_POWER_FACTOR_L2 = 89  # Read
REG_SUN_METER_POWER_FACTOR_L3 = 90  # Read
REG_SUN_METER_POWER_FACTOR_SF = 91  # Read - sunssf, wellknown -3
# 92-94: Reserve

# -- SunSpec Model 802 "Battery Base Model" (Akkuzellen) ---------------------
REG_SUN_BATTERY_MODEL_ID = 95  # Read - wellknown 802
REG_SUN_BATTERY_LENGTH = 96  # Read - wellknown 20
REG_SUN_BATTERY_CAPACITY = 97  # Read - Wh - Kapazität Speichersystem
REG_SUN_BATTERY_CHARGE_POWER_AVAILABLE = 98  # Read - W
REG_SUN_BATTERY_DISCHARGE_POWER_AVAILABLE = 99  # Read - W
REG_SUN_BATTERY_SOC_MAX = 100  # Read - %
REG_SUN_BATTERY_SOC_MIN = 101  # Read - %
REG_SUN_BATTERY_SOC = 102  # Read - % - Aktueller SoC
REG_SUN_BATTERY_DISCHARGE_DEPTH = 103  # Read - % - Entladetiefe
# 104-105: Reserve
REG_SUN_BATTERY_CHARGING_ACTIVE = 106  # Read - 0:keine Leistung 1:Leistung anliegend
# 107: Reserve
REG_SUN_BATTERY_EVENT = 108  # Read - 0:Normalbetrieb 3:Übertemperatur 4:Untertemperatur
REG_SUN_BATTERY_CELL_VOLTAGE_AVG = 109  # Read - mV - Durchschnittliche Zellspannung
REG_SUN_BATTERY_CAPACITY_SF = 110  # Read - sunssf, wellknown 0
REG_SUN_BATTERY_POWER_SF = 111  # Read - sunssf, wellknown 0
REG_SUN_BATTERY_SOC_SF = 112  # Read - sunssf, wellknown 0
# 113: Reserve
REG_SUN_BATTERY_CELL_VOLTAGE_SF = 114  # Read - sunssf, wellknown 0

READ_BLOCK_EXT_START = REG_SUN_ID
READ_BLOCK_EXT_COUNT = REG_SUN_BATTERY_CELL_VOLTAGE_SF - REG_SUN_ID + 1  # 115

# Immediate-Controls-Wertebereiche (modbus.pdf: "-100*SF bis +100*SF", SF=-2)
MIN_IC_POWER_SETPOINT_PCT = -100.0
MAX_IC_POWER_SETPOINT_PCT = 100.0
MAX_IC_TIMEOUT_SECONDS = 300

STORAGE_STATE_LABELS = {
    1: "Aus",
    2: "Standby",
    3: "Wartezeit",
    4: "Ein",
    7: "SM-Fehler",
}
STORAGE_EVENT_LABELS = {
    0: "Normalbetrieb",
    4: "Insel-Fehler",
    8: "Netzfrequenz zu hoch",
    9: "Netzfrequenz zu niedrig",
    10: "Netzspannung zu hoch",
    11: "Netzspannung zu niedrig",
    15: "Hardwarefehler",
}
BATTERY_EVENT_LABELS = {
    0: "Normalbetrieb",
    3: "Übertemperatur",
    4: "Untertemperatur",
}
CONTROL_MODE_LABELS = {
    0: "SmartMeter-Nullregelung",
    1: "Sollwertvorgabe",
}
UNKNOWN_LABEL = "Unbekannt"

SWITCH_STATE_OFF = 1
SWITCH_STATE_ON = 2
SWITCH_STATE_CONNECTED = 3

SWITCH_STATE_LABELS = {
    SWITCH_STATE_OFF: "Aus",
    SWITCH_STATE_ON: "Ein",
    SWITCH_STATE_CONNECTED: "Verbunden",
}
SWITCH_STATE_UNKNOWN_LABEL = UNKNOWN_LABEL

MIN_SOC = 0
MAX_SOC = 100

# Nicht dokumentierte Annahme: Leistungsgrenzwerte werden in dieser
# Bandbreite erwartet. Bitte an das jeweilige SAX-Power-Modell anpassen,
# falls die tatsächliche Nennleistung abweicht.
MIN_POWER_LIMIT = 0
MAX_POWER_LIMIT = 10000

# Sollwert Leistung P (Register 41) ist ein signed 16-bit Register.
MIN_SETPOINT_POWER = -32768
MAX_SETPOINT_POWER = 32767

# Doku: "Periodisches Wiederholen der Schreibbefehle (alle 5s bis 5min) bei
# aktiver Netzladung zur Vermeidung von Timeout-Resets."
GRID_CHARGE_WRITE_INTERVAL = 30  # Sekunden

SERVICE_START_GRID_CHARGE = "start_grid_charge"
SERVICE_STOP_GRID_CHARGE = "stop_grid_charge"
ATTR_POWER = "power"
ATTR_DEVICE_ID = "device_id"

DATA_COORDINATOR = "coordinator"

ISSUE_EXTENDED_MODE_UNAVAILABLE = "extended_mode_unavailable"
