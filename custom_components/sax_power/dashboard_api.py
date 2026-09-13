"""Berechtigte Entity-Metadaten für das Vue-Panel (REQ-VUE-ENTITY-BINDING)."""

from __future__ import annotations

from asyncio import CancelledError
from typing import Any, TypedDict

import voluptuous as vol
from homeassistant.auth.permissions.const import POLICY_CONTROL, POLICY_READ
from homeassistant.components import websocket_api
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import translation

from .const import DOMAIN
from .dashboard_statistics import async_register_dashboard_statistics
from .dashboard_tariff import async_register_dashboard_tariff

SUBSCRIBE_COMMAND = "sax_power/dashboard/subscribe"
_ENTITY_DOMAINS = {"sensor", "binary_sensor", "switch", "number", "time", "select"}
_CONTROL_DOMAINS = {"switch", "number", "time", "select"}


class _EntityMetadata(TypedDict):
    entity_id: str
    device_id: str | None
    domain: str
    key: str
    name: str | None
    states: dict[str, str]
    can_control: bool


@callback
def async_register_dashboard_api(hass: HomeAssistant) -> None:
    """Registriere den datenlesenden Befehl einmal pro Home-Assistant-Lauf."""
    if SUBSCRIBE_COMMAND not in hass.data.get(websocket_api.DOMAIN, {}):
        websocket_api.async_register_command(hass, websocket_subscribe_dashboard)
    async_register_dashboard_statistics(hass)
    async_register_dashboard_tariff(hass)


def _is_sax_entry(hass: HomeAssistant, entry_id: str) -> bool:
    entry = hass.config_entries.async_get_entry(entry_id)
    return entry is not None and entry.domain == DOMAIN


def _metadata(
    registry_entry: er.RegistryEntry,
    entry_id: str,
    translations: dict[str, str],
    connection: websocket_api.ActiveConnection,
) -> _EntityMetadata | None:
    prefix = f"{entry_id}_"
    entity_id = registry_entry.entity_id
    domain = registry_entry.domain
    permissions = connection.user.permissions
    if (
        registry_entry.platform != DOMAIN
        or registry_entry.disabled
        or domain not in _ENTITY_DOMAINS
        or not registry_entry.unique_id.startswith(prefix)
        or not permissions.check_entity(entity_id, POLICY_READ)
    ):
        return None
    key = registry_entry.unique_id.removeprefix(prefix)
    if not key:
        return None
    translation_key = registry_entry.translation_key or (
        "storage" if (domain, key) == ("switch", "storage_switch") else key
    )
    translation_prefix = f"component.{DOMAIN}.entity.{domain}.{translation_key}"
    state_prefix = f"{translation_prefix}.state."
    return {
        "entity_id": entity_id,
        "device_id": registry_entry.device_id,
        "domain": domain,
        "key": key,
        "name": (
            None
            if (domain, key) == ("sensor", "grid_serving_forecast")
            else registry_entry.name or translations.get(f"{translation_prefix}.name")
        ),
        "states": {
            state_key.removeprefix(state_prefix): value
            for state_key, value in translations.items()
            if state_key.startswith(state_prefix)
        },
        "can_control": domain in _CONTROL_DOMAINS
        and permissions.check_entity(entity_id, POLICY_CONTROL),
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): SUBSCRIBE_COMMAND,
        vol.Required("entry_id"): vol.All(str, vol.Length(min=1, max=128)),
        vol.Required("language"): vol.All(
            str,
            vol.Length(max=35),
            vol.Match(r"\A[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*\Z"),
        ),
    }
)
@websocket_api.async_response
async def websocket_subscribe_dashboard(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Liefere Registry-Zuordnung und Übersetzungen ohne eigenes Geräte-Polling."""
    msg_id = msg["id"]
    entry_id = msg["entry_id"]
    if not _is_sax_entry(hass, entry_id):
        connection.send_error(msg_id, websocket_api.ERR_NOT_FOUND, "Entry not found")
        return

    registry = er.async_get(hass)
    active = True
    translations: dict[str, str] | None = None
    tracked_ids: set[str] = set()

    @callback
    def send_metadata() -> None:
        nonlocal tracked_ids
        if not active or translations is None:
            return
        entities: list[_EntityMetadata] = []
        entries = er.async_entries_for_config_entry(registry, entry_id)
        tracked_ids = {entry.entity_id for entry in entries}
        # Berechtigungen können während einer offenen Verbindung wechseln.
        # Deshalb weder erlaubte Entities noch Kontrollrechte zwischenspeichern.
        if connection.user.is_active and _is_sax_entry(hass, entry_id):
            for entry in entries:
                if metadata := _metadata(entry, entry_id, translations, connection):
                    entities.append(metadata)
        entities.sort(key=lambda entity: (entity["domain"], entity["key"]))
        connection.send_event(msg_id, {"entities": entities})

    @callback
    def registry_updated(event: Event[er.EventEntityRegistryUpdatedData]) -> None:
        entity_id = event.data["entity_id"]
        current = registry.async_get(entity_id)
        if (
            entity_id in tracked_ids
            or event.data.get("old_entity_id") in tracked_ids
            or (current is not None and current.config_entry_id == entry_id)
        ):
            send_metadata()

    remove_listener = hass.bus.async_listen(
        er.EVENT_ENTITY_REGISTRY_UPDATED, registry_updated
    )

    @callback
    def unsubscribe() -> None:
        nonlocal active
        if active:
            active = False
            remove_listener()

    # Vor dem ersten await eintragen: Disconnect/Unsubscribe während des
    # Übersetzungsladens darf später keinen verwaisten Listener erzeugen.
    connection.subscriptions[msg_id] = unsubscribe
    try:
        translations = await translation.async_get_translations(
            hass, msg["language"], "entity", integrations=[DOMAIN]
        )
    except CancelledError:
        unsubscribe()
        connection.subscriptions.pop(msg_id, None)
        raise
    except Exception:
        if not active:
            return
        unsubscribe()
        connection.subscriptions.pop(msg_id, None)
        raise
    if active:
        connection.send_result(msg_id)
        send_metadata()
