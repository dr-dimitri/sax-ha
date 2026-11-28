<script setup lang="ts">
import { computed, nextTick, ref, useId } from "vue";
import type { Language } from "../tabs";
import TariffComparisonField from "../components/TariffComparisonField.vue";
import {
  calculateTariffComparison,
  validateAnnualConsumption,
  type ComparisonTariffError,
  type ComparisonTariffInput,
  type ComparisonTariffWindowInput,
} from "../tariff-comparison";

const props = defineProps<{ language: Language }>();

const messages = {
  de: {
    annualConsumption: "Jahresverbrauch (kWh)",
    addTariff: "Tarif hinzufügen",
    reset: "Zurücksetzen",
    tariff: "Tarif",
    name: "Tarifname",
    type: "Tarifart",
    fixed: "Fixpreis",
    timeOfUse: "Zeitvariabel",
    price: "Arbeitspreis (ct/kWh)",
    standardPrice: "Standardpreis (ct/kWh)",
    baseFee: "Grundgebühr (€)",
    baseFeePeriod: "Zeitraum der Grundgebühr",
    monthly: "Pro Monat",
    yearly: "Pro Jahr",
    bonus: "Einmaliger Bonus (€)",
    removeTariff: "Tarif entfernen",
    pricesHint:
      "Preise inklusive Steuern eingeben. Zahlen ohne Tausendertrennzeichen eingeben.",
    windowsHint:
      "Die Zeitfenster gelten täglich. Uhrzeiten im Format 22:30 oder 2230 eingeben. Die Anteile beziehen sich auf den Jahresverbrauch. Für den übrigen Verbrauch gilt der Standardpreis.",
    window: "Zeitfenster",
    addWindow: "Zeitfenster hinzufügen",
    removeWindow: "Zeitfenster entfernen",
    start: "Beginn",
    end: "Ende",
    share: "Verbrauchsanteil (%)",
    comparison: "Jahreskosten im Vergleich",
    costItem: "Kostenpunkt",
    standardShare: "Verbrauch zum Standardpreis",
    annualEnergyCost: "Verbrauchskosten pro Jahr",
    annualBaseFee: "Grundgebühr pro Jahr",
    firstYearBonus: "Bonus im ersten Jahr",
    firstYearCost: "Kosten im ersten Jahr",
    annualCost: "Kosten pro Folgejahr",
    incomplete: "Eingaben prüfen",
    noTariffs:
      "Gib den Jahresverbrauch ohne Tausendertrennzeichen ein (z. B. 3500) und füge einen Tarif hinzu.",
    errors: {
      required: "Bitte fülle dieses Feld aus.",
      invalidNumber: "Bitte gib eine gültige Zahl ein.",
      negative: "Der Wert muss mindestens 0 sein.",
      outOfRange: "Der Wert ist zu groß.",
      invalidTime: "Bitte gib eine vollständige Uhrzeit ein, z. B. 22:30.",
      sameTime: "Beginn und Ende müssen unterschiedlich sein.",
      overlap: "Dieses Zeitfenster überschneidet sich mit einem anderen.",
      notDiscounted: "Der Arbeitspreis muss unter dem Standardpreis liegen.",
      shareTooHigh: "Der Verbrauchsanteil darf höchstens 100 % betragen.",
      totalShareTooHigh:
        "Die Verbrauchsanteile aller Zeitfenster dürfen zusammen höchstens 100 % betragen.",
      missingWindow: "Füge mindestens ein vergünstigtes Zeitfenster hinzu.",
    },
  },
  en: {
    annualConsumption: "Annual consumption (kWh)",
    addTariff: "Add tariff",
    reset: "Reset",
    tariff: "Tariff",
    name: "Tariff name",
    type: "Tariff type",
    fixed: "Fixed price",
    timeOfUse: "Time of use",
    price: "Unit price (ct/kWh)",
    standardPrice: "Standard price (ct/kWh)",
    baseFee: "Standing charge (€)",
    baseFeePeriod: "Standing charge period",
    monthly: "Per month",
    yearly: "Per year",
    bonus: "One-time bonus (€)",
    removeTariff: "Remove tariff",
    pricesHint:
      "Enter prices including taxes and numbers without thousands separators.",
    windowsHint:
      "Time windows apply every day. Enter times as 22:30 or 2230. Each share is a percentage of annual consumption. Remaining consumption is billed at the standard price.",
    window: "Time window",
    addWindow: "Add time window",
    removeWindow: "Remove time window",
    start: "Start",
    end: "End",
    share: "Share of consumption (%)",
    comparison: "Annual cost comparison",
    costItem: "Cost item",
    standardShare: "Consumption at standard price",
    annualEnergyCost: "Annual energy cost",
    annualBaseFee: "Annual standing charge",
    firstYearBonus: "First-year bonus",
    firstYearCost: "First-year cost",
    annualCost: "Cost per subsequent year",
    incomplete: "Check inputs",
    noTariffs:
      "Enter annual consumption without thousands separators (e.g. 3500) and add a tariff.",
    errors: {
      required: "Fill in this field.",
      invalidNumber: "Enter a valid number.",
      negative: "The value must be at least 0.",
      outOfRange: "The value is too large.",
      invalidTime: "Enter a complete time, e.g. 22:30.",
      sameTime: "Start and end times must differ.",
      overlap: "This time window overlaps another one.",
      notDiscounted: "The unit price must be below the standard price.",
      shareTooHigh: "The share of consumption must be at most 100%.",
      totalShareTooHigh:
        "The shares of all time windows together must be at most 100%.",
      missingWindow: "Add at least one discounted time window.",
    },
  },
} as const;

