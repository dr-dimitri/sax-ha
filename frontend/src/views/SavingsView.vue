<script setup lang="ts">
import { computed, inject, ref, useId, watch } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import {
  finiteValue,
  formatSavingsDate,
  formatSavingsNumber,
  useSavingsStatistics,
} from "../savings";
import type { HomeAssistant } from "../types";

const props = defineProps<{ hass?: HomeAssistant; entryId?: string }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const id = useId();
const german = computed(() => dashboard?.language.value === "de");
const text = computed(() =>
  german.value
    ? {
        loading: "Die Statistik wird geladen …",
        unavailable: "Nicht verfügbar",
        unknown: "Unbekannt",
        payback: "Amortisation",
        investment:
          "Für die Amortisationswerte bitte die Investitionskosten unter „Geräte & Dienste → SAX Power Home → Konfigurieren → Wirtschaftlichkeit“ hinterlegen.",
        prior: "Bereits vor Bilanzbeginn berücksichtigt",
        net: "Netto-Ersparnis",
        started: "Bilanzbeginn",
        periods: "Kalenderwerte",
        day: "Heute bisher",
        week: "Diese Woche bisher",
        month: "Dieser Monat bisher",
        year: "Dieses Jahr bisher",
        tariff: "Tarifplan (tageszeitabhängig)",
        from: "Von",
        to: "Bis",
        price: "Arbeitspreis",
        now: "jetzt",
        base: "Grundpreis",
        feed: "Einspeisevergütung",
        next: "Nächster Preiswechsel",
        noPrice:
          "Derzeit gilt kein Preis. Bitte die Tarifkonfiguration prüfen.",
        range: "Freier Zeitraum",
        apply: "Zeitraum anzeigen",
        refresh: "Aktualisieren",
        selected: "Netto-Ersparnis im gewählten Zeitraum",
        chart: "Verlauf im gewählten Zeitraum",
        table: "Werte als Tabelle",
        noData: "Für diesen Zeitraum sind keine Recorder-Daten vorhanden.",
        noChartData:
          "Für das Diagramm liegen noch keine zusammengefassten Recorder-Daten vor.",
        chartHint:
          "Die Balken basieren auf zusammengefassten Stundenwerten. Der Zeitraumwert kann bereits neuere Fünf-Minuten-Daten enthalten.",
        noRecorder: "Die Recorder-Statistik ist derzeit nicht verfügbar.",
        failed:
          "Die Statistik konnte nicht geladen werden. Bitte erneut versuchen.",
        invalid:
          "Bitte ein gültiges Anfangs- und Enddatum wählen. Das Ende darf nicht vor dem Anfang liegen.",
        explain: "Hinweise zur Berechnung und Datenbasis",
        netHint:
          "Grundlage sind vermiedene Netzbezugskosten minus Netzladekosten und entgangene Einspeisevergütung. Spätere Kosten reduzieren das aktuelle Ergebnis; Mehrkosten erscheinen als negativer Wert.",
        calendarHint:
          "Kalenderwerte stammen aus der Recorder-Langzeitstatistik der Netto-Ersparnis. Bei aktualisierten Installationen kann diese Aufzeichnung jünger als der angezeigte Bilanzbeginn sein.",
        rangeHint:
          "Für freie Zeiträume fließen nur Daten seit Beginn dieser Recorder-Aufzeichnung ein. Eine frühere Auswahl erfindet keine Werte. Fehlt die Historie oder ist die Ergebnis-Entität vom Recorder ausgeschlossen, bleiben Wert und Diagramm unbekannt beziehungsweise leer. Bei einem manuellen Bilanzneustart innerhalb der Auswahl kann der Recorder signierte Änderungen vor und nach dem Neustart zusammenfassen. Der Vorlaufbetrag verändert diese Zeitraumwerte nicht.",
        disabled:
          "Die Wirtschaftlichkeitsberechnung ist deaktiviert. Bitte unter „Geräte & Dienste → SAX Power Home → Konfigurieren → Wirtschaftlichkeit“ konfigurieren.",
        price_unavailable:
          "Der Strompreis ist derzeit nicht verfügbar. Aktuelle Zeitraumwerte können unvollständig sein.",
        origin_unavailable:
          "Die Herkunft der Ladeenergie ist derzeit nicht bestimmbar.",
        partial_price_coverage:
          "Für einen Teil der Energie fehlte heute ein Preis. Das Ergebnis kann unvollständig sein.",
        storage_error:
          "Die Wirtschaftlichkeitsbilanz ist wegen eines Speicherfehlers angehalten. Bitte in den Home-Assistant-Reparaturen das Korrupt-Backup wiederherstellen; bloßes Neuladen startet keine neue Bilanz.",
        missing: "Die Wirtschaftlichkeitsdaten sind momentan nicht verfügbar.",
      }
    : {
        loading: "Loading statistics …",
        unavailable: "Unavailable",
        unknown: "Unknown",
        payback: "Payback",
        investment:
          "To show payback values, enter the investment cost under Devices & services → SAX Power Home → Configure → Economics.",
        prior: "Already accounted for before accounting started",
        net: "Net savings",
        started: "Accounting started",
        periods: "Calendar values",
        day: "Today so far",
        week: "This week so far",
        month: "This month so far",
        year: "This year so far",
        tariff: "Tariff schedule (time of use)",
        from: "From",
        to: "To",
        price: "Import price",
        now: "now",
        base: "Base price",
        feed: "Feed-in remuneration",
        next: "Next price change",
        noPrice:
          "No price currently applies. Please check the tariff configuration.",
        range: "Custom period",
        apply: "Show period",
        refresh: "Refresh",
        selected: "Net savings in the selected period",
        chart: "Changes in the selected period",
        table: "Show values as a table",
        noData: "There are no Recorder data for this period.",
        noChartData: "There are no aggregated Recorder data for the chart yet.",
        chartHint:
          "The bars use aggregated hourly values. The period value may already include more recent five-minute data.",
        noRecorder: "Recorder statistics are currently unavailable.",
        failed: "Statistics could not be loaded. Please try again.",
        invalid:
          "Please choose valid start and end dates. The end must not precede the start.",
        explain: "Calculation and data sources",
        netHint:
          "Net savings are avoided grid import costs minus grid charging costs and forgone feed-in remuneration. Later costs reduce the current result; additional costs appear as negative values.",
        calendarHint:
          "Calendar values come from the long-term Recorder statistics for net savings. After an upgrade, this history may start later than the displayed accounting start.",
        rangeHint:
          "Custom periods only include data since this Recorder history began. Choosing an earlier date does not invent values. If history is missing or the result entity is excluded from Recorder, the value and chart remain unknown or empty. A manual accounting restart within the selection may combine signed changes before and after the restart. The prior result does not alter these period values.",
        disabled:
          "The economics calculation is disabled. Configure it under Devices & services → SAX Power Home → Configure → Economics.",
        price_unavailable:
          "The electricity price is currently unavailable. Current period values may be incomplete.",
        origin_unavailable:
          "The origin of the charging energy cannot currently be determined.",
        partial_price_coverage:
          "A price was missing for some of today's energy. The result may be incomplete.",
        storage_error:
          "Accounting has stopped because of a storage error. Restore the corrupt backup in Home Assistant Repairs; reloading alone does not start a new ledger.",
        missing: "Economics data are currently unavailable.",
      },
);
const configured = computed(() =>
  dashboard?.entity("binary_sensor", "economics_investment_configured"),
);
const progress = computed(() =>
  dashboard?.entity("sensor", "economics_amortization_progress"),
);
const remaining = computed(() =>
  dashboard?.entity("sensor", "economics_remaining_to_payback"),
);
const roi = computed(() => dashboard?.entity("sensor", "economics_roi"));
const net = computed(() =>
  dashboard?.entity("sensor", "economics_net_savings"),
);
const status = computed(() => dashboard?.entity("sensor", "economics_status"));
const price = computed(() =>
  dashboard?.entity("sensor", "economics_current_import_price"),
);
const progressValue = computed(() =>
  progress.value?.available ? finiteValue(progress.value.state?.state) : null,
);
const progressBounded = computed(() =>
  progressValue.value === null
    ? null
    : Math.max(0, Math.min(100, progressValue.value)),
);
const money = (value: unknown) => {
  const formatted = formatSavingsNumber(value, props.hass);
  return formatted === null ? text.value.unavailable : `${formatted} €`;
};
const tariffPrice = (value: unknown) => {
  const formatted = formatSavingsNumber(value, props.hass, 4);
  return formatted === null ? text.value.unavailable : `${formatted} EUR/kWh`;
};
const timestamp = (value: unknown) =>
  formatSavingsDate(value, props.hass) ?? text.value.unavailable;
