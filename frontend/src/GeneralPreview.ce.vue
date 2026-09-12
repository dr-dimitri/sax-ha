<script setup lang="ts">
import { computed, onBeforeUnmount, provide, ref, shallowRef } from "vue";
import GeneralView from "./views/GeneralView.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "./ha";
import type {
  DashboardEntityMetadata,
  DashboardMetadata,
  HassConnection,
  HassEntity,
  HomeAssistant,
} from "./types";

const dark = ref(false);
const optional = ref(true);
const unavailable = ref(false);
const timers: number[] = [];
const definitions = [
  ["sensor", "soc", "Ladezustand", "State of charge", "63.5", "%"],
  [
    "sensor",
    "storage_max_cell_temp",
    "Max. Zelltemperatur",
    "Max. cell temperature",
    "24.3",
    "°C",
  ],
  ["switch", "storage_switch", "Speicher", "Battery", "on", ""],
  ["number", "max_soc", "Max. Ladezustand", "Max. state of charge", "90", "%"],
  ["sensor", "charge_power", "Ladeleistung", "Charging power", "1820", "W"],
  [
    "sensor",
    "discharge_power",
    "Entladeleistung",
    "Discharging power",
    "0",
    "W",
  ],
  ["sensor", "smartmeter_power", "Netzleistung", "Grid power", "-420", "W"],
  [
    "sensor",
    "energy_charged",
    "Energie geladen",
    "Energy charged",
    "1245.8",
    "kWh",
  ],
  [
    "sensor",
    "energy_discharged",
    "Energie entladen",
    "Energy discharged",
    "1028.4",
    "kWh",
  ],
  [
    "sensor",
    "sun_version_master",
    "Firmware Master",
    "Master firmware",
    "1.2.3",
    "",
  ],
  [
    "sensor",
    "sun_version_gateway",
    "Firmware Gateway",
    "Gateway firmware",
    "2.4.0",
    "",
  ],
  [
    "sensor",
    "sun_serial_number",
    "Seriennummer",
    "Serial number",
    "DEMO-2026-001",
    "",
  ],
  [
    "sensor",
    "storage_event_text",
    "Speicherereignis",
    "Battery event",
    "normal",
    "",
  ],
  [
    "sensor",
    "ic_control_mode_text",
    "Steuermodus",
    "Control mode",
    "normal",
    "",
  ],
  [
    "binary_sensor",
    "cell_calibration_active",
    "Zellkalibrierung aktiv",
    "Cell calibration active",
    "off",
    "",
  ],
  [
    "sensor",
    "next_cell_calibration",
    "Nächste Zellkalibrierung",
    "Next cell calibration",
    "2026-09-14",
    "",
  ],
] as const;
const sampleStates: Record<string, HassEntity> = Object.fromEntries(
  definitions.map(([domain, key, , , state, unit]) => {
    const entityId = `${domain}.preview_${key}`;
    return [
      entityId,
      {
        entity_id: entityId,
        state,
        attributes: {
          ...(unit ? { unit_of_measurement: unit } : {}),
          ...(domain === "number" ? { min: 0, max: 100, step: 1 } : {}),
          ...(key === "next_cell_calibration" ? { device_class: "date" } : {}),
        },
      },
    ];
  }),
);
let metadataListener: ((metadata: DashboardMetadata) => void) | undefined;
function metadata(): DashboardMetadata {
  const de = hass.value.language === "de";
  const entities: DashboardEntityMetadata[] = definitions
    .filter(([, key]) => optional.value || !key.startsWith("sun_"))
    .map(([domain, key, german, english]) => ({
      entity_id: `${domain}.preview_${key}`,
      domain,
      key,
      name: de ? german : english,
      states: { normal: de ? "Normalbetrieb" : "Normal operation" },
      can_control: domain === "switch" || domain === "number",
    }));
  return { entities };
}
const connection: HassConnection = {
  connected: true,
  async subscribeMessage<T>(callback: (message: T) => void) {
    const listener = (value: DashboardMetadata) => callback(value as T);
    metadataListener = listener;
    listener(metadata());
    return () => {
      if (metadataListener === listener) metadataListener = undefined;
    };
  },
  addEventListener() {},
  removeEventListener() {},
};
const hass = shallowRef<HomeAssistant>({
  language: "de",
  connection,
  states: sampleStates,
  config: { time_zone: "Europe/Berlin" },
  async callService(_domain, service, data, target) {
    await new Promise<void>((resolve) =>
      timers.push(window.setTimeout(resolve, 500)),
    );
    const entityId = target?.entity_id;
    if (typeof entityId !== "string") return;
    const confirmed = hass.value.states[entityId];
    const state =
      service === "turn_on"
        ? "on"
        : service === "turn_off"
          ? "off"
          : String(data?.value);
    timers.push(
      window.setTimeout(() => {
        hass.value = {
          ...hass.value,
          states: { ...hass.value.states, [entityId]: { ...confirmed, state } },
        };
      }, 500),
    );
  },
});
const dashboard = useSaxDashboard(
  () => hass.value,
  () => "general-preview",
);
provide(SAX_DASHBOARD_KEY, dashboard);
const german = computed(() => hass.value.language === "de");
function changeLanguage(): void {
  hass.value = { ...hass.value, language: german.value ? "en" : "de" };
}
function changeOptional(): void {
  optional.value = !optional.value;
  metadataListener?.(metadata());
}
function changeAvailability(): void {
  unavailable.value = !unavailable.value;
  hass.value = {
    ...hass.value,
    states: Object.fromEntries(
      Object.entries(hass.value.states).map(([id, entity]) => [
        id,
        {
          ...entity,
          state: unavailable.value ? "unavailable" : sampleStates[id].state,
        },
      ]),
    ),
  };
}
onBeforeUnmount(() => timers.forEach((timer) => window.clearTimeout(timer)));
</script>

