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
from homeassistant.setup import async_setup_component
from homeassistant.util.hass_dict import HassKey

from .const import CONF_VUE_DASHBOARD_ENABLED, DEFAULT_VUE_DASHBOARD_ENABLED
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
    return True


def _enabled(entry: ConfigEntry) -> bool:
    return entry.options.get(
        CONF_VUE_DASHBOARD_ENABLED,
        entry.data.get(CONF_VUE_DASHBOARD_ENABLED, DEFAULT_VUE_DASHBOARD_ENABLED),
    )


async def async_sync_vue_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Synchronisiere die dauerhafte Option, ohne das Batterie-Setup zu blockieren."""
    if _DATA_RUNTIME not in hass.data and not _enabled(entry):
        return True

    runtime = hass.data.setdefault(_DATA_RUNTIME, _PanelRuntime())
    async with runtime.lock:
        # Zwischen zwei Options-Updates kann ein asynchrones Frontend-Setup
        # liegen; entscheidend ist der zuletzt gespeicherte Zustand.
        if not _enabled(entry):
            if runtime.entry_id == entry.entry_id:
                return _remove_owned_panel(hass, runtime)
            return True
        current = hass.data.get(frontend.DATA_PANELS, {}).get(VUE_DASHBOARD_URL_PATH)
        if current is not None:
            if current is runtime.panel and runtime.entry_id == entry.entry_id:
                return True
            _LOGGER.warning(
                "Vue-Dashboard kann nicht aktiviert werden: Panel-Pfad %s "
                "ist bereits belegt",
                VUE_DASHBOARD_URL_PATH,
            )
            return False

        try:
            version = await hass.async_add_executor_job(_asset_version)
            if not await async_setup_component(hass, "panel_custom", {}):
                _LOGGER.warning(
                    "Vue-Dashboard kann nicht aktiviert werden: "
                    "Home-Assistant-Frontend ist nicht verfügbar"
                )
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
        except Exception:  # noqa: BLE001
            # Die optionale Oberfläche darf die Geräteverbindung und ihre
            # Schutz-/Ladefunktionen nicht von einem Frontendfehler abhängig machen.
            _LOGGER.exception("Vue-Dashboard konnte nicht aktiviert werden")
            return False
    return True


async def async_unload_vue_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Entferne ausschließlich das zu diesem Config Entry gehörende Panel."""
    runtime = hass.data.get(_DATA_RUNTIME)
    if runtime is None:
        return
    async with runtime.lock:
        if runtime.entry_id == entry.entry_id:
            _remove_owned_panel(hass, runtime)
