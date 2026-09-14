import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import { chargingSample } from "../src/charging-preview-data";
import TariffPlan from "../src/components/TariffPlan.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "../src/ha";
import SavingsView from "../src/views/SavingsView.vue";
import type {
  DashboardEntityMetadata,
  DashboardMetadata,
  HassConnection,
  HomeAssistant,
  TariffProfile,
} from "../src/types";

const apps: App[] = [];
const priceId = "sensor.my_renamed_import_price";
type TariffWindow = {
  start: string;
  end: string;
  price_eur_kwh: number | null;
  low_tariff?: boolean;
};
const twoWindows: TariffWindow[] = [
  { start: "06:00:00", end: "12:00:00", price_eur_kwh: 0.25678 },
  { start: "12:00:00", end: "18:00:00", price_eur_kwh: -0.015 },
];
const eightWindows: TariffWindow[] = Array.from({ length: 8 }, (_, index) => ({
  start: `${String(index * 3).padStart(2, "0")}:00:00`,
  end: `${String(((index + 1) * 3) % 24).padStart(2, "0")}:00:00`,
  price_eur_kwh: index === 1 ? -0.015 : 0.2 + index / 100,
}));
function tariffAttributes(windows = twoWindows): Record<string, unknown> {
  return {
    tariff_type: "time_of_use",
    windows: windows.map((window, index) => ({
      ...window,
      low_tariff: window.low_tariff ?? index === 1,
    })),
    active_window: { start: windows[1].start, end: windows[1].end },
    base_price_eur_kwh: 0.35,
    feed_in_price_eur_kwh: 0.08,
    next_price_change_at: "2026-03-29T16:00:00Z",
    unavailable_reason: null,
    low_tariff_price_eur_kwh: -0.015,
    base_price_is_low_tariff: false,
    low_tariff_active: true,
    low_tariff_valid_until: "2026-03-29T16:00:00Z",
  };
}
async function flush() {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}
async function mount(
  options: {
    windows?: TariffWindow[];
    investment?: "off" | "missing";
    language?: string;
    tariffType?: string;
    profile?: Partial<TariffProfile>;
    compact?: boolean;
  } = {},
) {
  const sample = chargingSample(options.language);
  const metadata: DashboardEntityMetadata[] = [
    ...sample.metadata,
    {
      domain: "sensor",
      key: "economics_current_import_price",
      entity_id: priceId,
      name: "Bezugspreis",
      states: {},
      can_control: false,
    },
  ];
  if (options.investment !== "missing") {
    metadata.push({
      domain: "binary_sensor",
      key: "economics_investment_configured",
      entity_id: "binary_sensor.investment",
      name: "Investitionskosten konfiguriert",
      states: {},
      can_control: false,
    });
    sample.states["binary_sensor.investment"] = {
      entity_id: "binary_sensor.investment",
      state: options.investment ?? "on",
      attributes: {},
    };
  }
  sample.states[priceId] = {
    entity_id: priceId,
    state: "-1.5",
    attributes: {
      ...tariffAttributes(options.windows),
      tariff_type: options.tariffType ?? "time_of_use",
    },
  };
  let emitMetadata: (data: DashboardMetadata) => void = () => {};
  const listeners = new Map<string, Set<() => void>>();
  const connection: HassConnection = {
    connected: true,
    async subscribeMessage<T>(callback: (message: T) => void) {
      emitMetadata = (data) => callback(data as T);
      emitMetadata({ entities: metadata });
      return () => {};
    },
    addEventListener(event, callback) {
      const handlers = listeners.get(event) ?? new Set();
      handlers.add(callback);
      listeners.set(event, handlers);
    },
    removeEventListener(event, callback) {
      listeners.get(event)?.delete(callback);
    },
  };
  const callService = vi.fn().mockResolvedValue(undefined);
  const initialProfile: TariffProfile = {
    tariff_type: options.tariffType ?? "time_of_use",
    base_price_ct_kwh: 35,
    feed_in_price_ct_kwh: 8,
    windows: (options.windows ?? twoWindows).map((window) => ({
      start: window.start,
      end: window.end,
      price_ct_kwh: window.price_eur_kwh! * 100,
    })),
    revision: "revision-1",
    can_edit: true,
    ...options.profile,
  };
  const callWS = vi.fn(async (request: Readonly<Record<string, unknown>>) => {
    if (request.type === "sax_power/dashboard/tariff/get")
      return initialProfile;
    if (request.type === "sax_power/dashboard/tariff/save")
      return { ...initialProfile, ...request, revision: "revision-2" };
    return undefined;
  });
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    states: sample.states,
    connection,
    callService,
    callWS: <T>(request: Readonly<Record<string, unknown>>) =>
      callWS(request) as Promise<T>,
    config: { time_zone: "Europe/Berlin" },
    locale: { time_format: "twenty_four" },
  });
  const root = document.createElement("div");
  document.body.append(root);
  const app = createApp({
    setup() {
      provide(
        SAX_DASHBOARD_KEY,
        useSaxDashboard(
          () => hass.value,
          () => "entry-1",
        ),
      );
      return () =>
        options.compact
          ? h(TariffPlan, { hass: hass.value, compact: true })
          : h("div", [
              h("div", { class: "timed-fixture" }, [
                h(TariffPlan, { hass: hass.value }),
              ]),
              h("div", { class: "savings-fixture" }, [
                h(SavingsView, { hass: hass.value, entryId: "entry-1" }),
              ]),
            ]);
    },
  });
  apps.push(app);
  app.mount(root);
  await flush();
  return {
    root,
    callService,
    callWS,
    hass,
    async disconnect(value = true) {
      Object.assign(connection, { connected: !value });
      listeners
        .get(value ? "disconnected" : "ready")
        ?.forEach((callback) => callback());
      await flush();
    },
    plans: () => [...root.querySelectorAll(".tariff-plan")],
    async update(state: string, attributes: Record<string, unknown>) {
      hass.value = {
        ...hass.value,
        states: {
          ...hass.value.states,
          [priceId]: { entity_id: priceId, state, attributes },
        },
      };
      await flush();
    },
    async metadata(visible: boolean) {
      emitMetadata({
        entities: metadata.filter(
          (item) => visible || item.entity_id !== priceId,
        ),
      });
      await flush();
    },
  };
}
function rows(plan: Element): (string | null)[][] {
  return [...plan.querySelectorAll(".tariff-plan__table tbody tr")].map((row) =>
    [...row.querySelectorAll("td")].map((cell) => cell.textContent),
  );
}
function chargingTimes(root: Element) {
  return [
    ...root.querySelectorAll<HTMLInputElement>(
      '.time-window-control input[type="time"]',
    ),
  ].map((input) => input.value);
}

