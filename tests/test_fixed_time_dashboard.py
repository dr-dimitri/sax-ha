"""REQ-FIXED-TIME-GRID-CHARGE: atomare Tarif-API vor physischen Geräte-ACKs."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pymodbus.exceptions import ModbusException
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.sax_power.const import (
    CONF_BRIDGE_CHARGE_ENABLED,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_FIXED_TIME_CHARGE_ENABLED,
    CONF_FIXED_TIME_CHARGE_START,
    CONF_PV_FORECAST_SENSOR,
    DOMAIN,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.dashboard_tariff import CONFIGURE_COMMAND

from .test_dashboard_tariff_response import _control_clock, _get, _prepare, _toggle
from .test_month_switch_response import coordinator as coordinator


async def _configure(
    client: Any,
    entry: MockConfigEntry,
    tariff: dict[str, Any],
    **changes: Any,
) -> dict[str, Any]:
    await client.send_json_auto_id(
        {
            "type": CONFIGURE_COMMAND,
            "entry_id": entry.entry_id,
            "revision": tariff["revision"],
            "tariff_type": tariff["tariff_type"],
            **changes,
        }
    )
    return await client.receive_json()


def _profile(tariff: dict[str, Any], target: str) -> dict[str, Any]:
    profile = dict(tariff["profiles"][target])
    if profile["feed_in_price_ct_kwh"] is None:
        profile["feed_in_price_ct_kwh"] = 8
    if target == "time_of_use" and profile["base_price_ct_kwh"] is None:
        profile["base_price_ct_kwh"] = 32
    if target == "dynamic" and profile["price_sensor"] is None:
        profile["price_sensor"] = "sensor.price"
    return profile


@pytest.mark.parametrize("tariff_type", ["time_of_use", "dynamic"])
async def test_fixed_time_default_and_saved_time_round_trip(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    tariff_type: str,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Ein unverfügbarer Start ist explizit null."""
    entry = _prepare(hass, coordinator, tariff_type)
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    assert tariff["fixed_time_charging"] == {"enabled": False, "start": None}
    for start, canonical in (("00:00", "00:00:00"), ("23:59:59", "23:59:59")):
        response = await _configure(
            client,
            entry,
            tariff,
            fixed_time_charging={"enabled": True, "start": start},
        )
        assert response["success"], response
        tariff = response["result"]
        assert tariff["fixed_time_charging"] == {"enabled": True, "start": canonical}
        assert entry.options[CONF_FIXED_TIME_CHARGE_ENABLED] is True
        assert entry.options[CONF_FIXED_TIME_CHARGE_START] == canonical
        assert not coordinator.timed_charge_enabled
        assert not coordinator.price_charge_enabled
        assert not coordinator.sun_charge_active
        if coordinator._month_control_task is not None:
            await coordinator._month_control_task
    response = await _configure(
        client,
        entry,
        tariff,
        fixed_time_charging={"enabled": False, "start": "23:59:59"},
    )
    assert response["success"], response
    assert response["result"]["fixed_time_charging"] == {
        "enabled": False,
        "start": "23:59:59",
    }
    assert (await _get(client, entry))["fixed_time_charging"] == response["result"][
        "fixed_time_charging"
    ]


