"""Native Reparaturabläufe und Migration (REQ-VUE-DASHBOARD-REPAIR)."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.components import frontend, repairs
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power import async_update_options
from custom_components.sax_power.const import (
    CONF_VUE_DASHBOARD_DISMISSED_VERSION,
    CONF_VUE_DASHBOARD_ENABLED,
    CONF_VUE_DASHBOARD_VERSION,
    DATA_COORDINATOR,
    DOMAIN,
    ISSUE_VUE_DASHBOARD_UPDATE,
)
from custom_components.sax_power.vue_dashboard import (
    VUE_DASHBOARD_URL_PATH,
    async_finish_vue_dashboard_repair,
    async_sync_vue_dashboard,
    async_unload_vue_dashboard,
)

_MODULE = "custom_components.sax_power.vue_dashboard"


@pytest.fixture
def entry(hass: HomeAssistant) -> MockConfigEntry:
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_VUE_DASHBOARD_VERSION: "previous-snapshot"},
        options={CONF_VUE_DASHBOARD_ENABLED: True},
    )
    config_entry.add_to_hass(hass)
    return config_entry


@pytest.fixture
def assets(hass: HomeAssistant, tmp_path: Path) -> Generator[Path]:
    asset = tmp_path / "panel.js"
    asset.write_text("// current snapshot\n")
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()
    with (
        patch(f"{_MODULE}.async_setup_component", new=AsyncMock(return_value=True)),
        patch(f"{_MODULE}.VUE_DASHBOARD_ASSET_PATH", asset),
    ):
        yield asset


def _version(asset: Path) -> str:
    return hashlib.sha256(asset.read_bytes()).hexdigest()


def _issue(hass: HomeAssistant, entry: MockConfigEntry) -> ir.IssueEntry | None:
    return ir.async_get(hass).async_get_issue(
        DOMAIN, f"{ISSUE_VUE_DASHBOARD_UPDATE}_{entry.entry_id}"
    )


def _panel(hass: HomeAssistant) -> frontend.Panel:
    return hass.data[frontend.DATA_PANELS][VUE_DASHBOARD_URL_PATH]


async def _flow(
    hass: HomeAssistant, entry: MockConfigEntry
) -> tuple[repairs.RepairsFlowManager, str]:
    hass.config.components.add(DOMAIN)
    assert await repairs.async_setup(hass, {})
    manager = repairs.repairs_flow_manager(hass)
    assert manager is not None
    result = await manager.async_init(
        DOMAIN,
        data={"issue_id": f"{ISSUE_VUE_DASHBOARD_UPDATE}_{entry.entry_id}"},
    )
    assert result["type"] == "menu"
    assert result["menu_options"] == ["confirm", "cancel"]
    return manager, result["flow_id"]


async def test_fresh_activation_sets_baseline_without_repair(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path
) -> None:
    """Ein gerade aktiviertes Panel braucht keinen künstlichen Updatehinweis."""
    hass.config_entries.async_update_entry(entry, data={CONF_VUE_DASHBOARD_VERSION: ""})
    assert await async_sync_vue_dashboard(hass, entry)
    assert entry.data[CONF_VUE_DASHBOARD_VERSION] == _version(assets)
    assert _issue(hass, entry) is None


async def test_legacy_snapshot_gets_one_reload_hint_without_claiming_old_server(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path
) -> None:
    """Vor #205 fehlte die Bestätigung; aktuelle URL allein erneuert kein Browser-CE."""
    hass.config_entries.async_update_entry(entry, data={})
    assert await async_sync_vue_dashboard(hass, entry)
    initial_panel = _panel(hass)
    assert _version(assets) in initial_panel.config["_panel_custom"]["module_url"]
    issue = _issue(hass, entry)
    assert issue is not None and issue.is_fixable
    assert issue.data["version"] == _version(assets)
    assert CONF_VUE_DASHBOARD_VERSION not in entry.data
    assert await async_sync_vue_dashboard(hass, entry)
    assert _panel(hass) is initial_panel
    assert _issue(hass, entry).created == issue.created


