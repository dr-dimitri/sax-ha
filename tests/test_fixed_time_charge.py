"""Daily charge runs and restore: REQ-FIXED-TIME-GRID-CHARGE."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir

from custom_components.sax_power.application.fixed_time_charge import (
    FixedTimeChargeState,
    fixed_time_charge_state,
)
from custom_components.sax_power.application.tariff_profiles import (
    bridge_configuration_error,
    options_for_tariff,
)
from custom_components.sax_power.const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_DASHBOARD_TARIFF_PROFILES,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_FIXED_TIME_CHARGE_ENABLED,
    CONF_FIXED_TIME_CHARGE_START,
    DOMAIN,
    ISSUE_CONTROL_CONFIG_UNRESOLVED,
    ISSUE_EMPTY_CHARGE_WINDOW,
    ISSUE_MAX_SOC_BELOW_MIN_SOC,
    ISSUE_NO_ACTIVE_MONTHS,
    REG_SUN_IC_CONTROL_MODE,
    SUN_IC_CONTROL_MODE_SMARTMETER,
    economics_tou_window_key,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.tariff import TariffType
from custom_components.sax_power.infrastructure.control_store import (
    ControlConfig,
    ControlConfigStore,
)
from custom_components.sax_power.infrastructure.fixed_time_charge_store import (
    FixedTimeChargeStateStore,
)
from custom_components.sax_power.price_optimizer import PricePlan

BERLIN = ZoneInfo("Europe/Berlin")
ENTRY_ID = "fixed_time_charge"


def _local(value: str) -> datetime:
    moment = datetime.fromisoformat(value)
    return (
        moment.replace(tzinfo=BERLIN)
        if moment.tzinfo is None
        else moment.astimezone(BERLIN)
    )


@contextmanager
def _at(value: str) -> Iterator[None]:
    moment = _local(value)
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


def _coordinator(
    hass: HomeAssistant,
    *,
    tariff: TariffType = TariffType.TIME_OF_USE,
    start: str = "02:00:00",
    minimum: int | None = 20,
) -> SaxPowerCoordinator:
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
        options={
            CONF_ECONOMICS_TARIFF_TYPE: tariff.value,
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.3,
            CONF_FIXED_TIME_CHARGE_ENABLED: True,
            CONF_FIXED_TIME_CHARGE_START: start,
        },
    )
    coordinator.data = {
        "soc": 55,
        "smartmeter_power": 0,
        "storage_power_active": 0,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    coordinator._timed_charge_enabled = tariff is TariffType.TIME_OF_USE
    coordinator._price_charge_enabled = tariff is TariffType.DYNAMIC
    coordinator._timed_charge_min_soc = minimum
    coordinator._timed_charge_max_soc = 80
    coordinator._max_soc = 100
    return coordinator


@pytest.mark.parametrize("tariff", [TariffType.TIME_OF_USE, TariffType.DYNAMIC])
@pytest.mark.parametrize("minimum", [None, 0, 20])
async def test_starts_above_minimum_without_tariff_price_or_forecast(
    hass: HomeAssistant, tariff: TariffType, minimum: int | None
) -> None:
    """An explicit clock time needs only a valid SOC and device reference."""
    coordinator = _coordinator(hass, tariff=tariff, minimum=minimum)
    try:
        with _at("2026-10-21T01:59:59"):
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert not coordinator._timed_charge_active
        assert coordinator.client.write_register.await_count == 0
        with _at("2026-10-21T02:00:00"):
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator._timed_charge_active
        assert not coordinator._price_charge_active
        assert coordinator._sun_charge_power < 0
        assert coordinator._active_charge_deadline() is None
    finally:
        await coordinator.async_shutdown()


async def test_completion_survives_restart_and_waits_for_next_daily_start(
    hass: HomeAssistant,
) -> None:
    coordinator = _coordinator(hass)
    restored = _coordinator(hass)
    try:
        with _at("2026-10-21T02:00:00"):
            await coordinator._async_enforce_grid_charge(coordinator.data)
            coordinator.data["soc"] = 80
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert not coordinator._timed_charge_active
        assert (
            coordinator.client.write_register.call_args.kwargs["address"]
            == REG_SUN_IC_CONTROL_MODE
        )
        assert (
            coordinator.client.write_register.call_args.kwargs["value"]
            == SUN_IC_CONTROL_MODE_SMARTMETER
        )
        await coordinator.async_shutdown()
        await restored.async_load_timed_charge_state()
        assert restored._fixed_time_charge_state.completed
        with _at("2026-10-21T12:00:00"):
            await restored._async_enforce_grid_charge(restored.data)
        assert not restored._timed_charge_active
        with _at("2026-10-22T01:59:59"):
            await restored._async_enforce_grid_charge(restored.data)
        assert not restored._timed_charge_active
        with _at("2026-10-22T02:00:00"):
            await restored._async_enforce_grid_charge(restored.data)
        assert restored._timed_charge_active
    finally:
        await coordinator.async_shutdown()
        await restored.async_shutdown()


async def test_fixed_start_ignores_expensive_tariff_phase(hass: HomeAssistant) -> None:
    coordinator = _coordinator(hass)
    coordinator.options = {
        **coordinator.options,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.1,
        economics_tou_window_key(1): {
            "start": "01:00:00",
            "end": "06:00:00",
            "price": 0.5,
        },
    }
    try:
        with _at("2026-10-21T02:00:00"):
            assert (
                coordinator._active_tariff_charge_state(_local("2026-10-21T02:00:00"))
                is None
            )
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator._timed_charge_active
    finally:
        await coordinator.async_shutdown()


async def test_unfinished_charge_resumes_after_midnight_and_restart(
    hass: HomeAssistant,
) -> None:
    coordinator = _coordinator(hass, start="23:30:00")
    restored = _coordinator(hass, start="23:30:00")
    try:
        with _at("2026-10-21T23:30:00"):
            await coordinator._async_enforce_grid_charge(coordinator.data)
        await coordinator.async_shutdown()
        await restored.async_load_timed_charge_state()
        with _at("2026-10-22T00:30:00"):
            await restored._async_enforce_grid_charge(restored.data)
        assert restored._timed_charge_active
        assert restored._fixed_time_charge_state.day.isoformat() == "2026-10-21"
    finally:
        await coordinator.async_shutdown()
        await restored.async_shutdown()


@pytest.mark.parametrize(
    "invalid_soc", [None, True, -1, 101, float("nan"), float("inf")]
)
async def test_invalid_soc_never_starts_or_creates_a_daily_permission(
    hass: HomeAssistant, invalid_soc: object
) -> None:
    coordinator = _coordinator(hass)
    coordinator.data["soc"] = invalid_soc
    try:
        with _at("2026-10-21T03:00:00"):
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert not coordinator._timed_charge_active
        assert coordinator._fixed_time_charge_state is None
        assert coordinator.client.write_register.await_count == 0
    finally:
        await coordinator.async_shutdown()


@pytest.mark.parametrize("stop", ["switch", "month", "basic", "schedule"])
async def test_active_charge_stops_when_permission_is_revoked(
    hass: HomeAssistant, stop: str
) -> None:
    coordinator = _coordinator(hass)
    try:
        with _at("2026-10-21T03:00:00"):
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._timed_charge_active
            if stop == "switch":
                coordinator._timed_charge_enabled = False
            elif stop == "month":
                coordinator._timed_charge_months = {1}
            elif stop == "basic":
                coordinator._basic_read_failed = True
            else:
                coordinator.options = {
                    **coordinator.options,
                    CONF_FIXED_TIME_CHARGE_START: "04:00",
                }
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert not coordinator._timed_charge_active
        assert not coordinator.sun_charge_active
    finally:
        await coordinator.async_shutdown()


async def test_global_cap_and_target_edit_remain_effective(hass: HomeAssistant) -> None:
    coordinator = _coordinator(hass, minimum=70)
    coordinator._max_soc = 40
    coordinator.data["soc"] = 39
    try:
        with _at("2026-10-21T03:00:00"):
            await coordinator.async_set_timed_charge_max_soc(
                40, defer_device_update=True
            )
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._timed_charge_active
            coordinator.data["soc"] = 40
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert not coordinator._timed_charge_active
        assert coordinator._fixed_time_charge_state.completed
    finally:
        await coordinator.async_shutdown()


@pytest.mark.parametrize("ack_phase", [1, 2])
async def test_disable_during_either_ack_phase_rolls_back_before_publishing_success(
    hass: HomeAssistant, ack_phase: int
) -> None:
    coordinator = _coordinator(hass)
    writes = 0

    async def write_register(**kwargs: object) -> MagicMock:
        nonlocal writes
        writes += 1
        if writes == ack_phase:
            coordinator._timed_charge_enabled = False
        response = MagicMock()
        response.isError.return_value = False
        return response

    coordinator.client.write_register.side_effect = write_register
    try:
        with _at("2026-10-21T02:00:00"):
            with pytest.raises(HomeAssistantError, match="Netzladefreigabe"):
                await coordinator._async_enforce_grid_charge(coordinator.data)
        assert not coordinator._timed_charge_active
        assert (
            coordinator.client.write_register.call_args.kwargs["address"]
            == REG_SUN_IC_CONTROL_MODE
        )
        assert (
            coordinator.client.write_register.call_args.kwargs["value"]
            == SUN_IC_CONTROL_MODE_SMARTMETER
        )
    finally:
        await coordinator.async_shutdown()


async def test_failed_ack_preserves_unfinished_permission_for_retry(
    hass: HomeAssistant,
) -> None:
    coordinator = _coordinator(hass)
    failure = MagicMock()
    failure.isError.return_value = True
    success = MagicMock()
    success.isError.return_value = False
    coordinator.client.write_register.side_effect = [success, failure, success]
    try:
        with _at("2026-10-21T02:00:00"):
            with pytest.raises(HomeAssistantError):
                await coordinator._async_enforce_grid_charge(coordinator.data)
            assert not coordinator._timed_charge_active
            assert not coordinator._fixed_time_charge_state.completed
            coordinator.client.write_register.side_effect = None
            coordinator.client.write_register.return_value = success
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator._timed_charge_active
    finally:
        await coordinator.async_shutdown()


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        ("2026-03-29T03:29:59+02:00", False),
        ("2026-03-29T03:30:00+02:00", True),
        ("2026-10-25T02:29:59+02:00", False),
        ("2026-10-25T02:30:00+02:00", True),
        ("2026-10-25T02:00:00+01:00", True),
    ],
)
def test_dst_occurrence_uses_first_fold_and_moves_skipped_time_forward(
    moment: str, expected: bool
) -> None:
    state = fixed_time_charge_state(
        None, now=_local(moment), start=dt_time(2, 30), target_reached=False
    )
    assert (state is not None) is expected


def test_completed_first_dst_fold_does_not_repeat_in_second_fold() -> None:
    state = fixed_time_charge_state(
        None,
        now=_local("2026-10-25T02:30:00+02:00"),
        start=dt_time(2, 30),
        target_reached=True,
    )
    repeated = fixed_time_charge_state(
        state,
        now=_local("2026-10-25T02:30:00+01:00"),
        start=dt_time(2, 30),
        target_reached=False,
    )
    assert repeated is not None and repeated.completed


async def test_pv_pause_keeps_the_same_unfinished_daily_run(
    hass: HomeAssistant,
) -> None:
    coordinator = _coordinator(hass)
    try:
        with _at("2026-10-21T02:00:00"):
            await coordinator._async_enforce_grid_charge(coordinator.data)
            coordinator._timed_charge_pv_surplus_cycles = 100
            coordinator.data["smartmeter_power"] = -1000
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert not coordinator._timed_charge_active
            assert not coordinator._fixed_time_charge_state.completed
            coordinator.data["smartmeter_power"] = 0
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator._timed_charge_active
    finally:
        await coordinator.async_shutdown()


async def test_daily_store_rejects_invalid_permission_and_roundtrips_completion(
    hass: HomeAssistant,
) -> None:
    store = FixedTimeChargeStateStore(hass, ENTRY_ID)
    state = FixedTimeChargeState(dt_time(2), _local("2026-10-21").date(), True)
    await store.async_save(state)
    assert await store.async_load() == state
    await store._store.async_save(
        {"start": "02:00", "day": "2026-10-21", "completed": 1}
    )
    assert await store.async_load() is None
    await store.async_save(None)
    assert await store.async_load() is None


async def test_dynamic_fixed_mode_ignores_legacy_window_overlap(
    hass: HomeAssistant,
) -> None:
    coordinator = _coordinator(hass, tariff=TariffType.DYNAMIC)
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(6)
    coordinator._timed_charge_months = {9}
    coordinator._grid_serving_months = {10}
    coordinator._grid_serving_start = dt_time(2)
    coordinator._grid_serving_end = dt_time(5)
    try:
        await coordinator._charge_control_lock.acquire()
        await coordinator.async_set_timed_charge_month(10, True)
        await coordinator.async_set_grid_serving_month(9, True)
        await coordinator.async_set_grid_serving_window(
            dt_time(1, 30), dt_time(5, 30), defer_device_update=True
        )
        assert coordinator.timed_charge_months == {9, 10}
        assert coordinator.grid_serving_months == {9, 10}
        assert coordinator.grid_serving_start == dt_time(1, 30)
        assert coordinator.grid_serving_end == dt_time(5, 30)
    finally:
        coordinator._charge_control_lock.release()
        await coordinator.async_shutdown()


async def test_old_price_slot_hold_cannot_block_fixed_charge_below_global_limit(
    hass: HomeAssistant,
) -> None:
    coordinator = _coordinator(hass, tariff=TariffType.DYNAMIC)
    coordinator._max_soc_hold_is_price_slot_bound = True
    coordinator._max_soc_price_slot_target = 100
    try:
        with (
            _at("2026-10-21T02:00:00"),
            patch.object(
                coordinator.price_planner,
                "plan_at",
                return_value=PricePlan(charge_now=True),
            ),
        ):
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator._timed_charge_active
        assert not coordinator._max_soc_hold_is_price_slot_bound
    finally:
        await coordinator.async_shutdown()


async def test_dynamic_restore_preserves_irrelevant_legacy_windows(
    hass: HomeAssistant,
) -> None:
    coordinator = _coordinator(hass, tariff=TariffType.DYNAMIC)
    await ControlConfigStore(hass, ENTRY_ID).async_save(
        ControlConfig(
            timed_charge_start=dt_time(1),
            timed_charge_end=dt_time(6),
            timed_charge_months=frozenset({10}),
            grid_serving_start=dt_time(2),
            grid_serving_end=dt_time(5),
            grid_serving_months=frozenset({10}),
            price_charge_enabled=True,
        )
    )
    try:
        await coordinator.async_load_control_state()
        assert coordinator.timed_charge_start == dt_time(1)
        assert coordinator.timed_charge_end == dt_time(6)
    finally:
        await coordinator.async_shutdown()


@pytest.mark.parametrize("tariff", [TariffType.TIME_OF_USE, TariffType.DYNAMIC])
async def test_fixed_diagnostics_ignore_threshold_but_still_report_empty_months(
    hass: HomeAssistant, tariff: TariffType
) -> None:
    coordinator = _coordinator(hass, tariff=tariff, minimum=70)
    coordinator._timed_charge_max_soc = 40
    coordinator._timed_charge_months = set()
    coordinator._control_unresolved_fields = {
        "timed_charge_start",
        "timed_charge_end",
        "timed_charge_min_soc",
    }
    try:
        coordinator._async_check_self_diagnostics()
        coordinator._async_sync_unresolved_fields_issue()
        registry = ir.async_get(hass)
        assert (
            registry.async_get_issue(
                DOMAIN, f"{ISSUE_MAX_SOC_BELOW_MIN_SOC}_{ENTRY_ID}"
            )
            is None
        )
        assert (
            registry.async_get_issue(
                DOMAIN, f"{ISSUE_EMPTY_CHARGE_WINDOW}_timed_charge_{ENTRY_ID}"
            )
            is None
        )
        assert (
            registry.async_get_issue(
                DOMAIN, f"{ISSUE_CONTROL_CONFIG_UNRESOLVED}_{ENTRY_ID}"
            )
            is None
        )
        assert (
            registry.async_get_issue(
                DOMAIN, f"{ISSUE_NO_ACTIVE_MONTHS}_timed_charge_{ENTRY_ID}"
            )
            is not None
        )
    finally:
        await coordinator.async_shutdown()


def test_tariff_switch_cannot_reactivate_an_inactive_bridge_preset() -> None:
    options = options_for_tariff(
        {
            CONF_ECONOMICS_TARIFF_TYPE: TariffType.DYNAMIC,
            CONF_FIXED_TIME_CHARGE_ENABLED: True,
            CONF_FIXED_TIME_CHARGE_START: "02:00:00",
            CONF_DASHBOARD_TARIFF_PROFILES: {
                TariffType.TIME_OF_USE: {CONF_BRIDGE_CHARGE_ENABLED: True},
            },
        },
        TariffType.TIME_OF_USE,
    )
    assert bridge_configuration_error(options) is None
