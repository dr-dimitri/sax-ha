import { effectScope } from "vue";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  MAX_COMPARISON_TARIFFS,
  useTariffComparisonStorage,
  type SavedComparisonTariff,
} from "../src/tariff-comparison-storage";
import type { HomeAssistant } from "../src/types";

const tariff: SavedComparisonTariff = {
  name: "Entwurf",
  number: 3,
  type: "time-of-use",
  price: "31,25",
  baseFee: "",
  baseFeePeriod: "yearly",
  bonus: "",
  windows: [{ start: "22:", end: "06:00", price: "25,5", share: "20" }],
};

const scopes: ReturnType<typeof effectScope>[] = [];

function compareWithStorage(
  callWS: (message: Readonly<Record<string, unknown>>) => Promise<unknown>,
  entryId?: string,
) {
  const hass: HomeAssistant = {
    language: "de",
    states: {},
    callWS: <T>(message: Readonly<Record<string, unknown>>) =>
      callWS(message) as Promise<T>,
  };
  const restore = vi.fn();
  const scope = effectScope();
  scopes.push(scope);
  const storage = scope.run(() =>
    useTariffComparisonStorage(
      () => hass,
      entryId,
      () => ({ annualConsumption: "2000", tariffs: [tariff] }),
      restore,
    ),
  )!;
  return { ...storage, restore, dispose: () => scope.stop() };
}

describe("tariff comparison Home Assistant storage", () => {
  afterEach(() => scopes.splice(0).forEach((scope) => scope.stop()));

  it("restores at most four tariffs, including unfinished inputs", async () => {
    const callWS = vi.fn(async () => ({
      revision: "1",
      annual_consumption: "3000,5",
      tariffs: Array(6).fill(tariff),
    }));
    const storage = compareWithStorage(callWS, "entry");
    await vi.waitFor(() => expect(storage.restore).toHaveBeenCalledOnce());
    expect(callWS).toHaveBeenCalledWith({
      type: "sax_power/dashboard/tariff_comparison/get",
      entry_id: "entry",
    });
    const [restored] = storage.restore.mock.calls[0]!;
    expect(restored.annualConsumption).toBe("3000,5");
    expect(restored.tariffs).toHaveLength(MAX_COMPARISON_TARIFFS);
    expect(restored.tariffs[0]).toEqual(tariff);
    expect(storage.status.value).toBe("ready");
    expect(callWS).toHaveBeenCalledOnce();
  });

  it("preserves edits made while a nonempty server comparison loads", async () => {
    let respond!: (snapshot: unknown) => void;
    const callWS = vi.fn(
      () =>
        new Promise((resolve) => {
          respond = resolve;
        }),
    );
    const storage = compareWithStorage(callWS, "entry");
    storage.changed();
    respond({ revision: "1", annual_consumption: "3000", tariffs: [tariff] });
    await vi.waitFor(() => expect(storage.status.value).toBe("conflict"));
    expect(storage.restore).not.toHaveBeenCalled();
    expect(callWS).toHaveBeenCalledOnce();
  });

  it("submits a scheduled change immediately when leaving the panel", async () => {
    const callWS = vi.fn(async () => ({
      revision: "1",
      annual_consumption: "",
      tariffs: [],
    }));
    const storage = compareWithStorage(callWS, "entry");
    await vi.waitFor(() => expect(storage.status.value).toBe("ready"));
    storage.changed();
    expect(callWS).toHaveBeenCalledOnce();

    storage.dispose();
    expect(callWS).toHaveBeenCalledTimes(2);
    expect(callWS).toHaveBeenLastCalledWith({
      type: "sax_power/dashboard/tariff_comparison/save",
      entry_id: "entry",
      revision: "1",
      annual_consumption: "2000",
      tariffs: [tariff],
    });
  });

  it("keeps the input available when the device responds with invalid data", async () => {
    const callWS = vi.fn(async () => ({ revision: "1", tariffs: [null] }));
    const storage = compareWithStorage(callWS, "entry");
    await vi.waitFor(() => expect(storage.status.value).toBe("loadError"));
    expect(storage.restore).not.toHaveBeenCalled();
  });

  it("does not use transport in a standalone calculator", () => {
    const callWS = vi.fn();
    const storage = compareWithStorage(callWS);
    storage.changed();
    expect(storage.status.value).toBe("local");
    expect(callWS).not.toHaveBeenCalled();
  });
});
