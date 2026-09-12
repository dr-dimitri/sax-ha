<script setup lang="ts">
import { computed, inject, useId } from "vue";
import EntityControl from "../components/EntityControl.vue";
import EntityValue from "../components/EntityValue.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import type { EntityDomain } from "../types";

const props = defineProps<{
  switchKey: string;
  cards: readonly {
    key: string;
    title: { de: string; en: string };
    entities: readonly (readonly [EntityDomain, string])[];
  }[];
}>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const id = useId();
const language = computed(() => dashboard?.language.value ?? "en");
const cards = computed(() =>
  props.cards
    .map((card) => ({
      ...card,
      entities: card.entities.filter(([domain, key]) =>
        dashboard?.entity(domain, key),
      ),
    }))
    .filter((card) => card.entities.length),
);
const hasSwitch = computed(() =>
  Boolean(dashboard?.entity("switch", props.switchKey)),
);
const text = computed(() =>
  language.value === "de"
    ? {
        loading: "Die Entitäten werden geladen …",
        empty: "Für diese Ansicht sind keine Entitäten verfügbar.",
      }
    : {
        loading: "Loading entities …",
        empty: "No entities are available for this view.",
      },
);
</script>

<template>
  <div class="charging-view">
    <p
      v-if="!dashboard?.ready.value && !dashboard?.error.value"
      class="charging-view__status"
      role="status"
    >
      {{ text.loading }}
    </p>
    <p
      v-else-if="dashboard?.ready.value && !hasSwitch && !cards.length"
      class="charging-view__status"
      role="status"
    >
      {{ text.empty }}
    </p>
    <EntityControl v-if="hasSwitch" domain="switch" :entity-key="switchKey" />
    <section
      v-for="card in cards"
      :key="card.key"
      class="charging-view__card"
      :aria-labelledby="`${id}-${card.key}`"
    >
      <h2 :id="`${id}-${card.key}`">{{ card.title[language] }}</h2>
      <div class="charging-view__rows">
        <template
          v-for="[domain, key] in card.entities"
          :key="`${domain}.${key}`"
        >
          <EntityControl
            v-if="
              domain === 'switch' ||
              domain === 'number' ||
              domain === 'time' ||
              domain === 'select'
            "
            :domain="domain"
            :entity-key="key"
          />
          <EntityValue v-else :domain="domain" :entity-key="key" />
        </template>
      </div>
    </section>
  </div>
</template>

<style>
.charging-view {
  display: grid;
  gap: 20px;
  margin-top: 24px;
  min-width: 0;
}
.charging-view__card {
  min-width: 0;
  padding: 24px;
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  box-shadow: var(--ha-card-box-shadow, none);
  color: var(--primary-text-color, #212121);
}
.charging-view__card h2 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.5;
}
.charging-view__rows {
  display: grid;
  gap: 16px;
}
.charging-view__rows .entity-control {
  border: 0;
  border-radius: 0;
  padding: 0 0 16px;
  border-bottom: 1px solid var(--divider-color, #e0e0e0);
  box-shadow: none;
}
.charging-view__rows .entity-control:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}
.charging-view__status {
  margin: 0;
  color: var(--secondary-text-color, #666);
  line-height: 1.6;
}
@media (max-width: 600px) {
  .charging-view {
    gap: 16px;
  }
  .charging-view__card {
    padding: 20px;
  }
}
</style>
