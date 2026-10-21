import { computed } from "vue";
import type { SaxDashboard } from "./ha";

export function useChargingMonths(dashboard: SaxDashboard | undefined) {
  const monthKeys = Array.from(
    { length: 12 },
    (_, index) => `timed_charge_month_${index + 1}`,
  );
  const monthSummary = computed(() => {
    const german = dashboard?.language.value === "de";
    const unknownText = german
      ? "Monatsauswahl nicht vollständig bekannt"
      : "Month selection is not fully known";
    const formatter = new Intl.DateTimeFormat(german ? "de" : "en", {
      month: "short",
      timeZone: "UTC",
    });
    const months = monthKeys.map((key, index) => {
      const entity = dashboard?.entity("switch", key);
      const state = entity?.state?.state;
      return {
        known: entity?.available && (state === "on" || state === "off"),
        selected: entity?.available && state === "on",
        name: formatter.format(new Date(Date.UTC(2024, index, 1))),
      };
    });
    const chosen = months.filter((month) => month.selected);
    const unknown = months.some((month) => !month.known);
    if (chosen.length === 12) return german ? "Ganzjährig" : "All year";
    if (!chosen.length)
      return unknown
        ? unknownText
        : german
          ? "Keine ausgewählt · Automatische Netzladung ganzjährig inaktiv"
          : "None selected · Automatic grid charging inactive all year";
    return `${chosen.map((month) => month.name).join(", ")}${unknown ? ` · ${unknownText}` : ""}`;
  });
  return { monthKeys, monthSummary };
}
