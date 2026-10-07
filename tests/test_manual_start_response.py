"""REQ-MANUAL-GRID-CHARGE: Antworten unterscheiden Ladung und vorgemerkte Aufträge."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util
from pymodbus.exceptions import ModbusException
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power.const import (
    ATTR_DEVICE_ID,
    ATTR_POWER,
    DOMAIN,
    PRICE_STRATEGY_ABSOLUTE,
    PV_SURPLUS_HYSTERESIS_CYCLES,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SERVICE_START_GRID_CHARGE,
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.price_optimizer import PricePlan, PriceSlot

from .test_manual_stop_response import manual_device as manual_device


async def _start(
    hass: HomeAssistant,
    device_id: str,
    websocket: Any | None,
    *,
    return_response: bool = True,
    power: int = -1000,
) -> dict[str, Any]:
    data = {ATTR_DEVICE_ID: device_id, ATTR_POWER: power}
    if websocket is None:
        response = await hass.services.async_call(
            DOMAIN,
            SERVICE_START_GRID_CHARGE,
            data,
            blocking=True,
            return_response=return_response,
        )
        return {"success": True, "result": response}
    await websocket.send_json_auto_id(
        {
            "type": "call_service",
            "domain": DOMAIN,
            "service": SERVICE_START_GRID_CHARGE,
            "service_data": data,
            "return_response": return_response,
        }
    )
    return await websocket.receive_json()


def _response(reply: dict[str, Any], boundary: str) -> dict[str, Any]:
    assert reply["success"] is True
    return reply["result"]["response"] if boundary == "websocket" else reply["result"]


@pytest.mark.parametrize("boundary", ["service", "websocket"])
async def test_start_response_awaits_control_lock_and_both_device_acknowledgements(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Ein charging-Ergebnis benötigt beide Quittungen."""
    coordinator, device_id = manual_device
    coordinator.data["soc"] = 72
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None
    mode_started, finish_mode = asyncio.Event(), asyncio.Event()
    power_started, finish_power = asyncio.Event(), asyncio.Event()
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == REG_SUN_IC_CONTROL_MODE:
            mode_started.set()
            await finish_mode.wait()
        else:
            power_started.set()
            await finish_power.wait()
        return success

    coordinator.client.write_register.side_effect = write
    async with coordinator._charge_control_lock:
        start = asyncio.create_task(_start(hass, device_id, websocket))
        await asyncio.sleep(0)
        assert not start.done()
        coordinator.client.write_register.assert_not_awaited()
    try:
        await asyncio.wait_for(mode_started.wait(), 1)
        assert not start.done()
        assert not coordinator.sun_charge_active
        assert not power_started.is_set()
        finish_mode.set()
        await asyncio.wait_for(power_started.wait(), 1)
        assert not start.done()
        assert not coordinator.sun_charge_active
    finally:
        finish_mode.set()
        finish_power.set()

    assert _response(await start, boundary) == {
        "state": "charging",
        "reason": None,
        "requested_power_w": -1000,
        "current_soc": 72,
        "effective_max_soc": 100,
    }
    assert coordinator.grid_charge_active and coordinator.sun_charge_active
    assert coordinator._sun_charge_power == -1000


