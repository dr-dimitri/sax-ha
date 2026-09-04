"""Persist the active fixed-horizon price-planning cycle.

Siehe anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE. Der Snapshot enthält
nicht den kompletten, aus dem Preis-Sensor jederzeit rekonstruierbaren
Ladeplan, sondern nur dessen Zeitbudget: Zyklusgrenzen, Budget und alle
bereits verstrichenen bzw. aktuell noch ausgewählten Intervalle.
"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from ..const import (
    DOMAIN,
    MAX_PRICE_HOURS,
    PRICE_PLAN_HORIZON_HOURS,
    PRICE_STRATEGY_RELATIVE,
    PRICE_STRATEGY_SMART,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.price_plan"
PRICE_PLAN_SAVE_DELAY = 10


@dataclass(frozen=True)
class PricePlanInterval:
    """Ein bereits belegter oder aktuell geplanter UTC-Zeitabschnitt."""

    start: datetime
    end: datetime


@dataclass(frozen=True)
class SmartBudgetInputs:
    """Bedarfsrelevante Eingänge der letzten Smart-Planung."""

    target_soc: int
    configured_hours: int
    current_soc: int | None
    capacity_kwh: float | None
    charge_power_w: int | None
    pv_forecast_kwh: float | None
    pv_factor: float


@dataclass(frozen=True)
class PricePlanCycleState:
    """Persistiertes Zeitbudget eines festen 24-Stunden-Zyklus."""

    anchor: datetime
    end: datetime
    strategy: str
    budget_seconds: float
    intervals: tuple[PricePlanInterval, ...] = ()
    smart_inputs: SmartBudgetInputs | None = None


class PricePlanCycleStore:
    """Persist one price-planning cycle per config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry_id}",
        )
        self._last_persisted: dict[str, Any] | None = None
        self._pending: dict[str, Any] | None = None
        self._save_scheduled = False

    async def async_load(self) -> PricePlanCycleState | None:
        """Load a cycle, discarding the complete snapshot when inconsistent."""
        raw = await self._store.async_load()
        if raw is None:
            return None
        if not isinstance(raw, dict):
            _LOGGER.warning(
                "Ungültigen gespeicherten Preisplan-Zyklus verworfen: kein Objekt"
            )
            return None
        self._last_persisted = raw
        if raw.get("active") is False:
            return None

        try:
            state = _deserialize(raw)
        except (TypeError, ValueError) as err:
            _LOGGER.warning(
                "Ungültigen gespeicherten Preisplan-Zyklus verworfen: %s", err
            )
            return None
        return state

    @callback
    def async_delay_save(
        self,
        state: PricePlanCycleState | None,
        delay: float = PRICE_PLAN_SAVE_DELAY,
    ) -> bool:
        """Coalesce plan changes and avoid writes for unchanged allocations."""
        payload = _serialize(state)
        if payload == (self._pending or self._last_persisted):
            return False
        self._pending = payload
        if not self._save_scheduled:
            self._save_scheduled = True
            self._store.async_delay_save(self._consume_pending, delay)
        return True

    async def async_save(self, state: PricePlanCycleState | None) -> None:
        """Immediately persist the newest cycle and cancel a delayed write."""
        payload = _serialize(state)
        self._pending = None
        self._save_scheduled = False
        await self._store.async_save(payload)
        self._last_persisted = payload

    def _consume_pending(self) -> dict[str, Any]:
        payload = self._pending or self._last_persisted or {"active": False}
        self._pending = None
        self._save_scheduled = False
        self._last_persisted = payload
        return payload


def _serialize(state: PricePlanCycleState | None) -> dict[str, Any]:
    if state is None:
        return {"active": False}
    return {
        "active": True,
        "anchor": state.anchor.astimezone(UTC).isoformat(),
        "end": state.end.astimezone(UTC).isoformat(),
        "strategy": state.strategy,
        "budget_seconds": state.budget_seconds,
        "intervals": [
            {
                "start": interval.start.astimezone(UTC).isoformat(),
                "end": interval.end.astimezone(UTC).isoformat(),
            }
            for interval in state.intervals
        ],
        "smart_inputs": (
            None if state.smart_inputs is None else asdict(state.smart_inputs)
        ),
    }


