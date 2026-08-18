"""Konsistenz-Tests für die (datengetriebene) Liste der Sensor-Beschreibungen.

Bei ~48 Sensoren ist ein Tippfehler in einem translation_key oder ein
doppelter unique_id-Suffix leicht zu übersehen - diese Tests fangen das ab,
ohne dass für jeden einzelnen Sensor ein eigener Test geschrieben werden muss.
"""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.sax_power.sensor import SENSOR_DESCRIPTIONS

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "sax_power"


def test_sensor_keys_are_unique() -> None:
    keys = [description.key for description in SENSOR_DESCRIPTIONS]
    assert len(keys) == len(set(keys))


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


def test_value_fn_handles_full_data_dict() -> None:
    """Jede value_fn muss mit einem vollständig befüllten Datensatz umgehen
    können, ohne eine Exception zu werfen (z. B. KeyError bei Tippfehlern)."""
    full_data = {
        "switch_state": 2,
        "switch_state_text": "Ein",
        "setpoint_power": 0,
        "setpoint_cosphi": 0,
        "soc": 55,
        "power": 1200,
        "smartmeter_power": -300,
        "discharge_limit": 3000,
        "charge_limit": 3000,
        "ext_sunspec_id": 1,
        "ext_sunspec_length": 2,
        "ext_current_sum_native": 99.0,
        "ext_current_l1": 5.0,
        "ext_current_l2": 6.0,
        "ext_current_l3": 7.0,
        "ext_current_sf": 0,
        "ext_current_sum": 18.0,
        "ext_voltage_l1": 230.0,
        "ext_voltage_l2": 231.0,
        "ext_voltage_l3": 229.0,
        "ext_voltage_sf": -1,
        "ext_voltage_sum": 690.0,
        "ext_power_active": 1000.0,
        "ext_power_active_sf": 0,
        "ext_frequency": 50.0,
        "ext_frequency_sf": -1,
        "ext_power_apparent": 1100.0,
        "ext_power_apparent_sf": 0,
        "ext_power_reactive": 100.0,
        "ext_power_reactive_sf": 0,
        "ext_power_factor": 95.0,
        "ext_power_factor_sf": -1,
        "sm_energy_fed_in": 1000.0,
        "sm_energy_consumed": 2000.0,
        "sm_energy_sf": 0,
        "sm_switch_state": 2,
        "sm_switch_state_text": "Ein",
        "sm_current_l1": 5.0,
        "sm_current_l2": 6.0,
        "sm_current_l3": 7.0,
        "sm_current_sum": 18.0,
        "sm_power_l1": 300.0,
        "sm_power_l2": 400.0,
        "sm_power_l3": 500.0,
        "sm_power_sf": 0,
        "sm_power_sum": 1200.0,
        "sm_voltage_l1": 231,
        "sm_voltage_l2": 232,
        "sm_voltage_l3": 233,
        "sm_voltage_sum": 696,
        "sm_power_total": 1200,
    }

    for description in SENSOR_DESCRIPTIONS:
        description.value_fn(full_data)
