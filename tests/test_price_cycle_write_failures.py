"""REQ-DYNAMIC-PRICE-CHARGE: failed disk writes cannot refill charge budgets."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
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

from custom_components.sax_power.const import PRICE_STRATEGY_RELATIVE
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.price_plan_store import (
    PRICE_PLAN_SAVE_DELAY,
    PricePlanCycleState,
    PricePlanCycleStore,
    PricePlanInterval,
)
from custom_components.sax_power.price_optimizer import PriceChargeContext, PriceSlot

NOW = datetime(2026, 9, 14, 12, tzinfo=UTC)


@pytest.fixture
def hass_storage() -> dict[str, object]:
    """Use Core's actual disk I/O, including its swallowed WriteError."""
    return {}


@pytest.fixture(autouse=True)
def isolated_storage(hass: HomeAssistant, tmp_path: Path) -> None:
    hass.config.config_dir = str(tmp_path)


def _cycle(hours: int = 3) -> PricePlanCycleState:
    return PricePlanCycleState(
        anchor=NOW,
        end=NOW + timedelta(hours=24),
        strategy=PRICE_STRATEGY_RELATIVE,
        budget_seconds=hours * 3600,
        intervals=(PricePlanInterval(NOW, NOW + timedelta(hours=hours)),),
    )


async def _elapse_save_delay(hass: HomeAssistant) -> None:
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=PRICE_PLAN_SAVE_DELAY + 1)
    )
    await hass.async_block_till_done()


