"""Bounded, opt-in asynchronous forecast archive; never controls the SAX device."""

from __future__ import annotations

import asyncio
import json
import logging
import types
from dataclasses import fields, is_dataclass, replace
from datetime import datetime, timedelta
from functools import lru_cache, partial
from typing import Any, Literal, TypeAliasType, get_args, get_origin, get_type_hints

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from ..const import DOMAIN
from ..domain.hems import EnergySlot, PvForecast
from ..domain.hems_evaluation import (
    EvaluationPair,
    ForecastBand,
    ForecastRecord,
    ForecastSeries,
    ForecastSeriesRecord,
    GateResult,
    Horizon,
    Phase,
    TimeSpan,
    archived_baselines,
    evaluate_gate,
    evaluate_records,
    evaluation_summary,
    finite,
    stable_id,
    union_spans,
    utc,
    validate_record,
)
from ..domain.hems_load import DischargeObservation
from ..domain.hems_uncertainty import (
    UncertaintyClass,
    UncertaintyModel,
    UncertaintyResult,
    assess_uncertainty,
    train_uncertainty,
)

_LOGGER = logging.getLogger(__name__)
_DETAIL_BYTES = 64 * 1024 * 1024
_PAIR_LIMIT = 50000
_TYPES = {
    cls.__name__: cls
    for cls in (
        EnergySlot,
        PvForecast,
        ForecastSeries,
        ForecastRecord,
        ForecastBand,
        EvaluationPair,
        TimeSpan,
        GateResult,
        UncertaintyClass,
        UncertaintyModel,
    )
}


def _encode(value: Any) -> Any:
    if isinstance(value, datetime):
        return {"datetime": utc(value).isoformat()}
    if is_dataclass(value):
        return {
            "type": type(value).__name__,
            "fields": {f.name: _encode(getattr(value, f.name)) for f in fields(value)},
        }
    if isinstance(value, tuple):
        return {"tuple": [_encode(item) for item in value]}
    if isinstance(value, dict):
        return {key: _encode(item) for key, item in value.items()}
    if value is None or isinstance(value, str | bool) or finite(value):
        return value
    raise ValueError("Unsupported or nonfinite archive data")


@lru_cache(maxsize=32)
def _hints(cls: type) -> dict[str, Any]:
    return get_type_hints(cls)


def _matches(value: Any, annotation: Any) -> bool:
    if isinstance(annotation, TypeAliasType):
        return _matches(value, annotation.__value__)
    origin, args = get_origin(annotation), get_args(annotation)
    if annotation is Any:
        return True
    if origin is types.UnionType:
        return any(_matches(value, arg) for arg in args)
    if origin is Literal:
        return value in args
    if origin is tuple:
        return isinstance(value, tuple) and (
            all(_matches(item, args[0]) for item in value)
            if len(args) == 2 and args[1] is Ellipsis
            else len(value) == len(args)
            and all(_matches(item, arg) for item, arg in zip(value, args, strict=True))
        )
    if annotation is float:
        return finite(value)
    if annotation is int:
        return type(value) is int
    return isinstance(value, annotation)


def _decode(value: Any, depth: int = 0) -> Any:
    if depth > 24:
        raise ValueError("Archive structure too deep")
    if not isinstance(value, dict):
        if value is None or isinstance(value, str | bool) or finite(value):
            return value
        raise ValueError("Invalid archive primitive")
    if set(value) == {"datetime"}:
        return utc(datetime.fromisoformat(value["datetime"]))
    if set(value) == {"tuple"} and isinstance(value["tuple"], list):
        return tuple(_decode(item, depth + 1) for item in value["tuple"])
    if set(value) == {"type", "fields"}:
        cls = _TYPES.get(value["type"])
        if cls is None or not isinstance(value["fields"], dict):
            raise ValueError("Unknown archive type")
        decoded = {
            key: _decode(item, depth + 1) for key, item in value["fields"].items()
        }
        hints = _hints(cls)
        if set(decoded) != set(hints) or not all(
            _matches(item, hints[key]) for key, item in decoded.items()
        ):
            raise ValueError("Archive field types do not match schema")
        return cls(**decoded)
    return {key: _decode(item, depth + 1) for key, item in value.items()}


