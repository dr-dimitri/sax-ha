"""Regression tests for REQ-ECONOMICS-ACCOUNTING balance persistence.

Store-Level-Tests (Round-Trip, unabhängige Feldvalidierung, korrupte/
rückläufige Snapshots, zwei Config Entries, Drosselung/Sofort-Flush) sowie
der Coordinator-seitige Bootstrap/Shutdown-Lebenszyklus. Die reine
Geldbilanz selbst (compute_economics_delta) ist in
tests/test_economics_accounting.py getestet; die volle Verdrahtung inkl.
Rundung und SOC-Minimum-Korrektur in tests/test_coordinator.py.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_INVESTMENT_COST,
    CONF_ECONOMICS_TARIFF_TYPE,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.economics_amortization import (
    MAX_STORED_DAYS,
    DayEconomicsResult,
)
from custom_components.sax_power.domain.tariff import TariffType
from custom_components.sax_power.infrastructure.economics_store import (
    ECONOMICS_SAVE_DELAY,
    STORAGE_KEY_PREFIX,
    EconomicsState,
    EconomicsStateStore,
)

FIXED_TARIFF_OPTIONS = {
    CONF_ECONOMICS_TARIFF_TYPE: TariffType.FIXED.value,
    CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.30,
}


def _coordinator(hass, entry_id: str = "entry", options: dict | None = None):
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    return SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id=entry_id,
        options=options or {},
    )


def _full_state(started_at, **overrides) -> EconomicsState:
    values = {
        "grid_charge_cost_eur": 10.0,
        "pv_opportunity_cost_eur": 2.0,
        "avoided_grid_cost_eur": 5.0,
        "operating_result_high_water_eur": 4.0,
        "unvalued_inventory_kwh": 3.0,
        "unpriced_charge_kwh": 1.0,
        "unpriced_discharge_kwh": 0.5,
        "economics_started_at": started_at,
    }
    values.update(overrides)
    return EconomicsState(**values)


def _stub_store_with_initial_data(
    store: EconomicsStateStore, initial: dict | None = None
) -> dict:
    """Ersetzt Store.async_save/async_load durch ein In-Memory-Paar, das
    sich wie ein immer erfolgreicher echter Store verhält: async_load
    liefert stets exakt das zurück, was zuletzt über async_save
    geschrieben wurde (oder `initial`, solange noch nichts geschrieben
    wurde). Isoliert diese Tests bewusst von echten Festplattenzugriffen,
    ohne dabei die Lese-Rückprobe aus
    EconomicsStateStore._write_and_verify zu umgehen (siehe
    test_a_silently_swallowed_write_error_is_detected_via_readback, die
    genau diese Rückprobe gezielt fehlschlagen lässt)."""
    current = dict(initial or {})

    async def _save(data):
        current.clear()
        current.update(data)

    async def _load():
        return dict(current)

    store._store.async_save = AsyncMock(side_effect=_save)
    store._store.async_load = AsyncMock(side_effect=_load)
    return current


def _seed_real_store(
    hass_storage, entry_id: str, payload: dict, *, version: int, minor_version: int
) -> None:
    """Legt einen echten Store-Envelope aus einer älteren Version an."""
    hass_storage[f"{STORAGE_KEY_PREFIX}.{entry_id}"] = {
        "version": version,
        "minor_version": minor_version,
        "key": f"{STORAGE_KEY_PREFIX}.{entry_id}",
        "data": payload,
    }


# --------------------------------------------------------------------------
# Store: Round-Trip und unabhängige Feldvalidierung
# --------------------------------------------------------------------------
async def test_store_round_trips_the_full_balance(hass) -> None:
    started_at = dt_util.utcnow()
    revised_at = started_at + timedelta(hours=2)
    store = EconomicsStateStore(hass, "roundtrip")
    state = _full_state(started_at, last_tariff_revision_at=revised_at)

    assert await store.async_save(state) is True
    loaded = await EconomicsStateStore(hass, "roundtrip").async_load()

    assert loaded == state
    assert loaded.initialized is True


async def test_store_allows_negative_money_sums(hass) -> None:
    """Negative Strompreise dürfen die Geldsummen negativ werden lassen -
    das ist kein Korruptionsindiz."""
    started_at = dt_util.utcnow()
    store = EconomicsStateStore(hass, "negative")
    state = _full_state(
        started_at, grid_charge_cost_eur=-4.5, avoided_grid_cost_eur=-1.0
    )

    assert await store.async_save(state) is True
    loaded = await EconomicsStateStore(hass, "negative").async_load()

    assert loaded.grid_charge_cost_eur == -4.5
    assert loaded.avoided_grid_cost_eur == -1.0


async def test_store_rejects_non_finite_money_amount(hass, caplog) -> None:
    store = EconomicsStateStore(hass, "nan")
    store._store.async_load = AsyncMock(
        return_value={
            **EconomicsStateStore._serialize(_full_state(dt_util.utcnow())),
            "grid_charge_cost_eur": float("nan"),
        }
    )

    loaded = await store.async_load()

    assert loaded.grid_charge_cost_eur is None
    assert "Ungültigen gespeicherten Betrag für Netzladekosten" in caplog.text


async def test_store_rejects_a_regressive_decrease_in_a_monotonic_field(
    hass, caplog
) -> None:
    """unpriced_charge_kwh ist eine echte kumulierte Menge und bleibt
    monoton - anders als die drei Geldsummen."""
    started_at = dt_util.utcnow()
    store = EconomicsStateStore(hass, "regressive")
    _stub_store_with_initial_data(store)
    assert (
        await store.async_save(_full_state(started_at, unpriced_charge_kwh=5.0)) is True
    )

    regressive = _full_state(started_at, unpriced_charge_kwh=4.0)
    assert await store.async_save(regressive) is False
    assert store._store.async_save.await_count == 1
    assert "Rückläufigen Wirtschaftlichkeits-Snapshot für Unbepreiste Ladung" in (
        caplog.text
    )


async def test_store_rejects_a_regressive_net_savings_high_water(hass, caplog) -> None:
    started_at = dt_util.utcnow()
    store = EconomicsStateStore(hass, "savings-regressive")
    _stub_store_with_initial_data(store)
    assert (
        await store.async_save(
            _full_state(started_at, operating_result_high_water_eur=100.0)
        )
        is True
    )

    assert (
        await store.async_save(
            _full_state(started_at, operating_result_high_water_eur=80.0)
        )
        is False
    )
    assert "Rückläufigen Wirtschaftlichkeits-Snapshot für " in caplog.text
    assert "Netto-Ersparnis-Höchststand" in caplog.text


async def test_store_permits_the_inventory_gauge_to_decrease(hass) -> None:
    """unvalued_inventory_kwh ist ein Bestand (Gauge) - Entladung und die
    SOC-Minimum-Korrektur lassen ihn sinken, das ist keine Regression."""
    started_at = dt_util.utcnow()
    store = EconomicsStateStore(hass, "inventory-gauge")
    _stub_store_with_initial_data(store)
    assert (
        await store.async_save(_full_state(started_at, unvalued_inventory_kwh=5.0))
        is True
    )

    assert (
        await store.async_save(_full_state(started_at, unvalued_inventory_kwh=0.0))
        is True
    )


async def test_store_rejects_a_changed_activation_timestamp(hass, caplog) -> None:
    """economics_started_at ist eine einmalig gesetzte Konstante."""
    first = dt_util.utcnow()
    second = first + timedelta(days=1)
    store = EconomicsStateStore(hass, "started-at-drift")
    _stub_store_with_initial_data(store)
    assert await store.async_save(_full_state(first)) is True

    assert await store.async_save(_full_state(second)) is False
    assert store._store.async_save.await_count == 1
    assert "Abweichenden Aktivierungszeitpunkt" in caplog.text


async def test_store_drops_only_the_invalid_field(hass, caplog) -> None:
    store = EconomicsStateStore(hass, "partial-invalid")
    store._store.async_load = AsyncMock(
        return_value={
            **EconomicsStateStore._serialize(_full_state(dt_util.utcnow())),
            "unvalued_inventory_kwh": -1,
        }
    )

    loaded = await store.async_load()

    assert loaded.unvalued_inventory_kwh is None
    assert loaded.grid_charge_cost_eur == 10.0
    assert loaded.initialized is False
    assert "Ungültigen gespeicherten Wert für Unbewerteter Bestand" in caplog.text


async def test_store_recovers_after_an_incomplete_bundle(hass) -> None:
    """Nach einem unvollständigen Bündel darf der vom Coordinator neu
    gestartete 0/0/0-Stand nicht an der alten Teil-Baseline scheitern
    (analog zu EnergyStateStore, REQ-ENERGY-ORIGIN)."""
    old_started_at = dt_util.utcnow() - timedelta(days=1)
    store = EconomicsStateStore(hass, "recovery")
    _stub_store_with_initial_data(
        store,
        {
            **EconomicsStateStore._serialize(_full_state(old_started_at)),
            "unvalued_inventory_kwh": -1,  # macht das Bündel unvollständig
        },
    )

    loaded = await store.async_load()
    assert loaded.initialized is False

    restarted = _full_state(
        dt_util.utcnow(),
        grid_charge_cost_eur=0.0,
        pv_opportunity_cost_eur=0.0,
        avoided_grid_cost_eur=0.0,
        unvalued_inventory_kwh=2.0,
        unpriced_charge_kwh=0.0,
        unpriced_discharge_kwh=0.0,
    )
    assert await store.async_save(restarted) is True


async def test_store_recovers_after_an_incomplete_bundle_with_priced_counters(
    hass,
) -> None:
    """Auch die beiden priced_*-Zähler müssen dabei aus der Baseline
    fallen: Sie gehören nicht zu `initialized` (sie kamen später dazu),
    unterliegen in _accept aber derselben Monotonieprüfung wie die
    unpriced_*-Zähler. Blieben sie stehen, während der Coordinator bei 0
    neu startet, würde jeder Speicherversuch als "rückläufig" abgelehnt -
    die Bilanz fröre dauerhaft in storage_error ein, und ein Reload hülfe
    nicht, weil die Datei unverändert bleibt."""
    old_started_at = dt_util.utcnow() - timedelta(days=1)
    store = EconomicsStateStore(hass, "recovery-priced")
    _stub_store_with_initial_data(
        store,
        {
            **EconomicsStateStore._serialize(
                _full_state(
                    old_started_at,
                    priced_charge_kwh=40.0,
                    priced_discharge_kwh=30.0,
                )
            ),
            "unvalued_inventory_kwh": -1,  # macht das Bündel unvollständig
        },
    )

    loaded = await store.async_load()
    assert loaded.initialized is False
    assert loaded.priced_charge_kwh == 40.0  # der Aufrufer sieht ihn weiter

    restarted = _full_state(
        dt_util.utcnow(),
        grid_charge_cost_eur=0.0,
        pv_opportunity_cost_eur=0.0,
        avoided_grid_cost_eur=0.0,
        unvalued_inventory_kwh=2.0,
        unpriced_charge_kwh=0.0,
        unpriced_discharge_kwh=0.0,
        priced_charge_kwh=0.0,
        priced_discharge_kwh=0.0,
    )
    assert await store.async_save(restarted) is True


async def test_store_restores_two_config_entries_independently(hass) -> None:
    first_started = dt_util.utcnow()
    second_started = first_started + timedelta(days=1)
    first = EconomicsStateStore(hass, "econ-first")
    second = EconomicsStateStore(hass, "econ-second")
    await first.async_save(_full_state(first_started, grid_charge_cost_eur=1.0))
    await second.async_save(_full_state(second_started, grid_charge_cost_eur=9.0))

    loaded_first = await EconomicsStateStore(hass, "econ-first").async_load()
    loaded_second = await EconomicsStateStore(hass, "econ-second").async_load()

    assert loaded_first.grid_charge_cost_eur == 1.0
    assert loaded_first.economics_started_at == first_started
    assert loaded_second.grid_charge_cost_eur == 9.0
    assert loaded_second.economics_started_at == second_started


# --------------------------------------------------------------------------
# Store: Tages-Buckets/Payback (REQ-ECONOMICS-AMORTIZATION)
# --------------------------------------------------------------------------
async def test_store_round_trips_day_results_current_day_and_payback(hass) -> None:
    started_at = dt_util.utcnow()
    payback_at = started_at + timedelta(days=200)
    day_one = DayEconomicsResult(
        day=date(2026, 3, 9),
        operating_result_eur=1.5,
        priced_charge_kwh=2.0,
        unpriced_charge_kwh=0.5,
        priced_discharge_kwh=1.0,
        unpriced_discharge_kwh=0.0,
        observed_seconds=86_400.0,
        day_length_seconds=86_400.0,
    )
    # Ein DST-Tag (25 h) mit einer Lücke: beide Werte müssen den
    # Round-Trip unverfälscht überstehen, sonst würde die Zeitabdeckung
    # nach einem Neustart anders bewertet als davor.
    day_two = DayEconomicsResult(
        day=date(2026, 3, 10),
        operating_result_eur=0.5,
        priced_charge_kwh=0.0,
        unpriced_charge_kwh=0.0,
        priced_discharge_kwh=0.5,
        unpriced_discharge_kwh=0.5,
        observed_seconds=80_000.0,
        day_length_seconds=90_000.0,
    )
    store = EconomicsStateStore(hass, "amortization-roundtrip")
    state = _full_state(
        started_at,
        day_results=(day_one, day_two),
        current_day=date(2026, 3, 11),
        current_day_operating_result_eur=0.25,
        current_day_priced_charge_kwh=0.1,
        current_day_unpriced_charge_kwh=0.2,
        current_day_priced_discharge_kwh=0.3,
        current_day_unpriced_discharge_kwh=0.4,
        current_day_observed_seconds=1_800.0,
        payback_achieved_at=payback_at,
    )

    assert await store.async_save(state) is True
    loaded = await EconomicsStateStore(hass, "amortization-roundtrip").async_load()

    assert loaded == state
    assert loaded.day_results == (day_one, day_two)
    assert loaded.current_day == date(2026, 3, 11)
    assert loaded.payback_achieved_at == payback_at


async def test_store_rejects_negative_savings_in_day_history(hass, caplog) -> None:
    day = DayEconomicsResult(
        day=date(2026, 3, 10),
        operating_result_eur=-0.5,
        priced_charge_kwh=0.0,
        unpriced_charge_kwh=0.0,
        priced_discharge_kwh=0.5,
        unpriced_discharge_kwh=0.0,
    )
    store = EconomicsStateStore(hass, "negative-day-savings")
    store._store.async_load = AsyncMock(
        return_value=EconomicsStateStore._serialize(
            _full_state(dt_util.utcnow(), day_results=(day,))
        )
    )

    loaded = await store.async_load()

    assert loaded.day_results == ()
    assert "Ungültigen gespeicherten Wert für Tagesergebnis" in caplog.text


async def test_store_drops_only_the_single_invalid_day_entry(hass, caplog) -> None:
    """Ein Tag ist ein eigenes atomares Bündel - ein kaputter Eintrag
    verwirft nur sich selbst, nicht die restliche Historie."""
    good_day = DayEconomicsResult(
        day=date(2026, 3, 9),
        operating_result_eur=1.0,
        priced_charge_kwh=1.0,
        unpriced_charge_kwh=0.0,
        priced_discharge_kwh=0.0,
        unpriced_discharge_kwh=0.0,
    )
    store = EconomicsStateStore(hass, "day-partial-invalid")
    serialized = EconomicsStateStore._serialize(
        _full_state(dt_util.utcnow(), day_results=(good_day,))
    )
    serialized["day_results"].append(
        {
            "day": date(2026, 3, 10).isoformat(),
            "operating_result_eur": 1.0,
            "priced_charge_kwh": -1,  # ungültig: negativ
            "unpriced_charge_kwh": 0.0,
            "priced_discharge_kwh": 0.0,
            "unpriced_discharge_kwh": 0.0,
        }
    )
    store._store.async_load = AsyncMock(return_value=serialized)

    loaded = await store.async_load()

    assert loaded.day_results == (good_day,)
    assert "Unvollständigen Tageseintrag verworfen" in caplog.text


async def test_store_drops_the_whole_current_day_bundle_if_one_field_is_invalid(
    hass, caplog
) -> None:
    """current_day und seine vier Zähler sind ein gemeinsames Bündel -
    fehlt/ist nur eines ungültig, gilt der ganze laufende Tag als nicht
    aussagekräftig (die abgeschlossene Historie bleibt davon unberührt)."""
    store = EconomicsStateStore(hass, "current-day-partial-invalid")
    serialized = EconomicsStateStore._serialize(
        _full_state(
            dt_util.utcnow(),
            current_day=date(2026, 3, 11),
            current_day_operating_result_eur=0.25,
            current_day_priced_charge_kwh=0.1,
            current_day_unpriced_charge_kwh=0.2,
            current_day_priced_discharge_kwh=0.3,
            current_day_unpriced_discharge_kwh=0.4,
        )
    )
    serialized["current_day_priced_charge_kwh"] = -1  # ungültig: negativ
    store._store.async_load = AsyncMock(return_value=serialized)

    loaded = await store.async_load()

    assert loaded.current_day is None
    assert loaded.current_day_operating_result_eur is None
    assert loaded.current_day_priced_charge_kwh is None
    assert loaded.current_day_unpriced_charge_kwh is None
    assert loaded.current_day_priced_discharge_kwh is None
    assert loaded.current_day_unpriced_discharge_kwh is None
    assert "Ungültigen gespeicherten Wert für Laufende bepreiste Ladung" in caplog.text


async def test_store_treats_a_day_without_observed_time_as_incomplete(hass) -> None:
    """Ein Store aus der Zeit vor der Zeitabdeckung (Issue #131) kennt
    observed_seconds/day_length_seconds noch nicht. Solche Tage bleiben als
    Historie erhalten, gelten aber als unvollständig beobachtet - sie
    dürfen keine Prognose tragen, für die nie eine Beobachtungsdauer
    gemessen wurde."""
    store = EconomicsStateStore(hass, "day-legacy-without-observed")
    serialized = EconomicsStateStore._serialize(_full_state(dt_util.utcnow()))
    serialized["day_results"] = [
        {
            "day": date(2026, 3, 9).isoformat(),
            "operating_result_eur": 1.0,
            "priced_charge_kwh": 1.0,
            "unpriced_charge_kwh": 0.0,
            "priced_discharge_kwh": 1.0,
            "unpriced_discharge_kwh": 0.0,
        }
    ]
    store._store.async_load = AsyncMock(return_value=serialized)

    loaded = await store.async_load()

    assert len(loaded.day_results) == 1
    assert loaded.day_results[0].observed_seconds == 0.0
    assert loaded.day_results[0].is_fully_observed is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("observed_seconds", -1.0),  # ungültig: negativ
        ("day_length_seconds", 0.0),  # ungültig: als Nenner unbrauchbar
        ("day_length_seconds", "24h"),  # ungültig: kein Zahlenwert
    ],
)
async def test_store_drops_a_day_with_an_invalid_time_coverage(
    hass, caplog, field, value
) -> None:
    """Ein VORHANDENER, aber ungültiger Wert bleibt ein Korruptionsindiz
    und verwirft den ganzen Tag - anders als ein schlicht fehlendes Feld
    aus einem älteren Store."""
    store = EconomicsStateStore(hass, f"day-invalid-{field}-{value}")
    serialized = EconomicsStateStore._serialize(_full_state(dt_util.utcnow()))
    entry = {
        "day": date(2026, 3, 9).isoformat(),
        "operating_result_eur": 1.0,
        "priced_charge_kwh": 1.0,
        "unpriced_charge_kwh": 0.0,
        "priced_discharge_kwh": 1.0,
        "unpriced_discharge_kwh": 0.0,
        "observed_seconds": 86_400.0,
        "day_length_seconds": 86_400.0,
    }
    entry[field] = value
    serialized["day_results"] = [entry]
    store._store.async_load = AsyncMock(return_value=serialized)

    loaded = await store.async_load()

    assert loaded.day_results == ()
    assert "Unvollständigen Tageseintrag verworfen" in caplog.text


async def test_store_drops_the_current_day_without_an_observed_duration(hass) -> None:
    """Die beobachtete Dauer gehört zum Bündel des laufenden Tages: ohne
    sie ließe sich der Tag nur mit einer erfundenen Abdeckung abschließen.
    Betroffen ist ausschließlich der ohnehin unvollständige laufende Tag,
    nicht die abgeschlossene Historie."""
    store = EconomicsStateStore(hass, "current-day-legacy-without-observed")
    serialized = EconomicsStateStore._serialize(
        _full_state(
            dt_util.utcnow(),
            current_day=date(2026, 3, 11),
            current_day_operating_result_eur=0.25,
            current_day_priced_charge_kwh=0.1,
            current_day_unpriced_charge_kwh=0.2,
            current_day_priced_discharge_kwh=0.3,
            current_day_unpriced_discharge_kwh=0.4,
            current_day_observed_seconds=1_800.0,
        )
    )
    del serialized["current_day_observed_seconds"]
    store._store.async_load = AsyncMock(return_value=serialized)

    loaded = await store.async_load()

    assert loaded.current_day is None
    assert loaded.current_day_observed_seconds is None
    assert loaded.current_day_operating_result_eur is None


async def test_store_caps_day_results_at_max_stored_days(hass) -> None:
    """Verteidigung gegen einen von Hand über MAX_STORED_DAYS hinaus
    erweiterten Store - im Normalbetrieb trimmt bereits der Coordinator
    beim Anhängen eines neuen Tages."""
    days = tuple(
        DayEconomicsResult(
            day=date(2026, 1, 1) + timedelta(days=offset),
            operating_result_eur=1.0,
            priced_charge_kwh=0.0,
            unpriced_charge_kwh=0.0,
            priced_discharge_kwh=0.0,
            unpriced_discharge_kwh=0.0,
        )
        for offset in range(MAX_STORED_DAYS + 5)
    )
    store = EconomicsStateStore(hass, "day-results-cap")
    serialized = EconomicsStateStore._serialize(
        _full_state(dt_util.utcnow(), day_results=days)
    )
    store._store.async_load = AsyncMock(return_value=serialized)

    loaded = await store.async_load()

    assert len(loaded.day_results) == MAX_STORED_DAYS
    # Die ältesten Tage sind verworfen, die jüngsten bleiben erhalten.
    assert loaded.day_results[-1].day == days[-1].day
    assert loaded.day_results[0].day == days[5].day


async def test_store_rejects_a_changed_payback_achieved_at(hass, caplog) -> None:
    """payback_achieved_at ist wie economics_started_at eine einmalig
    gesetzte Konstante (Regel 8)."""
    started_at = dt_util.utcnow()
    first = started_at + timedelta(days=100)
    second = started_at + timedelta(days=150)
    store = EconomicsStateStore(hass, "payback-drift")
    _stub_store_with_initial_data(store)
    assert (
        await store.async_save(_full_state(started_at, payback_achieved_at=first))
        is True
    )

    assert (
        await store.async_save(_full_state(started_at, payback_achieved_at=second))
        is False
    )
    assert store._store.async_save.await_count == 1
    assert "Abweichenden Payback-Erreichungszeitpunkt" in caplog.text


# --------------------------------------------------------------------------
# Store: Preisabdeckungszähler (REQ-ECONOMICS-OBSERVABILITY)
# --------------------------------------------------------------------------
async def test_store_round_trips_priced_amounts(hass) -> None:
    started_at = dt_util.utcnow()
    store = EconomicsStateStore(hass, "priced-roundtrip")
    state = _full_state(started_at, priced_charge_kwh=3.0, priced_discharge_kwh=2.5)

    assert await store.async_save(state) is True
    loaded = await EconomicsStateStore(hass, "priced-roundtrip").async_load()

    assert loaded.priced_charge_kwh == 3.0
    assert loaded.priced_discharge_kwh == 2.5


async def test_store_rejects_a_regressive_priced_amount(hass, caplog) -> None:
    """priced_charge_kwh/priced_discharge_kwh sind wie unpriced_*
    kumulierte Mengen und bleiben monoton."""
    started_at = dt_util.utcnow()
    store = EconomicsStateStore(hass, "priced-regressive")
    _stub_store_with_initial_data(store)
    assert (
        await store.async_save(_full_state(started_at, priced_charge_kwh=5.0)) is True
    )

    assert (
        await store.async_save(_full_state(started_at, priced_charge_kwh=4.0)) is False
    )
    assert store._store.async_save.await_count == 1
    assert "Rückläufigen Wirtschaftlichkeits-Snapshot für Bepreiste Ladung" in (
        caplog.text
    )


async def test_store_reset_bypasses_the_monotonicity_baseline(hass) -> None:
    """async_reset (sax_power.restart_economics_accounting) darf die sonst
    zu Recht geschützten monotonen Zähler und unveränderlichen Zeitstempel
    bewusst zurücksetzen."""
    started_at = dt_util.utcnow()
    store = EconomicsStateStore(hass, "reset-bypass")
    assert (
        await store.async_save(
            _full_state(
                started_at,
                operating_result_high_water_eur=100.0,
                unpriced_charge_kwh=5.0,
                priced_charge_kwh=5.0,
                payback_achieved_at=started_at,
            )
        )
        is True
    )

    new_started_at = started_at + timedelta(days=1)
    reset_state = _full_state(
        new_started_at,
        operating_result_high_water_eur=0.0,
        unpriced_charge_kwh=0.0,
        priced_charge_kwh=0.0,
        payback_achieved_at=None,
    )
    assert await store.async_reset(reset_state) is True

    loaded = await EconomicsStateStore(hass, "reset-bypass").async_load()
    assert loaded.economics_started_at == new_started_at
    assert loaded.operating_result_high_water_eur == 0.0
    assert loaded.unpriced_charge_kwh == 0.0
    assert loaded.priced_charge_kwh == 0.0
    assert loaded.payback_achieved_at is None


async def test_store_reset_still_rejects_a_structurally_invalid_snapshot(hass) -> None:
    """async_reset überspringt nur die Baseline-Vergleiche, nicht die
    grundsätzliche Wertebereichsprüfung - ein Programmierfehler darf keinen
    korrupten Store erzeugen."""
    store = EconomicsStateStore(hass, "reset-invalid")
    store._store.async_save = AsyncMock()

    assert (
        await store.async_reset(_full_state(dt_util.utcnow(), priced_charge_kwh=-1.0))
        is False
    )
    store._store.async_save.assert_not_called()


async def test_store_rejects_a_negative_net_savings_high_water(hass) -> None:
    store = EconomicsStateStore(hass, "negative-savings")
    store._store.async_save = AsyncMock()

    assert (
        await store.async_reset(
            _full_state(dt_util.utcnow(), operating_result_high_water_eur=-0.01)
        )
        is False
    )
    store._store.async_save.assert_not_called()


async def test_store_throttles_frequent_updates_and_keeps_newest_state(hass) -> None:
    """Zwei rasch aufeinanderfolgende async_delay_save-Aufrufe planen nur
    EINEN eigenen async_call_later-Timer (siehe EconomicsStateStore,
    kein Store.async_delay_save mehr - das würde einen echten
    Schreibfehler nicht beobachtbar machen, siehe Klassen-Docstring); nach
    Ablauf der Verzögerung wird genau einmal geschrieben, mit dem
    zuletzt koaleszierten Stand."""
    store = EconomicsStateStore(hass, "throttled")
    written = _stub_store_with_initial_data(store)
    started_at = dt_util.utcnow()

    assert store.async_delay_save(_full_state(started_at, grid_charge_cost_eur=1.0))
    assert store.async_delay_save(_full_state(started_at, grid_charge_cost_eur=1.5))

    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=ECONOMICS_SAVE_DELAY + 1)
    )
    await hass.async_block_till_done()

    assert store._store.async_save.await_count == 1
    assert written["grid_charge_cost_eur"] == 1.5


async def test_store_final_flush_writes_newest_state_immediately(hass) -> None:
    """async_save schreibt sofort den übergebenen Stand und storniert einen
    zuvor über async_delay_save geplanten Timer - der darf danach nicht
    doch noch feuern und den frisch geschriebenen Stand mit dem alten,
    koaleszierten Wert überschreiben."""
    store = EconomicsStateStore(hass, "flush")
    written = _stub_store_with_initial_data(store)
    started_at = dt_util.utcnow()
    store.async_delay_save(_full_state(started_at, grid_charge_cost_eur=1.0))

    assert await store.async_save(_full_state(started_at, grid_charge_cost_eur=2.0))
    assert store._store.async_save.await_count == 1
    assert written["grid_charge_cost_eur"] == 2.0

    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=ECONOMICS_SAVE_DELAY + 1)
    )
    await hass.async_block_till_done()
    assert store._store.async_save.await_count == 1
    assert written["grid_charge_cost_eur"] == 2.0


async def test_concurrent_writes_do_not_falsely_fail_the_readback(hass) -> None:
    """REQ-ECONOMICS-OBSERVABILITY-Review: zwei überlappende
    Schreibversuche (z. B. ein bereits laufender verzögerter Write und ein
    parallel gestarteter async_reset/Shutdown-Flush) dürfen sich die
    save-then-load-Sequenz aus _write_and_verify nicht gegenseitig
    verfälschen.

    Nachgebildet wird genau das Verhalten des echten
    homeassistant.helpers.storage.Store: `self._data` wird beim Aufruf von
    async_save() SOFORT (unabhängig von einem eventuell noch laufenden
    anderen Schreibvorgang) überschrieben, bevor der eigentliche
    Schreibvorgang serialisiert (Store._write_lock) startet - siehe
    Store.async_save/_async_handle_write_data. Ohne ein eigenes Lock in
    EconomicsStateStore, das die gesamte save-then-load-Sequenz pro
    Instanz seriealisiert, sieht der erste Aufrufer beim Rücklesen die
    bereits gesetzten, aber noch nicht geschriebenen Daten des zweiten
    Aufrufers und meldet fälschlich einen Fehlschlag - obwohl sein
    eigener Schreibvorgang tatsächlich erfolgreich war."""

    class _RacingFakeStore:
        """Minimalnachbildung von Store._data/_write_lock/async_load, die
        genau die für diesen Test relevante Race-Bedingung reproduziert."""

        def __init__(self) -> None:
            self._data: dict | None = None
            self._disk: dict | None = None
            self._write_lock = asyncio.Lock()

        async def async_save(self, data: dict) -> None:
            self._data = data
            async with self._write_lock:
                if self._data is None:
                    return
                taken = self._data
                self._data = None
                await asyncio.sleep(0)
                self._disk = taken

        async def async_load(self) -> dict | None:
            if self._data is not None:
                return dict(self._data)
            return dict(self._disk) if self._disk is not None else None

    store = EconomicsStateStore(hass, "racing")
    store._store = _RacingFakeStore()
    started_at = dt_util.utcnow()

    first_state = _full_state(started_at, grid_charge_cost_eur=1.0)
    second_state = _full_state(started_at, grid_charge_cost_eur=2.0)

    first_result, second_result = await asyncio.gather(
        store.async_reset(first_state),
        store.async_save(second_state),
    )

    assert first_result is True
    assert second_result is True


# trotzdem erkannt werden - Store._async_handle_write_data fängt eine
# echte WriteError/SerializationError ab und kehrt regulär zurück, ohne
# sie an den Aufrufer weiterzureichen. Simuliert hier, indem
# Store.async_save zu einem No-Op wird (wie beim echten, verschluckten
# Fehler) und Store.async_load weiterhin den alten Stand liefert.
# --------------------------------------------------------------------------
async def test_a_silently_swallowed_final_write_error_is_detected_via_readback(
    hass,
) -> None:
    store = EconomicsStateStore(hass, "swallowed-final")
    store._store.async_save = AsyncMock()  # No-Op wie bei verschluckter WriteError
    store._store.async_load = AsyncMock(return_value={"stale": True})

    assert await store.async_save(_full_state(dt_util.utcnow())) is False


async def test_a_silently_swallowed_reset_write_error_is_detected_via_readback(
    hass,
) -> None:
    """Direkte Absicherung des vom Review gemeldeten Szenarios: ein
    restart_economics_accounting darf nicht als erfolgreich gelten, wenn
    der Reset in Wahrheit nicht auf der Platte gelandet ist."""
    store = EconomicsStateStore(hass, "swallowed-reset")
    store._store.async_save = AsyncMock()
    store._store.async_load = AsyncMock(return_value={"stale": True})

    assert await store.async_reset(_full_state(dt_util.utcnow())) is False


async def test_a_silently_swallowed_delayed_write_error_invokes_the_callback(
    hass,
) -> None:
    """Der zeitversetzte Pfad hat keinen Aufrufer mehr, der auf einen
    Rückgabewert wartet - ein erst nach der Verzögerung erkannter
    Fehlschlag muss deshalb über on_persist_failed gemeldet werden."""
    failures = []
    store = EconomicsStateStore(
        hass, "swallowed-delayed", on_persist_failed=lambda: failures.append(True)
    )
    store._store.async_save = AsyncMock()
    store._store.async_load = AsyncMock(return_value={"stale": True})

    assert store.async_delay_save(_full_state(dt_util.utcnow())) is True
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=ECONOMICS_SAVE_DELAY + 1)
    )
    await hass.async_block_till_done()

    assert failures == [True]


async def test_a_successful_delayed_write_never_invokes_the_callback(hass) -> None:
    failures = []
    store = EconomicsStateStore(
        hass, "successful-delayed", on_persist_failed=lambda: failures.append(True)
    )
    _stub_store_with_initial_data(store)

    assert store.async_delay_save(_full_state(dt_util.utcnow())) is True
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=ECONOMICS_SAVE_DELAY + 1)
    )
    await hass.async_block_till_done()

    assert failures == []


async def test_coordinator_freezes_the_balance_when_a_delayed_write_is_silently_lost(
    hass,
) -> None:
    """End-to-End durch die echte EconomicsStateStore (nicht auf
    Coordinator-Ebene gemockt): ein von Home Assistant intern
    verschluckter Schreibfehler im zeitversetzten Pfad muss denselben
    storage_error-Zustand auslösen wie eine synchron erkannte Ablehnung."""
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(
        return_value=_full_state(dt_util.utcnow())
    )
    await coordinator.async_load_economics_state()
    coordinator._economics_store._store.async_save = AsyncMock()
    coordinator._economics_store._store.async_load = AsyncMock(
        return_value={"stale": True}
    )

    coordinator._async_schedule_economics_save()
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=ECONOMICS_SAVE_DELAY + 1)
    )
    await hass.async_block_till_done()

    assert coordinator._economics_store_write_blocked is True


# --------------------------------------------------------------------------
# Coordinator: Bootstrap, Deaktivierung, Shutdown
# --------------------------------------------------------------------------
async def test_load_leaves_the_balance_unset_without_a_store(hass) -> None:
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(return_value=None)

    await coordinator.async_load_economics_state()

    assert coordinator._economics_started_at is None
    await coordinator.async_shutdown()


async def test_load_restores_an_already_initialized_balance(hass) -> None:
    started_at = dt_util.utcnow()
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(
        return_value=_full_state(started_at)
    )

    await coordinator.async_load_economics_state()

    assert coordinator._economics_started_at == started_at
    assert coordinator._economics_grid_charge_cost_eur == 10.0
    assert coordinator._economics_operating_result_high_water_eur == 4.0
    await coordinator.async_shutdown()


async def test_load_repairs_a_high_water_below_the_current_raw_result(hass) -> None:
    """Ein inkonsistenter Peak darf keinen historischen Zuwachs neu verbuchen."""
    started_at = dt_util.utcnow()
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(
        return_value=_full_state(
            started_at,
            grid_charge_cost_eur=10.0,
            pv_opportunity_cost_eur=0.0,
            avoided_grid_cost_eur=110.0,
            operating_result_high_water_eur=80.0,
        )
    )

    await coordinator.async_load_economics_state()

    assert coordinator._economics_operating_result_high_water_eur == 100.0
    await coordinator.async_shutdown()


async def test_load_migrates_the_current_result_but_discards_legacy_day_cashflows(
    hass,
) -> None:
    """Alt-Stores kennen weder den früheren Peak noch Peak-Zuwächse je Tag.

    Der aktuelle Rohwert ist die einzige sichere Ausgangsbasis. Alte
    Tages-Cashflows dürfen nicht positiv geklemmt werden, weil eine Erholung
    unter einem früheren Höchststand sonst als neue Ersparnis erschiene.
    """
    started_at = dt_util.utcnow()
    legacy_day = DayEconomicsResult(
        day=date(2026, 3, 10),
        operating_result_eur=25.0,
        priced_charge_kwh=1.0,
        unpriced_charge_kwh=0.0,
        priced_discharge_kwh=1.0,
        unpriced_discharge_kwh=0.0,
    )
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(
        return_value=_full_state(
            started_at,
            grid_charge_cost_eur=10.0,
            pv_opportunity_cost_eur=0.0,
            avoided_grid_cost_eur=110.0,
            operating_result_high_water_eur=None,
            day_results=(legacy_day,),
            current_day=date(2026, 3, 11),
            current_day_operating_result_eur=5.0,
            current_day_priced_charge_kwh=0.0,
            current_day_unpriced_charge_kwh=0.0,
            current_day_priced_discharge_kwh=0.0,
            current_day_unpriced_discharge_kwh=0.0,
            current_day_observed_seconds=1_800.0,
        )
    )

    await coordinator.async_load_economics_state()

    assert coordinator._economics_operating_result_high_water_eur == 100.0
    assert coordinator._economics_day_results == ()
    assert coordinator._economics_current_day is None
    data: dict[str, object] = {}
    coordinator._publish_economics_balance(data, monetary_available=True)
    assert data["economics_operating_result"] == pytest.approx(100.0)
    assert data["economics_net_savings"] == pytest.approx(100.0)
    assert data["economics_net_savings_last_reset"] == started_at
    await coordinator.async_shutdown()


@pytest.mark.parametrize(
    ("avoided_grid_cost_eur", "expected_net_savings"),
    ((110.0, 100.0), (5.0, 0.0)),
)
async def test_real_minor_five_store_starts_fresh_daily_net_savings_history(
    hass,
    hass_storage,
    avoided_grid_cost_eur,
    expected_net_savings,
) -> None:
    """Der echte HA-Store-Pfad übernimmt keinen alten Tages-Cashflow."""
    entry_id = f"legacy-{expected_net_savings}"
    migration_at = datetime(2026, 8, 28, 10, 30, tzinfo=UTC)
    started_at = migration_at - timedelta(days=30)
    current_day = migration_at.astimezone(dt_util.DEFAULT_TIME_ZONE).date()
    legacy_day = DayEconomicsResult(
        day=current_day - timedelta(days=1),
        operating_result_eur=25.0,
        priced_charge_kwh=1.0,
        unpriced_charge_kwh=0.0,
        priced_discharge_kwh=1.0,
        unpriced_discharge_kwh=0.0,
    )
    legacy_payload = EconomicsStateStore._serialize(
        _full_state(
            started_at,
            grid_charge_cost_eur=10.0,
            pv_opportunity_cost_eur=0.0,
            avoided_grid_cost_eur=avoided_grid_cost_eur,
            operating_result_high_water_eur=None,
            day_results=(legacy_day,),
            current_day=current_day,
            current_day_operating_result_eur=5.0,
            current_day_priced_charge_kwh=0.0,
            current_day_unpriced_charge_kwh=0.0,
            current_day_priced_discharge_kwh=0.0,
            current_day_unpriced_discharge_kwh=0.0,
            current_day_observed_seconds=1_800.0,
        )
    )
    del legacy_payload["operating_result_high_water_eur"]
    _seed_real_store(
        hass_storage,
        entry_id,
        legacy_payload,
        version=1,
        minor_version=5,
    )
    options = {
        **FIXED_TARIFF_OPTIONS,
        CONF_ECONOMICS_INVESTMENT_COST: 1_000.0,
    }
    coordinator = _coordinator(hass, entry_id=entry_id, options=options)

    with patch(
        "custom_components.sax_power.coordinator.dt_util.utcnow",
        return_value=migration_at,
    ):
        await coordinator.async_load_economics_state()

    assert coordinator._economics_operating_result_high_water_eur == pytest.approx(
        expected_net_savings
    )
    assert coordinator._economics_day_results == ()
    assert coordinator._economics_current_day is None

    with patch(
        "custom_components.sax_power.coordinator.dt_util.now",
        return_value=migration_at,
    ):
        assert coordinator._advance_economics_day() is True
        data: dict[str, object] = {}
        coordinator._publish_amortization(data, monetary_available=True)
    assert data["economics_net_savings_today"] == pytest.approx(0.0)
    assert data["economics_net_savings_today_last_reset"] == (
        dt_util.start_of_local_day(current_day)
    )

    await coordinator.async_shutdown()
    assert hass_storage[f"{STORAGE_KEY_PREFIX}.{entry_id}"]["minor_version"] == 6
    assert (
        hass_storage[f"{STORAGE_KEY_PREFIX}.{entry_id}"]["data"][
            "operating_result_high_water_eur"
        ]
        == expected_net_savings
    )
    reloaded = _coordinator(hass, entry_id=entry_id, options=options)
    await reloaded.async_load_economics_state()
    assert reloaded._economics_operating_result_high_water_eur == pytest.approx(
        expected_net_savings
    )
    await reloaded.async_shutdown()


async def test_load_discards_legacy_day_cashflows_with_an_incomplete_core(
    hass,
) -> None:
    """Inkompatible Alt-Tage dürfen kein vollständiges Kernbündel voraussetzen."""
    legacy_day = DayEconomicsResult(
        day=date(2026, 3, 10),
        operating_result_eur=25.0,
        priced_charge_kwh=1.0,
        unpriced_charge_kwh=0.0,
        priced_discharge_kwh=1.0,
        unpriced_discharge_kwh=0.0,
    )
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(
        return_value=_full_state(
            dt_util.utcnow(),
            unvalued_inventory_kwh=None,
            operating_result_high_water_eur=None,
            day_results=(legacy_day,),
            current_day=date(2026, 3, 11),
            current_day_operating_result_eur=5.0,
            current_day_priced_charge_kwh=0.0,
            current_day_unpriced_charge_kwh=0.0,
            current_day_priced_discharge_kwh=0.0,
            current_day_unpriced_discharge_kwh=0.0,
            current_day_observed_seconds=1_800.0,
        )
    )

    await coordinator.async_load_economics_state()

    assert coordinator._economics_started_at is None
    assert coordinator._economics_day_results == ()
    assert coordinator._economics_current_day is None
    await coordinator.async_shutdown()


async def test_load_drops_all_dependent_history_from_an_incomplete_current_store(
    hass,
) -> None:
    """Eine neue Nullbilanz darf keine Historie des defekten Stands erben."""
    started_at = dt_util.utcnow()
    old_day = DayEconomicsResult(
        day=date(2026, 3, 10),
        operating_result_eur=25.0,
        priced_charge_kwh=1.0,
        unpriced_charge_kwh=0.0,
        priced_discharge_kwh=1.0,
        unpriced_discharge_kwh=0.0,
    )
    coordinator = _coordinator(
        hass,
        options={
            **FIXED_TARIFF_OPTIONS,
            CONF_ECONOMICS_INVESTMENT_COST: 1_000.0,
        },
    )
    persisted = _stub_store_with_initial_data(
        coordinator._economics_store,
        EconomicsStateStore._serialize(
            _full_state(
                started_at,
                unvalued_inventory_kwh=None,
                operating_result_high_water_eur=100.0,
                day_results=(old_day,),
                current_day=date(2026, 3, 11),
                current_day_operating_result_eur=5.0,
                current_day_priced_charge_kwh=0.0,
                current_day_unpriced_charge_kwh=0.0,
                current_day_priced_discharge_kwh=0.0,
                current_day_unpriced_discharge_kwh=0.0,
                current_day_observed_seconds=1_800.0,
                payback_achieved_at=started_at,
            )
        ),
    )

    await coordinator.async_load_economics_state()

    assert coordinator._economics_started_at is None
    assert coordinator._economics_operating_result_high_water_eur is None
    assert coordinator._economics_day_results == ()
    assert coordinator._economics_current_day is None
    assert coordinator._economics_payback_achieved_at is None

    # Mittags UTC liegt der Bootstrap in jeder von Home Assistant
    # unterstützten Zeitzone nach dem lokalen Tagesbeginn. Damit prüft der
    # Test die Reset-Priorität statt zufällig von der Ausführungsuhrzeit
    # abzuhängen.
    bootstrap_at = dt_util.utcnow().replace(hour=12, minute=0, second=0) + timedelta(
        days=1
    )
    data = {
        "storage_power_active": 0,
        "battery_capacity": 10_000,
        "battery_soc": 50,
    }
    with patch(
        "custom_components.sax_power.coordinator.dt_util.utcnow",
        return_value=bootstrap_at,
    ):
        coordinator._bootstrap_economics_if_ready(data)
    assert coordinator._economics_operating_result_high_water_eur == 0.0
    assert coordinator._economics_day_results == ()
    assert coordinator._economics_payback_achieved_at is None
    assert coordinator._economics_store_write_blocked is False

    with (
        patch(
            "custom_components.sax_power.coordinator.dt_util.now",
            return_value=bootstrap_at,
        ),
        patch(
            "custom_components.sax_power.coordinator.monotonic",
            return_value=1_000.0,
        ),
    ):
        coordinator._accumulate_energy(data)
    assert data["economics_net_savings_today_last_reset"] == bootstrap_at
    assert data["economics_net_savings_last_reset"] == bootstrap_at
    await coordinator.async_shutdown()
    assert persisted["operating_result_high_water_eur"] == 0.0
    assert persisted["payback_achieved_at"] is None


async def test_bootstrap_needs_no_numeric_capacity_or_soc(hass) -> None:
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(return_value=None)
    await coordinator.async_load_economics_state()

    data = {"storage_power_active": 0, "battery_soc": None, "battery_capacity": None}
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy(data)

    assert coordinator._economics_started_at is not None
    assert coordinator._economics_unvalued_inventory_kwh == 0.0
    assert data["economics_grid_charge_cost"] == 0.0
    await coordinator.async_shutdown()


async def test_bootstrap_values_existing_energy_at_zero(hass) -> None:
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(return_value=None)
    coordinator._economics_store.async_delay_save = MagicMock(return_value=True)
    await coordinator.async_load_economics_state()

    data = {
        "storage_power_active": 0,
        "battery_soc": 40,
        "battery_capacity": 10000,  # Wh -> 10 kWh
        "battery_soc_min": 5,
    }
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy(data)

    assert coordinator._economics_started_at is not None
    assert coordinator._economics_operating_result_high_water_eur == 0.0
    assert coordinator._economics_unvalued_inventory_kwh == 0.0
    assert data["economics_grid_charge_cost"] == 0.0
    assert data["economics_operating_result"] == 0.0
    assert data["economics_net_savings"] == 0.0
    assert data["economics_net_savings_last_reset"] == coordinator._economics_started_at
    await coordinator.async_shutdown()


async def test_disabled_tariff_reports_unavailable_and_does_not_bootstrap(
    hass,
) -> None:
    coordinator = _coordinator(hass, options={})
    coordinator._economics_store.async_load = AsyncMock(return_value=None)
    await coordinator.async_load_economics_state()

    data = {
        "storage_power_active": -1000,
        "battery_soc": 40,
        "battery_capacity": 10000,
        "smartmeter_power": 0,
    }
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy(data)

    assert coordinator._economics_started_at is None
    assert data["economics_grid_charge_cost"] is None
    assert data["economics_current_import_price"] is None
    assert data["economics_feed_in_price"] is None
    await coordinator.async_shutdown()


async def test_a_load_error_blocks_writes_until_a_reload(hass) -> None:
    """Ein Lesefehler darf einen vorhandenen, nur unlesbaren Store nicht
    durch eine frisch gebootstrappte Nullbilanz überschreiben. Anders als
    zuvor (REQ-ECONOMICS-ACCOUNTING) startet die Bilanz dabei jetzt auch
    NICHT mehr rein im Arbeitsspeicher weiter (REQ-ECONOMICS-OBSERVABILITY,
    Status storage_error) - "keine weitere Akkumulation auf ungesicherter/
    unklarer Baseline"."""
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(side_effect=OSError("kaputt"))
    coordinator._economics_store.async_delay_save = MagicMock(return_value=True)
    coordinator._economics_store.async_save = AsyncMock(return_value=True)

    await coordinator.async_load_economics_state()

    assert coordinator._economics_store_write_blocked is True

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy(
            {
                "storage_power_active": -1000,
                "smartmeter_power": 1000,
                "battery_soc": 50,
                "battery_capacity": 10000,
                "battery_soc_min": 5,
            }
        )
    data = {
        "storage_power_active": -1000,
        "smartmeter_power": 1000,
        "battery_soc": 50,
        "battery_capacity": 10000,
        "battery_soc_min": 5,
    }
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=4600.0
    ):
        coordinator._accumulate_energy(data)

    # Kein Bootstrap, keine Akkumulation, solange der Store als unlesbar
    # gilt - der Status macht das Problem sichtbar, statt einen
    # unbeobachteten 0-Start im Arbeitsspeicher zu riskieren.
    assert coordinator._economics_started_at is None
    assert coordinator._economics_grid_charge_cost_eur is None
    assert data["economics_status"] == "storage_error"
    coordinator._economics_store.async_delay_save.assert_not_called()

    await coordinator.async_shutdown()

    coordinator._economics_store.async_save.assert_not_called()


