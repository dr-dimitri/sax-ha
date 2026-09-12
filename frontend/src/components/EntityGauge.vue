<script setup lang="ts">
import { computed, inject, useId } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";

const props = defineProps<{
  entityKey: string;
  maximum: number;
  segments: readonly {
    from: number;
    color: "red" | "yellow" | "green";
    label: string;
  }[];
}>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const entity = computed(() => dashboard?.entity("sensor", props.entityKey));
const headingId = `sax-gauge-${useId()}`;
const numeric = computed(() => {
  const raw = entity.value?.state?.state.trim();
  if (!entity.value?.available || !raw) return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
});
const boundedValue = computed(() =>
  numeric.value === null
    ? null
    : Math.max(0, Math.min(props.maximum, numeric.value)),
);
const rangeLabel = computed(() => {
  if (numeric.value === null) return null;
  return (
    [...props.segments]
      .reverse()
      .find((segment) => numeric.value! >= segment.from)?.label ??
    props.segments[0]?.label
  );
});
const valueText = computed(() => {
  if (entity.value?.available && numeric.value === null) {
    return dashboard?.language.value === "de" ? "Unbekannt" : "Unknown";
  }
  return entity.value?.displayValue;
});
const arcs = computed(() =>
  props.segments.map((segment, index) => ({
    ...segment,
    offset: -(segment.from / props.maximum) * 100,
    length:
      (((props.segments[index + 1]?.from ?? props.maximum) - segment.from) /
        props.maximum) *
      100,
  })),
);
</script>

<template>
  <section v-if="entity" class="entity-gauge" :aria-labelledby="headingId">
    <h2 :id="headingId">{{ entity.name }}</h2>
    <div
      class="entity-gauge__meter"
      :role="boundedValue === null ? undefined : 'meter'"
      :aria-labelledby="boundedValue === null ? undefined : headingId"
      :aria-valuemin="boundedValue === null ? undefined : 0"
      :aria-valuemax="boundedValue === null ? undefined : maximum"
      :aria-valuenow="boundedValue ?? undefined"
      :aria-valuetext="
        boundedValue === null ? undefined : `${valueText} · ${rangeLabel}`
      "
    >
      <svg viewBox="0 0 240 124" aria-hidden="true">
        <path class="entity-gauge__track" d="M20 110 A100 100 0 0 1 220 110" />
        <template v-if="boundedValue !== null">
          <path
            v-for="arc in arcs"
            :key="arc.from"
            class="entity-gauge__segment"
            :class="`entity-gauge__segment--${arc.color}`"
            d="M20 110 A100 100 0 0 1 220 110"
            pathLength="100"
            :stroke-dasharray="`${arc.length} 100`"
            :stroke-dashoffset="arc.offset"
          />
          <line
            class="entity-gauge__needle"
            x1="120"
            y1="110"
            x2="120"
            y2="33"
            :transform="`rotate(${(boundedValue / maximum) * 180 - 90} 120 110)`"
          />
          <circle class="entity-gauge__pivot" cx="120" cy="110" r="5" />
        </template>
      </svg>
      <div class="entity-gauge__scale" aria-hidden="true">
        <span>0</span><span>{{ maximum }}</span>
      </div>
      <p class="entity-gauge__value">{{ valueText }}</p>
      <p v-if="rangeLabel" class="entity-gauge__range">{{ rangeLabel }}</p>
    </div>
  </section>
</template>

<style>
.entity-gauge {
  min-width: 0;
  padding: 24px;
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  box-shadow: var(--ha-card-box-shadow, none);
  color: var(--primary-text-color, #212121);
  text-align: center;
}
.entity-gauge h2 {
  margin: 0 0 20px;
  font-size: 16px;
  line-height: 1.5;
  font-weight: 500;
  overflow-wrap: anywhere;
}
.entity-gauge__meter {
  max-width: 260px;
  margin: 0 auto;
}
.entity-gauge svg {
  display: block;
  width: 100%;
  fill: none;
}
.entity-gauge__track,
.entity-gauge__segment {
  stroke-width: 15;
  stroke-linecap: butt;
}
.entity-gauge__track {
  stroke: var(--divider-color, #e0e0e0);
}
.entity-gauge__segment--red {
  stroke: var(--error-color, #db4437);
}
.entity-gauge__segment--yellow {
  stroke: var(--warning-color, #f4b400);
}
.entity-gauge__segment--green {
  stroke: var(--success-color, #0f9d58);
}
.entity-gauge__needle {
  stroke: var(--primary-text-color, #212121);
  stroke-width: 3;
  stroke-linecap: round;
}
.entity-gauge__pivot {
  stroke: none;
  fill: var(--primary-text-color, #212121);
}
.entity-gauge__scale {
  display: flex;
  justify-content: space-between;
  padding: 2px 7px;
  color: var(--secondary-text-color, #666);
  font-size: 12px;
}
.entity-gauge__value {
  margin: 10px 0 0;
  font-size: 28px;
  line-height: 1.4;
  font-weight: 500;
  overflow-wrap: anywhere;
}
.entity-gauge__range {
  margin: 4px 0 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--secondary-text-color, #666);
}
</style>
