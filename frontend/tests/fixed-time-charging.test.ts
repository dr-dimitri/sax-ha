import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createApp,
  h,
  nextTick,
  provide,
  ref,
  shallowRef,
  type App,
} from "vue";
import TimeOfUseChargingSettings from "../src/components/TimeOfUseChargingSettings.vue";
import DynamicChargingSettings from "../src/components/DynamicChargingSettings.vue";
import {
  SAX_DASHBOARD_KEY,
  useSaxDashboard,
  type SaxDashboard,
} from "../src/ha";
import { chargingSample } from "../src/charging-preview-data";
import type { HomeAssistant, TariffProfile } from "../src/types";
const apps: App[] = [];
async function flush() {
  for (let i = 0; i < 6; i++) {
    await Promise.resolve();
    await nextTick();
  }
}
async function mount(
  type: "time_of_use" | "dynamic",
  options: {
    active?: boolean;
    readonly?: boolean;
    language?: string;
    threshold?: string;
  } = {},
) {
  const sample = chargingSample(options.language ?? "de");
  sample.metadata.push({
    domain: "switch",
    key: "bridge_charge_enabled",
    entity_id: "switch.bridge",
    name: "Bridge",
    states: {},
    can_control: !options.readonly,
  });
  sample.states["switch.bridge"] = {
    entity_id: "switch.bridge",
    state: "off",
    attributes: {},
  };
  if (options.threshold)
    sample.states["number.renamed_timed_charge_min_soc"]!.state =
      options.threshold;
  if (options.readonly)
    sample.metadata.forEach((item) => {
      item.can_control = false;
    });
  let stored: TariffProfile = {
    tariff_type: type,
    base_price_ct_kwh: 32,
    feed_in_price_ct_kwh: 8,
    windows: [],
    revision: "1",
    can_edit: true,
    can_configure: !options.readonly,
    automation_enabled: false,
    fixed_time_charging: {
      enabled: !!options.active,
      start: options.active ? "02:00:00" : null,
    },
  };
  const callWS = vi.fn(async (request: Readonly<Record<string, unknown>>) => {
    if (request.type === "sax_power/dashboard/tariff/configure") {
      stored = {
        ...stored,
        revision: String(Number(stored.revision) + 1),
        fixed_time_charging: request.fixed_time_charging
          ? {
              ...(request.fixed_time_charging as {
                enabled: boolean;
                start: string;
              }),
              start: `${(request.fixed_time_charging as { start: string }).start}:00`,
            }
          : { ...stored.fixed_time_charging!, enabled: false },
      };
    }
    return structuredClone(stored);
  });
  const callService = vi.fn().mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    states: sample.states,
    callService,
    connection: {
      connected: true,
      addEventListener() {},
      removeEventListener() {},
      async subscribeMessage<T>(callback: (result: T) => void) {
        callback({ entities: sample.metadata } as T);
        return () => {};
      },
    },
    callWS: <T>(request: Readonly<Record<string, unknown>>) =>
      callWS(request) as Promise<T>,
  });
  const editing = ref(true);
  const settings = ref<{ submit(): Promise<boolean>; reset(): boolean }>();
  let dashboard!: SaxDashboard;
  const root = document.createElement("div");
  document.body.append(root);
  const app = createApp({
    setup() {
      dashboard = useSaxDashboard(
        () => hass.value,
        () => "entry-1",
      );
      provide(SAX_DASHBOARD_KEY, dashboard);
      void dashboard.loadTariff();
      return () =>
        h(
          type === "dynamic"
            ? DynamicChargingSettings
            : TimeOfUseChargingSettings,
          { ref: settings, editing: editing.value },
        );
    },
  });
  app.mount(root);
  apps.push(app);
  await flush();
  callWS.mockClear();
  return {
    root,
    dashboard,
    callWS,
    callService,
    submit: () => settings.value!.submit(),
    reset: () => settings.value!.reset(),
    async edit(value: boolean) {
      editing.value = value;
      await flush();
    },
  };
}
function fixed(root: Element) {
  return root.querySelector<HTMLButtonElement>(
    '[data-method="fixed_time"], [data-strategy="fixed_time"]',
  )!;
}
function input(root: Element) {
  return root.querySelector<HTMLInputElement>(
    ".fixed-time-charging-input input",
  )!;
}
async function fill(root: Element, value: string) {
  input(root).value = value;
  input(root).dispatchEvent(new Event("input", { bubbles: true }));
  await flush();
}
afterEach(() => {
  apps.splice(0).forEach((app) => app.unmount());
  document.body.replaceChildren();
});
for (const type of ["time_of_use", "dynamic"] as const)
  describe(`REQ-FIXED-TIME-GRID-CHARGE ${type}`, () => {
    it("requires explicit apply with the visible time and uses the grid SOC target", async () => {
      const fixture = await mount(type);
      fixed(fixture.root).click();
      await flush();
      expect(fixture.callWS).not.toHaveBeenCalled();
      expect(input(fixture.root).value).toBe("02:00");
      expect(fixture.root.querySelector(".month-selection")).not.toBeNull();
      const labels = [
        ...fixture.root.querySelectorAll(".entity-control label"),
      ].map((label) => label.textContent);
      expect(labels).toContain("Max SOC (%)");
      expect(labels.join(" ")).not.toContain("Ladestart unter");
      await fill(fixture.root, "00:00");
      expect(await fixture.submit()).toBe(true);
      await flush();
      expect(fixture.callWS).toHaveBeenCalledExactlyOnceWith({
        type: "sax_power/dashboard/tariff/configure",
        entry_id: "entry-1",
        tariff_type: type,
        revision: "1",
        fixed_time_charging: { enabled: true, start: "00:00" },
      });
      expect(
        fixture.root.querySelector(".fixed-time-charging-summary")?.textContent,
      ).toContain("00:00");
      expect(fixture.dashboard.tariff.value?.automation_enabled).toBe(false);
    });
    it.each(["02", "2:", "24:00", "12:6", ""])(
      "rejects incomplete or invalid time %s without writing",
      async (time) => {
        const fixture = await mount(type);
        fixed(fixture.root).click();
        await flush();
        await fill(fixture.root, time);
        expect(await fixture.submit()).toBe(false);
        await flush();
        expect(fixture.callWS).not.toHaveBeenCalled();
        expect(input(fixture.root).value).toBe(time);
        expect(input(fixture.root).getAttribute("aria-invalid")).toBe("true");
        expect(document.activeElement).toBe(input(fixture.root));
      },
    );
    it("keeps confirmed time and draft on failure, marks pending immediately and prevents duplicates", async () => {
      const fixture = await mount(type, { active: true });
      await fill(fixture.root, "03:15");
      let reject!: (cause: unknown) => void;
      fixture.callWS.mockImplementationOnce(
        () =>
          new Promise<TariffProfile>((_, fail) => {
            reject = fail;
          }),
      );
      const first = fixture.submit();
      expect(await fixture.submit()).toBe(false);
      await flush();
      expect(fixture.callWS).toHaveBeenCalledTimes(1);
      expect(input(fixture.root).disabled).toBe(true);
      expect(fixed(fixture.root).disabled).toBe(true);
      expect(
        fixture.root.querySelector("[role=status]")?.textContent,
      ).toContain("wird übernommen");
      expect(
        fixture.root.querySelector(".fixed-time-charging-summary")?.textContent,
      ).toContain("02:00");
      expect(fixture.reset()).toBe(false);
      reject(new Error("offline"));
      expect(await first).toBe(false);
      await flush();
      await fixture.edit(false);
      await fixture.edit(true);
      expect(input(fixture.root).value).toBe("03:15");
      expect(fixture.root.querySelector("[role=alert]")?.textContent).toContain(
        "Entwurf bleibt erhalten",
      );
      expect(
        fixture.root.querySelector(".fixed-time-charging-summary")?.textContent,
      ).toContain("02:00");
    });
    it.each([false, true])(
      "saves grid target below the irrelevant old threshold atomically when fixed is active=%s",
      async (active) => {
        const fixture = await mount(type, { active, threshold: "70" });
        if (!active) {
          fixed(fixture.root).click();
          await flush();
        }
        const target = fixture.root.querySelector<HTMLInputElement>(
          'input[id$="-timed_charge_max_soc"]',
        )!;
        target.value = "40";
        target.dispatchEvent(new Event("input", { bubbles: true }));
        await flush();
        expect(await fixture.submit()).toBe(true);
        await flush();
        expect(fixture.callService).not.toHaveBeenCalled();
        expect(fixture.callWS).toHaveBeenCalledExactlyOnceWith({
          type: "sax_power/dashboard/tariff/configure",
          entry_id: "entry-1",
          tariff_type: type,
          revision: "1",
          fixed_time_charging: { enabled: true, start: "02:00" },
          charging_settings: { timed_charge_max_soc: 40 },
        });
      },
    );
    it("validates the visible committed time even when no input event is dispatched", async () => {
      const fixture = await mount(type);
      fixed(fixture.root).click();
      await flush();
      input(fixture.root).value = "05:45";
      expect(await fixture.submit()).toBe(true);
      expect(fixture.callWS.mock.calls[0]?.[0]).toMatchObject({
        fixed_time_charging: { enabled: true, start: "05:45" },
      });
    });
    it("preserves the time draft after a revision conflict and retries with the refreshed revision", async () => {
      const fixture = await mount(type, { active: true });
      await fill(fixture.root, "03:30");
      fixture.callWS
        .mockRejectedValueOnce({ code: "conflict" })
        .mockResolvedValueOnce({
          ...fixture.dashboard.tariff.value!,
          revision: "2",
        });
      expect(await fixture.submit()).toBe(false);
      await flush();
      expect(input(fixture.root).value).toBe("03:30");
      expect(fixture.root.querySelector("[role=alert]")?.textContent).toContain(
        "inzwischen geändert",
      );
      expect(await fixture.submit()).toBe(true);
      expect(fixture.callWS.mock.calls.at(-1)?.[0]).toMatchObject({
        revision: "2",
        fixed_time_charging: { enabled: true, start: "03:30" },
      });
    });
    it("leaves fixed time and selects the next method in one configuration request", async () => {
      const fixture = await mount(type, { active: true });
      fixture.root
        .querySelector<HTMLButtonElement>(
          type === "dynamic"
            ? '[data-strategy="relative"]'
            : '[data-method="fixed"]',
        )!
        .click();
      await flush();
      expect(fixture.callService).not.toHaveBeenCalled();
      expect(fixture.callWS).toHaveBeenCalledExactlyOnceWith({
        type: "sax_power/dashboard/tariff/configure",
        entry_id: "entry-1",
        tariff_type: type,
        revision: "1",
        charging_method: type === "dynamic" ? "relative" : "fixed",
      });
    });
    it("disables editing without permission and shows the confirmed method in English", async () => {
      const fixture = await mount(type, {
        active: true,
        readonly: true,
        language: "en",
      });
      expect(fixed(fixture.root).disabled).toBe(true);
      expect(input(fixture.root).disabled).toBe(true);
      expect(fixture.root.textContent).toContain("Start at a fixed time");
      expect(fixture.root.textContent).toContain("Active months");
      expect(fixture.callWS).not.toHaveBeenCalled();
    });
  });
