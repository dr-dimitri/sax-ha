import { onScopeDispose, ref, shallowRef, watch } from "vue";
import type { HomeAssistant, Unsubscribe } from "./types";

export interface SavingsPeriod {
  start: string | null;
  end: string | null;
  change: number | null;
}

export interface SavingsStatistics {
  entity_id: string | null;
  time_zone: string;
  today: string;
  status: "ok" | "missing_entity" | "recorder_unavailable";
  periods: Record<"day" | "week" | "month" | "year", SavingsPeriod>;
  selected: {
    start_date: string;
    end_date: string;
    start: string;
    end: string;
    change: number | null;
    period: "hour" | "day" | "month";
    buckets: { start: string; end: string; change: number | null }[];
  };
}

export function finiteValue(value: unknown): number | null {
  if (typeof value !== "number" && typeof value !== "string") return null;
  if (typeof value === "string" && !value.trim()) return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function numberLocale(hass: HomeAssistant | undefined): string {
  return (
    (
      {
        comma_decimal: "en-US",
        decimal_comma: "de-DE",
        space_comma: "fr-FR",
      } as Record<string, string>
    )[hass?.locale?.number_format ?? ""] ??
    hass?.locale?.language ??
    hass?.language ??
    "en"
  );
}

export function formatSavingsNumber(
  value: unknown,
  hass: HomeAssistant | undefined,
  digits = 2,
): string | null {
  const number = finiteValue(value);
  if (number === null) return null;
  return new Intl.NumberFormat(numberLocale(hass), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    useGrouping: hass?.locale?.number_format !== "none",
  }).format(number);
}

export function formatSavingsDate(
  value: unknown,
  hass: HomeAssistant | undefined,
  options: Intl.DateTimeFormatOptions = {
    dateStyle: "medium",
    timeStyle: "short",
  },
): string | null {
  if (typeof value !== "string" || !value) return null;
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return null;
  return new Intl.DateTimeFormat(
    hass?.locale?.language ?? hass?.language ?? "en",
    {
      timeZone: hass?.config?.time_zone,
      hour12:
        hass?.locale?.time_format === "am_pm"
          ? true
          : hass?.locale?.time_format === "twenty_four"
            ? false
            : undefined,
      ...options,
    },
  ).format(date);
}

export function validSavingsDates(start: string, end: string): boolean {
  const valid = (value: string) =>
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    Number(value.slice(0, 4)) > 0 &&
    Number.isFinite(Date.parse(`${value}T00:00:00Z`)) &&
    new Date(`${value}T00:00:00Z`).toISOString().slice(0, 10) === value;
  return valid(start) && valid(end) && start <= end;
}

export function savingsFirstWeekday(hass: HomeAssistant | undefined): string {
  const weekdays = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
  const configured = hass?.locale?.first_weekday;
  if (configured && configured !== "language") {
    const shortened = configured.slice(0, 3);
    if (weekdays.includes(shortened)) return shortened;
  }
  if (configured === "language") {
    const locale = new Intl.Locale(
      hass?.locale?.language ?? hass?.language ?? "en",
    ) as Intl.Locale & {
      weekInfo?: { firstDay: number };
      getWeekInfo?: () => { firstDay: number };
    };
    const first = locale.getWeekInfo?.().firstDay ?? locale.weekInfo?.firstDay;
    if (first !== undefined) return weekdays[first % 7];
  }
  return "mon";
}

export function useSavingsStatistics(
  getHass: () => HomeAssistant | undefined,
  getEntryId: () => string | undefined,
  getEntityId: () => string | undefined,
) {
  const data = shallowRef<SavingsStatistics | null>(null);
  const loading = ref(false);
  const error = ref<"unavailable" | "failed" | "invalid" | null>(null);
  let dates: { start_date: string; end_date: string } | undefined;
  let generation = 0;
  let disposed = false;

  async function refresh(): Promise<void> {
    const current = ++generation;
    const hass = getHass();
    const entryId = getEntryId();
    data.value = null;
    error.value = null;
    loading.value = false;
    if (!entryId || !getEntityId()) return;
    if (!hass?.callWS || !hass.connection?.connected) {
      error.value = "unavailable";
      return;
    }
    loading.value = true;
    try {
      const result = await hass.callWS<SavingsStatistics>({
        type: "sax_power/dashboard/statistics",
        entry_id: entryId,
        first_weekday: savingsFirstWeekday(hass),
        ...dates,
      });
      if (!disposed && current === generation) data.value = result;
    } catch {
      if (!disposed && current === generation) error.value = "failed";
    } finally {
      if (!disposed && current === generation) loading.value = false;
    }
  }

  function select(start: string, end: string): void {
    if (!validSavingsDates(start, end)) {
      error.value = "invalid";
      return;
    }
    dates = { start_date: start, end_date: end };
    void refresh();
  }

  watch(
    [
      () => getHass()?.connection,
      getEntryId,
      getEntityId,
      () => savingsFirstWeekday(getHass()),
      () => getHass()?.config?.time_zone,
      () => Boolean(getHass()?.callWS),
    ],
    ([connection, entryId], previous, cleanup) => {
      if (entryId !== previous?.[1]) dates = undefined;
      let closed = false;
      let unsubscribe: Unsubscribe | undefined;
      let subscription = 0;
      const release = (unsub: Unsubscribe) => {
        try {
          void Promise.resolve(unsub()).catch(() => {});
        } catch {
          /* The socket may already be closed. */
        }
      };
      const disconnect = () => {
        ++generation;
        ++subscription;
        if (unsubscribe) release(unsubscribe);
        unsubscribe = undefined;
        data.value = null;
        loading.value = false;
        error.value = getEntityId() ? "unavailable" : null;
      };
      const connect = () => {
        if (closed) return;
        const current = ++subscription;
        if (unsubscribe) release(unsubscribe);
        unsubscribe = undefined;
        void refresh();
        if (!connection?.connected || !getEntityId()) return;
        // REQ-VUE-SAVINGS: refresh only when Recorder has produced new statistics.
        void connection
          .subscribeMessage(
            () => {
              if (!closed && current === subscription) void refresh();
            },
            {
              type: "subscribe_events",
              event_type: "recorder_5min_statistics_generated",
            },
            { resubscribe: false },
          )
          .then((unsub) => {
            if (closed || current !== subscription) release(unsub);
            else unsubscribe = unsub;
          })
          .catch(() => {
            // Manual refresh stays available if the event subscription is denied.
          });
      };
      connection?.addEventListener("ready", connect);
      connection?.addEventListener("disconnected", disconnect);
      connection?.addEventListener("reconnect-error", disconnect);
      connect();
      cleanup(() => {
        closed = true;
        disconnect();
        connection?.removeEventListener("ready", connect);
        connection?.removeEventListener("disconnected", disconnect);
        connection?.removeEventListener("reconnect-error", disconnect);
      });
    },
    { immediate: true },
  );
  onScopeDispose(() => {
    disposed = true;
    ++generation;
  });
  return { data, loading, error, refresh, select };
}
