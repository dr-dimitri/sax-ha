import { expect, test, type Locator, type Page } from "@playwright/test";
import type { HomeAssistant } from "../src/types";

async function prepare(
  page: Page,
  type: "time_of_use" | "dynamic",
  english: boolean,
) {
  await page.goto("/sax-power-vue/allgemein");
  if (english) await page.locator("#language").click();
  if (type === "dynamic") await page.locator("#tariff-dynamic").click();
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href$='/stromtarif']").click();
  const charging = panel.locator(".electricity-charging");
  await charging.locator("header .editor-actions > button:first-child").click();
  await charging
    .locator('[data-method="fixed_time"], [data-strategy="fixed_time"]')
    .click();
  return {
    panel,
    charging,
    input: charging.getByRole("textbox", {
      name: english ? "Daily charging start" : "Täglicher Ladestart",
    }),
    apply: charging
      .locator(".electricity-charging-editor .electricity-actions button")
      .first(),
  };
}
async function typeTime(input: Locator, value: string) {
  await input.fill("");
  await input.pressSequentially(value);
  await input.press("Tab");
}
for (const type of ["time_of_use", "dynamic"] as const) {
  test(`${type}: fixed daily start rejects incomplete keyboard input and saves midnight explicitly`, async ({
    page,
  }, testInfo) => {
    const english = testInfo.project.name.endsWith("en");
    const { panel, charging, input, apply } = await prepare(
      page,
      type,
      english,
    );
    if (testInfo.project.name.includes("dark"))
      await page.locator("#theme").click();
    const heading = charging.locator(".charge-plan h2");
    const expected = (time: string) =>
      english
        ? `Charging plan: Grid charging starts at ${time}`
        : `Ladeplanung: Netzladen startet ab ${time} Uhr`;
    await expect(input).toHaveValue("02:00");
    await expect(panel).not.toHaveAttribute("data-tariff-configure-requests");
    await expect(charging.locator(".month-selection")).toBeVisible();
    await expect(charging.getByRole("spinbutton")).toHaveCount(2);
    await typeTime(input, "02");
    await apply.click();
    await expect(input).toHaveAttribute("aria-invalid", "true");
    await expect(input).toHaveValue("02");
    await expect(input).toBeFocused();
    await expect(charging.getByRole("alert")).toContainText(
      english ? "complete time" : "vollständige Uhrzeit",
    );
    await expect(panel).not.toHaveAttribute("data-tariff-configure-requests");
    await typeTime(input, "00:00");
    await apply.click();
    await expect(charging.locator(".electricity-charging-editor")).toHaveCount(
      0,
    );
    await expect(
      charging.locator(".fixed-time-charging-summary"),
    ).toContainText("00:00");
    await expect(heading).toHaveText(expected("00:00"));
    await expect(
      heading.locator(".charge-plan__demand--fixed-time"),
    ).toBeVisible();
    const colors = await heading.locator("span").evaluate((element) => {
      const context = document.createElement("canvas").getContext("2d")!;
      context.fillStyle = getComputedStyle(element).color;
      context.fillRect(0, 0, 1, 1);
      return {
        rgb: [...context.getImageData(0, 0, 1, 1).data],
        suffix: getComputedStyle(element).color,
        heading: getComputedStyle(element.parentElement!).color,
      };
    });
    expect(colors.rgb[2]).toBeGreaterThan(colors.rgb[0]!);
    expect(colors.rgb[2]).toBeGreaterThan(colors.rgb[1]!);
    expect(colors.suffix).not.toBe(colors.heading);
    await expect(charging.locator(".charge-plan p")).toHaveCount(0);
    await expect(
      charging.locator(".electricity-charge-status"),
    ).not.toContainText("Warte auf Preisfenster");
    await expect(panel).toHaveAttribute("data-tariff-configure-requests", "1");
    await expect(page.locator("#actions")).toContainText(
      '"fixed_time_charging":{"enabled":true,"start":"00:00"}',
    );
    await charging
      .locator("header .editor-actions > button:first-child")
      .click();
    await expect(input).toHaveValue("00:00");
    await typeTime(input, "23:45");
    await expect(heading).toHaveText(expected("00:00"));
    const path = testInfo.outputPath(
      `fixed-time-${type}-${testInfo.project.name}.png`,
    );
    await panel.screenshot({ path });
    await testInfo.attach("fixed-time-editor", {
      path,
      contentType: "image/png",
    });
    if (
      !english &&
      ["desktop-light-de", "mobile-light-de"].includes(testInfo.project.name)
    )
      await page.screenshot({
        path: `/tmp/sax-fixed-time-${type}-${testInfo.project.name}.png`,
        fullPage: true,
      });
    await apply.click();
    await expect(
      charging.locator(".fixed-time-charging-summary"),
    ).toContainText("23:45");
    await expect(heading).toHaveText(expected("23:45"));
    await expect(panel).toHaveAttribute("data-tariff-configure-requests", "2");
    if (testInfo.project.name === "desktop-light-de")
      await charging.screenshot({ path: `/tmp/sax-startzeit-${type}.png` });
  });
  test(`${type}: first activation saves time and a target below the old SOC start threshold together`, async ({
    page,
  }, testInfo) => {
    const english = testInfo.project.name.endsWith("en");
    const { panel, charging, input, apply } = await prepare(
      page,
      type,
      english,
    );
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
    await typeTime(input, "01:30");
    const target = charging.getByRole("spinbutton", {
      name: english ? "Grid charge target (%)" : "Netzladeziel (%)",
      exact: true,
    });
    await target.fill("40");
    await target.press("Tab");
    await apply.click();
    await expect(charging.locator(".electricity-charging-editor")).toHaveCount(
      0,
    );
    await expect(
      charging.locator(".fixed-time-charging-summary"),
    ).toContainText("01:30");
    await expect(
      charging.locator(".dynamic-charging-summary, .tou-charging-summary"),
    ).toContainText("40 %");
    await expect(page.locator("#actions")).toContainText(
      '"charging_settings":{"timed_charge_max_soc":40}',
    );
    await expect(page.locator("#actions")).toContainText(
      '"fixed_time_charging":{"enabled":true,"start":"01:30"}',
    );
    await expect(panel).toHaveAttribute("data-tariff-configure-requests", "1");
    if (type === "time_of_use") {
      await expect(panel.locator(".tariff-plan__impact")).toContainText(
        english
          ? "regardless of the electricity price"
          : "unabhängig vom Strompreis",
      );
      await expect(panel.locator(".tariff-plan__period-status")).toHaveCount(0);
    }
  });
  test(`${type}: delayed and failed saves preserve the confirmed time, prevent duplicates and switch methods atomically`, async ({
    page,
  }, testInfo) => {
    const english = testInfo.project.name.endsWith("en");
    const { panel, charging, input, apply } = await prepare(
      page,
      type,
      english,
    );
    await apply.click();
    await expect(
      charging.locator(".fixed-time-charging-summary"),
    ).toContainText("02:00");
    const heading = charging.locator(".charge-plan h2");
    const confirmedHeading = english
      ? "Charging plan: Grid charging starts at 02:00"
      : "Ladeplanung: Netzladen startet ab 02:00 Uhr";
    await expect(heading).toHaveText(confirmedHeading);
    await charging
      .locator("header .editor-actions > button:first-child")
      .click();
    await typeTime(input, "03:15");
    await page.locator("#hold-action").click();
    await page.locator("#failure").click();
    await apply.click();
    await expect(input).toBeDisabled();
    await expect(apply).toBeDisabled();
    await expect(heading).toHaveText(confirmedHeading);
    await expect(
      charging.locator(".fixed-time-charging-summary"),
    ).toContainText("02:00");
    await expect(panel).toHaveAttribute("data-tariff-configure-requests", "2");
    await expect(charging.getByRole("status").first()).toContainText(
      english ? "Applying charging method" : "Ladeweise wird übernommen",
    );
    await page.locator("#release-action").click();
    await expect(input).toBeEnabled();
    await expect(input).toHaveValue("03:15");
    await expect(charging.getByRole("alert")).toContainText(
      english ? "draft is preserved" : "Entwurf bleibt erhalten",
    );
    await expect(heading).toHaveText(confirmedHeading);
    await expect(
      charging.locator(".fixed-time-charging-summary"),
    ).toContainText("02:00");
    const method = type === "dynamic" ? "relative" : "fixed";
    await charging
      .locator(`[data-strategy="${method}"], [data-method="${method}"]`)
      .click();
    await expect(
      charging.locator(
        `[data-strategy="${method}"], [data-method="${method}"]`,
      ),
    ).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator("#actions")).toContainText(
      `"charging_method":"${method}"`,
    );
    await expect(panel).toHaveAttribute("data-tariff-configure-requests", "3");
    await expect(
      charging.locator(".charge-plan__demand--fixed-time"),
    ).toHaveCount(0);
  });
}
