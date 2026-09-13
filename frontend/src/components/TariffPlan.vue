<script setup lang="ts">
import { computed, inject, useId } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import {
  finiteValue,
  formatSavingsDate,
  formatSavingsNumber,
} from "../savings";
import type { HomeAssistant } from "../types";

const props = defineProps<{ hass?: HomeAssistant }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const id = useId();
const text = computed(() =>
  dashboard?.language.value === "de"
    ? {
        tariff: "Tarifpreisfenster",
        from: "Von",
        to: "Bis",
        price: "Arbeitspreis",
        status: "Status",
        now: "jetzt",
        base: "Grundpreis",
        low: "Niedertarif",
        lowUntil: "Niedertarif aktiv bis",
        notLow: "Aktuell kein Niedertarif.",
        rule: "Die Tarifpreisfenster bestimmen die verbindlichen Ladezeiten. Niedertarif ist die niedrigste täglich tatsächlich vorkommende Preisstufe, einschließlich des Grundpreises in Fensterlücken. Die SOC-Ladung darf nur im Niedertarif laden; SOC-Grenzen und aktive Monate gelten weiterhin.",
        configure:
          "Zeiten sind nur unter Konfigurieren → Tarifpreisfenster änderbar. Bisherige separate Netzladezeiten sind bei diesem Tarif unwirksam.",
        noLowTariff:
          "Tarifdaten fehlen oder sind ungültig. Die SOC-Ladung bleibt gesperrt, bis gültige Tarifdaten vorliegen.",
        feed: "Einspeisevergütung",
        next: "Nächster Preiswechsel",
        unavailable: "Nicht verfügbar",
        noPrice:
          "Derzeit gilt kein Preis. Bitte die Tarifkonfiguration prüfen.",
      }
    : {
        tariff: "Tariff price windows",
        from: "From",
        to: "To",
        price: "Import price",
        status: "Status",
        now: "now",
        base: "Base price",
        low: "Low tariff",
        lowUntil: "Low tariff active until",
        notLow: "The low tariff is not currently active.",
        rule: "The tariff price windows define the binding charging times. The low tariff is the lowest price level that actually occurs each day, including the base price in gaps between windows. SOC charging is only allowed during the low tariff; SOC limits and active months still apply.",
        configure:
          "Times can only be changed under Configure → Tariff price windows. Previously configured separate grid charging times have no effect for this tariff.",
        noLowTariff:
          "Tariff data is missing or invalid. SOC charging remains blocked until valid tariff data is available.",
        feed: "Feed-in remuneration",
        next: "Next price change",
        unavailable: "Unavailable",
        noPrice:
          "No price currently applies. Please check the tariff configuration.",
      },
);
const price = computed(() =>
  dashboard?.entity("sensor", "economics_current_import_price"),
);
const tariffPrice = (value: unknown) => {
  const formatted = formatSavingsNumber(value, props.hass, 4);
  return formatted === null ? text.value.unavailable : `${formatted} EUR/kWh`;
};
const timestamp = (value: unknown) =>
  formatSavingsDate(value, props.hass) ?? text.value.unavailable;
const attributes = computed(() => price.value?.state?.attributes ?? {});
const tariffVisible = computed(
  () => attributes.value.tariff_type === "time_of_use",
);
type TariffWindow = {
  start: string;
  end: string;
  price_eur_kwh: unknown;
  low_tariff?: unknown;
};
const windows = computed<TariffWindow[]>(() =>
  Array.isArray(attributes.value.windows)
    ? attributes.value.windows.filter(
        (window): window is TariffWindow =>
          !!window &&
          typeof window === "object" &&
          typeof window.start === "string" &&
          typeof window.end === "string",
      )
    : [],
);
const reason = computed(() => attributes.value.unavailable_reason);
const hasPrice = computed(
  () =>
    price.value?.available === true &&
    finiteValue(price.value.state?.state) !== null &&
    reason.value == null,
);
const lowTariffAvailable = computed(
  () =>
    hasPrice.value &&
    finiteValue(attributes.value.low_tariff_price_eur_kwh) !== null &&
    typeof attributes.value.low_tariff_active === "boolean" &&
    (attributes.value.low_tariff_active === false ||
      lowTariffUntil.value !== null) &&
    typeof attributes.value.base_price_is_low_tariff === "boolean" &&
    Array.isArray(attributes.value.windows) &&
    windows.value.length === attributes.value.windows.length &&
    windows.value.every(
      (window) =>
        typeof window.low_tariff === "boolean" &&
        finiteValue(window.price_eur_kwh) !== null,
    ),
);
const lowTariffUntil = computed(() =>
  formatSavingsDate(attributes.value.low_tariff_valid_until, props.hass),
);
const lowTariffActive = computed(
  () =>
    lowTariffAvailable.value &&
    attributes.value.low_tariff_active === true &&
    lowTariffUntil.value !== null,
);
const isLow = (window: TariffWindow) =>
  lowTariffAvailable.value && window.low_tariff === true;
