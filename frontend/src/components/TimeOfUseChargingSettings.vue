<script setup lang="ts">
import { computed, inject, ref, useId, watch } from "vue";
import EntityControl from "./EntityControl.vue";
import MonthSelection from "./MonthSelection.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import { finiteValue } from "../savings";
import type { HomeAssistant } from "../types";

const props = defineProps<{ editing: boolean; hass?: HomeAssistant }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const german = computed(() => dashboard?.language.value === "de");
const feedbackId = `sax-tou-method-${useId()}`;
const visited = ref(props.editing);
watch(
  () => props.editing,
  (editing) => {
    if (editing) visited.value = true;
  },
);
const text = computed(() =>
  german.value
    ? {
        saved: "Gespeicherte Ladeweise",
        mode: "Ladeweise",
        immediate:
          "Jede Änderung wird einzeln übernommen. Die automatische Netzladung muss zusätzlich eingeschaltet sein.",
        fixed: "Festes Ladeziel",
        fixedHint:
          "Lädt in den günstigsten Tarifzeiten bis zu deinem Ladeziel. Beginnt nur, wenn der Ladestand unter der Startschwelle liegt.",
        bridge: "Nur Bedarf bis Solarstrom",
        bridgeHint:
          "Plant anhand deines bisherigen Verbrauchs nur die fehlende Energie bis zum erwarteten Solarstrom. Ist genug Energie im Speicher, wird nicht geladen.",
        target: "Ladeziel",
        fixedTarget: "Ladeziel (%)",
        bridgeTarget: "Höchstens laden bis (%)",
        fixedTargetHint:
          "Die Netzladung endet beim Ladeziel oder am Ende der günstigen Tarifzeit. Nach der Netzladung entlädt der Speicher bis zum Ende dieser Zeit nicht; Solarstrom kann ihn weiter füllen. Andere aktive Regeln können die Ladung begrenzen.",
        bridgeTargetHint:
          "Der berechnete Bedarf kann unter dieser Obergrenze liegen. Geladen wird nur in den günstigsten Tarifzeiten. Danach darf der Speicher wieder normal entladen. Ohne Verbrauchs- oder Prognosedaten wird kein neuer Ladeplan erstellt.",
        calibration:
          "Ausnahme: Bei fälliger Zellkalibrierung sind bis 100 % erlaubt, auch über Ladeziel und globale Ladegrenze hinaus. Alle anderen Ladebedingungen gelten weiter.",
        pvRequired:
          "Für „Nur Bedarf bis Solarstrom“ benötigst du eine passende PV-Prognose mit dem erwarteten Solarstart. Öffne in Schritt 1 „Bearbeiten“ und ergänze die Solarprognose.",
        months: "Aktive Monate",
        allYear: "Ganzjährig",
        noMonths:
          "Keine ausgewählt · Automatische Netzladung ganzjährig inaktiv",
        unknownMonths: "Monatsauswahl nicht vollständig bekannt",
        advanced: "Weitere Einstellungen",
        threshold: "Nur starten unter einem Ladestand von (%)",
        thresholdHint:
          "Beispiel: Bei 20 % beginnt eine neue Netzladung erst unter 20 %. Danach darf sie im selben günstigen Zeitfenster bis zum Ladeziel weiterlaufen. 0 % verhindert einen neuen Start.",
        thresholdSummary: "Neue Netzladung startet nur unter",
        zeroThreshold:
          "Startschwelle 0 %: Es beginnt keine neue automatische Netzladung.",
        thresholdUnavailable: "Startschwelle nicht verfügbar.",
        global: "Ladegrenze für alle Lademethoden (%)",
        globalHint:
          "Gilt auch für Solarstrom. Wenn du diese Grenze senkst, wird ein höheres Netzladeziel ebenfalls gesenkt. Ein späteres Anheben erhöht das Netzladeziel nicht automatisch.",
        disabled:
          "Automatische Netzladung ist aus. Die gespeicherten Einstellungen gelten nach dem Einschalten.",
        unavailable:
          "Ladeweise nicht verfügbar. Es wird keine Auswahl angenommen.",
        valueUnavailable: "Nicht verfügbar",
        readonly: "Keine Berechtigung zum Ändern der Ladeweise.",
        disconnected: "Keine Verbindung zu Home Assistant.",
        pending: "Ladeweise wird übernommen …",
      }
    : {
        saved: "Saved charging method",
        mode: "Charging method",
        immediate:
          "Each change is applied individually. Automatic grid charging must also be switched on.",
        fixed: "Fixed charge target",
        fixedHint:
          "Charges to your target during the cheapest tariff periods. Only starts when the battery level is below the start threshold.",
        bridge: "Only what is needed until solar power",
        bridgeHint:
          "Uses your recent consumption to plan only the missing energy until solar power is expected. Does not charge when the battery already holds enough energy.",
        target: "Charge target",
        fixedTarget: "Charge target (%)",
        bridgeTarget: "Charge up to at most (%)",
        fixedTargetHint:
          "Grid charging ends at the target or the end of the cheap tariff period. After grid charging, the battery does not discharge until this period ends; solar power can charge it further. Other active rules may limit charging.",
        bridgeTargetHint:
          "The calculated need may be below this upper limit. Charging only uses the cheapest tariff periods. Afterwards, the battery may discharge normally again. Missing consumption or forecast data prevents a new charging plan.",
        calibration:
          "Exception: When cell calibration is due, charging up to 100% is allowed beyond both the charge target and global limit. Other charging conditions still apply.",
        pvRequired:
          "“Only what is needed until solar power” requires a suitable forecast with the expected start of solar power. Open “Edit” in step 1 and add the solar forecast.",
        months: "Active months",
        allYear: "All year",
        noMonths: "None selected · Automatic grid charging inactive all year",
        unknownMonths: "Month selection is not fully known",
        advanced: "More settings",
        threshold: "Only start below a battery level of (%)",
        thresholdHint:
          "For example, 20% means a new grid charge starts only below 20%. It can then continue to the target within the same cheap period. 0% prevents a new start.",
        thresholdSummary: "New grid charging starts only below",
        zeroThreshold:
          "Start threshold 0%: No new automatic grid charge will start.",
        thresholdUnavailable: "Start threshold unavailable.",
        global: "Charge limit for all charging methods (%)",
        globalHint:
          "Also applies to solar charging. Lowering this limit also lowers a higher grid charge target. Raising it later does not automatically raise the grid charge target.",
        disabled:
          "Automatic grid charging is off. Saved settings apply after switching it on.",
        unavailable: "Charging method unavailable. No selection is assumed.",
        valueUnavailable: "Unavailable",
        readonly: "You do not have permission to change the charging method.",
        disconnected: "Disconnected from Home Assistant.",
        pending: "Applying charging method …",
      },
);
const bridge = computed(() =>
  dashboard?.entity("switch", "bridge_charge_enabled"),
);
type Method = "fixed" | "bridge";
const methods: Method[] = ["fixed", "bridge"];
const selected = computed<Method | null>(() => {
  if (!bridge.value?.available) return null;
  if (bridge.value.state?.state === "off") return "fixed";
  if (bridge.value.state?.state === "on") return "bridge";
  return null;
});
const blocked = computed(
  () =>
    !bridge.value?.canControl ||
    bridge.value.pending ||
    selected.value === null,
);
const status = computed(() => {
  if (bridge.value?.pending) return text.value.pending;
  if (!dashboard?.connected.value) return text.value.disconnected;
  if (!selected.value) return text.value.unavailable;
  if (!bridge.value?.metadata.can_control) return text.value.readonly;
  return "";
});
const target = computed(() =>
  dashboard?.entity("number", "timed_charge_max_soc"),
);
const threshold = computed(() =>
  dashboard?.entity("number", "timed_charge_min_soc"),
);
const thresholdSummary = computed(() => {
  const value = finiteValue(threshold.value?.state?.state);
  if (!threshold.value?.available || value === null)
    return text.value.thresholdUnavailable;
  if (value === 0) return text.value.zeroThreshold;
  return `${text.value.thresholdSummary} ${threshold.value.displayValue}.`;
});
const summary = computed(() => {
  if (!selected.value) return text.value.unavailable;
  const label =
    selected.value === "fixed"
      ? text.value.fixedTarget
      : text.value.bridgeTarget;
  const value = target.value?.available
    ? target.value.displayValue
    : text.value.valueUnavailable;
  return `${text.value[selected.value]} · ${label.replace(" (%)", "")} ${value}`;
});
const hasForecast = computed(
  () => !!dashboard?.tariff.value?.profiles?.time_of_use.pv_sensor,
);
const monthKeys = Array.from(
  { length: 12 },
  (_, index) => `timed_charge_month_${index + 1}`,
);
const monthSummary = computed(() => {
  const formatter = new Intl.DateTimeFormat(german.value ? "de" : "en", {
    month: "short",
    timeZone: "UTC",
  });
  const months = monthKeys.map((key, index) => {
    const entity = dashboard?.entity("switch", key);
    const state = entity?.state?.state;
    return {
      known: entity?.available && (state === "on" || state === "off"),
      selected: entity?.available && state === "on",
      name: formatter.format(new Date(Date.UTC(2024, index, 1))),
    };
  });
  const chosen = months.filter((month) => month.selected);
  const unknown = months.some((month) => !month.known);
  if (chosen.length === 12) return text.value.allYear;
  if (!chosen.length)
    return unknown ? text.value.unknownMonths : text.value.noMonths;
  return `${chosen.map((month) => month.name).join(", ")}${unknown ? ` · ${text.value.unknownMonths}` : ""}`;
});
async function choose(method: Method): Promise<void> {
  if (blocked.value || selected.value === method) return;
  await dashboard?.perform(
    "switch",
    "bridge_charge_enabled",
    method === "bridge",
  );
}
</script>

