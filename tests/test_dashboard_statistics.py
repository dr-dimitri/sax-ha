"""Recorder-Parität und Zugriffsgrenzen für Vue (REQ-VUE-SAVINGS)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.components.recorder import Recorder, statistics
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.tasks import StatisticsTask
from homeassistant.const import EVENT_RECORDER_5MIN_STATISTICS_GENERATED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.recorder import DATA_INSTANCE
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_recorder_block_till_done,
)
from pytest_homeassistant_custom_component.typing import (
    MockHAClientWebSocket,
    WebSocketGenerator,
)

from custom_components.sax_power.const import DOMAIN
from custom_components.sax_power.dashboard_api import async_register_dashboard_api
from custom_components.sax_power.dashboard_statistics import STATISTICS_COMMAND

_MODULE = "custom_components.sax_power.dashboard_statistics"
_ZONE = ZoneInfo("Europe/Berlin")


@pytest.fixture
def mock_recorder_before_hass(recorder_db_url: str) -> None:
    """Initialisiere die echte Recorder-Datenbank vor der hass-Fixture."""


@pytest.fixture
def dashboard_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    async_register_dashboard_api(hass)
    return entry


def _entity(hass: HomeAssistant, entry: MockConfigEntry) -> str:
    return (
        er.async_get(hass)
        .async_get_or_create(
            "sensor",
            DOMAIN,
            f"{entry.entry_id}_economics_net_savings",
            config_entry=entry,
            suggested_object_id="renamed_net_savings",
        )
        .entity_id
    )


async def _request(
    client: MockHAClientWebSocket, entry: MockConfigEntry, **kwargs: Any
) -> dict[str, Any]:
    await client.send_json_auto_id(
        {"type": STATISTICS_COMMAND, "entry_id": entry.entry_id, **kwargs}
    )
    return await client.receive_json()


async def _client_at_frozen_time(
    hass: HomeAssistant, factory: WebSocketGenerator, user: MockUser
) -> MockHAClientWebSocket:
    """Recorder-Zeitreisen brauchen ein erst am Zielzeitpunkt ausgestelltes JWT."""
    refresh_token = await hass.auth.async_create_refresh_token(user, "recorder-test")
    return await factory(
        hass, access_token=hass.auth.async_create_access_token(refresh_token)
    )


async def test_optional_entity_and_recorder_absence_are_explicit(
    hass: HomeAssistant,
    dashboard_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Ohne Statistikquelle gibt es null statt einer erfundenen Live-Bilanz."""
    client = await hass_ws_client(hass)
    with patch(f"{_MODULE}._read_statistics") as read:
        response = await _request(client, dashboard_entry)
        assert response["success"]
        assert response["result"]["status"] == "missing_entity"
        assert response["result"]["entity_id"] is None
        entity_id = _entity(hass, dashboard_entry)
        hass.states.async_set(entity_id, "9999.99")
        response = await _request(client, dashboard_entry)
        assert response["success"]
        assert response["result"]["status"] == "recorder_unavailable"
        assert response["result"]["entity_id"] == entity_id
        assert response["result"]["selected"]["change"] is None
        assert response["result"]["selected"]["buckets"] == []
        assert all(
            period["change"] is None
            for period in response["result"]["periods"].values()
        )
        read.assert_not_called()


@pytest.mark.parametrize(
    "fields",
    [
        {"start_date": "2026-01-01"},
        {"end_date": "2026-01-01"},
        {"start_date": "2026-02-30", "end_date": "2026-03-01"},
        {"start_date": "2026-03-02", "end_date": "2026-03-01"},
        {"start_date": "2026-1-1", "end_date": "2026-01-02"},
        {"start_date": "0000-01-01", "end_date": "2026-01-02"},
        {"start_date": "9999-12-31", "end_date": "9999-12-31"},
        {"first_weekday": "tomorrow"},
    ],
)
async def test_invalid_ranges_never_reach_recorder(
    hass: HomeAssistant,
    dashboard_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    fields: dict[str, str],
) -> None:
    """Ungültige und unvollständige Auswahlen lösen keine Datenbankabfrage aus."""
    _entity(hass, dashboard_entry)
    client = await hass_ws_client(hass)
    with patch(f"{_MODULE}._read_statistics") as read:
        response = await _request(client, dashboard_entry, **fields)
    assert response["error"]["code"] == "invalid_format"
    read.assert_not_called()


