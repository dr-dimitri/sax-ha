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
    capacity_inventory_correction,
    compute_economics_delta,
    compute_operating_result_high_water,
    initial_unvalued_inventory_kwh,
    min_soc_inventory_correction,
)
from custom_components.sax_power.domain.energy_accounting import (
    ZERO_DELTA,
    EnergyDelta,
)


def _charge(grid: float = 0.0, pv: float = 0.0) -> EnergyDelta:
    return EnergyDelta(charged_kwh=grid + pv, grid_kwh=grid, pv_kwh=pv)


# --------------------------------------------------------------------------
# Nichtnegative Netto-Ersparnis
# --------------------------------------------------------------------------
def test_operating_result_high_water_never_turns_a_loss_into_savings() -> None:
    assert compute_operating_result_high_water(0.0, -20.0) == 0.0


def test_operating_result_high_water_never_runs_backwards() -> None:
    assert compute_operating_result_high_water(100.0, 80.0) == 100.0
    assert compute_operating_result_high_water(100.0, 100.0) == 100.0
    assert compute_operating_result_high_water(100.0, 105.0) == 105.0


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
    assert delta.priced_charge_kwh_delta == pytest.approx(2.0)


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


def test_charge_without_a_smartmeter_reading_is_priced_as_grid_charge() -> None:
    """Ein Intervall ohne Smartmeter-Messwert kommt aus
    domain/energy_accounting bereits vollständig als Netzladung an (die
    Kategorie "Herkunft unbekannt" gibt es nicht mehr) und wird hier
    entsprechend mit dem Netzbezugspreis belastet - nicht als unbewerteter
    Bestand geparkt."""
    delta = compute_economics_delta(_charge(grid=1.0), 0.0, 0.0, 0.30, 0.08)

    assert delta.grid_charge_cost_delta == pytest.approx(0.30)
    assert delta.pv_opportunity_cost_delta == 0.0
    assert delta.unpriced_charge_delta_kwh == 0.0
    assert delta.unvalued_inventory_delta_kwh == 0.0


def test_missing_import_price_makes_grid_charge_unpriced() -> None:
    delta = compute_economics_delta(_charge(grid=2.0), 0.0, 0.0, None, 0.08)

    assert delta.grid_charge_cost_delta == 0.0
    assert delta.unpriced_charge_delta_kwh == pytest.approx(2.0)
    assert delta.unvalued_inventory_delta_kwh == pytest.approx(2.0)
    assert delta.priced_charge_kwh_delta == 0.0


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
    assert delta.priced_discharge_kwh_delta == 0.0


def test_discharge_beyond_inventory_is_partially_monetizable() -> None:
    """3 kWh Entladung, aber nur 1 kWh unbewerteter Bestand: 1 kWh
    verbraucht den Bestand ohne Geldwert, 2 kWh sind bepreist entladen."""
    delta = compute_economics_delta(ZERO_DELTA, 3.0, 1.0, 0.30, 0.08)

    assert delta.unvalued_inventory_delta_kwh == pytest.approx(-1.0)
    assert delta.avoided_grid_cost_delta == pytest.approx(0.6)
    assert delta.unpriced_discharge_delta_kwh == 0.0
    assert delta.priced_discharge_kwh_delta == pytest.approx(2.0)


def test_discharge_without_any_inventory_is_fully_monetizable() -> None:
    delta = compute_economics_delta(ZERO_DELTA, 2.0, 0.0, 0.30, 0.08)

    assert delta.unvalued_inventory_delta_kwh == 0.0
    assert delta.avoided_grid_cost_delta == pytest.approx(0.6)
    assert delta.priced_discharge_kwh_delta == pytest.approx(2.0)


def test_discharge_without_an_import_price_is_unpriced_not_backfilled() -> None:
    """Fehlt der Importpreis bei einer monetarisierbaren Entladung, wird
    die Energie als unpriced_discharge gezählt - nicht später rückwirkend
    bewertet."""
    delta = compute_economics_delta(ZERO_DELTA, 2.0, 0.0, None, 0.08)

    assert delta.avoided_grid_cost_delta == 0.0
    assert delta.unpriced_discharge_delta_kwh == pytest.approx(2.0)
    assert delta.priced_discharge_kwh_delta == 0.0


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


