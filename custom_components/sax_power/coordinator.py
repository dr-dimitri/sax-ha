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
    MAX_SETPOINT_POWER,
    MAX_SOC,
    MIN_SETPOINT_POWER,
    READ_BLOCK_COUNT,
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_START,
    READ_BLOCK_START,
    REG_LIMIT_CHARGE,
    REG_LIMIT_DISCHARGE,
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
    STORAGE_EVENT_LABELS,
    STORAGE_STATE_LABELS,
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
        self._pre_clamp_charge_limit = 0
        self._grid_charge_task: asyncio.Task | None = None
        self._grid_charge_power = 0
        self._discharge_active = False
        self._timed_charge_enabled = False
        self._timed_charge_start: dt_time | None = None
        self._timed_charge_end: dt_time | None = None
        self._timed_charge_active = False
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
            "discharge_limit": basic_reg(REG_LIMIT_DISCHARGE),
            "charge_limit": basic_reg(REG_LIMIT_CHARGE),
        }

        data.update(await self._async_read_extended())

        await self._async_enforce_max_soc(data)
        await self._async_enforce_timed_charge(data)
        data["timed_charge_active"] = self._timed_charge_active
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
        """Write a single holding register, raising HomeAssistantError on failure."""
        async with self._write_lock:
            try:
                if not self.client.connected:
                    await self.client.connect()
                result = await self.client.write_register(
                    address=address, value=to_unsigned16(value), device_id=self.slave_id
                )
            except (TimeoutError, ModbusException) as err:
                raise HomeAssistantError(
                    f"Schreiben von Register {address} fehlgeschlagen: {err}"
                ) from err
            if result.isError():
                raise HomeAssistantError(
                    f"Modbus-Fehler beim Schreiben von Register {address}: {result}"
                )

    # -- Max-SOC -----------------------------------------------------------
    # SAX kennt kein natives Max-SOC-Register. Stattdessen setzt der
    # Coordinator bei Erreichen des Ziel-SOC das Ladelimit-Register (44) auf
    # 0 und stellt beim Unterschreiten den zuvor gelesenen Wert wieder her
    # (siehe anforderung.yaml, Abschnitt 3 "Max. SOC Einstellung").

    @property
    def max_soc(self) -> int | None:
        return self._max_soc

    async def async_set_max_soc(self, max_soc: int | None) -> None:
        """Set (or clear with None) the software-side max charge SOC.

        Wird auch als Ziel-SOC für das zeitgesteuerte Laden verwendet
        (siehe Abschnitt "Zeitgesteuertes Laden" unten) - deshalb hier
        zusätzlich _async_enforce_timed_charge neu auswerten.
        """
        self._max_soc = max_soc
        if self.data is not None:
            await self._async_enforce_max_soc(self.data)
            await self._async_enforce_timed_charge(self.data)
            self.data["timed_charge_active"] = self._timed_charge_active
            self.async_set_updated_data(self.data)

    async def _async_enforce_max_soc(self, data: dict[str, Any]) -> None:
        if self._max_soc is None:
            return

        if data["soc"] >= self._max_soc and not self._max_soc_clamped:
            self._pre_clamp_charge_limit = data["charge_limit"]
            await self.async_write_register(REG_LIMIT_CHARGE, 0)
            self._max_soc_clamped = True
            data["charge_limit"] = 0
        elif data["soc"] < self._max_soc and self._max_soc_clamped:
            await self.async_write_register(
                REG_LIMIT_CHARGE, self._pre_clamp_charge_limit
            )
            self._max_soc_clamped = False
            data["charge_limit"] = self._pre_clamp_charge_limit

    # -- Netzladung (Grid Charge) -------------------------------------------
    # Das Schreiben von Register 41 versetzt den Speicher laut Doku implizit
    # in den P-Sollwert-Modus. Der Wert muss periodisch wiederholt werden,
    # da der Speicher sonst per Timeout in den vorherigen Modus zurückfällt.
    #
    # Hinweis: Dies nutzt weiterhin den Basic-Mode-Weg (Register 41, absolute
    # Watt). modbus.pdf dokumentiert zusätzlich einen offiziellen,
    # prozentualen Weg über den SunSpec-Modus ("Immediate Controls", Modell
    # 123, Register 40049-40051). Diese Integration liest die zugehörigen
    # Werte bereits als Sensoren mit (ic_power_setpoint_pct etc.), stellt sie
    # aber (noch) nicht als Schreibpfad zur Verfügung - das Umstellen eines
    # aktiven Schreibpfads für ein Gerät, das Leistung in ein reales Haus
    # ein-/ausspeist, verdient eine eigene, gezielte Abstimmung statt einer
    # Nebenwirkung dieser Änderung. Siehe anforderung.yaml,
    # REQ-SUNSPEC-MODE-CORRECTION.

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

    @property
    def discharge_active(self) -> bool:
        return self._discharge_active

    async def async_toggle_discharge(self) -> None:
        """Startet die Entladung mit dem zentralen Entladeleistungsgrenzwert
        (Register 43, dieselbe Number-Entity "Entladeleistungsgrenzwert") als
        Sollwert, oder stoppt eine über diese Aktion laufende Entladung
        wieder (erneutes Drücken des Buttons schaltet um). Bewusst keine
        eigene Leistungseinstellung, um keine redundante Einstellmöglichkeit
        zu erzeugen (siehe anforderung.yaml,
        REQ-DISCHARGE-BUTTON-DEDUP-SETTINGS). Nutzt denselben
        Hintergrund-Task wie async_start_grid_charge/das zeitgesteuerte
        Laden, siehe Kommentar oben.
        """
        if self._discharge_active:
            _LOGGER.debug("Entladung stoppen (erneuter Tastendruck).")
            await self.async_stop_grid_charge()
            self._discharge_active = False
            return

        if self.data is None:
            raise HomeAssistantError("Noch keine Daten vom SAX Speicher verfügbar.")
        discharge_limit = self.data["discharge_limit"]
        if discharge_limit <= 0:
            raise HomeAssistantError(
                "Entladeleistungsgrenzwert ist 0 W - es würde kein Sollwert "
                "bewirkt. Bitte zuerst einen Wert über 0 W bei der "
                "Number-Entity 'Entladeleistungsgrenzwert' setzen."
            )
        _LOGGER.debug(
            "Entladung starten: Sollwert %s W auf Register %s.",
            discharge_limit,
            REG_SETPOINT_POWER,
        )
        await self.async_start_grid_charge(discharge_limit)
        self._discharge_active = True

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

    # -- Zeitgesteuertes Laden ----------------------------------------------
    # Lädt den Speicher innerhalb eines konfigurierbaren Zeitfensters aktiv
    # auf einen Ziel-SOC, unabhängig von PV-Überschuss (z. B. für günstige
    # Nachtstromtarife). Nutzt intern denselben Mechanismus wie der
    # `start_grid_charge`-Service (periodischer P-Sollwert-Write auf
    # Register 41 über async_start_grid_charge/async_stop_grid_charge).
    # Sowohl die Ladeleistung (data["charge_limit"], Register 44) als auch
    # der Ziel-SOC sind bewusst KEINE eigenen Einstellungen: Der Ziel-SOC
    # nutzt denselben Wert wie "Maximaler Lade-SOC" (self._max_soc, siehe
    # Max-SOC-Abschnitt oben) - fehlt dieser (None), wird MAX_SOC (100 %)
    # als Ziel angenommen. Das vermeidet redundante Einstellmöglichkeiten
    # (siehe anforderung.yaml, REQ-DISCHARGE-BUTTON-DEDUP-SETTINGS).
    #
    # Wichtig: Zeitgesteuertes Laden und der manuelle
    # `start_grid_charge`/`stop_grid_charge`-Service (sowie der
    # "Entladung starten"-Button) teilen sich denselben Hintergrund-Task
    # (_grid_charge_task). Werden mehrere davon gleichzeitig verwendet,
    # gewinnt der zuletzt schreibende Aufruf - es gibt keine eigene
    # Arbitrierung zwischen ihnen.

    @property
    def timed_charge_enabled(self) -> bool:
        return self._timed_charge_enabled

    @property
    def timed_charge_start(self) -> dt_time | None:
        return self._timed_charge_start

    @property
    def timed_charge_end(self) -> dt_time | None:
        return self._timed_charge_end

    async def async_set_timed_charge_enabled(self, enabled: bool) -> None:
        self._timed_charge_enabled = enabled
        await self._async_apply_timed_charge_change()

    async def async_set_timed_charge_start(self, value: dt_time) -> None:
        self._timed_charge_start = value
        await self._async_apply_timed_charge_change()

    async def async_set_timed_charge_end(self, value: dt_time) -> None:
        self._timed_charge_end = value
        await self._async_apply_timed_charge_change()

    async def _async_apply_timed_charge_change(self) -> None:
        """Re-evaluate das Zeitfenster sofort nach einer Einstellungsänderung,
        statt bis zum nächsten Poll-Intervall zu warten."""
        if self.data is not None:
            await self._async_enforce_timed_charge(self.data)
            self.data["timed_charge_active"] = self._timed_charge_active
            self.async_set_updated_data(self.data)

    def _is_time_in_window(self, now: dt_time) -> bool:
        """True, wenn `now` im konfigurierten Zeitfenster liegt.

        Unterstützt über Mitternacht laufende Fenster (z. B. 23:00-05:00).
        Ist start == end (oder eines der beiden nicht gesetzt), gilt das
        Fenster als leer (nie aktiv) statt als "ganztägig".
        """
        start, end = self._timed_charge_start, self._timed_charge_end
        if start is None or end is None:
            return False
        if start <= end:
            return start <= now < end
        return now >= start or now < end

    async def _async_enforce_timed_charge(self, data: dict[str, Any]) -> None:
        target_soc = self._max_soc if self._max_soc is not None else MAX_SOC
        should_charge = (
            self._timed_charge_enabled
            and self._is_time_in_window(dt_util.now().time())
            and data["soc"] < target_soc
        )
        if should_charge and not self._timed_charge_active:
            await self.async_start_grid_charge(-data["charge_limit"])
            self._timed_charge_active = True
        elif not should_charge and self._timed_charge_active:
            await self.async_stop_grid_charge()
            self._timed_charge_active = False

    async def async_shutdown(self) -> None:
        await self.async_stop_grid_charge()
        ir.async_delete_issue(
            self.hass, DOMAIN, f"{ISSUE_EXTENDED_MODE_UNAVAILABLE}_{self.entry_id}"
        )
