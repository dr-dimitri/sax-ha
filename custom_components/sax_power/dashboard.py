"""Mitgeliefertes Lovelace-Dashboard für SAX Power (siehe anforderung.yaml,
REQ-BUNDLED-DASHBOARD).

Baut ein sechsteiliges Storage-Dashboard ("Allgemeine Informationen",
"Ladeautomatik", "Netzdienliches Laden", "Dynamisches Laden",
"Wirtschaftlichkeit", siehe REQ-ECONOMICS-DASHBOARD, und "Ersparnis",
siehe REQ-ECONOMICS-SAVINGS-DASHBOARD) und legt es -
wenn der Anwender das in der Ersteinrichtung ausgewählt hat (config_flow.py,
CONF_CREATE_DASHBOARD) - direkt in Home Assistants Lovelace-Speicher an,
damit es sofort ohne Neustart in der Sidebar erscheint.

Home Assistant selbst nutzt für sein eigenes Onboarding-Kartendashboard
denselben Weg (homeassistant.components.lovelace._create_map_dashboard):
über die dortige, für das laufende Setup live verdrahtete
DashboardsCollection-Instanz anlegen lassen - die Änderung landet dadurch
automatisch sowohl im Speicher als auch sofort sichtbar in der Sidebar,
weil ein Listener auf genau dieser Instanz lauscht. Diese Instanz ist von
außerhalb von homeassistant.components.lovelace nicht erreichbar, deshalb
hier nachgebaut aus den beiden dafür vorgesehenen (aber sonst nur intern
verdrahteten) Bausteinen: eine neue DashboardsCollection (liest/schreibt
denselben Speicher, persistiert den Eintrag korrekt) plus eine manuell
angelegte LovelaceStorage-Instanz + frontend.async_register_built_in_panel
(sorgt für die sofortige Sichtbarkeit, die der fehlende Listener sonst
übernehmen würde). Rein optionale Komfortfunktion - siehe
async_create_dashboard für die Fehlerbehandlung.

Kartenbeschriftungen verwenden bewusst nicht den vollen, geräteweiten
Anzeigenamen ("SAX Power Home <Entity>", entsteht durch
SaxPowerEntity._attr_has_entity_name), sondern nur den reinen
Entity-Namen aus der Übersetzung (component.sax_power.entity.<domain>.
<translation_key>.name) - andernfalls würde sich der Gerätename in jeder
einzelnen Kartenzeile wiederholen. Dafür werden dieselben Übersetzungen
geladen, die auch die Entity Registry selbst verwendet, statt den Text
hier zusätzlich fest zu hinterlegen (bleibt so für andere Sprachen als
Deutsch korrekt, siehe translations/en.json).
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import frontend
from homeassistant.components.lovelace import dashboard as lovelace_dashboard
from homeassistant.components.lovelace.const import CONF_ICON as LL_CONF_ICON
from homeassistant.components.lovelace.const import (
    CONF_REQUIRE_ADMIN,
    CONF_SHOW_IN_SIDEBAR,
    CONF_URL_PATH,
    DEFAULT_ICON,
    LOVELACE_DATA,
    MODE_STORAGE,
)
from homeassistant.components.lovelace.const import CONF_TITLE as LL_CONF_TITLE
from homeassistant.components.lovelace.const import DOMAIN as LOVELACE_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers import translation

from .const import (
    CONF_DASHBOARD_UPDATE_DISMISSED,
    DOMAIN,
    ISSUE_DASHBOARD_OUTDATED,
)

_LOGGER = logging.getLogger(__name__)

#: Jinja-Vorlage der Tarifplan-Karte (_tariff_plan_card). Der Platzhalter
#: wird per str.replace ersetzt, nicht per str.format: Die Vorlage ist voll
#: von geschweiften Klammern, die Jinja gehören.
#:
#: Die Vorlage entscheidet SELBST, ob die Karte etwas anzeigt: Bei jeder
#: anderen Tarifart als time_of_use rendert sie zu einer leeren
#: Zeichenkette, und `show_empty: false` blendet die Karte dann aus. Eine
#: Core-"conditional"-Karte kann das hier nicht leisten - ihre Bedingungen
#: prüfen ausschließlich den ZUSTAND einer Entity. Ein zusätzlich
#: angegebenes `attribute` ist dort schlicht kein unterstützter Schlüssel:
#: Es wird ignoriert, der Vergleich läuft weiter gegen den Zustand, und die
#: Karte war dadurch dauerhaft unsichtbar (Anwenderbericht zu #139).
#: Deshalb steht auch die Überschrift im Inhalt statt in `title` - ein
#: gesetzter Kartentitel bliebe sonst als leerer Kasten stehen.
#:
#: Die Zeilenumbrüche innerhalb der {{ ... }}-Ausdrücke halten die
#: Quelltextzeilen unter der Zeilenlänge, ohne die Ausgabe zu verändern -
#: eine Markdown-Tabellenzeile muss eine einzige Ausgabezeile bleiben.
#:
#: `unavailable_reason` entscheidet, ob überhaupt eine Zeile als "jetzt"
#: geltend markiert wird: Gilt gerade kein Preis, ist auch `active_window`
#: None - ohne diese zusätzliche Abfrage träfe die Markierung dann
#: fälschlich den Grundpreis.
_PRICE_ENTITY_PLACEHOLDER = "__PRICE_ENTITY__"
_TARIFF_PLAN_TEMPLATE = """\
{%- set entity = '__PRICE_ENTITY__' %}
{%- if state_attr(entity, 'tariff_type') == 'time_of_use' %}
{%- set windows = state_attr(entity, 'windows') or [] %}
{%- set active = state_attr(entity, 'active_window') %}
{%- set base = state_attr(entity, 'base_price_eur_kwh') %}
{%- set change = state_attr(entity, 'next_price_change_at') %}
{%- set reason = state_attr(entity, 'unavailable_reason') %}
### Tarifplan (tageszeitabhängig)

| | Von | Bis | Arbeitspreis |
|---|---|---|---|
{%- for window in windows %}
{%- set current = active is not none
    and window.start == active.start
    and window.end == active.end %}
