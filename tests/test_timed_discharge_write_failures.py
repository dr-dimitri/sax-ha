"""REQ-TIMED-SOC-CHARGE: only readable protection snapshots are persisted."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import EVENT_HOMEASSISTANT_FINAL_WRITE
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.file import WriteError

from custom_components.sax_power.application.timed_discharge import TimedDischargeState
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.timed_discharge_store import (
    TimedDischargeStateStore,
)

from .test_timed_discharge_coordinator import (
    EXPIRES,
    _confirm_grid_charge,
    _evaluate,
    _make_coordinator,
    _reach_target_with_pv,
)
from .test_timed_discharge_coordinator import charge_system as charge_system


@pytest.fixture
def hass_storage() -> dict[str, object]:
    """Exercise Core's real file writes and readbacks."""
    return {}


@pytest.fixture(autouse=True)
def isolated_storage(hass: HomeAssistant, tmp_path: Path) -> None:
    hass.config.config_dir = str(tmp_path)


@pytest.mark.parametrize("released", [False, True])
async def test_core_write_error_retains_active_and_inactive_snapshot_for_retry(
    hass: HomeAssistant, released: bool
) -> None:
    """Issue #267: a swallowed disk error confirms neither save nor removal."""
    store = TimedDischargeStateStore(hass, "disk-failure")
    previous = TimedDischargeState(EXPIRES - timedelta(hours=1))
    target = None if released else TimedDischargeState(EXPIRES)
    await store.async_save(previous)

    with (
        patch.object(
            store._store,
            "_write_prepared_data",
            side_effect=WriteError("disk temporarily full"),
        ),
        pytest.raises(HomeAssistantError),
    ):
        await store.async_save(target)

    assert store.save_pending
    assert await TimedDischargeStateStore(hass, "disk-failure").async_load() == previous
    await store.async_save(target)
    assert not store.save_pending
    assert await TimedDischargeStateStore(hass, "disk-failure").async_load() == target
    with patch.object(
        store._store, "async_save", wraps=store._store.async_save
    ) as save:
        await store.async_save(target)
        save.assert_not_awaited()


@pytest.mark.parametrize("phase", ["write", "readback"])
@pytest.mark.parametrize("first_write_fails", [False, True])
async def test_new_state_during_io_is_the_final_persisted_snapshot(
    hass: HomeAssistant, phase: str, first_write_fails: bool
) -> None:
    """Issue #267: slow or failed older writes cannot consume a newer release."""
    store = TimedDischargeStateStore(hass, "concurrent")
    entered = asyncio.Event()
    release = asyncio.Event()
    method = "_async_write_data" if phase == "write" else "async_load"
    original = getattr(store._store, method)

    async def delayed_io(*args: Any) -> Any:
        if not entered.is_set():
            entered.set()
            await release.wait()
            if first_write_fails:
                if phase == "write":
                    raise WriteError("disk temporarily unavailable")
                raise HomeAssistantError("readback temporarily unavailable")
        return await original(*args)

    with patch.object(store._store, method, side_effect=delayed_io):
        old_write = asyncio.create_task(store.async_save(TimedDischargeState(EXPIRES)))
        await asyncio.wait_for(entered.wait(), timeout=1)
        latest_write = asyncio.create_task(store.async_save(None))
        await asyncio.sleep(0)
        release.set()
        if first_write_fails:
            with pytest.raises(HomeAssistantError):
                await old_write
        else:
            await old_write
        await latest_write

    assert not store.save_pending
    assert await TimedDischargeStateStore(hass, "concurrent").async_load() is None
    assert await store._store.async_load() == {"active": False}


@pytest.mark.parametrize("released", [False, True])
async def test_stopping_defers_confirmation_until_final_disk_write(
    hass: HomeAssistant, released: bool
) -> None:
    """REQ-TIMED-SOC-CHARGE: a stopping-time readback must not confirm RAM."""
    store = TimedDischargeStateStore(hass, "final-write")
    previous = TimedDischargeState(EXPIRES - timedelta(hours=1))
    target = None if released else TimedDischargeState(EXPIRES)
    await store.async_save(previous)
    hass.set_state(CoreState.stopping)
    try:
        await store.async_save(target)
        assert store.save_pending
        assert store._unsub_final_write is not None
        assert (
            await TimedDischargeStateStore(hass, "final-write").async_load() == previous
        )
        hass.set_state(CoreState.final_write)
        hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
        await hass.async_block_till_done()
        assert not store.save_pending
        assert store._unsub_final_write is None
        assert (
            await TimedDischargeStateStore(hass, "final-write").async_load() == target
        )
    finally:
        hass.set_state(CoreState.running)


