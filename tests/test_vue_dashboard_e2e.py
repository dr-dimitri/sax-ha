"""Gemeinsame HA-Sitzungen mit echtem Modbus-Simulator (REQ-VUE-PARITY)."""

from __future__ import annotations

import asyncio
from datetime import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components import frontend
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pymodbus.client import AsyncModbusTcpClient
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser
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


async def test_configuration_services_confirm_without_waiting_for_device_control(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    unused_tcp_port: int,
) -> None:
    """REQ-VUE-ENTITY-BINDING: GUI-Konfiguration quittiert vor dem Geräteabgleich."""
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

        def entity_id(domain: str, key: str) -> str:
            resolved = registry.async_get_entity_id(
                domain, DOMAIN, f"{entry.entry_id}_{key}"
            )
            assert resolved
            return resolved

        actions = [
            ("switch", "timed_charge_enabled", "turn_on", {}, "on"),
            ("switch", "timed_charge_enabled", "turn_off", {}, "off"),
            ("switch", "price_charge_enabled", "turn_on", {}, "on"),
            ("switch", "price_charge_enabled", "turn_off", {}, "off"),
            ("switch", "grid_serving_enabled", "turn_on", {}, "on"),
            ("switch", "grid_serving_enabled", "turn_off", {}, "off"),
            ("number", "timed_charge_min_soc", "set_value", {"value": 30}, "30"),
            ("number", "timed_charge_max_soc", "set_value", {"value": 90}, "90"),
            ("number", "max_soc", "set_value", {"value": 85}, "85"),
            ("number", "price_charge_max_price", "set_value", {"value": -0.1}, "-0.1"),
            (
                "number",
                "price_charge_neutral_price",
                "set_value",
                {"value": 0.2},
                "0.2",
            ),
            ("number", "price_charge_hours", "set_value", {"value": 4}, "4"),
            (
                "number",
                "grid_serving_forecast_threshold",
                "set_value",
                {"value": 20},
                "20.0",
            ),
            (
                "select",
                "price_charge_strategy",
                "select_option",
                {"option": "relative"},
                "relative",
            ),
            (
                "time",
                "timed_charge_start",
                "set_value",
                {"time": "01:00:00"},
                "01:00:00",
            ),
            ("time", "timed_charge_end", "set_value", {"time": "05:00:00"}, "05:00:00"),
            (
                "time",
                "grid_serving_start",
                "set_value",
                {"time": "06:00:00"},
                "06:00:00",
            ),
            ("time", "grid_serving_end", "set_value", {"time": "10:00:00"}, "10:00:00"),
        ]
        with patch.object(
            coordinator.client,
            "write_register",
            wraps=coordinator.client.write_register,
        ) as write:
            async with coordinator._charge_control_lock:
                worker = None
                for request_id, (domain, key, service, data, expected) in enumerate(
                    actions, 1
                ):
                    target = entity_id(domain, key)
                    await sender.send_json(
                        {
                            "id": request_id,
                            "type": "call_service",
                            "domain": domain,
                            "service": service,
                            "service_data": data,
                            "target": {"entity_id": target},
                        }
                    )
                    await _result(sender, request_id)
                    await _state_event(observer, target, expected)
                    assert hass.states.get(target).state == expected
                    write.assert_not_called()
                    worker = worker or coordinator._month_control_task
                    assert coordinator._month_control_task is worker

                device_id = registry.async_get(
                    entity_id("switch", "timed_charge_enabled")
                ).device_id
                for request_id, (prefix, start, end) in enumerate(
                    [
                        ("timed_charge", "02:00:00", "04:00:00"),
                        ("grid_serving", "07:00:00", "11:00:00"),
                    ],
                    30,
                ):
                    await sender.send_json(
                        {
                            "id": request_id,
                            "type": "call_service",
                            "domain": DOMAIN,
                            "service": f"set_{prefix}_window",
                            "service_data": {
                                "device_id": device_id,
                                "start": start,
                                "end": end,
                            },
                        }
                    )
                    await _result(sender, request_id)
                    await _state_event(
                        observer, entity_id("time", f"{prefix}_start"), start
                    )
                    assert (
                        hass.states.get(entity_id("time", f"{prefix}_end")).state == end
                    )
                    write.assert_not_called()

                await sender.send_json(
                    {
                        "id": 40,
                        "type": "call_service",
                        "domain": "switch",
                        "service": "turn_on",
                        "target": {
                            "entity_id": entity_id("switch", "timed_charge_enabled")
                        },
                    }
                )
                await _result(sender, 40)
                await sender.send_json(
                    {
                        "id": 41,
                        "type": "call_service",
                        "domain": DOMAIN,
                        "service": "set_price_charge_enabled",
                        "service_data": {
                            "device_id": device_id,
                            "enabled": True,
                            "force": True,
                        },
                    }
                )
                await _result(sender, 41)
                assert (
                    hass.states.get(entity_id("switch", "timed_charge_enabled")).state
                    == "off"
                )
                assert (
                    hass.states.get(entity_id("switch", "price_charge_enabled")).state
                    == "on"
                )
                write.assert_not_called()
                assert coordinator._month_control_task is worker
                with patch.object(
                    coordinator.price_planner,
                    "evaluate",
                    wraps=coordinator.price_planner.evaluate,
                ) as evaluate:
                    await sender.send_json(
                        {
                            "id": 42,
                            "type": "call_service",
                            "domain": DOMAIN,
                            "service": "refresh_price_plan",
                            "service_data": {"device_id": device_id},
                        }
                    )
                    await _result(sender, 42)
                    evaluate.assert_called_once()
                write.assert_not_called()
                assert coordinator._month_control_task is worker
            await worker
        await sender.close()
        await observer.close()
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


