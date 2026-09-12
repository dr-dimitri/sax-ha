export const tabs = [
  {
    path: "allgemein",
    de: "Allgemeine Informationen",
    en: "General information",
  },
  { path: "ladeautomatik", de: "Ladeautomatik", en: "Scheduled charging" },
  {
    path: "netzdienliches-laden",
    de: "Netzdienliches Laden",
    en: "Grid-serving charging",
  },
  {
    path: "dynamisches-laden",
    de: "Dynamisches Laden",
    en: "Dynamic charging",
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
    preview: "Vorschau",
    introduction:
      "Das neue Dashboard entsteht parallel zu Ihrer bisherigen Ansicht.",
    introductionStandalone: "Das neue SAX-Power-Dashboard entsteht hier.",
    existing: "Bestehendes Dashboard öffnen",
    preparation: "Dieser Bereich wird vorbereitet",
    description:
      "Die Anzeigen und Einstellungen finden Sie weiterhin im bestehenden SAX-Power-Dashboard. Sie werden Schritt für Schritt auch hier verfügbar.",
    descriptionStandalone:
      "Die Anzeigen und Einstellungen dieses Bereichs sind noch in Vorbereitung. Sie werden Schritt für Schritt hier verfügbar.",
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
    preview: "Preview",
    introduction:
      "The new dashboard is being built alongside your existing dashboard.",
    introductionStandalone: "The new SAX Power dashboard is taking shape here.",
    existing: "Open existing dashboard",
    preparation: "This section is being prepared",
    description:
      "Your displays and settings remain available in the existing SAX Power dashboard. They will gradually become available here too.",
    descriptionStandalone:
      "The displays and settings for this section are being prepared. They will gradually become available here.",
    loading: "Loading Home Assistant …",
    missingEntry:
      "No SAX Power device is assigned to this dashboard yet. Please reload the integration.",
    notFound: "Section not found",
    notFoundDescription:
      "This dashboard section is unavailable. Choose one of the sections above.",
    returnToOverview: "Back to overview",
  },
} satisfies Record<Language, Record<string, string>>;
