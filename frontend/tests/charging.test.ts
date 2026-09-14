import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createApp,
  h,
  nextTick,
  provide,
  shallowRef,
  type App,
  type Component,
} from "vue";
import GridServingView from "../src/views/GridServingView.vue";
import GeneralView from "../src/views/GeneralView.vue";
import { chargingSample } from "../src/charging-preview-data";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "../src/ha";
import type {
  DashboardEntityMetadata,
  DashboardMetadata,
  HassConnection,
  HomeAssistant,
} from "../src/types";

const applications: App[] = [];
async function flush(): Promise<void> {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}
async function mount(
  view: Component | Component[],
  options: { language?: string; keys?: string[]; deferMetadata?: boolean } = {},
) {
  const sample = chargingSample(options.language);
  const metadata = sample.metadata.filter(
    (item) => !options.keys || options.keys.includes(item.key),
  );
  let emitMetadata: (data: DashboardMetadata) => void = () => {};
  const unsubscribe = vi.fn();
  const connection: HassConnection = {
    connected: true,
    async subscribeMessage<T>(callback: (message: T) => void) {
      emitMetadata = (data) => callback(data as T);
      if (!options.deferMetadata)
        emitMetadata({ entities: [...metadata].reverse() });
      return unsubscribe;
    },
    addEventListener() {},
    removeEventListener() {},
  };
  const callService = vi
    .fn<NonNullable<HomeAssistant["callService"]>>()
    .mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    states: sample.states,
    connection,
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
      return () =>
        h(
          "div",
          (Array.isArray(view) ? view : [view]).map((component) =>
            h(component, { hass: hass.value }),
          ),
        );
    },
  });
  applications.push(app);
  app.mount(root);
  await flush();
  return {
    root,
    hass,
    metadata,
    callService,
    async emit(items: DashboardEntityMetadata[] = metadata) {
      emitMetadata({ entities: items });
      await flush();
    },
    async update(
      key: string,
      state: string,
      attributes?: Record<string, unknown>,
    ) {
      const id = sample.metadata.find((item) => item.key === key)!.entity_id;
      const previous = hass.value.states[id];
      hass.value = {
        ...hass.value,
        states: {
          ...hass.value.states,
          [id]: {
            ...previous,
            state,
            attributes: { ...previous.attributes, ...attributes },
          },
        },
      };
      await flush();
    },
  };
}
function form(root: Element, name: string): HTMLFormElement {
  const label = [...root.querySelectorAll("label")].find(
    (element) => element.textContent === name,
  );
  expect(label, `Control ${name}`).toBeDefined();
  return label!.closest("form")!;
}
function names(root: Element): string[] {
  return [
    ...root.querySelectorAll(".entity-control__name, .entity-value__name"),
  ].map((element) => element.textContent!);
}

afterEach(() => {
  for (const app of applications.splice(0)) app.unmount();
  document.body.replaceChildren();
  vi.useRealTimers();
});

