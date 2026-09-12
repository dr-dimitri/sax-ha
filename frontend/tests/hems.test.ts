import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import HemsCard from "../src/components/HemsCard.vue";
import TimedChargingView from "../src/views/TimedChargingView.vue";
import DynamicChargingView from "../src/views/DynamicChargingView.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "../src/ha";
import { hemsNumber, hemsReason, hemsTime } from "../src/hems";
import type {
  DashboardMetadata,
  HassConnection,
  HomeAssistant,
} from "../src/types";

const apps: App[] = [];
const initial = {
  mode: "timed",
  status: "planned",
  reason_codes: ["night_bridge_required"],
  execution_charging: false,
  execution_constraint: null,
  next_evaluation_at: "2026-09-12T22:05:00Z",
  evaluated_at: "2026-09-12T22:00:00Z",
  planned_start: "2026-09-13T02:00:00Z",
  planned_end: "2026-09-13T02:30:00Z",
  pv_supply_at: "2026-09-13T06:00:00Z",
  remaining_grid_kwh: 1.25,
  target_soc: 47.5,
  expected_load_kwh: 3.2,
  pv_used_kwh: 0.5,
  available_battery_kwh: 1.8,
  reserve_soc: 20,
  reserve_kwh: 1.6,
  nights_count: 4,
  observed_hours: 8.5,
  load_coverage: 0.42,
  load_quality_flags: [
    "night_slot_mean",
    "pooled_night_estimate",
    "dawn_extrapolation",
  ],
  pv_provider: "solcast_solar",
  pv_source_id: "selected-plant",
  pv_fetched_at: "2026-09-12T18:00:00Z",
  pv_max_age_seconds: 86400,
  pv_freshness_policy: "sax_max_age_assumption",
  pv_update_success: null,
  pv_coverage_start: "2026-09-12T22:00:00Z",
  pv_coverage_end: "2026-09-13T07:00:00Z",
  pv_quality_flags: ["pv_partial_coverage"],
  eta_charge_assumption: 0.95,
  eta_discharge_assumption: 0.95,
};
async function flush() {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}
async function mount(
  language = "de",
  tariff: "timed" | "dynamic" = "timed",
  fullView = false,
) {
  const entityId = "sensor.renamed_night_status";
  let metadata: (value: DashboardMetadata) => void = () => {};
  const listeners = new Map<string, () => void>();
  const connection: HassConnection = {
    connected: true,
    async subscribeMessage<T>(callback: (value: T) => void) {
      metadata = (value) => callback(value as T);
      emit();
      return () => {};
    },
    addEventListener(event, callback) {
      listeners.set(event, callback);
    },
    removeEventListener(event) {
      listeners.delete(event);
    },
  };
  function emit(id = entityId) {
    metadata({
      entities: [
        {
          domain: "sensor",
          key: "hems_status",
          entity_id: id,
          name: "Night status",
          states: {},
          can_control: false,
        },
      ],
    });
  }
  const callService = vi.fn().mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language,
    states: {
      [entityId]: {
        entity_id: entityId,
        state: "planned",
        attributes: { ...initial, mode: tariff },
      },
    },
    connection,
    callService,
    config: { time_zone: "Europe/Berlin" },
  });
  const root = document.createElement("div");
  document.body.append(root);
  const app = createApp({
    setup() {
      provide(
        SAX_DASHBOARD_KEY,
        useSaxDashboard(
          () => hass.value,
          () => "battery-entry",
        ),
      );
      return () =>
        h(
          fullView
            ? tariff === "timed"
              ? TimedChargingView
              : DynamicChargingView
            : HemsCard,
          fullView ? { hass: hass.value } : { hass: hass.value, tariff },
        );
    },
  });
  apps.push(app);
  app.mount(root);
  await flush();
  return {
    root,
    hass,
    callService,
    async update(attributes: Record<string, unknown>, state = "planned") {
      hass.value = {
        ...hass.value,
        states: {
          [entityId]: {
            entity_id: entityId,
            state,
            attributes: { ...initial, mode: tariff, ...attributes },
          },
        },
      };
      await flush();
    },
    async disconnect() {
      listeners.get("disconnected")!();
      await flush();
    },
    async reconnect() {
      listeners.get("ready")!();
      await flush();
    },
    async rename() {
      const renamed = "sensor.new_name";
      hass.value = {
        ...hass.value,
        states: {
          [renamed]: { ...hass.value.states[entityId]!, entity_id: renamed },
        },
      };
      emit(renamed);
      await flush();
    },
    async remove() {
      metadata({ entities: [] });
      await flush();
    },
  };
}
afterEach(() => {
  for (const app of apps.splice(0)) app.unmount();
  document.body.replaceChildren();
  vi.useRealTimers();
});

