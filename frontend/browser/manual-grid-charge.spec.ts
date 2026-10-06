import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }, testInfo) => {
  await page.goto("/sax-power-vue/netzdienliches-laden");
  if (testInfo.project.name.endsWith("en"))
    await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
});

test("manual charge buttons fit their card and preserve accessible labels across panel widths", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const card = page.locator("sax-power-vue-panel .manual-grid-charge");
  const english = testInfo.project.name.endsWith("en");
  await expect(card.getByRole("heading", { level: 2 })).toHaveText(
    english ? "Manual grid charging" : "Manuelles Netzladen",
  );
  const power = card.getByRole("spinbutton", {
    name: english ? "Charging power (W)" : "Ladeleistung (W)",
  });
  await expect(power).toHaveValue("1000");
  await expect(power).toHaveAttribute("min", "1");
  await expect(power).toHaveAttribute("max", "32768");
  for (const control of await card.locator("input, button").all()) {
    const description = await control.getAttribute("aria-describedby");
    expect(description?.trim()).toBeTruthy();
    for (const id of description!.split(" "))
      await expect(card.locator(`[id="${id}"]`)).toHaveCount(1);
  }
  const violations = await card.evaluate((element) => {
    const bounds = element.getBoundingClientRect();
    const failures: string[] = [];
    const controls = [...element.querySelectorAll("input, button")];
    for (const control of controls) {
      const rect = control.getBoundingClientRect();
      if (rect.height < 43.5 || rect.width < 43.5)
        failures.push(`${control.tagName} target is too small`);
      if (parseFloat(getComputedStyle(control).fontSize) < 13.99)
        failures.push(`${control.tagName} text is too small`);
      if (
        rect.left < bounds.left ||
        rect.right > bounds.right ||
        rect.top < bounds.top ||
        rect.bottom > bounds.bottom
      )
        failures.push(`${control.tagName} leaves the card`);
      if (control.scrollWidth > control.clientWidth + 1)
        failures.push(`${control.tagName} clips its text`);
    }
    for (let index = 0; index < controls.length; index++) {
      const first = controls[index]!.getBoundingClientRect();
      for (const other of controls.slice(index + 1)) {
        const second = other.getBoundingClientRect();
        if (
          Math.min(first.right, second.right) -
            Math.max(first.left, second.left) >
            1 &&
          Math.min(first.bottom, second.bottom) -
            Math.max(first.top, second.top) >
            1
        )
          failures.push("Control targets overlap");
      }
    }
    if (element.scrollWidth > element.clientWidth + 1)
      failures.push("Card overflows horizontally");
    return failures;
  });
  expect(violations).toEqual([]);
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  expect(errors).toEqual([]);
});

test("manual start and stop wait for physical responses, preserve drafts on failure, and prevent duplicate writes", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const card = page.locator("sax-power-vue-panel .manual-grid-charge");
  const english = testInfo.project.name.endsWith("en");
  const start = card.getByRole("button", {
    name: english ? "Enable grid charging" : "Netzladen aktivieren",
    exact: true,
  });
  const stop = card.getByRole("button", {
    name: english ? "Disable grid charging" : "Netzladen abschalten",
    exact: true,
  });
  const power = card.getByRole("spinbutton");
  const telemetry = card.locator(".manual-grid-charge__telemetry");
  const confirmed = await telemetry.textContent();
  await power.fill("1250");
  await page.locator("#hold-action").click();
  await start.click();
  await expect(page.locator("#actions")).toContainText(
    "1: sax_power.start_grid_charge",
  );
  await expect(page.locator("#actions")).toContainText(
    '"device_id":"demo-device","power":-1250',
  );
  await expect(card).toHaveAttribute("aria-busy", "true");
  await expect(card.getByRole("status")).toContainText(
    english ? "Sending grid charging command" : "Netzladebefehl wird",
  );
  await expect(start).toBeDisabled();
  await expect(stop).toBeDisabled();
  await expect(power).toBeDisabled();
  await expect(telemetry).toHaveText(confirmed!);
  await card.locator("form").evaluate((form) => {
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    form.querySelector<HTMLButtonElement>('button[type="button"]')!.click();
  });
  await expect(page.locator("#actions")).toContainText(
    "1: sax_power.start_grid_charge",
  );
  await page.locator("#failure").click();
  await page.locator("#release-action").click();
  await expect(card.getByRole("alert")).toContainText(
    english ? "failed" : "fehlgeschlagen",
  );
  await expect(power).toHaveValue("1250");
  await expect(power).toHaveAttribute("aria-invalid", "false");
  await expect(telemetry).toHaveText(confirmed!);
  await start.click();
  await expect(page.locator("#actions")).toContainText(
    "2: sax_power.start_grid_charge",
  );
  await expect(card).toHaveAttribute("aria-busy", "false");
  await expect(telemetry).toContainText(english ? "1,250 W" : "1.250 W");
  await power.fill("0");
  await start.click();
  await expect(card.getByRole("alert")).toBeVisible();
  await expect(power).toHaveAttribute("aria-invalid", "true");
  await expect(page.locator("#actions")).toContainText(
    "2: sax_power.start_grid_charge",
  );
  await page.locator("#hold-action").click();
  await stop.click();
  await expect(card).toHaveAttribute("aria-busy", "true");
  await expect(page.locator("#actions")).toContainText(
    '3: sax_power.stop_grid_charge {"device_id":"demo-device"}',
  );
  await expect(telemetry).toContainText(english ? "1,250 W" : "1.250 W");
  await page.locator("#failure").click();
  await page.locator("#release-action").click();
  await expect(card.getByRole("alert")).toContainText(
    english ? "failed" : "fehlgeschlagen",
  );
  await expect(power).toHaveValue("0");
  await expect(power).toHaveAttribute("aria-invalid", "false");
  await expect(telemetry).toContainText(english ? "1,250 W" : "1.250 W");
  await stop.click();
  await expect(page.locator("#actions")).toContainText(
    "4: sax_power.stop_grid_charge",
  );
  await expect(card).toHaveAttribute("aria-busy", "false");
  await expect(telemetry).toContainText("0 W");
  await expect(power).toHaveValue("0");
  expect(errors).toEqual([]);
});

test("manual controls disable on unavailable telemetry and connection loss without writing", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const card = panel.locator(".manual-grid-charge");
  const power = card.getByRole("spinbutton");
  await power.fill("1750");
  await page.locator("#unavailable").click();
  for (const button of await card.getByRole("button").all())
    await expect(button).toBeDisabled();
  await expect(card.getByRole("status")).toContainText(
    english ? "unavailable" : "nicht verfügbar",
  );
  await expect(power).toHaveValue("1750");
  await page.locator("#unavailable").click();
  await page.locator("#connection").click();
  for (const button of await card.getByRole("button").all())
    await expect(button).toBeDisabled();
  await expect(card.getByRole("status")).toContainText(
    english ? "Disconnected" : "Keine Verbindung",
  );
  await expect(power).toHaveValue("1750");
  await page.locator("#connection").click();
  await panel.locator("nav a[href$='/allgemein']").click();
  await panel.locator("nav a[href$='/netzdienliches-laden']").click();
  await expect(card.getByRole("button").first()).toBeEnabled();
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});
