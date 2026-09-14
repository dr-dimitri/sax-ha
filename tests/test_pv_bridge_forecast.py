"""Read-only PV plant lookup and safe public time-series use (REQ-BRIDGE-CHARGE)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.infrastructure.pv_bridge_forecast import (
    PvBridgeForecast,
)

NOW = datetime(2026, 9, 13, 20, 7, tzinfo=UTC)
PV_START = datetime(2026, 9, 14, 5, tzinfo=UTC)


@dataclass
class _Source:
    entry: MockConfigEntry
    entity_id: str
    selected: str | None
    now: datetime = NOW
    calls: list[dict[str, Any]] = field(default_factory=list)
    power_w: Callable[[datetime], float] = lambda moment: (
        1500 if moment >= PV_START else 0
    )
    mutation: tuple[tuple[str | int, ...], Any] | None = None
    error: Exception | None = None
    block: asyncio.Event | None = None
    entered: asyncio.Event = field(default_factory=asyncio.Event)

    def response(self, request: dict[str, Any]) -> dict[str, Any]:
        start = datetime.fromisoformat(request["window"]["start"])
        end = datetime.fromisoformat(request["window"]["end"])
        intervals = []
        cursor = start
        while cursor < end:
            power_kw = self.power_w(cursor) / 1000
            intervals.append(
                {
                    "start": cursor.isoformat(),
                    "end": (cursor + timedelta(minutes=15)).isoformat(),
                    "energy_kwh": power_kw / 4,
                    "mean_ac_power_kw": power_kw,
                }
            )
            cursor += timedelta(minutes=15)
        energy = sum(item["energy_kwh"] for item in intervals)
        fetched_at = (self.now - timedelta(minutes=5)).isoformat()
        result = {
            "schema_version": 1,
            "timezone": "Europe/Berlin",
            "fetched_at": fetched_at,
            "last_update_success": True,
            "origin": "live",
            "window": {
                "schema_version": 1,
                "scope": "total",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "as_of": self.now.isoformat(),
                "fetched_at": fetched_at,
                "timezone": "Europe/Berlin",
                "status": "available",
                "reason": None,
                "coverage": {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "complete": True,
                },
                "quality_flags": [],
                "step_minutes": 15,
                "energy_kwh": energy,
                "mean_ac_power_kw": energy / ((end - start).total_seconds() / 3600),
                "assumption": "constant_interval_mean_power",
                "intervals": intervals,
            },
        }
        if self.mutation is not None:
            path, value = self.mutation
            target = result
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
        return result


@pytest.fixture
async def pv_source(
    hass: HomeAssistant,
) -> tuple[_Source, PvBridgeForecast]:
    entry = MockConfigEntry(domain="pv_forecast", data={"time_zone": "Europe/Berlin"})
    entry.add_to_hass(hass)
    entry.mock_state(hass, ConfigEntryState.LOADED)
    registered = er.async_get(hass).async_get_or_create(
        "sensor", "pv_forecast", "total-today", config_entry=entry
    )
    source = _Source(entry, registered.entity_id, registered.entity_id)

    async def forecast(call: ServiceCall) -> dict[str, Any]:
        source.calls.append(dict(call.data))
        source.entered.set()
        if source.block is not None:
            await source.block.wait()
        if source.error is not None:
            raise source.error
        return source.response(dict(call.data))

    hass.services.async_register(
        "pv_forecast",
        "get_forecast",
        forecast,
        supports_response=SupportsResponse.ONLY,
    )
    return source, PvBridgeForecast(hass, lambda: source.selected)


async def test_total_plant_service_yields_consumption_based_pv_start(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    source, adapter = pv_source
    await adapter.async_refresh(NOW)

    assert adapter.pv_start(NOW, 1000) == PV_START
    assert adapter.pv_start(NOW, 1500) == PV_START
    assert adapter.pv_start(NOW, 1501) is None
    assert source.calls == [
        {
            "config_entry_id": source.entry.entry_id,
            "window": {
                "start": "2026-09-13T20:15:00+00:00",
                "end": "2026-09-14T22:00:00+00:00",
                "step_minutes": 15,
            },
        }
    ]


async def test_single_bright_quarter_does_not_claim_sustained_pv_start(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    source, adapter = pv_source
    source.power_w = lambda moment: 2000 if moment == PV_START else 0
    await adapter.async_refresh(NOW)
    assert adapter.pv_start(NOW, 1000) is None


async def test_service_cache_is_limited_to_one_call_per_minute(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    source, adapter = pv_source
    for seconds in (0, 1, 30, 59):
        await adapter.async_refresh(NOW + timedelta(seconds=seconds))
    assert len(source.calls) == 1
    assert adapter.pv_start(NOW + timedelta(seconds=59), 1000) == PV_START
    assert adapter.pv_start(NOW + timedelta(seconds=61), 1000) == PV_START
    source.now = NOW + timedelta(seconds=60)
    await adapter.async_refresh(source.now)
    assert len(source.calls) == 2
    assert adapter.pv_start(source.now, 1000) == PV_START


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        (("last_update_success",), False),
        (("window", "quality_flags"), ["partial"]),
        (("origin",), "restored"),
        (("schema_version",), 2),
        (("window", "scope"), "roof"),
        (("window", "status"), "unavailable"),
        (("window", "reason"), "stale_forecast"),
        (("window", "step_minutes"), 30),
        (("window", "timezone"), "UTC"),
        (("window", "intervals", 0, "mean_ac_power_kw"), 10**1000),
    ],
    ids=[
        "accepted",
        "failed-update",
        "partial-quality",
        "restored-origin",
        "unsupported-schema",
        "wrong-scope",
        "unavailable",
        "rejection-reason",
        "wrong-step",
        "wrong-timezone",
        "numeric-overflow",
    ],
)
async def test_received_responses_keep_minute_cadence_under_coordinator_polling(
    pv_source: tuple[_Source, PvBridgeForecast],
    mutation: tuple[tuple[str | int, ...], Any] | None,
) -> None:
    """REQ-BRIDGE-CHARGE: rejected content must not amplify provider traffic."""
    source, adapter = pv_source
    source.mutation = mutation
    call_times = []

    for seconds in range(0, 600, 2):
        source.now = NOW + timedelta(seconds=seconds)
        previous_calls = len(source.calls)
        await adapter.async_refresh(source.now)
        if len(source.calls) != previous_calls:
            call_times.append(seconds)
        assert adapter.pv_start(source.now, 1000) == (
            PV_START if mutation is None else None
        )

    assert call_times == list(range(0, 600, 60))
    assert len(source.calls) == 10


@pytest.mark.parametrize("error_type", [HomeAssistantError, TimeoutError])
@pytest.mark.parametrize(
    "mutation",
    [
        (("window", "quality_flags"), ["partial"]),
        (("window", "intervals", 0, "mean_ac_power_kw"), 10**1000),
    ],
    ids=["rejected-quality", "numeric-overflow"],
)
async def test_rejected_retry_response_restores_normal_refresh_cadence(
    pv_source: tuple[_Source, PvBridgeForecast],
    error_type: type[Exception],
    mutation: tuple[tuple[str | int, ...], Any],
) -> None:
    """REQ-BRIDGE-CHARGE: a received rejection ends the transient retry phase."""
    source, adapter = pv_source
    source.error = error_type("Temporary PV service failure")
    await adapter.async_refresh(NOW)
    await adapter.async_refresh(NOW + timedelta(seconds=9))
    assert len(source.calls) == 1

    source.error = None
    source.mutation = mutation
    source.now = NOW + timedelta(seconds=10)
    await adapter.async_refresh(source.now)
    assert len(source.calls) == 2
    assert adapter.pv_start(source.now, 1000) is None

    for seconds in range(12, 70, 2):
        source.now = NOW + timedelta(seconds=seconds)
        await adapter.async_refresh(source.now)
    assert len(source.calls) == 2

    source.now = NOW + timedelta(seconds=70)
    await adapter.async_refresh(source.now)
    assert len(source.calls) == 3
    assert adapter.pv_start(source.now, 1000) is None


@pytest.mark.parametrize("error_type", [HomeAssistantError, TimeoutError])
async def test_transient_failure_after_rejection_retries_then_recovers(
    pv_source: tuple[_Source, PvBridgeForecast], error_type: type[Exception]
) -> None:
    """REQ-BRIDGE-CHARGE: retry cadence follows the latest service outcome."""
    source, adapter = pv_source
    source.mutation = (("last_update_success",), False)
    await adapter.async_refresh(NOW)
    source.error = error_type("Temporary PV service failure")
    await adapter.async_refresh(NOW + timedelta(seconds=60))
    await adapter.async_refresh(NOW + timedelta(seconds=69))
    assert len(source.calls) == 2

    source.error = None
    source.mutation = None
    source.now = NOW + timedelta(seconds=70)
    await adapter.async_refresh(source.now)
    assert len(source.calls) == 3
    assert adapter.pv_start(source.now, 1000) == PV_START
    await adapter.async_refresh(NOW + timedelta(seconds=80))
    await adapter.async_refresh(NOW + timedelta(seconds=129))
    assert len(source.calls) == 3

    source.now = NOW + timedelta(seconds=130)
    await adapter.async_refresh(source.now)
    assert len(source.calls) == 4
    assert adapter.pv_start(source.now, 1000) == PV_START


async def test_rejection_logs_once_per_reason_even_across_transient_failures(
    pv_source: tuple[_Source, PvBridgeForecast], caplog: pytest.LogCaptureFixture
) -> None:
    """REQ-BRIDGE-CHARGE: persistent rejection stays diagnosable without log spam."""
    source, adapter = pv_source
    source.mutation = (("last_update_success",), False)
    for seconds in (0, 60, 120):
        source.now = NOW + timedelta(seconds=seconds)
        await adapter.async_refresh(source.now)
    assert caplog.messages == [
        f"PV forecast response rejected for {source.entity_id}: "
        "last_update_success is not true"
    ]

    source.mutation = (("window", "quality_flags"), ["partial"])
    source.now = NOW + timedelta(seconds=180)
    await adapter.async_refresh(source.now)
    assert len(caplog.messages) == 2
    assert caplog.messages[-1].endswith("window quality_flags are not empty")

    source.error = HomeAssistantError("Temporary service failure")
    await adapter.async_refresh(NOW + timedelta(seconds=240))
    source.error = None
    source.now = NOW + timedelta(seconds=250)
    await adapter.async_refresh(source.now)
    assert len(caplog.messages) == 2


@pytest.mark.parametrize("reset", ["valid-response", "source-change"])
async def test_rejection_log_resets_after_recovery_or_source_change(
    pv_source: tuple[_Source, PvBridgeForecast],
    caplog: pytest.LogCaptureFixture,
    reset: str,
) -> None:
    """REQ-BRIDGE-CHARGE: a new rejection episode must be visible again."""
    source, adapter = pv_source
    source.mutation = (("last_update_success",), False)
    await adapter.async_refresh(NOW)
    assert len(caplog.messages) == 1

    if reset == "valid-response":
        source.mutation = None
        source.now = NOW + timedelta(seconds=60)
        await adapter.async_refresh(source.now)
        assert adapter.pv_start(source.now, 1000) == PV_START
        source.mutation = (("last_update_success",), False)
        source.now = NOW + timedelta(seconds=120)
    else:
        source.selected = None
        assert adapter.pv_start(NOW, 1000) is None
        source.selected = source.entity_id
        source.now = NOW + timedelta(seconds=1)

    await adapter.async_refresh(source.now)
    assert adapter.pv_start(source.now, 1000) is None
    assert len(caplog.messages) == 2
    assert caplog.messages[0] == caplog.messages[1]


@pytest.mark.parametrize("as_of_age", [0, 45, 60])
async def test_accepted_snapshot_survives_refresh_timeout_and_poll_jitter(
    pv_source: tuple[_Source, PvBridgeForecast], as_of_age: int
) -> None:
    """REQ-BRIDGE-CHARGE: accepted as_of ages must not cause periodic gaps."""
    source, adapter = pv_source
    source.mutation = (
        ("window", "as_of"),
        (NOW - timedelta(seconds=as_of_age)).isoformat(),
    )
    await adapter.async_refresh(NOW)

    for seconds in (0, 16, 59, 60, 62, 75):
        assert adapter.pv_start(NOW + timedelta(seconds=seconds), 1000) == PV_START
    assert adapter.pv_start(NOW + timedelta(seconds=76), 1000) is None


async def test_scheduled_refresh_retains_safe_snapshot_while_service_is_pending(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    """REQ-BRIDGE-CHARGE: a periodic writer may run during forecast refresh."""
    source, adapter = pv_source
    source.now = NOW - timedelta(seconds=45)
    await adapter.async_refresh(NOW)
    source.entered.clear()
    source.block = asyncio.Event()
    source.now = NOW + timedelta(seconds=62)

    refresh = asyncio.create_task(adapter.async_refresh(source.now))
    try:
        await source.entered.wait()
        assert adapter.pv_start(NOW + timedelta(seconds=64), 1000) == PV_START
    finally:
        source.block.set()
        await refresh
    assert adapter.pv_start(NOW + timedelta(seconds=64), 1000) == PV_START


async def test_transient_failure_retries_before_unchanged_snapshot_expires(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    """REQ-BRIDGE-CHARGE: a service failure must not enforce a full minute gap."""
    source, adapter = pv_source
    await adapter.async_refresh(NOW)
    source.error = HomeAssistantError("Temporary PV service failure")
    await adapter.async_refresh(NOW + timedelta(seconds=60))
    assert adapter.pv_start(NOW + timedelta(seconds=62), 1000) == PV_START

    for seconds in (61, 69):
        await adapter.async_refresh(NOW + timedelta(seconds=seconds))
    assert len(source.calls) == 2

    source.error = None
    source.now = NOW + timedelta(seconds=70)
    await adapter.async_refresh(source.now)
    assert len(source.calls) == 3
    assert adapter.pv_start(NOW + timedelta(seconds=76), 1000) == PV_START


async def test_repeated_failed_refreshes_cannot_extend_the_cache_deadline(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    """REQ-BRIDGE-CHARGE: retries never grant more lifetime to the old data."""
    source, adapter = pv_source
    await adapter.async_refresh(NOW)
    source.error = HomeAssistantError("PV service unavailable")
    for seconds in (60, 70, 80):
        await adapter.async_refresh(NOW + timedelta(seconds=seconds))
    assert len(source.calls) == 4
    assert adapter.pv_start(NOW + timedelta(seconds=76), 1000) is None


@pytest.mark.parametrize(
    "mutation",
    [
        (("last_update_success",), False),
        (("window", "intervals", 0, "mean_ac_power_kw"), 10**1000),
    ],
    ids=["failed-update", "numeric-overflow"],
)
async def test_invalid_refresh_immediately_revokes_the_previous_snapshot(
    pv_source: tuple[_Source, PvBridgeForecast],
    mutation: tuple[tuple[str | int, ...], Any],
) -> None:
    """REQ-BRIDGE-CHARGE: explicit unsafe forecast data overrides the reserve."""
    source, adapter = pv_source
    await adapter.async_refresh(NOW)
    source.now = NOW + timedelta(seconds=60)
    source.mutation = mutation
    await adapter.async_refresh(source.now)

    assert adapter.pv_start(source.now, 1000) is None


async def test_repeated_identical_response_cannot_renew_as_of_indefinitely(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    """REQ-BRIDGE-CHARGE: re-reading old data cannot grant unlimited permission."""
    source, adapter = pv_source
    await adapter.async_refresh(NOW)
    await adapter.async_refresh(NOW + timedelta(seconds=60))
    assert adapter.pv_start(NOW + timedelta(seconds=135), 1000) == PV_START
    assert adapter.pv_start(NOW + timedelta(seconds=136), 1000) is None
    await adapter.async_refresh(NOW + timedelta(seconds=136))
    assert len(source.calls) == 3
    assert adapter.pv_start(NOW + timedelta(seconds=136), 1000) is None


async def test_concurrent_refreshes_share_one_read(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    source, adapter = pv_source
    source.block = asyncio.Event()
    first = asyncio.create_task(adapter.async_refresh(NOW))
    await source.entered.wait()
    second = asyncio.create_task(adapter.async_refresh(NOW))
    source.block.set()
    await asyncio.gather(first, second)
    assert len(source.calls) == 1


async def test_queued_refresh_uses_receipt_time_after_a_delayed_service_response(
    pv_source: tuple[_Source, PvBridgeForecast], monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-BRIDGE-CHARGE: waiting for the shared read must not start another read."""
    source, adapter = pv_source
    monkeypatch.setattr(
        "custom_components.sax_power.infrastructure.pv_bridge_forecast.dt_util",
        SimpleNamespace(utcnow=lambda: source.now),
    )
    source.block = asyncio.Event()
    first = asyncio.create_task(adapter.async_refresh())
    await source.entered.wait()
    second = asyncio.create_task(adapter.async_refresh())
    await asyncio.sleep(0)
    source.now = NOW + timedelta(seconds=2)
    source.block.set()
    await asyncio.gather(first, second)

    assert len(source.calls) == 1
    assert adapter.pv_start(NOW + timedelta(seconds=77), 1000) == PV_START
    assert adapter.pv_start(NOW + timedelta(seconds=78), 1000) is None
    source.now = NOW + timedelta(seconds=61)
    await adapter.async_refresh()
    assert len(source.calls) == 1
    source.now = NOW + timedelta(seconds=62)
    await adapter.async_refresh()
    assert len(source.calls) == 2


