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

# Dritter, optionaler Schritt der Ersteinrichtung (siehe async_step_dashboard
# in config_flow.py sowie dashboard.py): legt bei Zustimmung einmalig das
# mitgelieferte Lovelace-Dashboard an. __init__.async_setup_entry setzt
# diesen Wert nach dem (Versuch des) Anlegens wieder auf False zurück -
# absichtlich VOR der Registrierung des Options-Update-Listeners, damit
# dieser interne Reset nicht selbst einen ungewollten Reload der gesamten
# Integration auslöst. Ohne den Reset würde jeder spätere Reload/Neustart
# versuchen, das Dashboard erneut anzulegen - dashboard.py ist zwar
# idempotent (legt es nur an, falls es nicht schon existiert), ein vom
# Anwender bewusst gelöschtes Dashboard würde sonst aber ungewollt wieder
# auftauchen. Siehe anforderung.yaml REQ-BUNDLED-DASHBOARD.
CONF_CREATE_DASHBOARD = "create_dashboard"
DEFAULT_CREATE_DASHBOARD = True

DEFAULT_PORT = 502
DEFAULT_SLAVE_ID_BASIC = 64
# SunSpec-Modus (siehe modbus.pdf, offizielle sax-power.net-Dokumentation):
# feste Slave-ID 100, unabhängig vom Basic-Mode-Gerät. Die zuvor angenommene
# Slave-ID 40 ("Extended Mode" laut modbus_llm.yaml) existiert auf realer
# Hardware nicht - ein Read darauf liefert eine Modbus-Exception ("Gateway
# Target Device Failed to Respond"). Siehe anforderung.yaml,
# REQ-SUNSPEC-MODE-CORRECTION.
DEFAULT_SLAVE_ID_EXTENDED = 100
DEFAULT_SCAN_INTERVAL = 10  # Steuert nur noch NORMAL (Basic Mode), siehe unten

# Drei-Stufen-Aktualisierung des SunSpec-Modus-Blocks (siehe anforderung.yaml,
# REQ-LOW-INTERVAL-REGISTERS/REQ-HIGH-INTERVAL-REGISTERS):
#   NORMAL - Basic Mode (Slave-ID 64): folgt dem oben konfigurierbaren
#            CONF_SCAN_INTERVAL/DEFAULT_SCAN_INTERVAL (Default 10s).
#   HIGH   - SunSpec-Modus, dynamische Mess-/Zustandswerte: fest und
#            unabhängig vom nutzerkonfigurierten NORMAL-Intervall, siehe
#            READ_BLOCK_EXT_HIGH_INTERVAL unten - u. a. relevant für eine
#            zügige Reaktion des netzdienlichen Ladens auf die tatsächliche
#            Ladeleistung (siehe anforderung.yaml, REQ-GRID-SERVING-CHARGE).
#   LOW    - SunSpec-Modus, statische Werte (Identität, Skalierungsfaktoren):
#            READ_BLOCK_EXT_LOW_INTERVAL weiter unten.
# SaxPowerCoordinator.__init__ setzt den internen Coordinator-Timer auf
# min(scan_interval, READ_BLOCK_EXT_HIGH_INTERVAL) und lässt
# _async_read_basic/_async_read_extended jeweils eigenständig prüfen, ob ihr
# Teilblock auf einem gegebenen Tick tatsächlich fällig ist - das
# config_flow-Minimum für scan_interval (5s) liegt dabei immer über
# READ_BLOCK_EXT_HIGH_INTERVAL, der Timer läuft also faktisch immer mit 2s.
READ_BLOCK_EXT_HIGH_INTERVAL = 2  # Sekunden

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

