"""Tests for the SAX Power coordinator."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from homeassistant.components import persistent_notification
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from custom_components.sax_power.application.calibration import CalibrationState
from custom_components.sax_power.const import (
    ALL_MONTHS,
    CELL_CALIBRATION_INTERVAL,
    CONF_PV_FORECAST_SENSOR,
    GRID_CHARGE_WRITE_INTERVAL,
    MAX_MANUAL_CHARGE_POWER,
    MAX_SETPOINT_POWER,
    MAX_SOC,
    MIN_SETPOINT_POWER,
    PV_SURPLUS_HYSTERESIS_CYCLES,
    READ_BLOCK_COUNT,
    READ_BLOCK_EXT_HIGH_INTERVAL,
    READ_BLOCK_EXT_LOW1_START,
    READ_BLOCK_EXT_LOW2_START,
    READ_BLOCK_EXT_LOW_INTERVAL,
    READ_BLOCK_EXT_START,
    READ_BLOCK_START,
    REG_SOC,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
    SUN_IC_MIN_WRITE_INTERVAL,
)
from custom_components.sax_power.coordinator import (
    SaxPowerCoordinator,
    _clamp_int,
    _grid_serving_pause_status,
    apply_sunssf,
    to_signed16,
    to_unsigned16,
    windows_overlap,
)


@pytest.mark.parametrize(
    (
        "enabled",
        "months",
        "hour",
        "sensor_configured",
        "forecast_kwh",
        "threshold_kwh",
        "expected",
    ),
    [
        (False, {7}, 10, False, None, 10, "Inaktiv"),
        (True, {7}, 10, False, None, 10, "Inaktiv im Monat August"),
        (True, {8}, 10, False, None, 10, "Außerhalb des Zeitfensters"),
        (
            True,
            {8},
            12,
            False,
            None,
            10,
            "Ladepause ist zwischen 11:00 Uhr und 14:00 Uhr im August aktiv.",
        ),
        (True, {8}, 12, True, None, 10, "PV-Prognose nicht verfügbar"),
        (
            True,
            {8},
            12,
            True,
            8,
            10,
            "Ladepause inaktiv, da die PV-Prognose von 8 kWh kleiner als der "
            "Mindestwert von 10 kWh ist.",
        ),
        (
            True,
            {8},
            12,
            True,
            12,
            10,
            "Ladepause ist zwischen 11:00 Uhr und 14:00 Uhr im August aktiv. Die "
            "PV-Prognose von 12 kWh ist größer als der Mindestwert von 10 kWh.",
        ),
        (
            True,
            {8},
            12,
            True,
            10,
            10,
            "Ladepause ist zwischen 11:00 Uhr und 14:00 Uhr im August aktiv. Die "
            "PV-Prognose von 10 kWh ist gleich dem Mindestwert von 10 kWh.",
        ),
        (
            True,
            {8},
            12,
            False,
            None,
            0,
            "Ladepause ist zwischen 11:00 Uhr und 14:00 Uhr im August aktiv.",
        ),
    ],
)
def test_grid_serving_pause_status_priority(
    enabled: bool,
    months: set[int],
    hour: int,
    sensor_configured: bool,
    forecast_kwh: float | None,
    threshold_kwh: float,
    expected: str,
) -> None:
    """REQ-GRID-SERVING-CHARGE: Statusfälle und Vergleich gelten priorisiert."""
    assert (
        _grid_serving_pause_status(
            now=datetime(2024, 8, 1, hour),
            enabled=enabled,
            start=dt_time(11),
            end=dt_time(14),
            months=months,
            forecast_sensor_configured=sensor_configured,
            forecast_kwh=forecast_kwh,
            threshold_kwh=threshold_kwh,
        )
        == expected
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


@pytest.mark.parametrize(
    ("value", "min_value", "max_value", "expected"),
    [
        (50, 0, 100, 50),  # innerhalb des Bereichs -> unverändert
        (0, 0, 100, 0),  # genau auf der unteren Grenze -> unverändert
        (100, 0, 100, 100),  # genau auf der oberen Grenze -> unverändert
        (-20, 0, 100, 0),  # unterschreitet -> auf min_value geklemmt
        (500, 0, 100, 100),  # überschreitet -> auf max_value geklemmt
        (None, 0, 100, None),  # "keine Einstellung" bleibt unverändert
    ],
)
def test_clamp_int(
    value: int | None, min_value: int, max_value: int, expected: int | None
) -> None:
    assert _clamp_int(value, min_value, max_value) == expected


def _make_client() -> MagicMock:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)
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
    # Bewusst MAX_SOC statt des tatsächlichen Number-Entity-Vorgabewerts
    # (DEFAULT_TIMED_CHARGE_MIN_SOC, siehe number.py) - hält Netzladung in
    # den meisten Tests unabhängig vom jeweils verwendeten current_soc
    # "armed", ohne dass jeder Test, der zeitgesteuertes Laden auslösen
    # will, zusätzlich async_set_timed_charge_min_soc aufrufen muss. Tests,
    # die den echten Vorgabewert selbst prüfen wollen, setzen ihn explizit
    # (siehe tests/test_number.py).
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


def test_update_interval_matches_high_interval(hass) -> None:
    """Der Coordinator-Timer läuft mit dem kürzeren der beiden Intervalle
    (siehe __init__) - da das config_flow-Minimum für scan_interval (5s)
    immer über READ_BLOCK_EXT_HIGH_INTERVAL (2s) liegt, ist das faktisch
    immer Letzteres, siehe anforderung.yaml, REQ-HIGH-INTERVAL-REGISTERS."""
    coordinator = _make_coordinator(hass, _make_client())  # scan_interval=10
    assert coordinator.update_interval == timedelta(
        seconds=READ_BLOCK_EXT_HIGH_INTERVAL
    )


async def test_due_cell_calibration_lifts_max_soc_without_forcing_grid_charge(
    hass,
) -> None:
    """REQ-PERIODIC-FULL-CALIBRATION: Fälligkeit hebt nur die Software-
    Sperre auf; ohne konfigurierte Ladeautomatik startet kein Netzladen."""
    coordinator = _make_coordinator(hass, _make_client())
    now = datetime(2026, 8, 24, 8, 0, tzinfo=UTC)
    coordinator._max_soc = 80
    coordinator._cell_calibration_state = CalibrationState(
        now - CELL_CALIBRATION_INTERVAL,
        was_full=False,
    )
    coordinator._calibration_store.async_save = AsyncMock()
    coordinator.async_start_sun_charge = AsyncMock()
    coordinator.async_stop_sun_charge = AsyncMock()

    changed = await coordinator._async_update_cell_calibration(80, now=now)
    await coordinator._async_enforce_grid_charge({"soc": 80, "smartmeter_power": 0})

    assert changed is True
    assert coordinator.cell_calibration_active is True
    assert coordinator.max_soc == 80
    assert coordinator.effective_max_soc == 100
    assert coordinator.max_soc_clamped is False
    coordinator.async_start_sun_charge.assert_not_awaited()
    coordinator.async_stop_sun_charge.assert_awaited_once()
    coordinator._calibration_store.async_save.assert_not_awaited()


async def test_full_soc_completes_calibration_and_reapplies_user_target(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    now = datetime(2026, 8, 24, 8, 0, tzinfo=UTC)
    coordinator._max_soc = 80
    coordinator._cell_calibration_state = CalibrationState(
        now - timedelta(days=8),
        was_full=False,
    )
    coordinator._cell_calibration_active = True
    coordinator._max_soc_released_for_discharge = True
    coordinator._last_effective_max_soc = MAX_SOC
    coordinator._calibration_store.async_save = AsyncMock()
    coordinator.async_start_sun_charge = AsyncMock()

    changed = await coordinator._async_update_cell_calibration(100, now=now)
    await coordinator._async_enforce_grid_charge({"soc": 100, "smartmeter_power": 0})

    assert changed is True
    assert coordinator.cell_calibration_active is False
    assert coordinator.effective_max_soc == 80
    assert coordinator._max_soc_released_for_discharge is False
    assert coordinator.last_full_charge_at == now
    assert coordinator.next_cell_calibration_at == now + CELL_CALIBRATION_INTERVAL
    assert coordinator.max_soc_clamped is True
    coordinator.async_start_sun_charge.assert_awaited_once_with(0)
    coordinator._calibration_store.async_save.assert_awaited_once_with(
        CalibrationState(now, was_full=True)
    )


async def test_max_soc_changes_keep_latest_user_value_during_calibration(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    now = datetime(2026, 8, 24, 8, 0, tzinfo=UTC)
    coordinator.data = {"soc": 50, "smartmeter_power": 0}
    coordinator._max_soc = 80
    coordinator._cell_calibration_state = CalibrationState(
        now - timedelta(days=8),
        was_full=False,
    )
    coordinator._calibration_store.async_save = AsyncMock()
    coordinator._async_apply_grid_charge_change = AsyncMock()
    coordinator.price_planner.evaluate = MagicMock()
    await coordinator._async_update_cell_calibration(50, now=now)

    with patch(
        "custom_components.sax_power.coordinator.dt_util.utcnow", return_value=now
    ):
        await coordinator.async_set_max_soc(90)
        assert coordinator.max_soc == 90
        assert coordinator.cell_calibration_active is True
        assert coordinator.effective_max_soc == 100

        await coordinator.async_set_max_soc(100)
        assert coordinator.cell_calibration_active is False
        assert coordinator.effective_max_soc == 100

        await coordinator.async_set_max_soc(70)
        assert coordinator.max_soc == 70
        assert coordinator.cell_calibration_active is True
        assert coordinator.effective_max_soc == 100


async def test_calibration_state_load_restores_overdue_schedule(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    now = datetime(2026, 8, 24, 8, 0, tzinfo=UTC)
    stored = CalibrationState(now - timedelta(days=8), was_full=False)
    coordinator._calibration_store.async_load = AsyncMock(return_value=stored)
    coordinator._calibration_store.async_save = AsyncMock()

    await coordinator.async_load_calibration_state()
    coordinator._max_soc = 80
    await coordinator._async_update_cell_calibration(50, now=now)

    assert coordinator.last_full_charge_at == stored.last_full_charge_at
    assert coordinator.cell_calibration_active is True
    assert coordinator.effective_max_soc == 100
    coordinator._calibration_store.async_save.assert_not_awaited()


async def test_calibration_storage_failure_does_not_abort_update(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    coordinator._max_soc = 80
    coordinator._calibration_store.async_save = AsyncMock(
        side_effect=OSError("Datenträger voll")
    )

    changed = await coordinator._async_update_cell_calibration(
        50,
        now=datetime(2026, 8, 24, 8, 0, tzinfo=UTC),
    )

    assert changed is False
    assert coordinator.last_full_charge_at is not None


async def test_write_register_forces_fresh_basic_read(hass) -> None:
    """Ein Schreibzugriff auf ein Basic-Mode-Register (z. B. über den
    Storage-On/Off-Schalter) muss beim direkt danach ausgelösten
    coordinator.async_refresh() einen echten Read liefern, nicht den vor dem
    Schreiben gecachten NORMAL-Wert - siehe DEVELOPMENT.md, Abschnitt
    "Refresh-Verhalten", sowie switch.SaxPowerStorageSwitch."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)
    client.read_holding_registers = AsyncMock(
        side_effect=_make_read_side_effect(basic_registers, extended_error=False)
    )
    coordinator = _make_coordinator(hass, client)

    def basic_read_count() -> int:
        return sum(
            1
            for call in client.read_holding_registers.call_args_list
            if call.kwargs["device_id"] == 64
        )

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        await coordinator._async_read_basic()  # initialer Read füllt den Cache
    assert basic_read_count() == 1

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.5
    ):
        # Ohne den Schreibzugriff wäre dies innerhalb des scan_interval
        # (10s) - der Cache würde greifen und den alten Wert liefern.
        await coordinator.async_write_register(45, 2)
        await coordinator._async_read_basic()
    assert basic_read_count() == 2


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


