import { afterEach, describe, expect, it, vi } from "vitest";
import {
  computed,
  createApp,
  h,
  nextTick,
  provide,
  ref,
  shallowRef,
  type App,
} from "vue";
import TimeWindowControl from "../src/components/TimeWindowControl.vue";
import {
  SAX_DASHBOARD_KEY,
  type DashboardEntity,
  type SaxDashboard,
} from "../src/ha";

const applications: App[] = [];
type Kind = "timed_charge" | "grid_serving";
type Boundary = "start" | "end";

async function flush(): Promise<void> {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}

function deferred() {
  let resolve!: (value: boolean) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<boolean>((done, fail) => {
    resolve = done;
    reject = fail;
  });
  return { promise, resolve, reject };
}

async function mount(
  options: {
    start?: string;
    end?: string;
    language?: "de" | "en";
    kind?: Kind;
    readOnly?: Boundary;
    missing?: Boundary | "both";
  } = {},
) {
  const kind = ref<Kind>(options.kind ?? "timed_charge");
  const connected = ref(true);
  const pending = ref(false);
  const error = ref<string | null>(null);
  function makeEntity(boundary: Boundary, state: string): DashboardEntity {
    const entityId = `time.original_${boundary}`;
    return {
      metadata: {
        entity_id: entityId,
        device_id: "device-1",
        domain: "time",
        key: `${kind.value}_${boundary}`,
        name: boundary,
        states: {},
        can_control: options.readOnly !== boundary,
      },
      state: { entity_id: entityId, state, attributes: {} },
      available: !["unknown", "unavailable"].includes(state),
      name: boundary,
      displayValue: state,
      canControl: options.readOnly !== boundary,
      pending: false,
      error: null,
    };
  }
  const source = shallowRef<Record<Boundary, DashboardEntity | null>>({
    start:
      options.missing === "start" || options.missing === "both"
        ? null
        : makeEntity("start", options.start ?? "22:00:00"),
    end:
      options.missing === "end" || options.missing === "both"
        ? null
        : makeEntity("end", options.end ?? "06:00:00"),
  });
  const service = vi
    .fn<(kind: Kind, start: string, end: string) => Promise<boolean>>()
    .mockResolvedValue(true);
  const dashboard: SaxDashboard = {
    language: computed(() => options.language ?? "de"),
    ready: ref(true),
    connected,
    error: computed(() => null),
    entity(domain, key) {
      if (domain !== "time") return null;
      const boundary =
        key === `${kind.value}_start`
          ? "start"
          : key === `${kind.value}_end`
            ? "end"
            : null;
      const item = boundary && source.value[boundary];
      return item
        ? {
            ...item,
            available: item.available && connected.value,
            pending: pending.value,
            error: error.value,
          }
        : null;
    },
    perform: vi.fn().mockResolvedValue(false),
    async performTimeWindow(requestKind, start, end) {
      pending.value = true;
      error.value = null;
      try {
        return await service(requestKind, start, end);
      } catch {
        error.value = "Die Änderung ist fehlgeschlagen.";
        return false;
      } finally {
        pending.value = false;
      }
    },
  };
  const root = document.createElement("div");
  document.body.append(root);
  const app = createApp({
    setup() {
      provide(SAX_DASHBOARD_KEY, dashboard);
      return () => h(TimeWindowControl, { kind: kind.value });
    },
  });
  applications.push(app);
  app.mount(root);
  await flush();
  return {
    root,
    service,
    source,
    pending,
    connected,
    kind,
    async update(start: string, end: string) {
      source.value = {
        start: {
          ...source.value.start!,
          state: { ...source.value.start!.state!, state: start },
          available: !["unknown", "unavailable"].includes(start),
        },
        end: {
          ...source.value.end!,
          state: { ...source.value.end!.state!, state: end },
          available: !["unknown", "unavailable"].includes(end),
        },
      };
      await flush();
    },
  };
}