afterEach(() => {
  for (const app of apps.splice(0)) app.unmount();
  document.body.replaceChildren();
  vi.useRealTimers();
});

describe("REQ-VUE-CHARGING / REQ-VUE-SAVINGS: shared tariff price windows", () => {
  it.each([
    { count: 2, windows: twoWindows },
    { count: 8, windows: eightWindows },
  ])(
    "shows $count configured windows and the same backend-selected active price in both views",
    async ({ windows }) => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date("2026-03-29T21:00:00Z"));
      const fixture = await mount({ windows });
      const plans = fixture.plans();
      expect(plans).toHaveLength(2);
      expect(rows(plans[0])).toEqual(rows(plans[1]));
      for (const plan of plans) {
        expect(plan.querySelector("h2")?.textContent).toBe("Dein Stromtarif");
        const displayed = rows(plan);
        expect(displayed).toHaveLength(windows.length + 1);
        windows.forEach((window, index) => {
          expect(displayed[index]).toContain(window.start.slice(0, 5));
          expect(displayed[index]).toContain(window.end.slice(0, 5));
        });
        expect(displayed.at(-1)).toContain("Standardpreis");
        expect(plan.textContent).toContain("35,00 ct/kWh");
        expect(plan.textContent).toContain("8,00 ct/kWh");
        expect(plan.textContent).toContain("29.03.2026, 18:00");
        const active = plan.querySelectorAll(".tariff-plan__current");
        expect(active).toHaveLength(1);
        expect(active[0].textContent).toContain(windows[1].start.slice(0, 5));
        expect(active[0].textContent).toContain("-1,50 ct/kWh");
        expect(plan.querySelectorAll("input, select, form")).toHaveLength(0);
      }
      expect(chargingTimes(fixture.root)).toEqual([]);
      expect(fixture.callService).not.toHaveBeenCalled();
      expect(fixture.callWS).not.toHaveBeenCalled();
    },
  );

  it.each(["off", "missing"] as const)(
    "keeps tariffs visible without configured investment costs (%s)",
    async (investment) => {
      const { plans, callService } = await mount({ investment });
      expect(plans()).toHaveLength(2);
      for (const plan of plans()) expect(rows(plan)).toHaveLength(3);
      expect(callService).not.toHaveBeenCalled();
    },
  );

  it("renders the backend's lowest occurring price level, including base-price gaps and adjacent equal windows", async () => {
    const fixture = await mount({ windows: eightWindows });
    await fixture.update("0.21", {
      ...tariffAttributes(eightWindows),
      base_price_eur_kwh: -0.1,
    });
    for (const plan of fixture.plans()) {
      const low = plan.querySelectorAll(".tariff-plan__low");
      expect(low).toHaveLength(1);
      expect(low[0].textContent).toContain("03:00");
      expect(rows(plan).at(-1)?.[0]).toBe("");
    }
    await fixture.update("0.35", {
      ...tariffAttributes(),
      windows: [
        { start: "22:00", end: "02:00", price_eur_kwh: 0.4, low_tariff: false },
        { start: "02:00", end: "06:00", price_eur_kwh: 0.35, low_tariff: true },
        { start: "06:00", end: "08:00", price_eur_kwh: 0.35, low_tariff: true },
      ],
      active_window: null,
      base_price_eur_kwh: 0.35,
      low_tariff_price_eur_kwh: 0.35,
      base_price_is_low_tariff: true,
      low_tariff_valid_until: "2026-03-29T20:00:00Z",
    });
    for (const plan of fixture.plans()) {
      expect(plan.querySelectorAll(".tariff-plan__low")).toHaveLength(3);
      expect(rows(plan).at(-1)?.[0]).toBe("jetzt · günstig");
      expect(
        plan.querySelector(".tariff-plan__low-status")?.textContent,
      ).toContain("29.03.2026, 22:00");
    }
    expect(fixture.callService).not.toHaveBeenCalled();
    expect(fixture.callWS).not.toHaveBeenCalled();
  });

  it.each([
    { low_tariff_price_eur_kwh: undefined },
    { low_tariff_price_eur_kwh: null },
    { low_tariff_price_eur_kwh: "NaN" },
    { low_tariff_active: undefined },
    { base_price_is_low_tariff: undefined },
    { windows: twoWindows },
    { windows: undefined },
    { windows: [null] },
    {
      windows: [
        { start: "22:00", end: "06:00", price_eur_kwh: null, low_tariff: true },
      ],
    },
    { low_tariff_valid_until: null },
    { low_tariff_valid_until: "invalid" },
    { unavailable_reason: "invalid_tariff" },
  ])(
    "never infers low tariff or charging permission from incomplete attributes: %j",
    async (attributes) => {
      const fixture = await mount();
      await fixture.update("-0.015", { ...tariffAttributes(), ...attributes });
      for (const plan of fixture.plans()) {
        expect(plan.querySelector(".tariff-plan__low")).toBeNull();
        expect(plan.querySelector(".tariff-plan__low-status")).toBeNull();
        expect(
          plan.querySelector(".tariff-plan__low-unavailable")?.textContent,
        ).toContain("SOC-Ladung bleibt gesperrt");
      }
      expect(chargingTimes(fixture.root)).toEqual([]);
      expect(fixture.callService).not.toHaveBeenCalled();
    },
  );

  it("follows backend low-tariff status without calculating local time boundaries", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-03-29T21:00:00Z"));
    const fixture = await mount();
    await fixture.update("0.35", {
      ...tariffAttributes(),
      active_window: null,
      low_tariff_active: false,
      low_tariff_valid_until: null,
    });
    for (const plan of fixture.plans()) {
      expect(plan.querySelectorAll(".tariff-plan__low")).toHaveLength(1);
      expect(
        plan.querySelector(".tariff-plan__low-status")?.textContent,
      ).toContain("Aktuell außerhalb der günstigsten Zeiten");
      expect(
        plan.querySelector(".tariff-plan__low-status")?.textContent,
      ).not.toContain("aktiv bis");
    }
    expect(fixture.callService).not.toHaveBeenCalled();
  });

  it("updates windows only for the registered time-of-use tariff", async () => {
    const fixture = await mount({ tariffType: "fixed" });
    expect(fixture.plans()).toHaveLength(0);
    expect(chargingTimes(fixture.root)).toEqual([]);
    await fixture.update("-0.015", tariffAttributes());
    expect(fixture.plans()).toHaveLength(2);
    expect(chargingTimes(fixture.root)).toEqual([]);
    await fixture.update("-0.015", tariffAttributes(eightWindows));
    for (const plan of fixture.plans()) expect(rows(plan)).toHaveLength(9);
    await fixture.metadata(false);
    expect(fixture.plans()).toHaveLength(0);
    expect(chargingTimes(fixture.root)).toEqual([]);
    await fixture.metadata(true);
    expect(fixture.plans()).toHaveLength(2);
    for (const tariffType of ["dynamic", "fixed", "disabled"]) {
      await fixture.update(".35", { tariff_type: tariffType });
      expect(fixture.plans()).toHaveLength(0);
      expect(chargingTimes(fixture.root)).toEqual([]);
    }
    await fixture.update(".35", {
      ...tariffAttributes(),
      active_window: null,
    });
    for (const plan of fixture.plans()) {
      expect(rows(plan)).toHaveLength(3);
      const active = plan.querySelectorAll(".tariff-plan__current");
      expect(active).toHaveLength(1);
      expect(active[0].textContent).toContain("Standardpreis");
    }
    expect(chargingTimes(fixture.root)).toEqual([]);
    expect(fixture.root.querySelectorAll(".time-window-control")).toHaveLength(
      0,
    );
    expect(fixture.callService).not.toHaveBeenCalled();
  });

  it("shows only the base-price row and tariff details when no price windows are configured", async () => {
    const fixture = await mount();
    await fixture.update(".35", {
      ...tariffAttributes(),
      windows: [],
      active_window: null,
    });
    expect(fixture.plans()).toHaveLength(2);
    for (const plan of fixture.plans()) {
      expect(rows(plan)).toEqual([["jetzt", "Standardpreis", "35,00 ct/kWh"]]);
      expect(plan.querySelectorAll(".tariff-plan__current")).toHaveLength(1);
      expect(plan.textContent).toContain("8,00 ct/kWh");
      expect(plan.textContent).toContain("29.03.2026, 18:00");
    }
    expect(chargingTimes(fixture.root)).toEqual([]);
    expect(fixture.callService).not.toHaveBeenCalled();
  });

  it.each(["unknown", "unavailable", "", "NaN", "Infinity"])(
    "shows no active price for an unavailable or invalid current price (%s)",
    async (state) => {
      const fixture = await mount();
      await fixture.update(state, tariffAttributes());
      expect(fixture.plans()).toHaveLength(2);
      for (const plan of fixture.plans()) {
        expect(rows(plan)).toHaveLength(3);
        expect(plan.querySelector(".tariff-plan__current")).toBeNull();
        expect(plan.textContent).toContain(
          "Derzeit ist kein aktueller Strompreis verfügbar",
        );
      }
      await fixture.update(state, {
        ...tariffAttributes(),
        active_window: null,
        base_price_eur_kwh: null,
        feed_in_price_eur_kwh: null,
        unavailable_reason: "missing_base_price",
      });
      for (const plan of fixture.plans()) {
        expect(rows(plan)).toHaveLength(3);
        expect(plan.querySelector(".tariff-plan__current")).toBeNull();
        expect(plan.textContent).toContain(
          "Derzeit ist kein aktueller Strompreis verfügbar",
        );
        expect(plan.textContent).toContain("missing_base_price");
        expect(plan.textContent).not.toContain("0,00 ct/kWh");
      }
      expect(fixture.callService).not.toHaveBeenCalled();
    },
  );

  it("keeps unknown window prices distinct from a valid zero price", async () => {
    const fixture = await mount();
    const windows = twoWindows.map((window, index) => ({
      ...window,
      price_eur_kwh: index === 1 ? null : 0,
    }));
    await fixture.update("0", tariffAttributes(windows));
    for (const plan of fixture.plans()) {
      expect(rows(plan)[0]).toContain("0,00 ct/kWh");
      expect(rows(plan)[1]).toContain("Nicht verfügbar");
      expect(plan.querySelector(".tariff-plan__current")).toBeNull();
    }
    expect(fixture.callService).not.toHaveBeenCalled();
  });

  it("explains the binding translated low-tariff schedule and where to configure it", async () => {
    const fixture = await mount({ language: "en-GB" });
    expect(fixture.plans()).toHaveLength(2);
    for (const plan of fixture.plans()) {
      expect(plan.querySelector("h2")?.textContent).toBe(
        "Your electricity tariff",
      );
      expect(plan.textContent).toContain("-1.50 ct/kWh");
      expect(plan.textContent).toContain(
        "lowest price level that actually occurs each day",
      );
      expect(plan.textContent).toContain(
        "How are the cheapest charging times selected?",
      );
      expect(plan.textContent).toContain(
        "separate grid charging times have no effect",
      );
      expect(
        plan.querySelector(".tariff-plan__low-status")?.textContent,
      ).toContain("Cheapest period until 29 Mar 2026, 18:00");
    }
    expect(
      fixture.root.querySelector(".timed-fixture")?.textContent,
    ).not.toContain("Grid charging window");
    expect(chargingTimes(fixture.root)).toEqual([]);
    expect(fixture.callService).not.toHaveBeenCalled();
  });
});