const baseLow = computed(
  () =>
    lowTariffAvailable.value &&
    attributes.value.base_price_is_low_tariff === true,
);
const status = (current: boolean, low: boolean) =>
  [current ? text.value.now : "", low ? text.value.low : ""]
    .filter(Boolean)
    .join(" · ");
const active = computed(() => {
  const value = attributes.value.active_window;
  return value && typeof value === "object"
    ? (value as { start?: unknown; end?: unknown })
    : null;
});
const isActive = (window: TariffWindow) =>
  hasPrice.value &&
  finiteValue(window.price_eur_kwh) !== null &&
  active.value?.start === window.start &&
  active.value?.end === window.end;
const baseActive = computed(
  () =>
    hasPrice.value &&
    active.value === null &&
    finiteValue(attributes.value.base_price_eur_kwh) !== null,
);
const clock = (value: string) =>
  formatSavingsDate(
    `2000-01-01T${value.length === 5 ? `${value}:00` : value}Z`,
    props.hass,
    { timeStyle: "short", timeZone: "UTC" },
  ) ?? value.slice(0, 5);
</script>

<template>
  <section
    v-if="tariffVisible"
    class="tariff-plan"
    :aria-labelledby="`${id}-tariff`"
  >
    <h2 :id="`${id}-tariff`">{{ text.tariff }}</h2>
    <p>{{ text.rule }}</p>
    <p>{{ text.configure }}</p>
    <div class="tariff-plan__scroll">
      <table class="tariff-plan__table">
        <thead>
          <tr>
            <th :aria-label="text.status"></th>
            <th>{{ text.from }}</th>
            <th>{{ text.to }}</th>
            <th>{{ text.price }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(window, index) in windows"
            :key="index"
            :class="{
              'tariff-plan__current': isActive(window),
              'tariff-plan__low': isLow(window),
            }"
          >
            <td>{{ status(isActive(window), isLow(window)) }}</td>
            <td>{{ clock(window.start) }}</td>
            <td>{{ clock(window.end) }}</td>
            <td>{{ tariffPrice(window.price_eur_kwh) }}</td>
          </tr>
          <tr
            :class="{
              'tariff-plan__current': baseActive,
              'tariff-plan__low': baseLow,
            }"
          >
            <td>{{ status(baseActive, baseLow) }}</td>
            <td colspan="2">{{ text.base }}</td>
            <td>{{ tariffPrice(attributes.base_price_eur_kwh) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="lowTariffAvailable" class="tariff-plan__low-status">
      <strong>{{ text.low }}:</strong>
      {{ tariffPrice(attributes.low_tariff_price_eur_kwh) }}.
      <template v-if="lowTariffActive">
        {{ text.lowUntil }} {{ lowTariffUntil }}.
      </template>
      <template v-else>{{ text.notLow }}</template>
    </p>
    <p v-else class="tariff-plan__low-unavailable">{{ text.noLowTariff }}</p>
    <p>
      <strong>{{ text.feed }}:</strong>
      {{ tariffPrice(attributes.feed_in_price_eur_kwh) }}
    </p>
    <p v-if="!hasPrice">
      {{ text.noPrice
      }}<span v-if="typeof reason === 'string' && reason"> ({{ reason }})</span>
    </p>
    <p v-else-if="attributes.next_price_change_at">
      <strong>{{ text.next }}:</strong>
      {{ timestamp(attributes.next_price_change_at) }}
    </p>
  </section>
</template>

<style>
.tariff-plan {
  min-width: 0;
  padding: 24px;
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  box-shadow: var(--ha-card-box-shadow, none);
  color: var(--primary-text-color, #212121);
}
.tariff-plan h2 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.5;
}
.tariff-plan p {
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.tariff-plan p:last-child {
  margin-bottom: 0;
}
.tariff-plan__scroll {
  overflow-x: auto;
}
.tariff-plan__table {
  border-collapse: collapse;
  width: 100%;
  line-height: 1.5;
  font-variant-numeric: tabular-nums;
}
.tariff-plan__table th,
.tariff-plan__table td {
  padding: 10px 8px;
  text-align: left;
  white-space: nowrap;
  border-bottom: 1px solid var(--divider-color, #e0e0e0);
}
.tariff-plan__table th:last-child,
.tariff-plan__table td:last-child {
  text-align: right;
}
.tariff-plan__current {
  font-weight: 600;
  background: var(
    --secondary-background-color,
    color-mix(in srgb, currentColor 8%, transparent)
  );
}
@media (max-width: 600px) {
  .tariff-plan {
    padding: 20px;
  }
}
@container sax-content (min-width: 860px) {
  .tariff-plan {
    padding: 18px;
  }
  .tariff-plan h2 {
    margin-bottom: 12px;
    font-size: 16px;
  }
  .tariff-plan p {
    margin-top: 10px;
    line-height: 1.5;
  }
  .tariff-plan__table th,
  .tariff-plan__table td {
    padding: 7px 8px;
  }
}
</style>
