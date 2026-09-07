"""Coordinator and polling regressions for REQ-GRID-ENERGY."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.sax_power.const import (
    READ_BLOCK_EXT_START,
    REG_SOC,
    REG_SUN_METER_POWER_ACTIVE_SF,
    REG_SUN_METER_POWER_ACTIVE_SUM,
    REG_SUN_STORAGE_POWER_ACTIVE,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.energy_store import (
    STORAGE_KEY_PREFIX,
    EnergyStateStore,
)

_CLOCK = "custom_components.sax_power.coordinator.monotonic"


def _make_coordinator(hass: HomeAssistant) -> SaxPowerCoordinator:
    client = MagicMock()
    client.connected = True
    return SaxPowerCoordinator(hass, client, 64, 100, 10, "grid-test")


@pytest.fixture
async def coordinator(hass: HomeAssistant) -> AsyncIterator[SaxPowerCoordinator]:
    instance = _make_coordinator(hass)
    await instance.async_load_energy_state()
    yield instance
    await instance.async_shutdown()


def _sample(
    coordinator: SaxPowerCoordinator, time: float, power: Any
) -> dict[str, Any]:
    coordinator._high_sample_revision += 1
    coordinator._high_sample_time = time
    coordinator._high_data = {"smartmeter_power": power}
    data: dict[str, Any] = {}
    with patch(_CLOCK, return_value=time):
        coordinator._accumulate_grid_energy(data)
    return data


@pytest.mark.parametrize("power, expected", [(1000, (1, 0)), (-1000, (0, 1))])
async def test_one_hour_counts_only_the_matching_grid_direction(
    coordinator: SaxPowerCoordinator, power: float, expected: tuple[float, float]
) -> None:
    """REQ-GRID-ENERGY: 1000 W for a measured hour yields 1 kWh without battery."""
    for time in range(0, 3601, 2):
        data = _sample(coordinator, time, power)
    assert (
        data["energy_imported_from_grid"],
        data["energy_exported_to_grid"],
    ) == expected
    assert coordinator._energy_charged_kwh is None
    assert coordinator._energy_discharged_kwh is None
    assert data["grid_energy_attributes"]["accounting_started_at"] is not None


async def test_direction_changes_use_previous_sample_and_zero_preserves_totals(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-GRID-ENERGY: Left Riemann integration never nets import against export."""
    assert _sample(coordinator, 0, 1800)["energy_imported_from_grid"] == 0
    data = _sample(coordinator, 2, -3600)
    assert data["energy_imported_from_grid"] == 0.001
    assert data["energy_exported_to_grid"] == 0
    data = _sample(coordinator, 4, 0)
    assert data["energy_exported_to_grid"] == 0.002
    data = _sample(coordinator, 6, 0)
    assert data["energy_imported_from_grid"] == 0.001
    assert data["energy_exported_to_grid"] == 0.002


@pytest.mark.parametrize("invalid", [None, float("nan"), float("inf"), True, "1800"])
async def test_invalid_grid_sample_breaks_the_interval(
    coordinator: SaxPowerCoordinator, invalid: Any
) -> None:
    """REQ-GRID-ENERGY: Both endpoints must be valid; recovery does not backfill."""
    _sample(coordinator, 0, 1800)
    _sample(coordinator, 2, invalid)
    assert _sample(coordinator, 4, 1800)["energy_imported_from_grid"] == 0
    assert _sample(coordinator, 6, 1800)["energy_imported_from_grid"] == 0.001


