"""REQ-TIMED-SOC-CHARGE: persistence of confirmed timed-charge protection."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.sax_power.application.timed_discharge import TimedDischargeState
from custom_components.sax_power.infrastructure.timed_discharge_store import (
    TimedDischargeStateStore,
)


async def test_store_round_trip_normalizes_utc_and_isolates_entries(
    hass: HomeAssistant,
) -> None:
    state = TimedDischargeState(
        expires_at=datetime(2026, 9, 5, 4, tzinfo=ZoneInfo("Europe/Berlin"))
    )

    await TimedDischargeStateStore(hass, "first").async_save(state)

    assert await TimedDischargeStateStore(hass, "first").async_load() == (
        TimedDischargeState(expires_at=datetime(2026, 9, 5, 2, tzinfo=UTC))
    )
    assert await TimedDischargeStateStore(hass, "second").async_load() is None


async def test_released_protection_is_removed_from_storage(hass: HomeAssistant) -> None:
    store = TimedDischargeStateStore(hass, "released")
    await store.async_save(
        TimedDischargeState(expires_at=datetime(2026, 9, 5, 2, tzinfo=UTC))
    )

    await store.async_save(None)

    assert await TimedDischargeStateStore(hass, "released").async_load() is None


@pytest.mark.parametrize(
    "raw",
    [
        {},
        [],
        "invalid",
        1,
        True,
        {"expires_at": None},
        {"expires_at": True},
        {"expires_at": 123},
        {"expires_at": []},
        {"expires_at": "2026-09-05T02:00:00"},
        {"expires_at": "2026-09-05"},
        {"expires_at": "not a timestamp"},
        {"expires_at": "0001-01-01T00:00:00+01:00"},
    ],
)
async def test_corrupt_state_never_invents_or_rewrites_protection(
    hass: HomeAssistant, raw: object
) -> None:
    store = TimedDischargeStateStore(hass, "corrupt")
    store._store.async_load = AsyncMock(return_value=raw)
    store._store.async_save = AsyncMock()
    store._store.async_remove = AsyncMock()

    assert await store.async_load() is None
    store._store.async_save.assert_not_called()
    store._store.async_remove.assert_not_called()


@pytest.mark.parametrize(
    "error", [HomeAssistantError(), NotImplementedError(), OSError(), ValueError()]
)
async def test_unreadable_state_does_not_create_protection_or_write_back(
    hass: HomeAssistant, error: Exception
) -> None:
    store = TimedDischargeStateStore(hass, "unreadable")
    store._store.async_load = AsyncMock(side_effect=error)
    store._store.async_save = AsyncMock()
    store._store.async_remove = AsyncMock()

    assert await store.async_load() is None
    store._store.async_save.assert_not_called()
    store._store.async_remove.assert_not_called()


@pytest.mark.parametrize("timestamp", [datetime(2026, 9, 5, 2), "invalid", None])
async def test_save_rejects_invalid_expiry_without_mutating_storage(
    hass: HomeAssistant, timestamp: object
) -> None:
    store = TimedDischargeStateStore(hass, "invalid_expiry")
    store._store.async_save = AsyncMock()
    store._store.async_remove = AsyncMock()

    with pytest.raises(ValueError):
        await store.async_save(TimedDischargeState(expires_at=timestamp))

    store._store.async_save.assert_not_called()
    store._store.async_remove.assert_not_called()


async def test_loading_keeps_absolute_expiry_for_coordinator_validation(
    hass: HomeAssistant,
) -> None:
    """Restoring must never recalculate or extend an already elapsed window."""
    expired = TimedDischargeState(expires_at=datetime(2020, 1, 1, tzinfo=UTC))
    store = TimedDischargeStateStore(hass, "expired")
    await store.async_save(expired)

    assert await TimedDischargeStateStore(hass, "expired").async_load() == expired
