"""Atomare Zeitfenster bewahren die Rechte beider Time-Entities im Vue-Panel."""

from __future__ import annotations

from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import Unauthorized, UnknownUser
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser

from custom_components.sax_power import _async_register_services
from custom_components.sax_power.const import DATA_COORDINATOR, DOMAIN


@pytest.fixture(params=["timed_charge", "grid_serving"])
def window_service(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    request: pytest.FixtureRequest,
) -> tuple[str, str, list[er.RegistryEntry], AsyncMock]:
    """Registriere ein reales Service-Schema mit einem isolierten Coordinator."""
    kind = request.param
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "battery")},
    )
    coordinator = MagicMock()
    action = AsyncMock()
    setattr(coordinator, f"async_set_{kind}_window", action)
    hass.data[DOMAIN] = {entry.entry_id: {DATA_COORDINATOR: coordinator}}
    entities = [
        entity_registry.async_get_or_create(
            "time",
            DOMAIN,
            f"{entry.entry_id}_{kind}_{part}",
            config_entry=entry,
            device_id=device.id,
            suggested_object_id=f"renamed_battery_{part}",
        )
        for part in ("start", "end")
    ]
    _async_register_services(hass)
    return f"set_{kind}_window", device.id, entities, action


async def test_window_service_requires_both_target_entities(
    hass: HomeAssistant,
    window_service: tuple[str, str, list[er.RegistryEntry], AsyncMock],
) -> None:
    """REQ-VUE-ENTITY-BINDING: Rechte auf eine Grenze erlauben keinen Doppelwrite."""
    service, device_id, entities, action = window_service
    user = MockUser().add_to_hass(hass)
    data = {"device_id": device_id, "start": "22:00:17", "end": "06:30:25"}
    for allowed in ([], [entities[0]], [entities[1]]):
        user.mock_policy(
            {
                "entities": {
                    "entity_ids": {
                        entity.entity_id: {"read": True, "control": True}
                        for entity in allowed
                    }
                }
            }
        )
        with pytest.raises(Unauthorized):
            await hass.services.async_call(
                DOMAIN, service, data, blocking=True, context=Context(user_id=user.id)
            )
    action.assert_not_awaited()

    user.mock_policy(
        {
            "entities": {
                "entity_ids": {
                    entity.entity_id: {"read": True, "control": True}
                    for entity in entities
                }
            }
        }
    )
    await hass.services.async_call(
        DOMAIN, service, data, blocking=True, context=Context(user_id=user.id)
    )
    action.assert_awaited_once_with(
        time(22, 0, 17), time(6, 30, 25), defer_device_update=True
    )


@pytest.mark.parametrize("problem", ["inactive", "unknown", "disabled", "device"])
async def test_window_service_rejects_invalid_user_or_registry_association(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    window_service: tuple[str, str, list[er.RegistryEntry], AsyncMock],
    problem: str,
) -> None:
    """Globale Kontrollrechte ersetzen weder aktiven Nutzer noch Gerätezuordnung."""
    service, device_id, entities, action = window_service
    user = MockUser(is_active=problem != "inactive")
    user.mock_policy({"entities": True})
    if problem != "unknown":
        user.add_to_hass(hass)
    if problem == "disabled":
        entity_registry.async_update_entity(
            entities[1].entity_id, disabled_by=er.RegistryEntryDisabler.USER
        )
    if problem == "device":
        entity_registry.async_update_entity(entities[1].entity_id, device_id=None)
    with pytest.raises(UnknownUser if problem == "unknown" else Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            service,
            {"device_id": device_id, "start": "22:00", "end": "06:30"},
            blocking=True,
            context=Context(user_id=user.id),
        )
    action.assert_not_awaited()


@pytest.mark.parametrize("actor", ["automation", "admin"])
async def test_window_service_preserves_internal_and_admin_calls(
    hass: HomeAssistant,
    window_service: tuple[str, str, list[er.RegistryEntry], AsyncMock],
    actor: str,
) -> None:
    """Automationen und Administratoren dürfen weiterhin leere Fenster setzen."""
    service, device_id, _entities, action = window_service
    user = MockUser(is_owner=True).add_to_hass(hass) if actor == "admin" else None
    await hass.services.async_call(
        DOMAIN,
        service,
        {"device_id": device_id, "start": "06:30", "end": "06:30"},
        blocking=True,
        context=Context(user_id=user.id if user else None),
    )
    action.assert_awaited_once_with(time(6, 30), time(6, 30), defer_device_update=True)
