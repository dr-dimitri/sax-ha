"""REQ-TIMED-SOC-CHARGE: retain an unfinished charge across a real store restore."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.file import WriteError

from custom_components.sax_power.application.timed_charge import TimedChargeState
from custom_components.sax_power.application.timed_discharge import TimedDischargeState
from custom_components.sax_power.const import (
    REG_SUN_IC_CONTROL_MODE,
    SUN_IC_CONTROL_MODE_SETPOINT,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.control_store import (
    ControlConfig,
    ControlConfigStore,
)
from custom_components.sax_power.infrastructure.timed_charge_store import (
    TimedChargeStateStore,
)
from custom_components.sax_power.infrastructure.timed_discharge_store import (
    TimedDischargeStateStore,
)

BERLIN = ZoneInfo("Europe/Berlin")
NOW = datetime(2026, 9, 5, 2, tzinfo=BERLIN)
ENTRY_ID = "timed_charge_restore"
STATE = TimedChargeState(dt_time(23), dt_time(6), datetime(2026, 9, 5, 4, tzinfo=UTC))


@contextmanager
def _at(moment: datetime) -> Iterator[None]:
    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.now", return_value=moment
        ),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow",
            return_value=moment.astimezone(UTC),
        ),
    ):
        yield


def _coordinator(hass: HomeAssistant, *, soc: object = 55) -> SaxPowerCoordinator:
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
        entry_id=ENTRY_ID,
    )
    coordinator.data = {
        "soc": soc,
        "smartmeter_power": 0,
        "storage_power_active": 0,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    return coordinator


async def _save_config(hass: HomeAssistant, **overrides: object) -> None:
    values = {
        "max_soc": 100,
        "timed_charge_enabled": True,
        "timed_charge_start": dt_time(23),
        "timed_charge_end": dt_time(6),
        "timed_charge_min_soc": 20,
        "timed_charge_max_soc": 80,
    }
    values.update(overrides)
    await ControlConfigStore(hass, ENTRY_ID).async_save(
        ControlConfig(**values).sanitized()
    )


async def _load(coordinator: SaxPowerCoordinator) -> None:
    await coordinator.async_load_control_state()
    await coordinator.async_load_timed_charge_state()
    await coordinator.async_load_timed_discharge_state()


async def test_restart_resumes_same_overnight_window_and_stops_at_own_target(
    hass: HomeAssistant,
) -> None:
    """A new coordinator resumes 18 -> 55 -> 80 percent through the real bootstrap."""
    await _save_config(hass)
    original = _coordinator(hass, soc=18)
    restored = _coordinator(hass)
    try:
        with _at(NOW - timedelta(hours=3)):
            await _load(original)
            await original.async_finish_bootstrap()
            assert original._timed_charge_active
            assert await TimedChargeStateStore(hass, ENTRY_ID).async_load() == STATE

        with _at(NOW):
            original.data["soc"] = 55
            await original._async_enforce_grid_charge(original.data)
            await original.async_shutdown()
            assert await TimedChargeStateStore(hass, ENTRY_ID).async_load() == STATE

            await _load(restored)
            assert not restored._timed_charge_armed
            restored.client.write_register.assert_not_awaited()
            await restored.async_finish_bootstrap()

            assert restored._timed_charge_armed
            assert restored._timed_charge_active
            assert restored._sun_charge_power < 0
            restored.client.write_register.assert_any_await(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SETPOINT,
                device_id=100,
            )
            assert restored._timed_discharge_state is None

            restored.data["soc"] = 80
            await restored._async_enforce_grid_charge(restored.data)
            assert not restored._timed_charge_armed
            assert not restored._timed_charge_active
            assert await TimedChargeStateStore(hass, ENTRY_ID).async_load() is None
            restored.data["soc"] = 55
            await restored._async_enforce_grid_charge(restored.data)
            assert not restored._timed_charge_active
    finally:
        await original.async_shutdown()
        await restored.async_shutdown()


@pytest.mark.parametrize(
    ("moment", "overrides"),
    [
        (NOW.replace(hour=6), {}),
        (NOW + timedelta(days=1), {}),
        (NOW - timedelta(days=1), {}),
        (NOW, {"timed_charge_enabled": False}),
        (NOW, {"timed_charge_months": frozenset({1})}),
        (NOW, {"timed_charge_start": dt_time(22)}),
        (NOW, {"timed_charge_end": dt_time(7)}),
        (NOW, {"timed_charge_start": None}),
        (NOW, {"timed_charge_enabled": False, "price_charge_enabled": True}),
    ],
)
async def test_restore_rejects_other_or_inactive_window(
    hass: HomeAssistant, moment: datetime, overrides: dict[str, object]
) -> None:
    """Only the identical enabled occurrence may inherit its old threshold crossing."""
    await _save_config(hass, **overrides)
    await TimedChargeStateStore(hass, ENTRY_ID).async_save(STATE)
    restored = _coordinator(hass)
    try:
        with _at(moment):
            await _load(restored)
            await restored.async_finish_bootstrap()
            assert not restored._timed_charge_armed
            assert not restored._timed_charge_active
            assert await TimedChargeStateStore(hass, ENTRY_ID).async_load() is None
    finally:
        await restored.async_shutdown()


@pytest.mark.parametrize("soc", [80, 100, None, float("nan"), True])
async def test_restore_never_charges_at_target_or_without_valid_soc(
    hass: HomeAssistant, soc: object
) -> None:
    await _save_config(hass)
    await TimedChargeStateStore(hass, ENTRY_ID).async_save(STATE)
    restored = _coordinator(hass, soc=soc)
    try:
        with _at(NOW):
            await _load(restored)
            await restored.async_finish_bootstrap()
            assert not restored._timed_charge_armed
            assert not restored._timed_charge_active
    finally:
        await restored.async_shutdown()


async def test_restore_waits_for_valid_soc_and_checks_window_again(
    hass: HomeAssistant,
) -> None:
    """A missing first SOC must neither lose the latch nor restore it after expiry."""
    await _save_config(hass)
    await TimedChargeStateStore(hass, ENTRY_ID).async_save(STATE)
    restored = _coordinator(hass, soc=None)
    try:
        with _at(NOW):
            await _load(restored)
            await restored.async_finish_bootstrap()
            assert restored._timed_charge_restore_state == STATE
        with _at(NOW.replace(hour=6)):
            restored.data["soc"] = 55
            await restored._async_enforce_grid_charge(restored.data)
            assert not restored._timed_charge_armed
            assert not restored._timed_charge_active
            assert restored._timed_charge_restore_state is None
    finally:
        await restored.async_shutdown()


@pytest.mark.parametrize("basic_failed", [False, True])
async def test_restore_resumes_after_a_valid_soc_arrives_in_same_window(
    hass: HomeAssistant, basic_failed: bool
) -> None:
    await _save_config(hass)
    await TimedChargeStateStore(hass, ENTRY_ID).async_save(STATE)
    restored = _coordinator(hass, soc=55 if basic_failed else None)
    restored._basic_read_failed = basic_failed
    try:
        with _at(NOW):
            await _load(restored)
            await restored.async_finish_bootstrap()
            assert not restored._timed_charge_active
            assert restored._timed_charge_restore_state == STATE
            restored.data["soc"] = 55
            restored._basic_read_failed = False
            await restored._async_enforce_grid_charge(restored.data)
            assert restored._timed_charge_active
    finally:
        await restored.async_shutdown()


@pytest.mark.parametrize("failure", [False, True])
async def test_missing_or_unreadable_store_never_invents_prior_charge(
    hass: HomeAssistant, failure: bool
) -> None:
    await _save_config(hass)
    restored = _coordinator(hass)
    if failure:
        restored._timed_charge_store._store.async_load = AsyncMock(
            side_effect=HomeAssistantError("unreadable")
        )
    try:
        with _at(NOW):
            await _load(restored)
            await restored.async_finish_bootstrap()
            assert not restored._timed_charge_armed
            assert not restored._timed_charge_active
    finally:
        await restored.async_shutdown()


async def test_latch_persists_during_pv_pause_without_inventing_discharge_proof(
    hass: HomeAssistant,
) -> None:
    await _save_config(hass)
    await TimedChargeStateStore(hass, ENTRY_ID).async_save(STATE)
    restored = _coordinator(hass)
    restored.data["smartmeter_power"] = -1000
    restored._timed_charge_pv_surplus_cycles = 100
    try:
        with _at(NOW):
            await _load(restored)
            await restored.async_finish_bootstrap()
            assert restored._timed_charge_armed
            assert not restored._timed_charge_active
            assert restored._timed_discharge_state is None
            assert await TimedChargeStateStore(hass, ENTRY_ID).async_load() == STATE
    finally:
        await restored.async_shutdown()


async def test_persistence_changes_only_on_edges_and_retries_failed_save(
    hass: HomeAssistant,
) -> None:
    await _save_config(hass)
    original = _coordinator(hass, soc=18)
    save = AsyncMock(side_effect=[OSError("disk"), None, None])
    original._timed_charge_store.async_save = save
    try:
        with _at(NOW):
            await _load(original)
            await original.async_finish_bootstrap()
            assert original._timed_charge_active
            assert original._timed_charge_persisted_state is None
            await original._async_enforce_grid_charge(original.data)
            assert save.await_count == 2
            assert original._timed_charge_persisted_state == STATE
            await original._async_enforce_grid_charge(original.data)
            assert save.await_count == 2
            await original.async_set_timed_charge_enabled(False)
            assert save.await_count == 3
            save.assert_awaited_with(None)
    finally:
        await original.async_shutdown()


async def test_core_swallowed_write_error_is_detected_and_retried(
    hass: HomeAssistant,
) -> None:
    """Run through Core's actual WriteError handler, not a mocked async_save error."""
    await _save_config(hass)
    original = _coordinator(hass, soc=18)
    try:
        with _at(NOW):
            await _load(original)
            with patch.object(
                original._timed_charge_store._store,
                "_async_write_data",
                side_effect=WriteError("disk full"),
            ):
                await original.async_finish_bootstrap()
            assert original._timed_charge_active
            assert original._timed_charge_persisted_state is None
            assert await TimedChargeStateStore(hass, ENTRY_ID).async_load() is None
            await original._async_enforce_grid_charge(original.data)
            assert original._timed_charge_persisted_state == STATE
            assert await TimedChargeStateStore(hass, ENTRY_ID).async_load() == STATE
    finally:
        await original.async_shutdown()