<template>
  <div class="general-preview" :class="{ dark }" :lang="hass.language">
    <main>
      <p class="general-preview__eyebrow">SAX Power · Vue</p>
      <h1>{{ german ? "Allgemeine Informationen" : "General information" }}</h1>
      <p class="general-preview__description">
        {{
          german
            ? "Lokale Vorschau mit Beispieldaten. Änderungen wirken ausschließlich in dieser Vorschau."
            : "Local preview with sample data. Changes apply only to this preview."
        }}
      </p>
      <div class="general-preview__options">
        <button @click="changeLanguage">
          {{ german ? "English" : "Deutsch" }}
        </button>
        <button :aria-pressed="dark" @click="dark = !dark">
          {{ german ? "Dunkles Design" : "Dark theme" }}
        </button>
        <button :aria-pressed="optional" @click="changeOptional">
          {{ german ? "SunSpec-Entitäten" : "SunSpec entities" }}
        </button>
        <button :aria-pressed="unavailable" @click="changeAvailability">
          {{ german ? "Nicht verfügbar simulieren" : "Simulate unavailable" }}
        </button>
      </div>
      <p v-if="dashboard.error.value" role="alert">
        {{ dashboard.error.value }}
      </p>
      <GeneralView />
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
.general-preview {
  min-height: 100vh;
  background: #f5f7fa;
  color: #212121;
  --primary-color: #027fa8;
  --primary-text-color: #212121;
  --secondary-text-color: #576675;
  --card-background-color: #fff;
  --divider-color: #cbd5df;
}
.general-preview.dark {
  background: #111820;
  color: #e8edf2;
  --primary-color: #65d3ee;
  --primary-text-color: #e8edf2;
  --secondary-text-color: #a8b7c5;
  --card-background-color: #1b2731;
  --divider-color: #435363;
  --error-color: #ff938a;
}
.general-preview main {
  max-width: 1040px;
  margin: 0 auto;
  padding: 40px 24px;
}
.general-preview__eyebrow {
  color: var(--secondary-text-color);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
}
.general-preview h1 {
  font-size: 30px;
  line-height: 1.3;
  font-weight: 500;
  margin: 8px 0;
}
.general-preview__description {
  color: var(--secondary-text-color);
  max-width: 620px;
}
.general-preview__options {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 24px 0;
}
.general-preview__options button {
  min-height: 44px;
  border: 1px solid var(--divider-color);
  border-radius: 6px;
  padding: 8px 12px;
  font: inherit;
  color: inherit;
  background: var(--card-background-color);
  cursor: pointer;
}
.general-preview__options button[aria-pressed="true"] {
  border-color: var(--primary-color);
}
.general-preview__options button:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}
@media (max-width: 600px) {
  .general-preview main {
    padding: 24px 16px;
  }
  .general-preview h1 {
    font-size: 25px;
  }
}
</style>
