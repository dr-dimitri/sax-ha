import { expect, test, type Locator, type Page } from "@playwright/test";
import { tabs } from "../src/tabs";
import type { HomeAssistant, TariffProfile } from "../src/types";

const pageErrors = new WeakMap<Page, string[]>();

async function openTariffMonths(panel: Locator) {
  await panel.locator("nav a[href$='/stromtarif']").click();
  await panel.locator(".electricity-charging header > button").click();
  await panel.locator(".tou-charging-advanced > summary").click();
  return panel.locator(".tou-charging-settings .month-selection");
}

// REQ-VUE-PARITY: load the HACS bundle, with explicit simulated HA boundaries.
test.beforeEach(async ({ page }, testInfo) => {
  const errors: string[] = [];
  pageErrors.set(page, errors);
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/sax-power-vue/allgemein");
  await expect(page.locator("sax-power-vue-panel .general-view")).toBeVisible();
  if (testInfo.project.name.endsWith("en"))
    await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
});

test.afterEach(({ page }) => {
  expect(pageErrors.get(page)).toEqual([]);
});

test("compact views retain readable controls and all entities across available panel widths", async ({
  page,
}, testInfo) => {
  const panel = page.locator("sax-power-vue-panel");
  const mobile = testInfo.project.name.startsWith("mobile");
  const layouts = mobile
    ? [{ width: 390, height: 844, sidebar: 0 }]
    : [
        { width: 1366, height: 768, sidebar: 256 },
        { width: 1440, height: 900, sidebar: 0 },
      ];
  const heightBudgets: Record<string, number> = {
    allgemein: 850,
    "netzdienliches-laden": 1100,
    stromtarif: 900,
    ersparnis: 1600,
  };
  const contentLabels = panel.locator(
    ".entity-gauge h2, .entity-control__name, .entity-value__name, .savings-rows dt, .savings-periods h2, .tariff-plan h2",
  );

  for (const tab of tabs) {
    if (tab.path === "stromtarif") continue;
    await panel.locator(`nav a[href='/sax-power-vue/${tab.path}']`).click();
    if (tab.path === "ersparnis")
      await expect(panel.locator(".savings-chart")).toBeVisible();
    else await expect(panel.locator(".entity-control").first()).toBeVisible();
    if (tab.path === "netzdienliches-laden") {
      await panel.locator(".month-selection__toggle").click();
      await expect(
        panel.locator(".grid-serving-source__confirmed"),
      ).toBeVisible();
      await expect(panel.locator(".grid-serving-source h3")).toBeVisible();
    }
    const expectedLabels = await contentLabels.allTextContents();
    expect(expectedLabels.length).toBeGreaterThan(0);
    const expectedControls = await panel
      .locator(".section input, .section select")
      .count();

    for (const layout of layouts) {
      await page.setViewportSize({
        width: layout.width,
        height: layout.height,
      });
      // Reserve actual host space, as HA's docked sidebar does, without changing the bundle.
      await page.addStyleTag({
        content: `sax-power-vue-panel { margin-left: ${layout.sidebar}px; width: calc(100% - ${layout.sidebar}px); }`,
      });
      await page.evaluate(
        () =>
          new Promise<void>((resolve) => {
            requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
          }),
      );
      // Preserve the dashboard height budget while inspecting every expanded control.
      const monthToggle = panel.locator(".month-selection__toggle");
      const hasMonths = (await monthToggle.count()) > 0;
      if (hasMonths) await monthToggle.click();
      const compactSize = await panel.evaluate((element) => {
        const source = (element.shadowRoot ?? element).querySelector(
          ".grid-serving-source",
        );
        const style = source ? getComputedStyle(source) : null;
        const sourceHeight = source?.getBoundingClientRect().height ?? 0;
        const sourceSpacing = style
          ? parseFloat(style.marginTop) + parseFloat(style.marginBottom)
          : 0;
        const compactPanelHeight = element.getBoundingClientRect().height;
        return {
          compactPanelHeight,
          sourceHeight,
          // Keep the original control budget and account only for the added source.
          originalControlsHeight:
            compactPanelHeight - sourceHeight - sourceSpacing,
        };
      });
      if (hasMonths) await monthToggle.click();
      await expect(contentLabels).toHaveText(expectedLabels);
      await expect(
        panel.locator(".section input, .section select"),
      ).toHaveCount(expectedControls);

      const geometry = await panel
        .locator(".section")
        .evaluate((section, isMobile) => {
          const root = section.getRootNode();
          const host =
            root instanceof ShadowRoot
              ? root.host
              : section.closest("sax-power-vue-panel")!;
          const violations: string[] = [];
          const visible = (element: Element): boolean => {
            const rect = element.getBoundingClientRect();
            return (
              rect.width > 0 &&
              rect.height > 0 &&
              getComputedStyle(element).visibility !== "hidden" &&
              !element.closest("dialog:not([open])")
            );
          };
          const name = (element: Element): string =>
            `${element.tagName.toLowerCase()} ${element.getAttribute("id") ?? element.textContent?.trim().slice(0, 65) ?? ""}`;
          const overlaps = (first: Element, second: Element): boolean => {
            const a = first.getBoundingClientRect();
            const b = second.getBoundingClientRect();
            return (
              Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1 &&
              Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1
            );
          };
          const controls = [
            ...section.querySelectorAll("input, select, button"),
          ].filter(visible);
          const targets: Element[] = [];
          for (const control of controls) {
            const checkbox = control.matches("input[type='checkbox']");
            const month =
              checkbox && control.closest(".charging-view__rows--months");
            const target = checkbox
              ? control.closest(".entity-control__switch-target")
              : control;
            if (!target) {
              violations.push(
                `${name(control)} is missing its checkbox click target`,
              );
              continue;
            }
            targets.push(target);
            const rect = target.getBoundingClientRect();
            if (rect.height < 43.5)
              violations.push(`${name(control)} target height ${rect.height}`);
            if (checkbox && rect.width < 43.5)
              violations.push(
                `${name(control)} checkbox target width ${rect.width}`,
              );
            if (checkbox) {
              const indicator = control.getBoundingClientRect();
              if (indicator.width !== 22 || indicator.height !== 22)
                violations.push(
                  `${name(control)} visible checkbox ${indicator.width}×${indicator.height}`,
                );
              if (
                indicator.left < rect.left ||
                indicator.right > rect.right ||
                indicator.top < rect.top ||
                indicator.bottom > rect.bottom
              )
                violations.push(
                  `${name(control)} extends outside its click target`,
                );
            }
            if (parseFloat(getComputedStyle(control).fontSize) < 13.99)
              violations.push(
                `${name(control)} font ${getComputedStyle(control).fontSize}`,
              );
            const card = month
              ? control.closest("form")!
              : (control.closest(
                  ".general-view__card, .charging-view__card, .savings-card, .tariff-plan",
                ) ?? control.closest("form")!);
            const bounds = card.getBoundingClientRect();
            if (
              rect.left < bounds.left - 1 ||
              rect.right > bounds.right + 1 ||
              rect.top < bounds.top - 1 ||
              rect.bottom > bounds.bottom + 1
            )
              violations.push(`${name(control)} extends outside its card`);
          }
          for (let index = 0; index < targets.length; index++) {
            for (const other of targets.slice(index + 1)) {
              if (overlaps(targets[index], other))
                violations.push(
                  `${name(targets[index])} overlaps ${name(other)}`,
                );
            }
          }
          for (const row of section.querySelectorAll(
            ".entity-control, .entity-value, .savings-rows > div",
          )) {
            const first = row.querySelector(
              ".entity-control__description, .entity-value__name, dt",
            );
            const second = row.querySelector(
              ".entity-control__input, .entity-value__state, dd",
            );
            if (
              first &&
              second &&
              visible(first) &&
              visible(second) &&
              overlaps(first, second)
            )
              violations.push(`${name(first)} overlaps its value or input`);
          }
          for (const label of section.querySelectorAll(
            ".entity-gauge h2, .entity-gauge__range, .entity-control__name, .entity-control__value, .entity-value__name, .entity-value__state, .savings-rows dt, .savings-rows dd, .savings-dates label, .savings-table th, .savings-table td, .tariff-plan th, .tariff-plan td",
          )) {
            // Mobile retains its existing smaller confirmation helper, like scale labels.
            if (isMobile && label.classList.contains("entity-control__value"))
              continue;
            if (
              visible(label) &&
              parseFloat(getComputedStyle(label).fontSize) < 13.99
            )
              violations.push(
                `${name(label)} font ${getComputedStyle(label).fontSize}`,
              );
          }
          for (const label of section.querySelectorAll(
            ".entity-gauge h2, .entity-control__name, .entity-value__name, .savings-rows dt, .savings-periods h2, .tariff-plan h2",
          )) {
            if (!visible(label)) violations.push(`${name(label)} is hidden`);
            const rect = label.getBoundingClientRect();
            const card =
              label.closest(
                ".entity-gauge, .general-view__card, .charging-view__card, .savings-card, .tariff-plan",
              ) ?? section;
            const bounds = card.getBoundingClientRect();
            if (rect.left < bounds.left - 1 || rect.right > bounds.right + 1)
              violations.push(`${name(label)} extends outside its card`);
          }
          const bounds = host.getBoundingClientRect();
          const months = section.querySelector(".charging-view__rows--months");
          const quarters = months
            ? [...months.querySelectorAll(".month-selection__quarter")]
            : [];
          const quarterColumns = quarters.length
            ? new Set(
                quarters.map((quarter) =>
                  Math.round(quarter.getBoundingClientRect().left),
                ),
              ).size
            : null;
          const quarterMonthCounts = quarters.map(
            (quarter) => quarter.querySelectorAll(".entity-control").length,
          );
          const quarterMonthColumns = quarters.map(
            (quarter) =>
              new Set(
                [...quarter.querySelectorAll(".entity-control")].map((tile) =>
                  Math.round(tile.getBoundingClientRect().left),
                ),
              ).size,
          );
          return {
            panelWidth: bounds.width,
            panelHeight: bounds.height,
            pageWidth: document.documentElement.scrollWidth,
            viewportWidth: window.innerWidth,
            controlCount: controls.length,
            quarterColumns,
            quarterMonthCounts,
            quarterMonthColumns,
            monthsHeight: months?.getBoundingClientRect().height ?? null,
            violations,
          };
        }, mobile);
      const description = `${tab.path}-${layout.width}x${layout.height}-sidebar${layout.sidebar}`;
      await testInfo.attach(description, {
        body: Buffer.from(
          JSON.stringify({ ...geometry, ...compactSize }, null, 2),
        ),
        contentType: "application/json",
      });
      if (layout.sidebar === 256) {
        await testInfo.attach(
          `compact-vue-${tab.path}-sidebar-${testInfo.project.name.endsWith("en") ? "en" : "de"}`,
          {
            body: await page.screenshot({ fullPage: true }),
            contentType: "image/png",
          },
        );
      }
      expect(geometry.panelWidth, description).toBeCloseTo(
        layout.width - layout.sidebar,
        0,
      );
      expect(geometry.pageWidth, description).toBeLessThanOrEqual(
        geometry.viewportWidth + 1,
      );
      expect(geometry.controlCount, description).toBeGreaterThan(0);
      expect(geometry.violations, description).toEqual([]);
      if (geometry.monthsHeight !== null) {
        expect(geometry.quarterColumns, description).toBe(mobile ? 1 : 2);
        expect(geometry.quarterMonthCounts, description).toEqual([3, 3, 3, 3]);
        expect(geometry.quarterMonthColumns, description).toEqual([3, 3, 3, 3]);
        expect(geometry.monthsHeight, description).toBeLessThanOrEqual(
          mobile ? 700 : 400,
        );
      }
      if (!mobile) {
        expect(compactSize.sourceHeight, description).toBeLessThanOrEqual(240);
        expect(
          compactSize.originalControlsHeight,
          description,
        ).toBeLessThanOrEqual(heightBudgets[tab.path]);
      }
    }
  }
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});

