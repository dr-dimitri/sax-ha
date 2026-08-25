"""Reine Decodertests für custom_components/sax_power/domain/sunspec.py.

Charakterisierungstests für sämtliche heute veröffentlichten LOW-/HIGH-Felder
- ohne Coordinator, ohne Home Assistant, ohne pymodbus. Die Coordinator- und
TCP-Integrationstests bleiben daneben der Wire-/Adapter-Nachweis (welcher
Registerausschnitt wann gelesen und an welchen Decoder gereicht wird).

Siehe anforderung.yaml: REQ-SUNSPEC-MODE-CORRECTION (Feldzuordnung/
Vorzeichenkonvention), REQ-SUNSPEC-DATATYPES (Sentinelwerte),
REQ-LOW-INTERVAL-REGISTERS (Aufteilung LOW/HIGH).
"""

from __future__ import annotations

import pytest

from custom_components.sax_power.const import (
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_LOW1_COUNT,
    READ_BLOCK_EXT_LOW1_START,
    READ_BLOCK_EXT_LOW2_COUNT,
    READ_BLOCK_EXT_LOW2_START,
    READ_BLOCK_EXT_START,
    UNKNOWN_LABEL,
)
from custom_components.sax_power.domain.registers import to_unsigned16
from custom_components.sax_power.domain.sunspec import (
    DEFAULT_BATTERY_SCALE_FACTORS,
    HIGH_BLOCK_FIELDS,
    BatteryScaleFactors,
    EnumField,
    ScaledField,
    SunSpecDecodeError,
    decode_high_block,
    decode_identity,
    decode_low_blocks,
)


def _block(start: int, count: int, values: dict[int, int]) -> list[int]:
    """Baut einen Registerblock aus internen SunSpec-Adressen.

    Nicht gesetzte Register sind 0 - bei Scale-Faktoren also Faktor 1, damit
    skalierte Werte im Test den Rohwerten entsprechen.
    """
    registers = [0] * count
    for address, value in values.items():
        registers[address - start] = value
    return registers


def _low1(overrides: dict[int, int] | None = None) -> list[int]:
    values = {
        0: 21365,  # SunS (Hi)
        1: 28243,  # SunS (Lo)
        2: 1,  # Common Model ID
        3: 15,  # Common Länge
        4: 21313,  # Hersteller "SA"
        5: 22608,  # "XP"
        6: 20311,  # "OW"
        7: 17746,  # "ER" -> "SAXPOWER"
        8: 18511,  # Gerätemodell "HO"
        9: 19781,  # "ME"
        10: 0,  # kein "PL"-Suffix -> "HOME"
        11: 23,  # Version Master
        12: 56,  # Version Gateway
        13: 15448,  # Seriennummer Hi
        14: 97,  # Seriennummer Lo
        15: 103,  # Inverter Model-ID
        16: 32,  # Inverter Länge
    }
    values.update(overrides or {})
    return _block(READ_BLOCK_EXT_LOW1_START, READ_BLOCK_EXT_LOW1_COUNT, values)


def _low2(overrides: dict[int, int] | None = None) -> list[int]:
    values = {
        110: 0,  # Scalefaktor Kapazität
        111: 0,  # Scalefaktor Lade-/Entladeleistung
        112: 0,  # Scalefaktor SoC
        113: 0,  # Reserve
        114: 0,  # Scalefaktor Zellspannung
    }
    values.update(overrides or {})
    return _block(READ_BLOCK_EXT_LOW2_START, READ_BLOCK_EXT_LOW2_COUNT, values)


def _high(overrides: dict[int, int] | None = None) -> list[int]:
    return _block(READ_BLOCK_EXT_START, READ_BLOCK_EXT_COUNT, overrides or {})


# -- LOW-Block: Common Model (1) + Battery-Skalierungsfaktoren ---------------


def test_decode_identity_decodes_common_model() -> None:
    """SunSpec Common Model: ASCII-Register, Firmwareversionen und die aus
    zwei uint16 zusammengesetzte Seriennummer."""
    identity = decode_identity(_low1())

    assert identity.manufacturer == "SAXPOWER"
    assert identity.model == "HOME"
    assert identity.version_master == 23
    assert identity.version_gateway == 56
    assert identity.serial_number == (15448 << 16) | 97


