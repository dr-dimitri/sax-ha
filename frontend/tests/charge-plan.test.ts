import { afterEach, describe, expect, it, vi } from "vitest";
import { createApp, h, nextTick, provide, shallowRef, type App } from "vue";
import ChargePlan from "../src/components/ChargePlan.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "../src/ha";
import type {
  DashboardMetadata,
  HassConnection,
  HomeAssistant,
} from "../src/types";

const apps: App[] = [];
const entityId = "sensor.my_renamed_charging_plan";
const planned = {
  observation_minutes: 32.5,
  average_discharge_w: 456,
  discharge_at: "2026-09-13T21:30:00Z",
  charge_start: "2026-09-13T22:00:00Z",
  charge_end: "2026-09-13T22:40:00Z",
  pv_start: "2026-09-14T05:00:00Z",
  target_soc: 42.5,
  shortfall_kwh: 0,
};
async function flush() {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}
async function mount(language = "de") {
  let emitMetadata: (data: DashboardMetadata) => void = () => {};
  const metadata = {
    domain: "sensor" as const,
    key: "bridge_charge_plan",
    entity_id: entityId,
    name: "Plan",
    states: {},
    can_control: false,
  };
  const listeners: Record<string, () => void> = {};
  const connection: HassConnection = {
    connected: true,
    async subscribeMessage<T>(callback: (message: T) => void) {
      emitMetadata = (data) => callback(data as T);
      emitMetadata({ entities: [metadata] });
      return () => {};
    },
    addEventListener(event, callback) {
      listeners[event] = callback;
    },
    removeEventListener(event) {
      delete listeners[event];
    },
  };
  const callService = vi.fn().mockResolvedValue(undefined);
  const callWS = vi.fn().mockResolvedValue(undefined);
  const hass = shallowRef<HomeAssistant>({
    language,
    connection,
    states: {
      [entityId]: {
        entity_id: entityId,
        state: "planned",
        attributes: planned,
      },
    },
    config: { time_zone: "Europe/Berlin" },
    locale: { time_format: "twenty_four" },
    callService,
    callWS,
  });
  const root = document.createElement("div");
  document.body.append(root);
  const app = createApp({
    setup() {
      provide(
        SAX_DASHBOARD_KEY,
        useSaxDashboard(
          () => hass.value,
          () => "entry-1",
        ),
      );
      return () => h(ChargePlan, { hass: hass.value });
    },
  });
  apps.push(app);
  app.mount(root);
  await flush();
  return {
    root,
    hass,
    callService,
    callWS,
    async update(state: string, attributes: Record<string, unknown> = planned) {
      hass.value = {
        ...hass.value,
        states: {
          [entityId]: { entity_id: entityId, state, attributes },
        },
      };
      await flush();
    },
    async metadata(visible: boolean) {
      emitMetadata({ entities: visible ? [metadata] : [] });
      await flush();
    },
    async disconnect() {
      listeners.disconnected();
      await flush();
    },
  };
}

afterEach(() => {
  for (const app of apps.splice(0)) app.unmount();
  document.body.replaceChildren();
});

