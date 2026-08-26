"""Mitgeliefertes Lovelace-Dashboard für SAX Power (siehe anforderung.yaml,
REQ-BUNDLED-DASHBOARD).

Baut ein fünfteiliges Storage-Dashboard ("Allgemeine Informationen",
"Ladeautomatik", "Netzdienliches Laden", "Dynamisches Laden",
"Wirtschaftlichkeit", siehe REQ-ECONOMICS-DASHBOARD) und legt es -
wenn der Anwender das in der Ersteinrichtung ausgewählt hat (config_flow.py,
CONF_CREATE_DASHBOARD) - direkt in Home Assistants Lovelace-Speicher an,
damit es sofort ohne Neustart in der Sidebar erscheint.

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

Kartenbeschriftungen verwenden bewusst nicht den vollen, geräteweiten
Anzeigenamen ("SAX Power Home <Entity>", entsteht durch
SaxPowerEntity._attr_has_entity_name), sondern nur den reinen
Entity-Namen aus der Übersetzung (component.sax_power.entity.<domain>.
<translation_key>.name) - andernfalls würde sich der Gerätename in jeder
einzelnen Kartenzeile wiederholen. Dafür werden dieselben Übersetzungen
geladen, die auch die Entity Registry selbst verwendet, statt den Text
hier zusätzlich fest zu hinterlegen (bleibt so für andere Sprachen als
Deutsch korrekt, siehe translations/en.json).
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
from homeassistant.helpers import translation

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DASHBOARD_URL_PATH = "sax-power"
DASHBOARD_TITLE = "SAX Power"
DASHBOARD_ICON = "mdi:battery-charging-100"

# Nur für die wenigen Fälle nötig, in denen der unique_id-Suffix (stabil,
# darf sich nicht mehr ändern) vom translation_key der Entity abweicht.
_TRANSLATION_KEY_OVERRIDES: dict[tuple[str, str], str] = {
    ("switch", "storage_switch"): "storage",
}

# Diese Entity aktualisiert ihren eigenen Namen täglich um das Datum. Ein hier
# gespeicherter Zeilenname würde dagegen bis zur Neuerstellung des Dashboards
# unverändert bleiben (siehe REQ-BUNDLED-DASHBOARD).
_ENTITY_NAME_FROM_STATE: set[tuple[str, str]] = {
    ("sensor", "grid_serving_forecast"),
}


def _entity_id(hass: HomeAssistant, entity_domain: str, unique_id: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(entity_domain, DOMAIN, unique_id)


def _entity_name(
    translations: dict[str, str], entity_domain: str, suffix: str
) -> str | None:
    translation_key = _TRANSLATION_KEY_OVERRIDES.get((entity_domain, suffix), suffix)
    return translations.get(
        f"component.{DOMAIN}.entity.{entity_domain}.{translation_key}.name"
    )


def _entities_card(
    hass: HomeAssistant,
    entry_id: str,
    title: str,
    entities: list[tuple[str, str]],
    translations: dict[str, str],
) -> dict[str, Any] | None:
    """Baut eine "entities"-Karte aus (Entity-Domain, unique_id-Suffix)-Paaren.

    Entities, die (noch) nicht in der Entity Registry stehen, werden
    stillschweigend übersprungen; eine Karte ohne verbliebene Entities wird
    komplett weggelassen statt leer angezeigt zu werden. Jede Zeile bekommt
    den reinen (geräteprefix-freien) Namen als Beschriftung, siehe
    Moduldocstring.
    """
    resolved: list[dict[str, str] | str] = []
    for entity_domain, suffix in entities:
        entity_id = _entity_id(hass, entity_domain, f"{entry_id}_{suffix}")
        if entity_id is None:
            continue
        if (entity_domain, suffix) in _ENTITY_NAME_FROM_STATE:
            resolved.append({"entity": entity_id})
            continue
        name = _entity_name(translations, entity_domain, suffix)
        resolved.append({"entity": entity_id, "name": name} if name else entity_id)
    if not resolved:
        return None
    return {
        "type": "entities",
        "title": title,
        "state_color": True,
        "entities": resolved,
    }


def _tile_card(
    hass: HomeAssistant,
    entry_id: str,
    entity_domain: str,
    suffix: str,
    translations: dict[str, str],
) -> dict[str, Any] | None:
    """Baut eine "tile"-Karte für eine einzelne Entity - moderner, größerer
    Status/Umschalter für die wichtigsten Ein/Aus-Größen, z. B. auf einen
    Blick sichtbar statt in einer Liste."""
    entity_id = _entity_id(hass, entity_domain, f"{entry_id}_{suffix}")
    if entity_id is None:
        return None
    card: dict[str, Any] = {"type": "tile", "entity": entity_id}
    name = _entity_name(translations, entity_domain, suffix)
    if name:
        card["name"] = name
    return card


def _gauge_card(
    hass: HomeAssistant,
    entry_id: str,
    entity_domain: str,
    suffix: str,
    translations: dict[str, str],
    *,
    min_value: float,
    max_value: float,
    segments: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Baut eine "gauge"-Karte statt einer Listenzeile - macht kritische
    Bereiche (z. B. Speicher fast leer, Zelltemperatur zu niedrig/hoch) auf
    einen Blick sichtbar. Immer über `segments` (Liste beliebiger, auch
    nicht monoton steigender Farbbereiche) statt über das alternative
    `severity`-Mapping (feste Schlüssel green/yellow/red): Home Assistants
    Gauge-Karte färbt `severity`-Farben über die Theme-Variablen
    (--success-/--warning-/--error-color), `segments`-Farben dagegen als
    wörtliche CSS-Farbnamen - dieselbe Zeichenkette "red"/"green" sieht
    dadurch in den beiden Modi unterschiedlich aus. Ausschließlich
    `segments` zu verwenden hält alle Gauge-Karten des Dashboards farblich
    konsistent. Immer im Nadel-Stil (needle), passend zum modernisierten
    Dashboard."""
    entity_id = _entity_id(hass, entity_domain, f"{entry_id}_{suffix}")
    if entity_id is None:
        return None
    return {
        "type": "gauge",
        "entity": entity_id,
        "name": _entity_name(translations, entity_domain, suffix),
        "min": min_value,
        "max": max_value,
        "needle": True,
        "segments": segments,
    }


