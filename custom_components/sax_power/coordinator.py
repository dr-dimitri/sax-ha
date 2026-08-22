"""DataUpdateCoordinator for the SAX Power integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Mapping
from datetime import time as dt_time
from datetime import timedelta
from time import monotonic
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    ALL_MONTHS,
    BATTERY_EVENT_LABELS,
    CHARGE_CONFLICT_ISSUES,
    CONTROL_MODE_LABELS,
    DEFAULT_PRICE_HOURS,
    DEFAULT_PRICE_STRATEGY,
    DOMAIN,
    GRID_CHARGE_WRITE_INTERVAL,
    ISSUE_EMPTY_CHARGE_WINDOW,
    ISSUE_EXTENDED_MODE_UNAVAILABLE,
    ISSUE_MAX_SOC_BELOW_MIN_SOC,
    ISSUE_NO_ACTIVE_MONTHS,
    ISSUE_PRICE_CHARGE_CONFLICT,
    ISSUE_PRICE_NEUTRAL_BELOW_LIMIT,
    ISSUE_PRICE_SENSOR_MISSING,
    ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE,
    ISSUE_TIMED_CHARGE_CONFLICT,
    MAX_IC_POWER_SETPOINT_PCT,
    MAX_PRICE_HOURS,
    MAX_PRICE_LIMIT,
    MAX_SETPOINT_POWER,
    MAX_SOC,
    MIN_IC_POWER_SETPOINT_PCT,
    MIN_PRICE_HOURS,
    MIN_PRICE_LIMIT,
    MIN_SETPOINT_POWER,
    MIN_SOC,
    PRICE_SENSOR_MISSING_GRACE_PERIOD,
    PRICE_STATUS_CHARGING,
    PRICE_STATUS_NO_PRICE_DATA,
    PRICE_STATUS_OFF,
    PRICE_STATUS_PAUSED_MAX_SOC,
    PRICE_STATUS_PAUSED_NEUTRAL_BAND,
    PRICE_STATUS_PAUSED_PV_SURPLUS,
    PRICE_STATUS_PAUSED_TIMED_CHARGE,
    PRICE_STATUS_PV_FORECAST_COVERS,
    PRICE_STRATEGIES,
    PRICE_STRATEGY_OFF,
    PV_SURPLUS_HYSTERESIS_CYCLES,
    READ_BLOCK_COUNT,
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_HIGH_INTERVAL,
    READ_BLOCK_EXT_LOW1_COUNT,
    READ_BLOCK_EXT_LOW1_START,
    READ_BLOCK_EXT_LOW2_COUNT,
    READ_BLOCK_EXT_LOW2_START,
    READ_BLOCK_EXT_LOW_INTERVAL,
    READ_BLOCK_EXT_START,
    READ_BLOCK_START,
    REG_SETPOINT_COSPHI,
    REG_SETPOINT_POWER,
    REG_SOC,
    REG_SUN_BATTERY_CAPACITY,
    REG_SUN_BATTERY_CAPACITY_SF,
    REG_SUN_BATTERY_CELL_VOLTAGE_AVG,
    REG_SUN_BATTERY_CELL_VOLTAGE_SF,
    REG_SUN_BATTERY_CHARGE_POWER_AVAILABLE,
    REG_SUN_BATTERY_CHARGING_ACTIVE,
    REG_SUN_BATTERY_DISCHARGE_DEPTH,
    REG_SUN_BATTERY_DISCHARGE_POWER_AVAILABLE,
    REG_SUN_BATTERY_EVENT,
    REG_SUN_BATTERY_POWER_SF,
    REG_SUN_BATTERY_SOC,
    REG_SUN_BATTERY_SOC_MAX,
    REG_SUN_BATTERY_SOC_MIN,
    REG_SUN_BATTERY_SOC_SF,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_MAX_POWER_REFERENCE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    REG_SUN_IC_POWER_SETPOINT_SF,
    REG_SUN_IC_TIMEOUT,
    REG_SUN_MANUFACTURER,
    REG_SUN_METER_CURRENT_L1,
    REG_SUN_METER_CURRENT_L2,
    REG_SUN_METER_CURRENT_L3,
    REG_SUN_METER_CURRENT_SF,
    REG_SUN_METER_CURRENT_SUM,
    REG_SUN_METER_FREQUENCY,
    REG_SUN_METER_FREQUENCY_SF,
    REG_SUN_METER_POWER_ACTIVE_L1,
    REG_SUN_METER_POWER_ACTIVE_L2,
    REG_SUN_METER_POWER_ACTIVE_L3,
    REG_SUN_METER_POWER_ACTIVE_SF,
    REG_SUN_METER_POWER_ACTIVE_SUM,
    REG_SUN_METER_POWER_APPARENT_SF,
    REG_SUN_METER_POWER_APPARENT_SUM,
    REG_SUN_METER_POWER_FACTOR_SF,
    REG_SUN_METER_POWER_FACTOR_SUM,
    REG_SUN_METER_POWER_REACTIVE_SF,
    REG_SUN_METER_POWER_REACTIVE_SUM,
    REG_SUN_METER_VOLTAGE_L1,
    REG_SUN_METER_VOLTAGE_L2,
    REG_SUN_METER_VOLTAGE_L3,
    REG_SUN_METER_VOLTAGE_LN_AVG,
    REG_SUN_METER_VOLTAGE_SF,
    REG_SUN_MODEL,
    REG_SUN_PV_POWER,
    REG_SUN_PV_POWER_SF,
    REG_SUN_SERIAL_HI,
    REG_SUN_SERIAL_LO,
    REG_SUN_STORAGE_CURRENT_A,
    REG_SUN_STORAGE_CURRENT_B,
    REG_SUN_STORAGE_CURRENT_C,
    REG_SUN_STORAGE_CURRENT_SF,
    REG_SUN_STORAGE_CURRENT_SUM,
    REG_SUN_STORAGE_EVENT,
    REG_SUN_STORAGE_FREQUENCY,
    REG_SUN_STORAGE_FREQUENCY_SF,
    REG_SUN_STORAGE_MAX_CELL_TEMP,
    REG_SUN_STORAGE_POWER_ACTIVE,
    REG_SUN_STORAGE_POWER_ACTIVE_SF,
    REG_SUN_STORAGE_POWER_APPARENT,
    REG_SUN_STORAGE_POWER_APPARENT_SF,
    REG_SUN_STORAGE_POWER_FACTOR,
    REG_SUN_STORAGE_POWER_FACTOR_SF,
    REG_SUN_STORAGE_POWER_REACTIVE,
    REG_SUN_STORAGE_POWER_REACTIVE_SF,
    REG_SUN_STORAGE_STATE,
    REG_SUN_STORAGE_TEMP_SF,
    REG_SUN_STORAGE_VOLTAGE_A,
    REG_SUN_STORAGE_VOLTAGE_B,
    REG_SUN_STORAGE_VOLTAGE_C,
    REG_SUN_STORAGE_VOLTAGE_SF,
    REG_SUN_VERSION_GATEWAY,
    REG_SUN_VERSION_MASTER,
    REG_SWITCH_STATE,
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
    STORAGE_EVENT_LABELS,
    STORAGE_STATE_LABELS,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
    SUN_IC_MIN_WRITE_INTERVAL,
    SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD,
    SWITCH_STATE_LABELS,
    SWITCH_STATE_UNKNOWN_LABEL,
    UNKNOWN_LABEL,
)
from .price_optimizer import PricePlan, SaxPricePlanner

_LOGGER = logging.getLogger(__name__)


def to_signed16(value: int) -> int:
    """Convert an unsigned 16-bit register value to its signed representation."""
    return value - 0x10000 if value >= 0x8000 else value


def to_unsigned16(value: int) -> int:
    """Convert a signed value to its unsigned 16-bit register representation."""
    return value & 0xFFFF


def apply_sunssf(raw_value: int, raw_scale_factor: int) -> float:
    """Apply a SunSpec scale factor register: value * 10**sunssf.

    Beide Rohwerte sind vorzeichenbehaftete 16-Bit-Register (siehe
    modbus.pdf, Abschnitt "SUNSPEC-Scalefaktoren").
    """
    value = to_signed16(raw_value)
    scale_factor = to_signed16(raw_scale_factor)
    return round(value * (10**scale_factor), 3)


def _clamp_int(value: int | None, min_value: int, max_value: int) -> int | None:
    """Klemmt einen Software-seitigen Einstellungswert auf [min_value,
    max_value]; None (= "keine Einstellung") bleibt unverändert.

    NumberEntity validiert min/max bereits selbst beim regulären
    async_set_native_value-Aufruf (Service-Call-Pfad über
    native_min_value/native_max_value) - dieser Clamp schützt zusätzlich den
    RestoreEntity-Pfad (async_added_to_hass), der einen zuvor gespeicherten
    Zustand direkt an den Coordinator durchreicht, ohne diese Validierung zu
    durchlaufen (siehe number.py, z. B. SaxPowerMaxSocNumber).
    """
    if value is None:
        return None
    return max(min_value, min(max_value, value))


def _clamp_float(
    value: float | None, min_value: float, max_value: float
) -> float | None:
    """Wie _clamp_int, für die Preisgrenze des preisoptimierten Ladens
    (EUR/kWh, siehe async_set_price_charge_max_price)."""
    if value is None:
        return None
    return max(min_value, min(max_value, float(value)))


def _time_to_seconds(value: dt_time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


def _window_intervals(start: dt_time, end: dt_time) -> list[tuple[int, int]]:
    """Zerlegt ein halboffenes Zeitfenster [start, end) in ein oder zwei
    zusammenhängende Intervalle (Sekunden seit Mitternacht), damit ein über
    Mitternacht laufendes Fenster (start > end) genauso wie ein normales
    Fenster auf Überlappung mit einem zweiten Fenster geprüft werden kann
    (siehe windows_overlap). start == end gilt als leeres Fenster, analog zu
    SaxPowerCoordinator._is_time_in_window."""
    start_s, end_s = _time_to_seconds(start), _time_to_seconds(end)
    if start_s == end_s:
        return []
    if start_s < end_s:
        return [(start_s, end_s)]
    return [(start_s, 24 * 3600), (0, end_s)]


def windows_overlap(
    start_a: dt_time | None,
    end_a: dt_time | None,
    start_b: dt_time | None,
    end_b: dt_time | None,
) -> bool:
    """True, wenn sich zwei (jeweils halboffene, ggf. über Mitternacht
    laufende) Zeitfenster überschneiden - Grundlage für die
    Nicht-Überlappungs-Prüfung zwischen Netzladung und netzdienlichem Laden
    (siehe anforderung.yaml, REQ-GRID-SERVING-CHARGE). Ein unvollständiges
    Fenster (mindestens eine der vier Zeiten fehlt) gilt als leer und damit
    nie überlappend."""
    if start_a is None or end_a is None or start_b is None or end_b is None:
        return False
    return any(
        a_start < b_end and b_start < a_end
        for a_start, a_end in _window_intervals(start_a, end_a)
        for b_start, b_end in _window_intervals(start_b, end_b)
    )


_MONTH_NAMES_DE = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}


def _format_window_for_message(
    start: dt_time | None, end: dt_time | None, months: set[int]
) -> str:
    """Menschenlesbare Beschreibung eines Zeitfensters (Tageszeit + aktive
    Monate) für die Überschneidungs-Benachrichtigung (siehe
    SaxPowerCoordinator._notify_time_window_overlap)."""
    if start is None or end is None:
        return "kein Zeitfenster gesetzt"
    time_part = f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"
    if months >= ALL_MONTHS:
        months_part = "ganzjährig"
    elif not months:
        months_part = "keine aktiven Monate"
    else:
        months_part = "aktiv: " + ", ".join(
            _MONTH_NAMES_DE[month] for month in sorted(months)
        )
    return f"{time_part} ({months_part})"


def decode_ascii_registers(registers: list[int]) -> str:
    """Decode SunSpec "str (encoded uint16)" registers into ASCII-Text.

    Jedes Register enthält zwei ASCII-Zeichen (High-Byte zuerst). Siehe
    modbus.pdf, z. B. Hersteller-Register 40004-40007 = "SAXPOWER".
    """
    raw = bytearray()
    for reg in registers:
        raw.append((reg >> 8) & 0xFF)
        raw.append(reg & 0xFF)
    return raw.decode("ascii", errors="replace").strip("\x00 ")


class SaxPowerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates Modbus reads/writes for a SAX Power storage system."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AsyncModbusTcpClient,
        slave_id: int,
        slave_id_extended: int,
        scan_interval: int,
        entry_id: str,
        options: Mapping[str, Any] | None = None,
    ) -> None:
        # Der Coordinator-Timer läuft mit dem kürzeren der beiden Intervalle,
        # damit weder der feste HIGH- noch der nutzerkonfigurierte
        # NORMAL-Poll-Zyklus verpasst wird - _async_read_basic/
        # _async_read_extended prüfen anschließend jeweils eigenständig
        # (per Zeitstempel), ob ihr Teilblock auf einem gegebenen Tick
        # tatsächlich fällig ist. Siehe const.READ_BLOCK_EXT_HIGH_INTERVAL
        # sowie anforderung.yaml, REQ-HIGH-INTERVAL-REGISTERS.
        super().__init__(
            hass,
            _LOGGER,
            name="SAX Power",
            update_interval=timedelta(
                seconds=min(scan_interval, READ_BLOCK_EXT_HIGH_INTERVAL)
            ),
        )
        self.client = client
        self.slave_id = slave_id
        self.slave_id_extended = slave_id_extended
        self.entry_id = entry_id
        # Options-Flow-Konfiguration (Strompreis-/PV-Prognose-Sensor, siehe
        # config_flow.SaxPowerOptionsFlow). Nur lesend genutzt; nach einer
        # Änderung lädt __init__.async_update_options den Config Entry neu,
        # sodass hier immer der aktuelle Stand steht.
        self.options: Mapping[str, Any] = dict(options or {})
        self._scan_interval = scan_interval
        self._write_lock = asyncio.Lock()
        self._max_soc: int | None = None
        self._max_soc_clamped = False
        self._max_soc_hold_is_window_bound = False
        self._max_soc_grid_import_wait_cycles = 0
        self._grid_charge_task: asyncio.Task | None = None
        self._grid_charge_power = 0
        self._timed_charge_enabled = False
        self._timed_charge_start: dt_time | None = None
        self._timed_charge_end: dt_time | None = None
        self._timed_charge_active = False
        self._timed_charge_months: set[int] = set(ALL_MONTHS)
        self._timed_charge_min_soc: int | None = None
        self._timed_charge_armed = False
        self._timed_charge_pv_surplus_cycles = 0
        self._grid_serving_enabled = False
        self._grid_serving_start: dt_time | None = None
        self._grid_serving_end: dt_time | None = None
        self._grid_serving_active = False
        self._grid_serving_months: set[int] = set(ALL_MONTHS)
        self._grid_serving_setpoint_active = False
        self._grid_serving_wait_cycles = 0
        self._grid_serving_charge_confirm_cycles = 0
        self._grid_serving_release_confirm_cycles = 0
        # Preisoptimiertes Laden (siehe anforderung.yaml,
        # REQ-DYNAMIC-PRICE-CHARGE): nutzt denselben SunSpec-Schreibpfad
        # (_sun_charge_task) wie zeitgesteuertes/netzdienliches Laden. Der
        # eigentliche Ladeplan liegt im Planner (price_optimizer.py), hier
        # stehen nur die vom Anwender gesetzten Stellgrößen.
        self._price_charge_enabled = False
        self._price_charge_strategy = DEFAULT_PRICE_STRATEGY
        self._price_charge_max_price: float | None = None
        self._price_charge_neutral_price: float | None = None
        self._price_charge_hours: int | None = None
        self._price_charge_active = False
        self._price_charge_status = PRICE_STATUS_OFF
        self.price_planner = SaxPricePlanner(hass, self)
        self._sun_charge_task: asyncio.Task | None = None
        self._sun_charge_power = 0
        self._ic_power_setpoint_sf_raw = to_unsigned16(-2)
        # Cache für den NORMAL-Block (Basic Mode): _async_read_basic befüllt
        # ihn nur alle self._scan_interval Sekunden neu, unabhängig vom
        # (i. d. R. kürzeren) Coordinator-Timer oben.
        self._basic_data: dict[str, Any] = {}
        self._basic_last_read: float | None = None
        # Cache für den HIGH-Block (SunSpec-Modus, dynamische Werte):
        # _async_read_extended befüllt ihn nur alle
        # READ_BLOCK_EXT_HIGH_INTERVAL Sekunden neu.
        self._high_data: dict[str, Any] = {}
        self._high_last_read: float | None = None
        # Cache für die LOW-Intervall-Register (siehe anforderung.yaml,
        # REQ-LOW-INTERVAL-REGISTERS): _async_read_low_block befüllt sie nur
        # alle READ_BLOCK_EXT_LOW_INTERVAL Sekunden neu, _parse_extended
        # verwendet die Battery-Skalierungsfaktoren aus den zuletzt gelesenen
        # Werten statt sie bei jedem Poll erneut zu lesen.
        self._low_block_data: dict[str, Any] = {}
        self._low_block_last_read: float | None = None
        self._battery_capacity_sf_raw = 0
        self._battery_power_sf_raw = 0
        self._battery_soc_sf_raw = 0
        self._battery_cell_voltage_sf_raw = 0
        # Energy-Dashboard-Kompatibilität (siehe anforderung.yaml,
        # REQ-ENERGY-DASHBOARD): laufende kWh-Zähler, aus der Momentanleistung
        # (storage_power_active) per gehaltener Riemann-Summe akkumuliert, da
        # der Speicher selbst keine Energiezähler-Register besitzt. None =
        # "noch nicht initialisiert" (wartet auf restore_energy_charged/
        # restore_energy_discharged über RestoreEntity, siehe sensor.py) -
        # unterscheidet sich damit bewusst von 0.0, siehe _accumulate_energy.
        self._energy_charged_kwh: float | None = None
        self._energy_discharged_kwh: float | None = None
        self._energy_last_ts: float | None = None
        # Basic Mode (Slave-ID self.slave_id) ist die Mindestanforderung für
        # jede Funktion der Integration und lässt das Update fehlschlagen
        # (UpdateFailed), wenn es nicht lesbar ist. Der SunSpec-Modus
        # (Slave-ID self.slave_id_extended, Default 100, siehe modbus.pdf)
        # wird davon bewusst entkoppelt: ist er nicht erreichbar, bleiben
        # die Basic-Mode-Sensoren trotzdem verfügbar und nur die
        # SunSpec-Sensoren zeigen "unbekannt" (siehe anforderung.yaml,
        # REQ-EXTENDED-MODE-RESILIENCE). Vorher führte ein nicht
        # erreichbarer Extended-Mode-Block dazu, dass ConfigEntryNotReady
        # ausgelöst wurde und die Integration gar keine Entities anlegte.
        self._extended_available = True
        # Zeitpunkt (monotonic), seit dem der SunSpec-Modus-Block
        # ununterbrochen nicht erreichbar ist - None, solange er erreichbar
        # ist. Von _async_read_high_block auf der Zustandsflanke gesetzt/
        # zurückgesetzt, von _check_sunspec_persistently_unavailable
        # unten ausgewertet (siehe anforderung.yaml,
        # REQ-SELF-DIAGNOSIS-REPAIRS).
        self._extended_unavailable_since: float | None = None
        # Selbstdiagnose (siehe anforderung.yaml, REQ-SELF-DIAGNOSIS-
        # REPAIRS): self._price_sensor_missing_since hält analog zu
        # self._extended_unavailable_since fest, seit wann der Preis-Sensor
        # ununterbrochen keine auswertbaren Preisdaten liefert. Die
        # *_issue_active-Flags/-Dicts verhindern, dass
        # _async_check_self_diagnostics dasselbe Issue bei jedem Poll-Zyklus
        # erneut anlegt (ir.async_create_issue ist zwar idempotent über die
        # issue_id, ein wiederholter Aufruf wäre aber unnötig).
        self._price_sensor_missing_since: float | None = None
        self._price_sensor_issue_active = False
        self._sunspec_persistent_issue_active = False
        self._max_soc_below_min_soc_issue_active = False
        self._empty_window_issue_active: dict[str, bool] = {}
        self._no_active_months_issue_active: dict[str, bool] = {}
        self._price_neutral_below_limit_issue_active = False

    async def _async_update_data(self) -> dict[str, Any]:
        data = dict(await self._async_read_basic())
        data.update(await self._async_read_extended())
        self._accumulate_energy(data)

        await self._async_enforce_grid_charge(data)
        self._publish_charge_state(data)
        self._async_check_self_diagnostics()
        return data

    def _publish_charge_state(self, data: dict[str, Any]) -> None:
        """Übernimmt die Zustände der drei Lade-Automatiken in
        coordinator.data, damit die zugehörigen Sensoren
        (sensor.py/binary_sensor.py) sie wie jeden anderen Messwert lesen
        können."""
        plan = self.price_planner.plan
        data["timed_charge_active"] = self._timed_charge_active
        data["grid_serving_active"] = self._grid_serving_active
        data["price_charge_active"] = self._price_charge_active
        data["price_charge_status"] = self._price_charge_status
        data["price_charge_next_start"] = plan.next_start
        data["price_charge_current_price"] = plan.current_price

    def _accumulate_energy(self, data: dict[str, Any]) -> None:
        """Akkumuliert geladene/entladene Energie (kWh) aus der aktuell
        bekannten storage_power_active (positiv = Entladung, negativ =
        Ladung, siehe Kommentar bei _watts_to_ic_setpoint_raw) per gehaltener
        Riemann-Summe (Wert seit dem letzten Tick × verstrichene Zeit) - der
        Speicher selbst besitzt keine Energiezähler-Register (siehe
        anforderung.yaml, REQ-ENERGY-DASHBOARD).

        self._energy_last_ts wird unabhängig vom Akkumulieren selbst bei
        jedem Tick als Baseline für den nächsten Aufruf aktualisiert. Beim
        ersten Tick (last_ts is None) sowie während der SunSpec-Modus nicht
        erreichbar ist (power is None, siehe REQ-EXTENDED-MODE-RESILIENCE)
        wird dagegen NICHT akkumuliert, um weder eine unbekannte
        Vor-Leistung noch eine Zeitspanne ohne Leistungswert fälschlich als
        Energie zu verbuchen.

        self._energy_charged_kwh/_energy_discharged_kwh bleiben zusätzlich
        so lange None (statt bei 0.0 zu starten), bis sensor.
        SaxPowerEnergySensor.async_added_to_hass einen zuvor gespeicherten
        Zählerstand per restore_energy_charged/restore_energy_discharged
        eingespielt hat - sonst würde der allererste Update-Lauf (passiert
        in __init__.py bereits vor dem Plattform-Setup, also vor jedem
        RestoreEntity-Restore) einen später restaurierten Zählerstand
        überschreiben."""
        now = monotonic()
        power = data.get("storage_power_active")
        last_ts = self._energy_last_ts
        self._energy_last_ts = now

        if last_ts is not None and power is not None:
            elapsed_hours = (now - last_ts) / 3600
            if self._energy_charged_kwh is not None:
                charge_w = -power if power < 0 else 0
                self._energy_charged_kwh += charge_w * elapsed_hours / 1000
            if self._energy_discharged_kwh is not None:
                discharge_w = power if power > 0 else 0
                self._energy_discharged_kwh += discharge_w * elapsed_hours / 1000

        data["energy_charged"] = (
            round(self._energy_charged_kwh, 3)
            if self._energy_charged_kwh is not None
            else None
        )
        data["energy_discharged"] = (
            round(self._energy_discharged_kwh, 3)
            if self._energy_discharged_kwh is not None
            else None
        )

    def restore_energy_charged(self, value_kwh: float) -> None:
        """Initialisiert den Zähler für geladene Energie mit einem zuvor
        gespeicherten Zustand (siehe sensor.SaxPowerEnergySensor)."""
        self._energy_charged_kwh = max(0.0, value_kwh)

    def restore_energy_discharged(self, value_kwh: float) -> None:
        """Analog zu restore_energy_charged für entladene Energie."""
        self._energy_discharged_kwh = max(0.0, value_kwh)

    async def _async_read_basic(self) -> dict[str, Any]:
        """Liest den NORMAL-Block (Basic Mode, Slave-ID self.slave_id) nur
        alle self._scan_interval Sekunden neu ein - unabhängig vom (durch
        READ_BLOCK_EXT_HIGH_INTERVAL vorgegebenen, i. d. R. kürzeren)
        Coordinator-Timer, siehe __init__ sowie anforderung.yaml,
        REQ-HIGH-INTERVAL-REGISTERS. Anders als beim LOW-Block
        (_async_read_low_block) lässt ein fehlgeschlagener Read weiterhin
        das gesamte Update fehlschlagen (UpdateFailed) - Basic Mode bleibt
        die Mindestanforderung für jede Funktion der Integration."""
        now = monotonic()
        if (
            self._basic_data
            and self._basic_last_read is not None
            and now - self._basic_last_read < self._scan_interval
        ):
            return self._basic_data

        try:
            if not self.client.connected:
                await self.client.connect()
            basic_result = await self.client.read_holding_registers(
                address=READ_BLOCK_START,
                count=READ_BLOCK_COUNT,
                device_id=self.slave_id,
            )
        except (TimeoutError, ModbusException) as err:
            raise UpdateFailed(
                f"Fehler bei der Kommunikation mit dem SAX Speicher (Basic Mode, "
                f"Slave-ID {self.slave_id}): {err}"
            ) from err
        if basic_result.isError():
            raise UpdateFailed(f"Modbus-Fehlerantwort (Basic Mode): {basic_result}")

        basic_regs = basic_result.registers

        def basic_reg(address: int) -> int:
            return basic_regs[address - READ_BLOCK_START]

        switch_state = basic_reg(REG_SWITCH_STATE)
        self._basic_data = {
            "switch_state": switch_state,
            "switch_state_text": SWITCH_STATE_LABELS.get(
                switch_state, SWITCH_STATE_UNKNOWN_LABEL
            ),
            "setpoint_power": to_signed16(basic_reg(REG_SETPOINT_POWER)),
            "setpoint_cosphi": to_signed16(basic_reg(REG_SETPOINT_COSPHI)),
            "soc": basic_reg(REG_SOC),
        }
        self._basic_last_read = now
        return self._basic_data

    async def _async_read_extended(self) -> dict[str, Any]:
        """Orchestriert HIGH- und LOW-Intervall-Teile des SunSpec-Modus-Blocks
        (Slave-ID self.slave_id_extended, Default 100). Der LOW-Block
        (_async_read_low_block) hat sein eigenes, unabhängiges Intervall
        (READ_BLOCK_EXT_LOW_INTERVAL) und wird deshalb bei jedem Tick
        geprüft; der HIGH-Block (_async_read_high_block) wird nur alle
        READ_BLOCK_EXT_HIGH_INTERVAL Sekunden tatsächlich neu vom Gerät
        gelesen. Muss der LOW-Block VOR dem HIGH-Block laufen: Letzterer
        verwendet die dort aktualisierten self._battery_*_sf_raw-Werte,
        statt sie selbst aus dem (inzwischen kleineren) HIGH-Block zu lesen
        - siehe anforderung.yaml, REQ-LOW-INTERVAL-REGISTERS/
        REQ-HIGH-INTERVAL-REGISTERS."""
        data = dict(await self._async_read_low_block())
        data.update(await self._async_read_high_block())
        return data

    @property
    def extended_available(self) -> bool:
        """Ob der SunSpec-Modus-Block zuletzt erreichbar war (siehe
        anforderung.yaml, REQ-EXTENDED-MODE-RESILIENCE) - u. a. für
        diagnostics.py."""
        return self._extended_available

    async def _async_read_high_block(self) -> dict[str, Any]:
        """Read+parse den HIGH-Block (dynamische Mess-/Zustandswerte) des
        SunSpec-Modus, ohne bei Fehlern das gesamte Update scheitern zu
        lassen (siehe Kommentar in __init__). Wird nur alle
        READ_BLOCK_EXT_HIGH_INTERVAL Sekunden tatsächlich neu vom Gerät
        gelesen, unabhängig vom nutzerkonfigurierten NORMAL-Intervall -
        siehe anforderung.yaml, REQ-HIGH-INTERVAL-REGISTERS."""
        now = monotonic()
        if (
            self._high_data
            and self._high_last_read is not None
            and now - self._high_last_read < READ_BLOCK_EXT_HIGH_INTERVAL
        ):
            return self._high_data

        try:
            extended_result = await self.client.read_holding_registers(
                address=READ_BLOCK_EXT_START,
                count=READ_BLOCK_EXT_COUNT,
                device_id=self.slave_id_extended,
            )
            if extended_result.isError():
                raise ModbusException(
                    f"Modbus-Fehlerantwort (SunSpec-Modus): {extended_result}"
                )
        except (TimeoutError, ModbusException) as err:
            if self._extended_available:
                _LOGGER.warning(
                    "SunSpec-Modus-Register (Slave-ID %s) nicht erreichbar - "
                    "Basic-Mode-Sensoren bleiben verfügbar, SunSpec-Sensoren "
                    "zeigen bis zur Wiederherstellung 'unbekannt': %s",
                    self.slave_id_extended,
                    err,
                )
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    f"{ISSUE_EXTENDED_MODE_UNAVAILABLE}_{self.entry_id}",
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key=ISSUE_EXTENDED_MODE_UNAVAILABLE,
                    translation_placeholders={"slave_id": str(self.slave_id_extended)},
                )
                self._extended_unavailable_since = monotonic()
            self._extended_available = False
            self._high_data = {}
            return {}

        if not self._extended_available:
            _LOGGER.info(
                "SunSpec-Modus-Register (Slave-ID %s) wieder erreichbar.",
                self.slave_id_extended,
            )
            ir.async_delete_issue(
                self.hass, DOMAIN, f"{ISSUE_EXTENDED_MODE_UNAVAILABLE}_{self.entry_id}"
            )
            self._extended_unavailable_since = None
        self._extended_available = True

        ext_regs = extended_result.registers

        def ext_reg(address: int) -> int:
            return ext_regs[address - READ_BLOCK_EXT_START]

        self._high_data = self._parse_extended(ext_reg)
        self._high_last_read = now
        return self._high_data

    async def _async_read_low_block(self) -> dict[str, Any]:
        """Liest die beiden statischen LOW-Intervall-Teilbereiche des
        SunSpec-Modus-Blocks (Geräteidentität + Inverter-Modellkopf,
        Battery-Skalierungsfaktoren) nur alle READ_BLOCK_EXT_LOW_INTERVAL
        Sekunden per eigenem read_holding_registers-Aufruf neu ein, statt bei
        jedem regulären Poll - beide Teilbereiche enthalten laut
        modbus_llm.yaml ausschließlich "wellknown" fixe bzw. sich im
        laufenden Betrieb praktisch nie ändernde Werte (siehe
        anforderung.yaml, REQ-LOW-INTERVAL-REGISTERS). Zwischen den
        Refreshs werden die zuletzt gelesenen Werte weiterverwendet; ein
        Scheitern des Refreshs lässt das Update deshalb nicht fehlschlagen."""
        now = monotonic()
        if (
            self._low_block_data
            and self._low_block_last_read is not None
            and now - self._low_block_last_read < READ_BLOCK_EXT_LOW_INTERVAL
        ):
            return self._low_block_data

        try:
            low1_result = await self.client.read_holding_registers(
                address=READ_BLOCK_EXT_LOW1_START,
                count=READ_BLOCK_EXT_LOW1_COUNT,
                device_id=self.slave_id_extended,
            )
            low2_result = await self.client.read_holding_registers(
                address=READ_BLOCK_EXT_LOW2_START,
                count=READ_BLOCK_EXT_LOW2_COUNT,
                device_id=self.slave_id_extended,
            )
            if low1_result.isError() or low2_result.isError():
                raise ModbusException(
                    "Modbus-Fehlerantwort (LOW-Intervall-Register): "
                    f"{low1_result if low1_result.isError() else low2_result}"
                )
        except (TimeoutError, ModbusException) as err:
            if self._low_block_data:
                _LOGGER.debug(
                    "LOW-Intervall-Register (Slave-ID %s) nicht lesbar - "
                    "vorherige Werte werden beibehalten: %s",
                    self.slave_id_extended,
                    err,
                )
            else:
                _LOGGER.warning(
                    "LOW-Intervall-Register (Slave-ID %s) nicht lesbar - "
                    "zugehörige Sensoren zeigen bis zum ersten erfolgreichen "
                    "Refresh 'unbekannt': %s",
                    self.slave_id_extended,
                    err,
                )
            return self._low_block_data

        low1_regs = low1_result.registers
        low2_regs = low2_result.registers

        def low1_reg(address: int) -> int:
            return low1_regs[address - READ_BLOCK_EXT_LOW1_START]

        def low2_reg(address: int) -> int:
            return low2_regs[address - READ_BLOCK_EXT_LOW2_START]

        self._low_block_data = self._parse_low_block(low1_reg, low2_reg)
        self._low_block_last_read = now
        return self._low_block_data

    def _parse_low_block(
        self,
        low1_reg: Callable[[int], int],
        low2_reg: Callable[[int], int],
    ) -> dict[str, Any]:
        """Parse die beiden LOW-Intervall-Teilbereiche (siehe
        _async_read_low_block). Aktualisiert nebenbei die
        self._battery_*_sf_raw-Caches, die _parse_extended für die
        Battery-Messwerte des HIGH-Blocks verwendet - analog zu
        self._ic_power_setpoint_sf_raw in _parse_extended."""
        self._battery_capacity_sf_raw = low2_reg(REG_SUN_BATTERY_CAPACITY_SF)
        self._battery_power_sf_raw = low2_reg(REG_SUN_BATTERY_POWER_SF)
        self._battery_soc_sf_raw = low2_reg(REG_SUN_BATTERY_SOC_SF)
        self._battery_cell_voltage_sf_raw = low2_reg(REG_SUN_BATTERY_CELL_VOLTAGE_SF)

        return {
            "sun_manufacturer": decode_ascii_registers(
                [low1_reg(REG_SUN_MANUFACTURER + i) for i in range(4)]
            ),
            "sun_model": decode_ascii_registers(
                [low1_reg(REG_SUN_MODEL + i) for i in range(3)]
            ),
            "sun_version_master": low1_reg(REG_SUN_VERSION_MASTER),
            "sun_version_gateway": low1_reg(REG_SUN_VERSION_GATEWAY),
            "sun_serial_number": (low1_reg(REG_SUN_SERIAL_HI) << 16)
            | low1_reg(REG_SUN_SERIAL_LO),
        }

    def _parse_extended(self, ext_reg: Callable[[int], int]) -> dict[str, Any]:
        """Parse den HIGH-Intervall-Teil des SunSpec-Modus-Registerblocks
        (Slave-ID 100, modbus.pdf).

        Deckt "3Ph Inverter"- (103, Speicherelektronik), "Immediate
        Controls"- (123), "WYE Connect 3Ph Meter"- (203, Netz/Smart Meter)
        und "Battery Base"-Modell (802, Akkuzellen) ab. Siehe
        anforderung.yaml, REQ-SUNSPEC-MODE-CORRECTION: löst die zuvor
        angenommene, auf realer Hardware nicht existente Slave-ID 40 ab.

        Das SunSpec-Common-Modell (Geräteidentität) sowie die
        Battery-Skalierungsfaktoren liegen inzwischen im separaten
        LOW-Intervall-Block (siehe _async_read_low_block/
        REQ-LOW-INTERVAL-REGISTERS) - Battery-Werte werden deshalb mit den
        zuletzt dort gelesenen self._battery_*_sf_raw skaliert statt mit
        einem eigenen ext_reg-Zugriff.
        """
        storage_current_sf = ext_reg(REG_SUN_STORAGE_CURRENT_SF)
        storage_voltage_sf = ext_reg(REG_SUN_STORAGE_VOLTAGE_SF)
        storage_state = ext_reg(REG_SUN_STORAGE_STATE)
        storage_event = ext_reg(REG_SUN_STORAGE_EVENT)

        control_mode = ext_reg(REG_SUN_IC_CONTROL_MODE)
        # Für den Schreibpfad (Watt -> Prozent-Sollwert) zwischengespeichert,
        # siehe SaxPowerCoordinator._watts_to_ic_setpoint_raw.
        self._ic_power_setpoint_sf_raw = ext_reg(REG_SUN_IC_POWER_SETPOINT_SF)

        meter_current_sf = ext_reg(REG_SUN_METER_CURRENT_SF)
        meter_voltage_sf = ext_reg(REG_SUN_METER_VOLTAGE_SF)
        meter_power_active_sf = ext_reg(REG_SUN_METER_POWER_ACTIVE_SF)

        battery_capacity_sf = self._battery_capacity_sf_raw
        battery_power_sf = self._battery_power_sf_raw
        battery_soc_sf = self._battery_soc_sf_raw
        battery_event = ext_reg(REG_SUN_BATTERY_EVENT)

        return {
            # -- Model 103: 3Ph Inverter (Speicherelektronik) --
            "storage_current_sum": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_CURRENT_SUM), storage_current_sf
            ),
            "storage_current_a": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_CURRENT_A), storage_current_sf
            ),
            "storage_current_b": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_CURRENT_B), storage_current_sf
            ),
            "storage_current_c": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_CURRENT_C), storage_current_sf
            ),
            "storage_voltage_a": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_VOLTAGE_A), storage_voltage_sf
            ),
            "storage_voltage_b": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_VOLTAGE_B), storage_voltage_sf
            ),
            "storage_voltage_c": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_VOLTAGE_C), storage_voltage_sf
            ),
            "storage_power_active": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_POWER_ACTIVE),
                ext_reg(REG_SUN_STORAGE_POWER_ACTIVE_SF),
            ),
            "storage_power_apparent": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_POWER_APPARENT),
                ext_reg(REG_SUN_STORAGE_POWER_APPARENT_SF),
            ),
            "storage_power_reactive": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_POWER_REACTIVE),
                ext_reg(REG_SUN_STORAGE_POWER_REACTIVE_SF),
            ),
            "storage_power_factor": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_POWER_FACTOR),
                ext_reg(REG_SUN_STORAGE_POWER_FACTOR_SF),
            ),
            "storage_frequency": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_FREQUENCY),
                ext_reg(REG_SUN_STORAGE_FREQUENCY_SF),
            ),
            "storage_max_cell_temp": apply_sunssf(
                ext_reg(REG_SUN_STORAGE_MAX_CELL_TEMP), ext_reg(REG_SUN_STORAGE_TEMP_SF)
            ),
            "storage_state": storage_state,
            "storage_state_text": STORAGE_STATE_LABELS.get(
                storage_state, UNKNOWN_LABEL
            ),
            "storage_event": storage_event,
            "storage_event_text": STORAGE_EVENT_LABELS.get(
                storage_event, UNKNOWN_LABEL
            ),
            # PV-Leistung laut modbus.pdf nur mit Smartmeter ADW200 verfügbar
            # - mit ADL400 typischerweise 0, siehe anforderung.yaml.
            "pv_power": apply_sunssf(
                ext_reg(REG_SUN_PV_POWER), ext_reg(REG_SUN_PV_POWER_SF)
            ),
            # -- Model 123: Immediate Controls --
            "ic_power_setpoint_pct": apply_sunssf(
                ext_reg(REG_SUN_IC_POWER_SETPOINT_PCT),
                ext_reg(REG_SUN_IC_POWER_SETPOINT_SF),
            ),
            "ic_timeout": ext_reg(REG_SUN_IC_TIMEOUT),
            "ic_control_mode": control_mode,
            "ic_control_mode_text": CONTROL_MODE_LABELS.get(
                control_mode, UNKNOWN_LABEL
            ),
            "ic_max_power_reference": ext_reg(REG_SUN_IC_MAX_POWER_REFERENCE),
            # -- Model 203: WYE Connect 3Ph Meter (Netz/Smart Meter) --
            "grid_current_sum": apply_sunssf(
                ext_reg(REG_SUN_METER_CURRENT_SUM), meter_current_sf
            ),
            "grid_current_l1": apply_sunssf(
                ext_reg(REG_SUN_METER_CURRENT_L1), meter_current_sf
            ),
            "grid_current_l2": apply_sunssf(
                ext_reg(REG_SUN_METER_CURRENT_L2), meter_current_sf
            ),
            "grid_current_l3": apply_sunssf(
                ext_reg(REG_SUN_METER_CURRENT_L3), meter_current_sf
            ),
            "grid_voltage_ln_avg": apply_sunssf(
                ext_reg(REG_SUN_METER_VOLTAGE_LN_AVG), meter_voltage_sf
            ),
            "grid_voltage_l1": apply_sunssf(
                ext_reg(REG_SUN_METER_VOLTAGE_L1), meter_voltage_sf
            ),
            "grid_voltage_l2": apply_sunssf(
                ext_reg(REG_SUN_METER_VOLTAGE_L2), meter_voltage_sf
            ),
            "grid_voltage_l3": apply_sunssf(
                ext_reg(REG_SUN_METER_VOLTAGE_L3), meter_voltage_sf
            ),
            "grid_frequency": apply_sunssf(
                ext_reg(REG_SUN_METER_FREQUENCY), ext_reg(REG_SUN_METER_FREQUENCY_SF)
            ),
            # Ersetzt das früher fehlerhafte "smartmeter_power" (Basic Mode,
            # Register 48), siehe anforderung.yaml REQ-SUNSPEC-MODE-CORRECTION.
            # Negiert: Standarddarstellung ist negativ = Einspeisung ins Netz
            # (PV-Überschuss), positiv = Netzbezug - das Register selbst
            # meldet das Gegenteil (siehe REQ-SUNSPEC-MODE-CORRECTION,
            # Abschnitt Vorzeichenkonvention).
            "smartmeter_power": -apply_sunssf(
                ext_reg(REG_SUN_METER_POWER_ACTIVE_SUM), meter_power_active_sf
            ),
            "grid_power_active_l1": apply_sunssf(
                ext_reg(REG_SUN_METER_POWER_ACTIVE_L1), meter_power_active_sf
            ),
            "grid_power_active_l2": apply_sunssf(
                ext_reg(REG_SUN_METER_POWER_ACTIVE_L2), meter_power_active_sf
            ),
            "grid_power_active_l3": apply_sunssf(
                ext_reg(REG_SUN_METER_POWER_ACTIVE_L3), meter_power_active_sf
            ),
            "grid_power_apparent_sum": apply_sunssf(
                ext_reg(REG_SUN_METER_POWER_APPARENT_SUM),
                ext_reg(REG_SUN_METER_POWER_APPARENT_SF),
            ),
            "grid_power_reactive_sum": apply_sunssf(
                ext_reg(REG_SUN_METER_POWER_REACTIVE_SUM),
                ext_reg(REG_SUN_METER_POWER_REACTIVE_SF),
            ),
            "grid_power_factor_sum": apply_sunssf(
                ext_reg(REG_SUN_METER_POWER_FACTOR_SUM),
                ext_reg(REG_SUN_METER_POWER_FACTOR_SF),
            ),
            # -- Model 802: Battery Base (Akkuzellen) --
            "battery_capacity": apply_sunssf(
                ext_reg(REG_SUN_BATTERY_CAPACITY), battery_capacity_sf
            ),
            "battery_charge_power_available": apply_sunssf(
                ext_reg(REG_SUN_BATTERY_CHARGE_POWER_AVAILABLE), battery_power_sf
            ),
            "battery_discharge_power_available": apply_sunssf(
                ext_reg(REG_SUN_BATTERY_DISCHARGE_POWER_AVAILABLE), battery_power_sf
            ),
            "battery_soc_max": apply_sunssf(
                ext_reg(REG_SUN_BATTERY_SOC_MAX), battery_soc_sf
            ),
            "battery_soc_min": apply_sunssf(
                ext_reg(REG_SUN_BATTERY_SOC_MIN), battery_soc_sf
            ),
            "battery_soc": apply_sunssf(ext_reg(REG_SUN_BATTERY_SOC), battery_soc_sf),
            "battery_discharge_depth": apply_sunssf(
                ext_reg(REG_SUN_BATTERY_DISCHARGE_DEPTH), battery_soc_sf
            ),
            "battery_charging_active": bool(ext_reg(REG_SUN_BATTERY_CHARGING_ACTIVE)),
            "battery_event": battery_event,
            "battery_event_text": BATTERY_EVENT_LABELS.get(
                battery_event, UNKNOWN_LABEL
            ),
            "battery_cell_voltage_avg": apply_sunssf(
                ext_reg(REG_SUN_BATTERY_CELL_VOLTAGE_AVG),
                self._battery_cell_voltage_sf_raw,
            ),
        }

    async def async_write_register(self, address: int, value: int) -> None:
        """Write a single Basic-Mode holding register (Slave-ID self.slave_id),
        raising HomeAssistantError on failure. Erzwingt beim nächsten
        _async_read_basic-Aufruf einen echten Read, unabhängig vom
        NORMAL-Intervall-Throttle - sonst könnte ein direkt nach dem
        Schreiben ausgelöster coordinator.async_refresh() (siehe
        switch.SaxPowerStorageSwitch) kurzzeitig noch den alten,
        gecachten Wert liefern (siehe DEVELOPMENT.md, "Refresh-Verhalten")."""
        await self._async_write_register(address, value, device_id=self.slave_id)
        self._basic_last_read = None

    async def async_write_extended_register(self, address: int, value: int) -> None:
        """Write a single SunSpec-Modus holding register (Slave-ID
        self.slave_id_extended, interne Adresse = Protokolladresse - 40000),
        raising HomeAssistantError on failure."""
        await self._async_write_register(
            address, value, device_id=self.slave_id_extended
        )

    async def _async_write_register(
        self, address: int, value: int, *, device_id: int
    ) -> None:
        async with self._write_lock:
            try:
                if not self.client.connected:
                    await self.client.connect()
                result = await self.client.write_register(
                    address=address, value=to_unsigned16(value), device_id=device_id
                )
            except (TimeoutError, ModbusException) as err:
                raise HomeAssistantError(
                    f"Schreiben von Register {address} (Slave-ID {device_id}) "
                    f"fehlgeschlagen: {err}"
                ) from err
            if result.isError():
                raise HomeAssistantError(
                    f"Modbus-Fehler beim Schreiben von Register {address} "
                    f"(Slave-ID {device_id}): {result}"
                )

    # -- Max-SOC -----------------------------------------------------------
    # SAX kennt kein natives Max-SOC-Register. Der Coordinator erzwingt den
    # Zielwert stattdessen über denselben SunSpec-Modus-Pfad wie das
    # zeitgesteuerte Laden weiter unten (_async_enforce_grid_charge,
    # _async_sun_charge_loop): Register 40051 (Steuermodus) auf 1
    # (Sollwertvorgabe) und Register 40049 (Leistungsvorgabe) auf 0 %,
    # sobald der SOC den Zielwert erreicht/überschreitet - bewusst
    # unabhängig davon, ob gerade zeitgesteuert geladen wird (siehe
    # anforderung.yaml, REQ-TIMED-SOC-CHARGE): so wird z. B. auch ein durch
    # PV-Überschuss auf den Zielwert geladener Speicher aktiv dort gehalten,
    # statt durch die geräteeigene Automatik (SmartMeter-Nullregelung)
    # darüber hinaus weitergeladen oder unterhalb des Zielwerts
    # leergefahren zu werden. Fällt der SOC wieder unter den Zielwert,
    # wird Register 40051 zurück auf 0 gesetzt.
    #
    # Wurde die Sperre dagegen INNERHALB eines Netzlade- oder netzdienlich-
    # Zeitfensters ausgelöst (_max_soc_hold_is_window_bound), gilt sie nur
    # bis zum Ende genau dieses Zeitfensters: solange das Fenster noch läuft,
    # wird Register 40051 periodisch auf 1 nachgeschrieben (sonst fällt das
    # Gerät nach Ablauf des Timeouts, Register 40050, von selbst auf
    # Nullregelung zurück); ist das Fenster vorbei, wird Register 40051
    # aktiv auf 0 zurückgesetzt, statt den Speicher unbegrenzt im
    # Sollwertmodus zu halten - siehe _async_enforce_grid_charge.
    #
    # Außerhalb jedes Zeitfensters gilt die Sperre grundsätzlich unbegrenzt,
    # ABER: bei gehaltenem 0-%-Sollwert deckt der Speicher den Hausverbrauch
    # nicht mehr mit (Register 40049 = 0 heißt Netto-Leistungsfluss = 0, kein
    # Laden UND kein Entladen), der SOC fällt dadurch im Normalfall nie von
    # selbst unter den Zielwert. Deshalb wertet _async_enforce_grid_charge in
    # diesem Fall zusätzlich am Smart Meter gemessenen Netzbezug
    # (smartmeter_power > SMARTMETER_PV_SURPLUS_THRESHOLD_WATT) als
    # Freigabe-Trigger aus - mit derselben Zyklen-Hysterese
    # (_cycles_confirmed/_max_soc_grid_import_wait_cycles,
    # PV_SURPLUS_HYSTERESIS_CYCLES) wie an den drei anderen Stellen, die
    # diesen Schwellwert auswerten, damit kurze Lastspitzen die Sperre nicht
    # sofort aufheben. Register 40051 wird dann aktiv auf 0
    # (SmartMeter-Nullregelung) zurückgesetzt, damit die geräteeigene
    # Automatik den Hausverbrauch wieder aus dem Speicher decken kann.

    @property
    def max_soc(self) -> int | None:
        return self._max_soc

    @property
    def max_soc_clamped(self) -> bool:
        return self._max_soc_clamped

    async def async_set_max_soc(self, max_soc: int | None) -> None:
        """Set (or clear with None) the software-side max charge SOC.

        Klemmt auf [MIN_SOC, MAX_SOC] statt den Wert ungeprüft zu
        übernehmen - number.SaxPowerMaxSocNumber ruft dies auch beim
        Restaurieren eines gespeicherten Zustands auf (async_added_to_hass),
        ohne die sonst greifende NumberEntity-Min/Max-Validierung des
        regulären Service-Call-Pfads."""
        self._max_soc = _clamp_int(max_soc, MIN_SOC, MAX_SOC)
        await self._async_apply_grid_charge_change()

    # -- Netzladung (Grid Charge, Basic Mode) --------------------------------
    # Das Schreiben von Register 41 versetzt den Speicher laut Doku implizit
    # in den P-Sollwert-Modus. Der Wert muss periodisch wiederholt werden,
    # da der Speicher sonst per Timeout in den vorherigen Modus zurückfällt.
    #
    # Ausschließlich noch für den manuellen start_grid_charge/stop_grid_charge-
    # Service (absoluter Watt-Sollwert, freie Vorzeichenwahl). Zeitgesteuertes
    # Laden nutzt stattdessen den SunSpec-Modus-Pfad weiter unten
    # (_async_sun_charge_loop), siehe dort.

    @property
    def grid_charge_active(self) -> bool:
        return self._grid_charge_task is not None and not self._grid_charge_task.done()

    async def async_start_grid_charge(self, power: int) -> None:
        """Start (or update the setpoint of) periodic grid-charge writes."""
        if not MIN_SETPOINT_POWER <= power <= MAX_SETPOINT_POWER:
            raise HomeAssistantError(
                f"power muss zwischen {MIN_SETPOINT_POWER} und "
                f"{MAX_SETPOINT_POWER} liegen"
            )
        self._grid_charge_power = power
        if self._grid_charge_task is None or self._grid_charge_task.done():
            self._grid_charge_task = self.hass.async_create_background_task(
                self._async_grid_charge_loop(), name="sax_power_grid_charge"
            )

    async def async_stop_grid_charge(self) -> None:
        if self._grid_charge_task is not None:
            self._grid_charge_task.cancel()
            self._grid_charge_task = None

    async def _async_grid_charge_loop(self) -> None:
        try:
            while True:
                await self.async_write_register(
                    REG_SETPOINT_POWER, self._grid_charge_power
                )
                await asyncio.sleep(GRID_CHARGE_WRITE_INTERVAL)
        except asyncio.CancelledError:
            raise
        except HomeAssistantError:
            _LOGGER.exception("Netzladung: periodischer Schreibvorgang fehlgeschlagen")
            raise

    # -- Netzladung (SunSpec-Modus, Immediate Controls) ----------------------
    # Schreibpfad für zeitgesteuertes Laden (siehe Abschnitt weiter unten):
    # SunSpec-Modus (Slave-ID self.slave_id_extended), Modell 123
    # "Immediate Controls".
    #
    # Ablauf laut modbus.pdf/modbus_llm.yaml: Erst Register 40051
    # (Steuermodus) auf 1 (Sollwertvorgabe) setzen, danach kann Register
    # 40049 (Leistungsvorgabe, Prozent der Referenz-Maximalleistung Register
    # 40053) gesetzt werden. Beide Register unterliegen demselben Timeout
    # (Register 40050, siehe REG_SUN_IC_TIMEOUT, max. 300s) und werden vom
    # Gerät verworfen, wenn sie nicht rechtzeitig erneut geschrieben werden -
    # deshalb schreibt die Schleife pro Zyklus beide Register neu (nicht nur
    # den Sollwert), mit einem Intervall, das sicher unterhalb des vom Gerät
    # gemeldeten Timeouts liegt (siehe _sun_ic_write_interval). Beim Stoppen
    # wird Register 40051 aktiv zurück auf 0 (SmartMeter-Nullregelung)
    # gesetzt, statt nur passiv auf den Timeout zu warten.
    #
    # Vorzeichenkonvention für Register 40049 laut modbus.pdf nicht
    # dokumentiert. Hier analog zum Basic-Mode-P-Sollwert (Register 41) und
    # zur gemessenen Wirkleistung (Register 40029, "positiv = Entladung")
    # angenommen: negativ = Laden. Die Integration schreibt hier bewusst nur
    # negative (Lade-)Sollwerte - siehe REG_SUN_IC_POWER_SETPOINT_PCT in
    # const.py für den Hintergrund (frühere, vom Hersteller als nicht
    # vorgesehen bestätigte "manuelle Entladung" mit positiven Sollwerten).

    @property
    def sun_charge_active(self) -> bool:
        return self._sun_charge_task is not None and not self._sun_charge_task.done()

    def _watts_to_ic_setpoint_raw(self, power_watts: int, data: dict[str, Any]) -> int:
        max_power_reference = data.get("ic_max_power_reference")
        if not max_power_reference:
            raise HomeAssistantError(
                "Referenzwert Maximalleistung (Register 40053) noch nicht "
                "bekannt - SunSpec-Modus-Block muss zuerst erfolgreich "
                "gelesen worden sein."
            )
        scale_factor = to_signed16(self._ic_power_setpoint_sf_raw)
        percent = (power_watts / max_power_reference) * 100
        percent = max(
            MIN_IC_POWER_SETPOINT_PCT, min(MAX_IC_POWER_SETPOINT_PCT, percent)
        )
        return to_unsigned16(round(percent / (10**scale_factor)))

    def _sun_ic_write_interval(self) -> int:
        """Wiederholungsintervall für die Schleife: die Hälfte des vom Gerät
        gemeldeten Timeouts (Register 40050), gedeckelt auf
        GRID_CHARGE_WRITE_INTERVAL und SUN_IC_MIN_WRITE_INTERVAL, solange
        kein aktueller Timeout-Wert bekannt ist."""
        timeout = self.data.get("ic_timeout") if self.data is not None else None
        if not timeout:
            return GRID_CHARGE_WRITE_INTERVAL
        return max(
            SUN_IC_MIN_WRITE_INTERVAL, min(timeout // 2, GRID_CHARGE_WRITE_INTERVAL)
        )

    async def async_start_sun_charge(self, power: int) -> None:
        """Start (or update the setpoint of) periodic SunSpec-Modus grid-charge
        writes (Register 40049/40051).

        Ändert sich der Sollwert, während bereits eine Schleife für einen
        ANDEREN Sollwert läuft (z. B. springt die Max-SOC-Sperre an und
        setzt die laufende Netzladung auf 0 % - siehe
        SaxPowerCoordinator._async_enforce_grid_charge), wird sofort
        einmalig geschrieben, statt bis zur nächsten planmäßigen
        Wiederholung der Schleife zu warten (bis zu
        GRID_CHARGE_WRITE_INTERVAL Sekunden später) - eine Einstellungs-
        änderung soll unmittelbar wirken.
        """
        if not MIN_SETPOINT_POWER <= power <= MAX_SETPOINT_POWER:
            raise HomeAssistantError(
                f"power muss zwischen {MIN_SETPOINT_POWER} und "
                f"{MAX_SETPOINT_POWER} liegen"
            )
        power_changed = power != self._sun_charge_power
        self._sun_charge_power = power
        if self._sun_charge_task is None or self._sun_charge_task.done():
            self._sun_charge_task = self.hass.async_create_background_task(
                self._async_sun_charge_loop(), name="sax_power_sun_charge"
            )
        elif power_changed:
            await self.async_write_extended_register(
                REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT
            )
            setpoint_raw = self._watts_to_ic_setpoint_raw(power, self.data or {})
            await self.async_write_extended_register(
                REG_SUN_IC_POWER_SETPOINT_PCT, setpoint_raw
            )

    async def async_stop_sun_charge(self) -> None:
        """No-op, wenn gerade keine SunSpec-Netzladung läuft (analog zu
        async_stop_grid_charge) - schreibt den Steuermodus deshalb nur
        zurück, wenn zuvor tatsächlich ein Lade-Task aktiv war, statt bei
        jedem Aufruf (z. B. beim Entladen des Config Entry) unbedingt in ein
        eventuell vom Nutzer selbst gesetztes Register 40051 einzugreifen."""
        if self._sun_charge_task is None:
            return
        self._sun_charge_task.cancel()
        try:
            await self._sun_charge_task
        except asyncio.CancelledError:
            pass
        except HomeAssistantError:
            # Trifft die Cancellation einen gerade laufenden Modbus-Write,
            # wandelt pymodbus sie in eine ModbusIOException um statt eine
            # reine CancelledError durchzureichen - async_write_register
            # daraus wiederum in HomeAssistantError. Der Task ist damit
            # trotzdem beendet, nur eben nicht über den CancelledError-Pfad.
            pass
        self._sun_charge_task = None
        try:
            await self.async_write_extended_register(
                REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER
            )
        except HomeAssistantError:
            _LOGGER.exception(
                "Netzladung (SunSpec-Modus): Steuermodus konnte nicht auf "
                "SmartMeter-Nullregelung zurückgesetzt werden - Gerät fällt "
                "spätestens nach Ablauf des Timeouts (Register 40050) "
                "automatisch zurück."
            )

    async def _async_sun_charge_loop(self) -> None:
        try:
            while True:
                await self.async_write_extended_register(
                    REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT
                )
                setpoint_raw = self._watts_to_ic_setpoint_raw(
                    self._sun_charge_power, self.data or {}
                )
                await self.async_write_extended_register(
                    REG_SUN_IC_POWER_SETPOINT_PCT, setpoint_raw
                )
                await asyncio.sleep(self._sun_ic_write_interval())
        except asyncio.CancelledError:
            raise
        except HomeAssistantError:
            _LOGGER.exception(
                "Netzladung (SunSpec-Modus): periodischer Schreibvorgang fehlgeschlagen"
            )
            raise

    # -- Zeitgesteuertes Laden ------------------------------------------------
    # Lädt den Speicher innerhalb eines konfigurierbaren Zeitfensters aktiv
    # auf einen Ziel-SOC, unabhängig von PV-Überschuss (z. B. für günstige
    # Nachtstromtarife), über den SunSpec-Modus-Pfad oben
    # (_async_sun_charge_loop). Lädt immer mit maximal möglicher Leistung
    # (MIN_SETPOINT_POWER, sättigt in _watts_to_ic_setpoint_raw auf
    # MIN_IC_POWER_SETPOINT_PCT) - eine frühere, konfigurierbare "Max.
    # Netzladeleistung" (SaxPowerChargeLimitNumber) wurde entfernt: der
    # eingestellte Watt-Wert hatte in der Praxis keinen Einfluss auf die
    # tatsächliche Ladeleistung, weil er ohnehin fast immer auf 100 %
    # sättigte. Der Ziel-SOC nutzt denselben Wert wie "Max. SOC"
    # (self._max_soc, siehe Max-SOC-Abschnitt oben) - fehlt dieser (None),
    # wird MAX_SOC (100 %) als Ziel angenommen. Das vermeidet redundante
    # Einstellmöglichkeiten (siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE).

    @property
    def timed_charge_enabled(self) -> bool:
        return self._timed_charge_enabled

    @property
    def timed_charge_start(self) -> dt_time | None:
        return self._timed_charge_start

    @property
    def timed_charge_end(self) -> dt_time | None:
        return self._timed_charge_end

    @property
    def timed_charge_months(self) -> frozenset[int]:
        return frozenset(self._timed_charge_months)

    @property
    def timed_charge_min_soc(self) -> int | None:
        return self._timed_charge_min_soc

    async def async_set_timed_charge_enabled(
        self, enabled: bool, *, force: bool = False
    ) -> bool:
        """Netzladung ein-/ausschalten. Gibt zurück, ob die Änderung
        übernommen wurde.

        Netzladung und preisoptimiertes Laden (siehe Abschnitt weiter unten)
        laden beide aktiv über denselben SunSpec-Schreibpfad aus dem Netz
        und dürfen deshalb nicht gleichzeitig aktiv sein. Wird die
        Netzladung eingeschaltet, während preisoptimiertes Laden läuft, wird
        die Änderung NICHT stillschweigend ausgeführt, sondern als
        reparierbares Issue zur Bestätigung vorgelegt (siehe
        _async_create_charge_conflict_issue/repairs.py) und hier mit False
        abgelehnt - der Anwender kann dort bestätigen (dann wird
        preisoptimiertes Laden abgeschaltet) oder abbrechen.

        `force=True` überspringt diese Rückfrage und schaltet das jeweils
        andere Feature direkt ab - genutzt vom Bestätigungsdialog selbst,
        vom Service set_price_charge_enabled (nicht-interaktiver
        Automationspfad) sowie beim Restaurieren des gespeicherten Zustands
        beim Start (switch.py), wo per Definition nie beide Features
        gleichzeitig aktiv gespeichert sein können.
        """
        if enabled and self._price_charge_enabled:
            if not force:
                self._async_create_charge_conflict_issue(ISSUE_TIMED_CHARGE_CONFLICT)
                return False
            self._price_charge_enabled = False
        self._timed_charge_enabled = enabled
        self.async_dismiss_charge_conflict()
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()
        return True

    async def async_set_timed_charge_min_soc(self, value: int | None) -> None:
        """Set (or clear with None) den unteren SOC-Schwellwert ("Min. SOC"),
        unterhalb dessen die Netzladung starten darf - siehe
        _async_enforce_grid_charge/_timed_charge_armed für die
        Hysterese-Logik (einmal unterschritten, wird bis zum "Max. SOC"
        durchgeladen, statt bei jedem Überschreiten von Min. SOC sofort
        wieder abzubrechen). Klemmt auf [MIN_SOC, MAX_SOC], siehe
        async_set_max_soc für die Begründung (RestoreEntity-Pfad ohne
        NumberEntity-Validierung)."""
        self._timed_charge_min_soc = _clamp_int(value, MIN_SOC, MAX_SOC)
        await self._async_apply_grid_charge_change()

    async def async_set_timed_charge_start(self, value: dt_time) -> None:
        if self._windows_overlap_with_months(
            value,
            self._timed_charge_end,
            self._timed_charge_months,
            self._grid_serving_start,
            self._grid_serving_end,
            self._grid_serving_months,
        ):
            self._notify_time_window_overlap(
                "Netzladung",
                value,
                self._timed_charge_end,
                self._timed_charge_months,
                "netzdienliches Laden",
                self._grid_serving_start,
                self._grid_serving_end,
                self._grid_serving_months,
            )
            self._timed_charge_start = None
        else:
            self._timed_charge_start = value
        await self._async_apply_grid_charge_change()

    async def async_set_timed_charge_end(self, value: dt_time) -> None:
        if self._windows_overlap_with_months(
            self._timed_charge_start,
            value,
            self._timed_charge_months,
            self._grid_serving_start,
            self._grid_serving_end,
            self._grid_serving_months,
        ):
            self._notify_time_window_overlap(
                "Netzladung",
                self._timed_charge_start,
                value,
                self._timed_charge_months,
                "netzdienliches Laden",
                self._grid_serving_start,
                self._grid_serving_end,
                self._grid_serving_months,
            )
            self._timed_charge_end = None
        else:
            self._timed_charge_end = value
        await self._async_apply_grid_charge_change()

    async def async_set_timed_charge_window(self, start: dt_time, end: dt_time) -> None:
        """Setzt Start und Ende der Netzladung atomar in einem Aufruf.

        Anders als async_set_timed_charge_start/-end (die je nur eine der
        beiden Zeit-Entities bedienen und dabei zwangsläufig gegen den noch
        alten Wert der jeweils anderen Grenze validieren) prüft dies direkt
        das tatsächliche Ziel-Fenster (start, end) - ein durch die
        Zwei-Schritt-Bearbeitung nur kurzzeitig entstehendes, in Wahrheit gar
        nicht beabsichtigtes Zwischenfenster kann die Prüfung dadurch nicht
        mehr fälschlich als Überschneidung erkennen (siehe anforderung.yaml,
        REQ-GRID-SERVING-CHARGE)."""
        if self._windows_overlap_with_months(
            start,
            end,
            self._timed_charge_months,
            self._grid_serving_start,
            self._grid_serving_end,
            self._grid_serving_months,
        ):
            self._notify_time_window_overlap(
                "Netzladung",
                start,
                end,
                self._timed_charge_months,
                "netzdienliches Laden",
                self._grid_serving_start,
                self._grid_serving_end,
                self._grid_serving_months,
            )
            self._timed_charge_start = None
            self._timed_charge_end = None
        else:
            self._timed_charge_start = start
            self._timed_charge_end = end
        await self._async_apply_grid_charge_change()

    async def async_set_timed_charge_month(
        self, month: int, enabled: bool, validate: bool = True
    ) -> None:
        """Nimmt `month` (1-12) in die aktiven Monate der Netzladung auf bzw.
        entfernt ihn daraus. `validate=False` überspringt die
        Überlappungsprüfung - ausschließlich für das Restaurieren des
        gespeicherten Zustands beim Start gedacht (siehe
        SaxPowerMonthSwitch.async_added_to_hass): Da beide Feature-Fenster
        initial auf "alle Monate" stehen und Monate einzeln, nacheinander
        restauriert werden, könnte eine Validierung während dieser
        Zwischenzustände fälschlich fehlschlagen, obwohl der jeweils
        gespeicherte Endzustand gar nicht überlappt."""
        new_months = set(self._timed_charge_months)
        if enabled:
            new_months.add(month)
        else:
            new_months.discard(month)
        if validate:
            self._assert_windows_dont_overlap(
                self._timed_charge_start,
                self._timed_charge_end,
                new_months,
                self._grid_serving_start,
                self._grid_serving_end,
                self._grid_serving_months,
            )
        self._timed_charge_months = new_months
        await self._async_apply_grid_charge_change()

    async def _async_apply_grid_charge_change(self) -> None:
        """Re-evaluate Zeitfenster/Max-SOC/Netzladeleistung sofort nach einer
        Einstellungsänderung, statt bis zum nächsten Poll-Intervall zu
        warten."""
        if self.data is not None:
            await self._async_enforce_grid_charge(self.data)
            self._publish_charge_state(self.data)
            self.async_set_updated_data(self.data)

    def _cycles_confirmed(self, counter_attr: str, condition: bool) -> bool:
        """Zyklen-Hysterese für Vergleiche gegen
        SMARTMETER_PV_SURPLUS_THRESHOLD_WATT: `condition` gilt erst als
        bestätigt (True), nachdem sie in PV_SURPLUS_HYSTERESIS_CYCLES
        aufeinanderfolgenden Aufrufen True war. Ein einzelner False-Wert
        setzt den in `counter_attr` (self-Attribut) gehaltenen Zähler sofort
        zurück, damit kurze Lastspitzen/Messausreißer am Smart Meter keinen
        Zustandswechsel auslösen - siehe const.PV_SURPLUS_HYSTERESIS_CYCLES
        sowie anforderung.yaml, REQ-TIMED-SOC-CHARGE/REQ-GRID-SERVING-CHARGE.
        Von allen vier Stellen genutzt, die SMARTMETER_PV_SURPLUS_THRESHOLD_
        WATT auswerten, damit sie sich einheitlich verhalten.
        """
        count = getattr(self, counter_attr) + 1 if condition else 0
        setattr(self, counter_attr, count)
        return count >= PV_SURPLUS_HYSTERESIS_CYCLES

    @staticmethod
    def _is_time_in_window(
        now: dt_time, start: dt_time | None, end: dt_time | None
    ) -> bool:
        """True, wenn `now` im Zeitfenster [start, end) liegt.

        Unterstützt über Mitternacht laufende Fenster (z. B. 23:00-05:00).
        Ist start == end (oder eines der beiden nicht gesetzt), gilt das
        Fenster als leer (nie aktiv) statt als "ganztägig".
        """
        if start is None or end is None:
            return False
        if start <= end:
            return start <= now < end
        return now >= start or now < end

    @staticmethod
    def _windows_overlap_with_months(
        start_a: dt_time | None,
        end_a: dt_time | None,
        months_a: set[int],
        start_b: dt_time | None,
        end_b: dt_time | None,
        months_b: set[int],
    ) -> bool:
        """True, wenn sich zwei Zeitfenster (Netzladung/netzdienliches Laden)
        sowohl in ihrer Tageszeit (windows_overlap) ALS AUCH in ihren aktiven
        Monaten (months_a/months_b, je ein Set aus 1-12, siehe
        switch.SaxPowerMonthSwitch) überschneiden - siehe anforderung.yaml,
        REQ-GRID-SERVING-CHARGE. Laufen beide Fenster nur in disjunkten
        Monaten (z. B. Netzladung nur November-Januar, netzdienliches Laden
        nur Mai-August), gelten sie NICHT als überlappend, egal wie sehr
        sich die Tageszeiten überschneiden, da die Fenster nie gleichzeitig
        aktiv sein können."""
        return bool(
            windows_overlap(start_a, end_a, start_b, end_b) and (months_a & months_b)
        )

    def _assert_windows_dont_overlap(
        self,
        start_a: dt_time | None,
        end_a: dt_time | None,
        months_a: set[int],
        start_b: dt_time | None,
        end_b: dt_time | None,
        months_b: set[int],
    ) -> None:
        """Bricht mit HomeAssistantError ab, statt eine Monats-Auswahl
        (Netzladung oder netzdienliches Laden) zu übernehmen, die dazu
        führen würde, dass sich ihr Zeitfenster (siehe
        _windows_overlap_with_months) mit dem des jeweils anderen Lademodus
        überschneidet - siehe anforderung.yaml, REQ-GRID-SERVING-CHARGE. Der
        Fehler wird von den Monats-Settern (async_set_timed_charge_month,
        async_set_grid_serving_month) an den aufrufenden Service-Call
        durchgereicht und dadurch dem Anwender im Frontend als Fehler
        angezeigt - unabhängig davon, welche der beiden Monats-Auswahlen
        gerade geändert wird. Die Zeit-Setter (async_set_timed_charge_
        start/-end/-window, async_set_grid_serving_start/-end/-window)
        nutzen _windows_overlap_with_months direkt und lehnen eine
        Überschneidung NICHT mehr mit einem Fehler ab, sondern zeigen eine
        Benachrichtigung und leeren die soeben geänderte Zeit (siehe
        _notify_time_window_overlap) - eine Zeit-Entity lässt sich anders
        als ein Monats-Schalter beim Ablehnen nicht sinnvoll auf einen
        vorherigen Wert zurücksetzen, ohne den Anwender zu verwirren, welcher
        von zwei möglicherweise gerade beide bearbeiteten Werten nun gilt."""
        if self._windows_overlap_with_months(
            start_a, end_a, months_a, start_b, end_b, months_b
        ):
            raise HomeAssistantError(
                "Das Zeitfenster überschneidet sich (Tageszeit UND aktive "
                "Monate) mit dem Zeitfenster des jeweils anderen Lademodus "
                "(Netzladung/netzdienliches Laden). Bitte andere aktive "
                "Monate wählen."
            )

    def _notify_time_window_overlap(
        self,
        feature_label: str,
        start: dt_time | None,
        end: dt_time | None,
        months: set[int],
        other_label: str,
        other_start: dt_time | None,
        other_end: dt_time | None,
        other_months: set[int],
    ) -> None:
        """Zeigt dem Anwender eine Persistent Notification mit beiden
        Zeitfenstern (Tageszeit + aktive Monate) an, statt die Änderung wie
        früher mit HomeAssistantError abzulehnen - siehe anforderung.yaml,
        REQ-GRID-SERVING-CHARGE. Wird ausschließlich von den Zeit-Settern
        (async_set_timed_charge_start/-end/-window,
        async_set_grid_serving_start/-end/-window) aufgerufen, unmittelbar
        bevor diese die soeben geänderte(n) Zeit(en) auf None (leer) setzen
        - eine leere Start- oder Endzeit bewirkt immer, dass das jeweilige
        Feature nicht ausgeführt wird (siehe _is_time_in_window/
        windows_overlap, die ein unvollständiges Fenster als nie aktiv bzw.
        nie überlappend behandeln)."""
        message = (
            f"Das soeben geänderte Zeitfenster für {feature_label} "
            f"({_format_window_for_message(start, end, months)}) überschneidet "
            f"sich mit dem Zeitfenster für {other_label} "
            f"({_format_window_for_message(other_start, other_end, other_months)}). "
            "Die soeben geänderte Zeit wurde geleert, damit das Feature nicht "
            "mit einer widersprüchlichen Konfiguration weiterläuft - bitte "
            "ein nicht überlappendes Zeitfenster oder andere aktive Monate "
            "wählen."
        )
        _LOGGER.warning(message)
        persistent_notification.async_create(
            self.hass,
            message,
            title="SAX Power: Zeitfenster überschneidet sich",
            notification_id=f"{DOMAIN}_{self.entry_id}_window_overlap",
        )

    async def _async_enforce_grid_charge(self, data: dict[str, Any]) -> None:
        """Zentrale Auswertung für Max-SOC-Sperre, zeitgesteuertes Laden,
        preisoptimiertes Laden und netzdienliches Laden - alle vier teilen
        sich den SunSpec-Modus-Schreibpfad (_sun_charge_task). Priorität
        (höchste zuerst):

        1. Ist der Ziel-SOC erreicht/überschritten, hat die Max-SOC-Sperre
           Vorrang: Register 40051 bleibt/wird auf Sollwertvorgabe gesetzt
           und Register 40049 auf 0 % gehalten (siehe Max-SOC-Abschnitt
           oben) - unabhängig davon, ob zeitgesteuertes oder netzdienliches
           Laden aktiviert ist. Wurde die Sperre INNERHALB eines der beiden
           Zeitfenster ausgelöst, gilt sie nur bis zu dessen Ende - danach
           wird Register 40051 aktiv auf 0 (Nullregelung) zurückgesetzt.
           Außerhalb jedes Zeitfensters (z. B. bei einem rein durch
           PV-Überschuss via Nullregelung vollen Speicher) gilt die Sperre
           dagegen unbegrenzt, bis entweder der SOC unter den Zielwert
           fällt ODER am Smart Meter über mehrere Zyklen hinweg Netzbezug
           gemessen wird (siehe _max_soc_hold_is_window_bound sowie den
           Max-SOC-Abschnitt oben zum Netzbezug-Freigabe-Trigger).
        2. Erst wenn die Max-SOC-Sperre nicht greift, kann zeitgesteuertes
           Laden (falls aktiviert, im Zeitfenster, im aktiven Monat - siehe
           "Aktive Monate"-Schalter unten -, mit gesetztem "Min. SOC"
           (siehe unten) UND ohne PV-Überschuss über
           SMARTMETER_PV_SURPLUS_THRESHOLD_WATT) die
           Schleife mit einem echten Ladesollwert übernehmen. Der
           PV-Überschuss-Check läuft dabei über dieselbe Zyklen-Hysterese
           wie die drei anderen Stellen, die diesen Schwellwert auswerten
           (self._cycles_confirmed, self._timed_charge_pv_surplus_cycles,
           PV_SURPLUS_HYSTERESIS_CYCLES): erst wenn der Smart Meter so viele
           Zyklen in Folge PV-Überschuss über dem Schwellwert meldet, beendet
           das die Netzladung - auch mitten im Zeitfenster, nicht erst am
           Fensterende. Ein einzelner Wert unter dem Schwellwert setzt die
           Bestätigung sofort zurück.

           "Min. SOC" (self._timed_charge_min_soc, NumberEntity analog zu
           "Max. SOC"): Netzladung startet nur, wenn der SOC diesen
           Schwellwert unterschritten hat - _timed_charge_armed hält diesen
           "unterschritten"-Zustand als Hysterese fest, damit einmal
           gestartetes Laden bis zum Erreichen von "Max. SOC" durchläuft,
           statt bei jedem erneuten Überschreiten von "Min. SOC" sofort
           wieder abzubrechen (siehe unten, vor der Berechnung von
           timed_should_charge).
        2b. Preisoptimiertes Laden (siehe eigenen Abschnitt weiter unten
           sowie anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE) lädt aus dem
           Netz, sobald der vom Planner (price_optimizer.py) berechnete
           Ladeplan für den aktuellen Zeitpunkt ein ausgewähltes
           Preisfenster meldet. Es
           steht hinter dem zeitgesteuerten Laden zurück (das per
           Bestätigungsdialog ohnehin nicht gleichzeitig aktiv sein kann,
           siehe async_set_timed_charge_enabled) und bricht - wie dieses -
           bei bestätigtem PV-Überschuss sofort ab. Ziel-SOC ist derselbe
           Wert wie "Max. SOC" (keine eigene Einstellung) - ist er erreicht,
           greift dieselbe Max-SOC-Sperre wie bei den anderen beiden
           Lademodi.

           Neutralpreis-Pausezone: lädt preisoptimiertes Laden gerade NICHT
           (price_should_charge False, z. B. weil der aktuelle Preis über
           der Preisgrenze liegt), aber der aktuelle Preis liegt noch
           unterhalb des Neutralpreises (number "Preisoptimiertes Laden
           Neutralpreis"), wird der Speicher statt der normalen
           SmartMeter-Nullregelung aktiv in den manuellen Sollwertmodus mit
           Sollwert 0 geschaltet (price_should_pause,
           async_start_sun_charge(0)) - Laden UND Entladen bleiben
           gestoppt, der komplette Hausverbrauch läuft über das Netz. Erst
           ab dem Neutralpreis lohnt sich die Entladung wieder (die
           Speicherverluste würden sie sonst teurer machen als der direkte
           Netzbezug), der Speicher geht dann zurück in die Nullregelung.
           Dieselben Ausschlussgründe wie bei price_should_charge (Max-SOC-
           Sperre, PV-Überschuss, zeitgesteuertes Laden hat Vorrang) gelten
           auch hier, und die Pausezone blockiert netzdienliches Laden
           genauso wie aktives preisoptimiertes Laden. Fehlt eine der
           beiden Preis-Einstellungen, oder liegt der Neutralpreis nicht
           über der Preisgrenze, bleibt price_should_pause False (siehe
           _check_price_neutral_below_limit für den zugehörigen
           Reparaturhinweis) - Verhalten unverändert wie vor Einführung des
           Neutralpreises.
        3. Netzdienliches Laden (falls aktiviert, im eigenen Zeitfenster, im
           eigenen aktiven Monat UND nicht bereits durch zeitgesteuertes
           oder preisoptimiertes Laden bzw. dessen Neutralpreis-Pausezone
           beansprucht - die Zeitfenster von
           zeitgesteuertem und
           netzdienlichem Laden dürfen sich zusätzlich nicht überschneiden,
           siehe _windows_overlap_with_months/_notify_time_window_overlap)
           läuft als eigene Zustandsmaschine über _async_step_grid_serving,
           NICHT über einen aus dem Smart-Meter-Überschuss berechneten
           Ladesollwert - es wird nie ein Sollwert > 0 geschrieben. Das
           Feature lädt bewusst NIE aktiv aus dem Netz, sondern überlässt
           die eigentliche
           Ladung der geräteeigenen SmartMeter-Nullregelung (Register 40051
           = 0), die von sich aus nur mit echtem PV-Überschuss lädt:

           a. Solange KEIN Eingriff läuft (self._grid_serving_setpoint_active
              False, Speicher in SmartMeter-Nullregelung oder gerade erst ins
              Zeitfenster eingetreten): Sobald die tatsächliche Ladeleistung
              des SAX (negativer Anteil von data["storage_power_active"],
              siehe sensor.py _negative_part("storage_power_active"), "SAX
              Ladeleistung") SMARTMETER_PV_SURPLUS_THRESHOLD_WATT so viele
              Zyklen in Folge erreicht oder überschreitet wie
              PV_SURPLUS_HYSTERESIS_CYCLES vorgibt
              (self._grid_serving_charge_confirm_cycles, dieselbe
              Zyklen-Hysterese wie bei den anderen drei Stellen, die diesen
              Schwellwert auswerten), wechselt der Speicher aktiv in den
              Sollwertvorgabemodus (Register 40051 = 1) UND die Ladung wird
              sofort auf 0 % gestoppt (async_start_sun_charge(0) - macht
              beides in einem Aufruf). Danach wird zusätzlich einmalig
              self._grid_serving_wait_cycles = PV_SURPLUS_HYSTERESIS_CYCLES
              gesetzt: die folgenden Aufrufe von _async_enforce_grid_charge
              tun in dieser Anzahl nichts weiter außer den Zähler
              herunterzuzählen, damit der Moduswechsel/Stopp sich setzen
              kann, bevor Schritt b neu bewertet wird.
           b. Erst wenn der Sollwertvorgabemodus aktiv ist (Schritt a
              ausgelöst UND die Wartezyklen abgelaufen sind) wird geprüft, ob
              die am Smart Meter gemessene Netzeinspeisung
              (data["smartmeter_power"]) so viele Zyklen in Folge unter
              SMARTMETER_PV_SURPLUS_THRESHOLD_WATT gefallen ist
              (self._grid_serving_release_confirm_cycles, dieselbe
              Zyklen-Hysterese). Ist das der Fall, wird der Speicher aktiv
              zurück in die SmartMeter-Nullregelung gesetzt
              (async_stop_sun_charge, Register 40051 = 0) - danach kann
              Schritt a beim nächsten Anstieg der SAX-Ladeleistung erneut
              greifen. Bleibt die Einspeisung weiterhin bei mindestens
              SMARTMETER_PV_SURPLUS_THRESHOLD_WATT (oder fehlt der Messwert,
              oder reißt die Unterschreitung zwischendurch wieder ab - ein
              einzelner Wert über dem Schwellwert setzt die Bestätigung
              sofort zurück), bleibt die Ladung bewusst bei 0 % gehalten -
              der Speicher wird an dieser Stelle erst wieder geladen, sobald
              ein Zeitpunkt mit dauerhaft gefallener Einspeisung erreicht
              ist, das ist der eigentliche Zweck der Funktion.

           Beide Prüfungen sind exklusiv (a nur ohne, b nur mit aktivem
           Sollwertvorgabemodus) - siehe _async_step_grid_serving.
        4. Andernfalls (alle Features deaktiviert, außerhalb Zeitfenster/
           Monat oder SOC erreicht) wird Register 40051 zurück auf 0
           (SmartMeter-Nullregelung) gesetzt und der Zustand der
           netzdienlichen Zustandsmaschine (_grid_serving_setpoint_active/
           _grid_serving_wait_cycles) zurückgesetzt.

        Aktive Monate: Zusätzlich zum Zeitfenster hat jedes Feature 12
        Monats-Schalter (switch.SaxPowerMonthSwitch, "aktiv im Januar" ...
        "aktiv im Dezember"), die festlegen, in welchen Kalendermonaten das
        jeweilige Zeitfenster überhaupt wirksam ist - z. B. Netzladung nur
        November-Januar, netzdienliches Laden nur Mai-August. Default: alle
        Monate aktiv. Ist für ein Feature kein einziger Monat ausgewählt,
        ist es ganzjährig inaktiv (analog zu einem leeren Zeitfenster).
        """
        target_soc = self._max_soc if self._max_soc is not None else MAX_SOC
        current_soc = data["soc"]
        soc_reached = current_soc >= target_soc
        if soc_reached:
            self._timed_charge_armed = False
        elif (
            self._timed_charge_min_soc is not None
            and current_soc < self._timed_charge_min_soc
        ):
            self._timed_charge_armed = True
        smartmeter_power = data.get("smartmeter_power")
        # Vorzeichenkonvention (siehe const.py, SMARTMETER_PV_SURPLUS_
        # THRESHOLD_WATT): negativ = Einspeisung/PV-Überschuss.
        pv_surplus_raw = (
            smartmeter_power is not None
            and smartmeter_power < -SMARTMETER_PV_SURPLUS_THRESHOLD_WATT
        )
        pv_surplus_active = self._cycles_confirmed(
            "_timed_charge_pv_surplus_cycles", pv_surplus_raw
        )
        now = dt_util.now()
        now_time = now.time()
        timed_should_charge = (
            not soc_reached
            and not pv_surplus_active
            and self._timed_charge_enabled
            and now.month in self._timed_charge_months
            and self._is_time_in_window(
                now_time, self._timed_charge_start, self._timed_charge_end
            )
            and self._timed_charge_min_soc is not None
            and self._timed_charge_armed
        )
        # Preisoptimiertes Laden (Punkt 2b, siehe Docstring): teilt sich
        # Ladeleistung, Ziel-SOC ("Max. SOC"), Max-SOC-Sperre und
        # PV-Überschuss-Hysterese mit dem zeitgesteuerten Laden. Der
        # Ladeplan selbst kommt aus dem Planner (price_optimizer.py) und
        # wird dort nur alle PRICE_EVAL_INTERVAL Sekunden neu berechnet -
        # die hier zusätzlich geprüften Abbruchgründe (Max-SOC-Sperre,
        # PV-Überschuss) greifen dagegen sofort bei jedem Poll-Zyklus.
        price_plan = self.price_planner.plan
        price_should_charge = (
            not soc_reached
            and not pv_surplus_active
            and not timed_should_charge
            and self._price_charge_enabled
            and self._price_charge_strategy != PRICE_STRATEGY_OFF
            and price_plan.charge_now
        )
        # Neutralpreis-Pausezone (siehe anforderung.yaml,
        # REQ-DYNAMIC-PRICE-CHARGE): liegt der aktuelle Strompreis über der
        # Preisgrenze, aber noch unter dem Neutralpreis, lohnt sich weder
        # Netzladung (zu teuer) noch eine Entladung aus dem Speicher (die
        # Speicherverluste würden die günstig eingekaufte Energie teurer
        # machen als der direkte Netzbezug) - der Speicher wird deshalb per
        # manuellem Sollwertmodus mit Sollwert 0 von der geräteeigenen
        # SmartMeter-Nullregelung getrennt, statt ihr die Entladung zu
        # überlassen. Erst ab dem Neutralpreis (oder ohne gültige
        # Preisgrenze/Neutralpreis-Kombination, siehe
        # _check_price_neutral_below_limit) bleibt es bei der normalen
        # Nullregelung. Greift nur außerhalb der eigenen Ladefenster
        # (price_should_charge bereits False) und weicht - wie das
        # preisoptimierte Laden selbst - sofort einem PV-Überschuss, damit
        # freie PV-Energie weiterhin ungehindert in den Speicher fließen
        # kann.
        price_should_pause = (
            not soc_reached
            and not pv_surplus_active
            and not timed_should_charge
            and not price_should_charge
            and self._price_charge_enabled
            and self._price_charge_strategy != PRICE_STRATEGY_OFF
            and price_plan.current_price is not None
            and self._price_charge_max_price is not None
            and self._price_charge_neutral_price is not None
            and self._price_charge_max_price < self._price_charge_neutral_price
            and self._price_charge_max_price
            < price_plan.current_price
            < self._price_charge_neutral_price
        )
        grid_serving_window_active = (
            self._grid_serving_enabled
            and now.month in self._grid_serving_months
            and self._is_time_in_window(
                now_time, self._grid_serving_start, self._grid_serving_end
            )
        )
        grid_serving_eligible = (
            not soc_reached
            and grid_serving_window_active
            and not timed_should_charge
            and not price_should_charge
            and not price_should_pause
        )
        if not grid_serving_eligible:
            self._grid_serving_setpoint_active = False
            self._grid_serving_wait_cycles = 0
            self._grid_serving_charge_confirm_cycles = 0
            self._grid_serving_release_confirm_cycles = 0

        max_soc_clamped_now = False
        if soc_reached:
            in_timed_window = (
                self._timed_charge_enabled
                and now.month in self._timed_charge_months
                and self._is_time_in_window(
                    now_time, self._timed_charge_start, self._timed_charge_end
                )
            )
            in_grid_serving_window = (
                self._grid_serving_enabled
                and now.month in self._grid_serving_months
                and self._is_time_in_window(
                    now_time, self._grid_serving_start, self._grid_serving_end
                )
            )
            if in_timed_window or in_grid_serving_window:
                # Ziel-SOC wurde innerhalb eines Netzlade-/netzdienlich-
                # Zeitfensters erreicht (oder die Sperre läuft von einem
                # solchen Fenster weiter) - Sperre bleibt gebunden an dieses
                # Fenster, damit sie spätestens an dessen Ende aktiv
                # aufgehoben wird, statt wie die geräteunabhängige
                # Max-SOC-Sperre unten unbegrenzt zu halten.
                self._max_soc_hold_is_window_bound = True
                self._max_soc_grid_import_wait_cycles = 0
                await self.async_start_sun_charge(0)
                max_soc_clamped_now = True
            elif self._max_soc_hold_is_window_bound:
                # Das Zeitfenster, während dessen die Sperre ausgelöst wurde,
                # ist vorbei - Register 40051 aktiv zurück auf 0 (SmartMeter-
                # Nullregelung) setzen, statt passiv auf den Timeout
                # (Register 40050) zu warten, damit der Speicher wieder im
                # normalen Betriebsmodus arbeitet.
                if self.sun_charge_active:
                    await self.async_stop_sun_charge()
                self._max_soc_hold_is_window_bound = False
                self._max_soc_grid_import_wait_cycles = 0
            else:
                # Geräteunabhängige Max-SOC-Sperre (siehe Abschnitt oben):
                # SOC wurde außerhalb jedes Netzlade-/netzdienlich-
                # Zeitfensters erreicht/überschritten (z. B. durch die
                # geräteeigene Nullregelung bei PV-Überschuss). Ein
                # gehaltener 0-%-Sollwert lässt den SOC nie von selbst unter
                # den Zielwert fallen (der Speicher deckt den Hausverbrauch
                # währenddessen nicht mit) - deshalb zusätzlich Netzbezug am
                # Smart Meter als Freigabe-Trigger auswerten, mit
                # Zyklen-Hysterese gegen kurze Lastspitzen.
                smartmeter_power = data.get("smartmeter_power")
                # Vorzeichenkonvention (siehe const.py, SMARTMETER_PV_
                # SURPLUS_THRESHOLD_WATT): positiv = Netzbezug.
                grid_import_raw = (
                    smartmeter_power is not None
                    and smartmeter_power > SMARTMETER_PV_SURPLUS_THRESHOLD_WATT
                )
                grid_import_confirmed = self._cycles_confirmed(
                    "_max_soc_grid_import_wait_cycles", grid_import_raw
                )
                if grid_import_confirmed:
                    if self.sun_charge_active:
                        await self.async_stop_sun_charge()
                    self._max_soc_grid_import_wait_cycles = 0
                else:
                    await self.async_start_sun_charge(0)
                    max_soc_clamped_now = True
            grid_serving_active_now = False
        else:
            self._max_soc_hold_is_window_bound = False
            self._max_soc_grid_import_wait_cycles = 0
            if timed_should_charge or price_should_charge:
                # MIN_SETPOINT_POWER sättigt in _watts_to_ic_setpoint_raw
                # auf MIN_IC_POWER_SETPOINT_PCT (-100 %, maximale
                # Ladeleistung) - siehe Kommentar am Abschnittsanfang
                # "Zeitgesteuertes Laden" zur entfernten "Max.
                # Netzladeleistung".
                await self.async_start_sun_charge(MIN_SETPOINT_POWER)
                grid_serving_active_now = False
            elif price_should_pause:
                # Neutralpreis-Pausezone: manueller Sollwertmodus mit
                # Sollwert 0 statt Nullregelung - stoppt Laden UND Entladen
                # (derselbe Aufruf wie bei der Max-SOC-Sperre/Schritt a des
                # netzdienlichen Ladens oben).
                await self.async_start_sun_charge(0)
                grid_serving_active_now = False
            elif grid_serving_eligible:
                grid_serving_active_now = await self._async_step_grid_serving(data)
            else:
                grid_serving_active_now = False
                if self.sun_charge_active:
                    await self.async_stop_sun_charge()

        self._timed_charge_active = timed_should_charge
        self._grid_serving_active = grid_serving_active_now
        self._price_charge_active = price_should_charge and not soc_reached
        self._price_charge_status = self._price_charge_status_text(
            price_plan,
            charging=self._price_charge_active,
            paused_neutral_band=price_should_pause,
            soc_reached=soc_reached,
            pv_surplus_active=pv_surplus_active,
            timed_should_charge=timed_should_charge,
        )
        self._max_soc_clamped = max_soc_clamped_now

    async def _async_step_grid_serving(self, data: dict[str, Any]) -> bool:
        """Ein Schritt der unter _async_enforce_grid_charge (Punkt 3)
        beschriebenen Zustandsmaschine für netzdienliches Laden. Nur
        aufgerufen, wenn grid_serving_eligible dort bereits True ist (SOC
        nicht erreicht, Zeitfenster/Monat/Schalter aktiv, kein Vorrang für
        zeitgesteuertes Laden). Gibt zurück, ob netzdienliches Laden gerade
        aktiv in den Sollwertvorgabemodus eingreift (entspricht
        self._grid_serving_setpoint_active nach diesem Aufruf).

        Schritt a (ohne aktiven Sollwertvorgabemodus): Prüft die
        tatsächliche Ladeleistung des SAX (negativer Anteil von
        data["storage_power_active"], siehe sensor.py
        _negative_part("storage_power_active")) gegen
        SMARTMETER_PV_SURPLUS_THRESHOLD_WATT, mit derselben
        Zyklen-Hysterese wie die drei anderen Stellen, die diesen
        Schwellwert auswerten (self._cycles_confirmed,
        PV_SURPLUS_HYSTERESIS_CYCLES) - erst wenn der Speicher selbst (über
        die geräteeigene SmartMeter-Nullregelung) so viele Zyklen in Folge
        mit mindestens diesem Wert lädt, übernimmt die Software aktiv die
        Kontrolle (Sollwertvorgabemodus + Ladung auf 0 % gestoppt in einem
        Aufruf, async_start_sun_charge(0)) und wartet danach zusätzlich
        einmalig PV_SURPLUS_HYSTERESIS_CYCLES Aufrufe dieser Methode ab
        (self._grid_serving_wait_cycles), bevor Schritt b greift - Register
        40051 und der gestoppte Sollwert sollen sich setzen können, bevor
        erneut ausgewertet wird.

        Schritt b (mit aktivem Sollwertvorgabemodus, nach Ablauf der
        Wartezyklen): Prüft die am Smart Meter gemessene Netzeinspeisung
        (data["smartmeter_power"]) gegen denselben Schwellwert, ebenfalls
        mit dieser Zyklen-Hysterese. Erst wenn sie so viele Zyklen in Folge
        unter den Schwellwert fällt, wird der Speicher aktiv zurück in die
        SmartMeter-Nullregelung gesetzt (async_stop_sun_charge). Bleibt die
        Einspeisung mindestens beim Schwellwert (oder ist der Messwert
        gerade nicht bekannt, oder reißt die Unterschreitung zwischendurch
        wieder ab), bleibt die Ladung bewusst bei 0 % gehalten - das ist der
        eigentliche Zweck der Funktion: der Speicher soll erst wieder laden,
        sobald ein Zeitpunkt mit gefallener Einspeisung erreicht ist, nicht
        fortlaufend mit dem Überschuss mitlaufen.
        """
        if not self._grid_serving_setpoint_active:
            storage_power_active = data.get("storage_power_active")
            sax_charge_power = (
                -storage_power_active
                if storage_power_active is not None and storage_power_active < 0
                else 0
            )
            charge_confirmed = self._cycles_confirmed(
                "_grid_serving_charge_confirm_cycles",
                sax_charge_power >= SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
            )
            if charge_confirmed:
                await self.async_start_sun_charge(0)
                self._grid_serving_setpoint_active = True
                self._grid_serving_wait_cycles = PV_SURPLUS_HYSTERESIS_CYCLES
                self._grid_serving_charge_confirm_cycles = 0
            return self._grid_serving_setpoint_active

        if self._grid_serving_wait_cycles > 0:
            self._grid_serving_wait_cycles -= 1
            return True

        smartmeter_power = data.get("smartmeter_power")
        # Vorzeichenkonvention (siehe const.py, SMARTMETER_PV_SURPLUS_
        # THRESHOLD_WATT): Einspeisung (negativ) ist unter den Schwellwert
        # gefallen, sobald der Anzeigewert über -Schwellwert liegt.
        release_confirmed = self._cycles_confirmed(
            "_grid_serving_release_confirm_cycles",
            smartmeter_power is not None
            and smartmeter_power > -SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
        )
        if release_confirmed:
            if self.sun_charge_active:
                await self.async_stop_sun_charge()
            self._grid_serving_setpoint_active = False
            self._grid_serving_release_confirm_cycles = 0
            return False

        return True

    # -- Netzdienliches Laden --------------------------------------------------
    # Eigenständiges, zum zeitgesteuerten Laden oben zeitlich exklusives
    # Feature (siehe _assert_windows_dont_overlap): blockiert das Laden des
    # Speichers innerhalb eines eigenen Zeitfensters aktiv, sobald PV-
    # Überschuss über der Schwelle gemessen wird, damit das Laden in die Zeit
    # mit dem höchsten PV-Ertrag verschoben wird, statt bereits im Fenster
    # stattzufinden. Teilt sich mit zeitgesteuertem Laden denselben
    # SunSpec-Modus-Schreibpfad sowie die Max-SOC-Sperre - "Max.
    # Netzladeleistung" wird hier NICHT benötigt, da nie tatsächlich mit
    # einem Sollwert > 0 geladen wird - siehe _async_enforce_grid_charge für
    # die Priorisierung und anforderung.yaml, REQ-GRID-SERVING-CHARGE.

    @property
    def grid_serving_enabled(self) -> bool:
        return self._grid_serving_enabled

    @property
    def grid_serving_start(self) -> dt_time | None:
        return self._grid_serving_start

    @property
    def grid_serving_end(self) -> dt_time | None:
        return self._grid_serving_end

    @property
    def grid_serving_months(self) -> frozenset[int]:
        return frozenset(self._grid_serving_months)

    @property
    def grid_serving_active(self) -> bool:
        return self._grid_serving_active

    async def async_set_grid_serving_enabled(self, enabled: bool) -> None:
        self._grid_serving_enabled = enabled
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_start(self, value: dt_time) -> None:
        if self._windows_overlap_with_months(
            value,
            self._grid_serving_end,
            self._grid_serving_months,
            self._timed_charge_start,
            self._timed_charge_end,
            self._timed_charge_months,
        ):
            self._notify_time_window_overlap(
                "netzdienliches Laden",
                value,
                self._grid_serving_end,
                self._grid_serving_months,
                "Netzladung",
                self._timed_charge_start,
                self._timed_charge_end,
                self._timed_charge_months,
            )
            self._grid_serving_start = None
        else:
            self._grid_serving_start = value
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_end(self, value: dt_time) -> None:
        if self._windows_overlap_with_months(
            self._grid_serving_start,
            value,
            self._grid_serving_months,
            self._timed_charge_start,
            self._timed_charge_end,
            self._timed_charge_months,
        ):
            self._notify_time_window_overlap(
                "netzdienliches Laden",
                self._grid_serving_start,
                value,
                self._grid_serving_months,
                "Netzladung",
                self._timed_charge_start,
                self._timed_charge_end,
                self._timed_charge_months,
            )
            self._grid_serving_end = None
        else:
            self._grid_serving_end = value
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_window(self, start: dt_time, end: dt_time) -> None:
        """Analog zu async_set_timed_charge_window, für das netzdienliche
        Laden - siehe dort für den Hintergrund (Vermeidung falscher
        Erkennung einer Überschneidung durch Zwischenzustände beim
        getrennten Setzen von Start- und Ende-Entity)."""
        if self._windows_overlap_with_months(
            start,
            end,
            self._grid_serving_months,
            self._timed_charge_start,
            self._timed_charge_end,
            self._timed_charge_months,
        ):
            self._notify_time_window_overlap(
                "netzdienliches Laden",
                start,
                end,
                self._grid_serving_months,
                "Netzladung",
                self._timed_charge_start,
                self._timed_charge_end,
                self._timed_charge_months,
            )
            self._grid_serving_start = None
            self._grid_serving_end = None
        else:
            self._grid_serving_start = start
            self._grid_serving_end = end
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_month(
        self, month: int, enabled: bool, validate: bool = True
    ) -> None:
        """Analog zu async_set_timed_charge_month, für das netzdienliche
        Laden."""
        new_months = set(self._grid_serving_months)
        if enabled:
            new_months.add(month)
        else:
            new_months.discard(month)
        if validate:
            self._assert_windows_dont_overlap(
                self._grid_serving_start,
                self._grid_serving_end,
                new_months,
                self._timed_charge_start,
                self._timed_charge_end,
                self._timed_charge_months,
            )
        self._grid_serving_months = new_months
        await self._async_apply_grid_charge_change()

    # -- Preisoptimiertes Laden ------------------------------------------------
    # Dritte Lade-Automatik neben zeitgesteuertem und netzdienlichem Laden
    # (siehe anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE). Lädt den Speicher
    # aus dem Netz, wenn der Strompreis günstig ist, und überlässt ihn in
    # teuren Phasen der normalen SmartMeter-Nullregelung, sodass die dort
    # gespeicherte Energie den Hausverbrauch deckt.
    #
    # Arbeitsteilung: price_optimizer.SaxPricePlanner liest den vom Anwender
    # ausgewählten Strompreis-Sensor (plus optional eine PV-Prognose) und
    # berechnet daraus alle PRICE_EVAL_INTERVAL Sekunden einen Ladeplan -
    # ohne jeden Modbus-Zugriff. Der Coordinator wertet diesen Plan bei jedem
    # Poll-Zyklus in _async_enforce_grid_charge aus und setzt ihn über
    # denselben SunSpec-Schreibpfad (_sun_charge_task, Register 40051/40049)
    # um wie die beiden anderen Automatiken - inklusive derselben
    # Max-SOC-Sperre und derselben PV-Überschuss-Hysterese.
    #
    # Lädt wie das zeitgesteuerte Laden immer mit maximal möglicher
    # Leistung (siehe Kommentar am Abschnittsanfang "Zeitgesteuertes
    # Laden"). Ziel-SOC: derselbe Wert wie "Max. SOC" (self._max_soc) -
    # keine eigene Einstellung, siehe number.SaxPowerMaxSocNumber.

    @property
    def price_charge_enabled(self) -> bool:
        return self._price_charge_enabled

    @property
    def price_charge_strategy(self) -> str:
        return self._price_charge_strategy

    @property
    def price_charge_max_price(self) -> float | None:
        return self._price_charge_max_price

    @property
    def price_charge_neutral_price(self) -> float | None:
        return self._price_charge_neutral_price

    @property
    def price_charge_hours(self) -> int:
        return (
            self._price_charge_hours
            if self._price_charge_hours is not None
            else DEFAULT_PRICE_HOURS
        )

    @property
    def price_charge_hours_raw(self) -> int | None:
        """Wie price_charge_hours, aber ohne Fallback - für die NumberEntity,
        die zwischen "noch nicht restauriert" (None) und einem echten Wert
        unterscheiden muss (siehe number.SaxPowerPriceChargeHoursNumber)."""
        return self._price_charge_hours

    @property
    def price_charge_active(self) -> bool:
        return self._price_charge_active

    @property
    def price_charge_status(self) -> str:
        return self._price_charge_status

    @property
    def price_plan(self) -> PricePlan:
        return self.price_planner.plan

    async def async_set_price_charge_enabled(
        self, enabled: bool, *, force: bool = False
    ) -> bool:
        """Preisoptimiertes Laden ein-/ausschalten. Gibt zurück, ob die
        Änderung übernommen wurde - siehe async_set_timed_charge_enabled für
        die gemeinsame Konfliktbehandlung mit der Netzladung."""
        if enabled and self._timed_charge_enabled:
            if not force:
                self._async_create_charge_conflict_issue(ISSUE_PRICE_CHARGE_CONFLICT)
                return False
            self._timed_charge_enabled = False
        self._price_charge_enabled = enabled
        self.async_dismiss_charge_conflict()
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()
        return True

    async def async_set_price_charge_strategy(self, strategy: str) -> None:
        if strategy not in PRICE_STRATEGIES:
            raise HomeAssistantError(
                f"Unbekannte Strategie {strategy!r} - erlaubt sind: "
                f"{', '.join(PRICE_STRATEGIES)}"
            )
        self._price_charge_strategy = strategy
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()

    async def async_set_price_charge_max_price(self, value: float | None) -> None:
        """Preisgrenze für den Modus "Absoluter Preis" (EUR/kWh).

        Klemmt auf [MIN_PRICE_LIMIT, MAX_PRICE_LIMIT], siehe async_set_max_soc
        für die Begründung (RestoreEntity-Pfad ohne NumberEntity-Validierung).
        """
        self._price_charge_max_price = _clamp_float(
            value, MIN_PRICE_LIMIT, MAX_PRICE_LIMIT
        )
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()

    async def async_set_price_charge_neutral_price(self, value: float | None) -> None:
        """Neutralpreis (EUR/kWh) - oberhalb der Preisgrenze liegender
        Schwellwert, ab dem sich die Entladung aus dem Speicher wieder
        lohnt (siehe const.py, DEFAULT_PRICE_NEUTRAL, sowie
        _async_enforce_grid_charge zur Pause-Zone dazwischen).

        Klemmt auf denselben Bereich wie die Preisgrenze, siehe
        async_set_price_charge_max_price. Erzwingt keine Reihenfolge
        gegenüber der Preisgrenze - eine falsch herum liegende Kombination
        wird stattdessen von _check_price_neutral_below_limit als
        Reparaturhinweis gemeldet, statt den Wert stillschweigend zu
        verwerfen."""
        self._price_charge_neutral_price = _clamp_float(
            value, MIN_PRICE_LIMIT, MAX_PRICE_LIMIT
        )
        await self._async_apply_grid_charge_change()

    async def async_set_price_charge_hours(self, value: int | None) -> None:
        self._price_charge_hours = _clamp_int(value, MIN_PRICE_HOURS, MAX_PRICE_HOURS)
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()

    async def async_apply_price_plan(self) -> None:
        """Vom Planner nach jeder periodischen Neuberechnung aufgerufen -
        wendet das Ergebnis sofort auf das Gerät an, statt bis zum nächsten
        Poll-Zyklus zu warten."""
        await self._async_apply_grid_charge_change()

    def _price_charge_status_text(
        self,
        plan: PricePlan,
        *,
        charging: bool,
        paused_neutral_band: bool,
        soc_reached: bool,
        pv_surplus_active: bool,
        timed_should_charge: bool,
    ) -> str:
        """Anzeigetext für den Sensor "Preisoptimiertes Laden Status".

        Der Planner kennt nur die Preisseite ("Warten auf Preisabfall",
        "Keine Preisdaten", ...). Hier kommen die Gründe dazu, die das Laden
        unabhängig vom Preis verhindern - in der Reihenfolge, in der
        _async_enforce_grid_charge sie tatsächlich auswertet, damit der
        angezeigte Grund immer der wirksame ist.
        """
        strategy_off = self._price_charge_strategy == PRICE_STRATEGY_OFF
        if not self._price_charge_enabled or strategy_off:
            return PRICE_STATUS_OFF
        if plan.status in (PRICE_STATUS_NO_PRICE_DATA, PRICE_STATUS_PV_FORECAST_COVERS):
            return plan.status
        if charging:
            return PRICE_STATUS_CHARGING
        if soc_reached:
            return PRICE_STATUS_PAUSED_MAX_SOC
        if timed_should_charge:
            return PRICE_STATUS_PAUSED_TIMED_CHARGE
        if pv_surplus_active:
            return PRICE_STATUS_PAUSED_PV_SURPLUS
        if paused_neutral_band:
            return PRICE_STATUS_PAUSED_NEUTRAL_BAND
        return plan.status

    # -- Konflikt Netzladung <-> preisoptimiertes Laden ------------------------
    def _async_create_charge_conflict_issue(self, issue_key: str) -> None:
        """Legt den Bestätigungsdialog an, statt die Aktivierung des zweiten
        netzladenden Features stillschweigend abzulehnen.

        Home Assistant kennt für Entity-Aktionen keinen synchronen
        Bestätigungsdialog; ein reparierbares Issue (repairs.py) ist der
        native Weg zu einem echten Ja/Nein-Dialog. Zusätzlich wird eine
        Persistent Notification erzeugt, damit der Anwender die Rückfrage
        sofort sieht und nicht erst beim nächsten Blick auf
        Einstellungen -> Reparaturen. Beide werden gemeinsam wieder entfernt
        (async_dismiss_charge_conflict).
        """
        if issue_key == ISSUE_PRICE_CHARGE_CONFLICT:
            message = (
                "Preisoptimiertes Laden wurde eingeschaltet, während die "
                "Netzladung (zeitgesteuertes Laden) aktiv ist. Beide laden "
                "aktiv aus dem Netz und können nicht gleichzeitig laufen. "
                "Unter Einstellungen -> Geräte & Dienste -> Reparaturen kann "
                "bestätigt werden, dass die Netzladung dafür abgeschaltet "
                "wird - oder der Vorgang abgebrochen werden. Bis dahin "
                "bleibt preisoptimiertes Laden ausgeschaltet."
            )
        else:
            message = (
                "Die Netzladung (zeitgesteuertes Laden) wurde eingeschaltet, "
                "während preisoptimiertes Laden aktiv ist. Beide laden aktiv "
                "aus dem Netz und können nicht gleichzeitig laufen. Unter "
                "Einstellungen -> Geräte & Dienste -> Reparaturen kann "
                "bestätigt werden, dass preisoptimiertes Laden dafür "
                "abgeschaltet wird - oder der Vorgang abgebrochen werden. Bis "
                "dahin bleibt die Netzladung ausgeschaltet."
            )
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            f"{issue_key}_{self.entry_id}",
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key=issue_key,
            data={"entry_id": self.entry_id, "issue_key": issue_key},
        )
        persistent_notification.async_create(
            self.hass,
            message,
            title="SAX Power: Bestätigung erforderlich",
            notification_id=f"{DOMAIN}_{self.entry_id}_charge_conflict",
        )

    def async_dismiss_charge_conflict(self) -> None:
        """Entfernt Bestätigungsdialog und Benachrichtigung - sowohl nach
        einer Bestätigung als auch nach einem Abbruch, und immer dann, wenn
        eine der beiden Einstellungen erfolgreich geändert wurde (der
        Konflikt ist dann per Definition nicht mehr aktuell)."""
        for issue_key in CHARGE_CONFLICT_ISSUES:
            ir.async_delete_issue(self.hass, DOMAIN, f"{issue_key}_{self.entry_id}")
        persistent_notification.async_dismiss(
            self.hass, f"{DOMAIN}_{self.entry_id}_charge_conflict"
        )

    # -- Selbstdiagnose (siehe anforderung.yaml, REQ-SELF-DIAGNOSIS-REPAIRS) --
    def _async_check_self_diagnostics(self) -> None:
        """Weitere Selbstdiagnose-Prüfungen über den Ladekonflikt
        (_async_create_charge_conflict_issue) und die sofortige SunSpec-
        Nichterreichbarkeits-Warnung (_async_read_high_block) hinaus.

        Bei jedem Poll-Zyklus aus _async_update_data aufgerufen; jede
        einzelne Prüfung legt ihr Issue aber nur auf einer Zustandsflanke
        an bzw. entfernt es wieder, statt es bei jedem Aufruf neu
        anzulegen (ir.async_create_issue wäre zwar idempotent über die
        issue_id, ein wiederholter Aufruf ist aber unnötig)."""
        self._check_price_sensor_missing()
        self._check_sunspec_persistently_unavailable()
        self._check_max_soc_below_min_soc()
        self._check_price_neutral_below_limit()
        self._check_empty_charge_window(
            "timed_charge",
            self._timed_charge_enabled,
            self._timed_charge_start,
            self._timed_charge_end,
            "Netzladung (zeitgesteuertes Laden)",
        )
        self._check_empty_charge_window(
            "grid_serving",
            self._grid_serving_enabled,
            self._grid_serving_start,
            self._grid_serving_end,
            "Netzdienliches Laden",
        )
        self._check_no_active_months(
            "timed_charge",
            self._timed_charge_enabled,
            self._timed_charge_months,
            "Netzladung (zeitgesteuertes Laden)",
        )
        self._check_no_active_months(
            "grid_serving",
            self._grid_serving_enabled,
            self._grid_serving_months,
            "Netzdienliches Laden",
        )

    def _check_price_sensor_missing(self) -> None:
        """Preisoptimiertes Laden ist aktiv, aber der konfigurierte
        Preis-Sensor existiert nicht (mehr) oder liefert seit über
        PRICE_SENSOR_MISSING_GRACE_PERIOD keine auswertbaren Preisdaten
        mehr (price_planner.plan.status == PRICE_STATUS_NO_PRICE_DATA
        impliziert bereits price_charge_enabled UND Strategie != "off",
        siehe price_optimizer.evaluate/compute_plan)."""
        issue_id = f"{ISSUE_PRICE_SENSOR_MISSING}_{self.entry_id}"
        missing = self.price_planner.plan.status == PRICE_STATUS_NO_PRICE_DATA
        if not missing:
            self._price_sensor_missing_since = None
            if self._price_sensor_issue_active:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
                self._price_sensor_issue_active = False
            return

        now = monotonic()
        if self._price_sensor_missing_since is None:
            self._price_sensor_missing_since = now
        if (
            not self._price_sensor_issue_active
            and now - self._price_sensor_missing_since
            >= PRICE_SENSOR_MISSING_GRACE_PERIOD
        ):
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_PRICE_SENSOR_MISSING,
                translation_placeholders={
                    "price_sensor": self.price_planner.price_entity_id or "?"
                },
            )
            self._price_sensor_issue_active = True

    def _check_sunspec_persistently_unavailable(self) -> None:
        """Eskalation von ISSUE_EXTENDED_MODE_UNAVAILABLE (das schon bei der
        ersten Nichterreichbarkeit angelegt wird): hält der Ausfall länger
        als SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD an, betrifft das
        nicht mehr nur die SunSpec-Sensoren, sondern macht auch alle drei
        Lade-Automatiken funktionslos - das verdient eine dringlichere,
        ausführlichere Meldung."""
        issue_id = f"{ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE}_{self.entry_id}"
        if self._extended_available or self._extended_unavailable_since is None:
            if self._sunspec_persistent_issue_active:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
                self._sunspec_persistent_issue_active = False
            return

        if (
            not self._sunspec_persistent_issue_active
            and monotonic() - self._extended_unavailable_since
            >= SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD
        ):
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE,
                translation_placeholders={"slave_id": str(self.slave_id_extended)},
            )
            self._sunspec_persistent_issue_active = True

    def _check_max_soc_below_min_soc(self) -> None:
        """ "Max. SOC" ist gleichzeitig das Ziel-SOC des zeitgesteuerten
        Ladens - liegt es unter "Min. SOC" (dem unteren Start-Schwellwert),
        kann die Netzladung nie starten: der Ladestart wird erst unterhalb
        von Min. SOC ausgelöst, die Max-SOC-Sperre greift aber schon
        vorher. Kein Zustandsflanken-Timer nötig, da es sich um eine
        statische Einstellungskombination statt eines transienten
        Messwerts handelt."""
        issue_id = f"{ISSUE_MAX_SOC_BELOW_MIN_SOC}_{self.entry_id}"
        problem = (
            self._max_soc is not None
            and self._timed_charge_min_soc is not None
            and self._max_soc < self._timed_charge_min_soc
        )
        if not problem:
            if self._max_soc_below_min_soc_issue_active:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
                self._max_soc_below_min_soc_issue_active = False
            return
        if self._max_soc_below_min_soc_issue_active:
            return
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_MAX_SOC_BELOW_MIN_SOC,
            translation_placeholders={
                "max_soc": str(self._max_soc),
                "min_soc": str(self._timed_charge_min_soc),
            },
        )
        self._max_soc_below_min_soc_issue_active = True

    def _check_price_neutral_below_limit(self) -> None:
        """Der Neutralpreis muss über der Preisgrenze liegen, sonst kann die
        in REQ-DYNAMIC-PRICE-CHARGE beschriebene Pause-Zone (Laden UND
        Entladen gestoppt zwischen Preisgrenze und Neutralpreis) nie
        greifen - price_should_pause in _async_enforce_grid_charge bleibt
        in diesem Fall bewusst False, der Speicher verhält sich unverändert
        wie vor Einführung des Neutralpreises. Statische
        Einstellungskombination wie bei _check_max_soc_below_min_soc, kein
        Zustandsflanken-Timer nötig."""
        issue_id = f"{ISSUE_PRICE_NEUTRAL_BELOW_LIMIT}_{self.entry_id}"
        problem = (
            self._price_charge_max_price is not None
            and self._price_charge_neutral_price is not None
            and self._price_charge_neutral_price <= self._price_charge_max_price
        )
        if not problem:
            if self._price_neutral_below_limit_issue_active:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
                self._price_neutral_below_limit_issue_active = False
            return
        if self._price_neutral_below_limit_issue_active:
            return
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_PRICE_NEUTRAL_BELOW_LIMIT,
            translation_placeholders={
                "max_price": str(self._price_charge_max_price),
                "neutral_price": str(self._price_charge_neutral_price),
            },
        )
        self._price_neutral_below_limit_issue_active = True

    def _check_empty_charge_window(
        self,
        feature_key: str,
        enabled: bool,
        start: dt_time | None,
        end: dt_time | None,
        feature_label: str,
    ) -> None:
        """Automatik aktiv, aber Start- und Endzeit ihres Zeitfensters sind
        identisch (siehe _window_intervals: start == end gilt als leeres
        Fenster) - die Automatik läuft dadurch nie, ohne dass das an der
        Entity selbst erkennbar wäre."""
        issue_id = f"{ISSUE_EMPTY_CHARGE_WINDOW}_{feature_key}_{self.entry_id}"
        problem = enabled and start is not None and end is not None and start == end
        active = self._empty_window_issue_active.get(feature_key, False)
        if not problem:
            if active:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
                self._empty_window_issue_active[feature_key] = False
            return
        if active:
            return
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_EMPTY_CHARGE_WINDOW,
            translation_placeholders={"feature": feature_label},
        )
        self._empty_window_issue_active[feature_key] = True

    def _check_no_active_months(
        self,
        feature_key: str,
        enabled: bool,
        months: frozenset[int],
        feature_label: str,
    ) -> None:
        """Automatik aktiv, aber kein einziger Monats-Schalter (switch.py)
        aktiviert - das Feature ist dadurch ganzjährig inaktiv (siehe
        _async_enforce_grid_charge, Abschnitt "Aktive Monate")."""
        issue_id = f"{ISSUE_NO_ACTIVE_MONTHS}_{feature_key}_{self.entry_id}"
        problem = enabled and not months
        active = self._no_active_months_issue_active.get(feature_key, False)
        if not problem:
            if active:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
                self._no_active_months_issue_active[feature_key] = False
            return
        if active:
            return
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_NO_ACTIVE_MONTHS,
            translation_placeholders={"feature": feature_label},
        )
        self._no_active_months_issue_active[feature_key] = True

    async def async_shutdown(self) -> None:
        # super().async_shutdown() (DataUpdateCoordinator) storniert den
        # periodischen Poll-Timer sowie den Debounced-Refresh - ohne diesen
        # Aufruf lief der Timer beim Entladen des Config Entry (siehe
        # __init__.async_unload_entry) unbemerkt im Hintergrund weiter.
        await super().async_shutdown()
        self.price_planner.async_shutdown()
        await self.async_stop_grid_charge()
        await self.async_stop_sun_charge()
        ir.async_delete_issue(
            self.hass, DOMAIN, f"{ISSUE_EXTENDED_MODE_UNAVAILABLE}_{self.entry_id}"
        )
