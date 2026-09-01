"""Home-Assistant-Adapter für das Tarifmodell der Wirtschaftlichkeit.

Einzige Stelle, an der die Wirtschaftlichkeitsauswertung Options- und
Sensorzustände liest; der Coordinator und die späteren Auswertungen
beziehen ihren Netzbezugspreis ausschließlich über
SaxTariffProvider.quote(). Die reinen Typen und Regeln liegen in
domain/tariff.py, die Options-Abbildung in application/economics.py.

Siehe anforderung.yaml, REQ-ECONOMICS-TARIFFS.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .application.economics import tariff_config_from_options
from .const import (
    CONF_PRICE_ATTRIBUTE,
    CONF_PRICE_SENSOR,
    CONF_PRICE_UNIT,
    DEFAULT_PRICE_UNIT,
)
from .domain.price_units import unit_factor
from .domain.tariff import (
    PriceQuote,
    QuoteResult,
    QuoteSource,
    QuoteUnavailable,
    TariffConfig,
    TariffType,
    evaluate_static_tariff,
    is_valid_feed_in_price,
    is_valid_import_price,
    validate_tariff,
)
from .price_optimizer import has_price_forecast, parse_price_slots

if TYPE_CHECKING:
    from .coordinator import SaxPowerCoordinator

_LOGGER = logging.getLogger(__name__)

DISABLED_RESULT = QuoteResult(reason=QuoteUnavailable.TARIFF_DISABLED)


class SaxTariffProvider:
    """Bestimmt den zu einem Zeitpunkt gültigen Netzbezugspreis.

    Die Auswertung läuft bei jedem Aufruf frisch gegen die aktuellen
    Options und Sensorzustände; eine Options-Änderung wirkt dadurch sofort
    und ohne Config-Entry-Reload. Der zusätzlich registrierte
    Zustandsbeobachter des dynamischen Preis-Sensors hält nur den
    zwischengespeicherten Stand (`last_result`) aktuell, den Diagnose und
    spätere Auswertungen ohne eigene Neuberechnung lesen können.
    """

    def __init__(self, hass: HomeAssistant, coordinator: SaxPowerCoordinator) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.last_result: QuoteResult = DISABLED_RESULT
        self._unsub: list[CALLBACK_TYPE] = []

    # -- Konfiguration aus dem Options Flow --------------------------------
    @property
    def config(self) -> TariffConfig:
        return tariff_config_from_options(self.coordinator.options)

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    @property
    def feed_in_price_eur_kwh(self) -> float | None:
        """Einspeisevergütung in EUR/kWh - der Beschaffungspreis von
        PV-Energie, die statt ins Netz in den Speicher fließt.

        Prüft den Wertebereich (0 bis 2 EUR/kWh) genauso wie
        validate_tariff() für die Quote-Erzeugung: Ein von Hand
        beschädigter Store kann einen endlichen, aber außerhalb des
        zulässigen Bereichs liegenden Wert enthalten (z. B. 3 EUR/kWh) -
        der darf nicht ungeprüft in die PV-Bewertung der
        Wirtschaftlichkeitsbilanz einfließen (REQ-ECONOMICS-ACCOUNTING).
        """
        config = self.config
        if not config.enabled:
            return None
        price = config.feed_in_price_eur_kwh
        return price if is_valid_feed_in_price(price) else None

    @property
    def price_entity_id(self) -> str | None:
        return self.coordinator.options.get(CONF_PRICE_SENSOR) or None

    # -- Lebenszyklus -------------------------------------------------------
    @callback
    def async_setup(self) -> None:
        """Zustandsbeobachter registrieren (idempotent).

        Räumt zuerst die Beobachter der vorherigen Konfiguration ab, damit
        ein Options-Wechsel weder einen Listener auf den alten Sensor
        stehen lässt noch einen zweiten auf denselben Sensor anlegt.
        """
        self.async_shutdown()
        entity_id = self.price_entity_id
        if self.config.tariff_type is TariffType.DYNAMIC and entity_id:
            self._unsub.append(
                async_track_state_change_event(
                    self.hass, [entity_id], self._async_price_sensor_changed
                )
            )
        self.evaluate()

    @callback
    def async_shutdown(self) -> None:
        while self._unsub:
            self._unsub.pop()()

    @callback
    def _async_price_sensor_changed(self, _event: Event[EventStateChangedData]) -> None:
        self.evaluate()

    # -- Auswertung ---------------------------------------------------------
    @callback
    def evaluate(self, moment: datetime | None = None) -> QuoteResult:
        """Aktuellen Netzbezugspreis bestimmen und zwischenspeichern."""
        self.last_result = self.quote(moment)
        return self.last_result

    def quote(self, moment: datetime | None = None) -> QuoteResult:
        """Netzbezugspreis zu `moment` (Vorgabe: jetzt, lokale Zeit).

        Liefert bei jedem Problem None samt maschinenlesbarem Grund - nie
        einen Ersatzpreis.
        """
        config = self.config
        # Gilt für alle Tarifarten, auch die dynamische: ohne gültige
        # Einspeisevergütung (und ohne die tarifeigenen Pflichtpreise)
        # entsteht gar kein Quote.
        reason = validate_tariff(config)
        if reason is not None:
            return QuoteResult(reason=reason)
        now = dt_util.as_local(moment) if moment else dt_util.now()
        if config.tariff_type is TariffType.DYNAMIC:
            return self._dynamic_quote(config, now)
        return evaluate_static_tariff(config, now)

    def _dynamic_quote(self, config: TariffConfig, now: datetime) -> QuoteResult:
        """Quote aus dem im Options Flow gewählten Strompreis-Sensor.

        Nutzt bewusst denselben Sensor, dieselbe Attribut- und dieselbe
        Einheitenkonfiguration wie die Ladeplanung
        (price_optimizer.parse_price_slots) - Wirtschaftlichkeit und
        Ladeentscheidung dürfen nicht gegen unterschiedliche Preise
        rechnen.
        """
        entity_id = self.price_entity_id
        if not entity_id:
            return QuoteResult(reason=QuoteUnavailable.PRICE_SENSOR_NOT_CONFIGURED)
        state = self.hass.states.get(entity_id)
        if state is None:
            return QuoteResult(reason=QuoteUnavailable.PRICE_SENSOR_MISSING)
        if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, ""):
            return QuoteResult(reason=QuoteUnavailable.PRICE_SENSOR_UNAVAILABLE)

        configured_unit = (
            self.coordinator.options.get(CONF_PRICE_UNIT) or DEFAULT_PRICE_UNIT
        )
        factor = unit_factor(
            configured_unit, state.attributes.get("unit_of_measurement")
        )
        if factor is None:
            return QuoteResult(reason=QuoteUnavailable.PRICE_UNIT_UNSUPPORTED)

        # Die Preisvorschau ist die genauere Quelle: sie liefert zusätzlich
        # den Gültigkeitszeitraum des Preises. Sobald der Sensor überhaupt
        # eine mitbringt, ist sie auch verbindlich - weder ein fehlender
        # Slot für "jetzt" (veraltete Vorschau) noch eine unlesbare Vorschau
        # darf stillschweigend durch den Sensorzustand ersetzt werden.
        attribute = self.coordinator.options.get(CONF_PRICE_ATTRIBUTE) or None
        slots = parse_price_slots(
            state, attribute=attribute, unit=configured_unit, now=now
        )
        if slots:
            for slot in slots:
                if slot.overlaps(now):
                    return self._priced(
                        slot.price,
                        QuoteSource.DYNAMIC_FORECAST,
                        slot.start,
                        slot.end,
                    )
            _LOGGER.debug(
                "Wirtschaftlichkeit: Preisvorschau von %s deckt %s nicht ab",
                entity_id,
                now.isoformat(),
            )
            return QuoteResult(reason=QuoteUnavailable.PRICE_FORECAST_OUT_OF_RANGE)
        if has_price_forecast(state, attribute=attribute):
            _LOGGER.debug(
                "Wirtschaftlichkeit: Preisvorschau von %s ist nicht auswertbar",
                entity_id,
            )
            return QuoteResult(reason=QuoteUnavailable.PRICE_FORECAST_UNREADABLE)

        try:
            value = float(state.state)
        except TypeError, ValueError:
            return QuoteResult(reason=QuoteUnavailable.PRICE_NOT_NUMERIC)
        if not math.isfinite(value):
            return QuoteResult(reason=QuoteUnavailable.PRICE_NOT_FINITE)
        return self._priced(value * factor, QuoteSource.DYNAMIC_STATE)

    def _priced(
        self,
        price_eur_kwh: float,
        source: QuoteSource,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> QuoteResult:
        """Quote aus einem bereits auf EUR/kWh normalisierten Preis.

        Der Wertebereich gilt auch für den dynamischen Tarif: ein Sensor,
        der 999 meldet, liefert keinen Arbeitspreis, sondern einen falsch
        skalierten oder schlicht falschen Wert - der darf nicht als gültiger
        Netzbezugspreis in die Wirtschaftlichkeit eingehen.
        """
        if not is_valid_import_price(price_eur_kwh):
            return QuoteResult(reason=QuoteUnavailable.PRICE_OUT_OF_RANGE)
        return QuoteResult(PriceQuote(price_eur_kwh, source, valid_from, valid_until))

    # -- Diagnose -----------------------------------------------------------
    @property
    def diagnostics(self) -> dict[str, Any]:
        """Tarifzustand für den Diagnose-Download (diagnostics.py)."""
        config = self.config
        result = self.evaluate()
        quote = result.quote
        return {
            "tariff_type": str(config.tariff_type),
            # Erlaubte Quell-ID (REQ-ECONOMICS-OBSERVABILITY): eine
            # Entity-ID ist keine identifizierende Information wie Host
            # oder Seriennummer und wird deshalb unredigiert gezeigt - nur
            # gesetzt, wenn der Tarif tatsächlich dynamisch ist.
            "price_sensor_entity_id": (
                self.price_entity_id
                if config.tariff_type is TariffType.DYNAMIC
                else None
            ),
            "feed_in_price_eur_kwh": config.feed_in_price_eur_kwh,
            "fixed_import_price_eur_kwh": config.fixed_import_price_eur_kwh,
            "tou_base_price_eur_kwh": config.tou_base_price_eur_kwh,
            "tou_windows": [
                {
                    "start": window.start.isoformat(),
                    "end": window.end.isoformat(),
                    "price_eur_kwh": window.price_eur_kwh,
                }
                for window in config.windows
            ],
            "quote_price_eur_kwh": None if quote is None else quote.price_eur_kwh,
            "quote_source": None if quote is None else str(quote.source),
            "quote_valid_from": (
                None
                if quote is None or quote.valid_from is None
                else quote.valid_from.isoformat()
            ),
            "quote_valid_until": (
                None
                if quote is None or quote.valid_until is None
                else quote.valid_until.isoformat()
            ),
            "quote_unavailable_reason": (
                None if result.reason is None else str(result.reason)
            ),
        }
