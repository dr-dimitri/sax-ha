<script setup lang="ts">
import { computed, inject, useId } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import { hemsNumber, hemsReason, hemsTime } from "../hems";
import type { HomeAssistant } from "../types";

const props = defineProps<{
  tariff: "timed" | "dynamic";
  hass?: HomeAssistant;
}>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const id = useId();
const language = computed(() => dashboard?.language.value ?? "en");
const entity = computed(() => dashboard?.entity("sensor", "hems_status"));
const attrs = computed(() =>
  entity.value?.available ? (entity.value.state?.attributes ?? {}) : {},
);
const active = computed(() => attrs.value.mode === props.tariff);
const state = computed(() =>
  !entity.value?.available
    ? "unavailable"
    : !active.value
      ? "inactive"
      : String(attrs.value.status ?? "unknown"),
);
const fallback = computed(
  () =>
    active.value &&
    (attrs.value.fallback === true || state.value === "fallback"),
);
const labels: Record<string, readonly [string, string]> = {
  title: ["Bedarfsgesteuerte Nachtregelung", "Demand-based night control"],
  unknown: ["Unbekannt", "Unknown"],
  unavailable: ["Nicht verfügbar", "Unavailable"],
  inactive: ["Deaktiviert", "Disabled"],
  dynamicInactive: [
    "Die Strategie Bedarfsgesteuert / Nachtbrücke ist im Feld Strategie auswählbar.",
    "Select Demand-based / Night bridge in the Strategy field.",
  ],
  planned: ["Netzladung geplant", "Grid charging planned"],
  no_need: ["Kein Netzladen geplant", "No grid charging planned"],
  limited: ["Bedarf nur teilweise gedeckt", "Demand only partly covered"],
  blocked: ["Plan gesperrt", "Plan blocked"],
  fallback: ["Rückfall auf Min-/Max-SOC", "Fallback to min/max SOC"],
  evaluating: ["Prüfung läuft", "Evaluating"],
  awaiting_evaluation: ["Prüfung wird vorbereitet", "Preparing evaluation"],
  execution: ["Ausführung", "Execution"],
  confirmed: [
    "Netzladebefehl vom Gerät bestätigt",
    "Grid charge command acknowledged by device",
  ],
  waiting: [
    "Derzeit keine bestätigte Netzladung",
    "No acknowledged grid charging at present",
  ],
  target: ["Berechnetes Ladeziel", "Calculated SOC target"],
  remaining: ["Verbleibende Netzladeenergie", "Remaining grid charging energy"],
  start: ["Geplanter Beginn", "Planned start"],
  end: ["Geplantes Ende", "Planned end"],
  next: ["Nächste Prüfung", "Next evaluation"],
  details: ["Datenbasis und Erklärung", "Data and explanation"],
  evaluated: ["Letzte Prüfung", "Last evaluation"],
  supply: ["Erwartete PV-Versorgung", "Expected solar supply"],
  load: ["Erwarteter Bedarf", "Expected demand"],
  pvUsed: [
    "Zeitlich genutzte PV-Energie",
    "Solar energy used at the right time",
  ],
  available: ["Nutzbare Speicherenergie", "Usable battery energy"],
  reserve: ["Planungsreserve", "Planning reserve"],
  unmet: ["Ungedeckter Bedarf", "Unmet demand"],
  history: ["Nachtbeobachtung", "Night observations"],
  nights: ["Nächte", "nights"],
  hours: ["Stunden beobachtet", "hours observed"],
  coverage: ["Beobachtete Abdeckung", "Observed coverage"],
  model: ["Modellzeitraum", "Model period"],
  provider: ["PV-Anbieter / Anlage", "Solar provider / installation"],
  fetched: ["PV-Daten abgerufen", "Solar data retrieved"],
  pvCoverage: ["PV-Abdeckung", "Solar coverage"],
  full: ["angefragter Zeitraum vollständig", "requested period complete"],
  partial: [
    "teilweise; benötigt wird die vollständige Nachtbrücke einschließlich 60 Minuten PV-Nachweis",
    "partial; the full night bridge including 60 minutes of solar confirmation is required",
  ],
  maxAge: ["Zulässiges PV-Datenalter", "Maximum solar data age"],
  success: ["Letzter PV-Abruf erfolgreich", "Last solar update successful"],
  yes: ["Ja", "Yes"],
  no: ["Nein", "No"],
  unknownSuccess: [
    "Unbekannt; keine Erfolgszusage des Anbieters",
    "Unknown; provider does not guarantee update success",
  ],
  efficiencies: [
    "Annahmen: Lade- / Entladewirkungsgrad",
    "Assumptions: charge / discharge efficiency",
  ],
  policy: ["SAX-Annahme zum Prognosealter", "SAX assumption for forecast age"],
  modelInfo: [
    "Nachtmodell aus SAX-Entladeenergie der letzten sieben Tage. Eine vollständige Tagesoptimierung ist nicht enthalten.",
    "Night model based on SAX discharge energy over the last seven days. Full-day optimisation is not included.",
  ],
  reserveInfo: [
    "Min-SOC ist die Reserve der Planung; er ist keine neue Gerätesperre gegen Entladung. Max-SOC begrenzt das Ladeziel. Im Rückfall gelten dieselben gespeicherten Werte nach den klassischen Regeln.",
    "Min SOC is the planning reserve; it is not a new physical discharge lock. Max SOC limits the target. Fallback applies the same saved values using the classic rules.",
  ],
  classicInfo: [
    "Min-SOC bleibt die Startschwelle; Max-SOC das Ladeziel der klassischen Regelung.",
    "Min SOC remains the start threshold; max SOC is the target of classic control.",
  ],
  setup: [
    "PV-Anbieter und Anlage sowie Wirkungsgradannahmen lassen sich unter Einstellungen → Geräte & Dienste → SAX Power → Konfigurieren auswählen.",
    "Select the solar provider, installation and efficiency assumptions in Settings → Devices & services → SAX Power → Configure.",
  ],
  fallbackInfo: [
    "Die gespeicherte Min-/Max-SOC-Regel gilt. Tarifgrenzen und Geräteschutz bleiben wirksam.",
    "The saved min/max SOC rule applies. Tariff limits and device protection remain in force.",
  ],
  calibrationExtra: [
    "Zusätzliche Netzenergie für Kalibrierung",
    "Additional grid energy for calibration",
  ],
  executionRemaining: [
    "Verbleibende Energie der aktuellen Ladefreigabe",
    "Remaining energy of the current charging permission",
  ],
  executionDeadline: [
    "Ende der aktuellen Ladefreigabe",
    "Current charging permission ends",
  ],
  calibrationTarget: [
    "Ladeziel für Zellkalibrierung",
    "Cell calibration target",
  ],
  disconnected: [
    "Die Verbindung fehlt. Plan und nächster Prüftermin sind nicht verfügbar.",
    "Connection unavailable. The plan and next evaluation time are unavailable.",
  ],
  methods: ["Verwendete Schätzverfahren", "Estimation methods used"],
  quality: ["Datenqualität", "Data quality"],
};
const text = (key: string) =>
  labels[key]?.[language.value === "de" ? 0 : 1] ??
  labels.unknown![language.value === "de" ? 0 : 1];
