import { describe, expect, it } from "vitest";
import {
  calculateTariffComparison,
  normalizeComparisonTime,
  validateAnnualConsumption,
  type ComparisonTariffInput,
  type ComparisonTariffWindowInput,
} from "../src/tariff-comparison";

const fixedTariff: ComparisonTariffInput = {
  type: "fixed",
  price: "30,50",
  baseFee: "12.50",
  baseFeePeriod: "monthly",
  bonus: "80",
  windows: [],
};

const nightWindow: ComparisonTariffWindowInput = {
  start: "22:00",
  end: "06:00",
  price: "19.25",
  share: "25,5",
};

function timeOfUse(
  windows: ComparisonTariffInput["windows"],
): ComparisonTariffInput {
  return {
    type: "time-of-use",
    price: "32,4",
    baseFee: "120",
    baseFeePeriod: "yearly",
    bonus: "90",
    windows,
  };
}

describe("tariff comparison", () => {
  it.each([
    ["0", "00:00"],
    [" 07 ", "07:00"],
    ["9", "09:00"],
    ["23", "23:00"],
    ["0730", "07:30"],
    ["12:15", "12:15"],
    ["24", "24"],
    ["26", "26"],
    ["2:", "2:"],
    ["12:4", "12:4"],
  ])("normalizes a time window input from %j to %j", (input, value) => {
    expect(normalizeComparisonTime(input)).toBe(value);
  });

  it("calculates fixed annual costs with a monthly fee and a first-year bonus", () => {
    expect(calculateTariffComparison("4000", fixedTariff)).toEqual({
      valid: true,
      annualEnergyCost: 1220,
      annualBaseFee: 150,
      annualCost: 1370,
      firstYearCost: 1290,
      bonus: 80,
      standardShare: 100,
      firstYearAtZero: 70,
      standardAtZero: 150,
      annualCostPerKwh: 0.305,
      costAtConsumption: expect.any(Function),
    });
  });

  it("accepts zero consumption and an empty bonus and ignores inactive windows", () => {
    expect(
      calculateTariffComparison("0", {
        ...fixedTariff,
        bonus: " ",
        windows: [{ start: "", end: "", price: "", share: "" }],
      }),
    ).toMatchObject({
      valid: true,
      annualEnergyCost: 0,
      annualCost: 150,
      firstYearCost: 150,
      bonus: 0,
    });
  });

  it("uses consumption shares for adjacent windows and the standard price for the remainder", () => {
    const result = calculateTariffComparison(
      "4200",
      timeOfUse([
        { start: "0600", end: "07:00", price: "21", share: "14.5" },
        nightWindow,
      ]),
    );
    expect(result.valid).toBe(true);
    if (!result.valid) return;
    expect(result.standardShare).toBe(60);
    expect(result.annualEnergyCost).toBe(1150.54);
    expect(result.annualBaseFee).toBe(120);
    expect(result.annualCost).toBe(1270.54);
    expect(result.firstYearCost).toBe(1180.54);
  });

  it("uses windows costing more than or as much as the standard price", () => {
    const result = calculateTariffComparison("1000", {
      ...timeOfUse([
        { start: "22", end: "0", price: "40", share: "20" },
        { start: "00", end: "06", price: "30", share: "15" },
      ]),
      price: "30",
    });
    expect(result).toMatchObject({
      valid: true,
      annualEnergyCost: 320,
      annualCost: 440,
      firstYearCost: 350,
      standardShare: 65,
      annualCostPerKwh: 0.32,
      standardAtZero: 120,
      firstYearAtZero: 30,
    });
    if (!result.valid) throw new Error("Expected a valid tariff");
    expect(result.costAtConsumption(2000, true)).toBe(670);
    expect(result.costAtConsumption(2000, false)).toBe(760);
  });

  it("rounds exact half cents away from zero for both comparison and inspection", () => {
    const result = calculateTariffComparison("1000", {
      ...timeOfUse([{ ...nightWindow, price: "10.13", share: "34.5" }]),
      price: "20,23",
      baseFee: "99.99",
      bonus: "267.45",
    });
    expect(result).toMatchObject({
      valid: true,
      annualEnergyCost: 167.46,
      annualBaseFee: 99.99,
      annualCost: 267.45,
      firstYearCost: -0.01,
    });
    if (!result.valid) throw new Error("Expected a valid tariff");
    expect(result.costAtConsumption(1000, true)).toBe(-0.01);
    expect(result.costAtConsumption(1000, false)).toBe(267.45);
    expect(result.costAtConsumption(0, true)).toBe(-167.46);
    expect(result.costAtConsumption(1e-7, false)).toBe(99.99);
    expect(result.costAtConsumption(Infinity, true)).toBeNull();
  });

  it("accepts an exact 100 percent with multiple decimal shares", () => {
    const windows = Array.from({ length: 12 }, (_, index) => ({
      start: `${String(index).padStart(2, "0")}:00`,
      end: `${String(index + 1).padStart(2, "0")}:00`,
      price: "20",
      share: index === 11 ? "98.9" : "0,1",
    }));
    expect(calculateTariffComparison("1000", timeOfUse(windows))).toMatchObject(
      { valid: true, standardShare: 0, annualCost: 320 },
    );
  });

  it("allows a window ending at midnight and a window starting there", () => {
    expect(
      calculateTariffComparison(
        "1000",
        timeOfUse([
          { ...nightWindow, end: "00:00", share: "25" },
          { ...nightWindow, start: "00:00", share: "25" },
        ]),
      ),
    ).toMatchObject({ valid: true, standardShare: 50 });
  });

  it("identifies all overlapping windows, including those contained in an overnight window", () => {
    expect(
      calculateTariffComparison(
        "1000",
        timeOfUse([
          { ...nightWindow, start: "1", end: "02" },
          nightWindow,
          { ...nightWindow, start: "03:00", end: "04:00" },
          { ...nightWindow, start: "06:00", end: "08:00", share: "0" },
        ]),
      ),
    ).toEqual({
      valid: false,
      errors: {
        windowFields: [
          { start: "overlap", end: "overlap" },
          { start: "overlap", end: "overlap" },
          { start: "overlap", end: "overlap" },
          {},
        ],
      },
    });
  });

  it("rejects a combined share above 100 percent even below floating-point precision", () => {
    expect(
      calculateTariffComparison(
        "1000",
        timeOfUse([
          { ...nightWindow, share: "99.9" },
          {
            ...nightWindow,
            start: "08:00",
            end: "09:00",
            share: "0.10000000000000001",
          },
        ]),
      ),
    ).toMatchObject({ valid: false, errors: { windows: "totalShareTooHigh" } });
  });

  it("identifies missing and invalid input fields", () => {
    const result = calculateTariffComparison("", {
      ...timeOfUse([
        { start: "24", end: "", price: "32.4", share: "100.1" },
        { start: "00:00", end: "0000", price: "-4", share: "2e0" },
      ]),
      baseFee: "abc",
      bonus: "-0.50",
    });
    expect(result).toEqual({
      valid: false,
      errors: {
        annualConsumption: "required",
        baseFee: "invalidNumber",
        bonus: "negative",
        windowFields: [
          {
            start: "invalidTime",
            end: "required",
            share: "shareTooHigh",
          },
          { end: "sameTime", price: "negative", share: "invalidNumber" },
        ],
      },
    });
  });

  it("requires at least one price window for a time-of-use tariff", () => {
    expect(calculateTariffComparison("1000", timeOfUse([]))).toEqual({
      valid: false,
      errors: { windows: "missingWindow", windowFields: [] },
    });
  });

  it("reports overflow during annualization and validates consumption independently", () => {
    expect(validateAnnualConsumption("1234,56")).toBeUndefined();
    expect(validateAnnualConsumption("-1")).toBe("negative");
    expect(validateAnnualConsumption("9".repeat(309))).toBe("outOfRange");
    expect(validateAnnualConsumption(`0.${"0".repeat(999)}`)).toBe(
      "outOfRange",
    );
    expect(
      calculateTariffComparison("1000", {
        ...fixedTariff,
        baseFee: "9".repeat(308),
      }),
    ).toMatchObject({ valid: false, errors: { baseFee: "outOfRange" } });
    expect(
      calculateTariffComparison("9".repeat(308), {
        ...fixedTariff,
        price: "10000",
      }),
    ).toMatchObject({ valid: false, errors: { price: "outOfRange" } });
  });
});
