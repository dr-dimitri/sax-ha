"""REQ-VUE-ENTITY-BINDING: One Apply accepts the complete charging draft."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from datetime import time as dt_time
from typing import Any
from unittest.mock import patch

import pytest
import voluptuous as vol
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import (
    HomeAssistantError,
    ServiceValidationError,
    Unauthorized,
    UnknownUser,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pymodbus.exceptions import ModbusException
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser

from custom_components.sax_power import _async_register_services
from custom_components.sax_power.const import (
    CHARGING_SETTING_KEYS,
    DATA_COORDINATOR,
    DOMAIN,
    REG_SUN_IC_CONTROL_MODE,
    SUN_IC_CONTROL_MODE_SETPOINT,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator

from .test_month_switch_response import coordinator as coordinator


@pytest.fixture
def charging_service(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    coordinator: SaxPowerCoordinator,
) -> tuple[str, dict[str, er.RegistryEntry]]:
    """Exercise HA's real service registry with its actual coordinator."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, entry_id="month_response")
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "battery")},
    )
    hass.data[DOMAIN] = {entry.entry_id: {DATA_COORDINATOR: coordinator}}
    entities = {
        key: entity_registry.async_get_or_create(
            "number",
            DOMAIN,
            f"{entry.entry_id}_{key}",
            config_entry=entry,
            device_id=device.id,
            suggested_object_id=f"renamed_battery_{key}",
        )
        for key in CHARGING_SETTING_KEYS
    }
    _async_register_services(hass)
    return device.id, entities


@pytest.mark.parametrize(
    "values",
    [
        {"timed_charge_min_soc": 80, "timed_charge_max_soc": 85, "max_soc": 90},
        {"timed_charge_min_soc": 10, "timed_charge_max_soc": 15, "max_soc": 20},
        {"timed_charge_min_soc": 0, "timed_charge_max_soc": 0, "max_soc": 0},
    ],
)
async def test_batch_soc_validates_final_pair_and_not_intermediate_values(
    coordinator: SaxPowerCoordinator, values: dict[str, int]
) -> None:
    """REQ-TIMED-SOC-CHARGE: Both limits may cross their previously saved partner."""
    coordinator._timed_charge_min_soc = 20
    coordinator._timed_charge_max_soc = 60
    async with coordinator._charge_control_lock:
        with (
            patch.object(coordinator, "async_update_listeners") as notify,
            patch.object(
                coordinator,
                "_async_schedule_control_save",
                wraps=coordinator._async_schedule_control_save,
            ) as save,
            patch.object(
                coordinator.price_planner,
                "evaluate",
                wraps=coordinator.price_planner.evaluate,
            ) as evaluate,
        ):
            await asyncio.wait_for(coordinator.async_set_charging_settings(values), 0.2)
            assert coordinator.timed_charge_min_soc == values["timed_charge_min_soc"]
            assert coordinator.timed_charge_max_soc == values["timed_charge_max_soc"]
            assert coordinator.max_soc == values["max_soc"]
            for key, value in values.items():
                assert coordinator._control_store._pending[key] == value
            notify.assert_called_once()
            save.assert_called_once()
            evaluate.assert_called_once()
            coordinator.client.write_register.assert_not_awaited()
    await coordinator._month_control_task


