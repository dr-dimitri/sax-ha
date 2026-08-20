"""Tests for the SAX Power coordinator."""

from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components import persistent_notification

from custom_components.sax_power.const import (
    ALL_MONTHS,
    GRID_CHARGE_WRITE_INTERVAL,
    MAX_SOC,
    READ_BLOCK_COUNT,
    READ_BLOCK_START,
    REG_SOC,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
    SUN_IC_MIN_WRITE_INTERVAL,
    IntervalType,
)
from custom_components.sax_power.coordinator import (
    SaxPowerCoordinator,
    apply_sunssf,
    to_signed16,
    to_unsigned16,
    windows_overlap,
)
from custom_components.sax_power.intervals import (
    SLOW_DATA_KEYS,
    TASK_INTERVALS,
    TASK_READ_BASIC,
    TASK_READ_EXTENDED,
    TASK_READ_SLOW_DATA,
    TASK_WRITE_GRID_CHARGE,
    TASK_WRITE_SUN_CHARGE,
)

# _make_coordinator (unten) legt den Coordinator immer mit scan_interval=10
# an - das NORMAL-Intervall (siehe const.IntervalType) entspricht in allen
# Tests unten also diesem Wert.
DEFAULT_NORMAL_INTERVAL = 10


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(0, 0), (100, 100), (32767, 32767), (32768, -32768), (65535, -1)],
)
def test_to_signed16(raw: int, expected: int) -> None:
    assert to_signed16(raw) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, 0), (100, 100), (-1, 65535), (-32768, 32768)],
)
def test_to_unsigned16(value: int, expected: int) -> None:
    assert to_unsigned16(value) == expected


@pytest.mark.parametrize(
    ("raw_value", "raw_sf", "expected"),
    [
        (1200, 0, 1200),  # sf=0 -> unverändert
        (551, to_unsigned16(-1), 55.1),  # sf=-1 -> Kommastelle
        (5, 2, 500),  # sf=2 -> Zehnerpotenz
        (to_unsigned16(-300), to_unsigned16(-2), -3.0),  # negativ + negativer sf
    ],
)
def test_apply_sunssf(raw_value: int, raw_sf: int, expected: float) -> None:
    assert apply_sunssf(raw_value, raw_sf) == expected


def _make_client() -> MagicMock:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    return client


def _make_coordinator(hass, client: MagicMock) -> SaxPowerCoordinator:
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
    )
    # Entspricht dem Vorgabewert, den SaxPowerTimedChargeMinSocNumber beim
    # allerersten Start setzt (siehe number.py) - ohne diesen Default würde
    # jeder Test, der zeitgesteuertes Laden auslösen will, zusätzlich
    # async_set_timed_charge_min_soc aufrufen müssen, obwohl ein echter
    # Coordinator diesen Wert längst über die Number-Entity gesetzt hätte.
    coordinator._timed_charge_min_soc = MAX_SOC
    return coordinator


async def test_async_write_register_raises_on_modbus_error(hass) -> None:
    from homeassistant.exceptions import HomeAssistantError

    client = _make_client()
    error_result = MagicMock()
    error_result.isError.return_value = True
    client.write_register = AsyncMock(return_value=error_result)

    coordinator = _make_coordinator(hass, client)

    with pytest.raises(HomeAssistantError):
        await coordinator.async_write_register(41, 1000)


def _make_read_side_effect(basic_registers: list[int], *, extended_error: bool):
    """Simuliert unterschiedliche read_holding_registers-Antworten je nach
    device_id, wie sie der Coordinator für Basic-Mode- (Slave 64) bzw.
    SunSpec-Modus-Reads (Slave 100) verwendet."""

    def _side_effect(*, address: int, count: int, device_id: int):
        result = MagicMock()
        if device_id != 100:
            result.isError.return_value = False
            result.registers = basic_registers
        else:
            result.isError.return_value = extended_error
            result.registers = [] if extended_error else [0] * count
        return result

    return _side_effect


async def test_update_data_degrades_gracefully_when_extended_unavailable(hass) -> None:
    """Ein nicht erreichbarer SunSpec-Modus-Block darf nicht die Basic-Mode-
    Sensoren mit ausfallen lassen (siehe anforderung.yaml,
    REQ-EXTENDED-MODE-RESILIENCE) - vorher führte das zu ConfigEntryNotReady
    und damit zu gar keinen Entities in Home Assistant."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    basic_registers[REG_SOC - READ_BLOCK_START] = 55
    client.read_holding_registers = AsyncMock(
        side_effect=_make_read_side_effect(basic_registers, extended_error=True)
    )

    coordinator = _make_coordinator(hass, client)
    data = await coordinator._async_update_data()

    assert data["soc"] == 55
    assert "storage_power_active" not in data
    assert coordinator._extended_available is False


async def test_update_data_recovers_when_extended_becomes_available(hass) -> None:
    """Nach einem vorherigen SunSpec-Modus-Ausfall müssen die SunSpec-
    Sensoren wieder befüllt werden, sobald der Block wieder lesbar ist."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    basic_registers[REG_SOC - READ_BLOCK_START] = 55
    client.read_holding_registers = AsyncMock(
        side_effect=_make_read_side_effect(basic_registers, extended_error=False)
    )

    coordinator = _make_coordinator(hass, client)
    coordinator._extended_available = False
    data = await coordinator._async_update_data()

    assert data["storage_power_active"] == 0
    assert coordinator._extended_available is True


