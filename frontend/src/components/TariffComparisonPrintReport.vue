<script setup lang="ts">
import { computed, useId } from "vue";
import type { Language } from "../tabs";
import {
  normalizeComparisonTime,
  type ComparisonTariffCalculation,
  type ComparisonTariffInput,
} from "../tariff-comparison";
import TariffComparisonCostChart from "./TariffComparisonCostChart.vue";

const props = defineProps<{
  language: Language;
  annualConsumption: number;
  incompleteCount?: number;
  tariffs: readonly {
    id: string;
    name: string;
    tariff: ComparisonTariffInput;
    result: Extract<ComparisonTariffCalculation, { valid: true }>;
  }[];
}>();

const text = computed(() =>
  props.language === "de"
    ? {
        title: "Tarifvergleich",
        consumption: "Jahresverbrauch",
        incomplete: "Unvollständige Tarife im Formular",
        overview: "Jahreskosten im Vergleich",
        tariff: "Tarif",
        energyCost: "Verbrauchskosten",
        annualBaseFee: "Grundgebühr pro Jahr",
        bonus: "Einmaliger Bonus",
        firstYear: "Erstes Jahr",
        laterYears: "Folgejahre",
        costTrends: "Kostenverlauf",
        details: "Tarifdetails",
        type: "Tarifart",
        fixed: "Fixpreis",
        timeOfUse: "Zeitvariabel",
        price: "Arbeitspreis",
        standardPrice: "Standardpreis",
        baseFee: "Grundgebühr",
        monthly: "€/Monat",
        yearly: "€/Jahr",
        windows: "Zeitfenster",
        start: "Beginn",
        end: "Ende",
        windowPrice: "Arbeitspreis (ct/kWh)",
        share: "Verbrauchsanteil (%)",
      }
    : {
        title: "Tariff comparison",
        consumption: "Annual consumption",
        incomplete: "Incomplete tariffs in the form",
        overview: "Annual cost comparison",
        tariff: "Tariff",
        energyCost: "Energy cost",
        annualBaseFee: "Annual standing charge",
        bonus: "One-time bonus",
        firstYear: "First year",
        laterYears: "Subsequent years",
        costTrends: "Cost trends",
        details: "Tariff details",
        type: "Tariff type",
        fixed: "Fixed price",
        timeOfUse: "Time of use",
        price: "Unit price",
        standardPrice: "Standard price",
        baseFee: "Standing charge",
        monthly: "€/month",
        yearly: "€/year",
        windows: "Time windows",
        start: "Start",
        end: "End",
        windowPrice: "Unit price (ct/kWh)",
        share: "Share of consumption (%)",
      },
);

const reportId = useId();
const locale = computed(() => (props.language === "de" ? "de-DE" : "en-GB"));
const number = computed(
  () => new Intl.NumberFormat(locale.value, { maximumFractionDigits: 12 }),
);
const euro = computed(
  () =>
    new Intl.NumberFormat(locale.value, { style: "currency", currency: "EUR" }),
);
const chartTariffs = computed(() =>
  props.tariffs.map(({ id, name, result }) => ({
    id,
    name,
    firstYearAtZero: result.firstYearAtZero,
    standardAtZero: result.standardAtZero,
    annualCostPerKwh: result.annualCostPerKwh,
    costAtConsumption: result.costAtConsumption,
  })),
);

function inputNumber(value: string): string {
  const [whole, fraction] = value.trim().split(/[.,]/);
  const separator = props.language === "de" ? "," : ".";
  return (
    number.value.format(BigInt(whole || "0")) +
    (fraction ? separator + fraction : "")
  );
}
</script>

