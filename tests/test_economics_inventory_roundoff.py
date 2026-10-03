"""REQ-ECONOMICS-ACCOUNTING: Tariff splits must not block balance persistence."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    ECONOMICS_TOU_WINDOW_KEYS,
)
from custom_components.sax_power.domain.economics_accounting import (
    EconomicsPriceSegment,
    compute_economics_interval,
)
from custom_components.sax_power.domain.energy_accounting import (
    ZERO_DELTA,
    compute_charge_delta,
)
from custom_components.sax_power.infrastructure.economics_store import (
    EconomicsStateStore,
)

from .test_coordinator import _make_client, _make_coordinator


@pytest.fixture
def hass_storage() -> dict:
    """Exercise actual JSON round-trips rather than the in-memory Store fixture."""
    return {}


@pytest.mark.parametrize(
    ("charge_power", "discharge_power", "first_seconds"),
    [(100, 300, 0.1), (300, 400, 0.3)],
)
def test_segmented_discharge_exhausts_inventory_without_negative_roundoff(
    charge_power: float, discharge_power: float, first_seconds: float
) -> None:
    """REQ-ECONOMICS-ACCOUNTING: Exhaustion stays exactly zero (Issue #266)."""
    charge = compute_charge_delta(-charge_power, None, 2 / 3600)
    assert charge is not None
    inventory = charge.charged_kwh
    discharged = discharge_power * (2 / 3600) / 1000

    delta = compute_economics_interval(
        ZERO_DELTA,
        discharged,
        inventory,
        (
            EconomicsPriceSegment(first_seconds, 0.30, 0.08),
            EconomicsPriceSegment(2 - first_seconds, 0.20, 0.08),
        ),
    )

    assert inventory + delta.unvalued_inventory_delta_kwh == 0.0
    assert delta.priced_discharge_kwh_delta == pytest.approx(discharged - inventory)
    assert delta.avoided_grid_cost_delta == pytest.approx(
        (discharged - inventory) * 0.20
    )


async def test_tariff_boundary_keeps_future_balance_snapshots_persistable(
    hass: HomeAssistant, tmp_path: Path
) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: Real tariff splits survive later saves/reload."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    hass.config.config_dir = str(tmp_path)
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.options = {
        CONF_ECONOMICS_TARIFF_TYPE: "time_of_use",
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.30,
        ECONOMICS_TOU_WINDOW_KEYS[0]: {
            "start": "06:00",
            "end": "07:00",
            "price_eur_kwh": 0.20,
        },
    }
    await coordinator.async_load_economics_state()
    coordinator._bootstrap_energy_origin(None)
    epoch = datetime(2026, 10, 3, 5, 59, 57, 900000, tzinfo=ZoneInfo("Europe/Berlin"))

    def sample(
        seconds: float, power: float, smartmeter: float | None, soc: float = 50
    ) -> dict[str, Any]:
        moment = epoch + timedelta(seconds=seconds)
        coordinator._high_sample_time = 100 + seconds
        coordinator._high_sample_revision += 1
        data = {
            "storage_power_active": power,
            "smartmeter_power": smartmeter,
            "battery_soc": soc,
            "battery_soc_min": 5,
            "battery_capacity": 10000,
        }
        with (
            patch(
                "custom_components.sax_power.coordinator.monotonic",
                return_value=100 + seconds,
            ),
            patch(
                "custom_components.sax_power.coordinator.dt_util.now",
                return_value=moment,
            ),
            patch(
                "custom_components.sax_power.coordinator.dt_util.utcnow",
                return_value=moment.astimezone(UTC),
            ),
        ):
            coordinator._accumulate_energy(data)
        return data

    async def assert_round_trip() -> None:
        await coordinator._async_flush_economics_state()
        assert not coordinator._economics_storage_error
        loaded = await EconomicsStateStore(hass, coordinator.entry_id).async_load()
        assert loaded == coordinator._economics_state()

    try:
        sample(0, -100, None)
        sample(2, -100, None)
        assert coordinator._economics_unvalued_inventory_kwh == 5.555555555555555e-05
        await assert_round_trip()

        sample(4, 300, 0)
        assert coordinator._economics_unvalued_inventory_kwh == 0.0
        assert coordinator._economics_avoided_grid_cost_eur == pytest.approx(
            (300 - 100) * (2 / 3600) / 1000 * 0.20
        )
        assert not coordinator._economics_storage_error
        await assert_round_trip()

        for seconds, power, smartmeter, soc in (
            (6, 300, 0, 50),
            (8, 0, 0, 5),
            (10, 0, 0, 5),
            (12, -100, 0, 50),
            (14, -100, 100, 50),
        ):
            data = sample(seconds, power, smartmeter, soc)
            assert coordinator._economics_unvalued_inventory_kwh == 0.0
            assert data["economics_status"] == "active"
            await assert_round_trip()

        assert coordinator._economics_pv_opportunity_cost_eur > 0
        assert coordinator._economics_grid_charge_cost_eur > 0

        confirmed = coordinator._economics_state()
        for invalid in (-1.0, -6.776263578034403e-21, float("nan"), float("inf")):
            assert not await coordinator._economics_store.async_save(
                replace(confirmed, unvalued_inventory_kwh=invalid)
            )
        await assert_round_trip()
    finally:
        await coordinator.async_shutdown(reset_device=False)
