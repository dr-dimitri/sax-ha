<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch } from "vue";
import { tariffChart } from "../tariff-chart";
import { formatSavingsDate, formatSavingsNumber } from "../savings";
import type { HomeAssistant, TariffPriceSeries } from "../types";
const props = defineProps<{
  series: TariffPriceSeries | null;
  hass?: HomeAssistant;
  loading?: boolean;
}>();
const german = computed(() => props.hass?.language?.startsWith("de") ?? true);
const text = computed(() =>
  german.value
    ? {
        empty: "Für diesen Tag sind noch keine Preise verfügbar.",
        partial:
          "Für Teile des Tages fehlen Preise. Die Lücken werden nicht aufgefüllt.",
        loading: "Preise werden geladen …",
        title: "Strompreise im Tagesverlauf in Cent pro Kilowattstunde",
        hint: "Preisdetails durch Antippen oder mit den Pfeiltasten.",
        table: "Preise als Tabelle",
        from: "Von",
        to: "Bis",
        price: "Preis",
        gap: "Keine Preisdaten",
        now: "Jetzt",
      }
    : {
        empty: "Prices are not available for this day yet.",
        partial: "Prices are missing for parts of the day. Gaps remain empty.",
        loading: "Loading prices …",
        title:
          "Electricity prices throughout the day in cents per kilowatt hour",
        hint: "Tap the chart or use the arrow keys for price details.",
        table: "Prices as a table",
        from: "From",
        to: "To",
        price: "Price",
        gap: "No price data",
        now: "Now",
      },
);
const container = ref<HTMLElement>();
const width = ref(620);
let observer: ResizeObserver | undefined;
onMounted(() => {
  if (typeof ResizeObserver === "undefined" || !container.value) return;
  observer = new ResizeObserver((entries) => {
    width.value = Math.max(180, entries[0]?.contentRect.width ?? 620);
  });
  observer.observe(container.value);
});
onBeforeUnmount(() => observer?.disconnect());
const chart = computed(() => tariffChart(props.series, width.value));
const selected = ref<number | null>(null);
const missing = ref(false);
watch(
  () => props.series,
  () => {
    selected.value = null;
    missing.value = false;
  },
);
const number = (value: unknown) =>
  formatSavingsNumber(value, props.hass, 2) ?? "—";
const offsetChanges = computed(() => {
  if (!props.series) return false;
  try {
    const formatter = new Intl.DateTimeFormat("en", {
      timeZone: props.series.time_zone,
      timeZoneName: "shortOffset",
    });
    const offset = (at: number) =>
      formatter
        .formatToParts(new Date(at))
        .find((part) => part.type === "timeZoneName")?.value;
    return (
      offset(Date.parse(props.series.start)) !==
      offset(Date.parse(props.series.end) - 1)
    );
  } catch {
    return false;
  }
});
const time = (value: string, detail = false) =>
  formatSavingsDate(value, props.hass, {
    ...(detail && offsetChanges.value
      ? ({
          hour: "2-digit",
          minute: "2-digit",
          timeZoneName: "shortOffset",
        } as const)
      : ({ timeStyle: "short" } as const)),
    timeZone: props.series?.time_zone,
  }) ?? "—";