def test_parse_extended_decodes_sunspec_block(hass) -> None:
    """Parst den kompletten SunSpec-Modus-Block (Slave-ID 100, siehe
    modbus.pdf) - Common, 3Ph Inverter (103), Immediate Controls (123),
    Meter (203) und Battery (802). Siehe anforderung.yaml,
    REQ-SUNSPEC-MODE-CORRECTION."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)

    # Alle 115 Register (Adresse 0-114) auf 0 vorbelegen, damit fehlende
    # Overrides unten nicht zu KeyError führen, und dann die für den Test
    # relevanten Werte überschreiben. sf-Register = 0 (Faktor 1), damit
    # skalierte Werte den Rohwerten entsprechen.
    raw = dict.fromkeys(range(115), 0)
    raw.update(
        {
            0: 21365,  # SunS (Hi)
            1: 28243,  # SunS (Lo)
            4: 21313,  # Hersteller "SA"
            5: 22608,  # "XP"
            6: 20311,  # "OW"
            7: 17746,  # "ER" -> "SAXPOWER"
            8: 18511,  # Gerätemodell "HO"
            9: 19781,  # "ME"
            10: to_unsigned16(0),  # kein "PL"-Suffix -> "SAX Power Home"
            11: 23,  # Version Master
            12: 56,  # Version Gateway
            13: 15448,  # Seriennummer Hi
            14: 97,  # Seriennummer Lo
            17: 30,  # Speicher Stromsumme
            18: 5,
            19: 6,
            20: 7,
            25: 230,  # Speicher Spannung A
            26: 231,
            27: 229,
            29: 1500,  # Wirkleistung Speicher Summe -> storage_power_active
            33: 1600,  # Scheinleistung
            35: 100,  # Blindleistung
            37: 95,  # Leistungsfaktor
            41: 35,  # Maximale Zelltemperatur
            43: 4,  # Zustand: Ein
            44: 0,  # Event: Normalbetrieb
            46: 1,  # Scalefaktor PV-Leistung (PV-Leistung selbst bleibt 0)
            49: 0,  # Leistungsvorgabe %
            50: 300,  # Timeout
            51: 1,  # Steuermodus: Sollwertvorgabe
            52: to_unsigned16(-2),  # Scalefaktor Leistungsvorgabe
            53: 4600,  # Referenzwert Maximalleistung
            56: 20,  # Netz Stromsumme
            57: 6,
            58: 7,
            59: 7,
            62: 231,  # Netzspannung L1
            63: 232,
            64: 233,
            72: 250,  # Summenwirkleistung Netz -> smartmeter_power
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

    def ext_reg(address: int) -> int:
        return raw[address]

    data = coordinator._parse_extended(ext_reg)

    assert data["sun_manufacturer"] == "SAXPOWER"
    assert data["sun_model"] == "HOME"
    assert data["sun_version_master"] == 23
    assert data["sun_serial_number"] == (15448 << 16) | 97

    assert data["storage_current_sum"] == 30
    assert data["storage_current_a"] == 5
    assert data["storage_power_active"] == 1500
    assert data["storage_state_text"] == "Ein"
    assert data["storage_event_text"] == "Normalbetrieb"

    assert data["ic_control_mode_text"] == "Sollwertvorgabe"
    assert data["ic_max_power_reference"] == 4600

    assert data["grid_current_sum"] == 20
    assert data["smartmeter_power"] == 250

    assert data["battery_capacity"] == 7680
    assert data["battery_soc"] == 55
    assert data["battery_discharge_power_available"] == 4600
    assert data["battery_charging_active"] is True
    assert data["battery_event_text"] == "Normalbetrieb"
    assert data["battery_cell_voltage_avg"] == 3300


# -- Zeitgesteuertes Laden ---------------------------------------------------


@pytest.mark.parametrize(
    ("start", "end", "now", "expected"),
    [
        (dt_time(1, 0), dt_time(5, 0), dt_time(3, 0), True),  # innerhalb
        (dt_time(1, 0), dt_time(5, 0), dt_time(0, 30), False),  # davor
        (dt_time(1, 0), dt_time(5, 0), dt_time(5, 0), False),  # Ende exklusiv
        (dt_time(1, 0), dt_time(5, 0), dt_time(1, 0), True),  # Start inklusiv
        (
            dt_time(23, 0),
            dt_time(5, 0),
            dt_time(23, 30),
            True,
        ),  # über Mitternacht, abends
        (
            dt_time(23, 0),
            dt_time(5, 0),
            dt_time(1, 0),
            True,
        ),  # über Mitternacht, morgens
        (
            dt_time(23, 0),
            dt_time(5, 0),
            dt_time(12, 0),
            False,
        ),  # über Mitternacht, tagsüber
    ],
)
def test_is_time_in_window(
    hass, start: dt_time, end: dt_time, now: dt_time, expected: bool
) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    assert coordinator._is_time_in_window(now, start, end) is expected


def test_is_time_in_window_unset_is_never_active(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    assert coordinator._is_time_in_window(dt_time(3, 0), None, None) is False


def _patched_now(hour: int, minute: int = 0, *, month: int = 1):
    """Patcht dt_util.now() auf einen festen Zeitpunkt.

    Bewusst statt der `freezer`-Fixture (freezegun): freezegun friert auch
    die vom Event-Loop für `asyncio.sleep` genutzte Uhr ein, wodurch der in
    async_start_grid_charge gespawnte Hintergrund-Task nie mehr aufwacht und
    der Test hängt. Ein gezielter Patch nur von dt_util.now() betrifft
    ausschließlich unsere eigene Zeitfenster-Prüfung.
    """
    return patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, month, 1, hour, minute),
    )


async def test_enforce_grid_charge_starts_timed_charge_when_enabled_in_window(
    hass,
) -> None:
    """Zeitgesteuertes Laden schreibt über den SunSpec-Modus (Slave-ID 100):
    erst Register 40051 (Steuermodus) auf Sollwertvorgabe, dann Register
    40049 (Leistungsvorgabe %) - siehe anforderung.yaml,
    REQ-TIMED-SOC-CHARGE."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    # ic_max_power_reference/ic_timeout werden vom Hintergrund-Task
    # (_async_sun_charge_loop) aus coordinator.data gelesen, nicht aus dem
    # unten übergebenen data-Dict - siehe SaxPowerCoordinator._sun_ic_write_interval.
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)  # Ziel-SOC = "Max. SOC"
    await coordinator.async_set_max_charge_power(3000)  # "Max. Netzladeleistung"

    try:
        with _patched_now(2):
            await coordinator.async_set_timed_charge_enabled(True)
        # async_start_sun_charge spawnt nur den Hintergrund-Task; der erste
        # Schreibvorgang läuft asynchron, daher kurz dem Event-Loop Zeit geben.
        await asyncio.sleep(0.1)

        assert coordinator._timed_charge_active is True
        assert coordinator.sun_charge_active is True
        client.write_register.assert_any_await(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        )
        # -3000 W / 4600 W Referenz-Maximalleistung * 100 = -65.217...%,
        # skaliert mit sunssf -2 (Default-Annahme, siehe
        # SaxPowerCoordinator._watts_to_ic_setpoint_raw) -> -6522.
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=to_unsigned16(-6522),
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()

    # Beim Stoppen wird der Steuermodus aktiv auf SmartMeter-Nullregelung
    # zurückgesetzt, statt nur passiv auf den Timeout zu warten.
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_enforce_grid_charge_inactive_outside_window(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)  # Ziel-SOC = "Max. SOC"
    await coordinator.async_set_max_charge_power(3000)
    await coordinator.async_set_timed_charge_enabled(True)

    with _patched_now(12):
        await coordinator._async_enforce_grid_charge({"soc": 10})

    assert coordinator._timed_charge_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_grid_charge_inactive_when_disabled(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)  # Ziel-SOC = "Max. SOC"
    await coordinator.async_set_max_charge_power(3000)
    # timed_charge_enabled bleibt False (Default)

    with _patched_now(2):
        await coordinator._async_enforce_grid_charge({"soc": 10})

    assert coordinator._timed_charge_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_grid_charge_inactive_without_max_charge_power(hass) -> None:
    """Ohne gesetzte "Max. Netzladeleistung" darf zeitgesteuertes Laden nicht
    starten (kein sinnvoller Sollwert berechenbar)."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_timed_charge_enabled(True)
    # max_charge_power bleibt None (Default)

    with _patched_now(2):
        await coordinator._async_enforce_grid_charge({"soc": 10})

    assert coordinator._timed_charge_active is False


async def test_enforce_grid_charge_inactive_without_min_soc(hass) -> None:
    """Ohne gesetztes "Netzladung Min. SOC" darf zeitgesteuertes Laden nicht
    starten - siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator._timed_charge_min_soc = None  # explizit ungesetzt
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    await coordinator.async_set_timed_charge_enabled(True)

    with _patched_now(2):
        await coordinator._async_enforce_grid_charge({"soc": 10})

    assert coordinator._timed_charge_active is False


