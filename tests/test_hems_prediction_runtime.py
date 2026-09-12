"""Integration regressions for candidate selection, live quality and issue clocks."""

from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import replace
from datetime import datetime, timedelta
from time import monotonic
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.sax_power.application.hems_prediction import HemsPrediction
from custom_components.sax_power.const import (
    CONF_HEMS_ARCHIVE_ENABLED,
    CONF_HEMS_FORECAST_MODE,
    CONF_HEMS_HISTORY_DAYS,
    CONF_HEMS_LIVE_ADJUSTMENT,
)
from custom_components.sax_power.domain.hems import (
    EnergySlot,
    LoadForecast,
    PlanningSnapshot,
    PlanStatus,
    PvForecast,
    TariffConstraints,
)
from custom_components.sax_power.domain.hems_evaluation import (
    ForecastSeriesRecord,
    GateResult,
    energy_between,
    validate_record,
)
from custom_components.sax_power.domain.hems_live import LIVE_MODEL_KEY
from custom_components.sax_power.domain.hems_load import (
    DischargeObservation,
    LoadVariants,
    NightSpan,
)
from custom_components.sax_power.domain.hems_uncertainty import UncertaintyResult
from custom_components.sax_power.infrastructure.hems_history import HemsHistory

from .test_hems_runtime import NOW, _dynamic, _plan
from .test_hems_runtime import coordinator as coordinator
from .test_hems_runtime import runtime as runtime

MODULE = "custom_components.sax_power.application.hems_runtime"
NIGHT = NightSpan(NOW - timedelta(hours=2), NOW + timedelta(hours=4))


def _forecast(at=NOW, power=2.0, method="legacy"):
    end = NIGHT.end + timedelta(hours=4)
    return LoadForecast(
        generated_at=at,
        evaluated_through=at,
        intervals=(
            EnergySlot(at, end, power * (end - at).total_seconds() / 3600, (method,)),
        ),
        nights_count=4,
        observed_hours=12,
        coverage=0.4,
        model_start=NIGHT.start,
        model_end=end,
    )


def _observations(end: datetime, *, power=2.0):
    start = end - timedelta(minutes=45)
    result = []
    while start < end:
        stop = min(start + timedelta(minutes=5), end)
        result.append(
            DischargeObservation(
                start, stop, power * (stop - start).total_seconds() / 3600, "valid"
            )
        )
        start = stop
    return tuple(result)


def _history(at=NOW, *, days=7):
    history = MagicMock(spec=HemsHistory)
    history.variants = LoadVariants(
        _forecast(at),
        _forecast(at, 1.0, "weighted_slot"),
        NIGHT,
        history_days=days,
        candidate_key=f"weighted-v1:{days}d",
        available_history_days=days,
    )
    history.observations.side_effect = lambda as_of, **kwargs: _observations(as_of)
    history.free_discharge.return_value = True
    return history


def _mock_archive(prediction, approved):
    async def gate(baseline_key, candidate_key, *, phase, horizon, as_of):
        return GateResult(
            phase in approved,
            "approved" if phase in approved else "insufficient_validation_nights",
            baseline_key,
            candidate_key,
            phase,
            horizon,
            as_of - timedelta(days=20),
            as_of,
            nights=14,
            observed_hours=14,
            retained=not prediction.enabled and phase in approved,
        )

    prediction.archive.async_gate = AsyncMock(side_effect=gate)
    prediction.archive.async_record = AsyncMock()
    prediction.archive.async_summary = AsyncMock(return_value={})
    prediction.archive.async_uncertainty = AsyncMock(
        return_value=UncertaintyResult("unavailable", "insufficient_training_nights")
    )


def _options(*, archive=True, mode="auto", days=7, live=False):
    return {
        CONF_HEMS_ARCHIVE_ENABLED: archive,
        CONF_HEMS_FORECAST_MODE: mode,
        CONF_HEMS_HISTORY_DAYS: str(days),
        CONF_HEMS_LIVE_ADJUSTMENT: live,
    }


@pytest.fixture
async def predictor(hass, freezer):
    freezer.move_to(NOW)
    await hass.config.async_set_time_zone("UTC")
    instance = HemsPrediction(hass, "prediction-runtime")
    approved = set()
    _mock_archive(instance, approved)
    yield instance, approved


