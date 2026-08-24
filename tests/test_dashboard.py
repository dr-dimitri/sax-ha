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
    SERVICE_REINSTALL_DASHBOARD,
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
    den Karten; die vier Tabs (Views) sind immer vorhanden."""
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


async def test_build_dashboard_config_skips_cards_without_entities(hass) -> None:
    """Ohne jede registrierte Entity bleiben alle vier Views vorhanden, aber
    ohne Karten - kein Fehler, keine leeren Platzhalterkarten."""
    config = await async_build_dashboard_config(hass, "unbekannter_entry")

    assert len(config["views"]) == 4
    for view in config["views"]:
        assert view["cards"] == []


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
    """Der neue Tab "Netzdienliches Laden" enthält Start-/Endezeit, den
    Schalter "Netzdienliches Laden aktiv", den Prognose-Schwellwert und die
    zwölf Monats-Schalter in
    einer eigenen Karte - die reine Status-Textanzeige entfällt, weil der
    Schalter deren Zustand bereits zeigt."""
    grid_serving_switch = _register(hass, "switch", "grid_serving_enabled")
    grid_serving_start = _register(hass, "time", "grid_serving_start")
    grid_serving_end = _register(hass, "time", "grid_serving_end")
    forecast_threshold = _register(hass, "number", "grid_serving_forecast_threshold")
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
    assert forecast_threshold in entities
    assert entities.issuperset(month_switches)

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
        assert len(saved_config["views"]) == 4
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
        assert len(saved_config["views"]) == 4
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
        assert len(saved_config["views"]) == 4
        mock_register_panel.assert_called_once()  # kein zweiter Panel-Aufruf
