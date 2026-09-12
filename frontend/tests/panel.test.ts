import { afterEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";
import { SaxPowerVuePanel } from "../src/panel";
import { tabPath, tabs } from "../src/tabs";
import type { HassConnection, HomeAssistant } from "../src/types";

type PanelElement = InstanceType<typeof SaxPowerVuePanel>;

const germanHass: HomeAssistant = {
  language: "de",
  states: {},
  panels: { "sax-power": {} },
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
    ).toEqual(tabs.map((tab) => `/sax-power-vue/${tab.path}`));
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
    expect(root.querySelector(".existing-link")?.getAttribute("href")).toBe(
      "/sax-power",
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

  it("does not advertise an existing dashboard when none is registered", async () => {
    const element = await mount({
      pathname: "/sax-power-vue/ersparnis",
      hass: { language: "de", states: {} },
    });

    expect(shadow(element).querySelector(".existing-link")).toBeNull();
    expect(
      shadow(element).querySelector(".savings-view")?.textContent,
    ).toContain("Hinweise zur Berechnung und Datenbasis");

    element.hass = germanHass;
    await flush();
    expect(shadow(element).querySelector(".existing-link")).not.toBeNull();
  });

  it("uses Home Assistant route properties and reacts to route changes", async () => {
    const element = await mount({ routePath: "/ersparnis" });
    expect(shadow(element).querySelector("h1")?.textContent?.trim()).toBe(
      "Ersparnis",
    );

    element.route = { path: "/dynamisches-laden", prefix: "/sax-power-vue" };
    await flush();

    expect(shadow(element).querySelector("h1")?.textContent?.trim()).toBe(
      "Dynamisches Laden",
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
      "Ladeautomatik",
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