type WindowDraft = ComparisonTariffWindowInput & { id: string };
type TariffDraft = ComparisonTariffInput & {
  id: string;
  name: string;
  number: number;
  windows: WindowDraft[];
};

const text = computed(() => messages[props.language]);
const locale = computed(() => (props.language === "de" ? "de-DE" : "en-GB"));
const euro = computed(
  () =>
    new Intl.NumberFormat(locale.value, { style: "currency", currency: "EUR" }),
);
const percent = computed(
  () =>
    new Intl.NumberFormat(locale.value, {
      style: "percent",
      maximumFractionDigits: 6,
    }),
);
const id = `sax-compare-${useId()}`;
const view = ref<HTMLElement>();
const addButton = ref<HTMLButtonElement>();
const annualConsumption = ref("");
const drafts = ref<TariffDraft[]>([]);
let serial = 0;
let tariffNumber = 0;

const comparisons = computed(() =>
  drafts.value.map((tariff) => ({
    tariff,
    name: tariff.name.trim() || `${text.value.tariff} ${tariff.number}`,
    result: calculateTariffComparison(annualConsumption.value, tariff),
  })),
);
const consumptionId = `${id}-consumption`;
const consumptionError = computed(() =>
  errorText(validateAnnualConsumption(annualConsumption.value)),
);
const rows = [
  "standardShare",
  "annualEnergyCost",
  "annualBaseFee",
  "firstYearBonus",
  "firstYearCost",
  "annualCost",
] as const;
const priceFields = ["price", "baseFee", "bonus"] as const;
const windowFields = ["start", "end", "price", "share"] as const;

function errorText(error?: ComparisonTariffError): string | undefined {
  return error ? text.value.errors[error] : undefined;
}

function focusField(field: string): void {
  void nextTick(() =>
    view.value?.querySelector<HTMLElement>(`#${field}`)?.focus(),
  );
}

function addTariff(): void {
  const tariffId = `${id}-tariff-${++serial}`;
  drafts.value.push({
    id: tariffId,
    name: "",
    number: ++tariffNumber,
    type: "fixed",
    price: "",
    baseFee: "",
    baseFeePeriod: "monthly",
    bonus: "",
    windows: [],
  });
  focusField(`${tariffId}-name`);
}

function addWindow(tariff: TariffDraft, focus = true): void {
  const windowId = `${id}-window-${++serial}`;
  tariff.windows.push({
    id: windowId,
    start: "",
    end: "",
    price: "",
    share: "",
  });
  if (focus) focusField(`${windowId}-start`);
}

function changeType(tariff: TariffDraft): void {
  if (tariff.type === "time-of-use" && !tariff.windows.length) {
    addWindow(tariff, false);
  }
}

