"""Bounded async persistence and lifecycle for immutable forecast evidence."""

import asyncio
import threading
from dataclasses import replace
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.sax_power.domain.hems_evaluation import stable_id
from custom_components.sax_power.domain.hems_uncertainty import UncertaintyClass
from custom_components.sax_power.infrastructure.hems_archive import (
    HemsArchive,
    _ArchiveStore,
    _decode,
    _encode,
)
from tests.test_hems_evaluation import NOW, forecast, observed, pair_for_night
from tests.test_hems_uncertainty import CLASS, training, validation

MODULE = "custom_components.sax_power.infrastructure.hems_archive"


@pytest.fixture
async def archive(hass, freezer):
    freezer.move_to(NOW)
    store = MagicMock()
    store.async_load = AsyncMock(return_value=None)
    store.async_save = AsyncMock()
    store.async_remove = AsyncMock()
    with patch(f"{MODULE}._ArchiveStore", return_value=store):
        value = HemsArchive(hass, "test", enabled=True)
    await value.async_start()
    yield value
    await value.async_stop()


async def test_immutable_roundtrip_idempotence_and_future_rejection(archive):
    record = forecast()
    assert await archive.async_record(record)
    assert await archive.async_record(record)
    assert archive.diagnostics["records"] == 1
    assert _decode(_encode(record)) == record
    with pytest.raises(ValueError, match="rewritten"):
        await archive.async_record(replace(record, planning_parameters_json='{"x":1}'))
    with pytest.raises(ValueError, match="future"):
        await archive.async_record(forecast(NOW + timedelta(hours=1)), as_of=NOW)


async def test_resolve_only_later_observations_and_keep_original_output(archive):
    record = forecast()
    await archive.async_record(record)
    later = forecast(NOW + timedelta(hours=2))
    obs = observed(NOW + timedelta(hours=1), NOW + timedelta(hours=2), 1)
    await archive.async_record(later, (obs,))
    pair = next(
        p
        for p in archive.pairs
        if p.horizon == "60m" and p.start == NOW + timedelta(hours=1)
    )
    assert pair.baseline_kwh == 2
    assert pair.candidate_kwh == 1
    assert pair.observed_kwh == 1
    await archive.async_record(
        forecast(NOW + timedelta(hours=3)), (replace(obs, energy_kwh=99),)
    )
    assert next(p for p in archive.pairs if p.pair_id == pair.pair_id) == pair
    assert (await archive.async_summary("baseline"))["mae_kwh"] == 1


async def test_target_waits_for_its_last_real_sample_without_rewriting_forecast(
    archive,
):
    original = forecast()
    await archive.async_record(original)
    start, end = NOW + timedelta(hours=1), NOW + timedelta(hours=2)
    last_sample = end - timedelta(seconds=1)
    before = observed(start, last_sample, 3599 / 3600)
    await archive.async_record(forecast(end), (before,))
    assert archive._watermark == last_sample
    assert not any(p.horizon == "60m" and p.start == start for p in archive.pairs)

    after = observed(last_sample, end + timedelta(seconds=1), 2 / 3600)
    await archive.async_record(forecast(end + timedelta(minutes=5)), (before, after))
    pair = next(p for p in archive.pairs if p.horizon == "60m" and p.start == start)
    assert pair.record_id == original.record_id
    assert pair.complete
    assert pair.observed_hours == 1
    assert pair.observed_kwh == pytest.approx(1)
    assert (
        next(r for r in archive._records if r.record_id == original.record_id)
        == original
    )


async def test_empty_or_future_observations_cannot_advance_completion_time(archive):
    await archive.async_record(forecast())
    assert archive._watermark is None
    now = NOW + timedelta(hours=2)
    future = observed(now, now + timedelta(seconds=1))
    await archive.async_record(forecast(now), (future,))
    assert archive._watermark is None
    assert archive.pairs == ()


