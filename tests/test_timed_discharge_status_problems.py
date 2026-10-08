"""REQ-TIMED-SOC-CHARGE: failed device phases remain visible until recovery."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.const import (
    CONF_ECONOMICS_TARIFF_TYPE,
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_START,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

from .test_timed_discharge_coordinator import (
    EXPIRES,
    _confirm_grid_charge,
    _evaluate,
    _reach_target_with_pv,
    _sample,
)
from .test_timed_discharge_coordinator import (
    charge_system as charge_system,
)


@pytest.mark.parametrize(
    ("failed_phase", "problem", "reset_required"),
    [
        ("mode", "control_mode_failed", False),
        ("setpoint", "setpoint_failed", False),
        ("rollback", "reset_failed", True),
    ],
)
async def test_failed_device_phase_survives_cleanup_and_recovers_on_fresh_poll(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
    failed_phase: str,
    problem: str,
    reset_required: bool,
) -> None:
    """REQ-TIMED-SOC-CHARGE: report the failed phase, never an inferred release."""
    coordinator, client = charge_system
    coordinator._timed_charge_enabled = True
    success = client.write_register.return_value
    client.write_register.side_effect = {
        "mode": [ModbusException("Modus abgelehnt")],
        "setpoint": [success, ModbusException("Sollwert abgelehnt"), success],
        "rollback": [
            success,
            ModbusException("Sollwert abgelehnt"),
            ModbusException("Rücksetzung abgelehnt"),
        ],
    }[failed_phase]

    with pytest.raises(HomeAssistantError):
        await _evaluate(coordinator)

    assert coordinator.data["timed_charge_discharge_status"] == problem
    assert coordinator._sun_charge_reset_required is reset_required
    assert not coordinator.sun_charge_active
    writes = [
        (call.kwargs["address"], call.kwargs["value"])
        for call in client.write_register.await_args_list
    ]
    assert writes[0] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT)
    if failed_phase != "mode":
        assert writes[1][0] == REG_SUN_IC_POWER_SETPOINT_PCT
        assert writes[-1] == (
            REG_SUN_IC_CONTROL_MODE,
            SUN_IC_CONTROL_MODE_SMARTMETER,
        )
    if failed_phase == "setpoint":
        assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SMARTMETER

    coordinator._clear_sun_charge_active_flags()
    coordinator._publish_charge_state(coordinator.data)
    assert coordinator.data["timed_charge_discharge_status"] == problem

    client.write_register.side_effect = None
    await _evaluate(coordinator)
    assert coordinator._sun_charge_control_problem is None
    assert coordinator.sun_charge_active
    for _ in range(2):
        _sample(coordinator, storage_power_active=-2000, smartmeter_power=2300)
        await _evaluate(coordinator)
    assert coordinator.data["timed_charge_discharge_status"] == "grid_charging"
    assert coordinator._timed_charge_enabled


async def test_failed_stop_is_explained_and_next_poll_confirms_release(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """REQ-TIMED-SOC-CHARGE: an accepted disable still exposes a failed reset."""
    coordinator, client = charge_system
    await _confirm_grid_charge(coordinator)
    client.write_register.side_effect = ModbusException("Rücksetzung abgelehnt")

    await coordinator.async_set_timed_charge_enabled(False)

    assert coordinator.data["timed_charge_discharge_status"] == "reset_failed"
    assert coordinator._sun_charge_reset_required
    assert not coordinator.sun_charge_active
    assert not coordinator._timed_charge_enabled

    client.write_register.side_effect = None
    await _evaluate(coordinator)

    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    assert coordinator._sun_charge_control_problem is None
    assert not coordinator._sun_charge_reset_required
    assert not coordinator._timed_charge_enabled


@pytest.mark.parametrize(
    ("reference", "scale"),
    [
        (None, 0),
        (0, 0),
        (float("nan"), 0),
        (4600, None),
        (4600, True),
        (4600, 0x8000),
    ],
)
async def test_invalid_control_data_is_explained_before_any_mode_write(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
    reference: float | int | None,
    scale: int | None,
) -> None:
    """REQ-TIMED-SOC-CHARGE: invalid device data must not imply a failed write."""
    coordinator, client = charge_system
    coordinator._timed_charge_enabled = True
    coordinator.data["ic_max_power_reference"] = reference
    coordinator._ic_power_setpoint_sf_raw = scale

    with pytest.raises(HomeAssistantError):
        await _evaluate(coordinator)

    assert coordinator.data["timed_charge_discharge_status"] == "control_data_missing"
    assert not coordinator.sun_charge_active
    client.write_register.assert_not_awaited()

    coordinator.data["ic_max_power_reference"] = 4600
    coordinator._ic_power_setpoint_sf_raw = 0
    await _evaluate(coordinator)

    assert coordinator._sun_charge_control_problem is None
    assert coordinator.sun_charge_active
    assert coordinator._timed_charge_enabled


async def test_periodic_setpoint_failure_preserves_hold_and_recovers_on_poll(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """REQ-TIMED-SOC-CHARGE: background failure reports its phase and retries."""
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)
    proof = coordinator._timed_discharge_state
    await coordinator._async_cancel_sun_charge_task()
    success = client.write_register.return_value
    client.write_register.side_effect = [
        success,
        ModbusException("Periodischer Sollwert abgelehnt"),
        success,
    ]

    with patch(
        "custom_components.sax_power.coordinator.asyncio.sleep", new=AsyncMock()
    ):
        with pytest.raises(HomeAssistantError):
            await coordinator._async_sun_charge_loop()

    assert coordinator.data["timed_charge_discharge_status"] == "setpoint_failed"
    assert coordinator._timed_discharge_state == proof
    assert not coordinator.sun_charge_active
    assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SMARTMETER

    client.write_register.side_effect = None
    _sample(coordinator, storage_power_active=0, smartmeter_power=400)
    await _evaluate(coordinator)

    assert coordinator.data["timed_charge_discharge_status"] == "discharge_blocked"
    assert coordinator._sun_charge_control_problem is None
    assert coordinator._timed_discharge_state == proof
    assert coordinator.sun_charge_active


async def test_periodic_expiry_reset_failure_is_explained_and_retried(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """REQ-TIMED-SOC-CHARGE: timer expiry and normal stops share reset feedback."""
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)
    await coordinator._async_cancel_sun_charge_task()
    client.write_register.reset_mock()
    client.write_register.side_effect = ModbusException("Timer-Rücksetzung abgelehnt")

    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=EXPIRES,
        ),
        patch("custom_components.sax_power.coordinator.asyncio.sleep", new=AsyncMock()),
    ):
        with pytest.raises(HomeAssistantError):
            await coordinator._async_sun_charge_loop()

    assert coordinator.data["timed_charge_discharge_status"] == "reset_failed"
    assert coordinator._sun_charge_reset_required
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )

    client.write_register.side_effect = None
    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=EXPIRES,
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.now", return_value=EXPIRES
        ),
    ):
        await _evaluate(coordinator)

    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    assert coordinator._sun_charge_control_problem is None
    assert not coordinator._sun_charge_reset_required
    assert not coordinator.sun_charge_active


async def test_successful_tariff_change_reset_does_not_create_a_problem(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """REQ-VUE-ELECTRICITY-TARIFF: superseding a writer is not a device failure."""
    coordinator, client = charge_system
    await _confirm_grid_charge(coordinator)
    client.write_register.reset_mock()

    await coordinator.async_apply_tariff_options(
        {CONF_ECONOMICS_TARIFF_TYPE: "time_of_use"}
    )
    if (task := coordinator._month_control_task) is not None:
        await asyncio.wait_for(task, 1)

    assert coordinator._sun_charge_control_problem is None
    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    assert not coordinator.sun_charge_active
    assert not coordinator._sun_charge_reset_required
    assert coordinator._tariff_control_revision == coordinator._tariff_source_revision
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_actual_sunspec_read_failure_is_explained_until_next_successful_read(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """REQ-EXTENDED-MODE-RESILIENCE: read failure is not a device-write failure."""
    coordinator, client = charge_system
    coordinator._async_read_basic = AsyncMock(return_value={"soc": 39})
    coordinator._async_read_low_block = AsyncMock(return_value={})
    client.read_holding_registers = AsyncMock(
        side_effect=ModbusException("SunSpec-Abfrage abgelehnt")
    )

    coordinator.data = await coordinator._async_update_data()

    assert (
        coordinator.data["timed_charge_discharge_status"] == "device_feedback_missing"
    )
    assert not coordinator._extended_available
    assert coordinator._sun_charge_control_problem is None
    assert coordinator.data["soc"] == 39
    client.write_register.assert_not_awaited()
    client.read_holding_registers.assert_awaited_once_with(
        address=READ_BLOCK_EXT_START,
        count=READ_BLOCK_EXT_COUNT,
        device_id=100,
    )

    success = MagicMock()
    success.isError.return_value = False
    success.registers = [0] * READ_BLOCK_EXT_COUNT
    client.read_holding_registers.side_effect = None
    client.read_holding_registers.return_value = success
    coordinator.data = await coordinator._async_update_data()

    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    assert coordinator._extended_available
    assert coordinator._sun_charge_control_problem is None
    assert client.read_holding_registers.await_count == 2


async def test_existing_hold_without_writer_is_not_reported_as_confirmed(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """REQ-TIMED-SOC-CHARGE: retained proof alone cannot confirm a device hold."""
    coordinator, _ = charge_system
    await _confirm_grid_charge(coordinator)
    proof = coordinator._timed_discharge_state
    await coordinator._async_cancel_sun_charge_task()

    coordinator._publish_charge_state(coordinator.data)

    assert coordinator.data["timed_charge_discharge_status"] == (
        "discharge_hold_unconfirmed"
    )
    assert coordinator._sun_charge_control_problem is None
    assert coordinator._timed_discharge_state == proof


async def test_open_reset_without_writer_is_not_reported_as_released(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """REQ-TIMED-SOC-CHARGE: an unfinished release cannot advertise normality."""
    coordinator, client = charge_system
    coordinator._sun_charge_reset_required = True
    coordinator._last_observed_ic_control_mode = SUN_IC_CONTROL_MODE_SETPOINT

    coordinator._publish_charge_state(coordinator.data)

    assert coordinator.data["timed_charge_discharge_status"] == "release_unconfirmed"
    assert coordinator._sun_charge_control_problem is None
    client.write_register.assert_not_awaited()

    await _evaluate(coordinator)

    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    assert not coordinator._sun_charge_reset_required


@pytest.mark.parametrize("problem", ["control_data_missing", "control_mode_failed"])
@pytest.mark.parametrize("new_feedback_mode", [0, 1])
async def test_inactive_noop_clears_problem_only_after_new_normal_mode_read(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
    problem: str,
    new_feedback_mode: int,
) -> None:
    """REQ-TIMED-SOC-CHARGE: cached or older in-flight reads cannot prove recovery."""
    coordinator, client = charge_system
    coordinator.data["ic_control_mode"] = SUN_IC_CONTROL_MODE_SMARTMETER
    await _evaluate(coordinator)
    client.write_register.reset_mock()
    read_started, finish_read = asyncio.Event(), asyncio.Event()
    response = MagicMock()
    response.isError.return_value = False
    response.registers = [0] * READ_BLOCK_EXT_COUNT

    async def delayed_read(**kwargs: int) -> MagicMock:
        read_started.set()
        await finish_read.wait()
        return response

    client.read_holding_registers = AsyncMock(side_effect=delayed_read)
    with patch("custom_components.sax_power.coordinator.monotonic", return_value=100):
        read_task = asyncio.create_task(coordinator._async_read_high_block())
        await read_started.wait()

    coordinator._timed_charge_enabled = True
    if problem == "control_data_missing":
        coordinator.data["ic_max_power_reference"] = 0
    else:
        client.write_register.side_effect = ModbusException("Modus-ACK fehlt")
    with patch("custom_components.sax_power.coordinator.monotonic", return_value=101):
        with pytest.raises(HomeAssistantError):
            await _evaluate(coordinator)

    client.write_register.side_effect = None
    client.write_register.reset_mock()
    with patch("custom_components.sax_power.coordinator.monotonic", return_value=101.5):
        finish_read.set()
        await read_task
        await coordinator.async_set_timed_charge_enabled(False)
        assert coordinator.data["timed_charge_discharge_status"] == problem
        assert coordinator._high_sample_started_at == 100
        assert coordinator._high_sample_time == 101.5

        client.read_holding_registers.reset_mock()
        await coordinator._async_read_high_block()
        client.read_holding_registers.assert_not_awaited()
        await coordinator.async_stop_sun_charge()
        coordinator._publish_charge_state(coordinator.data)
        assert coordinator.data["timed_charge_discharge_status"] == problem

    response.registers[REG_SUN_IC_CONTROL_MODE - READ_BLOCK_EXT_START] = (
        new_feedback_mode
    )
    client.read_holding_registers.side_effect = None
    client.read_holding_registers.return_value = response
    with patch("custom_components.sax_power.coordinator.monotonic", return_value=103):
        await coordinator._async_read_high_block()
        client.read_holding_registers.assert_awaited_once()
        await coordinator.async_stop_sun_charge()
        coordinator._publish_charge_state(coordinator.data)

    assert coordinator.data["timed_charge_discharge_status"] == (
        "normal" if new_feedback_mode == SUN_IC_CONTROL_MODE_SMARTMETER else problem
    )
    assert not coordinator._timed_charge_enabled
    client.write_register.assert_not_awaited()
