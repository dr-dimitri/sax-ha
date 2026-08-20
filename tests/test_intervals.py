"""Tests for the interval-type framework (intervals.py)."""

from __future__ import annotations

import pytest

from custom_components.sax_power.const import (
    INTERVAL_SECONDS_HIGH,
    INTERVAL_SECONDS_LOW,
    IntervalType,
)
from custom_components.sax_power.intervals import (
    TASK_INTERVALS,
    TASK_READ_BASIC,
    TASK_READ_EXTENDED,
    TASK_WRITE_GRID_CHARGE,
    TASK_WRITE_SUN_CHARGE,
    resolve_interval_seconds,
    task_interval_seconds,
)


@pytest.mark.parametrize(
    ("interval_type", "normal_interval_seconds", "expected"),
    [
        (IntervalType.HIGH, 10, INTERVAL_SECONDS_HIGH),
        # HIGH ist fest - unabhängig vom konfigurierten NORMAL-Intervall.
        (IntervalType.HIGH, 3600, INTERVAL_SECONDS_HIGH),
        (IntervalType.LOW, 10, INTERVAL_SECONDS_LOW),
        # LOW ist ebenfalls fest.
        (IntervalType.LOW, 3600, INTERVAL_SECONDS_LOW),
        # NORMAL folgt dem übergebenen (bei der Einrichtung konfigurierten)
        # Intervall.
        (IntervalType.NORMAL, 10, 10),
        (IntervalType.NORMAL, 42, 42),
    ],
)
def test_resolve_interval_seconds(
    interval_type: IntervalType, normal_interval_seconds: int, expected: int
) -> None:
    assert (
        resolve_interval_seconds(
            interval_type, normal_interval_seconds=normal_interval_seconds
        )
        == expected
    )


def test_task_interval_seconds_uses_task_mapping() -> None:
    assert task_interval_seconds(TASK_READ_BASIC, normal_interval_seconds=10) == 10


def test_task_interval_seconds_unknown_task_defaults_to_normal() -> None:
    """Ein Task, der nicht in TASK_INTERVALS eingetragen ist, gilt als
    NORMAL (sicherer Default) statt eine Exception auszulösen."""
    assert task_interval_seconds("does_not_exist", normal_interval_seconds=17) == 17


def test_all_existing_tasks_default_to_normal() -> None:
    """Initial müssen alle vorhandenen periodischen Lese-/Schreib-Tasks
    (Basic-/SunSpec-Modus-Read, Netzladung-/SunSpec-Netzladung-Write) dem
    Intervalltyp NORMAL zugeordnet sein - siehe anforderung.yaml."""
    for task in (
        TASK_READ_BASIC,
        TASK_READ_EXTENDED,
        TASK_WRITE_GRID_CHARGE,
        TASK_WRITE_SUN_CHARGE,
    ):
        assert TASK_INTERVALS[task] is IntervalType.NORMAL


@pytest.mark.parametrize(
    "task",
    [
        TASK_READ_BASIC,
        TASK_READ_EXTENDED,
        TASK_WRITE_GRID_CHARGE,
        TASK_WRITE_SUN_CHARGE,
    ],
)
def test_reassigning_a_task_to_high_changes_its_resolved_interval(task: str) -> None:
    """Demonstriert die eigentliche Anforderung: Ein Task lässt sich einem
    anderen Intervalltyp zuordnen, indem ausschließlich TASK_INTERVALS
    geändert wird - der Task-Code selbst (task_interval_seconds) muss dafür
    nicht angepasst werden."""
    original = TASK_INTERVALS[task]
    try:
        TASK_INTERVALS[task] = IntervalType.HIGH
        assert (
            task_interval_seconds(task, normal_interval_seconds=10)
            == INTERVAL_SECONDS_HIGH
        )
    finally:
        TASK_INTERVALS[task] = original
