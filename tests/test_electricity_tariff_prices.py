"""REQ-VUE-ELECTRICITY-TARIFF: charging and accounting see the same price."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant, State

from custom_components.sax_power.const import PRICE_STRATEGY_ABSOLUTE
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.price_units import unit_factor

NOW = datetime(2026, 9, 13, 12, 30, tzinfo=UTC)


def test_unknown_configured_unit_is_not_an_automatic_price_unit() -> None:
    assert unit_factor("bogus", "ct/kWh") is None


@pytest.fixture
async def coordinator(hass: HomeAssistant) -> AsyncIterator[SaxPowerCoordinator]:
    await hass.config.async_set_time_zone("UTC")
    instance = SaxPowerCoordinator(
        hass,
        MagicMock(),
        64,
        100,
        10,
        "electricity-price-test",
        options={
            "economics_tariff_type": "dynamic",
            "economics_feed_in_price_eur_kwh": 0.08,
            "price_sensor": "sensor.price",
            "price_unit": "auto",
        },
    )
    instance._price_charge_enabled = True
    instance._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    instance._price_charge_max_price = 0.3
    instance._max_soc = 90
    instance.data = {
        "soc": 40,
        "battery_capacity": 10000,
        "ic_max_power_reference": 4600,
    }
    instance.async_write_extended_register = AsyncMock()
    yield instance
    await instance.async_shutdown()


def _slot(start: datetime, end: datetime, price: float) -> dict[str, str | float]:
    return {"start": start.isoformat(), "end": end.isoformat(), "price": price}


@pytest.mark.parametrize(
    ("state", "unit"), [("unavailable", "ct/kWh"), ("unknown", "ct/kWh"), ("20", "W")]
)
async def test_broken_source_never_uses_its_old_forecast(
    coordinator: SaxPowerCoordinator, hass: HomeAssistant, state: str, unit: str
) -> None:
    hass.states.async_set(
        "sensor.price",
        state,
        {
            "unit_of_measurement": unit,
            "raw_today": [_slot(NOW, NOW + timedelta(hours=1), 20)],
        },
    )
    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
    ):
        plan = coordinator.price_planner.evaluate()
    assert not plan.charge_now
    assert plan.current_price is None
    assert coordinator.tariff_provider.quote(NOW).quote is None


@pytest.mark.parametrize("price", [-5.0, 0.0, 20.0, 45.0])
async def test_live_plan_and_accounting_quote_use_identical_cent_conversion(
    coordinator: SaxPowerCoordinator, hass: HomeAssistant, price: float
) -> None:
    hass.states.async_set(
        "sensor.price",
        "999",
        {
            "unit_of_measurement": "ct/kWh",
            "raw_today": [_slot(NOW, NOW + timedelta(hours=1), price)],
        },
    )
    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
    ):
        plan = coordinator.price_planner.evaluate()
    assert plan.current_price == coordinator.tariff_provider.quote(NOW).price_eur_kwh
    assert plan.current_price == pytest.approx(price / 100)
    assert plan.charge_now is (price <= 30)


async def test_numeric_state_is_current_price_but_never_an_invented_day_curve(
    coordinator: SaxPowerCoordinator, hass: HomeAssistant
) -> None:
    hass.states.async_set("sensor.price", "23", {"unit_of_measurement": "ct/kWh"})
    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
    ):
        plan = coordinator.price_planner.evaluate()
    assert plan.current_price == pytest.approx(0.23)
    assert coordinator.tariff_provider.quote(NOW).price_eur_kwh == pytest.approx(0.23)
    assert plan.slots == ()
    assert not plan.charge_now


async def test_yesterdays_relative_prices_do_not_become_todays_prices(
    coordinator: SaxPowerCoordinator, hass: HomeAssistant
) -> None:
    state = State(
        "sensor.price",
        "20",
        {"unit_of_measurement": "ct/kWh", "today": [20] * 24},
        last_updated=NOW - timedelta(days=1),
    )
    with (
        patch.object(type(hass.states), "get", return_value=state),
        patch(
            "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
        ),
    ):
        plan = coordinator.price_planner.evaluate()
        assert coordinator.tariff_provider.quote(NOW).quote is None
    assert plan.current_price is None
    assert not plan.charge_now


async def test_conflicting_overlap_is_not_selected_but_known_edges_survive(
    coordinator: SaxPowerCoordinator, hass: HomeAssistant
) -> None:
    start = NOW.replace(hour=12, minute=0)
    overlap = start + timedelta(hours=1, minutes=30)
    hass.states.async_set(
        "sensor.price",
        "10",
        {
            "unit_of_measurement": "ct/kWh",
            "raw_today": [
                _slot(start, start + timedelta(hours=2), 10),
                _slot(start + timedelta(hours=1), start + timedelta(hours=3), 20),
            ],
        },
    )
    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now", return_value=overlap
    ):
        plan = coordinator.price_planner.evaluate()
    assert coordinator.tariff_provider.quote(overlap).quote is None
    assert plan.current_price is None
    assert not plan.charge_now
    assert [(slot.start, slot.end) for slot in plan.slots] == [
        (start + timedelta(hours=2), start + timedelta(hours=3))
    ]


async def test_out_of_range_overlap_never_makes_a_future_window_unambiguous(
    coordinator: SaxPowerCoordinator, hass: HomeAssistant
) -> None:
    start = NOW + timedelta(hours=1)
    hass.states.async_set(
        "sensor.price",
        "10",
        {
            "unit_of_measurement": "ct/kWh",
            "raw_today": [
                _slot(start, start + timedelta(hours=2), 10),
                _slot(start, start + timedelta(hours=1), 9999),
            ],
        },
    )
    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
    ):
        plan = coordinator.price_planner.evaluate()
    assert [(slot.start, slot.end) for slot in plan.slots] == [
        (start + timedelta(hours=1), start + timedelta(hours=2))
    ]
    assert coordinator.tariff_provider.quote(start).quote is None


async def test_overflowing_forecast_value_leaves_a_gap_instead_of_crashing(
    coordinator: SaxPowerCoordinator, hass: HomeAssistant
) -> None:
    hass.states.async_set(
        "sensor.price",
        "20",
        {
            "unit_of_measurement": "ct/kWh",
            "raw_today": [
                _slot(NOW, NOW + timedelta(hours=1), 10**400),
                _slot(NOW + timedelta(hours=1), NOW + timedelta(hours=2), 20),
            ],
        },
    )
    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
    ):
        plan = coordinator.price_planner.evaluate()
    assert not plan.charge_now
    assert plan.current_price is None
    assert coordinator.tariff_provider.quote(NOW).quote is None
    assert len(plan.slots) == 1
