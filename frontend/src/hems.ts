import type { HomeAssistant } from "./types";

type Language = "de" | "en";
const reasons: Record<string, readonly [string, string]> = {
  soc_stale: [
    "Der Ladezustand ist für eine sichere Ladefreigabe zu alt.",
    "State of charge is too old to permit charging safely.",
  ],
  below_start_threshold: [
    "Der berechnete Ladebedarf liegt unter der Startschwelle für eine neue Netzladung.",
    "Calculated charging demand is below the threshold for starting a new grid charge.",
  ],
  price_limit_missing: [
    "Für die bedarfsgesteuerte Strategie fehlt eine gültige Preisgrenze.",
    "Demand-based charging requires a valid price limit.",
  ],
  no_price_data: [
    "Für die benötigten Tarifzeiten fehlen Preisdaten.",
    "Price data is missing for the required tariff periods.",
  ],
  invalid_planning_time: [
    "Der Prüfzeitpunkt ist ungültig.",
    "The evaluation time is invalid.",
  ],
  invalid_device_data: [
    "Für den sicheren Ladevollzug fehlen gültige Gerätedaten.",
    "Valid device data required for safe charging is missing.",
  ],
  discharge_power_unavailable: [
    "Die verfügbare Entladeleistung fehlt.",
    "Available discharging power is unknown.",
  ],
  night_geometry_unavailable: [
    "Der Nachtzeitraum ist nicht zuverlässig bestimmt.",
    "The night period is not known reliably.",
  ],
  unsupported_load_basis: [
    "Die Quelle liefert keine nächtliche SAX-Entladeenergie.",
    "The source does not provide night-time SAX discharge energy.",
  ],
  invalid_forecast_intervals: [
    "Die Prognoseintervalle sind ungültig.",
    "Forecast intervals are invalid.",
  ],
  invalid_tariff_constraints: [
    "Die Tarifzeiten oder Ladegrenzen sind ungültig.",
    "Tariff periods or charging limits are invalid.",
  ],
  no_charge_window: [
    "Im zulässigen Zeitraum ist kein Ladefenster freigegeben.",
    "No charging window is permitted in the available period.",
  ],
  planning_solver_failed: [
    "Es konnte kein verlässlicher Ladeplan berechnet werden.",
    "A reliable charging plan could not be calculated.",
  ],
  history_invalid: [
    "Die aufgezeichnete Entladehistorie enthält ungültige Daten.",
    "Recorded discharge history contains invalid data.",
  ],
  max_soc: [
    "Die maximale SOC-Grenze verhindert derzeit Netzladen.",
    "The maximum SOC limit currently prevents grid charging.",
  ],
  grid_serving: [
    "Die netzdienliche Steuerung hat derzeit Vorrang.",
    "Grid-serving control currently takes priority.",
  ],
  pv_invalid_intervals: [
    "Die Grenzen der PV-Prognoseintervalle sind ungültig.",
    "Solar forecast interval boundaries are invalid.",
  ],
  pv_overlapping_intervals: [
    "Überlappende PV-Angaben wurden als Datenlücken behandelt.",
    "Overlapping solar intervals were treated as missing data.",
  ],
  pv_partial_coverage: [
    "Die PV-Abdeckung ist teilweise. Maßgeblich ist die vollständige Abdeckung bis zur PV-Versorgung und ihrem 60-Minuten-Nachweis.",
    "Solar coverage is partial. Complete coverage up to solar supply and its 60-minute confirmation is what matters.",
  ],
  pv_invalid_interval_value: [
    "Ungültige PV-Energie- oder Leistungsangaben wurden ausgelassen.",
    "Invalid solar energy or power values were omitted.",
  ],
  pv_input_fallbacks: [
    "PV-Intervalle mit Ersatzwerten wurden ausgelassen.",
    "Solar intervals using fallback input values were omitted.",
  ],
  pv_incomplete_forecast: [
    "Unvollständige PV-Intervalle wurden ausgelassen.",
    "Incomplete solar intervals were omitted.",
  ],
  pv_no_valid_intervals: [
    "Die PV-Prognose enthält keine nutzbaren Intervalle.",
    "The solar forecast contains no usable intervals.",
  ],
  pv_unsupported_schema: [
    "Die PV-Quelle liefert ein nicht unterstütztes Antwortformat.",
    "The solar source returned an unsupported response format.",
  ],
  pv_invalid_scope: [
    "Die PV-Prognose beschreibt nicht die vollständige Anlage.",
    "The solar forecast does not describe the whole installation.",
  ],
  pv_invalid_metadata: [
    "Zeitzone oder Abdeckungsangaben der PV-Prognose sind ungültig.",
    "The solar forecast time zone or coverage metadata is invalid.",
  ],
  pv_missing_update_status: [
    "Die PV-Quelle bestätigt keinen erfolgreichen Abruf.",
    "The solar source does not confirm a successful update.",
  ],
  pv_invalid_response: [
    "Die PV-Quelle hat keine gültige Prognose geliefert.",
    "The solar source did not return a valid forecast.",
  ],
  pv_invalid_fetched_at: [
    "Der PV-Abrufzeitpunkt ist ungültig.",
    "The solar retrieval timestamp is invalid.",
  ],
  pv_future_fetched_at: [
    "Der PV-Abrufzeitpunkt liegt in der Zukunft.",
    "The solar retrieval timestamp is in the future.",
  ],
  pv_adapter_closed: [
    "Die PV-Quelle wurde entladen.",
    "The solar source was unloaded.",
  ],
  pv_query_in_progress: [
    "Eine PV-Abfrage läuft bereits.",
    "A solar query is already running.",
  ],
  night_slot_mean: [
    "Direkt beobachteter Uhrzeitslot",
    "Directly observed time slot",
  ],
  pooled_night_estimate: [
    "Gepooltes Nachtlastniveau",
    "Pooled night load level",
  ],
  dawn_extrapolation: [
    "Begrenzte Dämmerungsfortschreibung",
    "Limited dawn estimate",
  ],
  pooled_dawn_estimate: [
    "Dämmerungsschätzung aus dem gepoolten Nachtlastniveau",
    "Dawn estimate based on the pooled night load level",
  ],
  battery_covers_bridge: [
    "Die nutzbare Speicherenergie deckt den Bedarf bis zur erwarteten PV-Versorgung.",
    "Usable battery energy covers demand until the expected solar supply.",
  ],
  night_bridge_required: [
    "Die Nachtbrücke benötigt zusätzliche Netzenergie innerhalb der freigegebenen Tarifzeiten.",
    "The night bridge needs additional grid energy within permitted tariff periods.",
  ],
  waiting_for_pv_in_cheap_window: [
    "Kein Netzladen geplant: PV versorgt den Bedarf noch innerhalb des günstigen Zeitfensters.",
    "No grid charging planned: solar supply will cover demand within the cheap window.",
  ],
  pv_supplies_load: [
    "Die PV-Prognose deckt den verbleibenden Bedarf.",
    "The solar forecast covers remaining demand.",
  ],
  unmet_need: [
    "Der Bedarf kann unter den geltenden Zeit-, Leistungs- und SOC-Grenzen nicht vollständig gedeckt werden.",
    "Demand cannot be fully covered within the available time, power and SOC limits.",
  ],
  outside_model_scope: [
    "Außerhalb des Nachtmodells: Die Planung umfasst die Nacht und höchstens vier Stunden nach Sonnenaufgang.",
    "Outside the night model: planning covers the night and at most four hours after sunrise.",
  ],
  pv_supply_unconfirmed: [
    "Innerhalb der Dämmerungsgrenze ist keine durchgehend ausreichende PV-Versorgung für 60 Minuten nachgewiesen.",
    "Continuous sufficient solar supply for 60 minutes is not confirmed within the dawn limit.",
  ],
  invalid_soc_limits: [
    "Die SOC-Grenzen passen nicht zusammen. Reserve und maximale Ladegrenze prüfen.",
    "The SOC limits conflict. Check the reserve and maximum charging limit.",
  ],
  soc_unavailable: [
    "Der Ladezustand fehlt oder ist veraltet.",
    "Battery state of charge is missing or stale.",
  ],
  capacity_unavailable: [
    "Die nutzbare Speicherkapazität fehlt.",
    "Usable battery capacity is unavailable.",
  ],
  charge_power_unavailable: [
    "Die verfügbare Ladeleistung fehlt.",
    "Available charging power is unknown.",
  ],
  device_unavailable: [
    "Der Speicher ist nicht verfügbar.",
    "The battery is unavailable.",
  ],
  invalid_efficiency: [
    "Die Wirkungsgradannahmen sind ungültig.",
    "The efficiency assumptions are invalid.",
  ],
  pv_provider_not_configured: [
    "Für die Nachtregelung ist noch keine PV-Quelle eingerichtet.",
    "No solar source is configured for night control.",
  ],
  pv_source_unavailable: [
    "Die ausgewählte PV-Anlage ist nicht verfügbar oder nicht eindeutig zugeordnet.",
    "The selected solar installation is unavailable or cannot be identified uniquely.",
  ],
  pv_missing_fetched_at: [
    "Der tatsächliche Abrufzeitpunkt der PV-Prognose fehlt.",
    "The actual solar forecast retrieval timestamp is missing.",
  ],
  pv_stale_forecast: [
    "Die PV-Prognose überschreitet ihr zulässiges Datenalter.",
    "The solar forecast exceeds its permitted age.",
  ],
  pv_stale: ["Die PV-Prognose ist veraltet.", "The solar forecast is stale."],
  pv_update_failed: [
    "Der letzte gemeldete PV-Abruf ist fehlgeschlagen.",
    "The last reported solar update failed.",
  ],
  pv_source_changed: [
    "Die PV-Quelle wurde während der Prüfung geändert. Eine neue Prüfung ist erforderlich.",
    "The solar source changed during evaluation. A new evaluation is required.",
  ],
  pv_query_timeout: [
    "Die PV-Abfrage hat nicht rechtzeitig geantwortet.",
    "The solar query timed out.",
  ],
  pv_query_failed: [
    "Die PV-Quelle konnte nicht gelesen werden.",
    "The solar source could not be read.",
  ],
  pv_coverage_missing: [
    "Im entscheidungsrelevanten Zeitraum fehlen PV-Intervalle.",
    "Solar intervals are missing in the period required for this decision.",
  ],
  load_coverage_missing: [
    "Im entscheidungsrelevanten Zeitraum fehlt eine belastbare Nachtlastschätzung.",
    "The required period has no usable night load estimate.",
  ],
  history_unavailable: [
    "Die SAX-Entladehistorie ist noch nicht verfügbar.",
    "SAX discharge history is not yet available.",
  ],
  history_stale: [
    "Die Entladehistorie ist veraltet.",
    "Discharge history is stale.",
  ],
  insufficient_history: [
    "Es fehlen verwertbare Beobachtungen aus mindestens drei Nächten mit zusammen sechs Stunden.",
    "Usable observations from at least three nights with six hours in total are required.",
  ],
  unsupported_night_geometry: [
    "Sonnenaufgang und Sonnenuntergang konnten nicht zuverlässig bestimmt werden.",
    "Sunrise and sunset could not be determined reliably.",
  ],
  awaiting_evaluation: [
    "Die nächste Prüfung wird vorbereitet.",
    "The next evaluation is being prepared.",
  ],
  evaluating: ["Die Prüfung läuft.", "Evaluation is running."],
  evaluation_failed: [
    "Die Prüfung konnte nicht abgeschlossen werden.",
    "Evaluation could not be completed.",
  ],
  calibration: [
    "Mehrladung für Zellkalibrierung bis 100 %. Der reguläre Bedarf bleibt separat sichtbar.",
    "Additional charging to 100% for cell calibration. Regular demand remains visible separately.",
  ],
  manual_override: [
    "Manuelle Steuerung verhindert derzeit die Ausführung des Plans.",
    "Manual control currently prevents the plan from running.",
  ],
  pv_surplus: [
    "PV-Überschuss verhindert derzeit die geplante Netzladung.",
    "Solar surplus currently prevents planned grid charging.",
  ],
  price_limit: [
    "Die Preisgrenze erlaubt derzeit keine Netzladung.",
    "The price limit currently prevents grid charging.",
  ],
  outside_window: [
    "Das freigegebene Ladezeitfenster ist derzeit geschlossen.",
    "The permitted charging window is currently closed.",
  ],
  inactive: [
    "Die bedarfsgesteuerte Regelung ist für diesen Tarif deaktiviert.",
    "Demand-based control is disabled for this tariff.",
  ],
  observed_slot: [
    "Direkt beobachteter Uhrzeitslot",
    "Directly observed time slot",
  ],
  pooled_night: ["Gepooltes Nachtlastniveau", "Pooled night load level"],
  dawn_extension: [
    "Begrenzte Dämmerungsfortschreibung",
    "Limited dawn estimate",
  ],
};

