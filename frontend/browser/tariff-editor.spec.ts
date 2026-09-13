import { expect, test, type Locator, type Page } from "@playwright/test";
import type { HomeAssistant, TariffProfile } from "../src/types";

async function enterNativeTime(
  page: Page,
  field: Locator,
  time: string,
  browserName: string,
) {
  const [hour, minute] = time.split(":");
  await field.click({ position: { x: 12, y: 20 } });
  for (let i = 0; i < 4; i++) await page.keyboard.press("ArrowLeft");
  await page.keyboard.type(
    browserName === "chromium" ? String(Number(hour) % 12 || 12) : hour,
  );
  // A live HA update must preserve a partly entered native time segment.
  await page.evaluate(() => {
    const panel = document.querySelector(
      "sax-power-vue-panel",
    ) as HTMLElement & {
      hass: HomeAssistant;
    };
    const id = "sensor.demo_soc";
    panel.hass = {
      ...panel.hass,
      states: {
        ...panel.hass.states,
        [id]: { ...panel.hass.states[id], state: "64" },
      },
    };
  });
  for (let i = 0; i < 4; i++) await page.keyboard.press("ArrowLeft");
  await page.keyboard.press(browserName === "webkit" ? "Tab" : "ArrowRight");
  await page.keyboard.type(minute);
  if (browserName === "chromium") {
    await page.keyboard.press("ArrowRight");
    await page.keyboard.press(Number(hour) < 12 ? "a" : "p");
  }
  await expect(field).toHaveValue(time);
}

test("two separate low tariffs accept native keyboard entry while HA states update", async ({
  page,
  browserName,
}) => {
  await page.goto("/sax-power-vue/stromtarif");
  const tariff = page.locator("sax-power-vue-panel .tariff-plan");
  await tariff.getByRole("button", { name: "Bearbeiten", exact: true }).click();
  while (await tariff.locator(".tariff-plan__window").count())
    await tariff.locator(".tariff-plan__remove").last().click();
  for (const [start, end] of [
    ["00:00", "04:59"],
    ["12:30", "14:30"],
  ]) {
    await tariff
      .getByRole("button", { name: "+ Zeitfenster hinzufügen", exact: true })
      .click();
    const row = tariff.locator(".tariff-plan__window").last();
    const fields = row.locator('input[type="time"]');
    await enterNativeTime(page, fields.nth(0), start, browserName);
    await enterNativeTime(page, fields.nth(1), end, browserName);
    await row.locator('input[type="text"]').fill("18");
  }
  await tariff.getByRole("button", { name: "Speichern", exact: true }).click();
  await expect(tariff.locator("form")).toHaveCount(0);
  await expect(tariff.getByRole("alert")).toHaveCount(0);
  await expect(page.locator("#actions")).toContainText(
    '"start":"00:00:00","end":"04:59:00"',
  );
  await expect(page.locator("#actions")).toContainText(
    '"start":"12:30:00","end":"14:30:00"',
  );
});

