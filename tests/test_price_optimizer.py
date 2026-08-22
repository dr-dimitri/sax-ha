"""Tests für das preisoptimierte Laden (anforderung.yaml,
REQ-DYNAMIC-PRICE-CHARGE).

Aufgeteilt in drei Blöcke:
  1. Einlesen der Preisdaten aus den Attributformaten verbreiteter
     Strompreis-Integrationen (parse_price_slots).
  2. Reine Planberechnung je Strategie (compute_plan) - ohne Home Assistant.
  3. Zusammenspiel mit dem Coordinator (Schreibpfad, Vorrangregeln,
     Konfliktdialog gegenüber der Netzladung).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components import persistent_notification
from homeassistant.core import State
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util

from custom_components.sax_power.const import (
    CONF_PRICE_SENSOR,
    DATA_COORDINATOR,
    DOMAIN,
    ISSUE_PRICE_CHARGE_CONFLICT,
    ISSUE_TIMED_CHARGE_CONFLICT,
    MAX_SOC,
    PRICE_STATUS_CHARGING,
    PRICE_STATUS_NO_PRICE_DATA,
    PRICE_STATUS_OFF,
    PRICE_STATUS_PAUSED_GRID_SERVING,
    PRICE_STATUS_PAUSED_MAX_SOC,
    PRICE_STATUS_PAUSED_NEUTRAL_BAND,
    PRICE_STATUS_PAUSED_PV_SURPLUS,
    PRICE_STATUS_PAUSED_TIMED_CHARGE,
    PRICE_STATUS_PV_FORECAST_COVERS,
    PRICE_STATUS_WAITING,
    PRICE_STRATEGY_ABSOLUTE,
    PRICE_STRATEGY_OFF,
    PRICE_STRATEGY_RELATIVE,
    PRICE_STRATEGY_SMART,
    PRICE_UNIT_AUTO,
    PRICE_UNIT_CT_KWH,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
    SUN_IC_CONTROL_MODE_SETPOINT,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator, to_unsigned16
from custom_components.sax_power.price_optimizer import (
    PriceChargeContext,
    PricePlan,
    PriceSlot,
    compute_plan,
    parse_price_slots,
)
from custom_components.sax_power.repairs import async_create_fix_flow
from custom_components.sax_power.select import SaxPowerPriceStrategySelect
from custom_components.sax_power.switch import SaxPowerPriceChargeSwitch


def _local(hour: int, minute: int = 0, day: int = 15) -> datetime:
    """Lokale Zeit in der von den Tests genutzten Zeitzone.

    Bewusst eine Funktion statt einer Modulkonstanten: dt_util.
    DEFAULT_TIME_ZONE wird erst von der hass-Fixture gesetzt, ein zur
    Importzeit ausgewerteter Wert läge noch in UTC.
    """
    return datetime(2024, 1, day, hour, minute, tzinfo=dt_util.DEFAULT_TIME_ZONE)


def _patched_now(hour: int, minute: int = 0):
    """Patcht dt_util.now() auf einen festen Zeitpunkt - siehe
    tests/test_coordinator.py für die Begründung (freezegun würde den
    Hintergrund-Task für die Netzladung/netzdienliches Laden einfrieren)."""
    return patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=datetime(2024, 1, 1, hour, minute),
    )


def _now() -> datetime:
    return _local(12)


class _FakeState:
    """Minimaler Ersatz für homeassistant.core.State - parse_price_slots
    braucht nur `attributes`."""

    def __init__(self, state: str = "0.25", **attributes: object) -> None:
        self.state = state
        self.attributes = attributes


# ===========================================================================
# 1. Preisdaten einlesen
# ===========================================================================
def test_parse_price_slots_nordpool_raw_today_and_tomorrow() -> None:
    """Nordpool/EPEX-Stil: raw_today/raw_tomorrow mit start/end/value."""
    state = _FakeState(
        raw_today=[
            {
                "start": _local(12).isoformat(),
                "end": _local(13).isoformat(),
                "value": 0.30,
            },
            {
                "start": _local(13).isoformat(),
                "end": _local(14).isoformat(),
                "value": 0.10,
            },
        ],
        raw_tomorrow=[
            {
                "start": _local(0, day=16).isoformat(),
                "end": _local(1, day=16).isoformat(),
                "value": 0.05,
            },
        ],
    )
    slots = parse_price_slots(state, now=_now())

    assert len(slots) == 3
    assert slots[0].price == pytest.approx(0.30)
    assert slots[1].start == _local(13)
    assert slots[2].price == pytest.approx(0.05)


def test_parse_price_slots_tibber_number_lists() -> None:
    """Tibber-Stil: `today`/`tomorrow` sind reine Zahlenlisten für einen
    Kalendertag - die Startzeiten müssen daraus abgeleitet werden."""
    state = _FakeState(today=[0.10 + i / 100 for i in range(24)])
    slots = parse_price_slots(state, now=_now())

    assert len(slots) == 24
    assert slots[0].start == _local(0)
    assert slots[0].end == _local(1)
    assert slots[23].price == pytest.approx(0.33)


def test_parse_price_slots_quarter_hourly_entries() -> None:
    """96 Werte pro Tag ergeben Viertelstunden-Slots."""
    state = _FakeState(today=[0.2] * 96)
    slots = parse_price_slots(state, now=_now())

    assert len(slots) == 96
    assert slots[0].end - slots[0].start == timedelta(minutes=15)


def test_parse_price_slots_data_attribute_with_start_time() -> None:
    """ENTSO-e/Awattar-Stil: `data` mit start_time/price, ohne Endzeit -
    das Ende ergibt sich aus dem Beginn des Folge-Slots."""
    state = _FakeState(
        data=[
            {"start_time": _local(12).isoformat(), "price": 0.22},
            {"start_time": _local(13).isoformat(), "price": 0.18},
        ]
    )
    slots = parse_price_slots(state, now=_now())

    assert slots[0].end == _local(13)
    # Letzter Slot ohne Nachfolger: Länge aus dem kleinsten bekannten Abstand.
    assert slots[1].end == _local(14)


def test_parse_price_slots_converts_cent_via_unit() -> None:
    """ct/kWh wird anhand der Sensor-Einheit automatisch auf EUR/kWh
    umgerechnet."""
    state = _FakeState(
        unit_of_measurement="ct/kWh",
        today=[25.0] * 24,
    )
    slots = parse_price_slots(state, now=_now(), unit=PRICE_UNIT_AUTO)

    assert slots[0].price == pytest.approx(0.25)


def test_parse_price_slots_explicit_unit_overrides_sensor_unit() -> None:
    """Fehlt am Sensor eine (brauchbare) Einheit, lässt sie sich erzwingen."""
    state = _FakeState(today=[25.0] * 24)
    slots = parse_price_slots(state, now=_now(), unit=PRICE_UNIT_CT_KWH)

    assert slots[0].price == pytest.approx(0.25)


def test_parse_price_slots_explicit_attribute_wins() -> None:
    """Ein konfiguriertes Attribut hat Vorrang vor der Auto-Erkennung."""
    state = _FakeState(
        today=[0.10] * 24,
        eigene_vorschau=[
            {"start": _local(12).isoformat(), "value": 0.99},
        ],
    )
    slots = parse_price_slots(state, now=_now(), attribute="eigene_vorschau")

    assert len(slots) == 1
    assert slots[0].price == pytest.approx(0.99)


@pytest.mark.parametrize(
    "state",
    [
        None,
        _FakeState(),  # gar keine Attribute
        _FakeState(today=[]),  # leere Liste
        _FakeState(today=["keine Zahl"]),  # unbrauchbare Einträge
    ],
)
def test_parse_price_slots_returns_empty_without_usable_data(state: object) -> None:
    assert parse_price_slots(state, now=_now()) == []


# ===========================================================================
# 2. Planberechnung
# ===========================================================================
def _slots(*prices: float, start_hour: int = 12) -> list[PriceSlot]:
    """Stündliche Slots ab `start_hour` mit den übergebenen Preisen."""
    return [
        PriceSlot(
            start=_local(start_hour + index),
            end=_local(start_hour + index + 1),
            price=price,
        )
        for index, price in enumerate(prices)
    ]


def _ctx(**overrides: object) -> PriceChargeContext:
    defaults: dict[str, object] = {
        "enabled": True,
        "strategy": PRICE_STRATEGY_ABSOLUTE,
        "max_price": 0.20,
        "hours": 3,
        "target_soc": 80,
        "current_soc": 40,
        "capacity_kwh": 10.0,
        "charge_power_w": 3000,
        "pv_forecast_kwh": None,
        "pv_factor": 0.8,
    }
    defaults.update(overrides)
    return PriceChargeContext(**defaults)  # type: ignore[arg-type]


def test_compute_plan_off_when_disabled() -> None:
    plan = compute_plan(_now(), _slots(0.01), _ctx(enabled=False))

    assert plan.status == PRICE_STATUS_OFF
    assert plan.charge_now is False


def test_compute_plan_off_when_strategy_off() -> None:
    plan = compute_plan(_now(), _slots(0.01), _ctx(strategy=PRICE_STRATEGY_OFF))

    assert plan.status == PRICE_STATUS_OFF


def test_compute_plan_reports_missing_price_data() -> None:
    plan = compute_plan(_now(), [], _ctx())

    assert plan.status == PRICE_STATUS_NO_PRICE_DATA
    assert plan.next_start is None


def test_compute_plan_ignores_slots_in_the_past() -> None:
    """Nur Slots, die jetzt oder später enden, gehen in die Auswahl ein."""
    past = PriceSlot(start=_local(8), end=_local(9), price=0.01)
    plan = compute_plan(_now(), [past, *_slots(0.30)], _ctx())

    assert plan.charge_now is False
    assert plan.status == PRICE_STATUS_WAITING


def test_compute_plan_absolute_charges_below_threshold() -> None:
    plan = compute_plan(_now(), _slots(0.15, 0.30), _ctx(max_price=0.20))

    assert plan.charge_now is True
    assert plan.status == PRICE_STATUS_CHARGING
    assert plan.next_start == _local(12)
    assert plan.current_price == pytest.approx(0.15)


def test_compute_plan_absolute_waits_and_reports_next_start() -> None:
    """Über der Preisgrenze wird nicht geladen - der Sensor zeigt aber, wann
    das nächste günstige Fenster beginnt."""
    plan = compute_plan(_now(), _slots(0.30, 0.28, 0.12), _ctx(max_price=0.20))

    assert plan.charge_now is False
    assert plan.status == PRICE_STATUS_WAITING
    assert plan.next_start == _local(14)


def test_compute_plan_relative_selects_cheapest_hours() -> None:
    """ "Lade in den 2 günstigsten Stunden" wählt genau diese aus - unabhängig
    davon, ob sie am Anfang oder Ende des Horizonts liegen."""
    plan = compute_plan(
        _now(),
        _slots(0.30, 0.10, 0.40, 0.05),
        _ctx(strategy=PRICE_STRATEGY_RELATIVE, hours=2),
    )

    assert [slot.start for slot in plan.slots] == [_local(13), _local(15)]
    assert plan.charge_now is False
    assert plan.next_start == _local(13)
    # Die Preisgrenze des Plans ist der teuerste noch ausgewählte Slot.
    assert plan.threshold == pytest.approx(0.10)


def test_compute_plan_relative_charges_when_cheapest_slot_is_now() -> None:
    plan = compute_plan(
        _now(),
        _slots(0.05, 0.30, 0.40),
        _ctx(strategy=PRICE_STRATEGY_RELATIVE, hours=1),
    )

    assert plan.charge_now is True
    assert plan.status == PRICE_STATUS_CHARGING


def test_compute_plan_relative_limits_to_planning_horizon() -> None:
    """Slots jenseits von PRICE_PLAN_HORIZON_HOURS gehen nicht in die
    Auswahl ein, auch wenn sie billiger wären."""
    far_away = PriceSlot(
        start=_now() + timedelta(hours=30),
        end=_now() + timedelta(hours=31),
        price=0.01,
    )
    plan = compute_plan(
        _now(),
        [*_slots(0.30, 0.20), far_away],
        _ctx(strategy=PRICE_STRATEGY_RELATIVE, hours=1),
    )

    assert [slot.start for slot in plan.slots] == [_local(13)]


def test_compute_plan_smart_skips_grid_charge_when_pv_forecast_covers_demand() -> None:
    """Kernnutzen des Smart-Modus: 40 % -> 80 % bei 10 kWh sind 4 kWh; die
    Prognose liefert davon nutzbar 8 kWh * 0.8 = 6.4 kWh - es wird gar kein
    Netzstrom eingekauft."""
    plan = compute_plan(
        _now(),
        _slots(0.05, 0.05, 0.05),
        _ctx(strategy=PRICE_STRATEGY_SMART, pv_forecast_kwh=8.0, pv_factor=0.8),
    )

    assert plan.status == PRICE_STATUS_PV_FORECAST_COVERS
    assert plan.charge_now is False
    assert plan.slots == ()
    assert plan.needed_hours == 0


def test_compute_plan_smart_derives_hours_from_remaining_demand() -> None:
    """4 kWh Bedarf minus 1.6 kWh nutzbare Prognose = 2.4 kWh; bei 3 kW
    Ladeleistung also 0.8 h -> ein einziger (der günstigste) Slot."""
    plan = compute_plan(
        _now(),
        _slots(0.30, 0.10, 0.20),
        _ctx(
            strategy=PRICE_STRATEGY_SMART,
            hours=3,
            pv_forecast_kwh=2.0,
            pv_factor=0.8,
        ),
    )

    assert plan.needed_hours == 1
    assert [slot.start for slot in plan.slots] == [_local(13)]


def test_compute_plan_smart_respects_hours_slider_as_upper_bound() -> None:
    """Auch wenn rechnerisch mehr nötig wäre, kauft die Automatik nie mehr
    Stunden ein, als der Schieberegler erlaubt."""
    plan = compute_plan(
        _now(),
        _slots(0.30, 0.10, 0.20, 0.15),
        _ctx(
            strategy=PRICE_STRATEGY_SMART,
            hours=1,
            current_soc=0,
            target_soc=100,
            capacity_kwh=20.0,
            charge_power_w=1000,
        ),
    )

    assert len(plan.slots) == 1


def test_compute_plan_smart_falls_back_to_hours_without_capacity() -> None:
    """Ohne Kapazität (SunSpec-Block nicht erreichbar) ist keine
    Bedarfsrechnung möglich - dann verhält sich Smart wie Relativ."""
    plan = compute_plan(
        _now(),
        _slots(0.30, 0.10, 0.20),
        _ctx(strategy=PRICE_STRATEGY_SMART, hours=2, capacity_kwh=None),
    )

    assert len(plan.slots) == 2


# ===========================================================================
# 3. Zusammenspiel mit dem Coordinator
# ===========================================================================
def _make_client() -> MagicMock:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register = AsyncMock(return_value=write_result)
    return client


def _make_coordinator(hass, client: MagicMock | None = None) -> SaxPowerCoordinator:
    coordinator = SaxPowerCoordinator(
        hass,
        client or _make_client(),
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
    )
    coordinator._timed_charge_min_soc = MAX_SOC
    return coordinator


def _charging_plan() -> PricePlan:
    """Plan, der für "jetzt" ein ausgewähltes Preisfenster meldet."""
    slot = PriceSlot(start=_local(12), end=_local(13), price=0.05)
    return PricePlan(
        status=PRICE_STATUS_CHARGING,
        charge_now=True,
        next_start=slot.start,
        slots=(slot,),
        current_price=slot.price,
        threshold=slot.price,
    )


def _waiting_plan() -> PricePlan:
    slot = PriceSlot(start=_local(20), end=_local(21), price=0.05)
    return PricePlan(
        status=PRICE_STATUS_WAITING,
        charge_now=False,
        next_start=slot.start,
        slots=(slot,),
        current_price=0.32,
        threshold=slot.price,
    )


def test_context_uses_ic_max_power_reference_as_charge_power(hass) -> None:
    """ "Max. Netzladeleistung" wurde entfernt (siehe anforderung.yaml,
    REQ-TIMED-SOC-CHARGE) - die Bedarfsrechnung im Smart-Modus nimmt
    stattdessen "ic_max_power_reference" (Register 40053, vom Gerät selbst
    gemeldet) als angenommene Ladeleistung."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}

    ctx = coordinator.price_planner._context()

    assert ctx.charge_power_w == 4600


