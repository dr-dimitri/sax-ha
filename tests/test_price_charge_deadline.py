"""REQ-DYNAMIC-PRICE-CHARGE: selected UTC intervals bound device permission."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    PRICE_STATUS_CHARGING,
    PRICE_STATUS_NO_PRICE_DATA,
    PRICE_STRATEGY_ABSOLUTE,
    PRICE_STRATEGY_RELATIVE,
    PRICE_STRATEGY_SMART,
    PRICE_UNIT_EUR_KWH,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

BERLIN = ZoneInfo("Europe/Berlin")


@dataclass
class Clock:
    now: datetime


@pytest.fixture
async def system(
    hass: HomeAssistant,
) -> AsyncIterator[tuple[SaxPowerCoordinator, MagicMock, Clock]]:
    await hass.config.async_set_time_zone("Europe/Berlin")
    clock = Clock(datetime(2026, 9, 14, 14, 14, 30, tzinfo=BERLIN))
    client = MagicMock(connected=True)
    success = MagicMock()
    success.isError.return_value = False
    client.write_register = AsyncMock(return_value=success)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        64,
        100,
        10,
        "price_deadline",
        options={
            CONF_ECONOMICS_TARIFF_TYPE: "dynamic",
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
            CONF_PRICE_SENSOR: "sensor.deadline_price",
            CONF_PRICE_UNIT: PRICE_UNIT_EUR_KWH,
        },
    )
    coordinator._price_charge_enabled = True
    coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    coordinator._price_charge_max_price = 0.2
    coordinator._max_soc = 90
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "battery_capacity": 7100,
    }
    with (
        patch.object(dt_util, "now", side_effect=lambda: clock.now),
        patch.object(dt_util, "utcnow", side_effect=lambda: clock.now.astimezone(UTC)),
    ):
        try:
            yield coordinator, client, clock
        finally:
            await coordinator.async_shutdown(reset_device=False)


def _prices(hass: HomeAssistant, *slots: tuple[datetime, datetime, float]) -> None:
    hass.states.async_set(
        "sensor.deadline_price",
        "0.10",
        {
            "raw_today": [
                {"start": start, "end": end, "value": price}
                for start, end, price in slots
            ]
        },
    )


def _writes(client: MagicMock) -> list[tuple[int, int]]:
    return [
        (call.kwargs["address"], call.kwargs["value"])
        for call in client.write_register.await_args_list
    ]


@pytest.mark.parametrize("next_price", [0.8, None])
async def test_expired_absolute_permission_blocks_writer_and_poll_without_event(
    hass: HomeAssistant,
    system: tuple[SaxPowerCoordinator, MagicMock, Clock],
    next_price: float | None,
) -> None:
    """Issue #258: a cached day preview must expire before the minute tick."""
    coordinator, client, clock = system
    end = clock.now.replace(minute=15, second=0)
    slots = [(end - timedelta(minutes=15), end, 0.1)]
    if next_price is not None:
        slots.append((end, end + timedelta(minutes=45), next_price))
    _prices(hass, *slots)
    plan = coordinator.price_planner.evaluate()
    assert plan.charge_now
    await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator._active_charge_deadline() == end.astimezone(UTC)

    clock.now = end + timedelta(seconds=2)
    client.write_register.reset_mock()
    with pytest.raises(HomeAssistantError, match="Preis-Ladeintervall"):
        await coordinator._async_write_sun_charge_setpoint()
    assert not _writes(client)
    await coordinator._async_enforce_grid_charge(coordinator.data)

    assert not coordinator.price_charge_active
    assert not coordinator.price_planner.plan.charge_now
    assert coordinator.price_planner.plan.current_price == next_price
    assert _writes(client) == [(REG_SUN_IC_CONTROL_MODE, 0)]


