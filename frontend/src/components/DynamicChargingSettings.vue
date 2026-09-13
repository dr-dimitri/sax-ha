<script setup lang="ts">
import { computed, inject } from "vue";
import EntityControl from "./EntityControl.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import { finiteValue } from "../savings";

defineProps<{ editing: boolean }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const german = computed(() => dashboard?.language.value === "de");
const text = computed(() =>
  german.value
    ? {
        mode: "1. Wann soll der Speicher aus dem Netz laden?",
        saved: "Gespeicherte Ladeweise",
        immediate:
          "Änderungen gelten nach der Bestätigung durch Home Assistant. Die automatische Netzladung muss zusätzlich eingeschaltet sein.",
        target: "2. Wie voll soll der Speicher werden?",
        targetLabel: "Ladeziel (%)",
        targetHint:
          "Dies ist die globale Ladegrenze für alle Lademethoden, auch für PV-Ladung. Smart kann weniger Netzstrom laden, wenn die PV-Prognose den übrigen Bedarf deckt. Das Ziel ist keine Garantie: Preise, Ladezeit und andere aktive Regeln können die Ladung begrenzen.",
        hours: "Maximale Ladezeit je 24 Stunden",
        hoursHint:
          "Die günstigsten Zeitabschnitte ergeben zusammen höchstens diese Dauer. Der 24-Stunden-Zyklus beginnt beim Aktivieren dieser Ladeweise, nicht um Mitternacht. Heute/Morgen ändert nur die Preisansicht. Weniger Stunden begrenzen den Netzstrombezug, können aber ein volles Ladeziel verhindern.",
        smartHours:
          "Bedarfsgerecht nutzt nur die benötigte Zeit; diese Stundenzahl bleibt die Obergrenze. Fehlen Ladestand, Kapazität oder Ladeleistung, werden stattdessen die günstigsten Stunden bis zu dieser Obergrenze ausgewählt.",
        price: "Höchster Preis zum Laden (ct/kWh)",
        priceHint:
          "Bei einem Preis bis einschließlich dieser Grenze wird geladen, bis die globale Ladegrenze erreicht ist. Oberhalb findet keine preisgesteuerte Netzladung statt. Auch negative Preise sind möglich.",
        noPriceLimit:
          "Es gilt keine feste Preisgrenze: Auch die günstigsten verfügbaren Stunden können teuer sein. Diese Ladeweise benötigt eine Preisvorschau mit Zeitabschnitten; ein einzelner aktueller Preis reicht nicht.",
        pvMissing:
          "Ohne PV-Prognose wird keine künftige PV-Energie abgezogen. Eine Prognose kannst du unter Tarif & Preise ergänzen.",
        pvUsed:
          "Die gespeicherte PV-Prognose wird berücksichtigt, soweit sie verfügbar ist. Sie kann den benötigten Netzstrom reduzieren. Den angerechneten Anteil findest du unter Tarif & Preise.",
        offHint:
          "Diese Ladeweise setzt die preisgesteuerte Automatik aus, auch wenn der Hauptschalter eingeschaltet ist. Preise und Einstellungen bleiben erhalten.",
        advanced: "Weitere Einstellungen · Speicher schonen",
        neutral: "Speicher bei günstigem Strom schonen bis (ct/kWh)",
        neutralHint:
          "Wenn kein Ladeslot aktiv ist, pausiert der Speicher unterhalb dieses Preises: Er lädt und entlädt nicht; das Haus nutzt Netzstrom. So bleibt gespeicherte Energie für teurere Zeiten erhalten. Ab diesem Preis wird der normale Speicherbetrieb wieder freigegeben.",
        absoluteNeutral:
          "Bei der festen Preisgrenze wirkt diese Pause nur oberhalb der Ladepreisgrenze. Liegt dieser Wert gleich hoch oder niedriger, gibt es keine solche Pause.",
        neutralSummary:
          "Außerhalb der Ladezeiten: Speicher schonen und Haus aus dem Netz versorgen unter",
        neutralBand: "und oberhalb der Ladepreisgrenze",
        neutralInactive:
          "Speicher schonen ist ohne Wirkung: Die Grenze liegt nicht über dem höchsten Ladepreis.",
        neutralUnavailable:
          "Die Grenze zum Schonen des Speichers ist nicht verfügbar.",
        disabled:
          "Automatische Netzladung ist ausgeschaltet. Die gespeicherte Ladeweise greift erst nach dem Einschalten.",
        unavailable:
          "Ladeweise nicht verfügbar. Es wird keine Auswahl angenommen.",
        readonly: "Keine Berechtigung zum Ändern der Ladeweise.",
        disconnected: "Keine Verbindung zu Home Assistant.",
        pending: "Ladeweise wird übernommen …",
        targetSummary: "Ladegrenze",
        modes: {
          smart: {
            title: "Bedarfsgerecht laden",
            hint: "Kauft die noch benötigte Energie in günstigen Stunden. Eine PV-Prognose kann den Netzstrombedarf verringern.",
          },
          relative: {
            title: "Günstigste Stunden nutzen",
            hint: "Lädt in den günstigsten Zeitabschnitten bis zur eingestellten Stundenzahl oder Ladegrenze.",
          },
          absolute: {
            title: "Bis zu einem festen Preis laden",
            hint: "Du legst fest, was eine Kilowattstunde höchstens kosten darf. Nur bis zu diesem Preis wird geladen.",
          },
          off: {
            title: "Keine automatische Ladung",
            hint: "Setzt die preisgesteuerte Ladung aus. Die übrigen Einstellungen bleiben gespeichert.",
          },
        },
      }
    : {
        mode: "1. When should the battery charge from the grid?",
        saved: "Saved charging method",
        immediate:
          "Changes apply once confirmed by Home Assistant. Automatic grid charging must also be switched on.",
        target: "2. How full should the battery be?",
        targetLabel: "Charge target (%)",
        targetHint:
          "This is the global charge limit for every charging method, including solar charging. Smart charging may use less grid energy when forecast solar production covers the remaining need. Reaching the target is not guaranteed: prices, charging time and other active rules may limit charging.",
        hours: "Maximum charging time per 24 hours",
        hoursHint:
          "The cheapest time slots add up to at most this duration. The 24-hour cycle starts when you activate this charging method, not at midnight. Today/Tomorrow only changes the price chart. Fewer hours limit grid energy use but may prevent reaching the charge target.",
        smartHours:
          "Charging what is needed uses only the required time; these hours remain the upper limit. If battery level, capacity or charging power is missing, the cheapest hours up to this limit are selected instead.",
        price: "Maximum price for charging (ct/kWh)",
        priceHint:
          "Charging is allowed at or below this price until the global charge limit is reached. Above it, price-controlled grid charging stops. Negative prices are supported.",
        noPriceLimit:
          "There is no fixed price cap: even the cheapest available hours may be expensive. This method requires a price forecast with time slots; a single current price is not enough.",
        pvMissing:
          "Without a solar forecast, no future solar energy is deducted. You can add a forecast under Tariff & prices.",
        pvUsed:
          "The saved solar forecast is used when available. It may reduce the grid energy needed. Its contribution is configured under Tariff & prices.",
        offHint:
          "This method pauses price-controlled automation even when the main switch is on. Prices and settings are preserved.",
        advanced: "More settings · Preserve battery energy",
        neutral: "Preserve battery energy below (ct/kWh)",
        neutralHint:
          "When no charging slot is active, the battery pauses below this price: it neither charges nor discharges, and the house uses grid energy. This keeps stored energy for more expensive times. Normal battery operation resumes at this price or above.",
        absoluteNeutral:
          "With a fixed charging price, this pause applies only above that charging price. If this value is equal or lower, no such pause occurs.",
        neutralSummary:
          "Outside charging slots: preserve battery energy and supply the house from the grid below",
        neutralBand: "and above the charging price cap",
        neutralInactive:
          "Preserving battery energy has no effect: the threshold is not above the maximum charging price.",
        neutralUnavailable:
          "The threshold for preserving battery energy is unavailable.",
        disabled:
          "Automatic grid charging is off. The saved method takes effect after switching it on.",
        unavailable: "Charging method unavailable. No selection is assumed.",
        readonly: "You do not have permission to change the charging method.",
        disconnected: "Disconnected from Home Assistant.",
        pending: "Applying charging method …",
        targetSummary: "Charge limit",
        modes: {
          smart: {
            title: "Charge what is needed",
            hint: "Buys the remaining energy needed during cheap hours. A solar forecast can reduce grid energy needs.",
          },
          relative: {
            title: "Use the cheapest hours",
            hint: "Charges during the cheapest time slots up to the selected hours or charge limit.",
          },
          absolute: {
            title: "Charge below a fixed price",
            hint: "You set the highest price you want to pay per kilowatt-hour. Charging only runs at or below it.",
          },
          off: {
            title: "No automatic charging",
            hint: "Pauses price-controlled charging. All other settings are preserved.",
          },
        },
      },
);
const strategy = computed(() =>
  dashboard?.entity("select", "price_charge_strategy"),
);
type Strategy = "smart" | "relative" | "absolute" | "off";
const methods: Strategy[] = ["smart", "relative", "absolute", "off"];
const selected = computed(() => {
  const value = strategy.value?.state?.state;
  return strategy.value?.available && methods.includes(value as Strategy)
    ? (value as Strategy)
    : null;
});
const options = computed(() => strategy.value?.state?.attributes.options);
const blocked = computed(
  () => !strategy.value?.canControl || strategy.value.pending,
);
const status = computed(() => {
  if (!dashboard?.connected.value) return text.value.disconnected;
  if (!strategy.value?.available) return text.value.unavailable;
  if (!strategy.value.metadata.can_control) return text.value.readonly;
  return strategy.value.pending ? text.value.pending : "";
});
const hasForecast = computed(
  () => !!dashboard?.tariff.value?.profiles?.dynamic.pv_sensor,
);
const summary = computed(() => {
  if (!selected.value) return text.value.unavailable;
  const method = text.value.modes[selected.value].title;
  if (selected.value === "off") return method;
  const limit = dashboard?.entity("number", "max_soc")?.displayValue ?? "—";
  const value =
    dashboard?.entity(
      "number",
      selected.value === "absolute"
        ? "price_charge_max_price"
        : "price_charge_hours",
    )?.displayValue ?? "—";
  return `${method} · ${value} · ${text.value.targetSummary} ${limit}`;
});
const neutralSummary = computed(() => {
  const neutral = dashboard?.entity("number", "price_charge_neutral_price");
  const cap = dashboard?.entity("number", "price_charge_max_price");
  const neutralValue = finiteValue(neutral?.state?.state);
  const capValue = finiteValue(cap?.state?.state);
  if (
    !neutral?.available ||
    neutralValue === null ||
    (selected.value === "absolute" && (!cap?.available || capValue === null))
  )
    return text.value.neutralUnavailable;
  if (
    selected.value === "absolute" &&
    capValue !== null &&
    neutralValue <= capValue
  )
    return text.value.neutralInactive;
  return `${text.value.neutralSummary} ${neutral.displayValue}${selected.value === "absolute" ? ` ${text.value.neutralBand}` : ""}.`;
});
async function choose(method: Strategy) {
  if (
    blocked.value ||
    !Array.isArray(options.value) ||
    !options.value.includes(method) ||
    selected.value === method
  )
    return;
  await dashboard?.perform("select", "price_charge_strategy", method);
}
</script>