def _deserialize(raw: dict[str, Any]) -> PricePlanCycleState:
    anchor = _timestamp(raw.get("anchor"), "Zyklusanker")
    end = _timestamp(raw.get("end"), "Zyklusende")
    if end - anchor != timedelta(hours=PRICE_PLAN_HORIZON_HOURS):
        raise ValueError("Zyklus ist nicht genau 24 Stunden lang")

    strategy = raw.get("strategy")
    if strategy not in (PRICE_STRATEGY_RELATIVE, PRICE_STRATEGY_SMART):
        raise ValueError(f"unbekannte Strategie {strategy!r}")

    budget_seconds = _finite_number(raw.get("budget_seconds"), "Zeitbudget")
    if not 0 <= budget_seconds <= MAX_PRICE_HOURS * 3600:
        raise ValueError(f"Zeitbudget außerhalb des Wertebereichs: {budget_seconds!r}")

    raw_intervals = raw.get("intervals")
    if not isinstance(raw_intervals, list):
        raise ValueError("Intervalle sind keine Liste")
    intervals: list[PricePlanInterval] = []
    previous_end: datetime | None = None
    for raw_interval in raw_intervals:
        if not isinstance(raw_interval, dict):
            raise ValueError("Intervall ist kein Objekt")
        start = _timestamp(raw_interval.get("start"), "Intervallbeginn")
        interval_end = _timestamp(raw_interval.get("end"), "Intervallende")
        if not anchor <= start < interval_end <= end:
            raise ValueError("Intervall liegt außerhalb des Zyklus")
        if previous_end is not None and start < previous_end:
            raise ValueError("Intervalle sind nicht sortiert oder überschneiden sich")
        previous_end = interval_end
        intervals.append(PricePlanInterval(start, interval_end))

    raw_smart = raw.get("smart_inputs")
    smart_inputs = None
    if raw_smart is not None:
        if strategy != PRICE_STRATEGY_SMART or not isinstance(raw_smart, dict):
            raise ValueError("Smart-Eingänge passen nicht zur Strategie")
        smart_inputs = SmartBudgetInputs(
            target_soc=_integer(raw_smart.get("target_soc"), "Ziel-SOC"),
            configured_hours=_integer(
                raw_smart.get("configured_hours"), "konfigurierte Stunden"
            ),
            current_soc=_optional_integer(
                raw_smart.get("current_soc"), "aktueller SOC"
            ),
            capacity_kwh=_optional_number(
                raw_smart.get("capacity_kwh"), "Speicherkapazität"
            ),
            charge_power_w=_optional_integer(
                raw_smart.get("charge_power_w"), "Ladeleistung"
            ),
            pv_forecast_kwh=_optional_number(
                raw_smart.get("pv_forecast_kwh"), "PV-Prognose"
            ),
            pv_factor=_finite_number(raw_smart.get("pv_factor"), "PV-Faktor"),
        )
    elif strategy == PRICE_STRATEGY_SMART:
        raise ValueError("Smart-Eingänge fehlen")

    return PricePlanCycleState(
        anchor=anchor,
        end=end,
        strategy=strategy,
        budget_seconds=budget_seconds,
        intervals=tuple(intervals),
        smart_inputs=smart_inputs,
    )


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} ist kein Zeitstempel")
    parsed = dt_util.parse_datetime(value)
    if parsed is None or parsed.tzinfo is None:
        raise ValueError(f"{label} ist ungültig")
    return parsed.astimezone(UTC)


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} ist keine Zahl")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} ist nicht endlich")
    return result


def _optional_number(value: Any, label: str) -> float | None:
    return None if value is None else _finite_number(value, label)


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} ist keine Ganzzahl")
    return value


def _optional_integer(value: Any, label: str) -> int | None:
    return None if value is None else _integer(value, label)
