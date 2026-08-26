"""Pure status/coverage derivation für die Wirtschaftlichkeitsauswertung.

Siehe anforderung.yaml, REQ-ECONOMICS-OBSERVABILITY. Framework-unabhängig:
bekommt bereits ausgewertete Zustände (Store-Fehler, Bootstrap, Preis-
Verfügbarkeit, Herkunfts-/Preisabdeckung) als einfache Werte übergeben -
keine eigene Uhr, kein Zugriff auf Coordinator/Options/hass.
"""

from __future__ import annotations

from enum import StrEnum


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
    charge_price_coverage_percent: float | None,
    discharge_price_coverage_percent: float | None,
) -> EconomicsStatus:
    """Bestimmt den einen zutreffenden Status aus mehreren, ggf. gleichzeitig
    zutreffenden Problemen - über eine feste Prioritätsreihenfolge, nicht
    über die Reihenfolge der Prüfungen im Aufrufer.

    `disabled` gilt ausschließlich bei deaktiviertem Tarif und schlägt dabei
    jeden anderen Zustand (auch einen Store-Fehler) - ohne konfigurierten
    Tarif ist der Zustand der Geldbilanz für den Anwender nicht relevant.
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
    partial = (
        charge_price_coverage_percent is not None
        and charge_price_coverage_percent < 100.0
    ) or (
        discharge_price_coverage_percent is not None
        and discharge_price_coverage_percent < 100.0
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
