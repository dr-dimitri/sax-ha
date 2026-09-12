import { afterEach, describe, expect, it, vi } from "vitest";
import { effectScope, nextTick, shallowRef } from "vue";
import { useSaxDashboard } from "../src/ha";
import type {
  ConnectionEvent,
  DashboardEntityMetadata,
  DashboardMetadata,
  HassConnection,
  HassEntity,
  HomeAssistant,
  Unsubscribe,
} from "../src/types";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

class Connection implements HassConnection {
  connected = true;
  listeners = new Map<ConnectionEvent, Set<() => void>>();
  subscriptions: {
    callback: (message: DashboardMetadata) => void;
    unsubscribe: ReturnType<typeof vi.fn>;
  }[] = [];
  subscribe = vi.fn((): Promise<Unsubscribe> | undefined => undefined);
  requests: Readonly<Record<string, unknown>>[] = [];
  options: ({ resubscribe?: boolean } | undefined)[] = [];

  subscribeMessage<T>(
    callback: (message: T) => void,
    message: Readonly<Record<string, unknown>>,
    options?: { resubscribe?: boolean },
  ): Promise<Unsubscribe> {
    const unsubscribe = vi.fn(async () => {});
    this.subscriptions.push({
      callback: (payload) => callback(payload as T),
      unsubscribe,
    });
    this.requests.push(message);
    this.options.push(options);
    return this.subscribe() ?? Promise.resolve(unsubscribe);
  }

  addEventListener(event: ConnectionEvent, listener: () => void): void {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event)!.add(listener);
  }

  removeEventListener(event: ConnectionEvent, listener: () => void): void {
    this.listeners.get(event)?.delete(listener);
  }

  fire(event: ConnectionEvent): void {
    this.connected = event === "ready";
    for (const listener of this.listeners.get(event) ?? []) listener();
  }

  emit(
    entities: DashboardEntityMetadata[],
    index = this.subscriptions.length - 1,
  ) {
    this.subscriptions[index]!.callback({ entities });
  }
}

function metadata(
  domain: DashboardEntityMetadata["domain"] = "number",
  changes: Partial<DashboardEntityMetadata> = {},
): DashboardEntityMetadata {
  return {
    entity_id: `${domain}.battery_target`,
    domain,
    key: "target",
    name: "Zielwert",
    states: {},
    can_control: true,
    ...changes,
  };
}

function state(
  item: DashboardEntityMetadata,
  changes: Partial<HassEntity> = {},
): HassEntity {
  return {
    entity_id: item.entity_id,
    state: "50",
    attributes: {
      min: 0,
      max: 100,
      step: 0.1,
      unit_of_measurement: "%",
      friendly_name: "Batterie Zielwert",
    },
    ...changes,
  };
}

const scopes: ReturnType<typeof effectScope>[] = [];

function setup(
  items: DashboardEntityMetadata[] = [metadata()],
  connection = new Connection(),
) {
  const hass = shallowRef<HomeAssistant | undefined>({
    language: "de",
    states: Object.fromEntries(
      items.map((item) => [item.entity_id, state(item)]),
    ),
    connection,
    callService: vi.fn().mockResolvedValue({}),
  });
  const entryId = shallowRef<string | undefined>("entry-1");
  const scope = effectScope();
  scopes.push(scope);
  const dashboard = scope.run(() =>
    useSaxDashboard(
      () => hass.value,
      () => entryId.value,
    ),
  )!;
  if (connection.subscriptions.length) connection.emit(items);
  return { hass, connection, entryId, scope, dashboard };
}

async function flush(): Promise<void> {
  await nextTick();
  await Promise.resolve();
}

afterEach(() => {
  for (const scope of scopes.splice(0)) scope.stop();
});

