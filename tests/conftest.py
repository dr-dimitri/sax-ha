"""Fixtures for SAX Power tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def hass_config_dir(tmp_path: Path) -> str:
    """Isolate real HA storage writes from other tests and the source tree."""
    return str(tmp_path)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom_components in every test."""
    yield
