"""Tests für die Entladesperre / preisgesteuertes Aufsparen.

Siehe anforderung.yaml, REQ-DISCHARGE-BLOCK sowie
coordinator.SaxPowerCoordinator._async_enforce_grid_charge (Stufe 5 der
Vorrangkette) und price_optimizer.compute_discharge_block_plan.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from custom_components.sax_power.const import (
    DISCHARGE_BLOCK_MODE_OFF,
    DISCHARGE_BLOCK_MODE_PRICE,
    DISCHARGE_BLOCK_MODE_WINDOW,
    DISCHARGE_BLOCK_STATUS_BLOCKING,
    DISCHARGE_BLOCK_STATUS_NO_PRICE_DATA,
    DISCHARGE_BLOCK_STATUS_OFF,
    DISCHARGE_BLOCK_STATUS_PAUSED_CHARGING,
    DISCHARGE_BLOCK_STATUS_PAUSED_MIN_SOC,
    DISCHARGE_BLOCK_STATUS_PAUSED_PV_SURPLUS,
    DISCHARGE_BLOCK_STATUS_WAITING_PRICE,
    DISCHARGE_BLOCK_STATUS_WAITING_WINDOW,
    MAX_SOC,
    PV_SURPLUS_HYSTERESIS_CYCLES,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.price_optimizer import (
    DischargeBlockContext,
    PricePlan,
    PriceSlot,
    compute_discharge_block_plan,
)

# --------------------------------------------------------------------------
# compute_discharge_block_plan (reine Preislogik, ohne Coordinator)
# --------------------------------------------------------------------------
NOW = datetime(2024, 6, 1, 12, 30, tzinfo=dt_util.DEFAULT_TIME_ZONE)


def _slots(*prices: float, start_hour: int = 12) -> list[PriceSlot]:
    """Stündliche Slots ab `start_hour` desselben Tages."""
    base = NOW.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    return [
        PriceSlot(
            start=base + timedelta(hours=index),
            end=base + timedelta(hours=index + 1),
            price=price,
        )
        for index, price in enumerate(prices)
    ]


def test_compute_discharge_block_plan_blocks_below_threshold() -> None:
    """Liegt der laufende Slot unter der Schwelle, wird gesperrt - die
    gespeicherte Energie bleibt für die teuren Stunden übrig."""
    plan = compute_discharge_block_plan(
        NOW,
        _slots(0.10, 0.40),
        DischargeBlockContext(mode=DISCHARGE_BLOCK_MODE_PRICE, max_price=0.20),
    )

    assert plan.block_now is True
    assert plan.status == DISCHARGE_BLOCK_STATUS_BLOCKING
    assert plan.current_price == 0.10
    assert plan.threshold == 0.20
    assert [slot.price for slot in plan.slots] == [0.10]


def test_compute_discharge_block_plan_releases_above_threshold() -> None:
    """Über der Schwelle wird nicht gesperrt; next_start zeigt auf das
    nächste Sperrfenster im Planungshorizont."""
    plan = compute_discharge_block_plan(
        NOW,
        _slots(0.40, 0.35, 0.05),
        DischargeBlockContext(mode=DISCHARGE_BLOCK_MODE_PRICE, max_price=0.20),
    )

    assert plan.block_now is False
    assert plan.status == DISCHARGE_BLOCK_STATUS_WAITING_PRICE
    assert plan.next_start == NOW.replace(hour=14, minute=0)


def test_compute_discharge_block_plan_without_threshold_never_blocks() -> None:
    """Ohne gesetzte Preisschwelle (Number-Entity noch nicht restauriert)
    wird nicht gesperrt, statt eine Schwelle zu raten."""
    plan = compute_discharge_block_plan(
        NOW,
        _slots(0.05, 0.05),
        DischargeBlockContext(mode=DISCHARGE_BLOCK_MODE_PRICE, max_price=None),
    )

    assert plan.block_now is False
    assert plan.slots == ()


def test_compute_discharge_block_plan_without_price_data() -> None:
    plan = compute_discharge_block_plan(
        NOW,
        [],
        DischargeBlockContext(mode=DISCHARGE_BLOCK_MODE_PRICE, max_price=0.20),
    )

    assert plan.status == DISCHARGE_BLOCK_STATUS_NO_PRICE_DATA
    assert plan.block_now is False


def test_compute_discharge_block_plan_ignores_slots_beyond_horizon() -> None:
    """Nur Slots innerhalb von PRICE_PLAN_HORIZON_HOURS gehen ein - derselbe
    gleitende Planungshorizont wie beim preisoptimierten Laden."""
    far_future = [
        PriceSlot(
            start=NOW + timedelta(hours=30),
            end=NOW + timedelta(hours=31),
            price=0.01,
        )
    ]
    plan = compute_discharge_block_plan(
        NOW,
        far_future,
        DischargeBlockContext(mode=DISCHARGE_BLOCK_MODE_PRICE, max_price=0.20),
    )

    assert plan.status == DISCHARGE_BLOCK_STATUS_NO_PRICE_DATA


def test_compute_discharge_block_plan_off_when_mode_not_price() -> None:
    plan = compute_discharge_block_plan(
        NOW,
        _slots(0.05),
        DischargeBlockContext(mode=DISCHARGE_BLOCK_MODE_WINDOW, max_price=0.20),
    )

    assert plan.status == DISCHARGE_BLOCK_STATUS_OFF
    assert plan.block_now is False


# --------------------------------------------------------------------------
# Coordinator: Schreibpfad, Vorrangkette, Freigabegründe
# --------------------------------------------------------------------------
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
    # Vorgabewerte, die die zugehörigen Number-Entities beim ersten Start
    # setzen (siehe number.py) - ohne sie müsste jeder Test sie einzeln
    # setzen, obwohl ein echter Coordinator sie längst hätte.
    coordinator._timed_charge_min_soc = MAX_SOC
    coordinator._discharge_block_min_soc = 20
    coordinator.data = {
        "soc": 60,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": 0,
    }
    return coordinator


def _patched_now(hour: int = 12, month: int = 6):
    """Siehe tests/test_coordinator.py: nur dt_util.now() in coordinator.py
    patchen, damit asyncio-Timer der Hintergrund-Tasks unbeeinflusst
    bleiben."""
    return patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, month, 1, hour, 0),
    )


def _data(coordinator: SaxPowerCoordinator, **overrides) -> dict:
    coordinator.data.update(overrides)
    return coordinator.data


async def _enable_window_block(coordinator: SaxPowerCoordinator) -> None:
    await coordinator.async_set_discharge_block_start(dt_time(11, 0))
    await coordinator.async_set_discharge_block_end(dt_time(16, 0))
    await coordinator.async_set_discharge_block_mode(DISCHARGE_BLOCK_MODE_WINDOW)


async def test_discharge_block_holds_zero_setpoint(hass) -> None:
    """Die Sperre schreibt denselben gehaltenen 0-%-Sollwert wie die
    Max-SOC-Sperre: Register 40051 auf Sollwertvorgabe, Register 40049 auf
    0 % - keine neue Registerlogik."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)

    try:
        with _patched_now(12):
            await _enable_window_block(coordinator)
            await coordinator._async_enforce_grid_charge(_data(coordinator))
        await asyncio.sleep(0.1)

        assert coordinator.discharge_block_active is True
        assert coordinator.sun_charge_active is True
        assert coordinator.discharge_block_status == DISCHARGE_BLOCK_STATUS_BLOCKING
        client.write_register.assert_any_await(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        )
        client.write_register.assert_any_await(
            address=REG_SUN_IC_POWER_SETPOINT_PCT, value=0, device_id=100
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_discharge_block_inactive_outside_window(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())

    with _patched_now(20):
        await _enable_window_block(coordinator)
        await coordinator._async_enforce_grid_charge(_data(coordinator))

    assert coordinator.discharge_block_active is False
    assert coordinator.sun_charge_active is False
    assert coordinator.discharge_block_status == DISCHARGE_BLOCK_STATUS_WAITING_WINDOW


async def test_discharge_block_inactive_in_deselected_month(hass) -> None:
    """Monatslogik wie bei den beiden Ladefenstern: ein abgewählter Monat
    legt die Sperre für diesen Kalendermonat still."""
    coordinator = _make_coordinator(hass, _make_client())

    with _patched_now(12, month=6):
        await _enable_window_block(coordinator)
        await coordinator.async_set_discharge_block_month(6, False)
        await coordinator._async_enforce_grid_charge(_data(coordinator))

    assert 6 not in coordinator.discharge_block_months
    assert coordinator.discharge_block_active is False
    assert coordinator.sun_charge_active is False


async def test_discharge_block_mode_off_releases_setpoint(hass) -> None:
    """Sauberer Ausstieg: das Abschalten der Automatik setzt Register 40051
    aktiv auf 0 zurück, statt einen "stuck zero"-Sollwert stehen zu lassen."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)

    with _patched_now(12):
        await _enable_window_block(coordinator)
        await asyncio.sleep(0.1)
        assert coordinator.sun_charge_active is True

        await coordinator.async_set_discharge_block_mode(DISCHARGE_BLOCK_MODE_OFF)

    assert coordinator.sun_charge_active is False
    assert coordinator.discharge_block_active is False
    assert coordinator.discharge_block_status == DISCHARGE_BLOCK_STATUS_OFF
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_discharge_block_released_below_min_soc(hass) -> None:
    """Unterhalb des Mindest-SOC wird nie gesperrt - die Restenergie eines
    fast leeren Speichers bleibt nutzbar."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)

    with _patched_now(12):
        await _enable_window_block(coordinator)
        await asyncio.sleep(0.1)
        assert coordinator.sun_charge_active is True

        await coordinator._async_enforce_grid_charge(_data(coordinator, soc=20))

    assert coordinator.discharge_block_active is False
    assert coordinator.sun_charge_active is False
    assert coordinator.discharge_block_status == DISCHARGE_BLOCK_STATUS_PAUSED_MIN_SOC
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_discharge_block_released_by_confirmed_pv_surplus(hass) -> None:
    """Bestätigter PV-Überschuss hebt die Sperre auf: ein gehaltener
    0-W-Sollwert nähme sonst auch keine PV-Energie mehr auf und drückte den
    Ertrag ins Netz. Ein einzelner Zyklus reicht wegen der Hysterese nicht."""
    coordinator = _make_coordinator(hass, _make_client())

    try:
        with _patched_now(12):
            await _enable_window_block(coordinator)
            await asyncio.sleep(0.1)
            assert coordinator.sun_charge_active is True

            surplus = _data(
                coordinator,
                smartmeter_power=SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50,
            )
            for _ in range(PV_SURPLUS_HYSTERESIS_CYCLES - 1):
                await coordinator._async_enforce_grid_charge(surplus)
                assert coordinator.discharge_block_active is True

            await coordinator._async_enforce_grid_charge(surplus)

        assert coordinator.discharge_block_active is False
        assert coordinator.sun_charge_active is False
        assert (
            coordinator.discharge_block_status
            == DISCHARGE_BLOCK_STATUS_PAUSED_PV_SURPLUS
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_discharge_block_pv_surplus_hysteresis_resets_on_drop(hass) -> None:
    """Ein einzelner Wert unter dem Schwellwert setzt die Hysterese zurück -
    kurze Einspeisespitzen heben die Sperre nicht auf."""
    coordinator = _make_coordinator(hass, _make_client())

    try:
        with _patched_now(12):
            await _enable_window_block(coordinator)
            await asyncio.sleep(0.1)

            await coordinator._async_enforce_grid_charge(
                _data(
                    coordinator,
                    smartmeter_power=SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50,
                )
            )
            await coordinator._async_enforce_grid_charge(
                _data(coordinator, smartmeter_power=0)
            )
            await coordinator._async_enforce_grid_charge(
                _data(
                    coordinator,
                    smartmeter_power=SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50,
                )
            )

        assert coordinator.discharge_block_active is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_discharge_block_yields_to_timed_charge(hass) -> None:
    """Stufe 2 schlägt Stufe 5: läuft zeitgesteuertes Laden, wird der
    Ladesollwert geschrieben statt der 0-%-Sperrwert."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_timed_charge_start(dt_time(11, 0))
    await coordinator.async_set_timed_charge_end(dt_time(16, 0))

    try:
        with _patched_now(12):
            await _enable_window_block(coordinator)
            await coordinator.async_set_timed_charge_enabled(True)
            await coordinator._async_enforce_grid_charge(_data(coordinator))
        await asyncio.sleep(0.1)

        assert coordinator._timed_charge_active is True
        assert coordinator.discharge_block_active is False
        assert (
            coordinator.discharge_block_status == DISCHARGE_BLOCK_STATUS_PAUSED_CHARGING
        )
        assert coordinator._sun_charge_power != 0
    finally:
        await coordinator.async_stop_sun_charge()


async def test_discharge_block_yields_to_price_charge(hass) -> None:
    """Stufe 3 (preisoptimiertes Laden) schlägt Stufe 5 ebenfalls."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    await coordinator.async_set_max_soc(90)

    try:
        with _patched_now(12):
            await _enable_window_block(coordinator)
            await coordinator.async_set_price_charge_strategy("absolute")
            await coordinator.async_set_price_charge_enabled(True, force=True)
            # Der Ladeplan selbst kommt aus dem Planner (price_optimizer.py)
            # und wird hier direkt vorgegeben - geprüft wird die
            # Vorrangkette, nicht die Preisauswertung.
            coordinator.price_planner.plan = PricePlan(charge_now=True)
            await coordinator._async_enforce_grid_charge(_data(coordinator))
        await asyncio.sleep(0.1)

        assert coordinator.price_charge_active is True
        assert coordinator.discharge_block_active is False
        assert coordinator._sun_charge_power != 0
    finally:
        await coordinator.async_stop_sun_charge()


async def test_discharge_block_yields_to_grid_serving(hass) -> None:
    """Stufe 4 (netzdienliches Laden) schlägt Stufe 5 - und ein zuvor von
    der Sperre gehaltener 0-%-Sollwert wird dabei aktiv freigegeben: dessen
    Ladeleistung von 0 W käme sonst nie über die Erkennungsschwelle von
    Schritt a, die Zustandsmaschine bliebe stehen."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_grid_serving_start(dt_time(11, 0))
    await coordinator.async_set_grid_serving_end(dt_time(16, 0))

    try:
        with _patched_now(12):
            await _enable_window_block(coordinator)
            await asyncio.sleep(0.1)
            assert coordinator.sun_charge_active is True

            await coordinator.async_set_grid_serving_enabled(True)

        assert coordinator.discharge_block_active is False
        assert coordinator._discharge_block_setpoint_active is False
        assert coordinator.sun_charge_active is False
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SMARTMETER,
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_discharge_block_yields_to_max_soc_lock(hass) -> None:
    """Stufe 1 (Max-SOC-Sperre) bleibt oberste Priorität: bei erreichtem
    Ziel-SOC entscheidet sie über den Sollwert, nicht die Entladesperre."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_max_soc(90)

    try:
        with _patched_now(12):
            await _enable_window_block(coordinator)
            await coordinator._async_enforce_grid_charge(_data(coordinator, soc=95))
        await asyncio.sleep(0.1)

        assert coordinator.discharge_block_active is False
        assert coordinator._discharge_block_setpoint_active is False
        assert coordinator.max_soc_clamped is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_discharge_block_price_mode_uses_planner_plan(hass) -> None:
    """Im Modus "price" entscheidet der Sperrplan des Planners - ohne
    eigene Preis-Parsing-Logik im Coordinator."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    await coordinator.async_set_discharge_block_max_price(0.20)

    hass.states.async_set(
        "sensor.strompreis",
        "0.10",
        {
            "unit_of_measurement": "EUR/kWh",
            "raw_today": [
                {
                    "start": (dt_util.now() - timedelta(minutes=30)).isoformat(),
                    "end": (dt_util.now() + timedelta(minutes=30)).isoformat(),
                    "value": 0.10,
                }
            ],
        },
    )
    coordinator.options = {"price_sensor": "sensor.strompreis"}

    try:
        # Bewusst ohne _patched_now: der Modus "price" wertet keine
        # Tageszeit aus, die Preis-Slots oben liegen um die echte
        # dt_util.now() herum.
        await coordinator.async_set_discharge_block_mode(DISCHARGE_BLOCK_MODE_PRICE)
        await asyncio.sleep(0.1)

        assert coordinator.discharge_block_plan.block_now is True
        assert coordinator.discharge_block_active is True
        assert coordinator.sun_charge_active is True
    finally:
        await coordinator.async_stop_sun_charge()


async def test_discharge_block_price_mode_without_price_sensor(hass) -> None:
    """Ohne konfigurierten Preis-Sensor sperrt der Modus "price" nicht und
    benennt den Grund im Status."""
    coordinator = _make_coordinator(hass, _make_client())

    await coordinator.async_set_discharge_block_mode(DISCHARGE_BLOCK_MODE_PRICE)

    assert coordinator.discharge_block_active is False
    assert coordinator.sun_charge_active is False
    assert coordinator.discharge_block_status == DISCHARGE_BLOCK_STATUS_NO_PRICE_DATA


async def test_discharge_block_unknown_mode_rejected(hass) -> None:
    coordinator = _make_coordinator(hass, _make_client())

    with pytest.raises(HomeAssistantError):
        await coordinator.async_set_discharge_block_mode("unsinn")


async def test_discharge_block_window_setter_sets_both_bounds(hass) -> None:
    """Service set_discharge_block_window setzt beide Grenzen in einem
    Aufruf - ohne Überschneidungsprüfung, weil die Sperre ohnehin jeder
    Ladeautomatik weicht."""
    coordinator = _make_coordinator(hass, _make_client())
    await coordinator.async_set_timed_charge_start(dt_time(11, 0))
    await coordinator.async_set_timed_charge_end(dt_time(16, 0))

    await coordinator.async_set_discharge_block_window(dt_time(11, 0), dt_time(16, 0))

    assert coordinator.discharge_block_start == dt_time(11, 0)
    assert coordinator.discharge_block_end == dt_time(16, 0)


async def test_async_shutdown_leaves_no_held_setpoint(hass) -> None:
    """async_shutdown (auch über __init__.async_unload_entry beim Reload des
    Config Entry) setzt Register 40051 aktiv auf SmartMeter-Nullregelung
    zurück - es darf kein 0-%-Sollwert stehen bleiben."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)

    with _patched_now(12):
        await _enable_window_block(coordinator)
    await asyncio.sleep(0.1)
    assert coordinator.sun_charge_active is True

    await coordinator.async_shutdown()

    assert coordinator.sun_charge_active is False
    client.write_register.assert_awaited_with(
        address=REG_SUN_IC_CONTROL_MODE,
        value=SUN_IC_CONTROL_MODE_SMARTMETER,
        device_id=100,
    )


async def test_discharge_block_state_published_for_entities(hass) -> None:
    """binary_sensor/sensor lesen den Zustand wie jeden anderen Messwert aus
    coordinator.data (siehe _publish_charge_state)."""
    coordinator = _make_coordinator(hass, _make_client())

    try:
        with _patched_now(12):
            await _enable_window_block(coordinator)
            await coordinator._async_enforce_grid_charge(_data(coordinator))
            coordinator._publish_charge_state(coordinator.data)

        assert coordinator.data["discharge_block_active"] is True
        assert coordinator.data["discharge_block_status"] == (
            DISCHARGE_BLOCK_STATUS_BLOCKING
        )
    finally:
        await coordinator.async_stop_sun_charge()
