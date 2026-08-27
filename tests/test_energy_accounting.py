"""Tests für die reine Bilanzregel der Ladeenergie-Herkunft.

Siehe anforderung.yaml, REQ-ENERGY-ORIGIN. Reine Funktionstests ohne Home
Assistant - der Coordinator-seitige Verdrahtungstest (Rundung,
Entladung/SunSpec-Ausfall bleiben unberührt) liegt in
tests/test_coordinator.py.
"""

from __future__ import annotations

import random

import pytest

from custom_components.sax_power.domain.energy_accounting import (
    ZERO_DELTA,
    EnergyDelta,
    compute_charge_delta,
)


def test_unknown_storage_power_skips_the_interval() -> None:
    """storage_power_active unbekannt: Intervall vollständig überspringen,
    wie bisher - kein Delta, auch keine Nullen."""
    assert compute_charge_delta(None, 500.0, 1.0) is None
    assert compute_charge_delta(None, None, 1.0) is None


@pytest.mark.parametrize("storage_power_active", [0.0, 500.0, 1000.0])
def test_idle_or_discharging_produces_no_origin_change(
    storage_power_active: float,
) -> None:
    """storage_power_active >= 0 (Leerlauf oder Entladung, positives
    Vorzeichen) bedeutet charge_power_w == 0 - keine Herkunftsänderung,
    unabhängig vom Netzwert. Entladung verändert damit keinen
    Herkunftszähler."""
    delta = compute_charge_delta(storage_power_active, 500.0, 1.0)

    assert delta == ZERO_DELTA


def test_pure_pv_charge_assigns_everything_to_pv() -> None:
    """Reine PV-Ladung: kein Netzbezug (smartmeter_power <= 0), die
    gesamte Ladeenergie zählt als PV."""
    delta = compute_charge_delta(-2000.0, -500.0, 1.0)

    assert delta.charged_kwh == pytest.approx(2.0)
    assert delta.grid_kwh == 0.0
    assert delta.pv_kwh == pytest.approx(2.0)


def test_pure_grid_charge_assigns_everything_to_grid() -> None:
    """Reine Netzladung: Netzbezug deckt die komplette Ladeleistung."""
    delta = compute_charge_delta(-2000.0, 2000.0, 1.0)

    assert delta.charged_kwh == pytest.approx(2.0)
    assert delta.grid_kwh == pytest.approx(2.0)
    assert delta.pv_kwh == 0.0


def test_mixed_charge_splits_between_grid_and_pv() -> None:
    """Gemischte Ladung: Netzbezug deckt einen Teil, der Rest gilt als PV."""
    delta = compute_charge_delta(-2000.0, 800.0, 1.0)

    assert delta.charged_kwh == pytest.approx(2.0)
    assert delta.grid_kwh == pytest.approx(0.8)
    assert delta.pv_kwh == pytest.approx(1.2)


def test_export_during_charge_assigns_everything_to_pv() -> None:
    """Einspeisung während des Ladens (smartmeter_power < 0): kein
    Netzbezug, also komplett PV - max(smartmeter_power, 0) fängt das ab."""
    delta = compute_charge_delta(-1500.0, -3000.0, 1.0)

    assert delta.grid_kwh == 0.0
    assert delta.pv_kwh == pytest.approx(1.5)


def test_grid_import_exceeding_charge_power_still_caps_at_full_charge() -> None:
    """Netzbezug größer als die Ladeleistung (deckt zusätzlich
    Hausverbrauch): zählt trotzdem vollständig, aber nur bis zur
    tatsächlichen Ladeleistung, als Netzladung - kein negativer PV-Anteil."""
    delta = compute_charge_delta(-1000.0, 5000.0, 1.0)

    assert delta.charged_kwh == pytest.approx(1.0)
    assert delta.grid_kwh == pytest.approx(1.0)
    assert delta.pv_kwh == 0.0


def test_grid_import_smaller_than_charge_power_leaves_a_pv_remainder() -> None:
    """Netzbezug kleiner als die Ladeleistung: Differenz gilt als PV."""
    delta = compute_charge_delta(-3000.0, 1000.0, 1.0)

    assert delta.grid_kwh == pytest.approx(1.0)
    assert delta.pv_kwh == pytest.approx(2.0)


def test_unknown_smartmeter_value_assigns_everything_to_grid() -> None:
    """smartmeter_power unbekannt, aber storage_power_active bekannt: die
    gesamte Ladeenergie gilt konservativ als Netzladung. Sie als PV zu
    buchen wäre die günstigere Deutung (Einspeisevergütung statt
    Netzbezugspreis) und würde die Bilanz bei jedem Messausfall
    beschönigen."""
    delta = compute_charge_delta(-1200.0, None, 1.0)

    assert delta.charged_kwh == pytest.approx(1.2)
    assert delta.grid_kwh == pytest.approx(1.2)
    assert delta.pv_kwh == 0.0


def test_zero_elapsed_time_produces_zero_energy_regardless_of_power() -> None:
    delta = compute_charge_delta(-2000.0, 500.0, 0.0)

    assert delta == EnergyDelta(0.0, 0.0, 0.0)


def test_delta_invariant_holds_without_drift_across_many_random_intervals() -> None:
    """Für jedes gültige Ladeintervall gilt grid + pv == charged - über
    viele zufällige Intervalle hinweg, ohne kumulative Abweichung."""
    random.seed(20260826)
    total_charged = 0.0
    total_grid = 0.0
    total_pv = 0.0

    for _ in range(5000):
        storage_power_active = random.uniform(-20000.0, 20000.0)
        smartmeter_power = random.choice([None, random.uniform(-10000.0, 20000.0)])
        elapsed_hours = random.uniform(0.0005, 0.01)

        delta = compute_charge_delta(
            storage_power_active, smartmeter_power, elapsed_hours
        )
        assert delta is not None

        # Je Intervall: keine sichtbare Rundungsabweichung bei drei
        # veröffentlichten Nachkommastellen.
        assert round(delta.grid_kwh + delta.pv_kwh, 3) == round(delta.charged_kwh, 3)

        total_charged += delta.charged_kwh
        total_grid += delta.grid_kwh
        total_pv += delta.pv_kwh

    # Über die Summe vieler Intervalle bleibt die Abweichung im
    # Gleitkomma-Rauschen (viele Zehnerpotenzen unter der dritten
    # Nachkommastelle) - keine systematische Drift.
    assert total_grid + total_pv == pytest.approx(total_charged, abs=1e-6)
