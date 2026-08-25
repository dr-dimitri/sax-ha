"""Reine SunSpec-Protokolldecodierung für den SAX-Registerblock (Slave-ID 100).

Framework-frei: dieses Modul kennt weder Home Assistant noch pymodbus und
arbeitet ausschließlich auf ``Sequence[int]``-Registerblöcken, wie sie ein
einzelner ``read_holding_registers``-Aufruf liefert. Der Coordinator behält
Transport, Poll-Intervalle, Caches, Resilienz/Repair-Verhalten und die
Entscheidung, wann alte LOW-Skalierungsfaktoren weiterverwendet werden -
siehe anforderung.yaml, REQ-LOW-INTERVAL-REGISTERS/
REQ-HIGH-INTERVAL-REGISTERS und DEVELOPMENT.md ("Registerblock -> Decoder ->
Coordinator-Daten").

Die Feldzuordnung liegt bewusst als deklarative Tabelle (`HIGH_BLOCK_FIELDS`)
vor und nicht als handgeschriebenes dict-Literal: nur so lässt sich jede
Adresse und jede Signed/Unsigned-Entscheidung parametrisch gegen
modbus_llm.yaml prüfen (siehe tests/test_sunspec_mapping.py), statt sie in
einer 200-Zeilen-Funktion gegen Fixtures zu verstecken.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..const import (
    BATTERY_EVENT_LABELS,
    CONTROL_MODE_LABELS,
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_LOW1_COUNT,
    READ_BLOCK_EXT_LOW1_START,
    READ_BLOCK_EXT_LOW2_COUNT,
    READ_BLOCK_EXT_LOW2_START,
    READ_BLOCK_EXT_START,
    REG_SUN_BATTERY_CAPACITY,
    REG_SUN_BATTERY_CAPACITY_SF,
    REG_SUN_BATTERY_CELL_VOLTAGE_AVG,
    REG_SUN_BATTERY_CELL_VOLTAGE_SF,
    REG_SUN_BATTERY_CHARGE_POWER_AVAILABLE,
    REG_SUN_BATTERY_CHARGING_ACTIVE,
    REG_SUN_BATTERY_DISCHARGE_DEPTH,
    REG_SUN_BATTERY_DISCHARGE_POWER_AVAILABLE,
    REG_SUN_BATTERY_EVENT,
    REG_SUN_BATTERY_POWER_SF,
    REG_SUN_BATTERY_SOC,
    REG_SUN_BATTERY_SOC_MAX,
    REG_SUN_BATTERY_SOC_MIN,
    REG_SUN_BATTERY_SOC_SF,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_MAX_POWER_REFERENCE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    REG_SUN_IC_POWER_SETPOINT_SF,
    REG_SUN_IC_TIMEOUT,
    REG_SUN_MANUFACTURER,
    REG_SUN_METER_CURRENT_L1,
    REG_SUN_METER_CURRENT_L2,
    REG_SUN_METER_CURRENT_L3,
    REG_SUN_METER_CURRENT_SF,
    REG_SUN_METER_CURRENT_SUM,
    REG_SUN_METER_FREQUENCY,
    REG_SUN_METER_FREQUENCY_SF,
    REG_SUN_METER_POWER_ACTIVE_L1,
    REG_SUN_METER_POWER_ACTIVE_L2,
    REG_SUN_METER_POWER_ACTIVE_L3,
    REG_SUN_METER_POWER_ACTIVE_SF,
    REG_SUN_METER_POWER_ACTIVE_SUM,
    REG_SUN_METER_POWER_APPARENT_SF,
    REG_SUN_METER_POWER_APPARENT_SUM,
    REG_SUN_METER_POWER_FACTOR_SF,
    REG_SUN_METER_POWER_FACTOR_SUM,
    REG_SUN_METER_POWER_REACTIVE_SF,
    REG_SUN_METER_POWER_REACTIVE_SUM,
    REG_SUN_METER_VOLTAGE_L1,
    REG_SUN_METER_VOLTAGE_L2,
    REG_SUN_METER_VOLTAGE_L3,
    REG_SUN_METER_VOLTAGE_LN_AVG,
    REG_SUN_METER_VOLTAGE_SF,
    REG_SUN_MODEL,
    REG_SUN_PV_POWER,
    REG_SUN_PV_POWER_SF,
    REG_SUN_SERIAL_HI,
    REG_SUN_SERIAL_LO,
    REG_SUN_STORAGE_CURRENT_A,
    REG_SUN_STORAGE_CURRENT_B,
    REG_SUN_STORAGE_CURRENT_C,
    REG_SUN_STORAGE_CURRENT_SF,
    REG_SUN_STORAGE_CURRENT_SUM,
    REG_SUN_STORAGE_EVENT,
    REG_SUN_STORAGE_FREQUENCY,
    REG_SUN_STORAGE_FREQUENCY_SF,
    REG_SUN_STORAGE_MAX_CELL_TEMP,
    REG_SUN_STORAGE_POWER_ACTIVE,
    REG_SUN_STORAGE_POWER_ACTIVE_SF,
    REG_SUN_STORAGE_POWER_APPARENT,
    REG_SUN_STORAGE_POWER_APPARENT_SF,
    REG_SUN_STORAGE_POWER_FACTOR,
    REG_SUN_STORAGE_POWER_FACTOR_SF,
    REG_SUN_STORAGE_POWER_REACTIVE,
    REG_SUN_STORAGE_POWER_REACTIVE_SF,
    REG_SUN_STORAGE_STATE,
    REG_SUN_STORAGE_TEMP_SF,
    REG_SUN_STORAGE_VOLTAGE_A,
    REG_SUN_STORAGE_VOLTAGE_B,
    REG_SUN_STORAGE_VOLTAGE_C,
    REG_SUN_STORAGE_VOLTAGE_SF,
    REG_SUN_VERSION_GATEWAY,
    REG_SUN_VERSION_MASTER,
    STORAGE_EVENT_LABELS,
    STORAGE_STATE_LABELS,
    UNKNOWN_LABEL,
)
from .registers import (
    apply_typed_sunssf,
    decode_ascii_registers,
    decode_bool16,
    decode_int16,
    decode_uint16,
    to_unsigned16,
)

MANUFACTURER_REGISTER_COUNT = 4
MODEL_REGISTER_COUNT = 3


class SunSpecDecodeError(ValueError):
    """Ein Registerblock ist kürzer als das dokumentierte Modell-Layout.

    Bewusst eine eigene Ausnahme statt eines rohen IndexError irgendwo tief
    in der Feldzuordnung: nur so ist im Log erkennbar, welcher Teilblock zu
    kurz geantwortet hat.
    """


@dataclass(frozen=True, slots=True)
class BatteryScaleFactors:
    """Die vier ``sunssf``-Rohwerte aus dem LOW2-Teilblock (Modell 802).

    Rohwerte, nicht decodierte Exponenten: ``apply_typed_sunssf`` prüft den
    "not implemented"-Sentinel selbst und muss dafür das unveränderte
    Register sehen (siehe anforderung.yaml, REQ-SUNSPEC-DATATYPES).
    """

    capacity: int = 0
    power: int = 0
    soc: int = 0
    cell_voltage: int = 0


#: Ausgangszustand, solange der LOW-Block noch nie erfolgreich gelesen wurde.
#: Entspricht dem bisherigen Coordinator-Verhalten (alle vier Rohwerte 0, was
#: laut modbus_llm.yaml zugleich der "wellknown"-Wert des Geräts ist).
DEFAULT_BATTERY_SCALE_FACTORS = BatteryScaleFactors()

#: Rohwert für den "wellknown" Scalefaktor -2 von Register 40052, solange der
#: HIGH-Block noch nie gelesen wurde (siehe modbus_llm.yaml).
DEFAULT_IC_POWER_SETPOINT_SF_RAW = to_unsigned16(-2)


@dataclass(frozen=True, slots=True)
class DecodedIdentity:
    """SunSpec Common Model (ID 1) - Geräteidentität."""

    manufacturer: str
    model: str
    version_master: int | None
    version_gateway: int | None
    serial_number: int | None

    def as_data(self) -> dict[str, Any]:
        """Die Identität unter den von Coordinator und Config Flow
        gemeinsam genutzten ``sun_*``-Schlüsseln."""
        return {
            "sun_manufacturer": self.manufacturer,
            "sun_model": self.model,
            "sun_version_master": self.version_master,
            "sun_version_gateway": self.version_gateway,
            "sun_serial_number": self.serial_number,
        }


@dataclass(frozen=True, slots=True)
class DecodedLowBlock:
    """Ergebnis der beiden LOW-Intervall-Teilblöcke."""

    identity: DecodedIdentity
    scale_factors: BatteryScaleFactors

    @property
    def values(self) -> dict[str, Any]:
        """Die veröffentlichten Felder des LOW-Blocks."""
        return self.identity.as_data()


@dataclass(frozen=True, slots=True)
class DecodedHighBlock:
    """Ergebnis des HIGH-Intervall-Teilblocks."""

    values: Mapping[str, Any]
    #: Rohwert von Register 40052, den der Schreibpfad (Watt -> Prozent)
    #: braucht. Bleibt Rohwert, weil dort eine eigene, strengere
    #: Sentinel-/Bereichsprüfung vor jedem Write stattfindet.
    ic_power_setpoint_sf_raw: int


@dataclass(frozen=True, slots=True)
class ScaledField:
    """Ein mit einem ``sunssf``-Register skalierter Messwert.

    Genau eine der beiden Skalierungsquellen ist gesetzt:
    ``scale_factor_address`` (Register im selben HIGH-Block) oder
    ``battery_scale_factor`` (Attributname auf ``BatteryScaleFactors``, weil
    diese vier Faktoren im separaten LOW2-Block liegen).

    ``signed`` muss dem in modbus_llm.yaml dokumentierten Datentyp des
    Werteregisters entsprechen (int16 -> True, uint16 -> False); sonst
    verwechselt der Decoder 0xFFFF ("not implemented") mit -1.
    """

    key: str
    address: int
    signed: bool
    scale_factor_address: int | None = None
    battery_scale_factor: str | None = None
    negate: bool = False

    def __post_init__(self) -> None:
        # Läuft einmalig beim Aufbau von HIGH_BLOCK_FIELDS (Modulimport):
        # ein Tippfehler in der Tabelle fällt damit sofort auf, statt erst
        # beim ersten Poll als TypeError im Decoder.
        if (self.scale_factor_address is None) == (self.battery_scale_factor is None):
            raise ValueError(
                f"{self.key}: genau eine Skalierungsquelle erwartet "
                "(scale_factor_address ODER battery_scale_factor)."
            )


@dataclass(frozen=True, slots=True)
class EnumField:
    """Ein Zustands-/Ereignisregister samt zugehörigem Klartext-Schlüssel."""

    key: str
    text_key: str
    address: int
    signed: bool
    labels: Mapping[int, str]


@dataclass(frozen=True, slots=True)
class RawField:
    """Ein unskalierter Zahlenwert (uint16/int16 ohne Scale-Faktor)."""

    key: str
    address: int
    signed: bool


@dataclass(frozen=True, slots=True)
class BoolField:
    """Ein 0/1-Register (uint16), das als Wahrheitswert veröffentlicht wird."""

    key: str
    address: int


HighBlockField = ScaledField | EnumField | RawField | BoolField

# Reihenfolge = Reihenfolge der Schlüssel in coordinator.data. Adressen sind
# interne SunSpec-Adressen (Protokolladresse - 40000), siehe const.py.
HIGH_BLOCK_FIELDS: tuple[HighBlockField, ...] = (
    # -- Model 103: 3Ph Inverter (Speicherelektronik) --
    ScaledField(
        "storage_current_sum",
        REG_SUN_STORAGE_CURRENT_SUM,
        signed=False,
        scale_factor_address=REG_SUN_STORAGE_CURRENT_SF,
    ),
    ScaledField(
        "storage_current_a",
        REG_SUN_STORAGE_CURRENT_A,
        signed=False,
        scale_factor_address=REG_SUN_STORAGE_CURRENT_SF,
    ),
    ScaledField(
        "storage_current_b",
        REG_SUN_STORAGE_CURRENT_B,
        signed=False,
        scale_factor_address=REG_SUN_STORAGE_CURRENT_SF,
    ),
    ScaledField(
        "storage_current_c",
        REG_SUN_STORAGE_CURRENT_C,
        signed=False,
        scale_factor_address=REG_SUN_STORAGE_CURRENT_SF,
    ),
    ScaledField(
        "storage_voltage_a",
        REG_SUN_STORAGE_VOLTAGE_A,
        signed=False,
        scale_factor_address=REG_SUN_STORAGE_VOLTAGE_SF,
    ),
    ScaledField(
        "storage_voltage_b",
        REG_SUN_STORAGE_VOLTAGE_B,
        signed=False,
        scale_factor_address=REG_SUN_STORAGE_VOLTAGE_SF,
    ),
    ScaledField(
        "storage_voltage_c",
        REG_SUN_STORAGE_VOLTAGE_C,
        signed=False,
        scale_factor_address=REG_SUN_STORAGE_VOLTAGE_SF,
    ),
    ScaledField(
        "storage_power_active",
        REG_SUN_STORAGE_POWER_ACTIVE,
        signed=True,
        scale_factor_address=REG_SUN_STORAGE_POWER_ACTIVE_SF,
    ),
    ScaledField(
        "storage_power_apparent",
        REG_SUN_STORAGE_POWER_APPARENT,
        signed=False,
        scale_factor_address=REG_SUN_STORAGE_POWER_APPARENT_SF,
    ),
    ScaledField(
        "storage_power_reactive",
        REG_SUN_STORAGE_POWER_REACTIVE,
        signed=True,
        scale_factor_address=REG_SUN_STORAGE_POWER_REACTIVE_SF,
    ),
    ScaledField(
        "storage_power_factor",
        REG_SUN_STORAGE_POWER_FACTOR,
        signed=True,
        scale_factor_address=REG_SUN_STORAGE_POWER_FACTOR_SF,
    ),
    ScaledField(
        "storage_frequency",
        REG_SUN_STORAGE_FREQUENCY,
        signed=False,
        scale_factor_address=REG_SUN_STORAGE_FREQUENCY_SF,
    ),
    ScaledField(
        "storage_max_cell_temp",
        REG_SUN_STORAGE_MAX_CELL_TEMP,
        signed=True,
        scale_factor_address=REG_SUN_STORAGE_TEMP_SF,
    ),
    EnumField(
        "storage_state",
        "storage_state_text",
        REG_SUN_STORAGE_STATE,
        signed=True,
        labels=STORAGE_STATE_LABELS,
    ),
    EnumField(
        "storage_event",
        "storage_event_text",
        REG_SUN_STORAGE_EVENT,
        signed=False,
        labels=STORAGE_EVENT_LABELS,
    ),
    # PV-Leistung laut modbus.pdf nur mit Smartmeter ADW200 verfügbar - mit
    # ADL400 typischerweise 0, siehe anforderung.yaml.
    ScaledField(
        "pv_power",
        REG_SUN_PV_POWER,
        signed=False,
        scale_factor_address=REG_SUN_PV_POWER_SF,
    ),
    # -- Model 123: Immediate Controls --
    ScaledField(
        "ic_power_setpoint_pct",
        REG_SUN_IC_POWER_SETPOINT_PCT,
        signed=True,
        scale_factor_address=REG_SUN_IC_POWER_SETPOINT_SF,
    ),
    RawField("ic_timeout", REG_SUN_IC_TIMEOUT, signed=False),
    EnumField(
        "ic_control_mode",
        "ic_control_mode_text",
        REG_SUN_IC_CONTROL_MODE,
        signed=False,
        labels=CONTROL_MODE_LABELS,
    ),
    RawField("ic_max_power_reference", REG_SUN_IC_MAX_POWER_REFERENCE, signed=False),
    # -- Model 203: WYE Connect 3Ph Meter (Netz/Smart Meter) --
    ScaledField(
        "grid_current_sum",
        REG_SUN_METER_CURRENT_SUM,
        signed=False,
        scale_factor_address=REG_SUN_METER_CURRENT_SF,
    ),
    ScaledField(
        "grid_current_l1",
        REG_SUN_METER_CURRENT_L1,
        signed=False,
        scale_factor_address=REG_SUN_METER_CURRENT_SF,
    ),
    ScaledField(
        "grid_current_l2",
        REG_SUN_METER_CURRENT_L2,
        signed=False,
        scale_factor_address=REG_SUN_METER_CURRENT_SF,
    ),
    ScaledField(
        "grid_current_l3",
        REG_SUN_METER_CURRENT_L3,
        signed=False,
        scale_factor_address=REG_SUN_METER_CURRENT_SF,
    ),
    ScaledField(
        "grid_voltage_ln_avg",
        REG_SUN_METER_VOLTAGE_LN_AVG,
        signed=False,
        scale_factor_address=REG_SUN_METER_VOLTAGE_SF,
    ),
    ScaledField(
        "grid_voltage_l1",
        REG_SUN_METER_VOLTAGE_L1,
        signed=False,
        scale_factor_address=REG_SUN_METER_VOLTAGE_SF,
    ),
    ScaledField(
        "grid_voltage_l2",
        REG_SUN_METER_VOLTAGE_L2,
        signed=False,
        scale_factor_address=REG_SUN_METER_VOLTAGE_SF,
    ),
    ScaledField(
        "grid_voltage_l3",
        REG_SUN_METER_VOLTAGE_L3,
        signed=False,
        scale_factor_address=REG_SUN_METER_VOLTAGE_SF,
    ),
    ScaledField(
        "grid_frequency",
        REG_SUN_METER_FREQUENCY,
        signed=False,
        scale_factor_address=REG_SUN_METER_FREQUENCY_SF,
    ),
    # Ersetzt das früher fehlerhafte "smartmeter_power" (Basic Mode, Register
    # 48), siehe anforderung.yaml REQ-SUNSPEC-MODE-CORRECTION. negate=True:
    # Standarddarstellung ist negativ = Einspeisung ins Netz (PV-Überschuss),
    # positiv = Netzbezug - das Register selbst meldet das Gegenteil (siehe
    # REQ-SUNSPEC-MODE-CORRECTION, Abschnitt Vorzeichenkonvention).
    ScaledField(
        "smartmeter_power",
        REG_SUN_METER_POWER_ACTIVE_SUM,
        signed=True,
        scale_factor_address=REG_SUN_METER_POWER_ACTIVE_SF,
        negate=True,
    ),
    # Dieselbe Negation wie bei smartmeter_power (siehe oben) - die drei
    # Phasenwerte sind Teil desselben Registerblocks und teilen sich dessen
    # Rohvorzeichen; ohne Negation würde ihre Summe nicht mehr zum bereits
    # negierten smartmeter_power passen.
    ScaledField(
        "grid_power_active_l1",
        REG_SUN_METER_POWER_ACTIVE_L1,
        signed=True,
        scale_factor_address=REG_SUN_METER_POWER_ACTIVE_SF,
        negate=True,
    ),
    ScaledField(
        "grid_power_active_l2",
        REG_SUN_METER_POWER_ACTIVE_L2,
        signed=True,
        scale_factor_address=REG_SUN_METER_POWER_ACTIVE_SF,
        negate=True,
    ),
    ScaledField(
        "grid_power_active_l3",
        REG_SUN_METER_POWER_ACTIVE_L3,
        signed=True,
        scale_factor_address=REG_SUN_METER_POWER_ACTIVE_SF,
        negate=True,
    ),
    ScaledField(
        "grid_power_apparent_sum",
        REG_SUN_METER_POWER_APPARENT_SUM,
        signed=False,
        scale_factor_address=REG_SUN_METER_POWER_APPARENT_SF,
    ),
    ScaledField(
        "grid_power_reactive_sum",
        REG_SUN_METER_POWER_REACTIVE_SUM,
        signed=True,
        scale_factor_address=REG_SUN_METER_POWER_REACTIVE_SF,
    ),
    ScaledField(
        "grid_power_factor_sum",
        REG_SUN_METER_POWER_FACTOR_SUM,
        signed=True,
        scale_factor_address=REG_SUN_METER_POWER_FACTOR_SF,
    ),
    # -- Model 802: Battery Base (Akkuzellen) --
    ScaledField(
        "battery_capacity",
        REG_SUN_BATTERY_CAPACITY,
        signed=False,
        battery_scale_factor="capacity",
    ),
    ScaledField(
        "battery_charge_power_available",
        REG_SUN_BATTERY_CHARGE_POWER_AVAILABLE,
        signed=False,
        battery_scale_factor="power",
    ),
    ScaledField(
        "battery_discharge_power_available",
        REG_SUN_BATTERY_DISCHARGE_POWER_AVAILABLE,
        signed=False,
        battery_scale_factor="power",
    ),
    ScaledField(
        "battery_soc_max",
        REG_SUN_BATTERY_SOC_MAX,
        signed=False,
        battery_scale_factor="soc",
    ),
    ScaledField(
        "battery_soc_min",
        REG_SUN_BATTERY_SOC_MIN,
        signed=False,
        battery_scale_factor="soc",
    ),
    ScaledField(
        "battery_soc",
        REG_SUN_BATTERY_SOC,
        signed=False,
        battery_scale_factor="soc",
    ),
    ScaledField(
        "battery_discharge_depth",
        REG_SUN_BATTERY_DISCHARGE_DEPTH,
        signed=False,
        battery_scale_factor="soc",
    ),
    BoolField("battery_charging_active", REG_SUN_BATTERY_CHARGING_ACTIVE),
    EnumField(
        "battery_event",
        "battery_event_text",
        REG_SUN_BATTERY_EVENT,
        signed=False,
        labels=BATTERY_EVENT_LABELS,
    ),
    ScaledField(
        "battery_cell_voltage_avg",
        REG_SUN_BATTERY_CELL_VOLTAGE_AVG,
        signed=False,
        battery_scale_factor="cell_voltage",
    ),
)


def _block_reader(
    registers: Sequence[int], start: int, count: int, block_name: str
) -> _BlockReader:
    if len(registers) < count:
        raise SunSpecDecodeError(
            f"{block_name}: {count} Register erwartet, {len(registers)} erhalten."
        )
    return _BlockReader(registers, start)


@dataclass(frozen=True, slots=True)
class _BlockReader:
    """Übersetzt interne SunSpec-Adressen in Indizes des gelesenen Blocks."""

    registers: Sequence[int]
    start: int

    def __call__(self, address: int) -> int:
        return self.registers[address - self.start]


def decode_identity(low1: Sequence[int]) -> DecodedIdentity:
    """Decodiere das SunSpec Common Model aus dem LOW1-Teilblock.

    Gemeinsame Quelle für Coordinator (Sensoren) und Config Flow
    (Einrichtungs-Zusammenfassung, REQ-SETUP-FINISH-SUMMARY) - beide
    beschreiben dasselbe Gerät und dürfen sich nicht auseinanderentwickeln.
    """
    reg = _block_reader(
        low1, READ_BLOCK_EXT_LOW1_START, READ_BLOCK_EXT_LOW1_COUNT, "LOW1-Block"
    )

    # uint16 laut modbus_llm.yaml (REQ-SUNSPEC-DATATYPES) - decode_uint16
    # liefert None statt einer falschen Seriennummernhälfte, sobald das Gerät
    # hier den "not implemented"-Sentinel 0xFFFF meldet.
    serial_hi = decode_uint16(reg(REG_SUN_SERIAL_HI))
    serial_lo = decode_uint16(reg(REG_SUN_SERIAL_LO))

    return DecodedIdentity(
        manufacturer=decode_ascii_registers(
            [reg(REG_SUN_MANUFACTURER + i) for i in range(MANUFACTURER_REGISTER_COUNT)]
        ),
        model=decode_ascii_registers(
            [reg(REG_SUN_MODEL + i) for i in range(MODEL_REGISTER_COUNT)]
        ),
        version_master=decode_uint16(reg(REG_SUN_VERSION_MASTER)),
        version_gateway=decode_uint16(reg(REG_SUN_VERSION_GATEWAY)),
        serial_number=(
            (serial_hi << 16) | serial_lo
            if serial_hi is not None and serial_lo is not None
            else None
        ),
    )


def decode_battery_scale_factors(low2: Sequence[int]) -> BatteryScaleFactors:
    """Decodiere die vier Battery-Skalierungsfaktoren aus dem LOW2-Teilblock."""
    reg = _block_reader(
        low2, READ_BLOCK_EXT_LOW2_START, READ_BLOCK_EXT_LOW2_COUNT, "LOW2-Block"
    )
    return BatteryScaleFactors(
        capacity=reg(REG_SUN_BATTERY_CAPACITY_SF),
        power=reg(REG_SUN_BATTERY_POWER_SF),
        soc=reg(REG_SUN_BATTERY_SOC_SF),
        cell_voltage=reg(REG_SUN_BATTERY_CELL_VOLTAGE_SF),
    )


def decode_low_blocks(low1: Sequence[int], low2: Sequence[int]) -> DecodedLowBlock:
    """Decodiere beide LOW-Intervall-Teilblöcke (Identität + Battery-SF)."""
    return DecodedLowBlock(
        identity=decode_identity(low1),
        scale_factors=decode_battery_scale_factors(low2),
    )


def decode_high_block(
    high: Sequence[int], scale_factors: BatteryScaleFactors
) -> DecodedHighBlock:
    """Decodiere den HIGH-Intervall-Teilblock (dynamische Mess-/Zustandswerte).

    Deckt "3Ph Inverter" (103, Speicherelektronik), "Immediate Controls"
    (123), "WYE Connect 3Ph Meter" (203, Netz/Smart Meter) und "Battery Base"
    (802, Akkuzellen) ab.

    ``scale_factors`` kommt aus dem separaten LOW2-Teilblock: die vier
    Battery-Faktoren werden nur alle READ_BLOCK_EXT_LOW_INTERVAL Sekunden
    gelesen und liegen deshalb gar nicht in ``high`` (siehe
    anforderung.yaml, REQ-LOW-INTERVAL-REGISTERS). Der Aufrufer entscheidet,
    ob er dabei die zuletzt erfolgreich gelesenen oder die Vorgabewerte
    übergibt.
    """
    reg = _block_reader(high, READ_BLOCK_EXT_START, READ_BLOCK_EXT_COUNT, "HIGH-Block")
    values: dict[str, Any] = {}

    for field in HIGH_BLOCK_FIELDS:
        match field:
            case ScaledField():
                scale_factor_raw = (
                    reg(field.scale_factor_address)
                    if field.scale_factor_address is not None
                    else getattr(scale_factors, field.battery_scale_factor)
                )
                value = apply_typed_sunssf(
                    reg(field.address), scale_factor_raw, signed=field.signed
                )
                # None bleibt None statt am unären Minus zu crashen, sobald
                # das Register den "not implemented"-Sentinel meldet
                # (REQ-SUNSPEC-DATATYPES).
                values[field.key] = (
                    -value if field.negate and value is not None else value
                )
            case EnumField():
                raw = reg(field.address)
                decoded = decode_int16(raw) if field.signed else decode_uint16(raw)
                values[field.key] = decoded
                values[field.text_key] = field.labels.get(decoded, UNKNOWN_LABEL)
            case RawField():
                raw = reg(field.address)
                values[field.key] = (
                    decode_int16(raw) if field.signed else decode_uint16(raw)
                )
            case BoolField():
                values[field.key] = decode_bool16(reg(field.address))

    return DecodedHighBlock(
        values=values,
        ic_power_setpoint_sf_raw=reg(REG_SUN_IC_POWER_SETPOINT_SF),
    )
