"""Versioned persistence for the software-side charge control settings.

Siehe anforderung.yaml, REQ-CONTROL-CONFIG-BOOTSTRAP: Der Coordinator lädt
diesen Snapshot vollständig, BEVOR der erste Refresh Gerätebefehle ausführen
darf. Die sichtbaren Entity-States (RestoreEntity) dienen nur noch als
einmaliger Migrationspfad, solange es für einen Config Entry noch keinen
Store gibt.
"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass, replace
from datetime import time as dt_time
from enum import StrEnum
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from ..const import (
    ALL_MONTHS,
    DEFAULT_GRID_SERVING_ENABLED,
    DEFAULT_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    DEFAULT_PRICE_CHARGE_ENABLED,
    DEFAULT_PRICE_HOURS,
    DEFAULT_PRICE_LIMIT,
    DEFAULT_PRICE_NEUTRAL,
    DEFAULT_PRICE_STRATEGY,
    DEFAULT_TIMED_CHARGE_ENABLED,
    DEFAULT_TIMED_CHARGE_MIN_SOC,
    DOMAIN,
    MAX_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    MAX_PRICE_HOURS,
    MAX_PRICE_LIMIT,
    MAX_SOC,
    MIN_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    MIN_PRICE_HOURS,
    MIN_PRICE_LIMIT,
    MIN_SOC,
    PRICE_STRATEGIES,
)
from ..domain.scheduling import windows_overlap

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.control"
# Einstellungsänderungen kommen im Gegensatz zu den Energiezählern selten und
# in Schüben (Schieberegler, Restore mehrerer Monats-Switches). Ein kurzes
# Sammelfenster reicht, damit ein Neustart direkt nach einer Änderung den
# neuen Wert schon sieht.
CONTROL_SAVE_DELAY = 10

_TIME_FIELDS = (
    "timed_charge_start",
    "timed_charge_end",
    "grid_serving_start",
    "grid_serving_end",
)
_MONTH_FIELDS = ("timed_charge_months", "grid_serving_months")


class ControlConfigLoadStatus(StrEnum):
    """Woher die aktuell gültige Ladekonfiguration stammt.

    Die drei Fälle müssen auseinandergehalten werden, weil sich nur einer
    von ihnen migrieren lässt (REQ-CONTROL-CONFIG-BOOTSTRAP):

    - LOADED: Es gibt einen lesbaren Store; er ist die alleinige Quelle.
    - MISSING: Es gibt noch keinen Store - und NUR dann darf der einmalige
      RestoreEntity-Migrationspfad der Plattformen greifen.
    - FAILED: Es gibt einen Store, er ist aber nicht verwertbar (I/O-Fehler,
      kein Objekt, unbekannte künftige Version). Dann gelten sichere
      Defaults, ein veralteter Entity-Zustand darf NICHT einspringen, und
      der vorhandene Store wird nicht automatisch überschrieben.
    """

    LOADED = "loaded"
    MISSING = "missing"
    FAILED = "failed"


@dataclass(frozen=True)
class ControlConfigLoadResult:
    """Ergebnis eines Ladeversuchs; `config` ist nur bei LOADED gesetzt."""

    status: ControlConfigLoadStatus
    config: ControlConfig | None = None


@dataclass(frozen=True)
class ControlConfig:
    """Alle softwareseitigen Steuerwerte eines Config Entry.

    `None` bedeutet durchgehend "nicht gespeichert" - für die vier
    Zeitfelder ist es zusätzlich ein gültiger Endzustand (ein wegen
    Überschneidung geleertes Zeitfenster, siehe
    SaxPowerCoordinator._notify_time_window_overlap). Deshalb unterscheidet
    erst `ControlConfig.sanitized()` beim Laden zwischen beidem: fehlende
    Nicht-Zeit-Felder bekommen den Hard-Default, ein geleertes Zeitfenster
    bleibt leer.
    """

    max_soc: int | None = None
    timed_charge_enabled: bool | None = None
    timed_charge_start: dt_time | None = None
    timed_charge_end: dt_time | None = None
    timed_charge_months: frozenset[int] | None = None
    timed_charge_min_soc: int | None = None
    grid_serving_enabled: bool | None = None
    grid_serving_start: dt_time | None = None
    grid_serving_end: dt_time | None = None
    grid_serving_months: frozenset[int] | None = None
    grid_serving_forecast_threshold_kwh: float | None = None
    price_charge_enabled: bool | None = None
    price_charge_strategy: str | None = None
    price_charge_max_price: float | None = None
    price_charge_neutral_price: float | None = None
    price_charge_hours: int | None = None

    def sanitized(self) -> ControlConfig:
        """Füllt fehlende Felder auf und erzwingt die fachlichen Invarianten.

        Die Feldvalidierung beim Laden prüft jeden Wert nur für sich. Ein
        korrupter oder von Hand bearbeiteter Store kann aber auch aus lauter
        einzeln gültigen Werten bestehen und trotzdem eine Kombination
        enthalten, die kein Setter je erzeugt hätte - deshalb werden hier
        zusätzlich die Invarianten geprüft, die sonst nur die Setter
        garantieren (REQ-CONTROL-CONFIG-BOOTSTRAP).

        Fehlende Felder (Store von vor der Einführung eines Feldes, oder von
        der Feldvalidierung verworfen) bekommen ihren Hard-Default -
        fail-safe: lieber der dokumentierte Default als ein aus einem
        korrupten Wert abgeleiteter Zustand.
        """
        defaults: dict[str, Any] = {
            "max_soc": MAX_SOC,
            "timed_charge_enabled": DEFAULT_TIMED_CHARGE_ENABLED,
            "timed_charge_months": ALL_MONTHS,
            "timed_charge_min_soc": DEFAULT_TIMED_CHARGE_MIN_SOC,
            "grid_serving_enabled": DEFAULT_GRID_SERVING_ENABLED,
            "grid_serving_months": ALL_MONTHS,
            "grid_serving_forecast_threshold_kwh": (
                DEFAULT_GRID_SERVING_FORECAST_THRESHOLD_KWH
            ),
            "price_charge_enabled": DEFAULT_PRICE_CHARGE_ENABLED,
            "price_charge_strategy": DEFAULT_PRICE_STRATEGY,
            "price_charge_max_price": DEFAULT_PRICE_LIMIT,
            "price_charge_neutral_price": DEFAULT_PRICE_NEUTRAL,
            "price_charge_hours": DEFAULT_PRICE_HOURS,
        }
        filled = {
            field: default
            for field, default in defaults.items()
            if getattr(self, field) is None
        }
        config = replace(self, **filled) if filled else self
        if config.timed_charge_enabled and config.price_charge_enabled:
            # Netzladung und preisoptimiertes Laden laden beide aktiv über
            # denselben SunSpec-Schreibpfad und schließen sich gegenseitig
            # aus (siehe SaxPowerCoordinator.async_set_timed_charge_enabled).
            # Ein Store, in dem beide aktiv sind, kann nur beschädigt sein.
            _LOGGER.warning(
                "Gespeicherte Konfiguration hatte Netzladung und "
                "preisoptimiertes Laden gleichzeitig aktiv; "
                "preisoptimiertes Laden bleibt aus"
            )
            config = replace(config, price_charge_enabled=False)
        return config._without_overlapping_windows()

    def _without_overlapping_windows(self) -> ControlConfig:
        """Erzwingt die Nicht-Überschneidung der beiden Zeitfenster.

        Netzladung und netzdienliches Laden dürfen sich weder in ihrer
        Tageszeit noch in ihren aktiven Monaten überschneiden; die
        Zeit-/Monats-Setter lehnen so eine Kombination ab (siehe
        SaxPowerCoordinator._assert_windows_dont_overlap). Steht sie
        trotzdem im Store, wird das Netzladefenster geleert und nicht das
        des netzdienlichen Ladens: Netzladung zieht aktiv Strom aus dem
        Netz, netzdienliches Laden unterbricht nur eine PV-Ladung - ohne
        Fenster kann die Netzladung gar nicht erst anspringen.
        """
        timed_months = self.timed_charge_months or frozenset()
        grid_serving_months = self.grid_serving_months or frozenset()
        if not (timed_months & grid_serving_months):
            return self
        if not windows_overlap(
            self.timed_charge_start,
            self.timed_charge_end,
            self.grid_serving_start,
            self.grid_serving_end,
        ):
            return self
        _LOGGER.warning(
            "Gespeicherte Zeitfenster von Netzladung (%s-%s) und "
            "netzdienlichem Laden (%s-%s) überschneiden sich; das "
            "Netzladefenster wird geleert",
            self.timed_charge_start,
            self.timed_charge_end,
            self.grid_serving_start,
            self.grid_serving_end,
        )
        return replace(self, timed_charge_start=None, timed_charge_end=None)


class ControlConfigStore:
    """Persist one charge control snapshot per config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry_id}",
        )
        self._last_persisted: dict[str, Any] | None = None
        self._pending: dict[str, Any] | None = None
        self._save_scheduled = False

    async def async_load(self) -> ControlConfigLoadResult:
        """Load the snapshot, dropping each invalid field independently.

        MISSING gibt es ausschließlich, wenn für diesen Config Entry noch
        gar kein Store existiert - nur dann darf der einmalige
        RestoreEntity-Migrationspfad greifen. Ein vorhandener, aber gar
        nicht verwertbarer Store (I/O-Fehler, kein Objekt, unbekannte
        künftige Version) meldet FAILED: dann gelten sichere Defaults, und
        der Aufrufer überschreibt ihn nicht automatisch. Ein einzelner
        korrupter Wert innerhalb eines lesbaren Stores verwirft dagegen nur
        sich selbst und lässt den Rest der Konfiguration stehen.
        """
        try:
            raw = await self._store.async_load()
        except (HomeAssistantError, NotImplementedError, OSError, ValueError) as err:
            # NotImplementedError: Home Assistant meldet damit einen Store
            # mit einer Hauptversion, für die es hier keine Migration gibt -
            # typischerweise ein Downgrade. Der darf niemals von Version
            # STORAGE_VERSION überschrieben werden.
            _LOGGER.error(
                "Gespeicherte Ladekonfiguration konnte nicht gelesen werden; "
                "es gelten die Vorgabewerte und der vorhandene Store bleibt "
                "unangetastet: %s",
                err,
            )
            return ControlConfigLoadResult(ControlConfigLoadStatus.FAILED)
        if raw is None:
            return ControlConfigLoadResult(ControlConfigLoadStatus.MISSING)
        if not isinstance(raw, dict):
            _LOGGER.error(
                "Gespeicherte Ladekonfiguration ist kein Objekt; es gelten "
                "die Vorgabewerte und der vorhandene Store bleibt unangetastet"
            )
            return ControlConfigLoadResult(ControlConfigLoadStatus.FAILED)

        config = ControlConfig(
            max_soc=_valid_int(raw.get("max_soc"), MIN_SOC, MAX_SOC, "Max. SOC"),
            timed_charge_enabled=_valid_bool(
                raw.get("timed_charge_enabled"), "Netzladung aktiv"
            ),
            timed_charge_start=_valid_time(
                raw.get("timed_charge_start"), "Netzladung Start"
            ),
            timed_charge_end=_valid_time(
                raw.get("timed_charge_end"), "Netzladung Ende"
            ),
            timed_charge_months=_valid_months(
                raw.get("timed_charge_months"), "Netzladung Monate"
            ),
            timed_charge_min_soc=_valid_int(
                raw.get("timed_charge_min_soc"), MIN_SOC, MAX_SOC, "Netzladung Min. SOC"
            ),
            grid_serving_enabled=_valid_bool(
                raw.get("grid_serving_enabled"), "Netzdienliches Laden aktiv"
            ),
            grid_serving_start=_valid_time(
                raw.get("grid_serving_start"), "Netzdienliches Laden Start"
            ),
            grid_serving_end=_valid_time(
                raw.get("grid_serving_end"), "Netzdienliches Laden Ende"
            ),
            grid_serving_months=_valid_months(
                raw.get("grid_serving_months"), "Netzdienliches Laden Monate"
            ),
            grid_serving_forecast_threshold_kwh=_valid_float(
                raw.get("grid_serving_forecast_threshold_kwh"),
                MIN_GRID_SERVING_FORECAST_THRESHOLD_KWH,
                MAX_GRID_SERVING_FORECAST_THRESHOLD_KWH,
                "PV-Prognose-Mindestwert",
            ),
            price_charge_enabled=_valid_bool(
                raw.get("price_charge_enabled"), "Preisoptimiertes Laden aktiv"
            ),
            price_charge_strategy=_valid_strategy(raw.get("price_charge_strategy")),
            price_charge_max_price=_valid_float(
                raw.get("price_charge_max_price"),
                MIN_PRICE_LIMIT,
                MAX_PRICE_LIMIT,
                "Preisgrenze",
            ),
            price_charge_neutral_price=_valid_float(
                raw.get("price_charge_neutral_price"),
                MIN_PRICE_LIMIT,
                MAX_PRICE_LIMIT,
                "Neutralpreis",
            ),
            price_charge_hours=_valid_int(
                raw.get("price_charge_hours"),
                MIN_PRICE_HOURS,
                MAX_PRICE_HOURS,
                "Anzahl Stunden",
            ),
        )
        self._last_persisted = _serialize(config)
        return ControlConfigLoadResult(ControlConfigLoadStatus.LOADED, config)

    @callback
    def async_delay_save(
        self, config: ControlConfig, delay: float = CONTROL_SAVE_DELAY
    ) -> bool:
        """Coalesce a burst of setting changes into one delayed write.

        Gibt False zurück, wenn sich gegenüber dem zuletzt vorgemerkten bzw.
        geschriebenen Stand nichts geändert hat - so löst der bei JEDER
        Ladeentscheidung durchlaufene Schreibpfad
        (SaxPowerCoordinator._async_apply_grid_charge_change) keine Storage-
        Schreibvorgänge ohne Anlass aus.
        """
        payload = _serialize(config)
        if payload == (self._pending or self._last_persisted):
            return False
        self._pending = payload
        if not self._save_scheduled:
            self._save_scheduled = True
            self._store.async_delay_save(self._consume_pending, delay)
        return True

    async def async_save(self, config: ControlConfig) -> None:
        """Immediately persist a snapshot, cancelling a delayed write."""
        payload = _serialize(config)
        self._pending = None
        self._save_scheduled = False
        await self._store.async_save(payload)
        self._last_persisted = payload

    def _consume_pending(self) -> dict[str, Any]:
        payload = self._pending or self._last_persisted or {}
        self._pending = None
        self._save_scheduled = False
        self._last_persisted = payload
        return payload