async def test_adjacent_selected_slots_keep_permission_and_update_deadline(
    hass: HomeAssistant, system: tuple[SaxPowerCoordinator, MagicMock, Clock]
) -> None:
    """Issue #258: a selected successor receives its own current price."""
    coordinator, client, clock = system
    end = clock.now.replace(minute=15, second=0)
    next_end = end + timedelta(minutes=15)
    _prices(hass, (end - timedelta(minutes=15), end, 0.1), (end, next_end, 0.15))
    coordinator.price_planner.evaluate()
    await coordinator._async_enforce_grid_charge(coordinator.data)
    clock.now = end + timedelta(seconds=2)
    client.write_register.reset_mock()

    await coordinator._async_write_sun_charge_setpoint()
    await coordinator._async_enforce_grid_charge(coordinator.data)

    assert coordinator.price_charge_active
    assert coordinator.price_planner.plan.current_price == 0.15
    assert coordinator._active_charge_deadline() == next_end.astimezone(UTC)
    assert (REG_SUN_IC_CONTROL_MODE, 0) not in _writes(client)
    assert all(value == 55536 for address, value in _writes(client) if address == 49)


@pytest.mark.parametrize("strategy", [PRICE_STRATEGY_RELATIVE, PRICE_STRATEGY_SMART])
async def test_budgeted_partial_slot_expires_inside_provider_interval(
    hass: HomeAssistant,
    system: tuple[SaxPowerCoordinator, MagicMock, Clock],
    strategy: str,
) -> None:
    """Issue #258: even fractional seconds consume the selected time budget."""
    coordinator, client, clock = system
    coordinator._price_charge_strategy = strategy
    coordinator._price_charge_hours = 1
    provider_end = clock.now + timedelta(hours=1)
    future = provider_end + timedelta(hours=1)
    _prices(
        hass,
        (clock.now - timedelta(minutes=14), provider_end, 0.1),
        (future, future + timedelta(minutes=30), 0.01),
    )
    plan = coordinator.price_planner.evaluate()
    selected = plan.active_slot(clock.now)
    assert selected is not None
    assert selected.end.astimezone(UTC) < provider_end.astimezone(UTC)
    assert selected.end.second or selected.end.microsecond
    await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator._active_charge_deadline() == selected.end.astimezone(UTC)

    clock.now = selected.end + timedelta(microseconds=1)
    client.write_register.reset_mock()
    with pytest.raises(HomeAssistantError, match="Preis-Ladeintervall"):
        await coordinator._async_write_sun_charge_setpoint()
    await coordinator._async_enforce_grid_charge(coordinator.data)

    assert not coordinator.price_charge_active
    assert coordinator.price_planner.plan.current_price == 0.1
    assert _writes(client) == [(REG_SUN_IC_CONTROL_MODE, 0)]


@pytest.mark.parametrize("delayed_address", [REG_SUN_IC_CONTROL_MODE, 49])
async def test_late_device_ack_rolls_back_expired_permission(
    hass: HomeAssistant,
    system: tuple[SaxPowerCoordinator, MagicMock, Clock],
    delayed_address: int,
) -> None:
    """Issue #258: every ACK is checked against the real selected UTC end."""
    coordinator, client, clock = system
    end = clock.now + timedelta(seconds=1)
    _prices(hass, (clock.now, end, 0.1), (end, end + timedelta(hours=1), 0.8))
    coordinator.price_planner.evaluate()
    success = client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == delayed_address:
            clock.now = end + timedelta(seconds=1)
        return success

    client.write_register.side_effect = write
    with pytest.raises(HomeAssistantError, match="Preis-Ladeintervall"):
        await coordinator._async_enforce_grid_charge(coordinator.data)

    expected = [(REG_SUN_IC_CONTROL_MODE, 1)]
    if delayed_address == REG_SUN_IC_POWER_SETPOINT_PCT:
        expected.append((REG_SUN_IC_POWER_SETPOINT_PCT, 55536))
    expected.append((REG_SUN_IC_CONTROL_MODE, 0))
    assert _writes(client) == expected
    assert not coordinator.price_charge_active
    assert not coordinator._sun_charge_reset_required


