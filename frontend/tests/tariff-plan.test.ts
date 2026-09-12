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
    windows,
    active_window: { start: windows[1].start, end: windows[1].end },
    base_price_eur_kwh: 0.35,
    feed_in_price_eur_kwh: 0.08,
    next_price_change_at: "2026-03-29T16:00:00Z",
    unavailable_reason: null,
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
      expect(chargingTimes(fixture.root)).toEqual(["22:00", "06:00"]);
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

  it("updates windows, tariff type and entity registration live without changing the grid charging window", async () => {
    const fixture = await mount({ tariffType: "fixed" });
    expect(fixture.plans()).toHaveLength(0);
    await fixture.update("-0.015", tariffAttributes());
    expect(fixture.plans()).toHaveLength(2);
    await fixture.update("-0.015", tariffAttributes(eightWindows));
    for (const plan of fixture.plans()) expect(rows(plan)).toHaveLength(9);
    await fixture.metadata(false);
    expect(fixture.plans()).toHaveLength(0);
    await fixture.metadata(true);
    expect(fixture.plans()).toHaveLength(2);
    for (const tariffType of ["dynamic", "fixed", "disabled"]) {
      await fixture.update(".35", { tariff_type: tariffType });
      expect(fixture.plans()).toHaveLength(0);
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
    expect(chargingTimes(fixture.root)).toEqual(["22:00", "06:00"]);
    expect(fixture.root.querySelectorAll(".time-window-control")).toHaveLength(
      1,
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
    expect(chargingTimes(fixture.root)).toEqual(["22:00", "06:00"]);
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

  it("separates translated price windows from the editable grid charging window", async () => {
    const fixture = await mount({ language: "en-GB" });
    expect(fixture.plans()).toHaveLength(2);
    for (const plan of fixture.plans()) {
      expect(plan.querySelector("h2")?.textContent).toBe(
        "Tariff price windows",
      );
      expect(plan.textContent).toContain("-0.0150 EUR/kWh");
    }
    expect(fixture.root.querySelector(".timed-fixture")?.textContent).toContain(
      "Grid charging window",
    );
    expect(chargingTimes(fixture.root)).toEqual(["22:00", "06:00"]);
    expect(fixture.callService).not.toHaveBeenCalled();
  });
});
