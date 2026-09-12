export interface HomeAssistant {
  language: string;
  states: Readonly<Record<string, unknown>>;
  panels?: Readonly<Record<string, unknown>>;
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
