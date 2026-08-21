"""Mitgeliefertes Lovelace-Dashboard für SAX Power (siehe anforderung.yaml,
REQ-BUNDLED-DASHBOARD).

Baut ein dreiteiliges Storage-Dashboard ("Allgemeine Informationen",
"Ladeautomatik", "Dynamisches Laden") und legt es - wenn der Anwender das in
der Ersteinrichtung ausgewählt hat (config_flow.py, CONF_CREATE_DASHBOARD) -
direkt in Home Assistants Lovelace-Speicher an, damit es sofort ohne
Neustart in der Sidebar erscheint.

Home Assistant selbst nutzt für sein eigenes Onboarding-Kartendashboard
denselben Weg (homeassistant.components.lovelace._create_map_dashboard):
über die dortige, für das laufende Setup live verdrahtete
DashboardsCollection-Instanz anlegen lassen - die Änderung landet dadurch
automatisch sowohl im Speicher als auch sofort sichtbar in der Sidebar,
weil ein Listener auf genau dieser Instanz lauscht. Diese Instanz ist von
außerhalb von homeassistant.components.lovelace nicht erreichbar, deshalb
hier nachgebaut aus den beiden dafür vorgesehenen (aber sonst nur intern
verdrahteten) Bausteinen: eine neue DashboardsCollection (liest/schreibt
denselben Speicher, persistiert den Eintrag korrekt) plus eine manuell
angelegte LovelaceStorage-Instanz + frontend.async_register_built_in_panel
(sorgt für die sofortige Sichtbarkeit, die der fehlende Listener sonst
übernehmen würde). Rein optionale Komfortfunktion - siehe
async_create_dashboard für die Fehlerbehandlung.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import frontend
from homeassistant.components.lovelace import dashboard as lovelace_dashboard
from homeassistant.components.lovelace.const import CONF_ICON as LL_CONF_ICON
from homeassistant.components.lovelace.const import (
    CONF_REQUIRE_ADMIN,
    CONF_SHOW_IN_SIDEBAR,
    CONF_URL_PATH,
    DEFAULT_ICON,
    LOVELACE_DATA,
    MODE_STORAGE,
)
from homeassistant.components.lovelace.const import CONF_TITLE as LL_CONF_TITLE
from homeassistant.components.lovelace.const import DOMAIN as LOVELACE_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DASHBOARD_URL_PATH = "sax-power"
DASHBOARD_TITLE = "SAX Power"
DASHBOARD_ICON = "mdi:battery-charging-100"


def _entity_id(hass: HomeAssistant, entity_domain: str, unique_id: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(entity_domain, DOMAIN, unique_id)


def _entities_card(
    hass: HomeAssistant,
    entry_id: str,
    title: str,
    entities: list[tuple[str, str]],
) -> dict[str, Any] | None:
    """Baut eine "entities"-Karte aus (Entity-Domain, unique_id-Suffix)-Paaren.

    Entities, die (noch) nicht in der Entity Registry stehen, werden
    stillschweigend übersprungen; eine Karte ohne verbliebene Entities wird
    komplett weggelassen statt leer angezeigt zu werden.
    """
    resolved = [
        entity_id
        for entity_domain, suffix in entities
        if (entity_id := _entity_id(hass, entity_domain, f"{entry_id}_{suffix}"))
        is not None
    ]
    if not resolved:
        return None
    return {"type": "entities", "title": title, "entities": resolved}


def _view(
    title: str, path: str, icon: str, cards: list[dict[str, Any] | None]
) -> dict[str, Any]:
    return {
        "title": title,
        "path": path,
        "icon": icon,
        "cards": [card for card in cards if card is not None],
    }


def async_build_dashboard_config(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Baut die komplette Lovelace-Konfiguration (drei Tabs) für einen Entry."""
    general_view = _view(
        "Allgemeine Informationen",
        "allgemein",
        "mdi:information-outline",
        [
            _entities_card(
                hass,
                entry_id,
                "Übersicht",
                [
                    ("switch", "storage_switch"),
                    ("sensor", "storage_state_text"),
                    ("sensor", "soc"),
                    ("number", "max_soc"),
                ],
            ),
            _entities_card(
                hass,
                entry_id,
                "Leistung",
                [
                    ("sensor", "charge_power"),
                    ("sensor", "discharge_power"),
                    ("sensor", "smartmeter_power"),
                    ("sensor", "storage_max_cell_temp"),
                ],
            ),
            _entities_card(
                hass,
                entry_id,
                "Energie",
                [
                    ("sensor", "energy_charged"),
                    ("sensor", "energy_discharged"),
                ],
            ),
            _entities_card(
                hass,
                entry_id,
                "Gerät",
                [
                    ("sensor", "sun_manufacturer"),
                    ("sensor", "sun_model"),
                    ("sensor", "sun_version_master"),
                    ("sensor", "sun_version_gateway"),
                    ("sensor", "sun_serial_number"),
                    ("sensor", "storage_event_text"),
                ],
            ),
        ],
    )

    charging_view = _view(
        "Ladeautomatik",
        "ladeautomatik",
        "mdi:transmission-tower",
        [
            _entities_card(
                hass,
                entry_id,
                "Netzladung (zeitgesteuert)",
                [
                    ("switch", "timed_charge_enabled"),
                    ("time", "timed_charge_start"),
                    ("time", "timed_charge_end"),
                    ("number", "timed_charge_min_soc"),
                    ("number", "max_soc"),
                    ("number", "charge_limit"),
                    ("sensor", "timed_charge_active_text"),
                ],
            ),
            _entities_card(
                hass,
                entry_id,
                "Netzdienliches Laden",
                [
                    ("switch", "grid_serving_enabled"),
                    ("time", "grid_serving_start"),
                    ("time", "grid_serving_end"),
                    ("sensor", "grid_serving_active_text"),
                ],
            ),
        ],
    )

    price_view = _view(
        "Dynamisches Laden",
        "dynamisches-laden",
        "mdi:chart-line",
        [
            _entities_card(
                hass,
                entry_id,
                "Preisoptimiertes Laden",
                [
                    ("switch", "price_charge_enabled"),
                    ("select", "price_charge_strategy"),
                    ("number", "price_charge_max_price"),
                    ("number", "price_charge_hours"),
                    ("number", "max_soc"),
                    ("sensor", "price_charge_active_text"),
                    ("sensor", "price_charge_status_text"),
                    ("sensor", "price_charge_next_start"),
                    ("sensor", "price_charge_current_price"),
                ],
            ),
        ],
    )

    return {"views": [general_view, charging_view, price_view]}


