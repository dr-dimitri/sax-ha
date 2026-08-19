"""Constants for the SAX Power integration."""

from __future__ import annotations

DOMAIN = "sax_power"

CONF_SLAVE_ID_BASIC = "slave_id_basic"
CONF_SLAVE_ID_EXTENDED = "slave_id_extended"
CONF_SCAN_INTERVAL = "scan_interval"

# Optionale Vorbelegung für das zeitgesteuerte Laden (Zeitfenster + aktiv),
# abgefragt im zweiten Schritt der Ersteinrichtung (config_flow.py). Wirkt
# sich nur auf den allerersten Start eines neu eingerichteten Eintrags aus:
# sobald die zugehörigen Entities (time.py/switch.py) einmal einen echten
# Zustand über RestoreEntity gespeichert haben, hat dieser stets Vorrang -
# siehe entity.initial_config_value.
CONF_TIMED_CHARGE_START = "timed_charge_start"
CONF_TIMED_CHARGE_END = "timed_charge_end"
CONF_TIMED_CHARGE_ENABLED = "timed_charge_enabled"

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

DEFAULT_TIMED_CHARGE_START = "00:00:00"
DEFAULT_TIMED_CHARGE_END = "00:05:00"
DEFAULT_TIMED_CHARGE_ENABLED = False

# Netzdienliches Laden (siehe anforderung.yaml, REQ-GRID-SERVING-CHARGE):
# eigenes, zum zeitgesteuerten Laden (oben) nicht überlappendes Zeitfenster,
# in dem der Speicher ausschließlich mit PV-Überschuss geladen wird (nie aus
# dem Netz). Default-Fenster bewusst leer (Start == Ende, siehe
# coordinator._window_intervals/windows_overlap) statt eines echten
# Zeitraums wie beim zeitgesteuerten Laden oben: Ein leeres Fenster kann per
# Definition nie mit dem (beliebig vom Anwender konfigurierten) Fenster des
# zeitgesteuerten Ladens überlappen, auch nicht während eines Zwischenschritts
# beim Bearbeiten dessen Start-/Endzeit (über Mitternacht laufende Fenster
# können sonst kurzzeitig einen Großteil des Tages abdecken).
DEFAULT_GRID_SERVING_START = "00:00:00"
DEFAULT_GRID_SERVING_END = "00:00:00"
DEFAULT_GRID_SERVING_ENABLED = False

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
# ACHTUNG für spätere Umsetzungen ("manuelle Entladung" o. Ä.): positive
# (entladende) Sollwerte auf diesem Register wurden gegen echte Hardware
# getestet und wirkungslos befunden - siehe ausführlichen Kommentar bei
# REG_SUN_IC_POWER_SETPOINT_PCT unten. Die Integration schreibt dieses
# Register nur noch mit negativen (Lade-)Sollwerten (start_grid_charge).
REG_SETPOINT_POWER = 41  # Write - W - Sollwert Leistung P (P-Sollwert-Modus)
REG_SETPOINT_COSPHI = 42  # Write - Sollwert cos(phi)
# Register 43 ("Leistungsgrenzwert Entladung") wird von der Integration
# nicht mehr genutzt (siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE) - hier
# nur zur Vollständigkeit der Registerkarte dokumentiert.
REG_LIMIT_DISCHARGE = 43  # Write - W - Leistungsgrenzwert Entladung
# Register 44 wird nur noch einmalig gelesen, um "Max. Netzladeleistung"
# (number.py) beim allerersten Start mit dem aktuellen Geräte-Registerwert
# vorzubelegen - die Integration schreibt dieses Register nicht mehr.
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
# ACHTUNG für spätere Umsetzungen ("manuelle Entladung" o. Ä.): Positive
# Sollwerte auf REG_SUN_IC_POWER_SETPOINT_PCT (Entladung laut angenommener
# Vorzeichenkonvention, negativ = Laden) wurden gegen echte Hardware
# getestet - sowohl direkt als Prozentwert hier als auch alternativ als
# Watt-Wert auf dem älteren Basic-Mode-P-Sollwert (REG_SETPOINT_POWER oben),
# jeweils inkl. vorheriger Aktivierung von REG_SUN_IC_CONTROL_MODE =
# SUN_IC_CONTROL_MODE_SETPOINT. In beiden Fällen wurden die Register
# nachweislich korrekt geschrieben und zurückgelesen, auch nach Umstellung
# der geräteseitigen Betriebsart auf "P-Sollwert (TCP)" (siehe
# modbus_llm.yaml, operation_modes) - der Speicher hat in keinem Fall
# tatsächlich entladen. Auf Rückfrage hat der Hersteller bestätigt, dass
# eine ferngesteuerte manuelle Entladung so nicht vorgesehen ist. Die
# zugehörigen Entities ("Manuelle Entladung"-Schalter, "Entladeleistung"-
# Number) wurden deshalb wieder entfernt - siehe anforderung.yaml,
# REQ-MANUAL-DISCHARGE (Status: verworfen). Vor einem erneuten Versuch
# unbedingt zuerst erneut beim Hersteller nachfragen.
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

