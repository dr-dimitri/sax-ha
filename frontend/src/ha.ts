import {
  computed,
  onScopeDispose,
  reactive,
  readonly,
  ref,
  shallowRef,
  watch,
  type ComputedRef,
  type InjectionKey,
  type Ref,
} from "vue";
import type {
  DashboardEntityMetadata,
  DashboardMetadata,
  EntityDomain,
  HassEntity,
  HomeAssistant,
  TariffDraft,
  TariffConfiguration,
  TariffPriceSeries,
  TariffProfile,
  Unsubscribe,
} from "./types";

const messages = {
  de: {
    unavailable: "Nicht verfügbar",
    unknown: "Unbekannt",
    disconnected: "Keine Verbindung zu Home Assistant.",
    loadFailed: "Die SAX Power Entitäten konnten nicht geladen werden.",
    forbidden: "Diese Entität kann derzeit nicht bedient werden.",
    invalid: "Bitte einen gültigen Wert im erlaubten Bereich eingeben.",
    failed:
      "Die Änderung ist fehlgeschlagen. Bitte den aktuellen Zustand prüfen und erneut versuchen.",
    bridgePvRequired:
      "Öffne in Schritt 1 „Bearbeiten“ und ergänze die Solarprognose. Die bisherige Ladeweise bleibt erhalten.",
    bridgeTariffRequired:
      "Richte zuerst einen zeitvariablen Tarif mit gültigen Preisen ein. Die bisherige Ladeweise bleibt erhalten.",
    on: "Ein",
    off: "Aus",
  },
  en: {
    unavailable: "Unavailable",
    unknown: "Unknown",
    disconnected: "Disconnected from Home Assistant.",
    loadFailed: "The SAX Power entities could not be loaded.",
    forbidden: "This entity cannot be controlled at the moment.",
    invalid: "Please enter a valid value within the allowed range.",
    failed: "The change failed. Please check the current state and try again.",
    bridgePvRequired:
      "Open Edit in step 1 and add the solar forecast. The previous charging method is preserved.",
    bridgeTariffRequired:
      "First set up a time-of-use tariff with valid prices. The previous charging method is preserved.",
    on: "On",
    off: "Off",
  },
} as const;

type ErrorKey =
  | "disconnected"
  | "loadFailed"
  | "forbidden"
  | "invalid"
  | "failed"
  | "bridgePvRequired"
  | "bridgeTariffRequired";

export interface DashboardEntity {
  metadata: DashboardEntityMetadata;
  state: HassEntity | undefined;
  available: boolean;
  name: string;
  displayValue: string;
  canControl: boolean;
  pending: boolean;
  error: string | null;
}

export interface SaxDashboard {
  language: ComputedRef<"de" | "en">;
  ready: Readonly<Ref<boolean>>;
  connected: Readonly<Ref<boolean>>;
  error: ComputedRef<string | null>;
  entity(domain: EntityDomain, key: string): DashboardEntity | null;
  perform(domain: EntityDomain, key: string, value: unknown): Promise<boolean>;
  tariff: Readonly<Ref<TariffProfile | null>>;
  loadTariff(): Promise<TariffProfile>;
  saveTariff(draft: TariffDraft): Promise<TariffProfile>;
  configureTariff(configuration: TariffConfiguration): Promise<TariffProfile>;
  loadTariffSeries(day: "today" | "tomorrow"): Promise<TariffPriceSeries>;
  performTimeWindow(
    kind: "timed_charge" | "grid_serving",
    start: string,
    end: string,
  ): Promise<boolean>;
}

export const SAX_DASHBOARD_KEY: InjectionKey<SaxDashboard> =
  Symbol("sax-dashboard");

interface Action {
  pending: boolean;
  error: ErrorKey | null;
}

function normalizedTime(value: unknown): string | null {
  if (
    typeof value !== "string" ||
    (value.length !== 5 && value.length !== 8) ||
    !/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(value)
  ) {
    return null;
  }
  return value.length === 5 ? `${value}:00` : value;
}