@pytest.mark.parametrize("boundary", ["service", "websocket"])
@pytest.mark.parametrize("blocked", [False, True])
async def test_start_remains_compatible_without_requested_response(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
    blocked: bool,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Bestehende Automationen brauchen keine Antwort."""
    coordinator, device_id = manual_device
    assert (
        hass.services.supports_response(DOMAIN, SERVICE_START_GRID_CHARGE)
        is SupportsResponse.OPTIONAL
    )
    coordinator._max_soc = 50 if blocked else 100
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None

    reply = await _start(hass, device_id, websocket, return_response=False)

    assert reply["success"] is True
    if websocket is None:
        assert reply["result"] is None
    else:
        assert "response" not in reply["result"]
    assert coordinator.grid_charge_active
    assert coordinator._sun_charge_power == (0 if blocked else -1000)


@pytest.mark.parametrize("boundary", ["service", "websocket"])
@pytest.mark.parametrize("hold", ["released", "window_ended", "held", "import"])
async def test_max_soc_response_preserves_release_and_deferred_manual_request(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
    hold: str,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Eine sichere Freigabe bleibt trotz Start erhalten."""
    coordinator, device_id = manual_device
    coordinator.data.update(soc=72, smartmeter_power=0, storage_power_active=0)
    coordinator._max_soc = 70
    if hold == "released":
        coordinator._max_soc_released_for_discharge = True
        coordinator._sun_charge_commanded_mode = SUN_IC_CONTROL_MODE_SMARTMETER
        coordinator._last_observed_ic_control_mode = SUN_IC_CONTROL_MODE_SMARTMETER
    elif hold == "import":
        coordinator.data["smartmeter_power"] = (
            SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 100
        )
        for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES - 1):
            coordinator._high_sample_revision += 1
            await coordinator._async_enforce_grid_charge(coordinator.data)
        coordinator._high_sample_revision += 1
    else:
        await coordinator._async_enforce_grid_charge(coordinator.data)
        if hold == "window_ended":
            coordinator._max_soc_hold_is_window_bound = True
    coordinator.client.write_register.reset_mock()
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None

    result = _response(await _start(hass, device_id, websocket), boundary)

    assert result == {
        "state": "blocked",
        "reason": "max_soc",
        "requested_power_w": -1000,
        "current_soc": 72,
        "effective_max_soc": 70,
    }
    assert coordinator.grid_charge_active
    if hold in ("released", "held"):
        coordinator.client.write_register.assert_not_awaited()
    else:
        coordinator.client.write_register.assert_awaited_once_with(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        )
    assert coordinator._max_soc_released_for_discharge is (hold != "held")

    coordinator.data["soc"] = 69
    coordinator.client.write_register.reset_mock()
    await coordinator._async_enforce_grid_charge(coordinator.data)

    assert coordinator.grid_charge_active and coordinator.sun_charge_active
    assert coordinator._sun_charge_power == -1000
    assert coordinator.client.write_register.await_count == 2
    assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SETPOINT


