<script setup lang="ts">
import { computed, useId } from "vue";
import { hemsNumber, hemsTime } from "../hems";
import type { HomeAssistant } from "../types";

const props = defineProps<{
  value: unknown;
  language: "de" | "en";
  hass?: HomeAssistant;
}>();
const id = useId();
function object(value: unknown): Readonly<Record<string, unknown>> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Readonly<Record<string, unknown>>)
    : {};
}
const data = computed(() => object(props.value));
const band = computed(() => object(data.value.uncertainty));
const archive = computed(() => object(data.value.archive));
const summary = computed(() => object(data.value.summary));
const live = computed(() => object(data.value.live));
const labels: Record<string, readonly [string, string]> = {
  title: ["Wie belastbar ist die Vorhersage?", "How reliable is the forecast?"],
  expected: ["Erwartete SAX-Entladung", "Expected SAX discharge"],
  range: ["Empirischer Bereich", "Empirical range"],
  unknown: ["Unbekannt", "Unknown"],
  disabled: ["Prognosearchiv deaktiviert", "Forecast archive disabled"],
  archiveFailure: [
    "Das Prognosearchiv konnte nicht gelesen oder gespeichert werden. Neue Freigaben benötigen einen erfolgreich gespeicherten Nachweis.",
    "The forecast archive could not be read or saved. New approvals require successfully saved evidence.",
  ],
  observe: [
    "Neue Verfahren werden beobachtet",
    "New methods are being observed",
  ],
  auto: ["Automatik nach Gütenachweis", "Automatic use after validation"],
  baseline: ["Bisheriges Nachtprofil aktiv", "Existing night profile active"],
  candidate: [
    "Geprüftes neues Nachtprofil aktiv",
    "Validated new night profile active",
  ],
  unavailable: ["Bandbreite noch nicht belastbar", "Range not yet validated"],
  insufficient_training: [
    "Noch zu wenige vollständig beobachtete Lernnächte.",
    "Too few fully observed training nights.",
  ],
  insufficient_validation: [
    "Die spätere Prüfung benötigt weitere vollständig beobachtete Nächte.",
    "Later validation needs more fully observed nights.",
  ],
  insufficient_coverage: [
    "Der Zeitraum ist nicht vollständig beobachtbar.",
    "The period is not fully observable.",
  ],
  not_validated: [
    "Für diese Prognose liegt noch kein passender Gütenachweis vor.",
    "There is no matching validation for this forecast yet.",
  ],
  stale: ["Der Gütenachweis ist veraltet.", "Validation is outdated."],
  rejected: [
    "Die spätere Prüfung bestätigt die Bandbreite derzeit nicht.",
    "Later validation does not currently support this range.",
  ],
  details: ["Prognosedetails", "Forecast details"],
  model: ["Aktives Verfahren", "Active method"],
  history: ["Gewählte / vorhandene Historie", "Selected / available history"],
  days: ["Tage", "days"],
  training: ["Lernnächte", "Training nights"],
  validation: ["Spätere Prüfnächte", "Later validation nights"],
  coverage: ["Beobachtete Trefferrate", "Observed coverage rate"],
  width: ["Mittlere Bereichsbreite", "Mean range width"],
  evaluated: ["Datenstand", "Data as of"],
  target: ["Vergleichszeitraum", "Target period"],
  pairs: ["Archivierte Vergleichspaare", "Archived comparison pairs"],
  observed: ["Belegte Vergleichsstunden", "Observed comparison hours"],
  measuredNights: [
    "Nächte mit Fehlervergleich",
    "Nights with error comparison",
  ],
  mae: ["Mittlerer absoluter Fehler", "Mean absolute error"],
  bias: [
    "Mittlere Abweichung (Prognose minus Ist)",
    "Mean bias (forecast minus actual)",
  ],
  under: ["Summierte Unterschätzung", "Total underestimation"],
  over: ["Summierte Überschätzung", "Total overestimation"],
  retained: [
    "Freigegebene Profilversion; laufende Gütebeobachtung deaktiviert.",
    "Validated profile version; ongoing quality observation disabled.",
  ],
  live: ["Anpassung der aktuellen Nacht", "Current-night adjustment"],
  higher: [
    "Aktuelle Nacht bisher höher als erwartet; Anpassung klingt ab bis",
    "Current night higher than expected; adjustment decays until",
  ],
  lower: [
    "Aktuelle Nacht bisher niedriger als erwartet; Anpassung klingt ab bis",
    "Current night lower than expected; adjustment decays until",
  ],
  liveObserve: [
    "Aktuelle Anpassung wird zunächst nur geprüft.",
    "Current adjustment is being evaluated only.",
  ],
  liveUnavailable: [
    "Keine aktuelle Anpassung: Es fehlen frische, gemeinsam belegte Vergleichszeiten oder die Freigabe.",
    "No current adjustment: fresh paired observations or validation are missing.",
  ],
  limit: [
    "Die Aufbewahrungsgrenze wurde erreicht; die verfügbare Evidenz ist entsprechend begrenzt.",
    "The retention limit was reached; available evidence is limited accordingly.",
  ],
  caution: [
    "Der Bereich gilt nur für beobachtbare SAX-Entladung. Er ist keine Garantie für den gesamten Hausbedarf, PV-Ertrag oder die Netzlademenge. Min-SOC bleibt die vorhandene Reserve.",
    "The range applies only to observable SAX discharge. It does not guarantee total household demand, solar yield or grid charging energy. Min SOC remains the existing reserve.",
  ],
};
const text = (key: string) =>
  labels[key]?.[props.language === "de" ? 0 : 1] ??
  labels.unknown![props.language === "de" ? 0 : 1];
