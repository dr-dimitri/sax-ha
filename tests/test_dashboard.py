"""Tests für das mitgelieferte Lovelace-Dashboard (dashboard.py, siehe
anforderung.yaml, REQ-BUNDLED-DASHBOARD).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from homeassistant.components.lovelace import LovelaceData
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import sax_power
from custom_components.sax_power.const import (
    DATA_COORDINATOR,
    DOMAIN,
    SERVICE_CREATE_DASHBOARD,
)
from custom_components.sax_power.dashboard import (
    DASHBOARD_URL_PATH,
    async_build_dashboard_config,
    async_create_dashboard,
)

ENTRY_ID = "test_entry_id"


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
    den Karten; die drei Tabs (Views) sind immer vorhanden."""
    soc_entity_id = _register(hass, "sensor", "soc")
    storage_switch_entity_id = _register(hass, "switch", "storage_switch")
    price_switch_entity_id = _register(hass, "switch", "price_charge_enabled")

    config = await async_build_dashboard_config(hass, ENTRY_ID)

    assert [view["path"] for view in config["views"]] == [
        "allgemein",
        "ladeautomatik",
        "dynamisches-laden",
    ]

    general_entities = set(_iter_entity_ids(config["views"][0]["cards"]))
    assert soc_entity_id in general_entities
    assert storage_switch_entity_id in general_entities

    price_entities = set(_iter_entity_ids(config["views"][2]["cards"]))
    assert price_switch_entity_id in price_entities


async def test_build_dashboard_config_soc_uses_gauge_card_with_severity(hass) -> None:
    """Der Ladezustand wird als Gauge-Karte mit Nadel dargestellt: grün ab
    50 % SOC, orange ab 20 % SOC, darunter rot."""
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
    assert gauge["severity"] == {"red": 0, "yellow": 20, "green": 50}


async def test_build_dashboard_config_temperature_uses_gauge_card_with_segments(
    hass,
) -> None:
    """Die Zelltemperatur wird ebenfalls als Gauge mit Nadel dargestellt:
    0-5 °C rot (zu kalt), 5-32 °C grün (normal), 32-40 °C rot (zu heiß) -
    ein nicht-monotones Farbmuster, das das einfache severity-Mapping nicht
    abbilden kann, deshalb "segments" statt "severity"."""
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


async def test_build_dashboard_config_skips_cards_without_entities(hass) -> None:
    """Ohne jede registrierte Entity bleiben alle drei Views vorhanden, aber
    ohne Karten - kein Fehler, keine leeren Platzhalterkarten."""
    config = await async_build_dashboard_config(hass, "unbekannter_entry")

    assert len(config["views"]) == 3
    for view in config["views"]:
        assert view["cards"] == []


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
        assert len(saved_config["views"]) == 3
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
        assert len(saved_config["views"]) == 3
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
