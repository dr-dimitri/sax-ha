"""Versioned persistence for the operative money balance of the storage.

Siehe anforderung.yaml, REQ-ECONOMICS-ACCOUNTING/REQ-ECONOMICS-AMORTIZATION.
Analog zu infrastructure/energy_store.py, aber mit einer wichtigen
Abweichung: Die drei Geldsummen dürfen wegen negativer Strompreise legitim
schwanken und sogar negativ sein - anders als die monoton steigenden
Energiezähler ist "der neue Wert ist kleiner als der alte" hier kein
Korruptionsindiz und wird deshalb NICHT abgelehnt. Nur NaN/Inf/Fremdtypen
gelten als korrupt. Der zusätzlich fortgeschriebene
`operating_result_high_water_eur` ist nur ein nichtnegativer, monotoner
Diagnose-Peak; ausschließlich ein kontrollierter Bilanzneustart darf ihn auf
0 zurücksetzen. `unpriced_charge_kwh`/
`unpriced_discharge_kwh` sind ebenfalls echte kumulierte Energiemengen
(nur additiv) und bleiben monoton wie bei energy_store.py.
`unvalued_inventory_kwh` ist ein Bestand (Gauge, kann sowohl durch Ladung
steigen als auch durch Entladung oder die SOC-Minimum-Korrektur sinken)
und braucht deshalb keine Monotonie, nur eine Wertebereichsprüfung
(endlich, >= 0).

STORAGE_MINOR_VERSION (statt einer erhöhten Hauptversion) trägt die
Tages-Buckets/Payback-Erweiterung aus REQ-ECONOMICS-AMORTIZATION, die
kumulierten bepreisten Lade-/Entlademengen, den zuletzt verwendeten
Bilanzneustart-Grund aus REQ-ECONOMICS-OBSERVABILITY sowie die
Zeitabdeckung der Tages-Buckets (observed_seconds/day_length_seconds) und
den historischen Diagnose-Peak. Minor-Version 7 migriert zusätzlich den
nach alter Semantik noch unbekannt geführten Anfangsbestand auf 0 kWh;
Minor-Version 8 verwirft die mit der früheren Peak-Semantik geführten
Tageswerte (Issue #144) -
siehe den ausführlichen Kommentar bei infrastructure/energy_store.py,
STORAGE_VERSION für die Begründung (ein Hauptversionssprung hätte bei
jedem bestehenden Store NotImplementedError ausgelöst).
"""

from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Any