const selection = computed(() =>
  selected.value === null ? null : chart.value.slots[selected.value],
);
const now = computed(() => Date.parse(props.series?.now ?? ""));
const nowVisible = computed(
  () => now.value >= chart.value.start && now.value < chart.value.end,
);
const timeTicks = computed(() => [
  chart.value.start,
  chart.value.start + (chart.value.end - chart.value.start) / 2,
  chart.value.end,
]);
function inspect(event: PointerEvent) {
  const target = event.currentTarget as SVGElement;
  const bounds = target.getBoundingClientRect();
  const graphX = ((event.clientX - bounds.left) / bounds.width) * width.value;
  const at =
    chart.value.start +
    ((graphX - 48) / (width.value - 60)) *
      (chart.value.end - chart.value.start);
  const index = chart.value.slots.findIndex(
    (slot) => at >= slot.from && at < slot.to,
  );
  selected.value = index < 0 ? null : index;
  missing.value = index < 0;
}
function move(event: KeyboardEvent) {
  if (
    !["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key) ||
    !chart.value.slots.length
  )
    return;
  event.preventDefault();
  missing.value = false;
  selected.value =
    event.key === "Home"
      ? 0
      : event.key === "End"
        ? chart.value.slots.length - 1
        : Math.max(
            0,
            Math.min(
              chart.value.slots.length - 1,
              (selected.value ?? -1) + (event.key === "ArrowRight" ? 1 : -1),
            ),
          );
}
</script>
<template>
  <div ref="container" class="tariff-price-chart" :aria-busy="loading">
    <p v-if="loading" role="status">{{ text.loading }}</p>
    <div
      v-else-if="!chart.slots.length"
      class="tariff-price-chart__empty"
      role="status"
    >
      {{ text.empty }}
    </div>
    <template v-else>
      <p
        v-if="series?.status === 'partial'"
        class="tariff-price-chart__partial"
      >
        {{ text.partial }}
      </p>
      <svg
        :viewBox="`0 0 ${width} 252`"
        preserveAspectRatio="none"
        role="img"
        :aria-label="`${text.title}. ${text.hint}`"
        tabindex="0"
        @pointermove="inspect"
        @pointerdown="inspect"
        @keydown="move"
      >
        <title>{{ text.title }}</title>
        <text x="48" y="15">ct/kWh</text>
        <g v-for="tick in chart.ticks" :key="tick">
          <line
            x1="48"
            :x2="width - 12"
            :y1="chart.y(tick)"
            :y2="chart.y(tick)"
            class="tariff-price-chart__grid"
          />
          <text x="40" :y="chart.y(tick) + 4" text-anchor="end">
            {{ number(tick) }}
          </text>
        </g>
        <path :d="chart.path" class="tariff-price-chart__line" />
        <line
          v-if="nowVisible"
          :x1="chart.x(now)"
          :x2="chart.x(now)"
          y1="25"
          y2="216"
          class="tariff-price-chart__now"
        />
        <text
          v-if="nowVisible"
          :x="Math.max(68, Math.min(width - 30, chart.x(now)))"
          y="23"
          text-anchor="middle"
        >
          {{ text.now }}
        </text>
        <g v-if="selection">
          <line
            :x1="chart.x(selection.from)"
            :x2="chart.x(selection.to)"
            :y1="chart.y(selection.price_ct_kwh)"
            :y2="chart.y(selection.price_ct_kwh)"
            class="tariff-price-chart__selected"
          />
        </g>
        <text
          v-for="(tick, index) in timeTicks"
          :key="tick"
          :x="chart.x(tick)"
          y="244"
          :text-anchor="index === 0 ? 'start' : index === 2 ? 'end' : 'middle'"
        >
          {{ index === 2 ? "24:00" : time(new Date(tick).toISOString()) }}
        </text>
      </svg>
      <p class="tariff-price-chart__detail" aria-live="polite">
        {{
          selection
            ? `${time(selection.start, true)}–${time(selection.end, true)} · ${number(selection.price_ct_kwh)} ct/kWh`
            : missing
              ? text.gap
              : text.hint
        }}
      </p>
      <details>
        <summary>{{ text.table }}</summary>
        <div class="tariff-price-chart__scroll">
          <table>
            <thead>
              <tr>
                <th>{{ text.from }}</th>
                <th>{{ text.to }}</th>
                <th>{{ text.price }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="slot in chart.slots" :key="slot.start">
                <td>{{ time(slot.start, true) }}</td>
                <td>{{ time(slot.end, true) }}</td>
                <td>{{ number(slot.price_ct_kwh) }} ct/kWh</td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>
    </template>
  </div>
</template>
<style>
.tariff-price-chart {
  min-width: 0;
}
.tariff-price-chart svg {
  display: block;
  width: 100%;
  height: 240px;
  overflow: visible;
  touch-action: pan-y;
}
.tariff-price-chart svg text {
  fill: var(--secondary-text-color, #666);
  font-size: 14px;
}
.tariff-price-chart__line {
  fill: none;
  stroke: var(--primary-color, #03a9f4);
  stroke-width: 3;
  vector-effect: non-scaling-stroke;
}
.tariff-price-chart__grid {
  stroke: var(--divider-color, #ddd);
  vector-effect: non-scaling-stroke;
}
.tariff-price-chart__now {
  stroke: var(--secondary-text-color, #666);
  stroke-dasharray: 4;
  vector-effect: non-scaling-stroke;
}
.tariff-price-chart__selected {
  stroke: var(--success-color, #38964b);
  stroke-width: 6;
  vector-effect: non-scaling-stroke;
}
.tariff-price-chart__empty {
  min-height: 240px;
  display: grid;
  place-items: center;
  text-align: center;
  color: var(--secondary-text-color, #666);
}
.tariff-price-chart__detail,
.tariff-price-chart__partial {
  min-height: 20px;
  color: var(--secondary-text-color, #666);
  font-size: 14px;
}
.tariff-price-chart summary {
  cursor: pointer;
  min-height: 32px;
  padding: 6px 0;
}
.tariff-price-chart__scroll {
  overflow: auto;
}
.tariff-price-chart table {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}
.tariff-price-chart th,
.tariff-price-chart td {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid var(--divider-color, #ddd);
  white-space: nowrap;
}
.tariff-price-chart th:last-child,
.tariff-price-chart td:last-child {
  text-align: right;
}
</style>
