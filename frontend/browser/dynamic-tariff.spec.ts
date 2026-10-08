import { expect, test, type Page, type TestInfo } from "@playwright/test";

import type { HomeAssistant } from "../src/types";

const pageErrors = new WeakMap<Page, string[]>();

async function prepareMasterTariff(
  page: Page,
  tariff: "time_of_use" | "dynamic",
  enabled: boolean,
  english: boolean,
) {
  const panel = page.locator("sax-power-vue-panel");
  const master = panel.locator(".electricity-master input");
  const mode = tariff === "dynamic" ? "dynamic" : "timed";
  const tariffName =
    tariff === "dynamic"
      ? english
        ? "Dynamic"
        : "Dynamisch"
      : english
        ? "Time of use"
        : "Zeitvariabel";
  await panel.locator("nav a[href$='/allgemein']").click();
  await page.locator(`#tariff-${mode}`).click();
  if (!enabled) await page.locator("#tariff-off").click();
  await panel.locator("nav a[href$='/stromtarif']").click();
  await expect(panel.locator(".electricity-active strong")).toHaveText(
    tariffName,
  );
  await expect(master).toBeChecked({ checked: enabled });
  return { panel, master, mode, tariffName };
}

async function screenshot(page: Page, testInfo: TestInfo, name: string) {
  const path = testInfo.outputPath(`${name}.png`);
  await page.screenshot({ path, fullPage: true });
  await testInfo.attach(name, { path, contentType: "image/png" });
  if (
    name.startsWith("dynamic-overview") ||
    name.startsWith("dynamic-guided")
  ) {
    const panelPath = testInfo.outputPath(`${name}-panel.png`);
    await page.locator("sax-power-vue-panel").screenshot({ path: panelPath });
    await testInfo.attach(`${name}-panel`, {
      path: panelPath,
      contentType: "image/png",
    });
  }
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
  await page.locator("#tariff-dynamic").click();
  await page.locator("sax-power-vue-panel nav a[href$='/stromtarif']").click();
  await expect(
    page.locator("sax-power-vue-panel .electricity-active strong"),
  ).toHaveText(testInfo.project.name.endsWith("en") ? "Dynamic" : "Dynamisch");
});

test.afterEach(({ page }) => {
  expect(pageErrors.get(page)).toEqual([]);
});

// REQ-VUE-ELECTRICITY-TARIFF: a slow HA response must have immediate feedback,
// preserve the confirmed switch state, and prevent duplicate writes.
test("automatic grid charging acknowledges clicks immediately while HA confirms later", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const master = panel.locator(".electricity-master input");
  const target = panel.locator(".electricity-master");
  const status = panel.locator(".electricity-master-status");
  const actions = page.locator("#actions");
  await panel.locator(".electricity-price-details > summary").click();
  await expect(master).toHaveAccessibleName(
    english ? "Automatic grid charging" : "Automatische Netzladung",
  );
  await expect(master).toBeChecked();
  await expect(status).toHaveAttribute("role", "status");
  await expect(status).toHaveAttribute("aria-live", "polite");
  for (const [index, desired] of [false, true].entries()) {
    const previousAction = await actions.innerText();
    await page.locator("#hold-action").click();
    await master.click({ clickCount: 2 });
    await expect(master).toBeChecked({ checked: !desired });
    await expect(master).toBeDisabled();
    await expect(target).toHaveAttribute("aria-busy", "true");
    await expect(status).toHaveText(
      english
        ? desired
          ? "Turning on …"
          : "Turning off …"
        : desired
          ? "Einschalten wird übernommen …"
          : "Ausschalten wird übernommen …",
    );
    await expect(panel).toHaveAttribute(
      "data-tariff-configure-requests",
      String(index + 1),
    );
    await expect(actions).toHaveText(previousAction);
    // Read-only navigation remains usable during the delayed write.
    await panel
      .getByRole("button", {
        name: english ? "Tomorrow" : "Morgen",
        exact: true,
      })
      .click();
    await expect(panel.locator(".electricity-day")).toContainText(
      english ? "Tomorrow" : "Morgen",
    );
    await expect(master).toBeChecked({ checked: !desired });
    if (index === 0) {
      await master.scrollIntoViewIfNeeded();
      await screenshot(
        page,
        testInfo,
        `dynamic-master-pending-${testInfo.project.name}`,
      );
    }
    await page.locator("#release-action").click();
    await expect(master).toBeChecked({ checked: desired });
    await expect(master).toBeEnabled();
    await expect(target).toHaveAttribute("aria-busy", "false");
    await expect(status).not.toContainText(english ? "Turning" : "übernommen");
    await expect(actions).toContainText(`"automation_enabled":${desired}`);
    await expect(panel).toHaveAttribute(
      "data-tariff-configure-requests",
      String(index + 1),
    );
  }
  const confirmedAction = await actions.innerText();
  await page.locator("#hold-action").click();
  await page.locator("#failure").click();
  await master.click();
  await expect(master).toBeChecked();
  await expect(master).toBeDisabled();
  await page.locator("#release-action").click();
  await expect(
    panel.locator(".electricity-activation [role='alert']"),
  ).toBeVisible();
  await expect(master).toBeChecked();
  await expect(master).toBeEnabled();
  await expect(target).toHaveAttribute("aria-busy", "false");
  await expect(status).not.toContainText(english ? "Turning" : "übernommen");
  await expect(actions).toHaveText(confirmedAction);
  await master.click();
  await expect(master).not.toBeChecked();
  await expect(
    panel.locator(".electricity-activation [role='alert']"),
  ).toHaveCount(0);
  await expect(panel).toHaveAttribute("data-tariff-configure-requests", "4");
});

