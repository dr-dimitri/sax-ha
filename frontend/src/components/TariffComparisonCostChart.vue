<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, useId, watch } from "vue";
import type { Language } from "../tabs";

type ChartTariff = {
  id: string;
  name: string;
  firstYearAtZero: number;
  standardAtZero: number;
  annualCostPerKwh: number;
  costAtConsumption: (consumption: number, firstYear: boolean) => number | null;
};

const props = defineProps<{
  language: Language;
  annualConsumption: number;
  tariffs: readonly ChartTariff[];
}>();

const text = computed(() =>
  props.language === "de"
    ? {
        title: "Jahreskosten nach Stromverbrauch",
        year: "Tarifjahr",
        firstYear: "Erstes Jahr",
        laterYears: "Folgejahre",
        cost: "Jahreskosten (€)",
        consumption: "Jahresverbrauch (kWh)",
        selection: "Jahresverbrauch im Diagramm (kWh)",
        selectedCosts: "Kosten beim ausgewählten Verbrauch",
      }
    : {
        title: "Annual costs by electricity consumption",
        year: "Tariff year",
        firstYear: "First year",
        laterYears: "Subsequent years",
        cost: "Annual cost (€)",
        consumption: "Annual consumption (kWh)",
        selection: "Annual consumption in chart (kWh)",
        selectedCosts: "Costs at selected consumption",
      },
);

const locale = computed(() => (props.language === "de" ? "de-DE" : "en-GB"));
const number = computed(
  () => new Intl.NumberFormat(locale.value, { maximumFractionDigits: 2 }),
);
const compact = computed(
  () =>
    new Intl.NumberFormat(locale.value, {
      notation: "compact",
      maximumFractionDigits: 1,
    }),
);
const scientific = computed(
  () =>
    new Intl.NumberFormat(locale.value, {
      notation: "scientific",
      maximumFractionDigits: 1,
    }),
);
const euro = computed(
  () =>
    new Intl.NumberFormat(locale.value, { style: "currency", currency: "EUR" }),
);

const colors = [
  "#0081a5",
  "#b75128",
  "#725ec3",
  "#43882e",
  "#aa417c",
  "#77742b",
];
const dashes = ["none", "8 4", "3 4", "10 4 3 4", "2 3", "5 3 2 3"];
const id = `sax-cost-chart-${useId()}`;
const firstYear = ref(true);
const consumption = ref(props.annualConsumption);
const container = ref<HTMLElement>();
const width = ref(620);
let observer: ResizeObserver | undefined;

watch(
  () => props.annualConsumption,
  (value) => {
    consumption.value = value;
  },
);
onMounted(() => {
  const element = container.value;
  if (!element) return;
  width.value = Math.max(180, element.clientWidth);
  if (typeof ResizeObserver === "undefined") return;
  observer = new ResizeObserver(([entry]) => {
    if (entry) width.value = Math.max(180, Math.round(entry.contentRect.width));
  });
  observer.observe(element);
});
onBeforeUnmount(() => observer?.disconnect());

const height = 254;
const left = 52;
const top = 26;
const bottom = 204;
const right = computed(() => width.value - 22);

function axisValue(value: number): string {
  const magnitude = Math.abs(value);
  if (magnitude >= 1e12) return scientific.value.format(value);
  if (magnitude >= 10000) return compact.value.format(value);
  return number.value.format(value);
}

function plotCost(tariff: ChartTariff, at: number): number {
  const fixed = firstYear.value
    ? tariff.firstYearAtZero
    : tariff.standardAtZero;
  const cost = at === 0 ? fixed : fixed + tariff.annualCostPerKwh * at;
  return Math.min(Number.MAX_VALUE, Math.max(-Number.MAX_VALUE, cost));
}

const maximum = computed(() => {
  if (props.annualConsumption === 0) return 6000;
  const target = Math.min(
    Number.MAX_VALUE,
    Math.max(100, props.annualConsumption * 2),
  );
  const unit = 10 ** Math.floor(Math.log10(target));
  return Math.min(Number.MAX_VALUE, Math.ceil(target / unit) * unit);
});
const series = computed(() =>
  props.tariffs.map((tariff, index) => ({
    tariff,
    start: plotCost(tariff, 0),
    end: plotCost(tariff, maximum.value),
    color: colors[index % colors.length]!,
    dash: dashes[(index + Math.floor(index / colors.length)) % dashes.length]!,
  })),
);

const verticalAxis = computed(() => {
  const bounds = series.value.reduce(
    ({ low, high }, { start, end }) => ({
      low: Math.min(low, start),
      high: Math.max(high, end),
    }),
    { low: 0, high: 0 },
  );
  // Scale the bounds before subtracting so opposite large values stay finite.
  const scale = Math.max(1, -bounds.low, bounds.high);
  return {
    low: bounds.low / scale,
    high: bounds.high / scale || (bounds.low === 0 ? 1 : 0),
    scale,
  };
});
const xTicks = computed(() =>
  [0, 0.25, 0.5, 0.75, 1].map((fraction) => maximum.value * fraction),
);
const yTicks = computed(() => {
  const { low, high, scale } = verticalAxis.value;
  return [0, 0.25, 0.5, 0.75, 1].map(
    (fraction) => (low + fraction * (high - low)) * scale,
  );
});

