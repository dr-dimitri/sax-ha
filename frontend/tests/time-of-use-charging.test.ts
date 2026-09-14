import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import TimeOfUseChargingSettings from "../src/components/TimeOfUseChargingSettings.vue";
import {
  SAX_DASHBOARD_KEY,
  useSaxDashboard,
  type SaxDashboard,
} from "../src/ha";
import { chargingSample } from "../src/charging-preview-data";
import type { HomeAssistant, TariffProfile } from "../src/types";

const apps: App[] = [];
async function flush() {
  for (let index = 0; index < 6; index++) {
    await Promise.resolve();
    await nextTick();
  }
}
async function mount(
  options: {
    editing?: boolean;
    language?: string;
    bridge?: string | null;
    readonly?: boolean;
    pv?: boolean;
    threshold?: string;
  } = {},
) {
  const sample = chargingSample(options.language ?? "de");
  if (options.bridge !== null) {
    sample.metadata.push({
      domain: "switch",
      key: "bridge_charge_enabled",
      entity_id: "switch.renamed_bridge_charge_enabled",
      name: "Bridge charging",
      states: {},
      can_control: !options.readonly,
    });
    sample.states["switch.renamed_bridge_charge_enabled"] = {
      entity_id: "switch.renamed_bridge_charge_enabled",
      state: options.bridge ?? "off",
      attributes: {},
    };
  }
  if (options.threshold)
    sample.states["number.renamed_timed_charge_min_soc"]!.state =
      options.threshold;
  if (options.readonly)
    sample.metadata.forEach((item) => {
      item.can_control = false;
    });
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
  const profile: TariffProfile = {
    tariff_type: "time_of_use",
    base_price_ct_kwh: 32,
    feed_in_price_ct_kwh: 8,
    windows: [{ start: "00:00:00", end: "06:00:00", price_ct_kwh: 18 }],
    revision: "1",
    can_edit: !options.readonly,
    can_configure: !options.readonly,
    automation_enabled: false,
    profiles: {
      time_of_use: {
        base_price_ct_kwh: 32,
        feed_in_price_ct_kwh: 8,
        windows: [{ start: "00:00:00", end: "06:00:00", price_ct_kwh: 18 }],
        pv_sensor: options.pv ? "sensor.pv_tomorrow" : null,
      },
      dynamic: {
        feed_in_price_ct_kwh: 8,
        price_sensor: null,
        price_attribute: null,
        price_unit: "auto",
        pv_sensor: null,
        pv_factor: 100,
      },
    },
  };
  const callService = vi.fn().mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    states: sample.states,
    connection,
    callWS: async <T>() => structuredClone(profile) as T,
    callService,
  });
  const editing = shallowRef(options.editing ?? true);
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
        h(TimeOfUseChargingSettings, {
          hass: hass.value,
          editing: editing.value,
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
    callService,
    async disconnect() {
      connection.connected = false;
      listeners.get("disconnected")?.forEach((callback) => callback());
      await flush();
    },
    async edit(value: boolean) {
      editing.value = value;
      await flush();
    },
    async update(key: string, state: string) {
      const id = sample.metadata.find((item) => item.key === key)!.entity_id;
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
function method(root: Element, value: "fixed" | "bridge") {
  return root.querySelector<HTMLButtonElement>(
    `button[data-method="${value}"]`,
  )!;
}
function control(root: Element, label: string) {
  return [...root.querySelectorAll<HTMLFormElement>(".entity-control")].find(
    (form) =>
      form.querySelector(".entity-control__name")?.textContent?.trim() ===
      label,
  )!;
}
afterEach(() => {
  apps.splice(0).forEach((app) => app.unmount());
  document.body.replaceChildren();
});

describe("REQ-VUE-ELECTRICITY-TARIFF: understandable time-of-use charging", () => {
  it("summarizes confirmed method, target, threshold and months before opening settings", async () => {
    const fixture = await mount({ editing: false });
    expect(
      fixture.root.querySelector(".tou-charging-summary")?.textContent,
    ).toContain("Festes Ladeziel · Ladeziel 80 %");
    expect(
      fixture.root.querySelector(".tou-charging-threshold")?.textContent,
    ).toContain("nur unter 20 %");
    expect(
      fixture.root.querySelector(".tou-charging-month-summary")?.textContent,
    ).toContain("Ganzjährig");
    expect(fixture.root.querySelectorAll("input")).toHaveLength(0);
    expect(fixture.callService).not.toHaveBeenCalled();
    await fixture.edit(true);
    expect(method(fixture.root, "fixed").getAttribute("aria-pressed")).toBe(
      "true",
    );
    expect(
      fixture.root.querySelector<HTMLDetailsElement>(".tou-charging-advanced")
        ?.open,
    ).toBe(false);
    const target = control(fixture.root, "Ladeziel (%)");
    expect(target.closest("details")).toBeNull();
    expect(
      control(
        fixture.root,
        "Nur starten unter einem Ladestand von (%)",
      ).closest("details"),
    ).not.toBeNull();
    expect(
      control(fixture.root, "Ladegrenze für alle Lademethoden (%)").closest(
        "details",
      ),
    ).not.toBeNull();
    expect(fixture.root.textContent).toContain(
      "Öffne in Schritt 1 „Bearbeiten“",
    );
    expect(fixture.callService).not.toHaveBeenCalled();
  });

  it.each([
    ["de", "off"],
    ["de", "on"],
    ["en", "off"],
    ["en", "on"],
  ])(
    "explains the calibration exception to both charge limits in %s for bridge=%s, open and closed",
    async (language, bridge) => {
      // REQ-PERIODIC-FULL-CALIBRATION / REQ-BRIDGE-CHARGE: 100% permits charging; it does not force an extra full charge.
      const fixture = await mount({ language, bridge, editing: false });
      const expected =
        language === "de"
          ? "Ausnahme: Bei fälliger Zellkalibrierung sind bis 100 % erlaubt, auch über Ladeziel und globale Ladegrenze hinaus. Alle anderen Ladebedingungen gelten weiter."
          : "Exception: When cell calibration is due, charging up to 100% is allowed beyond both the charge target and global limit. Other charging conditions still apply.";
      for (const editing of [false, true, false]) {
        await fixture.edit(editing);
        const hints = fixture.root.querySelectorAll(
          ".tou-charging-calibration",
        );
        expect(hints).toHaveLength(1);
        expect(hints[0]!.textContent?.trim()).toBe(expected);
        expect(hints[0]!.closest("details")).toBeNull();
        if (editing)
          expect(hints[0]!.closest(".tou-charging-editor")).not.toBeNull();
        else expect(hints[0]!.closest(".tou-charging-editor")).toBeNull();
      }
      await fixture.edit(true);
      expect(
        fixture.root.querySelector(".tou-charging-editor")?.textContent,
      ).toContain(
        language === "de"
          ? bridge === "on"
            ? "Danach darf der Speicher wieder normal entladen."
            : "Nach der Netzladung entlädt der Speicher bis zum Ende dieser Zeit nicht"
          : bridge === "on"
            ? "Afterwards, the battery may discharge normally again."
            : "After grid charging, the battery does not discharge until this period ends",
      );
      expect(fixture.callService).not.toHaveBeenCalled();
    },
  );

  it("sends one existing bridge switch service, blocks repeats and waits for confirmed state", async () => {
    const fixture = await mount();
    let resolve!: () => void;
    fixture.callService.mockImplementationOnce(
      () =>
        new Promise<void>((done) => {
          resolve = done;
        }),
    );
    method(fixture.root, "bridge").click();
    method(fixture.root, "bridge").click();
    await flush();
    expect(fixture.callService).toHaveBeenCalledExactlyOnceWith(
      "switch",
      "turn_on",
      {},
      { entity_id: "switch.renamed_bridge_charge_enabled" },
      false,
    );
    expect(
      fixture.root.querySelector(".tou-charging-feedback [role=status]")
        ?.textContent,
    ).toContain("Ladeweise wird übernommen");
    expect(method(fixture.root, "bridge").disabled).toBe(true);
    expect(method(fixture.root, "fixed").getAttribute("aria-pressed")).toBe(
      "true",
    );
    expect(
      fixture.root.querySelector(".tou-charging-summary")?.textContent,
    ).toContain("Festes Ladeziel");
    resolve();
    await flush();
    expect(method(fixture.root, "fixed").getAttribute("aria-pressed")).toBe(
      "true",
    );
    await fixture.update("bridge_charge_enabled", "on");
    expect(method(fixture.root, "bridge").getAttribute("aria-pressed")).toBe(
      "true",
    );
    expect(
      fixture.root.querySelector(".tou-charging-summary")?.textContent,
    ).toContain("Nur Bedarf bis Solarstrom · Höchstens laden bis 80 %");
    expect(control(fixture.root, "Höchstens laden bis (%)")).toBeTruthy();
    expect(fixture.root.querySelector(".tou-charging-threshold")).toBeNull();
    expect(
      control(fixture.root, "Nur starten unter einem Ladestand von (%)"),
    ).toBeUndefined();
    method(fixture.root, "bridge").click();
    await flush();
    expect(fixture.callService).toHaveBeenCalledTimes(1);
    method(fixture.root, "fixed").click();
    await flush();
    expect(fixture.callService).toHaveBeenLastCalledWith(
      "switch",
      "turn_off",
      {},
      { entity_id: "switch.renamed_bridge_charge_enabled" },
      false,
    );
    expect(fixture.dashboard.tariff.value?.automation_enabled).toBe(false);
  });

  it("keeps confirmed mode and exposes the configuration remedy when the service fails", async () => {
    const fixture = await mount();
    fixture.callService.mockRejectedValueOnce({
      code: "home_assistant_error",
      translation_domain: "sax_power",
      translation_key: "bridge_pv_start_required",
    });
    method(fixture.root, "bridge").click();
    await flush();
    expect(method(fixture.root, "fixed").getAttribute("aria-pressed")).toBe(
      "true",
    );
    expect(method(fixture.root, "bridge").disabled).toBe(false);
    expect(fixture.root.querySelector("[role=alert]")?.textContent).toContain(
      "Solarprognose",
    );
    expect(fixture.root.querySelector("[role=alert]")?.textContent).toContain(
      "Schritt 1",
    );
    expect(fixture.callService).toHaveBeenCalledTimes(1);
  });

  it("retains confirmed target and the failed number draft when the editor is closed and reopened", async () => {
    const fixture = await mount();
    let reject!: () => void;
    fixture.callService.mockImplementationOnce(
      () =>
        new Promise<void>((_, failed) => {
          reject = () => failed(new Error("offline"));
        }),
    );
    const target = control(fixture.root, "Ladeziel (%)");
    const input = target.querySelector<HTMLInputElement>("input")!;
    input.value = "75";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    target.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    target.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    await flush();
    expect(fixture.callService).toHaveBeenCalledExactlyOnceWith(
      "number",
      "set_value",
      { value: 75 },
      { entity_id: "number.renamed_timed_charge_max_soc" },
      false,
    );
    expect(input.disabled).toBe(true);
    expect(target.querySelector("[role=status]")?.textContent).toContain(
      "Änderung wird",
    );
    expect(
      fixture.root.querySelector(".tou-charging-summary")?.textContent,
    ).toContain("80 %");
    await fixture.edit(false);
    reject();
    await flush();
    await fixture.edit(true);
    expect(
      control(fixture.root, "Ladeziel (%)").querySelector<HTMLInputElement>(
        "input",
      )?.value,
    ).toBe("75");
    expect(target.querySelector("[role=alert]")).not.toBeNull();
    expect(
      fixture.root.querySelector(".tou-charging-summary")?.textContent,
    ).toContain("80 %");
  });

  it.each(["unknown", "unavailable", "unexpected", null])(
    "does not pretend %s is fixed charging",
    async (state) => {
      const fixture = await mount({ bridge: state });
      expect(
        fixture.root.querySelector(".tou-charging-summary")?.textContent,
      ).toContain("Ladeweise nicht verfügbar");
      expect(method(fixture.root, "fixed").getAttribute("aria-pressed")).toBe(
        "false",
      );
      expect(method(fixture.root, "bridge").getAttribute("aria-pressed")).toBe(
        "false",
      );
      expect(method(fixture.root, "fixed").disabled).toBe(true);
      expect(method(fixture.root, "bridge").disabled).toBe(true);
      expect(fixture.root.querySelector(".tou-charging-threshold")).toBeNull();
      method(fixture.root, "bridge").click();
      expect(fixture.callService).not.toHaveBeenCalled();
    },
  );

  it("explains zero start threshold and does not call an incomplete month selection inactive", async () => {
    const fixture = await mount({ threshold: "0" });
    expect(
      fixture.root.querySelector(".tou-charging-threshold")?.textContent,
    ).toContain("Es beginnt keine neue automatische Netzladung");
    await fixture.update("timed_charge_month_1", "unavailable");
    expect(
      fixture.root.querySelector(".tou-charging-month-summary")?.textContent,
    ).toContain("nicht vollständig bekannt");
    expect(
      fixture.root.querySelector(".tou-charging-month-summary")?.textContent,
    ).not.toContain("Ganzjährig");
    for (let month = 2; month <= 12; month++)
      await fixture.update(`timed_charge_month_${month}`, "off");
    expect(
      fixture.root.querySelector(".tou-charging-month-summary")?.textContent,
    ).toContain("nicht vollständig bekannt");
    await fixture.update("timed_charge_month_1", "off");
    expect(
      fixture.root.querySelector(".tou-charging-month-summary")?.textContent,
    ).toContain("ganzjährig inaktiv");
  });

  it("blocks unavailable controls after disconnect and does not summarize cached values as confirmed", async () => {
    const fixture = await mount();
    await fixture.disconnect();
    expect(
      fixture.root.querySelector(".tou-charging-feedback")?.textContent,
    ).toContain("Keine Verbindung");
    expect(
      fixture.root.querySelector(".tou-charging-summary")?.textContent,
    ).toContain("nicht verfügbar");
    expect(method(fixture.root, "fixed").getAttribute("aria-pressed")).toBe(
      "false",
    );
    expect(method(fixture.root, "bridge").disabled).toBe(true);
    method(fixture.root, "bridge").click();
    expect(fixture.callService).not.toHaveBeenCalled();
  });

  it("shows English copy, a read-only confirmed method and an explained global limit", async () => {
    const fixture = await mount({
      language: "en",
      bridge: "on",
      readonly: true,
      pv: true,
    });
    expect(
      fixture.root.querySelector(".tou-charging-summary")?.textContent,
    ).toContain("Only what is needed until solar power");
    expect(method(fixture.root, "bridge").getAttribute("aria-pressed")).toBe(
      "true",
    );
    expect(method(fixture.root, "fixed").disabled).toBe(true);
    expect(
      fixture.root.querySelector(".tou-charging-feedback")?.textContent,
    ).toContain("permission");
    expect(
      control(
        fixture.root,
        "Charge up to at most (%)",
      ).querySelector<HTMLInputElement>("input")?.disabled,
    ).toBe(true);
    expect(
      fixture.root.querySelector(".tou-charging-advanced")?.textContent,
    ).toContain("Also applies to solar charging");
    expect(fixture.root.textContent).not.toContain("Open “Edit” in step 1");
    expect(fixture.callService).not.toHaveBeenCalled();
  });
});
