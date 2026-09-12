"""Load persisted state without mistaking Core quarantine for a new entry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store


def _store_file_presence(path_value: str) -> bool:
    path = Path(path_value)
    return path.exists() or any(path.parent.glob(f"{path.name}.corrupt.*"))


async def async_load_checked(
    hass: HomeAssistant, store: Store[dict[str, Any]]
) -> dict[str, Any] | None:
    """REQ-CONTROL-CONFIG-BOOTSTRAP / REQ-GRID-ENERGY: preserve unreadable state.

    Core moves malformed JSON to a .corrupt backup and returns None. Its
    backup must remain evidence of an existing store across reloads, while
    a repaired canonical file must take precedence over that backup.
    """
    existed_before = await hass.async_add_executor_job(_store_file_presence, store.path)
    raw = await store.async_load()
    if raw is None and (
        existed_before
        or await hass.async_add_executor_job(_store_file_presence, store.path)
    ):
        store.make_read_only()
        raise HomeAssistantError(
            "Vorhandener Store ist unlesbar oder wurde von Home Assistant "
            "quarantänisiert; gespeicherten Zustand aus dem Backup wiederherstellen"
        )
    return raw
