"""Tests für die reine Geldbilanz der Wirtschaftlichkeitsauswertung.

Siehe anforderung.yaml, REQ-ECONOMICS-ACCOUNTING. Reine Funktionstests ohne
Home Assistant - der Coordinator-seitige Verdrahtungstest (Bootstrap,
SOC-Minimum-Korrektur, Tarifwechsel, deaktivierter Tarif) liegt in
tests/test_economics_persistence.py bzw. tests/test_coordinator.py.
"""

from __future__ import annotations

import pytest

from custom_components.sax_power.domain.economics_accounting import (
    NO_DELTA,
    EconomicsDelta,
    compute_economics_delta,
    initial_unvalued_inventory_kwh,
    min_soc_inventory_correction,
)
from custom_components.sax_power.domain.energy_accounting import (
    ZERO_DELTA,
    EnergyDelta,
)


def _charge(grid: float = 0.0, pv: float = 0.0, unknown: float = 0.0) -> EnergyDelta:
    return EnergyDelta(
        charged_kwh=grid + pv + unknown, grid_kwh=grid, pv_kwh=pv, unknown_kwh=unknown
    )


# --------------------------------------------------------------------------
# Ladeseite
# --------------------------------------------------------------------------
def test_idle_interval_produces_no_delta() -> None:
    delta = compute_economics_delta(ZERO_DELTA, 0.0, 0.0, 0.30, 0.08)

    assert delta == NO_DELTA


def test_grid_charge_costs_the_import_price() -> None:
    delta = compute_economics_delta(_charge(grid=2.0), 0.0, 0.0, 0.30, 0.08)

    assert delta.grid_charge_cost_delta == pytest.approx(0.6)
    assert delta.pv_opportunity_cost_delta == 0.0
    assert delta.unvalued_inventory_delta_kwh == 0.0
    assert delta.unpriced_charge_delta_kwh == 0.0


def test_pv_charge_costs_the_feed_in_price() -> None:
    """PV-Ladung kostet die entgangene Einspeisevergütung - PV ist nicht
    kostenlos (Abgrenzung zum verworfenen Issue #42)."""
    delta = compute_economics_delta(_charge(pv=3.0), 0.0, 0.0, 0.30, 0.08)

    assert delta.pv_opportunity_cost_delta == pytest.approx(0.24)
    assert delta.grid_charge_cost_delta == 0.0
    assert delta.unvalued_inventory_delta_kwh == 0.0


def test_mixed_charge_costs_grid_and_pv_shares_separately() -> None:
    delta = compute_economics_delta(_charge(grid=1.0, pv=1.5), 0.0, 0.0, 0.30, 0.08)

    assert delta.grid_charge_cost_delta == pytest.approx(0.30)
    assert delta.pv_opportunity_cost_delta == pytest.approx(0.12)


def test_unknown_origin_charge_is_never_priced() -> None:
    """Herkunft unbekannt hat keinen Preisbegriff - unabhängig davon, ob
    gerade Preise verfügbar wären."""
    delta = compute_economics_delta(_charge(unknown=1.0), 0.0, 0.0, 0.30, 0.08)

    assert delta.grid_charge_cost_delta == 0.0
    assert delta.pv_opportunity_cost_delta == 0.0
    assert delta.unpriced_charge_delta_kwh == pytest.approx(1.0)
    assert delta.unvalued_inventory_delta_kwh == pytest.approx(1.0)


def test_missing_import_price_makes_grid_charge_unpriced() -> None:
    delta = compute_economics_delta(_charge(grid=2.0), 0.0, 0.0, None, 0.08)

    assert delta.grid_charge_cost_delta == 0.0
    assert delta.unpriced_charge_delta_kwh == pytest.approx(2.0)
    assert delta.unvalued_inventory_delta_kwh == pytest.approx(2.0)


def test_missing_feed_in_price_makes_pv_charge_unpriced() -> None:
    delta = compute_economics_delta(_charge(pv=1.0), 0.0, 0.0, 0.30, None)

    assert delta.pv_opportunity_cost_delta == 0.0
    assert delta.unpriced_charge_delta_kwh == pytest.approx(1.0)
    assert delta.unvalued_inventory_delta_kwh == pytest.approx(1.0)


def test_negative_import_price_is_applied_without_clamping() -> None:
    """Negative dynamische Preise sind zulässig - eine Netzladung darf
    dadurch sogar Geld einbringen."""
    delta = compute_economics_delta(_charge(grid=2.0), 0.0, 0.0, -0.05, 0.08)

    assert delta.grid_charge_cost_delta == pytest.approx(-0.1)


