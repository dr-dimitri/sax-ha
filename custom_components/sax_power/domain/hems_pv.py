"""Öffentliche PV-Antworten normalisieren (REQ-HEMS-PV-INPUT)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from itertools import pairwise
from math import isclose, isfinite
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .hems import EnergySlot, PvForecast

MAX_HORIZON = timedelta(hours=48)
_STEP = timedelta(minutes=15)
_MAX_SOURCE_INTERVALS = 4096


def utc_datetime(value: object) -> datetime:
    """Nur eindeutige absolute Zeitpunkte als UTC annehmen."""
    result = datetime.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(result, datetime) or result.utcoffset() is None:
        raise ValueError("Ein eindeutiger UTC-Zeitpunkt ist erforderlich")
    return result.astimezone(UTC)


def request_bounds(as_of: datetime, end: datetime | None) -> tuple[datetime, datetime]:
    """Den realen Suchhorizont unabhängig von lokalen Tageslängen begrenzen."""
    start = utc_datetime(as_of)
    finish = utc_datetime(end) if end is not None else start + MAX_HORIZON
    if not start < finish <= start + MAX_HORIZON:
        raise ValueError("Der PV-Horizont muss zwischen 0 und 48 Stunden liegen")
    return start, finish


def empty_forecast(
    provider: str,
    source_id: str,
    as_of: datetime,
    end: datetime,
    reason: str | None = None,
    *,
    max_age_seconds: float = 3600,
) -> PvForecast:
    """Fehlende Daten bleiben ohne operative Zahlen und erfundene Abrufzeit."""
    return PvForecast(
        provider=provider,
        source_id=source_id,
        generated_at=as_of,
        requested_start=as_of,
        requested_end=end,
        quality_reason=reason,
        max_age_seconds=max_age_seconds,
        freshness_policy=(
            "provider_60_minutes"
            if provider == "pv_forecast"
            else "sax_max_age_assumption"
        ),
    )


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("Die Prognose benötigt numerische Energie-/Leistungswerte")
    result = float(value)
    if not isfinite(result) or result < 0:
        raise ValueError("Ungültige Energie-/Leistungsprognose")
    return result


def _freshness(base: PvForecast, fetched: object) -> PvForecast:
    try:
        fetched_at = utc_datetime(fetched)
    except ValueError, TypeError, OverflowError:
        return replace(base, quality_reason="pv_missing_fetched_at")
    assert base.generated_at is not None and base.max_age_seconds is not None
    age = (base.generated_at - fetched_at).total_seconds()
    try:
        expires = fetched_at + timedelta(seconds=base.max_age_seconds)
    except OverflowError:
        return replace(base, quality_reason="pv_invalid_fetched_at")
    return replace(
        base,
        fetched_at=fetched_at,
        valid_until=expires,
        quality_reason=(
            "pv_future_fetched_at"
            if age < 0
            else "pv_stale_forecast" if age > base.max_age_seconds else None
        ),
    )


def _project(slot: EnergySlot, start: datetime, end: datetime) -> list[EnergySlot]:
    left, finish = max(slot.start, start), min(slot.end, end)
    total_seconds = (slot.end - slot.start).total_seconds()
    result: list[EnergySlot] = []
    while left < finish:
        quarter = left.replace(minute=left.minute // 15 * 15, second=0, microsecond=0)
        right = min(quarter + _STEP, finish)
        energy = slot.energy_kwh * ((right - left).total_seconds() / total_seconds)
        result.append(EnergySlot(left, right, energy))
        left = right
    return result


def _intervals(base: PvForecast, rows: object, *, solcast: bool = False) -> PvForecast:
    if (
        not isinstance(rows, Sequence)
        or isinstance(rows, str | bytes)
        or len(rows) > _MAX_SOURCE_INTERVALS
    ):
        return replace(base, quality_reason="pv_invalid_intervals")
    assert base.requested_start is not None and base.requested_end is not None
    start, end = base.requested_start, base.requested_end
    bounds: list[tuple[datetime, datetime, Mapping[str, Any]]] = []
    try:
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError("Ungültiges Prognoseintervall")
            left = utc_datetime(row.get("period_start" if solcast else "start"))
            right = (
                left + timedelta(minutes=30)
                if solcast
                else utc_datetime(row.get("end"))
            )
            if right <= left:
                raise ValueError("Ungültige Intervallgrenzen")
            if left < end and right > start:
                bounds.append((left, right, row))
    except ValueError, TypeError, OverflowError:
        return replace(base, quality_reason="pv_invalid_intervals")
    bounds.sort(key=lambda item: item[0])
    flags: set[str] = set(base.quality_flags)
    conflicts: set[int] = set()
    # Widersprüchliche spätere Quellenabschnitte entwerten keine bereits
    # vollständige Nachtbrücke; überlappende Angaben bleiben echte Datenlücken.
    cluster: list[int] = []
    cluster_end = start
    for index, (left, right, _) in enumerate(bounds):
        if left >= cluster_end:
            if len(cluster) > 1:
                conflicts.update(cluster)
            cluster = []
        cluster.append(index)
        cluster_end = max(right, cluster_end)
    if len(cluster) > 1:
        conflicts.update(cluster)
    if conflicts:
        flags.add("pv_overlapping_intervals")
    slots: list[EnergySlot] = []
    for index, (left, right, row) in enumerate(bounds):
        if index in conflicts:
            continue
        try:
            if solcast:
                energy = _number(row.get("pv_estimate")) * 0.5
            else:
                quality = row.get("quality_flags")
                if not isinstance(quality, list | tuple) or any(
                    not isinstance(flag, str) for flag in quality
                ):
                    raise ValueError("Ungültige Qualitätsangaben")
                if row.get("is_complete") is not True or quality:
                    flags.add(
                        "pv_incomplete_forecast"
                        if not quality
                        else "pv_input_fallbacks"
                    )
                    flags.update(f"pv_source_{flag}" for flag in quality)
                    continue
                energy = _number(row.get("energy_kwh"))
                power = _number(row.get("ac_power_kw"))
                if not isclose(
                    energy,
                    power * (right - left).total_seconds() / 3600,
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                ):
                    raise ValueError("Energie und Leistung widersprechen einander")
            if not isfinite(energy):
                raise ValueError("Ungültige Intervallenergie")
        except ValueError, TypeError, OverflowError:
            flags.add("pv_invalid_interval_value")
            continue
        slots.extend(_project(EnergySlot(left, right, energy), start, end))
    complete = (
        bool(slots)
        and slots[0].start == start
        and slots[-1].end == end
        and all(a.end == b.start for a, b in pairwise(slots))
    )
    if not complete:
        flags.add("pv_partial_coverage")
    return replace(
        base,
        intervals=tuple(slots),
        coverage_start=slots[0].start if slots else None,
        coverage_end=slots[-1].end if slots else None,
        coverage_complete=complete,
        quality_reason=None if slots else "pv_no_valid_intervals",
        quality_flags=tuple(sorted(flags)),
    )


def normalize_pv_forecast(
    payload: object, *, as_of: datetime, end: datetime, source_id: str
) -> PvForecast:
    """Schema 1 lesen; mangelhafte spätere Abschnitte sperren keine frühe Brücke."""
    start, end = request_bounds(as_of, end)
    base = empty_forecast("pv_forecast", source_id, start, end)
    if (
        not isinstance(payload, Mapping)
        or type(payload.get("schema_version")) is not int
        or payload.get("schema_version") != 1
    ):
        return replace(base, quality_reason="pv_unsupported_schema")
    if payload.get("scope", "total") != "total":
        return replace(base, quality_reason="pv_invalid_scope")
    try:
        timezone = payload["timezone"]
        if not isinstance(timezone, str):
            raise ValueError("Die Anlagenzeitzone fehlt")
        ZoneInfo(timezone)
        coverage = payload["coverage"]
        if (
            not isinstance(coverage, Mapping)
            or type(coverage.get("complete")) is not bool
        ):
            raise ValueError("Die Abdeckungsangaben fehlen")
        if coverage.get("start") is not None or coverage.get("end") is not None:
            if utc_datetime(coverage.get("start")) >= utc_datetime(coverage.get("end")):
                raise ValueError("Ungültige Abdeckung")
    except KeyError, ValueError, TypeError, OverflowError, ZoneInfoNotFoundError:
        return replace(base, quality_reason="pv_invalid_metadata")
    success = payload.get("last_update_success")
    base = replace(
        base,
        update_success=success if type(success) is bool else None,
        timezone=timezone,
        origin=(
            payload.get("origin")
            if payload.get("origin") in ("live", "restored")
            else "unknown"
        ),
    )
    base = _freshness(base, payload.get("fetched_at"))
    if base.quality_reason is not None:
        return base
    if success is not True:
        return replace(
            base,
            quality_reason=(
                "pv_update_failed" if success is False else "pv_missing_update_status"
            ),
        )
    return _intervals(base, payload.get("intervals"))


def normalize_solcast_forecast(
    payload: object,
    *,
    as_of: datetime,
    end: datetime,
    source_id: str,
    fetched_at: datetime,
    max_age_hours: float = 24,
) -> PvForecast:
    """Solcasts dokumentierte halbstündliche kW in AC-kWh umrechnen."""
    start, end = request_bounds(as_of, end)
    if isinstance(max_age_hours, bool) or not 1 <= max_age_hours <= 24:
        raise ValueError("Solcast-Prognosenalter muss 1 bis 24 Stunden betragen")
    base = empty_forecast(
        "solcast_solar", source_id, start, end, max_age_seconds=max_age_hours * 3600
    )
    base = _freshness(base, fetched_at)
    if base.quality_reason is not None:
        return base
    if not isinstance(payload, Mapping):
        return replace(base, quality_reason="pv_invalid_response")
    if payload.get("last_update_success") is False:
        return replace(base, quality_reason="pv_update_failed", update_success=False)
    return _intervals(base, payload.get("data"), solcast=True)
