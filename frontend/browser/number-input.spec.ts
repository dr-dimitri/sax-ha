import { expect, test, type Locator, type Page } from "@playwright/test";
import type { HomeAssistant } from "../src/types";

async function typeNumber(input: Locator, value: string) {
  await input.focus();
  await input.press("ControlOrMeta+A");
  await input.press("Backspace");
  await input.pressSequentially(value, { delay: 20 });
}

async function priceControls(page: Page, english: boolean) {
  await page.locator("#tariff-dynamic").click();
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href$='/stromtarif']").click();
  await panel.locator(".electricity-charging header > button").click();
  const settings = panel.locator(".dynamic-charging-settings");
  await settings.locator(".dynamic-charging-advanced summary").click();
  return [
    {
      key: "price_charge_max_price",
      label: english
        ? "Maximum price for charging (ct/kWh)"
        : "Höchster Preis zum Laden (ct/kWh)",
    },
    {
      key: "price_charge_neutral_price",
      label: english
        ? "Preserve battery energy below (ct/kWh)"
        : "Speicher bei günstigem Strom schonen bis (ct/kWh)",
    },
  ].map(({ key, label }) => {
    const input = settings.getByRole("spinbutton", {
      name: label,
      exact: true,
    });
    const form = settings.locator(".entity-control").filter({
      has: page.getByRole("spinbutton", { name: label, exact: true }),
    });
    return { key, input, form, apply: form.getByRole("button") };
  });
}

test.beforeEach(async ({ page }, testInfo) => {
  await page.goto("/sax-power-vue/allgemein");
  if (testInfo.project.name.endsWith("en"))
    await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
});

// REQ-VUE-ENTITY-BINDING / #259: native number inputs have intermediate
// states that assigning a complete .value cannot reproduce.
test("typed negative and decimal prices reach HA unchanged in both price controls", async ({
  page,
}, testInfo) => {
  const controls = await priceControls(
    page,
    testInfo.project.name.endsWith("en"),
  );
  const actions = page.locator("#actions");
  let writes = 0;
  for (const { key, input, apply } of controls) {
    for (const value of ["-5", "0.5", "12.5", "-0.5"]) {
      const before = await actions.innerText();
      await typeNumber(input, value);
      await expect(input).toHaveValue(value);
      await expect(actions).toHaveText(before);
      await apply.click();
      await expect(actions).toHaveText(
        `${++writes}: number.set_value ${JSON.stringify({ value: Number(value), entity_id: `number.demo_${key}` })}`,
      );
      await expect(input).toBeEnabled();
      await expect(input).toHaveValue(value);
    }
  }
});

test("cursor corrections and replacing selections preserve other digits and signs", async ({
  page,
}, testInfo) => {
  const controls = await priceControls(
    page,
    testInfo.project.name.endsWith("en"),
  );
  for (const [index, { key, input, apply }] of controls.entries()) {
    await typeNumber(input, "-12.5");
    await input.press("ArrowLeft");
    await input.press("ArrowLeft");
    await input.press("Backspace");
    await input.pressSequentially("0");
    await expect(input).toHaveValue("-10.5");
    await page.locator("sax-power-vue-panel").evaluate((element) => {
      const panel = element as HTMLElement & { hass: HomeAssistant };
      const id = "sensor.demo_soc";
      panel.hass = {
        ...panel.hass,
        states: {
          ...panel.hass.states,
          [id]: { ...panel.hass.states[id]!, state: "64" },
        },
      };
    });
    await input.pressSequentially("1");
    await expect(input).toHaveValue("-101.5");
    await input.press("Backspace");
    await expect(input).toHaveValue("-10.5");
    await input.press("ControlOrMeta+A");
    await input.press("ArrowRight");
    await input.press("Shift+ArrowLeft");
    await input.pressSequentially("7");
    await expect(input).toHaveValue("-10.7");
    await input.press("ControlOrMeta+A");
    await input.press("ArrowLeft");
    await input.press("ArrowRight");
    await input.press("Shift+ArrowRight");
    await input.press("Shift+ArrowRight");
    await input.pressSequentially("2");
    await expect(input).toHaveValue("-2.7");
    await apply.click();
    await expect(page.locator("#actions")).toHaveText(
      `${index + 1}: number.set_value ${JSON.stringify({ value: -2.7, entity_id: `number.demo_${key}` })}`,
    );
    await expect(input).toBeEnabled();
    await expect(input).toHaveValue("-2.7");
  }
});

test("empty, incomplete, out-of-range and off-step prices show a field error without writing", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const controls = await priceControls(page, english);
  for (const { input, apply, form } of controls) {
    for (const value of ["", "-", "1e", "1e309", "201", "-101", "0.05"]) {
      await typeNumber(input, value);
      const draft = await input.inputValue();
      await expect(apply).toBeEnabled();
      await apply.click();
      await expect(form.getByRole("alert")).toHaveText(
        english
          ? "Please enter a valid value within the allowed range."
          : "Bitte einen gültigen Wert im erlaubten Bereich eingeben.",
      );
      await expect(input).toHaveAttribute("aria-invalid", "true");
      await expect(input).toHaveValue(draft);
      await expect(form.locator(".entity-control__value")).toContainText("-5");
      await expect(page.locator("#actions")).toHaveText("Keine Aktion");
      if (value === "-") {
        await input.focus();
        await input.pressSequentially("5");
        await expect(input).toHaveValue("-5");
        await expect(page.locator("#actions")).toHaveText("Keine Aktion");
      }
    }
  }
});