const dateLabel = (value: string) =>
  formatSavingsDate(`${value}T12:00:00Z`, props.hass, {
    dateStyle: "medium",
    timeZone: "UTC",
  }) ?? value;
const statusMessage = computed(() => {
  const state = status.value?.available ? status.value.state?.state : undefined;
  if (state === "active") return null;
  if (
    state === "disabled" ||
    state === "price_unavailable" ||
    state === "origin_unavailable" ||
    state === "partial_price_coverage" ||
    state === "storage_error"
  )
    return text.value[state];
  return text.value.missing;
});
const attributes = computed(() => price.value?.state?.attributes ?? {});
const tariffVisible = computed(
  () => attributes.value.tariff_type === "time_of_use",
);
type TariffWindow = { start: string; end: string; price_eur_kwh: unknown };
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
    price.value?.available &&
    finiteValue(price.value.state?.state) !== null &&
    reason.value == null,
);
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
const statistics = useSavingsStatistics(
  () => props.hass,
  () => props.entryId,
  () => net.value?.metadata.entity_id,
);
const startDate = ref("");
const endDate = ref("");
let previousSelection: { start: string; end: string } | null = null;
watch(statistics.data, (value) => {
  if (!value) return;
  if (
    (!startDate.value && !endDate.value) ||
    (startDate.value === previousSelection?.start &&
      endDate.value === previousSelection?.end)
  ) {
    startDate.value = value.selected.start_date;
    endDate.value = value.selected.end_date;
  }
  previousSelection = {
    start: value.selected.start_date,
    end: value.selected.end_date,
  };
});
watch(
  () => props.entryId,
  () => {
    startDate.value = "";
    endDate.value = "";
    previousSelection = null;
  },
);
const statisticsError = computed(() =>
  statistics.error.value === "invalid"
    ? text.value.invalid
    : statistics.error.value === "failed"
      ? text.value.failed
      : statistics.error.value === "unavailable" ||
          statistics.data.value?.status === "recorder_unavailable"
        ? text.value.noRecorder
        : null,
);
const periodKeys = ["day", "week", "month", "year"] as const;
const buckets = computed(() => statistics.data.value?.selected.buckets ?? []);
const chartElement = ref<SVGSVGElement | null>(null);
const chartWidth = ref(720);
watch(chartElement, (element, _previous, cleanup) => {
  if (!element) return;
  const measure = (width: number) => {
    if (Number.isFinite(width) && width > 0) chartWidth.value = width;
  };
  measure(element.getBoundingClientRect().width);
  if (typeof ResizeObserver === "undefined") return;
  // A pixel-sized viewBox keeps dates and currency legible in narrow HA cards.
  const observer = new ResizeObserver((entries) => {
    for (const entry of entries) measure(entry.contentRect.width);
  });
  observer.observe(element);
  cleanup(() => observer.disconnect());
});
const chart = computed(() => {
  const values = buckets.value.map((item) => finiteValue(item.change));
  const high = Math.max(0, ...values.map((value) => value ?? 0));
  const low = Math.min(0, ...values.map((value) => value ?? 0));
  const extent = high - low || 1;
  const y = (value: number) => 20 + ((high - value) / extent) * 180;
  const selection = statistics.data.value?.selected;
  const start = Date.parse(selection?.start ?? "");
  const end = Date.parse(selection?.end ?? "");
  const duration = end - start;
  const highLabel = formatSavingsNumber(high, props.hass) ?? "";
  const lowLabel = formatSavingsNumber(low, props.hass) ?? "";
  const left = Math.max(
    56,
    Math.max(highLabel.length, lowLabel.length) * 7.1 + 12,
  );
  const right = chartWidth.value - 24;
  const plotWidth = Math.max(1, right - left);
  const x = (timestamp: string) =>
    left +
    Math.max(0, Math.min(1, (Date.parse(timestamp) - start) / duration)) *
      plotWidth;
  return {
    zero: y(0),
    high,
    low,
    highLabel,
    lowLabel,
    left,
    right,
    start: selection?.start ?? "",
    end: Number.isFinite(end) ? new Date(end - 1).toISOString() : "",
    // Recorder gaps and DST hours must retain their real position on the time axis.
    bars: buckets.value.map((item, index) => {
      const width = x(item.end) - x(item.start);
      return {
        ...item,
        value: values[index],
        x: x(item.start) + Math.min(2, width / 8),
        y: values[index] === null ? y(0) : y(Math.max(0, values[index]!)),
        height: values[index] === null ? 0 : Math.abs(y(values[index]!) - y(0)),
        width: Math.max(0, width - Math.min(4, width / 4)),
        label: timestamp(item.start),
      };
    }),
  };
});
const hasChart = computed(() =>
  buckets.value.some((bucket) => finiteValue(bucket.change) !== null),
);
const chartDate = (value: string) =>
  formatSavingsDate(
    value,
    props.hass,
    statistics.data.value?.selected.period === "hour"
      ? { timeStyle: "short" }
      : statistics.data.value?.selected.period === "month"
        ? { month: "short", year: "numeric" }
        : { day: "2-digit", month: "short" },
  ) ?? value;
