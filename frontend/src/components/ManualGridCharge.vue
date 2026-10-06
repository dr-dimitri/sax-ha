<script setup lang="ts">
import { computed, inject, ref, useId } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";

const dashboard = inject(SAX_DASHBOARD_KEY);
const id = `manual-grid-charge-${useId()}`;
const powerDraft = ref("1000");
const powerInput = ref<HTMLInputElement>();
const invalidSubmittedPower = ref(false);
const action = computed(() => dashboard?.manualGridCharge.value);
const storage = computed(() => dashboard?.entity("switch", "storage_switch"));
const chargePower = computed(() => {
  const sensor = dashboard?.entity("sensor", "charge_power");
  return sensor?.metadata.device_id &&
    sensor.metadata.device_id === storage.value?.metadata.device_id
    ? sensor
    : null;
});
const blocked = computed(
  () => !action.value?.canControl || action.value.pending,
);
const invalidPower = computed(() => {
  const power = powerDraft.value.trim() ? Number(powerDraft.value) : NaN;
  return (
    !Number.isInteger(power) ||
    power < 1 ||
    power > (action.value?.maxPower ?? 32768)
  );
});
const text = computed(() =>
  dashboard?.language.value === "de"
    ? {
        title: "Manuelles Netzladen",
        power: "Ladeleistung (W)",
        range: `Ganze Watt von 1 bis ${action.value?.maxPower ?? 32768}. Voreinstellung: 1000 W.`,
        start: "Netzladen aktivieren",
        stop: "Netzladen abschalten",
        telemetry: "Bestätigte aktuelle Ladeleistung",
        hint: "Die Max-SOC-Sperre hat Vorrang. Abschalten beendet den manuellen Ladeauftrag; aktive Ladeautomatiken können danach übernehmen.",
        pending: "Netzladebefehl wird an das Gerät gesendet …",
        loading: "Die Entitäten werden geladen …",
        disconnected: "Keine Verbindung zu Home Assistant.",
        unavailable: "Die Speichersteuerung ist nicht verfügbar.",
        forbidden: "Keine Berechtigung zur Speichersteuerung.",
      }
    : {
        title: "Manual grid charging",
        power: "Charging power (W)",
        range: `Whole watts from 1 to ${action.value?.maxPower ?? 32768}. Default: 1000 W.`,
        start: "Enable grid charging",
        stop: "Disable grid charging",
        telemetry: "Confirmed current charging power",
        hint: "The maximum SOC lock takes priority. Disabling ends the manual charging request; active charging automations may then take over.",
        pending: "Sending grid charging command to the device …",
        loading: "Loading entities …",
        disconnected: "Disconnected from Home Assistant.",
        unavailable: "Battery control is unavailable.",
        forbidden: "You do not have permission to control the battery.",
      },
);
const status = computed(() => {
  if (!dashboard?.connected.value) return text.value.disconnected;
  if (action.value?.pending) return text.value.pending;
  if (!dashboard.ready.value && !dashboard.error.value)
    return text.value.loading;
  if (!storage.value?.available || !storage.value.metadata.device_id)
    return text.value.unavailable;
  if (!action.value?.canControl) return text.value.forbidden;
  return "";
});

function changeDraft(event: Event): void {
  powerDraft.value = (event.target as HTMLInputElement).value;
  invalidSubmittedPower.value = false;
}

async function start(): Promise<void> {
  if (blocked.value || !dashboard) return;
  powerDraft.value = powerInput.value?.value ?? powerDraft.value;
  invalidSubmittedPower.value = invalidPower.value;
  await dashboard.startGridCharge(powerDraft.value);
}

async function stop(): Promise<void> {
  if (blocked.value || !dashboard) return;
  invalidSubmittedPower.value = false;
  await dashboard.stopGridCharge();
}
</script>

