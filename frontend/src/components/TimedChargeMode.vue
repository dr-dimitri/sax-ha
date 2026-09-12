<script setup lang="ts">
import { computed, inject, ref, useId } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";

const dashboard = inject(SAX_DASHBOARD_KEY);
const entity = computed(() => dashboard?.entity("select", "timed_charge_mode"));
const id = useId();
const fieldset = ref<HTMLFieldSetElement>();
const modes = ["standard", "adaptive"] as const;
const state = computed(() => entity.value?.state?.state);
const known = computed(
  () => entity.value?.available && modes.some((mode) => mode === state.value),
);
const blocked = computed(
  () => !known.value || !entity.value?.canControl || entity.value.pending,
);
const text = computed(() =>
  dashboard?.language.value === "de"
    ? {
        title: "Ladesteuerung",
        standard: "Min-/Max-SOC",
        adaptive: "Bedarfsgesteuert",
        standardDescription: "Startet unter Min-SOC und lädt bis Max-SOC.",
        adaptiveDescription:
          "Plant die nötige Ladung aus SAX-Verbrauch, PV-Prognose und Speicherstand.",
        hint: "Es wird nur die ausgewählte Ladesteuerung verwendet. Zeitfenster und aktive Monate gelten für beide.",
        unavailable: "Ladesteuerung nicht verfügbar",
        disconnected: "Keine Verbindung zu Home Assistant",
        readOnly: "Keine Berechtigung zum Ändern",
        pending: "Ladesteuerung wird an Home Assistant gesendet …",
      }
    : {
        title: "Charging control",
        standard: "Min/max SOC",
        adaptive: "Demand-based",
        standardDescription: "Starts below min SOC and charges up to max SOC.",
        adaptiveDescription:
          "Plans the required charge using SAX consumption, solar forecast and stored energy.",
        hint: "Only the selected charging control is used. Time windows and active months apply to both.",
        unavailable: "Charging control unavailable",
        disconnected: "Disconnected from Home Assistant",
        readOnly: "You do not have permission to change this setting",
        pending: "Sending charging control to Home Assistant …",
      },
);
const status = computed(() => {
  if (!dashboard?.connected.value) return text.value.disconnected;
  if (!known.value) return text.value.unavailable;
  if (!entity.value?.metadata.can_control) return text.value.readOnly;
  return entity.value.pending ? text.value.pending : "";
});

async function select(event: Event): Promise<void> {
  const desired = (event.target as HTMLInputElement).value;
  // REQ-HEMS-CONFIGURATION: both positions reflect the same confirmed HA state.
  for (const input of fieldset.value?.querySelectorAll("input") ?? [])
    input.checked = Boolean(known.value && input.value === state.value);
  if (blocked.value || desired === state.value) return;
  await dashboard?.perform("select", "timed_charge_mode", desired);
}
</script>

<template>
  <fieldset
    v-if="entity"
    ref="fieldset"
    class="timed-charge-mode"
    :aria-busy="entity.pending"
    :aria-describedby="`${id}-hint ${id}-status`"
  >
    <legend>{{ text.title }}</legend>
    <div class="timed-charge-mode__options">
      <label
        v-for="mode in modes"
        :key="mode"
        :class="{ 'timed-charge-mode__selected': known && state === mode }"
      >
        <input
          type="radio"
          :name="`${id}-mode`"
          :value="mode"
          :checked="known && state === mode"
          :disabled="blocked"
          :aria-labelledby="`${id}-${mode}`"
          :aria-describedby="`${id}-${mode}-description ${id}-status`"
          @change="select"
        />
        <span>
          <strong :id="`${id}-${mode}`">{{ text[mode] }}</strong>
          <span :id="`${id}-${mode}-description`">
            {{ text[`${mode}Description`] }}
          </span>
        </span>
      </label>
    </div>
    <p :id="`${id}-hint`">{{ text.hint }}</p>
    <div :id="`${id}-status`">
      <p v-if="entity.error" class="timed-charge-mode__error" role="alert">
        {{ entity.error }}
      </p>
      <p v-else-if="status" role="status">{{ status }}</p>
    </div>
  </fieldset>
</template>

<style>
.timed-charge-mode {
  margin: 0;
  min-width: 0;
  padding: 16px 20px;
  border: 1px solid var(--divider-color, #e0e0e0);
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  color: var(--primary-text-color, #212121);
}
.timed-charge-mode legend {
  padding: 0 8px;
  font-size: 18px;
  font-weight: 500;
}
.timed-charge-mode__options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.timed-charge-mode label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-height: 44px;
  padding: 14px;
  border: 2px solid var(--divider-color, #ddd);
  border-radius: 10px;
  cursor: pointer;
}
.timed-charge-mode label.timed-charge-mode__selected {
  border-color: var(--primary-color, #03a9f4);
  background: color-mix(
    in srgb,
    var(--primary-color, #03a9f4) 10%,
    transparent
  );
}
.timed-charge-mode label:has(:disabled) {
  cursor: not-allowed;
}
.timed-charge-mode input {
  font: inherit;
  flex-shrink: 0;
  margin: 2px 0 0;
  width: 20px;
  height: 20px;
  accent-color: var(--primary-color, #03a9f4);
}
.timed-charge-mode label:has(:focus-visible) {
  outline: 2px solid var(--primary-color, #03a9f4);
  outline-offset: 3px;
}
.timed-charge-mode strong,
.timed-charge-mode label span span {
  display: block;
}
.timed-charge-mode label span span {
  margin-top: 4px;
}
.timed-charge-mode p,
.timed-charge-mode label span span {
  color: var(--secondary-text-color, #666);
  line-height: 1.5;
  overflow-wrap: anywhere;
}
.timed-charge-mode p {
  margin: 12px 0 0;
}
.timed-charge-mode p.timed-charge-mode__error {
  color: var(--error-color, #b71c1c);
}
@media (max-width: 480px) {
  .timed-charge-mode__options {
    grid-template-columns: 1fr;
  }
}
</style>