def test_decode_identity_as_data_uses_published_keys() -> None:
    """Die von Coordinator und Config Flow gemeinsam genutzten Schlüssel."""
    assert decode_identity(_low1()).as_data() == {
        "sun_manufacturer": "SAXPOWER",
        "sun_model": "HOME",
        "sun_version_master": 23,
        "sun_version_gateway": 56,
        "sun_serial_number": (15448 << 16) | 97,
    }


def test_decode_identity_appends_plus_suffix() -> None:
    """ "HOME" + "PL" -> "HOMEPL" (SAX Power Home Plus)."""
    identity = decode_identity(_low1({10: 20556}))  # "PL"

    assert identity.model == "HOMEPL"


def test_decode_identity_strips_trailing_padding() -> None:
    """SunSpec-str-Register sind rechts mit NUL/Blank aufgefüllt."""
    identity = decode_identity(_low1({6: 0x2000, 7: 0x0000}))

    assert identity.manufacturer == "SAXP"


@pytest.mark.parametrize("sentinel_address", [13, 14])
def test_decode_identity_serial_sentinel_yields_none(sentinel_address: int) -> None:
    """REQ-SUNSPEC-DATATYPES: meldet eine der beiden uint16-Hälften den
    "not implemented"-Sentinel 0xFFFF, ist die Seriennummer unbekannt statt
    halb erfunden."""
    identity = decode_identity(_low1({sentinel_address: 0xFFFF}))

    assert identity.serial_number is None


def test_decode_identity_version_sentinel_yields_none() -> None:
    identity = decode_identity(_low1({11: 0xFFFF, 12: 0xFFFF}))

    assert identity.version_master is None
    assert identity.version_gateway is None


def test_decode_low_blocks_reads_battery_scale_factors() -> None:
    """Die vier ``sunssf``-Rohwerte des LOW2-Teilblocks landen unverändert in
    BatteryScaleFactors - decodiert wird erst in apply_typed_sunssf."""
    decoded = decode_low_blocks(
        _low1(),
        _low2({110: to_unsigned16(-1), 111: 0, 112: 0, 114: to_unsigned16(-3)}),
    )

    assert decoded.scale_factors == BatteryScaleFactors(
        capacity=to_unsigned16(-1),
        power=0,
        soc=0,
        cell_voltage=to_unsigned16(-3),
    )
    assert decoded.values["sun_manufacturer"] == "SAXPOWER"


def test_default_battery_scale_factors_are_neutral() -> None:
    """Vorgabewert vor dem ersten LOW-Read: alle vier Faktoren 0 (= Faktor 1),
    was laut modbus_llm.yaml zugleich der "wellknown"-Wert des Geräts ist."""
    assert DEFAULT_BATTERY_SCALE_FACTORS == BatteryScaleFactors(0, 0, 0, 0)


@pytest.mark.parametrize(
    ("low1_len", "low2_len"),
    [(READ_BLOCK_EXT_LOW1_COUNT - 1, READ_BLOCK_EXT_LOW2_COUNT), (0, 0)],
)
def test_decode_low_blocks_rejects_short_blocks(low1_len: int, low2_len: int) -> None:
    """Ein zu kurzer Teilblock muss als benannter Decodefehler auffallen,
    nicht als IndexError irgendwo tief in der Feldzuordnung."""
    with pytest.raises(SunSpecDecodeError):
        decode_low_blocks([0] * low1_len, [0] * low2_len)


def test_decode_low_blocks_rejects_short_low2_block() -> None:
    with pytest.raises(SunSpecDecodeError, match="LOW2"):
        decode_low_blocks(_low1(), [0] * (READ_BLOCK_EXT_LOW2_COUNT - 1))


# -- HIGH-Block: Modelle 103, 123, 203, 802 ---------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"scale_factor_address": 21, "battery_scale_factor": "soc"},
    ],
    ids=["keine", "beide"],
)
def test_scaled_field_requires_exactly_one_scale_factor_source(
    kwargs: dict[str, object],
) -> None:
    """Ein Tippfehler in der Feldtabelle muss beim Modulimport auffallen,
    nicht erst beim ersten Poll."""
    with pytest.raises(ValueError, match="Skalierungsquelle"):
        ScaledField("x", 17, signed=False, **kwargs)  # type: ignore[arg-type]