def _resolved_row(
    hass: HomeAssistant,
    entry_id: str,
    entity_domain: str,
    suffix: str,
    translations: dict[str, str],
) -> tuple[str | None, dict[str, str] | str | None]:
    """Löst eine einzelne (Entity-Domain, unique_id-Suffix)-Zeile auf und
    liefert sowohl die rohe Entity-ID (für Attribut-Zeilen, siehe
    _attribute_row) als auch die fertige entities-Kartenzeile - oder
    (None, None), wenn die Entity (noch) nicht registriert ist."""
    entity_id = _entity_id(hass, entity_domain, f"{entry_id}_{suffix}")
    if entity_id is None:
        return None, None
    if (entity_domain, suffix) in _ENTITY_NAME_FROM_STATE:
        return entity_id, {"entity": entity_id}
    name = _entity_name(translations, entity_domain, suffix)
    return entity_id, ({"entity": entity_id, "name": name} if name else entity_id)


def _attribute_row(
    entity_id: str | None, attribute: str, name: str
) -> dict[str, Any] | None:
    """Eine "attribute"-Zeile einer entities-Karte - zeigt ein Attribut der
    übergebenen Entity wie einen eigenen Sensor an (REQ-ECONOMICS-
    DASHBOARD, für Preisabdeckungen/Bilanzbeginn, die keinen eigenen
    Sensor haben, siehe REQ-ECONOMICS-OBSERVABILITY)."""
    if entity_id is None:
        return None
    return {
        "type": "attribute",
        "entity": entity_id,
        "attribute": attribute,
        "name": name,
    }


