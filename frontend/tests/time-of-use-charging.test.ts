import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createApp,
  h,
  nextTick,
  provide,
  shallowRef,
  ref,
  type App,
} from "vue";
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
    maxSoc?: string;
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
  if (options.maxSoc)
    sample.states["number.renamed_max_soc"]!.state = options.maxSoc;
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
  const settings = ref<{ submit(): Promise<boolean> } | null>(null);
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
          ref: settings,
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
    submit: () => settings.value!.submit(),
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
  it.each(["de", "en"])(
    "summarizes start, grid target and global SOC in order before opening settings in %s",
    async (language) => {
      const fixture = await mount({ editing: false, language, maxSoc: "90" });
      const english = language === "en";
      expect(
        fixture.root.querySelector(".tou-charging-summary")?.textContent,
      ).toContain(english ? "Fixed grid charge target" : "Festes Netzladeziel");
      const cards = fixture.root.querySelectorAll(
        ".tou-charging-soc-row .electricity-target",
      );
      expect(
        [...cards].map((card) => [
          card.querySelector("span")?.textContent?.trim(),
          card.querySelector("strong")?.textContent?.trim(),
        ]),
      ).toEqual([
        [english ? "Start only below" : "Start nur unter", "20 %"],
        [english ? "Grid charge target" : "Netzladeziel", "80 %"],
        ["Max SOC", "90 %"],
      ]);
      expect(
        fixture.root.querySelector(".tou-charging-month-summary")?.textContent,
      ).toContain(english ? "All year" : "Ganzjährig");
      expect(fixture.root.querySelectorAll("input")).toHaveLength(0);
      expect(fixture.callService).not.toHaveBeenCalled();
      await fixture.edit(true);
      expect(method(fixture.root, "fixed").getAttribute("aria-pressed")).toBe(
        "true",
      );
      expect(fixture.root.querySelector("details")).toBeNull();
      const labels = english
        ? ["Start threshold (%)", "Grid charge target (%)", "Max SOC (%)"]
        : ["Ladestart unter (%)", "Netzladeziel (%)", "Max SOC (%)"];
      expect(
        [
          ...fixture.root.querySelectorAll(
            ".tou-charging-limits .entity-control__name",
          ),
        ].map((label) => label.textContent?.trim()),
      ).toEqual(labels);
      for (const label of labels)
        expect(control(fixture.root, label).closest("details")).toBeNull();
      expect(
        fixture.root.querySelectorAll('input[role="switch"]'),
      ).toHaveLength(12);
      expect(fixture.root.textContent).not.toContain("Weitere Einstellungen");
      expect(fixture.root.querySelector(".month-selection__toggle")).toBeNull();
      expect(
        fixture.root.querySelector<HTMLElement>(".month-selection__details")
          ?.style.display,
      ).not.toBe("none");
      expect(method(fixture.root, "fixed").querySelector("span")).toBeNull();
      expect(method(fixture.root, "bridge").querySelector("span")).toBeNull();
      expect(fixture.callService).not.toHaveBeenCalled();
    },
  );

  it("applies a valid replacement SOC pair and global ceiling together without single-field buttons", async () => {
    const fixture = await mount();
    const controls = fixture.root.querySelectorAll(
      ".tou-charging-limits .entity-control",
    );
    expect(
      [...controls].every((control) => !control.querySelector("button")),
    ).toBe(true);
    for (const [label, value] of [
      ["Ladestart unter (%)", "85"],
      ["Netzladeziel (%)", "90"],
      ["Max SOC (%)", "100"],
    ]) {
      const input = control(
        fixture.root,
        label!,
      ).querySelector<HTMLInputElement>("input")!;
      input.value = value!;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
    await flush();
    expect(fixture.callService).not.toHaveBeenCalled();
    expect(await fixture.submit()).toBe(true);
    expect(fixture.callService).toHaveBeenCalledExactlyOnceWith(
      "sax_power",
      "set_charging_settings",
      {
        device_id: "charging-preview-device",
        timed_charge_min_soc: 85,
        timed_charge_max_soc: 90,
        max_soc: 100,
      },
      undefined,
      false,
    );
    expect(
      fixture.root.querySelector(".tou-charging-summary")?.textContent,
    ).toContain("80 %");
  });

  it("marks both crossed SOC fields and accepts a jointly entered zero pair", async () => {
    const fixture = await mount();
    const start = control(
      fixture.root,
      "Ladestart unter (%)",
    ).querySelector<HTMLInputElement>("input")!;
    const target = control(
      fixture.root,
      "Netzladeziel (%)",
    ).querySelector<HTMLInputElement>("input")!;
    const change = async (input: HTMLInputElement, value: string) => {
      input.value = value;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      await flush();
    };
    await change(start, "85");
    await change(target, "75");
    expect(await fixture.submit()).toBe(false);
    expect(fixture.callService).not.toHaveBeenCalled();
    expect(start.getAttribute("aria-invalid")).toBe("true");
    expect(target.getAttribute("aria-invalid")).toBe("true");
    await change(start, "0");
    await change(target, "0");
    expect(await fixture.submit()).toBe(true);
    expect(fixture.callService).toHaveBeenCalledExactlyOnceWith(
      "sax_power",
      "set_charging_settings",
      {
        device_id: "charging-preview-device",
        timed_charge_min_soc: 0,
        timed_charge_max_soc: 0,
      },
      undefined,
      false,
    );
  });

  it("rejects an invalid global draft without applying the valid replacement SOC pair", async () => {
    const fixture = await mount();
    for (const [label, value] of [
      ["Ladestart unter (%)", "25"],
      ["Netzladeziel (%)", "75"],
      ["Max SOC (%)", "90.5"],
    ]) {
      const input = control(
        fixture.root,
        label!,
      ).querySelector<HTMLInputElement>("input")!;
      input.value = value!;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
    await flush();
    expect(await fixture.submit()).toBe(false);
    expect(fixture.callService).not.toHaveBeenCalled();
    expect(
      control(fixture.root, "Max SOC (%)")
        .querySelector("input")
        ?.getAttribute("aria-invalid"),
    ).toBe("true");
    for (const [label, value] of [
      ["Ladestart unter (%)", "25"],
      ["Netzladeziel (%)", "75"],
    ]) {
      const input = control(
        fixture.root,
        label!,
      ).querySelector<HTMLInputElement>("input")!;
      expect(input.value).toBe(value);
      expect(input.getAttribute("aria-invalid")).toBe("false");
    }
  });

  it.each(["de", "en"])(
    "recovers an unavailable global SOC from later HA updates without opening settings in %s",
    async (language) => {
      const fixture = await mount({
        editing: false,
        language,
        maxSoc: "unavailable",
      });
      const global = fixture.root.querySelector(".tou-charging-global strong")!;
      expect(global.textContent?.trim()).toBe(
        language === "de" ? "Nicht verfügbar" : "Unavailable",
      );
      expect(
        fixture.root.querySelector(".tou-charging-target strong")?.textContent,
      ).toBe("80 %");
      await fixture.update("max_soc", "90");
      expect(global.textContent?.trim()).toBe("90 %");
      await fixture.update("timed_charge_min_soc", "25");
      await fixture.update("timed_charge_max_soc", "85");
      expect(
        fixture.root.querySelector(".tou-charging-threshold strong")
          ?.textContent,
      ).toBe("25 %");
      expect(
        fixture.root.querySelector(".tou-charging-target strong")?.textContent,
      ).toBe("85 %");
      expect(fixture.root.querySelector(".tou-charging-editor")).toBeNull();
      expect(fixture.callService).not.toHaveBeenCalled();
    },
  );

  it.each([
    ["de", "off"],
    ["de", "on"],
    ["en", "off"],
    ["en", "on"],
  ])(
    "omits the calibration hint in %s for bridge=%s, open and closed",
    async (language, bridge) => {
      const fixture = await mount({ language, bridge, editing: false });
      for (const editing of [false, true, false]) {
        await fixture.edit(editing);
        expect(fixture.root.textContent).not.toContain(
          language === "de"
            ? "Zellkalibrierung: vorübergehend bis 100 % erlaubt."
            : "Cell calibration: temporarily up to 100% allowed.",
        );
        expect(fixture.root.querySelector("details")).toBeNull();
      }
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
    ).toContain("Festes Netzladeziel");
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
    ).toContain("Nur Bedarf bis Solarstrom");
    expect(
      fixture.root.querySelector(".tou-charging-target")?.textContent,
    ).toContain("Maximales Netzladeziel80 %");
    expect(
      [
        ...fixture.root.querySelectorAll(
          ".tou-charging-soc-row .electricity-target span",
        ),
      ].map((label) => label.textContent?.trim()),
    ).toEqual(["Maximales Netzladeziel", "Max SOC"]);
    expect(control(fixture.root, "Maximales Netzladeziel (%)")).toBeTruthy();
    expect(fixture.root.querySelector(".tou-charging-threshold")).toBeNull();
    expect(control(fixture.root, "Ladestart unter (%)")).toBeUndefined();
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
      "Preise & Zeiten",
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
    const target = control(fixture.root, "Netzladeziel (%)");
    const input = target.querySelector<HTMLInputElement>("input")!;
    input.value = "75";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    void fixture.submit();
    void fixture.submit();
    await flush();
    expect(fixture.callService).toHaveBeenCalledExactlyOnceWith(
      "sax_power",
      "set_charging_settings",
      { device_id: "charging-preview-device", timed_charge_max_soc: 75 },
      undefined,
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
      control(fixture.root, "Netzladeziel (%)").querySelector<HTMLInputElement>(
        "input",
      )?.value,
    ).toBe("75");
    expect(target.querySelector("[role=alert]")).not.toBeNull();
    expect(
      fixture.root.querySelector(".tou-charging-summary")?.textContent,
    ).toContain("80 %");
  });

  it.each([
    ["Netzladeziel (%)", "19", "20"],
    ["Ladestart unter (%)", "81", "80"],
  ])(
    "rejects an inconsistent %s and retains the draft",
    async (label, invalid, equal) => {
      const fixture = await mount();
      const form = control(fixture.root, label!);
      const input = form.querySelector<HTMLInputElement>("input")!;
      const submit = async (value: string) => {
        input.value = value;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        await fixture.submit();
        await flush();
      };
      await submit(invalid!);
      expect(fixture.callService).not.toHaveBeenCalled();
      expect(input.getAttribute("aria-invalid")).toBe("true");
      expect(form.querySelector("[role=alert]")?.textContent).toContain(
        "mindestens so hoch wie der Ladestart",
      );
      await fixture.edit(false);
      await fixture.edit(true);
      expect(input.value).toBe(invalid);
      expect(
        fixture.root.querySelector(".tou-charging-summary")?.textContent,
      ).toContain("80 %");
      await submit(equal!);
      expect(fixture.callService).toHaveBeenCalledExactlyOnceWith(
        "sax_power",
        "set_charging_settings",
        {
          device_id: "charging-preview-device",
          [label === "Netzladeziel (%)"
            ? "timed_charge_max_soc"
            : "timed_charge_min_soc"]: Number(equal),
        },
        undefined,
        false,
      );
      expect(form.querySelector("[role=alert]")).toBeNull();
    },
  );

  it.each(["de", "en"])(
    "explains backend SOC validation after a concurrent change in %s",
    async (language) => {
      const fixture = await mount({ language });
      fixture.callService.mockRejectedValueOnce({
        translation_domain: "sax_power",
        translation_key: "timed_charge_soc_order",
      });
      const form = control(
        fixture.root,
        language === "de" ? "Netzladeziel (%)" : "Grid charge target (%)",
      );
      const input = form.querySelector<HTMLInputElement>("input")!;
      input.value = "75";
      input.dispatchEvent(new Event("input", { bubbles: true }));
      await fixture.submit();
      await flush();
      expect(fixture.callService).toHaveBeenCalledTimes(1);
      expect(form.querySelector("[role=alert]")?.textContent).toContain(
        language === "de" ? "Ladestart" : "start threshold",
      );
      expect(input.value).toBe("75");
      expect(input.disabled).toBe(false);
      expect(
        fixture.root.querySelector(".tou-charging-summary")?.textContent,
      ).toContain("80 %");
    },
  );

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
    ).toContain("Start bei0 %");
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
    expect(
      [
        ...fixture.root.querySelectorAll(
          ".tou-charging-soc-row .electricity-target span",
        ),
      ].map((label) => label.textContent?.trim()),
    ).toEqual(["Maximum grid charge target", "Max SOC"]);
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
        "Maximum grid charge target (%)",
      ).querySelector<HTMLInputElement>("input")?.disabled,
    ).toBe(true);
    expect(control(fixture.root, "Max SOC (%)").closest("details")).toBeNull();
    expect(
      fixture.root.querySelector(".tou-charging-editor")?.textContent,
    ).not.toContain("Solar forecast missing");
    expect(fixture.callService).not.toHaveBeenCalled();
  });
});
