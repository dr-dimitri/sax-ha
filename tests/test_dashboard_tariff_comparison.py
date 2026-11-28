"""REQ-VUE-TARIFF-COMPARISON: persisted private drafts at the WebSocket boundary."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.sax_power.const import DOMAIN
from custom_components.sax_power.dashboard_api import async_register_dashboard_api
from custom_components.sax_power.dashboard_tariff_comparison import (
    _STORES,
    GET_COMMAND,
    SAVE_COMMAND,
)
from tests.ha import MockConfigEntry, MockHAClientWebSocket, WebSocketGenerator


@pytest.fixture
def comparison_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    async_register_dashboard_api(hass)
    return entry


def _draft(number: int = 1) -> dict[str, Any]:
    return {
        "name": f"Tarif {number}",
        "number": number,
        "type": "time-of-use",
        "price": "0,",
        "baseFee": "",
        "baseFeePeriod": "monthly",
        "bonus": "nicht fertig",
        "windows": [{"start": "22:", "end": "", "price": "3,0", "share": "120"}],
    }


def _save_message(
    entry_id: str, revision: str, *drafts: dict[str, Any]
) -> dict[str, Any]:
    return {
        "type": SAVE_COMMAND,
        "entry_id": entry_id,
        "revision": revision,
        "annual_consumption": "3.500,",
        "tariffs": list(drafts),
    }


async def _get(client: MockHAClientWebSocket, entry_id: str) -> dict[str, Any]:
    await client.send_json_auto_id({"type": GET_COMMAND, "entry_id": entry_id})
    return await client.receive_json()


async def _save(
    client: MockHAClientWebSocket, message: dict[str, Any]
) -> dict[str, Any]:
    await client.send_json_auto_id(message)
    return await client.receive_json()


async def test_round_trip_preserves_unfinished_drafts_across_store_instances(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    comparison_entry: MockConfigEntry,
) -> None:
    client = await hass_ws_client(hass)
    entry_id = comparison_entry.entry_id
    empty = (await _get(client, entry_id))["result"]
    assert empty == {"revision": "0", "annual_consumption": "", "tariffs": []}

    request = _save_message(entry_id, "0", *(_draft(i) for i in range(1, 5)))
    saved = await _save(client, request)
    assert saved["success"]
    revision = saved["result"]["revision"]
    assert revision != "0"
    assert saved["result"] == {
        "revision": revision,
        "annual_consumption": request["annual_consumption"],
        "tariffs": request["tariffs"],
    }

    hass.data.pop(_STORES)
    another_browser = await hass_ws_client(hass)
    assert (await _get(another_browser, entry_id))["result"] == saved["result"]
    assert (await _save(another_browser, request))["result"] == saved["result"]

    too_many = _save_message(entry_id, revision, *(_draft(i) for i in range(1, 6)))
    invalid = await _save(client, too_many)
    assert invalid["error"]["code"] == "invalid_format"
    assert (await _get(client, entry_id))["result"] == saved["result"]

    reset = (await _save(client, _save_message(entry_id, revision)))["result"]
    assert reset["tariffs"] == []
    assert reset["annual_consumption"] == request["annual_consumption"]
    assert reset["revision"] != revision
    assert (await _get(another_browser, entry_id))["result"] == reset


async def test_private_drafts_are_isolated_by_user_and_sax_entry(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    comparison_entry: MockConfigEntry,
    hass_read_only_access_token: str,
) -> None:
    admin_client = await hass_ws_client(hass)
    regular_client = await hass_ws_client(
        hass, access_token=hass_read_only_access_token
    )
    entry_id = comparison_entry.entry_id
    another = MockConfigEntry(domain=DOMAIN, data={})
    another.add_to_hass(hass)

    admin = await _save(admin_client, _save_message(entry_id, "0", _draft(1)))
    assert admin["success"]
    assert (await _get(regular_client, entry_id))["result"]["tariffs"] == []
    assert (await _get(admin_client, another.entry_id))["result"]["tariffs"] == []

    own = await _save(regular_client, _save_message(entry_id, "0", _draft(2)))
    assert own["success"]
    assert own["result"]["tariffs"] == [_draft(2)]
    assert (await _get(admin_client, entry_id))["result"]["tariffs"] == [_draft(1)]
    assert (await _get(regular_client, entry_id))["result"] == own["result"]
    assert not hass.data.get(DOMAIN)


async def test_simultaneous_updates_with_same_revision_do_not_lose_drafts(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    comparison_entry: MockConfigEntry,
) -> None:
    first = await hass_ws_client(hass)
    second = await hass_ws_client(hass)
    entry_id = comparison_entry.entry_id

    results = await asyncio.gather(
        _save(first, _save_message(entry_id, "0", _draft(1))),
        _save(second, _save_message(entry_id, "0", _draft(2))),
    )

    saved = [response["result"] for response in results if response["success"]]
    errors = [
        response["error"]["code"] for response in results if not response["success"]
    ]
    assert len(saved) == 1
    assert errors == ["conflict"]
    assert (await _get(second, entry_id))["result"] == saved[0]


@pytest.mark.parametrize("field", ["user_id", "number", "window_extra", "tariff_extra"])
async def test_rejects_unknown_fields_and_non_integer_numbers(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    comparison_entry: MockConfigEntry,
    field: str,
) -> None:
    client = await hass_ws_client(hass)
    entry_id = comparison_entry.entry_id
    tariff = _draft()
    msg = _save_message(entry_id, "0", tariff)
    if field == "user_id":
        msg["user_id"] = "another-user"
    elif field == "number":
        tariff["number"] = True
    elif field == "window_extra":
        tariff["windows"][0]["arbitrary"] = "value"
    else:
        tariff["arbitrary"] = "value"

    assert (await _save(client, msg))["error"]["code"] == "invalid_format"
    assert (await _get(client, entry_id))["result"]["revision"] == "0"


async def test_nonexistent_and_other_integration_entries_are_rejected(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    comparison_entry: MockConfigEntry,
) -> None:
    client = await hass_ws_client(hass)
    other = MockConfigEntry(domain="demo", data={})
    other.add_to_hass(hass)
    for wrong_id in (other.entry_id, "nonexistent"):
        assert (await _get(client, wrong_id))["error"]["code"] == "not_found"
        assert (await _save(client, _save_message(wrong_id, "0", _draft())))["error"][
            "code"
        ] == "not_found"


async def test_failed_store_write_is_not_acknowledged(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    comparison_entry: MockConfigEntry,
) -> None:
    client = await hass_ws_client(hass)
    entry_id = comparison_entry.entry_id
    initial = (await _save(client, _save_message(entry_id, "0", _draft())))["result"]
    store = next(iter(hass.data[_STORES].values()))
    with patch.object(store._store, "async_save", new=AsyncMock()):
        response = await _save(
            client, _save_message(entry_id, initial["revision"], _draft(2))
        )
    assert response["error"]["code"] == "failed"
    assert (await _get(client, entry_id))["result"] == initial


async def test_invalid_stored_data_does_not_look_like_an_empty_comparison(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    comparison_entry: MockConfigEntry,
) -> None:
    client = await hass_ws_client(hass)
    entry_id = comparison_entry.entry_id
    await _get(client, entry_id)
    store = next(iter(hass.data[_STORES].values()))
    invalid = {"revision": "bad", "annual_consumption": None, "tariffs": []}
    await store._store.async_save(invalid)

    assert (await _get(client, entry_id))["error"]["code"] == "failed"
    assert (await _save(client, _save_message(entry_id, "0", _draft())))["error"][
        "code"
    ] == "failed"
    assert await store._store.async_load() == invalid


async def test_quarantined_comparison_does_not_look_like_an_empty_comparison(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    comparison_entry: MockConfigEntry,
) -> None:
    client = await hass_ws_client(hass)
    entry_id = comparison_entry.entry_id
    await _get(client, entry_id)
    store = next(iter(hass.data[_STORES].values()))
    backup = Path(f"{store._store.path}.corrupt.test")

    def create_quarantine_evidence() -> None:
        backup.parent.mkdir(exist_ok=True)
        backup.write_text("{", encoding="utf-8")

    await hass.async_add_executor_job(create_quarantine_evidence)

    assert (await _get(client, entry_id))["error"]["code"] == "failed"
    assert (await _save(client, _save_message(entry_id, "0", _draft())))["error"][
        "code"
    ] == "failed"
