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
    ISSUE_PRICE_UNIT_UNSUPPORTED,
    ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE,
    PRICE_SENSOR_MISSING_GRACE_PERIOD,
    PRICE_STATUS_NO_PRICE_DATA,
    PRICE_STRATEGY_ABSOLUTE,
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
    timed_max_soc: int | None
    timed_min_soc: int | None
    price_limit: float | None
    neutral_price: float | None
    price_strategy: str
    timed_enabled: bool
    timed_start: dt_time | None
    timed_end: dt_time | None
    timed_months: frozenset[int]
    grid_serving_enabled: bool
    grid_serving_start: dt_time | None
    grid_serving_end: dt_time | None
    grid_serving_months: frozenset[int]
    unsupported_price_unit: bool = False
    timed_uses_tariff: bool = False
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
        self._active_issue_ids: set[str] = set()

    def check(self, snapshot: DiagnosticSnapshot, now: float) -> None:
        """Evaluate every self-diagnostic rule for one coordinator update."""
        self._sync_issue(
            f"{ISSUE_PRICE_UNIT_UNSUPPORTED}_{self._entry_id}",
            snapshot.unsupported_price_unit
            and snapshot.price_status == PRICE_STATUS_NO_PRICE_DATA,
            ISSUE_PRICE_UNIT_UNSUPPORTED,
            {"price_sensor": snapshot.price_entity_id or "?"},
        )
        self._check_price_sensor_missing(snapshot, now)
        self._check_sunspec_persistently_unavailable(snapshot, now)
        self._check_max_soc_below_min_soc(snapshot)
        self._check_price_neutral_below_limit(snapshot)
        self._check_economics_price_unavailable(snapshot)
        self._check_empty_charge_window(
            "timed_charge",
            snapshot.timed_enabled and not snapshot.timed_uses_tariff,
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

    def _sync_issue(
        self,
        issue_id: str,
        problem: bool,
        translation_key: str,
        translation_placeholders: dict[str, str] | None = None,
    ) -> None:
        """REQ-SELF-DIAGNOSIS-REPAIRS: Registry-Issues überleben einen Reload."""
        if not problem:
            if issue_id in self._active_issue_ids or (
                ir.async_get(self._hass).async_get_issue(DOMAIN, issue_id) is not None
            ):
                ir.async_delete_issue(self._hass, DOMAIN, issue_id)
            self._active_issue_ids.discard(issue_id)
            return
        if issue_id in self._active_issue_ids:
            return
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=translation_key,
            translation_placeholders=translation_placeholders,
        )
        self._active_issue_ids.add(issue_id)

    def _check_price_sensor_missing(
        self, snapshot: DiagnosticSnapshot, now: float
    ) -> None:
        problem = (
            snapshot.price_status == PRICE_STATUS_NO_PRICE_DATA
            and not snapshot.unsupported_price_unit
        )
        if problem:
            if self._price_sensor_missing_since is None:
                self._price_sensor_missing_since = now
            if (
                now - self._price_sensor_missing_since
                < PRICE_SENSOR_MISSING_GRACE_PERIOD
            ):
                return
        else:
            self._price_sensor_missing_since = None
        self._sync_issue(
            f"{ISSUE_PRICE_SENSOR_MISSING}_{self._entry_id}",
            problem,
            ISSUE_PRICE_SENSOR_MISSING,
            {"price_sensor": snapshot.price_entity_id or "?"},
        )

    def _check_sunspec_persistently_unavailable(
        self, snapshot: DiagnosticSnapshot, now: float
    ) -> None:
        problem = (
            not snapshot.extended_available
            and snapshot.extended_unavailable_since is not None
        )
        if (
            problem
            and snapshot.extended_unavailable_since is not None
            and now - snapshot.extended_unavailable_since
            < SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD
        ):
            return
        self._sync_issue(
            f"{ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE}_{self._entry_id}",
            problem,
            ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE,
            {"slave_id": str(snapshot.slave_id_extended)},
        )

    def _check_max_soc_below_min_soc(self, snapshot: DiagnosticSnapshot) -> None:
        problem = (
            snapshot.timed_enabled
            and snapshot.timed_max_soc is not None
            and snapshot.timed_min_soc is not None
            and snapshot.timed_max_soc < snapshot.timed_min_soc
        )
        self._sync_issue(
            f"{ISSUE_MAX_SOC_BELOW_MIN_SOC}_{self._entry_id}",
            problem,
            ISSUE_MAX_SOC_BELOW_MIN_SOC,
            {
                "max_soc": str(snapshot.timed_max_soc),
                "min_soc": str(snapshot.timed_min_soc),
            },
        )

    def _check_price_neutral_below_limit(self, snapshot: DiagnosticSnapshot) -> None:
        problem = (
            snapshot.price_strategy == PRICE_STRATEGY_ABSOLUTE
            and snapshot.price_limit is not None
            and snapshot.neutral_price is not None
            and snapshot.neutral_price <= snapshot.price_limit
        )
        self._sync_issue(
            f"{ISSUE_PRICE_NEUTRAL_BELOW_LIMIT}_{self._entry_id}",
            problem,
            ISSUE_PRICE_NEUTRAL_BELOW_LIMIT,
            {
                "max_price": (
                    f"{snapshot.price_limit * 100:.2f}"
                    if snapshot.price_limit is not None
                    else ""
                ),
                "neutral_price": (
                    f"{snapshot.neutral_price * 100:.2f}"
                    if snapshot.neutral_price is not None
                    else ""
                ),
            },
        )

    def _check_economics_price_unavailable(self, snapshot: DiagnosticSnapshot) -> None:
        """REQ-ECONOMICS-OBSERVABILITY: Die Karenzzeit liegt im Coordinator."""
        problem = (
            snapshot.economics_tariff_enabled and snapshot.economics_price_unavailable
        )
        self._sync_issue(
            f"{ISSUE_ECONOMICS_PRICE_UNAVAILABLE}_{self._entry_id}",
            problem,
            ISSUE_ECONOMICS_PRICE_UNAVAILABLE,
        )

    def _check_empty_charge_window(
        self,
        feature_key: str,
        enabled: bool,
        start: dt_time | None,
        end: dt_time | None,
        feature_label: str,
    ) -> None:
        problem = enabled and (start is None or end is None or start == end)
        self._sync_issue(
            f"{ISSUE_EMPTY_CHARGE_WINDOW}_{feature_key}_{self._entry_id}",
            problem,
            ISSUE_EMPTY_CHARGE_WINDOW,
            {"feature": feature_label},
        )

    def _check_no_active_months(
        self,
        feature_key: str,
        enabled: bool,
        months: frozenset[int],
        feature_label: str,
    ) -> None:
        problem = enabled and not months
        self._sync_issue(
            f"{ISSUE_NO_ACTIVE_MONTHS}_{feature_key}_{self._entry_id}",
            problem,
            ISSUE_NO_ACTIVE_MONTHS,
            {"feature": feature_label},
        )
