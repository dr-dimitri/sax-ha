"""Real-file regressions for Core-quarantined control and energy stores."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util

from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.control_store import (
    ControlConfig,
    ControlConfigLoadStatus,
    ControlConfigStore,
)
from custom_components.sax_power.infrastructure.energy_store import (
    EnergyState,
    EnergyStateStore,
)
from custom_components.sax_power.switch import SaxPowerTimedChargeSwitch


@pytest.fixture
def hass_storage() -> dict[str, object]:
    """Use actual Core JSON loading instead of the usual in-memory fixture."""
    return {}


@pytest.fixture(autouse=True)
def isolated_storage(hass: HomeAssistant, tmp_path: Path) -> None:
    """Keep real canonical files and quarantine backups local to each test."""
    hass.config.config_dir = str(tmp_path)


def _coordinator(hass: HomeAssistant, entry_id: str) -> SaxPowerCoordinator:
    client = MagicMock()
    client.connected = True
    return SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=entry_id,
    )


def _write_corrupt_json(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"version":1,"data":', encoding="utf-8")


async def test_quarantined_control_store_never_reopens_legacy_migration(
    hass: HomeAssistant,
) -> None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP: malformed JSON is FAILED after reload too."""
    entry_id = "review-corrupt-control"
    path = Path(ControlConfigStore(hass, entry_id)._store.path)
    _write_corrupt_json(path)

    for _ in range(2):
        coordinator = _coordinator(hass, entry_id)
        await coordinator.async_load_control_state()

        assert coordinator.control_config_status is ControlConfigLoadStatus.FAILED
        assert coordinator.control_config_migration_pending is False
        entity = SaxPowerTimedChargeSwitch(coordinator, entry_id)
        entity.hass = hass
        entity.async_get_last_state = AsyncMock(return_value=State("switch.x", "on"))
        entity.async_write_ha_state = MagicMock()
        await entity.async_added_to_hass()
        assert coordinator.timed_charge_enabled is False
        entity.async_get_last_state.assert_not_awaited()
        await coordinator._async_persist_bootstrap_result()
        coordinator._control_bootstrap_pending = False
        await coordinator.async_shutdown(reset_device=False)
        assert not path.exists()

    assert len(list(path.parent.glob(f"{path.name}.corrupt.*"))) == 1
    await ControlConfigStore(hass, entry_id).async_save(ControlConfig(max_soc=65))
    restored = _coordinator(hass, entry_id)
    await restored.async_load_control_state()
    assert restored.control_config_status is ControlConfigLoadStatus.LOADED
    assert restored.max_soc == 65


async def test_quarantined_energy_store_never_restarts_grid_counters(
    hass: HomeAssistant,
) -> None:
    """REQ-GRID-ENERGY: neither initial load nor reload invents a zero baseline."""
    entry_id = "review-corrupt-energy"
    path = Path(EnergyStateStore(hass, entry_id)._store.path)
    _write_corrupt_json(path)

    for _ in range(2):
        coordinator = _coordinator(hass, entry_id)
        await coordinator.async_load_energy_state()

        assert coordinator._energy_store_write_blocked is True
        assert coordinator._grid_imported_kwh is None
        assert coordinator._grid_exported_kwh is None
        assert coordinator._grid_accounting_started_at is None
        assert coordinator._energy_grid_charged_kwh is None
        assert coordinator._energy_pv_charged_kwh is None

        coordinator.restore_energy_charged(42.0)
        coordinator.restore_energy_discharged(37.0)
        await coordinator._async_flush_energy_state()
        assert coordinator._energy_charged_kwh == 42.0
        assert coordinator._energy_discharged_kwh == 37.0
        assert not path.exists()

    assert len(list(path.parent.glob(f"{path.name}.corrupt.*"))) == 1
    started_at = dt_util.utcnow()
    state = EnergyState(
        charged_kwh=100.0,
        discharged_kwh=90.0,
        grid_charged_kwh=40.0,
        pv_charged_kwh=60.0,
        origin_accounting_started_at=started_at,
        grid_imported_kwh=200.0,
        grid_exported_kwh=300.0,
        grid_accounting_started_at=started_at,
    )
    assert await EnergyStateStore(hass, entry_id).async_save(state)
    restored = _coordinator(hass, entry_id)
    await restored.async_load_energy_state()
    assert restored._energy_store_write_blocked is False
    assert restored._energy_state() == state


async def test_genuinely_missing_control_and_energy_stores_still_bootstrap(
    hass: HomeAssistant,
) -> None:
    """A fresh installation still allows legacy migration and new grid counters."""
    coordinator = _coordinator(hass, "review-missing-stores")
    await coordinator.async_load_control_state()
    await coordinator.async_load_energy_state()

    assert coordinator.control_config_status is ControlConfigLoadStatus.MISSING
    assert coordinator.control_config_migration_pending is True
    assert coordinator._energy_store_write_blocked is False
    assert coordinator._grid_imported_kwh == 0.0
    assert coordinator._grid_exported_kwh == 0.0
    assert coordinator._grid_accounting_started_at is not None