test("storage requires confirmation in both directions and cancellation keeps the HA state", async ({
  page,
}, testInfo) => {
  const panel = page.locator("sax-power-vue-panel");
  const english = testInfo.project.name.endsWith("en");
  const input = panel.locator("input[role='switch']");
  const target = panel.locator(".entity-control__switch-target");
  const dialog = panel.locator("dialog.entity-control__confirmation");
  const actions = page.locator("#actions");
  const cancel = dialog.getByRole("button", {
    name: english ? "Cancel" : "Abbrechen",
    exact: true,
  });
  const device = panel.locator(".general-view__card").filter({
    has: page.getByRole("heading", {
      name: english ? "Device" : "Gerät",
      exact: true,
    }),
  });
  await expect(panel.locator(".general-view__card > h2")).toHaveText(
    english ? ["Power", "Device"] : ["Leistung", "Gerät"],
  );
  await expect(
    device.locator(".general-view__rows > :last-child input[role='switch']"),
  ).toHaveCount(1);
  await expect(target).toHaveCount(1);
  expect(
    await target.evaluate((element) => {
      const area = element.getBoundingClientRect();
      const indicator = element.querySelector("input")!.getBoundingClientRect();
      return (
        area.width >= 44 &&
        area.height >= 44 &&
        indicator.width === 22 &&
        indicator.height === 22 &&
        area.left + 4 < indicator.left &&
        area.top + 4 < indicator.top
      );
    }),
  ).toBe(true);
  for (const [index, initial] of [true, false].entries()) {
    const title = english
      ? initial
        ? "Turn off the battery?"
        : "Turn on the battery?"
      : initial
        ? "Speicher ausschalten?"
        : "Speicher einschalten?";
    const label = english
      ? initial
        ? "Turn off"
        : "Turn on"
      : initial
        ? "Ausschalten"
        : "Einschalten";
    const previousAction =
      index === 0
        ? "Keine Aktion"
        : '1: switch.turn_off {"entity_id":"switch.demo_storage_switch"}';
    await expect(input).toBeChecked({ checked: initial });
    await target.click({ position: { x: 4, y: 4 } });
    await expect(dialog).toBeVisible();
    await expect(dialog).toHaveAccessibleName(title);
    await expect(cancel).toBeFocused();
    await expect(input).toBeChecked({ checked: initial });
    await expect(actions).toHaveText(previousAction);
    await testInfo.attach(
      `vue-storage-confirm-${initial ? "off" : "on"}-${testInfo.project.name}`,
      {
        body: await page.screenshot({ fullPage: false }),
        contentType: "image/png",
      },
    );
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(input).toBeChecked({ checked: initial });
    await expect(actions).toHaveText(previousAction);
    await input.focus();
    await page.keyboard.press("Space");
    await expect(cancel).toBeFocused();
    await cancel.click();
    await expect(dialog).toBeHidden();
    await expect(actions).toHaveText(previousAction);
    await input.click();
    await expect(cancel).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(dialog).toBeHidden();
    await expect(actions).toHaveText(previousAction);
    await input.click();
    await dialog.getByRole("button", { name: label, exact: true }).click();
    await expect(dialog).toBeHidden();
    await expect(input).toBeChecked({ checked: !initial });
    await expect(actions).toHaveText(
      `${index + 1}: switch.${initial ? "turn_off" : "turn_on"} {"entity_id":"switch.demo_storage_switch"}`,
    );
  }
});