@pytest.mark.parametrize("neutral_price", [None, 0.9])
async def test_writer_wakes_at_boundary_and_confirms_next_state(
    hass: HomeAssistant,
    system: tuple[SaxPowerCoordinator, MagicMock, Clock],
    neutral_price: float | None,
) -> None:
    """Issue #258: no poll, source event or minute tick is needed for expiry."""
    coordinator, client, clock = system
    coordinator._price_charge_neutral_price = neutral_price
    end = clock.now + timedelta(milliseconds=350)
    _prices(hass, (clock.now, end, 0.1), (end, end + timedelta(hours=1), 0.8))
    coordinator.price_planner.evaluate()
    await coordinator._async_enforce_grid_charge(coordinator.data)
    await coordinator._async_cancel_sun_charge_task()
    client.write_register.reset_mock()
    sleeps: list[float] = []

    async def advance(interval: float) -> None:
        sleeps.append(interval)
        clock.now = end

    with patch("custom_components.sax_power.coordinator.asyncio.sleep", new=advance):
        await coordinator._async_sun_charge_loop()
    await hass.async_block_till_done()

    assert sleeps == [0.35]
    assert not coordinator.price_charge_active
    assert _writes(client) == (
        [(REG_SUN_IC_CONTROL_MODE, 0)]
        if neutral_price is None
        else [(REG_SUN_IC_CONTROL_MODE, 1), (REG_SUN_IC_POWER_SETPOINT_PCT, 0)]
    )


