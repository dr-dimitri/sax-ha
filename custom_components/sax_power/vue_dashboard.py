"""Optionales Vue-Panel neben dem Lovelace-Dashboard (REQ-VUE-DASHBOARD)."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component
from homeassistant.util.hass_dict import HassKey

from .const import (
    CONF_VUE_DASHBOARD_DISMISSED_VERSION,
    CONF_VUE_DASHBOARD_ENABLED,
    CONF_VUE_DASHBOARD_VERSION,
    DEFAULT_VUE_DASHBOARD_ENABLED,
    DOMAIN,
    ISSUE_VUE_DASHBOARD_UPDATE,
)
from .dashboard_api import async_register_dashboard_api

_LOGGER = logging.getLogger(__name__)

VUE_DASHBOARD_URL_PATH = "sax-power-vue"
VUE_DASHBOARD_TITLE = "SAX Power (Vue)"
VUE_DASHBOARD_ICON = "mdi:battery-charging-100"
VUE_DASHBOARD_ELEMENT = "sax-power-vue-panel"
VUE_DASHBOARD_ASSET_URL = "/sax_power/frontend/sax-power-vue.js"
VUE_DASHBOARD_ASSET_PATH = Path(__file__).parent / "frontend" / "sax-power-vue.js"


@dataclass(slots=True)
class _PanelRuntime:
    """Eigentum des Panels und die einmalige HTTP-Registrierung je HA-Lauf."""

    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    static_registered: bool = False
    entry_id: str | None = None
    panel: frontend.Panel | None = None
    version: str | None = None


_DATA_RUNTIME: HassKey[_PanelRuntime] = HassKey("sax_power_vue_dashboard")


def _asset_version() -> str:
    """Neue Asset-Inhalte erhalten unabhängig von der Releaseart eine neue URL."""
    return hashlib.sha256(VUE_DASHBOARD_ASSET_PATH.read_bytes()).hexdigest()


def _remove_owned_panel(hass: HomeAssistant, runtime: _PanelRuntime) -> bool:
    current = hass.data.get(frontend.DATA_PANELS, {}).get(VUE_DASHBOARD_URL_PATH)
    if runtime.panel is not None and current is runtime.panel:
        try:
            frontend.async_remove_panel(hass, VUE_DASHBOARD_URL_PATH)
        except Exception:
            # REQ-VUE-DASHBOARD: Auch beim Abschalten darf ein Frontendfehler
            # weder den Geräte-Unload noch die Optionsverarbeitung abbrechen.
            _LOGGER.exception("Vue-Dashboard konnte nicht entfernt werden")
            return False
    runtime.panel = None
    runtime.entry_id = None
    runtime.version = None
    return True


def _enabled(entry: ConfigEntry) -> bool:
    return entry.disabled_by is None and entry.options.get(
        CONF_VUE_DASHBOARD_ENABLED,
        entry.data.get(CONF_VUE_DASHBOARD_ENABLED, DEFAULT_VUE_DASHBOARD_ENABLED),
    )


def _issue_id(entry: ConfigEntry) -> str:
    return f"{ISSUE_VUE_DASHBOARD_UPDATE}_{entry.entry_id}"


def _update_issue(
    hass: HomeAssistant,
    entry: ConfigEntry,
    version: str,
    *,
    failed: bool = False,
    initialize: bool = False,
) -> None:
    """Ein bereits definiertes Custom Element braucht einen Browser-Reload."""
    if not vue_dashboard_available(hass, entry):
        ir.async_delete_issue(hass, DOMAIN, _issue_id(entry))
        return
    token = f"failed:{version}" if failed else version
    if initialize and not failed and entry.data.get(CONF_VUE_DASHBOARD_VERSION) == "":
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_VUE_DASHBOARD_VERSION: version}
        )
    if entry.data.get(CONF_VUE_DASHBOARD_DISMISSED_VERSION) == token or (
        not failed and entry.data.get(CONF_VUE_DASHBOARD_VERSION) == version
    ):
        ir.async_delete_issue(hass, DOMAIN, _issue_id(entry))
        return
    ir.async_create_issue(
        hass,
        DOMAIN,
        _issue_id(entry),
        is_fixable=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_VUE_DASHBOARD_UPDATE,
        data={
            "entry_id": entry.entry_id,
            "issue_key": ISSUE_VUE_DASHBOARD_UPDATE,
            "version": version,
            "token": token,
        },
    )


def vue_dashboard_available(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ob der Eintrag noch existiert und sein Vue-Dashboard aktiviert ist."""
    return hass.config_entries.async_get_entry(entry.entry_id) is entry and _enabled(
        entry
    )


