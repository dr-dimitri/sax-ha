<script setup lang="ts">
import { computed, inject, ref, useId, watch } from "vue";
import ChargingNumberFields from "./ChargingNumberFields.vue";
import FixedTimeChargingInput from "./FixedTimeChargingInput.vue";
import { useFixedTimeCharging } from "../fixed-time-charging";
import { useChargingMonths } from "../charging-months";
import MonthSelection from "./MonthSelection.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import { finiteValue } from "../savings";
import type { HomeAssistant } from "../types";

const props = defineProps<{ editing: boolean; hass?: HomeAssistant }>();
const emit = defineEmits<{ apply: [] }>();
const numbers = ref<InstanceType<typeof ChargingNumberFields>>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const fixedTime = useFixedTimeCharging(dashboard);
const timeInput = ref<InstanceType<typeof FixedTimeChargingInput>>();
const pending = computed(
  () =>
    fixedTime.pending.value ||
    numbers.value?.pending ||
    bridge.value?.pending ||
    false,
);
const saving = computed(
  () => fixedTime.pending.value || numbers.value?.pending || false,
);
async function submit(): Promise<boolean> {
  if (saving.value) return false;
  if (!fixedTime.validate(timeInput.value?.value())) {
    timeInput.value?.focus();
    return false;
  }
  if (fixedTime.selected.value) {
    const settings = numbers.value?.prepare() ?? null;
    return settings !== null && fixedTime.submit(settings);
  }
  return (await numbers.value?.submit()) ?? true;
}
defineExpose({
  submit,
  reset: () =>
    !saving.value && fixedTime.reset() && (numbers.value?.reset() ?? true),
  pending: saving,
});
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
        mode: "Ladeweise",
        fixed: "Festes Netzladeziel",
        fixed_time: "Ab fester Uhrzeit",
        startTime: "Täglicher Ladestart",
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
        threshold: "Ladestart unter (%)",
        maxSoc: "Max SOC",
        global: "Max SOC (%)",
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
        mode: "Charging method",
        fixed: "Fixed grid charge target",
        fixed_time: "Start at a fixed time",
        startTime: "Daily charging start",
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
        maxSoc: "Max SOC",
        global: "Max SOC (%)",
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
const selected = computed<Method | "fixed_time" | null>(() => {
  if (fixedTime.active.value && dashboard?.connected.value) return "fixed_time";
  if (!bridge.value?.available) return null;
  if (bridge.value.state?.state === "off") return "fixed";
  if (bridge.value.state?.state === "on") return "bridge";
  return null;
});
const editorMethod = computed(() =>
  fixedTime.selected.value ? "fixed_time" : selected.value,
);
const blocked = computed(
  () => !bridge.value?.canControl || pending.value || selected.value === null,
);
const status = computed(() => {
  if (fixedTime.pending.value || bridge.value?.pending)
    return text.value.pending;
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
const globalLimit = computed(() => dashboard?.entity("number", "max_soc"));
const numberFields = computed(() => [
  ...(editorMethod.value === "fixed"
    ? [{ key: "timed_charge_min_soc", label: text.value.threshold }]
    : []),
  ...(editorMethod.value
    ? [
        {
          key: "timed_charge_max_soc",
          label:
            editorMethod.value !== "bridge"
              ? text.value.fixedTarget
              : text.value.bridgeTarget,
        },
      ]
    : []),
  { key: "max_soc", label: text.value.global },
]);
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
const { monthKeys, monthSummary } = useChargingMonths(dashboard);
async function choose(method: Method): Promise<void> {
  if (blocked.value) return;
  if (selected.value === method) {
    if (fixedTime.selected.value) fixedTime.reset();
    return;
  }
  await fixedTime.leave(method, () =>
    dashboard!.perform("switch", "bridge_charge_enabled", method === "bridge"),
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
      <dl
        v-if="selected === 'fixed_time'"
        class="electricity-summary-rows fixed-time-charging-summary"
      >
        <div>
          <dt>{{ text.startTime }}</dt>
          <dd>
            {{ fixedTime.displayStart(fixedTime.confirmed.value?.start) }}
          </dd>
        </div>
      </dl>
      <div
        v-if="selected"
        class="electricity-targets tou-charging-soc-row"
        :class="{ 'tou-charging-soc-row--bridge': selected !== 'fixed' }"
      >
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
        <div class="electricity-target tou-charging-target">
          <span>{{ targetLabel }}</span
          ><strong>{{ targetValue }}</strong>
        </div>
        <div class="electricity-target tou-charging-global">
          <span>{{ text.maxSoc }}</span
          ><strong>{{
            globalLimit?.available
              ? globalLimit.displayValue
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
    <div :id="feedbackId" class="tou-charging-feedback">
      <p
        v-if="fixedTime.error.value && editorMethod !== 'fixed_time'"
        class="tou-charging-error"
        role="alert"
      >
        {{
          german
            ? "Die Änderung ist fehlgeschlagen. Bitte erneut versuchen."
            : "The change failed. Please try again."
        }}
      </p>
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
        :aria-busy="pending"
      >
        <button
          v-for="method in methods"
          :key="method"
          type="button"
          :data-method="method"
          :aria-pressed="editorMethod === method"
          :disabled="blocked"
          @click="choose(method)"
        >
          <strong>{{ text[method] }}</strong>
        </button>
        <button
          type="button"
          data-method="fixed_time"
          :aria-pressed="editorMethod === 'fixed_time'"
          :disabled="blocked || !fixedTime.canConfigure.value"
          @click="fixedTime.choose"
        >
          <strong>{{ text.fixed_time }}</strong>
        </button>
      </div>
      <FixedTimeChargingInput
        v-if="editorMethod === 'fixed_time'"
        ref="timeInput"
        :model-value="fixedTime.start.value"
        :disabled="blocked || !fixedTime.canConfigure.value"
        :error="fixedTime.error.value"
        @update:model-value="fixedTime.edit"
        @apply="emit('apply')"
      />
      <p
        v-if="editorMethod === 'bridge' && !hasForecast"
        class="tou-charging-hint"
      >
        {{ text.pvRequired }}
      </p>
      <div class="tou-charging-limits">
        <ChargingNumberFields
          ref="numbers"
          :fields="numberFields"
          :soc-threshold-applies="editorMethod !== 'fixed_time'"
          :disabled="fixedTime.pending.value"
          @apply="emit('apply')"
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
.tou-charging-settings .tou-charging-soc-row {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.tou-charging-settings .tou-charging-soc-row--bridge {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.tou-charging-soc-row > .electricity-target {
  padding: 8px;
}
.tou-charging-soc-row > .electricity-target > strong {
  margin-top: auto;
  font-size: clamp(18px, 4cqi, 24px);
}
.tou-charging-limits .entity-control {
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