def _statistics_graph_card(
    hass: HomeAssistant,
    entry_id: str,
    title: str,
    entities: list[tuple[str, str]],
) -> dict[str, Any] | None:
    """Core-"statistics-graph"-Karte als Balkendiagramm mit Tagesänderung
    (REQ-ECONOMICS-DASHBOARD) - keine Custom-Card-Abhängigkeit. `change`
    ist für `state_class: total`-Sensoren (wie die hier verwendeten
    Geldsensoren) eine unterstützte Langzeitstatistik-Kennzahl; sollte
    eine künftig getestete HA-Version das nicht mehr unterstützen, sind
    stattdessen die dedizierten Tages-Sensoren aus REQ-ECONOMICS-
    AMORTIZATION zu verwenden statt auf einen nicht unterstützten
    Kartentyp oder eine private Statistik-API auszuweichen."""
    resolved = [
        entity_id
        for entity_domain, suffix in entities
        if (entity_id := _entity_id(hass, entity_domain, f"{entry_id}_{suffix}"))
        is not None
    ]
    if not resolved:
        return None
    return {
        "type": "statistics-graph",
        "title": title,
        "entities": resolved,
        "stat_types": ["change"],
        "chart_type": "bar",
        "period": "day",
        "days_to_show": 30,
    }


def _grid_card(cards: list[dict[str, Any] | None]) -> dict[str, Any] | None:
    """Reiht mehrere Tile-Karten nebeneinander an - fehlende Entities werden
    wie bei _entities_card stillschweigend ausgelassen; bleibt am Ende
    nichts übrig, wird die ganze Zeile weggelassen."""
    resolved = [card for card in cards if card is not None]
    if not resolved:
        return None
    return {"type": "grid", "columns": 2, "square": False, "cards": resolved}


def _view(
    title: str, path: str, icon: str, cards: list[dict[str, Any] | None]
) -> dict[str, Any]:
    return {
        "title": title,
        "path": path,
        "icon": icon,
        "cards": [card for card in cards if card is not None],
    }