async def test_extended_unavailable_since_set_on_the_edge(hass) -> None:
    """_extended_unavailable_since (Grundlage für die Eskalation
    ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE, siehe anforderung.yaml,
    REQ-SELF-DIAGNOSIS-REPAIRS) wird nur beim ERSTEN Ausfall gesetzt, nicht
    bei jedem weiteren Poll-Zyklus, in dem der Block weiterhin nicht
    erreichbar ist."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    client.read_holding_registers = AsyncMock(
        side_effect=_make_read_side_effect(basic_registers, extended_error=True)
    )
    coordinator = _make_coordinator(hass, client)

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        await coordinator._async_update_data()
    assert coordinator._extended_unavailable_since == 1000.0

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=2000.0
    ):
        await coordinator._async_update_data()
    assert coordinator._extended_unavailable_since == 1000.0


async def test_extended_unavailable_since_cleared_on_recovery(hass) -> None:
    """Wird der SunSpec-Modus-Block wieder erreichbar, muss der Zeitstempel
    zurückgesetzt werden - sonst würde ein späterer, neuer Ausfall
    fälschlich sofort als "schon lange andauernd" gewertet."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    client.read_holding_registers = AsyncMock(
        side_effect=_make_read_side_effect(basic_registers, extended_error=True)
    )
    coordinator = _make_coordinator(hass, client)
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        await coordinator._async_update_data()
    assert coordinator._extended_unavailable_since == 1000.0

    client.read_holding_registers = AsyncMock(
        side_effect=_make_read_side_effect(basic_registers, extended_error=False)
    )
    await coordinator._async_update_data()

    assert coordinator._extended_unavailable_since is None


async def test_normal_block_throttled_high_block_follows_own_interval(hass) -> None:
    """Der NORMAL-Block (Basic Mode) wird trotz des jetzt kürzeren
    Coordinator-Timers (siehe READ_BLOCK_EXT_HIGH_INTERVAL) weiterhin nur
    alle self._scan_interval Sekunden tatsächlich neu gelesen; der
    HIGH-Block dagegen bei jedem Tick, sobald sein eigenes (kürzeres)
    Intervall abgelaufen ist - siehe anforderung.yaml,
    REQ-HIGH-INTERVAL-REGISTERS."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    basic_registers[REG_SOC - READ_BLOCK_START] = 55
    client.read_holding_registers = AsyncMock(
        side_effect=_make_read_side_effect(basic_registers, extended_error=False)
    )
    coordinator = _make_coordinator(hass, client)  # scan_interval=10

    def basic_read_count() -> int:
        return sum(
            1
            for call in client.read_holding_registers.call_args_list
            if call.kwargs["device_id"] == 64
        )

    def high_read_count() -> int:
        return sum(
            1
            for call in client.read_holding_registers.call_args_list
            if call.kwargs["address"] == READ_BLOCK_EXT_START
        )

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        await coordinator._async_update_data()
    assert basic_read_count() == 1  # erster Poll: beide Blöcke fällig
    assert high_read_count() == 1

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1001.0
    ):
        await coordinator._async_update_data()
    assert basic_read_count() == 1  # < scan_interval (10s): kein Reread
    # Der initiale Nullregelungs-Write hat den HIGH-Cache absichtlich
    # invalidiert; daher wird sein Readback unabhängig vom Intervall sofort
    # beim nächsten Takt verifiziert.
    assert high_read_count() == 2

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1003.0
    ):
        await coordinator._async_update_data()
    assert basic_read_count() == 1  # weiterhin < scan_interval
    assert high_read_count() == 3  # >= HIGH-Intervall seit t=1001 -> Reread

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1011.0
    ):
        await coordinator._async_update_data()
    assert basic_read_count() == 2  # >= scan_interval seit t=1000 -> Reread
    assert high_read_count() == 4  # >= HIGH-Intervall seit t=1003 -> Reread


async def test_low_block_read_only_once_per_interval(hass) -> None:
    """Die LOW-Intervall-Register (Common Model + Battery-Skalierungsfaktoren,
    Register 40000-40016/40110-40114) werden nur beim ersten Poll sowie nach
    Ablauf von READ_BLOCK_EXT_LOW_INTERVAL Sekunden neu gelesen, nicht bei
    jedem regulären Poll - siehe anforderung.yaml,
    REQ-LOW-INTERVAL-REGISTERS."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    basic_registers[REG_SOC - READ_BLOCK_START] = 55
    client.read_holding_registers = AsyncMock(
        side_effect=_make_read_side_effect(basic_registers, extended_error=False)
    )
    coordinator = _make_coordinator(hass, client)

    low_block_addresses = (READ_BLOCK_EXT_LOW1_START, READ_BLOCK_EXT_LOW2_START)

    def low_block_read_count() -> int:
        return sum(
            1
            for call in client.read_holding_registers.call_args_list
            if call.kwargs["address"] in low_block_addresses
        )

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        await coordinator._async_update_data()
    assert low_block_read_count() == 2  # LOW1 + LOW2 beim allerersten Poll

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1001.0
    ):
        await coordinator._async_update_data()
    assert low_block_read_count() == 2  # innerhalb des Intervalls: kein Reread

    with patch(
        "custom_components.sax_power.coordinator.monotonic",
        return_value=1000.0 + READ_BLOCK_EXT_LOW_INTERVAL + 1,
    ):
        await coordinator._async_update_data()
    assert low_block_read_count() == 4  # Intervall abgelaufen -> erneuter Read


async def test_low_block_failure_does_not_fail_update(hass) -> None:
    """Scheitert ausschließlich der LOW-Intervall-Read (der HIGH-Block bleibt
    lesbar), darf das Update nicht fehlschlagen - nur die zugehörigen
    Diagnose-Sensoren bleiben bis zum nächsten erfolgreichen Refresh ohne
    Wert, analog zu REQ-EXTENDED-MODE-RESILIENCE für den gesamten
    SunSpec-Modus-Block."""
    client = _make_client()
    basic_registers = [0] * READ_BLOCK_COUNT
    basic_registers[REG_SOC - READ_BLOCK_START] = 55

    def _side_effect(*, address: int, count: int, device_id: int):
        result = MagicMock()
        if device_id != 100:
            result.isError.return_value = False
            result.registers = basic_registers
        elif address == READ_BLOCK_EXT_START:
            result.isError.return_value = False
            result.registers = [0] * count
        else:
            result.isError.return_value = True
            result.registers = []
        return result

    client.read_holding_registers = AsyncMock(side_effect=_side_effect)
    coordinator = _make_coordinator(hass, client)

    data = await coordinator._async_update_data()

    assert data["soc"] == 55
    assert data["storage_power_active"] == 0
    assert "sun_manufacturer" not in data


def test_parse_low_block_decodes_identity_and_caches_battery_sf(hass) -> None:
    """Parst den LOW-Intervall-Block (SunSpec Common Model + Inverter-
    Modellkopf, Battery-Skalierungsfaktoren) - siehe anforderung.yaml,
    REQ-LOW-INTERVAL-REGISTERS. Die Battery-Skalierungsfaktoren werden dabei
    zusätzlich als self._battery_*_sf_raw zwischengespeichert, da
    _parse_extended sie nicht mehr selbst aus dem HIGH-Block liest."""
    coordinator = _make_coordinator(hass, _make_client())

    low1 = {
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
        15: 103,  # Inverter Model-ID
        16: 32,  # Inverter Länge
    }
    low2 = {
        110: to_unsigned16(-1),  # Scalefaktor Kapazität
        111: 0,  # Scalefaktor Lade/Entladeleistung
        112: 0,  # Scalefaktor SoC
        113: 0,  # Reserve
        114: 0,  # Scalefaktor Zellspannung
    }

    data = coordinator._parse_low_block(low1.__getitem__, low2.__getitem__)

    assert data["sun_manufacturer"] == "SAXPOWER"
    assert data["sun_model"] == "HOME"
    assert data["sun_version_master"] == 23
    assert data["sun_version_gateway"] == 56
    assert data["sun_serial_number"] == (15448 << 16) | 97

    assert coordinator._battery_capacity_sf_raw == to_unsigned16(-1)
    assert coordinator._battery_power_sf_raw == 0
    assert coordinator._battery_soc_sf_raw == 0
    assert coordinator._battery_cell_voltage_sf_raw == 0