function xAt(value: number): number {
  return left + (value / maximum.value) * (right.value - left);
}

function yAt(value: number): number {
  const { low, high, scale } = verticalAxis.value;
  return bottom - ((value / scale - low) / (high - low)) * (bottom - top);
}

function displayCost(tariff: ChartTariff): string {
  const value = tariff.costAtConsumption(consumption.value, firstYear.value);
  return value === null ? "—" : euro.value.format(value);
}
</script>

<template>
  <div ref="container" class="cost-chart">
    <fieldset class="year">
      <legend>{{ text.year }}</legend>
      <label>
        <input v-model="firstYear" :name="id" type="radio" :value="true" />
        {{ text.firstYear }}
      </label>
      <label>
        <input v-model="firstYear" :name="id" type="radio" :value="false" />
        {{ text.laterYears }}
      </label>
    </fieldset>

    <svg
      :viewBox="`0 0 ${width} ${height}`"
      role="img"
      :aria-label="text.title"
    >
      <text :x="left" y="14">{{ text.cost }}</text>
      <text :x="(left + right) / 2" :y="height - 7" text-anchor="middle">
        {{ text.consumption }}
      </text>
      <g v-for="(tick, index) in yTicks" :key="index">
        <line
          class="grid-line"
          :x1="left"
          :x2="right"
          :y1="yAt(tick)"
          :y2="yAt(tick)"
        />
        <text :x="left - 6" :y="yAt(tick) + 4" text-anchor="end">
          {{ axisValue(tick) }}
        </text>
      </g>
      <line
        v-if="verticalAxis.low < 0 && verticalAxis.high > 0"
        class="zero-line"
        :x1="left"
        :x2="right"
        :y1="yAt(0)"
        :y2="yAt(0)"
      />
      <g v-for="tick in xTicks" :key="tick">
        <line
          class="grid-line"
          :x1="xAt(tick)"
          :x2="xAt(tick)"
          :y1="top"
          :y2="bottom"
        />
        <text :x="xAt(tick)" :y="bottom + 18" text-anchor="middle">
          {{ axisValue(tick) }}
        </text>
      </g>
      <line
        class="cursor-line"
        :x1="xAt(consumption)"
        :x2="xAt(consumption)"
        :y1="top"
        :y2="bottom"
      />
      <g v-for="{ tariff, start, end, color, dash } in series" :key="tariff.id">
        <line
          class="tariff-line"
          :x1="left"
          :y1="yAt(start)"
          :x2="right"
          :y2="yAt(end)"
          :stroke="color"
          :stroke-dasharray="dash"
        />
        <circle
          :cx="xAt(consumption)"
          :cy="yAt(plotCost(tariff, consumption))"
          r="3.5"
          :fill="color"
        />
      </g>
    </svg>

    <div class="selection">
      <label :for="`${id}-consumption`">{{ text.selection }}</label>
      <output :for="`${id}-consumption`"
        >{{ number.format(consumption) }} kWh</output
      >
      <input
        :id="`${id}-consumption`"
        v-model.number="consumption"
        type="range"
        min="0"
        :max="maximum"
        step="any"
        :aria-valuetext="`${number.format(consumption)} kWh`"
      />
    </div>
    <ul class="selected-costs" role="list" :aria-label="text.selectedCosts">
      <li v-for="{ tariff, color, dash } in series" :key="tariff.id">
        <svg viewBox="0 0 28 12" width="28" height="12" aria-hidden="true">
          <line
            class="tariff-line"
            x1="1"
            y1="6"
            x2="27"
            y2="6"
            :stroke="color"
            :stroke-dasharray="dash"
          />
        </svg>
        <span>{{ tariff.name }}</span>
        <strong>{{ displayCost(tariff) }}</strong>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.cost-chart {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.year {
  display: flex;
  flex-wrap: wrap;
  column-gap: 20px;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.year legend,
.selection label {
  padding: 0;
  font-weight: 500;
}

.year label {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  cursor: pointer;
}

.year input {
  width: 20px;
  height: 20px;
  margin: 0;
}

.cost-chart > svg {
  display: block;
  width: 100%;
}

svg text {
  fill: var(--secondary-text-color, #666);
  font: inherit;
  font-size: 11px;
}

.grid-line,
.zero-line,
.cursor-line {
  stroke: var(--divider-color, #ddd);
}

.zero-line,
.cursor-line {
  stroke: var(--secondary-text-color, #666);
}

.cursor-line {
  stroke-dasharray: 3 4;
}

.tariff-line {
  stroke-width: 2.5;
  stroke-linecap: round;
  vector-effect: non-scaling-stroke;
}

.selection {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 4px 16px;
}

.selection input {
  width: 100%;
  min-height: 44px;
  margin: 0;
}

.selection output {
  font-variant-numeric: tabular-nums;
}

.selected-costs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr));
  gap: 8px 16px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.selected-costs li {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  align-items: center;
  gap: 8px;
  padding-block: 4px;
  border-bottom: 1px solid var(--divider-color, #ddd);
  overflow-wrap: anywhere;
}

.selected-costs strong {
  font-variant-numeric: tabular-nums;
}
</style>