function inputs(root: HTMLElement): HTMLInputElement[] {
  return [...root.querySelectorAll<HTMLInputElement>('input[type="time"]')];
}
function markers(root: HTMLElement): HTMLButtonElement[] {
  return [...root.querySelectorAll<HTMLButtonElement>('[role="slider"]')];
}
function apply(root: HTMLElement): HTMLButtonElement {
  return root.querySelector('button[type="submit"]')!;
}
function confirmed(root: HTMLElement): string {
  return root.querySelector(".time-window-control__confirmed")!.textContent!;
}
function segments(root: HTMLElement): HTMLElement[] {
  return [
    ...root.querySelectorAll<HTMLElement>(".time-window-control__segment"),
  ];
}
function enter(root: HTMLElement, boundary: Boundary, value: string): void {
  const input = inputs(root)[boundary === "start" ? 0 : 1];
  input.value = value;
  input.dispatchEvent(new Event("input", { bubbles: true }));
}
function submit(root: HTMLElement): void {
  root
    .querySelector("form")!
    .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
}
function press(marker: HTMLElement, key: string): void {
  marker.dispatchEvent(
    new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }),
  );
}
function pointer(
  marker: HTMLElement,
  type: string,
  clientX: number,
  pointerId = 1,
): void {
  const event = new MouseEvent(type, {
    clientX,
    button: 0,
    bubbles: true,
    cancelable: true,
  });
  Object.defineProperties(event, {
    pointerId: { value: pointerId },
    isPrimary: { value: true },
  });
  marker.dispatchEvent(event);
}

afterEach(() => {
  for (const app of applications.splice(0)) app.unmount();
  document.body.replaceChildren();
  vi.restoreAllMocks();
});

