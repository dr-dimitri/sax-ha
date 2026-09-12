import { expect, test } from "@playwright/test";

declare global {
  interface Window {
    saxDemoHems(
      mode: string | null,
      attributes?: Record<string, unknown>,
    ): void;
  }
}

test.beforeEach(async ({ page }, testInfo) => {
  await page.goto("/sax-power-vue/allgemein");
  await expect(page.locator("sax-power-vue-panel .general-view")).toBeVisible();
  if (testInfo.project.name.endsWith("en"))
    await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
});

test("REQ-HEMS-CONFIGURATION: exactly one timed mode with keyboard, failure and reconnect", async ({
  page,
}, testInfo) => {
  await page.evaluate(() => window.saxDemoHems("timed"));
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href='/sax-power-vue/ladeautomatik']").click();
  const control = panel.locator(".timed-charge-mode");
  const standard = control.locator('input[value="standard"]');
  const adaptive = control.locator('input[value="adaptive"]');
  await expect(adaptive).toBeChecked();
  await adaptive.focus();
  await page.keyboard.press("ArrowLeft");
  await expect(standard).toBeChecked();
  await expect(adaptive).not.toBeChecked();
  await expect(page.locator("#actions")).toContainText('"option":"standard"');
  await page.locator("#failure").click();
  await adaptive.click();
  await expect(control.getByRole("alert")).toBeVisible();
  await expect(standard).toBeChecked();
  await expect(adaptive).not.toBeChecked();
  await adaptive.click();
  await expect(adaptive).toBeChecked();
  await expect(standard).not.toBeChecked();
  await expect(control.getByRole("alert")).toHaveCount(0);
  await expect(page.locator("#actions")).toContainText(
    "3: select.select_option",
  );
  expect(
    await control.evaluate((el) => el.scrollWidth - el.clientWidth),
  ).toBeLessThanOrEqual(1);
  await control.screenshot({
    path: testInfo.outputPath("timed-charge-mode.png"),
  });
  await page.locator("#unavailable").click();
  await expect(standard).toBeDisabled();
  await expect(adaptive).toBeDisabled();
  await expect(control.locator("input:checked")).toHaveCount(0);
  await page.locator("#unavailable").click();
  await expect(adaptive).toBeChecked();
  await page.locator("#connection").click();
  await expect(control).toHaveCount(0);
  await page.locator("#connection").click();
  await expect(adaptive).toBeChecked();
  await expect(control.locator("input:checked")).toHaveCount(1);
  await expect(page.locator("#actions")).toContainText(
    "3: select.select_option",
  );
});

