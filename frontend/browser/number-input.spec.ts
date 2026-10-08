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

// REQ-VUE-ELECTRICITY-TARIFF / #268: retry after collapsing must send the
// failed draft, even if its response arrives while the editor is hidden.
test("all dynamic number drafts survive collapse, delayed failure, reopening and retry", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  await priceControls(page, english);
  const panel = page.locator("sax-power-vue-panel");
  const charging = panel.locator(".electricity-charging");
  const settings = charging.locator(".dynamic-charging-settings");
  const done = english ? "Done" : "Fertig";
  const actions = page.locator("#actions");
  let writes = 0;
  for (const [key, label, value] of [
    ["max_soc", english ? "Grid charge target (%)" : "Netzladeziel (%)", "85"],
    [
      "price_charge_max_price",
      english
        ? "Maximum price for charging (ct/kWh)"
        : "Höchster Preis zum Laden (ct/kWh)",
      "-0.5",
    ],
    [
      "price_charge_neutral_price",
      english
        ? "Preserve battery energy below (ct/kWh)"
        : "Speicher bei günstigem Strom schonen bis (ct/kWh)",
      "12.5",
    ],
    [
      "price_charge_hours",
      english
        ? "Maximum charging time per 24 hours"
        : "Maximale Ladezeit je 24 Stunden",
      "3",
    ],
  ]) {
    if (key === "price_charge_hours") {
      await settings.locator('[data-strategy="smart"]').click();
      await expect(settings.locator('[data-strategy="smart"]')).toHaveAttribute(
        "aria-pressed",
        "true",
      );
      writes++;
    }
    const input = settings.getByRole("spinbutton", {
      name: label,
      exact: true,
    });
    const form = settings.locator(".entity-control").filter({
      has: page.getByRole("spinbutton", { name: label, exact: true }),
    });
    const confirmed = await form.locator(".entity-control__value").innerText();
    await typeNumber(input, value!);
    await page.locator("#hold-action").click();
    await page.locator("#failure").click();
    await form.getByRole("button").click();
    const request = `${++writes}: number.set_value ${JSON.stringify({ value: Number(value), entity_id: `number.demo_${key}` })}`;
    await expect(actions).toHaveText(request);
    await charging.getByRole("button", { name: done, exact: true }).click();
    await expect(
      charging.locator(".electricity-charging-feedback"),
    ).toContainText(english ? "Sending change" : "Änderung wird");
    await charging.locator("header > button").click();
    await expect(input).toHaveValue(value!);
    await expect(input).toBeDisabled();
    await expect(form.getByRole("button")).toBeDisabled();
    await expect(form.locator(".entity-control__value")).toHaveText(confirmed);
    await expect(actions).toHaveText(request);
    await charging.getByRole("button", { name: done, exact: true }).click();
    await page.locator("#release-action").click();
    await expect(
      charging.locator(".electricity-charging-feedback").getByRole("alert"),
    ).toBeVisible();
    await charging.locator("header > button").click();
    await expect(input).toHaveValue(value!);
    await expect(input).toBeEnabled();
    await expect(form.getByRole("alert")).toBeVisible();
    await expect(form.locator(".entity-control__value")).toHaveText(confirmed);
    await form.getByRole("button").click();
    await expect(actions).toHaveText(
      `${++writes}: number.set_value ${JSON.stringify({ value: Number(value), entity_id: `number.demo_${key}` })}`,
    );
    await expect(input).toBeEnabled();
    await expect(input).toHaveValue(value!);
    await expect(form.getByRole("alert")).toHaveCount(0);
    await expect(form.locator(".entity-control__value")).toContainText(
      english ? value! : value!.replace(".", ","),
    );
  }
});