describe("consumption-based charging plan", () => {
  it("explains consumption, depletion, charging and PV start in the HA timezone across midnight", async () => {
    const { root, callService, callWS } = await mount();
    expect(root.querySelector("h2")?.textContent).toBe("Ladeplanung");
    expect(root.textContent).toContain("letzten 32,5 Minuten");
    expect(root.textContent).toContain("durchschnittlich 456 W");
    expect(root.textContent).toContain("13.09.2026, 23:30 Uhr entleert");
    expect(root.textContent).toContain("Niedertarif um 14.09.2026, 00:00 Uhr");
    expect(root.textContent).toContain("bis 14.09.2026, 00:40 Uhr");
    expect(root.textContent).toContain("PV-Start um 14.09.2026, 07:00 Uhr");
    expect(root.textContent).toContain("Geplantes Ladeziel: 42,5 %");
    expect(root.querySelectorAll("button, input, select, form")).toHaveLength(
      0,
    );
    expect(callService).not.toHaveBeenCalled();
    expect(callWS).not.toHaveBeenCalled();
  });

  it("localizes the plan and formats times with the user's HA locale", async () => {
    const { root, hass } = await mount("en-GB");
    expect(root.querySelector("h2")?.textContent).toBe("Charging plan");
    expect(root.textContent).toContain("last 32.5 minutes");
    expect(root.textContent).toContain("low-tariff charging will start");
    expect(root.textContent).toContain("14 Sept 2026, 00:00");
    hass.value = {
      ...hass.value,
      config: { time_zone: "America/New_York" },
      locale: { language: "en-US", time_format: "am_pm" },
    };
    await flush();
    expect(root.textContent).toContain("Sep 13, 2026, 6:00 PM");
    expect(root.textContent).toContain("Sep 14, 2026, 1:00 AM");
  });

  it.each(["de", "en-GB"])(
    "clearly reports no charging is needed (%s)",
    async (language) => {
      const { root, update } = await mount(language);
      await update("not_needed", {
        ...planned,
        discharge_at: "2026-09-14T06:00:00Z",
      });
      expect(root.textContent).toContain(
        language === "de"
          ? "Eine Netzladung ist nicht erforderlich"
          : "No grid charging is needed",
      );
      expect(root.textContent).not.toContain("00:40");
      expect(root.querySelector(".charge-plan__target")).toBeNull();
    },
  );

  it.each([
    ["waiting_for_data", "pv_start_missing", "PV-Prognose", "PV forecast"],
    [
      "waiting_for_data",
      "consumption_missing",
      "Entlademessung",
      "discharge measurements",
    ],
    [
      "waiting_for_data",
      "measurements_missing",
      "Batteriemesswerte",
      "battery measurements",
    ],
    ["paused", "calibration", "Batteriekalibrierung", "Battery calibration"],
    ["paused", "pv_surplus", "PV-Überschuss", "PV surplus"],
    ["paused", "manual_charge", "manuelle Ladung", "Manual charging"],
    ["off", "disabled", "Integrationsoptionen", "integration options"],
  ])(
    "explains the reason %s/%s in both languages without exposing internal codes",
    async (state, reason, german, english) => {
      for (const [language, expected] of [
        ["de", german],
        ["en-GB", english],
      ]) {
        const { root, update } = await mount(language);
        await update(state, { reason });
        expect(root.textContent).toContain(expected);
        expect(
          [...root.querySelectorAll("p")].map((item) => item.textContent),
        ).not.toContain(reason);
      }
    },
  );

  it("gives an activation hint without a reason and keeps unknown reasons generic", async () => {
    const { root, update } = await mount();
    await update("off", {});
    expect(root.textContent).toContain("Integrationsoptionen aktivieren");
    expect(root.textContent).toContain("Netzladung aktiv");
    await update("waiting_for_data", { reason: "private_new_reason" });
    expect(root.textContent).toContain(
      "mindestens eine Minute Beobachtungszeit",
    );
    expect(root.textContent).not.toContain("private_new_reason");
  });

  it("updates running, paused, complete and disabled plans without stale promises", async () => {
    const { root, update } = await mount();
    await update("charging");
    expect(root.textContent).toContain("Niedertarifladung läuft seit");
    for (const [state, expected] of [
      ["paused", "Ladeplanung ist pausiert"],
      ["complete", "Netzladung ist abgeschlossen"],
      ["off", "Ladeplanung ist ausgeschaltet"],
      ["waiting_for_data", "mindestens eine Minute Beobachtungszeit"],
    ]) {
      await update(state);
      expect(root.textContent).toContain(expected);
      expect(root.textContent).not.toContain("14.09.2026");
      expect(root.querySelector(".charge-plan__target")).toBeNull();
    }
  });

  it.each(["de", "en-GB"])(
    "warns about a shortfall and describes only partial charging (%s)",
    async (language) => {
      const { root, update } = await mount(language);
      await update("insufficient", { ...planned, shortfall_kwh: 1.234 });
      expect(root.textContent).toContain(
        language === "de" ? "Fehlbetrag: 1,23 kWh" : "shortfall: 1.23 kWh",
      );
      expect(root.textContent).toContain(
        language === "de"
          ? "teilweise Aufladung"
          : "Partial low-tariff charging",
      );
      expect(root.textContent).not.toContain("Daher beginnt");
      expect(root.textContent).not.toContain("Therefore");
      await update("insufficient", { pv_start: planned.pv_start });
      expect(root.textContent).not.toContain("NaN");
      expect(root.textContent).not.toContain("kWh");
      expect(root.textContent).not.toContain("00:00");
    },
  );

  it.each([null, "invalid", "2026-09-13T22:00:00", ""])(
    "does not invent a charging time for a missing or invalid timestamp (%s)",
    async (chargeStart) => {
      const { root, update } = await mount();
      await update("planned", { ...planned, charge_start: chargeStart });
      expect(root.textContent).toContain("noch unvollständig");
      expect(root.textContent).not.toContain("Daher beginnt");
      expect(root.textContent).not.toContain("Invalid Date");
    },
  );

  it("keeps the shortfall warning when a partial plan starts charging", async () => {
    const { root, update } = await mount();
    await update("charging", { ...planned, shortfall_kwh: 1.2 });
    expect(root.textContent).toContain("Fehlbetrag: 1,20 kWh");
    expect(root.textContent).toContain(
      "teilweise Aufladung im Niedertarif läuft seit",
    );
    expect(root.textContent).not.toContain("um die Zeit bis zum PV-Start um");
  });

  it("omits invalid measurements and missing forecast timestamps", async () => {
    const { root, update } = await mount();
    await update("planned", {
      ...planned,
      observation_minutes: 0.5,
      average_discharge_w: "NaN",
      target_soc: 101,
    });
    expect(root.textContent).not.toContain("letzten");
    expect(root.textContent).not.toContain("NaN");
    expect(root.textContent).not.toContain("Ladeziel");
    await update("not_needed", {});
    expect(root.textContent).toContain("derzeit nicht erforderlich");
    expect(root.textContent).not.toContain("PV-Start um");
  });

  it("follows metadata availability and hides stale plans when the sensor is unavailable", async () => {
    const fixture = await mount();
    for (const state of ["unknown", "unavailable", "unrecognized_state"]) {
      await fixture.update(state);
      expect(fixture.root.textContent).toContain("derzeit nicht verfügbar");
      expect(fixture.root.textContent).not.toContain("14.09.2026");
    }
    await fixture.metadata(false);
    expect(fixture.root.querySelector(".charge-plan")).toBeNull();
    await fixture.metadata(true);
    await fixture.update("planned");
    expect(fixture.root.textContent).toContain("Daher beginnt");
    await fixture.disconnect();
    expect(fixture.root.textContent).not.toContain("Daher beginnt");
    expect(fixture.callService).not.toHaveBeenCalled();
    expect(fixture.callWS).not.toHaveBeenCalled();
  });
});