# --------------------------------------------------------------------------
# Entladeseite
# --------------------------------------------------------------------------
def test_discharge_from_unvalued_inventory_avoids_no_cost() -> None:
    """Entladung von unbewertetem Bestand erzeugt keinen vermiedenen
    Geldwert - sonst entstünde ein kostenloser Scheingewinn (Issue #42)."""
    delta = compute_economics_delta(ZERO_DELTA, 1.0, 5.0, 0.30, 0.08)

    assert delta.avoided_grid_cost_delta == 0.0
    assert delta.unvalued_inventory_delta_kwh == pytest.approx(-1.0)
    assert delta.unpriced_discharge_delta_kwh == 0.0


def test_discharge_beyond_inventory_is_partially_monetizable() -> None:
    """3 kWh Entladung, aber nur 1 kWh unbewerteter Bestand: 1 kWh
    verbraucht den Bestand ohne Geldwert, 2 kWh sind bepreist entladen."""
    delta = compute_economics_delta(ZERO_DELTA, 3.0, 1.0, 0.30, 0.08)

    assert delta.unvalued_inventory_delta_kwh == pytest.approx(-1.0)
    assert delta.avoided_grid_cost_delta == pytest.approx(0.6)
    assert delta.unpriced_discharge_delta_kwh == 0.0


def test_discharge_without_any_inventory_is_fully_monetizable() -> None:
    delta = compute_economics_delta(ZERO_DELTA, 2.0, 0.0, 0.30, 0.08)

    assert delta.unvalued_inventory_delta_kwh == 0.0
    assert delta.avoided_grid_cost_delta == pytest.approx(0.6)


def test_discharge_without_an_import_price_is_unpriced_not_backfilled() -> None:
    """Fehlt der Importpreis bei einer monetarisierbaren Entladung, wird
    die Energie als unpriced_discharge gezählt - nicht später rückwirkend
    bewertet."""
    delta = compute_economics_delta(ZERO_DELTA, 2.0, 0.0, None, 0.08)

    assert delta.avoided_grid_cost_delta == 0.0
    assert delta.unpriced_discharge_delta_kwh == pytest.approx(2.0)


def test_negative_import_price_applies_to_avoided_cost_too() -> None:
    delta = compute_economics_delta(ZERO_DELTA, 2.0, 0.0, -0.05, 0.08)

    assert delta.avoided_grid_cost_delta == pytest.approx(-0.1)


def test_charge_efficiency_losses_reduce_the_result_without_a_factor() -> None:
    """Ladeverluste brauchen keinen angenommenen Wirkungsgrad: Kosten
    entstehen für die volle AC-Ladeenergie, Nutzen nur für die tatsächlich
    gemessene, kleinere Entladeenergie - die Differenz senkt automatisch
    das operative Ergebnis."""
    charge = compute_economics_delta(_charge(grid=1.0), 0.0, 0.0, 0.30, 0.08)
    # 10 % Ladeverlust: nur 0.9 kWh kommen beim Entladen wieder heraus.
    discharge = compute_economics_delta(ZERO_DELTA, 0.9, 0.0, 0.30, 0.08)

    operating_result = (
        discharge.avoided_grid_cost_delta
        - charge.grid_charge_cost_delta
        - charge.pv_opportunity_cost_delta
    )
    assert operating_result == pytest.approx(0.9 * 0.30 - 1.0 * 0.30)
    assert operating_result < 0


# --------------------------------------------------------------------------
# Anfangsbestand
# --------------------------------------------------------------------------
def test_initial_inventory_waits_for_numeric_capacity_and_soc() -> None:
    assert initial_unvalued_inventory_kwh(None, 50.0) is None
    assert initial_unvalued_inventory_kwh(10.0, None) is None


def test_initial_inventory_is_capacity_times_soc_share() -> None:
    assert initial_unvalued_inventory_kwh(10.0, 40) == pytest.approx(4.0)


# --------------------------------------------------------------------------
# SOC-Minimum-Korrektur
# --------------------------------------------------------------------------
def test_min_soc_correction_needs_both_values_known() -> None:
    assert min_soc_inventory_correction(1.0, None, 5) is None
    assert min_soc_inventory_correction(1.0, 5, None) is None


def test_min_soc_correction_only_applies_at_or_below_the_minimum() -> None:
    assert min_soc_inventory_correction(1.0, 10, 5) is None
    assert min_soc_inventory_correction(1.0, 5, 5) == 0.0
    assert min_soc_inventory_correction(1.0, 4, 5) == 0.0


def test_min_soc_correction_is_a_noop_once_inventory_is_already_zero() -> None:
    assert min_soc_inventory_correction(0.0, 5, 5) is None


def test_economics_delta_equality_and_default() -> None:
    assert NO_DELTA == EconomicsDelta()