async def test_enforce_grid_charge_inactive_when_soc_at_or_above_min_soc(hass) -> None:
    """Solange der SOC "Netzladung Min. SOC" nicht unterschritten hat, darf
    zeitgesteuertes Laden nicht starten, auch wenn alle anderen Bedingungen
    erfüllt sind."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    await coordinator.async_set_timed_charge_min_soc(40)
    await coordinator.async_set_timed_charge_enabled(True)

    with _patched_now(2):
        await coordinator._async_enforce_grid_charge({"soc": 40})  # == min_soc

    assert coordinator._timed_charge_active is False


async def test_enforce_grid_charge_starts_when_soc_below_min_soc(hass) -> None:
    """Unterschreitet der SOC "Netzladung Min. SOC", startet zeitgesteuertes
    Laden (bei erfüllten übrigen Bedingungen)."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 39,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    await coordinator.async_set_timed_charge_min_soc(40)

    try:
        with _patched_now(2):
            await coordinator.async_set_timed_charge_enabled(True)
        await asyncio.sleep(0.1)

        assert coordinator._timed_charge_active is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_timed_charge_min_soc_hysteresis_continues_until_max_soc(hass) -> None:
    """Regressionstest für die geforderte Hysterese: Einmal unterhalb
    "Netzladung Min. SOC" gestartet, lädt die Netzladung bis "Max. SOC"
    durch - auch wenn der SOC dabei zwischenzeitlich wieder über "Netzladung
    Min. SOC" (aber unterhalb "Max. SOC") steigt -, statt bei jedem erneuten
    Überschreiten von "Netzladung Min. SOC" sofort abzubrechen."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 39,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    await coordinator.async_set_timed_charge_min_soc(40)

    try:
        with _patched_now(2):
            # SOC unterschreitet 40 % -> startet und armt die Hysterese.
            await coordinator.async_set_timed_charge_enabled(True)
            await asyncio.sleep(0.1)
            assert coordinator._timed_charge_active is True

            # SOC steigt wieder über 40 %, ist aber noch unter "Max. SOC"
            # (90 %) -> lädt dank Hysterese unverändert weiter.
            coordinator.data["soc"] = 60
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._timed_charge_active is True

            # SOC erreicht "Max. SOC" -> Ladung endet, Hysterese wird
            # zurückgesetzt.
            coordinator.data["soc"] = 90
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._timed_charge_active is False

            # SOC fällt wieder unter "Max. SOC", bleibt aber über
            # "Netzladung Min. SOC" -> kein Neustart, bis der SOC erneut
            # unter 40 % fällt.
            coordinator.data["soc"] = 60
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._timed_charge_active is False
    finally:
        await coordinator.async_stop_sun_charge()
    assert coordinator.sun_charge_active is False


# -- Max-SOC-Sperre (unabhängig vom zeitgesteuerten Laden) -------------------


async def test_enforce_grid_charge_clamps_at_max_soc_even_without_timed_charge(
    hass,
) -> None:
    """Die Max-SOC-Sperre greift auch ohne aktiviertes zeitgesteuertes Laden
    (z. B. bei einem durch PV-Überschuss vollen Speicher): Register 40051
    wird auf Sollwertvorgabe gesetzt, Register 40049 auf 0 % gehalten -
    siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_max_soc(80)
    # timed_charge_enabled bleibt False (Default)

    try:
        await coordinator._async_enforce_grid_charge({"soc": 85})
        await asyncio.sleep(0.1)

        assert coordinator.max_soc_clamped is True
        assert coordinator.sun_charge_active is True
        assert coordinator._timed_charge_active is False
        client.write_register.assert_any_await(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        )
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=0,
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_releases_max_soc_clamp_below_target(hass) -> None:
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_max_soc(80)
    coordinator._max_soc_clamped = True
    # Echter (cancelbarer) Task statt MagicMock, da async_stop_sun_charge die
    # Cancellation awaitet, bevor es den Steuermodus zurücksetzt.
    coordinator._sun_charge_task = asyncio.create_task(asyncio.sleep(3600))

    await coordinator._async_enforce_grid_charge({"soc": 70})

    assert coordinator.max_soc_clamped is False
    assert coordinator.sun_charge_active is False
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_enforce_grid_charge_max_soc_clamp_stays_within_charge_window(
    hass,
) -> None:
    """Wird der Ziel-SOC INNERHALB des Netzladung-Zeitfensters erreicht,
    bleibt Register 40051 (Steuermodus) auf Sollwertvorgabe und Register
    40049 auf 0 % gehalten - die Sperre ist an dieses Zeitfenster gebunden
    (_max_soc_hold_is_window_bound), siehe
    test_enforce_grid_charge_max_soc_clamp_releases_after_charge_window_ends
    für die Freigabe am Fensterende."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 90, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    await coordinator.async_set_timed_charge_enabled(True)

    try:
        with _patched_now(2):
            await coordinator._async_enforce_grid_charge({"soc": 90})
        await asyncio.sleep(0.1)

        assert coordinator.max_soc_clamped is True
        assert coordinator.sun_charge_active is True
        assert coordinator._max_soc_hold_is_window_bound is True
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=0,
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_max_soc_clamp_releases_after_charge_window_ends(
    hass,
) -> None:
    """Wurde die Max-SOC-Sperre WÄHREND des Netzladung-Zeitfensters
    ausgelöst, muss sie spätestens am Fensterende aktiv aufgehoben werden
    (Register 40051 zurück auf SmartMeter-Nullregelung), statt unbegrenzt
    im Sollwertmodus zu bleiben - auch wenn der SOC weiterhin >= Max. SOC
    ist (was bei gehaltenem 0-%-Sollwert nie von selbst der Fall wäre)."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 90, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    await coordinator.async_set_timed_charge_enabled(True)

    try:
        with _patched_now(2):
            await coordinator._async_enforce_grid_charge({"soc": 90})
        await asyncio.sleep(0.1)
        assert coordinator._max_soc_hold_is_window_bound is True

        with _patched_now(6):  # nach Fensterende (Netzladung Ende = 5:00)
            await coordinator._async_enforce_grid_charge({"soc": 90})
        await asyncio.sleep(0.1)

        assert coordinator.max_soc_clamped is False
        assert coordinator.sun_charge_active is False
        assert coordinator._max_soc_hold_is_window_bound is False
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()


# -- PV-Überschuss-Prüfung (zusätzlich zum Zeitfenster) ----------------------


async def test_enforce_grid_charge_does_not_start_with_pv_surplus_above_threshold(
    hass,
) -> None:
    """Auch innerhalb des Zeitfensters darf zeitgesteuertes Laden nicht
    starten, sobald am Smart Meter mehr PV-Überschuss als
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT gemessen wird (positiver
    Anzeigewert = Überschuss aus der Dachphotovoltaik) - siehe
    anforderung.yaml, REQ-TIMED-SOC-CHARGE."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.data = {
        "soc": 10,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50,
    }
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    with _patched_now(2):
        await coordinator.async_set_timed_charge_enabled(True)
        await asyncio.sleep(0.1)

    assert coordinator._timed_charge_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_grid_charge_stops_when_pv_surplus_exceeds_threshold_mid_window(
    hass,
) -> None:
    """Eine bereits laufende Netzladung wird beendet, sobald der PV-
    Überschuss während des Zeitfensters über den Schwellwert steigt - beim
    nächsten Poll-Zyklus, nicht erst am konfigurierten Fensterende."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": 0,
    }
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    try:
        with _patched_now(2):
            await coordinator.async_set_timed_charge_enabled(True)
            await asyncio.sleep(0.1)
            assert coordinator.sun_charge_active is True

            # Simuliert den nächsten Poll-Zyklus (_async_update_data), bei
            # dem der Smart Meter nun PV-Überschuss über dem Schwellwert
            # meldet.
            coordinator.data["smartmeter_power"] = (
                SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50
            )
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)

            assert coordinator._timed_charge_active is False
            assert coordinator.sun_charge_active is False
            client.write_register.assert_awaited_with(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SMARTMETER,
                device_id=100,
            )
    finally:
        await coordinator.async_stop_sun_charge()


@pytest.mark.parametrize(
    "smartmeter_power",
    [
        SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,  # genau auf dem Schwellwert (nicht >)
        0,
        -500,  # Netzbezug statt PV-Überschuss
    ],
)
async def test_enforce_grid_charge_starts_at_or_below_pv_surplus_threshold(
    hass, smartmeter_power: float
) -> None:
    """Der Schwellwert greift erst bei Überschreitung (>) - ein Wert genau
    auf dem Schwellwert sowie Netzbezug (negativer Anzeigewert) blockieren
    das zeitgesteuerte Laden nicht."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": smartmeter_power,
    }
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    try:
        with _patched_now(2):
            await coordinator.async_set_timed_charge_enabled(True)
            await asyncio.sleep(0.1)

            assert coordinator._timed_charge_active is True
            assert coordinator.sun_charge_active is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_starts_when_smartmeter_power_missing(hass) -> None:
    """Fehlt der Smart-Meter-Wert (z. B. weil der SunSpec-Modus gerade nicht
    erreichbar ist), darf das zeitgesteuerte Laden dadurch nicht blockiert
    werden."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    try:
        with _patched_now(2):
            await coordinator.async_set_timed_charge_enabled(True)
            await asyncio.sleep(0.1)

            assert coordinator._timed_charge_active is True
            assert coordinator.sun_charge_active is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_stop_sun_charge_is_noop_when_not_running(hass) -> None:
    """Analog zu async_stop_grid_charge: ein Aufruf ohne laufende Ladung
    (z. B. beim Entladen des Config Entry) darf nicht ungefragt in Register
    40051 eingreifen."""
    client = _make_client()
    client.write_register = AsyncMock()
    coordinator = _make_coordinator(hass, client)

    await coordinator.async_stop_sun_charge()

    client.write_register.assert_not_awaited()


# -- SunSpec-Modus-Netzladung: Watt/Prozent-Konvertierung & Schreibintervall -


@pytest.mark.parametrize(
    ("power_watts", "max_power_reference", "expected_raw"),
    [
        (-3000, 4600, to_unsigned16(-6522)),  # Laden, ~-65.22%
        (4600, 4600, 10000),  # Entladen mit voller Referenzleistung -> +100%
        (
            -9200,
            4600,
            to_unsigned16(-10000),
        ),  # jenseits Referenzleistung -> -100% geklemmt
    ],
)
def test_watts_to_ic_setpoint_raw(
    hass, power_watts: int, max_power_reference: int, expected_raw: int
) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    coordinator._ic_power_setpoint_sf_raw = to_unsigned16(-2)  # wellknown
    data = {"ic_max_power_reference": max_power_reference}
    assert coordinator._watts_to_ic_setpoint_raw(power_watts, data) == expected_raw


def test_watts_to_ic_setpoint_raw_raises_without_max_power_reference(hass) -> None:
    from homeassistant.exceptions import HomeAssistantError

    coordinator = _make_coordinator(hass, _make_client())

    with pytest.raises(HomeAssistantError):
        coordinator._watts_to_ic_setpoint_raw(-3000, {})


