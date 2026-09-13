import { afterEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";
import { SaxPowerVuePanel } from "../src/panel";
import { tabPath, tabs } from "../src/tabs";
import type {
  DashboardMetadata,
  HassConnection,
  HomeAssistant,
  TariffProfile,
} from "../src/types";

type PanelElement = InstanceType<typeof SaxPowerVuePanel>;

const germanHass: HomeAssistant = {
  language: "de",
  states: {},
};

async function flush(): Promise<void> {
  await nextTick();
  await nextTick();
}

async function mount(
  options: {
    pathname?: string;
    routePath?: string;
    narrow?: boolean;
    hass?: HomeAssistant;
  } = {},
): Promise<PanelElement> {
  window.history.replaceState(
    null,
    "",
    options.pathname ?? "/sax-power-vue/allgemein",
  );
  const element = new SaxPowerVuePanel();
  element.hass = options.hass ?? germanHass;
  element.panel = {
    config: { entry_id: "entry-1" },
    url_path: "sax-power-vue",
  };
  element.narrow = options.narrow ?? false;
  if (options.routePath !== undefined) {
    element.route = { path: options.routePath, prefix: "/sax-power-vue" };
  }
  document.body.append(element);
  await flush();
  return element;
}

function shadow(element: PanelElement): ShadowRoot {
  return element.shadowRoot!;
}

function selectedLink(element: PanelElement): HTMLAnchorElement | null {
  return shadow(element).querySelector('nav a[aria-current="page"]');
}

async function mountTariffs(
  timed: string,
  dynamic: string,
  pathname = "/sax-power-vue/allgemein",
  canControl = true,
  language = "de",
) {
  let emit!: (message: DashboardMetadata) => void;
  const listeners = new Map<string, () => void>();
  const callService = vi.fn();
  const callWS = vi.fn().mockResolvedValue({
    tariff_type: "time_of_use",
    revision: "1",
    base_price_ct_kwh: 32,
    feed_in_price_ct_kwh: 8,
    windows: [],
    can_edit: canControl,
    can_configure: canControl,
  });
  const connection: HassConnection = {
    connected: true,
    subscribeMessage: vi.fn(async (callback) => {
      emit = callback;
      return () => {};
    }),
    addEventListener: vi.fn((event, callback) => {
      listeners.set(event, callback);
    }),
    removeEventListener: vi.fn(),
  };
  const metadata = ["timed_charge_enabled", "price_charge_enabled"].map(
    (key) => ({
      domain: "switch" as const,
      key,
      entity_id: `switch.renamed_${key}`,
      name: key,
      states: {},
      can_control: canControl,
    }),
  );
  const hass: HomeAssistant = {
    language,
    connection,
    states: {},
    callService,
    callWS,
  };
  const element = await mount({ hass, pathname });
  async function update(timed: string, dynamic: string) {
    element.hass = {
      ...hass,
      states: Object.fromEntries(
        metadata.map((item, index) => [
          item.entity_id,
          {
            entity_id: item.entity_id,
            state: index === 0 ? timed : dynamic,
            attributes: {},
          },
        ]),
      ),
    };
    await flush();
  }
  await update(timed, dynamic);
  emit({ entities: metadata });
  await flush();
  return { element, callService, callWS, update, emit, connection, listeners };
}

afterEach(async () => {
  document.body.replaceChildren();
  await flush();
  window.history.replaceState(null, "", "/sax-power-vue");
});

describe("dashboard paths", () => {
  it.each([
    ["/sax-power-vue", "allgemein"],
    ["/sax-power-vue/", "allgemein"],
    ["", "allgemein"],
    ["/", "allgemein"],
    ["/ersparnis", "ersparnis"],
    ["/sax-power-vue/ersparnis/?period=month#chart", "ersparnis"],
    ["/sax-power-vue/unbekannt", "unbekannt"],
    ["/sax-power-vue/ersparnis/unbekannt", "ersparnis/unbekannt"],
  ])("resolves %s to %s", (path, expected) => {
    expect(tabPath(path, "/sax-power-vue")).toBe(expected);
  });
});

describe("Home Assistant panel", () => {
  it.each(["de", "en"])(
    "opens both tariff tabs without writes or pending feedback in %s",
    async (language) => {
      const { element, callService } = await mountTariffs(
        "off",
        "off",
        "/sax-power-vue/allgemein",
        true,
        language,
      );
      const root = shadow(element);
      for (const path of ["ladeautomatik", "stromtarif", "ladeautomatik"]) {
        root
          .querySelector<HTMLAnchorElement>(`nav a[href$='/${path}']`)!
          .click();
        await flush();
        expect(selectedLink(element)?.getAttribute("href")).toBe(
          `/sax-power-vue/${path}`,
        );
        const control = root.querySelector<HTMLFormElement>(
          ".charging-view > .entity-control",
        )!;
        if (control) {
          expect(control.getAttribute("aria-busy")).toBe("false");
          expect(control.querySelector("input")!.disabled).toBe(false);
        }
        expect(root.textContent).not.toMatch(
          /Änderung wird an Home Assistant gesendet|Sending change to Home Assistant/,
        );
        expect(callService).not.toHaveBeenCalled();
      }
    },
  );

  it.each([
    ["off", "off"],
    ["on", "off"],
    ["off", "on"],
    ["on", "on"],
    ["on", "unknown"],
    ["unavailable", "on"],
  ])(
    "keeps electricity tariff and TOU fallback available independently of switch states (%s/%s)",
    async (timed, dynamic) => {
      const { element, callService } = await mountTariffs(timed, dynamic);
      expect(shadow(element).querySelectorAll("nav a")).toHaveLength(5);
      expect(
        shadow(element).querySelector('nav a[href$="/ladeautomatik"]'),
      ).not.toBeNull();
      expect(
        shadow(element).querySelector('nav a[href$="/stromtarif"]'),
      ).not.toBeNull();
      expect(
        shadow(element).querySelector('nav a[href$="/dynamisches-laden"]'),
      ).toBeNull();
      expect(callService).not.toHaveBeenCalled();
    },
  );
  it.each([
    ["on", "off"],
    ["off", "on"],
  ])(
    "redirects the legacy dynamic route without activating charging (%s/%s)",
    async (timed, dynamic) => {
      const { element, callService } = await mountTariffs(
        timed,
        dynamic,
        "/sax-power-vue/dynamisches-laden",
        false,
      );
      expect(window.location.pathname).toBe("/sax-power-vue/stromtarif");
      expect(selectedLink(element)?.getAttribute("href")).toBe(
        "/sax-power-vue/stromtarif",
      );
      expect(callService).not.toHaveBeenCalled();
    },
  );
  it("keeps the current route stable across activation, history and disconnect", async () => {
    const { element, callService, update, listeners } = await mountTariffs(
      "off",
      "off",
      "/sax-power-vue/ladeautomatik",
    );
    await update("off", "on");
    expect(window.location.pathname).toBe("/sax-power-vue/ladeautomatik");
    element.route = { path: "/dynamisches-laden", prefix: "/sax-power-vue" };
    await flush();
    expect(window.location.pathname).toBe("/sax-power-vue/stromtarif");
    window.history.pushState(null, "", "/sax-power-vue/ladeautomatik");
    window.dispatchEvent(new PopStateEvent("popstate"));
    await flush();
    expect(selectedLink(element)?.getAttribute("href")).toBe(
      "/sax-power-vue/ladeautomatik",
    );
    listeners.get("disconnected")?.();
    await flush();
    expect(shadow(element).querySelectorAll("nav a")).toHaveLength(5);
    expect(callService).not.toHaveBeenCalled();
  });

  it("shares one metadata subscription across navigation and HA state updates", async () => {
    const unsubscribe = vi.fn();
    const subscribeMessage = vi.fn().mockResolvedValue(unsubscribe);
    const callService = vi.fn();
    const connection: HassConnection = {
      connected: true,
      subscribeMessage,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    const hass = { ...germanHass, connection, callService };
    const element = await mount({ hass });
    expect(subscribeMessage).toHaveBeenCalledExactlyOnceWith(
      expect.any(Function),
      {
        type: "sax_power/dashboard/subscribe",
        entry_id: "entry-1",
        language: "de",
      },
      { resubscribe: false },
    );
    subscribeMessage.mock.calls[0][0]({ entities: [] });

    for (const tab of tabs) {
      shadow(element)
        .querySelector<HTMLAnchorElement>(
          `nav a[href="/sax-power-vue/${tab.path}"]`,
        )!
        .click();
      element.hass = { ...hass, states: {} };
      await flush();
    }
    expect(subscribeMessage).toHaveBeenCalledTimes(1);
    expect(callService).not.toHaveBeenCalled();

    element.remove();
    await flush();
    expect(unsubscribe).toHaveBeenCalledOnce();
    for (const event of ["ready", "disconnected", "reconnect-error"]) {
      expect(connection.removeEventListener).toHaveBeenCalledWith(
        event,
        expect.any(Function),
      );
    }
  });

  it("shows a localized metadata error and disposes the failed subscription", async () => {
    const connection: HassConnection = {
      connected: true,
      subscribeMessage: vi.fn().mockRejectedValue(new Error("denied")),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    const element = await mount({ hass: { ...germanHass, connection } });
    await flush();
    expect(shadow(element).querySelector('[role="alert"]')?.textContent).toBe(
      "Die SAX Power Entitäten konnten nicht geladen werden.",
    );
    expect(shadow(element).querySelectorAll("nav a")).toHaveLength(5);
    element.remove();
    await flush();
    expect(connection.removeEventListener).toHaveBeenCalledTimes(3);
  });

  it("mounts five stable sections and the general view with isolated styles", async () => {
    const element = await mount();
    const root = shadow(element);

    expect(customElements.get("sax-power-vue-panel")).toBe(SaxPowerVuePanel);
    expect(root.querySelectorAll("nav a")).toHaveLength(5);
    expect(
      [...root.querySelectorAll("nav a")].map((link) =>
        link.getAttribute("href"),
      ),
    ).toEqual([
      "/sax-power-vue/allgemein",
      "/sax-power-vue/stromtarif",
      "/sax-power-vue/ladeautomatik",
      "/sax-power-vue/netzdienliches-laden",
      "/sax-power-vue/ersparnis",
    ]);
    expect(
      [...root.querySelectorAll("nav a")].map((link) =>
        link.textContent?.trim(),
      ),
    ).toEqual([
      "Allgemeine Informationen",
      "Stromtarif",
      "Zeitvariabler Tarif",
      "Netzdienliches Laden",
      "Amortisation",
    ]);
    expect(selectedLink(element)?.textContent?.trim()).toBe(
      "Allgemeine Informationen",
    );
    expect(root.querySelector(".placeholder")).toBeNull();
    expect(root.querySelector('[role="status"]')).not.toBeNull();
    expect(
      [...root.querySelectorAll("style")]
        .map((style) => style.textContent)
        .join("\n"),
    ).toContain("--primary-background-color");
    expect(root.querySelector(".header")?.textContent?.trim()).toBe(
      "SAX Power",
    );
    expect(root.querySelector(".introduction")?.textContent).toBe(
      "Gerätewerte, Ladeeinstellungen und Ersparnis Ihres SAX-Power-Speichers.",
    );
    expect(element.children).toHaveLength(0);
  });

  it.each(tabs)("opens the $path deep link directly", async ({ path, de }) => {
    const element = await mount({ pathname: `/sax-power-vue/${path}` });

    expect(shadow(element).querySelector("h1")?.textContent?.trim()).toBe(de);
    expect(selectedLink(element)?.getAttribute("href")).toBe(
      `/sax-power-vue/${path}`,
    );
  });

  it("localizes the dashboard description and preserves the open view", async () => {
    const element = await mount({
      pathname: "/sax-power-vue/ersparnis",
      hass: { language: "de", states: {} },
    });

    expect(
      shadow(element).querySelector(".savings-view")?.textContent,
    ).toContain("Hinweise zur Berechnung und Datenbasis");

    element.hass = { language: "en", states: {} };
    await flush();
    expect(shadow(element).querySelector(".introduction")?.textContent).toBe(
      "Device values, charging settings and savings for your SAX Power battery.",
    );
    expect(shadow(element).querySelector("h1")?.textContent).toBe(
      "Amortization",
    );
  });

  it("uses Home Assistant route properties and reacts to route changes", async () => {
    const element = await mount({ routePath: "/ersparnis" });
    expect(shadow(element).querySelector("h1")?.textContent?.trim()).toBe(
      "Amortisation",
    );

    element.route = { path: "/dynamisches-laden", prefix: "/sax-power-vue" };
    await flush();

    expect(shadow(element).querySelector("h1")?.textContent?.trim()).toBe(
      "Stromtarif",
    );
  });

  it("passes HA objects through property updates without serializing state", async () => {
    const element = await mount();
    element.hass = {
      language: "en-GB",
      states: {
        "sensor.example": {
          entity_id: "sensor.example",
          state: "unavailable",
          attributes: {},
        },
      },
    };
    await flush();

    expect(shadow(element).querySelector("h1")?.textContent?.trim()).toBe(
      "General information",
    );
    expect(
      [...shadow(element).querySelectorAll("nav a")].map((link) =>
        link.textContent?.trim(),
      ),
    ).toEqual([
      "General information",
      "Electricity tariff",
      "Time-of-use tariff",
      "Grid-serving charging",
      "Amortization",
    ]);
    expect(
      shadow(element).querySelector(".dashboard")?.getAttribute("lang"),
    ).toBe("en");
    expect(element.hass.states["sensor.example"]).toEqual({
      entity_id: "sensor.example",
      state: "unavailable",
      attributes: {},
    });
    expect(element.hasAttribute("hass")).toBe(false);

    element.panel = { config: {}, url_path: "sax-power-vue" };
    await flush();
    expect(
      shadow(element).querySelector('[role="status"]')?.textContent,
    ).toContain("No SAX Power device is assigned");
    expect(shadow(element).querySelector(".placeholder")).toBeNull();

    element.panel = {
      config: { entry_id: "entry-2" },
      url_path: "sax-power-vue",
    };
    await flush();
    expect(shadow(element).querySelector(".placeholder")).toBeNull();
    expect(
      shadow(element).querySelector('[role="status"]')?.textContent,
    ).not.toContain("No SAX Power device is assigned");
  });

  it("shows a loading message until Home Assistant is supplied", async () => {
    const element = new SaxPowerVuePanel();
    document.body.append(element);
    await flush();

    expect(shadow(element).querySelector('[role="status"]')?.textContent).toBe(
      "Loading Home Assistant …",
    );
    element.hass = germanHass;
    element.panel = { config: { entry_id: "entry-1" } };
    await flush();

    expect(
      shadow(element).querySelector('[role="status"]')?.textContent,
    ).not.toBe("Loading Home Assistant …");
    expect(shadow(element).querySelector(".placeholder")).toBeNull();
  });

  it("navigates without reloading and notifies the HA router", async () => {
    const element = await mount();
    const onLocationChanged = vi.fn();
    window.addEventListener("location-changed", onLocationChanged, {
      once: true,
    });
    const pushState = vi.spyOn(window.history, "pushState");
    const savingsLink = shadow(element).querySelector<HTMLAnchorElement>(
      'nav a[href="/sax-power-vue/ersparnis"]',
    )!;
    savingsLink.click();
    await flush();

    expect(pushState).toHaveBeenCalledExactlyOnceWith(
      null,
      "",
      "/sax-power-vue/ersparnis",
    );
    expect(onLocationChanged).toHaveBeenCalledOnce();
    expect(onLocationChanged.mock.calls[0][0].detail).toEqual({
      replace: false,
    });
    expect(selectedLink(element)).toBe(savingsLink);
    expect(shadow(element).activeElement).toBe(
      shadow(element).querySelector("h1"),
    );

    savingsLink.click();
    await flush();
    expect(pushState).toHaveBeenCalledOnce();
  });

  it("keeps modified clicks available to native browser link handling", async () => {
    const element = await mount();
    const link = shadow(element).querySelector<HTMLAnchorElement>(
      'nav a[href="/sax-power-vue/ersparnis"]',
    )!;
    const pushState = vi.spyOn(window.history, "pushState");
    let intercepted: boolean | undefined;
    link.addEventListener("click", (event) => {
      intercepted = event.defaultPrevented;
      event.preventDefault();
    });
    link.dispatchEvent(
      new MouseEvent("click", {
        bubbles: true,
        cancelable: true,
        ctrlKey: true,
      }),
    );

    expect(intercepted).toBe(false);
    expect(pushState).not.toHaveBeenCalled();
  });

  it("reacts to browser back/forward and Home Assistant navigation", async () => {
    const element = await mount();
    window.history.replaceState(
      null,
      "",
      "/sax-power-vue/netzdienliches-laden",
    );
    window.dispatchEvent(new PopStateEvent("popstate"));
    await flush();
    expect(shadow(element).querySelector("h1")?.textContent?.trim()).toBe(
      "Netzdienliches Laden",
    );

    window.history.replaceState(null, "", "/sax-power-vue/ladeautomatik");
    window.dispatchEvent(new CustomEvent("location-changed"));
    await flush();
    expect(shadow(element).querySelector("h1")?.textContent?.trim()).toBe(
      "Zeitvariabler Tarif",
    );
  });

  it("offers recovery for unknown paths instead of showing another section", async () => {
    const element = await mount({ pathname: "/sax-power-vue/unbekannt" });

    expect(shadow(element).querySelector("h1")?.textContent?.trim()).toBe(
      "Bereich nicht gefunden",
    );
    expect(selectedLink(element)).toBeNull();
    shadow(element).querySelector<HTMLAnchorElement>(".status a")!.click();
    await flush();

    expect(selectedLink(element)?.getAttribute("href")).toBe(
      "/sax-power-vue/allgemein",
    );
  });

  it("updates narrow mode and exposes the native sidebar event", async () => {
    const element = await mount();
    expect(shadow(element).querySelector(".menu-button")).toBeNull();

    element.narrow = true;
    await flush();
    const onToggleMenu = vi.fn();
    document.addEventListener("hass-toggle-menu", onToggleMenu, { once: true });
    const button =
      shadow(element).querySelector<HTMLButtonElement>(".menu-button")!;
    expect(button.getAttribute("aria-label")).toBe("Seitenleiste öffnen");
    button.click();

    expect(onToggleMenu).toHaveBeenCalledOnce();
    expect(onToggleMenu.mock.calls[0][0].composed).toBe(true);
    expect(shadow(element).querySelector(".dashboard.narrow")).not.toBeNull();

    element.hass = { ...germanHass, kioskMode: true };
    await flush();
    expect(shadow(element).querySelector(".menu-button")).toBeNull();
  });

  it("keeps a hidden desktop sidebar reachable and respects kiosk mode", async () => {
    const element = await mount({
      hass: { ...germanHass, dockedSidebar: "always_hidden", kioskMode: false },
    });
    expect(shadow(element).querySelector(".menu-button")).not.toBeNull();

    element.hass = {
      ...germanHass,
      dockedSidebar: "always_hidden",
      kioskMode: true,
    };
    await flush();
    expect(shadow(element).querySelector(".menu-button")).toBeNull();

    element.hass = { ...germanHass, dockedSidebar: "docked", kioskMode: false };
    await flush();
    expect(shadow(element).querySelector(".menu-button")).toBeNull();
  });

  it("releases global navigation listeners on unmount and remounts cleanly", async () => {
    const element = await mount();
    const removeEventListener = vi.spyOn(window, "removeEventListener");
    element.remove();
    await flush();

    expect(removeEventListener).toHaveBeenCalledWith(
      "popstate",
      expect.any(Function),
    );
    expect(removeEventListener).toHaveBeenCalledWith(
      "location-changed",
      expect.any(Function),
    );

    window.history.replaceState(null, "", "/sax-power-vue/ersparnis");
    document.body.append(element);
    await flush();
    expect(shadow(element).querySelectorAll("nav")).toHaveLength(1);
    expect(selectedLink(element)?.getAttribute("href")).toBe(
      "/sax-power-vue/ersparnis",
    );
  });
});

it("REQ-VUE-TARIFF-EDITOR repairs missing price sensors and discards drafts when the entry changes even with an identical revision", async () => {
  const initial: TariffProfile = {
    tariff_type: "time_of_use",
    base_price_ct_kwh: null,
    feed_in_price_ct_kwh: null,
    windows: [],
    revision: "same-profile",
    can_edit: true,
  };
  const callWS = vi.fn(async (message: Readonly<Record<string, unknown>>) => ({
    ...initial,
    ...(message.type === "sax_power/dashboard/tariff/save" ? message : {}),
  }));
  const hass: HomeAssistant = {
    language: "de",
    states: {},
    connection: {
      connected: true,
      async subscribeMessage<T>(callback: (message: T) => void) {
        callback({ entities: [] } as T);
        return () => {};
      },
      addEventListener() {},
      removeEventListener() {},
    },
    callWS: <T>(message: Readonly<Record<string, unknown>>) =>
      callWS(message) as Promise<T>,
  };
  const element = await mount({
    hass,
    pathname: "/sax-power-vue/ladeautomatik",
  });
  for (let index = 0; index < 5; index++) await flush();
  expect(shadow(element).querySelector(".tariff-plan")).not.toBeNull();
  expect(shadow(element).querySelector(".time-window-control")).toBeNull();
  const edit = () =>
    shadow(element).querySelector<HTMLButtonElement>(
      ".tariff-plan__header button",
    )!;
  edit().click();
  for (let index = 0; index < 5; index++) await flush();
  const base = shadow(element).querySelector<HTMLInputElement>(
    '[name="base_price"]',
  )!;
  base.value = "42";
  base.dispatchEvent(new Event("input", { bubbles: true }));
  await flush();
  element.panel = {
    config: { entry_id: "entry-2" },
    url_path: "sax-power-vue",
  };
  for (let index = 0; index < 5; index++) await flush();
  expect(shadow(element).querySelector(".tariff-plan form")).toBeNull();
  edit().click();
  for (let index = 0; index < 5; index++) await flush();
  expect(
    shadow(element).querySelector<HTMLInputElement>('[name="base_price"]')
      ?.value,
  ).toBe("");
  expect(
    callWS.mock.calls.filter(
      ([message]) => message.type === "sax_power/dashboard/tariff/save",
    ),
  ).toHaveLength(0);
  expect(callWS).toHaveBeenLastCalledWith({
    type: "sax_power/dashboard/tariff/get",
    entry_id: "entry-2",
  });
});
it("REQ-VUE-TARIFF-EDITOR ignores a late tariff response from a previous entry", async () => {
  const initial: TariffProfile = {
    tariff_type: "time_of_use",
    base_price_ct_kwh: 30,
    feed_in_price_ct_kwh: 8,
    windows: [],
    revision: "same",
    can_edit: true,
  };
  let resolveOld: (result: TariffProfile) => void = () => {};
  const callWS = vi.fn(async (message: Readonly<Record<string, unknown>>) =>
    message.entry_id === "entry-1"
      ? new Promise<TariffProfile>((resolve) => {
          resolveOld = resolve;
        })
      : initial,
  );
  const hass: HomeAssistant = {
    language: "de",
    states: {},
    connection: {
      connected: true,
      async subscribeMessage<T>(callback: (message: T) => void) {
        callback({ entities: [] } as T);
        return () => {};
      },
      addEventListener() {},
      removeEventListener() {},
    },
    callWS: <T>(message: Readonly<Record<string, unknown>>) =>
      callWS(message) as Promise<T>,
  };
  const element = await mount({
    hass,
    pathname: "/sax-power-vue/ladeautomatik",
  });
  await flush();
  element.panel = {
    config: { entry_id: "entry-2" },
    url_path: "sax-power-vue",
  };
  for (let index = 0; index < 5; index++) await flush();
  resolveOld({ ...initial, base_price_ct_kwh: 99 });
  for (let index = 0; index < 5; index++) await flush();
  expect(shadow(element).querySelector(".tariff-plan")?.textContent).toContain(
    "30,00 ct/kWh",
  );
  expect(
    shadow(element).querySelector(".tariff-plan")?.textContent,
  ).not.toContain("99,00");
});

// REQ-VUE-ELECTRICITY-TARIFF: native changes refresh the shared saved selection.
it("refreshes tariff state after external automation switch changes", async () => {
  const fixture = await mountTariffs("off", "off");
  fixture.callWS.mockClear();
  await fixture.update("on", "off");
  expect(fixture.callWS).toHaveBeenCalledWith({
    type: "sax_power/dashboard/tariff/get",
    entry_id: "entry-1",
  });
});
