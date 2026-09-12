<script setup lang="ts">
import ChargingLayout from "./ChargingLayout.vue";

const cards = [
  {
    key: "price",
    layout: "columns",
    title: { de: "Preisoptimiertes Laden", en: "Price-optimised charging" },
    entities: [
      ["select", "price_charge_strategy"],
      ["number", "price_charge_max_price"],
      ["number", "price_charge_neutral_price"],
      ["number", "price_charge_hours"],
      ["number", "max_soc"],
      ["sensor", "price_charge_active_text"],
      ["sensor", "price_charge_status_text"],
      ["sensor", "grid_serving_forecast"],
      ["sensor", "price_charge_next_start"],
      ["sensor", "price_charge_current_price"],
    ],
  },
] as const;
</script>

<template>
  <ChargingLayout switch-key="price_charge_enabled" :cards="cards" />
</template>
