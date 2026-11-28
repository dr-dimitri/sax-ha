<script setup lang="ts">
import { computed, inject, useId } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import {
  finiteValue,
  formatSavingsDate,
  formatSavingsNumber,
} from "../savings";
import type { HomeAssistant } from "../types";
import { timeSeconds } from "../time";

const props = defineProps<{ hass?: HomeAssistant; automatic?: boolean }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const id = useId();
const german = computed(() => dashboard?.language.value === "de");
const plan = computed(() => dashboard?.entity("sensor", "bridge_charge_plan"));
const allLowTariffs = computed(() => {
  const tariff = dashboard?.tariff.value;
  return (
    tariff?.tariff_type === "time_of_use" &&
    tariff.all_low_tariffs_enabled === true
  );
});
const control = computed(() =>
  dashboard?.entity("switch", "bridge_charge_enabled"),
);
const attributes = computed(() => plan.value?.state?.attributes ?? {});
const fixedTimeStart = computed(() => {
  const fixed = dashboard?.tariff.value?.fixed_time_charging;
  if (!fixed?.enabled || !fixed.start || timeSeconds(fixed.start) === null)
    return null;
  return fixed.start.endsWith(":00") && fixed.start.length === 8
    ? fixed.start.slice(0, 5)
    : fixed.start;
});
const fixedTimeLabel = computed(() =>
  fixedTimeStart.value
    ? german.value
      ? `Feste Startzeit ${fixedTimeStart.value} Uhr`
      : `Scheduled start ${fixedTimeStart.value}`
    : null,
);
const discharge = computed(() =>
  dashboard?.entity("sensor", "discharge_forecast"),
);
const configurationHint = computed(() => {
  if (
    !control.value?.available ||
    control.value.state?.state !== "on" ||
    chargingActive.value
  )
    return null;
  switch (control.value?.state?.attributes.configuration_error) {
    case "bridge_pv_start_required":
      return german.value
        ? "Unter „Preise & Zeiten“ eine PV-Prognosequelle auswählen."
        : "Select a solar forecast source under “Prices & times”.";
    case "bridge_tariff_required":
      return german.value
        ? "Unter „Preise & Zeiten“ einen zeitvariablen Tarif einrichten."
        : "Configure a time-of-use tariff under “Prices & times”.";
    default:
      return null;
  }
});
const text = computed(() =>
  german.value
    ? {
        title: "Ladeplanung",
        allLowTariffs:
          "Ladestart in jedem Zeitfenster unter dem Standardpreis, sofern Netzladeziel und Schutzgrenzen es zulassen.",
        noCharge: "Keine Ladung nötig",
        chargeNeeded: "Ladung voraussichtlich nötig",
        charging: "Ladung läuft",
        demandUnknown: "Ladebedarf offen",
        conflict: "Reichweite und Ladeplan weichen ab",
        unavailable: "Planstatus unbekannt",
        postChargeWaiting:
          "Nach Ladeende wird der Bedarf mit neuen Verbrauchsdaten geprüft.",
        incomplete: "Ladezeiten noch unvollständig.",
        waiting: "Gültige Planungsdaten fehlen.",
        paused: "Netzladung pausiert.",
        complete: "Netzladung beendet.",
        completionPending:
          "Netzladung beendet. Fehlmenge ohne aktuelle Batteriedaten noch unbekannt.",
        unconfirmed: "Ladefluss noch unbestätigt.",
        noWindow: "Kein nutzbares Ladefenster im Niedertarif.",
        charge: "Netzladung",
        partial: "Teilladung",
        lowTariff: "im Niedertarif",
        firstTariff: "im ersten nutzbaren Niedertarif",
        emptyBattery: "Akku bei 0 %.",
      }
    : {
        title: "Charging plan",
        allLowTariffs:
          "Charging starts in every window below the standard price, subject to the grid charge target and protection limits.",
        noCharge: "No charging needed",
        chargeNeeded: "Charging likely needed",
        charging: "Charging in progress",
        demandUnknown: "Charging need unknown",
        conflict: "Battery forecast and plan disagree",
        unavailable: "Plan status unavailable",
        postChargeWaiting:
          "Demand after charging is assessed from fresh consumption readings.",
        incomplete: "Charging times are incomplete.",
        waiting: "Valid planning data is missing.",
        paused: "Grid charging paused.",
        complete: "Grid charging ended.",
        completionPending:
          "Grid charging ended. The shortfall is unknown until new battery readings arrive.",
        unconfirmed: "Charging power not yet confirmed.",
        noWindow: "No usable low-tariff charging window.",
        charge: "Grid charge",
        partial: "Partial charge",
        lowTariff: "at low tariff",
        firstTariff: "in the first available low-tariff window",
        emptyBattery: "Battery at 0%.",
      },
);
const status = computed(() =>
  plan.value?.available ? plan.value.state?.state : "unavailable",
);
const chargingActive = computed(
  () =>
    ["charging", "off"].includes(status.value ?? "") &&
    attributes.value.charging_active === true,
);
const fixedTargetLabel = computed(() => {
  const tariff = dashboard?.tariff.value;
  if (
    !props.automatic ||
    tariff?.tariff_type !== "time_of_use" ||
    tariff.fixed_time_charging?.enabled ||
    status.value !== "off" ||
    !control.value?.available ||
    control.value.state?.state !== "off"
  )
    return null;
  const entity = dashboard?.entity("number", "timed_charge_min_soc");
  const threshold = entity?.available ? finiteValue(entity.state?.state) : null;
  if (
    threshold === null ||
    !Number.isInteger(threshold) ||
    threshold < 0 ||
    threshold > 100
  )
    return null;
  const start = timestamp(attributes.value.empty_battery_start);
  if (start)
    return german.value
      ? `Akku bei 0 % – Ladestart zum Niedertarifbeginn am ${start} Uhr`
      : `Battery at 0% – charging planned for the start of low tariff on ${start}`;
  if (attributes.value.empty_battery_start_due === true)
    return german.value
      ? "Akku bei 0 % – Netzladung im Niedertarif freigegeben"
      : "Battery at 0% – grid charging permitted during this low-tariff period";
  if (threshold === 0)
    return german.value
      ? "Start im Niedertarif bei 0 % Akkustand"
      : "Starts during low-tariff hours at 0% battery charge";
  return german.value
    ? `Start im Niedertarif bei unter ${threshold} % Akkustand`
    : `Low-tariff charging below ${threshold}% battery charge`;
});
const reasons = computed<Record<string, string>>(() =>
  german.value
    ? {
        pv_start_missing:
          "Die PV-Prognose bestätigt noch keine 30 Minuten mit genug Solarstrom für den Verbrauch. Quelle unter „Preise & Zeiten“ prüfen.",
        consumption_missing:
          "Für die Prognose ist mindestens eine Minute Verbrauchsmessung nötig.",
        measurements_missing: "Aktuelle Batteriemesswerte fehlen.",
        calibration: "Batteriekalibrierung hat Vorrang.",
        pv_surplus: "PV-Überschuss vorhanden.",
        manual_charge: "Manuelle Ladung hat Vorrang.",
        soc_limit: "SOC-Grenze erreicht.",
      }
    : {
        pv_start_missing:
          "The forecast has yet to show 30 minutes of solar power covering consumption. Check the source under “Prices & times”.",
        consumption_missing:
          "The forecast needs at least one minute of consumption readings.",
        measurements_missing: "Current battery readings are missing.",
        calibration: "Battery calibration takes priority.",
        pv_surplus: "Surplus solar power available.",
        manual_charge: "Manual charging takes priority.",
        soc_limit: "Battery charge limit reached.",
      },
);
const reason = computed(() => {
  const code = attributes.value.reason;
  if (configurationHint.value && code === "pv_start_missing") return null;
  return typeof code === "string" && Object.hasOwn(reasons.value, code)
    ? reasons.value[code]
    : null;
});
function number(value: unknown, min: number, max: number, digits = 1) {
  const numeric = finiteValue(value);
  return numeric !== null && numeric >= min && numeric <= max
    ? formatSavingsNumber(numeric, props.hass, digits)
    : null;
}
function instant(value: unknown) {
  // Backend timestamps need an explicit zone; local parsing invents an offset.
  if (
    typeof value !== "string" ||
    !/^\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})$/.test(value)
  )
    return null;
  const time = Date.parse(value);
  return Number.isFinite(time) ? time : null;
}
function timestamp(
  value: unknown,
  sameDayAs?: unknown,
  timeStyle: Intl.DateTimeFormatOptions["timeStyle"] = "short",
) {
  if (instant(value) === null) return null;
  if (sameDayAs) {
    const date = { dateStyle: "medium" } as const;
    if (
      formatSavingsDate(value, props.hass, date) ===
      formatSavingsDate(sameDayAs, props.hass, date)
    )
      return formatSavingsDate(value, props.hass, { timeStyle });
  }
  return formatSavingsDate(value, props.hass, {
    dateStyle: "medium",
    timeStyle,
  });
}
const timeZone = computed(
  () =>
    new Intl.DateTimeFormat("en", {
      timeZone: props.hass?.config?.time_zone,
      timeZoneName: "shortOffset",
    }),
);
function windowTimeStyle(start: number, end: number) {
  const offset = (time: number) =>
    timeZone.value
      .formatToParts(time)
      .find((part) => part.type === "timeZoneName")?.value;
  if (offset(start) !== offset(end)) return "long";
  return Math.floor(start / 60000) === Math.floor(end / 60000)
    ? "medium"
    : "short";
}
function forecastDescription(
  value: Record<string, unknown>,
  atValue: unknown,
  retained = false,
) {
  const at = timestamp(atValue);
  const minutes = number(value.observation_minutes, 1, 15, 0);
  const average = number(
    value.average_discharge_w,
    Number.MIN_VALUE,
    Infinity,
    0,
  );
  if (!at || !minutes || (!average && !retained)) return null;
  const basis = german.value
    ? average
      ? `durchschnittlich ${average} W über ${minutes} min`
      : `${minutes} min Verbrauchsmessung`
    : average
      ? `average ${average} W over ${minutes} min`
      : `${minutes} min of consumption readings`;
  const description = german.value
    ? `Ohne Netzladung reicht der Speicher ${retained ? "laut Plan" : "voraussichtlich"} bis ${at} Uhr (${basis}).`
    : `${retained ? "The plan estimates the battery will last" : "The battery should last"} until ${at} without grid charging (${basis}).`;
  return { at: atValue, description };
}
const postChargeStatus = computed(() => {
  if (
    !plan.value?.available ||
    !completed.value ||
    !("post_charge_status" in attributes.value)
  )
    return null;
  const value = attributes.value.post_charge_status;
  return value === "needed" || value === "not_needed" ? value : "unknown";
});
const postChargeForecast = computed(() => {
  const value = attributes.value.post_charge_forecast_attributes;
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
});
const currentForecast = computed(() => {
  if (chargingActive.value) return null;
  if (postChargeStatus.value !== null) {
    const value = postChargeForecast.value;
    return value && postChargeStatus.value !== "unknown"
      ? forecastDescription(value, value.discharge_at)
      : null;
  }
  if (
    emptyBatteryStart.value ||
    (fixedTargetLabel.value &&
      attributes.value.empty_battery_start_due === true)
  )
    return null;
  if (!discharge.value?.available) return null;
  const state = discharge.value.state;
  return forecastDescription(state?.attributes ?? {}, state?.state);
});
const completed = computed(
  () =>
    ["waiting_for_data", "complete", "insufficient"].includes(
      status.value ?? "",
    ) && timestamp(attributes.value.completed_at) !== null,
);
const demand = computed(() => {
  if (chargingActive.value) return "charging";
  if (fixedTimeStart.value) return "fixed-time";
  if (fixedTargetLabel.value) return "fixed-target";
  if (postChargeStatus.value !== null)
    return postChargeStatus.value === "not_needed"
      ? "not-needed"
      : postChargeStatus.value;
  const shortfall = finiteValue(attributes.value.shortfall_kwh);
  const hasCompletion = attributes.value.completed_at != null;
  const evaluatedCompletion =
    completed.value &&
    timestamp(attributes.value.completion_evaluated_at) !== null &&
    shortfall !== null &&
    shortfall >= 0;
  // REQ-VUE-ELECTRICITY-TARIFF: an ended charge alone is no energy verdict.
  if (hasCompletion && !evaluatedCompletion) return "unknown";
  switch (status.value) {
    case "not_needed": {
      // Only the independent sensor can have changed since the plan was evaluated.
      const pv = instant(attributes.value.pv_start);
      const until = instant(currentForecast.value?.at);
      if (until !== null && pv !== null && pv - until >= 60_000)
        return "conflict";
      return "not-needed";
    }
    case "complete":
      return evaluatedCompletion && shortfall <= 0.001
        ? "not-needed"
        : "unknown";
    case "planned":
    case "charging":
    case "insufficient":
      return "needed";
    case "paused": {
      const target = finiteValue(attributes.value.target_soc);
      return (shortfall !== null && shortfall > 0) ||
        (timestamp(attributes.value.charge_start) &&
          timestamp(attributes.value.charge_end) &&
          target !== null &&
          target > 0 &&
          target <= 100)
        ? "needed"
        : "unknown";
    }
    default:
      return "unknown";
  }
});
const demandLabel = computed(() => {
  switch (demand.value) {
    case "charging":
      return text.value.charging;
    case "fixed-time":
      return fixedTimeLabel.value;
    case "fixed-target":
      return fixedTargetLabel.value;
    case "not-needed":
      return text.value.noCharge;
    case "conflict":
      return text.value.conflict;
    case "needed":
      return text.value.chargeNeeded;
    default:
      if (status.value === "off") return null;
      if (
        !["paused", "complete", "insufficient", "waiting_for_data"].includes(
          status.value ?? "",
        )
      )
        return text.value.unavailable;
      return text.value.demandUnknown;
  }
});
function remainingDuration(seconds: number) {
  const minutes = Math.ceil(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  const parts: string[] = [];
  if (hours)
    parts.push(
      `${number(hours, 1, Infinity, 0)} ${german.value ? (hours === 1 ? "Stunde" : "Stunden") : hours === 1 ? "hour" : "hours"}`,
    );
  if (remainder || !hours)
    parts.push(
      `${remainder} ${german.value ? (remainder === 1 ? "Minute" : "Minuten") : remainder === 1 ? "minute" : "minutes"}`,
    );
  return parts.join(" ");
}
function percentage(value: unknown) {
  return number(value, 0, 100, Number.isInteger(finiteValue(value)) ? 0 : 1);
}
function energyAmount(value: unknown) {
  const kwh = finiteValue(value);
  if (kwh === null || kwh <= 0) return null;
  if (kwh < 0.01)
    return `${german.value ? "weniger als" : "less than"} ${formatSavingsNumber(0.01, props.hass, 2)} kWh`;
  return `${formatSavingsNumber(kwh, props.hass, 2)} kWh`;
}
const chargingDescription = computed(() => {
  const attr = attributes.value;
  const power = number(attr.charging_power_w, Number.MIN_VALUE, Infinity, 0);
  const target = percentage(attr.charging_target_soc);
  const max = percentage(attr.charging_max_soc);
  const seconds = finiteValue(attr.charging_remaining_seconds);
  const duration =
    seconds !== null && seconds >= 0 ? remainingDuration(seconds) : null;
  const de = german.value;
  return [
    power && (de ? `${power} W Ladeleistung` : `${power} W charging power`),
    seconds === 0
      ? de
        ? "Restdauer unter 1 Minute"
        : "less than 1 minute remaining"
      : duration
        ? de
          ? `noch etwa ${duration}`
          : `about ${duration} remaining`
        : de
          ? "Restdauer unbekannt"
          : "remaining time unknown",
    target && (de ? `Ladeziel ${target} %` : `target ${target}%`),
    max &&
    finiteValue(attr.charging_max_soc) !== finiteValue(attr.charging_target_soc)
      ? de
        ? `Netzladegrenze ${max} %`
        : `grid charging limit ${max}%`
      : null,
  ]
    .filter(Boolean)
    .join(" · ");
});
const dataGap = computed(() => {
  if (!completed.value) return null;
  switch (attributes.value.data_gap_reason) {
    case "pv_start_missing":
      return german.value
        ? "Während der Ladung fehlte zeitweise die PV-Prognose."
        : "The solar forecast was temporarily unavailable during charging.";
    case "measurements_missing":
      return german.value
        ? "Während der Ladung fehlten zeitweise Batteriemesswerte."
        : "Battery readings were temporarily unavailable during charging.";
    default:
      return null;
  }
});
const assessment = computed(() => {
  const at = timestamp(attributes.value.completion_evaluated_at);
  if (!completed.value || !at) return null;
  return german.value
    ? `Letzte Ladung bewertet am ${at} Uhr.`
    : `Last charge assessed on ${at}.`;
});
const emptyBatteryStart = computed(
  () =>
    (fixedTargetLabel.value ||
      (!completed.value &&
        ["planned", "insufficient"].includes(status.value ?? ""))) &&
    timestamp(attributes.value.empty_battery_start),
);
const forecast = computed(() => {
  if (currentForecast.value) return currentForecast.value;
  if (
    completed.value ||
    emptyBatteryStart.value ||
    !["planned", "charging", "insufficient", "not_needed"].includes(
      status.value ?? "",
    )
  )
    return null;
  return forecastDescription(
    attributes.value,
    attributes.value.discharge_at,
    true,
  );
});
function solarStart(value: unknown, after?: unknown) {
  const at = timestamp(value, after);
  if (!at) return null;
  const previous = instant(after);
  if (
    previous !== null &&
    Math.floor(instant(value)! / 60_000) === Math.floor(previous / 60_000)
  )
    return german.value
      ? "Ab dann deckt PV voraussichtlich den Verbrauch."
      : "Solar power should cover consumption from then on.";
  return german.value
    ? `PV deckt den Verbrauch voraussichtlich ab ${at} Uhr.`
    : `Solar power should cover consumption from ${at}.`;
}
function shortfallDescription(pv?: string | null) {
  const amount = energyAmount(attributes.value.shortfall_kwh);
  const buffer = number(attributes.value.soc_buffer, 1, 100, 0);
  if (german.value) {
    const until = `Bis zum PV-Start${pv ? ` (${pv} Uhr)` : ""}`;
    const need = buffer ? " für Verbrauch und SOC-Puffer" : "";
    return amount
      ? `${until} fehlen voraussichtlich ${amount}${need}.`
      : `${until} reicht die Energie voraussichtlich nicht${need}.`;
  }
  const until = `before solar power takes over${pv ? ` at ${pv}` : ""}`;
  const need = buffer ? " for consumption and the battery reserve" : "";
  return amount
    ? `Expected shortfall of ${amount}${need} ${until}.`
    : `Available energy is unlikely to be sufficient${need} ${until}.`;
}
const description = computed(() => {
  const attr = attributes.value;
  if (chargingActive.value) {
    const shortfall =
      status.value === "charging" && (finiteValue(attr.shortfall_kwh) ?? 0) > 0;
    return [chargingDescription.value, shortfall && shortfallDescription()]
      .filter(Boolean)
      .join(". ");
  }
  const basis = forecast.value;
  const parts: (string | null | undefined)[] = [basis?.description];
  if (postChargeStatus.value !== null) {
    parts.push(
      postChargeStatus.value === "unknown"
        ? status.value === "waiting_for_data"
          ? text.value.completionPending
          : text.value.postChargeWaiting
        : solarStart(postChargeForecast.value?.pv_start, basis?.at),
    );
  } else if (completed.value) {
    if (status.value === "waiting_for_data")
      parts.push(text.value.completionPending);
    else {
      parts.push(text.value.complete);
      if (status.value === "insufficient") parts.push(shortfallDescription());
    }
  } else {
    switch (status.value) {
      case "planned":
      case "charging":
      case "insufficient": {
        const partial =
          status.value === "insufficient" ||
          (status.value === "charging" &&
            (finiteValue(attr.shortfall_kwh) ?? 0) > 0);
        if (status.value === "charging") parts.push(text.value.unconfirmed);
        const startAt = instant(attr.charge_start);
        const endAt = instant(attr.charge_end);
        const hasWindow = startAt !== null && endAt !== null && startAt < endAt;
        if (hasWindow) {
          const style = windowTimeStyle(startAt, endAt);
          const start = timestamp(attr.charge_start, basis?.at, style);
          const end = timestamp(attr.charge_end, attr.charge_start, style);
          const what = partial ? text.value.partial : text.value.charge;
          if (emptyBatteryStart.value) parts.push(text.value.emptyBattery);
          const tariff = emptyBatteryStart.value
            ? text.value.firstTariff
            : text.value.lowTariff;
          const sameStart = startAt === instant(basis?.at) && style === "short";
          if (german.value) {
            const from = sameStart ? "ab dann" : `von ${start}`;
            parts.push(
              `${what} ${tariff} ${from} bis ${end}${style === "long" ? "" : " Uhr"} geplant.`,
            );
          } else {
            parts.push(
              `${what} planned ${tariff} from ${sameStart ? "then" : start} to ${end}.`,
            );
          }
        } else if (partial && attr.reason === "no_usable_window") {
          parts.push(text.value.noWindow);
        } else if (!partial) {
          parts.push(text.value.incomplete);
        }
        const after = hasWindow ? attr.charge_end : basis?.at;
        if (partial)
          parts.push(shortfallDescription(timestamp(attr.pv_start, after)));
        else parts.push(solarStart(attr.pv_start, after));
        break;
      }
      case "not_needed":
        parts.push(solarStart(attr.pv_start, basis?.at));
        break;
      case "waiting_for_data":
        parts.push(
          reason.value ?? (configurationHint.value ? null : text.value.waiting),
        );
        break;
      case "paused":
        parts.push(text.value.paused, reason.value);
        break;
      case "complete":
        parts.push(text.value.complete);
        break;
    }
  }
  const pv = instant(
    postChargeStatus.value === "needed"
      ? postChargeForecast.value?.pv_start
      : attr.pv_start,
  );
  const dischargeAt = instant(basis?.at);
  if (
    demand.value === "needed" &&
    (status.value === "planned" || postChargeStatus.value === "needed") &&
    number(attr.soc_buffer, 1, 100, 0) &&
    pv !== null &&
    dischargeAt !== null &&
    dischargeAt >= pv
  )
    parts.push(
      german.value
        ? "Der Ladebedarf berücksichtigt den SOC-Puffer."
        : "Charging demand includes the battery reserve.",
    );
  return parts.filter(Boolean).join(" ");
});
const orderDetails = computed(() => {
  if (
    completed.value ||
    !["planned", "charging", "insufficient", "paused"].includes(
      status.value ?? "",
    )
  )
    return null;
  const amount = energyAmount(attributes.value.charge_energy_kwh);
  const target =
    !chargingActive.value && status.value !== "paused"
      ? percentage(attributes.value.target_soc)
      : null;
  return [
    amount &&
      (german.value
        ? `Geplante Lademenge ${amount}`
        : `Planned charge ${amount}`),
    target && (german.value ? `Ladeziel ${target} %` : `Target ${target}%`),
  ]
    .filter(Boolean)
    .join(" · ");
});
</script>

<template>
  <section
    v-if="allLowTariffs && automatic"
    class="charge-plan"
    :aria-labelledby="`${id}-charge-plan`"
  >
    <h2 :id="`${id}-charge-plan`">
      {{ chargingActive ? `${text.title}: ` : text.title
      }}<span
        v-if="chargingActive"
        class="charge-plan__demand charge-plan__demand--charging"
        aria-live="polite"
        >{{ text.charging }}</span
      >
    </h2>
    <p class="charge-plan__description">
      {{ chargingActive ? chargingDescription : text.allLowTariffs }}
    </p>
  </section>
  <section
    v-else-if="
      !allLowTariffs &&
      (plan || control || currentForecast || fixedTimeStart) &&
      (demandLabel || description || configurationHint)
    "
    class="charge-plan"
    :aria-labelledby="`${id}-charge-plan`"
  >
    <h2 :id="`${id}-charge-plan`">
      {{ demandLabel ? `${text.title}: ` : text.title
      }}<span
        v-if="demandLabel"
        class="charge-plan__demand"
        :class="`charge-plan__demand--${demand}`"
        aria-live="polite"
        >{{ demandLabel }}</span
      >
    </h2>
    <template v-if="!fixedTimeStart || chargingActive">
      <p v-if="chargingActive && fixedTimeLabel">{{ fixedTimeLabel }}</p>
      <p v-if="configurationHint && !fixedTimeStart">
        {{ configurationHint }}
      </p>
      <p
        v-if="description"
        class="charge-plan__description"
        :class="{ 'charge-plan__forecast': currentForecast }"
      >
        {{ description }}
      </p>
      <p v-if="dataGap">{{ dataGap }}</p>
      <p v-if="assessment">{{ assessment }}</p>
      <p v-if="orderDetails" class="charge-plan__target">{{ orderDetails }}</p>
    </template>
  </section>
</template>

<style>
.charge-plan {
  min-width: 0;
  padding: 24px;
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  box-shadow: var(--ha-card-box-shadow, none);
  color: var(--primary-text-color, #212121);
}
.charge-plan h2 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.5;
}
.charge-plan__demand--not-needed {
  color: color-mix(
    in srgb,
    var(--success-color, #008f35) 70%,
    var(--primary-text-color, #212121)
  );
}
.charge-plan__demand--needed,
.charge-plan__demand--fixed-time,
.charge-plan__demand--charging {
  color: color-mix(
    in srgb,
    var(--info-color, #1475e8) 70%,
    var(--primary-text-color, #212121)
  );
}
.charge-plan__demand--unknown,
.charge-plan__demand--conflict {
  color: color-mix(
    in srgb,
    var(--warning-color, #ef6c00) 70%,
    var(--primary-text-color, #212121)
  );
}
.charge-plan p {
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.charge-plan p:last-child {
  margin-bottom: 0;
}
.charge-plan__target {
  color: var(--secondary-text-color, #666);
}
@media (max-width: 600px) {
  .charge-plan {
    padding: 20px;
  }
}
@container sax-content (min-width: 860px) {
  .charge-plan {
    padding: 18px;
  }
  .charge-plan h2 {
    margin-bottom: 12px;
    font-size: 16px;
  }
}
</style>
