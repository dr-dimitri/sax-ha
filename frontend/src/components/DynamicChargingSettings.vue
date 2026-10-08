<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import ChargingNumberFields from "./ChargingNumberFields.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import { finiteValue } from "../savings";

const props = defineProps<{ editing: boolean }>();
const emit = defineEmits<{ apply: [] }>();
const numbers = ref<InstanceType<typeof ChargingNumberFields>>();
defineExpose({
  submit: () => numbers.value?.submit() ?? Promise.resolve(true),
  pending: computed(() => numbers.value?.pending ?? false),
});
const dashboard = inject(SAX_DASHBOARD_KEY);
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
  const value = strategy.value?.state?.state;
  return strategy.value?.available && methods.includes(value as Strategy)
    ? (value as Strategy)
    : null;
});
const options = computed(() => strategy.value?.state?.attributes.options);
const blocked = computed(
  () =>
    !strategy.value?.canControl ||
    strategy.value.pending ||
    numbers.value?.pending,
);
const status = computed(() => {
  if (!dashboard?.connected.value) return text.value.disconnected;
  if (!strategy.value?.available) return text.value.unavailable;
  if (!strategy.value.metadata.can_control) return text.value.readonly;
  return strategy.value.pending ? text.value.pending : "";
});
const limit = computed(() => dashboard?.entity("number", "max_soc"));
const numberFields = computed(() =>
  selected.value && selected.value !== "off"
    ? [
        { key: "max_soc", label: text.value.targetLabel },
        selected.value === "absolute"
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
    !options.value.includes(method) ||
    selected.value === method
  )
    return;
  await dashboard?.perform("select", "price_charge_strategy", method);
}
</script>

<template>
  <div class="dynamic-charging-settings">
    <div class="dynamic-charging-summary">
      <dl class="electricity-summary-rows">
        <div>
          <dt>{{ text.saved }}</dt>
          <dd>
            {{ selected ? text.modes[selected] : text.unavailable }}
          </dd>
        </div>
      </dl>
      <div v-if="selected && selected !== 'off'" class="electricity-targets">
        <div class="electricity-target">
          <span>{{ text.targetSummary }}</span
          ><strong>{{ limit?.available ? limit.displayValue : "—" }}</strong>
        </div>
        <div class="electricity-target">
          <span>{{ selected === "absolute" ? text.price : text.hours }}</span
          ><strong>{{
            chargeParameter?.available ? chargeParameter.displayValue : "—"
          }}</strong>
        </div>
      </div>
    </div>
    <p
      v-if="selected && selected !== 'off'"
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
        :aria-busy="strategy?.pending ?? false"
      >
        <button
          v-for="method in methods"
          :key="method"
          type="button"
          :data-strategy="method"
          :aria-pressed="selected === method"
          :disabled="
            blocked || !Array.isArray(options) || !options.includes(method)
          "
          @click="choose(method)"
        >
          <strong>{{ text.modes[method] }}</strong>
        </button>
      </div>
      <ChargingNumberFields
        ref="numbers"
        :fields="numberFields"
        @apply="emit('apply')"
      />
      <template v-if="selected && selected !== 'off'">
        <p class="electricity-muted">{{ text.targetHint }}</p>
        <template v-if="selected !== 'absolute'">
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
