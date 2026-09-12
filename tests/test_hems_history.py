"""Quality, persistence and Recorder regressions for REQ-HEMS-LOAD-PROFILE."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.recorder import DATA_INSTANCE
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.domain.hems_load import DischargeObservation
from custom_components.sax_power.infrastructure.hems_history import (
    HemsHistory,
    _HistoryStore,
)

NOW = datetime(2026, 9, 12, 22, tzinfo=UTC)
MODULE = "custom_components.sax_power.infrastructure.hems_history"


@pytest.fixture
async def history(hass, freezer):
    freezer.move_to(NOW)
    hass.config.latitude = 52.52
    hass.config.longitude = 13.405
    await hass.config.async_set_time_zone("Europe/Berlin")
    store = MagicMock()
    store.async_load = AsyncMock(return_value=None)
    store.async_save = AsyncMock()
    with patch(f"{MODULE}._HistoryStore", return_value=store):
        instance = HemsHistory(hass, "history-entry")
    await instance.async_start()
    yield instance
    await instance.async_stop()


def observe(history, at, **changes):
    values = {
        "storage_power_w": 500.0,
        "soc": 40.0,
        "device_min_soc": 0.0,
        "device_available": True,
        "control_known": True,
        "charge_active": False,
        "discharge_blocked": False,
        "calibration_active": False,
    }
    values.update(changes)
    history.observe(at, **values)


def test_observation_integrates_power_and_coalesces_bounded_records(history):
    """REQ-HEMS-LOAD-PROFILE: no double integration from repeated cached data."""
    for seconds in range(0, 901, 30):
        observe(history, NOW - timedelta(seconds=900 - seconds))
    assert len(history._records) == 3
    assert sum(item.energy_kwh for item in history._records) == pytest.approx(0.125)
    observe(history, NOW)
    assert sum(item.energy_kwh for item in history._records) == pytest.approx(0.125)
    history._store.async_delay_save.assert_called_once()


def test_bucket_boundaries_are_exact_even_with_unaligned_samples(history):
    begin = NOW - timedelta(minutes=5, seconds=1)
    observe(history, begin)
    observe(history, begin + timedelta(seconds=30))
    assert len(history._records) == 2
    assert history._records[0].end == NOW - timedelta(minutes=5)
    assert sum(item.energy_kwh for item in history._records) == pytest.approx(
        500 / 120000
    )


@pytest.mark.parametrize(
    ("changes", "quality"),
    [
        ({"storage_power_w": 0}, "valid"),
        ({"soc": 5}, "valid"),
        ({"soc": 0}, "censored"),
        ({"soc": 5, "device_min_soc": 5}, "censored"),
        ({"charge_active": True}, "censored"),
        ({"discharge_blocked": True}, "censored"),
        ({"calibration_active": True}, "censored"),
        ({"storage_power_w": -500}, "censored"),
        ({"control_known": False}, "unknown"),
        ({"device_available": False}, "unknown"),
        ({"device_min_soc": None}, "unknown"),
        ({"soc": float("nan")}, "unknown"),
        ({"storage_power_w": float("inf")}, "unknown"),
        ({"soc": True}, "unknown"),
    ],
)
def test_quality_is_not_inferred_from_zero_or_planning_reserve(
    history, changes, quality
):
    """Min planning reserve is intentionally absent from the observation API."""
    observe(history, NOW - timedelta(seconds=2), **changes)
    observe(history, NOW, **changes)
    assert history._records[-1].quality == quality
    if quality != "valid":
        assert history._records[-1].energy_kwh == 0


def test_unknown_gap_and_control_transition_do_not_learn_zero(history):
    observe(history, NOW - timedelta(minutes=3))
    observe(history, NOW - timedelta(seconds=4))
    observe(history, NOW - timedelta(seconds=2), discharge_blocked=True)
    observe(history, NOW)
    assert [item.quality for item in history._records] == ["unknown", "censored"]
    assert all(item.energy_kwh == 0 for item in history._records)
    assert history._evaluated_through == NOW


async def test_cold_start_keeps_model_geometry_for_runtime_fallback(history):
    forecast = await history.async_refresh(NOW)
    assert forecast.quality_reason == "history_unavailable"
    assert forecast.model_start < NOW < forecast.model_end
    assert forecast.intervals == ()


async def test_daytime_cold_start_is_inactive_instead_of_fallback(history):
    forecast = await history.async_refresh(NOW - timedelta(hours=9))
    assert forecast.quality_reason == "outside_model_scope"


async def test_polar_night_has_explicit_geometry_failure(history):
    history.hass.config.latitude = 89.0
    forecast = await history.async_refresh(datetime(2026, 12, 12, 22, tzinfo=UTC))
    assert forecast.quality_reason == "unsupported_night_geometry"


async def test_first_polar_day_does_not_use_old_normal_nights_as_scope(history):
    def event(hass, kind, day):
        if day >= NOW.date():
            return None
        return datetime.combine(day, datetime.min.time(), UTC) + timedelta(
            hours=18 if kind == "sunset" else 6
        )

    with patch(f"{MODULE}.get_astral_event_date", side_effect=event):
        result = await history.async_refresh(NOW)
    assert result.quality_reason == "unsupported_night_geometry"


@pytest.mark.parametrize(
    ("zone_name", "latitude", "longitude"),
    [("Europe/Berlin", 52.52, 13.4), ("America/Los_Angeles", 34.05, -118.24)],
)
def test_astronomy_matches_local_dates_on_both_sides_of_greenwich(
    history, zone_name, latitude, longitude
):
    history.hass.config.latitude = latitude
    history.hass.config.longitude = longitude
    zone = ZoneInfo(zone_name)
    nights = history._night_spans(NOW, zone)
    assert nights
    assert all(
        n.end.astimezone(zone).date() - n.start.astimezone(zone).date()
        == timedelta(days=1)
        for n in nights
    )
    assert all(5 < (n.end - n.start).total_seconds() / 3600 < 16 for n in nights)


async def test_persisted_history_keeps_quality_but_no_restart_interval(history):
    observe(history, NOW - timedelta(seconds=2))
    observe(history, NOW)
    raw = history._serialize()
    assert raw["entry_id"] == history.entry_id
    history._store.async_load.return_value = raw
    with patch(f"{MODULE}._HistoryStore", return_value=history._store):
        restored = HemsHistory(history.hass, history.entry_id)
    await restored.async_start()
    assert restored._records == history._records
    assert restored._evaluated_through is None
    observe(restored, NOW + timedelta(seconds=30))
    assert len(restored._records) == 1
    await restored.async_stop()


@pytest.mark.parametrize(
    "raw",
    [
        None,
        [],
        {},
        {"entry_id": "other", "intervals": []},
        {"entry_id": "history-entry", "intervals": [["bad", "date", 1, "valid"]]},
    ],
)
def test_invalid_or_other_device_store_cannot_supply_evidence(history, raw):
    assert history._decode(raw) == []


def test_recorder_energy_is_primary_only_with_full_quality_proof(history):
    start = NOW - timedelta(minutes=5)
    history._records = [DischargeObservation(start, NOW, 0.04, "valid")]
    history._recorder_rows[(start, NOW)] = 0.05
    effective = history._effective_observations()
    assert len(effective) == 1
    assert effective[0].energy_kwh == 0.05
    history._records = [DischargeObservation(start, NOW, 0, "censored")]
    assert history._effective_observations()[0].quality == "censored"
    assert history._effective_observations()[0].energy_kwh == 0


def test_recorder_cannot_hide_gap_or_partial_quality(history):
    start = NOW - timedelta(minutes=5)
    history._records = [
        DischargeObservation(start + timedelta(seconds=1), NOW, 0.04, "valid")
    ]
    history._recorder_rows[(start, NOW)] = 0.5
    assert history._effective_observations()[0].energy_kwh == 0.04


def _recorder(history, response):
    entry = MockConfigEntry(domain="sax_power", entry_id=history.entry_id)
    entry.add_to_hass(history.hass)
    entity = er.async_get(history.hass).async_get_or_create(
        "sensor",
        "sax_power",
        f"{history.entry_id}_energy_discharged",
        config_entry=entry,
    )
    recorder = MagicMock(engine=object())
    recorder.async_add_executor_job = AsyncMock(return_value=response)
    history.hass.data[DATA_INSTANCE] = recorder
    return recorder, entity


async def test_recorder_queries_are_incremental_and_normalized(history):
    recorder, entity = _recorder(history, [])
    await history.async_refresh(NOW)
    await history.async_refresh(NOW + timedelta(minutes=5))
    calls = recorder.async_add_executor_job.call_args_list
    assert calls[0].args[1] == entity.entity_id
    assert calls[0].args[2] == NOW - timedelta(hours=168)
    assert calls[1].args[2] == NOW - timedelta(minutes=15)
    history.hass.data.pop(DATA_INSTANCE)


async def test_concurrent_refreshes_share_one_recorder_query(history):
    entered = asyncio.Event()
    release = asyncio.Event()

    async def blocked(*args):
        entered.set()
        await release.wait()
        return []

    recorder, _ = _recorder(history, [])
    recorder.async_add_executor_job.side_effect = blocked
    first = asyncio.create_task(history.async_refresh(NOW))
    await entered.wait()
    second = asyncio.create_task(history.async_refresh(NOW))
    await asyncio.sleep(0)
    release.set()
    left, right = await asyncio.gather(first, second)
    assert left == right
    recorder.async_add_executor_job.assert_awaited_once()
    history.hass.data.pop(DATA_INSTANCE)


async def test_entity_rename_during_recorder_await_discards_response(history):
    recorder, entity = _recorder(history, [])

    async def changed(*args):
        er.async_get(history.hass).async_update_entity(
            entity.entity_id, new_entity_id="sensor.renamed_discharge"
        )
        return [
            {
                "start": (NOW - timedelta(minutes=5)).timestamp(),
                "end": NOW.timestamp(),
                "change": 20,
            }
        ]

    recorder.async_add_executor_job.side_effect = changed
    await history.async_refresh(NOW)
    assert history._recorder_rows == {}
    history.hass.data.pop(DATA_INSTANCE)


async def test_samples_during_recorder_await_do_not_make_snapshot_future(history):
    """REQ-HEMS-LOAD-PROFILE: an await must not mix two evaluation clocks."""
    observe(history, NOW)
    recorder, _ = _recorder(history, [])

    async def measured(*args):
        observe(history, NOW + timedelta(seconds=2))
        return []

    recorder.async_add_executor_job.side_effect = measured
    result = await history.async_refresh(NOW)
    assert result.evaluated_through == NOW
    assert result.quality_reason == "insufficient_history"
    assert history._records[-1].end == NOW + timedelta(seconds=2)
    history.hass.data.pop(DATA_INSTANCE)


def test_known_physical_limit_rejects_implausible_load_without_clipping(history):
    observe(
        history,
        NOW - timedelta(seconds=2),
        storage_power_w=10000,
        max_discharge_power_w=4600,
    )
    observe(history, NOW, storage_power_w=10000, max_discharge_power_w=4600)
    assert history._records[0].quality == "unknown"
    assert history._records[0].energy_kwh == 0


def test_recorder_requests_energy_unit_normalization(history):
    with patch(
        "homeassistant.components.recorder.statistics.statistics_during_period",
        return_value={"sensor.test": []},
    ) as reader:
        assert (
            history._read_statistics("sensor.test", NOW - timedelta(hours=1), NOW) == []
        )
    assert reader.call_args.args[-2] == {"energy": "kWh"}
    assert reader.call_args.args[-1] == {"change"}


def test_large_clock_gap_remains_bounded_and_unknown(history):
    observe(history, NOW - timedelta(days=400))
    observe(history, NOW)
    assert len(history._records) <= 2016
    assert history._records[0].start == NOW - timedelta(hours=168)
    assert all(item.quality == "unknown" for item in history._records)


async def test_recorder_correction_removes_old_numeric_value(history):
    start = NOW - timedelta(minutes=5)
    recorder, _ = _recorder(
        history, [{"start": start.timestamp(), "end": NOW.timestamp(), "change": 0.5}]
    )
    await history.async_refresh(NOW)
    assert history._recorder_rows[(start, NOW)] == 0.5
    recorder.async_add_executor_job.return_value = [
        {"start": start.timestamp(), "end": NOW.timestamp(), "change": None}
    ]
    await history.async_refresh(NOW)
    assert (start, NOW) not in history._recorder_rows
    history.hass.data.pop(DATA_INSTANCE)


async def test_stop_discards_waiting_refresh_and_blocks_new_observations(history):
    entered = asyncio.Event()

    async def blocked(*args):
        entered.set()
        await asyncio.Event().wait()

    recorder, _ = _recorder(history, [])
    recorder.async_add_executor_job.side_effect = blocked
    task = asyncio.create_task(history.async_refresh(NOW))
    await entered.wait()
    await history.async_stop()
    with pytest.raises(asyncio.CancelledError):
        await task
    observe(history, NOW)
    assert history._evaluated_through is None
    history.hass.data.pop(DATA_INSTANCE)


def test_history_selection_defaults_and_explicit_opt_in(history):
    assert history.history_days == 7
    assert history.history_window == timedelta(days=7)
    history.configure(history_days=28)
    assert history.history_window == timedelta(days=28)
    assert history.variants is None
    with pytest.raises(ValueError):
        history.configure(history_days=True)
    with pytest.raises(ValueError):
        history.configure(history_days=14)


def test_history_pruning_expands_only_real_quality_and_shrinks_immediately(history):
    history.configure(history_days=28)
    history._records = [
        DischargeObservation(
            NOW - timedelta(days=age, minutes=5),
            NOW - timedelta(days=age),
            0.1,
            quality,
        )
        for age, quality in ((27, "valid"), (8, "censored"), (1, "unknown"))
    ]
    history._prune(NOW)
    assert [item.quality for item in history._records] == [
        "valid",
        "censored",
        "unknown",
    ]
    history.configure(history_days=7)
    assert [item.quality for item in history._records] == ["unknown"]
    history.configure(history_days=28)
    assert len(history._records) == 1


async def test_history_store_v1_migration_retains_quality_and_requires_fresh_watermark(
    history,
):
    raw = {
        "entry_id": history.entry_id,
        "intervals": [
            [(NOW - timedelta(minutes=1)).isoformat(), NOW.isoformat(), 0.0, "censored"]
        ],
    }
    store = _HistoryStore(history.hass, 2, "test.history.migration")
    migrated = await store._async_migrate_func(1, 1, raw)
    assert migrated["intervals"] == raw["intervals"]
    assert migrated["history_days"] == 7
    assert "history_days" not in raw
    history._store.async_load.return_value = migrated
    with patch(f"{MODULE}._HistoryStore", return_value=history._store):
        restored = HemsHistory(history.hass, history.entry_id, history_days=28)
    await restored.async_start()
    assert restored.history_days == 28
    assert restored._records[-1].quality == "censored"
    assert restored._evaluated_through is None
    await restored.async_stop()


async def test_real_home_assistant_store_migrates_v1_envelope(
    hass, hass_storage, freezer
):
    freezer.move_to(NOW)
    key = "sax_power.hems_history.real-migration"
    original = [
        [(NOW - timedelta(seconds=30)).isoformat(), NOW.isoformat(), 0, "unknown"]
    ]
    hass_storage[key] = {
        "version": 1,
        "minor_version": 1,
        "key": key,
        "data": {"entry_id": "real-migration", "intervals": original},
    }
    restored = HemsHistory(hass, "real-migration")
    await restored.async_start()
    assert restored._records[-1].quality == "unknown"
    assert restored.history_days == 7
    assert restored._evaluated_through is None
    await restored.async_stop()
    assert hass_storage[key]["version"] == 2
    assert hass_storage[key]["data"]["intervals"] == original


async def test_twenty_eight_day_recorder_and_astronomy_are_consistent(history):
    recorder, _ = _recorder(history, [])
    await history.async_refresh(NOW)
    history.configure(history_days=28)
    await history.async_refresh(NOW)
    assert recorder.async_add_executor_job.call_args.args[2] == NOW - timedelta(days=28)
    nights = history._night_spans(NOW, ZoneInfo("Europe/Berlin"))
    assert len(nights) >= 29
    assert nights[0].start < NOW - timedelta(days=28)
    history.hass.data.pop(DATA_INSTANCE)


def test_observation_export_clips_history_without_including_future_or_losing_quality(
    history,
):
    history._records = [
        DischargeObservation(
            NOW - timedelta(minutes=50), NOW - timedelta(minutes=40), 0.1, "valid"
        ),
        DischargeObservation(
            NOW - timedelta(minutes=40), NOW - timedelta(minutes=10), 0, "censored"
        ),
        DischargeObservation(NOW - timedelta(minutes=10), NOW, 0, "unknown"),
        DischargeObservation(NOW, NOW + timedelta(minutes=5), 99, "valid"),
    ]
    exported = history.observations(NOW, lookback=timedelta(minutes=45))
    assert [i.quality for i in exported] == ["valid", "censored", "unknown"]
    assert exported[0].start == NOW - timedelta(minutes=45)
    assert exported[0].energy_kwh == pytest.approx(0.05)
    assert exported[-1].end == NOW


async def test_refresh_exposes_separate_candidates_and_keeps_legacy_seven_days(history):
    history.configure(history_days=28)
    nights = history._night_spans(NOW, ZoneInfo("Europe/Berlin"))
    old = [
        n
        for n in nights
        if NOW - timedelta(days=12) < n.start < NOW - timedelta(days=8)
    ]
    history._records = [
        DischargeObservation(
            n.start, n.end, (n.end - n.start).total_seconds() / 7200, "valid"
        )
        for n in old
    ]
    observe(history, NOW)
    baseline = await history.async_refresh(NOW)
    variants = history.variants
    assert variants.baseline is baseline
    assert baseline.quality_reason == "insufficient_history"
    assert variants.candidate.quality_reason is None
    assert variants.candidate_key == "weighted-v1:28d"
    assert variants.current_night.start < NOW < variants.current_night.end
    assert variants.candidate_metadata


async def test_reconfiguration_during_refresh_cannot_accept_wrong_profile(history):
    recorder, _ = _recorder(history, [])

    async def switch(*args):
        history.configure(history_days=28)
        return []

    recorder.async_add_executor_job.side_effect = switch
    result = await history.async_refresh(NOW)
    assert result.quality_reason == "history_unavailable"
    assert history.variants is None
    history.hass.data.pop(DATA_INSTANCE)


def test_selected_capacity_preserves_more_than_the_legacy_record_limit(history):
    history.configure(history_days=28)
    history._records = [
        DischargeObservation(
            NOW - timedelta(seconds=2 * (15001 - i)),
            NOW - timedelta(seconds=2 * (15000 - i)),
            0,
            "valid" if i % 2 else "unknown",
        )
        for i in range(15000)
    ]
    history._prune(NOW)
    assert len(history._records) == 15000
    assert history._decode(history._serialize()) == history._records


@pytest.mark.parametrize(
    "changes",
    [{"storage_power_w": -1}, {"discharge_blocked": True}, {"control_known": False}],
)
def test_free_discharge_uses_actual_quality_not_only_control_flags(history, changes):
    observe(history, NOW, **changes)
    assert not history.free_discharge(NOW)


@pytest.mark.parametrize(
    "age,free", [(-1, False), (0, True), (30, True), (30.001, False)]
)
def test_free_discharge_requires_fresh_sample_not_profile_watermark(history, age, free):
    observe(history, NOW, storage_power_w=0, soc=5, device_min_soc=0)
    assert history.free_discharge(NOW + timedelta(seconds=age)) is free


async def test_free_discharge_is_false_before_first_sample_and_after_stop(history):
    assert not history.free_discharge(NOW)
    observe(history, NOW)
    assert history.free_discharge(NOW)
    await history.async_stop()
    assert not history.free_discharge(NOW)
