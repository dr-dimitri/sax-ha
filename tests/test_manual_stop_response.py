"""REQ-MANUAL-GRID-CHARGE: Manuelle Stopps benötigen eine Gerätequittierung."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from pymodbus.exceptions import ModbusException
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power import _async_register_services
from custom_components.sax_power.const import (
    ATTR_DEVICE_ID,
    DATA_COORDINATOR,
    DOMAIN,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SERVICE_STOP_GRID_CHARGE,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator


@pytest.fixture
async def manual_device(
    hass: HomeAssistant,
) -> AsyncIterator[tuple[SaxPowerCoordinator, str]]:
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    client = MagicMock()
    client.connected = True
    success = MagicMock()
    success.isError.return_value = False
    client.write_register = AsyncMock(return_value=success)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=entry.entry_id,
    )
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
    }
    coordinator._max_soc = 100
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "manual_stop")},
    )
    _async_register_services(hass)
    yield coordinator, device.id
    await coordinator.async_shutdown(reset_device=False)


async def _stop(
    hass: HomeAssistant, device_id: str, websocket: Any | None
) -> dict[str, Any]:
    if websocket is None:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_GRID_CHARGE,
            {ATTR_DEVICE_ID: device_id},
            blocking=True,
        )
        return {"success": True}
    await websocket.send_json_auto_id(
        {
            "type": "call_service",
            "domain": DOMAIN,
            "service": SERVICE_STOP_GRID_CHARGE,
            "service_data": {ATTR_DEVICE_ID: device_id},
        }
    )
    return await websocket.receive_json()


@pytest.mark.parametrize("boundary", ["service", "websocket"])
@pytest.mark.parametrize("failure_kind", ["modbus", "timeout", "response"])
async def test_manual_stop_reports_failed_reset_and_retries_without_an_order(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
    failure_kind: str,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Fehlende Quittung bleibt an der echten Grenze Fehler."""
    coordinator, device_id = manual_device
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None
    await coordinator.async_start_grid_charge(-1500)
    writer = coordinator._sun_charge_task
    coordinator.client.write_register.reset_mock()
    reset_started, finish_reset = asyncio.Event(), asyncio.Event()

    async def fail_reset(**_kwargs: Any) -> MagicMock:
        reset_started.set()
        await finish_reset.wait()
        if failure_kind == "modbus":
            raise ModbusException("Reset abgelehnt")
        if failure_kind == "timeout":
            raise TimeoutError("Reset ohne Antwort")
        failure = MagicMock()
        failure.isError.return_value = True
        failure.__str__.return_value = "Reset abgelehnt"
        return failure

    coordinator.client.write_register.side_effect = fail_reset
    async with coordinator._charge_control_lock:
        stop = asyncio.create_task(_stop(hass, device_id, websocket))
        await asyncio.sleep(0)
        assert not stop.done()
        assert coordinator.grid_charge_active
        coordinator.client.write_register.assert_not_awaited()
    try:
        await asyncio.wait_for(reset_started.wait(), 1)
        assert not stop.done()
        assert writer is not None and writer.done()
        assert coordinator._sun_charge_task is None
        assert not coordinator.grid_charge_active
        assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SETPOINT
    finally:
        finish_reset.set()
    if websocket is None:
        with pytest.raises(HomeAssistantError, match="Rücksetzauftrag bleibt aktiv"):
            await stop
    else:
        result = await stop
        assert result["success"] is False
        assert "Rücksetzauftrag bleibt aktiv" in result["error"]["message"]
    assert coordinator._sun_charge_reset_required
    assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SETPOINT
    coordinator.client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )

    coordinator.client.write_register.side_effect = None
    result = await _stop(hass, device_id, websocket)

    assert result["success"] is True
    assert not coordinator._sun_charge_reset_required
    assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SMARTMETER
    assert coordinator.client.write_register.await_count == 2
    assert not coordinator.grid_charge_active
    assert not coordinator.sun_charge_active


