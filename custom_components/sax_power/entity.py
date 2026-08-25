"""Base entity for the SAX Power integration."""

from __future__ import annotations

import logging
import math
from datetime import time as dt_time
from typing import Any

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import SaxPowerCoordinator

_LOGGER = logging.getLogger(__name__)


def initial_config_value(hass: HomeAssistant, entry_id: str, key: str) -> Any | None:
    """Liest einen optionalen Vorgabewert aus den Config-Entry-Daten (siehe
    z. B. CONF_TIMED_CHARGE_START in const.py, abgefragt im zweiten Schritt
    der Ersteinrichtung in config_flow.py).

    Nur als letzte Fallback-Stufe gedacht, NACHDEM eine RestoreEntity bereits
    erfolglos nach einem zuvor gespeicherten echten Zustand gefragt wurde
    (siehe z. B. SaxPowerTimedChargeStartTime.async_added_to_hass) - wirkt
    sich dadurch effektiv nur auf den allerersten Start eines neu
    eingerichteten Eintrags aus. Gibt None zurück, wenn kein Config Entry
    gefunden wird oder der Schlüssel fehlt (z. B. bei über Reconfigure
    aktualisierten oder vor Einführung dieses Schritts angelegten Einträgen).
    """
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None:
        return None
    return entry.data.get(key)


# -- Einmalige Migration alter RestoreEntity-Zustände ------------------------
# Siehe anforderung.yaml, REQ-CONTROL-CONFIG-BOOTSTRAP. Diese drei Parser
# geben None zurück, sobald ein gespeicherter Zustand fachlich nicht
# verwertbar ist - insbesondere für "unknown"/"unavailable", die entstehen,
# wenn Home Assistant beendet wurde, während die Entity keinen Wert hatte.
# Ein solcher Zustand darf beim Migrieren weder als ausdrückliches "Aus"
# noch als Vorgabewert gelten: Der Aufrufer ruft dann gar keinen Setter auf
# und lässt die Einstellung auf ihrem Ausgangswert stehen, statt einen
# Ratewert zu übernehmen und anschließend dauerhaft zu speichern.


def restorable_bool(last_state: State) -> bool | None:
    """Migrierbarer Schalterzustand, sonst None."""
    if last_state.state == STATE_ON:
        return True
    if last_state.state == STATE_OFF:
        return False
    return None


def restorable_number(last_state: State) -> float | None:
    """Migrierbarer Zahlenwert, sonst None."""
    try:
        value = float(last_state.state)
    except TypeError, ValueError:
        return None
    return value if math.isfinite(value) else None


def restorable_time(last_state: State) -> dt_time | None:
    """Migrierbare Uhrzeit, sonst None."""
    return dt_util.parse_time(last_state.state)


def log_unmigratable_state(entity_id: str, last_state: State) -> None:
    """Meldet einen Altzustand, der nicht als Wert übernommen werden darf."""
    _LOGGER.warning(
        "Gespeicherter Zustand %r von %s ist nicht migrierbar; die Einstellung "
        "bleibt auf ihrem Ausgangswert, statt ihn als ausdrücklichen Wert zu "
        "übernehmen",
        last_state.state,
        entity_id,
    )


class SaxPowerEntity(CoordinatorEntity[SaxPowerCoordinator]):
    """Base entity providing shared device info for all SAX Power entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SaxPowerCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="SAX Power Home",
            manufacturer="SAX Power",
            model="Home (Plus)",
        )

    def _assign_ids(self, platform_domain: str, suffix: str) -> None:
        """Setzt unique_id und entity_id anhand eines stabilen Suffixes.

        `entity_id` wird hier bewusst explizit vorgegeben, statt es Home
        Assistant über has_entity_name automatisch aus Gerätename +
        Entity-Name ableiten zu lassen (siehe anforderung.yaml,
        REQ-STABLE-ENTITY-ID): Bietet Home Assistant nach der
        Ersteinrichtung an, das Gerät umzubenennen/einem Bereich
        zuzuordnen, und aktiviert der Anwender dabei "Entity-IDs
        aktualisieren", würde sich sonst auch die entity_id ändern - das
        mitgelieferte Dashboard (dashboard.py) referenziert zu diesem
        Zeitpunkt aber bereits die ursprüngliche entity_id fest und würde
        die Entity nicht mehr finden. Ein expliziter `self.entity_id` wird
        von Home Assistant unverändert als Vorschlag übernommen und bleibt
        über spätere Umbenennungen des Geräts hinweg stabil.
        """
        self._attr_unique_id = f"{self._entry_id}_{suffix}"
        self.entity_id = f"{platform_domain}.sax_power_{suffix}"


class SaxPowerConfigEntity(SaxPowerEntity):
    """Basisklasse für rein softwareseitige Konfigurations-Entities.

    Max-SOC, Zeitfenster, Monate, Automatik-Schalter, Ladestrategie und
    Preisparameter stammen aus keinem Register - sie werden vom Coordinator
    gehalten und über infrastructure/control_store.py persistiert (siehe
    anforderung.yaml, REQ-CONTROL-CONFIG-BOOTSTRAP). Deshalb dürfen sie
    NICHT an CoordinatorEntity.available (= coordinator.last_update_success)
    hängen: ein reiner Modbus-Ausfall macht die gespeicherten Werte weder
    unbekannt noch ungültig, würde die Entities aber sichtbar
    "nicht verfügbar" schalten - und einen Restore-State-Dump in genau
    diesem Zustand hinterlassen.
    """

    @property
    def available(self) -> bool:
        return True
