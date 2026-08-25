"""Framework-independent normalization of electricity prices to EUR/kWh.

Gemeinsame Quelle für die Ladeplanung (price_optimizer.py) und die
Wirtschaftlichkeitsauswertung (economics.py, siehe anforderung.yaml
REQ-ECONOMICS-TARIFFS) - beide müssen denselben Sensorwert identisch
interpretieren, sonst rechnet die Wirtschaftlichkeit gegen einen anderen
Preis, als die Ladeentscheidung ihn gesehen hat.
"""

from __future__ import annotations

from typing import Any

from ..const import PRICE_UNIT_CT_KWH, PRICE_UNIT_EUR_KWH

# Einheitentexte, die eindeutig auf Cent bzw. Euro hindeuten. Bewusst als
# Teilstring geprüft: die Sensoren schreiben "ct/kWh", "EUR/kWh", "€/kWh",
# "Cent/kWh" und Mischformen davon.
_CENT_MARKERS = ("ct", "cent", "¢")
_EURO_MARKERS = ("eur", "€")


def unit_factor(configured_unit: str, sensor_unit: Any) -> float | None:
    """Umrechnungsfaktor auf EUR/kWh, oder None bei fremder Einheit.

    Eine explizit konfigurierte Einheit gewinnt immer. "auto" wertet die
    Einheit des Sensors aus; eine leere/fehlende Einheit gilt dabei als
    EUR/kWh (die Fehlinterpretation lässt sich über CONF_PRICE_UNIT
    korrigieren), eine gesetzte, aber nicht preisartige Einheit ("kWh",
    "W", "%") dagegen als Fehler - dort steht kein Arbeitspreis.
    """
    if configured_unit == PRICE_UNIT_CT_KWH:
        return 0.01
    if configured_unit == PRICE_UNIT_EUR_KWH:
        return 1.0
    unit = str(sensor_unit or "").strip().lower()
    if not unit:
        return 1.0
    if any(marker in unit for marker in _CENT_MARKERS):
        return 0.01
    if any(marker in unit for marker in _EURO_MARKERS):
        return 1.0
    return None