| {{ '**jetzt**' if current else '' }} | {{ window.start[:5] }} | {{
    window.end[:5] }} | {{ '%.4f'|format(window.price_eur_kwh) }} EUR/kWh |
{%- endfor %}
| {{ '**jetzt**' if reason is none and active is none else '' }} | – | – | {{
    '%.4f'|format(base) if base is not none else '?' }} EUR/kWh (Grundpreis) |
{% if reason is not none %}
Derzeit gilt kein Preis ({{ reason }}) – bitte die Tarifkonfiguration prüfen.
{%- elif change is not none %}
Nächster Preiswechsel: {{ as_timestamp(change) | timestamp_custom('%H:%M') }} Uhr
{%- endif %}
{%- endif %}
"""

_SAVINGS_STATUS_ENTITY_PLACEHOLDER = "__SAVINGS_STATUS_ENTITY__"
_SAVINGS_STATUS_TEMPLATE = """\
{%- set status_entity = __SAVINGS_STATUS_ENTITY__ %}
{%- set status = states(status_entity)
    if status_entity is not none else 'unknown' %}
{%- set details = '[Technische Details](/sax-power/wirtschaftlichkeit)' %}
{%- if status == 'active' %}
{%- elif status == 'disabled' %}
{{- 'Die Wirtschaftlichkeitsberechnung ist deaktiviert. Bitte unter '
    ~ '„Geräte & Dienste → SAX Power Home → Konfigurieren → '
    ~ 'Wirtschaftlichkeit“ konfigurieren.' ~ '\n\n' ~ details }}
{%- elif status == 'waiting_for_initial_state' %}
{{- 'Die Wirtschaftlichkeitsberechnung wartet auf Speicherkapazität '
    ~ 'und Ladezustand.' ~ '\n\n' ~ details }}
{%- elif status == 'price_unavailable' %}
{{- 'Der Strompreis ist derzeit nicht verfügbar. Aktuelle Zeitraumwerte '
    ~ 'können unvollständig sein.' ~ '\n\n' ~ details }}
{%- elif status == 'origin_unavailable' %}
{{- 'Die Herkunft der Ladeenergie ist derzeit nicht bestimmbar.'
    ~ '\n\n' ~ details }}
{%- elif status == 'partial_price_coverage' %}
{{- 'Für einen Teil der Energie fehlte heute ein Preis. Das Ergebnis kann '
    ~ 'unvollständig sein.' ~ '\n\n' ~ details }}
{%- elif status == 'storage_error' %}
{{- 'Die Wirtschaftlichkeitsbilanz ist wegen eines Speicherfehlers '
    ~ 'angehalten. Bitte die **Home-Assistant-Reparaturen** prüfen.'
    ~ '\n\n' ~ details }}
{%- else %}
{{- 'Die Wirtschaftlichkeitsdaten sind momentan nicht verfügbar.'
    ~ '\n\n' ~ details }}
{%- endif %}
"""

# Dauerhaft gleichbleibender Erklärungstext des Ersparnis-Tabs. Das native
# HTML-Element details ist in der Allowlist des zu Home Assistant 2026.8.2
# gehörenden Markdown-Renderers enthalten. Ohne open-Attribut beginnt es
# bewusst geschlossen; der zustandsabhängige Anfangsbestand bleibt innerhalb
# des Elements abrufbar (REQ-ECONOMICS-SAVINGS-DASHBOARD).
_SAVINGS_INVENTORY_ENTITY_PLACEHOLDER = "__SAVINGS_INVENTORY_ENTITY__"
_SAVINGS_EXPLANATION_TEMPLATE = """\
<details>
<summary><strong>Hinweise zur Berechnung und Datenbasis</strong></summary>
<p><strong>Netto-Ersparnis:</strong> Grundlage sind vermiedene
Netzbezugskosten minus Netzladekosten und entgangene Einspeisevergütung.
Angezeigt wird ein gespeicherter, nichtnegativer Höchststand. Spätere Kosten
verringern eine bereits festgehaltene Ersparnis nicht.</p>
<p><strong>Kalenderwerte:</strong> Sie stammen aus der
Recorder-Langzeitstatistik der Netto-Ersparnis. Bei aktualisierten
Installationen kann diese Aufzeichnung jünger als der angezeigte Bilanzbeginn
sein.</p>
<p><strong>Freier Zeitraum:</strong> Es fließen nur Daten seit Beginn dieser
Recorder-Aufzeichnung ein. Eine frühere Auswahl erfindet keine Werte. Fehlt
Recorder-Historie oder ist die Ergebnis-Entity vom Recorder ausgeschlossen,
bleiben Wert und Diagramm unbekannt beziehungsweise leer. Schneidet die
Auswahl einen manuellen Neustart der Wirtschaftlichkeitsbilanz, kann der
Recorder die positiven Zuwächse vor und nach dem Neustart zusammenfassen.</p>
{%- set inventory_entity = __SAVINGS_INVENTORY_ENTITY__ %}
{%- set inventory = states(inventory_entity)
    if inventory_entity is not none else 'unknown' %}
{%- set unit = state_attr(inventory_entity, 'unit_of_measurement')
    if inventory_entity is not none else none %}
{%- if is_number(inventory) and inventory | float > 0 %}
{%- set formatted = ('%.3f' | format(inventory | float)) | replace('.', ',') %}
{%- set display = formatted ~ ' ' ~ unit if unit else formatted %}
<p>Beim Start der Bilanz waren bereits <strong>{{ display }}</strong> im
Speicher. Für diese Energie sind Herkunft und Preis unbekannt. Ihre Entladung
wird deshalb korrekt mit <strong>0 €</strong> bewertet. Sobald dieser
Anfangsbestand abgebaut ist, kann weitere bepreiste Entladung in die
Netto-Ersparnis eingehen. Das ist kein Messfehler.</p>
{%- endif %}
</details>
"""

DASHBOARD_URL_PATH = "sax-power"
DASHBOARD_TITLE = "SAX Power"
DASHBOARD_ICON = "mdi:battery-charging-100"
_SAVINGS_COLLECTION_KEY = "energy_sax_power_savings"

# Nur für die wenigen Fälle nötig, in denen der unique_id-Suffix (stabil,
# darf sich nicht mehr ändern) vom translation_key der Entity abweicht.
_TRANSLATION_KEY_OVERRIDES: dict[tuple[str, str], str] = {
    ("switch", "storage_switch"): "storage",
}

# Diese Entity aktualisiert ihren eigenen Namen täglich um das Datum. Ein hier
# gespeicherter Zeilenname würde dagegen bis zur Neuerstellung des Dashboards
# unverändert bleiben (siehe REQ-BUNDLED-DASHBOARD).
_ENTITY_NAME_FROM_STATE: set[tuple[str, str]] = {
    ("sensor", "grid_serving_forecast"),
}


def _entity_id(hass: HomeAssistant, entity_domain: str, unique_id: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(entity_domain, DOMAIN, unique_id)


def _entity_name(
    translations: dict[str, str], entity_domain: str, suffix: str
) -> str | None:
    translation_key = _TRANSLATION_KEY_OVERRIDES.get((entity_domain, suffix), suffix)
    return translations.get(
        f"component.{DOMAIN}.entity.{entity_domain}.{translation_key}.name"
    )


def _entities_card(
    hass: HomeAssistant,
    entry_id: str,
    title: str,
    entities: list[tuple[str, str]],
    translations: dict[str, str],
) -> dict[str, Any] | None:
    """Baut eine "entities"-Karte aus (Entity-Domain, unique_id-Suffix)-Paaren.

    Entities, die (noch) nicht in der Entity Registry stehen, werden
    stillschweigend übersprungen; eine Karte ohne verbliebene Entities wird
    komplett weggelassen statt leer angezeigt zu werden. Jede Zeile bekommt
    den reinen (geräteprefix-freien) Namen als Beschriftung, siehe
    Moduldocstring.
    """
    resolved: list[dict[str, str] | str] = []
    for entity_domain, suffix in entities:
        entity_id = _entity_id(hass, entity_domain, f"{entry_id}_{suffix}")
        if entity_id is None:
            continue
        if (entity_domain, suffix) in _ENTITY_NAME_FROM_STATE:
            resolved.append({"entity": entity_id})
            continue
        name = _entity_name(translations, entity_domain, suffix)
        resolved.append({"entity": entity_id, "name": name} if name else entity_id)
    if not resolved:
        return None
    return {
        "type": "entities",
        "title": title,
        "state_color": True,
        "entities": resolved,
    }


def _tile_card(
    hass: HomeAssistant,
    entry_id: str,
    entity_domain: str,
    suffix: str,
    translations: dict[str, str],
) -> dict[str, Any] | None:
    """Baut eine "tile"-Karte für eine einzelne Entity - moderner, größerer
    Status/Umschalter für die wichtigsten Ein/Aus-Größen, z. B. auf einen
    Blick sichtbar statt in einer Liste."""
    entity_id = _entity_id(hass, entity_domain, f"{entry_id}_{suffix}")
    if entity_id is None:
        return None
    card: dict[str, Any] = {"type": "tile", "entity": entity_id}
    name = _entity_name(translations, entity_domain, suffix)
    if name:
        card["name"] = name
    return card


def _gauge_card(
    hass: HomeAssistant,
    entry_id: str,
    entity_domain: str,
    suffix: str,
    translations: dict[str, str],
    *,
    min_value: float,
    max_value: float,
    segments: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Baut eine "gauge"-Karte statt einer Listenzeile - macht kritische
    Bereiche (z. B. Speicher fast leer, Zelltemperatur zu niedrig/hoch) auf
    einen Blick sichtbar. Immer über `segments` (Liste beliebiger, auch
    nicht monoton steigender Farbbereiche) statt über das alternative
    `severity`-Mapping (feste Schlüssel green/yellow/red): Home Assistants
    Gauge-Karte färbt `severity`-Farben über die Theme-Variablen
    (--success-/--warning-/--error-color), `segments`-Farben dagegen als
    wörtliche CSS-Farbnamen - dieselbe Zeichenkette "red"/"green" sieht
    dadurch in den beiden Modi unterschiedlich aus. Ausschließlich
    `segments` zu verwenden hält alle Gauge-Karten des Dashboards farblich
    konsistent. Immer im Nadel-Stil (needle), passend zum modernisierten
    Dashboard."""
    entity_id = _entity_id(hass, entity_domain, f"{entry_id}_{suffix}")
    if entity_id is None:
        return None
    return {
        "type": "gauge",
        "entity": entity_id,
        "name": _entity_name(translations, entity_domain, suffix),
        "min": min_value,
        "max": max_value,
        "needle": True,
        "segments": segments,
    }


