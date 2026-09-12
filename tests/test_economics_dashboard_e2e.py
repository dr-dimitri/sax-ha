"""End-to-End-Test der Wirtschaftlichkeits-Kette bis zum Ersparnis-Tab.

Tarifauflösung -> Herkunft -> Geldsensoren -> authentifizierte Dashboard-Sitzung,
über je einen PV-Lade-, Netzlade- und Entladeabschnitt hinweg.

Bewusst auf Coordinator-/Dashboard-Ebene statt über einen echten Modbus-
Server (test_integration_live.py) - hier geht es um das Zusammenspiel der
Wirtschaftlichkeits-Bausteine selbst (01/06 bis 06/06), nicht um
Registerzugriffe.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

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
    ECONOMICS_TOU_WINDOW_KEYS,
    economics_tou_window_key,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.dashboard_api import async_register_dashboard_api
from custom_components.sax_power.domain.tariff import TariffType
from custom_components.sax_power.sensor import SENSOR_DESCRIPTIONS

ENTRY_ID = "e2e_entry"


def _make_coordinator(hass: HomeAssistant) -> SaxPowerCoordinator:
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


@pytest.fixture
def dashboard_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, entry_id=ENTRY_ID, data={})
    entry.add_to_hass(hass)
    async_register_dashboard_api(hass)
    return entry


def _register(hass: HomeAssistant, entity_domain: str, suffix: str) -> str:
    entry = er.async_get(hass).async_get_or_create(
        entity_domain,
        DOMAIN,
        f"{ENTRY_ID}_{suffix}",
        config_entry=hass.config_entries.async_get_entry(ENTRY_ID),
        suggested_object_id=f"store_{suffix}",
    )
    return entry.entity_id


async def _dashboard_states(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, entry: MockConfigEntry
) -> dict[str, Any]:
    client = await hass_ws_client(hass)
    try:
        await client.send_json(
            {
                "id": 1,
                "type": "sax_power/dashboard/subscribe",
                "entry_id": entry.entry_id,
                "language": "de",
            }
        )
        assert (await client.receive_json())["success"]
        metadata = (await client.receive_json())["event"]["entities"]
        await client.send_json({"id": 2, "type": "get_states"})
        response = await client.receive_json()
        assert response["success"]
        states = {item["entity_id"]: item for item in response["result"]}
        return {item["key"]: states[item["entity_id"]] for item in metadata}
    finally:
        await client.close()


async def test_pv_grid_discharge_flow_reaches_money_sensors_and_dashboard(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    dashboard_entry: MockConfigEntry,
) -> None:
    """REQ-VUE-SAVINGS: Geldwerte erreichen die authentifizierte Dashboard-Sitzung."""
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
    assert discharge_tick["economics_net_savings"] == pytest.approx(-0.08)

    # -- Datenqualität (REQ-ECONOMICS-OBSERVABILITY): vollständige
    # Preis-/Herkunftsabdeckung während des gesamten Ablaufs -> aktiv.
    assert discharge_tick["economics_status"] == "active"

    # -- ROI und Amortisationsstand (REQ-ECONOMICS-AMORTIZATION) --------
    assert discharge_tick["economics_net_savings_today"] == pytest.approx(-0.08)
    assert discharge_tick["economics_roi"] == pytest.approx(-0.01)
    assert discharge_tick["economics_amortization_progress"] == pytest.approx(0.0)
    assert coordinator.economics_diagnostics["operating_result_raw_eur"] == (
        pytest.approx(0.30 - 0.30 - 0.08)
    )

    coordinator.data = discharge_tick
    keys = (
        "economics_status",
        "economics_current_import_price",
        "economics_net_savings",
        "economics_roi",
        "economics_amortization_progress",
    )
    for key in keys:
        entity_id = _register(hass, "sensor", key)
        description = next(item for item in SENSOR_DESCRIPTIONS if item.key == key)
        attributes = (
            description.attributes_fn(coordinator) if description.attributes_fn else {}
        )
        hass.states.async_set(entity_id, str(discharge_tick[key]), attributes)
    investment_id = _register(hass, "binary_sensor", "economics_investment_configured")
    hass.states.async_set(investment_id, "on")

    states = await _dashboard_states(hass, hass_ws_client, dashboard_entry)
    assert set(states) == {*keys, "economics_investment_configured"}
    assert states["economics_status"]["state"] == "active"
    assert float(states["economics_current_import_price"]["state"]) == 0.30
    assert float(states["economics_net_savings"]["state"]) == pytest.approx(-0.08)
    assert float(states["economics_roi"]["state"]) == pytest.approx(-0.01)
    assert float(states["economics_amortization_progress"]["state"]) == 0.0
    assert states["economics_investment_configured"]["state"] == "on"


@pytest.mark.parametrize("window_count", [1, 2, 8])
@pytest.mark.parametrize(
    "moment",
    [
        datetime(2026, 6, 1, 23, 0),
        datetime(2026, 6, 2, 0, 0),
        datetime(2026, 6, 2, 6, 0),
        datetime(2026, 6, 2, 20, 0),
    ],
    ids=["overnight-start", "midnight", "adjacent-boundary", "base-price"],
)
async def test_tariff_plan_reaches_the_dashboard_session(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    dashboard_entry: MockConfigEntry,
    window_count: int,
    moment: datetime,
) -> None:
    """REQ-VUE-CHARGING/-SAVINGS: Optionsflow -> Modell -> Sensor -> Dashboard.

    Beide Ansichten erhalten alle gespeicherten Fenster in Planreihenfolge,
    auch über Mitternacht und an direkt angrenzenden Fenstergrenzen.
    """
    await hass.config.async_set_time_zone("Europe/Berlin")
    profile = (
        ("22:00:00", "06:00:00", 0.2101),
        ("06:00:00", "08:00:00", 0.2202),
        ("08:00:00", "10:00:00", 0.2303),
        ("10:00:00", "12:00:00", 0.2404),
        ("12:00:00", "14:00:00", 0.2505),
        ("14:00:00", "16:00:00", 0.2606),
        ("16:00:00", "18:00:00", 0.2707),
        ("18:00:00", "20:00:00", 0.2808),
    )[:window_count]
    windows = [
        {"start": start, "end": end, "price_eur_kwh": price}
        for start, end, price in profile
    ]
    options_windows = {key: {} for key in ECONOMICS_TOU_WINDOW_KEYS}
    options_windows.update(
        {
            economics_tou_window_key(index): {
                CONF_ECONOMICS_WINDOW_START: start,
                CONF_ECONOMICS_WINDOW_END: end,
                CONF_ECONOMICS_WINDOW_PRICE: price,
            }
            for index, (start, end, price) in enumerate(profile, start=1)
        }
    )
    result = await hass.config_entries.options.async_init(dashboard_entry.entry_id)
    assert result["type"] == FlowResultType.MENU
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "economics"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ECONOMICS_TARIFF_TYPE: TariffType.TIME_OF_USE.value},
    )
    assert result["step_id"] == "economics_time_of_use"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
            CONF_ECONOMICS_TOU_BASE_PRICE: 0.30,
            **options_windows,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert {
        key: dashboard_entry.options.get(key, {}) for key in ECONOMICS_TOU_WINDOW_KEYS
    } == options_windows

    coordinator = _make_coordinator(hass)
    coordinator.options = dict(dashboard_entry.options)
    config = coordinator.tariff_provider.config
    assert config.windows_valid
    assert [
        {
            "start": window.start.isoformat(),
            "end": window.end.isoformat(),
            "price_eur_kwh": window.price_eur_kwh,
        }
        for window in config.windows
    ] == windows

    if moment.hour in (23, 0):
        active_window = windows[0]
        next_change = "2026-06-02T06:00:00+02:00"
    elif moment.hour == 6 and window_count > 1:
        active_window = windows[1]
        next_change = "2026-06-02T08:00:00+02:00"
    else:
        active_window = None
        next_change = "2026-06-02T22:00:00+02:00"
    expected_price = active_window["price_eur_kwh"] if active_window else 0.30
    expected_attributes = {
        "tariff_type": "time_of_use",
        "quote_source": "time_of_use_window" if active_window else "time_of_use_base",
        "unavailable_reason": None,
        "active_window": active_window,
        "next_price_change_at": next_change,
        "base_price_eur_kwh": 0.30,
        "feed_in_price_eur_kwh": 0.08,
        "windows": sorted(windows, key=lambda window: window["start"]),
    }
    coordinator._energy_charged_kwh = 0.0
    coordinator._energy_discharged_kwh = 0.0

    with (
        patch("custom_components.sax_power.coordinator.monotonic", return_value=1000.0),
        patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=moment,
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
    assert attributes == expected_attributes

    price_entity_id = _register(hass, "sensor", "economics_current_import_price")
    hass.states.async_set(price_entity_id, str(data[description.key]), attributes)

    states = await _dashboard_states(hass, hass_ws_client, dashboard_entry)
    price = states["economics_current_import_price"]
    assert price["entity_id"] == price_entity_id
    assert float(price["state"]) == expected_price
    assert price["attributes"] == expected_attributes
