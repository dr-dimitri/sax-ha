"""REQ-TIMED-SOC-CHARGE: persist only complete, validated window identities."""

from datetime import UTC, datetime
from datetime import time as dt_time
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.sax_power.application.timed_charge import TimedChargeState
from custom_components.sax_power.infrastructure.timed_charge_store import (
    TimedChargeStateStore,
)


async def test_round_trip_normalizes_utc_and_isolates_entries(
    hass: HomeAssistant,
) -> None:
    store = TimedChargeStateStore(hass, "first")
    await store.async_save(
        TimedChargeState(
            dt_time(23),
            dt_time(6),
            datetime(2026, 9, 5, 6, tzinfo=ZoneInfo("Europe/Berlin")),
        )
    )
    assert await TimedChargeStateStore(hass, "first").async_load() == TimedChargeState(
        dt_time(23), dt_time(6), datetime(2026, 9, 5, 4, tzinfo=UTC)
    )
    assert await TimedChargeStateStore(hass, "second").async_load() is None
    await store.async_save(None)
    assert await TimedChargeStateStore(hass, "first").async_load() is None


@pytest.mark.parametrize(
    "raw",
    [
        None,
        {},
        [],
        True,
        {"start": "23:00:00", "end": "06:00:00"},
        {"start": "23:00:00", "end": "06:00:00", "expires_at": True},
        {"start": "23:00:00", "end": "06:00:00", "expires_at": "invalid"},
        {"start": "23:00:00", "end": "06:00:00", "expires_at": "2026-09-05T06:00"},
        {
            "start": "23:00:00",
            "end": "06:00:00",
            "expires_at": "0001-01-01T00:00+01:00",
        },
        {"start": True, "end": "06:00:00", "expires_at": "2026-09-05T06:00+02:00"},
        {"start": "25:00", "end": "06:00:00", "expires_at": "2026-09-05T06:00+02:00"},
        {
            "start": "23:00+02:00",
            "end": "06:00",
            "expires_at": "2026-09-05T06:00+02:00",
        },
        {"start": "06:00", "end": "06:00", "expires_at": "2026-09-05T06:00+02:00"},
        {
            "armed": False,
            "start": "23:00",
            "end": "06:00",
            "expires_at": "2026-09-05T06:00+02:00",
        },
        {
            "armed": 1,
            "start": "23:00",
            "end": "06:00",
            "expires_at": "2026-09-05T06:00+02:00",
        },
    ],
)
async def test_invalid_state_never_invents_or_rewrites_a_latch(
    hass: HomeAssistant, raw: object
) -> None:
    store = TimedChargeStateStore(hass, "invalid")
    if isinstance(raw, dict):
        raw = {"armed": True, **raw}
    store._store.async_load = AsyncMock(return_value=raw)
    store._store.async_save = AsyncMock()
    store._store.async_remove = AsyncMock()
    assert await store.async_load() is None
    store._store.async_save.assert_not_called()
    store._store.async_remove.assert_not_called()


async def test_readback_failure_is_reported_as_home_assistant_error(
    hass: HomeAssistant,
) -> None:
    store = TimedChargeStateStore(hass, "readback")
    store._store.async_save = AsyncMock()
    store._store.async_load = AsyncMock(side_effect=NotImplementedError("version"))
    with pytest.raises(HomeAssistantError, match="nicht sicher gespeichert"):
        await store.async_save(None)


@pytest.mark.parametrize(
    "error", [HomeAssistantError(), NotImplementedError(), OSError(), ValueError()]
)
async def test_load_failure_does_not_create_a_latch_or_modify_storage(
    hass: HomeAssistant, error: Exception
) -> None:
    store = TimedChargeStateStore(hass, "unreadable")
    store._store.async_load = AsyncMock(side_effect=error)
    store._store.async_save = AsyncMock()
    store._store.async_remove = AsyncMock()
    assert await store.async_load() is None
    store._store.async_save.assert_not_called()
    store._store.async_remove.assert_not_called()


@pytest.mark.parametrize(
    "state",
    [
        True,
        TimedChargeState(None, dt_time(6), datetime(2026, 9, 5, 4, tzinfo=UTC)),
        TimedChargeState(dt_time(23), dt_time(6), datetime(2026, 9, 5, 4)),
        TimedChargeState(dt_time(23), dt_time(6), None),
    ],
)
async def test_save_validates_before_mutating_storage(
    hass: HomeAssistant, state: object
) -> None:
    store = TimedChargeStateStore(hass, "invalid")
    store._store.async_save = AsyncMock()
    with pytest.raises(ValueError):
        await store.async_save(state)
    store._store.async_save.assert_not_called()