function removeTariff(tariff: TariffDraft): void {
  const index = drafts.value.indexOf(tariff);
  drafts.value.splice(index, 1);
  const nearby = drafts.value[index] ?? drafts.value[index - 1];
  if (nearby) focusField(`${nearby.id}-name`);
  else addButton.value?.focus();
}

function removeWindow(tariff: TariffDraft, index: number): void {
  tariff.windows.splice(index, 1);
  focusField(`${tariff.id}-add-window`);
}

function reset(): void {
  drafts.value = [];
  tariffNumber = 0;
  addButton.value?.focus();
}
</script>

<template>
  <div ref="view" class="tariff-comparison-view">
    <div class="toolbar">
      <TariffComparisonField
        :id="consumptionId"
        v-model="annualConsumption"
        class="consumption"
        :label="text.annualConsumption"
        :error="consumptionError"
      />
      <div class="actions">
        <button
          ref="addButton"
          type="button"
          class="primary"
          @click="addTariff"
        >
          {{ text.addTariff }}
        </button>
        <button type="button" :disabled="!drafts.length" @click="reset">
          {{ text.reset }}
        </button>
      </div>
    </div>
    <p v-if="!drafts.length" class="hint">{{ text.noTariffs }}</p>
    <p v-else class="hint">{{ text.pricesHint }}</p>

    <div v-if="drafts.length" class="tariffs">
      <article
        v-for="{ tariff, name, result } in comparisons"
        :key="tariff.id"
        class="tariff"
        :aria-labelledby="`${tariff.id}-heading`"
      >
        <div class="card-header">
          <h2 :id="`${tariff.id}-heading`">{{ name }}</h2>
          <button type="button" @click="removeTariff(tariff)">
            {{ text.removeTariff }}
          </button>
        </div>
        <div class="fields">
          <div class="field">
            <label :for="`${tariff.id}-name`">{{ text.name }}</label>
            <input :id="`${tariff.id}-name`" v-model="tariff.name" />
          </div>
          <div class="field">
            <label :for="`${tariff.id}-type`">{{ text.type }}</label>
            <select
              :id="`${tariff.id}-type`"
              v-model="tariff.type"
              @change="changeType(tariff)"
            >
              <option value="fixed">{{ text.fixed }}</option>
              <option value="time-of-use">{{ text.timeOfUse }}</option>
            </select>
          </div>
          <template v-for="field in priceFields" :key="field">
            <TariffComparisonField
              :id="`${tariff.id}-${field}`"
              v-model="tariff[field]"
              :label="
                field === 'price' && tariff.type === 'time-of-use'
                  ? text.standardPrice
                  : text[field]
              "
              :error="
                result.valid ? undefined : errorText(result.errors[field])
              "
            />
            <div v-if="field === 'baseFee'" class="field">
              <label :for="`${tariff.id}-base-fee-period`">{{
                text.baseFeePeriod
              }}</label>
              <select
                :id="`${tariff.id}-base-fee-period`"
                v-model="tariff.baseFeePeriod"
              >
                <option value="monthly">{{ text.monthly }}</option>
                <option value="yearly">{{ text.yearly }}</option>
              </select>
            </div>
          </template>
        </div>

        <template v-if="tariff.type === 'time-of-use'">
          <p class="hint">{{ text.windowsHint }}</p>
          <fieldset v-for="(window, index) in tariff.windows" :key="window.id">
            <legend>{{ text.window }} {{ index + 1 }}</legend>
            <div class="fields">
              <TariffComparisonField
                v-for="field in windowFields"
                :id="`${window.id}-${field}`"
                :key="field"
                v-model="window[field]"
                :label="text[field]"
                :time="field === 'start' || field === 'end'"
                :error="
                  result.valid
                    ? undefined
                    : errorText(result.errors.windowFields[index]?.[field])
                "
              />
            </div>
            <button type="button" @click="removeWindow(tariff, index)">
              {{ text.removeWindow }}
            </button>
          </fieldset>
          <p v-if="!result.valid && result.errors.windows" class="error">
            {{ text.errors[result.errors.windows] }}
          </p>
          <button
            :id="`${tariff.id}-add-window`"
            type="button"
            @click="addWindow(tariff)"
          >
            {{ text.addWindow }}
          </button>
        </template>
      </article>
    </div>

    <div
      v-if="drafts.length"
      class="comparison"
      role="region"
      :aria-labelledby="`${id}-results`"
      tabindex="0"
    >
      <table>
        <caption :id="`${id}-results`">
          {{
            text.comparison
          }}
        </caption>
        <thead>
          <tr>
            <th scope="col">{{ text.costItem }}</th>
            <th
              v-for="{ tariff, name, result } in comparisons"
              :key="tariff.id"
              scope="col"
            >
              {{ name }}
              <small v-if="!result.valid">{{ text.incomplete }}</small>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row"
            :class="{ total: row === 'firstYearCost' || row === 'annualCost' }"
          >
            <th scope="row">{{ text[row] }}</th>
            <td v-for="{ tariff, result } in comparisons" :key="tariff.id">
              <template v-if="!result.valid">—</template>
              <template v-else-if="row === 'standardShare'">{{
                tariff.type === "fixed"
                  ? "—"
                  : percent.format(result.standardShare / 100)
              }}</template>
              <template v-else-if="row === 'firstYearBonus'">{{
                euro.format(result.bonus ? -result.bonus : 0)
              }}</template>
              <template v-else>{{ euro.format(result[row]) }}</template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.tariff-comparison-view {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.toolbar,
.actions,
.card-header {
  display: flex;
  align-items: start;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar {
  align-items: end;
  justify-content: space-between;
  gap: 12px;
}

.toolbar:has(:deep(.error)) {
  align-items: start;
}

.tariffs,
.fields {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 24rem), 1fr));
  align-items: start;
}

