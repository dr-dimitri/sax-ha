<script setup lang="ts">
import { computed, inject, useId } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import EntityControl from "./EntityControl.vue";
import {
  finiteValue,
  formatSavingsDate,
  formatSavingsNumber,
} from "../savings";
import type { HomeAssistant } from "../types";

const props = defineProps<{ hass?: HomeAssistant }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const id = useId();
const german = computed(() => dashboard?.language.value === "de");
const plan = computed(() => dashboard?.entity("sensor", "bridge_charge_plan"));
const control = computed(() =>
  dashboard?.entity("switch", "bridge_charge_enabled"),
);
const attributes = computed(() => plan.value?.state?.attributes ?? {});
const configurationHint = computed(() => {
  switch (control.value?.state?.attributes.configuration_error) {
    case "bridge_pv_start_required":
      return german.value
        ? "Zum Einschalten unter Konfigurieren eine PV-Prognosequelle auswählen."
        : "To enable planning, select a PV forecast source in the integration options.";
    case "bridge_tariff_required":
      return german.value
        ? "Zum Einschalten unter Konfigurieren einen zeitvariablen Tarif einrichten."
        : "To enable planning, configure a time-of-use tariff in the integration options.";
    default:
      return null;
  }
});
const text = computed(() =>
  german.value
    ? {
        title: "Ladeplanung",
        setup:
          "Die Planung lädt nur den benötigten Bedarf bis zum PV-Start. „Netzladung aktiv“ muss ebenfalls eingeschaltet sein. Tarif und PV-Prognosequelle werden unter Konfigurieren ausgewählt.",
        unavailable: "Die Ladeplanung ist derzeit nicht verfügbar.",
        incomplete:
          "Die Angaben zum Ladeplan sind noch unvollständig. Ladezeiten können derzeit nicht angezeigt werden.",
        off: "Die verbrauchsabhängige Ladeplanung ist ausgeschaltet.",
        waiting_for_data:
          "Für die Ladeplanung werden noch gültige Verbrauchsdaten und ein PV-Start benötigt. Die Verbrauchsprognose benötigt mindestens eine Minute Beobachtungszeit.",
        paused:
          "Die Ladeplanung ist pausiert. Die geplante Netzladung ist derzeit nicht freigegeben.",
        complete: "Die geplante Netzladung ist abgeschlossen.",
        not_needed: "Eine Netzladung ist derzeit nicht erforderlich.",
        insufficient:
          "Die mögliche Netzladung reicht voraussichtlich nicht aus, um die Zeit bis zum PV-Start vollständig zu überbrücken.",
      }
    : {
        title: "Charging plan",
        setup:
          "Planning charges only the energy needed until PV starts. The main grid charging switch must also be on. Select the tariff and PV forecast source in the integration options.",
        unavailable: "The charging plan is currently unavailable.",
        incomplete:
          "The charging plan is still incomplete. Charging times cannot currently be displayed.",
        off: "Consumption-based charging planning is turned off.",
        waiting_for_data:
          "Charging planning is waiting for valid consumption data and a PV start. The consumption forecast needs at least one minute of observations.",
        paused:
          "The charging plan is paused. Planned grid charging is currently not permitted.",
        complete: "The planned grid charging is complete.",
        not_needed: "No grid charging is currently needed.",
        insufficient:
          "The available grid charging is not expected to cover the entire period until PV starts.",
      },
);
const status = computed(() =>
  plan.value?.available ? plan.value.state?.state : "unavailable",
);
const reasons = computed<Record<string, string>>(() =>
  german.value
    ? {
        pv_start_missing:
          "Die gewählte PV-Prognose liefert noch keinen Zeitraum, der den Verbrauch mindestens 30 Minuten lang deckt. Bitte die PV-Prognose in den Integrationsoptionen prüfen.",
        consumption_missing:
          "Für die Verbrauchsprognose wird mindestens eine Minute Entlademessung benötigt.",
        measurements_missing: "Aktuelle Batteriemesswerte fehlen.",
        calibration: "Die Batteriekalibrierung hat Vorrang.",
        pv_surplus: "PV-Überschuss pausiert die geplante Netzladung.",
        manual_charge: "Die manuelle Ladung hat Vorrang.",
        disabled:
          "Den Schalter „Verbrauchsbasierte Ladeplanung“ hier und den Hauptschalter „Netzladung aktiv“ einschalten.",
      }
    : {
        pv_start_missing:
          "The selected PV forecast does not yet provide a period covering consumption for at least 30 minutes. Check the PV forecast in the integration options.",
        consumption_missing:
          "The consumption forecast needs at least one minute of discharge measurements.",
        measurements_missing: "Current battery measurements are missing.",
        calibration: "Battery calibration takes priority.",
        pv_surplus: "PV surplus pauses planned grid charging.",
        manual_charge: "Manual charging takes priority.",
        disabled:
          "Turn on “Consumption-based charging planning” here and the main grid charging switch.",
      },
);
const reason = computed(() =>
  typeof attributes.value.reason === "string"
    ? reasons.value[attributes.value.reason]
    : undefined,
);
function number(value: unknown, min: number, max: number, digits = 1) {
  const numeric = finiteValue(value);
  return numeric !== null && numeric >= min && numeric <= max
    ? formatSavingsNumber(numeric, props.hass, digits)
    : null;
}
function timestamp(value: unknown) {
  // Backend timestamps need an explicit zone; local parsing invents an offset.
  return typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})$/.test(value)
    ? formatSavingsDate(value, props.hass)
    : null;
}
const dates = computed(() => ({
  discharge: timestamp(attributes.value.discharge_at),
  start: timestamp(attributes.value.charge_start),
  end: timestamp(attributes.value.charge_end),
  pv: timestamp(attributes.value.pv_start),
}));
const forecast = computed(() => {
  const minutes = number(attributes.value.observation_minutes, 1, 60);
  if (!minutes || !dates.value.discharge) return null;
  const average = number(attributes.value.average_discharge_w, 0, Infinity, 0);
  if (german.value) {
    const consumption = average ? ` (durchschnittlich ${average} W)` : "";
    return `Aufgrund des Verbrauchs der letzten ${minutes} Minuten${consumption} wird der Speicher voraussichtlich bis ${dates.value.discharge} Uhr entleert sein.`;
  }
  const consumption = average ? ` (an average of ${average} W)` : "";
  return `Based on consumption over the last ${minutes} minutes${consumption}, the battery is expected to be depleted by ${dates.value.discharge}.`;
});
const paragraphs = computed(() => {
  const { start, end, pv } = dates.value;
  const runningPartial =
    status.value === "charging" &&
    (finiteValue(attributes.value.shortfall_kwh) ?? 0) > 0;
  switch (runningPartial ? "insufficient" : status.value) {
    case "planned":
    case "charging": {
      if (!start || !end || !pv) return [text.value.incomplete];
      const charging = status.value === "charging";
      const schedule = german.value
        ? `${charging ? "Die Niedertarifladung läuft seit" : forecast.value ? "Daher beginnt die Aufladung im Niedertarif um" : "Die Aufladung im Niedertarif beginnt um"} ${start} Uhr und dauert voraussichtlich bis ${end} Uhr, um die Zeit bis zum PV-Start um ${pv} Uhr zu überbrücken.`
        : `${charging ? "Low-tariff charging has been running since" : forecast.value ? "Therefore, low-tariff charging will start at" : "Low-tariff charging will start at"} ${start} and is expected to continue until ${end}, to cover consumption until PV starts at ${pv}.`;
      return [forecast.value, schedule];
    }
    case "not_needed":
      return [
        forecast.value,
        pv
          ? german.value
            ? `Eine Netzladung ist nicht erforderlich: Der Speicher reicht voraussichtlich bis zum PV-Start um ${pv} Uhr.`
            : `No grid charging is needed: the battery is expected to last until PV starts at ${pv}.`
          : text.value.not_needed,
      ];
    case "insufficient": {
      const shortfall = number(attributes.value.shortfall_kwh, 0, Infinity, 2);
      const shortage = shortfall
        ? german.value
          ? ` Voraussichtlicher Fehlbetrag: ${shortfall} kWh.`
          : ` Expected shortfall: ${shortfall} kWh.`
        : "";
      const partial =
        start && end
          ? german.value
            ? runningPartial
              ? `Eine teilweise Aufladung im Niedertarif läuft seit ${start} Uhr bis voraussichtlich ${end} Uhr.`
              : `Eine teilweise Aufladung im Niedertarif ist von ${start} Uhr bis voraussichtlich ${end} Uhr geplant.`
            : runningPartial
              ? `Partial low-tariff charging has been running since ${start} and is expected to continue until ${end}.`
              : `Partial low-tariff charging is planned from ${start} until approximately ${end}.`
          : null;
      const horizon = pv
        ? german.value
          ? `Der PV-Start wird für ${pv} Uhr erwartet.`
          : `PV is expected to start at ${pv}.`
        : null;
      return [
        forecast.value,
        text.value.insufficient + shortage,
        partial,
        horizon,
      ];
    }
    case "off":
      return [text.value.off, reason.value ?? reasons.value.disabled];
    case "waiting_for_data":
      return [reason.value ?? text.value.waiting_for_data];
    case "paused":
      return [text.value.paused, reason.value];
    case "complete":
      return [text.value.complete];
    default:
      return [text.value.unavailable];
  }
});
const target = computed(() => {
  if (!["planned", "charging", "insufficient"].includes(status.value ?? ""))
    return null;
  const soc = number(attributes.value.target_soc, 0, 100);
  return soc
    ? german.value
      ? `Geplantes Ladeziel: ${soc} %.`
      : `Planned charge target: ${soc} %.`
    : null;
});
</script>

