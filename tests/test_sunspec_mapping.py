"""Bindet die Feldzuordnung in domain/sunspec.py parametrisch an
modbus_llm.yaml als überprüfbare Quelle an.

modbus_llm.yaml ist die gegen modbus.pdf und echte Hardware verifizierte
Registerkarte (siehe anforderung.yaml, REQ-SUNSPEC-MODE-CORRECTION). Die
Datei wird bewusst NUR im Test geladen, nie zur Laufzeit: die Integration
soll ohne YAML-Parser und ohne Dateizugriff decodieren. Der Test schließt
damit die Lücke, dass Adressverschiebungen oder eine falsche
Signed/Unsigned-Entscheidung bisher nur über große Coordinator-Fixtures
auffielen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from custom_components.sax_power import const
from custom_components.sax_power.const import (
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_LOW1_COUNT,
    READ_BLOCK_EXT_LOW1_START,
    READ_BLOCK_EXT_LOW2_COUNT,
    READ_BLOCK_EXT_LOW2_START,
    READ_BLOCK_EXT_START,
)
from custom_components.sax_power.domain.sunspec import (
    HIGH_BLOCK_FIELDS,
    BatteryScaleFactors,
    BoolField,
    EnumField,
    RawField,
    ScaledField,
)

MODBUS_YAML_PATH = Path(__file__).resolve().parents[1] / "modbus_llm.yaml"

#: Adress-Offset des SunSpec-Modus (Slave-ID 100), siehe AGENTS.md und
#: modbus_llm.yaml (connection_settings.addressing_rule).
SUNSPEC_ADDRESS_OFFSET = 40000
SUNSPEC_SLAVE_ID = 100


def _load_sunspec_registers() -> dict[int, dict[str, Any]]:
    document = yaml.safe_load(MODBUS_YAML_PATH.read_text(encoding="utf-8"))
    for register_map in document["register_maps"]:
        if register_map["slave_id"] == SUNSPEC_SLAVE_ID:
            return {
                register["internal_addr"]: register
                for register in register_map["registers"]
            }
    raise AssertionError(
        f"modbus_llm.yaml enthält keine Registerkarte für Slave-ID "
        f"{SUNSPEC_SLAVE_ID}."
    )


SUNSPEC_REGISTERS = _load_sunspec_registers()


def _is_signed(internal_address: int) -> bool:
    """Signed laut dokumentiertem SunSpec-Datentyp (REQ-SUNSPEC-DATATYPES).

    int16 und sunssf sind signiert, uint16/enum16/bitfield16 nicht.
    """
    datatype = SUNSPEC_REGISTERS[internal_address]["datatype"]
    assert datatype in (
        "int16",
        "uint16",
    ), f"Register {internal_address}: unerwarteter Datentyp {datatype!r}."
    return datatype == "int16"


def _field_ids(fields: tuple[Any, ...]) -> list[str]:
    return [field.key for field in fields]


# -- const.py gegen modbus_llm.yaml ----------------------------------------


SUN_REGISTER_CONSTANTS = sorted(
    name
    for name in dir(const)
    if name.startswith("REG_SUN_") and isinstance(getattr(const, name), int)
)


@pytest.mark.parametrize("name", SUN_REGISTER_CONSTANTS)
def test_sun_register_constant_matches_documented_address(name: str) -> None:
    """Jede REG_SUN_*-Konstante ist eine in modbus_llm.yaml dokumentierte
    interne Adresse, und deren Protokolladresse folgt dem SunSpec-Offset
    -40000 (nicht dem Basic-Mode-Offset -40001)."""
    internal_address = getattr(const, name)
    register = SUNSPEC_REGISTERS.get(internal_address)

    assert (
        register is not None
    ), f"{name} = {internal_address} ist in modbus_llm.yaml nicht dokumentiert."
    assert register["protocol_addr"] - SUNSPEC_ADDRESS_OFFSET == internal_address


def test_read_blocks_stay_inside_documented_map_and_do_not_overlap() -> None:
    """Die drei gelesenen Teilblöcke liegen innerhalb der dokumentierten
    Registerkarte, überlappen sich nicht und lassen keine Lücke - sonst
    entstünde entweder ein zusätzlicher Modbus-Request oder ein still
    verlorenes Register (REQ-LOW-INTERVAL-REGISTERS).

    Geprüft werden Blockgrenzen, nicht jede Einzeladresse: die ASCII-Felder
    des Common Model belegen laut modbus_llm.yaml mehrere Register, sind dort
    aber nur unter ihrer Startadresse aufgeführt.
    """
    low1 = range(
        READ_BLOCK_EXT_LOW1_START, READ_BLOCK_EXT_LOW1_START + READ_BLOCK_EXT_LOW1_COUNT
    )
    high = range(READ_BLOCK_EXT_START, READ_BLOCK_EXT_START + READ_BLOCK_EXT_COUNT)
    low2 = range(
        READ_BLOCK_EXT_LOW2_START, READ_BLOCK_EXT_LOW2_START + READ_BLOCK_EXT_LOW2_COUNT
    )

    documented = SUNSPEC_REGISTERS.keys()
    for block in (low1, high, low2):
        assert min(documented) <= block.start
        assert block[-1] <= max(documented)

    # Lückenlos aneinandergereiht: LOW1 | HIGH | LOW2.
    assert low1[-1] + 1 == high.start
    assert high[-1] + 1 == low2.start


# -- Feldzuordnung des HIGH-Blocks ------------------------------------------


@pytest.mark.parametrize("field", HIGH_BLOCK_FIELDS, ids=_field_ids(HIGH_BLOCK_FIELDS))
def test_high_block_field_address_is_inside_high_block(field: Any) -> None:
    """Kein Feld darf aus dem tatsächlich gelesenen Blockausschnitt
    herauszeigen - sonst liefe der Decoder in einen IndexError oder läse
    stillschweigend das falsche Register."""
    high = range(READ_BLOCK_EXT_START, READ_BLOCK_EXT_START + READ_BLOCK_EXT_COUNT)

    assert field.address in high
    if isinstance(field, ScaledField) and field.scale_factor_address is not None:
        assert field.scale_factor_address in high


@pytest.mark.parametrize("field", HIGH_BLOCK_FIELDS, ids=_field_ids(HIGH_BLOCK_FIELDS))
def test_high_block_field_signedness_matches_documented_datatype(field: Any) -> None:
    """REQ-SUNSPEC-DATATYPES: die Signed/Unsigned-Entscheidung jedes Feldes
    muss dem in modbus_llm.yaml dokumentierten Datentyp entsprechen. Ohne
    diese Prüfung verwechselt ein falsch gesetztes Flag 0xFFFF ("not
    implemented") mit -1 bzw. 0x8001 mit -32767."""
    if isinstance(field, BoolField):
        # 0/1-Register sind laut modbus_llm.yaml uint16.
        assert not _is_signed(field.address)
        return

    assert field.signed == _is_signed(field.address)


@pytest.mark.parametrize(
    "field",
    [field for field in HIGH_BLOCK_FIELDS if isinstance(field, ScaledField)],
    ids=[field.key for field in HIGH_BLOCK_FIELDS if isinstance(field, ScaledField)],
)
def test_scaled_field_uses_exactly_one_documented_scale_factor(
    field: ScaledField,
) -> None:
    """Genau eine Skalierungsquelle je Feld, und ein im HIGH-Block liegender
    Faktor muss dort auch als ``sunssf`` dokumentiert sein."""
    has_address = field.scale_factor_address is not None
    has_battery = field.battery_scale_factor is not None

    assert (
        has_address != has_battery
    ), f"{field.key}: genau eine Skalierungsquelle erwartet."

    if has_address:
        register = SUNSPEC_REGISTERS[field.scale_factor_address]
        assert register.get("unit") == "sunssf", (
            f"{field.key}: Register {field.scale_factor_address} ist in "
            "modbus_llm.yaml kein Scalefaktor."
        )
    else:
        assert field.battery_scale_factor in {
            f.name for f in BatteryScaleFactors.__dataclass_fields__.values()
        }


@pytest.mark.parametrize(
    ("attribute", "constant_name"),
    [
        ("capacity", "REG_SUN_BATTERY_CAPACITY_SF"),
        ("power", "REG_SUN_BATTERY_POWER_SF"),
        ("soc", "REG_SUN_BATTERY_SOC_SF"),
        ("cell_voltage", "REG_SUN_BATTERY_CELL_VOLTAGE_SF"),
    ],
)
def test_battery_scale_factor_registers_live_in_low2_block(
    attribute: str, constant_name: str
) -> None:
    """Die vier Battery-Faktoren liegen im LOW2-Teilblock und sind dort als
    ``sunssf`` dokumentiert - deshalb bekommt decode_high_block sie
    übergeben (REQ-LOW-INTERVAL-REGISTERS)."""
    address = getattr(const, constant_name)
    low2 = range(
        READ_BLOCK_EXT_LOW2_START, READ_BLOCK_EXT_LOW2_START + READ_BLOCK_EXT_LOW2_COUNT
    )

    assert address in low2
    assert SUNSPEC_REGISTERS[address].get("unit") == "sunssf"
    assert attribute in BatteryScaleFactors.__dataclass_fields__


def test_high_block_field_keys_are_unique() -> None:
    """Ein doppelter Schlüssel würde ein Feld stillschweigend überschreiben."""
    keys = [field.key for field in HIGH_BLOCK_FIELDS]
    keys += [
        field.text_key for field in HIGH_BLOCK_FIELDS if isinstance(field, EnumField)
    ]

    assert len(keys) == len(set(keys))


def test_high_block_addresses_are_unique() -> None:
    """Jede Adresse wird höchstens einmal als Werteregister veröffentlicht."""
    addresses = [field.address for field in HIGH_BLOCK_FIELDS]

    assert len(addresses) == len(set(addresses))


def test_enum_and_raw_fields_are_documented_as_enumerations_or_numbers() -> None:
    """Sanity-Check gegen Copy-Paste-Fehler: Enum-/Rohfelder dürfen keinen
    Scalefaktor-Registerplatz belegen."""
    for field in HIGH_BLOCK_FIELDS:
        if isinstance(field, EnumField | RawField | BoolField):
            assert SUNSPEC_REGISTERS[field.address].get("unit") != "sunssf"
