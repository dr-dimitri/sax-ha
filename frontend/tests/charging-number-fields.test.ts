import { afterEach, describe, expect, it, vi } from "vitest";
import { computed, createApp, h, nextTick, provide, ref, type App } from "vue";
import ChargingNumberFields from "../src/components/ChargingNumberFields.vue";
import {
  SAX_DASHBOARD_KEY,
  type DashboardEntity,
  type SaxDashboard,
} from "../src/ha";

const apps: App[] = [];
type Field = { key: string; label: string };
const socFields: Field[] = [
  { key: "timed_charge_min_soc", label: "Ladestart (%)" },
  { key: "timed_charge_max_soc", label: "Netzladeziel (%)" },
  { key: "max_soc", label: "Max SOC (%)" },
];

async function flush(): Promise<void> {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}

function state(
  key: string,
  value: string,
  attributes: Record<string, unknown> = {},
): DashboardEntity {
  const entityId = `number.renamed_${key}`;
  return {
    metadata: {
      domain: "number",
      key,
      entity_id: entityId,
      device_id: "battery",
      name: key,
      states: {},
      can_control: true,
    },
    state: {
      entity_id: entityId,
      state: value,
      attributes: { min: 0, max: 100, step: 1, ...attributes },
    },
    available: true,
    canControl: true,
    displayValue: `${value} %`,
    name: key,
    pending: false,
    error: null,
  };
}

async function mount(
  options: { language?: "de" | "en"; fields?: Field[] } = {},
) {
  const language = ref(options.language ?? "de");
  const connected = ref(true);
  const ready = ref(true);
  const fields = ref(options.fields ?? socFields);
  const visible = ref(true);
  const entries = ref<Record<string, DashboardEntity>>({
    timed_charge_min_soc: state("timed_charge_min_soc", "20"),
    timed_charge_max_soc: state("timed_charge_max_soc", "80", { max: 90 }),
    max_soc: state("max_soc", "90"),
    price_charge_max_price: state("price_charge_max_price", "-5", {
      min: -100,
      max: 200,
      step: 0.1,
    }),
    price_charge_hours: state("price_charge_hours", "4", {
      max: 24,
      step: 0.5,
    }),
    price_charge_neutral_price: state("price_charge_neutral_price", "30", {
      min: -100,
      max: 200,
      step: 0.1,
    }),
  });
  const perform = vi
    .fn<(values: Record<string, string>) => Promise<boolean>>()
    .mockResolvedValue(true);
  const clearControlError = vi.fn((_domain: string, key: string) => {
    const item = entries.value[key];
    if (item && !item.pending) item.error = null;
  });
  const dashboard = {
    language: computed(() => language.value),
    connected,
    ready,
    entity: (_domain: string, key: string) => entries.value[key] ?? null,
    performChargingSettings: perform,
    clearControlError,
  } as unknown as SaxDashboard;
  const apply = vi.fn();
  const api = ref<InstanceType<typeof ChargingNumberFields>>();
  const root = document.createElement("div");
  document.body.append(root);
  const app = createApp({
    setup() {
      provide(SAX_DASHBOARD_KEY, dashboard);
      return () =>
        h("div", { style: { display: visible.value ? undefined : "none" } }, [
          h(ChargingNumberFields, {
            ref: api,
            fields: fields.value,
            onApply: apply,
          }),
        ]);
    },
  });
  apps.push(app);
  app.mount(root);
  await flush();
  const form = (key: string) =>
    [...root.querySelectorAll<HTMLFormElement>("form")].find(
      (item) =>
        item.querySelector("label")?.textContent ===
        fields.value.find((field) => field.key === key)?.label,
    )!;
  const input = (key: string) =>
    form(key).querySelector<HTMLInputElement>("input")!;
  return {
    root,
    clearControlError,
    entries,
    fields,
    visible,
    language,
    connected,
    ready,
    perform,
    apply,
    api,
    form,
    input,
    async edit(key: string, value: string) {
      input(key).value = value;
      input(key).dispatchEvent(new Event("input", { bubbles: true }));
      await flush();
    },
    async update(key: string, value: string) {
      const item = entries.value[key]!;
      item.state!.state = value;
      item.displayValue = `${value} %`;
      await flush();
    },
    async submit() {
      const result = await api.value!.submit();
      await flush();
      return result;
    },
  };
}

