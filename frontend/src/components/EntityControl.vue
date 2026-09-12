<script setup lang="ts">
import { computed, inject, ref, useId, watch } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";

const props = defineProps<{
  domain: "switch" | "number" | "time" | "select";
  entityKey: string;
}>();

const dashboard = inject(SAX_DASHBOARD_KEY);
const entity = computed(() => dashboard?.entity(props.domain, props.entityKey));
const id = useId();
const inputId = `sax-control-${id}`;
const statusId = `sax-status-${id}`;
const valueId = `sax-value-${id}`;
const draft = ref("");
const state = computed(() => entity.value?.state?.state ?? "");
const attributes = computed(() => entity.value?.state?.attributes ?? {});
const options = computed(() => {
  const values = attributes.value.options;
  return Array.isArray(values)
    ? values.filter((value): value is string => typeof value === "string")
    : [];
});
const language = computed(() => dashboard?.language.value ?? "en");
const text = computed(() =>
  language.value === "de"
    ? {
        apply: "Übernehmen",
        confirmed: "Bestätigter Wert",
        disconnected: "Keine Verbindung zu Home Assistant",
        unavailable: "Nicht verfügbar",
        readOnly: "Keine Berechtigung zum Ändern",
        pending: "Änderung wird an Home Assistant gesendet …",
      }
    : {
        apply: "Apply",
        confirmed: "Confirmed value",
        disconnected: "Disconnected from Home Assistant",
        unavailable: "Unavailable",
        readOnly: "You do not have permission to change this setting",
        pending: "Sending change to Home Assistant …",
      },
);

const blocked = computed(
  () => !entity.value?.canControl || entity.value.pending,
);
const status = computed(() => {
  if (!dashboard?.connected.value) return text.value.disconnected;
  if (!entity.value?.available) return text.value.unavailable;
  if (!entity.value.metadata.can_control) return text.value.readOnly;
  return entity.value.pending ? text.value.pending : "";
});

function initialDraft(value: string): string {
  if (!entity.value?.available) return "";
  return value;
}

watch(
  [() => entity.value?.metadata.entity_id, () => state.value],
  ([, value]) => {
    draft.value = initialDraft(value);
  },
  { immediate: true },
);

function numberAttribute(key: "min" | "max" | "step"): number | undefined {
  const value = attributes.value[key];
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

function optionLabel(value: string): string {
  return entity.value?.metadata.states[value] ?? value;
}

async function submitDraft(): Promise<void> {
  if (blocked.value || !dashboard) return;
  await dashboard.perform(props.domain, props.entityKey, draft.value);
}

async function changeSwitch(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const desired = input.checked;
  // REQ-VUE-ENTITY-BINDING: service acknowledgement is not a state update.
  input.checked = state.value === "on";
  if (blocked.value || !dashboard) return;
  await dashboard.perform(props.domain, props.entityKey, desired);
}

async function changeSelect(event: Event): Promise<void> {
  const input = event.target as HTMLSelectElement;
  const desired = input.value;
  input.value = state.value;
  if (blocked.value || !dashboard) return;
  await dashboard.perform(props.domain, props.entityKey, desired);
}
</script>

<template>
  <form
    v-if="entity"
    class="entity-control"
    :aria-busy="entity.pending"
    @submit.prevent="submitDraft"
  >
    <div class="entity-control__description">
      <label :for="inputId" class="entity-control__name">{{
        entity.name
      }}</label>
      <p :id="valueId" class="entity-control__value">
        <span>{{ text.confirmed }}:</span> {{ entity.displayValue }}
      </p>
    </div>

    <div class="entity-control__input">
      <input
        v-if="domain === 'switch'"
        :id="inputId"
        type="checkbox"
        role="switch"
        :checked="state === 'on'"
        :disabled="blocked"
        :aria-describedby="`${valueId} ${statusId}`"
        @change="changeSwitch"
      />
      <select
        v-else-if="domain === 'select'"
        :id="inputId"
        :value="entity.available ? state : ''"
        :disabled="blocked"
        :aria-describedby="`${valueId} ${statusId}`"
        @change="changeSelect"
      >
        <option v-if="!entity.available" value="" disabled>
          {{ text.unavailable }}
        </option>
        <option v-for="option in options" :key="option" :value="option">
          {{ optionLabel(option) }}
        </option>
      </select>
      <template v-else>
        <input
          :id="inputId"
          v-model="draft"
          :type="domain === 'number' ? 'number' : 'time'"
          :min="domain === 'number' ? numberAttribute('min') : undefined"
          :max="domain === 'number' ? numberAttribute('max') : undefined"
          :step="domain === 'number' ? numberAttribute('step') : 1"
          :disabled="blocked"
          :aria-describedby="`${valueId} ${statusId}`"
          required
        />
        <button type="submit" :disabled="blocked || draft === ''">
          {{ text.apply }}
        </button>
      </template>
    </div>

    <div :id="statusId" class="entity-control__feedback">
      <p v-if="entity.error" class="entity-control__error" role="alert">
        {{ entity.error }}
      </p>
      <p v-else-if="status" role="status">{{ status }}</p>
    </div>
  </form>
</template>

<style>
.entity-control {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 24px;
  padding: 20px;
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  color: var(--primary-text-color, #212121);
  box-shadow: var(--ha-card-box-shadow, none);
}

.entity-control__description {
  flex: 1 1 200px;
  min-width: 0;
  overflow-wrap: anywhere;
}

.entity-control__name {
  display: block;
  font-weight: 500;
  line-height: 1.5;
}

.entity-control__value {
  margin: 4px 0 0;
  color: var(--secondary-text-color, #666);
  font-size: 0.9em;
  line-height: 1.5;
}

.entity-control__input {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 100%;
}

.entity-control input,
.entity-control select,
.entity-control button {
  min-height: 44px;
  max-width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--divider-color, #767676);
  border-radius: 6px;
  color: inherit;
  background: var(--card-background-color, #fff);
  font: inherit;
}

.entity-control input[type="number"] {
  width: 120px;
}

.entity-control input[type="checkbox"] {
  width: 28px;
  margin: 0 8px;
  accent-color: var(--primary-color, #03a9f4);
  cursor: pointer;
}

.entity-control button {
  border-color: var(--primary-color, #03a9f4);
  color: var(--primary-text-color, #212121);
  cursor: pointer;
}

.entity-control :disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.entity-control input:focus-visible,
.entity-control select:focus-visible,
.entity-control button:focus-visible {
  outline: 2px solid var(--primary-color, #03a9f4);
  outline-offset: 2px;
}

.entity-control__feedback {
  flex-basis: 100%;
  color: var(--secondary-text-color, #666);
  line-height: 1.5;
}

.entity-control__feedback:empty {
  display: none;
}

.entity-control__feedback p {
  margin: 0;
}

.entity-control__error {
  color: var(--error-color, #b71c1c);
}
</style>