<template>
  <div class="dynamic-charging-settings">
    <p class="dynamic-charging-summary">
      <span>{{ text.saved }}:</span> {{ summary }}
    </p>
    <p
      v-if="selected && selected !== 'off'"
      class="electricity-muted dynamic-charging-neutral-summary"
    >
      {{ neutralSummary }}
    </p>
    <p
      v-if="dashboard?.tariff.value?.automation_enabled === false"
      class="electricity-muted"
    >
      {{ text.disabled }}
    </p>
    <p v-if="strategy?.error" class="electricity-error" role="alert">
      {{ strategy.error }}
    </p>
    <p v-else-if="status" role="status" aria-live="polite">{{ status }}</p>
    <div v-if="editing">
      <h3>{{ text.mode }}</h3>
      <p class="electricity-muted">{{ text.immediate }}</p>
      <div
        class="dynamic-charging-methods"
        role="group"
        :aria-label="text.mode"
        :aria-busy="strategy?.pending ?? false"
      >
        <button
          v-for="method in methods"
          :key="method"
          type="button"
          :data-strategy="method"
          :aria-pressed="selected === method"
          :disabled="
            blocked || !Array.isArray(options) || !options.includes(method)
          "
          @click="choose(method)"
        >
          <strong>{{ text.modes[method].title }}</strong>
          <span>{{ text.modes[method].hint }}</span>
        </button>
      </div>
      <p v-if="selected === 'off'" class="electricity-muted">
        {{ text.offHint }}
      </p>
      <template v-if="selected && selected !== 'off'">
        <h3>{{ text.target }}</h3>
        <EntityControl
          domain="number"
          entity-key="max_soc"
          :label="text.targetLabel"
          hide-confirmed-label
        />
        <p class="electricity-muted">{{ text.targetHint }}</p>
        <template v-if="selected === 'absolute'">
          <EntityControl
            domain="number"
            entity-key="price_charge_max_price"
            :label="text.price"
            hide-confirmed-label
          />
          <p class="electricity-muted">{{ text.priceHint }}</p>
        </template>
        <template v-else>
          <EntityControl
            domain="number"
            entity-key="price_charge_hours"
            :label="text.hours"
            hide-confirmed-label
          />
          <p class="electricity-muted">{{ text.hoursHint }}</p>
          <p class="dynamic-charging-notice">{{ text.noPriceLimit }}</p>
          <template v-if="selected === 'smart'">
            <p class="electricity-muted">{{ text.smartHours }}</p>
            <p class="electricity-muted">
              {{ hasForecast ? text.pvUsed : text.pvMissing }}
            </p>
          </template>
        </template>
        <details class="dynamic-charging-advanced">
          <summary>{{ text.advanced }}</summary>
          <EntityControl
            domain="number"
            entity-key="price_charge_neutral_price"
            :label="text.neutral"
            hide-confirmed-label
          />
          <p class="electricity-muted">{{ text.neutralHint }}</p>
          <p v-if="selected === 'absolute'" class="electricity-muted">
            {{ text.absoluteNeutral }}
          </p>
        </details>
      </template>
    </div>
  </div>
</template>

<style>
.dynamic-charging-summary span {
  font-weight: 600;
}
.dynamic-charging-methods {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}
.dynamic-charging-methods button {
  text-align: left;
  padding: 16px;
  color: var(--primary-text-color, #212121);
}
.dynamic-charging-methods button[aria-pressed="true"] {
  border: 2px solid var(--primary-color, #03a9f4);
  background: var(--secondary-background-color, #f5f5f5);
  padding: 15px;
}
.dynamic-charging-methods strong,
.dynamic-charging-methods span {
  display: block;
  line-height: 1.5;
}
.dynamic-charging-methods span {
  color: var(--secondary-text-color, #666);
  margin-top: 6px;
  font-size: 14px;
}
.dynamic-charging-advanced {
  border-top: 1px solid var(--divider-color, #ddd);
  padding-top: 12px;
  margin-top: 20px;
}
.dynamic-charging-advanced summary {
  cursor: pointer;
  min-height: 44px;
  align-content: center;
}
.dynamic-charging-notice {
  border-left: 3px solid var(--primary-color, #03a9f4);
  padding-left: 12px;
}
@media (max-width: 700px) {
  .dynamic-charging-methods {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
