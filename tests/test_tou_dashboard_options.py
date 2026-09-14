"""REQ-VUE-TARIFF-EDITOR: TOU configuration requires an accessible price editor."""

from __future__ import annotations

from copy import deepcopy

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.const import (
    CONF_DASHBOARD_TARIFF_PROFILES,
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_INVESTMENT_COST,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_PV_FORECAST_FACTOR,
    CONF_VUE_DASHBOARD_ENABLED,
    DOMAIN,
    ECONOMICS_TOU_WINDOW_KEYS,
)

PROFILE = {
    CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
    CONF_ECONOMICS_TOU_BASE_PRICE: 0.3421,
    ECONOMICS_TOU_WINDOW_KEYS[0]: {
        "start": "22:00:00",
        "end": "06:00:00",
        "price_eur_kwh": -0.1234,
    },
}


@pytest.mark.parametrize("profile_kind", ["new", "active", "inactive"])
@pytest.mark.parametrize("data_enabled", [None, False, True])
@pytest.mark.parametrize("options_enabled", [None, False, True])
async def test_time_of_use_needs_no_dashboard_opt_in(
    hass: HomeAssistant,
    profile_kind: str,
    data_enabled: bool | None,
    options_enabled: bool | None,
) -> None:
    """REQ-VUE-TARIFF-EDITOR: Alte Abwahlen erhalten Tarifauswahl und EUR-Profile."""
    data = {} if data_enabled is None else {CONF_VUE_DASHBOARD_ENABLED: data_enabled}
    options = (
        {} if options_enabled is None else {CONF_VUE_DASHBOARD_ENABLED: options_enabled}
    )
    if profile_kind == "active":
        options.update({CONF_ECONOMICS_TARIFF_TYPE: "time_of_use", **deepcopy(PROFILE)})
    elif profile_kind == "inactive":
        options.update(
            {
                CONF_ECONOMICS_TARIFF_TYPE: "disabled",
                CONF_DASHBOARD_TARIFF_PROFILES: {"time_of_use": deepcopy(PROFILE)},
            }
        )
    entry = MockConfigEntry(domain=DOMAIN, data=data, options=options)
    entry.add_to_hass(hass)
    submitted = {
        CONF_ECONOMICS_TARIFF_TYPE: "time_of_use",
        CONF_PV_FORECAST_FACTOR: 63,
        CONF_ECONOMICS_INVESTMENT_COST: 12345.67,
    }
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], submitted
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_TARIFF_TYPE] == "time_of_use"
    assert CONF_VUE_DASHBOARD_ENABLED not in entry.options
    assert entry.options[CONF_PV_FORECAST_FACTOR] == 63
    assert entry.options[CONF_ECONOMICS_INVESTMENT_COST] == 12345.67
    if profile_kind == "new":
        assert all(key not in entry.options for key in PROFILE)
    else:
        assert all(entry.options[key] == value for key, value in PROFILE.items())


async def test_repeated_first_page_can_select_time_of_use_directly(
    hass: HomeAssistant,
) -> None:
    """REQ-VUE-TARIFF-EDITOR: Wiederholte Seiten brauchen keine Dashboard-Abfrage."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ECONOMICS_TARIFF_TYPE: "fixed"}
    )
    assert result["step_id"] == "economics_fixed"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ECONOMICS_TARIFF_TYPE: "time_of_use"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ECONOMICS_TARIFF_TYPE] == "time_of_use"
    assert CONF_VUE_DASHBOARD_ENABLED not in entry.options
