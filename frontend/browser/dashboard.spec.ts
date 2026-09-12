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
    .filter({ has: shared })
    .getByRole("button")
    .click();
  await expect(panel.getByRole("alert")).toBeVisible();
  await expect(
    panel
      .locator("form")
      .filter({ has: shared })
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
    .filter({ has: times.nth(0) })
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
    .filter({ has: price })
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