export function hemsReason(code: unknown, language: Language): string {
  if (typeof code !== "string" || !code)
    return language === "de" ? "Unbekannt" : "Unknown";
  if (!reasons[code] && code.startsWith("pv_source_"))
    return language === "de"
      ? `Qualitätshinweis der PV-Quelle: ${code.slice(10)}`
      : `Solar source quality flag: ${code.slice(10)}`;
  return (
    reasons[code]?.[language === "de" ? 0 : 1] ??
    (language === "de"
      ? `Weitere Einschränkung: ${code}`
      : `Additional constraint: ${code}`)
  );
}

export function hemsNumber(
  value: unknown,
  language: Language,
  unit = "",
): string {
  if (typeof value !== "number" || !Number.isFinite(value))
    return language === "de" ? "Unbekannt" : "Unknown";
  return `${new Intl.NumberFormat(language === "de" ? "de-DE" : "en-GB", { maximumFractionDigits: 2 }).format(value)}${unit ? ` ${unit}` : ""}`;
}

export function hemsTime(
  value: unknown,
  language: Language,
  hass?: HomeAssistant,
): string {
  if (typeof value !== "string" || !/(Z|[+-]\d{2}:\d{2})$/.test(value))
    return language === "de" ? "Unbekannt" : "Unknown";
  const date = new Date(value);
  if (!Number.isFinite(date.getTime()))
    return language === "de" ? "Unbekannt" : "Unknown";
  try {
    return new Intl.DateTimeFormat(
      hass?.locale?.language ?? (language === "de" ? "de-DE" : "en-GB"),
      {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: hass?.config?.time_zone,
        hour12: hass?.locale?.time_format === "am_pm",
      },
    ).format(date);
  } catch {
    return language === "de" ? "Unbekannt" : "Unknown";
  }
}
