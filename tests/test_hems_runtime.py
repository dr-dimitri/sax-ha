"""Cross-boundary runtime regressions for REQ-HEMS-RUNTIME and both tariffs."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from time import monotonic
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from custom_components.sax_power.application.hems_runtime import (
    HemsExecution,
    HemsRuntime,
)
from custom_components.sax_power.application.hems_tariffs import timed_constraints
from custom_components.sax_power.const import PRICE_STRATEGY_ADAPTIVE
from custom_components.sax_power.domain.hems import (
    ChargeInterval,
    EnergyPlan,
    LoadForecast,
    PlanStatus,
    PvForecast,
)
from custom_components.sax_power.price_optimizer import PriceSlot, SaxPricePlanner

from .test_month_switch_response import coordinator as coordinator

NOW = datetime(2026, 9, 12, 2, tzinfo=UTC)
MODULE = "custom_components.sax_power.application.hems_runtime"


@pytest.fixture
async def runtime(coordinator, freezer):
    freezer.move_to(NOW)
    await coordinator.hass.config.async_set_time_zone("UTC")
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_mode = "adaptive"
    coordinator._timed_charge_start = time(0)
    coordinator._timed_charge_end = time(6)
    coordinator._timed_charge_min_soc = 10
    coordinator._timed_charge_max_soc = 90
    coordinator._max_soc = 90
    coordinator._timed_charge_months = set(range(1, 13))
    coordinator._basic_last_read = monotonic()
    coordinator._basic_read_failed = False
    coordinator._extended_available = True
    coordinator.data.update(
        soc=20,
        battery_capacity=10000,
        battery_soc_min=0,
        battery_discharge_power_available=4600,
    )
    instance = coordinator.hems
    instance.history = MagicMock()
    instance.history.async_start = AsyncMock()
    instance.history.async_stop = AsyncMock()
    instance.history.async_refresh = AsyncMock(return_value=_load())
    store = MagicMock()
    store.async_load = AsyncMock(return_value=None)
    store.async_save = AsyncMock()
    instance._execution_store = store
    coordinator.async_apply_price_plan = AsyncMock()
    await instance.async_start()
    yield instance


def _load():
    return LoadForecast(
        generated_at=NOW,
        evaluated_through=NOW,
        quality_reason="insufficient_history",
        model_start=NOW - timedelta(hours=2),
        model_end=NOW + timedelta(hours=8),
    )


def _plan(status=PlanStatus.PLANNED, *, energy=1.0, target=40, end=None):
    return EnergyPlan(
        decision_id="test-plan",
        revision="0",
        evaluated_at=NOW,
        valid_until=NOW + timedelta(minutes=10),
        status=status,
        reason_codes=(
            "insufficient_history" if status is PlanStatus.FALLBACK else "night_bridge",
        ),
        intervals=(
            (ChargeInterval(NOW, end or NOW + timedelta(minutes=5), energy),)
            if status is PlanStatus.PLANNED
            else ()
        ),
        planned_grid_kwh=energy if status is PlanStatus.PLANNED else None,
        target_soc=target,
    )


def _execution_ready(runtime, plan=None):
    runtime.load = _load()
    runtime.plan = plan or _plan()


def test_single_timer_regular_time_comes_from_backend(runtime):
    cancel = MagicMock()
    with (
        patch(
            f"{MODULE}.async_track_point_in_utc_time", return_value=cancel
        ) as schedule,
        patch.object(runtime, "request_evaluation") as evaluate,
    ):
        runtime.configuration_changed()
        runtime.configuration_changed()
        assert schedule.call_count == 1
        assert evaluate.call_count == 1
        assert runtime.next_evaluation_at == NOW + timedelta(seconds=300)
        with patch(
            f"{MODULE}.dt_util.utcnow", return_value=NOW + timedelta(seconds=300)
        ):
            runtime._tick(NOW + timedelta(seconds=300))
        assert schedule.call_count == 2
        assert runtime.next_evaluation_at == NOW + timedelta(seconds=600)
        runtime.coordinator._timed_charge_enabled = False
        runtime.configuration_changed()
        assert runtime.next_evaluation_at is None
        assert cancel.called


async def test_source_event_burst_has_one_active_evaluation_and_one_followup(runtime):
    entered, release = asyncio.Event(), asyncio.Event()
    calls = 0
    active = 0
    maximum = 0

    async def blocked(revision):
        nonlocal calls, active, maximum
        calls += 1
        active += 1
        maximum = max(maximum, active)
        entered.set()
        await release.wait()
        active -= 1

    with patch.object(runtime, "_evaluate", side_effect=blocked):
        runtime.request_evaluation()
        await entered.wait()
        for _ in range(10):
            runtime.request_evaluation()
        release.set()
        await runtime._task
    assert calls == 2
    assert maximum == 1


async def test_stale_revision_after_source_await_cannot_publish_or_apply(runtime):
    entered, release = asyncio.Event(), asyncio.Event()

    async def blocked(as_of):
        entered.set()
        await release.wait()
        return _load()

    runtime.history.async_refresh.side_effect = blocked
    task = asyncio.create_task(runtime._evaluate(runtime._revision))
    await entered.wait()
    runtime._revision += 1
    release.set()
    await task
    assert runtime.plan is None
    runtime.coordinator.async_apply_price_plan.assert_not_awaited()


@pytest.mark.parametrize("offset", [300, 600, 601])
def test_fast_execution_stops_at_interval_or_lease_boundary(runtime, offset):
    _execution_ready(runtime)
    assert runtime.execution(NOW, runtime.coordinator.data).charge
    assert not runtime.execution(
        NOW + timedelta(seconds=offset), runtime.coordinator.data
    ).charge


def test_expired_lease_requests_one_replan_before_regular_five_minute_tick(runtime):
    """A permission boundary cannot make a short future charge window disappear."""
    _execution_ready(runtime)
    with patch.object(runtime, "request_evaluation") as replan:
        for offset in (600, 602, 604):
            result = runtime.execution(
                NOW + timedelta(seconds=offset), runtime.coordinator.data
            )
            assert not result.charge
        replan.assert_called_once()


def test_fast_execution_stops_at_actual_quantity_without_waiting_five_minutes(runtime):
    _execution_ready(runtime)
    runtime._delivered_kwh = 1
    assert not runtime.execution(
        NOW + timedelta(seconds=20), runtime.coordinator.data
    ).charge


@pytest.mark.parametrize(
    ("energy", "soc", "active", "expected"),
    [
        (0.049, 20, False, False),
        (0.05, 20, False, True),
        (0.01, 10, False, True),
        (0.01, 20, True, True),
    ],
)
def test_start_threshold_preserves_empty_bridge_and_existing_charge(
    runtime, energy, soc, active, expected
):
    """Stabilize small new commands without weakening mandatory stop boundaries."""
    _execution_ready(runtime, _plan(energy=energy))
    runtime.coordinator.data["soc"] = soc
    runtime.coordinator._timed_charge_active = active
    result = runtime.execution(NOW, runtime.coordinator.data)
    assert result.charge is expected
    if not expected:
        assert result.reason == "below_start_threshold"
    assert not runtime.execution(
        NOW + timedelta(minutes=5), runtime.coordinator.data
    ).charge


@pytest.mark.parametrize("soc", [40, 60, None, float("nan")])
def test_target_or_missing_soc_cannot_continue_charging(runtime, soc):
    _execution_ready(runtime)
    runtime.coordinator.data["soc"] = soc
    assert not runtime.execution(NOW, runtime.coordinator.data).charge


def test_fallback_uses_strict_minimum_then_latched_target(runtime):
    _execution_ready(runtime, _plan(PlanStatus.FALLBACK))
    runtime.coordinator.data["soc"] = 10
    assert not runtime.execution(NOW, runtime.coordinator.data).charge
    runtime.coordinator.data["soc"] = 9
    assert runtime.execution(NOW, runtime.coordinator.data).charge
    runtime.coordinator.data["soc"] = 15
    assert runtime.execution(
        NOW + timedelta(seconds=5), runtime.coordinator.data
    ).charge
    runtime.coordinator.data["soc"] = 90
    assert not runtime.execution(
        NOW + timedelta(seconds=10), runtime.coordinator.data
    ).charge


def test_recovered_forecast_retires_old_fallback_arming(runtime):
    """REQ-HEMS-RUNTIME: another data loss cannot resurrect a replaced target."""
    _execution_ready(runtime, _plan(PlanStatus.FALLBACK))
    runtime.coordinator.data["soc"] = 5
    assert runtime.execution(NOW, runtime.coordinator.data).charge
    original_deadline = runtime._execution_deadline
    runtime.coordinator.data["soc"] = 20
    runtime.plan = _plan(PlanStatus.NO_NEED, energy=0, target=20)
    assert not runtime.execution(
        NOW + timedelta(seconds=5), runtime.coordinator.data
    ).charge
    runtime.plan = _plan(PlanStatus.FALLBACK)
    assert not runtime.execution(
        NOW + timedelta(seconds=10), runtime.coordinator.data
    ).charge
    # Recovery must not secretly grant a fresh quantity/time budget either.
    assert runtime._execution_deadline == original_deadline


def test_fallback_obeys_month_and_window_without_changing_saved_mode(runtime):
    _execution_ready(runtime, _plan(PlanStatus.FALLBACK))
    runtime.coordinator.data["soc"] = 5
    runtime.coordinator._timed_charge_months = {1, 4, 12}
    assert not runtime.execution(NOW, runtime.coordinator.data).charge
    assert runtime.coordinator.timed_charge_mode == "adaptive"
    runtime.coordinator._timed_charge_months.add(9)
    runtime.coordinator._timed_charge_start = time(3)
    assert not runtime.execution(NOW, runtime.coordinator.data).charge


def test_outside_model_scope_cannot_run_fallback(runtime):
    _execution_ready(runtime, _plan(PlanStatus.FALLBACK))
    runtime.load = LoadForecast(model_start=NOW - timedelta(hours=8), model_end=NOW)
    runtime.coordinator.data["soc"] = 5
    result = runtime.execution(NOW, runtime.coordinator.data)
    assert not result.charge
    assert result.reason == "outside_model_scope"


def test_zero_need_cannot_start_calibration(runtime):
    _execution_ready(runtime, _plan(PlanStatus.NO_NEED, energy=0, target=20))
    runtime.coordinator._cell_calibration_active = True
    result = runtime.execution(NOW, runtime.coordinator.data)
    assert not result.charge
    assert not result.calibration


def test_acknowledged_calibration_can_continue_past_normal_need(runtime):
    _execution_ready(runtime)
    runtime.coordinator._cell_calibration_active = True
    assert runtime.execution(NOW, runtime.coordinator.data).calibration
    runtime.acknowledged(True)
    runtime.plan = _plan(PlanStatus.NO_NEED, energy=0, target=20)
    result = runtime.execution(NOW + timedelta(seconds=5), runtime.coordinator.data)
    assert result.charge
    assert result.target_soc == 100
    assert result.calibration


@pytest.mark.parametrize("previous_plan", ["valid", "expired", "missing"])
def test_calibration_cannot_resume_next_night_without_new_positive_need(
    runtime, previous_plan
):
    """A long cheap window does not carry a calibration cause across daylight."""
    runtime.coordinator._timed_charge_end = time(23)
    runtime.coordinator._cell_calibration_active = True
    runtime.coordinator.data["ic_max_power_reference"] = 400
    _execution_ready(runtime)
    assert runtime.execution(NOW, runtime.coordinator.data).calibration
    runtime.acknowledged(True)
    model_end = runtime.load.model_end
    runtime.plan = replace(
        _plan(PlanStatus.NO_NEED, energy=0, target=20),
        valid_until=model_end + timedelta(minutes=5),
    )
    if previous_plan == "expired":
        runtime.plan = _plan()
    elif previous_plan == "missing":
        runtime.plan = None
    assert not runtime.execution(model_end, runtime.coordinator.data).charge
    assert not runtime._calibration_proof
    next_night = NOW + timedelta(hours=18)
    runtime.load = LoadForecast(
        model_start=next_night,
        model_end=next_night + timedelta(hours=14),
    )
    runtime.plan = replace(
        _plan(PlanStatus.NO_NEED, energy=0, target=20),
        evaluated_at=next_night,
        valid_until=next_night + timedelta(minutes=5),
    )
    result = runtime.execution(next_night, runtime.coordinator.data)
    assert not result.charge
    assert not result.calibration


async def test_shutdown_drains_active_work_and_removes_timer(runtime):
    entered, release = asyncio.Event(), asyncio.Event()

    async def active(revision):
        entered.set()
        await release.wait()

    cancel = MagicMock()
    runtime._remove_timer = cancel
    runtime.next_evaluation_at = NOW + timedelta(minutes=5)
    with patch.object(runtime, "_evaluate", side_effect=active):
        runtime.request_evaluation()
        await entered.wait()
        shutdown = asyncio.create_task(runtime.async_shutdown())
        await asyncio.sleep(0)
        assert not shutdown.done()
        assert runtime.next_evaluation_at is None
        release.set()
        await shutdown
    cancel.assert_called_once()
    runtime.history.async_stop.assert_awaited_once()
    assert runtime._task is None


async def test_shutdown_cancels_history_read_before_waiting_for_evaluation(runtime):
    """A source read is cancellable; only a device ACK needs to be drained."""
    entered = asyncio.Event()
    response = asyncio.get_running_loop().create_future()

    async def read(as_of):
        entered.set()
        return await asyncio.shield(response)

    async def stop():
        response.cancel()

    runtime.history.async_refresh.side_effect = read
    runtime.history.async_stop.side_effect = stop
    runtime.request_evaluation()
    await entered.wait()
    try:
        await asyncio.wait_for(runtime.async_shutdown(), 0.5)
    finally:
        response.cancel()
    assert runtime._task is None
    assert runtime.plan is None
    runtime.coordinator.async_apply_price_plan.assert_not_awaited()


async def test_device_reset_precedes_slow_hems_cleanup(runtime):
    """Source or Store latency during unload must not prolong a negative setpoint."""
    cleanup_entered, release_cleanup = asyncio.Event(), asyncio.Event()

    async def cleanup():
        cleanup_entered.set()
        await release_cleanup.wait()

    with (
        patch.object(runtime, "async_shutdown", side_effect=cleanup),
        patch.object(runtime.coordinator, "async_stop_sun_charge") as reset,
    ):
        shutdown = asyncio.create_task(runtime.coordinator.async_shutdown())
        await cleanup_entered.wait()
        try:
            reset.assert_awaited_once()
            assert not shutdown.done()
        finally:
            release_cleanup.set()
            await shutdown
    await runtime.async_shutdown()


def test_month_boundary_uses_current_local_month_and_keeps_selected_months():
    now = datetime(2026, 9, 30, 23, 50, tzinfo=UTC)
    result = timed_constraints(
        now, start=time(22), end=time(3), months={1, 4, 9}, time_zone=UTC
    )
    assert result.charge_windows[0].start == now
    assert result.charge_windows[0].end == datetime(2026, 10, 1, tzinfo=UTC)


def test_fall_dst_preserves_both_occurrences_of_allowed_clock_hour():
    zone = ZoneInfo("Europe/Berlin")
    now = datetime(2026, 10, 25, 0, tzinfo=UTC)
    result = timed_constraints(
        now, start=time(2), end=time(3), months={10}, time_zone=zone
    )
    assert result.charge_windows[0].start == now
    assert result.charge_windows[0].end == now + timedelta(hours=2)


def _dynamic(runtime):
    coordinator = runtime.coordinator
    coordinator._timed_charge_enabled = False
    coordinator._price_charge_enabled = True
    coordinator._price_charge_strategy = PRICE_STRATEGY_ADAPTIVE
    coordinator._price_charge_hours = 1
    coordinator._price_charge_max_price = 0.2
    coordinator._price_charge_neutral_price = 0.3
    return coordinator.price_planner


def test_adaptive_budget_is_not_refilled_by_repeat_evaluation_or_restart(runtime):
    planner = _dynamic(runtime)
    slots = [PriceSlot(NOW, NOW + timedelta(hours=4), 0.1)]
    planner.adaptive_constraints(NOW, slots)
    planner.adaptive_allocate(
        NOW, (ChargeInterval(NOW, NOW + timedelta(minutes=30), 1),)
    )
    after = NOW + timedelta(minutes=20)
    assert planner.adaptive_constraints(after, slots).max_charge_seconds == 2400
    assert planner.adaptive_constraints(after, slots).max_charge_seconds == 2400
    restored = SaxPricePlanner(runtime.hass, runtime.coordinator)
    restored._cycle_state = planner._cycle_state
    assert restored.adaptive_constraints(after, slots).max_charge_seconds == 2400


def test_cheap_pv_wait_window_crosses_budget_anchor_but_execution_does_not(runtime):
    planner = _dynamic(runtime)
    planner.adaptive_constraints(NOW - timedelta(hours=23), [])
    slots = [PriceSlot(NOW, NOW + timedelta(hours=4), 0.1)]
    constraints = planner.adaptive_constraints(NOW, slots)
    assert constraints.cheap_windows[0].end == NOW + timedelta(hours=4)
    assert constraints.charge_windows[0].end == NOW + timedelta(hours=1)


def test_dynamic_fallback_never_enables_timed_tariff_or_ignores_price_cap(runtime):
    _dynamic(runtime)
    _execution_ready(runtime, _plan(PlanStatus.FALLBACK))
    runtime.coordinator.data["soc"] = 5
    with patch.object(
        runtime,
        "_prices",
        return_value=[PriceSlot(NOW, NOW + timedelta(hours=1), 0.25)],
    ):
        assert not runtime.execution(NOW, runtime.coordinator.data).charge
    assert not runtime.coordinator.timed_charge_enabled
    assert runtime.coordinator.price_charge_enabled


def test_fallback_deadline_and_remaining_quantity_never_refill_on_recheck(runtime):
    _execution_ready(runtime, _plan(PlanStatus.FALLBACK))
    runtime.coordinator.data["soc"] = 5
    assert runtime.execution(NOW, runtime.coordinator.data).charge
    deadline = runtime._execution_deadline
    limit = runtime._execution_limit_kwh
    assert deadline is not None and limit is not None
    assert runtime.execution(
        NOW + timedelta(seconds=20), runtime.coordinator.data
    ).charge
    assert runtime._execution_deadline == deadline
    assert runtime._execution_limit_kwh == limit
    runtime._execution_delivered_kwh = limit
    assert not runtime.execution(
        NOW + timedelta(seconds=30), runtime.coordinator.data
    ).charge
    assert runtime._execution_limit_kwh == limit


@pytest.mark.parametrize("retired", ["consumed", "recovered"])
async def test_restart_does_not_restore_a_retired_fallback_quantity(runtime, retired):
    _execution_ready(runtime, _plan(PlanStatus.FALLBACK))
    runtime.coordinator.data["soc"] = 5
    assert runtime.execution(NOW, runtime.coordinator.data).charge
    if retired == "consumed":
        runtime._execution_delivered_kwh = runtime._execution_limit_kwh
    saved = runtime._persisted()
    restored = HemsRuntime(runtime.coordinator)
    restored.history = MagicMock()
    restored.history.async_start = AsyncMock()
    restored.history.async_stop = AsyncMock()
    restored._execution_store = MagicMock()
    restored._execution_store.async_load = AsyncMock(return_value=saved)
    restored._execution_store.async_save = AsyncMock()
    await restored.async_start()
    assert restored.plan is None
    _execution_ready(restored, _plan(PlanStatus.FALLBACK))
    if retired == "recovered":
        runtime.coordinator.data["soc"] = 20
        restored.plan = _plan(PlanStatus.NO_NEED, energy=0, target=20)
        assert not restored.execution(
            NOW + timedelta(seconds=10), runtime.coordinator.data
        ).charge
        restored.plan = _plan(PlanStatus.FALLBACK)
    assert not restored.execution(
        NOW + timedelta(seconds=20), runtime.coordinator.data
    ).charge
    assert restored._execution_limit_kwh == saved["limit_kwh"]
    assert restored._execution_deadline.isoformat() == saved["deadline"]
    await restored.async_shutdown()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        (None, None),
        ("deadline", "not-a-timestamp"),
        ("deadline", "2026-09-12T05:00:00"),
        ("deadline", None),
        ("deadline", 123),
        ("delivered_kwh", -0.01),
        ("delivered_kwh", float("nan")),
        ("limit_kwh", -1),
        ("limit_kwh", None),
        ("limit_kwh", float("nan")),
        ("target_soc", 101),
        ("target_soc", None),
    ],
)
async def test_execution_checkpoint_is_validated_before_restoring_permission(
    runtime, key, value
):
    """A malformed checkpoint must not partially restore a 100%-charge trigger."""
    coordinator = runtime.coordinator
    coordinator._cell_calibration_active = True
    coordinator.data["soc"] = 5
    _execution_ready(runtime, _plan(PlanStatus.FALLBACK))
    assert runtime.execution(NOW, coordinator.data).calibration
    runtime.acknowledged(True)
    saved = runtime._persisted()
    if key is not None:
        saved[key] = value
    restored = HemsRuntime(coordinator)
    restored.history = MagicMock()
    restored.history.async_start = AsyncMock()
    restored.history.async_stop = AsyncMock()
    restored._execution_store = MagicMock()
    restored._execution_store.async_load = AsyncMock(return_value=saved)
    restored._execution_store.async_save = AsyncMock()
    await restored.async_start()
    try:
        valid = key is None
        assert restored._calibration_proof is valid
        assert restored._fallback_armed is valid
        assert restored.plan is None
        if not valid:
            assert restored._execution_limit_kwh is None
            assert restored._execution_deadline is None
            assert restored._execution_delivered_kwh == 0
        coordinator.data["soc"] = 20
        _execution_ready(restored, _plan(PlanStatus.NO_NEED, energy=0, target=20))
        result = restored.execution(NOW + timedelta(seconds=10), coordinator.data)
        assert result.charge is valid
        assert result.calibration is valid
        if not valid:
            save = restored._execution_store.async_delay_save
            save.assert_called_once()
            repaired = save.call_args.args[0]()
            assert repaired["calibration_proof"] is False
            assert repaired["fallback_armed"] is False
    finally:
        await restored.async_shutdown()


async def test_measured_energy_corrects_quantized_soc_only_once(runtime):
    _execution_ready(runtime)
    coordinator = runtime.coordinator
    assert runtime.execution(NOW, coordinator.data).charge

    def sample(seconds, power):
        coordinator._high_sample_revision += 1
        coordinator._high_sample_time = 100 + seconds
        coordinator.data.update(storage_power_active=power, smartmeter_power=3600)
        with patch(
            f"{MODULE}.dt_util.utcnow", return_value=NOW + timedelta(seconds=seconds)
        ):
            runtime.observe(coordinator.data)

    for seconds in (0, 10, 20):
        sample(seconds, -3600)
    with patch.object(runtime, "request_evaluation"):
        runtime.source_changed()
    assert not runtime.execution(NOW + timedelta(seconds=20), coordinator.data).charge
    with patch(f"{MODULE}.compute_energy_plan", return_value=_plan()) as calculate:
        with patch(
            f"{MODULE}.dt_util.utcnow", return_value=NOW + timedelta(seconds=20)
        ):
            await runtime._evaluate(runtime._revision)
        first = calculate.call_args.args[0].current_soc
        with patch(
            f"{MODULE}.dt_util.utcnow", return_value=NOW + timedelta(seconds=21)
        ):
            await runtime._evaluate(runtime._revision)
        second = calculate.call_args.args[0].current_soc
        runtime.plan = _plan(PlanStatus.NO_NEED, energy=0, target=20)
        assert not runtime.execution(
            NOW + timedelta(seconds=21), coordinator.data
        ).charge
        sample(22, 0)
        sample(32, 3600)
        sample(42, 3600)
        with patch(
            f"{MODULE}.dt_util.utcnow", return_value=NOW + timedelta(seconds=42)
        ):
            await runtime._evaluate(runtime._revision)
        discharged = calculate.call_args.args[0].current_soc
    assert first == pytest.approx(20.19)
    assert second == pytest.approx(first)
    assert discharged == pytest.approx(20 + (0.019 - 0.02 / 0.95) / 10 * 100)


async def test_grid_energy_during_planner_await_counts_toward_the_accepted_plan(
    runtime,
):
    """The immutable snapshot predates this charge, so the new plan must deduct it."""
    coordinator = runtime.coordinator
    _execution_ready(runtime)
    assert runtime.execution(NOW, coordinator.data).charge
    coordinator.data.update(storage_power_active=-3600, smartmeter_power=3600)
    coordinator._high_sample_revision = 1
    coordinator._high_sample_time = 100
    runtime.observe(coordinator.data)
    entered, release = asyncio.Event(), asyncio.Event()

    async def compute(function, snapshot):
        entered.set()
        await release.wait()
        return _plan(energy=1)

    with patch.object(runtime.hass, "async_add_executor_job", side_effect=compute):
        evaluating = asyncio.create_task(runtime._evaluate(runtime._revision))
        await entered.wait()
        coordinator._high_sample_revision = 2
        coordinator._high_sample_time = 110
        with patch(
            f"{MODULE}.dt_util.utcnow", return_value=NOW + timedelta(seconds=10)
        ):
            runtime.observe(coordinator.data)
        release.set()
        await evaluating
    assert runtime.attributes["remaining_grid_kwh"] == pytest.approx(0.99)
    coordinator._high_sample_revision = 3
    coordinator._high_sample_time = 120
    with patch(f"{MODULE}.dt_util.utcnow", return_value=NOW + timedelta(seconds=20)):
        runtime.observe(coordinator.data)
    assert runtime.attributes["remaining_grid_kwh"] == pytest.approx(0.98)


@pytest.mark.parametrize("complete", [False, True])
def test_pv_coverage_contract_is_preserved_in_runtime_attributes(runtime, complete):
    runtime.pv = PvForecast(coverage_complete=complete)
    assert runtime.attributes["pv_coverage_complete"] is complete


def test_due_calibration_alone_does_not_censor_actual_free_discharge(runtime):
    coordinator = runtime.coordinator
    coordinator._cell_calibration_active = True
    coordinator._high_sample_revision = 1
    coordinator._high_sample_time = monotonic()
    coordinator.data["storage_power_active"] = 500
    coordinator.data["ic_control_mode"] = 0
    runtime.observe(coordinator.data)
    assert runtime.history.observe.call_args.kwargs["calibration_active"] is False
    assert runtime.history.observe.call_args.kwargs["discharge_blocked"] is False


@pytest.mark.parametrize("available", [0, -1])
def test_bms_discharge_block_censors_an_otherwise_free_night_sample(runtime, available):
    """A valid zero load requires physical discharge permission, not just mode0."""
    coordinator = runtime.coordinator
    coordinator._high_sample_revision = 1
    coordinator.data.update(
        soc=40,
        storage_power_active=0,
        ic_control_mode=0,
        battery_discharge_power_available=available,
    )
    runtime.observe(coordinator.data)
    assert runtime.history.observe.call_args.kwargs["discharge_blocked"] is True


@pytest.mark.parametrize("available", [None, float("nan")])
def test_missing_bms_discharge_permission_is_unknown_quality(runtime, available):
    coordinator = runtime.coordinator
    coordinator._high_sample_revision = 1
    coordinator.data.update(
        soc=40,
        storage_power_active=0,
        ic_control_mode=0,
        battery_discharge_power_available=available,
    )
    runtime.observe(coordinator.data)
    assert runtime.history.observe.call_args.kwargs["control_known"] is False


def test_grid_charge_accounting_ignores_house_import_and_duplicate_samples(runtime):
    coordinator = runtime.coordinator
    runtime._execution = HemsExecution(charge=True)
    coordinator.data.update(storage_power_active=-500, smartmeter_power=1500)
    coordinator._high_sample_revision = 1
    coordinator._high_sample_time = 100
    runtime.observe(coordinator.data)
    coordinator._high_sample_revision = 2
    coordinator._high_sample_time = 102
    runtime.observe(coordinator.data)
    expected = 500 * 2 / 3_600_000
    assert runtime._delivered_kwh == pytest.approx(expected)
    runtime.observe(coordinator.data)
    assert runtime._delivered_kwh == pytest.approx(expected)
    coordinator._high_sample_revision = 3
    coordinator._high_sample_time = 200
    runtime.observe(coordinator.data)
    assert runtime._delivered_kwh == pytest.approx(expected)


def test_continuous_energy_samples_cannot_postpone_execution_checkpoint(runtime):
    """REQ-HEMS-RUNTIME: charge progress must reach disk during a long charge."""
    coordinator = runtime.coordinator
    runtime._execution = HemsExecution(charge=True)
    coordinator.data.update(storage_power_active=-500, smartmeter_power=1500)
    for index in range(4):
        coordinator._high_sample_revision = index + 1
        coordinator._high_sample_time = 100 + index * 2
        runtime.observe(coordinator.data)
    save = runtime._execution_store.async_delay_save
    assert save.call_count == 1
    callback, delay = save.call_args.args
    assert delay <= 5
    stored = callback()
    assert stored["delivered_kwh"] == pytest.approx(500 * 6 / 3_600_000)
    coordinator._high_sample_revision = 5
    coordinator._high_sample_time = 108
    runtime.observe(coordinator.data)
    assert save.call_count == 2


def test_fast_execution_refuses_stale_soc_before_poll_failure_flag(runtime):
    _execution_ready(runtime)
    runtime.coordinator._basic_last_read = monotonic() - 100
    assert not runtime.coordinator._basic_read_failed
    assert not runtime.execution(NOW, runtime.coordinator.data).charge


@pytest.mark.parametrize("minimum", [None, float("nan")])
async def test_missing_bms_minimum_cannot_become_invented_zero_in_plan(
    runtime, minimum
):
    runtime.coordinator.data["battery_soc_min"] = minimum
    await runtime._evaluate(runtime._revision)
    assert runtime.plan is not None
    assert runtime.plan.status is PlanStatus.BLOCKED


@pytest.mark.parametrize("minimum", [None, float("nan")])
def test_newly_missing_bms_minimum_stops_existing_lease(runtime, minimum):
    _execution_ready(runtime)
    runtime.coordinator.data["battery_soc_min"] = minimum
    assert not runtime.execution(NOW, runtime.coordinator.data).charge


async def test_missing_user_reserve_cannot_become_an_invented_plan_default(runtime):
    """REQ-HEMS-TIMED-CHARGE: plan with the configured MinSOC or explain its lack."""
    runtime.coordinator._timed_charge_min_soc = None
    await runtime._evaluate(runtime._revision)
    assert runtime.plan is not None
    assert runtime.plan.status is PlanStatus.BLOCKED
    assert not runtime.execution(NOW, runtime.coordinator.data).charge