@pytest.mark.parametrize(
    "prefix, start, end",
    [
        ("timed_charge", "22:03:17", "06:37:23"),
        ("grid_serving", "10:05:19", "15:47:29"),
    ],
)
async def test_dashboard_window_service_confirms_both_renamed_entities_atomically(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    hass_read_only_user: MockUser,
    unused_tcp_port: int,
    prefix: str,
    start: str,
    end: str,
) -> None:
    """REQ-VUE-CHARGING: Registry-Gerät, WS-Rechte und exaktes Zeitpaar greifen."""
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
            CONF_VUE_DASHBOARD_ENABLED: True,
            CONF_VUE_DASHBOARD_VERSION: "",
        },
    )
    entry.add_to_hass(hass)
    try:
        assert await async_setup_component(hass, "frontend", {})
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
        registry = er.async_get(hass)
        expected = {}
        for part, value in (("start", start), ("end", end)):
            entity_id = registry.async_get_entity_id(
                "time", DOMAIN, f"{entry.entry_id}_{prefix}_{part}"
            )
            assert entity_id
            renamed = f"time.my_battery_{part}"
            registry.async_update_entity(entity_id, new_entity_id=renamed)
            expected[renamed] = value
        await hass.async_block_till_done()
        hass_read_only_user.mock_policy(
            {
                "entities": {
                    "entity_ids": {
                        entity_id: {"read": True, "control": True}
                        for entity_id in expected
                    }
                }
            }
        )
        sender = await hass_ws_client(hass, access_token=hass_read_only_access_token)
        observer = await hass_ws_client(hass)
        await sender.send_json(
            {
                "id": 1,
                "type": "sax_power/dashboard/subscribe",
                "entry_id": entry.entry_id,
                "language": "de",
            }
        )
        await _result(sender, 1)
        metadata = (await sender.receive_json())["event"]["entities"]
        assert {item["entity_id"] for item in metadata} == set(expected)
        device_ids = {item["device_id"] for item in metadata}
        assert len(device_ids) == 1 and None not in device_ids
        device_id = device_ids.pop()
        assert all(item["can_control"] for item in metadata)
        await observer.send_json(
            {"id": 1, "type": "subscribe_events", "event_type": "state_changed"}
        )
        await _result(observer, 1)

        with (
            patch.object(
                coordinator,
                f"async_set_{prefix}_window",
                wraps=getattr(coordinator, f"async_set_{prefix}_window"),
            ) as set_window,
            patch.object(coordinator, f"async_set_{prefix}_start") as set_start,
            patch.object(coordinator, f"async_set_{prefix}_end") as set_end,
        ):
            await sender.send_json(
                {
                    "id": 2,
                    "type": "call_service",
                    "domain": DOMAIN,
                    "service": f"set_{prefix}_window",
                    "service_data": {
                        "device_id": device_id,
                        "start": start,
                        "end": end,
                    },
                }
            )
            await _result(sender, 2)
            waiting = dict(expected)
            async with asyncio.timeout(5):
                while waiting:
                    message = await observer.receive_json()
                    if message["type"] != "event":
                        continue
                    event = message["event"]
                    if event.get("event_type") != "state_changed":
                        continue
                    data = event["data"]
                    if data["entity_id"] in waiting:
                        assert data["new_state"]["state"] == waiting.pop(
                            data["entity_id"]
                        )
            assert {
                entity_id: hass.states.get(entity_id).state for entity_id in expected
            } == expected
            set_window.assert_awaited_once_with(
                time.fromisoformat(start),
                time.fromisoformat(end),
                defer_device_update=True,
            )
            set_start.assert_not_awaited()
            set_end.assert_not_awaited()

            hass_read_only_user.mock_policy(
                {
                    "entities": {
                        "entity_ids": {
                            "time.my_battery_start": {"read": True, "control": True}
                        }
                    }
                }
            )
            await sender.send_json(
                {
                    "id": 3,
                    "type": "call_service",
                    "domain": DOMAIN,
                    "service": f"set_{prefix}_window",
                    "service_data": {
                        "device_id": device_id,
                        "start": "01:00",
                        "end": "02:00",
                    },
                }
            )
            denied = await sender.receive_json()
            assert denied["id"] == 3
            assert denied["success"] is False
            assert denied["error"]["code"] == "home_assistant_error"
            assert denied["error"]["message"] == "Unauthorized"
            set_window.assert_awaited_once()
        await sender.close()
        await observer.close()
    finally:
        await hass.config_entries.async_unload(entry.entry_id)
        await server.shutdown()
