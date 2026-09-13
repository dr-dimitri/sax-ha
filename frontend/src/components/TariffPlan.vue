<script setup lang="ts">
import {
  computed,
  inject,
  nextTick,
  onBeforeUnmount,
  ref,
  useId,
  watch,
} from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import SensorPicker from "./SensorPicker.vue";
import {
  finiteValue,
  formatSavingsDate,
  formatSavingsNumber,
} from "../savings";
import type { HomeAssistant, TariffProfile } from "../types";

const props = defineProps<{ hass?: HomeAssistant; compact?: boolean }>();
const emit = defineEmits<{ saved: []; editing: [value: boolean] }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const id = useId();
const text = computed(() =>
  dashboard?.language.value === "de"
    ? {
        tariff: props.compact ? "Tarif & Preise" : "Tarifpreisfenster",
        pv: "PV-Start-Sensor (optional)",
        pvRequired: "PV-Start-Sensor (erforderlich)",
        windows: "Zeitfenster",
        gross:
          "Alle Preise brutto. Speichern aktualisiert auch die erlaubten Ladezeiten.",
        edit: "Bearbeiten",
        save: "Speichern",
        cancel: "Abbrechen",
        saving: "Wird gespeichert …",
        loading: "Wird geladen …",
        add: "+ Zeitfenster hinzufügen",
        remove: "Entfernen",
        window: "Zeitfenster",
        baseHint: "Gilt außerhalb der Zeitfenster.",
        overnight:
          "Endet ein Fenster vor seiner Startzeit, gilt es über Mitternacht. Fenster dürfen sich nicht überschneiden.",
        details: "So gelten die Ladezeiten",
        first:
          "Trage zuerst Standardpreis und Einspeisevergütung ein. Nebentarife kannst du bei Bedarf als Zeitfenster ergänzen.",
        priceError:
          "Bitte Preise mit höchstens zwei Nachkommastellen eingeben: Standardpreis und Zeitfenster von −200 bis 500 ct/kWh, Einspeisevergütung von 0 bis 200 ct/kWh.",
        timeError:
          "Bitte gültige Start- und Endzeiten eingeben. Start und Ende müssen verschieden sein.",
        overlap: "Die Zeitfenster überschneiden sich. Bitte die Zeiten prüfen.",
        disconnected:
          "Keine Verbindung zu Home Assistant. Dein Entwurf bleibt erhalten.",
        forbidden:
          "Tarife können nur mit einem Administratorkonto und bei aktivem zeitvariablen Tarif bearbeitet werden.",
        conflict:
          "Der Tarif wurde inzwischen geändert. Dein Entwurf bleibt erhalten. Lade den gespeicherten Tarif, bevor du erneut bearbeitest.",
        reload: "Gespeicherten Tarif laden (Entwurf verwerfen)",
        bridgePvRequired:
          "Die PV-Start-Quelle wird für die aktive verbrauchsbasierte Ladung benötigt. Wähle eine Quelle oder schalte diese Ladeplanung zuerst aus.",
        failed:
          "Der Tarif konnte nicht geladen oder gespeichert werden. Bitte erneut versuchen.",
        invalid:
          "Der Tarif wurde nicht gespeichert. Bitte Preise und Zeitfenster prüfen.",
        saved: "Tarif gespeichert.",
        from: "Von",
        to: "Bis",
        price: "Arbeitspreis",
        status: "Status",
        now: "jetzt",
        base: "Standardpreis",
        low: "Niedertarif",
        lowUntil: "Niedertarif aktiv bis",
        notLow: "Aktuell kein Niedertarif.",
        rule: "Die Tarifpreisfenster bestimmen die verbindlichen Ladezeiten. Niedertarif ist die niedrigste täglich tatsächlich vorkommende Preisstufe, einschließlich des Standardpreises in Fensterlücken. Die SOC-Ladung darf nur im Niedertarif laden; SOC-Grenzen und aktive Monate gelten weiterhin.",
        configure:
          "Bisherige separate Netzladezeiten sind bei diesem Tarif unwirksam.",
        noLowTariff:
          "Tarifdaten fehlen oder sind ungültig. Die SOC-Ladung bleibt gesperrt, bis gültige Tarifdaten vorliegen.",
        feed: "Einspeisevergütung",
        next: "Nächster Preiswechsel",
        unavailable: "Nicht verfügbar",
        noPrice:
          "Derzeit gilt kein Preis. Bitte die Tarifkonfiguration prüfen.",
      }
    : {
        tariff: props.compact ? "Tariff & prices" : "Tariff price windows",
        pv: "PV start sensor (optional)",
        pvRequired: "PV start sensor (required)",
        windows: "time windows",
        gross:
          "All prices include tax. Saving also updates the permitted charging times.",
        edit: "Edit",
        save: "Save",
        cancel: "Cancel",
        saving: "Saving …",
        loading: "Loading …",
        add: "+ Add time window",
        remove: "Remove",
        window: "Time window",
        baseHint: "Applies outside the time windows.",
        overnight:
          "A window ending before its start continues past midnight. Windows must not overlap.",
        details: "How charging times apply",
        first:
          "Start with the standard price and feed-in remuneration. Add time windows for other rates as needed.",
        priceError:
          "Enter prices with up to two decimal places: standard price and windows from −200 to 500 ct/kWh, feed-in remuneration from 0 to 200 ct/kWh.",
        timeError:
          "Enter valid start and end times. Start and end must differ.",
        overlap: "The time windows overlap. Please check the times.",
        disconnected:
          "Disconnected from Home Assistant. Your draft is preserved.",
        forbidden:
          "Editing tariffs requires an administrator account and an active time-of-use tariff.",
        conflict:
          "The tariff has changed elsewhere. Your draft is preserved. Load the saved tariff before editing again.",
        reload: "Load saved tariff (discard draft)",
        bridgePvRequired:
          "The active consumption-based charging plan requires a PV start source. Choose a source or turn off this charging plan first.",
        failed: "The tariff could not be loaded or saved. Please try again.",
        invalid:
          "The tariff was not saved. Please check prices and time windows.",
        saved: "Tariff saved.",
        from: "From",
        to: "To",
        price: "Import price",
        status: "Status",
        now: "now",
        base: "Standard price",
        low: "Low tariff",
        lowUntil: "Low tariff active until",
        notLow: "The low tariff is not currently active.",
        rule: "The tariff price windows define the binding charging times. The low tariff is the lowest price level that actually occurs each day, including the standard price in gaps between windows. SOC charging is only allowed during the low tariff; SOC limits and active months still apply.",
        configure:
          "Previously configured separate grid charging times have no effect for this tariff.",
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
  const price = finiteValue(value);
  const formatted = formatSavingsNumber(
    price === null ? null : price * 100,
    props.hass,
    2,
  );
  return formatted === null ? text.value.unavailable : `${formatted} ct/kWh`;
};
const timestamp = (value: unknown) =>
  formatSavingsDate(value, props.hass) ?? text.value.unavailable;
const savedProfile = ref<TariffProfile | null>(null);
const lastAttributes = ref<Readonly<Record<string, unknown>>>({});
watch(
  () => price.value?.state?.attributes,
  (value) => {
    if (value) lastAttributes.value = value;
  },
  { immediate: true },
);
const sourceAttributes = computed(
  () =>
    price.value?.state?.attributes ??
    (!dashboard?.connected.value ? lastAttributes.value : {}),
);
const savedSourceFingerprint = ref<string | null>(null);
function tariffFingerprint(
  attrs: Readonly<Record<string, unknown>>,
): string | null {
  if (!attrs.tariff_type) return null;
  const price = (value: unknown) => {
    const parsed = finiteValue(value);
    return parsed === null ? null : Math.round(parsed * 1e8) / 1e8;
  };
  const time = (value: unknown) =>
    typeof value === "string" && value.length === 5 ? `${value}:00` : value;
  const windows = Array.isArray(attrs.windows)
    ? attrs.windows
        .map((window) => {
          if (!window || typeof window !== "object") return null;
          return {
            start: time(window.start),
            end: time(window.end),
            price: price(window.price_eur_kwh),
          };
        })
        .sort((first, second) =>
          JSON.stringify(first).localeCompare(JSON.stringify(second)),
        )
    : null;
  return JSON.stringify({
    type: attrs.tariff_type,
    base: price(attrs.base_price_eur_kwh),
    feed: price(attrs.feed_in_price_eur_kwh),
    windows,
  });
}
function clearConfirmedProfile() {
  const profile = savedProfile.value;
  const actual = tariffFingerprint(sourceAttributes.value);
  if (!profile || !actual) return;
  const expected = tariffFingerprint({
    tariff_type: profile.tariff_type,
    base_price_eur_kwh:
      profile.base_price_ct_kwh === null
        ? null
        : profile.base_price_ct_kwh / 100,
    feed_in_price_eur_kwh:
      profile.feed_in_price_ct_kwh === null
        ? null
        : profile.feed_in_price_ct_kwh / 100,
    windows: profile.windows.map((window) => ({
      ...window,
      price_eur_kwh: window.price_ct_kwh / 100,
    })),
  });
  // REQ-VUE-TARIFF-EDITOR: ignore stale telemetry but accept newer tariff configuration.
  if (actual === expected || actual !== savedSourceFingerprint.value)
    savedProfile.value = null;
}
watch(sourceAttributes, clearConfirmedProfile);
let disposed = false;
onBeforeUnmount(() => {
  disposed = true;
});
watch(
  [() => dashboard?.ready.value, () => sourceAttributes.value.tariff_type],
  ([ready, type]) => {
    if (ready && !type && !dashboard?.tariff.value)
      void dashboard?.loadTariff().catch(() => {
        // REQ-VUE-TARIFF-EDITOR: missing read access must not create a card.
      });
  },
  { immediate: true },
);
const attributes = computed(() => {
  const profile =
    savedProfile.value ??
    (props.compact || !sourceAttributes.value.tariff_type
      ? dashboard?.tariff.value
      : null);
  if (!profile) return sourceAttributes.value;
  return {
    ...sourceAttributes.value,
    tariff_type: profile.tariff_type,
    base_price_eur_kwh:
      profile.base_price_ct_kwh === null
        ? null
        : profile.base_price_ct_kwh / 100,
    feed_in_price_eur_kwh:
      profile.feed_in_price_ct_kwh === null
        ? null
        : profile.feed_in_price_ct_kwh / 100,
    windows: profile.windows.map((window) => ({
      ...window,
      price_eur_kwh: window.price_ct_kwh / 100,
    })),
    active_window: null,
    low_tariff_price_eur_kwh: null,
  };
});
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
    reason.value == null &&
    !savedProfile.value,
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

const editing = ref(false);
watch(editing, (value) => emit("editing", value));
const pending = ref(false);
const pendingAction = ref<"loading" | "saving">("loading");
const editor = ref<HTMLElement>();
const editButton = ref<HTMLButtonElement>();
const profile = ref<TariffProfile | null>(null);
const baseInput = ref("");
const feedInput = ref("");
const pvSensor = ref<string | null>(null);
const bridgeEnabled = computed(
  () =>
    dashboard?.entity("switch", "bridge_charge_enabled")?.state?.state === "on",
);
const draftWindows = ref<
  { key: number; start: string; end: string; price: string }[]
>([]);
let windowKey = 0;
const error = ref<string | null>(null);
const conflict = ref(false);
const saved = ref(false);
const connectionAvailable = computed(
  () => dashboard?.connected.value === true && dashboard.ready.value,
);
const errorMessage = computed(() =>
  error.value ? text.value[error.value as "failed"] : null,
);
function reportError(cause: unknown) {
  if (disposed) return;
  const code =
    cause && typeof cause === "object" && "code" in cause
      ? cause.code
      : "failed";
  conflict.value = code === "conflict";
  error.value =
    code === "bridge_pv_start_required"
      ? "bridgePvRequired"
      : code === "invalid_tariff" || code === "invalid_format"
        ? "invalid"
        : ["conflict", "disconnected", "forbidden"].includes(String(code))
          ? String(code)
          : "failed";
}
function inputPrice(value: number | null) {
  return value === null
    ? ""
    : value
        .toFixed(2)
        .replace(".", dashboard?.language.value === "de" ? "," : ".");
}
async function openEditor() {
  if (!dashboard || pending.value) return;
  pendingAction.value = "loading";
  pending.value = true;
  error.value = null;
  saved.value = false;
  try {
    const result = await dashboard.loadTariff();
    if (disposed) return;
    if (!result.can_edit || result.tariff_type !== "time_of_use")
      throw { code: "forbidden" };
    profile.value = result;
    baseInput.value = inputPrice(result.base_price_ct_kwh);
    feedInput.value = inputPrice(result.feed_in_price_ct_kwh);
    pvSensor.value = result.profiles?.time_of_use.pv_sensor ?? null;
    draftWindows.value = result.windows.map((window) => ({
      key: windowKey++,
      start: window.start,
      end: window.end,
      price: inputPrice(window.price_ct_kwh),
    }));
    conflict.value = false;
    editing.value = true;
  } catch (cause) {
    reportError(cause);
  } finally {
    pending.value = false;
    await nextTick();
    if (editing.value)
      editor.value?.querySelector<HTMLInputElement>("input")?.focus();
  }
}
function cancel() {
  editing.value = false;
  error.value = null;
  conflict.value = false;
  draftWindows.value = [];
  void nextTick(() => editButton.value?.focus());
}
async function addWindow() {
  draftWindows.value.push({ key: windowKey++, start: "", end: "", price: "" });
  await nextTick();
  editor.value
    ?.querySelector<HTMLInputElement>(".tariff-plan__window:last-of-type input")
    ?.focus();
}
async function removeWindow(index: number) {
  draftWindows.value.splice(index, 1);
  await nextTick();
  const windows = editor.value?.querySelectorAll<HTMLElement>(
    ".tariff-plan__window",
  );
  const next =
    windows?.[
      Math.min(index, windows.length - 1)
    ]?.querySelector<HTMLInputElement>("input");
  (
    next ?? editor.value?.querySelector<HTMLButtonElement>(".tariff-plan__add")
  )?.focus();
}
function parsePrice(input: string, min: number, max: number): number | null {
  if (!/^-?\d+(?:[.,]\d{1,2})?$/.test(input.trim())) return null;
  const value = Number(input.trim().replace(",", "."));
  return Number.isFinite(value) && value >= min && value <= max ? value : null;
}
function timeSeconds(value: string): number | null {
  if (!/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(value)) return null;
  const [hours, minutes, seconds = 0] = value.split(":").map(Number);
  return hours! * 3600 + minutes! * 60 + seconds;
}
async function save() {
  if (!dashboard || !profile.value || pending.value || conflict.value) return;
  error.value = null;
  const base = parsePrice(baseInput.value, -200, 500);
  const feed = parsePrice(feedInput.value, 0, 200);
  const windows = draftWindows.value.map((window) => ({
    ...window,
    value: parsePrice(window.price, -200, 500),
  }));
  if (
    base === null ||
    feed === null ||
    windows.some((window) => window.value === null)
  ) {
    error.value = "priceError";
    return;
  }
  const segments: { start: number; end: number }[] = [];
  for (const window of windows) {
    const start = timeSeconds(window.start);
    const end = timeSeconds(window.end);
    if (start === null || end === null || start === end) {
      error.value = "timeError";
      return;
    }
    segments.push(
      ...(start < end
        ? [{ start, end }]
        : [
            { start, end: 86400 },
            { start: 0, end },
          ]),
    );
  }
  const orderedSegments = segments
    .filter((segment) => segment.start < segment.end)
    .sort((a, b) => a.start - b.start);
  if (
    orderedSegments.some(
      (segment, index) =>
        index > 0 && segment.start < orderedSegments[index - 1]!.end,
    )
  ) {
    error.value = "overlap";
    return;
  }
  pendingAction.value = "saving";
  pending.value = true;
  const sourceFingerprint = tariffFingerprint(sourceAttributes.value);
  try {
    const draft = {
      revision: profile.value.revision,
      base_price_ct_kwh: base,
      feed_in_price_ct_kwh: feed,
      windows: windows.map((window) => ({
        start: window.start.length === 5 ? `${window.start}:00` : window.start,
        end: window.end.length === 5 ? `${window.end}:00` : window.end,
        price_ct_kwh: window.value!,
      })),
    };
    const result = props.compact
      ? await dashboard.configureTariff({
          revision: draft.revision,
          tariff_type: "time_of_use",
          profile: {
            base_price_ct_kwh: draft.base_price_ct_kwh,
            feed_in_price_ct_kwh: draft.feed_in_price_ct_kwh,
            windows: draft.windows,
            pv_sensor: pvSensor.value,
          },
        })
      : await dashboard.saveTariff(draft);
    if (disposed) return;
    savedProfile.value = result;
    savedSourceFingerprint.value = sourceFingerprint;
    clearConfirmedProfile();
    cancel();
    saved.value = true;
    emit("saved");
  } catch (cause) {
    reportError(cause);
  } finally {
    pending.value = false;
  }
}
watch(connectionAvailable, (connected) => {
  if (!connected && editing.value) error.value = "disconnected";
  else if (connected && error.value === "disconnected") error.value = null;
});
watch(tariffVisible, (visible) => {
  if (!visible && dashboard?.ready.value) cancel();
});
</script>

<template>
  <section
    v-if="tariffVisible"
    class="tariff-plan"
    :aria-labelledby="`${id}-tariff`"
  >
    <header class="tariff-plan__header">
      <h2 :id="`${id}-tariff`">{{ text.tariff }}</h2>
      <button
        v-if="!editing"
        ref="editButton"
        type="button"
        :disabled="pending || !connectionAvailable"
        :aria-expanded="editing"
        :aria-controls="`${id}-editor`"
        @click="openEditor"
      >
        {{ pending ? text.loading : text.edit }}
      </button>
    </header>
    <p v-if="pending" role="status">
      {{ text[pendingAction] }}
    </p>
    <p v-if="compact && !editing" class="tariff-plan__compact-summary">
      {{ text.base }} {{ tariffPrice(attributes.base_price_eur_kwh) }} ·
      {{ windows.length }} {{ text.windows }} · {{ text.feed }}
      {{ tariffPrice(attributes.feed_in_price_eur_kwh) }}
    </p>
    <p v-if="saved" role="status">{{ text.saved }}</p>
    <p v-if="errorMessage" role="alert" class="tariff-plan__error">
      {{ errorMessage }}
    </p>
    <form
      v-if="editing"
      :id="`${id}-editor`"
      ref="editor"
      class="tariff-plan__editor"
      :aria-busy="pending"
      novalidate
      @submit.prevent="save"
    >
      <p v-if="profile?.base_price_ct_kwh === null">{{ text.first }}</p>
      <fieldset :disabled="pending || !connectionAvailable">
        <p class="tariff-plan__hint">{{ text.gross }}</p>
        <div class="tariff-plan__prices">
          <label
            >{{ text.base }} (ct/kWh)<input
              v-model="baseInput"
              name="base_price"
              type="text"
              inputmode="decimal"
              autocomplete="off"
              :aria-describedby="`${id}-base-hint`"
            /><small :id="`${id}-base-hint`">{{ text.baseHint }}</small></label
          >
          <label
            >{{ text.feed }} (ct/kWh)<input
              v-model="feedInput"
              name="feed_in_price"
              type="text"
              inputmode="decimal"
              autocomplete="off"
          /></label>
        </div>
        <SensorPicker
          v-if="compact"
          v-model="pvSensor"
          :hass="hass"
          :label="bridgeEnabled ? text.pvRequired : text.pv"
        />
        <div
          v-for="(window, index) in draftWindows"
          :key="window.key"
          class="tariff-plan__window"
        >
          <span class="tariff-plan__window-name"
            >{{ text.window }} {{ index + 1 }}</span
          >
          <label
            >{{ text.from
            }}<input
              v-model="window.start"
              type="time"
              :step="
                (window.start.slice(-2) !== '00' &&
                  window.start.length === 8) ||
                (window.end.slice(-2) !== '00' && window.end.length === 8)
                  ? 1
                  : 60
              "
              :aria-label="`${text.window} ${index + 1}: ${text.from}`"
          /></label>
          <label
            >{{ text.to
            }}<input
              v-model="window.end"
              type="time"
              :step="
                (window.start.slice(-2) !== '00' &&
                  window.start.length === 8) ||
                (window.end.slice(-2) !== '00' && window.end.length === 8)
                  ? 1
                  : 60
              "
              :aria-label="`${text.window} ${index + 1}: ${text.to}`"
          /></label>
          <label
            >{{ text.price }} (ct/kWh)<input
              v-model="window.price"
              type="text"
              inputmode="decimal"
              autocomplete="off"
              :aria-label="`${text.window} ${index + 1}: ${text.price} (ct/kWh)`"
          /></label>
          <button
            type="button"
            class="tariff-plan__remove"
            :aria-label="`${text.window} ${index + 1}: ${text.remove}`"
            @click="removeWindow(index)"
          >
            {{ text.remove }}
          </button>
        </div>
        <button
          v-if="draftWindows.length < 8"
          type="button"
          class="tariff-plan__add"
          @click="addWindow"
        >
          {{ text.add }}
        </button>
        <p class="tariff-plan__hint">{{ text.overnight }}</p>
      </fieldset>
      <div class="tariff-plan__actions">
        <button
          type="submit"
          class="tariff-plan__save"
          :disabled="pending || !connectionAvailable || conflict"
        >
          {{ pending ? text[pendingAction] : text.save }}
        </button>
        <button type="button" :disabled="pending" @click="cancel">
          {{ text.cancel }}
        </button>
        <button
          v-if="conflict"
          type="button"
          :disabled="pending || !connectionAvailable"
          @click="openEditor"
        >
          {{ text.reload }}
        </button>
      </div>
    </form>
    <div v-if="!editing && !compact" class="tariff-plan__scroll">
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
    <p
      v-if="!editing && !compact && lowTariffAvailable"
      class="tariff-plan__low-status"
    >
      <strong>{{ text.low }}:</strong>
      {{ tariffPrice(attributes.low_tariff_price_eur_kwh) }}.
      <template v-if="lowTariffActive">
        {{ text.lowUntil }} {{ lowTariffUntil }}.
      </template>
      <template v-else>{{ text.notLow }}</template>
    </p>
    <p
      v-else-if="!editing && !compact && !savedProfile"
      class="tariff-plan__low-unavailable"
    >
      {{ text.noLowTariff }}
    </p>
    <p v-if="!editing && !compact">
      <strong>{{ text.feed }}:</strong>
      {{ tariffPrice(attributes.feed_in_price_eur_kwh) }}
    </p>
    <p v-if="!editing && !compact && !hasPrice && !savedProfile">
      {{ text.noPrice
      }}<span v-if="typeof reason === 'string' && reason"> ({{ reason }})</span>
    </p>
    <p
      v-else-if="
        !editing && !compact && attributes.next_price_change_at && !savedProfile
      "
    >
      <strong>{{ text.next }}:</strong>
      {{ timestamp(attributes.next_price_change_at) }}
    </p>
    <details v-if="!compact" class="tariff-plan__details">
      <summary>{{ text.details }}</summary>
      <p>{{ text.rule }}</p>
      <p>{{ text.configure }}</p>
    </details>
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
.tariff-plan__compact-summary {
  color: var(--secondary-text-color, #666);
  margin: 0;
}
.tariff-plan__editor > fieldset > .sensor-picker {
  margin-top: 16px;
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
.tariff-plan__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.tariff-plan__header h2 {
  margin: 0;
}
.tariff-plan button {
  font: inherit;
  cursor: pointer;
  min-height: 44px;
  padding: 8px 12px;
  color: var(--primary-color, #03a9f4);
  background: transparent;
  border: 1px solid var(--divider-color, #e0e0e0);
  border-radius: 8px;
}
.tariff-plan button:disabled {
  cursor: default;
  opacity: 0.5;
}
.tariff-plan button:focus-visible,
.tariff-plan input:focus-visible,
.tariff-plan summary:focus-visible {
  outline: 2px solid var(--primary-color, #03a9f4);
  outline-offset: 2px;
}
.tariff-plan__editor {
  margin-bottom: 16px;
}
.tariff-plan__editor fieldset {
  min-width: 0;
  border: 0;
  padding: 0;
  margin: 0;
}
.tariff-plan__prices {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.tariff-plan__editor label {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
}
.tariff-plan__editor input {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 44px;
  border: 1px solid var(--divider-color, #bbb);
  border-radius: 6px;
  padding: 10px;
  font: inherit;
  font-variant-numeric: tabular-nums;
  color: var(--primary-text-color, #212121);
  background: var(--card-background-color, #fff);
}
.tariff-plan__editor small,
.tariff-plan__hint {
  font-size: 13px;
  color: var(--secondary-text-color, #666);
}
.tariff-plan__window {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--divider-color, #e0e0e0);
}
.tariff-plan__window-name {
  grid-column: 1 / -1;
  font-weight: 600;
  font-size: 14px;
}
.tariff-plan__window label:nth-of-type(3) {
  grid-column: 1;
}
.tariff-plan__remove {
  justify-self: end;
}
.tariff-plan__add {
  margin-top: 16px;
}
.tariff-plan__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tariff-plan .tariff-plan__save {
  background: var(--primary-color, #03a9f4);
  color: var(--text-primary-color, #fff);
}
.tariff-plan__error {
  color: var(--error-color, #db4437);
}
.tariff-plan__details {
  margin-top: 14px;
  font-size: 14px;
}
.tariff-plan__details summary {
  cursor: pointer;
  color: var(--secondary-text-color, #666);
  padding: 8px 0;
}
@media (max-width: 400px) {
  .tariff-plan__prices,
  .tariff-plan__window {
    grid-template-columns: minmax(0, 1fr);
  }
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
