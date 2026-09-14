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
        self._fingerprint: object = None
        self._configuration: object = None

    def reset(self, status: str, reason: str | None = None) -> None:
        self.plan = None
        self.started = False
        self.completed_at = None
        self.status = status
        self.attributes = {"reason": reason} if reason else {}

    def sync_configuration(self, configuration: object) -> None:
        """Invalidate changed permissions even while planning inputs are missing."""
        if configuration != self._configuration:
            self.reset("waiting_for_data")
            self._configuration = configuration

    def wait_for_data(self, now: datetime, reason: str) -> None:
        """REQ-BRIDGE-CHARGE: A transient outage preserves only a bounded charge."""
        if (
            self.plan is not None
            and self.plan.end is not None
            and (self.started or self.completed_at is not None)
        ):
            if self.started and now >= self.plan.end:
                self.started = False
                self.completed_at = now
            if self.started:
                self.pause(reason)
            else:
                self.status = "waiting_for_data"
                self.attributes["reason"] = reason
        else:
            self.reset("waiting_for_data", reason)

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
        if self.started and self.plan is not None:
            assert self.plan.end is not None and self.plan.target_soc is not None
            if now < self.plan.end and data["battery_soc"] < self.plan.target_soc:
                self.status = "charging"
                self.attributes["reason"] = self.plan.reason
                return True
            self.started = False
            self.completed_at = now
            self.status = "complete"
            self.attributes["reason"] = None
            remaining = max(
                0.0,
                self.attributes["average_discharge_w"]
                * max(0.0, (pv_start - now).total_seconds())
                / 3600
                - data["battery_capacity"]
                * max(0.0, data["battery_soc"] - data["battery_soc_min"])
                / 100,
            )
            self.attributes["shortfall_kwh"] = remaining / 1000
            if remaining > 1:
                self.status = "insufficient"
                self.attributes["reason"] = "charge_shortfall"
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
