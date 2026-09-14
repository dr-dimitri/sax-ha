<script setup lang="ts">
import {
  computed,
  inject,
  nextTick,
  onBeforeUnmount,
  ref,
  useId,
  watch,
} from "vue";
import SensorPicker from "./SensorPicker.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import type { GridServingForecastSource, HomeAssistant } from "../types";

const props = defineProps<{ hass?: HomeAssistant }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const id = `grid-serving-source-${useId()}`;
const section = ref<HTMLElement>();
const editButton = ref<HTMLButtonElement>();
const confirmed = ref<GridServingForecastSource | null>(null);
const draft = ref<string | null>(null);
const revision = ref("");
const editing = ref(false);
const pending = ref<"loading" | "saving" | null>(null);
const errorCode = ref<string | null>(null);
const saved = ref(false);
let disposed = false;
let refreshRequested = false;
onBeforeUnmount(() => {
  disposed = true;
});
const connected = computed(() => dashboard?.connected.value ?? false);
const text = computed(() =>
  dashboard?.language.value === "de"
    ? {
        title: "Solarprognose für die Ladepause",
        hint: "Wähle einen Energiesensor für den heute noch erwarteten Solarertrag (Wh, kWh oder MWh). Liegt der Wert unter der Mindest-PV-Prognose, greift die Ladepause nicht. Bei einer Mindest-PV-Prognose von 0 kWh wird diese Bedingung nicht geprüft.",
        source: "PV-Sensor (heute verbleibend)",
        none: "Keine Quelle ausgewählt",
        missing:
          "Ohne Quelle greift die Ladepause bei einer Mindest-PV-Prognose über 0 kWh nicht.",
        readonly: "Nur Administratoren können die Quelle ändern.",
        edit: "Bearbeiten",
        save: "Speichern",
        cancel: "Abbrechen",
        loading: "Auswahl wird geladen …",
        saving: "Auswahl wird gespeichert …",
        saved:
          "Quelle gespeichert. Die Ladepause wird anhand der neuen Prognose geprüft.",
        reload: "Aktuelle Auswahl laden",
        conflict:
          "Die Quelle wurde zwischenzeitlich geändert. Dein Entwurf bleibt erhalten. Lade die aktuelle Auswahl, bevor du erneut bearbeitest.",
        disconnected:
          "Keine Verbindung zu Home Assistant. Dein Entwurf bleibt erhalten.",
        invalid_sensor:
          "Dieser Sensor ist nicht mehr verfügbar. Wähle einen vorhandenen Energiesensor.",
        invalid_unit:
          "Wähle einen Energiesensor in Wh, kWh oder MWh. Ein Leistungssensor in W oder kW ist ungeeignet.",
        forbidden: "Du bist nicht berechtigt, diese Quelle zu bearbeiten.",
        failed:
          "Die Auswahl konnte nicht übernommen werden. Dein Entwurf bleibt erhalten. Bitte erneut versuchen.",
      }
    : {
        title: "Solar forecast for the charging pause",
        hint: "Choose an energy sensor for the solar yield still expected today (Wh, kWh or MWh). Below the minimum PV forecast, the charging pause does not apply. A minimum of 0 kWh skips this condition.",
        source: "PV sensor (remaining today)",
        none: "No source selected",
        missing:
          "Without a source, the charging pause does not apply when the minimum PV forecast is above 0 kWh.",
        readonly: "Only administrators can change the source.",
        edit: "Edit",
        save: "Save",
        cancel: "Cancel",
        loading: "Loading selection …",
        saving: "Saving selection …",
        saved:
          "Source saved. The charging pause is checked against the new forecast.",
        reload: "Load current selection",
        conflict:
          "The source changed elsewhere. Your draft is preserved. Load the current selection before editing again.",
        disconnected:
          "Disconnected from Home Assistant. Your draft is preserved.",
        invalid_sensor:
          "This sensor is no longer available. Select an existing energy sensor.",
        invalid_unit:
          "Choose an energy sensor in Wh, kWh or MWh. Power sensors in W or kW are not suitable.",
        forbidden: "You do not have permission to edit this source.",
        failed:
          "The selection could not be saved. Your draft is preserved. Please try again.",
      },
);
const error = computed(() =>
  errorCode.value
    ? (text.value[errorCode.value as keyof typeof text.value] ??
      text.value.failed)
    : null,
);
const sourceName = computed(() => {
  const source = confirmed.value?.pv_sensor;
  if (!source) return text.value.none;
  const name = props.hass?.states[source]?.attributes.friendly_name;
  return typeof name === "string" ? name : source;
});
const energyHass = computed(() =>
  props.hass
    ? {
        ...props.hass,
        states: Object.fromEntries(
          Object.entries(props.hass.states).filter(
            ([, state]) =>
              state.entity_id !==
                dashboard?.entity("sensor", "grid_serving_forecast")?.metadata
                  .entity_id &&
              ["wh", "kwh", "mwh"].includes(
                String(state.attributes.unit_of_measurement ?? "")
                  .trim()
                  .toLowerCase(),
              ),
          ),
        ),
      }
    : undefined,
);
function showError(cause: unknown) {
  errorCode.value =
    cause && typeof cause === "object" && "code" in cause
      ? String(cause.code)
      : "failed";
  if (errorCode.value === "forbidden" && confirmed.value)
    confirmed.value = { ...confirmed.value, can_edit: false };
}
async function load(edit = false) {
  if (!dashboard || pending.value || !connected.value) return;
  pending.value = "loading";
  errorCode.value = null;
  if (edit) saved.value = false;
  try {
    const result = await dashboard.loadGridServingForecast();
    if (disposed) return;
    if (refreshRequested) return;
    if (confirmed.value?.revision !== result.revision) saved.value = false;
    confirmed.value = result;
    if (!edit && editing.value && result.revision !== revision.value)
      errorCode.value = "conflict";
    if (edit && result.can_edit) {
      draft.value = result.pv_sensor;
      revision.value = result.revision;
      editing.value = true;
    } else if (edit) {
      editing.value = false;
    }
  } catch (cause) {
    if (!disposed) showError(cause);
  } finally {
    if (!disposed) {
      pending.value = null;
      if (refreshRequested) {
        refreshRequested = false;
        void load(edit);
      } else if (edit && editing.value) {
        await nextTick();
        section.value?.querySelector("select")?.focus();
      } else if (saved.value && !editing.value) {
        await nextTick();
        editButton.value?.focus();
      }
    }
  }
}
async function save() {
  if (
    !dashboard ||
    pending.value ||
    !editing.value ||
    !confirmed.value?.can_edit ||
    errorCode.value === "conflict"
  )
    return;
  if (!connected.value) {
    errorCode.value = "disconnected";
    return;
  }
  pending.value = "saving";
  errorCode.value = null;
  saved.value = false;
  try {
    const result = await dashboard.saveGridServingForecast({
      pv_sensor: draft.value,
      revision: revision.value,
    });
    if (disposed) return;
    if (
      refreshRequested &&
      dashboard.entity("sensor", "grid_serving_forecast")?.state?.attributes
        .source_entity_id !== result.pv_sensor
    )
      return;
    confirmed.value = result;
    editing.value = false;
    saved.value = true;
  } catch (cause) {
    if (!disposed) showError(cause);
  } finally {
    if (!disposed) {
      pending.value = null;
      if (refreshRequested) {
        refreshRequested = false;
        void load();
      } else if (saved.value) {
        await nextTick();
        editButton.value?.focus();
      }
    }
  }
}
async function cancel() {
  if (pending.value) return;
  editing.value = false;
  errorCode.value = null;
  await nextTick();
  editButton.value?.focus();
}
function refresh() {
  if (pending.value) refreshRequested = true;
  else void load();
}
watch(
  [connected, () => dashboard?.ready.value],
  ([online, ready]) => {
    if (online && ready && (!editing.value || pending.value)) refresh();
  },
  { immediate: true },
);
watch(
  () =>
    dashboard?.entity("sensor", "grid_serving_forecast")?.state?.attributes
      .source_entity_id,
  (source, previous) => {
    if (source !== previous && dashboard?.ready.value) refresh();
  },
);
</script>

