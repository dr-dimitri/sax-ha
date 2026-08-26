"""Versioned persistence for the derived energy counters."""

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

# Die Herkunftszähler (REQ-ENERGY-ORIGIN) sind rein additiv: Ein
# Version-1-Snapshot hat diese Felder schlicht nicht im gespeicherten
# Objekt - async_load liefert dafür None zurück wie für jedes fehlende
# Feld, der Coordinator erkennt daran den Migrationsfall und startet die
# Herkunftszählung ab dann transparent bei 0 (siehe
# SaxPowerCoordinator._bootstrap_energy_origin).
#
# Deshalb bleibt STORAGE_VERSION (die Home-Assistant-Hauptversion)
# unverändert bei 1, nur STORAGE_MINOR_VERSION steigt auf 2: Home
# Assistants Store ruft _async_migrate_func nur auf, wenn sich entweder
# Haupt- oder Minor-Version ändert, und die Standardimplementierung wirft
# dabei NotImplementedError. Bei UNVERÄNDERTER Hauptversion fängt der
# Store diesen Fehler selbst ab und behält die vorhandenen Rohdaten bei
# (siehe homeassistant.helpers.storage.Store._async_migrate_func) - bei
# einer geänderten Hauptversion würde derselbe Fehler dagegen ungefangen
# nach oben durchschlagen und das Setup jeder bestehenden Installation mit
# einem Version-1-Snapshot zum Absturz bringen. Ein fehlendes Feld bekommt
# stattdessen über die reguläre Feldvalidierung unten einen sicheren Wert
# ("noch nicht initialisiert"), ohne bestehende Felder anzutasten - genau
# wie bei infrastructure/control_store.py, das aus demselben Grund seine
# STORAGE_VERSION nie erhöht hat.
STORAGE_VERSION = 1
STORAGE_MINOR_VERSION = 2
STORAGE_KEY_PREFIX = f"{DOMAIN}.energy"
ENERGY_SAVE_DELAY = 300


@dataclass(frozen=True)
class EnergyState:
    """Persisted, independently initialised energy counters.

    Die drei Herkunftszähler und `origin_accounting_started_at` bilden
    zusammen EINE Einheit: Sie werden gemeinsam initialisiert (siehe
    `origin_initialized`) und gemeinsam zurückgesetzt, falls auch nur eines
    der vier Felder ungültig ist - ein isoliert wiederhergestellter Zähler
    ohne bekannten Startzeitpunkt (oder umgekehrt) wäre nicht aussagekräftig.
    Das steht nicht im Widerspruch zur unabhängigen Feldvalidierung beim
    Laden (siehe EnergyStateStore.async_load): Jedes Feld wird dort für
    sich geprüft und einzeln verworfen; erst der Coordinator entscheidet,
    ob das verbleibende Herkunfts-Quartett insgesamt noch verwertbar ist.
    """

    charged_kwh: float | None = None
    discharged_kwh: float | None = None
    grid_charged_kwh: float | None = None
    pv_charged_kwh: float | None = None
    unknown_charged_kwh: float | None = None
    origin_accounting_started_at: datetime | None = None

    @property
    def initialized(self) -> bool:
        """Return whether at least one counter has a numeric baseline."""
        return self.charged_kwh is not None or self.discharged_kwh is not None

    @property
    def origin_initialized(self) -> bool:
        """Ob die Herkunftszählung vollständig initialisiert ist.

        Nur wenn alle vier Felder vorhanden sind, gilt der Store als
        maßgebliche Quelle - fehlt eines (frischer Eintrag, Version-1-
        Snapshot ohne diese Felder, oder ein einzelnes verworfenes Feld),
        startet der Coordinator die Herkunftszählung transparent neu.
        """
        return (
            self.grid_charged_kwh is not None
            and self.pv_charged_kwh is not None
            and self.unknown_charged_kwh is not None
            and self.origin_accounting_started_at is not None
        )


