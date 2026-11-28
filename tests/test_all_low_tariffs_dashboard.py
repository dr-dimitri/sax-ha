"""REQ-ALL-LOW-TARIFFS-CHARGE: WebSocket contract for the charging method."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.sax_power.const import (
    CONF_ALL_LOW_TARIFFS_CHARGE_ENABLED,
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_FIXED_TIME_CHARGE_ENABLED,
    CONF_FIXED_TIME_CHARGE_START,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from tests.ha import WebSocketGenerator

from .test_dashboard_tariff_response import _get, _prepare
from .test_fixed_time_dashboard import _configure, _profile
from .test_month_switch_response import coordinator as coordinator


async def test_all_low_tariffs_accepts_mode_and_limits_before_device_lock(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    """The last confirmed options and valid targets are applied together."""
    entry = _prepare(hass, coordinator, "time_of_use")
    options = {
        **entry.options,
        CONF_FIXED_TIME_CHARGE_ENABLED: True,
        CONF_FIXED_TIME_CHARGE_START: "03:00:00",
    }
    hass.config_entries.async_update_entry(entry, options=options)
    coordinator.options = dict(options)
    coordinator._timed_charge_min_soc = 70
    client = await hass_ws_client(hass)
    original = await _get(client, entry)
    assert not original["all_low_tariffs_enabled"]

    with patch.object(coordinator, "_async_enforce_grid_charge_locked") as enforce:
        async with coordinator._charge_control_lock:
            response = await asyncio.wait_for(
                _configure(
                    client,
                    entry,
                    original,
                    charging_method="all_low_tariffs",
                    charging_settings={"max_soc": 60, "timed_charge_max_soc": 50},
                    automation_enabled=True,
                ),
                0.2,
            )
            assert response["success"], response
            saved = response["result"]
            assert saved["all_low_tariffs_enabled"] is True
            assert saved["fixed_time_charging"]["enabled"] is False
            assert saved["automation_enabled"] is True
            assert original["revision"] != saved["revision"]
            assert coordinator.options == entry.options
            assert coordinator.options[CONF_ALL_LOW_TARIFFS_CHARGE_ENABLED] is True
            assert coordinator.options[CONF_BRIDGE_CHARGE_ENABLED] is False
            assert coordinator.control_config().max_soc == 60
            assert coordinator.control_config().timed_charge_max_soc == 50
            assert await _get(client, entry) == saved

            invalid = await _configure(
                client, entry, saved, charging_settings={"timed_charge_max_soc": 101}
            )
            assert invalid["error"]["code"] == "invalid_tariff"
            assert coordinator.control_config().timed_charge_max_soc == 50

            replaced = await _configure(client, entry, saved, charging_method="fixed")
            assert replaced["success"], replaced
            assert replaced["result"]["all_low_tariffs_enabled"] is False
            assert CONF_ALL_LOW_TARIFFS_CHARGE_ENABLED not in entry.options
            assert coordinator.control_config().timed_charge_max_soc == 50
            task = coordinator._month_control_task
            assert task is not None
            coordinator.client.write_register.assert_not_awaited()
            enforce.assert_not_awaited()
        await task


@pytest.mark.parametrize(
    ("active", "submitted"),
    [("dynamic", "dynamic"), ("dynamic", "time_of_use"), ("fixed", "time_of_use")],
)
async def test_all_low_tariffs_requires_an_active_time_of_use_tariff(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    active: str,
    submitted: str,
) -> None:
    """Selecting a method must never activate another tariff implicitly."""
    entry = _prepare(hass, coordinator, active)
    client = await hass_ws_client(hass)
    original = await _get(client, entry)
    options = dict(entry.options)
    response = await _configure(
        client,
        entry,
        original,
        tariff_type=submitted,
        charging_method="all_low_tariffs",
    )
    assert response["error"]["code"] == "invalid_tariff"
    assert entry.options == coordinator.options == options
    coordinator.client.write_register.assert_not_awaited()


async def test_all_low_tariffs_is_restored_with_its_time_of_use_profile(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    """Leaving time-of-use disables the method until its profile is restored."""
    entry = _prepare(hass, coordinator, "time_of_use")
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    response = await _configure(
        client, entry, tariff, charging_method="all_low_tariffs"
    )
    assert response["success"], response
    tariff = response["result"]
    for target in ("dynamic", "time_of_use"):
        response = await _configure(
            client, entry, tariff, tariff_type=target, profile=_profile(tariff, target)
        )
        assert response["success"], response
        tariff = response["result"]
        assert tariff["all_low_tariffs_enabled"] is (target == "time_of_use")
        assert (CONF_ALL_LOW_TARIFFS_CHARGE_ENABLED in entry.options) is (
            target == "time_of_use"
        )


async def test_all_low_tariffs_rejects_an_incomplete_time_of_use_tariff(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    entry = _prepare(hass, coordinator, "time_of_use")
    options = dict(entry.options)
    options.pop(CONF_ECONOMICS_TOU_BASE_PRICE)
    hass.config_entries.async_update_entry(entry, options=options)
    coordinator.options = dict(options)
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    response = await _configure(
        client, entry, tariff, charging_method="all_low_tariffs"
    )
    assert response["error"]["code"] == "invalid_tariff"
    assert coordinator.options == entry.options == options
