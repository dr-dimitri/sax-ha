"""Pure status/coverage derivation für die Wirtschaftlichkeitsauswertung.

Siehe anforderung.yaml, REQ-ECONOMICS-OBSERVABILITY. Framework-unabhängig:
bekommt bereits ausgewertete Zustände (Store-Fehler, Bootstrap, Preis-
Verfügbarkeit, Herkunfts-/Preisabdeckung) als einfache Werte übergeben -
keine eigene Uhr, kein Zugriff auf Coordinator/Options/hass.
"""

from __future__ import annotations

from enum import StrEnum

#: Mindest-Preisabdeckung des laufenden Kalendertages, unterhalb derer der
#: Status auf partial_price_coverage wechselt. Bewusst eine Toleranz statt
#: eines exakten "< 100 %": eine einzelne unbepreiste Kilowattstunde ist im
#: Normalbetrieb praktisch unvermeidbar (der erste Tick nach einem Neustart
#: läuft oft, bevor die Preis-Integration ihre Entity angelegt hat, dazu
#: kommen kurze Tarifpausen und Intervalle unbekannter Herkunft) und darf
#: keinen Warnzustand auslösen (Issue #134). Derselbe Wert wie
#: domain.economics_amortization.DAY_COVERAGE_THRESHOLD_PERCENT, aber
#: bewusst eine eigene Konstante: dort entscheidet er über die
#: Verwertbarkeit eines abgeschlossenen Tages in der Prognose, hier über
#: die Anzeige des laufenden Tages.
PRICE_COVERAGE_THRESHOLD_PERCENT = 95.0


class EconomicsStatus(StrEnum):
    """Stabile, maschinenlesbare Zustände des Status-Sensors economics_status.

    Priorität (höchste zuerst): DISABLED (unabhängig von allem anderen,
    solange der Tarif deaktiviert ist) > STORAGE_ERROR >
    WAITING_FOR_INITIAL_STATE > PRICE_UNAVAILABLE > ORIGIN_UNAVAILABLE >
    PARTIAL_PRICE_COVERAGE > ACTIVE - siehe compute_economics_status.
    """

    DISABLED = "disabled"
    WAITING_FOR_INITIAL_STATE = "waiting_for_initial_state"
    ACTIVE = "active"
    PARTIAL_PRICE_COVERAGE = "partial_price_coverage"
    PRICE_UNAVAILABLE = "price_unavailable"
    ORIGIN_UNAVAILABLE = "origin_unavailable"
    STORAGE_ERROR = "storage_error"


def compute_economics_status(
    *,
    tariff_enabled: bool,
    storage_error: bool,
    started: bool,
    price_unavailable: bool,
    origin_unavailable: bool,
    charge_price_coverage_percent_today: float | None,
    discharge_price_coverage_percent_today: float | None,
) -> EconomicsStatus:
    """Bestimmt den einen zutreffenden Status aus mehreren, ggf. gleichzeitig
    zutreffenden Problemen - über eine feste Prioritätsreihenfolge, nicht
    über die Reihenfolge der Prüfungen im Aufrufer.

    `disabled` gilt ausschließlich bei deaktiviertem Tarif und schlägt dabei
    jeden anderen Zustand (auch einen Store-Fehler) - ohne konfigurierten
    Tarif ist der Zustand der Geldbilanz für den Anwender nicht relevant.

    Die beiden Abdeckungen sind ausdrücklich die des LAUFENDEN
    Kalendertages, nicht die seit economics_started_at kumulierten
    Lifetime-Quoten: `partial_price_coverage` soll melden, dass die Bilanz
    gerade jetzt nennenswerte Lücken hat, nicht dass sie irgendwann in
    ihrer Lebenszeit einmal eine hatte. Aus einer Lifetime-Quote (die nie
    zurückgeht) wäre der Zustand sonst nur noch über einen Bilanzneustart
    zu verlassen, der zugleich die gesamte Geldbilanz verwirft - ein
    dauerhaft anliegender Warnzustand wird ignoriert und der Sensor
    verlöre genau die Aussage, für die er gebaut ist (Issue #134).
    """
    if not tariff_enabled:
        return EconomicsStatus.DISABLED
    if storage_error:
        return EconomicsStatus.STORAGE_ERROR
    if not started:
        return EconomicsStatus.WAITING_FOR_INITIAL_STATE
    if price_unavailable:
        return EconomicsStatus.PRICE_UNAVAILABLE
    if origin_unavailable:
        return EconomicsStatus.ORIGIN_UNAVAILABLE
    partial = any(
        coverage is not None and coverage < PRICE_COVERAGE_THRESHOLD_PERCENT
        for coverage in (
            charge_price_coverage_percent_today,
            discharge_price_coverage_percent_today,
        )
    )
    if partial:
        return EconomicsStatus.PARTIAL_PRICE_COVERAGE
    return EconomicsStatus.ACTIVE


def compute_price_coverage_percent(
    priced_kwh: float | None, unpriced_kwh: float | None
) -> float | None:
    """Anteil (%) bepreister an gesamter relevanter Energie.

    Energiebasiert, nicht tickbasiert - eine kurze Preislücke bei geringer
    Leistung wiegt dadurch weniger als eine bei hoher Leistung. Bei Nenner 0
    (noch gar keine relevante Energie seit Start) 100 %, analog zu
    domain.economics_amortization.DayEconomicsResult.price_coverage_percent
    und domain.energy_accounting-Herkunftsabdeckung. None, solange einer der
    beiden zugrunde liegenden Zähler selbst noch nicht initialisiert ist.
    """
    if priced_kwh is None or unpriced_kwh is None:
        return None
    total = priced_kwh + unpriced_kwh
    if total <= 0:
        return 100.0
    return priced_kwh / total * 100