async def _prepare(prediction, history, at=NOW, *, free=True):
    return await prediction.async_prepare(
        history,
        history.variants.baseline,
        as_of=at,
        max_discharge_power_w=4600,
        free_discharge=free,
    )


def _snapshot(load, at=NOW):
    return PlanningSnapshot(
        as_of=at,
        revision="test",
        load=load,
        pv=PvForecast(),
        tariff=TariffConstraints(),
        current_soc=20,
        soc_measured_at=at,
        capacity_kwh=10,
        charge_power_w=4600,
        reserve_soc=10,
        max_soc=90,
    )


async def test_default_predictor_keeps_baseline_archive_off_and_live_off(predictor):
    prediction, approved = predictor
    approved.update(("night", "dawn"))
    prediction.configure({}, NOW)
    history = _history()
    selected = await _prepare(prediction, history)
    assert selected is history.variants.baseline
    assert prediction.history_days == 7
    assert prediction.mode == "observe"
    assert prediction.enabled is False
    assert prediction.live_enabled is False
    assert prediction.live_result is None
    assert not prediction.attributes["candidate_active"]
    await prediction.async_record(
        _snapshot(selected), _plan(PlanStatus.NO_NEED), issued_at=NOW
    )
    prediction.archive.async_record.assert_not_awaited()


@pytest.mark.parametrize(
    "approved_phases", [(), ("night",), ("dawn",), ("night", "dawn")]
)
async def test_phase_selection_uses_only_its_own_gate(predictor, approved_phases):
    prediction, approved = predictor
    approved.update(approved_phases)
    prediction.configure(_options(), NOW)
    history = _history()
    selected = await _prepare(prediction, history)
    assert energy_between(selected.intervals, NOW, NIGHT.end) == pytest.approx(
        4 if "night" in approved else 8
    )
    assert energy_between(
        selected.intervals, NIGHT.end, NIGHT.end + timedelta(hours=4)
    ) == pytest.approx(4 if "dawn" in approved else 8)
    assert prediction.attributes["candidate_active"] is ("night" in approved)
    assert [
        c.kwargs["phase"] for c in prediction.archive.async_gate.call_args_list
    ] == ["night", "dawn"]


async def test_live_combination_requires_its_complete_key_not_profile_only_approval(
    predictor,
):
    prediction, approved = predictor
    approved.update(("night", "dawn"))
    prediction.configure(_options(live=False), NOW)
    history = _history()
    await _prepare(prediction, history)
    profile_key = prediction.candidate_key
    prediction.configure(_options(live=True), NOW)
    approved.clear()
    selected = await _prepare(prediction, history)
    assert prediction.candidate_key != profile_key
    key = json.loads(prediction.candidate_key)
    assert key["live_version"] == LIVE_MODEL_KEY
    assert "decay-on-censor" in key["live_policy"]
    assert json.loads(prediction.raw_key)["live_version"] == "off"
    assert selected is history.variants.baseline
    assert not prediction.attributes["candidate_active"]


async def test_approved_28_day_candidate_survives_missing_legacy_quality(predictor):
    prediction, approved = predictor
    approved.update(("night", "dawn"))
    prediction.configure(_options(days=28), NOW)
    history = _history(days=28)
    history.variants = replace(
        history.variants,
        baseline=replace(
            history.variants.baseline,
            intervals=(),
            quality_reason="insufficient_history",
        ),
    )
    selected = await _prepare(prediction, history)
    assert selected.quality_reason is None
    assert energy_between(
        selected.intervals, NOW, NIGHT.end + timedelta(hours=4)
    ) == pytest.approx(8)
    assert all("weighted_slot" in slot.quality_flags for slot in selected.intervals)
    assert json.loads(prediction.baseline_key)["history_days"] == 7
    assert json.loads(prediction.candidate_key)["history_days"] == 28
    assert prediction.attributes["candidate_active"]