describe("SAX entity binding (REQ-VUE-ENTITY-BINDING)", () => {
  it("uses one entry-scoped metadata subscription and only HA's existing states", async () => {
    const { hass, connection, dashboard } = setup();
    expect(connection.requests).toEqual([
      {
        type: "sax_power/dashboard/subscribe",
        entry_id: "entry-1",
        language: "de",
      },
    ]);
    expect(connection.options).toEqual([{ resubscribe: false }]);
    expect(dashboard.ready.value).toBe(true);
    expect(dashboard.entity("number", "target")?.displayValue).toBe("50 %");
    hass.value = {
      ...hass.value!,
      states: {
        "number.battery_target": state(metadata(), { state: "63.2" }),
        "number.unrelated": state(metadata(), { state: "99" }),
      },
    };
    await flush();
    expect(dashboard.entity("number", "target")?.displayValue).toBe("63,2 %");
    expect(connection.requests).toHaveLength(1);
    expect(dashboard.entity("number", "unrelated")).toBeNull();
    expect(hass.value.callService).not.toHaveBeenCalled();
  });

  it("uses registry names and IDs after renaming, without deriving IDs from keys", () => {
    const { dashboard, connection, hass } = setup();
    const renamed = metadata("number", {
      entity_id: "number.mein_eigener_name",
      name: "Mein Ladeziel",
    });
    hass.value = {
      ...hass.value!,
      states: { [renamed.entity_id]: state(renamed, { state: "70" }) },
    };
    connection.emit([renamed]);
    expect(dashboard.entity("number", "target")).toMatchObject({
      name: "Mein Ladeziel",
      displayValue: "70 %",
      metadata: { entity_id: "number.mein_eigener_name" },
    });
    connection.emit([]);
    expect(dashboard.entity("number", "target")).toBeNull();
  });

  it("distinguishes keys shared between domains and honors disabled/permission filtering", async () => {
    const number = metadata();
    const sensor = metadata("sensor", { can_control: false });
    const { dashboard, hass, connection } = setup([number, sensor]);
    expect(dashboard.entity("sensor", "target")?.canControl).toBe(false);
    expect(await dashboard.perform("sensor", "target", 42)).toBe(false);
    connection.emit([sensor]);
    expect(dashboard.entity("number", "target")).toBeNull();
    expect(await dashboard.perform("number", "target", 42)).toBe(false);
    expect(hass.value?.callService).not.toHaveBeenCalled();
  });

  it.each(["unknown", "unavailable"])(
    "never presents %s as zero or permits a write",
    async (value) => {
      const { dashboard, hass } = setup();
      hass.value = {
        ...hass.value!,
        states: {
          "number.battery_target": state(metadata(), { state: value }),
        },
      };
      const entity = dashboard.entity("number", "target")!;
      expect(entity.available).toBe(false);
      expect(entity.displayValue).toBe(
        value === "unknown" ? "Unbekannt" : "Nicht verfügbar",
      );
      expect(await dashboard.perform("number", "target", 42)).toBe(false);
      expect(hass.value.callService).not.toHaveBeenCalled();
    },
  );

  it("keeps missing state distinct from a missing registry entity and from zero", () => {
    const { dashboard, hass } = setup();
    hass.value = { ...hass.value!, states: {} };
    expect(dashboard.entity("number", "target")).toMatchObject({
      state: undefined,
      available: false,
      displayValue: "Nicht verfügbar",
    });
    hass.value = {
      ...hass.value,
      states: { "number.battery_target": state(metadata(), { state: "0" }) },
    };
    expect(dashboard.entity("number", "target")).toMatchObject({
      available: true,
      displayValue: "0 %",
    });
  });

  it("uses HA's formatter and dynamic names, falling back to localized units and state labels", () => {
    const item = metadata("sensor", {
      name: null,
      states: { waiting: "Wartet" },
    });
    const { dashboard, hass } = setup([item]);
    const formatter = vi.fn(() => "HA-formatiert");
    hass.value = { ...hass.value!, formatEntityState: formatter };
    expect(dashboard.entity("sensor", "target")).toMatchObject({
      name: "Batterie Zielwert",
      displayValue: "HA-formatiert",
    });
    expect(formatter).toHaveBeenCalledWith(hass.value.states[item.entity_id]);
    hass.value = {
      ...hass.value,
      formatEntityState: undefined,
      states: { [item.entity_id]: state(item, { state: "waiting" }) },
    };
    expect(dashboard.entity("sensor", "target")?.displayValue).toBe("Wartet");
    hass.value = {
      ...hass.value,
      locale: { number_format: "comma_decimal", language: "en-US" },
      states: { [item.entity_id]: state(item, { state: "1250.5" }) },
    };
    expect(dashboard.entity("sensor", "target")?.displayValue).toBe(
      "1,250.5 %",
    );
  });

  it("formats timestamps in the configured timezone when HA's formatter is not yet supplied", () => {
    const item = metadata("sensor");
    const { dashboard, hass } = setup([item]);
    hass.value = {
      ...hass.value!,
      language: "de",
      config: { time_zone: "Europe/Berlin" },
      states: {
        [item.entity_id]: state(item, {
          state: "2026-09-12T10:30:00+00:00",
          attributes: { device_class: "timestamp" },
        }),
      },
    };
    expect(dashboard.entity("sensor", "target")?.displayValue).toBe(
      "12.09.2026, 12:30",
    );
  });

  it.each([
    ["de", "Pacific/Honolulu", "2026-09-15", "15.09.2026"],
    ["en-US", "Pacific/Kiritimati", "2026-09-15", "Sep 15, 2026"],
    ["de", "Europe/Berlin", "2026-02-30", "2026-02-30"],
    ["de", "Europe/Berlin", "not-a-date", "not-a-date"],
  ])(
    "formats calendar dates without a timezone shift (%s, %s, %s)",
    (language, zone, value, expected) => {
      const item = metadata("sensor");
      const { dashboard, hass, connection } = setup([item]);
      hass.value = {
        ...hass.value!,
        language,
        config: { time_zone: zone },
        states: {
          [item.entity_id]: state(item, {
            state: value,
            attributes: { device_class: "date" },
          }),
        },
      };
      connection.emit([item]);
      expect(dashboard.entity("sensor", "target")?.displayValue).toBe(expected);
    },
  );

  it("waits for late HA/entry configuration without errors or writes", () => {
    const { dashboard, hass, entryId, connection } = setup();
    hass.value = undefined;
    expect(dashboard.error.value).toBeNull();
    expect(dashboard.ready.value).toBe(false);
    expect(dashboard.connected.value).toBe(false);
    hass.value = { language: "en", states: {} };
    expect(dashboard.error.value).toBeNull();
    entryId.value = undefined;
    hass.value = { ...hass.value, connection };
    expect(connection.requests).toHaveLength(1);
    entryId.value = "entry-2";
    expect(connection.requests).toHaveLength(2);
    expect(connection.requests[1]).toMatchObject({
      language: "en",
      entry_id: "entry-2",
    });
  });

  it("invalidates stale streams on entry/language/connection replacement and disposes listeners", async () => {
    const { dashboard, hass, entryId, connection, scope } = setup();
    await flush();
    entryId.value = "entry-2";
    connection.emit([metadata("number", { name: "Alter Name" })], 0);
    expect(dashboard.ready.value).toBe(false);
    expect(dashboard.entity("number", "target")).toBeNull();
    connection.emit([metadata("number", { name: "Neuer Name" })]);
    expect(dashboard.entity("number", "target")?.name).toBe("Neuer Name");
    expect(connection.subscriptions[0]?.unsubscribe).toHaveBeenCalledOnce();
    hass.value = { ...hass.value!, language: "en" };
    expect(connection.requests.at(-1)?.language).toBe("en");
    expect(dashboard.language.value).toBe("en");
    const replacement = new Connection();
    hass.value = { ...hass.value, connection: replacement };
    expect(
      [...connection.listeners.values()].every((set) => set.size === 0),
    ).toBe(true);
    connection.emit([metadata()]);
    expect(dashboard.ready.value).toBe(false);
    replacement.emit([metadata()]);
    await flush();
    scope.stop();
    expect(replacement.subscriptions[0]?.unsubscribe).toHaveBeenCalledOnce();
    expect(
      [...replacement.listeners.values()].every((set) => set.size === 0),
    ).toBe(true);
    expect(dashboard.ready.value).toBe(false);
  });

  it("cleans a subscription resolving after unmount and ignores late failures", async () => {
    const connection = new Connection();
    const pending = deferred<Unsubscribe>();
    connection.subscribe.mockReturnValueOnce(pending.promise);
    const { dashboard, scope } = setup([], connection);
    scope.stop();
    const unsubscribe = vi.fn(async () => {});
    pending.resolve(unsubscribe);
    await flush();
    expect(unsubscribe).toHaveBeenCalledOnce();
    expect(dashboard.ready.value).toBe(false);

    const nextConnection = new Connection();
    const nextPending = deferred<Unsubscribe>();
    nextConnection.subscribe.mockReturnValueOnce(nextPending.promise);
    const next = setup([], nextConnection);
    next.scope.stop();
    nextPending.reject(new Error("too late"));
    await flush();
    expect(next.dashboard.error.value).toBeNull();
  });

  it("reports subscription rejection and retries only after a connection-ready event", async () => {
    const connection = new Connection();
    connection.subscribe.mockRejectedValueOnce(new Error("denied"));
    const { dashboard, hass } = setup([], connection);
    await flush();
    expect(dashboard.ready.value).toBe(false);
    expect(dashboard.error.value).toContain("nicht geladen");
    hass.value = { ...hass.value!, states: {} };
    await flush();
    expect(connection.requests).toHaveLength(1);
    connection.fire("ready");
    connection.emit([metadata()]);
    expect(connection.requests).toHaveLength(2);
    expect(dashboard.error.value).toBeNull();
  });

  it("drops stale metadata when disconnected and resubscribes once on reconnection", async () => {
    const { dashboard, connection, hass } = setup();
    await flush();
    connection.fire("disconnected");
    expect(dashboard.connected.value).toBe(false);
    expect(dashboard.error.value).toContain("Keine Verbindung");
    expect(dashboard.entity("number", "target")).toBeNull();
    connection.emit([metadata()], 0);
    expect(dashboard.ready.value).toBe(false);
    connection.fire("reconnect-error");
    expect(connection.requests).toHaveLength(1);
    connection.fire("ready");
    expect(dashboard.connected.value).toBe(true);
    expect(dashboard.ready.value).toBe(false);
    connection.emit([metadata()]);
    expect(dashboard.ready.value).toBe(true);
    expect(connection.requests).toHaveLength(2);
    expect(hass.value?.callService).not.toHaveBeenCalled();
  });
});