def _valid_pair(pair: Any, as_of: datetime) -> bool:
    if not isinstance(pair, EvaluationPair) or not (
        pair.issued_at < pair.start < pair.end <= as_of
        and pair.pair_id
        and pair.record_id
        and pair.night_id
        and pair.baseline_key
        and pair.applied_key
        and pair.basis == "sax_discharge_ac"
    ):
        return False
    if any(
        not finite(value) or value < 0
        for value in (
            pair.baseline_kwh,
            pair.observed_kwh,
            *(() if pair.applied_kwh is None else (pair.applied_kwh,)),
            *(() if pair.candidate_kwh is None else (pair.candidate_kwh,)),
        )
    ):
        return False
    if union_spans(pair.valid_spans) != pair.valid_spans or any(
        not pair.start <= span.start < span.end <= pair.end for span in pair.valid_spans
    ):
        return False
    if any(
        not reason or not finite(seconds) or seconds < 0
        for reason, seconds in pair.excluded_seconds
    ):
        return False
    if pair.complete and (
        pair.valid_spans != (TimeSpan(pair.start, pair.end),) or pair.excluded_seconds
    ):
        return False
    return all(
        band.start == pair.start
        and band.end == pair.end
        and band.trained_until < pair.issued_at < band.start
        and finite(band.lower_kwh)
        and finite(band.upper_kwh)
        and 0 <= band.lower_kwh <= band.upper_kwh
        for band in pair.bands
    )


class _ArchiveStore(Store[dict[str, Any]]):
    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict[str, Any]
    ) -> dict[str, Any]:
        # No historic reconstruction is permitted. Future minor migrations may
        # add metadata but must retain the original issued series byte for byte.
        if old_major_version != 1:
            raise NotImplementedError
        return old_data