async def test_missing_legacy_dawn_is_not_invented_from_night_approval(predictor):
    prediction, approved = predictor
    approved.add("night")
    prediction.configure(_options(days=28), NOW)
    history = _history(days=28)
    history.variants = replace(
        history.variants,
        baseline=replace(
            history.variants.baseline,
            intervals=(),
            quality_reason="insufficient_history",
        ),
    )
    selected = await _prepare(prediction, history)
    assert selected.intervals[-1].end == NIGHT.end
    assert (
        energy_between(selected.intervals, NIGHT.end, NIGHT.end + timedelta(hours=1))
        is None
    )


async def test_invalid_candidate_keeps_applied_key_and_metadata_on_actual_baseline(
    predictor,
):
    prediction, approved = predictor
    approved.update(("night", "dawn"))
    prediction.configure(_options(), NOW)
    history = _history()
    history.variants = replace(
        history.variants,
        candidate=replace(
            history.variants.candidate, intervals=(), quality_reason="history_invalid"
        ),
    )
    selected = await _prepare(prediction, history)
    assert selected is history.variants.baseline
    assert prediction.applied_key == prediction.baseline_key
    assert not prediction.attributes["candidate_active"]


def _install_live_sources(prediction, *, future=False):
    def source(start, end, model_key):
        records = [
            ForecastSeriesRecord(
                start - timedelta(seconds=1), _forecast(start, 1.0).intervals, model_key
            )
        ]
        if future:
            records.append(
                ForecastSeriesRecord(
                    end + timedelta(seconds=1),
                    _forecast(start, 99).intervals,
                    model_key,
                )
            )
        return tuple(records)

    prediction.archive.archived_baselines = MagicMock(side_effect=source)


async def test_archive_off_stops_new_live_anchors_and_preserves_original_expiry(
    predictor,
):
    prediction, approved = predictor
    approved.update(("night", "dawn"))
    prediction.configure(_options(live=True), NOW - timedelta(minutes=45))
    _install_live_sources(prediction)
    await _prepare(
        prediction, _history(NOW - timedelta(minutes=45)), NOW - timedelta(minutes=45)
    )
    await _prepare(prediction, _history())
    assert prediction.live_result.anchor == NOW
    assert prediction.live_result.correction_kw == pytest.approx(0.5)
    prediction.configure(_options(live=True, archive=False), NOW + timedelta(minutes=5))
    await _prepare(
        prediction, _history(NOW + timedelta(minutes=5)), NOW + timedelta(minutes=5)
    )
    assert prediction.live_result.anchor == NOW
    assert prediction.live_result.expires_at == NOW + timedelta(hours=1)
    assert prediction.live_result.reason == "archive_disabled"
    await _prepare(
        prediction, _history(NOW + timedelta(hours=1)), NOW + timedelta(hours=1)
    )
    assert prediction.live_result.correction_kw is None
    assert not prediction.attributes["live"]["active"]


async def test_night_only_live_approval_is_inactive_in_dawn(predictor):
    prediction, approved = predictor
    approved.add("night")
    anchor = NIGHT.end - timedelta(minutes=15)
    prediction.configure(_options(live=True), anchor - timedelta(minutes=45))
    _install_live_sources(prediction)
    await _prepare(
        prediction,
        _history(anchor - timedelta(minutes=45)),
        anchor - timedelta(minutes=45),
    )
    await _prepare(prediction, _history(anchor), anchor)
    assert prediction.attributes["live"]["active"]
    dawn = NIGHT.end + timedelta(minutes=5)
    history = _history(dawn)
    selected = await _prepare(prediction, history, dawn)
    assert prediction.live_result.anchor == anchor
    assert prediction.live_result.correction_kw is not None
    assert selected.intervals == history.variants.baseline.intervals
    assert not prediction.attributes["live"]["active"]
    assert not prediction.attributes["candidate_active"]


async def test_later_basis_cannot_backfill_the_live_comparison(predictor):
    prediction, _ = predictor
    prediction.configure(_options(live=True), NOW - timedelta(minutes=45))
    _install_live_sources(prediction, future=True)
    await _prepare(
        prediction, _history(NOW - timedelta(minutes=45)), NOW - timedelta(minutes=45)
    )
    await _prepare(prediction, _history())
    assert prediction.live_result.expected_kwh == pytest.approx(0.75)
    assert prediction.live_result.measured_kwh == pytest.approx(1.5)
    assert prediction.live_result.correction_kw == pytest.approx(0.5)