afterEach(() => {
  apps.splice(0).forEach((app) => app.unmount());
  document.body.replaceChildren();
});

describe("shared charging number drafts", () => {
  it("has no individual apply buttons and delegates Enter/form submission to its parent", async () => {
    const fixture = await mount();
    expect(fixture.root.querySelectorAll("button")).toHaveLength(0);
    await fixture.edit("timed_charge_max_soc", "85");
    fixture
      .form("timed_charge_max_soc")
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flush();
    expect(fixture.apply).toHaveBeenCalledOnce();
    expect(fixture.perform).not.toHaveBeenCalled();
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).toHaveBeenCalledExactlyOnceWith({
      timed_charge_max_soc: "85",
    });
  });

  it("submits a jointly raised start, target and global limit without using the old global ceiling", async () => {
    const fixture = await mount();
    await fixture.edit("timed_charge_min_soc", "85");
    await fixture.edit("timed_charge_max_soc", "95");
    await fixture.edit("max_soc", "100");
    expect(fixture.input("timed_charge_max_soc").max).toBe("100");
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).toHaveBeenCalledExactlyOnceWith({
      timed_charge_min_soc: "85",
      timed_charge_max_soc: "95",
      max_soc: "100",
    });
    expect(
      fixture
        .form("timed_charge_min_soc")
        .querySelector(".entity-control__value")?.textContent,
    ).toBe("20 %");
    expect(
      fixture
        .form("timed_charge_max_soc")
        .querySelector(".entity-control__value")?.textContent,
    ).toBe("80 %");
    await fixture.update("timed_charge_min_soc", "85");
    await fixture.update("timed_charge_max_soc", "95");
    await fixture.update("max_soc", "100");
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).toHaveBeenCalledTimes(1);
  });

  it("lowers only the global limit while retaining a higher saved target", async () => {
    const fixture = await mount();
    await fixture.edit("max_soc", "10");
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).toHaveBeenCalledExactlyOnceWith({ max_soc: "10" });
    expect(fixture.input("timed_charge_max_soc").value).toBe("80");
    expect(fixture.input("timed_charge_min_soc").value).toBe("20");
  });

  it("does not write unchanged or numerically equivalent values", async () => {
    const fixture = await mount();
    expect(await fixture.submit()).toBe(true);
    await fixture.edit("max_soc", "90.0");
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).not.toHaveBeenCalled();
  });

  it.each(["", "1e", "-1", "101", "20.5"])(
    "rejects invalid start %j before any batch and focuses precisely that field",
    async (value) => {
      const fixture = await mount();
      await fixture.edit("timed_charge_min_soc", value);
      await fixture.edit("max_soc", "100");
      const nativeValue = fixture.input("timed_charge_min_soc").value;
      expect(await fixture.submit()).toBe(false);
      expect(fixture.perform).not.toHaveBeenCalled();
      expect(document.activeElement).toBe(
        fixture.input("timed_charge_min_soc"),
      );
      expect(
        fixture.input("timed_charge_min_soc").getAttribute("aria-invalid"),
      ).toBe("true");
      expect(fixture.input("timed_charge_min_soc").value).toBe(nativeValue);
      expect(fixture.input("max_soc").value).toBe("100");
    },
  );

  it.each(["de", "en"] as const)(
    "retains and identifies an inconsistent complete SOC draft in %s",
    async (language) => {
      const fixture = await mount({ language });
      await fixture.edit("timed_charge_min_soc", "85");
      await fixture.edit("timed_charge_max_soc", "84");
      expect(await fixture.submit()).toBe(false);
      expect(fixture.perform).not.toHaveBeenCalled();
      expect(document.activeElement).toBe(
        fixture.input("timed_charge_max_soc"),
      );
      expect(
        fixture.input("timed_charge_min_soc").getAttribute("aria-invalid"),
      ).toBe("true");
      expect(
        fixture.input("timed_charge_max_soc").getAttribute("aria-invalid"),
      ).toBe("true");
      expect(
        fixture.form("timed_charge_max_soc").querySelector("[role=alert]")
          ?.textContent,
      ).toContain(language === "de" ? "Ladestart" : "start threshold");
      expect(fixture.input("timed_charge_min_soc").value).toBe("85");
      await fixture.edit("timed_charge_max_soc", "85");
      expect(await fixture.submit()).toBe(true);
      expect(fixture.perform).toHaveBeenCalledExactlyOnceWith({
        timed_charge_min_soc: "85",
        timed_charge_max_soc: "85",
      });
    },
  );

  it("marks the changed start for an order error and permits a start of zero", async () => {
    const fixture = await mount();
    await fixture.edit("timed_charge_min_soc", "81");
    expect(await fixture.submit()).toBe(false);
    expect(document.activeElement).toBe(fixture.input("timed_charge_min_soc"));
    await fixture.edit("timed_charge_min_soc", "0");
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).toHaveBeenCalledExactlyOnceWith({
      timed_charge_min_soc: "0",
    });
  });

  it("checks a changed target against the proposed global limit", async () => {
    const fixture = await mount();
    await fixture.edit("timed_charge_max_soc", "95");
    await fixture.edit("max_soc", "90");
    expect(await fixture.submit()).toBe(false);
    expect(document.activeElement).toBe(fixture.input("timed_charge_max_soc"));
    expect(fixture.perform).not.toHaveBeenCalled();
  });

  it("locks immediately, prevents duplicate batches, and retains drafts through collapse and delayed failure", async () => {
    const fixture = await mount();
    let resolve!: (saved: boolean) => void;
    fixture.perform.mockImplementationOnce(
      () =>
        new Promise<boolean>((done) => {
          resolve = done;
        }),
    );
    await fixture.edit("timed_charge_max_soc", "75");
    const save = fixture.api.value!.submit();
    expect(fixture.api.value!.pending).toBe(true);
    expect(await fixture.api.value!.submit()).toBe(false);
    await flush();
    expect(fixture.perform).toHaveBeenCalledOnce();
    expect(fixture.input("timed_charge_min_soc").disabled).toBe(true);
    expect(
      fixture.form("timed_charge_max_soc").querySelector("[role=status]")
        ?.textContent,
    ).toContain("Änderung wird");
    fixture
      .form("timed_charge_max_soc")
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    expect(fixture.apply).not.toHaveBeenCalled();
    fixture.visible.value = false;
    await fixture.update("max_soc", "100");
    resolve(false);
    expect(await save).toBe(false);
    fixture.visible.value = true;
    await flush();
    expect(fixture.api.value!.pending).toBe(false);
    expect(fixture.input("timed_charge_max_soc").value).toBe("75");
    expect(fixture.input("max_soc").value).toBe("100");
    expect(
      fixture
        .form("timed_charge_max_soc")
        .querySelector(".entity-control__value")?.textContent,
    ).toBe("80 %");
    expect(
      fixture.form("timed_charge_max_soc").querySelector("[role=alert]"),
    ).not.toBeNull();
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).toHaveBeenCalledTimes(2);
    expect(fixture.perform).toHaveBeenLastCalledWith({
      timed_charge_max_soc: "75",
    });
  });

  it("clears a failed action when the user restores the confirmed value and applies without a write", async () => {
    const fixture = await mount();
    await fixture.edit("timed_charge_max_soc", "75");
    fixture.perform.mockImplementationOnce(async () => {
      fixture.entries.value.timed_charge_max_soc!.error =
        "Die Änderung ist fehlgeschlagen.";
      return false;
    });
    expect(await fixture.submit()).toBe(false);
    expect(
      fixture.form("timed_charge_max_soc").querySelector("[role=alert]"),
    ).not.toBeNull();
    await fixture.edit("timed_charge_max_soc", "80");
    expect(fixture.clearControlError).toHaveBeenLastCalledWith(
      "number",
      "timed_charge_max_soc",
    );
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).toHaveBeenCalledTimes(1);
    expect(
      fixture.form("timed_charge_max_soc").querySelector("[role=alert]"),
    ).toBeNull();
    expect(
      fixture
        .form("timed_charge_max_soc")
        .querySelector(".entity-control__value")?.textContent,
    ).toBe("80 %");
    expect(fixture.input("timed_charge_max_soc").value).toBe("80");
  });

  it("clears paired local validation errors after restoring visible confirmed values without a final input event", async () => {
    const fixture = await mount();
    await fixture.edit("timed_charge_min_soc", "85");
    await fixture.edit("timed_charge_max_soc", "84");
    expect(await fixture.submit()).toBe(false);
    expect(fixture.root.querySelectorAll("[role=alert]")).toHaveLength(2);
    fixture.input("timed_charge_min_soc").value = "20";
    fixture.input("timed_charge_max_soc").value = "80";
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).not.toHaveBeenCalled();
    expect(fixture.root.querySelectorAll("[role=alert]")).toHaveLength(0);
  });

  it("preserves an edited draft while confirmed values and pristine fields follow HA", async () => {
    const fixture = await mount();
    await fixture.edit("timed_charge_max_soc", "75");
    await fixture.update("timed_charge_max_soc", "85");
    await fixture.update("timed_charge_min_soc", "25");
    fixture.language.value = "en";
    await flush();
    expect(fixture.input("timed_charge_max_soc").value).toBe("75");
    expect(
      fixture
        .form("timed_charge_max_soc")
        .querySelector(".entity-control__value")?.textContent,
    ).toBe("85 %");
    expect(fixture.input("timed_charge_min_soc").value).toBe("25");
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).toHaveBeenCalledExactlyOnceWith({
      timed_charge_max_soc: "75",
    });
  });

  it("does not rewrite the native number input while typing or receiving unrelated updates", async () => {
    const fixture = await mount();
    const input = fixture.input("timed_charge_max_soc");
    const descriptor = Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )!;
    const rewritten = vi.fn();
    Object.defineProperty(input, "value", {
      get: () => descriptor.get!.call(input) as string,
      set: (value: string) => {
        rewritten(value);
        descriptor.set!.call(input, value);
      },
      configurable: true,
    });
    input.value = "";
    rewritten.mockClear();
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await flush();
    await fixture.update("max_soc", "100");
    fixture.language.value = "en";
    await flush();
    expect(rewritten).not.toHaveBeenCalled();
    expect(input.value).toBe("");
  });

  it("reads the visible native values when a final input event has not arrived", async () => {
    const fixture = await mount();
    fixture.input("timed_charge_max_soc").value = "75";
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).toHaveBeenCalledExactlyOnceWith({
      timed_charge_max_soc: "75",
    });
  });

  it("focuses the changed target when a concurrent backend order guard rejects the entire batch", async () => {
    const fixture = await mount();
    await fixture.edit("timed_charge_min_soc", "25");
    await fixture.edit("timed_charge_max_soc", "85");
    fixture.perform.mockImplementationOnce(async () => {
      for (const key of ["timed_charge_min_soc", "timed_charge_max_soc"])
        fixture.entries.value[key]!.error =
          "Das Netzladeziel muss mindestens so hoch wie der Ladestart sein.";
      return false;
    });
    expect(await fixture.submit()).toBe(false);
    expect(document.activeElement).toBe(fixture.input("timed_charge_max_soc"));
    expect(
      fixture.input("timed_charge_min_soc").getAttribute("aria-invalid"),
    ).toBe("true");
    expect(
      fixture.input("timed_charge_max_soc").getAttribute("aria-invalid"),
    ).toBe("true");
    expect(fixture.input("timed_charge_min_soc").value).toBe("25");
    expect(fixture.input("timed_charge_max_soc").value).toBe("85");
  });

  it("resets only the draft whose entity identity has changed and rejects stale completion", async () => {
    const fixture = await mount();
    let resolve!: (saved: boolean) => void;
    fixture.perform.mockImplementationOnce(
      () =>
        new Promise<boolean>((done) => {
          resolve = done;
        }),
    );
    await fixture.edit("timed_charge_max_soc", "75");
    await fixture.edit("max_soc", "95");
    const save = fixture.api.value!.submit();
    fixture.entries.value.timed_charge_max_soc = state(
      "timed_charge_max_soc",
      "70",
    );
    fixture.entries.value.timed_charge_max_soc.metadata.entity_id =
      "number.new_target";
    await flush();
    resolve(true);
    expect(await save).toBe(false);
    await flush();
    expect(fixture.input("timed_charge_max_soc").value).toBe("70");
    expect(fixture.input("max_soc").value).toBe("95");
  });

  it("preserves unsent input when metadata temporarily disappears", async () => {
    const fixture = await mount();
    await fixture.edit("timed_charge_max_soc", "75");
    const previous = fixture.entries.value.timed_charge_max_soc!;
    delete fixture.entries.value.timed_charge_max_soc;
    await flush();
    fixture.entries.value.timed_charge_max_soc = previous;
    await flush();
    expect(fixture.input("timed_charge_max_soc").value).toBe("75");
  });

  it("validates every visible field and submits dynamic fractions in one batch", async () => {
    const fixture = await mount({
      fields: [
        { key: "max_soc", label: "Netzladeziel (%)" },
        { key: "price_charge_max_price", label: "Ladepreis" },
        { key: "price_charge_neutral_price", label: "Schonpreis" },
      ],
    });
    await fixture.edit("max_soc", "95");
    await fixture.edit("price_charge_max_price", "-12.5");
    await fixture.edit("price_charge_neutral_price", "12.5");
    expect(await fixture.submit()).toBe(true);
    expect(fixture.perform).toHaveBeenCalledExactlyOnceWith({
      max_soc: "95",
      price_charge_max_price: "-12.5",
      price_charge_neutral_price: "12.5",
    });
  });

  it.each(["missing", "readonly", "invalid constraints"])(
    "does not send any changed setting when its changed field is %s",
    async (cause) => {
      const fixture = await mount();
      await fixture.edit("timed_charge_min_soc", "25");
      await fixture.edit("max_soc", "100");
      if (cause === "missing")
        delete fixture.entries.value.timed_charge_min_soc;
      else if (cause === "readonly")
        fixture.entries.value.timed_charge_min_soc!.canControl = false;
      else
        fixture.entries.value.timed_charge_min_soc!.state!.attributes = {
          min: 0,
          max: 100,
          step: 0,
        };
      await flush();
      expect(await fixture.submit()).toBe(false);
      expect(fixture.perform).not.toHaveBeenCalled();
      expect(
        fixture.input("timed_charge_min_soc").getAttribute("aria-invalid"),
      ).toBe("true");
      expect(fixture.input("max_soc").value).toBe("100");
    },
  );

  it.each(["missing", "readonly"])(
    "allows an independent changed field while a pristine field is %s",
    async (cause) => {
      const fixture = await mount();
      await fixture.edit("max_soc", "100");
      if (cause === "missing")
        delete fixture.entries.value.timed_charge_min_soc;
      else fixture.entries.value.timed_charge_min_soc!.canControl = false;
      await flush();
      expect(await fixture.submit()).toBe(true);
      expect(fixture.perform).toHaveBeenCalledExactlyOnceWith({
        max_soc: "100",
      });
    },
  );
});