<template>
  <div class="tou-charging-settings">
    <p class="tou-charging-summary">
      <strong>{{ text.saved }}:</strong> {{ summary }}
    </p>
    <p
      v-if="selected && !editing"
      class="tou-charging-hint tou-charging-calibration"
    >
      {{ text.calibration }}
    </p>
    <p v-if="selected === 'fixed'" class="tou-charging-threshold">
      {{ thresholdSummary }}
    </p>
    <p class="tou-charging-month-summary">
      <strong>{{ text.months }}:</strong> {{ monthSummary }}
    </p>
    <p
      v-if="dashboard?.tariff.value?.automation_enabled === false"
      class="tou-charging-hint"
    >
      {{ text.disabled }}
    </p>
    <div :id="feedbackId" class="tou-charging-feedback">
      <p
        v-if="editing && bridge?.error"
        class="tou-charging-error"
        role="alert"
      >
        {{ bridge.error }}
      </p>
      <p
        v-if="status && (editing || !bridge?.pending)"
        role="status"
        aria-live="polite"
      >
        {{ status }}
      </p>
    </div>
    <div v-if="visited" v-show="editing" class="tou-charging-editor">
      <h3>{{ text.mode }}</h3>
      <p class="tou-charging-hint">{{ text.immediate }}</p>
      <div
        class="tou-charging-methods"
        role="group"
        :aria-label="text.mode"
        :aria-describedby="feedbackId"
        :aria-busy="bridge?.pending ?? false"
      >
        <button
          v-for="method in methods"
          :key="method"
          type="button"
          :data-method="method"
          :aria-pressed="selected === method"
          :disabled="blocked"
          @click="choose(method)"
        >
          <strong>{{ text[method] }}</strong>
          <span>{{
            method === "fixed" ? text.fixedHint : text.bridgeHint
          }}</span>
        </button>
      </div>
      <p v-if="!hasForecast" class="tou-charging-hint">{{ text.pvRequired }}</p>
      <template v-if="selected">
        <h3>{{ text.target }}</h3>
        <EntityControl
          domain="number"
          entity-key="timed_charge_max_soc"
          :label="selected === 'fixed' ? text.fixedTarget : text.bridgeTarget"
          hide-confirmed-label
        />
        <p class="tou-charging-hint">
          {{
            selected === "fixed" ? text.fixedTargetHint : text.bridgeTargetHint
          }}
        </p>
        <p v-if="editing" class="tou-charging-hint tou-charging-calibration">
          {{ text.calibration }}
        </p>
      </template>
      <details class="tou-charging-advanced">
        <summary>{{ text.advanced }}</summary>
        <template v-if="selected === 'fixed'">
          <EntityControl
            domain="number"
            entity-key="timed_charge_min_soc"
            :label="text.threshold"
            hide-confirmed-label
          />
          <p class="tou-charging-hint">{{ text.thresholdHint }}</p>
        </template>
        <EntityControl
          domain="number"
          entity-key="max_soc"
          :label="text.global"
          hide-confirmed-label
        />
        <p class="tou-charging-hint">{{ text.globalHint }}</p>
        <h3>{{ text.months }}</h3>
        <MonthSelection :entity-keys="monthKeys" />
      </details>
    </div>
  </div>
