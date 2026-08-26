"""Regression tests for REQ-ECONOMICS-ACCOUNTING balance persistence.

Store-Level-Tests (Round-Trip, unabhängige Feldvalidierung, korrupte/
rückläufige Snapshots, zwei Config Entries, Drosselung/Sofort-Flush) sowie
der Coordinator-seitige Bootstrap/Shutdown-Lebenszyklus. Die reine
Geldbilanz selbst (compute_economics_delta) ist in
tests/test_economics_accounting.py getestet; die volle Verdrahtung inkl.
Rundung und SOC-Minimum-Korrektur in tests/test_coordinator.py.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.util import dt as dt_util

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.economics_amortization import (
    MAX_STORED_DAYS,
    DayEconomicsResult,
)
from custom_components.sax_power.domain.tariff import TariffType
from custom_components.sax_power.infrastructure.economics_store import (
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
        "unvalued_inventory_kwh": 3.0,
        "unpriced_charge_kwh": 1.0,
        "unpriced_discharge_kwh": 0.5,
        "economics_started_at": started_at,
    }
    values.update(overrides)
    return EconomicsState(**values)


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
    store._store.async_save = AsyncMock()
    assert (
        await store.async_save(_full_state(started_at, unpriced_charge_kwh=5.0)) is True
    )

    regressive = _full_state(started_at, unpriced_charge_kwh=4.0)
    assert await store.async_save(regressive) is False
    assert store._store.async_save.await_count == 1
    assert "Rückläufigen Wirtschaftlichkeits-Snapshot für Unbepreiste Ladung" in (
        caplog.text
    )


async def test_store_permits_the_inventory_gauge_to_decrease(hass) -> None:
    """unvalued_inventory_kwh ist ein Bestand (Gauge) - Entladung und die
    SOC-Minimum-Korrektur lassen ihn sinken, das ist keine Regression."""
    started_at = dt_util.utcnow()
    store = EconomicsStateStore(hass, "inventory-gauge")
    store._store.async_save = AsyncMock()
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
    store._store.async_save = AsyncMock()
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
    store._store.async_load = AsyncMock(
        return_value={
            **EconomicsStateStore._serialize(_full_state(old_started_at)),
            "unvalued_inventory_kwh": -1,  # macht das Bündel unvollständig
        }
    )
    store._store.async_save = AsyncMock()

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
    )
    day_two = DayEconomicsResult(
        day=date(2026, 3, 10),
        operating_result_eur=-0.5,
        priced_charge_kwh=0.0,
        unpriced_charge_kwh=0.0,
        priced_discharge_kwh=0.5,
        unpriced_discharge_kwh=0.5,
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
        payback_achieved_at=payback_at,
    )

    assert await store.async_save(state) is True
    loaded = await EconomicsStateStore(hass, "amortization-roundtrip").async_load()

    assert loaded == state
    assert loaded.day_results == (day_one, day_two)
    assert loaded.current_day == date(2026, 3, 11)
    assert loaded.payback_achieved_at == payback_at


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
    store._store.async_save = AsyncMock()
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
    store._store.async_save = AsyncMock()
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
        unpriced_charge_kwh=0.0,
        priced_charge_kwh=0.0,
        payback_achieved_at=None,
    )
    assert await store.async_reset(reset_state) is True

    loaded = await EconomicsStateStore(hass, "reset-bypass").async_load()
    assert loaded.economics_started_at == new_started_at
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


def test_store_throttles_frequent_updates_and_keeps_newest_state(hass) -> None:
    store = EconomicsStateStore(hass, "throttled")
    store._store.async_delay_save = MagicMock()
    started_at = dt_util.utcnow()

    assert store.async_delay_save(_full_state(started_at, grid_charge_cost_eur=1.0))
    assert store.async_delay_save(_full_state(started_at, grid_charge_cost_eur=1.5))

    store._store.async_delay_save.assert_called_once()
    data_func = store._store.async_delay_save.call_args.args[0]
    assert data_func()["grid_charge_cost_eur"] == 1.5


async def test_store_final_flush_writes_newest_state_immediately(hass) -> None:
    store = EconomicsStateStore(hass, "flush")
    store._store.async_delay_save = MagicMock()
    store._store.async_save = AsyncMock()
    started_at = dt_util.utcnow()
    store.async_delay_save(_full_state(started_at, grid_charge_cost_eur=1.0))

    assert await store.async_save(_full_state(started_at, grid_charge_cost_eur=2.0))
    store._store.async_save.assert_awaited_once()
    assert store._store.async_save.await_args.args[0]["grid_charge_cost_eur"] == 2.0


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
    await coordinator.async_shutdown()


async def test_bootstrap_waits_for_numeric_capacity_and_soc(hass) -> None:
    coordinator = _coordinator(hass, options=FIXED_TARIFF_OPTIONS)
    coordinator._economics_store.async_load = AsyncMock(return_value=None)
    await coordinator.async_load_economics_state()

    data = {"storage_power_active": 0, "battery_soc": None, "battery_capacity": None}
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._accumulate_energy(data)

    assert coordinator._economics_started_at is None
    assert data["economics_grid_charge_cost"] is None
    assert data["economics_unvalued_inventory"] is None
    await coordinator.async_shutdown()


async def test_bootstrap_sets_the_initial_inventory_once_data_is_known(hass) -> None:
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
    assert coordinator._economics_unvalued_inventory_kwh == pytest.approx(4.0)
    assert data["economics_unvalued_inventory"] == pytest.approx(4.0)
    assert data["economics_grid_charge_cost"] == 0.0
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
    assert saved.economics_started_at == started_at


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
