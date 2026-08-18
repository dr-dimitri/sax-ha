"""DataUpdateCoordinator for the SAX Power integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    DOMAIN,
    GRID_CHARGE_WRITE_INTERVAL,
    MAX_SETPOINT_POWER,
    MIN_SETPOINT_POWER,
    READ_BLOCK_COUNT,
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_START,
    READ_BLOCK_START,
    REG_EXT_CURRENT_L1,
    REG_EXT_CURRENT_L2,
    REG_EXT_CURRENT_L3,
    REG_EXT_CURRENT_SF,
    REG_EXT_CURRENT_SUM,
    REG_EXT_FREQUENCY,
    REG_EXT_FREQUENCY_SF,
    REG_EXT_POWER_ACTIVE,
    REG_EXT_POWER_ACTIVE_SF,
    REG_EXT_POWER_APPARENT,
    REG_EXT_POWER_APPARENT_SF,
    REG_EXT_POWER_FACTOR,
    REG_EXT_POWER_FACTOR_SF,
    REG_EXT_POWER_REACTIVE,
    REG_EXT_POWER_REACTIVE_SF,
    REG_EXT_SM_CURRENT_L1,
    REG_EXT_SM_CURRENT_L2,
    REG_EXT_SM_CURRENT_L3,
    REG_EXT_SM_ENERGY_CONSUMED,
    REG_EXT_SM_ENERGY_FED_IN,
    REG_EXT_SM_ENERGY_SF,
    REG_EXT_SM_POWER_L1,
    REG_EXT_SM_POWER_L2,
    REG_EXT_SM_POWER_L3,
    REG_EXT_SM_POWER_SF,
    REG_EXT_SM_POWER_TOTAL,
    REG_EXT_SM_SWITCH_STATE,
    REG_EXT_SM_VOLTAGE_L1,
    REG_EXT_SM_VOLTAGE_L2,
    REG_EXT_SM_VOLTAGE_L3,
    REG_EXT_SUNSPEC_ID,
    REG_EXT_SUNSPEC_LENGTH,
    REG_EXT_VOLTAGE_L1,
    REG_EXT_VOLTAGE_L2,
    REG_EXT_VOLTAGE_L3,
    REG_EXT_VOLTAGE_SF,
    REG_LIMIT_CHARGE,
    REG_LIMIT_DISCHARGE,
    REG_POWER,
    REG_SETPOINT_COSPHI,
    REG_SETPOINT_POWER,
    REG_SMARTMETER_POWER,
    REG_SOC,
    REG_SWITCH_STATE,
    SM_CURRENT_SCALE_FACTOR,
    SWITCH_STATE_LABELS,
    SWITCH_STATE_UNKNOWN_LABEL,
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
    modbus_llm.yaml, Abschnitt "SunSpec-Skalierung").
    """
    value = to_signed16(raw_value)
    scale_factor = to_signed16(raw_scale_factor)
    return round(value * (10**scale_factor), 3)


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
        # Basic Mode (Slave-ID self.slave_id) ist die Mindestanforderung für
        # jede Funktion der Integration und lässt das Update fehlschlagen
        # (UpdateFailed), wenn es nicht lesbar ist. Extended Mode wird davon
        # bewusst entkoppelt: ist Slave-ID self.slave_id_extended (z. B.
        # weil auf dem Gateway nicht freigeschaltet) nicht erreichbar,
        # bleiben die Basic-Mode-Sensoren trotzdem verfügbar und nur die
        # Extended-Mode-Sensoren zeigen "unbekannt" (siehe anforderung.yaml,
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
            "power": to_signed16(basic_reg(REG_POWER)),
            "smartmeter_power": to_signed16(basic_reg(REG_SMARTMETER_POWER)),
            "discharge_limit": basic_reg(REG_LIMIT_DISCHARGE),
            "charge_limit": basic_reg(REG_LIMIT_CHARGE),
        }

        data.update(await self._async_read_extended())

        await self._async_enforce_max_soc(data)
        return data

    async def _async_read_extended(self) -> dict[str, Any]:
        """Read+parse den Extended-Mode-Block, ohne bei Fehlern das gesamte
        Update scheitern zu lassen (siehe Kommentar in __init__)."""
        try:
            extended_result = await self.client.read_holding_registers(
                address=READ_BLOCK_EXT_START,
                count=READ_BLOCK_EXT_COUNT,
                device_id=self.slave_id_extended,
            )
            if extended_result.isError():
                raise ModbusException(
                    f"Modbus-Fehlerantwort (Extended Mode): {extended_result}"
                )
        except (TimeoutError, ModbusException) as err:
            if self._extended_available:
                _LOGGER.warning(
                    "Extended-Mode-Register (Slave-ID %s) nicht erreichbar - "
                    "Basic-Mode-Sensoren bleiben verfügbar, Extended-Mode-"
                    "Sensoren zeigen bis zur Wiederherstellung 'unbekannt': %s",
                    self.slave_id_extended,
                    err,
                )
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    f"extended_mode_unavailable_{self.entry_id}",
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="extended_mode_unavailable",
                    translation_placeholders={"slave_id": str(self.slave_id_extended)},
                )
            self._extended_available = False
            return {}

        if not self._extended_available:
            _LOGGER.info(
                "Extended-Mode-Register (Slave-ID %s) wieder erreichbar.",
                self.slave_id_extended,
            )
            ir.async_delete_issue(
                self.hass, DOMAIN, f"extended_mode_unavailable_{self.entry_id}"
            )
        self._extended_available = True

        ext_regs = extended_result.registers

        def ext_reg(address: int) -> int:
            return ext_regs[address - READ_BLOCK_EXT_START]

        return self._parse_extended(ext_reg)

    def _parse_extended(self, ext_reg: Callable[[int], int]) -> dict[str, Any]:
        """Parse the Extended-Mode-Register-Block (Speicher + Smart Meter).

        Wendet die SunSpec-Skalierung an und berechnet für jede
        Phasen-Trio-Gruppe (L1/L2/L3) zusätzlich eine Summe, siehe
        anforderung.yaml Anforderung REQ-ALL-REGISTERS-READABLE.
        """
        current_sf = ext_reg(REG_EXT_CURRENT_SF)
        current_l1 = apply_sunssf(ext_reg(REG_EXT_CURRENT_L1), current_sf)
        current_l2 = apply_sunssf(ext_reg(REG_EXT_CURRENT_L2), current_sf)
        current_l3 = apply_sunssf(ext_reg(REG_EXT_CURRENT_L3), current_sf)

        voltage_sf = ext_reg(REG_EXT_VOLTAGE_SF)
        voltage_l1 = apply_sunssf(ext_reg(REG_EXT_VOLTAGE_L1), voltage_sf)
        voltage_l2 = apply_sunssf(ext_reg(REG_EXT_VOLTAGE_L2), voltage_sf)
        voltage_l3 = apply_sunssf(ext_reg(REG_EXT_VOLTAGE_L3), voltage_sf)

        sm_current_scale = 10**SM_CURRENT_SCALE_FACTOR
        sm_current_l1 = round(
            to_signed16(ext_reg(REG_EXT_SM_CURRENT_L1)) * sm_current_scale, 3
        )
        sm_current_l2 = round(
            to_signed16(ext_reg(REG_EXT_SM_CURRENT_L2)) * sm_current_scale, 3
        )
        sm_current_l3 = round(
            to_signed16(ext_reg(REG_EXT_SM_CURRENT_L3)) * sm_current_scale, 3
        )

        sm_power_sf = ext_reg(REG_EXT_SM_POWER_SF)
        sm_power_l1 = apply_sunssf(ext_reg(REG_EXT_SM_POWER_L1), sm_power_sf)
        sm_power_l2 = apply_sunssf(ext_reg(REG_EXT_SM_POWER_L2), sm_power_sf)
        sm_power_l3 = apply_sunssf(ext_reg(REG_EXT_SM_POWER_L3), sm_power_sf)

        sm_voltage_l1 = to_signed16(ext_reg(REG_EXT_SM_VOLTAGE_L1))
        sm_voltage_l2 = to_signed16(ext_reg(REG_EXT_SM_VOLTAGE_L2))
        sm_voltage_l3 = to_signed16(ext_reg(REG_EXT_SM_VOLTAGE_L3))

        sm_switch_state = ext_reg(REG_EXT_SM_SWITCH_STATE)

        return {
            "ext_sunspec_id": ext_reg(REG_EXT_SUNSPEC_ID),
            "ext_sunspec_length": ext_reg(REG_EXT_SUNSPEC_LENGTH),
            "ext_current_sum_native": apply_sunssf(
                ext_reg(REG_EXT_CURRENT_SUM), current_sf
            ),
            "ext_current_l1": current_l1,
            "ext_current_l2": current_l2,
            "ext_current_l3": current_l3,
            "ext_current_sf": to_signed16(current_sf),
            "ext_current_sum": round(current_l1 + current_l2 + current_l3, 3),
            "ext_voltage_l1": voltage_l1,
            "ext_voltage_l2": voltage_l2,
            "ext_voltage_l3": voltage_l3,
            "ext_voltage_sf": to_signed16(voltage_sf),
            "ext_voltage_sum": round(voltage_l1 + voltage_l2 + voltage_l3, 3),
            "ext_power_active": apply_sunssf(
                ext_reg(REG_EXT_POWER_ACTIVE), ext_reg(REG_EXT_POWER_ACTIVE_SF)
            ),
            "ext_power_active_sf": to_signed16(ext_reg(REG_EXT_POWER_ACTIVE_SF)),
            "ext_frequency": apply_sunssf(
                ext_reg(REG_EXT_FREQUENCY), ext_reg(REG_EXT_FREQUENCY_SF)
            ),
            "ext_frequency_sf": to_signed16(ext_reg(REG_EXT_FREQUENCY_SF)),
            "ext_power_apparent": apply_sunssf(
                ext_reg(REG_EXT_POWER_APPARENT), ext_reg(REG_EXT_POWER_APPARENT_SF)
            ),
            "ext_power_apparent_sf": to_signed16(ext_reg(REG_EXT_POWER_APPARENT_SF)),
            "ext_power_reactive": apply_sunssf(
                ext_reg(REG_EXT_POWER_REACTIVE), ext_reg(REG_EXT_POWER_REACTIVE_SF)
            ),
            "ext_power_reactive_sf": to_signed16(ext_reg(REG_EXT_POWER_REACTIVE_SF)),
            "ext_power_factor": apply_sunssf(
                ext_reg(REG_EXT_POWER_FACTOR), ext_reg(REG_EXT_POWER_FACTOR_SF)
            ),
            "ext_power_factor_sf": to_signed16(ext_reg(REG_EXT_POWER_FACTOR_SF)),
            "sm_energy_fed_in": apply_sunssf(
                ext_reg(REG_EXT_SM_ENERGY_FED_IN), ext_reg(REG_EXT_SM_ENERGY_SF)
            ),
            "sm_energy_consumed": apply_sunssf(
                ext_reg(REG_EXT_SM_ENERGY_CONSUMED), ext_reg(REG_EXT_SM_ENERGY_SF)
            ),
            "sm_energy_sf": to_signed16(ext_reg(REG_EXT_SM_ENERGY_SF)),
            "sm_switch_state": sm_switch_state,
            "sm_switch_state_text": SWITCH_STATE_LABELS.get(
                sm_switch_state, SWITCH_STATE_UNKNOWN_LABEL
            ),
            "sm_current_l1": sm_current_l1,
            "sm_current_l2": sm_current_l2,
            "sm_current_l3": sm_current_l3,
            "sm_current_sum": round(sm_current_l1 + sm_current_l2 + sm_current_l3, 3),
            "sm_power_l1": sm_power_l1,
            "sm_power_l2": sm_power_l2,
            "sm_power_l3": sm_power_l3,
            "sm_power_sf": to_signed16(sm_power_sf),
            "sm_power_sum": round(sm_power_l1 + sm_power_l2 + sm_power_l3, 3),
            "sm_voltage_l1": sm_voltage_l1,
            "sm_voltage_l2": sm_voltage_l2,
            "sm_voltage_l3": sm_voltage_l3,
            "sm_voltage_sum": sm_voltage_l1 + sm_voltage_l2 + sm_voltage_l3,
            "sm_power_total": to_signed16(ext_reg(REG_EXT_SM_POWER_TOTAL)),
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
        """Set (or clear with None) the software-side max charge SOC."""
        self._max_soc = max_soc
        if self.data is not None:
            await self._async_enforce_max_soc(self.data)
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

    async def async_shutdown(self) -> None:
        await self.async_stop_grid_charge()
        ir.async_delete_issue(
            self.hass, DOMAIN, f"extended_mode_unavailable_{self.entry_id}"
        )
