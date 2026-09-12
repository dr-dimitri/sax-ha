<script setup lang="ts">
import { computed, inject } from "vue";
import ChargingLayout from "./ChargingLayout.vue";
import HemsCard from "../components/HemsCard.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import type { HomeAssistant } from "../types";

defineProps<{ hass?: HomeAssistant }>();

const dashboard = inject(SAX_DASHBOARD_KEY);
const adaptive = computed(
  () =>
    dashboard?.entity("select", "price_charge_strategy")?.state?.state ===
    "adaptive",
);
const cards = computed(
  () =>
    [
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
          ...(adaptive.value
            ? ([
                ["number", "timed_charge_min_soc"],
                ["number", "timed_charge_max_soc"],
              ] as const)
            : []),
          ["sensor", "price_charge_active_text"],
          ["sensor", "price_charge_status_text"],
          ...(!adaptive.value
            ? ([["sensor", "grid_serving_forecast"]] as const)
            : []),
          ["sensor", "price_charge_next_start"],
          ["sensor", "price_charge_current_price"],
        ],
      },
    ] as const,
);
</script>

<template>
  <ChargingLayout
    switch-key="price_charge_enabled"
    :cards="cards"
    hide-confirmed-label
  />
  <HemsCard tariff="dynamic" :hass="hass" />
</template>
