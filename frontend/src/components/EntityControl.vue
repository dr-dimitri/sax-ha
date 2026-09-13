<script setup lang="ts">
import {
  computed,
  inject,
  nextTick,
  onBeforeUnmount,
  ref,
  shallowRef,
  useId,
  watch,
} from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";

const props = defineProps<{
  domain: "switch" | "number" | "time" | "select";
  entityKey: string;
  label?: string;
  confirmSwitch?: boolean;
  hideConfirmedLabel?: boolean;
  monthTile?: boolean;
  timeUnit?: boolean;
}>();

const dashboard = inject(SAX_DASHBOARD_KEY);
const entity = computed(() => dashboard?.entity(props.domain, props.entityKey));
const id = useId();
const inputId = `sax-control-${id}`;
const statusId = `sax-status-${id}`;
const valueId = `sax-value-${id}`;
const draft = ref("");
const dialog = ref<HTMLDialogElement>();
const confirmation = shallowRef<{
  entityId: string;
  domain: string;
  key: string;
  sourceState: string;
  desired: boolean;
} | null>(null);
const state = computed(() => entity.value?.state?.state ?? "");
const attributes = computed(() => entity.value?.state?.attributes ?? {});
const options = computed(() => {
  const values = attributes.value.options;
  return Array.isArray(values)
    ? values.filter((value): value is string => typeof value === "string")
    : [];
});
const language = computed(() => dashboard?.language.value ?? "en");
const descriptionIds = computed(() =>
  props.domain === "switch" ? statusId : `${valueId} ${statusId}`,
);
const confirmedDisplayValue = computed(() => {
  const value = entity.value?.displayValue;
  const showTimeUnit =
    props.timeUnit &&
    props.domain === "time" &&
    language.value === "de" &&
    entity.value?.available &&
    /^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(state.value);
  return showTimeUnit ? `${value} Uhr` : value;
});
const text = computed(() =>
  language.value === "de"
    ? {
        apply: "Übernehmen",
        confirmed: "Bestätigter Wert",
        disconnected: "Keine Verbindung zu Home Assistant",
        unavailable: "Nicht verfügbar",
        readOnly: "Keine Berechtigung zum Ändern",
        pending: "Änderung wird an Home Assistant gesendet …",
        cancel: "Abbrechen",
        turnOn: "Einschalten",
        turnOff: "Ausschalten",
        confirmationTitle: confirmation.value?.desired
          ? "Speicher einschalten?"
          : "Speicher ausschalten?",
        confirmationQuestion: confirmation.value?.desired
          ? "Möchten Sie den Speicher wirklich einschalten?"
          : "Möchten Sie den Speicher wirklich ausschalten?",
      }
    : {
        apply: "Apply",
        confirmed: "Confirmed value",
        disconnected: "Disconnected from Home Assistant",
        unavailable: "Unavailable",
        readOnly: "You do not have permission to change this setting",
        pending: "Sending change to Home Assistant …",
        cancel: "Cancel",
        turnOn: "Turn on",
        turnOff: "Turn off",
        confirmationTitle: confirmation.value?.desired
          ? "Turn on the battery?"
          : "Turn off the battery?",
        confirmationQuestion: confirmation.value?.desired
          ? "Do you really want to turn on the battery?"
          : "Do you really want to turn off the battery?",
      },
);

const blocked = computed(
  () =>
    !entity.value?.canControl ||
    entity.value.pending ||
    (props.monthTile && state.value !== "on" && state.value !== "off"),
);
const status = computed(() => {
  if (!dashboard?.connected.value) return text.value.disconnected;
  if (!entity.value?.available) return text.value.unavailable;
  if (props.monthTile && state.value !== "on" && state.value !== "off")
    return text.value.unavailable;
  if (!entity.value.metadata.can_control) return text.value.readOnly;
  return entity.value.pending ? text.value.pending : "";
});

function initialDraft(value: string): string {
  if (!entity.value?.available) return "";
  return props.domain === "time" ? minute(value) : value;
}

function minute(value: string): string {
  return /^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(value)
    ? value.slice(0, 5)
    : "";
}

function changeDraft(event: Event): void {
  const input = event.target as HTMLInputElement;
  draft.value = props.domain === "time" ? minute(input.value) : input.value;
  input.value = draft.value;
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
  if (
    blocked.value ||
    !dashboard ||
    (props.domain !== "number" && props.domain !== "time")
  )
    return;
  await dashboard.perform(
    props.domain,
    props.entityKey,
    props.domain === "time" && draft.value ? `${draft.value}:00` : draft.value,
  );
}

function cancelConfirmation(): void {
  confirmation.value = null;
  if (dialog.value?.open) dialog.value.close();
}

function closedConfirmation(): void {
  if (!dialog.value?.open) confirmation.value = null;
}

// REQ-VUE-GENERAL: confirmation applies only to the state and entity shown.
watch(
  [
    () => entity.value?.metadata.entity_id,
    state,
    blocked,
    () => props.domain,
    () => props.entityKey,
    () => props.confirmSwitch,
  ],
  cancelConfirmation,
  { flush: "sync" },
);
onBeforeUnmount(cancelConfirmation);

async function confirmChange(): Promise<void> {
  const request = confirmation.value;
  cancelConfirmation();
  if (
    !request ||
    blocked.value ||
    !dashboard ||
    request.entityId !== entity.value?.metadata.entity_id ||
    request.sourceState !== state.value ||
    request.domain !== props.domain ||
    request.key !== props.entityKey
  )
    return;
  await dashboard.perform(props.domain, props.entityKey, request.desired);
}

