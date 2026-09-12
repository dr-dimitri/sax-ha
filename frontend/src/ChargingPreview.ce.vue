<script setup lang="ts">
import { computed, onBeforeUnmount, provide, ref, shallowRef } from "vue";
import TimedChargingView from "./views/TimedChargingView.vue";
import GridServingView from "./views/GridServingView.vue";
import DynamicChargingView from "./views/DynamicChargingView.vue";
import { chargingSample } from "./charging-preview-data";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "./ha";
import type { DashboardMetadata, HassConnection, HomeAssistant } from "./types";

const active = ref(0);
const dark = ref(false);
const unavailable = ref(false);
const fail = ref(false);
const timers: number[] = [];
const calls = ref<string[]>([]);
const views = [TimedChargingView, DynamicChargingView, GridServingView];
const titles = {
  de: ["Zeitvariabler Tarif", "Dynamischer Tarif", "Netzdienliches Laden"],
  en: ["Time-of-use tariff", "Dynamic tariff", "Grid-serving charging"],
};
const sample = chargingSample();
const connection: HassConnection = {
  connected: true,
  async subscribeMessage<T>(callback: (message: T) => void) {
    callback({ entities: chargingSample(hass.value.language).metadata } as T &
      DashboardMetadata);
    return () => {};
  },
  addEventListener() {},
  removeEventListener() {},
};
const hass = shallowRef<HomeAssistant>({
  language: "de",
  states: sample.states,
  connection,
  config: { time_zone: "Europe/Berlin" },
  async callService(domain, service, data, target) {
    calls.value.push(
      `${domain}.${service} ${JSON.stringify({ ...data, ...target })}`,
    );
    await new Promise<void>((resolve) =>
      timers.push(window.setTimeout(resolve, 400)),
    );
    if (fail.value) throw new Error("Simulated failure");
    if (domain === "sax_power") {
      const prefix =
        service === "set_timed_charge_window"
          ? "timed_charge"
          : service === "set_grid_serving_window"
            ? "grid_serving"
            : null;
      if (!prefix) return;
      timers.push(
        window.setTimeout(() => {
          const states = { ...hass.value.states };
          for (const boundary of ["start", "end"]) {
            const entityId = `time.renamed_${prefix}_${boundary}`;
            states[entityId] = {
              ...states[entityId],
              state: String(data?.[boundary]),
            };
          }
          hass.value = { ...hass.value, states };
        }, 400),
      );
      return;
    }
    const id = target?.entity_id;
    if (typeof id !== "string") return;
    const state =
      service === "turn_on"
        ? "on"
        : service === "turn_off"
          ? "off"
          : String(data?.value ?? data?.time ?? data?.option);
    timers.push(
      window.setTimeout(() => {
        hass.value = {
          ...hass.value,
          states: {
            ...hass.value.states,
            [id]: { ...hass.value.states[id], state },
          },
        };
      }, 400),
    );
  },
});
const dashboard = useSaxDashboard(
  () => hass.value,
  () => "charging-preview",
);
provide(SAX_DASHBOARD_KEY, dashboard);
const language = computed(() => dashboard.language.value);
function changeLanguage(): void {
  const language = hass.value.language === "de" ? "en" : "de";
  const forecastId = "sensor.renamed_grid_serving_forecast";
  hass.value = {
    ...hass.value,
    language,
    states: {
      ...hass.value.states,
      [forecastId]: {
        ...hass.value.states[forecastId],
        attributes: chargingSample(language).states[forecastId].attributes,
      },
    },
  };
}
function changeAvailability(): void {
  unavailable.value = !unavailable.value;
  const id = "sensor.renamed_grid_serving_forecast";
  hass.value = {
    ...hass.value,
    states: {
      ...hass.value.states,
      [id]: {
        ...hass.value.states[id],
        state: unavailable.value ? "unavailable" : "24.3",
      },
    },
  };
}
onBeforeUnmount(() => timers.forEach((timer) => window.clearTimeout(timer)));
</script>

<template>
  <div class="charging-preview" :class="{ dark }" :lang="language">
    <main>
      <p class="charging-preview__eyebrow">SAX Power · Vue</p>
      <h1>{{ titles[language][active] }}</h1>
      <p class="charging-preview__description">
        {{
          language === "de"
            ? "Lokale Vorschau mit Beispieldaten. Änderungen wirken ausschließlich in dieser Vorschau."
            : "Local preview with sample data. Changes apply only to this preview."
        }}
      </p>
      <nav
        class="charging-preview__options"
        :aria-label="language === 'de' ? 'Ladeansichten' : 'Charging views'"
      >
        <button
          v-for="(title, index) in titles[language]"
          :key="index"
          :aria-pressed="active === index"
          @click="active = index"
        >
          {{ title }}
        </button>
      </nav>
      <div class="charging-preview__options">
        <button @click="changeLanguage">
          {{ language === "de" ? "English" : "Deutsch" }}
        </button>
        <button :aria-pressed="dark" @click="dark = !dark">
          {{ language === "de" ? "Dunkles Design" : "Dark theme" }}
        </button>
        <button :aria-pressed="unavailable" @click="changeAvailability">
          {{
            language === "de"
              ? "Prognose nicht verfügbar"
              : "Forecast unavailable"
          }}
        </button>
        <button :aria-pressed="fail" @click="fail = !fail">
          {{
            language === "de"
              ? "Schreibfehler simulieren"
              : "Simulate write failure"
          }}
        </button>
      </div>
      <component :is="views[active]" />
      <details class="charging-preview__log">
        <summary>
          {{
            language === "de"
              ? "Simulierte Bedienaktionen"
              : "Simulated actions"
          }}
          ({{ calls.length }})
        </summary>
        <ol>
          <li v-for="(call, index) in calls" :key="index">{{ call }}</li>
        </ol>
      </details>
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
.charging-preview {
  min-height: 100vh;
  background: #f5f7fa;
  color: #212121;
  --primary-color: #027fa8;
  --primary-text-color: #212121;
  --secondary-text-color: #576675;
  --card-background-color: #fff;
  --divider-color: #cbd5df;
}
.charging-preview.dark {
  background: #111820;
  color: #e8edf2;
  --primary-color: #65d3ee;
  --primary-text-color: #e8edf2;
  --secondary-text-color: #a8b7c5;
  --card-background-color: #1b2731;
  --divider-color: #435363;
  --error-color: #ff938a;
}
.charging-preview main {
  max-width: 1040px;
  margin: 0 auto;
  padding: 40px 24px;
}
.charging-preview__eyebrow {
  color: var(--secondary-text-color);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
}
.charging-preview h1 {
  font-size: 30px;
  line-height: 1.3;
  font-weight: 500;
  margin: 8px 0;
}
.charging-preview__description {
  color: var(--secondary-text-color);
  max-width: 620px;
}
.charging-preview__options {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 24px 0;
}
.charging-preview__options button {
  min-height: 44px;
  border: 1px solid var(--divider-color);
  border-radius: 6px;
  padding: 8px 12px;
  font: inherit;
  color: inherit;
  background: var(--card-background-color);
  cursor: pointer;
}
.charging-preview__options button[aria-pressed="true"] {
  border-color: var(--primary-color);
}
.charging-preview__options button:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}
.charging-preview__log {
  margin-top: 24px;
  overflow-wrap: anywhere;
  color: var(--secondary-text-color);
}
@media (max-width: 600px) {
  .charging-preview main {
    padding: 24px 16px;
  }
  .charging-preview h1 {
    font-size: 25px;
  }
}
</style>