// REQ-VUE-ELECTRICITY-TARIFF: native HA changes must reach the master switch
// before the periodic profile refresh, so its next click uses the current state.
for (const tariff of ["time_of_use", "dynamic"] as const) {
  for (const externalEnabled of [false, true]) {
    test(`${tariff} master follows external ${externalEnabled ? "off-to-on" : "on-to-off"} changes and sends the inverse on its next click`, async ({
      page,
    }, testInfo) => {
      const { panel, master, mode, tariffName } = await prepareMasterTariff(
        page,
        tariff,
        !externalEnabled,
        testInfo.project.name.endsWith("en"),
      );
      const confirmedAction = await page.locator("#actions").innerText();

      await page
        .locator(externalEnabled ? `#tariff-${mode}` : "#tariff-off")
        .click();
      await expect(master).toBeChecked({
        checked: externalEnabled,
        timeout: 2_000,
      });
      await expect(master).toBeEnabled();
      await expect(panel.locator(".electricity-active strong")).toHaveText(
        tariffName,
      );
      await expect(page.locator("#actions")).toHaveText(confirmedAction);

      await master.click();
      await expect(panel).toHaveAttribute(
        "data-tariff-configure-requests",
        "1",
      );
      await expect(page.locator("#actions")).toContainText(
        `"automation_enabled":${!externalEnabled}`,
      );
      await expect(page.locator("#actions")).toContainText(
        `"tariff_type":"${tariff}"`,
      );
      await expect(master).toBeChecked({ checked: !externalEnabled });
      await expect(master).toBeEnabled();
    });

    // REQ-VUE-ENTITY-BINDING: external HA updates can arrive after the backend
    // accepted a write but before its older WebSocket acknowledgement returns;
    // the confirming read also needs pending feedback and duplicate prevention.
    test(`${tariff} master preserves newer external ${externalEnabled ? "on" : "off"} state across a delayed write acknowledgement`, async ({
      page,
    }, testInfo) => {
      const { panel, master, mode } = await prepareMasterTariff(
        page,
        tariff,
        externalEnabled,
        testInfo.project.name.endsWith("en"),
      );
      await panel.evaluate((element) => {
        const host = element as HTMLElement & {
          hass: HomeAssistant;
          releaseTariffConfirmation?: () => void;
          releaseTariffRefresh?: () => void;
        };
        const original = host.hass.callWS!;
        let holdTariffRefresh = false;
        host.hass = {
          ...host.hass,
          callWS: async <T>(
            request: Readonly<Record<string, unknown>>,
          ): Promise<T> => {
            const response = await original<T>(request);
            if (request.type === "sax_power/dashboard/tariff/configure") {
              await new Promise<void>((resolve) => {
                host.releaseTariffConfirmation = resolve;
                host.dataset.heldTariffConfirmation = "true";
              });
              holdTariffRefresh = true;
            } else if (
              request.type === "sax_power/dashboard/tariff/get" &&
              holdTariffRefresh
            ) {
              holdTariffRefresh = false;
              await new Promise<void>((resolve) => {
                host.releaseTariffRefresh = resolve;
                host.dataset.heldTariffRefresh = "true";
              });
            }
            return response;
          },
        };
      });

      await master.click();
      await expect(panel).toHaveAttribute(
        "data-held-tariff-confirmation",
        "true",
      );
      await expect(master).toBeDisabled();
      await expect(page.locator("#actions")).toContainText(
        `"automation_enabled":${!externalEnabled}`,
      );
      await page
        .locator(externalEnabled ? `#tariff-${mode}` : "#tariff-off")
        .click();
      await panel.evaluate((element) => {
        const host = element as HTMLElement & {
          releaseTariffConfirmation?: () => void;
        };
        host.releaseTariffConfirmation!();
        delete host.releaseTariffConfirmation;
      });

      await expect(panel).toHaveAttribute("data-held-tariff-refresh", "true");
      await expect(master).toBeDisabled();
      await expect(panel.locator(".electricity-master")).toHaveAttribute(
        "aria-busy",
        "true",
      );
      await master.click({ force: true });
      await expect(panel).toHaveAttribute(
        "data-tariff-configure-requests",
        "1",
      );
      await panel.evaluate((element) => {
        const host = element as HTMLElement & {
          releaseTariffRefresh?: () => void;
        };
        host.releaseTariffRefresh!();
        delete host.releaseTariffRefresh;
      });

      await expect(master).toBeEnabled();
      await expect(master).toBeChecked({
        checked: externalEnabled,
        timeout: 2_000,
      });
      await expect(panel).toHaveAttribute(
        "data-tariff-configure-requests",
        "1",
      );
      await master.click();
      await expect(panel).toHaveAttribute(
        "data-tariff-configure-requests",
        "2",
      );
      await expect(page.locator("#actions")).toContainText(
        `"automation_enabled":${!externalEnabled}`,
      );
      await expect(master).toBeChecked({ checked: !externalEnabled });
      await expect(master).toBeEnabled();
    });
  }
}