def test_decode_high_block_decodes_all_models() -> None:
    """Vollständige Feldzuordnung über alle vier Modelle des HIGH-Blocks -
    3Ph Inverter (103), Immediate Controls (123), WYE Connect 3Ph Meter (203)
    und Battery Base (802). Scale-Faktoren sind 0 (Faktor 1), sofern nicht
    ausdrücklich gesetzt."""
    high = _high(
        {
            17: 30,  # Speicher Stromsumme
            18: 5,
            19: 6,
            20: 7,
            25: 230,  # Speicher Spannung A
            26: 231,
            27: 229,
            29: 1500,  # Wirkleistung Speicher Summe -> storage_power_active
            31: 5000,  # Netzfrequenz am Speicher
            32: to_unsigned16(-2),  # Scalefaktor Netzfrequenz
            33: 1600,  # Scheinleistung
            35: 100,  # Blindleistung
            37: 95,  # Leistungsfaktor
            41: 35,  # Maximale Zelltemperatur
            43: 4,  # Zustand: Ein
            44: 0,  # Event: Normalbetrieb
            45: 42,  # PV-Leistung
            46: 1,  # Scalefaktor PV-Leistung
            49: 0,  # Leistungsvorgabe %
            50: 300,  # Timeout
            51: 1,  # Steuermodus: Sollwertvorgabe
            52: to_unsigned16(-2),  # Scalefaktor Leistungsvorgabe
            53: 4600,  # Referenzwert Maximalleistung
            56: 20,  # Netz Stromsumme
            57: 6,
            58: 7,
            59: 7,
            61: 230,  # Durchschnitt Spannung Netz L-N
            62: 231,  # Netzspannung L1
            63: 232,
            64: 233,
            70: 4999,  # Netzfrequenz
            71: to_unsigned16(-2),  # Scalefaktor Frequenz
            72: 250,  # Summenwirkleistung Netz -> smartmeter_power
            73: 100,  # Netzleistung L1
            74: 80,  # Netzleistung L2
            75: 70,  # Netzleistung L3
            77: 900,  # Summenscheinleistung Netz
            82: 120,  # Summenblindleistung Netz
            87: 990,  # Leistungsfaktor Netz Summe
            97: 7680,  # Kapazität Speichersystem
            98: 0,  # Verfügbare Ladeleistung
            99: 4600,  # Verfügbare Entladeleistung
            100: 100,  # Maximaler SoC
            101: 0,  # Minimaler SoC
            102: 55,  # Aktueller SoC
            103: 45,  # Entladetiefe
            106: 1,  # Ladestatus Akku: Leistung anliegend
            108: 0,  # Event: Normalbetrieb
            109: 3300,  # Durchschnittliche Zellspannung
        }
    )

    decoded = decode_high_block(high, DEFAULT_BATTERY_SCALE_FACTORS)
    data = decoded.values

    # Der Common-Model-Teil gehört zum LOW-Block und darf hier nicht auftauchen.
    assert "sun_manufacturer" not in data

    # -- Model 103 --
    assert data["storage_current_sum"] == 30
    assert data["storage_current_a"] == 5
    assert data["storage_current_b"] == 6
    assert data["storage_current_c"] == 7
    assert data["storage_voltage_a"] == 230
    assert data["storage_voltage_b"] == 231
    assert data["storage_voltage_c"] == 229
    assert data["storage_power_active"] == 1500
    assert data["storage_power_apparent"] == 1600
    assert data["storage_power_reactive"] == 100
    assert data["storage_power_factor"] == 95
    assert data["storage_frequency"] == 50.0
    assert data["storage_max_cell_temp"] == 35
    assert data["storage_state"] == 4
    assert data["storage_state_text"] == "Ein"
    assert data["storage_event"] == 0
    assert data["storage_event_text"] == "Normalbetrieb"
    assert data["pv_power"] == 420

    # -- Model 123 --
    assert data["ic_power_setpoint_pct"] == 0
    assert data["ic_timeout"] == 300
    assert data["ic_control_mode"] == 1
    assert data["ic_control_mode_text"] == "Sollwertvorgabe"
    assert data["ic_max_power_reference"] == 4600
    assert decoded.ic_power_setpoint_sf_raw == to_unsigned16(-2)

    # -- Model 203 --
    assert data["grid_current_sum"] == 20
    assert data["grid_current_l1"] == 6
    assert data["grid_current_l2"] == 7
    assert data["grid_current_l3"] == 7
    assert data["grid_voltage_ln_avg"] == 230
    assert data["grid_voltage_l1"] == 231
    assert data["grid_voltage_l2"] == 232
    assert data["grid_voltage_l3"] == 233
    assert data["grid_frequency"] == 49.99
    # Vorzeichenkonvention: das Rohregister meldet positiv bei Einspeisung,
    # data["smartmeter_power"] wird beim Einlesen negiert (Standarddarstellung
    # negativ = Einspeisung, positiv = Netzbezug) - siehe const.py,
    # SMARTMETER_PV_SURPLUS_THRESHOLD_WATT. Die drei Phasenwerte teilen sich
    # denselben Registerblock und damit dasselbe rohe Vorzeichen, werden also
    # ebenfalls negiert - ihre Summe entspricht weiterhin smartmeter_power.
    assert data["smartmeter_power"] == -250
    assert data["grid_power_active_l1"] == -100
    assert data["grid_power_active_l2"] == -80
    assert data["grid_power_active_l3"] == -70
    assert data["grid_power_apparent_sum"] == 900
    assert data["grid_power_reactive_sum"] == 120
    assert data["grid_power_factor_sum"] == 990

    # -- Model 802 --
    assert data["battery_capacity"] == 7680
    assert data["battery_charge_power_available"] == 0
    assert data["battery_discharge_power_available"] == 4600
    assert data["battery_soc_max"] == 100
    assert data["battery_soc_min"] == 0
    assert data["battery_soc"] == 55
    assert data["battery_discharge_depth"] == 45
    assert data["battery_charging_active"] is True
    assert data["battery_event"] == 0
    assert data["battery_event_text"] == "Normalbetrieb"
    assert data["battery_cell_voltage_avg"] == 3300