def test_evaluate_reports_current_price_even_when_price_charge_disabled(
    hass,
) -> None:
    """price_charge_current_price ist eine reine Info-Anzeige und darf nicht
    an der Lade-Automatik hängen - sonst zeigt sie "unbekannt", obwohl der
    Preis-Sensor korrekt konfiguriert ist und aktuelle Daten liefert (siehe
    anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE)."""
    hass.states.async_set(
        "sensor.epex_spot_data_market_price",
        "0.179",
        {
            "unit_of_measurement": "EUR/kWh",
            "data": [
                {
                    "start_time": _local(12).isoformat(),
                    "end_time": _local(13).isoformat(),
                    "price_per_kwh": 0.179,
                }
            ],
        },
    )
    coordinator = _make_coordinator(hass)
    coordinator.options = {CONF_PRICE_SENSOR: "sensor.epex_spot_data_market_price"}
    coordinator.data = {}

    with patch(
        "custom_components.sax_power.price_optimizer.dt_util.now",
        return_value=_local(12, 30),
    ):
        plan = coordinator.price_planner.evaluate()

    assert coordinator.price_charge_enabled is False
    assert plan.status == PRICE_STATUS_OFF
    assert plan.current_price == pytest.approx(0.179)


async def _enable_price_charge(coordinator: SaxPowerCoordinator) -> None:
    await coordinator.async_set_price_charge_strategy(PRICE_STRATEGY_RELATIVE)
    await coordinator.async_set_max_soc(80)
    await coordinator.async_set_price_charge_enabled(True)


