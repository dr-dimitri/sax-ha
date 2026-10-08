<script setup lang="ts">
import {
  computed,
  inject,
  nextTick,
  onBeforeUnmount,
  reactive,
  ref,
  useId,
  watch,
} from "vue";
import { SAX_DASHBOARD_KEY, type DashboardEntity } from "../ha";
import { finiteValue } from "../savings";

type Field = { key: string; label: string };
type LocalError = "invalid" | "order" | "failed" | "unavailable" | "readonly";
type Draft = {
  entityId: string | null;
  confirmed: string;
  value: string;
  edited: boolean;
};

const props = defineProps<{ fields: Field[] }>();
const emit = defineEmits<{ apply: [] }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const id = `sax-charging-number-${useId()}`;
const drafts = reactive<Record<string, Draft>>({});
const errors = reactive<Record<string, LocalError | undefined>>({});
const inputs = new Map<string, HTMLInputElement>();
const localPending = ref(false);
let revision = 0;
const text = computed(() =>
  dashboard?.language.value === "de"
    ? {
        pending: "Änderung wird an Home Assistant gesendet …",
        invalid: "Bitte einen gültigen Wert im erlaubten Bereich eingeben.",
        order:
          "Das Netzladeziel muss mindestens so hoch wie der Ladestart sein.",
        failed: "Die Änderung ist fehlgeschlagen. Bitte erneut versuchen.",
        unavailable: "Nicht verfügbar",
        readonly: "Keine Berechtigung zum Ändern",
        disconnected: "Keine Verbindung zu Home Assistant",
      }
    : {
        pending: "Sending change to Home Assistant …",
        invalid: "Please enter a valid value within the allowed range.",
        order:
          "The grid charge target must be at least as high as the start threshold.",
        failed: "The change failed. Please try again.",
        unavailable: "Unavailable",
        readonly: "You do not have permission to change this setting",
        disconnected: "Disconnected from Home Assistant",
      },
);
function entity(key: string): DashboardEntity | null {
  return dashboard?.entity("number", key) ?? null;
}
const pending = computed(
  () =>
    localPending.value ||
    props.fields.some((field) => entity(field.key)?.pending),
);
function blocked(key: string): boolean {
  return pending.value || !dashboard?.ready.value || !entity(key)?.canControl;
}
function numeric(value: string): number | null {
  return value.trim() === "" ? null : finiteValue(value);
}
function changed(key: string): boolean {
  const draft = drafts[key];
  return (
    !!draft && draft.edited && numeric(draft.value) !== numeric(draft.confirmed)
  );
}
function attribute(
  key: string,
  name: "min" | "max" | "step",
): number | undefined {
  if (key === "timed_charge_max_soc" && name === "max") {
    const globalDraft = props.fields.some((field) => field.key === "max_soc")
      ? numeric(drafts.max_soc?.value ?? "")
      : null;
    if (globalDraft !== null) return globalDraft;
  }
  const value = entity(key)?.state?.attributes[name];
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}
watch(
  () =>
    props.fields.map(({ key }) => [
      key,
      entity(key)?.metadata.entity_id,
      entity(key)?.state?.state,
    ]),
  () => {
    for (const { key } of props.fields) {
      const item = entity(key);
      const entityId = item?.metadata.entity_id ?? null;
      const confirmed = item?.state?.state ?? "";
      const previous = drafts[key];
      if (!previous || (entityId && entityId !== previous.entityId)) {
        revision += 1;
        drafts[key] = {
          entityId,
          confirmed,
          value:
            item?.available && numeric(confirmed) !== null ? confirmed : "",
          edited: false,
        };
        delete errors[key];
      } else if (entityId && confirmed !== previous.confirmed) {
        previous.confirmed = confirmed;
        // REQ-VUE-ELECTRICITY-TARIFF: unrelated HA updates must not replace a draft.
        if (
          !previous.edited ||
          numeric(previous.value) === numeric(confirmed)
        ) {
          previous.value =
            item?.available && numeric(confirmed) !== null ? confirmed : "";
          previous.edited = false;
          delete errors[key];
        }
      }
    }
  },
  { immediate: true, flush: "sync" },
);
onBeforeUnmount(() => {
  revision += 1;
});

function edit(key: string, event: Event): void {
  if (blocked(key)) return;
  const draft = drafts[key];
  if (!draft) return;
  draft.value = (event.target as HTMLInputElement).value;
  draft.edited = true;
  delete errors[key];
  dashboard?.clearControlError("number", key);
}
function setInput(key: string, element: unknown): void {
  if (element instanceof HTMLInputElement) inputs.set(key, element);
  else inputs.delete(key);
}
function error(key: string): string | null {
  const local = errors[key];
  return local ? text.value[local] : (entity(key)?.error ?? null);
}
function status(key: string): string {
  if (pending.value) return text.value.pending;
  if (!dashboard?.connected.value) return text.value.disconnected;
  if (!entity(key)?.available) return text.value.unavailable;
  if (!entity(key)?.metadata.can_control) return text.value.readonly;
  return "";
}
function fail(key: string, cause: LocalError): false {
  errors[key] = cause;
  inputs.get(key)?.focus();
  return false;
}
function requestApply(): void {
  if (!pending.value) emit("apply");
}