@pytest.mark.parametrize(
    ("ic_timeout", "expected_interval"),
    [
        # Kein Timeout bekannt -> Fallback auf das über TASK_WRITE_SUN_CHARGE
        # aufgelöste Intervall (NORMAL/scan_interval=10, siehe
        # DEFAULT_NORMAL_INTERVAL), NICHT mehr auf GRID_CHARGE_WRITE_INTERVAL
        # (30) direkt.
        (None, DEFAULT_NORMAL_INTERVAL),
        # Geräte-Default (modbus.pdf, 300s) -> weiterhin auf denselben
        # Basiswert gedeckelt (hier kleiner als GRID_CHARGE_WRITE_INTERVAL).
        (300, DEFAULT_NORMAL_INTERVAL),
        (20, 10),  # Hälfte des gemeldeten Timeouts
        (4, SUN_IC_MIN_WRITE_INTERVAL),  # sehr kurzer Timeout -> Untergrenze
    ],
)
def test_sun_ic_write_interval(
    hass, ic_timeout: int | None, expected_interval: int
) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    if ic_timeout is not None:
        coordinator.data = {"ic_timeout": ic_timeout}
    assert coordinator._sun_ic_write_interval() == expected_interval


# -- Intervalltypen (dynamische/asynchrone Intervalle) -----------------------
# Siehe intervals.py: HIGH (fest, 2s), NORMAL (konfigurierbar, Default 10s),
# LOW (fest, 10 Minuten). Basic-/SunSpec-Modus-Read sowie beide periodischen
# Schreib-Tasks stehen auf NORMAL; die trägen SunSpec-Felder
# (TASK_READ_SLOW_DATA, siehe SLOW_DATA_KEYS) auf LOW (siehe
# anforderung.yaml).


def test_normal_tasks_default_to_normal_interval(hass) -> None:
    """Basic-/SunSpec-Modus-Read sowie beide periodischen Schreib-Tasks
    haben den Intervalltyp NORMAL - siehe TASK_INTERVALS."""
    for task in (
        TASK_READ_BASIC,
        TASK_READ_EXTENDED,
        TASK_WRITE_GRID_CHARGE,
        TASK_WRITE_SUN_CHARGE,
    ):
        assert TASK_INTERVALS[task] is IntervalType.NORMAL


def test_slow_data_task_has_low_interval(hass) -> None:
    """Die trägen SunSpec-Felder (TASK_READ_SLOW_DATA, siehe
    SLOW_DATA_KEYS) haben den Intervalltyp LOW - siehe TASK_INTERVALS."""
    assert TASK_INTERVALS[TASK_READ_SLOW_DATA] is IntervalType.LOW


def test_coordinator_poll_interval_matches_configured_normal_interval(hass) -> None:
    """Der Poll-Timer des Coordinators (update_interval) wird über
    TASK_READ_BASIC/NORMAL aufgelöst und entspricht deshalb weiterhin dem
    bei der Einrichtung konfigurierten scan_interval, solange dieser Task
    auf NORMAL steht."""
    coordinator = _make_coordinator(hass, _make_client())
    assert coordinator.update_interval.total_seconds() == DEFAULT_NORMAL_INTERVAL


@pytest.mark.parametrize(
    ("scan_interval", "expected"),
    [
        (DEFAULT_NORMAL_INTERVAL, DEFAULT_NORMAL_INTERVAL),  # Standardfall
        (2, SUN_IC_MIN_WRITE_INTERVAL),  # sehr kurz konfiguriert -> Untergrenze greift
        (3600, GRID_CHARGE_WRITE_INTERVAL),  # sehr lang -> Obergrenze greift
    ],
)
def test_resolved_write_interval_is_clamped_to_safe_range(
    hass, scan_interval: int, expected: int
) -> None:
    """_resolved_write_interval() deckelt das über NORMAL/scan_interval
    aufgelöste Intervall auf [SUN_IC_MIN_WRITE_INTERVAL,
    GRID_CHARGE_WRITE_INTERVAL] (Hersteller-Doku: 'alle 5s bis 5min'),
    unabhängig davon, wie klein oder groß scan_interval konfiguriert ist."""
    coordinator = SaxPowerCoordinator(
        hass,
        _make_client(),
        slave_id=64,
        slave_id_extended=100,
        scan_interval=scan_interval,
        entry_id="test_entry_id",
    )
    assert coordinator._resolved_write_interval(TASK_WRITE_GRID_CHARGE) == expected
    assert coordinator._resolved_write_interval(TASK_WRITE_SUN_CHARGE) == expected


async def test_grid_charge_loop_sleeps_for_resolved_write_interval(hass) -> None:
    """_async_grid_charge_loop schläft zwischen den Schreibzyklen um das über
    TASK_WRITE_GRID_CHARGE aufgelöste Intervall, nicht mehr um die feste
    GRID_CHARGE_WRITE_INTERVAL-Konstante direkt.

    `custom_components.sax_power.coordinator.asyncio` ist dasselbe
    Modulobjekt wie das globale `asyncio` (kein lokaler Alias) - ein Patch
    von `.sleep` wirkt sich deshalb auf JEDEN `asyncio.sleep`-Aufruf im
    Prozess aus, auch auf den des Tests selbst. Die Original-Funktion wird
    daher vor dem Patch als `real_sleep` gesichert und für die eigene
    Steuerung des Tests verwendet, statt erneut über das (dann gepatchte)
    Attribut `asyncio.sleep` zuzugreifen."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)
    coordinator = _make_coordinator(hass, client)

    real_sleep = asyncio.sleep
    sleep_calls: list[float] = []

    async def _fake_sleep(seconds: float, *args, **kwargs) -> None:
        sleep_calls.append(seconds)
        raise asyncio.CancelledError

    with patch(
        "custom_components.sax_power.coordinator.asyncio.sleep", new=_fake_sleep
    ):
        await coordinator.async_start_grid_charge(1000)
        await real_sleep(0.05)

    assert sleep_calls == [DEFAULT_NORMAL_INTERVAL]


async def test_modbus_lock_serializes_concurrent_read_and_write(hass) -> None:
    """Reads (_async_update_data, inkl. _async_read_extended) und Writes
    (_async_write_register) dürfen niemals gleichzeitig auf den gemeinsam
    genutzten Modbus-Client zugreifen - siehe SaxPowerCoordinator.
    _modbus_lock. Ohne Lock-Schutz auf der Lese-Seite können ein
    periodischer Coordinator-Poll und ein paralleler Hintergrund-Schreib-
    Task (z. B. _async_grid_charge_loop) gleichzeitig Anfragen an den
    Speicher senden, was auf echter Hardware zu 'Connection Refused' führen
    kann."""
    client = _make_client()
    in_flight = 0
    max_in_flight = 0

    async def _read_side_effect(*, address: int, count: int, device_id: int):
        nonlocal in_flight, max_in_flight
        in_flight += 1
        max_in_flight = max(max_in_flight, in_flight)
        await asyncio.sleep(0.05)
        in_flight -= 1
        result = MagicMock()
        result.isError.return_value = False
        result.registers = [0] * count
        return result

    async def _write_side_effect(*, address: int, value: int, device_id: int):
        nonlocal in_flight, max_in_flight
        in_flight += 1
        max_in_flight = max(max_in_flight, in_flight)
        await asyncio.sleep(0.05)
        in_flight -= 1
        result = MagicMock()
        result.isError.return_value = False
        return result

    client.read_holding_registers = AsyncMock(side_effect=_read_side_effect)
    client.write_register = AsyncMock(side_effect=_write_side_effect)

    coordinator = _make_coordinator(hass, client)

    await asyncio.gather(
        coordinator._async_update_data(),
        coordinator.async_write_register(41, 1000),
    )

    assert max_in_flight == 1


# -- Träge SunSpec-Felder (LOW-Intervall) -------------------------------------
# Hersteller, Gerätemodell, Softwareversion Master/Gateway, Seriennummer,
# Referenzwert Maximalleistung, Speicherkapazität, Entladetiefe, Ladestatus
# Akku und Durchschnittliche Zellspannung (siehe intervals.SLOW_DATA_KEYS)
# liegen physisch im selben SunSpec-Modus-Block wie die schnell benötigten
# Werte und werden deshalb weiterhin bei jedem NORMAL-Zyklus mitgelesen -
# ihre Übernahme in coordinator.data wird aber auf das LOW-Intervall (fest
# 10 Minuten) gedrosselt, siehe SaxPowerCoordinator._apply_slow_data_throttle.


def _make_slow_data_read_side_effect(basic_registers: list[int], battery_capacity: int):
    """Wie _make_read_side_effect, liefert aber im SunSpec-Modus-Block einen
    einstellbaren Wert für Register 97 (battery_capacity, Index 97 relativ
    zu READ_BLOCK_EXT_START=0) - stellvertretend für ein träges Feld, um
    dessen Drosselung zu testen."""

    def _side_effect(*, address: int, count: int, device_id: int):
        result = MagicMock()
        if device_id != 100:
            result.isError.return_value = False
            result.registers = basic_registers
            return result
        result.isError.return_value = False
        registers = [0] * count
        registers[97] = battery_capacity
        result.registers = registers
        return result

    return _side_effect


async def test_slow_data_keys_populated_on_first_successful_read(hass) -> None:
    """Beim allerersten erfolgreichen SunSpec-Modus-Read werden die trägen
    Felder sofort mit dem frisch gelesenen Wert befüllt, nicht erst nach
    Ablauf des LOW-Intervalls."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    client.read_holding_registers = AsyncMock(
        side_effect=_make_slow_data_read_side_effect(basic_registers, 1000)
    )
    coordinator = _make_coordinator(hass, client)

    data = await coordinator._async_update_data()

    assert data["battery_capacity"] == 1000
    assert SLOW_DATA_KEYS <= data.keys()