def test_parse_extended_decodes_sunspec_block(hass) -> None:
    """Parst den HIGH-Intervall-Teil des SunSpec-Modus-Blocks (Slave-ID 100,
    siehe modbus.pdf) - 3Ph Inverter (103), Immediate Controls (123), Meter
    (203) und Battery (802). Siehe anforderung.yaml,
    REQ-SUNSPEC-MODE-CORRECTION sowie REQ-LOW-INTERVAL-REGISTERS (Common
    Model + Battery-Skalierungsfaktoren werden separat getestet, siehe
    test_parse_low_block_decodes_identity_and_caches_battery_sf)."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)

    # Alle Register im HIGH-Block (Adresse 17-109) auf 0 vorbelegen, damit
    # fehlende Overrides unten nicht zu KeyError führen, und dann die für
    # den Test relevanten Werte überschreiben. sf-Register = 0 (Faktor 1),
    # damit skalierte Werte den Rohwerten entsprechen. Die
    # Battery-Skalierungsfaktoren kommen inzwischen aus dem LOW-Block
    # (self._battery_*_sf_raw, hier auf ihrem __init__-Default 0 belassen).
    raw = dict.fromkeys(range(17, 110), 0)
    raw.update(
        {
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
            73: 100,  # Netzleistung L1
            74: 80,  # Netzleistung L2
            75: 70,  # Netzleistung L3
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

    assert "sun_manufacturer" not in data  # jetzt Teil des LOW-Blocks

    assert data["storage_current_sum"] == 30
    assert data["storage_current_a"] == 5
    assert data["storage_power_active"] == 1500
    assert data["storage_state_text"] == "Ein"
    assert data["storage_event_text"] == "Normalbetrieb"

    assert data["ic_control_mode_text"] == "Sollwertvorgabe"
    assert data["ic_max_power_reference"] == 4600

    assert data["grid_current_sum"] == 20
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
    die vom Event-Loop für `asyncio.sleep` genutzte Uhr ein, wodurch der
    gemeinsame SunSpec-Hintergrundtask nie mehr aufwacht und der Test hängt.
    Ein gezielter Patch nur von dt_util.now() betrifft
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

    try:
        with _patched_now(2):
            await coordinator.async_set_timed_charge_enabled(True)

        assert coordinator._timed_charge_active is True
        assert coordinator.sun_charge_active is True
        client.write_register.assert_any_await(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        )
        # Lädt immer mit maximal möglicher Leistung (MIN_SETPOINT_POWER
        # sättigt in _watts_to_ic_setpoint_raw auf -100 %), sunssf -2
        # (Default-Annahme) -> -10000.
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=to_unsigned16(-10000),
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


@pytest.mark.parametrize(
    "power",
    [
        True,
        1.5,
        MIN_SETPOINT_POWER - 1,
        0,
        1,
        MAX_SETPOINT_POWER + 1,
    ],
)
async def test_manual_grid_charge_rejects_unsafe_power_before_write(
    hass, power: object
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Nur strikt negative int16-Wattwerte sind
    zulässig; jeder andere Wert scheitert übersetzbar ohne Modbus-Write."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}

    with pytest.raises(ServiceValidationError) as raised:
        await coordinator.async_start_grid_charge(power)  # type: ignore[arg-type]

    assert raised.value.translation_domain == "sax_power"
    assert raised.value.translation_key == "invalid_grid_charge_power"
    assert raised.value.translation_placeholders == {
        "min_power": str(MIN_SETPOINT_POWER),
        "max_power": str(MAX_MANUAL_CHARGE_POWER),
        "power": repr(power),
    }
    client.write_register.assert_not_awaited()
    assert coordinator.grid_charge_active is False


async def test_manual_grid_charge_first_write_failure_is_visible(hass) -> None:
    """REQ-MANUAL-GRID-CHARGE: Der Service bestätigt keinen Start, bevor
    Register 40051 erfolgreich geschrieben wurde."""
    client = _make_client()
    failure = MagicMock()
    failure.isError.return_value = True
    failure.__str__.return_value = "Mode-Write abgelehnt"
    client.write_register = AsyncMock(return_value=failure)
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_max_power_reference": 4600,
    }

    with pytest.raises(HomeAssistantError, match="Register 40051.*abgebrochen"):
        await coordinator.async_start_grid_charge(-1500)

    assert coordinator.grid_charge_active is False
    assert coordinator.sun_charge_active is False
    assert client.write_register.await_args_list == [
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        )
    ]


async def test_manual_grid_charge_stop_retries_orphaned_failed_rollback(hass) -> None:
    """REQ-MANUAL-GRID-CHARGE: Scheitern 40049 und sein Modus-0-Rollback,
    muss stop_grid_charge den offenen Reset trotz verworfenem Auftrag erneut
    versuchen und erst nach dessen Quittung als sicher beendet gelten."""
    client = _make_client()
    success = MagicMock()
    success.isError.return_value = False
    setpoint_failure = MagicMock()
    setpoint_failure.isError.return_value = True
    setpoint_failure.__str__.return_value = "Setpoint-Write abgelehnt"
    rollback_failure = MagicMock()
    rollback_failure.isError.return_value = True
    rollback_failure.__str__.return_value = "Rollback-Write abgelehnt"
    client.write_register = AsyncMock(
        side_effect=[success, setpoint_failure, rollback_failure, success]
    )
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_max_power_reference": 4600,
    }

    with pytest.raises(HomeAssistantError, match="Rücksetzauftrag bleibt aktiv"):
        await coordinator.async_start_grid_charge(-1500)

    assert coordinator.grid_charge_active is False
    assert coordinator.sun_charge_active is False
    assert coordinator._sun_charge_reset_required is True

    await coordinator.async_stop_grid_charge()

    assert coordinator._sun_charge_reset_required is False
    assert coordinator._sun_charge_commanded_mode == SUN_IC_CONTROL_MODE_SMARTMETER
    assert client.write_register.await_args_list == [
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        ),
        call(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=to_unsigned16(-3261),
            device_id=100,
        ),
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        ),
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        ),
    ]


async def test_manual_grid_charge_stop_leaves_running_automation_untouched(
    hass,
) -> None:
    """Ohne manuellen Auftrag ist ein offener Reset der Besitznachweis des
    tatsächlich laufenden gemeinsamen Writers und darf ihn nicht stoppen."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(5)
    coordinator._timed_charge_armed = True

    try:
        with _patched_now(2):
            await coordinator._async_enforce_grid_charge(coordinator.data)
        task = coordinator._sun_charge_task
        assert task is not None
        assert coordinator.grid_charge_active is False
        assert coordinator._sun_charge_reset_required is True
        client.write_register.reset_mock()

        await coordinator.async_stop_grid_charge()

        assert coordinator._sun_charge_task is task
        assert task.done() is False
        assert coordinator._timed_charge_active is True
        client.write_register.assert_not_awaited()
    finally:
        coordinator._timed_charge_enabled = False
        await coordinator.async_shutdown()


async def test_manual_grid_charge_uses_sunspec_and_updates_immediately(hass) -> None:
    """REQ-MANUAL-GRID-CHARGE: Start und Änderung nutzen ausschließlich
    40051/40049; ein neuer Sollwert wartet nicht auf den periodischen Takt."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }

    try:
        await coordinator.async_start_grid_charge(-1000)

        assert coordinator.grid_charge_active is True
        assert coordinator.sun_charge_active is True
        assert client.write_register.await_args_list == [
            call(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SETPOINT,
                device_id=100,
            ),
            call(
                address=REG_SUN_IC_POWER_SETPOINT_PCT,
                value=to_unsigned16(-2174),
                device_id=100,
            ),
        ]

        client.write_register.reset_mock()
        await coordinator.async_start_grid_charge(-2000)

        assert coordinator._sun_charge_power == -2000
        assert client.write_register.await_args_list == [
            call(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SETPOINT,
                device_id=100,
            ),
            call(
                address=REG_SUN_IC_POWER_SETPOINT_PCT,
                value=to_unsigned16(-4348),
                device_id=100,
            ),
        ]
    finally:
        await coordinator.async_stop_grid_charge()


async def test_manual_grid_charge_yields_to_max_soc(hass) -> None:
    """REQ-MANUAL-GRID-CHARGE: Max-SOC schreibt 0 %, obwohl ein negativer
    manueller Ladeauftrag gespeichert bleibt."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator._max_soc = 50
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }

    try:
        await coordinator.async_start_grid_charge(-1500)

        assert coordinator.grid_charge_active is True
        assert coordinator.max_soc_clamped is True
        assert coordinator._sun_charge_power == 0
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=0,
            device_id=100,
        )
    finally:
        await coordinator.async_shutdown()


async def test_manual_grid_charge_takes_priority_then_releases_automation(hass) -> None:
    """REQ-MANUAL-GRID-CHARGE: Manuell gewinnt vor zeitgesteuert; Stop setzt
    zuerst Modus 0 und gibt danach die zentrale Automatik wieder frei."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(5)
    coordinator._timed_charge_armed = True

    try:
        with _patched_now(2):
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._sun_charge_power == MIN_SETPOINT_POWER
            assert coordinator._timed_charge_active is True

            await coordinator.async_start_grid_charge(-1500)
            assert coordinator._sun_charge_power == -1500
            assert coordinator._timed_charge_active is False

            client.write_register.reset_mock()
            await coordinator.async_stop_grid_charge()

        assert coordinator.grid_charge_active is False
        assert coordinator._sun_charge_power == MIN_SETPOINT_POWER
        assert coordinator._timed_charge_active is True
        assert client.write_register.await_args_list == [
            call(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SMARTMETER,
                device_id=100,
            ),
            call(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SETPOINT,
                device_id=100,
            ),
            call(
                address=REG_SUN_IC_POWER_SETPOINT_PCT,
                value=to_unsigned16(-10000),
                device_id=100,
            ),
        ]
    finally:
        coordinator._timed_charge_enabled = False
        await coordinator.async_shutdown()


async def test_manual_grid_charge_stop_awaits_cancellation_before_reset(hass) -> None:
    """REQ-MANUAL-GRID-CHARGE: Auch ein Task im Schreibabschnitt ist vor
    dem bestätigten Stop beendet; erst danach kann Register 40051 = 0 folgen."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    await coordinator.async_start_grid_charge(-1500)
    await coordinator._async_cancel_sun_charge_task()
    writer_started = asyncio.Event()
    writer_finished = asyncio.Event()

    async def blocked_writer() -> None:
        try:
            async with coordinator._sun_charge_write_lock:
                writer_started.set()
                await asyncio.Future()
        finally:
            writer_finished.set()

    task = asyncio.create_task(blocked_writer())
    coordinator._sun_charge_task = task
    await writer_started.wait()
    client.write_register.reset_mock()

    await coordinator.async_stop_grid_charge()

    assert task.done()
    assert writer_finished.is_set()
    assert coordinator._sun_charge_task is None
    assert coordinator.grid_charge_active is False
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_manual_grid_charge_shutdown_stops_shared_writer(hass) -> None:
    """REQ-MANUAL-GRID-CHARGE: Unload wartet den gemeinsamen Writer ab und
    hinterlässt weder manuellen Auftrag noch schreibenden Hintergrundtask."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "smartmeter_power": 0,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    await coordinator.async_start_grid_charge(-1500)
    task = coordinator._sun_charge_task
    assert task is not None
    client.write_register.reset_mock()

    await coordinator.async_shutdown()

    assert task.done()
    assert coordinator._sun_charge_task is None
    assert coordinator.grid_charge_active is False
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_active_sun_charge_immediately_repairs_observed_mode_change(hass) -> None:
    """Liest der Coordinator trotz laufendem Schreib-Task wieder Modus 0,
    muss er 40051/40049 sofort erneut setzen statt bis zum periodischen
    Schreibintervall zu warten. Das deckt Geräte- und externe Schreibvorgänge
    auf denselben Registern ab."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }

    try:
        await coordinator.async_start_sun_charge(0)
        client.write_register.reset_mock()
        coordinator._last_observed_ic_control_mode = SUN_IC_CONTROL_MODE_SMARTMETER

        await coordinator.async_start_sun_charge(0)

        assert [call.kwargs for call in client.write_register.await_args_list] == [
            {
                "address": REG_SUN_IC_CONTROL_MODE,
                "value": SUN_IC_CONTROL_MODE_SETPOINT,
                "device_id": 100,
            },
            {
                "address": REG_SUN_IC_POWER_SETPOINT_PCT,
                "value": 0,
                "device_id": 100,
            },
        ]
    finally:
        await coordinator.async_stop_sun_charge()


