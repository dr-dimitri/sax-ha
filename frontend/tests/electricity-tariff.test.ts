import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import ElectricityTariffView from "../src/views/ElectricityTariffView.vue";
import TariffPriceChart from "../src/components/TariffPriceChart.vue";
import TimedChargingView from "../src/views/TimedChargingView.vue";
import {
  SAX_DASHBOARD_KEY,
  useSaxDashboard,
  type SaxDashboard,
} from "../src/ha";
import { chargingSample } from "../src/charging-preview-data";
import { tariffChart } from "../src/tariff-chart";
import type {
  HomeAssistant,
  TariffPriceSeries,
  TariffProfile,
} from "../src/types";
const apps: App[] = [];
async function flush() {
  for (let index = 0; index < 6; index++) {
    await Promise.resolve();
    await nextTick();
  }
}
const initialProfile = (): TariffProfile => ({
  tariff_type: "time_of_use",
  base_price_ct_kwh: 32,
  feed_in_price_ct_kwh: 8,
  windows: [{ start: "00:00:00", end: "06:00:00", price_ct_kwh: 18 }],
  revision: "1",
  can_edit: true,
  can_configure: true,
  automation_enabled: false,
  profiles: {
    time_of_use: {
      base_price_ct_kwh: 32,
      feed_in_price_ct_kwh: 8,
      windows: [{ start: "00:00:00", end: "06:00:00", price_ct_kwh: 18 }],
      pv_sensor: null,
    },
    dynamic: {
      feed_in_price_ct_kwh: 8,
      price_sensor: "sensor.market_price",
      price_attribute: null,
      price_unit: "ct_kwh",
      pv_sensor: null,
      pv_factor: 70,
    },
  },
});
const sampleSeries = (
  day: "today" | "tomorrow" = "today",
): TariffPriceSeries => ({
  tariff_type: "time_of_use",
  day,
  date: "2026-09-13",
  time_zone: "Europe/Berlin",
  start: "2026-09-13T00:00:00+02:00",
  end: "2026-09-14T00:00:00+02:00",
  now: "2026-09-13T12:15:00+02:00",
  current_price_ct_kwh: -2.5,
  status: "partial",
  reason: null,
  slots: [
    {
      start: "2026-09-13T00:00:00+02:00",
      end: "2026-09-13T06:00:00+02:00",
      price_ct_kwh: 18,
    },
    {
      start: "2026-09-13T06:00:00+02:00",
      end: "2026-09-13T12:00:00+02:00",
      price_ct_kwh: 32,
    },
    {
      start: "2026-09-13T13:00:00+02:00",
      end: "2026-09-14T00:00:00+02:00",
      price_ct_kwh: -2.5,
    },
  ],
  gaps: [
    { start: "2026-09-13T12:00:00+02:00", end: "2026-09-13T13:00:00+02:00" },
  ],
  revision: "1",
});
async function mount(
  options: {
    type?: string;
    readonly?: boolean;
    language?: string;
    enabled?: boolean;
    legacy?: boolean;
  } = {},
) {
  const sample = chargingSample(options.language ?? "de");
  sample.metadata.push({
    domain: "switch",
    key: "bridge_charge_enabled",
    entity_id: "switch.renamed_bridge_charge_enabled",
    name: "Bridge charging",
    states: {},
    can_control: true,
  });
  sample.states["switch.renamed_bridge_charge_enabled"] = {
    entity_id: "switch.renamed_bridge_charge_enabled",
    state: "off",
    attributes: {},
  };
  sample.states["sensor.market_price"] = {
    entity_id: "sensor.market_price",
    state: "-2.5",
    attributes: { friendly_name: "Marktpreis", unit_of_measurement: "ct/kWh" },
  };
  let stored = {
    ...initialProfile(),
    tariff_type: options.type ?? "time_of_use",
    automation_enabled: options.enabled ?? false,
    can_configure: !options.readonly,
    can_edit: !options.readonly,
  };
  const listeners = new Map<string, Set<() => void>>();
  const connection = {
    connected: true,
    async subscribeMessage<T>(callback: (message: T) => void) {
      callback({ entities: sample.metadata } as T);
      return () => {};
    },
    addEventListener(event: string, callback: () => void) {
      const callbacks = listeners.get(event) ?? new Set();
      callbacks.add(callback);
      listeners.set(event, callbacks);
    },
    removeEventListener(event: string, callback: () => void) {
      listeners.get(event)?.delete(callback);
    },
  };
  const callWS = vi.fn(
    async (
      request: Readonly<Record<string, unknown>>,
    ): Promise<TariffProfile | TariffPriceSeries> => {
      if (request.type === "sax_power/dashboard/tariff/get")
        return structuredClone(stored);
      if (request.type === "sax_power/dashboard/tariff/series")
        return {
          ...sampleSeries(request.day as "today" | "tomorrow"),
          tariff_type: stored.tariff_type,
        };
      if (request.type === "sax_power/dashboard/tariff/configure") {
        if (request.revision !== stored.revision) throw { code: "conflict" };
        stored = {
          ...stored,
          tariff_type: String(request.tariff_type),
          revision: String(Number(stored.revision) + 1),
          automation_enabled:
            typeof request.automation_enabled === "boolean"
              ? request.automation_enabled
              : stored.automation_enabled,
        };
        if (request.profile)
          stored.profiles = {
            ...stored.profiles!,
            [stored.tariff_type]: request.profile,
          };
        return structuredClone(stored);
      }
      throw { code: "not_found" };
    },
  );
  const callService = vi.fn().mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    states: sample.states,
    connection,
    callWS: <T>(message: Readonly<Record<string, unknown>>) =>
      callWS(message) as Promise<T>,
    callService,
    config: { time_zone: "Europe/Berlin" },
  });
  const root = document.createElement("div");
  document.body.append(root);
  let dashboard!: SaxDashboard;
  const app = createApp({
    setup() {
      dashboard = useSaxDashboard(
        () => hass.value,
        () => "entry-1",
      );
      provide(SAX_DASHBOARD_KEY, dashboard);
      void dashboard.loadTariff();
      return () =>
        h(options.legacy ? TimedChargingView : ElectricityTariffView, {
          hass: hass.value,
        });
    },
  });
  apps.push(app);
  app.mount(root);
  await flush();
  return {
    root,
    dashboard,
    hass,
    callWS,
    callService,
    get stored() {
      return stored;
    },
    async disconnect() {
      connection.connected = false;
      listeners.get("disconnected")?.forEach((callback) => callback());
      await flush();
    },
    async update(key: string, state: string) {
      const id = sample.metadata.find((item) => item.key === key)?.entity_id!;
      hass.value = {
        ...hass.value,
        states: {
          ...hass.value.states,
          [id]: { ...hass.value.states[id]!, state },
        },
      };
      await flush();
    },
  };
}
function button(root: Element, label: string) {
  return [...root.querySelectorAll<HTMLButtonElement>("button")].find(
    (button) => button.textContent?.trim() === label,
  )!;
}
async function click(root: Element, label: string) {
  button(root, label).click();
  await flush();
}
async function fill(root: Element, selector: string, value: string) {
  const input = root.querySelector<HTMLInputElement>(selector)!;
  input.value = value;
  input.dispatchEvent(new Event("input", { bubbles: true }));
  await flush();
}
const writes = (fixture: Awaited<ReturnType<typeof mount>>) =>
  fixture.callWS.mock.calls.filter(
    ([request]) => request.type === "sax_power/dashboard/tariff/configure",
  );
