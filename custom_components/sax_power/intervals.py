"""Zuordnung der periodischen Lese-/Schreib-Tasks der Integration zu ihrem
Intervalltyp (siehe const.IntervalType: HIGH/NORMAL/LOW).

Um das Intervall eines Tasks zu ändern (z. B. einen künftigen
Pilot-Modus-Zählerwert-Push auf HIGH oder träge Systemdaten wie
Seriennummer/Firmware auf LOW zu legen), genügt eine Änderung des
zugeordneten Werts in TASK_INTERVALS unten - der Task-Code selbst (siehe
coordinator.py) fragt seine Intervalllänge stets über task_interval_seconds()
ab und muss dafür nicht angepasst werden.

Initial sind sämtliche vorhandenen Lese- und Schreiboperationen auf NORMAL
gesetzt (siehe anforderung.yaml).
"""

from __future__ import annotations

from .const import INTERVAL_SECONDS_HIGH, INTERVAL_SECONDS_LOW, IntervalType

# -- Task-Namen --------------------------------------------------------------
# Lese-Tasks: Basic-Mode- bzw. SunSpec-Modus-Registerblock (siehe
# SaxPowerCoordinator._async_update_data/_async_read_extended).
TASK_READ_BASIC = "read_basic"
TASK_READ_EXTENDED = "read_extended"
# Träge SunSpec-Werte (Identität, Referenzwerte, seltene Batterie-Kennzahlen)
# innerhalb desselben Blocks wie TASK_READ_EXTENDED - siehe SLOW_DATA_KEYS
# unten sowie SaxPowerCoordinator._apply_slow_data_throttle.
TASK_READ_SLOW_DATA = "read_slow_data"
# Schreib-Tasks: periodisches Wiederholen der Lade-Sollwerte, damit der
# Speicher nicht per Timeout in den vorherigen Modus zurückfällt (siehe
# SaxPowerCoordinator._async_grid_charge_loop/_async_sun_charge_loop).
TASK_WRITE_GRID_CHARGE = "write_grid_charge"
TASK_WRITE_SUN_CHARGE = "write_sun_charge"

TASK_INTERVALS: dict[str, IntervalType] = {
    TASK_READ_BASIC: IntervalType.NORMAL,
    TASK_READ_EXTENDED: IntervalType.NORMAL,
    TASK_READ_SLOW_DATA: IntervalType.LOW,
    TASK_WRITE_GRID_CHARGE: IntervalType.NORMAL,
    TASK_WRITE_SUN_CHARGE: IntervalType.NORMAL,
}

# coordinator.data-Keys, die vom Task TASK_READ_SLOW_DATA abgedeckt werden -
# träge SunSpec-Werte, die sich praktisch nie/nur sehr selten ändern
# (Identität, Referenzwert Maximalleistung, seltene Batterie-Kennzahlen).
# Physisch bleiben sie Teil des einen zusammenhängenden SunSpec-Modus-
# Blocklesevorgangs (siehe SaxPowerCoordinator._async_read_extended, die
# Register liegen zwischen den schnell benötigten Werten) - das Intervall
# von TASK_READ_SLOW_DATA bestimmt stattdessen, wie oft ihr zuletzt
# gelesener Wert in coordinator.data übernommen wird, siehe
# SaxPowerCoordinator._apply_slow_data_throttle. "battery_charging_active"
# steht hier statt des davon abgeleiteten Sensor-Keys
# "battery_charging_active_text" (siehe sensor.py), der lediglich den
# Rohwert übersetzt und automatisch mitgedrosselt wird.
SLOW_DATA_KEYS = frozenset(
    {
        "sun_manufacturer",
        "sun_model",
        "sun_version_master",
        "sun_version_gateway",
        "sun_serial_number",
        "ic_max_power_reference",
        "battery_capacity",
        "battery_discharge_depth",
        "battery_charging_active",
        "battery_cell_voltage_avg",
    }
)


def resolve_interval_seconds(
    interval_type: IntervalType, *, normal_interval_seconds: int
) -> int:
    """Löst einen Intervalltyp in eine konkrete Sekundenzahl auf.

    `normal_interval_seconds` ist das beim Setup konfigurierte Intervall
    (CONF_SCAN_INTERVAL) und wird nur für IntervalType.NORMAL verwendet -
    HIGH und LOW sind fest (siehe const.INTERVAL_SECONDS_HIGH/_LOW).
    """
    if interval_type is IntervalType.HIGH:
        return INTERVAL_SECONDS_HIGH
    if interval_type is IntervalType.LOW:
        return INTERVAL_SECONDS_LOW
    return normal_interval_seconds


def task_interval_seconds(task: str, *, normal_interval_seconds: int) -> int:
    """Löst das Intervall eines Tasks über TASK_INTERVALS auf. Ein nicht in
    TASK_INTERVALS eingetragener Task gilt als NORMAL (sicherer Default)."""
    interval_type = TASK_INTERVALS.get(task, IntervalType.NORMAL)
    return resolve_interval_seconds(
        interval_type, normal_interval_seconds=normal_interval_seconds
    )