<template>
  <main class="tariff-comparison-print-report" :lang="language">
    <header class="report-header">
      <div>
        <h1>{{ text.title }}</h1>
        <p v-if="incompleteCount" class="report-note">
          {{ text.incomplete }}: {{ number.format(incompleteCount) }}
        </p>
      </div>
      <dl class="report-consumption">
        <dt>{{ text.consumption }}</dt>
        <dd>{{ number.format(annualConsumption) }} kWh</dd>
      </dl>
    </header>

    <table class="report-overview">
      <caption>
        {{
          text.overview
        }}
      </caption>
      <thead>
        <tr>
          <th scope="col">{{ text.tariff }}</th>
          <th scope="col">{{ text.energyCost }}</th>
          <th scope="col">{{ text.annualBaseFee }}</th>
          <th scope="col">{{ text.bonus }}</th>
          <th scope="col">{{ text.firstYear }}</th>
          <th scope="col">{{ text.laterYears }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="{ id, name, result } in tariffs" :key="id">
          <th scope="row">{{ name }}</th>
          <td>{{ euro.format(result.annualEnergyCost) }}</td>
          <td>{{ euro.format(result.annualBaseFee) }}</td>
          <td>{{ euro.format(result.bonus ? -result.bonus : 0) }}</td>
          <td class="report-total">{{ euro.format(result.firstYearCost) }}</td>
          <td class="report-total">{{ euro.format(result.annualCost) }}</td>
        </tr>
      </tbody>
    </table>

    <section class="report-section" :aria-labelledby="`${reportId}-chart`">
      <h2 :id="`${reportId}-chart`">{{ text.costTrends }}</h2>
      <div class="report-chart">
        <h3>{{ text.firstYear }}</h3>
        <TariffComparisonCostChart
          report-period="first"
          :language="language"
          :annual-consumption="annualConsumption"
          :tariffs="chartTariffs"
        />
      </div>
      <div class="report-chart">
        <h3>{{ text.laterYears }}</h3>
        <TariffComparisonCostChart
          report-period="later"
          :language="language"
          :annual-consumption="annualConsumption"
          :tariffs="chartTariffs"
        />
      </div>
    </section>

    <section class="report-section" :aria-labelledby="`${reportId}-details`">
      <h2 :id="`${reportId}-details`">{{ text.details }}</h2>
      <article
        v-for="{ id, name, tariff } in tariffs"
        :key="id"
        class="report-tariff"
        :aria-labelledby="`${reportId}-${id}`"
      >
        <h3 :id="`${reportId}-${id}`">{{ name }}</h3>
        <dl class="report-fields">
          <div>
            <dt>{{ text.type }}</dt>
            <dd>{{ tariff.type === "fixed" ? text.fixed : text.timeOfUse }}</dd>
          </div>
          <div>
            <dt>
              {{ tariff.type === "fixed" ? text.price : text.standardPrice }}
            </dt>
            <dd>{{ inputNumber(tariff.price) }} ct/kWh</dd>
          </div>
          <div>
            <dt>{{ text.baseFee }}</dt>
            <dd>
              {{ inputNumber(tariff.baseFee) }}
              {{
                tariff.baseFeePeriod === "monthly" ? text.monthly : text.yearly
              }}
            </dd>
          </div>
          <div>
            <dt>{{ text.bonus }}</dt>
            <dd>{{ inputNumber(tariff.bonus) }} €</dd>
          </div>
        </dl>
        <table v-if="tariff.type === 'time-of-use'" class="report-windows">
          <caption>
            {{
              text.windows
            }}
          </caption>
          <thead>
            <tr>
              <th scope="col">{{ text.start }}</th>
              <th scope="col">{{ text.end }}</th>
              <th scope="col">{{ text.windowPrice }}</th>
              <th scope="col">{{ text.share }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="window in tariff.windows" :key="window.start">
              <td>{{ normalizeComparisonTime(window.start) }}</td>
              <td>{{ normalizeComparisonTime(window.end) }}</td>
              <td>{{ inputNumber(window.price) }}</td>
              <td>{{ inputNumber(window.share) }}</td>
            </tr>
          </tbody>
        </table>
      </article>
    </section>
  </main>
</template>
