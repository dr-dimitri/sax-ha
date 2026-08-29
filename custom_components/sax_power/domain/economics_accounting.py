"""Pure computation of the operative money balance of the storage.

Siehe anforderung.yaml, REQ-ECONOMICS-ACCOUNTING. Framework-unabhängig:
verwendet ausschließlich den bereits berechneten `EnergyDelta` aus
domain/energy_accounting.py (02/06) sowie den zum Zeitpunkt gültigen
Netzbezugspreis/Einspeisevergütung (01/06) - keine eigene Uhr, kein eigener
Preisbegriff.

Bewertet wird ausschließlich tatsächlich gemessene Lade-/Entladeenergie,
nie ein Sollwert. PV-Ladung kostet die entgangene Einspeisevergütung,
Netzladung den zu diesem Zeitpunkt gültigen Netzbezugspreis, Entladung ist
den zu diesem Zeitpunkt vermiedenen Netzbezug wert.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .energy_accounting import EnergyDelta


@dataclass(frozen=True, slots=True)
class EconomicsDelta:
    """Geld- und Bestandszuwächse eines einzelnen Messintervalls.

    Alle Beträge in EUR, alle Mengen in kWh - ungerundet, volle
    Float-Präzision. `unvalued_inventory_delta_kwh` kann negativ sein
    (Entladung verbraucht Bestand).
    """

    grid_charge_cost_delta: float = 0.0
    pv_opportunity_cost_delta: float = 0.0
    avoided_grid_cost_delta: float = 0.0
    unvalued_inventory_delta_kwh: float = 0.0
    unpriced_charge_delta_kwh: float = 0.0
    unpriced_discharge_delta_kwh: float = 0.0
    # Energiemengen (kWh) hinter den beiden Kostenpositionen bzw. der
    # bepreisten Entladung - zusätzlich zu den Beträgen selbst, damit die
    # Tagesbilanz (REQ-ECONOMICS-AMORTIZATION) daraus die Preisabdeckung
    # eines Kalendertags bilden kann, ohne einen Betrag durch einen
    # (möglicherweise negativen oder 0) Preis zurückzurechnen.
    priced_charge_kwh_delta: float = 0.0
    priced_discharge_kwh_delta: float = 0.0


NO_DELTA = EconomicsDelta()


def compute_operating_result_high_water(
    previous_high_water_eur: float, operating_result_eur: float
) -> float:
    """Nichtnegativer historischer Peak für Diagnose und Store-Kompatibilität.

    Der Peak ist ausdrücklich keine Netto-Ersparnis und darf keine finanzielle
    Hauptkennzahl speisen: spätere Kosten müssen Ergebnis, ROI und Tageswert
    wieder reduzieren können (Issue #144).
    """
    return max(0.0, previous_high_water_eur, operating_result_eur)


def compute_economics_delta(
    charge_delta: EnergyDelta,
    discharged_kwh: float,
    unvalued_inventory_kwh: float,
    import_price_eur_kwh: float | None,
    feed_in_price_eur_kwh: float | None,
) -> EconomicsDelta:
    """Geldwert eines Mess-Intervalls aus bereits bekannter Energieherkunft.

    Ladeseite (siehe anforderung.yaml, REQ-ECONOMICS-ACCOUNTING):
    Netzladung kostet den Netzbezugspreis, PV-Ladung die entgangene
    Einspeisevergütung. Fehlt der jeweilige Preis, wird nichts erfunden -
    die Energie erhöht stattdessen `unvalued_inventory_kwh` (unbewerteter
    Bestand im Speicher) und den zugehörigen `unpriced_charge`-Zähler,
    statt später rückwirkend bewertet zu werden.

    Entladeseite: Jede Entladung verbraucht zuerst aus dem unbewerteten
    Bestand (`min(discharged_kwh, unvalued_inventory_kwh)`) - dieser Anteil
    erzeugt AUSDRÜCKLICH keinen vermiedenen Geldwert, weil für ihn nie eine
    Kostenbuchung stattfand: Andernfalls würde eine vorausgegangene
    Preislücke einen kostenlosen Scheingewinn erzeugen. Nur der danach
    verbleibende monetarisierbare Rest (bepreist geladen oder beim
    Bilanzstart mit 0 EUR angesetzt) ist den aktuellen Netzbezugspreis wert;
    fehlt dieser Preis, zählt der Rest als
    `unpriced_discharge` und wird ebenfalls nicht rückwirkend bewertet.

    `unvalued_inventory_kwh` ist der VOR diesem Intervall gültige Bestand -
    der Aufrufer trägt `unvalued_inventory_delta_kwh` nach.
    """
    grid_cost = 0.0
    pv_cost = 0.0
    unpriced_charge = 0.0
    priced_charge = 0.0
    inventory_delta = 0.0

    if charge_delta.charged_kwh and not charge_delta.origin_known:
        # Die Herkunftszähler dürfen bei fehlendem Smartmeter weiterhin die
        # vollständige Ladung konservativ als Netz ausweisen. Geld darf aus
        # dieser kompatibilitätsbedingten Fallback-Zuordnung jedoch weder bei
        # negativen Importpreisen noch bei hoher Einspeisevergütung entstehen.
        unpriced_charge = charge_delta.charged_kwh
        inventory_delta = charge_delta.charged_kwh
    elif charge_delta.grid_kwh:
        if import_price_eur_kwh is not None:
            grid_cost = charge_delta.grid_kwh * import_price_eur_kwh
            priced_charge += charge_delta.grid_kwh
        else:
            unpriced_charge += charge_delta.grid_kwh
            inventory_delta += charge_delta.grid_kwh

    if charge_delta.origin_known and charge_delta.pv_kwh:
        if feed_in_price_eur_kwh is not None:
            pv_cost = charge_delta.pv_kwh * feed_in_price_eur_kwh
            priced_charge += charge_delta.pv_kwh
        else:
            unpriced_charge += charge_delta.pv_kwh
            inventory_delta += charge_delta.pv_kwh

    avoided_cost = 0.0
    unpriced_discharge = 0.0
    priced_discharge = 0.0
    if discharged_kwh:
        available_inventory = max(unvalued_inventory_kwh, 0.0)
        consumed_from_inventory = min(discharged_kwh, available_inventory)
        inventory_delta -= consumed_from_inventory
        monetizable = discharged_kwh - consumed_from_inventory
        if monetizable:
            if import_price_eur_kwh is not None:
                avoided_cost = monetizable * import_price_eur_kwh
                priced_discharge = monetizable
            else:
                unpriced_discharge = monetizable

    return EconomicsDelta(
        grid_charge_cost_delta=grid_cost,
        pv_opportunity_cost_delta=pv_cost,
        avoided_grid_cost_delta=avoided_cost,
        unvalued_inventory_delta_kwh=inventory_delta,
        unpriced_charge_delta_kwh=unpriced_charge,
        unpriced_discharge_delta_kwh=unpriced_discharge,
        priced_charge_kwh_delta=priced_charge,
        priced_discharge_kwh_delta=priced_discharge,
    )


def min_soc_inventory_correction(
    unvalued_inventory_kwh: float, soc: float | None, soc_min: float | None
) -> float | None:
    """Korrektur des unbewerteten Bestands am SOC-Minimum, oder None.

    Erreicht der Speicher sein (geräteseitig gemeldetes) Minimum, ist keine
    nutzbare unbekannte Energie mehr vorhanden - ein verbleibender,
    rechnerisch nie ganz auf 0 gelaufener Rest (Rundungsdrift über viele
    Intervalle) darf dann verworfen werden. Liefert None, wenn keine
    Korrektur nötig bzw. möglich ist (SOC/Minimum unbekannt, SOC noch über
    dem Minimum, oder der Bestand ist ohnehin schon 0) - der Aufrufer soll
    diese Korrektur mit Zeitstempel diagnostisch protokollieren.
    """
    if soc is None or soc_min is None:
        return None
    if soc > soc_min:
        return None
    if unvalued_inventory_kwh <= 0:
        return None
    return 0.0


def capacity_inventory_correction(
    unvalued_inventory_kwh: float,
    capacity_kwh: float | None,
    soc: float | None,
    soc_resolution_percent: float,
) -> float | None:
    """Deckel des unbewerteten Bestands auf den Speicherinhalt, oder None.

    Der unbewertete Bestand ist ein Lagerbestand und kann nie größer sein
    als die anhand des quantisierten SOC sicher mögliche Energie. Ein
    gemeldeter SOC ist eine Stufengrenze; deshalb verwendet der Deckel den
    konservativen oberen Rand `soc + soc_resolution_percent` (Issue #145).
    Ohne
    diesen Deckel bliebe nach jedem unbepreisten Zyklus die Ladeverlust-
    Differenz (geladen > entladen) dauerhaft als Rest im Bestand liegen und
    würde später eine bereits bepreist geladene Entladung fälschlich als
    unbewertet abbuchen - der vermiedene Netzbezug fiele dauerhaft zu
    niedrig aus (Issue #132).

    Der Vorsichtsgedanke aus dem verworfenen Issue #42 bleibt unberührt: er
    verlangt nur, dass der Bestand nicht zu KLEIN ist. Liefert None, wenn
    keine Korrektur nötig bzw. möglich ist (Kapazität/SOC unbekannt -
    gegen einen unbekannten Wert wird nie geklemmt - oder der Bestand
    liegt ohnehin nicht über dem Speicherinhalt); der Aufrufer soll die
    Korrektur diagnostisch protokollieren.
    """
    if (
        capacity_kwh is None
        or soc is None
        or not math.isfinite(soc_resolution_percent)
        or soc_resolution_percent <= 0
    ):
        return None
    upper_soc = 0.0 if soc <= 0 else min(soc + soc_resolution_percent, 100.0)
    stored_kwh = max(capacity_kwh * upper_soc / 100, 0.0)
    if unvalued_inventory_kwh <= stored_kwh:
        return None
    return stored_kwh
