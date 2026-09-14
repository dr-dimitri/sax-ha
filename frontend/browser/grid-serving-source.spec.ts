import { expect, test } from "@playwright/test";

test("grid-serving PV source keeps confirmed values and drafts while saving or failing", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/sax-power-vue/netzdienliches-laden");
  const english = testInfo.project.name.endsWith("en");
  if (english) await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
  const source = page.locator("sax-power-vue-panel .grid-serving-source");
  await expect(source.locator(".grid-serving-source__confirmed")).toHaveText(
    "Solarertrag heute verbleibend",
  );
  await source
    .getByRole("button", { name: english ? "Edit" : "Bearbeiten", exact: true })
    .click();
  const picker = source.locator("select");
  await expect(picker).toBeFocused();
  await expect(
    picker.locator('option[value="sensor.demo_grid_serving_forecast"]'),
  ).toHaveCount(0);
  await picker.selectOption("sensor.demo_remaining_forecast_alternative");
  await page.locator("#hold-action").click();
  await source
    .getByRole("button", { name: english ? "Save" : "Speichern", exact: true })
    .click();
  await expect(source).toHaveAttribute("aria-busy", "true");
  await expect(source.getByRole("status")).toContainText(
    english ? "Saving selection" : "wird gespeichert",
  );
  await expect(picker).toBeDisabled();
  await expect(source.locator(".grid-serving-source__confirmed")).toHaveText(
    "Solarertrag heute verbleibend",
  );
  await page.locator("#failure").click();
  await page.locator("#release-action").click();
  await expect(source.getByRole("alert")).toBeVisible();
  await expect(picker).toHaveValue(
    "sensor.demo_remaining_forecast_alternative",
  );
  await expect(picker).toBeEnabled();
  await source
    .getByRole("button", { name: english ? "Save" : "Speichern", exact: true })
    .click();
  await expect(source.locator(".grid-serving-source__confirmed")).toHaveText(
    "Alternative Solarprognose heute",
  );
  await expect(source.getByRole("status")).toContainText(
    english ? "Source saved" : "Quelle gespeichert",
  );
  await expect(
    source.getByRole("button", {
      name: english ? "Edit" : "Bearbeiten",
      exact: true,
    }),
  ).toBeFocused();
  await expect(page.locator("#actions")).toContainText(
    "1: sax_power.grid_serving_source",
  );
  expect(
    await source.evaluate(
      (element) => element.scrollWidth <= element.clientWidth,
    ),
  ).toBe(true);
  expect(errors).toEqual([]);
});
