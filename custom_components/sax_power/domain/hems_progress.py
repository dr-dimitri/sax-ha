"""Live Fortschrittsnachweis innerhalb einer SOC-Stufe (REQ-HEMS-RUNTIME)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from math import isfinite


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        result = float(value)
    except OverflowError:
        return None
    return result if isfinite(result) else None


def _soc(value: object) -> float | None:
    result = _number(value)
    return result if result is not None and 0 <= result <= 100 else None


def _utc(value: object) -> datetime | None:
    try:
        result = datetime.fromisoformat(value) if isinstance(value, str) else value
        return (
            result.astimezone(UTC)
            if isinstance(result, datetime) and result.utcoffset() is not None
            else None
        )
    except ValueError, TypeError, OverflowError:
        return None


@dataclass(frozen=True, slots=True)
class ProgressEstimate:
    """SOC-Schätzung ohne Ladeabsicht oder Vollzugsfreigabe."""

    effective_soc: float | None
    correction_kwh: float = 0.0
    observed_at: datetime | None = None
    reason: str = "progress_unavailable"


class SocProgressLedger:
    """Speicherleistung unabhängig von Planwechseln und Lade-Intent bilanzieren.

    Positive SAX-Leistung bedeutet Entladung. Zwischen zwei frischen Messungen
    zählt die kleinere Einspeicherung bzw. größere Entladung der Endpunkte.
    Damit erhält insbesondere ein Start-/Stoppintervall keine unbewiesene volle
    Ladeenergie. Die Korrektur ist eine konservative Schätzung im Rahmen der
    Messauflösung, kein Ersatz für einen vom BMS gemessenen Ladezustand.
    """

    def __init__(
        self,
        *,
        max_sample_gap_seconds: float = 30,
        max_restore_age_seconds: float = 30,
    ) -> None:
        for value in (max_sample_gap_seconds, max_restore_age_seconds):
            if _number(value) is None or not 0 < value <= 30:
                raise ValueError("Fortschrittsnachweise dürfen höchstens 30 s alt sein")
        self._max_gap = max_sample_gap_seconds
        self._max_restore_age = max_restore_age_seconds
        self._settings: tuple[float, float, float] | None = None
        self._raw_soc: float | None = None
        self._correction = 0.0
        self._at: datetime | None = None
        self._evidence_at: datetime | None = None
        self._power: float | None = None
        self._restore_discharge_w: float | None = None
        self._reason = "progress_unavailable"

    def invalidate(self) -> None:
        """Unbekannte Gerätezustände unterbrechen den Nachweis ausdrücklich."""
        self._raw_soc = None
        self._correction = 0.0
        self._at = self._evidence_at = None
        self._power = self._restore_discharge_w = None
        self._reason = "progress_unavailable"

    def configure(
        self,
        *,
        capacity_kwh: object,
        eta_charge: object,
        eta_discharge: object,
    ) -> bool:
        """Andere Kapazität/Wirkungsgrade beginnen einen neuen Energienachweis."""
        capacity, charge, discharge = map(
            _number, (capacity_kwh, eta_charge, eta_discharge)
        )
        settings = (
            (capacity, charge, discharge)
            if capacity is not None
            and capacity > 0
            and charge is not None
            and 0 < charge <= 1
            and discharge is not None
            and 0 < discharge <= 1
            else None
        )
        if settings != self._settings:
            self.invalidate()
            self._settings = settings
        return settings is not None

    def _clamp(self, correction: float) -> float:
        assert self._settings is not None and self._raw_soc is not None
        capacity = self._settings[0]
        step = capacity / 100
        return max(
            -min(step, self._raw_soc * step),
            min(correction, step, (100 - self._raw_soc) * step),
        )

    def _rate(self, power: float) -> float:
        assert self._settings is not None
        _, charge, discharge = self._settings
        return -power * charge if power < 0 else -power / discharge

    def observe(
        self, *, at: datetime, raw_soc: object, storage_power_w: object
    ) -> ProgressEstimate:
        """Genau einen frischen Leistungssample bilanzieren; doppelte ignorieren."""
        instant, raw, power = _utc(at), _soc(raw_soc), _number(storage_power_w)
        if instant is None:
            self.invalidate()
            return ProgressEstimate(raw, reason="progress_invalid_time")
        first_restored_sample = (
            instant == self._at
            and self._power is None
            and self._restore_discharge_w is not None
        )
        if self._at is not None and (
            instant < self._at or (instant == self._at and not first_restored_sample)
        ):
            return self.estimate(as_of=self._at, raw_soc=self._raw_soc)
        if self._settings is None or raw is None or power is None:
            self.invalidate()
            self._at = instant
            self._reason = "progress_invalid_sample"
            return ProgressEstimate(raw, reason=self._reason)
        seconds = (instant - self._at).total_seconds() if self._at else None
        if raw != self._raw_soc or seconds is None or seconds > self._max_gap:
            self._correction = 0.0
            self._reason = (
                "progress_gap"
                if seconds is not None and seconds > self._max_gap
                else "progress_reanchored"
            )
        elif self._power is not None:
            delta = (
                min(self._rate(self._power), self._rate(power)) * seconds / 3_600_000
            )
            self._correction = self._clamp(self._correction + delta)
            self._reason = "progress_observed"
        elif self._restore_discharge_w is not None:
            self._correction = self._clamp(
                self._correction
                - self._restore_discharge_w / self._settings[2] * seconds / 3_600_000
            )
            self._reason = "progress_restored"
        self._raw_soc, self._power = raw, power
        self._at = self._evidence_at = instant
        self._restore_discharge_w = None
        return self.estimate(as_of=instant, raw_soc=raw)

    def estimate(self, *, as_of: datetime, raw_soc: object) -> ProgressEstimate:
        """Nur zur aktuellen Roh-SOC-Stufe passenden und frischen Rest anwenden."""
        instant, raw = _utc(as_of), _soc(raw_soc)
        if raw is None:
            return ProgressEstimate(None, reason="progress_invalid_soc")
        if self._settings is None:
            return ProgressEstimate(raw, reason="progress_unconfigured")
        if raw != self._raw_soc:
            self.invalidate()
            return ProgressEstimate(raw, reason="progress_soc_changed")
        if instant is None or self._evidence_at is None or self._at is None:
            return ProgressEstimate(raw, reason="progress_unavailable")
        if (
            instant < self._at
            or not 0 <= (instant - self._evidence_at).total_seconds() <= self._max_gap
        ):
            return ProgressEstimate(raw, reason="progress_stale")
        effective = raw + self._correction / self._settings[0] * 100
        return ProgressEstimate(
            effective, self._correction, self._evidence_at, self._reason
        )

    def dump(self) -> dict[str, object] | None:
        """Nur gemessenen Rest persistieren; Restore verlängert seine Frist nicht."""
        if self._settings is None or self._power is None or self._at is None:
            return None
        return {
            "version": 1,
            "capacity_kwh": self._settings[0],
            "eta_charge": self._settings[1],
            "eta_discharge": self._settings[2],
            "raw_soc": self._raw_soc,
            "correction_kwh": self._correction,
            "observed_at": self._at.isoformat(),
        }

    def restore(
        self,
        payload: object,
        *,
        as_of: datetime,
        raw_soc: object,
        max_discharge_power_w: object,
    ) -> bool:
        """Kurzen Neustart konservativ überbrücken, niemals einen Plan freigeben.

        Während des unbekannten Neustartintervalls wird die maximal mögliche
        Entladung abgezogen. Ohne Grenze, aktuellen SOC oder passenden Kontext
        wird kein Restnachweis angenommen. Die alte Leistung wird nie fortgesetzt.
        """
        self.invalidate()
        if self._settings is None or not isinstance(payload, Mapping):
            return False
        instant, raw = _utc(as_of), _soc(raw_soc)
        observed = _utc(payload.get("observed_at"))
        limit, correction = map(
            _number, (max_discharge_power_w, payload.get("correction_kwh"))
        )
        settings = tuple(
            _number(payload.get(key))
            for key in ("capacity_kwh", "eta_charge", "eta_discharge")
        )
        if (
            type(payload.get("version")) is not int
            or payload.get("version") != 1
            or instant is None
            or observed is None
            or raw is None
            or _soc(payload.get("raw_soc")) != raw
            or settings != self._settings
            or limit is None
            or limit <= 0
            or correction is None
            or abs(correction) > self._settings[0] / 100
        ):
            return False
        age = (instant - observed).total_seconds()
        if not 0 <= age <= min(self._max_gap, self._max_restore_age):
            return False
        self._raw_soc = raw
        self._correction = self._clamp(
            correction - limit / self._settings[2] * age / 3_600_000
        )
        self._at, self._evidence_at = instant, observed
        self._restore_discharge_w = limit
        self._reason = "progress_restored"
        return True
