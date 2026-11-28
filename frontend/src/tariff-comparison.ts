import { normalizeTime, timeSeconds } from "./time";

export interface ComparisonTariffWindowInput {
  start: string;
  end: string;
  price: string;
  share: string;
}

export interface ComparisonTariffInput {
  type: "fixed" | "time-of-use";
  price: string;
  baseFee: string;
  baseFeePeriod: "monthly" | "yearly";
  bonus: string;
  windows: readonly ComparisonTariffWindowInput[];
}

export type ComparisonTariffError =
  | "required"
  | "invalidNumber"
  | "negative"
  | "outOfRange"
  | "invalidTime"
  | "sameTime"
  | "overlap"
  | "notDiscounted"
  | "shareTooHigh"
  | "totalShareTooHigh"
  | "missingWindow";

export interface ComparisonTariffErrors {
  annualConsumption?: ComparisonTariffError;
  price?: ComparisonTariffError;
  baseFee?: ComparisonTariffError;
  bonus?: ComparisonTariffError;
  windows?: ComparisonTariffError;
  windowFields: Array<
    Partial<Record<keyof ComparisonTariffWindowInput, ComparisonTariffError>>
  >;
}

export type ComparisonTariffCalculation =
  | {
      valid: true;
      annualEnergyCost: number;
      annualBaseFee: number;
      annualCost: number;
      firstYearCost: number;
      bonus: number;
      standardShare: number;
    }
  | { valid: false; errors: ComparisonTariffErrors };

type Decimal = { coefficient: bigint; scale: number };

type ParsedNumber =
  | { value: Decimal; error?: never }
  | { value: null; error: ComparisonTariffError };

type WindowSegment = { start: number; end: number; windowIndex: number };

const SECONDS_PER_DAY = 24 * 60 * 60;
const ZERO: Decimal = { coefficient: 0n, scale: 0 };
const FULL_SHARE: Decimal = { coefficient: 100n, scale: 0 };

function parseNumber(input: string, optional = false): ParsedNumber {
  const decimal = input.trim().replace(",", ".");
  if (!decimal) {
    return optional ? { value: ZERO } : { value: null, error: "required" };
  }
  // Keep exact arithmetic bounded even when a long value is pasted.
  if (decimal.length > 1000) return { value: null, error: "outOfRange" };
  if (!/^-?(?:\d+(?:\.\d+)?|\.\d+)$/.test(decimal)) {
    return { value: null, error: "invalidNumber" };
  }
  if (decimal.startsWith("-")) return { value: null, error: "negative" };
  if (!Number.isFinite(Number(decimal))) {
    return { value: null, error: "outOfRange" };
  }
  const [whole, fraction = ""] = decimal.split(".");
  return {
    value: {
      coefficient: BigInt(`${whole || "0"}${fraction}`),
      scale: fraction.length,
    },
  };
}

export function validateAnnualConsumption(
  value: string,
): ComparisonTariffError | undefined {
  return parseNumber(value).error;
}

function add(first: Decimal, second: Decimal): Decimal {
  const scale = Math.max(first.scale, second.scale);
  const coefficient =
    first.coefficient * 10n ** BigInt(scale - first.scale) +
    second.coefficient * 10n ** BigInt(scale - second.scale);
  return { coefficient, scale };
}

function subtract(first: Decimal, second: Decimal): Decimal {
  return add(first, { coefficient: -second.coefficient, scale: second.scale });
}

function multiply(first: Decimal, second: Decimal): Decimal {
  return {
    coefficient: first.coefficient * second.coefficient,
    scale: first.scale + second.scale,
  };
}

function toNumber(value: Decimal): number {
  return Number(`${value.coefficient}e-${value.scale}`);
}

function roundedEuro(value: Decimal): number {
  if (value.scale <= 2) return toNumber(value);
  const divisor = 10n ** BigInt(value.scale - 2);
  const sign = value.coefficient < 0n ? -1n : 1n;
  const cents = (value.coefficient * sign + divisor / 2n) / divisor;
  return toNumber({ coefficient: cents * sign, scale: 2 });
}

function markOverlaps(
  segments: WindowSegment[],
  windowFields: ComparisonTariffErrors["windowFields"],
): void {
  segments.sort((first, second) => first.start - second.start);
  let latest: WindowSegment | undefined;
  for (const segment of segments) {
    if (latest && segment.start < latest.end) {
      for (const index of [latest.windowIndex, segment.windowIndex]) {
        windowFields[index]!.start = "overlap";
        windowFields[index]!.end = "overlap";
      }
    }
    if (!latest || segment.end > latest.end) latest = segment;
  }
}