test("one dashboard with four complete views, local assets and responsive screenshots", async ({
  page,
}, testInfo) => {
  const panel = page.locator("sax-power-vue-panel");
  const language = testInfo.project.name.endsWith("en") ? "en" : "de";
  await expect(panel.locator("nav a")).toHaveText(
    language === "de"
      ? [
          "Allgemeine Informationen",
          "Stromtarif",
          "Netzdienliches Laden",
          "Amortisation",
        ]
      : [
          "General information",
          "Electricity tariff",
          "Grid-serving charging",
          "Amortization",
        ],
  );
  expect(
    await panel
      .locator("nav a")
      .evaluateAll((links) => links.map((link) => link.getAttribute("href"))),
  ).toEqual([
    "/sax-power-vue/allgemein",
    "/sax-power-vue/stromtarif",
    "/sax-power-vue/netzdienliches-laden",
    "/sax-power-vue/ersparnis",
  ]);
  await expect(
    page
      .getByRole("navigation", { name: "Dashboard-Einstieg" })
      .getByRole("link"),
  ).toHaveCount(1);
  await expect(panel.locator(".header")).toHaveText("SAX Power");
  for (const tab of tabs) {
    await panel.locator(`nav a[href='/sax-power-vue/${tab.path}']`).click();
    await expect(panel.getByRole("heading", { level: 1 })).toHaveText(
      tab[language],
    );
    await expect(panel.locator("nav [aria-current='page']")).toHaveText(
      tab[language],
    );
    await expect(panel.locator(".placeholder")).toHaveCount(0);
    if (tab.path === "stromtarif") {
      await panel.locator(".electricity-price-details > summary").click();
      await expect(panel.locator(".electricity-price-card svg")).toBeVisible();
      await testInfo.attach(`vue-${tab.path}-${testInfo.project.name}`, {
        body: await page.screenshot({ fullPage: true }),
        contentType: "image/png",
      });
      continue;
    }
    await expect(panel).not.toContainText(
      /Änderung wird an Home Assistant gesendet|Sending change to Home Assistant/,
    );
    if (tab.path === "ersparnis") {
      await expect(panel.locator(".savings-chart")).toBeVisible();
    } else {
      await expect(
        panel.locator(".entity-control input, .entity-control select").first(),
      ).toBeVisible();
    }
    if (tab.path === "netzdienliches-laden") {
      const months = panel.locator(".charging-view__rows--months");
      const toggle = months.getByRole("button", {
        name: language === "de" ? "Ändern" : "Edit",
        exact: true,
      });
      await expect(toggle).toHaveAttribute("aria-expanded", "false");
      await expect(months.locator(".month-selection__summary")).toBeVisible();
      await toggle.click();
      await expect(months.locator(".month-selection__toggle")).toHaveAttribute(
        "aria-expanded",
        "true",
      );
      await expect(months.locator(".month-selection__quarter")).toHaveCount(4);
      await expect(months.getByRole("switch")).toHaveCount(12);
      await expect(months.locator(".entity-control__value")).toHaveCount(0);
    }
    if (tab.path === "netzdienliches-laden") {
      const window = panel.locator(".time-window-control");
      await expect(window).toHaveCount(1);
      await expect(window.getByRole("slider")).toHaveCount(2);
      await expect(
        window.locator(".time-window-control__confirmed"),
      ).toContainText("22:00");
      await expect(
        window.locator(".time-window-control__confirmed"),
      ).toContainText("06:00");
      if (language === "de")
        await expect(
          window.locator(".time-window-control__confirmed"),
        ).toContainText("Uhr");
      await expect(window.locator("input[type=text]").nth(0)).toHaveValue(
        "22:00",
      );
      await expect(window.locator("input[type=text]").nth(1)).toHaveValue(
        "06:00",
      );
    }
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    );
    expect(overflow).toBe(false);
    await expect(
      panel
        .locator(".entity-control")
        .filter({ has: page.getByRole("switch") })
        .locator(".entity-control__value"),
    ).toHaveCount(0);
    await testInfo.attach(`vue-${tab.path}-${testInfo.project.name}`, {
      body: await page.screenshot({ fullPage: true }),
      contentType: "image/png",
    });
  }
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  expect(
    await page.evaluate(() =>
      performance
        .getEntriesByType("resource")
        .map((entry) => new URL(entry.name).origin),
    ),
  ).toEqual(expect.arrayContaining(["http://127.0.0.1:5190"]));
  const external = await page.evaluate(() =>
    performance
      .getEntriesByType("resource")
      .some((entry) => new URL(entry.name).origin !== location.origin),
  );
  expect(external).toBe(false);
});

