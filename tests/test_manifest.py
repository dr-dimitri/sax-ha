"""Tests for integration metadata and Home Assistant package constraints."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path


def test_pymodbus_requirement_matches_home_assistant_constraint() -> None:
    """Keep the custom integration installable in the pinned HA runtime."""
    manifest_path = (
        Path(__file__).parents[1] / "custom_components" / "sax_power" / "manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pymodbus_requirement = next(
        requirement
        for requirement in manifest["requirements"]
        if requirement.startswith("pymodbus")
    )
    home_assistant_constraints = (
        files("homeassistant")
        .joinpath("package_constraints.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert pymodbus_requirement in home_assistant_constraints
