"""Private tariff comparison drafts for REQ-VUE-TARIFF-COMPARISON."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any, Literal, TypedDict
from uuid import uuid4

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import CoreState, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store
from homeassistant.util.hass_dict import HassKey

from .const import DOMAIN
from .infrastructure.storage_load import async_load_checked

GET_COMMAND = "sax_power/dashboard/tariff_comparison/get"
SAVE_COMMAND = "sax_power/dashboard/tariff_comparison/save"
MAX_COMPARISON_TARIFFS = 4

_LOGGER = logging.getLogger(__name__)
_STORAGE_VERSION = 1
_ENTRY_ID_SCHEMA = vol.All(str, vol.Length(min=1, max=128))
_REVISION_SCHEMA = vol.All(str, vol.Length(min=1, max=128))


class _WindowDraft(TypedDict):
    start: str
    end: str
    price: str
    share: str


class _TariffDraft(TypedDict):
    name: str
    number: int
    type: Literal["fixed", "time-of-use"]
    price: str
    baseFee: str
    baseFeePeriod: Literal["monthly", "yearly"]
    bonus: str
    windows: list[_WindowDraft]


class _ComparisonDraft(TypedDict):
    annual_consumption: str
    tariffs: list[_TariffDraft]


class _StoredComparison(_ComparisonDraft):
    revision: str


def _tariff_number(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 2**53 - 1:
        raise vol.Invalid("Expected a positive safe integer")
    return value


_WINDOW_SCHEMA = {
    vol.Required("start"): str,
    vol.Required("end"): str,
    vol.Required("price"): str,
    vol.Required("share"): str,
}
_TARIFF_SCHEMA = {
    vol.Required("name"): str,
    vol.Required("number"): _tariff_number,
    vol.Required("type"): vol.In(("fixed", "time-of-use")),
    vol.Required("price"): str,
    vol.Required("baseFee"): str,
    vol.Required("baseFeePeriod"): vol.In(("monthly", "yearly")),
    vol.Required("bonus"): str,
    vol.Required("windows"): [_WINDOW_SCHEMA],
}
_COMPARISON_FIELDS = {
    vol.Required("revision"): _REVISION_SCHEMA,
    vol.Required("annual_consumption"): str,
    vol.Required("tariffs"): vol.All(
        vol.Length(max=MAX_COMPARISON_TARIFFS), [_TARIFF_SCHEMA]
    ),
}
_COMPARISON_SCHEMA = vol.Schema(_COMPARISON_FIELDS)


class _ComparisonConflict(Exception):
    """The client attempted to replace a newer draft."""


class _ComparisonStore:
    def __init__(self, hass: HomeAssistant, entry_id: str, user_id: str) -> None:
        scope = hashlib.sha256(f"{entry_id}\0{user_id}".encode()).hexdigest()
        self._store: Store[dict[str, Any]] = Store(
            hass,
            _STORAGE_VERSION,
            f"{DOMAIN}.tariff_comparison.{scope}",
            private=True,
            atomic_writes=True,
            serialize_in_event_loop=False,
        )
        self._lock = asyncio.Lock()

    async def _read(self) -> _StoredComparison:
        stored = await async_load_checked(self._store.hass, self._store)
        if stored is None:
            return {"revision": "0", "annual_consumption": "", "tariffs": []}
        return _COMPARISON_SCHEMA(stored)

    async def async_load(self) -> _StoredComparison:
        async with self._lock:
            return await self._read()

    async def async_save(
        self, draft: _ComparisonDraft, revision: str
    ) -> _StoredComparison:
        async with self._lock:
            current = await self._read()
            if (
                current["annual_consumption"] == draft["annual_consumption"]
                and current["tariffs"] == draft["tariffs"]
            ):
                return current
            if current["revision"] != revision:
                raise _ComparisonConflict
            if self._store.hass.state is CoreState.stopping:
                raise HomeAssistantError("Home Assistant is stopping")
            updated: _StoredComparison = {**draft, "revision": uuid4().hex}
            await self._store.async_save(updated)
            # Core can log a write error without raising one to the caller.
            if await self._read() != updated:
                raise HomeAssistantError("Tariff comparison could not be verified")
            return updated


_STORES: HassKey[dict[tuple[str, str], _ComparisonStore]] = HassKey(
    f"{DOMAIN}_tariff_comparison_stores"
)


@callback
def async_register_dashboard_tariff_comparison(hass: HomeAssistant) -> None:
    """Register the authenticated read and save commands once per HA run."""
    for name, command in (
        (GET_COMMAND, websocket_get_tariff_comparison),
        (SAVE_COMMAND, websocket_save_tariff_comparison),
    ):
        if name not in hass.data.get(websocket_api.DOMAIN, {}):
            websocket_api.async_register_command(hass, command)


async def _send_comparison(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    if not connection.user.is_active:
        connection.send_error(msg["id"], "forbidden", "Tariff comparison denied")
        return
    entry_id = msg["entry_id"]
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Entry not found")
        return

    # This workspace contains only the authenticated user's calculator inputs.
    key = (entry_id, connection.user.id)
    stores = hass.data.setdefault(_STORES, {})
    if key not in stores:
        stores[key] = _ComparisonStore(hass, *key)
    store = stores[key]
    try:
        result = (
            await store.async_save(
                {
                    "annual_consumption": msg["annual_consumption"],
                    "tariffs": msg["tariffs"],
                },
                msg["revision"],
            )
            if msg["type"] == SAVE_COMMAND
            else await store.async_load()
        )
    except _ComparisonConflict:
        connection.send_error(msg["id"], "conflict", "Tariff comparison has changed")
    except (
        HomeAssistantError,
        KeyError,
        NotImplementedError,
        OSError,
        TypeError,
        ValueError,
        vol.Invalid,
    ):
        _LOGGER.warning("Tarifvergleich konnte nicht geladen oder gespeichert werden")
        connection.send_error(msg["id"], "failed", "Tariff comparison storage failed")
    else:
        if connection.user.is_active:
            connection.send_result(msg["id"], result)
        else:
            connection.send_error(msg["id"], "forbidden", "Tariff comparison denied")


@websocket_api.websocket_command(
    {
        vol.Required("type"): GET_COMMAND,
        vol.Required("entry_id"): _ENTRY_ID_SCHEMA,
    }
)
@websocket_api.async_response
async def websocket_get_tariff_comparison(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Load the current user's tariff comparison for this SAX entry."""
    await _send_comparison(hass, connection, msg)


@websocket_api.websocket_command(
    {
        vol.Required("type"): SAVE_COMMAND,
        vol.Required("entry_id"): _ENTRY_ID_SCHEMA,
        **_COMPARISON_FIELDS,
    }
)
@websocket_api.async_response
async def websocket_save_tariff_comparison(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Save only an unchanged revision of the current user's tariff comparison."""
    await _send_comparison(hass, connection, msg)
