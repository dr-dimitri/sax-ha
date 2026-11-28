import { expect, test, type Locator } from "@playwright/test";

const labels = {
  de: {
    tab: "Tarifvergleich",
    electricityTariff: "Stromtarif",
    consumption: "Jahresverbrauch (kWh)",
    addTariff: "Tarif hinzufügen",
    name: "Tarifname",
    type: "Tarifart",
    timeOfUse: "Zeitvariabel",
    price: "Arbeitspreis (ct/kWh)",
    standardPrice: "Standardpreis (ct/kWh)",
    baseFee: "Grundgebühr (€)",
    feePeriod: "Zeitraum der Grundgebühr",
    monthly: "Pro Monat",
    annual: "Pro Jahr",
    bonus: "Einmaliger Bonus (€)",
    addWindow: "Zeitfenster hinzufügen",
    window: "Zeitfenster",
    start: "Beginn",
    end: "Ende",
    share: "Verbrauchsanteil (%)",
    results: "Jahreskosten im Vergleich",
    standardConsumption: "Verbrauch zum Standardpreis",
    firstYear: "Kosten im ersten Jahr",
    laterYears: "Kosten pro Folgejahr",
    reset: "Zurücksetzen",
    totalShareTooHigh:
      "Die Verbrauchsanteile aller Zeitfenster dürfen zusammen höchstens 100 % betragen.",
  },
  en: {
    tab: "Tariff comparison",
    electricityTariff: "Electricity tariff",
    consumption: "Annual consumption (kWh)",
    addTariff: "Add tariff",
    name: "Tariff name",
    type: "Tariff type",
    timeOfUse: "Time of use",
    price: "Unit price (ct/kWh)",
    standardPrice: "Standard price (ct/kWh)",
    baseFee: "Standing charge (€)",
    feePeriod: "Standing charge period",
    monthly: "Per month",
    annual: "Per year",
    bonus: "One-time bonus (€)",
    addWindow: "Add time window",
    window: "Time window",
    start: "Start",
    end: "End",
    share: "Share of consumption (%)",
    results: "Annual cost comparison",
    standardConsumption: "Consumption at standard price",
    firstYear: "First-year cost",
    laterYears: "Cost per subsequent year",
    reset: "Reset",
    totalShareTooHigh:
      "The shares of all time windows together must be at most 100%.",
  },
} as const;

type Labels = (typeof labels)[keyof typeof labels];

async function addTariff(panel: Locator, copy: Labels, name: string) {
  await panel
    .getByRole("button", { name: copy.addTariff, exact: true })
    .click();
  await panel.getByLabel(copy.name, { exact: true }).last().fill(name);
  return panel.getByRole("article", { name, exact: true });
}

async function enterTime(field: Locator, time: string) {
  await field.fill("");
  await field.pressSequentially(time);
  await field.press("Tab");
  await expect(field).toHaveValue(time);
}

async function commitTime(field: Locator, time: string) {
  // A browser can commit the visible value without firing an input event.
  await field.evaluate((element: HTMLInputElement, value) => {
    element.value = value;
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }, time);
}

test.beforeEach(async ({ page }, testInfo) => {
  await page.goto("/sax-power-vue/tarifvergleich");
  if (testInfo.project.name.endsWith("en"))
    await page.locator("#language").click();
  if (testInfo.project.name.includes("dark"))
    await page.locator("#theme").click();
});

// REQ-VUE-TARIFF-COMPARISON: exercise the bundled calculator with no HA writes.
test("fixed and time-of-use tariffs compare first and later years from the same consumption", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const copy = labels[english ? "en" : "de"];
  const panel = page.locator("sax-power-vue-panel");
  await expect(panel.getByRole("heading", { level: 1 })).toHaveText(copy.tab);
  await panel.getByLabel(copy.consumption).fill("3600");

  const fixed = await addTariff(panel, copy, "Fest 30");
  await fixed.getByLabel(copy.price).fill(english ? "30.25" : "30,25");
  await fixed.getByLabel(copy.baseFee).fill("10");
  await fixed.getByLabel(copy.feePeriod).selectOption({ label: copy.monthly });
  await fixed.getByLabel(copy.bonus).fill("200");

  const variable = await addTariff(panel, copy, "Nacht & Mittag");
  await variable.getByLabel(copy.type).selectOption({ label: copy.timeOfUse });
  await variable.getByLabel(copy.standardPrice).fill("35");
  await variable.getByLabel(copy.baseFee).fill("84");
  await variable
    .getByLabel(copy.feePeriod)
    .selectOption({ label: copy.annual });
  await variable.getByRole("button", { name: copy.addWindow }).click();

  for (const [index, window] of [
    { start: "22:00", end: "06:00", price: "15", share: "30" },
    { start: "12:00", end: "14:00", price: "20", share: "20" },
  ].entries()) {
    const fields = variable.getByRole("group", {
      name: `${copy.window} ${index + 1}`,
      exact: true,
    });
    await enterTime(
      fields.getByLabel(copy.start, { exact: true }),
      window.start,
    );
    await enterTime(fields.getByLabel(copy.end, { exact: true }), window.end);
    await fields.getByLabel(copy.price).fill(window.price);
    await fields
      .getByLabel(copy.share)
      .fill(`${window.share}${english ? "." : ","}5`);
  }

  const comparison = panel.getByRole("table", { name: copy.results });
  const row = (name: string) =>
    comparison.getByRole("row").filter({
      has: page.getByRole("rowheader", { name, exact: true }),
    });
  await expect(
    comparison.getByRole("columnheader", { name: "Fest 30" }),
  ).toBeVisible();
  await expect(
    comparison.getByRole("columnheader", { name: "Nacht & Mittag" }),
  ).toBeVisible();
  if (testInfo.project.name.startsWith("mobile")) {
    const region = panel.getByRole("region", { name: copy.results });
    expect(
      await region.evaluate((element) => element.scrollWidth),
    ).toBeLessThanOrEqual(
      await region.evaluate((element) => element.clientWidth),
    );
  }
  await expect(
    row(copy.standardConsumption).getByRole("cell").last(),
  ).toContainText("49");
  const currency = new Intl.NumberFormat(english ? "en-GB" : "de-DE", {
    style: "currency",
    currency: "EUR",
  });
  for (const [label, expected] of [
    [copy.firstYear, [1009, 1013.7]],
    [copy.laterYears, [1209, 1013.7]],
  ] as const) {
    const cells = row(label).getByRole("cell");
    await expect(cells.nth(0)).toContainText(currency.format(expected[0]));
    await expect(cells.nth(1)).toContainText(currency.format(expected[1]));
  }
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});

