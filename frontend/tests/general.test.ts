import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import GeneralView from "../src/views/GeneralView.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "../src/ha";
import type {
  DashboardEntityMetadata,
  DashboardMetadata,
  EntityDomain,
  HassConnection,
  HassEntity,
  HomeAssistant,
} from "../src/types";

const applications: App[] = [];
const entities: readonly (readonly [EntityDomain, string])[] = [
  ["sensor", "soc"],
  ["sensor", "storage_max_cell_temp"],
  ["switch", "storage_switch"],
  ["number", "max_soc"],
  ["sensor", "charge_power"],
  ["sensor", "discharge_power"],
  ["sensor", "smartmeter_power"],
  ["sensor", "energy_charged"],
  ["sensor", "energy_discharged"],
  ["sensor", "sun_version_master"],
  ["sensor", "sun_version_gateway"],
  ["sensor", "sun_serial_number"],
  ["sensor", "storage_event_text"],
  ["sensor", "ic_control_mode_text"],
  ["binary_sensor", "cell_calibration_active"],
  ["sensor", "next_cell_calibration"],
];
const names: Record<string, string> = {
  soc: "Ladezustand",
  storage_max_cell_temp: "Max. Zelltemperatur",
  storage_switch: "Speicher",
  max_soc: "Max. Ladezustand",
  charge_power: "Ladeleistung",
  discharge_power: "Entladeleistung",
  smartmeter_power: "Netzleistung",
  energy_charged: "Energie geladen",
  energy_discharged: "Energie entladen",
  sun_version_master: "Firmware Master",
  sun_version_gateway: "Firmware Gateway",
  sun_serial_number: "Seriennummer",
  storage_event_text: "Speicherereignis",
  ic_control_mode_text: "Steuermodus",
  cell_calibration_active: "Zellkalibrierung aktiv",
  next_cell_calibration: "Nächste Zellkalibrierung",
};

async function flush(): Promise<void> {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}

async function mount(
  options: {
    keys?: string[];
    language?: string;
    deferMetadata?: boolean;
    values?: Record<string, string>;
  } = {},
) {
  const selected = entities.filter(
    ([, key]) => !options.keys || options.keys.includes(key),
  );
  const metadata = selected.map(([domain, key]): DashboardEntityMetadata => ({
    domain,
    key,
    entity_id: `${domain}.renamed_${key}`,
    name: names[key],
    states: {},
    can_control: domain === "switch" || domain === "number",
  }));
  const states: Record<string, HassEntity> = Object.fromEntries(
    metadata.map((item) => {
      const attributes =
        item.key === "soc" || item.key === "max_soc"
          ? { unit_of_measurement: "%", min: 0, max: 100, step: 1 }
          : item.key === "storage_max_cell_temp"
            ? { unit_of_measurement: "°C" }
            : item.key.includes("power")
              ? { unit_of_measurement: "W" }
              : item.key.startsWith("energy_")
                ? { unit_of_measurement: "kWh" }
                : item.key === "next_cell_calibration"
                  ? { device_class: "timestamp" }
                  : {};
      return [
        item.entity_id,
        {
          entity_id: item.entity_id,
          state:
            options.values?.[item.key] ??
            (item.domain === "switch"
              ? "on"
              : item.domain === "binary_sensor"
                ? "off"
                : item.key === "next_cell_calibration"
                  ? "2026-09-14T05:00:00+00:00"
                  : "42"),
          attributes,
        },
      ];
    }),
  );
  let emitMetadata: (data: DashboardMetadata) => void = () => {};
  const connection: HassConnection = {
    connected: true,
    async subscribeMessage<T>(callback: (message: T) => void) {
      emitMetadata = (data) => callback(data as T);
      if (!options.deferMetadata) emitMetadata({ entities: metadata });
      return () => {};
    },
    addEventListener() {},
    removeEventListener() {},
  };
  const callService = vi
    .fn<NonNullable<HomeAssistant["callService"]>>()
    .mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    connection,
    states,
    callService,
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
      return () => h(GeneralView);
    },
  });
  applications.push(app);
  app.mount(root);
  await flush();
  return {
    root,
    hass,
    callService,
    async emit(items = metadata) {
      emitMetadata({ entities: items });
      await flush();
    },
    async update(key: string, value: string) {
      const entityId = metadata.find((item) => item.key === key)!.entity_id;
      hass.value = {
        ...hass.value,
        states: {
          ...hass.value.states,
          [entityId]: { ...hass.value.states[entityId], state: value },
        },
      };
      await flush();
    },
  };
}

afterEach(() => {
  for (const app of applications.splice(0)) app.unmount();
  document.body.replaceChildren();
});

