"""REQ-HEMS-FORECAST-EVALUATION: explizite Optionen und begrenzte Archivaktionen."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol
from homeassistant.core import Context
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser

from custom_components.sax_power import _async_register_services, _control_options
from custom_components.sax_power.config_flow import STEP_OPTIONS_SCHEMA
from custom_components.sax_power.const import DATA_COORDINATOR, DOMAIN


def test_upgrade_defaults_do_not_activate_learning_or_extend_history() -> None:
    result = STEP_OPTIONS_SCHEMA({})
    assert result["hems_archive_enabled"] is False
    assert result["hems_history_days"] == "7"
    assert result["hems_forecast_mode"] == "observe"
    assert result["hems_live_adjustment"] is False
    assert _control_options({}) == _control_options(
        {key: value for key, value in result.items() if key.startswith("hems_")}
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("hems_history_days", "14"),
        ("hems_history_days", "0"),
        ("hems_forecast_mode", "force"),
        ("hems_archive_enabled", "invalid"),
    ],
)
def test_invalid_prediction_options_are_rejected(field: str, value: object) -> None:
    with pytest.raises(vol.Invalid):
        STEP_OPTIONS_SCHEMA({field: value})


async def test_options_save_explicit_observation_and_28_day_choice(hass) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "127.0.0.1"})
    entry.add_to_hass(hass)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {
            "hems_archive_enabled": True,
            "hems_history_days": "28",
            "hems_forecast_mode": "observe",
            "hems_live_adjustment": True,
        },
    )
    assert result["data"]["hems_archive_enabled"] is True
    assert result["data"]["hems_history_days"] == "28"
    assert result["data"]["hems_forecast_mode"] == "observe"
    assert result["data"]["hems_live_adjustment"] is True


@pytest.fixture
def archive_service(hass, device_registry):
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, "archive-battery")}
    )
    coordinator = MagicMock()
    coordinator.hems.prediction.archive.async_export = AsyncMock(
        return_value={"schema": 1, "items": [], "next_offset": None}
    )
    coordinator.hems.prediction.async_delete = AsyncMock()
    hass.data[DOMAIN] = {entry.entry_id: {DATA_COORDINATOR: coordinator}}
    _async_register_services(hass)
    return device.id, coordinator


async def test_archive_export_is_bounded_readonly_and_admin_only(hass, archive_service):
    device, coordinator = archive_service
    user = MockUser().add_to_hass(hass)
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            "export_hems_archive",
            {
                "device_id": device,
            },
            blocking=True,
            return_response=True,
            context=Context(user_id=user.id),
        )
    coordinator.hems.prediction.archive.async_export.assert_not_awaited()
    admin = MockUser(is_owner=True).add_to_hass(hass)
    result = await hass.services.async_call(
        DOMAIN,
        "export_hems_archive",
        {
            "device_id": device,
            "offset": 10,
            "limit": 20,
        },
        blocking=True,
        return_response=True,
        context=Context(user_id=admin.id),
    )
    assert result["schema"] == 1
    coordinator.hems.prediction.archive.async_export.assert_awaited_once_with(
        offset=10, limit=20
    )
    coordinator.hems.source_changed.assert_not_called()
    for limit in (0, 101):
        with pytest.raises(vol.Invalid):
            await hass.services.async_call(
                DOMAIN,
                "export_hems_archive",
                {
                    "device_id": device,
                    "limit": limit,
                },
                blocking=True,
                return_response=True,
                context=Context(user_id=admin.id),
            )


async def test_archive_delete_requires_confirmation_and_invalidates_after_success(
    hass, archive_service
):
    device, coordinator = archive_service
    user = MockUser(is_owner=True).add_to_hass(hass)
    for data in ({}, {"confirm": False}):
        with pytest.raises(vol.Invalid):
            await hass.services.async_call(
                DOMAIN,
                "delete_hems_archive",
                {
                    "device_id": device,
                    **data,
                },
                blocking=True,
                context=Context(user_id=user.id),
            )
    coordinator.hems.prediction.async_delete.assert_not_awaited()
    await hass.services.async_call(
        DOMAIN,
        "delete_hems_archive",
        {
            "device_id": device,
            "confirm": True,
        },
        blocking=True,
        context=Context(user_id=user.id),
    )
    coordinator.hems.prediction.async_delete.assert_awaited_once()
    coordinator.hems.source_changed.assert_called_once()


async def test_failed_archive_deletion_does_not_report_success(hass, archive_service):
    device, coordinator = archive_service
    coordinator.hems.prediction.async_delete.side_effect = HomeAssistantError(
        "write failed"
    )
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "delete_hems_archive",
            {
                "device_id": device,
                "confirm": True,
            },
            blocking=True,
        )
    coordinator.hems.source_changed.assert_not_called()