async def test_profile_change_cannot_reuse_prior_live_anchor(predictor):
    prediction, _ = predictor
    prediction.configure(_options(live=True), NOW - timedelta(minutes=45))
    _install_live_sources(prediction)
    await _prepare(
        prediction, _history(NOW - timedelta(minutes=45)), NOW - timedelta(minutes=45)
    )
    await _prepare(prediction, _history())
    assert prediction.live_result.anchor == NOW
    prediction.configure(_options(live=True, days=28), NOW + timedelta(minutes=5))
    await _prepare(
        prediction,
        _history(NOW + timedelta(minutes=5), days=28),
        NOW + timedelta(minutes=5),
    )
    assert prediction.live_result.anchor is None


async def test_archive_record_freezes_actual_issue_clock_and_raw_version(predictor):
    prediction, _ = predictor
    prediction.configure(_options(mode="observe"), NOW)
    history = _history()
    selected = await _prepare(prediction, history)
    issued_at = NOW + timedelta(seconds=10)
    await prediction.async_record(
        _snapshot(selected), _plan(PlanStatus.NO_NEED), issued_at=issued_at
    )
    first = prediction.archive.async_record.call_args.args[0]
    validate_record(first)
    assert first.issued_at == issued_at
    assert first.data_as_of == NOW
    assert first.applied.model_key == prediction.baseline_key
    assert first.raw_profiles[1].model_key == prediction.raw_key
    assert (
        json.loads(first.raw_profiles[1].metadata_json)["generated_at"]
        == NOW.isoformat()
    )
    frozen_intervals = first.raw_profiles[1].intervals
    later = NOW + timedelta(minutes=5)
    history.variants = replace(
        history.variants, candidate=_forecast(later, 99, "weighted_slot")
    )
    await _prepare(prediction, history, later)
    await prediction.async_record(
        _snapshot(prediction.selected, later),
        _plan(PlanStatus.NO_NEED),
        issued_at=later + timedelta(seconds=10),
    )
    assert first.raw_profiles[1].intervals == frozen_intervals
    assert (
        first.raw_profiles[1].intervals
        != prediction.archive.async_record.call_args.args[0].raw_profiles[1].intervals
    )


async def test_runtime_reads_soc_and_its_freshness_after_prediction_await(
    runtime, freezer
):
    prediction = runtime.prediction
    _mock_archive(prediction, set())
    runtime.history.variants = _history().variants
    runtime.history.observations.return_value = _observations(NOW)
    runtime.history.async_refresh.return_value = runtime.history.variants.baseline
    gate = prediction.archive.async_gate.side_effect
    switched = False

    async def refresh_device(*args, **kwargs):
        nonlocal switched
        if not switched:
            switched = True
            freezer.tick(timedelta(seconds=2))
            runtime.coordinator.data = {**runtime.coordinator.data, "soc": 70}
            runtime.coordinator._basic_last_read = monotonic()
            await asyncio.sleep(0)
        return await gate(*args, **kwargs)

    prediction.archive.async_gate.side_effect = refresh_device
    with patch(
        f"{MODULE}.compute_energy_plan", return_value=_plan(PlanStatus.NO_NEED)
    ) as compute:
        await runtime._evaluate(runtime._revision)
    snapshot = compute.call_args.args[0]
    assert snapshot.current_soc == 70
    assert snapshot.soc_measured_at == snapshot.as_of
    assert snapshot.as_of == NOW + timedelta(seconds=2)


@pytest.mark.parametrize(
    "power,blocked,expected", [(-100, False, False), (0, True, False), (0, False, True)]
)
async def test_runtime_live_free_flag_uses_real_history_quality(
    runtime, power, blocked, expected
):
    history = HemsHistory(runtime.hass, "prediction-quality")
    await history.async_start()
    history.observe(
        NOW,
        storage_power_w=power,
        soc=20,
        device_min_soc=0,
        device_available=True,
        control_known=True,
        charge_active=False,
        discharge_blocked=blocked,
        calibration_active=False,
    )
    history.variants = _history().variants
    runtime.history = history
    with (
        patch.object(
            history, "async_refresh", AsyncMock(return_value=history.variants.baseline)
        ),
        patch.object(
            runtime.prediction,
            "async_prepare",
            AsyncMock(return_value=history.variants.baseline),
        ) as prepare,
        patch(f"{MODULE}.compute_energy_plan", return_value=_plan(PlanStatus.NO_NEED)),
    ):
        await runtime._evaluate(runtime._revision)
    assert prepare.call_args.kwargs["free_discharge"] is expected


