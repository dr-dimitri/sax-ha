import {
  expect,
  test,
  type Locator,
  type Page,
  type TestInfo,
} from "@playwright/test";

import type { HomeAssistant } from "../src/types";

const pageErrors = new WeakMap<Page, string[]>();

async function capture(page: Page, testInfo: TestInfo, state: string) {
  const path = testInfo.outputPath(`time-of-use-${state}.png`);
  await page.locator("sax-power-vue-panel").screenshot({ path });
  await testInfo.attach(`time-of-use-${state}-${testInfo.project.name}`, {
    path,
    contentType: "image/png",
  });
}

async function expectControlsToFit(container: Locator) {
  expect(
    await container.evaluate((element) => {
      const bounds = element.getBoundingClientRect();
      return {
        overflow: document.documentElement.scrollWidth > innerWidth,
        outside: [...element.querySelectorAll("input, select, button, summary")]
          .filter((control) => {
            const box = control.getBoundingClientRect();
            return box.width > 0 && box.height > 0;
          })
          .filter((control) => {
            const box = control.getBoundingClientRect();
            return box.left < bounds.left - 1 || box.right > bounds.right + 1;
          })
          .map(
            (control) =>
              control.getAttribute("aria-label") ?? control.textContent,
          ),
      };
    }),
  ).toEqual({ overflow: false, outside: [] });
}

test.beforeEach(async ({ page }, testInfo) => {
  const errors: string[] = [];
  pageErrors.set(page, errors);
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/sax-power-vue/allgemein");
  if (testInfo.project.name.endsWith("en"))
    await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
  await page.locator("sax-power-vue-panel nav a[href$='/stromtarif']").click();
});

test.afterEach(({ page }) => {
  expect(pageErrors.get(page)).toEqual([]);
});

// REQ-VUE-ELECTRICITY-TARIFF: setup follows the user's decisions, and
// inspecting prices or settings never implicitly enables grid charging.
test("time-of-use setup presents three decisions before optional price details without mobile overflow", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const steps = panel.locator(
    ".tariff-plan > header h2, .electricity-charging > header h2, .electricity-activation h2",
  );
  await expect(steps).toHaveText(
    english
      ? [
          "1. When is your electricity cheaper?",
          "2. How much should the battery charge?",
          "3. Turn on automatic charging",
        ]
      : [
          "1. Wann ist dein Strom günstig?",
          "2. Wie viel möchtest du laden?",
          "3. Automatik einschalten",
        ],
  );
  const cheapestPeriod = panel
    .locator(".tariff-plan__periods li")
    .filter({ has: page.locator(".tariff-plan__badge") });
  await expect(cheapestPeriod).toHaveCount(1);
  await expect(cheapestPeriod).toContainText("00:00 – 06:00");
  await expect(cheapestPeriod).toContainText(
    english ? "18.00 ct/kWh" : "18,00 ct/kWh",
  );
  const master = panel.locator(".electricity-activation").getByRole("switch");
  await expect(master).not.toBeChecked();
  await expect(panel.locator(".electricity-master input")).toHaveCount(1);
  const details = panel.locator(".electricity-price-details");
  await expect(details).not.toHaveAttribute("open", "");
  await expect(panel.locator(".electricity-price-card svg")).toBeHidden();
  const priceCard = await panel
    .locator(".electricity-price-card")
    .boundingBox();
  const activation = await panel
    .locator(".electricity-activation")
    .boundingBox();
  expect(priceCard!.y).toBeGreaterThanOrEqual(
    activation!.y + activation!.height,
  );
  for (const width of testInfo.project.name.startsWith("mobile")
    ? [390, 320]
    : [1440, 1100]) {
    await page.setViewportSize({ width, height: 1000 });
    await expectControlsToFit(panel);
    await capture(page, testInfo, `overview-${width}`);
  }
  const showPrices = details.locator(":scope > summary");
  await expect(showPrices).toHaveText(
    english ? "Show price chart" : "Preisverlauf anzeigen",
  );
  await showPrices.focus();
  await page.keyboard.press("Enter");
  await expect(details).toHaveAttribute("open", "");
  await expect(panel.locator(".electricity-price-card svg")).toBeVisible();
  await expectControlsToFit(panel);
  await page.keyboard.press("Space");
  await expect(details).not.toHaveAttribute("open", "");
  await expect(master).not.toBeChecked();
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});