const number = (value: unknown, unit = "") =>
  hemsNumber(value, props.language, unit);
const time = (value: unknown) => hemsTime(value, props.language, props.hass);
const valid = computed(
  () =>
    band.value.status === "validated" &&
    [band.value.expected_kwh, band.value.lower_kwh, band.value.upper_kwh].every(
      (value) =>
        typeof value === "number" && Number.isFinite(value) && value >= 0,
    ) &&
    Number(band.value.lower_kwh) <= Number(band.value.upper_kwh),
);
const reason = computed(() => {
  const code = String(band.value.reason ?? "not_validated");
  return labels[code] ? text(code) : text("not_validated");
});
const status = computed(() =>
  data.value.retained === true
    ? text("retained")
    : archive.value.enabled !== true
      ? text("disabled")
      : text(data.value.mode === "auto" ? "auto" : "observe"),
);
const details = computed(() => [
  [
    "model",
    text(data.value.candidate_active === true ? "candidate" : "baseline"),
  ],
  [
    "history",
    `${number(data.value.history_days)} / ${number(data.value.available_history_days)} ${text("days")}`,
  ],
  ["training", number(band.value.training_nights)],
  ["validation", number(band.value.validation_nights)],
  [
    "coverage",
    typeof band.value.empirical_coverage === "number"
      ? number(band.value.empirical_coverage * 100, "%")
      : text("unknown"),
  ],
  ["width", number(band.value.mean_width_kwh, "kWh")],
  ["pairs", number(archive.value.pairs_count)],
  ["observed", number(summary.value.observed_hours, "h")],
  ["measuredNights", number(summary.value.nights)],
  ["mae", number(summary.value.mae_kwh, "kWh")],
  ["bias", number(summary.value.bias_kwh, "kWh")],
  ["under", number(summary.value.under_kwh, "kWh")],
  ["over", number(summary.value.over_kwh, "kWh")],
  ["evaluated", time(data.value.evaluated_at)],
]);
</script>

<template>
  <section
    class="hems-quality"
    :aria-labelledby="`${id}-title`"
    data-testid="hems-quality"
  >
    <h3 :id="`${id}-title`">{{ text("title") }}</h3>
    <p>{{ status }}</p>
    <p v-if="['load_failed', 'save_failed'].includes(String(archive.status))">
      {{ text("archiveFailure") }}
    </p>
    <p v-if="typeof band.expected_kwh === 'number'">
      {{ text("expected") }}:
      <strong>{{ number(band.expected_kwh, "kWh") }}</strong>
      <span v-if="band.start && band.end">
        · {{ time(band.start) }} – {{ time(band.end) }}</span
      >
    </p>
    <p v-if="valid" data-testid="hems-range">
      {{ text("range") }}:
      <strong
        >{{ number(band.lower_kwh) }}–{{
          number(band.upper_kwh, "kWh")
        }}</strong
      >
    </p>
    <p v-else data-testid="hems-range-unavailable">
      {{ text("unavailable") }}. {{ reason }}
    </p>
    <p v-if="live.active === true">
      {{ text(Number(live.adjustment_kw) >= 0 ? "higher" : "lower") }}
      {{ time(live.expires_at) }}.
    </p>
    <p v-else-if="live.enabled === true">
      {{ text(live.observing === true ? "liveObserve" : "liveUnavailable") }}
    </p>
    <details>
      <summary>{{ text("details") }}</summary>
      <dl class="hems-card__data">
        <div v-for="[key, value] in details" :key="key">
          <dt>{{ text(key!) }}</dt>
          <dd>{{ value }}</dd>
        </div>
      </dl>
      <p v-if="archive.truncated === true">{{ text("limit") }}</p>
      <p>{{ text("caution") }}</p>
    </details>
  </section>
</template>

<style>
.hems-quality {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--divider-color, #ddd);
}
.hems-quality h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}
.hems-quality summary {
  cursor: pointer;
}
</style>