async def test_failed_release_still_stops_device_and_retries_persistence(
    hass: HomeAssistant,
) -> None:
    await _save_config(hass)
    original = _coordinator(hass, soc=18)
    try:
        with _at(NOW):
            await _load(original)
            await original.async_finish_bootstrap()
            original.data["soc"] = 80
            with patch.object(
                original._timed_charge_store._store,
                "_async_write_data",
                side_effect=WriteError("disk full"),
            ):
                await original._async_enforce_grid_charge(original.data)
            assert not original._timed_charge_armed
            assert not original._timed_charge_active
            assert not original.sun_charge_active
            assert original._timed_charge_persisted_state == STATE
            await original._async_enforce_grid_charge(original.data)
            assert original._timed_charge_persisted_state is None
            assert await TimedChargeStateStore(hass, ENTRY_ID).async_load() is None
    finally:
        await original.async_shutdown()


@pytest.mark.parametrize(
    ("moment", "end", "expiry"),
    [
        (
            datetime(2026, 3, 29, 3, 15, tzinfo=BERLIN),
            dt_time(6),
            datetime(2026, 3, 29, 4, tzinfo=UTC),
        ),
        (
            datetime(2026, 10, 25, 2, 15, tzinfo=BERLIN, fold=1),
            dt_time(6),
            datetime(2026, 10, 25, 5, tzinfo=UTC),
        ),
    ],
)
async def test_restore_keeps_absolute_window_identity_across_dst(
    hass: HomeAssistant, moment: datetime, end: dt_time, expiry: datetime
) -> None:
    await _save_config(hass, timed_charge_end=end)
    await TimedChargeStateStore(hass, ENTRY_ID).async_save(
        TimedChargeState(dt_time(23), end, expiry)
    )
    restored = _coordinator(hass)
    try:
        with _at(moment):
            await _load(restored)
            await restored.async_finish_bootstrap()
            assert restored._timed_charge_active
    finally:
        await restored.async_shutdown()


