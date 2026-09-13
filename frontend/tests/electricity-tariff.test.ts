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
  if (options.readonly)
    sample.metadata.forEach((item) => {
      item.can_control = false;
    });
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
    expect(fixture.root.textContent).toContain(
      "Ausgeschaltet: Diese Automatik",
    );
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
      expect(section.querySelector<HTMLDetailsElement>("details")?.open).toBe(
        true,
      );
      const factorInput = section.querySelector('[name="dynamic_pv_factor"]');
      expect(factorInput?.getAttribute("aria-invalid")).toBe("true");
      expect(document.activeElement).toBe(factorInput);
      await fill(section, '[name="dynamic_pv_factor"]', "50");
      await click(section, language === "de" ? "Speichern" : "Save");
      expect(writes(fixture)).toHaveLength(1);
      expect(writes(fixture)[0]?.[0].profile).toMatchObject({
        pv_factor: 50,
        feed_in_price_ct_kwh: 9.25,
      });
    },
  );
  it.each([
    ["de", "0", 0],
    ["en", "0", 0],
    ["de", "7,86", 7.86],
    ["en", "7.86", 7.86],
  ])(
    "keeps the EPEX euro source and identifies its missing feed-in price in %s, then accepts %s",
    async (language, input, expected) => {
      const fixture = await mount({
        type: "dynamic",
        language: String(language),
      });
      const epex = "sensor.epex_spot_data_market_price";
      fixture.stored.profiles!.dynamic = {
        ...fixture.stored.profiles!.dynamic,
        price_sensor: null,
        price_unit: "auto",
        feed_in_price_ct_kwh: null,
      };
      fixture.hass.value = {
        ...fixture.hass.value,
        states: {
          ...fixture.hass.value.states,
          [epex]: {
            entity_id: epex,
            state: "0.179",
            attributes: {
              friendly_name: "EPEX Spot Data Market Price",
              unit_of_measurement: "€/kWh",
              data: [
                {
                  start_time: "2026-09-13T12:30:00+02:00",
                  end_time: "2026-09-13T12:45:00+02:00",
                  price_per_kwh: 0.179,
                },
              ],
            },
          },
        },
      };
      const section = fixture.root.querySelector(".electricity-prices")!;
      await click(section, language === "de" ? "Bearbeiten" : "Edit");
      const source = section.querySelector<HTMLSelectElement>(
        '[name="dynamic_price_sensor"]',
      )!;
      source.value = epex;
      source.dispatchEvent(new Event("change", { bubbles: true }));
      await flush();
      await click(section, language === "de" ? "Speichern" : "Save");
      expect(writes(fixture)).toHaveLength(0);
      expect(source.value).toBe(epex);
      expect(source.getAttribute("aria-invalid")).toBeNull();
      const feed = section.querySelector<HTMLInputElement>(
        '[name="dynamic_feed"]',
      )!;
      const alert = section.querySelector('[role="alert"]')!;
      expect(feed.value).toBe("");
      expect(feed.getAttribute("aria-invalid")).toBe("true");
      expect(feed.getAttribute("aria-describedby")).toBe(alert.id);
      expect(document.activeElement).toBe(feed);
      expect(alert.textContent).toContain(
        language === "de"
          ? "Bitte die Einspeisevergütung in ct/kWh eintragen."
          : "Please enter the feed-in remuneration in ct/kWh.",
      );
      expect(alert.textContent).toContain(
        language === "de"
          ? "Wenn du keine Vergütung erhältst, trage 0 ein."
          : "Enter 0 if you receive no remuneration.",
      );
      expect(alert.textContent).not.toContain("Preisquelle");
      expect(alert.textContent).not.toContain("price source");
      await fill(section, '[name="dynamic_feed"]', String(input));
      await click(section, language === "de" ? "Speichern" : "Save");
      expect(writes(fixture)).toHaveLength(1);
      expect(writes(fixture)[0]?.[0].profile).toMatchObject({
        price_sensor: epex,
        price_unit: "auto",
        feed_in_price_ct_kwh: expected,
      });
      expect(section.querySelector("form")).toBeNull();
    },
  );
  it.each(["de", "en"])(
    "marks the source only when no source was selected in %s",
    async (language) => {
      const fixture = await mount({ type: "dynamic", language });
      fixture.stored.profiles!.dynamic.price_sensor = null;
      const section = fixture.root.querySelector(".electricity-prices")!;
      await click(section, language === "de" ? "Bearbeiten" : "Edit");
      await click(section, language === "de" ? "Speichern" : "Save");
      expect(writes(fixture)).toHaveLength(0);
      const source = section.querySelector('[name="dynamic_price_sensor"]');
      expect(source?.getAttribute("aria-invalid")).toBe("true");
      expect(document.activeElement).toBe(source);
      expect(section.querySelector('[role="alert"]')?.textContent).toBe(
        language === "de"
          ? "Bitte einen Strompreis-Sensor auswählen."
          : "Please select an electricity price sensor.",
      );
    },
  );
  it.each(["-1", "201", "7.861", "NaN"])(
    "identifies invalid feed-in price %s without discarding or blaming the sensor",
    async (value) => {
      const fixture = await mount({ type: "dynamic" });
      const section = fixture.root.querySelector(".electricity-prices")!;
      await click(section, "Bearbeiten");
      await fill(section, '[name="dynamic_feed"]', value);
      await click(section, "Speichern");
      expect(writes(fixture)).toHaveLength(0);
      expect(section.querySelector('[role="alert"]')?.textContent).toContain(
        "Bitte die Einspeisevergütung als Zahl von 0 bis 200 ct/kWh",
      );
      const feed = section.querySelector<HTMLInputElement>(
        '[name="dynamic_feed"]',
      )!;
      expect(feed.value).toBe(value);
      expect(document.activeElement).toBe(feed);
      expect(
        section.querySelector<HTMLSelectElement>(
          '[name="dynamic_price_sensor"]',
        )?.value,
      ).toBe("sensor.market_price");
    },
  );
  it.each(
    ["de", "en"].flatMap((language) =>
      [
        [
          "price_sensor_not_configured",
          "price_sensor",
          "Strompreis-Sensor",
          "electricity price sensor",
        ],
        ["price_sensor_missing", "price_sensor", "nicht gefunden", "not found"],
        ["price_unit_unsupported", "price_unit", "Einheit", "unit"],
        [
          "pv_sensor_missing",
          "pv_sensor",
          "PV-Prognose-Sensor",
          "PV forecast sensor",
        ],
        [
          "invalid_price_attribute",
          "price_attribute",
          "Attributnamen",
          "attribute name",
        ],
        [
          "invalid_feed_in_price",
          "feed",
          "Einspeisevergütung",
          "feed-in remuneration",
        ],
        ["invalid_pv_factor", "pv_factor", "PV-Anteil", "PV percentage"],
      ].map(([code, field, german, english]) => [
        language,
        code,
        field,
        language === "de" ? german : english,
      ]),
    ),
  )(
    "focuses the field behind %s error %s and preserves the draft",
    async (language, code, field, expected) => {
      const fixture = await mount({ type: "dynamic", language });
      const section = fixture.root.querySelector(".electricity-prices")!;
      await click(section, language === "de" ? "Bearbeiten" : "Edit");
      await fill(section, '[name="dynamic_feed"]', "9,25");
      fixture.callWS.mockRejectedValueOnce({ code });
      await click(section, language === "de" ? "Speichern" : "Save");
      const input = section.querySelector(`[name="dynamic_${field}"]`)!;
      expect(input.getAttribute("aria-invalid")).toBe("true");
      expect(document.activeElement).toBe(input);
      const alert = section.querySelector('[role="alert"]')!;
      expect(alert.textContent).toContain(expected);
      expect(input.getAttribute("aria-describedby")).toBe(alert.id);
      if (input.closest("details"))
        expect(input.closest("details")?.open).toBe(true);
      expect(
        section.querySelector<HTMLInputElement>('[name="dynamic_feed"]')?.value,
      ).toBe("9,25");
      expect(
        section.querySelector<HTMLSelectElement>(
          '[name="dynamic_price_sensor"]',
        )?.value,
      ).toBe("sensor.market_price");
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
    expect(section.textContent).toContain("Ladegrenze für alle Lademethoden");
    expect(section.textContent).toContain("Ladeziel (%)");
    expect(section.textContent).toContain("Nur starten unter einem Ladestand");
    expect(section.textContent).toContain("Aktive Monate");
    await click(section, "Fertig");
    expect(section.querySelector(".electricity-charging-editor")).toBeNull();
  });
  it.each(["de", "en"])(
    "guides charging choices with relevant fields and accurate effects in %s",
    async (language) => {
      const fixture = await mount({ type: "dynamic", language });
      const section = fixture.root.querySelector(".electricity-charging")!;
      await click(section, language === "de" ? "Bearbeiten" : "Edit");
      const english = language === "en";
      expect(section.querySelectorAll("[data-strategy]")).toHaveLength(4);
      expect(section.textContent).toContain(
        english ? "Maximum price for charging" : "Höchster Preis zum Laden",
      );
      expect(section.textContent).not.toContain(
        english ? "Maximum charging time" : "Maximale Ladezeit",
      );
      expect(
        section.querySelector<HTMLDetailsElement>(".dynamic-charging-advanced")
          ?.open,
      ).toBe(false);
      expect(
        section.querySelector(".dynamic-charging-neutral-summary")?.textContent,
      ).toContain("30 ct/kWh");
      await fixture.update("price_charge_strategy", "smart");
      expect(section.textContent).toContain(
        english
          ? "Maximum charging time per 24 hours"
          : "Maximale Ladezeit je 24 Stunden",
      );
      expect(section.textContent).toContain(
        english
          ? "battery level, capacity or charging power is missing"
          : "Fehlen Ladestand, Kapazität oder Ladeleistung",
      );
      expect(section.textContent).toContain(
        english
          ? "a single current price is not enough"
          : "ein einzelner aktueller Preis reicht nicht",
      );
      expect(section.textContent).toContain(
        english ? "Without a solar forecast" : "Ohne PV-Prognose",
      );
      expect(section.textContent).not.toContain(
        english ? "Maximum price for charging" : "Höchster Preis zum Laden",
      );
      expect(
        section.querySelector(".dynamic-charging-summary")?.textContent,
      ).toContain("4 h");
      expect(
        section.querySelector(".dynamic-charging-summary")?.textContent,
      ).toContain("80 %");
      await fixture.update("price_charge_strategy", "relative");
      expect(section.textContent).toContain(
        english
          ? "even the cheapest available hours may be expensive"
          : "Auch die günstigsten verfügbaren Stunden können teuer sein",
      );
      expect(section.textContent).not.toContain(
        english ? "Without a solar forecast" : "Ohne PV-Prognose",
      );
      await fixture.update("price_charge_strategy", "off");
      expect(section.querySelector(".entity-control")).toBeNull();
      expect(section.textContent).toContain(
        english
          ? "even when the main switch is on"
          : "auch wenn der Hauptschalter eingeschaltet ist",
      );
      expect(fixture.callService).not.toHaveBeenCalled();
      expect(writes(fixture)).toHaveLength(0);
    },
  );
  it("shows an ineffective neutral threshold and preserves its value across methods", async () => {
    const fixture = await mount({ type: "dynamic" });
    await fixture.update("price_charge_neutral_price", "-10");
    const section = fixture.root.querySelector(".electricity-charging")!;
    expect(
      section.querySelector(".dynamic-charging-neutral-summary")?.textContent,
    ).toContain("ohne Wirkung");
    await fixture.update("price_charge_strategy", "relative");
    expect(
      section.querySelector(".dynamic-charging-neutral-summary")?.textContent,
    ).toContain("-10 ct/kWh");
    expect(fixture.callService).not.toHaveBeenCalled();
  });
  it.each(["", " ", "unavailable", "invalid"])(
    "does not infer a neutral threshold from %s",
    async (state) => {
      const fixture = await mount({ type: "dynamic" });
      await fixture.update("price_charge_neutral_price", state);
      const summary = fixture.root.querySelector(
        ".dynamic-charging-neutral-summary",
      )!;
      expect(summary.textContent).toContain("nicht verfügbar");
      expect(summary.textContent).not.toContain("ohne Wirkung");
      expect(summary.textContent).not.toContain("0 ct/kWh");
    },
  );
  it.each(["smart", "relative", "off"])(
    "sends %s through the existing select service without an optimistic selection",
    async (method) => {
      const fixture = await mount({ type: "dynamic" });
      const section = fixture.root.querySelector(".electricity-charging")!;
      await click(section, "Bearbeiten");
      let resolve!: () => void;
      fixture.callService.mockImplementationOnce(
        () =>
          new Promise<void>((done) => {
            resolve = done;
          }),
      );
      const choice = section.querySelector<HTMLButtonElement>(
        `[data-strategy="${method}"]`,
      )!;
      choice.click();
      await flush();
      expect(
        section
          .querySelector('[data-strategy="absolute"]')
          ?.getAttribute("aria-pressed"),
      ).toBe("true");
      expect(choice.getAttribute("aria-pressed")).toBe("false");
      expect(choice.disabled).toBe(true);
      expect(section.querySelector('[aria-busy="true"]')).not.toBeNull();
      expect(section.textContent).toContain("Ladeweise wird übernommen …");
      choice.click();
      expect(fixture.callService).toHaveBeenCalledTimes(1);
      expect(fixture.callService).toHaveBeenCalledWith(
        "select",
        "select_option",
        { option: method },
        { entity_id: "select.renamed_price_charge_strategy" },
        false,
      );
      resolve();
      await flush();
      expect(choice.getAttribute("aria-pressed")).toBe("false");
      await fixture.update("price_charge_strategy", method);
      expect(choice.getAttribute("aria-pressed")).toBe("true");
      expect(writes(fixture)).toHaveLength(0);
    },
  );
  it("keeps charge target, hours and neutral values on their existing number services", async () => {
    const fixture = await mount({ type: "dynamic" });
    await fixture.update("price_charge_strategy", "smart");
    const section = fixture.root.querySelector(".electricity-charging")!;
    await click(section, "Bearbeiten");
    for (const [label, key, value] of [
      ["Ladeziel (%)", "max_soc", "85"],
      ["Maximale Ladezeit je 24 Stunden", "price_charge_hours", "3"],
      [
        "Speicher bei günstigem Strom schonen bis (ct/kWh)",
        "price_charge_neutral_price",
        "12.5",
      ],
    ]) {
      const form = [...section.querySelectorAll(".entity-control")].find(
        (form) => form.querySelector("label")?.textContent === label,
      )!;
      await fill(form, "input", value!);
      await click(form, "Übernehmen");
      expect(fixture.callService).toHaveBeenLastCalledWith(
        "number",
        "set_value",
        { value: Number(value) },
        { entity_id: `number.renamed_${key}` },
        false,
      );
    }
    expect(writes(fixture)).toHaveLength(0);
  });
  it.each([
    ["dynamic", "strategy"],
    ["dynamic", "number"],
    ["time_of_use", "number"],
  ])(
    "keeps pending changes and late failures visible after closing %s %s settings",
    async (type, control) => {
      const fixture = await mount({ type });
      const section = fixture.root.querySelector(".electricity-charging")!;
      await click(section, "Bearbeiten");
      let reject!: (cause: unknown) => void;
      fixture.callService.mockImplementationOnce(
        () =>
          new Promise<void>((_, fail) => {
            reject = fail;
          }),
      );
      if (control === "strategy") {
        section
          .querySelector<HTMLButtonElement>('[data-strategy="relative"]')!
          .click();
        await flush();
      } else {
        const form = section.querySelector(".entity-control")!;
        await fill(form, "input", "85");
        await click(form, "Übernehmen");
      }
      await click(section, "Fertig");
      expect(section.querySelector(".electricity-charging-editor")).toBeNull();
      expect(section.querySelector('[role="status"]')?.textContent).toContain(
        control === "strategy"
          ? "Ladeweise wird übernommen"
          : "Änderung wird an Home Assistant gesendet",
      );
      reject(new Error("Service failed"));
      await flush();
      expect(section.querySelector('[role="status"]')).toBeNull();
      expect(section.querySelector('[role="alert"]')?.textContent).toContain(
        "fehlgeschlagen",
      );
      if (control === "strategy")
        expect(
          section.querySelector(".dynamic-charging-summary")?.textContent,
        ).toContain("Bis zu einem festen Preis laden");
      expect(fixture.callService).toHaveBeenCalledTimes(1);
    },
  );
  it.each(["de", "en"])(
    "explains the required solar forecast quantity and date in %s",
    async (language) => {
      const fixture = await mount({ type: "dynamic", language });
      const section = fixture.root.querySelector(".electricity-prices")!;
      await click(section, language === "de" ? "Bearbeiten" : "Edit");
      expect(section.textContent).toContain(
        language === "de"
          ? "PV-Gesamtertrag für morgen als Energie in kWh oder Wh"
          : "total solar energy forecast for tomorrow in kWh or Wh",
      );
      expect(section.textContent).toContain(
        language === "de"
          ? "keine aktuelle Leistung und keinen heutigen Restertrag"
          : "not current power or today's remaining production",
      );
    },
  );
  it("keeps custom price settings visible as a summary and preserves them when saving basic fields", async () => {
    const fixture = await mount({ type: "dynamic" });
    fixture.stored.profiles!.dynamic.price_attribute = "raw_today";
    const section = fixture.root.querySelector(".electricity-prices")!;
    await click(section, "Bearbeiten");
    expect(
      section.querySelector<HTMLDetailsElement>(".electricity-price-advanced")
        ?.open,
    ).toBe(false);
    expect(
      section.querySelector(".electricity-additional-settings")?.textContent,
    ).toContain("raw_today");
    expect(
      section.querySelector(".electricity-additional-settings")?.textContent,
    ).toContain("70");
    await fill(section, '[name="dynamic_feed"]', "8.5");
    await click(section, "Speichern");
    expect(writes(fixture)[0]?.[0].profile).toMatchObject({
      price_attribute: "raw_today",
      price_unit: "ct_kwh",
      pv_factor: 70,
      feed_in_price_ct_kwh: 8.5,
    });
  });
  it.each(["readonly", "unavailable", "disconnected"])(
    "prevents changing the charging method when %s",
    async (state) => {
      const fixture = await mount({
        type: "dynamic",
        readonly: state === "readonly",
      });
      if (state === "unavailable")
        await fixture.update("price_charge_strategy", "unavailable");
      if (state === "disconnected") await fixture.disconnect();
      await click(
        fixture.root.querySelector(".electricity-charging")!,
        "Bearbeiten",
      );
      expect(
        [
          ...fixture.root.querySelectorAll<HTMLButtonElement>(
            "[data-strategy]",
          ),
        ].every((choice) => choice.disabled),
      ).toBe(true);
      if (state !== "readonly")
        expect(
          fixture.root.querySelector('[data-strategy][aria-pressed="true"]'),
        ).toBeNull();
      expect(fixture.callService).not.toHaveBeenCalled();
    },
  );
  it("reports delayed automation changes immediately and preserves the confirmed switch on failure", async () => {
    const fixture = await mount({ type: "dynamic" });
    let reject!: (cause: unknown) => void;
    fixture.callWS.mockImplementationOnce(
      () =>
        new Promise<TariffProfile>((_, fail) => {
          reject = fail;
        }),
    );
    const master = fixture.root.querySelector<HTMLInputElement>(
      ".electricity-master input",
    )!;
    master.click();
    await flush();
    expect(master.checked).toBe(false);
    expect(master.disabled).toBe(true);
    expect(master.closest("label")?.getAttribute("aria-busy")).toBe("true");
    expect(
      fixture.root.querySelector(".electricity-master-status")?.textContent,
    ).toContain("Einschalten wird übernommen …");
    master.click();
    expect(writes(fixture)).toHaveLength(1);
    reject({ code: "failed" });
    await flush();
    expect(master.checked).toBe(false);
    expect(master.disabled).toBe(false);
    expect(
      fixture.root.querySelector(".electricity-master-status")?.textContent,
    ).toBe("");
    expect(fixture.root.querySelector('[role="alert"]')?.textContent).toContain(
      "fehlgeschlagen",
    );
  });
});
describe("REQ-VUE-ELECTRICITY-TARIFF: activation feedback beside step 3", () => {
  it.each(["failed", "conflict"])(
    "keeps delayed %s feedback and recovery beside the confirmed time-of-use switch",
    async (code) => {
      const fixture = await mount();
      let reject!: (cause: unknown) => void;
      fixture.callWS.mockImplementationOnce(
        () =>
          new Promise<TariffProfile>((_, fail) => {
            reject = fail;
          }),
      );
      const section = fixture.root.querySelector(".electricity-activation")!;
      const master = section.querySelector<HTMLInputElement>("input")!;
      master.click();
      await flush();
      expect(master.checked).toBe(false);
      expect(master.disabled).toBe(true);
      expect(section.querySelector("[role=status]")?.textContent).toContain(
        "Einschalten wird übernommen",
      );
      master.click();
      expect(writes(fixture)).toHaveLength(1);
      reject({ code });
      await flush();
      expect(master.checked).toBe(false);
      expect(master.disabled).toBe(false);
      const alert = section.querySelector<HTMLElement>("[role=alert]")!;
      expect(alert.textContent).toContain(
        code === "conflict" ? "inzwischen geändert" : "fehlgeschlagen",
      );
      expect(master.getAttribute("aria-describedby")).toContain(alert.id);
      expect(
        fixture.root.querySelector(".electricity-tariff-bar [role=alert]"),
      ).toBeNull();
      if (code === "conflict") {
        const reload = button(
          section,
          "Gespeicherte Einstellungen laden (Entwurf verwerfen)",
        );
        expect(reload).toBeTruthy();
        reload.click();
        await flush();
        expect(section.querySelector("[role=alert]")).toBeNull();
      }
    },
  );

  it.each(["readonly", "disconnected"])(
    "explains %s beside the unavailable activation switch",
    async (reason) => {
      const fixture = await mount({ readonly: reason === "readonly" });
      if (reason === "disconnected") await fixture.disconnect();
      const section = fixture.root.querySelector(".electricity-activation")!;
      expect(section.querySelector<HTMLInputElement>("input")?.disabled).toBe(
        true,
      );
      expect(section.textContent).toContain(
        reason === "readonly" ? "Keine Berechtigung" : "Keine Verbindung",
      );
      expect(writes(fixture)).toHaveLength(0);
    },
  );
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