function button(root: Element, text: string): HTMLButtonElement {
  return [...root.querySelectorAll("button")].find(
    (button) => button.textContent?.trim() === text,
  )!;
}
async function click(root: Element, text: string) {
  button(root, text).click();
  await flush();
}
async function fill(root: Element, selector: string, value: string) {
  const input = root.querySelector<HTMLInputElement>(selector)!;
  input.value = value;
  input.dispatchEvent(new Event("input", { bubbles: true }));
  await flush();
}
function saves(fixture: Awaited<ReturnType<typeof mount>>) {
  return fixture.callWS.mock.calls.filter(
    ([request]) => request.type === "sax_power/dashboard/tariff/save",
  );
}
describe("REQ-VUE-TARIFF-EDITOR: explicit dashboard tariff editor", () => {
  it.each([
    ["de", "Bearbeiten", "Wird geladen …", "Speichern", "Wird gespeichert …"],
    ["en", "Edit", "Loading …", "Save", "Saving …"],
  ])(
    "announces delayed reads and writes immediately in %s",
    async (language, edit, loading, save, saving) => {
      const fixture = await mount({ language });
      const plan = fixture.plans()[0]!;
      const profile = await fixture.callWS({
        type: "sax_power/dashboard/tariff/get",
      });
      let resolve!: (value: TariffProfile) => void;
      fixture.callWS.mockImplementationOnce(
        () =>
          new Promise<TariffProfile>((done) => {
            resolve = done;
          }),
      );
      await click(plan, edit);
      expect(plan.querySelector('[role="status"]')?.textContent).toContain(
        loading,
      );
      const requests = fixture.callWS.mock.calls.length;
      button(plan, loading).click();
      await flush();
      expect(fixture.callWS).toHaveBeenCalledTimes(requests);
      resolve(profile as TariffProfile);
      await flush();
      let reject!: (cause: unknown) => void;
      fixture.callWS.mockImplementationOnce(
        () =>
          new Promise<TariffProfile>((_done, fail) => {
            reject = fail;
          }),
      );
      await click(plan, save);
      expect(plan.querySelector('[role="status"]')?.textContent).toContain(
        saving,
      );
      expect(plan.querySelector("form")?.getAttribute("aria-busy")).toBe(
        "true",
      );
      button(plan, saving).click();
      await flush();
      expect(saves(fixture)).toHaveLength(1);
      reject({ code: "failed" });
      await flush();
      expect(plan.querySelector('[role="alert"]')).not.toBeNull();
      expect(button(plan, save).disabled).toBe(false);
      expect(
        plan.querySelector<HTMLInputElement>('[name="base_price"]')?.value,
      ).toBe(language === "de" ? "35,00" : "35.00");
    },
  );
  it("loads existing prices in cents, saves the complete tariff atomically, then collapses", async () => {
    const fixture = await mount();
    const plan = fixture.plans()[0]!;
    await click(plan, "Bearbeiten");
    expect(fixture.callWS).toHaveBeenLastCalledWith({
      type: "sax_power/dashboard/tariff/get",
      entry_id: "entry-1",
    });
    expect(
      plan.querySelector<HTMLInputElement>('[name="base_price"]')?.value,
    ).toBe("35,00");
    expect(plan.querySelectorAll(".tariff-plan__window")).toHaveLength(2);
    await fill(plan, '[name="base_price"]', "32,75");
    await fill(plan, '[name="feed_in_price"]', "8.12");
    await fill(plan, ".tariff-plan__price", "-2,50");
    expect(saves(fixture)).toHaveLength(0);
    await click(plan, "Speichern");
    expect(saves(fixture)[0]?.[0]).toEqual({
      type: "sax_power/dashboard/tariff/save",
      entry_id: "entry-1",
      revision: "revision-1",
      base_price_ct_kwh: 32.75,
      feed_in_price_ct_kwh: 8.12,
      windows: [
        { start: "06:00:00", end: "12:00:00", price_ct_kwh: -2.5 },
        { start: "12:00:00", end: "18:00:00", price_ct_kwh: -1.5 },
      ],
    });
    expect(plan.querySelector("form")).toBeNull();
    expect(plan.textContent).toContain("32,75 ct/kWh");
    expect(plan.textContent).toContain("Tarif gespeichert");
    expect(fixture.callService).not.toHaveBeenCalled();
  });
  it("discards cancelled edits without saving, and reloads the persisted revision on reopening", async () => {
    const fixture = await mount();
    const plan = fixture.plans()[0]!;
    await click(plan, "Bearbeiten");
    await fill(plan, '[name="base_price"]', "99");
    await click(plan, "Abbrechen");
    expect(saves(fixture)).toHaveLength(0);
    await click(plan, "Bearbeiten");
    expect(
      plan.querySelector<HTMLInputElement>('[name="base_price"]')?.value,
    ).toBe("35,00");
  });
  it.each(["", "NaN", "32,123", "501", "-201"])(
    "rejects invalid base price %s without saving",
    async (value) => {
      const fixture = await mount();
      const plan = fixture.plans()[0]!;
      await click(plan, "Bearbeiten");
      await fill(plan, '[name="base_price"]', value);
      await click(plan, "Speichern");
      expect(plan.querySelector('[role="alert"]')?.textContent).toContain(
        "zwei Nachkommastellen",
      );
      expect(saves(fixture)).toHaveLength(0);
    },
  );
  it("rejects equal and overlapping times, including overnight, and supports adjacent overnight windows", async () => {
    const fixture = await mount({
      windows: [
        { start: "22:00:15", end: "06:00:15", price_eur_kwh: 0.18 },
        { start: "06:00:15", end: "08:00:00", price_eur_kwh: 0.22 },
      ],
    });
    const plan = fixture.plans()[0]!;
    await click(plan, "Bearbeiten");
    await fill(plan, ".tariff-plan__time", "06:00:15");
    await click(plan, "Speichern");
    expect(plan.querySelector('[role="alert"]')?.textContent).toContain(
      "verschieden",
    );
    await fill(plan, ".tariff-plan__time", "07:00:00");
    await click(plan, "Speichern");
    expect(plan.querySelector('[role="alert"]')?.textContent).toContain(
      "überschneiden",
    );
    await fill(plan, ".tariff-plan__time", "22:00:15");
    await click(plan, "Speichern");
    expect(saves(fixture)).toHaveLength(1);
    expect(saves(fixture)[0]?.[0].windows).toEqual([
      { start: "22:00:15", end: "06:00:15", price_ct_kwh: 18 },
      { start: "06:00:15", end: "08:00:00", price_ct_kwh: 22 },
    ]);
  });
  it.each([
    ["1230", "12:30:00"],
    [" 12:30 ", "12:30:00"],
    ["12:30:15", "12:30:15"],
    ["0000", "00:00:00"],
    ["2359", "23:59:00"],
  ])(
    "normalizes complete time %s without changing its meaning",
    async (input, expected) => {
      const fixture = await mount({
        profile: {
          windows: [{ start: "12:00:00", end: "15:30:00", price_ct_kwh: 16 }],
        },
      });
      const plan = fixture.plans()[0]!;
      await click(plan, "Bearbeiten");
      await fill(plan, ".tariff-plan__time", input);
      await click(plan, "Speichern");
      expect(saves(fixture)[0]?.[0].windows).toEqual([
        { start: expected, end: "15:30:00", price_ct_kwh: 16 },
      ]);
    },
  );
  it.each(["12", "123", "12:", "12:3", "24:00", "2360", "12:30:60", "noon"])(
    "preserves invalid time %s without inventing missing parts or saving",
    async (value) => {
      const fixture = await mount();
      const plan = fixture.plans()[0]!;
      await click(plan, "Bearbeiten");
      await fill(plan, ".tariff-plan__time", value);
      const input = plan.querySelector<HTMLInputElement>(".tariff-plan__time")!;
      input.dispatchEvent(new Event("change", { bubbles: true }));
      await flush();
      expect(input.value).toBe(value);
      await click(plan, "Speichern");
      expect(input.value).toBe(value);
      expect(input.getAttribute("aria-invalid")).toBe("true");
      expect(document.activeElement).toBe(input);
      expect(saves(fixture)).toHaveLength(0);
    },
  );
  it.each(["change", "submit"])(
    "saves the visible midnight and midday windows after %s commits",
    async (commit) => {
      const fixture = await mount({ profile: { windows: [] } });
      const plan = fixture.plans()[0]!;
      await click(plan, "Bearbeiten");
      for (let index = 0; index < 2; index++) {
        await click(plan, "+ Zeitfenster hinzufügen");
        const row = [
          ...plan.querySelectorAll<HTMLElement>(".tariff-plan__window"),
        ].at(-1)!;
        await fill(row, ".tariff-plan__price", "18,50");
      }
      const inputs =
        plan.querySelectorAll<HTMLInputElement>(".tariff-plan__time");
      for (const [index, value] of [
        "00:00",
        "04:59",
        "12:30",
        "14:30",
      ].entries()) {
        inputs[index]!.value = value;
        if (commit === "change")
          inputs[index]!.dispatchEvent(new Event("change", { bubbles: true }));
      }
      await click(plan, "Speichern");
      expect(plan.querySelector('[role="alert"]')).toBeNull();
      expect(saves(fixture)[0]?.[0].windows).toEqual([
        { start: "00:00:00", end: "04:59:00", price_ct_kwh: 18.5 },
        { start: "12:30:00", end: "14:30:00", price_ct_kwh: 18.5 },
      ]);
    },
  );
  it.each([
    ["de", "start", "Zeitfenster 2", "Startzeit"],
    ["de", "end", "Zeitfenster 2", "Endzeit"],
    ["en", "start", "Time window 2", "start time"],
    ["en", "end", "Time window 2", "end time"],
  ])(
    "identifies and focuses the incomplete %s %s field, preserving both drafts",
    async (language, field, windowLabel, fieldLabel) => {
      const fixture = await mount({
        language,
        windows: [
          { start: "00:00:00", end: "04:59:00", price_eur_kwh: 0.18 },
          { start: "12:30:00", end: "14:30:00", price_eur_kwh: 0.18 },
        ],
      });
      const plan = fixture.plans()[0]!;
      await click(plan, language === "de" ? "Bearbeiten" : "Edit");
      const row = plan.querySelectorAll<HTMLElement>(
        ".tariff-plan__window",
      )[1]!;
      const input = row.querySelector<HTMLInputElement>(
        `input[name$="_${field}"]`,
      )!;
      input.value = "";
      input.dispatchEvent(new Event("input", { bubbles: true }));
      await click(plan, language === "de" ? "Speichern" : "Save");
      const alert = plan.querySelector('[role="alert"]')!;
      expect(alert.textContent).toContain(windowLabel);
      expect(alert.textContent).toContain(fieldLabel);
      expect(input.getAttribute("aria-invalid")).toBe("true");
      expect(input.getAttribute("aria-describedby")?.split(" ")).toContain(
        alert.id,
      );
      expect(document.activeElement).toBe(input);
      expect(plan.querySelectorAll(".tariff-plan__window")).toHaveLength(2);
      expect(saves(fixture)).toHaveLength(0);
      input.value = field === "start" ? "12:30" : "14:30";
      input.dispatchEvent(new Event("change", { bubbles: true }));
      await flush();
      expect(plan.querySelector('[role="alert"]')).toBeNull();
      await click(plan, language === "de" ? "Speichern" : "Save");
      expect(saves(fixture)).toHaveLength(1);
    },
  );
  it("supports an empty initial profile, optional new windows and removal up to the eight-window limit", async () => {
    const fixture = await mount({
      profile: {
        base_price_ct_kwh: null,
        feed_in_price_ct_kwh: null,
        windows: [],
      },
    });
    const plan = fixture.plans()[0]!;
    await click(plan, "Bearbeiten");
    expect(plan.textContent).toContain("Trage zuerst");
    expect(plan.querySelectorAll(".tariff-plan__window")).toHaveLength(0);
    for (let index = 0; index < 8; index++)
      await click(plan, "+ Zeitfenster hinzufügen");
    expect(button(plan, "+ Zeitfenster hinzufügen")).toBeUndefined();
    for (let index = 0; index < 8; index++) await click(plan, "Entfernen");
    await fill(plan, '[name="base_price"]', "30");
    await fill(plan, '[name="feed_in_price"]', "0");
    await click(plan, "Speichern");
    expect(saves(fixture)[0]?.[0].windows).toEqual([]);
  });
  it("keeps read-only accounts out of the editor and disables actions while disconnected", async () => {
    const fixture = await mount({ profile: { can_edit: false } });
    const plan = fixture.plans()[0]!;
    await click(plan, "Bearbeiten");
    expect(plan.querySelector("form")).toBeNull();
    expect(plan.querySelector('[role="alert"]')?.textContent).toContain(
      "Administratorkonto",
    );
    await fixture.disconnect();
    expect(button(plan, "Bearbeiten").disabled).toBe(true);
    expect(saves(fixture)).toHaveLength(0);
  });
  it.each(["conflict", "invalid_tariff", "forbidden", "not_found"])(
    "preserves the draft on server error %s",
    async (code) => {
      const fixture = await mount();
      const plan = fixture.plans()[0]!;
      await click(plan, "Bearbeiten");
      await fill(plan, '[name="base_price"]', "32");
      fixture.callWS.mockRejectedValueOnce({ code });
      await click(plan, "Speichern");
      expect(
        plan.querySelector<HTMLInputElement>('[name="base_price"]')?.value,
      ).toBe("32");
      expect(plan.querySelector('[role="alert"]')).not.toBeNull();
      if (code === "conflict") {
        expect(button(plan, "Speichern").disabled).toBe(true);
        await click(plan, "Gespeicherten Tarif laden (Entwurf verwerfen)");
        expect(
          plan.querySelector<HTMLInputElement>('[name="base_price"]')?.value,
        ).toBe("35,00");
      }
    },
  );
  it.each(["de", "en"])(
    "explains a missing PV source in %s and retains the tariff draft",
    async (language) => {
      const fixture = await mount({ language });
      const plan = fixture.plans()[0]!;
      await click(plan, language === "de" ? "Bearbeiten" : "Edit");
      await fill(plan, '[name="base_price"]', "32");
      fixture.callWS.mockRejectedValueOnce({ code: "pv_sensor_missing" });
      await click(plan, language === "de" ? "Speichern" : "Save");
      expect(plan.querySelector('[role="alert"]')?.textContent).toContain(
        language === "de"
          ? "PV-Start-Sensor wurde nicht gefunden"
          : "PV start sensor was not found",
      );
      expect(
        plan.querySelector<HTMLInputElement>('[name="base_price"]')?.value,
      ).toBe("32");
      expect(plan.querySelectorAll(".tariff-plan__window")).toHaveLength(2);
    },
  );
  it("preserves a pending draft when disconnected and allows retry only after reconnect", async () => {
    const fixture = await mount();
    const plan = fixture.plans()[0]!;
    await click(plan, "Bearbeiten");
    await fill(plan, '[name="base_price"]', "33");
    let resolve: (value: TariffProfile) => void = () => {};
    fixture.callWS.mockImplementationOnce(
      () =>
        new Promise<TariffProfile>((done) => {
          resolve = done;
        }),
    );
    await click(plan, "Speichern");
    expect(button(plan, "Wird gespeichert …").disabled).toBe(true);
    await fixture.disconnect();
    resolve({
      tariff_type: "time_of_use",
      base_price_ct_kwh: 33,
      feed_in_price_ct_kwh: 8,
      windows: [],
      revision: "later",
      can_edit: true,
    });
    await flush();
    expect(
      plan.querySelector<HTMLInputElement>('[name="base_price"]')?.value,
    ).toBe("33");
    expect(button(plan, "Speichern").disabled).toBe(true);
    await fixture.disconnect(false);
    expect(button(plan, "Speichern").disabled).toBe(false);
  });
});

