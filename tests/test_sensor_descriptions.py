"""Konsistenz-Tests für die (datengetriebene) Liste der Sensor-Beschreibungen.

Bei ~55 Sensoren ist ein Tippfehler in einem translation_key oder ein
doppelter unique_id-Suffix leicht zu übersehen - diese Tests fangen das ab,
ohne dass für jeden einzelnen Sensor ein eigener Test geschrieben werden muss.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from homeassistant.const import EntityCategory

from custom_components.sax_power.coordinator import SaxPowerCoordinator, to_unsigned16
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


def _full_data(hass) -> dict:
    """Baut einen vollständig befüllten, coordinator.data-artigen Datensatz.

    Nutzt die echte Coordinator-Parsing-Logik (_parse_extended) auf
    Testwerten statt einer manuell gepflegten Kopie aller ~55 Schlüssel -
    das hält den Test automatisch synchron mit dem tatsächlichen
    Register-Layout (siehe anforderung.yaml, REQ-SUNSPEC-MODE-CORRECTION).
    """
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
    )

    raw = dict.fromkeys(range(115), 0)
    raw[52] = to_unsigned16(-2)  # Scalefaktor Leistungsvorgabe (Immediate Controls)
    extended = coordinator._parse_extended(lambda address: raw[address])

    basic = {
        "switch_state": 2,
        "switch_state_text": "Ein",
        "setpoint_power": 0,
        "setpoint_cosphi": 0,
        "soc": 55,
        "timed_charge_active": False,
    }
    return {**basic, **extended}


def test_value_fn_handles_full_data_dict(hass) -> None:
    """Jede value_fn muss mit einem vollständig befüllten Datensatz umgehen
    können, ohne eine Exception zu werfen (z. B. KeyError bei Tippfehlern)."""
    full_data = _full_data(hass)

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
        "smartmeter_power",
        "storage_max_cell_temp",
        "pv_power",
        "price_charge_status_text",
        "price_charge_next_start",
    )
    for key in core_keys:
        description = _description_by_key(key)
        assert description.entity_category is None, key


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
