import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import SavingsView from "../src/views/SavingsView.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "../src/ha";
import {
  finiteValue,
  savingsFirstWeekday,
  validSavingsDates,
  type SavingsStatistics,
} from "../src/savings";
import type {
  ConnectionEvent,
  DashboardEntityMetadata,
  DashboardMetadata,
  HassConnection,
  HassEntity,
  HomeAssistant,
} from "../src/types";

const apps: App[] = [];
const keys = [
  "economics_investment_configured",
  "economics_amortization_progress",
  "economics_remaining_to_payback",
  "economics_roi",
  "economics_net_savings",
  "economics_status",
  "economics_current_import_price",
];
const values: Record<string, string> = {
  economics_investment_configured: "on",
  economics_amortization_progress: "25.345",
  economics_remaining_to_payback: "750.005",
  economics_roi: "250.10",
  economics_net_savings: "-12.345",
  economics_status: "active",
  economics_current_import_price: "0.25678",
};
const attrs: Record<string, Record<string, unknown>> = {
  economics_roi: {
    prior_result_eur: 262.445,
    prior_result_eur_formatted: "262.44",
  },
  economics_status: { economics_started_at: "2026-03-28T23:00:00Z" },
  economics_current_import_price: {
    tariff_type: "time_of_use",
    windows: [
      { start: "06:00:00", end: "12:00:00", price_eur_kwh: 0.25678 },
      { start: "12:00:00", end: "18:00:00", price_eur_kwh: -0.015 },
    ],
    active_window: { start: "06:00:00", end: "12:00:00" },
    base_price_eur_kwh: 0.35,
    feed_in_price_eur_kwh: 0.08,
    next_price_change_at: "2026-03-29T10:00:00Z",
    unavailable_reason: null,
  },
};

function result(
  change: number | null = -2.125,
  start = "2026-03-29",
  end = start,
): SavingsStatistics {
  const period = { start: "2026-03-28T23:00:00Z", end: null, change };
  return {
    entity_id: "sensor.renamed_economics_net_savings",
    time_zone: "Europe/Berlin",
    today: "2026-03-29",
    status: "ok",
    periods: {
      day: { ...period },
      week: { ...period },
      month: { ...period },
      year: { ...period },
    },
    selected: {
      start_date: start,
      end_date: end,
      start: "2026-03-28T23:00:00Z",
      end: "2026-03-29T22:00:00Z",
      change,
      period: "hour",
      buckets:
        change === null
          ? []
          : [
              {
                start: "2026-03-29T00:00:00Z",
                end: "2026-03-29T01:00:00Z",
                change: 1.25,
              },
              {
                start: "2026-03-29T01:00:00Z",
                end: "2026-03-29T02:00:00Z",
                change: -3.375,
              },
            ],
    },
  };
}
async function flush() {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}