async def test_cached_refresh_does_not_double_count_or_extend_sample_time(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-GRID-ENERGY: Entity/service refreshes use a cached HIGH sample."""
    _sample(coordinator, 0, 1800)
    data: dict[str, Any] = {}
    with patch(_CLOCK, return_value=1):
        coordinator._accumulate_grid_energy(data)
        coordinator._accumulate_grid_energy(data)
    assert data["energy_imported_from_grid"] == 0
    assert _sample(coordinator, 2, 1800)["energy_imported_from_grid"] == 0.001


@pytest.mark.parametrize("gap", [4.01, 3600])
async def test_long_gap_starts_a_new_baseline(
    coordinator: SaxPowerCoordinator, gap: float
) -> None:
    """REQ-GRID-ENERGY: Suspended polling is not a measured interval."""
    _sample(coordinator, 0, 1800)
    assert _sample(coordinator, gap, 1800)["energy_imported_from_grid"] == 0
    assert _sample(coordinator, gap + 2, 1800)["energy_imported_from_grid"] == 0.001


async def test_stale_cached_sample_cannot_be_reused_as_a_baseline(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-GRID-ENERGY: Invalidating stale data precedes the revision guard."""
    _sample(coordinator, 0, 1800)
    with patch(_CLOCK, return_value=5):
        coordinator._accumulate_grid_energy({})
    assert coordinator._grid_energy_last_sample is None
    assert _sample(coordinator, 6, 1800)["energy_imported_from_grid"] == 0
    assert _sample(coordinator, 8, 1800)["energy_imported_from_grid"] == 0.001


async def test_shutdown_and_restart_restore_grid_totals_without_battery_baseline(
    hass: HomeAssistant,
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-GRID-ENERGY: Reload preserves exact totals, never counts offline time."""
    _sample(coordinator, 0, 1800)
    _sample(coordinator, 2, -3600)
    _sample(coordinator, 4, 0)
    started_at = coordinator._grid_accounting_started_at
    await coordinator.async_shutdown()
    stored = await EnergyStateStore(hass, coordinator.entry_id).async_load()
    assert stored is not None
    assert stored.grid_imported_kwh == pytest.approx(0.001)
    assert stored.grid_exported_kwh == pytest.approx(0.002)
    restarted = _make_coordinator(hass)
    await restarted.async_load_energy_state()
    try:
        data = _sample(restarted, 3600, 1800)
        assert data["energy_imported_from_grid"] == 0.001
        assert data["energy_exported_to_grid"] == 0.002
        assert restarted._grid_accounting_started_at == started_at
        data = _sample(restarted, 3602, 1800)
        assert data["energy_imported_from_grid"] == 0.002
    finally:
        await restarted.async_shutdown()


async def test_unreadable_store_cannot_be_overwritten_by_battery_restore(
    hass: HomeAssistant,
) -> None:
    """REQ-GRID-ENERGY: Read failure must preserve the unknown disk snapshot."""
    coordinator = _make_coordinator(hass)
    coordinator._energy_store.async_load = AsyncMock(side_effect=OSError("unreadable"))
    coordinator._energy_store.async_delay_save = MagicMock()
    coordinator._energy_store.async_save = AsyncMock()
    await coordinator.async_load_energy_state()
    coordinator.restore_energy_charged(12.5)
    _sample(coordinator, 0, 1800)
    data = _sample(coordinator, 2, 1800)
    assert data["energy_imported_from_grid"] is None
    assert data["energy_exported_to_grid"] is None
    await coordinator.async_shutdown()
    coordinator._energy_store.async_delay_save.assert_not_called()
    coordinator._energy_store.async_save.assert_not_awaited()


@pytest.mark.parametrize("legacy", [True, False])
async def test_bootstrap_migrates_or_repairs_only_the_grid_group(
    hass: HomeAssistant, hass_storage: dict[str, Any], legacy: bool
) -> None:
    """REQ-GRID-ENERGY: Actual bootstrap and flush preserve all pre-existing totals."""
    started = datetime(2025, 1, 1, tzinfo=UTC).isoformat()
    key = f"{STORAGE_KEY_PREFIX}.grid-test"
    payload = {
        "charged_kwh": 50.0,
        "discharged_kwh": 20.0,
        "grid_charged_kwh": 12.0,
        "pv_charged_kwh": 38.0,
        "origin_accounting_started_at": started,
    }
    if not legacy:
        payload.update(
            grid_imported_kwh=-1,
            grid_exported_kwh=25.0,
            grid_accounting_started_at=started,
        )
    hass_storage[key] = {
        "version": 1,
        "minor_version": 3 if legacy else 4,
        "key": key,
        "data": payload,
    }
    coordinator = _make_coordinator(hass)
    await coordinator.async_load_energy_state()
    data = _sample(coordinator, 0, 1800)
    assert data["energy_imported_from_grid"] == 0
    assert data["energy_exported_to_grid"] == 0
    assert data["grid_energy_attributes"]["accounting_started_at"] != started
    await coordinator.async_shutdown()
    restored = await EnergyStateStore(hass, coordinator.entry_id).async_load()
    assert restored is not None
    assert restored.charged_kwh == 50.0
    assert restored.discharged_kwh == 20.0
    assert restored.grid_charged_kwh == 12.0
    assert restored.pv_charged_kwh == 38.0
    assert restored.origin_accounting_started_at.isoformat() == started
    assert restored.grid_imported_kwh == 0.0
    assert restored.grid_exported_kwh == 0.0


@pytest.mark.parametrize("failure", ["basic", "sunspec", "sentinel"])
async def test_wire_decoding_and_poll_failure_recovery(
    coordinator: SaxPowerCoordinator,
    failure: str,
) -> None:
    """REQ-GRID-ENERGY: Actual decoder normalizes sign/SF; outages preserve totals."""
    fail = False

    def read(*, address: int, count: int, device_id: int) -> MagicMock:
        result = MagicMock()
        result.isError.return_value = fail and (
            (failure == "basic" and device_id == 64)
            or (failure == "sunspec" and address == READ_BLOCK_EXT_START)
        )
        registers = [0] * count
        if device_id == 64:
            registers[REG_SOC - address] = 50
        elif address == READ_BLOCK_EXT_START:
            # The meter raw register is positive for export, and uses 10**SF.
            registers[REG_SUN_METER_POWER_ACTIVE_SUM - address] = (
                0x8000 if fail and failure == "sentinel" else 180
            )
            registers[REG_SUN_METER_POWER_ACTIVE_SF - address] = 1
            registers[REG_SUN_STORAGE_POWER_ACTIVE - address] = 0x8000
        result.registers = registers
        return result

    coordinator.client.read_holding_registers = AsyncMock(side_effect=read)
    coordinator._control_bootstrap_pending = True
    with patch(_CLOCK, return_value=0):
        data = await coordinator._async_update_data()
    assert data["smartmeter_power"] == -1800
    assert data["storage_power_active"] is None
    with patch(_CLOCK, return_value=2):
        data = await coordinator._async_update_data()
    assert data["energy_exported_to_grid"] == 0.001
    fail = True
    coordinator._basic_last_read = None
    with patch(_CLOCK, return_value=4):
        if failure == "basic":
            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()
        else:
            data = await coordinator._async_update_data()
            assert data["energy_exported_to_grid"] == 0.001
    assert coordinator._grid_energy_last_sample is None
    fail = False
    with patch(_CLOCK, return_value=6):
        data = await coordinator._async_update_data()
    assert data["energy_exported_to_grid"] == 0.001
    with patch(_CLOCK, return_value=8):
        data = await coordinator._async_update_data()
    assert data["energy_exported_to_grid"] == 0.002
