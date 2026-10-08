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
        saved: "Ladeweise",
        start: "Start nur unter",
        startAtZero: "Start bei",
        calibrationShort: "Zellkalibrierung: vorübergehend bis 100 % erlaubt.",
        mode: "Ladeweise",
        fixed: "Festes Netzladeziel",
        bridge: "Nur Bedarf bis Solarstrom",
        target: "Netzladeziel",
        fixedTarget: "Netzladeziel (%)",
        bridgeTarget: "Maximales Netzladeziel (%)",
        pvRequired: "PV-Prognose fehlt · unter „Preise & Zeiten“ ergänzen.",
        months: "Aktive Monate",
        allYear: "Ganzjährig",
        noMonths:
          "Keine ausgewählt · Automatische Netzladung ganzjährig inaktiv",
        unknownMonths: "Monatsauswahl nicht vollständig bekannt",
        threshold: "Ladestart (%)",
        global: "Ladegrenze für alle Lademethoden (%)",
        unavailable: "Ladeweise nicht verfügbar.",
        valueUnavailable: "Nicht verfügbar",
        readonly: "Keine Berechtigung zum Ändern der Ladeweise.",
        disconnected: "Keine Verbindung zu Home Assistant.",
        pending: "Ladeweise wird übernommen …",
      }
    : {
        saved: "Charging method",
        start: "Start only below",
        startAtZero: "Start at",
        calibrationShort: "Cell calibration: temporarily up to 100% allowed.",
        mode: "Charging method",
        fixed: "Fixed grid charge target",
        bridge: "Only what is needed until solar power",
        target: "Grid charge target",
        fixedTarget: "Grid charge target (%)",
        bridgeTarget: "Maximum grid charge target (%)",
        pvRequired: "Solar forecast missing · add it under Prices & times.",
        months: "Active months",
        allYear: "All year",
        noMonths: "None selected · Automatic grid charging inactive all year",
        unknownMonths: "Month selection is not fully known",
        threshold: "Start threshold (%)",
        global: "Charge limit for all charging methods (%)",
        unavailable: "Charging method unavailable.",
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
const targetLabel = computed(() =>
  selected.value === "bridge"
    ? text.value.bridgeTarget.replace(" (%)", "")
    : text.value.target,
);
const targetValue = computed(() =>
  target.value?.available
    ? target.value.displayValue
    : text.value.valueUnavailable,
);
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
    <div class="tou-charging-summary">
      <dl class="electricity-summary-rows">
        <div>
          <dt>{{ text.saved }}</dt>
          <dd>{{ selected ? text[selected] : text.unavailable }}</dd>
        </div>
      </dl>
      <div v-if="selected" class="electricity-targets">
        <div class="electricity-target">
          <span>{{ targetLabel }}</span
          ><strong>{{ targetValue }}</strong>
        </div>
        <div
          v-if="selected === 'fixed'"
          class="electricity-target tou-charging-threshold"
        >
          <span>{{
            finiteValue(threshold?.state?.state) === 0
              ? text.startAtZero
              : text.start
          }}</span
          ><strong>{{
            threshold?.available
              ? threshold.displayValue
              : text.valueUnavailable
          }}</strong>
        </div>
      </div>
      <dl class="electricity-summary-rows tou-charging-month-summary">
        <div>
          <dt>{{ text.months }}</dt>
          <dd>{{ monthSummary }}</dd>
        </div>
      </dl>
    </div>
    <p v-if="selected" class="tou-charging-hint tou-charging-calibration">
      {{ text.calibrationShort }}
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
        </button>
      </div>
      <p v-if="selected === 'bridge' && !hasForecast" class="tou-charging-hint">
        {{ text.pvRequired }}
      </p>
      <div class="tou-charging-limits">
        <EntityControl
          v-if="selected"
          domain="number"
          entity-key="timed_charge_max_soc"
          :label="selected === 'fixed' ? text.fixedTarget : text.bridgeTarget"
          hide-confirmed-label
        />
        <EntityControl
          v-if="selected === 'fixed'"
          domain="number"
          entity-key="timed_charge_min_soc"
          :label="text.threshold"
          hide-confirmed-label
        />
        <EntityControl
          domain="number"
          entity-key="max_soc"
          :label="text.global"
          hide-confirmed-label
        />
      </div>
      <h3>{{ text.months }}</h3>
      <MonthSelection :entity-keys="monthKeys" always-expanded />
    </div>
  </div>
</template>

<style>
.tou-charging-settings {
  min-width: 0;
}
.tou-charging-limits > .entity-control {
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
  padding: 12px;
  text-align: left;
  font: inherit;
  cursor: pointer;
}
.tou-charging-methods button[aria-pressed="true"] {
  border: 2px solid var(--primary-color, #03a9f4);
  background: var(--secondary-background-color, #f5f5f5);
  padding: 11px;
}
.tou-charging-methods strong {
  display: block;
  line-height: 1.5;
}
.tou-charging-methods button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.tou-charging-methods button:focus-visible {
  outline: 3px solid var(--primary-color, #03a9f4);
  outline-offset: 3px;
}
@media (max-width: 700px) {
  .tou-charging-methods {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
