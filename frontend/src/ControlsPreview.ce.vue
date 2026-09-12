<script setup lang="ts">
import { computed, provide, ref, shallowRef } from "vue";
import EntityControl from "./components/EntityControl.vue";
import EntityValue from "./components/EntityValue.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "./ha";
import type {
  ConnectionEvent,
  DashboardEntityMetadata,
  HassConnection,
  HassEntity,
  HomeAssistant,
} from "./types";

const dark = ref(false);
const failNext = ref(false);
const disconnected = ref(false);
const listeners = new Map<ConnectionEvent, () => void>();
const definitions = [
  { domain: "sensor", key: "soc", de: "Ladezustand", en: "State of charge" },
  { domain: "switch", key: "storage", de: "Speicher", en: "Battery" },
  {
    domain: "number",
    key: "target",
    de: "Ziel-Ladezustand",
    en: "Target state of charge",
  },
  { domain: "time", key: "start", de: "Ladebeginn", en: "Charging start" },
  { domain: "select", key: "mode", de: "Lademodus", en: "Charging mode" },
] as const;
const samples: Record<string, HassEntity> = Object.fromEntries(
  definitions.map(({ domain, key }) => {
    const values = {
      soc: "63.5",
      storage: "on",
      target: "80",
      start: "03:00:00",
      mode: "automatic",
    };
    const attributes = {
      soc: { unit_of_measurement: "%" },
      storage: {},
      target: { min: 10, max: 100, step: 0.5, unit_of_measurement: "%" },
      start: {},
      mode: { options: ["automatic", "manual"] },
    };
    const entityId = `${domain}.preview_${key}`;
    return [
      entityId,
      { entity_id: entityId, state: values[key], attributes: attributes[key] },
    ];
  }),
);
const connection: HassConnection = {
  get connected() {
    return !disconnected.value;
  },
  async subscribeMessage<T>(callback: (message: T) => void) {
    const language = hass.value.language === "de" ? "de" : "en";
    const entities: DashboardEntityMetadata[] = definitions.map(
      (definition) => ({
        entity_id: `${definition.domain}.preview_${definition.key}`,
        domain: definition.domain,
        key: definition.key,
        name: definition[language],
        states:
          language === "de"
            ? { automatic: "Automatisch", manual: "Manuell" }
            : { automatic: "Automatic", manual: "Manual" },
        can_control: definition.domain !== "sensor",
      }),
    );
    callback({ entities } as T);
    return () => {};
  },
  addEventListener: (event, listener) => {
    listeners.set(event, listener);
  },
  removeEventListener: (event) => {
    listeners.delete(event);
  },
};
const hass = shallowRef<HomeAssistant>({
  language: "de",
  states: samples,
  connection,
  async callService(_domain, service, data, target) {
    await new Promise<void>((resolve) => window.setTimeout(resolve, 600));
    if (failNext.value) {
      failNext.value = false;
      throw new Error("Simulated preview failure");
    }
    const entityId = target?.entity_id;
    if (typeof entityId !== "string") return;
    const confirmed = hass.value.states[entityId];
    const value =
      service === "turn_on"
        ? "on"
        : service === "turn_off"
          ? "off"
          : String(data?.value ?? data?.time ?? data?.option);
    window.setTimeout(() => {
      hass.value = {
        ...hass.value,
        states: {
          ...hass.value.states,
          [entityId]: { ...confirmed, state: value },
        },
      };
    }, 900);
  },
});
const dashboard = useSaxDashboard(
  () => hass.value,
  () => "preview-entry",
);
provide(SAX_DASHBOARD_KEY, dashboard);
const german = computed(() => hass.value.language === "de");

function changeLanguage(): void {
  hass.value = { ...hass.value, language: german.value ? "en" : "de" };
}

function changeConnection(): void {
  disconnected.value = !disconnected.value;
  listeners.get(disconnected.value ? "disconnected" : "ready")?.();
}
</script>

