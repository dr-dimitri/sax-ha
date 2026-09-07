"""REQ-GRID-ENERGY: persistence, migration and independent corruption recovery."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant

from custom_components.sax_power.infrastructure.energy_store import (
    STORAGE_KEY_PREFIX,
    EnergyState,
    EnergyStateStore,
)

STARTED_AT = datetime(2026, 9, 7, 8, tzinfo=UTC)


def _state() -> EnergyState:
    return EnergyState(
        charged_kwh=12.5,
        discharged_kwh=4.25,
        grid_charged_kwh=8.0,
        pv_charged_kwh=4.5,
        origin_accounting_started_at=STARTED_AT - timedelta(days=1),
        grid_imported_kwh=30.0,
        grid_exported_kwh=15.0,
        grid_accounting_started_at=STARTED_AT,
    )


def _raw_state() -> dict[str, Any]:
    return {
        "charged_kwh": 12.5,
        "discharged_kwh": 4.25,
        "grid_charged_kwh": 8.0,
        "pv_charged_kwh": 4.5,
        "origin_accounting_started_at": (STARTED_AT - timedelta(days=1)).isoformat(),
        "grid_imported_kwh": 30.0,
        "grid_exported_kwh": 15.0,
        "grid_accounting_started_at": STARTED_AT.isoformat(),
    }


def test_grid_only_baseline_is_persistable_without_battery_initialization() -> None:
    state = EnergyState(
        grid_imported_kwh=0.0,
        grid_exported_kwh=0.0,
        grid_accounting_started_at=STARTED_AT,
    )

    assert state.initialized
    assert state.grid_initialized
    assert not state.origin_initialized
    assert not EnergyState(grid_imported_kwh=0.0).initialized


async def test_real_version_three_store_preserves_battery_and_origin_history(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Die additive Migration durch den echten HA Store erzeugt keine Netz-Historie."""
    key = f"{STORAGE_KEY_PREFIX}.migration"
    legacy = {
        key: value
        for key, value in _raw_state().items()
        if key
        not in ("grid_imported_kwh", "grid_exported_kwh", "grid_accounting_started_at")
    }
    hass_storage[key] = {
        "version": 1,
        "minor_version": 3,
        "key": key,
        "data": legacy,
    }
    store = EnergyStateStore(hass, "migration")

    loaded = await store.async_load()

    assert loaded == replace(
        _state(),
        grid_imported_kwh=None,
        grid_exported_kwh=None,
        grid_accounting_started_at=None,
    )
    assert loaded.origin_initialized
    assert not loaded.grid_initialized
    restarted = replace(
        loaded,
        grid_imported_kwh=0.0,
        grid_exported_kwh=0.0,
        grid_accounting_started_at=STARTED_AT,
    )
    assert await store.async_save(restarted)
    assert await EnergyStateStore(hass, "migration").async_load() == restarted


async def test_grid_round_trip_normalizes_utc_and_keeps_entries_independent(
    hass: HomeAssistant,
) -> None:
    state = replace(
        _state(),
        grid_accounting_started_at=datetime(
            2026, 9, 7, 10, tzinfo=ZoneInfo("Europe/Berlin")
        ),
    )

    assert await EnergyStateStore(hass, "first").async_save(state)

    loaded = await EnergyStateStore(hass, "first").async_load()
    assert loaded == _state()
    assert loaded.grid_accounting_started_at.tzinfo is UTC
    assert await EnergyStateStore(hass, "second").async_load() is None


@pytest.mark.parametrize("field", ["grid_imported_kwh", "grid_exported_kwh"])
@pytest.mark.parametrize(
    "invalid",
    [
        None,
        -1,
        True,
        "7",
        float("nan"),
        float("inf"),
        pytest.param(10**1000, id="overflowing-integer"),
    ],
)
async def test_invalid_grid_counter_preserves_other_fields_and_allows_group_restart(
    hass: HomeAssistant, field: str, invalid: object
) -> None:
    raw = {**_raw_state(), field: invalid}
    store = EnergyStateStore(hass, "corrupt-counter")
    store._store.async_load = AsyncMock(return_value=raw)
    store._store.async_save = AsyncMock()

    loaded = await store.async_load()

    assert loaded == replace(_state(), **{field: None})
    assert not loaded.grid_initialized
    restarted = replace(
        loaded,
        grid_imported_kwh=0.0,
        grid_exported_kwh=0.0,
        grid_accounting_started_at=STARTED_AT + timedelta(days=1),
    )
    assert await store.async_save(restarted)
    store._store.async_save.assert_awaited_once()


