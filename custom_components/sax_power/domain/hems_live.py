"""Causal, bounded SAX night residuals (REQ-HEMS-LIVE-ADJUSTMENT)."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from .hems import EnergySlot, LoadForecast
from .hems_load import (
    DAWN_DURATION,
    DischargeObservation,
    NightSpan,
    _valid_observations,
    aware,
    finite_number,
)

LIVE_MODEL_KEY = (
    "residual-v1:45m:30valid:5fresh:half30:expiry60:gain0.5:cap0.5:floor0.1:decay"
)
LOOKBACK = timedelta(minutes=45)
MIN_VALID_SECONDS = 30 * 60
MAX_OBSERVATION_AGE = timedelta(minutes=5)
HALF_LIFE_SECONDS = 30 * 60
MAX_LIFETIME = timedelta(minutes=60)
LIVE_FLAG = "live_residual_v1"


@dataclass(frozen=True, slots=True)
class ArchivedLoadBasis:
    """An immutable, uncorrected forecast actually issued before its targets."""

    issued_at: datetime
    intervals: tuple[EnergySlot, ...]
    model_key: str


@dataclass(frozen=True, slots=True)
class LiveResult:
    """Shadow forecast; activation remains the runtime/archive gate's decision."""

    forecast: LoadForecast
    basis_key: str
    reason: str
    anchor: datetime | None = None
    valid_minutes: float = 0.0
    measured_kwh: float | None = None
    expected_kwh: float | None = None
    correction_kw: float | None = None
    expires_at: datetime | None = None
    remaining_seconds: float = 0.0
    model_key: str = LIVE_MODEL_KEY


@dataclass(frozen=True, slots=True)
class _Evidence:
    anchor: datetime
    seconds: float
    measured_kwh: float
    expected_kwh: float
    correction_kw: float


def _valid_intervals(intervals: tuple[EnergySlot, ...]) -> bool:
    previous: datetime | None = None
    for item in intervals:
        if (
            not aware(item.start)
            or not aware(item.end)
            or item.end <= item.start
            or not finite_number(item.energy_kwh)
            or item.energy_kwh < 0
            or (previous is not None and item.start < previous)
            or LIVE_FLAG in item.quality_flags
        ):
            return False
        previous = item.end
    return True


def _paired_evidence(
    observations: tuple[DischargeObservation, ...],
    archives: tuple[ArchivedLoadBasis, ...],
    *,
    start: datetime,
    end: datetime,
    model_key: str,
    max_power_kw: float,
) -> _Evidence | None:
    sources = tuple(
        source
        for source in archives
        if source.model_key == model_key
        and aware(source.issued_at)
        and source.issued_at < end
        and _valid_intervals(source.intervals)
    )
    measured = expected = seconds = 0.0
    latest: datetime | None = None
    for observed in observations:
        if observed.quality != "valid" or observed.end > end:
            continue
        lo, hi = max(start, observed.start), min(end, observed.end)
        if lo >= hi:
            continue
        boundaries = {lo, hi}
        for source in sources:
            for slot in source.intervals:
                if lo < slot.start < hi:
                    boundaries.add(slot.start)
                if lo < slot.end < hi:
                    boundaries.add(slot.end)
        ordered = sorted(boundaries)
        for left, right in zip(ordered, ordered[1:], strict=False):
            choices = [
                (source.issued_at, slot)
                for source in sources
                if source.issued_at < left
                for slot in source.intervals
                if slot.start <= left and right <= slot.end
            ]
            if not choices:
                continue
            latest_issue = max(issued for issued, _ in choices)
            latest_slots = [slot for issued, slot in choices if issued == latest_issue]
            # Conflicting same-time outputs cannot be resolved by input ordering.
            powers = {
                slot.energy_kwh * 3600 / (slot.end - slot.start).total_seconds()
                for slot in latest_slots
            }
            if len(powers) != 1:
                continue
            duration = (right - left).total_seconds()
            measured += (
                observed.energy_kwh
                * duration
                / (observed.end - observed.start).total_seconds()
            )
            expected += powers.pop() * duration / 3600
            seconds += duration
            latest = right
    if seconds < MIN_VALID_SECONDS or latest is None:
        return None
    if not all(finite_number(value) for value in (measured, expected, seconds)):
        return None
    mean_expected = expected * 3600 / seconds
    residual = (measured - expected) * 3600 / seconds * 0.5
    cap = min(max_power_kw, max(0.1, 0.5 * mean_expected))
    return _Evidence(latest, seconds, measured, expected, max(-cap, min(cap, residual)))


