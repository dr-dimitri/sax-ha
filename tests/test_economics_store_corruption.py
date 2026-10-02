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
from custom_components.sax_power.domain.energy_accounting import EnergyDelta
from custom_components.sax_power.domain.tariff import TariffType
from custom_components.sax_power.infrastructure.economics_store import (
    EconomicsState,
    EconomicsStateStore,
)

from .energy_samples import accumulate_economics_interval

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


async def test_real_malformed_store_continues_and_survives_reload(hass) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: Backup erhalten, automatisch weiterrechnen."""
    entry_id = "continuous-malformed-json"
    coordinator = _coordinator(hass, entry_id)
    path = Path(coordinator._economics_store._store.path)
    _remove_test_files(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    broken = "{kein gültiges JSON"
    path.write_text(broken, encoding="utf-8")

    await coordinator.async_load_economics_state()
    assert coordinator._economics_started_at is None
    corrupt_backups = list(path.parent.glob(f"{path.name}.corrupt.*"))
    assert len(corrupt_backups) == 1
    assert corrupt_backups[0].read_text(encoding="utf-8") == broken

    data = {
        "storage_power_active": -1000,
        "smartmeter_power": 1000,
        "battery_soc": 50,
        "battery_capacity": 10000,
        "battery_soc_min": 5,
    }
    for seconds in (1000.0, 1002.0):
        with patch(
            "custom_components.sax_power.coordinator.monotonic", return_value=seconds
        ):
            accumulate_economics_interval(coordinator, data)
    assert coordinator._economics_started_at is not None
    assert coordinator._economics_grid_charge_cost_eur > 0
    before = coordinator._economics_state()
    await coordinator.async_shutdown()
    assert path.exists()

    reloaded = _coordinator(hass, entry_id)
    await reloaded.async_load_economics_state()
    assert reloaded._economics_storage_error is False
    assert reloaded._economics_state() == before
    assert corrupt_backups[0].read_text(encoding="utf-8") == broken
    await reloaded.async_shutdown()

    # Ein gültiges Backup lässt sich weiterhin ausdrücklich zurückspielen.
    started_at = dt_util.utcnow() - timedelta(days=2)
    assert await EconomicsStateStore(hass, entry_id).async_save(_full_state(started_at))
    restored = _coordinator(hass, entry_id)
    await restored.async_load_economics_state()
    assert restored._economics_started_at == started_at
    assert restored._economics_grid_charge_cost_eur == 10.0
    await restored.async_shutdown()
    _remove_test_files(path)


async def test_corrupt_backup_alone_does_not_prevent_a_new_balance(hass) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: ältere Sperre beim Reload aufheben."""
    entry_id = "continuous-old-quarantine"
    coordinator = _coordinator(hass, entry_id)
    path = Path(coordinator._economics_store._store.path)
    _remove_test_files(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(f"{path.name}.corrupt.old")
    backup.write_text("unlesbar", encoding="utf-8")
    await coordinator.async_load_economics_state()
    coordinator._accumulate_economics({}, None, 0.0, 0.0)
    assert coordinator._economics_started_at is not None
    await coordinator.async_shutdown()
    assert path.exists()
    assert backup.read_text(encoding="utf-8") == "unlesbar"
    _remove_test_files(path)


async def test_load_exception_preserves_original_before_replacement(hass) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: auch unbekannte Versionen sichern."""
    entry_id = "continuous-incompatible"
    coordinator = _coordinator(hass, entry_id)
    path = Path(coordinator._economics_store._store.path)
    _remove_test_files(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    original = '{"version": 999, "key": "unknown", "data": {"valuable": 10}}'
    path.write_text(original, encoding="utf-8")
    await coordinator.async_load_economics_state()
    assert coordinator._economics_storage_error is True
    coordinator._accumulate_economics({}, None, 0.0, 0.0)
    await coordinator.async_shutdown()
    backups = list(path.parent.glob(f"{path.name}.corrupt.*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == original
    assert coordinator._economics_storage_error is False
    loaded = await EconomicsStateStore(hass, entry_id).async_load()
    assert loaded.initialized
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
        accumulate_economics_interval(
            coordinator,
            {
                "storage_power_active": 0,
                "smartmeter_power": 0,
                "battery_soc": 50,
                "battery_capacity": 10000,
                "battery_soc_min": 5,
            },
        )

    assert coordinator._economics_storage_error is False
    assert coordinator._economics_started_at is not None
    await coordinator.async_shutdown()
    _remove_test_files(path)


async def test_failed_backup_does_not_stop_accounting_or_overwrite_original(
    hass,
) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: Sicherungsfehler später erneut versuchen."""
    entry_id = "continuous-backup-failure"
    coordinator = _coordinator(hass, entry_id)
    path = Path(coordinator._economics_store._store.path)
    _remove_test_files(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    original = '{"version": 999, "key": "unknown", "data": {"valuable": 10}}'
    path.write_text(original, encoding="utf-8")
    await coordinator.async_load_economics_state()
    coordinator._accumulate_economics({}, None, 0.0, 0.0)
    before = coordinator._economics_state()
    with patch(
        "custom_components.sax_power.infrastructure.economics_store."
        "_preserve_unreadable_store",
        side_effect=OSError("Sicherung fehlgeschlagen"),
    ):
        await coordinator._economics_store._async_delayed_write(dt_util.utcnow())
    assert path.read_text(encoding="utf-8") == original
    assert coordinator._economics_state() == before
    assert coordinator._economics_store._pending is not None
    assert coordinator._economics_storage_error is True
    now = dt_util.now()
    for seconds in (0, 2):
        with patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=now + timedelta(seconds=seconds),
        ):
            coordinator._accumulate_economics({}, EnergyDelta(1.0, 1.0, 0.0), 0.0, 2.0)
    assert coordinator._economics_grid_charge_cost_eur > before.grid_charge_cost_eur
    await coordinator._economics_store._async_delayed_write(dt_util.utcnow())
    assert coordinator._economics_storage_error is False
    backups = list(path.parent.glob(f"{path.name}.corrupt.*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == original
    await coordinator.async_shutdown()
    _remove_test_files(path)