from homeassistant.const import EVENT_HOMEASSISTANT_FINAL_WRITE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from ..const import DOMAIN, MAX_ECONOMICS_RESTART_REASON_LENGTH
from ..domain.economics_amortization import (
    MAX_STORED_DAYS,
    SECONDS_PER_DAY,
    DayEconomicsResult,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
# Minor-Version 7 ändert die Semantik des beim Bilanzstart bereits vorhandenen
# Speicherinhalts: Bis einschließlich Version 6 wurde er als unbewerteter
# Bestand geführt. Seit Version 7 gilt er als mit 0 EUR beschafft. Der
# Store-Migrationspfad setzt den verbliebenen Altbestand deshalb einmalig auf
# 0, ohne Geldsummen, Bilanzbeginn oder Preisabdeckungszähler zurückzusetzen.
# Minor-Version 8 startet nur die inkompatiblen Tages-Peak-Zuwächse neu; das
# signierte Gesamtergebnis bleibt aus den drei Geldsummen rekonstruierbar.
STORAGE_MINOR_VERSION = 8
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
    # Nichtnegative Netto-Ersparnis seit Bilanzbeginn. Anders als die drei
    # Rohsummen fällt dieser historische Höchststand nie; ein absichtlicher
    # Bilanzneustart setzt ihn über async_reset auf 0 zurück.
    operating_result_high_water_eur: float | None = None
    unvalued_inventory_kwh: float | None = None
    unpriced_charge_kwh: float | None = None
    unpriced_discharge_kwh: float | None = None
    economics_started_at: datetime | None = None
    last_tariff_revision_at: datetime | None = None
    # -- REQ-ECONOMICS-AMORTIZATION ----------------------------------------
    # Abgeschlossene Kalendertage (höchstens MAX_STORED_DAYS, älteste
    # zuerst) - als eigenes Bündel validiert. Fehlt diese Historie (frischer
    # Eintrag, Store aus der Zeit vor 04/06), startet sie einfach leer. Bei
    # einem unvollständigen Kernstand verwirft der Coordinator sie dagegen,
    # damit keine alte Prognose in eine neu gebootstrappte Bilanz gerät.
    day_results: tuple[DayEconomicsResult, ...] = ()
    # Der aktuell noch laufende, unvollständige Kalendertag - `current_day`
    # ist None, solange kein Tag begonnen wurde. Die sechs Werte bilden mit
    # `current_day` zusammen ein eigenes, kleines Sieben-Felder-Bündel (siehe
    # _validated_current_day): Fehlt einer, gilt der ganze angefangene Tag
    # als nicht mehr aussagekräftig und wird verworfen - nicht die
    # abgeschlossene Historie.
    current_day: date | None = None
    current_day_operating_result_eur: float | None = None
    current_day_priced_charge_kwh: float | None = None
    current_day_unpriced_charge_kwh: float | None = None
    current_day_priced_discharge_kwh: float | None = None
    current_day_unpriced_discharge_kwh: float | None = None
    current_day_observed_seconds: float | None = None
    # Zeitpunkt (UTC), zu dem der kumulierte operative Betrag erstmals die
    # Investitionskosten erreicht hat - einmalig gesetzt und danach
    # unveränderlich, unabhängig von einer späteren Änderung der
    # Investitionskosten (siehe anforderung.yaml, REQ-ECONOMICS-AMORTIZATION,
    # Regel 8).
    payback_achieved_at: datetime | None = None
    # -- REQ-ECONOMICS-OBSERVABILITY ----------------------------------------
    # Kumulierte, seit economics_started_at tatsächlich bepreiste Lade-/
    # Entlademenge (kWh) - Gegenstück zu unpriced_charge_kwh/
    # unpriced_discharge_kwh oben, für charge_price_coverage_percent/
    # discharge_price_coverage_percent des Status-Sensors economics_status.
    # Unabhängig vom Sieben-Felder-Bündel: fehlt eines (Store aus der Zeit
    # vor 05/06), beginnt die Abdeckungszählung transparent bei 0 ab jetzt,
    # analog zur Herkunftszählung aus REQ-ENERGY-ORIGIN.
    priced_charge_kwh: float | None = None
    priced_discharge_kwh: float | None = None
    # Zeitpunkt (UTC) und optionaler freier Grund des zuletzt ausgeführten
    # kontrollierten Bilanzneustarts (sax_power.restart_economics_accounting)
    # - rein diagnostisch, für den lokalen Diagnose-Download; beeinflusst
    # keine Berechnung. Darf sich bei jedem weiteren Neustart beliebig
    # ändern (keine Unveränderlichkeit wie economics_started_at).
    last_restart_at: datetime | None = None
    last_restart_reason: str | None = None

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


class _EconomicsStore(Store[dict[str, Any]]):
    """Home-Assistant-Store mit fachlicher Minor-Version-Migration."""

    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: Any
    ) -> Any:
        """Migriere Altbestand und inkompatible Tagesergebnis-Semantik."""
        if old_major_version != STORAGE_VERSION:
            raise NotImplementedError
        if old_minor_version >= STORAGE_MINOR_VERSION or not isinstance(old_data, dict):
            return old_data

        migrated = dict(old_data)
        if old_minor_version < 7:
            inventory = migrated.get("unvalued_inventory_kwh")
            # Ein fehlender oder korrupter Kernwert muss weiterhin das gesamte
            # Sieben-Felder-Bündel entwerten. Nur ein tatsächlich gültiger
            # Altbestand wird migriert; damit repariert die Migration keine
            # beschädigten Snapshots stillschweigend.
            if (
                isinstance(inventory, int | float)
                and not isinstance(inventory, bool)
                and math.isfinite(inventory)
                and inventory >= 0
            ):
                migrated["unvalued_inventory_kwh"] = 0.0
                if inventory > 0:
                    _LOGGER.info(
                        "Bewerte gespeicherten Anfangsbestand von %.3f kWh "
                        "bei der Migration mit 0 EUR",
                        inventory,
                    )
        if old_minor_version < 8:
            migrated["day_results"] = []
            for key in (
                "current_day",
                "current_day_operating_result_eur",
                "current_day_priced_charge_kwh",
                "current_day_unpriced_charge_kwh",
                "current_day_priced_discharge_kwh",
                "current_day_unpriced_discharge_kwh",
                "current_day_observed_seconds",
            ):
                migrated[key] = None
        return migrated


