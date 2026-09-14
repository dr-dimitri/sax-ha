import { expect, test, type Locator, type TestInfo } from "@playwright/test";
import type { HomeAssistant } from "../src/types";

test("completion and missing assessment remain distinct after a forecast gap", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const mobile = testInfo.project.name.startsWith("mobile");
  await page.goto("/sax-power-vue/stromtarif?bridge-plan");
  if (english) await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
  const panel = page.locator("sax-power-vue-panel");
  await panel.locator(".electricity-plan > summary").click();
  const card = panel.locator(".charge-plan");
  await page.setViewportSize({ width: mobile ? 320 : 1440, height: 1000 });

  for (const state of ["waiting_for_data", "insufficient", "complete"]) {
    await panel.evaluate((element, state) => {
      const host = element as HTMLElement & { hass: HomeAssistant };
      const entityId = "sensor.demo_bridge_charge_plan";
      const previous = host.hass.states[entityId];
      host.hass = {
        ...host.hass,
        states: {
          ...host.hass.states,
          [entityId]: {
            ...previous,
            state,
            attributes: {
              ...previous.attributes,
              completed_at: "2026-09-14T00:00:00Z",
              completion_evaluated_at:
                state === "waiting_for_data" ? null : "2026-09-14T00:02:00Z",
              shortfall_kwh:
                state === "waiting_for_data"
                  ? null
                  : state === "insufficient"
                    ? 0.56
                    : 0,
              reason:
                state === "insufficient"
                  ? "charge_shortfall"
                  : "measurements_missing",
              data_gap_reason: "pv_start_missing",
            },
          },
        },
      };
    }, state);
    await expect(card).toContainText(
      english ? "PV forecast was temporarily" : "PV-Prognose zeitweise",
    );
    if (state === "waiting_for_data") {
      await expect(card).toContainText(
        english ? "shortfall is still unknown" : "Fehlmenge ist noch unbekannt",
      );
      await expect(card).not.toContainText("0,00 kWh");
      await expect(card).not.toContainText("0.00 kWh");
    } else if (state === "insufficient") {
      await expect(card).toContainText(
        english ? "shortfall: 0.56 kWh" : "Fehlbetrag: 0,56 kWh",
      );
      await expect(card).not.toContainText(
        english ? "charging is planned" : "Aufladung im Niedertarif ist",
      );
    } else {
      await expect(card).toContainText(
        english ? "grid charging is complete" : "Netzladung ist abgeschlossen",
      );
    }
    await verifyCardGeometry(card);
    await attachScreenshot(
      card,
      testInfo,
      `completion-${state}`,
      mobile ? 320 : 1440,
    );
  }
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});

async function verifyCardGeometry(card: Locator) {
  const geometry = await card.evaluate((element) => {
    const bounds = element.getBoundingClientRect();
    const violations = [...element.querySelectorAll("h2, p")]
      .filter((paragraph) => {
        const style = getComputedStyle(paragraph);
        const rect = paragraph.getBoundingClientRect();
        const content = document.createRange();
        content.selectNodeContents(paragraph);
        return (
          rect.width === 0 ||
          rect.height === 0 ||
          style.visibility === "hidden" ||
          parseFloat(style.fontSize) < 13.99 ||
          style.textOverflow === "ellipsis" ||
          [...content.getClientRects()].some(
            (line) =>
              line.left < bounds.left - 1 ||
              line.right > bounds.right + 1 ||
              line.top < bounds.top - 1 ||
              line.bottom > bounds.bottom + 1,
          )
        );
      })
      .map((paragraph) => paragraph.textContent);
    return {
      left: bounds.left,
      right: bounds.right,
      pageWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
      violations,
    };
  });
  expect(geometry.left).toBeGreaterThanOrEqual(0);
  expect(geometry.right).toBeLessThanOrEqual(geometry.viewportWidth);
  expect(geometry.pageWidth).toBeLessThanOrEqual(geometry.viewportWidth);
  expect(geometry.violations).toEqual([]);
}

