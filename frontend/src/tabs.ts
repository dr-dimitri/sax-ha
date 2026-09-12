export const tabs = [
  {
    path: "allgemein",
    de: "Allgemeine Informationen",
    en: "General information",
  },
  {
    path: "ladeautomatik",
    de: "Zeitvariabler Tarif",
    en: "Time-of-use tariff",
  },
  {
    path: "dynamisches-laden",
    de: "Dynamischer Tarif",
    en: "Dynamic tariff",
  },
  {
    path: "netzdienliches-laden",
    de: "Netzdienliches Laden",
    en: "Grid-serving charging",
  },
  { path: "ersparnis", de: "Ersparnis", en: "Savings" },
] as const;

export type Language = "de" | "en";

export function tabPath(path: string, basePath: string): string {
  const pathname = path.split(/[?#]/, 1)[0].replace(/\/+$/, "");
  const relativePath = pathname.startsWith(`${basePath}/`)
    ? pathname.slice(basePath.length)
    : pathname === basePath
      ? ""
      : pathname;
  return relativePath.replace(/^\//, "") || tabs[0].path;
}

export const messages = {
  de: {
    navigation: "Dashboard-Bereiche",
    menu: "Seitenleiste öffnen",
    introduction:
      "Gerätewerte, Ladeeinstellungen und Ersparnis Ihres SAX-Power-Speichers.",
    loading: "Home Assistant wird geladen …",
    missingEntry:
      "Diesem Dashboard ist noch kein SAX-Power-Gerät zugeordnet. Bitte laden Sie die Integration neu.",
    notFound: "Bereich nicht gefunden",
    notFoundDescription:
      "Dieser Dashboard-Bereich ist nicht verfügbar. Wählen Sie einen der oben angezeigten Bereiche.",
    returnToOverview: "Zur Übersicht",
  },
  en: {
    navigation: "Dashboard sections",
    menu: "Open sidebar",
    introduction:
      "Device values, charging settings and savings for your SAX Power battery.",
    loading: "Loading Home Assistant …",
    missingEntry:
      "No SAX Power device is assigned to this dashboard yet. Please reload the integration.",
    notFound: "Section not found",
    notFoundDescription:
      "This dashboard section is unavailable. Choose one of the sections above.",
    returnToOverview: "Back to overview",
  },
} satisfies Record<Language, Record<string, string>>;