const title = computed(() => text(fallback.value ? "fallback" : state.value));
const reasons = computed(() =>
  active.value && Array.isArray(attrs.value.reason_codes)
    ? attrs.value.reason_codes
        .filter((item): item is string => typeof item === "string")
        .slice(0, 10)
    : [],
);
const quality = computed(() =>
  [
    attrs.value.load_quality,
    attrs.value.pv_quality,
    ...(Array.isArray(attrs.value.pv_quality_flags)
      ? attrs.value.pv_quality_flags
      : []),
  ].filter((item): item is string => typeof item === "string" && !!item),
);
const methods = computed(() =>
  Array.isArray(attrs.value.load_quality_flags)
    ? attrs.value.load_quality_flags
        .filter((item): item is string => typeof item === "string")
        .slice(0, 8)
    : [],
);
const number = (value: unknown, unit = "") =>
  hemsNumber(value, language.value, unit);
const time = (value: unknown) => hemsTime(value, language.value, props.hass);
const next = computed(() =>
  active.value && state.value !== "evaluating"
    ? time(attrs.value.next_evaluation_at)
    : text("unknown"),
);
const execution = computed(() =>
  text(
    attrs.value.execution_charging === true
      ? "confirmed"
      : attrs.value.execution_charging === false
        ? "waiting"
        : "unknown",
  ),
);
const metrics = computed(() => [
  ["remaining", number(attrs.value.remaining_grid_kwh, "kWh")],
  ["target", number(attrs.value.target_soc, "%")],
  ["start", time(attrs.value.planned_start)],
  ["end", time(attrs.value.planned_end)],
]);
const data = computed(() => [
  ["executionRemaining", number(attrs.value.execution_remaining_kwh, "kWh")],
  ["executionDeadline", time(attrs.value.execution_deadline)],
  ["evaluated", time(attrs.value.evaluated_at)],
  ["supply", time(attrs.value.pv_supply_at)],
  ["load", number(attrs.value.expected_load_kwh, "kWh")],
  ["pvUsed", number(attrs.value.pv_used_kwh, "kWh")],
  ["available", number(attrs.value.available_battery_kwh, "kWh")],
  [
    "reserve",
    `${number(attrs.value.reserve_soc, "%")} / ${number(attrs.value.reserve_kwh, "kWh")}`,
  ],
  ["unmet", number(attrs.value.unmet_grid_kwh, "kWh")],
  [
    "history",
    `${number(attrs.value.nights_count)} ${text("nights")} · ${number(attrs.value.observed_hours)} ${text("hours")}`,
  ],
  [
    "coverage",
    typeof attrs.value.load_coverage === "number"
      ? number(attrs.value.load_coverage * 100, "%")
      : text("unknown"),
  ],
  [
    "model",
    `${time(attrs.value.load_model_start)} – ${time(attrs.value.load_model_end)}`,
  ],
  [
    "methods",
    methods.value.length
      ? methods.value
          .map((method) => hemsReason(method, language.value))
          .join(" · ")
      : text("unknown"),
  ],
  [
    "provider",
    `${attrs.value.pv_provider || text("unknown")} / ${attrs.value.pv_source_id || text("unknown")}`,
  ],
  ["fetched", time(attrs.value.pv_fetched_at)],
  [
    "pvCoverage",
    `${time(attrs.value.pv_coverage_start)} – ${time(attrs.value.pv_coverage_end)} · ${text(attrs.value.pv_coverage_complete === true ? "full" : attrs.value.pv_coverage_complete === false ? "partial" : "unknown")}`,
  ],
  [
    "maxAge",
    `${typeof attrs.value.pv_max_age_seconds === "number" ? number(attrs.value.pv_max_age_seconds / 3600, "h") : text("unknown")}${attrs.value.pv_freshness_policy === "sax_max_age_assumption" ? ` · ${text("policy")}` : ""}`,
  ],
  [
    "success",
    text(
      attrs.value.pv_update_success === true
        ? "yes"
        : attrs.value.pv_update_success === false
          ? "no"
          : "unknownSuccess",
    ),
  ],
  [
    "efficiencies",
    `${number(attrs.value.eta_charge_assumption)} / ${number(attrs.value.eta_discharge_assumption)}`,
  ],
]);
</script>

