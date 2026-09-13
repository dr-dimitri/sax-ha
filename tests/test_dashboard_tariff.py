"""Dashboard-Tarifeditor: Vertrag, atomare Speicherung und Rechte (REQ-VUE-CHARGING)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser
from pytest_homeassistant_custom_component.typing import (
    MockHAClientWebSocket,
    WebSocketGenerator,
)

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_PV_FORECAST_FACTOR,
    DOMAIN,
    ECONOMICS_TOU_WINDOW_KEYS,
)
from custom_components.sax_power.dashboard_api import async_register_dashboard_api
from custom_components.sax_power.dashboard_tariff import (
    GET_COMMAND,
    SAVE_COMMAND,
    websocket_save_tariff,
)


@pytest.fixture
def tariff_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_ECONOMICS_TARIFF_TYPE: "time_of_use",
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.3212,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.0786,
            ECONOMICS_TOU_WINDOW_KEYS[0]: {
                "start": "22:00:13",
                "end": "06:00:00",
                "price_eur_kwh": 0.21,
            },
            CONF_PV_FORECAST_FACTOR: 70,
        },
    )
    entry.add_to_hass(hass)
    async_register_dashboard_api(hass)
    return entry


async def _get(client: MockHAClientWebSocket, entry: MockConfigEntry) -> dict[str, Any]:
    await client.send_json_auto_id({"type": GET_COMMAND, "entry_id": entry.entry_id})
    response = await client.receive_json()
    assert response["success"] is True
    return response["result"]


def _save(entry: MockConfigEntry, tariff: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": SAVE_COMMAND,
        "entry_id": entry.entry_id,
        **{
            key: tariff[key]
            for key in (
                "base_price_ct_kwh",
                "feed_in_price_ct_kwh",
                "windows",
                "revision",
            )
        },
    }


async def test_admin_roundtrip_preserves_euro_options_and_precision(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    tariff_entry: MockConfigEntry,
) -> None:
    """REQ-ECONOMICS-TARIFFS: Ein Cent-Roundtrip erhält interne EUR-Werte."""
    original = deepcopy(dict(tariff_entry.options))
    client = await hass_ws_client(hass)
    tariff = await _get(client, tariff_entry)
    assert tariff == {
        "tariff_type": "time_of_use",
        "base_price_ct_kwh": 32.12,
        "feed_in_price_ct_kwh": 7.86,
        "windows": [{"start": "22:00:13", "end": "06:00:00", "price_ct_kwh": 21.0}],
        "revision": tariff["revision"],
        "can_edit": True,
    }
    await client.send_json_auto_id(_save(tariff_entry, tariff))
    response = await client.receive_json()
    assert response["success"] is True
    assert response["result"] == tariff
    assert tariff_entry.options == original


@pytest.mark.parametrize("window_count", [0, 1, 8])
async def test_save_atomically_replaces_windows_and_notifies_options_listener(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    tariff_entry: MockConfigEntry,
    window_count: int,
) -> None:
    """Fenster werden gemeinsam aktualisiert; entfernte verschwinden."""
    client = await hass_ws_client(hass)
    tariff = await _get(client, tariff_entry)
    listener = AsyncMock()
    tariff_entry.add_update_listener(listener)
    tariff["base_price_ct_kwh"] = -12.34
    tariff["feed_in_price_ct_kwh"] = 8.126
    tariff["windows"] = [
        {
            "start": f"{(21 + i * 3) % 24:02}:00",
            "end": f"{(i * 3) % 24:02}:00",
            "price_ct_kwh": 10 + i,
        }
        for i in range(window_count)
    ]
    await client.send_json_auto_id(_save(tariff_entry, tariff))
    response = await client.receive_json()
    assert response["success"] is True
    result = response["result"]
    assert len(result["windows"]) == window_count
    assert result["revision"] != tariff["revision"]
    assert result["feed_in_price_ct_kwh"] == 8.13
    assert tariff_entry.options[CONF_ECONOMICS_TOU_BASE_PRICE] == -0.1234
    assert tariff_entry.options[CONF_PV_FORECAST_FACTOR] == 70
    assert (
        sum(key in tariff_entry.options for key in ECONOMICS_TOU_WINDOW_KEYS)
        == window_count
    )
    await hass.async_block_till_done()
    listener.assert_awaited_once_with(hass, tariff_entry)


@pytest.mark.parametrize("change", ["base", "feed", "window", "type", "unrelated"])
async def test_revision_prevents_overwriting_a_newer_tariff(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    tariff_entry: MockConfigEntry,
    change: str,
) -> None:
    """Parallel geänderte Tarife sind geschützt; andere Options bleiben erhalten."""
    client = await hass_ws_client(hass)
    tariff = await _get(client, tariff_entry)
    changes = {
        "base": {CONF_ECONOMICS_TOU_BASE_PRICE: 0.33},
        "feed": {CONF_ECONOMICS_FEED_IN_PRICE: 0.10},
        "window": {
            ECONOMICS_TOU_WINDOW_KEYS[1]: {
                "start": "10:00",
                "end": "11:00",
                "price_eur_kwh": 0.2,
            }
        },
        "type": {CONF_ECONOMICS_TARIFF_TYPE: "fixed"},
        "unrelated": {CONF_PV_FORECAST_FACTOR: 90},
    }
    hass.config_entries.async_update_entry(
        tariff_entry, options={**tariff_entry.options, **changes[change]}
    )
    current = dict(tariff_entry.options)
    await client.send_json_auto_id(_save(tariff_entry, tariff))
    response = await client.receive_json()
    if change == "unrelated":
        assert response["success"] is True
        assert tariff_entry.options[CONF_PV_FORECAST_FACTOR] == 90
    else:
        assert response["error"]["code"] == "conflict"
    assert tariff_entry.options == current


@pytest.mark.parametrize(
    "changes",
    [
        {"base_price_ct_kwh": None},
        {"base_price_ct_kwh": "32"},
        {"base_price_ct_kwh": True},
        {"base_price_ct_kwh": -200.01},
        {"base_price_ct_kwh": 500.01},
        {"base_price_ct_kwh": float("inf")},
        {"base_price_ct_kwh": 10**400},
        {"base_price_ct_kwh": float("nan")},
        {"feed_in_price_ct_kwh": -0.01},
        {"feed_in_price_ct_kwh": 200.01},
        {"feed_in_price_ct_kwh": False},
        {"windows": [{"start": "22:00", "end": "06:00"}]},
        {"windows": [{"start": "22:00", "end": "22:00", "price_ct_kwh": 10}]},
        {"windows": [{"start": "25:00", "end": "06:00", "price_ct_kwh": 10}]},
        {"windows": [{"start": "2:00", "end": "06:00", "price_ct_kwh": 10}]},
        {"windows": [{"start": "22:00", "end": "06:00", "price_ct_kwh": 501}]},
        {
            "windows": [
                {"start": "22:00", "end": "06:00", "price_ct_kwh": 10, "extra": 1}
            ]
        },
        {
            "windows": [
                {"start": "22:00", "end": "06:00", "price_ct_kwh": 10},
                {"start": "05:00", "end": "07:00", "price_ct_kwh": 15},
            ]
        },
        {"windows": [{}] * 9},
        {"windows": {}},
    ],
)
async def test_invalid_profile_does_not_partially_write(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    tariff_entry: MockConfigEntry,
    changes: dict[str, Any],
) -> None:
    """REQ-ECONOMICS-TARIFFS: Ungültige Teilangaben verwerfen die Speicherung."""
    client = await hass_ws_client(hass)
    tariff = await _get(client, tariff_entry)
    original = deepcopy(dict(tariff_entry.options))
    # JSON lässt NaN/Infinity nicht zu; direkt am Handler dessen Preisprüfung testen.
    connection = MagicMock()
    connection.user.is_active = True
    connection.user.is_admin = True
    websocket_save_tariff(
        hass, connection, {"id": 42, **_save(tariff_entry, tariff), **changes}
    )
    assert connection.send_error.call_args.args[1] == "invalid_tariff"
    connection.send_result.assert_not_called()
    assert tariff_entry.options == original


@pytest.mark.parametrize(
    "field", ["revision", "base_price_ct_kwh", "feed_in_price_ct_kwh", "windows"]
)
async def test_missing_fields_are_rejected_by_the_websocket_schema(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    tariff_entry: MockConfigEntry,
    field: str,
) -> None:
    client = await hass_ws_client(hass)
    message = _save(tariff_entry, await _get(client, tariff_entry))
    del message[field]
    original = deepcopy(dict(tariff_entry.options))
    await client.send_json_auto_id(message)
    assert (await client.receive_json())["error"]["code"] == "invalid_format"
    assert tariff_entry.options == original


@pytest.mark.parametrize("command", [GET_COMMAND, SAVE_COMMAND])
@pytest.mark.parametrize("foreign", [False, True])
async def test_missing_and_foreign_entry_cannot_be_accessed(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    tariff_entry: MockConfigEntry,
    command: str,
    foreign: bool,
) -> None:
    client = await hass_ws_client(hass)
    message = _save(tariff_entry, await _get(client, tariff_entry))
    entry_id = "missing"
    if foreign:
        entry = MockConfigEntry(domain="other", data={}, options=tariff_entry.options)
        entry.add_to_hass(hass)
        entry_id = entry.entry_id
    if command == GET_COMMAND:
        message = {"type": command}
    message["entry_id"] = entry_id
    await client.send_json_auto_id(message)
    assert (await client.receive_json())["error"]["code"] == "not_found"


async def test_reader_needs_both_price_permissions_and_cannot_save(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    hass_read_only_user: MockUser,
    tariff_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    entities = [
        entity_registry.async_get_or_create(
            "sensor",
            DOMAIN,
            f"{tariff_entry.entry_id}_{key}",
            config_entry=tariff_entry,
        )
        for key in ("economics_current_import_price", "economics_feed_in_price")
    ]
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    tariff = await _get(client, tariff_entry)
    assert tariff["can_edit"] is False
    await client.send_json_auto_id(_save(tariff_entry, tariff))
    assert (await client.receive_json())["error"]["code"] == "forbidden"
    hass_read_only_user.mock_policy(
        {"entities": {"entity_ids": {entities[0].entity_id: {"read": True}}}}
    )
    await client.send_json_auto_id(
        {"type": GET_COMMAND, "entry_id": tariff_entry.entry_id}
    )
    assert (await client.receive_json())["error"]["code"] == "forbidden"


async def test_inactive_admin_cannot_save(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    tariff_entry: MockConfigEntry,
) -> None:
    client = await hass_ws_client(hass)
    tariff = await _get(client, tariff_entry)
    connection = MagicMock()
    connection.user.is_active = False
    connection.user.is_admin = True
    websocket_save_tariff(hass, connection, {"id": 42, **_save(tariff_entry, tariff)})
    assert connection.send_error.call_args.args[1] == "forbidden"


@pytest.mark.parametrize("tariff_type", ["time_of_use", "fixed", "disabled"])
async def test_admin_can_repair_missing_prices_but_only_for_time_of_use(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    tariff_entry: MockConfigEntry,
    tariff_type: str,
) -> None:
    hass.config_entries.async_update_entry(
        tariff_entry, options={CONF_ECONOMICS_TARIFF_TYPE: tariff_type}
    )
    client = await hass_ws_client(hass)
    tariff = await _get(client, tariff_entry)
    assert tariff["base_price_ct_kwh"] is None
    assert tariff["feed_in_price_ct_kwh"] is None
    assert tariff["windows"] == []
    assert tariff["can_edit"] is (tariff_type == "time_of_use")
    await client.send_json_auto_id(
        {
            **_save(tariff_entry, tariff),
            "base_price_ct_kwh": 32,
            "feed_in_price_ct_kwh": 8,
        }
    )
    response = await client.receive_json()
    assert response["success"] is (tariff_type == "time_of_use")
    if tariff_type != "time_of_use":
        assert response["error"]["code"] == "invalid_tariff"


@pytest.mark.parametrize("base,feed", [(-200.0, 0.0), (500.0, 200.0)])
async def test_price_bounds_are_valid_cent_values(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    tariff_entry: MockConfigEntry,
    base: float,
    feed: float,
) -> None:
    """REQ-ECONOMICS-TARIFFS: Beide erlaubten Grenzwerte gelten in Cent."""
    client = await hass_ws_client(hass)
    tariff = await _get(client, tariff_entry)
    await client.send_json_auto_id(
        {
            **_save(tariff_entry, tariff),
            "base_price_ct_kwh": base,
            "feed_in_price_ct_kwh": feed,
            "windows": [{"start": "22:00", "end": "06:00", "price_ct_kwh": base}],
        }
    )
    response = await client.receive_json()
    assert response["success"] is True
    assert response["result"]["base_price_ct_kwh"] == base
    assert response["result"]["feed_in_price_ct_kwh"] == feed
    assert tariff_entry.options[CONF_ECONOMICS_TOU_BASE_PRICE] == base / 100
    assert tariff_entry.options[CONF_ECONOMICS_FEED_IN_PRICE] == feed / 100