# Aktive Monate für Netzladung/netzdienliches Laden (siehe anforderung.yaml,
# REQ-GRID-SERVING-CHARGE): je Feature 12 Monats-Schalter (switch.py), die
# festlegen, in welchen Kalendermonaten das jeweilige Zeitfenster überhaupt
# wirksam ist (z. B. Netzladung nur November-Januar, netzdienliches Laden
# nur Mai-August). Default: alle Monate aktiv, damit sich bestehende
# Konfigurationen nach einem Update unverändert verhalten, bis der Anwender
# einzelne Monate bewusst abwählt. Sind für ein Feature gar keine Monate
# ausgewählt, ist es ganzjährig inaktiv (analog zu einem leeren Zeitfenster).
ALL_MONTHS = frozenset(range(1, 13))

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
# Register 44 ("Leistungsgrenzwert Ladung") wird von der Integration nicht
# mehr genutzt (weder gelesen noch geschrieben) - die frühere
# Software-Einstellung "Max. Netzladeleistung" (number.py) wurde entfernt,
# weil der eingestellte Watt-Wert in der Praxis keinen Einfluss auf die
# tatsächliche Ladeleistung hatte (siehe anforderung.yaml,
# REQ-TIMED-SOC-CHARGE) - hier nur zur Vollständigkeit der Registerkarte
# dokumentiert, analog zu REG_LIMIT_DISCHARGE.
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
# liegt zusammenhängend. Gelesen wird er nicht mehr mit einem einzelnen
# read_holding_registers-Aufruf, sondern in drei Teilblöcken mit
# unterschiedlicher Aktualisierungsfrequenz - siehe READ_BLOCK_EXT_START/
# READ_BLOCK_EXT_LOW1_START/READ_BLOCK_EXT_LOW2_START unten sowie
# anforderung.yaml, REQ-LOW-INTERVAL-REGISTERS.

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

# -- LOW-Intervall (siehe anforderung.yaml, REQ-LOW-INTERVAL-REGISTERS) -----
# Zwei Teilbereiche des obigen Blocks enthalten laut modbus_llm.yaml
# ausschließlich "wellknown" fixe bzw. sich im laufenden Betrieb praktisch
# nie ändernde Werte (Geräteidentität/Firmware-Version bzw.
# Skalierungsfaktoren) und liegen jeweils direkt am Rand des Blocks -
# SaxPowerCoordinator._async_read_low_block liest sie deshalb per eigenem
# read_holding_registers-Aufruf nur alle READ_BLOCK_EXT_LOW_INTERVAL
# Sekunden statt bei jedem Poll. Der reguläre (HIGH-)Block schrumpft
# dadurch von 115 auf 93 Register, ohne dass dafür im Normalbetrieb
# zusätzliche Requests nötig sind.
READ_BLOCK_EXT_LOW_INTERVAL = 3600  # Sekunden

# Teilbereich 1: SunSpec Common Model (Hersteller, Modell, Firmware-Version,
# Seriennummer) + Modellkopf von "3Ph Inverter" (Modell-ID/Länge) - direkt
# angrenzend an REG_SUN_STORAGE_CURRENT_SUM, dem ersten dynamischen Messwert.
READ_BLOCK_EXT_LOW1_START = REG_SUN_ID
READ_BLOCK_EXT_LOW1_COUNT = REG_SUN_INVERTER_LENGTH - REG_SUN_ID + 1  # 17

READ_BLOCK_EXT_START = REG_SUN_STORAGE_CURRENT_SUM
READ_BLOCK_EXT_COUNT = (
    REG_SUN_BATTERY_CELL_VOLTAGE_AVG - REG_SUN_STORAGE_CURRENT_SUM + 1
)  # 93

# Teilbereich 2: Battery-Skalierungsfaktoren (alle laut modbus_llm.yaml
# "wellknown" mit fixem Wert 0) - liegen am Ende des Blocks.
READ_BLOCK_EXT_LOW2_START = REG_SUN_BATTERY_CAPACITY_SF
READ_BLOCK_EXT_LOW2_COUNT = (
    REG_SUN_BATTERY_CELL_VOLTAGE_SF - REG_SUN_BATTERY_CAPACITY_SF + 1
)  # 5

