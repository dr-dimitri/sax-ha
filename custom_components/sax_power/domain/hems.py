"""Immutable boundary contracts for REQ-HEMS-ENERGY-PLANNER."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class EnergySlot:
    """AC energy within a half-open, timezone-aware interval."""

    start: datetime
    end: datetime
    energy_kwh: float
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LoadForecast:
    """Night battery-discharge proxy; missing observations are never zero."""

    intervals: tuple[EnergySlot, ...] = ()
    generated_at: datetime | None = None
    evaluated_through: datetime | None = None
    quality_reason: str | None = None
    nights_count: int = 0
    observed_hours: float = 0.0
    coverage: float = 0.0
    model_start: datetime | None = None
    model_end: datetime | None = None
    basis: str = "battery_discharge_night"
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PvForecast:
    """Provider-normalized AC production and explicit freshness evidence."""

    intervals: tuple[EnergySlot, ...] = ()
    generated_at: datetime | None = None
    fetched_at: datetime | None = None
    valid_until: datetime | None = None
    source_id: str = ""
    provider: str = ""
    requested_start: datetime | None = None
    requested_end: datetime | None = None
    quality_reason: str | None = None
    quality_flags: tuple[str, ...] = ()
    update_success: bool | None = None
    max_age_seconds: float | None = None
    freshness_policy: str = ""
    coverage_start: datetime | None = None
    coverage_end: datetime | None = None
    coverage_complete: bool = False
    timezone: str = ""
    origin: str = "unknown"


@dataclass(frozen=True, slots=True)
class TariffWindow:
    """A real UTC price/permission interval; prices are already normalized."""

    start: datetime
    end: datetime
    price_eur_kwh: float | None = None


@dataclass(frozen=True, slots=True)
class TariffConstraints:
    """Adapter-owned permissions; the planner never reopens a spent budget.

    ``cheap_windows`` retain physical price-window boundaries across budget
    cycles. ``charge_windows`` are the actually executable subset.
    """

    charge_windows: tuple[TariffWindow, ...] = ()
    cheap_windows: tuple[TariffWindow, ...] = ()
    discharge_blocked_windows: tuple[TariffWindow, ...] = ()
    max_charge_seconds: float | None = None
    hold_after_charge: bool = False
    quality_reason: str | None = None


@dataclass(frozen=True, slots=True)
class PlanningSnapshot:
    """One coherent revision, without Home Assistant or hardware objects."""

    as_of: datetime
    revision: str
    load: LoadForecast
    pv: PvForecast
    tariff: TariffConstraints
    current_soc: float | None
    soc_measured_at: datetime | None
    capacity_kwh: float | None
    charge_power_w: float | None
    reserve_soc: float
    max_soc: float
    eta_charge: float = 0.95
    eta_discharge: float = 0.95
    physical_min_soc: float = 0.0
    discharge_power_w: float | None = None
    device_available: bool = True
    max_soc_age_seconds: float = 30.0


class PlanStatus(StrEnum):
    """Data fallback is distinct from missing device safety prerequisites."""

    INACTIVE = "inactive"
    FALLBACK = "fallback"
    BLOCKED = "blocked"
    NO_NEED = "no_need"
    PLANNED = "planned"
    LIMITED = "limited"


@dataclass(frozen=True, slots=True)
class ChargeInterval:
    """Executable maximum-power interval with an AC energy ceiling."""

    start: datetime
    end: datetime
    energy_kwh: float
    price_eur_kwh: float | None = None


@dataclass(frozen=True, slots=True)
class EnergyPoint:
    """Expected stored DC-equivalent energy at a chronological boundary."""

    at: datetime
    stored_kwh: float


@dataclass(frozen=True, slots=True)
class EnergyPlan:
    """Planning outcome; actual device acknowledgement belongs to runtime."""

    decision_id: str
    revision: str
    evaluated_at: datetime
    valid_until: datetime
    status: PlanStatus
    reason_codes: tuple[str, ...]
    intervals: tuple[ChargeInterval, ...] = ()
    pv_supply_at: datetime | None = None
    required_grid_kwh: float | None = None
    planned_grid_kwh: float | None = None
    unmet_grid_kwh: float | None = None
    available_battery_kwh: float | None = None
    reserve_kwh: float | None = None
    target_soc: float | None = None
    expected_load_kwh: float | None = None
    pv_used_kwh: float | None = None
    trajectory: tuple[EnergyPoint, ...] = ()
    load_basis: str = "battery_discharge_night"
    quality_flags: tuple[str, ...] = ()

    @property
    def charge_now(self) -> bool:
        """Whether the plan requests charging at its evaluation instant."""
        return any(
            item.start <= self.evaluated_at < item.end for item in self.intervals
        )

    @property
    def next_start(self) -> datetime | None:
        return next((item.start for item in self.intervals), None)

    @property
    def next_end(self) -> datetime | None:
        return next((item.end for item in self.intervals), None)