@pytest.mark.parametrize(
    "invalid",
    [None, True, 42, "invalid", "2026-09-07T10:00:00", "0001-01-01T00:00:00+01:00"],
)
async def test_invalid_grid_start_preserves_counters_and_allows_group_restart(
    hass: HomeAssistant, invalid: object
) -> None:
    store = EnergyStateStore(hass, "corrupt-start")
    store._store.async_load = AsyncMock(
        return_value={**_raw_state(), "grid_accounting_started_at": invalid}
    )
    store._store.async_save = AsyncMock()

    loaded = await store.async_load()

    assert loaded == replace(_state(), grid_accounting_started_at=None)
    assert not loaded.grid_initialized
    assert await store.async_save(
        replace(
            loaded,
            grid_imported_kwh=0.0,
            grid_exported_kwh=0.0,
            grid_accounting_started_at=STARTED_AT + timedelta(days=1),
        )
    )


async def test_corrupt_origin_does_not_reset_valid_grid_baseline(
    hass: HomeAssistant,
) -> None:
    store = EnergyStateStore(hass, "corrupt-origin")
    store._store.async_load = AsyncMock(
        return_value={**_raw_state(), "pv_charged_kwh": -1}
    )
    store._store.async_save = AsyncMock()
    loaded = await store.async_load()

    assert loaded.grid_initialized
    assert not loaded.origin_initialized
    restarted = replace(
        loaded,
        grid_charged_kwh=0.0,
        pv_charged_kwh=0.0,
        origin_accounting_started_at=STARTED_AT,
    )
    assert await store.async_save(restarted)
    assert not await store.async_save(replace(restarted, grid_imported_kwh=0.0))


@pytest.mark.parametrize("field", ["grid_imported_kwh", "grid_exported_kwh"])
@pytest.mark.parametrize(
    "invalid",
    [
        None,
        -1,
        1.0,
        True,
        "50",
        float("nan"),
        float("inf"),
        pytest.param(10**1000, id="overflowing-integer"),
    ],
)
async def test_grid_counter_cannot_regress_or_become_invalid(
    hass: HomeAssistant, field: str, invalid: object
) -> None:
    store = EnergyStateStore(hass, "monotonic")
    store._store.async_save = AsyncMock()
    assert await store.async_save(_state())

    assert not await store.async_save(replace(_state(), **{field: invalid}))
    assert store._store.async_save.await_count == 1


@pytest.mark.parametrize("timestamp", [None, STARTED_AT + timedelta(seconds=1)])
async def test_grid_start_remains_immutable(
    hass: HomeAssistant, timestamp: datetime | None
) -> None:
    store = EnergyStateStore(hass, "immutable-start")
    store._store.async_save = AsyncMock()
    assert await store.async_save(_state())

    assert not await store.async_save(
        replace(_state(), grid_accounting_started_at=timestamp)
    )
    assert store._store.async_save.await_count == 1


@pytest.mark.parametrize("timestamp", [True, "invalid", datetime(2026, 9, 7, 10)])
async def test_grid_start_rejects_invalid_initial_snapshot(
    hass: HomeAssistant, timestamp: object
) -> None:
    store = EnergyStateStore(hass, "invalid-initial-start")
    store._store.async_save = AsyncMock()

    assert not await store.async_save(
        replace(_state(), grid_accounting_started_at=timestamp)
    )
    store._store.async_save.assert_not_awaited()


async def test_pending_grid_counters_are_monotonic_and_coalesce(
    hass: HomeAssistant,
) -> None:
    store = EnergyStateStore(hass, "pending")
    store._store.async_delay_save = MagicMock()
    first = _state()
    latest = replace(first, grid_imported_kwh=31.0, grid_exported_kwh=15.5)

    assert store.async_delay_save(first)
    assert store.async_delay_save(latest)
    assert not store.async_delay_save(first)

    store._store.async_delay_save.assert_called_once()
    consume = store._store.async_delay_save.call_args.args[0]
    assert consume() == {
        **_raw_state(),
        "grid_imported_kwh": 31.0,
        "grid_exported_kwh": 15.5,
    }
