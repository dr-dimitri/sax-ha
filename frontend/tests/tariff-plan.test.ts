import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import { chargingSample } from "../src/charging-preview-data";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "../src/ha";
import SavingsView from "../src/views/SavingsView.vue";
import TimedChargingView from "../src/views/TimedChargingView.vue";
import type {
  DashboardEntityMetadata,
  DashboardMetadata,
  HassConnection,
  HomeAssistant,
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
    state: "-0.015",
    attributes: {
      ...tariffAttributes(options.windows),
      tariff_type: options.tariffType ?? "time_of_use",
    },
  };
  let emitMetadata: (data: DashboardMetadata) => void = () => {};
  const connection: HassConnection = {
    connected: true,
    async subscribeMessage<T>(callback: (message: T) => void) {
      emitMetadata = (data) => callback(data as T);
      emitMetadata({ entities: metadata });
      return () => {};
    },
    addEventListener() {},
    removeEventListener() {},
  };
  const callService = vi.fn().mockResolvedValue(undefined);
  const callWS = vi.fn().mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    states: sample.states,
    connection,
    callService,
    callWS,
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
        h("div", [
          h("div", { class: "timed-fixture" }, [
            h(TimedChargingView, { hass: hass.value }),
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
        expect(plan.querySelector("h2")?.textContent).toBe("Tarifpreisfenster");
        const displayed = rows(plan);
        expect(displayed).toHaveLength(windows.length + 1);
        windows.forEach((window, index) => {
          expect(displayed[index]).toContain(window.start.slice(0, 5));
          expect(displayed[index]).toContain(window.end.slice(0, 5));
        });
        expect(displayed.at(-1)).toContain("Grundpreis");
        expect(plan.textContent).toContain("0,3500 EUR/kWh");
        expect(plan.textContent).toContain("0,0800 EUR/kWh");
        expect(plan.textContent).toContain("29.03.2026, 18:00");
        const active = plan.querySelectorAll(".tariff-plan__current");
        expect(active).toHaveLength(1);
        expect(active[0].textContent).toContain(windows[1].start.slice(0, 5));
        expect(active[0].textContent).toContain("-0,0150 EUR/kWh");
        expect(
          plan.querySelectorAll("input, select, button, form"),
        ).toHaveLength(0);
      }
      expect(chargingTimes(fixture.root)).toEqual([]);
      expect(fixture.root.textContent).toContain("Netzladung Min. SOC");
      expect(fixture.root.textContent).toContain("Netzladen Max. SOC");
      expect(fixture.root.textContent).toContain("Aktive Monate");
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
      expect(rows(plan).at(-1)?.[0]).toBe("jetzt · Niedertarif");
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
      expect(fixture.root.textContent).toContain("Netzladung Min. SOC");
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
      ).toContain("Aktuell kein Niedertarif");
      expect(
        plan.querySelector(".tariff-plan__low-status")?.textContent,
      ).not.toContain("aktiv bis");
    }
    expect(fixture.callService).not.toHaveBeenCalled();
  });

  it("updates windows and hides legacy charging times only for the registered time-of-use tariff", async () => {
    const fixture = await mount({ tariffType: "fixed" });
    expect(fixture.plans()).toHaveLength(0);
    expect(chargingTimes(fixture.root)).toEqual(["22:00", "06:00"]);
    await fixture.update("-0.015", tariffAttributes());
    expect(fixture.plans()).toHaveLength(2);
    expect(chargingTimes(fixture.root)).toEqual([]);
    await fixture.update("-0.015", tariffAttributes(eightWindows));
    for (const plan of fixture.plans()) expect(rows(plan)).toHaveLength(9);
    await fixture.metadata(false);
    expect(fixture.plans()).toHaveLength(0);
    expect(chargingTimes(fixture.root)).toEqual(["22:00", "06:00"]);
    await fixture.metadata(true);
    expect(fixture.plans()).toHaveLength(2);
    for (const tariffType of ["dynamic", "fixed", "disabled"]) {
      await fixture.update(".35", { tariff_type: tariffType });
      expect(fixture.plans()).toHaveLength(0);
      expect(chargingTimes(fixture.root)).toEqual(["22:00", "06:00"]);
    }
    await fixture.update(".35", {
      ...tariffAttributes(),
      active_window: null,
    });
    for (const plan of fixture.plans()) {
      expect(rows(plan)).toHaveLength(3);
      const active = plan.querySelectorAll(".tariff-plan__current");
      expect(active).toHaveLength(1);
      expect(active[0].textContent).toContain("Grundpreis");
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
      expect(rows(plan)).toEqual([["jetzt", "Grundpreis", "0,3500 EUR/kWh"]]);
      expect(plan.querySelectorAll(".tariff-plan__current")).toHaveLength(1);
      expect(plan.textContent).toContain("0,0800 EUR/kWh");
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
        expect(plan.textContent).toContain("Derzeit gilt kein Preis");
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
        expect(plan.textContent).toContain("Derzeit gilt kein Preis");
        expect(plan.textContent).toContain("missing_base_price");
        expect(plan.textContent).not.toContain("0,0000 EUR/kWh");
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
      expect(rows(plan)[0]).toContain("0,0000 EUR/kWh");
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
        "Tariff price windows",
      );
      expect(plan.textContent).toContain("-0.0150 EUR/kWh");
      expect(plan.textContent).toContain(
        "lowest price level that actually occurs each day",
      );
      expect(plan.textContent).toContain("Configure → Tariff price windows");
      expect(plan.textContent).toContain(
        "separate grid charging times have no effect",
      );
      expect(
        plan.querySelector(".tariff-plan__low-status")?.textContent,
      ).toContain("Low tariff active until 29 Mar 2026, 18:00");
    }
    expect(
      fixture.root.querySelector(".timed-fixture")?.textContent,
    ).not.toContain("Grid charging window");
    expect(chargingTimes(fixture.root)).toEqual([]);
    expect(fixture.callService).not.toHaveBeenCalled();
  });
});