describe("paired time window control", () => {
  it("shows the confirmed pair, seconds-capable fields and an overnight draft on two rail segments", async () => {
    const { root, service } = await mount();
    expect(inputs(root).map((input) => [input.value, input.step])).toEqual([
      ["22:00:00", "1"],
      ["06:00:00", "1"],
    ]);
    expect(
      [...root.querySelectorAll("label")].map((label) => label.htmlFor),
    ).toEqual(inputs(root).map((input) => input.id));
    expect(confirmed(root)).toBe("Bestätigt: 22:00 – 06:00 Uhr");
    expect(root.textContent).toContain("8 Std. · Ende am Folgetag");
    expect(segments(root)).toHaveLength(2);
    expect(segments(root)[0].style.left).toBe("91.66666666666667%");
    expect(segments(root)[1].style.width).toBe("25%");
    expect(
      markers(root).map((marker) => marker.getAttribute("aria-label")),
    ).toEqual(["Startmarke", "Endmarke"]);
    expect(markers(root)[0].getAttribute("aria-valuetext")).toBe("22:00 Uhr");
    expect(apply(root).disabled).toBe(true);
    expect(service).not.toHaveBeenCalled();
  });

  it.each<Kind>(["timed_charge", "grid_serving"])(
    "submits %s once as a pair, preserves seconds and awaits actual HA confirmation",
    async (kind) => {
      const { root, service, update } = await mount({
        kind,
        start: "01:00:17",
        end: "05:30:49",
      });
      enter(root, "start", "02:15:33");
      await flush();
      expect(service).not.toHaveBeenCalled();
      expect(root.textContent).toContain("Entwurf:");
      expect(confirmed(root)).toContain("01:00:17 – 05:30:49 Uhr");
      submit(root);
      await flush();
      expect(service).toHaveBeenCalledExactlyOnceWith(
        kind,
        "02:15:33",
        "05:30:49",
      );
      expect(confirmed(root)).toContain("01:00:17 – 05:30:49 Uhr");
      expect(root.textContent).toContain(
        "Bestätigung durch Home Assistant ausstehend",
      );
      await update("02:15:33", "05:30:49");
      expect(confirmed(root)).toContain("02:15:33 – 05:30:49 Uhr");
      expect(apply(root).disabled).toBe(true);
      expect(root.textContent).not.toContain("ausstehend");
    },
  );

  it("keeps equal boundaries as an empty, valid interval rather than a full day", async () => {
    const { root, service } = await mount();
    enter(root, "end", "22:00");
    await flush();
    expect(root.textContent).toContain("Leeres Zeitfenster");
    expect(segments(root)).toHaveLength(0);
    expect(markers(root)[0].style.left).toBe(markers(root)[1].style.left);
    expect(markers(root).every((marker) => !marker.disabled)).toBe(true);
    submit(root);
    await flush();
    expect(service).toHaveBeenCalledExactlyOnceWith(
      "timed_charge",
      "22:00:00",
      "22:00",
    );
  });

  it("adjusts independent markers with the keyboard without writing and exposes their full range", async () => {
    const { root, service } = await mount({
      start: "08:00:19",
      end: "10:00:37",
    });
    const [start, end] = markers(root);
    press(start, "ArrowRight");
    await flush();
    expect(inputs(root).map((input) => input.value)).toEqual([
      "08:01:00",
      "10:00:37",
    ]);
    press(end, "PageDown");
    await flush();
    expect(inputs(root)[1].value).toBe("09:45:00");
    press(start, "Home");
    press(end, "End");
    await flush();
    expect(inputs(root).map((input) => input.value)).toEqual([
      "00:00:00",
      "23:59:59",
    ]);
    expect(end.getAttribute("aria-valuenow")).toBe(
      end.getAttribute("aria-valuemax"),
    );
    press(start, "ArrowLeft");
    press(end, "ArrowRight");
    await flush();
    expect(inputs(root).map((input) => input.value)).toEqual([
      "00:00:00",
      "23:59:59",
    ]);
    expect(service).not.toHaveBeenCalled();
  });

  it("drags captured pointers in minute steps across midnight and leaves the other boundary exact", async () => {
    const { root, service } = await mount({
      start: "10:00:19",
      end: "12:00:37",
    });
    const rail = root.querySelector<HTMLElement>(".time-window-control__rail")!;
    vi.spyOn(rail, "getBoundingClientRect").mockReturnValue({
      left: 100,
      width: 1440,
    } as DOMRect);
    const start = markers(root)[0];
    const capture = vi.fn();
    Object.assign(start, {
      setPointerCapture: capture,
      hasPointerCapture: () => true,
      releasePointerCapture: vi.fn(),
    });
    pointer(start, "pointerdown", 700);
    pointer(start, "pointermove", 1420, 9);
    await flush();
    expect(inputs(root)[0].value).toBe("10:00:19");
    pointer(start, "pointermove", 1420);
    pointer(start, "pointerup", 1420);
    await flush();
    expect(capture).toHaveBeenCalledWith(1);
    expect(inputs(root).map((input) => input.value)).toEqual([
      "22:00:00",
      "12:00:37",
    ]);
    expect(segments(root)).toHaveLength(2);
    expect(service).not.toHaveBeenCalled();
  });

  it("does not round seconds or shift a marker when it is only clicked", async () => {
    const { root, service } = await mount({ start: "10:00:19" });
    const rail = root.querySelector<HTMLElement>(".time-window-control__rail")!;
    vi.spyOn(rail, "getBoundingClientRect").mockReturnValue({
      left: 100,
      width: 1440,
    } as DOMRect);
    pointer(markers(root)[0], "pointerdown", 710);
    pointer(markers(root)[0], "pointerup", 710);
    await flush();
    expect(inputs(root)[0].value).toBe("10:00:19");
    expect(apply(root).disabled).toBe(true);
    expect(service).not.toHaveBeenCalled();
  });

  it("keeps the grab offset when a drag starts at the edge of the larger touch target", async () => {
    const { root } = await mount({ start: "10:00:00" });
    const rail = root.querySelector<HTMLElement>(".time-window-control__rail")!;
    vi.spyOn(rail, "getBoundingClientRect").mockReturnValue({
      left: 100,
      width: 1440,
    } as DOMRect);
    const marker = markers(root)[0];
    pointer(marker, "pointerdown", 720);
    pointer(marker, "pointermove", 721);
    pointer(marker, "pointerup", 721);
    await flush();
    expect(inputs(root)[0].value).toBe("10:01:00");
  });

  it("blocks duplicate submission and both fields and markers while the shared action is pending", async () => {
    const { root, service } = await mount();
    const action = deferred();
    service.mockReturnValueOnce(action.promise);
    enter(root, "start", "21:00");
    submit(root);
    submit(root);
    await flush();
    expect(service).toHaveBeenCalledOnce();
    expect(
      [...inputs(root), ...markers(root), apply(root)].every(
        (element) => element.disabled,
      ),
    ).toBe(true);
    expect(root.querySelector("form")!.getAttribute("aria-busy")).toBe("true");
    expect(root.textContent).toContain(
      "Änderung wird an Home Assistant gesendet",
    );
    action.reject(new Error("private backend details"));
    await flush();
    expect(root.querySelector('[role="alert"]')!.textContent).toContain(
      "fehlgeschlagen",
    );
    expect(root.textContent).not.toContain("private");
    expect(inputs(root)[0].value).toBe("21:00");
    expect(confirmed(root)).toContain("22:00 – 06:00 Uhr");
    expect(apply(root).disabled).toBe(false);
  });

  it.each<Boundary>(["start", "end"])(
    "disables the whole pair when %s is read-only",
    async (readOnly) => {
      const { root, service } = await mount({ readOnly });
      expect(
        [...inputs(root), ...markers(root), apply(root)].every(
          (element) => element.disabled,
        ),
      ).toBe(true);
      expect(root.textContent).toContain("Keine Berechtigung");
      press(markers(root)[0], "ArrowRight");
      submit(root);
      await flush();
      expect(service).not.toHaveBeenCalled();
    },
  );

  it.each<Boundary>(["start", "end"])(
    "does not offer a partial pair when %s is missing",
    async (missing) => {
      const { root, service } = await mount({ missing });
      expect(
        inputs(root).every((input) => input.disabled && input.value === ""),
      ).toBe(true);
      expect(confirmed(root)).toBe(
        missing === "start"
          ? "Bestätigt: Nicht verfügbar – 06:00 Uhr"
          : "Bestätigt: 22:00 Uhr – Nicht verfügbar",
      );
      expect(root.textContent).toContain("Zeitfenster nicht verfügbar");
      submit(root);
      await flush();
      expect(service).not.toHaveBeenCalled();
    },
  );

  it("hides an entirely missing pair", async () => {
    const { root } = await mount({ missing: "both" });
    expect(root.querySelector("form")).toBeNull();
  });

  it.each([undefined, null, "another-device"])(
    "requires matching device metadata before enabling paired writes (%s)",
    async (deviceId) => {
      const { root, source, service } = await mount();
      source.value = {
        ...source.value,
        end: {
          ...source.value.end!,
          metadata: { ...source.value.end!.metadata, device_id: deviceId },
        },
      };
      await flush();
      expect(inputs(root).every((input) => input.disabled)).toBe(true);
      expect(markers(root).every((marker) => marker.disabled)).toBe(true);
      expect(root.textContent).toContain("nicht gemeinsam geändert");
      expect(confirmed(root)).toContain("22:00 – 06:00 Uhr");
      submit(root);
      await flush();
      expect(service).not.toHaveBeenCalled();
    },
  );

  it("keeps translated entity labels while giving the slider markers short names", async () => {
    const { root, source } = await mount();
    source.value = {
      ...source.value,
      start: { ...source.value.start!, name: "Beginn der Ladepause" },
    };
    await flush();
    expect(root.querySelector("label")!.textContent).toContain(
      "Beginn der Ladepause (Uhr)",
    );
    expect(markers(root)[0].textContent).toBe("Start");
  });

  it("rejects an incomplete input while preserving the confirmed values", async () => {
    const { root, service } = await mount();
    enter(root, "start", "");
    await flush();
    expect(apply(root).disabled).toBe(true);
    expect(markers(root).every((marker) => marker.disabled)).toBe(true);
    expect(segments(root)).toHaveLength(0);
    submit(root);
    await flush();
    expect(service).not.toHaveBeenCalled();
    expect(confirmed(root)).toContain("22:00 – 06:00 Uhr");
  });

  it("preserves drafts across unrelated updates but discards the entire draft when one HA boundary changes", async () => {
    const { root, source, update, service } = await mount();
    enter(root, "start", "21:00");
    source.value = {
      ...source.value,
      start: { ...source.value.start!, name: "Renamed display label" },
    };
    await flush();
    expect(inputs(root)[0].value).toBe("21:00");
    await update("22:00:00", "07:00:00");
    expect(inputs(root).map((input) => input.value)).toEqual([
      "22:00:00",
      "07:00:00",
    ]);
    expect(root.textContent).toContain("Der Entwurf wurde verworfen");
    submit(root);
    await flush();
    expect(service).not.toHaveBeenCalled();
  });

  it("does not claim that a nonexistent draft was discarded on an ordinary HA update", async () => {
    const { root, update } = await mount();
    await update("21:00:00", "06:00:00");
    expect(confirmed(root)).toContain("21:00 – 06:00 Uhr");
    expect(root.textContent).not.toContain("verworfen");
  });

  it.each(["unknown", "unavailable"])(
    "discards a draft when a boundary becomes %s and does not restore it on recovery",
    async (state) => {
      const { root, update, service } = await mount();
      enter(root, "start", "21:00");
      await update(state, "06:00:00");
      expect(
        inputs(root).every((input) => input.disabled && input.value === ""),
      ).toBe(true);
      expect(segments(root)).toHaveLength(0);
      await update("22:00:00", "06:00:00");
      expect(inputs(root)[0].value).toBe("22:00:00");
      expect(apply(root).disabled).toBe(true);
      expect(service).not.toHaveBeenCalled();
    },
  );

  it("does not carry a draft or an old service acknowledgement to replacement entities", async () => {
    const { root, source, service } = await mount();
    const action = deferred();
    service.mockReturnValueOnce(action.promise);
    enter(root, "start", "21:00");
    submit(root);
    await flush();
    source.value = Object.fromEntries(
      Object.entries(source.value).map(([boundary, entity]) => [
        boundary,
        {
          ...entity!,
          metadata: {
            ...entity!.metadata,
            entity_id: `time.replacement_${boundary}`,
          },
        },
      ]),
    ) as Record<Boundary, DashboardEntity>;
    await flush();
    expect(inputs(root)[0].value).toBe("22:00:00");
    action.resolve(true);
    await flush();
    expect(root.textContent).not.toContain("ausstehend");
    expect(apply(root).disabled).toBe(true);
  });

  it("discards the draft and releases a captured pointer when both entities move to another device", async () => {
    const { root, source, service } = await mount();
    enter(root, "start", "21:00");
    await flush();
    const marker = markers(root)[0];
    const release = vi.fn();
    Object.assign(marker, {
      setPointerCapture: vi.fn(),
      hasPointerCapture: () => true,
      releasePointerCapture: release,
    });
    const rail = root.querySelector<HTMLElement>(".time-window-control__rail")!;
    vi.spyOn(rail, "getBoundingClientRect").mockReturnValue({
      left: 100,
      width: 1440,
    } as DOMRect);
    pointer(marker, "pointerdown", 1360);
    source.value = Object.fromEntries(
      Object.entries(source.value).map(([boundary, entity]) => [
        boundary,
        {
          ...entity!,
          metadata: { ...entity!.metadata, device_id: "replacement-device" },
        },
      ]),
    ) as Record<Boundary, DashboardEntity>;
    await flush();
    expect(release).toHaveBeenCalledExactlyOnceWith(1);
    expect(inputs(root).map((input) => input.value)).toEqual([
      "22:00:00",
      "06:00:00",
    ]);
    pointer(marker, "pointermove", 1400);
    pointer(marker, "pointerup", 1400);
    await flush();
    expect(inputs(root)[0].value).toBe("22:00:00");
    expect(apply(root).disabled).toBe(true);
    submit(root);
    await flush();
    expect(service).not.toHaveBeenCalled();
  });

  it("cancels an active drag on disconnect and uses confirmed values after reconnect", async () => {
    const { root, connected, service } = await mount();
    const rail = root.querySelector<HTMLElement>(".time-window-control__rail")!;
    vi.spyOn(rail, "getBoundingClientRect").mockReturnValue({
      left: 100,
      width: 1440,
    } as DOMRect);
    const marker = markers(root)[0];
    pointer(marker, "pointerdown", 700);
    connected.value = false;
    await flush();
    pointer(marker, "pointermove", 800);
    expect(inputs(root)[0].value).toBe("");
    expect(root.textContent).toContain("Keine Verbindung");
    connected.value = true;
    await flush();
    expect(inputs(root)[0].value).toBe("22:00:00");
    expect(service).not.toHaveBeenCalled();
  });

  it("provides English labels and an empty window without German time units", async () => {
    const { root } = await mount({
      language: "en",
      start: "10:00:00",
      end: "10:00:00",
    });
    expect(confirmed(root)).toBe("Confirmed: 10:00 – 10:00");
    expect(apply(root).textContent).toBe("Apply");
    expect(root.textContent).toContain("Empty time window");
    expect(markers(root)[0].getAttribute("aria-label")).toBe("Start marker");
    expect(root.textContent).not.toContain("Uhr");
  });
});