function displayValue(
  hass: HomeAssistant | undefined,
  metadata: DashboardEntityMetadata,
  state: HassEntity | undefined,
  language: "de" | "en",
  connected: boolean,
): string {
  const text = messages[language];
  if (!connected || !state || state.state === "unavailable") {
    return text.unavailable;
  }
  if (state.state === "unknown") return text.unknown;
  if (hass?.formatEntityState) return hass.formatEntityState(state);
  if (metadata.states[state.state]) return metadata.states[state.state];
  if (state.attributes.device_class === "date") {
    const date = new Date(`${state.state}T00:00:00Z`);
    if (
      /^\d{4}-\d{2}-\d{2}$/.test(state.state) &&
      !Number.isNaN(date.getTime()) &&
      date.toISOString().slice(0, 10) === state.state
    ) {
      try {
        return new Intl.DateTimeFormat(
          hass?.locale?.language ?? hass?.language ?? language,
          { dateStyle: "medium", timeZone: "UTC" },
        ).format(date);
      } catch {
        return state.state;
      }
    }
    return state.state;
  }
  if (state.attributes.device_class === "timestamp") {
    const timestamp = new Date(state.state);
    if (!Number.isNaN(timestamp.getTime())) {
      try {
        return new Intl.DateTimeFormat(
          hass?.locale?.language ?? hass?.language ?? language,
          {
            dateStyle: "medium",
            timeStyle: "short",
            timeZone: hass?.config?.time_zone,
            hour12:
              hass?.locale?.time_format === "am_pm"
                ? true
                : hass?.locale?.time_format === "twenty_four"
                  ? false
                  : undefined,
          },
        ).format(timestamp);
      } catch {
        return state.state;
      }
    }
  }
  if (metadata.domain === "switch" || metadata.domain === "binary_sensor") {
    if (state.state === "on" || state.state === "off") return text[state.state];
  }
  const value = state.state.trim() === "" ? NaN : Number(state.state);
  if (Number.isFinite(value)) {
    const numberLocale =
      (
        {
          comma_decimal: "en-US",
          decimal_comma: "de-DE",
          space_comma: "fr-FR",
        } as Record<string, string>
      )[hass?.locale?.number_format ?? ""] ??
      hass?.locale?.language ??
      hass?.language ??
      language;
    let formatted: string;
    try {
      formatted = new Intl.NumberFormat(numberLocale, {
        maximumFractionDigits: 20,
        useGrouping: hass?.locale?.number_format !== "none",
      }).format(value);
    } catch {
      formatted = String(value);
    }
    const unit = state.attributes.unit_of_measurement;
    return typeof unit === "string" && unit
      ? `${formatted} ${unit}`
      : formatted;
  }
  return state.state;
}

function serviceCall(
  entity: DashboardEntity,
  value: unknown,
): { service: string; data: Record<string, unknown> } | null {
  const attrs = entity.state?.attributes ?? {};
  switch (entity.metadata.domain) {
    case "switch":
      return typeof value === "boolean"
        ? { service: value ? "turn_on" : "turn_off", data: {} }
        : null;
    case "number": {
      if (
        (typeof value !== "number" && typeof value !== "string") ||
        (typeof value === "string" && value.trim() === "")
      ) {
        return null;
      }
      const number = Number(value);
      const { min, max, step } = attrs;
      if (
        !Number.isFinite(number) ||
        typeof min !== "number" ||
        !Number.isFinite(min) ||
        typeof max !== "number" ||
        !Number.isFinite(max) ||
        typeof step !== "number" ||
        !Number.isFinite(step) ||
        step <= 0 ||
        min > max ||
        number < min ||
        number > max
      ) {
        return null;
      }
      const steps = (number - min) / step;
      if (
        !Number.isFinite(steps) ||
        Math.abs(steps - Math.round(steps)) > 1e-7
      ) {
        return null;
      }
      return { service: "set_value", data: { value: number } };
    }
    case "time": {
      const time = normalizedTime(value);
      return time ? { service: "set_value", data: { time } } : null;
    }
    case "select":
      return typeof value === "string" &&
        Array.isArray(attrs.options) &&
        attrs.options.includes(value)
        ? { service: "select_option", data: { option: value } }
        : null;
    default:
      return null;
  }
}