async def async_sync_vue_dashboard(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    force: bool = False,
    expected_version: str | None = None,
) -> bool:
    """Synchronisiere die dauerhafte Option, ohne das Batterie-Setup zu blockieren."""
    if _DATA_RUNTIME not in hass.data and not _enabled(entry):
        ir.async_delete_issue(hass, DOMAIN, _issue_id(entry))
        return not force

    runtime = hass.data.setdefault(_DATA_RUNTIME, _PanelRuntime())
    async with runtime.lock:
        # Zwischen zwei Options-Updates kann ein asynchrones Frontend-Setup
        # liegen; entscheidend ist der zuletzt gespeicherte Zustand.
        if not _enabled(entry):
            ir.async_delete_issue(hass, DOMAIN, _issue_id(entry))
            if runtime.entry_id == entry.entry_id:
                removed = _remove_owned_panel(hass, runtime)
                return removed and not force
            return not force
        version = ""
        try:
            version = await hass.async_add_executor_job(_asset_version)
            if not vue_dashboard_available(hass, entry):
                return False
            current = hass.data.get(frontend.DATA_PANELS, {}).get(
                VUE_DASHBOARD_URL_PATH
            )
            owned = current is runtime.panel and runtime.entry_id == entry.entry_id
            if current is not None and not owned:
                _LOGGER.warning(
                    "Vue-Dashboard kann nicht aktiviert werden: Panel-Pfad %s "
                    "ist bereits belegt",
                    VUE_DASHBOARD_URL_PATH,
                )
                _update_issue(hass, entry, version, failed=True)
                return False
            if expected_version is not None and expected_version != version:
                _update_issue(hass, entry, version)
                return False
            if owned and not force:
                _update_issue(
                    hass, entry, version, initialize=runtime.version == version
                )
                return True
            if not await async_setup_component(hass, "panel_custom", {}):
                _LOGGER.warning(
                    "Vue-Dashboard kann nicht aktiviert werden: "
                    "Home-Assistant-Frontend ist nicht verfügbar"
                )
                _update_issue(hass, entry, version, failed=True)
                return False
            if not vue_dashboard_available(hass, entry):
                return False
            async_register_dashboard_api(hass)
            if not runtime.static_registered:
                await hass.http.async_register_static_paths(
                    [
                        StaticPathConfig(
                            VUE_DASHBOARD_ASSET_URL,
                            str(VUE_DASHBOARD_ASSET_PATH),
                            cache_headers=True,
                        )
                    ]
                )
                # Home Assistant bietet kein Unregister für statische Routen.
                # Die einzelne, datenfreie Asset-Route bleibt deshalb auch
                # beim Deaktivieren erhalten (REQ-VUE-DASHBOARD).
                runtime.static_registered = True
            if not vue_dashboard_available(hass, entry):
                return False
            # Während Frontend-/HTTP-Setup darf ein anderes Panel den Pfad
            # belegt haben; die Reparatur ersetzt ausschließlich unser eigenes.
            current = hass.data.get(frontend.DATA_PANELS, {}).get(
                VUE_DASHBOARD_URL_PATH
            )
            if current is not None and (
                current is not runtime.panel or runtime.entry_id != entry.entry_id
            ):
                _update_issue(hass, entry, version, failed=True)
                return False
            if current is not None and not _remove_owned_panel(hass, runtime):
                _update_issue(hass, entry, version, failed=True)
                return False
            await panel_custom.async_register_panel(
                hass,
                frontend_url_path=VUE_DASHBOARD_URL_PATH,
                webcomponent_name=VUE_DASHBOARD_ELEMENT,
                sidebar_title=VUE_DASHBOARD_TITLE,
                sidebar_icon=VUE_DASHBOARD_ICON,
                module_url=f"{VUE_DASHBOARD_ASSET_URL}?v={version}",
                config={"entry_id": entry.entry_id},
                require_admin=False,
            )
            runtime.panel = hass.data[frontend.DATA_PANELS][VUE_DASHBOARD_URL_PATH]
            runtime.entry_id = entry.entry_id
            runtime.version = version
            if not vue_dashboard_available(hass, entry):
                _remove_owned_panel(hass, runtime)
                return False
            _update_issue(hass, entry, version, initialize=not force)
        except Exception:  # noqa: BLE001
            # Die optionale Oberfläche darf die Geräteverbindung und ihre
            # Schutz-/Ladefunktionen nicht von einem Frontendfehler abhängig machen.
            _LOGGER.exception("Vue-Dashboard konnte nicht aktiviert werden")
            if vue_dashboard_available(hass, entry):
                _update_issue(hass, entry, version, failed=True)
            return False
    return True


async def async_finish_vue_dashboard_repair(
    hass: HomeAssistant,
    entry: ConfigEntry,
    version: str,
    *,
    dismissed_token: str | None = None,
) -> bool:
    """Quittiere nur den im Dialog gezeigten Stand (REQ-VUE-DASHBOARD-REPAIR)."""
    runtime = hass.data.setdefault(_DATA_RUNTIME, _PanelRuntime())
    async with runtime.lock:
        try:
            current_version = await hass.async_add_executor_job(_asset_version)
        except OSError:
            current_version = ""
        if not vue_dashboard_available(hass, entry):
            return False
        if current_version != version:
            _update_issue(hass, entry, current_version, failed=not current_version)
            return False
        data = dict(entry.data)
        if dismissed_token is not None:
            issue = ir.async_get(hass).async_get_issue(DOMAIN, _issue_id(entry))
            if (
                issue is None
                or issue.data is None
                or issue.data.get("token") != dismissed_token
            ):
                return False
            data[CONF_VUE_DASHBOARD_DISMISSED_VERSION] = dismissed_token
        else:
            current = hass.data.get(frontend.DATA_PANELS, {}).get(
                VUE_DASHBOARD_URL_PATH
            )
            if (
                not version
                or current is not runtime.panel
                or runtime.entry_id != entry.entry_id
                or runtime.version != version
            ):
                _update_issue(hass, entry, version, failed=True)
                return False
            data[CONF_VUE_DASHBOARD_VERSION] = version
            data.pop(CONF_VUE_DASHBOARD_DISMISSED_VERSION, None)
        hass.config_entries.async_update_entry(entry, data=data)
        return True


async def async_unload_vue_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Entferne ausschließlich das zu diesem Config Entry gehörende Panel."""
    ir.async_delete_issue(hass, DOMAIN, _issue_id(entry))
    runtime = hass.data.get(_DATA_RUNTIME)
    if runtime is None:
        return
    async with runtime.lock:
        if runtime.entry_id == entry.entry_id:
            _remove_owned_panel(hass, runtime)
