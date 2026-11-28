import { expect, test } from "@playwright/test";
import type { HomeAssistant } from "../src/types";

test("all low tariffs confirms the mode and grid target together after retry", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const method = english
    ? "In all low-tariff windows"
    : "In allen Niedrigtarifen";
  const fixedTarget = english
    ? "Fixed grid charge target"
    : "Festes Netzladeziel";
  await page.goto("/sax-power-vue/allgemein");
  if (english) await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href$='/stromtarif']").click();
  await panel.evaluate((element) => {
    const host = element as HTMLElement & { hass: HomeAssistant };
    const entityId = "number.demo_timed_charge_min_soc";
    host.hass = {
      ...host.hass,
      states: {
        ...host.hass.states,
        [entityId]: { ...host.hass.states[entityId]!, state: "70" },
      },
    };
  });

  const charging = panel.locator(".electricity-charging");
  const settings = charging.locator(".tou-charging-settings");
  const summary = settings.locator(".tou-charging-summary");
  const choose = settings.getByRole("button", { name: method });
  const prices = panel.locator(".tariff-plan__periods .tariff-plan__badge");
  await expect(prices).toHaveCount(1);
  await charging.locator("header .editor-actions > button:first-child").click();
  await expect(choose).toBeEnabled();
  await choose.click();
  await expect(choose).toHaveAttribute("aria-pressed", "true");
  await expect(summary).toContainText(fixedTarget);
  await expect(charging.getByRole("spinbutton")).toHaveCount(2);
  await expect(charging.locator(".month-selection")).toBeVisible();
  await expect(panel).not.toHaveAttribute("data-tariff-configure-requests");

  const target = charging.getByRole("spinbutton", {
    name: english ? "Grid charge target (%)" : "Netzladeziel (%)",
    exact: true,
  });
  await target.fill("40");
  await target.press("Tab");
  const apply = charging
    .locator(".electricity-charging-editor .electricity-actions button")
    .first();
  await page.locator("#hold-action").click();
  await page.locator("#failure").click();
  await apply.click({ clickCount: 2 });
  await expect(apply).toBeDisabled();
  await expect(choose).toBeDisabled();
  await expect(target).toBeDisabled();
  await expect(settings.getByRole("status").first()).toContainText(
    english ? "Applying charging method" : "Ladeweise wird übernommen",
  );
  await expect(panel).toHaveAttribute("data-tariff-configure-requests", "1");
  await expect(summary).toContainText(fixedTarget);
  await expect(summary).toContainText("80 %");
  await expect(prices).toHaveCount(1);

  await page.locator("#release-action").click();
  await expect(target).toBeEnabled();
  await expect(target).toHaveValue("40");
  await expect(choose).toHaveAttribute("aria-pressed", "true");
  await expect(summary).toContainText(fixedTarget);
  await expect(settings.getByRole("alert")).toContainText(
    english ? "Your draft is preserved" : "Dein Entwurf bleibt erhalten",
  );

  await apply.click();
  await expect(charging.locator(".electricity-charging-editor")).toHaveCount(0);
  await expect(summary).toContainText(method);
  await expect(summary).toContainText("40 %");
  await expect(settings.locator(".tou-charging-threshold")).toHaveCount(0);
  await expect(panel).toHaveAttribute("data-tariff-configure-requests", "2");
  await expect(page.locator("#actions")).toContainText(
    '"charging_method":"all_low_tariffs"',
  );
  await expect(page.locator("#actions")).toContainText(
    '"charging_settings":{"timed_charge_max_soc":40}',
  );
  await expect(prices).toHaveCount(2);
  await expect(prices).toHaveText(
    Array(2).fill(english ? "below standard price" : "unter Standardpreis"),
  );
  const automatic = charging.locator(".electricity-master input");
  await expect(automatic).not.toBeChecked();
  await automatic.click();
  await expect(automatic).toBeChecked();
  await expect(charging.locator(".charge-plan")).toContainText(
    english ? "below the standard price" : "unter dem Standardpreis",
  );
});

for (const type of ["dynamic", "fixed"] as const) {
  test(`all low tariffs is disabled with a ${type} tariff`, async ({
    page,
  }, testInfo) => {
    const english = testInfo.project.name.endsWith("en");
    await page.goto("/sax-power-vue/allgemein");
    if (english) await page.locator("#language").click();
    await page
      .locator(type === "dynamic" ? "#tariff-dynamic" : "#legacy-tariff")
      .click();
    const panel = page.locator("sax-power-vue-panel");
    await panel.locator("nav a[href$='/stromtarif']").click();
    if (type === "dynamic")
      await panel
        .locator(
          ".electricity-charging header .editor-actions > button:first-child",
        )
        .click();
    await expect(
      panel.getByRole("button", {
        name: english ? "In all low-tariff windows" : "In allen Niedrigtarifen",
      }),
    ).toBeDisabled();
    await expect(panel).not.toHaveAttribute("data-tariff-configure-requests");
  });
}