describe("REQ-VUE-GENERAL: general dashboard view", () => {
  it("preserves every entity and the card order of the existing Lovelace view", async () => {
    const source = readFileSync(
      "../custom_components/sax_power/dashboard.py",
      "utf8",
    );
    const general = source
      .split("general_view = _view(")[1]
      .split("charging_view = _view(")[0];
    const lovelaceEntities = [
      ...general.matchAll(
        /"(sensor|binary_sensor|switch|number)"\s*,\s*"([a-z_]+)"/g,
      ),
    ].map((match) => [match[1], match[2]]);
    expect(entities).toEqual(lovelaceEntities);
    const { root, callService } = await mount();
    expect(
      [
        ...root.querySelectorAll(
          ".entity-gauge h2, .entity-control__name, .entity-value__name",
        ),
      ].map((item) => item.textContent),
    ).toEqual(entities.map(([, key]) => names[key]));
    expect(
      [...root.querySelectorAll(".general-view__card h2")].map(
        (item) => item.textContent,
      ),
    ).toEqual(["Leistung", "Energie", "Gerät"]);
    expect(root.textContent).toContain("Netzleistung");
    expect(root.textContent).toContain("Steuermodus");
    expect(root.querySelectorAll("input")).toHaveLength(2);
    expect(callService).not.toHaveBeenCalled();
  });

  it("shows both scales and the same gauge color ranges as Lovelace", async () => {
    const { root } = await mount({
      keys: ["soc", "storage_max_cell_temp"],
      values: { soc: "50", storage_max_cell_temp: "32" },
    });
    const meters = root.querySelectorAll('[role="meter"]');
    expect(
      [...meters].map((item) => [
        item.getAttribute("aria-valuemin"),
        item.getAttribute("aria-valuemax"),
        item.getAttribute("aria-valuenow"),
        item.getAttribute("aria-valuetext"),
      ]),
    ).toEqual([
      ["0", "100", "50", "50 % · Hoch"],
      ["0", "40", "32", "32 °C · Hoch"],
    ]);
    expect(
      [...meters[0].querySelectorAll(".entity-gauge__segment")].map((item) => [
        item.getAttribute("class")?.split("--")[1],
        item.getAttribute("stroke-dasharray"),
        item.getAttribute("stroke-dashoffset"),
      ]),
    ).toEqual([
      ["red", "20 100", "0"],
      ["yellow", "30 100", "-20"],
      ["green", "50 100", "-50"],
    ]);
    expect(
      [...meters[1].querySelectorAll(".entity-gauge__segment")].map((item) => [
        item.getAttribute("class")?.split("--")[1],
        item.getAttribute("stroke-dasharray"),
        item.getAttribute("stroke-dashoffset"),
      ]),
    ).toEqual([
      ["red", "12.5 100", "0"],
      ["green", "67.5 100", "-12.5"],
      ["red", "20 100", "-80"],
    ]);
    for (const meter of meters)
      expect(
        root.querySelector(`[id="${meter.getAttribute("aria-labelledby")}"]`)
          ?.textContent,
      ).toBeTruthy();
  });

  it.each([
    [0, "Niedrig"],
    [19.9, "Niedrig"],
    [20, "Mittel"],
    [49.9, "Mittel"],
    [50, "Hoch"],
    [100, "Hoch"],
  ] as const)(
    "positions the SOC needle and describes the range for %s percent",
    async (value, range) => {
      const { root } = await mount({
        keys: ["soc"],
        values: { soc: String(value) },
      });
      expect(
        root.querySelector('[role="meter"]')?.getAttribute("aria-valuenow"),
      ).toBe(String(value));
      expect(
        root.querySelector(".entity-gauge__needle")?.getAttribute("transform"),
      ).toBe(`rotate(${(value / 100) * 180 - 90} 120 110)`);
      expect(root.querySelector(".entity-gauge__range")?.textContent).toBe(
        range,
      );
      expect(
        root.querySelector('[role="meter"]')?.getAttribute("aria-valuetext"),
      ).toContain(range);
    },
  );

  it.each([
    [0, "Niedrig"],
    [4.9, "Niedrig"],
    [5, "Im Bereich"],
    [31.9, "Im Bereich"],
    [32, "Hoch"],
    [40, "Hoch"],
  ] as const)(
    "positions the temperature needle and describes the range for %s degrees",
    async (value, range) => {
      const { root } = await mount({
        keys: ["storage_max_cell_temp"],
        values: { storage_max_cell_temp: String(value) },
      });
      expect(
        root.querySelector('[role="meter"]')?.getAttribute("aria-valuenow"),
      ).toBe(String(value));
      expect(
        root.querySelector(".entity-gauge__needle")?.getAttribute("transform"),
      ).toBe(`rotate(${(value / 40) * 180 - 90} 120 110)`);
      expect(root.querySelector(".entity-gauge__range")?.textContent).toBe(
        range,
      );
      expect(
        root.querySelector('[role="meter"]')?.getAttribute("aria-valuetext"),
      ).toContain(range);
    },
  );

  it.each(["unknown", "unavailable", "", "NaN", "Infinity"])(
    "shows %s without inventing a gauge reading",
    async (state) => {
      const { root } = await mount({ keys: ["soc"], values: { soc: state } });
      expect(root.querySelector('[role="meter"]')).toBeNull();
      expect(root.querySelector(".entity-gauge__needle")).toBeNull();
      expect(root.querySelector(".entity-gauge__range")).toBeNull();
      expect(root.querySelector(".entity-gauge__value")?.textContent).toBe(
        state === "unavailable" ? "Nicht verfügbar" : "Unbekannt",
      );
      expect(
        root.querySelector(".entity-gauge__value")?.textContent,
      ).not.toContain("0");
    },
  );

  it("keeps the actual out-of-scale temperature visible and bounds only the needle", async () => {
    const { root, update } = await mount({
      keys: ["storage_max_cell_temp"],
      values: { storage_max_cell_temp: "-3" },
    });
    expect(
      root.querySelector('[role="meter"]')?.getAttribute("aria-valuenow"),
    ).toBe("0");
    expect(root.textContent).toContain("-3 °C");
    await update("storage_max_cell_temp", "44");
    expect(
      root.querySelector('[role="meter"]')?.getAttribute("aria-valuenow"),
    ).toBe("40");
    expect(root.textContent).toContain("44 °C");
  });

  it("hides absent optional rows and whole empty cards", async () => {
    const { root, emit } = await mount({ keys: ["soc", "charge_power"] });
    expect(root.querySelectorAll(".entity-gauge")).toHaveLength(1);
    expect(root.querySelectorAll(".general-view__card")).toHaveLength(1);
    expect(root.querySelector(".general-view__card h2")?.textContent).toBe(
      "Leistung",
    );
    expect(root.querySelector("input")).toBeNull();
    expect(root.textContent).not.toContain("Gerät");
    await emit([]);
    expect(
      root.querySelectorAll("section, form, .general-view__gauges"),
    ).toHaveLength(0);
    expect(root.querySelector('[role="status"]')?.textContent).toBe(
      "Für diese Ansicht sind keine Entitäten verfügbar.",
    );
  });

  it("distinguishes loading from an empty metadata result", async () => {
    const { root, emit } = await mount({ keys: [], deferMetadata: true });
    expect(root.querySelector('[role="status"]')?.textContent).toBe(
      "Die Entitäten werden geladen …",
    );
    await emit();
    expect(root.querySelector('[role="status"]')?.textContent).toBe(
      "Für diese Ansicht sind keine Entitäten verfügbar.",
    );
  });

  it("uses live HA formatting, enum state, timestamp and renamed entity IDs", async () => {
    const { root, hass, callService, update } = await mount();
    expect(root.textContent).toContain("14.09.2026, 07:00");
    expect(root.textContent).toContain("Aus");
    await update("charge_power", "1250.5");
    expect(root.textContent).toContain("1.250,5 W");
    hass.value = {
      ...hass.value,
      formatEntityState: (entity) => `HA: ${entity.state}`,
    };
    await flush();
    expect(root.textContent).toContain("HA: 1250.5");
    const input = root.querySelector<HTMLInputElement>('input[type="number"]')!;
    input.value = "80";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await flush();
    expect(callService).not.toHaveBeenCalled();
    input
      .closest("form")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flush();
    expect(callService).toHaveBeenCalledExactlyOnceWith(
      "number",
      "set_value",
      { value: 80 },
      { entity_id: "number.renamed_max_soc" },
      false,
    );
    expect(root.textContent).toContain("Bestätigter Wert: HA: 42");
  });

  it("renders English section headings and empty-state copy", async () => {
    const { root, emit } = await mount({ language: "en-GB" });
    expect(
      [...root.querySelectorAll(".general-view__card h2")].map(
        (item) => item.textContent,
      ),
    ).toEqual(["Power", "Energy", "Device"]);
    expect(root.textContent).toContain("Confirmed value");
    expect(
      [...root.querySelectorAll(".entity-gauge__range")].map(
        (item) => item.textContent,
      ),
    ).toEqual(["Medium", "High"]);
    await emit([]);
    expect(root.textContent).toBe("No entities are available for this view.");
  });
});