<template>
  <div class="preview-page" :class="{ dark }" :lang="hass.language">
    <main>
      <header>
        <p class="eyebrow">SAX Power · Vue</p>
        <h1>
          {{ german ? "Vorschau der Bedienelemente" : "Control preview" }}
        </h1>
        <p class="description">
          {{
            german
              ? "Nur lokale Beispieldaten. Änderungen wirken ausschließlich in dieser Vorschau."
              : "Local sample data only. Changes apply only to this preview."
          }}
        </p>
      </header>
      <div
        class="preview-options"
        :aria-label="german ? 'Vorschau-Einstellungen' : 'Preview settings'"
      >
        <button type="button" @click="changeLanguage">
          {{ german ? "English" : "Deutsch" }}
        </button>
        <button type="button" :aria-pressed="dark" @click="dark = !dark">
          {{ german ? "Dunkles Design" : "Dark theme" }}
        </button>
        <button
          type="button"
          :aria-pressed="disconnected"
          @click="changeConnection"
        >
          {{
            disconnected
              ? german
                ? "Erneut verbinden"
                : "Reconnect"
              : german
                ? "Verbindung unterbrechen"
                : "Disconnect"
          }}
        </button>
        <label
          ><input v-model="failNext" type="checkbox" />{{
            german ? "Nächste Änderung schlägt fehl" : "Fail next change"
          }}</label
        >
      </div>
      <div class="value-card">
        <EntityValue domain="sensor" entity-key="soc" />
      </div>
      <div class="controls">
        <p v-if="dashboard.error.value" role="alert">
          {{ dashboard.error.value }}
        </p>
        <EntityControl domain="switch" entity-key="storage" />
        <EntityControl domain="number" entity-key="target" />
        <EntityControl domain="time" entity-key="start" />
        <EntityControl domain="select" entity-key="mode" />
      </div>
    </main>
  </div>
</template>

<style>
:host {
  display: block;
  font:
    16px/1.5 Roboto,
    Arial,
    sans-serif;
}
* {
  box-sizing: border-box;
}
.preview-page {
  min-height: 100vh;
  background: #f5f7fa;
  color: #212121;
  --primary-color: #027fa8;
  --primary-text-color: #212121;
  --secondary-text-color: #576675;
  --card-background-color: #fff;
  --divider-color: #cbd5df;
}
.preview-page.dark {
  background: #111820;
  color: #e8edf2;
  --primary-color: #65d3ee;
  --primary-text-color: #e8edf2;
  --secondary-text-color: #a8b7c5;
  --card-background-color: #1b2731;
  --divider-color: #435363;
  --error-color: #ff938a;
}
main {
  max-width: 860px;
  margin: 0 auto;
  padding: 48px 24px;
}
.eyebrow {
  color: var(--secondary-text-color);
  font-weight: 600;
  letter-spacing: 0.08em;
  font-size: 13px;
}
h1 {
  margin: 8px 0 12px;
  line-height: 1.25;
  font-size: 30px;
  font-weight: 600;
}
.description {
  max-width: 620px;
  color: var(--secondary-text-color);
}
.preview-options {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin: 28px 0;
}
.preview-options button {
  min-height: 44px;
  padding: 8px 12px;
  border: 1px solid var(--divider-color);
  border-radius: 6px;
  background: var(--card-background-color);
  color: inherit;
  font: inherit;
  cursor: pointer;
}
.preview-options button[aria-pressed="true"] {
  border-color: var(--primary-color);
}
.preview-options label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  font-size: 14px;
}
.preview-options input {
  width: 20px;
  height: 20px;
  accent-color: var(--primary-color);
}
.value-card {
  padding: 20px;
  margin-bottom: 24px;
  border-radius: 12px;
  background: var(--card-background-color);
}
.controls {
  display: grid;
  gap: 16px;
}
@media (max-width: 520px) {
  main {
    padding: 24px 16px;
  }
  h1 {
    font-size: 25px;
  }
}
</style>
