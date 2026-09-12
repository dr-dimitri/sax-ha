import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import EntityControl from "../src/components/EntityControl.vue";
import EntityValue from "../src/components/EntityValue.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "../src/ha";
import type {
  ConnectionEvent,
  DashboardEntityMetadata,
  DashboardMetadata,
  EntityDomain,
  HassConnection,
  HassEntity,
  HomeAssistant,
} from "../src/types";

const applications: App[] = [];

async function flush(): Promise<void> {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}

function deferred(): {
  promise: Promise<void>;
  resolve: () => void;
  reject: (error: Error) => void;
} {
  let resolve!: () => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<void>((done, fail) => {
    resolve = done;
    reject = fail;
  });
  return { promise, resolve, reject };
}

async function mount(
  domain: EntityDomain,
  options: {
    state?: string;
    attributes?: Record<string, unknown>;
    language?: string;
    canControl?: boolean;
    copies?: number;
    missing?: boolean;
    valueOnly?: boolean;
    entityKey?: string;
    confirmSwitch?: boolean;
    hideConfirmedLabel?: boolean;
  } = {},
) {
  const entityId = `${domain}.renamed_by_user`;
  const metadata: DashboardEntityMetadata = {
    entity_id: entityId,
    domain,
    key: options.entityKey ?? "example",
    name: "Zielwert",
    states: { automatic: "Automatisch", manual: "Manuell" },
    can_control: options.canControl ?? true,
  };
  const state: HassEntity = {
    entity_id: entityId,
    state: options.state ?? "50",
    attributes: {
      min: 10,
      max: 90,
      step: 0.5,
      unit_of_measurement: "%",
      ...options.attributes,
    },
  };
  const listeners = new Map<ConnectionEvent, () => void>();
  let emitMetadata: (data: DashboardMetadata) => void = () => {};
  const connection: HassConnection = {
    connected: true,
    async subscribeMessage<T>(callback: (message: T) => void) {
      emitMetadata = (data) => callback(data as T);
      emitMetadata({ entities: options.missing ? [] : [metadata] });
      return vi.fn<() => void>();
    },
    addEventListener: (event, listener) => listeners.set(event, listener),
    removeEventListener: (event) => {
      listeners.delete(event);
    },
  };
  const callService = vi.fn<NonNullable<HomeAssistant["callService"]>>();
  callService.mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    connection,
    states: { [entityId]: state },
    callService,
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
          Array.from({ length: options.copies ?? 1 }, () =>
            options.valueOnly
              ? h(EntityValue, {
                  domain,
                  entityKey: options.entityKey ?? "example",
                })
              : h(EntityControl, {
                  domain: domain as "switch" | "number" | "time" | "select",
                  entityKey: options.entityKey ?? "example",
                  confirmSwitch: options.confirmSwitch,
                  hideConfirmedLabel: options.hideConfirmedLabel,
                }),
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
    callService,
    metadata,
    emitMetadata: (entities: DashboardEntityMetadata[]) =>
      emitMetadata({ entities }),
    disconnect: () => listeners.get("disconnected")?.(),
    async updateState(value: string, attributes = state.attributes) {
      hass.value = {
        ...hass.value,
        states: {
          ...hass.value.states,
          [entityId]: { ...state, state: value, attributes },
        },
      };
      await flush();
    },
  };
}

function input(root: HTMLElement): HTMLInputElement {
  return root.querySelector("input")!;
}

function enter(root: HTMLElement, value: string): void {
  input(root).value = value;
  input(root).dispatchEvent(new Event("input", { bubbles: true }));
}

function submit(root: HTMLElement): void {
  root
    .querySelector("form")!
    .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
}

afterEach(() => {
  for (const app of applications.splice(0)) app.unmount();
  document.body.replaceChildren();
});

