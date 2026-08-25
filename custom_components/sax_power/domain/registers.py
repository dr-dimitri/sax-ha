"""Pure helpers for encoding and decoding SAX/SunSpec register values.

SunSpec-Datentypen und "not implemented"-Sentinelwerte laut SunSpec Device
Information Model Specification V1.1, Abschnitt 6.4 (siehe anforderung.yaml,
REQ-SUNSPEC-DATATYPES): signierte Typen (int16, sunssf) markieren einen nicht
implementierten Wert mit 0x8000, unsignierte Typen (uint16, enum16,
bitfield16) mit 0xFFFF. Ein Rohwert muss deshalb IMMER passend zu seinem in
modbus_llm.yaml dokumentierten Datentyp decodiert werden, bevor er
vorzeichenbehaftet interpretiert oder skaliert wird - eine pauschale
Signed-Konvertierung verwechselt sonst je nach Typ 0xFFFF mit -1 oder 0x8001
mit -32767.
"""

from __future__ import annotations

_INT16_NOT_IMPLEMENTED = 0x8000
_UINT16_NOT_IMPLEMENTED = 0xFFFF


def to_signed16(value: int) -> int:
    """Convert an unsigned 16-bit register value to its signed representation."""
    return value - 0x10000 if value >= 0x8000 else value


def to_unsigned16(value: int) -> int:
    """Convert a signed value to its unsigned 16-bit register representation."""
    return value & 0xFFFF


def decode_int16(raw_value: int) -> int | None:
    """Decode a SunSpec ``int16`` register, ``None`` on the "not implemented"
    sentinel (0x8000)."""
    if raw_value == _INT16_NOT_IMPLEMENTED:
        return None
    return to_signed16(raw_value)


def decode_uint16(raw_value: int) -> int | None:
    """Decode a SunSpec ``uint16``/``enum16``/``bitfield16`` register, ``None``
    on the "not implemented" sentinel (0xFFFF)."""
    if raw_value == _UINT16_NOT_IMPLEMENTED:
        return None
    return raw_value & 0xFFFF


def decode_sunssf(raw_scale_factor: int) -> int | None:
    """Decode a SunSpec scale-factor register (``sunssf``), encoded as
    ``int16``. ``None`` on the "not implemented" sentinel (0x8000)."""
    return decode_int16(raw_scale_factor)


def decode_bool16(raw_value: int) -> bool | None:
    """Decode a SunSpec boolean-style register (0/1 as ``uint16``). ``None``
    on the "not implemented" sentinel (0xFFFF) or any other value that isn't
    0 or 1, so an unrecognised raw value never silently reads as truthy."""
    decoded = decode_uint16(raw_value)
    if decoded is None or decoded not in (0, 1):
        return None
    return bool(decoded)


def apply_typed_sunssf(
    raw_value: int, raw_scale_factor: int, *, signed: bool = True
) -> float | None:
    """Decode a scaled SunSpec value together with its ``sunssf`` register.

    ``signed`` must match the value register's own declared type in
    modbus_llm.yaml (``int16`` -> True, ``uint16`` -> False) - the scale
    factor register itself is always ``sunssf``/``int16``. Returns ``None``
    if either register carries its type's "not implemented" sentinel, so a
    missing measurement never turns into a bogus 0 or an extreme value via
    an unintended power-of-ten underflow/overflow.
    """
    value = decode_int16(raw_value) if signed else decode_uint16(raw_value)
    scale_factor = decode_sunssf(raw_scale_factor)
    if value is None or scale_factor is None:
        return None
    return round(value * (10**scale_factor), 3)


def decode_ascii_registers(registers: list[int]) -> str:
    """Decode SunSpec ``str`` registers containing two ASCII bytes each."""
    raw = bytearray()
    for register in registers:
        raw.append((register >> 8) & 0xFF)
        raw.append(register & 0xFF)
    return raw.decode("ascii", errors="replace").strip("\x00 ")
