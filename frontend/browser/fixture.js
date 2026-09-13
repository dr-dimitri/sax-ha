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
let holdNextAction = false;
let releaseAction = null;
let tariffConfigureRequests = 0;
let writes = 0;
let activeTariff = "time_of_use";
let tariffRevision = 1;
const bridgePlan = new URLSearchParams(location.search).has("bridge-plan");

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
      key !== "bridge_charge_enabled" &&
      !general.includes(key) &&
      !economics.includes(key) &&
      !(bridgePlan && key === "bridge_charge_plan") &&
      !["timed_charge_", "grid_serving_", "price_charge_"].some((prefix) =>
        key.startsWith(prefix),
      )
    )
      continue;
    if (
      domain === "binary_sensor" &&
      key !== "bridge_charge_enabled" &&
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
    device_id: "demo-device",
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
    state = "-5";
    attributes = {
      min: -100,
      max: 200,
      step: 0.1,
      unit_of_measurement: "ct/kWh",
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
    next_cell_calibration: "2026-09-14",
    timed_charge_enabled: "off",
    bridge_charge_enabled: bridgePlan ? "on" : "off",
    price_charge_enabled: "off",
    timed_charge_min_soc: "20",
    timed_charge_discharge_status: "normal",
    grid_serving_forecast: "24.3",
    grid_serving_pause_status: "Inaktiv",
    grid_serving_forecast_threshold: "10",
    price_charge_active_text: "Inaktiv",
    price_charge_status_text: "Warte auf Preisfenster",
    price_charge_next_start: "2026-09-13T20:00:00Z",
    price_charge_current_price: "-4",
    economics_investment_configured: "on",
    economics_amortization_progress: "28.5",
    economics_remaining_to_payback: "7150",
    economics_roi: "28.5",
    economics_net_savings: "1350.25",
    economics_status: "active",
    economics_current_import_price: "24.56",
    bridge_charge_plan: "planned",
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
  if (key === "next_cell_calibration") attributes.device_class = "date";
  if (key === "price_charge_next_start") attributes.device_class = "timestamp";
  if (key === "price_charge_current_price")
    attributes.unit_of_measurement = "ct/kWh";
  if (key === "grid_serving_forecast")
    attributes.friendly_name = "PV-Prognose 13.9.";
  if (key === "economics_roi") attributes.prior_result_eur = 1499.75;
  if (key === "economics_status")
    attributes.economics_started_at = "2026-01-01T00:00:00Z";
  if (key === "economics_current_import_price")
    attributes = {
      unit_of_measurement: "ct/kWh",
      tariff_type: "time_of_use",
      windows: [
        { start: "00:00", end: "06:00", price_eur_kwh: 0.18, low_tariff: true },
        {
          start: "18:00",
          end: "22:00",
          price_eur_kwh: 0.2456,
          low_tariff: false,
        },
      ],
      active_window: { start: "18:00", end: "22:00" },
      base_price_eur_kwh: 0.32,
      feed_in_price_eur_kwh: 0.0812,
      next_price_change_at: "2026-09-12T20:00:00Z",
      unavailable_reason: null,
      low_tariff_price_eur_kwh: 0.18,
      base_price_is_low_tariff: false,
      low_tariff_active: false,
      low_tariff_valid_until: null,
    };
  if (key === "bridge_charge_plan")
    attributes = {
      enabled: true,
      observation_minutes: 30,
      average_discharge_w: 1000,
      discharge_at: "2026-09-14T00:00:00Z",
      charge_start: "2026-09-13T23:00:00Z",
      charge_end: "2026-09-14T00:00:00Z",
      pv_start: "2026-09-14T05:00:00Z",
      target_soc: 60,
      shortfall_kwh: 0,
    };
  return { entity_id, state, attributes };
}
let states = Object.fromEntries(
  definitions.map((item) => [item.entity_id, example(item)]),
);
const tariffProfiles = {
  time_of_use: {
    base_price_ct_kwh: 32,
    feed_in_price_ct_kwh: 8.12,
    windows: [
      { start: "00:00:00", end: "06:00:00", price_ct_kwh: 18 },
      { start: "18:00:00", end: "22:00:00", price_ct_kwh: 24.56 },
    ],
    pv_sensor: null,
  },
  dynamic: {
    feed_in_price_ct_kwh: 8.12,
    price_sensor: "sensor.demo_dynamic_price",
    price_attribute: null,
    price_unit: "ct_kwh",
    pv_sensor: null,
    pv_factor: 70,
  },
};
states["sensor.demo_dynamic_price"] = {
  entity_id: "sensor.demo_dynamic_price",
  state: "24.56",
  attributes: {
    friendly_name: "Day-ahead electricity price",
    unit_of_measurement: "ct/kWh",
  },
};
const tariffModes = {
  timed: ["on", "off"],
  dynamic: ["off", "on"],
  off: ["off", "off"],
  both: ["on", "on"],
};
function setTariffMode(mode) {
  if (mode === "timed" || mode === "dynamic") {
    activeTariff = mode === "dynamic" ? "dynamic" : "time_of_use";
    const id = "sensor.demo_economics_current_import_price";
    states[id] = {
      ...states[id],
      attributes: { ...states[id].attributes, tariff_type: activeTariff },
    };
  }
  for (const [index, key] of [
    "timed_charge_enabled",
    "price_charge_enabled",
  ].entries()) {
    const entityId = `switch.demo_${key}`;
    states[entityId] = {
      ...states[entityId],
      state: tariffModes[mode][index],
    };
  }
  sessionStorage.setItem("sax-demo-tariff", mode);
}
const savedTariff = sessionStorage.getItem("sax-demo-tariff");
if (savedTariff && Object.hasOwn(tariffModes, savedTariff))
  setTariffMode(savedTariff);
if (bridgePlan) setTariffMode("timed");
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
async function waitForActionRelease() {
  if (!holdNextAction) return;
  holdNextAction = false;
  const button = document.querySelector("#release-action");
  button.disabled = false;
  await new Promise((resolve) => {
    releaseAction = resolve;
  });
  releaseAction = null;
  button.disabled = true;
}
async function callService(domain, service, data, target) {
  writes += 1;
  actions.textContent = `${writes}: ${domain}.${service} ${JSON.stringify({ ...data, ...target })}`;
  await waitForActionRelease();
  await new Promise((resolve) => setTimeout(resolve, 150));
  if (rejectNext) {
    rejectNext = false;
    throw new Error("Simulated service failure");
  }
  if (domain === "sax_power") {
    const prefix =
      service === "set_timed_charge_window"
        ? "timed_charge"
        : service === "set_grid_serving_window"
          ? "grid_serving"
          : null;
    if (!prefix || data.device_id !== "demo-device")
      throw new Error("Unknown demo window");
    for (const boundary of ["start", "end"]) {
      const entityId = `time.demo_${prefix}_${boundary}`;
      states = {
        ...states,
        [entityId]: { ...states[entityId], state: data[boundary] },
      };
    }
    update();
    return;
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
function tariffResult() {
  const attrs = states["sensor.demo_economics_current_import_price"].attributes;
  const tou = {
    ...tariffProfiles.time_of_use,
    base_price_ct_kwh:
      attrs.base_price_eur_kwh === null ? null : attrs.base_price_eur_kwh * 100,
    feed_in_price_ct_kwh:
      attrs.feed_in_price_eur_kwh === null
        ? null
        : attrs.feed_in_price_eur_kwh * 100,
    windows: (attrs.windows ?? []).map((window) => ({
      start: window.start,
      end: window.end,
      price_ct_kwh: window.price_eur_kwh * 100,
    })),
  };
  return {
    tariff_type: activeTariff,
    base_price_ct_kwh:
      activeTariff === "time_of_use" ? tou.base_price_ct_kwh : null,
    feed_in_price_ct_kwh:
      activeTariff === "time_of_use"
        ? tou.feed_in_price_ct_kwh
        : tariffProfiles.dynamic.feed_in_price_ct_kwh,
    windows: activeTariff === "time_of_use" ? tou.windows : [],
    profiles: { ...tariffProfiles, time_of_use: tou },
    revision: String(tariffRevision),
    can_edit: activeTariff === "time_of_use",
    can_configure: true,
    automation_enabled:
      states[
        `switch.demo_${activeTariff === "dynamic" ? "price" : "timed"}_charge_enabled`
      ]?.state === "on",
  };
}
function tariffSeries(day) {
  const date = day === "tomorrow" ? "2026-09-14" : "2026-09-13";
  const start = `${date}T00:00:00+02:00`;
  const stop = day === "tomorrow" ? "2026-09-15" : "2026-09-14";
  const end = `${stop}T00:00:00+02:00`;
  const dayStart = Date.parse(start);
  const slots = Array.from({ length: 24 }, (_, hour) => {
    let price;
    if (activeTariff === "dynamic")
      price = [
        25, 24, 23, 22, 21, 22, 25, 30, 28, 24, 20, 12, 3, -2, -4, 6, 18, 28,
        35, 38, 32, 29, 27, 26,
      ][hour];
    else {
      const minute = hour * 60;
      const profile = tariffResult();
      const window = profile.windows.find((window) => {
        const [sh, sm] = window.start.split(":").map(Number),
          [eh, em] = window.end.split(":").map(Number);
        const a = sh * 60 + sm,
          b = eh * 60 + em;
        return a < b ? minute >= a && minute < b : minute >= a || minute < b;
      });
      price = window?.price_ct_kwh ?? profile.base_price_ct_kwh;
    }
    return {
      start: new Date(dayStart + hour * 3600000).toISOString(),
      end: new Date(dayStart + (hour + 1) * 3600000).toISOString(),
      price_ct_kwh: price,
    };
  });
  return {
    tariff_type: activeTariff,
    day,
    date,
    time_zone: "Europe/Berlin",
    start,
    end,
    now: "2026-09-13T10:15:00+02:00",
    current_price_ct_kwh:
      activeTariff === "dynamic" ? 20 : tariffResult().base_price_ct_kwh,
    status: "available",
    reason: null,
    slots,
    gaps: [],
    revision: String(tariffRevision),
  };
}
async function callWS(request) {
  if (request.type === "sax_power/dashboard/tariff/series")
    return tariffSeries(request.day);
  if (request.type === "sax_power/dashboard/tariff/get") return tariffResult();
  if (request.type === "sax_power/dashboard/tariff/configure") {
    panel.dataset.tariffConfigureRequests = String(++tariffConfigureRequests);
    await waitForActionRelease();
    if (rejectNext) {
      rejectNext = false;
      throw { code: "invalid_tariff" };
    }
    if (request.revision !== String(tariffRevision)) throw { code: "conflict" };
    const enabled =
      request.automation_enabled ?? tariffResult().automation_enabled;
    activeTariff = request.tariff_type;
    if (request.profile) {
      tariffProfiles[activeTariff] = { ...request.profile };
      if (activeTariff === "time_of_use") {
        const id = "sensor.demo_economics_current_import_price";
        states[id] = {
          ...states[id],
          attributes: {
            ...states[id].attributes,
            base_price_eur_kwh: request.profile.base_price_ct_kwh / 100,
            feed_in_price_eur_kwh: request.profile.feed_in_price_ct_kwh / 100,
            windows: request.profile.windows.map((window) => ({
              ...window,
              price_eur_kwh: window.price_ct_kwh / 100,
              low_tariff: false,
            })),
          },
        };
      }
    }
    for (const kind of ["timed", "price"]) {
      const id = `switch.demo_${kind}_charge_enabled`;
      states[id] = {
        ...states[id],
        state:
          enabled && (kind === "price") === (activeTariff === "dynamic")
            ? "on"
            : "off",
      };
    }
    const id = "sensor.demo_economics_current_import_price";
    states[id] = {
      ...states[id],
      attributes: { ...states[id].attributes, tariff_type: activeTariff },
    };
    tariffRevision++;
    writes++;
    actions.textContent = `${writes}: sax_power.configure_tariff ${JSON.stringify(request)}`;
    update();
    return tariffResult();
  }
  if (request.type.startsWith("sax_power/dashboard/tariff/")) {
    const id = "sensor.demo_economics_current_import_price";
    const attrs = states[id].attributes;
    if (request.type.endsWith("/save")) {
      if (rejectNext) {
        rejectNext = false;
        throw { code: "invalid_tariff" };
      }
      if (request.revision !== String(tariffRevision))
        throw { code: "conflict" };
      tariffRevision += 1;
      writes += 1;
      actions.textContent = `${writes}: sax_power.save_tariff ${JSON.stringify(request)}`;
      const lowPrice = Math.min(
        request.base_price_ct_kwh,
        ...request.windows.map((window) => window.price_ct_kwh),
      );
      states = {
        ...states,
        [id]: {
          ...states[id],
          attributes: {
            ...attrs,
            base_price_eur_kwh: request.base_price_ct_kwh / 100,
            feed_in_price_eur_kwh: request.feed_in_price_ct_kwh / 100,
            low_tariff_price_eur_kwh: lowPrice / 100,
            base_price_is_low_tariff: request.base_price_ct_kwh === lowPrice,
            windows: request.windows.map((window) => ({
              ...window,
              price_eur_kwh: window.price_ct_kwh / 100,
              low_tariff: window.price_ct_kwh === lowPrice,
            })),
          },
        },
      };
      update();
    }
    return tariffResult();
  }
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
document.querySelector("#hold-action").onclick = () => {
  holdNextAction = true;
};
document.querySelector("#release-action").onclick = () => {
  releaseAction?.();
};
for (const mode of Object.keys(tariffModes)) {
  document.querySelector(`#tariff-${mode}`).onclick = () => {
    setTariffMode(mode);
    update();
  };
}
document.querySelector("#legacy-times").onclick = () => {
  for (const kind of ["timed_charge", "grid_serving"]) {
    for (const [boundary, value] of [
      ["start", "22:00:17"],
      ["end", "06:00:29"],
    ]) {
      const entityId = `time.demo_${kind}_${boundary}`;
      states[entityId] = { ...states[entityId], state: value };
    }
  }
  update();
};
document.querySelector("#legacy-tariff").onclick = () => {
  activeTariff = "fixed";
  const id = "sensor.demo_economics_current_import_price";
  states[id] = {
    ...states[id],
    attributes: { ...states[id].attributes, tariff_type: "fixed" },
  };
  update();
};
update();
