"""REQ-HEMS-RUNTIME: one cancellable source reader, one leased device decision.

All acknowledged device operations remain in SaxPowerCoordinator. This service
publishes intent and enforces its quantitative limits in the coordinator's tick.
"""

from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import monotonic
from typing import TYPE_CHECKING, Any

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from ..const import (
    CONF_HEMS_CHARGE_EFFICIENCY,
    CONF_HEMS_DISCHARGE_EFFICIENCY,
    CONF_HEMS_PV_ENTRY,
    CONF_HEMS_PV_PROVIDER,
    CONF_HEMS_SOLCAST_MAX_AGE,
    CONF_HEMS_SOLCAST_TIMESTAMP,
    CONF_HEMS_SOLCAST_TIMESTAMP_REGISTRY_ID,
    PRICE_STATUS_CHARGING,
    PRICE_STATUS_WAITING,
    PRICE_STRATEGY_ADAPTIVE,
)
from ..domain.hems import (
    ChargeInterval,
    EnergyPlan,
    LoadForecast,
    PlanningSnapshot,
    PlanStatus,
    PvForecast,
    TariffConstraints,
)
from ..domain.hems_planner import compute_energy_plan
from ..domain.hems_progress import SocProgressLedger
from ..infrastructure.hems_history import HemsHistory
from ..infrastructure.hems_pv import HemsPvAdapter
from .hems_prediction import HemsPrediction
from .hems_tariffs import timed_constraints

if TYPE_CHECKING:
    from ..coordinator import SaxPowerCoordinator
    from ..price_optimizer import PricePlan, PriceSlot

_LOGGER = logging.getLogger(__name__)
EVALUATION_SECONDS = 300
MIN_START_ENERGY_KWH = 0.05