@pytest.mark.parametrize("reference", [None, 0])
async def test_sun_charge_rejects_missing_or_zero_reference_before_write(
    hass, reference: int | None
) -> None:
    """REQ-TIMED-SOC-CHARGE: Register 40053 wird vor Modus 1 validiert."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"ic_max_power_reference": reference}

    with pytest.raises(HomeAssistantError, match="Referenzwert Maximalleistung"):
        await coordinator.async_start_sun_charge(0)

    client.write_register.assert_not_awaited()
    assert coordinator._sun_charge_task is None
    assert coordinator.sun_charge_active is False
    assert coordinator._sun_charge_reset_required is False


@pytest.mark.parametrize(
    "power", [True, 1.5, MIN_SETPOINT_POWER - 1, 1, MAX_SETPOINT_POWER + 1]
)
async def test_sun_charge_rejects_invalid_power_before_write(
    hass, power: object
) -> None:
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"ic_max_power_reference": 4600}

    with pytest.raises(HomeAssistantError, match="power muss zwischen"):
        await coordinator.async_start_sun_charge(power)  # type: ignore[arg-type]

    client.write_register.assert_not_awaited()


@pytest.mark.parametrize("scale_factor_raw", [to_unsigned16(-32768), to_unsigned16(-3)])
async def test_sun_charge_rejects_invalid_scale_or_encoded_raw_before_write(
    hass, scale_factor_raw: int
) -> None:
    """Ungültiges sunssf und ein nicht darstellbarer int16-Rohwert schreiben nie."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"ic_max_power_reference": 4600}
    coordinator._ic_power_setpoint_sf_raw = scale_factor_raw

    with pytest.raises(HomeAssistantError):
        await coordinator.async_start_sun_charge(-3000)

    client.write_register.assert_not_awaited()
    assert coordinator._sun_charge_task is None
    assert coordinator._sun_charge_reset_required is False


async def test_sun_charge_mode_write_failure_does_not_publish_task(hass) -> None:
    """Ohne quittierten Modus 1 folgen weder Sollwert noch Rollback."""
    client = _make_client()
    failure = MagicMock()
    failure.isError.return_value = True
    failure.__str__.return_value = "Mode-Write abgelehnt"
    client.write_register = AsyncMock(return_value=failure)
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"ic_max_power_reference": 4600}

    with pytest.raises(HomeAssistantError, match="Register 40051.*abgebrochen"):
        await coordinator.async_start_sun_charge(0)

    assert client.write_register.await_args_list == [
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        )
    ]
    assert coordinator._sun_charge_task is None
    assert coordinator.sun_charge_active is False
    assert coordinator._sun_charge_reset_required is False


async def test_sun_charge_setpoint_failure_rolls_mode_back_immediately(
    hass, caplog
) -> None:
    """Ein Fehler auf 40049 wird in derselben Sequenz mit 40051=0 gerollt."""
    client = _make_client()
    success = MagicMock()
    success.isError.return_value = False
    failure = MagicMock()
    failure.isError.return_value = True
    failure.__str__.return_value = "Setpoint-Write abgelehnt"
    client.write_register = AsyncMock(side_effect=[success, failure, success])
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"ic_max_power_reference": 4600}

    with pytest.raises(HomeAssistantError, match="Rollback.*erfolgreich"):
        await coordinator.async_start_sun_charge(0)

    assert client.write_register.await_args_list == [
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        ),
        call(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=0,
            device_id=100,
        ),
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        ),
    ]
    assert "Setpoint-Write abgelehnt" in caplog.text
    assert "Rollback über Register 40051" in caplog.text
    assert "SmartMeter-Nullregelung erfolgreich" in caplog.text
    assert coordinator._sun_charge_task is None
    assert coordinator.sun_charge_active is False
    assert coordinator._sun_charge_reset_required is False
    assert coordinator._sun_charge_commanded_mode == SUN_IC_CONTROL_MODE_SMARTMETER


async def test_failed_sun_charge_rollback_stays_pending_until_next_reset(
    hass, caplog
) -> None:
    """Ein gescheiterter 40051=0-Rollback wird beim nächsten Stop wiederholt."""
    client = _make_client()
    success = MagicMock()
    success.isError.return_value = False
    setpoint_failure = MagicMock()
    setpoint_failure.isError.return_value = True
    setpoint_failure.__str__.return_value = "Setpoint-Write abgelehnt"
    rollback_failure = MagicMock()
    rollback_failure.isError.return_value = True
    rollback_failure.__str__.return_value = "Rollback-Write abgelehnt"
    client.write_register = AsyncMock(
        side_effect=[success, setpoint_failure, rollback_failure, success]
    )
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"ic_max_power_reference": 4600}

    with pytest.raises(HomeAssistantError, match="Rücksetzauftrag bleibt aktiv"):
        await coordinator.async_start_sun_charge(0)

    assert coordinator._sun_charge_task is None
    assert coordinator._sun_charge_reset_required is True
    assert coordinator._sun_charge_commanded_mode == SUN_IC_CONTROL_MODE_SETPOINT
    assert "Rollback-Write abgelehnt" in caplog.text

    await coordinator.async_stop_sun_charge()

    assert coordinator._sun_charge_reset_required is False
    assert coordinator._sun_charge_commanded_mode == SUN_IC_CONTROL_MODE_SMARTMETER
    written_addresses = [
        write.kwargs["address"] for write in client.write_register.await_args_list
    ]
    assert written_addresses == [
        REG_SUN_IC_CONTROL_MODE,
        REG_SUN_IC_POWER_SETPOINT_PCT,
        REG_SUN_IC_CONTROL_MODE,
        REG_SUN_IC_CONTROL_MODE,
    ]


async def test_failed_immediate_setpoint_change_rolls_back_and_stops_task(hass) -> None:
    """Auch die Sofortänderung eines laufenden Tasks ist atomar abgesichert."""
    client = _make_client()
    success = MagicMock()
    success.isError.return_value = False
    failure = MagicMock()
    failure.isError.return_value = True
    failure.__str__.return_value = "Setpoint-Write abgelehnt"
    client.write_register = AsyncMock(return_value=success)
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_start_sun_charge(0)
    coordinator._timed_charge_active = True
    client.write_register.reset_mock()
    client.write_register.side_effect = [success, failure, success]

    with pytest.raises(HomeAssistantError, match="Rollback.*erfolgreich"):
        await coordinator.async_start_sun_charge(-1000)

    written_addresses = [
        write.kwargs["address"] for write in client.write_register.await_args_list
    ]
    assert written_addresses == [
        REG_SUN_IC_CONTROL_MODE,
        REG_SUN_IC_POWER_SETPOINT_PCT,
        REG_SUN_IC_CONTROL_MODE,
    ]
    assert coordinator._sun_charge_power == 0
    assert coordinator._sun_charge_task is None
    assert coordinator.sun_charge_active is False
    assert coordinator._sun_charge_reset_required is False
    assert coordinator._timed_charge_active is False


async def test_sun_charge_sequences_cannot_interleave(hass) -> None:
    """Periodischer und sofortiger Pfad serialisieren jeweils beide Register."""
    client = _make_client()
    success = MagicMock()
    success.isError.return_value = False
    first_write_started = asyncio.Event()
    release_first_write = asyncio.Event()

    async def delayed_first_write(**_kwargs):
        if not first_write_started.is_set():
            first_write_started.set()
            await release_first_write.wait()
        return success

    client.write_register = AsyncMock(side_effect=delayed_first_write)
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"ic_max_power_reference": 4600}

    first_sequence = asyncio.create_task(
        coordinator._async_write_sun_charge_setpoint(0)
    )
    await first_write_started.wait()
    second_sequence = asyncio.create_task(
        coordinator._async_write_sun_charge_setpoint(-1000)
    )
    await asyncio.sleep(0)

    assert client.write_register.await_count == 1
    release_first_write.set()
    await asyncio.gather(first_sequence, second_sequence)

    written_addresses = [
        write.kwargs["address"] for write in client.write_register.await_args_list
    ]
    assert written_addresses == [
        REG_SUN_IC_CONTROL_MODE,
        REG_SUN_IC_POWER_SETPOINT_PCT,
        REG_SUN_IC_CONTROL_MODE,
        REG_SUN_IC_POWER_SETPOINT_PCT,
    ]


