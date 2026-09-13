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
        tariff: props.compact
          ? "1. Wann ist dein Strom günstig?"
          : "Dein Stromtarif",
        introduction:
          "Trage die Preise aus deinem Stromvertrag ein. Sie gelten jeden Tag zu denselben Zeiten.",
        currentPrice: "Strompreis jetzt",
        baseSection: "Normaler Strompreis",
        windowsSection: "Zeiten mit anderem Preis",
        windowsHint:
          "Zum Beispiel ein günstiger Nachtpreis von 22:00 bis 06:00 Uhr. Nur die Zeiten eintragen, in denen ein anderer Preis als der Standardpreis gilt.",
        noWindows:
          "Noch keine anderen Preiszeiten: Der Standardpreis gilt den ganzen Tag.",
        feedSection: "Vergütung für Solarstrom",
        feedHint:
          "Wie viel erhältst du für eine eingespeiste kWh? Dieser Wert wird für die Ersparnisberechnung verwendet. Ohne Vergütung 0 eintragen.",
        impact: "Das bewirkt dein Tarif",
        impactHint:
          "Die Automatik nutzt die günstigsten Zeiten für die feste und verbrauchsbasierte Netzladung. Ladestand, Ladeziel und aktive Monate gelten zusätzlich.",
        saveHint:
          "Speichern übernimmt Preise und mögliche Ladezeiten. Es schaltet die Netzladung nicht ein.",
        pvDetails: "Zusätzlich: Solarprognose für die Ladeplanung",
        pvHint:
          "Nur für verbrauchsbasierte Ladeplanung erforderlich. Wähle die eingerichtete PV-Prognosequelle, damit die Planung den Bedarf bis zum Solarstart berechnen kann.",
        allPrices: "Alle Preise ansehen",
        everyDay: "Täglich",
        remaining: "zu allen übrigen Zeiten",
        overnightLabel: "über Nacht",
        technicalReason: "Technischer Hinweis",
        awaitingTariff: "Die aktuellen Ladezeiten werden aktualisiert.",
        pv: "PV-Start-Sensor (optional)",
        pvRequired: "PV-Start-Sensor (erforderlich)",
        gross:
          "Alle Preise in ct/kWh inklusive Steuern, ohne monatliche Grundgebühr. Beispiel: 30 eingeben für 30 ct/kWh.",
        edit: "Bearbeiten",
        save: "Speichern",
        cancel: "Abbrechen",
        saving: "Wird gespeichert …",
        loading: "Wird geladen …",
        add: "+ Zeitfenster hinzufügen",
        remove: "Entfernen",
        window: "Zeitfenster",
        baseHint:
          "Gilt den ganzen Tag, außer zu den unten eingetragenen Zeiten.",
        overnight:
          "Endet ein Fenster vor seiner Startzeit, gilt es über Mitternacht. Fenster dürfen sich nicht überschneiden.",
        details: "Wie werden günstige Ladezeiten ausgewählt?",
        first:
          "Trage zuerst deinen normalen Strompreis ein. Ergänze danach abweichende Preiszeiten und die Einspeisevergütung.",
        priceError:
          "Bitte Preise mit höchstens zwei Nachkommastellen eingeben: Standardpreis und Zeitfenster von −200 bis 500 ct/kWh, Einspeisevergütung von 0 bis 200 ct/kWh.",
        startError: "Bitte eine vollständige Startzeit eingeben (z. B. 12:30).",
        endError: "Bitte eine vollständige Endzeit eingeben (z. B. 14:30).",
        equalTimeError: "Start und Ende müssen verschieden sein.",
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
        pvMissing:
          "Der gewählte PV-Start-Sensor wurde nicht gefunden. Wähle einen vorhandenen Sensor oder entferne die Auswahl, wenn die Quelle optional ist.",
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
        low: "günstig",
        lowTariffPrice: "Günstigster Tagespreis",
        lowUntil: "Günstige Zeit bis",
        notLow: "Aktuell außerhalb der günstigsten Zeiten.",
        rule: "Der niedrigste täglich vorkommende Strompreis heißt Niedertarif. Alle Zeiten mit diesem Preis sind mögliche Ladezeiten. Auch der Standardpreis zählt, wenn er in Lücken zwischen den Zeitfenstern gilt. Die feste und verbrauchsbasierte Netzladung verwenden ausschließlich diese günstigsten Zeiten.",
        configure:
          "Bisherige separate Netzladezeiten sind bei diesem Tarif unwirksam.",
        noLowTariff:
          "Günstige Ladezeiten sind derzeit nicht verfügbar. Die SOC-Ladung bleibt gesperrt, bis gültige Tarifdaten vorliegen. Prüfe die Preise über Bearbeiten, wenn dieser Hinweis bestehen bleibt.",
        feed: "Einspeisevergütung",
        next: "Nächster Preiswechsel",
        unavailable: "Nicht verfügbar",
        noPrice: "Derzeit ist kein aktueller Strompreis verfügbar.",
      }
    : {
        tariff: props.compact
          ? "1. When is your electricity cheaper?"
          : "Your electricity tariff",
        introduction:
          "Enter the prices from your electricity contract. They apply at the same times every day.",
        currentPrice: "Electricity price now",
        baseSection: "Regular electricity price",
        windowsSection: "Times with a different price",
        windowsHint:
          "For example, a cheaper night rate from 22:00 to 06:00. Only add times when a different price applies instead of the standard price.",
        noWindows:
          "No other price periods yet: the standard price applies all day.",
        feedSection: "Payment for solar electricity",
        feedHint:
          "How much do you receive for each exported kWh? This value is used to calculate savings. Enter 0 if you receive no payment.",
        impact: "What your tariff does",
        impactHint:
          "Automation uses the cheapest times for fixed-target and consumption-based grid charging. Battery level, charging target and active months also apply.",
        saveHint:
          "Saving applies the prices and possible charging times. It does not turn on grid charging.",
        pvDetails: "Additional setup: solar forecast for charging planning",
        pvHint:
          "Only required for consumption-based charging planning. Select your configured PV forecast source so planning can calculate the energy needed until solar production starts.",
        allPrices: "View all prices",
        everyDay: "Every day",
        remaining: "at all remaining times",
        overnightLabel: "overnight",
        technicalReason: "Technical details",
        awaitingTariff: "Current charging times are being updated.",
        pv: "PV start sensor (optional)",
        pvRequired: "PV start sensor (required)",
        gross:
          "All prices in ct/kWh including tax, excluding the monthly standing charge. Example: enter 30 for 30 ct/kWh.",
        edit: "Edit",
        save: "Save",
        cancel: "Cancel",
        saving: "Saving …",
        loading: "Loading …",
        add: "+ Add time window",
        remove: "Remove",
        window: "Time window",
        baseHint: "Applies all day, except during the times entered below.",
        overnight:
          "A window ending before its start continues past midnight. Windows must not overlap.",
        details: "How are the cheapest charging times selected?",
        first:
          "Start with your regular electricity price. Then add any different price periods and your feed-in payment.",
        priceError:
          "Enter prices with up to two decimal places: standard price and windows from −200 to 500 ct/kWh, feed-in remuneration from 0 to 200 ct/kWh.",
        startError: "Enter a complete start time (e.g. 12:30).",
        endError: "Enter a complete end time (e.g. 14:30).",
        equalTimeError: "Start and end must differ.",
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
        pvMissing:
          "The selected PV start sensor was not found. Choose an existing sensor or clear the selection if this source is optional.",
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
        low: "cheapest",
        lowTariffPrice: "Cheapest daily price",
        lowUntil: "Cheapest period until",
        notLow: "Currently outside the cheapest times.",
        rule: "The lowest price level that actually occurs each day is called the low tariff. Every period at this price is a possible charging time. The standard price also counts when it applies in gaps between windows. Fixed-target and consumption-based grid charging only use these cheapest times.",
        configure:
          "Previously configured separate grid charging times have no effect for this tariff.",
        noLowTariff:
          "The cheapest charging times are currently unavailable. SOC charging remains blocked until valid tariff data is available. Check the prices using Edit if this message persists.",
        feed: "Feed-in remuneration",
        next: "Next price change",
        unavailable: "Unavailable",
        noPrice: "The current electricity price is unavailable.",
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
const currentPrice = computed(() => {
  const formatted = formatSavingsNumber(
    price.value?.state?.state,
    props.hass,
    2,
  );
  return formatted === null ? text.value.unavailable : `${formatted} ct/kWh`;
});
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
const attributes = computed<Readonly<Record<string, unknown>>>(() => {
  const profile =
    savedProfile.value ??
    (props.compact || !sourceAttributes.value.tariff_type
      ? dashboard?.tariff.value
      : null);
  if (!profile) return sourceAttributes.value;
  const configured = {
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
  // REQ-VUE-TARIFF-EDITOR: only matching telemetry can identify cheap periods.
  return tariffFingerprint(configured) ===
    tariffFingerprint(sourceAttributes.value)
    ? sourceAttributes.value
    : configured;
});
const tariffMetadataMatches = computed(
  () =>
    tariffFingerprint(attributes.value) ===
    tariffFingerprint(sourceAttributes.value),
);
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
const timeError = ref<{
  key: number;
  field: "start" | "end";
  reason: "startError" | "endError" | "equalTimeError";
} | null>(null);
const conflict = ref(false);
const saved = ref(false);
const connectionAvailable = computed(
  () => dashboard?.connected.value === true && dashboard.ready.value,
);
const errorMessage = computed(() => {
  if (error.value === "timeError" && timeError.value) {
    const index = draftWindows.value.findIndex(
      (window) => window.key === timeError.value!.key,
    );
    return `${text.value.window} ${index + 1}: ${text.value[timeError.value.reason]}`;
  }
  return error.value ? text.value[error.value as "failed"] : null;
});
function timeInput(key: number, field: "start" | "end") {
  return editor.value?.querySelector<HTMLInputElement>(
    `[name="window_${key}_${field}"]`,
  );
}
function changeTime(key: number, field: "start" | "end", event: Event) {
  const window = draftWindows.value.find((window) => window.key === key);
  if (window) window[field] = (event.target as HTMLInputElement).value;
  clearTimeError(key);
}
function clearTimeError(key?: number) {
  if (key !== undefined && timeError.value?.key !== key) return;
  timeError.value = null;
  if (error.value === "timeError") error.value = null;
}
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
      : code === "pv_sensor_missing"
        ? "pvMissing"
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
  clearTimeError();
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
  clearTimeError();
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
  clearTimeError(draftWindows.value[index]?.key);
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
  clearTimeError();
  // REQ-VUE-TARIFF-EDITOR: native pickers can commit independently of Vue's input event.
  for (const window of draftWindows.value) {
    for (const field of ["start", "end"] as const) {
      const input = timeInput(window.key, field);
      if (input) window[field] = input.value;
    }
  }
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
      const field = start === null ? "start" : "end";
      timeError.value = {
        key: window.key,
        field,
        reason:
          start === null
            ? "startError"
            : end === null
              ? "endError"
              : "equalTimeError",
      };
      error.value = "timeError";
      await nextTick();
      timeInput(window.key, field)?.focus();
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
    <p v-if="!editing" class="tariff-plan__introduction">
      {{ text.introduction }}
    </p>
    <div v-if="compact && !editing" class="tariff-plan__compact-summary">
      <p>
        <strong
          >{{ text.base }}:
          {{ tariffPrice(attributes.base_price_eur_kwh) }}</strong
        ><span v-if="baseLow" class="tariff-plan__badge">{{ text.low }}</span
        ><br />{{ text.remaining }}
      </p>
      <ul v-if="windows.length" class="tariff-plan__periods">
        <li v-for="(window, index) in windows" :key="index">
          <span
            >{{ text.everyDay }} {{ clock(window.start) }} –
            {{ clock(window.end)
            }}<span v-if="window.end < window.start">
              ({{ text.overnightLabel }})</span
            ></span
          >
          <span class="tariff-plan__period-price"
            ><span v-if="isLow(window)" class="tariff-plan__badge">{{
              text.low
            }}</span
            ><strong>{{ tariffPrice(window.price_eur_kwh) }}</strong></span
          >
        </li>
      </ul>
      <p v-else>{{ text.noWindows }}</p>
      <p v-if="lowTariffAvailable" class="tariff-plan__low-status">
        <strong>{{ text.lowTariffPrice }}:</strong>
        {{ tariffPrice(attributes.low_tariff_price_eur_kwh) }}.
        <template v-if="lowTariffActive"
          >{{ text.lowUntil }} {{ lowTariffUntil }}.</template
        >
        <template v-else>{{ text.notLow }}</template>
      </p>
      <p
        v-else-if="savedProfile || !tariffMetadataMatches"
        class="tariff-plan__pending-status"
      >
        {{ text.awaitingTariff }}
      </p>
      <p v-else class="tariff-plan__low-unavailable">{{ text.noLowTariff }}</p>
      <p class="tariff-plan__impact">{{ text.impactHint }}</p>
    </div>
    <p v-if="saved" role="status">{{ text.saved }}</p>
    <p
      v-if="errorMessage"
      :id="`${id}-error`"
      role="alert"
      class="tariff-plan__error"
    >
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
        <div class="tariff-plan__step">
          <h3>{{ text.baseSection }}</h3>
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
        </div>
        <div class="tariff-plan__step">
          <h3>{{ text.windowsSection }}</h3>
          <p class="tariff-plan__hint">{{ text.windowsHint }}</p>
          <p v-if="!draftWindows.length" class="tariff-plan__empty">
            {{ text.noWindows }}
          </p>
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
                :name="`window_${window.key}_start`"
                type="time"
                :aria-invalid="
                  timeError?.key === window.key && timeError.field === 'start'
                "
                :aria-describedby="
                  timeError?.key === window.key && timeError.field === 'start'
                    ? `${id}-error`
                    : undefined
                "
                @input="clearTimeError(window.key)"
                @change="changeTime(window.key, 'start', $event)"
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
                :name="`window_${window.key}_end`"
                type="time"
                :aria-invalid="
                  timeError?.key === window.key && timeError.field === 'end'
                "
                :aria-describedby="
                  timeError?.key === window.key && timeError.field === 'end'
                    ? `${id}-error`
                    : undefined
                "
                @input="clearTimeError(window.key)"
                @change="changeTime(window.key, 'end', $event)"
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
          <p v-if="draftWindows.length" class="tariff-plan__hint">
            {{ text.overnight }}
          </p>
        </div>
        <div class="tariff-plan__step">
          <h3>{{ text.feedSection }}</h3>
          <label
            >{{ text.feed }} (ct/kWh)<input
              v-model="feedInput"
              name="feed_in_price"
              type="text"
              inputmode="decimal"
              autocomplete="off"
              :aria-describedby="`${id}-feed-hint`"
            /><small :id="`${id}-feed-hint`">{{ text.feedHint }}</small></label
          >
        </div>
        <details
          v-if="compact"
          class="tariff-plan__details tariff-plan__pv-details"
          :open="
            bridgeEnabled ||
            error === 'bridgePvRequired' ||
            error === 'pvMissing'
          "
        >
          <summary>{{ text.pvDetails }}</summary>
          <p class="tariff-plan__hint">{{ text.pvHint }}</p>
          <SensorPicker
            v-model="pvSensor"
            :hass="hass"
            :label="bridgeEnabled ? text.pvRequired : text.pv"
          />
        </details>
        <div class="tariff-plan__impact">
          <strong>{{ text.impact }}</strong>
          <p>{{ text.impactHint }}</p>
          <p>{{ text.saveHint }}</p>
        </div>
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
    <div
      v-if="!editing && !compact && !savedProfile"
      class="tariff-plan__overview"
    >
      <p class="tariff-plan__current-price">
        <span>{{ text.currentPrice }}</span
        ><strong>{{ hasPrice ? currentPrice : text.unavailable }}</strong>
      </p>
      <p v-if="lowTariffAvailable" class="tariff-plan__low-status">
        <strong>{{ text.lowTariffPrice }}:</strong>
        {{ tariffPrice(attributes.low_tariff_price_eur_kwh) }}.
        <template v-if="lowTariffActive">
          {{ text.lowUntil }} {{ lowTariffUntil }}.
        </template>
        <template v-else>{{ text.notLow }}</template>
      </p>
      <p v-else class="tariff-plan__low-unavailable">
        {{ text.noLowTariff }}
      </p>
    </div>
    <p
      v-if="
        !editing &&
        !compact &&
        hasPrice &&
        attributes.next_price_change_at &&
        !savedProfile
      "
    >
      <strong>{{ text.next }}:</strong>
      {{ timestamp(attributes.next_price_change_at) }}
    </p>
    <details
      v-if="!editing && !compact"
      class="tariff-plan__details tariff-plan__all-prices"
    >
      <summary>{{ text.allPrices }}</summary>
      <div
        class="tariff-plan__scroll"
        tabindex="0"
        role="region"
        :aria-label="text.allPrices"
      >
        <table class="tariff-plan__table">
          <thead>
            <tr>
              <th scope="col">{{ text.status }}</th>
              <th scope="col">{{ text.from }}</th>
              <th scope="col">{{ text.to }}</th>
              <th scope="col">{{ text.price }}</th>
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
      <p>
        <strong>{{ text.feed }}:</strong>
        {{ tariffPrice(attributes.feed_in_price_eur_kwh) }}
      </p>
      <p v-if="!hasPrice && !savedProfile">
        {{ text.noPrice
        }}<span v-if="typeof reason === 'string' && reason">
          {{ text.technicalReason }}: {{ reason }}</span
        >
      </p>
    </details>
    <details class="tariff-plan__details">
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
.tariff-plan__introduction {
  color: var(--secondary-text-color, #666);
  margin: 0 0 16px;
}
.tariff-plan__compact-summary {
  margin: 0;
}
.tariff-plan__periods {
  list-style: none;
  padding: 0;
  margin: 12px 0;
}
.tariff-plan__periods li {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 4px 12px;
  border-top: 1px solid var(--divider-color, #e0e0e0);
  padding: 10px 0;
  line-height: 1.5;
}
.tariff-plan__period-price {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.tariff-plan__badge {
  display: inline-block;
  margin-inline-start: 8px;
  padding: 2px 7px;
  border: 1px solid var(--success-color, #43a047);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
}
.tariff-plan__periods strong {
  white-space: nowrap;
}
.tariff-plan__step {
  margin: 20px 0;
}
.tariff-plan__step h3 {
  margin: 0 0 10px;
  font-size: 15px;
  line-height: 1.5;
}
.tariff-plan__step > label {
  max-width: 460px;
}
.tariff-plan__step > label input {
  max-width: 240px;
}
.tariff-plan__step .tariff-plan__hint {
  margin-top: 0;
}
.tariff-plan__impact {
  margin: 16px 0;
  padding: 14px;
  border-radius: 8px;
  background: var(--secondary-background-color, #f5f5f5);
  font-size: 14px;
  line-height: 1.6;
}
.tariff-plan__impact p {
  margin: 6px 0;
}
.tariff-plan__empty {
  color: var(--secondary-text-color, #666);
  font-size: 14px;
}
.tariff-plan__overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
  gap: 12px;
}
.tariff-plan__overview > p {
  margin: 0;
}
.tariff-plan__current-price {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: var(--secondary-background-color, #f5f5f5);
  border-radius: 8px;
}
.tariff-plan__current-price > span {
  font-size: 14px;
  color: var(--secondary-text-color, #666);
}
.tariff-plan__current-price > strong {
  font-size: 26px;
  font-variant-numeric: tabular-nums;
}
.tariff-plan__low-status {
  font-size: 14px;
  padding: 12px 0;
}
.tariff-plan__low-unavailable {
  font-size: 14px;
  border-inline-start: 3px solid var(--warning-color, #ff9800);
  padding-inline-start: 12px;
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
  flex-wrap: wrap;
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
.tariff-plan summary:focus-visible,
.tariff-plan__scroll:focus-visible {
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
.tariff-plan input[aria-invalid="true"] {
  border-color: var(--error-color, #db4437);
}
.tariff-plan__details {
  margin-top: 14px;
  font-size: 14px;
}
.tariff-plan__details summary {
  cursor: pointer;
  color: var(--secondary-text-color, #666);
  padding: 12px 0;
  min-height: 44px;
  box-sizing: border-box;
  line-height: 1.5;
}
@media (max-width: 400px) {
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