for (const tariff of ["timed", "dynamic"] as const) {
  test(`REQ-HEMS-FORECAST-UNCERTAINTY: ${tariff} explains evidence and preserves unknown values`, async ({
    page,
  }, testInfo) => {
    const english = testInfo.project.name.endsWith("en");
    await page.evaluate(
      (mode) =>
        window.saxDemoHems(mode, {
          forecast_quality: {
            mode: "observe",
            history_days: 28,
            available_history_days: 7,
            archive: { enabled: true, pairs_count: 75 },
            uncertainty: {
              status: "validated",
              expected_kwh: 0.8,
              lower_kwh: 0,
              upper_kwh: 1.1,
              training_nights: 60,
              validation_nights: 30,
              empirical_coverage: 0.8,
            },
          },
        }),
      tariff,
    );
    const panel = page.locator("sax-power-vue-panel");
    await panel
      .locator(
        `nav a[href='/sax-power-vue/${tariff === "timed" ? "ladeautomatik" : "dynamisches-laden"}']`,
      )
      .click();
    const quality = panel.locator(".hems-quality");
    await expect(quality.locator('[data-testid="hems-range"]')).toContainText(
      english ? "0–1.1 kWh" : "0–1,1 kWh",
    );
    await quality.locator("summary").focus();
    await page.keyboard.press("Enter");
    await expect(quality.locator("details")).toHaveAttribute("open", "");
    await expect(quality).toContainText(
      english ? "does not guarantee" : "keine Garantie",
    );
    const overflow = await quality.evaluate(
      (element) => element.scrollWidth - element.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
    await quality.screenshot({
      path: testInfo.outputPath("forecast-quality.png"),
    });
    await page.evaluate(
      (mode) =>
        window.saxDemoHems(mode, {
          forecast_quality: {
            archive: { enabled: true },
            uncertainty: { status: "unavailable", reason: "stale" },
          },
        }),
      tariff,
    );
    await expect(quality.locator('[data-testid="hems-range"]')).toHaveCount(0);
    await expect(quality).toContainText(english ? "outdated" : "veraltet");
    await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  });
}

for (const tariff of ["timed", "dynamic"] as const) {
  test(`REQ-HEMS-OBSERVABILITY: ${tariff} is responsive, readonly and keyboard accessible`, async ({
    page,
  }, testInfo) => {
    const english = testInfo.project.name.endsWith("en");
    await page.evaluate((mode) => window.saxDemoHems(mode), tariff);
    const panel = page.locator("sax-power-vue-panel");
    const path = tariff === "timed" ? "ladeautomatik" : "dynamisches-laden";
    await panel.locator(`nav a[href='/sax-power-vue/${path}']`).click();
    const card = panel.locator(".hems-card");
    await expect(card).toBeVisible();
    await expect(card).toContainText(english ? "1.25 kWh" : "1,25 kWh");
    await expect(card).toContainText(
      english
        ? "No acknowledged grid charging"
        : "Derzeit keine bestätigte Netzladung",
    );
    await expect(card.locator('[data-testid="hems-next"]')).toContainText(
      "00:05",
    );
    const summary = card.locator("summary");
    await card.screenshot({ path: testInfo.outputPath("night-control.png") });
    await summary.focus();
    await page.keyboard.press("Enter");
    await expect(card.locator("details")).toHaveAttribute("open", "");
    await expect(card).toContainText("42 %");
    await expect(card).toContainText(
      english ? "SAX assumption" : "SAX-Annahme",
    );
    const bounds = await card.evaluate((element) => {
      const rect = element.getBoundingClientRect();
      return {
        left: rect.left,
        right: rect.right,
        width: innerWidth,
        client: element.clientWidth,
        scroll: element.scrollWidth,
      };
    });
    expect(bounds.left).toBeGreaterThanOrEqual(0);
    expect(bounds.right).toBeLessThanOrEqual(bounds.width);
    expect(bounds.scroll).toBeLessThanOrEqual(bounds.client + 1);
    await expect(page.locator("#actions")).toHaveText("Keine Aktion");
    await expect(panel).not.toContainText("Bestätigter Wert:");
  });
}

test("fallback, override, acknowledged calibration and reconnect preserve backend truth", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  await page.evaluate(() =>
    window.saxDemoHems("timed", {
      status: "fallback",
      fallback: true,
      reason_codes: ["pv_stale_forecast"],
      remaining_grid_kwh: null,
      target_soc: null,
      planned_start: null,
      planned_end: null,
      next_evaluation_at: null,
      execution_constraint: "manual_override",
    }),
  );
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href='/sax-power-vue/ladeautomatik']").click();
  const card = panel.locator(".hems-card");
  await expect(card).toContainText(
    english ? "Fallback to min/max SOC" : "Rückfall auf Min-/Max-SOC",
  );
  await expect(card).toContainText(
    english ? "Manual control" : "Manuelle Steuerung",
  );
  await expect(card.locator('[data-testid="hems-next"]')).toHaveText(
    english ? "Unknown" : "Unbekannt",
  );
  await expect(card.locator(".hems-card__metrics")).not.toContainText("0 kWh");
  await page.locator("#connection").click();
  await expect(card).toHaveCount(0);
  await page.locator("#connection").click();
  await page.evaluate(() =>
    window.saxDemoHems("timed", {
      execution_charging: true,
      calibration: true,
      execution_target_soc: 100,
      next_evaluation_at: "2026-09-12T22:12:00Z",
    }),
  );
  await expect(card).toContainText(
    english
      ? "Grid charge command acknowledged"
      : "Netzladebefehl vom Gerät bestätigt",
  );
  await expect(card).toContainText("100 %");
  await expect(card.locator('[data-testid="hems-next"]')).toContainText(
    "00:12",
  );
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});