@pytest.mark.parametrize("quality", ["unknown", "censored"])
async def test_explicit_quality_tail_completes_target_as_unobservable(archive, quality):
    await archive.async_record(forecast())
    start, end = NOW + timedelta(hours=1), NOW + timedelta(hours=2)
    middle = start + timedelta(minutes=30)
    observations = (observed(start, middle, 0.5), observed(middle, end, 0, quality))
    await archive.async_record(forecast(end), observations)
    assert archive._watermark == end
    pair = next(p for p in archive.pairs if p.horizon == "60m" and p.start == start)
    assert not pair.complete
    assert pair.observed_hours == 0.5
    assert pair.excluded_seconds == ((quality, 1800),)


async def test_off_collects_nothing_and_reenable_does_not_fill_archive_gap(archive):
    record = forecast()
    await archive.async_record(record)
    archive.configure(False, NOW + timedelta(minutes=5))
    assert not await archive.async_record(forecast(NOW + timedelta(minutes=10)))
    assert archive.archived_baselines(NOW, NOW + timedelta(hours=1), "baseline") == ()
    archive.configure(True, NOW + timedelta(hours=2))
    assert not await archive.async_record(record)
    await archive.async_record(
        forecast(NOW + timedelta(hours=3)),
        (observed(NOW + timedelta(hours=1), NOW + timedelta(hours=2)),),
    )
    assert not any(p.record_id == record.record_id for p in archive.pairs)


async def test_disabled_default_and_separate_entry_keys(hass, freezer):
    freezer.move_to(NOW)
    one, two = HemsArchive(hass, "one"), HemsArchive(hass, "two")
    assert not one.enabled
    assert one._store.key != two._store.key
    assert not await one.async_record(forecast())


async def test_retention_byte_and_pair_limits_are_visible(archive, freezer):
    archive._max_detail_bytes = 1
    archive._max_pairs = 2
    archive._pairs = tuple(pair_for_night(day) for day in range(3))
    freezer.move_to(NOW + timedelta(days=3))
    await archive.async_record(forecast(NOW + timedelta(days=3)))
    assert archive.diagnostics["records"] == 0
    assert archive.diagnostics["pairs"] == 2
    assert archive.diagnostics["pruned"] == 2
    freezer.move_to(NOW + timedelta(days=370))
    result = await archive.async_export()
    assert result["items"] == []
    assert archive.diagnostics["pairs"] == 0


async def test_profile_grandfathering_only_exact_previously_proven_key(
    archive, freezer
):
    as_of = NOW + timedelta(days=15)
    freezer.move_to(as_of)
    archive._pairs = tuple(pair_for_night(day) for day in range(14))
    archive._frozen[stable_id(("baseline", "candidate"))] = NOW - timedelta(days=1)
    gate = await archive.async_gate("baseline", "candidate", "night", as_of=as_of)
    assert gate.approved
    archive.configure(False, as_of)
    retained = await archive.async_gate("baseline", "candidate", "night", as_of=as_of)
    assert retained.approved and retained.retained
    assert not (
        await archive.async_gate("baseline", "candidate:28d", "night", as_of=as_of)
    ).approved
    assert not (
        await archive.async_gate("baseline", "candidate", "dawn", as_of=as_of)
    ).approved


async def test_missing_retained_evidence_revokes_approval_when_monitoring_on(
    archive, freezer
):
    as_of = NOW + timedelta(days=15)
    freezer.move_to(as_of)
    archive._pairs = tuple(pair_for_night(day) for day in range(14))
    archive._frozen[stable_id(("baseline", "candidate"))] = NOW - timedelta(days=1)
    assert (
        await archive.async_gate("baseline", "candidate", "night", as_of=as_of)
    ).approved
    archive._pairs = ()
    assert not (
        await archive.async_gate("baseline", "candidate", "night", as_of=as_of)
    ).approved
    archive.configure(False, as_of)
    assert not (
        await archive.async_gate("baseline", "candidate", "night", as_of=as_of)
    ).approved