def test_decode_high_block_publishes_exactly_the_declared_fields() -> None:
    """Jedes Feld aus HIGH_BLOCK_FIELDS landet in coordinator.data - und nur
    diese. Fängt ab, dass ein neu ergänzter Feldtyp in decode_high_block
    stillschweigend übersprungen wird."""
    expected = set()
    for field in HIGH_BLOCK_FIELDS:
        expected.add(field.key)
        if isinstance(field, EnumField):
            expected.add(field.text_key)

    data = decode_high_block(_high(), DEFAULT_BATTERY_SCALE_FACTORS).values

    assert set(data) == expected


def test_decode_high_block_negates_grid_power_sign() -> None:
    """Einspeisung (Rohregister positiv) muss als negativer Anzeigewert
    ankommen, Netzbezug (Rohregister negativ) als positiver - und umgekehrt
    (REQ-SUNSPEC-MODE-CORRECTION, Vorzeichenkonvention)."""
    high = _high({72: to_unsigned16(-1200), 73: to_unsigned16(-400)})

    data = decode_high_block(high, DEFAULT_BATTERY_SCALE_FACTORS).values

    assert data["smartmeter_power"] == 1200
    assert data["grid_power_active_l1"] == 400


def test_decode_high_block_applies_signed_storage_power() -> None:
    """storage_power_active ist int16: Laden (negativ) darf nicht als
    ~65000 W ankommen."""
    high = _high({29: to_unsigned16(-2300)})

    data = decode_high_block(high, DEFAULT_BATTERY_SCALE_FACTORS).values

    assert data["storage_power_active"] == -2300


def test_decode_high_block_uses_battery_scale_factors_from_low_block() -> None:
    """Die vier Battery-Faktoren liegen im LOW2-Block und werden übergeben -
    decode_high_block liest sie nicht selbst (REQ-LOW-INTERVAL-REGISTERS)."""
    high = _high({97: 7680, 98: 460, 102: 55, 109: 3300})
    scale_factors = BatteryScaleFactors(
        capacity=1,
        power=1,
        soc=0,
        cell_voltage=to_unsigned16(-1),
    )

    data = decode_high_block(high, scale_factors).values

    assert data["battery_capacity"] == 76800
    assert data["battery_charge_power_available"] == 4600
    assert data["battery_soc"] == 55
    assert data["battery_cell_voltage_avg"] == 330.0


def test_decode_high_block_battery_scale_factor_sentinel_yields_none() -> None:
    """REQ-SUNSPEC-DATATYPES: ein sunssf-Sentinel im LOW-Block darf keinen
    Zehnerpotenz-Unterlauf erzeugen, sondern muss zu None führen."""
    high = _high({102: 55})
    scale_factors = BatteryScaleFactors(soc=0x8000)

    data = decode_high_block(high, scale_factors).values

    assert data["battery_soc"] is None


