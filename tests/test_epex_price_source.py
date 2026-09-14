"""REQ-VUE-ELECTRICITY-TARIFF: EPEX-Preisquellen bleiben auswählbar und konsistent.

Das Anbieterformat stammt aus mampfes/ha_epex_spot, sensor.py und localization.py:
€/kWh, data mit start_time/end_time/price_per_kwh; ältere Versionen nutzten ct/kWh.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power.const import CONF_PRICE_SENSOR, PRICE_STRATEGY_ABSOLUTE
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.dashboard_tariff import (
    CONFIGURE_COMMAND,
    SERIES_COMMAND,
)

from .test_dashboard_tariff_configuration import (
    _get,
    dynamic_profile,
)
from .test_dashboard_tariff_configuration import (
    entry as entry,
)

EPEX_SENSOR = "sensor.epex_spot_data_market_price"
NOW = datetime(2026, 9, 13, 12, 30, tzinfo=UTC)


def _epex_attributes(unit: str, price: float) -> dict[str, Any]:
    return {
        "friendly_name": "EPEX Spot Data Market Price",
        "unit_of_measurement": unit,
        "price_per_kwh": price,
        "data": [
            {
                "start_time": NOW.isoformat(),
                "end_time": (NOW + timedelta(minutes=15)).isoformat(),
                "price_per_kwh": price,
            },
            {
                "start_time": (NOW + timedelta(minutes=15)).isoformat(),
                "end_time": (NOW + timedelta(minutes=30)).isoformat(),
                "price_per_kwh": price * 2,
            },
        ],
    }


async def _save_epex(
    client: Any, entry: MockConfigEntry, **changes: Any
) -> dict[str, Any]:
    current = await _get(client, entry)
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": current["revision"],
            "tariff_type": "dynamic",
            "profile": dynamic_profile(price_sensor=EPEX_SENSOR, **changes),
        }
    )
    return await client.receive_json()


@pytest.mark.parametrize("unit,factor", [("€/kWh", 1), ("ct/kWh", 0.01)])
@pytest.mark.parametrize("price", [-0.05, 0, 0.179])
async def test_epex_source_saves_and_supplies_identical_prices_everywhere(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    unit: str,
    factor: float,
    price: float,
) -> None:
    """Die echte EPEX-Struktur passiert API, Chart, Ladeplanung und Bilanzierung."""
    await hass.config.async_set_time_zone("UTC")
    hass.states.async_set(EPEX_SENSOR, str(price), _epex_attributes(unit, price))
    client = await hass_ws_client(hass)

    response = await _save_epex(client, entry)

    assert response["success"]
    assert entry.options[CONF_PRICE_SENSOR] == EPEX_SENSOR
    assert response["result"]["profiles"]["dynamic"]["price_unit"] == "auto"
    assert (await _get(client, entry))["profiles"]["dynamic"]["price_sensor"] == (
        EPEX_SENSOR
    )
    coordinator = SaxPowerCoordinator(
        hass, MagicMock(), 64, 100, 10, entry.entry_id, options=dict(entry.options)
    )
    coordinator._price_charge_enabled = True
    coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    coordinator._price_charge_max_price = 0.3
    coordinator._max_soc = 90
    coordinator.data = {"soc": 40, "ic_max_power_reference": 4600}
    try:
        with patch(
            "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
        ):
            plan = coordinator.price_planner.evaluate()
        quote = coordinator.tariff_provider.quote(NOW)
        assert not coordinator.price_planner.has_unsupported_price_unit
        assert (
            plan.current_price == quote.price_eur_kwh == pytest.approx(price * factor)
        )
        assert plan.charge_now
        assert plan.slots[0].end == NOW + timedelta(minutes=15)

        with patch(
            "custom_components.sax_power.dashboard_price_series.dt_util.utcnow",
            return_value=NOW,
        ):
            await client.send_json_auto_id(
                {
                    "type": SERIES_COMMAND,
                    "entry_id": entry.entry_id,
                    "day": "today",
                }
            )
            series = await client.receive_json()
        assert series["success"]
        assert series["result"]["current_price_ct_kwh"] == pytest.approx(
            price * factor * 100
        )
        assert len(series["result"]["slots"]) == 2
    finally:
        await coordinator.async_shutdown(reset_device=False)


@pytest.mark.parametrize("unit", ["£/kWh", "USD/kWh", "SEK/kWh", "W"])
async def test_price_per_kwh_attribute_does_not_override_an_unsupported_currency(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    unit: str,
) -> None:
    """Auch ein passendes Attributformat ist kein Nachweis für Euro-Preise."""
    hass.states.async_set(EPEX_SENSOR, "0.179", _epex_attributes(unit, 0.179))
    client = await hass_ws_client(hass)
    before = dict(entry.options)

    response = await _save_epex(client, entry)

    assert response["error"]["code"] == "price_unit_unsupported"
    assert entry.options == before


@pytest.mark.parametrize("state", ["unknown", "unavailable"])
async def test_temporarily_unavailable_epex_sensor_can_still_be_selected(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    state: str,
) -> None:
    """Auswählen bleibt möglich; alte Vorschau darf keinen Ersatzpreis liefern."""
    hass.states.async_set(EPEX_SENSOR, state, _epex_attributes("€/kWh", 0.179))
    client = await hass_ws_client(hass)
    response = await _save_epex(client, entry)
    assert response["success"]
    coordinator = SaxPowerCoordinator(
        hass, MagicMock(), 64, 100, 10, entry.entry_id, options=dict(entry.options)
    )
    try:
        with patch(
            "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
        ):
            plan = coordinator.price_planner.evaluate()
        assert plan.current_price is None
        assert not plan.charge_now
        assert coordinator.tariff_provider.quote(NOW).price_eur_kwh is None
    finally:
        await coordinator.async_shutdown(reset_device=False)


async def test_missing_feed_in_price_identifies_the_field_and_keeps_the_epex_choice(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
) -> None:
    """Ein gültiger EPEX-Sensor ist nicht die Ursache einer fehlenden Vergütung."""
    hass.states.async_set(EPEX_SENSOR, "0.179", _epex_attributes("€/kWh", 0.179))
    client = await hass_ws_client(hass)
    before = dict(entry.options)

    response = await _save_epex(client, entry, feed_in_price_ct_kwh=None)

    assert response["error"]["code"] == "invalid_feed_in_price"
    assert entry.options == before
    assert (await _save_epex(client, entry, feed_in_price_ct_kwh=7.86))["success"]
    assert entry.options[CONF_PRICE_SENSOR] == EPEX_SENSOR