async def test_writer_reset_for_missing_soc_clears_price_activity(
    hass: HomeAssistant, system: tuple[SaxPowerCoordinator, MagicMock, Clock]
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: a confirmed outage reset also ends activity."""
    coordinator, client, clock = system
    _prices(hass, (clock.now, clock.now + timedelta(hours=1), 0.1))
    coordinator.price_planner.evaluate()
    await coordinator._async_enforce_grid_charge(coordinator.data)
    await coordinator._async_cancel_sun_charge_task()
    coordinator._basic_read_failed = True
    client.write_register.reset_mock()

    with patch(
        "custom_components.sax_power.coordinator.asyncio.sleep", new=AsyncMock()
    ):
        await coordinator._async_sun_charge_loop()

    assert not coordinator.price_charge_active
    assert coordinator._price_charge_deadline is None
    assert coordinator.data["price_charge_active"] is False
    assert _writes(client) == [(REG_SUN_IC_CONTROL_MODE, 0)]


@pytest.mark.parametrize("delayed_address", [REG_SUN_IC_CONTROL_MODE, 49])
async def test_late_ack_can_continue_in_adjacent_selected_slot(
    hass: HomeAssistant,
    system: tuple[SaxPowerCoordinator, MagicMock, Clock],
    delayed_address: int,
) -> None:
    """Issue #258: adjacent selected UTC intervals do not require a reset."""
    coordinator, client, clock = system
    end = clock.now + timedelta(seconds=1)
    _prices(hass, (clock.now, end, 0.1), (end, end + timedelta(hours=1), 0.15))
    coordinator.price_planner.evaluate()
    success = client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == delayed_address:
            clock.now = end + timedelta(seconds=1)
        return success

    client.write_register.side_effect = write
    await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator.price_charge_active
    assert _writes(client) == [
        (REG_SUN_IC_CONTROL_MODE, 1),
        (REG_SUN_IC_POWER_SETPOINT_PCT, 55536),
    ]
    assert coordinator.price_planner.plan.current_price == 0.15


async def test_gap_and_following_selected_slot_update_status_and_start(
    hass: HomeAssistant, system: tuple[SaxPowerCoordinator, MagicMock, Clock]
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: display and permission recover together."""
    coordinator, _, clock = system
    end = clock.now + timedelta(seconds=10)
    following = end + timedelta(seconds=10)
    _prices(hass, (clock.now, end, 0.1), (following, end + timedelta(hours=1), 0.15))
    coordinator.price_planner.evaluate()
    clock.now = end
    gap_plan = coordinator.price_planner.plan_at(clock.now)
    assert not gap_plan.charge_now
    assert gap_plan.status == PRICE_STATUS_NO_PRICE_DATA
    assert gap_plan.current_price is None
    assert gap_plan.next_start.astimezone(UTC) == following.astimezone(UTC)

    clock.now = following
    recovered = coordinator.price_planner.plan_at(clock.now)
    assert recovered.charge_now
    assert recovered.status == PRICE_STATUS_CHARGING
    assert recovered.current_price == 0.15
    assert recovered.next_start.astimezone(UTC) == following.astimezone(UTC)


async def test_boundary_timer_releases_max_soc_hold_without_charge_deadline(
    hass: HomeAssistant, system: tuple[SaxPowerCoordinator, MagicMock, Clock]
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: a zero-power hold expires at its price end."""
    coordinator, client, clock = system
    end = clock.now + timedelta(seconds=1)
    coordinator.data["soc"] = 90
    _prices(hass, (clock.now, end, 0.1), (end, end + timedelta(hours=1), 0.8))
    with patch(
        "custom_components.sax_power.price_optimizer.async_track_point_in_utc_time",
        return_value=MagicMock(),
    ) as track:
        coordinator.price_planner.async_setup()
        callback = track.call_args.args[1]
        await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator._max_soc_hold_is_price_slot_bound
        assert coordinator._active_charge_deadline() is None
        clock.now = end
        client.write_register.reset_mock()
        await callback(end.astimezone(UTC))

    assert not coordinator._max_soc_hold_is_price_slot_bound
    assert not coordinator._max_soc_clamped
    assert _writes(client) == [(REG_SUN_IC_CONTROL_MODE, 0)]


async def test_boundary_timer_tracks_partial_selection_and_cleans_up(
    hass: HomeAssistant, system: tuple[SaxPowerCoordinator, MagicMock, Clock]
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: display and device share boundary selection."""
    coordinator, _, clock = system
    coordinator._price_charge_strategy = PRICE_STRATEGY_RELATIVE
    coordinator._price_charge_hours = 1
    future = clock.now + timedelta(hours=2)
    _prices(
        hass,
        (clock.now, clock.now + timedelta(hours=1), 0.1),
        (future, future + timedelta(minutes=45), 0.01),
    )
    unsubscribe = MagicMock()
    coordinator.async_apply_price_plan = AsyncMock()
    with patch(
        "custom_components.sax_power.price_optimizer.async_track_point_in_utc_time",
        return_value=unsubscribe,
    ) as track:
        coordinator.price_planner.async_setup()
        end = clock.now + timedelta(minutes=15)
        assert track.call_args.args[2] == end.astimezone(UTC)
        callback = track.call_args.args[1]
        clock.now = end
        await callback(end.astimezone(UTC))
        assert not coordinator.price_planner.plan.charge_now
        coordinator.async_apply_price_plan.assert_awaited_once()
        assert track.call_args.args[2] == (end + timedelta(minutes=45)).astimezone(UTC)
        await coordinator.price_planner.async_shutdown()
        assert unsubscribe.call_count >= 2


async def test_fall_back_hour_uses_distinct_utc_intervals(
    hass: HomeAssistant, system: tuple[SaxPowerCoordinator, MagicMock, Clock]
) -> None:
    """Issue #258: the repeated local hour cannot inherit first-fold permission."""
    coordinator, client, clock = system
    first = datetime(2026, 10, 25, 2, 0, tzinfo=BERLIN, fold=0)
    second = first.replace(fold=1)
    after = datetime(2026, 10, 25, 3, 0, tzinfo=BERLIN)
    clock.now = (second.astimezone(UTC) - timedelta(seconds=30)).astimezone(BERLIN)
    _prices(hass, (first, second, 0.1), (second, after, 0.8))
    coordinator.price_planner.evaluate()
    await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator.price_charge_active
    assert coordinator._active_charge_deadline() == second.astimezone(UTC)

    clock.now = (second.astimezone(UTC) + timedelta(seconds=2)).astimezone(BERLIN)
    client.write_register.reset_mock()
    await coordinator._async_enforce_grid_charge(coordinator.data)
    assert not coordinator.price_charge_active
    assert coordinator.price_planner.plan.current_price == 0.8
    assert _writes(client) == [(REG_SUN_IC_CONTROL_MODE, 0)]