<template>
  <section
    ref="section"
    class="grid-serving-source"
    :aria-labelledby="`${id}-title`"
    :aria-busy="Boolean(pending)"
  >
    <div class="grid-serving-source__header">
      <div>
        <h3 :id="`${id}-title`">{{ text.title }}</h3>
        <p v-if="confirmed" class="grid-serving-source__confirmed">
          {{ sourceName }}
        </p>
      </div>
      <button
        v-if="confirmed?.can_edit && !editing"
        ref="editButton"
        type="button"
        :disabled="Boolean(pending) || !connected"
        @click="load(true)"
      >
        {{ text.edit }}
      </button>
    </div>
    <p :id="`${id}-hint`">{{ text.hint }}</p>
    <p v-if="confirmed && !confirmed.pv_sensor && !editing">
      {{ text.missing }}
    </p>
    <p v-if="confirmed && !confirmed.can_edit">{{ text.readonly }}</p>
    <p v-if="pending" role="status">
      {{ pending === "loading" ? text.loading : text.saving }}
    </p>
    <p v-if="saved" role="status">{{ text.saved }}</p>
    <p
      v-if="error"
      :id="`${id}-error`"
      class="grid-serving-source__error"
      role="alert"
    >
      {{ error }}
    </p>
    <button
      v-if="errorCode === 'conflict' || (!confirmed && error)"
      type="button"
      :disabled="Boolean(pending) || !connected"
      @click="load(editing)"
    >
      {{ text.reload }}
    </button>
    <form v-if="editing" @submit.prevent="save">
      <SensorPicker
        :hass="energyHass"
        v-model="draft"
        :label="text.source"
        name="grid_serving_pv_sensor"
        :disabled="Boolean(pending) || !connected || !confirmed?.can_edit"
        :invalid="
          errorCode === 'invalid_sensor' || errorCode === 'invalid_unit'
        "
        :described-by="`${id}-hint${error ? ` ${id}-error` : ''}`"
      />
      <div class="grid-serving-source__actions">
        <button
          type="submit"
          :disabled="
            Boolean(pending) ||
            !connected ||
            !confirmed?.can_edit ||
            errorCode === 'conflict'
          "
        >
          {{ text.save }}
        </button>
        <button type="button" :disabled="Boolean(pending)" @click="cancel">
          {{ text.cancel }}
        </button>
      </div>
    </form>
  </section>