async def test_slow_data_keys_keep_cached_value_before_low_interval_elapses(
    hass,
) -> None:
    """Ändert sich der zugrunde liegende Rohwert eines trägen Feldes
    zwischen zwei Reads, bevor das LOW-Intervall (10 Minuten) abgelaufen
    ist, bleibt in coordinator.data der zuvor übernommene Wert erhalten -
    obwohl der darunterliegende Modbus-Read den neuen Wert bereits liefert."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    coordinator = _make_coordinator(hass, client)

    with patch(
        "custom_components.sax_power.coordinator.dt_util.utcnow",
        return_value=datetime(2024, 1, 1, 0, 0, 0),
    ):
        client.read_holding_registers = AsyncMock(
            side_effect=_make_slow_data_read_side_effect(basic_registers, 1000)
        )
        data_first = await coordinator._async_update_data()

    with patch(
        "custom_components.sax_power.coordinator.dt_util.utcnow",
        return_value=datetime(2024, 1, 1, 0, 5, 0),  # +5 Minuten < LOW-Intervall
    ):
        client.read_holding_registers = AsyncMock(
            side_effect=_make_slow_data_read_side_effect(basic_registers, 2000)
        )
        data_second = await coordinator._async_update_data()

    assert data_first["battery_capacity"] == 1000
    assert data_second["battery_capacity"] == 1000


async def test_slow_data_keys_refresh_after_low_interval_elapses(hass) -> None:
    """Nach Ablauf des LOW-Intervalls (10 Minuten) wird der zuletzt vom
    Modbus-Read gelieferte Wert eines trägen Feldes in coordinator.data
    übernommen."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    coordinator = _make_coordinator(hass, client)

    with patch(
        "custom_components.sax_power.coordinator.dt_util.utcnow",
        return_value=datetime(2024, 1, 1, 0, 0, 0),
    ):
        client.read_holding_registers = AsyncMock(
            side_effect=_make_slow_data_read_side_effect(basic_registers, 1000)
        )
        data_first = await coordinator._async_update_data()

    with patch(
        "custom_components.sax_power.coordinator.dt_util.utcnow",
        return_value=datetime(2024, 1, 1, 0, 10, 0),  # +10 Minuten = LOW-Intervall
    ):
        client.read_holding_registers = AsyncMock(
            side_effect=_make_slow_data_read_side_effect(basic_registers, 2000)
        )
        data_second = await coordinator._async_update_data()

    assert data_first["battery_capacity"] == 1000
    assert data_second["battery_capacity"] == 2000


# -- Netzdienliches Laden: Zeitfenster-Überlappung ---------------------------


@pytest.mark.parametrize(
    ("start_a", "end_a", "start_b", "end_b", "expected"),
    [
        (dt_time(1, 0), dt_time(5, 0), dt_time(6, 0), dt_time(7, 0), False),  # getrennt
        (
            dt_time(1, 0),
            dt_time(5, 0),
            dt_time(4, 0),
            dt_time(8, 0),
            True,
        ),  # überlappend
        (
            dt_time(1, 0),
            dt_time(5, 0),
            dt_time(5, 0),
            dt_time(6, 0),
            False,
        ),  # berühren sich (Ende exklusiv)
        (
            dt_time(1, 0),
            dt_time(5, 0),
            dt_time(2, 0),
            dt_time(3, 0),
            True,
        ),  # b liegt vollständig in a
        # Fenster a läuft über Mitternacht (23:00-05:00), b liegt im Nacht-Teil
        (dt_time(23, 0), dt_time(5, 0), dt_time(1, 0), dt_time(2, 0), True),
        # Fenster a läuft über Mitternacht, b liegt tagsüber -> keine Überlappung
        (dt_time(23, 0), dt_time(5, 0), dt_time(12, 0), dt_time(13, 0), False),
        # beide Fenster laufen über Mitternacht und überlappen sich im Abend-Teil
        (dt_time(22, 0), dt_time(2, 0), dt_time(23, 0), dt_time(3, 0), True),
        (
            dt_time(1, 0),
            dt_time(1, 0),
            dt_time(0, 0),
            dt_time(23, 59),
            False,
        ),  # a leer (Start==Ende)
    ],
)
def test_windows_overlap(
    start_a: dt_time,
    end_a: dt_time,
    start_b: dt_time,
    end_b: dt_time,
    expected: bool,
) -> None:
    assert windows_overlap(start_a, end_a, start_b, end_b) is expected
    # Symmetrisch: Reihenfolge der beiden Fenster darf keine Rolle spielen.
    assert windows_overlap(start_b, end_b, start_a, end_a) is expected


@pytest.mark.parametrize(
    ("start_a", "end_a", "start_b", "end_b"),
    [
        (None, dt_time(5, 0), dt_time(1, 0), dt_time(2, 0)),
        (dt_time(1, 0), None, dt_time(1, 0), dt_time(2, 0)),
        (dt_time(1, 0), dt_time(5, 0), None, dt_time(2, 0)),
        (dt_time(1, 0), dt_time(5, 0), dt_time(1, 0), None),
    ],
)
def test_windows_overlap_incomplete_window_never_overlaps(
    start_a, end_a, start_b, end_b
) -> None:
    assert windows_overlap(start_a, end_a, start_b, end_b) is False


def _overlap_notifications(hass) -> list[dict]:
    """Persistent Notifications mit "window_overlap" in der ID - siehe
    SaxPowerCoordinator._notify_time_window_overlap. persistent_notification
    legt dafür keine hass.states-Entity mehr an, sondern verwaltet die
    Notifications intern in hass.data[persistent_notification.DOMAIN]
    (siehe homeassistant.components.persistent_notification.async_create)."""
    notifications = hass.data.get(persistent_notification.DOMAIN, {})
    return [
        notification
        for notification_id, notification in notifications.items()
        if "window_overlap" in notification_id
    ]


async def test_set_timed_charge_start_clears_on_overlap_with_grid_serving_window(
    hass,
) -> None:
    """Der Anwender muss informiert werden, wenn er die Netzladezeiten so
    ändert, dass sie in den netzdienlichen Zeitraum fallen würden - siehe
    anforderung.yaml, REQ-GRID-SERVING-CHARGE. Statt die Änderung mit
    HomeAssistantError abzulehnen (altes Verhalten), zeigt der Coordinator
    eine Persistent Notification mit beiden Zeitfenstern/Monaten und leert
    die soeben geänderte Startzeit."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))

    # Verschiebt die Netzladung so, dass sie in den netzdienlichen Zeitraum
    # hineinreicht (neues Fenster 12:00-05:00, über Mitternacht laufend,
    # überschneidet sich mit 10:00-14:00 im Abschnitt 12:00-14:00).
    await coordinator.async_set_timed_charge_start(dt_time(12, 0))
    await hass.async_block_till_done()

    assert coordinator.timed_charge_start is None
    assert coordinator.timed_charge_end == dt_time(5, 0)
    notifications = _overlap_notifications(hass)
    assert len(notifications) == 1
    assert "10:00" in notifications[0]["message"]
    assert "12:00" in notifications[0]["message"]


async def test_set_grid_serving_start_clears_on_overlap_with_timed_charge_window(
    hass,
) -> None:
    """Umgekehrter Fall: Der Anwender wird auch beim Einrichten des
    netzdienlichen Ladens selbst informiert, wenn dessen Zeitfenster in den
    Netzladung-Zeitraum fallen würde."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))

    # Verschiebt das netzdienliche Fenster so, dass es in die Netzladung
    # hineinreicht (neues Fenster 3:00-14:00 überschneidet sich mit 1:00-5:00
    # im Abschnitt 3:00-5:00).
    await coordinator.async_set_grid_serving_start(dt_time(3, 0))
    await hass.async_block_till_done()

    assert coordinator.grid_serving_start is None
    assert coordinator.grid_serving_end == dt_time(14, 0)
    assert len(_overlap_notifications(hass)) == 1