# Immediate-Controls-Wertebereiche (modbus.pdf: "-100*SF bis +100*SF", SF=-2)
MIN_IC_POWER_SETPOINT_PCT = -100.0
MAX_IC_POWER_SETPOINT_PCT = 100.0

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
SERVICE_SET_TIMED_CHARGE_WINDOW = "set_timed_charge_window"
SERVICE_SET_GRID_SERVING_WINDOW = "set_grid_serving_window"
ATTR_POWER = "power"
ATTR_DEVICE_ID = "device_id"
ATTR_START = "start"
ATTR_END = "end"

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
# SaxPowerCoordinator._async_enforce_grid_charge.
#
# Nutzt den zentralen "Max. Netzladeleistung"-Grenzwert (Register 44
# einmalig vorbelegt) als Leistung sowie "Max. SOC" (Fallback MAX_SOC oben)
# als oberes Ziel - beide gemeinsam mit netzdienlichem Laden genutzt, keine
# eigenen Einstellungen dafür. Der untere Start-Schwellwert "Netzladung
# Min. SOC" ist dagegen eine reine, featurespezifische Netzladung-
# Einstellung (number.py, SaxPowerTimedChargeMinSocNumber) - siehe
# anforderung.yaml, REQ-TIMED-SOC-CHARGE.
#
# Zusätzlicher Abbruchgrund neben Zeitfenster/Max-SOC: Sobald am Smart Meter
# (data["smartmeter_power"], Register 40072 "Summenwirkleistung Netz", siehe
# REG_SUN_METER_POWER_ACTIVE_SUM) mehr als dieser Schwellwert an PV-Überschuss
# gemessen wird, wird die Netzladung beendet - siehe
# SaxPowerCoordinator._async_enforce_grid_charge, REQ-TIMED-SOC-CHARGE.
# Vorzeichenkonvention laut Anwender: ein POSITIVER Anzeigewert steht für
# Überschuss aus der Dachphotovoltaik (Einspeisung), der Rohregisterwert kann
# davon abweichen - siehe apply_sunssf/to_signed16 für die Umrechnung.
#
# Wird außerdem von der Zustandsmaschine für netzdienliches Laden
# (SaxPowerCoordinator._async_step_grid_serving, REQ-GRID-SERVING-CHARGE) für
# zwei unterschiedliche Signale mit demselben Schwellwert genutzt: als
# Auslöser für den Wechsel in den Sollwertvorgabemodus (tatsächliche
# Ladeleistung des SAX, negativer Anteil von data["storage_power_active"])
# sowie als Rückkehr-Kriterium in die SmartMeter-Nullregelung (Netzeinspeisung
# data["smartmeter_power"] unter diesem Wert).
SMARTMETER_PV_SURPLUS_THRESHOLD_WATT = 50

# Zyklen-Hysterese für JEDEN Vergleich gegen SMARTMETER_PV_SURPLUS_THRESHOLD_
# WATT (Max-SOC-Freigabe-Trigger, zeitgesteuertes Laden, netzdienliches Laden
# Schritt a+b): eine Schwellwert-Über-/Unterschreitung zählt erst nach so
# vielen aufeinanderfolgenden Poll-Zyklen als bestätigt, siehe
# SaxPowerCoordinator._cycles_confirmed. Schützt einheitlich gegen kurze
# Lastspitzen/Messausreißer am Smart Meter.
PV_SURPLUS_HYSTERESIS_CYCLES = 2

# ==========================================================================
# Preisoptimiertes Laden (siehe anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE)
# ==========================================================================
# Reine Software-Logik oberhalb des vorhandenen SunSpec-Schreibpfads
# (Register 40051/40049, siehe _async_sun_charge_loop): lädt den Speicher
# aus dem Netz, wenn der Strompreis günstig ist. Die Preisdaten kommen
# ausschließlich aus einer beliebigen, vom Anwender im Options Flow
# ausgewählten Home-Assistant-Sensor-Entity (Tibber, Nordpool, EPEX Spot,
# ENTSO-e, Awattar, ...) - die Integration ruft selbst keine Preise ab.

# -- Options-Flow-Schlüssel (config_flow.SaxPowerOptionsFlow) --------------
CONF_PRICE_SENSOR = "price_sensor"
CONF_PRICE_ATTRIBUTE = "price_attribute"
CONF_PRICE_UNIT = "price_unit"
CONF_PV_FORECAST_SENSOR = "pv_forecast_sensor"
CONF_PV_FORECAST_FACTOR = "pv_forecast_factor"
CONF_PRICE_STRATEGY = "price_strategy"

# Preis-Einheit des ausgewählten Sensors. "auto" leitet sie aus dessen
# unit_of_measurement ab (alles mit "ct"/"cent" wird durch 100 geteilt),
# die beiden anderen Werte erzwingen die jeweilige Interpretation - nötig
# für Sensoren ohne (oder mit irreführender) Einheit.
PRICE_UNIT_AUTO = "auto"
PRICE_UNIT_EUR_KWH = "eur_kwh"
PRICE_UNIT_CT_KWH = "ct_kwh"
PRICE_UNITS = (PRICE_UNIT_AUTO, PRICE_UNIT_EUR_KWH, PRICE_UNIT_CT_KWH)
DEFAULT_PRICE_UNIT = PRICE_UNIT_AUTO