@pytest.mark.parametrize(
    ("moment", "expiry"),
    [
        (
            datetime(2026, 3, 29, 3, tzinfo=BERLIN),
            datetime(2026, 3, 29, 1, tzinfo=UTC),
        ),
        (
            datetime(2026, 10, 25, 2, 15, tzinfo=BERLIN, fold=1),
            datetime(2026, 10, 25, 0, 30, tzinfo=UTC),
        ),
    ],
)
async def test_restore_does_not_reopen_dst_window_after_its_original_expiry(
    hass: HomeAssistant, moment: datetime, expiry: datetime
) -> None:
    await _save_config(hass, timed_charge_end=dt_time(2, 30))
    await TimedChargeStateStore(hass, ENTRY_ID).async_save(
        TimedChargeState(dt_time(23), dt_time(2, 30), expiry)
    )
    restored = _coordinator(hass)
    try:
        with _at(moment):
            await _load(restored)
            await restored.async_finish_bootstrap()
            assert not restored._timed_charge_armed
            assert not restored._timed_charge_active
    finally:
        await restored.async_shutdown()


async def test_completed_discharge_window_suppresses_restore_after_extension(
    hass: HomeAssistant,
) -> None:
    """REQ-TIMED-SOC-CHARGE: the original confirmed end remains authoritative."""
    await _save_config(hass, timed_charge_end=dt_time(7))
    await TimedChargeStateStore(hass, ENTRY_ID).async_save(
        TimedChargeState(dt_time(23), dt_time(7), STATE.expires_at + timedelta(hours=1))
    )
    await TimedDischargeStateStore(hass, ENTRY_ID).async_save(
        TimedDischargeState(STATE.expires_at)
    )
    restored = _coordinator(hass)
    try:
        with _at(NOW.replace(hour=6, minute=10)):
            await _load(restored)
            await restored.async_finish_bootstrap()
            assert not restored._timed_charge_armed
            assert not restored._timed_charge_active
    finally:
        await restored.async_shutdown()