async def test_set_timed_charge_end_clears_on_overlap(hass) -> None:
    """Die Überlappungsprüfung greift auch für die Endzeit, nicht nur für die
    Startzeit."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_grid_serving_start(dt_time(3, 0))
    await coordinator.async_set_grid_serving_end(dt_time(8, 0))
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(2, 0))

    # Neues Fenster 1:00-4:00 überschneidet sich mit 3:00-8:00.
    await coordinator.async_set_timed_charge_end(dt_time(4, 0))
    await hass.async_block_till_done()

    assert coordinator.timed_charge_start == dt_time(1, 0)
    assert coordinator.timed_charge_end is None
    assert len(_overlap_notifications(hass)) == 1


async def test_set_grid_serving_end_clears_on_overlap(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(8, 0))
    await coordinator.async_set_timed_charge_end(dt_time(10, 0))
    await coordinator.async_set_grid_serving_start(dt_time(6, 0))
    await coordinator.async_set_grid_serving_end(dt_time(6, 30))

    # Neues Fenster 6:00-9:00 überschneidet sich mit 8:00-10:00.
    await coordinator.async_set_grid_serving_end(dt_time(9, 0))
    await hass.async_block_till_done()

    assert coordinator.grid_serving_start == dt_time(6, 0)
    assert coordinator.grid_serving_end is None
    assert len(_overlap_notifications(hass)) == 1


async def test_empty_start_or_end_never_activates_feature(hass) -> None:
    """Eine leere (None) Start- oder Endzeit - egal ob durch das Löschen der
    Überlappungs-Benachrichtigung oder anderweitig entstanden - bewirkt
    immer, dass das jeweilige Feature nicht ausgeführt wird (siehe
    SaxPowerCoordinator._is_time_in_window)."""
    coordinator = _make_coordinator(hass, _make_client())
    assert (
        coordinator._is_time_in_window(dt_time(12, 0), None, dt_time(14, 0)) is False
    )
    assert (
        coordinator._is_time_in_window(dt_time(12, 0), dt_time(10, 0), None) is False
    )
    assert coordinator._is_time_in_window(dt_time(12, 0), None, None) is False


async def test_set_windows_with_non_overlapping_times_succeeds(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))

    assert coordinator.timed_charge_start == dt_time(1, 0)
    assert coordinator.timed_charge_end == dt_time(5, 0)
    assert coordinator.grid_serving_start == dt_time(10, 0)
    assert coordinator.grid_serving_end == dt_time(14, 0)


async def test_set_grid_serving_window_clears_on_genuine_overlap(hass) -> None:
    """async_set_grid_serving_window prüft wie die Einzel-Setter das
    tatsächliche Ziel-Fenster - eine echte Überschneidung wird weiterhin
    erkannt, führt aber (wie bei den Einzel-Settern) zu einer
    Benachrichtigung statt zu HomeAssistantError, und beide soeben
    übergebenen Werte werden geleert."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(12, 0))
    await coordinator.async_set_timed_charge_end(dt_time(14, 0))
    await coordinator.async_set_grid_serving_start(dt_time(15, 0))
    await coordinator.async_set_grid_serving_end(dt_time(20, 0))

    await coordinator.async_set_grid_serving_window(dt_time(13, 0), dt_time(16, 0))
    await hass.async_block_till_done()

    assert coordinator.grid_serving_start is None
    assert coordinator.grid_serving_end is None
    assert len(_overlap_notifications(hass)) == 1


async def test_set_grid_serving_window_succeeds_for_non_overlapping_target(
    hass,
) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(12, 0))
    await coordinator.async_set_timed_charge_end(dt_time(14, 0))
    await coordinator.async_set_grid_serving_start(dt_time(15, 0))
    await coordinator.async_set_grid_serving_end(dt_time(20, 0))

    await coordinator.async_set_grid_serving_window(dt_time(8, 0), dt_time(11, 0))

    assert coordinator.grid_serving_start == dt_time(8, 0)
    assert coordinator.grid_serving_end == dt_time(11, 0)


