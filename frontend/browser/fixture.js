import "/sax_power/frontend/sax-power-vue.js";

const translations = await Promise.all(
  ["de", "en"].map(async (language) => [
    language,
    await (await fetch(`/${language}.json`)).json(),
  ]),
);
const languages = Object.fromEntries(translations);
const panel = document.querySelector("sax-power-vue-panel");
const actions = document.querySelector("#actions");
const listeners = new Map();
const metadataSubscribers = new Set();
let language = "de";
let connected = true;
let unavailable = false;
let rejectNext = false;
let writes = 0;

const general = [
  "soc",
  "storage_max_cell_temp",
  "storage_switch",
  "max_soc",
  "charge_power",
  "discharge_power",
  "smartmeter_power",
  "energy_charged",
  "energy_discharged",
  "sun_version_master",
  "sun_version_gateway",
  "sun_serial_number",
  "storage_event_text",
  "ic_control_mode_text",
  "cell_calibration_active",
  "next_cell_calibration",
];
const economics = [
  "economics_investment_configured",
  "economics_amortization_progress",
  "economics_remaining_to_payback",
  "economics_roi",
  "economics_net_savings",
  "economics_status",
  "economics_current_import_price",
];
const definitions = [];
for (const [domain, items] of Object.entries(languages.de.entity)) {
  for (const [translationKey, translation] of Object.entries(items)) {
    const key =
      domain === "switch" && translationKey === "storage"
        ? "storage_switch"
        : translationKey;
    if (
      !general.includes(key) &&
      !economics.includes(key) &&
      !["timed_charge_", "grid_serving_", "price_charge_"].some((prefix) =>
        key.startsWith(prefix),
      )
    )
      continue;
    if (
      domain === "binary_sensor" &&
      !general.includes(key) &&
      !economics.includes(key)
    )
      continue;
    definitions.push({
      domain,
      key,
      translationKey,
      entity_id: `${domain}.demo_${key}`,
      translation,
    });
  }
}
function metadata() {
  return definitions.map(({ domain, key, translationKey, entity_id }) => ({
    domain,
    key,
    entity_id,
    name:
      key === "grid_serving_forecast"
        ? null
        : languages[language].entity[domain][translationKey].name,
    states: languages[language].entity[domain][translationKey].state ?? {},
    can_control: ["number", "time", "switch", "select"].includes(domain),
  }));
}
function example({ domain, key, entity_id }) {
  let state = domain === "switch" || domain === "binary_sensor" ? "on" : "0";
  let attributes = {};
  if (domain === "number") {
    state = "80";
    attributes = { min: 0, max: 100, step: 1, unit_of_measurement: "%" };
  }
  if (domain === "time")
    state = key.endsWith("start") ? "22:00:00" : "06:00:00";
  if (domain === "select") {
    state = "absolute";
    attributes.options = ["off", "absolute", "relative", "smart"];
  }
  if (key.includes("price") && domain === "number") {
    state = "-0.05";
    attributes = {
      min: -1,
      max: 2,
      step: 0.001,
      unit_of_measurement: "EUR/kWh",
    };
  }
  if (key === "price_charge_hours") {
    state = "4";
    attributes = { min: 1, max: 24, step: 1, unit_of_measurement: "h" };
  }
  const values = {
    soc: "63.5",
    storage_max_cell_temp: "24.3",
    charge_power: "1820",
    discharge_power: "0",
    smartmeter_power: "-420",
    energy_charged: "1245.8",
    energy_discharged: "1028.4",
    sun_version_master: "1.2.3",
    sun_version_gateway: "2.4.0",
    sun_serial_number: "DEMO-2026",
    storage_event_text: "Normalbetrieb",
    ic_control_mode_text: "Normalbetrieb",
    cell_calibration_active: "off",
    next_cell_calibration: "2026-09-14T05:00:00Z",
    timed_charge_min_soc: "20",
    timed_charge_discharge_status: "normal",
    grid_serving_forecast: "24.3",
    grid_serving_pause_status: "Inaktiv",
    grid_serving_forecast_threshold: "10",
    price_charge_active_text: "Inaktiv",
    price_charge_status_text: "Warte auf Preisfenster",
    price_charge_next_start: "2026-09-13T20:00:00Z",
    price_charge_current_price: "-0.04",
    economics_investment_configured: "on",
    economics_amortization_progress: "28.5",
    economics_remaining_to_payback: "7150",
    economics_roi: "28.5",
    economics_net_savings: "1350.25",
    economics_status: "active",
    economics_current_import_price: "0.2456",
  };
  state = values[key] ?? state;
  if (["soc", "economics_amortization_progress", "economics_roi"].includes(key))
    attributes.unit_of_measurement = "%";
  if (key === "storage_max_cell_temp") attributes.unit_of_measurement = "°C";
  if (["charge_power", "discharge_power", "smartmeter_power"].includes(key))
    attributes.unit_of_measurement = "W";
  if (key.startsWith("energy_") || key === "grid_serving_forecast")
    attributes.unit_of_measurement = "kWh";
  if (key === "grid_serving_forecast_threshold")
    attributes = { min: 0, max: 100, step: 0.1, unit_of_measurement: "kWh" };
  if (["price_charge_next_start", "next_cell_calibration"].includes(key))
    attributes.device_class = "timestamp";
  if (key === "price_charge_current_price")
    attributes.unit_of_measurement = "EUR/kWh";
  if (key === "grid_serving_forecast")
    attributes.friendly_name = "PV-Prognose 13.9.";
  if (key === "economics_roi") attributes.prior_result_eur = 1499.75;
  if (key === "economics_status")
    attributes.economics_started_at = "2026-01-01T00:00:00Z";
  if (key === "economics_current_import_price")
    attributes = {
      unit_of_measurement: "EUR/kWh",
      tariff_type: "time_of_use",
      windows: [
        { start: "00:00", end: "06:00", price_eur_kwh: 0.18 },
        { start: "18:00", end: "22:00", price_eur_kwh: 0.2456 },
      ],
      active_window: { start: "18:00", end: "22:00" },
      base_price_eur_kwh: 0.32,
      feed_in_price_eur_kwh: 0.0812,
      next_price_change_at: "2026-09-12T20:00:00Z",
      unavailable_reason: null,
    };
  return { entity_id, state, attributes };
}
let states = Object.fromEntries(
  definitions.map((item) => [item.entity_id, example(item)]),
);
const connection = {
  get connected() {
    return connected;
  },
  async subscribeMessage(callback, request) {
    if (request.type === "sax_power/dashboard/subscribe") {
      metadataSubscribers.add(callback);
      callback({ entities: metadata() });
      return () => metadataSubscribers.delete(callback);
    }
    if (request.type === "subscribe_events") return () => {};
    throw new Error("Unknown demo subscription");
  },
  addEventListener(event, callback) {
    if (!listeners.has(event)) listeners.set(event, new Set());
    listeners.get(event).add(callback);
  },
  removeEventListener(event, callback) {
    listeners.get(event)?.delete(callback);
  },
};
function update() {
  panel.hass = {
    language,
    locale: {
      language: language === "de" ? "de-DE" : "en-GB",
      first_weekday: "mon",
    },
    config: { time_zone: "Europe/Berlin" },
    states: unavailable
      ? Object.fromEntries(
          Object.entries(states).map(([id, item]) => [
            id,
            { ...item, state: "unavailable" },
          ]),
        )
      : { ...states },
    connection,
    callService,
    callWS,
  };
}
async function callService(domain, service, data, target) {
  writes += 1;
  actions.textContent = `${writes}: ${domain}.${service} ${JSON.stringify({ ...data, ...target })}`;
  await new Promise((resolve) => setTimeout(resolve, 150));
  if (rejectNext) {
    rejectNext = false;
    throw new Error("Simulated service failure");
  }
  const entityId = target.entity_id;
  const state =
    service === "turn_on"
      ? "on"
      : service === "turn_off"
        ? "off"
        : String(data.value ?? data.time ?? data.option);
  states = { ...states, [entityId]: { ...states[entityId], state } };
  update();
}
function berlinMidnight(day) {
  const offset = new Intl.DateTimeFormat("en", {
    timeZone: "Europe/Berlin",
    timeZoneName: "longOffset",
  })
    .formatToParts(new Date(`${day}T00:00:00Z`))
    .find((part) => part.type === "timeZoneName")
    .value.replace("GMT", "");
  return `${day}T00:00:00${offset}`;
}
async function callWS(request) {
  if (request.type !== "sax_power/dashboard/statistics")
    throw new Error("Unknown demo request");
  const start = request.start_date ?? "2026-09-12";
  const end = request.end_date ?? "2026-09-12";
  const nextDay = new Date(`${end}T00:00:00Z`);
  nextDay.setUTCDate(nextDay.getUTCDate() + 1);
  const period = (change) => ({
    start: "2026-09-11T22:00:00Z",
    end: null,
    change,
  });
  return {
    entity_id: "sensor.demo_economics_net_savings",
    time_zone: "Europe/Berlin",
    today: "2026-09-12",
    status: "ok",
    periods: {
      day: period(2.45),
      week: period(-1.25),
      month: period(18.73),
      year: period(1350.25),
    },
    selected: {
      start_date: start,
      end_date: end,
      start: berlinMidnight(start),
      end: berlinMidnight(nextDay.toISOString().slice(0, 10)),
      change: 1.75,
      period: "hour",
      buckets: [
        { start: `${start}T06:00:00Z`, end: `${start}T07:00:00Z`, change: 2.5 },
        {
          start: `${start}T07:00:00Z`,
          end: `${start}T08:00:00Z`,
          change: -0.75,
        },
      ],
    },
  };
}
panel.panel = { config: { entry_id: "demo-entry" }, url_path: "sax-power-vue" };
panel.route = {
  path: location.pathname === "/" ? "/allgemein" : location.pathname,
};
const size = matchMedia("(max-width: 600px)");
panel.narrow = size.matches;
size.addEventListener("change", (event) => {
  panel.narrow = event.matches;
});
document.querySelector("#language").onclick = () => {
  language = language === "de" ? "en" : "de";
  document.documentElement.lang = language;
  update();
};
document.querySelector("#theme").onclick = () =>
  document.body.classList.toggle("dark");
document.querySelector("#connection").onclick = () => {
  connected = !connected;
  for (const callback of listeners.get(connected ? "ready" : "disconnected") ??
    [])
    callback();
  update();
};
document.querySelector("#external").onclick = () => {
  states["number.demo_max_soc"] = {
    ...states["number.demo_max_soc"],
    state: "75",
  };
  update();
};
document.querySelector("#unavailable").onclick = () => {
  unavailable = !unavailable;
  update();
};
document.querySelector("#failure").onclick = () => {
  rejectNext = true;
};
update();
