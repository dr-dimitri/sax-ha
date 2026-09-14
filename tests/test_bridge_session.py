"""Bounded execution and retained observations for REQ-BRIDGE-CHARGE."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from custom_components.sax_power.application.bridge_session import BridgeChargeSession
from custom_components.sax_power.domain.bridge_charge import ChargeWindow

NOW = datetime(2026, 9, 13, tzinfo=UTC)
PV_START = NOW + timedelta(hours=8)
BATTERY = {
    "battery_soc": 10,
    "battery_soc_min": 10,
    "battery_capacity": 10000,
    "ic_max_power_reference": 2000,
}


def _observation(now: datetime = NOW, **values: Any) -> dict[str, Any]:
    return {
        "observed_at": now.isoformat(),
        "average_discharge_w": 500,
        "observation_minutes": 60,
    } | values


def _prepare(
    session: BridgeChargeSession,
    *,
    now: datetime = NOW,
    observation: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    **values: Any,
) -> bool:
    return session.prepare(
        **(
            {
                "now": now,
                "pv_start": PV_START,
                "observation": (
                    _observation(now) if observation is None else observation
                ),
                "data": BATTERY | (data or {}),
                "max_soc": 80,
                "windows": [ChargeWindow(NOW, NOW + timedelta(hours=6))],
                "fingerprint": "unchanged_configuration",
            }
            | values
        )
    )


def _started() -> BridgeChargeSession:
    session = BridgeChargeSession()
    assert _prepare(session)
    session.mark_started()
    return session


def test_due_plan_does_not_claim_charging_before_command_acknowledgment() -> None:
    session = BridgeChargeSession()
    assert _prepare(session)
    assert session.status == "planned"
    assert not session.started
    assert session.plan is not None
    assert session.attributes["charge_start"] == NOW.isoformat()
    assert session.attributes["charge_end"] == (NOW + timedelta(hours=1.6)).isoformat()
    assert session.attributes["pv_start"] == PV_START.isoformat()
    assert session.attributes["target_soc"] == 42
    assert session.attributes["shortfall_kwh"] == 0
    session.mark_started()
    assert session.status == "charging" and session.started


def test_future_plan_becomes_due_without_moving_start_with_each_poll() -> None:
    session = BridgeChargeSession()
    assert not _prepare(session, data={"battery_soc": 25})
    assert session.status == "planned"
    assert session.plan is not None
    start, end = session.plan.start, session.plan.end
    assert start == NOW + timedelta(hours=3)
    assert not _prepare(session, now=NOW + timedelta(hours=1), data={"battery_soc": 20})
    assert session.plan is not None
    assert (session.plan.start, session.plan.end) == (start, end)
    assert _prepare(session, now=start)
    assert session.plan is not None and session.plan.end == end


def test_active_charge_preserves_plan_across_forecast_reset() -> None:
    session = _started()
    plan = session.plan
    attributes = dict(session.attributes)
    assert _prepare(
        session,
        now=NOW + timedelta(minutes=2),
        observation={},
        data={"battery_soc": 11},
    )
    assert session.plan is plan
    assert session.attributes == attributes
    assert session.status == "charging"


def test_active_charge_does_not_replace_its_measured_demand_mid_charge() -> None:
    session = _started()
    plan = session.plan
    assert _prepare(
        session,
        now=NOW + timedelta(minutes=1),
        observation=_observation(NOW + timedelta(minutes=1), average_discharge_w=9000),
    )
    assert session.plan is plan
    assert session.attributes["average_discharge_w"] == 500


def test_exact_deadline_stops_without_a_new_discharge_observation() -> None:
    session = _started()
    assert session.plan is not None and session.plan.end is not None
    deadline = session.plan.end
    assert not _prepare(session, now=deadline, observation={}, data={"battery_soc": 42})
    assert session.status == "complete"
    assert not session.started and session.completed_at == deadline
    assert session.attributes["shortfall_kwh"] == 0


def test_precise_target_soc_stops_before_deadline() -> None:
    session = _started()
    now = NOW + timedelta(hours=1)
    assert not _prepare(session, now=now, data={"battery_soc": 42})
    assert not session.started and session.completed_at == now
    # Reaching the planned SOC early leaves more discharge time until PV.
    assert session.status == "insufficient"
    assert session.attributes["shortfall_kwh"] == pytest.approx(0.3)


def test_fractional_soc_below_target_keeps_charging() -> None:
    session = _started()
    assert _prepare(
        session,
        now=NOW + timedelta(hours=1),
        observation={},
        data={"battery_soc": 41.99},
    )
    assert session.started and session.status == "charging"


def test_actual_energy_shortfall_is_reported_when_deadline_expires() -> None:
    session = _started()
    assert session.plan is not None and session.plan.end is not None
    assert not _prepare(
        session,
        now=session.plan.end,
        observation={},
        data={"battery_soc": 30},
    )
    assert session.status == "insufficient"
    assert session.attributes["reason"] == "charge_shortfall"
    assert session.attributes["shortfall_kwh"] == pytest.approx(1.2)


def test_configuration_change_invalidates_frozen_plan_without_fresh_demand() -> None:
    session = _started()
    assert not _prepare(
        session,
        now=NOW + timedelta(minutes=2),
        observation={},
        fingerprint="changed_configuration",
    )
    assert session.plan is None and not session.started
    assert session.status == "waiting_for_data"
    assert session.attributes == {"reason": "consumption_missing"}


def test_configuration_change_replans_when_new_observation_is_available() -> None:
    session = _started()
    original = session.plan
    assert _prepare(
        session,
        now=NOW + timedelta(minutes=1),
        max_soc=20,
        fingerprint="lower_ceiling",
        windows=[ChargeWindow(NOW, NOW + timedelta(minutes=30))],
    )
    assert session.plan is not original
    assert session.status == "insufficient" and not session.started
    assert session.plan is not None and session.plan.target_soc <= 20


def test_pause_can_resume_same_frozen_plan_without_extending_deadline() -> None:
    session = _started()
    plan = session.plan
    session.pause("pv_surplus")
    assert session.status == "paused"
    assert session.attributes["reason"] == "pv_surplus"
    assert _prepare(
        session,
        now=NOW + timedelta(minutes=2),
        observation={},
        data={"battery_soc": 11},
    )
    assert session.plan is plan
    assert session.status == "charging" and session.started
    assert session.attributes["reason"] is None


def test_pause_does_not_extend_expired_plan() -> None:
    session = _started()
    session.pause("manual_charge")
    assert session.plan is not None and session.plan.end is not None
    assert not _prepare(
        session,
        now=session.plan.end + timedelta(seconds=1),
        observation={},
        data={"battery_soc": 42},
    )
    assert not session.started and session.status == "complete"


def test_unstarted_paused_plan_needs_current_observations_to_resume() -> None:
    session = BridgeChargeSession()
    assert _prepare(session)
    session.pause("pv_surplus")
    assert not _prepare(session, now=NOW + timedelta(seconds=10), observation={})
    assert session.status == "waiting_for_data"
    assert session.plan is None


def test_short_charge_cannot_immediately_reuse_its_precharge_history() -> None:
    session = BridgeChargeSession()
    assert _prepare(session, pv_start=NOW + timedelta(minutes=2))
    session.mark_started()
    assert session.plan is not None and session.plan.end is not None
    deadline = session.plan.end
    assert deadline == NOW + timedelta(seconds=24)
    assert not _prepare(session, now=deadline, pv_start=NOW + timedelta(minutes=2))
    completed = session.plan
    assert not _prepare(
        session,
        now=deadline + timedelta(seconds=59),
        pv_start=NOW + timedelta(minutes=2),
    )
    assert session.plan is completed
    assert _prepare(
        session,
        now=deadline + timedelta(seconds=60),
        pv_start=NOW + timedelta(minutes=2),
    )
    assert session.plan is not completed
    assert session.completed_at is None and not session.started


def test_completed_plan_stays_visible_while_new_observations_are_missing() -> None:
    session = _started()
    assert session.plan is not None and session.plan.end is not None
    deadline = session.plan.end
    assert not _prepare(session, now=deadline, observation={}, data={"battery_soc": 42})
    assert not _prepare(
        session,
        now=deadline + timedelta(minutes=2),
        observation={},
        data={"battery_soc": 41},
    )
    assert session.status == "complete"
    assert session.completed_at == deadline


def test_sufficient_existing_energy_reports_no_charge_with_observation() -> None:
    session = BridgeChargeSession()
    assert not _prepare(session, data={"battery_soc": 60})
    assert session.status == "not_needed"
    assert session.attributes["observation_minutes"] == 60
    assert session.attributes["average_discharge_w"] == 500
    assert session.attributes["charge_start"] is None
    assert session.attributes["charge_end"] is None
    assert session.attributes["shortfall_kwh"] == 0


def test_partial_plan_retains_shortfall_when_charge_starts() -> None:
    session = BridgeChargeSession()
    assert _prepare(session, windows=[ChargeWindow(NOW, NOW + timedelta(minutes=30))])
    assert session.status == "insufficient"
    assert session.attributes["shortfall_kwh"] == pytest.approx(2.75)
    session.mark_started()
    assert session.status == "charging"
    assert session.attributes["shortfall_kwh"] == pytest.approx(2.75)


def test_no_usable_window_has_shortfall_and_no_charge_times() -> None:
    session = BridgeChargeSession()
    assert not _prepare(session, windows=[])
    assert session.status == "insufficient"
    assert session.attributes["shortfall_kwh"] == 4
    assert session.attributes["charge_start"] is None


def test_invalid_battery_plan_reports_waiting_instead_of_charging() -> None:
    session = BridgeChargeSession()
    assert not _prepare(session, data={"battery_capacity": 0})
    assert session.status == "waiting_for_data"
    assert session.attributes["reason"] == "invalid_battery_state"
    assert session.attributes["shortfall_kwh"] is None


@pytest.mark.parametrize(
    "observation",
    [
        {},
        _observation(observed_at=None),
        _observation(observed_at="unavailable"),
        _observation(observed_at=NOW.replace(tzinfo=None).isoformat()),
        _observation(NOW - timedelta(seconds=5.01)),
        _observation(NOW + timedelta(microseconds=1)),
        _observation(average_discharge_w=0),
        _observation(average_discharge_w=-1),
        _observation(observation_minutes=0.99),
        _observation(observation_minutes=60.01),
    ],
)
def test_missing_invalid_or_stale_observation_rejects_new_plan(
    observation: dict[str, Any],
) -> None:
    session = BridgeChargeSession()
    assert not _prepare(session, observation=observation)
    assert session.plan is None
    assert session.status == "waiting_for_data"
    assert session.attributes == {"reason": "consumption_missing"}


@pytest.mark.parametrize("key", ["average_discharge_w", "observation_minutes"])
@pytest.mark.parametrize("invalid", [None, True, "10", float("inf"), float("nan")])
def test_invalid_observation_numbers_are_rejected(key: str, invalid: Any) -> None:
    session = BridgeChargeSession()
    assert not _prepare(session, observation=_observation(**{key: invalid}))
    assert session.status == "waiting_for_data" and session.plan is None


@pytest.mark.parametrize("minutes", [1, 60])
def test_five_second_freshness_and_observation_duration_boundaries_are_valid(
    minutes: float,
) -> None:
    session = BridgeChargeSession()
    assert _prepare(
        session,
        observation=_observation(
            NOW - timedelta(seconds=5), observation_minutes=minutes
        ),
    )
    assert session.status == "planned"
    assert session.attributes["observation_minutes"] == minutes


def test_missing_fresh_observation_removes_previously_scheduled_plan() -> None:
    session = BridgeChargeSession()
    assert not _prepare(session, data={"battery_soc": 25})
    assert session.plan is not None
    assert not _prepare(session, now=NOW + timedelta(seconds=10), observation={})
    assert session.plan is None
    assert session.status == "waiting_for_data"


def test_reset_clears_execution_and_explanation() -> None:
    session = _started()
    session.reset("off", "disabled")
    assert session.status == "off"
    assert session.plan is None and not session.started
    assert session.completed_at is None
    assert session.attributes == {"reason": "disabled"}


@pytest.mark.parametrize("path", ["regular", "data_gap"])
@pytest.mark.parametrize("soc,shortfall", [(30, 1.2), (42, 0)])
def test_completion_uses_frozen_pv_horizon_and_measured_energy(
    path: str, soc: float, shortfall: float
) -> None:
    """REQ-BRIDGE-CHARGE: Both completion paths assess the same frozen plan."""
    session = _started()
    assert session.plan is not None and session.plan.end is not None
    deadline = session.plan.end
    if path == "regular":
        assert not _prepare(
            session,
            now=deadline,
            pv_start=PV_START + timedelta(hours=5),
            observation={},
            data={"battery_soc": soc},
        )
    else:
        session.wait_for_data(
            deadline, "pv_start_missing", data=BATTERY | {"battery_soc": soc}
        )
        assert session.attributes["data_gap_reason"] == "pv_start_missing"
    assert session.status == ("insufficient" if shortfall else "complete")
    assert session.attributes["shortfall_kwh"] == pytest.approx(shortfall)
    assert session.attributes["completed_at"] == deadline.isoformat()
    assert session.attributes["completion_evaluated_at"] == deadline.isoformat()
    assert session.attributes["pv_start"] == PV_START.isoformat()
    assert not session.started


@pytest.mark.parametrize("key", ["battery_soc", "battery_soc_min", "battery_capacity"])
@pytest.mark.parametrize("invalid", [None, True, "10", float("inf"), float("nan")])
def test_completion_waits_for_valid_measurements_then_assesses_once(
    key: str, invalid: Any
) -> None:
    """REQ-BRIDGE-CHARGE: Deferred energy is unknown, with a dated recovery verdict."""
    session = _started()
    assert session.plan is not None and session.plan.end is not None
    deadline = session.plan.end
    session.wait_for_data(
        deadline, "measurements_missing", data=BATTERY | {key: invalid}
    )
    assert session.status == "waiting_for_data"
    assert session.attributes["reason"] == "measurements_missing"
    assert session.attributes["shortfall_kwh"] is None
    assert session.attributes["completed_at"] == deadline.isoformat()
    assert session.attributes["completion_evaluated_at"] is None
    recovered = deadline + timedelta(minutes=2)
    assert not _prepare(
        session, now=recovered, observation={}, data={"battery_soc": 30}
    )
    assert session.status == "insufficient"
    assert session.attributes["shortfall_kwh"] == pytest.approx(1.2 - 1 / 60)
    assert session.attributes["completion_evaluated_at"] == recovered.isoformat()
    assert session.completed_at == deadline
    attributes = dict(session.attributes)
    session.wait_for_data(recovered + timedelta(minutes=1), "pv_start_missing")
    assert session.attributes == attributes


def test_deferred_completion_keeps_cooldown_when_pv_recovers() -> None:
    """REQ-BRIDGE-CHARGE: Completing a gap must not reuse precharge history."""
    session = BridgeChargeSession()
    assert _prepare(session, pv_start=NOW + timedelta(minutes=2))
    session.mark_started()
    assert session.plan is not None and session.plan.end is not None
    plan = session.plan
    deadline = plan.end
    session.wait_for_data(deadline, "measurements_missing")
    assert session.attributes["shortfall_kwh"] is None
    assert not _prepare(session, now=deadline + timedelta(seconds=59))
    assert session.plan is plan
    assert session.attributes["shortfall_kwh"] is not None
    assert session.completed_at == deadline
    assert _prepare(session, now=deadline + timedelta(seconds=60))
    assert session.plan is not plan
    assert session.completed_at is None
    assert "data_gap_reason" not in session.attributes
    assert "completed_at" not in session.attributes


def test_configuration_change_discards_deferred_completion() -> None:
    """REQ-BRIDGE-CHARGE: Revocation invalidates both execution and later verdicts."""
    session = _started()
    assert session.plan is not None and session.plan.end is not None
    deadline = session.plan.end
    session.wait_for_data(deadline, "measurements_missing")
    session.sync_configuration("changed_configuration")
    assert not _prepare(session, now=deadline + timedelta(seconds=1), observation={})
    assert session.plan is None and session.completed_at is None
    assert session.attributes == {"reason": "consumption_missing"}


def test_finished_verdict_does_not_acquire_later_unrelated_data_gap() -> None:
    """REQ-BRIDGE-CHARGE: A later outage cannot rewrite the finished charge."""
    session = _started()
    assert session.plan is not None and session.plan.end is not None
    deadline = session.plan.end
    assert not _prepare(session, now=deadline, observation={}, data={"battery_soc": 42})
    attributes = dict(session.attributes)
    assert "data_gap_reason" not in attributes
    session.wait_for_data(deadline + timedelta(seconds=1), "pv_start_missing")
    assert session.status == "complete"
    assert session.attributes == attributes
