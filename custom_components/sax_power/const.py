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

SWITCH_STATE_OFF = 1
SWITCH_STATE_ON = 2
SWITCH_STATE_CONNECTED = 3

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