// REQ-VUE-ENTITY-BINDING: the activation step preserves the confirmed
// switch state throughout delayed and failed WebSocket responses.
test("activation waits for confirmation and preserves the previous setting on failure", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const activation = panel.locator(".electricity-activation");
  const master = activation.getByRole("switch");
  const status = activation.locator(".electricity-master-status");
  await expect(master).toHaveAccessibleName(
    english ? "Automatic grid charging" : "Automatische Netzladung",
  );
  await page.locator("#hold-action").click();
  await master.focus();
  await page.keyboard.press("Space");
  await expect(master).not.toBeChecked();
  await expect(master).toBeDisabled();
  await expect(activation.locator(".electricity-master")).toHaveAttribute(
    "aria-busy",
    "true",
  );
  await expect(status).toHaveAttribute("role", "status");
  await expect(status).toHaveAttribute("aria-live", "polite");
  await expect(status).toHaveText(
    english ? "Turning on …" : "Einschalten wird übernommen …",
  );
  await page.keyboard.press("Space");
  await expect(panel).toHaveAttribute("data-tariff-configure-requests", "1");
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  await capture(page, testInfo, "activation-pending");
  await page.locator("#release-action").click();
  await expect(master).toBeChecked();
  await expect(master).toBeEnabled();
  await expect(activation.locator(".electricity-master")).toHaveAttribute(
    "aria-busy",
    "false",
  );
  await expect(page.locator("#actions")).toContainText(
    '"automation_enabled":true',
  );
  const confirmedAction = await page.locator("#actions").innerText();
  await page.locator("#hold-action").click();
  await page.locator("#failure").click();
  await master.click();
  await expect(master).toBeChecked();
  await expect(master).toBeDisabled();
  await page.locator("#release-action").click();
  await expect(activation.getByRole("alert")).toBeVisible();
  await expect(master).toHaveAttribute(
    "aria-describedby",
    /electricity-activation-error/,
  );
  await expect(master).toBeChecked();
  await expect(master).toBeEnabled();
  await expect(page.locator("#actions")).toHaveText(confirmedAction);
  await master.click();
  await expect(master).not.toBeChecked();
  await expect(panel.getByRole("alert")).toHaveCount(0);
  await expect(panel).toHaveAttribute("data-tariff-configure-requests", "3");
});