# -- Strategien (select.SaxPowerPriceStrategySelect) -----------------------
# "off" ist zusätzlich zum Hauptschalter vorhanden, damit sich die Automatik
# stilllegen lässt, ohne die restliche Konfiguration (Preisgrenze, Stunden)
# zu verlieren - wirksam ist preisoptimiertes Laden nur, wenn der
# Hauptschalter an UND die Strategie ungleich "off" ist.
PRICE_STRATEGY_OFF = "off"
PRICE_STRATEGY_ABSOLUTE = "absolute"
PRICE_STRATEGY_RELATIVE = "relative"
PRICE_STRATEGY_SMART = "smart"
PRICE_STRATEGIES = (
    PRICE_STRATEGY_OFF,
    PRICE_STRATEGY_ABSOLUTE,
    PRICE_STRATEGY_RELATIVE,
    PRICE_STRATEGY_SMART,
)
DEFAULT_PRICE_STRATEGY = PRICE_STRATEGY_OFF

DEFAULT_PRICE_CHARGE_ENABLED = False

# Preisgrenze (Modus "Absoluter Preis") in EUR/kWh. Der negative Bereich ist
# bewusst zugelassen: an Börsenstrom gekoppelte Tarife weisen zeitweise
# negative Arbeitspreise aus, und genau dann soll geladen werden dürfen.
MIN_PRICE_LIMIT = -1.0
MAX_PRICE_LIMIT = 2.0
PRICE_LIMIT_STEP = 0.001
DEFAULT_PRICE_LIMIT = 0.20

# Anzahl der günstigsten Stunden (Modi "Relativ" und "Smart"). Im
# Smart-Modus zusätzlich Obergrenze für die aus dem Energiebedarf
# errechnete Stundenzahl.
MIN_PRICE_HOURS = 1
MAX_PRICE_HOURS = 24
DEFAULT_PRICE_HOURS = 3

# Anteil der PV-Prognose, der als tatsächlich im Speicher landender Ertrag
# eingerechnet wird (Modus "Smart"). < 100 % deckt Eigenverbrauch,
# Wetterunsicherheit und Wandlungsverluste ab.
MIN_PV_FORECAST_FACTOR = 0
MAX_PV_FORECAST_FACTOR = 100
DEFAULT_PV_FORECAST_FACTOR = 80

# Prüfintervall der Ladebedingungen (REQ-DYNAMIC-PRICE-CHARGE). Der
# Coordinator-Timer läuft deutlich schneller (siehe
# READ_BLOCK_EXT_HIGH_INTERVAL); der Ladeplan selbst wird nur in diesem
# Intervall (sowie sofort bei jeder Einstellungsänderung und jedem
# Zustandswechsel des Preis-Sensors) neu berechnet.
PRICE_EVAL_INTERVAL = 60  # Sekunden

# Planungshorizont: nur Preis-Slots, die innerhalb dieser Zeitspanne ab
# "jetzt" beginnen, gehen in die Auswahl der günstigsten Stunden ein. Damit
# ist die Auswahl ein gleitendes 24-Stunden-Fenster über die jeweils
# bekannten Preisdaten (Rest von heute + ggf. bereits veröffentlichtes
# Morgen), nicht der Kalendertag.
PRICE_PLAN_HORIZON_HOURS = 24

# Fallback-Länge eines Preis-Slots, wenn sie sich weder aus einem
# "end"-Feld noch aus dem Abstand zum nächsten Slot ableiten lässt.
DEFAULT_PRICE_SLOT_MINUTES = 60

# Statustexte des Sensors "Preisoptimiertes Laden Status". Bewusst deutsche
# Klartexte statt übersetzbarer Enum-Zustände - identisch zum bestehenden
# Muster der übrigen *_text-Sensoren (STORAGE_STATE_LABELS oben).
PRICE_STATUS_OFF = "Aus"
PRICE_STATUS_NO_PRICE_DATA = "Keine Preisdaten"
PRICE_STATUS_WAITING = "Warten auf Preisabfall"
PRICE_STATUS_CHARGING = "Lade aus Netz"
PRICE_STATUS_PV_FORECAST_COVERS = "PV-Prognose deckt Bedarf"
PRICE_STATUS_PAUSED_PV_SURPLUS = "Pausiert (PV-Überschuss)"
PRICE_STATUS_PAUSED_MAX_SOC = "Pausiert (Max. SOC)"
PRICE_STATUS_PAUSED_TIMED_CHARGE = "Pausiert (Netzladung aktiv)"