// REQ-VUE-PARITY / REQ-ECONOMICS-TARIFFS: show price windows on the tariff tab.
test("eight tariff windows match the compact electricity summary and detailed amortization table without service actions", async ({
  page,
}, testInfo) => {
  const panel = page.locator("sax-power-vue-panel");
  const english = testInfo.project.name.endsWith("en");
  const mobile = testInfo.project.name.startsWith("mobile");
  const windows = [
    { start: "22:00", end: "02:00", price_eur_kwh: 0.18 },
    { start: "03:00", end: "05:00", price_eur_kwh: -0.05 },
    { start: "06:00", end: "08:00", price_eur_kwh: 0 },
    { start: "09:00", end: "11:00", price_eur_kwh: 0.21 },
    { start: "12:00", end: "14:00", price_eur_kwh: 0.22 },
    { start: "15:00", end: "17:00", price_eur_kwh: 0.23 },
    { start: "18:00", end: "20:00", price_eur_kwh: 0.2456 },
    { start: "20:00", end: "21:00", price_eur_kwh: 0.28 },
  ];
  const price = (value: number) =>
    `${new Intl.NumberFormat(english ? "en-GB" : "de-DE", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value * 100)} ct/kWh`;
  await page.locator("#tariff-timed").click();
  await panel.evaluate((element, configuredWindows) => {
    const host = element as HTMLElement & { hass: HomeAssistant };
    const entityId = "sensor.demo_economics_current_import_price";
    const current = host.hass.states[entityId];
    const original = host.hass.callWS!;
    host.hass = {
      ...host.hass,
      callWS: async <T>(
        request: Readonly<Record<string, unknown>>,
      ): Promise<T> => {
        const result = await original<T>(request);
        if (request.type !== "sax_power/dashboard/tariff/get") return result;
        const profile = result as TariffProfile;
        const windows = configuredWindows.map((window) => ({
          start: window.start,
          end: window.end,
          price_ct_kwh: window.price_eur_kwh * 100,
        }));
        return {
          ...profile,
          revision: "eight-window-fixture",
          windows,
          profiles: {
            ...profile.profiles,
            time_of_use: { ...profile.profiles!.time_of_use, windows },
          },
        } as T;
      },
      states: {
        ...host.hass.states,
        [entityId]: {
          ...current,
          attributes: {
            ...current.attributes,
            windows: configuredWindows.map((window, index) => ({
              ...window,
              low_tariff: index === 1,
            })),
            active_window: { start: "18:00", end: "20:00" },
            low_tariff_price_eur_kwh: -0.05,
          },
        },
      },
    };
  }, windows);
  await panel.locator("nav a[href$='/stromtarif']").click();
  await expect(panel.getByRole("heading", { level: 1 })).toHaveText(
    english ? "Electricity tariff" : "Stromtarif",
  );
  await expect(
    panel.getByRole("heading", {
      name: english ? "Grid charging window" : "Netzladezeitfenster",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(panel.locator(".time-window-control")).toHaveCount(0);
  await expect(
    panel.locator(".time-window-control input[type=text]"),
  ).toHaveCount(0);
  const tariff = panel.locator(".tariff-plan");
  await expect(tariff.getByRole("heading", { level: 2 })).toHaveText(
    english
      ? "1. When is your electricity cheaper?"
      : "1. Wann ist dein Strom günstig?",
  );
  const periods = tariff.locator(".tariff-plan__periods li");
  await expect(periods).toHaveCount(8);
  for (const [index, window] of windows.entries()) {
    await expect(periods.nth(index)).toContainText(window.start);
    await expect(periods.nth(index)).toContainText(window.end);
    await expect(periods.nth(index)).toContainText(price(window.price_eur_kwh));
  }
  await expect(periods.first()).toContainText(
    english ? "overnight" : "über Nacht",
  );
  await expect(tariff.locator(".tariff-plan__badge")).toHaveCount(1);
  await expect(periods.nth(1).locator(".tariff-plan__badge")).toBeVisible();
  await expect(tariff).toContainText(price(0.32));
  await expect(tariff.locator("input, select, [role=slider]")).toHaveCount(0);
  const expectedPeriods = await periods.allTextContents();
  for (const width of mobile ? [390, 320] : [1440, 1100]) {
    await page.setViewportSize({ width, height: mobile ? 844 : 1000 });
    await expect(periods).toHaveText(expectedPeriods);
    const geometry = await periods.evaluateAll((items) => ({
      pageWidth: document.documentElement.scrollWidth,
      viewportWidth: innerWidth,
      overflowing: items
        .filter((item) => {
          const bounds = item.getBoundingClientRect();
          return [...item.children].some((child) => {
            const rect = child.getBoundingClientRect();
            return rect.left < bounds.left - 1 || rect.right > bounds.right + 1;
          });
        })
        .map((item) => item.textContent),
    }));
    expect(geometry.pageWidth).toBeLessThanOrEqual(geometry.viewportWidth);
    expect(geometry.overflowing).toEqual([]);
  }
  await panel.locator("nav a[href$='/ersparnis']").click();
  await expect(panel.locator(".savings-tariff")).toBeVisible();
  const rows = tariff.locator(".tariff-plan__table tbody tr");
  await tariff.locator(".tariff-plan__all-prices > summary").click();
  await expect(rows).toHaveCount(9);
  for (const [index, window] of windows.entries()) {
    await expect(rows.nth(index).locator("td")).toHaveText([
      index === 6
        ? english
          ? "now"
          : "jetzt"
        : index === 1
          ? english
            ? "cheapest"
            : "günstig"
          : "",
      window.start,
      window.end,
      price(window.price_eur_kwh),
    ]);
  }
  await expect(rows.last().locator("td")).toHaveText([
    "",
    english ? "Standard price" : "Standardpreis",
    price(0.32),
  ]);
  await expect(tariff.locator(".tariff-plan__current")).toHaveCount(1);
  await expect(tariff.locator(".tariff-plan__low")).toHaveCount(1);
  await expect(tariff.locator(".tariff-plan__low")).toContainText("03:00");
  await expect(tariff).toContainText(
    english
      ? "How are the cheapest charging times selected?"
      : "Wie werden günstige Ladezeiten ausgewählt?",
  );
  await expect(tariff.locator(".tariff-plan__current")).toContainText("18:00");
  await expect(tariff).toContainText(price(0.0812));
  await expect(tariff).toContainText(
    english ? "Next price change" : "Nächster Preiswechsel",
  );
  await expect(tariff.locator("input, select, [role=slider]")).toHaveCount(0);
  const expectedRows = await rows.allTextContents();
  for (const width of mobile ? [390, 320] : [1366, 1440]) {
    const sidebar = width === 1366 ? 256 : 0;
    await page.setViewportSize({ width, height: mobile ? 844 : 1000 });
    await page.addStyleTag({
      content: `sax-power-vue-panel { margin-left: ${sidebar}px; width: calc(100% - ${sidebar}px); }`,
    });
    await expect(rows).toHaveText(expectedRows);
    const geometry = await tariff.evaluate((element) => {
      const bounds = element.getBoundingClientRect();
      const scroll = element.querySelector<HTMLElement>(
        ".tariff-plan__scroll",
      )!;
      const scrollBounds = scroll.getBoundingClientRect();
      const firstCell = scroll.querySelector("tbody td")!;
      const lastCell = scroll.querySelector(
        "tbody tr:last-child td:last-child",
      )!;
      scroll.scrollLeft = 0;
      const reachesStart =
        firstCell.getBoundingClientRect().left >= scrollBounds.left - 1;
      scroll.scrollLeft = scroll.scrollWidth;
      const reachesEnd =
        lastCell.getBoundingClientRect().right <= scrollBounds.right + 1;
      scroll.scrollLeft = 0;
      return {
        left: bounds.left,
        right: bounds.right,
        pageWidth: document.documentElement.scrollWidth,
        viewportWidth: window.innerWidth,
        reachesStart,
        reachesEnd,
        unreadable: [...element.querySelectorAll("th, td, p")]
          .filter((cell) => !cell.closest("details:not([open])"))
          .filter((cell) => {
            const style = getComputedStyle(cell);
            const rect = cell.getBoundingClientRect();
            const text = document.createRange();
            text.selectNodeContents(cell);
            const lines = new Set(
              [...text.getClientRects()].map((line) => Math.round(line.top)),
            );
            return (
              rect.width === 0 ||
              rect.height === 0 ||
              style.visibility === "hidden" ||
              parseFloat(style.fontSize) < 13.99 ||
              style.textOverflow === "ellipsis" ||
              (cell.matches("th, td") && lines.size > 1)
            );
          })
          .map((cell) => cell.textContent),
      };
    });
    expect(geometry.left).toBeGreaterThanOrEqual(sidebar);
    expect(geometry.right).toBeLessThanOrEqual(width);
    expect(geometry.pageWidth).toBeLessThanOrEqual(geometry.viewportWidth);
    expect(geometry.reachesStart).toBe(true);
    expect(geometry.reachesEnd).toBe(true);
    expect(geometry.unreadable).toEqual([]);
    const screenshotPath = testInfo.outputPath(
      `tariff-eight-windows-${width}.png`,
    );
    await page.screenshot({ path: screenshotPath, fullPage: true });
    await testInfo.attach(
      `tariff-eight-windows-${width}-${testInfo.project.name}`,
      {
        path: screenshotPath,
        contentType: "image/png",
      },
    );
  }
  await panel.locator("nav a[href$='/stromtarif']").click();
  await expect(periods).toHaveText(expectedPeriods);
  await panel.evaluate((element) => {
    const host = element as HTMLElement & { hass: HomeAssistant };
    const id = "sensor.demo_economics_current_import_price";
    const current = host.hass.states[id];
    host.hass = {
      ...host.hass,
      states: {
        ...host.hass.states,
        [id]: {
          ...current,
          attributes: {
            ...current.attributes,
            low_tariff_price_eur_kwh: null,
          },
        },
      },
    };
  });
  await expect(tariff.locator(".tariff-plan__badge")).toHaveCount(0);
  await expect(tariff.locator(".tariff-plan__low-unavailable")).toContainText(
    english ? "SOC charging remains blocked" : "SOC-Ladung bleibt gesperrt",
  );
  await expect(panel.locator(".time-window-control")).toHaveCount(0);
  await page.locator("#legacy-tariff").click();
  await expect(tariff).toHaveCount(0);
  await expect(panel.locator(".time-window-control")).toHaveCount(0);
  await expect(panel.locator(".electricity-charging")).toHaveCount(0);
  await expect(panel.locator(".electricity-activation")).toHaveCount(0);
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});

test("confirmed shared values, errors, reconnect and unavailable controls", async ({
  page,
}) => {
  const panel = page.locator("sax-power-vue-panel");
  const number = panel
    .locator(".entity-control")
    .filter({ has: page.locator("input[type=number]") });
  const input = number.locator("input");
  await expect(input).toHaveValue("80");
  await input.fill("85");
  await number.getByRole("button").click();
  await expect(number.locator(".entity-control__value")).toContainText("85");
  await expect(page.locator("#actions")).toContainText("1: number.set_value");
  await page.locator("#external").click();
  await expect(input).toHaveValue("75");
  await panel.locator("nav a[href$='/stromtarif']").click();
  await page.locator("#tariff-dynamic").click();
  await panel.locator(".electricity-charging header button").click();
  const shared = panel.locator("input[max='100']");
  await expect(shared).toHaveValue("75");
  await page.locator("#connection").click();
  await expect(shared).toHaveCount(0);
  await expect(panel.locator(".status[role='alert']")).toContainText(
    /Keine Verbindung|Disconnected/,
  );
  await page.locator("#connection").click();
  await expect(shared).toBeEnabled();
  await page.locator("#unavailable").click();
  await expect(shared).toHaveCount(0);
  await expect(
    panel.locator("[data-strategy][aria-pressed='true']"),
  ).toHaveCount(0);
  for (const method of await panel.locator("[data-strategy]").all())
    await expect(method).toBeDisabled();
  await expect(panel.locator(".dynamic-charging-summary")).toContainText(
    /Ladeweise nicht verfügbar|Charging method unavailable/,
  );
  await page.locator("#unavailable").click();
  await expect(shared).toHaveValue("75");
  await page.locator("#failure").click();
  await shared.fill("90");
  await panel
    .locator("form")
    .filter({ has: page.locator("input[max='100']") })
    .getByRole("button")
    .click();
  await expect(panel.getByRole("alert")).toBeVisible();
  await expect(
    panel
      .locator("form")
      .filter({ has: page.locator("input[max='100']") })
      .locator(".entity-control__value"),
  ).toContainText("75");
  await expect(page.locator("#actions")).toContainText("2: number.set_value");
});

test("tariff months, grid-serving overnight window and guided negative price settings use their matching controls", async ({
  page,
}, testInfo) => {
  const panel = page.locator("sax-power-vue-panel");
  const months = await openTariffMonths(panel);
  await months.locator(".month-selection__toggle").click();
  await expect(months.getByRole("switch")).toHaveCount(12);
  await expect(panel.locator(".time-window-control")).toHaveCount(0);
  const firstMonth = months.getByRole("switch").first();
  const firstTarget = months.locator(".entity-control__switch-target").first();
  const outsideIndicator = await firstTarget.evaluate((target) => {
    const area = target.getBoundingClientRect();
    const indicator = target.querySelector("input")!.getBoundingClientRect();
    const x = area.left + 4;
    const y = area.top + 4;
    return (
      x < indicator.left ||
      x > indicator.right ||
      y < indicator.top ||
      y > indicator.bottom
    );
  });
  expect(outsideIndicator).toBe(true);
  await firstTarget.click({ position: { x: 4, y: 4 } });
  await expect(firstMonth).not.toBeChecked();
  await expect(page.locator("#actions")).toHaveText(
    '1: switch.turn_off {"entity_id":"switch.demo_timed_charge_month_1"}',
  );
  await firstMonth.focus();
  await expect(firstMonth).toBeFocused();
  await page.keyboard.press("Space");
  await expect(firstMonth).toBeChecked();
  await expect(page.locator("#actions")).toHaveText(
    '2: switch.turn_on {"entity_id":"switch.demo_timed_charge_month_1"}',
  );
  await page.locator("#failure").click();
  const secondMonth = months.getByRole("switch").nth(1);
  await secondMonth.click();
  await expect(secondMonth).toBeChecked();
  await expect(months.getByRole("alert")).toBeVisible();
  await expect(page.locator("#actions")).toHaveText(
    '3: switch.turn_off {"entity_id":"switch.demo_timed_charge_month_2"}',
  );
  const longName = testInfo.project.name.endsWith("en")
    ? "February – additional custom month description"
    : "Februar – zusätzliche individuelle Monatsbeschreibung";
  // Stress only text geometry; metadata and service behavior have separate assertions.
  await months
    .locator(".entity-control__name")
    .nth(1)
    .evaluate((label, name) => {
      label.textContent = name;
    }, longName);
  await expect(secondMonth).toHaveAccessibleName(longName);
  const errorFits = await months.getByRole("alert").evaluate((message) => {
    const error = message.getBoundingClientRect();
    const form = message.closest("form")!;
    const bounds = form.getBoundingClientRect();
    return (
      error.left >= bounds.left &&
      error.right <= bounds.right &&
      error.top >= bounds.top &&
      error.bottom <= bounds.bottom
    );
  });
  expect(errorFits).toBe(true);
  const longNameFits = await secondMonth.evaluate((control) => {
    const form = control.closest("form")!;
    const tile = form.getBoundingClientRect();
    const name = form
      .querySelector(".entity-control__name")!
      .getBoundingClientRect();
    const input = form.querySelector("input")!.getBoundingClientRect();
    const overlapping =
      Math.min(name.right, input.right) > Math.max(name.left, input.left) &&
      Math.min(name.bottom, input.bottom) > Math.max(name.top, input.top);
    return (
      name.left >= tile.left &&
      name.right <= tile.right &&
      name.bottom <= tile.bottom &&
      !overlapping
    );
  });
  expect(longNameFits).toBe(true);
  await panel.locator("nav a[href$='/netzdienliches-laden']").click();
  await panel.locator(".month-selection__toggle").click();
  await expect(panel.locator(".charging-view").getByRole("switch")).toHaveCount(
    13,
  );
  await expect(
    panel.getByText("PV-Prognose 13.9.", { exact: true }),
  ).toBeVisible();
  const timeWindow = panel.locator(".time-window-control");
  const times = timeWindow.locator("input[type=text]");
  await expect(times.nth(0)).toHaveValue("22:00");
  await expect(times.nth(1)).toHaveValue("06:00");
  await times.nth(0).fill("23:15");
  await timeWindow.locator("button[type=submit]").click();
  await expect(page.locator("#actions")).toHaveText(
    '4: sax_power.set_grid_serving_window {"device_id":"demo-device","start":"23:15:00","end":"06:00:00"}',
  );
  await page.locator("#tariff-dynamic").click();
  await panel.locator("nav a[href$='/stromtarif']").click();
  await panel.locator(".electricity-charging header button").click();
  await expect(panel.locator("[data-strategy]")).toHaveCount(4);
  await panel.locator('[data-strategy="smart"]').click();
  await expect(panel.locator('[data-strategy="smart"]')).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await panel.locator(".dynamic-charging-advanced summary").click();
  const price = panel.locator("input[min='-100']").first();
  await price.fill("-12.5");
  await panel
    .locator("form")
    .filter({ has: page.locator("input[min='-100']") })
    .first()
    .getByRole("button")
    .click();
  await expect(page.locator("#actions")).toContainText('"value":-12.5');
  await expect(price).toHaveValue("-12.5");
});

// REQ-VUE-PARITY: quarter groups keep arbitrary confirmed month selections readable.
test("compact month summaries retain gaps, whole-tile controls and errors when collapsed", async ({
  page,
}, testInfo) => {
  const panel = page.locator("sax-power-vue-panel");
  const english = testInfo.project.name.endsWith("en");
  const actions = page.locator("#actions");
  let writes = 0;
  for (const [path, kind] of [
    ["stromtarif", "timed_charge"],
    ["netzdienliches-laden", "grid_serving"],
  ]) {
    await panel.locator(`nav a[href$='/${path}']`).click();
    const months =
      kind === "timed_charge"
        ? await openTariffMonths(panel)
        : panel.locator(".month-selection");
    const toggle = months.locator(".month-selection__toggle");
    const quarters = months.locator(".month-selection__quarters");
    const summary = months.locator(".month-selection__summary");
    const count = months.locator(".month-selection__count");
    const switches = months.getByRole("switch");
    const targets = months.locator(".entity-control__switch-target");
    const before = await actions.innerText();
    await expect(toggle).toHaveAccessibleName(english ? "Edit" : "Ändern");
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(quarters).toBeHidden();
    await expect(summary).toBeVisible();
    await toggle.focus();
    await page.keyboard.press("Enter");
    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await expect(quarters).toBeVisible();
    await expect(switches).toHaveCount(12);
    await expect(actions).toHaveText(before);

    // Each click starts in tile padding, outside the visible checkbox.
    for (const month of [2, 5, 6, 7, 9, 10, 11, 12]) {
      await targets.nth(month - 1).click({ position: { x: 4, y: 4 } });
      await expect(switches.nth(month - 1)).not.toBeChecked();
      writes += 1;
      await expect(actions).toHaveText(
        `${writes}: switch.turn_off {"entity_id":"switch.demo_${kind}_month_${month}"}`,
      );
    }
    const selected = english
      ? "January, March–April, August"
      : "Januar, März–April, August";
    await expect(summary).toHaveText(selected);
    await expect(count).toHaveText(
      english ? "4 of 12 months selected" : "4 von 12 Monaten ausgewählt",
    );
    const lastWrite = await actions.innerText();
    await toggle.click();
    await expect(quarters).toBeHidden();
    await expect(summary).toBeVisible();
    await expect(summary).toHaveText(selected);
    await expect(actions).toHaveText(lastWrite);
    await testInfo.attach(`month-summary-${kind}-${testInfo.project.name}`, {
      body: await page.screenshot({ fullPage: true }),
      contentType: "image/png",
    });
    await toggle.click();
    for (let index = 0; index < 12; index++)
      await expect(switches.nth(index)).toBeChecked({
        checked: [1, 3, 4, 8].includes(index + 1),
      });
    await expect(actions).toHaveText(lastWrite);

    // A rejected change cannot alter the summary or disappear on collapse.
    await page.locator("#failure").click();
    await targets.nth(1).click({ position: { x: 4, y: 4 } });
    writes += 1;
    await expect(months.getByRole("alert")).toBeVisible();
    await expect(switches.nth(1)).not.toBeChecked();
    await expect(summary).toHaveText(selected);
    await expect(actions).toHaveText(
      `${writes}: switch.turn_on {"entity_id":"switch.demo_${kind}_month_2"}`,
    );
    const rejectedWrite = await actions.innerText();
    await toggle.click();
    await expect(quarters).toBeHidden();
    await expect(months.getByRole("alert")).toBeVisible();
    await expect(summary).toHaveText(selected);
    await expect(actions).toHaveText(rejectedWrite);

    // Retrying a gap month joins only its neighboring run after HA confirms it.
    await toggle.click();
    await switches.nth(1).focus();
    await page.keyboard.press("Space");
    await expect(switches.nth(1)).toBeChecked();
    writes += 1;
    await expect(actions).toHaveText(
      `${writes}: switch.turn_on {"entity_id":"switch.demo_${kind}_month_2"}`,
    );
    await expect(summary).toHaveText(
      english ? "January–April, August" : "Januar–April, August",
    );
    await expect(months.getByRole("alert")).toHaveCount(0);
    await toggle.click();
    await expect(summary).toBeVisible();
    await expect(count).toHaveText(
      english ? "5 of 12 months selected" : "5 von 12 Monaten ausgewählt",
    );
  }
});

test("grid-serving time window supports dragging, keyboard and atomic submission", async ({
  page,
  context,
}, testInfo) => {
  const panel = page.locator("sax-power-vue-panel");
  const mobile = testInfo.project.name.startsWith("mobile");
  await page.locator("#legacy-times").click();
  if (mobile) await page.setViewportSize({ width: 390, height: 844 });
  await panel.locator("nav a[href$='/netzdienliches-laden']").click();
  const window = panel.locator(".time-window-control");
  const inputs = window.locator("input[type=text]");
  const markers = window.getByRole("slider");
  const apply = window.locator("button[type=submit]");
  const confirmed = window.locator(".time-window-control__confirmed");
  const before = await page.locator("#actions").innerText();
  await expect(markers).toHaveCount(2);
  await expect(window.locator(".time-window-control__segment")).toHaveCount(2);
  await expect(inputs.nth(0)).toHaveAttribute("placeholder", "HH:MM");
  await expect(inputs.nth(1)).toHaveAttribute("placeholder", "HH:MM");
  await expect(confirmed).toContainText("22:00:17");
  await expect(confirmed).toContainText("06:00:29");
  await expect(apply).toBeEnabled();
  await markers.nth(0).click();
  await expect(inputs.nth(0)).toHaveValue("22:00");
  await expect(apply).toBeEnabled();
  await markers.nth(0).press("ArrowRight");
  await expect(inputs.nth(0)).toHaveValue("22:01");
  await expect(inputs.nth(1)).toHaveValue("06:00");
  await expect(confirmed).toContainText("22:00");
  await expect(page.locator("#actions")).toHaveText(before);

  await markers.nth(0).scrollIntoViewIfNeeded();
  const rail = await window.locator(".time-window-control__rail").boundingBox();
  const marker = await markers.nth(0).boundingBox();
  expect(rail).not.toBeNull();
  expect(marker).not.toBeNull();
  const from = {
    x: marker!.x + marker!.width / 2,
    y: marker!.y + marker!.height / 2,
  };
  const to = { x: rail!.x + rail!.width / 2, y: from.y };
  if (mobile) {
    const touch = await context.newCDPSession(page);
    await touch.send("Input.dispatchTouchEvent", {
      type: "touchStart",
      touchPoints: [{ ...from, id: 0 }],
    });
    await touch.send("Input.dispatchTouchEvent", {
      type: "touchMove",
      touchPoints: [{ ...to, id: 0 }],
    });
    await touch.send("Input.dispatchTouchEvent", {
      type: "touchEnd",
      touchPoints: [],
    });
    await touch.detach();
  } else {
    await page.mouse.move(from.x, from.y);
    await page.mouse.down();
    await page.mouse.move(to.x, to.y, { steps: 8 });
    await page.mouse.up();
  }
  await expect(inputs.nth(0)).toHaveValue("12:00");
  await expect(inputs.nth(1)).toHaveValue("06:00");
  await expect(page.locator("#actions")).toHaveText(before);

  await inputs.nth(1).fill("12:00");
  await expect(window.locator(".time-window-control__segment")).toHaveCount(0);
  const same = await markers.evaluateAll((elements) =>
    elements.map((element) => {
      const bounds = element.getBoundingClientRect();
      return {
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height,
      };
    }),
  );
  expect(same[0].x).toBeCloseTo(same[1].x);
  expect(same[0].y + same[0].height).toBeLessThanOrEqual(same[1].y);
  await markers.nth(1).press("Home");
  await expect(inputs.nth(1)).toHaveValue("00:00");
  await markers.nth(1).press("End");
  await expect(inputs.nth(1)).toHaveValue("23:59");
  await expect(markers.nth(1)).toHaveAttribute("aria-valuemax", "86340");
  await expect(markers.nth(1)).toHaveAttribute("aria-valuenow", "86340");
  await inputs.nth(0).fill("23:15");
  await inputs.nth(1).fill("06:30");
  await apply.click();
  await expect(page.locator("#actions")).toHaveText(
    '1: sax_power.set_grid_serving_window {"device_id":"demo-device","start":"23:15:00","end":"06:30:00"}',
  );
  await expect(confirmed).toContainText("23:15");
  await expect(confirmed).toContainText("06:30");
  await expect(confirmed).not.toContainText(":17");
  await expect(confirmed).not.toContainText(":29");
  await expect(apply).toBeEnabled();
  if (mobile) {
    await page.setViewportSize({ width: 320, height: 1100 });
    const narrow = await inputs.evaluateAll((elements) =>
      elements.map((element) => {
        const bounds = element.getBoundingClientRect();
        return {
          left: bounds.left,
          right: bounds.right,
          width: bounds.width,
        };
      }),
    );
    for (const field of narrow) {
      expect(field.width).toBeGreaterThanOrEqual(136);
      expect(field.left).toBeGreaterThanOrEqual(0);
      expect(field.right).toBeLessThanOrEqual(320);
    }
    const ticks = await window
      .locator(".time-window-control__ticks span")
      .evaluateAll((elements) =>
        elements.map((element) => {
          const range = document.createRange();
          range.selectNodeContents(element);
          const bounds = range.getBoundingClientRect();
          return { left: bounds.left, right: bounds.right };
        }),
      );
    for (let index = 1; index < ticks.length; index++)
      expect(ticks[index].left).toBeGreaterThan(ticks[index - 1].right);
  }
  await testInfo.attach(`time-window-grid_serving-${testInfo.project.name}`, {
    body: await page.screenshot({ fullPage: true }),
    contentType: "image/png",
  });
});

test("failed time-window submission preserves both confirmed values and can be retried", async ({
  page,
}) => {
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href$='/netzdienliches-laden']").click();
  const window = panel.locator(".time-window-control");
  const inputs = window.locator("input[type=text]");
  const confirmed = window.locator(".time-window-control__confirmed");
  const apply = window.locator("button[type=submit]");
  await page.locator("#failure").click();
  await inputs.nth(0).fill("10:00");
  await inputs.nth(1).fill("15:00");
  await apply.click();
  await expect(window.getByRole("alert")).toBeVisible();
  await expect(confirmed).toContainText("22:00");
  await expect(confirmed).toContainText("06:00");
  await expect(inputs.nth(0)).toHaveValue("10:00");
  await expect(inputs.nth(1)).toHaveValue("15:00");
  await apply.click();
  await expect(confirmed).toContainText("10:00");
  await expect(confirmed).toContainText("15:00");
  await expect(window.getByRole("alert")).toHaveCount(0);
  await expect(page.locator("#actions")).toContainText(
    "2: sax_power.set_grid_serving_window",
  );
  await page.locator("#unavailable").click();
  await expect(inputs.nth(0)).toBeDisabled();
  await expect(inputs.nth(1)).toBeDisabled();
  for (const marker of await window.getByRole("slider").all())
    await expect(marker).toBeDisabled();
});

test("one inclusive date selection drives signed chart and accessible table", async ({
  page,
}, testInfo) => {
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href$='/ersparnis']").click();
  await expect(panel.locator(".savings-periods article")).toHaveCount(4);
  await expect(panel.locator(".savings-chart__bar--negative")).toHaveCount(1);
  await expect(panel.locator(".savings-explanation")).not.toHaveAttribute(
    "open",
    "",
  );
  const dates = panel.locator("input[type=date]");
  await dates.nth(0).fill("2026-08-01");
  await dates.nth(1).fill("2026-08-31");
  await panel.locator(".savings-dates button[type=submit]").click();
  const formatter = new Intl.DateTimeFormat(
    testInfo.project.name.endsWith("en") ? "en-GB" : "de-DE",
    { dateStyle: "medium", timeZone: "UTC" },
  );
  const selectedStart = formatter.format(new Date("2026-08-01T12:00:00Z"));
  const selectedEnd = formatter.format(new Date("2026-08-31T12:00:00Z"));
  await expect(panel.locator(".savings-selected-dates")).toHaveText(
    `${selectedStart} – ${selectedEnd}`,
  );
  await expect(dates.nth(0)).toHaveValue("2026-08-01");
  await expect(panel.getByRole("img")).toHaveAccessibleName(/Verlauf|Changes/);
  await panel.locator(".savings-chart-table summary").click();
  await expect(panel.locator(".savings-chart-table tbody tr")).toHaveCount(2);
  await expect(
    panel.locator(".savings-chart-table tbody tr").first(),
  ).toContainText(selectedStart);
  await expect(panel.locator(".savings-chart-table")).toContainText(/-0[,.]75/);
  await panel.locator(".savings-explanation summary").click();
  await expect(panel.locator(".savings-explanation")).toHaveAttribute(
    "open",
    "",
  );
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});

for (const legacyPath of ["ladeautomatik", "dynamisches-laden"]) {
  test(`old ${legacyPath} deep link redirects to electricity tariff and preserves history without activation`, async ({
    page,
  }) => {
    const panel = page.locator("sax-power-vue-panel");
    await page.goto(`/sax-power-vue/${legacyPath}`);
    await expect(page).toHaveURL(/stromtarif$/);
    await expect(panel.locator("nav [aria-current='page']")).toHaveAttribute(
      "href",
      "/sax-power-vue/stromtarif",
    );
    await expect(panel.locator("nav a")).toHaveCount(4);
    await expect(panel.locator(`nav a[href$='/${legacyPath}']`)).toHaveCount(0);
    await page.reload();
    await expect(panel.locator(".electricity-tariff-view")).toBeVisible();
    await panel.locator("nav a[href$='/netzdienliches-laden']").click();
    await page.goBack();
    await expect(page).toHaveURL(/stromtarif$/);
    await page.goForward();
    await expect(page).toHaveURL(/netzdienliches-laden$/);
    await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  });
}

test("next cell calibration displays only the calendar date in the HA language", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const row = page.locator("sax-power-vue-panel .entity-value").filter({
    has: page.getByText(
      english ? "Next cell calibration" : "Nächste Zellkalibrierung",
      { exact: true },
    ),
  });
  const expectedDate = new Intl.DateTimeFormat(english ? "en-GB" : "de-DE", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(new Date("2026-09-14T00:00:00Z"));
  await expect(row.locator(".entity-value__state")).toHaveText(expectedDate);
  await expect(row.locator(".entity-value__state")).not.toContainText(
    /\d{1,2}:\d{2}/,
  );
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});

test("keyboard navigation, deep links, reload and browser history", async ({
  page,
}) => {
  const panel = page.locator("sax-power-vue-panel");
  const link = panel.locator("nav a[href$='/stromtarif']");
  await link.focus();
  await expect(link).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(panel.getByRole("heading", { level: 1 })).toBeFocused();
  await expect(page).toHaveURL(/stromtarif$/);
  await page.goBack();
  await expect(page).toHaveURL(/allgemein$/);
  await page.goto("/sax-power-vue/ersparnis");
  await expect(panel.locator(".savings-chart")).toBeVisible();
  await page.reload();
  await expect(panel.locator(".savings-chart")).toBeVisible();
  await expect(panel.locator("nav [aria-current='page']")).toHaveAttribute(
    "href",
    "/sax-power-vue/ersparnis",
  );
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});

// REQ-VUE-ELECTRICITY-TARIFF: compact chart and explicit persisted settings.
test("electricity tariff saves compact prices and keeps all editor fields usable down to 320px", async ({
  page,
}, testInfo) => {
  const en = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href='/sax-power-vue/stromtarif']").click();
  await panel.locator(".electricity-price-details > summary").click();
  await expect(panel.locator(".tariff-price-chart svg")).toBeVisible();
  await expect(panel.locator(".electricity-master input")).toHaveCount(1);
  await page.setViewportSize({ width: 320, height: 844 });
  const editButton = panel.locator(".electricity-charging header > button");
  expect((await editButton.boundingBox())?.height).toBeLessThanOrEqual(48);
  const price = panel.locator(".tariff-plan");
  await expect(price.locator("form")).toHaveCount(0);
  await price
    .getByRole("button", { name: en ? "Edit" : "Bearbeiten", exact: true })
    .click();
  await page.setViewportSize({ width: 320, height: 844 });
  const fields = price.locator("input:visible,select:visible");
  for (const input of await fields.all()) {
    const box = await input.boundingBox();
    expect(box?.x).toBeGreaterThanOrEqual(0);
    expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(320);
    expect(box?.width).toBeGreaterThanOrEqual(150);
  }
  await price.locator('input[name="base_price"]').fill(en ? "34.25" : "34,25");
  await price
    .getByRole("button", { name: en ? "Save" : "Speichern", exact: true })
    .click();
  await expect(price.locator("form")).toHaveCount(0);
  await expect(price).toContainText(en ? "34.25" : "34,25");
  await expect(page.locator("#actions")).toContainText(
    '"base_price_ct_kwh":34.25',
  );
  await price
    .getByRole("button", { name: en ? "Edit" : "Bearbeiten", exact: true })
    .click();
  await price.locator('input[name="base_price"]').fill("99");
  await price
    .getByRole("button", { name: en ? "Cancel" : "Abbrechen", exact: true })
    .click();
  await expect(price).toContainText(en ? "34.25" : "34,25");
  expect(
    await panel.evaluate(
      (element) => element.scrollWidth <= element.clientWidth + 1,
    ),
  ).toBe(true);
});
test("electricity tariff explicitly selects dynamic and uses one central automation switch", async ({
  page,
}, testInfo) => {
  const en = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href='/sax-power-vue/stromtarif']").click();
  await panel
    .getByRole("button", {
      name: en ? "Change tariff" : "Tarif wechseln",
      exact: true,
    })
    .click();
  await panel.locator('input[value="dynamic"]').check();
  await expect(page.locator("#actions")).not.toContainText("configure_tariff");
  await panel
    .getByRole("button", {
      name: en ? "Apply tariff" : "Tarif übernehmen",
      exact: true,
    })
    .click();
  await expect(panel.locator(".electricity-active strong")).toHaveText(
    en ? "Dynamic" : "Dynamisch",
  );
  const master = panel.locator(".electricity-master input");
  const checked = await master.isChecked();
  await master.setChecked(!checked);
  await expect(page.locator("#actions")).toContainText(
    `"automation_enabled":${!checked}`,
  );
  await expect(page.locator("#actions")).toContainText(
    '"tariff_type":"dynamic"',
  );
  const prices = panel.locator(".electricity-prices");
  await prices
    .getByRole("button", { name: en ? "Edit" : "Bearbeiten", exact: true })
    .click();
  await prices.locator('[name="dynamic_feed"]').fill(en ? "9.25" : "9,25");
  await page.locator("#failure").click();
  await prices
    .getByRole("button", { name: en ? "Save" : "Speichern", exact: true })
    .click();
  await expect(panel.locator('[role="alert"]')).toBeVisible();
  await expect(prices.locator('[name="dynamic_feed"]')).toHaveValue(
    en ? "9.25" : "9,25",
  );
  await prices
    .getByRole("button", { name: en ? "Save" : "Speichern", exact: true })
    .click();
  await expect(prices.locator("form")).toHaveCount(0);
  await expect(prices).toContainText(en ? "9.25" : "9,25");
});
test("electricity chart preserves negative values and gaps and marks missing tomorrow honestly", async ({
  page,
}, testInfo) => {
  const en = testInfo.project.name.endsWith("en");
  await page.locator("#tariff-dynamic").click();
  await page.evaluate(() => {
    const panel = document.querySelector(
      "sax-power-vue-panel",
    ) as HTMLElement & { hass: HomeAssistant };
    const original = panel.hass.callWS!;
    panel.hass = {
      ...panel.hass,
      callWS: async <T>(
        request: Readonly<Record<string, unknown>>,
      ): Promise<T> => {
        const result = await original<any>(request);
        if (request.type === "sax_power/dashboard/tariff/series") {
          if (request.day === "tomorrow")
            return {
              ...result,
              status: "unavailable",
              slots: [],
              gaps: [{ start: result.start, end: result.end }],
              reason: "price_forecast_missing",
            };
          const removed = result.slots.splice(8, 1)[0];
          return {
            ...result,
            status: "partial",
            gaps: [{ start: removed.start, end: removed.end }],
          };
        }
        return result;
      },
    };
  });
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href='/sax-power-vue/stromtarif']").click();
  await panel.locator(".electricity-price-details > summary").click();
  const chart = panel.locator(".tariff-price-chart");
  await expect(chart).toContainText(
    en ? "Gaps remain empty" : "Lücken werden nicht aufgefüllt",
  );
  const curve = chart.locator(".tariff-price-chart__line");
  expect((await curve.getAttribute("d"))?.match(/M/g)?.length).toBe(2);
  await chart.locator("svg").focus();
  await page.keyboard.press("End");
  await expect(chart.locator(".tariff-price-chart__detail")).toContainText(
    "ct/kWh",
  );
  await chart.locator("summary").click();
  await expect(chart.locator("table")).toContainText(en ? "-4.00" : "-4,00");
  await panel
    .getByRole("button", { name: en ? "Tomorrow" : "Morgen", exact: true })
    .click();
  await expect(chart.locator("svg")).toHaveCount(0);
  await expect(chart).toContainText(
    en ? "Prices are not available" : "noch keine Preise verfügbar",
  );
});