async function attachScreenshot(
  card: Locator,
  testInfo: TestInfo,
  state: string,
  width: number,
) {
  const screenshotPath = testInfo.outputPath(`bridge-${state}-${width}.png`);
  await card.page().screenshot({ path: screenshotPath, fullPage: true });
  await testInfo.attach(`bridge-${state}-${width}-${testInfo.project.name}`, {
    path: screenshotPath,
    contentType: "image/png",
  });
}

test("consumption-based bridge plan explains the charge and no-charge decision without obsolete controls or overflow", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const english = testInfo.project.name.endsWith("en");
  const mobile = testInfo.project.name.startsWith("mobile");
  await page.goto("/sax-power-vue/stromtarif?bridge-plan");
  const panel = page.locator("sax-power-vue-panel");
  const plan = panel.locator(".charge-plan");
  await panel.locator(".electricity-plan > summary").click();
  await expect(plan).toBeVisible();
  if (english) await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
  await expect(panel.getByRole("heading", { level: 1 })).toHaveText(
    english ? "Electricity tariff" : "Stromtarif",
  );
  await expect(plan.getByRole("heading", { level: 2 })).toHaveText(
    english ? "Charging plan" : "Ladeplanung",
  );
  await expect(plan).toContainText(
    english ? "last 30.0 minutes" : "letzten 30,0 Minuten",
  );
  await expect(plan).toContainText(
    english ? "an average of 1,000 W" : "durchschnittlich 1.000 W",
  );
  await expect(plan).toContainText(
    english
      ? "depleted by 14 Sept 2026, 02:00"
      : "bis 14.09.2026, 02:00 Uhr entleert",
  );
  await expect(plan).toContainText(
    english
      ? "low-tariff charging will start at 14 Sept 2026, 01:00"
      : "Aufladung im Niedertarif um 14.09.2026, 01:00 Uhr",
  );
  await expect(plan).toContainText(
    english
      ? "continue until 14 Sept 2026, 02:00"
      : "dauert voraussichtlich bis 14.09.2026, 02:00 Uhr",
  );
  await expect(plan).toContainText(
    english
      ? "PV starts at 14 Sept 2026, 07:00"
      : "PV-Start um 14.09.2026, 07:00 Uhr",
  );
  await expect(panel.locator(".time-window-control")).toHaveCount(0);
  await expect(
    panel.locator(".entity-control__name").filter({
      hasText: english ? "Grid charge min. SOC" : "Netzladung Min. SOC",
    }),
  ).toHaveCount(0);
  await expect(panel.locator(".tariff-plan")).toBeVisible();
  await expect(plan.getByRole("switch")).toHaveCount(0);

  for (const width of mobile ? [390, 320] : [1440, 1100]) {
    await page.setViewportSize({ width, height: mobile ? 844 : 1000 });
    await verifyCardGeometry(plan);
    await attachScreenshot(plan, testInfo, "planned", width);
  }

  await panel.evaluate((element) => {
    const host = element as HTMLElement & { hass: HomeAssistant };
    const entityId = "sensor.demo_bridge_charge_plan";
    const previous = host.hass.states[entityId];
    host.hass = {
      ...host.hass,
      states: {
        ...host.hass.states,
        [entityId]: {
          ...previous,
          state: "not_needed",
          attributes: {
            ...previous.attributes,
            discharge_at: "2026-09-14T06:00:00Z",
            charge_start: null,
            charge_end: null,
            target_soc: null,
          },
        },
      },
    };
  });
  await expect(plan).toContainText(
    english
      ? "No grid charging is needed"
      : "Eine Netzladung ist nicht erforderlich",
  );
  await expect(plan).toContainText(
    english
      ? "PV starts at 14 Sept 2026, 07:00"
      : "PV-Start um 14.09.2026, 07:00 Uhr",
  );
  await expect(plan).not.toContainText("01:00");
  await expect(plan).not.toContainText("02:00");
  await expect(panel.locator(".time-window-control")).toHaveCount(0);
  for (const width of mobile ? [390, 320] : [1440, 1100]) {
    await page.setViewportSize({ width, height: mobile ? 844 : 1000 });
    await verifyCardGeometry(plan);
    await attachScreenshot(plan, testInfo, "not-needed", width);
  }
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
  expect(errors).toEqual([]);
});