// REQ-VUE-ELECTRICITY-TARIFF: understandable choices expose only relevant
// parameters, and both the selected method and saved values belong to HA.
test("guided charging methods explain their effects and reveal relevant settings after confirmation", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const charging = panel.locator(".electricity-charging");
  const settings = charging.locator(".dynamic-charging-settings");
  const methods = settings.locator("[data-strategy]");
  const summary = settings.locator(".dynamic-charging-summary");
  const absolute = settings.locator('[data-strategy="absolute"]');
  const relative = settings.locator('[data-strategy="relative"]');
  const smart = settings.locator('[data-strategy="smart"]');
  const off = settings.locator('[data-strategy="off"]');
  const price = settings.getByRole("spinbutton", {
    name: english
      ? "Maximum price for charging (ct/kWh)"
      : "Höchster Preis zum Laden (ct/kWh)",
    exact: true,
  });
  const hoursName = english
    ? "Maximum charging time per 24 hours"
    : "Maximale Ladezeit je 24 Stunden";
  const hours = settings.getByRole("spinbutton", {
    name: hoursName,
    exact: true,
  });
  const target = settings.getByRole("spinbutton", {
    name: english ? "Charge target (%)" : "Ladeziel (%)",
    exact: true,
  });
  await expect(summary).toContainText(
    english ? "Charge below a fixed price" : "Bis zu einem festen Preis laden",
  );
  await expect(methods).toHaveCount(0);
  await screenshot(page, testInfo, `dynamic-overview-${testInfo.project.name}`);
  await charging.locator("header > button").click();
  await expect(methods).toHaveCount(4);
  await expect(methods.locator("strong")).toHaveText(
    english
      ? [
          "Charge what is needed",
          "Use the cheapest hours",
          "Charge below a fixed price",
          "No automatic charging",
        ]
      : [
          "Bedarfsgerecht laden",
          "Günstigste Stunden nutzen",
          "Bis zu einem festen Preis laden",
          "Keine automatische Ladung",
        ],
  );
  await expect(absolute).toHaveAttribute("aria-pressed", "true");
  await expect(price).toHaveValue("-5");
  await expect(hours).toHaveCount(0);
  await expect(target).toHaveValue("80");
  await expect(settings).toContainText(
    english ? "including solar charging" : "auch für PV-Ladung",
  );
  await expect(
    settings.locator(".dynamic-charging-advanced"),
  ).not.toHaveAttribute("open", "");
  await page.locator("#hold-action").click();
  await relative.click({ clickCount: 2 });
  await expect(settings.locator(".dynamic-charging-methods")).toHaveAttribute(
    "aria-busy",
    "true",
  );
  await expect(settings.getByRole("status")).toHaveText(
    english ? "Applying charging method …" : "Ladeweise wird übernommen …",
  );
  for (const method of await methods.all()) await expect(method).toBeDisabled();
  await expect(absolute).toHaveAttribute("aria-pressed", "true");
  await expect(relative).toHaveAttribute("aria-pressed", "false");
  await expect(price).toBeVisible();
  await expect(hours).toHaveCount(0);
  await expect(page.locator("#actions")).toHaveText(
    '1: select.select_option {"option":"relative","entity_id":"select.demo_price_charge_strategy"}',
  );
  await charging
    .getByRole("button", {
      name: english ? "Done" : "Fertig",
      exact: true,
    })
    .click();
  await expect(settings.locator(".dynamic-charging-methods")).toBeHidden();
  await expect(settings.getByRole("status")).toHaveText(
    english ? "Applying charging method …" : "Ladeweise wird übernommen …",
  );
  await page.locator("#release-action").click();
  await expect(summary).toContainText(
    english ? "Use the cheapest hours" : "Günstigste Stunden nutzen",
  );
  await charging.locator("header > button").click();
  await expect(relative).toHaveAttribute("aria-pressed", "true");
  await expect(absolute).toHaveAttribute("aria-pressed", "false");
  await expect(price).toHaveCount(0);
  await expect(hours).toHaveValue("4");
  await expect(settings).toContainText(
    english ? "There is no fixed price cap" : "Es gilt keine feste Preisgrenze",
  );
  await expect(settings).toContainText(
    english ? "not at midnight" : "nicht um Mitternacht",
  );
  const hoursControl = settings.locator(".entity-control").filter({
    has: page.getByRole("spinbutton", { name: hoursName, exact: true }),
  });
  await hours.fill("6");
  await page.locator("#hold-action").click();
  await hoursControl.getByRole("button").click();
  await expect(hoursControl.locator(".entity-control__value")).toContainText(
    "4",
  );
  await expect(hours).toBeDisabled();
  await expect(summary).toContainText("4 h");
  await page.locator("#release-action").click();
  await expect(hoursControl.locator(".entity-control__value")).toContainText(
    "6",
  );
  await expect(summary).toContainText("6 h");
  await smart.click();
  await expect(smart).toHaveAttribute("aria-pressed", "true");
  await expect(hours).toHaveValue("6");
  await expect(settings).toContainText(
    english ? "Without a solar forecast" : "Ohne PV-Prognose",
  );
  await expect(settings).toContainText(
    english
      ? "If battery level, capacity or charging power is missing"
      : "Fehlen Ladestand, Kapazität oder Ladeleistung",
  );
  const widths = testInfo.project.name.startsWith("mobile")
    ? [390, 320]
    : [1440, 1100];
  for (const width of widths) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    const controlsFit = await settings
      .locator("button:visible, input:visible")
      .evaluateAll((elements) =>
        elements.every((element) => {
          const box = element.getBoundingClientRect();
          const bounds = element
            .closest(".electricity-charging")!
            .getBoundingClientRect();
          return (
            box.height >= 44 &&
            box.left >= bounds.left &&
            box.right <= bounds.right
          );
        }),
      );
    expect(controlsFit).toBe(true);
    await screenshot(
      page,
      testInfo,
      `dynamic-guided-${width}-${testInfo.project.name}`,
    );
  }
  await off.click();
  await expect(off).toHaveAttribute("aria-pressed", "true");
  await expect(settings.locator("input")).toHaveCount(0);
  await expect(settings).toContainText(
    english
      ? "even when the main switch is on"
      : "auch wenn der Hauptschalter eingeschaltet ist",
  );
  await expect(panel.locator(".electricity-master input")).toBeChecked();
  await absolute.click();
  await expect(price).toHaveValue("-5");
  await expect(target).toHaveValue("80");
  await settings.locator(".dynamic-charging-advanced summary").click();
  await expect(settings).toContainText(
    english ? "the house uses grid energy" : "das Haus nutzt Netzstrom",
  );
  await expect(
    settings.getByRole("spinbutton", {
      name: english
        ? "Preserve battery energy below (ct/kWh)"
        : "Speicher bei günstigem Strom schonen bis (ct/kWh)",
      exact: true,
    }),
  ).toHaveValue("-5");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

