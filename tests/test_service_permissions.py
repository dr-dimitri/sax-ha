"""SAX-Services dürfen HA-Kontrollrechte nicht über device_id umgehen."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.auth.permissions import PermissionLookup
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import Unauthorized, UnknownUser
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power import _async_register_services
from custom_components.sax_power.const import DATA_COORDINATOR, DOMAIN
from custom_components.sax_power.coordinator import SaxPowerCoordinator

from .test_month_switch_response import coordinator as coordinator


@dataclass(frozen=True)
class ServiceCase:
    """Fachlich benötigte Freigaben für einen öffentlichen Service-Aufruf."""

    service: str
    data: dict[str, Any]
    controls: tuple[tuple[str, str], ...]


CASES = (
    ServiceCase("start_grid_charge", {"power": -1500}, (("switch", "storage_switch"),)),
    ServiceCase("stop_grid_charge", {}, (("switch", "storage_switch"),)),
    ServiceCase("refresh_price_plan", {}, (("switch", "price_charge_enabled"),)),
    ServiceCase(
        "set_price_charge_enabled",
        {"enabled": True},
        (("switch", "price_charge_enabled"),),
    ),
    ServiceCase(
        "set_price_charge_enabled",
        {"enabled": True, "force": True},
        (("switch", "price_charge_enabled"), ("switch", "timed_charge_enabled")),
    ),
    ServiceCase(
        "set_price_charge_enabled",
        {"enabled": False, "force": True},
        (("switch", "price_charge_enabled"),),
    ),
    ServiceCase(
        "set_timed_charge_window",
        {"start": "22:00", "end": "06:00"},
        (("time", "timed_charge_start"), ("time", "timed_charge_end")),
    ),
    ServiceCase(
        "set_grid_serving_window",
        {"start": "10:00", "end": "14:00"},
        (("time", "grid_serving_start"), ("time", "grid_serving_end")),
    ),
    ServiceCase("restart_economics_accounting", {"confirm": True}, ()),
)


@pytest.fixture(params=CASES, ids=lambda case: f"{case.service}-{case.data}")
def service_case(request: pytest.FixtureRequest) -> ServiceCase:
    return request.param


@dataclass
class ServiceDevice:
    entry: MockConfigEntry
    device_id: str
    entities: dict[tuple[str, str], er.RegistryEntry]
    coordinator: MagicMock


def _device(hass: HomeAssistant) -> ServiceDevice:
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
    )
    coordinator = MagicMock()
    for case in CASES:
        setattr(coordinator, f"async_{case.service}", AsyncMock(return_value=True))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}
    registry = er.async_get(hass)
    controls = {control for case in CASES for control in case.controls}
    entities = {
        (domain, key): registry.async_get_or_create(
            domain,
            DOMAIN,
            f"{entry.entry_id}_{key}",
            config_entry=entry,
            device_id=device.id,
            suggested_object_id=f"renamed_{entry.entry_id}_{key}",
        )
        for domain, key in controls
    }
    _async_register_services(hass)
    return ServiceDevice(entry, device.id, entities, coordinator)


@pytest.fixture
def service_user(hass: HomeAssistant, hass_read_only_user: MockUser) -> MockUser:
    hass_read_only_user.perm_lookup = PermissionLookup(
        er.async_get(hass), dr.async_get(hass)
    )
    return hass_read_only_user


@pytest.fixture
def service_device(hass: HomeAssistant) -> ServiceDevice:
    return _device(hass)


async def _call(client: Any, case: ServiceCase, device_id: str) -> dict[str, Any]:
    await client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": DOMAIN,
            "service": case.service,
            "service_data": {"device_id": device_id, **case.data},
        }
    )
    return await client.receive_json()


async def test_read_only_websocket_cannot_mutate_or_replan(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    service_device: ServiceDevice,
    service_case: ServiceCase,
) -> None:
    """REQ-VUE-ENTITY-BINDING: Die echte Servicegrenze schützt auch Lesebenutzer."""
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    response = await _call(client, service_case, service_device.device_id)
    assert response["success"] is False
    assert response["error"]["message"] == "Unauthorized"
    assert not service_device.coordinator.mock_calls


@pytest.mark.parametrize("scope", ["entity", "device", "all"])
async def test_websocket_accepts_exact_entity_or_device_control(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    service_user: MockUser,
    service_device: ServiceDevice,
    service_case: ServiceCase,
    scope: str,
) -> None:
    """Kontrollrechte erlauben Geräteaktionen, aber keinen Bilanzreset."""
    if scope == "entity":
        policy: Any = {
            "entity_ids": {
                service_device.entities[control].entity_id: {"control": True}
                for control in service_case.controls
            }
        }
    elif scope == "device":
        policy = {"device_ids": {service_device.device_id: {"control": True}}}
    else:
        policy = True
    service_user.mock_policy({"entities": policy})
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    response = await _call(client, service_case, service_device.device_id)
    if service_case.controls:
        assert response["success"] is True
        getattr(
            service_device.coordinator, f"async_{service_case.service}"
        ).assert_awaited_once()
    else:
        assert response["success"] is False
        assert response["error"]["message"] == "Unauthorized"
        assert not service_device.coordinator.mock_calls


@pytest.mark.parametrize("actor", ["admin", "automation"])
async def test_admin_and_internal_calls_remain_supported(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    service_device: ServiceDevice,
    service_case: ServiceCase,
    actor: str,
) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: Bestätigte interne/admin Aktionen funktionieren."""
    if actor == "admin":
        client = await hass_ws_client(hass)
        assert (await _call(client, service_case, service_device.device_id))["success"]
    else:
        await hass.services.async_call(
            DOMAIN,
            service_case.service,
            {"device_id": service_device.device_id, **service_case.data},
            blocking=True,
        )
    getattr(
        service_device.coordinator, f"async_{service_case.service}"
    ).assert_awaited_once()