</template>

<style>
.grid-serving-source {
  display: grid;
  gap: 12px;
  margin-block: 20px;
  padding-block: 16px;
  border-block: 1px solid var(--divider-color, #ddd);
  min-width: 0;
}
.grid-serving-source__header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
}
.grid-serving-source__header > div {
  min-width: 0;
}
.grid-serving-source h3 {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 500;
}
.grid-serving-source p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--secondary-text-color, #666);
  overflow-wrap: anywhere;
}
.grid-serving-source .grid-serving-source__confirmed {
  color: var(--primary-text-color, #222);
}
.grid-serving-source .grid-serving-source__error {
  color: var(--error-color, #b00020);
}
.grid-serving-source form {
  display: grid;
  gap: 12px;
}
.grid-serving-source__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.grid-serving-source button {
  min-height: 44px;
  padding: 8px 16px;
  border: 1px solid var(--divider-color, #ccc);
  border-radius: 6px;
  color: var(--primary-color, #0077a3);
  background: var(--card-background-color, #fff);
  font: inherit;
  cursor: pointer;
}
.grid-serving-source button:disabled {
  opacity: 0.5;
  cursor: default;
}
.grid-serving-source button:focus-visible {
  outline: 2px solid var(--primary-color, #0077a3);
  outline-offset: 2px;
}
</style>