async def async_build_dashboard_config(
    hass: HomeAssistant, entry_id: str
) -> dict[str, Any]:
    """Baut die komplette Lovelace-Konfiguration (vier Tabs) für einen Entry."""
    translations = await translation.async_get_translations(
        hass, hass.config.language, "entity", integrations=[DOMAIN]
    )

    general_view = _view(
        "Allgemeine Informationen",
        "allgemein",
        "mdi:information-outline",
        [
            _grid_card(
                [
                    _gauge_card(
                        hass,
                        entry_id,
                        "sensor",
                        "soc",
                        translations,
                        min_value=0,
                        max_value=100,
                        # Dieselben Farben wie die Zelltemperatur-Gauge
                        # unten (rot/grün) - siehe _gauge_card-Docstring.
                        segments=[
                            {"from": 0, "color": "red"},
                            {"from": 20, "color": "yellow"},
                            {"from": 50, "color": "green"},
                        ],
                    ),
                    _gauge_card(
                        hass,
                        entry_id,
                        "sensor",
                        "storage_max_cell_temp",
                        translations,
                        min_value=0,
                        max_value=40,
                        # 0-5 °C zu kalt, 5-32 °C normaler Betriebsbereich,
                        # 32-40 °C zu heiß - kein einfaches "je höher desto
                        # kritischer" wie beim SOC.
                        segments=[
                            {"from": 0, "color": "red"},
                            {"from": 5, "color": "green"},
                            {"from": 32, "color": "red"},
                        ],
                    ),
                ]
            ),
            _tile_card(hass, entry_id, "switch", "storage_switch", translations),
            _entities_card(
                hass,
                entry_id,
                "Leistung",
                [
                    ("number", "max_soc"),
                    ("sensor", "charge_power"),
                    ("sensor", "discharge_power"),
                    ("sensor", "smartmeter_power"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Energie",
                [
                    ("sensor", "energy_charged"),
                    ("sensor", "energy_discharged"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Gerät",
                [
                    ("sensor", "sun_version_master"),
                    ("sensor", "sun_version_gateway"),
                    ("sensor", "sun_serial_number"),
                    ("sensor", "storage_event_text"),
                    ("sensor", "ic_control_mode_text"),
                    ("binary_sensor", "cell_calibration_active"),
                    ("sensor", "next_cell_calibration"),
                ],
                translations,
            ),
        ],
    )

    charging_view = _view(
        "Ladeautomatik",
        "ladeautomatik",
        "mdi:transmission-tower",
        [
            _tile_card(hass, entry_id, "switch", "timed_charge_enabled", translations),
            _entities_card(
                hass,
                entry_id,
                "Zeitfenster",
                [
                    ("time", "timed_charge_start"),
                    ("time", "timed_charge_end"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Einstellungen",
                [
                    ("number", "timed_charge_min_soc"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Aktive Monate",
                [("switch", f"timed_charge_month_{month}") for month in range(1, 13)],
                translations,
            ),
        ],
    )

    grid_serving_view = _view(
        "Netzdienliches Laden",
        "netzdienliches-laden",
        "mdi:transmission-tower-export",
        [
            _tile_card(hass, entry_id, "switch", "grid_serving_enabled", translations),
            _entities_card(
                hass,
                entry_id,
                "Ladepause",
                [
                    ("time", "grid_serving_start"),
                    ("time", "grid_serving_end"),
                    ("sensor", "grid_serving_forecast"),
                    ("number", "grid_serving_forecast_threshold"),
                    ("sensor", "grid_serving_pause_status"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Aktive Monate",
                [("switch", f"grid_serving_month_{month}") for month in range(1, 13)],
                translations,
            ),
        ],
    )

    price_view = _view(
        "Dynamisches Laden",
        "dynamisches-laden",
        "mdi:chart-line",
        [
            _tile_card(hass, entry_id, "switch", "price_charge_enabled", translations),
            _entities_card(
                hass,
                entry_id,
                "Preisoptimiertes Laden",
                [
                    ("select", "price_charge_strategy"),
                    ("number", "price_charge_max_price"),
                    ("number", "price_charge_neutral_price"),
                    ("number", "price_charge_hours"),
                    ("number", "max_soc"),
                    ("sensor", "price_charge_active_text"),
                    ("sensor", "price_charge_status_text"),
                    ("sensor", "grid_serving_forecast"),
                    ("sensor", "price_charge_next_start"),
                    ("sensor", "price_charge_current_price"),
                ],
                translations,
            ),
        ],
    )

    status_entity_id, status_row = _resolved_row(
        hass, entry_id, "sensor", "economics_status", translations
    )
    status_rows: list[dict[str, Any] | str] = [status_row] if status_row else []
    for entity_domain, suffix in (
        ("sensor", "economics_current_import_price"),
        ("sensor", "economics_feed_in_price"),
        ("sensor", "energy_origin_coverage"),
    ):
        _, row = _resolved_row(hass, entry_id, entity_domain, suffix, translations)
        if row is not None:
            status_rows.append(row)
    for attribute, label in (
        ("charge_price_coverage_percent", "Preisabdeckung Ladung"),
        ("discharge_price_coverage_percent", "Preisabdeckung Entladung"),
        ("economics_started_at", "Beginn der Bilanz"),
    ):
        row = _attribute_row(status_entity_id, attribute, label)
        if row is not None:
            status_rows.append(row)
    status_card = (
        {
            "type": "entities",
            "title": "Status und Preise",
            "state_color": True,
            "entities": status_rows,
        }
        if status_rows
        else None
    )

    economics_view = _view(
        "Wirtschaftlichkeit",
        "wirtschaftlichkeit",
        "mdi:cash-chart",
        [
            status_card,
            _entities_card(
                hass,
                entry_id,
                "Herkunft der Ladeenergie",
                [
                    ("sensor", "energy_charged_from_pv"),
                    ("sensor", "energy_charged_from_grid"),
                    ("sensor", "energy_charged_origin_unknown"),
                    ("sensor", "energy_charged"),
                    ("sensor", "energy_discharged"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Operative Geldbilanz",
                [
                    ("sensor", "economics_avoided_grid_cost"),
                    ("sensor", "economics_grid_charge_cost"),
                    ("sensor", "economics_pv_opportunity_cost"),
                    ("sensor", "economics_operating_result"),
                    ("sensor", "economics_unpriced_charge"),
                    ("sensor", "economics_unpriced_discharge"),
                ],
                translations,
            ),
            _gauge_card(
                hass,
                entry_id,
                "sensor",
                "economics_amortization_progress",
                translations,
                min_value=0,
                max_value=100,
                segments=[
                    {"from": 0, "color": "red"},
                    {"from": 50, "color": "yellow"},
                    {"from": 100, "color": "green"},
                ],
            ),
            _entities_card(
                hass,
                entry_id,
                "Investition und Amortisation",
                [
                    ("sensor", "economics_roi"),
                    ("sensor", "economics_remaining_to_payback"),
                    ("sensor", "economics_result_today"),
                    ("sensor", "economics_average_daily_result_30d"),
                    ("sensor", "economics_projected_annual_result"),
                    ("sensor", "economics_estimated_payback_date"),
                ],
                translations,
            ),
            _statistics_graph_card(
                hass,
                entry_id,
                "Verlauf (30 Tage)",
                [
                    ("sensor", "economics_operating_result"),
                    ("sensor", "economics_avoided_grid_cost"),
                    ("sensor", "economics_grid_charge_cost"),
                    ("sensor", "economics_pv_opportunity_cost"),
                ],
            ),
        ],
    )

    return {
        "views": [
            general_view,
            charging_view,
            grid_serving_view,
            price_view,
            economics_view,
        ]
    }


async def async_create_dashboard(
    hass: HomeAssistant, entry: ConfigEntry, *, force: bool = False
) -> None:
    """Legt das mitgelieferte SAX-Power-Dashboard an, falls es noch nicht existiert.

    `force=True` (Service sax_power.reinstall_dashboard, siehe __init__.py)
    überschreibt zusätzlich ein bereits vorhandenes Dashboard mit der
    aktuell aus den Views/Karten gebauten Konfiguration - z. B. um es nach
    manuellen Änderungen wieder auf den Auslieferungszustand
    zurückzusetzen. Panel-Registrierung/Sidebar-Eintrag bleiben dabei
    unangetastet, es wird nur der Karteninhalt neu geschrieben.

    Rein optionale Komfortfunktion, die auf nicht-öffentlichen Lovelace-
    Interna aufbaut (siehe Modul-Docstring) - jeder Fehler wird deshalb nur
    geloggt statt weitergereicht, damit ein künftiges Home-Assistant-Update,
    das diese Interna ändert, niemals die Einrichtung der eigentlichen
    Integration blockiert.
    """
    try:
        await _async_create_dashboard(hass, entry, force=force)
    except Exception:  # siehe Docstring - darf die Integration nie blockieren
        _LOGGER.warning(
            'Dashboard "%s" konnte nicht automatisch angelegt werden - bitte bei '
            "Bedarf manuell über Einstellungen -> Dashboards anlegen",
            DASHBOARD_TITLE,
            exc_info=True,
        )


async def _async_create_dashboard(
    hass: HomeAssistant, entry: ConfigEntry, *, force: bool
) -> None:
    lovelace_data = hass.data.get(LOVELACE_DATA)
    if lovelace_data is None:
        _LOGGER.warning("Lovelace ist nicht verfügbar, Dashboard wird übersprungen")
        return

    existing_storage = lovelace_data.dashboards.get(DASHBOARD_URL_PATH)
    if existing_storage is not None:
        if force:
            await existing_storage.async_save(
                await async_build_dashboard_config(hass, entry.entry_id)
            )
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
    await storage.async_save(await async_build_dashboard_config(hass, entry.entry_id))
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
