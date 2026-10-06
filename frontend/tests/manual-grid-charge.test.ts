import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import ManualGridCharge from "../src/components/ManualGridCharge.vue";
import EntityControl from "../src/components/EntityControl.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "../src/ha";
import type {
  ConnectionEvent,
  DashboardEntityMetadata,
  DashboardMetadata,
  HassConnection,
  HomeAssistant,
} from "../src/types";

const apps: App[] = [];
async function flush() {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}
function deferred() {
  let resolve!: () => void;
  let reject!: (cause: unknown) => void;
  const promise = new Promise<void>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
async function mount(
  options: {
    language?: string;
    canControl?: boolean;
    deviceId?: string | null;
    state?: string;
    missing?: boolean;
    reference?: string;
    copies?: number;
    storageControl?: boolean;
    telemetry?: boolean;
  } = {},
) {
  const metadata: DashboardEntityMetadata[] = [
    {
      domain: "switch",
      key: "storage_switch",
      entity_id: "switch.storage_renamed_by_user",
      device_id:
        options.deviceId === undefined ? "registry-device" : options.deviceId,
      name: "Speicher",
      states: {},
      can_control: options.canControl ?? true,
    },
    ...(options.telemetry === false
      ? []
      : [
          {
            domain: "sensor" as const,
            key: "charge_power",
            entity_id: "sensor.charge_renamed_by_user",
            device_id: "registry-device",
            name: "Bestätigte Ladeleistung",
            states: {},
            can_control: false,
          },
        ]),
    ...(options.reference
      ? [
          {
            domain: "sensor" as const,
            key: "ic_max_power_reference",
            entity_id: "sensor.rated_power",
            device_id: "registry-device",
            name: "Geräteleistung",
            states: {},
            can_control: false,
          },
        ]
      : []),
  ];
  const listeners = new Map<ConnectionEvent, Set<() => void>>();
  let emitMetadata: (message: DashboardMetadata) => void = () => {};
  const connection: HassConnection = {
    connected: true,
    async subscribeMessage<T>(callback: (message: T) => void) {
      emitMetadata = (message) => callback(message as T);
      emitMetadata({ entities: options.missing ? [] : metadata });
      return () => {};
    },
    addEventListener(event, listener) {
      if (!listeners.has(event)) listeners.set(event, new Set());
      listeners.get(event)!.add(listener);
    },
    removeEventListener(event, listener) {
      listeners.get(event)?.delete(listener);
    },
  };
  const callService = vi
    .fn<NonNullable<HomeAssistant["callService"]>>()
    .mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    states: {
      "switch.storage_renamed_by_user": {
        entity_id: "switch.storage_renamed_by_user",
        state: options.state ?? "off",
        attributes: {},
      },
      "sensor.charge_renamed_by_user": {
        entity_id: "sensor.charge_renamed_by_user",
        state: "0",
        attributes: { unit_of_measurement: "W" },
      },
      "sensor.rated_power": {
        entity_id: "sensor.rated_power",
        state: options.reference ?? "unknown",
        attributes: { unit_of_measurement: "W" },
      },
    },
    connection,
    callService,
  });
  const root = document.createElement("div");
  document.body.append(root);
  let dashboard!: ReturnType<typeof useSaxDashboard>;
  const app = createApp({
    setup() {
      dashboard = useSaxDashboard(
        () => hass.value,
        () => "entry-registry",
      );
      provide(SAX_DASHBOARD_KEY, dashboard);
      return () =>
        h("div", [
          ...Array.from({ length: options.copies ?? 1 }, () =>
            h(ManualGridCharge),
          ),
          ...(options.storageControl
            ? [
                h(EntityControl, {
                  domain: "switch",
                  entityKey: "storage_switch",
                }),
              ]
            : []),
        ]);
    },
  });
  apps.push(app);
  app.mount(root);
  await flush();
  return {
    root,
    hass,
    callService,
    dashboard,
    async disconnect() {
      Object.assign(connection, { connected: false });
      for (const listener of listeners.get("disconnected") ?? []) listener();
      await flush();
    },
    async updateCharge(value: string) {
      const previous = hass.value.states["sensor.charge_renamed_by_user"]!;
      hass.value = {
        ...hass.value,
        states: {
          ...hass.value.states,
          [previous.entity_id]: { ...previous, state: value },
        },
      };
      await flush();
    },
  };
}
function button(root: ParentNode, name: string) {
  const result = [...root.querySelectorAll<HTMLButtonElement>("button")].find(
    (element) => element.textContent?.trim() === name,
  );
  expect(result).toBeTruthy();
  return result!;
}
function field(root: ParentNode) {
  return root.querySelector<HTMLInputElement>('input[type="number"]')!;
}
async function enter(root: ParentNode, value: string) {
  field(root).value = value;
  field(root).dispatchEvent(new Event("input", { bubbles: true }));
  await flush();
}
async function click(root: ParentNode, name: string) {
  button(root, name).click();
  await flush();
}
afterEach(() => {
  for (const app of apps.splice(0)) app.unmount();
  document.body.replaceChildren();
});

