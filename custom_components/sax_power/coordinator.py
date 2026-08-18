"""DataUpdateCoordinator for the SAX Power integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    GRID_CHARGE_WRITE_INTERVAL,
    MAX_SETPOINT_POWER,
    MIN_SETPOINT_POWER,
    READ_BLOCK_COUNT,
    READ_BLOCK_START,
    REG_LIMIT_CHARGE,
    REG_LIMIT_DISCHARGE,
    REG_POWER,
    REG_SETPOINT_POWER,
    REG_SMARTMETER_POWER,
    REG_SOC,
    REG_SWITCH_STATE,
)

_LOGGER = logging.getLogger(__name__)


def to_signed16(value: int) -> int:
    """Convert an unsigned 16-bit register value to its signed representation."""
    return value - 0x10000 if value >= 0x8000 else value


def to_unsigned16(value: int) -> int:
    """Convert a signed value to its unsigned 16-bit register representation."""
    return value & 0xFFFF


class SaxPowerCoordinator(DataUpdateCoordinator[dict[str, int]]):
    """Coordinates Modbus reads/writes for a SAX Power storage system."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AsyncModbusTcpClient,
        slave_id: int,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="SAX Power",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.slave_id = slave_id
        self._write_lock = asyncio.Lock()
        self._max_soc: int | None = None
        self._max_soc_clamped = False
        self._pre_clamp_charge_limit = 0
        self._grid_charge_task: asyncio.Task | None = None
        self._grid_charge_power = 0

    async def _async_update_data(self) -> dict[str, int]:
        try:
            if not self.client.connected:
                await self.client.connect()
            result = await self.client.read_holding_registers(
                address=READ_BLOCK_START,
                count=READ_BLOCK_COUNT,
                device_id=self.slave_id,
            )
        except (TimeoutError, ModbusException) as err:
            raise UpdateFailed(
                f"Fehler bei der Kommunikation mit dem SAX Speicher: {err}"
            ) from err

        if result.isError():
            raise UpdateFailed(f"Modbus-Fehlerantwort vom SAX Speicher: {result}")

        regs = result.registers

        def reg(address: int) -> int:
            return regs[address - READ_BLOCK_START]

        data = {
            "switch_state": reg(REG_SWITCH_STATE),
            "soc": reg(REG_SOC),
            "power": to_signed16(reg(REG_POWER)),
            "smartmeter_power": to_signed16(reg(REG_SMARTMETER_POWER)),
            "discharge_limit": reg(REG_LIMIT_DISCHARGE),
            "charge_limit": reg(REG_LIMIT_CHARGE),
        }

        await self._async_enforce_max_soc(data)
        return data

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

    async def _async_enforce_max_soc(self, data: dict[str, int]) -> None:
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