it.each(
  [
    [
      { start: "00:00:00", end: "06:00:00", price_eur_kwh: 0.18 },
      { start: "18:00:00", end: "00:00:00", price_eur_kwh: 0.2 },
    ],
    eightWindows,
  ].map((windows) => ({ windows })),
)(
  "REQ-VUE-TARIFF-EDITOR accepts adjacent windows ending at midnight",
  async ({ windows }) => {
    const fixture = await mount({ windows });
    const plan = fixture.plans()[0]!;
    await click(plan, "Bearbeiten");
    await click(plan, "Speichern");
    expect(plan.querySelector('[role="alert"]')).toBeNull();
    expect(saves(fixture)).toHaveLength(1);
  },
);
it("REQ-VUE-TARIFF-EDITOR retains a saved tariff until matching sensor attributes arrive", async () => {
  const fixture = await mount();
  const plan = fixture.plans()[0]!;
  await click(plan, "Bearbeiten");
  await fill(plan, '[name="base_price"]', "42");
  await click(plan, "Speichern");
  await fixture.update("-1.5", {
    ...tariffAttributes(),
    next_price_change_at: "2026-03-30T16:00:00Z",
  });
  expect(plan.textContent).toContain("42,00 ct/kWh");
  expect(plan.textContent).not.toContain("35,00 ct/kWh");
  expect(plan.querySelector(".tariff-plan__low-unavailable")).toBeNull();
  await fixture.update("-1.5", {
    ...tariffAttributes(),
    base_price_eur_kwh: 0.42,
    windows: [
      {
        start: "06:00:00",
        end: "12:00:00",
        price_eur_kwh: 0.2568,
        low_tariff: false,
      },
      {
        start: "12:00:00",
        end: "18:00:00",
        price_eur_kwh: -0.015,
        low_tariff: true,
      },
    ],
  });
  expect(plan.textContent).toContain("42,00 ct/kWh");
  expect(plan.querySelector(".tariff-plan__low-status")).not.toBeNull();
});

