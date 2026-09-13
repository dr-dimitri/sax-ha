<script setup lang="ts">
import { computed, inject, nextTick, onBeforeUnmount, ref, watch } from "vue";
import EntityControl from "../components/EntityControl.vue";
import EntityValue from "../components/EntityValue.vue";
import MonthSelection from "../components/MonthSelection.vue";
import ChargePlan from "../components/ChargePlan.vue";
import TariffPlan from "../components/TariffPlan.vue";
import TariffPriceChart from "../components/TariffPriceChart.vue";
import SensorPicker from "../components/SensorPicker.vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import { formatSavingsDate, formatSavingsNumber } from "../savings";
import type {
  DynamicTariffProfile,
  HomeAssistant,
  TariffPriceSeries,
  TariffProfile,
} from "../types";
const props = defineProps<{ hass?: HomeAssistant }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const german = computed(() => dashboard?.language.value === "de");
const text = computed(() =>
  german.value
    ? {
        active: "Aktiver Tarif",
        tou: "Zeitvariabel",
        dynamic: "Dynamisch",
        unset: "Noch nicht eingerichtet",
        change: "Tarif wechseln",
        apply: "Tarif übernehmen",
        cancel: "Abbrechen",
        save: "Speichern",
        done: "Fertig",
        edit: "Bearbeiten",
        loading: "Wird geladen …",
        automatic: "Automatische Netzladung",
        off: "Automatische Netzladung aus",
        on: "Automatische Netzladung ein",
        offHint: "Der aktive Tarif bleibt für Preise und Auswertung erhalten.",
        chooseHint:
          "Nur der gewählte Tarif ist aktiv. Gespeicherte Einstellungen bleiben beim Wechsel erhalten.",
        incomplete:
          "Dieser Tarif ist noch nicht eingerichtet. Nach dem Wechsel bleibt die automatische Netzladung aus. Richte danach Tarif & Preise ein.",
        touHint: "Feste Preise zu wiederkehrenden Uhrzeiten",
        dynamicHint: "Preise aus einem Strompreis-Sensor",
        price: "Strompreis",
        current: "Aktuell",
        today: "Heute",
        tomorrow: "Morgen",
        prices: "Tarif & Preise",
        feed: "Einspeisevergütung",
        source: "Strompreis-Sensor",
        attribute: "Preisattribut (optional)",
        unit: "Einheit der Preisquelle",
        autoUnit: "Automatisch erkennen",
        pv: "PV-Prognose-Sensor (optional)",
        pvFactor: "Anrechenbarer PV-Anteil (%)",
        charging: "Ladeverhalten",
        details: "Ladeplan & Prognose",
        global: "Globale SOC-Obergrenze",
        globalHint:
          "Gilt für alle Lademethoden. Das zeitvariable Ladeziel kann zusätzlich niedriger sein.",
        target: "Zeitvariables Ladeziel",
        minimum: "Startschwelle der Netzladung",
        minimumHint: "Ladung beginnt nur unter diesem SOC.",
        bridge: "Verbrauchsbasiert bis zum PV-Start laden",
        months: "Aktive Monate",
        budget:
          "Smart nutzt das Stundenbudget als Obergrenze. Der 24-h-Planungszyklus ist unabhängig von der Tagesansicht.",
        neutral: "Der Neutralpreis steuert den Netzbezug ohne Laden.",
        priceHint:
          "Alle Preise brutto in ct/kWh. Die Quelleneinheit wird nur zur Umrechnung verwendet.",
        readonly: "Keine Berechtigung zum Ändern des Tarifs.",
        disconnected:
          "Keine Verbindung zu Home Assistant. Dein Entwurf bleibt erhalten.",
        failed: "Die Änderung ist fehlgeschlagen. Bitte erneut versuchen.",
        conflict:
          "Der Tarif wurde inzwischen geändert. Dein Entwurf bleibt erhalten. Lade die gespeicherten Einstellungen erneut.",
        reload: "Gespeicherte Einstellungen laden (Entwurf verwerfen)",
        invalid:
          "Bitte Preisquelle und Preise prüfen: Einspeisung 0 bis 200 ct/kWh, PV-Anteil 0 bis 100 %.",
        saved: "Einstellungen gespeichert.",
        tariffChanged:
          "Der aktive Tarif wurde an anderer Stelle gewechselt. Der bisherige Preisentwurf wurde geschlossen.",
        unavailable: "Nicht verfügbar",
        sourceHint:
          "Die Preisquelle muss die Preise inklusive der gewünschten Steuern und Zuschläge liefern.",
        fixed: "Festes Ladeziel",
        pvMode: "Bis PV-Start",
        units: {
          auto: "Automatisch erkennen",
          eur_kwh: "EUR/kWh",
          ct_kwh: "ct/kWh",
          eur_mwh: "EUR/MWh",
          ct_mwh: "ct/MWh",
        },
      }
    : {
        active: "Active tariff",
        tou: "Time of use",
        dynamic: "Dynamic",
        unset: "Not configured",
        change: "Change tariff",
        apply: "Apply tariff",
        cancel: "Cancel",
        save: "Save",
        done: "Done",
        edit: "Edit",
        loading: "Loading …",
        automatic: "Automatic grid charging",
        off: "Automatic grid charging off",
        on: "Automatic grid charging on",
        offHint:
          "The active tariff remains available for prices and accounting.",
        chooseHint:
          "Only the selected tariff is active. Saved settings are preserved when switching.",
        incomplete:
          "This tariff is not configured yet. Automatic grid charging will be off after switching. Set up Tariff & prices next.",
        touHint: "Fixed prices at recurring times",
        dynamicHint: "Prices from an electricity price sensor",
        price: "Electricity price",
        current: "Current",
        today: "Today",
        tomorrow: "Tomorrow",
        prices: "Tariff & prices",
        feed: "Feed-in remuneration",
        source: "Electricity price sensor",
        attribute: "Price attribute (optional)",
        unit: "Price source unit",
        autoUnit: "Detect automatically",
        pv: "PV forecast sensor (optional)",
        pvFactor: "PV share to account for (%)",
        charging: "Charging settings",
        details: "Charging plan & forecast",
        global: "Global SOC limit",
        globalHint:
          "Applies to every charging method. The time-of-use charge target can additionally be lower.",
        target: "Time-of-use charge target",
        minimum: "Grid charging start threshold",
        minimumHint: "Charging starts only below this SOC.",
        bridge: "Charge based on consumption until PV starts",
        months: "Active months",
        budget:
          "Smart uses the hours budget as an upper limit. The 24-hour planning cycle is independent of the selected day.",
        neutral: "The neutral price controls grid import without charging.",
        priceHint:
          "All prices include tax and use ct/kWh. The source unit is used for conversion only.",
        readonly: "You do not have permission to change the tariff.",
        disconnected:
          "Disconnected from Home Assistant. Your draft is preserved.",
        failed: "The change failed. Please try again.",
        conflict:
          "The tariff has changed elsewhere. Your draft is preserved. Reload the saved settings.",
        reload: "Load saved settings (discard draft)",
        invalid:
          "Check the price source and values: feed-in price 0 to 200 ct/kWh, PV share 0 to 100%.",
        saved: "Settings saved.",
        tariffChanged:
          "The active tariff was changed elsewhere. The previous price draft was closed.",
        unavailable: "Unavailable",
        sourceHint:
          "The price source must include the taxes and fees you want to account for.",
        fixed: "Fixed charge target",
        pvMode: "Until PV starts",
        units: {
          auto: "Detect automatically",
          eur_kwh: "EUR/kWh",
          ct_kwh: "ct/kWh",
          eur_mwh: "EUR/MWh",
          ct_mwh: "ct/MWh",
        },
      },
);
const lastProfile = ref<TariffProfile | null>(null);
watch(
  () => dashboard?.tariff.value,
  (value) => {
    if (value) lastProfile.value = value;
  },
  { immediate: true },
);
const profile = computed(() => dashboard?.tariff.value ?? lastProfile.value);
const active = computed(() => profile.value?.tariff_type);
const known = computed(
  () => active.value === "time_of_use" || active.value === "dynamic",
);
const connected = computed(
  () => dashboard?.connected.value === true && dashboard.ready.value,
);
const canConfigure = computed(
  () => profile.value?.can_configure === true && connected.value,
);
const activeName = computed(() =>
  active.value === "dynamic"
    ? text.value.dynamic
    : active.value === "time_of_use"
      ? text.value.tou
      : text.value.unset,
);
const masterEntity = computed(() =>
  dashboard?.entity(
    "switch",
    active.value === "dynamic"
      ? "price_charge_enabled"
      : "timed_charge_enabled",
  ),
);
const automatic = computed(() =>
  typeof profile.value?.automation_enabled === "boolean"
    ? profile.value.automation_enabled
    : masterEntity.value?.available
      ? masterEntity.value.state?.state === "on"
      : null,
);
const bridge = computed(
  () =>
    dashboard?.entity("switch", "bridge_charge_enabled")?.state?.state === "on",
);
const strategy = computed(() =>
  dashboard?.entity("select", "price_charge_strategy"),
);
const series = ref<TariffPriceSeries | null>(null);
const seriesLoading = ref(false);
const day = ref<"today" | "tomorrow">("today");
const error = ref<string | null>(null);
const conflict = ref(false);
const pending = ref(false);
const changed = ref(false);
const externalTariffChange = ref(false);
const changing = ref(false);
const selected = ref<"time_of_use" | "dynamic">("time_of_use");
const selectionRevision = ref("");
const priceEditing = ref(false);
const touEditing = ref(false);
const chargingOpen = ref(false);
const draft = ref<DynamicTariffProfile>({
  feed_in_price_ct_kwh: null,
  price_sensor: null,
  price_attribute: null,
  price_unit: "auto",
  pv_sensor: null,
  pv_factor: 100,
});
const feed = ref("");
const pvFactor = ref("");
const editRevision = ref("");
const pricesEditor = ref<HTMLElement>();
const priceButton = ref<HTMLButtonElement>();
const chargingButton = ref<HTMLButtonElement>();
let disposed = false;
let seriesRequest = 0;
onBeforeUnmount(() => {
  disposed = true;
  seriesRequest++;
  window.clearInterval(refreshTimer);
});
const editorOpen = computed(
  () => priceEditing.value || touEditing.value || chargingOpen.value,
);
const currentPrice = computed(() =>
  formatSavingsNumber(
    connected.value ? series.value?.current_price_ct_kwh : null,
    props.hass,
    2,
  ),
);
const date = computed(() =>
  series.value
    ? formatSavingsDate(`${series.value.date}T12:00:00Z`, props.hass, {
        dateStyle: "medium",
        timeZone: "UTC",
      })
    : null,
);
const sourceState = computed(() => {
  const sensor =
    active.value === "dynamic"
      ? profile.value?.profiles?.dynamic.price_sensor
      : dashboard?.entity("sensor", "economics_current_import_price")?.metadata
          .entity_id;
  return sensor ? props.hass?.states[sensor] : undefined;
});
const months = Array.from(
  { length: 12 },
  (_, index) => `timed_charge_month_${index + 1}`,
);
const monthCount = computed(
  () =>
    months.filter(
      (key) => dashboard?.entity("switch", key)?.state?.state === "on",
    ).length,
);
const chargingSummary = computed(() =>
  active.value === "dynamic"
    ? `${strategy.value?.displayValue ?? text.value.unavailable} · ${text.value.global} ${dashboard?.entity("number", "max_soc")?.displayValue ?? "—"}`
    : `${bridge.value ? text.value.pvMode : `${text.value.target} ${dashboard?.entity("number", "timed_charge_max_soc")?.displayValue ?? "—"}`} · ${monthCount.value} ${text.value.months.toLowerCase()}`,
);
const dynamicSummary = computed(() => {
  const source = profile.value?.profiles?.dynamic.price_sensor;
  const name = source
    ? (props.hass?.states[source]?.attributes.friendly_name ?? source)
    : text.value.unset;
  return `${name} · ${text.value.feed} ${formatSavingsNumber(profile.value?.profiles?.dynamic.feed_in_price_ct_kwh, props.hass, 2) ?? "—"} ct/kWh`;
});
function showError(cause: unknown) {
  if (disposed) return;
  const code =
    cause && typeof cause === "object" && "code" in cause
      ? String(cause.code)
      : "failed";
  conflict.value = code === "conflict";
  error.value =
    code === "conflict"
      ? text.value.conflict
      : code === "forbidden"
        ? text.value.readonly
        : code === "disconnected"
          ? text.value.disconnected
          : code === "invalid_tariff" || code === "invalid_format"
            ? text.value.invalid
            : text.value.failed;
}
async function loadSeries() {
  const request = ++seriesRequest;
  if (!dashboard || !connected.value || !known.value) {
    series.value = null;
    seriesLoading.value = false;
    return;
  }
  const requestedTariff = active.value;
  const requestedRevision = profile.value?.revision;
  const requestedDay = day.value;
  seriesLoading.value = true;
  try {
    const result = await dashboard.loadTariffSeries(requestedDay);
    if (
      !disposed &&
      request === seriesRequest &&
      active.value === requestedTariff &&
      profile.value?.revision === requestedRevision &&
      day.value === requestedDay
    )
      series.value =
        result.tariff_type === requestedTariff &&
        result.revision === requestedRevision &&
        result.day === requestedDay
          ? result
          : null;
  } catch {
    if (!disposed && request === seriesRequest) series.value = null;
  } finally {
    if (!disposed && request === seriesRequest) seriesLoading.value = false;
  }
}
watch(
  [connected, active, () => profile.value?.revision, day, sourceState],
  () => {
    void loadSeries();
  },
  { immediate: true },
);
watch(active, (value, previous) => {
  if (previous && value !== previous && editorOpen.value) {
    priceEditing.value = false;
    touEditing.value = false;
    chargingOpen.value = false;
    error.value = null;
    conflict.value = false;
    externalTariffChange.value = true;
  }
  day.value = "today";
  series.value = null;
});
watch(
  connected,
  (value) => {
    if (value) void dashboard?.loadTariff().catch(showError);
  },
  { immediate: true },
);
// REQ-VUE-ELECTRICITY-TARIFF: constant sources still cross tariff and day boundaries.
const refreshTimer = window.setInterval(() => {
  if (!connected.value) return;
  void loadSeries();
  if (!pending.value) void dashboard?.loadTariff().catch(() => {});
}, 60_000);
const incompleteSelection = computed(() => {
  const candidate = profile.value?.profiles?.[selected.value];
  if (!candidate || candidate.feed_in_price_ct_kwh === null) return true;
  return "price_sensor" in candidate
    ? !candidate.price_sensor
    : candidate.base_price_ct_kwh === null;
});
function beginChoice() {
  externalTariffChange.value = false;
  selected.value = active.value === "dynamic" ? "dynamic" : "time_of_use";
  selectionRevision.value = profile.value?.revision ?? "";
  changing.value = true;
  error.value = null;
  changed.value = false;
}
async function applyChoice() {
  if (!dashboard || !canConfigure.value || pending.value) return;
  pending.value = true;
  error.value = null;
  try {
    await dashboard.configureTariff({
      revision: selectionRevision.value,
      tariff_type: selected.value,
      ...(incompleteSelection.value ? { automation_enabled: false } : {}),
    });
    if (!disposed) {
      changing.value = false;
      changed.value = true;
    }
  } catch (cause) {
    showError(cause);
  } finally {
    pending.value = false;
  }
}
async function toggle(event: Event) {
  const input = event.target as HTMLInputElement;
  const enabled = input.checked;
  input.checked = automatic.value === true;
  if (!dashboard || !canConfigure.value || !known.value || pending.value)
    return;
  pending.value = true;
  error.value = null;
  try {
    await dashboard.configureTariff({
      revision: profile.value!.revision,
      tariff_type: active.value as "time_of_use" | "dynamic",
      automation_enabled: enabled,
    });
  } catch (cause) {
    showError(cause);
  } finally {
    pending.value = false;
  }
}
async function openPrices() {
  externalTariffChange.value = false;
  if (!dashboard || pending.value) return;
  pending.value = true;
  error.value = null;
  changed.value = false;
  try {
    const latest = await dashboard.loadTariff();
    if (disposed) return;
    if (
      !latest.can_configure ||
      latest.tariff_type !== "dynamic" ||
      !latest.profiles
    )
      throw { code: "forbidden" };
    draft.value = { ...latest.profiles.dynamic };
    feed.value =
      draft.value.feed_in_price_ct_kwh === null
        ? ""
        : String(draft.value.feed_in_price_ct_kwh).replace(
            ".",
            german.value ? "," : ".",
          );
    pvFactor.value = String(draft.value.pv_factor);
    editRevision.value = latest.revision;
    priceEditing.value = true;
    conflict.value = false;
  } catch (cause) {
    showError(cause);
  } finally {
    pending.value = false;
    await nextTick();
    pricesEditor.value?.querySelector<HTMLElement>("select,input")?.focus();
  }
}
function closePrices() {
  priceEditing.value = false;
  error.value = null;
  conflict.value = false;
  void nextTick(() => priceButton.value?.focus());
}
async function savePrices() {
  if (!dashboard || pending.value || conflict.value) return;
  const price = /^\d+(?:[.,]\d{1,2})?$/.test(feed.value.trim())
    ? Number(feed.value.trim().replace(",", "."))
    : NaN;
  const factor = Number(pvFactor.value);
  if (
    !draft.value.price_sensor ||
    !Number.isFinite(price) ||
    price < 0 ||
    price > 200 ||
    pvFactor.value.trim() === "" ||
    !Number.isFinite(factor) ||
    factor < 0 ||
    factor > 100
  ) {
    error.value = text.value.invalid;
    return;
  }
  pending.value = true;
  error.value = null;
  try {
    await dashboard.configureTariff({
      revision: editRevision.value,
      tariff_type: "dynamic",
      profile: {
        ...draft.value,
        price_attribute: draft.value.price_attribute?.trim() || null,
        feed_in_price_ct_kwh: price,
        pv_factor: factor,
      },
    });
    if (!disposed) {
      closePrices();
      changed.value = true;
    }
  } catch (cause) {
    showError(cause);
  } finally {
    pending.value = false;
  }
}
async function reload() {
  if (!dashboard || pending.value) return;
  pending.value = true;
  try {
    await dashboard.loadTariff();
    if (!disposed) {
      priceEditing.value = false;
      changing.value = false;
      error.value = null;
      conflict.value = false;
    }
  } catch (cause) {
    showError(cause);
  } finally {
    pending.value = false;
  }
}
function closeCharging() {
  chargingOpen.value = false;
  void nextTick(() => chargingButton.value?.focus());
}
</script>
<template>
  <div class="electricity-tariff-view">
    <section class="electricity-card electricity-tariff-bar">
      <div class="electricity-tariff-bar__row">
        <div class="electricity-active">
          <span>{{ text.active }}</span
          ><strong>{{ activeName }}</strong
          ><button
            type="button"
            :disabled="!canConfigure || pending || editorOpen"
            :aria-expanded="changing"
            @click="beginChoice"
          >
            {{ text.change }}
          </button>
        </div>
        <label v-if="known" class="electricity-master"
          ><input
            type="checkbox"
            role="switch"
            :checked="automatic === true"
            :disabled="
              !canConfigure ||
              pending ||
              automatic === null ||
              changing ||
              editorOpen
            "
            @change="toggle"
          />{{ text.automatic }}</label
        >
      </div>
      <form
        v-if="changing"
        class="electricity-choice"
        @submit.prevent="applyChoice"
      >
        <fieldset :disabled="pending || !connected">
          <legend class="electricity-sr-only">{{ text.active }}</legend>
          <label v-for="type in ['time_of_use', 'dynamic'] as const" :key="type"
            ><input
              v-model="selected"
              type="radio"
              name="electricity-tariff"
              :value="type"
            /><span
              ><strong>{{
                type === "time_of_use" ? text.tou : text.dynamic
              }}</strong
              ><small>{{
                type === "time_of_use" ? text.touHint : text.dynamicHint
              }}</small></span
            ></label
          >
        </fieldset>
        <p>{{ text.chooseHint }}</p>
        <p v-if="incompleteSelection" role="status">{{ text.incomplete }}</p>
        <div class="electricity-actions">
          <button type="submit" :disabled="pending || !connected || conflict">
            {{ text.apply }}</button
          ><button
            type="button"
            :disabled="pending"
            @click="
              changing = false;
              error = null;
            "
          >
            {{ text.cancel }}
          </button>
        </div>
      </form>
      <p v-if="error" role="alert" class="electricity-error">{{ error }}</p>
      <button
        v-if="conflict"
        type="button"
        :disabled="pending || !connected"
        @click="reload"
      >
        {{ text.reload }}
      </button>
      <p v-if="changed" role="status">{{ text.saved }}</p>
      <p v-if="externalTariffChange" role="status">{{ text.tariffChanged }}</p>
      <p v-if="!profile && !error" role="status">{{ text.loading }}</p>
    </section>
    <section class="electricity-card electricity-price-card">
      <div class="electricity-price-card__heading">
        <div>
          <h2>{{ text.price }}</h2>
          <p class="electricity-current-price">
            {{ currentPrice ?? text.unavailable
            }}<span v-if="currentPrice !== null"> ct/kWh</span>
          </p>
          <p class="electricity-muted">{{ text.current }} · {{ activeName }}</p>
        </div>
        <div
          v-if="active === 'dynamic'"
          class="electricity-days"
          :aria-label="text.price"
        >
          <button
            v-for="value in ['today', 'tomorrow'] as const"
            :key="value"
            type="button"
            :aria-pressed="day === value"
            @click="day = value"
          >
            {{ value === "today" ? text.today : text.tomorrow }}
          </button>
        </div>
      </div>
      <p class="electricity-day">
        {{ day === "today" ? text.today : text.tomorrow
        }}<span v-if="date"> · {{ date }}</span>
      </p>
      <TariffPriceChart
        :series="series"
        :hass="hass"
        :loading="seriesLoading"
      />
      <div class="electricity-charge-status">
        <strong>{{
          automatic === null ? text.unavailable : automatic ? text.on : text.off
        }}</strong>
        <p v-if="automatic === false">{{ text.offHint }}</p>
        <EntityValue
          v-if="active === 'dynamic'"
          domain="sensor"
          entity-key="price_charge_status_text"
        /><EntityValue
          v-else
          domain="sensor"
          entity-key="timed_charge_discharge_status"
        />
      </div>
    </section>
    <TariffPlan
      v-if="active === 'time_of_use'"
      :hass="hass"
      compact
      @editing="touEditing = $event"
      @saved="loadSeries"
    />
    <section
      v-else-if="active === 'dynamic'"
      class="electricity-card electricity-prices"
    >
      <header>
        <div>
          <h2>{{ text.prices }}</h2>
          <p class="electricity-muted">{{ dynamicSummary }}</p>
        </div>
        <button
          v-if="!priceEditing"
          ref="priceButton"
          type="button"
          :disabled="pending || !canConfigure || changing"
          :aria-expanded="priceEditing"
          @click="openPrices"
        >
          {{ text.edit }}
        </button>
      </header>
      <form
        v-if="priceEditing"
        ref="pricesEditor"
        class="electricity-price-editor"
        novalidate
        @submit.prevent="savePrices"
      >
        <fieldset :disabled="pending || !connected">
          <p class="electricity-muted">{{ text.priceHint }}</p>
          <div class="electricity-fields">
            <SensorPicker
              v-model="draft.price_sensor"
              :hass="hass"
              :label="text.source"
            /><label
              >{{ text.attribute
              }}<input
                v-model="draft.price_attribute"
                type="text"
                autocomplete="off" /></label
            ><label
              >{{ text.unit
              }}<select v-model="draft.price_unit">
                <option
                  v-for="(label, value) in text.units"
                  :key="value"
                  :value="value"
                >
                  {{ label }}
                </option>
              </select></label
            ><label
              >{{ text.feed }} (ct/kWh)<input
                v-model="feed"
                type="text"
                inputmode="decimal"
                name="dynamic_feed"
                autocomplete="off" /></label
            ><SensorPicker
              v-model="draft.pv_sensor"
              :hass="hass"
              :label="text.pv"
            /><label
              >{{ text.pvFactor
              }}<input
                v-model="pvFactor"
                type="number"
                min="0"
                max="100"
                step="1"
            /></label>
          </div>
          <p class="electricity-muted">{{ text.sourceHint }}</p>
        </fieldset>
        <div class="electricity-actions">
          <button type="submit" :disabled="pending || !connected || conflict">
            {{ text.save }}</button
          ><button type="button" :disabled="pending" @click="closePrices">
            {{ text.cancel }}
          </button>
        </div>
      </form>
    </section>
    <section v-if="known" class="electricity-card electricity-charging">
      <header>
        <div>
          <h2>{{ text.charging }}</h2>
          <p class="electricity-muted">{{ chargingSummary }}</p>
        </div>
        <button
          v-if="!chargingOpen"
          ref="chargingButton"
          type="button"
          :disabled="changing"
          :aria-expanded="chargingOpen"
          @click="chargingOpen = true"
        >
          {{ text.edit }}
        </button>
      </header>
      <div v-if="chargingOpen" class="electricity-charging-editor">
        <h3>{{ text.global }}</h3>
        <EntityControl
          domain="number"
          entity-key="max_soc"
          :label="text.global"
          hide-confirmed-label
        />
        <p class="electricity-muted">{{ text.globalHint }}</p>
        <template v-if="active === 'time_of_use'"
          ><EntityControl
            domain="switch"
            entity-key="bridge_charge_enabled"
            :label="text.bridge" /><EntityControl
            domain="number"
            entity-key="timed_charge_max_soc"
            :label="text.target"
            hide-confirmed-label /><EntityControl
            v-if="!bridge"
            domain="number"
            entity-key="timed_charge_min_soc"
            :label="text.minimum"
            hide-confirmed-label />
          <p v-if="!bridge" class="electricity-muted">{{ text.minimumHint }}</p>
          <h3>{{ text.months }}</h3>
          <MonthSelection :entity-keys="months"
        /></template>
        <template v-else
          ><EntityControl
            domain="select"
            entity-key="price_charge_strategy"
            hide-confirmed-label
          /><EntityControl
            v-if="strategy?.state?.state === 'absolute'"
            domain="number"
            entity-key="price_charge_max_price"
            hide-confirmed-label
          /><EntityControl
            domain="number"
            entity-key="price_charge_neutral_price"
            hide-confirmed-label
          />
          <p class="electricity-muted">{{ text.neutral }}</p>
          <EntityControl
            v-if="['relative', 'smart'].includes(strategy?.state?.state ?? '')"
            domain="number"
            entity-key="price_charge_hours"
            hide-confirmed-label
          />
          <p
            v-if="strategy?.state?.state === 'smart'"
            class="electricity-muted"
          >
            {{ text.budget }}
          </p></template
        >
        <div class="electricity-actions">
          <button type="button" @click="closeCharging">{{ text.done }}</button>
        </div>
      </div>
    </section>
    <details v-if="known" class="electricity-card electricity-plan">
      <summary>{{ text.details }}</summary>
      <ChargePlan
        v-if="active === 'time_of_use'"
        :hass="hass"
        hide-control
      /><template v-else
        ><EntityValue
          domain="sensor"
          entity-key="price_charge_active_text" /><EntityValue
          domain="sensor"
          entity-key="price_charge_status_text" /><EntityValue
          domain="sensor"
          entity-key="price_charge_next_start" /><EntityValue
          domain="sensor"
          entity-key="grid_serving_forecast"
      /></template>
    </details>
  </div>