describe("shared dashboard controls", () => {
  it.each(["de", "en-GB"])(
    "retains the accessible confirmed value while hiding its label (%s)",
    async (language) => {
      const { root, callService, updateState } = await mount("number", {
        language,
        hideConfirmedLabel: true,
      });
      const value = root.querySelector(".entity-control__value")!;
      expect(value.textContent?.trim()).toBe("50 %");
      expect(
        input(root).getAttribute("aria-describedby")?.split(" "),
      ).toContain(value.id);
      enter(root, "72.5");
      await flush();
      expect(value.textContent?.trim()).toBe("50 %");
      expect(callService).not.toHaveBeenCalled();
      submit(root);
      await flush();
      expect(value.textContent?.trim()).toBe("50 %");
      await updateState("72.5");
      expect(value.textContent?.trim()).toBe(
        language === "de" ? "72,5 %" : "72.5 %",
      );
      expect(input(root).value).toBe("72.5");
    },
  );

  it("labels a number, uses HA bounds, and submits only an explicit action", async () => {
    const { root, callService, updateState } = await mount("number");
    const field = input(root);
    expect(root.querySelector("label")?.htmlFor).toBe(field.id);
    expect(root.querySelector("label")?.textContent).toBe("Zielwert");
    expect(field.min).toBe("10");
    expect(field.max).toBe("90");
    expect(field.step).toBe("0.5");
    expect(field.value).toBe("50");
    expect(root.querySelector("button")?.textContent).toBe("Übernehmen");
    expect(root.textContent).toContain("Bestätigter Wert: 50 %");
    expect(callService).not.toHaveBeenCalled();

    enter(root, "72.5");
    await flush();
    expect(callService).not.toHaveBeenCalled();
    expect(root.textContent).toContain("Bestätigter Wert: 50 %");
    submit(root);
    await flush();
    expect(callService).toHaveBeenCalledExactlyOnceWith(
      "number",
      "set_value",
      { value: 72.5 },
      { entity_id: "number.renamed_by_user" },
      false,
    );
    expect(root.textContent).toContain("Bestätigter Wert: 50 %");

    await updateState("72.5");
    expect(root.textContent).toContain("Bestätigter Wert: 72,5 %");
    expect(field.value).toBe("72.5");
  });

  it("preserves a typed draft across unrelated HA state updates", async () => {
    const { root, hass, callService } = await mount("number");
    enter(root, "71");
    hass.value = {
      ...hass.value,
      states: {
        ...hass.value.states,
        "sensor.other": {
          entity_id: "sensor.other",
          state: "12",
          attributes: {},
        },
      },
    };
    await flush();
    expect(input(root).value).toBe("71");
    expect(callService).not.toHaveBeenCalled();
  });

  it.each(["91", "10.25", ""])(
    "rejects the invalid number draft %s without calling a service",
    async (value) => {
      const { root, callService } = await mount("number");
      enter(root, value);
      submit(root);
      await flush();
      expect(callService).not.toHaveBeenCalled();
      expect(root.querySelector('[role="alert"]')?.textContent).toContain(
        "gültigen Wert",
      );
      expect(root.textContent).toContain("Bestätigter Wert: 50 %");
    },
  );

  it("submits time explicitly and waits for the HA state update", async () => {
    const { root, callService, updateState } = await mount("time", {
      state: "04:30:00",
      attributes: { unit_of_measurement: undefined },
    });
    expect(input(root).type).toBe("time");
    expect(input(root).step).toBe("60");
    enter(root, "05:45");
    await flush();
    expect(callService).not.toHaveBeenCalled();
    submit(root);
    await flush();
    expect(callService).toHaveBeenCalledExactlyOnceWith(
      "time",
      "set_value",
      { time: "05:45:00" },
      { entity_id: "time.renamed_by_user" },
      false,
    );
    expect(root.textContent).toContain("04:30:00");
    await updateState("05:45:00");
    expect(root.textContent).toContain("05:45:00");
  });

  it("shows legacy time states as minutes without writing and submits zero seconds explicitly", async () => {
    const { root, callService, updateState } = await mount("time", {
      state: "04:30:19",
      attributes: { unit_of_measurement: undefined },
    });
    expect(input(root).value).toBe("04:30");
    expect(input(root).step).toBe("60");
    expect(root.textContent).toContain("Bestätigter Wert: 04:30:19");
    expect(callService).not.toHaveBeenCalled();
    enter(root, "04:30:45");
    await flush();
    expect(input(root).value).toBe("04:30");
    expect(callService).not.toHaveBeenCalled();
    submit(root);
    await flush();
    expect(callService).toHaveBeenCalledExactlyOnceWith(
      "time",
      "set_value",
      { time: "04:30:00" },
      { entity_id: "time.renamed_by_user" },
      false,
    );
    expect(root.textContent).toContain("Bestätigter Wert: 04:30:19");
    await updateState("05:45:27");
    expect(input(root).value).toBe("05:45");
    expect(callService).toHaveBeenCalledOnce();
  });

  it.each([
    ["storage_switch", false, true],
    ["example", true, true],
    ["timed_charge_january", false, false],
    ["timed_charge", false, false],
  ] as const)(
    "limits the compact switch target to storage or confirmation controls (%s, %s)",
    async (entityKey, confirmSwitch, compact) => {
      const { root } = await mount("switch", {
        entityKey,
        confirmSwitch,
        state: "off",
      });
      const target = root.querySelector<HTMLLabelElement>(
        ".entity-control__switch-target",
      )!;
      expect(
        target.classList.contains("entity-control__switch-target--compact"),
      ).toBe(compact);
      expect(target.htmlFor).toBe(input(root).id);
      expect(input(root).getAttribute("role")).toBe("switch");
    },
  );

  it("retains explicit confirmation when the compact storage target is clicked", async () => {
    const { root, callService } = await mount("switch", {
      entityKey: "storage_switch",
      confirmSwitch: true,
      state: "off",
    });
    const dialog = root.querySelector("dialog")!;
    dialog.showModal = vi.fn(() => {
      dialog.open = true;
    });
    dialog.close = vi.fn(() => {
      dialog.open = false;
    });
    root.querySelector<HTMLElement>(".entity-control__switch-target")!.click();
    await flush();
    expect(dialog.open).toBe(true);
    expect(input(root).checked).toBe(false);
    expect(callService).not.toHaveBeenCalled();
    dialog.querySelectorAll("button")[1].click();
    await flush();
    expect(dialog.open).toBe(false);
    expect(callService).toHaveBeenCalledExactlyOnceWith(
      "switch",
      "turn_on",
      {},
      { entity_id: "switch.renamed_by_user" },
      false,
    );
    expect(input(root).checked).toBe(false);
  });

  it("keeps a read-only compact storage target disabled", async () => {
    const { root, callService } = await mount("switch", {
      entityKey: "storage_switch",
      confirmSwitch: true,
      state: "off",
      canControl: false,
    });
    root.querySelector<HTMLElement>(".entity-control__switch-target")!.click();
    await flush();
    expect(input(root).disabled).toBe(true);
    expect(root.querySelector("dialog")!.open).toBe(false);
    expect(callService).not.toHaveBeenCalled();
  });

  it.each([
    ["off", true, "turn_on"],
    ["on", false, "turn_off"],
  ] as const)(
    "uses an explicit switch action from %s and does not optimistically change it",
    async (initial, desired, service) => {
      const { root, callService, updateState } = await mount("switch", {
        state: initial,
      });
      const action = deferred();
      callService.mockReturnValueOnce(action.promise);
      const field = input(root);
      expect(field.getAttribute("role")).toBe("switch");
      field.checked = desired;
      field.dispatchEvent(new Event("change", { bubbles: true }));
      await flush();
      expect(field.checked).toBe(!desired);
      expect(field.disabled).toBe(true);
      expect(root.querySelector("form")?.getAttribute("aria-busy")).toBe(
        "true",
      );
      expect(callService).toHaveBeenCalledExactlyOnceWith(
        "switch",
        service,
        {},
        { entity_id: "switch.renamed_by_user" },
        false,
      );
      action.resolve();
      await flush();
      expect(field.checked).toBe(!desired);
      await updateState(desired ? "on" : "off");
      expect(field.checked).toBe(desired);
    },
  );

  it("takes select options and translated names from HA and retains the confirmed selection", async () => {
    const { root, callService, updateState, metadata, emitMetadata } =
      await mount("select", {
        state: "automatic",
        attributes: { options: ["automatic", "manual"] },
      });
    const field = root.querySelector("select")!;
    expect(root.querySelector("label")?.htmlFor).toBe(field.id);
    expect([...field.options].map((option) => option.text)).toEqual([
      "Automatisch",
      "Manuell",
    ]);
    expect(field.value).toBe("automatic");
    field.value = "manual";
    field.dispatchEvent(new Event("change", { bubbles: true }));
    await flush();
    expect(field.value).toBe("automatic");
    expect(callService).toHaveBeenCalledExactlyOnceWith(
      "select",
      "select_option",
      { option: "manual" },
      { entity_id: "select.renamed_by_user" },
      false,
    );
    await updateState("manual");
    expect(field.value).toBe("manual");
    emitMetadata([{ ...metadata, name: "Neuer Anzeigename" }]);
    await flush();
    expect(root.querySelector("label")?.textContent).toBe("Neuer Anzeigename");
  });

  it("shares pending and sanitized errors between copies of one control", async () => {
    const { root, callService } = await mount("number", { copies: 2 });
    const action = deferred();
    callService.mockReturnValueOnce(action.promise);
    const fields = [...root.querySelectorAll("input")];
    expect(new Set(fields.map((field) => field.id)).size).toBe(2);
    enter(root, "80");
    submit(root);
    const secondForm = root.querySelectorAll("form")[1];
    secondForm.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    await flush();
    expect(callService).toHaveBeenCalledOnce();
    expect(fields.every((field) => field.disabled)).toBe(true);
    expect(root.querySelectorAll('[role="status"]')).toHaveLength(2);

    action.reject(new Error("secret backend stack details"));
    await flush();
    expect(fields.every((field) => !field.disabled)).toBe(true);
    expect(root.querySelectorAll('[role="alert"]')).toHaveLength(2);
    expect(root.textContent).toContain("Die Änderung ist fehlgeschlagen");
    expect(root.textContent).not.toContain("secret");
    expect(root.textContent).toContain("Bestätigter Wert: 50 %");
  });

  it.each(["unknown", "unavailable"])(
    "disables %s states without inventing a numeric value",
    async (state) => {
      const { root, callService } = await mount("number", { state });
      expect(input(root).disabled).toBe(true);
      expect(input(root).value).toBe("");
      expect(root.textContent).toContain("Nicht verfügbar");
      expect(root.textContent).not.toContain("0 %");
      submit(root);
      await flush();
      expect(callService).not.toHaveBeenCalled();
    },
  );

  it("disables read-only entities and disappears when no entity is registered", async () => {
    const { root, callService, emitMetadata } = await mount("number", {
      canControl: false,
    });
    expect(input(root).disabled).toBe(true);
    expect(root.textContent).toContain("Keine Berechtigung zum Ändern");
    submit(root);
    await flush();
    expect(callService).not.toHaveBeenCalled();
    emitMetadata([]);
    await flush();
    expect(root.querySelector("form")).toBeNull();
    expect(root.textContent).toBe("");
  });

  it("removes stale controls on disconnect without issuing a write", async () => {
    const { root, callService, disconnect } = await mount("switch", {
      state: "on",
    });
    disconnect();
    await flush();
    expect(root.querySelector("input")).toBeNull();
    expect(callService).not.toHaveBeenCalled();
  });

  it("renders English labels and service errors without raw diagnostics", async () => {
    const { root, callService } = await mount("number", { language: "en-GB" });
    expect(root.querySelector("button")?.textContent).toBe("Apply");
    expect(root.textContent).toContain("Confirmed value: 50 %");
    callService.mockRejectedValueOnce(new Error("internal diagnostic"));
    submit(root);
    await flush();
    expect(root.querySelector('[role="alert"]')?.textContent).toContain(
      "The change failed",
    );
    expect(root.textContent).not.toContain("internal diagnostic");
  });

  it("renders live values with dynamic names and hides missing optional entities", async () => {
    const { root, updateState, emitMetadata, metadata } = await mount(
      "sensor",
      {
        valueOnly: true,
        state: "12.5",
        attributes: { unit_of_measurement: "kWh" },
      },
    );
    expect(root.querySelector(".entity-value__state")?.textContent).toBe(
      "12,5 kWh",
    );
    await updateState("unavailable");
    expect(root.querySelector(".entity-value__state")?.textContent).toBe(
      "Nicht verfügbar",
    );
    emitMetadata([{ ...metadata, name: "Aktueller Name" }]);
    await flush();
    expect(root.querySelector(".entity-value__name")?.textContent).toBe(
      "Aktueller Name",
    );
    emitMetadata([]);
    await flush();
    expect(root.querySelector(".entity-value")).toBeNull();
  });
});