# Steuermodus-Werte für Register 40051 (siehe REG_SUN_IC_CONTROL_MODE oben
# sowie CONTROL_MODE_LABELS unten).
SUN_IC_CONTROL_MODE_SMARTMETER = 0  # Normalbetrieb (SmartMeter-Nullregelung)
SUN_IC_CONTROL_MODE_SETPOINT = 1  # Sollwertvorgabe - Voraussetzung für Register 40049

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
# aktiver Netzladung zur Vermeidung von Timeout-Resets." Gilt für den
# Basic-Mode-Pfad (Register 41, start_grid_charge-Service).
GRID_CHARGE_WRITE_INTERVAL = 30  # Sekunden

# -- SunSpec-Modus-Netzladung (Immediate Controls, Register 40049/40051) --
# Das Wiederholungsintervall für den periodischen Refresh ist die Hälfte des
# vom Gerät gemeldeten Timeouts (Register 40050, siehe REG_SUN_IC_TIMEOUT),
# damit der Sollwert sicher vor dessen Ablauf aufgefrischt wird.
# GRID_CHARGE_WRITE_INTERVAL dient dabei als Obergrenze (kein Grund, öfter zu
# schreiben als beim Basic-Mode-Pfad) sowie als Fallback, solange der
# Timeout-Wert noch nicht gelesen wurde. Siehe
# SaxPowerCoordinator._sun_ic_write_interval.
SUN_IC_MIN_WRITE_INTERVAL = 5  # Sekunden, Untergrenze gegen zu enges Polling

SERVICE_START_GRID_CHARGE = "start_grid_charge"
SERVICE_STOP_GRID_CHARGE = "stop_grid_charge"
ATTR_POWER = "power"
ATTR_DEVICE_ID = "device_id"

DATA_COORDINATOR = "coordinator"

ISSUE_EXTENDED_MODE_UNAVAILABLE = "extended_mode_unavailable"

# -- Zeitgesteuertes Laden -------------------------------------------------
# Software-Logik (kein natives Geräteregister für die Aktivierung selbst):
# Lädt den Speicher innerhalb eines konfigurierbaren Zeitfensters aktiv aus
# dem Netz auf einen Ziel-SOC, unabhängig von PV-Überschuss (z. B. für
# günstige Nachtstromtarife). Schreibt über den SunSpec-Modus (Slave-ID 100,
# "Immediate Controls", Register 40051 Steuermodus auf Sollwertvorgabe +
# Register 40049 Leistungsvorgabe in Prozent der Referenz-Maximalleistung),
# NICHT über den Basic-Mode-P-Sollwert (Register 41) - siehe
# SaxPowerCoordinator._async_enforce_timed_charge.
#
# Nutzt den zentralen "Max. Ladeleistung"-Grenzwert (Register 44) als Leistung
# sowie "Max. SOC" (Fallback MAX_SOC oben) als Ziel-SOC. Keine
# eigenen Einstellungen dafür - siehe anforderung.yaml,
# REQ-TIMED-SOC-CHARGE.
#
# Zusätzlicher Abbruchgrund neben Zeitfenster/Max-SOC: Sobald am Smart Meter
# (data["smartmeter_power"], Register 40072 "Summenwirkleistung Netz", siehe
# REG_SUN_METER_POWER_ACTIVE_SUM) mehr als dieser Schwellwert an PV-Überschuss
# gemessen wird, wird die Netzladung beendet - siehe
# SaxPowerCoordinator._async_enforce_grid_charge, REQ-TIMED-SOC-CHARGE.
# Vorzeichenkonvention laut Anwender: ein POSITIVER Anzeigewert steht für
# Überschuss aus der Dachphotovoltaik (Einspeisung), der Rohregisterwert kann
# davon abweichen - siehe apply_sunssf/to_signed16 für die Umrechnung. Als
# eigene Konstante ausgelagert, da der Schwellwert absehbar auch an anderer
# Stelle benötigt wird (z. B. für eine PV-Überschuss-Erkennung außerhalb der
# Netzladung).
SMARTMETER_PV_SURPLUS_THRESHOLD_WATT = 200
