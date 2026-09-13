import type { TariffPriceSeries } from "./types";

export function tariffChart(series: TariffPriceSeries | null, width = 1000) {
  const start = Date.parse(series?.start ?? "");
  const end = Date.parse(series?.end ?? "");
  const validDay =
    Number.isFinite(start) && Number.isFinite(end) && end > start;
  const slots = validDay
    ? (series?.slots ?? [])
        .flatMap((slot) => {
          const from = Date.parse(slot.start),
            to = Date.parse(slot.end);
          return Number.isFinite(from) &&
            Number.isFinite(to) &&
            to > from &&
            from >= start &&
            to <= end &&
            Number.isFinite(slot.price_ct_kwh)
            ? [{ ...slot, from, to }]
            : [];
        })
        .sort((a, b) => a.from - b.from)
    : [];
  // REQ-VUE-ELECTRICITY-TARIFF: gaps and malformed overlapping data never become invented prices.
  if (
    slots.some((slot, index) => index > 0 && slot.from < slots[index - 1]!.to)
  )
    slots.splice(0);
  const low = Math.min(0, ...slots.map((slot) => slot.price_ct_kwh));
  const high = Math.max(0, ...slots.map((slot) => slot.price_ct_kwh));
  const padding = Math.max(1, (high - low) * 0.12);
  const min = low - padding,
    max = high + padding;
  const x = (time: number) =>
    48 + ((time - start) / (end - start)) * (width - 60);
  const y = (price: number) => 26 + ((max - price) / (max - min)) * 184;
  let path = "";
  slots.forEach((slot, index) => {
    const previous = slots[index - 1];
    path +=
      previous && previous.to === slot.from
        ? ` V ${y(slot.price_ct_kwh)}`
        : ` M ${x(slot.from)} ${y(slot.price_ct_kwh)}`;
    path += ` H ${x(slot.to)}`;
  });
  return {
    start,
    end,
    slots,
    min,
    max,
    x,
    y,
    path,
    ticks: [...new Set([low, 0, low + (high - low) / 2, high])].sort(
      (a, b) => a - b,
    ),
  };
}
