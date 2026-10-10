"""SAX gateway rejection frames must not stall polling or fake write success."""

from __future__ import annotations

import asyncio
import struct
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pymodbus.client import AsyncModbusTcpClient

from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.modbus_framing import (
    SaxModbusPacketTrace,
)

from .test_integration_live import _build_basic_registers, _build_extended_registers

REQUEST = bytes.fromhex("0002 0000 0006 64 06 0033 0000")
BUSY = bytes.fromhex("0002 0000 0006 64 86 06")
VALID_BUSY = bytes.fromhex("0002 0000 0003 64 86 06")


def test_fragmented_exception_and_following_packet_keep_stream_boundaries() -> None:
    """REQ-EXTENDED-MODE-RESILIENCE: only the MBAP length changes."""
    trace = SaxModbusPacketTrace(100)
    assert trace(True, REQUEST) == REQUEST
    for boundary in range(1, len(BUSY)):
        assert trace(False, BUSY[:boundary]) == BUSY[:boundary]
    assert trace(False, BUSY) == VALID_BUSY
    assert trace(False, BUSY + REQUEST) == VALID_BUSY + REQUEST


@pytest.mark.parametrize(
    "packet",
    [
        REQUEST,
        VALID_BUSY,
        bytes.fromhex("0003 0000 0006 64 86 06"),
        bytes.fromhex("0002 0001 0006 64 86 06"),
        bytes.fromhex("0002 0000 0006 40 86 06"),
        bytes.fromhex("0002 0000 0006 64 83 06"),
        bytes.fromhex("0002 0000 0007 64 86 06"),
        bytes.fromhex("0002 0000 0006 64 86 ff"),
    ],
)
def test_success_and_unrelated_frames_are_untouched(packet: bytes) -> None:
    """REQ-EXTENDED-MODE-RESILIENCE: no blanket packet repair or ACK synthesis."""
    trace = SaxModbusPacketTrace(100)
    trace(True, REQUEST)
    assert trace(False, packet) == packet


@pytest.mark.parametrize(
    "outgoing",
    [
        bytes.fromhex("0002 0000 0006 64 03 0033 0001"),
        bytes.fromhex("0002 0000 0006 40 06 0033 0000"),
    ],
)
def test_new_read_or_other_device_disarms_exception_repair(outgoing: bytes) -> None:
    trace = SaxModbusPacketTrace(100)
    trace(True, REQUEST)
    trace(True, outgoing)
    assert trace(False, BUSY) == BUSY


@dataclass
class RejectingGateway:
    """Replay the real gateway's malformed busy response over a TCP stream."""

    writes: list[bytes] = field(default_factory=list)
    clients: list[asyncio.StreamWriter] = field(default_factory=list)

    async def handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        self.clients.append(writer)
        try:
            while True:
                header = await reader.readexactly(7)
                payload = await reader.readexactly(
                    int.from_bytes(header[4:6], "big") - 1
                )
                if payload[0] == 6:
                    self.writes.append(header + payload)
                    response = header + b"\x86\x06"
                else:
                    assert payload[0] == 3
                    address, count = struct.unpack(">HH", payload[1:])
                    registers = (
                        _build_basic_registers()
                        if header[6] == 64
                        else _build_extended_registers()
                    )
                    values = registers[address : address + count]
                    body = bytes([3, count * 2]) + struct.pack(
                        f">{count}H", *(value & 0xFFFF for value in values)
                    )
                    response = (
                        header[:4]
                        + struct.pack(">H", len(body) + 1)
                        + header[6:]
                        + body
                    )
                writer.write(response[:8])
                await writer.drain()
                await asyncio.sleep(0.001)
                writer.write(response[8:])
                await writer.drain()
        except asyncio.IncompleteReadError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()