async def test_shutdown_flushes_the_current_balance(hass) -> None:
    started_at = dt_util.utcnow()
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(
        return_value=_full_state(started_at)
    )
    coordinator._economics_store.async_save = AsyncMock(return_value=True)
    await coordinator.async_load_economics_state()

    await coordinator.async_shutdown()

    coordinator._economics_store.async_save.assert_awaited_once()
    saved = coordinator._economics_store.async_save.await_args.args[0]
    assert saved.grid_charge_cost_eur == 10.0
    assert saved.operating_result_high_water_eur == 4.0
    assert saved.economics_started_at == started_at


async def test_a_rejected_delayed_save_freezes_the_balance(hass) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: schlägt async_delay_save fehl (_accept
    lehnt den Snapshot ab, z. B. wegen eines Bugs, der einen regressiven
    Wert erzeugt), gilt der Store ab sofort als storage_error - keine
    weitere Akkumulation auf einer nicht mehr vertrauenswürdigen
    Baseline."""
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(
        return_value=_full_state(dt_util.utcnow())
    )
    await coordinator.async_load_economics_state()
    coordinator._economics_store.async_delay_save = MagicMock(return_value=False)

    coordinator._async_schedule_economics_save()

    assert coordinator._economics_store_write_blocked is True


async def test_a_rejected_final_save_freezes_the_balance(hass) -> None:
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(
        return_value=_full_state(dt_util.utcnow())
    )
    await coordinator.async_load_economics_state()
    coordinator._economics_store.async_save = AsyncMock(return_value=False)

    await coordinator._async_flush_economics_state()

    assert coordinator._economics_store_write_blocked is True


async def test_a_raised_final_save_error_freezes_the_balance(hass) -> None:
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(
        return_value=_full_state(dt_util.utcnow())
    )
    await coordinator.async_load_economics_state()
    coordinator._economics_store.async_save = AsyncMock(
        side_effect=OSError("Platte voll")
    )

    await coordinator._async_flush_economics_state()

    assert coordinator._economics_store_write_blocked is True


async def test_notify_tariff_revision_updates_the_timestamp_and_schedules_a_save(
    hass,
) -> None:
    started_at = dt_util.utcnow()
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(
        return_value=_full_state(started_at)
    )
    coordinator._economics_store.async_delay_save = MagicMock(return_value=True)
    await coordinator.async_load_economics_state()

    coordinator.notify_tariff_revision()

    assert coordinator._last_tariff_revision_at is not None
    coordinator._economics_store.async_delay_save.assert_called_once()
    await coordinator.async_shutdown()