def _resolved_row(
    hass: HomeAssistant,
    entry_id: str,
    entity_domain: str,
    suffix: str,
    translations: dict[str, str],
) -> tuple[str | None, dict[str, str] | str | None]:
    """Löst eine einzelne (Entity-Domain, unique_id-Suffix)-Zeile auf und
    liefert sowohl die rohe Entity-ID (für Attribut-Zeilen, siehe
    _attribute_row) als auch die fertige entities-Kartenzeile - oder
    (None, None), wenn die Entity (noch) nicht registriert ist."""
    entity_id = _entity_id(hass, entity_domain, f"{entry_id}_{suffix}")
    if entity_id is None:
        return None, None
    if (entity_domain, suffix) in _ENTITY_NAME_FROM_STATE:
        return entity_id, {"entity": entity_id}
    name = _entity_name(translations, entity_domain, suffix)
    return entity_id, ({"entity": entity_id, "name": name} if name else entity_id)


def _attribute_row(
    entity_id: str | None,
    attribute: str,
    name: str,
    *,
    suffix: str | None = None,
) -> dict[str, Any] | None:
    """Eine "attribute"-Zeile einer entities-Karte - zeigt ein Attribut der
    übergebenen Entity wie einen eigenen Sensor an (REQ-ECONOMICS-
    DASHBOARD, für Preisabdeckungen/Bilanzbeginn, die keinen eigenen
    Sensor haben, siehe REQ-ECONOMICS-OBSERVABILITY)."""
    if entity_id is None:
        return None
    row = {
        "type": "attribute",
        "entity": entity_id,
        "attribute": attribute,
        "name": name,
    }
    if suffix is not None:
        row["suffix"] = suffix
    return row


def _statistics_graph_card(
    hass: HomeAssistant,
    entry_id: str,
    title: str,
    entities: list[tuple[str, str]],
) -> dict[str, Any] | None:
    """Core-"statistics-graph"-Karte als Balkendiagramm mit Tagesänderung
    (REQ-ECONOMICS-DASHBOARD) - keine Custom-Card-Abhängigkeit. `change`
    ist für `state_class: total`-Sensoren (wie die hier verwendeten
    Geldsensoren) eine unterstützte Langzeitstatistik-Kennzahl; sollte
    eine künftig getestete HA-Version das nicht mehr unterstützen, sind
    stattdessen die dedizierten Tages-Sensoren aus REQ-ECONOMICS-
    AMORTIZATION zu verwenden statt auf einen nicht unterstützten
    Kartentyp oder eine private Statistik-API auszuweichen."""
    resolved = [
        entity_id
        for entity_domain, suffix in entities
        if (entity_id := _entity_id(hass, entity_domain, f"{entry_id}_{suffix}"))
        is not None
    ]
    if not resolved:
        return None
    return {
        "type": "statistics-graph",
        "title": title,
        "entities": resolved,
        "stat_types": ["change"],
        "chart_type": "bar",
        "period": "day",
        "days_to_show": 30,
    }


def _calendar_statistic_card(
    entity_id: str, name: str, calendar_period: str
) -> dict[str, Any]:
    """Core-Statistikkarte für eine lokale Kalenderperiode.

    Die Karte überlässt die Auswertung vollständig Home Assistants
    Recorder-Langzeitstatistik; sie berechnet weder Zeitgrenzen noch Werte
    selbst (REQ-ECONOMICS-SAVINGS-DASHBOARD).
    """
    return {
        "type": "statistic",
        "entity": entity_id,
        "name": name,
        "stat_type": "change",
        "period": {"calendar": {"period": calendar_period}},
    }


def _grid_card(cards: list[dict[str, Any] | None]) -> dict[str, Any] | None:
    """Reiht mehrere Karten nebeneinander an - fehlende Entities werden
    wie bei _entities_card stillschweigend ausgelassen; bleibt am Ende
    nichts übrig, wird die ganze Zeile weggelassen."""
    resolved = [card for card in cards if card is not None]
    if not resolved:
        return None
    return {"type": "grid", "columns": 2, "square": False, "cards": resolved}


