<script setup lang="ts">
import { computed, provide, ref } from "vue";
import SavingsView from "./views/SavingsView.vue";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "./ha";
import type {
  DashboardEntityMetadata,
  HassEntity,
  HomeAssistant,
  TariffProfile,
} from "./types";
import type { SavingsStatistics } from "./savings";

const language = ref("de");
const dark = ref(false);
const state = ref("active");
const tariff = ref("time_of_use");
const previewTariff = ref<TariffProfile>({
  tariff_type: "time_of_use",
  base_price_ct_kwh: 28.92,
  feed_in_price_ct_kwh: 7.8,
  windows: [
    { start: "00:00:00", end: "06:00:00", price_ct_kwh: 18.92 },
    { start: "17:00:00", end: "21:00:00", price_ct_kwh: 38.92 },
  ],
  revision: "preview-1",
  can_edit: true,
});
const empty = ref(false);
const investment = ref(true);
const metadata: DashboardEntityMetadata[] = [
  [
    "binary_sensor",
    "economics_investment_configured",
    "Investition hinterlegt",
  ],
  ["sensor", "economics_amortization_progress", "Amortisationsfortschritt"],
  [
    "sensor",
    "economics_remaining_to_payback",
    "Restbetrag bis zur Amortisation",
  ],
  ["sensor", "economics_roi", "Amortisationsergebnis"],
  ["sensor", "economics_net_savings", "Netto-Ersparnis"],
  ["sensor", "economics_status", "Wirtschaftlichkeitsstatus"],
  ["sensor", "economics_current_import_price", "Aktueller Netzbezugspreis"],
].map(([domain, key, name]) => ({
  domain: domain as "sensor" | "binary_sensor",
  key,
  name,
  entity_id: `${domain}.demo_${key}`,
  states: {},
  can_control: false,
}));
const connection = {
  connected: true,
  async subscribeMessage<T>(
    callback: (value: T) => void,
    message: Readonly<Record<string, unknown>>,
  ) {
    if (message.type === "sax_power/dashboard/subscribe")
      callback({ entities: metadata } as T);
    return () => {};
  },
  addEventListener() {},
  removeEventListener() {},
};
const hass = computed<HomeAssistant>(() => {
  const values = [
    investment.value ? "on" : "off",
    "43.35",
    "4248.55",
    "3251.45",
    "251.45",
    state.value,
    "28.92",
  ];
  const states: Record<string, HassEntity> = Object.fromEntries(
    metadata.map((item, index) => [
      item.entity_id,
      {
        entity_id: item.entity_id,
        state: values[index],
        attributes:
          item.key === "economics_roi"
            ? { prior_result_eur: 3000 }
            : item.key === "economics_status"
              ? { economics_started_at: "2026-01-01T00:00:00+01:00" }
              : item.key === "economics_current_import_price"
                ? {
                    tariff_type: tariff.value,
                    unit_of_measurement: "ct/kWh",
                    windows: previewTariff.value.windows.map(
                      (window, index) => ({
                        ...window,
                        price_eur_kwh: window.price_ct_kwh / 100,
                        low_tariff: index === 0,
                      }),
                    ),
                    active_window: null,
                    base_price_eur_kwh:
                      previewTariff.value.base_price_ct_kwh! / 100,
                    feed_in_price_eur_kwh:
                      previewTariff.value.feed_in_price_ct_kwh! / 100,
                    next_price_change_at: "2026-09-12T17:00:00+02:00",
                    unavailable_reason: null,
                    low_tariff_price_eur_kwh: 0.1892,
                    base_price_is_low_tariff: false,
                    low_tariff_active: false,
                    low_tariff_valid_until: null,
                  }
                : {},
      },
    ]),
  );
  return {
    language: language.value,
    states,
    connection,
    config: { time_zone: "Europe/Berlin" },
    locale: {
      language: language.value,
      time_format: "twenty_four",
      first_weekday: "language",
    },
    async callWS<T>(message: Readonly<Record<string, unknown>>) {
      if (message.type === "sax_power/dashboard/tariff/get")
        return { ...previewTariff.value, tariff_type: tariff.value } as T;
      if (message.type === "sax_power/dashboard/tariff/save") {
        previewTariff.value = {
          ...previewTariff.value,
          ...message,
          revision: `${previewTariff.value.revision}-saved`,
        } as TariffProfile;
        return previewTariff.value as T;
      }
      const startDate =
        typeof message.start_date === "string"
          ? message.start_date
          : "2026-09-12";
      const endDate =
        typeof message.end_date === "string" ? message.end_date : "2026-09-12";
      const offset = Date.parse(`${startDate}T00:00:00+02:00`);
      const changes = empty.value
        ? []
        : [
            -0.24, -0.45, -0.1, 0, 0.42, 0.87, 1.15, 0.67, 0.84, 0.92, 1.44,
            0.48,
          ];
      const period = (change: number) => ({
        start: `${startDate}T00:00:00+02:00`,
        end: null,
        change: empty.value ? null : change,
      });
      const result: SavingsStatistics = {
        entity_id: "sensor.demo_economics_net_savings",
        time_zone: "Europe/Berlin",
        today: "2026-09-12",
        status: "ok",
        periods: {
          day: period(6),
          week: period(12.15),
          month: period(28.4),
          year: period(251.45),
        },
        selected: {
          start_date: startDate,
          end_date: endDate,
          start: `${startDate}T00:00:00+02:00`,
          end: `${endDate}T23:59:59+02:00`,
          change: empty.value ? null : 6,
          period: "hour",
          buckets: changes.map((change, index) => ({
            start: new Date(offset + index * 3600000).toISOString(),
            end: new Date(offset + (index + 1) * 3600000).toISOString(),
            change,
          })),
        },
      };
      return result as T;
    },
  };
});
provide(
  SAX_DASHBOARD_KEY,
  useSaxDashboard(
    () => hass.value,
    () => "demo",
  ),
);
</script>

