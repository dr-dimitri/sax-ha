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

test("discharge diagnostics follow HA feedback and recover without editing settings", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const feedback = panel.locator(".electricity-charge-status");
  const value = feedback.locator(".entity-value__state");
  await expect(feedback.locator(".entity-value__name")).toHaveText(
    english ? "Discharge status" : "Entladestatus",
  );
  async function update(state: string) {
    await panel.evaluate((element, state) => {
      const host = element as HTMLElement & { hass: HomeAssistant };
      const id = "sensor.demo_timed_charge_discharge_status";
      host.hass = {
        ...host.hass,
        states: {
          ...host.hass.states,
          [id]: { ...host.hass.states[id]!, state },
        },
      };
    }, state);
  }
  await update("unknown");
  await expect(value).toHaveText(english ? "Unknown" : "Unbekannt");
  for (const [state, de, en] of [
    [
      "control_mode_failed",
      "Steuermodus konnte nicht gesetzt werden",
      "Control mode could not be set",
    ],
    [
      "setpoint_failed",
      "Ladeleistung konnte nicht gesetzt werden",
      "Charging power could not be set",
    ],
    [
      "reset_failed",
      "SmartMeter-Nullregelung konnte nicht aktiviert werden",
      "Smart meter zero regulation could not be enabled",
    ],
    [
      "control_failed",
      "Ladefreigabe fehlt oder wurde widerrufen",
      "Charging permission is missing or was revoked",
    ],
    [
      "control_data_missing",
      "Gerätedaten für Ladeauftrag fehlen oder sind ungültig",
      "Device data for charging is missing or invalid",
    ],
    [
      "device_feedback_missing",
      "Geräterückmeldung fehlt",
      "Device feedback missing",
    ],
    [
      "discharge_hold_unconfirmed",
      "Entladesperre nicht bestätigt",
      "Discharge block not confirmed",
    ],
    [
      "release_unconfirmed",
      "Entladefreigabe nicht bestätigt",
      "Discharge release not confirmed",
    ],
  ] as const) {
    await update(state);
    await expect(value).toHaveText(english ? en : de);
    await expect(value).toBeVisible();
    await expectControlsToFit(panel);
    await update("normal");
    await expect(value).toHaveText(
      english ? "Normal operation" : "Normalbetrieb",
    );
    await update("grid_charging");
    await expect(value).toHaveText(english ? "Grid charging" : "Netzladen");
  }
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});