// REQ-VUE-ELECTRICITY-TARIFF: advanced source values stay intact when a novice
// changes only the feed-in price, including when HA takes time to save it.
test("dynamic prices keep advanced values and show progress while saving and changing tariff", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  const prices = panel.locator(".electricity-prices");
  const before = prices.locator(".electricity-price-summary");
  await prices.locator("header > button").click();
  const form = prices.locator(".electricity-price-editor");
  const advanced = prices.locator(".electricity-price-advanced");
  const feed = prices.locator('[name="dynamic_feed"]');
  const factor = prices.locator('[name="dynamic_pv_factor"]');
  const source = prices.locator(".sensor-picker select").first();
  await expect(source).toBeFocused();
  await expect(source).toHaveValue("sensor.demo_dynamic_price");
  await expect(factor).toBeHidden();
  await expect(advanced).not.toHaveAttribute("open", "");
  await expect(
    prices.locator(".electricity-additional-settings"),
  ).toContainText("70");
  await expect(prices).toContainText(
    english ? "not as a charging price cap" : "nicht als Ladepreisgrenze",
  );
  await feed.fill(english ? "9.25" : "9,25");
  const widths = testInfo.project.name.startsWith("mobile")
    ? [390, 320]
    : [1440, 1100];
  for (const width of widths) {
    await page.setViewportSize({ width, height: 1000 });
    await advanced.locator("summary").click();
    await expect(factor).toHaveValue("70");
    await expect(advanced.locator("select")).toHaveValue("ct_kwh");
    const fieldsFit = await form.locator("input,select").evaluateAll((fields) =>
      fields.every((field) => {
        const box = field.getBoundingClientRect();
        const bounds = field
          .closest(".electricity-prices")!
          .getBoundingClientRect();
        return (
          box.width >= 150 &&
          box.height >= 44 &&
          box.left >= bounds.left &&
          box.right <= bounds.right
        );
      }),
    );
    expect(fieldsFit).toBe(true);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await screenshot(
      page,
      testInfo,
      `dynamic-price-settings-${width}-${testInfo.project.name}`,
    );
    await advanced.locator("summary").click();
  }
  await page.locator("#hold-action").click();
  const save = form.locator('button[type="submit"]');
  await save.click({ clickCount: 2 });
  await expect(form).toHaveAttribute("aria-busy", "true");
  await expect(panel.locator(".electricity-operation-status")).toHaveText(
    english ? "Saving …" : "Wird gespeichert …",
  );
  await expect(save).toHaveText(english ? "Saving …" : "Wird gespeichert …");
  await expect(save).toBeDisabled();
  await expect(feed).toBeDisabled();
  await expect(before).not.toContainText(english ? "9.25" : "9,25");
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  await expect(panel).toHaveAttribute("data-tariff-configure-requests", "1");
  await page.locator("#release-action").click();
  await expect(form).toHaveCount(0);
  await expect(before).toContainText(english ? "9.25" : "9,25");
  await expect(page.locator("#actions")).toContainText('"pv_factor":70');
  await expect(page.locator("#actions")).toContainText('"price_unit":"ct_kwh"');
  await expect(page.locator("#actions")).toContainText(
    '"price_attribute":null',
  );
  await panel
    .getByRole("button", {
      name: english ? "Change tariff" : "Tarif wechseln",
      exact: true,
    })
    .click();
  const choice = panel.locator(".electricity-choice");
  await choice.locator('input[value="time_of_use"]').check();
  const confirmedAction = await page.locator("#actions").innerText();
  await page.locator("#hold-action").click();
  const apply = choice.locator('button[type="submit"]');
  await apply.click({ clickCount: 2 });
  await expect(choice).toHaveAttribute("aria-busy", "true");
  await expect(panel.locator(".electricity-operation-status")).toHaveText(
    english ? "Applying tariff …" : "Tarif wird übernommen …",
  );
  await expect(apply).toHaveText(
    english ? "Applying tariff …" : "Tarif wird übernommen …",
  );
  await expect(apply).toBeDisabled();
  await expect(choice.locator("input").first()).toBeDisabled();
  await expect(panel.locator(".electricity-active strong")).toHaveText(
    english ? "Dynamic" : "Dynamisch",
  );
  await expect(page.locator("#actions")).toHaveText(confirmedAction);
  await expect(panel).toHaveAttribute("data-tariff-configure-requests", "2");
  await page.locator("#release-action").click();
  await expect(choice).toHaveCount(0);
  await expect(panel.locator(".electricity-active strong")).toHaveText(
    english ? "Time of use" : "Zeitvariabel",
  );
  await expect(panel).toHaveAttribute("data-tariff-configure-requests", "2");
});

