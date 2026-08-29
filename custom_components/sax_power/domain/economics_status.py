"""Pure status/coverage derivation für die Wirtschaftlichkeitsauswertung.

Siehe anforderung.yaml, REQ-ECONOMICS-OBSERVABILITY. Framework-unabhängig:
bekommt bereits ausgewertete Zustände (Store-Fehler, Preis-
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

#: Absolute Untergrenze der Lücke, ab der die relative Schwelle überhaupt
#: geprüft wird. Ohne sie wäre die Toleranz rein relativ und träfe genau
#: den Fall nicht, für den sie gedacht ist: kurz nach Mitternacht ist der
#: Tagesbucket leer, ein einziges unbepreistes Intervall von 0,01 kWh
#: ergibt dann 0 % Abdeckung - und die Warnung stünde den ganzen Tag,
#: obwohl es um 10 Wh geht. 0,5 kWh liegt deutlich über solchen Resten
#: (ein Poll-Intervall bei voller Leistung sind ~0,01 kWh) und deutlich
#: unter einem echten Preisausfall (Stunden mit kWh im zweistelligen
#: Bereich).
MIN_UNPRICED_KWH_FOR_PARTIAL = 0.5


class EconomicsStatus(StrEnum):
    """Stabile, maschinenlesbare Zustände des Status-Sensors economics_status.

    Priorität (höchste zuerst): DISABLED (unabhängig von allem anderen,
    solange der Tarif deaktiviert ist) > STORAGE_ERROR > PRICE_UNAVAILABLE >
    ORIGIN_UNAVAILABLE >
    PARTIAL_PRICE_COVERAGE > ACTIVE - siehe compute_economics_status.
    """

    DISABLED = "disabled"
    ACTIVE = "active"
    PARTIAL_PRICE_COVERAGE = "partial_price_coverage"
    PRICE_UNAVAILABLE = "price_unavailable"
    ORIGIN_UNAVAILABLE = "origin_unavailable"
    STORAGE_ERROR = "storage_error"


def compute_economics_status(
    *,
    tariff_enabled: bool,
    storage_error: bool,
    price_unavailable: bool,
    origin_unavailable: bool,
    priced_charge_kwh_today: float | None,
    unpriced_charge_kwh_today: float | None,
    priced_discharge_kwh_today: float | None,
    unpriced_discharge_kwh_today: float | None,
) -> EconomicsStatus:
    """Bestimmt den einen zutreffenden Status aus mehreren, ggf. gleichzeitig
    zutreffenden Problemen - über eine feste Prioritätsreihenfolge, nicht
    über die Reihenfolge der Prüfungen im Aufrufer.

    `disabled` gilt ausschließlich bei deaktiviertem Tarif und schlägt dabei
    jeden anderen Zustand (auch einen Store-Fehler) - ohne konfigurierten
    Tarif ist der Zustand der Geldbilanz für den Anwender nicht relevant.

    Die vier Energiemengen sind ausdrücklich die des LAUFENDEN
    Kalendertages, nicht die seit economics_started_at kumulierten
    Lifetime-Zähler: `partial_price_coverage` soll melden, dass die Bilanz
    gerade jetzt nennenswerte Lücken hat, nicht dass sie irgendwann in
    ihrer Lebenszeit einmal eine hatte. Aus einer Lifetime-Quote (die nie
    zurückgeht) wäre der Zustand sonst nur noch über einen Bilanzneustart
    zu verlassen, der zugleich die gesamte Geldbilanz verwirft - ein
    dauerhaft anliegender Warnzustand wird ignoriert und der Sensor
    verlöre genau die Aussage, für die er gebaut ist (Issue #134).

    Bewusst NICHT erfasst ist die Entladung aus dem unbewerteten Bestand
    (REQ-ECONOMICS-ACCOUNTING): sie ist weder bepreiste noch unbepreiste
    Entladung und bewegt deshalb keinen der vier Werte. Die zugehörige
    Lücke wird an dem Tag gemeldet, an dem die nicht bepreisbare LADUNG
    stattfand - dort entsteht sie, und dort ist sie behebbar. Ein
    späterer Tag, an dem dieser Bestand entladen wird, ist rechnerisch
    einwandfrei (das Ergebnis ist korrekt 0 EUR, nicht unbekannt) und
    bleibt deshalb active.
    """
    if not tariff_enabled:
        return EconomicsStatus.DISABLED
    if storage_error:
        return EconomicsStatus.STORAGE_ERROR
    if price_unavailable:
        return EconomicsStatus.PRICE_UNAVAILABLE
    if origin_unavailable:
        return EconomicsStatus.ORIGIN_UNAVAILABLE
    partial = is_price_coverage_partial(
        priced_charge_kwh_today, unpriced_charge_kwh_today
    ) or is_price_coverage_partial(
        priced_discharge_kwh_today, unpriced_discharge_kwh_today
    )
    if partial:
        return EconomicsStatus.PARTIAL_PRICE_COVERAGE
    return EconomicsStatus.ACTIVE


def is_price_coverage_partial(
    priced_kwh: float | None, unpriced_kwh: float | None
) -> bool:
    """Fällt die Preislücke einer Seite (Laden ODER Entladen) ins Gewicht?

    Verlangt beides: eine absolut nennenswerte Lücke
    (MIN_UNPRICED_KWH_FOR_PARTIAL) UND einen relativ nennenswerten Anteil
    (unterhalb PRICE_COVERAGE_THRESHOLD_PERCENT). Beide Schwellen
    zusammen sind nötig - die relative allein lässt eine winzige Lücke in
    einem noch leeren Tagesbucket auf 0 % Abdeckung laufen, die absolute
    allein würde jeden längeren Preisausfall an einem energiereichen Tag
    verschweigen. Zähler, die noch nicht initialisiert sind (None), sind
    kein Abdeckungsproblem - das deckt bereits storage_error ab.
    """
    if priced_kwh is None or unpriced_kwh is None:
        return False
    if unpriced_kwh < MIN_UNPRICED_KWH_FOR_PARTIAL:
        return False
    coverage = compute_price_coverage_percent(priced_kwh, unpriced_kwh)
    return coverage is not None and coverage < PRICE_COVERAGE_THRESHOLD_PERCENT


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