async function mount(
  options: {
    omit?: string[];
    status?: string;
    configured?: string;
    response?: SavingsStatistics;
    language?: string;
    defer?: boolean;
    fail?: boolean;
  } = {},
) {
  const metadata: DashboardEntityMetadata[] = keys
    .filter((key) => !options.omit?.includes(key))
    .map((key) => ({
      domain:
        key === "economics_investment_configured" ? "binary_sensor" : "sensor",
      key,
      entity_id: `${key === "economics_investment_configured" ? "binary_sensor" : "sensor"}.renamed_${key}`,
      name:
        key === "economics_remaining_to_payback"
          ? "Restbetrag"
          : key === "economics_amortization_progress"
            ? "Amortisationsfortschritt"
            : key,
      states: {},
      can_control: false,
    }));
  const states: Record<string, HassEntity> = Object.fromEntries(
    metadata.map((item) => [
      item.entity_id,
      {
        entity_id: item.entity_id,
        state:
          item.key === "economics_status"
            ? (options.status ?? values[item.key])
            : item.key === "economics_investment_configured"
              ? (options.configured ?? values[item.key])
              : values[item.key],
        attributes: attrs[item.key] ?? {},
      },
    ]),
  );
  let emitMetadata: (value: DashboardMetadata) => void = () => {};
  let emitRecorder: () => void = () => {};
  const events = new Map<ConnectionEvent, Set<() => void>>();
  const unsubRecorder = vi.fn();
  const connection: HassConnection = {
    connected: true,
    async subscribeMessage<T>(
      callback: (data: T) => void,
      message: Readonly<Record<string, unknown>>,
    ) {
      if (message.type === "subscribe_events") {
        emitRecorder = () => callback({} as T);
        return unsubRecorder;
      }
      emitMetadata = (value) => callback(value as T);
      emitMetadata({ entities: metadata });
      return () => {};
    },
    addEventListener(event, listener) {
      if (!events.has(event)) events.set(event, new Set());
      events.get(event)!.add(listener);
    },
    removeEventListener(event, listener) {
      events.get(event)?.delete(listener);
    },
  };
  const pending: { resolve(value: SavingsStatistics): void; reject(): void }[] =
    [];
  const callWS = vi.fn(async (_message: Readonly<Record<string, unknown>>) => {
    if (options.fail) throw new Error("Recorder unavailable");
    if (!options.defer) return options.response ?? result();
    return new Promise<SavingsStatistics>((resolve, reject) =>
      pending.push({ resolve, reject: () => reject(new Error("old failure")) }),
    );
  });
  const callService = vi.fn().mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    states,
    connection,
    callWS: <T>(message: Readonly<Record<string, unknown>>) =>
      callWS(message) as Promise<T>,
    callService,
    config: { time_zone: "Europe/Berlin" },
    locale: { time_format: "twenty_four", first_weekday: "monday" },
  });
  const entryId = shallowRef("entry-1");
  const root = document.createElement("div");
  document.body.append(root);
  const app = createApp({
    setup() {
      provide(
        SAX_DASHBOARD_KEY,
        useSaxDashboard(
          () => hass.value,
          () => entryId.value,
        ),
      );
      return () => h(SavingsView, { hass: hass.value, entryId: entryId.value });
    },
  });
  apps.push(app);
  app.mount(root);
  await flush();
  return {
    root,
    hass,
    app,
    entryId,
    pending,
    callWS,
    callService,
    unsubRecorder,
    async update(key: string, state: string, attributes = attrs[key] ?? {}) {
      const entityId = metadata.find((item) => item.key === key)!.entity_id;
      hass.value = {
        ...hass.value,
        states: {
          ...hass.value.states,
          [entityId]: { ...hass.value.states[entityId], state, attributes },
        },
      };
      await flush();
    },
    async metadata(omit: string[]) {
      emitMetadata({
        entities: metadata.filter((item) => !omit.includes(item.key)),
      });
      await flush();
    },
    async event(event: ConnectionEvent) {
      Object.assign(connection, { connected: event === "ready" });
      for (const callback of [...(events.get(event) ?? [])]) callback();
      await flush();
    },
    async recorder() {
      emitRecorder();
      await flush();
    },
  };
}
function submit(root: HTMLElement, start: string, end: string) {
  const fields = root.querySelectorAll<HTMLInputElement>('input[type="date"]');
  fields[0].value = start;
  fields[0].dispatchEvent(new Event("input", { bubbles: true }));
  fields[1].value = end;
  fields[1].dispatchEvent(new Event("input", { bubbles: true }));
  root
    .querySelector("form")!
    .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
}

afterEach(() => {
  for (const app of apps.splice(0)) app.unmount();
  document.body.replaceChildren();
  vi.unstubAllGlobals();
});