async function changeSwitch(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const desired = input.checked;
  // REQ-VUE-ENTITY-BINDING: service acknowledgement is not a state update.
  input.checked = state.value === "on";
  if (blocked.value || !dashboard) return;
  if (props.confirmSwitch && entity.value) {
    const request = {
      entityId: entity.value.metadata.entity_id,
      domain: props.domain,
      key: props.entityKey,
      sourceState: state.value,
      desired,
    };
    confirmation.value = request;
    await nextTick();
    if (confirmation.value === request && !blocked.value)
      dialog.value?.showModal();
    return;
  }
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
    :class="{
      'entity-control--month': monthTile,
      'entity-control--selected':
        monthTile && entity.available && state === 'on',
    }"
    :aria-busy="entity.pending"
    @submit.prevent="submitDraft"
  >
    <label
      v-if="monthTile && domain === 'switch'"
      :for="inputId"
      class="entity-control__switch-target entity-control__month-target"
    >
      <span class="entity-control__name">{{ label ?? entity.name }}</span>
      <input
        :id="inputId"
        type="checkbox"
        role="switch"
        :checked="entity.available && state === 'on'"
        :indeterminate="
          !entity.available || (state !== 'on' && state !== 'off')
        "
        :disabled="blocked"
        :aria-describedby="statusId"
        @change="changeSwitch"
      />
    </label>
    <template v-else>
      <div class="entity-control__description">
        <label :for="inputId" class="entity-control__name">{{
          label ?? entity.name
        }}</label>
        <p
          v-if="domain !== 'switch'"
          :id="valueId"
          class="entity-control__value"
        >
          <span v-if="!hideConfirmedLabel">{{ text.confirmed }}:</span>
          {{ confirmedDisplayValue }}
        </p>
      </div>

      <div class="entity-control__input">
        <label
          v-if="domain === 'switch'"
          :for="inputId"
          class="entity-control__switch-target"
        >
          <input
            :id="inputId"
            type="checkbox"
            role="switch"
            :checked="state === 'on'"
            :disabled="blocked"
            :aria-describedby="descriptionIds"
            @change="changeSwitch"
          />
        </label>
        <select
          v-else-if="domain === 'select'"
          :id="inputId"
          :value="entity.available ? state : ''"
          :disabled="blocked"
          :aria-describedby="descriptionIds"
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
            :value="draft"
            :type="domain === 'number' ? 'number' : 'time'"
            :min="domain === 'number' ? numberAttribute('min') : undefined"
            :max="domain === 'number' ? numberAttribute('max') : undefined"
            :step="domain === 'number' ? numberAttribute('step') : 60"
            :disabled="blocked"
            :aria-describedby="descriptionIds"
            required
            @input="changeDraft"
          />
          <button type="submit" :disabled="blocked || draft === ''">
            {{ text.apply }}
          </button>
        </template>
      </div>
    </template>

    <div :id="statusId" class="entity-control__feedback">
      <p v-if="entity.error" class="entity-control__error" role="alert">
        {{ entity.error }}
      </p>
      <p v-else-if="status" role="status">{{ status }}</p>
    </div>
    <dialog
      v-if="confirmSwitch"
      ref="dialog"
      class="entity-control__confirmation"
      :aria-labelledby="`${id}-confirmation-title`"
      :aria-describedby="`${id}-confirmation-question`"
      @cancel.prevent="cancelConfirmation"
      @close="closedConfirmation"
    >
      <h3 :id="`${id}-confirmation-title`">{{ text.confirmationTitle }}</h3>
      <p :id="`${id}-confirmation-question`">{{ text.confirmationQuestion }}</p>
      <div class="entity-control__confirmation-actions">
        <button type="button" autofocus @click="cancelConfirmation">
          {{ text.cancel }}
        </button>
        <button
          type="button"
          :disabled="blocked || !confirmation"
          @click="confirmChange"
        >
          {{ confirmation?.desired ? text.turnOn : text.turnOff }}
        </button>
      </div>
    </dialog>
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

.entity-control__switch-target {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 44px;
  cursor: pointer;
}

.entity-control__switch-target:has(:disabled) {
  cursor: not-allowed;
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
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  min-height: 22px;
  margin: 0;
  padding: 0;
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

.entity-control__confirmation {
  width: min(440px, calc(100vw - 32px));
  max-height: calc(100vh - 32px);
  padding: 24px;
  border: 1px solid var(--divider-color, #767676);
  border-radius: 12px;
  background: var(--card-background-color, #fff);
  color: var(--primary-text-color, #212121);
  overflow: auto;
}

.entity-control__confirmation::backdrop {
  background: rgb(0 0 0 / 55%);
}

.entity-control__confirmation h3 {
  margin: 0;
  font-size: 20px;
  line-height: 1.4;
}

.entity-control__confirmation p {
  margin: 16px 0 24px;
  line-height: 1.6;
}

.entity-control__confirmation-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12px;
}
@container sax-content (min-width: 860px) {
  .entity-control {
    gap: 8px 12px;
    padding: 14px;
  }
  .entity-control__description {
    flex-basis: 140px;
  }
  .entity-control__value {
    margin-top: 2px;
    font-size: 14px;
  }
  .entity-control input[type="number"] {
    width: 104px;
  }
}
</style>
