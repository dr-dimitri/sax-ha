"""Pure computation of per-interval charge energy origin.

Siehe anforderung.yaml, REQ-ENERGY-ORIGIN. Framework-unabhängig: Der
Coordinator liefert gemessene Leistungen und die verstrichene Zeit, dieses
Modul rechnet nur - kein Home Assistant, kein Modbus, keine eigene Uhr. Die
Zeitbasis ist exakt dieselbe wie bei energy_charged/energy_discharged
(coordinator._accumulate_energy) - es gibt keine zweite, parallele
Riemann-Summe.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EnergyDelta:
    """kWh-Zuwächse eines einzelnen Messintervalls.

    `charged_kwh` ist exakt derselbe Gesamt-Ladezuwachs, den der bestehende
    energy_charged-Zähler verbucht - Aufrufer müssen ihn dort ebenfalls
    verwenden statt ihn ein zweites Mal zu berechnen, damit Herkunfts- und
    Gesamtzähler niemals auseinanderlaufen. `grid_kwh + pv_kwh` ergibt
    `charged_kwh` bis auf Gleitkomma-Rundung in der Größenordnung
    einzelner ULPs - viele Zehnerpotenzen unterhalb der auf drei
    Nachkommastellen veröffentlichten Präzision. Es gibt bewusst keine
    dritte Kategorie: Physikalisch speist entweder PV oder das Netz, und
    jede Ladeenergie ist genau einer der beiden zugeordnet.

    `origin_known` trennt dabei eine gemessene Aufteilung von der
    kompatibilitätsbedingt als Netz ausgewiesenen Fallback-Zuordnung. Diese
    Qualitätsinformation muss bis zur Geldbilanz erhalten bleiben: Aus
    `grid_kwh == charged_kwh` allein lässt sich nicht erkennen, ob der
    Netzanteil gemessen oder nur wegen eines fehlenden Smartmeter-Werts
    angenommen wurde (Issue #146).
    """

    charged_kwh: float
    grid_kwh: float
    pv_kwh: float
    origin_known: bool = True


ZERO_DELTA = EnergyDelta(0.0, 0.0, 0.0)


def compute_charge_delta(
    storage_power_active: float | None,
    smartmeter_power: float | None,
    elapsed_hours: float,
) -> EnergyDelta | None:
    """Herkunft der Ladeenergie eines Messintervalls.

    Liefert None, wenn `storage_power_active` unbekannt ist - der Aufrufer
    muss das Intervall dann vollständig überspringen, exakt wie er es
    bereits für energy_charged/energy_discharged tut (ein unbekannter
    Leistungswert darf nie als "lädt nicht" gedeutet werden).

    Verbindliche Bilanzregel (siehe anforderung.yaml, REQ-ENERGY-ORIGIN):
    storage_power_active < 0 heißt Laden, smartmeter_power > 0 heißt
    Netzbezug. Netzbezug, der die aktuelle Ladeleistung übersteigt, deckt
    zusätzlich laufenden Hausverbrauch und zählt trotzdem vollständig als
    Netzladung - bei gleichzeitigem Hausverbrauch lässt sich der
    PV-Anteil aus storage_power_active und smartmeter_power allein nicht
    physikalisch eindeutig herleiten. Das ist eine konservative Schätzung
    anhand des Netzanschlusspunktes, keine physikalisch eindeutige
    Quellenzuordnung.

    Fehlt `smartmeter_power`, ist die Aufteilung nicht messbar. Die
    öffentlichen Herkunftszähler dürfen die Energie weiterhin vollständig
    als Netzladung ausweisen, `origin_known=False` verhindert aber eine
    monetäre Bewertung dieser bloßen Fallback-Annahme (Issue #146).
    """
    if storage_power_active is None:
        return None

    charge_power_w = max(-storage_power_active, 0.0)
    if charge_power_w == 0:
        return ZERO_DELTA

    charged_kwh = charge_power_w * elapsed_hours / 1000
    if smartmeter_power is None:
        return EnergyDelta(charged_kwh, charged_kwh, 0.0, origin_known=False)

    grid_charge_power_w = min(charge_power_w, max(smartmeter_power, 0.0))
    grid_kwh = grid_charge_power_w * elapsed_hours / 1000
    # pv_kwh als Rest von charged_kwh statt über eine zweite unabhängige
    # Multiplikation (pv_power_w * elapsed_hours / 1000): So bleibt die
    # Summe grid_kwh + pv_kwh in derselben Größenordnung wie charged_kwh
    # verankert, statt zwei unabhängig gerundete Werte gegeneinander
    # aufzusummieren.
    pv_kwh = charged_kwh - grid_kwh
    return EnergyDelta(charged_kwh, grid_kwh, pv_kwh)
