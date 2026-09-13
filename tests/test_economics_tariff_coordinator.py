"""REQ-ECONOMICS-ACCOUNTING: Measured energy follows active tariff changes."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power import async_update_options
from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    DATA_COORDINATOR,
    DOMAIN,
    ECONOMICS_TOU_WINDOW_KEYS,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

_ZONE = ZoneInfo("Europe/Berlin")


@pytest.fixture
async def coordinator(hass: HomeAssistant) -> AsyncIterator[SaxPowerCoordinator]:
    await hass.config.async_set_time_zone("Europe/Berlin")
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_ECONOMICS_TARIFF_TYPE: "time_of_use",
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.30,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
            ECONOMICS_TOU_WINDOW_KEYS[0]: {
                "start": "22:00",
                "end": "06:00",
                "price_eur_kwh": 0.20,
            },
        },
    )
    entry.add_to_hass(hass)
    client = MagicMock(connected=True)
    coord = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=entry.entry_id,
        options=entry.options,
    )
    await coord.async_load_energy_state()
    coord.restore_energy_charged(0.0)
    coord.restore_energy_discharged(0.0)
    await coord.async_load_economics_state()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coord}
    unsubscribe = entry.add_update_listener(async_update_options)
    coord.async_apply_price_plan = AsyncMock()
    with patch(
        "custom_components.sax_power.async_sync_vue_dashboard", new_callable=AsyncMock
    ):
        yield coord
    unsubscribe()
    await coord.async_shutdown()


def _tick(
    coordinator: SaxPowerCoordinator, at: float, *, power: int, meter: int
) -> dict[str, Any]:
    data = {
        "storage_power_active": power,
        "smartmeter_power": meter,
        "battery_soc": 50,
        "battery_soc_min": 5,
        "battery_capacity": 10000,
    }
    with patch("custom_components.sax_power.coordinator.monotonic", return_value=at):
        coordinator._accumulate_energy(data)
    coordinator.data = data
    return data


async def test_coordinator_prices_both_halves_of_a_window_change(
    coordinator: SaxPowerCoordinator, freezer: Any
) -> None:
    start = datetime(2026, 9, 13, 21, 59, 55, tzinfo=_ZONE)
    freezer.move_to(start)
    coordinator.tariff_provider.async_setup()
    _tick(coordinator, 1000, power=0, meter=0)
    freezer.move_to(start + timedelta(seconds=10))

    charged = _tick(coordinator, 1010, power=-3600, meter=3600)

    assert charged["energy_charged"] == pytest.approx(0.01)
    assert charged["economics_current_import_price"] == pytest.approx(0.20)
    assert coordinator._economics_grid_charge_cost_eur == pytest.approx(
        0.005 * 0.30 + 0.005 * 0.20
    )
    assert coordinator._economics_unpriced_charge_kwh == 0
    freezer.move_to(start + timedelta(seconds=20))
    discharged = _tick(coordinator, 1020, power=3600, meter=0)
    assert discharged["energy_discharged"] == pytest.approx(0.01)
    assert coordinator._economics_avoided_grid_cost_eur == pytest.approx(0.01 * 0.20)
    assert discharged["economics_operating_result"] == pytest.approx(-0.0005)


async def test_live_options_listener_splits_new_tariff_without_repricing_old_costs(
    hass: HomeAssistant, coordinator: SaxPowerCoordinator, freezer: Any
) -> None:
    start = datetime(2026, 9, 13, 12, tzinfo=_ZONE)
    freezer.move_to(start)
    coordinator.tariff_provider.async_setup()
    _tick(coordinator, 1000, power=0, meter=0)
    freezer.move_to(start + timedelta(seconds=10))
    _tick(coordinator, 1010, power=-3600, meter=3600)
    old_cost = coordinator._economics_grid_charge_cost_eur
    assert old_cost == pytest.approx(0.003)

    freezer.move_to(start + timedelta(seconds=15))
    entry = hass.config_entries.async_get_entry(coordinator.entry_id)
    assert entry is not None
    hass.config_entries.async_update_entry(
        entry,
        options={
            CONF_ECONOMICS_TARIFF_TYPE: "fixed",
            CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.50,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.12,
        },
    )
    await hass.async_block_till_done()
    assert coordinator._economics_grid_charge_cost_eur == old_cost
    freezer.move_to(start + timedelta(seconds=20))

    charged = _tick(coordinator, 1020, power=-3600, meter=3600)

    assert charged["economics_current_import_price"] == pytest.approx(0.50)
    assert coordinator._economics_grid_charge_cost_eur == pytest.approx(
        old_cost + 0.005 * 0.30 + 0.005 * 0.50
    )
    freezer.move_to(start + timedelta(seconds=30))
    _tick(coordinator, 1030, power=3600, meter=0)
    assert coordinator._economics_avoided_grid_cost_eur == pytest.approx(0.005)
