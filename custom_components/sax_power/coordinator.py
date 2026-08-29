"""DataUpdateCoordinator for the SAX Power integration."""

from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import Mapping
from dataclasses import replace
from datetime import date, datetime, timedelta
from datetime import time as dt_time
from time import monotonic
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from pymodbus.exceptions import ModbusException

from .application.calibration import CalibrationState, evaluate_calibration
from .application.charge_policy import ChargePolicyInput, evaluate_charge_policy
from .application.economics import (
    investment_cost_eur_from_options,
    prior_result_eur_from_options,
)
from .application.ports import ModbusClient
from .const import (
    ALL_MONTHS,
    CELL_CALIBRATION_INTERVAL,
    CHARGE_CONFLICT_ISSUES,
    CONTROL_MODE_LABELS,
    DEFAULT_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    DEFAULT_PRICE_HOURS,
    DEFAULT_PRICE_STRATEGY,
    DOMAIN,
    ECONOMICS_PRICE_UNAVAILABLE_GRACE_PERIOD,
    GRID_CHARGE_WRITE_INTERVAL,
    ISSUE_CONTROL_CONFIG_UNREADABLE,
    ISSUE_CONTROL_CONFIG_UNRESOLVED,
    ISSUE_EXTENDED_MODE_UNAVAILABLE,
    ISSUE_PRICE_CHARGE_CONFLICT,
    ISSUE_TIMED_CHARGE_CONFLICT,
    MAX_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    MAX_IC_POWER_SETPOINT_PCT,
    MAX_MANUAL_CHARGE_POWER,
    MAX_PRICE_HOURS,
    MAX_PRICE_LIMIT,
    MAX_SOC,
    MIN_GRID_SERVING_FORECAST_THRESHOLD_KWH,
    MIN_IC_POWER_SETPOINT_PCT,
    MIN_PRICE_HOURS,
    MIN_PRICE_LIMIT,
    MIN_SETPOINT_POWER,
    MIN_SOC,
    PRICE_STATUS_CHARGING,
    PRICE_STATUS_NO_PRICE_DATA,
    PRICE_STATUS_OFF,
    PRICE_STATUS_PAUSED_GRID_SERVING,
    PRICE_STATUS_PAUSED_MAX_SOC,
    PRICE_STATUS_PAUSED_NEUTRAL_BAND,
    PRICE_STATUS_PAUSED_PV_SURPLUS,
    PRICE_STATUS_PAUSED_TIMED_CHARGE,
    PRICE_STATUS_PV_FORECAST_COVERS,
    PRICE_STRATEGIES,
    PRICE_STRATEGY_OFF,
    PV_SURPLUS_HYSTERESIS_CYCLES,
    READ_BLOCK_COUNT,
    READ_BLOCK_EXT_COUNT,
    READ_BLOCK_EXT_HIGH_INTERVAL,
    READ_BLOCK_EXT_LOW1_COUNT,
    READ_BLOCK_EXT_LOW1_START,
    READ_BLOCK_EXT_LOW2_COUNT,
    READ_BLOCK_EXT_LOW2_START,
    READ_BLOCK_EXT_LOW_INTERVAL,
    READ_BLOCK_EXT_START,
    READ_BLOCK_START,
    REG_SETPOINT_COSPHI,
    REG_SETPOINT_POWER,
    REG_SOC,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
    REG_SWITCH_STATE,
    SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
    SUN_IC_CONTROL_MODE_SETPOINT,
    SUN_IC_CONTROL_MODE_SMARTMETER,
    SUN_IC_MIN_WRITE_INTERVAL,
    SWITCH_STATE_LABELS,
    SWITCH_STATE_UNKNOWN_LABEL,
    UNKNOWN_LABEL,
)
from .domain.economics_accounting import (
    EconomicsDelta,
    capacity_inventory_correction,
    compute_economics_delta,
    compute_operating_result_high_water,
    min_soc_inventory_correction,
)
from .domain.economics_amortization import (
    MAX_STORED_DAYS,
    DayEconomicsResult,
    compute_amortization_progress_percent,
    compute_remaining_to_payback_eur,
    compute_roi_percent,
)
from .domain.economics_status import (
    compute_economics_status,
    compute_price_coverage_percent,
)
from .domain.energy_accounting import EnergyDelta, compute_charge_delta
from .domain.registers import (
    to_signed16,
    to_unsigned16,
)
from .domain.scheduling import is_time_in_window, windows_overlap
from .domain.sunspec import (
    DEFAULT_BATTERY_SCALE_FACTORS,
    DEFAULT_IC_POWER_SETPOINT_SF_RAW,
    decode_high_block,
    decode_low_blocks,
)
from .domain.tariff import (
    QuoteResult,
    QuoteUnavailable,
    TariffType,
    active_window,
    sorted_windows,
    window_as_mapping,
)
from .domain.validation import clamp_float as _clamp_float
from .domain.validation import clamp_int as _clamp_int
from .domain.validation import round_half_up
from .economics import SaxTariffProvider
from .infrastructure.calibration_store import CalibrationStateStore
from .infrastructure.control_store import (
    ControlConfig,
    ControlConfigLoadStatus,
    ControlConfigStore,
)
from .infrastructure.economics_store import (
    STORAGE_MINOR_VERSION as ECONOMICS_STORE_MINOR_VERSION,
)
from .infrastructure.economics_store import EconomicsState, EconomicsStateStore
from .infrastructure.energy_store import EnergyState, EnergyStateStore
from .infrastructure.self_diagnostics import DiagnosticSnapshot, SelfDiagnostics
from .price_optimizer import PricePlan, SaxPricePlanner

_LOGGER = logging.getLogger(__name__)

#: Raster (Sekunden), in dem allein die fortlaufende Beobachtungsdauer des
#: laufenden Tages ein verzögertes Speichern auslöst. Sie wächst bei JEDEM
#: verbuchten Intervall; ohne dieses Raster schriebe der Store auch auf
#: einem völlig ruhenden System dauerhaft alle ECONOMICS_SAVE_DELAY
#: Sekunden (Flash-Verschleiß auf SD-Karten-Installationen). 15 Minuten
#: sind rund 1 % eines Kalendertages. Mehr Beobachtungsdauer kann ein
#: ungeplanter Neustart nicht verlieren. Jede andere
#: Änderung (Geld, Energie, Tagesabschluss) speichert unverändert sofort
#: und nimmt den aktuellen Stand dabei ohnehin mit.
OBSERVED_TIME_SAVE_GRANULARITY_SECONDS = 900.0

#: Mindestabstand zwischen zwei Log-Zeilen der Bestandsdeckelung
#: (capacity_inventory_correction, REQ-ECONOMICS-ACCOUNTING). Der Deckel
#: kann bei mehreren bestätigten, sinkenden SOC-Stufen wiederholt greifen -
#: ungedrosselt entstünden daraus viele identische INFO-Zeilen. Die
#: kumulierte Korrekturmenge steht
#: unabhängig davon jederzeit vollständig im Diagnose-Download.
INVENTORY_CAP_LOG_INTERVAL_SECONDS = 3600.0

# Nach einer Bewegung kann der quantisierte SOC noch denselben alten Wert
# melden. Zwei aufeinanderfolgende frische Stillstands-Ticks verhindern, dass
# gerade nachweislich geladene unbepreiste Energie gelöscht wird (Issue #145).
INVENTORY_CORRECTION_IDLE_CONFIRMATIONS = 2


def _rounded(value: float | None, digits: int) -> float | None:
    """Auf `digits` gerundeter Geld-/Prozentwert ohne negative Null.

    `round(-0.0001, 2)` ergibt -0.0, und Home Assistant zeigt das als
    "-0,0" an - ein Vorzeichen, das dem Anwender einen Verlust meldet, den
    die gerundete Zahl selbst gar nicht mehr ausweist. Die Normalisierung
    bleibt für negative Ergebnis- und Kostenwerte nötig. Der Vergleich
    `== 0` trifft +0.0 und -0.0 gleichermaßen und lässt jeden tatsächlich
    von 0 verschiedenen Wert unangetastet.
    """
    if value is None:
        return None
    rounded = round(value, digits)
    return 0.0 if rounded == 0 else rounded


def _economics_capacity_kwh(capacity_wh: Any) -> float | None:
    """Speicherkapazität (Wh) als kWh, oder None bei unbekanntem Rohwert.

    Eine gemeldete Kapazität von 0 (oder negativ) ist kein plausibler
    Messwert, sondern ein noch nicht gefüllter bzw. gestörter
    SunSpec-Block. Sie darf den internen unbewerteten Bestand nicht auf 0
    deckeln - das verwürfe eine während einer Preislücke tatsächlich
    geladene Energiemenge.
    price_optimizer._context behandelt denselben Rohwert aus demselben
    Grund als unbekannt.
    """
    if capacity_wh is None or capacity_wh <= 0:
        return None
    return float(capacity_wh) / 1000


_MONTH_NAMES_DE = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}

# Anzeigenamen für ISSUE_CONTROL_CONFIG_UNRESOLVED (siehe
# SaxPowerCoordinator._async_sync_unresolved_fields_issue) - dieselben
# Feldnamen wie infrastructure/control_store.CONTROL_MIGRATABLE_FIELDS,
# hier auf die deutschen Entity-Namen abgebildet, wie sie der Anwender in
# der Oberfläche sieht.
_CONTROL_FIELD_LABELS = {
    "max_soc": "Max. SOC",
    "timed_charge_enabled": "Netzladung aktiv",
    "timed_charge_start": "Netzladung Start",
    "timed_charge_end": "Netzladung Ende",
    "timed_charge_months": "Netzladung Aktive Monate",
    "timed_charge_min_soc": "Netzladung Min. SOC",
    "grid_serving_enabled": "Netzdienliches Laden aktiv",
    "grid_serving_start": "Netzdienliches Laden Start",
    "grid_serving_end": "Netzdienliches Laden Ende",
    "grid_serving_months": "Netzdienliches Laden Aktive Monate",
    "grid_serving_forecast_threshold_kwh": (
        "Netzdienliches Laden PV-Prognose-Mindestwert"
    ),
    "price_charge_enabled": "Preisoptimiertes Laden aktiv",
    "price_charge_strategy": "Preisoptimiertes Laden Strategie",
    "price_charge_max_price": "Preisoptimiertes Laden Preisgrenze",
    "price_charge_neutral_price": "Preisoptimiertes Laden Neutralpreis",
    "price_charge_hours": "Preisoptimiertes Laden Anzahl Stunden",
}


def _format_window_for_message(
    start: dt_time | None, end: dt_time | None, months: set[int]
) -> str:
    """Menschenlesbare Beschreibung eines Zeitfensters (Tageszeit + aktive
    Monate) für die Überschneidungs-Benachrichtigung (siehe
    SaxPowerCoordinator._notify_time_window_overlap)."""
    if start is None or end is None:
        return "kein Zeitfenster gesetzt"
    time_part = f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"
    if months >= ALL_MONTHS:
        months_part = "ganzjährig"
    elif not months:
        months_part = "keine aktiven Monate"
    else:
        months_part = "aktiv: " + ", ".join(
            _MONTH_NAMES_DE[month] for month in sorted(months)
        )
    return f"{time_part} ({months_part})"


def _format_kwh(value: float) -> str:
    """Formatiert kWh ohne technisch bedingte Nachkommastellen."""
    return f"{value:.10f}".rstrip("0").rstrip(".")


def _grid_serving_pause_status(
    *,
    now: datetime,
    enabled: bool,
    start: dt_time | None,
    end: dt_time | None,
    months: set[int],
    forecast_sensor_configured: bool,
    forecast_kwh: float | None,
    threshold_kwh: float,
) -> str:
    """Ermittelt den sichtbaren Ladepausen-Status gemäß REQ-GRID-SERVING-CHARGE."""
    month_name = _MONTH_NAMES_DE[now.month]
    if not enabled:
        return "Inaktiv"
    if now.month not in months:
        return f"Inaktiv im Monat {month_name}"
    if not is_time_in_window(now.time(), start, end):
        return "Außerhalb des Zeitfensters"
    if threshold_kwh > 0 and forecast_sensor_configured and forecast_kwh is None:
        return "PV-Prognose nicht verfügbar"

    assert start is not None and end is not None
    active = (
        f"Ladepause ist zwischen {start.strftime('%H:%M')} Uhr und "
        f"{end.strftime('%H:%M')} Uhr im {month_name} aktiv."
    )
    if threshold_kwh <= 0 or not forecast_sensor_configured:
        return active

    assert forecast_kwh is not None
    forecast_text = _format_kwh(forecast_kwh)
    threshold_text = _format_kwh(threshold_kwh)
    if forecast_kwh < threshold_kwh:
        return (
            "Ladepause inaktiv, da die PV-Prognose von "
            f"{forecast_text} kWh kleiner als der Mindestwert von "
            f"{threshold_text} kWh ist."
        )
    comparison = "gleich dem" if forecast_kwh == threshold_kwh else "größer als der"
    return (
        f"{active} Die PV-Prognose von {forecast_text} kWh ist {comparison} "
        f"Mindestwert von {threshold_text} kWh."
    )


class SaxPowerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates Modbus reads/writes for a SAX Power storage system."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ModbusClient,
        slave_id: int,
        slave_id_extended: int,
        scan_interval: int,
        entry_id: str,
        options: Mapping[str, Any] | None = None,
    ) -> None:
        # Der Coordinator-Timer läuft mit dem kürzeren der beiden Intervalle,
        # damit weder der feste HIGH- noch der nutzerkonfigurierte
        # NORMAL-Poll-Zyklus verpasst wird - _async_read_basic/
        # _async_read_extended prüfen anschließend jeweils eigenständig
        # (per Zeitstempel), ob ihr Teilblock auf einem gegebenen Tick
        # tatsächlich fällig ist. Siehe const.READ_BLOCK_EXT_HIGH_INTERVAL
        # sowie anforderung.yaml, REQ-HIGH-INTERVAL-REGISTERS.
        super().__init__(
            hass,
            _LOGGER,
            name="SAX Power",
            update_interval=timedelta(
                seconds=min(scan_interval, READ_BLOCK_EXT_HIGH_INTERVAL)
            ),
        )
        self.client = client
        self.slave_id = slave_id
        self.slave_id_extended = slave_id_extended
        self.entry_id = entry_id
        # Options-Flow-Konfiguration (Strompreis-/PV-Prognose-Sensor, siehe
        # config_flow.SaxPowerOptionsFlow). __init__.async_update_options
        # ersetzt dieses Mapping bei einer Änderung direkt (kein Config-
        # Entry-Reload mehr, siehe dort) und ruft anschließend
        # price_planner.async_setup() erneut auf, damit hier immer der
        # aktuelle Stand steht.
        self.options: Mapping[str, Any] = dict(options or {})
        self._scan_interval = scan_interval
        self._write_lock = asyncio.Lock()
        # Die beiden Immediate-Control-Register bilden eine logische
        # Sequenz. Periodischer Task und sofortige Sollwertänderung dürfen
        # ihre Mode/Setpoint/Rollback-Writes nicht ineinander verschachteln
        # (REQ-TIMED-SOC-CHARGE).
        self._sun_charge_write_lock = asyncio.Lock()
        # Polling, Entity-Setter und Prognose-Callbacks können dieselbe
        # Ladeentscheidung gleichzeitig anstoßen. Nur eine vollständig
        # ausgewertete Entscheidung darf die SunSpec-Register steuern, sonst
        # kann ein älterer Aktiv-Zweig einen gerade ausgeführten Rücksprung in
        # die Nullregelung wieder überschreiben (REQ-GRID-SERVING-CHARGE).
        self._charge_control_lock = asyncio.Lock()
        self._max_soc: int | None = None
        self._cell_calibration_state = CalibrationState()
        self._cell_calibration_active = False
        self._calibration_store = CalibrationStateStore(hass, entry_id)
        self._energy_store = EnergyStateStore(hass, entry_id)
        self._energy_store_loaded = False
        # Wirtschaftlichkeitsbilanz (REQ-ECONOMICS-ACCOUNTING): eigener
        # Store, eigenes Bootstrap-Fenster - siehe async_load_economics_state
        # und _bootstrap_economics_if_ready weiter unten.
        self._economics_store = EconomicsStateStore(
            hass, entry_id, on_persist_failed=self._on_economics_persist_failed
        )
        self._economics_store_loaded = False
        # Bleibt bis zu einem erfolgreichen Neuladen des Config Entry
        # gesetzt, wenn der vorhandene Store beim Start nicht gelesen
        # werden konnte (siehe async_load_economics_state) - verhindert,
        # dass ein anschließend aus lauter Nullen neu gebootstrapptes
        # Bilanz-Objekt den eigentlich vorhandenen, nur unlesbaren Store
        # überschreibt (analog zu _control_store_write_blocked).
        self._economics_store_write_blocked = False
        # Versionierter, vom sichtbaren Entity-Zustand unabhängiger Snapshot
        # aller softwareseitigen Steuerwerte (REQ-CONTROL-CONFIG-BOOTSTRAP).
        self._control_store = ControlConfigStore(hass, entry_id)
        # MISSING als Ausgangswert: Eine direkt instanziierte
        # Coordinator-Instanz, die async_load_control_state nie aufruft
        # (Tests, Diagnose), verhält sich damit wie ein Eintrag ohne Store -
        # der RestoreEntity-Migrationspfad bleibt für sie offen.
        self._control_config_status = ControlConfigLoadStatus.MISSING
        # Gesetzt, solange ein vorhandener, aber nicht verwertbarer Store
        # nicht automatisch überschrieben werden darf - siehe
        # _async_schedule_control_save.
        self._control_store_write_blocked = False
        # Feldnamen, deren RestoreEntity-Altzustand beim einmaligen
        # Migrieren nicht verwertbar war (unknown/unavailable/unparsebar) -
        # siehe mark_control_field_unresolved/clear_control_field_unresolved
        # sowie anforderung.yaml, REQ-CONTROL-CONFIG-BOOTSTRAP. Bleibt über
        # Neustarts hinweg gesetzt (persistiert in ControlConfig.
        # unresolved_fields), bis die betroffene Einstellung bewusst über
        # ihre Entity neu gesetzt wird - erst das ist ein ausdrücklicher
        # Wert, kein Ratewert.
        self._control_unresolved_fields: set[str] = set()
        # Solange True, darf KEINE Ladeentscheidung das Gerät steuern: der
        # erste Refresh und die (nur noch migrierenden) Entity-Setter würden
        # sonst aus einer Teilkonfiguration heraus schreiben - insbesondere
        # Register 40051 auf Modus 0, obwohl ein gespeichertes Fenster gerade
        # aktiv ist. Wird von async_load_control_state() geöffnet und von
        # async_finish_bootstrap() nach dem Plattform-Setup wieder
        # geschlossen. Default False, damit ein direkt instanziierter
        # Coordinator (Tests, Diagnose) sich unverändert verhält.
        self._control_bootstrap_pending = False
        self._max_soc_clamped = False
        self._max_soc_hold_is_window_bound = False
        self._max_soc_grid_import_wait_cycles = 0
        self._max_soc_released_for_discharge = False
        self._last_effective_max_soc: int | None = None
        # Nicht persistierter Auftrag des kompatiblen start_grid_charge-
        # Service. Die eigentliche Gerätesteuerung läuft ausschließlich über
        # _sun_charge_task und die zentrale Prioritätsentscheidung unter
        # _charge_control_lock (REQ-MANUAL-GRID-CHARGE).
        self._grid_charge_power: int | None = None
        self._timed_charge_enabled = False
        self._timed_charge_start: dt_time | None = None
        self._timed_charge_end: dt_time | None = None
        self._timed_charge_active = False
        self._timed_charge_months: set[int] = set(ALL_MONTHS)
        self._timed_charge_min_soc: int | None = None
        self._timed_charge_armed = False
        self._timed_charge_pv_surplus_cycles = 0
        self._grid_serving_enabled = False
        self._grid_serving_start: dt_time | None = None
        self._grid_serving_end: dt_time | None = None
        self._grid_serving_active = False
        self._grid_serving_months: set[int] = set(ALL_MONTHS)
        self._grid_serving_forecast_threshold_kwh: float | None = None
        self._grid_serving_forecast_kwh: float | None = None
        self._grid_serving_forecast_allowed = True
        self._grid_serving_window_active = False
        self._grid_serving_pause_status_text = "Inaktiv"
        self._grid_serving_setpoint_active = False
        self._grid_serving_wait_cycles = 0
        self._grid_serving_charge_confirm_cycles = 0
        self._grid_serving_release_confirm_cycles = 0
        self._grid_serving_import_confirm_cycles = 0
        # Preisoptimiertes Laden (siehe anforderung.yaml,
        # REQ-DYNAMIC-PRICE-CHARGE): nutzt denselben SunSpec-Schreibpfad
        # (_sun_charge_task) wie zeitgesteuertes/netzdienliches Laden. Der
        # eigentliche Ladeplan liegt im Planner (price_optimizer.py), hier
        # stehen nur die vom Anwender gesetzten Stellgrößen.
        self._price_charge_enabled = False
        self._price_charge_strategy = DEFAULT_PRICE_STRATEGY
        self._price_charge_max_price: float | None = None
        self._price_charge_neutral_price: float | None = None
        self._price_charge_hours: int | None = None
        self._price_charge_active = False
        self._price_charge_status = PRICE_STATUS_OFF
        self.price_planner = SaxPricePlanner(hass, self)
        # Wirtschaftlichkeit: bestimmt den zu einem Zeitpunkt gültigen
        # Netzbezugspreis (REQ-ECONOMICS-TARIFFS). Ohne konfigurierten
        # Tarif liefert er ausschließlich "deaktiviert" und greift in
        # nichts ein - insbesondere nicht in die Ladeplanung.
        self.tariff_provider = SaxTariffProvider(hass, self)
        self._sun_charge_task: asyncio.Task | None = None
        # Bleibt bis zur erfolgreich quittierten Rückkehr in Registermodus 0
        # gesetzt. Dadurch geht der Rücksetzauftrag nach einem transienten
        # Modbus-Fehler nicht zusammen mit der Task-Referenz verloren
        # (REQ-GRID-SERVING-CHARGE).
        self._sun_charge_reset_required = False
        # Letzter von dieser Coordinator-Instanz erfolgreich geschriebener
        # Sollzustand für Register 40051. None bedeutet bewusst "noch nie
        # abgeglichen": Auch eine frisch gestartete, inaktive Instanz
        # schreibt dadurch genau einmal die Nullregelung, statt aus einem
        # leeren Python-Taskzustand fälschlich auf den Gerätezustand zu
        # schließen (REQ-GRID-SERVING-CHARGE).
        self._sun_charge_commanded_mode: int | None = None
        self._sun_charge_command_revision = 0
        self._last_observed_ic_control_mode: int | None = None
        self._sun_charge_power = 0
        self._ic_power_setpoint_sf_raw = DEFAULT_IC_POWER_SETPOINT_SF_RAW
        # Cache für den NORMAL-Block (Basic Mode): _async_read_basic befüllt
        # ihn nur alle self._scan_interval Sekunden neu, unabhängig vom
        # (i. d. R. kürzeren) Coordinator-Timer oben.
        self._basic_data: dict[str, Any] = {}
        self._basic_last_read: float | None = None
        # Cache für den HIGH-Block (SunSpec-Modus, dynamische Werte):
        # _async_read_extended befüllt ihn nur alle
        # READ_BLOCK_EXT_HIGH_INTERVAL Sekunden neu.
        self._high_data: dict[str, Any] = {}
        self._high_last_read: float | None = None
        # Cache für die LOW-Intervall-Register (siehe anforderung.yaml,
        # REQ-LOW-INTERVAL-REGISTERS): _async_read_low_block befüllt sie nur
        # alle READ_BLOCK_EXT_LOW_INTERVAL Sekunden neu; decode_high_block
        # bekommt die Battery-Skalierungsfaktoren aus den zuletzt gelesenen
        # Werten übergeben, statt sie bei jedem Poll erneut zu lesen.
        self._low_block_data: dict[str, Any] = {}
        self._low_block_last_read: float | None = None
        self._battery_scale_factors = DEFAULT_BATTERY_SCALE_FACTORS
        # Energy-Dashboard-Kompatibilität (REQ-ENERGY-DASHBOARD): Der
        # Coordinator hält die abgeleiteten Zähler unabhängig vom sichtbaren
        # RestoreEntity-Zustand in einem versionierten Store. None bedeutet
        # weiterhin "noch nicht initialisiert"; so kann ein nichtnumerischer
        # Altzustand keinen künstlichen Reset auf 0 auslösen.
        self._energy_charged_kwh: float | None = None
        self._energy_discharged_kwh: float | None = None
        self._energy_last_ts: float | None = None
        # Herkunft der Ladeenergie (REQ-ENERGY-ORIGIN): dieselbe
        # None-bis-Initialisierung wie oben, zusätzlich als Dreiergruppe
        # (zwei Zähler + Startzeitpunkt) - siehe
        # _bootstrap_energy_origin sowie EnergyState.origin_initialized.
        self._energy_grid_charged_kwh: float | None = None
        self._energy_pv_charged_kwh: float | None = None
        self._origin_accounting_started_at: datetime | None = None
        # Wirtschaftlichkeitsbilanz (REQ-ECONOMICS-ACCOUNTING): dieselbe
        # None-bis-Bootstrap-Logik, zusätzlich gebunden an
        # SaxTariffProvider.config.enabled - solange der Tarif deaktiviert
        # ist, bleibt die gesamte Bilanz unangetastet (siehe
        # _accumulate_economics). unvalued_inventory_kwh ist der seit dem
        # Bilanzstart nicht bepreiste Energiebestand im Speicher, abzüglich
        # seither entladener unbewerteter Energie. Der beim Start bereits
        # vorhandene Speicherinhalt wird bewusst mit 0 EUR angesetzt und
        # gehört deshalb nicht zu diesem Bestand.
        self._economics_grid_charge_cost_eur: float | None = None
        self._economics_pv_opportunity_cost_eur: float | None = None
        self._economics_avoided_grid_cost_eur: float | None = None
        # Persistierter, nichtnegativer Diagnose-Peak des operativen
        # Ergebnisses. Er bleibt für Store-Kompatibilität und Diagnose
        # erhalten, speist aber keine finanzielle Kennzahl (Issue #144).
        self._economics_operating_result_high_water_eur: float | None = None
        self._economics_unvalued_inventory_kwh: float | None = None
        self._economics_unpriced_charge_kwh: float | None = None
        self._economics_unpriced_discharge_kwh: float | None = None
        self._economics_started_at: datetime | None = None
        self._last_tariff_revision_at: datetime | None = None
        # Reine Diagnose der Bestandsdeckelung (Issue #132): wie viel
        # unbewerteter Bestand seit dem Start dieses Coordinators verworfen
        # wurde und wann darüber zuletzt geloggt wurde (monotonic, siehe
        # INVENTORY_CAP_LOG_INTERVAL_SECONDS). Bewusst nicht persistiert -
        # beides beeinflusst keine Berechnung.
        self._economics_inventory_capped_kwh: float = 0.0
        self._economics_inventory_cap_logged_at: float | None = None
        self._economics_inventory_idle_confirmations = (
            INVENTORY_CORRECTION_IDLE_CONFIRMATIONS
        )
        self._economics_inventory_discharged_since_charge = False
        # ROI und Amortisationsstand (REQ-ECONOMICS-AMORTIZATION): lokale
        # Kalendertag-Buckets, unabhängig vom Sieben-Felder-Bündel oben -
        # siehe _advance_economics_day. day_results sind abgeschlossene
        # Tage (älteste zuerst, höchstens MAX_STORED_DAYS); current_day und
        # die sechs Werte bilden zusammen den noch laufenden Tag und werden
        # nur gemeinsam gesetzt oder verworfen (siehe _start_economics_day).
        self._economics_day_results: tuple[DayEconomicsResult, ...] = ()
        self._economics_current_day: date | None = None
        self._economics_current_day_operating_result_eur: float | None = None
        self._economics_current_day_priced_charge_kwh: float | None = None
        self._economics_current_day_unpriced_charge_kwh: float | None = None
        self._economics_current_day_priced_discharge_kwh: float | None = None
        self._economics_current_day_unpriced_discharge_kwh: float | None = None
        # Tatsächlich beobachtete Zeit des laufenden Tages (Sekunden,
        # Issue #131) - gespeist aus derselben Riemann-Summe wie die
        # Energie selbst (_accumulate_energy), keine zweite Uhr.
        self._economics_current_day_observed_seconds: float | None = None
        # Legacy-Feld aus älteren Stores. Die Prognose wurde entfernt; der
        # Wert wird nur unverändert geladen und gespeichert, damit ein
        # bestehender Store keinen abweichenden Snapshot erhält.
        self._economics_payback_achieved_at: datetime | None = None
        # Datenqualität/Diagnose (REQ-ECONOMICS-OBSERVABILITY): kumulierte,
        # seit economics_started_at tatsächlich bepreiste Lade-/
        # Entlademenge - Gegenstück zu den beiden unpriced-Zählern oben, für
        # charge_price_coverage_percent/discharge_price_coverage_percent.
        self._economics_priced_charge_kwh: float | None = None
        self._economics_priced_discharge_kwh: float | None = None
        # Seit wann ununterbrochen kein gültiger Netzbezugspreis mehr
        # vorlag (monotonic) - None, solange zuletzt ein Preis vorlag.
        # _economics_price_unavailable ist der daraus abgeleitete, fertig
        # ausgewertete Status (Karenzzeit bzw. sofortiger
        # Konfigurationsfehler bei Fest-/Zeitfenstertarif, siehe
        # _update_economics_price_availability) - unabhängig vom
        # persistierten Zustand, nur zur Laufzeit gültig.
        self._economics_price_unavailable_since: float | None = None
        self._economics_price_unavailable = False
        self._economics_last_successful_quote_at: datetime | None = None
        # Zeitpunkt und optionaler Grund des zuletzt ausgeführten
        # kontrollierten Bilanzneustarts (siehe
        # async_restart_economics_accounting) - rein diagnostisch,
        # persistiert für den lokalen Diagnose-Download.
        self._economics_last_restart_at: datetime | None = None
        self._economics_last_restart_reason: str | None = None
        # Basic Mode (Slave-ID self.slave_id) ist die Mindestanforderung für
        # jede Funktion der Integration und lässt das Update fehlschlagen
        # (UpdateFailed), wenn es nicht lesbar ist. Der SunSpec-Modus
        # (Slave-ID self.slave_id_extended, Default 100, siehe modbus.pdf)
        # wird davon bewusst entkoppelt: ist er nicht erreichbar, bleiben
        # die Basic-Mode-Sensoren trotzdem verfügbar und nur die
        # SunSpec-Sensoren zeigen "unbekannt" (siehe anforderung.yaml,
        # REQ-EXTENDED-MODE-RESILIENCE). Vorher führte ein nicht
        # erreichbarer Extended-Mode-Block dazu, dass ConfigEntryNotReady
        # ausgelöst wurde und die Integration gar keine Entities anlegte.
        self._extended_available = True
        # Zeitpunkt (monotonic), seit dem der SunSpec-Modus-Block
        # ununterbrochen nicht erreichbar ist - None, solange er erreichbar
        # ist. Von _async_read_high_block auf der Zustandsflanke gesetzt/
        # zurückgesetzt, von _check_sunspec_persistently_unavailable
        # unten ausgewertet (siehe anforderung.yaml,
        # REQ-SELF-DIAGNOSIS-REPAIRS).
        self._extended_unavailable_since: float | None = None
        self._self_diagnostics = SelfDiagnostics(hass, entry_id)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = dict(await self._async_read_basic())
            data.update(await self._async_read_extended())
        except UpdateFailed:
            # Die Riemann-Baseline darf einen Ausfall nicht überbrücken:
            # _energy_last_ts wird ausschließlich in _accumulate_energy
            # fortgeschrieben, das bei einem fehlgeschlagenen Basic-Read gar
            # nicht mehr erreicht wird. Ohne dieses Verwerfen verbuchte der
            # erste erfolgreiche Tick nach einem stundenlangen Geräte-/
            # Netzausfall die GESAMTE Ausfallzeit mit der zuletzt bekannten
            # Leistung als Energie und zählte sie zusätzlich als beobachtete
            # Zeit des Kalendertages (REQ-ECONOMICS-AMORTIZATION), obwohl in
            # dieser Zeit nichts gemessen wurde - der Tag sähe damit
            # vollständig beobachtet aus, genau den Fall soll die
            # Zeitabdeckung ausschließen.
            self._energy_last_ts = None
            raise
        self._accumulate_energy(data)

        calibration_changed = await self._async_update_cell_calibration(data["soc"])
        if calibration_changed:
            self.price_planner.evaluate()
        if not self._control_bootstrap_pending:
            # REQ-CONTROL-CONFIG-BOOTSTRAP: Lesen ist während des Bootstraps
            # erlaubt, Steuern nicht - der erste Refresh läuft absichtlich
            # ohne Ladeentscheidung durch.
            await self._async_enforce_grid_charge(data)
        self._publish_charge_state(data)
        self._async_check_self_diagnostics()
        return data

    def _publish_charge_state(self, data: dict[str, Any]) -> None:
        """Übernimmt die Zustände der drei Lade-Automatiken in
        coordinator.data, damit die zugehörigen Sensoren
        (sensor.py/binary_sensor.py) sie wie jeden anderen Messwert lesen
        können."""
        plan = self.price_planner.plan
        data["timed_charge_active"] = self._timed_charge_active
        data["grid_serving_active"] = self._grid_serving_active
        data["grid_serving_window_active"] = self._grid_serving_window_active
        data["grid_serving_forecast_kwh"] = self._grid_serving_forecast_kwh
        data["grid_serving_forecast_allowed"] = self._grid_serving_forecast_allowed
        data["grid_serving_pause_status"] = self._grid_serving_pause_status_text
        data["price_charge_active"] = self._price_charge_active
        data["price_charge_status"] = self._price_charge_status
        data["price_charge_next_start"] = plan.next_start
        data["price_charge_current_price"] = plan.current_price
        data["next_cell_calibration"] = self.next_cell_calibration_at

    def _accumulate_energy(self, data: dict[str, Any]) -> None:
        """Akkumuliert geladene/entladene Energie (kWh) aus der aktuell
        bekannten storage_power_active (positiv = Entladung, negativ =
        Ladung, siehe Kommentar bei _watts_to_ic_setpoint_raw) per gehaltener
        Riemann-Summe (Wert seit dem letzten Tick × verstrichene Zeit) - der
        Speicher selbst besitzt keine Energiezähler-Register (siehe
        anforderung.yaml, REQ-ENERGY-DASHBOARD).

        self._energy_last_ts wird unabhängig vom Akkumulieren selbst bei
        jedem Tick als Baseline für den nächsten Aufruf aktualisiert. Beim
        ersten Tick (last_ts is None) sowie während der SunSpec-Modus nicht
        erreichbar ist (power is None, siehe REQ-EXTENDED-MODE-RESILIENCE)
        wird dagegen NICHT akkumuliert, um weder eine unbekannte
        Vor-Leistung noch eine Zeitspanne ohne Leistungswert fälschlich als
        Energie zu verbuchen.

        self._energy_charged_kwh/_energy_discharged_kwh bleiben zusätzlich
        so lange None (statt bei 0.0 zu starten), bis der unabhängige Store
        geladen oder einmalig ein numerischer RestoreEntity-Altzustand
        migriert wurde.

        Die Herkunft der Ladeenergie (REQ-ENERGY-ORIGIN,
        domain.energy_accounting.compute_charge_delta) läuft in derselben
        Riemann-Summe mit - dieselbe elapsed_hours, derselbe
        charged_kwh-Zuwachs wie oben, keine zweite Uhr. Entladung bleibt
        davon unberührt: compute_charge_delta liefert bei Entladeleistung
        ausschließlich Nullen. Die Wirtschaftlichkeitsbilanz
        (REQ-ECONOMICS-ACCOUNTING) erhält denselben charge_delta sowie den
        rohen, noch ungerundeten Entladezuwachs dieses Intervalls - auch
        das keine zweite Uhr, sondern dieselbe Berechnung wie oben."""
        now = monotonic()
        power = data.get("storage_power_active")
        last_ts = self._energy_last_ts
        self._energy_last_ts = now
        changed = False
        charge_delta: EnergyDelta | None = None
        discharge_kwh = 0.0
        # Nur Intervalle, die tatsächlich verbucht werden, gelten als
        # beobachtete Zeit des Kalendertages (REQ-ECONOMICS-AMORTIZATION,
        # Zeitabdeckung): Ein Neustart (last_ts is None) und eine Phase
        # ohne Leistungswert (SunSpec nicht erreichbar) sind exakt die
        # Lücken, die der Tag später als Unvollständigkeit ausweisen soll.
        observed_seconds = 0.0

        if last_ts is not None and power is not None:
            observed_seconds = now - last_ts
            elapsed_hours = (now - last_ts) / 3600
            charge_delta = compute_charge_delta(
                power, data.get("smartmeter_power"), elapsed_hours
            )
            discharge_w = power if power > 0 else 0
            discharge_kwh = discharge_w * elapsed_hours / 1000
            if charge_delta is not None:  # power ist hier bekannt
                if self._energy_charged_kwh is not None:
                    self._energy_charged_kwh += charge_delta.charged_kwh
                    changed = changed or charge_delta.charged_kwh > 0
                if self._energy_grid_charged_kwh is not None:
                    self._energy_grid_charged_kwh += charge_delta.grid_kwh
                    self._energy_pv_charged_kwh += charge_delta.pv_kwh
            if self._energy_discharged_kwh is not None:
                self._energy_discharged_kwh += discharge_kwh
                changed = changed or discharge_kwh > 0

        if changed:
            self._async_schedule_energy_save()

        data["energy_charged"] = (
            round(self._energy_charged_kwh, 3)
            if self._energy_charged_kwh is not None
            else None
        )
        data["energy_discharged"] = (
            round(self._energy_discharged_kwh, 3)
            if self._energy_discharged_kwh is not None
            else None
        )
        data["energy_charged_from_grid"] = (
            round(self._energy_grid_charged_kwh, 3)
            if self._energy_grid_charged_kwh is not None
            else None
        )
        data["energy_charged_from_pv"] = (
            round(self._energy_pv_charged_kwh, 3)
            if self._energy_pv_charged_kwh is not None
            else None
        )
        data["energy_origin_attributes"] = self._energy_origin_attributes()
        self._accumulate_economics(data, charge_delta, discharge_kwh, observed_seconds)

    def _energy_origin_attributes(self) -> dict[str, Any]:
        """Startzeitpunkt der Herkunftszählung als Sensorattribut
        (REQ-ENERGY-ORIGIN).

        Die drei Zähler energy_charged, energy_charged_from_grid/_pv und
        die Geldbilanz aus REQ-ECONOMICS-ACCOUNTING beginnen zu drei
        verschiedenen Zeitpunkten: der Gesamtzähler mit der ersten
        Installation, die Herkunft mit _bootstrap_energy_origin, die
        Geldbilanz erst mit dem ersten vollständig gespeicherten Tarif.
        Ihre Werte sind deshalb NICHT gegeneinander verrechenbar - genau
        das legt das Dashboard aber nahe, weil es sie untereinander zeigt
        (Anwenderbericht: 2,44 kWh PV-Ladung neben 0,0084 EUR
        PV-Opportunitätskosten, was 0,112 kWh entspricht; beide Werte
        waren korrekt). economics_started_at ist als Attribut des
        Status-Sensors längst sichtbar, sein Gegenstück hier war es
        nirgends - auch nicht im Diagnose-Download.
        """
        return {
            "origin_accounting_started_at": (
                None
                if self._origin_accounting_started_at is None
                else self._origin_accounting_started_at.isoformat()
            ),
        }

    def _energy_origin_initialized(self) -> bool:
        """Ob die Herkunftszählung läuft (siehe _bootstrap_energy_origin).

        Seit dem Wegfall der Kategorie "Herkunft unbekannt" ist jede
        gezählte Ladeenergie genau einer Quelle zugeordnet - eine
        Abdeckungsquote wäre damit konstant 100 % und sagte nichts mehr
        aus. Übrig bleibt genau die eine Aussage, die der
        Wirtschaftlichkeitsstatus braucht: ob überhaupt schon gezählt
        wird (REQ-ENERGY-ORIGIN).
        """
        return (
            self._energy_grid_charged_kwh is not None
            and self._energy_pv_charged_kwh is not None
        )

    # -- Wirtschaftlichkeitsbilanz (REQ-ECONOMICS-ACCOUNTING) ---------------
    def _accumulate_economics(
        self,
        data: dict[str, Any],
        charge_delta: EnergyDelta | None,
        discharged_kwh: float,
        observed_seconds: float,
    ) -> None:
        """Bewertet die Ladeenergie-Herkunft dieses Intervalls in Geld.

        Bewusst außerhalb jeder Ladeentscheidung: reine Nachbetrachtung
        bereits gemessener Energie, kein Modbus-Write.

        `observed_seconds` ist die Dauer genau dieses verbuchten Intervalls
        (aus _accumulate_energy, dieselbe Riemann-Summe) und wächst in den
        laufenden Tag hinein - daraus entsteht dessen Zeitabdeckung
        (REQ-ECONOMICS-AMORTIZATION). Ein Intervall über Mitternacht hinweg
        zählt dabei vollständig zum neuen Tag, exakt wie seine Energie und
        sein Geldwert; die dadurch fehlende Restsekunden des Vortages sind
        gegenüber der Schwelle von 5 % eines Tages bedeutungslos.

        economics_current_import_price/economics_feed_in_price sind reine
        Durchreichungen des aktuellen Tarifs (SaxTariffProvider) und werden
        unabhängig vom Bilanz-Bootstrap immer aktualisiert - sie beschreiben
        den JETZT gültigen Tarif, nicht die kumulierte Bilanz.

        Der Bootstrap (siehe _bootstrap_economics_if_ready) läuft nur,
        solange der Tarif aktiv ist - "beim erstmaligen Aktivieren" (siehe
        anforderung.yaml, REQ-ECONOMICS-ACCOUNTING). Ist die Bilanz aber
        einmal gestartet, akkumuliert sie AUCH während einer späteren
        Tarifpause (tariff_type=disabled) unverändert weiter: current_price/
        feed_in_price sind während der Pause bereits None (SaxTariffProvider
        liefert das für einen deaktivierten Tarif von sich aus), jede in
        dieser Zeit geladene Energie landet dadurch automatisch im
        unbewerteten Bestand. Würde die Akkumulation stattdessen komplett
        pausieren, bliebe in der Pause geladene Energie unbeobachtet und
        eine spätere Entladung würde beim Reaktivieren fälschlich vollständig
        als vermiedener Netzbezug monetarisiert - ein kostenloser
        Scheingewinn, exakt der bei #42 vermiedene Fehler. Nur die
        VERÖFFENTLICHTEN monetären Sensoren blenden während einer Pause auf
        None statt auf die (weiter mitlaufenden) internen Summen (siehe
        _publish_economics_balance) - kein falscher Nullgewinn, aber auch
        keine sichtbaren Beträge, solange der Tarif aus ist.
        """
        # Zeitpunkt bewusst einmal bestimmt und weitergereicht: Preis und
        # die Tarifplan-Attribute darunter müssen denselben Moment
        # beschreiben, sonst könnte ein Fensterwechsel zwischen beiden
        # Aufrufen ein Fenster ausweisen, das zum gemeldeten Preis gar
        # nicht gehört (REQ-ECONOMICS-SAVINGS-DASHBOARD).
        moment = dt_util.now()
        quote_result = self.tariff_provider.quote(moment)
        current_price = quote_result.price_eur_kwh
        feed_in_price = self.tariff_provider.feed_in_price_eur_kwh
        data["economics_current_import_price"] = (
            None if current_price is None else round(current_price, 5)
        )
        data["economics_price_attributes"] = self._tariff_plan_attributes(
            quote_result, moment, feed_in_price
        )
        data["economics_feed_in_price"] = (
            None if feed_in_price is None else round(feed_in_price, 5)
        )

        tariff_enabled = self.tariff_provider.config.enabled
        if tariff_enabled:
            self._update_economics_price_availability(
                quote_result, current_price, monotonic()
            )
        else:
            # Re-Aktivierung soll ohne einen stehen gebliebenen
            # Karenzzeit-Countdown aus einer früheren Deaktivierung starten.
            self._economics_price_unavailable_since = None
            self._economics_price_unavailable = False

        # REQ-ECONOMICS-OBSERVABILITY: ein unlesbarer Store darf weder einen
        # frischen 0-Bootstrap im Arbeitsspeicher starten noch eine bereits
        # laufende Bilanz weiter akkumulieren - siehe
        # _bootstrap_economics_if_ready sowie den Docstring dort.
        frozen = self._economics_store_write_blocked
        if tariff_enabled:
            self._bootstrap_economics_if_ready(data)
        if self._economics_started_at is None:
            # Nie aktiviert, oder wegen eines unlesbaren Stores blockiert.
            self._publish_economics_balance(data, monetary_available=False)
            self._publish_amortization(data, monetary_available=False)
            self._publish_economics_status(
                data,
                tariff_enabled=tariff_enabled,
                current_price=current_price,
                feed_in_price=feed_in_price,
            )
            return

        changed = False
        if not frozen:
            delta: EconomicsDelta | None = None
            if charge_delta is not None:
                delta = compute_economics_delta(
                    charge_delta,
                    discharged_kwh,
                    self._economics_unvalued_inventory_kwh,
                    current_price,
                    feed_in_price,
                )

            # Tageswechsel-Erkennung VOR der Anwendung des aktuellen Deltas,
            # damit der Tageszähler das erste Delta eines neuen Tages nicht
            # noch dem abgeschlossenen Vortag zurechnet.
            if self._advance_economics_day():
                changed = True

            if (
                observed_seconds > 0
                and self._economics_current_day_observed_seconds is not None
            ):
                # Die beobachtete Zeit muss einen Neustart überleben, sonst
                # sähe jeder Neustart den laufenden Tag als unvollständiger
                # an, als er tatsächlich war. Anders als die Geldsummen
                # bewegt sie sich aber bei JEDEM verbuchten Intervall -
                # deshalb löst sie das Speichern nur beim Überschreiten des
                # nächsten Rasterschritts aus (siehe
                # OBSERVED_TIME_SAVE_GRANULARITY_SECONDS).
                previous = self._economics_current_day_observed_seconds
                self._economics_current_day_observed_seconds = (
                    previous + observed_seconds
                )
                changed = changed or (
                    self._economics_current_day_observed_seconds
                    // OBSERVED_TIME_SAVE_GRANULARITY_SECONDS
                    > previous // OBSERVED_TIME_SAVE_GRANULARITY_SECONDS
                )

            if delta is not None:
                previous_raw_result = (
                    self._economics_avoided_grid_cost_eur
                    - self._economics_grid_charge_cost_eur
                    - self._economics_pv_opportunity_cost_eur
                )
                previous_high_water = self._economics_operating_result_high_water_eur
                if previous_high_water is None:
                    previous_high_water = max(0.0, previous_raw_result)
                self._economics_grid_charge_cost_eur += delta.grid_charge_cost_delta
                self._economics_pv_opportunity_cost_eur += (
                    delta.pv_opportunity_cost_delta
                )
                self._economics_avoided_grid_cost_eur += delta.avoided_grid_cost_delta
                self._economics_unvalued_inventory_kwh += (
                    delta.unvalued_inventory_delta_kwh
                )
                self._economics_unpriced_charge_kwh += delta.unpriced_charge_delta_kwh
                self._economics_unpriced_discharge_kwh += (
                    delta.unpriced_discharge_delta_kwh
                )
                self._economics_priced_charge_kwh += delta.priced_charge_kwh_delta
                self._economics_priced_discharge_kwh += delta.priced_discharge_kwh_delta
                current_raw_result = (
                    self._economics_avoided_grid_cost_eur
                    - self._economics_grid_charge_cost_eur
                    - self._economics_pv_opportunity_cost_eur
                )
                current_high_water = compute_operating_result_high_water(
                    previous_high_water, current_raw_result
                )
                self._economics_operating_result_high_water_eur = current_high_water
                self._economics_current_day_operating_result_eur += (
                    current_raw_result - previous_raw_result
                )
                self._economics_current_day_priced_charge_kwh += (
                    delta.priced_charge_kwh_delta
                )
                self._economics_current_day_unpriced_charge_kwh += (
                    delta.unpriced_charge_delta_kwh
                )
                self._economics_current_day_priced_discharge_kwh += (
                    delta.priced_discharge_kwh_delta
                )
                self._economics_current_day_unpriced_discharge_kwh += (
                    delta.unpriced_discharge_delta_kwh
                )
                # Auch ein gültiger Preis von exakt 0 EUR/kWh bewegt
                # priced_charge_kwh_delta/priced_discharge_kwh_delta, ohne
                # einen der übrigen sechs Werte zu verändern - ohne die
                # beiden hier würde eine solche Bewegung kein verzögertes
                # Speichern auslösen und der Tageszähler könnte einen
                # ungeplanten Neustart nicht überleben.
                changed = changed or any(
                    (
                        delta.grid_charge_cost_delta,
                        delta.pv_opportunity_cost_delta,
                        delta.avoided_grid_cost_delta,
                        delta.unvalued_inventory_delta_kwh,
                        delta.unpriced_charge_delta_kwh,
                        delta.unpriced_discharge_delta_kwh,
                        delta.priced_charge_kwh_delta,
                        delta.priced_discharge_kwh_delta,
                    )
                )

            charging_now = self._economics_is_charging(data, charge_delta)
            if charging_now:
                self._economics_inventory_idle_confirmations = 0
                self._economics_inventory_discharged_since_charge = False
            elif self._economics_is_discharging(data, discharged_kwh):
                self._economics_inventory_idle_confirmations = 0
                self._economics_inventory_discharged_since_charge = True
            elif self._economics_is_stationary(data):
                self._economics_inventory_idle_confirmations = min(
                    self._economics_inventory_idle_confirmations + 1,
                    INVENTORY_CORRECTION_IDLE_CONFIRMATIONS,
                )
            else:
                # Ein fehlender Leistungswert ist kein bestätigter
                # Stillstand. Ohne Bewegungsqualität darf keine Korrektur
                # freigeschaltet werden (Issue #145).
                self._economics_inventory_idle_confirmations = 0

            if (
                self._economics_inventory_idle_confirmations
                >= INVENTORY_CORRECTION_IDLE_CONFIRMATIONS
            ):
                # Läuft unabhängig davon, ob der Tarif gerade aktiv ist - die
                # Bestandskorrektur betrifft die Integrität des unbewerteten
                # Bestands selbst, nicht die aktuelle Bepreisung.
                correction = (
                    min_soc_inventory_correction(
                        self._economics_unvalued_inventory_kwh,
                        data.get("battery_soc"),
                        data.get("battery_soc_min"),
                    )
                    if self._economics_inventory_discharged_since_charge
                    else None
                )
                if correction is not None:
                    _LOGGER.info(
                        "Wirtschaftlichkeit: unbewerteter Bestand am "
                        "SOC-Minimum auf 0 korrigiert (war %.3f kWh, %s)",
                        self._economics_unvalued_inventory_kwh,
                        dt_util.utcnow().isoformat(),
                    )
                    self._economics_unvalued_inventory_kwh = correction
                    self._economics_inventory_discharged_since_charge = False
                    changed = True

                # Der Bestand ist ein Lagerbestand und kann nie mehr Energie
                # umfassen, als anhand des quantisierten SOC sicher im Speicher
                # liegen kann. Der obere Rand verhindert das Löschen gerade
                # geladener Energie innerhalb derselben SOC-Stufe (Issue #145).
                capped = capacity_inventory_correction(
                    self._economics_unvalued_inventory_kwh,
                    _economics_capacity_kwh(data.get("battery_capacity")),
                    data.get("battery_soc"),
                    self._economics_soc_resolution_percent(),
                )
                if capped is not None:
                    self._note_inventory_cap_correction(
                        self._economics_unvalued_inventory_kwh, capped
                    )
                    self._economics_unvalued_inventory_kwh = capped
                    changed = True

        if changed:
            self._async_schedule_economics_save()
        self._publish_economics_balance(data, monetary_available=tariff_enabled)
        self._publish_amortization(data, monetary_available=tariff_enabled)
        self._publish_economics_status(
            data,
            tariff_enabled=tariff_enabled,
            current_price=current_price,
            feed_in_price=feed_in_price,
        )

    def _note_inventory_cap_correction(
        self, previous_kwh: float, capped_kwh: float
    ) -> None:
        """Protokolliert eine Deckelung des unbewerteten Bestands.

        Zählt die verworfene Menge vollständig für den Diagnose-Download
        mit, loggt aber höchstens alle INVENTORY_CAP_LOG_INTERVAL_SECONDS
        eine Zeile (siehe Konstante).
        """
        self._economics_inventory_capped_kwh += previous_kwh - capped_kwh
        now = monotonic()
        last = self._economics_inventory_cap_logged_at
        if last is not None and now - last < INVENTORY_CAP_LOG_INTERVAL_SECONDS:
            return
        self._economics_inventory_cap_logged_at = now
        _LOGGER.info(
            "Wirtschaftlichkeit: unbewerteter Bestand auf den tatsächlichen "
            "Speicherinhalt gedeckelt (war %.3f kWh, jetzt %.3f kWh, "
            "insgesamt %.3f kWh verworfen, %s)",
            previous_kwh,
            capped_kwh,
            self._economics_inventory_capped_kwh,
            dt_util.utcnow().isoformat(),
        )

    @staticmethod
    def _economics_is_charging(
        data: dict[str, Any], charge_delta: EnergyDelta | None
    ) -> bool:
        """Aktive oder im aktuellen Intervall verbuchte Ladung erkennen."""
        if charge_delta is not None and charge_delta.charged_kwh > 0:
            return True
        power = data.get("storage_power_active")
        return (
            isinstance(power, int | float)
            and not isinstance(power, bool)
            and math.isfinite(power)
            and power < 0
        )

    @staticmethod
    def _economics_is_discharging(data: dict[str, Any], discharged_kwh: float) -> bool:
        """Aktive oder im aktuellen Intervall verbuchte Entladung erkennen."""
        if discharged_kwh > 0:
            return True
        power = data.get("storage_power_active")
        return (
            isinstance(power, int | float)
            and not isinstance(power, bool)
            and math.isfinite(power)
            and power > 0
        )

    @staticmethod
    def _economics_is_stationary(data: dict[str, Any]) -> bool:
        """Nur einen sicher gemessenen Nullwert als Stillstand werten."""
        power = data.get("storage_power_active")
        return (
            isinstance(power, int | float)
            and not isinstance(power, bool)
            and math.isfinite(power)
            and power == 0
        )

    def _economics_soc_resolution_percent(self) -> float:
        """Messquantum des Battery-SOC in Prozent, konservativ 1 %."""
        exponent = to_signed16(self._battery_scale_factors.soc)
        if not -10 <= exponent <= 10:
            return 1.0
        return 10.0**exponent

    def _net_savings_today_last_reset(self) -> datetime | None:
        """Zeitpunkt, zu dem economics_net_savings_today zuletzt auf 0 sprang.

        Ein zyklisch zurückgesetzter total-Sensor muss diesen Zeitpunkt
        mitliefern, sonst verbucht die Langzeitstatistik den Sprung auf 0
        nicht als Reset, sondern als negativen Zuwachs in Höhe des
        bisherigen Tagesergebnisses (Issue #133).

        Normalfall ist der Beginn des laufenden Tages in derselben lokalen
        Zeitzone, aus der auch die Tageswechsel-Erkennung ihr Datum bezieht
        (_advance_economics_day). Ein neuer Bilanz-Bootstrap nach einem
        unvollständigen Store sowie ein manueller Bilanzneustart können den
        Tageszähler aber mitten am Tag auf 0 setzen, ohne das Datum zu ändern.
        Deshalb gilt der späteste Zeitpunkt aus Tagesbeginn,
        economics_started_at und last_restart_at. Die beiden Bilanzzeitpunkte
        sind persistiert und überstehen einen Home-Assistant-Neustart, ohne
        dass sich der gemeldete Reset nachträglich verschiebt.
        """
        if self._economics_current_day is None:
            return None
        day_start = dt_util.start_of_local_day(self._economics_current_day)
        candidates = (
            day_start,
            self._economics_started_at,
            self._economics_last_restart_at,
        )
        return max(candidate for candidate in candidates if candidate is not None)

    def _start_economics_day(self, day: date) -> None:
        self._economics_current_day = day
        self._economics_current_day_operating_result_eur = 0.0
        self._economics_current_day_priced_charge_kwh = 0.0
        self._economics_current_day_unpriced_charge_kwh = 0.0
        self._economics_current_day_priced_discharge_kwh = 0.0
        self._economics_current_day_unpriced_discharge_kwh = 0.0
        self._economics_current_day_observed_seconds = 0.0

    def _advance_economics_day(self) -> bool:
        """Erkennt einen lokalen Kalendertagswechsel (REQ-ECONOMICS-
        AMORTIZATION).

        Läuft bei jedem Poll-Tick mit einem existierenden Datenpunkt mit,
        ohne eigenen Timer - das lokale Datum kommt bewusst aus
        `dt_util.now()` (Home-Assistant-Zeitzone), nicht aus UTC, damit ein
        Tag dem tatsächlichen Kalendertag am Aufstellort entspricht. Ein
        DST-Tag mit 23 oder 25 Stunden wird dabei NICHT auf 24h normiert -
        er bleibt einfach ein Tag mit entsprechend weniger/mehr
        Datenpunkten (Regel 1). Idempotent gegenüber einem Neustart (der
        laufende Tag ist persistiert, siehe async_load_economics_state) und
        einer doppelten Verarbeitung desselben Ticks: Nur ein tatsächlicher
        Wechsel des lokalen Datums schließt genau einmal einen Tag ab.

        Bewusst OHNE das aktuelle Delta: Muss vor dessen Anwendung auf die
        Gesamtsummen laufen, damit der geschlossene Tag exakt den am Ende des
        Vortags erreichten Stand sieht (siehe _accumulate_economics).
        """
        today_local = dt_util.now().date()
        if self._economics_current_day is None:
            self._start_economics_day(today_local)
            return True
        if today_local != self._economics_current_day:
            self._close_economics_day()
            self._start_economics_day(today_local)
            return True
        return False

    def _close_economics_day(self) -> None:
        """Schließt den laufenden Kalendertag ab und hängt ihn an die
        Tageshistorie an.

        Wird ausschließlich von _advance_economics_day bei einem erkannten
        Datumswechsel aufgerufen, bevor der neue Tag über
        _start_economics_day beginnt - `_economics_current_day` und seine
        sechs Werte sind an dieser Stelle deshalb garantiert gesetzt (float,
        kein None).

        Die Tageslänge wird hier festgeschrieben (nicht erst beim Lesen der
        Historie), damit ein DST-Tag mit 23/25 Stunden dauerhaft an seiner
        tatsächlichen Länge gemessen wird und eine spätere Änderung der
        Zeitzone historische Tage nicht rückwirkend umbewertet.
        """
        closed_day = DayEconomicsResult(
            day=self._economics_current_day,
            operating_result_eur=self._economics_current_day_operating_result_eur,
            priced_charge_kwh=self._economics_current_day_priced_charge_kwh,
            unpriced_charge_kwh=self._economics_current_day_unpriced_charge_kwh,
            priced_discharge_kwh=self._economics_current_day_priced_discharge_kwh,
            unpriced_discharge_kwh=self._economics_current_day_unpriced_discharge_kwh,
            observed_seconds=self._economics_current_day_observed_seconds,
            day_length_seconds=self._local_day_length_seconds(
                self._economics_current_day
            ),
        )
        self._economics_day_results = (*self._economics_day_results, closed_day)[
            -MAX_STORED_DAYS:
        ]

    @staticmethod
    def _local_day_length_seconds(day: date) -> float:
        """Tatsächliche Länge eines lokalen Kalendertages in Sekunden.

        23 h/25 h an den DST-Umstellungstagen, sonst 24 h - der Nenner der
        Zeitabdeckung (REQ-ECONOMICS-AMORTIZATION, Regel 1). Die Grenzen
        kommen aus dt_util.start_of_local_day, derselben
        Home-Assistant-Zeitzone, aus der auch die Tageswechsel-Erkennung
        ihr Datum bezieht (_advance_economics_day).
        """
        start = dt_util.start_of_local_day(day)
        next_start = dt_util.start_of_local_day(day + timedelta(days=1))
        # Bewusst über UTC: Python ignoriert bei der Subtraktion zweier
        # datetimes mit DEMSELBEN tzinfo-Objekt dessen Offset komplett und
        # rechnet reine Wanduhrzeit - ein DST-Tag käme dabei immer auf
        # exakt 24 h heraus, also genau auf den Wert, den diese Methode
        # vermeiden soll.
        return (dt_util.as_utc(next_start) - dt_util.as_utc(start)).total_seconds()

    def _publish_amortization(
        self, data: dict[str, Any], *, monetary_available: bool
    ) -> None:
        """Veröffentlicht den Amortisationsstand (REQ-ECONOMICS-
        AMORTIZATION) in coordinator.data.

        `monetary_available=False` (deaktivierter Tarif) blendet die vier
        Geldwert-Sensoren nach derselben Regel wie
        _publish_economics_balance auf None aus (ROI, Fortschritt, Restbetrag,
        Tagesergebnis) - aus demselben Grund: kein sichtbarer Betrag, solange
        der Tarif aus ist,
        obwohl intern weiter akkumuliert wird.

        Fehlende/ungültige Investitionskosten deaktivieren dagegen ALLE
        vier Sensoren dieser Anforderung unabhängig vom Tarifstatus.
        """
        investment_cost = investment_cost_eur_from_options(self.options)
        # Trägt die Sichtbarkeit der Investitionskarte im Dashboard: Eine
        # Core-"conditional"-Karte kann ausschließlich den ZUSTAND einer
        # Entity prüfen, nie ein Attribut (siehe dashboard.py, #139) -
        # dieses Flag ist deshalb ein eigener Binary-Sensor.
        data["economics_investment_configured"] = investment_cost is not None
        if investment_cost is None:
            for key in (
                "economics_roi",
                "economics_amortization_progress",
                "economics_remaining_to_payback",
                "economics_net_savings_today",
                "economics_net_savings_today_last_reset",
            ):
                data[key] = None
            data["economics_roi_attributes"] = {
                "prior_result_eur": None,
                "measured_operating_result_eur": None,
            }
            return

        # Exakt dasselbe aktuelle Nettoergebnis, das economics_net_savings
        # veröffentlicht (_publish_economics_balance) - die reine Messung
        # ohne Vorlauf. Ein historischer Peak würde normale spätere Kosten
        # aus ROI und Restbetrag ausblenden (Issue #144).
        measured_result = self._net_savings_eur()
        # Der Vorlauf-Ertrag geht ausschließlich hier ein, nicht in
        # _publish_economics_balance: economics_net_savings bleibt der
        # von dieser Integration selbst gemessene Betrag (siehe
        # const.CONF_ECONOMICS_PRIOR_RESULT). Er wird bewusst nur zu einer
        # bereits laufenden Bilanz addiert - stünde er auch für sich
        # allein, zeigte das Dashboard einen ROI aus reiner Handeingabe,
        # während daneben jeder gemessene Geldwert unbekannt ist.
        prior_result = prior_result_eur_from_options(self.options)
        operating_result = (
            None if measured_result is None else measured_result + prior_result
        )
        published_operating_result = operating_result if monetary_available else None
        roi_percent = compute_roi_percent(published_operating_result, investment_cost)
        remaining_to_payback = compute_remaining_to_payback_eur(
            investment_cost, published_operating_result
        )
        data["economics_roi"] = _rounded(roi_percent, 2)
        data["economics_amortization_progress"] = (
            None
            if roi_percent is None
            else _rounded(compute_amortization_progress_percent(roi_percent), 2)
        )
        data["economics_remaining_to_payback"] = _rounded(remaining_to_payback, 2)

        current_day_result = (
            self._economics_current_day_operating_result_eur
            if monetary_available
            else None
        )
        data["economics_net_savings_today"] = _rounded(current_day_result, 4)
        data["economics_net_savings_today_last_reset"] = (
            self._net_savings_today_last_reset()
        )

        # Ohne diese beiden Attribute stünden im Dashboard drei Zahlen
        # nebeneinander, die sich nicht zur Deckung bringen lassen: ein
        # operatives Ergebnis von 250 EUR, ein Restbetrag von 350 EUR und
        # ein ROI von 65 % bei 1000 EUR Investition. Erst der hier
        # ausgewiesene Vorlauf-Ertrag erklärt die Differenz.
        data["economics_roi_attributes"] = {
            "prior_result_eur": prior_result,
            # Bewusst measured_result, nicht operating_result: Das Attribut
            # soll die Differenz zum Sensor economics_net_savings
            # AUFLÖSEN. Stünde hier der bereits um den Vorlauf erhöhte
            # Betrag, zeigte es genau die Zahl nicht, gegen die der Leser
            # abgleicht.
            "measured_operating_result_eur": _rounded(measured_result, 2),
        }

    # -- Datenqualität/Diagnose (REQ-ECONOMICS-OBSERVABILITY) ----------------
    def _update_economics_price_availability(
        self, quote_result: QuoteResult, current_price: float | None, now: float
    ) -> None:
        """Verfolgt, seit wann ununterbrochen kein gültiger Netzbezugspreis
        mehr vorlag, und leitet daraus _economics_price_unavailable ab.

        Ein ungültig GESPEICHERTER Fest-/Zeitfenstertarif
        (QuoteUnavailable.TARIFF_INCOMPLETE, z. B. ein fehlender Pflichtpreis
        oder eine kaputte Zeitfenstergruppe) ist ein sofortiger
        Konfigurationsfehler - anders als ein transienter Ausfall des
        dynamischen Preis-Sensors gilt dafür keine Karenzzeit. Läuft nur,
        solange der Tarif aktiv ist (siehe Aufrufer _accumulate_economics).
        """
        if current_price is not None:
            self._economics_price_unavailable_since = None
            self._economics_price_unavailable = False
            self._economics_last_successful_quote_at = dt_util.utcnow()
            return
        if quote_result.reason is QuoteUnavailable.TARIFF_INCOMPLETE:
            self._economics_price_unavailable = True
            return
        if self._economics_price_unavailable_since is None:
            self._economics_price_unavailable_since = now
        self._economics_price_unavailable = (
            now - self._economics_price_unavailable_since
            >= ECONOMICS_PRICE_UNAVAILABLE_GRACE_PERIOD
        )

    def _tariff_plan_attributes(
        self,
        quote_result: QuoteResult,
        moment: datetime,
        feed_in_price: float | None,
    ) -> dict[str, Any]:
        """Der hinterlegte Tarifplan als Attribute des Preis-Sensors.

        REQ-ECONOMICS-SAVINGS-DASHBOARD: Der reine Preiswert beantwortet weder
        "habe ich meinen Tarif richtig eingetragen?" noch "welches Fenster
        liefert diesen Preis gerade, und wann ändert er sich wieder?". Die
        Konfiguration liegt sonst ausschließlich in entry.options und ist
        damit nur im Options Flow einsehbar - dort aber immer im
        Bearbeitungsmodus und ohne jeden Bezug zur aktuellen Uhrzeit.

        Die tageszeitabhängigen Felder (base_price_eur_kwh, windows) sind
        bei jeder anderen Tarifart None statt eines Restwerts aus einer
        früheren Konfiguration: ein sichtbarer Tarifplan, der gar nicht
        gilt, wäre irreführender als gar keiner.
        """
        config = self.tariff_provider.config
        quote = quote_result.quote
        time_of_use = config.tariff_type is TariffType.TIME_OF_USE
        # Ohne gültigen Quote (z. B. TARIFF_INCOMPLETE nach einem von Hand
        # bearbeiteten Store) gilt gerade überhaupt kein Preis - dann darf
        # auch kein Fenster als "jetzt geltend" erscheinen. Die
        # Fensterliste selbst bleibt sichtbar: genau sie braucht der
        # Anwender, um den Konfigurationsfehler zu finden.
        window = active_window(config, moment) if quote is not None else None
        return {
            "tariff_type": str(config.tariff_type),
            "quote_source": None if quote is None else str(quote.source),
            "unavailable_reason": (
                None if quote_result.reason is None else str(quote_result.reason)
            ),
            "active_window": None if window is None else window_as_mapping(window),
            # Der nächste PREISwechsel, nicht das Ende der Gültigkeit:
            # Beim Festpreis unbegrenzt (valid_until ist None), beim
            # dynamischen Tarif das Ende des Vorschau-Slots. Ein
            # tageszeitabhängiger Tarif ganz ohne Zeitfenster ist zwar eine
            # gültige Konfiguration, verhält sich aber wie ein Festpreis;
            # sein valid_until ist dort der bloße Tagesumbruch
            # (domain.tariff._segment_bounds) und würde einen Preiswechsel
            # um Mitternacht melden, den es nicht gibt.
            "next_price_change_at": (
                None
                if quote is None
                or quote.valid_until is None
                or (time_of_use and not config.windows)
                else quote.valid_until.isoformat()
            ),
            "base_price_eur_kwh": (
                config.tou_base_price_eur_kwh if time_of_use else None
            ),
            "feed_in_price_eur_kwh": feed_in_price,
            "windows": (
                [window_as_mapping(entry) for entry in sorted_windows(config)]
                if time_of_use
                else None
            ),
        }

    def _publish_economics_status(
        self,
        data: dict[str, Any],
        *,
        tariff_enabled: bool,
        current_price: float | None,
        feed_in_price: float | None,
    ) -> None:
        """Veröffentlicht economics_status samt Diagnoseattributen.

        Fasst zusammen, ob und warum die Wirtschaftlichkeitsbilanz gerade
        vertrauenswürdig ist - eine Geldzahl ohne Aussage zur Datenqualität
        ist irreführend. Läuft unabhängig vom `frozen`/Bootstrap-Zweig in
        _accumulate_economics, damit auch storage_error sichtbar wird,
        bevor die Bilanz je gestartet ist.

        Den Zustand bestimmen ausschließlich die Abdeckungen des LAUFENDEN
        Kalendertages (dieselben Tages-Buckets wie in
        REQ-ECONOMICS-AMORTIZATION, keine zusätzlichen Zähler) - die
        kumulierten Lifetime-Quoten bleiben als Langzeitinformation
        daneben erhalten, taugen aber nicht als Auslöser, weil sie nie
        zurückgehen (Issue #134, siehe compute_economics_status).
        """
        charge_coverage = compute_price_coverage_percent(
            self._economics_priced_charge_kwh, self._economics_unpriced_charge_kwh
        )
        discharge_coverage = compute_price_coverage_percent(
            self._economics_priced_discharge_kwh,
            self._economics_unpriced_discharge_kwh,
        )
        charge_coverage_today = compute_price_coverage_percent(
            self._economics_current_day_priced_charge_kwh,
            self._economics_current_day_unpriced_charge_kwh,
        )
        discharge_coverage_today = compute_price_coverage_percent(
            self._economics_current_day_priced_discharge_kwh,
            self._economics_current_day_unpriced_discharge_kwh,
        )
        status = compute_economics_status(
            tariff_enabled=tariff_enabled,
            storage_error=self._economics_store_write_blocked,
            price_unavailable=self._economics_price_unavailable,
            origin_unavailable=not self._energy_origin_initialized(),
            priced_charge_kwh_today=self._economics_current_day_priced_charge_kwh,
            unpriced_charge_kwh_today=self._economics_current_day_unpriced_charge_kwh,
            priced_discharge_kwh_today=(
                self._economics_current_day_priced_discharge_kwh
            ),
            unpriced_discharge_kwh_today=(
                self._economics_current_day_unpriced_discharge_kwh
            ),
        )
        data["economics_status"] = status.value
        price_entity_id = (
            self.tariff_provider.price_entity_id
            if self.tariff_provider.config.tariff_type is TariffType.DYNAMIC
            else None
        )
        data["economics_status_attributes"] = {
            # Redundant zum Sensorzustand, aber Teil desselben
            # Attributsatzes - siehe die analoge average_daily_result_eur-
            # Ergänzung bei REQ-ECONOMICS-AMORTIZATION.
            "reason": status.value,
            "tariff_type": str(self.tariff_provider.config.tariff_type),
            "price_sensor_entity_id": price_entity_id,
            "economics_started_at": (
                None
                if self._economics_started_at is None
                else self._economics_started_at.isoformat()
            ),
            "last_tariff_revision_at": (
                None
                if self._last_tariff_revision_at is None
                else self._last_tariff_revision_at.isoformat()
            ),
            "last_successful_quote_at": (
                None
                if self._economics_last_successful_quote_at is None
                else self._economics_last_successful_quote_at.isoformat()
            ),
            "current_import_price_eur_kwh": (
                None if current_price is None else round(current_price, 5)
            ),
            "feed_in_price_eur_kwh": (
                None if feed_in_price is None else round(feed_in_price, 5)
            ),
            "priced_charge_kwh": (
                None
                if self._economics_priced_charge_kwh is None
                else round(self._economics_priced_charge_kwh, 3)
            ),
            "unpriced_charge_kwh": (
                None
                if self._economics_unpriced_charge_kwh is None
                else round(self._economics_unpriced_charge_kwh, 3)
            ),
            "priced_discharge_kwh": (
                None
                if self._economics_priced_discharge_kwh is None
                else round(self._economics_priced_discharge_kwh, 3)
            ),
            "unpriced_discharge_kwh": (
                None
                if self._economics_unpriced_discharge_kwh is None
                else round(self._economics_unpriced_discharge_kwh, 3)
            ),
            "charge_price_coverage_percent": (
                None if charge_coverage is None else round(charge_coverage, 1)
            ),
            "discharge_price_coverage_percent": (
                None if discharge_coverage is None else round(discharge_coverage, 1)
            ),
            # Die beiden Tageswerte bestimmen den Zustand (Issue #134) -
            # die kumulierten Quoten darüber bleiben als
            # Langzeitinformation daneben stehen.
            "charge_price_coverage_percent_today": (
                None
                if charge_coverage_today is None
                else round(charge_coverage_today, 1)
            ),
            "discharge_price_coverage_percent_today": (
                None
                if discharge_coverage_today is None
                else round(discharge_coverage_today, 1)
            ),
        }

    def _bootstrap_economics_if_ready(self, _data: dict[str, Any]) -> None:
        """Startet die Bilanz beim erstmaligen Aktivieren.

        Der beim Start bereits vorhandene Speicherinhalt wird mit 0 EUR
        angesetzt. Die Bilanz startet deshalb unabhängig von Kapazität und
        Ladezustand mit einem unbewerteten Bestand von 0 kWh. Läuft nur
        einmal: Ist economics_started_at bereits gesetzt (laufender Betrieb
        oder aus dem Store geladen), passiert hier nichts mehr - auch nicht
        nach einem zwischenzeitlichen Deaktivieren/Reaktivieren des Tarifs.

        Läuft außerdem NICHT, solange der Store als unlesbar gilt
        (_economics_store_write_blocked, REQ-ECONOMICS-OBSERVABILITY,
        Status storage_error) - sonst würde eine aus lauter Nullen frisch
        gebootstrappte Bilanz im Arbeitsspeicher weiterlaufen, obwohl sie
        nie gesichert werden kann. Ohne diesen Neustart bleibt der Zustand
        stattdessen bis zu einem erfolgreichen Neuladen des Config Entry
        unverändert `None` ("wartend"), statt unbeobachtet zu akkumulieren.
        """
        if (
            self._economics_started_at is not None
            or self._economics_store_write_blocked
        ):
            return
        self._economics_grid_charge_cost_eur = 0.0
        self._economics_pv_opportunity_cost_eur = 0.0
        self._economics_avoided_grid_cost_eur = 0.0
        self._economics_operating_result_high_water_eur = 0.0
        self._economics_unvalued_inventory_kwh = 0.0
        self._economics_unpriced_charge_kwh = 0.0
        self._economics_unpriced_discharge_kwh = 0.0
        self._economics_priced_charge_kwh = 0.0
        self._economics_priced_discharge_kwh = 0.0
        self._economics_started_at = dt_util.utcnow()
        self._async_schedule_economics_save()

    def _net_savings_eur(self) -> float | None:
        """Aktuelles signiertes Nettoergebnis aus den drei Geldsummen."""
        if (
            self._economics_avoided_grid_cost_eur is None
            or self._economics_grid_charge_cost_eur is None
            or self._economics_pv_opportunity_cost_eur is None
        ):
            return None
        return (
            self._economics_avoided_grid_cost_eur
            - self._economics_grid_charge_cost_eur
            - self._economics_pv_opportunity_cost_eur
        )

    def _publish_economics_balance(
        self, data: dict[str, Any], *, monetary_available: bool
    ) -> None:
        """Veröffentlicht die Bilanz in coordinator.data.

        `monetary_available=False` (deaktivierter Tarif) blendet
        ausschließlich die fünf monetären Sensoren (device_class monetary)
        auf None aus - ein deaktivierter Tarif darf keinen Betrag mehr
        zeigen, unabhängig davon, dass intern (siehe _accumulate_economics)
        weiter akkumuliert wird. Die internen Bestands- und
        Preisabdeckungszähler bleiben davon unberührt.
        """
        grid_cost = self._economics_grid_charge_cost_eur if monetary_available else None
        pv_cost = (
            self._economics_pv_opportunity_cost_eur if monetary_available else None
        )
        avoided_cost = (
            self._economics_avoided_grid_cost_eur if monetary_available else None
        )
        data["economics_grid_charge_cost"] = _rounded(grid_cost, 4)
        data["economics_pv_opportunity_cost"] = _rounded(pv_cost, 4)
        data["economics_avoided_grid_cost"] = _rounded(avoided_cost, 4)
        data["economics_operating_result"] = (
            None
            if grid_cost is None or pv_cost is None or avoided_cost is None
            else _rounded(avoided_cost - grid_cost - pv_cost, 4)
        )
        data["economics_net_savings"] = (
            _rounded(self._net_savings_eur(), 4) if monetary_available else None
        )
        # SensorDeviceClass.MONETARY erlaubt in Home Assistant nur
        # state_class TOTAL. Der Reset-Zeitpunkt trennt kontrollierte
        # Bilanzabschnitte; normale Rückgänge durch Kosten bleiben echte
        # signierte Änderungen innerhalb desselben Abschnitts.
        data["economics_balance_last_reset"] = self._economics_started_at
        # Kompatibler Alias für bereits bestehende Tests/Consumers des zuerst
        # eingeführten Netto-Ersparnis-Sensors (Issue #151).
        data["economics_net_savings_last_reset"] = self._economics_started_at

    def notify_tariff_revision(self) -> None:
        """Options-Änderung: Zeitpunkt der letzten Tarifrevision merken.

        Rein diagnostisch. Aktualisiert bei jeder Options-Flow-Änderung,
        nicht nur bei tariff-relevanten Feldern - die Genauigkeit "nur bei
        echter Tarifänderung" wäre für einen reinen Diagnosewert
        unverhältnismäßiger Aufwand. Historische Beträge bleiben davon
        unberührt: Eine Tarifänderung wirkt ausschließlich prospektiv, weil
        jeder künftige Delta-Schritt einfach den dann aktuellen Preis
        verwendet (siehe _accumulate_economics) - nichts wird rückwirkend
        neu berechnet.
        """
        self._last_tariff_revision_at = dt_util.utcnow()
        self._async_schedule_economics_save()

    async def async_load_economics_state(self) -> None:
        """Load the persisted money balance before the first device refresh."""
        try:
            state = await self._economics_store.async_load()
        except (HomeAssistantError, NotImplementedError, OSError, ValueError) as err:
            # Der vorhandene Store ist unlesbar, aber nicht zwangsläufig
            # leer - ein anschließend aus lauter Nullen neu gebootstrapptes
            # Bilanz-Objekt darf ihn deshalb nie überschreiben. Bootstrap
            # und Akkumulation bleiben bis zur Wiederherstellung eingefroren.
            _LOGGER.warning(
                "Wirtschaftlichkeitszustand konnte nicht geladen werden; "
                "Bilanz bleibt bis zur Wiederherstellung eingefroren: %s",
                err,
            )
            self._economics_store_loaded = True
            self._economics_store_write_blocked = True
            return

        legacy_result_history = (
            state is not None and state.operating_result_high_water_eur is None
        )
        if state is not None and state.initialized:
            self._economics_grid_charge_cost_eur = state.grid_charge_cost_eur
            self._economics_pv_opportunity_cost_eur = state.pv_opportunity_cost_eur
            self._economics_avoided_grid_cost_eur = state.avoided_grid_cost_eur
            raw_result = (
                state.avoided_grid_cost_eur
                - state.grid_charge_cost_eur
                - state.pv_opportunity_cost_eur
            )
            self._economics_operating_result_high_water_eur = (
                compute_operating_result_high_water(
                    state.operating_result_high_water_eur or 0.0,
                    raw_result,
                )
            )
            self._economics_unvalued_inventory_kwh = state.unvalued_inventory_kwh
            self._economics_unpriced_charge_kwh = state.unpriced_charge_kwh
            self._economics_unpriced_discharge_kwh = state.unpriced_discharge_kwh
            self._economics_started_at = state.economics_started_at
            # REQ-ECONOMICS-OBSERVABILITY: additiv zum Sieben-Felder-Bündel
            # oben - ein Store aus der Zeit davor kennt diese beiden Felder
            # noch nicht und beginnt die Abdeckungszählung transparent bei 0
            # ab jetzt, analog zur Herkunftszählung aus REQ-ENERGY-ORIGIN
            # (siehe _bootstrap_energy_origin).
            self._economics_priced_charge_kwh = state.priced_charge_kwh or 0.0
            self._economics_priced_discharge_kwh = state.priced_discharge_kwh or 0.0
        if state is not None:
            self._last_tariff_revision_at = state.last_tariff_revision_at
            self._economics_last_restart_at = state.last_restart_at
            self._economics_last_restart_reason = state.last_restart_reason
        if state is not None and state.initialized:
            # Stores bis Minor-Version 5 enthalten Tageswerte mit einer
            # anderen Snapshot-Semantik. Deshalb startet ihre Tageshistorie
            # neu; die drei Rohsummen und ihr aktuelles signiertes Ergebnis
            # bleiben vollständig erhalten.
            self._economics_day_results = (
                () if legacy_result_history else state.day_results
            )
            self._economics_payback_achieved_at = state.payback_achieved_at
            if not legacy_result_history and state.current_day is not None:
                self._economics_current_day = state.current_day
                self._economics_current_day_operating_result_eur = (
                    state.current_day_operating_result_eur
                )
                self._economics_current_day_priced_charge_kwh = (
                    state.current_day_priced_charge_kwh
                )
                self._economics_current_day_unpriced_charge_kwh = (
                    state.current_day_unpriced_charge_kwh
                )
                self._economics_current_day_priced_discharge_kwh = (
                    state.current_day_priced_discharge_kwh
                )
                self._economics_current_day_unpriced_discharge_kwh = (
                    state.current_day_unpriced_discharge_kwh
                )
                self._economics_current_day_observed_seconds = (
                    state.current_day_observed_seconds
                )
        self._economics_store_loaded = True

    def _economics_state(self) -> EconomicsState:
        return EconomicsState(
            grid_charge_cost_eur=self._economics_grid_charge_cost_eur,
            pv_opportunity_cost_eur=self._economics_pv_opportunity_cost_eur,
            avoided_grid_cost_eur=self._economics_avoided_grid_cost_eur,
            operating_result_high_water_eur=(
                self._economics_operating_result_high_water_eur
            ),
            unvalued_inventory_kwh=self._economics_unvalued_inventory_kwh,
            unpriced_charge_kwh=self._economics_unpriced_charge_kwh,
            unpriced_discharge_kwh=self._economics_unpriced_discharge_kwh,
            economics_started_at=self._economics_started_at,
            last_tariff_revision_at=self._last_tariff_revision_at,
            day_results=self._economics_day_results,
            current_day=self._economics_current_day,
            current_day_operating_result_eur=(
                self._economics_current_day_operating_result_eur
            ),
            current_day_priced_charge_kwh=(
                self._economics_current_day_priced_charge_kwh
            ),
            current_day_unpriced_charge_kwh=(
                self._economics_current_day_unpriced_charge_kwh
            ),
            current_day_priced_discharge_kwh=(
                self._economics_current_day_priced_discharge_kwh
            ),
            current_day_unpriced_discharge_kwh=(
                self._economics_current_day_unpriced_discharge_kwh
            ),
            current_day_observed_seconds=(self._economics_current_day_observed_seconds),
            payback_achieved_at=self._economics_payback_achieved_at,
            priced_charge_kwh=self._economics_priced_charge_kwh,
            priced_discharge_kwh=self._economics_priced_discharge_kwh,
            last_restart_at=self._economics_last_restart_at,
            last_restart_reason=self._economics_last_restart_reason,
        )

    def _async_schedule_economics_save(self) -> None:
        if self._economics_store_write_blocked:
            return
        state = self._economics_state()
        if not (self._economics_store_loaded and state.initialized):
            return
        if not self._economics_store.async_delay_save(state):
            # _accept() hat den Snapshot bereits synchron als korrupt/
            # regressiv abgelehnt (siehe infrastructure/economics_store.py)
            # - ab hier ist der gespeicherte Zustand nicht mehr
            # vertrauenswürdig. Ein erst NACH der Verzögerung auftretender
            # echter Schreibfehler kann an dieser Stelle noch nicht bekannt
            # sein (async_delay_save schreibt asynchron) und wird
            # stattdessen über _on_economics_persist_failed gemeldet.
            # Status storage_error, keine weitere Akkumulation, bis ein
            # Neuladen des Config Entry eine frische Instanz erzeugt
            # (REQ-ECONOMICS-OBSERVABILITY) - siehe auch
            # async_load_economics_state für den spiegelbildlichen Fall
            # eines Ladefehlers.
            _LOGGER.warning(
                "Wirtschaftlichkeitszustand beim Speichern abgelehnt - "
                "Bilanz wird eingefroren, bis der Config Entry neu geladen "
                "wird"
            )
            self._economics_store_write_blocked = True

    def _on_economics_persist_failed(self) -> None:
        """Callback aus EconomicsStateStore (siehe deren Klassen-Docstring):
        meldet einen erst nach der Verzögerung von async_delay_save
        erkannten, tatsächlichen Schreibfehler (Lese-Rückprobe gegen die
        Datei) - der synchrone Rückgabewert von async_delay_save deckt nur
        die sofortige _accept()-Ablehnung ab, nicht das asynchrone
        Schreibergebnis selbst."""
        if self._economics_store_write_blocked:
            return
        _LOGGER.warning(
            "Wirtschaftlichkeitszustand konnte im Hintergrund nicht "
            "gespeichert werden - Bilanz wird eingefroren, bis der Config "
            "Entry neu geladen wird"
        )
        self._economics_store_write_blocked = True

    async def _async_flush_economics_state(self) -> None:
        if self._economics_store_write_blocked:
            return
        state = self._economics_state()
        if not self._economics_store_loaded or not state.initialized:
            return
        try:
            saved = await self._economics_store.async_save(state)
        except (HomeAssistantError, OSError, ValueError) as err:
            _LOGGER.warning(
                "Wirtschaftlichkeitszustand konnte beim Entladen nicht "
                "gespeichert werden: %s",
                err,
            )
            self._economics_store_write_blocked = True
            return
        if not saved:
            _LOGGER.warning(
                "Wirtschaftlichkeitszustand beim Entladen abgelehnt - "
                "Bilanz wird eingefroren, bis der Config Entry neu geladen "
                "wird"
            )
            self._economics_store_write_blocked = True

    async def async_restart_economics_accounting(
        self, *, reason: str | None = None
    ) -> None:
        """Kontrollierter Bilanzneustart (REQ-ECONOMICS-OBSERVABILITY,
        Service `sax_power.restart_economics_accounting`).

        Setzt AUSSCHLIESSLICH die drei Economics-Geldsummen, den
        historischen Diagnose-Peak, die Preisabdeckungszähler
        (priced_*/unpriced_*), die Tages-Buckets, den
        Aktivierungs-/Revisionszeitpunkt und einen bereits erreichten
        Payback-Zeitpunkt zurück, setzt den unbewerteten Bestand wie beim
        erstmaligen Aktivieren auf 0 - und rührt dabei nie
        `energy_charged`/`energy_discharged` oder die
        Herkunftszähler aus REQ-ENERGY-ORIGIN an. `reason` ist rein
        diagnostisch: er wird zusammen mit dem UTC-Zeitpunkt dieses
        Neustarts persistiert (EconomicsState.last_restart_at/
        last_restart_reason) und im Diagnose-Download angezeigt -
        beeinflusst aber keine Berechnung.

        Speichert atomar VOR jeder In-Memory-Änderung: schlägt das
        Speichern fehl, bleibt der bisherige Zustand vollständig und
        unverändert bestehen (kein halb angewendeter Neustart). Keine
        rückwirkende Neuberechnung und kein automatischer Reset bei einer
        späteren Tarif-/Investitionsänderung - das war schon vorher so und
        ändert sich durch diesen Service nicht.
        """
        economics_ready = (
            self.tariff_provider.config.enabled
            and self._economics_started_at is not None
        )
        if not economics_ready:
            raise ServiceValidationError(
                "Ein Bilanzneustart ist nur möglich, solange die "
                "Wirtschaftlichkeit aktiviert und bereits initialisiert ist",
                translation_domain=DOMAIN,
                translation_key="economics_restart_not_ready",
            )

        now = dt_util.utcnow()
        new_state = replace(
            self._economics_state(),
            grid_charge_cost_eur=0.0,
            pv_opportunity_cost_eur=0.0,
            avoided_grid_cost_eur=0.0,
            operating_result_high_water_eur=0.0,
            unvalued_inventory_kwh=0.0,
            unpriced_charge_kwh=0.0,
            unpriced_discharge_kwh=0.0,
            priced_charge_kwh=0.0,
            priced_discharge_kwh=0.0,
            economics_started_at=now,
            last_tariff_revision_at=now,
            day_results=(),
            current_day=None,
            current_day_operating_result_eur=None,
            current_day_priced_charge_kwh=None,
            current_day_unpriced_charge_kwh=None,
            current_day_priced_discharge_kwh=None,
            current_day_unpriced_discharge_kwh=None,
            current_day_observed_seconds=None,
            payback_achieved_at=None,
            last_restart_at=now,
            last_restart_reason=reason,
        )
        if not await self._economics_store.async_reset(new_state):
            raise HomeAssistantError(
                "Bilanzneustart konnte nicht gespeichert werden - der "
                "bisherige Zustand bleibt unverändert bestehen"
            )

        self._economics_grid_charge_cost_eur = 0.0
        self._economics_pv_opportunity_cost_eur = 0.0
        self._economics_avoided_grid_cost_eur = 0.0
        self._economics_operating_result_high_water_eur = 0.0
        self._economics_unvalued_inventory_kwh = 0.0
        self._economics_unpriced_charge_kwh = 0.0
        self._economics_unpriced_discharge_kwh = 0.0
        self._economics_priced_charge_kwh = 0.0
        self._economics_priced_discharge_kwh = 0.0
        self._economics_started_at = now
        self._last_tariff_revision_at = now
        self._economics_day_results = ()
        self._economics_current_day = None
        self._economics_current_day_operating_result_eur = None
        self._economics_current_day_priced_charge_kwh = None
        self._economics_current_day_unpriced_charge_kwh = None
        self._economics_current_day_priced_discharge_kwh = None
        self._economics_current_day_unpriced_discharge_kwh = None
        self._economics_current_day_observed_seconds = None
        self._economics_payback_achieved_at = None
        self._economics_price_unavailable_since = None
        self._economics_price_unavailable = False
        self._economics_last_restart_at = now
        self._economics_last_restart_reason = reason
        _LOGGER.info(
            "Wirtschaftlichkeitsbilanz manuell neu gestartet (%s)%s",
            now.isoformat(),
            f" - Grund: {reason}" if reason else "",
        )

    @property
    def energy_diagnostics(self) -> dict[str, Any]:
        """Interner Zählerzustand für den Diagnose-Download (diagnostics.py).

        Gegenstück zu economics_diagnostics: die ungerundeten Rohsummen und
        vor allem origin_accounting_started_at. Ohne diesen Zeitstempel
        ließ sich aus einem Diagnose-Download nicht entscheiden, ob eine
        Differenz zwischen Herkunftszählern und Geldbilanz ein Rechenfehler
        ist oder nur zwei verschiedene Zählzeiträume - siehe
        _energy_origin_attributes.
        """
        return {
            "origin_accounting_started_at": (
                None
                if self._origin_accounting_started_at is None
                else self._origin_accounting_started_at.isoformat()
            ),
            "charged_kwh": self._energy_charged_kwh,
            "discharged_kwh": self._energy_discharged_kwh,
            "grid_charged_kwh": self._energy_grid_charged_kwh,
            "pv_charged_kwh": self._energy_pv_charged_kwh,
        }

    @property
    def economics_diagnostics(self) -> dict[str, Any]:
        """Interner Bilanzzustand für den Diagnose-Download (diagnostics.py).

        Anders als coordinator.data (nur die zuletzt veröffentlichten,
        gerundeten Sensorwerte) zeigt dies zusätzlich die beiden
        Zeitstempel sowie die ungerundeten Rohsummen.
        """
        return {
            "started_at": (
                None
                if self._economics_started_at is None
                else self._economics_started_at.isoformat()
            ),
            "last_tariff_revision_at": (
                None
                if self._last_tariff_revision_at is None
                else self._last_tariff_revision_at.isoformat()
            ),
            "grid_charge_cost_eur": self._economics_grid_charge_cost_eur,
            "pv_opportunity_cost_eur": self._economics_pv_opportunity_cost_eur,
            "avoided_grid_cost_eur": self._economics_avoided_grid_cost_eur,
            "operating_result_raw_eur": (
                None
                if self._economics_avoided_grid_cost_eur is None
                or self._economics_grid_charge_cost_eur is None
                or self._economics_pv_opportunity_cost_eur is None
                else self._economics_avoided_grid_cost_eur
                - self._economics_grid_charge_cost_eur
                - self._economics_pv_opportunity_cost_eur
            ),
            "operating_result_high_water_eur": (
                self._economics_operating_result_high_water_eur
            ),
            "unvalued_inventory_kwh": self._economics_unvalued_inventory_kwh,
            "unpriced_charge_kwh": self._economics_unpriced_charge_kwh,
            "unpriced_discharge_kwh": self._economics_unpriced_discharge_kwh,
            "inventory_capped_kwh": self._economics_inventory_capped_kwh,
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
                for day in self._economics_day_results
            ],
            "current_day": (
                None
                if self._economics_current_day is None
                else self._economics_current_day.isoformat()
            ),
            "current_day_operating_result_eur": (
                self._economics_current_day_operating_result_eur
            ),
            "current_day_priced_charge_kwh": (
                self._economics_current_day_priced_charge_kwh
            ),
            "current_day_unpriced_charge_kwh": (
                self._economics_current_day_unpriced_charge_kwh
            ),
            "current_day_priced_discharge_kwh": (
                self._economics_current_day_priced_discharge_kwh
            ),
            "current_day_unpriced_discharge_kwh": (
                self._economics_current_day_unpriced_discharge_kwh
            ),
            "current_day_observed_seconds": (
                self._economics_current_day_observed_seconds
            ),
            "payback_achieved_at": (
                None
                if self._economics_payback_achieved_at is None
                else self._economics_payback_achieved_at.isoformat()
            ),
            # -- REQ-ECONOMICS-OBSERVABILITY -------------------------------
            "status": (self.data or {}).get("economics_status"),
            "store_write_blocked": self._economics_store_write_blocked,
            "store_minor_version": ECONOMICS_STORE_MINOR_VERSION,
            "priced_charge_kwh": self._economics_priced_charge_kwh,
            "priced_discharge_kwh": self._economics_priced_discharge_kwh,
            "price_unavailable": self._economics_price_unavailable,
            "last_successful_quote_at": (
                None
                if self._economics_last_successful_quote_at is None
                else self._economics_last_successful_quote_at.isoformat()
            ),
            "last_restart_at": (
                None
                if self._economics_last_restart_at is None
                else self._economics_last_restart_at.isoformat()
            ),
            "last_restart_reason": self._economics_last_restart_reason,
        }

    async def async_load_energy_state(self) -> None:
        """Load the independent counters before the first device refresh."""
        try:
            state = await self._energy_store.async_load()
        except (HomeAssistantError, NotImplementedError, OSError, ValueError) as err:
            # NotImplementedError: Home Assistant meldet damit einen Store
            # mit einer Hauptversion, für die es hier keine Migration gibt
            # (siehe infrastructure/energy_store.py, STORAGE_VERSION-
            # Kommentar) - typischerweise ein Downgrade auf eine ältere
            # Integrationsversion nach einem zwischenzeitlichen Update.
            _LOGGER.warning(
                "Energiezählerzustand konnte nicht geladen werden; "
                "warte auf einen numerischen Altzustand: %s",
                err,
            )
            self._energy_store_loaded = True
            return

        if state is not None:
            self._energy_charged_kwh = state.charged_kwh
            self._energy_discharged_kwh = state.discharged_kwh
        self._bootstrap_energy_origin(state)
        self._energy_store_loaded = True

    def _bootstrap_energy_origin(self, state: EnergyState | None) -> None:
        """Startet die Herkunftszählung transparent ab jetzt.

        Läuft nur, wenn der Store selbst erfolgreich gelesen wurde - state
        ist hier None nur bei einer frischen Installation (kein
        gespeichertes Objekt), nicht bei einem I/O-Fehler; der bleibt in
        async_load_energy_state unbehandelt, damit ein defekter Store
        keinen stillen Nullstart der Herkunft auslöst.

        Ein bereits vollständig initialisierter Store
        (state.origin_initialized) übernimmt seine Werte unverändert. In
        jedem anderen Fall - brandneuer Eintrag, Version-1-Snapshot ohne
        diese Felder, oder ein einzelnes beim Laden verworfenes Feld -
        beginnt die Herkunftszählung jetzt bei 0 mit dem aktuellen
        UTC-Zeitpunkt als origin_accounting_started_at. Historische
        Ladeenergie wird dabei nicht rückwirkend zugeordnet (siehe
        anforderung.yaml, REQ-ENERGY-ORIGIN); der bestehende
        energy_charged-Gesamtzähler bleibt davon unberührt. Der neue Stand
        wird bewusst nicht sofort geschrieben, sondern über den normalen
        Speicherpfad (Änderung oder Shutdown-Flush) persistiert - kein
        zusätzlicher Schreibvorgang allein durch das Laden.
        """
        if state is not None and state.origin_initialized:
            self._energy_grid_charged_kwh = state.grid_charged_kwh
            self._energy_pv_charged_kwh = state.pv_charged_kwh
            self._origin_accounting_started_at = state.origin_accounting_started_at
            return
        self._energy_grid_charged_kwh = 0.0
        self._energy_pv_charged_kwh = 0.0
        self._origin_accounting_started_at = dt_util.utcnow()

    def restore_energy_charged(self, value_kwh: float | None) -> None:
        """Migrate a numeric legacy RestoreEntity charge counter once."""
        self._restore_legacy_energy("_energy_charged_kwh", "Laden", value_kwh)

    def restore_energy_discharged(self, value_kwh: float | None) -> None:
        """Migrate a numeric legacy RestoreEntity discharge counter once."""
        self._restore_legacy_energy("_energy_discharged_kwh", "Entladen", value_kwh)

    def _restore_legacy_energy(
        self, attribute: str, label: str, value_kwh: float | None
    ) -> None:
        current = getattr(self, attribute)
        if current is not None:
            if value_kwh is not None and value_kwh < current:
                _LOGGER.warning(
                    "Rückläufigen RestoreEntity-Altzustand für %s verworfen: "
                    "%r statt mindestens %r",
                    label,
                    value_kwh,
                    current,
                )
            return
        if (
            value_kwh is None
            or isinstance(value_kwh, bool)
            or not math.isfinite(value_kwh)
            or value_kwh < 0
        ):
            if value_kwh is not None:
                _LOGGER.warning(
                    "Ungültigen RestoreEntity-Altzustand für %s verworfen: %r",
                    label,
                    value_kwh,
                )
            return
        setattr(self, attribute, float(value_kwh))
        self._async_schedule_energy_save()

    def _energy_state(self) -> EnergyState:
        return EnergyState(
            charged_kwh=self._energy_charged_kwh,
            discharged_kwh=self._energy_discharged_kwh,
            grid_charged_kwh=self._energy_grid_charged_kwh,
            pv_charged_kwh=self._energy_pv_charged_kwh,
            origin_accounting_started_at=self._origin_accounting_started_at,
        )

    def _async_schedule_energy_save(self) -> None:
        state = self._energy_state()
        if self._energy_store_loaded and state.initialized:
            self._energy_store.async_delay_save(state)

    async def _async_flush_energy_state(self) -> None:
        state = self._energy_state()
        if not self._energy_store_loaded or not state.initialized:
            return
        try:
            await self._energy_store.async_save(state)
        except (HomeAssistantError, OSError, ValueError) as err:
            # Der Modbus-/Unload-Pfad muss auch bei lokal defektem Storage
            # vollständig aufräumen; der Store versucht beim regulären HA-
            # Stop zusätzlich seinen registrierten Final-Write.
            _LOGGER.warning(
                "Energiezählerzustand konnte beim Entladen nicht gespeichert "
                "werden: %s",
                err,
            )

    async def _async_read_basic(self) -> dict[str, Any]:
        """Liest den NORMAL-Block (Basic Mode, Slave-ID self.slave_id) nur
        alle self._scan_interval Sekunden neu ein - unabhängig vom (durch
        READ_BLOCK_EXT_HIGH_INTERVAL vorgegebenen, i. d. R. kürzeren)
        Coordinator-Timer, siehe __init__ sowie anforderung.yaml,
        REQ-HIGH-INTERVAL-REGISTERS. Anders als beim LOW-Block
        (_async_read_low_block) lässt ein fehlgeschlagener Read weiterhin
        das gesamte Update fehlschlagen (UpdateFailed) - Basic Mode bleibt
        die Mindestanforderung für jede Funktion der Integration."""
        now = monotonic()
        if (
            self._basic_data
            and self._basic_last_read is not None
            and now - self._basic_last_read < self._scan_interval
        ):
            return self._basic_data

        try:
            if not self.client.connected:
                await self.client.connect()
            basic_result = await self.client.read_holding_registers(
                address=READ_BLOCK_START,
                count=READ_BLOCK_COUNT,
                device_id=self.slave_id,
            )
        except (TimeoutError, ModbusException) as err:
            raise UpdateFailed(
                f"Fehler bei der Kommunikation mit dem SAX Speicher (Basic Mode, "
                f"Slave-ID {self.slave_id}): {err}"
            ) from err
        if basic_result.isError():
            raise UpdateFailed(f"Modbus-Fehlerantwort (Basic Mode): {basic_result}")

        basic_regs = basic_result.registers

        def basic_reg(address: int) -> int:
            return basic_regs[address - READ_BLOCK_START]

        switch_state = basic_reg(REG_SWITCH_STATE)
        self._basic_data = {
            "switch_state": switch_state,
            "switch_state_text": SWITCH_STATE_LABELS.get(
                switch_state, SWITCH_STATE_UNKNOWN_LABEL
            ),
            "setpoint_power": to_signed16(basic_reg(REG_SETPOINT_POWER)),
            "setpoint_cosphi": to_signed16(basic_reg(REG_SETPOINT_COSPHI)),
            "soc": basic_reg(REG_SOC),
        }
        self._basic_last_read = now
        return self._basic_data

    async def _async_read_extended(self) -> dict[str, Any]:
        """Orchestriert HIGH- und LOW-Intervall-Teile des SunSpec-Modus-Blocks
        (Slave-ID self.slave_id_extended, Default 100). Der LOW-Block
        (_async_read_low_block) hat sein eigenes, unabhängiges Intervall
        (READ_BLOCK_EXT_LOW_INTERVAL) und wird deshalb bei jedem Tick
        geprüft; der HIGH-Block (_async_read_high_block) wird nur alle
        READ_BLOCK_EXT_HIGH_INTERVAL Sekunden tatsächlich neu vom Gerät
        gelesen. Muss der LOW-Block VOR dem HIGH-Block laufen: Letzterer
        skaliert die Battery-Messwerte mit den dort aktualisierten
        self._battery_scale_factors, statt sie selbst aus dem (inzwischen
        kleineren) HIGH-Block zu lesen - siehe anforderung.yaml,
        REQ-LOW-INTERVAL-REGISTERS/REQ-HIGH-INTERVAL-REGISTERS."""
        data = dict(await self._async_read_low_block())
        data.update(await self._async_read_high_block())
        return data

    @property
    def extended_available(self) -> bool:
        """Ob der SunSpec-Modus-Block zuletzt erreichbar war (siehe
        anforderung.yaml, REQ-EXTENDED-MODE-RESILIENCE) - u. a. für
        diagnostics.py."""
        return self._extended_available

    async def _async_read_high_block(self) -> dict[str, Any]:
        """Read+parse den HIGH-Block (dynamische Mess-/Zustandswerte) des
        SunSpec-Modus, ohne bei Fehlern das gesamte Update scheitern zu
        lassen (siehe Kommentar in __init__). Wird nur alle
        READ_BLOCK_EXT_HIGH_INTERVAL Sekunden tatsächlich neu vom Gerät
        gelesen, unabhängig vom nutzerkonfigurierten NORMAL-Intervall -
        siehe anforderung.yaml, REQ-HIGH-INTERVAL-REGISTERS."""
        now = monotonic()
        if (
            self._high_data
            and self._high_last_read is not None
            and now - self._high_last_read < READ_BLOCK_EXT_HIGH_INTERVAL
        ):
            return self._high_data

        try:
            extended_result = await self.client.read_holding_registers(
                address=READ_BLOCK_EXT_START,
                count=READ_BLOCK_EXT_COUNT,
                device_id=self.slave_id_extended,
            )
            if extended_result.isError():
                raise ModbusException(
                    f"Modbus-Fehlerantwort (SunSpec-Modus): {extended_result}"
                )
        except (TimeoutError, ModbusException) as err:
            if self._extended_available:
                _LOGGER.warning(
                    "SunSpec-Modus-Register (Slave-ID %s) nicht erreichbar - "
                    "Basic-Mode-Sensoren bleiben verfügbar, SunSpec-Sensoren "
                    "zeigen bis zur Wiederherstellung 'unbekannt': %s",
                    self.slave_id_extended,
                    err,
                )
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    f"{ISSUE_EXTENDED_MODE_UNAVAILABLE}_{self.entry_id}",
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key=ISSUE_EXTENDED_MODE_UNAVAILABLE,
                    translation_placeholders={"slave_id": str(self.slave_id_extended)},
                )
                self._extended_unavailable_since = monotonic()
            self._extended_available = False
            self._high_data = {}
            return {}

        if not self._extended_available:
            _LOGGER.info(
                "SunSpec-Modus-Register (Slave-ID %s) wieder erreichbar.",
                self.slave_id_extended,
            )
            ir.async_delete_issue(
                self.hass, DOMAIN, f"{ISSUE_EXTENDED_MODE_UNAVAILABLE}_{self.entry_id}"
            )
            self._extended_unavailable_since = None
        self._extended_available = True

        decoded = decode_high_block(
            extended_result.registers, self._battery_scale_factors
        )
        # Für den Schreibpfad (Watt -> Prozent-Sollwert) zwischengespeichert,
        # siehe SaxPowerCoordinator._watts_to_ic_setpoint_raw - dort erfolgt
        # die Sentinel-Prüfung dieses Rohwerts eigenständig vor jedem Write.
        self._ic_power_setpoint_sf_raw = decoded.ic_power_setpoint_sf_raw
        self._high_data = dict(decoded.values)
        self._high_last_read = now
        return self._high_data

    async def _async_read_low_block(self) -> dict[str, Any]:
        """Liest die beiden statischen LOW-Intervall-Teilbereiche des
        SunSpec-Modus-Blocks (Geräteidentität + Inverter-Modellkopf,
        Battery-Skalierungsfaktoren) nur alle READ_BLOCK_EXT_LOW_INTERVAL
        Sekunden per eigenem read_holding_registers-Aufruf neu ein, statt bei
        jedem regulären Poll - beide Teilbereiche enthalten laut
        modbus_llm.yaml ausschließlich "wellknown" fixe bzw. sich im
        laufenden Betrieb praktisch nie ändernde Werte (siehe
        anforderung.yaml, REQ-LOW-INTERVAL-REGISTERS). Zwischen den
        Refreshs werden die zuletzt gelesenen Werte weiterverwendet; ein
        Scheitern des Refreshs lässt das Update deshalb nicht fehlschlagen."""
        now = monotonic()
        if (
            self._low_block_data
            and self._low_block_last_read is not None
            and now - self._low_block_last_read < READ_BLOCK_EXT_LOW_INTERVAL
        ):
            return self._low_block_data

        try:
            low1_result = await self.client.read_holding_registers(
                address=READ_BLOCK_EXT_LOW1_START,
                count=READ_BLOCK_EXT_LOW1_COUNT,
                device_id=self.slave_id_extended,
            )
            low2_result = await self.client.read_holding_registers(
                address=READ_BLOCK_EXT_LOW2_START,
                count=READ_BLOCK_EXT_LOW2_COUNT,
                device_id=self.slave_id_extended,
            )
            if low1_result.isError() or low2_result.isError():
                raise ModbusException(
                    "Modbus-Fehlerantwort (LOW-Intervall-Register): "
                    f"{low1_result if low1_result.isError() else low2_result}"
                )
        except (TimeoutError, ModbusException) as err:
            if self._low_block_data:
                _LOGGER.debug(
                    "LOW-Intervall-Register (Slave-ID %s) nicht lesbar - "
                    "vorherige Werte werden beibehalten: %s",
                    self.slave_id_extended,
                    err,
                )
            else:
                _LOGGER.warning(
                    "LOW-Intervall-Register (Slave-ID %s) nicht lesbar - "
                    "zugehörige Sensoren zeigen bis zum ersten erfolgreichen "
                    "Refresh 'unbekannt': %s",
                    self.slave_id_extended,
                    err,
                )
            return self._low_block_data

        decoded = decode_low_blocks(low1_result.registers, low2_result.registers)
        # Die Battery-Skalierungsfaktoren stammen ausschließlich aus diesem
        # Teilblock; decode_high_block bekommt sie beim nächsten HIGH-Read
        # übergeben, statt sie selbst zu lesen (REQ-LOW-INTERVAL-REGISTERS).
        self._battery_scale_factors = decoded.scale_factors
        self._low_block_data = decoded.values
        self._low_block_last_read = now
        return self._low_block_data

    async def async_write_register(self, address: int, value: int) -> None:
        """Write a single Basic-Mode holding register (Slave-ID self.slave_id),
        raising HomeAssistantError on failure. Erzwingt beim nächsten
        _async_read_basic-Aufruf einen echten Read, unabhängig vom
        NORMAL-Intervall-Throttle - sonst könnte ein direkt nach dem
        Schreiben ausgelöster coordinator.async_refresh() (siehe
        switch.SaxPowerStorageSwitch) kurzzeitig noch den alten,
        gecachten Wert liefern (siehe DEVELOPMENT.md, "Refresh-Verhalten")."""
        await self._async_write_register(address, value, device_id=self.slave_id)
        self._basic_last_read = None

    async def async_write_extended_register(self, address: int, value: int) -> None:
        """Write a single SunSpec-Modus holding register (Slave-ID
        self.slave_id_extended, interne Adresse = Protokolladresse - 40000),
        raising HomeAssistantError on failure."""
        await self._async_write_register(
            address, value, device_id=self.slave_id_extended
        )
        # Ein erfolgreicher Write macht den zuletzt gelesenen HIGH-Block
        # potentiell veraltet. Der nächste Coordinator-Takt muss deshalb
        # tatsächlich vom Gerät lesen und darf nicht den bis zu zwei
        # Sekunden alten Cache erneut veröffentlichen.
        self._high_last_read = None

    async def _async_write_register(
        self, address: int, value: int, *, device_id: int
    ) -> None:
        async with self._write_lock:
            try:
                if not self.client.connected:
                    await self.client.connect()
                result = await self.client.write_register(
                    address=address, value=to_unsigned16(value), device_id=device_id
                )
            except (TimeoutError, ModbusException) as err:
                raise HomeAssistantError(
                    f"Schreiben von Register {address} (Slave-ID {device_id}) "
                    f"fehlgeschlagen: {err}"
                ) from err
            if result.isError():
                raise HomeAssistantError(
                    f"Modbus-Fehler beim Schreiben von Register {address} "
                    f"(Slave-ID {device_id}): {result}"
                )

    # -- Max-SOC -----------------------------------------------------------
    # SAX kennt kein natives Max-SOC-Register. Der Coordinator erzwingt den
    # Zielwert stattdessen über denselben SunSpec-Modus-Pfad wie das
    # zeitgesteuerte Laden weiter unten (_async_enforce_grid_charge,
    # _async_sun_charge_loop): Register 40051 (Steuermodus) auf 1
    # (Sollwertvorgabe) und Register 40049 (Leistungsvorgabe) auf 0 %,
    # sobald der SOC den Zielwert erreicht/überschreitet - bewusst
    # unabhängig davon, ob gerade zeitgesteuert geladen wird (siehe
    # anforderung.yaml, REQ-TIMED-SOC-CHARGE): so wird z. B. auch ein durch
    # PV-Überschuss auf den Zielwert geladener Speicher aktiv dort gehalten,
    # statt durch die geräteeigene Automatik (SmartMeter-Nullregelung)
    # darüber hinaus weitergeladen oder unterhalb des Zielwerts
    # leergefahren zu werden. Fällt der SOC wieder unter den Zielwert,
    # wird Register 40051 zurück auf 0 gesetzt.
    #
    # Wurde die Sperre dagegen INNERHALB eines Netzlade- oder netzdienlich-
    # Zeitfensters ausgelöst (_max_soc_hold_is_window_bound), gilt sie nur
    # bis zum Ende genau dieses Zeitfensters: solange das Fenster noch läuft,
    # wird Register 40051 periodisch auf 1 nachgeschrieben (sonst fällt das
    # Gerät nach Ablauf des Timeouts, Register 40050, von selbst auf
    # Nullregelung zurück); ist das Fenster vorbei, wird Register 40051
    # aktiv auf 0 zurückgesetzt, statt den Speicher unbegrenzt im
    # Sollwertmodus zu halten - siehe _async_enforce_grid_charge.
    #
    # Außerhalb jedes Zeitfensters gilt die Sperre grundsätzlich unbegrenzt,
    # ABER: bei gehaltenem 0-%-Sollwert deckt der Speicher den Hausverbrauch
    # nicht mehr mit (Register 40049 = 0 heißt Netto-Leistungsfluss = 0, kein
    # Laden UND kein Entladen), der SOC fällt dadurch im Normalfall nie von
    # selbst unter den Zielwert. Deshalb wertet _async_enforce_grid_charge in
    # diesem Fall zusätzlich am Smart Meter gemessenen Netzbezug
    # (smartmeter_power > SMARTMETER_PV_SURPLUS_THRESHOLD_WATT) als
    # Freigabe-Trigger aus - mit derselben Zyklen-Hysterese
    # (_cycles_confirmed/_max_soc_grid_import_wait_cycles,
    # PV_SURPLUS_HYSTERESIS_CYCLES) wie an den drei anderen Stellen, die
    # diesen Schwellwert auswerten, damit kurze Lastspitzen die Sperre nicht
    # sofort aufheben. Register 40051 wird dann aktiv auf 0
    # (SmartMeter-Nullregelung) zurückgesetzt, damit die geräteeigene
    # Automatik den Hausverbrauch wieder aus dem Speicher decken kann.
    # Diese bestätigte Freigabe bleibt verriegelt, solange der SOC nicht
    # wirklich unter den wirksamen Zielwert fällt. Ohne diesen Latch würde
    # der nächste Poll bei unverändertem SOC sofort wieder 0 % anfordern und
    # die Register zwischen beiden Modi flattern lassen (REQ-TIMED-SOC-CHARGE).

    @property
    def max_soc(self) -> int | None:
        """Return the persistent max SOC configured by the user."""
        return self._max_soc

    @property
    def effective_max_soc(self) -> int:
        """Return the target SOC after applying the calibration override."""
        if self._cell_calibration_active:
            return MAX_SOC
        return self._max_soc if self._max_soc is not None else MAX_SOC

    @property
    def cell_calibration_active(self) -> bool:
        return self._cell_calibration_active

    @property
    def last_full_charge_at(self) -> datetime | None:
        return self._cell_calibration_state.last_full_charge_at

    @property
    def next_cell_calibration_at(self) -> datetime | None:
        last_full_charge_at = self.last_full_charge_at
        if last_full_charge_at is None:
            return None
        return last_full_charge_at + CELL_CALIBRATION_INTERVAL

    @property
    def max_soc_clamped(self) -> bool:
        return self._max_soc_clamped

    async def async_load_calibration_state(self) -> None:
        """Load the calibration schedule before the first device refresh."""
        try:
            state = await self._calibration_store.async_load()
        except (HomeAssistantError, OSError, ValueError) as err:
            _LOGGER.warning(
                "Zellkalibrierungszustand konnte nicht geladen werden; "
                "beginne mit neuer Baseline: %s",
                err,
            )
            return
        if state is not None:
            self._cell_calibration_state = state

    async def _async_update_cell_calibration(
        self, current_soc: int | float, *, now: datetime | None = None
    ) -> bool:
        """Evaluate and persist calibration edges; return active-state change."""
        decision = evaluate_calibration(
            now=now or dt_util.utcnow(),
            current_soc=current_soc,
            configured_max_soc=self._max_soc,
            state=self._cell_calibration_state,
            interval=CELL_CALIBRATION_INTERVAL,
            maximum_soc=MAX_SOC,
        )
        active_changed = decision.calibration_active != self._cell_calibration_active
        self._cell_calibration_state = decision.state
        self._cell_calibration_active = decision.calibration_active
        if decision.state_changed:
            try:
                await self._calibration_store.async_save(decision.state)
            except (HomeAssistantError, OSError, ValueError) as err:
                # REQ-PERIODIC-FULL-CALIBRATION: Ein lokaler Storage-Fehler
                # darf die sicherheitsrelevante Modbus-Auswertung nicht
                # abbrechen; die laufende Instanz behält den Zustand im RAM.
                _LOGGER.warning(
                    "Zellkalibrierungszustand konnte nicht gespeichert werden: %s",
                    err,
                )
        return active_changed

    # -- Persistenz der Ladeeinstellungen (REQ-CONTROL-CONFIG-BOOTSTRAP) -----
    # Alle softwareseitigen Steuerwerte (Max-SOC, Zeitfenster, Monate,
    # Schalter, Strategie und Preisparameter) liegen in einem versionierten,
    # vom sichtbaren Entity-Zustand unabhängigen Store. Er wird vollständig
    # geladen, bevor der erste Refresh überhaupt steuern darf; die
    # RestoreEntity-Zustände der Plattformen sind nur noch der einmalige
    # Migrationspfad für Einträge, für die es noch keinen Store gibt.
    # Dadurch kann ein "unknown"/"unavailable" gewordener Entity-Zustand
    # (z. B. bei Basic-Modbus-Ausfall) keinen gespeicherten Wert mehr als
    # Default oder "aus" überschreiben.

    @property
    def control_config_status(self) -> ControlConfigLoadStatus:
        """Woher die aktuell gültige Ladekonfiguration stammt."""
        return self._control_config_status

    @property
    def control_config_migration_pending(self) -> bool:
        """True, wenn der einmalige RestoreEntity-Migrationspfad greifen darf.

        Ausschließlich bei ControlConfigLoadStatus.MISSING, also solange es
        für diesen Config Entry noch gar keinen Store gibt. Bei LOADED ist
        der Store die alleinige Quelle; bei FAILED gelten sichere Defaults -
        in beiden Fällen darf ein veralteter Entity-Zustand nicht
        einspringen (number.py/switch.py/select.py/time.py)."""
        return self._control_config_status is ControlConfigLoadStatus.MISSING

    @property
    def control_bootstrap_pending(self) -> bool:
        """True zwischen async_load_control_state und async_finish_bootstrap."""
        return self._control_bootstrap_pending

    @property
    def control_config_unresolved_fields(self) -> frozenset[str]:
        """Feldnamen, deren Wert derzeit nicht als bestätigt gilt.

        Siehe mark_control_field_unresolved für die Bedeutung."""
        return frozenset(self._control_unresolved_fields)

    def mark_control_field_unresolved(self, field: str) -> None:
        """Markiert `field`, weil sein RestoreEntity-Altzustand nicht
        verwertbar war (unknown/unavailable/unparsebar, siehe
        entity.log_unmigratable_state).

        Bleibt gesetzt und wird mitgespeichert (control_config(),
        infrastructure/control_store.py), bis clear_control_field_unresolved
        läuft - also bis der Anwender diese Einstellung bewusst über ihre
        Entity neu setzt. sanitized() füllt trotzdem sofort einen sicheren
        Hard-Default, damit der Betrieb nicht blockiert; dieses Set ist die
        einzige Stelle, an der sichtbar bleibt, dass es sich dabei nicht um
        einen bestätigten Anwenderwert handelt (REQ-CONTROL-CONFIG-
        BOOTSTRAP, Akzeptanzkriterium "unknown/unavailable gilt nie als
        ausdrückliches Aus oder Default")."""
        self._control_unresolved_fields.add(field)

    def clear_control_field_unresolved(self, field: str) -> None:
        """Bestätigt `field` als ausdrücklichen Anwenderwert.

        Von jedem betroffenen async_set_*-Setter aufgerufen, sobald er den
        Wert tatsächlich übernimmt - unabhängig davon, ob das Feld überhaupt
        als unresolved markiert war (dann ein No-Op). Synchronisiert danach
        den Reparaturhinweis neu, außer der Bootstrap läuft noch - dessen
        Abschluss übernimmt das selbst (async_finish_bootstrap)."""
        self._control_unresolved_fields.discard(field)
        if not self._control_bootstrap_pending:
            self._async_sync_unresolved_fields_issue()

    def _async_sync_unresolved_fields_issue(self) -> None:
        """Legt den Reparaturhinweis für nicht migrierte Felder an oder
        entfernt ihn - siehe mark_control_field_unresolved."""
        issue_id = f"{ISSUE_CONTROL_CONFIG_UNRESOLVED}_{self.entry_id}"
        if not self._control_unresolved_fields:
            ir.async_delete_issue(self.hass, DOMAIN, issue_id)
            return
        labels = sorted(
            _CONTROL_FIELD_LABELS.get(field, field)
            for field in self._control_unresolved_fields
        )
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_CONTROL_CONFIG_UNRESOLVED,
            translation_placeholders={"fields": ", ".join(labels)},
        )

    def control_config(self) -> ControlConfig:
        """Aktueller Stand aller softwareseitigen Steuerwerte."""
        return ControlConfig(
            max_soc=self._max_soc,
            timed_charge_enabled=self._timed_charge_enabled,
            timed_charge_start=self._timed_charge_start,
            timed_charge_end=self._timed_charge_end,
            timed_charge_months=frozenset(self._timed_charge_months),
            timed_charge_min_soc=self._timed_charge_min_soc,
            grid_serving_enabled=self._grid_serving_enabled,
            grid_serving_start=self._grid_serving_start,
            grid_serving_end=self._grid_serving_end,
            grid_serving_months=frozenset(self._grid_serving_months),
            grid_serving_forecast_threshold_kwh=(
                self._grid_serving_forecast_threshold_kwh
            ),
            price_charge_enabled=self._price_charge_enabled,
            price_charge_strategy=self._price_charge_strategy,
            price_charge_max_price=self._price_charge_max_price,
            price_charge_neutral_price=self._price_charge_neutral_price,
            price_charge_hours=self._price_charge_hours,
            unresolved_fields=frozenset(self._control_unresolved_fields),
        )

    async def async_load_control_state(self) -> None:
        """Load the stored charge configuration and open the bootstrap gate.

        Muss vor async_config_entry_first_refresh() laufen (siehe
        __init__.async_setup_entry): Ab hier bis async_finish_bootstrap()
        sind Register-Reads weiter erlaubt, jede steuernde Entscheidung ist
        dagegen gesperrt.

        Unterscheidet drei Fälle (ControlConfigLoadStatus): Ein lesbarer
        Store ist die alleinige Quelle. Fehlt er, migrieren die Plattformen
        ihre RestoreEntity-Zustände einmalig. Ist er vorhanden, aber nicht
        verwertbar, bleiben die Automatiken auf ihren sicheren Defaults
        stehen (aus, Max-SOC 100 %) - weder eine halb geratene Konfiguration
        noch ein veralteter Entity-Zustand darf dann einspringen, und der
        vorhandene Store wird nicht automatisch überschrieben.
        """
        self._control_bootstrap_pending = True
        result = await self._control_store.async_load()
        self._control_config_status = result.status
        self._control_store_write_blocked = (
            result.status is ControlConfigLoadStatus.FAILED
        )
        self._async_sync_unreadable_store_issue()
        if result.config is not None:
            self._apply_control_config(result.config.sanitized())

    def _async_sync_unreadable_store_issue(self) -> None:
        """Meldet einen unlesbaren Store dem Anwender, statt es nur zu
        loggen: Ohne diesen Hinweis würde er nicht bemerken, dass eigene
        Änderungen für die Dauer dieser Instanz nicht dauerhaft gespeichert
        werden (siehe _async_schedule_control_save)."""
        issue_id = f"{ISSUE_CONTROL_CONFIG_UNREADABLE}_{self.entry_id}"
        if self._control_store_write_blocked:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_CONTROL_CONFIG_UNREADABLE,
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, issue_id)

    def _apply_control_config(self, config: ControlConfig) -> None:
        """Übernimmt einen geladenen Snapshot, ohne etwas zu schreiben.

        Bewusst an den Settern vorbei: die lösen jeweils sofort eine eigene
        Ladeentscheidung aus, genau das soll der Bootstrap ja verhindern.
        Sowohl die Wertebereiche der Einzelfelder als auch die fachlichen
        Invarianten der Gesamtkonfiguration (sich ausschließende
        Automatiken, nicht überlappende Zeitfenster) sind zu diesem
        Zeitpunkt bereits geprüft - siehe ControlConfig.sanitized() in
        infrastructure/control_store.py, das dafür ausdrücklich NICHT
        voraussetzt, dass nur von Settern erzeugte Kombinationen im Store
        stehen.
        """
        self._max_soc = config.max_soc
        self._timed_charge_enabled = bool(config.timed_charge_enabled)
        self._timed_charge_start = config.timed_charge_start
        self._timed_charge_end = config.timed_charge_end
        self._timed_charge_months = set(config.timed_charge_months or ())
        self._timed_charge_min_soc = config.timed_charge_min_soc
        self._grid_serving_enabled = bool(config.grid_serving_enabled)
        self._grid_serving_start = config.grid_serving_start
        self._grid_serving_end = config.grid_serving_end
        self._grid_serving_months = set(config.grid_serving_months or ())
        self._grid_serving_forecast_threshold_kwh = (
            config.grid_serving_forecast_threshold_kwh
        )
        self._price_charge_enabled = bool(config.price_charge_enabled)
        if config.price_charge_strategy is not None:
            self._price_charge_strategy = config.price_charge_strategy
        self._price_charge_max_price = config.price_charge_max_price
        self._price_charge_neutral_price = config.price_charge_neutral_price
        self._price_charge_hours = config.price_charge_hours
        self._control_unresolved_fields = set(config.unresolved_fields or ())

    async def async_finish_bootstrap(self) -> None:
        """Close the bootstrap gate and apply exactly one charge decision.

        Wird nach dem Plattform-Setup aufgerufen, also erst wenn entweder der
        Store (Regelfall) oder der einmalige RestoreEntity-Migrationspfad die
        vollständige Konfiguration bereitgestellt hat. Die eine Auswertung
        läuft über denselben Pfad wie jede spätere Änderung und damit unter
        dem vorhandenen Control-Lock (_async_enforce_grid_charge) - aber mit
        persist=False, weil der Bootstrap seine Persistenz je nach Herkunft
        der Konfiguration selbst entscheidet."""
        if not self._control_bootstrap_pending:
            return
        self._control_bootstrap_pending = False
        self._async_sync_unresolved_fields_issue()
        await self._async_persist_bootstrap_result()
        await self._async_apply_grid_charge_change(persist=False)

    async def _async_persist_bootstrap_result(self) -> None:
        """Schreibt das Bootstrap-Ergebnis - außer der Store ist defekt.

        Ein nicht verwertbarer Store (FAILED) wird NICHT automatisch
        überschrieben: Sein Inhalt kann die einzig verbliebene Kopie einer
        korrekten Konfiguration sein (vorübergehender Lesefehler) oder von
        einer neueren Version stammen, die diese hier nicht kennt. Die
        Sperre gilt dabei für die gesamte Lebensdauer dieser
        Coordinator-Instanz (siehe _async_schedule_control_save) - auch eine
        danach bewusst geänderte Einstellung schreibt ihn nicht wieder, weil
        der dabei geschriebene Snapshot sonst alle anderen, tatsächlich noch
        im Store stehenden Einstellungen mit überschreiben würde. Erst ein
        Neuladen des Config Entry (frische Instanz, neuer Ladeversuch) kann
        wieder schreiben.
        """
        if self._control_store_write_blocked:
            _LOGGER.warning(
                "Ladeeinstellungen werden nicht automatisch gespeichert, weil "
                "der vorhandene Store nicht gelesen werden konnte; er bleibt "
                "unverändert, bis diese Config-Entry-Instanz neu geladen wird "
                "und der Store dann wieder lesbar ist"
            )
            return
        if self._control_config_status is ControlConfigLoadStatus.LOADED:
            # Unverändert übernommen - nur schreiben, falls sanitized()
            # etwas korrigiert hat (der Store verwirft gleiche Snapshots).
            self._async_schedule_control_save()
            return
        # Migration ohne Store: nicht verzögert, damit der Snapshot auch
        # einen unmittelbar folgenden Neustart überlebt.
        try:
            await self._control_store.async_save(self.control_config())
        except (HomeAssistantError, OSError, ValueError) as err:
            _LOGGER.warning(
                "Ladeeinstellungen konnten nicht gespeichert werden: %s", err
            )

    def _async_schedule_control_save(self) -> None:
        """Merkt den aktuellen Snapshot für einen gesammelten Store-Write vor.

        Der Store verwirft einen unveränderten Snapshot selbst, deshalb darf
        das aus jeder Ladeentscheidung heraus aufgerufen werden.

        Bewusst KEIN automatisches Aufheben der Schreibsperre eines defekten
        Stores mehr: Diese Instanz kennt den vorher gespeicherten Stand nicht
        (der Ladeversuch ist gescheitert) und würde mit dem aktuellen, aus
        lauter Initialwerten bestehenden Snapshot alle anderen, tatsächlich
        weiter im Store stehenden Einstellungen überschreiben, sobald auch
        nur eine einzelne Einstellung geändert wird - siehe
        anforderung.yaml, REQ-CONTROL-CONFIG-BOOTSTRAP. Die Sperre gilt
        deshalb für die gesamte Lebensdauer dieser Coordinator-Instanz; erst
        ein Neuladen des Config Entry (frische Instanz, neuer Ladeversuch)
        kann sie aufheben."""
        if self._control_store_write_blocked:
            _LOGGER.warning(
                "Einstellungsänderung wird nicht gespeichert, weil der "
                "vorhandene Store beim Start nicht gelesen werden konnte; "
                "sie bleibt bis zu einem Neuladen des Config Entry nur im "
                "Arbeitsspeicher wirksam"
            )
            return
        try:
            self._control_store.async_delay_save(self.control_config())
        except (HomeAssistantError, OSError, ValueError) as err:
            _LOGGER.warning(
                "Ladeeinstellungen konnten nicht gespeichert werden: %s", err
            )

    async def _async_flush_control_state(self) -> None:
        """Schreibt den Snapshot beim Entladen sofort, statt auf den
        Sammel-Timer zu warten.

        Übersprungen, solange der Bootstrap läuft (die Konfiguration ist
        dann noch unvollständig) sowie bei gesperrtem Store - siehe
        _async_schedule_control_save."""
        if self._control_bootstrap_pending or self._control_store_write_blocked:
            return
        try:
            await self._control_store.async_save(self.control_config())
        except (HomeAssistantError, OSError, ValueError) as err:
            _LOGGER.warning(
                "Ladeeinstellungen konnten beim Entladen nicht gespeichert "
                "werden: %s",
                err,
            )

    async def async_set_max_soc(self, max_soc: int | None) -> None:
        """Set (or clear with None) the software-side max charge SOC.

        Klemmt auf [MIN_SOC, MAX_SOC] statt den Wert ungeprüft zu
        übernehmen - number.SaxPowerMaxSocNumber ruft dies auch beim
        Restaurieren eines gespeicherten Zustands auf (async_added_to_hass),
        ohne die sonst greifende NumberEntity-Min/Max-Validierung des
        regulären Service-Call-Pfads."""
        self._max_soc = _clamp_int(max_soc, MIN_SOC, MAX_SOC)
        self.clear_control_field_unresolved("max_soc")
        if self.data is not None and (current_soc := self.data.get("soc")) is not None:
            await self._async_update_cell_calibration(current_soc)
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()

    # -- Manueller Netzladeauftrag (kompatible Service-API) -------------------
    # start_grid_charge/stop_grid_charge bleiben als Automation-API erhalten,
    # besitzen aber keinen eigenen Register-Writer. Der Auftrag wird unter
    # demselben Control-Lock wie Max-SOC und alle Automatiken ausgewertet und
    # über den gemeinsamen SunSpec-Task ausgeführt (REQ-MANUAL-GRID-CHARGE).

    @property
    def grid_charge_active(self) -> bool:
        return self._grid_charge_power is not None

    async def async_start_grid_charge(self, power: int) -> None:
        """Starte oder aktualisiere einen zentral arbitrierten Ladeauftrag."""
        if (
            isinstance(power, bool)
            or not isinstance(power, int)
            or not MIN_SETPOINT_POWER <= power <= MAX_MANUAL_CHARGE_POWER
        ):
            raise ServiceValidationError(
                f"power muss eine ganze Zahl zwischen {MIN_SETPOINT_POWER} "
                f"und {MAX_MANUAL_CHARGE_POWER} sein",
                translation_domain=DOMAIN,
                translation_key="invalid_grid_charge_power",
                translation_placeholders={
                    "min_power": str(MIN_SETPOINT_POWER),
                    "max_power": str(MAX_MANUAL_CHARGE_POWER),
                    "power": repr(power),
                },
            )
        if self.data is None:
            raise HomeAssistantError(
                "Netzladung kann erst nach dem ersten erfolgreichen "
                "Coordinator-Update gestartet werden"
            )
        async with self._charge_control_lock:
            previous_power = self._grid_charge_power
            self._grid_charge_power = power
            try:
                # Der Aufruf kehrt erst zurück, wenn die wirksame zentrale
                # Entscheidung (manueller Sollwert oder höherrangige Max-SOC-
                # Sperre) vom Gerät quittiert wurde.
                await self._async_enforce_grid_charge_locked(self.data)
            except HomeAssistantError:
                self._grid_charge_power = previous_power
                raise

    async def async_stop_grid_charge(self) -> None:
        """Beende den Auftrag erst nach Task-Ende und sicherem Resetversuch."""
        async with self._charge_control_lock:
            manual_charge_requested = self._grid_charge_power is not None
            sun_charge_writer_running = (
                self._sun_charge_task is not None and not self._sun_charge_task.done()
            )
            orphaned_reset_required = (
                self._sun_charge_reset_required and not sun_charge_writer_running
            )
            if not manual_charge_requested and not orphaned_reset_required:
                return
            self._grid_charge_power = None
            # Ein unvollständiger Start kann den Auftrag bereits verworfen
            # haben, obwohl Modus 1 quittiert und sein Rollback fehlgeschlagen
            # ist. Dieser verwaiste Besitznachweis muss auch ohne sichtbaren
            # manuellen Auftrag zurückgesetzt werden (REQ-MANUAL-GRID-CHARGE).
            await self.async_stop_sun_charge()
            if manual_charge_requested and self.data is not None:
                # Nur ein tatsächlich beendeter manueller Auftrag gibt die
                # zentrale Entscheidung neu frei. Ein reiner Fehler-Reset darf
                # keine laufende Automatik unterbrechen oder neu anstoßen.
                await self._async_enforce_grid_charge_locked(self.data)

    # -- Netzladung (SunSpec-Modus, Immediate Controls) ----------------------
    # Schreibpfad für zeitgesteuertes Laden (siehe Abschnitt weiter unten):
    # SunSpec-Modus (Slave-ID self.slave_id_extended), Modell 123
    # "Immediate Controls".
    #
    # Ablauf laut modbus.pdf/modbus_llm.yaml: Erst Register 40051
    # (Steuermodus) auf 1 (Sollwertvorgabe) setzen, danach kann Register
    # 40049 (Leistungsvorgabe, Prozent der Referenz-Maximalleistung Register
    # 40053) gesetzt werden. Beide Register unterliegen demselben Timeout
    # (Register 40050, siehe REG_SUN_IC_TIMEOUT, max. 300s) und werden vom
    # Gerät verworfen, wenn sie nicht rechtzeitig erneut geschrieben werden -
    # deshalb schreibt die Schleife pro Zyklus beide Register neu (nicht nur
    # den Sollwert), mit einem Intervall, das sicher unterhalb des vom Gerät
    # gemeldeten Timeouts liegt (siehe _sun_ic_write_interval). Beim Stoppen
    # wird Register 40051 aktiv zurück auf 0 (SmartMeter-Nullregelung)
    # gesetzt, statt nur passiv auf den Timeout zu warten.
    #
    # Vorzeichenkonvention für Register 40049 laut modbus.pdf nicht
    # dokumentiert. Hier analog zum Basic-Mode-P-Sollwert (Register 41) und
    # zur gemessenen Wirkleistung (Register 40029, "positiv = Entladung")
    # angenommen: negativ = Laden. Die Integration schreibt hier bewusst nur
    # nicht positive Werte: negative Ladesollwerte oder 0 für Sperren/Pausen -
    # siehe REG_SUN_IC_POWER_SETPOINT_PCT in const.py für den Hintergrund
    # (frühere, vom Hersteller als nicht vorgesehen bestätigte "manuelle
    # Entladung" mit positiven Sollwerten).

    @property
    def sun_charge_active(self) -> bool:
        return self._sun_charge_task is not None and not self._sun_charge_task.done()

    def _record_ic_control_mode(self, mode: int) -> None:
        """Übernehme einen quittierten Schreibwert sofort in den HA-Zustand."""
        self._sun_charge_commanded_mode = mode
        self._sun_charge_command_revision += 1
        self._last_observed_ic_control_mode = mode
        label = CONTROL_MODE_LABELS.get(mode, UNKNOWN_LABEL)
        for cached_data in (self._high_data, self.data):
            if cached_data is not None:
                cached_data["ic_control_mode"] = mode
                cached_data["ic_control_mode_text"] = label

    def _watts_to_ic_setpoint_raw(self, power_watts: int, data: dict[str, Any]) -> int:
        max_power_reference = data.get("ic_max_power_reference")
        if (
            isinstance(max_power_reference, bool)
            or not isinstance(max_power_reference, int | float)
            or not math.isfinite(max_power_reference)
            or max_power_reference <= 0
        ):
            raise HomeAssistantError(
                "Referenzwert Maximalleistung (Register 40053) ist nicht "
                f"gültig: {max_power_reference!r}. Der SunSpec-Modus-Block "
                "muss zuerst erfolgreich gelesen worden sein."
            )
        scale_factor_raw = self._ic_power_setpoint_sf_raw
        if (
            isinstance(scale_factor_raw, bool)
            or not isinstance(scale_factor_raw, int)
            or not 0 <= scale_factor_raw <= 0xFFFF
        ):
            raise HomeAssistantError(
                "Skalierungsfaktor für Register 40049 ist nicht gültig: "
                f"{scale_factor_raw!r}."
            )
        scale_factor = to_signed16(scale_factor_raw)
        # SunSpec erlaubt für sunssf nur -10 bis +10; -32768 kennzeichnet
        # einen nicht implementierten Wert. Die frühe Begrenzung verhindert
        # zugleich unkontrolliert große Zehnerpotenzen im Schreibpfad.
        if not -10 <= scale_factor <= 10:
            raise HomeAssistantError(
                "Skalierungsfaktor für Register 40049 liegt außerhalb des "
                f"SunSpec-Bereichs -10..10: {scale_factor}."
            )
        percent = (power_watts / max_power_reference) * 100
        percent = max(
            MIN_IC_POWER_SETPOINT_PCT, min(MAX_IC_POWER_SETPOINT_PCT, percent)
        )
        raw_value = round(percent / (10**scale_factor))
        if not -0x8000 <= raw_value <= 0x7FFF:
            raise HomeAssistantError(
                "Berechneter Rohwert für Register 40049 liegt außerhalb des "
                f"int16-Bereichs: {raw_value}."
            )
        return to_unsigned16(raw_value)

    def _sun_ic_write_interval(self) -> int:
        """Wiederholungsintervall für die Schleife: die Hälfte des vom Gerät
        gemeldeten Timeouts (Register 40050), gedeckelt auf
        GRID_CHARGE_WRITE_INTERVAL und SUN_IC_MIN_WRITE_INTERVAL, solange
        kein aktueller Timeout-Wert bekannt ist."""
        timeout = self.data.get("ic_timeout") if self.data is not None else None
        if not timeout:
            return GRID_CHARGE_WRITE_INTERVAL
        return max(
            SUN_IC_MIN_WRITE_INTERVAL, min(timeout // 2, GRID_CHARGE_WRITE_INTERVAL)
        )

    async def _async_write_sun_charge_setpoint(self, power: int | None = None) -> None:
        """Write mode and setpoint as one best-effort atomic sequence."""
        async with self._sun_charge_write_lock:
            await self._async_write_sun_charge_setpoint_unlocked(power)

    async def _async_write_sun_charge_setpoint_unlocked(
        self, power: int | None = None
    ) -> None:
        """Execute one sequence while the Immediate Controls lock is held."""
        requested_power = self._sun_charge_power if power is None else power
        # REQ-TIMED-SOC-CHARGE: Jede Voraussetzung und der endgültige
        # int16-Rohwert müssen feststehen, bevor Modus 1 das Gerät aus seiner
        # sicheren SmartMeter-Nullregelung nimmt.
        setpoint_raw = self._watts_to_ic_setpoint_raw(requested_power, self.data or {})
        try:
            await self.async_write_extended_register(
                REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SETPOINT
            )
        except HomeAssistantError as err:
            message = (
                "SunSpec-Sollwertsequenz beim Schreiben von Steuermodus "
                f"Register 40051 abgebrochen: {err}"
            )
            _LOGGER.error(message)
            raise HomeAssistantError(message) from err

        # Ab der quittierten Modusumschaltung bleibt der Rücksetzauftrag für
        # die spätere Freigabe bestehen; bei einer unvollständigen Sequenz
        # löscht ihn ausschließlich ein quittierter Modus-0-Rollback.
        self._sun_charge_reset_required = True
        self._record_ic_control_mode(SUN_IC_CONTROL_MODE_SETPOINT)
        try:
            await self.async_write_extended_register(
                REG_SUN_IC_POWER_SETPOINT_PCT, setpoint_raw
            )
        except HomeAssistantError as setpoint_error:
            try:
                await self.async_write_extended_register(
                    REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER
                )
            except HomeAssistantError as rollback_error:
                message = (
                    "SunSpec-Sollwertsequenz nach quittiertem Moduswechsel: "
                    f"Schreiben von Register 40049 fehlgeschlagen: "
                    f"{setpoint_error}; Rollback über Register 40051 auf "
                    "SmartMeter-Nullregelung ebenfalls fehlgeschlagen: "
                    f"{rollback_error}. Rücksetzauftrag bleibt aktiv."
                )
            else:
                self._sun_charge_reset_required = False
                self._record_ic_control_mode(SUN_IC_CONTROL_MODE_SMARTMETER)
                message = (
                    "SunSpec-Sollwertsequenz nach quittiertem Moduswechsel: "
                    f"Schreiben von Register 40049 fehlgeschlagen: "
                    f"{setpoint_error}; Rollback über Register 40051 auf "
                    "SmartMeter-Nullregelung erfolgreich."
                )
            _LOGGER.error(message)
            raise HomeAssistantError(message) from setpoint_error

    async def async_start_sun_charge(self, power: int) -> None:
        """Start (or update the setpoint of) periodic SunSpec-Modus grid-charge
        writes (Register 40049/40051).

        Ändert sich der Sollwert, während bereits eine Schleife für einen
        ANDEREN Sollwert läuft (z. B. springt die Max-SOC-Sperre an und
        setzt die laufende Netzladung auf 0 % - siehe
        SaxPowerCoordinator._async_enforce_grid_charge), wird sofort
        einmalig geschrieben, statt bis zur nächsten planmäßigen
        Wiederholung der Schleife zu warten (bis zu
        GRID_CHARGE_WRITE_INTERVAL Sekunden später) - eine Einstellungs-
        änderung soll unmittelbar wirken.
        """
        if (
            isinstance(power, bool)
            or not isinstance(power, int)
            or not MIN_SETPOINT_POWER <= power <= 0
        ):
            raise HomeAssistantError(
                f"power muss zwischen {MIN_SETPOINT_POWER} und 0 liegen"
            )
        power_changed = power != self._sun_charge_power
        device_left_setpoint_mode = (
            self._last_observed_ic_control_mode == SUN_IC_CONTROL_MODE_SMARTMETER
        )
        if self._sun_charge_task is None or self._sun_charge_task.done():
            self._sun_charge_task = None
            # Der aufrufende Zustandswechsel darf erst als angewendet gelten,
            # nachdem beide Register vom Gerät quittiert wurden. Die frühere
            # reine Task-Erzeugung ließ Status und tatsächlichen Steuermodus
            # kurzzeitig auseinanderlaufen (REQ-GRID-SERVING-CHARGE).
            try:
                await self._async_write_sun_charge_setpoint(power)
            except HomeAssistantError:
                self._clear_sun_charge_active_flags()
                raise
            self._sun_charge_power = power
            self._sun_charge_task = self.hass.async_create_background_task(
                self._async_sun_charge_loop(), name="sax_power_sun_charge"
            )
        elif (
            power_changed
            or device_left_setpoint_mode
            or self._sun_charge_commanded_mode != SUN_IC_CONTROL_MODE_SETPOINT
        ):
            # Ein gelesener Modus 0 trotz laufendem Task beweist, dass Gerät
            # oder ein externer Schreiber 40051 zwischenzeitlich verändert
            # hat. Nicht bis zum nächsten periodischen Refresh warten.
            try:
                await self._async_write_sun_charge_setpoint(power)
            except HomeAssistantError:
                # Nach einer unvollständigen Sofortänderung darf der
                # schlafende Task den alten Sollwert nicht später erneut
                # aktivieren. Der nächste Coordinator-Takt entscheidet neu.
                await self._async_cancel_sun_charge_task()
                self._clear_sun_charge_active_flags()
                raise
            self._sun_charge_power = power

    def _clear_sun_charge_active_flags(self) -> None:
        """Avoid publishing activity after an incomplete device sequence."""
        self._timed_charge_active = False
        self._grid_serving_active = False
        self._grid_serving_setpoint_active = False
        self._price_charge_active = False
        self._max_soc_clamped = False

    async def _async_cancel_sun_charge_task(self) -> None:
        """Cancel and forget the periodic writer without another mode write."""
        if self._sun_charge_task is None:
            return
        self._sun_charge_task.cancel()
        try:
            await self._sun_charge_task
        except asyncio.CancelledError, HomeAssistantError:
            pass
        self._sun_charge_task = None

    async def async_stop_sun_charge(self) -> None:
        """Gleiche Register 40051 mit dem Sollzustand Nullregelung ab.

        Die erste inaktive Entscheidung jeder Coordinator-Instanz schreibt
        immer. Danach ist die Methode ein No-Op, solange weder Task/
        Rücksetzauftrag noch eine abweichende Geräte-Rückmeldung vorliegen.
        Fehlgeschlagene Rücksetzungen werden beim nächsten Takt wiederholt.
        """
        needs_reset = (
            self._sun_charge_task is not None
            or self._sun_charge_reset_required
            or self._sun_charge_commanded_mode == SUN_IC_CONTROL_MODE_SETPOINT
            or (
                self._sun_charge_commanded_mode is None
                and self._last_observed_ic_control_mode is not None
            )
            or self._last_observed_ic_control_mode == SUN_IC_CONTROL_MODE_SETPOINT
        )
        if not needs_reset:
            return
        await self._async_cancel_sun_charge_task()
        try:
            async with self._sun_charge_write_lock:
                await self.async_write_extended_register(
                    REG_SUN_IC_CONTROL_MODE, SUN_IC_CONTROL_MODE_SMARTMETER
                )
        except HomeAssistantError:
            _LOGGER.exception(
                "Netzladung (SunSpec-Modus): Steuermodus konnte nicht auf "
                "SmartMeter-Nullregelung zurückgesetzt werden - Gerät fällt "
                "spätestens nach Ablauf des Timeouts (Register 40050) "
                "automatisch zurück."
            )
        else:
            self._sun_charge_reset_required = False
            self._record_ic_control_mode(SUN_IC_CONTROL_MODE_SMARTMETER)

    async def _async_sun_charge_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._sun_ic_write_interval())
                await self._async_write_sun_charge_setpoint()
        except asyncio.CancelledError:
            raise
        except HomeAssistantError:
            self._clear_sun_charge_active_flags()
            _LOGGER.exception(
                "Netzladung (SunSpec-Modus): periodischer Schreibvorgang fehlgeschlagen"
            )
            raise

    # -- Zeitgesteuertes Laden ------------------------------------------------
    # Lädt den Speicher innerhalb eines konfigurierbaren Zeitfensters aktiv
    # auf einen Ziel-SOC, unabhängig von PV-Überschuss (z. B. für günstige
    # Nachtstromtarife), über den SunSpec-Modus-Pfad oben
    # (_async_sun_charge_loop). Lädt immer mit maximal möglicher Leistung
    # (MIN_SETPOINT_POWER, sättigt in _watts_to_ic_setpoint_raw auf
    # MIN_IC_POWER_SETPOINT_PCT) - eine frühere, konfigurierbare "Max.
    # Netzladeleistung" (SaxPowerChargeLimitNumber) wurde entfernt: der
    # eingestellte Watt-Wert hatte in der Praxis keinen Einfluss auf die
    # tatsächliche Ladeleistung, weil er ohnehin fast immer auf 100 %
    # sättigte. Der Ziel-SOC nutzt denselben Wert wie "Max. SOC"
    # (self._max_soc, siehe Max-SOC-Abschnitt oben) - fehlt dieser (None),
    # wird MAX_SOC (100 %) als Ziel angenommen. Das vermeidet redundante
    # Einstellmöglichkeiten (siehe anforderung.yaml, REQ-TIMED-SOC-CHARGE).

    @property
    def timed_charge_enabled(self) -> bool:
        return self._timed_charge_enabled

    @property
    def timed_charge_start(self) -> dt_time | None:
        return self._timed_charge_start

    @property
    def timed_charge_end(self) -> dt_time | None:
        return self._timed_charge_end

    @property
    def timed_charge_months(self) -> frozenset[int]:
        return frozenset(self._timed_charge_months)

    @property
    def timed_charge_min_soc(self) -> int | None:
        return self._timed_charge_min_soc

    async def async_set_timed_charge_enabled(
        self, enabled: bool, *, force: bool = False
    ) -> bool:
        """Netzladung ein-/ausschalten. Gibt zurück, ob die Änderung
        übernommen wurde.

        Netzladung und preisoptimiertes Laden (siehe Abschnitt weiter unten)
        laden beide aktiv über denselben SunSpec-Schreibpfad aus dem Netz
        und dürfen deshalb nicht gleichzeitig aktiv sein. Wird die
        Netzladung eingeschaltet, während preisoptimiertes Laden läuft, wird
        die Änderung NICHT stillschweigend ausgeführt, sondern als
        reparierbares Issue zur Bestätigung vorgelegt (siehe
        _async_create_charge_conflict_issue/repairs.py) und hier mit False
        abgelehnt - der Anwender kann dort bestätigen (dann wird
        preisoptimiertes Laden abgeschaltet) oder abbrechen.

        `force=True` überspringt diese Rückfrage und schaltet das jeweils
        andere Feature direkt ab - genutzt vom Bestätigungsdialog selbst,
        vom Service set_price_charge_enabled (nicht-interaktiver
        Automationspfad) sowie beim Restaurieren des gespeicherten Zustands
        beim Start (switch.py), wo per Definition nie beide Features
        gleichzeitig aktiv gespeichert sein können.
        """
        if enabled and self._price_charge_enabled:
            if not force:
                self._async_create_charge_conflict_issue(ISSUE_TIMED_CHARGE_CONFLICT)
                return False
            self._price_charge_enabled = False
        self._timed_charge_enabled = enabled
        self.clear_control_field_unresolved("timed_charge_enabled")
        self.async_dismiss_charge_conflict()
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()
        return True

    async def async_set_timed_charge_min_soc(self, value: int | None) -> None:
        """Set (or clear with None) den unteren SOC-Schwellwert ("Min. SOC"),
        unterhalb dessen die Netzladung starten darf - siehe
        _async_enforce_grid_charge/_timed_charge_armed für die
        Hysterese-Logik (einmal unterschritten, wird bis zum "Max. SOC"
        durchgeladen, statt bei jedem Überschreiten von Min. SOC sofort
        wieder abzubrechen). Klemmt auf [MIN_SOC, MAX_SOC], siehe
        async_set_max_soc für die Begründung (RestoreEntity-Pfad ohne
        NumberEntity-Validierung)."""
        self._timed_charge_min_soc = _clamp_int(value, MIN_SOC, MAX_SOC)
        self.clear_control_field_unresolved("timed_charge_min_soc")
        await self._async_apply_grid_charge_change()

    async def async_set_timed_charge_start(self, value: dt_time) -> None:
        if self._windows_overlap_with_months(
            value,
            self._timed_charge_end,
            self._timed_charge_months,
            self._grid_serving_start,
            self._grid_serving_end,
            self._grid_serving_months,
        ):
            self._notify_time_window_overlap(
                "Netzladung",
                value,
                self._timed_charge_end,
                self._timed_charge_months,
                "netzdienliches Laden",
                self._grid_serving_start,
                self._grid_serving_end,
                self._grid_serving_months,
            )
            self._timed_charge_start = None
        else:
            self._timed_charge_start = value
        self.clear_control_field_unresolved("timed_charge_start")
        await self._async_apply_grid_charge_change()

    async def async_set_timed_charge_end(self, value: dt_time) -> None:
        if self._windows_overlap_with_months(
            self._timed_charge_start,
            value,
            self._timed_charge_months,
            self._grid_serving_start,
            self._grid_serving_end,
            self._grid_serving_months,
        ):
            self._notify_time_window_overlap(
                "Netzladung",
                self._timed_charge_start,
                value,
                self._timed_charge_months,
                "netzdienliches Laden",
                self._grid_serving_start,
                self._grid_serving_end,
                self._grid_serving_months,
            )
            self._timed_charge_end = None
        else:
            self._timed_charge_end = value
        self.clear_control_field_unresolved("timed_charge_end")
        await self._async_apply_grid_charge_change()

    async def async_set_timed_charge_window(self, start: dt_time, end: dt_time) -> None:
        """Setzt Start und Ende der Netzladung atomar in einem Aufruf.

        Anders als async_set_timed_charge_start/-end (die je nur eine der
        beiden Zeit-Entities bedienen und dabei zwangsläufig gegen den noch
        alten Wert der jeweils anderen Grenze validieren) prüft dies direkt
        das tatsächliche Ziel-Fenster (start, end) - ein durch die
        Zwei-Schritt-Bearbeitung nur kurzzeitig entstehendes, in Wahrheit gar
        nicht beabsichtigtes Zwischenfenster kann die Prüfung dadurch nicht
        mehr fälschlich als Überschneidung erkennen (siehe anforderung.yaml,
        REQ-GRID-SERVING-CHARGE)."""
        if self._windows_overlap_with_months(
            start,
            end,
            self._timed_charge_months,
            self._grid_serving_start,
            self._grid_serving_end,
            self._grid_serving_months,
        ):
            self._notify_time_window_overlap(
                "Netzladung",
                start,
                end,
                self._timed_charge_months,
                "netzdienliches Laden",
                self._grid_serving_start,
                self._grid_serving_end,
                self._grid_serving_months,
            )
            self._timed_charge_start = None
            self._timed_charge_end = None
        else:
            self._timed_charge_start = start
            self._timed_charge_end = end
        self.clear_control_field_unresolved("timed_charge_start")
        self.clear_control_field_unresolved("timed_charge_end")
        await self._async_apply_grid_charge_change()

    async def async_set_timed_charge_month(
        self, month: int, enabled: bool, validate: bool = True
    ) -> None:
        """Nimmt `month` (1-12) in die aktiven Monate der Netzladung auf bzw.
        entfernt ihn daraus. `validate=False` überspringt die
        Überlappungsprüfung - ausschließlich für das Restaurieren des
        gespeicherten Zustands beim Start gedacht (siehe
        SaxPowerMonthSwitch.async_added_to_hass): Da beide Feature-Fenster
        initial auf "alle Monate" stehen und Monate einzeln, nacheinander
        restauriert werden, könnte eine Validierung während dieser
        Zwischenzustände fälschlich fehlschlagen, obwohl der jeweils
        gespeicherte Endzustand gar nicht überlappt."""
        new_months = set(self._timed_charge_months)
        if enabled:
            new_months.add(month)
        else:
            new_months.discard(month)
        if validate:
            self._assert_windows_dont_overlap(
                self._timed_charge_start,
                self._timed_charge_end,
                new_months,
                self._grid_serving_start,
                self._grid_serving_end,
                self._grid_serving_months,
            )
        self._timed_charge_months = new_months
        if validate:
            # Nur eine echte, vom Anwender ausgelöste Änderung (siehe
            # Docstring oben) gilt als Bestätigung des gesamten Monats-Sets -
            # der Migrationspfad (validate=False) ruft dies für jeden der 12
            # Schalter einzeln auf und darf eine für ein ANDERES Monat
            # gesetzte Markierung nicht versehentlich mit löschen.
            self.clear_control_field_unresolved("timed_charge_months")
        await self._async_apply_grid_charge_change()

    async def _async_apply_grid_charge_change(self, *, persist: bool = True) -> None:
        """Re-evaluate Zeitfenster/Max-SOC/Netzladeleistung sofort nach einer
        Einstellungsänderung, statt bis zum nächsten Poll-Intervall zu
        warten.

        Gemeinsamer Endpunkt aller async_set_*-Setter: hier - und nur hier -
        wird der Konfigurations-Snapshot zum Speichern vorgemerkt
        (REQ-CONTROL-CONFIG-BOOTSTRAP). Während des Bootstraps passiert
        beides nicht: die Setter restaurieren dann nur noch Altzustände, und
        eine Teilkonfiguration darf weder das Gerät steuern noch den
        vollständigen gespeicherten Stand überschreiben.

        `persist=False` nutzt ausschließlich async_finish_bootstrap für
        seine eine Auswertung: Die dortige Konfiguration stammt nicht aus
        einer Anwenderänderung, deshalb entscheidet der Bootstrap selbst, ob
        und wie sie geschrieben wird (siehe _async_persist_bootstrap_result).
        """
        if self._control_bootstrap_pending:
            return
        if persist:
            self._async_schedule_control_save()
        if self.data is not None:
            await self._async_enforce_grid_charge(self.data)
            self._publish_charge_state(self.data)
            self.async_set_updated_data(self.data)

    def _cycles_confirmed(self, counter_attr: str, condition: bool) -> bool:
        """Zyklen-Hysterese für Vergleiche gegen
        SMARTMETER_PV_SURPLUS_THRESHOLD_WATT: `condition` gilt erst als
        bestätigt (True), nachdem sie in PV_SURPLUS_HYSTERESIS_CYCLES
        aufeinanderfolgenden Aufrufen True war. Ein einzelner False-Wert
        setzt den in `counter_attr` (self-Attribut) gehaltenen Zähler sofort
        zurück, damit kurze Lastspitzen/Messausreißer am Smart Meter keinen
        Zustandswechsel auslösen - siehe const.PV_SURPLUS_HYSTERESIS_CYCLES
        sowie anforderung.yaml, REQ-TIMED-SOC-CHARGE/REQ-GRID-SERVING-CHARGE.
        Von allen vier Stellen genutzt, die SMARTMETER_PV_SURPLUS_THRESHOLD_
        WATT auswerten, damit sie sich einheitlich verhalten.
        """
        count = getattr(self, counter_attr) + 1 if condition else 0
        setattr(self, counter_attr, count)
        return count >= PV_SURPLUS_HYSTERESIS_CYCLES

    @staticmethod
    def _is_time_in_window(
        now: dt_time, start: dt_time | None, end: dt_time | None
    ) -> bool:
        """True, wenn `now` im Zeitfenster [start, end) liegt.

        Unterstützt über Mitternacht laufende Fenster (z. B. 23:00-05:00).
        Ist start == end (oder eines der beiden nicht gesetzt), gilt das
        Fenster als leer (nie aktiv) statt als "ganztägig".
        """
        return is_time_in_window(now, start, end)

    @staticmethod
    def _windows_overlap_with_months(
        start_a: dt_time | None,
        end_a: dt_time | None,
        months_a: set[int],
        start_b: dt_time | None,
        end_b: dt_time | None,
        months_b: set[int],
    ) -> bool:
        """True, wenn sich zwei Zeitfenster (Netzladung/netzdienliches Laden)
        sowohl in ihrer Tageszeit (windows_overlap) ALS AUCH in ihren aktiven
        Monaten (months_a/months_b, je ein Set aus 1-12, siehe
        switch.SaxPowerMonthSwitch) überschneiden - siehe anforderung.yaml,
        REQ-GRID-SERVING-CHARGE. Laufen beide Fenster nur in disjunkten
        Monaten (z. B. Netzladung nur November-Januar, netzdienliches Laden
        nur Mai-August), gelten sie NICHT als überlappend, egal wie sehr
        sich die Tageszeiten überschneiden, da die Fenster nie gleichzeitig
        aktiv sein können."""
        return bool(
            windows_overlap(start_a, end_a, start_b, end_b) and (months_a & months_b)
        )

    def _assert_windows_dont_overlap(
        self,
        start_a: dt_time | None,
        end_a: dt_time | None,
        months_a: set[int],
        start_b: dt_time | None,
        end_b: dt_time | None,
        months_b: set[int],
    ) -> None:
        """Bricht mit HomeAssistantError ab, statt eine Monats-Auswahl
        (Netzladung oder netzdienliches Laden) zu übernehmen, die dazu
        führen würde, dass sich ihr Zeitfenster (siehe
        _windows_overlap_with_months) mit dem des jeweils anderen Lademodus
        überschneidet - siehe anforderung.yaml, REQ-GRID-SERVING-CHARGE. Der
        Fehler wird von den Monats-Settern (async_set_timed_charge_month,
        async_set_grid_serving_month) an den aufrufenden Service-Call
        durchgereicht und dadurch dem Anwender im Frontend als Fehler
        angezeigt - unabhängig davon, welche der beiden Monats-Auswahlen
        gerade geändert wird. Die Zeit-Setter (async_set_timed_charge_
        start/-end/-window, async_set_grid_serving_start/-end/-window)
        nutzen _windows_overlap_with_months direkt und lehnen eine
        Überschneidung NICHT mehr mit einem Fehler ab, sondern zeigen eine
        Benachrichtigung und leeren die soeben geänderte Zeit (siehe
        _notify_time_window_overlap) - eine Zeit-Entity lässt sich anders
        als ein Monats-Schalter beim Ablehnen nicht sinnvoll auf einen
        vorherigen Wert zurücksetzen, ohne den Anwender zu verwirren, welcher
        von zwei möglicherweise gerade beide bearbeiteten Werten nun gilt."""
        if self._windows_overlap_with_months(
            start_a, end_a, months_a, start_b, end_b, months_b
        ):
            raise HomeAssistantError(
                "Das Zeitfenster überschneidet sich (Tageszeit UND aktive "
                "Monate) mit dem Zeitfenster des jeweils anderen Lademodus "
                "(Netzladung/netzdienliches Laden). Bitte andere aktive "
                "Monate wählen."
            )

    def _notify_time_window_overlap(
        self,
        feature_label: str,
        start: dt_time | None,
        end: dt_time | None,
        months: set[int],
        other_label: str,
        other_start: dt_time | None,
        other_end: dt_time | None,
        other_months: set[int],
    ) -> None:
        """Zeigt dem Anwender eine Persistent Notification mit beiden
        Zeitfenstern (Tageszeit + aktive Monate) an, statt die Änderung wie
        früher mit HomeAssistantError abzulehnen - siehe anforderung.yaml,
        REQ-GRID-SERVING-CHARGE. Wird ausschließlich von den Zeit-Settern
        (async_set_timed_charge_start/-end/-window,
        async_set_grid_serving_start/-end/-window) aufgerufen, unmittelbar
        bevor diese die soeben geänderte(n) Zeit(en) auf None (leer) setzen
        - eine leere Start- oder Endzeit bewirkt immer, dass das jeweilige
        Feature nicht ausgeführt wird (siehe _is_time_in_window/
        windows_overlap, die ein unvollständiges Fenster als nie aktiv bzw.
        nie überlappend behandeln)."""
        message = (
            f"Das soeben geänderte Zeitfenster für {feature_label} "
            f"({_format_window_for_message(start, end, months)}) überschneidet "
            f"sich mit dem Zeitfenster für {other_label} "
            f"({_format_window_for_message(other_start, other_end, other_months)}). "
            "Die soeben geänderte Zeit wurde geleert, damit das Feature nicht "
            "mit einer widersprüchlichen Konfiguration weiterläuft - bitte "
            "ein nicht überlappendes Zeitfenster oder andere aktive Monate "
            "wählen."
        )
        _LOGGER.warning(message)
        persistent_notification.async_create(
            self.hass,
            message,
            title="SAX Power: Zeitfenster überschneidet sich",
            notification_id=f"{DOMAIN}_{self.entry_id}_window_overlap",
        )

    async def _async_enforce_grid_charge(self, data: dict[str, Any]) -> None:
        """Werte Ladebedingungen aus und wende genau eine Entscheidung an."""
        async with self._charge_control_lock:
            await self._async_enforce_grid_charge_locked(data)

    async def _async_enforce_grid_charge_locked(self, data: dict[str, Any]) -> None:
        """Zentrale Auswertung für Max-SOC-Sperre, zeitgesteuertes Laden,
        manuellen Netzladeauftrag, zeitgesteuertes, netzdienliches und
        preisoptimiertes Laden - alle teilen sich den SunSpec-Modus-
        Schreibpfad (_sun_charge_task). Priorität
        (höchste zuerst):

        1. Ist der Ziel-SOC erreicht/überschritten, hat die Max-SOC-Sperre
           Vorrang: Register 40051 bleibt/wird auf Sollwertvorgabe gesetzt
           und Register 40049 auf 0 % gehalten (siehe Max-SOC-Abschnitt
           oben) - unabhängig davon, ob zeitgesteuertes oder netzdienliches
           Laden aktiviert ist. Wurde die Sperre INNERHALB eines der beiden
           Zeitfenster ausgelöst, gilt sie nur bis zu dessen Ende - danach
           wird Register 40051 aktiv auf 0 (Nullregelung) zurückgesetzt.
           Außerhalb jedes Zeitfensters (z. B. bei einem rein durch
           PV-Überschuss via Nullregelung vollen Speicher) gilt die Sperre
           dagegen unbegrenzt, bis entweder der SOC unter den Zielwert
           fällt ODER am Smart Meter über mehrere Zyklen hinweg Netzbezug
           gemessen wird (siehe _max_soc_hold_is_window_bound sowie den
           Max-SOC-Abschnitt oben zum Netzbezug-Freigabe-Trigger).
        2. Erst wenn die Max-SOC-Sperre nicht greift, übernimmt ein über
           start_grid_charge angeforderter strikt negativer manueller
           Ladesollwert. Er hat Vorrang vor allen Automatiken und bleibt bis
           stop_grid_charge aktiv.
        3. Erst wenn weder Max-SOC-Sperre noch manueller Auftrag greifen,
           kann zeitgesteuertes
           Laden (falls aktiviert, im Zeitfenster, im aktiven Monat - siehe
           "Aktive Monate"-Schalter unten -, mit gesetztem "Min. SOC"
           (siehe unten) UND ohne PV-Überschuss über
           SMARTMETER_PV_SURPLUS_THRESHOLD_WATT) die
           Schleife mit einem echten Ladesollwert übernehmen. Der
           PV-Überschuss-Check läuft dabei über dieselbe Zyklen-Hysterese
           wie die drei anderen Stellen, die diesen Schwellwert auswerten
           (self._cycles_confirmed, self._timed_charge_pv_surplus_cycles,
           PV_SURPLUS_HYSTERESIS_CYCLES): erst wenn der Smart Meter so viele
           Zyklen in Folge PV-Überschuss über dem Schwellwert meldet, beendet
           das die Netzladung - auch mitten im Zeitfenster, nicht erst am
           Fensterende. Ein einzelner Wert unter dem Schwellwert setzt die
           Bestätigung sofort zurück.

           "Min. SOC" (self._timed_charge_min_soc, NumberEntity analog zu
           "Max. SOC"): Netzladung startet nur, wenn der SOC diesen
           Schwellwert unterschritten hat - _timed_charge_armed hält diesen
           "unterschritten"-Zustand als Hysterese fest, damit einmal
           gestartetes Laden bis zum Erreichen von "Max. SOC" durchläuft,
           statt bei jedem erneuten Überschreiten von "Min. SOC" sofort
           wieder abzubrechen (siehe unten, vor der Berechnung von
           timed_should_charge).
        4. Netzdienliches Laden (falls aktiviert, im eigenen Zeitfenster, im
           eigenen aktiven Monat UND nicht bereits durch zeitgesteuertes
           Laden beansprucht - die Zeitfenster von zeitgesteuertem und
           netzdienlichem Laden dürfen sich zusätzlich nicht überschneiden,
           siehe _windows_overlap_with_months/_notify_time_window_overlap)
           hat Vorrang vor preisoptimiertem Laden (grid_serving_window_active
           schließt price_should_charge/price_should_pause aus, NICHT
           umgekehrt - siehe Punkt 4). Grund: netzdienliches Laden ist
           typischerweise nur in den ertragsreichen Sommermonaten aktiv, in
           denen ohnehin kaum oder gar kein Netzbezug nötig ist; ohne diesen
           Vorrang würden sich beide Automatiken - sobald ihre jeweiligen
           Bedingungen gleichzeitig erfüllt sind - gegenseitig ein- und
           ausschalten, weil sie denselben Sollwertvorgabemodus für
           unterschiedliche Zwecke beanspruchen. Netzdienliches Laden läuft
           als eigene Zustandsmaschine über _async_step_grid_serving, NICHT
           über einen aus dem Smart-Meter-Überschuss berechneten
           Ladesollwert - es wird nie ein Sollwert > 0 geschrieben. Das
           Feature lädt bewusst NIE aktiv aus dem Netz, sondern überlässt
           die eigentliche
           Ladung der geräteeigenen SmartMeter-Nullregelung (Register 40051
           = 0), die von sich aus nur mit echtem PV-Überschuss lädt:

           a. Solange KEIN Eingriff läuft (self._grid_serving_setpoint_active
              False, Speicher in SmartMeter-Nullregelung oder gerade erst ins
              Zeitfenster eingetreten): Sobald die tatsächliche Ladeleistung
              des SAX (negativer Anteil von data["storage_power_active"],
              siehe sensor.py _negative_part("storage_power_active"), "SAX
              Ladeleistung") SMARTMETER_PV_SURPLUS_THRESHOLD_WATT so viele
              Zyklen in Folge erreicht oder überschreitet wie
              PV_SURPLUS_HYSTERESIS_CYCLES vorgibt
              (self._grid_serving_charge_confirm_cycles, dieselbe
              Zyklen-Hysterese wie bei den anderen drei Stellen, die diesen
              Schwellwert auswerten), wechselt der Speicher aktiv in den
              Sollwertvorgabemodus (Register 40051 = 1) UND die Ladung wird
              sofort auf 0 % gestoppt (async_start_sun_charge(0) - macht
              beides in einem Aufruf). Danach wird zusätzlich einmalig
              self._grid_serving_wait_cycles = PV_SURPLUS_HYSTERESIS_CYCLES
              gesetzt: die folgenden Aufrufe von _async_enforce_grid_charge
              tun in dieser Anzahl nichts weiter außer den Zähler
              herunterzuzählen, damit der Moduswechsel/Stopp sich setzen
              kann, bevor Schritt b neu bewertet wird.
           b. Erst wenn der Sollwertvorgabemodus aktiv ist (Schritt a
              ausgelöst UND die Wartezyklen abgelaufen sind) wird geprüft, ob
              die am Smart Meter gemessene Netzeinspeisung
              (data["smartmeter_power"]) so viele Zyklen in Folge unter
              SMARTMETER_PV_SURPLUS_THRESHOLD_WATT gefallen ist
              (self._grid_serving_release_confirm_cycles, dieselbe
              Zyklen-Hysterese). Ist das der Fall, wird der Speicher aktiv
              zurück in die SmartMeter-Nullregelung gesetzt
              (async_stop_sun_charge, Register 40051 = 0) - danach kann
              Schritt a beim nächsten Anstieg der SAX-Ladeleistung erneut
              greifen. Bleibt die Einspeisung weiterhin bei mindestens
              SMARTMETER_PV_SURPLUS_THRESHOLD_WATT (oder fehlt der Messwert,
              oder reißt die Unterschreitung zwischendurch wieder ab - ein
              einzelner Wert über dem Schwellwert setzt die Bestätigung
              sofort zurück), bleibt die Ladung bewusst bei 0 % gehalten -
              der Speicher wird an dieser Stelle erst wieder geladen, sobald
              ein Zeitpunkt mit dauerhaft gefallener Einspeisung erreicht
              ist, das ist der eigentliche Zweck der Funktion.

           Beide Prüfungen sind exklusiv (a nur ohne, b nur mit aktivem
           Sollwertvorgabemodus) - siehe _async_step_grid_serving.
        5. Erst wenn weder die Max-SOC-Sperre, manuelle Netzladung,
           zeitgesteuertes noch
           netzdienliches Laden (dessen Zeitfenster gerade aktiv ist -
           grid_serving_window_active) greifen, kann preisoptimiertes Laden
           (siehe eigenen Abschnitt weiter unten sowie anforderung.yaml,
           REQ-DYNAMIC-PRICE-CHARGE) aus dem Netz laden, sobald der vom
           Planner (price_optimizer.py) berechnete Ladeplan für den
           aktuellen Zeitpunkt ein ausgewähltes Preisfenster meldet. Es
           bricht - wie zeitgesteuertes Laden - bei bestätigtem
           PV-Überschuss sofort ab. Ziel-SOC ist derselbe Wert wie "Max.
           SOC" (keine eigene Einstellung) - ist er erreicht, greift
           dieselbe Max-SOC-Sperre wie bei den anderen Lademodi.

           Neutralpreis-Pausezone: lädt preisoptimiertes Laden gerade NICHT
           (price_should_charge False, z. B. weil der aktuelle Preis über
           der Preisgrenze liegt), aber der aktuelle Preis liegt noch
           unterhalb des Neutralpreises (number "Preisoptimiertes Laden
           Neutralpreis"), wird der Speicher statt der normalen
           SmartMeter-Nullregelung aktiv in den manuellen Sollwertmodus mit
           Sollwert 0 geschaltet (price_should_pause,
           async_start_sun_charge(0)) - Laden UND Entladen bleiben
           gestoppt, der komplette Hausverbrauch läuft über das Netz. Erst
           ab dem Neutralpreis lohnt sich die Entladung wieder (die
           Speicherverluste würden sie sonst teurer machen als der direkte
           Netzbezug), der Speicher geht dann zurück in die Nullregelung.
           Dieselben Ausschlussgründe wie bei price_should_charge (Max-SOC-
           Sperre, PV-Überschuss, zeitgesteuertes UND netzdienliches Laden
           haben Vorrang) gelten auch hier. Fehlt eine der beiden
           Preis-Einstellungen, oder liegt der Neutralpreis nicht über der
           Preisgrenze, bleibt price_should_pause False (siehe
           _check_price_neutral_below_limit für den zugehörigen
           Reparaturhinweis) - Verhalten unverändert wie vor Einführung des
           Neutralpreises.
        6. Andernfalls (alle Features deaktiviert, außerhalb Zeitfenster/
           Monat oder SOC erreicht) wird Register 40051 zurück auf 0
           (SmartMeter-Nullregelung) gesetzt und der Zustand der
           netzdienlichen Zustandsmaschine (_grid_serving_setpoint_active/
           _grid_serving_wait_cycles) zurückgesetzt.

        Aktive Monate: Zusätzlich zum Zeitfenster hat jedes Feature 12
        Monats-Schalter (switch.SaxPowerMonthSwitch, "aktiv im Januar" ...
        "aktiv im Dezember"), die festlegen, in welchen Kalendermonaten das
        jeweilige Zeitfenster überhaupt wirksam ist - z. B. Netzladung nur
        November-Januar, netzdienliches Laden nur Mai-August. Default: alle
        Monate aktiv. Ist für ein Feature kein einziger Monat ausgewählt,
        ist es ganzjährig inaktiv (analog zu einem leeren Zeitfenster).
        """
        command_revision_before = self._sun_charge_command_revision

        # Nach Reload/Neuinstallation kann der Speicher noch bis zum Ablauf
        # von Register 40050 im Sollwertmodus der vorherigen Instanz stehen,
        # obwohl deren Task und RAM-Merker nicht mehr existieren. Die echte
        # Register-Rückmeldung übernimmt dann den Rücksetzauftrag; ohne sie
        # blieb der inaktive Pfad bis zu 300 Sekunden wirkungslos.
        observed_control_mode = data.get("ic_control_mode")
        control_mode_changed = (
            observed_control_mode != self._last_observed_ic_control_mode
        )
        self._last_observed_ic_control_mode = observed_control_mode
        if (
            control_mode_changed
            and observed_control_mode == SUN_IC_CONTROL_MODE_SETPOINT
        ):
            self._sun_charge_reset_required = True

        target_soc = self.effective_max_soc
        current_soc = data["soc"]
        if (
            self._last_effective_max_soc is not None
            and target_soc < self._last_effective_max_soc
        ):
            # Eine Zielabsenkung ist eine neue Überschreitung. Eine Erhöhung
            # behält die Freigabe dagegen bei, solange der neue Zielwert noch
            # unter dem aktuellen SOC liegt (REQ-TIMED-SOC-CHARGE).
            self._max_soc_released_for_discharge = False
        self._last_effective_max_soc = target_soc
        if current_soc < target_soc:
            self._max_soc_released_for_discharge = False
        if current_soc >= target_soc:
            self._timed_charge_armed = False
        elif (
            self._timed_charge_min_soc is not None
            and current_soc < self._timed_charge_min_soc
        ):
            self._timed_charge_armed = True
        smartmeter_power = data.get("smartmeter_power")
        # Vorzeichenkonvention (siehe const.py, SMARTMETER_PV_SURPLUS_
        # THRESHOLD_WATT): negativ = Einspeisung/PV-Überschuss.
        pv_surplus_raw = (
            smartmeter_power is not None
            and smartmeter_power < -SMARTMETER_PV_SURPLUS_THRESHOLD_WATT
        )
        pv_surplus_active = self._cycles_confirmed(
            "_timed_charge_pv_surplus_cycles", pv_surplus_raw
        )
        now = dt_util.now()
        price_plan = self.price_planner.plan
        grid_serving_forecast_kwh = self.price_planner.forecast_kwh()
        grid_serving_forecast_threshold = self.grid_serving_forecast_threshold_kwh
        grid_serving_forecast_sensor_configured = (
            self.price_planner.pv_forecast_entity_id is not None
        )
        grid_serving_forecast_allowed = (
            not grid_serving_forecast_sensor_configured
            or grid_serving_forecast_threshold <= 0
            or (
                grid_serving_forecast_kwh is not None
                and grid_serving_forecast_kwh >= grid_serving_forecast_threshold
            )
        )
        policy = evaluate_charge_policy(
            ChargePolicyInput(
                now=now,
                current_soc=current_soc,
                target_soc=target_soc,
                pv_surplus_active=pv_surplus_active,
                timed_enabled=self._timed_charge_enabled,
                timed_start=self._timed_charge_start,
                timed_end=self._timed_charge_end,
                timed_months=self._timed_charge_months,
                timed_min_soc=self._timed_charge_min_soc,
                timed_armed=self._timed_charge_armed,
                grid_serving_enabled=self._grid_serving_enabled,
                grid_serving_start=self._grid_serving_start,
                grid_serving_end=self._grid_serving_end,
                grid_serving_months=self._grid_serving_months,
                grid_serving_forecast_allowed=grid_serving_forecast_allowed,
                price_enabled=self._price_charge_enabled,
                price_strategy_active=(
                    self._price_charge_strategy != PRICE_STRATEGY_OFF
                ),
                price_charge_now=price_plan.charge_now,
                current_price=price_plan.current_price,
                price_limit=self._price_charge_max_price,
                neutral_price=self._price_charge_neutral_price,
            )
        )
        soc_reached = policy.soc_reached
        timed_should_charge = policy.timed_should_charge
        grid_serving_window_active = policy.grid_serving_window_active
        grid_serving_eligible = policy.grid_serving_eligible
        price_should_charge = policy.price_should_charge
        price_should_pause = policy.price_should_pause
        self._grid_serving_forecast_kwh = grid_serving_forecast_kwh
        self._grid_serving_forecast_allowed = grid_serving_forecast_allowed
        self._grid_serving_window_active = grid_serving_window_active
        self._grid_serving_pause_status_text = _grid_serving_pause_status(
            now=now,
            enabled=self._grid_serving_enabled,
            start=self._grid_serving_start,
            end=self._grid_serving_end,
            months=self._grid_serving_months,
            forecast_sensor_configured=grid_serving_forecast_sensor_configured,
            forecast_kwh=grid_serving_forecast_kwh,
            threshold_kwh=grid_serving_forecast_threshold,
        )
        if not grid_serving_eligible:
            self._grid_serving_setpoint_active = False
            self._grid_serving_wait_cycles = 0
            self._grid_serving_charge_confirm_cycles = 0
            self._grid_serving_release_confirm_cycles = 0
            self._grid_serving_import_confirm_cycles = 0

        max_soc_clamped_now = False
        manual_charge_active_now = False
        if soc_reached:
            in_timed_window = policy.timed_window_active
            in_grid_serving_window = policy.grid_serving_window_active
            if in_timed_window or in_grid_serving_window:
                # Ziel-SOC wurde innerhalb eines Netzlade-/netzdienlich-
                # Zeitfensters erreicht (oder die Sperre läuft von einem
                # solchen Fenster weiter) - Sperre bleibt gebunden an dieses
                # Fenster, damit sie spätestens an dessen Ende aktiv
                # aufgehoben wird, statt wie die geräteunabhängige
                # Max-SOC-Sperre unten unbegrenzt zu halten.
                self._max_soc_hold_is_window_bound = True
                self._max_soc_grid_import_wait_cycles = 0
                await self.async_start_sun_charge(0)
                max_soc_clamped_now = True
            elif self._max_soc_hold_is_window_bound:
                # Das Zeitfenster, während dessen die Sperre ausgelöst wurde,
                # ist vorbei - Register 40051 aktiv zurück auf 0 (SmartMeter-
                # Nullregelung) setzen, statt passiv auf den Timeout
                # (Register 40050) zu warten, damit der Speicher wieder im
                # normalen Betriebsmodus arbeitet.
                await self.async_stop_sun_charge()
                self._max_soc_hold_is_window_bound = False
                self._max_soc_grid_import_wait_cycles = 0
            else:
                # Geräteunabhängige Max-SOC-Sperre (siehe Abschnitt oben):
                # SOC wurde außerhalb jedes Netzlade-/netzdienlich-
                # Zeitfensters erreicht/überschritten (z. B. durch die
                # geräteeigene Nullregelung bei PV-Überschuss). Ein
                # gehaltener 0-%-Sollwert lässt den SOC nie von selbst unter
                # den Zielwert fallen (der Speicher deckt den Hausverbrauch
                # währenddessen nicht mit) - deshalb zusätzlich Netzbezug am
                # Smart Meter als Freigabe-Trigger auswerten, mit
                # Zyklen-Hysterese gegen kurze Lastspitzen.
                if self._max_soc_released_for_discharge:
                    # Nach bestätigter Freigabe darf derselbe unveränderte
                    # SOC keinen neuen 0-%-Task erzeugen. stop ist nach der
                    # ersten erfolgreichen Rücksetzung ein Write-freier No-Op.
                    await self.async_stop_sun_charge()
                    self._max_soc_grid_import_wait_cycles = 0
                else:
                    smartmeter_power = data.get("smartmeter_power")
                    # Vorzeichenkonvention (siehe const.py, SMARTMETER_PV_
                    # SURPLUS_THRESHOLD_WATT): positiv = Netzbezug.
                    grid_import_raw = (
                        smartmeter_power is not None
                        and smartmeter_power > SMARTMETER_PV_SURPLUS_THRESHOLD_WATT
                    )
                    grid_import_confirmed = self._cycles_confirmed(
                        "_max_soc_grid_import_wait_cycles", grid_import_raw
                    )
                    if grid_import_confirmed:
                        await self.async_stop_sun_charge()
                        if self._sun_charge_reset_required:
                            # Ein fehlgeschlagenes Modus-0-Schreiben ist noch
                            # keine Freigabe. Der bestätigte Zähler bleibt
                            # stehen, damit der nächste Poll nur die
                            # Rücksetzung wiederholt und nicht erneut klemmt.
                            max_soc_clamped_now = True
                        else:
                            self._max_soc_grid_import_wait_cycles = 0
                            self._max_soc_released_for_discharge = True
                    else:
                        await self.async_start_sun_charge(0)
                        max_soc_clamped_now = True
            grid_serving_active_now = False
        else:
            self._max_soc_hold_is_window_bound = False
            self._max_soc_grid_import_wait_cycles = 0
            manual_charge_active_now = self._grid_charge_power is not None
            if manual_charge_active_now:
                await self.async_start_sun_charge(self._grid_charge_power)
                grid_serving_active_now = False
            elif timed_should_charge or price_should_charge:
                # MIN_SETPOINT_POWER sättigt in _watts_to_ic_setpoint_raw
                # auf MIN_IC_POWER_SETPOINT_PCT (-100 %, maximale
                # Ladeleistung) - siehe Kommentar am Abschnittsanfang
                # "Zeitgesteuertes Laden" zur entfernten "Max.
                # Netzladeleistung". timed_should_charge und
                # price_should_charge sind hier bereits gegenseitig
                # ausschließend (price_should_charge schließt
                # timed_should_charge aus), Reihenfolge daher unerheblich.
                await self.async_start_sun_charge(MIN_SETPOINT_POWER)
                grid_serving_active_now = False
            elif grid_serving_eligible:
                # Vorrang vor der Neutralpreis-Pausezone: netzdienliches
                # Laden schließt price_should_pause bereits über
                # grid_serving_window_active aus (siehe oben), daher wird
                # dieser Zweig nie erreicht, wenn price_should_pause True
                # ist - grid_serving_eligible steht trotzdem vor
                # price_should_pause, damit die Priorität auch strukturell
                # sichtbar bleibt.
                if not self._grid_serving_setpoint_active:
                    # REQ-GRID-SERVING-CHARGE: Vor Schritt a muss die
                    # SmartMeter-Nullregelung tatsächlich freigegeben sein.
                    # Sonst kann ein 0-%-Task der zuvor höher priorisierten
                    # Max-SOC-Sperre weiterlaufen, obwohl deren Zielwert
                    # inzwischen angehoben wurde; Schritt a sieht dann 0 W
                    # Ladeleistung und kann den verwaisten Task nie selbst
                    # übernehmen oder beenden.
                    await self.async_stop_sun_charge()
                grid_serving_active_now = await self._async_step_grid_serving(data)
            elif price_should_pause:
                # Neutralpreis-Pausezone: manueller Sollwertmodus mit
                # Sollwert 0 statt Nullregelung - stoppt Laden UND Entladen
                # (derselbe Aufruf wie bei der Max-SOC-Sperre/Schritt a des
                # netzdienlichen Ladens oben).
                await self.async_start_sun_charge(0)
                grid_serving_active_now = False
            else:
                grid_serving_active_now = False
                # Nicht aus dem Vorhandensein eines Python-Tasks auf den
                # Gerätezustand schließen: Der erste inaktive Takt gleicht
                # Register 40051 ausdrücklich mit Modus 0 ab, danach ist der
                # Aufruf bei unverändertem Sollzustand ein No-Op.
                await self.async_stop_sun_charge()

        # _async_update_data arbeitet beim ersten Refresh noch mit einem
        # lokalen Dictionary, während self.data None ist. Nur einen in genau
        # dieser Auswertung quittierten Write dort optimistisch übernehmen.
        # Ohne neuen Write muss der echte Readback gewinnen; die frühere
        # pauschale Übernahme von _sun_charge_commanded_mode konnte eine
        # bereits wirksame Nullregelung dauerhaft als Sollwertvorgabe
        # anzeigen, wenn die Modbus-Antwort des Rücksetzwrites ausblieb.
        if (
            self._sun_charge_command_revision != command_revision_before
            and self._sun_charge_commanded_mode is not None
        ):
            data["ic_control_mode"] = self._sun_charge_commanded_mode
            data["ic_control_mode_text"] = CONTROL_MODE_LABELS.get(
                self._sun_charge_commanded_mode, UNKNOWN_LABEL
            )

        self._timed_charge_active = timed_should_charge and not manual_charge_active_now
        self._grid_serving_active = grid_serving_active_now
        self._price_charge_active = (
            price_should_charge and not soc_reached and not manual_charge_active_now
        )
        self._price_charge_status = self._price_charge_status_text(
            price_plan,
            charging=self._price_charge_active,
            paused_neutral_band=price_should_pause,
            soc_reached=soc_reached,
            pv_surplus_active=pv_surplus_active,
            timed_should_charge=timed_should_charge or manual_charge_active_now,
            grid_serving_window_active=grid_serving_window_active,
        )
        self._max_soc_clamped = max_soc_clamped_now

    async def _async_step_grid_serving(self, data: dict[str, Any]) -> bool:
        """Ein Schritt der unter _async_enforce_grid_charge (Punkt 4)
        beschriebenen Zustandsmaschine für netzdienliches Laden. Nur
        aufgerufen, wenn grid_serving_eligible dort bereits True ist (SOC
        nicht erreicht, Zeitfenster/Monat/Schalter aktiv, kein Vorrang für
        zeitgesteuertes Laden). Gibt zurück, ob netzdienliches Laden gerade
        aktiv in den Sollwertvorgabemodus eingreift (entspricht
        self._grid_serving_setpoint_active nach diesem Aufruf).

        Schritt a (ohne aktiven Sollwertvorgabemodus): Prüft die
        tatsächliche Ladeleistung des SAX (negativer Anteil von
        data["storage_power_active"], siehe sensor.py
        _negative_part("storage_power_active")) gegen
        SMARTMETER_PV_SURPLUS_THRESHOLD_WATT, mit derselben
        Zyklen-Hysterese wie die drei anderen Stellen, die diesen
        Schwellwert auswerten (self._cycles_confirmed,
        PV_SURPLUS_HYSTERESIS_CYCLES) - erst wenn der Speicher selbst (über
        die geräteeigene SmartMeter-Nullregelung) so viele Zyklen in Folge
        mit mindestens diesem Wert lädt, übernimmt die Software aktiv die
        Kontrolle (Sollwertvorgabemodus + Ladung auf 0 % gestoppt in einem
        Aufruf, async_start_sun_charge(0)) und wartet danach zusätzlich
        einmalig PV_SURPLUS_HYSTERESIS_CYCLES Aufrufe dieser Methode ab
        (self._grid_serving_wait_cycles), bevor Schritt b greift - Register
        40051 und der gestoppte Sollwert sollen sich setzen können, bevor
        erneut ausgewertet wird.

        Schritt a.1 (Netzbezugs-Schutz, mit aktivem Sollwertvorgabemodus,
        UNABHÄNGIG von den Wartezyklen): Solange der Sollwert bei 0 % steht,
        fließt kein Ladestrom mehr in den Speicher - deckt der Hausverbrauch
        die PV-Erzeugung nicht mehr, entsteht dadurch Netzbezug, den die
        Nullregelung sonst durch eigenständiges Entladen abfangen würde.
        Deshalb wird data["smartmeter_power"] hier zusätzlich, bereits
        während der Wartezyklen, gegen SMARTMETER_PV_SURPLUS_THRESHOLD_WATT
        auf tatsächlichen Netzbezug geprüft (positiver Wert, siehe
        Vorzeichenkonvention in REQ-SUNSPEC-MODE-CORRECTION), ebenfalls mit
        der PV_SURPLUS_HYSTERESIS_CYCLES-Zyklen-Hysterese
        (self._grid_serving_import_confirm_cycles). Bleibt der Netzbezug so
        viele Zyklen in Folge über dem Schwellwert, wird der Speicher sofort
        aktiv zurück in die SmartMeter-Nullregelung gesetzt
        (async_stop_sun_charge) - der Speicher lädt dadurch weiterhin nicht
        (kein PV-Überschuss vorhanden, sonst läge kein Netzbezug vor),
        entlädt sich aber smartmeter-gesteuert, um den Netzbezug zu
        vermeiden. Damit bricht dieser Schutz auch die Wartezyklen-
        Unterdrückung, unter der Schritt b sonst steht. Fällt der Netzbezug
        anschließend wieder unter den Schwellwert, wertet die Methode ab dem
        nächsten Aufruf wieder regulär ab Schritt a.

        Schritt b (mit aktivem Sollwertvorgabemodus, nach Ablauf der
        Wartezyklen, ohne bestätigten Netzbezug): Prüft die am Smart Meter
        gemessene Netzeinspeisung (data["smartmeter_power"]) gegen denselben
        Schwellwert, ebenfalls mit dieser Zyklen-Hysterese. Erst wenn sie so
        viele Zyklen in Folge unter den Schwellwert fällt, wird der Speicher
        aktiv zurück in die SmartMeter-Nullregelung gesetzt
        (async_stop_sun_charge). Bleibt die Einspeisung mindestens beim
        Schwellwert (oder ist der Messwert gerade nicht bekannt, oder reißt
        die Unterschreitung zwischendurch wieder ab), bleibt die Ladung
        bewusst bei 0 % gehalten - das ist der eigentliche Zweck der
        Funktion: der Speicher soll erst wieder laden, sobald ein Zeitpunkt
        mit gefallener Einspeisung erreicht ist, nicht fortlaufend mit dem
        Überschuss mitlaufen.
        """
        if not self._grid_serving_setpoint_active:
            storage_power_active = data.get("storage_power_active")
            sax_charge_power = (
                -storage_power_active
                if storage_power_active is not None and storage_power_active < 0
                else 0
            )
            charge_confirmed = self._cycles_confirmed(
                "_grid_serving_charge_confirm_cycles",
                sax_charge_power >= SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
            )
            if charge_confirmed:
                await self.async_start_sun_charge(0)
                self._grid_serving_setpoint_active = True
                self._grid_serving_wait_cycles = PV_SURPLUS_HYSTERESIS_CYCLES
                self._grid_serving_charge_confirm_cycles = 0
            return self._grid_serving_setpoint_active

        smartmeter_power = data.get("smartmeter_power")
        import_confirmed = self._cycles_confirmed(
            "_grid_serving_import_confirm_cycles",
            smartmeter_power is not None
            and smartmeter_power > SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
        )
        if import_confirmed:
            await self.async_stop_sun_charge()
            self._grid_serving_setpoint_active = False
            self._grid_serving_wait_cycles = 0
            self._grid_serving_import_confirm_cycles = 0
            self._grid_serving_release_confirm_cycles = 0
            return False

        if self._grid_serving_wait_cycles > 0:
            self._grid_serving_wait_cycles -= 1
            await self.async_start_sun_charge(0)
            return True

        # Vorzeichenkonvention (siehe const.py, SMARTMETER_PV_SURPLUS_
        # THRESHOLD_WATT): Einspeisung (negativ) ist unter den Schwellwert
        # gefallen, sobald der Anzeigewert über -Schwellwert liegt.
        release_confirmed = self._cycles_confirmed(
            "_grid_serving_release_confirm_cycles",
            smartmeter_power is not None
            and smartmeter_power > -SMARTMETER_PV_SURPLUS_THRESHOLD_WATT,
        )
        if release_confirmed:
            await self.async_stop_sun_charge()
            self._grid_serving_setpoint_active = False
            self._grid_serving_release_confirm_cycles = 0
            return False

        # Selbstheilung: async_start_sun_charge(0) hier - statt nur beim
        # ersten Auslösen von Schritt a - erneut aufzurufen, ist bei
        # unverändertem Sollwert UND weiterhin laufendem _sun_charge_task ein
        # No-Op (siehe async_start_sun_charge), stellt aber sicher, dass ein
        # unerwartet gestorbener Task (z. B. durch einen einzelnen
        # transienten Modbus-Fehler in _async_sun_charge_loop, der den Task
        # beendet statt ihn zu retryen) noch in demselben Zyklus neu
        # gestartet wird. Ohne diesen Aufruf blieb
        # self._grid_serving_setpoint_active dauerhaft True, während
        # Register 40049/40051 nicht mehr neu geschrieben wurden - das Gerät
        # fiel nach seinem eigenen Timeout (Register 40050) unbeaufsichtigt
        # in die SmartMeter-Nullregelung zurück und lud unbemerkt wieder,
        # während der Sensor "Netzdienliches Laden aktiv" weiterhin True
        # zeigte (ursprünglich gemeldeter Bug: SAX beginnt während
        # netzdienlichem Laden plötzlich zu laden).
        await self.async_start_sun_charge(0)
        return True

    # -- Netzdienliches Laden --------------------------------------------------
    # Eigenständiges, zum zeitgesteuerten Laden oben zeitlich exklusives
    # Feature (siehe _assert_windows_dont_overlap): blockiert das Laden des
    # Speichers innerhalb eines eigenen Zeitfensters aktiv, sobald PV-
    # Überschuss über der Schwelle gemessen wird, damit das Laden in die Zeit
    # mit dem höchsten PV-Ertrag verschoben wird, statt bereits im Fenster
    # stattzufinden. Teilt sich mit zeitgesteuertem Laden denselben
    # SunSpec-Modus-Schreibpfad sowie die Max-SOC-Sperre - "Max.
    # Netzladeleistung" wird hier NICHT benötigt, da nie tatsächlich mit
    # einem Sollwert > 0 geladen wird - siehe _async_enforce_grid_charge für
    # die Priorisierung und anforderung.yaml, REQ-GRID-SERVING-CHARGE.

    @property
    def grid_serving_enabled(self) -> bool:
        return self._grid_serving_enabled

    @property
    def grid_serving_start(self) -> dt_time | None:
        return self._grid_serving_start

    @property
    def grid_serving_end(self) -> dt_time | None:
        return self._grid_serving_end

    @property
    def grid_serving_months(self) -> frozenset[int]:
        return frozenset(self._grid_serving_months)

    @property
    def grid_serving_active(self) -> bool:
        return self._grid_serving_active

    @property
    def grid_serving_forecast_threshold_kwh(self) -> float:
        """Effective forecast threshold; 0 keeps static scheduling active."""
        return (
            self._grid_serving_forecast_threshold_kwh
            if self._grid_serving_forecast_threshold_kwh is not None
            else DEFAULT_GRID_SERVING_FORECAST_THRESHOLD_KWH
        )

    @property
    def grid_serving_forecast_threshold_kwh_raw(self) -> float | None:
        """Configured value without fallback, used by the RestoreEntity."""
        return self._grid_serving_forecast_threshold_kwh

    @property
    def grid_serving_forecast_kwh(self) -> float | None:
        return self._grid_serving_forecast_kwh

    @property
    def grid_serving_forecast_allowed(self) -> bool:
        return self._grid_serving_forecast_allowed

    @property
    def grid_serving_window_active(self) -> bool:
        return self._grid_serving_window_active

    async def async_set_grid_serving_enabled(self, enabled: bool) -> None:
        self._grid_serving_enabled = enabled
        self.clear_control_field_unresolved("grid_serving_enabled")
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_forecast_threshold_kwh(
        self, value: float | None
    ) -> None:
        """Set and immediately apply the optional minimum PV forecast."""
        self._grid_serving_forecast_threshold_kwh = _clamp_float(
            round_half_up(value),
            MIN_GRID_SERVING_FORECAST_THRESHOLD_KWH,
            MAX_GRID_SERVING_FORECAST_THRESHOLD_KWH,
        )
        self.clear_control_field_unresolved("grid_serving_forecast_threshold_kwh")
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_start(self, value: dt_time) -> None:
        if self._windows_overlap_with_months(
            value,
            self._grid_serving_end,
            self._grid_serving_months,
            self._timed_charge_start,
            self._timed_charge_end,
            self._timed_charge_months,
        ):
            self._notify_time_window_overlap(
                "netzdienliches Laden",
                value,
                self._grid_serving_end,
                self._grid_serving_months,
                "Netzladung",
                self._timed_charge_start,
                self._timed_charge_end,
                self._timed_charge_months,
            )
            self._grid_serving_start = None
        else:
            self._grid_serving_start = value
        self.clear_control_field_unresolved("grid_serving_start")
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_end(self, value: dt_time) -> None:
        if self._windows_overlap_with_months(
            self._grid_serving_start,
            value,
            self._grid_serving_months,
            self._timed_charge_start,
            self._timed_charge_end,
            self._timed_charge_months,
        ):
            self._notify_time_window_overlap(
                "netzdienliches Laden",
                self._grid_serving_start,
                value,
                self._grid_serving_months,
                "Netzladung",
                self._timed_charge_start,
                self._timed_charge_end,
                self._timed_charge_months,
            )
            self._grid_serving_end = None
        else:
            self._grid_serving_end = value
        self.clear_control_field_unresolved("grid_serving_end")
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_window(self, start: dt_time, end: dt_time) -> None:
        """Analog zu async_set_timed_charge_window, für das netzdienliche
        Laden - siehe dort für den Hintergrund (Vermeidung falscher
        Erkennung einer Überschneidung durch Zwischenzustände beim
        getrennten Setzen von Start- und Ende-Entity)."""
        if self._windows_overlap_with_months(
            start,
            end,
            self._grid_serving_months,
            self._timed_charge_start,
            self._timed_charge_end,
            self._timed_charge_months,
        ):
            self._notify_time_window_overlap(
                "netzdienliches Laden",
                start,
                end,
                self._grid_serving_months,
                "Netzladung",
                self._timed_charge_start,
                self._timed_charge_end,
                self._timed_charge_months,
            )
            self._grid_serving_start = None
            self._grid_serving_end = None
        else:
            self._grid_serving_start = start
            self._grid_serving_end = end
        self.clear_control_field_unresolved("grid_serving_start")
        self.clear_control_field_unresolved("grid_serving_end")
        await self._async_apply_grid_charge_change()

    async def async_set_grid_serving_month(
        self, month: int, enabled: bool, validate: bool = True
    ) -> None:
        """Analog zu async_set_timed_charge_month, für das netzdienliche
        Laden."""
        new_months = set(self._grid_serving_months)
        if enabled:
            new_months.add(month)
        else:
            new_months.discard(month)
        if validate:
            self._assert_windows_dont_overlap(
                self._grid_serving_start,
                self._grid_serving_end,
                new_months,
                self._timed_charge_start,
                self._timed_charge_end,
                self._timed_charge_months,
            )
        self._grid_serving_months = new_months
        if validate:
            # Siehe async_set_timed_charge_month für den Hintergrund.
            self.clear_control_field_unresolved("grid_serving_months")
        await self._async_apply_grid_charge_change()

    # -- Preisoptimiertes Laden ------------------------------------------------
    # Dritte Lade-Automatik neben zeitgesteuertem und netzdienlichem Laden
    # (siehe anforderung.yaml, REQ-DYNAMIC-PRICE-CHARGE). Lädt den Speicher
    # aus dem Netz, wenn der Strompreis günstig ist, und überlässt ihn in
    # teuren Phasen der normalen SmartMeter-Nullregelung, sodass die dort
    # gespeicherte Energie den Hausverbrauch deckt.
    #
    # Arbeitsteilung: price_optimizer.SaxPricePlanner liest den vom Anwender
    # ausgewählten Strompreis-Sensor (plus optional eine PV-Prognose) und
    # berechnet daraus alle PRICE_EVAL_INTERVAL Sekunden einen Ladeplan -
    # ohne jeden Modbus-Zugriff. Der Coordinator wertet diesen Plan bei jedem
    # Poll-Zyklus in _async_enforce_grid_charge aus und setzt ihn über
    # denselben SunSpec-Schreibpfad (_sun_charge_task, Register 40051/40049)
    # um wie die beiden anderen Automatiken - inklusive derselben
    # Max-SOC-Sperre und derselben PV-Überschuss-Hysterese.
    #
    # Lädt wie das zeitgesteuerte Laden immer mit maximal möglicher
    # Leistung (siehe Kommentar am Abschnittsanfang "Zeitgesteuertes
    # Laden"). Ziel-SOC: derselbe Wert wie "Max. SOC" (self._max_soc) -
    # keine eigene Einstellung, siehe number.SaxPowerMaxSocNumber.

    @property
    def price_charge_enabled(self) -> bool:
        return self._price_charge_enabled

    @property
    def price_charge_strategy(self) -> str:
        return self._price_charge_strategy

    @property
    def price_charge_max_price(self) -> float | None:
        return self._price_charge_max_price

    @property
    def price_charge_neutral_price(self) -> float | None:
        return self._price_charge_neutral_price

    @property
    def price_charge_hours(self) -> int:
        return (
            self._price_charge_hours
            if self._price_charge_hours is not None
            else DEFAULT_PRICE_HOURS
        )

    @property
    def price_charge_hours_raw(self) -> int | None:
        """Wie price_charge_hours, aber ohne Fallback - für die NumberEntity,
        die zwischen "noch nicht restauriert" (None) und einem echten Wert
        unterscheiden muss (siehe number.SaxPowerPriceChargeHoursNumber)."""
        return self._price_charge_hours

    @property
    def price_charge_active(self) -> bool:
        return self._price_charge_active

    @property
    def price_charge_status(self) -> str:
        return self._price_charge_status

    @property
    def price_plan(self) -> PricePlan:
        return self.price_planner.plan

    async def async_set_price_charge_enabled(
        self, enabled: bool, *, force: bool = False
    ) -> bool:
        """Preisoptimiertes Laden ein-/ausschalten. Gibt zurück, ob die
        Änderung übernommen wurde - siehe async_set_timed_charge_enabled für
        die gemeinsame Konfliktbehandlung mit der Netzladung."""
        if enabled and self._timed_charge_enabled:
            if not force:
                self._async_create_charge_conflict_issue(ISSUE_PRICE_CHARGE_CONFLICT)
                return False
            self._timed_charge_enabled = False
        self._price_charge_enabled = enabled
        self.clear_control_field_unresolved("price_charge_enabled")
        self.async_dismiss_charge_conflict()
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()
        return True

    async def async_set_price_charge_strategy(self, strategy: str) -> None:
        if strategy not in PRICE_STRATEGIES:
            raise HomeAssistantError(
                f"Unbekannte Strategie {strategy!r} - erlaubt sind: "
                f"{', '.join(PRICE_STRATEGIES)}"
            )
        self._price_charge_strategy = strategy
        self.clear_control_field_unresolved("price_charge_strategy")
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()

    async def async_set_price_charge_max_price(self, value: float | None) -> None:
        """Preisgrenze für den Modus "Absoluter Preis" (EUR/kWh).

        Klemmt auf [MIN_PRICE_LIMIT, MAX_PRICE_LIMIT], siehe async_set_max_soc
        für die Begründung (RestoreEntity-Pfad ohne NumberEntity-Validierung).
        """
        self._price_charge_max_price = _clamp_float(
            value, MIN_PRICE_LIMIT, MAX_PRICE_LIMIT
        )
        self.clear_control_field_unresolved("price_charge_max_price")
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()

    async def async_set_price_charge_neutral_price(self, value: float | None) -> None:
        """Neutralpreis (EUR/kWh) - oberhalb der Preisgrenze liegender
        Schwellwert, ab dem sich die Entladung aus dem Speicher wieder
        lohnt (siehe const.py, DEFAULT_PRICE_NEUTRAL, sowie
        _async_enforce_grid_charge zur Pause-Zone dazwischen).

        Klemmt auf denselben Bereich wie die Preisgrenze, siehe
        async_set_price_charge_max_price. Erzwingt keine Reihenfolge
        gegenüber der Preisgrenze - eine falsch herum liegende Kombination
        wird stattdessen von _check_price_neutral_below_limit als
        Reparaturhinweis gemeldet, statt den Wert stillschweigend zu
        verwerfen."""
        self._price_charge_neutral_price = _clamp_float(
            value, MIN_PRICE_LIMIT, MAX_PRICE_LIMIT
        )
        self.clear_control_field_unresolved("price_charge_neutral_price")
        await self._async_apply_grid_charge_change()

    async def async_set_price_charge_hours(self, value: int | None) -> None:
        self._price_charge_hours = _clamp_int(value, MIN_PRICE_HOURS, MAX_PRICE_HOURS)
        self.clear_control_field_unresolved("price_charge_hours")
        self.price_planner.evaluate()
        await self._async_apply_grid_charge_change()

    async def async_apply_price_plan(self) -> None:
        """Vom Planner nach jeder periodischen Neuberechnung aufgerufen -
        wendet das Ergebnis sofort auf das Gerät an, statt bis zum nächsten
        Poll-Zyklus zu warten."""
        await self._async_apply_grid_charge_change()

    def _price_charge_status_text(
        self,
        plan: PricePlan,
        *,
        charging: bool,
        paused_neutral_band: bool,
        soc_reached: bool,
        pv_surplus_active: bool,
        timed_should_charge: bool,
        grid_serving_window_active: bool,
    ) -> str:
        """Anzeigetext für den Sensor "Preisoptimiertes Laden Status".

        Der Planner kennt nur die Preisseite ("Warten auf Preisabfall",
        "Keine Preisdaten", ...). Hier kommen die Gründe dazu, die das Laden
        unabhängig vom Preis verhindern - in der Reihenfolge, in der
        _async_enforce_grid_charge sie tatsächlich auswertet, damit der
        angezeigte Grund immer der wirksame ist.
        """
        strategy_off = self._price_charge_strategy == PRICE_STRATEGY_OFF
        if not self._price_charge_enabled or strategy_off:
            return PRICE_STATUS_OFF
        if plan.status in (PRICE_STATUS_NO_PRICE_DATA, PRICE_STATUS_PV_FORECAST_COVERS):
            return plan.status
        if charging:
            return PRICE_STATUS_CHARGING
        if soc_reached:
            return PRICE_STATUS_PAUSED_MAX_SOC
        if timed_should_charge:
            return PRICE_STATUS_PAUSED_TIMED_CHARGE
        if grid_serving_window_active:
            return PRICE_STATUS_PAUSED_GRID_SERVING
        if pv_surplus_active:
            return PRICE_STATUS_PAUSED_PV_SURPLUS
        if paused_neutral_band:
            return PRICE_STATUS_PAUSED_NEUTRAL_BAND
        return plan.status

    # -- Konflikt Netzladung <-> preisoptimiertes Laden ------------------------
    def _async_create_charge_conflict_issue(self, issue_key: str) -> None:
        """Legt den Bestätigungsdialog an, statt die Aktivierung des zweiten
        netzladenden Features stillschweigend abzulehnen.

        Home Assistant kennt für Entity-Aktionen keinen synchronen
        Bestätigungsdialog; ein reparierbares Issue (repairs.py) ist der
        native Weg zu einem echten Ja/Nein-Dialog. Zusätzlich wird eine
        Persistent Notification erzeugt, damit der Anwender die Rückfrage
        sofort sieht und nicht erst beim nächsten Blick auf
        Einstellungen -> Reparaturen. Beide werden gemeinsam wieder entfernt
        (async_dismiss_charge_conflict).
        """
        if issue_key == ISSUE_PRICE_CHARGE_CONFLICT:
            message = (
                "Preisoptimiertes Laden wurde eingeschaltet, während die "
                "Netzladung (zeitgesteuertes Laden) aktiv ist. Beide laden "
                "aktiv aus dem Netz und können nicht gleichzeitig laufen. "
                "Unter Einstellungen -> Geräte & Dienste -> Reparaturen kann "
                "bestätigt werden, dass die Netzladung dafür abgeschaltet "
                "wird - oder der Vorgang abgebrochen werden. Bis dahin "
                "bleibt preisoptimiertes Laden ausgeschaltet."
            )
        else:
            message = (
                "Die Netzladung (zeitgesteuertes Laden) wurde eingeschaltet, "
                "während preisoptimiertes Laden aktiv ist. Beide laden aktiv "
                "aus dem Netz und können nicht gleichzeitig laufen. Unter "
                "Einstellungen -> Geräte & Dienste -> Reparaturen kann "
                "bestätigt werden, dass preisoptimiertes Laden dafür "
                "abgeschaltet wird - oder der Vorgang abgebrochen werden. Bis "
                "dahin bleibt die Netzladung ausgeschaltet."
            )
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            f"{issue_key}_{self.entry_id}",
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key=issue_key,
            data={"entry_id": self.entry_id, "issue_key": issue_key},
        )
        persistent_notification.async_create(
            self.hass,
            message,
            title="SAX Power: Bestätigung erforderlich",
            notification_id=f"{DOMAIN}_{self.entry_id}_charge_conflict",
        )

    def async_dismiss_charge_conflict(self) -> None:
        """Entfernt Bestätigungsdialog und Benachrichtigung - sowohl nach
        einer Bestätigung als auch nach einem Abbruch, und immer dann, wenn
        eine der beiden Einstellungen erfolgreich geändert wurde (der
        Konflikt ist dann per Definition nicht mehr aktuell)."""
        for issue_key in CHARGE_CONFLICT_ISSUES:
            ir.async_delete_issue(self.hass, DOMAIN, f"{issue_key}_{self.entry_id}")
        persistent_notification.async_dismiss(
            self.hass, f"{DOMAIN}_{self.entry_id}_charge_conflict"
        )

    # -- Selbstdiagnose (siehe anforderung.yaml, REQ-SELF-DIAGNOSIS-REPAIRS) --
    def _async_check_self_diagnostics(self) -> None:
        """Evaluate repair rules through the dedicated boundary adapter."""
        self._self_diagnostics.check(
            DiagnosticSnapshot(
                price_status=self.price_planner.plan.status,
                price_entity_id=self.price_planner.price_entity_id,
                extended_available=self._extended_available,
                extended_unavailable_since=self._extended_unavailable_since,
                slave_id_extended=self.slave_id_extended,
                max_soc=self._max_soc,
                timed_min_soc=self._timed_charge_min_soc,
                price_limit=self._price_charge_max_price,
                neutral_price=self._price_charge_neutral_price,
                timed_enabled=self._timed_charge_enabled,
                timed_start=self._timed_charge_start,
                timed_end=self._timed_charge_end,
                timed_months=frozenset(self._timed_charge_months),
                grid_serving_enabled=self._grid_serving_enabled,
                grid_serving_start=self._grid_serving_start,
                grid_serving_end=self._grid_serving_end,
                grid_serving_months=frozenset(self._grid_serving_months),
                economics_tariff_enabled=self.tariff_provider.config.enabled,
                economics_price_unavailable=self._economics_price_unavailable,
            ),
            monotonic(),
        )

    async def async_shutdown(self) -> None:
        # super().async_shutdown() (DataUpdateCoordinator) storniert den
        # periodischen Poll-Timer sowie den Debounced-Refresh - ohne diesen
        # Aufruf lief der Timer beim Entladen des Config Entry (siehe
        # __init__.async_unload_entry) unbemerkt im Hintergrund weiter.
        await super().async_shutdown()
        await self._async_flush_energy_state()
        await self._async_flush_economics_state()
        await self._async_flush_control_state()
        self.price_planner.async_shutdown()
        self.tariff_provider.async_shutdown()
        # Kein Stop-via-Service: Dieser würde nach dem manuellen Reset eine
        # konfigurierte Automatik erneut anwenden. Beim Shutdown werden unter
        # demselben Control-Lock stattdessen alle neuen Entscheidungen
        # ausgesperrt, der gemeinsame Writer abgewartet und Modus 0 versucht.
        async with self._charge_control_lock:
            self._grid_charge_power = None
            await self.async_stop_sun_charge()
        ir.async_delete_issue(
            self.hass, DOMAIN, f"{ISSUE_EXTENDED_MODE_UNAVAILABLE}_{self.entry_id}"
        )