def _tariff_plan_card(hass: HomeAssistant, entry_id: str) -> dict[str, Any] | None:
    """Der tageszeitabhängige Tarifplan als Tabelle (REQ-ECONOMICS-DASHBOARD).

    Gespeist wird die Karte ausschließlich aus den Attributen des
    Netzbezugspreis-Sensors (`windows`, `active_window`,
    `base_price_eur_kwh`, `next_price_change_at`) - sie enthält damit keine
    eigene Kopie der Konfiguration und kann nach einer Options-Änderung
    nicht veralten. Ohne registrierten Preis-Sensor entfällt sie ganz.
    """
    price_entity_id = _entity_id(
        hass, "sensor", f"{entry_id}_economics_current_import_price"
    )
    if price_entity_id is None:
        return None
    return {
        "type": "markdown",
        # Ohne show_empty bliebe bei jeder anderen Tarifart ein leerer
        # Kasten stehen (Vorgabe des Kartentyps ist True).
        "show_empty": False,
        "content": _TARIFF_PLAN_TEMPLATE.replace(
            _PRICE_ENTITY_PLACEHOLDER, price_entity_id
        ),
    }


def _stack_card(cards: list[dict[str, Any] | None]) -> dict[str, Any] | None:
    """Stapelt mehrere Karten vertikal zu einer Core-"vertical-stack"-Karte
    - anders als _grid_card (nebeneinander, für Tile-Karten) hier für eine
    feste Lese-Reihenfolge innerhalb eines fachlich zusammengehörigen
    Blocks (REQ-ECONOMICS-DASHBOARD, Karte "Investition und
    Amortisation": ROI-Zeile, Fortschritts-Gauge, restliche Zeilen - eine
    "entities"-Karte kann selbst keine Gauge einbetten). Fehlende Karten
    werden wie bei _grid_card stillschweigend ausgelassen; bleibt am Ende
    nichts übrig, wird die ganze Karte weggelassen."""
    resolved = [card for card in cards if card is not None]
    if not resolved:
        return None
    return {"type": "vertical-stack", "cards": resolved}


def _savings_free_period_block(entity_id: str) -> dict[str, Any]:
    """Core-Karten für eine gemeinsame freie Energy-Datumswahl.

    Alle drei auswertenden Karten teilen denselben expliziten Collection-Key;
    Home Assistant bestimmt Zeitraum und Diagrammauflösung vollständig selbst
    (REQ-ECONOMICS-SAVINGS-DASHBOARD).
    """
    return {
        "type": "vertical-stack",
        "cards": [
            {
                "type": "markdown",
                "content": "### Freier Zeitraum",
            },
            {
                "type": "energy-date-selection",
                "collection_key": _SAVINGS_COLLECTION_KEY,
                "disable_compare": True,
            },
            {
                "type": "statistic",
                "entity": entity_id,
                "name": "Netto-Ersparnis im gewählten Zeitraum",
                "period": "energy_date_selection",
                "stat_type": "change",
                "collection_key": _SAVINGS_COLLECTION_KEY,
            },
            {
                "type": "statistics-graph",
                "title": "Verlauf im gewählten Zeitraum",
                "entities": [entity_id],
                "stat_types": ["change"],
                "chart_type": "bar",
                "energy_date_selection": True,
                "collection_key": _SAVINGS_COLLECTION_KEY,
            },
        ],
    }


def _jinja_entity(entity_id: str | None) -> str:
    """Gibt eine sichere Jinja-Konstante für eine aufgelöste Entity zurück."""
    return "none" if entity_id is None else repr(entity_id)


def _savings_status_card(status_entity_id: str | None) -> dict[str, Any]:
    """Blendet den gesunden Wirtschaftlichkeitsstatus vollständig aus."""
    return {
        "type": "markdown",
        "show_empty": False,
        "content": _SAVINGS_STATUS_TEMPLATE.replace(
            _SAVINGS_STATUS_ENTITY_PLACEHOLDER, _jinja_entity(status_entity_id)
        ),
    }


