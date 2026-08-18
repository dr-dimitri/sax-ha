"""Constants for the SAX Power integration."""

from __future__ import annotations

DOMAIN = "sax_power"

CONF_SLAVE_ID_BASIC = "slave_id_basic"
CONF_SLAVE_ID_EXTENDED = "slave_id_extended"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 502
DEFAULT_SLAVE_ID_BASIC = 64
DEFAULT_SLAVE_ID_EXTENDED = 40
DEFAULT_SCAN_INTERVAL = 10

# Basic Mode (Slave-ID 64) Holding-Register.
# Interne Adresse = Protokolladresse - 40001 (siehe modbus_llm.yaml).
# Alle benötigten Register liegen zusammenhängend in einem Block (41-48),
# sodass ein einzelner read_holding_registers-Aufruf genügt.
REG_SETPOINT_POWER = 41  # Write - W - Sollwert Leistung P (P-Sollwert-Modus)
REG_SETPOINT_COSPHI = 42  # Write - Sollwert cos(phi)
REG_LIMIT_DISCHARGE = 43  # Write - W - Leistungsgrenzwert Entladung
REG_LIMIT_CHARGE = 44  # Write - W - Leistungsgrenzwert Ladung
REG_SWITCH_STATE = 45  # Read/Write - Schaltzustand des Speichers
REG_SOC = 46  # Read - % - SOC des Speichers
REG_POWER = 47  # Read - W - Leistung P des Speichers (signed)
REG_SMARTMETER_POWER = 48  # Read - W - Leistung des Smart Meters (signed)

READ_BLOCK_START = REG_SETPOINT_POWER
READ_BLOCK_COUNT = REG_SMARTMETER_POWER - REG_SETPOINT_POWER + 1

# Extended Mode (Slave-ID 40) Holding-Register. Speicher- und
# Smart-Meter-Teilblock liegen zusammenhängend (70-109), sodass auch hier
# ein einzelner read_holding_registers-Aufruf genügt. Register ohne
# definierte Bedeutung ("N.A." in modbus_llm.yaml: 77-79, 94) werden
# mitgelesen, aber nicht als Entity exponiert.
REG_EXT_SUNSPEC_ID = 70  # Read
REG_EXT_SUNSPEC_LENGTH = 71  # Read
REG_EXT_CURRENT_SUM = 72  # Read - A - Summe Phasenströme (Herstellerwert)
REG_EXT_CURRENT_L1 = 73  # Read - A
REG_EXT_CURRENT_L2 = 74  # Read - A
REG_EXT_CURRENT_L3 = 75  # Read - A
REG_EXT_CURRENT_SF = 76  # Read - sunssf, wellknown -2
REG_EXT_VOLTAGE_L1 = 80  # Read - V
REG_EXT_VOLTAGE_L2 = 81  # Read - V
REG_EXT_VOLTAGE_L3 = 82  # Read - V
REG_EXT_VOLTAGE_SF = 83  # Read - sunssf, wellknown -1
REG_EXT_POWER_ACTIVE = 84  # Read - W - Summenleistung AC (Wirk), signed
REG_EXT_POWER_ACTIVE_SF = 85  # Read - sunssf, wellknown 1
REG_EXT_FREQUENCY = 86  # Read - Hz - Netzfrequenz
REG_EXT_FREQUENCY_SF = 87  # Read - sunssf, wellknown -1
REG_EXT_POWER_APPARENT = 88  # Read - VA - Summenleistung AC (Schein)
REG_EXT_POWER_APPARENT_SF = 89  # Read - sunssf, wellknown 1
REG_EXT_POWER_REACTIVE = 90  # Read - VAr - Summenleistung AC (Blind)
REG_EXT_POWER_REACTIVE_SF = 91  # Read - sunssf, wellknown 1
REG_EXT_POWER_FACTOR = 92  # Read - % - Leistungsfaktor
REG_EXT_POWER_FACTOR_SF = 93  # Read - sunssf, wellknown -1

# Extended Mode - Smart Meter (gleicher Read-Block, Slave-ID 40).
REG_EXT_SM_ENERGY_FED_IN = 95  # Read - kWh - Energie eingespeist
REG_EXT_SM_ENERGY_CONSUMED = 96  # Read - kWh - Energie bezogen
REG_EXT_SM_ENERGY_SF = 97  # Read - sunssf, wellknown 1
REG_EXT_SM_SWITCH_STATE = 98  # Read - Schaltzustand des Speichers (Spiegel)
REG_EXT_SM_CURRENT_L1 = 99  # Read - A - fester Faktor -2 (kein sunssf-Register)
REG_EXT_SM_CURRENT_L2 = 100  # Read - A - fester Faktor -2
REG_EXT_SM_CURRENT_L3 = 101  # Read - A - fester Faktor -2
REG_EXT_SM_POWER_L1 = 102  # Read - W (Doku nennt L1/L12/L13 statt L1/L2/L3)
REG_EXT_SM_POWER_L2 = 103  # Read - W
REG_EXT_SM_POWER_L3 = 104  # Read - W
REG_EXT_SM_POWER_SF = 105  # Read - sunssf, wellknown 1
REG_EXT_SM_VOLTAGE_L1 = 106  # Read - V - unskaliert laut Doku
REG_EXT_SM_VOLTAGE_L2 = 107  # Read - V - unskaliert laut Doku
REG_EXT_SM_VOLTAGE_L3 = 108  # Read - V - unskaliert laut Doku
REG_EXT_SM_POWER_TOTAL = 109  # Read - W - Summenleistung (Wirk)

READ_BLOCK_EXT_START = REG_EXT_SUNSPEC_ID
READ_BLOCK_EXT_COUNT = REG_EXT_SM_POWER_TOTAL - REG_EXT_SUNSPEC_ID + 1

# Smart-Meter-Ströme werden laut modbus_llm.yaml mit einem festen Faktor
# skaliert (kein eigenes sunssf-Register), anders als die übrigen Extended-
# Mode-Messwerte.
SM_CURRENT_SCALE_FACTOR = -2

SWITCH_STATE_OFF = 1
SWITCH_STATE_ON = 2
SWITCH_STATE_CONNECTED = 3

SWITCH_STATE_LABELS = {
    SWITCH_STATE_OFF: "Aus",
    SWITCH_STATE_ON: "Ein",
    SWITCH_STATE_CONNECTED: "Verbunden",
}
SWITCH_STATE_UNKNOWN_LABEL = "Unbekannt"

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