async def test_price_charge_writes_setpoint_when_plan_says_charge(hass) -> None:
    """Erfüllte Bedingung -> Zwangsladung aus dem Netz über den
    SunSpec-Schreibpfad (Register 40051 + 40049)."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await _enable_price_charge(coordinator)
    coordinator.price_planner.plan = _charging_plan()

    try:
        await coordinator._async_enforce_grid_charge({"soc": 50})
        await asyncio.sleep(0.1)

        assert coordinator.price_charge_active is True
        assert coordinator.sun_charge_active is True
        assert coordinator.price_charge_status == PRICE_STATUS_CHARGING
        client.write_register.assert_any_await(
            address=REG_SUN_IC_CONTROL_MODE,
            value=SUN_IC_CONTROL_MODE_SETPOINT,
            device_id=100,
        )
        # Lädt immer mit maximal möglicher Leistung (MIN_SETPOINT_POWER
        # sättigt in _watts_to_ic_setpoint_raw auf -100 %), sunssf -2 ->
        # -10000.
        client.write_register.assert_awaited_with(
            address=REG_SUN_IC_POWER_SETPOINT_PCT,
            value=to_unsigned16(-10000),
            device_id=100,
        )
    finally:
        await coordinator.async_stop_sun_charge()


async def test_price_charge_idle_returns_to_zero_feed_in_mode(hass) -> None:
    """Nicht erfüllte Bedingung -> zurück in die SmartMeter-Nullregelung."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}
    await _enable_price_charge(coordinator)
    coordinator.price_planner.plan = _waiting_plan()

    await coordinator._async_enforce_grid_charge({"soc": 50})

    assert coordinator.price_charge_active is False
    assert coordinator.sun_charge_active is False
    assert coordinator.price_charge_status == PRICE_STATUS_WAITING


