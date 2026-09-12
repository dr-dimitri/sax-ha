"""Neuer HA-Lauf mit gespeichertem Vue-Zustand (REQ-VUE-DASHBOARD)."""

from __future__ import annotations

import hashlib
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_test_home_assistant,
)

from custom_components.sax_power import async_setup_entry, async_unload_entry
from custom_components.sax_power.const import (
    CONF_VUE_DASHBOARD_ENABLED,
    CONF_VUE_DASHBOARD_VERSION,
    DOMAIN,
    ISSUE_VUE_DASHBOARD_UPDATE,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.vue_dashboard import (
    VUE_DASHBOARD_ASSET_URL,
    VUE_DASHBOARD_URL_PATH,
)


@contextmanager
def _setup_boundaries(
    hass: HomeAssistant, entry: ConfigEntry, asset: Path
) -> Generator[AsyncMock]:
    """Gerät und Plattformen isolieren; HA-Storage und Panel bleiben echt."""
    coordinator = MagicMock(spec=SaxPowerCoordinator)
    coordinator.options = dict(entry.options)
    coordinator.price_planner = MagicMock()
    coordinator.price_planner.async_load_cycle_state = AsyncMock()
    coordinator.tariff_provider = MagicMock()
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    coordinator.client = client
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()
    with (
        patch("custom_components.sax_power.AsyncModbusTcpClient", return_value=client),
        patch(
            "custom_components.sax_power.SaxPowerCoordinator", return_value=coordinator
        ),
        patch(
            "custom_components.sax_power.async_check_dashboard_up_to_date",
            new=AsyncMock(),
        ),
        patch.object(
            hass.config_entries, "async_forward_entry_setups", new=AsyncMock()
        ),
        patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.sax_power.vue_dashboard.async_setup_component",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.sax_power.vue_dashboard.VUE_DASHBOARD_ASSET_PATH", asset
        ),
    ):
        yield hass.http.async_register_static_paths
        coordinator.async_apply_price_plan.assert_not_awaited()


@pytest.mark.parametrize(
    ("enabled_after_restart", "bundle_changed"),
    [(True, False), (False, False), (True, True)],
)
async def test_restart_restores_saved_option_and_bundle_confirmation(
    hass_storage: dict[str, Any],
    tmp_path: Path,
    enabled_after_restart: bool,
    bundle_changed: bool,
) -> None:
    """REQ-VUE-DASHBOARD-REPAIR: Neustart lädt Optionen/Hash aus HA-Storage neu."""
    asset = tmp_path / "sax-power-vue.js"
    asset.write_text("// first installed bundle\n")
    original_version = hashlib.sha256(asset.read_bytes()).hexdigest()
    original = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.1.50",
            "slave_id_basic": 64,
            CONF_VUE_DASHBOARD_ENABLED: True,
            CONF_VUE_DASHBOARD_VERSION: "",
        },
        options={CONF_VUE_DASHBOARD_ENABLED: True},
    )
    async with async_test_home_assistant() as first:
        original.add_to_hass(first)
        with _setup_boundaries(first, original, asset) as first_static:
            try:
                assert await async_setup_entry(first, original)
                await first.async_block_till_done()
                first_static.assert_awaited_once()
                first_panel = first.data[frontend.DATA_PANELS][VUE_DASHBOARD_URL_PATH]
                assert original.data[CONF_VUE_DASHBOARD_VERSION] == original_version
                first.config_entries.async_update_entry(
                    original,
                    options={CONF_VUE_DASHBOARD_ENABLED: enabled_after_restart},
                )
                await first.async_block_till_done()
                assert await async_unload_entry(first, original)
            finally:
                # Der reguläre HA-Final-Write serialisiert die verzögerten Änderungen.
                await first.async_stop(force=True)

    saved = hass_storage["core.config_entries"]["data"]["entries"][0]
    assert saved["data"] == dict(original.data)
    assert saved["options"] == dict(original.options)
    if bundle_changed:
        asset.write_text("// snapshot installed while Home Assistant is stopped\n")
    installed_version = hashlib.sha256(asset.read_bytes()).hexdigest()

    async with async_test_home_assistant() as restarted:
        try:
            assert restarted is not first
            assert DOMAIN not in restarted.data
            assert not frontend.async_panel_exists(restarted, VUE_DASHBOARD_URL_PATH)
            await restarted.config_entries.async_initialize()
            restored = restarted.config_entries.async_get_entry(original.entry_id)
            assert restored is not None and restored is not original
            assert dict(restored.data) == saved["data"]
            assert dict(restored.options) == saved["options"]
            with _setup_boundaries(restarted, restored, asset) as restarted_static:
                assert await async_setup_entry(restarted, restored)
                await restarted.async_block_till_done()
                assert (
                    frontend.async_panel_exists(restarted, VUE_DASHBOARD_URL_PATH)
                    is enabled_after_restart
                )
                if enabled_after_restart:
                    restarted_static.assert_awaited_once()
                    panel = restarted.data[frontend.DATA_PANELS][VUE_DASHBOARD_URL_PATH]
                    assert panel is not first_panel
                    assert panel.config["entry_id"] == original.entry_id
                    assert panel.config["_panel_custom"]["module_url"] == (
                        f"{VUE_DASHBOARD_ASSET_URL}?v={installed_version}"
                    )
                else:
                    restarted_static.assert_not_awaited()
                issue = ir.async_get(restarted).async_get_issue(
                    DOMAIN, f"{ISSUE_VUE_DASHBOARD_UPDATE}_{original.entry_id}"
                )
                if bundle_changed:
                    assert issue is not None
                    assert issue.data["version"] == installed_version
                else:
                    assert issue is None
                assert restored.data[CONF_VUE_DASHBOARD_VERSION] == original_version
                assert await async_unload_entry(restarted, restored)
        finally:
            await restarted.async_stop(force=True)