async def test_initial_failed_refresh_grants_no_permission_and_retries_soon(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    source, adapter = pv_source
    source.error = HomeAssistantError("PV source offline")
    await adapter.async_refresh(NOW)
    assert adapter.pv_start(NOW, 1000) is None
    await adapter.async_refresh(NOW + timedelta(seconds=9))
    assert len(source.calls) == 1
    source.error = None
    source.now = NOW + timedelta(seconds=10)
    await adapter.async_refresh(source.now)
    assert len(source.calls) == 2
    assert adapter.pv_start(source.now, 1000) == PV_START


@pytest.mark.parametrize("has_snapshot", [False, True])
async def test_timeout_keeps_only_previously_accepted_data_and_retries_soon(
    pv_source: tuple[_Source, PvBridgeForecast],
    monkeypatch: pytest.MonkeyPatch,
    has_snapshot: bool,
) -> None:
    """REQ-BRIDGE-CHARGE: a slow service gets a bounded retry without new permission."""
    source, adapter = pv_source
    if has_snapshot:
        await adapter.async_refresh(NOW)
        source.now = NOW + timedelta(seconds=60)
    monkeypatch.setattr(
        "custom_components.sax_power.infrastructure.pv_bridge_forecast._SERVICE_TIMEOUT",
        0.01,
    )
    source.block = asyncio.Event()
    try:
        await adapter.async_refresh(source.now)
        assert adapter.pv_start(source.now, 1000) == (
            PV_START if has_snapshot else None
        )
        assert len(source.calls) == (2 if has_snapshot else 1)
        await adapter.async_refresh(source.now + timedelta(seconds=9))
        assert len(source.calls) == (2 if has_snapshot else 1)
    finally:
        source.block.set()
    source.now += timedelta(seconds=10)
    await adapter.async_refresh(source.now)
    assert len(source.calls) == (3 if has_snapshot else 2)
    assert adapter.pv_start(source.now, 1000) == PV_START


@pytest.mark.parametrize("selected", [None, "sensor.missing", "switch.pv"])
async def test_source_change_immediately_invalidates_cached_data(
    pv_source: tuple[_Source, PvBridgeForecast], selected: str | None
) -> None:
    source, adapter = pv_source
    await adapter.async_refresh(NOW)
    source.selected = selected
    assert adapter.pv_start(NOW, 1000) is None
    await adapter.async_refresh(NOW)
    assert len(source.calls) == 1


async def test_source_change_during_read_cannot_publish_old_plant_data(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    source, adapter = pv_source
    source.block = asyncio.Event()
    task = asyncio.create_task(adapter.async_refresh(NOW))
    await source.entered.wait()
    source.selected = None
    source.block.set()
    await task
    assert adapter.pv_start(NOW, 1000) is None


async def test_unloaded_plant_immediately_invalidates_cached_data(
    hass: HomeAssistant, pv_source: tuple[_Source, PvBridgeForecast]
) -> None:
    source, adapter = pv_source
    await adapter.async_refresh(NOW)
    source.entry.mock_state(hass, ConfigEntryState.NOT_LOADED)
    assert adapter.pv_start(NOW, 1000) is None


@pytest.mark.parametrize(
    ("domain", "platform"), [("template", "pv_forecast"), ("pv_forecast", "template")]
)
async def test_foreign_registry_sources_do_not_call_pv_forecast(
    hass: HomeAssistant,
    pv_source: tuple[_Source, PvBridgeForecast],
    domain: str,
    platform: str,
) -> None:
    source, adapter = pv_source
    entry = MockConfigEntry(domain=domain, data={"time_zone": "Europe/Berlin"})
    entry.add_to_hass(hass)
    entry.mock_state(hass, ConfigEntryState.LOADED)
    registered = er.async_get(hass).async_get_or_create(
        "sensor", platform, "foreign", config_entry=entry
    )
    source.selected = registered.entity_id
    await adapter.async_refresh(NOW)
    assert adapter.pv_start(NOW, 1000) is None
    assert source.calls == []


async def test_missing_service_never_uses_the_energy_sensor_as_a_pv_start(
    hass: HomeAssistant, pv_source: tuple[_Source, PvBridgeForecast]
) -> None:
    source, adapter = pv_source
    hass.states.async_set(source.entity_id, "999", {"unit_of_measurement": "kWh"})
    hass.services.async_remove("pv_forecast", "get_forecast")
    await adapter.async_refresh(NOW)
    assert adapter.pv_start(NOW, 1000) is None


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("schema_version",), 2),
        (("schema_version",), True),
        (("last_update_success",), False),
        (("origin",), "restored"),
        (("window", "schema_version"), 2),
        (("window", "schema_version"), True),
        (("window", "scope"), "roof"),
        (("window", "status"), "unavailable"),
        (("window", "reason"), "stale_forecast"),
        (("window", "quality_flags"), ["temperature_fallback"]),
        (("window", "coverage", "complete"), False),
        (("window", "coverage", "start"), NOW.isoformat()),
        (("window", "timezone"), "UTC"),
        (("window", "step_minutes"), 30),
        (("window", "assumption"), "instantaneous_power"),
        (("window", "as_of"), (NOW + timedelta(seconds=1)).isoformat()),
        (("window", "as_of"), (NOW - timedelta(seconds=61)).isoformat()),
        (("window", "fetched_at"), (NOW + timedelta(seconds=1)).isoformat()),
        (("window", "fetched_at"), (NOW - timedelta(minutes=61)).isoformat()),
        (("window", "fetched_at"), "2026-09-13T20:00:00"),
        (("window", "fetched_at"), None),
        (("window", "intervals"), []),
        (("window", "intervals", 1, "start"), "2026-09-13T21:00:00+00:00"),
        (("window", "intervals", 0, "mean_ac_power_kw"), -1),
        (("window", "intervals", 0, "mean_ac_power_kw"), float("nan")),
        (("window", "intervals", 0, "mean_ac_power_kw"), float("inf")),
        (("window", "intervals", 0, "mean_ac_power_kw"), True),
        (("window", "intervals", 0, "energy_kwh"), 10),
        (("window", "energy_kwh"), 9000),
        (("window", "mean_ac_power_kw"), 9000),
    ],
)
async def test_invalid_or_unsafe_contract_never_authorizes_a_pv_deadline(
    pv_source: tuple[_Source, PvBridgeForecast],
    path: tuple[str | int, ...],
    value: Any,
) -> None:
    source, adapter = pv_source
    source.mutation = (path, value)
    await adapter.async_refresh(NOW)
    assert adapter.pv_start(NOW, 1000) is None