async def test_set_grid_serving_window_avoids_stale_intermediate_false_positive(
    hass,
) -> None:
    """Regressionstest für den gemeldeten Bug: Verschiebt man das
    Zeitfenster des netzdienlichen Ladens über die einzelnen Start-/
    Ende-Entities (async_set_grid_serving_start gefolgt von
    async_set_grid_serving_end), kann ein rein durch die getrennte
    Bearbeitung entstehender Zwischenzustand (neuer Start + noch alter
    Ende-Wert) fälschlich als Überschneidung mit der Netzladung erkannt
    werden, obwohl weder das alte noch das neue Ziel-Fenster tatsächlich
    überlappen. async_set_grid_serving_window setzt beide Werte atomar und
    validiert nur das echte Ziel-Fenster, wodurch dieser Zwischenzustand gar
    nicht erst entsteht."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(12, 0))
    await coordinator.async_set_timed_charge_end(dt_time(14, 0))
    await coordinator.async_set_grid_serving_start(dt_time(15, 0))
    await coordinator.async_set_grid_serving_end(dt_time(20, 0))

    # Der Zwischenzustand (neuer Start 08:00 + noch nicht aktualisiertes
    # altes Ende 20:00) würde die Netzladung (12:00-14:00) überlappen und
    # von async_set_grid_serving_start allein als Überschneidung erkannt -
    # der Start wird dadurch geleert statt auf 08:00 übernommen.
    await coordinator.async_set_grid_serving_start(dt_time(8, 0))
    await hass.async_block_till_done()
    assert coordinator.grid_serving_start is None

    # Das tatsächliche Ziel-Fenster (08:00-11:00) überlappt die Netzladung
    # nicht und wird über den atomaren Setter akzeptiert.
    await coordinator.async_set_grid_serving_window(dt_time(8, 0), dt_time(11, 0))
    assert coordinator.grid_serving_start == dt_time(8, 0)
    assert coordinator.grid_serving_end == dt_time(11, 0)


async def test_set_timed_charge_window_clears_on_genuine_overlap(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))

    await coordinator.async_set_timed_charge_window(dt_time(2, 0), dt_time(11, 0))
    await hass.async_block_till_done()

    assert coordinator.timed_charge_start is None
    assert coordinator.timed_charge_end is None
    assert len(_overlap_notifications(hass)) == 1


async def test_set_timed_charge_window_succeeds_for_non_overlapping_target(
    hass,
) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))

    await coordinator.async_set_timed_charge_window(dt_time(20, 0), dt_time(23, 0))

    assert coordinator.timed_charge_start == dt_time(20, 0)
    assert coordinator.timed_charge_end == dt_time(23, 0)


# -- Netzdienliches Laden: Ladeverhalten -------------------------------------


async def test_enforce_grid_charge_grid_serving_switches_to_setpoint_and_stops_charge(
    hass,
) -> None:
    """Schritt a: Erst wenn der Speicher selbst (über die geräteeigene
    SmartMeter-Nullregelung) bereits mit mindestens
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT lädt (negativer Anteil von
    data["storage_power_active"]), übernimmt netzdienliches Laden aktiv die
    Kontrolle: Wechsel in den Sollwertvorgabemodus UND Ladung sofort auf
    0 % gestoppt, in einem Aufruf (async_start_sun_charge(0)), danach
    zweimal warten (_grid_serving_wait_cycles)."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
        await asyncio.sleep(0.1)

        assert coordinator.grid_serving_active is True
        assert coordinator._timed_charge_active is False
        assert coordinator.sun_charge_active is True
        assert coordinator._grid_serving_wait_cycles == 2
        client.write_register.assert_any_await(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        )
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=0,
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_grid_serving_holds_during_wait_cycles(hass) -> None:
    """Nach dem Auslösen von Schritt a wird Schritt b (Rückkehr in die
    SmartMeter-Nullregelung bei Netzeinspeisung unter dem Schwellwert) für
    die nächsten zwei Aufrufe von _async_enforce_grid_charge unterdrückt,
    selbst wenn die Netzeinspeisung in der Zwischenzeit bereits unter den
    Schwellwert fällt - erst der dritte Aufruf nach dem Trigger wertet
    Schritt b wieder aus."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            await asyncio.sleep(0.1)
            assert coordinator._grid_serving_setpoint_active is True
            assert coordinator._grid_serving_wait_cycles == 2

            # Netzeinspeisung fällt bereits während der Wartezeit unter den
            # Schwellwert - darf noch nicht zur Rückkehr in die
            # Nullregelung führen.
            coordinator.data["smartmeter_power"] = 0

            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._grid_serving_wait_cycles == 1
            assert coordinator.grid_serving_active is True
            assert coordinator.sun_charge_active is True

            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._grid_serving_wait_cycles == 0
            assert coordinator.grid_serving_active is True
            assert coordinator.sun_charge_active is True

            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator.grid_serving_active is False
            assert coordinator.sun_charge_active is False
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_grid_serving_stays_stopped_while_feed_in_high(
    hass,
) -> None:
    """Solange die Netzeinspeisung nach Ablauf der Wartezyklen weiterhin
    mindestens beim Schwellwert liegt, bleibt die Ladung bewusst bei 0 %
    gehalten - der Speicher lädt erst wieder, sobald ein Zeitpunkt mit
    gefallener Einspeisung erreicht ist, statt (wie vor dieser Änderung)
    fortlaufend mit dem gemessenen Überschuss weiterzuladen."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            await asyncio.sleep(0.1)
            write_count_after_trigger = client.write_register.await_count

            for _ in range(3):
                await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)

            assert coordinator.grid_serving_active is True
            assert coordinator.sun_charge_active is True
            # Solange sich am Zustand nichts ändert, schreibt Schritt b
            # selbst nichts erneut - nur der ohnehin laufende periodische
            # Refresh (weit außerhalb der 0.1s Sleep-Zeit hier) würde den
            # gehaltenen 0-%-Sollwert erneut schreiben.
            assert client.write_register.await_count == write_count_after_trigger
            client.write_register.assert_any_await(
                address=REG_SUN_IC_POWER_SETPOINT_PCT,
                value=0,
                device_id=100,
            )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_grid_serving_reverts_to_nullregelung_below_threshold(
    hass,
) -> None:
    """Schritt b: Ist der Sollwertvorgabemodus aktiv (Wartezyklen bereits
    abgelaufen) und fällt die Netzeinspeisung unter den Schwellwert, wird
    der Speicher aktiv zurück in die SmartMeter-Nullregelung gesetzt."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT - 1,
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            coordinator._grid_serving_setpoint_active = True
            coordinator._grid_serving_wait_cycles = 0
            await coordinator.async_start_sun_charge(0)
            await asyncio.sleep(0.1)

            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)

        assert coordinator.grid_serving_active is False
        assert coordinator.sun_charge_active is False
        assert coordinator._grid_serving_setpoint_active is False
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_grid_serving_inactive_without_sax_charge_power(
    hass,
) -> None:
    """Netzdienliches Laden darf innerhalb seines Zeitfensters nicht in den
    Sollwertvorgabemodus wechseln, solange der Speicher selbst (SmartMeter-
    Nullregelung) noch nicht mit mindestens dem Schwellwert lädt."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT - 1),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    with _patched_now(12):
        await coordinator.async_set_grid_serving_enabled(True)
        await asyncio.sleep(0.1)

    assert coordinator.grid_serving_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_grid_charge_grid_serving_inactive_when_storage_power_missing(
    hass,
) -> None:
    """Ohne bekannte tatsächliche Ladeleistung des SAX (z. B. weil der
    SunSpec-Modus gerade nicht erreichbar ist) kann Schritt a nicht
    auslösen - der Speicher bleibt in der SmartMeter-Nullregelung."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    with _patched_now(12):
        await coordinator.async_set_grid_serving_enabled(True)
        await asyncio.sleep(0.1)

    assert coordinator.grid_serving_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_grid_charge_grid_serving_holds_when_feed_in_unknown(
    hass,
) -> None:
    """Ist der Sollwertvorgabemodus bereits aktiv und fehlt anschließend der
    Smart-Meter-Messwert (z. B. SunSpec-Modus vorübergehend nicht
    erreichbar), darf Schritt b nicht ungeprüft in die Nullregelung
    zurückschalten - ohne bekannten Wert bleibt die Ladung gehalten."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            coordinator._grid_serving_setpoint_active = True
            coordinator._grid_serving_wait_cycles = 0
            await coordinator.async_start_sun_charge(0)
            await asyncio.sleep(0.1)

            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)

        assert coordinator.grid_serving_active is True
        assert coordinator.sun_charge_active is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_grid_serving_inactive_outside_window(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    with _patched_now(20):
        await coordinator.async_set_grid_serving_enabled(True)
        await asyncio.sleep(0.1)

    assert coordinator.grid_serving_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_grid_charge_grid_serving_inactive_when_disabled(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    # grid_serving_enabled bleibt False (Default)

    with _patched_now(12):
        await coordinator._async_enforce_grid_charge(coordinator.data)

    assert coordinator.grid_serving_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_grid_charge_max_soc_lock_takes_priority_over_grid_serving(
    hass,
) -> None:
    """Die Max-SOC-Sperre hat auch gegenüber netzdienlichem Laden Vorrang -
    "Auch der angegebene SOC muss berücksichtigt werden"."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 95,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
        await asyncio.sleep(0.1)

        assert coordinator.max_soc_clamped is True
        assert coordinator.grid_serving_active is False
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=0,
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_timed_charge_and_grid_serving_are_mutually_exclusive(
    hass,
) -> None:
    """Selbst wenn beide Zeitfenster (z. B. durch einen über ein Update
    restaurierten Altzustand, unter Umgehung der Setter-Validierung)
    überlappend gespeichert sind, können zeitgesteuertes und netzdienliches
    Laden nie gleichzeitig aktiv werden: grid_serving_eligible verlangt
    explizit "not timed_should_charge" (siehe _async_enforce_grid_charge) -
    solange zeitgesteuertes Laden mit den gegebenen Bedingungen (kein
    PV-Überschuss) aktiv ist, kann netzdienliches Laden für denselben Zyklus
    nicht greifen; erst wenn PV-Überschuss vorliegt, wird zeitgesteuertes
    Laden selbst inaktiv und netzdienliches Laden kann - bei ausreichender
    tatsächlicher SAX-Ladeleistung - übernehmen."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    # Überlappende Fenster direkt gesetzt (umgeht die Setter-Validierung).
    coordinator._timed_charge_start = dt_time(10, 0)
    coordinator._timed_charge_end = dt_time(14, 0)
    coordinator._timed_charge_enabled = True
    coordinator._grid_serving_start = dt_time(10, 0)
    coordinator._grid_serving_end = dt_time(14, 0)
    coordinator._grid_serving_enabled = True
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)

    try:
        with _patched_now(12):
            # Kein PV-Überschuss -> nur zeitgesteuertes Laden kann greifen.
            await coordinator._async_enforce_grid_charge(
                {**coordinator.data, "smartmeter_power": 0}
            )
            await asyncio.sleep(0.1)
            assert coordinator._timed_charge_active is True
            assert coordinator.grid_serving_active is False

            # PV-Überschuss UND ausreichende tatsächliche SAX-Ladeleistung ->
            # nur netzdienliches Laden kann greifen.
            await coordinator._async_enforce_grid_charge(
                {
                    **coordinator.data,
                    "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
                    "storage_power_active": -(
                        SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50
                    ),
                }
            )
            await asyncio.sleep(0.1)
            assert coordinator._timed_charge_active is False
            assert coordinator.grid_serving_active is True
    finally:
        await coordinator.async_stop_sun_charge()


# -- Aktive Monate: Zustand und Enforcement ----------------------------------


def test_months_default_to_all_months(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    assert coordinator.timed_charge_months == frozenset(ALL_MONTHS)
    assert coordinator.grid_serving_months == frozenset(ALL_MONTHS)


async def test_set_timed_charge_month_toggles_membership(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_month(5, False)
    assert 5 not in coordinator.timed_charge_months
    assert coordinator.timed_charge_months == frozenset(ALL_MONTHS - {5})

    await coordinator.async_set_timed_charge_month(5, True)
    assert coordinator.timed_charge_months == frozenset(ALL_MONTHS)


async def test_set_grid_serving_month_toggles_membership(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_grid_serving_month(11, False)
    assert coordinator.grid_serving_months == frozenset(ALL_MONTHS - {11})


async def test_enforce_grid_charge_timed_charge_inactive_outside_active_month(
    hass,
) -> None:
    """ "Netzladung im November, Dezember und Januar zwischen 1 und 5 Uhr" -
    außerhalb der ausgewählten Monate darf trotz passendem Zeitfenster nicht
    geladen werden."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    for month in (11, 12, 1):
        await coordinator.async_set_timed_charge_month(month, True)
    for month in set(ALL_MONTHS) - {11, 12, 1}:
        await coordinator.async_set_timed_charge_month(month, False)
    await coordinator.async_set_timed_charge_enabled(True)

    # Im Zeitfenster (2 Uhr), aber im Juli - nicht in den aktiven Monaten.
    with _patched_now(2, month=7):
        await coordinator._async_enforce_grid_charge(
            {"soc": 10, "ic_max_power_reference": 4600, "ic_timeout": 300}
        )
    assert coordinator._timed_charge_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_grid_charge_timed_charge_active_in_active_month(hass) -> None:
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 10, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    for month in set(ALL_MONTHS) - {11, 12, 1}:
        await coordinator.async_set_timed_charge_month(month, False)
    await coordinator.async_set_timed_charge_enabled(True)

    try:
        # Im Zeitfenster (2 Uhr) UND im Dezember - einer der aktiven Monate.
        with _patched_now(2, month=12):
            await coordinator._async_enforce_grid_charge(coordinator.data)
        await asyncio.sleep(0.1)

        assert coordinator._timed_charge_active is True
        assert coordinator.sun_charge_active is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_grid_serving_respects_active_months(hass) -> None:
    """ "Netzdienliches Laden in Mai, Juni, Juli und August zwischen 11 und 14
    Uhr" - außerhalb dieser Monate darf trotz PV-Überschuss und passendem
    Zeitfenster nicht geladen werden."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(11, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    for month in set(ALL_MONTHS) - {5, 6, 7, 8}:
        await coordinator.async_set_grid_serving_month(month, False)
    await coordinator.async_set_grid_serving_enabled(True)

    # Im Zeitfenster (12 Uhr), aber im Oktober - nicht in den aktiven Monaten.
    with _patched_now(12, month=10):
        await coordinator._async_enforce_grid_charge(coordinator.data)
    assert coordinator.grid_serving_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_grid_charge_grid_serving_active_in_selected_month(hass) -> None:
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(11, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    for month in set(ALL_MONTHS) - {5, 6, 7, 8}:
        await coordinator.async_set_grid_serving_month(month, False)
    await coordinator.async_set_grid_serving_enabled(True)

    try:
        with _patched_now(12, month=7):
            await coordinator._async_enforce_grid_charge(coordinator.data)
        await asyncio.sleep(0.1)

        assert coordinator.grid_serving_active is True
        assert coordinator.sun_charge_active is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_inactive_when_all_months_deselected(hass) -> None:
    """Sind für ein Feature gar keine Monate ausgewählt, ist es ganzjährig
    inaktiv - analog zu einem leeren Zeitfenster."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_max_charge_power(3000)
    for month in ALL_MONTHS:
        await coordinator.async_set_timed_charge_month(month, False)
    await coordinator.async_set_timed_charge_enabled(True)

    assert coordinator.timed_charge_months == frozenset()
    with _patched_now(2, month=1):
        await coordinator._async_enforce_grid_charge(
            {"soc": 10, "ic_max_power_reference": 4600, "ic_timeout": 300}
        )
    assert coordinator._timed_charge_active is False


# -- Aktive Monate: Überlappungsprüfung berücksichtigt Monate ---------------


async def test_overlapping_times_with_disjoint_months_are_allowed(hass) -> None:
    """ "Netzdienliches Laden in Mai-August, Netzladung in November-Januar" -
    die Tageszeiten dürfen sich beliebig überlappen, weil die Fenster nie im
    selben Monat aktiv sind.

    Monate zunächst direkt gesetzt (umgeht Setter-Validierung) - das
    entspricht dem realistischen Bedienpfad, bei dem der Anwender zuerst
    beide Monatsauswahlen auf disjunkte Werte einstellt (unproblematisch,
    solange noch keines der beiden Zeitfenster das andere überlappt - siehe
    Kommentar in der Netzdienlich-Sektion zu den leeren Default-Zeiten) und
    danach beide Zeitfenster ändert."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator._timed_charge_months = {11, 12, 1}
    coordinator._grid_serving_months = {5, 6, 7, 8}

    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    # Gleiches Zeitfenster wie die Netzladung, aber disjunkte Monate - darf
    # nicht abgelehnt werden.
    await coordinator.async_set_grid_serving_start(dt_time(1, 0))
    await coordinator.async_set_grid_serving_end(dt_time(5, 0))

    assert coordinator.timed_charge_start == dt_time(1, 0)
    assert coordinator.grid_serving_start == dt_time(1, 0)


async def test_set_timed_charge_month_rejects_overlap_with_grid_serving(hass) -> None:
    """Fügt man einen Monat hinzu, der die Netzladung wieder in dieselben
    Monate wie das netzdienliche Laden bringt (bei gleichzeitig
    überlappenden Zeitfenstern), muss das abgelehnt werden."""
    from homeassistant.exceptions import HomeAssistantError

    coordinator = _make_coordinator(hass, _make_client())
    coordinator._timed_charge_start = dt_time(1, 0)
    coordinator._timed_charge_end = dt_time(5, 0)
    coordinator._timed_charge_months = {11, 12, 1}
    coordinator._grid_serving_start = dt_time(3, 0)
    coordinator._grid_serving_end = dt_time(6, 0)
    coordinator._grid_serving_months = {6, 7}

    # Zeitfenster überschneiden sich bereits (3-5 Uhr), Monate sind aktuell
    # disjunkt (Netzladung Nov/Dez/Jan vs. netzdienlich Jun/Jul) - erlaubt.
    # Erweitert man die Netzladung nun auf Juni, überschneiden sich auch die
    # Monate -> muss abgelehnt werden.
    with pytest.raises(HomeAssistantError):
        await coordinator.async_set_timed_charge_month(6, True)

    assert 6 not in coordinator.timed_charge_months


async def test_set_grid_serving_month_rejects_overlap_with_timed_charge(hass) -> None:
    from homeassistant.exceptions import HomeAssistantError

    coordinator = _make_coordinator(hass, _make_client())
    coordinator._timed_charge_start = dt_time(1, 0)
    coordinator._timed_charge_end = dt_time(5, 0)
    coordinator._timed_charge_months = {6, 7}
    coordinator._grid_serving_start = dt_time(3, 0)
    coordinator._grid_serving_end = dt_time(6, 0)
    coordinator._grid_serving_months = {11, 12, 1}

    # Zeitfenster überschneiden sich bereits (3-5 Uhr), Monate sind aktuell
    # disjunkt - erweitert man netzdienliches Laden nun auf Juni,
    # überschneiden sich auch die Monate -> muss abgelehnt werden.
    with pytest.raises(HomeAssistantError):
        await coordinator.async_set_grid_serving_month(6, True)

    assert 6 not in coordinator.grid_serving_months


async def test_month_restore_does_not_validate_overlap(hass) -> None:
    """validate=False (Restaurieren beim Start, siehe SaxPowerMonthSwitch)
    muss auch überlappende Zwischenzustände klaglos übernehmen - die
    Validierung ist ausschließlich für explizite Nutzeränderungen gedacht."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator._timed_charge_start = dt_time(1, 0)
    coordinator._timed_charge_end = dt_time(5, 0)
    coordinator._grid_serving_start = dt_time(3, 0)
    coordinator._grid_serving_end = dt_time(6, 0)

    # Beide Fenster überschneiden sich (3-5 Uhr) und starten mit "alle
    # Monate" (Default) - ohne validate=False würde das hier ablehnen.
    await coordinator.async_set_timed_charge_month(6, True, validate=False)
    await coordinator.async_set_grid_serving_month(6, True, validate=False)

    assert 6 in coordinator.timed_charge_months
    assert 6 in coordinator.grid_serving_months