export function calculateTariffComparison(
  annualConsumptionInput: string,
  tariff: ComparisonTariffInput,
): ComparisonTariffCalculation {
  const annualConsumption = parseNumber(annualConsumptionInput);
  const price = parseNumber(tariff.price);
  const baseFee = parseNumber(tariff.baseFee);
  const bonus = parseNumber(tariff.bonus, true);
  const errors: ComparisonTariffErrors = { windowFields: [] };
  if (annualConsumption.error)
    errors.annualConsumption = annualConsumption.error;
  if (price.error) errors.price = price.error;
  if (baseFee.error) errors.baseFee = baseFee.error;
  if (bonus.error) errors.bonus = bonus.error;

  let standardShare = FULL_SHARE;
  let discountedPrice = ZERO;
  if (tariff.type === "time-of-use") {
    if (tariff.windows.length === 0) errors.windows = "missingWindow";
    const segments: WindowSegment[] = [];
    tariff.windows.forEach((window, windowIndex) => {
      const fields: ComparisonTariffErrors["windowFields"][number] = {};
      errors.windowFields.push(fields);
      const start = timeSeconds(normalizeTime(window.start));
      const end = timeSeconds(normalizeTime(window.end));
      if (start === null)
        fields.start = window.start.trim() ? "invalidTime" : "required";
      if (end === null)
        fields.end = window.end.trim() ? "invalidTime" : "required";
      if (start !== null && end !== null) {
        if (start === end) {
          fields.end = "sameTime";
        } else if (start < end) {
          segments.push({ start, end, windowIndex });
        } else {
          segments.push({ start, end: SECONDS_PER_DAY, windowIndex });
          if (end > 0) segments.push({ start: 0, end, windowIndex });
        }
      }

      const windowPrice = parseNumber(window.price);
      if (windowPrice.error) fields.price = windowPrice.error;
      else if (
        price.value !== null &&
        subtract(windowPrice.value, price.value).coefficient >= 0n
      ) {
        fields.price = "notDiscounted";
      }

      const share = parseNumber(window.share);
      if (share.error) {
        fields.share = share.error;
      } else if (subtract(FULL_SHARE, share.value).coefficient < 0n) {
        fields.share = "shareTooHigh";
      } else {
        standardShare = subtract(standardShare, share.value);
        if (windowPrice.value !== null) {
          discountedPrice = add(
            discountedPrice,
            multiply(windowPrice.value, share.value),
          );
        }
      }
    });
    markOverlaps(segments, errors.windowFields);
    if (standardShare.coefficient < 0n) errors.windows = "totalShareTooHigh";
  }

  if (
    annualConsumption.value === null ||
    price.value === null ||
    baseFee.value === null ||
    bonus.value === null ||
    errors.windows ||
    errors.windowFields.some((fields) => Object.keys(fields).length > 0)
  ) {
    return { valid: false, errors };
  }

  const weightedPrice = add(
    multiply(price.value, standardShare),
    discountedPrice,
  );
  // Convert both the price from cents to euros and the share from percent.
  const energy = multiply(annualConsumption.value, {
    ...weightedPrice,
    scale: weightedPrice.scale + 4,
  });
  const fee = {
    ...baseFee.value,
    coefficient:
      baseFee.value.coefficient *
      (tariff.baseFeePeriod === "monthly" ? 12n : 1n),
  };
  const total = add(energy, fee);
  // Round each displayed amount from its exact value, including both totals.
  const annualEnergyCost = roundedEuro(energy);
  const annualBaseFee = roundedEuro(fee);
  const annualCost = roundedEuro(total);
  if (!Number.isFinite(annualEnergyCost)) errors.price = "outOfRange";
  if (!Number.isFinite(annualBaseFee)) errors.baseFee = "outOfRange";
  if (errors.price || errors.baseFee) return { valid: false, errors };
  if (!Number.isFinite(annualCost)) {
    errors.price = "outOfRange";
    return { valid: false, errors };
  }

  return {
    valid: true,
    annualEnergyCost,
    annualBaseFee,
    annualCost,
    firstYearCost: roundedEuro(subtract(total, bonus.value)),
    bonus: roundedEuro(bonus.value),
    standardShare: toNumber(standardShare),
  };
}
