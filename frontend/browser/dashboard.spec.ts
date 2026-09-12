import { expect, test, type Page } from "@playwright/test";
import { tabs } from "../src/tabs";

const pageErrors = new WeakMap<Page, string[]>();

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
    ladeautomatik: 1150,
    "netzdienliches-laden": 1100,
    "dynamisches-laden": 900,
    ersparnis: 1600,
  };
  const contentLabels = panel.locator(
    ".entity-gauge h2, .entity-control__name, .entity-value__name, .savings-rows dt, .savings-periods h2",
  );

  for (const tab of tabs) {
    await panel.locator(`nav a[href='/sax-power-vue/${tab.path}']`).click();
    if (tab.path === "ersparnis")
      await expect(panel.locator(".savings-chart")).toBeVisible();
    else await expect(panel.locator(".entity-control").first()).toBeVisible();
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
          for (const control of controls) {
            const rect = control.getBoundingClientRect();
            if (rect.height < 43.5)
              violations.push(`${name(control)} height ${rect.height}`);
            if (parseFloat(getComputedStyle(control).fontSize) < 13.99)
              violations.push(
                `${name(control)} font ${getComputedStyle(control).fontSize}`,
              );
            const card =
              control.closest(
                ".general-view__card, .charging-view__card, .savings-card",
              ) ?? control.closest("form")!;
            const bounds = card.getBoundingClientRect();
            if (
              rect.left < bounds.left - 1 ||
              rect.right > bounds.right + 1 ||
              rect.top < bounds.top - 1 ||
              rect.bottom > bounds.bottom + 1
            )
              violations.push(`${name(control)} extends outside its card`);
          }
          for (let index = 0; index < controls.length; index++) {
            for (const other of controls.slice(index + 1)) {
              if (overlaps(controls[index], other))
                violations.push(
                  `${name(controls[index])} overlaps ${name(other)}`,
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
            ".entity-gauge h2, .entity-gauge__range, .entity-control__name, .entity-control__value, .entity-value__name, .entity-value__state, .savings-rows dt, .savings-rows dd, .savings-dates label, .savings-table th, .savings-table td",
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
            ".entity-gauge h2, .entity-control__name, .entity-value__name, .savings-rows dt, .savings-periods h2",
          )) {
            if (!visible(label)) violations.push(`${name(label)} is hidden`);
            const rect = label.getBoundingClientRect();
            const card =
              label.closest(
                ".entity-gauge, .general-view__card, .charging-view__card, .savings-card",
              ) ?? section;
            const bounds = card.getBoundingClientRect();
            if (rect.left < bounds.left - 1 || rect.right > bounds.right + 1)
              violations.push(`${name(label)} extends outside its card`);
          }
          const bounds = host.getBoundingClientRect();
          return {
            panelWidth: bounds.width,
            panelHeight: bounds.height,
            pageWidth: document.documentElement.scrollWidth,
            viewportWidth: window.innerWidth,
            controlCount: controls.length,
            violations,
          };
        }, mobile);
      const description = `${tab.path}-${layout.width}x${layout.height}-sidebar${layout.sidebar}`;
      await testInfo.attach(description, {
        body: Buffer.from(JSON.stringify(geometry, null, 2)),
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
      if (!mobile)
        expect(geometry.panelHeight, description).toBeLessThanOrEqual(
          heightBudgets[tab.path],
        );
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
    await input.click();
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
    await input.click();
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

test("five complete views, local assets, responsive screenshots and parallel entry", async ({
  page,
}, testInfo) => {
  const panel = page.locator("sax-power-vue-panel");
  const language = testInfo.project.name.endsWith("en") ? "en" : "de";
  await expect(
    page
      .getByRole("navigation", { name: "Parallele Dashboard-Einstiege" })
      .getByRole("link"),
  ).toHaveCount(2);
  for (const tab of tabs) {
    await panel.locator(`nav a[href='/sax-power-vue/${tab.path}']`).click();
    await expect(panel.getByRole("heading", { level: 1 })).toHaveText(
      tab[language],
    );
    await expect(panel.locator("nav [aria-current='page']")).toHaveText(
      tab[language],
    );
    await expect(panel.locator(".placeholder")).toHaveCount(0);
    if (tab.path === "ersparnis") {
      await expect(panel.locator(".savings-chart")).toBeVisible();
    } else {
      await expect(
        panel.locator(".entity-control input, .entity-control select").first(),
      ).toBeVisible();
    }
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    );
    expect(overflow).toBe(false);
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
  await panel.locator("nav a[href$='/dynamisches-laden']").click();
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
  await expect(shared).toBeDisabled();
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

test("overnight times, months, native strategy options and negative prices", async ({
  page,
}) => {
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href$='/ladeautomatik']").click();
  await expect(panel.getByRole("switch")).toHaveCount(13);
  const times = panel.locator("input[type=time]");
  await expect(times.nth(0)).toHaveValue("22:00:00");
  await expect(times.nth(1)).toHaveValue("06:00:00");
  await times.nth(0).fill("23:15:00");
  await panel
    .locator("form")
    .filter({ has: page.locator("input[type=time]") })
    .first()
    .getByRole("button")
    .click();
  await expect(page.locator("#actions")).toContainText('"time":"23:15:00"');
  await panel.getByRole("switch").nth(1).click();
  await expect(panel.getByRole("switch").nth(1)).not.toBeChecked();
  await panel.locator("nav a[href$='/netzdienliches-laden']").click();
  await expect(panel.getByRole("switch")).toHaveCount(13);
  await expect(
    panel.getByText("PV-Prognose 13.9.", { exact: true }),
  ).toBeVisible();
  await panel.locator("nav a[href$='/dynamisches-laden']").click();
  await expect(panel.locator("select option")).toHaveCount(4);
  await panel.getByRole("combobox").selectOption("smart");
  await expect(panel.getByRole("combobox")).toHaveValue("smart");
  const price = panel.locator("input[min='-1']").first();
  await price.fill("-0.125");
  await panel
    .locator("form")
    .filter({ has: page.locator("input[min='-1']") })
    .first()
    .getByRole("button")
    .click();
  await expect(page.locator("#actions")).toContainText('"value":-0.125');
  await expect(price).toHaveValue("-0.125");
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

test("keyboard navigation, deep links, reload and browser history", async ({
  page,
}) => {
  const panel = page.locator("sax-power-vue-panel");
  const link = panel.locator("nav a[href$='/ladeautomatik']");
  await link.focus();
  await expect(link).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(panel.getByRole("heading", { level: 1 })).toBeFocused();
  await expect(page).toHaveURL(/ladeautomatik$/);
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
