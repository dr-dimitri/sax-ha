"""Dashboard-Aktivierung mit gemeinsamer Option (REQ-BRIDGE-CHARGE)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_PV_FORECAST_SENSOR,
    DATA_COORDINATOR,
    DOMAIN,
)
from custom_components.sax_power.switch import SaxPowerBridgeChargeSwitch

from .test_integration_live import (
    _build_basic_registers,
    _build_extended_registers,
    _modbus_server,
)


@pytest.mark.parametrize(
    ("options", "error"),
    [
        ({}, "bridge_pv_start_required"),
        ({CONF_ECONOMICS_TARIFF_TYPE: "time_of_use"}, "bridge_pv_start_required"),
        ({CONF_PV_FORECAST_SENSOR: "sensor.pv"}, "bridge_tariff_required"),
        (
            {CONF_PV_FORECAST_SENSOR: "sensor.pv", CONF_ECONOMICS_TARIFF_TYPE: "fixed"},
            "bridge_tariff_required",
        ),
    ],
)
async def test_missing_configuration_rejects_activation_but_allows_disabling(
    hass: HomeAssistant, options: dict[str, str], error: str
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, options=options)
    entry.add_to_hass(hass)
    entity = SaxPowerBridgeChargeSwitch(MagicMock(), entry)
    entity.hass = hass
    with patch.object(entity, "async_write_ha_state"):
        with pytest.raises(ServiceValidationError) as raised:
            await entity.async_turn_on()
        assert raised.value.translation_key == error
        assert entity.extra_state_attributes == {"configuration_error": error}
        assert dict(entry.options) == options
        assert not entity.is_on
        hass.config_entries.async_update_entry(
            entry, options={**options, CONF_BRIDGE_CHARGE_ENABLED: True}
        )
        await entity.async_turn_off()
        assert not entity.is_on
        assert dict(entry.options) == {**options, CONF_BRIDGE_CHARGE_ENABLED: False}


async def test_switch_and_options_share_live_state_without_reload(
    hass: HomeAssistant, socket_enabled: None, unused_tcp_port: int
) -> None:
    """Der HA-Service persistiert die Option am bestehenden Coordinator."""
    server = _modbus_server(
        unused_tcp_port, _build_basic_registers(), _build_extended_registers()
    )
    await server.serve_forever(background=True)
    options = {
        CONF_ECONOMICS_TARIFF_TYPE: "time_of_use",
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.30,
        CONF_PV_FORECAST_SENSOR: "sensor.pv_forecast",
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "127.0.0.1",
            "port": unused_tcp_port,
            "slave_id_basic": 64,
            "slave_id_extended": 100,
            "scan_interval": 3600,
        },
        options=options,
    )
    entry.add_to_hass(hass)
    try:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
        registry = er.async_get(hass)
        entity_id = registry.async_get_entity_id(
            "switch", DOMAIN, f"{entry.entry_id}_bridge_charge_enabled"
        )
        assert entity_id
        assert hass.states.get(entity_id).state == "off"
        registry.async_update_entity(entity_id, new_entity_id="switch.my_charge_plan")
        await hass.async_block_till_done()
        entity_id = "switch.my_charge_plan"
        assert not coordinator.timed_charge_enabled
        for service, enabled in (("turn_on", True), ("turn_off", False)):
            async with coordinator._charge_control_lock:
                await asyncio.wait_for(
                    hass.services.async_call(
                        "switch", service, {"entity_id": entity_id}, blocking=True
                    ),
                    0.2,
                )
                assert entry.options[CONF_BRIDGE_CHARGE_ENABLED] is enabled
                assert hass.states.get(entity_id).state == ("on" if enabled else "off")
            await hass.async_block_till_done()
            assert dict(entry.options) == {
                **options,
                CONF_BRIDGE_CHARGE_ENABLED: enabled,
            }
            assert coordinator.bridge_charge_enabled is enabled
            assert hass.states.get(entity_id).state == ("on" if enabled else "off")
            assert not coordinator.timed_charge_enabled
            assert hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR] is coordinator

        # Optionsänderungen müssen auch ohne nächsten Geräte-Poll sichtbar sein.
        hass.config_entries.async_update_entry(
            entry, options={**options, CONF_BRIDGE_CHARGE_ENABLED: True}
        )
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == "on"
        assert coordinator.bridge_charge_enabled
        coordinator.last_update_success = False
        coordinator.async_update_listeners()
        assert hass.states.get(entity_id).state == "on"
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": entity_id}, blocking=True
        )
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == "off"
        assert not coordinator.bridge_charge_enabled

        # Neustart übernimmt die Config-Entry-Option, keinen separaten Restore-Wert.
        hass.config_entries.async_update_entry(
            entry, options={**options, CONF_BRIDGE_CHARGE_ENABLED: True}
        )
        await hass.async_block_till_done()
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == "on"
        assert hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR].bridge_charge_enabled
    finally:
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            await hass.config_entries.async_unload(entry.entry_id)
        await server.shutdown()