def test_pv_charge_efficiency_losses_reduce_the_result_without_a_factor() -> None:
    """Derselbe Zusammenhang auf der PV-Seite: Die Opportunitätskosten
    hängen an der GELADENEN Energie (entgangene Einspeisevergütung für
    jede eingespeicherte kWh), der vermiedene Netzbezug dagegen an der
    ENTLADENEN. Der Ladeverlust verschlechtert das Ergebnis damit auch
    hier von selbst, ohne angenommenen Wirkungsgrad."""
    charge = compute_economics_delta(_charge(pv=1.0), 0.0, 0.0, 0.30, 0.08)
    discharge = compute_economics_delta(ZERO_DELTA, 0.9, 0.0, 0.30, 0.08)

    assert charge.pv_opportunity_cost_delta == pytest.approx(1.0 * 0.08)
    assert discharge.avoided_grid_cost_delta == pytest.approx(0.9 * 0.30)

    operating_result = (
        discharge.avoided_grid_cost_delta
        - charge.grid_charge_cost_delta
        - charge.pv_opportunity_cost_delta
    )
    assert operating_result == pytest.approx(0.9 * 0.30 - 1.0 * 0.08)

    # Gegenprobe: Ohne Verlust fiele das Ergebnis um genau den Wert der
    # verlorenen 0.1 kWh besser aus - der Verlust ist also tatsächlich
    # eingepreist und nicht bloß rechnerisch unsichtbar.
    lossless = compute_economics_delta(ZERO_DELTA, 1.0, 0.0, 0.30, 0.08)
    assert lossless.avoided_grid_cost_delta - discharge.avoided_grid_cost_delta == (
        pytest.approx(0.1 * 0.30)
    )


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


# --------------------------------------------------------------------------
# Deckelung auf den Speicherinhalt (Issue #132)
# --------------------------------------------------------------------------
def test_inventory_cap_needs_both_values_known() -> None:
    assert capacity_inventory_correction(9.0, None, 50) is None
    assert capacity_inventory_correction(9.0, 10.0, None) is None


def test_inventory_cap_only_applies_above_the_physical_content() -> None:
    assert capacity_inventory_correction(4.0, 10.0, 50) is None
    assert capacity_inventory_correction(5.0, 10.0, 50) is None
    assert capacity_inventory_correction(5.5, 10.0, 50) == pytest.approx(5.0)


def test_inventory_cap_never_returns_a_negative_content() -> None:
    """Ein (theoretisch) negativ gemeldeter SOC darf keinen negativen
    Bestand erzeugen - der Bestand kennt nur 0 als Untergrenze."""
    assert capacity_inventory_correction(1.0, 10.0, -5) == 0.0


def test_inventory_cap_empties_the_inventory_at_an_empty_storage() -> None:
    assert capacity_inventory_correction(0.7, 10.0, 0) == 0.0


def test_charging_losses_of_an_unpriced_cycle_leave_a_residual_without_the_cap() -> (
    None
):
    """Zusammenspiel aus Issue #132: 7 kWh unbepreiste Ladung heben den SOC
    verlustbedingt nur um 6,3 kWh; ohne Deckel bliebe der Rest für immer im
    Bestand und würde später bepreiste Entladung entwerten."""
    charge = compute_economics_delta(_charge(grid=7.0), 0.0, 0.0, None, None)
    inventory = charge.unvalued_inventory_delta_kwh
    assert inventory == pytest.approx(7.0)

    discharge = compute_economics_delta(ZERO_DELTA, 6.3, inventory, 0.30, 0.08)
    inventory += discharge.unvalued_inventory_delta_kwh
    assert discharge.avoided_grid_cost_delta == 0.0
    assert inventory == pytest.approx(0.7)  # Ladeverlust-Rest

    # Der Deckel räumt ihn ab, sobald der Speicher tatsächlich leer ist.
    assert capacity_inventory_correction(inventory, 10.0, 0) == 0.0


def test_economics_delta_equality_and_default() -> None:
    assert NO_DELTA == EconomicsDelta()
