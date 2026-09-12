"""REQ-HEMS-DYNAMIC: adaptive price permission and immutable cycle spending."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import State

from custom_components.sax_power.const import PRICE_STRATEGY_ADAPTIVE
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.hems import ChargeInterval
from custom_components.sax_power.infrastructure.price_plan_store import (
    PricePlanCycleStore,
)
from custom_components.sax_power.price_optimizer import PriceSlot, parse_price_slots

NOW = datetime(2026, 9, 13, 4, tzinfo=UTC)


def at(hours: float) -> datetime:
    return NOW + timedelta(hours=hours)


def price(start: float, end: float, value: float = 0.1) -> PriceSlot:
    return PriceSlot(at(start), at(end), value)


def allocation(start: float, end: float) -> ChargeInterval:
    return ChargeInterval(at(start), at(end), (end - start) * 4)


def coordinator(hass, *, entry_id: str = "adaptive-budget") -> SaxPowerCoordinator:
    client = MagicMock()
    client.connected = True
    client.write_register = AsyncMock()
    result = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=entry_id,
    )
    result._price_charge_enabled = True
    result._price_charge_strategy = PRICE_STRATEGY_ADAPTIVE
    result._price_charge_hours = 2
    result._price_charge_max_price = 0.2
    result._price_charge_neutral_price = 0.3
    result.data = {"soc": 20, "battery_capacity": 10000, "ic_max_power_reference": 4000}
    return result


def source(entries, *, unit="EUR/kWh", state="0.1"):
    return State(
        "sensor.price", state, {"raw_today": entries, "unit_of_measurement": unit}
    )


def entry(start, end=None, value=0.1):
    data = {"start": at(start).isoformat(), "value": value}
    if end is not None:
        data["end"] = at(end).isoformat()
    return data


def test_strict_parser_never_extends_last_unbounded_price():
    data = source([entry(0), entry(1)])
    strict = parse_price_slots(data, strict=True, now=NOW)
    assert [(item.start, item.end) for item in strict] == [(NOW, at(1))]
    assert len(parse_price_slots(data, now=NOW)) == 2


def test_strict_parser_preserves_explicit_final_slot():
    slots = parse_price_slots(source([entry(0, 1), entry(1, 2)]), strict=True, now=NOW)
    assert slots[-1].end == at(2)


def test_strict_parser_does_not_bridge_missing_quarter_hours():
    slots = parse_price_slots(
        source([entry(0), entry(0.25), entry(1.25), entry(1.5)]), strict=True, now=NOW
    )
    assert [(item.start, item.end) for item in slots] == [
        (NOW, at(0.25)),
        (at(1.25), at(1.5)),
    ]


def test_strict_parser_truncates_overlap_at_next_price_boundary():
    slots = parse_price_slots(
        source([entry(0, 3, 0.1), entry(1, 2, 0.5)]), strict=True, now=NOW
    )
    assert [(item.start, item.end, item.price) for item in slots] == [
        (NOW, at(1), 0.1),
        (at(1), at(2), 0.5),
    ]


def test_strict_parser_invalid_price_still_bounds_predecessor():
    slots = parse_price_slots(
        source([entry(0, 3, 0.1), entry(1, 2, "unknown"), entry(2, 3, 0.2)]),
        strict=True,
        now=NOW,
    )
    assert [(item.start, item.end) for item in slots] == [(NOW, at(1)), (at(2), at(3))]


def test_explicit_malformed_end_cannot_be_reinterpreted_as_missing():
    bad = entry(0)
    bad["end"] = "invalid"
    assert parse_price_slots(source([bad, entry(1, 2)]), strict=True, now=NOW)[
        0
    ].start == at(1)


@pytest.mark.parametrize("unit", ["kWh", "W", "%", "USD/kWh"])
def test_strict_price_units_never_fall_back_to_one(unit):
    assert (
        parse_price_slots(source([entry(0, 1)], unit=unit), strict=True, now=NOW) == []
    )
    assert parse_price_slots(source([entry(0, 1)], unit=unit), now=NOW)


@pytest.mark.parametrize("state", ["unknown", "unavailable"])
def test_unavailable_source_does_not_grant_old_attribute_prices(state):
    assert (
        parse_price_slots(source([entry(0, 1)], state=state), strict=True, now=NOW)
        == []
    )


def test_strict_ct_conversion_and_negative_price():
    slots = parse_price_slots(
        source([entry(0, 1, -5)], unit="ct/kWh"), strict=True, now=NOW
    )
    assert slots[0].price == pytest.approx(-0.05)


def test_strict_numeric_array_keeps_final_explicit_interval():
    state = State(
        "sensor.price", ".1", {"today": [0.1] * 24, "unit_of_measurement": "EUR/kWh"}
    )
    slots = parse_price_slots(state, strict=True, now=NOW)
    assert len(slots) == 24
    assert sum((item.end - item.start).total_seconds() for item in slots) == 86400


def test_price_cap_and_real_windows_precede_budget_selection(hass):
    c = coordinator(hass)
    values = [price(0, 1, 0.1), price(1, 2, 0.2), price(2, 3, 0.201), price(3, 4, -0.1)]
    constraints = c.price_planner.adaptive_constraints(NOW, values)
    assert [(i.start, i.end) for i in constraints.cheap_windows] == [
        (NOW, at(2)),
        (at(3), at(4)),
    ]
    assert [i.price_eur_kwh for i in constraints.charge_windows] == [0.1, 0.2, -0.1]
    assert constraints.max_charge_seconds == 7200


def test_pv_wait_window_crosses_cycle_anchor(hass):
    c = coordinator(hass)
    c.price_planner.adaptive_constraints(at(-23.5), [price(-23.5, 0)])
    constraints = c.price_planner.adaptive_constraints(NOW, [price(0, 4)])
    assert constraints.cheap_windows[0].end == at(4)
    assert constraints.charge_windows[0].end == at(0.5)


def test_identical_timers_and_fallback_replacements_do_not_refill(hass):
    c = coordinator(hass)
    p = c.price_planner
    values = [price(0, 8)]
    p.adaptive_constraints(NOW, values)
    p.adaptive_allocate(NOW, (allocation(0, 2),))
    for elapsed in [0, 0.25, 0.5, 0.75, 1]:
        constraints = p.adaptive_constraints(at(elapsed), values)
        p.adaptive_allocate(at(elapsed), (allocation(elapsed, 2),))
        assert constraints.max_charge_seconds == pytest.approx((2 - elapsed) * 3600)
    assert p._cycle_state.anchor == NOW
    assert (
        sum((i.end - i.start).total_seconds() for i in p._cycle_state.intervals) == 7200
    )


def test_replanning_can_replace_future_but_cannot_spend_new_past(hass):
    c = coordinator(hass)
    p = c.price_planner
    p.adaptive_constraints(NOW, [price(0, 8)])
    p.adaptive_allocate(NOW, (allocation(1, 2),))
    p.adaptive_allocate(at(1.5), (allocation(0, 1), allocation(3, 8)))
    assert [(i.start, i.end) for i in p._cycle_state.intervals] == [
        (at(1), at(1.5)),
        (at(3), at(4.5)),
    ]


def test_configured_hours_change_preserves_consumed_seconds(hass):
    c = coordinator(hass)
    p = c.price_planner
    values = [price(0, 8)]
    p.adaptive_constraints(NOW, values)
    p.adaptive_allocate(NOW, (allocation(0, 2),))
    c._price_charge_hours = 1
    assert p.adaptive_constraints(at(1.5), values).max_charge_seconds == 0
    p.adaptive_allocate(at(1.5), ())
    c._price_charge_hours = 3
    assert p.adaptive_constraints(at(1.5), values).max_charge_seconds == 5400


def test_allocator_revalidates_price_cap_and_clips_overbudget(hass):
    c = coordinator(hass)
    p = c.price_planner
    p.adaptive_constraints(NOW, [price(0, 1, 0.1), price(1, 2, 0.2), price(2, 8, 0.1)])
    c._price_charge_max_price = 0.15
    p.adaptive_allocate(NOW, (allocation(0, 8),))
    assert [(i.start, i.end) for i in p._cycle_state.intervals] == [
        (NOW, at(1)),
        (at(2), at(3)),
    ]


def test_missing_prices_cancel_future_without_forgetting_elapsed(hass):
    c = coordinator(hass)
    p = c.price_planner
    p.adaptive_constraints(NOW, [price(0, 8)])
    p.adaptive_allocate(NOW, (allocation(0, 2),))
    assert p.adaptive_constraints(at(0.5), []).quality_reason == "no_price_data"
    p.adaptive_allocate(at(0.5), ())
    assert [(i.start, i.end) for i in p._cycle_state.intervals] == [(NOW, at(0.5))]
    assert p.adaptive_constraints(at(1), [price(1, 8)]).max_charge_seconds == 5400


def test_clock_reversal_does_not_create_fresh_cycle(hass):
    c = coordinator(hass)
    p = c.price_planner
    p.adaptive_constraints(NOW, [price(0, 8)])
    p.adaptive_allocate(NOW, (allocation(0, 2),))
    original = p._cycle_state
    assert (
        p.adaptive_constraints(at(-1), [price(-1, 8)]).quality_reason
        == "price_cycle_clock_reversed"
    )
    p.adaptive_allocate(at(-1), (allocation(-1, 1),))
    assert p._cycle_state == original


def test_cycle_rollover_uses_original_boundary_after_downtime(hass):
    c = coordinator(hass)
    p = c.price_planner
    p.adaptive_constraints(NOW, [price(0, 8)])
    p.adaptive_constraints(at(49), [price(49, 56)])
    assert p._cycle_state.anchor == at(48)
    assert p._cycle_state.end == at(72)


def test_disabled_adaptive_does_not_create_or_allocate_cycle(hass):
    c = coordinator(hass)
    c._price_charge_enabled = False
    p = c.price_planner
    assert (
        p.adaptive_constraints(NOW, [price(0, 8)]).quality_reason == "adaptive_disabled"
    )
    p.adaptive_allocate(NOW, (allocation(0, 2),))
    assert p._cycle_state is None


@pytest.mark.parametrize(
    "neutral,expected", [(0.3, True), (0.2, False), (0.1, False), (None, False)]
)
def test_new_neutral_policy_includes_unselected_cheap_slots(hass, neutral, expected):
    c = coordinator(hass)
    c._price_charge_neutral_price = neutral
    constraints = c.price_planner.adaptive_constraints(NOW, [price(0, 1, 0.1)])
    assert bool(constraints.discharge_blocked_windows) is expected


async def test_restart_preserves_exact_adaptive_cycle_and_elapsed_budget(hass):
    c = coordinator(hass)
    p = c.price_planner
    await p.async_load_cycle_state()
    p.adaptive_constraints(NOW, [price(0, 8)])
    p.adaptive_allocate(NOW, (allocation(0, 2),))
    await p.async_flush_cycle_state()
    restarted = coordinator(hass)
    await restarted.price_planner.async_load_cycle_state()
    constraints = restarted.price_planner.adaptive_constraints(at(1.25), [price(0, 8)])
    assert constraints.max_charge_seconds == 2700
    assert restarted.price_planner._cycle_state.anchor == NOW
    assert restarted.price_planner._cycle_state.strategy == PRICE_STRATEGY_ADAPTIVE


async def test_broken_persisted_cycle_cannot_grant_fresh_adaptive_budget(hass):
    c = coordinator(hass)
    c.price_planner._cycle_store._store.async_load = AsyncMock(
        return_value={"active": True, "anchor": "broken"}
    )
    await c.price_planner.async_load_cycle_state()
    constraints = c.price_planner.adaptive_constraints(NOW, [price(0, 8)])
    assert constraints.quality_reason == "price_cycle_unavailable"
    assert constraints.max_charge_seconds == 0


async def test_store_reports_failure_separately_from_a_new_install(hass):
    store = PricePlanCycleStore(hass, "test-empty")
    assert await store.async_load() is None
    assert not store.load_failed
    store._store.async_load = AsyncMock(return_value=[])
    assert await store.async_load() is None
    assert store.load_failed


def test_explicit_dst_folds_remain_distinct_in_strict_parser():
    zone = ZoneInfo("Europe/Berlin")
    first = datetime(2026, 10, 25, 2, tzinfo=zone, fold=0)
    second = datetime(2026, 10, 25, 2, tzinfo=zone, fold=1)
    state = source(
        [
            {"start": first.isoformat(), "end": second.isoformat(), "value": 0.1},
            {
                "start": second.isoformat(),
                "end": datetime(2026, 10, 25, 3, tzinfo=zone).isoformat(),
                "value": 0.2,
            },
        ]
    )
    slots = parse_price_slots(state, strict=True, now=first)
    assert len(slots) == 2
    assert all(
        (s.end.astimezone(UTC) - s.start.astimezone(UTC)).total_seconds() == 3600
        for s in slots
    )