async def async_create_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Legt das mitgelieferte SAX-Power-Dashboard an, falls es noch nicht existiert.

    Rein optionale Komfortfunktion, die auf nicht-öffentlichen Lovelace-
    Interna aufbaut (siehe Modul-Docstring) - jeder Fehler wird deshalb nur
    geloggt statt weitergereicht, damit ein künftiges Home-Assistant-Update,
    das diese Interna ändert, niemals die Einrichtung der eigentlichen
    Integration blockiert.
    """
    try:
        await _async_create_dashboard(hass, entry)
    except Exception:  # siehe Docstring - darf die Integration nie blockieren
        _LOGGER.warning(
            'Dashboard "%s" konnte nicht automatisch angelegt werden - bitte bei '
            "Bedarf manuell über Einstellungen -> Dashboards anlegen",
            DASHBOARD_TITLE,
            exc_info=True,
        )


async def _async_create_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    lovelace_data = hass.data.get(LOVELACE_DATA)
    if lovelace_data is None:
        _LOGGER.warning("Lovelace ist nicht verfügbar, Dashboard wird übersprungen")
        return
    if DASHBOARD_URL_PATH in lovelace_data.dashboards:
        return  # bereits angelegt (z. B. durch einen früheren Setup-Lauf)

    # Eigene DashboardsCollection-Instanz statt der von lovelace.async_setup
    # verdrahteten (siehe Modul-Docstring) - liest/schreibt denselben
    # Speicher, deshalb hier zusätzlich prüfen, ob der Eintrag schon
    # persistiert wurde (z. B. nach einem Neustart), auch wenn er im
    # laufenden Betrieb noch nicht in lovelace_data.dashboards auftaucht.
    dashboards_collection = lovelace_dashboard.DashboardsCollection(hass)
    await dashboards_collection.async_load()
    if any(
        item[CONF_URL_PATH] == DASHBOARD_URL_PATH
        for item in dashboards_collection.async_items()
    ):
        return

    item = await dashboards_collection.async_create_item(
        {
            LL_CONF_ICON: DASHBOARD_ICON,
            LL_CONF_TITLE: DASHBOARD_TITLE,
            CONF_URL_PATH: DASHBOARD_URL_PATH,
        }
    )

    storage = lovelace_dashboard.LovelaceStorage(hass, item)
    await storage.async_save(async_build_dashboard_config(hass, entry.entry_id))
    lovelace_data.dashboards[DASHBOARD_URL_PATH] = storage

    frontend.async_register_built_in_panel(
        hass,
        LOVELACE_DOMAIN,
        frontend_url_path=DASHBOARD_URL_PATH,
        require_admin=item[CONF_REQUIRE_ADMIN],
        show_in_sidebar=item[CONF_SHOW_IN_SIDEBAR],
        sidebar_title=item[LL_CONF_TITLE],
        sidebar_icon=item.get(LL_CONF_ICON, DEFAULT_ICON),
        config={"mode": MODE_STORAGE},
    )
