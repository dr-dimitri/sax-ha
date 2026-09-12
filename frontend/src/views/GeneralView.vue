<script setup lang="ts">
import { computed, inject, useId } from "vue";
import EntityControl from "../components/EntityControl.vue";
import EntityGauge from "../components/EntityGauge.vue";
import EntityValue from "../components/EntityValue.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import type { EntityDomain } from "../types";

const dashboard = inject(SAX_DASHBOARD_KEY);
const id = useId();
const text = computed(() =>
  dashboard?.language.value === "de"
    ? {
        power: "Leistung",
        device: "Gerät",
        low: "Niedrig",
        medium: "Mittel",
        high: "Hoch",
        inRange: "Im Bereich",
        loading: "Die Entitäten werden geladen …",
        empty: "Für diese Ansicht sind keine Entitäten verfügbar.",
      }
    : {
        power: "Power",
        device: "Device",
        low: "Low",
        medium: "Medium",
        high: "High",
        inRange: "In range",
        loading: "Loading entities …",
        empty: "No entities are available for this view.",
      },
);
const definitions: {
  title: "power" | "device";
  entities: readonly (readonly [EntityDomain, string])[];
}[] = [
  {
    title: "power",
    entities: [
      ["number", "max_soc"],
      ["sensor", "charge_power"],
      ["sensor", "discharge_power"],
      ["sensor", "smartmeter_power"],
    ],
  },
  {
    title: "device",
    entities: [
      ["sensor", "energy_charged"],
      ["sensor", "energy_discharged"],
      ["sensor", "sun_version_master"],
      ["sensor", "sun_version_gateway"],
      ["sensor", "sun_serial_number"],
      ["sensor", "storage_event_text"],
      ["sensor", "ic_control_mode_text"],
      ["binary_sensor", "cell_calibration_active"],
      ["sensor", "next_cell_calibration"],
      ["switch", "storage_switch"],
    ],
  },
];
const cards = computed(() =>
  definitions
    .map((card) => ({
      ...card,
      entities: card.entities.filter(([domain, key]) =>
        dashboard?.entity(domain, key),
      ),
    }))
    .filter((card) => card.entities.length),
);
const hasGauge = computed(() =>
  Boolean(
    dashboard?.entity("sensor", "soc") ||
    dashboard?.entity("sensor", "storage_max_cell_temp"),
  ),
);
const hasEntities = computed(() => hasGauge.value || cards.value.length > 0);
</script>

<template>
  <div class="general-view">
    <p
      v-if="!dashboard?.ready.value && !dashboard?.error.value"
      class="general-view__status"
      role="status"
    >
      {{ text.loading }}
    </p>
    <p
      v-else-if="dashboard?.ready.value && !hasEntities"
      class="general-view__status"
      role="status"
    >
      {{ text.empty }}
    </p>
    <div v-if="hasGauge" class="general-view__gauges">
      <EntityGauge
        entity-key="soc"
        :maximum="100"
        :segments="[
          { from: 0, color: 'red', label: text.low },
          { from: 20, color: 'yellow', label: text.medium },
          { from: 50, color: 'green', label: text.high },
        ]"
      />
      <EntityGauge
        entity-key="storage_max_cell_temp"
        :maximum="40"
        :segments="[
          { from: 0, color: 'red', label: text.low },
          { from: 5, color: 'green', label: text.inRange },
          { from: 32, color: 'red', label: text.high },
        ]"
      />
    </div>
    <section
      v-for="card in cards"
      :key="card.title"
      class="general-view__card"
      :class="`general-view__card--${card.title}`"
      :aria-labelledby="`${id}-${card.title}`"
    >
      <h2 :id="`${id}-${card.title}`">{{ text[card.title] }}</h2>
      <div class="general-view__rows">
        <template
          v-for="[domain, key] in card.entities"
          :key="`${domain}.${key}`"
        >
          <EntityControl
            v-if="domain === 'number' || domain === 'switch'"
            :domain="domain"
            :entity-key="key"
            :confirm-switch="domain === 'switch' && key === 'storage_switch'"
          />
          <EntityValue v-else :domain="domain" :entity-key="key" />
        </template>
      </div>
    </section>
  </div>
</template>

<style>
.general-view {
  display: grid;
  gap: 20px;
  margin-top: 24px;
  min-width: 0;
}
.general-view__gauges {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr));
  gap: 20px;
}
.general-view__card {
  min-width: 0;
  padding: 24px;
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  box-shadow: var(--ha-card-box-shadow, none);
  color: var(--primary-text-color, #212121);
}
.general-view__card h2 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.5;
}
.general-view__rows {
  display: grid;
  gap: 16px;
}
.general-view__rows .entity-control {
  border: 0;
  border-radius: 0;
  padding: 0 0 16px;
  border-bottom: 1px solid var(--divider-color, #e0e0e0);
  box-shadow: none;
}
.general-view__rows .entity-control:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}
.general-view__status {
  margin: 0;
  color: var(--secondary-text-color, #666);
  line-height: 1.6;
}
@container sax-content (min-width: 860px) {
  .general-view {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;
    gap: 16px;
    margin-top: 16px;
  }
  .general-view__gauges {
    grid-column: 1;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }
  .general-view__gauges:has(> :only-child) {
    grid-template-columns: minmax(0, 1fr);
  }
  .general-view__card {
    padding: 18px;
  }
  .general-view__card--power {
    grid-column: 1;
  }
  .general-view__card--device {
    grid-column: 2;
    grid-row: 1 / span 2;
  }
  .general-view:not(:has(.general-view__gauges)) .general-view__card--device,
  .general-view:not(:has(.general-view__card--power))
    .general-view__card--device {
    grid-row: 1;
  }
  .general-view:has(> :only-child),
  .general-view:not(:has(.general-view__card--device)) {
    grid-template-columns: minmax(0, 1fr);
  }
  .general-view__card:only-child {
    grid-column: auto;
    grid-row: auto;
  }
  .general-view__card h2 {
    margin-bottom: 12px;
    font-size: 16px;
  }
  .general-view__rows {
    gap: 10px;
  }
  .general-view__rows .entity-control {
    padding: 0 0 10px;
  }
  .general-view__rows .entity-control:last-child {
    padding-bottom: 0;
  }
  .general-view__status {
    grid-column: 1 / -1;
  }
}
@media (max-width: 600px) {
  .general-view {
    gap: 16px;
  }
  .general-view__gauges {
    gap: 16px;
  }
  .general-view__card {
    padding: 20px;
  }
}
</style>
