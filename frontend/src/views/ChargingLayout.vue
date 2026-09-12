<script setup lang="ts">
import { computed, inject, useId } from "vue";
import EntityControl from "../components/EntityControl.vue";
import EntityValue from "../components/EntityValue.vue";
import MonthSelection from "../components/MonthSelection.vue";
import TimeWindowControl from "../components/TimeWindowControl.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import type { EntityDomain } from "../types";

const props = defineProps<{
  switchKey: string;
  cards: readonly {
    key: string;
    group?: string;
    layout?: "columns" | "months";
    timeWindow?: "timed_charge" | "grid_serving";
    title: { de: string; en: string };
    entities: readonly (readonly [EntityDomain, string])[];
  }[];
}>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const id = useId();
const language = computed(() => dashboard?.language.value ?? "en");
const cards = computed(() =>
  props.cards
    .map((card) => {
      const availableEntities = card.entities.filter(([domain, key]) =>
        dashboard?.entity(domain, key),
      );
      const entities =
        card.layout === "months" &&
        (availableEntities.length ||
          dashboard?.entity("switch", props.switchKey))
          ? card.entities
          : availableEntities;
      return {
        ...card,
        showTimeWindow: Boolean(
          card.timeWindow && entities.some(([domain]) => domain === "time"),
        ),
        entities: entities.filter(
          ([domain]) => !card.timeWindow || domain !== "time",
        ),
      };
    })
    .filter((card) => card.entities.length || card.showTimeWindow),
);
const groups = computed(() => {
  const grouped: {
    key: string;
    cards: typeof cards.value;
    wide: boolean;
  }[] = [];
  for (const card of cards.value) {
    const key = card.group ?? card.key;
    const previous = grouped.at(-1);
    if (previous?.key === key) previous.cards.push(card);
    else grouped.push({ key, cards: [card], wide: false });
  }
  const narrowCount = grouped.filter(
    (group) => !group.cards.some((card) => card.layout),
  ).length;
  return grouped.map((group) => ({
    ...group,
    wide: narrowCount <= 1 || group.cards.some((card) => card.layout),
  }));
});
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
    <div v-if="groups.length" class="charging-view__cards">
      <div
        v-for="group in groups"
        :key="group.key"
        class="charging-view__group"
        :class="{ 'charging-view__group--wide': group.wide }"
      >
        <section
          v-for="card in group.cards"
          :key="card.key"
          class="charging-view__card"
          :aria-labelledby="`${id}-${card.key}`"
        >
          <h2 :id="`${id}-${card.key}`">{{ card.title[language] }}</h2>
          <TimeWindowControl
            v-if="card.showTimeWindow && card.timeWindow"
            :kind="card.timeWindow"
          />
          <div
            v-if="card.entities.length"
            class="charging-view__rows"
            :class="{
              'charging-view__rows--columns': card.layout === 'columns',
              'charging-view__rows--months': card.layout === 'months',
            }"
          >
            <MonthSelection
              v-if="card.layout === 'months'"
              :entity-keys="card.entities.map(([, key]) => key)"
            />
            <template
              v-else
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
    </div>
  </div>
</template>

<style>
.charging-view {
  display: grid;
  gap: 20px;
  margin-top: 24px;
  min-width: 0;
}
.charging-view__cards,
.charging-view__group {
  display: grid;
  gap: 20px;
  min-width: 0;
  align-content: start;
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
.charging-view__card > .time-window-control + .charging-view__rows {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--divider-color, #e0e0e0);
}
.charging-view__rows > .entity-control {
  border: 0;
  border-radius: 0;
  padding: 0 0 16px;
  border-bottom: 1px solid var(--divider-color, #e0e0e0);
  box-shadow: none;
}
.charging-view__rows > .entity-control:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}
.charging-view__status {
  margin: 0;
  color: var(--secondary-text-color, #666);
  line-height: 1.6;
}
@media (max-width: 600px) {
  .charging-view,
  .charging-view__cards,
  .charging-view__group {
    gap: 16px;
  }
  .charging-view__card {
    padding: 20px;
  }
}

@container sax-content (min-width: 860px) {
  .charging-view {
    gap: 14px;
    margin-top: 16px;
  }
  .charging-view__cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    align-items: start;
  }
  .charging-view__group {
    gap: 14px;
  }
  .charging-view__group--wide {
    grid-column: 1 / -1;
  }
  .charging-view__card {
    padding: 18px;
  }
  .charging-view__card h2 {
    margin-bottom: 12px;
    font-size: 16px;
  }
  .charging-view__rows {
    gap: 12px;
  }
  .charging-view__rows > .entity-control {
    gap: 8px 12px;
    padding-bottom: 12px;
  }
  .charging-view__rows > .entity-control:last-child {
    padding-bottom: 0;
  }
  .charging-view__rows > .entity-control .entity-control__description {
    flex-basis: 120px;
  }
  .charging-view__rows--columns {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    column-gap: 24px;
    align-items: start;
  }
  .charging-view__rows--columns > :last-child:nth-child(odd) {
    grid-column: 1 / -1;
  }
  .charging-view__rows--columns .entity-value {
    min-height: 44px;
    padding-block: 8px;
  }
}
</style>