it("REQ-VUE-TARIFF-EDITOR accepts the sensor's sorted windows and later external tariff changes", async () => {
  const unordered = [
    { start: "18:00:00", end: "22:00:00", price_eur_kwh: 0.18 },
    { start: "00:00:00", end: "06:00:00", price_eur_kwh: 0.1 },
  ];
  const fixture = await mount({ windows: unordered });
  const plan = fixture.plans()[0]!;
  await click(plan, "Bearbeiten");
  await fill(plan, '[name="base_price"]', "42");
  await click(plan, "Speichern");
  await fixture.update("10", {
    ...tariffAttributes(unordered.slice().reverse()),
    base_price_eur_kwh: 0.42,
  });
  expect(plan.querySelector(".tariff-plan__low-status")).not.toBeNull();
  await click(plan, "Bearbeiten");
  await fill(plan, '[name="base_price"]', "43");
  await click(plan, "Speichern");
  await fixture.update("10", {
    ...tariffAttributes(unordered),
    base_price_eur_kwh: 0.5,
  });
  expect(plan.textContent).toContain("50,00 ct/kWh");
  expect(plan.textContent).not.toContain("43,00 ct/kWh");
  await click(plan, "Bearbeiten");
  await fill(plan, '[name="base_price"]', "44");
  await click(plan, "Speichern");
  await fixture.update("10", { tariff_type: "dynamic" });
  expect(fixture.plans()).toHaveLength(0);
});

