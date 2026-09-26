"""Real Core storage failures must not confirm unsaved charging settings."""

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
from homeassistant.util import dt as dt_util
from homeassistant.util.file import WriteError
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.control_store import (
    CONTROL_SAVE_DELAY,
    ControlConfig,
    ControlConfigStore,
)


@pytest.fixture
def hass_storage() -> dict[str, object]:
    """Keep Core's actual file writes and reads for these regressions."""
    return {}


@pytest.fixture(autouse=True)
def isolated_storage(hass: HomeAssistant, tmp_path: Path) -> None:
    hass.config.config_dir = str(tmp_path)


async def _elapse_save_delay(hass: HomeAssistant) -> None:
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=CONTROL_SAVE_DELAY + 1)
    )
    await hass.async_block_till_done()


async def test_failed_delayed_write_retries_without_another_setting_change(
    hass: HomeAssistant,
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: transient disk failure cannot lose a limit."""
    store = ControlConfigStore(hass, "delayed-failure")
    await store.async_save(ControlConfig(max_soc=90))
    assert store.async_delay_save(ControlConfig(max_soc=65))

    with patch.object(
        store._store, "_write_prepared_data", side_effect=WriteError("disk full")
    ):
        await _elapse_save_delay(hass)

    saved = await ControlConfigStore(hass, "delayed-failure").async_load()
    assert saved.config is not None and saved.config.max_soc == 90
    assert store._last_persisted["max_soc"] == 90

    await _elapse_save_delay(hass)
    saved = await ControlConfigStore(hass, "delayed-failure").async_load()
    assert saved.config is not None and saved.config.max_soc == 65
    assert store.async_delay_save(ControlConfig(max_soc=65)) is False


@pytest.mark.parametrize("final_write_retry", [False, True])
async def test_failed_immediate_write_reports_failure_and_remains_retryable(
    hass: HomeAssistant, final_write_retry: bool
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: only a readable snapshot is confirmed."""
    store = ControlConfigStore(hass, "immediate-failure")
    await store.async_save(ControlConfig(max_soc=90))
    with (
        patch.object(
            store._store, "_write_prepared_data", side_effect=WriteError("disk full")
        ),
        pytest.raises(HomeAssistantError),
    ):
        await store.async_save(ControlConfig(max_soc=65))

    assert store._save_scheduled is False
    assert store._unsub_delayed_write is None
    assert store._unsub_final_write is not None
    if final_write_retry:
        hass.set_state(CoreState.final_write)
        hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
        await hass.async_block_till_done()
        hass.set_state(CoreState.running)
    else:
        assert store.async_delay_save(ControlConfig(max_soc=65))
        await _elapse_save_delay(hass)
    saved = await ControlConfigStore(hass, "immediate-failure").async_load()
    assert saved.config is not None and saved.config.max_soc == 65
    assert store._unsub_final_write is None


@pytest.mark.parametrize(
    ("phase", "fail_write"),
    [("write", False), ("write", True), ("readback", False)],
)
async def test_new_setting_during_io_is_the_final_persisted_snapshot(
    hass: HomeAssistant, phase: str, fail_write: bool
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: slow or failed I/O preserves newer settings."""
    store = ControlConfigStore(hass, "concurrent-setting")
    await store.async_save(ControlConfig(max_soc=90))
    entered = asyncio.Event()
    release = asyncio.Event()
    method = "_async_write_data" if phase == "write" else "async_load"
    original = getattr(store._store, method)

    async def delayed_io(*args: Any) -> Any:
        if not entered.is_set():
            entered.set()
            await release.wait()
            if fail_write:
                raise WriteError("disk temporarily unavailable")
        return await original(*args)

    with patch.object(store._store, method, side_effect=delayed_io):
        assert store.async_delay_save(ControlConfig(max_soc=65), delay=0)
        await asyncio.wait_for(entered.wait(), timeout=1)
        assert store.async_delay_save(ControlConfig(max_soc=70), delay=0)
        release.set()
        await hass.async_block_till_done()

    saved = await ControlConfigStore(hass, "concurrent-setting").async_load()
    assert saved.config is not None and saved.config.max_soc == 70
    assert store._last_persisted["max_soc"] == 70
    assert store._pending is None
    assert store.async_delay_save(ControlConfig(max_soc=70)) is False


@pytest.mark.parametrize("during_stop", [False, True])
async def test_final_write_flushes_settings_and_cleans_up_listeners(
    hass: HomeAssistant, during_stop: bool
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: shutdown preserves changes before the timer."""
    store = ControlConfigStore(hass, "shutdown-setting")
    await store.async_save(ControlConfig(max_soc=90))
    assert store.async_delay_save(ControlConfig(max_soc=65), delay=3600)
    if during_stop:
        hass.set_state(CoreState.stopping)
        await store.async_save(ControlConfig(max_soc=65))
        assert store._last_persisted["max_soc"] == 90

    hass.set_state(CoreState.final_write)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
    await hass.async_block_till_done()
    hass.set_state(CoreState.running)

    saved = await ControlConfigStore(hass, "shutdown-setting").async_load()
    assert saved.config is not None and saved.config.max_soc == 65
    assert store._pending is None
    assert store._save_scheduled is False
    assert store._unsub_delayed_write is None
    assert store._unsub_final_write is None


async def test_failed_initial_migration_is_retried_after_bootstrap(
    hass: HomeAssistant,
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: a failed initial save retries automatically."""
    coordinator = SaxPowerCoordinator(
        hass,
        MagicMock(),
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="bootstrap-failure",
    )
    await coordinator.async_load_control_state()
    await coordinator.async_set_max_soc(65)
    store = coordinator._control_store
    with patch.object(
        store._store, "_write_prepared_data", side_effect=WriteError("disk full")
    ):
        await coordinator.async_finish_bootstrap()

    assert store._last_persisted is None
    assert store._save_scheduled is True
    await _elapse_save_delay(hass)
    saved = await ControlConfigStore(hass, "bootstrap-failure").async_load()
    assert saved.config is not None and saved.config.max_soc == 65
    await coordinator.async_shutdown(reset_device=False)
    assert store._pending is None
    assert store._unsub_delayed_write is None
    assert store._unsub_final_write is None


async def test_failed_unload_cannot_overwrite_settings_after_a_reload(
    hass: HomeAssistant,
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: old owners cannot flush over newer settings."""
    entry_id = "failed-unload"
    await ControlConfigStore(hass, entry_id).async_save(ControlConfig(max_soc=90))
    coordinator = SaxPowerCoordinator(
        hass,
        MagicMock(),
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=entry_id,
    )
    await coordinator.async_load_control_state()
    await coordinator.async_finish_bootstrap()
    await coordinator.async_set_max_soc(65)
    old_store = coordinator._control_store
    with patch.object(
        old_store._store, "_write_prepared_data", side_effect=WriteError("disk full")
    ):
        await coordinator.async_shutdown(reset_device=False)

    assert old_store._unsub_delayed_write is None
    assert old_store._unsub_final_write is None
    new_store = ControlConfigStore(hass, entry_id)
    await new_store.async_save(ControlConfig(max_soc=70))
    hass.set_state(CoreState.final_write)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
    await hass.async_block_till_done()
    hass.set_state(CoreState.running)

    saved = await ControlConfigStore(hass, entry_id).async_load()
    assert saved.config is not None and saved.config.max_soc == 70


@pytest.mark.parametrize("final_save", [False, True])
async def test_failure_during_stop_keeps_the_final_write_retry(
    hass: HomeAssistant, final_save: bool
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: stopping during I/O keeps the final flush."""
    entry_id = "stopping-during-write"
    store = ControlConfigStore(hass, entry_id)
    await store.async_save(ControlConfig(max_soc=90))
    entered = asyncio.Event()
    release = asyncio.Event()
    original = store._store._async_write_data

    async def fail_first_write(*args: Any) -> Any:
        if not entered.is_set():
            entered.set()
            await release.wait()
            raise WriteError("disk temporarily unavailable")
        return await original(*args)

    with patch.object(store._store, "_async_write_data", side_effect=fail_first_write):
        write_task: asyncio.Task[None] | None = None
        if final_save:
            write_task = asyncio.create_task(
                store.async_save(ControlConfig(max_soc=65), final=True)
            )
        else:
            assert store.async_delay_save(ControlConfig(max_soc=65), delay=0)
        await asyncio.wait_for(entered.wait(), timeout=1)
        hass.set_state(CoreState.stopping)
        release.set()
        if write_task is not None:
            with pytest.raises(HomeAssistantError):
                await write_task
        await hass.async_block_till_done()
        assert store._unsub_delayed_write is None
        assert store._unsub_final_write is not None
        assert store._last_persisted["max_soc"] == 90

        hass.set_state(CoreState.final_write)
        hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
        await hass.async_block_till_done()
        hass.set_state(CoreState.running)

    saved = await ControlConfigStore(hass, entry_id).async_load()
    assert saved.config is not None and saved.config.max_soc == 65
    assert store._unsub_delayed_write is None
    assert store._unsub_final_write is None