def _corrected_energy(
    item: EnergySlot, evidence: _Evidence, *, max_power_kw: float, model_end: datetime
) -> float:
    """Integrate the clipped exponential, including crossings within a slot."""
    lo, hi = max(item.start, evidence.anchor), min(
        item.end, evidence.anchor + MAX_LIFETIME, model_end
    )
    if lo >= hi:
        return item.energy_kwh
    power = item.energy_kwh * 3600 / (item.end - item.start).total_seconds()
    decay = math.log(2) / HALF_LIFE_SECONDS
    start = (lo - evidence.anchor).total_seconds()
    stop = (hi - evidence.anchor).total_seconds()
    boundaries = {start, stop}
    for limit in (0.0, max_power_kw):
        if evidence.correction_kw:
            ratio = (limit - power) / evidence.correction_kw
            if ratio > 0:
                crossing = -math.log(ratio) / decay
                if start < crossing < stop:
                    boundaries.add(crossing)
    total = power * ((item.end - item.start).total_seconds() - (stop - start))
    ordered = sorted(boundaries)
    for left, right in zip(ordered, ordered[1:], strict=False):
        midpoint = power + evidence.correction_kw * math.exp(
            -decay * (left + right) / 2
        )
        if midpoint <= 0:
            continue
        if midpoint >= max_power_kw:
            total += max_power_kw * (right - left)
        else:
            total += power * (right - left) + evidence.correction_kw / decay * (
                math.exp(-decay * left) - math.exp(-decay * right)
            )
    return max(0.0, total / 3600)


class LiveAdjuster:
    """Transient evidence; a restart deliberately requires new observations."""

    def __init__(self) -> None:
        self._context: tuple[str, datetime, datetime, float] | None = None
        self._started_at: datetime | None = None
        self._evidence: _Evidence | None = None
        self._last_evaluated_at: datetime | None = None

    def reset(self) -> None:
        self._context = None
        self._started_at = None
        self._evidence = None
        self._last_evaluated_at = None

    def evaluate(
        self,
        *,
        basis: LoadForecast,
        observations: tuple[DischargeObservation, ...],
        archived_bases: tuple[ArchivedLoadBasis, ...],
        as_of: datetime,
        night: NightSpan,
        model_key: str,
        max_discharge_power_w: float | None,
        archive_enabled: bool,
        free_discharge: bool,
    ) -> LiveResult:
        """Return a candidate only; never change reserve, PV or device permissions."""
        if not aware(as_of):
            raise ValueError("as_of must be timezone-aware")
        as_of = as_of.astimezone(UTC)
        if self._last_evaluated_at is not None and as_of < self._last_evaluated_at:
            self.reset()
        self._last_evaluated_at = as_of
        invalid = (
            basis.quality_reason is not None
            or not basis.intervals
            or not _valid_intervals(basis.intervals)
            or LIVE_FLAG in basis.quality_flags
            or not aware(night.start)
            or not aware(night.end)
            or night.end <= night.start
            or not finite_number(max_discharge_power_w)
            or max_discharge_power_w <= 0
            or type(archive_enabled) is not bool
            or type(free_discharge) is not bool
        )
        if invalid:
            self.reset()
            return LiveResult(basis, model_key, "invalid_basis")
        assert max_discharge_power_w is not None
        if not night.start <= as_of < night.end + DAWN_DURATION:
            self.reset()
            return LiveResult(basis, model_key, "outside_model_scope")
        context = (model_key, night.start, night.end, max_discharge_power_w)
        if context != self._context:
            self._context = context
            self._started_at = as_of
            self._evidence = None
        assert self._started_at is not None
        reason = "insufficient_live_evidence"
        if not archive_enabled:
            reason = "archive_disabled"
        elif not free_discharge:
            reason = "discharge_not_free"
        elif as_of >= night.end:
            reason = "dawn_no_new_evidence"
        elif not _valid_observations(observations):
            reason = "invalid_observations"
        else:
            evidence = _paired_evidence(
                observations,
                archived_bases,
                start=max(as_of - LOOKBACK, night.start, self._started_at),
                end=as_of,
                model_key=model_key,
                max_power_kw=max_discharge_power_w / 1000,
            )
            if evidence is not None:
                if as_of - evidence.anchor > MAX_OBSERVATION_AGE:
                    reason = "live_evidence_stale"
                elif self._evidence is None or evidence.anchor > self._evidence.anchor:
                    self._evidence = evidence
                    reason = "adjusted"
                else:
                    reason = "unchanged_evidence"
        evidence = self._evidence
        if evidence is None:
            return LiveResult(basis, model_key, reason)
        expiry = evidence.anchor + MAX_LIFETIME
        if as_of >= expiry:
            return LiveResult(basis, model_key, "correction_expired")
        forecast = replace(
            basis,
            intervals=tuple(
                replace(
                    item,
                    energy_kwh=_corrected_energy(
                        item,
                        evidence,
                        max_power_kw=max_discharge_power_w / 1000,
                        model_end=night.end + DAWN_DURATION,
                    ),
                    quality_flags=(*item.quality_flags, LIVE_FLAG),
                )
                for item in basis.intervals
            ),
            quality_flags=(*basis.quality_flags, LIVE_FLAG),
        )
        return LiveResult(
            forecast,
            model_key,
            reason,
            evidence.anchor,
            evidence.seconds / 60,
            evidence.measured_kwh,
            evidence.expected_kwh,
            evidence.correction_kw,
            expiry,
            (expiry - as_of).total_seconds(),
        )