describe("REQ-VUE-TARIFF-EDITOR: guided everyday tariff setup", () => {
  it.each(["de", "en"])(
    "keeps the current price visible and full detail optional in %s",
    async (language) => {
      const fixture = await mount({ language });
      for (const plan of fixture.plans()) {
        expect(
          plan.querySelector(".tariff-plan__current-price")?.textContent,
        ).toContain(language === "de" ? "-1,50 ct/kWh" : "-1.50 ct/kWh");
        const details = plan.querySelector<HTMLDetailsElement>(
          ".tariff-plan__all-prices",
        )!;
        expect(details.open).toBe(false);
        expect(details.querySelector("summary")?.textContent).toBe(
          language === "de" ? "Alle Preise ansehen" : "View all prices",
        );
        const scroll = details.querySelector<HTMLElement>(
          ".tariff-plan__scroll",
        )!;
        expect(scroll.tabIndex).toBe(0);
        expect(scroll.getAttribute("aria-label")).toBeTruthy();
        expect(details.querySelector("table th")?.getAttribute("scope")).toBe(
          "col",
        );
      }
      expect(saves(fixture)).toHaveLength(0);
    },
  );

  it.each(["de", "en"])(
    "explains daily prices and overnight periods in the compact %s overview",
    async (language) => {
      const fixture = await mount({
        compact: true,
        language,
        windows: [
          { start: "22:00:00", end: "06:00:00", price_eur_kwh: 0.18 },
          { start: "06:00:00", end: "08:00:00", price_eur_kwh: 0.22 },
        ],
      });
      const plan = fixture.plans()[0]!;
      expect(plan.querySelector("h2")?.textContent).toBe(
        language === "de"
          ? "1. Wann ist dein Strom günstig?"
          : "1. When is your electricity cheaper?",
      );
      const summary = plan.querySelector(".tariff-plan__compact-summary")!;
      expect(summary.textContent).toContain(
        language === "de" ? "35,00 ct/kWh" : "35.00 ct/kWh",
      );
      expect(summary.textContent).toContain("22:00 – 06:00");
      expect(summary.textContent).toContain(
        language === "de" ? "über Nacht" : "overnight",
      );
      expect(summary.textContent).toContain(
        language === "de" ? "aktive Monate" : "active months",
      );
      expect(plan.querySelector("form")).toBeNull();
      expect(saves(fixture)).toHaveLength(0);
    },
  );

  it.each(["de", "en"])(
    "places prices, different times and feed-in payment in order and explains saving in %s",
    async (language) => {
      const fixture = await mount({ compact: true, language });
      const plan = fixture.plans()[0]!;
      await click(plan, language === "de" ? "Bearbeiten" : "Edit");
      const steps = [...plan.querySelectorAll(".tariff-plan__step")];
      expect(steps).toHaveLength(3);
      expect(steps[0].querySelector('[name="base_price"]')).not.toBeNull();
      expect(steps[1].querySelectorAll(".tariff-plan__window")).toHaveLength(2);
      expect(steps[2].querySelector('[name="feed_in_price"]')).not.toBeNull();
      const feed = plan.querySelector('[name="feed_in_price"]')!;
      expect(
        document.getElementById(feed.getAttribute("aria-describedby")!)
          ?.textContent,
      ).toContain(language === "de" ? "Ohne Vergütung 0" : "Enter 0");
      expect(
        plan.querySelector(".tariff-plan__editor .tariff-plan__impact")
          ?.textContent,
      ).toContain(
        language === "de"
          ? "Es schaltet die Netzladung nicht ein"
          : "It does not turn on grid charging",
      );
      expect(
        plan.querySelector<HTMLDetailsElement>(".tariff-plan__pv-details")
          ?.open,
      ).toBe(false);
      expect(saves(fixture)).toHaveLength(0);
      expect(fixture.callService).not.toHaveBeenCalled();
    },
  );
});

