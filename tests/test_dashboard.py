"""Tests für das mitgelieferte Lovelace-Dashboard (dashboard.py, siehe
anforderung.yaml, REQ-BUNDLED-DASHBOARD).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from homeassistant.components.lovelace import LovelaceData
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers import template
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import sax_power
from custom_components.sax_power import binary_sensor, sensor  # noqa: F401
from custom_components.sax_power.const import (
    CONF_DASHBOARD_UPDATE_DISMISSED,
    DATA_COORDINATOR,
    DOMAIN,
    ISSUE_DASHBOARD_OUTDATED,
    SERVICE_CREATE_DASHBOARD,
    SERVICE_REINSTALL_DASHBOARD,
)
from custom_components.sax_power.dashboard import (
    DASHBOARD_URL_PATH,
    async_build_dashboard_config,
    async_check_dashboard_up_to_date,
    async_create_dashboard,
)

ENTRY_ID = "test_entry_id"
COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "sax_power"


def _register(hass, entity_domain: str, suffix: str) -> str:
    entry = er.async_get(hass).async_get_or_create(
        entity_domain, DOMAIN, f"{ENTRY_ID}_{suffix}"
    )
    return entry.entity_id


def _iter_cards(cards: list[dict[str, Any]]):
    """Läuft rekursiv durch eine beliebige Mischung aus entities-/tile-/
    gauge-/grid-Karten (siehe dashboard.py) und liefert jede Blattkarte
    (also nicht die grid-Container selbst)."""
    for card in cards:
        if card["type"] == "grid":
            yield from _iter_cards(card["cards"])
        else:
            yield card


def _iter_entity_ids(cards: list[dict[str, Any]]):
    """Sammelt alle referenzierten Entity-IDs."""
    for card in _iter_cards(cards):
        if card["type"] == "entities":
            for row in card["entities"]:
                yield row["entity"] if isinstance(row, dict) else row
        elif "entity" in card:
            yield card["entity"]


async def test_build_dashboard_config_resolves_registered_entities(hass) -> None:
    """Nur tatsächlich in der Entity Registry vorhandene Entities landen in
    den Karten; die fünf Tabs (Views) sind immer vorhanden."""
    soc_entity_id = _register(hass, "sensor", "soc")
    storage_switch_entity_id = _register(hass, "switch", "storage_switch")
    grid_serving_switch_entity_id = _register(hass, "switch", "grid_serving_enabled")
    price_switch_entity_id = _register(hass, "switch", "price_charge_enabled")
    calibration_active_id = _register(hass, "binary_sensor", "cell_calibration_active")
    next_calibration_id = _register(hass, "sensor", "next_cell_calibration")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    assert [view["path"] for view in config["views"]] == [
        "allgemein",
        "ladeautomatik",
        "netzdienliches-laden",
        "dynamisches-laden",
        "ersparnis",
    ]

    general_entities = set(_iter_entity_ids(config["views"][0]["cards"]))
    assert soc_entity_id in general_entities
    assert storage_switch_entity_id in general_entities
    assert calibration_active_id in general_entities
    assert next_calibration_id in general_entities

    grid_serving_entities = set(_iter_entity_ids(config["views"][2]["cards"]))
    assert grid_serving_switch_entity_id in grid_serving_entities

    price_entities = set(_iter_entity_ids(config["views"][3]["cards"]))
    assert price_switch_entity_id in price_entities


async def test_build_dashboard_config_soc_uses_gauge_card_with_segments(hass) -> None:
    """Der Ladezustand wird als Gauge-Karte mit Nadel dargestellt: grün ab
    50 % SOC, gelb ab 20 % SOC, darunter rot. Über "segments" statt
    "severity", damit rot/grün exakt dieselbe Farbe wie bei der
    Zelltemperatur-Gauge ergeben (siehe _gauge_card-Docstring in
    dashboard.py)."""
    soc_entity_id = _register(hass, "sensor", "soc")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    gauge_cards = [
        card
        for card in _iter_cards(config["views"][0]["cards"])
        if card["type"] == "gauge" and card["entity"] == soc_entity_id
    ]
    assert len(gauge_cards) == 1
    gauge = gauge_cards[0]
    assert gauge["needle"] is True
    assert gauge["segments"] == [
        {"from": 0, "color": "red"},
        {"from": 20, "color": "yellow"},
        {"from": 50, "color": "green"},
    ]


async def test_build_dashboard_config_temperature_uses_gauge_card_with_segments(
    hass,
) -> None:
    """Die Zelltemperatur wird ebenfalls als Gauge mit Nadel dargestellt:
    0-5 °C rot (zu kalt), 5-32 °C grün (normal), 32-40 °C rot (zu heiß) -
    ein nicht-monotones Farbmuster, das ein einfaches severity-Mapping
    nicht abbilden kann."""
    temp_entity_id = _register(hass, "sensor", "storage_max_cell_temp")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    gauge_cards = [
        card
        for card in _iter_cards(config["views"][0]["cards"])
        if card["type"] == "gauge" and card["entity"] == temp_entity_id
    ]
    assert len(gauge_cards) == 1
    gauge = gauge_cards[0]
    assert gauge["needle"] is True
    assert gauge["min"] == 0
    assert gauge["max"] == 40
    assert gauge["segments"] == [
        {"from": 0, "color": "red"},
        {"from": 5, "color": "green"},
        {"from": 32, "color": "red"},
    ]


async def test_build_dashboard_config_soc_and_temperature_gauges_share_red_and_green(
    hass,
) -> None:
    """Beide Gauges verwenden für rot/grün exakt dieselbe Farbangabe -
    ansonsten würde dieselbe Farbe je nach Gauge unterschiedlich aussehen
    (severity- vs. segments-Rendering, siehe _gauge_card-Docstring)."""
    soc_entity_id = _register(hass, "sensor", "soc")
    temp_entity_id = _register(hass, "sensor", "storage_max_cell_temp")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    gauges = {
        card["entity"]: card
        for card in _iter_cards(config["views"][0]["cards"])
        if card["type"] == "gauge"
    }
    for entity_id in (soc_entity_id, temp_entity_id):
        colors = {segment["color"] for segment in gauges[entity_id]["segments"]}
        assert {"red", "green"} <= colors


async def test_build_dashboard_config_entity_names_drop_device_prefix(hass) -> None:
    """Kartenzeilen zeigen nur den reinen Entity-Namen ("Ladezustand"),
    nicht den vollen, geräteweiten Anzeigenamen ("SAX Power Home
    Ladezustand")."""
    _register(hass, "sensor", "energy_charged")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    energy_card = next(
        card for card in config["views"][0]["cards"] if card.get("title") == "Energie"
    )
    row = energy_card["entities"][0]
    assert isinstance(row, dict)
    assert row["name"] == "Total energy charged"  # hass-Testfixture: Sprache "en"
    assert "SAX Power Home" not in row["name"]


async def test_build_dashboard_config_price_charge_card_labels_drop_prefix(
    hass,
) -> None:
    """Kartenzeilen der "Preisoptimiertes Laden"-Karte (Tab "Dynamisches
    Laden") tragen nicht mehr den Präfix "Preisoptimiertes Laden"/"Price-
    optimised charging" im Label - der Kartentitel gibt den Kontext bereits
    vor. Betrifft price_charge_strategy, price_charge_max_price,
    price_charge_hours, price_charge_active_text, price_charge_status_text
    und price_charge_next_start; price_charge_current_price und max_soc
    hatten nie einen solchen Präfix."""
    _register(hass, "select", "price_charge_strategy")
    _register(hass, "number", "price_charge_max_price")
    _register(hass, "number", "price_charge_hours")
    _register(hass, "sensor", "price_charge_active_text")
    _register(hass, "sensor", "price_charge_status_text")
    _register(hass, "sensor", "price_charge_next_start")
    _register(hass, "sensor", "price_charge_current_price")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    price_view = next(
        view for view in config["views"] if view["path"] == "dynamisches-laden"
    )
    price_card = next(
        card
        for card in price_view["cards"]
        if card.get("title") == "Preisoptimiertes Laden"
    )
    names = [row["name"] for row in price_card["entities"] if isinstance(row, dict)]
    assert names  # es gibt tatsächlich aufgelöste Zeilen zu prüfen
    for name in names:
        assert "price-optimised charging" not in name.lower()


def test_german_price_charge_labels_capitalize_laden() -> None:
    """REQ-BUNDLED-DASHBOARD: Laden wird in beiden Preislabels als
    substantivierter Infinitiv großgeschrieben."""
    for filename in ("strings.json", "translations/de.json"):
        with (COMPONENT_DIR / filename).open(encoding="utf-8") as handle:
            number_names = json.load(handle)["entity"]["number"]

        assert number_names["price_charge_max_price"]["name"] == (
            "Netzbezug und Laden bis"
        )
        assert number_names["price_charge_neutral_price"]["name"] == (
            "Netzbezug ohne Laden bis"
        )


async def test_price_charge_forecast_follows_status_with_dynamic_name(hass) -> None:
    """REQ-BUNDLED-DASHBOARD: Die PV-Prognose steht im Preis-Tab direkt
    unter Status und übernimmt dort ihren täglich aktualisierten Namen."""
    status = _register(hass, "sensor", "price_charge_status_text")
    forecast = _register(hass, "sensor", "grid_serving_forecast")
    next_start = _register(hass, "sensor", "price_charge_next_start")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    price_view = next(
        view for view in config["views"] if view["path"] == "dynamisches-laden"
    )
    price_card = next(
        card
        for card in price_view["cards"]
        if card.get("title") == "Preisoptimiertes Laden"
    )
    assert price_card["entities"] == [
        {"entity": status, "name": "Status"},
        {"entity": forecast},
        {"entity": next_start, "name": "Next start"},
    ]


async def test_build_dashboard_config_skips_cards_without_entities(hass) -> None:
    """Ohne registrierte Entity bleiben alle fünf Views vorhanden.

    Die ersten vier Views bleiben kartenlos; im Ersparnis-View bleiben der
    neutrale Status-Fallback und der statische Einordnungstext, aber keine
    leeren Entity-/Grid-Karten.
    """
    config = await async_build_dashboard_config(hass, "unbekannter_entry")

    assert len(config["views"]) == 5
    for view in config["views"][:4]:
        assert view["cards"] == []
    assert [card["type"] for card in config["views"][4]["cards"]] == [
        "markdown",
        "markdown",
    ]


async def test_build_dashboard_config_status_card_removed(hass) -> None:
    """Die frühere Karte "Status" im Tab "Allgemeine Informationen" wurde
    entfernt - die zugrunde liegenden binary_sensor-Entities existieren
    weiterhin (REQ-BINARY-SENSORS), landen aber in keiner Karte mehr."""
    battery_charging = _register(hass, "binary_sensor", "battery_charging")
    timed_charge_active = _register(hass, "binary_sensor", "timed_charge_active")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    assert not any(
        card.get("title") == "Status" for card in config["views"][0]["cards"]
    )
    general_entities = set(_iter_entity_ids(config["views"][0]["cards"]))
    assert battery_charging not in general_entities
    assert timed_charge_active not in general_entities


async def test_build_dashboard_config_smartmeter_power_uses_netzleistung_label(
    hass,
) -> None:
    """ "Netzleistung" (bisher "Smart Meter Leistung") ist eine ganz normale
    Zeile der "Leistung"-Karte, wie jede andere Sensor-Entity dort auch -
    kein Sonderfall mehr (siehe REQ-BUNDLED-DASHBOARD)."""
    smartmeter_power = _register(hass, "sensor", "smartmeter_power")
    charge_power = _register(hass, "sensor", "charge_power")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    leistung_card = next(
        card for card in config["views"][0]["cards"] if card.get("title") == "Leistung"
    )
    leistung_entities = {
        row["entity"] if isinstance(row, dict) else row
        for row in leistung_card["entities"]
    }
    assert charge_power in leistung_entities
    assert smartmeter_power in leistung_entities

    row = next(
        row
        for row in leistung_card["entities"]
        if isinstance(row, dict) and row["entity"] == smartmeter_power
    )
    assert row["name"] == "Grid power"  # hass-Testfixture: Sprache "en"


async def test_build_dashboard_config_geraet_card_drops_manufacturer_and_model(
    hass,
) -> None:
    """Die Karte "Gerät" zeigt "Hersteller" und "Gerätemodell" nicht mehr an -
    beide sind fest bekannt (SAX Power Home) und boten dort keinen
    Mehrwert."""
    sun_manufacturer = _register(hass, "sensor", "sun_manufacturer")
    sun_model = _register(hass, "sensor", "sun_model")
    sun_version_master = _register(hass, "sensor", "sun_version_master")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    geraet_card = next(
        card for card in config["views"][0]["cards"] if card.get("title") == "Gerät"
    )
    geraet_entities = {
        row["entity"] if isinstance(row, dict) else row
        for row in geraet_card["entities"]
    }
    assert sun_manufacturer not in geraet_entities
    assert sun_model not in geraet_entities
    assert sun_version_master in geraet_entities


async def test_geraet_card_shows_control_mode_after_storage_event(
    hass,
) -> None:
    """REQ-BUNDLED-DASHBOARD: Der Steuermodus folgt in der Gerätekarte
    unmittelbar auf das Speicher-Ereignis und verwendet sein kurzes Label."""
    storage_event = _register(hass, "sensor", "storage_event_text")
    control_mode = _register(hass, "sensor", "ic_control_mode_text")
    hass.config.language = "de"

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    geraet_card = next(
        card for card in config["views"][0]["cards"] if card.get("title") == "Gerät"
    )
    assert geraet_card["entities"] == [
        {"entity": storage_event, "name": "Speicher Ereignis"},
        {"entity": control_mode, "name": "Steuermodus"},
    ]


async def test_build_dashboard_config_storage_state_dropped_switch_kept(hass) -> None:
    """Die reine Zustands-Anzeige "Speicher Zustand" wird nicht mehr
    dargestellt, der Speicher-Schalter bleibt aber erhalten."""
    storage_state_entity_id = _register(hass, "sensor", "storage_state_text")
    storage_switch_entity_id = _register(hass, "switch", "storage_switch")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    general_entities = set(_iter_entity_ids(config["views"][0]["cards"]))
    assert storage_switch_entity_id in general_entities
    assert storage_state_entity_id not in general_entities


async def test_build_dashboard_config_grid_serving_view(hass) -> None:
    """REQ-BUNDLED-DASHBOARD: Ladepause bündelt alle relevanten Anzeigen."""
    grid_serving_switch = _register(hass, "switch", "grid_serving_enabled")
    grid_serving_start = _register(hass, "time", "grid_serving_start")
    grid_serving_end = _register(hass, "time", "grid_serving_end")
    forecast = _register(hass, "sensor", "grid_serving_forecast")
    forecast_threshold = _register(hass, "number", "grid_serving_forecast_threshold")
    pause_status = _register(hass, "sensor", "grid_serving_pause_status")
    month_switches = [
        _register(hass, "switch", f"grid_serving_month_{month}")
        for month in range(1, 13)
    ]

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    grid_serving_view = next(
        view for view in config["views"] if view["path"] == "netzdienliches-laden"
    )
    entities = set(_iter_entity_ids(grid_serving_view["cards"]))
    assert grid_serving_switch in entities
    assert grid_serving_start in entities
    assert grid_serving_end in entities
    assert forecast in entities
    assert forecast_threshold in entities
    assert pause_status in entities
    assert entities.issuperset(month_switches)

    pause_card = next(
        card for card in grid_serving_view["cards"] if card.get("title") == "Ladepause"
    )
    assert [row["entity"] for row in pause_card["entities"]] == [
        grid_serving_start,
        grid_serving_end,
        forecast,
        forecast_threshold,
        pause_status,
    ]
    assert [row.get("name") for row in pause_card["entities"]] == [
        "Start",
        "End",
        None,
        "Minimum PV forecast",
        "Status",
    ]
    assert not any(
        card.get("title") == "Einstellungen" for card in grid_serving_view["cards"]
    )

    months_card = next(
        card
        for card in grid_serving_view["cards"]
        if card.get("title") == "Aktive Monate"
    )
    assert {row["entity"] for row in months_card["entities"]} == set(month_switches)


async def test_build_dashboard_config_charging_view(hass) -> None:
    """Der Tab "Ladeautomatik" ist analog zu "Netzdienliches Laden"
    aufgebaut (Schalter, Zeitfenster-Karte, "Aktive Monate"-Karte), enthält
    aber weder die Max-SOC-Einstellung noch die Status-Textanzeige - der
    Schalter deckt deren Zustand bereits ab. Netzdienliche Entities landen
    nicht mehr in diesem Tab, die sind jetzt im eigenen Tab."""
    grid_serving_switch = _register(hass, "switch", "grid_serving_enabled")
    grid_serving_start = _register(hass, "time", "grid_serving_start")
    timed_charge_switch = _register(hass, "switch", "timed_charge_enabled")
    timed_charge_start = _register(hass, "time", "timed_charge_start")
    timed_charge_end = _register(hass, "time", "timed_charge_end")
    timed_charge_min_soc = _register(hass, "number", "timed_charge_min_soc")
    max_soc = _register(hass, "number", "max_soc")
    timed_charge_active_text = _register(hass, "sensor", "timed_charge_active_text")
    month_switches = [
        _register(hass, "switch", f"timed_charge_month_{month}")
        for month in range(1, 13)
    ]

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    charging_view = next(
        view for view in config["views"] if view["path"] == "ladeautomatik"
    )
    entities = set(_iter_entity_ids(charging_view["cards"]))
    assert timed_charge_switch in entities
    assert timed_charge_start in entities
    assert timed_charge_end in entities
    assert timed_charge_min_soc in entities
    assert entities.issuperset(month_switches)
    assert max_soc not in entities
    assert timed_charge_active_text not in entities
    assert grid_serving_switch not in entities
    assert grid_serving_start not in entities

    months_card = next(
        card for card in charging_view["cards"] if card.get("title") == "Aktive Monate"
    )
    assert {row["entity"] for row in months_card["entities"]} == set(month_switches)


async def test_build_dashboard_config_start_end_labels_are_generic(hass) -> None:
    """Die Zeitfenster-Entities heißen in beiden Tabs immer "Start" bzw.
    "Ende" (bzw. "Start"/"End" in der englischen Test-Sprache) statt
    tabspezifisch "Netzladung Start" oder "Netzdienliches Laden Start" -
    damit sehen beide Tabs vergleichbar aus. Die Karte selbst heißt bei
    "Ladeautomatik" weiterhin "Zeitfenster", bei "Netzdienliches Laden"
    aber "Ladepause" - dort verhindert das Zeitfenster das Laden, statt es
    auszulösen."""
    _register(hass, "time", "timed_charge_start")
    _register(hass, "time", "timed_charge_end")
    _register(hass, "time", "grid_serving_start")
    _register(hass, "time", "grid_serving_end")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    charging_view = next(
        view for view in config["views"] if view["path"] == "ladeautomatik"
    )
    grid_serving_view = next(
        view for view in config["views"] if view["path"] == "netzdienliches-laden"
    )

    for view, title in (
        (charging_view, "Zeitfenster"),
        (grid_serving_view, "Ladepause"),
    ):
        window_card = next(card for card in view["cards"] if card.get("title") == title)
        names = {row["entity"]: row["name"] for row in window_card["entities"]}
        assert set(names.values()) == {"Start", "End"}


async def test_build_dashboard_config_month_switch_labels_are_bare_month_names(
    hass,
) -> None:
    """Die Monats-Schalter zeigen nur noch den Monatsnamen (z. B. "January")
    statt "Netzladung aktiv im Januar" / "Netzdienliches Laden aktiv im
    Januar" - gilt für beide Tabs."""
    _register(hass, "switch", "timed_charge_month_1")
    _register(hass, "switch", "grid_serving_month_1")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    charging_view = next(
        view for view in config["views"] if view["path"] == "ladeautomatik"
    )
    grid_serving_view = next(
        view for view in config["views"] if view["path"] == "netzdienliches-laden"
    )

    for view in (charging_view, grid_serving_view):
        months_card = next(
            card for card in view["cards"] if card.get("title") == "Aktive Monate"
        )
        assert months_card["entities"][0]["name"] == "January"


# ===========================================================================
# Tab "Ersparnis" (REQ-ECONOMICS-SAVINGS-DASHBOARD)
# ===========================================================================
def _savings_view(config: dict[str, Any]) -> dict[str, Any]:
    return next(view for view in config["views"] if view["path"] == "ersparnis")


def _savings_status_card(view: dict[str, Any]) -> dict[str, Any]:
    return next(
        card
        for card in view["cards"]
        if card["type"] == "markdown"
        and card.get("show_empty") is False
        and "status_entity" in card.get("content", "")
    )


def _savings_explanation_card(view: dict[str, Any]) -> dict[str, Any]:
    return next(
        card
        for card in view["cards"]
        if card["type"] == "markdown" and "<details>" in card["content"]
    )


async def test_savings_status_hint_is_last_and_renders_every_state(hass) -> None:
    missing_config = await async_build_dashboard_config(hass, ENTRY_ID)
    missing_view = _savings_view(missing_config)
    missing_card = _savings_status_card(missing_view)
    assert missing_card == missing_view["cards"][-1]
    assert missing_card["type"] == "markdown"
    assert missing_card["show_empty"] is False
    assert "set status_entity = none" in missing_card["content"]
    missing_rendered = template.Template(missing_card["content"], hass).async_render(
        parse_result=False
    )
    assert missing_rendered == (
        "Die Wirtschaftlichkeitsdaten sind momentan nicht verfügbar."
    )

    status = _register(hass, "sensor", "economics_status")
    config = await async_build_dashboard_config(hass, ENTRY_ID)
    view = _savings_view(config)
    card = _savings_status_card(view)
    assert card == view["cards"][-1]
    assert card["type"] == "markdown"
    assert card["show_empty"] is False
    assert repr(status) in card["content"]

    messages = {
        "active": "",
        "disabled": (
            "Die Wirtschaftlichkeitsberechnung ist deaktiviert. Bitte unter "
            "„Geräte & Dienste → SAX Power Home → Konfigurieren → "
            "Wirtschaftlichkeit“ konfigurieren."
        ),
        "waiting_for_initial_state": (
            "Die Wirtschaftlichkeitsberechnung wartet auf Speicherkapazität "
            "und Ladezustand."
        ),
        "price_unavailable": (
            "Der Strompreis ist derzeit nicht verfügbar. Aktuelle Zeitraumwerte "
            "können unvollständig sein."
        ),
        "origin_unavailable": (
            "Die Herkunft der Ladeenergie ist derzeit nicht bestimmbar."
        ),
        "partial_price_coverage": (
            "Für einen Teil der Energie fehlte heute ein Preis. Das Ergebnis "
            "kann unvollständig sein."
        ),
        "storage_error": (
            "Die Wirtschaftlichkeitsbilanz ist wegen eines Speicherfehlers "
            "angehalten. Bitte die **Home-Assistant-Reparaturen** prüfen."
        ),
        "unknown": "Die Wirtschaftlichkeitsdaten sind momentan nicht verfügbar.",
        "unavailable": ("Die Wirtschaftlichkeitsdaten sind momentan nicht verfügbar."),
        "future_status": (
            "Die Wirtschaftlichkeitsdaten sind momentan nicht verfügbar."
        ),
    }
    for status_state, message in messages.items():
        hass.states.async_set(status, status_state)

        rendered = template.Template(card["content"], hass).async_render(
            parse_result=False
        )

        assert rendered == message, status_state


async def test_savings_inventory_is_merged_into_explanation_and_renders_sensor_value(
    hass,
) -> None:
    status = _register(hass, "sensor", "economics_status")
    _register(hass, "sensor", "economics_net_savings")
    inventory = _register(hass, "sensor", "economics_unvalued_inventory")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    view = _savings_view(config)
    card = _savings_explanation_card(view)
    grid = next(candidate for candidate in view["cards"] if candidate["type"] == "grid")
    free_period = _savings_free_period_block(view)
    assert view["cards"].index(free_period) > view["cards"].index(grid)
    assert view["cards"].index(card) == view["cards"].index(free_period) + 1
    assert not any(
        candidate["type"] == "conditional"
        and candidate["conditions"][0].get("condition") == "numeric_state"
        for candidate in view["cards"]
    )
    content = card["content"]
    assert repr(inventory) in content

    rendered = template.Template(content, hass).async_render(parse_result=False)
    assert "Beim Start der Bilanz" not in rendered
    for state in ("0", "-0.001", "unknown", "unavailable"):
        hass.states.async_set(
            inventory,
            state,
            {"unit_of_measurement": "kWh"},
        )
        rendered = template.Template(content, hass).async_render(parse_result=False)
        assert "Beim Start der Bilanz" not in rendered, state

    hass.states.async_set(
        inventory,
        "1.23456",
        {"unit_of_measurement": "kWh"},
    )
    rendered = template.Template(content, hass).async_render(parse_result=False)
    normalized = " ".join(rendered.split())
    assert (
        "<p>Beim Start der Bilanz waren bereits <strong>1,235 kWh</strong> "
        "im Speicher. Für diese Energie sind Herkunft und Preis unbekannt. "
        "Ihre Entladung wird deshalb korrekt mit <strong>0 €</strong> bewertet. "
        "Sobald dieser Anfangsbestand abgebaut ist, kann weitere bepreiste "
        "Entladung in die Netto-Ersparnis eingehen. Das ist kein Messfehler.</p>"
        in normalized
    )

    hass.states.async_set(status, "active")
    hass.states.async_set(
        inventory,
        "0",
        {"unit_of_measurement": "kWh"},
    )
    assert (
        template.Template(_savings_status_card(view)["content"], hass).async_render(
            parse_result=False
        )
        == ""
    )
    assert "Beim Start der Bilanz" not in template.Template(content, hass).async_render(
        parse_result=False
    )


async def test_savings_explanation_handles_missing_inventory_entity(
    hass,
) -> None:
    _register(hass, "sensor", "economics_net_savings")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    view = _savings_view(config)
    assert not any(
        card["type"] == "conditional"
        and card["conditions"][0].get("condition") == "numeric_state"
        for card in view["cards"]
    )
    content = _savings_explanation_card(view)["content"]
    assert "set inventory_entity = none" in content
    rendered = template.Template(content, hass).async_render(parse_result=False)
    assert "<details>" in rendered
    assert "Beim Start der Bilanz" not in rendered


async def test_savings_inventory_explanation_remains_available_without_result_entity(
    hass,
) -> None:
    inventory = _register(hass, "sensor", "economics_unvalued_inventory")
    hass.states.async_set(inventory, "2", {"unit_of_measurement": "kWh"})

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    content = _savings_explanation_card(_savings_view(config))["content"]
    rendered = template.Template(content, hass).async_render(parse_result=False)
    assert "Beim Start der Bilanz waren bereits <strong>2,000 kWh</strong>" in (
        " ".join(rendered.split())
    )


async def test_savings_view_is_fifth_with_expected_title_and_icon(hass) -> None:
    config = await async_build_dashboard_config(hass, ENTRY_ID)

    assert config["views"][4] == _savings_view(config)
    assert config["views"][4]["title"] == "Ersparnis"
    assert config["views"][4]["icon"] == "mdi:cash-multiple"


async def test_savings_view_uses_requested_card_order(hass) -> None:
    _register(hass, "binary_sensor", "economics_investment_configured")
    _register(hass, "sensor", "economics_amortization_progress")
    _register(hass, "sensor", "economics_net_savings")
    _register(hass, "sensor", "economics_current_import_price")
    _register(hass, "sensor", "economics_status")
    _register(hass, "sensor", "economics_unvalued_inventory")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    cards = _savings_view(config)["cards"]
    assert len(cards) == 6
    assert cards[0]["type"] == "vertical-stack"
    assert cards[0]["cards"][0]["type"] == "conditional"
    assert cards[1]["type"] == "grid"
    assert cards[2] == _tariff_plan_card(_savings_view(config))
    assert cards[3]["type"] == "vertical-stack"
    assert any(
        nested["type"] == "energy-date-selection" for nested in cards[3]["cards"]
    )
    assert cards[4] == _savings_explanation_card(_savings_view(config))
    assert cards[5] == _savings_status_card(_savings_view(config))


async def test_savings_view_uses_exact_calendar_statistics(hass) -> None:
    result = _register(hass, "sensor", "economics_net_savings")
    result_today = _register(hass, "sensor", "economics_net_savings_today")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    view = _savings_view(config)
    grid = next(card for card in view["cards"] if card["type"] == "grid")
    assert grid["columns"] == 2
    assert grid["square"] is False
    assert grid["cards"] == [
        {
            "type": "statistic",
            "entity": result,
            "name": name,
            "stat_type": "change",
            "period": {"calendar": {"period": period}},
        }
        for name, period in (
            ("Heute bisher", "day"),
            ("Diese Woche bisher", "week"),
            ("Dieser Monat bisher", "month"),
            ("Dieses Jahr bisher", "year"),
        )
    ]
    assert result_today not in json.dumps(view)
    assert "offset" not in json.dumps(grid)


async def test_savings_view_places_prior_result_directly_below_remaining(hass) -> None:
    result = _register(hass, "sensor", "economics_net_savings")
    status = _register(hass, "sensor", "economics_status")
    configured = _register(hass, "binary_sensor", "economics_investment_configured")
    _register(hass, "sensor", "economics_amortization_progress")
    remaining = _register(hass, "sensor", "economics_remaining_to_payback")
    roi = _register(hass, "sensor", "economics_roi")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    view = _savings_view(config)
    block = _savings_payback_block(view)
    assert block["cards"][1]["conditions"] == [{"entity": configured, "state": "on"}]
    details = _configured_payback_stack(block)["cards"][1]
    assert details["type"] == "entities"
    assert details["state_color"] is True
    assert details["entities"][0]["entity"] == remaining
    assert details["entities"][1:] == [
        {
            "type": "attribute",
            "entity": roi,
            "attribute": "prior_result_eur",
            "name": "Bereits vor Bilanzbeginn berücksichtigt",
            "suffix": "€",
        },
        {"entity": result, "name": "Netto-Ersparnis"},
        {
            "type": "attribute",
            "entity": status,
            "attribute": "economics_started_at",
            "name": "Bilanzbeginn",
        },
    ]
    assert not any(
        card.get("title") == "Gesamt seit Bilanzbeginn" for card in view["cards"]
    )
    assert "fixed_period" not in json.dumps(view)


async def test_savings_view_collapses_static_explanations_into_one_control(
    hass,
) -> None:
    _register(hass, "sensor", "economics_net_savings")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    view = _savings_view(config)
    card = _savings_explanation_card(view)
    assert card["type"] == "markdown"
    content = card["content"]
    assert content.startswith("<details>\n<summary>")
    assert content.endswith("</details>\n")
    assert "<details open" not in content
    assert content.count("<details>") == 1
    assert content.count("</details>") == 1
    assert content.count("<summary>") == 1
    assert content.count("</summary>") == 1
    assert json.dumps(view).count("<details>") == 1
    assert json.dumps(view).count("</details>") == 1
    assert "Hinweise zur Berechnung und Datenbasis" in content
    assert "Netto-Ersparnis:" in content
    assert "gespeicherter, nichtnegativer Höchststand" in content
    assert "Recorder-Langzeitstatistik der Netto-Ersparnis" in content
    assert "jünger als der angezeigte Bilanzbeginn" in content
    assert "Freier Zeitraum:" in content
    assert "Eine frühere Auswahl erfindet keine Werte" in content
    assert "vom Recorder ausgeschlossen" in content
    assert "unbekannt beziehungsweise leer" in content
    assert "manuellen Neustart" in content
    assert "positiven Zuwächse vor und nach dem Neustart" in content

    explanatory_cards = [
        card["content"]
        for card in view["cards"]
        if card["type"] == "markdown"
        and "Recorder-Langzeitstatistik" in card["content"]
    ]
    assert explanatory_cards == [content]


async def test_savings_view_omits_data_cards_without_result_entity(hass) -> None:
    _register(hass, "sensor", "economics_status")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    view = _savings_view(config)
    assert [card["type"] for card in view["cards"]] == ["markdown", "markdown"]
    assert not any(card["type"] == "grid" for card in view["cards"])
    assert not any(
        card.get("title") == "Gesamt seit Bilanzbeginn" for card in view["cards"]
    )


def _savings_free_period_block(view: dict[str, Any]) -> dict[str, Any]:
    return next(
        card
        for card in view["cards"]
        if card["type"] == "vertical-stack"
        and any(nested["type"] == "energy-date-selection" for nested in card["cards"])
    )


async def test_savings_free_period_cards_share_the_exact_collection_key(
    hass,
) -> None:
    result = _register(hass, "sensor", "economics_net_savings")
    _register(hass, "sensor", "economics_avoided_grid_cost")
    _register(hass, "sensor", "economics_grid_charge_cost")
    _register(hass, "sensor", "economics_pv_opportunity_cost")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    block = _savings_free_period_block(_savings_view(config))
    assert [card["type"] for card in block["cards"]] == [
        "energy-date-selection",
        "statistic",
        "statistics-graph",
    ]
    selection, statistic, graph = block["cards"]
    assert selection == {
        "type": "energy-date-selection",
        "collection_key": "energy_sax_power_savings",
        "disable_compare": True,
    }
    assert statistic == {
        "type": "statistic",
        "entity": result,
        "name": "Netto-Ersparnis im gewählten Zeitraum",
        "period": "energy_date_selection",
        "stat_type": "change",
        "collection_key": "energy_sax_power_savings",
    }
    assert graph == {
        "type": "statistics-graph",
        "title": "Verlauf im gewählten Zeitraum",
        "entities": [result],
        "stat_types": ["change"],
        "chart_type": "bar",
        "energy_date_selection": True,
        "collection_key": "energy_sax_power_savings",
    }
    assert "period" not in graph


async def test_savings_free_period_has_no_separate_heading(hass) -> None:
    _register(hass, "sensor", "economics_net_savings")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    block = _savings_free_period_block(_savings_view(config))
    assert block["cards"][0]["type"] == "energy-date-selection"
    assert "### Freier Zeitraum" not in json.dumps(block)


async def test_savings_free_period_is_fully_omitted_without_result_entity(
    hass,
) -> None:
    _register(hass, "sensor", "economics_status")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    serialized = json.dumps(_savings_view(config))
    assert "energy-date-selection" not in serialized
    assert "energy_sax_power_savings" not in serialized
    assert "Verlauf im gewählten Zeitraum" not in serialized


def _savings_payback_block(view: dict[str, Any]) -> dict[str, Any]:
    return next(
        card
        for card in view["cards"]
        if card["type"] == "vertical-stack"
        and card["cards"][0].get("type") == "conditional"
        and "Amortisationswerte" in card["cards"][0].get("card", {}).get("content", "")
    )


def _configured_payback_stack(block: dict[str, Any]) -> dict[str, Any]:
    return next(
        card["card"]
        for card in block["cards"]
        if card["type"] == "conditional" and card["conditions"][0].get("state") == "on"
    )


async def test_savings_payback_block_uses_runtime_investment_gate(hass) -> None:
    configured = _register(hass, "binary_sensor", "economics_investment_configured")
    progress = _register(hass, "sensor", "economics_amortization_progress")
    remaining = _register(hass, "sensor", "economics_remaining_to_payback")
    roi = _register(hass, "sensor", "economics_roi")
    result = _register(hass, "sensor", "economics_net_savings")
    status = _register(hass, "sensor", "economics_status")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    view = _savings_view(config)
    block = _savings_payback_block(view)
    free_period = _savings_free_period_block(view)
    assert view["cards"].index(block) < view["cards"].index(free_period)
    assert [card["type"] for card in block["cards"]] == [
        "conditional",
        "conditional",
    ]
    disabled, enabled = block["cards"]
    assert disabled["conditions"] == [{"entity": configured, "state": "off"}]
    assert disabled["card"] == {
        "type": "markdown",
        "content": (
            "Für die Amortisationswerte bitte die Investitionskosten "
            "unter „Geräte & Dienste → SAX Power Home → Konfigurieren → "
            "Wirtschaftlichkeit“ hinterlegen."
        ),
    }
    assert enabled["conditions"] == [{"entity": configured, "state": "on"}]

    stack = enabled["card"]
    assert [card["type"] for card in stack["cards"]] == ["gauge", "entities"]
    gauge = stack["cards"][0]
    assert gauge["entity"] == progress
    assert gauge["min"] == 0
    assert gauge["max"] == 100
    assert gauge["segments"] == [{"from": 0, "color": "blue"}]
    assert [row["entity"] for row in stack["cards"][1]["entities"]] == [
        remaining,
        roi,
        result,
        status,
    ]
    assert stack["cards"][1]["entities"][1] == {
        "type": "attribute",
        "entity": roi,
        "attribute": "prior_result_eur",
        "name": "Bereits vor Bilanzbeginn berücksichtigt",
        "suffix": "€",
    }


async def test_savings_payback_block_is_omitted_without_investment_gate(
    hass,
) -> None:
    _register(hass, "sensor", "economics_amortization_progress")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    assert not any(
        card["type"] == "vertical-stack"
        and any(nested.get("type") == "conditional" for nested in card["cards"])
        for card in _savings_view(config)["cards"]
    )


async def test_create_dashboard_skipped_without_lovelace(hass) -> None:
    """Ohne geladene Lovelace-Komponente (z. B. in den meisten Unit-Tests)
    darf async_create_dashboard nicht fehlschlagen, sondern nur überspringen."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)

    assert LOVELACE_DATA not in hass.data
    await async_create_dashboard(hass, entry)  # darf nicht raisen


async def test_create_dashboard_registers_panel_and_is_idempotent(hass) -> None:
    """Legt das Dashboard an, macht es über hass.data[LOVELACE_DATA] sowie
    als Sidebar-Panel sichtbar, und erzeugt es bei einem zweiten Aufruf
    nicht erneut."""
    _register(hass, "sensor", "soc")
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)

    hass.data[LOVELACE_DATA] = LovelaceData(
        resource_mode="storage",
        dashboards={},
        resources=None,
        yaml_dashboards={},
    )

    with patch(
        "custom_components.sax_power.dashboard.frontend.async_register_built_in_panel"
    ) as mock_register_panel:
        await async_create_dashboard(hass, entry)

        assert DASHBOARD_URL_PATH in hass.data[LOVELACE_DATA].dashboards
        dashboard_storage = hass.data[LOVELACE_DATA].dashboards[DASHBOARD_URL_PATH]
        saved_config = await dashboard_storage.async_load(False)
        assert len(saved_config["views"]) == 5
        mock_register_panel.assert_called_once()
        assert (
            mock_register_panel.call_args.kwargs["frontend_url_path"]
            == DASHBOARD_URL_PATH
        )

        await async_create_dashboard(hass, entry)
        mock_register_panel.assert_called_once()  # kein zweiter Aufruf


async def test_create_dashboard_force_overwrites_existing_config(hass) -> None:
    """force=True (Reinstall-Button, siehe button.py) überschreibt ein
    bereits bestehendes Dashboard mit der aktuell gebauten Konfiguration,
    registriert das Panel dabei aber nicht erneut."""
    _register(hass, "sensor", "soc")
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)

    hass.data[LOVELACE_DATA] = LovelaceData(
        resource_mode="storage",
        dashboards={},
        resources=None,
        yaml_dashboards={},
    )

    with patch(
        "custom_components.sax_power.dashboard.frontend.async_register_built_in_panel"
    ) as mock_register_panel:
        await async_create_dashboard(hass, entry)
        dashboard_storage = hass.data[LOVELACE_DATA].dashboards[DASHBOARD_URL_PATH]
        await dashboard_storage.async_save({"views": []})  # simuliert manuelle Änderung

        await async_create_dashboard(hass, entry, force=True)

        saved_config = await dashboard_storage.async_load(False)
        assert len(saved_config["views"]) == 5
        mock_register_panel.assert_called_once()  # weiterhin kein zweiter Panel-Aufruf


async def test_create_dashboard_swallows_unexpected_errors(hass) -> None:
    """Ein Fehler beim Anlegen (z. B. durch eine künftige Home-Assistant-
    Änderung an den genutzten Lovelace-Interna) darf niemals nach außen
    dringen - siehe Docstring von async_create_dashboard."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)

    hass.data[LOVELACE_DATA] = LovelaceData(
        resource_mode="storage",
        dashboards={},
        resources=None,
        yaml_dashboards={},
    )

    with patch(
        "custom_components.sax_power.dashboard.lovelace_dashboard.DashboardsCollection",
        side_effect=RuntimeError("Lovelace-Interna haben sich geändert"),
    ):
        await async_create_dashboard(hass, entry)  # darf nicht raisen


async def test_create_dashboard_service_creates_dashboard_for_device(hass) -> None:
    """Der Service sax_power.create_dashboard erlaubt, das Dashboard
    nachträglich anzulegen - z. B. wenn es in der Ersteinrichtung abgewählt
    wurde oder der Eintrag vor Einführung dieses Features angelegt wurde."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[ENTRY_ID] = {DATA_COORDINATOR: object()}
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=ENTRY_ID, identifiers={(DOMAIN, ENTRY_ID)}
    )

    hass.data[LOVELACE_DATA] = LovelaceData(
        resource_mode="storage",
        dashboards={},
        resources=None,
        yaml_dashboards={},
    )
    sax_power._async_register_services(hass)

    with patch(
        "custom_components.sax_power.dashboard.frontend.async_register_built_in_panel"
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CREATE_DASHBOARD,
            {"device_id": device.id},
            blocking=True,
        )

    assert DASHBOARD_URL_PATH in hass.data[LOVELACE_DATA].dashboards


async def test_reinstall_dashboard_service_resets_existing_dashboard_for_device(
    hass,
) -> None:
    """Der Service sax_power.reinstall_dashboard setzt ein bereits
    bestehendes, zwischenzeitlich manuell verändertes Dashboard auf den
    Auslieferungszustand zurück - Ersatz für die frühere, auf der
    Geräteseite unzuverlässig sichtbare Reinstall-ButtonEntity."""
    _register(hass, "sensor", "soc")
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[ENTRY_ID] = {DATA_COORDINATOR: object()}
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=ENTRY_ID, identifiers={(DOMAIN, ENTRY_ID)}
    )

    hass.data[LOVELACE_DATA] = LovelaceData(
        resource_mode="storage",
        dashboards={},
        resources=None,
        yaml_dashboards={},
    )
    sax_power._async_register_services(hass)

    with patch(
        "custom_components.sax_power.dashboard.frontend.async_register_built_in_panel"
    ) as mock_register_panel:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CREATE_DASHBOARD,
            {"device_id": device.id},
            blocking=True,
        )
        dashboard_storage = hass.data[LOVELACE_DATA].dashboards[DASHBOARD_URL_PATH]
        await dashboard_storage.async_save({"views": []})  # simuliert manuelle Änderung

        await hass.services.async_call(
            DOMAIN,
            SERVICE_REINSTALL_DASHBOARD,
            {"device_id": device.id},
            blocking=True,
        )

        saved_config = await dashboard_storage.async_load(False)
        assert len(saved_config["views"]) == 5
        mock_register_panel.assert_called_once()  # kein zweiter Panel-Aufruf


# --------------------------------------------------------------------------
# Tarifplan-Karte (REQ-ECONOMICS-SAVINGS-DASHBOARD)
# --------------------------------------------------------------------------
def _tariff_plan_card(view: dict[str, Any]) -> dict[str, Any] | None:
    """Die Markdown-Karte, die den Tarifplan rendert.

    Bewusst KEINE "conditional"-Karte: deren Bedingungen können nur den
    Zustand einer Entity prüfen, nie ein Attribut (#139). Die Karte
    entscheidet stattdessen selbst, ob sie etwas ausgibt.
    """
    return next(
        (
            card
            for card in view["cards"]
            if card["type"] == "markdown" and "tariff_type" in card.get("content", "")
        ),
        None,
    )


async def test_savings_view_tariff_plan_card_is_gated_by_tariff_type(hass) -> None:
    """Der Preis-Sensor existiert bei jeder Tarifart; ein Tagesplan ergibt
    aber nur beim tageszeitabhängigen Tarif Sinn. Die Karte entscheidet das
    zur Laufzeit selbst: Bei jeder anderen Tarifart rendert die Vorlage zu
    einer leeren Zeichenkette, und show_empty blendet die Karte dann aus.
    Eine "conditional"-Karte kann das nicht leisten - ihre Bedingungen
    prüfen nur den Zustand einer Entity, nie ein Attribut (#139)."""
    _register(hass, "sensor", "economics_current_import_price")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    card = _tariff_plan_card(_savings_view(config))
    assert card is not None
    assert card["type"] == "markdown"
    assert card["show_empty"] is False
    # Ein Kartentitel bliebe als leerer Kasten stehen - die Überschrift
    # gehört deshalb in den bedingten Teil des Inhalts.
    assert "title" not in card
    assert "### Tarifplan" in card["content"]


async def test_savings_view_tariff_plan_card_reads_only_sensor_attributes(
    hass,
) -> None:
    """Die Karte darf keine eigene Kopie der Tarifkonfiguration enthalten -
    sonst zeigte sie nach einer Options-Änderung veraltete Preise, ohne
    dass das jemand bemerkt."""
    price = _register(hass, "sensor", "economics_current_import_price")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    content = _tariff_plan_card(_savings_view(config))["content"]
    assert f"'{price}'" in content
    for attribute in (
        "tariff_type",
        "windows",
        "active_window",
        "base_price_eur_kwh",
        "next_price_change_at",
    ):
        assert f"'{attribute}'" in content


async def test_savings_view_tariff_plan_card_omitted_without_price_sensor(
    hass,
) -> None:
    """Ohne registrierten Preis-Sensor hat die Karte keine Datenquelle."""
    _register(hass, "sensor", "economics_status")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    assert _tariff_plan_card(_savings_view(config)) is None


async def test_savings_view_tariff_plan_card_renders_a_table(hass) -> None:
    """Die Vorlage wird hier wirklich gerendert, nicht nur auf Zeichenketten
    geprüft. Genau diese Lücke - Code, den nur das Frontend je ausführt -
    hat in #135 dafür gesorgt, dass eine unbrauchbare Konfigurationsseite
    mit grüner Testsuite ausgeliefert wurde."""
    # timestamp_custom rechnet in die lokale Zeitzone von Home Assistant um;
    # der Coordinator liefert den Zeitstempel bereits als Ortszeit, beide
    # müssen für eine nachvollziehbare Erwartung dieselbe Zone meinen.
    await hass.config.async_set_time_zone("Europe/Berlin")
    price = _register(hass, "sensor", "economics_current_import_price")
    hass.states.async_set(
        price,
        "0.21",
        {
            "tariff_type": "time_of_use",
            "windows": [
                {"start": "06:00:00", "end": "08:00:00", "price_eur_kwh": 0.41},
                {"start": "22:00:00", "end": "06:00:00", "price_eur_kwh": 0.21},
            ],
            "active_window": {
                "start": "22:00:00",
                "end": "06:00:00",
                "price_eur_kwh": 0.21,
            },
            "base_price_eur_kwh": 0.30,
            "next_price_change_at": "2026-03-11T06:00:00+01:00",
        },
    )

    config = await async_build_dashboard_config(hass, ENTRY_ID)
    content = _tariff_plan_card(_savings_view(config))["content"]
    rendered = template.Template(content, hass).async_render(parse_result=False)

    lines = [line for line in rendered.splitlines() if line.startswith("|")]
    # Kopfzeile, Trennzeile, zwei Fenster, Grundpreis.
    assert len(lines) == 5
    assert lines[2] == "|  | 06:00 | 08:00 | 0.4100 EUR/kWh |"
    assert lines[3] == "| **jetzt** | 22:00 | 06:00 | 0.2100 EUR/kWh |"
    assert lines[4].endswith("0.3000 EUR/kWh (Grundpreis) |")
    assert "**jetzt**" not in lines[4]
    assert "Nächster Preiswechsel: 06:00 Uhr" in rendered


async def test_savings_view_tariff_plan_card_marks_the_base_price(hass) -> None:
    """Außerhalb aller Fenster gilt der Grundpreis - dann trägt seine Zeile
    die Markierung, und ohne bekannten nächsten Wechsel entfällt der
    Hinweis darunter ersatzlos."""
    price = _register(hass, "sensor", "economics_current_import_price")
    hass.states.async_set(
        price,
        "0.30",
        {
            "tariff_type": "time_of_use",
            "windows": [
                {"start": "22:00:00", "end": "06:00:00", "price_eur_kwh": 0.21}
            ],
            "active_window": None,
            "base_price_eur_kwh": 0.30,
            "next_price_change_at": None,
        },
    )

    config = await async_build_dashboard_config(hass, ENTRY_ID)
    content = _tariff_plan_card(_savings_view(config))["content"]
    rendered = template.Template(content, hass).async_render(parse_result=False)

    lines = [line for line in rendered.splitlines() if line.startswith("|")]
    assert lines[3] == "| **jetzt** | – | – | 0.3000 EUR/kWh (Grundpreis) |"
    assert "**jetzt**" not in lines[2]
    assert "Preiswechsel" not in rendered


async def test_savings_view_tariff_plan_card_survives_missing_attributes(
    hass,
) -> None:
    """Zwischen Neustart und erstem Coordinator-Tick trägt der Sensor noch
    keine Attribute. Eine Vorlage, die dabei eine Exception wirft, zeigt im
    Dashboard nur eine rote Fehlerkarte - hier bleibt sie stattdessen leer
    und die Karte blendet sich aus."""
    price = _register(hass, "sensor", "economics_current_import_price")
    hass.states.async_set(price, "unknown", {})

    config = await async_build_dashboard_config(hass, ENTRY_ID)
    content = _tariff_plan_card(_savings_view(config))["content"]
    rendered = template.Template(content, hass).async_render(parse_result=False)

    assert rendered.strip() == ""


async def test_savings_view_tariff_plan_card_is_empty_for_other_tariffs(
    hass,
) -> None:
    """Ein Festpreis hat keinen Tagesplan: Die Vorlage rendert zu einer
    leeren Zeichenkette, damit show_empty die Karte ausblenden kann."""
    price = _register(hass, "sensor", "economics_current_import_price")
    hass.states.async_set(
        price,
        "0.30",
        {
            "tariff_type": "fixed",
            "windows": None,
            "active_window": None,
            "base_price_eur_kwh": None,
            "next_price_change_at": None,
            "unavailable_reason": None,
        },
    )

    config = await async_build_dashboard_config(hass, ENTRY_ID)
    content = _tariff_plan_card(_savings_view(config))["content"]
    rendered = template.Template(content, hass).async_render(parse_result=False)

    assert rendered.strip() == ""


async def test_savings_view_tariff_plan_card_marks_nothing_without_a_price(
    hass,
) -> None:
    """Gilt gerade kein Preis, ist auch `active_window` None - ohne
    zusätzliche Abfrage von `unavailable_reason` träfe die Markierung
    "jetzt" dann fälschlich den Grundpreis (Review-Befund). Stattdessen
    nennt die Karte den Grund."""
    price = _register(hass, "sensor", "economics_current_import_price")
    hass.states.async_set(
        price,
        "unknown",
        {
            "tariff_type": "time_of_use",
            "windows": [
                {"start": "22:00:00", "end": "06:00:00", "price_eur_kwh": 0.21}
            ],
            "active_window": None,
            "unavailable_reason": "tariff_incomplete",
            "base_price_eur_kwh": None,
            "next_price_change_at": None,
        },
    )

    config = await async_build_dashboard_config(hass, ENTRY_ID)
    content = _tariff_plan_card(_savings_view(config))["content"]
    rendered = template.Template(content, hass).async_render(parse_result=False)

    assert "**jetzt**" not in rendered
    assert "Derzeit gilt kein Preis (tariff_incomplete)" in rendered
    # Die Fensterliste bleibt sichtbar - genau sie braucht der Anwender,
    # um den Konfigurationsfehler zu finden.
    assert "| 22:00 | 06:00 | 0.2100 EUR/kWh |" in rendered


# --------------------------------------------------------------------------
# Hinweis auf ein veraltetes Dashboard (#138)
# --------------------------------------------------------------------------
def _lovelace(hass) -> None:
    hass.data[LOVELACE_DATA] = LovelaceData(
        resource_mode="storage", dashboards={}, resources=None, yaml_dashboards={}
    )


async def _existing_dashboard(hass, entry) -> Any:
    """Legt das Dashboard an und gibt seinen Storage zurück."""
    with patch(
        "custom_components.sax_power.dashboard.frontend.async_register_built_in_panel"
    ):
        await async_create_dashboard(hass, entry)
    return hass.data[LOVELACE_DATA].dashboards[DASHBOARD_URL_PATH]


def _issue(hass, entry_id: str):
    return ir.async_get(hass).async_get_issue(
        DOMAIN, f"{ISSUE_DASHBOARD_OUTDATED}_{entry_id}"
    )


def _replace_dashboard_values(node: Any, replacements: dict[str, str]) -> Any:
    if isinstance(node, dict):
        return {
            key: _replace_dashboard_values(value, replacements)
            for key, value in node.items()
        }
    if isinstance(node, list):
        return [_replace_dashboard_values(value, replacements) for value in node]
    return replacements.get(node, node) if isinstance(node, str) else node


async def test_outdated_dashboard_is_reported(hass) -> None:
    """Das Dashboard wird nur bei der Ersteinrichtung gebaut. Ergänzt eine
    neuere Version einen Tab, fehlt er einem bestehenden Dashboard
    stillschweigend - ohne diesen Hinweis erfährt der Anwender davon nie
    (Anwenderbericht zu #138)."""
    _register(hass, "sensor", "soc")
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    _lovelace(hass)
    storage = await _existing_dashboard(hass, entry)

    # Ein Dashboard aus einer Version, die den Ersparnis-Tab noch nicht kannte.
    stored = await storage.async_load(False)
    await storage.async_save(
        {"views": [v for v in stored["views"] if v["path"] != "ersparnis"]}
    )

    await async_check_dashboard_up_to_date(hass, entry)

    issue = _issue(hass, ENTRY_ID)
    assert issue is not None
    assert issue.is_fixable
    assert issue.translation_placeholders["views"] == "Ersparnis"


async def test_dashboard_with_removed_economics_view_is_reported(hass) -> None:
    """Der alte technische View löst eine bewusste Neuinstallation aus."""
    _register(hass, "sensor", "soc")
    _register(hass, "sensor", "economics_net_savings")
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    _lovelace(hass)
    storage = await _existing_dashboard(hass, entry)
    stored = await storage.async_load(False)
    stored["views"].insert(
        4,
        {
            "title": "Wirtschaftlichkeit",
            "path": "wirtschaftlichkeit",
            "icon": "mdi:cash-multiple",
            "cards": [],
        },
    )
    await storage.async_save(stored)

    await async_check_dashboard_up_to_date(hass, entry)

    issue = _issue(hass, ENTRY_ID)
    assert issue is not None
    assert issue.translation_placeholders["views"] == "Ersparnis"
    assert await storage.async_load(False) == stored


async def test_complete_dashboard_is_not_reported(hass) -> None:
    _register(hass, "sensor", "soc")
    _register(hass, "sensor", "economics_net_savings")
    _register(hass, "sensor", "economics_net_savings_today")
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    _lovelace(hass)
    await _existing_dashboard(hass, entry)

    await async_check_dashboard_up_to_date(hass, entry)

    assert _issue(hass, ENTRY_ID) is None


async def test_snapshot_dashboard_with_old_cashflow_entities_is_reported(
    hass,
) -> None:
    """Gleiche fünf Pfade dürfen eine veraltete Ersparnis-Entity nicht tarnen."""
    _register(hass, "sensor", "soc")
    raw_result = _register(hass, "sensor", "economics_operating_result")
    net_savings = _register(hass, "sensor", "economics_net_savings")
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    _lovelace(hass)
    storage = await _existing_dashboard(hass, entry)
    stored = await storage.async_load(False)
    stale = _replace_dashboard_values(stored, {net_savings: raw_result})
    await storage.async_save(stale)

    await async_check_dashboard_up_to_date(hass, entry)

    issue = _issue(hass, ENTRY_ID)
    assert issue is not None
    assert issue.translation_placeholders["views"] == "Ersparnis"
    # Wie bei fehlenden Tabs bleibt jede Nutzeranpassung bis zur bewussten
    # Bestätigung des Reparatur-Flows unangetastet.
    assert await storage.async_load(False) == stale


async def test_dashboard_with_removed_amortization_forecast_is_reported(hass) -> None:
    """Die entfernten Prognosefelder lösen für den Ersparnis-View aus."""
    _register(hass, "sensor", "economics_net_savings")
    _register(hass, "sensor", "economics_net_savings_today")
    _register(hass, "sensor", "economics_amortization_progress")
    _register(hass, "binary_sensor", "economics_investment_configured")
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    _lovelace(hass)
    storage = await _existing_dashboard(hass, entry)
    stored = await storage.async_load(False)

    savings_view = next(view for view in stored["views"] if view["path"] == "ersparnis")
    savings_view["cards"].append(
        {
            "type": "entity",
            "entity": ("sensor.sax_power_economics_estimated_payback_date"),
        }
    )
    await storage.async_save(stored)

    await async_check_dashboard_up_to_date(hass, entry)

    issue = _issue(hass, ENTRY_ID)
    assert issue is not None
    assert issue.translation_placeholders["views"] == "Ersparnis"


async def test_savings_dashboard_with_old_headings_and_missing_tariff_is_reported(
    hass,
) -> None:
    """Der vorherige Fünf-Karten-Stand verlangt eine bewusste Neuinstallation."""
    _register(hass, "sensor", "economics_net_savings")
    _register(hass, "sensor", "economics_net_savings_today")
    _register(hass, "sensor", "economics_current_import_price")
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    _lovelace(hass)
    storage = await _existing_dashboard(hass, entry)
    stored = await storage.async_load(False)
    savings_view = next(view for view in stored["views"] if view["path"] == "ersparnis")
    savings_view["cards"] = [
        card
        for card in savings_view["cards"]
        if not (card["type"] == "markdown" and "tariff_type" in card.get("content", ""))
    ]
    savings_view["cards"][0]["cards"].insert(
        0, {"type": "markdown", "content": "### Amortisation"}
    )
    free_period = _savings_free_period_block(savings_view)
    free_period["cards"].insert(
        0, {"type": "markdown", "content": "### Freier Zeitraum"}
    )
    await storage.async_save(stored)

    await async_check_dashboard_up_to_date(hass, entry)

    issue = _issue(hass, ENTRY_ID)
    assert issue is not None
    assert issue.translation_placeholders["views"] == "Ersparnis"
    assert await storage.async_load(False) == stored


async def test_missing_dashboard_is_not_reported(hass) -> None:
    """Ein gar nicht vorhandenes Dashboard ist eine bewusste Entscheidung
    des Anwenders (siehe const.CONF_CREATE_DASHBOARD) - eine
    Reparaturaufforderung würde genau das Dashboard zurückholen, das er
    gerade gelöscht hat."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    _lovelace(hass)

    await async_check_dashboard_up_to_date(hass, entry)

    assert _issue(hass, ENTRY_ID) is None


async def test_dismissed_hint_is_not_reported_again(hass) -> None:
    """Wer den Hinweis einmal ablehnt, soll ihn nicht bei jedem Neustart
    erneut sehen."""
    _register(hass, "sensor", "soc")
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id=ENTRY_ID,
        data={CONF_DASHBOARD_UPDATE_DISMISSED: True},
    )
    entry.add_to_hass(hass)
    _lovelace(hass)
    storage = await _existing_dashboard(hass, entry)
    await storage.async_save({"views": []})

    await async_check_dashboard_up_to_date(hass, entry)

    assert _issue(hass, ENTRY_ID) is None


async def test_outdated_issue_disappears_after_the_dashboard_is_rebuilt(hass) -> None:
    """Selbstheilung: Wer den Dienst sax_power.reinstall_dashboard von Hand
    aufruft, darf den Hinweis nicht behalten."""
    _register(hass, "sensor", "soc")
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    _lovelace(hass)
    storage = await _existing_dashboard(hass, entry)
    await storage.async_save({"views": []})
    await async_check_dashboard_up_to_date(hass, entry)
    assert _issue(hass, ENTRY_ID) is not None

    with patch(
        "custom_components.sax_power.dashboard.frontend.async_register_built_in_panel"
    ):
        await async_create_dashboard(hass, entry, force=True)
    await async_check_dashboard_up_to_date(hass, entry)

    assert _issue(hass, ENTRY_ID) is None


async def test_dashboard_check_swallows_unexpected_errors(hass) -> None:
    """Wie der gesamte übrige Dashboard-Code eine rein optionale
    Komfortfunktion auf nicht-öffentlichen Lovelace-Interna - ein Fehler
    darf die Integration niemals blockieren."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    _lovelace(hass)

    with patch(
        "custom_components.sax_power.dashboard._async_missing_dashboard_views",
        side_effect=RuntimeError("Lovelace-Interna geändert"),
    ):
        await async_check_dashboard_up_to_date(hass, entry)  # darf nicht raisen

    assert _issue(hass, ENTRY_ID) is None


# --------------------------------------------------------------------------
# Bedingungen von "conditional"-Karten (#139)
# --------------------------------------------------------------------------
def _iter_all_cards(cards: list[dict[str, Any]]):
    """Läuft rekursiv durch ALLE Karten, auch durch conditional/stack."""
    for card in cards:
        yield card
        yield from _iter_all_cards(card.get("cards", []))
        if (nested := card.get("card")) is not None:
            yield from _iter_all_cards([nested])


async def test_no_conditional_card_tests_an_attribute(hass) -> None:
    """Die Bedingungen einer Core-"conditional"-Karte prüfen ausschließlich
    den ZUSTAND einer Entity - einen Schlüssel `attribute` kennen sie
    nicht.

    Er wird nicht etwa abgelehnt, sondern stillschweigend ignoriert: Der
    Vergleich läuft weiter gegen den Zustand. Eine so gebaute Karte ist
    damit dauerhaft unsichtbar (`state` trifft nie zu) oder dauerhaft
    sichtbar (`state_not` trifft immer zu) - beides ohne jede
    Fehlermeldung, in der gespeicherten YAML-Konfiguration unauffällig und
    nur im laufenden Dashboard zu bemerken. Genau so blieben die
    Tarifplan-Karte unsichtbar und die Investitionskarte dauerhaft
    sichtbar (Anwenderbericht zu #139)."""
    reg = er.async_get(hass)
    for entity_domain, suffixes in (
        ("sensor", [d.key for d in sax_power.sensor.SENSOR_DESCRIPTIONS]),
        (
            "binary_sensor",
            [d.key for d in sax_power.binary_sensor.BINARY_SENSOR_DESCRIPTIONS],
        ),
    ):
        for suffix in suffixes:
            reg.async_get_or_create(entity_domain, DOMAIN, f"{ENTRY_ID}_{suffix}")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    conditions = [
        condition
        for view in config["views"]
        for card in _iter_all_cards(view["cards"])
        for condition in card.get("conditions", [])
    ]
    assert conditions, "Keine conditional-Karte gefunden - Test greift ins Leere"
    for condition in conditions:
        assert "attribute" not in condition, (
            f"Bedingung prüft ein Attribut: {condition} - "
            "wird von Home Assistant ignoriert"
        )