function reset(): boolean {
  if (pending.value) return false;
  for (const key of Object.keys(drafts)) {
    const item = entity(key);
    const confirmed = item?.state?.state ?? "";
    const value =
      item?.available && numeric(confirmed) !== null ? confirmed : "";
    drafts[key] = {
      entityId: item?.metadata.entity_id ?? null,
      confirmed,
      value,
      edited: false,
    };
    const input = inputs.get(key);
    if (input) input.value = value;
    delete errors[key];
    dashboard?.clearControlError("number", key);
  }
  return true;
}

async function submit(): Promise<boolean> {
  if (pending.value || !dashboard) return false;
  for (const { key } of props.fields) {
    const input = inputs.get(key);
    const draft = drafts[key];
    if (input && draft && input.value !== draft.value) {
      draft.value = input.value;
      draft.edited = true;
      delete errors[key];
      dashboard.clearControlError("number", key);
    }
  }
  const dirty = props.fields.filter(({ key }) => changed(key));
  if (!dirty.length) {
    for (const key of Object.keys(errors)) delete errors[key];
    return true;
  }
  for (const { key } of props.fields) {
    delete errors[key];
    const item = entity(key);
    if (!item?.available) {
      if (changed(key)) return fail(key, "unavailable");
      continue;
    }
    if (changed(key) && (!item.canControl || !dashboard.ready.value))
      return fail(key, "readonly");
    const value = numeric(drafts[key]?.value ?? "");
    const min = attribute(key, "min");
    const max = attribute(key, "max");
    const step = attribute(key, "step");
    if (
      value === null ||
      inputs.get(key)?.validity.badInput ||
      min === undefined ||
      max === undefined ||
      step === undefined ||
      step <= 0 ||
      min > max ||
      value < min ||
      (value > max && (key !== "timed_charge_max_soc" || changed(key))) ||
      !Number.isFinite((value - min) / step) ||
      Math.abs((value - min) / step - Math.round((value - min) / step)) > 1e-7
    )
      return fail(key, "invalid");
  }
  const minKey = "timed_charge_min_soc";
  const targetKey = "timed_charge_max_soc";
  const minChanged = dirty.some(({ key }) => key === minKey);
  const targetChanged = dirty.some(({ key }) => key === targetKey);
  if (minChanged || targetChanged) {
    const value = (key: string) =>
      props.fields.some((field) => field.key === key)
        ? numeric(drafts[key]?.value ?? "")
        : entity(key)?.available
          ? numeric(entity(key)?.state?.state ?? "")
          : null;
    const minimum = value(minKey);
    const target = value(targetKey);
    if (minimum !== null && target !== null && minimum > target) {
      if (minChanged && targetChanged) errors[minKey] = "order";
      return fail(targetChanged ? targetKey : minKey, "order");
    }
  }
  localPending.value = true;
  const current = revision;
  const identities = dirty.map(({ key }) => [key, drafts[key]?.entityId]);
  try {
    const saved = await dashboard.performChargingSettings(
      Object.fromEntries(dirty.map(({ key }) => [key, drafts[key]!.value])),
    );
    if (
      revision !== current ||
      identities.some(
        ([key, entityId]) => entity(key!)?.metadata.entity_id !== entityId,
      )
    )
      return false;
    if (!saved) {
      const orderError = dirty.some(
        ({ key }) => entity(key)?.error === text.value.order,
      );
      if (orderError && minChanged && targetChanged) {
        errors[minKey] = "order";
        errors[targetKey] = "order";
      }
      const failed = orderError
        ? (dirty.find(
            ({ key }) => key === (targetChanged ? targetKey : minKey),
          ) ?? dirty[0]!)
        : (dirty.find(({ key }) => entity(key)?.error) ?? dirty[0]!);
      if (!entity(failed.key)?.error) errors[failed.key] = "failed";
      localPending.value = false;
      await nextTick();
      if (revision === current) inputs.get(failed.key)?.focus();
    }
    return saved;
  } catch {
    localPending.value = false;
    await nextTick();
    if (revision === current) fail(dirty[0]!.key, "failed");
    return false;
  } finally {
    localPending.value = false;
  }
}

defineExpose({ submit, reset, pending });
</script>

<template>
  <div class="charging-number-fields" :aria-busy="pending">
    <form
      v-for="field in fields"
      :key="field.key"
      class="entity-control"
      :aria-busy="pending"
      @submit.prevent="requestApply"
    >
      <div class="entity-control__description">
        <label :for="`${id}-${field.key}`" class="entity-control__name">{{
          field.label
        }}</label>
        <p :id="`${id}-${field.key}-value`" class="entity-control__value">
          {{ entity(field.key)?.displayValue ?? text.unavailable }}
        </p>
      </div>
      <div class="entity-control__input">
        <input
          :id="`${id}-${field.key}`"
          :ref="(element) => setInput(field.key, element)"
          :value="drafts[field.key]?.value ?? ''"
          type="number"
          :min="attribute(field.key, 'min')"
          :max="attribute(field.key, 'max')"
          :step="attribute(field.key, 'step')"
          :disabled="blocked(field.key)"
          :aria-describedby="`${id}-${field.key}-value ${id}-${field.key}-status`"
          :aria-invalid="!!error(field.key)"
          required
          @input="edit(field.key, $event)"
          @invalid.prevent="requestApply"
        />
      </div>
      <div :id="`${id}-${field.key}-status`" class="entity-control__feedback">
        <p v-if="error(field.key)" class="entity-control__error" role="alert">
          {{ error(field.key) }}
        </p>
        <p v-else-if="status(field.key)" role="status" aria-live="polite">
          {{ status(field.key) }}
        </p>
      </div>
    </form>
  </div>
</template>