export function useSaxDashboard(
  getHass: () => HomeAssistant | undefined,
  getEntryId: () => string | undefined,
): SaxDashboard {
  const language = computed(() =>
    getHass()?.language.toLowerCase().startsWith("de") ? "de" : "en",
  );
  const tariff = shallowRef<TariffProfile | null>(null);
  const ready = ref(false);
  const connected = ref(false);
  const errorKey = ref<ErrorKey | null>(null);
  const error = computed(() =>
    errorKey.value ? messages[language.value][errorKey.value] : null,
  );
  const metadata = shallowRef<readonly DashboardEntityMetadata[]>([]);
  const actions = reactive(new Map<string, Action>());
  const running = reactive(new Map<string, Action>());
  const operationKey = (domain: EntityDomain, key: string) =>
    JSON.stringify([getEntryId(), domain, key]);
  let generation = 0;

  function reset(invalidateActions = true): void {
    if (invalidateActions) generation += 1;
    ready.value = false;
    tariff.value = null;
    metadata.value = [];
    for (const [id, action] of actions) {
      if (!action.pending) actions.delete(id);
      else action.error = null;
    }
  }

  const stop = watch(
    [() => getHass()?.connection, getEntryId, () => getHass()?.language],
    ([connection, entryId, locale], old, cleanup) => {
      reset(connection !== old?.[0] || entryId !== old?.[1]);
      errorKey.value = null;
      connected.value = connection?.connected ?? false;
      if (!connection || !entryId) return;

      let disposed = false;
      let unsubscribe: Unsubscribe | undefined;
      let subscriptionGeneration = 0;

      function release(unsub: Unsubscribe): void {
        try {
          void Promise.resolve(unsub()).catch(() => {
            // A closed socket has already dropped its backend subscriptions.
          });
        } catch {
          // A connection can close between the cleanup request and its send.
        }
      }

      function invalidate(invalidateActions = true): void {
        subscriptionGeneration += 1;
        reset(invalidateActions);
        if (unsubscribe) release(unsubscribe);
        unsubscribe = undefined;
      }

      function subscribe(): void {
        if (disposed || !connection || !connection.connected) return;
        invalidate(false);
        connected.value = true;
        errorKey.value = null;
        const current = subscriptionGeneration;
        // REQ-VUE-ENTITY-BINDING: own resubscription prevents duplicate streams.
        void connection
          .subscribeMessage<DashboardMetadata>(
            (message) => {
              if (
                disposed ||
                current !== subscriptionGeneration ||
                !connected.value
              ) {
                return;
              }
              metadata.value = message.entities;
              const currentIds = new Set(
                message.entities.map((item) => item.entity_id),
              );
              for (const id of actions.keys()) {
                if (!currentIds.has(id) && !actions.get(id)?.pending)
                  actions.delete(id);
              }
              ready.value = true;
              errorKey.value = null;
            },
            {
              type: "sax_power/dashboard/subscribe",
              entry_id: entryId,
              language: locale || "en",
            },
            { resubscribe: false },
          )
          .then((unsub) => {
            if (disposed || current !== subscriptionGeneration) {
              release(unsub);
            } else {
              unsubscribe = unsub;
            }
          })
          .catch(() => {
            if (!disposed && current === subscriptionGeneration) {
              reset();
              errorKey.value = "loadFailed";
            }
          });
      }

      function disconnect(): void {
        if (disposed) return;
        connected.value = false;
        invalidate();
        errorKey.value = "disconnected";
      }

      connection.addEventListener("ready", subscribe);
      connection.addEventListener("disconnected", disconnect);
      connection.addEventListener("reconnect-error", disconnect);
      if (connection.connected) subscribe();
      else errorKey.value = "disconnected";

      cleanup(() => {
        disposed = true;
        connection.removeEventListener("ready", subscribe);
        connection.removeEventListener("disconnected", disconnect);
        connection.removeEventListener("reconnect-error", disconnect);
        invalidate(
          getHass()?.connection !== connection || getEntryId() !== entryId,
        );
      });
    },
    { immediate: true, flush: "sync" },
  );

  onScopeDispose(() => {
    stop();
    reset();
    connected.value = false;
  });

  function entity(domain: EntityDomain, key: string): DashboardEntity | null {
    const item = metadata.value.find(
      (entry) => entry.domain === domain && entry.key === key,
    );
    if (!item) return null;
    const hass = getHass();
    const state = hass?.states[item.entity_id];
    const available =
      connected.value &&
      !!state &&
      state.state !== "unknown" &&
      state.state !== "unavailable";
    const action =
      running.get(operationKey(domain, key)) ?? actions.get(item.entity_id);
    return {
      metadata: item,
      state,
      available,
      name:
        item.name ??
        (typeof state?.attributes.friendly_name === "string"
          ? state.attributes.friendly_name
          : item.key),
      displayValue: displayValue(
        hass,
        item,
        state,
        language.value,
        connected.value,
      ),
      canControl: available && item.can_control && !!hass?.callService,
      pending: action?.pending ?? false,
      error: action?.error ? messages[language.value][action.error] : null,
    };
  }

  async function perform(
    domain: EntityDomain,
    key: string,
    value: unknown,
  ): Promise<boolean> {
    const item = entity(domain, key);
    if (!item) return false;
    if (item.pending) return false;
    const action: Action = reactive({ pending: false, error: null });
    actions.set(item.metadata.entity_id, action);
    const hass = getHass();
    if (!item.canControl || !hass?.callService || !ready.value) {
      action.error = "forbidden";
      return false;
    }
    const call = serviceCall(item, value);
    if (!call) {
      action.error = "invalid";
      return false;
    }
    action.pending = true;
    const operation = operationKey(domain, key);
    running.set(operation, action);
    const current = generation;
    const isCurrent = () =>
      current === generation &&
      actions.get(item.metadata.entity_id) === action &&
      entity(domain, key)?.metadata.entity_id === item.metadata.entity_id;
    try {
      await hass.callService(
        domain,
        call.service,
        call.data,
        { entity_id: item.metadata.entity_id },
        false,
      );
      return isCurrent();
    } catch (cause) {
      if (isCurrent()) {
        action.error = "failed";
        if (
          domain === "switch" &&
          key === "bridge_charge_enabled" &&
          cause &&
          typeof cause === "object" &&
          "translation_domain" in cause &&
          cause.translation_domain === "sax_power" &&
          "translation_key" in cause
        ) {
          if (cause.translation_key === "bridge_pv_start_required")
            action.error = "bridgePvRequired";
          else if (cause.translation_key === "bridge_tariff_required")
            action.error = "bridgeTariffRequired";
        }
      }
      return false;
    } finally {
      action.pending = false;
      if (running.get(operation) === action) running.delete(operation);
    }
  }

  async function performTimeWindow(
    kind: "timed_charge" | "grid_serving",
    start: string,
    end: string,
  ): Promise<boolean> {
    const keys = [`${kind}_start`, `${kind}_end`];
    const items = keys.map((key) => entity("time", key));
    if (items.some((item) => item?.pending)) return false;
    const action: Action = reactive({ pending: false, error: null });
    for (const item of items) {
      if (item) actions.set(item.metadata.entity_id, action);
    }
    const deviceId = items[0]?.metadata.device_id;
    const hass = getHass();
    if (
      !ready.value ||
      !hass?.callService ||
      !deviceId ||
      items.some(
        (item) => !item?.canControl || item.metadata.device_id !== deviceId,
      )
    ) {
      action.error = "forbidden";
      return false;
    }
    const normalizedStart = normalizedTime(start);
    const normalizedEnd = normalizedTime(end);
    if (!normalizedStart || !normalizedEnd) {
      action.error = "invalid";
      return false;
    }
    const entityIds = items.map((item) => item!.metadata.entity_id);
    const operations = keys.map((key) => operationKey("time", key));
    action.pending = true;
    for (const operation of operations) running.set(operation, action);
    const current = generation;
    const isCurrent = () =>
      current === generation &&
      entityIds.every((id, index) => {
        const currentItem = entity("time", keys[index]!);
        return (
          actions.get(id) === action &&
          currentItem?.metadata.entity_id === id &&
          currentItem.metadata.device_id === deviceId
        );
      });
    try {
      await hass.callService(
        "sax_power",
        `set_${kind}_window`,
        { device_id: deviceId, start: normalizedStart, end: normalizedEnd },
        undefined,
        false,
      );
      return isCurrent();
    } catch {
      if (isCurrent()) action.error = "failed";
      return false;
    } finally {
      action.pending = false;
      for (const operation of operations) {
        if (running.get(operation) === action) running.delete(operation);
      }
    }
  }

  let tariffReadSequence = 0;
  let tariffWrite: {
    generation: number;
    promise: Promise<TariffProfile>;
  } | null = null;

  let tariffRead: {
    generation: number;
    sequence: number;
    promise: Promise<TariffProfile>;
  } | null = null;

  async function tariffRequest(
    draft?: TariffDraft | TariffConfiguration,
  ): Promise<TariffProfile> {
    const hass = getHass();
    const entryId = getEntryId();
    if (!connected.value) throw { code: "disconnected" };
    if (!ready.value || !hass?.callWS || !entryId) throw { code: "forbidden" };
    const current = generation;
    if (!draft && tariffWrite?.generation === current)
      return tariffWrite.promise;
    const request = ++tariffReadSequence;
    const response = hass.callWS<TariffProfile>({
      type: `sax_power/dashboard/tariff/${draft ? ("tariff_type" in draft ? "configure" : "save") : "get"}`,
      entry_id: entryId,
      ...draft,
    });
    const operation: Promise<TariffProfile> =
      (async (): Promise<TariffProfile> => {
        const profile = await response;
        if (current !== generation || !connected.value)
          throw { code: "disconnected" };
        if (!profile || typeof profile.revision !== "string")
          throw { code: "failed" };
        // REQ-VUE-ELECTRICITY-TARIFF: a delayed read must never undo a confirmed write.
        if (!draft && request !== tariffReadSequence) {
          if (tariffWrite?.generation === current) return tariffWrite.promise;
          if (
            tariffRead?.generation === current &&
            tariffRead.sequence !== request
          )
            return tariffRead.promise;
          return tariff.value ?? profile;
        }
        if (draft) tariffReadSequence++;
        tariff.value = profile;
        return profile;
      })();
    if (draft) tariffWrite = { generation: current, promise: operation };
    else
      tariffRead = {
        generation: current,
        sequence: request,
        promise: operation,
      };
    try {
      return await operation;
    } finally {
      if (tariffWrite?.promise === operation) tariffWrite = null;
      if (tariffRead?.promise === operation) tariffRead = null;
    }
  }

  async function loadTariffSeries(
    day: "today" | "tomorrow",
  ): Promise<TariffPriceSeries> {
    const hass = getHass();
    const entryId = getEntryId();
    if (!connected.value) throw { code: "disconnected" };
    if (!ready.value || !hass?.callWS || !entryId) throw { code: "forbidden" };
    const current = generation;
    const result = await hass.callWS<TariffPriceSeries>({
      type: "sax_power/dashboard/tariff/series",
      entry_id: entryId,
      day,
    });
    if (current !== generation || !connected.value)
      throw { code: "disconnected" };
    if (
      !result ||
      !Array.isArray(result.slots) ||
      typeof result.start !== "string"
    )
      throw { code: "failed" };
    return result;
  }

  return {
    language,
    ready: readonly(ready),
    connected: readonly(connected),
    error,
    entity,
    perform,
    performTimeWindow,
    tariff: computed(() => tariff.value),
    loadTariff: () => tariffRequest(),
    saveTariff: (draft) => tariffRequest(draft),
    configureTariff: (configuration) => tariffRequest(configuration),
    loadTariffSeries,
  };
}