async def test_stop_sun_charge_retries_failed_smartmeter_reset(hass) -> None:
    """REQ-GRID-SERVING-CHARGE: Ein transient fehlgeschlagenes Rücksetzen
    darf den Besitznachweis nicht löschen; der nächste Aufruf schreibt
    Register 40051 erneut auf SmartMeter-Nullregelung."""
    client = _make_client()
    success = MagicMock()
    success.isError.return_value = False
    failure = MagicMock()
    failure.isError.return_value = True
    client.write_register = AsyncMock(return_value=success)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    await coordinator.async_start_sun_charge(0)
    await asyncio.sleep(0.1)
    client.write_register.reset_mock()
    client.write_register.side_effect = [failure, success]

    await coordinator.async_stop_sun_charge()

    assert coordinator._sun_charge_task is None
    assert coordinator._sun_charge_reset_required is True
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )

    await coordinator.async_stop_sun_charge()

    assert coordinator._sun_charge_reset_required is False
    assert client.write_register.await_count == 2
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_real_smartmeter_readback_wins_when_reset_acknowledgement_fails(
    hass,
) -> None:
    """REQ-GRID-SERVING-CHARGE: Wirkt Register 40051 = 0 bereits am Gerät,
    obwohl die Modbus-Schreibantwort als Fehler zurückkommt, muss der nächste
    echte Readback die HA-Anzeige auf Nullregelung setzen. Der alte zuletzt
    quittierte Befehl Modus 1 darf den gelesenen Wert nicht überschreiben."""
    client = _make_client()
    failure = MagicMock()
    failure.isError.return_value = True
    client.write_register = AsyncMock(return_value=failure)

    coordinator = _make_coordinator(hass, client)
    coordinator._sun_charge_commanded_mode = SUN_IC_CONTROL_MODE_SETPOINT
    coordinator._last_observed_ic_control_mode = SUN_IC_CONTROL_MODE_SETPOINT
    data = {
        "soc": 50,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_control_mode_text": "SmartMeter-Nullregelung",
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }
    coordinator.data = data

    await coordinator._async_enforce_grid_charge(data)

    assert data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SMARTMETER
    assert data["ic_control_mode_text"] == "SmartMeter-Nullregelung"
    assert coordinator._sun_charge_commanded_mode == SUN_IC_CONTROL_MODE_SETPOINT
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_inactive_grid_serving_retries_failed_smartmeter_reset(hass) -> None:
    """Ein inaktiver Folgetakt wiederholt das zuvor fehlgeschlagene
    Rücksetzen automatisch, obwohl der Schreib-Task bereits entfernt ist."""
    client = _make_client()
    success = MagicMock()
    success.isError.return_value = False
    failure = MagicMock()
    failure.isError.return_value = True
    client.write_register = AsyncMock(return_value=success)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300),
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10))
    await coordinator.async_set_grid_serving_end(dt_time(14))
    await coordinator.async_set_max_soc(90)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator.grid_serving_active is True

            client.write_register.reset_mock()
            client.write_register.side_effect = [failure, success]
            await coordinator.async_set_grid_serving_enabled(False)

            assert coordinator.grid_serving_active is False
            assert coordinator._sun_charge_task is None
            assert coordinator._sun_charge_reset_required is True

            await coordinator._async_enforce_grid_charge(coordinator.data)

        assert coordinator._sun_charge_reset_required is False
        assert client.write_register.await_count == 2
        for write in client.write_register.await_args_list:
            assert write.kwargs == {
                "address": REG_SUN_IC_CONTROL_MODE,
                "value": SUN_IC_CONTROL_MODE_SMARTMETER,
                "device_id": 100,
            }
    finally:
        await coordinator.async_stop_sun_charge()


async def test_inactive_fresh_coordinator_resets_observed_orphaned_setpoint_mode(
    hass,
) -> None:
    """REQ-GRID-SERVING-CHARGE: Nach Reload oder Neuinstallation existiert
    kein Python-Task mehr, Register 40051 kann aber bis zum 300-s-Timeout der
    vorherigen Instanz auf Sollwertvorgabe stehen. Der gelesene Gerätemodus
    muss den Rücksprung in die SmartMeter-Nullregelung auslösen."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SETPOINT,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }

    await coordinator._async_enforce_grid_charge(coordinator.data)

    assert coordinator.sun_charge_active is False
    assert coordinator._sun_charge_reset_required is False
    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_inactive_fresh_coordinator_explicitly_confirms_smartmeter_mode(
    hass,
) -> None:
    """REQ-GRID-SERVING-CHARGE: Auch wenn der erste Read bereits Modus 0
    meldet, wird der inaktive Sollzustand beim Start einmal ausdrücklich
    geschrieben. Folgetakte dürfen denselben Wert nicht fortlaufend senden."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_control_mode": SUN_IC_CONTROL_MODE_SMARTMETER,
        "ic_control_mode_text": "SmartMeter-Nullregelung",
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
    }

    await coordinator._async_enforce_grid_charge(coordinator.data)

    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )

    client.write_register.reset_mock()
    await coordinator._async_enforce_grid_charge(coordinator.data)
    client.write_register.assert_not_awaited()


async def test_enforce_grid_charge_inactive_outside_window(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)  # Ziel-SOC = "Max. SOC"
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
    # timed_charge_enabled bleibt False (Default)

    with _patched_now(2):
        await coordinator._async_enforce_grid_charge({"soc": 10})

    assert coordinator._timed_charge_active is False
    assert coordinator.sun_charge_active is False


async def test_enforce_grid_charge_inactive_without_min_soc(hass) -> None:
    """Ohne gesetztes "Netzladung Min. SOC" darf zeitgesteuertes Laden nicht
    starten - siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator._timed_charge_min_soc = None  # explizit ungesetzt
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)
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


async def test_enforce_grid_charge_max_soc_clamp_holds_on_single_grid_import_cycle(
    hass,
) -> None:
    """Netzbezug über der Schwelle in nur einem Zyklus reicht nicht - die
    Hysterese (2 Zyklen) hält die geräteunabhängige Max-SOC-Sperre weiter
    aktiv, siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 85, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_max_soc(80)

    try:
        await coordinator._async_enforce_grid_charge(
            {
                "soc": 85,
                # Vorzeichenkonvention: positiv = Netzbezug (siehe const.py).
                "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50,
            }
        )
        await asyncio.sleep(0.1)

        assert coordinator.max_soc_clamped is True
        assert coordinator.sun_charge_active is True
        assert coordinator._max_soc_grid_import_wait_cycles == 1
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_max_soc_clamp_releases_after_two_grid_import_cycles(
    hass,
) -> None:
    """Netzbezug über SMARTMETER_PV_SURPLUS_THRESHOLD_WATT über zwei
    aufeinanderfolgende Zyklen hebt die geräteunabhängige Max-SOC-Sperre
    aktiv auf (Register 40051 zurück auf SmartMeter-Nullregelung). Fünf
    weitere Polls bei unverändertem SOC dürfen die Sperre nicht erneut
    aktivieren - siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_max_soc(80)

    grid_import_data = {
        "soc": 85,
        # Vorzeichenkonvention: positiv = Netzbezug (siehe const.py).
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50,
    }
    try:
        clamped_states = []
        for _ in range(7):
            await coordinator._async_enforce_grid_charge(grid_import_data)
            clamped_states.append(coordinator.max_soc_clamped)

        assert clamped_states == [True, False, False, False, False, False, False]
        assert coordinator.max_soc_clamped is False
        assert coordinator.sun_charge_active is False
        assert coordinator._max_soc_grid_import_wait_cycles == 0
        assert coordinator._max_soc_released_for_discharge is True
        assert client.write_register.await_args_list == [
            call(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SETPOINT,
                device_id=100,
            ),
            call(
                address=REG_SUN_IC_POWER_SETPOINT_PCT,
                value=0,
                device_id=100,
            ),
            call(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SMARTMETER,
                device_id=100,
            ),
        ]
    finally:
        await coordinator.async_stop_sun_charge()


async def test_max_soc_release_latch_resets_below_target_and_clamps_again(hass) -> None:
    """Nach echter SOC-Unterschreitung ist eine spätere Überschreitung neu."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_max_soc(80)
    grid_import_data = {
        "soc": 85,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50,
    }

    try:
        for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES):
            await coordinator._async_enforce_grid_charge(grid_import_data)
        assert coordinator._max_soc_released_for_discharge is True

        client.write_register.reset_mock()
        await coordinator._async_enforce_grid_charge({"soc": 79, "smartmeter_power": 0})
        assert coordinator._max_soc_released_for_discharge is False
        assert coordinator.max_soc_clamped is False

        await coordinator._async_enforce_grid_charge({"soc": 81, "smartmeter_power": 0})
        assert coordinator.max_soc_clamped is True
        assert coordinator.sun_charge_active is True
        assert client.write_register.await_args_list == [
            call(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SETPOINT,
                device_id=100,
            ),
            call(
                address=REG_SUN_IC_POWER_SETPOINT_PCT,
                value=0,
                device_id=100,
            ),
        ]
    finally:
        await coordinator.async_stop_sun_charge()


