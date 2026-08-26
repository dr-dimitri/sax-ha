"""Versioned persistence for the operative money balance of the storage.

Siehe anforderung.yaml, REQ-ECONOMICS-ACCOUNTING. Analog zu
infrastructure/energy_store.py, aber mit einer wichtigen Abweichung: Die
drei Geldsummen dürfen wegen negativer Strompreise legitim schwanken und
sogar negativ sein - anders als die monoton steigenden Energiezähler ist
"der neue Wert ist kleiner als der alte" hier kein Korruptionsindiz und
wird deshalb NICHT abgelehnt. Nur NaN/Inf/Fremdtypen gelten als korrupt.
`unpriced_charge_kwh`/`unpriced_discharge_kwh` sind dagegen echte
kumulierte Energiemengen (nur additiv) und bleiben monoton wie bei
energy_store.py. `unvalued_inventory_kwh` ist ein Bestand (Gauge, kann
sowohl durch Ladung steigen als auch durch Entladung oder die
SOC-Minimum-Korrektur sinken) und braucht deshalb ebenfalls keine
Monotonie, nur eine Wertebereichsprüfung (endlich, >= 0).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.economics"
ECONOMICS_SAVE_DELAY = 300


@dataclass(frozen=True)
class EconomicsState:
    """Persistierter Stand der Wirtschaftlichkeitsbilanz eines Config Entry.

    `economics_started_at` ist der Zeitpunkt der erstmaligen Aktivierung
    (UTC) - einmalig gesetzt und danach unveränderlich, analog zu
    EnergyState.origin_accounting_started_at. `last_tariff_revision_at`
    ist rein diagnostisch (letzte Options-Änderung) und darf sich beliebig
    oft ändern.
    """

    grid_charge_cost_eur: float | None = None
    pv_opportunity_cost_eur: float | None = None
    avoided_grid_cost_eur: float | None = None
    unvalued_inventory_kwh: float | None = None
    unpriced_charge_kwh: float | None = None
    unpriced_discharge_kwh: float | None = None
    economics_started_at: datetime | None = None
    last_tariff_revision_at: datetime | None = None

    @property
    def initialized(self) -> bool:
        """Ob die Bilanz vollständig aktiviert (bootstrapped) wurde.

        Alle sieben Kernfelder bilden ein gemeinsam behandeltes Bündel -
        analog zu EnergyState.origin_initialized (REQ-ENERGY-ORIGIN): Ist
        auch nur eines ungültig, ist der Rest ohne bekannten
        Aktivierungszeitpunkt bzw. ohne die übrigen Teilsummen nicht
        aussagekräftig, und der Coordinator bootstrapped die Bilanz beim
        nächsten Datenpunkt komplett neu (siehe
        SaxPowerCoordinator._bootstrap_economics_if_ready). Das rein
        diagnostische `last_tariff_revision_at` ist bewusst NICHT Teil
        dieses Bündels.
        """
        return (
            self.grid_charge_cost_eur is not None
            and self.pv_opportunity_cost_eur is not None
            and self.avoided_grid_cost_eur is not None
            and self.unvalued_inventory_kwh is not None
            and self.unpriced_charge_kwh is not None
            and self.unpriced_discharge_kwh is not None
            and self.economics_started_at is not None
        )


class EconomicsStateStore:
    """Persist the operative money balance per config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry_id}",
        )
        self._last_persisted = EconomicsState()
        self._pending: EconomicsState | None = None
        self._save_scheduled = False

    async def async_load(self) -> EconomicsState | None:
        """Load the balance, rejecting invalid fields independently."""
        raw = await self._store.async_load()
        if raw is None:
            return None
        if not isinstance(raw, dict):
            _LOGGER.warning(
                "Ungültigen gespeicherten Wirtschaftlichkeitszustand "
                "verworfen: kein Objekt"
            )
            return EconomicsState()

        state = EconomicsState(
            grid_charge_cost_eur=self._validated_amount(
                raw.get("grid_charge_cost_eur"), "Netzladekosten"
            ),
            pv_opportunity_cost_eur=self._validated_amount(
                raw.get("pv_opportunity_cost_eur"), "PV-Opportunitätskosten"
            ),
            avoided_grid_cost_eur=self._validated_amount(
                raw.get("avoided_grid_cost_eur"), "Vermiedene Netzkosten"
            ),
            unvalued_inventory_kwh=self._validated_nonnegative(
                raw.get("unvalued_inventory_kwh"), "Unbewerteter Bestand"
            ),
            unpriced_charge_kwh=self._validated_nonnegative(
                raw.get("unpriced_charge_kwh"), "Unbepreiste Ladung"
            ),
            unpriced_discharge_kwh=self._validated_nonnegative(
                raw.get("unpriced_discharge_kwh"), "Unbepreiste Entladung"
            ),
            economics_started_at=self._validated_timestamp(
                raw.get("economics_started_at"), "Aktivierungszeitpunkt"
            ),
            last_tariff_revision_at=self._validated_timestamp(
                raw.get("last_tariff_revision_at"), "letzte Tarifrevision"
            ),
        )
        self._last_persisted = self._baseline(state)
        return state

    @staticmethod
    def _baseline(state: EconomicsState) -> EconomicsState:
        """Monotonie-/Vergleichs-Baseline aus einem geladenen Zustand
        ableiten (siehe EnergyStateStore._origin_baseline für dasselbe
        Muster bei REQ-ENERGY-ORIGIN).

        Der an den Aufrufer zurückgegebene `state` behält jedes einzeln
        gültige Feld (unabhängige Feldvalidierung, siehe oben). Als interne
        Baseline für künftige Schreibversuche (`_accept`) ist ein
        unvollständiges Bündel (`initialized` falsch) dagegen unbrauchbar:
        Der Coordinator bootstrapped die Bilanz in diesem Fall komplett neu
        (alle Teilsummen auf 0, neuer Aktivierungszeitpunkt) - ohne diese
        Bereinigung würde dieser neue Stand an den stehen gebliebenen alten
        Teilwerten bzw. dem alten Aktivierungszeitpunkt als "rückläufig"
        bzw. "abweichend" scheitern und die Bilanz bliebe über jeden
        Neustart hinweg dauerhaft unpersistiert.
        """
        if state.initialized:
            return state
        fields = (
            state.grid_charge_cost_eur,
            state.pv_opportunity_cost_eur,
            state.avoided_grid_cost_eur,
            state.unvalued_inventory_kwh,
            state.unpriced_charge_kwh,
            state.unpriced_discharge_kwh,
            state.economics_started_at,
        )
        if all(value is None for value in fields):
            return state
        return replace(
            state,
            grid_charge_cost_eur=None,
            pv_opportunity_cost_eur=None,
            avoided_grid_cost_eur=None,
            unvalued_inventory_kwh=None,
            unpriced_charge_kwh=None,
            unpriced_discharge_kwh=None,
            economics_started_at=None,
        )

    @callback
    def async_delay_save(
        self, state: EconomicsState, delay: float = ECONOMICS_SAVE_DELAY
    ) -> bool:
        """Coalesce frequent balance changes into one delayed write."""
        if not self._accept(state):
            return False
        self._pending = state
        if not self._save_scheduled:
            self._save_scheduled = True
            self._store.async_delay_save(self._consume_pending, delay)
        return True

    async def async_save(self, state: EconomicsState) -> bool:
        """Immediately persist a final snapshot, cancelling a delayed write."""
        if not self._accept(state):
            return False
        self._pending = None
        self._save_scheduled = False
        await self._store.async_save(self._serialize(state))
        self._last_persisted = state
        return True

    def _consume_pending(self) -> dict[str, Any]:
        """Return the newest coalesced state when Home Assistant writes it."""
        state = self._pending or self._last_persisted
        self._pending = None
        self._save_scheduled = False
        self._last_persisted = state
        return self._serialize(state)

    def _accept(self, state: EconomicsState) -> bool:
        """Feldweise Plausibilitätsprüfung vor dem Schreiben.

        Die drei Geldsummen dürfen wegen negativer Preise schwanken und
        sinken - hier nur Endlichkeit prüfen, kein Monotonie-Vergleich.
        unpriced_charge_kwh/unpriced_discharge_kwh sind dagegen echte
        kumulierte Mengen und bleiben monoton. economics_started_at ist
        eine einmalig gesetzte Konstante.
        """
        baseline = self._pending or self._last_persisted
        for label, value in (
            ("Netzladekosten", state.grid_charge_cost_eur),
            ("PV-Opportunitätskosten", state.pv_opportunity_cost_eur),
            ("Vermiedene Netzkosten", state.avoided_grid_cost_eur),
        ):
            if value is not None and (
                not math.isfinite(value) or isinstance(value, bool)
            ):
                _LOGGER.warning(
                    "Ungültigen Wirtschaftlichkeits-Snapshot für %s verworfen: %r",
                    label,
                    value,
                )
                return False
        for label, value, previous in (
            ("Unbewerteter Bestand", state.unvalued_inventory_kwh, None),
            (
                "Unbepreiste Ladung",
                state.unpriced_charge_kwh,
                baseline.unpriced_charge_kwh,
            ),
            (
                "Unbepreiste Entladung",
                state.unpriced_discharge_kwh,
                baseline.unpriced_discharge_kwh,
            ),
        ):
            if value is not None and (
                not math.isfinite(value) or value < 0 or isinstance(value, bool)
            ):
                _LOGGER.warning(
                    "Ungültigen Wirtschaftlichkeits-Snapshot für %s verworfen: %r",
                    label,
                    value,
                )
                return False
            if previous is not None and (value is None or value < previous):
                _LOGGER.warning(
                    "Rückläufigen Wirtschaftlichkeits-Snapshot für %s verworfen: "
                    "%r statt mindestens %r",
                    label,
                    value,
                    previous,
                )
                return False
        if (
            baseline.economics_started_at is not None
            and state.economics_started_at != baseline.economics_started_at
        ):
            _LOGGER.warning(
                "Abweichenden Aktivierungszeitpunkt der Wirtschaftlichkeit "
                "verworfen: %r statt %r",
                state.economics_started_at,
                baseline.economics_started_at,
            )
            return False
        return True

    @staticmethod
    def _validated_amount(value: Any, label: str) -> float | None:
        """Ein Geldbetrag: endlich, aber ausdrücklich ohne Vorzeichenprüfung
        (negative Strompreise sind zulässig, siehe REQ-ECONOMICS-ACCOUNTING)."""
        if value is None:
            return None
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(value)
        ):
            _LOGGER.warning(
                "Ungültigen gespeicherten Betrag für %s verworfen: %r",
                label,
                value,
            )
            return None
        return float(value)

    @staticmethod
    def _validated_nonnegative(value: Any, label: str) -> float | None:
        if value is None:
            return None
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(value)
            or value < 0
        ):
            _LOGGER.warning(
                "Ungültigen gespeicherten Wert für %s verworfen: %r",
                label,
                value,
            )
            return None
        return float(value)

    @staticmethod
    def _validated_timestamp(value: Any, label: str) -> datetime | None:
        if value is None:
            return None
        parsed = dt_util.parse_datetime(value) if isinstance(value, str) else None
        if parsed is None or parsed.tzinfo is None:
            _LOGGER.warning(
                "Ungültigen gespeicherten Zeitstempel für %s verworfen: %r",
                label,
                value,
            )
            return None
        return dt_util.as_utc(parsed)

    @staticmethod
    def _serialize(state: EconomicsState) -> dict[str, Any]:
        return {
            "grid_charge_cost_eur": state.grid_charge_cost_eur,
            "pv_opportunity_cost_eur": state.pv_opportunity_cost_eur,
            "avoided_grid_cost_eur": state.avoided_grid_cost_eur,
            "unvalued_inventory_kwh": state.unvalued_inventory_kwh,
            "unpriced_charge_kwh": state.unpriced_charge_kwh,
            "unpriced_discharge_kwh": state.unpriced_discharge_kwh,
            "economics_started_at": (
                state.economics_started_at.isoformat()
                if state.economics_started_at is not None
                else None
            ),
            "last_tariff_revision_at": (
                state.last_tariff_revision_at.isoformat()
                if state.last_tariff_revision_at is not None
                else None
            ),
        }
