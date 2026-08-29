"""Framework-independent normalization of electricity prices to EUR/kWh.

Gemeinsame Quelle für die Ladeplanung (price_optimizer.py) und die
Wirtschaftlichkeitsauswertung (economics.py, siehe anforderung.yaml
REQ-ECONOMICS-TARIFFS) - beide müssen denselben Sensorwert identisch
interpretieren, sonst rechnet die Wirtschaftlichkeit gegen einen anderen
Preis, als die Ladeentscheidung ihn gesehen hat.
"""

from __future__ import annotations

from typing import Any

from ..const import (
    PRICE_UNIT_CT_KWH,
    PRICE_UNIT_CT_MWH,
    PRICE_UNIT_EUR_KWH,
    PRICE_UNIT_EUR_MWH,
)

_EXPLICIT_FACTORS = {
    PRICE_UNIT_EUR_KWH: 1.0,
    PRICE_UNIT_CT_KWH: 0.01,
    PRICE_UNIT_EUR_MWH: 0.001,
    PRICE_UNIT_CT_MWH: 0.00001,
}
_CURRENCY_FACTORS = {
    "eur": 1.0,
    "euro": 1.0,
    "€": 1.0,
    "ct": 0.01,
    "cent": 0.01,
    "cents": 0.01,
    "¢": 0.01,
}
_ENERGY_FACTORS = {"kwh": 1.0, "mwh": 0.001}


def unit_factor(configured_unit: str, sensor_unit: Any) -> float | None:
    """Umrechnungsfaktor auf EUR/kWh, oder None bei fremder Einheit.

    Eine explizit konfigurierte Einheit gewinnt immer. "auto" wertet die
    Einheit des Sensors aus; eine leere/fehlende Einheit gilt dabei als
    EUR/kWh (die Fehlinterpretation lässt sich über CONF_PRICE_UNIT
    korrigieren), eine gesetzte, aber nicht preisartige Einheit ("kWh",
    "W", "%") dagegen als Fehler - dort steht kein Arbeitspreis.
    """
    if configured_unit in _EXPLICIT_FACTORS:
        return _EXPLICIT_FACTORS[configured_unit]
    unit = "".join(str(sensor_unit or "").lower().split())
    if not unit:
        return 1.0
    parts = unit.split("/")
    if len(parts) != 2:
        return None
    currency, energy = parts
    currency_factor = _CURRENCY_FACTORS.get(currency)
    energy_factor = _ENERGY_FACTORS.get(energy)
    if currency_factor is None or energy_factor is None:
        return None
    return currency_factor * energy_factor