async def test_price_charge_paused_by_max_soc_lock(hass) -> None:
    """ "Max. SOC" ist der einzige Ziel-SOC und beendet die Netzladung, sobald
    er erreicht ist."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 95, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await _enable_price_charge(coordinator)
    await coordinator.async_set_max_soc(90)
    coordinator.price_planner.plan = _charging_plan()

    try:
        await coordinator._async_enforce_grid_charge({"soc": 95, "smartmeter_power": 0})

        assert coordinator.price_charge_active is False
        assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_MAX_SOC
    finally:
        await coordinator.async_stop_sun_charge()


async def test_price_charge_paused_by_pv_surplus(hass) -> None:
    """PV-Überschuss am Smart Meter bricht die Netzladung ab - günstiger als
    Netzstrom ist die eigene Sonne immer."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}
    await _enable_price_charge(coordinator)
    coordinator.price_planner.plan = _charging_plan()

    # Vorzeichenkonvention: negativ = Einspeisung/PV-Überschuss.
    data = {
        "soc": 50,
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 500),
    }
    # Zyklen-Hysterese: erst nach mehreren bestätigten Zyklen wirksam.
    for _ in range(5):
        await coordinator._async_enforce_grid_charge(data)

    assert coordinator.price_charge_active is False
    assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_PV_SURPLUS