def _savings_explanation_card(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Bündelt statische Hinweise und den optionalen Anfangsbestand."""
    inventory_entity_id = _entity_id(
        hass, "sensor", f"{entry_id}_economics_unvalued_inventory"
    )
    content = _SAVINGS_EXPLANATION_TEMPLATE.replace(
        _SAVINGS_INVENTORY_ENTITY_PLACEHOLDER,
        _jinja_entity(inventory_entity_id),
    )
    return {
        "type": "markdown",
        "content": content,
    }


def _savings_payback_block(
    hass: HomeAssistant,
    entry_id: str,
    translations: dict[str, str],
    savings_result_entity_id: str | None,
    status_entity_id: str | None,
) -> dict[str, Any] | None:
    """Kompakte Darstellung des aktuellen Amortisationsstands."""
    configured_entity_id = _entity_id(
        hass, "binary_sensor", f"{entry_id}_economics_investment_configured"
    )
    if configured_entity_id is None:
        return None

    roi_entity_id = _entity_id(hass, "sensor", f"{entry_id}_economics_roi")
    progress_gauge = _gauge_card(
        hass,
        entry_id,
        "sensor",
        "economics_amortization_progress",
        translations,
        min_value=0,
        max_value=100,
        segments=[{"from": 0, "color": "blue"}],
    )

    detail_rows: list[dict[str, Any] | str] = []
    for suffix in ("economics_remaining_to_payback",):
        _, row = _resolved_row(hass, entry_id, "sensor", suffix, translations)
        if row is not None:
            detail_rows.append(row)
    if savings_result_entity_id is not None:
        detail_rows.append(
            {"entity": savings_result_entity_id, "name": "Netto-Ersparnis"}
        )
    savings_started_at_row = _attribute_row(
        status_entity_id, "economics_started_at", "Bilanzbeginn"
    )
    if savings_started_at_row is not None:
        detail_rows.append(savings_started_at_row)
    prior_row = _attribute_row(
        roi_entity_id,
        "prior_result_eur",
        "Bereits vor Bilanzbeginn berücksichtigt",
        suffix="€",
    )
    if prior_row is not None:
        detail_rows.append(prior_row)
    details_card = (
        {
            "type": "entities",
            "state_color": True,
            "entities": detail_rows,
        }
        if detail_rows
        else None
    )

    configured_stack = _stack_card([progress_gauge, details_card])
    assert configured_stack is not None
    return {
        "type": "vertical-stack",
        "cards": [
            {
                "type": "markdown",
                "content": "### Amortisation",
            },
            {
                "type": "conditional",
                "conditions": [{"entity": configured_entity_id, "state": "off"}],
                "card": {
                    "type": "markdown",
                    "content": (
                        "Für die Amortisationswerte bitte die "
                        "Investitionskosten unter „Geräte & Dienste → SAX "
                        "Power Home → Konfigurieren → Wirtschaftlichkeit“ "
                        "hinterlegen."
                    ),
                },
            },
            {
                "type": "conditional",
                "conditions": [{"entity": configured_entity_id, "state": "on"}],
                "card": configured_stack,
            },
        ],
    }


def _view(
    title: str, path: str, icon: str, cards: list[dict[str, Any] | None]
) -> dict[str, Any]:
    return {
        "title": title,
        "path": path,
        "icon": icon,
        "cards": [card for card in cards if card is not None],
    }


async def async_build_dashboard_config(
    hass: HomeAssistant, entry_id: str
) -> dict[str, Any]:
    """Baut die komplette Lovelace-Konfiguration (sechs Tabs) für einen Entry."""
    translations = await translation.async_get_translations(
        hass, hass.config.language, "entity", integrations=[DOMAIN]
    )

    general_view = _view(
        "Allgemeine Informationen",
        "allgemein",
        "mdi:information-outline",
        [
            _grid_card(
                [
                    _gauge_card(
                        hass,
                        entry_id,
                        "sensor",
                        "soc",
                        translations,
                        min_value=0,
                        max_value=100,
                        # Dieselben Farben wie die Zelltemperatur-Gauge
                        # unten (rot/grün) - siehe _gauge_card-Docstring.
                        segments=[
                            {"from": 0, "color": "red"},
                            {"from": 20, "color": "yellow"},
                            {"from": 50, "color": "green"},
                        ],
                    ),
                    _gauge_card(
                        hass,
                        entry_id,
                        "sensor",
                        "storage_max_cell_temp",
                        translations,
                        min_value=0,
                        max_value=40,
                        # 0-5 °C zu kalt, 5-32 °C normaler Betriebsbereich,
                        # 32-40 °C zu heiß - kein einfaches "je höher desto
                        # kritischer" wie beim SOC.
                        segments=[
                            {"from": 0, "color": "red"},
                            {"from": 5, "color": "green"},
                            {"from": 32, "color": "red"},
                        ],
                    ),
                ]
            ),
            _tile_card(hass, entry_id, "switch", "storage_switch", translations),
            _entities_card(
                hass,
                entry_id,
                "Leistung",
                [
                    ("number", "max_soc"),
                    ("sensor", "charge_power"),
                    ("sensor", "discharge_power"),
                    ("sensor", "smartmeter_power"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Energie",
                [
                    ("sensor", "energy_charged"),
                    ("sensor", "energy_discharged"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Gerät",
                [
                    ("sensor", "sun_version_master"),
                    ("sensor", "sun_version_gateway"),
                    ("sensor", "sun_serial_number"),
                    ("sensor", "storage_event_text"),
                    ("sensor", "ic_control_mode_text"),
                    ("binary_sensor", "cell_calibration_active"),
                    ("sensor", "next_cell_calibration"),
                ],
                translations,
            ),
        ],
    )

    charging_view = _view(
        "Ladeautomatik",
        "ladeautomatik",
        "mdi:transmission-tower",
        [
            _tile_card(hass, entry_id, "switch", "timed_charge_enabled", translations),
            _entities_card(
                hass,
                entry_id,
                "Zeitfenster",
                [
                    ("time", "timed_charge_start"),
                    ("time", "timed_charge_end"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Einstellungen",
                [
                    ("number", "timed_charge_min_soc"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Aktive Monate",
                [("switch", f"timed_charge_month_{month}") for month in range(1, 13)],
                translations,
            ),
        ],
    )

    grid_serving_view = _view(
        "Netzdienliches Laden",
        "netzdienliches-laden",
        "mdi:transmission-tower-export",
        [
            _tile_card(hass, entry_id, "switch", "grid_serving_enabled", translations),
            _entities_card(
                hass,
                entry_id,
                "Ladepause",
                [
                    ("time", "grid_serving_start"),
                    ("time", "grid_serving_end"),
                    ("sensor", "grid_serving_forecast"),
                    ("number", "grid_serving_forecast_threshold"),
                    ("sensor", "grid_serving_pause_status"),
                ],
                translations,
            ),
            _entities_card(
                hass,
                entry_id,
                "Aktive Monate",
                [("switch", f"grid_serving_month_{month}") for month in range(1, 13)],
                translations,
            ),
        ],
    )

    price_view = _view(
        "Dynamisches Laden",
        "dynamisches-laden",
        "mdi:chart-line",
        [
            _tile_card(hass, entry_id, "switch", "price_charge_enabled", translations),
            _entities_card(
                hass,
                entry_id,
                "Preisoptimiertes Laden",
                [
                    ("select", "price_charge_strategy"),
                    ("number", "price_charge_max_price"),
                    ("number", "price_charge_neutral_price"),
                    ("number", "price_charge_hours"),
                    ("number", "max_soc"),
                    ("sensor", "price_charge_active_text"),
                    ("sensor", "price_charge_status_text"),
                    ("sensor", "grid_serving_forecast"),
                    ("sensor", "price_charge_next_start"),
                    ("sensor", "price_charge_current_price"),
                ],
                translations,
            ),
        ],
    )

    status_entity_id, status_row = _resolved_row(
        hass, entry_id, "sensor", "economics_status", translations
    )
    status_rows: list[dict[str, Any] | str] = [status_row] if status_row else []
    for entity_domain, suffix in (
        ("sensor", "economics_current_import_price"),
        ("sensor", "economics_feed_in_price"),
    ):
        _, row = _resolved_row(hass, entry_id, entity_domain, suffix, translations)
        if row is not None:
            status_rows.append(row)
    for attribute, label in (
        # Bewusst die Tageswerte: sie bestimmen den Zustand des
        # Status-Sensors direkt darüber (REQ-ECONOMICS-OBSERVABILITY,
        # Issue #134) - die kumulierten Lifetime-Quoten bleiben als
        # Attribute desselben Sensors erhalten.
        ("charge_price_coverage_percent_today", "Preisabdeckung Ladung (heute)"),
        (
            "discharge_price_coverage_percent_today",
            "Preisabdeckung Entladung (heute)",
        ),
        ("economics_started_at", "Beginn der Bilanz"),
    ):
        row = _attribute_row(status_entity_id, attribute, label)
        if row is not None:
            status_rows.append(row)
    status_card = (
        {
            "type": "entities",
            "title": "Status und Preise",
            "state_color": True,
            "entities": status_rows,
        }
        if status_rows
        else None
    )

    pv_entity_id, pv_row = _resolved_row(
        hass, entry_id, "sensor", "energy_charged_from_pv", translations
    )
    origin_rows: list[dict[str, Any] | str] = [pv_row] if pv_row else []
    for entity_domain, suffix in (
        ("sensor", "energy_charged_from_grid"),
        ("sensor", "energy_charged"),
        ("sensor", "energy_discharged"),
    ):
        _, row = _resolved_row(hass, entry_id, entity_domain, suffix, translations)
        if row is not None:
            origin_rows.append(row)
    # Die drei Zähler dieser Karte und die Geldbilanz eine Karte tiefer
    # beginnen zu verschiedenen Zeitpunkten (REQ-ENERGY-ORIGIN): Der
    # Gesamtzähler läuft seit der Installation, die Herkunft seit
    # _bootstrap_energy_origin, die Bilanz erst seit dem ersten
    # vollständigen Tarif. Ohne beide Zeitpunkte nebeneinander liest sich
    # die Differenz wie ein Rechenfehler (Anwenderbericht: 2,44 kWh
    # PV-Ladung neben 0,0084 EUR PV-Opportunitätskosten - beide Werte
    # korrekt, nur verschieden alt).
    origin_start_row = _attribute_row(
        pv_entity_id, "origin_accounting_started_at", "Beginn der Herkunftszählung"
    )
    if origin_start_row is not None:
        origin_rows.append(origin_start_row)
    origin_card = (
        {
            "type": "entities",
            "title": "Herkunft der Ladeenergie",
            "state_color": True,
            "entities": origin_rows,
        }
        if origin_rows
        else None
    )
    # REQ-ECONOMICS-DASHBOARD verlangt hier ausdrücklich den Hinweis, dass
    # die Herkunftsaufteilung eine konservative Schätzung am
    # Netzanschlusspunkt ist (REQ-ENERGY-ORIGIN), keine physikalische
    # Einzelstromverfolgung - als Teil dieser einen Karte (vertical-stack),
    # nicht als zusätzliche eigenständige Karte, und nur relevant, wenn
    # überhaupt eine der Herkunfts-Entities vorhanden ist.
    origin_note_card = (
        {
            "type": "markdown",
            "content": (
                "Die Herkunftsaufteilung ist eine konservative Schätzung "
                "am Netzanschlusspunkt, keine physikalische "
                "Einzelstromverfolgung."
            ),
        }
        if origin_card is not None
        else None
    )
    origin_block = _stack_card([origin_card, origin_note_card])

    # REQ-ECONOMICS-DASHBOARD: eine gemeinsame Karte in genau dieser
    # Reihenfolge (ROI, Fortschritts-Gauge, dann der Rest) - eine
    # "entities"-Karte kann selbst keine Gauge einbetten, deshalb
    # _stack_card (vertical-stack) aus drei Teilkarten. Die vier Sensoren
    # sind (anders als z. B. die netzdienlichen Entities) immer bereits
    # statisch registriert, auch ohne konfigurierte Investitionskosten
    # (siehe REQ-ECONOMICS-AMORTIZATION). Eine build-time-Prüfung der
    # Config-Entry-Options wäre nach einer späteren Options-Änderung
    # veraltet, ohne dass das gespeicherte Dashboard je neu gebaut wird
    # (async_update_options aktualisiert nur den Coordinator) - die ganze
    # Karte deshalb stattdessen in eine Core-"conditional"-Karte packen,
    # die zur Laufzeit an ein Laufzeitsignal hängt, das ausschließlich die
    # Investitionskosten-Konfiguration abbildet: sie blendet sich beim
    # Setzen/Entfernen der Investitionskosten automatisch ein/aus, sobald
    # der Coordinator neu rechnet, ganz ohne Dashboard-Neubau.
    #
    # `economics_roi` selbst eignet sich dafür NICHT als Gate: es wird
    # laut SaxPowerCoordinator._publish_amortization auch bei
    # deaktiviertem Tarif oder noch nicht initialisierter Geldbilanz
    # "unknown", obwohl Investitionskosten konfiguriert sind.
    #
    # Die Bedingung prüft deshalb den ZUSTAND eines eigenen
    # Binary-Sensors, der genau "Investitionskosten hinterlegt" abbildet.
    roi_entity_id, roi_row = _resolved_row(
        hass, entry_id, "sensor", "economics_roi", translations
    )
    roi_rows: list[dict[str, Any] | str] = [roi_row] if roi_row else []
    # Der ROI rechnet den Vorlauf-Ertrag mit ein, das operative Ergebnis
    # eine Karte höher nicht - ohne diese Zeile ließe sich die Differenz
    # zwischen beiden im Dashboard nicht auflösen (siehe
    # coordinator._publish_amortization).
    prior_row = _attribute_row(
        roi_entity_id,
        "prior_result_eur",
        "Bereits erwirtschafteter Ertrag",
        suffix="€",
    )
    if prior_row is not None:
        roi_rows.append(prior_row)
    roi_row_card = (
        {
            "type": "entities",
            "title": "Investition und Amortisation",
            "state_color": True,
            "entities": roi_rows,
        }
        if roi_rows
        else None
    )
    progress_gauge = _gauge_card(
        hass,
        entry_id,
        "sensor",
        "economics_amortization_progress",
        translations,
        min_value=0,
        max_value=100,
        # Durchgehend blau statt der sonst üblichen Ampel: Ein niedriger
        # Amortisationsfortschritt ist kein Fehlerzustand, den der Anwender
        # abstellen könnte, sondern nur ein früher Zeitpunkt auf einer
        # mehrjährigen Strecke - rot/gelb hätte genau das suggeriert.
        segments=[{"from": 0, "color": "blue"}],
    )
    remaining_rows_card = _entities_card(
        hass,
        entry_id,
        "",
        [
            ("sensor", "economics_remaining_to_payback"),
            ("sensor", "economics_net_savings_today"),
        ],
        translations,
    )
    investment_stack = _stack_card([roi_row_card, progress_gauge, remaining_rows_card])
    investment_card = investment_stack
    if investment_stack is not None:
        configured_entity_id = _entity_id(
            hass, "binary_sensor", f"{entry_id}_economics_investment_configured"
        )
        if configured_entity_id is not None:
            investment_card = {
                "type": "conditional",
                "conditions": [{"entity": configured_entity_id, "state": "on"}],
                "card": investment_stack,
            }

    balance_rows: list[dict[str, Any] | str] = []
    for entity_domain, suffix in (
        ("sensor", "economics_avoided_grid_cost"),
        ("sensor", "economics_grid_charge_cost"),
        ("sensor", "economics_pv_opportunity_cost"),
        ("sensor", "economics_operating_result"),
        ("sensor", "economics_net_savings"),
        ("sensor", "economics_unpriced_charge"),
        ("sensor", "economics_unpriced_discharge"),
    ):
        _, row = _resolved_row(hass, entry_id, entity_domain, suffix, translations)
        if row is not None:
            balance_rows.append(row)
    # Die tatsächlich bewertete Energiemenge macht jeden Betrag dieser
    # Karte nachrechenbar (Betrag / Preis = Menge) und zeigt zugleich, dass
    # sie sich NICHT auf die Herkunftszähler der Karte darüber bezieht,
    # sondern nur auf den Zeitraum seit Bilanzbeginn - siehe
    # coordinator._energy_origin_attributes. Beide Mengen sind Attribute
    # des Status-Sensors (REQ-ECONOMICS-OBSERVABILITY) und haben keinen
    # eigenen Sensor.
    for attribute, label in (
        ("priced_charge_kwh", "Bewertete Ladung"),
        ("priced_discharge_kwh", "Bewertete Entladung"),
    ):
        row = _attribute_row(status_entity_id, attribute, label)
        if row is not None:
            balance_rows.append(row)
    balance_card = (
        {
            "type": "entities",
            "title": "Operative Geldbilanz",
            "state_color": True,
            "entities": balance_rows,
        }
        if balance_rows
        else None
    )

    # REQ-ECONOMICS-DASHBOARD: Der hinterlegte Tarifplan lebt sonst
    # ausschließlich in entry.options und ist damit nur im Options Flow
    # einsehbar - dort aber immer im Bearbeitungsmodus und ohne jeden Bezug
    # zur aktuellen Uhrzeit. Acht Zeitfenster über Mitternacht hinweg sind
    # fehleranfällig; ohne Anzeige fällt ein Zahlendreher erst Wochen später
    # in der Geldbilanz auf. Die Karte hängt wie die Investitionskarte an
    # einem Laufzeitsignal (hier dem Attribut `tariff_type`) statt an einem
    # zur Bauzeit gelesenen Options-Wert: Ein Tarifwechsel blendet sie
    # dadurch selbsttätig ein und aus, ohne dass das gespeicherte Dashboard
    # je neu gebaut wird.
    tariff_plan_card = _tariff_plan_card(hass, entry_id)

    # Die Tab-Leiste zeigt bei gesetztem Icon ausschließlich das Icon, den
    # Titel nur noch als Tooltip. Ein Name, den Material Design Icons nicht
    # kennt, rendert als leere Fläche - der Tab ist dann zwar vorhanden und
    # anklickbar, aber unsichtbar. Genau das passierte mit dem frei
    # erfundenen "mdi:cash-chart" (Anwenderbericht: "Wirtschaftlichkeits-Tab
    # wird nicht angezeigt", obwohl der View im gespeicherten Dashboard
    # stand). Neue Icons deshalb immer gegen die MDI-Liste prüfen.
    economics_view = _view(
        "Wirtschaftlichkeit",
        "wirtschaftlichkeit",
        "mdi:cash-multiple",
        [
            status_card,
            tariff_plan_card,
            origin_block,
            balance_card,
            investment_card,
            _statistics_graph_card(
                hass,
                entry_id,
                "Verlauf (30 Tage)",
                [
                    ("sensor", "economics_operating_result"),
                    ("sensor", "economics_avoided_grid_cost"),
                    ("sensor", "economics_grid_charge_cost"),
                    ("sensor", "economics_pv_opportunity_cost"),
                ],
            ),
        ],
    )

    savings_status_card = _savings_status_card(status_entity_id)
    savings_explanation_card = _savings_explanation_card(hass, entry_id)
    savings_result_entity_id = _entity_id(
        hass, "sensor", f"{entry_id}_economics_net_savings"
    )
    savings_period_grid = None
    savings_free_period_block = None
    if savings_result_entity_id is not None:
        savings_period_grid = _grid_card(
            [
                _calendar_statistic_card(
                    savings_result_entity_id, "Heute bisher", "day"
                ),
                _calendar_statistic_card(
                    savings_result_entity_id, "Diese Woche bisher", "week"
                ),
                _calendar_statistic_card(
                    savings_result_entity_id, "Dieser Monat bisher", "month"
                ),
                _calendar_statistic_card(
                    savings_result_entity_id, "Dieses Jahr bisher", "year"
                ),
            ]
        )
        savings_free_period_block = _savings_free_period_block(savings_result_entity_id)

    savings_payback_block = _savings_payback_block(
        hass,
        entry_id,
        translations,
        savings_result_entity_id,
        status_entity_id,
    )

    savings_view = _view(
        "Ersparnis",
        "ersparnis",
        "mdi:piggy-bank",
        [
            savings_payback_block,
            savings_period_grid,
            savings_explanation_card,
            savings_free_period_block,
            savings_status_card,
        ],
    )

    return {
        "views": [
            general_view,
            charging_view,
            grid_serving_view,
            price_view,
            economics_view,
            savings_view,
        ]
    }


async def async_create_dashboard(
    hass: HomeAssistant, entry: ConfigEntry, *, force: bool = False
) -> None:
    """Legt das mitgelieferte SAX-Power-Dashboard an, falls es noch nicht existiert.

    `force=True` (Service sax_power.reinstall_dashboard, siehe __init__.py)
    überschreibt zusätzlich ein bereits vorhandenes Dashboard mit der
    aktuell aus den Views/Karten gebauten Konfiguration - z. B. um es nach
    manuellen Änderungen wieder auf den Auslieferungszustand
    zurückzusetzen. Panel-Registrierung/Sidebar-Eintrag bleiben dabei
    unangetastet, es wird nur der Karteninhalt neu geschrieben.

    Rein optionale Komfortfunktion, die auf nicht-öffentlichen Lovelace-
    Interna aufbaut (siehe Modul-Docstring) - jeder Fehler wird deshalb nur
    geloggt statt weitergereicht, damit ein künftiges Home-Assistant-Update,
    das diese Interna ändert, niemals die Einrichtung der eigentlichen
    Integration blockiert.
    """
    try:
        await _async_create_dashboard(hass, entry, force=force)
    except Exception:  # siehe Docstring - darf die Integration nie blockieren
        _LOGGER.warning(
            'Dashboard "%s" konnte nicht automatisch angelegt werden - bitte bei '
            "Bedarf manuell über Einstellungen -> Dashboards anlegen",
            DASHBOARD_TITLE,
            exc_info=True,
        )


async def _async_create_dashboard(
    hass: HomeAssistant, entry: ConfigEntry, *, force: bool
) -> None:
    lovelace_data = hass.data.get(LOVELACE_DATA)
    if lovelace_data is None:
        _LOGGER.warning("Lovelace ist nicht verfügbar, Dashboard wird übersprungen")
        return

    existing_storage = lovelace_data.dashboards.get(DASHBOARD_URL_PATH)
    if existing_storage is not None:
        if force:
            await existing_storage.async_save(
                await async_build_dashboard_config(hass, entry.entry_id)
            )
        return  # bereits angelegt (z. B. durch einen früheren Setup-Lauf)

    # Eigene DashboardsCollection-Instanz statt der von lovelace.async_setup
    # verdrahteten (siehe Modul-Docstring) - liest/schreibt denselben
    # Speicher, deshalb hier zusätzlich prüfen, ob der Eintrag schon
    # persistiert wurde (z. B. nach einem Neustart), auch wenn er im
    # laufenden Betrieb noch nicht in lovelace_data.dashboards auftaucht.
    dashboards_collection = lovelace_dashboard.DashboardsCollection(hass)
    await dashboards_collection.async_load()
    if any(
        item[CONF_URL_PATH] == DASHBOARD_URL_PATH
        for item in dashboards_collection.async_items()
    ):
        return

    item = await dashboards_collection.async_create_item(
        {
            LL_CONF_ICON: DASHBOARD_ICON,
            LL_CONF_TITLE: DASHBOARD_TITLE,
            CONF_URL_PATH: DASHBOARD_URL_PATH,
        }
    )

    storage = lovelace_dashboard.LovelaceStorage(hass, item)
    await storage.async_save(await async_build_dashboard_config(hass, entry.entry_id))
    lovelace_data.dashboards[DASHBOARD_URL_PATH] = storage

    frontend.async_register_built_in_panel(
        hass,
        LOVELACE_DOMAIN,
        frontend_url_path=DASHBOARD_URL_PATH,
        require_admin=item[CONF_REQUIRE_ADMIN],
        show_in_sidebar=item[CONF_SHOW_IN_SIDEBAR],
        sidebar_title=item[LL_CONF_TITLE],
        sidebar_icon=item.get(LL_CONF_ICON, DEFAULT_ICON),
        config={"mode": MODE_STORAGE},
    )


async def async_check_dashboard_up_to_date(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Meldet ein vorhandenes, aber unvollständiges/veraltetes Dashboard.

    Das mitgelieferte Dashboard wird genau einmal gebaut - danach setzt
    __init__ das Flag CONF_CREATE_DASHBOARD zurück, und async_create_dashboard
    fasst ein vorhandenes Dashboard ohne `force` nicht an. Ergänzt eine
    neuere Version einen Tab, sieht ein Bestandsanwender davon deshalb
    nichts: Der Tab fehlt einfach, ohne Fehlermeldung und ohne Hinweis
    darauf, dass der Dienst sax_power.reinstall_dashboard ihn nachliefern
    würde (Anwenderbericht zu #138).

    Gemeldet wird ausschließlich ein VORHANDENES Dashboard, dem Tabs des
    aktuellen Auslieferungsstands oder die neuen Netto-Ersparnis-Entities
    fehlen. Letzteres erkennt gezielt die bereits veröffentlichten
    Snapshot-Dashboards, deren unveränderte View-Pfade sonst einen aktuellen
    Stand vortäuschen würden. Ein gar nicht vorhandenes Dashboard ist
    dagegen eine bewusste Entscheidung des Anwenders (siehe
    const.CONF_CREATE_DASHBOARD) und wird nicht angemahnt - eine
    Reparaturaufforderung würde genau das Dashboard zurückholen, das er
    gerade gelöscht hat.

    Wie der gesamte übrige Dashboard-Code eine rein optionale
    Komfortfunktion auf nicht-öffentlichen Lovelace-Interna: Jeder Fehler
    wird nur geloggt, niemals weitergereicht.
    """
    if entry.data.get(CONF_DASHBOARD_UPDATE_DISMISSED):
        return
    try:
        missing = await _async_missing_dashboard_views(hass, entry)
    except Exception:  # siehe Docstring - darf die Integration nie blockieren
        _LOGGER.debug("Dashboard-Stand nicht prüfbar", exc_info=True)
        return

    issue_id = f"{ISSUE_DASHBOARD_OUTDATED}_{entry.entry_id}"
    if not missing:
        ir.async_delete_issue(hass, DOMAIN, issue_id)
        return

    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_DASHBOARD_OUTDATED,
        translation_placeholders={
            "dashboard": DASHBOARD_TITLE,
            "views": ", ".join(missing),
        },
        data={"entry_id": entry.entry_id, "issue_key": ISSUE_DASHBOARD_OUTDATED},
    )


