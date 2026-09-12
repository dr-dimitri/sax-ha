<script setup lang="ts">
import ChargingLayout from "./ChargingLayout.vue";

const cards = [
  {
    key: "window",
    group: "schedule",
    timeWindow: "timed_charge",
    title: { de: "Zeitfenster", en: "Time window" },
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
</script>

<template>
  <ChargingLayout
    switch-key="timed_charge_enabled"
    :cards="cards"
    hide-confirmed-label
  />
</template>