// REQ-VUE-ELECTRICITY-TARIFF: the overview groups prices and charging, and
// inspecting prices or settings never implicitly enables grid charging.
test("time-of-use groups prices and grid charging into compact responsive cards", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const steps = panel.locator(
    ".tariff-plan > header h2, .electricity-charging > header h2, .electricity-activation h2",
  );
  await expect(steps).toHaveText(
    english
      ? ["Prices & times", "Grid charging"]
      : ["Preise & Zeiten", "Netzladung"],
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
  await expect(
    panel.locator(".electricity-price-card .tariff-plan"),
  ).toHaveCount(1);
  await expect(
    panel.locator(".electricity-charging .electricity-activation"),
  ).toHaveCount(1);
  await expect(
    panel.locator(".electricity-charging .electricity-plan"),
  ).toHaveCount(1);
  const socValues = panel.locator(
    ".tou-charging-soc-row > .electricity-target",
  );
  await expect(socValues.locator("span")).toHaveText(
    english
      ? ["Start only below", "Grid charge target", "Max SOC"]
      : ["Start nur unter", "Netzladeziel", "Max SOC"],
  );
  for (const width of testInfo.project.name.startsWith("mobile")
    ? [390, 320]
    : [1440, 1100]) {
    await page.setViewportSize({ width, height: 1000 });
    const pricesBox = (await panel
      .locator(".electricity-price-card")
      .boundingBox())!;
    const chargingBox = (await panel
      .locator(".electricity-charging")
      .boundingBox())!;
    if (width >= 1100) {
      expect(Math.abs(pricesBox.y - chargingBox.y)).toBeLessThan(2);
      expect(chargingBox.x).toBeGreaterThanOrEqual(
        pricesBox.x + pricesBox.width,
      );
      expect(Math.max(pricesBox.height, chargingBox.height)).toBeLessThan(760);
    } else {
      expect(chargingBox.y).toBeGreaterThanOrEqual(
        pricesBox.y + pricesBox.height,
      );
    }
    const socBounds = await socValues.evaluateAll((values) =>
      values.map((value) => {
        const box = value.getBoundingClientRect();
        const label = value.querySelector("span")!.getBoundingClientRect();
        const number = value.querySelector("strong")!.getBoundingClientRect();
        return {
          x: box.x,
          y: box.y,
          width: box.width,
          labelBottom: label.bottom,
          numberTop: number.top,
        };
      }),
    );
    for (const value of socBounds)
      expect(value.labelBottom).toBeLessThanOrEqual(value.numberTop);
    for (let index = 1; index < socBounds.length; index++) {
      expect(Math.abs(socBounds[index]!.y - socBounds[0]!.y)).toBeLessThan(2);
      expect(
        Math.abs(socBounds[index]!.numberTop - socBounds[0]!.numberTop),
      ).toBeLessThan(2);
      expect(socBounds[index]!.x).toBeGreaterThanOrEqual(
        socBounds[index - 1]!.x + socBounds[index - 1]!.width,
      );
    }
    await expectControlsToFit(panel);
    await capture(page, testInfo, `overview-${width}`);
  }
  const showPrices = details.locator(":scope > summary");
  await expect(showPrices).toHaveText(english ? "Price chart" : "Preisverlauf");
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
    english ? "Fixed grid charge target" : "Festes Netzladeziel",
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
  const target = settings.getByRole("spinbutton", {
    name: english ? "Grid charge target (%)" : "Netzladeziel (%)",
    exact: true,
  });
  await expect(methods.locator("strong")).toHaveText(
    english
      ? ["Fixed grid charge target", "Only what is needed until solar power"]
      : ["Festes Netzladeziel", "Nur Bedarf bis Solarstrom"],
  );
  await expect(fixed).toHaveAttribute("aria-pressed", "true");
  await expect(bridge).toHaveAttribute("aria-pressed", "false");
  await expect(settings.locator("details")).toHaveCount(0);
  await expect(settings.getByRole("spinbutton")).toHaveCount(3);
  await expect(settings.getByRole("switch")).toHaveCount(12);
  for (const input of await settings.locator("input").all())
    await expect(input).toBeVisible();
  await expect(methods.locator("span")).toHaveCount(0);
  await expect(target).toHaveValue("80");
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
  await charging.locator("header > button").click();
  await expect(methods).toBeHidden();
  await expect(summary).toContainText(
    english ? "Fixed grid charge target" : "Festes Netzladeziel",
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
      name: english
        ? "Maximum grid charge target (%)"
        : "Maximales Netzladeziel (%)",
      exact: true,
    }),
  ).toHaveValue("80");
  await expect(settings).toContainText(
    english ? "Solar forecast missing" : "PV-Prognose fehlt",
  );
  await expect(
    settings.getByRole("spinbutton", {
      name: english ? "Start threshold (%)" : "Ladestart unter (%)",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(
    settings.getByRole("spinbutton", {
      name: "Max SOC (%)",
      exact: true,
    }),
  ).toHaveValue("80");
  await expectControlsToFit(settings);
  await fixed.click();
  await expect(target).toHaveValue("80");
  await expect(
    settings.getByRole("spinbutton", {
      name: english ? "Start threshold (%)" : "Ladestart unter (%)",
      exact: true,
    }),
  ).toHaveValue("20");
  await expect(panel.locator(".electricity-master input")).not.toBeChecked();
});

test("charge target keeps its draft and confirmed value through delayed failure and retry, disabling cancellation", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const charging = panel.locator(".electricity-charging");
  await charging.locator("header > button").click();
  const settings = charging.locator(".tou-charging-settings");
  const summary = settings.locator(".tou-charging-summary");
  const target = settings.getByRole("spinbutton", {
    name: english ? "Grid charge target (%)" : "Netzladeziel (%)",
    exact: true,
  });
  const control = settings.locator(".entity-control").filter({
    has: page.getByRole("spinbutton", {
      name: english ? "Grid charge target (%)" : "Netzladeziel (%)",
      exact: true,
    }),
  });
  const apply = charging.locator("header > button");
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
  await expect(
    charging.locator(".electricity-charging-editor button"),
  ).toBeDisabled();
  await expect(charging.locator(".electricity-charging-editor")).toBeVisible();
  await page.locator("#release-action").click();
  await expect(control.getByRole("alert")).toBeVisible();
  await expect(summary).toContainText("80 %");
  await expect(target).toHaveValue("65");
  await expect(control.locator(".entity-control__value")).toContainText("80 %");
  await expect(control).toHaveAttribute("aria-busy", "false");
  await apply.click();
  await expect(charging.locator(".electricity-charging-editor")).toHaveCount(0);
  await charging.locator("header > button").click();
  await expect(control.getByRole("alert")).toHaveCount(0);
  await expect(summary).toContainText("65 %");
  await expect(page.locator("#actions")).toHaveText(
    '2: sax_power.set_charging_settings {"device_id":"demo-device","timed_charge_max_soc":65}',
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