it("REQ-VUE-TARIFF-EDITOR marks only backend-selected cheap periods in the compact overview, including gaps and all-day prices", async () => {
  const fixture = await mount({ compact: true });
  const plan = fixture.plans()[0]!;
  expect(plan.querySelectorAll(".tariff-plan__badge")).toHaveLength(1);
  expect(
    plan.querySelector(".tariff-plan__badge")?.closest("li")?.textContent,
  ).toContain("12:00 – 18:00");
  await fixture.update("35", {
    ...tariffAttributes(),
    windows: twoWindows.map((window) => ({
      ...window,
      price_eur_kwh: 0.35,
      low_tariff: true,
    })),
    active_window: null,
    base_price_is_low_tariff: true,
    low_tariff_price_eur_kwh: 0.35,
  });
  expect(plan.querySelectorAll(".tariff-plan__badge")).toHaveLength(3);
  expect(
    plan.querySelector(".tariff-plan__compact-summary > p")?.textContent,
  ).toContain("günstig");
  await fixture.update("35", {
    ...tariffAttributes(),
    windows: [],
    active_window: null,
    base_price_is_low_tariff: true,
    low_tariff_price_eur_kwh: 0.35,
  });
  expect(plan.querySelectorAll(".tariff-plan__badge")).toHaveLength(1);
  expect(
    plan.querySelector(".tariff-plan__compact-summary")?.textContent,
  ).toContain("Standardpreis gilt den ganzen Tag");
});