class EnergyStateStore:
    """Persist both monotonically increasing counters per config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry_id}",
            minor_version=STORAGE_MINOR_VERSION,
        )
        self._last_persisted = EnergyState()
        self._pending: EnergyState | None = None
        self._save_scheduled = False

    async def async_load(self) -> EnergyState | None:
        """Load both counters, rejecting invalid fields independently."""
        raw = await self._store.async_load()
        if raw is None:
            return None
        if not isinstance(raw, dict):
            _LOGGER.warning(
                "Ungültigen gespeicherten Energiezählerzustand verworfen: "
                "kein Objekt"
            )
            return EnergyState()

        state = EnergyState(
            charged_kwh=self._validated_counter(raw.get("charged_kwh"), "Laden"),
            discharged_kwh=self._validated_counter(
                raw.get("discharged_kwh"), "Entladen"
            ),
            grid_charged_kwh=self._validated_counter(
                raw.get("grid_charged_kwh"), "Netzladung (Herkunft)"
            ),
            pv_charged_kwh=self._validated_counter(
                raw.get("pv_charged_kwh"), "PV-Ladung (Herkunft)"
            ),
            unknown_charged_kwh=self._validated_counter(
                raw.get("unknown_charged_kwh"), "Unbekannte Herkunft"
            ),
            origin_accounting_started_at=self._validated_timestamp(
                raw.get("origin_accounting_started_at")
            ),
        )
        self._last_persisted = self._origin_baseline(state)
        return state

    @staticmethod
    def _origin_baseline(state: EnergyState) -> EnergyState:
        """Monotonie-Baseline für die Herkunftsfelder aus einem geladenen
        Zustand ableiten.

        `async_load` validiert jedes Feld unabhängig (siehe oben) - ein
        einzelnes verworfenes Feld darf die übrigen, individuell gültigen
        Felder nicht löschen, das gilt auch für den an den Aufrufer
        zurückgegebenen `state`. Als interne Monotonie-Baseline (siehe
        `_accept_monotonic`) ist ein unvollständiges Herkunfts-Quartett
        (`origin_initialized` falsch) dagegen unbrauchbar: Der Coordinator
        setzt in diesem Fall alle drei Zähler und den Startzeitpunkt
        gemeinsam neu auf (siehe SaxPowerCoordinator._bootstrap_energy_origin)
        - ohne diese Anpassung würde der nächste Speicherversuch an den
        stehen gebliebenen alten Teilwerten bzw. dem alten Startzeitpunkt
        als "rückläufig" bzw. "abweichend" scheitern (siehe
        _accept_monotonic) und die Herkunft bliebe dauerhaft unpersistiert.
        charged_kwh/discharged_kwh bleiben von dieser Bereinigung
        unberührt.
        """
        if state.origin_initialized:
            return state
        if (
            state.grid_charged_kwh is None
            and state.pv_charged_kwh is None
            and state.unknown_charged_kwh is None
            and state.origin_accounting_started_at is None
        ):
            return state
        return replace(
            state,
            grid_charged_kwh=None,
            pv_charged_kwh=None,
            unknown_charged_kwh=None,
            origin_accounting_started_at=None,
        )

    @callback
    def async_delay_save(
        self, state: EnergyState, delay: float = ENERGY_SAVE_DELAY
    ) -> bool:
        """Coalesce frequent counter changes into one delayed write."""
        if not self._accept_monotonic(state):
            return False
        self._pending = state
        if not self._save_scheduled:
            self._save_scheduled = True
            self._store.async_delay_save(self._consume_pending, delay)
        return True

    async def async_save(self, state: EnergyState) -> bool:
        """Immediately persist a final snapshot, cancelling a delayed write."""
        if not self._accept_monotonic(state):
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

    def _accept_monotonic(self, state: EnergyState) -> bool:
        baseline = self._pending or self._last_persisted
        for label, value, previous in (
            ("Laden", state.charged_kwh, baseline.charged_kwh),
            ("Entladen", state.discharged_kwh, baseline.discharged_kwh),
            (
                "Netzladung (Herkunft)",
                state.grid_charged_kwh,
                baseline.grid_charged_kwh,
            ),
            ("PV-Ladung (Herkunft)", state.pv_charged_kwh, baseline.pv_charged_kwh),
            (
                "Unbekannte Herkunft",
                state.unknown_charged_kwh,
                baseline.unknown_charged_kwh,
            ),
        ):
            if value is not None and (
                not math.isfinite(value) or value < 0 or isinstance(value, bool)
            ):
                _LOGGER.warning(
                    "Ungültigen Energiezähler-Snapshot für %s verworfen: %r",
                    label,
                    value,
                )
                return False
            if previous is not None and (value is None or value < previous):
                _LOGGER.warning(
                    "Rückläufigen Energiezähler-Snapshot für %s verworfen: "
                    "%r statt mindestens %r",
                    label,
                    value,
                    previous,
                )
                return False
        if (
            baseline.origin_accounting_started_at is not None
            and state.origin_accounting_started_at
            != baseline.origin_accounting_started_at
        ):
            # Der Startzeitpunkt der Herkunftszählung ist eine einmalig
            # gesetzte Konstante (siehe origin_initialized) - ein
            # abweichender Wert kann nur aus einem beschädigten Snapshot
            # stammen, niemals aus einer regulären Coordinator-Änderung.
            _LOGGER.warning(
                "Abweichenden Startzeitpunkt der Herkunftszählung verworfen: "
                "%r statt %r",
                state.origin_accounting_started_at,
                baseline.origin_accounting_started_at,
            )
            return False
        return True

    @staticmethod
    def _validated_counter(value: Any, label: str) -> float | None:
        if value is None:
            return None
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(value)
            or value < 0
        ):
            _LOGGER.warning(
                "Ungültigen gespeicherten Energiezähler für %s verworfen: %r",
                label,
                value,
            )
            return None
        return float(value)

    @staticmethod
    def _validated_timestamp(value: Any) -> datetime | None:
        if value is None:
            return None
        parsed = dt_util.parse_datetime(value) if isinstance(value, str) else None
        if parsed is None or parsed.tzinfo is None:
            _LOGGER.warning(
                "Ungültigen gespeicherten Startzeitpunkt der Herkunftszählung "
                "verworfen: %r",
                value,
            )
            return None
        return dt_util.as_utc(parsed)

    @staticmethod
    def _serialize(state: EnergyState) -> dict[str, Any]:
        return {
            "charged_kwh": state.charged_kwh,
            "discharged_kwh": state.discharged_kwh,
            "grid_charged_kwh": state.grid_charged_kwh,
            "pv_charged_kwh": state.pv_charged_kwh,
            "unknown_charged_kwh": state.unknown_charged_kwh,
            "origin_accounting_started_at": (
                state.origin_accounting_started_at.isoformat()
                if state.origin_accounting_started_at is not None
                else None
            ),
        }
