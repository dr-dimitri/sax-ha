<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import ChargingNumberFields from "./ChargingNumberFields.vue";
import MonthSelection from "./MonthSelection.vue";
import { useChargingMonths } from "../charging-months";
import FixedTimeChargingInput from "./FixedTimeChargingInput.vue";
import { useFixedTimeCharging } from "../fixed-time-charging";
import { SAX_DASHBOARD_KEY } from "../ha";
import { finiteValue } from "../savings";

const props = defineProps<{ editing: boolean }>();
const emit = defineEmits<{ apply: [] }>();
const numbers = ref<InstanceType<typeof ChargingNumberFields>>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const fixedTime = useFixedTimeCharging(dashboard);
const timeInput = ref<InstanceType<typeof FixedTimeChargingInput>>();
const pending = computed(
  () =>
    fixedTime.pending.value ||
    numbers.value?.pending ||
    strategy.value?.pending ||
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
const { monthKeys, monthSummary } = useChargingMonths(dashboard);
const visited = ref(props.editing);
watch(
  () => props.editing,
  (editing) => {
    if (editing) visited.value = true;
  },
);
const german = computed(() => dashboard?.language.value === "de");
const text = computed(() =>
  german.value
    ? {
        mode: "Ladeweise",
        fixedTime: "Ab fester Uhrzeit",
        startTime: "Täglicher Ladestart",
        months: "Aktive Monate",
        global: "Max SOC (%)",
        globalSummary: "Max SOC",
        saved: "Ladeweise",
        targetLabel: "Netzladeziel (%)",
        targetHint: "Globale Ladegrenze · gilt auch für Solarstrom.",
        hours: "Maximale Ladezeit je 24 Stunden",
        price: "Höchster Preis zum Laden (ct/kWh)",
        noPriceLimit: "Keine feste Preisgrenze.",
        neutral: "Speicher bei günstigem Strom schonen bis (ct/kWh)",
        neutralSummary: "Speicher schonen unter",
        neutralBand: "und oberhalb der Ladepreisgrenze",
        neutralInactive: "Speicher schonen: ohne Wirkung.",
        neutralUnavailable: "Grenze zum Schonen des Speichers nicht verfügbar.",
        unavailable: "Ladeweise nicht verfügbar.",
        readonly: "Keine Berechtigung zum Ändern der Ladeweise.",
        disconnected: "Keine Verbindung zu Home Assistant.",
        pending: "Ladeweise wird übernommen …",
        targetSummary: "Netzladeziel",
        modes: {
          smart: "Bedarfsgerecht laden",
          relative: "Günstigste Stunden nutzen",
          absolute: "Bis zu einem festen Preis laden",
          off: "Keine automatische Ladung",
        },
      }
    : {
        mode: "Charging method",
        fixedTime: "Start at a fixed time",
        startTime: "Daily charging start",
        months: "Active months",
        global: "Max SOC (%)",
        globalSummary: "Max SOC",
        saved: "Charging method",
        targetLabel: "Grid charge target (%)",
        targetHint: "Global charge limit · also applies to solar charging.",
        hours: "Maximum charging time per 24 hours",
        price: "Maximum price for charging (ct/kWh)",
        noPriceLimit: "No fixed price cap.",
        neutral: "Preserve battery energy below (ct/kWh)",
        neutralSummary: "Preserve battery energy below",
        neutralBand: "and above the charging price cap",
        neutralInactive: "Preserving battery energy: no effect.",
        neutralUnavailable: "Battery preservation threshold unavailable.",
        unavailable: "Charging method unavailable.",
        readonly: "You do not have permission to change the charging method.",
        disconnected: "Disconnected from Home Assistant.",
        pending: "Applying charging method …",
        targetSummary: "Grid charge target",
        modes: {
          smart: "Charge what is needed",
          relative: "Use the cheapest hours",
          absolute: "Charge below a fixed price",
          off: "No automatic charging",
        },
      },
);
const strategy = computed(() =>
  dashboard?.entity("select", "price_charge_strategy"),
);
type Strategy = "smart" | "relative" | "absolute" | "off";
const methods: Strategy[] = ["smart", "relative", "absolute", "off"];
const selected = computed(() => {
  if (fixedTime.active.value && dashboard?.connected.value) return "fixed_time";
  const value = strategy.value?.state?.state;
  return strategy.value?.available && methods.includes(value as Strategy)
    ? (value as Strategy)
    : null;
});
const editorMethod = computed(() =>
  fixedTime.selected.value ? "fixed_time" : selected.value,
);
const options = computed(() => strategy.value?.state?.attributes.options);
const blocked = computed(() => !strategy.value?.canControl || pending.value);
const status = computed(() => {
  if (!dashboard?.connected.value) return text.value.disconnected;
  if (!strategy.value?.available) return text.value.unavailable;
  if (!strategy.value.metadata.can_control) return text.value.readonly;
  return fixedTime.pending.value || strategy.value.pending
    ? text.value.pending
    : "";
});
const limit = computed(() => dashboard?.entity("number", "max_soc"));
const fixedLimit = computed(() =>
  dashboard?.entity("number", "timed_charge_max_soc"),
);
const numberFields = computed(() =>
  editorMethod.value === "fixed_time"
    ? [
        { key: "timed_charge_max_soc", label: text.value.targetLabel },
        { key: "max_soc", label: text.value.global },
      ]
    : editorMethod.value && editorMethod.value !== "off"
      ? [
          { key: "max_soc", label: text.value.targetLabel },
          editorMethod.value === "absolute"
            ? { key: "price_charge_max_price", label: text.value.price }
            : { key: "price_charge_hours", label: text.value.hours },
          { key: "price_charge_neutral_price", label: text.value.neutral },
        ]
      : [],
);
const chargeParameter = computed(() =>
  dashboard?.entity(
    "number",
    selected.value === "absolute"
      ? "price_charge_max_price"
      : "price_charge_hours",
  ),
);
const neutralSummary = computed(() => {
  const neutral = dashboard?.entity("number", "price_charge_neutral_price");
  const cap = dashboard?.entity("number", "price_charge_max_price");
  const neutralValue = finiteValue(neutral?.state?.state);
  const capValue = finiteValue(cap?.state?.state);
  if (
    !neutral?.available ||
    neutralValue === null ||
    (selected.value === "absolute" && (!cap?.available || capValue === null))
  )
    return text.value.neutralUnavailable;
  if (
    selected.value === "absolute" &&
    capValue !== null &&
    neutralValue <= capValue
  )
    return text.value.neutralInactive;
  return `${text.value.neutralSummary} ${neutral.displayValue}${selected.value === "absolute" ? ` ${text.value.neutralBand}` : ""}.`;
});
async function choose(method: Strategy) {
  if (
    blocked.value ||
    !Array.isArray(options.value) ||
    !options.value.includes(method)
  )
    return;
  if (selected.value === method) {
    if (fixedTime.selected.value) fixedTime.reset();
    return;
  }
  await fixedTime.leave(method, () =>
    dashboard!.perform("select", "price_charge_strategy", method),
  );
}
</script>

<template>
  <div class="dynamic-charging-settings">
    <div class="dynamic-charging-summary">
      <dl class="electricity-summary-rows">
        <div>
          <dt>{{ text.saved }}</dt>
          <dd>
            {{
              selected === "fixed_time"
                ? text.fixedTime
                : selected
                  ? text.modes[selected]
                  : text.unavailable
            }}
          </dd>
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
      <div v-if="selected && selected !== 'off'" class="electricity-targets">
        <div class="electricity-target">
          <span>{{ text.targetSummary }}</span
          ><strong>{{
            selected === "fixed_time"
              ? fixedLimit?.available
                ? fixedLimit.displayValue
                : "—"
              : limit?.available
                ? limit.displayValue
                : "—"
          }}</strong>
        </div>
        <div class="electricity-target">
          <span>{{
            selected === "fixed_time"
              ? text.globalSummary
              : selected === "absolute"
                ? text.price
                : text.hours
          }}</span
          ><strong>{{
            selected === "fixed_time"
              ? limit?.available
                ? limit.displayValue
                : "—"
              : chargeParameter?.available
                ? chargeParameter.displayValue
                : "—"
          }}</strong>
        </div>
      </div>
      <dl
        v-if="selected === 'fixed_time'"
        class="electricity-summary-rows fixed-time-month-summary"
      >
        <div>
          <dt>{{ text.months }}</dt>
          <dd>{{ monthSummary }}</dd>
        </div>
      </dl>
    </div>
    <p
      v-if="selected && selected !== 'off' && selected !== 'fixed_time'"
      class="electricity-muted dynamic-charging-neutral-summary"
    >
      {{ neutralSummary }}
    </p>
    <p v-if="strategy?.error" class="electricity-error" role="alert">
      {{ strategy.error }}
    </p>
    <p v-else-if="status" role="status" aria-live="polite">{{ status }}</p>
    <div v-if="visited" v-show="editing" class="dynamic-charging-editor">
      <h3>{{ text.mode }}</h3>
      <div
        class="dynamic-charging-methods"
        role="group"
        :aria-label="text.mode"
        :aria-busy="pending"
      >
        <button
          v-for="method in methods"
          :key="method"
          type="button"
          :data-strategy="method"
          :aria-pressed="editorMethod === method"
          :disabled="
            blocked || !Array.isArray(options) || !options.includes(method)
          "
          @click="choose(method)"
        >
          <strong>{{ text.modes[method] }}</strong>
        </button>
        <button
          type="button"
          data-strategy="fixed_time"
          :aria-pressed="editorMethod === 'fixed_time'"
          :disabled="blocked || !fixedTime.canConfigure.value"
          @click="fixedTime.choose"
        >
          <strong>{{ text.fixedTime }}</strong>
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
        v-if="fixedTime.error.value && editorMethod !== 'fixed_time'"
        class="electricity-error"
        role="alert"
      >
        {{
          german
            ? "Die Änderung ist fehlgeschlagen. Bitte erneut versuchen."
            : "The change failed. Please try again."
        }}
      </p>
      <ChargingNumberFields
        ref="numbers"
        :fields="numberFields"
        :soc-threshold-applies="editorMethod !== 'fixed_time'"
        :disabled="fixedTime.pending.value"
        @apply="emit('apply')"
      />
      <template v-if="editorMethod === 'fixed_time'"
        ><h3>{{ text.months }}</h3>
        <MonthSelection :entity-keys="monthKeys" always-expanded
      /></template>
      <template
        v-if="
          editorMethod &&
          editorMethod !== 'off' &&
          editorMethod !== 'fixed_time'
        "
      >
        <p class="electricity-muted">{{ text.targetHint }}</p>
        <template v-if="editorMethod !== 'absolute'">
          <p class="dynamic-charging-notice">{{ text.noPriceLimit }}</p>
        </template>
      </template>
    </div>
  </div>
</template>

<style>
.dynamic-charging-methods {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}
.dynamic-charging-methods button {
  text-align: left;
  padding: 12px;
  color: var(--primary-text-color, #212121);
}
.dynamic-charging-methods button[aria-pressed="true"] {
  border: 2px solid var(--primary-color, #03a9f4);
  background: var(--secondary-background-color, #f5f5f5);
  padding: 11px;
}
.dynamic-charging-methods strong {
  display: block;
  line-height: 1.5;
}
.dynamic-charging-editor > .entity-control {
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  padding: 12px 0;
}
.dynamic-charging-notice {
  border-left: 3px solid var(--primary-color, #03a9f4);
  padding-left: 12px;
}
@media (max-width: 700px) {
  .dynamic-charging-methods {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