async def test_failed_initial_cycle_write_retries_without_replanning(
    hass: HomeAssistant,
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: recovered storage preserves consumed time."""
    coordinator = SaxPowerCoordinator(hass, MagicMock(), 64, 100, 10, "cycle-retry")
    planner = coordinator.price_planner
    await planner.async_load_cycle_state()
    context = PriceChargeContext(
        enabled=True,
        strategy=PRICE_STRATEGY_RELATIVE,
        max_price=0.3,
        hours=3,
        target_soc=90,
        current_soc=10,
        capacity_kwh=10,
        charge_power_w=1000,
        pv_forecast_kwh=None,
        pv_factor=0,
    )
    slots = [
        PriceSlot(
            NOW + timedelta(hours=index),
            NOW + timedelta(hours=index + 1),
            0.1 + index / 100,
        )
        for index in range(8)
    ]
    planner._compute_budgeted_plan(NOW, slots, context)
    store = planner._cycle_store
    with patch.object(
        store._store, "_write_prepared_data", side_effect=WriteError("disk full")
    ):
        await _elapse_save_delay(hass)

    assert await PricePlanCycleStore(hass, coordinator.entry_id).async_load() is None
    assert store._last_persisted is None
    assert store._pending is not None
    for minutes in (1, 30, 60, 90):
        planner._compute_budgeted_plan(NOW + timedelta(minutes=minutes), slots, context)
    await _elapse_save_delay(hass)

    restarted = SaxPowerCoordinator(
        hass, MagicMock(), 64, 100, 10, coordinator.entry_id
    )
    await restarted.price_planner.async_load_cycle_state()
    plan = restarted.price_planner._compute_budgeted_plan(
        NOW + timedelta(minutes=90), slots, context
    )
    assert sum((slot.end - slot.start for slot in plan.slots), timedelta()) == (
        timedelta(minutes=90)
    )
    assert store.async_delay_save(store_state := planner._cycle_state) is False
    assert store_state is not None
    await coordinator.async_shutdown(reset_device=False)
    await restarted.async_shutdown(reset_device=False)


async def test_failed_immediate_write_keeps_previous_snapshot_and_retries(
    hass: HomeAssistant,
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: only confirmed data may replace a disk baseline."""
    store = PricePlanCycleStore(hass, "immediate-retry")
    await store.async_save(_cycle(3))
    with (
        patch.object(
            store._store, "_write_prepared_data", side_effect=WriteError("disk full")
        ),
        pytest.raises(HomeAssistantError),
    ):
        await store.async_save(_cycle(1))
    assert await PricePlanCycleStore(hass, "immediate-retry").async_load() == _cycle(3)
    await _elapse_save_delay(hass)
    assert await PricePlanCycleStore(hass, "immediate-retry").async_load() == _cycle(1)


@pytest.mark.parametrize(
    "phase,fail_write", [("write", False), ("write", True), ("readback", False)]
)
async def test_latest_cycle_wins_during_slow_or_failed_storage(
    hass: HomeAssistant, phase: str, fail_write: bool
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: source updates during I/O retain the newest plan."""
    store = PricePlanCycleStore(hass, "cycle-concurrent")
    await store.async_save(_cycle(3))
    entered = asyncio.Event()
    release = asyncio.Event()
    method = "_async_write_data" if phase == "write" else "async_load"
    original = getattr(store._store, method)

    async def delayed_io(*args: Any) -> Any:
        if not entered.is_set():
            entered.set()
            await release.wait()
            if fail_write:
                raise WriteError("disk temporarily full")
        return await original(*args)

    with patch.object(store._store, method, side_effect=delayed_io):
        assert store.async_delay_save(_cycle(2), delay=0)
        await asyncio.wait_for(entered.wait(), timeout=1)
        assert store.async_delay_save(_cycle(1), delay=0)
        release.set()
        await hass.async_block_till_done()

    assert await PricePlanCycleStore(hass, "cycle-concurrent").async_load() == _cycle(1)
    assert store._pending is None
    assert store._unsub_delayed_write is None
    assert store._unsub_final_write is None


@pytest.mark.parametrize("during_stop", [False, True])
async def test_final_write_saves_the_latest_budget_and_cleans_up(
    hass: HomeAssistant, during_stop: bool
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: Core's stop deferral cannot confirm only RAM."""
    store = PricePlanCycleStore(hass, "cycle-stop")
    await store.async_save(_cycle(3))
    store.async_delay_save(_cycle(1), delay=3600)
    if during_stop:
        hass.set_state(CoreState.stopping)
        await store.async_save(_cycle(1), final=True)
        assert await PricePlanCycleStore(hass, "cycle-stop").async_load() == _cycle(3)
    hass.set_state(CoreState.final_write)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
    await hass.async_block_till_done()
    hass.set_state(CoreState.running)
    assert await PricePlanCycleStore(hass, "cycle-stop").async_load() == _cycle(1)
    assert store._pending is None
    assert store._unsub_delayed_write is None
    assert store._unsub_final_write is None


async def test_failed_unload_does_not_retry_over_a_reloaded_entry(
    hass: HomeAssistant,
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: the former store owner cannot revive an old plan."""
    coordinator = SaxPowerCoordinator(hass, MagicMock(), 64, 100, 10, "cycle-unload")
    planner = coordinator.price_planner
    await planner.async_load_cycle_state()
    planner._set_cycle_state(_cycle(3))
    old_store = planner._cycle_store
    with patch.object(
        old_store._store, "_write_prepared_data", side_effect=WriteError("disk full")
    ):
        await coordinator.async_shutdown(reset_device=False)
    assert old_store._unsub_delayed_write is None
    assert old_store._unsub_final_write is None
    new_store = PricePlanCycleStore(hass, coordinator.entry_id)
    await new_store.async_save(_cycle(1))
    await _elapse_save_delay(hass)
    hass.set_state(CoreState.final_write)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
    await hass.async_block_till_done()
    hass.set_state(CoreState.running)
    assert await new_store.async_load() == _cycle(1)


async def test_failure_during_stopping_retains_the_final_write_retry(
    hass: HomeAssistant,
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: stopping during a write preserves its retry."""
    store = PricePlanCycleStore(hass, "cycle-io-stop")
    await store.async_save(_cycle(3))
    entered = asyncio.Event()
    release = asyncio.Event()
    original = store._store._async_write_data

    async def fail_first_write(*args: Any) -> Any:
        if not entered.is_set():
            entered.set()
            await release.wait()
            raise WriteError("disk temporarily full")
        return await original(*args)

    with patch.object(store._store, "_async_write_data", side_effect=fail_first_write):
        write_task = asyncio.create_task(store.async_save(_cycle(1), final=True))
        await asyncio.wait_for(entered.wait(), timeout=1)
        hass.set_state(CoreState.stopping)
        release.set()
        with pytest.raises(HomeAssistantError):
            await write_task
        assert store._unsub_delayed_write is None
        assert store._unsub_final_write is not None
        hass.set_state(CoreState.final_write)
        hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
        await hass.async_block_till_done()
        hass.set_state(CoreState.running)
    assert await store.async_load() == _cycle(1)


async def test_failed_disabled_cycle_write_cannot_resurrect_old_budget(
    hass: HomeAssistant,
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: turning automation off also survives disk errors."""
    store = PricePlanCycleStore(hass, "cycle-disable")
    await store.async_save(_cycle(3))
    store.async_delay_save(None)
    with patch.object(
        store._store, "_write_prepared_data", side_effect=WriteError("disk full")
    ):
        await _elapse_save_delay(hass)
    await _elapse_save_delay(hass)
    assert await PricePlanCycleStore(hass, "cycle-disable").async_load() is None