async def test_price_charge_pauses_in_neutral_band(hass) -> None:
    """Preis liegt über der Preisgrenze, aber unterhalb des Neutralpreises:
    manueller Sollwertmodus mit Sollwert 0 statt Nullregelung - Laden UND
    Entladen bleiben gestoppt (siehe anforderung.yaml,
    REQ-DYNAMIC-PRICE-CHARGE, Abschnitt Neutralpreis-Pausezone)."""
    client = _make_client()
    coordinator = _make_coordinator(hass, client)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await _enable_price_charge(coordinator)
    await coordinator.async_set_price_charge_max_price(0.20)
    await coordinator.async_set_price_charge_neutral_price(0.40)
    coordinator.price_planner.plan = PricePlan(
        status=PRICE_STATUS_WAITING, charge_now=False, current_price=0.30
    )

    try:
        await coordinator._async_enforce_grid_charge({"soc": 50, "smartmeter_power": 0})
        await asyncio.sleep(0.1)

        assert coordinator.price_charge_active is False
        assert coordinator.sun_charge_active is True
        assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_NEUTRAL_BAND
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


async def test_price_charge_returns_to_nullregelung_above_neutral_price(hass) -> None:
    """Ab dem Neutralpreis lohnt sich die Entladung wieder - der Speicher
    geht zurück in die geräteeigene SmartMeter-Nullregelung, das Smart
    Meter regelt die Entladung."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}
    await _enable_price_charge(coordinator)
    await coordinator.async_set_price_charge_max_price(0.20)
    await coordinator.async_set_price_charge_neutral_price(0.40)
    coordinator.price_planner.plan = PricePlan(
        status=PRICE_STATUS_WAITING, charge_now=False, current_price=0.45
    )

    await coordinator._async_enforce_grid_charge({"soc": 50, "smartmeter_power": 0})

    assert coordinator.sun_charge_active is False
    assert coordinator.price_charge_status == PRICE_STATUS_WAITING


async def test_price_charge_neutral_band_yields_to_pv_surplus(hass) -> None:
    """PV-Überschuss hat auch gegenüber der Neutralpreis-Pausezone Vorrang -
    sonst würde der manuelle Sollwertmodus freie PV-Energie am Nachladen in
    den Speicher hindern."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}
    await _enable_price_charge(coordinator)
    await coordinator.async_set_price_charge_max_price(0.20)
    await coordinator.async_set_price_charge_neutral_price(0.40)
    coordinator.price_planner.plan = PricePlan(
        status=PRICE_STATUS_WAITING, charge_now=False, current_price=0.30
    )

    # Vorzeichenkonvention: negativ = Einspeisung/PV-Überschuss.
    data = {
        "soc": 50,
        "smartmeter_power": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 500),
    }
    for _ in range(5):
        await coordinator._async_enforce_grid_charge(data)

    assert coordinator.sun_charge_active is False
    assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_PV_SURPLUS