describe("REQ-VUE-SAVINGS: economics view", () => {
  it("shows payback, calendar periods and tariffs with signed full-precision values", async () => {
    const { root, callWS, callService } = await mount();
    expect(
      [...root.querySelectorAll("h2")].map((element) => element.textContent),
    ).toEqual([
      "Amortisation",
      "Heute bisher",
      "Diese Woche bisher",
      "Dieser Monat bisher",
      "Dieses Jahr bisher",
      "Tarifplan (tageszeitabhängig)",
      "Freier Zeitraum",
    ]);
    expect(root.textContent).toContain("750,01 €");
    expect(root.textContent).toContain("262,45 €");
    expect(root.textContent).toContain("-12,35 €");
    expect(root.textContent).toContain("29.03.2026, 00:00");
    expect(
      root.querySelector('[role="meter"]')?.getAttribute("aria-valuenow"),
    ).toBe("25.345");
    expect(
      root.querySelector(".savings-explanation")?.hasAttribute("open"),
    ).toBe(false);
    expect(root.querySelector(".savings-status")).toBeNull();
    expect(root.querySelectorAll(".savings-chart__bar--negative")).toHaveLength(
      1,
    );
    expect(root.textContent).toContain("-2,13 €");
    expect(callWS).toHaveBeenCalledExactlyOnceWith({
      type: "sax_power/dashboard/statistics",
      entry_id: "entry-1",
      first_weekday: "mon",
    });
    expect(callService).not.toHaveBeenCalled();
  });
  it("shows investment configuration guidance without fabricating a progress value", async () => {
    const { root } = await mount({ configured: "off" });
    expect(root.textContent).toContain("Investitionskosten");
    expect(root.querySelector('[role="meter"]')).toBeNull();
    expect(root.querySelector(".savings-rows")).toBeNull();
    expect(root.querySelector(".savings-periods")).not.toBeNull();
  });
  it.each([
    "disabled",
    "price_unavailable",
    "origin_unavailable",
    "partial_price_coverage",
    "storage_error",
    "unknown",
    "unavailable",
    "unexpected",
  ])("shows exactly one economics status notice for %s", async (status) => {
    const { root } = await mount({ status });
    expect(root.querySelectorAll(".savings-status")).toHaveLength(1);
    const expected: Record<string, string> = {
      disabled: "deaktiviert",
      price_unavailable: "Strompreis",
      origin_unavailable: "Herkunft",
      partial_price_coverage: "Teil der Energie",
      storage_error: "Korrupt-Backup",
    };
    expect(root.querySelector(".savings-status")?.textContent).toContain(
      expected[status] ?? "momentan nicht verfügbar",
    );
  });
  it("omits missing optional cards and statistics instead of empty containers", async () => {
    const { root, callWS } = await mount({ omit: keys });
    expect(root.querySelectorAll("section, form, article, dl")).toHaveLength(0);
    expect(root.querySelector(".savings-status")?.textContent).toContain(
      "momentan nicht verfügbar",
    );
    expect(callWS).not.toHaveBeenCalled();
  });
  it("omits all net-savings details and queries when that entity is absent", async () => {
    const { root, callWS } = await mount({
      omit: [
        "economics_net_savings",
        "economics_roi",
        "economics_remaining_to_payback",
        "economics_status",
      ],
    });
    expect(root.querySelectorAll(".savings-rows > div")).toHaveLength(0);
    expect(root.querySelectorAll("article, form")).toHaveLength(0);
    expect(callWS).not.toHaveBeenCalled();
  });
  it("updates TOU attributes live and never marks a missing price as an active base tariff", async () => {
    const { root, update } = await mount();
    expect(root.textContent).toContain("0,2568 EUR/kWh");
    expect(root.textContent).toContain("0,0800 EUR/kWh");
    expect(root.textContent).toContain("29.03.2026, 12:00");
    expect(root.querySelectorAll(".savings-current")).toHaveLength(1);
    await update("economics_current_import_price", "unavailable", {
      ...attrs.economics_current_import_price,
      active_window: null,
      base_price_eur_kwh: null,
      feed_in_price_eur_kwh: null,
      unavailable_reason: "missing_base_price",
    });
    expect(root.querySelectorAll(".savings-current")).toHaveLength(0);
    expect(root.textContent).toContain("missing_base_price");
    expect(root.textContent).not.toContain("0,0000 EUR/kWh");
    await update("economics_current_import_price", ".35", {
      ...attrs.economics_current_import_price,
      active_window: null,
    });
    expect(root.querySelector(".savings-current")?.textContent).toContain(
      "Grundpreis",
    );
    await update("economics_current_import_price", ".35", {
      tariff_type: "fixed",
    });
    expect(root.textContent).not.toContain("Tarifplan");
  });
  it("shows an honest empty Recorder result and keeps zero distinct from missing", async () => {
    const { root } = await mount({ response: result(null) });
    expect(root.querySelector("svg")).toBeNull();
    expect(root.textContent).toContain("keine Recorder-Daten");
    expect(root.textContent).not.toContain("0,00 €");
    const zero = await mount({ response: result(0) });
    expect(zero.root.textContent).toContain("0,00 €");
  });

  it("preserves missing hours on the actual 23-hour DST time axis", async () => {
    const response = result();
    response.selected.buckets[1] = {
      start: "2026-03-29T02:00:00Z",
      end: "2026-03-29T03:00:00Z",
      change: -3.375,
    };
    const { root } = await mount({ response });
    const bars = [...root.querySelectorAll(".savings-chart__bar")];
    expect(
      Number(bars[1].getAttribute("x")) - Number(bars[0].getAttribute("x")),
    ).toBeCloseTo((2 * 640) / 23);
    expect(Number(bars[0].getAttribute("width"))).toBeCloseTo(640 / 23 - 4);
    expect(root.querySelectorAll(".savings-chart__bar")).toHaveLength(2);
  });

  it("keeps chart labels at their CSS size on mobile and releases its resize observer", async () => {
    let resized: ResizeObserverCallback = () => {};
    const disconnect = vi.fn();
    vi.stubGlobal(
      "ResizeObserver",
      class {
        constructor(callback: ResizeObserverCallback) {
          resized = callback;
        }
        observe() {}
        disconnect = disconnect;
      },
    );
    const fixture = await mount();
    resized(
      [{ contentRect: { width: 280 } } as ResizeObserverEntry],
      {} as ResizeObserver,
    );
    await flush();
    const svg = fixture.root.querySelector(".savings-chart")!;
    expect(svg.getAttribute("viewBox")).toBe("0 0 280 240");
    const end = Number(svg.querySelector("line")?.getAttribute("x2"));
    expect(end).toBeLessThan(280);
    for (const bar of svg.querySelectorAll("rect")) {
      expect(
        Number(bar.getAttribute("x")) + Number(bar.getAttribute("width")),
      ).toBeLessThan(end);
    }
    resized(
      [{ contentRect: { width: 640 } } as ResizeObserverEntry],
      {} as ResizeObserver,
    );
    await flush();
    expect(svg.getAttribute("viewBox")).toBe("0 0 640 240");
    fixture.app.unmount();
    expect(disconnect).toHaveBeenCalledOnce();
  });

  it("keeps a newer five-minute total distinct from hourly bars and their empty state", async () => {
    const response = result(-5);
    response.selected.buckets[0].change = -10;
    response.selected.buckets[1].change = 2;
    const { root } = await mount({ response });
    expect(root.textContent).toContain("-5,00 €");
    expect(root.querySelector(".savings-chart-table")?.textContent).toContain(
      "-10,00 €",
    );
    expect(root.textContent).toContain("neuere Fünf-Minuten-Daten");
    const onlyTail = result(3);
    onlyTail.selected.buckets = [];
    const fresh = await mount({ response: onlyTail });
    expect(fresh.root.textContent).toContain("3,00 €");
    expect(fresh.root.querySelector(".savings-empty")?.textContent).toBe(
      "Für das Diagramm liegen noch keine zusammengefassten Recorder-Daten vor.",
    );
  });

  it.each(["", "NaN", "Infinity", "not-a-price"])(
    "does not mark the base tariff active for an invalid price %s",
    async (price) => {
      const { root, update } = await mount();
      await update("economics_current_import_price", price, {
        ...attrs.economics_current_import_price,
        active_window: null,
      });
      expect(root.querySelector(".savings-current")).toBeNull();
      expect(root.textContent).toContain("Derzeit gilt kein Preis");
    },
  );
  it("keeps date drafts from changing values and ignores late results for an old selection", async () => {
    const { root, pending, callWS } = await mount({ defer: true });
    pending[0].resolve(result());
    await flush();
    const input = root.querySelector<HTMLInputElement>('input[type="date"]')!;
    input.value = "2026-03-01";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await flush();
    expect(callWS).toHaveBeenCalledTimes(1);
    submit(root, "2026-03-01", "2026-03-10");
    await flush();
    expect(root.querySelector("svg")).toBeNull();
    submit(root, "2026-03-11", "2026-03-29");
    await flush();
    pending[2].resolve(result(-8, "2026-03-11", "2026-03-29"));
    await flush();
    pending[1].resolve(result(999, "2026-03-01", "2026-03-10"));
    await flush();
    expect(root.textContent).toContain("-8,00 €");
    expect(root.textContent).not.toContain("999,00 €");
    expect(
      root.querySelector(".savings-selected-dates")?.textContent,
    ).toContain("11.03.2026");
    expect(callWS).toHaveBeenLastCalledWith({
      type: "sax_power/dashboard/statistics",
      entry_id: "entry-1",
      first_weekday: "mon",
      start_date: "2026-03-11",
      end_date: "2026-03-29",
    });
  });
  it("handles statistic errors and invalid ranges without issuing a new query", async () => {
    const { root, callWS } = await mount({ fail: true });
    expect(root.querySelector('[role="alert"]')?.textContent).toContain(
      "konnte nicht geladen",
    );
    submit(root, "2026-04-01", "2026-03-01");
    await flush();
    expect(callWS).toHaveBeenCalledTimes(1);
    expect(root.querySelector('[role="alert"]')?.textContent).toContain(
      "Ende darf nicht",
    );
  });

  it("keeps the latest selection after a stale Recorder request fails", async () => {
    const { root, pending } = await mount({ defer: true });
    submit(root, "2026-02-01", "2026-02-28");
    await flush();
    pending[1].resolve(result(4.25, "2026-02-01", "2026-02-28"));
    await flush();
    pending[0].reject();
    await flush();
    expect(root.textContent).toContain("4,25 €");
    expect(root.querySelector('[role="alert"]')).toBeNull();
  });

  it("shows a Recorder availability error without using the live ledger as a substitute", async () => {
    const response = result(null);
    response.status = "recorder_unavailable";
    const { root } = await mount({ response });
    expect(root.querySelector('[role="alert"]')?.textContent).toContain(
      "Recorder-Statistik ist derzeit nicht verfügbar",
    );
    expect(root.querySelector("svg")).toBeNull();
    expect(root.querySelector(".savings-periods")?.textContent).not.toContain(
      "-12,35",
    );
  });

  it("keeps missing monetary and progress states unavailable", async () => {
    const { root, update } = await mount();
    await update("economics_amortization_progress", "unavailable");
    await update("economics_remaining_to_payback", "unknown");
    await update("economics_roi", "unavailable");
    await update("economics_net_savings", "unavailable");
    expect(root.querySelector('[role="meter"]')).toBeNull();
    expect(
      [...root.querySelectorAll(".savings-rows dd")]
        .slice(0, 3)
        .map((element) => element.textContent),
    ).toEqual(["Nicht verfügbar", "Nicht verfügbar", "Nicht verfügbar"]);
    expect(root.querySelector(".savings-rows")?.textContent).not.toContain(
      "0,00 €",
    );
  });

  it("invalidates a pending response at unmount", async () => {
    const fixture = await mount({ defer: true });
    fixture.app.unmount();
    fixture.pending[0].resolve(result(999));
    await flush();
    expect(fixture.root.textContent).toBe("");
  });

  it("advances an untouched default date selection with the local Recorder day", async () => {
    const fixture = await mount();
    fixture.callWS.mockResolvedValueOnce(result(4, "2026-03-30"));
    await fixture.recorder();
    expect(
      [
        ...fixture.root.querySelectorAll<HTMLInputElement>(
          'input[type="date"]',
        ),
      ].map((field) => field.value),
    ).toEqual(["2026-03-30", "2026-03-30"]);
  });
  it("refreshes from native Recorder events, reconnects once resolved and cleans up", async () => {
    const fixture = await mount();
    await fixture.recorder();
    expect(fixture.callWS).toHaveBeenCalledTimes(2);
    await fixture.event("disconnected");
    expect(fixture.root.querySelector("svg")).toBeNull();
    await fixture.event("ready");
    expect(fixture.callWS.mock.calls.length).toBeGreaterThanOrEqual(3);
    fixture.app.unmount();
    const count = fixture.callWS.mock.calls.length;
    await fixture.recorder();
    expect(fixture.callWS).toHaveBeenCalledTimes(count);
    expect(fixture.unsubRecorder).toHaveBeenCalled();
  });
  it("drops in-flight values when a registry update removes access to the savings entity", async () => {
    const fixture = await mount({ defer: true });
    await fixture.metadata(["economics_net_savings"]);
    fixture.pending[0].resolve(result(999));
    await flush();
    expect(fixture.root.querySelector("svg")).toBeNull();
    expect(fixture.root.textContent).not.toContain("999,00 €");
  });
  it("formats English copy and respects HA timezone and decimal preferences", async () => {
    const { root, hass } = await mount({ language: "en-GB" });
    expect(root.textContent).toContain("Today so far");
    expect(root.textContent).toContain("0.2568 EUR/kWh");
    expect(root.textContent).toContain("29 Mar 2026, 12:00");
    hass.value = {
      ...hass.value,
      locale: { ...hass.value.locale, number_format: "decimal_comma" },
    };
    await flush();
    expect(root.textContent).toContain("0,2568 EUR/kWh");
  });
});

describe("REQ-VUE-SAVINGS: dates and values", () => {
  it.each([null, undefined, "", "  ", "NaN", "Infinity", true, {}, []])(
    "does not invent numeric data for %s",
    (value) => expect(finiteValue(value)).toBeNull(),
  );
  it("validates actual calendar dates including leap years", () => {
    expect(validSavingsDates("2024-02-29", "2024-03-31")).toBe(true);
    expect(validSavingsDates("2026-02-29", "2026-03-31")).toBe(false);
    expect(validSavingsDates("2026-03-29", "2026-03-29")).toBe(true);
    expect(validSavingsDates("0000-01-01", "2026-03-29")).toBe(false);
  });
  it.each([
    ["de-DE", "mon"],
    ["en-US", "sun"],
    ["en-GB", "mon"],
  ])("uses the same local week start for %s", (language, expected) => {
    expect(
      savingsFirstWeekday({
        language,
        states: {},
        locale: { language, first_weekday: "language" },
      }),
    ).toBe(expected);
  });
  it("respects explicitly selected weekday over language defaults", () =>
    expect(
      savingsFirstWeekday({
        language: "en-US",
        states: {},
        locale: { first_weekday: "saturday" },
      }),
    ).toBe("sat"));
});