<template>
  <section
    v-if="plan || control"
    class="charge-plan"
    :aria-labelledby="`${id}-charge-plan`"
  >
    <h2 :id="`${id}-charge-plan`">{{ text.title }}</h2>
    <EntityControl domain="switch" entity-key="bridge_charge_enabled" />
    <p v-if="control">{{ text.setup }}</p>
    <p v-if="configurationHint">{{ configurationHint }}</p>
    <template v-for="(paragraph, index) in paragraphs" :key="index">
      <p v-if="paragraph">{{ paragraph }}</p>
    </template>
    <p v-if="target" class="charge-plan__target">{{ target }}</p>
  </section>
</template>

<style>
.charge-plan {
  min-width: 0;
  padding: 24px;
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  box-shadow: var(--ha-card-box-shadow, none);
  color: var(--primary-text-color, #212121);
}
.charge-plan h2 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.5;
}
.charge-plan p {
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.charge-plan p:last-child {
  margin-bottom: 0;
}
.charge-plan__target {
  color: var(--secondary-text-color, #666);
}
@media (max-width: 600px) {
  .charge-plan {
    padding: 20px;
  }
}
@container sax-content (min-width: 860px) {
  .charge-plan {
    padding: 18px;
  }
  .charge-plan h2 {
    margin-bottom: 12px;
    font-size: 16px;
  }
}
</style>