async def test_price_charge_neutral_band_inactive_without_neutral_price_configured(
    hass,
) -> None:
    """Fehlt der Neutralpreis (noch nicht restauriert), bleibt das Verhalten
    unverändert wie vor Einführung des Features - keine stille Annahme
    irgendeines Vorgabewerts."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}
    await _enable_price_charge(coordinator)
    await coordinator.async_set_price_charge_max_price(0.20)
    assert coordinator.price_charge_neutral_price is None
    coordinator.price_planner.plan = PricePlan(
        status=PRICE_STATUS_WAITING, charge_now=False, current_price=0.30
    )

    await coordinator._async_enforce_grid_charge({"soc": 50, "smartmeter_power": 0})

    assert coordinator.sun_charge_active is False
    assert coordinator.price_charge_status == PRICE_STATUS_WAITING


async def test_grid_serving_takes_priority_over_price_charge_neutral_band(hass) -> None:
    """Netzdienliches Laden hat Vorrang vor preisoptimiertem Laden -
    einschließlich dessen Neutralpreis-Pausezone (siehe anforderung.yaml,
    REQ-DYNAMIC-PRICE-CHARGE sowie REQ-GRID-SERVING-CHARGE). Vorher blockierte
    die Pausezone netzdienliches Laden; das führte dazu, dass sich beide
    Automatiken gegenseitig ein- und ausschalten konnten, sobald ihre
    Bedingungen gleichzeitig erfüllt waren - jetzt weicht die Pausezone
    stattdessen dem aktiven Zeitfenster des netzdienlichen Ladens, und
    _async_step_grid_serving darf normal anlaufen."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        # smartmeter_power bewusst unterhalb des Schwellwerts (kein
        # bestätigter PV-Überschuss, der auch netzdienliches Laden selbst
        # ausbremsen würde) - storage_power_active löst netzdienliches Laden
        # in Schritt a aus (siehe _async_step_grid_serving).
        "smartmeter_power": 0,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await _enable_price_charge(coordinator)
    await coordinator.async_set_price_charge_max_price(0.20)
    await coordinator.async_set_price_charge_neutral_price(0.40)
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    coordinator.price_planner.plan = PricePlan(
        status=PRICE_STATUS_WAITING, charge_now=False, current_price=0.30
    )

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            await asyncio.sleep(0.1)
            # Zweiter Zyklus bestätigt die Zyklen-Hysterese von Schritt a
            # (PV_SURPLUS_HYSTERESIS_CYCLES) - der erste allein reicht noch
            # nicht, netzdienliches Laden aktiv zu übernehmen.
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)

        assert coordinator.grid_serving_active is True
        assert coordinator.sun_charge_active is True
        assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_GRID_SERVING
    finally:
        await coordinator.async_stop_sun_charge()


async def test_grid_serving_takes_priority_over_price_charge_active_charging(
    hass,
) -> None:
    """Netzdienliches Laden hat auch dann Vorrang, wenn preisoptimiertes
    Laden gerade aktiv aus dem Netz laden würde (price_plan.charge_now
    True) - nicht nur gegenüber der Neutralpreis-Pausezone. Ohne diesen
    Vorrang würde sich price_should_charge bei jedem Neuberechnungszyklus
    des Ladeplans (alle 60 s) mit dem netzdienlichen Laden abwechseln,
    sobald beide Bedingungen gleichzeitig erfüllt sind - z. B. an einem
    Sommermittag mit PV-Überschuss und gleichzeitig günstigem Netzpreis."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {
        "soc": 50,
        "ic_max_power_reference": 4600,
        "ic_timeout": 300,
        "smartmeter_power": 0,
        "storage_power_active": -(SMARTMETER_PV_SURPLUS_THRESHOLD_WATT + 50),
    }
    await _enable_price_charge(coordinator)
    await coordinator.async_set_grid_serving_start(dt_time(10, 0))
    await coordinator.async_set_grid_serving_end(dt_time(14, 0))
    coordinator.price_planner.plan = PricePlan(
        status=PRICE_STATUS_WAITING, charge_now=True, current_price=0.10
    )

    try:
        with _patched_now(12):
            await coordinator.async_set_grid_serving_enabled(True)
            await asyncio.sleep(0.1)
            # Zweiter Zyklus bestätigt die Zyklen-Hysterese von Schritt a
            # (PV_SURPLUS_HYSTERESIS_CYCLES) - der erste allein reicht noch
            # nicht, netzdienliches Laden aktiv zu übernehmen.
            await coordinator._async_enforce_grid_charge(coordinator.data)
            await asyncio.sleep(0.1)

        assert coordinator.grid_serving_active is True
        assert coordinator.price_charge_active is False
        assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_GRID_SERVING
    finally:
        await coordinator.async_stop_sun_charge()


async def test_timed_charge_takes_priority_over_price_charge(hass) -> None:
    """Beide zugleich (nur über force herstellbar): die Netzladung gewinnt,
    der Status des preisoptimierten Ladens benennt den Grund."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600, "ic_timeout": 300}
    await coordinator.async_set_max_soc(90)
    await coordinator.async_set_timed_charge_start(dt_time(1, 0))
    await coordinator.async_set_timed_charge_end(dt_time(5, 0))
    await coordinator.async_set_price_charge_strategy(PRICE_STRATEGY_RELATIVE)
    coordinator._price_charge_enabled = True
    coordinator._timed_charge_enabled = True
    coordinator.price_planner.plan = _charging_plan()

    try:
        with patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=datetime(2024, 1, 15, 2, 0),
        ):
            await coordinator._async_enforce_grid_charge({"soc": 50})

        assert coordinator._timed_charge_active is True
        assert coordinator.price_charge_active is False
        assert coordinator.price_charge_status == PRICE_STATUS_PAUSED_TIMED_CHARGE
    finally:
        await coordinator.async_stop_sun_charge()


