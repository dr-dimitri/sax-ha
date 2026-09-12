"""Tests für das optionale parallele Panel (REQ-VUE-DASHBOARD)."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components import frontend, websocket_api
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power import (
    _async_rollback_failed_setup,
    async_setup_entry,
    async_unload_entry,
    async_update_options,
)
from custom_components.sax_power.config_flow import STEP_OPTIONS_SCHEMA
from custom_components.sax_power.const import (
    CONF_PV_FORECAST_FACTOR,
    CONF_VUE_DASHBOARD_ENABLED,
    DATA_COORDINATOR,
    DOMAIN,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.dashboard_api import SUBSCRIBE_COMMAND
from custom_components.sax_power.vue_dashboard import (
    VUE_DASHBOARD_ASSET_URL,
    VUE_DASHBOARD_ELEMENT,
    VUE_DASHBOARD_TITLE,
    VUE_DASHBOARD_URL_PATH,
    async_sync_vue_dashboard,
    async_unload_vue_dashboard,
)

_MODULE = "custom_components.sax_power.vue_dashboard"


@pytest.fixture
def vue_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.50", "slave_id_basic": 64},
        options={CONF_VUE_DASHBOARD_ENABLED: True},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def panel_environment(
    hass: HomeAssistant, tmp_path: Path
) -> Generator[tuple[AsyncMock, Path]]:
    asset = tmp_path / "sax-power-vue.js"
    asset.write_text("customElements.define('sax-power-vue-panel', class {});\n")
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()
    with (
        patch(f"{_MODULE}.async_setup_component", new=AsyncMock(return_value=True)),
        patch(f"{_MODULE}.VUE_DASHBOARD_ASSET_PATH", asset),
    ):
        yield hass.http.async_register_static_paths, asset


def _panel(hass: HomeAssistant) -> frontend.Panel:
    return hass.data[frontend.DATA_PANELS][VUE_DASHBOARD_URL_PATH]


async def test_panel_is_opt_in(hass: HomeAssistant) -> None:
    """Bestandsinstallationen legen weder Panel noch HTTP-Route an."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    with patch(f"{_MODULE}.async_setup_component") as setup:
        assert await async_sync_vue_dashboard(hass, entry)
    setup.assert_not_called()
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)


async def test_panel_uses_local_hashed_module_and_preserves_lovelace(
    hass: HomeAssistant, vue_entry: MockConfigEntry, panel_environment
) -> None:
    """Vue erhält einen separaten Einstieg; die Lovelace-Konfiguration bleibt gleich."""
    register_static, asset = panel_environment
    frontend.async_register_built_in_panel(
        hass,
        "lovelace",
        frontend_url_path="sax-power",
        config={"mode": "storage", "url_path": "sax-power"},
    )
    lovelace = hass.data[frontend.DATA_PANELS]["sax-power"]

    assert await async_sync_vue_dashboard(hass, vue_entry)

    panel = _panel(hass)
    assert SUBSCRIBE_COMMAND in hass.data[websocket_api.DOMAIN]
    assert panel.sidebar_title == VUE_DASHBOARD_TITLE
    assert panel.component_name == "custom"
    assert panel.require_admin is False
    assert panel.config["entry_id"] == vue_entry.entry_id
    custom = panel.config["_panel_custom"]
    assert custom["name"] == VUE_DASHBOARD_ELEMENT
    assert custom["embed_iframe"] is False
    assert custom["trust_external"] is False
    version = hashlib.sha256(asset.read_bytes()).hexdigest()
    assert custom["module_url"] == f"{VUE_DASHBOARD_ASSET_URL}?v={version}"
    register_static.assert_awaited_once()
    static_config = register_static.call_args.args[0][0]
    assert static_config.url_path == VUE_DASHBOARD_ASSET_URL
    assert static_config.path == str(asset)
    assert static_config.cache_headers is True
    assert hass.data[frontend.DATA_PANELS]["sax-power"] is lovelace

    await async_unload_vue_dashboard(hass, vue_entry)
    assert hass.data[frontend.DATA_PANELS]["sax-power"] is lovelace