@pytest.fixture
async def gateway(
    hass: HomeAssistant, socket_enabled: None, unused_tcp_port: int
) -> AsyncIterator[tuple[SaxPowerCoordinator, RejectingGateway]]:
    gateway = RejectingGateway()
    server = await asyncio.start_server(gateway.handle, "127.0.0.1", unused_tcp_port)
    client = AsyncModbusTcpClient(
        "127.0.0.1",
        port=unused_tcp_port,
        timeout=1,
        trace_packet=SaxModbusPacketTrace(100),
    )
    await client.connect()
    coordinator = SaxPowerCoordinator(hass, client, 64, 100, 10, "rejecting-gateway")
    await coordinator.async_load_energy_state()
    try:
        yield coordinator, gateway
    finally:
        await coordinator.async_shutdown(reset_device=False)
        client.close()
        server.close()
        await server.wait_closed()
        for writer in gateway.clients:
            writer.close()
            await writer.wait_closed()
        await asyncio.sleep(0)


async def test_device_busy_is_returned_promptly_without_retries_or_success(
    gateway: tuple[SaxPowerCoordinator, RejectingGateway],
) -> None:
    """REQ-EXTENDED-MODE-RESILIENCE: malformed busy is a failure, not a timeout."""
    coordinator, server = gateway
    async with asyncio.timeout(0.5):
        with pytest.raises(HomeAssistantError, match="Gerät beschäftigt.*Ausnahme 6"):
            await coordinator.async_write_extended_register(51, 0)
        readback = await coordinator.client.read_holding_registers(
            address=51, count=1, device_id=100
        )
    assert len(server.writes) == 1
    assert readback.registers == [0]
    assert coordinator._sun_charge_commanded_mode is None


@pytest.mark.parametrize("pending_reset", [False, True])
async def test_real_poll_keeps_forecast_with_readback_or_rejected_owned_reset(
    gateway: tuple[SaxPowerCoordinator, RejectingGateway], pending_reset: bool
) -> None:
    """REQ-DISCHARGE-FORECAST: rejected writes cannot starve a measured minute."""
    coordinator, server = gateway
    if pending_reset:
        coordinator._sun_charge_reset_required = True
        coordinator._sun_charge_commanded_mode = 1
    async with asyncio.timeout(2):
        for tick in range(31):
            with patch(
                "custom_components.sax_power.coordinator.monotonic",
                return_value=100 + tick * 2,
            ):
                data = await coordinator._async_update_data()
    assert data["discharge_forecast"] is not None
    assert data["discharge_forecast_attributes"]["observation_minutes"] == 1
    assert data["discharge_forecast_attributes"]["average_discharge_w"] == 1200
    assert len(server.writes) == (31 if pending_reset else 0)
    assert coordinator._sun_charge_reset_required is pending_reset
    assert coordinator._sun_charge_commanded_mode == (1 if pending_reset else 0)
    assert not coordinator.sun_charge_active


@pytest.mark.parametrize(
    "condition", ["missing", "stale", "unavailable", "mode_one", "explicit"]
)
async def test_initial_readback_never_bypasses_a_required_reset(
    gateway: tuple[SaxPowerCoordinator, RejectingGateway], condition: str
) -> None:
    """REQ-GRID-SERVING-CHARGE: only fresh mode zero can avoid an initial write."""
    coordinator, server = gateway
    coordinator._last_observed_ic_control_mode = 0
    coordinator._high_sample_control_mode = 0
    coordinator._high_sample_time = 100
    if condition == "missing":
        coordinator._high_sample_time = None
    elif condition == "stale":
        coordinator._high_sample_time = 94
    elif condition == "unavailable":
        coordinator._extended_available = False
    elif condition == "mode_one":
        coordinator._high_sample_control_mode = 1
        coordinator._last_observed_ic_control_mode = 1
    with patch("custom_components.sax_power.coordinator.monotonic", return_value=100):
        if condition == "explicit":
            with pytest.raises(
                HomeAssistantError, match="Rücksetzauftrag bleibt aktiv"
            ):
                await coordinator.async_stop_sun_charge(require_confirmation=True)
        else:
            await coordinator.async_stop_sun_charge()
    assert len(server.writes) == 1
    assert coordinator._sun_charge_reset_required
    assert coordinator._sun_charge_commanded_mode is None