async def test_runtime_publishes_actual_output_time_before_device_ack(runtime):
    prediction = runtime.prediction
    prediction.configure(_options(mode="observe"), NOW)
    _mock_archive(prediction, set())
    runtime.history.variants = _history().variants
    runtime.history.observations.return_value = _observations(NOW)
    runtime.history.async_refresh.return_value = runtime.history.variants.baseline
    clock = [NOW]

    def compute(snapshot):
        clock[0] = NOW + timedelta(seconds=10)
        return _plan(PlanStatus.NO_NEED)

    async def ack():
        clock[0] = NOW + timedelta(seconds=20)

    runtime.coordinator.async_apply_price_plan.side_effect = ack
    with (
        patch(f"{MODULE}.dt_util.utcnow", side_effect=lambda: clock[0]),
        patch(f"{MODULE}.compute_energy_plan", side_effect=compute),
    ):
        await runtime._evaluate(runtime._revision)
    record = prediction.archive.async_record.call_args.args[0]
    assert record.issued_at == NOW + timedelta(seconds=10)
    assert record.data_as_of == NOW


async def test_configuration_during_gate_await_cannot_apply_old_candidate(predictor):
    prediction, _ = predictor
    prediction.configure(_options(), NOW)
    history = _history()

    async def changed(baseline_key, candidate_key, *, phase, horizon, as_of):
        prediction.configure(_options(mode="observe", archive=False), as_of)
        return GateResult(
            True,
            "approved",
            baseline_key,
            candidate_key,
            phase,
            horizon,
            NOW - timedelta(days=20),
            as_of,
        )

    prediction.archive.async_gate.side_effect = changed
    selected = await _prepare(prediction, history)
    assert selected is history.variants.baseline
    assert not prediction.attributes["candidate_active"]


async def test_inflight_live_worker_cannot_restore_anchor_after_configuration_change(
    predictor,
):
    prediction, _ = predictor
    prediction.configure(_options(live=True), NOW - timedelta(minutes=45))
    _install_live_sources(prediction)
    await _prepare(
        prediction, _history(NOW - timedelta(minutes=45)), NOW - timedelta(minutes=45)
    )
    old_adjuster = prediction.live
    original_evaluate = old_adjuster.evaluate
    entered = asyncio.Event()
    release = threading.Event()
    loop = asyncio.get_running_loop()

    def blocked(**kwargs):
        loop.call_soon_threadsafe(entered.set)
        assert release.wait(5)
        return original_evaluate(**kwargs)

    with patch.object(old_adjuster, "evaluate", new=blocked):
        history = _history()
        task = asyncio.create_task(_prepare(prediction, history))
        try:
            await asyncio.wait_for(entered.wait(), 2)
            prediction.configure(_options(live=True, days=28), NOW)
            assert prediction.live is not old_adjuster
        finally:
            release.set()
        assert await task is history.variants.baseline
    assert prediction.live_result is None
    await _prepare(prediction, _history(days=28))
    assert prediction.live_result.anchor is None


@pytest.mark.parametrize("dynamic", [False, True])
async def test_both_tariffs_receive_same_approved_forecast_and_unchanged_reserve(
    runtime, dynamic
):
    if dynamic:
        _dynamic(runtime)
    prediction = runtime.prediction
    prediction.configure(_options(), NOW)
    _mock_archive(prediction, {"night", "dawn"})
    runtime.history.variants = _history().variants
    runtime.history.observations.return_value = _observations(NOW)
    runtime.history.async_refresh.return_value = runtime.history.variants.baseline
    with patch(
        f"{MODULE}.compute_energy_plan", return_value=_plan(PlanStatus.NO_NEED)
    ) as compute:
        await runtime._evaluate(runtime._revision)
    snapshot = compute.call_args.args[0]
    assert energy_between(
        snapshot.load.intervals, NOW, NIGHT.end + timedelta(hours=4)
    ) == pytest.approx(8)
    assert snapshot.reserve_soc == 10
    assert snapshot.max_soc == 90
    assert runtime.mode == ("dynamic" if dynamic else "timed")


