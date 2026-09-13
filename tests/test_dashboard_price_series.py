"""Full tariff-day coverage and boundaries for the shared Stromtarif view."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    DOMAIN,
    ECONOMICS_TOU_WINDOW_KEYS,
)
from custom_components.sax_power.dashboard_api import async_register_dashboard_api
from custom_components.sax_power.dashboard_price_series import price_series
from custom_components.sax_power.dashboard_tariff import SERIES_COMMAND


def _options(tariff_type: str = "dynamic") -> dict[str, Any]:
    return {
        CONF_ECONOMICS_TARIFF_TYPE: tariff_type,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_PRICE_SENSOR: "sensor.price",
        CONF_PRICE_UNIT: "auto",
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
        ECONOMICS_TOU_WINDOW_KEYS[0]: {
            "start": "22:00",
            "end": "06:00",
            "price_eur_kwh": 0.2,
        },
    }


@pytest.mark.parametrize("day,hours", [("2026-03-29", 23), ("2026-10-25", 25)])
@pytest.mark.parametrize("tariff_type", ["dynamic", "time_of_use"])
async def test_price_series_covers_the_real_local_dst_day(
    hass: HomeAssistant, freezer: Any, day: str, hours: int, tariff_type: str
) -> None:
    await hass.config.async_set_time_zone("Europe/Berlin")
    now = datetime.fromisoformat(f"{day}T10:00:00+00:00")
    freezer.move_to(now)
    hass.states.async_set(
        "sensor.price",
        "20",
        {"unit_of_measurement": "ct/kWh", "today": [20.0] * (hours * 4)},
    )
    result = price_series(
        hass, _options(tariff_type), day="today", revision="one", now=now
    )
    start, end = datetime.fromisoformat(result["start"]), datetime.fromisoformat(
        result["end"]
    )
    assert end - start == timedelta(hours=hours)
    assert result["date"] == day
    assert result["time_zone"] == "Europe/Berlin"
    assert result["status"] == "available"
    assert result["gaps"] == []
    assert (
        sum(
            (
                datetime.fromisoformat(slot["end"])
                - datetime.fromisoformat(slot["start"])
            ).total_seconds()
            for slot in result["slots"]
        )
        == hours * 3600
    )
    assert result["current_price_ct_kwh"] == (20 if tariff_type == "dynamic" else 32)
    if tariff_type == "dynamic":
        assert len(result["slots"]) == hours * 4


async def test_today_and_tomorrow_include_all_source_slots_not_only_planned_charges(
    hass: HomeAssistant,
    freezer: Any,
) -> None:
    await hass.config.async_set_time_zone("Europe/Berlin")
    now = datetime(2026, 9, 13, 10, tzinfo=UTC)
    freezer.move_to(now)
    today = list(range(24))
    tomorrow = list(range(-10, 14))
    hass.states.async_set(
        "sensor.price",
        "12",
        {"unit_of_measurement": "ct/kWh", "today": today, "tomorrow": tomorrow},
    )
    for day, values in (("today", today), ("tomorrow", tomorrow)):
        result = price_series(hass, _options(), day=day, revision="one", now=now)
        assert result["status"] == "available"
        assert [slot["price_ct_kwh"] for slot in result["slots"]] == values
        assert result["current_price_ct_kwh"] == 12


async def test_stale_relative_prices_do_not_move_to_a_new_calendar_day(
    hass: HomeAssistant,
    freezer: Any,
) -> None:
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-09-13T10:00:00+00:00")
    hass.states.async_set(
        "sensor.price", "12", {"unit_of_measurement": "ct/kWh", "today": [12.0] * 24}
    )
    result = price_series(
        hass,
        _options(),
        day="today",
        revision="one",
        now=datetime(2026, 9, 14, 10, tzinfo=UTC),
    )
    assert result["status"] == "unavailable"
    assert result["slots"] == []
    assert result["current_price_ct_kwh"] is None


@pytest.mark.parametrize(
    "state,unit,reason",
    [
        ("unknown", "ct/kWh", "price_sensor_unavailable"),
        ("unavailable", "ct/kWh", "price_sensor_unavailable"),
        ("30", "W", "price_unit_unsupported"),
    ],
)
async def test_unavailable_or_wrong_unit_cannot_reuse_old_forecast_attributes(
    hass: HomeAssistant,
    freezer: Any,
    state: str,
    unit: str,
    reason: str,
) -> None:
    now = datetime(2026, 9, 13, 10, tzinfo=UTC)
    freezer.move_to(now)
    hass.states.async_set(
        "sensor.price", state, {"unit_of_measurement": unit, "today": [30.0] * 24}
    )
    result = price_series(hass, _options(), day="today", revision="one", now=now)
    assert result["slots"] == []
    assert result["current_price_ct_kwh"] is None
    assert result["reason"] == reason


async def test_missing_forecast_does_not_invent_a_full_day_from_the_current_state(
    hass: HomeAssistant,
    freezer: Any,
) -> None:
    now = datetime(2026, 9, 13, 10, tzinfo=UTC)
    freezer.move_to(now)
    hass.states.async_set("sensor.price", "31.2", {"unit_of_measurement": "ct/kWh"})
    result = price_series(hass, _options(), day="today", revision="one", now=now)
    assert result["slots"] == []
    assert result["current_price_ct_kwh"] == 31.2
    assert result["gaps"] == [{"start": result["start"], "end": result["end"]}]


@pytest.mark.parametrize("source", [None, "", False])
async def test_incomplete_dynamic_profile_reports_a_missing_source(
    hass: HomeAssistant, source: Any
) -> None:
    result = price_series(
        hass,
        {**_options(), CONF_PRICE_SENSOR: source},
        day="today",
        revision="one",
    )
    assert result["status"] == "unavailable"
    assert result["reason"] == "price_sensor_not_configured"
    assert result["slots"] == []
    assert result["current_price_ct_kwh"] is None


async def test_out_of_range_prices_leave_gaps_without_hiding_valid_neighbors(
    hass: HomeAssistant, freezer: Any
) -> None:
    await hass.config.async_set_time_zone("UTC")
    now = datetime(2026, 9, 13, 1, 30, tzinfo=UTC)
    freezer.move_to(now)
    values = [20, 501, -201, -200, 500, *([30] * 19)]
    hass.states.async_set(
        "sensor.price", "501", {"unit_of_measurement": "ct/kWh", "today": values}
    )
    result = price_series(hass, _options(), day="today", revision="one", now=now)
    assert result["status"] == "partial"
    assert result["current_price_ct_kwh"] is None
    assert [slot["price_ct_kwh"] for slot in result["slots"]] == [
        20,
        -200,
        500,
        *([30] * 19),
    ]
    assert result["gaps"] == [
        {
            "start": "2026-09-13T01:00:00+00:00",
            "end": "2026-09-13T03:00:00+00:00",
        }
    ]


async def test_overlap_and_missing_prices_are_explicit_gaps(
    hass: HomeAssistant,
    freezer: Any,
) -> None:
    await hass.config.async_set_time_zone("UTC")
    now = datetime(2026, 9, 13, 1, 30, tzinfo=UTC)
    freezer.move_to(now)
    hass.states.async_set(
        "sensor.price",
        "20",
        {
            "unit_of_measurement": "ct/kWh",
            "prices": [
                {
                    "start": "2026-09-13T00:00:00+00:00",
                    "end": "2026-09-13T02:00:00+00:00",
                    "price": 20,
                },
                {
                    "start": "2026-09-13T01:00:00+00:00",
                    "end": "2026-09-13T03:00:00+00:00",
                    "price": -5,
                },
                {
                    "start": "2026-09-13T04:00:00+00:00",
                    "end": "2026-09-13T05:00:00+00:00",
                    "price": 12,
                },
            ],
        },
    )
    result = price_series(hass, _options(), day="today", revision="one", now=now)
    assert result["status"] == "partial"
    assert result["current_price_ct_kwh"] is None
    assert all(
        not (
            datetime.fromisoformat(slot["start"])
            <= now
            < datetime.fromisoformat(slot["end"])
        )
        for slot in result["slots"]
    )
    assert result["slots"][-1]["price_ct_kwh"] == 12
    assert any(
        datetime.fromisoformat(gap["start"]) <= now < datetime.fromisoformat(gap["end"])
        for gap in result["gaps"]
    )


@pytest.mark.parametrize(
    "unit,value",
    [("ct_kwh", 20), ("eur_kwh", 0.2), ("eur_mwh", 200), ("ct_mwh", 20000)],
)
async def test_explicit_source_units_are_always_returned_as_cents(
    hass: HomeAssistant,
    freezer: Any,
    unit: str,
    value: float,
) -> None:
    now = datetime(2026, 9, 13, 10, tzinfo=UTC)
    freezer.move_to(now)
    hass.states.async_set("sensor.price", str(value), {"today": [value] * 24})
    result = price_series(
        hass,
        {**_options(), CONF_PRICE_UNIT: unit},
        day="today",
        revision="one",
        now=now,
    )
    assert result["status"] == "available"
    assert {slot["price_ct_kwh"] for slot in result["slots"]} == {20}


async def test_series_checks_underlying_source_read_permissions(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    hass_read_only_user: MockUser,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=_options())
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    ids = [
        registry.async_get_or_create(
            "sensor", DOMAIN, f"{entry.entry_id}_{key}", config_entry=entry
        ).entity_id
        for key in ("economics_current_import_price", "economics_feed_in_price")
    ]
    hass_read_only_user.mock_policy(
        {"entities": {"entity_ids": {entity_id: {"read": True} for entity_id in ids}}}
    )
    async_register_dashboard_api(hass)
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    await client.send_json_auto_id(
        {"type": SERIES_COMMAND, "entry_id": entry.entry_id, "day": "today"}
    )
    assert (await client.receive_json())["error"]["code"] == "forbidden"
