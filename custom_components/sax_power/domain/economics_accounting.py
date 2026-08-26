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


NO_DELTA = EconomicsDelta()


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
    Einspeisevergütung. Fehlt der jeweilige Preis oder ist die Herkunft
    unbekannt, wird nichts erfunden - die Energie erhöht stattdessen
    `unvalued_inventory_kwh` (unbewerteter Bestand im Speicher) und den
    zugehörigen `unpriced_charge`-Zähler, statt später rückwirkend bewertet
    zu werden.

    Entladeseite: Jede Entladung verbraucht zuerst aus dem unbewerteten
    Bestand (`min(discharged_kwh, unvalued_inventory_kwh)`) - dieser Anteil
    erzeugt AUSDRÜCKLICH keinen vermiedenen Geldwert, weil für ihn nie eine
    Kostenbuchung stattfand: Andernfalls entstünde beim Entladen von
    Alt-/Unbekannt-Bestand ein kostenloser Scheingewinn (der Fehler aus dem
    verworfenen Issue #42). Nur der danach verbleibende, tatsächlich
    bepreist geladene Rest ("monetizable") ist den aktuellen
    Netzbezugspreis wert; fehlt dieser Preis, zählt der Rest als
    `unpriced_discharge` und wird ebenfalls nicht rückwirkend bewertet.

    `unvalued_inventory_kwh` ist der VOR diesem Intervall gültige Bestand -
    der Aufrufer trägt `unvalued_inventory_delta_kwh` nach.
    """
    grid_cost = 0.0
    pv_cost = 0.0
    unpriced_charge = 0.0
    inventory_delta = 0.0

    if charge_delta.grid_kwh:
        if import_price_eur_kwh is not None:
            grid_cost = charge_delta.grid_kwh * import_price_eur_kwh
        else:
            unpriced_charge += charge_delta.grid_kwh
            inventory_delta += charge_delta.grid_kwh

    if charge_delta.pv_kwh:
        if feed_in_price_eur_kwh is not None:
            pv_cost = charge_delta.pv_kwh * feed_in_price_eur_kwh
        else:
            unpriced_charge += charge_delta.pv_kwh
            inventory_delta += charge_delta.pv_kwh

    if charge_delta.unknown_kwh:
        # Herkunft unbekannt hat keinen Preisbegriff - unabhängig davon, ob
        # gerade ein Netzbezugspreis verfügbar wäre.
        unpriced_charge += charge_delta.unknown_kwh
        inventory_delta += charge_delta.unknown_kwh

    avoided_cost = 0.0
    unpriced_discharge = 0.0
    if discharged_kwh:
        available_inventory = max(unvalued_inventory_kwh, 0.0)
        consumed_from_inventory = min(discharged_kwh, available_inventory)
        inventory_delta -= consumed_from_inventory
        monetizable = discharged_kwh - consumed_from_inventory
        if monetizable:
            if import_price_eur_kwh is not None:
                avoided_cost = monetizable * import_price_eur_kwh
            else:
                unpriced_discharge = monetizable

    return EconomicsDelta(
        grid_charge_cost_delta=grid_cost,
        pv_opportunity_cost_delta=pv_cost,
        avoided_grid_cost_delta=avoided_cost,
        unvalued_inventory_delta_kwh=inventory_delta,
        unpriced_charge_delta_kwh=unpriced_charge,
        unpriced_discharge_delta_kwh=unpriced_discharge,
    )


def initial_unvalued_inventory_kwh(
    capacity_kwh: float | None, soc: float | None
) -> float | None:
    """Anfangsbestand beim erstmaligen Aktivieren der Auswertung.

    Bereits im Speicher liegende Energie ist zu diesem Zeitpunkt
    unbekannter Herkunft und darf beim ersten Entladen keinen kostenlosen
    Gewinn erzeugen (siehe anforderung.yaml, REQ-ECONOMICS-ACCOUNTING,
    "Ehrlicher Start"). None, solange Kapazität oder SOC nicht numerisch
    bekannt sind - der Aufrufer wartet dann mit der Aktivierung.
    """
    if capacity_kwh is None or soc is None:
        return None
    return capacity_kwh * soc / 100


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