def _serialize(config: ControlConfig) -> dict[str, Any]:
    payload = asdict(config)
    for field in _TIME_FIELDS:
        value = payload[field]
        payload[field] = value.isoformat() if value is not None else None
    for field in _MONTH_FIELDS:
        value = payload[field]
        payload[field] = sorted(value) if value is not None else None
    return payload


def _discard(label: str, value: Any) -> None:
    _LOGGER.warning("Ungültigen gespeicherten Wert für %s verworfen: %r", label, value)


def _valid_bool(value: Any, label: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        _discard(label, value)
        return None
    return value


def _valid_int(value: Any, minimum: int, maximum: int, label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        _discard(label, value)
        return None
    if not minimum <= value <= maximum:
        _discard(label, value)
        return None
    return value


def _valid_float(
    value: Any, minimum: float, maximum: float, label: str
) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        _discard(label, value)
        return None
    if not math.isfinite(value) or not minimum <= value <= maximum:
        _discard(label, value)
        return None
    return float(value)


def _valid_time(value: Any, label: str) -> dt_time | None:
    if value is None:
        return None
    if not isinstance(value, str) or (parsed := dt_util.parse_time(value)) is None:
        _discard(label, value)
        return None
    return parsed


def _valid_months(value: Any, label: str) -> frozenset[int] | None:
    if value is None:
        return None
    if not isinstance(value, list) or any(
        isinstance(month, bool) or not isinstance(month, int) or month not in ALL_MONTHS
        for month in value
    ):
        _discard(label, value)
        return None
    return frozenset(value)


def _valid_strategy(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value not in PRICE_STRATEGIES:
        _discard("Ladestrategie", value)
        return None
    return value