@pytest.mark.parametrize("actor", ["unknown", "inactive", "inactive_admin"])
async def test_missing_or_inactive_users_cannot_call_services(
    hass: HomeAssistant,
    service_device: ServiceDevice,
    service_case: ServiceCase,
    actor: str,
) -> None:
    """Ein alter Context bleibt nach Nutzerentzug auch mit globalen Rechten gesperrt."""
    user = MockUser(is_active=False, is_owner=actor == "inactive_admin")
    user.mock_policy({"entities": True})
    if actor != "unknown":
        user.add_to_hass(hass)
    with pytest.raises(UnknownUser if actor == "unknown" else Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            service_case.service,
            {"device_id": service_device.device_id, **service_case.data},
            blocking=True,
            context=Context(user_id=user.id),
        )
    assert not service_device.coordinator.mock_calls


@pytest.mark.parametrize("case", [case for case in CASES if len(case.controls) > 1])
async def test_websocket_requires_every_affected_control(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    service_user: MockUser,
    service_device: ServiceDevice,
    case: ServiceCase,
) -> None:
    """force braucht beide Schalter; Fenster brauchen beide Grenzen."""
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    for control in case.controls:
        service_user.mock_policy(
            {
                "entities": {
                    "entity_ids": {
                        service_device.entities[control].entity_id: {"control": True}
                    }
                }
            }
        )
        response = await _call(client, case, service_device.device_id)
        assert response["success"] is False
        assert response["error"]["message"] == "Unauthorized"
    assert not service_device.coordinator.mock_calls


@pytest.mark.parametrize("case", [case for case in CASES if case.controls])
async def test_control_of_another_device_does_not_authorize_target(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    service_user: MockUser,
    service_device: ServiceDevice,
    case: ServiceCase,
) -> None:
    """Gleiche SAX-Entities eines anderen Config Entry erlauben keinen Fremdwrite."""
    other = _device(hass)
    service_user.mock_policy(
        {"entities": {"device_ids": {other.device_id: {"control": True}}}}
    )
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    response = await _call(client, case, service_device.device_id)
    assert response["success"] is False
    assert response["error"]["message"] == "Unauthorized"
    assert not service_device.coordinator.mock_calls
    assert not other.coordinator.mock_calls


@pytest.mark.parametrize("problem", ["disabled", "missing", "device", "domain"])
async def test_registry_association_must_match_the_physical_control(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    service_user: MockUser,
    service_device: ServiceDevice,
    problem: str,
) -> None:
    """Auch globale Rechte ersetzen keine aktive, passende SAX-Entity am Zielgerät."""
    registry = er.async_get(hass)
    entity = service_device.entities[("switch", "storage_switch")]
    if problem == "disabled":
        registry.async_update_entity(
            entity.entity_id, disabled_by=er.RegistryEntryDisabler.USER
        )
    elif problem == "device":
        registry.async_update_entity(entity.entity_id, device_id=None)
    else:
        registry.async_remove(entity.entity_id)
        if problem == "domain":
            registry.async_get_or_create(
                "sensor",
                DOMAIN,
                entity.unique_id,
                config_entry=service_device.entry,
                device_id=service_device.device_id,
            )
    service_user.mock_policy({"entities": True})
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    response = await _call(client, CASES[0], service_device.device_id)
    assert response["success"] is False
    assert response["error"]["message"] == "Unauthorized"
    assert not service_device.coordinator.mock_calls


@pytest.mark.parametrize("case", [CASES[2], CASES[4], CASES[6], CASES[7]])
async def test_authorized_software_services_acknowledge_before_device_lock(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    service_user: MockUser,
    service_device: ServiceDevice,
    coordinator: SaxPowerCoordinator,
    case: ServiceCase,
) -> None:
    """REQ-VUE-ENTITY-BINDING: Rechteprüfung blockiert keine Softwarequittierung."""
    hass.data[DOMAIN][service_device.entry.entry_id][DATA_COORDINATOR] = coordinator
    service_user.mock_policy(
        {
            "entities": {
                "entity_ids": {
                    service_device.entities[control].entity_id: {"control": True}
                    for control in case.controls
                }
            }
        }
    )
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    applied = AsyncMock()
    with patch.object(coordinator, "_async_enforce_grid_charge_locked", applied):
        async with coordinator._charge_control_lock:
            response = await asyncio.wait_for(
                _call(client, case, service_device.device_id), 0.5
            )
            assert response["success"] is True
            assert coordinator._control_store._pending is not None
            task = coordinator._month_control_task
            assert task is not None and not task.done()
            applied.assert_not_awaited()
            coordinator.client.write_register.assert_not_awaited()
        await task
    applied.assert_awaited_once()