test("charging choices explain their effects and retain the confirmed method while a change is pending or rejected", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const charging = panel.locator(".electricity-charging");
  const settings = charging.locator(".tou-charging-settings");
  const summary = settings.locator(".tou-charging-summary");
  const edit = charging.locator("header > button");
  await expect(summary).toContainText(
    english ? "Fixed charge target" : "Festes Ladeziel",
  );
  await expect(settings.locator(".tou-charging-threshold")).toContainText(
    "20 %",
  );
  await expect(settings.locator(".tou-charging-month-summary")).toContainText(
    english ? "All year" : "Ganzjährig",
  );
  await expect(settings.locator("[data-method]")).toHaveCount(0);
  await edit.focus();
  await page.keyboard.press("Enter");
  const methods = settings.locator(".tou-charging-methods");
  const fixed = methods.locator('[data-method="fixed"]');
  const bridge = methods.locator('[data-method="bridge"]');
  const advanced = settings.locator(".tou-charging-advanced");
  const target = settings.getByRole("spinbutton", {
    name: english ? "Charge target (%)" : "Ladeziel (%)",
    exact: true,
  });
  await expect(methods.locator("strong")).toHaveText(
    english
      ? ["Fixed charge target", "Only what is needed until solar power"]
      : ["Festes Ladeziel", "Nur Bedarf bis Solarstrom"],
  );
  await expect(fixed).toHaveAttribute("aria-pressed", "true");
  await expect(bridge).toHaveAttribute("aria-pressed", "false");
  await expect(advanced).not.toHaveAttribute("open", "");
  await expect(settings.locator("input:visible")).toHaveCount(1);
  await expect(target).toHaveValue("80");
  await expect(settings).toContainText(
    english
      ? "solar power can charge it further"
      : "Solarstrom kann ihn weiter füllen",
  );
  await expect(settings).toContainText(
    english
      ? "When cell calibration is due, charging up to 100% is allowed"
      : "Bei fälliger Zellkalibrierung sind bis 100 % erlaubt",
  );
  await expect(settings).toContainText(
    english
      ? "Each change is applied individually"
      : "Jede Änderung wird einzeln übernommen",
  );
  for (const width of testInfo.project.name.startsWith("mobile")
    ? [390, 320]
    : [1440, 1100]) {
    await page.setViewportSize({ width, height: 1000 });
    await expectControlsToFit(settings);
    for (const method of await methods.getByRole("button").all())
      expect((await method.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    await capture(page, testInfo, `charging-${width}`);
  }
  await page.locator("#hold-action").click();
  await page.locator("#failure").click();
  await bridge.focus();
  await page.keyboard.press("Enter");
  await expect(methods).toHaveAttribute("aria-busy", "true");
  await expect(settings.getByRole("status")).toHaveText(
    english ? "Applying charging method …" : "Ladeweise wird übernommen …",
  );
  await expect(fixed).toBeDisabled();
  await expect(bridge).toBeDisabled();
  await expect(fixed).toHaveAttribute("aria-pressed", "true");
  await expect(bridge).toHaveAttribute("aria-pressed", "false");
  await expect(target).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page.locator("#actions")).toHaveText(
    '1: switch.turn_on {"entity_id":"switch.demo_bridge_charge_enabled"}',
  );
  await charging
    .getByRole("button", { name: english ? "Done" : "Fertig", exact: true })
    .click();
  await expect(methods).toBeHidden();
  await expect(summary).toContainText(
    english ? "Fixed charge target" : "Festes Ladeziel",
  );
  await expect(charging.getByRole("status")).toBeVisible();
  await page.locator("#release-action").click();
  await expect(charging.getByRole("alert")).toBeVisible();
  await edit.click();
  await expect(fixed).toHaveAttribute("aria-pressed", "true");
  await expect(bridge).toHaveAttribute("aria-pressed", "false");
  await expect(bridge).toBeEnabled();
  await bridge.click();
  await expect(bridge).toHaveAttribute("aria-pressed", "true");
  await expect(charging.getByRole("alert")).toHaveCount(0);
  await expect(target).toHaveCount(0);
  await expect(
    settings.getByRole("spinbutton", {
      name: english ? "Charge up to at most (%)" : "Höchstens laden bis (%)",
      exact: true,
    }),
  ).toHaveValue("80");
  await expect(settings).toContainText(
    english
      ? "Missing consumption or forecast data prevents a new charging plan"
      : "Ohne Verbrauchs- oder Prognosedaten wird kein neuer Ladeplan erstellt",
  );
  await expect(settings).toContainText(
    english
      ? "requires a suitable forecast with the expected start of solar power"
      : "benötigst du eine passende PV-Prognose mit dem erwarteten Solarstart",
  );
  await expect(settings).toContainText(
    english ? "Open “Edit” in step 1" : "Öffne in Schritt 1 „Bearbeiten“",
  );
  await advanced.locator(":scope > summary").focus();
  await page.keyboard.press("Space");
  await expect(advanced).toHaveAttribute("open", "");
  await expect(
    settings.getByRole("spinbutton", {
      name: english
        ? "Only start below a battery level of (%)"
        : "Nur starten unter einem Ladestand von (%)",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(
    settings.getByRole("spinbutton", {
      name: english
        ? "Charge limit for all charging methods (%)"
        : "Ladegrenze für alle Lademethoden (%)",
      exact: true,
    }),
  ).toHaveValue("80");
  await expect(settings).toContainText(
    english
      ? "Raising it later does not automatically raise the grid charge target"
      : "Ein späteres Anheben erhöht das Netzladeziel nicht automatisch",
  );
  await expectControlsToFit(settings);
  await fixed.click();
  await expect(target).toHaveValue("80");
  await expect(
    settings.getByRole("spinbutton", {
      name: english
        ? "Only start below a battery level of (%)"
        : "Nur starten unter einem Ladestand von (%)",
      exact: true,
    }),
  ).toHaveValue("20");
  await expect(panel.locator(".electricity-master input")).not.toBeChecked();
});

test("charge target keeps its draft and confirmed value through delayed failure, collapse and retry", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const charging = panel.locator(".electricity-charging");
  await charging.locator("header > button").click();
  const settings = charging.locator(".tou-charging-settings");
  const summary = settings.locator(".tou-charging-summary");
  const target = settings.getByRole("spinbutton", {
    name: english ? "Charge target (%)" : "Ladeziel (%)",
    exact: true,
  });
  const control = settings.locator(".entity-control").filter({
    has: page.getByRole("spinbutton", {
      name: english ? "Charge target (%)" : "Ladeziel (%)",
      exact: true,
    }),
  });
  const apply = control.getByRole("button");
  await target.fill("65");
  await page.locator("#hold-action").click();
  await page.locator("#failure").click();
  await apply.click();
  await expect(target).toBeDisabled();
  await expect(apply).toBeDisabled();
  await expect(control).toHaveAttribute("aria-busy", "true");
  await expect(control.getByRole("status")).toBeVisible();
  await expect(control.locator(".entity-control__value")).toContainText("80 %");
  await expect(summary).toContainText("80 %");
  await charging
    .getByRole("button", { name: english ? "Done" : "Fertig", exact: true })
    .click();
  await expect(charging.getByRole("status")).toBeVisible();
  await page.locator("#release-action").click();
  await expect(charging.getByRole("alert")).toBeVisible();
  await expect(summary).toContainText("80 %");
  await charging.locator("header > button").click();
  await expect(target).toHaveValue("65");
  await expect(control.locator(".entity-control__value")).toContainText("80 %");
  await expect(control).toHaveAttribute("aria-busy", "false");
  await apply.click();
  await expect(control.getByRole("alert")).toHaveCount(0);
  await expect(summary).toContainText("65 %");
  await expect(page.locator("#actions")).toHaveText(
    '2: number.set_value {"value":65,"entity_id":"number.demo_timed_charge_max_soc"}',
  );
  await expect(panel.locator(".electricity-master input")).not.toBeChecked();
});

test("current discharge forecast remains visible independently of automatic charging and hides when measurements are unavailable", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  await page.goto("/sax-power-vue/stromtarif?bridge-plan");
  if (english) await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator(".electricity-plan > summary").click();
  const forecast = panel.locator(".charge-plan__forecast");
  await expect(forecast).toBeVisible();
  await expect(forecast).toContainText(
    english ? "Current discharge forecast" : "Aktuelle Entladeprognose",
  );
  await expect(forecast).toContainText("800 W");
  await expect(forecast).toContainText("03:15");
  await expect(forecast).toContainText(
    english ? "lower charge limit" : "unteren Ladegrenze",
  );
  await expect(forecast).not.toContainText("1000 W");
  await panel.evaluate((element) => {
    const host = element as HTMLElement & { hass: HomeAssistant };
    const id = "sensor.demo_bridge_charge_plan";
    host.hass = {
      ...host.hass,
      states: {
        ...host.hass.states,
        [id]: {
          entity_id: id,
          state: "off",
          attributes: { reason: "disabled" },
        },
      },
    };
  });
  await expect(forecast).toBeVisible();
  await expect(forecast).toContainText("03:15");
  await expect(panel.locator(".charge-plan")).toContainText(
    english ? "planning is turned off" : "Ladeplanung ist ausgeschaltet",
  );
  await expectControlsToFit(panel);
  await capture(page, testInfo, "current-forecast");
  await panel.evaluate((element) => {
    const host = element as HTMLElement & { hass: HomeAssistant };
    const id = "sensor.demo_discharge_forecast";
    host.hass = {
      ...host.hass,
      states: {
        ...host.hass.states,
        [id]: { ...host.hass.states[id]!, state: "unavailable" },
      },
    };
  });
  await expect(forecast).toHaveCount(0);
  await expect(panel.locator(".charge-plan")).not.toContainText("03:15");
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});
