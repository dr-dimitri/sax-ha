"""Verknüpfe Prognosekandidaten und Gütenachweis ohne eigene Ladefreigabe."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from functools import partial
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ..const import (
    CONF_HEMS_ARCHIVE_ENABLED,
    CONF_HEMS_FORECAST_MODE,
    CONF_HEMS_HISTORY_DAYS,
    CONF_HEMS_LIVE_ADJUSTMENT,
)
from ..domain.hems import EnergyPlan, EnergySlot, LoadForecast, PlanningSnapshot
from ..domain.hems_evaluation import (
    ForecastRecord,
    ForecastSeries,
    GateResult,
    ModelKey,
    canonical_json,
    energy_between,
    stable_id,
)
from ..domain.hems_live import LIVE_MODEL_KEY, LiveAdjuster, LiveResult
from ..domain.hems_load import DischargeObservation, LoadVariants
from ..domain.hems_uncertainty import UncertaintyClass, UncertaintyResult
from ..infrastructure.hems_archive import HemsArchive
from ..infrastructure.hems_history import HemsHistory


def _json(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json(item) for item in value]
    return value


def _select_phases(
    baseline: LoadForecast,
    candidate: LoadForecast,
    sunrise: datetime,
    *,
    night_approved: bool,
    dawn_approved: bool,
) -> LoadForecast:
    """Der separat geprüfte Dämmerungsnachweis ersetzt keine Nachtfreigabe."""
    if (
        candidate.quality_reason is not None
        or not candidate.intervals
        or not (night_approved or dawn_approved)
    ):
        return baseline
    slots: list[EnergySlot] = []
    for phase, approved in (("night", night_approved), ("dawn", dawn_approved)):
        source = candidate if approved else baseline
        for slot in source.intervals:
            start = slot.start if phase == "night" else max(sunrise, slot.start)
            end = min(sunrise, slot.end) if phase == "night" else slot.end
            if start < end:
                slots.append(
                    replace(
                        slot,
                        start=start,
                        end=end,
                        energy_kwh=slot.energy_kwh
                        * (end - start).total_seconds()
                        / (slot.end - slot.start).total_seconds(),
                    )
                )
    return replace(
        candidate,
        intervals=tuple(slots),
        quality_flags=tuple(
            sorted({flag for slot in slots for flag in slot.quality_flags})
        ),
    )


class HemsPrediction:
    """Ein Config Entry besitzt einen beobachtenden, versionierten Lernpfad."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self.archive = HemsArchive(hass, entry_id)
        self.live = LiveAdjuster()
        self.enabled = False
        self.history_days = 7
        self.mode = "observe"
        self.live_enabled = False
        self.variants: LoadVariants | None = None
        self.live_result: LiveResult | None = None
        self.selected = LoadForecast()
        self.candidate = LoadForecast()
        self.baseline_key = ""
        self.raw_key = ""
        self.candidate_key = ""
        self.applied_key = ""
        self.gates: dict[str, GateResult] = {}
        self.uncertainty: UncertaintyResult | None = None
        self._observations: tuple[DischargeObservation, ...] = ()
        self._previous_record: str | None = None
        self._evaluated_at: datetime | None = None
        self._generation = 0
        self._configuration: tuple[object, ...] | None = None
        self.summary: dict[str, Any] = {}

    def configure(self, options: dict[str, Any], as_of: datetime) -> None:
        days = 28 if options.get(CONF_HEMS_HISTORY_DAYS) in (28, "28") else 7
        live = options.get(CONF_HEMS_LIVE_ADJUSTMENT) is True
        if (days, live) != (self.history_days, self.live_enabled):
            self.live = LiveAdjuster()
            self.gates = {}
            self.uncertainty = None
        self.history_days, self.live_enabled = days, live
        self.mode = (
            "auto" if options.get(CONF_HEMS_FORECAST_MODE) == "auto" else "observe"
        )
        self.enabled = options.get(CONF_HEMS_ARCHIVE_ENABLED) is True
        configuration = (days, live, self.mode, self.enabled)
        if configuration != self._configuration:
            self._generation += 1
            self.uncertainty = None
            self.summary = {}
            self._configuration = configuration
        self.archive.configure(self.enabled, as_of=as_of)

    def restore_baseline(self, baseline: LoadForecast) -> None:
        """REQ-HEMS-FORECAST-EVALUATION: Unvollständige Zuordnung nie archivieren."""
        self.selected = self.candidate = baseline
        self.applied_key = self.baseline_key
        self.variants = None
        self.live_result = None
        self.gates = {}
        self.uncertainty = None
        self.summary = {}
        self._observations = ()

    async def async_start(self) -> None:
        await self.archive.async_start()

    async def async_prepare(
        self,
        history: HemsHistory,
        baseline: LoadForecast,
        *,
        as_of: datetime,
        max_discharge_power_w: float | None,
        free_discharge: bool,
    ) -> LoadForecast:
        self.restore_baseline(baseline)
        self._evaluated_at = as_of
        variants = history.variants
        self.variants = variants if isinstance(variants, LoadVariants) else None
        generation = self._generation
        if (
            not isinstance(self.variants, LoadVariants)
            or self.variants.current_night is None
        ):
            return baseline
        variants = self.variants
        context = stable_id(
            (
                self.hass.config.time_zone,
                self.hass.config.latitude,
                self.hass.config.longitude,
            )
        )
        self.baseline_key = ModelKey(variants.baseline_key, context).identifier
        self.raw_key = ModelKey(
            variants.candidate_key, context, self.history_days
        ).identifier
        self.candidate_key = ModelKey(
            variants.candidate_key,
            context,
            self.history_days,
            live_version=LIVE_MODEL_KEY if self.live_enabled else "off",
            live_parameters=LIVE_MODEL_KEY if self.live_enabled else "none",
            live_policy=(
                "decay-on-censor:no-new-anchor-off:v1" if self.live_enabled else "off"
            ),
        ).identifier
        self._observations = history.observations(as_of)
        candidate = variants.candidate
        if self.live_enabled:
            archived = await self.hass.async_add_executor_job(
                self.archive.archived_baselines,
                as_of - timedelta(minutes=45),
                as_of,
                self.raw_key,
            )
            if generation != self._generation:
                return baseline
            adjuster = self.live
            result = await self.hass.async_add_executor_job(
                partial(
                    adjuster.evaluate,
                    basis=candidate,
                    observations=history.observations(
                        as_of, lookback=timedelta(minutes=45)
                    ),
                    archived_bases=archived,
                    as_of=as_of,
                    night=variants.current_night,
                    model_key=self.raw_key,
                    max_discharge_power_w=max_discharge_power_w,
                    archive_enabled=self.enabled,
                    free_discharge=free_discharge,
                )
            )
            if generation != self._generation:
                return baseline
            self.live_result = result
            candidate = result.forecast
        else:
            self.live = LiveAdjuster()
        self.candidate = candidate
        generation = self._generation
        for phase in ("night", "dawn"):
            self.gates[phase] = await self.archive.async_gate(
                self.baseline_key,
                self.candidate_key,
                phase=phase,
                horizon="60m",
                as_of=as_of,
            )
            if generation != self._generation:
                return baseline
        candidate_valid = candidate.quality_reason is None and bool(candidate.intervals)
        night_approved = (
            self.mode == "auto" and candidate_valid and self.gates["night"].approved
        )
        dawn_approved = (
            self.mode == "auto" and candidate_valid and self.gates["dawn"].approved
        )
        self.selected = _select_phases(
            baseline,
            candidate,
            variants.current_night.end,
            night_approved=night_approved,
            dawn_approved=dawn_approved,
        )
        self.applied_key = (
            self.candidate_key
            if night_approved and dawn_approved
            else (
                self.baseline_key
                if not (night_approved or dawn_approved)
                else canonical_json(
                    {
                        "night": (
                            self.candidate_key if night_approved else self.baseline_key
                        ),
                        "dawn": (
                            self.candidate_key if dawn_approved else self.baseline_key
                        ),
                    }
                )
            )
        )
        return self.selected

    async def async_record(
        self, snapshot: PlanningSnapshot, plan: EnergyPlan, *, issued_at: datetime
    ) -> None:
        variants = self.variants
        if (
            not self.enabled
            or not isinstance(variants, LoadVariants)
            or variants.current_night is None
            or snapshot.load.quality_reason is not None
            or snapshot.load.model_end is None
            or issued_at >= snapshot.load.model_end
        ):
            return
        generation = self._generation
        night = variants.current_night
        start = issued_at.astimezone(UTC).replace(
            minute=0, second=0, microsecond=0
        ) + timedelta(hours=1)
        end = start + timedelta(hours=1)
        phase = "night" if end <= night.end else "dawn"
        zone = dt_util.get_time_zone(self.hass.config.time_zone) or UTC
        group = (
            f"issued:{issued_at.astimezone(zone).hour:02d}|"
            f"target:{start.astimezone(zone).hour:02d}"
        )
        if (end <= night.end or night.end <= start) and end <= snapshot.load.model_end:
            self.uncertainty = await self.archive.async_uncertainty(
                UncertaintyClass(self.applied_key, phase=phase, output_group=group),
                expected_kwh=energy_between(snapshot.load.intervals, start, end),
                start=start,
                end=end,
                as_of=issued_at,
            )
        if generation != self._generation or not self.enabled:
            return
        metadata = {
            "history_days": variants.history_days,
            "available_history_days": variants.available_history_days,
            "nights_count": variants.candidate.nights_count,
            "observed_hours": variants.candidate.observed_hours,
            "coverage": variants.candidate.coverage,
            "slots": [_json(asdict(row)) for row in variants.candidate_metadata],
        }
        baseline = ForecastSeries(
            self.baseline_key,
            variants.baseline.intervals,
            canonical_json(self._forecast_metadata(variants.baseline)),
        )
        metadata.update(self._forecast_metadata(variants.candidate))
        raw = ForecastSeries(
            self.raw_key, variants.candidate.intervals, canonical_json(metadata)
        )
        candidate = ForecastSeries(
            self.candidate_key, self.candidate.intervals, canonical_json(metadata)
        )
        record_id = stable_id(
            (issued_at, snapshot.revision, self.applied_key, snapshot.load.intervals)
        )
        record = ForecastRecord(
            record_id=record_id,
            issued_at=issued_at,
            data_as_of=snapshot.as_of,
            night_id=night.start.isoformat(),
            night_start=night.start,
            sunrise=night.end,
            model_end=snapshot.load.model_end,
            baseline=baseline,
            applied=ForecastSeries(self.applied_key, snapshot.load.intervals),
            candidate=candidate if self.candidate.quality_reason is None else None,
            raw_profiles=(baseline, raw),
            pv=snapshot.pv,
            planning_parameters_json=canonical_json(
                _json(
                    {
                        "reserve_soc": snapshot.reserve_soc,
                        "max_soc": snapshot.max_soc,
                        "capacity_kwh": snapshot.capacity_kwh,
                        "charge_power_w": snapshot.charge_power_w,
                        "eta_charge": snapshot.eta_charge,
                        "eta_discharge": snapshot.eta_discharge,
                        "physical_min_soc": snapshot.physical_min_soc,
                        "tariff": asdict(snapshot.tariff),
                        "mode": self.mode,
                        "time_zone": self.hass.config.time_zone,
                    }
                )
            ),
            live_metadata_json=canonical_json(self._live_metadata()),
            current_usable_kwh=plan.available_battery_kwh,
            predecessor_id=self._previous_record,
            time_zone=self.hass.config.time_zone,
            bands=(
                (self.uncertainty.candidate_band,)
                if self.uncertainty and self.uncertainty.candidate_band
                else ()
            ),
        )
        await self.archive.async_record(record, self._observations, as_of=issued_at)
        if generation == self._generation:
            self._previous_record = record_id
            summary = await self.archive.async_summary(self.applied_key)
            if generation == self._generation:
                self.summary = summary

    def _live_metadata(self) -> dict[str, Any]:
        result = self.live_result
        phase = (
            "dawn"
            if self.variants is not None
            and self.variants.current_night is not None
            and self._evaluated_at is not None
            and self._evaluated_at >= self.variants.current_night.end
            else "night"
        )
        gate = self.gates.get(phase)
        active = bool(
            result
            and result.correction_kw is not None
            and abs(result.correction_kw) > 1e-9
            and gate is not None
            and gate.approved
            and self._candidate_active
        )
        return {
            "enabled": self.live_enabled,
            "active": active,
            "observing": bool(
                result and result.correction_kw is not None and not active
            ),
            "reason": result.reason if result else "disabled",
            "anchor": result.anchor.isoformat() if result and result.anchor else None,
            "expires_at": (
                result.expires_at.isoformat() if result and result.expires_at else None
            ),
            "adjustment_kw": result.correction_kw if result else None,
            "valid_minutes": result.valid_minutes if result else 0,
            "measured_kwh": result.measured_kwh if result else None,
            "expected_kwh": result.expected_kwh if result else None,
        }

    @staticmethod
    def _forecast_metadata(forecast: LoadForecast) -> dict[str, Any]:
        return _json(
            {
                "generated_at": forecast.generated_at,
                "evaluated_through": forecast.evaluated_through,
                "quality_reason": forecast.quality_reason,
                "quality_flags": forecast.quality_flags,
                "nights_count": forecast.nights_count,
                "observed_hours": forecast.observed_hours,
                "coverage": forecast.coverage,
                "model_start": forecast.model_start,
                "model_end": forecast.model_end,
            }
        )

    @property
    def _candidate_active(self) -> bool:
        night = (
            self.variants.current_night
            if isinstance(self.variants, LoadVariants)
            else None
        )
        phase = (
            "dawn"
            if night and self._evaluated_at and self._evaluated_at >= night.end
            else "night"
        )
        gate = self.gates.get(phase)
        return (
            self.mode == "auto"
            and bool(self.candidate.intervals)
            and self.selected.quality_reason is None
            and self.candidate.quality_reason is None
            and gate is not None
            and gate.approved
        )

    @property
    def attributes(self) -> dict[str, Any]:
        uncertainty = self.uncertainty
        reasons = {
            "insufficient_training_nights": "insufficient_training",
            "training_evidence_missing": "insufficient_training",
            "insufficient_validation_nights": "insufficient_validation",
            "forecast_coverage_missing": "insufficient_coverage",
            "validation_failed": "rejected",
            "coverage_below_threshold": "rejected",
            "validation_stale": "stale",
        }
        return {
            "schema_version": 1,
            "mode": self.mode,
            "history_days": self.history_days,
            "available_history_days": (
                self.variants.available_history_days
                if isinstance(self.variants, LoadVariants)
                else 0
            ),
            "candidate_active": self._candidate_active,
            "retained": self._candidate_active
            and any(g.retained for g in self.gates.values()),
            "comparison_hours": max(
                (g.observed_hours for g in self.gates.values()), default=0
            ),
            "evaluated_at": (
                self._evaluated_at.isoformat() if self._evaluated_at else None
            ),
            "archive": {
                **self.archive.diagnostics,
                "pairs_count": self.archive.diagnostics["pairs"],
                "truncated": self.archive.diagnostics["pruned"] > 0,
            },
            "live": self._live_metadata(),
            "summary": self.summary,
            "gates": {phase: _json(asdict(gate)) for phase, gate in self.gates.items()},
            "uncertainty": {
                "status": (
                    "validated"
                    if uncertainty and uncertainty.status == "reliable"
                    else uncertainty.status if uncertainty else "unavailable"
                ),
                "reason": (
                    reasons.get(uncertainty.reason, uncertainty.reason)
                    if uncertainty
                    else "not_validated"
                ),
                "expected_kwh": uncertainty.expected_kwh if uncertainty else None,
                "lower_kwh": uncertainty.lower_kwh if uncertainty else None,
                "upper_kwh": uncertainty.upper_kwh if uncertainty else None,
                "start": (
                    uncertainty.start.isoformat()
                    if uncertainty and uncertainty.start
                    else None
                ),
                "end": (
                    uncertainty.end.isoformat()
                    if uncertainty and uncertainty.end
                    else None
                ),
                "training_nights": uncertainty.training_nights if uncertainty else 0,
                "validation_nights": (
                    uncertainty.validation_nights if uncertainty else 0
                ),
                "empirical_coverage": uncertainty.hit_rate if uncertainty else None,
                "mean_width_kwh": uncertainty.mean_width_kwh if uncertainty else None,
            },
        }

    async def async_delete(self) -> None:
        self._generation += 1
        self.live = LiveAdjuster()
        self.gates = {}
        self.uncertainty = None
        self._previous_record = None
        self.summary = {}
        await self.archive.async_delete()

    async def async_stop(self) -> None:
        self._generation += 1
        self.live = LiveAdjuster()
        await self.archive.async_stop()
