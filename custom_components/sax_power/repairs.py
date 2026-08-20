"""Repairs-Flows für die SAX Power Integration.

Enthält den Bestätigungsdialog für den Konflikt zwischen Netzladung
(zeitgesteuertes Laden) und preisoptimiertem Laden. Beide laden aktiv aus
dem Netz über denselben SunSpec-Schreibpfad und dürfen deshalb nicht
gleichzeitig aktiv sein.

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

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DATA_COORDINATOR, DOMAIN, ISSUE_PRICE_CHARGE_CONFLICT
from .coordinator import SaxPowerCoordinator


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    """Fix-Flow für ein reparierbares Issue dieser Integration."""
    return ChargeConflictRepairFlow(data or {})


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
