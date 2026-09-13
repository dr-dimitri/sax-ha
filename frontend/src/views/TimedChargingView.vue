<script setup lang="ts">
import { computed, inject } from "vue";
import ChargingLayout from "./ChargingLayout.vue";
import TariffPlan from "../components/TariffPlan.vue";
import ChargePlan from "../components/ChargePlan.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import type { HomeAssistant } from "../types";

defineProps<{ hass?: HomeAssistant }>();

const dashboard = inject(SAX_DASHBOARD_KEY);
const bridgeEnabled = computed(() => {
  const control = dashboard?.entity("switch", "bridge_charge_enabled");
  return control
    ? control.state?.state === "on"
    : dashboard?.entity("sensor", "bridge_charge_plan")?.state?.attributes
        .enabled === true;
});
const timeOfUseTariff = computed(
  () =>
    dashboard?.entity("sensor", "economics_current_import_price")?.state
      ?.attributes.tariff_type === "time_of_use",
);
const baseCards = [
  {
    key: "window",
    group: "schedule",
    timeWindow: "timed_charge",
    title: { de: "Netzladezeitfenster", en: "Grid charging window" },
    entities: [
      ["time", "timed_charge_start"],
      ["time", "timed_charge_end"],
    ],
  },
  {
    key: "discharge",
    group: "schedule",
    title: { de: "Entladestatus", en: "Discharge status" },
    entities: [["sensor", "timed_charge_discharge_status"]],
  },
  {
    key: "settings",
    title: { de: "Einstellungen", en: "Settings" },
    entities: [
      ["number", "timed_charge_max_soc"],
      ["number", "timed_charge_min_soc"],
    ],
  },
  {
    key: "months",
    layout: "months",
    title: { de: "Aktive Monate", en: "Active months" },
    entities: Array.from(
      { length: 12 },
      (_, index) => ["switch", `timed_charge_month_${index + 1}`] as const,
    ),
  },
] as const;
const cards = computed(() =>
  baseCards
    .filter(
      (card) =>
        card.key !== "window" ||
        (!bridgeEnabled.value && !timeOfUseTariff.value),
    )
    .map((card) => ({
      ...card,
      entities: card.entities.filter(
        ([, key]) => !bridgeEnabled.value || key !== "timed_charge_min_soc",
      ),
    })),
);
</script>

<template>
  <div class="timed-charging-view">
    <ChargingLayout
      switch-key="timed_charge_enabled"
      :cards="cards"
      hide-confirmed-label
    />
    <ChargePlan :hass="hass" class="timed-charging-view__tariff" />
    <TariffPlan :hass="hass" class="timed-charging-view__tariff" />
  </div>
</template>

<style>
.timed-charging-view {
  min-width: 0;
}
.timed-charging-view__tariff {
  margin-top: 20px;
}
@media (max-width: 600px) {
  .timed-charging-view__tariff {
    margin-top: 16px;
  }
}
@container sax-content (min-width: 860px) {
  .timed-charging-view__tariff {
    margin-top: 16px;
  }
}
</style>
