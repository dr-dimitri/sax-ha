import { expect, test } from "@playwright/test";
import type { HomeAssistant } from "../src/types";

// REQ-VUE-CHARGING / #251: run real keyboard entry on macOS WebKit too.
test("time window keeps partial hours, validates the named field and normalizes midnight", async ({
  page,
}) => {
  await page.goto("/sax-power-vue/netzdienliches-laden");
  const window = page.locator("sax-power-vue-panel .time-window-control");
  const fields = window.locator("input");
  const start = fields.nth(0);
  const end = fields.nth(1);
  const apply = window.getByRole("button", { name: "Übernehmen", exact: true });
  const confirmed = window.locator(".time-window-control__confirmed");
  await expect(start).toHaveAttribute("type", "text");
  await start.fill("");
  await start.pressSequentially("12");
  await page.evaluate(() => {
    const panel = document.querySelector(
      "sax-power-vue-panel",
    ) as HTMLElement & { hass: HomeAssistant };
    const id = "sensor.demo_soc";
    panel.hass = {
      ...panel.hass,
      states: {
        ...panel.hass.states,
        [id]: { ...panel.hass.states[id], state: "64" },
      },
    };
  });
  await expect(start).toBeFocused();
  await expect(start).toHaveValue("12");
  await apply.click();
  await expect(window.getByRole("alert")).toContainText("Start");
  await expect(start).toHaveAttribute("aria-invalid", "true");
  await expect(start).toBeFocused();
  await expect(start).toHaveValue("12");
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  await start.pressSequentially(":30");
  await start.press("Tab");
  await expect(start).toHaveValue("12:30");
  await end.fill("2460");
  await apply.click();
  await expect(window.getByRole("alert")).toContainText("Ende");
  await expect(end).toBeFocused();
  await expect(end).toHaveValue("2460");
  await start.fill("");
  await start.pressSequentially("0000");
  await start.press("Tab");
  await expect(start).toHaveValue("00:00");
  await end.fill("04:59");
  await page.locator("#failure").click();
  await page.locator("#hold-action").click();
  await apply.click();
  await expect(window).toHaveAttribute("aria-busy", "true");
  await expect(window.getByRole("status")).toContainText("gesendet");
  await expect(apply).toBeDisabled();
  await expect(start).toBeDisabled();
  await expect(end).toBeDisabled();
  await expect(confirmed).toContainText("22:00");
  await expect(confirmed).toContainText("06:00");
  await window.evaluate((form) =>
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    ),
  );
  await expect(page.locator("#actions")).toContainText(
    "1: sax_power.set_grid_serving_window",
  );
  await page.locator("#release-action").click();
  await expect(window.getByRole("alert")).toBeVisible();
  await expect(start).toHaveValue("00:00");
  await expect(end).toHaveValue("04:59");
  await expect(confirmed).toContainText("22:00");
  await apply.click();
  await expect(window.getByRole("alert")).toHaveCount(0);
  await expect(confirmed).toContainText("00:00 – 04:59");
  await expect(page.locator("#actions")).toHaveText(
    '2: sax_power.set_grid_serving_window {"device_id":"demo-device","start":"00:00:00","end":"04:59:00"}',
  );
});

for (const notification of ["change", "blur", "submit"] as const) {
  test(`time window reads visible values committed through ${notification} without input events`, async ({
    page,
  }) => {
    await page.goto("/sax-power-vue/netzdienliches-laden");
    const window = page.locator("sax-power-vue-panel .time-window-control");
    await window.locator("input").evaluateAll((fields, event) => {
      for (const [index, field] of fields.entries()) {
        (field as HTMLInputElement).value = ["0000", "04:59"][index];
        if (event !== "submit")
          field.dispatchEvent(new Event(event, { bubbles: true }));
      }
    }, notification);
    const apply = window.getByRole("button", {
      name: "Übernehmen",
      exact: true,
    });
    await expect(apply).toBeEnabled();
    await apply.click();
    await expect(page.locator("#actions")).toHaveText(
      '1: sax_power.set_grid_serving_window {"device_id":"demo-device","start":"00:00:00","end":"04:59:00"}',
    );
    await expect(
      window.locator(".time-window-control__confirmed"),
    ).toContainText("00:00 – 04:59");
  });
}