@pytest.mark.parametrize("domain", ["demo", DOMAIN])
async def test_foreign_and_removed_entries_are_rejected(
    hass: HomeAssistant,
    dashboard_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    domain: str,
) -> None:
    """Fremde Config Entries liefern keine Statistikdaten."""
    other = MockConfigEntry(domain=domain, data={})
    if domain != DOMAIN:
        other.add_to_hass(hass)
    client = await hass_ws_client(hass)
    response = await _request(client, other)
    assert response["error"]["code"] == "not_found"


async def test_registry_owner_and_disabled_entities_are_respected(
    hass: HomeAssistant,
    dashboard_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Ein nachgebildeter unique_id-Suffix allein gewährt keinen fremden Zugriff."""
    other = MockConfigEntry(domain=DOMAIN, data={})
    other.add_to_hass(hass)
    registry = er.async_get(hass)
    entity = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{dashboard_entry.entry_id}_economics_net_savings",
        config_entry=other,
    )
    client = await hass_ws_client(hass)
    assert (await _request(client, dashboard_entry))["result"]["status"] == (
        "missing_entity"
    )
    registry.async_remove(entity.entity_id)
    entity_id = _entity(hass, dashboard_entry)
    registry.async_update_entity(entity_id, disabled_by=er.RegistryEntryDisabler.USER)
    assert (await _request(client, dashboard_entry))["result"]["status"] == (
        "missing_entity"
    )


async def test_permissions_apply_to_resolved_statistic_entity(
    hass: HomeAssistant,
    dashboard_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    hass_read_only_user: MockUser,
) -> None:
    """Lesezugriff reicht aus; ohne Entity-Leserecht bleibt auch Recorder verborgen."""
    entity_id = _entity(hass, dashboard_entry)
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    assert (await _request(client, dashboard_entry))["success"]
    hass_read_only_user.mock_policy({"entities": {}})
    with patch(f"{_MODULE}._read_statistics") as read:
        response = await _request(client, dashboard_entry)
    assert response["error"]["code"] == "unauthorized"
    read.assert_not_called()
    hass_read_only_user.mock_policy(
        {"entities": {"entity_ids": {entity_id: {"read": True}}}}
    )
    assert (await _request(client, dashboard_entry))["success"]


@pytest.mark.parametrize("change", ["permission", "rename", "remove"])
async def test_pending_results_are_rechecked_before_disclosure(
    hass: HomeAssistant,
    dashboard_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    hass_read_only_user: MockUser,
    change: str,
) -> None:
    """Änderungen während der SQL-Abfrage geben kein altes Ergebnis frei."""
    entity_id = _entity(hass, dashboard_entry)
    started, finish = asyncio.Event(), asyncio.Event()

    async def delayed(*args: Any) -> dict[str, Any]:
        started.set()
        await finish.wait()
        return args[3]

    recorder = MagicMock()
    recorder.async_add_executor_job = AsyncMock(side_effect=delayed)
    hass.data[DATA_INSTANCE] = recorder
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    await client.send_json_auto_id(
        {"type": STATISTICS_COMMAND, "entry_id": dashboard_entry.entry_id}
    )
    await started.wait()
    if change == "permission":
        hass_read_only_user.mock_policy({"entities": {}})
    elif change == "rename":
        er.async_get(hass).async_update_entity(entity_id, new_entity_id="sensor.new_id")
    else:
        await hass.config_entries.async_remove(dashboard_entry.entry_id)
    finish.set()
    response = await client.receive_json()
    assert response["error"]["code"] == (
        "unauthorized" if change == "permission" else "not_found"
    )
    hass.data.pop(DATA_INSTANCE)


async def test_recorder_failure_is_not_a_successful_zero(
    hass: HomeAssistant,
    dashboard_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """SQL-Fehler bleiben als Fehler erkennbar und betreffen keine Geräteaktion."""
    _entity(hass, dashboard_entry)
    recorder = MagicMock()
    recorder.async_add_executor_job = AsyncMock(side_effect=RuntimeError("SQL failed"))
    hass.data[DATA_INSTANCE] = recorder
    client = await hass_ws_client(hass)
    response = await _request(client, dashboard_entry)
    assert response["error"]["code"] == "recorder_error"
    assert "result" not in response
    hass.data.pop(DATA_INSTANCE)


async def test_read_only_user_can_subscribe_to_native_statistics_refresh(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
) -> None:
    """Auch Lesebenutzer aktualisieren die Vue-Auswertung ohne Sensor-Polling."""
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    await client.send_json_auto_id(
        {
            "type": "subscribe_events",
            "event_type": EVENT_RECORDER_5MIN_STATISTICS_GENERATED,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    hass.bus.async_fire(EVENT_RECORDER_5MIN_STATISTICS_GENERATED)
    event = await client.receive_json()
    assert event["event"]["event_type"] == EVENT_RECORDER_5MIN_STATISTICS_GENERATED
    await client.send_json_auto_id(
        {"type": "unsubscribe_events", "subscription": response["id"]}
    )
    assert (await client.receive_json())["success"]


async def _assert_native_parity(
    recorder: Recorder,
    result: dict[str, Any],
    entity_id: str,
    first_weekday: str,
) -> None:
    """Vergleiche gegen dieselben öffentlichen Recorder-Aufrufe wie HA-Core-Karten."""
    from homeassistant.components.recorder.util import resolve_period

    hass = recorder.hass
    for period, value in result["periods"].items():
        definition = {"calendar": {"period": period}}
        if period == "week":
            definition["calendar"]["first_weekday"] = first_weekday
        start, end = resolve_period(definition)
        native = await recorder.async_add_executor_job(
            statistics.statistic_during_period,
            hass,
            start,
            end,
            entity_id,
            {"change"},
            None,
        )
        assert value == {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "change": native.get("change"),
        }
    selection = result["selected"]
    start = datetime.fromisoformat(selection["start"])
    end = datetime.fromisoformat(selection["end"])
    native_total = await recorder.async_add_executor_job(
        statistics.statistic_during_period,
        hass,
        start,
        end,
        entity_id,
        {"change"},
        None,
    )
    assert selection["change"] == native_total.get("change")
    native_buckets = await recorder.async_add_executor_job(
        statistics.statistics_during_period,
        hass,
        start,
        end - timedelta(milliseconds=1),
        {entity_id},
        selection["period"],
        None,
        {"change"},
    )
    assert selection["buckets"] == [
        {
            "start": datetime.fromtimestamp(row["start"], UTC).isoformat(),
            "end": datetime.fromtimestamp(row["end"], UTC).isoformat(),
            "change": row.get("change"),
        }
        for row in native_buckets.get(entity_id, [])
    ]


@pytest.mark.parametrize(
    ("start_date", "end_date", "period", "hours", "first_weekday"),
    [
        ("2026-03-29", "2026-03-29", "hour", 23, "mon"),
        ("2026-10-25", "2026-10-25", "hour", 25, "sun"),
        ("2026-03-28", "2026-03-30", "hour", 71, "mon"),
        ("2026-03-28", "2026-03-31", "day", 95, "mon"),
        ("2026-02-01", "2026-03-31", "month", 1415, "mon"),
    ],
)
async def test_calendar_and_selection_match_real_recorder_across_dst(
    recorder_mock: Recorder,
    freezer: Any,
    dashboard_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_admin_user: MockUser,
    start_date: str,
    end_date: str,
    period: str,
    hours: int,
    first_weekday: str,
) -> None:
    """Kalendergrenzen, Stundenauflösung und signierte Änderungen entsprechen HA."""
    hass = recorder_mock.hass
    await hass.config.async_set_time_zone("Europe/Berlin")
    entity_id = _entity(hass, dashboard_entry)
    start = datetime.fromisoformat(start_date).replace(tzinfo=_ZONE).astimezone(UTC)
    end_local = datetime.fromisoformat(end_date).replace(tzinfo=_ZONE) + timedelta(
        days=1
    )
    end = end_local.astimezone(UTC)
    freezer.move_to(end + timedelta(hours=2, minutes=7))
    assert (end - start).total_seconds() / 3600 == hours
    rows = []
    total = 0.0
    for index in range(hours + 1):
        value = (-3.0, 2.0, -1.0)[index % 3]
        total += value
        rows.append(
            {
                "start": start + timedelta(hours=index - 1),
                "state": total,
                "sum": total,
            }
        )
    statistics.async_import_statistics(
        hass,
        {
            "source": "recorder",
            "statistic_id": entity_id,
            "name": None,
            "unit_class": None,
            "unit_of_measurement": "EUR",
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
        },
        rows,
    )
    await async_recorder_block_till_done(hass)
    # Der Vorlaufbetrag ist nur Amortisationskontext; selbst riesige Livewerte
    # dürfen weder Recorder-Abfragen ersetzen noch deren Ergebnis erhöhen.
    hass.states.async_set(entity_id, "987654.32", {"unit_of_measurement": "EUR"})
    hass.states.async_set("sensor.roi", "50", {"prior_result_eur": 999999.0})
    client = await _client_at_frozen_time(hass, hass_ws_client, hass_admin_user)
    response = await _request(
        client,
        dashboard_entry,
        start_date=start_date,
        end_date=end_date,
        first_weekday=first_weekday,
    )
    assert response["success"]
    result = response["result"]
    assert result["status"] == "ok"
    assert result["time_zone"] == "Europe/Berlin"
    assert result["today"] == dt_util.now().date().isoformat()
    assert result["selected"]["period"] == period
    assert result["selected"]["start"] == start.isoformat()
    assert result["selected"]["end"] == end.isoformat()
    assert result["selected"]["change"] < 0
    await _assert_native_parity(recorder_mock, result, entity_id, first_weekday)


async def test_real_recorder_without_statistics_stays_empty(
    recorder_mock: Recorder,
    dashboard_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Auch bei laufendem Recorder sind fehlende Messreihen keine Nullersparnis."""
    hass = recorder_mock.hass
    entity_id = _entity(hass, dashboard_entry)
    hass.states.async_set(entity_id, "12.34")
    response = await _request(await hass_ws_client(hass), dashboard_entry)
    assert response["success"]
    result = response["result"]
    assert result["status"] == "ok"
    assert result["selected"]["change"] is None
    assert result["selected"]["buckets"] == []
    await _assert_native_parity(recorder_mock, result, entity_id, "mon")


async def test_native_sensor_statistics_preserve_negative_balance_restart(
    recorder_mock: Recorder,
    freezer: Any,
    dashboard_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_admin_user: MockUser,
) -> None:
    """Echte Sensor-/Recorder-Kompilierung erhält -10 + 2 EUR über last_reset hinweg."""
    hass = recorder_mock.hass
    assert await async_setup_component(hass, "sensor", {})
    entity_id = _entity(hass, dashboard_entry)
    first = datetime(2026, 8, 29, 10, tzinfo=UTC)
    first_reset = first - timedelta(days=1)
    second_reset = first + timedelta(minutes=6)

    def set_total(value: float, reset: datetime) -> None:
        hass.states.async_set(
            entity_id,
            str(value),
            {
                "device_class": "monetary",
                "state_class": "total",
                "unit_of_measurement": "EUR",
                "last_reset": reset.isoformat(),
            },
        )

    freezer.move_to(first - timedelta(minutes=4))
    set_total(0.0, first_reset)
    await async_recorder_block_till_done(hass)
    recorder_mock.queue_task(StatisticsTask(first - timedelta(minutes=5), False))
    await async_recorder_block_till_done(hass)
    freezer.move_to(first + timedelta(seconds=10))
    set_total(0.0, first_reset)
    freezer.move_to(first + timedelta(minutes=1))
    set_total(-10.0, first_reset)
    await async_recorder_block_till_done(hass)
    recorder_mock.queue_task(StatisticsTask(first, False))
    await async_recorder_block_till_done(hass)
    freezer.move_to(second_reset)
    set_total(0.0, second_reset)
    freezer.move_to(first + timedelta(minutes=7))
    set_total(2.0, second_reset)
    await async_recorder_block_till_done(hass)
    recorder_mock.queue_task(StatisticsTask(first + timedelta(minutes=5), False))
    await async_recorder_block_till_done(hass)
    freezer.move_to(first + timedelta(hours=1, minutes=7))
    recorder_mock.queue_task(StatisticsTask(first + timedelta(minutes=55), False))
    await async_recorder_block_till_done(hass)

    response = await _request(
        await _client_at_frozen_time(hass, hass_ws_client, hass_admin_user),
        dashboard_entry,
        start_date="2026-08-29",
        end_date="2026-08-29",
    )
    assert response["success"]
    result = response["result"]
    assert result["selected"]["change"] == -8.0
    await _assert_native_parity(recorder_mock, result, entity_id, "mon")

    freezer.move_to(first + timedelta(hours=1, minutes=8))
    set_total(5.0, second_reset)
    await async_recorder_block_till_done(hass)
    recorder_mock.queue_task(
        StatisticsTask(first + timedelta(hours=1, minutes=5), False)
    )
    await async_recorder_block_till_done(hass)
    freezer.move_to(first + timedelta(hours=1, minutes=12))
    response = await _request(
        await _client_at_frozen_time(hass, hass_ws_client, hass_admin_user),
        dashboard_entry,
        start_date="2026-08-29",
        end_date="2026-08-29",
    )
    updated = response["result"]
    assert updated["selected"]["change"] == -5.0
    # Die Core-Kennzahl berücksichtigt bereits die 5-Minuten-Randperiode,
    # während der unveränderte Stunden-Graph noch die letzte volle Stunde zeigt.
    assert updated["selected"]["buckets"] == result["selected"]["buckets"]
    await _assert_native_parity(recorder_mock, updated, entity_id, "mon")