test("dynamic setup matches the time-of-use groups and keeps price detail optional", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  await expect(
    panel.locator(
      ".electricity-prices h2, .electricity-charging h2, .electricity-activation h2",
    ),
  ).toHaveText(
    english
      ? ["Prices & times", "Grid charging"]
      : ["Preise & Zeiten", "Netzladung"],
  );
  await expect(panel.locator(".electricity-master input")).toHaveCount(1);
  await expect(panel.locator(".electricity-tariff-bar input")).toHaveCount(0);
  const prices = panel.locator(".electricity-price-card");
  const details = prices.locator(".electricity-price-details");
  await expect(details).not.toHaveAttribute("open", "");
  await expect(prices.locator("svg")).toBeHidden();
  await expect(
    panel.locator(".electricity-charging > .electricity-activation"),
  ).toHaveCount(1);
  for (const width of testInfo.project.name.startsWith("mobile")
    ? [390, 320]
    : [1440, 1100]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await panel.evaluate((element) => {
        const bounds = element.getBoundingClientRect();
        return (
          document.documentElement.scrollWidth <= innerWidth &&
          [...element.querySelectorAll("button, input, select, summary")].every(
            (control) => {
              const box = control.getBoundingClientRect();
              return (
                !box.width ||
                !box.height ||
                (box.left >= bounds.left && box.right <= bounds.right)
              );
            },
          )
        );
      }),
    ).toBe(true);
    if (!english) {
      expect(
        await panel
          .locator(".electricity-price-summary")
          .evaluate((element) => {
            const text = element.querySelector(
              ":scope > div:nth-child(2) dt",
            )!.firstChild!;
            const word = "Einspeisevergütung";
            const start = text.textContent!.indexOf(word);
            const range = document.createRange();
            range.setStart(text, start);
            range.setEnd(text, start + word.length);
            return range.getClientRects().length;
          }),
      ).toBe(1);
    }
    await screenshot(page, testInfo, `dynamic-overview-steps-${width}`);
  }
  const summary = details.locator(":scope > summary");
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(prices.locator("svg")).toBeVisible();
  await prices
    .getByRole("button", { name: english ? "Tomorrow" : "Morgen", exact: true })
    .click();
  await expect(prices.locator(".electricity-day")).toContainText(
    english ? "Tomorrow" : "Morgen",
  );
  await summary.focus();
  await page.keyboard.press("Space");
  await expect(details).not.toHaveAttribute("open", "");
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});