async def test_stop_during_write_retains_final_write_retry(hass: HomeAssistant) -> None:
    """REQ-TIMED-SOC-CHARGE: stopping during a failed write retains its proof."""
    store = TimedDischargeStateStore(hass, "stop-during-write")
    entered = asyncio.Event()
    release = asyncio.Event()

    async def failed_io(*_args: Any) -> None:
        entered.set()
        await release.wait()
        raise WriteError("disk temporarily unavailable")

    try:
        with patch.object(store._store, "_async_write_data", side_effect=failed_io):
            task = asyncio.create_task(store.async_save(TimedDischargeState(EXPIRES)))
            await asyncio.wait_for(entered.wait(), timeout=1)
            hass.set_state(CoreState.stopping)
            release.set()
            await task
        assert store.save_pending
        assert store._unsub_final_write is not None
        hass.set_state(CoreState.final_write)
        hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
        await hass.async_block_till_done()
        assert await store.async_load() == TimedDischargeState(EXPIRES)
        assert not store.save_pending
        assert store._unsub_final_write is None
    finally:
        hass.set_state(CoreState.running)


@pytest.mark.parametrize("released", [False, True])
async def test_unchanged_control_cycle_retries_failed_protection_storage(
    hass: HomeAssistant,
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
    released: bool,
) -> None:
    """Issue #267: unchanged polls retry both confirmed and revoked protection."""
    coordinator, _client = charge_system
    store = coordinator._timed_discharge_store
    if released:
        await _reach_target_with_pv(coordinator)
    with patch.object(
        store._store,
        "_write_prepared_data",
        side_effect=WriteError("disk temporarily full"),
    ):
        if released:
            await coordinator.async_set_timed_charge_enabled(False)
        else:
            await _confirm_grid_charge(coordinator)

    assert store.save_pending
    await _evaluate(coordinator)
    assert not store.save_pending
    expected = None if released else TimedDischargeState(EXPIRES)
    assert await TimedDischargeStateStore(hass, coordinator.entry_id).async_load() == (
        expected
    )


@pytest.mark.parametrize("released", [False, True])
async def test_clean_reload_flushes_failed_latest_protection_state(
    hass: HomeAssistant,
    charge_system: tuple[SaxPowerCoordinator, MagicMock],
    released: bool,
) -> None:
    """Issue #267: reload keeps a confirmed hold or its most recent release."""
    coordinator, client = charge_system
    store = coordinator._timed_discharge_store
    if released:
        await _reach_target_with_pv(coordinator)
    with patch.object(
        store._store,
        "_write_prepared_data",
        side_effect=WriteError("disk temporarily full"),
    ):
        if released:
            await coordinator.async_set_timed_charge_enabled(False)
        else:
            await _confirm_grid_charge(coordinator)
    assert store.save_pending

    await coordinator.async_shutdown()
    assert not store.save_pending
    assert store._unsub_final_write is None
    replacement = _make_coordinator(hass, client)
    replacement._timed_charge_enabled = True
    await replacement.async_load_timed_discharge_state()
    replacement.data["soc"] = 60
    try:
        await _evaluate(replacement)
        assert replacement.sun_charge_active is not released
    finally:
        await replacement.async_shutdown()


async def test_software_ack_and_latest_state_survive_slow_protection_storage(
    hass: HomeAssistant, charge_system: tuple[SaxPowerCoordinator, MagicMock]
) -> None:
    """REQ-VUE-ENTITY-BINDING: a store write cannot delay accepted switches."""
    coordinator, _client = charge_system
    await _reach_target_with_pv(coordinator)
    store = coordinator._timed_discharge_store
    entered = asyncio.Event()
    release = asyncio.Event()
    original = store._store._async_write_data

    async def delayed_io(*args: Any) -> Any:
        if not entered.is_set():
            entered.set()
            await release.wait()
        return await original(*args)

    with patch.object(store._store, "_async_write_data", side_effect=delayed_io):
        await asyncio.wait_for(
            coordinator.async_set_timed_charge_enabled(False, defer_device_update=True),
            timeout=0.2,
        )
        task = coordinator._month_control_task
        try:
            await asyncio.wait_for(entered.wait(), timeout=1)
            await asyncio.wait_for(
                coordinator.async_set_timed_charge_enabled(
                    True, defer_device_update=True
                ),
                timeout=0.2,
            )
            assert coordinator.timed_charge_enabled
        finally:
            release.set()
        await task

    assert coordinator._timed_discharge_state is None
    assert not store.save_pending
    assert (
        await TimedDischargeStateStore(hass, coordinator.entry_id).async_load() is None
    )


async def test_failed_old_shutdown_cannot_overwrite_reloaded_owner(
    hass: HomeAssistant, charge_system: tuple[SaxPowerCoordinator, MagicMock]
) -> None:
    """REQ-SETUP-ROLLBACK: retired protection owners cannot flush after reload."""
    coordinator, _client = charge_system
    await _reach_target_with_pv(coordinator)
    old_store = coordinator._timed_discharge_store
    with patch.object(
        old_store._store,
        "_write_prepared_data",
        side_effect=WriteError("disk temporarily full"),
    ):
        await coordinator.async_set_timed_charge_enabled(False)
        await coordinator.async_shutdown()

    assert old_store.save_pending
    assert old_store._unsub_final_write is None
    new_state = TimedDischargeState(EXPIRES + timedelta(hours=1))
    await TimedDischargeStateStore(hass, coordinator.entry_id).async_save(new_state)
    hass.set_state(CoreState.final_write)
    try:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
        await hass.async_block_till_done()
        assert await TimedDischargeStateStore(
            hass, coordinator.entry_id
        ).async_load() == (new_state)
    finally:
        hass.set_state(CoreState.running)