</template>
<style>
.electricity-tariff-view {
  display: grid;
  gap: 16px;
  margin-top: 20px;
  min-width: 0;
}
.electricity-card {
  min-width: 0;
  padding: 20px;
  border: 1px solid var(--divider-color, #ddd);
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--card-background-color, #fff);
}
.electricity-card h2 {
  font-size: 18px;
  margin: 0;
}
.electricity-card h3 {
  font-size: 16px;
  margin: 20px 0 10px;
}
.electricity-card p {
  line-height: 1.6;
  margin: 10px 0 0;
}
.electricity-card button {
  font: inherit;
  min-height: 44px;
  padding: 8px 12px;
  cursor: pointer;
  border: 1px solid var(--divider-color, #ddd);
  border-radius: 7px;
  background: transparent;
  color: var(--primary-color, #03a9f4);
}
.electricity-card button:disabled {
  opacity: 0.5;
  cursor: default;
}
.electricity-card header,
.electricity-tariff-bar__row,
.electricity-price-card__heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
.electricity-card header > div {
  min-width: 0;
  flex: 1;
}
.electricity-card header > button {
  flex-shrink: 0;
  white-space: nowrap;
}
.electricity-active {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.electricity-active > span,
.electricity-muted {
  color: var(--secondary-text-color, #666);
}
.electricity-active > strong {
  color: var(--primary-color, #03a9f4);
}
.electricity-master {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  cursor: pointer;
}
.electricity-master input {
  width: 22px;
  height: 22px;
  accent-color: var(--primary-color, #03a9f4);
  flex-shrink: 0;
}
.electricity-choice {
  border-top: 1px solid var(--divider-color, #ddd);
  margin-top: 16px;
  padding-top: 16px;
}
.electricity-choice fieldset {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  min-width: 0;
  padding: 0;
  border: 0;
}
.electricity-choice fieldset > label {
  display: flex;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--divider-color, #ddd);
  border-radius: 8px;
  cursor: pointer;
}
.electricity-choice input {
  accent-color: var(--primary-color, #03a9f4);
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}
.electricity-choice strong,
.electricity-choice small {
  display: block;
}
.electricity-choice small {
  margin-top: 5px;
  color: var(--secondary-text-color, #666);
  font-size: 14px;
}
.electricity-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
.electricity-actions button[type="submit"] {
  background: var(--primary-color, #03a9f4);
  color: var(--text-primary-color, #fff);
}
.electricity-current-price {
  font-size: 32px;
  font-weight: 500;
  line-height: 1.1 !important;
}
.electricity-current-price span {
  font-size: 16px;
  font-weight: 400;
}
.electricity-days {
  display: flex;
  gap: 6px;
}
.electricity-days [aria-pressed="true"] {
  background: var(--secondary-background-color, #eee);
  border-color: var(--primary-color, #03a9f4);
}
.electricity-day {
  margin: 20px 0 !important;
}
.electricity-charge-status {
  border-top: 1px solid var(--divider-color, #ddd);
  padding-top: 14px;
  margin-top: 12px;
}
.electricity-error {
  color: var(--error-color, #db4437);
}
.electricity-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 16px;
}
.electricity-fields > label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  font-size: 14px;
}
.electricity-fields input,
.electricity-fields select {
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: 10px;
  font: inherit;
  color: var(--primary-text-color, #222);
  background: var(--card-background-color, #fff);
  border: 1px solid var(--divider-color, #ccc);
  border-radius: 6px;
}
.electricity-price-editor fieldset {
  padding: 0;
  margin: 0;
  border: 0;
  min-width: 0;
}
.electricity-charging-editor .entity-control {
  margin-top: 12px;
}
.electricity-plan > summary {
  font-size: 18px;
  font-weight: 500;
  cursor: pointer;
  min-height: 44px;
  display: list-item;
  align-content: center;
}
.electricity-plan > .charge-plan {
  border: 0;
  padding: 16px 0 0;
  box-shadow: none;
}
.electricity-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}
@media (max-width: 700px) {
  .electricity-tariff-bar__row {
    align-items: flex-start;
    flex-direction: column;
  }
  .electricity-fields,
  .electricity-choice fieldset {
    grid-template-columns: minmax(0, 1fr);
  }
  .electricity-price-card__heading {
    align-items: flex-start;
    flex-wrap: wrap;
  }
  .electricity-card {
    padding: 16px;
  }
  .electricity-card header {
    align-items: flex-start;
  }
  .electricity-current-price {
    font-size: 28px;
  }
}
</style>
