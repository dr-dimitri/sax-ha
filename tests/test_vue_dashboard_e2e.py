"""Gemeinsame HA-Sitzungen mit echtem Modbus-Simulator (REQ-VUE-PARITY)."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components import frontend
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pymodbus.client import AsyncModbusTcpClient
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import (
    MockHAClientWebSocket,
    WebSocketGenerator,
)

from custom_components.sax_power.const import (
    CONF_VUE_DASHBOARD_ENABLED,
    CONF_VUE_DASHBOARD_VERSION,
    DATA_COORDINATOR,
    DOMAIN,
)
from custom_components.sax_power.vue_dashboard import VUE_DASHBOARD_URL_PATH

from .test_integration_live import (
    _build_basic_registers,
    _build_extended_registers,
    _modbus_server,
)


async def _result(client: MockHAClientWebSocket, request_id: int) -> dict[str, Any]:
    async with asyncio.timeout(5):
        while True:
            message = await client.receive_json()
            if message.get("id") == request_id and message["type"] == "result":
                assert message["success"], message
                return message["result"]


async def _state_event(
    client: MockHAClientWebSocket, entity_id: str, state: str
) -> None:
    async with asyncio.timeout(5):
        while True:
            message = await client.receive_json()
            if message["type"] != "event":
                continue
            event = message["event"]
            if event.get("event_type") != "state_changed":
                continue
            data = event["data"]
            if data["entity_id"] == entity_id and data["new_state"]["state"] == state:
                return


async def test_dashboard_clients_share_services_states_and_one_modbus_client(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    unused_tcp_port: int,
) -> None:
    """Beide HA-Clients sehen dieselben Änderungen; Öffnen erzeugt keine Geräte-I/O."""
    server = _modbus_server(
        unused_tcp_port, _build_basic_registers(), _build_extended_registers()
    )
    await server.serve_forever(background=True)
    clients: list[AsyncModbusTcpClient] = []

    def create_client(*args: Any, **kwargs: Any) -> AsyncModbusTcpClient:
        client = AsyncModbusTcpClient(*args, **kwargs)
        client.read_holding_registers = MagicMock(wraps=client.read_holding_registers)
        client.write_register = MagicMock(wraps=client.write_register)
        clients.append(client)
        return client

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "127.0.0.1",
            "port": unused_tcp_port,
            "slave_id_basic": 64,
            "slave_id_extended": 100,
            "scan_interval": 3600,
            CONF_VUE_DASHBOARD_ENABLED: True,
            CONF_VUE_DASHBOARD_VERSION: "",
        },
    )
    entry.add_to_hass(hass)
    try:
        assert await async_setup_component(hass, "frontend", {})
        with patch("custom_components.sax_power.AsyncModbusTcpClient", create_client):
            assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert len(clients) == 1
        modbus = clients[0]
        registry = er.async_get(hass)
        switch_id = registry.async_get_entity_id(
            "switch", DOMAIN, f"{entry.entry_id}_storage_switch"
        )
        limit_id = registry.async_get_entity_id(
            "number", DOMAIN, f"{entry.entry_id}_max_soc"
        )
        assert switch_id and limit_id
        panel = hass.data[frontend.DATA_PANELS][VUE_DASHBOARD_URL_PATH]
        reads = modbus.read_holding_registers.call_count
        writes = modbus.write_register.call_count

        first = await hass_ws_client(hass)
        second = await hass_ws_client(hass)
        for client in (first, second):
            await client.send_json(
                {
                    "id": 1,
                    "type": "sax_power/dashboard/subscribe",
                    "entry_id": entry.entry_id,
                    "language": "de",
                }
            )
            await _result(client, 1)
            entities = (await client.receive_json())["event"]["entities"]
            assert (
                next(item for item in entities if item["key"] == "max_soc")["entity_id"]
                == limit_id
            )
        for client in (first, second):
            await client.send_json(
                {"id": 2, "type": "subscribe_events", "event_type": "state_changed"}
            )
            await _result(client, 2)
        await hass.async_block_till_done()
        assert modbus.read_holding_registers.call_count == reads
        assert modbus.write_register.call_count == writes

        for sender, observer, action, state in (
            (first, second, "turn_off", "off"),
            (second, first, "turn_on", "on"),
        ):
            before = modbus.write_register.call_count
            await sender.send_json(
                {
                    "id": 3 if action == "turn_off" else 4,
                    "type": "call_service",
                    "domain": "switch",
                    "service": action,
                    "target": {"entity_id": switch_id},
                }
            )
            await _state_event(observer, switch_id, state)
            await hass.async_block_till_done()
            assert hass.states.get(switch_id).state == state
            assert modbus.write_register.call_count == before + 1

        await first.send_json(
            {
                "id": 5,
                "type": "call_service",
                "domain": "number",
                "service": "set_value",
                "service_data": {"value": 90},
                "target": {"entity_id": limit_id},
            }
        )
        await _state_event(second, limit_id, "90")
        assert hass.states.get(limit_id).state == "90"

        assert "sax-power" not in hass.data[frontend.DATA_PANELS]
        for service in ("create_dashboard", "reinstall_dashboard"):
            assert not hass.services.has_service(DOMAIN, service)
        assert hass.data[frontend.DATA_PANELS][VUE_DASHBOARD_URL_PATH] is panel
        await first.close()
        await second.close()
        assert len(clients) == 1
    finally:
        await hass.config_entries.async_unload(entry.entry_id)
        await server.shutdown()


@pytest.mark.parametrize("prefix", ["timed_charge", "grid_serving"])
async def test_month_services_confirm_while_device_control_is_busy(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    unused_tcp_port: int,
    prefix: str,
) -> None:
    """REQ-VUE-CHARGING: alle Monate quittieren ohne Warten auf Geräte-I/O."""
    server = _modbus_server(
        unused_tcp_port, _build_basic_registers(), _build_extended_registers()
    )
    await server.serve_forever(background=True)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "127.0.0.1",
            "port": unused_tcp_port,
            "slave_id_basic": 64,
            "slave_id_extended": 100,
            "scan_interval": 3600,
        },
    )
    entry.add_to_hass(hass)
    try:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
        registry = er.async_get(hass)
        sender = await hass_ws_client(hass)
        observer = await hass_ws_client(hass)
        await observer.send_json(
            {"id": 1, "type": "subscribe_events", "event_type": "state_changed"}
        )
        await _result(observer, 1)
        applied = asyncio.Event()
        enforce = coordinator._async_enforce_grid_charge_locked

        async def record_apply(data: dict[str, Any]) -> None:
            await enforce(data)
            applied.set()

        with (
            patch.object(
                coordinator.client,
                "write_register",
                wraps=coordinator.client.write_register,
            ) as write,
            patch.object(
                coordinator, "_async_enforce_grid_charge_locked", record_apply
            ),
        ):
            # A slow device operation must not postpone configuration acceptance.
            async with coordinator._charge_control_lock:
                for month in range(1, 13):
                    entity_id = registry.async_get_entity_id(
                        "switch", DOMAIN, f"{entry.entry_id}_{prefix}_month_{month}"
                    )
                    assert entity_id
                    assert hass.states.get(entity_id).state == "on"
                    await sender.send_json(
                        {
                            "id": month,
                            "type": "call_service",
                            "domain": "switch",
                            "service": "turn_off",
                            "target": {"entity_id": entity_id},
                        }
                    )
                    await _result(sender, month)
                    await _state_event(observer, entity_id, "off")
                    assert hass.states.get(entity_id).state == "off"
                    write.assert_not_called()
                    assert not applied.is_set()
            async with asyncio.timeout(5):
                await applied.wait()
        await sender.close()
        await observer.close()
    finally:
        await hass.config_entries.async_unload(entry.entry_id)
        await server.shutdown()