def finite(value: object) -> float | None:
    """Do not turn unavailable safety or measurement inputs into zero."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if math.isfinite(value) else None


@dataclass(frozen=True, slots=True)
class HemsExecution:
    charge: bool = False
    target_soc: float | None = None
    pause: bool = False
    reason: str = "inactive"
    fallback: bool = False
    calibration: bool = False


class HemsRuntime:
    """One entry's opt-in night controller and bounded quality history."""

    def __init__(self, coordinator: SaxPowerCoordinator) -> None:
        self.coordinator = coordinator
        self.hass = coordinator.hass
        self.history = HemsHistory(self.hass, coordinator.entry_id)
        self.prediction = HemsPrediction(self.hass, coordinator.entry_id)
        self.plan: EnergyPlan | None = None
        self.load = LoadForecast()
        self.pv = PvForecast()
        self.constraints = TariffConstraints()
        self.next_evaluation_at: datetime | None = None
        self._remove_timer: Any = None
        self._task: asyncio.Task[None] | None = None
        self._dirty = False
        self._revision = 0
        self._started = False
        self._shutdown = False
        self._adapter: HemsPvAdapter | None = None
        self._context = ""
        self._fallback_armed = False
        self._fallback_active = False
        self._calibration_proof = False
        self._execution_limit_kwh: float | None = None
        self._execution_delivered_kwh = 0.0
        self._execution_deadline: datetime | None = None
        self._execution_target: float | None = None
        self._execution_store: Store[dict[str, Any]] = Store(
            self.hass, 1, f"sax_power.hems_execution.{coordinator.entry_id}"
        )
        self._execution_store_loaded = False
        self._execution_save_scheduled = False
        self._execution = HemsExecution()
        self._execution_intervals: tuple[ChargeInterval, ...] = ()
        self._delivered_kwh = 0.0
        self._measured_grid_kwh = 0.0
        self.progress = SocProgressLedger()
        self._pending_progress: object = None
        self._sample_revision = -1
        self._sample: tuple[float, float] | None = None
        self._last_configuration: object = None
        self._expired_requested_id: str | None = None
        self.execution_constraint: str | None = None
        self._remove_source_listener: Any = None

    @property
    def mode(self) -> str | None:
        c = self.coordinator
        if (
            c.price_charge_enabled
            and c.price_charge_strategy == PRICE_STRATEGY_ADAPTIVE
        ):
            return "dynamic"
        if c.timed_charge_enabled and c.timed_charge_mode == "adaptive":
            return "timed"
        return None

    async def async_start(self) -> None:
        if self._started or self._shutdown:
            return
        self.prediction.configure(self.coordinator.options, dt_util.utcnow())
        self.history.configure(history_days=self.prediction.history_days)
        await self.prediction.async_start()
        await self.history.async_start()
        try:
            raw = await self._execution_store.async_load()
            if isinstance(raw, dict) and isinstance(raw.get("context"), str):
                self._pending_progress = raw.get("progress")
                limit = finite(raw.get("limit_kwh"))
                delivered = finite(raw.get("delivered_kwh"))
                target = finite(raw.get("target_soc"))
                armed = raw.get("fallback_armed") is True
                calibration = raw.get("calibration_proof") is True
                deadline = raw.get("deadline")
                parsed = None
                if isinstance(deadline, str):
                    parsed = datetime.fromisoformat(deadline)
                    if parsed.tzinfo is None:
                        raise ValueError("Naive execution deadline")
                    parsed = parsed.astimezone(UTC)
                if (
                    delivered is None
                    or delivered < 0
                    or (limit is not None and limit < 0)
                    or (target is not None and not 0 <= target <= 100)
                    or ((armed or calibration) and None in (limit, target, parsed))
                ):
                    raise ValueError("Invalid execution evidence")
                # Validate the entire checkpoint before restoring any permission.
                self._context = raw["context"]
                self._fallback_armed = armed
                self._calibration_proof = calibration
                self._execution_limit_kwh = limit
                self._execution_delivered_kwh = delivered
                self._execution_target = target
                self._execution_deadline = parsed
        except HomeAssistantError, OSError, ValueError, NotImplementedError:
            _LOGGER.warning("HEMS-Vollzugsnachweis nicht lesbar; keine alte Freigabe")
        self._execution_store_loaded = True
        self._started = True
        self._remove_source_listener = self.hass.bus.async_listen(
            "state_changed", self._source_event
        )

    @callback
    def _source_event(self, event: Any) -> None:
        entity = er.async_get(self.hass).async_get(event.data.get("entity_id", ""))
        if (
            entity is not None
            and entity.config_entry_id
            == self.coordinator.options.get(CONF_HEMS_PV_ENTRY)
        ):
            self.source_changed()

    @callback
    def source_changed(self) -> None:
        if self.mode is None or self._shutdown:
            return
        self._revision += 1
        self.plan = None
        self.prediction.uncertainty = None
        if self._adapter is not None:
            self._adapter.invalidate()
        self.request_evaluation()

    @callback
    def configuration_changed(self) -> None:
        """Invalidate synchronously, before any asynchronous device acknowledgement."""
        configuration = (
            self.coordinator.control_config(),
            dict(self.coordinator.options),
        )
        if configuration == self._last_configuration and (
            self._remove_timer is not None or self.mode is None
        ):
            return
        self._last_configuration = configuration
        self.prediction.configure(self.coordinator.options, dt_util.utcnow())
        self.history.configure(history_days=self.prediction.history_days)
        self._revision += 1
        self.plan = None
        self._execution_intervals = ()
        self._sample = None
        if self._adapter is not None:
            self._adapter.invalidate()
        if (
            not self._started
            or self._shutdown
            or self.coordinator.control_bootstrap_pending
        ):
            return
        if self.mode is None:
            self._cancel_timer()
            self._set_context("")
            self._execution = HemsExecution()
        else:
            if self._remove_timer is None:
                self._schedule()
            self.request_evaluation()

    def _cancel_timer(self) -> None:
        if self._remove_timer is not None:
            self._remove_timer()
        self._remove_timer = None
        self.next_evaluation_at = None

    def _schedule(self) -> None:
        self._cancel_timer()
        self.next_evaluation_at = dt_util.utcnow() + timedelta(
            seconds=EVALUATION_SECONDS
        )
        self._remove_timer = async_track_point_in_utc_time(
            self.hass, self._tick, self.next_evaluation_at
        )

    @callback
    def _tick(self, _now: datetime) -> None:
        if self._shutdown or self.mode is None:
            self._cancel_timer()
            return
        self._schedule()
        self.request_evaluation()

    @callback
    def request_evaluation(self) -> None:
        if not self._started or self._shutdown or self.mode is None:
            return
        self._dirty = True
        if self._task is None or self._task.done():
            # Register ownership before a fully synchronous evaluation can finish.
            self._task = self.hass.async_create_task(
                self._run(), "sax_power_hems", eager_start=False
            )

    async def _run(self) -> None:
        try:
            while self._dirty and not self._shutdown and self.mode is not None:
                self._dirty = False
                revision = self._revision
                try:
                    await self._evaluate(revision)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    # Provider errors must not permanently disable the periodic tick.
                    _LOGGER.exception("HEMS-Auswertung fehlgeschlagen")
                    if revision == self._revision:
                        self.plan = None
                        self._execution = HemsExecution(reason="evaluation_failed")
        finally:
            self._task = None

    def _current(self, revision: int) -> bool:
        return (
            revision == self._revision
            and not self._shutdown
            and not self.coordinator._shutdown_started
            and self.mode is not None
        )

    def _tariff(self, now: datetime) -> TariffConstraints:
        c = self.coordinator
        if self.mode == "dynamic":
            return c.price_planner.adaptive_constraints(now, self._prices(now))
        hold = c._timed_discharge_state
        return timed_constraints(
            now,
            start=c._timed_charge_start,
            end=c._timed_charge_end,
            months=c._timed_charge_months,
            time_zone=dt_util.get_time_zone(self.hass.config.time_zone) or UTC,
            hold_until=hold.expires_at if hold is not None else None,
            completed_until=c._timed_discharge_last_window_end,
        )

    def _prices(self, now: datetime) -> list[PriceSlot]:
        from ..price_optimizer import parse_price_slots

        planner = self.coordinator.price_planner
        return parse_price_slots(
            (
                self.hass.states.get(planner.price_entity_id)
                if planner.price_entity_id
                else None
            ),
            attribute=planner.price_attribute,
            unit=planner.price_unit,
            now=now,
            strict=True,
        )

    async def _evaluate(self, revision: int) -> None:
        as_of = dt_util.utcnow()
        load = await self.history.async_refresh(as_of)
        if not self._current(revision):
            return
        options = self.coordinator.options
        provider = options.get(CONF_HEMS_PV_PROVIDER, "none")
        entry = options.get(CONF_HEMS_PV_ENTRY)
        pv = PvForecast(quality_reason="pv_provider_not_configured")
        if provider in ("pv_forecast", "solcast_solar") and entry:
            self._adapter = HemsPvAdapter(
                self.hass,
                provider,
                entry,
                solcast_timestamp_entity_id=options.get(CONF_HEMS_SOLCAST_TIMESTAMP),
                solcast_timestamp_registry_id=options.get(
                    CONF_HEMS_SOLCAST_TIMESTAMP_REGISTRY_ID
                ),
                solcast_max_age_hours=options.get(CONF_HEMS_SOLCAST_MAX_AGE, 24),
            )
            pv = await self._adapter.async_read(as_of, end=load.model_end)
            if not self._current(revision):
                return
        c = self.coordinator
        data = c.data or {}
        now = dt_util.utcnow()
        try:
            load = await self.prediction.async_prepare(
                self.history,
                load,
                as_of=now,
                max_discharge_power_w=finite(data.get("ic_max_power_reference")),
                free_discharge=(
                    self.history.free_discharge(now) is True
                    and not c._basic_read_failed
                    and c.extended_available
                    and data.get("ic_control_mode") == 0
                    and not (
                        c._timed_charge_active
                        or c._price_charge_active
                        or c.grid_charge_active
                    )
                ),
            )
        except Exception:
            self.prediction.restore_baseline(load)
            _LOGGER.exception(
                "HEMS-Prognoseprüfung fehlgeschlagen; bisheriges Profil bleibt aktiv"
            )
        if not self._current(revision):
            return
        now = dt_util.utcnow()
        data = c.data or {}
        constraints = self._tariff(now)
        soc = finite(data.get("soc"))
        capacity = finite(data.get("battery_capacity"))
        capacity = capacity / 1000 if capacity is not None else None
        eta_c = options.get(CONF_HEMS_CHARGE_EFFICIENCY, 0.95)
        self._configure_progress(data, now)
        soc = self.progress.estimate(as_of=now, raw_soc=soc).effective_soc
        age = (
            (monotonic() - c._basic_last_read)
            if c._basic_last_read is not None
            else None
        )
        snapshot = PlanningSnapshot(
            as_of=now,
            revision=str(revision),
            load=load,
            pv=pv,
            tariff=constraints,
            current_soc=soc,
            soc_measured_at=(
                now - timedelta(seconds=max(0, age)) if age is not None else None
            ),
            capacity_kwh=capacity,
            charge_power_w=finite(data.get("ic_max_power_reference")),
            # The current BMS availability can be zero while empty; it is not
            # the technical discharge limit after the planned grid charge.
            discharge_power_w=finite(data.get("ic_max_power_reference")),
            reserve_soc=(
                c.timed_charge_min_soc
                if c.timed_charge_min_soc is not None
                else math.nan
            ),
            max_soc=min(
                c.timed_charge_max_soc, c.max_soc if c.max_soc is not None else 100
            ),
            physical_min_soc=finite(data.get("battery_soc_min")) or 0,
            eta_charge=eta_c,
            eta_discharge=options.get(CONF_HEMS_DISCHARGE_EFFICIENCY, 0.95),
            device_available=(
                not c._basic_read_failed
                and c.extended_available
                and finite(data.get("battery_soc_min")) is not None
            ),
            max_soc_age_seconds=max(30, c.update_interval.total_seconds() * 2),
        )
        measured_at_snapshot = self._measured_grid_kwh
        plan = await self.hass.async_add_executor_job(compute_energy_plan, snapshot)
        if not self._current(revision):
            return
        issued_at = dt_util.utcnow()
        self.load, self.pv, self.constraints = load, pv, constraints
        if self._fallback_armed and plan.status is not PlanStatus.FALLBACK:
            self._fallback_armed = False
            self._persist()
        self._fallback_active = plan.status is PlanStatus.FALLBACK
        self.plan = plan
        self._delivered_kwh = max(0, self._measured_grid_kwh - measured_at_snapshot)
        self._execution_intervals = plan.intervals
        self.execution(now, data)
        if self.mode == "dynamic":
            c.price_planner.adaptive_allocate(now, self._execution_intervals)
            c.price_planner.evaluate()
        c._publish_charge_state(data)
        c.async_update_listeners()
        # This await can execute a Modbus ACK sequence; shutdown drains it.
        await c.async_apply_price_plan()
        if self._current(revision):
            try:
                await self.prediction.async_record(snapshot, plan, issued_at=issued_at)
            except Exception:
                # Optionale Prognosebeobachtung darf die Gerätesicherheit nicht umgehen.
                _LOGGER.exception(
                    "HEMS-Prognosearchiv konnte die Ausgabe nicht übernehmen"
                )
        if self._current(revision):
            c._publish_charge_state(c.data or {})
            c.async_update_listeners()

    def _set_context(self, context: str) -> None:
        if context == self._context:
            return
        self._context = context
        self._fallback_armed = False
        self._calibration_proof = False
        self._execution_limit_kwh = None
        self._execution_delivered_kwh = 0
        self._execution_deadline = None
        self._execution_target = None
        self._persist()

    def _persist(self) -> None:
        if self._execution_store_loaded and not self._execution_save_scheduled:
            self._execution_save_scheduled = True
            try:
                self._execution_store.async_delay_save(self._consume_persisted, 5)
            except HomeAssistantError, OSError, ValueError:
                self._execution_save_scheduled = False
                _LOGGER.exception(
                    "HEMS-Vollzugsnachweis konnte nicht vorgemerkt werden"
                )

    def _consume_persisted(self) -> dict[str, Any]:
        self._execution_save_scheduled = False
        return self._persisted()

    def _persisted(self) -> dict[str, Any]:
        return {
            "progress": self.progress.dump(),
            "context": self._context,
            "fallback_armed": self._fallback_armed,
            "calibration_proof": self._calibration_proof,
            "limit_kwh": self._execution_limit_kwh,
            "delivered_kwh": self._execution_delivered_kwh,
            "target_soc": self._execution_target,
            "deadline": (
                self._execution_deadline.isoformat()
                if self._execution_deadline
                else None
            ),
        }

    def execution(self, now: datetime, data: dict[str, Any]) -> HemsExecution:
        """Called in the fast control path; a lease never replaces live safety."""
        now = now.astimezone(UTC)
        plan = self.plan
        result = HemsExecution(
            reason="awaiting_evaluation" if self.mode else "inactive"
        )
        scope = self.load.model_start, self.load.model_end
        outside_scope = (
            scope[0] is not None
            and scope[1] is not None
            and not scope[0] <= now < scope[1]
        )
        if outside_scope and (self._calibration_proof or self._fallback_armed):
            # A new night requires a new positive trigger, even after a stale lease.
            self._calibration_proof = self._fallback_armed = False
            self._persist()
        if self.mode is None or plan is None or now >= plan.valid_until:
            if (
                self.mode is not None
                and plan is not None
                and now >= plan.valid_until
                and self._expired_requested_id != plan.decision_id
            ):
                # REQ-HEMS-RUNTIME: short windows must not wait for the regular tick.
                self._expired_requested_id = plan.decision_id
                self.request_evaluation()
            self._execution = result
            return result
        if scope[0] is None or scope[1] is None or not scope[0] <= now < scope[1]:
            self._execution = HemsExecution(reason="outside_model_scope")
            return self._execution
        c = self.coordinator
        if (
            c._basic_last_read is None
            or not 0
            <= monotonic() - c._basic_last_read
            <= max(30, c.update_interval.total_seconds() * 2)
        ):
            self._execution = HemsExecution(reason="soc_stale")
            return self._execution
        tariff = self._tariff(now)
        window = next((w for w in tariff.cheap_windows if w.start <= now < w.end), None)
        context = (
            f"{self.mode}:{window.end.isoformat()}:{scope[0].isoformat()}:"
            f"{c._timed_charge_start}:{c._timed_charge_end}"
            if window
            else ""
        )
        self._set_context(context)
        soc = finite(data.get("soc"))
        eligible = next(
            (w for w in tariff.charge_windows if w.start <= now < w.end), None
        )
        seconds = tariff.max_charge_seconds
        allowed = eligible is not None and (seconds is None or seconds > 0)
        if soc is None or c._basic_read_failed or not c.extended_available:
            self._execution = HemsExecution(reason="device_unavailable")
            return self._execution
        capacity = finite(data.get("battery_capacity"))
        power = finite(data.get("ic_max_power_reference"))
        minimum = finite(data.get("battery_soc_min"))
        if (
            not 0 <= soc <= 100
            or capacity is None
            or capacity <= 0
            or power is None
            or power <= 0
            or minimum is None
            or not 0 <= minimum <= 100
            or c.timed_charge_min_soc is None
            or max(minimum, c.timed_charge_min_soc or 0)
            > min(c.timed_charge_max_soc, c.max_soc if c.max_soc is not None else 100)
        ):
            self._execution = HemsExecution(reason="invalid_device_data")
            return self._execution
        fallback = plan.status is PlanStatus.FALLBACK
        if self._fallback_armed and not fallback:
            self._fallback_armed = False
            self._persist()
        self._fallback_active = fallback
        target = plan.target_soc
        if fallback:
            target = min(
                c.timed_charge_max_soc, c.max_soc if c.max_soc is not None else 100
            )
            minimum = c.timed_charge_min_soc
            if (
                allowed
                and minimum is not None
                and soc < minimum
                and not self._fallback_armed
            ):
                self._fallback_armed = True
                self._persist()
            if soc >= target and self._fallback_armed:
                self._fallback_armed = False
                self._persist()
            positive = self._fallback_armed
        else:
            positive = any(i.start <= now < i.end for i in plan.intervals)
            if (
                plan.planned_grid_kwh is not None
                and self._delivered_kwh >= plan.planned_grid_kwh
            ):
                positive = False
        below_start_threshold = (
            not fallback
            and positive
            and plan.planned_grid_kwh is not None
            and plan.planned_grid_kwh < MIN_START_ENERGY_KWH
            and soc > max(minimum, c.timed_charge_min_soc)
            and not (c._timed_charge_active or c._price_charge_active)
        )
        if below_start_threshold:
            positive = False
        calibration = c.cell_calibration_active and (
            positive or self._calibration_proof
        )
        if calibration:
            target = 100
            positive = True
        charge = bool(
            allowed
            and positive
            and target is not None
            and soc < target
            and plan.status not in (PlanStatus.BLOCKED, PlanStatus.INACTIVE)
        )
        if (fallback or calibration) and charge:
            assert eligible is not None and target is not None
            capacity = finite(data.get("battery_capacity"))
            power = finite(data.get("ic_max_power_reference"))
            eta = finite(c.options.get(CONF_HEMS_CHARGE_EFFICIENCY, 0.95))
            if capacity and power and power > 0 and eta and 0 < eta <= 1:
                energy = max(0, capacity / 1000 * (target - soc) / 100 / eta)
                if (
                    self._execution_target != target
                    or self._execution_limit_kwh is None
                ):
                    self._execution_target = target
                    self._execution_limit_kwh = self._execution_delivered_kwh + energy
                    self._execution_deadline = now + timedelta(
                        seconds=energy / power * 3_600_000
                    )
                    self._persist()
                energy = min(
                    energy,
                    max(0, self._execution_limit_kwh - self._execution_delivered_kwh),
                )
                duration = min(
                    (eligible.end - now).total_seconds(),
                    energy / power * 3_600_000,
                    seconds if seconds is not None else float("inf"),
                    (
                        max(0, (self._execution_deadline - now).total_seconds())
                        if self._execution_deadline
                        else 0
                    ),
                )
                charge = duration > 0
                self._execution_intervals = (
                    ChargeInterval(
                        now,
                        now + timedelta(seconds=duration),
                        duration * power / 3_600_000,
                        eligible.price_eur_kwh,
                    ),
                )
            else:
                charge = False
        if self.mode == "dynamic":
            from ..price_optimizer import current_price

            price = current_price(self._prices(now), now)
            cap, neutral = c.price_charge_max_price, c.price_charge_neutral_price
            pause = (
                not charge
                and price is not None
                and cap is not None
                and neutral is not None
                and cap < neutral
                and price < neutral
            )
        else:
            pause = False
        self._execution = HemsExecution(
            charge=charge,
            target_soc=target,
            pause=pause,
            fallback=fallback,
            calibration=calibration and charge,
            reason=(
                "calibration"
                if calibration and charge
                else (
                    "below_start_threshold"
                    if below_start_threshold
                    else plan.reason_codes[0] if plan.reason_codes else str(plan.status)
                )
            ),
        )
        if self.mode == "dynamic":
            c.price_planner.adaptive_allocate(now, self._execution_intervals)
        return self._execution

    def acknowledged(self, charging: bool) -> None:
        if charging and self._execution.calibration and not self._calibration_proof:
            self._calibration_proof = True
            self._persist()

    def _configure_progress(self, data: dict[str, Any], now: datetime) -> None:
        capacity = finite(data.get("battery_capacity"))
        configured = self.progress.configure(
            capacity_kwh=capacity / 1000 if capacity is not None else None,
            eta_charge=self.coordinator.options.get(CONF_HEMS_CHARGE_EFFICIENCY, 0.95),
            eta_discharge=self.coordinator.options.get(
                CONF_HEMS_DISCHARGE_EFFICIENCY, 0.95
            ),
        )
        if (
            configured
            and self._pending_progress is not None
            and finite(data.get("soc")) is not None
            and not self.coordinator._basic_read_failed
            and self.coordinator.extended_available
        ):
            self.progress.restore(
                self._pending_progress,
                as_of=now,
                raw_soc=data["soc"],
                max_discharge_power_w=data.get("ic_max_power_reference"),
            )
            self._pending_progress = None

    def observe(self, data: dict[str, Any]) -> None:
        """Fresh samples train history and measure only battery grid energy."""
        c = self.coordinator
        if (
            self._sample_revision == c._high_sample_revision
            or c.control_bootstrap_pending
        ):
            return
        self._sample_revision = c._high_sample_revision
        now = dt_util.utcnow()
        self._configure_progress(data, now)
        self.progress.observe(
            at=now,
            raw_soc=data.get("soc"),
            storage_power_w=(
                data.get("storage_power_active")
                if not c._basic_read_failed and c.extended_available
                else None
            ),
        )
        if self.mode is not None:
            self._persist()
        self.history.observe(
            now,
            storage_power_w=data.get("storage_power_active"),
            soc=data.get("soc"),
            device_min_soc=data.get("battery_soc_min"),
            device_available=not c._basic_read_failed and c.extended_available,
            control_known=(
                data.get("ic_control_mode") in (0, 1)
                and finite(data.get("battery_discharge_power_available")) is not None
            ),
            charge_active=c._timed_charge_active
            or c._price_charge_active
            or c.grid_charge_active,
            discharge_blocked=(
                data.get("ic_control_mode") == 1
                or (
                    finite(data.get("battery_discharge_power_available")) is not None
                    and data["battery_discharge_power_available"] <= 0
                )
            ),
            calibration_active=(
                c.cell_calibration_active
                and (
                    c._timed_charge_active
                    or c._price_charge_active
                    or c.grid_charge_active
                )
            ),
            energy_discharged_kwh=c._energy_discharged_kwh,
            max_discharge_power_w=data.get("ic_max_power_reference"),
        )
        power, grid = finite(data.get("storage_power_active")), finite(
            data.get("smartmeter_power")
        )
        at = c._high_sample_time
        if power is None or grid is None or at is None or not self._execution.charge:
            self._sample = None
            return
        grid_charge = min(max(0, -power), max(0, grid))
        if self._sample is not None:
            previous, watts = self._sample
            seconds = at - previous
            if 0 < seconds <= 30:
                energy = watts * seconds / 3_600_000
                self._delivered_kwh += energy
                self._measured_grid_kwh += energy
                self._execution_delivered_kwh += energy
                if energy > 0:
                    self._persist()
        self._sample = (at, grid_charge)

    def price_plan(self, now: datetime, slots: list[PriceSlot]) -> PricePlan:
        from ..price_optimizer import PricePlan, PriceSlot, current_price

        result = self.execution(now, self.coordinator.data or {})
        selected = tuple(
            PriceSlot(i.start, i.end, i.price_eur_kwh or 0)
            for i in self._execution_intervals
        )
        return PricePlan(
            status=PRICE_STATUS_CHARGING if result.charge else PRICE_STATUS_WAITING,
            charge_now=result.charge,
            current_price=current_price(slots, now),
            threshold=self.coordinator.price_charge_max_price,
            next_start=next((slot.start for slot in selected if slot.end > now), None),
            slots=selected,
        )

    @property
    def attributes(self) -> dict[str, Any]:
        plan = self.plan
        return {
            "forecast_quality": self.prediction.attributes,
            "mode": self.mode,
            "status": str(plan.status) if plan else self._execution.reason,
            "reason_codes": (
                list(plan.reason_codes) if plan else [self._execution.reason]
            ),
            "execution_reason": self._execution.reason,
            "execution_constraint": self.execution_constraint,
            "fallback": self._execution.fallback,
            "decision_id": plan.decision_id if plan else None,
            "evaluated_at": plan.evaluated_at.isoformat() if plan else None,
            "next_evaluation_at": (
                self.next_evaluation_at.isoformat() if self.next_evaluation_at else None
            ),
            "valid_until": plan.valid_until.isoformat() if plan else None,
            "pv_supply_at": (
                plan.pv_supply_at.isoformat() if plan and plan.pv_supply_at else None
            ),
            "required_grid_kwh": plan.required_grid_kwh if plan else None,
            "remaining_grid_kwh": (
                max(0, (plan.planned_grid_kwh or 0) - self._delivered_kwh)
                if plan and plan.planned_grid_kwh is not None
                else None
            ),
            "unmet_grid_kwh": plan.unmet_grid_kwh if plan else None,
            "target_soc": plan.target_soc if plan else None,
            "execution_target_soc": self._execution.target_soc,
            "calibration": self._execution.calibration,
            "available_battery_kwh": plan.available_battery_kwh if plan else None,
            "reserve_kwh": plan.reserve_kwh if plan else None,
            "expected_load_kwh": plan.expected_load_kwh if plan else None,
            "pv_used_kwh": plan.pv_used_kwh if plan else None,
            "planned_start": (
                plan.next_start.isoformat() if plan and plan.next_start else None
            ),
            "planned_end": (
                plan.next_end.isoformat() if plan and plan.next_end else None
            ),
            "load_basis": self.load.basis,
            "load_coverage": self.load.coverage,
            "load_model_start": (
                self.load.model_start.isoformat() if self.load.model_start else None
            ),
            "load_model_end": (
                self.load.model_end.isoformat() if self.load.model_end else None
            ),
            "nights_count": self.load.nights_count,
            "observed_hours": round(self.load.observed_hours, 2),
            "load_quality": self.load.quality_reason,
            "load_quality_flags": list(self.load.quality_flags),
            "pv_provider": self.pv.provider,
            "pv_source_id": self.pv.source_id,
            "pv_quality_flags": list(self.pv.quality_flags),
            "pv_coverage_complete": self.pv.coverage_complete,
            "pv_coverage_start": (
                self.pv.intervals[0].start.isoformat() if self.pv.intervals else None
            ),
            "pv_coverage_end": (
                self.pv.intervals[-1].end.isoformat() if self.pv.intervals else None
            ),
            "pv_max_age_seconds": self.pv.max_age_seconds,
            "pv_freshness_policy": self.pv.freshness_policy,
            "pv_update_success": self.pv.update_success,
            "reserve_soc": self.coordinator.timed_charge_min_soc,
            "execution_charging": bool(
                (self.mode == "timed" and self.coordinator._timed_charge_active)
                or (self.mode == "dynamic" and self.coordinator._price_charge_active)
            ),
            "planned_pause": self._execution.pause,
            "calibration_extra_kwh": (
                max(
                    0,
                    self._execution_limit_kwh
                    - self._execution_delivered_kwh
                    - max(0, (plan.planned_grid_kwh or 0) - self._delivered_kwh),
                )
                if self._execution.calibration
                and self._execution_limit_kwh is not None
                and plan
                and plan.planned_grid_kwh is not None
                else None
            ),
            "execution_remaining_kwh": (
                max(0, self._execution_limit_kwh - self._execution_delivered_kwh)
                if self._execution_limit_kwh is not None
                else None
            ),
            "execution_deadline": (
                self._execution_deadline.isoformat()
                if self._execution_deadline
                else None
            ),
            "pv_quality": self.pv.quality_reason,
            "pv_fetched_at": (
                self.pv.fetched_at.isoformat() if self.pv.fetched_at else None
            ),
            "eta_charge_assumption": self.coordinator.options.get(
                CONF_HEMS_CHARGE_EFFICIENCY, 0.95
            ),
            "eta_discharge_assumption": self.coordinator.options.get(
                CONF_HEMS_DISCHARGE_EFFICIENCY, 0.95
            ),
        }

    async def async_shutdown(self) -> None:
        self._shutdown = True
        self._revision += 1
        self._cancel_timer()
        if self._remove_source_listener is not None:
            self._remove_source_listener()
            self._remove_source_listener = None
        if self._adapter is not None:
            self._adapter.shutdown()
        await self.history.async_stop()
        if self._task is not None:
            # Do not cancel a task that may have entered the coordinator ACK path.
            await asyncio.gather(self._task, return_exceptions=True)
        await self.prediction.async_stop()
        if self._execution_store_loaded:
            try:
                await self._execution_store.async_save(self._persisted())
            except HomeAssistantError, OSError, ValueError:
                _LOGGER.exception("HEMS-Vollzugsnachweis konnte nicht gesichert werden")