test("unsent native partial drafts remain editable after collapsing and reopening", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const [{ input }] = await priceControls(page, english);
  const charging = page.locator("sax-power-vue-panel .electricity-charging");
  const actions = page.locator("#actions");
  for (const [draft, suffix, result] of [
    ["-", "5", "-5"],
    ["1e", "1", "1e1"],
  ]) {
    await typeNumber(input, draft!);
    await expect(input).toHaveValue("");
    expect(
      await input.evaluate(
        (element: HTMLInputElement) => element.validity.badInput,
      ),
    ).toBe(true);
    await charging
      .getByRole("button", { name: english ? "Done" : "Fertig", exact: true })
      .click();
    await charging.locator("header > button").click();
    await expect(input).toHaveValue("");
    expect(
      await input.evaluate(
        (element: HTMLInputElement) => element.validity.badInput,
      ),
    ).toBe(true);
    await input.focus();
    await input.pressSequentially(suffix!);
    await expect(input).toHaveValue(result!);
    await expect(actions).toHaveText("Keine Aktion");
  }
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
test("global SOC remains directly editable and displays the restored confirmed target", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href$='/stromtarif']").click();
  await panel.locator(".electricity-charging header > button").click();
  const target = panel.getByRole("spinbutton", {
    name: english ? "Grid charge target (%)" : "Netzladeziel (%)",
    exact: true,
  });
  const global = panel.getByRole("spinbutton", {
    name: english
      ? "Charge limit for all charging methods (%)"
      : "Ladegrenze für alle Lademethoden (%)",
    exact: true,
  });
  await expect(panel.locator(".tou-charging-settings details")).toHaveCount(0);
  await expect(global).toBeVisible();
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

// REQ-TIMED-SOC-CHARGE: native keyboard input keeps rejected drafts and
// allows equal boundaries and the valid zero start in Chromium and Safari.
test("charge target and start reject crossed limits and accept zero", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator("nav a[href$='/stromtarif']").click();
  await panel.locator(".electricity-charging header > button").click();
  const actions = page.locator("#actions");
  for (const [label, invalid] of [
    [english ? "Grid charge target (%)" : "Netzladeziel (%)", "19"],
    [english ? "Start threshold (%)" : "Ladestart (%)", "81"],
  ]) {
    const input = panel.getByRole("spinbutton", { name: label, exact: true });
    const form = panel.locator(".entity-control").filter({
      has: page.getByRole("spinbutton", { name: label, exact: true }),
    });
    await typeNumber(input, invalid!);
    await form.getByRole("button").click();
    await expect(form.getByRole("alert")).toHaveText(
      english
        ? "The grid charge target must be at least as high as the start threshold."
        : "Das Netzladeziel muss mindestens so hoch wie der Ladestart sein.",
    );
    await expect(input).toHaveAttribute("aria-invalid", "true");
    await expect(input).toHaveValue(invalid!);
    await expect(actions).toHaveText("Keine Aktion");
  }
  const start = panel.getByRole("spinbutton", {
    name: english ? "Start threshold (%)" : "Ladestart (%)",
    exact: true,
  });
  const startForm = panel.locator(".entity-control").filter({
    has: page.getByRole("spinbutton", {
      name: english ? "Start threshold (%)" : "Ladestart (%)",
      exact: true,
    }),
  });
  await typeNumber(start, "0");
  await startForm.getByRole("button").click();
  await expect(actions).toHaveText(
    '1: number.set_value {"value":0,"entity_id":"number.demo_timed_charge_min_soc"}',
  );
  await expect(startForm.getByRole("alert")).toHaveCount(0);
  await expect(panel.locator(".tou-charging-threshold")).toContainText(
    english ? "Start at" : "Start bei",
  );
  const target = panel.getByRole("spinbutton", {
    name: english ? "Grid charge target (%)" : "Netzladeziel (%)",
    exact: true,
  });
  await typeNumber(target, "0");
  await panel
    .locator(".entity-control")
    .filter({
      has: page.getByRole("spinbutton", {
        name: english ? "Grid charge target (%)" : "Netzladeziel (%)",
        exact: true,
      }),
    })
    .getByRole("button")
    .click();
  await expect(actions).toHaveText(
    '2: number.set_value {"value":0,"entity_id":"number.demo_timed_charge_max_soc"}',
  );
});