# -- Konflikt zwischen Netzladung und preisoptimiertem Laden --------------
# Beide Features laden aktiv aus dem Netz über denselben Schreibpfad und
# dürfen deshalb nicht gleichzeitig aktiv sein. Statt die Aktivierung
# kommentarlos abzulehnen, legt der Coordinator ein reparierbares Issue an
# (repairs.py) - der Anwender bestätigt darin, dass das jeweils andere
# Feature abgeschaltet werden soll, oder bricht ab.
ISSUE_PRICE_CHARGE_CONFLICT = "price_charge_conflict"
ISSUE_TIMED_CHARGE_CONFLICT = "timed_charge_conflict"
CHARGE_CONFLICT_ISSUES = (ISSUE_PRICE_CHARGE_CONFLICT, ISSUE_TIMED_CHARGE_CONFLICT)

SERVICE_REFRESH_PRICE_PLAN = "refresh_price_plan"
SERVICE_SET_PRICE_CHARGE_ENABLED = "set_price_charge_enabled"
ATTR_ENABLED = "enabled"
ATTR_FORCE = "force"

# Legt das mitgelieferte Dashboard nachträglich an (dashboard.py) - für
# Anwender, die es in der Ersteinrichtung abgewählt haben, es versehentlich
# gelöscht haben, oder deren Eintrag vor Einführung dieses Features angelegt
# wurde (siehe anforderung.yaml, REQ-BUNDLED-DASHBOARD). Idempotent: legt es
# nur an, falls es nicht schon existiert.
SERVICE_CREATE_DASHBOARD = "create_dashboard"

# Setzt ein ggf. bereits vorhandenes Dashboard auf den Auslieferungszustand
# zurück (dashboard.async_create_dashboard mit force=True) - z. B. nach
# manuellen Änderungen. Ersetzt den früheren Reinstall-Button (button.py):
# ButtonEntities auf der Geräteseite wurden vom Anwender nicht zuverlässig
# gefunden; ein über Entwicklertools -> Aktionen aufrufbarer Service ist in
# Home Assistant der robustere, immer sichtbare Weg dafür.
SERVICE_REINSTALL_DASHBOARD = "reinstall_dashboard"

# ==========================================================================
# Selbstdiagnose / erweiterte Repairs (siehe anforderung.yaml,
# REQ-SELF-DIAGNOSIS-REPAIRS)
# ==========================================================================
# Weitere reparierbare Issues über den Ladekonflikt
# (ISSUE_PRICE_CHARGE_CONFLICT/ISSUE_TIMED_CHARGE_CONFLICT oben) und die
# sofortige SunSpec-Nichterreichbarkeits-Warnung (ISSUE_EXTENDED_MODE_
# UNAVAILABLE) hinaus: erkennen still fehlschlagende Konfigurationen, die
# sonst nur an unerwartet ausbleibendem Ladeverhalten auffallen würden.
# Alle fünf sind rein informativ (is_fixable=False) und heilen sich selbst
# (SaxPowerCoordinator._async_check_self_diagnostics, hinter einer
# Zustandsflanke je Prüfung, damit weder Log noch Issue Registry bei jedem
# Poll-Zyklus neu befüllt werden), sobald ihre jeweilige Ursache behoben
# ist - analog zum Muster von ISSUE_EXTENDED_MODE_UNAVAILABLE.
ISSUE_PRICE_SENSOR_MISSING = "price_sensor_missing"
ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE = "sunspec_persistently_unavailable"
ISSUE_MAX_SOC_BELOW_MIN_SOC = "max_soc_below_min_soc"
ISSUE_EMPTY_CHARGE_WINDOW = "empty_charge_window"
ISSUE_NO_ACTIVE_MONTHS = "no_active_months"

# Mindestdauer eines fortbestehenden Problemzustands, bevor die jeweilige
# Prüfung anschlägt - kurze Aussetzer (ein einzelner verpasster
# Preis-Update-Zyklus, ein kurzer Netzwerk-Hänger) sollen kein Issue
# erzeugen. ISSUE_EXTENDED_MODE_UNAVAILABLE selbst legt schon bei der
# ERSTEN Nichterreichbarkeit sein eigenes, weniger dringliches Warn-Issue
# an - ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE eskaliert erst, wenn der
# Zustand tatsächlich anhält.
PRICE_SENSOR_MISSING_GRACE_PERIOD = 6 * 3600  # Sekunden
SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD = 3600  # Sekunden