@pytest.mark.parametrize(
    "submitted",
    [
        None,
        True,
        [],
        {},
        {"enabled": True},
        {"start": "03:00"},
        {"enabled": 1, "start": "03:00"},
        {"enabled": "true", "start": "03:00"},
        {"enabled": None, "start": "03:00"},
        {"enabled": True, "start": None},
        {"enabled": True, "start": False},
        {"enabled": True, "start": ["03:00"]},
        {"enabled": True, "start": ""},
        {"enabled": True, "start": "3:00"},
        {"enabled": True, "start": "03:"},
        {"enabled": True, "start": "03:0"},
        {"enabled": True, "start": "03:00:"},
        {"enabled": True, "start": "24:00"},
        {"enabled": True, "start": "-1:00"},
        {"enabled": True, "start": "03:60"},
        {"enabled": True, "start": "03:00:60"},
        {"enabled": True, "start": "03:00:00.5"},
        {"enabled": True, "start": "03:00+02:00"},
        {"enabled": True, "start": "03:00Z"},
        {"enabled": True, "start": " 03:00"},
        {"enabled": False, "start": None},
        {"enabled": True, "start": "03:00", "end": "04:00"},
    ],
)
async def test_invalid_fixed_start_rejects_entire_tariff_and_runtime_mutation(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    submitted: Any,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Ungültige Eingaben verlieren keine Entwürfe."""
    entry = _prepare(hass, coordinator, "time_of_use")
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    before = deepcopy(dict(entry.options))
    response = await _configure(
        client,
        entry,
        tariff,
        tariff_type="dynamic",
        profile=_profile(tariff, "dynamic"),
        automation_enabled=True,
        fixed_time_charging=submitted,
    )
    assert response["success"] is False
    assert response["error"]["code"] == "invalid_fixed_time_start"
    assert entry.options == coordinator.options == before
    assert not coordinator.timed_charge_enabled
    assert not coordinator.price_charge_enabled
    assert coordinator._month_control_task is None
    assert coordinator._control_store._pending is None
    coordinator.client.write_register.assert_not_awaited()


async def test_fixed_time_is_global_and_excludes_restored_bridge_profile(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Tarifwechsel behalten die tägliche Uhrzeit."""
    entry = _prepare(hass, coordinator, "time_of_use")
    hass.states.async_set("sensor.pv_start", "8", {"unit_of_measurement": "kWh"})
    options = {
        **entry.options,
        CONF_BRIDGE_CHARGE_ENABLED: True,
        CONF_PV_FORECAST_SENSOR: "sensor.pv_start",
    }
    hass.config_entries.async_update_entry(entry, options=options)
    coordinator.options = dict(options)
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    response = await _configure(
        client,
        entry,
        tariff,
        fixed_time_charging={"enabled": True, "start": "03:15"},
        automation_enabled=True,
    )
    assert response["success"], response
    tariff = response["result"]
    assert entry.options[CONF_BRIDGE_CHARGE_ENABLED] is False
    for target in ("dynamic", "time_of_use"):
        response = await _configure(
            client,
            entry,
            tariff,
            tariff_type=target,
            profile=_profile(tariff, target),
        )
        assert response["success"], response
        tariff = response["result"]
        assert tariff["fixed_time_charging"] == {"enabled": True, "start": "03:15:00"}
        assert tariff["automation_enabled"] is True
        assert coordinator.timed_charge_enabled is (target == "time_of_use")
        assert coordinator.price_charge_enabled is (target == "dynamic")
        assert not coordinator.bridge_charge_enabled
        assert entry.options[CONF_BRIDGE_CHARGE_ENABLED] is False


@pytest.mark.parametrize(
    ("tariff_type", "method"),
    [
        ("time_of_use", "fixed"),
        ("time_of_use", "bridge"),
        ("dynamic", "smart"),
        ("dynamic", "relative"),
        ("dynamic", "absolute"),
        ("dynamic", "off"),
    ],
)
async def test_method_change_disables_fixed_start_atomically_before_device_lock(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    tariff_type: str,
    method: str,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Ein neuer Modus benötigt keinen Geräte-Lock."""
    entry = _prepare(hass, coordinator, tariff_type)
    options = {
        **entry.options,
        CONF_FIXED_TIME_CHARGE_ENABLED: True,
        CONF_FIXED_TIME_CHARGE_START: "03:00:00",
        CONF_PV_FORECAST_SENSOR: "sensor.pv_start",
    }
    hass.config_entries.async_update_entry(entry, options=options)
    coordinator.options = dict(options)
    hass.states.async_set("sensor.pv_start", "8", {"unit_of_measurement": "kWh"})
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    async with coordinator._charge_control_lock:
        response = await asyncio.wait_for(
            _configure(client, entry, tariff, charging_method=method), 0.2
        )
        assert response["success"], response
        assert response["result"]["fixed_time_charging"] == {
            "enabled": False,
            "start": "03:00:00",
        }
        assert coordinator.options == entry.options
        assert not coordinator.fixed_time_charge_enabled
        if tariff_type == "time_of_use":
            assert coordinator.bridge_charge_enabled is (method == "bridge")
        else:
            assert coordinator.price_charge_strategy == method
            assert (
                coordinator._control_store._pending["price_charge_strategy"] == method
            )
        coordinator.client.write_register.assert_not_awaited()
        task = coordinator._month_control_task
    await task


@pytest.mark.parametrize(
    ("tariff_type", "method", "fixed"),
    [
        ("time_of_use", "smart", None),
        ("dynamic", "fixed", None),
        ("time_of_use", "fixed", {"enabled": True, "start": "03:00"}),
        ("dynamic", "relative", {"enabled": True, "start": "03:00"}),
    ],
)
async def test_conflicting_method_rejects_without_mutation(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    tariff_type: str,
    method: str,
    fixed: dict[str, Any] | None,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Der Server akzeptiert genau einen Lademodus."""
    entry = _prepare(hass, coordinator, tariff_type)
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    before = deepcopy(dict(entry.options))
    response = await _configure(
        client,
        entry,
        tariff,
        charging_method=method,
        **({"fixed_time_charging": fixed} if fixed is not None else {}),
    )
    assert response["error"]["code"] == "invalid_tariff"
    assert entry.options == coordinator.options == before
    assert coordinator._month_control_task is None


async def test_changed_fixed_start_invalidates_old_tariff_revision(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Andere Editoren überschreiben keine neue Uhrzeit."""
    entry = _prepare(hass, coordinator, "dynamic")
    client = await hass_ws_client(hass)
    original = await _get(client, entry)
    response = await _configure(
        client,
        entry,
        original,
        fixed_time_charging={"enabled": True, "start": "03:00"},
    )
    assert response["success"], response
    assert response["result"]["revision"] != original["revision"]
    if coordinator._month_control_task is not None:
        await coordinator._month_control_task
    before = deepcopy(dict(entry.options))
    response = await _configure(
        client,
        entry,
        original,
        fixed_time_charging={"enabled": False, "start": "04:00"},
        automation_enabled=True,
    )
    assert response["error"]["code"] == "conflict"
    assert entry.options == coordinator.options == before
    assert not coordinator.price_charge_enabled


async def test_fixed_start_requires_administrator_even_with_tariff_read_permission(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Leseberechtigung erteilt keine Ladefreigabe."""
    from homeassistant.helpers import entity_registry as er

    entry = _prepare(hass, coordinator, "dynamic")
    registry = er.async_get(hass)
    for key in ("economics_current_import_price", "economics_feed_in_price"):
        registry.async_get_or_create(
            "sensor", DOMAIN, f"{entry.entry_id}_{key}", config_entry=entry
        )
    client = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    tariff = await _get(client, entry)
    before = dict(entry.options)
    response = await _configure(
        client,
        entry,
        tariff,
        fixed_time_charging={"enabled": True, "start": "03:00"},
    )
    assert response["error"]["code"] == "forbidden"
    assert entry.options == coordinator.options == before
    coordinator.client.write_register.assert_not_awaited()


@pytest.mark.parametrize("tariff_type", ["time_of_use", "dynamic"])
async def test_fixed_start_and_automation_coalesce_behind_held_device_lock(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    tariff_type: str,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Nur die zuletzt bestätigte Uhrzeit steuert."""
    entry = _prepare(hass, coordinator, tariff_type)
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    with patch.object(coordinator, "_async_enforce_grid_charge_locked") as enforce:
        async with coordinator._charge_control_lock:
            task = None
            for enabled, start in ((True, "03:00"), (False, "04:15"), (True, "05:30")):
                response = await asyncio.wait_for(
                    _configure(
                        client,
                        entry,
                        tariff,
                        fixed_time_charging={"enabled": enabled, "start": start},
                        automation_enabled=enabled,
                    ),
                    0.2,
                )
                assert response["success"], response
                tariff = response["result"]
                assert tariff["fixed_time_charging"] == {
                    "enabled": enabled,
                    "start": f"{start}:00",
                }
                assert tariff["automation_enabled"] is enabled
                assert coordinator.options == entry.options
                assert coordinator.fixed_time_charge_enabled is enabled
                assert coordinator.timed_charge_enabled is (
                    enabled and tariff_type == "time_of_use"
                )
                assert coordinator.price_charge_enabled is (
                    enabled and tariff_type == "dynamic"
                )
                if task is None:
                    task = coordinator._month_control_task
                assert coordinator._month_control_task is task
                assert coordinator._control_store._pending is not None
                enforce.assert_not_awaited()
                coordinator.client.write_register.assert_not_awaited()
        await task
        enforce.assert_awaited_once()


@pytest.mark.parametrize("periodic", [False, True])
@pytest.mark.parametrize(
    "held_register", [REG_SUN_IC_CONTROL_MODE, REG_SUN_IC_POWER_SETPOINT_PCT]
)
@pytest.mark.parametrize("failed_ack", [False, True])
async def test_fixed_start_change_during_ack_drains_and_resets_previous_writer(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    periodic: bool,
    held_register: int,
    failed_ack: bool,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: WS bestätigt vor beiden Geräte-ACK-Phasen."""
    entry = _prepare(hass, coordinator, "dynamic")
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    started, finish = asyncio.Event(), asyncio.Event()
    cancelled = False
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        nonlocal cancelled
        matches_writer = (
            asyncio.current_task() is coordinator._sun_charge_task
        ) is periodic
        if (
            not started.is_set()
            and matches_writer
            and address == held_register
            and (address != REG_SUN_IC_CONTROL_MODE or value == 1)
        ):
            started.set()
            try:
                await finish.wait()
            except asyncio.CancelledError:
                cancelled = True
                raise
            if failed_ack:
                raise ModbusException("delayed fixed-start test failure")
        return success

    coordinator.client.write_register.side_effect = write
    with (
        _control_clock(),
        patch.object(coordinator, "_sun_ic_write_interval", return_value=0.01),
    ):
        assert (await _toggle(client, entry, tariff, True))["success"]
        try:
            await asyncio.wait_for(started.wait(), 1)
            writer = coordinator._sun_charge_task
            response = await asyncio.wait_for(
                _configure(
                    client,
                    entry,
                    tariff,
                    fixed_time_charging={"enabled": True, "start": "03:00"},
                ),
                0.2,
            )
            assert response["success"], response
            assert response["result"]["fixed_time_charging"] == {
                "enabled": True,
                "start": "03:00:00",
            }
            assert response["result"]["automation_enabled"] is True
            assert coordinator.options == entry.options
            assert coordinator.options[CONF_ECONOMICS_TARIFF_TYPE] == "dynamic"
            task = coordinator._month_control_task
            assert task is not None and not task.done()
            if periodic:
                assert writer is not None
                assert not writer.cancelling()
                assert not writer.done()
            else:
                assert not coordinator.price_charge_active
        finally:
            finish.set()
        await asyncio.wait_for(task, 1)
    assert not cancelled
    assert coordinator.fixed_time_charge_enabled
    assert coordinator.price_charge_enabled
    assert not coordinator.sun_charge_active
    assert not coordinator.price_charge_active
    assert not coordinator._timed_charge_active
    assert not coordinator._sun_charge_reset_required
    assert coordinator._tariff_control_revision == coordinator._tariff_source_revision
    writes = [
        (call.kwargs["address"], call.kwargs["value"])
        for call in coordinator.client.write_register.await_args_list
    ]
    assert writes[0] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT)
    assert writes[-1] == (REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER)


async def test_rejected_reset_preserves_fixed_start_and_retries_on_poll(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Ein Gerätefehler verliert keine bestätigte Zeit."""
    entry = _prepare(hass, coordinator, "dynamic")
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    started, finish = asyncio.Event(), asyncio.Event()
    success = coordinator.client.write_register.return_value

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == REG_SUN_IC_POWER_SETPOINT_PCT:
            started.set()
            await finish.wait()
        if address == REG_SUN_IC_CONTROL_MODE and value == 0:
            raise ModbusException("fixed-start reset rejected")
        return success

    coordinator.client.write_register.side_effect = write
    with _control_clock():
        assert (await _toggle(client, entry, tariff, True))["success"]
        try:
            await asyncio.wait_for(started.wait(), 1)
            response = await asyncio.wait_for(
                _configure(
                    client,
                    entry,
                    tariff,
                    fixed_time_charging={"enabled": True, "start": "03:00"},
                ),
                0.2,
            )
            assert response["success"], response
            task = coordinator._month_control_task
        finally:
            finish.set()
        await asyncio.wait_for(task, 1)
        assert coordinator._sun_charge_reset_required
        assert not coordinator.sun_charge_active
        assert not coordinator.price_charge_active
        assert coordinator.options == entry.options
        assert (await _get(client, entry))["fixed_time_charging"] == {
            "enabled": True,
            "start": "03:00:00",
        }
        assert coordinator.price_charge_enabled
        coordinator.client.write_register.side_effect = None
        await coordinator._async_enforce_grid_charge(coordinator.data)
    assert not coordinator._sun_charge_reset_required
    coordinator.client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


@pytest.mark.parametrize("tariff_type", ["time_of_use", "dynamic"])
async def test_initial_fixed_selection_accepts_target_below_old_minimum_atomically(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    tariff_type: str,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Erstwahl und Ziel sind ein Softwareauftrag."""
    entry = _prepare(hass, coordinator, tariff_type)
    coordinator._timed_charge_min_soc = 70
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    with _control_clock():
        async with coordinator._charge_control_lock:
            response = await asyncio.wait_for(
                _configure(
                    client,
                    entry,
                    tariff,
                    fixed_time_charging={"enabled": True, "start": "03:00"},
                    charging_settings={"max_soc": 60, "timed_charge_max_soc": 40},
                    automation_enabled=True,
                ),
                0.2,
            )
            assert response["success"], response
            assert response["result"]["fixed_time_charging"] == {
                "enabled": True,
                "start": "03:00:00",
            }
            assert response["result"]["automation_enabled"] is True
            assert coordinator._max_soc == 60
            assert coordinator.timed_charge_max_soc == 40
            assert coordinator.timed_charge_min_soc == 70
            assert coordinator.options == entry.options
            assert coordinator._control_store._pending["max_soc"] == 60
            assert coordinator._control_store._pending["timed_charge_max_soc"] == 40
            assert coordinator.timed_charge_enabled is (tariff_type == "time_of_use")
            assert coordinator.price_charge_enabled is (tariff_type == "dynamic")
            coordinator.client.write_register.assert_not_awaited()
            task = coordinator._month_control_task
        await task
    assert not coordinator.sun_charge_active


@pytest.mark.parametrize(
    "settings",
    [
        None,
        [],
        {},
        {"timed_charge_max_soc": None},
        {"timed_charge_max_soc": True},
        {"timed_charge_max_soc": "40"},
        {"timed_charge_max_soc": -1},
        {"timed_charge_max_soc": 101},
        {"timed_charge_max_soc": 40.5},
        {"max_soc": False},
        {"max_soc": -1},
        {"max_soc": 101},
        {"max_soc": 60, "timed_charge_max_soc": 70},
        {"timed_charge_max_soc": 40, "timed_charge_min_soc": 20},
    ],
)
async def test_invalid_atomic_fixed_settings_roll_back_options_and_control_state(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    settings: Any,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Kein Teil eines ungültigen Entwurfs wird aktiv."""
    entry = _prepare(hass, coordinator, "dynamic")
    coordinator._timed_charge_min_soc = 70
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    before_options = deepcopy(dict(entry.options))
    before_controls = coordinator.control_config()
    response = await _configure(
        client,
        entry,
        tariff,
        fixed_time_charging={"enabled": True, "start": "03:00"},
        charging_settings=settings,
        automation_enabled=True,
    )
    assert response["success"] is False, response
    assert entry.options == coordinator.options == before_options
    assert coordinator.control_config() == before_controls
    assert coordinator._month_control_task is None
    assert coordinator._control_store._pending is None
    coordinator.client.write_register.assert_not_awaited()


@pytest.mark.parametrize("fixed", [None, {"enabled": False, "start": "03:00"}])
async def test_atomic_fixed_settings_require_fixed_mode_in_the_final_snapshot(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    coordinator: SaxPowerCoordinator,
    fixed: dict[str, Any] | None,
) -> None:
    """REQ-FIXED-TIME-GRID-CHARGE: Die atomaren SOC-Werte gehören zum Zeitmodus."""
    entry = _prepare(hass, coordinator, "time_of_use")
    client = await hass_ws_client(hass)
    tariff = await _get(client, entry)
    before_options = deepcopy(dict(entry.options))
    before_controls = coordinator.control_config()
    response = await _configure(
        client,
        entry,
        tariff,
        charging_settings={"timed_charge_max_soc": 40},
        **({"fixed_time_charging": fixed} if fixed is not None else {}),
    )
    assert response["success"] is False, response
    assert entry.options == coordinator.options == before_options
    assert coordinator.control_config() == before_controls
    assert coordinator._month_control_task is None