</script>

<template>
  <div class="savings-view">
    <div class="savings-overview">
      <section
        v-if="configured?.available && configured.state?.state === 'off'"
        class="savings-card savings-payback"
        :aria-labelledby="`${id}-investment`"
      >
        <h2 :id="`${id}-investment`">{{ text.payback }}</h2>
        <p>{{ text.investment }}</p>
      </section>
      <section
        v-else-if="
          configured?.available &&
          configured.state?.state === 'on' &&
          (progress || remaining || roi || net || status)
        "
        class="savings-card savings-payback"
        :aria-labelledby="`${id}-payback`"
      >
        <h2 :id="`${id}-payback`">{{ text.payback }}</h2>
        <div v-if="progress" class="savings-progress">
          <h3 :id="`${id}-progress`">{{ progress.name }}</h3>
          <p class="savings-large">
            {{
              progressValue === null
                ? text.unavailable
                : `${formatSavingsNumber(progressValue, hass)} %`
            }}
          </p>
          <div
            class="savings-progress__track"
            :role="progressBounded === null ? undefined : 'meter'"
            :aria-labelledby="`${id}-progress`"
            :aria-valuemin="progressBounded === null ? undefined : 0"
            :aria-valuemax="progressBounded === null ? undefined : 100"
            :aria-valuenow="progressBounded ?? undefined"
          >
            <span
              v-if="progressBounded !== null"
              :style="{ width: `${progressBounded}%` }"
            ></span>
          </div>
        </div>
        <dl v-if="remaining || roi || net || status" class="savings-rows">
          <div v-if="remaining">
            <dt>{{ remaining.name }}</dt>
            <dd>
              {{ money(remaining.available ? remaining.state?.state : null) }}
            </dd>
          </div>
          <div v-if="roi">
            <dt>{{ text.prior }}</dt>
            <dd>
              {{
                money(
                  roi.available
                    ? (roi.state?.attributes.prior_result_eur ??
                        roi.state?.attributes.prior_result_eur_formatted)
                    : null,
                )
              }}
            </dd>
          </div>
          <div v-if="net">
            <dt>{{ text.net }}</dt>
            <dd>{{ money(net.available ? net.state?.state : null) }}</dd>
          </div>
          <div v-if="status">
            <dt>{{ text.started }}</dt>
            <dd>
              {{
                timestamp(
                  status.available
                    ? status.state?.attributes.economics_started_at
                    : null,
                )
              }}
            </dd>
          </div>
        </dl>
      </section>
      <section v-if="net" class="savings-periods" :aria-label="text.periods">
        <article
          v-for="period in periodKeys"
          :key="period"
          class="savings-card"
        >
          <h2>{{ text[period] }}</h2>
          <p class="savings-large">
            {{
              statistics.loading.value
                ? "…"
                : money(statistics.data.value?.periods[period].change)
            }}
          </p>
        </article>
      </section>
    </div>
    <section
      v-if="tariffVisible"
      class="savings-card savings-tariff"
      :aria-labelledby="`${id}-tariff`"
    >
      <h2 :id="`${id}-tariff`">{{ text.tariff }}</h2>
      <div class="savings-table-scroll">
        <table class="savings-table">
          <thead>
            <tr>
              <th aria-label="Status"></th>
              <th>{{ text.from }}</th>
              <th>{{ text.to }}</th>
              <th>{{ text.price }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(window, index) in windows"
              :key="index"
              :class="{ 'savings-current': isActive(window) }"
            >
              <td>{{ isActive(window) ? text.now : "" }}</td>
              <td>{{ clock(window.start) }}</td>
              <td>{{ clock(window.end) }}</td>
              <td>{{ tariffPrice(window.price_eur_kwh) }}</td>
            </tr>
            <tr :class="{ 'savings-current': baseActive }">
              <td>{{ baseActive ? text.now : "" }}</td>
              <td colspan="2">{{ text.base }}</td>
              <td>{{ tariffPrice(attributes.base_price_eur_kwh) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p>
        <strong>{{ text.feed }}:</strong>
        {{ tariffPrice(attributes.feed_in_price_eur_kwh) }}
      </p>
      <p v-if="!hasPrice">
        {{ text.noPrice
        }}<span v-if="typeof reason === 'string' && reason">
          ({{ reason }})</span
        >
      </p>
      <p v-else-if="attributes.next_price_change_at">
        <strong>{{ text.next }}:</strong>
        {{ timestamp(attributes.next_price_change_at) }}
      </p>
    </section>
    <section
      v-if="net"
      class="savings-card savings-range"
      :aria-labelledby="`${id}-range`"
    >
      <h2 :id="`${id}-range`">{{ text.range }}</h2>
      <form
        class="savings-dates"
        @submit.prevent="statistics.select(startDate, endDate)"
      >
        <label :for="`${id}-from`"
          >{{ text.from
          }}<input
            :id="`${id}-from`"
            v-model="startDate"
            type="date"
            required
            :max="endDate || undefined"
        /></label>
        <label :for="`${id}-to`"
          >{{ text.to
          }}<input
            :id="`${id}-to`"
            v-model="endDate"
            type="date"
            required
            :min="startDate || undefined"
        /></label>
        <button type="submit">{{ text.apply }}</button>
        <button
          type="button"
          :disabled="statistics.loading.value"
          @click="statistics.refresh"
        >
          {{ text.refresh }}
        </button>
      </form>
      <p v-if="statistics.loading.value" role="status">{{ text.loading }}</p>
      <p v-else-if="statisticsError" role="alert">{{ statisticsError }}</p>
      <template v-else-if="statistics.data.value">
        <p class="savings-selected-dates">
          {{ dateLabel(statistics.data.value.selected.start_date) }} –
          {{ dateLabel(statistics.data.value.selected.end_date) }}
        </p>
        <h3>{{ text.selected }}</h3>
        <p class="savings-large">
          {{ money(statistics.data.value.selected.change) }}
        </p>
        <h3 :id="`${id}-chart`">{{ text.chart }}</h3>
        <p class="savings-chart-hint">{{ text.chartHint }}</p>
        <template v-if="hasChart">
          <svg
            ref="chartElement"
            class="savings-chart"
            :viewBox="`0 0 ${chartWidth} 240`"
            role="img"
            :aria-labelledby="`${id}-chart`"
            :aria-describedby="`${id}-chart-description`"
          >
            <desc :id="`${id}-chart-description`">
              {{ text.net }}:
              {{ money(statistics.data.value.selected.change) }}.
              {{ text.table }}.
            </desc>
            <line
              :x1="chart.left - 2"
              :x2="chart.right + 2"
              :y1="chart.zero"
              :y2="chart.zero"
              class="savings-chart__axis"
            />
            <text :x="chart.left - 8" y="24" text-anchor="end">
              {{ chart.highLabel }}
            </text>
            <text :x="chart.left - 8" y="204" text-anchor="end">
              {{ chart.lowLabel }}
            </text>
            <text x="10" y="226">EUR</text>
            <text v-if="buckets.length" :x="chart.left" y="226">
              {{ chartDate(chart.start) }}
            </text>
            <text
              v-if="buckets.length > 1"
              :x="chart.right"
              y="226"
              text-anchor="end"
            >
              {{ chartDate(chart.end) }}
            </text>
            <rect
              v-for="(bar, index) in chart.bars"
              :key="index"
              :x="bar.x"
              :y="bar.y"
              :width="bar.width"
              :height="bar.height"
              class="savings-chart__bar"
              :class="{ 'savings-chart__bar--negative': (bar.value ?? 0) < 0 }"
            >
              <title>{{ bar.label }}: {{ money(bar.value) }}</title>
            </rect>
          </svg>
          <details class="savings-chart-table">
            <summary>{{ text.table }}</summary>
            <div class="savings-table-scroll">
              <table class="savings-table">
                <thead>
                  <tr>
                    <th>{{ text.from }}</th>
                    <th>{{ text.to }}</th>
                    <th>{{ text.net }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(bar, index) in chart.bars" :key="index">
                    <td>{{ bar.label }}</td>
                    <td>{{ timestamp(bar.end) }}</td>
                    <td>{{ money(bar.value) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>
        </template>
        <p
          v-if="!hasChart || statistics.data.value.selected.change === null"
          class="savings-empty"
        >
          {{
            statistics.data.value.selected.change === null
              ? text.noData
              : text.noChartData
          }}
        </p>
      </template>
    </section>
    <details class="savings-card savings-explanation">
      <summary>{{ text.explain }}</summary>
      <p>{{ text.netHint }}</p>
      <p>{{ text.calendarHint }}</p>
      <p>{{ text.rangeHint }}</p>
    </details>
    <p
      v-if="statusMessage && dashboard?.ready.value"
      class="savings-card savings-status"
      role="status"
    >
      {{ statusMessage }}
    </p>
  </div>
</template>

<style>
.savings-view {
  display: grid;
  gap: 20px;
  margin-top: 24px;
  min-width: 0;
}
.savings-overview {
  display: contents;
}
.savings-card {
  min-width: 0;
  padding: 24px;
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  box-shadow: var(--ha-card-box-shadow, none);
  color: var(--primary-text-color, #212121);
}
.savings-card h2 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.5;
}
.savings-card h3 {
  margin: 20px 0 8px;
  font-size: 16px;
  font-weight: 500;
}
.savings-card p {
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.savings-card p:last-child {
  margin-bottom: 0;
}
.savings-large {
  margin: 0 0 12px;
  font-size: 28px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}
.savings-progress__track {
  height: 16px;
  overflow: hidden;
  border-radius: 8px;
  background: var(--divider-color, #e0e0e0);
}
.savings-progress__track span {
  display: block;
  height: 100%;
  background: var(--info-color, #039be5);
}
.savings-rows {
  margin: 20px 0 0;
}
.savings-rows > div {
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--divider-color, #e0e0e0);
  line-height: 1.5;
}
.savings-rows > div:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}
.savings-rows dd {
  margin: 0;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.savings-periods {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 210px), 1fr));
  gap: 16px;
}
.savings-periods h2 {
  font-size: 16px;
}
.savings-table-scroll {
  overflow-x: auto;
}
.savings-table {
  border-collapse: collapse;
  width: 100%;
  line-height: 1.5;
  font-variant-numeric: tabular-nums;
}
.savings-table th,
.savings-table td {
  padding: 10px 8px;
  text-align: left;
  border-bottom: 1px solid var(--divider-color, #e0e0e0);
}
.savings-table th:last-child,
.savings-table td:last-child {
  text-align: right;
}
.savings-current {
  font-weight: 600;
  background: var(
    --secondary-background-color,
    color-mix(in srgb, currentColor 8%, transparent)
  );
}
.savings-dates {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: end;
}
.savings-dates label {
  display: grid;
  gap: 8px;
  flex: 1 1 180px;
  min-width: 0;
}
.savings-dates input,
.savings-dates button {
  box-sizing: border-box;
  font: inherit;
  min-height: 44px;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid var(--divider-color, #bdbdbd);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  color: var(--primary-text-color, #212121);
}
.savings-dates input {
  width: 100%;
  color-scheme: light dark;
}
.savings-dates button {
  cursor: pointer;
  color: var(--primary-color, #0288d1);
}
.savings-dates button:disabled {
  opacity: 0.6;
  cursor: default;
}
.savings-dates :focus-visible,
.savings-card summary:focus-visible {
  outline: 2px solid var(--primary-color, #03a9f4);
  outline-offset: 3px;
}
.savings-selected-dates,
.savings-empty {
  color: var(--secondary-text-color, #666);
}
.savings-chart {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
}
.savings-chart text {
  font-size: 12px;
  fill: var(--secondary-text-color, #666);
}
.savings-chart__axis {
  stroke: var(--primary-text-color, #212121);
  stroke-width: 1;
}
.savings-chart__bar {
  fill: var(--info-color, #039be5);
}
.savings-chart__bar--negative {
  fill: var(--error-color, #db4437);
}
.savings-card summary {
  cursor: pointer;
  min-height: 24px;
  line-height: 1.6;
  font-weight: 500;
}
.savings-chart-table {
  margin-top: 16px;
}
.savings-status {
  margin: 0;
  line-height: 1.6;
}
@container sax-content (min-width: 860px) {
  .savings-view {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;
    gap: 16px;
    margin-top: 16px;
  }
  .savings-view > * {
    grid-column: 1 / -1;
  }
  .savings-overview {
    display: grid;
    gap: 16px;
    min-width: 0;
  }
  .savings-overview:empty {
    display: none;
  }
  .savings-view:has(> .savings-overview > section):has(> .savings-tariff)
    > :is(.savings-overview, .savings-tariff) {
    grid-column: auto;
  }
  .savings-card {
    padding: 18px;
  }
  .savings-card h2 {
    margin-bottom: 12px;
    font-size: 16px;
  }
  .savings-card h3 {
    margin-top: 16px;
    font-size: 14px;
  }
  .savings-card p {
    margin-top: 10px;
    line-height: 1.5;
  }
  .savings-progress h3 {
    margin-top: 0;
  }
  .savings-card .savings-large {
    margin-top: 0;
    margin-bottom: 8px;
    font-size: 24px;
  }
  .savings-rows {
    margin-top: 12px;
  }
  .savings-rows > div {
    gap: 12px;
    padding: 8px 0;
  }
  .savings-rows dt {
    min-width: 0;
  }
  .savings-rows dd {
    flex-shrink: 0;
    max-width: 58%;
  }
  .savings-periods {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
  }
  .savings-view:has(> .savings-tariff) .savings-periods {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .savings-periods .savings-card {
    padding: 14px 16px;
  }
  .savings-periods h2 {
    margin-bottom: 6px;
    font-size: 14px;
  }
  .savings-periods .savings-large {
    margin-bottom: 0;
    font-size: 22px;
  }
  .savings-table th,
  .savings-table td {
    padding: 7px 8px;
  }
  .savings-dates {
    gap: 12px;
  }
  .savings-dates label {
    flex: 0 1 220px;
    gap: 6px;
  }
  .savings-range .savings-selected-dates {
    margin-bottom: 8px;
  }
  .savings-range .savings-chart-hint {
    margin-top: 0;
    margin-bottom: 8px;
  }
  .savings-chart-table {
    margin-top: 12px;
  }
}
@media (max-width: 600px) {
  .savings-view {
    gap: 16px;
  }
  .savings-card {
    padding: 20px;
  }
  .savings-rows > div {
    flex-wrap: wrap;
    gap: 4px 16px;
  }
  .savings-rows dd {
    margin-left: auto;
  }
}
</style>