describe("explicit HA service actions (REQ-VUE-ENTITY-BINDING)", () => {
  it.each([
    ["switch", true, "turn_on", {}],
    ["switch", false, "turn_off", {}],
    ["number", "42.1", "set_value", { value: 42.1 }],
    ["time", "06:45", "set_value", { time: "06:45:00" }],
    ["time", "23:59:59", "set_value", { time: "23:59:59" }],
    ["select", "automatic", "select_option", { option: "automatic" }],
  ] as const)(
    "calls %s.%s using the current registry ID",
    async (domain, value, service, data) => {
      const item = metadata(domain, { entity_id: `${domain}.renamed` });
      const { dashboard, hass } = setup([item]);
      hass.value = {
        ...hass.value!,
        states: {
          [item.entity_id]: state(item, {
            state: domain === "switch" ? "off" : "50",
            attributes: {
              min: 0,
              max: 100,
              step: 0.1,
              options: ["automatic", "off"],
            },
          }),
        },
      };
      expect(await dashboard.perform(domain, "target", value)).toBe(true);
      expect(hass.value.callService).toHaveBeenCalledExactlyOnceWith(
        domain,
        service,
        data,
        { entity_id: item.entity_id },
        false,
      );
      expect(dashboard.entity(domain, "target")?.state?.state).toBe(
        domain === "switch" ? "off" : "50",
      );
      expect(dashboard.entity(domain, "target")?.pending).toBe(false);
    },
  );

  it.each([
    "",
    " ",
    "NaN",
    "Infinity",
    Infinity,
    NaN,
    -1,
    100.1,
    42.05,
    true,
    null,
    {},
  ])(
    "rejects unsafe number input %s before any service call",
    async (value) => {
      const { dashboard, hass } = setup();
      expect(await dashboard.perform("number", "target", value)).toBe(false);
      expect(hass.value?.callService).not.toHaveBeenCalled();
      expect(dashboard.entity("number", "target")?.error).toContain(
        "gültigen Wert",
      );
    },
  );

  it.each([
    {},
    { min: 0, max: 100 },
    { min: 0, max: Infinity, step: 1 },
    { min: 0, max: 100, step: 0 },
    { min: 100, max: 0, step: 1 },
    { min: "0", max: 100, step: 1 },
  ])(
    "rejects missing or invalid HA numeric constraints %o",
    async (attributes) => {
      const { dashboard, hass } = setup();
      hass.value = {
        ...hass.value!,
        states: { "number.battery_target": state(metadata(), { attributes }) },
      };
      expect(await dashboard.perform("number", "target", 50)).toBe(false);
      expect(hass.value.callService).not.toHaveBeenCalled();
    },
  );

  it.each([
    ["switch", "on"],
    ["switch", 1],
    ["time", "24:00"],
    ["time", "01:60"],
    ["time", "12:00:60"],
    ["time", "2026-01-01T12:00:00"],
    ["time", "6:00"],
    ["select", "arbitrary"],
    ["select", null],
  ] as const)("rejects invalid %s action %s", async (domain, value) => {
    const { dashboard, hass } = setup([metadata(domain)]);
    expect(await dashboard.perform(domain, "target", value)).toBe(false);
    expect(hass.value?.callService).not.toHaveBeenCalled();
  });

  it("shares a pending lock between consumers and exposes failures without automatic retries", async () => {
    const { dashboard, hass } = setup();
    const result = deferred<unknown>();
    const service = vi.fn(() => result.promise);
    hass.value = { ...hass.value!, callService: service };
    const first = dashboard.perform("number", "target", 42);
    expect(dashboard.entity("number", "target")?.pending).toBe(true);
    expect(await dashboard.perform("number", "target", 55)).toBe(false);
    expect(service).toHaveBeenCalledOnce();
    hass.value = {
      ...hass.value,
      states: { "number.battery_target": state(metadata(), { state: "42" }) },
    };
    expect(dashboard.entity("number", "target")?.pending).toBe(true);
    result.reject(new Error("service unavailable"));
    expect(await first).toBe(false);
    expect(dashboard.entity("number", "target")).toMatchObject({
      pending: false,
    });
    expect(dashboard.entity("number", "target")?.error).toContain(
      "fehlgeschlagen",
    );
    expect(service).toHaveBeenCalledOnce();
    service.mockResolvedValueOnce({});
    expect(await dashboard.perform("number", "target", 50)).toBe(true);
    expect(dashboard.entity("number", "target")?.error).toBeNull();
  });

  it.each(["entry", "reconnect"])(
    "preserves an in-flight entity lock through %s changes and ignores its stale outcome",
    async (change) => {
      const { dashboard, hass, connection, entryId } = setup();
      const result = deferred<unknown>();
      const service = vi.fn(() => result.promise);
      hass.value = { ...hass.value!, callService: service };
      const first = dashboard.perform("number", "target", 42);
      if (change === "entry") entryId.value = "entry-2";
      else {
        connection.fire("disconnected");
        connection.fire("ready");
      }
      connection.emit([metadata()]);
      expect(dashboard.entity("number", "target")?.pending).toBe(true);
      expect(await dashboard.perform("number", "target", 55)).toBe(false);
      expect(service).toHaveBeenCalledOnce();
      result.reject(new Error("old request failed"));
      expect(await first).toBe(false);
      expect(dashboard.entity("number", "target")).toMatchObject({
        pending: false,
        error: null,
      });
    },
  );

  it("preserves pending actions and translates their errors after a language change", async () => {
    const { dashboard, hass, connection } = setup();
    const result = deferred<unknown>();
    const service = vi.fn(() => result.promise);
    hass.value = { ...hass.value!, callService: service };
    const first = dashboard.perform("number", "target", 42);
    hass.value = { ...hass.value, language: "en" };
    connection.emit([metadata()]);
    expect(dashboard.entity("number", "target")?.pending).toBe(true);
    expect(await dashboard.perform("number", "target", 55)).toBe(false);
    result.reject(new Error("same request failed"));
    expect(await first).toBe(false);
    expect(dashboard.entity("number", "target")?.pending).toBe(false);
    expect(dashboard.entity("number", "target")?.error).toContain(
      "The change failed",
    );
    expect(service).toHaveBeenCalledOnce();
  });

  it("ignores outcomes for a renamed registry entity and never applies them to its replacement", async () => {
    const { dashboard, hass, connection } = setup();
    const result = deferred<unknown>();
    hass.value = { ...hass.value!, callService: vi.fn(() => result.promise) };
    const first = dashboard.perform("number", "target", 42);
    const renamed = metadata("number", { entity_id: "number.new_id" });
    hass.value = {
      ...hass.value,
      states: { [renamed.entity_id]: state(renamed) },
    };
    connection.emit([renamed]);
    expect(dashboard.entity("number", "target")?.pending).toBe(true);
    expect(await dashboard.perform("number", "target", 55)).toBe(false);
    expect(hass.value.callService).toHaveBeenCalledOnce();
    result.reject(new Error("old request failed"));
    expect(await first).toBe(false);
    expect(dashboard.entity("number", "target")).toMatchObject({
      pending: false,
      error: null,
    });
  });
});