<template>
  <section
    v-if="entity"
    class="hems-card"
    :class="{ 'hems-card--fallback': fallback }"
    :aria-labelledby="`${id}-title`"
  >
    <header>
      <h2 :id="`${id}-title`">{{ text("title") }}</h2>
      <span class="hems-card__badge">{{ title }}</span>
    </header>
    <div class="hems-card__explanation" role="status" aria-live="polite">
      <p v-if="!entity.available">{{ text("disconnected") }}</p>
      <template v-else-if="active">
        <p v-if="fallback">{{ text("fallbackInfo") }}</p>
        <p v-for="reason in reasons" :key="reason">
          {{ hemsReason(reason, language) }}
        </p>
        <p v-if="typeof attrs.execution_constraint === 'string'">
          {{ hemsReason(attrs.execution_constraint, language) }}
        </p>
        <p>
          <strong>{{ text("execution") }}:</strong> {{ execution
          }}<template
            v-if="
              typeof attrs.execution_reason === 'string' &&
              !reasons.includes(attrs.execution_reason)
            "
            >. {{ hemsReason(attrs.execution_reason, language) }}</template
          >
        </p>
        <p v-if="attrs.calibration === true">
          {{ hemsReason("calibration", language) }}
          {{ text("calibrationTarget") }}:
          {{ number(attrs.execution_target_soc, "%") }}
          · {{ text("calibrationExtra") }}:
          {{ number(attrs.calibration_extra_kwh, "kWh") }}
        </p>
      </template>
      <p v-else>
        {{ text(tariff === "timed" ? "classicInfo" : "dynamicInactive") }}
      </p>
    </div>
    <dl v-if="active" class="hems-card__metrics">
      <div v-for="[key, value] in metrics" :key="key">
        <dt>{{ text(key!) }}</dt>
        <dd>{{ value }}</dd>
      </div>
      <div class="hems-card__next">
        <dt>{{ text("next") }}</dt>
        <dd data-testid="hems-next">{{ next }}</dd>
      </div>
    </dl>
    <details v-if="entity.available">
      <summary>{{ text("details") }}</summary>
      <p>{{ text("modelInfo") }}</p>
      <p>
        {{
          text(
            active
              ? "reserveInfo"
              : tariff === "timed"
                ? "classicInfo"
                : "dynamicInactive",
          )
        }}
      </p>
      <p>{{ text("setup") }}</p>
      <template v-if="active">
        <dl class="hems-card__data">
          <div v-for="[key, value] in data" :key="key">
            <dt>{{ text(key!) }}</dt>
            <dd>{{ value }}</dd>
          </div>
        </dl>
        <p v-for="reason in quality" :key="reason">
          {{ text("quality") }}: {{ hemsReason(reason, language) }}
        </p>
      </template>
    </details>
  </section>
