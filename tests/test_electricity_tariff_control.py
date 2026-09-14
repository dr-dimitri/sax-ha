"""REQ-VUE-ELECTRICITY-TARIFF: tariff choice owns both legacy control paths."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.application.charge_policy import (
    tariff_automation_controls,
)
from custom_components.sax_power.const import (
    CONF_DASHBOARD_TARIFF_PROFILES,
    DOMAIN,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.tariff import TariffType


def _options(kind: str) -> dict[str, Any]:
    return {
        "economics_tariff_type": kind,
        "economics_tou_base_price_eur_kwh": 0.34,
        "economics_feed_in_price_eur_kwh": 0.082,
        "price_sensor": "sensor.electricity",
        "price_unit": "ct/kWh",
    }


@pytest.fixture
async def tariff_coordinator(
    hass: HomeAssistant,
) -> AsyncIterator[tuple[SaxPowerCoordinator, MockConfigEntry]]:
    entry = MockConfigEntry(domain=DOMAIN, options=_options("time_of_use"))
    entry.add_to_hass(hass)
    coordinator = SaxPowerCoordinator(
        hass, MagicMock(), 64, 100, 10, entry.entry_id, options=dict(entry.options)
    )
    coordinator.price_planner.async_setup = MagicMock()
    coordinator.tariff_provider.async_setup = MagicMock()
    coordinator._async_enforce_grid_charge_locked = AsyncMock()
    coordinator.async_write_extended_register = AsyncMock()
    coordinator.data = {"soc": 40}
    yield coordinator, entry
    await coordinator.async_shutdown()


@pytest.mark.parametrize("kind", [TariffType.TIME_OF_USE, TariffType.DYNAMIC])
@pytest.mark.parametrize("enabled", [False, True])
def test_selected_tariff_has_exactly_one_matching_automation(
    kind: TariffType, enabled: bool
) -> None:
    assert tariff_automation_controls(kind, True, True, enabled=enabled) == (
        enabled and kind is TariffType.TIME_OF_USE,
        enabled and kind is TariffType.DYNAMIC,
    )


@pytest.mark.parametrize("enabled", [False, True])
async def test_tariff_switch_preserves_master_and_commits_matching_control(
    tariff_coordinator, hass: HomeAssistant, enabled: bool
) -> None:
    coordinator, entry = tariff_coordinator
    coordinator._timed_charge_enabled = enabled
    await coordinator.async_apply_dashboard_tariff(
        _options("dynamic"), enabled=None, expected_options=dict(entry.options)
    )
    assert entry.options["economics_tariff_type"] == "dynamic"
    assert coordinator.options == entry.options
    assert not coordinator.timed_charge_enabled
    assert coordinator.price_charge_enabled is enabled
    await hass.async_block_till_done()
    coordinator._async_enforce_grid_charge_locked.assert_awaited_once()

    await coordinator.async_apply_dashboard_tariff(
        _options("time_of_use"), enabled=None, expected_options=dict(entry.options)
    )
    assert coordinator.timed_charge_enabled is enabled
    assert not coordinator.price_charge_enabled


async def test_master_off_keeps_tariff_price_and_global_soc(tariff_coordinator) -> None:
    coordinator, entry = tariff_coordinator
    coordinator._timed_charge_enabled = True
    coordinator._max_soc = 87
    await coordinator.async_apply_dashboard_tariff(
        dict(entry.options), enabled=False, expected_options=dict(entry.options)
    )
    assert coordinator.tariff_provider.config.tariff_type is TariffType.TIME_OF_USE
    assert coordinator.tariff_provider.quote().price_eur_kwh == pytest.approx(0.34)
    assert coordinator.max_soc == 87
    assert not coordinator.timed_charge_enabled
    assert not coordinator.price_charge_enabled
    coordinator.price_planner.async_setup.assert_not_called()
    coordinator.tariff_provider.async_setup.assert_not_called()


async def test_saved_inactive_profile_does_not_restart_price_sources(
    tariff_coordinator,
) -> None:
    coordinator, entry = tariff_coordinator
    options = dict(entry.options)
    options[CONF_DASHBOARD_TARIFF_PROFILES] = {
        "dynamic": {"price_sensor": "sensor.new"}
    }
    await coordinator.async_apply_dashboard_tariff(
        options, enabled=None, expected_options=dict(entry.options)
    )
    coordinator.price_planner.async_setup.assert_not_called()
    coordinator.tariff_provider.async_setup.assert_not_called()
    assert coordinator._last_tariff_revision_at is None


async def test_stale_dashboard_save_cannot_change_tariff_or_switches(
    tariff_coordinator, hass: HomeAssistant
) -> None:
    coordinator, entry = tariff_coordinator
    expected = dict(entry.options)
    newer = {**expected, "economics_feed_in_price_eur_kwh": 0.09}
    hass.config_entries.async_update_entry(entry, options=newer)
    with pytest.raises(ServiceValidationError) as error:
        await coordinator.async_apply_dashboard_tariff(
            _options("dynamic"), enabled=True, expected_options=expected
        )
    assert error.value.translation_key == "dashboard_tariff_conflict"
    assert dict(entry.options) == newer
    assert coordinator.options == expected
    assert not coordinator.price_charge_enabled


async def test_queued_options_listener_uses_latest_entry(
    tariff_coordinator, hass
) -> None:
    coordinator, entry = tariff_coordinator
    stale = _options("dynamic")
    newest = {**_options("time_of_use"), "economics_tou_base_price_eur_kwh": 0.45}
    hass.config_entries.async_update_entry(entry, options=newest)
    async with coordinator._charge_control_lock:
        await asyncio.wait_for(coordinator.async_apply_tariff_options(stale), 0.2)
    assert coordinator.options == newest
    assert coordinator.tariff_provider.quote().price_eur_kwh == pytest.approx(0.45)


@pytest.mark.parametrize("kind", ["fixed", "disabled", "time_of_use"])
async def test_incomplete_target_cannot_inherit_an_enabled_legacy_control(
    tariff_coordinator, hass: HomeAssistant, kind: str
) -> None:
    coordinator, entry = tariff_coordinator
    original = _options(kind)
    coordinator.options = original
    hass.config_entries.async_update_entry(entry, options=original)
    coordinator._timed_charge_enabled = True
    target = {"economics_tariff_type": "dynamic"}
    with pytest.raises(ServiceValidationError, match="vollständig"):
        await coordinator.async_apply_dashboard_tariff(
            target, enabled=None, expected_options=original
        )
    assert dict(entry.options) == original
    assert coordinator.options == original
    assert coordinator.timed_charge_enabled
    assert not coordinator.price_charge_enabled
    await coordinator.async_apply_dashboard_tariff(
        target, enabled=False, expected_options=original
    )
    assert dict(entry.options) == target
    assert not coordinator.timed_charge_enabled
    assert not coordinator.price_charge_enabled


async def test_native_master_change_before_acceptance_revalidates_incomplete_target(
    tariff_coordinator,
) -> None:
    coordinator, entry = tariff_coordinator
    await coordinator._charge_control_lock.acquire()
    request = asyncio.create_task(
        coordinator.async_apply_dashboard_tariff(
            {"economics_tariff_type": "dynamic"},
            enabled=None,
            expected_options=dict(entry.options),
        )
    )
    coordinator._timed_charge_enabled = True
    try:
        with pytest.raises(ServiceValidationError, match="vollständig"):
            await asyncio.wait_for(request, 0.2)
    finally:
        coordinator._charge_control_lock.release()
    assert entry.options["economics_tariff_type"] == "time_of_use"
    assert coordinator.timed_charge_enabled
    assert not coordinator.price_charge_enabled


@pytest.mark.parametrize(
    ("kind", "method"),
    [
        ("dynamic", "async_set_timed_charge_enabled"),
        ("time_of_use", "async_set_price_charge_enabled"),
    ],
)
async def test_legacy_switch_cannot_activate_inactive_tariff(
    tariff_coordinator, kind: str, method: str
) -> None:
    coordinator, _entry = tariff_coordinator
    coordinator.options = _options(kind)
    with pytest.raises(ServiceValidationError, match="Stromtarif"):
        await getattr(coordinator, method)(True, force=True, defer_device_update=True)
    assert not coordinator.timed_charge_enabled
    assert not coordinator.price_charge_enabled


async def test_bootstrap_drops_mismatched_legacy_switch_without_starting_another(
    tariff_coordinator,
) -> None:
    coordinator, _entry = tariff_coordinator
    coordinator.options = _options("dynamic")
    coordinator._control_bootstrap_pending = True
    coordinator._timed_charge_enabled = True
    coordinator._async_persist_bootstrap_result = AsyncMock()
    await coordinator.async_finish_bootstrap()
    assert not coordinator.timed_charge_enabled
    assert not coordinator.price_charge_enabled


async def test_tariff_change_cancels_old_writer_only_during_device_reconciliation(
    tariff_coordinator,
) -> None:
    coordinator, entry = tariff_coordinator
    coordinator._async_enforce_grid_charge_locked = (
        SaxPowerCoordinator._async_enforce_grid_charge_locked.__get__(coordinator)
    )
    writer = asyncio.create_task(asyncio.sleep(3600))
    coordinator._sun_charge_task = writer
    async with coordinator._charge_control_lock:
        await coordinator.async_apply_dashboard_tariff(
            _options("dynamic"), enabled=False, expected_options=dict(entry.options)
        )
        assert not writer.cancelling()
        task = coordinator._month_control_task
    await asyncio.wait_for(task, 1)
    assert writer.cancelled()


async def test_bootstrap_cannot_accept_a_partial_dashboard_configuration(
    tariff_coordinator,
) -> None:
    coordinator, entry = tariff_coordinator
    coordinator._control_bootstrap_pending = True
    with pytest.raises(ServiceValidationError, match="geladen"):
        await coordinator.async_apply_dashboard_tariff(
            _options("dynamic"), enabled=True, expected_options=dict(entry.options)
        )
    assert entry.options["economics_tariff_type"] == "time_of_use"
