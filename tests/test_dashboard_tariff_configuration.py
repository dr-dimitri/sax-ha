"""Common tariff tab API: profiles, source validation and exclusive control hook."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power.const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_DASHBOARD_TARIFF_PROFILES,
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_PRICE_SENSOR,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    DATA_COORDINATOR,
    DOMAIN,
    ECONOMICS_TOU_WINDOW_KEYS,
)
from custom_components.sax_power.dashboard_api import async_register_dashboard_api
from custom_components.sax_power.dashboard_tariff import CONFIGURE_COMMAND, GET_COMMAND


@pytest.fixture
def entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_ECONOMICS_TARIFF_TYPE: "time_of_use",
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
            ECONOMICS_TOU_WINDOW_KEYS[0]: {
                "start": "22:00",
                "end": "06:00",
                "price_eur_kwh": 0.2,
            },
            CONF_PV_FORECAST_SENSOR: "sensor.pv_tou",
            CONF_BRIDGE_CHARGE_ENABLED: True,
        },
    )
    entry.add_to_hass(hass)
    hass.states.async_set("sensor.price", "0.3", {"unit_of_measurement": "EUR/kWh"})
    hass.states.async_set("sensor.pv_smart", "10", {"unit_of_measurement": "kWh"})
    hass.states.async_set("sensor.pv_tou", "10", {"unit_of_measurement": "kWh"})
    async_register_dashboard_api(hass)
    return entry


def dynamic_profile(**changes: Any) -> dict[str, Any]:
    return {
        "feed_in_price_ct_kwh": 7.86,
        "price_sensor": "sensor.price",
        "price_attribute": None,
        "price_unit": "auto",
        "pv_sensor": "sensor.pv_smart",
        "pv_factor": 70,
        **changes,
    }


async def _get(client: Any, entry: MockConfigEntry) -> dict[str, Any]:
    await client.send_json_auto_id({"type": GET_COMMAND, "entry_id": entry.entry_id})
    response = await client.receive_json()
    assert response["success"]
    return response["result"]


async def test_switch_restores_inactive_tariff_and_its_distinct_pv_source(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, entry: MockConfigEntry
) -> None:
    """Profiles preserve original Euro values and independent source selections."""
    client = await hass_ws_client(hass)
    initial = await _get(client, entry)
    for tariff_type, profile in (
        ("dynamic", dynamic_profile()),
        ("time_of_use", None),
        ("dynamic", None),
    ):
        current = await _get(client, entry)
        await client.send_json_auto_id(
            {
                "type": CONFIGURE_COMMAND,
                "entry_id": entry.entry_id,
                "revision": current["revision"],
                "tariff_type": tariff_type,
                **({"profile": profile} if profile is not None else {}),
            }
        )
        result = await client.receive_json()
        assert result["success"] is True
        assert result["result"]["tariff_type"] == tariff_type
        assert (
            result["result"]["profiles"]["time_of_use"]
            == initial["profiles"]["time_of_use"]
        )
        assert result["result"]["profiles"]["dynamic"] == dynamic_profile()
        assert entry.options[CONF_ECONOMICS_FEED_IN_PRICE] == (
            0.08 if tariff_type == "time_of_use" else 0.0786
        )
        assert entry.options[CONF_PV_FORECAST_SENSOR] == (
            "sensor.pv_tou" if tariff_type == "time_of_use" else "sensor.pv_smart"
        )
        assert entry.options[CONF_BRIDGE_CHARGE_ENABLED] is (
            tariff_type == "time_of_use"
        )
    assert CONF_DASHBOARD_TARIFF_PROFILES in entry.options


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        ({"price_sensor": None}, "price_sensor_not_configured"),
        ({"price_sensor": "switch.bad"}, "price_sensor_missing"),
        ({"price_sensor": "sensor.missing"}, "price_sensor_missing"),
        ({"price_unit": "bogus"}, "price_unit_unsupported"),
        ({"price_unit": False}, "price_unit_unsupported"),
        ({"pv_factor": "NaN"}, "invalid_pv_factor"),
        ({"pv_factor": 70.5}, "invalid_pv_factor"),
        ({"pv_factor": True}, "invalid_pv_factor"),
        ({"pv_factor": 101}, "invalid_pv_factor"),
        ({"pv_sensor": "sensor.missing"}, "pv_sensor_missing"),
        ({"price_attribute": []}, "invalid_price_attribute"),
        ({"price_attribute": "x" * 129}, "invalid_price_attribute"),
        ({"feed_in_price_ct_kwh": -1}, "invalid_feed_in_price"),
    ],
)
async def test_invalid_configuration_leaves_all_profiles_unchanged(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    changes: dict[str, Any],
    error: str,
) -> None:
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    before = deepcopy(dict(entry.options))
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": current["revision"],
            "tariff_type": "dynamic",
            "profile": dynamic_profile(**changes),
        }
    )
    assert (await client.receive_json())["error"]["code"] == error
    assert entry.options == before


async def test_auto_unit_rejects_non_price_sensor_but_explicit_unit_can_correct_it(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, entry: MockConfigEntry
) -> None:
    hass.states.async_set("sensor.price", "30", {"unit_of_measurement": "W"})
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    for unit in ("auto", "ct_kwh"):
        await client.send_json_auto_id(
            {
                "type": CONFIGURE_COMMAND,
                "entry_id": entry.entry_id,
                "revision": current["revision"],
                "tariff_type": "dynamic",
                "profile": dynamic_profile(price_unit=unit),
            }
        )
        response = await client.receive_json()
        assert response["success"] is (unit == "ct_kwh")


@pytest.mark.parametrize("conflict", [False, True])
async def test_configure_uses_one_atomic_runtime_hook(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    conflict: bool,
) -> None:
    coordinator = MagicMock(timed_charge_enabled=True, price_charge_enabled=False)

    async def apply(
        options: dict[str, Any],
        *,
        enabled: bool | None,
        expected_options: dict[str, Any],
    ) -> None:
        assert expected_options == dict(entry.options)
        if conflict:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="dashboard_tariff_conflict"
            )
        hass.config_entries.async_update_entry(entry, options=options)
        coordinator.price_charge_enabled = enabled
        coordinator.timed_charge_enabled = False

    coordinator.async_apply_dashboard_tariff = AsyncMock(side_effect=apply)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    assert current["automation_enabled"] is True
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": current["revision"],
            "tariff_type": "dynamic",
            "profile": dynamic_profile(),
            "automation_enabled": True,
        }
    )
    response = await client.receive_json()
    coordinator.async_apply_dashboard_tariff.assert_awaited_once()
    if conflict:
        assert response["error"]["code"] == "conflict"
    else:
        assert response["result"]["automation_enabled"] is True
        assert response["result"]["tariff_type"] == "dynamic"


async def test_unloaded_entry_allows_configuration_but_not_an_automation_ack(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, entry: MockConfigEntry
) -> None:
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": current["revision"],
            "tariff_type": "dynamic",
            "profile": dynamic_profile(),
            "automation_enabled": False,
        }
    )
    assert (await client.receive_json())["error"]["code"] == "unavailable"
    assert entry.options[CONF_ECONOMICS_TARIFF_TYPE] == "time_of_use"


async def test_options_flow_keeps_profiles_and_restores_saved_time_of_use(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, entry: MockConfigEntry
) -> None:
    client = await hass_ws_client(hass)
    original = await _get(client, entry)
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": original["revision"],
            "tariff_type": "dynamic",
            "profile": dynamic_profile(),
        }
    )
    assert (await client.receive_json())["success"]
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {
            CONF_ECONOMICS_TARIFF_TYPE: "time_of_use",
            CONF_PV_FORECAST_FACTOR: 60,
        },
    )
    assert result["type"] == "create_entry"
    assert entry.options[CONF_ECONOMICS_TOU_BASE_PRICE] == 0.32
    assert entry.options[CONF_ECONOMICS_FEED_IN_PRICE] == 0.08
    restored = await _get(client, entry)
    assert restored["profiles"]["dynamic"] == dynamic_profile()


async def test_stale_profile_revision_rejects_the_configuration_before_the_hook(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, entry: MockConfigEntry
) -> None:
    client = await hass_ws_client(hass)
    current = await _get(client, entry)
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_PV_FORECAST_SENSOR: None}
    )
    coordinator = MagicMock()
    coordinator.async_apply_dashboard_tariff = AsyncMock()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": current["revision"],
            "tariff_type": "dynamic",
            "profile": dynamic_profile(),
        }
    )
    assert (await client.receive_json())["error"]["code"] == "conflict"
    coordinator.async_apply_dashboard_tariff.assert_not_called()


async def test_configuration_requires_admin_even_when_tariff_read_access_exists(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    entry: MockConfigEntry,
) -> None:
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for key in ("economics_current_import_price", "economics_feed_in_price"):
        registry.async_get_or_create(
            "sensor", DOMAIN, f"{entry.entry_id}_{key}", config_entry=entry
        )
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    current = await _get(client, entry)
    assert current["can_configure"] is False
    before = dict(entry.options)
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": current["revision"],
            "tariff_type": "dynamic",
            "profile": dynamic_profile(),
        }
    )
    assert (await client.receive_json())["error"]["code"] == "forbidden"
    assert entry.options == before


async def test_dynamic_options_flow_suggests_its_own_saved_feed_in_price(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, entry: MockConfigEntry
) -> None:
    hass.config_entries.async_update_entry(
        entry,
        options={
            **entry.options,
            CONF_DASHBOARD_TARIFF_PROFILES: {
                "dynamic": {
                    CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
                    CONF_PRICE_SENSOR: "sensor.price",
                }
            },
        },
    )
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {
            CONF_ECONOMICS_TARIFF_TYPE: "dynamic",
            CONF_PRICE_SENSOR: "sensor.price",
        },
    )
    suggested = {
        key.schema: key.description["suggested_value"]
        for key in flow["data_schema"].schema
        if isinstance(key.description, dict) and "suggested_value" in key.description
    }
    assert suggested[CONF_ECONOMICS_FEED_IN_PRICE] == 7.86