async def test_max_soc_release_latch_handles_target_raise_and_lower(hass) -> None:
    """Eine Zielerhöhung behält die Freigabe, eine Absenkung widerruft sie."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_max_soc(80)
    coordinator.data = {
        "soc": 95,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50,
    }

    try:
        for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES):
            await coordinator._async_enforce_grid_charge(coordinator.data)
        assert coordinator._max_soc_released_for_discharge is True

        client.write_register.reset_mock()
        await coordinator.async_set_max_soc(90)
        assert coordinator._max_soc_released_for_discharge is True
        assert coordinator.max_soc_clamped is False
        client.write_register.assert_not_awaited()

        await coordinator.async_set_max_soc(85)
        assert coordinator._max_soc_released_for_discharge is False
        assert coordinator.max_soc_clamped is True
        assert client.write_register.await_args_list == [
            call(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SETPOINT,
                device_id=100,
            ),
            call(
                address=REG_SUN_IC_POWER_SETPOINT_PCT,
                value=0,
                device_id=100,
            ),
        ]
    finally:
        await coordinator.async_stop_sun_charge()


async def test_max_soc_release_latch_waits_for_successful_mode_reset(hass) -> None:
    """Ein fehlgeschlagener Modus-0-Write darf keine Freigabe vortäuschen."""
    client = _make_client()
    success = MagicMock()
    success.isError.return_value = False
    failure = MagicMock()
    failure.isError.return_value = True
    client.write_register = AsyncMock(side_effect=[success, success, failure, success])
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_max_soc(80)
    grid_import_data = {
        "soc": 85,
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50,
    }

    await coordinator._async_enforce_grid_charge(grid_import_data)
    await coordinator._async_enforce_grid_charge(grid_import_data)

    assert coordinator._max_soc_released_for_discharge is False
    assert coordinator.max_soc_clamped is True
    assert coordinator._sun_charge_reset_required is True

    await coordinator._async_enforce_grid_charge(grid_import_data)

    assert coordinator._max_soc_released_for_discharge is True
    assert coordinator.max_soc_clamped is False
    assert coordinator._sun_charge_reset_required is False
    assert client.write_register.await_args_list == [
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        ),
        call(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=0,
            device_id=100,
        ),
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        ),
        call(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        ),
    ]


async def test_enforce_grid_charge_max_soc_clamp_resets_grid_import_counter(
    hass,
) -> None:
    """Fällt der gemessene Netzbezug zwischen zwei Zyklen wieder unter die
    Schwelle, wird der Hysterese-Zähler zurückgesetzt statt weiterzuzählen -
    die Sperre bleibt bestehen, bis erneut zwei aufeinanderfolgende Zyklen
    mit ausreichend Netzbezug gemessen werden."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 85, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_max_soc(80)

    grid_import_data = {
        "soc": 85,
        # Vorzeichenkonvention: positiv = Netzbezug (siehe const.py).
        "smartmeter_power": SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50,
    }
    no_import_data = {"soc": 85, "smartmeter_power": 0}

    try:
        await coordinator._async_enforce_grid_charge(grid_import_data)
        await asyncio.sleep(0.1)
        assert coordinator._max_soc_grid_import_wait_cycles == 1

        await coordinator._async_enforce_grid_charge(no_import_data)
        await asyncio.sleep(0.1)
        assert coordinator._max_soc_grid_import_wait_cycles == 0
        assert coordinator.max_soc_clamped is True

        await coordinator._async_enforce_grid_charge(grid_import_data)
        await asyncio.sleep(0.1)
        assert coordinator._max_soc_grid_import_wait_cycles == 1
        assert coordinator.max_soc_clamped is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_max_soc_clamp_ignores_missing_smartmeter_power(
    hass,
) -> None:
    """Fehlt data["smartmeter_power"] (z. B. SunSpec-Modus nicht erreichbar),
    bleibt die geräteunabhängige Max-SOC-Sperre unverändert unbegrenzt
    bestehen - kein Freigabe-Trigger ohne Messwert."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 85, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_max_soc(80)

    try:
        for _ in range(3):
            await coordinator._async_enforce_grid_charge({"soc": 85})
            await asyncio.sleep(0.1)

        assert coordinator.max_soc_clamped is True
        assert coordinator.sun_charge_active is True
        assert coordinator._max_soc_grid_import_wait_cycles == 0
    finally:
        await coordinator.async_stop_sun_charge()


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
    await coordinator.async_set_timed_charge_enabled(True)

    try:
        with _patched_now(2):
            await coordinator._async_enforce_grid_charge({"soc": 90})
        await asyncio.sleep(0.1)

        assert coordinator.max_soc_clamped is True
        assert coordinator.sun_charge_active is True
        assert coordinator._max_soc_hold_is_window_bound is True
        assert coordinator._max_soc_released_for_discharge is False
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
        assert coordinator._max_soc_released_for_discharge is False
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
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT gemessen wird (negativer
    Anzeigewert = Überschuss aus der Dachphotovoltaik) - siehe
    anforderung.yaml, REQ-TIMED-SOC-CHARGE."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.data = {
        "soc": 10,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_max_soc(90)

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
    übernächsten Poll-Zyklus (Zyklen-Hysterese, PV_SURPLUS_HYSTERESIS_CYCLES),
    nicht erst am konfigurierten Fensterende."""
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

    try:
        with _patched_now(2):
            await coordinator.async_set_timed_charge_enabled(True)
            await asyncio.sleep(0.1)
            assert coordinator.sun_charge_active is True

            # Simuliert den nächsten Poll-Zyklus (_async_update_data), bei
            # dem der Smart Meter nun PV-Überschuss über dem Schwellwert
            # meldet. Ein einzelner Zyklus reicht wegen der Hysterese noch
            # nicht, um die Netzladung zu beenden.
            coordinator.data["smartmeter_power"] = -(
                SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50
            )
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)

            assert coordinator._timed_charge_active is True
            assert coordinator.sun_charge_active is True

            # Erst der zweite aufeinanderfolgende Zyklus mit PV-Überschuss
            # über dem Schwellwert bestätigt die Hysterese und beendet die
            # Netzladung.
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


async def test_enforce_grid_charge_pv_surplus_hysteresis_resets_on_drop(
    hass,
) -> None:
    """Fällt der PV-Überschuss zwischen zwei Zyklen wieder auf/unter den
    Schwellwert, wird der Hysterese-Zähler zurückgesetzt statt weiterzuzählen
    - die Netzladung läuft weiter, bis erneut zwei aufeinanderfolgende Zyklen
    mit Überschuss über dem Schwellwert gemessen werden."""
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

    try:
        with _patched_now(2):
            await coordinator.async_set_timed_charge_enabled(True)
            await asyncio.sleep(0.1)

            coordinator.data["smartmeter_power"] = -(
                SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50
            )
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator._timed_charge_pv_surplus_cycles == 1

            coordinator.data["smartmeter_power"] = 0
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator._timed_charge_pv_surplus_cycles == 0
            assert coordinator._timed_charge_active is True
            assert coordinator.sun_charge_active is True
    finally:
        await coordinator.async_stop_sun_charge()