.fields {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.card-header {
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
}

.tariff,
fieldset {
  display: grid;
  gap: 12px;
  min-width: 0;
  margin: 0;
  padding: 12px;
  border: 1px solid var(--divider-color, #ddd);
  border-radius: 8px;
}

.tariff {
  padding: 16px;
}

.tariff button {
  justify-self: start;
}

.field {
  display: grid;
  min-width: 0;
  gap: 4px;
}

.field label,
:deep(.field label),
legend {
  font-weight: 500;
}

.consumption {
  flex: 0 1 220px;
}

input,
:deep(.field input),
select,
button {
  min-height: 44px;
  max-width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--divider-color, #aaa);
  border-radius: 6px;
  color: inherit;
  background: var(--card-background-color, #fff);
  font: inherit;
}

input,
:deep(.field input),
select {
  width: 100%;
  min-width: 0;
  border-color: var(--input-idle-line-color, var(--secondary-text-color, #666));
}

button {
  cursor: pointer;
}

button.primary {
  border-color: var(--primary-color, #03a9f4);
  background: var(--primary-color, #03a9f4);
  color: var(--text-primary-color, #fff);
  font-weight: 600;
}

button:disabled {
  cursor: default;
  opacity: 0.6;
}

.hint,
.error,
:deep(.field .error) {
  margin: 0;
  line-height: 1.5;
}

.hint,
small {
  color: var(--secondary-text-color, #666);
}

.error,
:deep(.field .error) {
  color: var(--error-color, #a23a2d);
}

:deep(.field input[aria-invalid="true"]) {
  border-color: var(--error-color, #a23a2d);
}

.comparison {
  max-width: 100%;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

caption {
  padding: 8px 0;
  text-align: start;
  font-size: 18px;
  font-weight: 500;
}

th,
td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--divider-color, #ddd);
  text-align: end;
}

th:first-child {
  min-width: 8rem;
  text-align: start;
}

thead th {
  min-width: 8rem;
}

td {
  white-space: nowrap;
}

small {
  display: block;
  font-weight: 400;
}

.total {
  background: var(--secondary-background-color, #f4f4f4);
  font-weight: 600;
}

@container sax-content (max-width: 430px) {
  .fields {
    grid-template-columns: minmax(0, 1fr);
  }

  th,
  td {
    padding-inline: 8px;
  }

  thead th {
    min-width: 5.5rem;
  }

  th:first-child {
    min-width: 8.5rem;
  }
}
</style>
