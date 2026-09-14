"""Bounded execution state for a reusable PV bridge plan."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from ..domain.bridge_charge import BridgeChargePlan, ChargeWindow, plan_bridge_charge


class BridgeChargeSession:
    """Retain the measured demand while charging resets the discharge forecast."""

    def __init__(self) -> None:
        self.plan: BridgeChargePlan | None = None
        self.status = "off"
        self.attributes: dict[str, Any] = {}
        self.started = False
        self.completed_at: datetime | None = None
        self._completion_pending = False
        self._pv_start: datetime | None = None
        self._fingerprint: object = None
        self._configuration: object = None

    def reset(self, status: str, reason: str | None = None) -> None:
        self.plan = None
        self.started = False
        self.completed_at = None
        self._completion_pending = False
        self._pv_start = None
        self.status = status
        self.attributes = {"reason": reason} if reason else {}

    def sync_configuration(self, configuration: object) -> None:
        """Invalidate changed permissions even while planning inputs are missing."""
        if configuration != self._configuration:
            self.reset("waiting_for_data")
            self._configuration = configuration

    def wait_for_data(
        self,
        now: datetime,
        reason: str | None,
        *,
        data: Mapping[str, Any] | None = None,
    ) -> None:
        """Preserve bounded execution; callers may supply only fresh measurements."""
        if (
            self.plan is not None
            and self.plan.end is not None
            and (self.started or self.completed_at is not None)
        ):
            if self.completed_at is not None and not self._completion_pending:
                return
            if self.started and reason is not None:
                self.attributes["data_gap_reason"] = reason
            self._finish_if_due(now, data)
            if self.started:
                self.pause(reason or "awaiting_confirmation")
        else:
            self.reset("waiting_for_data", reason)

    def _finish_if_due(self, now: datetime, data: Mapping[str, Any] | None) -> None:
        """REQ-BRIDGE-CHARGE: Missing measurements defer only the energy verdict."""
        if self.plan is None or self.plan.end is None:
            return
        usable = data is not None and all(
            not isinstance(data.get(key), bool)
            and isinstance(data.get(key), int | float)
            and math.isfinite(data[key])
            for key in ("battery_soc", "battery_soc_min", "battery_capacity")
        )
        if usable:
            assert data is not None
            usable = (
                data["battery_capacity"] > 0
                and 0 <= data["battery_soc_min"] <= data["battery_soc"] <= 100
            )
        if self.started and (
            now >= self.plan.end
            or (
                usable
                and data is not None
                and self.plan.target_soc is not None
                and data["battery_soc"] >= self.plan.target_soc
            )
        ):
            self.started = False
            self.completed_at = now.astimezone(UTC)
            self._completion_pending = True
            self.attributes["completed_at"] = self.completed_at.isoformat()
            self.attributes["completion_evaluated_at"] = None
            self.attributes["shortfall_kwh"] = None
            self.status = "waiting_for_data"
            self.attributes["reason"] = "measurements_missing"
            if not usable:
                self.attributes.setdefault("data_gap_reason", "measurements_missing")
        if not self._completion_pending or not usable:
            return
        assert data is not None and self._pv_start is not None
        # The frozen plan's PV horizon also applies when the live forecast is
        # missing or has moved. Recovery uses its current measured energy.
        remaining = max(
            0.0,
            self.attributes["average_discharge_w"]
            * max(0.0, (self._pv_start - now).total_seconds())
            / 3600
            - data["battery_capacity"]
            * max(0.0, data["battery_soc"] - data["battery_soc_min"])
            / 100,
        )
        self._completion_pending = False
        self.attributes["shortfall_kwh"] = remaining / 1000
        self.attributes["completion_evaluated_at"] = now.astimezone(UTC).isoformat()
        self.status = "insufficient" if remaining > 1 else "complete"
        self.attributes["reason"] = "charge_shortfall" if remaining > 1 else None

    def prepare(
        self,
        *,
        now: datetime,
        pv_start: datetime,
        observation: Mapping[str, Any],
        data: Mapping[str, Any],
        max_soc: float,
        windows: Sequence[ChargeWindow],
        fingerprint: object,
    ) -> bool:
        """Return whether an existing or newly computed bounded charge is due."""
        now = now.astimezone(UTC)
        if fingerprint != self._fingerprint:
            self.reset("waiting_for_data")
            self._fingerprint = fingerprint
        self._finish_if_due(now, data)
        if self.started and self.plan is not None:
            assert self.plan.end is not None and self.plan.target_soc is not None
            if now < self.plan.end and data["battery_soc"] < self.plan.target_soc:
                self.status = "charging"
                self.attributes["reason"] = self.plan.reason
                self.attributes.pop("data_gap_reason", None)
                return True
        if self.completed_at is not None:
            # A short charge may leave the pre-charge rolling average intact.
            # A new plan needs at least a minute of subsequent observations.
            if now < self.completed_at + timedelta(minutes=1):
                return False
        observed_at = observation.get("observed_at")
        try:
            timestamp = datetime.fromisoformat(str(observed_at))
        except ValueError:
            timestamp = None
        average = observation.get("average_discharge_w")
        minutes = observation.get("observation_minutes")
        if (
            timestamp is None
            or timestamp.tzinfo is None
            or not 0 <= (now - timestamp.astimezone(UTC)).total_seconds() <= 5
            or any(
                isinstance(value, bool)
                or not isinstance(value, int | float)
                or not math.isfinite(value)
                for value in (average, minutes)
            )
            or average <= 0
            or not 1 <= minutes <= 60
        ):
            if self.completed_at is None:
                self.reset("waiting_for_data", "consumption_missing")
            return False
        self.completed_at = None
        self._completion_pending = False
        self._pv_start = pv_start
        self.plan = plan_bridge_charge(
            now=now,
            pv_start=pv_start,
            average_discharge_w=average,
            capacity_wh=data.get("battery_capacity"),
            soc=data.get("battery_soc"),
            min_soc=data.get("battery_soc_min"),
            max_soc=max_soc,
            charge_power_w=data.get("ic_max_power_reference"),
            windows=windows,
        )
        plan = self.plan
        self.status = (
            "waiting_for_data" if plan.status == "unavailable" else plan.status
        )
        self.attributes = {
            "observation_minutes": minutes,
            "average_discharge_w": average,
            "discharge_at": (
                plan.discharge_until.isoformat() if plan.discharge_until else None
            ),
            "charge_start": plan.start.isoformat() if plan.start else None,
            "charge_end": plan.end.isoformat() if plan.end else None,
            "pv_start": pv_start.isoformat(),
            "target_soc": plan.target_soc,
            "shortfall_kwh": (
                plan.missing_energy_wh / 1000
                if plan.missing_energy_wh is not None
                else None
            ),
            "reason": plan.reason,
        }
        return (
            plan.start is not None
            and plan.end is not None
            and plan.start <= now < plan.end
        )

    def mark_started(self) -> None:
        """Freeze only a charge whose command passed the central device policy."""
        self.started = True
        self.status = "charging"
        if self.plan is not None:
            self.attributes["reason"] = self.plan.reason

    def pause(self, reason: str) -> None:
        self.status = "paused"
        self.attributes["reason"] = reason
