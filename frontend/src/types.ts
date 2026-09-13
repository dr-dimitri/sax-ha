export type EntityDomain =
  "sensor" | "binary_sensor" | "switch" | "number" | "time" | "select";

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Readonly<Record<string, unknown>>;
  last_changed?: string;
  last_updated?: string;
  context?: { id: string; parent_id?: string | null; user_id?: string | null };
}

export interface DashboardEntityMetadata {
  entity_id: string;
  domain: EntityDomain;
  device_id?: string | null;
  key: string;
  name: string | null;
  states: Readonly<Record<string, string>>;
  can_control: boolean;
}

export interface DashboardMetadata {
  entities: readonly DashboardEntityMetadata[];
}

export interface TariffPriceWindow {
  start: string;
  end: string;
  price_ct_kwh: number;
}

export interface TariffProfile {
  tariff_type: string;
  base_price_ct_kwh: number | null;
  feed_in_price_ct_kwh: number | null;
  windows: TariffPriceWindow[];
  revision: string;
  can_edit: boolean;
  can_configure?: boolean;
  automation_enabled?: boolean | null;
  profiles?: {
    time_of_use: TimeOfUseProfile;
    dynamic: DynamicTariffProfile;
  };
}

export interface TimeOfUseProfile {
  base_price_ct_kwh: number | null;
  feed_in_price_ct_kwh: number | null;
  windows: TariffPriceWindow[];
  pv_sensor: string | null;
}

export interface DynamicTariffProfile {
  feed_in_price_ct_kwh: number | null;
  price_sensor: string | null;
  price_attribute: string | null;
  price_unit: "auto" | "eur_kwh" | "ct_kwh" | "eur_mwh" | "ct_mwh";
  pv_sensor: string | null;
  pv_factor: number;
}

export interface TariffConfiguration {
  revision: string;
  tariff_type: "time_of_use" | "dynamic";
  profile?: TimeOfUseProfile | DynamicTariffProfile;
  automation_enabled?: boolean;
}

export interface TariffPriceSeries {
  tariff_type: string;
  day: "today" | "tomorrow";
  date: string;
  time_zone: string;
  start: string;
  end: string;
  now: string;
  current_price_ct_kwh: number | null;
  status: "available" | "partial" | "unavailable";
  reason: string | null;
  slots: { start: string; end: string; price_ct_kwh: number }[];
  gaps: { start: string; end: string }[];
  revision: string;
}

export interface TariffDraft {
  revision: string;
  base_price_ct_kwh: number;
  feed_in_price_ct_kwh: number;
  windows: TariffPriceWindow[];
}

export type ConnectionEvent = "ready" | "disconnected" | "reconnect-error";
export type Unsubscribe = () => Promise<void> | void;

export interface HassConnection {
  readonly connected: boolean;
  subscribeMessage<T>(
    callback: (message: T) => void,
    message: Readonly<Record<string, unknown>>,
    options?: { resubscribe?: boolean },
  ): Promise<Unsubscribe>;
  addEventListener(event: ConnectionEvent, listener: () => void): void;
  removeEventListener(event: ConnectionEvent, listener: () => void): void;
}

export interface HomeAssistant {
  language: string;
  states: Readonly<Record<string, HassEntity>>;
  callWS?<T>(message: Readonly<Record<string, unknown>>): Promise<T>;
  connection?: HassConnection;
  connected?: boolean;
  locale?: {
    language?: string;
    first_weekday?: string;
    number_format?: string;
    time_format?: string;
  };
  config?: { time_zone?: string };
  formatEntityState?(entity: HassEntity, state?: string): string;
  callService?(
    domain: string,
    service: string,
    serviceData?: Record<string, unknown>,
    target?: { entity_id?: string | string[] },
    notifyOnError?: boolean,
    returnResponse?: boolean,
  ): Promise<unknown>;
  dockedSidebar?: "docked" | "always_hidden" | "auto";
  kioskMode?: boolean;
}

export interface PanelInfo {
  config?: {
    entry_id?: string;
  };
  url_path?: string;
}

export interface PanelRoute {
  path: string;
  prefix?: string;
}