@pytest.mark.parametrize(
    "smartmeter_power",
    [
        -SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,  # genau auf dem Schwellwert (nicht <)
        0,
        500,  # Netzbezug statt PV-Überschuss
    ],
)
async def test_enforce_grid_charge_starts_at_or_below_pv_surplus_threshold(
    hass, smartmeter_power: float
) -> None:
    """Der Schwellwert greift erst bei Unterschreitung (<) - ein Wert genau
    auf dem Schwellwert sowie Netzbezug (positiver Anzeigewert) blockieren
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

    try:
        with _patched_now(2):
            await coordinator.async_set_timed_charge_enabled(True)
            await asyncio.sleep(0.1)

            assert coordinator._timed_charge_active is True
            assert coordinator.sun_charge_active is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_stop_sun_charge_initially_reconciles_then_is_noop(hass) -> None:
    """REQ-GRID-SERVING-CHARGE: Eine neue Coordinator-Instanz darf aus dem
    fehlenden Python-Task nicht auf den Gerätezustand schließen. Die erste
    inaktive Entscheidung schreibt Modus 0 genau einmal; danach ist derselbe
    Sollzustand ein No-Op und der HA-Cache zeigt die Quittung sofort."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "ic_control_mode": SUN_IC_CONTROL_MODE_SETPOINT,
        "ic_control_mode_text": "Sollwertvorgabe",
    }
    coordinator._high_data = dict(coordinator.data)
    coordinator._high_last_read = 123.0
    coordinator._last_observed_ic_control_mode = SUN_IC_CONTROL_MODE_SETPOINT

    await coordinator.async_stop_sun_charge()

    client.write_register.assert_awaited_once_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )
    assert coordinator._sun_charge_commanded_mode == SUN_IC_CONTROL_MODE_SMARTMETER
    assert coordinator.data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SMARTMETER
    assert coordinator.data["ic_control_mode_text"] == "SmartMeter-Nullregelung"
    assert coordinator._high_data["ic_control_mode"] == SUN_IC_CONTROL_MODE_SMARTMETER
    assert coordinator._high_last_read is None

    client.write_register.reset_mock()
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
    assert coordinator._is_time_in_window(dt_time(12, 0), None, dt_time(14, 0)) is False
    assert coordinator._is_time_in_window(dt_time(12, 0), dt_time(10, 0), None) is False
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
    SmartMeter-Nullregelung) so viele Zyklen in Folge wie
    PV_SURPLUS_HYSTERESIS_CYCLES bereits mit mindestens
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT lädt (negativer Anteil von
    data["storage_power_active"]), übernimmt netzdienliches Laden aktiv die
    Kontrolle: Wechsel in den Sollwertvorgabemodus UND Ladung sofort auf
    0 % gestoppt, in einem Aufruf (async_start_sun_charge(0)), danach
    zusätzlich zweimal warten (_grid_serving_wait_cycles). Ein einzelner
    Zyklus reicht wegen der Hysterese noch nicht aus."""
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

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            await asyncio.sleep(0.1)

            assert coordinator.grid_serving_active is False
            assert coordinator.sun_charge_active is False
            assert coordinator._grid_serving_charge_confirm_cycles == 1

            await coordinator._async_enforce_grid_charge(coordinator.data)
        await asyncio.sleep(0.1)

        assert coordinator.grid_serving_active is True
        assert coordinator._timed_charge_active is False
        assert coordinator.sun_charge_active is True
        assert coordinator._grid_serving_wait_cycles == PV_SURPLUS_HYSTERESIS_CYCLES
        assert coordinator._grid_serving_charge_confirm_cycles == 0
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


@pytest.mark.parametrize("deactivation", ["switch", "month", "window", "forecast"])
async def test_grid_serving_deactivation_restores_smartmeter_after_task_stopped(
    hass, deactivation: str
) -> None:
    """REQ-GRID-SERVING-CHARGE: Verliert eine laufende Ladepause durch
    Schalter, Monat oder Zeitfenster ihre Berechtigung, muss Register 40051
    auch dann aktiv auf Nullregelung wechseln, wenn der periodische
    Schreib-Task bereits beendet ist."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300),
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10))
    await coordinator.async_set_grid_serving_end(dt_time(14))
    await coordinator.async_set_max_soc(90)

    try:
        with _patched_now(12, month=1):
            await coordinator.async_set_grid_serving_enabled(True)
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator.grid_serving_active is True

            task = coordinator._sun_charge_task
            assert task is not None
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert coordinator.sun_charge_active is False
            client.write_register.reset_mock()

            if deactivation == "switch":
                await coordinator.async_set_grid_serving_enabled(False)
            elif deactivation == "month":
                await coordinator.async_set_grid_serving_month(1, False)
            elif deactivation == "window":
                await coordinator.async_set_grid_serving_window(
                    dt_time(14), dt_time(16)
                )
            else:
                hass.states.async_set(
                    "sensor.pv_prognose_morgen",
                    "4",
                    {"unit_of_measurement": "kWh"},
                )
                coordinator.options = {
                    CONF_PV_FORECAST_SENSOR: "sensor.pv_prognose_morgen"
                }
                await coordinator.async_set_grid_serving_forecast_threshold_kwh(8)

        assert coordinator.grid_serving_active is False
        assert coordinator._grid_serving_setpoint_active is False
        assert coordinator.sun_charge_active is False
        client.write_register.assert_awaited_once_with(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_grid_serving_deactivation_wins_over_concurrent_activation(hass) -> None:
    """REQ-GRID-SERVING-CHARGE: Eine bereits laufende Poll-Auswertung darf
    die SunSpec-Sollwertvorgabe nicht nach einer neueren Deaktivierung wieder
    einschalten. Status und Register 40051 müssen dieselbe Entscheidung
    abbilden."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300),
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    coordinator._grid_serving_enabled = True
    coordinator._grid_serving_start = dt_time(10)
    coordinator._grid_serving_end = dt_time(14)
    coordinator._max_soc = 90

    start_entered = asyncio.Event()
    allow_start = asyncio.Event()
    original_start = coordinator.async_start_sun_charge

    async def delayed_start(power: int) -> None:
        start_entered.set()
        await allow_start.wait()
        await original_start(power)

    try:
        with (
            _patched_now(12),
            patch.object(coordinator, "async_start_sun_charge", delayed_start),
        ):
            # Erster Zyklus füllt nur die Hysterese; der zweite will die
            # Ladepause einschalten und wird direkt vor dem Registerpfad
            # kontrolliert angehalten.
            await coordinator._async_enforce_grid_charge(coordinator.data)
            activation = asyncio.create_task(
                coordinator._async_enforce_grid_charge(coordinator.data)
            )
            await start_entered.wait()

            deactivation = asyncio.create_task(
                coordinator.async_set_grid_serving_enabled(False)
            )
            await asyncio.sleep(0)
            allow_start.set()
            await asyncio.gather(activation, deactivation)
            await asyncio.sleep(0.1)

        assert coordinator.grid_serving_enabled is False
        assert coordinator.grid_serving_active is False
        assert coordinator.data["grid_serving_pause_status"] == "Inaktiv"
        assert coordinator.sun_charge_active is False
        assert client.write_register.await_args_list[-1].kwargs == {
            "address": REG_SUN_IC_CONTROL_MODE,
            "value": SUN_IC_CONTROL_MODE_SMARTMETER,
            "device_id": 100,
        }
    finally:
        allow_start.set()
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

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            # Schritt a braucht selbst PV_SURPLUS_HYSTERESIS_CYCLES
            # aufeinanderfolgende Zyklen mit ausreichender SAX-Ladeleistung,
            # bevor der Sollwertvorgabemodus überhaupt aktiv wird.
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator._grid_serving_setpoint_active is True
            assert coordinator._grid_serving_wait_cycles == PV_SURPLUS_HYSTERESIS_CYCLES

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

            # Erst jetzt wertet Schritt b die Netzeinspeisung wieder aus -
            # auch dort greift dieselbe Zyklen-Hysterese, ein einzelner
            # Aufruf unter dem Schwellwert reicht noch nicht.
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator.grid_serving_active is True
            assert coordinator.sun_charge_active is True

            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator.grid_serving_active is False
            assert coordinator.sun_charge_active is False
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_grid_serving_import_protection_overrides_wait_cycles(
    hass,
) -> None:
    """Schritt a.1 (Netzbezugs-Schutz): Tritt während der Wartezyklen nach
    Schritt a tatsächlicher Netzbezug (positiver smartmeter_power) über
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT für PV_SURPLUS_HYSTERESIS_CYCLES
    aufeinanderfolgende Zyklen auf, bricht das die Wartezyklen-
    Unterdrückung und schaltet sofort zurück in die SmartMeter-
    Nullregelung, damit der Speicher smartmeter-gesteuert entladen kann
    statt Netzbezug entstehen zu lassen. Ein einzelner Zyklus reicht wegen
    der Hysterese noch nicht aus. Sobald der Netzbezug wieder abklingt,
    wertet die Zustandsmaschine ab dem nächsten Zyklus wieder regulär ab
    Schritt a - bei weiterhin hoher SAX-Ladeleistung greift Schritt a nach
    erneuten PV_SURPLUS_HYSTERESIS_CYCLES Zyklen wieder ein ("ursprüngliche
    Regelung greift wieder")."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300),
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator._grid_serving_setpoint_active is True
            assert coordinator._grid_serving_wait_cycles == PV_SURPLUS_HYSTERESIS_CYCLES

            # Während der Wartezyklen entsteht tatsächlicher Netzbezug.
            coordinator.data["smartmeter_power"] = (
                SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 1
            )

            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._grid_serving_wait_cycles == 1
            assert coordinator.grid_serving_active is True
            assert coordinator.sun_charge_active is True

            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator.grid_serving_active is False
            assert coordinator.sun_charge_active is False
            assert coordinator._grid_serving_setpoint_active is False
            assert coordinator._grid_serving_wait_cycles == 0
            client.write_register.assert_awaited_with(
                address=REG_SUN_IC_CONTROL_MODE,
                value=SUN_IC_CONTROL_MODE_SMARTMETER,
                device_id=100,
            )

            # Netzbezug klingt ab - die ursprüngliche Regelung (Schritt a)
            # greift wieder, sobald der Speicher erneut über den
            # Schwellwert lädt.
            coordinator.data["smartmeter_power"] = -(
                SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300
            )
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator._grid_serving_setpoint_active is False

            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator._grid_serving_setpoint_active is True
            assert coordinator.sun_charge_active is True
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
        # Vorzeichenkonvention: negativ = Einspeisung - bleibt über den
        # gesamten Test hinweg hoch, damit Schritt b nie freigibt.
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300),
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            # Zweiter Zyklus bestätigt Schritt a (Zyklen-Hysterese) und
            # löst den Sollwertvorgabemodus tatsächlich aus.
            await coordinator._async_enforce_grid_charge(coordinator.data)
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


