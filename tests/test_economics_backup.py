"""REQ-ECONOMICS-OBSERVABILITY: one rolling backup and automatic recovery."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.sax_power.infrastructure.economics_store import (
    ECONOMICS_BACKUP_INTERVAL,
    EconomicsState,
    EconomicsStateStore,
)


@pytest.fixture
def hass_storage() -> dict:
    """Exercise actual atomic JSON writes rather than the default memory fixture."""
    return {}


@pytest.fixture
async def store(
    hass: HomeAssistant, request: pytest.FixtureRequest
) -> AsyncGenerator[EconomicsStateStore]:
    name = request.node.name.replace("[", "-").replace("]", "")
    instance = EconomicsStateStore(hass, f"backup-{name}")
    yield instance
    await instance.async_stop_backup()
    instance._cancel_delayed_write()
    for storage in (instance._store, instance._backup_store):
        path = Path(storage.path)
        path.unlink(missing_ok=True)
        for quarantined in path.parent.glob(f"{path.name}.corrupt.*"):
            quarantined.unlink()


@pytest.fixture
def state() -> EconomicsState:
    return EconomicsState(
        grid_charge_cost_eur=10.0,
        pv_opportunity_cost_eur=2.0,
        avoided_grid_cost_eur=40.0,
        operating_result_high_water_eur=28.0,
        unvalued_inventory_kwh=3.0,
        unpriced_charge_kwh=1.0,
        unpriced_discharge_kwh=0.5,
        priced_charge_kwh=20.0,
        priced_discharge_kwh=30.0,
        economics_started_at=dt_util.utcnow() - timedelta(days=2),
    )


async def _backup(store: EconomicsStateStore, state: EconomicsState) -> None:
    async with store._write_lock:
        assert await store._async_write_backup(state)


def _payload(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["data"]


async def test_backup_runs_every_ten_minutes_and_replaces_one_file(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    store: EconomicsStateStore,
    state: EconomicsState,
) -> None:
    """600-second cadence remains independent of charge/discharge activity."""
    now = dt_util.utcnow()
    assert await store.async_save(state)
    store.async_start_backup()
    timer = store._unsub_backup_timer
    store.async_start_backup()
    assert store._unsub_backup_timer is timer
    path = Path(store._backup_store.path)
    freezer.move_to(now + timedelta(seconds=599))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert not path.exists()

    freezer.move_to(now + timedelta(seconds=601))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    first = _payload(store._backup_store.path)
    assert first["grid_charge_cost_eur"] == 10.0
    assert store.backup_last_saved_at is not None

    assert await store.async_save(replace(state, grid_charge_cost_eur=12.0))
    freezer.move_to(now + timedelta(seconds=1200))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert _payload(store._backup_store.path) == first
    freezer.move_to(now + timedelta(seconds=1202))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert _payload(store._backup_store.path)["grid_charge_cost_eur"] == 12.0
    assert list(path.parent.glob(f"{path.name}*")) == [path]
    assert ECONOMICS_BACKUP_INTERVAL == 600


@pytest.mark.parametrize("damage", ["missing", "json", "field", "version"])
async def test_backup_restores_all_values_and_repairs_the_main_file(
    hass: HomeAssistant, store: EconomicsStateStore, state: EconomicsState, damage: str
) -> None:
    """Readable backup wins over missing, quarantined or semantically bad data."""
    assert await store.async_save(state)
    await _backup(store, state)
    backup_path = Path(store._backup_store.path)
    unchanged_backup = backup_path.read_text(encoding="utf-8")
    path = Path(store._store.path)
    if damage == "missing":
        path.unlink()
    elif damage == "json":
        path.write_text("{defekt", encoding="utf-8")
    else:
        damaged = json.loads(path.read_text(encoding="utf-8"))
        if damage == "field":
            damaged["data"]["grid_charge_cost_eur"] = "kaputt"
        else:
            damaged["version"] = 999
        path.write_text(json.dumps(damaged), encoding="utf-8")

    loaded = await store.async_load()
    assert loaded == state
    assert store.backup_restored_at is not None
    assert backup_path.read_text(encoding="utf-8") == unchanged_backup
    assert (
        await EconomicsStateStore(
            hass, store._store.key.removeprefix("sax_power.economics.")
        ).async_load()
        == state
    )
    if damage != "missing":
        assert len(list(path.parent.glob(f"{path.name}.corrupt.*"))) == 1


async def test_healthy_primary_has_priority_over_older_backup(
    store: EconomicsStateStore, state: EconomicsState
) -> None:
    await _backup(store, state)
    newer = replace(state, grid_charge_cost_eur=12.0)
    assert await store.async_save(newer)
    assert await store.async_load() == newer
    assert store.backup_restored_at is None


async def test_failed_main_write_never_reaches_the_backup(
    store: EconomicsStateStore, state: EconomicsState
) -> None:
    """Pending or silently rejected primary writes must not replace good data."""
    assert await store.async_save(state)
    store._store.async_save = AsyncMock()
    assert not await store.async_save(replace(state, grid_charge_cost_eur=15.0))
    await _backup(store, store._last_persisted)
    assert _payload(store._backup_store.path)["grid_charge_cost_eur"] == 10.0
    assert not await store._async_write_backup(
        replace(state, grid_charge_cost_eur=float("nan"))
    )
    assert _payload(store._backup_store.path)["grid_charge_cost_eur"] == 10.0


async def test_failed_backup_keeps_previous_copy_and_retries_on_next_tick(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    store: EconomicsStateStore,
    state: EconomicsState,
) -> None:
    assert await store.async_save(state)
    await _backup(store, state)
    path = Path(store._backup_store.path)
    original = path.read_text(encoding="utf-8")
    original_save = store._backup_store.async_save
    store._backup_store.async_save = AsyncMock()
    assert await store.async_save(replace(state, grid_charge_cost_eur=15.0))
    now = dt_util.utcnow()
    store.async_start_backup()
    freezer.move_to(now + timedelta(seconds=601))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert path.read_text(encoding="utf-8") == original
    assert store._unsub_backup_timer is not None
    store._backup_store.async_save = original_save
    freezer.move_to(now + timedelta(seconds=1202))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert _payload(store._backup_store.path)["grid_charge_cost_eur"] == 15.0


async def test_invalid_backup_allows_normal_fresh_start(
    store: EconomicsStateStore,
) -> None:
    path = Path(store._backup_store.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{kaputtes Backup", encoding="utf-8")
    assert await store.async_load() is None
    assert store.backup_restored_at is None


async def test_recovery_read_survives_failed_main_repair(
    store: EconomicsStateStore, state: EconomicsState
) -> None:
    """Backup continues in memory even when the damaged primary is unwritable."""
    await _backup(store, state)
    store._store.async_save = AsyncMock(side_effect=OSError("Platte voll"))
    assert await store.async_load() == state
    assert store._last_persisted == state
    assert _payload(store._backup_store.path)["grid_charge_cost_eur"] == 10.0


async def test_reset_replaces_backup_without_resurrecting_the_old_balance(
    store: EconomicsStateStore, state: EconomicsState
) -> None:
    assert await store.async_save(state)
    await _backup(store, state)
    reset = replace(
        state,
        economics_started_at=dt_util.utcnow(),
        grid_charge_cost_eur=0.0,
        pv_opportunity_cost_eur=0.0,
        avoided_grid_cost_eur=0.0,
        operating_result_high_water_eur=0.0,
        priced_charge_kwh=0.0,
        priced_discharge_kwh=0.0,
        unpriced_charge_kwh=0.0,
        unpriced_discharge_kwh=0.0,
        unvalued_inventory_kwh=0.0,
    )
    assert await store.async_reset(reset)
    Path(store._store.path).unlink()
    assert await store.async_load() == reset


async def test_failed_reset_keeps_the_old_balance_recoverable(
    store: EconomicsStateStore, state: EconomicsState
) -> None:
    assert await store.async_save(state)
    await _backup(store, state)
    store._store.async_save = AsyncMock(side_effect=OSError("Fehler"))
    assert not await store.async_reset(replace(state, grid_charge_cost_eur=0.0))
    assert store._deserialize(_payload(store._backup_store.path)) == state


async def test_backup_shutdown_waits_for_io_and_never_restarts_the_timer(
    store: EconomicsStateStore, state: EconomicsState
) -> None:
    assert await store.async_save(state)
    entered, release = asyncio.Event(), asyncio.Event()
    save = store._backup_store.async_save

    async def paused(data: dict) -> None:
        entered.set()
        await release.wait()
        await save(data)

    store._backup_store.async_save = paused
    store.async_start_backup()
    store._unsub_backup_timer()
    writing = asyncio.create_task(store._async_backup_tick(dt_util.utcnow()))
    await entered.wait()
    stopping = asyncio.create_task(store.async_stop_backup())
    await asyncio.sleep(0)
    assert not stopping.done()
    release.set()
    await asyncio.gather(writing, stopping)
    assert store._unsub_backup_timer is None
    assert store._unsub_backup_final_write is None


async def test_reset_backup_io_keeps_old_polls_valid_and_supersedes_their_writes(
    store: EconomicsStateStore, state: EconomicsState
) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: Backup-I/O darf keine Fehlersperre auslösen."""
    assert await store.async_save(state)
    await _backup(store, state)
    entered, release = asyncio.Event(), asyncio.Event()
    save = store._backup_store.async_save

    async def paused(data: dict) -> None:
        entered.set()
        await release.wait()
        await save(data)

    store._backup_store.async_save = paused
    reset = replace(state, economics_started_at=dt_util.utcnow())
    resetting = asyncio.create_task(store.async_reset(reset))
    await entered.wait()
    advanced_old = replace(state, grid_charge_cost_eur=12.0)
    assert store.async_delay_save(advanced_old)
    waiting_old = asyncio.create_task(store.async_save(advanced_old))
    await asyncio.sleep(0)
    release.set()
    assert await resetting
    assert await waiting_old
    assert store._pending is None
    assert await store.async_load() == reset
    assert store._deserialize(_payload(store._backup_store.path)) == reset


async def test_reset_cannot_proceed_when_old_backup_cannot_be_retired(
    store: EconomicsStateStore, state: EconomicsState
) -> None:
    assert await store.async_save(state)
    await _backup(store, state)
    store._backup_store.async_remove = AsyncMock(side_effect=OSError("Fehler"))
    assert not await store.async_reset(
        replace(state, economics_started_at=dt_util.utcnow())
    )
    assert await store.async_load() == state
    assert store._deserialize(_payload(store._backup_store.path)) == state