async def _async_missing_dashboard_views(
    hass: HomeAssistant, entry: ConfigEntry
) -> list[str]:
    """Titel fehlender oder fachlich veralteter Tabs.

    Verglichen werden die Pfade, nicht die Titel: Der Pfad ist der stabile
    Bezeichner eines Views, der Titel dagegen ist Anzeigetext. Für die
    Umstellung von Roh-Cashflow auf persistierte Netto-Ersparnis reicht das
    einmalig nicht: Die Snapshot-Stände besitzen bereits alle sechs Pfade,
    referenzieren in den beiden betroffenen Views aber die alten Entities.
    Deshalb müssen dort die aktuellen Entity-IDs vorkommen. Es wird weiterhin
    nichts automatisch überschrieben; der Treffer öffnet nur denselben
    reparierbaren Hinweis wie ein fehlender Tab.

    Leer, wenn das Dashboard vollständig ist, gar nicht existiert oder nicht
    im Storage-Modus läuft (ein YAML-Dashboard verwaltet der Anwender selbst).
    """
    lovelace_data = hass.data.get(LOVELACE_DATA)
    if lovelace_data is None:
        return []
    storage = lovelace_data.dashboards.get(DASHBOARD_URL_PATH)
    if not isinstance(storage, lovelace_dashboard.LovelaceStorage):
        return []

    stored = await storage.async_load(False)
    if not isinstance(stored, dict):
        return []
    stored_views = {
        view.get("path"): view
        for view in stored.get("views", [])
        if isinstance(view, dict)
    }

    expected = await async_build_dashboard_config(hass, entry.entry_id)
    outdated_paths = {
        view["path"] for view in expected["views"] if view["path"] not in stored_views
    }

    for path, suffix in (
        ("wirtschaftlichkeit", "economics_net_savings_today"),
        ("ersparnis", "economics_net_savings"),
    ):
        stored_view = stored_views.get(path)
        entity_id = _entity_id(hass, "sensor", f"{entry.entry_id}_{suffix}")
        if (
            stored_view is None
            or entity_id is None
            or _contains_dashboard_value(stored_view, entity_id)
        ):
            continue
        outdated_paths.add(path)

    savings_view = stored_views.get("ersparnis")
    investment_gate_entity_id = _entity_id(
        hass,
        "binary_sensor",
        f"{entry.entry_id}_economics_investment_configured",
    )
    if (
        savings_view is not None
        and investment_gate_entity_id is not None
        and not _contains_dashboard_value(savings_view, "### Amortisation")
    ):
        outdated_paths.add("ersparnis")

    for path in ("wirtschaftlichkeit", "ersparnis"):
        stored_view = stored_views.get(path)
        if stored_view is None:
            continue
        if any(
            _contains_dashboard_fragment(stored_view, removed_suffix)
            for removed_suffix in (
                "economics_average_daily_result_30d",
                "economics_projected_annual_result",
                "economics_estimated_payback_date",
            )
        ):
            outdated_paths.add(path)
    return [
        view["title"] for view in expected["views"] if view["path"] in outdated_paths
    ]


def _contains_dashboard_value(node: Any, expected: str) -> bool:
    """Ob ein verschachtelter Lovelace-Baustein exakt `expected` enthält."""
    if isinstance(node, dict):
        return any(
            _contains_dashboard_value(value, expected) for value in node.values()
        )
    if isinstance(node, list | tuple):
        return any(_contains_dashboard_value(value, expected) for value in node)
    return node == expected


def _contains_dashboard_fragment(node: Any, expected: str) -> bool:
    """Ob ein String in der Lovelace-Struktur den Wert enthält."""
    if isinstance(node, dict):
        return any(
            _contains_dashboard_fragment(value, expected) for value in node.values()
        )
    if isinstance(node, list | tuple):
        return any(_contains_dashboard_fragment(value, expected) for value in node)
    return isinstance(node, str) and expected in node
