"""Read-only Live-Mitschnitt der Speicher-Leistungsregister (Diagnose).

Hintergrund: Die Energie- und Geldbilanz der Integration ist ein reines
Zeitintegral über data["storage_power_active"] (SunSpec-Register 40029).
Meldet dieses Register die tatsächliche Lade-/Entladeleistung nicht, bleibt
jede abgeleitete Zahl klein, ohne dass irgendein Plausibilitätsfehler
auffiele - genau dieser Fall wurde an einer echten Anlage beobachtet: Der
Speicher lieferte über Nacht rund 2,3 kWh ins Haus (Smart Meter am
Netzanschluss durchgehend bei 0 W), die Integration verbuchte davon
0,010 kWh.

Dieses Skript pollt deshalb die Rohwerte samt Skalierungsfaktoren direkt
vom Gerät und stellt sie dem Smart-Meter-Wert und dem SOC gegenüber. Es
SCHREIBT NICHTS - ausschließlich read_holding_registers.

    python scripts/dump_storage_power.py --host 192.168.1.50

Auswertung: Läuft der SOC sichtbar hoch oder runter (oder zeigt das Smart
Meter eine Leistung, die nur der Speicher liefern kann), während "W" bei
~0 klebt, meldet 40029 die Leistung nicht - dann ist die Bilanz nicht das
Problem, sondern ihre einzige Eingangsgröße.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

from pymodbus.client import AsyncModbusTcpClient

# Bewusst ohne Import aus custom_components: Das Skript soll auch dann
# laufen, wenn keine Home-Assistant-Umgebung installiert ist. Die Adressen
# stammen aus modbus_llm.yaml (SunSpec-Modus: protocol_addr - 40000).
SUN_CURRENT_SUM = 17
SUN_CURRENT_SF = 21
SUN_VOLTAGE_A = 25
SUN_VOLTAGE_SF = 28
SUN_POWER_ACTIVE = 29
SUN_POWER_ACTIVE_SF = 30
SUN_POWER_APPARENT = 33
SUN_POWER_APPARENT_SF = 34
SUN_BLOCK_START = SUN_CURRENT_SUM
SUN_BLOCK_COUNT = SUN_POWER_APPARENT_SF - SUN_CURRENT_SUM + 1

# Summenwirkleistung Netz (protocol 40072). Achtung: Das Rohregister ist
# positiv bei EINSPEISUNG - die Integration negiert es vor der Ablage in
# data["smartmeter_power"]. Dieses Skript zeigt bewusst den Rohwert und
# benennt ihn deshalb "Netz(roh)".
SUN_METER_POWER = 72
SUN_METER_POWER_SF = 76
SUN_METER_START = SUN_METER_POWER
SUN_METER_COUNT = SUN_METER_POWER_SF - SUN_METER_POWER + 1

SUN_BATTERY_SOC = 102
SUN_BATTERY_SOC_SF = 112
SUN_BATTERY_START = SUN_BATTERY_SOC
SUN_BATTERY_COUNT = SUN_BATTERY_SOC_SF - SUN_BATTERY_SOC + 1

# Basic Mode (protocol_addr - 40001): das laut modbus_llm.yaml als
# unzuverlässig verworfene Leistungsregister - hier bewusst zum Vergleich,
# um zu sehen, ob es die Entladung zeigt, wenn 40029 sie verschweigt.
BASIC_SOC = 46
BASIC_POWER = 47
BASIC_START = BASIC_SOC
BASIC_COUNT = BASIC_POWER - BASIC_SOC + 1


def signed16(value: int) -> int:
    return value - 65536 if value >= 32768 else value


def scaled(raw: int, sf_raw: int, *, signed: bool) -> float | None:
    """Rohwert × 10**sunssf, oder None bei einem Sentinel.

    0x8000 ist der SunSpec-Sentinel "nicht implementiert" - für den
    Skalierungsfaktor wie für einen signed-Messwert.
    """
    sf = signed16(sf_raw)
    if sf == -32768:
        return None
    value = signed16(raw) if signed else raw
    if signed and value == -32768:
        return None
    if not signed and raw == 0xFFFF:
        return None
    return value * 10**sf


async def read(client: AsyncModbusTcpClient, start: int, count: int, unit: int):
    result = await client.read_holding_registers(
        address=start, count=count, device_id=unit
    )
    if result.isError():
        raise RuntimeError(f"Modbus-Fehler bei {start}+{count} (Unit {unit}): {result}")
    return result.registers


async def poll_once(client: AsyncModbusTcpClient, sun_id: int, basic_id: int) -> str:
    block = await read(client, SUN_BLOCK_START, SUN_BLOCK_COUNT, sun_id)
    meter = await read(client, SUN_METER_START, SUN_METER_COUNT, sun_id)
    battery = await read(client, SUN_BATTERY_START, SUN_BATTERY_COUNT, sun_id)
    basic = await read(client, BASIC_START, BASIC_COUNT, basic_id)

    def sun(address: int) -> int:
        return block[address - SUN_BLOCK_START]

    w_raw = sun(SUN_POWER_ACTIVE)
    w_sf = sun(SUN_POWER_ACTIVE_SF)
    va_raw = sun(SUN_POWER_APPARENT)
    va_sf = sun(SUN_POWER_APPARENT_SF)
    a_raw = sun(SUN_CURRENT_SUM)
    a_sf = sun(SUN_CURRENT_SF)
    v_raw = sun(SUN_VOLTAGE_A)
    v_sf = sun(SUN_VOLTAGE_SF)

    watts = scaled(w_raw, w_sf, signed=True)
    va = scaled(va_raw, va_sf, signed=False)
    amps = scaled(a_raw, a_sf, signed=False)
    volts = scaled(v_raw, v_sf, signed=False)
    meter_w = scaled(meter[0], meter[-1], signed=True)
    soc = scaled(battery[0], battery[-1], signed=False)

    # Aus Strom und Spannung gerechnet: Ist der Speicher wirklich im
    # Leerlauf, muss diese Scheinleistung ebenfalls klein sein. Weicht sie
    # deutlich von W/VA ab, widersprechen sich die Register des Geräts.
    implied = None if amps is None or volts is None else amps * volts

    return (
        f"{datetime.now(UTC).strftime('%H:%M:%S')} "
        f"W={_fmt(watts):>9} (roh {signed16(w_raw):>6}, sf {signed16(w_sf):>3})  "
        f"VA={_fmt(va):>9} (roh {va_raw:>6}, sf {signed16(va_sf):>3})  "
        f"A={_fmt(amps):>7}  V={_fmt(volts):>7}  A*V={_fmt(implied):>9}  "
        f"Netz(roh)={_fmt(meter_w):>9}  SOC={_fmt(soc):>5}  "
        f"Basic[47]={basic[BASIC_POWER - BASIC_START]:>6} "
        f"Basic-SOC={basic[BASIC_SOC - BASIC_START]:>3}"
    )


def _fmt(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--slave-extended", type=int, default=100)
    parser.add_argument("--slave-basic", type=int, default=64)
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument(
        "--count", type=int, default=0, help="Anzahl Messungen; 0 = endlos"
    )
    args = parser.parse_args()

    client = AsyncModbusTcpClient(host=args.host, port=args.port)
    if not await client.connect():
        raise SystemExit(f"Verbindung zu {args.host}:{args.port} fehlgeschlagen")
    try:
        taken = 0
        while args.count == 0 or taken < args.count:
            print(await poll_once(client, args.slave_extended, args.slave_basic))
            taken += 1
            if args.count == 0 or taken < args.count:
                await asyncio.sleep(args.interval)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
