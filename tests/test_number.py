"""Tests for the SAX Power number entities (software-side default/init logic).

Instanziiert die Entities direkt (mit einem echten SaxPowerCoordinator, aber
ohne echten Modbus-Client) statt über den vollen Config-Flow/Setup-Pfad -
das deckt die reine Vorbelegungslogik in async_added_to_hass ab, ohne die
Slug-/Entity-ID-Generierung der echten Plattform-Registrierung nachbilden zu
müssen (siehe tests/test_integration_live.py für den vollen End-to-End-Pfad).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.number import NumberMode
from homeassistant.core import State

from custom_components.sax_power.const import (
    DEFAULT_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    DEFAULT_PRICE_HOURS,
    DEFAULT_PRICE_LIMIT,
    DEFAULT_PRICE_NEUTRAL,
    DEFAULT_TIMED_CHARGE_MIN_SOC,
    MAX_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    MAX_PRICE_HOURS,
    MAX_PRICE_LIMIT,
    MAX_SOC,
    MIN_SOC,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.number import (
    SaxPowerGridServingForecastThresholdNumber,
    SaxPowerMaxSocNumber,
    SaxPowerPriceChargeHoursNumber,
    SaxPowerPriceLimitNumber,
    SaxPowerPriceNeutralPriceNumber,
    SaxPowerTimedChargeMaxSocNumber,
    SaxPowerTimedChargeMinSocNumber,
)


@pytest.fixture
async def coordinator(hass):
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    coord = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
    )
    coord.data = {"soc": 50}
    yield coord
    # async_added_to_hass() below subscribes the entity as a coordinator
    # listener, which starts the periodic poll timer - shut it down again so
    # no lingering timer trips up the test harness.
    await coord.async_shutdown()


def _prepare_entity(entity, hass, entity_id: str, last_state: State | None) -> None:
    entity.hass = hass
    entity.entity_id = entity_id
    # Nur direkt instanziiert (kein echtes EntityPlatform-Setup wie im
    # vollen Integrationstest) - async_write_ha_state würde daher an der
    # Übersetzung der Einheit scheitern; für diesen reinen Vorbelegungstest
    # irrelevant.
    entity.async_write_ha_state = MagicMock()
    entity.async_get_last_state = AsyncMock(return_value=last_state)


@pytest.mark.parametrize("max_soc", [None, 0, 65, 100])
async def test_timed_charge_max_soc_uses_configured_global_limit(
    coordinator, max_soc
) -> None:
    """REQ-TIMED-SOC-CHARGE: Anfangswert und Slidergrenze folgen Max. SOC."""
    coordinator._max_soc = max_soc
    entity = SaxPowerTimedChargeMaxSocNumber(coordinator, "test_entry_id")

    expected = MAX_SOC if max_soc is None else max_soc
    assert entity.native_value == expected
    assert entity.native_max_value == expected
    assert entity.native_min_value == MIN_SOC
    assert entity.native_step == 1
    assert entity.mode is NumberMode.SLIDER
    assert entity.translation_key == "timed_charge_max_soc"


async def test_timed_charge_max_soc_tracks_global_limit_changes(
    hass, coordinator
) -> None:
    """REQ-TIMED-SOC-CHARGE: Absenken reduziert Ziel und Slidergrenze sofort."""
    coordinator._max_soc = 90
    coordinator.async_start_sun_charge = AsyncMock()
    entity = SaxPowerTimedChargeMaxSocNumber(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "number.test_timed_charge_max_soc", None)

    await entity.async_set_native_value(80)
    assert entity.native_value == 80
    assert entity.native_max_value == 90

    await coordinator.async_set_max_soc(60)
    assert entity.native_value == 60
    assert entity.native_max_value == 60

    await coordinator.async_set_max_soc(95)
    assert entity.native_value == 60
    assert entity.native_max_value == 95


async def test_timed_charge_max_soc_keeps_configured_limits_during_calibration(
    hass, coordinator
) -> None:
    """REQ-PERIODIC-FULL-CALIBRATION: Der Override ändert keine Sliderwerte."""
    coordinator._max_soc = 80
    entity = SaxPowerTimedChargeMaxSocNumber(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "number.test_timed_charge_max_soc", None)
    await entity.async_set_native_value(60)
    coordinator._cell_calibration_active = True

    assert entity.native_value == 60
    assert entity.native_max_value == 80
    assert coordinator.effective_timed_charge_max_soc == 100


async def test_timed_charge_min_soc_seeds_to_default_on_fresh_install(
    hass, coordinator
) -> None:
    """Allererster Start (kein RestoreEntity-Zustand): "Netzladung Min. SOC"
    muss mit DEFAULT_TIMED_CHARGE_MIN_SOC (20 %) vorbelegt werden statt bei
    "unbekannt"/0 zu bleiben - andernfalls würde Netzladung bei der
    Ersteinrichtung nie von selbst armen (SOC wäre praktisch nie < 0 %)."""
    entity = SaxPowerTimedChargeMinSocNumber(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "number.test_timed_charge_min_soc", None)

    await entity.async_added_to_hass()

    assert coordinator.timed_charge_min_soc == DEFAULT_TIMED_CHARGE_MIN_SOC


async def test_timed_charge_min_soc_restores_a_genuine_value(hass, coordinator) -> None:
    """Ein echter, zuvor vom Nutzer gesetzter Wert hat Vorrang vor dem
    Vorgabewert."""
    entity = SaxPowerTimedChargeMinSocNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_timed_charge_min_soc",
        State("number.test_timed_charge_min_soc", "40"),
    )

    await entity.async_added_to_hass()

    assert coordinator.timed_charge_min_soc == 40


async def test_timed_charge_min_soc_restore_clamps_out_of_range_value(
    hass, coordinator
) -> None:
    """Ein wiederhergestellter Wert außerhalb [MIN_SOC, MAX_SOC] (z. B. ein
    korrupter oder aus einer künftigen Version stammender Zustand) wird
    geklemmt statt ungeprüft übernommen zu werden - dieser Restaurierungspfad
    ruft den Coordinator-Setter direkt auf, ohne die sonst greifende
    NumberEntity-Min/Max-Validierung des regulären Service-Call-Pfads."""
    entity = SaxPowerTimedChargeMinSocNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_timed_charge_min_soc",
        State("number.test_timed_charge_min_soc", "150"),
    )

    await entity.async_added_to_hass()

    assert coordinator.timed_charge_min_soc == MAX_SOC


async def test_max_soc_restores_a_genuine_value(hass, coordinator) -> None:
    entity = SaxPowerMaxSocNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity, hass, "number.test_max_soc", State("number.test_max_soc", "80")
    )

    await entity.async_added_to_hass()

    assert coordinator.max_soc == 80


async def test_max_soc_entity_keeps_user_value_during_calibration(
    hass, coordinator
) -> None:
    entity = SaxPowerMaxSocNumber(coordinator, "test_entry_id")
    coordinator._max_soc = 80
    coordinator._cell_calibration_active = True

    assert entity.native_value == 80
    assert coordinator.effective_max_soc == 100


async def test_max_soc_restore_clamps_out_of_range_value(hass, coordinator) -> None:
    """Analog zu test_timed_charge_min_soc_restore_clamps_out_of_range_value,
    hier für "Max. SOC" - ein negativer wiederhergestellter Wert wird auf
    MIN_SOC geklemmt statt als ungültiger (negativer) Wert gespeichert und
    z. B. im Zahlenfeld angezeigt zu werden. current_soc (50) liegt bei
    diesem Beispiel sowohl über dem unklemmten als auch dem geklemmten Wert,
    die Max-SOC-Sperre greift dadurch in beiden Fällen - daher wird
    async_start_sun_charge hier real ausgelöst und der Modbus-Write gemockt."""
    write_result = MagicMock()
    write_result.isError.return_value = False
    coordinator.client.write_register = AsyncMock(return_value=write_result)
    coordinator.data["ic_max_power_reference"] = 4600
    coordinator.data["ic_timeout"] = 300
    entity = SaxPowerMaxSocNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity, hass, "number.test_max_soc", State("number.test_max_soc", "-20")
    )

    await entity.async_added_to_hass()

    assert coordinator.max_soc == MIN_SOC


# -- Netzdienliches Laden (anforderung.yaml, REQ-GRID-SERVING-CHARGE) ------
async def test_grid_serving_forecast_threshold_defaults_to_disabled(
    hass, coordinator
) -> None:
    entity = SaxPowerGridServingForecastThresholdNumber(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "number.test_grid_serving_forecast", None)

    await entity.async_added_to_hass()

    assert coordinator.grid_serving_forecast_threshold_kwh == pytest.approx(
        DEFAULT_GRID_SERVING_FORECAST_THRESHOLD_KWH
    )


async def test_grid_serving_forecast_threshold_restores_value(
    hass, coordinator
) -> None:
    """Persistierte Dezimalwerte werden kaufmännisch auf volle kWh gerundet."""
    entity = SaxPowerGridServingForecastThresholdNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_grid_serving_forecast",
        State("number.test_grid_serving_forecast", "8.5"),
    )

    await entity.async_added_to_hass()

    assert entity.native_step == 1
    assert coordinator.grid_serving_forecast_threshold_kwh == pytest.approx(9)


async def test_grid_serving_forecast_threshold_rounds_every_write(
    hass, coordinator
) -> None:
    entity = SaxPowerGridServingForecastThresholdNumber(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "number.test_grid_serving_forecast", None)

    await entity.async_set_native_value(8.49)

    assert coordinator.grid_serving_forecast_threshold_kwh == pytest.approx(8)


async def test_grid_serving_forecast_threshold_restore_clamps_value(
    hass, coordinator
) -> None:
    entity = SaxPowerGridServingForecastThresholdNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_grid_serving_forecast",
        State("number.test_grid_serving_forecast", "1200"),
    )

    await entity.async_added_to_hass()

    assert entity.native_max_value == 999
    assert coordinator.grid_serving_forecast_threshold_kwh == pytest.approx(
        MAX_GRID_SERVING_FORECAST_THRESHOLD_KWH
    )


# -- Preisoptimiertes Laden (anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE) ----
async def test_price_limit_defaults_on_fresh_install(hass, coordinator) -> None:
    """Ohne gespeicherten Zustand steht die Preisgrenze auf dem Vorgabewert
    statt auf 0 EUR/kWh (dabei würde nie geladen)."""
    entity = SaxPowerPriceLimitNumber(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "number.test_price_limit", None)

    await entity.async_added_to_hass()

    assert coordinator.price_charge_max_price == pytest.approx(DEFAULT_PRICE_LIMIT)


async def test_price_limit_restores_negative_value(hass, coordinator) -> None:
    """Negative Arbeitspreise sind ein gültiger Schwellwert und dürfen beim
    Restaurieren nicht auf 0 geklemmt werden."""
    entity = SaxPowerPriceLimitNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_price_limit",
        State("number.test_price_limit", "-0.05"),
    )

    await entity.async_added_to_hass()

    assert coordinator.price_charge_max_price == pytest.approx(-0.05)


async def test_price_limit_restore_clamps_out_of_range_value(hass, coordinator) -> None:
    entity = SaxPowerPriceLimitNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_price_limit",
        State("number.test_price_limit", "99"),
    )

    await entity.async_added_to_hass()

    assert coordinator.price_charge_max_price == pytest.approx(MAX_PRICE_LIMIT)


async def test_price_neutral_price_defaults_on_fresh_install(hass, coordinator) -> None:
    """Ohne gespeicherten Zustand steht der Neutralpreis auf dem Vorgabewert
    statt auf 0 EUR/kWh."""
    entity = SaxPowerPriceNeutralPriceNumber(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "number.test_price_neutral", None)

    await entity.async_added_to_hass()

    assert coordinator.price_charge_neutral_price == pytest.approx(
        DEFAULT_PRICE_NEUTRAL
    )


async def test_price_neutral_price_restores_a_genuine_value(hass, coordinator) -> None:
    entity = SaxPowerPriceNeutralPriceNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_price_neutral",
        State("number.test_price_neutral", "0.42"),
    )

    await entity.async_added_to_hass()

    assert coordinator.price_charge_neutral_price == pytest.approx(0.42)


async def test_price_neutral_price_restore_clamps_out_of_range_value(
    hass, coordinator
) -> None:
    entity = SaxPowerPriceNeutralPriceNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_price_neutral",
        State("number.test_price_neutral", "99"),
    )

    await entity.async_added_to_hass()

    assert coordinator.price_charge_neutral_price == pytest.approx(MAX_PRICE_LIMIT)


async def test_price_charge_hours_defaults_on_fresh_install(hass, coordinator) -> None:
    entity = SaxPowerPriceChargeHoursNumber(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "number.test_price_hours", None)

    await entity.async_added_to_hass()

    assert coordinator.price_charge_hours == DEFAULT_PRICE_HOURS


async def test_price_charge_hours_restore_clamps_out_of_range_value(
    hass, coordinator
) -> None:
    entity = SaxPowerPriceChargeHoursNumber(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "number.test_price_hours",
        State("number.test_price_hours", "48"),
    )

    await entity.async_added_to_hass()

    assert coordinator.price_charge_hours == MAX_PRICE_HOURS
