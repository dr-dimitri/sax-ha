"""Home Assistant repair-issue adapter for integration self diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time as dt_time

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from ..const import (
    DOMAIN,
    ISSUE_ECONOMICS_PRICE_UNAVAILABLE,
    ISSUE_EMPTY_CHARGE_WINDOW,
    ISSUE_MAX_SOC_BELOW_MIN_SOC,
    ISSUE_NO_ACTIVE_MONTHS,
    ISSUE_PRICE_NEUTRAL_BELOW_LIMIT,
    ISSUE_PRICE_SENSOR_MISSING,
    ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE,
    PRICE_SENSOR_MISSING_GRACE_PERIOD,
    PRICE_STATUS_NO_PRICE_DATA,
    SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD,
)


@dataclass(frozen=True, slots=True)
class DiagnosticSnapshot:
    """Current settings and runtime state needed by all diagnostic rules."""

    price_status: str
    price_entity_id: str | None
    extended_available: bool
    extended_unavailable_since: float | None
    slave_id_extended: int
    max_soc: int | None
    timed_min_soc: int | None
    price_limit: float | None
    neutral_price: float | None
    timed_enabled: bool
    timed_start: dt_time | None
    timed_end: dt_time | None
    timed_months: frozenset[int]
    grid_serving_enabled: bool
    grid_serving_start: dt_time | None
    grid_serving_end: dt_time | None
    grid_serving_months: frozenset[int]
    # REQ-ECONOMICS-OBSERVABILITY: economics_price_unavailable ist bereits
    # vom Coordinator fertig ausgewertet (Karenzzeit bzw. sofortiger
    # Konfigurationsfehler bei Fest-/Zeitfenstertarif, siehe
    # SaxPowerCoordinator._update_economics_price_availability) - hier nur
    # noch die Zustandsflanke für Issue-Erzeugung/-Löschung.
    economics_tariff_enabled: bool = False
    economics_price_unavailable: bool = False


class SelfDiagnostics:
    """Create and clear repair issues on diagnostic state transitions."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._entry_id = entry_id
        self._price_sensor_missing_since: float | None = None
        self._price_sensor_issue_active = False
        self._sunspec_persistent_issue_active = False
        self._max_soc_below_min_soc_issue_active = False
        self._price_neutral_below_limit_issue_active = False
        self._empty_window_issue_active: dict[str, bool] = {}
        self._no_active_months_issue_active: dict[str, bool] = {}
        self._economics_price_unavailable_issue_active = False

    def check(self, snapshot: DiagnosticSnapshot, now: float) -> None:
        """Evaluate every self-diagnostic rule for one coordinator update."""
        self._check_price_sensor_missing(snapshot, now)
        self._check_sunspec_persistently_unavailable(snapshot, now)
        self._check_max_soc_below_min_soc(snapshot)
        self._check_price_neutral_below_limit(snapshot)
        self._check_economics_price_unavailable(snapshot)
        self._check_empty_charge_window(
            "timed_charge",
            snapshot.timed_enabled,
            snapshot.timed_start,
            snapshot.timed_end,
            "Netzladung (zeitgesteuertes Laden)",
        )
        self._check_empty_charge_window(
            "grid_serving",
            snapshot.grid_serving_enabled,
            snapshot.grid_serving_start,
            snapshot.grid_serving_end,
            "Netzdienliches Laden",
        )
        self._check_no_active_months(
            "timed_charge",
            snapshot.timed_enabled,
            snapshot.timed_months,
            "Netzladung (zeitgesteuertes Laden)",
        )
        self._check_no_active_months(
            "grid_serving",
            snapshot.grid_serving_enabled,
            snapshot.grid_serving_months,
            "Netzdienliches Laden",
        )

    def _check_price_sensor_missing(
        self, snapshot: DiagnosticSnapshot, now: float
    ) -> None:
        issue_id = f"{ISSUE_PRICE_SENSOR_MISSING}_{self._entry_id}"
        if snapshot.price_status != PRICE_STATUS_NO_PRICE_DATA:
            self._price_sensor_missing_since = None
            if self._price_sensor_issue_active:
                ir.async_delete_issue(self._hass, DOMAIN, issue_id)
                self._price_sensor_issue_active = False
            return

        if self._price_sensor_missing_since is None:
            self._price_sensor_missing_since = now
        if (
            not self._price_sensor_issue_active
            and now - self._price_sensor_missing_since
            >= PRICE_SENSOR_MISSING_GRACE_PERIOD
        ):
            ir.async_create_issue(
                self._hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_PRICE_SENSOR_MISSING,
                translation_placeholders={
                    "price_sensor": snapshot.price_entity_id or "?"
                },
            )
            self._price_sensor_issue_active = True

    def _check_sunspec_persistently_unavailable(
        self, snapshot: DiagnosticSnapshot, now: float
    ) -> None:
        issue_id = f"{ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE}_{self._entry_id}"
        if snapshot.extended_available or snapshot.extended_unavailable_since is None:
            if self._sunspec_persistent_issue_active:
                ir.async_delete_issue(self._hass, DOMAIN, issue_id)
                self._sunspec_persistent_issue_active = False
            return

        if (
            not self._sunspec_persistent_issue_active
            and now - snapshot.extended_unavailable_since
            >= SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD
        ):
            ir.async_create_issue(
                self._hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE,
                translation_placeholders={"slave_id": str(snapshot.slave_id_extended)},
            )
            self._sunspec_persistent_issue_active = True

    def _check_max_soc_below_min_soc(self, snapshot: DiagnosticSnapshot) -> None:
        issue_id = f"{ISSUE_MAX_SOC_BELOW_MIN_SOC}_{self._entry_id}"
        problem = (
            snapshot.max_soc is not None
            and snapshot.timed_min_soc is not None
            and snapshot.max_soc < snapshot.timed_min_soc
        )
        if not problem:
            if self._max_soc_below_min_soc_issue_active:
                ir.async_delete_issue(self._hass, DOMAIN, issue_id)
                self._max_soc_below_min_soc_issue_active = False
            return
        if self._max_soc_below_min_soc_issue_active:
            return
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_MAX_SOC_BELOW_MIN_SOC,
            translation_placeholders={
                "max_soc": str(snapshot.max_soc),
                "min_soc": str(snapshot.timed_min_soc),
            },
        )
        self._max_soc_below_min_soc_issue_active = True

    def _check_price_neutral_below_limit(self, snapshot: DiagnosticSnapshot) -> None:
        issue_id = f"{ISSUE_PRICE_NEUTRAL_BELOW_LIMIT}_{self._entry_id}"
        problem = (
            snapshot.price_limit is not None
            and snapshot.neutral_price is not None
            and snapshot.neutral_price <= snapshot.price_limit
        )
        if not problem:
            if self._price_neutral_below_limit_issue_active:
                ir.async_delete_issue(self._hass, DOMAIN, issue_id)
                self._price_neutral_below_limit_issue_active = False
            return
        if self._price_neutral_below_limit_issue_active:
            return
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_PRICE_NEUTRAL_BELOW_LIMIT,
            translation_placeholders={
                "max_price": str(snapshot.price_limit),
                "neutral_price": str(snapshot.neutral_price),
            },
        )
        self._price_neutral_below_limit_issue_active = True

    def _check_economics_price_unavailable(self, snapshot: DiagnosticSnapshot) -> None:
        """REQ-ECONOMICS-OBSERVABILITY: rein informativ, ohne eigene
        Karenzzeit - die steckt bereits in
        snapshot.economics_price_unavailable (Coordinator).

        Die Löschung prüft zusätzlich zum lokalen
        `_economics_price_unavailable_issue_active`-Flag den tatsächlichen
        Issue-Registry-Zustand: Das Flag lebt nur im Arbeitsspeicher dieser
        SelfDiagnostics-Instanz und startet nach jedem Neuladen des Config
        Entry wieder bei `False` - ein zuvor angelegtes, in der Registry
        aber weiterhin vorhandenes Issue würde sonst nie gelöscht, selbst
        wenn der Preis inzwischen wieder gültig ist. Für das Anlegen genügt
        weiterhin das Flag: ein doppelter Aufruf von `async_create_issue`
        für dieselbe issue_id ist ohnehin idempotent, das Flag vermeidet
        ihn nur zusätzlich.
        """
        issue_id = f"{ISSUE_ECONOMICS_PRICE_UNAVAILABLE}_{self._entry_id}"
        problem = (
            snapshot.economics_tariff_enabled and snapshot.economics_price_unavailable
        )
        if not problem:
            if self._economics_price_unavailable_issue_active or (
                ir.async_get(self._hass).async_get_issue(DOMAIN, issue_id) is not None
            ):
                ir.async_delete_issue(self._hass, DOMAIN, issue_id)
            self._economics_price_unavailable_issue_active = False
            return
        if self._economics_price_unavailable_issue_active:
            return
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_ECONOMICS_PRICE_UNAVAILABLE,
        )
        self._economics_price_unavailable_issue_active = True

    def _check_empty_charge_window(
        self,
        feature_key: str,
        enabled: bool,
        start: dt_time | None,
        end: dt_time | None,
        feature_label: str,
    ) -> None:
        issue_id = f"{ISSUE_EMPTY_CHARGE_WINDOW}_{feature_key}_{self._entry_id}"
        problem = enabled and start is not None and end is not None and start == end
        active = self._empty_window_issue_active.get(feature_key, False)
        if not problem:
            if active:
                ir.async_delete_issue(self._hass, DOMAIN, issue_id)
                self._empty_window_issue_active[feature_key] = False
            return
        if active:
            return
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_EMPTY_CHARGE_WINDOW,
            translation_placeholders={"feature": feature_label},
        )
        self._empty_window_issue_active[feature_key] = True

    def _check_no_active_months(
        self,
        feature_key: str,
        enabled: bool,
        months: frozenset[int],
        feature_label: str,
    ) -> None:
        issue_id = f"{ISSUE_NO_ACTIVE_MONTHS}_{feature_key}_{self._entry_id}"
        problem = enabled and not months
        active = self._no_active_months_issue_active.get(feature_key, False)
        if not problem:
            if active:
                ir.async_delete_issue(self._hass, DOMAIN, issue_id)
                self._no_active_months_issue_active[feature_key] = False
            return
        if active:
            return
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_NO_ACTIVE_MONTHS,
            translation_placeholders={"feature": feature_label},
        )
        self._no_active_months_issue_active[feature_key] = True
