"""Worker copied into a fresh installation by verify_dashboard_package.py.

Only Python and Home Assistant test dependencies are available to this check.
The frontend is served by HA from the installed ZIP; no Node/build step runs.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

from homeassistant.components import frontend
from homeassistant.components import repairs as ha_repairs
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power import const, vue_dashboard

INSTALLATION_ROOT = Path(__file__).parent.resolve()
PACKAGE_ROOT = INSTALLATION_ROOT / "custom_components" / "sax_power"


def test_only_installed_python_and_complete_frontend_are_used() -> None:
    """REQ-VUE-PARITY: neither Python modules nor browser assets fall back to Git."""
    assert sys.flags.isolated
    assert Path.cwd().resolve() == INSTALLATION_ROOT
    assert (PACKAGE_ROOT / "manifest.json").is_file()
    assert not (PACKAGE_ROOT / "dashboard.py").exists()
    manifest = json.loads((PACKAGE_ROOT / "manifest.json").read_text())
    assert "lovelace" not in manifest.get("after_dependencies", [])
    for name, module in list(sys.modules.items()):
        if name.startswith("custom_components.sax_power"):
            module_path = Path(module.__file__).resolve()
            assert module_path.is_relative_to(PACKAGE_ROOT), (name, module_path)
    assert vue_dashboard.VUE_DASHBOARD_ASSET_PATH.resolve().is_relative_to(PACKAGE_ROOT)
    assert not (INSTALLATION_ROOT / "node_modules").exists()
    assert not (INSTALLATION_ROOT / "frontend").exists()
    asset = vue_dashboard.VUE_DASHBOARD_ASSET_PATH.read_bytes()
    assert (
        hashlib.sha256(asset).hexdigest() == os.environ["SAX_DASHBOARD_PACKAGE_SHA256"]
    )
    assert b"sax-power-vue-panel" in asset
    assert b"/@vite/client" not in asset
    for language in ("de", "en"):
        translations = json.loads(
            (PACKAGE_ROOT / "translations" / f"{language}.json").read_text()
        )
        assert "vue_dashboard_update" in translations["issues"]
        assert "dashboard_outdated" not in translations["issues"]


async def test_installed_asset_and_repair_hash_are_served_by_home_assistant(
    hass: HomeAssistant, hass_client: Any, enable_custom_integrations: Any
) -> None:
    """REQ-VUE-PARITY: the installed panel and repair flow work without Modbus."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={const.CONF_VUE_DASHBOARD_VERSION: ""},
    )
    entry.add_to_hass(hass)
    # Enable discovery of the installed repairs platform without starting the
    # coordinator: full integration/Modbus setup is tested in the E2E suite.
    hass.config.components.add(const.DOMAIN)
    asset_path = vue_dashboard.VUE_DASHBOARD_ASSET_PATH
    original = await hass.async_add_executor_job(asset_path.read_bytes)
    expected_hash = hashlib.sha256(original).hexdigest()
    with patch(
        "pymodbus.client.AsyncModbusTcpClient.connect",
        new_callable=AsyncMock,
        side_effect=AssertionError("Der Pakettest darf keine Batterie verbinden."),
    ) as modbus_connect:
        assert await vue_dashboard.async_sync_vue_dashboard(hass, entry)
        panels = hass.data[frontend.DATA_PANELS]
        assert panels[vue_dashboard.VUE_DASHBOARD_URL_PATH].sidebar_title == "SAX Power"
        module_url = panels[vue_dashboard.VUE_DASHBOARD_URL_PATH].config[
            "_panel_custom"
        ]["module_url"]
        assert (
            module_url == f"{vue_dashboard.VUE_DASHBOARD_ASSET_URL}?v={expected_hash}"
        )
        client = await hass_client()
        response = await client.get(module_url)
        assert response.status == 200
        assert "javascript" in response.headers["Content-Type"]
        assert "max-age" in response.headers["Cache-Control"]
        assert await response.read() == original
        response = await client.get("/sax_power/frontend/vue_dashboard.py")
        assert response.status == 404

        updated = original + b"\n// Isolated package update smoke check.\n"
        updated_hash = hashlib.sha256(updated).hexdigest()
        try:
            await hass.async_add_executor_job(asset_path.write_bytes, updated)
            assert await vue_dashboard.async_sync_vue_dashboard(hass, entry)
            issue = ir.async_get(hass).async_get_issue(
                const.DOMAIN, f"{const.ISSUE_VUE_DASHBOARD_UPDATE}_{entry.entry_id}"
            )
            assert issue is not None and issue.data is not None
            assert issue.data["version"] == updated_hash
            manager = ha_repairs.repairs_flow_manager(hass)
            assert manager is not None
            result = await manager.async_init(
                const.DOMAIN,
                data={
                    "issue_id": f"{const.ISSUE_VUE_DASHBOARD_UPDATE}_{entry.entry_id}"
                },
            )
            assert result["type"] == "menu"
            flow_id = result["flow_id"]
            result = await manager.async_configure(flow_id, {"next_step_id": "confirm"})
            assert result["type"] == "form" and result["step_id"] == "reload"
            updated_url = panels[vue_dashboard.VUE_DASHBOARD_URL_PATH].config[
                "_panel_custom"
            ]["module_url"]
            assert updated_url != module_url
            assert updated_url.endswith(f"?v={updated_hash}")
            response = await client.get(updated_url)
            assert response.status == 200
            assert await response.read() == updated
            result = await manager.async_configure(flow_id, {})
            assert result["type"] == "create_entry"
            assert entry.data[const.CONF_VUE_DASHBOARD_VERSION] == updated_hash
            assert (
                ir.async_get(hass).async_get_issue(
                    const.DOMAIN, f"{const.ISSUE_VUE_DASHBOARD_UPDATE}_{entry.entry_id}"
                )
                is None
            )
        finally:
            await hass.async_add_executor_job(asset_path.write_bytes, original)
        await vue_dashboard.async_unload_vue_dashboard(hass, entry)
        assert not frontend.async_panel_exists(
            hass, vue_dashboard.VUE_DASHBOARD_URL_PATH
        )
        modbus_connect.assert_not_called()
