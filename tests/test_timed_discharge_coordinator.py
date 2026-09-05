"""REQ-TIMED-SOC-CHARGE: measured charging owns the timed discharge hold."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from time import monotonic
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.application.timed_discharge import TimedDischargeState
from custom_components.sax_power.const import (
    READ_BLOCK_EXT_HIGH_INTERVAL,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator, to_unsigned16
from custom_components.sax_power.infrastructure.timed_discharge_store import (
    TimedDischargeStateStore,
)

NOW = datetime(2026, 9, 5, 2, tzinfo=UTC)
EXPIRES = datetime(2026, 9, 5, 5, tzinfo=UTC)


def _make_coordinator(hass: HomeAssistant, client: MagicMock) -> SaxPowerCoordinator:
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="timed_discharge_entry",
    )
    coordinator._max_soc = 90
    coordinator._timed_charge_min_soc = 40
    coordinator._timed_charge_max_soc = 60
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(5)
    coordinator.data = {
        "soc": 39,
        "storage_power_active": 0,
        "smartmeter_power": 0,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    return coordinator


@pytest.fixture
async def charge_system(
    hass: HomeAssistant,
) -> AsyncIterator[tuple[SaxPowerCoordinator, MagicMock]]:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    success = MagicMock()
    success.isError.return_value = False
    client.write_register = AsyncMock(return_value=success)
    coordinator = _make_coordinator(hass, client)
    with (
        patch("custom_components.sax_power.coordinator.dt_util.now", return_value=NOW),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow", return_value=NOW
        ),
    ):
        try:
            yield coordinator, client
        finally:
            await coordinator.async_shutdown()


def _sample(coordinator: SaxPowerCoordinator, **values: object) -> None:
    assert coordinator.data is not None
    coordinator.data["ic_control_mode"] = SUN_IC_CONTROL_MODE_SETPOINT
    coordinator.data.update(values)
    coordinator._high_data = coordinator.data.copy()
    coordinator._high_sample_revision += 1
    coordinator._high_sample_started_at = monotonic()
    coordinator._high_sample_time = monotonic()
    coordinator._high_sample_control_mode = coordinator.data["ic_control_mode"]


async def _evaluate(coordinator: SaxPowerCoordinator) -> None:
    assert coordinator.data is not None
    await coordinator._async_enforce_grid_charge(coordinator.data)
    coordinator._publish_charge_state(coordinator.data)


async def _confirm_grid_charge(coordinator: SaxPowerCoordinator) -> None:
    await coordinator.async_set_timed_charge_enabled(True)
    for _ in range(2):
        _sample(coordinator, storage_power_active=-2000, smartmeter_power=2300)
        await _evaluate(coordinator)
    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)


async def _reach_target_with_pv(coordinator: SaxPowerCoordinator) -> None:
    await _confirm_grid_charge(coordinator)
    _sample(coordinator, soc=60, storage_power_active=-700, smartmeter_power=-300)
    await _evaluate(coordinator)
    assert coordinator._sun_charge_power == -1000


async def test_failed_hold_setpoint_preserves_proof_and_recovers_on_next_poll(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """REQ-TIMED-SOC-CHARGE: a failed sequence is unknown, never a lost proof."""
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)
    success = client.write_register.return_value
    client.write_register.side_effect = [
        success,
        ModbusException("Sollwert fehlgeschlagen"),
        success,
    ]
    _sample(coordinator, storage_power_active=0, smartmeter_power=400)

    with pytest.raises(HomeAssistantError, match="40049 fehlgeschlagen"):
        await _evaluate(coordinator)

    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)
    assert coordinator.data["timed_charge_discharge_status"] is None
    assert coordinator.sun_charge_active is False
    assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SMARTMETER

    client.write_register.side_effect = None
    await _evaluate(coordinator)
    assert coordinator._sun_charge_power == 0
    assert coordinator.sun_charge_active is True
    assert coordinator.data["timed_charge_discharge_status"] == "discharge_blocked"


async def test_failed_disable_reset_is_not_reported_as_successful_release(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    """REQ-TIMED-SOC-CHARGE: retry the release without resurrecting charging."""
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)
    client.write_register.side_effect = ModbusException("Reset fehlgeschlagen")

    await coordinator.async_set_timed_charge_enabled(False)

    assert coordinator._timed_discharge_state is None
    assert coordinator._sun_charge_reset_required is True
    assert coordinator.data["timed_charge_discharge_status"] is None
    assert coordinator.sun_charge_active is False

    client.write_register.side_effect = None
    await _evaluate(coordinator)
    assert coordinator._sun_charge_reset_required is False
    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    assert coordinator.sun_charge_active is False


async def test_two_fresh_measurements_confirm_and_persist_timed_grid_charging(
    hass: HomeAssistant, charge_system: tuple[SaxPowerCoordinator, MagicMock]
) -> None:
    coordinator, client = charge_system
    await coordinator.async_set_timed_charge_enabled(True)
    assert coordinator._timed_discharge_state is None
    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    client.write_register.assert_any_await(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SETPOINT,
        device_id=100,
    )

    _sample(coordinator, storage_power_active=-2000, smartmeter_power=2300)
    await _evaluate(coordinator)
    assert coordinator._timed_discharge_state is None

    _sample(coordinator, storage_power_active=-2200, smartmeter_power=2500)
    await _evaluate(coordinator)

    assert coordinator.data["timed_charge_discharge_status"] == "grid_charging"
    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)
    assert await TimedDischargeStateStore(hass, coordinator.entry_id).async_load() == (
        TimedDischargeState(EXPIRES)
    )


async def test_repeated_setters_cannot_turn_one_measurement_into_confirmation(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    coordinator, _ = charge_system
    await coordinator.async_set_timed_charge_enabled(True)
    _sample(coordinator, storage_power_active=-2000, smartmeter_power=2300)
    await _evaluate(coordinator)

    for _ in range(3):
        await coordinator.async_set_timed_charge_max_soc(60)

    assert coordinator._timed_discharge_state is None
    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    _sample(coordinator, storage_power_active=-2100, smartmeter_power=2400)
    await _evaluate(coordinator)
    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)


@pytest.mark.parametrize(
    ("storage", "grid"),
    [
        (-2000, 0),
        (0, 2000),
        (500, 500),
        (-2000, -500),
        (None, 2000),
        (-2000, None),
        (float("nan"), 2000),
        (-2000, float("nan")),
        (False, 2000),
        (-2000, True),
    ],
)
async def test_pv_or_missing_measured_grid_charge_never_creates_protection(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
    storage: object,
    grid: object,
) -> None:
    coordinator, _ = charge_system
    await coordinator.async_set_timed_charge_enabled(True)

    for _ in range(3):
        _sample(coordinator, storage_power_active=storage, smartmeter_power=grid)
        await _evaluate(coordinator)

    assert coordinator._timed_discharge_state is None
    assert coordinator.data["timed_charge_discharge_status"] == "normal"


async def test_measurement_started_before_command_ack_cannot_prove_its_effect(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    coordinator, _ = charge_system
    await coordinator.async_set_timed_charge_enabled(True)

    for _ in range(2):
        _sample(coordinator, storage_power_active=-2000, smartmeter_power=2300)
        coordinator._high_sample_started_at = coordinator._timed_charge_started_at - 1
        await _evaluate(coordinator)

    assert coordinator._timed_discharge_state is None


async def test_optimistic_mode_cache_does_not_turn_real_mode_zero_into_proof(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    coordinator, _ = charge_system
    await coordinator.async_set_timed_charge_enabled(True)

    for _ in range(2):
        _sample(
            coordinator,
            storage_power_active=-2000,
            smartmeter_power=2300,
            ic_control_mode=SUN_IC_CONTROL_MODE_SMARTMETER,
        )
        coordinator._record_ic_control_mode(SUN_IC_CONTROL_MODE_SETPOINT)
        assert coordinator._high_data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SETPOINT
        await _evaluate(coordinator)

    assert coordinator._timed_discharge_state is None
    assert coordinator.data["timed_charge_discharge_status"] == "normal"


async def test_stale_or_interrupted_measurements_require_two_new_confirmations(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    coordinator, _ = charge_system
    await coordinator.async_set_timed_charge_enabled(True)
    _sample(coordinator, storage_power_active=-2000, smartmeter_power=2300)
    await _evaluate(coordinator)

    _sample(coordinator, storage_power_active=-2000, smartmeter_power=2300)
    coordinator._high_sample_time = monotonic() - 2 * READ_BLOCK_EXT_HIGH_INTERVAL - 1
    await _evaluate(coordinator)
    assert coordinator._timed_discharge_state is None

    _sample(coordinator, storage_power_active=-2000, smartmeter_power=2300)
    await _evaluate(coordinator)
    assert coordinator._timed_discharge_state is None
    _sample(coordinator, storage_power_active=-2000, smartmeter_power=2300)
    await _evaluate(coordinator)
    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)


async def test_own_target_keeps_discharge_blocked_and_allows_only_pv_charge(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)

    assert coordinator._timed_charge_active is False
    assert coordinator.max_soc_clamped is False
    assert coordinator.sun_charge_active is True
    assert coordinator._sun_charge_timed_discharge is True
    assert coordinator.data["timed_charge_discharge_status"] == "discharge_blocked"
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_POWER_SETPOINT_PCT,
        value=to_unsigned16(-2174),
        device_id=100,
    )

    _sample(coordinator, storage_power_active=-1000, smartmeter_power=1600)
    await _evaluate(coordinator)

    assert coordinator._sun_charge_power == 0
    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_POWER_SETPOINT_PCT, value=0, device_id=100
    )


async def test_unconfirmed_charge_reaching_target_releases_normal_operation(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    coordinator, client = charge_system
    await coordinator.async_set_timed_charge_enabled(True)
    _sample(coordinator, soc=60, storage_power_active=-1000, smartmeter_power=-500)
    await _evaluate(coordinator)

    assert coordinator._timed_discharge_state is None
    assert coordinator.sun_charge_active is False
    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_disabling_releases_immediately_and_reenabling_is_no_measurement(
    hass: HomeAssistant, charge_system: tuple[SaxPowerCoordinator, MagicMock]
) -> None:
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)
    client.write_register.reset_mock()

    await coordinator.async_set_timed_charge_enabled(False)

    assert coordinator._timed_discharge_state is None
    assert coordinator.sun_charge_active is False
    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )
    assert (
        await TimedDischargeStateStore(hass, coordinator.entry_id).async_load() is None
    )

    await coordinator.async_set_timed_charge_enabled(True)
    for _ in range(3):
        await _evaluate(coordinator)
    assert coordinator._timed_discharge_state is None
    assert coordinator.sun_charge_active is False
    assert coordinator.data["timed_charge_discharge_status"] == "normal"


async def test_window_end_releases_protection_and_does_not_carry_into_next_day(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)
    client.write_register.reset_mock()

    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.now", return_value=EXPIRES
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=EXPIRES,
        ),
    ):
        await _evaluate(coordinator)

    assert coordinator._timed_discharge_state is None
    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )
    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=NOW + timedelta(days=1),
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=NOW + timedelta(days=1),
        ),
    ):
        await _evaluate(coordinator)
    assert coordinator._timed_discharge_state is None
    assert coordinator.sun_charge_active is False


async def test_restart_restores_confirmed_expiry_and_reapplies_protection(
    hass: HomeAssistant, charge_system: tuple[SaxPowerCoordinator, MagicMock]
) -> None:
    original, client = charge_system
    await _reach_target_with_pv(original)
    await original.async_shutdown()
    restored = _make_coordinator(hass, client)
    restored._timed_charge_enabled = True
    restored.data["soc"] = 60
    try:
        await restored.async_load_timed_discharge_state()
        await _evaluate(restored)

        assert restored._timed_discharge_state == TimedDischargeState(EXPIRES)
        assert restored.sun_charge_active is True
        assert restored._sun_charge_power == 0
        assert restored.data["timed_charge_discharge_status"] == "discharge_blocked"
    finally:
        await restored.async_shutdown()


@pytest.mark.parametrize(
    "expires_at", [NOW, NOW - timedelta(seconds=1), NOW + timedelta(hours=26)]
)
async def test_restart_rejects_expired_or_unbounded_protection(
    charge_system: tuple[SaxPowerCoordinator, MagicMock], expires_at: datetime
) -> None:
    coordinator, _ = charge_system
    await coordinator._timed_discharge_store.async_save(TimedDischargeState(expires_at))
    coordinator._timed_charge_enabled = True
    coordinator.data["soc"] = 60

    await coordinator.async_load_timed_discharge_state()
    await _evaluate(coordinator)

    assert coordinator._timed_discharge_state is None
    assert coordinator.sun_charge_active is False
    assert coordinator.data["timed_charge_discharge_status"] == "normal"


@pytest.mark.parametrize("failed_block", ["basic", "extended"])
async def test_read_failure_replaces_stale_pv_power_with_zero(
    charge_system: tuple[SaxPowerCoordinator, MagicMock], failed_block: str
) -> None:
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)
    client.write_register.reset_mock()
    if failed_block == "basic":
        coordinator._async_read_basic = AsyncMock(side_effect=UpdateFailed("offline"))
        with pytest.raises(UpdateFailed, match="offline"):
            await coordinator._async_update_data()
    else:
        coordinator._async_read_basic = AsyncMock(return_value={"soc": 60})
        coordinator._async_read_low_block = AsyncMock(return_value={})
        error = MagicMock()
        error.isError.return_value = True
        client.read_holding_registers = AsyncMock(return_value=error)
        coordinator._high_last_read = None
        coordinator.data = await coordinator._async_update_data()
        assert "ic_max_power_reference" not in coordinator.data

    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)
    assert coordinator._sun_charge_power == 0
    assert coordinator.sun_charge_active is True
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_POWER_SETPOINT_PCT, value=0, device_id=100
    )


@pytest.mark.parametrize("no_valid_scale", [False, True])
async def test_hold_writer_replaces_stale_pv_without_waiting_for_coordinator(
    charge_system: tuple[SaxPowerCoordinator, MagicMock], no_valid_scale: bool
) -> None:
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)
    await coordinator._async_cancel_sun_charge_task()
    coordinator._high_sample_time = monotonic() - 2 * READ_BLOCK_EXT_HIGH_INTERVAL - 1
    if no_valid_scale:
        coordinator.data.pop("ic_max_power_reference")
        coordinator._high_data.pop("ic_max_power_reference")
        coordinator._ic_power_setpoint_sf_raw = None
    client.write_register.reset_mock()

    with patch(
        "custom_components.sax_power.coordinator.asyncio.sleep",
        new=AsyncMock(side_effect=[None, asyncio.CancelledError()]),
    ):
        with pytest.raises(asyncio.CancelledError):
            await coordinator._async_sun_charge_loop()

    assert coordinator._sun_charge_power == 0
    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_POWER_SETPOINT_PCT, value=0, device_id=100
    )


async def test_hold_writer_cannot_pv_charge_above_global_soc_limit(
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
) -> None:
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)
    _sample(coordinator, soc=90, storage_power_active=-700, smartmeter_power=-300)
    await _evaluate(coordinator)
    assert coordinator._sun_charge_timed_discharge is True
    await coordinator._async_cancel_sun_charge_task()
    client.write_register.reset_mock()

    with patch(
        "custom_components.sax_power.coordinator.asyncio.sleep",
        new=AsyncMock(side_effect=[None, asyncio.CancelledError()]),
    ):
        with pytest.raises(asyncio.CancelledError):
            await coordinator._async_sun_charge_loop()

    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)
    assert coordinator._sun_charge_power == 0
    assert coordinator.max_soc_clamped is True
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_POWER_SETPOINT_PCT, value=0, device_id=100
    )


@pytest.mark.parametrize("global_soc_reached", [False, True])
async def test_hold_writer_releases_at_exact_deadline_without_basic_polls(
    charge_system: tuple[SaxPowerCoordinator, MagicMock], global_soc_reached: bool
) -> None:
    coordinator, client = charge_system
    await _reach_target_with_pv(coordinator)
    if global_soc_reached:
        _sample(coordinator, soc=90, storage_power_active=-700, smartmeter_power=-300)
        await _evaluate(coordinator)
        assert coordinator.max_soc_clamped is True
    assert coordinator._sun_charge_timed_discharge is True
    await coordinator._async_cancel_sun_charge_task()
    coordinator._async_read_basic = AsyncMock(side_effect=UpdateFailed("offline"))
    client.write_register.reset_mock()
    with patch(
        "custom_components.sax_power.coordinator.dt_util.utcnow",
        return_value=EXPIRES - timedelta(milliseconds=500),
    ) as utcnow:

        async def reach_deadline(interval: float) -> None:
            assert interval == 0.5
            utcnow.return_value = EXPIRES

        with patch(
            "custom_components.sax_power.coordinator.asyncio.sleep",
            new=AsyncMock(side_effect=reach_deadline),
        ):
            await coordinator._async_sun_charge_loop()

    coordinator._async_read_basic.assert_not_called()
    assert coordinator._timed_discharge_state is None
    assert coordinator._sun_charge_timed_discharge is False
    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    assert coordinator.max_soc_clamped is False
    if global_soc_reached:
        assert coordinator._max_soc_released_for_discharge is True
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


@pytest.mark.parametrize("soc", [50, 60, 90])
async def test_extending_window_cannot_restart_charge_or_hold_after_original_end(
    charge_system: tuple[SaxPowerCoordinator, MagicMock], soc: int
) -> None:
    """An edited 06:00 end cannot extend a charge confirmed to end at 05:00."""
    coordinator, client = charge_system
    await _confirm_grid_charge(coordinator)
    _sample(
        coordinator,
        soc=soc,
        storage_power_active=-2000 if soc == 50 else 0,
        smartmeter_power=2300 if soc == 50 else 400,
    )
    await _evaluate(coordinator)
    await coordinator.async_set_timed_charge_end(dt_time(6))
    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)
    client.write_register.reset_mock()

    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.now", return_value=EXPIRES
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=EXPIRES,
        ),
    ):
        for poll in range(2):
            _sample(
                coordinator,
                storage_power_active=-2000 if soc == 50 and poll == 0 else 0,
                smartmeter_power=2300 if soc == 50 and poll == 0 else 400,
                ic_control_mode=(
                    SUN_IC_CONTROL_MODE_SETPOINT
                    if poll == 0
                    else SUN_IC_CONTROL_MODE_SMARTMETER
                ),
            )
            await _evaluate(coordinator)

            assert coordinator._timed_discharge_state is None
            assert coordinator._timed_charge_active is False
            assert coordinator.sun_charge_active is False
            assert coordinator.max_soc_clamped is False
            assert coordinator.data["timed_charge_discharge_status"] == "normal"

    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )
    assert coordinator._timed_discharge_last_window_end == EXPIRES


@pytest.mark.parametrize("soc", [50, 60, 90])
async def test_restart_after_original_end_keeps_extended_window_completed(
    hass: HomeAssistant,
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
    soc: int,
) -> None:
    """A restored end marker suppresses today's extension, not tomorrow's charge."""
    original, client = charge_system
    await original.async_set_timed_charge_min_soc(55)
    await _confirm_grid_charge(original)
    _sample(original, soc=soc, storage_power_active=0, smartmeter_power=400)
    await _evaluate(original)
    await original.async_set_timed_charge_end(dt_time(6))
    await original.async_shutdown()
    restored = _make_coordinator(hass, client)
    restored._timed_charge_enabled = True
    restored._timed_charge_end = dt_time(6)
    restored._timed_charge_min_soc = 55
    restored.data["soc"] = soc
    restart_time = EXPIRES + timedelta(minutes=10)
    try:
        with (
            patch(
                "custom_components.sax_power.coordinator.dt_util.now",
                return_value=restart_time,
            ),
            patch(
                "custom_components.sax_power.coordinator.dt_util.utcnow",
                return_value=restart_time,
            ),
        ):
            await restored.async_load_timed_discharge_state()
            assert restored._timed_discharge_state is None
            assert restored._timed_discharge_last_window_end == EXPIRES
            for _ in range(3):
                _sample(
                    restored,
                    storage_power_active=0,
                    smartmeter_power=400,
                    ic_control_mode=SUN_IC_CONTROL_MODE_SMARTMETER,
                )
                await _evaluate(restored)

                assert restored._timed_discharge_state is None
                assert restored._timed_charge_active is False
                assert restored.sun_charge_active is False
                assert restored.max_soc_clamped is False
                assert restored.data["timed_charge_discharge_status"] == "normal"

        with (
            patch(
                "custom_components.sax_power.coordinator.dt_util.now",
                return_value=NOW + timedelta(days=1),
            ),
            patch(
                "custom_components.sax_power.coordinator.dt_util.utcnow",
                return_value=NOW + timedelta(days=1),
            ),
        ):
            _sample(restored, soc=39, storage_power_active=0, smartmeter_power=400)
            await _evaluate(restored)
            assert restored._timed_charge_active is True
            for _ in range(2):
                _sample(restored, storage_power_active=-2000, smartmeter_power=2300)
                await _evaluate(restored)

        assert restored._timed_discharge_state == TimedDischargeState(
            EXPIRES + timedelta(days=1, hours=1)
        )
        assert restored.data["timed_charge_discharge_status"] == "grid_charging"
    finally:
        await restored.async_shutdown()


@pytest.mark.parametrize("changed_setting", ["month", "start", "end", "window"])
async def test_editing_schedule_keeps_original_confirmed_expiry(
    charge_system: tuple[SaxPowerCoordinator, MagicMock], changed_setting: str
) -> None:
    coordinator, _ = charge_system
    await _reach_target_with_pv(coordinator)
    if changed_setting == "month":
        await coordinator.async_set_timed_charge_month(9, False)
    elif changed_setting == "start":
        await coordinator.async_set_timed_charge_start(dt_time(3))
    elif changed_setting == "end":
        await coordinator.async_set_timed_charge_end(dt_time(6))
    else:
        await coordinator.async_set_timed_charge_window(dt_time(22), dt_time(6))

    assert coordinator._timed_discharge_state == TimedDischargeState(EXPIRES)
    assert coordinator.data["timed_charge_discharge_status"] == "discharge_blocked"
    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.now", return_value=EXPIRES
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=EXPIRES,
        ),
    ):
        _sample(coordinator, storage_power_active=0, smartmeter_power=400)
        await _evaluate(coordinator)

    assert coordinator._timed_discharge_state is None
    assert coordinator.sun_charge_active is False
    assert coordinator.data["timed_charge_discharge_status"] == "normal"