@pytest.mark.parametrize(
    ("weather_age", "accepted"),
    [
        (timedelta(minutes=58, seconds=45), True),
        (timedelta(minutes=58, seconds=45, microseconds=1), False),
        (timedelta(minutes=59, seconds=30), False),
        (timedelta(minutes=60), False),
    ],
)
async def test_weather_age_must_leave_the_entire_cache_reserve(
    pv_source: tuple[_Source, PvBridgeForecast],
    weather_age: timedelta,
    accepted: bool,
) -> None:
    """REQ-BRIDGE-CHARGE: the reserve never exceeds the 60 minute weather limit."""
    source, adapter = pv_source
    source.mutation = (
        ("window", "fetched_at"),
        (NOW - weather_age).isoformat(),
    )
    await adapter.async_refresh(NOW)
    assert adapter.pv_start(NOW, 1000) == (PV_START if accepted else None)
    assert adapter.pv_start(NOW + timedelta(seconds=75), 1000) == (
        PV_START if accepted else None
    )
    assert adapter.pv_start(NOW + timedelta(seconds=75, microseconds=1), 1000) is None


@pytest.mark.parametrize("consumption", [None, True, -1, 0, float("nan"), float("inf")])
async def test_invalid_consumption_has_no_comparison_threshold(
    pv_source: tuple[_Source, PvBridgeForecast], consumption: Any
) -> None:
    _source, adapter = pv_source
    await adapter.async_refresh(NOW)
    assert adapter.pv_start(NOW, consumption) is None


async def test_forecast_does_not_survive_a_backwards_clock_jump(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    _source, adapter = pv_source
    await adapter.async_refresh(NOW)
    assert adapter.pv_start(NOW - timedelta(seconds=1), 1000) is None


async def test_spring_dst_request_stays_inside_the_two_local_forecast_days(
    pv_source: tuple[_Source, PvBridgeForecast],
) -> None:
    source, adapter = pv_source
    source.now = datetime(2026, 3, 28, 22, 50, tzinfo=UTC)
    await adapter.async_refresh(source.now)
    window = source.calls[0]["window"]
    assert window["start"] == "2026-03-28T23:00:00+00:00"
    assert window["end"] == "2026-03-29T22:00:00+00:00"