@pytest.mark.parametrize("boundary", ["service", "websocket"])
async def test_manual_stop_awaits_reset_and_automatic_successor_acknowledgement(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Die Max-SOC-Sperre übernimmt erst nach Modus 0."""
    coordinator, device_id = manual_device
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None
    await coordinator.async_start_grid_charge(-1500)
    coordinator._max_soc = 40
    coordinator.client.write_register.reset_mock()
    success = coordinator.client.write_register.return_value
    reset_started, finish_reset = asyncio.Event(), asyncio.Event()
    successor_started, finish_successor = asyncio.Event(), asyncio.Event()

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if (
            address == REG_SUN_IC_CONTROL_MODE
            and value == SUN_IC_CONTROL_MODE_SMARTMETER
        ):
            reset_started.set()
            await finish_reset.wait()
        elif address == REG_SUN_IC_POWER_SETPOINT_PCT:
            successor_started.set()
            await finish_successor.wait()
        return success

    coordinator.client.write_register.side_effect = write
    stop = asyncio.create_task(_stop(hass, device_id, websocket))
    try:
        await asyncio.wait_for(reset_started.wait(), 1)
        assert not stop.done()
        assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SETPOINT
        finish_reset.set()
        await asyncio.wait_for(successor_started.wait(), 1)
        assert not stop.done()
        assert not coordinator.sun_charge_active
    finally:
        finish_reset.set()
        finish_successor.set()
    assert (await stop)["success"] is True
    assert coordinator.max_soc_clamped
    assert coordinator.sun_charge_active
    assert coordinator._sun_charge_power == 0
    assert not coordinator.grid_charge_active
    assert [
        (call.kwargs["address"], call.kwargs["value"])
        for call in coordinator.client.write_register.await_args_list
    ] == [
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER),
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT),
        (REG_SUN_IC_POWER_SETPOINT_PCT, 0),
    ]

    writer = coordinator._sun_charge_task
    coordinator.client.write_register.reset_mock()
    assert (await _stop(hass, device_id, websocket))["success"] is True
    assert coordinator._sun_charge_task is writer
    assert coordinator.sun_charge_active
    coordinator.client.write_register.assert_not_awaited()


async def test_manual_stop_retries_failed_partial_start_through_service(
    hass: HomeAssistant, manual_device: tuple[SaxPowerCoordinator, str]
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Der Reset überlebt einen bereits verworfenen Start."""
    coordinator, device_id = manual_device
    success = coordinator.client.write_register.return_value
    coordinator.client.write_register.side_effect = [
        success,
        ModbusException("Sollwert fehlgeschlagen"),
        ModbusException("Rollback fehlgeschlagen"),
        ModbusException("Stopp fehlgeschlagen"),
        success,
    ]
    with pytest.raises(HomeAssistantError, match="Rücksetzauftrag bleibt aktiv"):
        await coordinator.async_start_grid_charge(-1500)
    assert not coordinator.grid_charge_active
    assert not coordinator.sun_charge_active

    with pytest.raises(HomeAssistantError, match="Rücksetzauftrag bleibt aktiv"):
        await _stop(hass, device_id, None)
    assert coordinator._sun_charge_reset_required

    assert (await _stop(hass, device_id, None))["success"] is True
    assert not coordinator._sun_charge_reset_required
    assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SMARTMETER
    assert coordinator.client.write_register.await_count == 5


async def test_shutdown_finishes_cleanup_despite_failed_reset(
    manual_device: tuple[SaxPowerCoordinator, str],
) -> None:
    """REQ-SETUP-ROLLBACK: Ein fehlender Reset-ACK verhindert keinen Unload."""
    coordinator, _ = manual_device
    await coordinator.async_start_grid_charge(-1500)
    writer = coordinator._sun_charge_task
    coordinator.client.write_register.side_effect = ModbusException(
        "Reset fehlgeschlagen"
    )

    await coordinator.async_shutdown()

    assert coordinator._shutdown_complete
    assert coordinator._sun_charge_reset_required
    assert not coordinator.grid_charge_active
    assert not coordinator.sun_charge_active
    assert writer is not None and writer.done()


async def test_manual_stop_preserves_reset_after_cancelled_writer_rolls_back(
    manual_device: tuple[SaxPowerCoordinator, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Writer-Rollback quittiert nicht den Stopp-Reset."""
    coordinator, _ = manual_device
    monkeypatch.setattr(coordinator, "_sun_ic_write_interval", lambda: 0)
    await coordinator.async_start_grid_charge(-1500)
    success = coordinator.client.write_register.return_value
    setpoint_started = asyncio.Event()
    resets = 0

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        nonlocal resets
        if address == REG_SUN_IC_POWER_SETPOINT_PCT:
            setpoint_started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError as err:
                # pymodbus can translate cancellation into a ModbusIOException.
                raise ModbusException("Sollwert beim Abbruch fehlgeschlagen") from err
        if (
            address == REG_SUN_IC_CONTROL_MODE
            and value == SUN_IC_CONTROL_MODE_SMARTMETER
        ):
            resets += 1
            if resets == 2:
                raise ModbusException("Expliziter Stopp fehlgeschlagen")
        return success

    coordinator.client.write_register.side_effect = write
    await asyncio.wait_for(setpoint_started.wait(), 1)

    with pytest.raises(HomeAssistantError, match="Rücksetzauftrag bleibt aktiv"):
        await coordinator.async_stop_grid_charge()

    assert resets == 2
    assert not coordinator.grid_charge_active
    assert not coordinator.sun_charge_active
    assert coordinator._sun_charge_reset_required
    assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SMARTMETER

    await coordinator.async_stop_grid_charge()

    assert resets == 3
    assert not coordinator._sun_charge_reset_required
