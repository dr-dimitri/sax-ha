import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import GridServingForecastSource from "../src/components/GridServingForecastSource.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "../src/ha";
import type {
  ConnectionEvent,
  GridServingForecastSource as Source,
  HassConnection,
  HomeAssistant,
} from "../src/types";

const apps: App[] = [];
async function flush() {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (cause: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
async function mount(
  options: {
    language?: string;
    source?: string | null;
    canEdit?: boolean;
  } = {},
) {
  const source = shallowRef<Source>({
    pv_sensor:
      options.source === undefined ? "sensor.remaining" : options.source,
    revision: "source-1",
    can_edit: options.canEdit ?? true,
  });
  const listeners = new Map<ConnectionEvent, Set<() => void>>();
  const connection: HassConnection = {
    connected: true,
    async subscribeMessage<T>(callback: (data: T) => void) {
      callback({
        entities: [
          {
            domain: "sensor",
            key: "grid_serving_forecast",
            entity_id: "sensor.sax_forecast",
            name: "PV-Prognose",
            states: {},
            can_control: false,
          },
        ],
      } as T);
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
  const callWS = vi.fn(async (request: Readonly<Record<string, unknown>>) => {
    if (request.type === "sax_power/dashboard/grid_serving/get")
      return { ...source.value };
    if (request.type === "sax_power/dashboard/grid_serving/save") {
      source.value = {
        ...source.value,
        pv_sensor: request.pv_sensor as string | null,
        revision: "source-2",
      };
      return { ...source.value };
    }
    throw new Error("Unexpected WS request");
  });
  const hass = shallowRef<HomeAssistant>({
    language: options.language ?? "de",
    connection,
    states: Object.fromEntries(
      [
        ["sensor.remaining", "Heute verbleibend", "kWh"],
        ["sensor.other", "Neue Anlage", "Wh"],
        ["sensor.power", "Momentane Leistung", "W"],
        ["sensor.sax_forecast", "SAX Prognose", "kWh"],
      ].map(([entity_id, friendly_name, unit_of_measurement]) => [
        entity_id,
        {
          entity_id,
          state: "12",
          attributes: {
            friendly_name,
            unit_of_measurement,
            ...(entity_id === "sensor.sax_forecast"
              ? { source_entity_id: source.value.pv_sensor }
              : {}),
          },
        },
      ]),
    ),
    callWS: <T>(request: Readonly<Record<string, unknown>>) =>
      callWS(request) as Promise<T>,
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
      return () => h(GridServingForecastSource, { hass: hass.value });
    },
  });
  apps.push(app);
  app.mount(root);
  await flush();
  async function fire(event: ConnectionEvent) {
    Object.assign(connection, { connected: event === "ready" });
    for (const listener of listeners.get(event) ?? []) listener();
    await flush();
  }
  async function externalSource(value: string | null) {
    source.value = {
      ...source.value,
      pv_sensor: value,
      revision: "source-external",
    };
    const state = hass.value.states["sensor.sax_forecast"];
    hass.value = {
      ...hass.value,
      states: {
        ...hass.value.states,
        [state.entity_id]: {
          ...state,
          attributes: { ...state.attributes, source_entity_id: value },
        },
      },
    };
    await flush();
  }
  return { root, hass, callWS, source, fire, externalSource };
}
function button(root: HTMLElement, text: string) {
  const result = [...root.querySelectorAll<HTMLButtonElement>("button")].find(
    (item) => item.textContent?.trim() === text,
  );
  expect(result).toBeTruthy();
  return result!;
}
async function click(root: HTMLElement, text: string) {
  button(root, text).click();
  await flush();
}
async function select(root: HTMLElement, value: string) {
  const field = root.querySelector("select")!;
  field.value = value;
  field.dispatchEvent(new Event("change", { bubbles: true }));
  await flush();
}
function savedCalls(callWS: ReturnType<typeof vi.fn>) {
  return callWS.mock.calls.filter(([request]) =>
    request.type.endsWith("/save"),
  );
}
afterEach(() => {
  for (const app of apps.splice(0)) app.unmount();
  document.body.replaceChildren();
});

describe("REQ-GRID-SERVING-CHARGE: dashboard PV source", () => {
  it.each(["de", "en-GB"])(
    "shows the confirmed source and suitable energy choices (%s)",
    async (language) => {
      const { root, callWS } = await mount({ language });
      expect(
        root.querySelector(".grid-serving-source__confirmed")?.textContent,
      ).toBe("Heute verbleibend");
      await click(root, language === "de" ? "Bearbeiten" : "Edit");
      expect(
        [...root.querySelectorAll("option")].map((item) => item.value),
      ).toEqual(["", "sensor.remaining", "sensor.other"]);
      expect(document.activeElement).toBe(root.querySelector("select"));
      expect(savedCalls(callWS)).toHaveLength(0);
      expect(root.textContent).toContain(
        language === "de" ? "heute noch erwarteten" : "still expected today",
      );
    },
  );

  it("keeps confirmed selection and prevents duplicate writes until the response arrives", async () => {
    const { root, callWS } = await mount();
    await click(root, "Bearbeiten");
    await select(root, "sensor.other");
    const waiting = deferred<Source>();
    callWS.mockImplementationOnce(() => waiting.promise);
    await click(root, "Speichern");
    expect(root.querySelector("[role=status]")?.textContent).toContain(
      "wird gespeichert",
    );
    expect(
      root.querySelector(".grid-serving-source")?.getAttribute("aria-busy"),
    ).toBe("true");
    expect(
      root.querySelector(".grid-serving-source__confirmed")?.textContent,
    ).toBe("Heute verbleibend");
    expect(root.querySelector("select")?.disabled).toBe(true);
    expect(button(root, "Abbrechen").disabled).toBe(true);
    await click(root, "Speichern");
    root
      .querySelector("form")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flush();
    expect(savedCalls(callWS)).toHaveLength(1);
    expect(savedCalls(callWS)[0][0]).toEqual({
      type: "sax_power/dashboard/grid_serving/save",
      entry_id: "entry-1",
      revision: "source-1",
      pv_sensor: "sensor.other",
    });
    waiting.resolve({
      pv_sensor: "sensor.other",
      revision: "source-2",
      can_edit: true,
    });
    await flush();
    expect(root.querySelector("select")).toBeNull();
    expect(
      root.querySelector(".grid-serving-source__confirmed")?.textContent,
    ).toBe("Neue Anlage");
    expect(root.querySelector("[role=status]")?.textContent).toContain(
      "Quelle gespeichert",
    );
    expect(document.activeElement).toBe(button(root, "Bearbeiten"));
  });

  it.each(["failed", "invalid_sensor", "invalid_unit"])(
    "preserves drafts after %s and supports retry",
    async (code) => {
      const { root, callWS } = await mount();
      await click(root, "Bearbeiten");
      await select(root, "sensor.other");
      callWS.mockRejectedValueOnce({ code });
      await click(root, "Speichern");
      expect(root.querySelector("select")?.value).toBe("sensor.other");
      expect(
        root.querySelector(".grid-serving-source__confirmed")?.textContent,
      ).toBe("Heute verbleibend");
      const alert = root.querySelector<HTMLElement>("[role=alert]")!;
      expect(alert).toBeTruthy();
      expect(
        root.querySelector("select")?.getAttribute("aria-describedby"),
      ).toContain(alert.id);
      if (code !== "failed")
        expect(root.querySelector("select")?.getAttribute("aria-invalid")).toBe(
          "true",
        );
      await click(root, "Speichern");
      expect(savedCalls(callWS)).toHaveLength(2);
      expect(root.querySelector("[role=alert]")).toBeNull();
    },
  );

  it("retains a conflicting draft until explicit reload", async () => {
    const { root, callWS, source } = await mount();
    await click(root, "Bearbeiten");
    await select(root, "sensor.other");
    source.value = {
      pv_sensor: null,
      can_edit: true,
      revision: "source-external",
    };
    callWS.mockRejectedValueOnce({ code: "conflict" });
    await click(root, "Speichern");
    expect(root.querySelector("select")?.value).toBe("sensor.other");
    expect(button(root, "Speichern").disabled).toBe(true);
    await click(root, "Aktuelle Auswahl laden");
    expect(root.querySelector("select")?.value).toBe("");
    await select(root, "sensor.other");
    await click(root, "Speichern");
    expect(savedCalls(callWS).at(-1)![0].revision).toBe("source-external");
  });

  it.each([false, true])(
    "refreshes external source changes without losing an open draft (%s)",
    async (editing) => {
      const { root, externalSource, callWS } = await mount();
      if (editing) {
        await click(root, "Bearbeiten");
        await select(root, "");
      }
      await externalSource("sensor.other");
      expect(
        root.querySelector(".grid-serving-source__confirmed")?.textContent,
      ).toBe("Neue Anlage");
      if (editing) {
        expect(root.querySelector("select")?.value).toBe("");
        expect(button(root, "Speichern").disabled).toBe(true);
        expect(root.querySelector("[role=alert]")?.textContent).toContain(
          "zwischenzeitlich",
        );
      }
      expect(savedCalls(callWS)).toHaveLength(0);
    },
  );

  it("ignores a late save response after disconnect and keeps the draft for retry", async () => {
    const { root, callWS, fire } = await mount();
    await click(root, "Bearbeiten");
    await select(root, "sensor.other");
    const waiting = deferred<Source>();
    callWS.mockImplementationOnce(() => waiting.promise);
    await click(root, "Speichern");
    await fire("disconnected");
    waiting.resolve({
      pv_sensor: "sensor.other",
      can_edit: true,
      revision: "source-2",
    });
    await flush();
    expect(
      root.querySelector(".grid-serving-source__confirmed")?.textContent,
    ).toBe("Heute verbleibend");
    expect(root.querySelector("select")?.value).toBe("sensor.other");
    expect(root.querySelector("[role=alert]")?.textContent).toContain(
      "Keine Verbindung",
    );
    await fire("ready");
    await flush();
    expect(button(root, "Speichern").disabled).toBe(false);
    await click(root, "Speichern");
    expect(savedCalls(callWS)).toHaveLength(2);
  });

  it("coalesces source changes during a delayed edit read and opens the latest source", async () => {
    const { root, callWS, externalSource } = await mount();
    const waiting = deferred<Source>();
    callWS.mockImplementationOnce(() => waiting.promise);
    await click(root, "Bearbeiten");
    await externalSource("sensor.other");
    await externalSource(null);
    expect(callWS).toHaveBeenCalledTimes(2);
    waiting.resolve({
      pv_sensor: "sensor.remaining",
      revision: "source-1",
      can_edit: true,
    });
    await flush();
    await flush();
    expect(callWS).toHaveBeenCalledTimes(3);
    expect(root.querySelector("select")?.value).toBe("");
    expect(
      root.querySelector(".grid-serving-source__confirmed")?.textContent,
    ).toBe("Keine Quelle ausgewählt");
    expect(document.activeElement).toBe(root.querySelector("select"));
  });

  it("retains the draft when an external source supersedes an in-flight save", async () => {
    const { root, callWS, externalSource } = await mount();
    await click(root, "Bearbeiten");
    await select(root, "sensor.other");
    const waiting = deferred<Source>();
    callWS.mockImplementationOnce(() => waiting.promise);
    await click(root, "Speichern");
    await externalSource(null);
    waiting.resolve({
      pv_sensor: "sensor.other",
      revision: "source-2",
      can_edit: true,
    });
    await flush();
    await flush();
    expect(root.querySelector("select")?.value).toBe("sensor.other");
    expect(
      root.querySelector(".grid-serving-source__confirmed")?.textContent,
    ).toBe("Keine Quelle ausgewählt");
    expect(root.querySelector("[role=alert]")?.textContent).toContain(
      "zwischenzeitlich",
    );
    expect(button(root, "Speichern").disabled).toBe(true);
    expect(savedCalls(callWS)).toHaveLength(1);
  });

  it("reloads after reconnect during a read without accepting the old connection response", async () => {
    const { root, callWS, fire, source } = await mount();
    const waiting = deferred<Source>();
    callWS.mockImplementationOnce(() => waiting.promise);
    await click(root, "Bearbeiten");
    await fire("disconnected");
    source.value = {
      pv_sensor: "sensor.other",
      can_edit: true,
      revision: "source-reconnected",
    };
    await fire("ready");
    waiting.resolve({
      pv_sensor: "sensor.remaining",
      revision: "source-1",
      can_edit: true,
    });
    await flush();
    await flush();
    expect(root.querySelector("select")?.value).toBe("sensor.other");
    expect(
      root.querySelector(".grid-serving-source__confirmed")?.textContent,
    ).toBe("Neue Anlage");
    expect(root.querySelector("[role=alert]")).toBeNull();
  });

  it("allows explicit clearing and explains the effect on a positive forecast threshold", async () => {
    const { root, callWS } = await mount();
    await click(root, "Bearbeiten");
    await select(root, "");
    await click(root, "Speichern");
    expect(savedCalls(callWS)[0][0].pv_sensor).toBeNull();
    expect(root.textContent).toContain("Ohne Quelle greift die Ladepause");
  });

  it("disables editing after permission revocation without discarding the draft", async () => {
    const { root, callWS } = await mount();
    await click(root, "Bearbeiten");
    await select(root, "sensor.other");
    callWS.mockRejectedValueOnce({ code: "forbidden" });
    await click(root, "Speichern");
    expect(root.querySelector("select")?.value).toBe("sensor.other");
    expect(button(root, "Speichern").disabled).toBe(true);
    expect(root.textContent).toContain("Nur Administratoren");
  });

  it("keeps the confirmed source read-only for nonadministrators", async () => {
    const { root, callWS } = await mount({ canEdit: false });
    expect(root.querySelector("button")).toBeNull();
    expect(root.textContent).toContain("Heute verbleibend");
    expect(savedCalls(callWS)).toHaveLength(0);
  });

  it("does not write when cancelling a changed selection", async () => {
    const { root, callWS } = await mount();
    await click(root, "Bearbeiten");
    await select(root, "sensor.other");
    await click(root, "Abbrechen");
    expect(root.querySelector("select")).toBeNull();
    expect(savedCalls(callWS)).toHaveLength(0);
    expect(
      root.querySelector(".grid-serving-source__confirmed")?.textContent,
    ).toBe("Heute verbleibend");
  });
});
