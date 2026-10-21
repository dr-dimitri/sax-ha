import { computed, ref, watch } from "vue";
import type { SaxDashboard } from "./ha";
import { normalizeTime, timeSeconds } from "./time";
import type { ChargingMethod } from "./types";

export function useFixedTimeCharging(dashboard: SaxDashboard | undefined) {
  function displayStart(value: string | null | undefined): string {
    return value && /^\d{2}:\d{2}:00$/.test(value)
      ? value.slice(0, 5)
      : (value ?? "02:00");
  }
  const confirmed = computed(
    () => dashboard?.tariff.value?.fixed_time_charging,
  );
  const active = computed(() => confirmed.value?.enabled === true);
  const selected = ref(active.value);
  const start = ref(displayStart(confirmed.value?.start));
  const edited = ref(false);
  const pending = ref(false);
  const error = ref<"invalid" | "failed" | "conflict" | null>(null);
  const canConfigure = computed(
    () =>
      dashboard?.ready.value === true &&
      dashboard.connected.value === true &&
      dashboard.tariff.value?.can_configure === true,
  );
  watch(
    confirmed,
    (value) => {
      if (!edited.value) {
        selected.value = value?.enabled === true;
        start.value = displayStart(value?.start);
      }
    },
    { immediate: true },
  );
  function reset(): boolean {
    if (pending.value) return false;
    edited.value = false;
    selected.value = active.value;
    start.value = displayStart(confirmed.value?.start);
    error.value = null;
    return true;
  }
  function choose(): void {
    if (pending.value || !canConfigure.value) return;
    selected.value = true;
    edited.value = true;
    error.value = null;
  }
  function edit(value: string): void {
    start.value = value;
    edited.value = true;
    error.value = null;
  }
  function validate(value = start.value): boolean {
    if (!selected.value) return true;
    start.value = normalizeTime(value);
    if (timeSeconds(start.value) === null) {
      error.value = "invalid";
      return false;
    }
    error.value = null;
    return true;
  }
  async function configure(
    method?: ChargingMethod,
    settings?: Record<string, number>,
  ): Promise<boolean> {
    const profile = dashboard?.tariff.value;
    if (pending.value || !canConfigure.value || !dashboard || !profile)
      return false;
    pending.value = true;
    error.value = null;
    try {
      await dashboard.configureTariff({
        revision: profile.revision,
        tariff_type: profile.tariff_type as "time_of_use" | "dynamic",
        ...(settings && Object.keys(settings).length
          ? { charging_settings: settings }
          : {}),
        ...(method
          ? { charging_method: method }
          : { fixed_time_charging: { enabled: true, start: start.value } }),
      });
      edited.value = false;
      selected.value = active.value;
      start.value = displayStart(confirmed.value?.start);
      return true;
    } catch (cause) {
      error.value =
        (cause as { code?: string })?.code === "conflict"
          ? "conflict"
          : "failed";
      if (error.value === "conflict") {
        try {
          await dashboard.loadTariff();
        } catch {
          /* Keep the failed draft visible. */
        }
      }
      return false;
    } finally {
      pending.value = false;
    }
  }
  async function submit(settings?: Record<string, number>): Promise<boolean> {
    if (!selected.value) return true;
    if (!validate()) return false;
    if (
      (!settings || !Object.keys(settings).length) &&
      active.value &&
      timeSeconds(start.value) === timeSeconds(confirmed.value?.start ?? "")
    ) {
      edited.value = false;
      return true;
    }
    return configure(undefined, settings);
  }
  async function leave(
    method: ChargingMethod,
    apply: () => Promise<unknown>,
  ): Promise<void> {
    if (pending.value) return;
    error.value = null;
    if (active.value) await configure(method);
    else {
      selected.value = false;
      edited.value = false;
      await apply();
    }
  }
  return {
    active,
    selected,
    start,
    pending,
    error,
    canConfigure,
    confirmed,
    displayStart,
    reset,
    choose,
    edit,
    validate,
    submit,
    leave,
  };
}
