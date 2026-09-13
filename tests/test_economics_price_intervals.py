"""REQ-ECONOMICS-ACCOUNTING: Prices apply only during their observed validity."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_PRICE_SENSOR,
    ECONOMICS_TOU_WINDOW_KEYS,
)
from custom_components.sax_power.domain.economics_accounting import (
    EconomicsPriceSegment,
    compute_economics_delta,
    compute_economics_interval,
)
from custom_components.sax_power.domain.energy_accounting import ZERO_DELTA, EnergyDelta
from custom_components.sax_power.domain.tariff import QuoteUnavailable
from custom_components.sax_power.economics import SaxTariffProvider

_ZONE = ZoneInfo("Europe/Berlin")
_ONE_GRID_KWH = EnergyDelta(1.0, 1.0, 0.0)
_ONE_PV_KWH = EnergyDelta(1.0, 0.0, 1.0)


def _provider(hass: HomeAssistant, tariff_type: str) -> SaxTariffProvider:
    return SaxTariffProvider(
        hass,
        MagicMock(
            options={
                CONF_ECONOMICS_TARIFF_TYPE: tariff_type,
                CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
                CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.30,
                CONF_ECONOMICS_TOU_BASE_PRICE: 0.30,
                CONF_PRICE_SENSOR: "sensor.price",
                ECONOMICS_TOU_WINDOW_KEYS[0]: {
                    "start": "22:00",
                    "end": "06:00",
                    "price_eur_kwh": 0.20,
                },
            }
        ),
    )


@pytest.mark.parametrize("hour", [21, 5])
async def test_window_boundary_splits_charge_cost_and_discharge_savings(
    hass: HomeAssistant, hour: int
) -> None:
    await hass.config.async_set_time_zone("Europe/Berlin")
    provider = _provider(hass, "time_of_use")
    start = datetime(2026, 9, 13, hour, 59, 55, tzinfo=_ZONE)
    end = start + timedelta(seconds=10)
    provider.accounting_segments(start, 0)

    segments = provider.accounting_segments(end, 10)

    assert [segment.seconds for segment in segments] == [5.0, 5.0]
    assert sorted(segment.import_price_eur_kwh for segment in segments) == [0.20, 0.30]
    charge = compute_economics_interval(_ONE_GRID_KWH, 0, 0, segments)
    discharge = compute_economics_interval(ZERO_DELTA, 1, 0, segments)
    assert charge.grid_charge_cost_delta == pytest.approx(0.25)
    assert discharge.avoided_grid_cost_delta == pytest.approx(0.25)
    assert charge.priced_charge_kwh_delta == pytest.approx(1.0)
    assert discharge.priced_discharge_kwh_delta == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("start", "window_start", "window_end", "prices"),
    [
        (datetime(2026, 3, 29, 0, 59, 55, tzinfo=UTC), "02:30", "04:00", [0.3, 0.2]),
        (datetime(2026, 10, 25, 0, 59, 55, tzinfo=UTC), "02:30", "03:00", [0.2, 0.3]),
    ],
)
async def test_clock_change_splits_real_seconds_at_the_local_tariff_boundary(
    hass: HomeAssistant,
    start: datetime,
    window_start: str,
    window_end: str,
    prices: list[float],
) -> None:
    await hass.config.async_set_time_zone("Europe/Berlin")
    provider = _provider(hass, "time_of_use")
    provider.coordinator.options[ECONOMICS_TOU_WINDOW_KEYS[0]] = {
        "start": window_start,
        "end": window_end,
        "price_eur_kwh": 0.2,
    }
    provider.accounting_segments(start, 0)

    segments = provider.accounting_segments(start + timedelta(seconds=10), 10)

    assert [segment.seconds for segment in segments] == [5.0, 5.0]
    assert [segment.import_price_eur_kwh for segment in segments] == prices


def test_segmented_discharge_consumes_unknown_inventory_in_time_order() -> None:
    delta = compute_economics_interval(
        ZERO_DELTA,
        1,
        0.5,
        [EconomicsPriceSegment(5, 0.1, 0.08), EconomicsPriceSegment(5, 0.4, 0.08)],
    )
    assert delta.avoided_grid_cost_delta == pytest.approx(0.2)
    assert delta.unvalued_inventory_delta_kwh == pytest.approx(-0.5)
    assert delta.priced_discharge_kwh_delta == pytest.approx(0.5)


@pytest.mark.parametrize("price", [float("nan"), float("inf"), -2.01, 5.01])
def test_invalid_import_price_never_enters_the_money_balance(price: float) -> None:
    charge = compute_economics_delta(_ONE_GRID_KWH, 0, 0, price, 0.08)
    discharge = compute_economics_delta(ZERO_DELTA, 1, 0, price, 0.08)
    assert charge.grid_charge_cost_delta == 0
    assert charge.unpriced_charge_delta_kwh == 1
    assert discharge.avoided_grid_cost_delta == 0
    assert discharge.unpriced_discharge_delta_kwh == 1


@pytest.mark.parametrize("price", [float("nan"), float("inf"), -0.01, 2.01])
def test_invalid_feed_price_never_enters_the_money_balance(price: float) -> None:
    charge = compute_economics_delta(_ONE_PV_KWH, 0, 0, 0.3, price)
    assert charge.pv_opportunity_cost_delta == 0
    assert charge.unpriced_charge_delta_kwh == 1


async def test_tariff_edit_does_not_reprice_the_preceding_interval_or_prior_costs(
    hass: HomeAssistant, freezer: Any
) -> None:
    provider = _provider(hass, "fixed")
    start = datetime(2026, 9, 13, 12, tzinfo=UTC)
    freezer.move_to(start)
    provider.async_setup()
    first = compute_economics_interval(
        _ONE_GRID_KWH,
        0,
        0,
        provider.accounting_segments(start + timedelta(seconds=10), 10),
    )
    freezer.move_to(start + timedelta(seconds=15))
    provider.coordinator.options = {
        **provider.coordinator.options,
        CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.50,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.12,
    }
    provider.async_setup()

    segments = provider.accounting_segments(start + timedelta(seconds=20), 10)
    grid = compute_economics_interval(_ONE_GRID_KWH, 0, 0, segments)
    pv = compute_economics_interval(_ONE_PV_KWH, 0, 0, segments)
    discharge = compute_economics_interval(ZERO_DELTA, 1, 0, segments)

    assert first.grid_charge_cost_delta == pytest.approx(0.30)
    assert grid.grid_charge_cost_delta == pytest.approx(0.40)
    assert pv.pv_opportunity_cost_delta == pytest.approx(0.10)
    assert discharge.avoided_grid_cost_delta == pytest.approx(0.40)
    assert provider.quote().price_eur_kwh == pytest.approx(0.50)
    provider.async_shutdown()


async def test_dynamic_slot_boundary_uses_the_same_quotes_as_the_live_price(
    hass: HomeAssistant, freezer: Any
) -> None:
    start = datetime(2026, 9, 13, 12, 59, 55, tzinfo=UTC)
    boundary = start + timedelta(seconds=5)
    freezer.move_to(start)
    hass.states.async_set(
        "sensor.price",
        "99",
        {
            "unit_of_measurement": "ct/kWh",
            "raw_today": [
                {"start": start.isoformat(), "end": boundary.isoformat(), "value": 10},
                {
                    "start": boundary.isoformat(),
                    "end": (boundary + timedelta(hours=1)).isoformat(),
                    "value": 40,
                },
            ],
        },
    )
    provider = _provider(hass, "dynamic")
    provider.accounting_segments(start, 0)

    segments = provider.accounting_segments(start + timedelta(seconds=10), 10)

    assert segments == (
        EconomicsPriceSegment(5.0, 0.10, 0.08),
        EconomicsPriceSegment(5.0, 0.40, 0.08),
    )
    assert provider.quote(boundary).price_eur_kwh == pytest.approx(0.40)
    assert compute_economics_interval(
        _ONE_GRID_KWH, 0, 0, segments
    ).grid_charge_cost_delta == pytest.approx(0.25)


async def test_late_forecast_recovery_never_backfills_an_observed_price_gap(
    hass: HomeAssistant, freezer: Any
) -> None:
    start = datetime(2026, 9, 13, 12, tzinfo=UTC)
    freezer.move_to(start)
    hass.states.async_set("sensor.price", "unavailable")
    provider = _provider(hass, "dynamic")
    provider.async_setup()
    freezer.move_to(start + timedelta(seconds=5))
    hass.states.async_set(
        "sensor.price",
        "0.25",
        {
            "raw_today": [
                {
                    "start": (start - timedelta(hours=1)).isoformat(),
                    "end": (start + timedelta(hours=1)).isoformat(),
                    "value": 0.25,
                }
            ]
        },
    )
    await hass.async_block_till_done()

    segments = provider.accounting_segments(start + timedelta(seconds=10), 10)
    charge = compute_economics_interval(_ONE_GRID_KWH, 0, 0, segments)

    assert charge.grid_charge_cost_delta == pytest.approx(0.125)
    assert charge.unpriced_charge_delta_kwh == pytest.approx(0.5)
    assert charge.unvalued_inventory_delta_kwh == pytest.approx(0.5)
    # The recovered price never makes previously unpriced charge free inventory.
    discharge = compute_economics_delta(
        ZERO_DELTA, 1, charge.unvalued_inventory_delta_kwh, 0.4, 0.08
    )
    assert discharge.avoided_grid_cost_delta == pytest.approx(0.20)
    provider.async_shutdown()


async def test_dynamic_state_changes_are_priced_at_the_observed_change_time(
    hass: HomeAssistant, freezer: Any
) -> None:
    start = datetime(2026, 9, 13, 12, tzinfo=UTC)
    freezer.move_to(start)
    hass.states.async_set("sensor.price", "-0.10")
    provider = _provider(hass, "dynamic")
    provider.async_setup()
    freezer.move_to(start + timedelta(seconds=6))
    hass.states.async_set("sensor.price", "0.30")
    await hass.async_block_till_done()

    segments = provider.accounting_segments(start + timedelta(seconds=10), 10)

    assert segments == (
        EconomicsPriceSegment(6.0, -0.10, 0.08),
        EconomicsPriceSegment(4.0, 0.30, 0.08),
    )
    assert compute_economics_interval(
        _ONE_GRID_KWH, 0, 0, segments
    ).grid_charge_cost_delta == pytest.approx(0.06)
    provider.async_shutdown()


async def test_dynamic_overlapping_slots_are_not_an_arbitrary_current_price(
    hass: HomeAssistant, freezer: Any
) -> None:
    start = datetime(2026, 9, 13, 12, tzinfo=UTC)
    freezer.move_to(start)
    hass.states.async_set(
        "sensor.price",
        "0.30",
        {
            "raw_today": [
                {
                    "start": start.isoformat(),
                    "end": (start + timedelta(hours=1)).isoformat(),
                    "value": 0.2,
                },
                {
                    "start": (start + timedelta(minutes=30)).isoformat(),
                    "end": (start + timedelta(hours=2)).isoformat(),
                    "value": 0.3,
                },
            ]
        },
    )
    provider = _provider(hass, "dynamic")
    result = provider.quote(start + timedelta(minutes=45))
    assert result.quote is None
    assert result.reason is QuoteUnavailable.PRICE_FORECAST_UNREADABLE


async def test_old_relative_today_prices_do_not_move_to_tomorrow(
    hass: HomeAssistant, freezer: Any
) -> None:
    await hass.config.async_set_time_zone("UTC")
    start = datetime(2026, 9, 13, 23, 59, 55, tzinfo=UTC)
    freezer.move_to(start)
    hass.states.async_set("sensor.price", "0.30", {"raw_today": [0.2] * 24})
    provider = _provider(hass, "dynamic")
    provider.accounting_segments(start, 0)

    segments = provider.accounting_segments(start + timedelta(seconds=10), 10)

    assert segments == (
        EconomicsPriceSegment(5.0, 0.2, 0.08),
        EconomicsPriceSegment(5.0, None, 0.08),
    )


@pytest.mark.parametrize("observed_seconds", [0, -1, float("nan"), float("inf"), 1e100])
async def test_unusable_interval_durations_cannot_create_a_price(
    hass: HomeAssistant, observed_seconds: float
) -> None:
    provider = _provider(hass, "fixed")
    assert (
        provider.accounting_segments(
            datetime(2026, 9, 13, 12, tzinfo=UTC), observed_seconds
        )
        == ()
    )
    delta = compute_economics_interval(_ONE_GRID_KWH, 0, 0, ())
    assert delta.unpriced_charge_delta_kwh == pytest.approx(1.0)
    assert delta.grid_charge_cost_delta == 0.0


async def test_backwards_clock_and_time_before_first_observation_stay_unpriced(
    hass: HomeAssistant,
) -> None:
    provider = _provider(hass, "fixed")
    start = datetime(2026, 9, 13, 12, tzinfo=UTC)
    assert provider.accounting_segments(start, 10) == (
        EconomicsPriceSegment(10.0, None, None),
    )
    assert provider.accounting_segments(start - timedelta(seconds=10), 10) == (
        EconomicsPriceSegment(10.0, None, None),
    )


async def test_many_price_updates_keep_bounded_history_without_backpricing(
    hass: HomeAssistant, freezer: Any
) -> None:
    provider = _provider(hass, "fixed")
    start = datetime(2026, 9, 13, 12, tzinfo=UTC)
    freezer.move_to(start)
    provider.async_setup()
    for index in range(1, 301):
        freezer.move_to(start + timedelta(seconds=index))
        provider.coordinator.options = {
            **provider.coordinator.options,
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.3 + index / 10000,
        }
        provider.async_setup()

    segments = provider.accounting_segments(start + timedelta(seconds=301), 301)

    assert sum(segment.seconds for segment in segments) == 301
    assert segments[0] == EconomicsPriceSegment(45.0, None, None)
    assert len(segments) == 257
    # The consumed history must not be applied again to the next interval.
    following = provider.accounting_segments(start + timedelta(seconds=311), 10)
    assert len(following) == 1
    assert following[0].seconds == 10.0
    assert following[0].import_price_eur_kwh == pytest.approx(0.33)
    provider.async_shutdown()