async def test_enforce_grid_charge_grid_serving_restarts_dead_write_task_while_holding(
    hass,
) -> None:
    """Regressionstest: Stirbt der periodische Schreib-Task
    (_sun_charge_task) unerwartet, während netzdienliches Laden aktiv den
    0-%-Sollwert hält (self._grid_serving_setpoint_active True) - z. B. weil
    ein einzelner transienter Modbus-Fehler in _async_sun_charge_loop den
    Task beendet, statt ihn zu retryen -, muss der nächste Aufruf von
    _async_enforce_grid_charge den Task neu starten, solange weder Schritt
    a.1 (Netzbezug) noch Schritt b (gefallene Einspeisung) zurückschalten.

    Ursprünglich gemeldeter Bug: Ohne den erneuten async_start_sun_charge(0)
    -Aufruf in _async_step_grid_serving (Wartezyklen- UND Halte-Zweig) blieb
    self._grid_serving_setpoint_active dauerhaft True (Sensor "Netzdienliches
    Laden aktiv" zeigte weiterhin "aktiv"), während Register 40049/40051
    nach dem toten Task nie wieder neu geschrieben wurden - das Gerät fiel
    nach seinem eigenen Timeout (Register 40050, max. 300 s) unbeaufsichtigt
    in die SmartMeter-Nullregelung zurück und begann unbemerkt wieder mit
    PV-Überschuss zu laden, obwohl netzdienliches Laden laut Software noch
    aktiv eingriff."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        # Vorzeichenkonvention: negativ = Einspeisung - bleibt hoch (kein
        # Netzbezug -> a.1 löst nicht aus, keine gefallene Einspeisung ->
        # Schritt b gibt nicht frei), der Speicher soll durchgehend
        # gehalten werden.
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300),
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)

            assert coordinator._grid_serving_setpoint_active is True
            assert coordinator.sun_charge_active is True

            # Simuliert den unkontrollierten Absturz des Schreib-Tasks
            # (dasselbe Endergebnis wie ein re-raise nach einem transienten
            # Modbus-Fehler in _async_sun_charge_loop) - OHNE über
            # async_stop_sun_charge() zu laufen, damit
            # _grid_serving_setpoint_active unverändert True bleibt.
            coordinator._sun_charge_task.cancel()
            try:
                await coordinator._sun_charge_task
            except asyncio.CancelledError:
                pass
            assert coordinator.sun_charge_active is False

            # Wartezyklen aus Schritt a sind noch nicht abgelaufen - auch
            # dieser Zweig muss selbstheilend neu starten.
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator._grid_serving_setpoint_active is True
            assert coordinator.sun_charge_active is True

            # Wartezyklen ablaufen lassen, Task erneut sterben lassen, damit
            # auch der Halte-Zweig (nach Ablauf der Wartezyklen) geprüft ist.
            for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES):
                await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator._grid_serving_wait_cycles == 0

            coordinator._sun_charge_task.cancel()
            try:
                await coordinator._sun_charge_task
            except asyncio.CancelledError:
                pass
            assert coordinator.sun_charge_active is False

            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)

        assert coordinator.grid_serving_active is True
        assert coordinator._grid_serving_setpoint_active is True
        assert coordinator.sun_charge_active is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_enforce_grid_charge_grid_serving_reverts_to_nullregelung_below_threshold(
    hass,
) -> None:
    """Schritt b: Ist der Sollwertvorgabemodus aktiv (Wartezyklen bereits
    abgelaufen) und fällt die Netzeinspeisung so viele Zyklen in Folge wie
    PV_SURPLUS_HYSTERESIS_CYCLES vorgibt unter den Schwellwert, wird der
    Speicher aktiv zurück in die SmartMeter-Nullregelung gesetzt."""
    client = _make_client()
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)

    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        # Vorzeichenkonvention: negativ = Einspeisung. Knapp unter dem
        # Schwellwert exportiert (-49 statt -50), also gerade noch im
        # Freigabebereich (> -Schwellwert).
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT - 1),
    }
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    await coordinator.async_set_max_soc(90)

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            coordinator._grid_serving_setpoint_active = True
            coordinator._grid_serving_wait_cycles = 0
            await coordinator.async_start_sun_charge(0)
            await asyncio.sleep(0.1)

            # Ein einzelner Zyklus unter dem Schwellwert reicht wegen der
            # Hysterese noch nicht aus.
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)
            assert coordinator.grid_serving_active is True
            assert coordinator.sun_charge_active is True

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


async def test_grid_serving_releases_max_soc_task_when_target_is_raised(hass) -> None:
    """REQ-GRID-SERVING-CHARGE: Wird das Max-SOC im Ladepausenfenster
    angehoben, darf dessen alter 0-%-Task nicht ohne aktiven Eigentümer
    weiterlaufen. Schritt a muss aus echter SmartMeter-Nullregelung starten."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {
        "soc": 90,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": 0,
        "storage_power_active": 0,
    }
    coordinator._grid_serving_enabled = True
    coordinator._grid_serving_start = dt_time(10)
    coordinator._grid_serving_end = dt_time(14)
    coordinator._max_soc = 90

    try:
        with _patched_now(12):
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator.max_soc_clamped is True
            assert coordinator.sun_charge_active is True

            client.write_register.reset_mock()
            await coordinator.async_set_max_soc(95)

        assert coordinator.max_soc_clamped is False
        assert coordinator.grid_serving_active is False
        assert coordinator._grid_serving_setpoint_active is False
        assert coordinator.sun_charge_active is False
        client.write_register.assert_awaited_once_with(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_grid_serving_releases_max_soc_task_when_calibration_starts(
    hass,
) -> None:
    """REQ-PERIODIC-FULL-CALIBRATION/REQ-GRID-SERVING-CHARGE: Auch das
    automatische Anheben des effektiven Max-SOC auf 100 % muss den alten
    0-%-Task freigeben, bevor die Ladepause neue SAX-Ladung erkennen kann."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    now = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    coordinator.data = {
        "soc": 80,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": 0,
        "storage_power_active": 0,
    }
    coordinator._grid_serving_enabled = True
    coordinator._grid_serving_start = dt_time(10)
    coordinator._grid_serving_end = dt_time(14)
    coordinator._max_soc = 80
    coordinator._cell_calibration_state = CalibrationState(
        now - CELL_CALIBRATION_INTERVAL,
        was_full=False,
    )

    try:
        with _patched_now(12, month=8):
            await coordinator._async_enforce_grid_charge(coordinator.data)
            assert coordinator.max_soc_clamped is True
            assert coordinator.sun_charge_active is True

            client.write_register.reset_mock()
            changed = await coordinator._async_update_cell_calibration(80, now=now)
            await coordinator._async_enforce_grid_charge(coordinator.data)

        assert changed is True
        assert coordinator.cell_calibration_active is True
        assert coordinator.effective_max_soc == MAX_SOC
        assert coordinator.max_soc_clamped is False
        assert coordinator.grid_serving_active is False
        assert coordinator._grid_serving_setpoint_active is False
        assert coordinator.sun_charge_active is False
        client.write_register.assert_awaited_once_with(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
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
    bestätigter PV-Überschuss) aktiv ist, kann netzdienliches Laden für
    denselben Zyklus nicht greifen; erst wenn PV-Überschuss über
    PV_SURPLUS_HYSTERESIS_CYCLES aufeinanderfolgende Zyklen bestätigt ist,
    wird zeitgesteuertes Laden selbst inaktiv, und erst danach kann
    netzdienliches Laden - nach seiner eigenen, ebenso vielzyklischen
    Bestätigung ausreichender tatsächlicher SAX-Ladeleistung - übernehmen."""
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

    grid_serving_data = {
        **coordinator.data,
        # Vorzeichenkonvention: negativ = Einspeisung/PV-Überschuss - löst
        # den PV-Überschuss-Abbruch des zeitgesteuerten Ladens unten aus.
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 300),
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }

    try:
        with _patched_now(12):
            # Kein PV-Überschuss -> nur zeitgesteuertes Laden kann greifen.
            await coordinator._async_enforce_grid_charge(
                {**coordinator.data, "smartmeter_power": 0}
            )
            await asyncio.sleep(0.1)
            assert coordinator._timed_charge_active is True
            assert coordinator.grid_serving_active is False

            # Erster Zyklus mit PV-Überschuss reicht wegen der
            # Zyklen-Hysterese noch nicht, um zeitgesteuertes Laden zu
            # beenden.
            await coordinator._async_enforce_grid_charge(grid_serving_data)
            await asyncio.sleep(0.1)
            assert coordinator._timed_charge_active is True
            assert coordinator.grid_serving_active is False

            # Zweiter aufeinanderfolgender Zyklus bestätigt den
            # PV-Überschuss: zeitgesteuertes Laden wird inaktiv, und
            # netzdienliches Laden beginnt selbst mit Schritt a seine
            # eigene Hysterese (noch nicht bestätigt).
            await coordinator._async_enforce_grid_charge(grid_serving_data)
            await asyncio.sleep(0.1)
            assert coordinator._timed_charge_active is False
            assert coordinator.grid_serving_active is False

            # Zweiter aufeinanderfolgender Zyklus mit ausreichender
            # SAX-Ladeleistung bestätigt Schritt a - netzdienliches Laden
            # übernimmt aktiv.
            await coordinator._async_enforce_grid_charge(grid_serving_data)
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
    for month in set(ALL_MONTHS) - {5, 6, 7, 8}:
        await coordinator.async_set_grid_serving_month(month, False)
    await coordinator.async_set_grid_serving_enabled(True)

    try:
        with _patched_now(12, month=7):
            # Zwei aufeinanderfolgende Zyklen wegen der Zyklen-Hysterese
            # von Schritt a (PV_SURPLUS_HYSTERESIS_CYCLES).
            await coordinator._async_enforce_grid_charge(coordinator.data)
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


# -- Energy-Dashboard-Kompatibilität (REQ-ENERGY-DASHBOARD) ------------------


def test_accumulate_energy_stays_none_before_restore(hass) -> None:
    """Ohne vorherigen restore_energy_charged/-discharged-Aufruf (d. h. vor
    Abschluss des RestoreEntity-Restores, siehe sensor.SaxPowerEnergySensor)
    bleibt der Zählerstand None, selbst über mehrere Ticks mit bekannter
    Leistung hinweg - siehe SaxPowerCoordinator._accumulate_energy."""
    coordinator = _make_coordinator(hass, _make_client())

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        data = {"storage_power_active": -1000}
        coordinator._accumulate_energy(data)
    assert data["energy_charged"] is None
    assert data["energy_discharged"] is None

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=4600.0
    ):
        data = {"storage_power_active": -1000}
        coordinator._accumulate_energy(data)
    assert data["energy_charged"] is None
    assert data["energy_discharged"] is None


def test_accumulate_energy_first_tick_establishes_baseline_only(hass) -> None:
    """Der erste Tick nach dem Restore darf noch keine (unbekannte)
    Vor-Leistung verbuchen, sondern nur die Zeitbasis für den nächsten Tick
    setzen."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.restore_energy_charged(0.0)
    coordinator.restore_energy_discharged(0.0)

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        data = {"storage_power_active": -1000}
        coordinator._accumulate_energy(data)

    assert data["energy_charged"] == 0.0
    assert data["energy_discharged"] == 0.0


def test_accumulate_energy_charging_splits_into_charged_kwh(hass) -> None:
    """1000 W Ladeleistung (storage_power_active negativ) über 3600s ergibt
    1 kWh im Lade-Zähler, der Entlade-Zähler bleibt bei 0."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.restore_energy_charged(0.0)
    coordinator.restore_energy_discharged(0.0)

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy({"storage_power_active": -1000})

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=4600.0
    ):
        data = {"storage_power_active": -1000}
        coordinator._accumulate_energy(data)

    assert data["energy_charged"] == 1.0
    assert data["energy_discharged"] == 0.0


def test_accumulate_energy_discharging_splits_into_discharged_kwh(hass) -> None:
    """Analog zu test_accumulate_energy_charging_splits_into_charged_kwh für
    positive Leistung (Entladung)."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.restore_energy_charged(0.0)
    coordinator.restore_energy_discharged(0.0)

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy({"storage_power_active": 2000})

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=2800.0
    ):
        data = {"storage_power_active": 2000}
        coordinator._accumulate_energy(data)

    assert data["energy_charged"] == 0.0
    assert data["energy_discharged"] == 1.0


def test_accumulate_energy_skips_interval_when_power_unknown(hass) -> None:
    """Wird der SunSpec-Modus-Block zwischenzeitlich nicht erreichbar
    (storage_power_active None, siehe REQ-EXTENDED-MODE-RESILIENCE), darf
    weder die Lücke selbst noch die Zeit davor nach Wiederkehr fälschlich
    als Energie verbucht werden - _energy_last_ts wird trotzdem
    fortgeschrieben, damit kein "Nachhol"-Sprung entsteht."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.restore_energy_charged(0.0)
    coordinator.restore_energy_discharged(0.0)

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy({"storage_power_active": -1000})

    # SunSpec-Modus fällt für eine lange Zeitspanne aus.
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=100000.0
    ):
        coordinator._accumulate_energy({"storage_power_active": None})

    # Wieder erreichbar, kurz danach.
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=100010.0
    ):
        data = {"storage_power_active": -1000}
        coordinator._accumulate_energy(data)

    # Nur die 10s seit der Wiederkehr fließen ein (1000W * 10/3600/1000 kWh),
    # nicht die ~99000s Ausfallzeit davor.
    assert data["energy_charged"] == round(1000 * (10 / 3600) / 1000, 3)


def test_restore_energy_charged_and_discharged_continue_from_saved_value(
    hass,
) -> None:
    """restore_energy_charged/-discharged setzen einen zuvor gespeicherten
    Zählerstand (siehe sensor.SaxPowerEnergySensor.async_added_to_hass) -
    nachfolgende Akkumulation baut darauf auf, statt bei 0 neu zu starten."""
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.restore_energy_charged(12.5)
    coordinator.restore_energy_discharged(7.0)

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy({"storage_power_active": -1000})

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=4600.0
    ):
        data = {"storage_power_active": -1000}
        coordinator._accumulate_energy(data)

    assert data["energy_charged"] == 13.5
    assert data["energy_discharged"] == 7.0


def test_restore_energy_rejects_negative_values(hass, caplog) -> None:
    """Ein negativer Altzustand bleibt uninitialisiert und wird geloggt.

    Insbesondere darf daraus kein künstlicher Reset auf 0 entstehen
    (REQ-ENERGY-DASHBOARD, Regression zu Issue #101).
    """
    coordinator = _make_coordinator(hass, _make_client())
    coordinator.restore_energy_charged(-5.0)
    coordinator.restore_energy_discharged(-3.0)

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        data = {"storage_power_active": 0}
        coordinator._accumulate_energy(data)

    assert data["energy_charged"] is None
    assert data["energy_discharged"] is None
    assert "Ungültigen RestoreEntity-Altzustand" in caplog.text