class EconomicsStateStore:
    """Persist the operative money balance per config entry.

    Home Assistants `Store` fängt eine echte `WriteError`/
    `SerializationError` beim Schreiben intern ab und protokolliert sie
    nur (`Store._async_handle_write_data`) - weder `Store.async_save()`
    noch der über `Store.async_delay_save()` verzögerte Schreibpfad melden
    einen solchen Fehler an den Aufrufer zurück. Damit ein echter
    Festplattenfehler trotzdem beobachtbar bleibt, verzichtet diese Klasse
    bewusst auf `Store.async_delay_save()` und verwaltet die Verzögerung
    selbst (`async_call_later`): Nach jedem Schreibversuch liest
    `_write_and_verify` den soeben geschriebenen Schlüssel über die
    öffentliche `Store.async_load()`-API zurück und vergleicht ihn mit den
    beabsichtigten Daten - eine schweigend verschluckte `WriteError` lässt
    die Datei unverändert und wird dadurch als Abweichung sichtbar. Für
    den zeitversetzten Pfad gibt es dafür keinen synchronen Rückgabewert
    mehr (der eigentliche Schreibvorgang findet erst nach der Verzögerung
    statt) - ein tatsächlicher Fehlschlag wird stattdessen über den
    optionalen `on_persist_failed`-Callback gemeldet.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        on_persist_failed: Callable[[], None] | None = None,
    ) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = _EconomicsStore(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry_id}",
            minor_version=STORAGE_MINOR_VERSION,
        )
        self._last_persisted = EconomicsState()
        self._pending: EconomicsState | None = None
        self._unsub_delayed_write: CALLBACK_TYPE | None = None
        # Sicherheitsnetz analog zu Store._async_ensure_final_write_listener:
        # nur registriert, während ein verzögerter Schreibvorgang aussteht
        # (siehe async_delay_save/_cancel_delayed_write) - schreibt ihn
        # sofort, falls Home Assistant vor Ablauf der Verzögerung
        # herunterfährt. Ohne dieses Sicherheitsnetz bliebe sowohl ein
        # letzter Schreibvorgang verloren als auch ein über das
        # Programmende hinaus offener Low-Level-Timer bestehen (sichtbar
        # z. B. als "Lingering timer" in Tests).
        self._unsub_final_write_listener: CALLBACK_TYPE | None = None
        self._on_persist_failed = on_persist_failed
        # Serialisiert die komplette save-then-load-Sequenz aus
        # _write_and_verify pro Instanz: Store._data wird von
        # Store.async_save() SOFORT überschrieben, unabhängig von einem
        # eventuell noch laufenden anderen Schreibvorgang (nur die
        # eigentliche Schreib-E/A ist über Store._write_lock serialisiert,
        # nicht diese Zuweisung) - ohne dieses Lock könnte ein zweiter,
        # überlappender Schreibversuch (z. B. ein bereits laufender
        # verzögerter Write parallel zu async_reset()/dem Shutdown-Flush)
        # Store.async_load() nach dem ersten Write dessen eigene, noch
        # ausstehende Daten statt der soeben geschriebenen zurückgeben
        # lassen und den ersten, tatsächlich erfolgreichen Write fälschlich
        # als fehlgeschlagen melden.
        self._write_and_verify_lock = asyncio.Lock()

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
            operating_result_high_water_eur=self._validated_nonnegative(
                raw.get("operating_result_high_water_eur"),
                "Netto-Ersparnis-Höchststand",
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
            day_results=self._validated_day_results(raw.get("day_results")),
            payback_achieved_at=self._validated_timestamp(
                raw.get("payback_achieved_at"), "Payback-Erreichungszeitpunkt"
            ),
            priced_charge_kwh=self._validated_nonnegative(
                raw.get("priced_charge_kwh"), "Bepreiste Ladung"
            ),
            priced_discharge_kwh=self._validated_nonnegative(
                raw.get("priced_discharge_kwh"), "Bepreiste Entladung"
            ),
            last_restart_at=self._validated_timestamp(
                raw.get("last_restart_at"), "letzter Bilanzneustart"
            ),
            last_restart_reason=self._validated_restart_reason(
                raw.get("last_restart_reason")
            ),
            **self._validated_current_day(raw),
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
            state.operating_result_high_water_eur,
            state.unvalued_inventory_kwh,
            state.unpriced_charge_kwh,
            state.unpriced_discharge_kwh,
            state.economics_started_at,
            # priced_charge_kwh/priced_discharge_kwh gehören NICHT zu
            # `initialized` (sie kamen später dazu und dürfen einen sonst
            # vollständigen Snapshot nicht entwerten), unterliegen in
            # _accept aber derselben Monotonieprüfung wie die beiden
            # unpriced_*-Zähler. Blieben sie hier stehen, während der
            # Coordinator die Bilanz bei 0 neu startet, würde jeder
            # Speicherversuch als "rückläufig" abgelehnt und die Bilanz
            # dauerhaft in storage_error einfrieren - ein Reload hilft
            # nicht, weil die Datei unverändert bleibt.
            state.priced_charge_kwh,
            state.priced_discharge_kwh,
            # Ein Payback-Zeitpunkt gehört zur alten, unvollständigen Bilanz.
            # Bliebe er in der Baseline stehen, würde der neue Bootstrap mit
            # payback_achieved_at=None als unzulässige Rücknahme abgelehnt.
            state.payback_achieved_at,
        )
        if all(value is None for value in fields):
            return state
        return replace(
            state,
            grid_charge_cost_eur=None,
            pv_opportunity_cost_eur=None,
            avoided_grid_cost_eur=None,
            operating_result_high_water_eur=None,
            unvalued_inventory_kwh=None,
            unpriced_charge_kwh=None,
            unpriced_discharge_kwh=None,
            economics_started_at=None,
            priced_charge_kwh=None,
            priced_discharge_kwh=None,
            payback_achieved_at=None,
        )

    @callback
    def async_delay_save(
        self, state: EconomicsState, delay: float = ECONOMICS_SAVE_DELAY
    ) -> bool:
        """Coalesce frequent balance changes into one delayed write.

        Der Rückgabewert deckt ausschließlich die sofortige `_accept()`-
        Plausibilitätsprüfung ab - der eigentliche Schreibversuch (und
        damit ein möglicher echter Fehlschlag) findet erst nach `delay`
        Sekunden statt und wird über `on_persist_failed` gemeldet, siehe
        Klassen-Docstring.
        """
        if not self._accept(state):
            return False
        self._pending = state
        if self._unsub_delayed_write is None:
            self._unsub_delayed_write = async_call_later(
                self._hass, delay, self._async_delayed_write
            )
            self._async_ensure_final_write_listener()
        return True

    @callback
    def _async_ensure_final_write_listener(self) -> None:
        if self._unsub_final_write_listener is None:
            self._unsub_final_write_listener = self._hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_FINAL_WRITE, self._async_handle_final_write
            )

    @callback
    def _async_cleanup_final_write_listener(self) -> None:
        if self._unsub_final_write_listener is not None:
            self._unsub_final_write_listener()
            self._unsub_final_write_listener = None

    async def _async_handle_final_write(self, _event: Any) -> None:
        """Home Assistant fährt herunter, bevor die Verzögerung abgelaufen
        ist - denselben ausstehenden Stand sofort schreiben, statt ihn zu
        verlieren (siehe _unsub_final_write_listener-Kommentar)."""
        self._unsub_final_write_listener = None
        if self._unsub_delayed_write is not None:
            self._unsub_delayed_write()
        await self._async_delayed_write(dt_util.utcnow())

    async def _async_delayed_write(self, _now: datetime) -> None:
        """Vom `async_call_later`-Timer (oder dem Sicherheitsnetz
        `_async_handle_final_write`) aufgerufen - schreibt den zuletzt
        koaleszierten Stand und meldet einen tatsächlichen Fehlschlag über
        `_on_persist_failed`, da hier (anders als bei `async_save`/
        `async_reset`) kein Aufrufer mehr auf einen Rückgabewert wartet."""
        self._unsub_delayed_write = None
        self._async_cleanup_final_write_listener()
        state = self._pending
        self._pending = None
        if state is None:
            return
        if not await self._write_and_verify(state) and self._on_persist_failed:
            self._on_persist_failed()

    async def async_save(self, state: EconomicsState) -> bool:
        """Immediately persist a final snapshot, cancelling a delayed write."""
        if not self._accept(state):
            return False
        self._cancel_delayed_write()
        return await self._write_and_verify(state)

    async def async_reset(self, state: EconomicsState) -> bool:
        """Persist a deliberate restart (REQ-ECONOMICS-OBSERVABILITY,
        `sax_power.restart_economics_accounting`), bypassing die
        Monotonie-/Unveränderlichkeits-Baseline aus _accept.

        Ein kontrollierter Neustart setzt die sonst zu Recht geschützten
        monotonen Zähler (unpriced_charge_kwh, priced_charge_kwh, ...) und
        die sonst unveränderlichen Zeitstempel (economics_started_at,
        payback_achieved_at) bewusst zurück - das ist kein Korruptionsindiz
        wie ein spontan rückläufiger Wert außerhalb dieses expliziten
        Aufrufs. Nur die strukturelle Gültigkeit (endlich, Wertebereich)
        wird weiterhin geprüft, damit ein Programmierfehler trotzdem nicht
        zu einem korrupten Store führen kann.
        """
        if not self._valid_snapshot(state):
            return False
        self._cancel_delayed_write()
        return await self._write_and_verify(state)

    def _cancel_delayed_write(self) -> None:
        self._pending = None
        if self._unsub_delayed_write is not None:
            self._unsub_delayed_write()
            self._unsub_delayed_write = None
        self._async_cleanup_final_write_listener()

    async def _write_and_verify(self, state: EconomicsState) -> bool:
        """Persist `state` and read the key back to confirm the write
        actually reached disk (siehe Klassen-Docstring) - der einzige über
        die öffentliche `Store`-API beobachtbare Nachweis, da ein
        schweigend verschluckter Schreibfehler die Datei unverändert
        lässt: `written` weicht dann von den gerade geschriebenen Daten ab
        (oder bleibt bei einem allerersten Schreibversuch `None`).

        Die gesamte Sequenz läuft unter `_write_and_verify_lock`, damit ein
        zweiter, überlappender Aufruf (siehe dessen Kommentar in
        `__init__`) nicht zwischen diesen Save- und Load-Aufruf geraten
        kann.
        """
        async with self._write_and_verify_lock:
            data = self._serialize(state)
            try:
                await self._store.async_save(data)
                written = await self._store.async_load()
            except (HomeAssistantError, OSError) as err:
                _LOGGER.warning(
                    "Wirtschaftlichkeitszustand konnte nicht gespeichert werden: %s",
                    err,
                )
                return False
            if written != data:
                _LOGGER.warning(
                    "Wirtschaftlichkeitszustand nach dem Speichern nicht wie "
                    "erwartet lesbar - Schreibvorgang vermutlich fehlgeschlagen"
                )
                return False
            self._last_persisted = state
            return True

    @staticmethod
    def _valid_snapshot(state: EconomicsState) -> bool:
        """Rein strukturelle Prüfung (endlich, Wertebereich) ohne jeden
        Vergleich gegen eine Baseline - siehe _accept/async_reset."""
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
        for label, value in (
            (
                "Netto-Ersparnis-Höchststand",
                state.operating_result_high_water_eur,
            ),
            ("Unbewerteter Bestand", state.unvalued_inventory_kwh),
            ("Unbepreiste Ladung", state.unpriced_charge_kwh),
            ("Unbepreiste Entladung", state.unpriced_discharge_kwh),
            ("Bepreiste Ladung", state.priced_charge_kwh),
            ("Bepreiste Entladung", state.priced_discharge_kwh),
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
        return True

    def _accept(self, state: EconomicsState) -> bool:
        """Feldweise Plausibilitätsprüfung vor dem Schreiben.

        Die drei Geldsummen dürfen wegen negativer Preise schwanken und
        sinken - hier nur Endlichkeit prüfen (_valid_snapshot), kein
        Monotonie-Vergleich. operating_result_high_water_eur sowie
        unpriced_charge_kwh/unpriced_discharge_kwh/ priced_charge_kwh/
        priced_discharge_kwh bleiben dagegen monoton. economics_started_at/
        payback_achieved_at sind einmalig gesetzte Konstanten. Ein
        gewollter Bilanzneustart (async_reset) umgeht diese Prüfungen
        bewusst.
        """
        if not self._valid_snapshot(state):
            return False
        baseline = self._pending or self._last_persisted
        for label, value, previous in (
            (
                "Netto-Ersparnis-Höchststand",
                state.operating_result_high_water_eur,
                baseline.operating_result_high_water_eur,
            ),
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
            (
                "Bepreiste Ladung",
                state.priced_charge_kwh,
                baseline.priced_charge_kwh,
            ),
            (
                "Bepreiste Entladung",
                state.priced_discharge_kwh,
                baseline.priced_discharge_kwh,
            ),
        ):
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
        if (
            baseline.payback_achieved_at is not None
            and state.payback_achieved_at != baseline.payback_achieved_at
        ):
            _LOGGER.warning(
                "Abweichenden Payback-Erreichungszeitpunkt verworfen: %r " "statt %r",
                state.payback_achieved_at,
                baseline.payback_achieved_at,
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
    def _validated_positive(value: Any, label: str) -> float | None:
        """Wie _validated_nonnegative, aber ohne die 0: eine Tageslänge
        von 0 Sekunden wäre als Nenner der Zeitabdeckung sinnlos."""
        if (
            value is None
            or isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(value)
            or value <= 0
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
    def _validated_date(value: Any, label: str) -> date | None:
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        _LOGGER.warning(
            "Ungültiges gespeichertes Datum für %s verworfen: %r", label, value
        )
        return None

    @staticmethod
    def _validated_restart_reason(value: Any) -> str | None:
        """Rein diagnostischer Freitext (siehe EconomicsState.
        last_restart_reason) - nur Typ und Länge werden geprüft, kein
        Inhalt."""
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            _LOGGER.warning(
                "Ungültigen gespeicherten Bilanzneustart-Grund verworfen: %r",
                value,
            )
            return None
        return value[:MAX_ECONOMICS_RESTART_REASON_LENGTH]

    @classmethod
    def _validated_day_results(cls, value: Any) -> tuple[DayEconomicsResult, ...]:
        """Abgeschlossene Kalendertage, jeder für sich validiert.

        Ein einzelner kaputter Tageseintrag verwirft nur sich selbst - ein
        Tag ist dabei ein eigenes atomares Bündel (siehe
        DayEconomicsResult): Ein Datum ohne brauchbare Beträge (oder
        umgekehrt) ist als Ganzes nicht aussagekräftig. Mehrere Einträge
        zum selben Datum (aus einem von Hand bearbeiteten Store) behalten
        nur den zuletzt genannten.
        """
        if not isinstance(value, list):
            if value is not None:
                _LOGGER.warning(
                    "Ungültige gespeicherte Tageshistorie verworfen: %r", value
                )
            return ()
        by_day: dict[date, DayEconomicsResult] = {}
        for entry in value:
            day_result = cls._validated_day_result(entry)
            if day_result is not None:
                by_day[day_result.day] = day_result
        # Verteidigung gegen einen von Hand über MAX_STORED_DAYS hinaus
        # erweiterten Store - im Normalbetrieb trimmt bereits der
        # Coordinator beim Anhängen eines neuen Tages (siehe
        # SaxPowerCoordinator._close_economics_day).
        ordered_days = sorted(by_day)[-MAX_STORED_DAYS:]
        return tuple(by_day[day] for day in ordered_days)

    @classmethod
    def _validated_day_result(cls, entry: Any) -> DayEconomicsResult | None:
        if not isinstance(entry, dict):
            _LOGGER.warning("Ungültigen Tageseintrag verworfen: kein Objekt: %r", entry)
            return None
        day = cls._validated_date(entry.get("day"), "Tagesdatum")
        operating_result = cls._validated_amount(
            entry.get("operating_result_eur"), "Tagesergebnis"
        )
        priced_charge = cls._validated_nonnegative(
            entry.get("priced_charge_kwh"), "Bepreiste Tagesladung"
        )
        unpriced_charge = cls._validated_nonnegative(
            entry.get("unpriced_charge_kwh"), "Unbepreiste Tagesladung"
        )
        priced_discharge = cls._validated_nonnegative(
            entry.get("priced_discharge_kwh"), "Bepreiste Tagesentladung"
        )
        unpriced_discharge = cls._validated_nonnegative(
            entry.get("unpriced_discharge_kwh"), "Unbepreiste Tagesentladung"
        )
        # Ein Store aus der Zeit vor der Zeitabdeckung (Issue #131) kennt
        # die beiden Felder noch nicht. Ein solcher Tag wird NICHT
        # verworfen - er bleibt als Historie sichtbar, gilt aber mit 0
        # beobachteten Sekunden als unvollständig und kommt damit erst
        # wieder für eine Prognose in Frage, wenn 30 neue, tatsächlich
        # beobachtete Tage vorliegen. Ein vorhandener, aber ungültiger Wert
        # bleibt dagegen ein Korruptionsindiz und verwirft den ganzen Tag.
        observed_seconds = (
            0.0
            if "observed_seconds" not in entry
            else cls._validated_nonnegative(
                entry.get("observed_seconds"), "Beobachtete Tagesdauer"
            )
        )
        day_length_seconds = (
            SECONDS_PER_DAY
            if "day_length_seconds" not in entry
            else cls._validated_positive(entry.get("day_length_seconds"), "Tageslänge")
        )
        if (
            day is None
            or operating_result is None
            or priced_charge is None
            or unpriced_charge is None
            or priced_discharge is None
            or unpriced_discharge is None
            or observed_seconds is None
            or day_length_seconds is None
        ):
            _LOGGER.warning("Unvollständigen Tageseintrag verworfen: %r", entry)
            return None
        return DayEconomicsResult(
            day=day,
            operating_result_eur=operating_result,
            priced_charge_kwh=priced_charge,
            unpriced_charge_kwh=unpriced_charge,
            priced_discharge_kwh=priced_discharge,
            unpriced_discharge_kwh=unpriced_discharge,
            observed_seconds=observed_seconds,
            day_length_seconds=day_length_seconds,
        )

    @classmethod
    def _validated_current_day(cls, raw: dict[str, Any]) -> dict[str, Any]:
        """Der noch laufende Tag als eigenes Sieben-Felder-Bündel (siehe
        EconomicsState.current_day). Ist auch nur ein Feld ungültig oder
        fehlt es, gilt der ganze angefangene Tag als nicht aussagekräftig
        und startet beim nächsten Datenpunkt frisch - die abgeschlossene
        Historie (day_results) bleibt davon unberührt. Das gilt bewusst
        auch für die beobachtete Dauer aus einem älteren Store (Issue
        #131): ein angefangener Tag ohne bekannte Beobachtungsdauer würde
        sonst mit einer erfundenen Abdeckung abgeschlossen - anders als bei
        den bereits abgeschlossenen Tagen kostet ein Neustart hier nur den
        laufenden, ohnehin unvollständigen Tag.
        """
        fields = {
            "current_day": cls._validated_date(raw.get("current_day"), "Laufender Tag"),
            "current_day_operating_result_eur": cls._validated_amount(
                raw.get("current_day_operating_result_eur"), "Laufendes Tagesergebnis"
            ),
            "current_day_priced_charge_kwh": cls._validated_nonnegative(
                raw.get("current_day_priced_charge_kwh"), "Laufende bepreiste Ladung"
            ),
            "current_day_unpriced_charge_kwh": cls._validated_nonnegative(
                raw.get("current_day_unpriced_charge_kwh"),
                "Laufende unbepreiste Ladung",
            ),
            "current_day_priced_discharge_kwh": cls._validated_nonnegative(
                raw.get("current_day_priced_discharge_kwh"),
                "Laufende bepreiste Entladung",
            ),
            "current_day_unpriced_discharge_kwh": cls._validated_nonnegative(
                raw.get("current_day_unpriced_discharge_kwh"),
                "Laufende unbepreiste Entladung",
            ),
            "current_day_observed_seconds": cls._validated_nonnegative(
                raw.get("current_day_observed_seconds"),
                "Laufende beobachtete Tagesdauer",
            ),
        }
        if any(value is None for value in fields.values()):
            return dict.fromkeys(fields)
        return fields

    @staticmethod
    def _serialize(state: EconomicsState) -> dict[str, Any]:
        return {
            "grid_charge_cost_eur": state.grid_charge_cost_eur,
            "pv_opportunity_cost_eur": state.pv_opportunity_cost_eur,
            "avoided_grid_cost_eur": state.avoided_grid_cost_eur,
            "operating_result_high_water_eur": state.operating_result_high_water_eur,
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
            "day_results": [
                {
                    "day": day.day.isoformat(),
                    "operating_result_eur": day.operating_result_eur,
                    "priced_charge_kwh": day.priced_charge_kwh,
                    "unpriced_charge_kwh": day.unpriced_charge_kwh,
                    "priced_discharge_kwh": day.priced_discharge_kwh,
                    "unpriced_discharge_kwh": day.unpriced_discharge_kwh,
                    "observed_seconds": day.observed_seconds,
                    "day_length_seconds": day.day_length_seconds,
                }
                for day in state.day_results
            ],
            "current_day": (
                state.current_day.isoformat() if state.current_day is not None else None
            ),
            "current_day_operating_result_eur": state.current_day_operating_result_eur,
            "current_day_priced_charge_kwh": state.current_day_priced_charge_kwh,
            "current_day_unpriced_charge_kwh": state.current_day_unpriced_charge_kwh,
            "current_day_priced_discharge_kwh": state.current_day_priced_discharge_kwh,
            "current_day_unpriced_discharge_kwh": (
                state.current_day_unpriced_discharge_kwh
            ),
            "current_day_observed_seconds": state.current_day_observed_seconds,
            "payback_achieved_at": (
                state.payback_achieved_at.isoformat()
                if state.payback_achieved_at is not None
                else None
            ),
            "priced_charge_kwh": state.priced_charge_kwh,
            "priced_discharge_kwh": state.priced_discharge_kwh,
            "last_restart_at": (
                state.last_restart_at.isoformat()
                if state.last_restart_at is not None
                else None
            ),
            "last_restart_reason": state.last_restart_reason,
        }