describe("REQ-VUE-CHARGING: manual grid-charge buttons", () => {
  it.each(["de", "en-GB"])(
    "labels explicit actions and uses confirmed telemetry only (%s)",
    async (language) => {
      const { root, callService, updateCharge } = await mount({ language });
      const english = !language.startsWith("de");
      const start = english ? "Enable grid charging" : "Netzladen aktivieren";
      const stop = english ? "Disable grid charging" : "Netzladen abschalten";
      const input = field(root);
      expect(root.querySelector("label")?.htmlFor).toBe(input.id);
      expect(input.value).toBe("1000");
      expect(input.min).toBe("1");
      expect(input.max).toBe("32768");
      expect(input.step).toBe("1");
      expect(button(root, start).disabled).toBe(false);
      expect(button(root, stop).disabled).toBe(false);
      expect(root.textContent).toContain("0 W");
      expect(callService).not.toHaveBeenCalled();
      await enter(root, "1250");
      expect(callService).not.toHaveBeenCalled();
      await click(root, start);
      expect(callService).toHaveBeenCalledExactlyOnceWith(
        "sax_power",
        "start_grid_charge",
        { device_id: "registry-device", power: -1250 },
        undefined,
        false,
      );
      expect(root.textContent).toContain("0 W");
      expect(input.value).toBe("1250");
      await updateCharge("1250");
      expect(root.textContent).toContain(english ? "1,250 W" : "1.250 W");
      await click(root, stop);
      expect(callService).toHaveBeenLastCalledWith(
        "sax_power",
        "stop_grid_charge",
        { device_id: "registry-device" },
        undefined,
        false,
      );
    },
  );

  it("shares pending feedback across copies and storage controls until acknowledgement", async () => {
    const { root, callService } = await mount({
      copies: 2,
      storageControl: true,
    });
    const waiting = deferred();
    callService.mockReturnValueOnce(waiting.promise);
    await click(root, "Netzladen aktivieren");
    const copies = root.querySelectorAll(".manual-grid-charge");
    expect(copies).toHaveLength(2);
    for (const copy of copies) {
      expect(copy.getAttribute("aria-busy")).toBe("true");
      expect(
        copy.querySelector('[role="status"]')?.textContent?.trim(),
      ).toBeTruthy();
      expect(field(copy).disabled).toBe(true);
      expect(button(copy, "Netzladen aktivieren").disabled).toBe(true);
      expect(button(copy, "Netzladen abschalten").disabled).toBe(true);
      expect(copy.textContent).toContain("0 W");
    }
    const storage = root.querySelector<HTMLInputElement>(
      'input[role="switch"]',
    )!;
    expect(storage.disabled).toBe(true);
    await click(root, "Netzladen aktivieren");
    await click(root, "Netzladen abschalten");
    root
      .querySelector("form")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flush();
    expect(callService).toHaveBeenCalledOnce();
    waiting.resolve();
    await flush();
    for (const copy of copies) {
      expect(copy.getAttribute("aria-busy")).toBe("false");
      expect(button(copy, "Netzladen abschalten").disabled).toBe(false);
    }
    expect(storage.disabled).toBe(false);
  });

  it.each(["Netzladen aktivieren", "Netzladen abschalten"])(
    "preserves the draft and confirmed telemetry on failed %s",
    async (action) => {
      const { root, callService } = await mount();
      await enter(root, "1500");
      const waiting = deferred();
      callService.mockReturnValueOnce(waiting.promise);
      await click(root, action);
      expect(
        root.querySelector(".manual-grid-charge")?.getAttribute("aria-busy"),
      ).toBe("true");
      waiting.reject(new Error("physical device rejected the write"));
      await flush();
      expect(root.querySelector('[role="alert"]')?.textContent).toContain(
        "fehlgeschlagen",
      );
      expect(field(root).value).toBe("1500");
      expect(root.textContent).toContain("0 W");
      expect(button(root, action).disabled).toBe(false);
      await click(root, action);
      expect(callService).toHaveBeenCalledTimes(2);
      expect(root.querySelector('[role="alert"]')).toBeNull();
    },
  );

  it.each(["", "0", "-1", "1.5", "32769"])(
    "rejects invalid start power %s and allows stop independently",
    async (value) => {
      const { root, callService } = await mount();
      await enter(root, value);
      await click(root, "Netzladen aktivieren");
      root
        .querySelector("form")!
        .dispatchEvent(
          new Event("submit", { bubbles: true, cancelable: true }),
        );
      await flush();
      expect(callService).not.toHaveBeenCalled();
      expect(button(root, "Netzladen abschalten").disabled).toBe(false);
      await click(root, "Netzladen abschalten");
      expect(callService).toHaveBeenCalledExactlyOnceWith(
        "sax_power",
        "stop_grid_charge",
        { device_id: "registry-device" },
        undefined,
        false,
      );
      expect(field(root).value).toBe(value);
    },
  );

  it("bounds the draft with this device's rated power without silently rewriting it", async () => {
    const { root, callService } = await mount({ reference: "800" });
    expect(field(root).max).toBe("800");
    await enter(root, "801");
    await click(root, "Netzladen aktivieren");
    expect(callService).not.toHaveBeenCalled();
    expect(field(root).value).toBe("801");
    await enter(root, "800");
    await click(root, "Netzladen aktivieren");
    expect(callService).toHaveBeenCalledExactlyOnceWith(
      "sax_power",
      "start_grid_charge",
      { device_id: "registry-device", power: -800 },
      undefined,
      false,
    );
  });

  it("submits the visible DOM value when autofill does not dispatch an input event", async () => {
    const { root, callService } = await mount();
    field(root).value = "1750";
    await click(root, "Netzladen aktivieren");
    expect(callService).toHaveBeenCalledExactlyOnceWith(
      "sax_power",
      "start_grid_charge",
      { device_id: "registry-device", power: -1750 },
      undefined,
      false,
    );
    expect(field(root).value).toBe("1750");
  });

  it("identifies invalid start power without marking stop failures as field errors", async () => {
    const { root, callService } = await mount();
    await enter(root, "0");
    await click(root, "Netzladen aktivieren");
    expect(field(root).getAttribute("aria-invalid")).toBe("true");
    expect(root.querySelector('[role="alert"]')).not.toBeNull();
    await enter(root, "1500");
    expect(field(root).getAttribute("aria-invalid")).toBe("false");
    await enter(root, "0");
    callService.mockRejectedValueOnce(new Error("stop rejected"));
    await click(root, "Netzladen abschalten");
    expect(root.querySelector('[role="alert"]')?.textContent).toContain(
      "fehlgeschlagen",
    );
    expect(field(root).getAttribute("aria-invalid")).toBe("false");
  });

  it.each([
    { canControl: false },
    { deviceId: null },
    { state: "unknown" },
    { state: "unavailable" },
    { missing: true },
  ])(
    "disables unauthorized or unavailable device actions (%j)",
    async (options) => {
      const { root, callService } = await mount(options);
      expect(button(root, "Netzladen aktivieren").disabled).toBe(true);
      expect(button(root, "Netzladen abschalten").disabled).toBe(true);
      await click(root, "Netzladen aktivieren");
      await click(root, "Netzladen abschalten");
      expect(callService).not.toHaveBeenCalled();
    },
  );

  it("disables both actions on connection loss while retaining the draft", async () => {
    const { root, callService, disconnect } = await mount();
    await enter(root, "1500");
    await disconnect();
    expect(button(root, "Netzladen aktivieren").disabled).toBe(true);
    expect(button(root, "Netzladen abschalten").disabled).toBe(true);
    expect(field(root).value).toBe("1500");
    expect(callService).not.toHaveBeenCalled();
  });

  it("permits device actions without an optional charge-power sensor", async () => {
    const { root, callService } = await mount({ telemetry: false });
    expect(button(root, "Netzladen aktivieren").disabled).toBe(false);
    await click(root, "Netzladen abschalten");
    expect(callService).toHaveBeenCalledOnce();
  });
});
