"""Reale Dateisystem-Regression für verschluckte Store-Korruption (#150)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.util import dt as dt_util

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.tariff import TariffType
from custom_components.sax_power.infrastructure.economics_store import (
    EconomicsState,
    EconomicsStateStore,
)

FIXED_TARIFF_OPTIONS = {
    CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value,
    CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.30,
}


@pytest.fixture
def hass_storage() -> dict:
    """Deaktiviert für dieses Modul bewusst den üblichen In-Memory-Store."""
    return {}


def _coordinator(hass, entry_id: str) -> SaxPowerCoordinator:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    return SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=entry_id,
        options=FIXED_TARIFF_OPTIONS,
    )


def _full_state(started_at) -> EconomicsState:
    return EconomicsState(
        grid_charge_cost_eur=10.0,
        pv_opportunity_cost_eur=2.0,
        avoided_grid_cost_eur=5.0,
        operating_result_high_water_eur=4.0,
        unvalued_inventory_kwh=3.0,
        unpriced_charge_kwh=1.0,
        unpriced_discharge_kwh=0.5,
        economics_started_at=started_at,
    )


def _remove_test_files(path: Path) -> None:
    path.unlink(missing_ok=True)
    for backup in path.parent.glob(f"{path.name}.corrupt.*"):
        backup.unlink()


async def test_real_malformed_store_stays_frozen_across_reloads(hass) -> None:
    """Core benennt echtes malformed JSON um; kein Reload erzeugt Nullen."""
    entry_id = "issue-150-malformed-json"
    coordinator = _coordinator(hass, entry_id)
    path = Path(coordinator._economics_store._store.path)
    _remove_test_files(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{kein gültiges JSON", encoding="utf-8")

    await coordinator.async_load_economics_state()

    assert coordinator._economics_store_write_blocked is True
    assert coordinator._economics_started_at is None
    assert not path.exists()
    corrupt_backups = list(path.parent.glob(f"{path.name}.corrupt.*"))
    assert len(corrupt_backups) == 1
    assert coordinator._economics_store._unsub_delayed_write is None

    data = {
        "storage_power_active": 0,
        "smartmeter_power": 0,
        "battery_soc": 50,
        "battery_capacity": 10000,
        "battery_soc_min": 5,
    }
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy(data)
    assert data["economics_status"] == "storage_error"
    await coordinator.async_shutdown()
    assert not path.exists()

    reloaded = _coordinator(hass, entry_id)
    await reloaded.async_load_economics_state()

    assert reloaded._economics_store_write_blocked is True
    assert reloaded._economics_started_at is None
    assert not path.exists()
    assert corrupt_backups[0].exists()
    await reloaded.async_shutdown()

    # Ein bewusst zurückgespielter gültiger Store gewinnt trotz des zur
    # Beweissicherung verbleibenden .corrupt-Backups.
    started_at = dt_util.utcnow() - timedelta(days=2)
    assert await EconomicsStateStore(hass, entry_id).async_save(_full_state(started_at))
    restored = _coordinator(hass, entry_id)
    await restored.async_load_economics_state()

    assert restored._economics_store_write_blocked is False
    assert restored._economics_started_at == started_at
    assert restored._economics_grid_charge_cost_eur == 10.0
    await restored.async_shutdown()
    _remove_test_files(path)


async def test_real_missing_store_still_bootstraps_normally(hass) -> None:
    entry_id = "issue-150-genuinely-new"
    coordinator = _coordinator(hass, entry_id)
    path = Path(coordinator._economics_store._store.path)
    _remove_test_files(path)

    await coordinator.async_load_economics_state()
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy(
            {
                "storage_power_active": 0,
                "smartmeter_power": 0,
                "battery_soc": 50,
                "battery_capacity": 10000,
                "battery_soc_min": 5,
            }
        )

    assert coordinator._economics_store_write_blocked is False
    assert coordinator._economics_started_at is not None
    await coordinator.async_shutdown()
    _remove_test_files(path)