test("typed prices retain drafts and confirmed values across pending, failure and retry", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const [{ input, apply, form }] = await priceControls(page, english);
  await typeNumber(input, "-0.5");
  await page.locator("#hold-action").click();
  await page.locator("#failure").click();
  await apply.click({ clickCount: 2 });
  await expect(form).toHaveAttribute("aria-busy", "true");
  await expect(form.getByRole("status")).toHaveText(
    english
      ? "Sending change to Home Assistant …"
      : "Änderung wird an Home Assistant gesendet …",
  );
  await expect(input).toBeDisabled();
  await expect(apply).toBeDisabled();
  await expect(form.locator(".entity-control__value")).toContainText("-5");
  await expect(page.locator("#actions")).toHaveText(
    '1: number.set_value {"value":-0.5,"entity_id":"number.demo_price_charge_max_price"}',
  );
  await page.locator("#release-action").click();
  await expect(form.getByRole("alert")).toBeVisible();
  await expect(input).toHaveValue("-0.5");
  await expect(input).toBeEnabled();
  await expect(form.locator(".entity-control__value")).toContainText("-5");
  await page.locator("#hold-action").click();
  await apply.click();
  await expect(form.locator(".entity-control__value")).toContainText("-5");
  await page.locator("#release-action").click();
  await expect(form).toHaveAttribute("aria-busy", "false");
  await expect(form.getByRole("alert")).toHaveCount(0);
  await expect(input).toHaveValue("-0.5");
  await expect(form.locator(".entity-control__value")).toContainText(
    english ? "-0.5" : "-0,5",
  );
  await expect(page.locator("#actions")).toHaveText(
    '2: number.set_value {"value":-0.5,"entity_id":"number.demo_price_charge_max_price"}',
  );
});

test("max SOC and solar forecast threshold remain usable with keyboard entry", async ({
  page,
}) => {
  const panel = page.locator("sax-power-vue-panel");
  for (const [index, [path, key, value]] of [
    ["allgemein", "max_soc", "75"],
    ["netzdienliches-laden", "grid_serving_forecast_threshold", "12"],
  ].entries()) {
    await panel.locator(`nav a[href$='/${path}']`).click();
    const input = panel.getByRole("spinbutton");
    const form = panel.locator(".entity-control").filter({
      has: page.getByRole("spinbutton"),
    });
    await typeNumber(input, value!);
    await expect(input).toHaveValue(value!);
    await form.getByRole("button").click();
    await expect(page.locator("#actions")).toHaveText(
      `${index + 1}: number.set_value ${JSON.stringify({ value: Number(value), entity_id: `number.demo_${key}` })}`,
    );
    await expect(input).toBeEnabled();
    await expect(input).toHaveValue(value!);
  }
});

// REQ-TIMED-SOC-CHARGE / #260: HA supplies the effective target while
// preserving the stored target; the dashboard must explain these updates.
test("global SOC help explains temporary caps and displays the restored confirmed target", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href$='/stromtarif']").click();
  await panel.locator(".electricity-charging header > button").click();
  await panel.locator(".tou-charging-advanced summary").click();
  const target = panel.getByRole("spinbutton", {
    name: english ? "Charge target (%)" : "Ladeziel (%)",
    exact: true,
  });
  const global = panel.getByRole("spinbutton", {
    name: english
      ? "Charge limit for all charging methods (%)"
      : "Ladegrenze für alle Lademethoden (%)",
    exact: true,
  });
  await expect(panel.locator(".tou-charging-advanced")).toContainText(
    english
      ? "Also applies to solar charging. This limit temporarily caps the saved grid charge target. Raising it makes the original target effective again, up to the new global limit. Only explicitly changing the grid charge target permanently changes its saved value."
      : "Gilt auch für Solarstrom. Diese Grenze begrenzt das gespeicherte Netzladeziel vorübergehend. Wenn du sie anhebst, wird das ursprüngliche Ziel bis zur neuen globalen Grenze wieder wirksam. Nur wenn du das Netzladeziel ausdrücklich änderst, wird dessen gespeicherter Wert dauerhaft geändert.",
  );
  for (const [limit, effective] of [
    [90, 80],
    [60, 60],
    [95, 80],
  ]) {
    await panel.evaluate(
      (element, [limit, effective]) => {
        const host = element as HTMLElement & { hass: HomeAssistant };
        const globalId = "number.demo_max_soc";
        const targetId = "number.demo_timed_charge_max_soc";
        host.hass = {
          ...host.hass,
          states: {
            ...host.hass.states,
            [globalId]: {
              ...host.hass.states[globalId]!,
              state: String(limit),
            },
            [targetId]: {
              ...host.hass.states[targetId]!,
              state: String(effective),
            },
          },
        };
      },
      [limit, effective],
    );
    await expect(global).toHaveValue(String(limit));
    await expect(target).toHaveValue(String(effective));
    await expect(panel.locator(".tou-charging-summary")).toContainText(
      `${effective} %`,
    );
    await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  }
});