describe("REQ-VUE-CHARGING: grid-serving charging view", () => {
  it.each(["de", "en-GB"])(
    "omits confirmed values for every switch across all views with valid feedback descriptions (%s)",
    async (language) => {
      const { root } = await mount([GeneralView, GridServingView], {
        language,
      });
      const switches = root.querySelectorAll<HTMLInputElement>(
        'input[role="switch"]',
      );
      expect(switches.length).toBeGreaterThan(12);
      for (const field of switches) {
        const control = field.closest(".entity-control")!;
        expect(control.querySelector(".entity-control__value")).toBeNull();
        expect(
          control.querySelector(".entity-control__description")?.children
            .length ?? 1,
        ).toBe(1);
        expect(field.getAttribute("aria-describedby")).toBe(
          control.querySelector(".entity-control__feedback")!.id,
        );
      }
    },
  );

  it("preserves the grid-serving pause order, forecast and all month names without an extra settings card", async () => {
    const { root, callService } = await mount(GridServingView);
    expect(
      [...root.querySelectorAll(".charging-view h2")].map(
        (item) => item.textContent,
      ),
    ).toEqual(["Ladepause", "Aktive Monate"]);
    expect(names(root)).toEqual([
      "Netzdienliches Laden aktiv",
      "PV-Prognose morgen",
      "Mindest PV-Prognose",
      "Status",
      "Januar",
      "Februar",
      "März",
      "April",
      "Mai",
      "Juni",
      "Juli",
      "August",
      "September",
      "Oktober",
      "November",
      "Dezember",
    ]);
    expect(root.textContent).toContain("24,3 kWh");
    expect(root.textContent).not.toContain("Zeitfenster");
    expect(root.querySelectorAll('input[type="number"]')).toHaveLength(1);
    expect(callService).not.toHaveBeenCalled();
  });

  it.each([
    [GridServingView, "grid_serving", "de"],
    [GridServingView, "grid_serving", "en-GB"],
  ] as const)(
    "applies each overnight window atomically and waits for confirmed HA states (%s)",
    async (view, prefix, language) => {
      const { root, callService, update } = await mount(view, { language });
      const control = root.querySelector<HTMLFormElement>(
        ".time-window-control",
      )!;
      expect(control).not.toBeNull();
      expect(control.querySelectorAll('input[type="time"]')).toHaveLength(2);
      expect(control.querySelectorAll('[role="slider"]')).toHaveLength(2);
      const confirmed = () =>
        control.querySelector(".time-window-control__confirmed")!.textContent;
      expect(confirmed()).toContain("22:00");
      expect(confirmed()).toContain("06:00");
      if (language === "de") expect(confirmed()).toContain("Uhr");
      const start =
        control.querySelector<HTMLInputElement>('input[type="time"]')!;
      start.value = "23:15";
      start.dispatchEvent(new Event("input", { bubbles: true }));
      await flush();
      expect(callService).not.toHaveBeenCalled();
      control.dispatchEvent(
        new Event("submit", { bubbles: true, cancelable: true }),
      );
      await flush();
      expect(callService.mock.calls).toEqual([
        [
          "sax_power",
          `set_${prefix}_window`,
          {
            device_id: "charging-preview-device",
            start: "23:15:00",
            end: "06:00:00",
          },
          undefined,
          false,
        ],
      ]);
      expect(confirmed()).toContain("22:00");
      await update(`${prefix}_start`, "23:15:00");
      expect(start.value).toBe("23:15");
      expect(confirmed()).toContain("23:15");
    },
  );

  it("blocks the shared window when a confirmed time is unavailable or malformed", async () => {
    const { root, update, callService } = await mount(GridServingView);
    const control = root.querySelector(".time-window-control")!;
    for (const state of [
      "unknown",
      "unavailable",
      "invalid",
      "25:00:00",
      "12:60:00",
      "12:30:60",
    ]) {
      await update("grid_serving_start", state);
      expect(
        control.querySelector<HTMLInputElement>('input[type="time"]')!.disabled,
      ).toBe(true);
    }
    await update("grid_serving_start", "09:05");
    expect(
      control.querySelector(".time-window-control__confirmed")!.textContent,
    ).toContain("09:05");
    expect(
      control.querySelector<HTMLInputElement>('input[type="time"]')!.disabled,
    ).toBe(false);
    expect(callService).not.toHaveBeenCalled();
  });

  it.each([[GridServingView, "grid_serving"]] as const)(
    "updates month switches only after HA confirmation and does not infer a month schedule (%s)",
    async (view, prefix) => {
      const { root, callService, update } = await mount(view);
      const months = root.querySelector(".charging-view__rows--months")!;
      expect(months.querySelectorAll(".entity-control__value")).toHaveLength(0);
      expect(months.querySelectorAll('input[role="switch"]')).toHaveLength(12);
      for (const input of months.querySelectorAll("input")) {
        const describedIds = input
          .getAttribute("aria-describedby")!
          .split(/\s+/);
        expect(describedIds.length).toBeGreaterThan(0);
        for (const id of describedIds)
          expect(root.querySelector(`[id="${id}"]`)).not.toBeNull();
        expect(root.querySelector(`[for="${input.id}"]`)).not.toBeNull();
      }
      expect(
        root.querySelector(
          ":scope .charging-view > .entity-control .entity-control__value",
        ),
      ).toBeNull();
      vi.useFakeTimers();
      vi.setSystemTime(new Date("2026-09-30T21:59:59Z"));
      const september = form(root, "September").querySelector("input")!;
      september.checked = false;
      september.dispatchEvent(new Event("change", { bubbles: true }));
      await flush();
      expect(callService).toHaveBeenCalledExactlyOnceWith(
        "switch",
        "turn_off",
        {},
        { entity_id: `switch.renamed_${prefix}_month_9` },
        false,
      );
      expect(september.checked).toBe(true);
      await update(`${prefix}_month_9`, "off");
      expect(september.checked).toBe(false);
      vi.setSystemTime(new Date("2026-10-01T00:00:00Z"));
      await flush();
      expect(callService).toHaveBeenCalledTimes(1);
      expect(form(root, "Oktober").querySelector("input")!.checked).toBe(true);
      await update(`${prefix}_month_10`, "off");
      const october = form(root, "Oktober");
      const octoberSwitch = october.querySelector("input")!;
      expect(octoberSwitch.checked).toBe(false);
      callService.mockRejectedValueOnce(new Error("server detail"));
      octoberSwitch.checked = true;
      octoberSwitch.dispatchEvent(new Event("change", { bubbles: true }));
      await flush();
      expect(octoberSwitch.checked).toBe(false);
      const feedback = root.querySelector(
        `[id="${octoberSwitch.getAttribute("aria-describedby")}"]`,
      )!;
      expect(feedback.querySelector('[role="alert"]')?.textContent).toContain(
        "Änderung ist fehlgeschlagen",
      );
      expect(october.querySelector(".entity-control__value")).toBeNull();
      expect(callService).toHaveBeenCalledTimes(2);
    },
  );

  it.each([
    [GridServingView, "grid_serving", "de"],
    [GridServingView, "grid_serving", "en-GB"],
  ] as const)(
    "summarises separate selected ranges and opens all four quarters without writing (%s, %s, %s)",
    async (view, prefix, language) => {
      const { root, update, callService } = await mount(view, { language });
      const toggle = root.querySelector<HTMLButtonElement>(
        ".month-selection__toggle",
      )!;
      const details = root.querySelector<HTMLElement>(
        `[id="${toggle.getAttribute("aria-controls")}"]`,
      )!;
      const summary = () =>
        root.querySelector(".month-selection__summary")!.textContent;
      expect(summary()).toBe(language === "de" ? "Ganzjährig" : "All year");
      expect(toggle.getAttribute("aria-expanded")).toBe("false");
      expect(details.style.display).toBe("none");
      toggle.click();
      await flush();
      expect(toggle.getAttribute("aria-expanded")).toBe("true");
      expect(details.style.display).not.toBe("none");
      const quarters = [...details.querySelectorAll("fieldset")];
      expect(quarters).toHaveLength(4);
      expect(
        quarters.map((quarter) => quarter.querySelectorAll("input").length),
      ).toEqual([3, 3, 3, 3]);
      expect(
        quarters.every(
          (quarter) => quarter.querySelector("legend")?.textContent,
        ),
      ).toBe(true);
      const selected = new Set([1, 3, 4, 5, 10]);
      for (let month = 1; month <= 12; month++)
        await update(
          `${prefix}_month_${month}`,
          selected.has(month) ? "on" : "off",
        );
      expect(summary()).toContain(
        language === "de"
          ? "Januar, März–Mai, Oktober"
          : "January, March–May, October",
      );
      expect(
        root.querySelector(".month-selection__count")!.textContent,
      ).toContain("5");
      toggle.click();
      await flush();
      expect(toggle.getAttribute("aria-expanded")).toBe("false");
      expect(details.style.display).toBe("none");
      expect(summary()).toContain(
        language === "de"
          ? "Januar, März–Mai, Oktober"
          : "January, March–May, October",
      );
      for (let month = 1; month <= 12; month++)
        await update(
          `${prefix}_month_${month}`,
          [1, 2, 11, 12].includes(month) ? "on" : "off",
        );
      expect(summary()).toContain(
        language === "de"
          ? "Januar–Februar, November–Dezember"
          : "January–February, November–December",
      );
      for (const month of [1, 2, 11, 12])
        await update(`${prefix}_month_${month}`, "off");
      expect(summary()).toBe(
        language === "de"
          ? "Keine Monate ausgewählt · Ganzjährig inaktiv"
          : "No months selected · Inactive all year",
      );
      expect(callService).not.toHaveBeenCalled();
    },
  );

  it.each([[GridServingView, "grid_serving"]] as const)(
    "distinguishes no selected months from missing or unavailable month states (%s)",
    async (view, prefix) => {
      const { root, update, emit, metadata, callService } = await mount(view);
      const summary = () =>
        root.querySelector(".month-selection__summary")!.textContent;
      for (let month = 1; month <= 12; month++)
        await update(`${prefix}_month_${month}`, "off");
      expect(summary()).toContain("Ganzjährig inaktiv");
      for (const state of ["unknown", "unavailable", "invalid"]) {
        await update(`${prefix}_month_2`, state);
        expect(summary()).not.toContain("Ganzjährig inaktiv");
        expect(root.querySelector(".month-selection")!.textContent).toMatch(
          /unbekannt|nicht verfügbar|unklar/i,
        );
      }
      await update(`${prefix}_month_2`, "off");
      await emit(metadata.filter((item) => item.key !== `${prefix}_month_2`));
      expect(summary()).not.toContain("Ganzjährig inaktiv");
      await emit();
      expect(summary()).toContain("Ganzjährig inaktiv");
      await update(`${prefix}_month_3`, "on");
      expect(summary()).toContain("März");
      expect(summary()).not.toContain("Ganzjährig inaktiv");
      expect(callService).not.toHaveBeenCalled();
    },
  );

  it("keeps the confirmed summary during a pending write and displays rejection after collapsing", async () => {
    const { root, update, callService } = await mount(GridServingView);
    for (let month = 1; month <= 12; month++)
      await update(`grid_serving_month_${month}`, "off");
    let reject: (error: Error) => void = () => {};
    callService.mockImplementationOnce(
      () =>
        new Promise((_resolve, rejectPromise) => {
          reject = rejectPromise;
        }),
    );
    const toggle = root.querySelector<HTMLButtonElement>(
      ".month-selection__toggle",
    )!;
    toggle.click();
    await flush();
    const january = form(root, "Januar").querySelector("input")!;
    january.checked = true;
    january.dispatchEvent(new Event("change", { bubbles: true }));
    await flush();
    expect(january.checked).toBe(false);
    expect(
      root.querySelector(".month-selection__summary")!.textContent,
    ).toContain("Ganzjährig inaktiv");
    toggle.click();
    await flush();
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    reject(new Error("conflicting charge windows"));
    await flush();
    expect(
      root.querySelector(".month-selection__summary")!.textContent,
    ).toContain("Ganzjährig inaktiv");
    const visibleError = [
      ...root.querySelectorAll<HTMLElement>('.month-selection [role="alert"]'),
    ].find((element) => {
      let node: HTMLElement | null = element;
      while (node) {
        if (node.style.display === "none") return false;
        node = node.parentElement;
      }
      return true;
    });
    expect(visibleError?.textContent).toContain("Änderung ist fehlgeschlagen");
    expect(callService).toHaveBeenCalledTimes(1);
    toggle.click();
    await flush();
    expect(january.checked).toBe(false);
    expect(callService).toHaveBeenCalledTimes(1);
  });

  it("keeps the live charging pause status and unavailable forecast supplied by HA", async () => {
    const { root, update, callService } = await mount(GridServingView);
    await update("grid_serving_pause_status", "Ladepause aktiv");
    await update("grid_serving_forecast", "unavailable", {
      friendly_name: "PV-Prognose heute",
    });
    expect(root.textContent).toContain("Ladepause aktiv");
    const forecast = [...root.querySelectorAll(".entity-value")].find((item) =>
      item.textContent?.includes("PV-Prognose heute"),
    )!;
    expect(forecast.querySelector(".entity-value__state")?.textContent).toBe(
      "Nicht verfügbar",
    );
    expect(forecast.textContent).not.toContain("0 kWh");
    expect(callService).not.toHaveBeenCalled();
  });

  it.each([GridServingView])(
    "omits absent entities and empty cards while distinguishing initial loading (%s)",
    async (view) => {
      const { root, emit } = await mount(view, {
        keys: [],
        deferMetadata: true,
      });
      expect(root.textContent).toBe("Die Entitäten werden geladen …");
      await emit();
      expect(root.textContent).toBe(
        "Für diese Ansicht sind keine Entitäten verfügbar.",
      );
      expect(root.querySelectorAll("section, form")).toHaveLength(0);
    },
  );

  it("renders translated English headings, Start/End and month labels", async () => {
    const { root } = await mount([GridServingView], {
      language: "en-GB",
    });
    expect(
      [...root.querySelectorAll(".charging-view h2")].map(
        (item) => item.textContent,
      ),
    ).toEqual(["Charging pause", "Active months"]);
    expect(
      root.querySelectorAll('.time-window-control input[type="time"]'),
    ).toHaveLength(2);
    expect(names(root).filter((name) => name === "January")).toHaveLength(1);
    expect(names(root)).toContain("December");
    expect(root.textContent).toContain("PV forecast tomorrow");
  });
});