async def test_panel_lifecycle_does_not_duplicate_static_routes(
    hass: HomeAssistant, vue_entry: MockConfigEntry, panel_environment
) -> None:
    """Setup, parallele Updates und Reloads hinterlassen genau eine statische Route."""
    register_static, _ = panel_environment
    assert all(
        await asyncio.gather(
            async_sync_vue_dashboard(hass, vue_entry),
            async_sync_vue_dashboard(hass, vue_entry),
        )
    )
    first_panel = _panel(hass)
    assert await async_sync_vue_dashboard(hass, vue_entry)
    assert _panel(hass) is first_panel
    await async_unload_vue_dashboard(hass, vue_entry)
    await async_unload_vue_dashboard(hass, vue_entry)
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    assert await async_sync_vue_dashboard(hass, vue_entry)
    assert _panel(hass) is not first_panel
    register_static.assert_awaited_once()


async def test_options_override_persisted_onboarding_setting(
    hass: HomeAssistant, panel_environment
) -> None:
    """Das Onboarding-Flag bleibt dauerhaft; spätere Optionen haben Vorrang."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_VUE_DASHBOARD_ENABLED: True})
    entry.add_to_hass(hass)
    assert await async_sync_vue_dashboard(hass, entry)
    assert frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    assert entry.data[CONF_VUE_DASHBOARD_ENABLED] is True

    hass.config_entries.async_update_entry(
        entry, options={CONF_VUE_DASHBOARD_ENABLED: False}
    )
    assert await async_sync_vue_dashboard(hass, entry)
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    hass.config_entries.async_update_entry(
        entry, options={CONF_VUE_DASHBOARD_ENABLED: True}
    )
    assert await async_sync_vue_dashboard(hass, entry)
    assert frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    panel_environment[0].assert_awaited_once()


async def test_queued_option_updates_use_last_saved_value(
    hass: HomeAssistant, vue_entry: MockConfigEntry, panel_environment
) -> None:
    """Schnelles Aus-/Einschalten beim Setup hinterlässt das gewünschte Panel."""
    setup_started = asyncio.Event()
    finish_setup = asyncio.Event()

    async def delayed_setup(*args: object) -> bool:
        setup_started.set()
        await finish_setup.wait()
        return True

    with patch(f"{_MODULE}.async_setup_component", side_effect=delayed_setup):
        initial = asyncio.create_task(async_sync_vue_dashboard(hass, vue_entry))
        await setup_started.wait()
        hass.config_entries.async_update_entry(
            vue_entry, options={CONF_VUE_DASHBOARD_ENABLED: False}
        )
        disable = asyncio.create_task(async_sync_vue_dashboard(hass, vue_entry))
        await asyncio.sleep(0)
        hass.config_entries.async_update_entry(
            vue_entry, options={CONF_VUE_DASHBOARD_ENABLED: True}
        )
        finish_setup.set()
        assert all(await asyncio.gather(initial, disable))
    assert frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    panel_environment[0].assert_awaited_once()


async def test_panel_removal_failure_can_be_retried_without_breaking_unload(
    hass: HomeAssistant, vue_entry: MockConfigEntry, panel_environment
) -> None:
    """REQ-VUE-DASHBOARD: UI-Abmeldung darf Geräte-Cleanup nicht unterbrechen."""
    assert await async_sync_vue_dashboard(hass, vue_entry)
    hass.config_entries.async_update_entry(
        vue_entry, options={CONF_VUE_DASHBOARD_ENABLED: False}
    )
    with patch(
        f"{_MODULE}.frontend.async_remove_panel", side_effect=RuntimeError("frontend")
    ):
        assert not await async_sync_vue_dashboard(hass, vue_entry)
        await async_unload_vue_dashboard(hass, vue_entry)

    assert frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    await async_unload_vue_dashboard(hass, vue_entry)
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)


async def test_reload_uses_new_hash_after_bundle_change(
    hass: HomeAssistant, vue_entry: MockConfigEntry, panel_environment
) -> None:
    """Auch Snapshots mit gleicher Manifest-Version erneuern den Modul-Cache."""
    register_static, asset = panel_environment
    assert await async_sync_vue_dashboard(hass, vue_entry)
    old_url = _panel(hass).config["_panel_custom"]["module_url"]
    await async_unload_vue_dashboard(hass, vue_entry)
    await hass.async_add_executor_job(asset.write_text, "// newer bundle\n")
    assert await async_sync_vue_dashboard(hass, vue_entry)
    assert _panel(hass).config["_panel_custom"]["module_url"] != old_url
    register_static.assert_awaited_once()


async def test_foreign_panel_is_neither_overwritten_nor_removed(
    hass: HomeAssistant, vue_entry: MockConfigEntry, panel_environment, caplog
) -> None:
    """Ein bereits belegter URL-Pfad bleibt Eigentum seines ursprünglichen Panels."""
    frontend.async_register_built_in_panel(
        hass, "map", frontend_url_path=VUE_DASHBOARD_URL_PATH
    )
    foreign = _panel(hass)
    assert not await async_sync_vue_dashboard(hass, vue_entry)
    await async_unload_vue_dashboard(hass, vue_entry)
    assert _panel(hass) is foreign
    panel_environment[0].assert_not_awaited()
    assert "bereits belegt" in caplog.text


async def test_unload_preserves_replacement_or_other_entry_panel(
    hass: HomeAssistant, vue_entry: MockConfigEntry, panel_environment
) -> None:
    """Unload entfernt weder fremde Entries noch ein extern ersetztes Panel."""
    assert await async_sync_vue_dashboard(hass, vue_entry)
    other_entry = MockConfigEntry(domain=DOMAIN, data={})
    await async_unload_vue_dashboard(hass, other_entry)
    assert frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    frontend.async_register_built_in_panel(
        hass, "map", frontend_url_path=VUE_DASHBOARD_URL_PATH, update=True
    )
    foreign = _panel(hass)
    await async_unload_vue_dashboard(hass, vue_entry)
    assert _panel(hass) is foreign


@pytest.mark.parametrize("failure", ["asset", "frontend", "static", "panel"])
async def test_optional_failure_can_be_retried(
    hass: HomeAssistant,
    vue_entry: MockConfigEntry,
    panel_environment,
    failure: str,
    caplog,
) -> None:
    """Fehlende Assets und Frontendfehler verhindern die Batterie-Integration nicht."""
    register_static, _ = panel_environment
    targets = {
        "asset": (f"{_MODULE}._asset_version", OSError("missing bundle")),
        "frontend": (f"{_MODULE}.async_setup_component", None),
        "panel": (
            f"{_MODULE}.panel_custom.async_register_panel",
            ValueError("panel failed"),
        ),
    }
    if failure == "static":
        register_static.side_effect = RuntimeError("route failed")
        assert not await async_sync_vue_dashboard(hass, vue_entry)
        register_static.side_effect = None
    else:
        target, error = targets[failure]
        with patch(target, side_effect=error, return_value=False):
            assert not await async_sync_vue_dashboard(hass, vue_entry)
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    assert "Vue-Dashboard" in caplog.text
    assert await async_sync_vue_dashboard(hass, vue_entry)
    assert frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    assert register_static.await_count == (2 if failure == "static" else 1)


async def test_ui_option_changes_do_not_reapply_charging_policy(
    hass: HomeAssistant, vue_entry: MockConfigEntry, panel_environment
) -> None:
    """Reine UI-Änderungen verändern keine Tarifrevision oder Ladesteuerung."""
    coordinator = MagicMock()
    coordinator.options = {}
    coordinator.async_apply_price_plan = AsyncMock()
    hass.data[DOMAIN] = {vue_entry.entry_id: {DATA_COORDINATOR: coordinator}}

    await async_update_options(hass, vue_entry)
    assert frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    hass.config_entries.async_update_entry(
        vue_entry, options={CONF_VUE_DASHBOARD_ENABLED: False}
    )
    await async_update_options(hass, vue_entry)
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    assert coordinator.options == {CONF_VUE_DASHBOARD_ENABLED: False}
    coordinator.async_apply_price_plan.assert_not_awaited()
    coordinator.notify_tariff_revision.assert_not_called()
    coordinator.price_planner.async_setup.assert_not_called()
    coordinator.tariff_provider.async_setup.assert_not_called()


async def test_first_options_save_does_not_apply_newly_explicit_defaults(
    hass: HomeAssistant, vue_entry: MockConfigEntry, panel_environment
) -> None:
    """Vom Options-Schema ergänzte Defaults sind keine Änderung der Ladesteuerung."""
    coordinator = MagicMock()
    coordinator.options = {}
    coordinator.async_apply_price_plan = AsyncMock()
    hass.data[DOMAIN] = {vue_entry.entry_id: {DATA_COORDINATOR: coordinator}}
    options = STEP_OPTIONS_SCHEMA({CONF_VUE_DASHBOARD_ENABLED: True})
    hass.config_entries.async_update_entry(vue_entry, options=options)
    await async_update_options(hass, vue_entry)
    assert frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    assert coordinator.options == options
    coordinator.async_apply_price_plan.assert_not_awaited()
    coordinator.notify_tariff_revision.assert_not_called()

    # Ein abweichender Prognosefaktor bleibt eine echte Steuerungsänderung.
    hass.config_entries.async_update_entry(
        vue_entry, options={**options, CONF_PV_FORECAST_FACTOR: 50}
    )
    await async_update_options(hass, vue_entry)
    coordinator.async_apply_price_plan.assert_awaited_once()
    coordinator.notify_tariff_revision.assert_called_once()


@pytest.mark.parametrize("missing_asset", [False, True])
async def test_integration_setup_and_unload_manage_optional_panel(
    hass: HomeAssistant,
    vue_entry: MockConfigEntry,
    panel_environment,
    missing_asset: bool,
) -> None:
    """Ein Frontendfehler lässt Setup, Bootstrap und regulären Unload funktionsfähig."""
    coordinator = MagicMock(spec=SaxPowerCoordinator)
    coordinator.price_planner = MagicMock()
    coordinator.price_planner.async_load_cycle_state = AsyncMock()
    coordinator.tariff_provider = MagicMock()
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    coordinator.client = client
    if missing_asset:
        await hass.async_add_executor_job(panel_environment[1].unlink)
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
        ) as unload_platforms,
    ):
        assert await async_setup_entry(hass, vue_entry)
        coordinator.async_finish_bootstrap.assert_awaited_once()
        assert (
            frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
            is not missing_asset
        )
        unload_platforms.return_value = False
        assert not await async_unload_entry(hass, vue_entry)
        coordinator.async_shutdown.assert_not_awaited()
        assert (
            frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
            is not missing_asset
        )
        unload_platforms.return_value = True
        assert await async_unload_entry(hass, vue_entry)
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    coordinator.async_shutdown.assert_awaited_once()
    client.close.assert_called_once()


@pytest.mark.parametrize("cleanup_error", [False, True])
async def test_setup_rollback_cleans_panel_and_preserves_device_cleanup(
    hass: HomeAssistant,
    vue_entry: MockConfigEntry,
    panel_environment,
    cleanup_error: bool,
) -> None:
    """Ein Setup-Rollback beendet Panel und Client, auch bei einem UI-Cleanup-Fehler."""
    assert await async_sync_vue_dashboard(hass, vue_entry)
    client = MagicMock()
    coordinator = MagicMock(spec=SaxPowerCoordinator)
    hass.data[DOMAIN] = {vue_entry.entry_id: {DATA_COORDINATOR: coordinator}}
    with patch(
        "custom_components.sax_power.async_unload_vue_dashboard",
        wraps=async_unload_vue_dashboard,
        side_effect=RuntimeError("UI cleanup failed") if cleanup_error else None,
    ):
        await _async_rollback_failed_setup(
            hass, vue_entry, client, coordinator, platforms_started=False
        )
    assert frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH) is cleanup_error
    coordinator.async_shutdown.assert_awaited_once_with(reset_device=False)
    client.close.assert_called_once()
    assert vue_entry.entry_id not in hass.data[DOMAIN]
    await async_unload_vue_dashboard(hass, vue_entry)
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)


async def test_static_module_is_served_by_home_assistant(
    hass: HomeAssistant, vue_entry: MockConfigEntry, hass_client
) -> None:
    """Die echte HA-HTTP-Route liefert das eingecheckte Modul unter seiner Cache-URL."""
    assert await async_sync_vue_dashboard(hass, vue_entry)
    client = await hass_client()
    response = await client.get(_panel(hass).config["_panel_custom"]["module_url"])
    assert response.status == 200
    assert "javascript" in response.headers["Content-Type"]
    assert "max-age" in response.headers["Cache-Control"]
    assert VUE_DASHBOARD_ELEMENT in await response.text()
    response = await client.get("/sax_power/frontend/vue_dashboard.py")
    assert response.status == 404
