<script setup lang="ts">
import ChargingLayout from "./ChargingLayout.vue";

const cards = [
  {
    key: "pause",
    layout: "columns",
    timeWindow: "grid_serving",
    title: { de: "Ladepause", en: "Charging pause" },
    entities: [
      ["time", "grid_serving_start"],
      ["time", "grid_serving_end"],
      ["sensor", "grid_serving_forecast"],
      ["number", "grid_serving_forecast_threshold"],
      ["sensor", "grid_serving_pause_status"],
    ],
  },
  {
    key: "months",
    layout: "months",
    title: { de: "Aktive Monate", en: "Active months" },
    entities: Array.from(
      { length: 12 },
      (_, index) => ["switch", `grid_serving_month_${index + 1}`] as const,
    ),
  },
] as const;
</script>

<template>
  <ChargingLayout switch-key="grid_serving_enabled" :cards="cards" />
</template>