async def test_native_repair_registers_new_bundle_and_requires_reload_confirmation(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path
) -> None:
    """Snapshot-Hash erneuert die URL; erst der Reload-Schritt quittiert den Stand."""
    assert await async_sync_vue_dashboard(hass, entry)
    old_panel = _panel(hass)
    await hass.async_add_executor_job(
        assets.write_text, "// new bundle, same manifest\n"
    )
    assert await async_sync_vue_dashboard(hass, entry)
    assert _panel(hass) is old_panel
    version = _version(assets)
    assert _issue(hass, entry).data["version"] == version

    manager, flow_id = await _flow(hass, entry)
    result = await manager.async_configure(flow_id, {"next_step_id": "confirm"})
    assert result["type"] == "form" and result["step_id"] == "reload"
    assert _panel(hass) is not old_panel
    assert version in _panel(hass).config["_panel_custom"]["module_url"]
    assert _issue(hass, entry) is not None
    assert entry.data[CONF_VUE_DASHBOARD_VERSION] == "previous-snapshot"
    result = await manager.async_configure(flow_id, {})
    assert result["type"] == "create_entry"
    assert entry.data[CONF_VUE_DASHBOARD_VERSION] == version
    assert _issue(hass, entry) is None
    hass.http.async_register_static_paths.assert_awaited_once()
    await async_unload_vue_dashboard(hass, entry)
    assert await async_sync_vue_dashboard(hass, entry)
    assert _issue(hass, entry) is None


async def test_dismiss_is_persistent_for_this_bundle_only(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path
) -> None:
    """Abbrechen erhält das Panel und meldet einen späteren Snapshot erneut."""
    assert await async_sync_vue_dashboard(hass, entry)
    panel = _panel(hass)
    manager, flow_id = await _flow(hass, entry)
    result = await manager.async_configure(flow_id, {"next_step_id": "cancel"})
    assert result["type"] == "create_entry"
    assert _panel(hass) is panel
    assert entry.data[CONF_VUE_DASHBOARD_DISMISSED_VERSION] == _version(assets)
    assert entry.data[CONF_VUE_DASHBOARD_VERSION] == "previous-snapshot"
    assert _issue(hass, entry) is None
    await async_unload_vue_dashboard(hass, entry)
    assert await async_sync_vue_dashboard(hass, entry)
    assert _issue(hass, entry) is None
    await hass.async_add_executor_job(assets.write_text, "// following snapshot\n")
    assert await async_sync_vue_dashboard(hass, entry)
    assert _issue(hass, entry).data["version"] == _version(assets)


@pytest.mark.parametrize("stage", ["confirm", "reload", "cancel"])
async def test_stale_native_flow_never_acknowledges_or_deletes_newer_issue(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path, stage: str
) -> None:
    """Der RepairsFlowManager darf keinen neueren Hinweis unter derselben ID löschen."""
    assert await async_sync_vue_dashboard(hass, entry)
    manager, flow_id = await _flow(hass, entry)
    if stage == "reload":
        await manager.async_configure(flow_id, {"next_step_id": "confirm"})
    await hass.async_add_executor_job(assets.write_text, "// changed during dialog\n")
    result = await manager.async_configure(
        flow_id, {} if stage == "reload" else {"next_step_id": stage}
    )
    assert result["type"] == "abort" and result["reason"] == "update_changed"
    assert entry.data[CONF_VUE_DASHBOARD_VERSION] == "previous-snapshot"
    assert CONF_VUE_DASHBOARD_DISMISSED_VERSION not in entry.data
    assert _issue(hass, entry).data["version"] == _version(assets)


@pytest.mark.parametrize("existing_panel", [False, True])
async def test_failed_registration_remains_fixable_and_retry_can_succeed(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path, existing_panel: bool
) -> None:
    """Ein fehlgeschlagener Repair hat keinen CREATE_ENTRY-Erfolg und keinen Marker."""
    if existing_panel:
        assert await async_sync_vue_dashboard(hass, entry)
    with patch(f"{_MODULE}.panel_custom.async_register_panel", side_effect=ValueError):
        if not existing_panel:
            assert not await async_sync_vue_dashboard(hass, entry)
        manager, flow_id = await _flow(hass, entry)
        result = await manager.async_configure(flow_id, {"next_step_id": "confirm"})
    assert result["type"] == "form" and result["step_id"] == "confirm"
    assert result["errors"] == {"base": "update_failed"}
    assert _issue(hass, entry) is not None
    assert entry.data[CONF_VUE_DASHBOARD_VERSION] == "previous-snapshot"
    result = await manager.async_configure(flow_id, {})
    assert result["type"] == "form" and result["step_id"] == "reload"
    assert (await manager.async_configure(flow_id, {}))["type"] == "create_entry"
    assert entry.data[CONF_VUE_DASHBOARD_VERSION] == _version(assets)
    assert _issue(hass, entry) is None