</template>

<style>
.tou-charging-settings {
  min-width: 0;
}
.tou-charging-editor > .entity-control,
.tou-charging-advanced > .entity-control {
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  padding: 12px 0;
}
.tou-charging-summary,
.tou-charging-threshold,
.tou-charging-month-summary {
  line-height: 1.5;
  overflow-wrap: anywhere;
}
.tou-charging-hint {
  color: var(--secondary-text-color, #666);
  font-size: 14px;
  line-height: 1.6;
}
.tou-charging-error {
  color: var(--error-color, #b00020);
}
.tou-charging-methods {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 16px 0;
}
.tou-charging-methods button {
  min-height: 44px;
  min-width: 0;
  border: 1px solid var(--divider-color, #ddd);
  border-radius: 8px;
  background: var(--card-background-color, #fff);
  color: var(--primary-text-color, #212121);
  padding: 16px;
  text-align: left;
  font: inherit;
  cursor: pointer;
}
.tou-charging-methods button[aria-pressed="true"] {
  border: 2px solid var(--primary-color, #03a9f4);
  background: var(--secondary-background-color, #f5f5f5);
  padding: 15px;
}
.tou-charging-methods strong,
.tou-charging-methods span {
  display: block;
  line-height: 1.5;
}
.tou-charging-methods span {
  color: var(--secondary-text-color, #666);
  font-size: 14px;
  margin-top: 6px;
}
.tou-charging-methods button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.tou-charging-methods button:focus-visible,
.tou-charging-advanced summary:focus-visible {
  outline: 3px solid var(--primary-color, #03a9f4);
  outline-offset: 3px;
}
.tou-charging-advanced {
  border-top: 1px solid var(--divider-color, #ddd);
  padding-top: 12px;
  margin-top: 20px;
}
.tou-charging-advanced summary {
  cursor: pointer;
  min-height: 44px;
  align-content: center;
}
@media (max-width: 700px) {
  .tou-charging-methods {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