async def test_revision_change_during_device_ack_prevents_stale_archive_record(runtime):
    prediction = runtime.prediction
    prediction.configure(_options(mode="observe"), NOW)
    _mock_archive(prediction, set())
    runtime.history.variants = _history().variants
    runtime.history.observations.return_value = _observations(NOW)
    runtime.history.async_refresh.return_value = runtime.history.variants.baseline

    async def changed():
        runtime._revision += 1

    runtime.coordinator.async_apply_price_plan.side_effect = changed
    with patch(f"{MODULE}.compute_energy_plan", return_value=_plan(PlanStatus.NO_NEED)):
        await runtime._evaluate(runtime._revision)
    prediction.archive.async_record.assert_not_awaited()


async def test_dawn_gate_exception_after_prior_activation_restores_baseline_identity(
    runtime,
):
    prediction = runtime.prediction
    prediction.configure(_options(), NOW)
    _mock_archive(prediction, {"night", "dawn"})
    runtime.history.variants = _history().variants
    runtime.history.observations.return_value = _observations(NOW)
    runtime.history.async_refresh.return_value = runtime.history.variants.baseline
    gate = prediction.archive.async_gate.side_effect
    with patch(
        f"{MODULE}.compute_energy_plan", return_value=_plan(PlanStatus.NO_NEED)
    ) as compute:
        await runtime._evaluate(runtime._revision)
        assert prediction.attributes["candidate_active"]
        previous_candidate_key = prediction.applied_key
        prediction.archive.async_record.reset_mock()

        async def failed_dawn(*args, **kwargs):
            if kwargs["phase"] == "dawn":
                raise OSError("archive evaluation unavailable")
            return await gate(*args, **kwargs)

        prediction.archive.async_gate.side_effect = failed_dawn
        await runtime._evaluate(runtime._revision)
    snapshot = compute.call_args.args[0]
    assert snapshot.load is runtime.history.variants.baseline
    assert prediction.selected is snapshot.load
    assert prediction.applied_key == prediction.baseline_key
    assert prediction.applied_key != previous_candidate_key
    prediction.archive.async_record.assert_not_awaited()
    assert not runtime.attributes["forecast_quality"]["candidate_active"]
    assert not runtime.attributes["forecast_quality"]["live"]["active"]


@pytest.mark.parametrize(
    "status,reason,ui_status,ui_reason",
    [
        ("reliable", "validated", "validated", "validated"),
        (
            "unavailable",
            "insufficient_training_nights",
            "unavailable",
            "insufficient_training",
        ),
        (
            "observing",
            "insufficient_validation_nights",
            "observing",
            "insufficient_validation",
        ),
        ("unavailable", "coverage_below_threshold", "unavailable", "rejected"),
        (
            "unavailable",
            "forecast_coverage_missing",
            "unavailable",
            "insufficient_coverage",
        ),
        ("stale", "validation_stale", "stale", "stale"),
    ],
)
def test_real_uncertainty_result_uses_frontend_status_and_reason_contract(
    runtime, status, reason, ui_status, ui_reason
):
    runtime.prediction.uncertainty = UncertaintyResult(
        status=status,
        reason=reason,
        expected_kwh=1.0,
        lower_kwh=0.8 if status == "reliable" else None,
        upper_kwh=1.2 if status == "reliable" else None,
        start=NOW + timedelta(hours=1),
        end=NOW + timedelta(hours=2),
        training_nights=60,
        validation_nights=30,
        hits=24,
        hit_rate=0.8,
        mean_width_kwh=0.4,
    )
    ui = runtime.attributes["forecast_quality"]["uncertainty"]
    assert ui["status"] == ui_status
    assert ui["reason"] == ui_reason
    assert ui["training_nights"] == 60
    assert ui["validation_nights"] == 30
    assert ui["empirical_coverage"] == 0.8
    if status == "reliable":
        assert (ui["expected_kwh"], ui["lower_kwh"], ui["upper_kwh"]) == (1.0, 0.8, 1.2)