async def test_restored_missing_asset_does_not_confirm_fresh_baseline_without_panel(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path
) -> None:
    """Ein veralteter Fehlerdialog darf eine fehlende Registrierung nicht quittieren."""
    hass.config_entries.async_update_entry(entry, data={CONF_VUE_DASHBOARD_VERSION: ""})
    await hass.async_add_executor_job(assets.unlink)
    assert not await async_sync_vue_dashboard(hass, entry)
    manager, flow_id = await _flow(hass, entry)
    await hass.async_add_executor_job(assets.write_text, "// restored asset\n")
    result = await manager.async_configure(flow_id, {"next_step_id": "confirm"})
    assert result["type"] == "abort" and result["reason"] == "update_changed"
    assert entry.data[CONF_VUE_DASHBOARD_VERSION] == ""
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    assert _issue(hass, entry).data["version"] == _version(assets)


@pytest.mark.parametrize("removed", [False, True])
async def test_removed_or_disabled_entry_cannot_be_reactivated_by_old_repair(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path, removed: bool
) -> None:
    """Alte Dialoge reaktivieren keine entfernten oder abgeschalteten Einträge."""
    assert await async_sync_vue_dashboard(hass, entry)
    manager, flow_id = await _flow(hass, entry)
    await async_unload_vue_dashboard(hass, entry)
    if removed:
        await hass.config_entries.async_remove(entry.entry_id)
    else:
        await hass.config_entries.async_set_disabled_by(
            entry.entry_id, config_entries.ConfigEntryDisabler.USER
        )
    result = await manager.async_configure(flow_id, {"next_step_id": "confirm"})
    assert result["type"] == "abort" and result["reason"] == "no_longer_available"
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    assert _issue(hass, entry) is None


@pytest.mark.parametrize("setup_result", [False, True])
async def test_disable_during_setup_leaves_neither_panel_nor_issue(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path, setup_result: bool
) -> None:
    """Auch der Fehlerpfad prüft die aktuelle Aktivierung nach einem Await erneut."""
    started = asyncio.Event()
    finish = asyncio.Event()

    async def delayed_setup(*args: object) -> bool:
        started.set()
        await finish.wait()
        return setup_result

    with patch(f"{_MODULE}.async_setup_component", side_effect=delayed_setup):
        task = asyncio.create_task(async_sync_vue_dashboard(hass, entry))
        await started.wait()
        await hass.config_entries.async_set_disabled_by(
            entry.entry_id, config_entries.ConfigEntryDisabler.USER
        )
        finish.set()
        assert not await task
    assert not frontend.async_panel_exists(hass, VUE_DASHBOARD_URL_PATH)
    assert _issue(hass, entry) is None


async def test_foreign_panel_cannot_be_confirmed_as_repaired(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path
) -> None:
    """Fremde Panel-Eigentümer werden auch im Reparaturmodus respektiert."""
    frontend.async_register_built_in_panel(
        hass, "map", frontend_url_path=VUE_DASHBOARD_URL_PATH
    )
    foreign = _panel(hass)
    assert not await async_sync_vue_dashboard(hass, entry)
    manager, flow_id = await _flow(hass, entry)
    result = await manager.async_configure(flow_id, {"next_step_id": "confirm"})
    assert result["type"] == "form" and result["errors"] == {"base": "update_failed"}
    assert _panel(hass) is foreign
    assert not await async_finish_vue_dashboard_repair(hass, entry, _version(assets))


async def test_repair_markers_do_not_reapply_charging_policy(
    hass: HomeAssistant, entry: MockConfigEntry, assets: Path
) -> None:
    """Interne Metadaten erzeugen keine Geräte- oder Ladeplan-Schreibaktion."""
    coordinator = MagicMock()
    coordinator.options = dict(entry.options)
    coordinator.async_apply_price_plan = AsyncMock()
    hass.data[DOMAIN] = {entry.entry_id: {DATA_COORDINATOR: coordinator}}
    unsubscribe = entry.add_update_listener(async_update_options)
    try:
        assert await async_sync_vue_dashboard(hass, entry)
        manager, flow_id = await _flow(hass, entry)
        await manager.async_configure(flow_id, {"next_step_id": "confirm"})
        await manager.async_configure(flow_id, {})
        await hass.async_block_till_done()
    finally:
        unsubscribe()
    coordinator.async_apply_price_plan.assert_not_awaited()
    coordinator.notify_tariff_revision.assert_not_called()
    coordinator.price_planner.async_setup.assert_not_called()
    assert _issue(hass, entry) is None
