"""Application-facing ports for external infrastructure."""

from __future__ import annotations

from typing import Any, Protocol


class ModbusClient(Protocol):
    """Minimal asynchronous Modbus client contract used by the coordinator."""

    connected: bool

    async def connect(self) -> bool:
        """Connect to the device."""

    async def read_holding_registers(
        self,
        address: int,
        *,
        count: int,
        device_id: int,
    ) -> Any:
        """Read holding registers from one Modbus device id."""

    async def write_register(
        self,
        address: int,
        value: int,
        *,
        device_id: int,
    ) -> Any:
        """Write one holding register on one Modbus device id."""

    def close(self) -> None:
        """Close the underlying transport."""
