"""Repairs-Flows für die SAX Power Integration.

Enthält den Bestätigungsdialog für den Konflikt zwischen
Netzladung (zeitgesteuertes Laden) und preisoptimiertem Laden - beide
laden aktiv aus dem Netz über denselben SunSpec-Schreibpfad und dürfen
deshalb nicht gleichzeitig aktiv sein - sowie das Nachrüsten fehlender
Tabs im mitgelieferten Dashboard (siehe
dashboard.async_check_dashboard_up_to_date). Ein eigener Flow erneuert das
optionale Vue-Panel und erinnert an das notwendige Browser-Neuladen
(REQ-VUE-DASHBOARD-REPAIR).

Home Assistant kennt für das Umlegen eines Schalters keinen synchronen
Bestätigungsdialog. Ein reparierbares Issue ist der native Weg zu einem
echten Ja/Nein-Dialog: Der Coordinator lehnt die Aktivierung zunächst ab
und legt dieses Issue an (siehe
SaxPowerCoordinator._async_create_charge_conflict_issue); der Anwender
bestätigt hier, dass das jeweils andere Feature abgeschaltet werden soll,
oder bricht ab - dann bleibt alles unverändert.

Siehe anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.repairs import RepairsFlow
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_DASHBOARD_UPDATE_DISMISSED,
    DATA_COORDINATOR,
    DOMAIN,
    ISSUE_DASHBOARD_OUTDATED,
    ISSUE_PRICE_CHARGE_CONFLICT,
    ISSUE_VUE_DASHBOARD_UPDATE,
)
from .coordinator import SaxPowerCoordinator
from .dashboard import async_create_dashboard
from .vue_dashboard import (
    async_finish_vue_dashboard_repair,
    async_sync_vue_dashboard,
    vue_dashboard_available,
)


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    """Fix-Flow für ein reparierbares Issue dieser Integration.

    Verzweigt über den `issue_key` aus den Issue-Daten statt über die
    `issue_id`: Letztere trägt die Entry-ID als Suffix und ist deshalb
    kein fester Wert, gegen den sich vergleichen ließe.
    """
    issue_data = data or {}
    if issue_data.get("issue_key") == ISSUE_DASHBOARD_OUTDATED:
        return DashboardOutdatedRepairFlow(issue_data)
    if issue_data.get("issue_key") == ISSUE_VUE_DASHBOARD_UPDATE:
        return VueDashboardRepairFlow(issue_data)
    return ChargeConflictRepairFlow(issue_data)


class ChargeConflictRepairFlow(RepairsFlow):
    """Bestätigen oder Abbrechen des Wechsels zwischen den beiden
    netzladenden Automatiken.

    `issue_data` stammt aus dem `data`-Parameter von
    ir.async_create_issue und enthält den Config Entry sowie die
    Information, welches der beiden Features aktiviert werden sollte.
    """

    def __init__(self, issue_data: dict[str, Any]) -> None:
        super().__init__()
        self._entry_id: str = issue_data.get("entry_id", "")
        self._issue_key: str = issue_data.get("issue_key", "")

    def _coordinator(self) -> SaxPowerCoordinator | None:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry_id)
        if entry_data is None:
            return None
        coordinator: SaxPowerCoordinator = entry_data[DATA_COORDINATOR]
        return coordinator

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return self.async_show_menu(step_id="init", menu_options=["confirm", "cancel"])

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Das jeweils andere Feature abschalten und das gewünschte aktivieren.

        force=True, weil der Anwender genau diesen Tausch hier gerade
        bestätigt hat - eine erneute Rückfrage würde den Dialog sonst
        endlos wiederholen.
        """
        if (coordinator := self._coordinator()) is not None:
            if self._issue_key == ISSUE_PRICE_CHARGE_CONFLICT:
                await coordinator.async_set_price_charge_enabled(True, force=True)
            else:
                await coordinator.async_set_timed_charge_enabled(True, force=True)
        return self.async_create_entry(title="", data={})

    async def async_step_cancel(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Nichts ändern - beide Einstellungen bleiben, wie sie waren.

        Das Issue selbst räumt Home Assistant nach Abschluss des Flows auf;
        die zusätzlich erzeugte Persistent Notification muss die Integration
        dagegen selbst entfernen.
        """
        if (coordinator := self._coordinator()) is not None:
            coordinator.async_dismiss_charge_conflict()
        return self.async_create_entry(title="", data={})


class DashboardOutdatedRepairFlow(RepairsFlow):
    """Fehlende Tabs im mitgelieferten Dashboard nachrüsten - oder nicht.

    Beide Wege sind endgültig: Das Nachrüsten baut das Dashboard neu und
    überschreibt dabei eigene Änderungen daran (es gibt keinen Weg, nur
    einen einzelnen Tab zu ergänzen, ohne den Rest anzufassen). Das
    Ablehnen merkt sich die Integration dauerhaft im Config Entry, damit
    der Hinweis nicht bei jedem Neustart erneut erscheint - ein bewusst
    umgebautes Dashboard ist ein legitimer Zustand.
    """

    def __init__(self, issue_data: dict[str, Any]) -> None:
        super().__init__()
        self._entry_id: str = issue_data.get("entry_id", "")

    def _entry(self) -> ConfigEntry | None:
        return self.hass.config_entries.async_get_entry(self._entry_id)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return self.async_show_menu(step_id="init", menu_options=["confirm", "cancel"])

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Dashboard auf den aktuellen Auslieferungsstand bringen.

        force=True, weil ein vorhandenes Dashboard sonst unangetastet
        bliebe - genau das ist ja der gemeldete Zustand.
        """
        if (entry := self._entry()) is not None:
            await async_create_dashboard(self.hass, entry, force=True)
        return self.async_create_entry(title="", data={})

    async def async_step_cancel(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Nichts ändern und künftig nicht mehr danach fragen."""
        if (entry := self._entry()) is not None:
            self.hass.config_entries.async_update_entry(
                entry,
                data={**entry.data, CONF_DASHBOARD_UPDATE_DISMISSED: True},
            )
        return self.async_create_entry(title="", data={})


class VueDashboardRepairFlow(RepairsFlow):
    """Vue-Panel aktualisieren und Browser-Neuladen bewusst bestätigen."""

    def __init__(self, issue_data: dict[str, Any]) -> None:
        super().__init__()
        self._entry_id: str = issue_data.get("entry_id", "")
        self._version: str = issue_data.get("version", "")
        self._token: str = issue_data.get("token", "")
        self._prepared = False

    def _entry(self) -> ConfigEntry | None:
        entry = self.hass.config_entries.async_get_entry(self._entry_id)
        return (
            entry
            if entry is not None
            and entry.domain == DOMAIN
            and vue_dashboard_available(self.hass, entry)
            else None
        )

    def _issue_current(self) -> bool:
        issue = ir.async_get(self.hass).async_get_issue(
            DOMAIN, f"{ISSUE_VUE_DASHBOARD_UPDATE}_{self._entry_id}"
        )
        return (
            issue is not None
            and issue.data is not None
            and issue.data.get("version") == self._version
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return self.async_show_menu(step_id="init", menu_options=["confirm", "cancel"])

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if (entry := self._entry()) is None:
            return self.async_abort(reason="no_longer_available")
        if not await async_sync_vue_dashboard(
            self.hass, entry, force=True, expected_version=self._version
        ):
            if not self._issue_current():
                return self.async_abort(reason="update_changed")
            return self.async_show_form(
                step_id="confirm",
                data_schema=vol.Schema({}),
                errors={"base": "update_failed"},
            )
        self._prepared = True
        return await self.async_step_reload()

    async def async_step_reload(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            entry = self._entry()
            if entry is None:
                return self.async_abort(reason="no_longer_available")
            if not self._prepared or not await async_finish_vue_dashboard_repair(
                self.hass, entry, self._version
            ):
                return self.async_abort(reason="update_changed")
            return self.async_create_entry(title="", data={})
        return self.async_show_form(step_id="reload", data_schema=vol.Schema({}))

    async def async_step_cancel(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if (entry := self._entry()) is None:
            return self.async_abort(reason="no_longer_available")
        if not await async_finish_vue_dashboard_repair(
            self.hass, entry, self._version, dismissed_token=self._token
        ):
            return self.async_abort(reason="update_changed")
        return self.async_create_entry(title="", data={})
