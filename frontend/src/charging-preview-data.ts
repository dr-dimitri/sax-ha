import de from "../../custom_components/sax_power/translations/de.json";
import en from "../../custom_components/sax_power/translations/en.json";
import type {
  DashboardEntityMetadata,
  EntityDomain,
  HassEntity,
} from "./types";

interface Translation {
  name: string;
  state?: Record<string, string>;
}

// Preview-only data: production views receive both names and values from HA.
export function chargingSample(language = "de"): {
  metadata: DashboardEntityMetadata[];
  states: Record<string, HassEntity>;
} {
  const translations = (language.startsWith("de") ? de : en).entity;
  const metadata: DashboardEntityMetadata[] = [];
  const states: Record<string, HassEntity> = {};
  for (const [domain, values] of Object.entries(translations)) {
    if (domain === "binary_sensor") continue;
    for (const [key, translation] of Object.entries(values) as [
      string,
      Translation,
    ][]) {
      if (
        key !== "max_soc" &&
        !key.startsWith("timed_charge_") &&
        !key.startsWith("grid_serving_") &&
        !key.startsWith("price_charge_")
      )
        continue;
      const entityId = `${domain}.renamed_${key}`;
      const item: DashboardEntityMetadata = {
        entity_id: entityId,
        device_id: "charging-preview-device",
        domain: domain as EntityDomain,
        key,
        name: key === "grid_serving_forecast" ? null : translation.name,
        states: translation.state ?? {},
        can_control: domain !== "sensor",
      };
      metadata.push(item);
      let state = "on";
      let attributes: Record<string, unknown> = {};
      if (domain === "time")
        state = key.endsWith("start") ? "22:00:00" : "06:00:00";
      if (domain === "select") {
        state = "absolute";
        attributes = { options: ["off", "absolute", "relative", "smart"] };
      }
      if (domain === "number") {
        state = "80";
        attributes = { min: 0, max: 100, step: 1, unit_of_measurement: "%" };
        if (key === "timed_charge_max_soc") attributes.max = 90;
        if (key === "timed_charge_min_soc") state = "20";
        if (key.includes("price") && !key.endsWith("hours")) {
          state = key.endsWith("neutral_price") ? "30" : "-5";
          attributes = {
            min: -100,
            max: 200,
            step: 0.1,
            unit_of_measurement: "ct/kWh",
          };
        }
        if (key.endsWith("hours")) {
          state = "4";
          attributes = { min: 1, max: 24, step: 1, unit_of_measurement: "h" };
        }
        if (key === "grid_serving_forecast_threshold") {
          state = "10";
          attributes = {
            min: 0,
            max: 100,
            step: 0.1,
            unit_of_measurement: "kWh",
          };
        }
      }
      if (domain === "sensor") {
        state = language.startsWith("de") ? "Inaktiv" : "Inactive";
        if (key === "timed_charge_discharge_status") state = "normal";
        if (key === "grid_serving_forecast") {
          state = "24.3";
          attributes = {
            friendly_name: language.startsWith("de")
              ? "PV-Prognose morgen"
              : "PV forecast tomorrow",
            unit_of_measurement: "kWh",
          };
        }
        if (key === "price_charge_current_price") {
          state = "-4";
          attributes = { unit_of_measurement: "ct/kWh" };
        }
        if (key === "price_charge_next_start") {
          state = "2026-09-14T05:00:00Z";
          attributes = { device_class: "timestamp" };
        }
      }
      states[entityId] = { entity_id: entityId, state, attributes };
    }
  }
  return { metadata, states };
}
