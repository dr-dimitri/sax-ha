"""Konsistenz-Tests für die (datengetriebene) Liste der Sensor-Beschreibungen.

Bei ~55 Sensoren ist ein Tippfehler in einem translation_key oder ein
doppelter unique_id-Suffix leicht zu übersehen - diese Tests fangen das ab,
ohne dass für jeden einzelnen Sensor ein eigener Test geschrieben werden muss.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import CURRENCY_EURO, EntityCategory, UnitOfEnergy, UnitOfPower
from homeassistant.helpers import entity_registry as er

from custom_components.sax_power.const import (
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_LOW1_COUNT,
    READ_BLOCK_EXT_LOW2_COUNT,
    READ_BLOCK_EXT_START,
    REG_SUN_IC_POWER_SETPOINT_SF,
)
from custom_components.sax_power.domain.registers import to_unsigned16
from custom_components.sax_power.domain.sunspec import (
    decode_high_block,
    decode_low_blocks,
)
from custom_components.sax_power.sensor import (
    SENSOR_DESCRIPTIONS,
    SaxPowerForecastSensor,
    SaxPowerSensor,
)

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "sax_power"


def test_sensor_keys_are_unique() -> None:
    keys = [description.key for description in SENSOR_DESCRIPTIONS]
    assert len(keys) == len(set(keys))


def test_daily_net_savings_uses_a_fresh_recorder_entity() -> None:
    """Der tägliche Roh-Cashflow darf nicht als Netto-Historie umgedeutet werden."""
    keys = {description.key for description in SENSOR_DESCRIPTIONS}

    assert "economics_net_savings_today" in keys
    assert "economics_result_today" not in keys


def test_amortization_forecast_entities_are_no_longer_published() -> None:
    keys = {description.key for description in SENSOR_DESCRIPTIONS}

    assert "economics_average_daily_result_30d" not in keys
    assert "economics_projected_annual_result" not in keys
    assert "economics_estimated_payback_date" not in keys


def test_internal_unpriced_energy_values_are_not_published_as_entities() -> None:
    keys = {description.key for description in SENSOR_DESCRIPTIONS}

    assert "economics_unvalued_inventory" not in keys
    assert "economics_unpriced_charge" not in keys
    assert "economics_unpriced_discharge" not in keys


def test_roi_attributes_format_prior_result_with_two_decimal_places() -> None:
    """Der rohe Vorlauf bleibt numerisch; die Core-Attributzeile erhält
    daneben eine Anzeigeform mit exakt zwei Nachkommastellen."""
    description = next(
        entry for entry in SENSOR_DESCRIPTIONS if entry.key == "economics_roi"
    )
    coordinator = SimpleNamespace(
        data={
            "economics_roi_attributes": {
                "prior_result_eur": 400.5,
                "measured_operating_result_eur": 250.0,
            }
        }
    )

    attributes = description.attributes_fn(coordinator)

    assert attributes["prior_result_eur"] == 400.5
    assert attributes["prior_result_eur_formatted"] == "400.50"


def test_sensor_descriptions_have_reasonable_count() -> None:
    # Grobe Regression-Absicherung: die Anzahl soll nicht "aus Versehen"
    # drastisch schrumpfen (z. B. durch einen Merge-Fehler).
    assert len(SENSOR_DESCRIPTIONS) >= 40


def _load(filename: str) -> dict:
    with (COMPONENT_DIR / filename).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_every_sensor_has_translations_in_all_locales() -> None:
    keys = {description.key for description in SENSOR_DESCRIPTIONS}
    for filename in ("strings.json", "translations/de.json", "translations/en.json"):
        data = _load(filename)
        translated_keys = set(data.get("entity", {}).get("sensor", {}).keys())
        missing = keys - translated_keys
        assert not missing, f"{filename} fehlt Übersetzung für: {sorted(missing)}"


def test_german_forecast_threshold_label_uses_hyphen() -> None:
    translations = _load("translations/de.json")

    assert (
        translations["entity"]["number"]["grid_serving_forecast_threshold"]["name"]
        == "Mindest PV-Prognose"
    )


def _full_data() -> dict:
    """Baut einen vollständig befüllten, coordinator.data-artigen Datensatz.

    Nutzt die echten Decoder (domain/sunspec.py) auf Testwerten statt einer
    manuell gepflegten Kopie aller ~55 Schlüssel - das hält den Test
    automatisch synchron mit dem tatsächlichen Register-Layout (siehe
    anforderung.yaml, REQ-SUNSPEC-MODE-CORRECTION).
    """
    high = [0] * READ_BLOCK_EXT_COUNT
    # Scalefaktor Leistungsvorgabe (Immediate Controls) - der einzige, für
    # den 0 kein plausibler "wellknown"-Wert ist.
    high[REG_SUN_IC_POWER_SETPOINT_SF - READ_BLOCK_EXT_START] = to_unsigned16(-2)

    low = decode_low_blocks(
        [0] * READ_BLOCK_EXT_LOW1_COUNT, [0] * READ_BLOCK_EXT_LOW2_COUNT
    )
    extended = {
        **low.values,
        **decode_high_block(high, low.scale_factors).values,
    }

    basic = {
        "switch_state": 2,
        "switch_state_text": "Ein",
        "setpoint_power": 0,
        "setpoint_cosphi": 0,
        "soc": 55,
        "timed_charge_active": False,
    }
    return {**basic, **extended}


def test_value_fn_handles_full_data_dict() -> None:
    """Jede value_fn muss mit einem vollständig befüllten Datensatz umgehen
    können, ohne eine Exception zu werfen (z. B. KeyError bei Tippfehlern)."""
    full_data = _full_data()

    for description in SENSOR_DESCRIPTIONS:
        description.value_fn(full_data)


def _description_by_key(key: str):
    for description in SENSOR_DESCRIPTIONS:
        if description.key == key:
            return description
    raise AssertionError(f"Keine Sensor-Beschreibung mit key={key!r} gefunden")


def test_diagnostic_entities_carry_diagnostic_category() -> None:
    """REQ-52: technische Detail-/Rohwerte und Geräteidentität sind
    entity_category=DIAGNOSTIC, damit sie die Hauptübersicht nicht
    zumüllen (siehe GitHub-Issue #52)."""
    diagnostic_keys = (
        "sun_manufacturer",
        "sun_serial_number",
        "setpoint_power",
        "storage_state_text",
        "storage_voltage_a",
        "storage_power_factor",
        "grid_current_l1",
        "grid_power_apparent_sum",
        "battery_cell_voltage_avg",
    )
    for key in diagnostic_keys:
        description = _description_by_key(key)
        assert description.entity_category == EntityCategory.DIAGNOSTIC, key


def test_core_entities_have_no_entity_category() -> None:
    """REQ-52: Alltagsrelevante Kernwerte (SOC, Leistung, Temperatur,
    Automatik-Status) bleiben ohne entity_category, damit sie auf der
    Hauptübersicht sichtbar bleiben (siehe GitHub-Issue #52)."""
    core_keys = (
        "soc",
        "discharge_power",
        "charge_power",
        "charge_discharge_power",
        "smartmeter_power",
        "storage_max_cell_temp",
        "pv_power",
        "price_charge_status_text",
        "price_charge_next_start",
        "grid_serving_forecast",
        "grid_serving_pause_status",
        "timed_charge_discharge_status",
    )
    for key in core_keys:
        description = _description_by_key(key)
        assert description.entity_category is None, key


@pytest.mark.parametrize(
    "status", ["normal", "grid_charging", "discharge_blocked", None]
)
def test_timed_charge_discharge_status_reports_coordinator_state(status) -> None:
    """REQ-TIMED-SOC-CHARGE: Der Entladestatus folgt dem bestätigten Zustand."""
    description = _description_by_key("timed_charge_discharge_status")
    coordinator = MagicMock()
    coordinator.data = {
        "timed_charge_discharge_status": status,
        "timed_charge_active": True,
        "price_charge_active": True,
    }
    entity = SaxPowerSensor(coordinator, "test_entry_id", description)

    assert entity.device_class == SensorDeviceClass.ENUM
    assert entity.options == ["normal", "grid_charging", "discharge_blocked"]
    assert entity.unique_id == "test_entry_id_timed_charge_discharge_status"
    assert entity.native_value == status
    assert description.value_fn({"timed_charge_active": True}) is None
    coordinator.data = None
    assert entity.native_value is None


def test_timed_charge_discharge_status_translations_cover_all_states() -> None:
    """REQ-TIMED-SOC-CHARGE: Alle Zustände besitzen lesbare Übersetzungen."""
    expected_states = {
        "normal": "Normalbetrieb",
        "grid_charging": "Netzladen",
        "discharge_blocked": "Entladung wg. Netzladen gestoppt",
    }
    for filename in ("strings.json", "translations/de.json"):
        translated = _load(filename)["entity"]["sensor"][
            "timed_charge_discharge_status"
        ]
        assert translated["name"] == "Entladestatus"
        assert translated["state"] == expected_states
    english = _load("translations/en.json")["entity"]["sensor"][
        "timed_charge_discharge_status"
    ]
    assert set(english["state"]) == set(expected_states)


def test_charge_discharge_power_preserves_storage_power_sign() -> None:
    """REQ-SUNSPEC-MODE-CORRECTION: Der kombinierte Sensor zeigt
    Entladung positiv und Ladung negativ in derselben Entity."""
    description = _description_by_key("charge_discharge_power")

    assert description.device_class == SensorDeviceClass.POWER
    assert description.state_class == SensorStateClass.MEASUREMENT
    assert description.native_unit_of_measurement == UnitOfPower.WATT
    assert description.value_fn({"storage_power_active": 1200}) == 1200
    assert description.value_fn({"storage_power_active": -850}) == -850
    assert description.value_fn({"storage_power_active": 0}) == 0
    assert description.value_fn({}) is None


def test_grid_serving_forecast_is_kwh_or_unknown() -> None:
    description = _description_by_key("grid_serving_forecast")

    assert description.device_class == "energy"
    assert description.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
    assert description.value_fn({"grid_serving_forecast_kwh": 12.5}) == 12.5
    assert description.value_fn({"grid_serving_forecast_kwh": None}) is None


@pytest.mark.parametrize(
    "key",
    (
        "economics_grid_charge_cost",
        "economics_pv_opportunity_cost",
        "economics_avoided_grid_cost",
        "economics_operating_result",
        "economics_net_savings",
    ),
)
def test_economics_totals_share_the_balance_last_reset(key: str) -> None:
    description = _description_by_key(key)
    started_at = datetime(2026, 3, 10, 9, 0, tzinfo=UTC)

    assert description.device_class == SensorDeviceClass.MONETARY
    assert description.state_class == SensorStateClass.TOTAL
    assert description.native_unit_of_measurement == CURRENCY_EURO
    assert description.last_reset_fn is not None
    assert description.last_reset_fn({"economics_balance_last_reset": started_at}) == (
        started_at
    )


def test_grid_serving_forecast_name_tracks_current_date_without_device_prefix(
    hass,
) -> None:
    description = _description_by_key("grid_serving_forecast")
    coordinator = MagicMock()
    entity = SaxPowerForecastSensor(coordinator, "test_entry_id", description)
    entity.platform_data = SimpleNamespace(
        platform_name="sax_power",
        domain="sensor",
        platform_translations={
            "component.sax_power.entity.sensor.grid_serving_forecast.name": (
                "PV-Prognose"
            )
        },
    )

    with patch(
        "custom_components.sax_power.sensor.dt_util.now",
        return_value=datetime(2026, 8, 24),
    ):
        assert entity.name == "PV-Prognose 24.8."

        registry_entry = er.async_get(hass).async_get_or_create(
            "sensor",
            "sax_power",
            entity.unique_id,
            device_id=None,
            has_entity_name=entity.has_entity_name,
            original_name=entity.name,
            suggested_object_id="sax_power_grid_serving_forecast",
        )
        assert er.async_get_full_entity_name(hass, registry_entry) == (
            "PV-Prognose 24.8."
        )

    with patch(
        "custom_components.sax_power.sensor.dt_util.now",
        return_value=datetime(2026, 8, 25),
    ):
        assert entity.name == "PV-Prognose 25.8."

    assert entity.has_entity_name is False
    assert entity.device_info is None


def test_only_resettable_totals_declare_a_last_reset() -> None:
    """Home Assistant wertet last_reset ausschließlich für state_class
    total aus - an einem anderen Sensor wäre die Funktion wirkungslos und
    damit irreführend (Issue #133)."""
    for description in SENSOR_DESCRIPTIONS:
        if description.last_reset_fn is not None:
            assert description.state_class == SensorStateClass.TOTAL, description.key


def test_net_savings_today_reports_the_daily_reset_timestamp() -> None:
    """Der Tagessensor reicht den vom Coordinator veröffentlichten
    Reset-Zeitpunkt als last_reset durch; ein Sensor ohne last_reset_fn
    liefert unverändert None (Issue #133)."""
    midnight = datetime(2026, 3, 11, tzinfo=UTC)
    coordinator = MagicMock()
    coordinator.data = {
        "economics_net_savings_today": 2.5,
        "economics_net_savings_today_last_reset": midnight,
    }

    entity = SaxPowerSensor(
        coordinator, "test_entry_id", _description_by_key("economics_net_savings_today")
    )
    assert entity.entity_description.suggested_display_precision == 2
    assert entity.last_reset == midnight

    other = SaxPowerSensor(
        coordinator, "test_entry_id", _description_by_key("economics_roi")
    )
    assert other.last_reset is None


def test_net_savings_today_last_reset_ignores_a_missing_or_foreign_value() -> None:
    """Solange der Coordinator noch keinen Tag begonnen hat (oder unter dem
    Schlüssel etwas anderes als ein datetime steht), darf kein Fremdtyp als
    last_reset in die Langzeitstatistik geraten."""
    description = _description_by_key("economics_net_savings_today")
    assert description.last_reset_fn is not None
    assert description.last_reset_fn({}) is None
    assert (
        description.last_reset_fn({"economics_net_savings_today_last_reset": None})
        is None
    )
    assert (
        description.last_reset_fn(
            {"economics_net_savings_today_last_reset": "2026-03-11"}
        )
        is None
    )

    coordinator = MagicMock()
    coordinator.data = None
    entity = SaxPowerSensor(coordinator, "test_entry_id", description)
    assert entity.last_reset is None


def test_next_cell_calibration_is_a_diagnostic_timestamp() -> None:
    description = _description_by_key("next_cell_calibration")

    assert description.entity_category == EntityCategory.DIAGNOSTIC
    assert description.device_class == "timestamp"


def test_value_fn_handles_missing_extended_data() -> None:
    """value_fn darf auch dann nicht werfen, wenn der SunSpec-Modus-Block
    fehlt (z. B. weil Slave-ID 100 gerade nicht erreichbar ist) - nur die
    Basic-Mode-Schlüssel sind dann vorhanden, siehe
    anforderung.yaml REQ-EXTENDED-MODE-RESILIENCE."""
    basic_only_data = {
        "switch_state": 2,
        "switch_state_text": "Ein",
        "setpoint_power": 0,
        "setpoint_cosphi": 0,
        "soc": 55,
        "timed_charge_active": False,
    }

    for description in SENSOR_DESCRIPTIONS:
        description.value_fn(basic_only_data)