@pytest.mark.parametrize("maximum", [0, 10, 100])
async def test_global_only_batch_preserves_saved_start_and_target(
    coordinator: SaxPowerCoordinator, maximum: int
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: An independent cap never rewrites the pair."""
    coordinator._timed_charge_min_soc = 20
    async with coordinator._charge_control_lock:
        await coordinator.async_set_charging_settings({"max_soc": maximum})
        assert coordinator.control_config().timed_charge_min_soc == 20
        assert coordinator.control_config().timed_charge_max_soc == 90
        assert coordinator.timed_charge_max_soc == min(90, maximum)
    await coordinator._month_control_task


@pytest.mark.parametrize(
    "key,value",
    [
        ("max_soc", True),
        ("max_soc", "80"),
        ("max_soc", None),
        ("max_soc", float("nan")),
        ("max_soc", float("inf")),
        ("max_soc", -1),
        ("max_soc", 101),
        ("max_soc", 80.5),
        ("timed_charge_min_soc", 10.5),
        ("timed_charge_min_soc", -1),
        ("timed_charge_max_soc", 90.5),
        ("timed_charge_max_soc", 101),
        ("price_charge_hours", 0),
        ("price_charge_hours", 25),
        ("price_charge_hours", 2.5),
        ("price_charge_max_price", -100.1),
        ("price_charge_max_price", 200.1),
        ("price_charge_max_price", 12.35),
        ("price_charge_neutral_price", 12.35),
        ("price_charge_neutral_price", False),
        ("unexpected", 1),
    ],
)
async def test_invalid_batch_value_changes_nothing(
    coordinator: SaxPowerCoordinator, key: str, value: Any
) -> None:
    """All draft fields pass strict type, range and step checks before any mutation."""
    before = coordinator.control_config()
    async with coordinator._charge_control_lock:
        with pytest.raises(ServiceValidationError) as error:
            await asyncio.wait_for(
                coordinator.async_set_charging_settings(
                    {"price_charge_hours": 4, key: value}
                ),
                0.2,
            )
        assert error.value.translation_key == "invalid_charging_setting"
        assert error.value.translation_placeholders["field"] == key
        assert coordinator.control_config() == before
        assert coordinator._control_store._pending is None
        assert coordinator._month_control_task is None
        coordinator.client.write_register.assert_not_awaited()


@pytest.mark.parametrize(
    "values,code",
    [
        ({}, "charging_settings_required"),
        (
            {"timed_charge_min_soc": 80, "timed_charge_max_soc": 70, "max_soc": 90},
            "timed_charge_soc_order",
        ),
        (
            {"timed_charge_min_soc": 50, "max_soc": 40},
            "timed_charge_soc_order",
        ),
        (
            {"timed_charge_max_soc": 80, "max_soc": 70},
            "invalid_charging_setting",
        ),
    ],
)
async def test_invalid_batch_pair_changes_nothing(
    coordinator: SaxPowerCoordinator, values: dict[str, int], code: str
) -> None:
    """REQ-TIMED-SOC-CHARGE: The final global cap participates in pair validation."""
    before = coordinator.control_config()
    async with coordinator._charge_control_lock:
        with pytest.raises(ServiceValidationError) as error:
            await asyncio.wait_for(coordinator.async_set_charging_settings(values), 0.2)
        assert error.value.translation_key == code
        assert coordinator.control_config() == before
        assert coordinator._control_store._pending is None
        assert coordinator._month_control_task is None


@pytest.mark.parametrize("price", [-100, 0, 12.3, 200])
async def test_price_batch_uses_number_entity_cent_units(
    coordinator: SaxPowerCoordinator, price: float
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: The dashboard and batch service both use ct/kWh."""
    async with coordinator._charge_control_lock:
        await coordinator.async_set_charging_settings(
            {
                "price_charge_max_price": price,
                "price_charge_neutral_price": price,
                "price_charge_hours": 4,
            }
        )
        assert coordinator.price_charge_max_price == price / 100
        assert coordinator.price_charge_neutral_price == price / 100
        assert coordinator.price_charge_hours == 4
    await coordinator._month_control_task


async def test_batch_service_checks_only_and_all_submitted_entity_rights(
    hass: HomeAssistant,
    charging_service: tuple[str, dict[str, er.RegistryEntry]],
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-VUE-ENTITY-BINDING: Partial rights cannot authorize a complete batch."""
    device_id, entities = charging_service
    user = MockUser().add_to_hass(hass)
    allowed = ["max_soc", "timed_charge_min_soc", "timed_charge_max_soc"]
    values = {"max_soc": 90, "timed_charge_min_soc": 30, "timed_charge_max_soc": 80}
    before = coordinator.control_config()
    for missing in allowed:
        user.mock_policy(
            {
                "entities": {
                    "entity_ids": {
                        entities[key].entity_id: {"read": True, "control": True}
                        for key in allowed
                        if key != missing
                    }
                }
            }
        )
        with pytest.raises(Unauthorized):
            await hass.services.async_call(
                DOMAIN,
                "set_charging_settings",
                {"device_id": device_id, **values},
                blocking=True,
                context=Context(user_id=user.id),
            )
        assert coordinator.control_config() == before
    user.mock_policy(
        {
            "entities": {
                "entity_ids": {
                    entities[key].entity_id: {"read": True, "control": True}
                    for key in allowed
                }
            }
        }
    )
    async with coordinator._charge_control_lock:
        await asyncio.wait_for(
            hass.services.async_call(
                DOMAIN,
                "set_charging_settings",
                {"device_id": device_id, **values},
                blocking=True,
                context=Context(user_id=user.id),
            ),
            0.2,
        )
        assert coordinator.max_soc == 90
        assert coordinator.timed_charge_min_soc == 30
        assert coordinator.timed_charge_max_soc == 80
        coordinator.client.write_register.assert_not_awaited()
    await coordinator._month_control_task


@pytest.mark.parametrize("problem", ["inactive", "unknown", "disabled", "device"])
async def test_batch_service_rejects_invalid_registry_association_or_user(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    charging_service: tuple[str, dict[str, er.RegistryEntry]],
    coordinator: SaxPowerCoordinator,
    problem: str,
) -> None:
    """Device association and an active user are required even with global rights."""
    device_id, entities = charging_service
    user = MockUser(is_active=problem != "inactive")
    user.mock_policy({"entities": True})
    if problem != "unknown":
        user.add_to_hass(hass)
    target = entities["max_soc"].entity_id
    if problem == "disabled":
        entity_registry.async_update_entity(
            target, disabled_by=er.RegistryEntryDisabler.USER
        )
    elif problem == "device":
        entity_registry.async_update_entity(target, device_id=None)
    before = coordinator.control_config()
    with pytest.raises(UnknownUser if problem == "unknown" else Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            "set_charging_settings",
            {"device_id": device_id, "max_soc": 80},
            blocking=True,
            context=Context(user_id=user.id),
        )
    assert coordinator.control_config() == before


async def test_unknown_batch_service_field_fails_schema_before_mutation(
    hass: HomeAssistant,
    charging_service: tuple[str, dict[str, er.RegistryEntry]],
    coordinator: SaxPowerCoordinator,
) -> None:
    """The service exposes only the supported numeric charging fields."""
    device_id, _ = charging_service
    before = coordinator.control_config()
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            "set_charging_settings",
            {"device_id": device_id, "max_soc": 80, "timed_charge_enabled": True},
            blocking=True,
        )
    assert coordinator.control_config() == before


async def test_later_batch_during_device_ack_is_applied_by_same_worker(
    hass: HomeAssistant,
    charging_service: tuple[str, dict[str, er.RegistryEntry]],
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-VUE-ENTITY-BINDING: Device acknowledgement cannot delay the next draft."""
    device_id, _ = charging_service
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(0)
    coordinator._timed_charge_end = dt_time(6)
    coordinator._timed_charge_min_soc = 80
    coordinator._timed_charge_armed = True
    started = asyncio.Event()
    finish = asyncio.Event()
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> Any:
        if address == REG_SUN_IC_CONTROL_MODE and value == SUN_IC_CONTROL_MODE_SETPOINT:
            started.set()
            await finish.wait()
        return success

    coordinator.client.write_register.side_effect = write
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, 2, tzinfo=UTC),
    ):
        await hass.services.async_call(
            DOMAIN,
            "set_charging_settings",
            {"device_id": device_id, "max_soc": 95},
            blocking=True,
        )
        worker = coordinator._month_control_task
        try:
            await asyncio.wait_for(started.wait(), 1)
            await asyncio.wait_for(
                hass.services.async_call(
                    DOMAIN,
                    "set_charging_settings",
                    {
                        "device_id": device_id,
                        "max_soc": 40,
                        "timed_charge_min_soc": 20,
                        "timed_charge_max_soc": 30,
                    },
                    blocking=True,
                ),
                0.2,
            )
            assert coordinator._month_control_task is worker
            assert coordinator.max_soc == 40
            assert coordinator.timed_charge_max_soc == 30
            assert coordinator._timed_charge_active is False
        finally:
            finish.set()
        await worker
    assert coordinator._timed_charge_active is False
    assert coordinator.control_config().timed_charge_max_soc == 30


async def test_failed_device_write_preserves_accepted_batch(
    coordinator: SaxPowerCoordinator,
) -> None:
    """Accepted settings survive a device failure; activity requires a device ACK."""
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(0)
    coordinator._timed_charge_end = dt_time(6)
    coordinator._timed_charge_armed = True
    coordinator.client.write_register.side_effect = ModbusException("offline")
    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, 2, tzinfo=UTC),
    ):
        await coordinator.async_set_charging_settings(
            {"max_soc": 95, "timed_charge_min_soc": 70, "timed_charge_max_soc": 85}
        )
        await coordinator._month_control_task
    assert coordinator.max_soc == 95
    assert coordinator.timed_charge_min_soc == 70
    assert coordinator.timed_charge_max_soc == 85
    assert coordinator._timed_charge_active is False
    assert coordinator._control_store._pending["timed_charge_max_soc"] == 85


async def test_shutdown_rejects_batch_before_mutation(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-VUE-ENTITY-BINDING: A late draft never revives an unloaded device."""
    before = coordinator.control_config()
    await coordinator.async_shutdown(reset_device=False)
    with pytest.raises(HomeAssistantError, match="entladen"):
        await coordinator.async_set_charging_settings({"max_soc": 80})
    assert coordinator.control_config() == before