@pytest.mark.parametrize("boundary", ["service", "websocket"])
async def test_price_slot_soc_hold_reports_blocked_below_the_global_limit(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Der Preis-Slot-Hold entscheidet auch nach SOC-Abfall."""
    coordinator, device_id = manual_device
    coordinator.data["soc"] = 69
    coordinator._max_soc = 70
    coordinator._max_soc_hold_is_price_slot_bound = True
    coordinator._max_soc_price_slot_target = 70
    coordinator._price_charge_enabled = True
    coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    now = dt_util.now()
    coordinator.price_planner.plan = PricePlan(
        charge_now=True,
        slots=(PriceSlot(now, now + timedelta(hours=1), 0.1),),
    )
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None

    result = _response(await _start(hass, device_id, websocket), boundary)

    assert result["state"] == "blocked" and result["reason"] == "max_soc"
    assert result["current_soc"] < result["effective_max_soc"]
    assert coordinator.grid_charge_active and coordinator.max_soc_clamped
    assert coordinator._sun_charge_power == 0
    assert all(
        call.kwargs["value"] == 0
        for call in coordinator.client.write_register.await_args_list
        if call.kwargs["address"] == REG_SUN_IC_POWER_SETPOINT_PCT
    )


@pytest.mark.parametrize("boundary", ["service", "websocket"])
@pytest.mark.parametrize("soc", [None, True, float("nan"), float("inf"), -1, 101, "72"])
async def test_invalid_soc_is_rejected_before_request_or_device_mutation(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
    soc: Any,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Fehlende SOC-Bestätigung ist kein stiller Erfolg."""
    coordinator, device_id = manual_device
    coordinator.data["soc"] = soc
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None

    if websocket is None:
        with pytest.raises(HomeAssistantError, match="gültigen aktuellen SOC"):
            await _start(hass, device_id, websocket)
    else:
        reply = await _start(hass, device_id, websocket)
        assert reply["success"] is False
        assert reply["error"]["translation_key"] == "manual_grid_charge_soc_unavailable"
    assert not coordinator.grid_charge_active and not coordinator.sun_charge_active
    coordinator.client.write_register.assert_not_awaited()


@pytest.mark.parametrize("boundary", ["service", "websocket"])
@pytest.mark.parametrize("failed_register", [40051, 40049])
@pytest.mark.parametrize("failure_kind", ["modbus", "timeout", "response"])
async def test_failed_acknowledgement_never_returns_a_charging_response(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
    failed_register: int,
    failure_kind: str,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Schreibfehler bleiben echte Servicefehler."""
    coordinator, device_id = manual_device
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None
    success = coordinator.client.write_register.return_value
    target = (
        REG_SUN_IC_CONTROL_MODE
        if failed_register == 40051
        else REG_SUN_IC_POWER_SETPOINT_PCT
    )

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address != target or value == SUN_IC_CONTROL_MODE_SMARTMETER:
            return success
        if failure_kind == "modbus":
            raise ModbusException("Start abgelehnt")
        if failure_kind == "timeout":
            raise TimeoutError("Start ohne Antwort")
        failure = MagicMock()
        failure.isError.return_value = True
        return failure

    coordinator.client.write_register.side_effect = write
    if websocket is None:
        with pytest.raises(HomeAssistantError, match=f"Register {failed_register}"):
            await _start(hass, device_id, websocket)
    else:
        reply = await _start(hass, device_id, websocket)
        assert reply["success"] is False
        assert f"Register {failed_register}" in reply["error"]["message"]
    assert not coordinator.grid_charge_active and not coordinator.sun_charge_active


@pytest.mark.parametrize("boundary", ["service", "websocket"])
async def test_response_applies_a_max_soc_change_accepted_during_device_ack(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Die Antwort bestätigt keinen überholten Grenzwert."""
    coordinator, device_id = manual_device
    coordinator.data["soc"] = 72
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None
    power_started, finish_power = asyncio.Event(), asyncio.Event()
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == REG_SUN_IC_POWER_SETPOINT_PCT and value != 0:
            power_started.set()
            await finish_power.wait()
        return success

    coordinator.client.write_register.side_effect = write
    start = asyncio.create_task(_start(hass, device_id, websocket))
    try:
        await asyncio.wait_for(power_started.wait(), 1)
        await asyncio.wait_for(
            coordinator.async_set_max_soc(70, defer_device_update=True), 1
        )
        assert not start.done()
    finally:
        finish_power.set()

    assert _response(await start, boundary) == {
        "state": "blocked",
        "reason": "max_soc",
        "requested_power_w": -1000,
        "current_soc": 72,
        "effective_max_soc": 70,
    }
    assert coordinator.grid_charge_active and coordinator.max_soc_clamped
    assert coordinator._sun_charge_power == 0


@pytest.mark.parametrize("rollback_fails", [False, True])
async def test_failed_partial_start_publishes_the_last_acknowledged_mode(
    hass: HomeAssistant,
    manual_device: tuple[SaxPowerCoordinator, str],
    rollback_fails: bool,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Fehler verstecken weder Reset-ACK noch offenen Modus."""
    coordinator, device_id = manual_device
    success = coordinator.client.write_register.return_value
    rollback_started, finish_rollback = asyncio.Event(), asyncio.Event()
    published_modes: list[int] = []

    def state_updated() -> None:
        published_modes.append(coordinator.data["ic_control_mode"])

    unsubscribe = coordinator.async_add_listener(state_updated)

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == REG_SUN_IC_POWER_SETPOINT_PCT:
            raise ModbusException("Sollwert abgelehnt")
        if value == SUN_IC_CONTROL_MODE_SMARTMETER:
            rollback_started.set()
            await finish_rollback.wait()
            if rollback_fails:
                raise ModbusException("Rollback abgelehnt")
        return success

    coordinator.client.write_register.side_effect = write
    start = asyncio.create_task(_start(hass, device_id, None))
    try:
        await asyncio.wait_for(rollback_started.wait(), 1)
        assert not start.done()
        assert not published_modes
    finally:
        finish_rollback.set()
    try:
        with pytest.raises(HomeAssistantError, match="Register 40049"):
            await start
        assert published_modes == [
            (
                SUN_IC_CONTROL_MODE_SETPOINT
                if rollback_fails
                else SUN_IC_CONTROL_MODE_SMARTMETER
            )
        ]
        assert coordinator._sun_charge_reset_required is rollback_fails
        assert not coordinator.grid_charge_active and not coordinator.sun_charge_active
    finally:
        unsubscribe()


@pytest.mark.parametrize("boundary", ["service", "websocket"])
@pytest.mark.parametrize("blocked", [False, True])
@pytest.mark.parametrize(
    "scale, power", [(0, -1), (0, -20), (0, -23), (65535, -1), (2, -1000)]
)
async def test_unrepresentable_manual_power_is_rejected_without_device_writes(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
    blocked: bool,
    scale: int,
    power: int,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Ein negativer Wattwert darf keinen 0-%-Hold starten."""
    coordinator, device_id = manual_device
    coordinator._ic_power_setpoint_sf_raw = scale
    coordinator._max_soc = 50 if blocked else 100
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None

    if websocket is None:
        with pytest.raises(HomeAssistantError) as raised:
            await _start(hass, device_id, websocket, power=power)
        assert raised.value.translation_key == "manual_grid_charge_power_resolution"
    else:
        reply = await _start(hass, device_id, websocket, power=power)
        assert reply["success"] is False
        assert (
            reply["error"]["translation_key"] == "manual_grid_charge_power_resolution"
        )
    assert not coordinator.grid_charge_active and not coordinator.sun_charge_active
    coordinator.client.write_register.assert_not_awaited()


@pytest.mark.parametrize("boundary", ["service", "websocket"])
async def test_manual_power_just_above_device_resolution_is_acknowledged(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    manual_device: tuple[SaxPowerCoordinator, str],
    boundary: str,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Bei 4600 W/SF 0 trennt 23/24 W die Darstellbarkeit."""
    coordinator, device_id = manual_device
    coordinator._ic_power_setpoint_sf_raw = 0
    websocket = await hass_ws_client(hass) if boundary == "websocket" else None

    result = _response(await _start(hass, device_id, websocket, power=-24), boundary)

    assert result["state"] == "charging"
    assert result["requested_power_w"] == -24
    assert coordinator._sun_charge_power == -24
    coordinator.client.write_register.assert_awaited_with(
        address=REG_SUN_IC_POWER_SETPOINT_PCT, value=65535, device_id=100
    )


async def test_unrepresentable_change_preserves_the_existing_manual_request(
    hass: HomeAssistant,
    manual_device: tuple[SaxPowerCoordinator, str],
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Ungültige Folgeaufträge erhalten laufende Ladung."""
    coordinator, device_id = manual_device
    await _start(hass, device_id, None)
    writer = coordinator._sun_charge_task
    coordinator._ic_power_setpoint_sf_raw = 0
    coordinator.client.write_register.reset_mock()

    with pytest.raises(HomeAssistantError) as raised:
        await _start(hass, device_id, None, power=-23)

    assert raised.value.translation_key == "manual_grid_charge_power_resolution"
    assert coordinator._grid_charge_power == -1000
    assert coordinator._sun_charge_power == -1000
    assert coordinator._sun_charge_task is writer and coordinator.sun_charge_active
    coordinator.client.write_register.assert_not_awaited()


async def test_scale_change_after_validation_cannot_write_a_zero_manual_setpoint(
    hass: HomeAssistant,
    manual_device: tuple[SaxPowerCoordinator, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Der tatsächliche Write prüft die aktuelle Skalierung."""
    coordinator, device_id = manual_device

    async def scale_changes_while_persisting(_state: Any) -> None:
        coordinator._ic_power_setpoint_sf_raw = 0

    monkeypatch.setattr(
        coordinator, "_async_persist_timed_charge_state", scale_changes_while_persisting
    )
    with pytest.raises(HomeAssistantError) as raised:
        await _start(hass, device_id, None, power=-23)

    assert raised.value.translation_key == "manual_grid_charge_power_resolution"
    assert not coordinator.grid_charge_active and not coordinator.sun_charge_active
    coordinator.client.write_register.assert_not_awaited()
