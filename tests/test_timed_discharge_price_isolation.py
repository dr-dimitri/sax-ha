"""REQ-TIMED-SOC-CHARGE: Preisstrategien behalten ihre eigene Entladelogik."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from time import monotonic
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.sax_power.application.timed_discharge import TimedDischargeState
from custom_components.sax_power.const import (
    PRICE_STATUS_CHARGING,
    PRICE_STATUS_PAUSED_MAX_SOC,
    PRICE_STATUS_PAUSED_NEUTRAL_BAND,
    PRICE_STATUS_PAUSED_PV_SURPLUS,
    PRICE_STATUS_PAUSED_TIMED_CHARGE,
    PRICE_STATUS_WAITING,
    PRICE_STRATEGY_ABSOLUTE,
    PRICE_STRATEGY_RELATIVE,
    PRICE_STRATEGY_SMART,
    PV_SURPLUS_HYSTERESIS_CYCLES,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.registers import to_unsigned16
from custom_components.sax_power.price_optimizer import PricePlan, PriceSlot

NOW = datetime(2026, 9, 5, 12, tzinfo=UTC)
STRATEGIES = (PRICE_STRATEGY_ABSOLUTE, PRICE_STRATEGY_RELATIVE, PRICE_STRATEGY_SMART)


def _charging_plan() -> PricePlan:
    slot = PriceSlot(start=NOW, end=NOW + timedelta(hours=1), price=0.10)
    return PricePlan(
        status=PRICE_STATUS_CHARGING,
        charge_now=True,
        slots=(slot,),
        current_price=slot.price,
        threshold=slot.price,
    )


def _fresh_grid_sample(coordinator: SaxPowerCoordinator) -> None:
    coordinator._high_sample_started_at = monotonic()
    coordinator._high_sample_revision += 1
    coordinator._high_sample_time = monotonic()
    coordinator._high_data = {
        "storage_power_active": -1000,
        "smartmeter_power": 1200,
    }
    coordinator.data.update(coordinator._high_data)


@pytest.fixture
async def timed_hold(
    hass: HomeAssistant,
) -> AsyncIterator[tuple[SaxPowerCoordinator, MagicMock]]:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    result = MagicMock()
    result.isError.return_value = False
    client.write_register = AsyncMock(return_value=result)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="price_isolation",
    )
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(10)
    coordinator._timed_charge_end = dt_time(14)
    coordinator._timed_charge_min_soc = 50
    coordinator._timed_charge_max_soc = 60
    coordinator._max_soc = 80
    coordinator._price_charge_max_price = 0.20
    coordinator._price_charge_neutral_price = 0.40
    coordinator.data = {
        "soc": 70,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "storage_power_active": 0,
        "smartmeter_power": 0,
    }
    with (
        patch("custom_components.sax_power.coordinator.dt_util.now", return_value=NOW),
        patch(
            "custom_components.sax_power.coordinator.dt_util.utcnow", return_value=NOW
        ),
    ):
        await coordinator._async_set_timed_discharge_state(
            TimedDischargeState(expires_at=NOW + timedelta(hours=2))
        )
        await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator._sun_charge_timed_discharge is True
        assert coordinator._timed_charge_discharge_status == "discharge_blocked"
        client.write_register.reset_mock()
        try:
            yield coordinator, client
        finally:
            await coordinator.async_shutdown()


async def _enable_price(
    coordinator: SaxPowerCoordinator, strategy: str, plan: PricePlan
) -> None:
    coordinator._price_charge_strategy = strategy
    coordinator.price_planner.plan = plan
    with patch.object(coordinator.price_planner, "evaluate", return_value=plan):
        assert await coordinator.async_set_price_charge_enabled(True, force=True)
    assert coordinator.timed_charge_enabled is False
    assert coordinator._timed_discharge_state is None
    assert await coordinator._timed_discharge_store.async_load() is None
    assert coordinator._sun_charge_timed_discharge is False
    assert coordinator.data["timed_charge_discharge_status"] == "normal"


@pytest.mark.parametrize("strategy", STRATEGIES)
async def test_price_charge_replaces_timed_hold_and_never_records_grid_proof(
    timed_hold, strategy: str
) -> None:
    """Alle Preisstrategien laden trotz früherer Sperre bis zum globalen Ziel."""
    coordinator, client = timed_hold

    await _enable_price(coordinator, strategy, _charging_plan())

    assert coordinator.price_charge_active is True
    assert coordinator.price_charge_status == PRICE_STATUS_CHARGING
    assert client.write_register.await_args_list == [
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        ),
        call(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=to_unsigned16(-10000),
            device_id=100,
        ),
    ]
    for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES + 1):
        _fresh_grid_sample(coordinator)
        await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator._timed_discharge_state is None
        assert coordinator._timed_charge_grid_measured is False
        assert coordinator._timed_charge_confirmation_cycles == 0
        assert coordinator.price_charge_active is True


@pytest.mark.parametrize("release", ["neutral_price", "pv_surplus"])
async def test_price_neutral_band_uses_its_own_release_conditions(
    timed_hold, release: str
) -> None:
    """Die Neutralpreiszone darf vor Ablauf der früheren Netzladesperre enden."""
    coordinator, client = timed_hold
    plan = PricePlan(status=PRICE_STATUS_WAITING, charge_now=False, current_price=0.30)
    await _enable_price(coordinator, PRICE_STRATEGY_ABSOLUTE, plan)
    assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_NEUTRAL_BAND
    assert coordinator.sun_charge_active is True
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_POWER_SETPOINT_PCT, value=0, device_id=100
    )
    client.write_register.reset_mock()
    if release == "neutral_price":
        coordinator.price_planner.plan = PricePlan(
            status=PRICE_STATUS_WAITING, charge_now=False, current_price=0.45
        )
        expected_status = PRICE_STATUS_WAITING
    else:
        coordinator.data["smartmeter_power"] = -1000
        expected_status = PRICE_STATUS_PAUSED_PV_SURPLUS

    for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES + 1):
        await coordinator._async_enforce_grid_charge(coordinator.data)

    assert coordinator.price_charge_status == expected_status
    assert coordinator.sun_charge_active is False
    assert coordinator._timed_discharge_state is None
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


@pytest.mark.parametrize("strategy", STRATEGIES)
async def test_price_max_soc_hold_ends_with_price_slot_not_old_timed_window(
    timed_hold, strategy: str
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: Das globale Ziel hält nur den eigenen Preis-Slot."""
    coordinator, client = timed_hold
    await _enable_price(coordinator, strategy, _charging_plan())
    coordinator.data["soc"] = 80
    for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES + 1):
        _fresh_grid_sample(coordinator)
        await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator.max_soc_clamped is True
    assert coordinator._max_soc_hold_is_price_slot_bound is True
    assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_MAX_SOC
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_POWER_SETPOINT_PCT, value=0, device_id=100
    )
    client.write_register.reset_mock()
    coordinator.data["soc"] = 79

    await coordinator._async_enforce_grid_charge(coordinator.data)

    assert coordinator.max_soc_clamped is True
    assert coordinator.price_charge_active is False
    assert coordinator._timed_discharge_state is None
    client.write_register.assert_not_awaited()
    coordinator.price_planner.plan = PricePlan(
        status=PRICE_STATUS_WAITING, charge_now=False, current_price=0.45
    )

    await coordinator._async_enforce_grid_charge(coordinator.data)

    assert coordinator.max_soc_clamped is False
    assert coordinator.sun_charge_active is False
    assert coordinator._max_soc_hold_is_price_slot_bound is False
    assert coordinator.price_charge_status == PRICE_STATUS_WAITING
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_enabled_price_mode_clears_stale_proof_even_with_both_flags_set(
    timed_hold,
) -> None:
    """Ein widersprüchlicher Altzustand erzeugt keine neue Netzladesperre."""
    coordinator, _client = timed_hold
    coordinator._price_charge_enabled = True
    coordinator._price_charge_strategy = PRICE_STRATEGY_RELATIVE
    coordinator.price_planner.plan = _charging_plan()
    coordinator.data["soc"] = 40

    for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES + 2):
        _fresh_grid_sample(coordinator)
        await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator._timed_discharge_state is None
        assert coordinator._timed_charge_grid_measured is False
        assert coordinator._timed_charge_confirmation_cycles == 0

    assert coordinator._timed_charge_active is True
    assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_TIMED_CHARGE
    assert await coordinator._timed_discharge_store.async_load() is None


async def test_disabling_timed_charge_releases_existing_hold_immediately(
    timed_hold,
) -> None:
    """Das Abschalten löscht den Netzladebeleg und quittiert die Nullregelung."""
    coordinator, client = timed_hold

    assert await coordinator.async_set_timed_charge_enabled(False)

    assert coordinator._timed_discharge_state is None
    assert await coordinator._timed_discharge_store.async_load() is None
    assert coordinator.sun_charge_active is False
    assert coordinator.data["timed_charge_discharge_status"] == "normal"
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )
