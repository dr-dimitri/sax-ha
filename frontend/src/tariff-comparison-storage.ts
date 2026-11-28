import { computed, onScopeDispose, ref, watch } from "vue";
import type {
  ComparisonTariffInput,
  ComparisonTariffWindowInput,
} from "./tariff-comparison";
import type { HomeAssistant } from "./types";

export const MAX_COMPARISON_TARIFFS = 4;
const SAVE_DELAY_MS = 200;
const WS_COMMAND = "sax_power/dashboard/tariff_comparison";

export type SavedComparisonTariff = ComparisonTariffInput & {
  name: string;
  number: number;
};

export interface SavedComparison {
  annualConsumption: string;
  tariffs: SavedComparisonTariff[];
}

type Blocked = "loadError" | "saveError" | "conflict";
type Phase = "ready" | "loading" | "pending" | "saving" | "saved" | Blocked;
type Restore = "initial" | "keepDraft" | "stored";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isWindow(value: unknown): value is ComparisonTariffWindowInput {
  return (
    isRecord(value) &&
    typeof value.start === "string" &&
    typeof value.end === "string" &&
    typeof value.price === "string" &&
    typeof value.share === "string"
  );
}

function isTariff(value: unknown): value is SavedComparisonTariff {
  return (
    isRecord(value) &&
    typeof value.name === "string" &&
    typeof value.number === "number" &&
    Number.isSafeInteger(value.number) &&
    value.number > 0 &&
    (value.type === "fixed" || value.type === "time-of-use") &&
    (value.baseFeePeriod === "monthly" || value.baseFeePeriod === "yearly") &&
    typeof value.price === "string" &&
    typeof value.baseFee === "string" &&
    typeof value.bonus === "string" &&
    Array.isArray(value.windows) &&
    value.windows.every(isWindow)
  );
}

function readSnapshot(saved: unknown): SavedComparison & { revision: string } {
  if (
    !isRecord(saved) ||
    typeof saved.revision !== "string" ||
    typeof saved.annual_consumption !== "string" ||
    !Array.isArray(saved.tariffs) ||
    !saved.tariffs.every(isTariff)
  ) {
    throw new Error("Invalid tariff comparison response");
  }
  return {
    revision: saved.revision,
    annualConsumption: saved.annual_consumption,
    tariffs: saved.tariffs.slice(0, MAX_COMPARISON_TARIFFS),
  };
}

export function useTariffComparisonStorage(
  getHass: () => HomeAssistant | undefined,
  entryId: string | undefined,
  readDraft: () => SavedComparison,
  restoreDraft: (saved: SavedComparison) => void,
) {
  const configured = computed(() => Boolean(entryId && getHass()?.callWS));
  const socketOnline = ref<boolean>();
  const online = computed(
    () =>
      configured.value &&
      socketOnline.value !== false &&
      getHass()?.connected !== false,
  );
  const phase = ref<Phase>("ready");
  const status = computed(() =>
    !configured.value ? "local" : online.value ? phase.value : "offline",
  );
  let revision: string | undefined;
  let blocked: Blocked | undefined;
  let edit = 0;
  let savedEdit = 0;
  let restoring = false;
  let inFlight = false;
  let disposed = false;
  let timer: ReturnType<typeof setTimeout> | undefined;

  function clearTimer(): void {
    clearTimeout(timer);
    timer = undefined;
  }

  function settle(): void {
    if (!online.value || inFlight || disposed) return;
    if (blocked) {
      phase.value = blocked;
    } else if (revision === undefined) {
      void load("initial");
    } else if (edit !== savedEdit) {
      phase.value = "pending";
      timer = setTimeout(() => void save(), SAVE_DELAY_MS);
    } else if (phase.value !== "saved") {
      phase.value = "ready";
    }
  }

  async function load(mode: Restore): Promise<void> {
    clearTimer();
    const editAtStart = edit;
    inFlight = true;
    phase.value = "loading";
    try {
      const snapshot = readSnapshot(
        await getHass()!.callWS!({
          type: `${WS_COMMAND}/get`,
          entry_id: entryId,
        }),
      );
      if (disposed) return;
      revision = snapshot.revision;
      blocked = undefined;
      const applyStored =
        mode === "stored"
          ? edit === editAtStart
          : mode === "initial" && edit === savedEdit;
      if (applyStored) {
        restoring = true;
        try {
          restoreDraft(snapshot);
          savedEdit = edit;
        } finally {
          restoring = false;
        }
      } else if (
        mode === "stored" ||
        (mode === "initial" &&
          (snapshot.annualConsumption || snapshot.tariffs.length))
      ) {
        blocked = "conflict";
      }
    } catch {
      if (online.value && !blocked) blocked = "loadError";
    } finally {
      inFlight = false;
      settle();
    }
  }

  async function save(): Promise<void> {
    clearTimer();
    if (!online.value || disposed) return;
    const savedAt = edit;
    const draft = readDraft();
    inFlight = true;
    phase.value = "saving";
    try {
      const snapshot = readSnapshot(
        await getHass()!.callWS!({
          type: `${WS_COMMAND}/save`,
          entry_id: entryId,
          revision,
          annual_consumption: draft.annualConsumption,
          tariffs: draft.tariffs,
        }),
      );
      if (disposed) return;
      revision = snapshot.revision;
      savedEdit = savedAt;
      phase.value = "saved";
    } catch (error) {
      if (isRecord(error) && error.code === "conflict") blocked = "conflict";
      else if (online.value) blocked = "saveError";
    } finally {
      inFlight = false;
      settle();
    }
  }

  function changed(): void {
    if (restoring) return;
    edit++;
    clearTimer();
    settle();
  }

  function retry(): void {
    if (!online.value || inFlight) return;
    if (blocked === "conflict") {
      void load("keepDraft");
    } else {
      blocked = undefined;
      settle();
    }
  }

  function acceptStored(): void {
    if (online.value && !inFlight) void load("stored");
  }

  watch(
    () => getHass()?.connection,
    (connection, _, cleanup) => {
      socketOnline.value = connection?.connected;
      if (!connection) return;
      const ready = () => {
        socketOnline.value = true;
      };
      const disconnected = () => {
        socketOnline.value = false;
      };
      connection.addEventListener("ready", ready);
      connection.addEventListener("disconnected", disconnected);
      cleanup(() => {
        connection.removeEventListener("ready", ready);
        connection.removeEventListener("disconnected", disconnected);
      });
    },
    { immediate: true },
  );

  watch(
    online,
    (available) => {
      clearTimer();
      if (available) {
        if (blocked !== "conflict") blocked = undefined;
        settle();
      }
    },
    { immediate: true },
  );

  onScopeDispose(() => {
    // Leaving the panel should still submit edits waiting for the debounce.
    if (timer !== undefined) void save();
    disposed = true;
    clearTimer();
  });

  return { status, changed, retry, acceptStored };
}