test("incomplete and conflicting window inputs keep their drafts and resetting clears the tariffs", async ({
  page,
}, testInfo) => {
  const english = testInfo.project.name.endsWith("en");
  const copy = labels[english ? "en" : "de"];
  const panel = page.locator("sax-power-vue-panel");
  const consumption = panel.getByLabel(copy.consumption);
  await consumption.fill("4200");
  const tariff = await addTariff(panel, copy, "Wochenangebot");
  await tariff.getByLabel(copy.type).selectOption({ label: copy.timeOfUse });
  await tariff.getByLabel(copy.standardPrice).fill("35");
  await tariff.getByLabel(copy.baseFee).fill("0");
  await tariff.getByRole("button", { name: copy.addWindow }).click();

  const first = tariff.getByRole("group", {
    name: `${copy.window} 1`,
    exact: true,
  });
  const second = tariff.getByRole("group", {
    name: `${copy.window} 2`,
    exact: true,
  });
  const firstStart = first.getByLabel(copy.start, { exact: true });
  await firstStart.pressSequentially("22");
  await firstStart.press("Tab");
  await expect(firstStart).toHaveValue("22");
  await expect(firstStart).toHaveAttribute("aria-invalid", "true");
  await enterTime(firstStart, "22:00");
  await expect(firstStart).not.toHaveAttribute("aria-invalid", "true");
  await enterTime(first.getByLabel(copy.end, { exact: true }), "06:00");
  await first.getByLabel(copy.price).fill("10");
  await first.getByLabel(copy.share).fill("60");

  const secondStart = second.getByLabel(copy.start, { exact: true });
  const secondEnd = second.getByLabel(copy.end, { exact: true });
  await enterTime(secondStart, "00:00");
  await enterTime(secondEnd, "08:00");
  await second.getByLabel(copy.price).fill("15");
  await second.getByLabel(copy.share).fill("40");
  await expect(secondStart).toHaveAttribute("aria-invalid", "true");
  await commitTime(secondStart, "06:00");
  await expect(secondStart).not.toHaveAttribute("aria-invalid", "true");
  await commitTime(secondEnd, "06:00");
  await expect(secondEnd).toHaveAttribute("aria-invalid", "true");
  await enterTime(secondEnd, "08:00");
  await expect(secondEnd).not.toHaveAttribute("aria-invalid", "true");

  const secondShare = second.getByLabel(copy.share);
  await secondShare.fill("41");
  await secondShare.press("Tab");
  const totalError = tariff.getByText(copy.totalShareTooHigh, { exact: true });
  await expect(totalError).toBeVisible();
  await secondShare.fill("40");
  await expect(totalError).toHaveCount(0);

  await panel
    .getByRole("link", { name: copy.electricityTariff, exact: true })
    .click();
  await expect(tariff).toBeHidden();
  await panel.getByRole("link", { name: copy.tab, exact: true }).click();
  await expect(consumption).toHaveValue("4200");
  await expect(firstStart).toHaveValue("22:00");
  await expect(secondShare).toHaveValue("40");

  await addTariff(panel, copy, "Weiteres Angebot");
  await panel.getByRole("button", { name: copy.reset, exact: true }).click();
  await expect(panel.getByLabel(copy.name, { exact: true })).toHaveCount(0);
  await expect(panel.getByRole("table", { name: copy.results })).toHaveCount(0);
  await expect(consumption).toHaveValue("4200");
  await addTariff(panel, copy, "Nur für diese Sitzung");
  await page.reload();
  await expect(panel.getByRole("heading", { level: 1 })).toHaveText(
    labels.de.tab,
  );
  await expect(panel.getByLabel(labels.de.name, { exact: true })).toHaveCount(
    0,
  );
  await expect(panel.getByLabel(labels.de.consumption)).toHaveValue("");
  await expect(page.locator("#actions")).toHaveText("Keine Aktion");
});
