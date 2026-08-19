"""DataUpdateCoordinator for the SAX Power integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import time as dt_time
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    BATTERY_EVENT_LABELS,
    CONTROL_MODE_LABELS,
    DOMAIN,
    GRID_CHARGE_WRITE_INTERVAL,
    ISSUE_EXTENDED_MODE_UNAVAILABLE,
    MAX_IC_POWER_SETPOINT_PCT,
    MAX_SETPOINT_POWER,
    MAX_SOC,
    MIN_IC_POWER_SETPOINT_PCT,
    MIN_SETPOINT_POWER,
    READ_BLOCK_COUNT,
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_START,
    READ_BLOCK_START,
    REG_LIMIT_CHARGE,
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
    SWITCH_STATE_LABELS,
    SWITCH_STATE_UNKNOWN_LABEL,
    UNKNOWN_LABEL,
)

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
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="SAX Power",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.slave_id = slave_id
        self.slave_id_extended = slave_id_extended
        self.entry_id = entry_id
        self._write_lock = asyncio.Lock()
        self._max_soc: int | None = None
        self._max_soc_clamped = False
        self._max_charge_power: int | None = None
        self._grid_charge_task: asyncio.Task | None = None
        self._grid_charge_power = 0
        self._timed_charge_enabled = False
        self._timed_charge_start: dt_time | None = None
        self._timed_charge_end: dt_time | None = None
        self._timed_charge_active = False
        self._grid_serving_enabled = False
        self._grid_serving_start: dt_time | None = None
        self._grid_serving_end: dt_time | None = None
        self._grid_serving_active = False
        self._sun_charge_task: asyncio.Task | None = None
        self._sun_charge_power = 0
        self._ic_power_setpoint_sf_raw = to_unsigned16(-2)
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

    async def _async_update_data(self) -> dict[str, Any]:
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
        data: dict[str, Any] = {
            "switch_state": switch_state,
            "switch_state_text": SWITCH_STATE_LABELS.get(
                switch_state, SWITCH_STATE_UNKNOWN_LABEL
            ),
            "setpoint_power": to_signed16(basic_reg(REG_SETPOINT_POWER)),
            "setpoint_cosphi": to_signed16(basic_reg(REG_SETPOINT_COSPHI)),
            "soc": basic_reg(REG_SOC),
            # Nur noch als einmaliger Vorgabewert für "Max. Netzladeleistung"
            # relevant (siehe SaxPowerChargeLimitNumber.async_added_to_hass) -
            # die Integration schreibt Register 44 nicht mehr.
            "charge_limit": basic_reg(REG_LIMIT_CHARGE),
        }

        data.update(await self._async_read_extended())

        await self._async_enforce_grid_charge(data)
        data["timed_charge_active"] = self._timed_charge_active
        data["grid_serving_active"] = self._grid_serving_active
        return data

    async def _async_read_extended(self) -> dict[str, Any]:
        """Read+parse den SunSpec-Modus-Block (Slave-ID self.slave_id_extended,
        Default 100), ohne bei Fehlern das gesamte Update scheitern zu lassen
        (siehe Kommentar in __init__)."""
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
            self._extended_available = False
            return {}

        if not self._extended_available:
            _LOGGER.info(
                "SunSpec-Modus-Register (Slave-ID %s) wieder erreichbar.",
                self.slave_id_extended,
            )
            ir.async_delete_issue(
                self.hass, DOMAIN, f"{ISSUE_EXTENDED_MODE_UNAVAILABLE}_{self.entry_id}"
            )
        self._extended_available = True

        ext_regs = extended_result.registers

        def ext_reg(address: int) -> int:
            return ext_regs[address - READ_BLOCK_EXT_START]

        return self._parse_extended(ext_reg)

    def _parse_extended(self, ext_reg: Callable[[int], int]) -> dict[str, Any]:
        """Parse den SunSpec-Modus-Registerblock (Slave-ID 100, modbus.pdf).

        Deckt SunSpec Common-, "3Ph Inverter"- (103, Speicherelektronik),
        "Immediate Controls"- (123), "WYE Connect 3Ph Meter"- (203, Netz/
        Smart Meter) und "Battery Base"-Modell (802, Akkuzellen) ab. Siehe
        anforderung.yaml, REQ-SUNSPEC-MODE-CORRECTION: löst die zuvor
        angenommene, auf realer Hardware nicht existente Slave-ID 40 ab.
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

        battery_capacity_sf = ext_reg(REG_SUN_BATTERY_CAPACITY_SF)
        battery_power_sf = ext_reg(REG_SUN_BATTERY_POWER_SF)
        battery_soc_sf = ext_reg(REG_SUN_BATTERY_SOC_SF)
        battery_event = ext_reg(REG_SUN_BATTERY_EVENT)

        return {
            # -- SunSpec Common (Identität, Diagnose) --
            "sun_manufacturer": decode_ascii_registers(
                [ext_reg(REG_SUN_MANUFACTURER + i) for i in range(4)]
            ),
            "sun_model": decode_ascii_registers(
                [ext_reg(REG_SUN_MODEL + i) for i in range(3)]
            ),
            "sun_version_master": ext_reg(REG_SUN_VERSION_MASTER),
            "sun_version_gateway": ext_reg(REG_SUN_VERSION_GATEWAY),
            "sun_serial_number": (ext_reg(REG_SUN_SERIAL_HI) << 16)
            | ext_reg(REG_SUN_SERIAL_LO),
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
            "smartmeter_power": apply_sunssf(
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
                ext_reg(REG_SUN_BATTERY_CELL_VOLTAGE_SF),
            ),
        }

    async def async_write_register(self, address: int, value: int) -> None:
        """Write a single Basic-Mode holding register (Slave-ID self.slave_id),
        raising HomeAssistantError on failure."""
        await self._async_write_register(address, value, device_id=self.slave_id)

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

    @property
    def max_soc(self) -> int | None:
        return self._max_soc

    @property
    def max_soc_clamped(self) -> bool:
        return self._max_soc_clamped

    async def async_set_max_soc(self, max_soc: int | None) -> None:
        """Set (or clear with None) the software-side max charge SOC."""
        self._max_soc = max_soc
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
    # (_async_sun_charge_loop). Nutzt "Max. Netzladeleistung"
    # (self._max_charge_power) als Leistung - ein reiner Software-Zustand
    # (kein direkter Register-Write mehr auf das Basic-Mode-Register 44),
    # der vom Speicher nur berücksichtigt wird, während Register 40051 auf
    # Sollwertvorgabe steht (siehe SaxPowerChargeLimitNumber). Der Ziel-SOC
    # nutzt denselben Wert wie "Max. SOC" (self._max_soc, siehe
    # Max-SOC-Abschnitt oben) - fehlt dieser (None), wird MAX_SOC (100 %)
    # als Ziel angenommen. Das vermeidet redundante Einstellmöglichkeiten
    # (siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE).

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
    def max_charge_power(self) -> int | None:
        return self._max_charge_power

    async def async_set_timed_charge_enabled(self, enabled: bool) -> None:
        self._timed_charge_enabled = enabled
        await self._async_apply_grid_charge_change()

    async def async_set_timed_charge_start(self, value: dt_time) -> None:
        self._assert_windows_dont_overlap(
            value,
            self._timed_charge_end,
            self._grid_serving_start,
            self._grid_serving_end,
        )
        self._timed_charge_start = value
        await self._async_apply_grid_charge_change()

    async def async_set_timed_charge_end(self, value: dt_time) -> None:
        self._assert_windows_dont_overlap(
            self._timed_charge_start,
            value,
            self._grid_serving_start,
            self._grid_serving_end,
        )
        self._timed_charge_end = value
        await self._async_apply_grid_charge_change()

    async def async_set_max_charge_power(self, value: int | None) -> None:
        """Set the software-side target power (Watt) for "Max. Netzladeleistung"."""
        self._max_charge_power = value
        await self._async_apply_grid_charge_change()

    async def _async_apply_grid_charge_change(self) -> None:
        """Re-evaluate Zeitfenster/Max-SOC/Netzladeleistung sofort nach einer
        Einstellungsänderung, statt bis zum nächsten Poll-Intervall zu
        warten."""
        if self.data is not None:
            await self._async_enforce_grid_charge(self.data)
            self.data["timed_charge_active"] = self._timed_charge_active
            self.data["grid_serving_active"] = self._grid_serving_active
            self.async_set_updated_data(self.data)

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

    def _assert_windows_dont_overlap(
        self,
        start_a: dt_time | None,
        end_a: dt_time | None,
        start_b: dt_time | None,
        end_b: dt_time | None,
    ) -> None:
        """Bricht mit HomeAssistantError ab, statt ein Zeitfenster (Netzladung
        oder netzdienliches Laden) zu übernehmen, das sich mit dem jeweils
        anderen Fenster überschneiden würde - siehe anforderung.yaml,
        REQ-GRID-SERVING-CHARGE. Der Fehler wird von den vier
        Time-Entity-Settern (async_set_timed_charge_start/-end,
        async_set_grid_serving_start/-end) an den aufrufenden Service-Call
        durchgereicht und dadurch dem Anwender im Frontend als Fehler
        angezeigt - unabhängig davon, welches der beiden Fenster gerade
        geändert wird."""
        if windows_overlap(start_a, end_a, start_b, end_b):
            raise HomeAssistantError(
                "Das Zeitfenster überschneidet sich mit dem Zeitfenster des "
                "jeweils anderen Lademodus (Netzladung/netzdienliches Laden). "
                "Bitte ein nicht überlappendes Zeitfenster wählen."
            )

    async def _async_enforce_grid_charge(self, data: dict[str, Any]) -> None:
        """Zentrale Auswertung für Max-SOC-Sperre, zeitgesteuertes Laden und
        netzdienliches Laden - alle drei teilen sich den
        SunSpec-Modus-Schreibpfad (_sun_charge_task). Priorität (höchste
        zuerst):

        1. Ist der Ziel-SOC erreicht/überschritten, hat die Max-SOC-Sperre
           Vorrang: Register 40051 bleibt/wird auf Sollwertvorgabe gesetzt
           und Register 40049 auf 0 % gehalten (siehe Max-SOC-Abschnitt
           oben) - unabhängig davon, ob zeitgesteuertes oder netzdienliches
           Laden aktiviert ist.
        2. Erst wenn die Max-SOC-Sperre nicht greift, kann zeitgesteuertes
           Laden (falls aktiviert, im Zeitfenster, mit gesetzter "Max.
           Netzladeleistung" UND ohne PV-Überschuss über
           SMARTMETER_PV_SURPLUS_THRESHOLD_WATT) die Schleife mit einem
           echten Ladesollwert übernehmen. Ein PV-Überschuss beendet die
           Netzladung dabei auch mitten im Zeitfenster, sobald er beim
           nächsten Poll-Zyklus erkannt wird - nicht erst am Fensterende.
        3. Netzdienliches Laden (falls aktiviert, im eigenen Zeitfenster, mit
           gesetzter "Max. Netzladeleistung" UND mit PV-Überschuss über
           SMARTMETER_PV_SURPLUS_THRESHOLD_WATT) kann parallel zu Schritt 2
           ausgewertet werden, da beide Bedingungen sich bereits über
           pv_surplus_active gegenseitig ausschließen (zeitgesteuertes Laden
           verlangt KEINEN, netzdienliches Laden verlangt EINEN
           PV-Überschuss) - die genau umgekehrte PV-Bedingung zum
           zeitgesteuerten Laden. Das Feature lädt bewusst NIE aus dem Netz,
           sondern ausschließlich mit dem gerade am Smart Meter gemessenen
           PV-Überschuss, auf "Max. Netzladeleistung" gedeckelt
           (min(max_charge_power, smartmeter_power)) - sinkt der Überschuss,
           sinkt der Sollwert im selben Poll-Zyklus mit, es wird also nie
           mehr geladen als gerade an Überschuss verfügbar ist. Die
           Zeitfenster von zeitgesteuertem und netzdienlichem Laden dürfen
           sich zusätzlich nicht überschneiden (siehe
           _assert_windows_dont_overlap) - das ist eine reine
           Konfigurationsregel für den Anwender, keine Voraussetzung für
           sicheren Betrieb.
        4. Andernfalls wird Register 40051 zurück auf 0 (SmartMeter-
           Nullregelung) gesetzt.

        PV-Überschuss-Erkennung: data["smartmeter_power"] (Register 40072,
        siehe REG_SUN_METER_POWER_ACTIVE_SUM) ist bereits derselbe,
        vorzeichenrichtig umgerechnete Wert, der auch im "Smart Meter
        Leistung"-Sensor angezeigt wird (sensor.py, _direct). Laut Anwender
        bedeutet ein POSITIVER Anzeigewert Überschuss aus der
        Dachphotovoltaik - der rohe Registerinhalt selbst kann davon
        abweichende Vorzeichen haben (siehe apply_sunssf/to_signed16), daher
        wird hier bewusst der bereits umgerechnete Anzeigewert ausgewertet,
        nicht das Rohregister. Fehlt der Wert (z. B. SunSpec-Modus gerade
        nicht erreichbar), blockiert das die Netzladung nicht, verhindert
        aber netzdienliches Laden (siehe unten - ohne bekannten Überschuss
        kann nicht sichergestellt werden, dass nicht aus dem Netz geladen
        wird).
        """
        target_soc = self._max_soc if self._max_soc is not None else MAX_SOC
        soc_reached = data["soc"] >= target_soc
        smartmeter_power = data.get("smartmeter_power")
        pv_surplus_active = (
            smartmeter_power is not None
            and smartmeter_power > SMARTMETER_PV_SURPLUS_THRESHOLD_WATT
        )
        now = dt_util.now().time()
        timed_should_charge = (
            not soc_reached
            and not pv_surplus_active
            and self._timed_charge_enabled
            and self._is_time_in_window(
                now, self._timed_charge_start, self._timed_charge_end
            )
            and self._max_charge_power is not None
        )
        grid_serving_should_charge = (
            not soc_reached
            and pv_surplus_active
            and self._grid_serving_enabled
            and self._is_time_in_window(
                now, self._grid_serving_start, self._grid_serving_end
            )
            and self._max_charge_power is not None
        )

        if soc_reached:
            await self.async_start_sun_charge(0)
        elif timed_should_charge:
            await self.async_start_sun_charge(-self._max_charge_power)
        elif grid_serving_should_charge:
            # smartmeter_power ist hier != None (sonst wäre pv_surplus_active
            # False) und > SMARTMETER_PV_SURPLUS_THRESHOLD_WATT > 0.
            charge_power = min(self._max_charge_power, round(smartmeter_power))
            await self.async_start_sun_charge(-charge_power)
        elif self.sun_charge_active:
            await self.async_stop_sun_charge()

        self._timed_charge_active = timed_should_charge
        self._grid_serving_active = grid_serving_should_charge
        self._max_soc_clamped = soc_reached

    # -- Netzdienliches Laden --------------------------------------------------
    # Eigenständiges, zum zeitgesteuerten Laden oben zeitlich exklusives
    # Feature (siehe _assert_windows_dont_overlap): lädt den Speicher
    # innerhalb eines eigenen Zeitfensters, aber NUR mit PV-Überschuss - nie
    # aus dem Netz. Teilt sich mit zeitgesteuertem Laden denselben
    # SunSpec-Modus-Schreibpfad sowie die Max-SOC-Sperre und "Max.
    # Netzladeleistung" (self._max_charge_power) als Leistungsobergrenze -
    # siehe _async_enforce_grid_charge für die Priorisierung und
    # anforderung.yaml, REQ-GRID-SERVING-CHARGE.

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
    def grid_serving_active(self) -> bool:
        return self._grid_serving_active

    async def async_set_grid_serving_enabled(self, enabled: bool) -> None:
        self._grid_serving_enabled = enabled
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_start(self, value: dt_time) -> None:
        self._assert_windows_dont_overlap(
            value,
            self._grid_serving_end,
            self._timed_charge_start,
            self._timed_charge_end,
        )
        self._grid_serving_start = value
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_end(self, value: dt_time) -> None:
        self._assert_windows_dont_overlap(
            self._grid_serving_start,
            value,
            self._timed_charge_start,
            self._timed_charge_end,
        )
        self._grid_serving_end = value
        await self._async_apply_grid_charge_change()

    async def async_shutdown(self) -> None:
        # super().async_shutdown() (DataUpdateCoordinator) storniert den
        # periodischen Poll-Timer sowie den Debounced-Refresh - ohne diesen
        # Aufruf lief der Timer beim Entladen des Config Entry (siehe
        # __init__.async_unload_entry) unbemerkt im Hintergrund weiter.
        await super().async_shutdown()
        await self.async_stop_grid_charge()
        await self.async_stop_sun_charge()
        ir.async_delete_issue(
            self.hass, DOMAIN, f"{ISSUE_EXTENDED_MODE_UNAVAILABLE}_{self.entry_id}"
        )
