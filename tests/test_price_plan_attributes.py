"""REQ-DYNAMIC-PRICE-CHARGE: Attribute beschreiben die letzte Planberechnung."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.recorder.db_schema import StateAttributes
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    MockEntityPlatform,
    async_capture_events,
)

from custom_components.sax_power.const import (
    CONF_PRICE_SENSOR,
    DOMAIN,
    PRICE_STATUS_CHARGING,
    PRICE_STRATEGY_ABSOLUTE,
    PRICE_STRATEGY_RELATIVE,
    PRICE_STRATEGY_SMART,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.price_optimizer import PricePlan, SaxPricePlanner
from custom_components.sax_power.sensor import SENSOR_DESCRIPTIONS, SaxPowerSensor

NOW = datetime(2024, 1, 15, 12, tzinfo=UTC)


def _planner(hass: HomeAssistant, strategy: str) -> SaxPricePlanner:
    hass.states.async_set(
        "sensor.price",
        "0.05",
        {
            "unit_of_measurement": "EUR/kWh",
            "raw_today": [
                {
                    "start": NOW + timedelta(hours=hour),
                    "end": NOW + timedelta(hours=hour + 1),
                    "value": 0.05 + hour / 100,
                }
                for hour in range(6)
            ],
        },
    )
    coordinator = SaxPowerCoordinator(
        hass,
        MagicMock(),
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="price-attributes",
        options={CONF_PRICE_SENSOR: "sensor.price"},
    )
    coordinator._price_charge_enabled = True
    coordinator._price_charge_strategy = strategy
    coordinator._price_charge_hours = 3
    coordinator._max_soc = 80
    coordinator.data = {
        "soc": 50,
        "battery_capacity": 10000,
        "ic_max_power_reference": 1000,
    }
    return coordinator.price_planner


@pytest.mark.parametrize("strategy", [PRICE_STRATEGY_RELATIVE, PRICE_STRATEGY_SMART])
def test_price_plan_attributes_stay_stable_until_evaluation(
    hass: HomeAssistant, strategy: str
) -> None:
    """Ohne neue Planung erzeugt allein der Zeitablauf keinen Attributwechsel."""
    planner = _planner(hass, strategy)
    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
    ):
        assert planner.evaluate().charge_now
        attributes = planner.plan_attributes

    assert attributes["verbleibendes_zeitbudget_stunden"] == 3.0
    for seconds in (2, 30, 59, 7200):
        with patch(
            "custom_components.sax_power.price_optimizer.dt_util.now",
            return_value=NOW + timedelta(seconds=seconds),
        ):
            assert planner.plan_attributes == attributes


@pytest.mark.parametrize("strategy", [PRICE_STRATEGY_RELATIVE, PRICE_STRATEGY_SMART])
def test_price_plan_evaluation_updates_remaining_budget(
    hass: HomeAssistant, strategy: str
) -> None:
    """Eine neue Planung verbucht verstrichene Ladezeit im Attributsnapshot."""
    planner = _planner(hass, strategy)
    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
    ):
        planner.evaluate()

    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now",
        return_value=NOW + timedelta(minutes=1),
    ):
        planner.evaluate()
        assert planner.plan_attributes["verbleibendes_zeitbudget_stunden"] == 2.983

    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now",
        return_value=NOW + timedelta(hours=1),
    ):
        assert planner.plan_attributes["verbleibendes_zeitbudget_stunden"] == 2.983
        planner.evaluate()
        assert planner.plan_attributes["verbleibendes_zeitbudget_stunden"] == 2.0

    planner.coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now",
        return_value=NOW + timedelta(hours=2),
    ):
        planner.evaluate()
        assert planner.plan_attributes["verbleibendes_zeitbudget_stunden"] is None


def test_price_plan_attributes_reflect_manually_assigned_plan(
    hass: HomeAssistant,
) -> None:
    """Der Budgetcache darf die übrigen Attribute von self.plan nicht einfrieren."""
    planner = _planner(hass, PRICE_STRATEGY_RELATIVE)
    planner.plan = PricePlan(
        status=PRICE_STATUS_CHARGING,
        current_price=0.12345,
        threshold=0.15,
        needed_hours=1.25,
    )

    attributes = planner.plan_attributes

    assert attributes["aktueller_preis"] == 0.12345
    assert attributes["preisgrenze"] == 0.15
    assert attributes["benoetigte_stunden"] == 1.25
    assert attributes["verbleibendes_zeitbudget_stunden"] is None


async def test_price_status_keeps_windows_live_but_excludes_them_from_recorder(
    hass: HomeAssistant,
) -> None:
    """Die Entity registriert den Ausschluss am echten state_changed-Ereignis."""
    planner = _planner(hass, PRICE_STRATEGY_RELATIVE)
    coordinator = planner.coordinator
    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now", return_value=NOW
    ):
        planner.evaluate()
    coordinator.data["price_charge_status"] = planner.plan.status
    entry = MockConfigEntry(domain=DOMAIN, entry_id=coordinator.entry_id)
    entry.add_to_hass(hass)
    description = next(
        item for item in SENSOR_DESCRIPTIONS if item.key == "price_charge_status_text"
    )
    sensor = SaxPowerSensor(coordinator, entry.entry_id, description)
    platform = MockEntityPlatform(hass, domain="sensor", platform_name=DOMAIN)
    platform.config_entry = entry
    events = async_capture_events(hass, EVENT_STATE_CHANGED)

    try:
        await platform.async_add_entities([sensor])
        await hass.async_block_till_done()
        live = hass.states.get(sensor.entity_id)
        assert live is not None
        assert live.attributes["geplante_fenster"] == [
            slot.as_dict() for slot in planner.plan.slots
        ]
        assert live.attributes["geplante_fenster"]
        event = next(
            event for event in events if event.data["entity_id"] == sensor.entity_id
        )
        recorded = json.loads(
            StateAttributes.shared_attrs_bytes_from_event(event, None)
        )

        assert "geplante_fenster" not in recorded
        assert recorded["aktueller_preis"] == live.attributes["aktueller_preis"]
        assert recorded["verbleibendes_zeitbudget_stunden"] == 3.0
    finally:
        await platform.async_reset()
        await coordinator.async_shutdown(reset_device=False)
