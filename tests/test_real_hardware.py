"""Live-Hardware-Test: liest echte Werte direkt von einem physischen
SAX Power Home (Plus) im lokalen Netz.

Anders als test_integration_live.py (echtes Wire-Protokoll, aber ein
simulierter Modbus-Server via pymodbus.server.ModbusTcpServer) verbindet
sich dieser Test mit einem *echten* Gerät. Die Ziel-IP wird aus
tests/real_device.yaml gelesen (siehe dort für Hintergrund und wie man sie
einträgt), damit sie für dieses Repository persistiert ist, ohne die
Integration selbst mit einer festen IP zu koppeln.

Rein lesend, kein Schreibzugriff auf ein reales, ggf. produktives
Speichersystem. Überspringt sich automatisch (pytest.skip), wenn keine IP
hinterlegt oder der Speicher gerade nicht erreichbar ist - läuft also weder
in CI noch auf Entwicklerrechnern ohne physischen Zugriff auf die Hardware.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import pytest_socket
import yaml
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.const import (
    READ_BLOCK_COUNT,
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_START,
    READ_BLOCK_START,
    REG_SOC,
    REG_SUN_STORAGE_FREQUENCY,
    REG_SUN_STORAGE_FREQUENCY_SF,
    REG_SUN_STORAGE_POWER_ACTIVE,
    REG_SUN_STORAGE_POWER_ACTIVE_SF,
)
from custom_components.sax_power.coordinator import apply_sunssf

REAL_DEVICE_CONFIG_PATH = Path(__file__).parent / "real_device.yaml"

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _load_real_device_config() -> dict[str, Any]:
    if not REAL_DEVICE_CONFIG_PATH.exists():
        return {}
    with REAL_DEVICE_CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@pytest.fixture
async def real_client():
    """Verbindung zu einem echten SAX Speicher, oder Skip.

    pytest-homeassistant-custom-component sperrt Socket-Erstellung und
    Netzwerkzugriffe standardmäßig komplett (bis auf `127.0.0.1`), siehe
    deren `pytest_runtest_setup`. Die `socket_enabled`-Fixture aus
    pytest-socket reicht dafür NICHT aus, da deren `enable_socket()` zwar
    die Socket-Erstellung freigibt, aber `socket_allow_hosts()` danach
    trotzdem wieder greift. Stattdessen wird hier explizit zuerst
    `enable_socket()` (hebt die komplette Sperre auf) und anschließend
    `socket_allow_hosts()` mit genau der Ziel-IP aufgerufen (schränkt
    wieder gezielt auf diese IP + `127.0.0.1` ein, statt Sockets pauschal
    komplett offen zu lassen).
    """
    config = _load_real_device_config()
    host = config.get("host")
    if not host:
        pytest.skip(
            "Keine echte SAX-IP in tests/real_device.yaml hinterlegt - "
            "Live-Hardware-Test wird übersprungen (siehe Kommentar dort)."
        )

    pytest_socket.enable_socket()
    pytest_socket.socket_allow_hosts([host, "127.0.0.1"], allow_unix_socket=True)

    port = config.get("port", 502)
    timeout = config.get("connect_timeout", 3)
    client = AsyncModbusTcpClient(host=host, port=port, timeout=timeout)
    try:
        connected = await client.connect()
    except (ModbusException, OSError):
        connected = False
    if not connected:
        pytest.skip(f"SAX Speicher unter {host}:{port} nicht erreichbar.")

    try:
        yield client, config
    finally:
        client.close()


async def test_read_real_basic_mode_values(real_client) -> None:
    """Liest den echten Basic-Mode-Block (SOC, Schaltzustand, Grenzwerte)
    von der realen Hardware und prüft plausible Wertebereiche.

    Anders als beim simulierten Server (test_integration_live.py) sind die
    tatsächlichen Werte zur Testzeit unbekannt, deshalb wird auf plausible
    Bandbreiten geprüft statt auf feste erwartete Werte.
    """
    client, config = real_client
    slave_id_basic = config.get("slave_id_basic", 64)

    result = await client.read_holding_registers(
        address=READ_BLOCK_START, count=READ_BLOCK_COUNT, device_id=slave_id_basic
    )
    assert not result.isError(), f"Modbus-Fehlerantwort (Basic Mode): {result}"
    assert len(result.registers) == READ_BLOCK_COUNT

    def basic_reg(address: int) -> int:
        return result.registers[address - READ_BLOCK_START]

    soc = basic_reg(REG_SOC)
    assert 0 <= soc <= 100, f"SOC außerhalb des gültigen Bereichs (0-100 %): {soc}"

    print(f"\n[Live-Hardware] SOC={soc}%")


async def test_read_real_sunspec_mode_values(real_client) -> None:
    """Liest den echten SunSpec-Modus-Block (Slave-ID 100, siehe modbus.pdf)
    und prüft plausible Wertebereiche, inkl. der echten Speicherleistung
    (ersetzt das zuvor unzuverlässige Basic-Mode-Register 47, siehe
    anforderung.yaml REQ-SUNSPEC-MODE-CORRECTION).

    Überspringt statt fehlzuschlagen, wenn der SunSpec-Modus auf diesem
    Gerät nicht erreichbar ist (ältere Firmware, siehe modbus.pdf
    "Verfügbarkeit") - sowohl bei einer Modbus-Fehlerantwort (`isError()`)
    als auch bei einer pymodbus-Exception, dasselbe Verhalten wie im
    produktiven Coordinator (`_async_read_extended`)."""
    client, config = real_client
    slave_id_extended = config.get("slave_id_extended", 100)

    try:
        result = await client.read_holding_registers(
            address=READ_BLOCK_EXT_START,
            count=READ_BLOCK_EXT_COUNT,
            device_id=slave_id_extended,
        )
    except ModbusException as err:
        pytest.skip(
            f"SunSpec-Modus (Slave-ID {slave_id_extended}) auf diesem "
            f"Speicher nicht erreichbar: {err}"
        )
    if result.isError():
        pytest.skip(
            f"SunSpec-Modus (Slave-ID {slave_id_extended}) auf diesem "
            "Speicher nicht erreichbar."
        )
    assert len(result.registers) == READ_BLOCK_EXT_COUNT

    def ext_reg(address: int) -> int:
        return result.registers[address - READ_BLOCK_EXT_START]

    frequency = apply_sunssf(
        ext_reg(REG_SUN_STORAGE_FREQUENCY), ext_reg(REG_SUN_STORAGE_FREQUENCY_SF)
    )
    assert 40.0 <= frequency <= 65.0, f"Netzfrequenz unplausibel: {frequency} Hz"

    storage_power = apply_sunssf(
        ext_reg(REG_SUN_STORAGE_POWER_ACTIVE), ext_reg(REG_SUN_STORAGE_POWER_ACTIVE_SF)
    )
    # Grobe Plausibilitätsprüfung: kein Heimspeicher bewegt mehrere hundert
    # Kilowatt. Fängt genau die Art von Regressionsfehler ab (Adressierung/
    # Offset falsch), die diesen Fix ursprünglich nötig gemacht hat.
    assert (
        -100_000 <= storage_power <= 100_000
    ), f"Speicherleistung unplausibel: {storage_power} W"

    print(f"\n[Live-Hardware] Netzfrequenz={frequency}Hz")
    print(f"[Live-Hardware] Speicherleistung={storage_power}W")
