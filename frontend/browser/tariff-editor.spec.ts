import { expect, test } from "@playwright/test";

// REQ-VUE-TARIFF-EDITOR: exercise the bundled UI against the simulated HA API.
test("tariff editor saves cents explicitly and remains compact after editing on desktop and mobile", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/sax-power-vue/ladeautomatik");
  if (english) await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
  const panel = page.locator("sax-power-vue-panel");
  const tariff = panel.locator(".tariff-plan");
  await expect(tariff).toBeVisible();
  const compactHeight = (await tariff.boundingBox())!.height;
  const edit = tariff.getByRole("button", {
    name: english ? "Edit" : "Bearbeiten",
    exact: true,
  });
  await edit.click();
  const base = tariff.locator('[name="base_price"]');
  const feed = tariff.locator('[name="feed_in_price"]');
  await expect(base).toBeFocused();
  await expect(base).toHaveValue(english ? "32.00" : "32,00");
  await expect(tariff.locator(".tariff-plan__window")).toHaveCount(2);
  await expect(tariff.locator('input[type="time"]').first()).toHaveAttribute(
    "step",
    "60",
  );
  await base.fill("31,25");
  await feed.fill("8.12");
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  const add = tariff.getByRole("button", {
    name: english ? "+ Add time window" : "+ Zeitfenster hinzufügen",
    exact: true,
  });
  await add.click();
  const last = tariff.locator(".tariff-plan__window").last();
  await last.locator('input[type="time"]').nth(0).fill("22:00");
  await last.locator('input[type="time"]').nth(1).fill("03:00");
  await last.locator('input[type="text"]').fill("-2,50");
  const save = tariff.getByRole("button", {
    name: english ? "Save" : "Speichern",
    exact: true,
  });
  await save.click();
  await expect(tariff.getByRole("alert")).toContainText(
    english ? "overlap" : "überschneiden",
  );
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  await last.locator('input[type="time"]').nth(1).fill("00:00");
  for (const width of testInfo.project.name.startsWith("mobile")
    ? [390, 320]
    : [1440, 1100]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await expect(save).toBeVisible();
    if (width <= 400) {
      const widths = await tariff
        .locator('input[type="time"]')
        .evaluateAll((inputs) =>
          inputs.map((input) => input.getBoundingClientRect().width),
        );
      expect(widths.every((inputWidth) => inputWidth >= 150)).toBe(true);
    }
    await testInfo.attach(`tariff-editor-${width}-${testInfo.project.name}`, {
      body: await page.screenshot({ fullPage: true }),
      contentType: "image/png",
    });
  }
  await page.locator("#failure").click();
  await save.click();
  await expect(tariff.getByRole("alert")).toContainText(
    english ? "not saved" : "nicht gespeichert",
  );
  await expect(base).toHaveValue("31,25");
  await save.click();
  await expect(tariff.locator("form")).toHaveCount(0);
  await expect(edit).toBeFocused();
  await expect(tariff).toContainText(english ? "31.25 ct/kWh" : "31,25 ct/kWh");
  await expect(tariff).toContainText(english ? "-2.50 ct/kWh" : "-2,50 ct/kWh");
  await expect(page.locator("#actions")).toContainText(
    '"base_price_ct_kwh":31.25',
  );
  await page.setViewportSize(
    testInfo.project.use.viewport ?? { width: 1440, height: 1000 },
  );
  expect((await tariff.boundingBox())!.height).toBeLessThan(compactHeight + 90);
  await edit.click();
  await base.fill("99");
  await tariff
    .getByRole("button", {
      name: english ? "Cancel" : "Abbrechen",
      exact: true,
    })
    .click();
  await expect(edit).toBeFocused();
  await expect(tariff).not.toContainText("99,00");
  await panel.locator("nav a[href='/sax-power-vue/ersparnis']").click();
  await expect(tariff).toContainText(english ? "31.25 ct/kWh" : "31,25 ct/kWh");
  await edit.click();
  await expect(base).toHaveValue(english ? "31.25" : "31,25");
  expect(errors).toEqual([]);
});