it("REQ-VUE-TARIFF-EDITOR waits for matching telemetry before marking cheap periods after a compact save", async () => {
  const windows = [
    { start: "06:00:00", end: "12:00:00", price_eur_kwh: 0.18 },
    { start: "12:00:00", end: "18:00:00", price_eur_kwh: 0.22 },
  ];
  const fixture = await mount({ compact: true, windows });
  const plan = fixture.plans()[0]!;
  await click(plan, "Bearbeiten");
  await fill(plan, '[name="base_price"]', "42");
  fixture.callWS.mockResolvedValueOnce({
    tariff_type: "time_of_use",
    base_price_ct_kwh: 42,
    feed_in_price_ct_kwh: 8,
    windows: windows.map((window) => ({
      start: window.start,
      end: window.end,
      price_ct_kwh: window.price_eur_kwh * 100,
    })),
    can_edit: true,
    revision: "2",
  });
  await click(plan, "Speichern");
  expect(plan.querySelectorAll(".tariff-plan__badge")).toHaveLength(0);
  expect(plan.querySelector(".tariff-plan__low-status")).toBeNull();
  expect(
    plan.querySelector(".tariff-plan__pending-status")?.textContent,
  ).toContain("werden aktualisiert");
  await fixture.update("22", {
    ...tariffAttributes(windows),
    base_price_eur_kwh: 0.42,
  });
  expect(plan.querySelectorAll(".tariff-plan__badge")).toHaveLength(1);
  expect(
    plan.querySelector(".tariff-plan__badge")?.closest("li")?.textContent,
  ).toContain("12:00 – 18:00");
  expect(plan.querySelector(".tariff-plan__low-status")).not.toBeNull();
  expect(plan.querySelector(".tariff-plan__pending-status")).toBeNull();
});

it("REQ-VUE-TARIFF-EDITOR opens additional PV setup when the server requires it and keeps the price draft", async () => {
  const fixture = await mount({ compact: true });
  const plan = fixture.plans()[0]!;
  await click(plan, "Bearbeiten");
  await fill(plan, '[name="base_price"]', "32");
  fixture.callWS.mockRejectedValueOnce({ code: "bridge_pv_start_required" });
  await click(plan, "Speichern");
  expect(
    plan.querySelector<HTMLDetailsElement>(".tariff-plan__pv-details")?.open,
  ).toBe(true);
  expect(
    plan.querySelector<HTMLInputElement>('[name="base_price"]')?.value,
  ).toBe("32");
  expect(plan.querySelector('[role="alert"]')?.textContent).toContain(
    "PV-Start-Quelle",
  );
  expect(fixture.callService).not.toHaveBeenCalled();
});