async def test_price_charge_publishes_state_into_coordinator_data(hass) -> None:
    """Die Sensoren lesen den Zustand wie jeden anderen Messwert aus
    coordinator.data."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}
    await _enable_price_charge(coordinator)
    coordinator.price_planner.plan = _waiting_plan()

    data = {"soc": 50}
    await coordinator._async_enforce_grid_charge(data)
    coordinator._publish_charge_state(data)

    assert data["price_charge_active"] is False
    assert data["price_charge_status"] == PRICE_STATUS_WAITING
    assert data["price_charge_next_start"] == _local(20)
    assert data["price_charge_current_price"] == pytest.approx(0.32)


# -- Konflikt Netzladung <-> preisoptimiertes Laden -------------------------
async def test_enabling_price_charge_while_timed_charge_active_asks_first(
    hass,
) -> None:
    """Statt eines der beiden Features stillschweigend zu übersteuern, legt
    der Coordinator einen Bestätigungsdialog an und lehnt die Änderung
    vorerst ab."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50}
    await coordinator.async_set_timed_charge_enabled(True)

    applied = await coordinator.async_set_price_charge_enabled(True)

    assert applied is False
    assert coordinator.price_charge_enabled is False
    assert coordinator.timed_charge_enabled is True
    issue = ir.async_get(hass).async_get_issue(
        DOMAIN, f"{ISSUE_PRICE_CHARGE_CONFLICT}_test_entry_id"
    )
    assert issue is not None
    assert issue.is_fixable is True
    assert issue.data == {
        "entry_id": "test_entry_id",
        "issue_key": ISSUE_PRICE_CHARGE_CONFLICT,
    }
    notifications = hass.data.get(persistent_notification.DOMAIN, {})
    assert f"{DOMAIN}_test_entry_id_charge_conflict" in notifications


async def test_enabling_timed_charge_while_price_charge_active_asks_first(
    hass,
) -> None:
    """Gleiches Verhalten in der Gegenrichtung."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50}
    await coordinator.async_set_price_charge_enabled(True)

    applied = await coordinator.async_set_timed_charge_enabled(True)

    assert applied is False
    assert coordinator.timed_charge_enabled is False
    assert coordinator.price_charge_enabled is True
    assert (
        ir.async_get(hass).async_get_issue(
            DOMAIN, f"{ISSUE_TIMED_CHARGE_CONFLICT}_test_entry_id"
        )
        is not None
    )


async def test_force_swaps_the_two_grid_charging_features(hass) -> None:
    """force=True (Bestätigungsdialog, Service, Restore) schaltet das jeweils
    andere Feature ab, statt erneut nachzufragen."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50}
    await coordinator.async_set_timed_charge_enabled(True)

    applied = await coordinator.async_set_price_charge_enabled(True, force=True)

    assert applied is True
    assert coordinator.price_charge_enabled is True
    assert coordinator.timed_charge_enabled is False
    assert (
        ir.async_get(hass).async_get_issue(
            DOMAIN, f"{ISSUE_PRICE_CHARGE_CONFLICT}_test_entry_id"
        )
        is None
    )


async def test_turning_the_other_feature_off_clears_the_conflict_dialog(hass) -> None:
    """Löst der Anwender den Konflikt selbst auf, verschwindet die Rückfrage
    mitsamt Benachrichtigung."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50}
    await coordinator.async_set_timed_charge_enabled(True)
    await coordinator.async_set_price_charge_enabled(True)

    await coordinator.async_set_timed_charge_enabled(False)

    assert (
        ir.async_get(hass).async_get_issue(
            DOMAIN, f"{ISSUE_PRICE_CHARGE_CONFLICT}_test_entry_id"
        )
        is None
    )
    notifications = hass.data.get(persistent_notification.DOMAIN, {})
    assert f"{DOMAIN}_test_entry_id_charge_conflict" not in notifications


async def test_invalid_strategy_is_rejected(hass) -> None:
    from homeassistant.exceptions import HomeAssistantError

    coordinator = _make_coordinator(hass)

    with pytest.raises(HomeAssistantError):
        await coordinator.async_set_price_charge_strategy("gibt_es_nicht")


# -- Bestätigungsdialog (repairs.py) ----------------------------------------
def _register_coordinator(hass, coordinator: SaxPowerCoordinator) -> None:
    """Macht den Coordinator für den Repairs-Flow auffindbar (im echten
    Betrieb erledigt das async_setup_entry)."""
    hass.data.setdefault(DOMAIN, {})[coordinator.entry_id] = {
        DATA_COORDINATOR: coordinator
    }


async def test_repair_flow_confirm_swaps_the_active_feature(hass) -> None:
    """Bestätigen im Dialog schaltet die Netzladung ab und aktiviert das
    preisoptimierte Laden."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50}
    _register_coordinator(hass, coordinator)
    await coordinator.async_set_timed_charge_enabled(True)
    await coordinator.async_set_price_charge_enabled(True)

    flow = await async_create_fix_flow(
        hass,
        f"{ISSUE_PRICE_CHARGE_CONFLICT}_test_entry_id",
        {"entry_id": "test_entry_id", "issue_key": ISSUE_PRICE_CHARGE_CONFLICT},
    )
    flow.hass = hass
    menu = await flow.async_step_init()
    assert menu["type"] == FlowResultType.MENU
    assert menu["menu_options"] == ["confirm", "cancel"]

    result = await flow.async_step_confirm()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert coordinator.price_charge_enabled is True
    assert coordinator.timed_charge_enabled is False


