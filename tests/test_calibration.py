"""Tests for periodic full-charge calibration (REQ-PERIODIC-FULL-CALIBRATION)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from custom_components.sax_power.application.calibration import (
    CalibrationState,
    evaluate_calibration,
)
from custom_components.sax_power.const import CELL_CALIBRATION_INTERVAL, MAX_SOC
from custom_components.sax_power.infrastructure.calibration_store import (
    CalibrationStateStore,
)

NOW = datetime(2026, 8, 24, 8, 0, tzinfo=UTC)


def _evaluate(
    *,
    now: datetime = NOW,
    soc: int = 50,
    max_soc: int | None = 80,
    state: CalibrationState | None = None,
):
    return evaluate_calibration(
        now=now,
        current_soc=soc,
        configured_max_soc=max_soc,
        state=state or CalibrationState(),
        interval=CELL_CALIBRATION_INTERVAL,
        maximum_soc=MAX_SOC,
    )


def test_first_valid_soc_establishes_baseline_without_immediate_calibration() -> None:
    decision = _evaluate()

    assert decision.state == CalibrationState(NOW, was_full=False)
    assert decision.next_calibration_at == NOW + timedelta(days=7)
    assert decision.calibration_active is False
    assert decision.effective_max_soc == 80
    assert decision.state_changed is True


def test_calibration_becomes_due_at_exactly_seven_days() -> None:
    state = CalibrationState(NOW, was_full=False)

    before = _evaluate(now=NOW + timedelta(days=7) - timedelta(seconds=1), state=state)
    due = _evaluate(now=NOW + timedelta(days=7), state=state)

    assert before.calibration_active is False
    assert before.effective_max_soc == 80
    assert due.calibration_active is True
    assert due.effective_max_soc == MAX_SOC
    assert due.state_changed is False


@pytest.mark.parametrize("max_soc", [None, MAX_SOC])
def test_calibration_override_is_disabled_without_reduced_max_soc(
    max_soc: int | None,
) -> None:
    decision = _evaluate(
        now=NOW + timedelta(days=30),
        max_soc=max_soc,
        state=CalibrationState(NOW, was_full=False),
    )

    assert decision.calibration_active is False
    assert decision.effective_max_soc == MAX_SOC


def test_reaching_full_resets_due_date_once() -> None:
    overdue = CalibrationState(NOW - timedelta(days=8), was_full=False)

    reached = _evaluate(state=overdue, soc=100)
    still_full = _evaluate(
        now=NOW + timedelta(hours=1),
        state=reached.state,
        soc=100,
    )

    assert reached.state == CalibrationState(NOW, was_full=True)
    assert reached.calibration_active is False
    assert reached.effective_max_soc == 80
    assert reached.next_calibration_at == NOW + timedelta(days=7)
    assert reached.state_changed is True
    assert still_full.state == reached.state
    assert still_full.next_calibration_at == reached.next_calibration_at
    assert still_full.state_changed is False


def test_new_full_edge_is_detected_after_soc_drops() -> None:
    full = CalibrationState(NOW, was_full=True)
    dropped = _evaluate(now=NOW + timedelta(hours=1), state=full, soc=99)
    reached_again = _evaluate(
        now=NOW + timedelta(hours=2),
        state=dropped.state,
        soc=100,
    )

    assert dropped.state == CalibrationState(NOW, was_full=False)
    assert dropped.state_changed is True
    assert reached_again.state == CalibrationState(
        NOW + timedelta(hours=2), was_full=True
    )
    assert reached_again.state_changed is True


def test_latest_reduced_user_setting_applies_after_calibration() -> None:
    overdue = CalibrationState(NOW - timedelta(days=8), was_full=False)

    active = _evaluate(state=overdue, max_soc=70)
    changed = _evaluate(state=active.state, max_soc=90)
    completed = _evaluate(state=changed.state, max_soc=90, soc=100)

    assert active.effective_max_soc == 100
    assert changed.calibration_active is True
    assert changed.effective_max_soc == 100
    assert completed.calibration_active is False
    assert completed.effective_max_soc == 90


async def test_calibration_store_round_trip_uses_utc(hass) -> None:
    store = CalibrationStateStore(hass, "round_trip")
    state = CalibrationState(
        datetime(2026, 8, 24, 10, 0, tzinfo=UTC),
        was_full=True,
    )

    await store.async_save(state)
    loaded = await CalibrationStateStore(hass, "round_trip").async_load()

    assert loaded == state


@pytest.mark.parametrize(
    "raw",
    [
        {},
        {"last_full_charge_at": 123, "was_full": False},
        {"last_full_charge_at": "2026-08-24T08:00:00", "was_full": False},
        {"last_full_charge_at": NOW.isoformat(), "was_full": "false"},
    ],
)
async def test_calibration_store_discards_invalid_data(hass, raw) -> None:
    store = CalibrationStateStore(hass, "invalid")
    store._store.async_load = AsyncMock(return_value=raw)

    assert await store.async_load() is None


async def test_calibration_store_rejects_naive_timestamp(hass) -> None:
    store = CalibrationStateStore(hass, "naive")

    with pytest.raises(ValueError, match="ohne Zeitzone"):
        await store.async_save(
            CalibrationState(datetime(2026, 8, 24, 8, 0), was_full=False)
        )
