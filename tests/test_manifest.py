"""Tests for integration metadata and Home Assistant package constraints."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture
def manifest() -> dict[str, object]:
    """Load the integration manifest."""
    manifest_path = ROOT / "custom_components" / "sax_power" / "manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def test_pymodbus_requirement_matches_home_assistant_constraint(
    manifest: dict[str, object],
) -> None:
    """Keep the custom integration installable in the pinned HA runtime."""
    requirements = manifest["requirements"]
    assert isinstance(requirements, list)
    pymodbus_requirement = next(
        requirement
        for requirement in requirements
        if isinstance(requirement, str)
        if requirement.startswith("pymodbus")
    )
    home_assistant_constraints = (
        files("homeassistant")
        .joinpath("package_constraints.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert pymodbus_requirement in home_assistant_constraints


def test_hacs_minimum_matches_tested_home_assistant_version() -> None:
    """HACS must reject every Home Assistant runtime not covered by CI."""
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    requirements = (ROOT / "requirements_test.txt").read_text(encoding="utf-8")
    tested_version = next(
        line.removeprefix("homeassistant==")
        for line in requirements.splitlines()
        if line.startswith("homeassistant==")
    )

    assert hacs["homeassistant"] == tested_version