async def test_repair_flow_cancel_leaves_everything_unchanged(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50}
    _register_coordinator(hass, coordinator)
    await coordinator.async_set_timed_charge_enabled(True)
    await coordinator.async_set_price_charge_enabled(True)

    flow = await async_create_fix_flow(
        hass,
        f"{ISSUE_PRICE_CHARGE_CONFLICT}_test_entry_id",
        {"entry_id": "test_entry_id", "issue_key": ISSUE_PRICE_CHARGE_CONFLICT},
    )
    flow.hass = hass
    result = await flow.async_step_cancel()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert coordinator.price_charge_enabled is False
    assert coordinator.timed_charge_enabled is True
    notifications = hass.data.get(persistent_notification.DOMAIN, {})
    assert f"{DOMAIN}_test_entry_id_charge_conflict" not in notifications


# -- Strategie-Select --------------------------------------------------------
def _prepare_entity(entity, hass, entity_id: str, last_state: State | None) -> None:
    entity.hass = hass
    entity.entity_id = entity_id
    entity.async_write_ha_state = MagicMock()
    entity.async_get_last_state = AsyncMock(return_value=last_state)


async def test_strategy_select_uses_options_default_on_fresh_install(hass) -> None:
    """Ohne gespeicherten Zustand gilt die im Options Flow hinterlegte
    Vorgabestrategie."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50}
    coordinator.options = {"price_strategy": PRICE_STRATEGY_SMART}
    entity = SaxPowerPriceStrategySelect(coordinator, "test_entry_id")
    _prepare_entity(entity, hass, "select.test_strategy", None)

    await entity.async_added_to_hass()
    # async_added_to_hass abonniert die Entity beim Coordinator und startet
    # damit dessen Poll-Timer - ohne Shutdown bliebe er nach dem Test hängen
    # (siehe die coordinator-Fixture in tests/test_number.py).
    await coordinator.async_shutdown()

    assert coordinator.price_charge_strategy == PRICE_STRATEGY_SMART
    assert entity.current_option == PRICE_STRATEGY_SMART


async def test_strategy_select_restores_previous_state(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50}
    entity = SaxPowerPriceStrategySelect(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "select.test_strategy",
        State("select.test_strategy", PRICE_STRATEGY_ABSOLUTE),
    )

    await entity.async_added_to_hass()
    # async_added_to_hass abonniert die Entity beim Coordinator und startet
    # damit dessen Poll-Timer - ohne Shutdown bliebe er nach dem Test hängen
    # (siehe die coordinator-Fixture in tests/test_number.py).
    await coordinator.async_shutdown()

    assert coordinator.price_charge_strategy == PRICE_STRATEGY_ABSOLUTE


async def test_strategy_select_ignores_unknown_restored_state(hass) -> None:
    """Ein "unknown"/"unavailable"-Zustand (z. B. nach einem Absturz) darf
    nicht als Strategie durchgereicht werden."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50}
    entity = SaxPowerPriceStrategySelect(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "select.test_strategy",
        State("select.test_strategy", "unknown"),
    )

    await entity.async_added_to_hass()
    # async_added_to_hass abonniert die Entity beim Coordinator und startet
    # damit dessen Poll-Timer - ohne Shutdown bliebe er nach dem Test hängen
    # (siehe die coordinator-Fixture in tests/test_number.py).
    await coordinator.async_shutdown()

    assert coordinator.price_charge_strategy == PRICE_STRATEGY_OFF


# -- Hauptschalter -----------------------------------------------------------
async def test_price_charge_switch_restore_does_not_ask_for_confirmation(
    hass,
) -> None:
    """Beim Wiederherstellen darf kein Bestätigungsdialog aufpoppen - der
    Anwender hat gerade nichts angeklickt."""
    coordinator = _make_coordinator(hass)
    coordinator.data = {"soc": 50}
    entity = SaxPowerPriceChargeSwitch(coordinator, "test_entry_id")
    _prepare_entity(
        entity,
        hass,
        "switch.test_price_charge",
        State("switch.test_price_charge", "on"),
    )

    await entity.async_added_to_hass()
    # async_added_to_hass abonniert die Entity beim Coordinator und startet
    # damit dessen Poll-Timer - ohne Shutdown bliebe er nach dem Test hängen
    # (siehe die coordinator-Fixture in tests/test_number.py).
    await coordinator.async_shutdown()

    assert coordinator.price_charge_enabled is True
    assert (
        ir.async_get(hass).async_get_issue(
            DOMAIN, f"{ISSUE_PRICE_CHARGE_CONFLICT}_test_entry_id"
        )
        is None
    )
