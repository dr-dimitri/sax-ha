"""Pure helpers for encoding and decoding SAX/SunSpec register values."""

from __future__ import annotations


def to_signed16(value: int) -> int:
    """Convert an unsigned 16-bit register value to its signed representation."""
    return value - 0x10000 if value >= 0x8000 else value


def to_unsigned16(value: int) -> int:
    """Convert a signed value to its unsigned 16-bit register representation."""
    return value & 0xFFFF


def apply_sunssf(raw_value: int, raw_scale_factor: int) -> float:
    """Apply a signed SunSpec scale factor to a signed register value."""
    value = to_signed16(raw_value)
    scale_factor = to_signed16(raw_scale_factor)
    return round(value * (10**scale_factor), 3)


def decode_ascii_registers(registers: list[int]) -> str:
    """Decode SunSpec ``str`` registers containing two ASCII bytes each."""
    raw = bytearray()
    for register in registers:
        raw.append((register >> 8) & 0xFF)
        raw.append(register & 0xFF)
    return raw.decode("ascii", errors="replace").strip("\x00 ")
