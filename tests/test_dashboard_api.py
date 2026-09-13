"""WebSocket-Vertrag und Zugriffsrechte des Vue-Panels (REQ-VUE-ENTITY-BINDING)."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser
from pytest_homeassistant_custom_component.typing import (
    MockHAClientWebSocket,
    WebSocketGenerator,
)

from custom_components.sax_power.const import DOMAIN
from custom_components.sax_power.dashboard_api import (
    SUBSCRIBE_COMMAND,
    async_register_dashboard_api,
)

_MODULE = "custom_components.sax_power.dashboard_api"


@pytest.fixture
def dashboard_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    async_register_dashboard_api(hass)
    return entry


def _entity(
    registry: er.EntityRegistry,
    entry: MockConfigEntry,
    key: str = "soc",
    domain: str = "sensor",
    **kwargs: Any,
) -> er.RegistryEntry:
    return registry.async_get_or_create(
        domain,
        DOMAIN,
        f"{entry.entry_id}_{key}",
        config_entry=entry,
        suggested_object_id=f"sax_{key}",
        **kwargs,
    )


async def _subscribe(
    client: MockHAClientWebSocket, entry: MockConfigEntry, language: str = "de"
) -> list[dict[str, Any]]:
    await client.send_json_auto_id(
        {"type": SUBSCRIBE_COMMAND, "entry_id": entry.entry_id, "language": language}
    )
    result = await client.receive_json()
    assert result["success"] is True
    event = await client.receive_json()
    assert event["type"] == "event"
    assert event["id"] == result["id"]
    return event["event"]["entities"]


@pytest.mark.parametrize(
    "language, name", [("de", "Ladezustand"), ("en", "State of charge")]
)
async def test_metadata_uses_stable_ids_and_requested_language(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    dashboard_entry: MockConfigEntry,
    language: str,
    name: str,
) -> None:
    """Umbenannte entity_id bleibt per unique_id an den gewählten Entry gebunden."""
    entity = _entity(entity_registry, dashboard_entry)
    entity_registry.async_update_entity(
        entity.entity_id, new_entity_id="sensor.my_store"
    )
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)

    assert await _subscribe(client, dashboard_entry, language) == [
        {
            "entity_id": "sensor.my_store",
            "device_id": None,
            "domain": "sensor",
            "key": "soc",
            "name": name,
            "states": {},
            "can_control": False,
        }
    ]


async def test_metadata_reports_registry_device_for_renamed_time_entities(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    dashboard_entry: MockConfigEntry,
) -> None:
    """Atomare Fenster verwenden die Registry-Geräte-ID auch nach Entity-Umbenennung."""
    device = device_registry.async_get_or_create(
        config_entry_id=dashboard_entry.entry_id,
        identifiers={(DOMAIN, "battery")},
    )
    item = _entity(
        entity_registry,
        dashboard_entry,
        "timed_charge_start",
        "time",
        device_id=device.id,
    )
    entity_registry.async_update_entity(item.entity_id, new_entity_id="time.my_start")
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    entities = await _subscribe(client, dashboard_entry)
    assert entities[0]["entity_id"] == "time.my_start"
    assert entities[0]["device_id"] == device.id

    entity_registry.async_update_entity("time.my_start", device_id=None)
    assert (await client.receive_json())["event"]["entities"][0]["device_id"] is None


async def test_metadata_matches_registry_names_and_enum_translations(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    dashboard_entry: MockConfigEntry,
) -> None:
    """Sondernamen, Enum-Werte und dynamische Forecast-Namen bleiben korrekt."""
    _entity(entity_registry, dashboard_entry, "storage_switch", "switch")
    _entity(entity_registry, dashboard_entry, "grid_serving_forecast")
    _entity(entity_registry, dashboard_entry, "timed_charge_discharge_status")
    custom = _entity(entity_registry, dashboard_entry)
    entity_registry.async_update_entity(custom.entity_id, name="Meine Batterie")
    client = await hass_ws_client(hass)
    entities = {item["key"]: item for item in await _subscribe(client, dashboard_entry)}

    assert entities["soc"]["name"] == "Meine Batterie"
    assert entities["storage_switch"]["name"] == "Speicher On/Off"
    assert entities["storage_switch"]["can_control"] is True
    assert entities["grid_serving_forecast"]["name"] is None
    assert entities["timed_charge_discharge_status"]["states"] == {
        "normal": "Normalbetrieb",
        "grid_charging": "Netzladen",
        "discharge_blocked": "Entladung wg. Netzladen gestoppt",
    }


async def test_metadata_excludes_foreign_disabled_and_invalid_entities(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    dashboard_entry: MockConfigEntry,
) -> None:
    """Keine andere Anlage, Plattform, deaktivierte Option oder State-ID erraten."""
    allowed = _entity(entity_registry, dashboard_entry)
    other = MockConfigEntry(domain=DOMAIN, data={})
    other.add_to_hass(hass)
    _entity(entity_registry, other)
    _entity(
        entity_registry,
        dashboard_entry,
        "sun_model",
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    _entity(entity_registry, dashboard_entry, "unsupported", "button")
    _entity(entity_registry, dashboard_entry, "")
    entity_registry.async_get_or_create(
        "sensor", DOMAIN, "foreign_prefix", config_entry=dashboard_entry
    )
    entity_registry.async_get_or_create(
        "sensor",
        "demo",
        f"{dashboard_entry.entry_id}_demo",
        config_entry=dashboard_entry,
    )
    hass.states.async_set("sensor.sax_unknown", "123")
    client = await hass_ws_client(hass)

    entities = await _subscribe(client, dashboard_entry)
    assert [item["entity_id"] for item in entities] == [allowed.entity_id]


async def test_registry_changes_refresh_metadata_and_unsubscribe_cleans_listener(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    dashboard_entry: MockConfigEntry,
) -> None:
    """Rename, Optionsaktivierung und Removal aktualisieren ein offenes Panel."""
    entity = _entity(entity_registry, dashboard_entry)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    before = hass.bus.async_listeners().get(er.EVENT_ENTITY_REGISTRY_UPDATED, 0)
    await _subscribe(client, dashboard_entry)
    assert hass.bus.async_listeners()[er.EVENT_ENTITY_REGISTRY_UPDATED] == before + 1

    entity_registry.async_update_entity(
        entity.entity_id, new_entity_id="sensor.renamed", name="Akku"
    )
    event = await client.receive_json()
    assert event["event"]["entities"][0]["entity_id"] == "sensor.renamed"
    assert event["event"]["entities"][0]["name"] == "Akku"

    entity_registry.async_update_entity(
        "sensor.renamed", disabled_by=er.RegistryEntryDisabler.USER
    )
    assert (await client.receive_json())["event"]["entities"] == []
    entity_registry.async_update_entity("sensor.renamed", disabled_by=None)
    assert (await client.receive_json())["event"]["entities"][0]["key"] == "soc"

    optional = _entity(entity_registry, dashboard_entry, "sun_model")
    assert len((await client.receive_json())["event"]["entities"]) == 2
    entity_registry.async_remove(optional.entity_id)
    assert len((await client.receive_json())["event"]["entities"]) == 1
    entity_registry.async_remove("sensor.renamed")
    assert (await client.receive_json())["event"]["entities"] == []

    await client.send_json_auto_id({"type": "unsubscribe_events", "subscription": 1})
    assert (await client.receive_json())["success"] is True
    assert hass.bus.async_listeners().get(er.EVENT_ENTITY_REGISTRY_UPDATED, 0) == before


async def test_unrelated_registry_changes_do_not_emit_metadata(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    dashboard_entry: MockConfigEntry,
) -> None:
    """Änderungen fremder Entries erzeugen keine Datenereignisse im Panel."""
    client = await hass_ws_client(hass)
    await _subscribe(client, dashboard_entry)
    entity_registry.async_get_or_create("sensor", "demo", "other")
    await hass.async_block_till_done()
    await client.send_json_auto_id({"type": "ping"})
    assert (await client.receive_json())["type"] == "pong"


@pytest.mark.parametrize("entry_id", ["missing", "foreign"])
async def test_unknown_and_other_integration_entries_are_rejected(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    dashboard_entry: MockConfigEntry,
    entry_id: str,
) -> None:
    """Ungültige Entries liefern weder Metadaten noch bleibende Listener."""
    other = MockConfigEntry(domain="demo", entry_id="foreign", data={})
    other.add_to_hass(hass)
    client = await hass_ws_client(hass)
    before = hass.bus.async_listeners().get(er.EVENT_ENTITY_REGISTRY_UPDATED, 0)
    await client.send_json_auto_id(
        {"type": SUBSCRIBE_COMMAND, "entry_id": entry_id, "language": "de"}
    )
    result = await client.receive_json()
    assert result["success"] is False
    assert result["error"]["code"] == "not_found"
    assert hass.bus.async_listeners().get(er.EVENT_ENTITY_REGISTRY_UPDATED, 0) == before


@pytest.mark.parametrize("language", ["", "../de", "en_US", "de\n", "a" * 36, 42])
async def test_invalid_language_is_rejected_before_loading_translations(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    dashboard_entry: MockConfigEntry,
    language: Any,
) -> None:
    """Nur begrenzte Sprachkennungen dürfen die Übersetzungsauflösung erreichen."""
    client = await hass_ws_client(hass)
    with patch(f"{_MODULE}.translation.async_get_translations") as translations:
        await client.send_json_auto_id(
            {
                "type": SUBSCRIBE_COMMAND,
                "entry_id": dashboard_entry.entry_id,
                "language": language,
            }
        )
        result = await client.receive_json()
        assert result["error"]["code"] == "invalid_format"
        translations.assert_not_called()


async def test_read_only_user_receives_no_control_rights(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    entity_registry: er.EntityRegistry,
    dashboard_entry: MockConfigEntry,
) -> None:
    """Das optionale Panel bleibt für HA-Lesebenutzer vollständig schreibgeschützt."""
    for domain in ("sensor", "switch", "number", "time", "select"):
        _entity(entity_registry, dashboard_entry, f"test_{domain}", domain)
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    entities = await _subscribe(client, dashboard_entry)
    assert len(entities) == 5
    assert all(item["can_control"] is False for item in entities)


async def test_partial_permissions_are_checked_again_for_every_emission(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    hass_read_only_user: MockUser,
    entity_registry: er.EntityRegistry,
    dashboard_entry: MockConfigEntry,
) -> None:
    """Entzogene Rechte entfernen auch Metadaten bereits sichtbarer Entities."""
    allowed = _entity(entity_registry, dashboard_entry, "storage_switch", "switch")
    _entity(entity_registry, dashboard_entry)
    hass_read_only_user.mock_policy(
        {
            "entities": {
                "entity_ids": {allowed.entity_id: {"read": True, "control": True}}
            }
        }
    )
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    entities = await _subscribe(client, dashboard_entry)
    assert [item["entity_id"] for item in entities] == [allowed.entity_id]
    assert entities[0]["can_control"] is True

    hass_read_only_user.mock_policy({"entities": {}})
    entity_registry.async_update_entity(allowed.entity_id, name="Renamed")
    assert (await client.receive_json())["event"]["entities"] == []


@pytest.mark.parametrize("close_connection", [False, True])
async def test_cancel_during_translation_loading_does_not_leak_listener(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    dashboard_entry: MockConfigEntry,
    close_connection: bool,
) -> None:
    """Ein verzögertes Initialabo lebt nach Unsubscribe oder Disconnect nicht auf."""
    started = asyncio.Event()
    finish = asyncio.Event()

    async def translations(*args: Any, **kwargs: Any) -> dict[str, str]:
        started.set()
        await finish.wait()
        return {}

    client = await hass_ws_client(hass)
    before = hass.bus.async_listeners().get(er.EVENT_ENTITY_REGISTRY_UPDATED, 0)
    with patch(f"{_MODULE}.translation.async_get_translations", translations):
        await client.send_json_auto_id(
            {
                "type": SUBSCRIBE_COMMAND,
                "entry_id": dashboard_entry.entry_id,
                "language": "de",
            }
        )
        await started.wait()
        assert (
            hass.bus.async_listeners()[er.EVENT_ENTITY_REGISTRY_UPDATED] == before + 1
        )
        if close_connection:
            await client.close()
        else:
            await client.send_json_auto_id(
                {"type": "unsubscribe_events", "subscription": 1}
            )
            assert (await client.receive_json())["success"] is True
        await hass.async_block_till_done()
        assert (
            hass.bus.async_listeners().get(er.EVENT_ENTITY_REGISTRY_UPDATED, 0)
            == before
        )
        finish.set()
        await hass.async_block_till_done(wait_background_tasks=True)
        if not close_connection:
            await client.send_json_auto_id({"type": "ping"})
            assert (await client.receive_json())["type"] == "pong"


async def test_translation_failure_removes_listener(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    dashboard_entry: MockConfigEntry,
) -> None:
    """Ein fehlgeschlagenes Initialabo hinterlässt keinen Eventbus-Listener."""
    client = await hass_ws_client(hass)
    before = hass.bus.async_listeners().get(er.EVENT_ENTITY_REGISTRY_UPDATED, 0)
    with patch(
        f"{_MODULE}.translation.async_get_translations",
        AsyncMock(side_effect=ValueError("translation failed")),
    ):
        await client.send_json_auto_id(
            {
                "type": SUBSCRIBE_COMMAND,
                "entry_id": dashboard_entry.entry_id,
                "language": "de",
            }
        )
        assert (await client.receive_json())["success"] is False
    assert hass.bus.async_listeners().get(er.EVENT_ENTITY_REGISTRY_UPDATED, 0) == before


async def test_registration_is_idempotent(hass: HomeAssistant) -> None:
    """Mehrfaches optionales Panel-Setup registriert den Befehl nur einmal."""
    with patch(
        f"{_MODULE}.websocket_api.async_register_command",
        wraps=websocket_api.async_register_command,
    ) as register:
        async_register_dashboard_api(hass)
        async_register_dashboard_api(hass)
    assert register.call_count == 4
    assert len({call.args[1] for call in register.call_args_list}) == 4


async def test_initial_metadata_includes_changes_during_translation_loading(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    dashboard_entry: MockConfigEntry,
) -> None:
    """Zwischen Übersetzung und Listener darf kein Registry-Update verloren gehen."""
    started = asyncio.Event()
    finish = asyncio.Event()

    async def translations(*args: Any, **kwargs: Any) -> dict[str, str]:
        started.set()
        await finish.wait()
        return {}

    entity = _entity(entity_registry, dashboard_entry)
    client = await hass_ws_client(hass)
    with patch(f"{_MODULE}.translation.async_get_translations", translations):
        await client.send_json_auto_id(
            {
                "type": SUBSCRIBE_COMMAND,
                "entry_id": dashboard_entry.entry_id,
                "language": "de",
            }
        )
        await started.wait()
        entity_registry.async_update_entity(
            entity.entity_id, new_entity_id="sensor.latest"
        )
        await hass.async_block_till_done()
        finish.set()
        assert (await client.receive_json())["success"] is True
        entities = (await client.receive_json())["event"]["entities"]
        assert [item["entity_id"] for item in entities] == ["sensor.latest"]
