"""Preisoptimiertes Laden: Auswertung der Preisdaten und Ladeplanung.

Reine Rechen- und Auswertungslogik ohne jeden Modbus-Zugriff (siehe
AGENTS.md: sämtliche Register-Reads/-Writes gehören in den Coordinator).
Dieses Modul liest ausschließlich Home-Assistant-Zustände - den vom
Anwender im Options Flow ausgewählten Strompreis-Sensor sowie optional
einen PV-Prognose-Sensor - und leitet daraus ab, ob und wann aus dem Netz
geladen werden soll. Der Coordinator übernimmt diese Entscheidung und
setzt sie über den vorhandenen SunSpec-Schreibpfad um.

Siehe anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_PRICE_ATTRIBUTE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    CONF_PV_FORECAST_FACTOR,
    CONF_PV_FORECAST_SENSOR,
    DEFAULT_PRICE_SLOT_MINUTES,
    DEFAULT_PRICE_UNIT,
    DEFAULT_PV_FORECAST_FACTOR,
    MAX_SOC,
    PRICE_EVAL_INTERVAL,
    PRICE_PLAN_HORIZON_HOURS,
    PRICE_STATUS_CHARGING,
    PRICE_STATUS_NO_PRICE_DATA,
    PRICE_STATUS_OFF,
    PRICE_STATUS_PV_FORECAST_COVERS,
    PRICE_STATUS_WAITING,
    PRICE_STRATEGY_ABSOLUTE,
    PRICE_STRATEGY_OFF,
    PRICE_STRATEGY_SMART,
    PRICE_UNIT_CT_KWH,
    PRICE_UNIT_EUR_KWH,
)

if TYPE_CHECKING:
    from .coordinator import SaxPowerCoordinator

_LOGGER = logging.getLogger(__name__)

# Attributnamen, unter denen verbreitete Strompreis-Integrationen ihre
# Preisvorschau ablegen. Gruppenweise geprüft (erste Gruppe, die überhaupt
# Slots liefert, gewinnt), damit Sensoren mit mehreren parallelen
# Darstellungen nicht doppelt eingelesen werden:
#   ("raw_today", "raw_tomorrow")  Nordpool, EPEX Spot
#   ("today", "tomorrow")          Tibber (Listen aus Zahlen)
#   ("data",)                      ENTSO-e, Awattar
#   ("forecast",)/("prices",)      diverse Template-/HACS-Sensoren
# Über CONF_PRICE_ATTRIBUTE lässt sich stattdessen ein einzelnes Attribut
# fest vorgeben, falls die Automatik bei einem Sensor danebenliegt.
ATTRIBUTE_GROUPS: tuple[tuple[str, ...], ...] = (
    ("raw_today", "raw_tomorrow"),
    ("today", "tomorrow"),
    ("data",),
    ("forecast",),
    ("prices",),
    ("price_data",),
    ("raw_two_days",),
)

# Schlüssel innerhalb eines Listeneintrags (dict), unter denen Startzeit
# bzw. Preis stehen können - in dieser Reihenfolge geprüft.
_START_KEYS = (
    "start",
    "start_time",
    "startsAt",
    "starts_at",
    "from",
    "time",
    "datetime",
    "hour",
)
_END_KEYS = ("end", "end_time", "endsAt", "ends_at", "to")
_PRICE_KEYS = (
    "value",
    "price",
    "total",
    "cost",
    "marketprice",
    "price_per_kwh",
    "amount",
)


@dataclass(frozen=True)
class PriceSlot:
    """Ein Preis-Zeitfenster (üblicherweise 60 oder 15 Minuten)."""

    start: datetime
    end: datetime
    price: float

    def overlaps(self, moment: datetime) -> bool:
        return self.start <= moment < self.end

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "price": round(self.price, 5),
        }


@dataclass(frozen=True)
class PriceChargeContext:
    """Alle Eingangsgrößen einer Planberechnung.

    Bewusst ein reines Datenobjekt statt eines Zugriffs auf den Coordinator:
    macht compute_plan() ohne Home-Assistant-Instanz testbar.
    """

    enabled: bool
    strategy: str
    max_price: float | None
    hours: int
    target_soc: int
    current_soc: int | None
    capacity_kwh: float | None
    charge_power_w: int | None
    pv_forecast_kwh: float | None
    pv_factor: float


@dataclass(frozen=True)
class PricePlan:
    """Ergebnis einer Planberechnung.

    `status` ist der rein preisseitige Status. Der Coordinator kann ihn
    überschreiben, sobald ein Grund außerhalb der Preislogik das Laden
    verhindert (Max-SOC-Sperre, PV-Überschuss, fehlende Ladeleistung) -
    siehe SaxPowerCoordinator._price_charge_status_text.
    """

    status: str = PRICE_STATUS_OFF
    charge_now: bool = False
    next_start: datetime | None = None
    slots: tuple[PriceSlot, ...] = ()
    current_price: float | None = None
    threshold: float | None = None
    needed_hours: int | None = None
    pv_forecast_kwh: float | None = None


EMPTY_PLAN = PricePlan()


# --------------------------------------------------------------------------
# Preisdaten einlesen
# --------------------------------------------------------------------------
def _unit_factor(configured_unit: str, sensor_unit: Any) -> float:
    """Umrechnungsfaktor auf EUR/kWh.

    "auto" wertet die Einheit des Sensors aus: alles, was nach Cent aussieht
    (ct, cent, ¢), wird durch 100 geteilt. Ist keine Einheit hinterlegt,
    bleibt der Wert unverändert - eine Fehlinterpretation lässt sich dann
    über CONF_PRICE_UNIT explizit korrigieren.
    """
    if configured_unit == PRICE_UNIT_CT_KWH:
        return 0.01
    if configured_unit == PRICE_UNIT_EUR_KWH:
        return 1.0
    unit = str(sensor_unit or "").lower()
    if "ct" in unit or "cent" in unit or "¢" in unit:
        return 0.01
    return 1.0


def _coerce_datetime(value: Any, base_day: datetime | None) -> datetime | None:
    """Startzeit eines Listeneintrags in eine lokale datetime umwandeln.

    Neben ISO-Strings und datetime-Objekten wird auch eine reine
    Stundenzahl unterstützt (Attribut "hour" mancher Template-Sensoren) -
    dafür wird `base_day` (lokale Mitternacht des betreffenden Tages)
    benötigt.
    """
    if isinstance(value, datetime):
        return dt_util.as_local(value)
    if isinstance(value, str):
        parsed = dt_util.parse_datetime(value)
        if parsed is not None:
            return dt_util.as_local(parsed)
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if base_day is None:
            return None
        return base_day + timedelta(hours=float(value))
    return None


def _coerce_price(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        price = float(value)
    except TypeError, ValueError:
        return None
    if not math.isfinite(price):
        return None
    return price


def _entry_values(
    entry: Any, base_day: datetime | None, index: int, count: int
) -> tuple[datetime | None, datetime | None, float | None]:
    """(start, end, preis) eines einzelnen Listeneintrags.

    Reine Zahlen (Tibber-Stil: 24 bzw. 96 Werte für einen Kalendertag)
    werden gleichmäßig über den Tag verteilt, dafür wird `base_day`
    benötigt. Dicts liefern Start (und optional Ende) selbst.
    """
    if isinstance(entry, Mapping):
        start = None
        for key in _START_KEYS:
            if key in entry:
                start = _coerce_datetime(entry[key], base_day)
                if start is not None:
                    break
        end = None
        for key in _END_KEYS:
            if key in entry:
                end = _coerce_datetime(entry[key], base_day)
                if end is not None:
                    break
        price = None
        for key in _PRICE_KEYS:
            if key in entry:
                price = _coerce_price(entry[key])
                if price is not None:
                    break
        return start, end, price

    price = _coerce_price(entry)
    if price is None or base_day is None or count <= 0:
        return None, None, price
    slot = timedelta(days=1) / count
    start = base_day + slot * index
    return start, start + slot, price


def _base_day(attribute: str, now: datetime) -> datetime:
    """Lokale Mitternacht des Tages, auf den sich ein Attribut bezieht."""
    day = dt_util.start_of_local_day(now)
    if "tomorrow" in attribute:
        return day + timedelta(days=1)
    return day


def _parse_entries(
    entries: Sequence[Any], base_day: datetime | None
) -> list[tuple[datetime, datetime | None, float]]:
    parsed: list[tuple[datetime, datetime | None, float]] = []
    count = len(entries)
    for index, entry in enumerate(entries):
        start, end, price = _entry_values(entry, base_day, index, count)
        if start is None or price is None:
            continue
        parsed.append((start, end, price))
    return parsed


def _finalize_slots(
    raw: Iterable[tuple[datetime, datetime | None, float]], factor: float
) -> list[PriceSlot]:
    """Rohdaten zu einer lückenlos sortierten, entdoppelten Slot-Liste.

    Fehlt bei einem Eintrag das Ende, wird der Beginn des nächsten Slots
    verwendet; beim letzten Eintrag die häufigste Länge der übrigen Slots
    (Fallback DEFAULT_PRICE_SLOT_MINUTES). Damit funktionieren sowohl
    stündliche als auch viertelstündliche Preisdaten ohne Sonderfall.
    """
    by_start: dict[datetime, tuple[datetime | None, float]] = {}
    for start, end, price in raw:
        by_start.setdefault(start, (end, price))
    starts = sorted(by_start)
    if not starts:
        return []

    gaps = [(starts[i + 1] - starts[i]).total_seconds() for i in range(len(starts) - 1)]
    positive_gaps = [gap for gap in gaps if gap > 0]
    default_seconds = (
        min(positive_gaps)
        if positive_gaps
        else DEFAULT_PRICE_SLOT_MINUTES * 60  # nur ein einziger Slot bekannt
    )

    slots: list[PriceSlot] = []
    for index, start in enumerate(starts):
        end, price = by_start[start]
        if end is None or end <= start:
            if index + 1 < len(starts):
                end = starts[index + 1]
            else:
                end = start + timedelta(seconds=default_seconds)
        slots.append(PriceSlot(start=start, end=end, price=price * factor))
    return slots


def parse_price_slots(
    state: Any,
    *,
    attribute: str | None = None,
    unit: str = DEFAULT_PRICE_UNIT,
    now: datetime | None = None,
) -> list[PriceSlot]:
    """Preis-Slots aus dem Zustand einer beliebigen Preis-Sensor-Entity.

    Unterstützt die verbreiteten Attributformate (siehe ATTRIBUTE_GROUPS):
    Listen von Dicts mit Start-/Preisfeldern (Nordpool, EPEX Spot, ENTSO-e,
    Awattar) ebenso wie reine Zahlenlisten für einen Kalendertag (Tibber).
    Gibt eine leere Liste zurück, wenn sich nichts Verwertbares finden
    lässt - der Aufrufer meldet das dann als "Keine Preisdaten".
    """
    if state is None:
        return []
    attributes: Mapping[str, Any] = getattr(state, "attributes", {}) or {}
    factor = _unit_factor(unit, attributes.get("unit_of_measurement"))
    now = now or dt_util.now()

    groups: tuple[tuple[str, ...], ...] = (
        ((attribute,),) if attribute else ATTRIBUTE_GROUPS
    )
    for group in groups:
        raw: list[tuple[datetime, datetime | None, float]] = []
        for name in group:
            entries = attributes.get(name)
            if not isinstance(entries, (list, tuple)) or not entries:
                continue
            raw.extend(_parse_entries(entries, _base_day(name, now)))
        if raw:
            return _finalize_slots(raw, factor)
    return []


def current_price(slots: Sequence[PriceSlot], moment: datetime) -> float | None:
    for slot in slots:
        if slot.overlaps(moment):
            return slot.price
    return None


# --------------------------------------------------------------------------
# Planberechnung
# --------------------------------------------------------------------------
def _cheapest_slots(
    slots: Sequence[PriceSlot], hours: float, now: datetime
) -> list[PriceSlot]:
    """Die günstigsten Slots, bis `hours` Ladedauer zusammenkommen.

    Aufsummiert wird die noch verbleibende Dauer (bei einem bereits
    laufenden Slot also nur der Rest), damit "3 günstigste Stunden" auch
    dann drei tatsächlich nutzbare Stunden ergibt, wenn die Auswahl mitten
    in einem Slot berechnet wird. Bei Preisgleichheit gewinnt der frühere
    Slot, damit der Plan bei identischen Preisen stabil bleibt.
    """
    if hours <= 0:
        return []
    target = timedelta(hours=hours)
    collected = timedelta()
    chosen: list[PriceSlot] = []
    for slot in sorted(slots, key=lambda item: (item.price, item.start)):
        if collected >= target:
            break
        chosen.append(slot)
        collected += slot.end - max(slot.start, now)
    return sorted(chosen, key=lambda item: item.start)


def _smart_required_hours(ctx: PriceChargeContext) -> tuple[float | None, float]:
    """(benötigte Ladestunden, eingerechnete PV-Prognose in kWh).

    Rechnet den noch fehlenden Energiebedarf bis zu ctx.target_soc ("Max.
    SOC", keine eigene Einstellung) aus und zieht davon den Teil der
    PV-Prognose ab, der laut Konfiguration tatsächlich
    im Speicher landen dürfte. Bleibt nichts übrig, wird gar nicht aus dem
    Netz geladen (Rückgabe 0.0) - genau das ist der Zweck des Smart-Modus:
    nachts keinen teuren Netzstrom kaufen, wenn morgen genug kostenlose
    Sonne kommt.

    Fehlen die dafür nötigen Größen (Kapazität aus dem SunSpec-Block, SOC
    oder Ladeleistung), ist keine Bedarfsrechnung möglich - Rückgabe None,
    der Aufrufer fällt dann auf die reine Stundenauswahl zurück.
    """
    usable_pv = max(0.0, (ctx.pv_forecast_kwh or 0.0) * ctx.pv_factor)
    if (
        ctx.capacity_kwh is None
        or ctx.capacity_kwh <= 0
        or ctx.current_soc is None
        or not ctx.charge_power_w
    ):
        return None, usable_pv

    missing_kwh = max(0.0, (ctx.target_soc - ctx.current_soc) / 100 * ctx.capacity_kwh)
    remaining_kwh = max(0.0, missing_kwh - usable_pv)
    if remaining_kwh <= 0:
        return 0.0, usable_pv
    return remaining_kwh / (ctx.charge_power_w / 1000), usable_pv


def compute_plan(
    now: datetime, slots: Sequence[PriceSlot], ctx: PriceChargeContext
) -> PricePlan:
    """Ladeplan für den aktuellen Zeitpunkt.

    Der Plan beschreibt ausschließlich die Preis-/Prognoseseite: welche
    Zeitfenster ausgewählt sind, ob eines davon gerade läuft und wann das
    nächste beginnt. Ob tatsächlich geladen wird, entscheidet der
    Coordinator zusätzlich anhand von Max-SOC-Sperre, PV-Überschuss und
    Vorrang der (zeitgesteuerten) Netzladung.
    """
    price_now = current_price(slots, now)
    if not ctx.enabled or ctx.strategy == PRICE_STRATEGY_OFF:
        return PricePlan(status=PRICE_STATUS_OFF, current_price=price_now)

    horizon_end = now + timedelta(hours=PRICE_PLAN_HORIZON_HOURS)
    future = [slot for slot in slots if slot.end > now and slot.start < horizon_end]
    if not future:
        return PricePlan(
            status=PRICE_STATUS_NO_PRICE_DATA,
            current_price=price_now,
        )

    needed_hours: float | None = None
    pv_usable: float | None = None
    status = PRICE_STATUS_WAITING

    if ctx.strategy == PRICE_STRATEGY_ABSOLUTE:
        threshold = ctx.max_price
        selected = (
            []
            if threshold is None
            else [slot for slot in future if slot.price <= threshold]
        )
    else:
        if ctx.strategy == PRICE_STRATEGY_SMART:
            required, pv_usable = _smart_required_hours(ctx)
            if required is not None and required <= 0:
                return PricePlan(
                    status=PRICE_STATUS_PV_FORECAST_COVERS,
                    current_price=price_now,
                    needed_hours=0,
                    pv_forecast_kwh=pv_usable,
                )
            # Der Schieberegler "Anzahl Stunden" bleibt im Smart-Modus die
            # Obergrenze: er begrenzt, wie viel Netzstrom der Anwender
            # maximal einkaufen möchte, auch wenn rechnerisch mehr nötig
            # wäre.
            needed_hours = (
                float(ctx.hours)
                if required is None
                else min(float(ctx.hours), required)
            )
        else:
            needed_hours = float(ctx.hours)
        selected = _cheapest_slots(future, needed_hours, now)
        threshold = max((slot.price for slot in selected), default=None)

    charge_now = any(slot.overlaps(now) for slot in selected)
    if charge_now:
        status = PRICE_STATUS_CHARGING
        next_start = next(slot.start for slot in selected if slot.overlaps(now))
    else:
        next_start = next((slot.start for slot in selected if slot.start > now), None)

    return PricePlan(
        status=status,
        charge_now=charge_now,
        next_start=next_start,
        slots=tuple(selected),
        current_price=price_now,
        threshold=threshold,
        needed_hours=None if needed_hours is None else math.ceil(needed_hours),
        pv_forecast_kwh=pv_usable,
    )


# --------------------------------------------------------------------------
# Anbindung an Home Assistant
# --------------------------------------------------------------------------
class SaxPricePlanner:
    """Hält den aktuellen Ladeplan und rechnet ihn periodisch neu.

    Die Neuberechnung läuft in PRICE_EVAL_INTERVAL (60s, siehe
    anforderung.yaml REQ-DYNAMIC-PRICE-CHARGE) - zusätzlich sofort, sobald
    sich der Preis- oder Prognose-Sensor ändert oder der Anwender eine
    Einstellung anpasst. Der Coordinator liest bei jedem seiner (deutlich
    kürzeren) Poll-Zyklen nur noch das zwischengespeicherte Ergebnis, damit
    SOC-abhängige Abbrüche trotzdem ohne 60-Sekunden-Verzögerung greifen.
    """

    def __init__(self, hass: HomeAssistant, coordinator: SaxPowerCoordinator) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.plan: PricePlan = EMPTY_PLAN
        self._unsub: list[Any] = []

    # -- Konfiguration aus dem Options Flow --------------------------------
    @property
    def price_entity_id(self) -> str | None:
        return self.coordinator.options.get(CONF_PRICE_SENSOR) or None

    @property
    def pv_forecast_entity_id(self) -> str | None:
        return self.coordinator.options.get(CONF_PV_FORECAST_SENSOR) or None

    @property
    def price_attribute(self) -> str | None:
        return self.coordinator.options.get(CONF_PRICE_ATTRIBUTE) or None

    @property
    def price_unit(self) -> str:
        return self.coordinator.options.get(CONF_PRICE_UNIT) or DEFAULT_PRICE_UNIT

    @property
    def pv_factor(self) -> float:
        percent = self.coordinator.options.get(
            CONF_PV_FORECAST_FACTOR, DEFAULT_PV_FORECAST_FACTOR
        )
        try:
            return max(0.0, min(100.0, float(percent))) / 100
        except TypeError, ValueError:
            return DEFAULT_PV_FORECAST_FACTOR / 100

    # -- Lebenszyklus -------------------------------------------------------
    @callback
    def async_setup(self) -> None:
        """Timer und Zustandsbeobachter registrieren (idempotent)."""
        self.async_shutdown()
        self._unsub.append(
            async_track_time_interval(
                self.hass,
                self._async_interval_evaluate,
                timedelta(seconds=PRICE_EVAL_INTERVAL),
                name="sax_power_price_plan",
            )
        )
        tracked = [
            entity_id
            for entity_id in (self.price_entity_id, self.pv_forecast_entity_id)
            if entity_id
        ]
        if tracked:
            self._unsub.append(
                async_track_state_change_event(
                    self.hass, tracked, self._async_source_changed
                )
            )
        self.evaluate()

    @callback
    def async_shutdown(self) -> None:
        while self._unsub:
            self._unsub.pop()()

    async def _async_interval_evaluate(self, _now: datetime) -> None:
        """Periodische Prüfung der Ladebedingungen (PRICE_EVAL_INTERVAL).

        Rechnet den Plan neu und lässt den Coordinator das Ergebnis sofort
        auf das Gerät anwenden, statt bis zu einem Poll-Zyklus zu warten.
        """
        self.evaluate()
        await self.coordinator.async_apply_price_plan()

    @callback
    def _async_source_changed(self, _event: Event[EventStateChangedData]) -> None:
        self.evaluate()

    # -- Auswertung ---------------------------------------------------------
    def _forecast_kwh(self) -> float | None:
        """Erwarteter PV-Ertrag laut Prognose-Sensor, in kWh.

        Erwartet wird ein Sensor, dessen Zustand die noch zu erwartende
        Erzeugung als Energie liefert - typischerweise
        `sensor.energy_production_tomorrow` (Forecast.Solar) oder das
        Solcast-Pendant. Wh werden anhand der Einheit auf kWh umgerechnet.
        """
        entity_id = self.pv_forecast_entity_id
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, ""):
            return None
        try:
            value = float(state.state)
        except TypeError, ValueError:
            return None
        if not math.isfinite(value):
            return None
        unit = str(state.attributes.get("unit_of_measurement") or "").lower()
        if unit == "wh":
            value /= 1000
        elif unit == "mwh":
            value *= 1000
        return value

    def _context(self) -> PriceChargeContext:
        coordinator = self.coordinator
        data = coordinator.data or {}
        capacity_wh = data.get("battery_capacity")
        return PriceChargeContext(
            enabled=coordinator.price_charge_enabled,
            strategy=coordinator.price_charge_strategy,
            max_price=coordinator.price_charge_max_price,
            hours=coordinator.price_charge_hours,
            target_soc=(
                coordinator.max_soc if coordinator.max_soc is not None else MAX_SOC
            ),
            current_soc=data.get("soc"),
            capacity_kwh=None if not capacity_wh else float(capacity_wh) / 1000,
            # Seit dem Wegfall der Software-Einstellung "Max.
            # Netzladeleistung" (siehe anforderung.yaml,
            # REQ-TIMED-SOC-CHARGE) lädt die Integration immer mit
            # maximal möglicher Leistung - "ic_max_power_reference"
            # (Register 40053, "Referenzwert Maximalleistung") ist der vom
            # Gerät selbst gemeldete Bezugspunkt dafür und damit die
            # realistischere Grundlage für die Bedarfsrechnung als der
            # frühere, in der Praxis wirkungslose Nutzerwert.
            charge_power_w=data.get("ic_max_power_reference"),
            pv_forecast_kwh=self._forecast_kwh(),
            pv_factor=self.pv_factor,
        )

    @callback
    def evaluate(self) -> PricePlan:
        """Ladeplan neu berechnen und zwischenspeichern."""
        entity_id = self.price_entity_id
        now = dt_util.now()
        slots: list[PriceSlot] = []
        if entity_id:
            slots = parse_price_slots(
                self.hass.states.get(entity_id),
                attribute=self.price_attribute,
                unit=self.price_unit,
                now=now,
            )
            if not slots:
                _LOGGER.debug(
                    "Preisoptimiertes Laden: keine auswertbaren Preisdaten in %s",
                    entity_id,
                )
        self.plan = self._evaluate_price_charge(now, slots, entity_id)
        return self.plan

    def _evaluate_price_charge(
        self, now: datetime, slots: Sequence[PriceSlot], entity_id: str | None
    ) -> PricePlan:
        ctx = self._context()
        # Der aktuelle Preis ist eine reine Info-Anzeige (price_charge_-
        # current_price-Sensor) und wird deshalb schon vor den Enabled-/
        # Strategie-Prüfungen ermittelt - sonst zeigt der Sensor "unbekannt",
        # obwohl der Preis-Sensor korrekt konfiguriert ist, nur weil die
        # Lade-Automatik (noch) ausgeschaltet ist.
        price_now = current_price(slots, now)
        if not ctx.enabled or ctx.strategy == PRICE_STRATEGY_OFF:
            return PricePlan(status=PRICE_STATUS_OFF, current_price=price_now)
        if not entity_id:
            # Feature eingeschaltet, aber im Options Flow ist (noch) kein
            # Preis-Sensor hinterlegt - ohne Preise gibt es nichts zu planen.
            return PricePlan(status=PRICE_STATUS_NO_PRICE_DATA, current_price=price_now)
        return compute_plan(now, slots, ctx)

    @property
    def plan_attributes(self) -> dict[str, Any]:
        """Zusatzattribute für den Status-Sensor (Nachvollziehbarkeit)."""
        plan = self.plan
        return {
            "strategie": self.coordinator.price_charge_strategy,
            "aktueller_preis": (
                None if plan.current_price is None else round(plan.current_price, 5)
            ),
            "preisgrenze": (
                None if plan.threshold is None else round(plan.threshold, 5)
            ),
            "neutralpreis": (
                None
                if self.coordinator.price_charge_neutral_price is None
                else round(self.coordinator.price_charge_neutral_price, 5)
            ),
            "benoetigte_stunden": plan.needed_hours,
            "pv_prognose_kwh": (
                None if plan.pv_forecast_kwh is None else round(plan.pv_forecast_kwh, 2)
            ),
            "preis_sensor": self.price_entity_id,
            "pv_prognose_sensor": self.pv_forecast_entity_id,
            "geplante_fenster": [slot.as_dict() for slot in plan.slots],
        }