for (const notification of ["change", "submit"] as const) {
  // Explicitly simulate a picker that commits its DOM value without an input event.
  // Native WebKit keyboard input is independently covered above.
  test(`time values committed through ${notification} are saved from the visible fields`, async ({
    page,
  }) => {
    await page.goto("/sax-power-vue/stromtarif");
    const tariff = page.locator("sax-power-vue-panel .tariff-plan");
    await tariff
      .getByRole("button", { name: "Bearbeiten", exact: true })
      .click();
    await tariff.locator(".tariff-plan__remove").last().click();
    await tariff.locator('input[type="time"]').nth(1).fill("04:59");
    await tariff
      .getByRole("button", { name: "+ Zeitfenster hinzufügen", exact: true })
      .click();
    const row = tariff.locator(".tariff-plan__window").last();
    await row.locator('input[type="text"]').fill("18");
    await row.locator('input[type="time"]').evaluateAll((fields, event) => {
      for (const [index, field] of fields.entries()) {
        (field as HTMLInputElement).value = ["12:30", "14:30"][index];
        if (event === "change")
          field.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }, notification);
    await expect(row.locator('input[type="time"]').nth(0)).toHaveValue("12:30");
    await expect(row.locator('input[type="time"]').nth(1)).toHaveValue("14:30");
    await tariff
      .getByRole("button", { name: "Speichern", exact: true })
      .click();
    await expect(tariff.locator("form")).toHaveCount(0);
    await expect(tariff.getByRole("alert")).toHaveCount(0);
    await expect(page.locator("#actions")).toContainText(
      '"start":"12:30:00","end":"14:30:00"',
    );
  });
}

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

// REQ-VUE-ELECTRICITY-TARIFF / #244: the backend owns the PV-source guard.
test("active consumption plan keeps the tariff draft after a required PV source rejection", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/sax-power-vue/stromtarif?bridge-plan");
  if (english) await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
  const panel = page.locator("sax-power-vue-panel");
  const tariff = panel.locator(".tariff-plan");
  await expect(tariff).toBeVisible();
  await page.evaluate(() => {
    const panel = document.querySelector(
      "sax-power-vue-panel",
    ) as HTMLElement & { hass: HomeAssistant };
    const original = panel.hass.callWS!;
    const source = "sensor.demo_pv_start";
    panel.hass = {
      ...panel.hass,
      states: {
        ...panel.hass.states,
        [source]: {
          entity_id: source,
          state: "2026-09-14T07:00:00+02:00",
          attributes: { friendly_name: "PV start", device_class: "timestamp" },
        },
      },
      callWS: async <T>(
        request: Readonly<Record<string, unknown>>,
      ): Promise<T> => {
        if (request.type === "sax_power/dashboard/tariff/get") {
          const result = await original<TariffProfile>(request);
          return {
            ...result,
            profiles: {
              ...result.profiles,
              time_of_use: {
                ...result.profiles!.time_of_use,
                pv_sensor: source,
              },
            },
          } as T;
        }
        if (
          request.type === "sax_power/dashboard/tariff/configure" &&
          (request.profile as { pv_sensor?: string | null } | undefined)
            ?.pv_sensor === null &&
          panel.hass.states["switch.demo_bridge_charge_enabled"]?.state === "on"
        ) {
          panel.dataset.rejectedTariff = JSON.stringify(request);
          throw { code: "bridge_pv_start_required" };
        }
        return original<T>(request);
      },
    };
  });
  await tariff
    .getByRole("button", { name: english ? "Edit" : "Bearbeiten", exact: true })
    .click();
  const source = tariff.locator(".sensor-picker select");
  await expect(tariff.locator(".sensor-picker")).toContainText(
    english ? "(required)" : "(erforderlich)",
  );
  await expect(source).toHaveValue("sensor.demo_pv_start");
  await source.selectOption("");
  const base = tariff.locator('[name="base_price"]');
  await base.fill(english ? "31.25" : "31,25");
  const windowPrice = tariff
    .locator('.tariff-plan__window input[type="text"]')
    .first();
  await windowPrice.fill(english ? "17.75" : "17,75");
  const save = tariff.getByRole("button", {
    name: english ? "Save" : "Speichern",
    exact: true,
  });
  await save.click();
  await expect(tariff.getByRole("alert")).toContainText(
    english
      ? "Choose a source or turn off this charging plan first."
      : "Wähle eine Quelle oder schalte diese Ladeplanung zuerst aus.",
  );
  await expect(base).toHaveValue(english ? "31.25" : "31,25");
  await expect(windowPrice).toHaveValue(english ? "17.75" : "17,75");
  await expect(source).toHaveValue("");
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  expect(
    await panel.evaluate(
      (element) =>
        JSON.parse((element as HTMLElement).dataset.rejectedTariff!).profile
          .pv_sensor,
    ),
  ).toBeNull();
  await source.selectOption("sensor.demo_pv_start");
  await save.click();
  await expect(tariff.locator("form")).toHaveCount(0);
  await expect(page.locator("#actions")).toContainText(
    '"pv_sensor":"sensor.demo_pv_start"',
  );
  expect(
    await panel.evaluate(
      (element) =>
        (element as HTMLElement & { hass: HomeAssistant }).hass.states[
          "switch.demo_bridge_charge_enabled"
        ]?.state,
    ),
  ).toBe("on");
  expect(errors).toEqual([]);
});