describe("atomic HA time windows (REQ-VUE-ENTITY-BINDING)", () => {
  function windowMetadata(
    kind: "timed_charge" | "grid_serving" = "timed_charge",
  ) {
    return ["start", "end"].map((part) =>
      metadata("time", {
        entity_id: `time.renamed_${kind}_${part}`,
        key: `${kind}_${part}`,
        device_id: "registered-battery",
      }),
    );
  }

  it.each(["timed_charge", "grid_serving"] as const)(
    "submits both %s values to the registry device in one call without changing HA states",
    async (kind) => {
      const items = windowMetadata(kind);
      const { dashboard, hass } = setup(items);
      const before = hass.value!.states;
      expect(await dashboard.performTimeWindow(kind, "22:00:17", "06:30")).toBe(
        true,
      );
      expect(hass.value!.callService).toHaveBeenCalledExactlyOnceWith(
        "sax_power",
        `set_${kind}_window`,
        { device_id: "registered-battery", start: "22:00:17", end: "06:30:00" },
        undefined,
        false,
      );
      expect(hass.value!.states).toBe(before);
    },
  );

  it("preserves equal endpoints as the existing empty-window setting", async () => {
    const { dashboard, hass } = setup(windowMetadata());
    expect(
      await dashboard.performTimeWindow("timed_charge", "06:30", "06:30:00"),
    ).toBe(true);
    expect(hass.value!.callService).toHaveBeenCalledWith(
      "sax_power",
      "set_timed_charge_window",
      { device_id: "registered-battery", start: "06:30:00", end: "06:30:00" },
      undefined,
      false,
    );
  });

  it.each(["24:00", "6:00", "12:60", "12:00:60", "", "06:30\n"])(
    "rejects either invalid endpoint %j for both controls",
    async (value) => {
      const { dashboard, hass } = setup(windowMetadata());
      for (const [start, end] of [
        [value, "06:00"],
        ["22:00", value],
      ]) {
        expect(
          await dashboard.performTimeWindow("timed_charge", start!, end!),
        ).toBe(false);
        for (const part of ["start", "end"]) {
          expect(
            dashboard.entity("time", `timed_charge_${part}`)?.error,
          ).toContain("gültigen Wert");
        }
      }
      expect(hass.value!.callService).not.toHaveBeenCalled();
    },
  );

  it.each([
    "missing",
    "unavailable",
    "unknown",
    "permission",
    "device",
    "no-device",
    "old-backend",
  ])(
    "rejects the complete window when one endpoint has %s metadata/state",
    async (problem) => {
      const items = windowMetadata();
      if (problem === "permission") items[1]!.can_control = false;
      if (problem === "device") items[1]!.device_id = "other-device";
      if (problem === "no-device") items[1]!.device_id = null;
      if (problem === "old-backend")
        for (const item of items) delete item.device_id;
      const { dashboard, hass, connection } = setup(items);
      if (problem === "missing") connection.emit([items[0]!]);
      if (problem === "unavailable" || problem === "unknown") {
        hass.value = {
          ...hass.value!,
          states: {
            ...hass.value!.states,
            [items[1]!.entity_id]: state(items[1]!, { state: problem }),
          },
        };
      }
      expect(
        await dashboard.performTimeWindow("timed_charge", "22:00", "06:30"),
      ).toBe(false);
      expect(hass.value!.callService).not.toHaveBeenCalled();
      expect(dashboard.entity("time", "timed_charge_start")?.error).toContain(
        "nicht bedient",
      );
    },
  );

  it("locks both controls against complete and individual writes and exposes one shared failure", async () => {
    const { dashboard, hass } = setup(windowMetadata());
    const result = deferred<unknown>();
    const service = vi.fn(() => result.promise);
    hass.value = { ...hass.value!, callService: service };
    const first = dashboard.performTimeWindow("timed_charge", "22:00", "06:30");
    for (const part of ["start", "end"]) {
      expect(dashboard.entity("time", `timed_charge_${part}`)?.pending).toBe(
        true,
      );
      expect(
        await dashboard.perform("time", `timed_charge_${part}`, "01:00"),
      ).toBe(false);
    }
    expect(
      await dashboard.performTimeWindow("timed_charge", "21:00", "06:00"),
    ).toBe(false);
    expect(service).toHaveBeenCalledOnce();
    result.reject(new Error("overlap rejected"));
    expect(await first).toBe(false);
    for (const part of ["start", "end"]) {
      expect(dashboard.entity("time", `timed_charge_${part}`)?.pending).toBe(
        false,
      );
      expect(dashboard.entity("time", `timed_charge_${part}`)?.error).toContain(
        "fehlgeschlagen",
      );
    }
    service.mockResolvedValueOnce({});
    expect(
      await dashboard.performTimeWindow("timed_charge", "21:00", "06:00"),
    ).toBe(true);
    expect(dashboard.entity("time", "timed_charge_end")?.error).toBeNull();
  });

  it.each(["start", "end"])(
    "waits for an individual %s action before allowing the atomic write",
    async (part) => {
      const { dashboard, hass } = setup(windowMetadata());
      const result = deferred<unknown>();
      const service = vi.fn(() => result.promise);
      hass.value = { ...hass.value!, callService: service };
      const first = dashboard.perform("time", `timed_charge_${part}`, "01:00");
      expect(
        await dashboard.performTimeWindow("timed_charge", "21:00", "06:00"),
      ).toBe(false);
      expect(service).toHaveBeenCalledOnce();
      result.resolve({});
      expect(await first).toBe(true);
    },
  );

  it.each(["entry", "reconnect", "rename", "device"])(
    "ignores stale complete-window outcomes after %s changes while keeping both locks",
    async (change) => {
      const items = windowMetadata();
      const { dashboard, hass, connection, entryId } = setup(items);
      const result = deferred<unknown>();
      const service = vi.fn(() => result.promise);
      hass.value = { ...hass.value!, callService: service };
      const first = dashboard.performTimeWindow(
        "timed_charge",
        "22:00",
        "06:30",
      );
      if (change === "entry") entryId.value = "entry-2";
      if (change === "reconnect") {
        connection.fire("disconnected");
        connection.fire("ready");
      }
      const replacement = items.map((item) => ({ ...item }));
      if (change === "rename") replacement[1]!.entity_id = "time.new_end_name";
      if (change === "device")
        for (const item of replacement) item.device_id = "replacement-battery";
      hass.value = {
        ...hass.value!,
        states: Object.fromEntries(
          replacement.map((item) => [item.entity_id, state(item)]),
        ),
      };
      connection.emit(replacement);
      for (const part of ["start", "end"]) {
        expect(dashboard.entity("time", `timed_charge_${part}`)?.pending).toBe(
          true,
        );
      }
      expect(
        await dashboard.performTimeWindow("timed_charge", "21:00", "06:00"),
      ).toBe(false);
      result.reject(new Error("old call failed"));
      expect(await first).toBe(false);
      for (const part of ["start", "end"]) {
        expect(dashboard.entity("time", `timed_charge_${part}`)).toMatchObject({
          pending: false,
          error: null,
        });
      }
      expect(service).toHaveBeenCalledOnce();
    },
  );

  it("keeps the two independent windows operable concurrently", async () => {
    const { dashboard, hass } = setup([
      ...windowMetadata(),
      ...windowMetadata("grid_serving"),
    ]);
    const result = deferred<unknown>();
    const service = vi
      .fn()
      .mockReturnValueOnce(result.promise)
      .mockResolvedValueOnce({});
    hass.value = { ...hass.value!, callService: service };
    const first = dashboard.performTimeWindow("timed_charge", "22:00", "06:30");
    expect(
      await dashboard.performTimeWindow("grid_serving", "11:00", "15:00"),
    ).toBe(true);
    result.resolve({});
    expect(await first).toBe(true);
    expect(service).toHaveBeenCalledTimes(2);
  });

  it("does not confirm a successful old request after reconnecting", async () => {
    const items = windowMetadata();
    const { dashboard, hass, connection } = setup(items);
    const result = deferred<unknown>();
    hass.value = { ...hass.value!, callService: vi.fn(() => result.promise) };
    const first = dashboard.performTimeWindow("timed_charge", "22:00", "06:30");
    connection.fire("disconnected");
    connection.fire("ready");
    connection.emit(items);
    result.resolve({});
    expect(await first).toBe(false);
    expect(dashboard.entity("time", "timed_charge_start")).toMatchObject({
      pending: false,
      error: null,
    });
  });

  it("preserves both locks across language changes and localizes their shared error", async () => {
    const items = windowMetadata();
    const { dashboard, hass, connection } = setup(items);
    const result = deferred<unknown>();
    hass.value = { ...hass.value!, callService: vi.fn(() => result.promise) };
    const first = dashboard.performTimeWindow("timed_charge", "22:00", "06:30");
    hass.value = { ...hass.value!, language: "en" };
    connection.emit(items);
    expect(
      await dashboard.performTimeWindow("timed_charge", "21:00", "06:00"),
    ).toBe(false);
    result.reject(new Error("service rejected"));
    expect(await first).toBe(false);
    for (const part of ["start", "end"]) {
      expect(dashboard.entity("time", `timed_charge_${part}`)?.error).toContain(
        "The change failed",
      );
    }
  });
});