class HemsArchive:
    """Own per-entry evidence and immutable prospective model state.

    All serialization, target evaluation and pruning runs in HA's executor.
    Generation checks ensure disable/unload cannot publish an in-flight result.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        *,
        enabled: bool = False,
        max_detail_bytes: int = _DETAIL_BYTES,
        max_pairs: int = _PAIR_LIMIT,
    ) -> None:
        if (
            not 0 < max_detail_bytes <= _DETAIL_BYTES
            or not 0 < max_pairs <= _PAIR_LIMIT
        ):
            raise ValueError("Invalid archive limits")
        self.hass = hass
        self.enabled = enabled
        self._store = _ArchiveStore(hass, 1, f"{DOMAIN}.hems_archive.{entry_id}")
        self._max_detail_bytes, self._max_pairs = max_detail_bytes, max_pairs
        self._records: tuple[ForecastRecord, ...] = ()
        self._pairs: tuple[EvaluationPair, ...] = ()
        self._frozen: dict[str, datetime] = {}
        self._approvals: dict[str, GateResult] = {}
        self._models: dict[str, UncertaintyModel] = {}
        self._watermark: datetime | None = None
        self._enabled_at = dt_util.utcnow()
        self._lock = asyncio.Lock()
        self._generation = 0
        self._started = False
        self._stopped = False
        self._writable = True
        self._status = "collecting" if enabled else "disabled"
        self._pruned = 0
        self._detail_bytes = 0

    @property
    def pairs(self) -> tuple[EvaluationPair, ...]:
        return self._pairs

    @property
    def diagnostics(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "status": self._status,
            "records": len(self._records),
            "pairs": len(self._pairs),
            "detail_bytes": self._detail_bytes,
            "pruned": self._pruned,
            "oldest_issue": (
                self._records[0].issued_at.isoformat() if self._records else None
            ),
            "latest_issue": (
                self._records[-1].issued_at.isoformat() if self._records else None
            ),
            "basis": "sax_discharge_ac",
            "retention_days": 90,
            "pair_retention_days": 365,
            "max_detail_bytes": self._max_detail_bytes,
            "max_pairs": self._max_pairs,
        }

    @callback
    def configure(self, enabled: bool, as_of: datetime | None = None) -> None:
        if enabled == self.enabled:
            return
        self.enabled = enabled
        self._generation += 1
        self._status = (
            "load_failed"
            if not self._writable
            else "collecting" if enabled else "disabled"
        )
        if enabled:
            self._enabled_at = utc(as_of or dt_util.utcnow())
            self._watermark = self._enabled_at

    def archived_baselines(
        self, start: datetime, end: datetime, model_key: str
    ) -> tuple[ForecastSeriesRecord, ...]:
        if not self.enabled or self._stopped:
            return ()
        return archived_baselines(
            tuple(r for r in self._records if r.issued_at >= self._enabled_at),
            start,
            end,
            model_key,
        )

    async def async_start(self) -> None:
        if self._started or self._stopped:
            return
        generation = self._generation
        try:
            raw = await self._store.async_load()
            state = await self.hass.async_add_executor_job(
                self._restore, raw, dt_util.utcnow()
            )
        except Exception:
            _LOGGER.exception("HEMS-Prognosearchiv konnte nicht geladen werden")
            self._status = "load_failed"
            self._writable = False
            self._started = True
            return
        if generation == self._generation and not self._stopped:
            self._install(state)
            if self.enabled and state.get("collection_enabled"):
                self._enabled_at = state.get("collection_start", self._enabled_at)
            self._started = True

    def _restore(self, raw: dict | None, as_of: datetime) -> dict:
        if raw is None:
            return self._state()
        state = _decode(raw)
        if state.get("schema") != 1:
            raise ValueError("Unsupported forecast archive schema")
        if (
            not isinstance(state.get("records"), tuple)
            or not isinstance(state.get("pairs"), tuple)
            or not isinstance(state.get("approvals"), dict)
            or not isinstance(state.get("models"), dict)
            or not isinstance(state.get("frozen"), dict)
            or not isinstance(state.get("collection_start"), datetime)
            or state["collection_start"] > as_of
            or type(state.get("collection_enabled")) is not bool
            or type(state.get("pruned")) is not int
            or state["pruned"] < 0
            or state.get("watermark") is not None
            and (
                not isinstance(state["watermark"], datetime)
                or state["watermark"] > as_of
            )
        ):
            raise ValueError("Incomplete archive checkpoint")
        for record in state.get("records", ()):
            if not isinstance(record, ForecastRecord):
                raise ValueError("Invalid archived record")
            validate_record(record)
        if not all(_valid_pair(pair, as_of) for pair in state.get("pairs", ())):
            raise ValueError("Invalid archived pair chronology")
        if not all(
            isinstance(gate, GateResult)
            and gate.approved
            and gate.nights >= 14
            and gate.observed_hours >= 14 - 1e-9
            and gate.frozen_at < gate.evaluated_at <= as_of
            and key
            == stable_id(
                (gate.baseline_key, gate.candidate_key, gate.phase, gate.horizon)
            )
            and all(
                finite(value) and value >= 0
                for value in (
                    gate.baseline_mae_per_hour,
                    gate.candidate_mae_per_hour,
                    gate.baseline_p90_under_per_hour,
                    gate.candidate_p90_under_per_hour,
                )
            )
            and gate.baseline_mae_per_hour > 0
            and gate.candidate_mae_per_hour <= gate.baseline_mae_per_hour * 0.95
            and gate.candidate_p90_under_per_hour
            <= gate.baseline_p90_under_per_hour * 1.05
            for key, gate in state.get("approvals", {}).items()
        ):
            raise ValueError("Invalid retained approval")
        if not all(
            isinstance(model, UncertaintyModel)
            and model.training_nights >= 60
            and model.trained_until <= as_of
            and key == model.target_class.identifier
            and len(set(model.training_pair_ids)) == 60
            and model.lower_error_kwh <= model.upper_error_kwh
            for key, model in state.get("models", {}).items()
        ):
            raise ValueError("Invalid uncertainty model")
        if not all(
            isinstance(value, datetime) and value <= as_of
            for value in state.get("frozen", {}).values()
        ):
            raise ValueError("Invalid candidate chronology")
        return self._prune(state, as_of)

    def _state(self) -> dict:
        return {
            "schema": 1,
            "records": self._records,
            "pairs": self._pairs,
            "frozen": dict(self._frozen),
            "approvals": dict(self._approvals),
            "models": dict(self._models),
            "watermark": self._watermark,
            "pruned": self._pruned,
            "detail_bytes": self._detail_bytes,
            "collection_enabled": self.enabled,
            "collection_start": self._enabled_at,
        }

    def _install(self, state: dict) -> None:
        self._records, self._pairs = state["records"], state["pairs"]
        self._frozen, self._approvals = state["frozen"], state["approvals"]
        self._models, self._watermark = state["models"], state["watermark"]
        self._pruned, self._detail_bytes = state["pruned"], state["detail_bytes"]

    def _prune(self, state: dict, as_of: datetime) -> dict:
        records = [
            r
            for r in state["records"]
            if as_of - timedelta(days=90) <= r.issued_at <= as_of
        ]
        pairs = [
            p for p in state["pairs"] if as_of - timedelta(days=365) <= p.end <= as_of
        ]
        records.sort(key=lambda r: (r.issued_at, r.record_id))
        pairs.sort(key=lambda p: (p.end, p.pair_id))
        sizes = [len(json.dumps(_encode(r), allow_nan=False).encode()) for r in records]
        size = sum(sizes)
        drop = 0
        while size > self._max_detail_bytes and drop < len(sizes):
            size -= sizes[drop]
            drop += 1
        records = records[drop:]
        pairs = pairs[-self._max_pairs :]
        removed = (
            len(state["records"]) + len(state["pairs"]) - len(records) - len(pairs)
        )
        return {
            **state,
            "records": tuple(records),
            "pairs": tuple(pairs),
            "pruned": state["pruned"] + removed,
            "detail_bytes": size,
            "frozen": dict(list(state["frozen"].items())[-256:]),
            "approvals": dict(list(state["approvals"].items())[-256:]),
            "models": dict(list(state["models"].items())[-256:]),
        }

    async def _save(self) -> bool:
        if not self._writable:
            return False
        try:
            encoded = await self.hass.async_add_executor_job(_encode, self._state())
            await self._store.async_save(encoded)
            if self._status == "save_failed":
                self._status = "collecting" if self.enabled else "disabled"
            return True
        except Exception:
            _LOGGER.exception("HEMS-Prognosearchiv konnte nicht gespeichert werden")
            self._status = "save_failed"
            return False

    async def async_record(
        self,
        record: ForecastRecord,
        observations: tuple[DischargeObservation, ...] = (),
        as_of: datetime | None = None,
    ) -> bool:
        """Append, never replace; a failed write cannot mint a durable approval."""
        as_of = utc(as_of or record.issued_at)
        if (
            not self.enabled
            or self._stopped
            or not self._writable
            or record.issued_at < self._enabled_at
        ):
            return False
        if record.issued_at > as_of:
            raise ValueError("Cannot archive a future forecast")
        generation = self._generation
        async with self._lock:
            if not self.enabled or generation != self._generation:
                return False
            state = self._state()
            updated = await self.hass.async_add_executor_job(
                self._append, state, record, tuple(observations), as_of
            )
            if generation != self._generation or self._stopped:
                return False
            self._install(updated)
            return await self._save()

    def _append(
        self,
        state: dict,
        record: ForecastRecord,
        observations: tuple[DischargeObservation, ...],
        as_of: datetime,
    ) -> dict:
        validate_record(record)
        # Round-trip enforces immutable tuple fields even for untyped callers.
        record = _decode(_encode(record))
        records = {r.record_id: r for r in state["records"]}
        previous = records.get(record.record_id)
        if previous is not None and previous != record:
            raise ValueError("An issued forecast cannot be rewritten")
        records[record.record_id] = record
        all_records = tuple(records.values())
        eligible = tuple(
            r
            for r in all_records
            if r.issued_at >= self._enabled_at
            and (state["watermark"] is None or r.model_end > state["watermark"])
        )
        # The planning tick commonly precedes the last sample by a few seconds.
        # Finalizing through wall time would permanently censor that valid tail.
        observed_through = max(
            (
                utc(obs.end)
                for obs in observations
                if utc(obs.start) < utc(obs.end) <= as_of
            ),
            default=None,
        )
        watermark = state["watermark"]
        resolved = ()
        if observed_through is not None and (
            watermark is None or observed_through > watermark
        ):
            resolved = evaluate_records(
                eligible, observations, min(as_of, observed_through), watermark
            )
            watermark = min(as_of, observed_through)
        pairs = {p.pair_id: p for p in state["pairs"]}
        for pair in resolved:
            pairs.setdefault(pair.pair_id, pair)
        if record.candidate is not None:
            key = stable_id((record.baseline.model_key, record.candidate.model_key))
            state["frozen"].setdefault(key, record.issued_at)
        return self._prune(
            {
                **state,
                "records": all_records,
                "pairs": tuple(pairs.values()),
                "watermark": watermark,
            },
            as_of,
        )

    async def async_gate(
        self,
        baseline_key: str,
        candidate_key: str,
        phase: Phase,
        horizon: Horizon = "60m",
        as_of: datetime | None = None,
    ) -> GateResult:
        as_of = utc(as_of or dt_util.utcnow())
        key = stable_id((baseline_key, candidate_key, phase, horizon))
        frozen_key = stable_id((baseline_key, candidate_key))
        frozen = self._frozen.get(frozen_key, as_of)
        if not self.enabled or self._stopped or not self._writable:
            if key in self._approvals:
                return replace(
                    self._approvals[key],
                    reason="approved_monitoring_disabled",
                    retained=True,
                    evaluated_at=as_of,
                )
            return GateResult(
                False,
                "archive_disabled" if self._writable else "archive_load_failed",
                baseline_key,
                candidate_key,
                phase,
                horizon,
                frozen,
                as_of,
            )
        generation = self._generation
        async with self._lock:
            result = await self.hass.async_add_executor_job(
                partial(
                    evaluate_gate,
                    self._pairs,
                    baseline_key=baseline_key,
                    candidate_key=candidate_key,
                    phase=phase,
                    horizon=horizon,
                    frozen_at=frozen,
                    as_of=as_of,
                )
            )
            if generation != self._generation or self._stopped:
                return replace(result, approved=False, reason="archive_changed")
            if result.approved:
                previous = self._approvals.get(key)
                if (
                    previous is not None
                    and replace(result, evaluated_at=previous.evaluated_at) == previous
                ):
                    return result
                self._approvals[key] = result
                if not await self._save():
                    self._approvals.pop(key, None)
                    return replace(result, approved=False, reason="archive_save_failed")
                if generation != self._generation or self._stopped:
                    self._approvals.pop(key, None)
                    await self._save()
                    return replace(result, approved=False, reason="archive_changed")
            else:
                if self._approvals.pop(key, None) is not None:
                    await self._save()
            return result

    async def async_uncertainty(
        self,
        target_class: UncertaintyClass,
        *,
        expected_kwh: float | None,
        start: datetime,
        end: datetime,
        as_of: datetime,
    ) -> UncertaintyResult:
        if not self.enabled or self._stopped or not self._writable:
            return UncertaintyResult(
                "unavailable", "archive_disabled", expected_kwh, start=start, end=end
            )
        generation = self._generation
        async with self._lock:
            key = target_class.identifier
            model = self._models.get(key)
            if model is None:
                model = await self.hass.async_add_executor_job(
                    train_uncertainty, self._pairs, target_class, as_of
                )
                if generation != self._generation or self._stopped:
                    return UncertaintyResult(
                        "unavailable", "archive_changed", expected_kwh
                    )
                if model is not None:
                    self._models[key] = model
                    if not await self._save():
                        self._models.pop(key, None)
                        return UncertaintyResult(
                            "unavailable", "archive_save_failed", expected_kwh
                        )
            result = await self.hass.async_add_executor_job(
                partial(
                    assess_uncertainty,
                    model,
                    self._pairs,
                    target_class,
                    expected_kwh=expected_kwh,
                    start=start,
                    end=end,
                    as_of=as_of,
                )
            )
            if generation != self._generation or self._stopped:
                return UncertaintyResult("unavailable", "archive_changed", expected_kwh)
            return result

    async def async_export(self, *, offset: int = 0, limit: int = 100) -> dict:
        """Page detail/compact records without exposing large sensor attributes."""
        if (
            type(offset) is not int
            or offset < 0
            or type(limit) is not int
            or not 1 <= limit <= 1000
        ):
            raise ValueError("Export requires a nonnegative offset and limit 1..1000")
        async with self._lock:
            generation = self._generation
            state = await self.hass.async_add_executor_job(
                self._prune, self._state(), dt_util.utcnow()
            )
            if generation != self._generation:
                return {
                    "schema": 1,
                    "offset": offset,
                    "total": 0,
                    "items": [],
                    "next_offset": None,
                }
            if not self._stopped:
                self._install(state)
            return await self.hass.async_add_executor_job(
                self._export_page, state, offset, limit
            )

    @staticmethod
    def _export_page(state: dict, offset: int, limit: int) -> dict:
        values = (*state["records"], *state["pairs"])
        items, size = [], 0
        for value in values[offset : offset + limit]:
            encoded = _encode(value)
            item_size = len(json.dumps(encoded).encode())
            if items and size + item_size > 2 * 1024 * 1024:
                break
            items.append(encoded)
            size += item_size
        next_offset = offset + len(items)
        return {
            "schema": 1,
            "offset": offset,
            "total": len(values),
            "items": items,
            "next_offset": next_offset if next_offset < len(values) else None,
        }

    async def async_summary(
        self, model_key: str, *, horizon: Horizon = "60m", phase: Phase = "night"
    ) -> dict[str, Any]:
        """Expose selected-class MAE/bias and observed/excluded duration compactly."""
        pairs = tuple(
            p for p in self._pairs if p.horizon == horizon and p.phase == phase
        )
        summary = await self.hass.async_add_executor_job(
            evaluation_summary, pairs, model_key
        )
        return {**summary, "horizon": horizon, "phase": phase}

    async def async_delete(self) -> None:
        self._generation += 1
        async with self._lock:
            self._records, self._pairs = (), ()
            self._frozen, self._approvals, self._models = {}, {}, {}
            self._watermark = self._enabled_at = dt_util.utcnow()
            self._detail_bytes, self._pruned = 0, 0
            await self._store.async_remove()
            self._writable = True
            self._status = "collecting" if self.enabled else "disabled"

    async def async_stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        self._generation += 1
        async with self._lock:
            state = await self.hass.async_add_executor_job(
                self._prune, self._state(), dt_util.utcnow()
            )
            self._install(state)
            if self._started:
                await self._save()