</template>

<style>
.hems-card {
  margin-top: 20px;
  padding: 22px;
  border: 1px solid var(--divider-color, #ddd);
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  color: var(--primary-text-color, #212121);
  min-width: 0;
  overflow-wrap: anywhere;
  line-height: 1.55;
}
.hems-card header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 20px;
  justify-content: space-between;
}
.hems-card h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}
.hems-card__badge {
  border: 1px solid var(--divider-color, #ddd);
  border-radius: 20px;
  padding: 3px 12px;
  font-size: 13px;
}
.hems-card--fallback {
  border-left: 4px solid var(--warning-color, #b87900);
}
.hems-card p {
  margin: 12px 0;
}
.hems-card__metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 24px;
  margin: 18px 0;
}
.hems-card dt {
  color: var(--secondary-text-color, #666);
  font-size: 14px;
}
.hems-card dd {
  margin: 3px 0 0;
  font-variant-numeric: tabular-nums;
}
.hems-card__metrics dd {
  font-weight: 600;
}
.hems-card__next {
  grid-column: 1 / -1;
}
.hems-card summary {
  cursor: pointer;
  padding: 8px 0;
  color: var(--primary-text-color, #212121);
  font-weight: 500;
}
.hems-card summary:focus-visible {
  outline: 2px solid var(--primary-color, #03a9f4);
  outline-offset: 3px;
  border-radius: 4px;
}
.hems-card__data {
  display: grid;
  gap: 12px;
}
.hems-card__data > div {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) minmax(0, 1.4fr);
  gap: 12px;
}
@media (max-width: 600px) {
  .hems-card {
    padding: 18px;
    margin-top: 16px;
  }
  .hems-card__data > div {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
