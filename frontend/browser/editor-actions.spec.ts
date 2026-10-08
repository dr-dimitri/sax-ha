import { expect, test, type Locator } from "@playwright/test";

async function expectPairs(panel: Locator) {
  const pairs = await panel.locator(".editor-actions").evaluateAll((groups) =>
    groups.flatMap((group) => {
      const buttons = [
        ...group.querySelectorAll<HTMLButtonElement>(":scope > button"),
      ];
      if (buttons.length < 2 || !group.getBoundingClientRect().height)
        return [];
      return [
        {
          labels: buttons.map((button) => button.textContent?.trim()),
          boxes: buttons.map((button) => {
            const rect = button.getBoundingClientRect();
            return {
              left: rect.left,
              right: rect.right,
              top: rect.top,
              height: rect.height,
            };
          }),
          parentRight: group.parentElement!.getBoundingClientRect().right,
        },
      ];
    }),
  );
  expect(pairs.length).toBeGreaterThan(0);
  for (const { labels, boxes, parentRight } of pairs) {
    expect(labels).toHaveLength(2);
    expect(labels[0]).toMatch(
      /^(Übernehmen|Tarif übernehmen|Apply|Apply tariff)$/,
    );
    expect(labels[1]).toMatch(/^(Abbrechen|Cancel)$/);
    expect(Math.abs(boxes[0].top - boxes[1].top)).toBeLessThan(1);
    expect(boxes[1].left - boxes[0].right).toBeGreaterThanOrEqual(0);
    expect(boxes[1].left - boxes[0].right).toBeLessThanOrEqual(12);
    expect(boxes[1].right).toBeLessThanOrEqual(parentRight + 1);
    expect(boxes.every((box) => box.height >= 44)).toBe(true);
  }
  const isolated = await panel
    .getByRole("button", {
      name: /^(Übernehmen|Tarif übernehmen|Apply|Apply tariff|Abbrechen|Cancel)$/,
    })
    .evaluateAll((buttons) =>
      buttons
        .filter(
          (button) =>
            button.getBoundingClientRect().height &&
            (!button.parentElement?.classList.contains("editor-actions") ||
              button.parentElement.children.length !== 2),
        )
        .map((button) => button.textContent),
    );
  expect(isolated).toEqual([]);
}

test("all editors pair Apply on the left with Cancel on the right without wrapping", async ({
  page,
}, testInfo) => {
  if (testInfo.project.name.startsWith("mobile"))
    await page.setViewportSize({ width: 320, height: 844 });
  await page.goto("/sax-power-vue/allgemein");
  const english = testInfo.project.name.endsWith("en");
  if (english) await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
  const panel = page.locator("sax-power-vue-panel");
  const cancel = english ? "Cancel" : "Abbrechen";
  const edit = english ? "Edit" : "Bearbeiten";
  await expectPairs(panel);
  await panel.locator(".entity-control:has(dialog) input").click();
  await expect(panel.locator("dialog")).toBeVisible();
  await expectPairs(panel);
  await panel
    .locator("dialog")
    .getByRole("button", { name: cancel, exact: true })
    .click();
  await panel.locator("nav a[href$='/netzdienliches-laden']").click();
  await panel
    .locator(".grid-serving-source")
    .getByRole("button", { name: edit, exact: true })
    .click();
  await expectPairs(panel);
  const times = panel.locator(".time-window-control input");
  const confirmed = await times.evaluateAll((inputs) =>
    inputs.map((input) => (input as HTMLInputElement).value),
  );
  await times.first().fill("12");
  await panel
    .locator(".time-window-control")
    .getByRole("button", { name: cancel, exact: true })
    .click();
  expect(
    await times.evaluateAll((inputs) =>
      inputs.map((input) => (input as HTMLInputElement).value),
    ),
  ).toEqual(confirmed);
  await panel
    .locator(".grid-serving-source")
    .getByRole("button", { name: cancel, exact: true })
    .click();
  for (const dynamic of [false, true]) {
    await panel.locator("nav a[href$='/stromtarif']").click();
    if (dynamic) await page.locator("#tariff-dynamic").click();
    await panel
      .getByRole("button", {
        name: english ? "Change tariff" : "Tarif wechseln",
        exact: true,
      })
      .click();
    await expectPairs(panel);
    await panel
      .locator(".electricity-choice")
      .getByRole("button", { name: cancel, exact: true })
      .click();
    for (const selector of [
      ".electricity-price-card",
      ".electricity-charging",
    ]) {
      const section = panel.locator(selector);
      await section.getByRole("button", { name: edit, exact: true }).click();
      await expectPairs(panel);
      await expect(
        section.getByRole("button", { name: cancel, exact: true }),
      ).toHaveCount(2);
      await section
        .locator("header")
        .getByRole("button", { name: cancel, exact: true })
        .click();
    }
  }
  await page.locator("#tariff-timed").click();
  await panel.locator("nav a[href$='/ersparnis']").click();
  const tariff = panel.locator(".tariff-plan");
  await tariff.getByRole("button", { name: edit, exact: true }).click();
  await expectPairs(panel);
  await tariff
    .locator("header")
    .getByRole("button", { name: cancel, exact: true })
    .click();
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});