<template>
  <section
    class="manual-grid-charge"
    :aria-labelledby="`${id}-title`"
    :aria-busy="action?.pending ?? false"
  >
    <h2 :id="`${id}-title`">{{ text.title }}</h2>
    <p :id="`${id}-hint`" class="manual-grid-charge__hint">{{ text.hint }}</p>
    <p v-if="chargePower" class="manual-grid-charge__telemetry">
      {{ text.telemetry }}: {{ chargePower.displayValue }}
    </p>
    <form novalidate @submit.prevent="start">
      <div class="manual-grid-charge__power">
        <label :for="`${id}-power`">{{ text.power }}</label>
        <input
          :id="`${id}-power`"
          ref="powerInput"
          type="number"
          :value="powerDraft"
          min="1"
          :max="action?.maxPower ?? 32768"
          step="1"
          required
          :disabled="blocked"
          :aria-describedby="`${id}-range ${id}-feedback`"
          :aria-invalid="Boolean(action?.error && invalidSubmittedPower)"
          @input="changeDraft"
        />
        <p :id="`${id}-range`" class="manual-grid-charge__range">
          {{ text.range }}
        </p>
      </div>
      <div class="manual-grid-charge__actions">
        <button
          type="submit"
          :disabled="blocked"
          :aria-describedby="`${id}-hint ${id}-feedback`"
        >
          {{ text.start }}
        </button>
        <button
          type="button"
          :disabled="blocked"
          :aria-describedby="`${id}-hint ${id}-feedback`"
          @click="stop"
        >
          {{ text.stop }}
        </button>
      </div>
    </form>
    <div :id="`${id}-feedback`" class="manual-grid-charge__feedback">
      <p v-if="action?.error" class="manual-grid-charge__error" role="alert">
        {{ action.error }}
      </p>
      <p v-else-if="status" role="status">{{ status }}</p>
    </div>
  </section>
</template>

<style>
.manual-grid-charge {
  min-width: 0;
  padding: 24px;
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  color: var(--primary-text-color, #212121);
  box-shadow: var(--ha-card-box-shadow, none);
}
.manual-grid-charge h2 {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.5;
}
.manual-grid-charge__hint,
.manual-grid-charge__telemetry,
.manual-grid-charge__range,
.manual-grid-charge__feedback {
  color: var(--secondary-text-color, #666);
  line-height: 1.6;
}
.manual-grid-charge__hint {
  margin: 0 0 16px;
}
.manual-grid-charge__telemetry {
  margin: 0 0 16px;
}
.manual-grid-charge form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px 24px;
}
.manual-grid-charge__power {
  display: grid;
  grid-template-columns: auto 120px;
  align-items: center;
  gap: 8px 12px;
}
.manual-grid-charge__power label {
  font-weight: 500;
}
.manual-grid-charge__range {
  grid-column: 1 / -1;
  margin: 0;
  font-size: 0.9em;
}
.manual-grid-charge__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.manual-grid-charge input,
.manual-grid-charge button {
  min-height: 44px;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
  padding: 8px 12px;
  border: 1px solid var(--divider-color, #767676);
  border-radius: 6px;
  background: var(--card-background-color, #fff);
  color: inherit;
  font: inherit;
}
.manual-grid-charge button {
  border-color: var(--primary-color, #03a9f4);
  cursor: pointer;
}
.manual-grid-charge :disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
.manual-grid-charge input:focus-visible,
.manual-grid-charge button:focus-visible {
  outline: 2px solid var(--primary-color, #03a9f4);
  outline-offset: 2px;
}
.manual-grid-charge__feedback:empty {
  display: none;
}
.manual-grid-charge__feedback p {
  margin: 16px 0 0;
}
.manual-grid-charge__error {
  color: var(--error-color, #b71c1c);
}
@media (max-width: 600px) {
  .manual-grid-charge {
    padding: 20px;
  }
  .manual-grid-charge__power {
    grid-template-columns: minmax(0, 1fr) 104px;
    width: 100%;
  }
  .manual-grid-charge__actions,
  .manual-grid-charge__actions button {
    width: 100%;
  }
}
@container sax-content (min-width: 860px) {
  .manual-grid-charge {
    padding: 18px;
  }
  .manual-grid-charge h2 {
    font-size: 16px;
  }
}
</style>
