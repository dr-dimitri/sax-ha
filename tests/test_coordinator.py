"""Tests for the SAX Power coordinator."""

from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.sax_power.const import (
    GRID_CHARGE_WRITE_INTERVAL,
    READ_BLOCK_COUNT,
    READ_BLOCK_START,
    REG_SOC,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
    SUN_IC_MIN_WRITE_INTERVAL,
)
from custom_components.sax_power.coordinator import (
    SaxPowerCoordinator,
    apply_sunssf,
    to_signed16,
    to_unsigned16,
)


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
    return SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
    )


async def test_enforce_max_soc_clamps_charge_limit(hass) -> None:
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    await coordinator.async_set_max_soc(80)

    data = {"soc": 85, "charge_limit": 3000}
    await coordinator._async_enforce_max_soc(data)

    assert data["charge_limit"] == 0
    client.write_register.assert_awaited_once()
    assert coordinator._max_soc_clamped is True


async def test_enforce_max_soc_restores_charge_limit(hass) -> None:
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator._max_soc = 80
    coordinator._max_soc_clamped = True
    coordinator._pre_clamp_charge_limit = 3000

    data = {"soc": 70, "charge_limit": 0}
    await coordinator._async_enforce_max_soc(data)

    assert data["charge_limit"] == 3000
    assert coordinator._max_soc_clamped is False


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
    coordinator._timed_charge_start = start
    coordinator._timed_charge_end = end
    assert coordinator._is_time_in_window(now) is expected


def test_is_time_in_window_unset_is_never_active(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    assert coordinator._is_time_in_window(dt_time(3, 0)) is False


def _patched_now(hour: int, minute: int = 0):
    """Patcht dt_util.now() auf einen festen Zeitpunkt.

    Bewusst statt der `freezer`-Fixture (freezegun): freezegun friert auch
    die vom Event-Loop für `asyncio.sleep` genutzte Uhr ein, wodurch der in
    async_start_grid_charge gespawnte Hintergrund-Task nie mehr aufwacht und
    der Test hängt. Ein gezielter Patch nur von dt_util.now() betrifft
    ausschließlich unsere eigene Zeitfenster-Prüfung.
    """
    return patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, hour, minute),
    )


async def test_enforce_timed_charge_starts_when_enabled_in_window_below_target(
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
        "charge_limit": 3000,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)  # Ziel-SOC = "Max. SOC"

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


async def test_enforce_timed_charge_stops_when_target_soc_reached(hass) -> None:
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 90,
        "charge_limit": 3000,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)  # Ziel-SOC = "Max. SOC"
    coordinator._timed_charge_active = True
    # Echter (cancelbarer) Task statt MagicMock, da async_stop_sun_charge die
    # Cancellation awaitet, bevor es den Steuermodus zurücksetzt.
    coordinator._sun_charge_task = asyncio.create_task(asyncio.sleep(3600))

    with _patched_now(2):
        await coordinator._async_enforce_timed_charge({"soc": 90, "charge_limit": 3000})

    assert coordinator._timed_charge_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_timed_charge_inactive_outside_window(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)  # Ziel-SOC = "Max. SOC"
    await coordinator.async_set_timed_charge_enabled(True)

    with _patched_now(12):
        await coordinator._async_enforce_timed_charge({"soc": 10, "charge_limit": 3000})

    assert coordinator._timed_charge_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_timed_charge_inactive_when_disabled(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)  # Ziel-SOC = "Max. SOC"
    # timed_charge_enabled bleibt False (Default)

    with _patched_now(2):
        await coordinator._async_enforce_timed_charge({"soc": 10, "charge_limit": 3000})

    assert coordinator._timed_charge_active is False
    assert coordinator.sun_charge_active is False


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
        (None, GRID_CHARGE_WRITE_INTERVAL),  # noch kein Timeout bekannt -> Fallback
        (300, GRID_CHARGE_WRITE_INTERVAL),  # Geräte-Default (modbus.pdf) -> gedeckelt
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
