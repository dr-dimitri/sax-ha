"""Öffentliche PV-Verträge und Lebenszyklus (REQ-HEMS-PV-INPUT)."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from math import fsum
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.domain.hems_pv import (
    normalize_pv_forecast,
    normalize_solcast_forecast,
)
from custom_components.sax_power.infrastructure.hems_pv import HemsPvAdapter

NOW = datetime(2026, 9, 12, 4, tzinfo=UTC)


def forecast(
    powers: tuple[float, ...] = (0, 1, 3, 2),
    *,
    start: datetime = NOW,
    step: timedelta = timedelta(minutes=30),
) -> dict[str, Any]:
    """Nur öffentliche JSON-Felder, keine fremden Upstream-Klassen."""
    rows = [
        {
            "start": (start + index * step).isoformat(),
            "end": (start + (index + 1) * step).isoformat(),
            "energy_kwh": power * step.total_seconds() / 3600,
            "ac_power_kw": power,
            "quality_flags": [],
            "is_complete": True,
        }
        for index, power in enumerate(powers)
    ]
    return {
        "schema_version": 1,
        "timezone": "Europe/Berlin",
        "forecast_start_date": start.date().isoformat(),
        "forecast_days": 2,
        "fetched_at": NOW.isoformat(),
        "last_update_success": True,
        "origin": "live",
        "coverage": {
            "start": rows[0]["start"],
            "end": rows[-1]["end"],
            "complete": True,
        },
        "intervals": rows,
    }


def solcast(powers: tuple[float, ...] = (0, 1, 3, 2)) -> dict[str, Any]:
    return {
        "data": [
            {
                "period_start": NOW + timedelta(minutes=30 * index),
                "pv_estimate": power,
                "pv_estimate10": power * 0.8,
                "pv_estimate90": power * 1.2,
            }
            for index, power in enumerate(powers)
        ]
    }


def normalize(payload: object, *, start: datetime = NOW, hours: float = 2):
    return normalize_pv_forecast(
        payload, as_of=start, end=start + timedelta(hours=hours), source_id="plant"
    )


def test_provider_conformance_and_partial_edges() -> None:
    """REQ-HEMS-PV-INPUT: dieselbe physikalische Reihe bleibt anbieterneutral."""
    start, end = NOW + timedelta(minutes=5), NOW + timedelta(hours=1, minutes=55)
    pv = normalize_pv_forecast(forecast(), as_of=start, end=end, source_id="plant")
    other = normalize_solcast_forecast(
        solcast(), as_of=start, end=end, source_id="plant", fetched_at=NOW
    )
    assert pv.intervals == other.intervals
    assert pv.coverage_complete and other.coverage_complete
    assert fsum(slot.energy_kwh for slot in pv.intervals) == pytest.approx(17 / 6)
    assert pv.intervals[0].start == start and pv.intervals[-1].end == end
    assert pv.update_success is True and other.update_success is None
    assert other.freshness_policy == "sax_max_age_assumption"


def test_48_hours_use_192_cells_and_preserve_zero() -> None:
    result = normalize(forecast((0,) * 48, step=timedelta(hours=1)), hours=48)
    assert result.quality_reason is None
    assert result.coverage_complete
    assert len(result.intervals) == 192
    assert all(item.energy_kwh == 0 for item in result.intervals)


@pytest.mark.parametrize(
    "fault", ["gap", "fallback", "incomplete", "negative", "nan", "power", "overlap"]
)
def test_bad_later_interval_preserves_usable_early_coverage(fault: str) -> None:
    payload = forecast((1, 1, 1, 1))
    row = payload["intervals"][-1]
    if fault == "gap":
        payload["intervals"].pop()
    elif fault == "overlap":
        payload["intervals"].append(deepcopy(row))
    elif fault == "fallback":
        row["quality_flags"] = ["gti_fallback"]
    elif fault == "incomplete":
        row["is_complete"] = False
    elif fault == "power":
        row["ac_power_kw"] = 2
    else:
        row["energy_kwh"] = -1 if fault == "negative" else float("nan")
    result = normalize(payload, hours=48)
    assert result.quality_reason is None
    assert result.coverage_end == NOW + timedelta(minutes=90)
    assert len(result.intervals) == 6
    assert not result.coverage_complete
    assert "pv_partial_coverage" in result.quality_flags


def test_gap_in_middle_stays_gap_and_is_not_zero_filled() -> None:
    payload = forecast((1, 1, 1, 1))
    payload["intervals"].pop(1)
    result = normalize(payload)
    assert result.quality_reason is None
    assert not result.coverage_complete
    assert result.intervals[1].end == NOW + timedelta(minutes=30)
    assert result.intervals[2].start == NOW + timedelta(hours=1)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("schema_version", 2, "pv_unsupported_schema"),
        ("schema_version", True, "pv_unsupported_schema"),
        ("scope", "roof", "pv_invalid_scope"),
        ("timezone", "missing/zone", "pv_invalid_metadata"),
        ("coverage", {}, "pv_invalid_metadata"),
        ("last_update_success", False, "pv_update_failed"),
        ("last_update_success", None, "pv_missing_update_status"),
        ("fetched_at", None, "pv_missing_fetched_at"),
        ("fetched_at", "2026-09-12T04:00:00", "pv_missing_fetched_at"),
        (
            "fetched_at",
            (NOW + timedelta(seconds=1)).isoformat(),
            "pv_future_fetched_at",
        ),
        (
            "fetched_at",
            (NOW - timedelta(minutes=60, seconds=1)).isoformat(),
            "pv_stale_forecast",
        ),
    ],
)
def test_invalid_pv_metadata_never_releases_numbers(field, value, reason) -> None:
    payload = forecast()
    payload[field] = value
    result = normalize(payload)
    assert result.quality_reason == reason
    assert not result.intervals


def test_60_minute_boundary_and_restored_failure() -> None:
    payload = forecast()
    payload["fetched_at"] = (NOW - timedelta(minutes=60)).isoformat()
    result = normalize(payload)
    assert result.quality_reason is None
    assert result.valid_until == NOW
    payload.update(origin="restored", last_update_success=False)
    failed = normalize(payload)
    assert failed.quality_reason == "pv_update_failed"
    assert failed.origin == "restored"
    assert failed.fetched_at == result.fetched_at


@pytest.mark.parametrize(
    "fault", ["duplicate", "overlap", "naive", "reversed", "missing"]
)
def test_invalid_interval_geometry_cannot_be_hidden_by_projection(fault: str) -> None:
    payload = forecast()
    rows = payload["intervals"]
    if fault == "duplicate":
        rows.append(deepcopy(rows[0]))
    elif fault == "overlap":
        rows[1]["start"] = (NOW + timedelta(minutes=25)).isoformat()
    elif fault == "naive":
        rows[1]["start"] = "2026-09-12T04:30:00"
    elif fault == "reversed":
        rows[1]["end"] = rows[1]["start"]
    else:
        del rows[1]["end"]
    result = normalize(payload)
    if fault in ("duplicate", "overlap"):
        assert result.quality_reason is None
        assert "pv_overlapping_intervals" in result.quality_flags
        assert result.intervals[0].start == NOW + timedelta(
            minutes=30 if fault == "duplicate" else 60
        )
    else:
        assert result.quality_reason == "pv_invalid_intervals"
        assert not result.intervals


@pytest.mark.parametrize("hours", [1, 8, 24])
def test_solcast_age_is_explicit_and_independent_of_pv_policy(hours: int) -> None:
    kwargs = dict(
        as_of=NOW,
        end=NOW + timedelta(hours=2),
        source_id="solcast",
        max_age_hours=hours,
    )
    result = normalize_solcast_forecast(
        solcast(), fetched_at=NOW - timedelta(hours=hours), **kwargs
    )
    assert result.quality_reason is None and result.update_success is None
    assert result.max_age_seconds == hours * 3600
    stale = normalize_solcast_forecast(
        solcast(), fetched_at=NOW - timedelta(hours=hours, seconds=1), **kwargs
    )
    assert stale.quality_reason == "pv_stale_forecast"
    assert not stale.intervals


@pytest.mark.parametrize("day", [(2026, 3, 29, 23), (2026, 10, 25, 25)])
def test_dst_actual_day_duration_preserves_energy(day) -> None:
    year, month, date, hours = day
    start = datetime(year, month, date, tzinfo=ZoneInfo("Europe/Berlin"))
    end = (start + timedelta(days=1)).astimezone(UTC)
    payload = forecast(
        (1,) * hours, start=start.astimezone(UTC), step=timedelta(hours=1)
    )
    payload["fetched_at"] = start.isoformat()
    result = normalize_pv_forecast(payload, as_of=start, end=end, source_id="plant")
    assert result.coverage_complete
    assert len(result.intervals) == hours * 4
    assert fsum(item.energy_kwh for item in result.intervals) == hours


def loaded_entry(hass: HomeAssistant, provider: str) -> MockConfigEntry:
    entry = MockConfigEntry(domain=provider, data={})
    entry.add_to_hass(hass)
    entry.mock_state(hass, ConfigEntryState.LOADED)
    return entry


def timestamp_entity(hass: HomeAssistant, entry: MockConfigEntry) -> er.RegistryEntry:
    entity = er.async_get(hass).async_get_or_create(
        "sensor",
        "solcast_solar",
        "lastupdated",
        config_entry=entry,
        suggested_object_id="my_solcast_last_polled",
    )
    hass.states.async_set(
        entity.entity_id, NOW.isoformat(), {"device_class": "timestamp"}
    )
    return entity


@pytest.mark.parametrize("provider", ["pv_forecast", "solcast_solar"])
async def test_public_service_only_and_registry_rename(
    hass: HomeAssistant, provider: str
) -> None:
    entry = loaded_entry(hass, provider)
    entity = timestamp_entity(hass, entry) if provider == "solcast_solar" else None
    calls: list[ServiceCall] = []

    async def read(call: ServiceCall) -> dict[str, Any]:
        calls.append(call)
        return forecast() if provider == "pv_forecast" else solcast()

    service = "get_forecast" if provider == "pv_forecast" else "query_forecast_data"
    hass.services.async_register(
        provider, service, read, supports_response=SupportsResponse.ONLY
    )
    adapter = HemsPvAdapter(hass, provider, entry.entry_id)
    result = await adapter.async_read(
        NOW + timedelta(minutes=5), NOW + timedelta(minutes=115)
    )
    assert result.quality_reason is None and result.coverage_complete
    assert len(calls) == 1
    if entity is None:
        assert calls[0].data == {"config_entry_id": entry.entry_id}
    else:
        assert calls[0].data == {
            "start_date_time": NOW,
            "end_date_time": NOW + timedelta(hours=2),
            "undampened": False,
        }
        er.async_get(hass).async_update_entity(
            entity.entity_id, new_entity_id="sensor.renamed"
        )
        hass.states.async_set("sensor.renamed", NOW.isoformat())
        renamed = await adapter.async_read(NOW, NOW + timedelta(hours=2))
        assert renamed.quality_reason is None
    adapter.shutdown()


@pytest.mark.parametrize("persisted_identity", [False, True])
async def test_explicit_solcast_timestamp_rename_survives_new_adapter(
    hass: HomeAssistant, persisted_identity: bool
) -> None:
    """Runtime rebuilds adapters; identity must survive between instances."""
    entry = loaded_entry(hass, "solcast_solar")
    entity = timestamp_entity(hass, entry)
    original_name = entity.entity_id
    arguments = {
        "solcast_timestamp_entity_id": original_name,
        "solcast_timestamp_registry_id": entity.id if persisted_identity else None,
    }

    async def read(call: ServiceCall) -> dict[str, Any]:
        return solcast()

    hass.services.async_register(
        "solcast_solar",
        "query_forecast_data",
        read,
        supports_response=SupportsResponse.ONLY,
    )
    first = HemsPvAdapter(hass, "solcast_solar", entry.entry_id, **arguments)
    assert (await first.async_read(NOW)).quality_reason is None
    first.shutdown()
    registry = er.async_get(hass)
    registry.async_update_entity(original_name, new_entity_id="sensor.renamed_polled")
    hass.states.async_remove(original_name)
    hass.states.async_set("sensor.renamed_polled", NOW.isoformat())
    if persisted_identity:
        reused = registry.async_get_or_create(
            "sensor",
            "solcast_solar",
            "peak_time_tomorrow",
            config_entry=entry,
            suggested_object_id=original_name.split(".", 1)[1],
        )
        assert reused.entity_id == original_name
        hass.states.async_set(original_name, "unknown")
    rebuilt = HemsPvAdapter(hass, "solcast_solar", entry.entry_id, **arguments)
    assert (await rebuilt.async_read(NOW)).quality_reason is None
    rebuilt.shutdown()


@pytest.mark.parametrize("problem", ["deleted", "foreign", "invalid", "wrong_sensor"])
async def test_timestamp_identity_never_rebinds_to_another_sensor(
    hass: HomeAssistant, problem: str
) -> None:
    entry = loaded_entry(hass, "solcast_solar")
    entity = timestamp_entity(hass, entry)
    registry = er.async_get(hass)
    name, identity = entity.entity_id, entity.id
    if problem == "deleted":
        registry.async_remove(name)
        replacement = registry.async_get_or_create(
            "sensor", "solcast_solar", "last_updated", config_entry=entry
        )
        hass.states.async_set(replacement.entity_id, NOW.isoformat())
        assert replacement.id != identity
    elif problem == "foreign":
        other = loaded_entry(hass, "other")
        identity = timestamp_entity(hass, other).id
    elif problem == "invalid":
        identity = "nonexistent-registry-id"
    else:
        unrelated = registry.async_get_or_create(
            "sensor", "solcast_solar", "peak_time_tomorrow", config_entry=entry
        )
        name, identity = unrelated.entity_id, None
    adapter = HemsPvAdapter(
        hass,
        "solcast_solar",
        entry.entry_id,
        solcast_timestamp_entity_id=name,
        solcast_timestamp_registry_id=identity,
    )
    result = await adapter.async_read(NOW)
    assert result.quality_reason == "pv_missing_fetched_at"
    assert not result.intervals


@pytest.mark.parametrize(
    "problem", ["missing", "unknown", "foreign", "disabled", "ambiguous"]
)
async def test_solcast_source_identity_and_missing_timestamp_stop_before_query(
    hass: HomeAssistant, problem: str
) -> None:
    entry = loaded_entry(hass, "solcast_solar")
    explicit = None
    if problem != "missing":
        source = loaded_entry(hass, "other") if problem == "foreign" else entry
        entity = timestamp_entity(hass, source)
        if problem == "unknown":
            hass.states.async_set(entity.entity_id, "unknown")
        elif problem == "disabled":
            er.async_get(hass).async_update_entity(
                entity.entity_id, disabled_by=er.RegistryEntryDisabler.USER
            )
        elif problem == "foreign":
            explicit = entity.entity_id
        elif problem == "ambiguous":
            loaded_entry(hass, "solcast_solar")
    adapter = HemsPvAdapter(
        hass, "solcast_solar", entry.entry_id, solcast_timestamp_entity_id=explicit
    )
    result = await adapter.async_read(NOW)
    assert result.quality_reason in ("pv_missing_fetched_at", "pv_source_unavailable")
    assert not result.intervals


async def test_solcast_changed_timestamp_discards_response(hass: HomeAssistant) -> None:
    entry = loaded_entry(hass, "solcast_solar")
    entity = timestamp_entity(hass, entry)

    async def read(call: ServiceCall) -> dict[str, Any]:
        hass.states.async_set(
            entity.entity_id, (NOW + timedelta(seconds=1)).isoformat()
        )
        return solcast()

    hass.services.async_register(
        "solcast_solar",
        "query_forecast_data",
        read,
        supports_response=SupportsResponse.ONLY,
    )
    result = await HemsPvAdapter(hass, "solcast_solar", entry.entry_id).async_read(NOW)
    assert result.quality_reason == "pv_source_changed" and not result.intervals


@pytest.mark.parametrize(
    "change", ["shutdown", "invalidate", "options", "unload", "timeout"]
)
async def test_inflight_change_timeout_and_unload_discard_stale_data(
    hass: HomeAssistant, change: str
) -> None:
    entry = loaded_entry(hass, "pv_forecast")
    started, release, cancelled = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def read(call: ServiceCall) -> dict[str, Any]:
        started.set()
        try:
            await release.wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise
        return forecast()

    hass.services.async_register(
        "pv_forecast", "get_forecast", read, supports_response=SupportsResponse.ONLY
    )
    adapter = HemsPvAdapter(
        hass,
        "pv_forecast",
        entry.entry_id,
        timeout_seconds=0.05 if change == "timeout" else 10,
    )
    task = asyncio.create_task(adapter.async_read(NOW))
    await started.wait()
    concurrent = await adapter.async_read(NOW)
    assert concurrent.quality_reason == "pv_query_in_progress"
    if change == "shutdown":
        adapter.shutdown()
    elif change == "invalidate":
        adapter.invalidate()
    elif change == "options":
        hass.config_entries.async_update_entry(entry, options={"forecast_days": 3})
        release.set()
    elif change == "unload":
        entry.mock_state(hass, ConfigEntryState.NOT_LOADED)
        release.set()
    result = await task
    assert not result.intervals
    assert result.quality_reason == (
        "pv_query_timeout" if change == "timeout" else "pv_source_changed"
    )
    if change in ("shutdown", "invalidate", "timeout"):
        assert cancelled.is_set()


async def test_service_failure_does_not_poison_next_evaluation(
    hass: HomeAssistant,
) -> None:
    entry = loaded_entry(hass, "pv_forecast")
    fail = True

    async def read(call: ServiceCall) -> dict[str, Any]:
        if fail:
            raise ServiceValidationError("not available")
        return forecast()

    hass.services.async_register(
        "pv_forecast", "get_forecast", read, supports_response=SupportsResponse.ONLY
    )
    adapter = HemsPvAdapter(hass, "pv_forecast", entry.entry_id)
    assert (await adapter.async_read(NOW)).quality_reason == "pv_query_failed"
    fail = False
    assert (await adapter.async_read(NOW)).quality_reason is None