describe("REQ-HEMS-OBSERVABILITY", () => {
  it.each(["timed", "dynamic"] as const)(
    "uses the same readonly card in %s without writes",
    async (tariff) => {
      const { root, callService } = await mount("de", tariff, true);
      expect(root.querySelector(".hems-card")).not.toBeNull();
      expect(root.textContent).toContain("Netzladung geplant");
      expect(root.textContent).toContain("1,25 kWh");
      expect(root.textContent).toContain("Derzeit keine bestätigte Netzladung");
      expect(root.textContent).not.toContain("Bestätigter Wert:");
      expect(callService).not.toHaveBeenCalled();
    },
  );
  it("uses backend timestamps unchanged by browser clock, and localises DE/EN", async () => {
    const { root, update } = await mount("en", "dynamic");
    const next = () =>
      root.querySelector('[data-testid="hems-next"]')!.textContent;
    expect(root.textContent).toContain("1.25 kWh");
    expect(next()).toContain("13 Sept 2026, 00:05");
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2032-01-01T00:00:00Z"));
    await flush();
    expect(next()).toContain("13 Sept 2026, 00:05");
    await update({ next_evaluation_at: "2026-09-12T22:12:00Z" });
    expect(next()).toContain("00:12");
  });
  it.each([
    ["no_need", "battery_covers_bridge", "Kein Netzladen geplant"],
    ["limited", "unmet_need", "Bedarf nur teilweise gedeckt"],
    ["blocked", "invalid_soc_limits", "Die SOC-Grenzen passen nicht zusammen"],
    ["inactive", "outside_model_scope", "höchstens vier Stunden"],
    ["fallback", "pv_stale_forecast", "Rückfall auf Min-/Max-SOC"],
    ["fallback", "insufficient_history", "mindestens drei Nächten"],
  ])("explains %s / %s", async (status, reason, message) => {
    const { root, update } = await mount();
    await update({ status, reason_codes: [reason] });
    expect(root.textContent).toContain(message);
  });
  it("separates override, device acknowledgment and calibration from the plan", async () => {
    const { root, update } = await mount();
    await update({ execution_constraint: "manual_override" });
    expect(root.textContent).toContain("Manuelle Steuerung verhindert");
    expect(root.textContent).not.toContain(
      "Netzladebefehl vom Gerät bestätigt",
    );
    await update({
      execution_charging: true,
      calibration: true,
      execution_target_soc: 100,
    });
    expect(root.textContent).toContain("Netzladebefehl vom Gerät bestätigt");
    expect(root.textContent).toContain(
      "Mehrladung für Zellkalibrierung bis 100 %",
    );
    expect(root.textContent).toContain("47,5 %");
  });
  it("preserves unknown amounts and times during fallback and evaluating", async () => {
    const { root, update } = await mount();
    await update({
      status: "fallback",
      reason_codes: ["pv_provider_not_configured"],
      remaining_grid_kwh: null,
      target_soc: null,
      planned_start: null,
      planned_end: null,
      next_evaluation_at: null,
    });
    expect(
      root.querySelector(".hems-card__metrics")!.textContent,
    ).not.toContain("0 kWh");
    expect(
      root.querySelector(".hems-card__metrics")!.textContent,
    ).not.toContain("1970");
    expect(root.querySelector('[data-testid="hems-next"]')!.textContent).toBe(
      "Unbekannt",
    );
    await update({ status: "evaluating" });
    expect(root.querySelector('[data-testid="hems-next"]')!.textContent).toBe(
      "Unbekannt",
    );
  });
  it("shows actual history coverage, provider age assumption and unknown update success", async () => {
    const { root } = await mount();
    expect(root.textContent).toContain("42 %");
    expect(root.textContent).toContain("4 Nächte · 8,5 Stunden beobachtet");
    expect(root.textContent).toContain("Direkt beobachteter Uhrzeitslot");
    expect(root.textContent).toContain("Gepooltes Nachtlastniveau");
    expect(root.textContent).toContain("Begrenzte Dämmerungsfortschreibung");
    expect(root.textContent).toContain("24 h · SAX-Annahme");
    expect(root.textContent).toContain("keine Erfolgszusage des Anbieters");
    expect(root.textContent).toContain("Die PV-Abdeckung ist teilweise");
  });
  it("drops stale display on disconnect, rename, missing metadata and different tariff", async () => {
    const { root, callService, disconnect, reconnect, rename, update, remove } =
      await mount();
    await disconnect();
    expect(root.textContent).not.toContain("1,25 kWh");
    expect(root.querySelector(".hems-card")).toBeNull();
    await reconnect();
    expect(root.textContent).toContain("1,25 kWh");
    await update({ mode: "dynamic" });
    expect(root.querySelector(".hems-card__metrics")).toBeNull();
    await update({ mode: "timed" });
    await rename();
    expect(root.textContent).toContain("1,25 kWh");
    await remove();
    expect(root.querySelector(".hems-card")).toBeNull();
    expect(callService).not.toHaveBeenCalled();
  });
  it("renders unknown reasons as escaped text and rejects fabricated values", async () => {
    const { root, update } = await mount();
    await update({ reason_codes: ["<img src=x onerror=alert(1)>"] });
    expect(root.querySelector("img")).toBeNull();
    expect(hemsNumber(null, "de", "kWh")).toBe("Unbekannt");
    expect(hemsNumber(NaN, "en")).toBe("Unknown");
    expect(hemsTime("2026-09-12T00:00:00", "de")).toBe("Unbekannt");
    expect(hemsReason("new_reason", "en")).toContain("Additional constraint");
    expect(hemsReason("pv_source_changed", "de")).toContain(
      "während der Prüfung geändert",
    );
    expect(hemsReason("pv_source_unavailable", "en")).toContain(
      "installation is unavailable",
    );
  });
});
