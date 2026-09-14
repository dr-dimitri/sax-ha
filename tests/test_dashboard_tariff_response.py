"""REQ-VUE-ELECTRICITY-TARIFF: Der Tarifhauptschalter bestätigt ohne Gerätewartezeit."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_PRICE_SENSOR,
    DATA_COORDINATOR,
    DOMAIN,
    PRICE_STRATEGY_ABSOLUTE,
    REG_SUN_IC_CONTROL_MODE,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.dashboard_api import async_register_dashboard_api
from custom_components.sax_power.dashboard_tariff import CONFIGURE_COMMAND, GET_COMMAND

from .test_month_switch_response import coordinator as coordinator


@contextmanager
def _control_clock() -> Iterator[None]:
    """Keep HA boundary timers on the test date without freezing asyncio sleep."""
    now = datetime(2024, 1, 1, 2, tzinfo=UTC)
    with (
        patch("custom_components.sax_power.coordinator.dt_util.now", return_value=now),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow", return_value=now
        ),
        patch(
            "homeassistant.helpers.event.time",
            SimpleNamespace(time=lambda: now.timestamp()),
        ),
        patch(
            "homeassistant.helpers.event.time_tracker_timestamp",
            return_value=now.timestamp(),
        ),
        patch("homeassistant.helpers.event.time_tracker_utcnow", return_value=now),
    ):
        yield


def _prepare(
    hass: HomeAssistant, coordinator: SaxPowerCoordinator, tariff_type: str
) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id=coordinator.entry_id,
        options={
            CONF_ECONOMICS_TARIFF_TYPE: tariff_type,
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.32,
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
            CONF_PRICE_SENSOR: "sensor.price",
        },
    )
    entry.add_to_hass(hass)
    coordinator.options = dict(entry.options)
    coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    coordinator._price_charge_max_price = 0.2
    hass.states.async_set(
        "sensor.price",
        "0.1",
        {
            "unit_of_measurement": "EUR/kWh",
            "prices": [
                {
                    "start": "2024-01-01T00:00:00+00:00",
                    "end": "2024-01-01T06:00:00+00:00",
                    "price": 0.1,
                }
            ],
        },
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}
    async_register_dashboard_api(hass)
    return entry


async def _get(client: Any, entry: MockConfigEntry) -> dict[str, Any]:
    await client.send_json_auto_id({"type": GET_COMMAND, "entry_id": entry.entry_id})
    response = await client.receive_json()
    assert response["success"]
    return response["result"]


async def _toggle(
    client: Any, entry: MockConfigEntry, tariff: dict[str, Any], enabled: bool
) -> dict[str, Any]:
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": tariff["revision"],
            "tariff_type": tariff["tariff_type"],
            "automation_enabled": enabled,
        }
    )
    return await client.receive_json()


@pytest.mark.parametrize("tariff_type", ["time_of_use", "dynamic"])
async def test_tariff_switch_confirms_and_coalesces_while_device_control_is_busy(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    tariff_type: str,
) -> None:
    """Ein/Aus antwortet vor dem Geräte-Lock und verändert keine Tarifkonfiguration."""
    entry = _prepare(hass, coordinator, tariff_type)
    before = dict(entry.options)
    listener = AsyncMock()
    entry.add_update_listener(listener)
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    with (
        patch.object(coordinator.price_planner, "async_setup") as setup_planner,
        patch.object(coordinator.tariff_provider, "async_setup") as setup_provider,
        patch.object(coordinator, "_async_enforce_grid_charge_locked") as enforce,
        patch.object(coordinator, "async_update_listeners") as notify,
    ):
        async with coordinator._charge_control_lock:
            task = None
            for enabled in (True, False, True):
                response = await asyncio.wait_for(
                    _toggle(client, entry, tariff, enabled), 0.2
                )
                assert response["success"]
                assert response["result"]["automation_enabled"] is enabled
                assert response["result"]["revision"] == tariff["revision"]
                assert coordinator.timed_charge_enabled is (
                    enabled and tariff_type == "time_of_use"
                )
                assert coordinator.price_charge_enabled is (
                    enabled and tariff_type == "dynamic"
                )
                if task is None:
                    task = coordinator._month_control_task
                assert coordinator._month_control_task is task
                assert task is not None and not task.done()
                assert coordinator._control_store._pending is not None
                assert coordinator._control_store._pending["price_charge_enabled"] is (
                    enabled and tariff_type == "dynamic"
                )
                assert entry.options == coordinator.options == before
                assert not coordinator.price_charge_active
                enforce.assert_not_awaited()
                coordinator.client.write_register.assert_not_awaited()
            notify.assert_called()
        await task
        enforce.assert_awaited_once()
    setup_planner.assert_not_called()
    setup_provider.assert_not_called()
    listener.assert_not_awaited()


async def test_tariff_switch_off_during_write_awaits_ack_and_rolls_back(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    """Sofort bestätigtes Aus wartet den Modus-ACK ab und widerruft den Sollwert."""
    entry = _prepare(hass, coordinator, "dynamic")
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    started, finish = asyncio.Event(), asyncio.Event()
    cancelled = False
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        nonlocal cancelled
        if address == REG_SUN_IC_CONTROL_MODE and value == SUN_IC_CONTROL_MODE_SETPOINT:
            started.set()
            try:
                await finish.wait()
            except asyncio.CancelledError:
                cancelled = True
                raise
        return success

    coordinator.client.write_register.side_effect = write
    with _control_clock():
        assert (await _toggle(client, entry, tariff, True))["success"]
        task = coordinator._month_control_task
        try:
            await asyncio.wait_for(started.wait(), 1)
            assert not coordinator.price_charge_active
            response = await asyncio.wait_for(
                _toggle(client, entry, tariff, False), 0.2
            )
            assert response["success"]
            assert response["result"]["automation_enabled"] is False
            assert not coordinator.price_charge_enabled
            assert coordinator._month_control_task is task
        finally:
            finish.set()
        await task
    writes = [
        (call.kwargs["address"], call.kwargs["value"])
        for call in coordinator.client.write_register.await_args_list
    ]
    assert writes == [
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT),
        (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER),
    ]
    assert not cancelled
    assert not coordinator.sun_charge_active
    assert not coordinator.price_charge_active
    assert not coordinator._sun_charge_reset_required


@pytest.mark.parametrize("tariff_type", ["time_of_use", "dynamic"])
async def test_saving_an_unchanged_profile_does_not_wait_for_device_control(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    tariff_type: str,
) -> None:
    """Ein bereits vollständiges Profil erneut zu speichern ist kein Tarifwechsel."""
    entry = _prepare(hass, coordinator, tariff_type)
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)

    async def save() -> dict[str, Any]:
        await client.send_json_auto_id(
            {
                "type": CONFIGURE_COMMAND,
                "entry_id": entry.entry_id,
                "revision": tariff["revision"],
                "tariff_type": tariff_type,
                "profile": tariff["profiles"][tariff_type],
            }
        )
        return await client.receive_json()

    initial = await save()
    assert initial["success"]
    tariff = initial["result"]
    if coordinator._month_control_task is not None:
        await coordinator._month_control_task
    before = dict(entry.options)
    with (
        patch.object(coordinator.price_planner, "async_setup") as planner,
        patch.object(coordinator.tariff_provider, "async_setup") as provider,
    ):
        async with coordinator._charge_control_lock:
            response = await asyncio.wait_for(save(), 0.2)
            assert response["success"]
            assert response["result"]["revision"] == tariff["revision"]
            assert entry.options == coordinator.options == before
            task = coordinator._month_control_task
        if task is not None:
            await task
    planner.assert_not_called()
    provider.assert_not_called()


@pytest.mark.parametrize("reason", ["shutdown", "bootstrap", "conflict", "incomplete"])
async def test_fast_tariff_switch_rejects_invalid_state_before_mutation(
    hass: HomeAssistant, coordinator: SaxPowerCoordinator, reason: str
) -> None:
    """Der schnelle Konfigurationspfad überspringt keine Laufzeitvalidierung."""
    entry = _prepare(hass, coordinator, "dynamic")
    options = dict(entry.options)
    if reason == "shutdown":
        await coordinator.async_shutdown(reset_device=False)
    elif reason == "bootstrap":
        coordinator._control_bootstrap_pending = True
    elif reason == "conflict":
        hass.config_entries.async_update_entry(
            entry, options={**options, CONF_PRICE_SENSOR: "sensor.other"}
        )
    else:
        options.pop(CONF_PRICE_SENSOR)
        coordinator.options = options
        hass.config_entries.async_update_entry(entry, options=options)
    before = dict(entry.options)
    async with coordinator._charge_control_lock:
        with pytest.raises((HomeAssistantError, ServiceValidationError)):
            await asyncio.wait_for(
                coordinator.async_apply_dashboard_tariff(
                    options, enabled=True, expected_options=options
                ),
                0.2,
            )
    assert not coordinator.price_charge_enabled
    assert not coordinator.timed_charge_enabled
    assert entry.options == before
    assert coordinator._control_store._pending is None
    assert coordinator._month_control_task is None
    coordinator.client.write_register.assert_not_awaited()
