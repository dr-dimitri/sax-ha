"""SAX repair issues owned by a Home Assistant config entry."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir

from ..const import DOMAIN


@callback
def async_create_entry_issue(
    hass: HomeAssistant,
    entry_id: str,
    issue_id: str,
    *,
    translation_key: str,
    is_fixable: bool = False,
    data: dict[str, str | int | float | None] | None = None,
    translation_placeholders: dict[str, str] | None = None,
) -> None:
    """Link each warning to its owner when HA supports entry-owned issues."""
    if hass.config_entries.async_get_entry(entry_id) is None:
        return
    owner = (
        {"config_entry_id": entry_id}
        if hasattr(ir.IssueEntry, "config_entry_id")
        else {}
    )
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        **owner,
        severity=ir.IssueSeverity.WARNING,
        is_fixable=is_fixable,
        data=data,
        translation_key=translation_key,
        translation_placeholders=translation_placeholders,
    )


@callback
def async_delete_unlinked_issue(hass: HomeAssistant, issue_id: str) -> None:
    """Keep linked issues and their dismissal across reloads (HA 2026.11+)."""
    issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    if issue is not None and getattr(issue, "config_entry_id", None) is None:
        ir.async_delete_issue(hass, DOMAIN, issue_id)