<template>
  <div class="preview" :class="{ 'preview--dark': dark }">
    <header>
      <p>LOKALE DEMO · BEISPIELDATEN</p>
      <h1>Amortisation</h1>
      <div class="preview-controls">
        <label
          >Sprache
          <select v-model="language">
            <option value="de">Deutsch</option>
            <option value="en">English</option>
          </select></label
        >
        <label
          >Status
          <select v-model="state">
            <option value="active">Aktiv</option>
            <option value="disabled">Deaktiviert</option>
            <option value="price_unavailable">Preis fehlt</option>
            <option value="origin_unavailable">Herkunft fehlt</option>
            <option value="partial_price_coverage">
              Teilweise Preisabdeckung
            </option>
            <option value="storage_error">Speicherfehler</option>
            <option value="unknown">Unbekannt</option>
          </select></label
        >
        <label
          >Tarif
          <select v-model="tariff">
            <option value="time_of_use">Tageszeitabhängig</option>
            <option value="fixed">Festpreis</option>
          </select></label
        >
        <label
          ><input v-model="investment" type="checkbox" /> Investition
          hinterlegt</label
        ><label
          ><input v-model="empty" type="checkbox" /> Leere Statistik (danach
          aktualisieren)</label
        ><label><input v-model="dark" type="checkbox" /> Dunkel</label>
      </div>
      <p>
        Die Werte stammen ausschließlich aus lokalen Beispielen. Es gibt keine
        Verbindung zu einem Speicher.
      </p>
    </header>
    <SavingsView :hass="hass" entry-id="demo" />
  </div>
</template>

<style>
:host {
  display: block;
  font-family: Roboto, Arial, sans-serif;
}
.preview {
  --primary-color: #0288d1;
  box-sizing: border-box;
  min-height: 100vh;
  padding: 32px;
  background: var(--primary-background-color, #fafafa);
  color: var(--primary-text-color, #212121);
}
.preview > * {
  max-width: 1080px;
  margin-inline: auto;
}
.preview header p {
  line-height: 1.6;
  color: var(--secondary-text-color, #666);
}
.preview header p:first-child {
  font-size: 12px;
  letter-spacing: 0.12em;
}
.preview h1 {
  font-size: 32px;
  font-weight: 400;
  margin: 8px 0 24px;
}
.preview-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}
.preview-controls label {
  display: flex;
  align-items: center;
  gap: 8px;
}
.preview-controls select {
  font: inherit;
  padding: 8px;
  min-height: 44px;
  background: var(--card-background-color, #fff);
  color: inherit;
  border: 1px solid var(--divider-color, #ddd);
  border-radius: 6px;
}
.preview--dark {
  --primary-background-color: #111;
  --primary-text-color: #e6e6e6;
  --secondary-text-color: #aaa;
  --card-background-color: #1c1c1c;
  --divider-color: #404040;
  --secondary-background-color: #2c2c2c;
  --primary-color: #4fc3f7;
}
@media (max-width: 600px) {
  .preview {
    padding: 20px 12px;
  }
}
</style>
