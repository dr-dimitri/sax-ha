"""Pure ROI- und Amortisationsberechnung.

Siehe anforderung.yaml, REQ-ECONOMICS-AMORTIZATION. Die aktuellen Werte
bauen ausschließlich auf der persistierten Netto-Ersparnis auf. Lokale
Tageswerte bleiben für den Tageszähler und die bestehende Store-Kompatibilität
erhalten; eine künftige Amortisation wird nicht mehr prognostiziert.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

#: Höchstens so viele abgeschlossene Tages-Buckets werden persistiert.
MAX_STORED_DAYS = 60

#: Historische Schwellen bleiben für die Bewertung gespeicherter Tageswerte
#: erhalten. Sie lösen keine Amortisationsprognose mehr aus.
DAY_COVERAGE_THRESHOLD_PERCENT = 95.0
DAY_TIME_COVERAGE_THRESHOLD_PERCENT = 95.0

#: Regellänge eines Kalendertages in Sekunden. Die tatsächliche Länge des
#: lokalen Kalendertages bestimmt der Coordinator beim Tagesabschluss.
SECONDS_PER_DAY = 86_400.0


@dataclass(frozen=True, slots=True)
class DayEconomicsResult:
    """Ein abgeschlossener Kalendertag für Tageszähler und Store."""

    day: date
    operating_result_eur: float
    priced_charge_kwh: float
    unpriced_charge_kwh: float
    priced_discharge_kwh: float
    unpriced_discharge_kwh: float
    observed_seconds: float = 0.0
    day_length_seconds: float = SECONDS_PER_DAY

    @property
    def relevant_kwh(self) -> float:
        """Für die Preisabdeckung relevante Energiemenge dieses Tages."""
        return (
            self.priced_charge_kwh
            + self.unpriced_charge_kwh
            + self.priced_discharge_kwh
            + self.unpriced_discharge_kwh
        )

    @property
    def price_coverage_percent(self) -> float:
        """Anteil der relevanten Energie mit bekanntem Preis."""
        relevant = self.relevant_kwh
        if relevant <= 0:
            return 100.0
        priced = self.priced_charge_kwh + self.priced_discharge_kwh
        return priced / relevant * 100

    @property
    def meets_coverage_threshold(self) -> bool:
        return self.price_coverage_percent >= DAY_COVERAGE_THRESHOLD_PERCENT

    @property
    def time_coverage_percent(self) -> float:
        """Anteil des lokalen Kalendertages mit Datenpunkten."""
        if self.day_length_seconds <= 0:
            return 0.0
        return min(self.observed_seconds / self.day_length_seconds * 100, 100.0)

    @property
    def is_fully_observed(self) -> bool:
        return self.time_coverage_percent >= DAY_TIME_COVERAGE_THRESHOLD_PERCENT


def compute_roi_percent(
    operating_result_eur: float | None, investment_cost_eur: float | None
) -> float | None:
    """ROI in Prozent der Anschaffungskosten, bewusst ohne Klemmen."""
    if investment_cost_eur is None or investment_cost_eur <= 0:
        return None
    if operating_result_eur is None:
        return None
    return operating_result_eur / investment_cost_eur * 100


def compute_amortization_progress_percent(roi_percent: float | None) -> float | None:
    """Amortisationsfortschritt auf den Gauge-Bereich 0..100 begrenzen."""
    if roi_percent is None:
        return None
    return max(0.0, min(100.0, roi_percent))


def compute_remaining_to_payback_eur(
    investment_cost_eur: float | None, operating_result_eur: float | None
) -> float | None:
    """Noch nicht amortisierten Investitionsbetrag berechnen."""
    if investment_cost_eur is None or operating_result_eur is None:
        return None
    return max(investment_cost_eur - operating_result_eur, 0.0)
