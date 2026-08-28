"""End-to-End-Test der gesamten Wirtschaftlichkeits-Kette (REQ-ECONOMICS-
DASHBOARD, Akzeptanzkriterium): Tarifauflösung -> Herkunft -> Geldsensoren
-> Dashboard-Entityauflösung, über je einen PV-Lade-, Netzlade- und
Entladeabschnitt hinweg.

Bewusst auf Coordinator-/Dashboard-Ebene statt über einen echten Modbus-
Server (test_integration_live.py) - hier geht es um das Zusammenspiel der
Wirtschaftlichkeits-Bausteine selbst (01/06 bis 06/06), nicht um
Registerzugriffe.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import template

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_INVESTMENT_COST,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_ECONOMICS_TOU_BASE_PRICE,
    CONF_ECONOMICS_WINDOW_END,
    CONF_ECONOMICS_WINDOW_PRICE,
    CONF_ECONOMICS_WINDOW_START,
    DOMAIN,
    economics_tou_window_key,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.dashboard import async_build_dashboard_config
from custom_components.sax_power.domain.tariff import TariffType
from custom_components.sax_power.sensor import SENSOR_DESCRIPTIONS

ENTRY_ID = "e2e_entry"


def _make_coordinator(hass) -> SaxPowerCoordinator:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    return SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=ENTRY_ID,
    )


def _register(hass, entity_domain: str, suffix: str) -> str:
    entry = er.async_get(hass).async_get_or_create(
        entity_domain, DOMAIN, f"{ENTRY_ID}_{suffix}"
    )
    return entry.entity_id


async def test_pv_grid_discharge_flow_reaches_money_sensors_and_dashboard(
    hass,
) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.options = {
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.30,
        CONF_ECONOMICS_INVESTMENT_COST: 1000.0,
    }
    # Normalerweise setzt async_load_energy_state() das vor dem ersten
    # Refresh (siehe __init__.py) - hier direkt, da dieser Test bewusst nur
    # den Coordinator statt der vollen Setup-Sequenz verwendet.
    coordinator._energy_charged_kwh = 0.0
    coordinator._energy_discharged_kwh = 0.0
    coordinator._energy_grid_charged_kwh = 0.0
    coordinator._energy_pv_charged_kwh = 0.0

    def _tick(monotonic_value, now, *, storage_power_active, smartmeter_power, soc):
        with (
            patch(
                "custom_components.sax_power.coordinator.monotonic",
                return_value=monotonic_value,
            ),
            patch(
                "custom_components.sax_power.coordinator.dt_util.now",
                return_value=now,
            ),
        ):
            data = {
                "storage_power_active": storage_power_active,
                "smartmeter_power": smartmeter_power,
                "battery_soc": soc,
                "battery_capacity": 10000,
                "battery_soc_min": 5,
            }
            coordinator._accumulate_energy(data)
        return data

    base = datetime(2026, 6, 1, 8, 0)

    # 1) Bootstrap - reine Zeitbasis, kein Delta, Anfangsbestand 0.
    _tick(1000.0, base, storage_power_active=0, smartmeter_power=0, soc=0)

    # 2) Eine Stunde PV-Ladung (Einspeisung während des Ladens -> PV deckt
    #    die gesamte Ladeleistung, siehe REQ-ENERGY-ORIGIN).
    pv_tick = _tick(
        1000.0 + 3600,
        base,
        storage_power_active=-1000,
        smartmeter_power=-500,
        soc=10,
    )

    # 3) Eine Stunde Netzladung (Netzbezug deckt die Ladeleistung).
    grid_tick = _tick(
        1000.0 + 2 * 3600,
        base,
        storage_power_active=-1000,
        smartmeter_power=1000,
        soc=20,
    )

    # 4) Eine Stunde Entladung.
    discharge_tick = _tick(
        1000.0 + 3 * 3600,
        base,
        storage_power_active=1000,
        smartmeter_power=0,
        soc=10,
    )

    # -- Herkunft (REQ-ENERGY-ORIGIN) -----------------------------------
    assert pv_tick["energy_charged_from_pv"] == 1.0
    assert grid_tick["energy_charged_from_grid"] == 1.0

    # -- Tarifauflösung + Geldsensoren (REQ-ECONOMICS-TARIFFS/-ACCOUNTING) --
    assert pv_tick["economics_current_import_price"] == 0.30
    assert pv_tick["economics_feed_in_price"] == 0.08
    assert pv_tick["economics_pv_opportunity_cost"] == 0.08
    assert grid_tick["economics_grid_charge_cost"] == 0.30
    assert discharge_tick["economics_avoided_grid_cost"] == 0.30
    assert discharge_tick["economics_operating_result"] == pytest.approx(
        0.30 - 0.30 - 0.08
    )

    # -- Datenqualität (REQ-ECONOMICS-OBSERVABILITY): vollständige
    # Preis-/Herkunftsabdeckung während des gesamten Ablaufs -> aktiv.
    assert discharge_tick["economics_status"] == "active"

    # -- ROI-/Amortisationsprognose (REQ-ECONOMICS-AMORTIZATION) --------
    assert discharge_tick["economics_result_today"] == pytest.approx(0.30 - 0.30 - 0.08)
    assert discharge_tick["economics_roi"] == pytest.approx(
        round((0.30 - 0.30 - 0.08) / 1000.0 * 100, 2)
    )

    # -- Dashboard-Entityauflösung (REQ-ECONOMICS-DASHBOARD) -------------
    status_id = _register(hass, "sensor", "economics_status")
    import_price_id = _register(hass, "sensor", "economics_current_import_price")
    feed_in_id = _register(hass, "sensor", "economics_feed_in_price")
    pv_id = _register(hass, "sensor", "energy_charged_from_pv")
    grid_id = _register(hass, "sensor", "energy_charged_from_grid")
    avoided_id = _register(hass, "sensor", "economics_avoided_grid_cost")
    grid_cost_id = _register(hass, "sensor", "economics_grid_charge_cost")
    pv_cost_id = _register(hass, "sensor", "economics_pv_opportunity_cost")
    result_id = _register(hass, "sensor", "economics_operating_result")
    roi_id = _register(hass, "sensor", "economics_roi")
    progress_id = _register(hass, "sensor", "economics_amortization_progress")

    config = await async_build_dashboard_config(hass, ENTRY_ID)
    economics_view = next(
        view for view in config["views"] if view["path"] == "wirtschaftlichkeit"
    )

    def _entity_ids(cards):
        for card in cards:
            if card["type"] in ("grid", "vertical-stack"):
                yield from _entity_ids(card["cards"])
            elif card["type"] == "conditional":
                yield from _entity_ids([card["card"]])
            elif card["type"] == "entities":
                for row in card["entities"]:
                    yield row["entity"] if isinstance(row, dict) else row
            elif "entity" in card:
                yield card["entity"]

    resolved = set(_entity_ids(economics_view["cards"]))
    for entity_id in (
        status_id,
        import_price_id,
        feed_in_id,
        pv_id,
        grid_id,
        avoided_id,
        grid_cost_id,
        pv_cost_id,
        result_id,
        roi_id,
        progress_id,
    ):
        assert entity_id in resolved


async def test_origin_start_reaches_the_dashboard_row(hass) -> None:
    """Ganze Kette des Herkunftsbeginns (REQ-ENERGY-ORIGIN): Coordinator ->
    Sensorattribut -> Attributzeile der Dashboard-Karte.

    Der Attributname muss an allen drei Stellen derselbe sein - sonst
    stünde im Dashboard eine leere Zeile, und genau die Angabe fehlte, die
    die verschieden alten Zähler auseinanderhält."""
    coordinator = _make_coordinator(hass)
    started_at = datetime(2026, 3, 1, 8, 0, tzinfo=UTC)
    with patch(
        "custom_components.sax_power.coordinator.dt_util.utcnow",
        return_value=started_at,
    ):
        coordinator._bootstrap_energy_origin(None)
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        data = {"storage_power_active": 0, "smartmeter_power": 0}
        coordinator._accumulate_energy(data)
    coordinator.data = data

    description = next(
        entry for entry in SENSOR_DESCRIPTIONS if entry.key == "energy_charged_from_pv"
    )
    assert description.attributes_fn is not None
    attributes = description.attributes_fn(coordinator)
    assert attributes["origin_accounting_started_at"] == started_at.isoformat()

    pv_entity_id = _register(hass, "sensor", "energy_charged_from_pv")
    config = await async_build_dashboard_config(hass, ENTRY_ID)
    economics_view = next(
        view for view in config["views"] if view["path"] == "wirtschaftlichkeit"
    )
    rows = [
        row
        for card in economics_view["cards"]
        if card["type"] == "vertical-stack"
        for sub in card["cards"]
        for row in sub.get("entities", [])
        if isinstance(row, dict) and row.get("type") == "attribute"
    ]
    assert {
        "type": "attribute",
        "entity": pv_entity_id,
        "attribute": "origin_accounting_started_at",
        "name": "Beginn der Herkunftszählung",
    } in rows


async def test_tariff_plan_reaches_the_dashboard_card(hass) -> None:
    """Ganze Kette des Tarifplans (REQ-ECONOMICS-DASHBOARD): Options ->
    Coordinator-Attribute -> Sensor-Entity -> gerenderte Dashboard-Karte.

    Jedes Glied für sich ist bereits abgedeckt; hier geht es darum, dass
    die vier Attributnamen an allen drei Stellen dieselben sind - ein
    umbenanntes Attribut fiele sonst erst im Dashboard des Anwenders auf,
    als leere Karte ohne jede Fehlermeldung."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    coordinator = _make_coordinator(hass)
    coordinator.options = {
        CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value,
        CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
        CONF_ECONOMICS_TOU_BASE_PRICE: 0.30,
        economics_tou_window_key(1): {
            CONF_ECONOMICS_WINDOW_START: "22:00:00",
            CONF_ECONOMICS_WINDOW_END: "06:00:00",
            CONF_ECONOMICS_WINDOW_PRICE: 0.21,
        },
    }
    coordinator._energy_charged_kwh = 0.0
    coordinator._energy_discharged_kwh = 0.0

    with (
        patch("custom_components.sax_power.coordinator.monotonic", return_value=1000.0),
        patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=datetime(2026, 6, 1, 23, 0),
        ),
    ):
        data = {
            "storage_power_active": 0,
            "smartmeter_power": 0,
            "battery_soc": 50,
            "battery_capacity": 10000,
            "battery_soc_min": 5,
        }
        coordinator._accumulate_energy(data)
    coordinator.data = data

    # Genau der Weg, den auch die Sensor-Entity nimmt (sensor.py,
    # SaxPowerSensorEntityDescription.attributes_fn).
    description = next(
        entry
        for entry in SENSOR_DESCRIPTIONS
        if entry.key == "economics_current_import_price"
    )
    assert description.attributes_fn is not None
    attributes = description.attributes_fn(coordinator)

    price_entity_id = _register(hass, "sensor", "economics_current_import_price")
    hass.states.async_set(price_entity_id, str(data[description.key]), attributes)

    config = await async_build_dashboard_config(hass, ENTRY_ID)
    economics_view = next(
        view for view in config["views"] if view["path"] == "wirtschaftlichkeit"
    )
    card = next(
        entry
        for entry in economics_view["cards"]
        if entry["type"] == "markdown" and "tariff_type" in entry.get("content", "")
    )
    rendered = template.Template(card["content"], hass).async_render(parse_result=False)

    assert "| **jetzt** | 22:00 | 06:00 | 0.2100 EUR/kWh |" in rendered
    assert "0.3000 EUR/kWh (Grundpreis)" in rendered
    assert "Nächster Preiswechsel: 06:00 Uhr" in rendered