def test_decode_high_block_decodes_not_implemented_sentinels() -> None:
    """REQ-SUNSPEC-DATATYPES: Sentinelwerte ("not implemented", SunSpec Device
    Information Model Specification V1.1 Abschnitt 6.4) müssen als None
    ankommen statt als falscher Zahlenwert - weder als Unterlauf über einen
    Sentinel-Skalierungsfaktor noch als vorzeichenverdrehter uint16-Wert, und
    ohne dass die Negation von smartmeter_power/grid_power_active_* an einem
    None crasht."""
    high = _high(
        {
            17: 0xFFFF,  # uint16-Sentinel -> None
            29: 0x8000,  # int16-Sentinel -> storage_power_active None
            43: 0x8000,  # storage_state (int16) Sentinel -> None/Unbekannt
            44: 0xFFFF,  # storage_event (uint16) Sentinel -> None
            50: 0xFFFF,  # ic_timeout (uint16) Sentinel -> None
            51: 0xFFFF,  # ic_control_mode (uint16) Sentinel -> None
            53: 0xFFFF,  # ic_max_power_reference Sentinel -> None
            72: 0x8000,  # smartmeter_power-Rohwert Sentinel -> None
            73: 0x8000,  # grid_power_active_l1-Rohwert Sentinel -> None
            76: 0,  # meter_power_active_sf regulär, isoliert den Wert-Sentinel
            81: 0x8000,  # sunssf-Sentinel -> grid_power_apparent_sum None
            106: 0xFFFF,  # battery_charging_active Sentinel -> None
            108: 0xFFFF,  # battery_event Sentinel -> None
        }
    )

    data = decode_high_block(high, DEFAULT_BATTERY_SCALE_FACTORS).values

    assert data["storage_current_sum"] is None
    assert data["storage_power_active"] is None
    assert data["storage_state"] is None
    assert data["storage_state_text"] == UNKNOWN_LABEL
    assert data["storage_event"] is None
    assert data["storage_event_text"] == UNKNOWN_LABEL
    assert data["ic_timeout"] is None
    assert data["ic_control_mode"] is None
    assert data["ic_control_mode_text"] == UNKNOWN_LABEL
    assert data["ic_max_power_reference"] is None
    assert data["smartmeter_power"] is None
    assert data["grid_power_active_l1"] is None
    assert data["grid_power_apparent_sum"] is None
    assert data["battery_charging_active"] is None
    assert data["battery_event"] is None
    assert data["battery_event_text"] == UNKNOWN_LABEL


@pytest.mark.parametrize(
    ("key", "text_key", "address", "raw", "expected_text"),
    [
        ("storage_state", "storage_state_text", 43, 99, UNKNOWN_LABEL),
        ("storage_event", "storage_event_text", 44, 99, UNKNOWN_LABEL),
        ("ic_control_mode", "ic_control_mode_text", 51, 99, UNKNOWN_LABEL),
        ("battery_event", "battery_event_text", 108, 99, UNKNOWN_LABEL),
    ],
)
def test_decode_high_block_unknown_enum_keeps_raw_value(
    key: str, text_key: str, address: int, raw: int, expected_text: str
) -> None:
    """Ein undokumentierter Enumwert darf nicht verschluckt werden: der
    Rohwert bleibt sichtbar, nur der Klartext fällt auf "Unbekannt" zurück."""
    data = decode_high_block(
        _high({address: raw}), DEFAULT_BATTERY_SCALE_FACTORS
    ).values

    assert data[key] == raw
    assert data[text_key] == expected_text


@pytest.mark.parametrize("raw", [2, 5, 0xFFFE])
def test_decode_high_block_battery_charging_active_rejects_non_boolean(
    raw: int,
) -> None:
    """Ein weder 0 noch 1 lautender Rohwert darf nicht still als True gelten."""
    data = decode_high_block(_high({106: raw}), DEFAULT_BATTERY_SCALE_FACTORS).values

    assert data["battery_charging_active"] is None


def test_decode_high_block_rejects_short_block() -> None:
    with pytest.raises(SunSpecDecodeError, match="HIGH"):
        decode_high_block(
            [0] * (READ_BLOCK_EXT_COUNT - 1), DEFAULT_BATTERY_SCALE_FACTORS
        )


def test_decode_high_block_ignores_surplus_registers() -> None:
    """Ein längerer Block (z. B. ein alter Ein-Block-Read) bleibt lesbar -
    die Feldzuordnung greift ausschließlich über Blockstart + Offset."""
    high = _high({102: 55}) + [1234] * 5

    data = decode_high_block(high, DEFAULT_BATTERY_SCALE_FACTORS).values

    assert data["battery_soc"] == 55