async def test_save_failure_never_grants_new_profile(archive):
    archive._store.async_save.side_effect = OSError("disk unavailable")
    archive._pairs = tuple(pair_for_night(day) for day in range(14))
    archive._frozen[stable_id(("baseline", "candidate"))] = NOW - timedelta(days=1)
    gate = await archive.async_gate(
        "baseline", "candidate", "night", as_of=NOW + timedelta(days=15)
    )
    assert not gate.approved
    assert gate.reason == "archive_save_failed"
    assert archive.diagnostics["status"] == "save_failed"


async def test_restart_keeps_original_forecasts_and_uncertainty_training(
    archive, hass, freezer
):
    await archive.async_record(forecast())
    archive._pairs = training()
    as_of = NOW + timedelta(days=60)
    freezer.move_to(as_of)
    result = await archive.async_uncertainty(
        CLASS,
        expected_kwh=1,
        start=as_of + timedelta(hours=1),
        end=as_of + timedelta(hours=2),
        as_of=as_of,
    )
    assert result.training_nights == 60
    model = archive._models[CLASS.identifier]
    archive._pairs = (*archive._pairs, *validation(model))
    await archive._save()
    raw = archive._store.async_save.call_args.args[0]
    freezer.move_to(NOW + timedelta(days=92))
    archive._store.async_load.return_value = raw
    with patch(f"{MODULE}._ArchiveStore", return_value=archive._store):
        restarted = HemsArchive(hass, "test", enabled=True)
    await restarted.async_start()
    assert restarted._models[CLASS.identifier] == model
    result = await restarted.async_uncertainty(
        CLASS,
        expected_kwh=1,
        start=NOW + timedelta(days=92, hours=1),
        end=NOW + timedelta(days=92, hours=2),
        as_of=NOW + timedelta(days=92),
    )
    assert result.status == "reliable"
    changed = UncertaintyClass("new-version", output_group=CLASS.output_group)
    assert (
        await restarted.async_uncertainty(
            changed,
            expected_kwh=1,
            start=NOW + timedelta(days=92, hours=1),
            end=NOW + timedelta(days=92, hours=2),
            as_of=NOW + timedelta(days=92),
        )
    ).reason == "insufficient_training_nights"


async def test_executor_work_does_not_block_ha_and_disable_invalidates_result(archive):
    started, proceed = threading.Event(), threading.Event()
    original = archive._append

    def wait_append(*args):
        started.set()
        assert proceed.wait(5)
        return original(*args)

    with patch.object(archive, "_append", new=wait_append):
        task = asyncio.create_task(archive.async_record(forecast()))
        await archive.hass.async_add_executor_job(started.wait, 5)
        archive.configure(False, NOW)
        proceed.set()
        assert not await task
    assert archive.diagnostics["records"] == 0


async def test_export_delete_race_cannot_resurrect_records(archive):
    await archive.async_record(forecast())
    await asyncio.gather(archive.async_export(), archive.async_delete())
    assert archive.diagnostics["records"] == 0
    assert archive._pairs == ()
    archive._store.async_remove.assert_awaited_once()
    with pytest.raises(ValueError):
        await archive.async_export(limit=1001)


async def test_migration_rejects_incompatible_major(hass):
    store = _ArchiveStore(hass, 1, "migration")
    assert await store._async_migrate_func(1, 0, {"schema": 1}) == {"schema": 1}
    with pytest.raises(NotImplementedError):
        await store._async_migrate_func(2, 0, {})


async def test_corrupt_storage_does_not_load_partial_approvals(archive, hass):
    archive._store.async_load.return_value = {
        "schema": 1,
        "records": {"tuple": []},
        "pairs": {"tuple": []},
        "approvals": {"bad": True},
    }
    with patch(f"{MODULE}._ArchiveStore", return_value=archive._store):
        restarted = HemsArchive(hass, "test", enabled=True)
    await restarted.async_start()
    assert restarted.diagnostics["status"] == "load_failed"
    assert restarted._approvals == {}
    archive._store.async_save.reset_mock()
    assert not await restarted.async_record(forecast())
    await restarted.async_stop()
    archive._store.async_save.assert_not_awaited()