afterEach(() => {
  apps.splice(0).forEach((app) => app.unmount());
  document.body.replaceChildren();
  vi.useRealTimers();
});
describe("REQ-VUE-ELECTRICITY-TARIFF: one active tariff and compact configuration", () => {
  it("keeps tariff selection independent of disabled charging and exposes one main switch", async () => {
    const fixture = await mount();
    expect(
      fixture.root.querySelectorAll(".electricity-master input"),
    ).toHaveLength(1);
    expect(fixture.root.textContent).toContain("Zeitvariabel");
    expect(fixture.root.textContent).toContain("Automatische Netzladung aus");
    expect(fixture.root.textContent).toContain("-2,50");
    expect(
      fixture.root.querySelectorAll(".electricity-charging-editor"),
    ).toHaveLength(0);
    expect(writes(fixture)).toHaveLength(0);
  });
  it("applies a tariff choice once, preserves automations off, and controls the active automation through configure", async () => {
    const fixture = await mount();
    await click(fixture.root, "Tarif wechseln");
    const dynamic = fixture.root.querySelector<HTMLInputElement>(
      'input[value="dynamic"]',
    )!;
    dynamic.checked = true;
    dynamic.dispatchEvent(new Event("change", { bubbles: true }));
    await flush();
    expect(writes(fixture)).toHaveLength(0);
    await click(fixture.root, "Tarif übernehmen");
    expect(writes(fixture)[0]?.[0]).toEqual({
      type: "sax_power/dashboard/tariff/configure",
      entry_id: "entry-1",
      revision: "1",
      tariff_type: "dynamic",
    });
    expect(fixture.stored.automation_enabled).toBe(false);
    const master = fixture.root.querySelector<HTMLInputElement>(
      ".electricity-master input",
    )!;
    master.checked = true;
    master.dispatchEvent(new Event("change", { bubbles: true }));
    await flush();
    expect(writes(fixture)[1]?.[0]).toEqual({
      type: "sax_power/dashboard/tariff/configure",
      entry_id: "entry-1",
      revision: "2",
      tariff_type: "dynamic",
      automation_enabled: true,
    });
    expect(fixture.callService).not.toHaveBeenCalled();
  });
  it("keeps automation off when selecting an incomplete profile so its editor is reachable", async () => {
    const fixture = await mount({ enabled: true });
    fixture.stored.profiles!.dynamic.price_sensor = null;
    await fixture.dashboard.loadTariff();
    await click(fixture.root, "Tarif wechseln");
    const radio = fixture.root.querySelector<HTMLInputElement>(
      'input[value="dynamic"]',
    )!;
    radio.click();
    await flush();
    expect(fixture.root.textContent).toContain(
      "Nach dem Wechsel bleibt die automatische Netzladung aus",
    );
    await click(fixture.root, "Tarif übernehmen");
    expect(writes(fixture)[0]?.[0]).toMatchObject({
      tariff_type: "dynamic",
      automation_enabled: false,
    });
    await click(
      fixture.root.querySelector(".electricity-prices")!,
      "Bearbeiten",
    );
    expect(
      fixture.root.querySelector(".electricity-prices select"),
    ).not.toBeNull();
  });
  it("refreshes stable prices and external settings each minute and stops after unmount", async () => {
    vi.useFakeTimers();
    const fixture = await mount();
    fixture.callWS.mockClear();
    fixture.stored.automation_enabled = true;
    await vi.advanceTimersByTimeAsync(60_000);
    await flush();
    expect(
      fixture.callWS.mock.calls.some(
        ([request]) => request.type === "sax_power/dashboard/tariff/series",
      ),
    ).toBe(true);
    expect(
      fixture.root.querySelector<HTMLInputElement>(".electricity-master input")
        ?.checked,
    ).toBe(true);
    apps.splice(0).forEach((app) => app.unmount());
    fixture.callWS.mockClear();
    await vi.advanceTimersByTimeAsync(120_000);
    expect(fixture.callWS).not.toHaveBeenCalled();
  });
  it("ignores a delayed tariff read after a confirmed configuration write", async () => {
    const fixture = await mount();
    let resolve!: (value: TariffProfile) => void;
    fixture.callWS.mockImplementationOnce(
      () =>
        new Promise<TariffProfile>((done) => {
          resolve = done;
        }),
    );
    const read = fixture.dashboard.loadTariff();
    const stale = structuredClone(fixture.stored);
    await fixture.dashboard.configureTariff({
      revision: stale.revision,
      tariff_type: "dynamic",
    });
    resolve(stale);
    expect((await read).tariff_type).toBe("dynamic");
    expect(fixture.dashboard.tariff.value?.tariff_type).toBe("dynamic");
  });
  it("shows the legacy fallback without a second automation when dynamic is selected even with both native switches off", async () => {
    const fixture = await mount({ type: "dynamic", legacy: true });
    expect(fixture.root.textContent).toContain("Aktiver Tarif: Dynamisch");
    expect(fixture.root.querySelector("input,form")).toBeNull();
    expect(fixture.root.querySelector("a")?.getAttribute("href")).toBe(
      "/sax-power-vue/stromtarif",
    );
  });
  it.each(["dynamic", "time_of_use"])(
    "unlocks controls after an external tariff switch closes the %s editor",
    async (type) => {
      const fixture = await mount({ type });
      const section = fixture.root.querySelector(
        type === "dynamic" ? ".electricity-prices" : ".tariff-plan",
      )!;
      await click(section, "Bearbeiten");
      expect(button(fixture.root, "Tarif wechseln").disabled).toBe(true);
      fixture.stored.tariff_type =
        type === "dynamic" ? "time_of_use" : "dynamic";
      fixture.stored.revision = "2";
      await fixture.dashboard.loadTariff();
      await flush();
      expect(button(fixture.root, "Tarif wechseln").disabled).toBe(false);
      expect(
        fixture.root.querySelector<HTMLInputElement>(
          ".electricity-master input",
        )?.disabled,
      ).toBe(false);
      expect(fixture.root.textContent).toContain(
        "an anderer Stelle gewechselt",
      );
      expect(
        fixture.root.querySelector(
          ".electricity-price-editor,.tariff-plan__editor",
        ),
      ).toBeNull();
    },
  );
  it("ignores a delayed series after an external change to an unsupported tariff", async () => {
    const fixture = await mount({ type: "dynamic" });
    let resolve!: (series: TariffPriceSeries) => void;
    fixture.callWS.mockImplementationOnce(
      () =>
        new Promise<TariffPriceSeries>((done) => {
          resolve = done;
        }),
    );
    await click(fixture.root, "Morgen");
    fixture.stored.tariff_type = "fixed";
    fixture.stored.revision = "2";
    await fixture.dashboard.loadTariff();
    await flush();
    resolve({ ...sampleSeries("tomorrow"), tariff_type: "dynamic" });
    await flush();
    expect(fixture.root.querySelector(".tariff-price-chart svg")).toBeNull();
    expect(
      fixture.root.querySelector(".electricity-current-price")?.textContent,
    ).toContain("Nicht verfügbar");
  });
  it("loads tomorrow prices on demand and preserves a missing tomorrow as unavailable", async () => {
    const fixture = await mount({ type: "dynamic" });
    fixture.callWS.mockResolvedValueOnce({
      ...sampleSeries("tomorrow"),
      tariff_type: "dynamic",
      slots: [],
      status: "unavailable",
    });
    await click(fixture.root, "Morgen");
    expect(fixture.callWS).toHaveBeenLastCalledWith({
      type: "sax_power/dashboard/tariff/series",
      entry_id: "entry-1",
      day: "tomorrow",
    });
    expect(fixture.root.textContent).toContain("noch keine Preise verfügbar");
    expect(fixture.root.querySelector("svg")).toBeNull();
  });
  it("displays the server calendar date independently of browser and HA time zones", async () => {
    const fixture = await mount({ type: "dynamic" });
    fixture.callWS.mockResolvedValueOnce({
      ...sampleSeries("tomorrow"),
      tariff_type: "dynamic",
      time_zone: "Pacific/Kiritimati",
    });
    await click(fixture.root, "Morgen");
    expect(
      fixture.root.querySelector(".electricity-day")?.textContent,
    ).toContain("13.09.2026");
  });
  it("edits dynamic sources and cents with explicit save and cancellation", async () => {
    const fixture = await mount({ type: "dynamic" });
    const section = fixture.root.querySelector(".electricity-prices")!;
    await click(section, "Bearbeiten");
    await fill(section, '[name="dynamic_feed"]', "9,25");
    expect(writes(fixture)).toHaveLength(0);
    await click(section, "Speichern");
    expect(section.querySelector("form")).toBeNull();
    expect(writes(fixture)[0]?.[0].profile).toEqual({
      ...initialProfile().profiles!.dynamic,
      feed_in_price_ct_kwh: 9.25,
    });
    await click(section, "Bearbeiten");
    await fill(section, '[name="dynamic_feed"]', "99");
    await click(section, "Abbrechen");
    expect(writes(fixture)).toHaveLength(1);
  });
  it.each(["de", "en"])(
    "rejects fractional PV shares locally and keeps the draft in %s",
    async (language) => {
      const fixture = await mount({ type: "dynamic", language });
      const section = fixture.root.querySelector(".electricity-prices")!;
      await click(section, language === "de" ? "Bearbeiten" : "Edit");
      await fill(section, '[name="dynamic_feed"]', "9,25");
      await fill(section, '[name="dynamic_pv_factor"]', "50.5");
      await click(section, language === "de" ? "Speichern" : "Save");
      expect(writes(fixture)).toHaveLength(0);
      expect(section.querySelector("form")).not.toBeNull();
      expect(fixture.root.textContent).toContain(
        language === "de"
          ? "Bitte einen ganzen PV-Anteil von 0 bis 100 % eingeben."
          : "Enter a whole PV percentage from 0 to 100%.",
      );
      expect(
        section.querySelector<HTMLInputElement>('[name="dynamic_feed"]')?.value,
      ).toBe("9,25");
      await fill(section, '[name="dynamic_pv_factor"]', "50");
      await click(section, language === "de" ? "Speichern" : "Save");
      expect(writes(fixture)).toHaveLength(1);
      expect(writes(fixture)[0]?.[0].profile).toMatchObject({
        pv_factor: 50,
        feed_in_price_ct_kwh: 9.25,
      });
    },
  );
  it.each(["conflict", "invalid_tariff", "forbidden"])(
    "keeps a dynamic draft on %s",
    async (code) => {
      const fixture = await mount({ type: "dynamic" });
      const section = fixture.root.querySelector(".electricity-prices")!;
      await click(section, "Bearbeiten");
      await fill(section, '[name="dynamic_feed"]', "9,25");
      fixture.callWS.mockRejectedValueOnce({ code });
      await click(section, "Speichern");
      expect(
        section.querySelector<HTMLInputElement>('[name="dynamic_feed"]')?.value,
      ).toBe("9,25");
      expect(fixture.root.querySelector('[role="alert"]')).not.toBeNull();
    },
  );
  // REQ-VUE-ELECTRICITY-TARIFF / #244: a server guard never discards the price draft.
  it.each([
    ["time_of_use", "de"],
    ["time_of_use", "en"],
    ["dynamic", "de"],
    ["dynamic", "en"],
  ])(
    "explains the required PV start source and preserves the %s draft in %s",
    async (type, language) => {
      const fixture = await mount({ type, language });
      const english = language === "en";
      const profile =
        type === "dynamic"
          ? fixture.stored.profiles!.dynamic
          : fixture.stored.profiles!.time_of_use;
      profile.pv_sensor = "sensor.market_price";
      await fixture.update("bridge_charge_enabled", "on");
      const section = fixture.root.querySelector(
        type === "dynamic" ? ".electricity-prices" : ".tariff-plan",
      )!;
      await click(section, english ? "Edit" : "Bearbeiten");
      const field =
        type === "dynamic" ? '[name="dynamic_feed"]' : '[name="base_price"]';
      await fill(section, field, english ? "9.25" : "9,25");
      const source = section.querySelectorAll<HTMLSelectElement>(
        ".sensor-picker select",
      )[type === "dynamic" ? 1 : 0]!;
      expect(source.value).toBe("sensor.market_price");
      if (type === "time_of_use")
        expect(source.closest("label")?.textContent).toContain(
          english ? "(required)" : "(erforderlich)",
        );
      source.value = "";
      source.dispatchEvent(new Event("change", { bubbles: true }));
      await flush();
      fixture.callWS.mockRejectedValueOnce({
        code: "bridge_pv_start_required",
      });
      await click(section, english ? "Save" : "Speichern");
      expect(
        fixture.root.querySelector('[role="alert"]')?.textContent,
      ).toContain(
        english
          ? "Choose a source or turn off this charging plan first."
          : "Wähle eine Quelle oder schalte diese Ladeplanung zuerst aus.",
      );
      expect(section.querySelector<HTMLInputElement>(field)?.value).toBe(
        english ? "9.25" : "9,25",
      );
      expect(source.value).toBe("");
      expect(writes(fixture)).toHaveLength(1);
      expect(writes(fixture)[0]?.[0].profile).toMatchObject({
        pv_sensor: null,
      });
      expect(profile.pv_sensor).toBe("sensor.market_price");
      expect(fixture.callService).not.toHaveBeenCalled();
      source.value = "sensor.market_price";
      source.dispatchEvent(new Event("change", { bubbles: true }));
      await flush();
      await click(section, english ? "Save" : "Speichern");
      expect(section.querySelector("form")).toBeNull();
      expect(writes(fixture)[1]?.[0].profile).toMatchObject({
        pv_sensor: "sensor.market_price",
      });
    },
  );
  it("blocks tariff writes for readers and while disconnected", async () => {
    const reader = await mount({ readonly: true });
    expect(button(reader.root, "Tarif wechseln").disabled).toBe(true);
    const fixture = await mount({ type: "dynamic" });
    await click(
      fixture.root.querySelector(".electricity-prices")!,
      "Bearbeiten",
    );
    await fixture.disconnect();
    expect(button(fixture.root, "Speichern").disabled).toBe(true);
    expect(writes(fixture)).toHaveLength(0);
  });
  it("separates global SOC and TOU target/minimum, then collapses charging settings", async () => {
    const fixture = await mount();
    const section = fixture.root.querySelector(".electricity-charging")!;
    await click(section, "Bearbeiten");
    expect(section.textContent).toContain("Globale SOC-Obergrenze");
    expect(section.textContent).toContain("Zeitvariables Ladeziel");
    expect(section.textContent).toContain("Startschwelle der Netzladung");
    expect(section.textContent).toContain("Aktive Monate");
    await click(section, "Fertig");
    expect(section.querySelector(".electricity-charging-editor")).toBeNull();
  });
  it("keeps neutral price available and shows the hours budget for relative and smart strategies", async () => {
    const fixture = await mount({ type: "dynamic" });
    const section = fixture.root.querySelector(".electricity-charging")!;
    await click(section, "Bearbeiten");
    expect(section.textContent).toContain("Netzbezug und Laden bis");
    expect(section.textContent).not.toContain("Anzahl Stunden");
    await fixture.update("price_charge_strategy", "smart");
    expect(section.textContent).toContain("Anzahl Stunden");
    expect(section.textContent).toContain("Smart nutzt das Stundenbudget");
    expect(section.textContent).toContain("Netzbezug ohne Laden bis");
    expect(section.textContent).not.toContain("Netzbezug und Laden bis");
  });
});
describe("REQ-VUE-ELECTRICITY-TARIFF: exact price steps and gaps", () => {
  it("draws separate paths across gaps and keeps negative prices below zero", () => {
    const chart = tariffChart(sampleSeries());
    expect(chart.path.match(/M/g)).toHaveLength(2);
    expect(chart.path).toContain(" V ");
    expect(chart.y(-2.5)).toBeGreaterThan(chart.y(0));
    expect(chart.ticks).toContain(0);
    expect(chart.ticks).toEqual([...chart.ticks].sort((a, b) => a - b));
    expect(chart.slots).toHaveLength(3);
  });
  it("distinguishes the repeated autumn hour only on a daylight-saving transition day", async () => {
    const root = document.createElement("div");
    document.body.append(root);
    const value = shallowRef<TariffPriceSeries>({
      ...sampleSeries(),
      start: "2026-10-25T00:00:00+02:00",
      end: "2026-10-26T00:00:00+01:00",
      slots: [
        {
          start: "2026-10-25T02:00:00+02:00",
          end: "2026-10-25T02:00:00+01:00",
          price_ct_kwh: 5,
        },
      ],
    });
    const app = createApp({
      render: () =>
        h(TariffPriceChart, {
          series: value.value,
          hass: { language: "de", states: {} },
        }),
    });
    apps.push(app);
    app.mount(root);
    await flush();
    expect(root.querySelector("table")?.textContent).toContain("02:00 GMT+2");
    expect(root.querySelector("table")?.textContent).toContain("02:00 GMT+1");
    root
      .querySelector("svg")
      ?.dispatchEvent(new KeyboardEvent("keydown", { key: "Home" }));
    await flush();
    expect(
      root.querySelector(".tariff-price-chart__detail")?.textContent,
    ).toContain("02:00 GMT+2–02:00 GMT+1");
    value.value = sampleSeries();
    await flush();
    expect(root.querySelector("table")?.textContent).not.toContain("GMT");
  });
  it("does not display invalid overlapping intervals", () => {
    const series = sampleSeries();
    series.slots[1]!.start = series.slots[0]!.start;
    expect(tariffChart(series).slots).toHaveLength(0);
  });
  it("uses actual 23-hour daylight-saving day bounds", () => {
    const series = {
      ...sampleSeries(),
      start: "2026-03-29T00:00:00+01:00",
      end: "2026-03-30T00:00:00+02:00",
      slots: [],
    };
    const chart = tariffChart(series, 320);
    expect(chart.end - chart.start).toBe(23 * 3600000);
    expect(chart.x(chart.start)).toBe(48);
    expect(chart.x(chart.end)).toBe(308);
  });
});
