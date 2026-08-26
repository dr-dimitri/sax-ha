# Entwicklerdokumentation

Interna zur Implementierung der SAX-Power-Home-Integration. Für die
Benutzerdokumentation siehe [README.md](README.md). Für KI-Coding-Agenten
siehe [AGENTS.md](AGENTS.md) (Setup-/Test-/Lint-Befehle, Code-Stil,
Git-Workflow) sowie [anforderung.yaml](anforderung.yaml) (feature-bezogene
Ist-Zustand-Anforderungen je REQ-ID).

## Inhaltsverzeichnis

- [Aufbau](#aufbau)
- [Datenfluss](#datenfluss)
- [Startreihenfolge und Persistenz der Ladeeinstellungen](#startreihenfolge-und-persistenz-der-ladeeinstellungen)
- [Register-Mapping](#register-mapping)
- [SunSpec-Skalierung](#sunspec-skalierung)
- [Refresh-Verhalten](#refresh-verhalten)
- [Tests](#tests)
  - [Manuelle Testausführung](#manuelle-testausführung)
  - [Test gegen echte Hardware](#test-gegen-echte-hardware)
- [Releaseprozess](#releaseprozess)
- [Lokale Entwicklung (DevContainer)](#lokale-entwicklung-devcontainer)
- [Quellen](#quellen)

## Aufbau

```
custom_components/sax_power/
├── manifest.json      Metadaten, Requirements (pymodbus==3.13.1), Domain
├── const.py            Register-/Konfigurationskonstanten, Defaults
├── domain/              Reine, frameworkunabhängige Regeln: Register-Codecs,
│                          SunSpec-Blockdecodierung (sunspec.py),
│                          Zeitfenster und Wertevalidierung, Preis-Einheiten
│                          (price_units.py), das Tarifmodell (tariff.py), die
│                          Herkunftsbilanzregel der Ladeenergie
│                          (energy_accounting.py), die Geldbilanz darauf
│                          (economics_accounting.py) sowie die ROI-/
│                          Amortisationsprognose darüber
│                          (economics_amortization.py)
├── application/         Use-Case-Policies für Ladeprioritäten und periodische
│                          Vollkalibrierung, die Abbildung der Tarif-Options auf
│                          das Domänenmodell (economics.py) sowie der
│                          injizierbare Modbus-Client-Port
├── infrastructure/      Home-Assistant-Adapter für zustandsbasierte
│                          Repair-Issues sowie die vier versionierten Stores
│                          (Kalibrierung, Energiezähler inkl. Herkunft der
│                          Ladeenergie, Wirtschaftlichkeitsbilanz,
│                          Ladeeinstellungen)
├── config_flow.py       GUI-Einrichtung (Verbindung + optionale
│                          Netzladung-Vorbelegung), Verbindungsvalidierung,
│                          Options Flow (preisoptimiertes Laden + gemeinsame
│                          PV-Prognose)
├── coordinator.py       DataUpdateCoordinator: Reads (Basic+SunSpec), Writes,
│                          Poll-Intervalle/Caches, Max-SOC-Logik, Netzladung,
│                          zeitgesteuertes Laden, netzdienliches Laden,
│                          preisoptimiertes Laden (Anwendung des Ladeplans),
│                          Zeitfenster-Überlappungsprüfung
├── price_optimizer.py    Preisoptimiertes Laden: Einlesen der Preisdaten aus
│                          einer beliebigen Preis-Sensor-Entity, Ladeplanung je
│                          Strategie, gemeinsame Prognosequelle,
│                          60-Sekunden-Takt - ohne Modbus-Zugriff
├── economics.py          Home-Assistant-Adapter des Tarifmodells
│                          (SaxTariffProvider): liest Options und Preis-Sensor
│                          und liefert den geltenden Netzbezugspreis als Quote,
│                          siehe anforderung.yaml REQ-ECONOMICS-TARIFFS. Die
│                          Geldbilanz selbst (REQ-ECONOMICS-ACCOUNTING) hat
│                          keinen eigenen Adapter - sie läuft im Coordinator
│                          mit (_accumulate_economics, siehe unten), weil sie
│                          keine eigenen HA-Zustandsbeobachter braucht
├── entity.py             Basisklasse mit gemeinsamer DeviceInfo,
│                          _assign_ids() (unique_id + vom Gerätenamen
│                          unabhängige entity_id, siehe
│                          REQ-STABLE-DEVICE-IDENTITY),
│                          initial_config_value() (Config-Entry-Fallback)
├── __init__.py            Setup/Teardown des Config Entry, Service-Registrierung
├── sensor.py              ~90 Sensoren, beschreibungsbasiert (eine Klasse, eine Liste),
│                          plus zwei RestoreEntity-Energiezähler (energy_charged/
│                          energy_discharged) fürs Energy-Dashboard
├── number.py              Max. SOC (einzige SOC-Einstellung, auch Ziel-SOC für
│                          Zeitfenster- und preisoptimiertes Laden), Netzladung
│                          Min. SOC, Mindest-PV-Prognose für netzdienliches
│                          Laden, Preisgrenze/Anzahl Stunden
│                          (preisoptimiertes Laden)
├── select.py              Strategie des preisoptimierten Ladens
├── switch.py              Speicher ein/aus, zeitgesteuertes Laden ein/aus,
│                          netzdienliches Laden ein/aus, preisoptimiertes Laden ein/aus
├── time.py                Zeitfenster-Start/-Ende für zeitgesteuertes und
│                          netzdienliches Laden
├── repairs.py             Bestätigungsdialog für den Konflikt zwischen Netzladung
│                          und preisoptimiertem Laden
├── diagnostics.py          Diagnose-Download (Geräteseite): Coordinator-Zustand
│                          + coordinator.data + Ladeplan, IP-Adresse redigiert
├── dashboard.py            Mitgeliefertes Lovelace-Dashboard (5 Tabs), optional in
│                          der Ersteinrichtung anlegbar, siehe anforderung.yaml
│                          REQ-BUNDLED-DASHBOARD/REQ-ECONOMICS-DASHBOARD
├── services.yaml           Service-Schema für die UI
└── translations/            DE/EN-Übersetzungen (strings.json ist die Vorlage)

tests/                Siehe Abschnitt "Tests"
.devcontainer/         VS Code DevContainer für lokale Entwicklung
```

Die Abhängigkeiten zeigen von den Home-Assistant-Entrypoints nach innen:
`sensor.py`/`number.py`/`switch.py`/`time.py` verwenden den Coordinator, der
die Use-Case-Policy aus `application/` orchestriert; diese Policy verwendet
nur die reinen Regeln aus `domain/`. Die Domain importiert weder Home
Assistant noch pymodbus. Der konkrete `AsyncModbusTcpClient` wird beim Setup
erzeugt und über den `application.ports.ModbusClient`-Port in den Coordinator
injiziert. Dadurch bleibt der Coordinator der einzige Besitzer aller
Modbus-I/O-Operationen, während die Entscheidungslogik isoliert testbar ist.

Die Ladeprioritäten in `application/charge_policy.py` sind bewusst reine
Berechnung. Hysterese-Zähler, asynchrone Zustandsübergänge, periodische
Sollwert-Writes und Fehlerabbildung verbleiben im Coordinator, weil sie den
laufenden Use Case und die physische Gerätekommunikation orchestrieren. Das
erhält die extern sichtbare Funktionalität und schafft zugleich eine klare
Naht für weitere schrittweise Extraktionen.

`config_flow.py` implementiert sowohl `async_step_user` (Ersteinrichtung) als
auch `async_step_reconfigure` (spätere Änderung, z. B. der IP-Adresse) über
eine gemeinsame Methode (`_async_step_connection`). Beide validieren die
Verbindung mit demselben Testread, bevor die Daten gespeichert werden. Nur
`async_step_user` verzweigt bei Erfolg zusätzlich in drei weitere, optionale
Schritte, bevor der Eintrag angelegt wird - `async_step_reconfigure`
überspringt sie alle: `async_step_grid_charge` (Vorbelegung für das
zeitgesteuerte Laden, siehe `STEP_GRID_CHARGE_SCHEMA`), `async_step_dashboard`
(Dashboard anlegen ja/nein, siehe `STEP_DASHBOARD_SCHEMA` und
REQ-BUNDLED-DASHBOARD) und zuletzt `async_step_finish` - eine reine
Zusammenfassungsseite ohne eigene Eingabefelder (Firmware, Seriennummer,
SunSpec-Erreichbarkeit, Anzahl angelegter Entities als
`description_placeholders`, per Testread über `_async_read_finish_summary`
ermittelt), siehe anforderung.yaml REQ-SETUP-FINISH-SUMMARY. Der Config Entry
wird erst hier angelegt.

Zusätzlich gibt es einen Options Flow (`SaxPowerOptionsFlow`) für das
preisoptimierte Laden. Dort stehen nur die Dinge, die sich nicht sinnvoll als
Entity abbilden lassen (Auswahl der Quell-Sensoren und deren Interpretation);
die im Alltag veränderlichen Stellgrößen sind echte Entities am SAX-Gerät.
Eine Änderung wendet `async_update_options` direkt auf den laufenden
Coordinator an (`coordinator.options` ersetzen + `price_planner.async_setup()`
erneut aufrufen, idempotent + Plan sofort anwenden) - bewusst **kein**
Config-Entry-Reload mehr: Ein
Reload hätte über `SaxPowerCoordinator.async_shutdown`/`async_stop_sun_charge`
ein gerade aktiv gehaltenes netzdienliches Laden (Register 40051 zurück auf
SmartMeter-Nullregelung) unterbrochen und einen kurzen, ungewollten
Ladevorgang ausgelöst, bis die neu erzeugte Instanz die
`PV_SURPLUS_HYSTERESIS_CYCLES`-Bestätigung erneut durchlaufen hätte -
ursprünglich gemeldeter Bug, siehe `anforderung.yaml`,
REQ-DYNAMIC-PRICE-CHARGE.

Derselbe Options Flow konfiguriert zusätzlich das Tarifmodell der
Wirtschaftlichkeitsauswertung (REQ-ECONOMICS-TARIFFS). Die Tarifart steht als
`economics_tariff_type` auf der ersten Seite; anschließend verzweigt der Flow
in genau einen tarifspezifischen Schritt (`economics_fixed`,
`economics_time_of_use`, `economics_dynamic`) oder speichert bei
`disabled` sofort. Beim Speichern übernimmt der Flow ausschließlich die zur
gewählten Tarifart gehörenden Schlüssel und verwirft alle übrigen aus
`ECONOMICS_OPTION_KEYS` - ein alter Festpreis darf nach einem Rückwechsel
nicht unbemerkt wieder gelten. Die acht Zeitfenstergruppen sind eigene
`section`-Blöcke und liegen deshalb als verschachtelte Mappings in
`entry.options`.

Die Auswertung selbst ist dreigeteilt: `domain/tariff.py` enthält die reinen
Typen (`TariffType`, `DailyPriceWindow`, `TariffConfig`, `PriceQuote`) samt
Zeitfensterregeln und der Bewertung der nicht-dynamischen Tarife,
`application/economics.py` bildet gespeicherte Options auf diese Typen ab, und
`economics.py` ist der einzige Ort, der dafür `hass.states` liest.
`SaxTariffProvider.async_setup()` folgt demselben idempotenten Muster wie
`SaxPricePlanner.async_setup()` und wird von `async_update_options` erneut
aufgerufen. Ein fehlender oder unbrauchbarer Preis ist immer `None` plus ein
`QuoteUnavailable`-Grund - nie 0 EUR/kWh, weil ein stiller Nullpreis
Netzbezug als kostenlos bewerten und jede spätere Rechnung unbemerkt
verfälschen würde. `domain.tariff.validate_tariff()` läuft dafür vor jeder
Quote-Erzeugung und prüft für **alle** Tarifarten die Einspeisevergütung und
die tarifeigenen Pflichtpreise gegen ihren Wertebereich; der Options Flow
allein genügt nicht, weil `entry.options` auch von Hand bearbeitet sein kann.
Derselbe Wertebereich gilt für den normalisierten Preis des dynamischen
Tarifs. Eine vorhandene Preisvorschau ist verbindlich
(`price_optimizer.has_price_forecast()` trennt "keine Vorschau" von "Vorschau
vorhanden, aber unlesbar") - der Sensorzustand ersetzt sie nie. Ein über
`CONF_PRICE_ATTRIBUTE` ausdrücklich benanntes Attribut zählt dabei schon bei
jedem nicht leeren Wert als Vorschau; nur die Auto-Erkennung verlangt die
Listenform der bekannten Attributnamen. Die Zuordnung eines Zeitfensters erfolgt ausschließlich
über die lokale Wanduhrzeit; damit braucht die Sommerzeitumstellung keinen
Sonderfall.

### Wirtschaftlichkeitsbilanz (REQ-ECONOMICS-ACCOUNTING)

Läuft in `SaxPowerCoordinator._accumulate_economics`, aufgerufen am Ende von
`_accumulate_energy` mit demselben `EnergyDelta` (02/06) und demselben
rohen, ungerundeten Entladezuwachs dieses Intervalls - keine zweite Uhr,
keine zweite Riemann-Summe. Die reine Rechnung liegt in
`domain/economics_accounting.py`:

- `compute_economics_delta` bewertet ein Intervall: Netzladung kostet den
  Netzbezugspreis, PV-Ladung die Einspeisevergütung. Fehlt der jeweilige
  Preis oder ist die Herkunft unbekannt, wird nichts erfunden - die Energie
  erhöht stattdessen `unvalued_inventory_kwh` (unbewerteter Bestand) und
  einen `unpriced_charge`-Zähler. Jede Entladung verbraucht zuerst aus
  diesem Bestand (`min(discharged_kwh, unvalued_inventory_kwh)`) - dieser
  Anteil erzeugt AUSDRÜCKLICH keinen vermiedenen Geldwert (sonst entstünde
  beim Entladen von Alt-/Unbekannt-Bestand ein kostenloser Scheingewinn,
  der Kernfehler des verworfenen Issues #42). Nur der danach verbleibende,
  tatsächlich bepreist geladene Rest ("monetizable") ist den aktuellen
  Netzbezugspreis wert.
- `initial_unvalued_inventory_kwh`/`min_soc_inventory_correction` decken
  den "Ehrlichen Start" ab: Der Anfangsbestand
  (`battery_capacity * battery_soc / 100`) wird einmalig beim erstmaligen
  Aktivieren gesetzt (`SaxPowerCoordinator._bootstrap_economics_if_ready`,
  wartet auf numerisch bekannte `battery_capacity`/`battery_soc` - beide
  aus demselben SunSpec-Modus-Block wie `battery_soc_min`, bewusst nicht
  die Basic-Mode-SOC), und am geräteseitig gemeldeten SOC-Minimum
  (`data["battery_soc_min"]`) wird ein rechnerisch nie ganz auf 0
  gelaufener Rest verworfen und diagnostisch geloggt.
- `capacity_inventory_correction` deckelt den Bestand bei jedem Tick auf den
  tatsächlichen Speicherinhalt (`capacity_kwh * battery_soc / 100`, dieselbe
  Größe wie der Anfangsbestand). Ohne diesen Deckel bliebe die
  Ladeverlust-Differenz jedes *unbepreisten* Zyklus (geladen > entladen)
  dauerhaft im Bestand liegen und würde später bepreist geladene Entladung
  als unbewertet abbuchen (Issue #132). Ist Kapazität oder SOC gerade
  unbekannt, wird nicht gedeckelt. Geloggt wird höchstens einmal je
  `INVENTORY_CAP_LOG_INTERVAL_SECONDS`; die insgesamt verworfene Menge steht
  als `inventory_capped_kwh` im Diagnose-Download.

`operating_result` (vermiedene Netzkosten − Netzladekosten −
PV-Opportunitätskosten) wird nie separat gespeichert, sondern in
`_publish_economics_balance` aus den drei Teilsummen abgeleitet - so kann er
nie von ihnen abweichen.

Der einmalige Bootstrap läuft nur, solange `SaxTariffProvider.config.enabled`
wahr ist. Nach dem Bootstrap akkumuliert `_accumulate_economics` aber AUCH
während einer späteren Tarifpause unverändert weiter: `current_price`/
`feed_in_price` sind während der Pause bereits `None` (der Tarif-Adapter
liefert das für einen deaktivierten Tarif von sich aus), pausenweise
geladene Energie landet dadurch automatisch im unbewerteten Bestand statt
unbeobachtet zu bleiben - andernfalls würde eine nach dem Reaktivieren
erfolgende Entladung dieser Energie fälschlich vollständig als vermiedenen
Netzbezug monetarisieren (derselbe Scheingewinn-Fehler wie bei #42, nur
über den Umweg einer Pause statt des Anfangsbestands). Nur die
VERÖFFENTLICHTEN vier monetären Sensoren blenden während einer Pause auf
`None` (`_publish_economics_balance(..., monetary_available=...)`) statt
auf die weiter mitlaufenden internen Summen; `unvalued_inventory_kwh`/
`unpriced_charge_kwh`/`unpriced_discharge_kwh` sind keine Geldwerte und
bleiben sichtbar. `economics_current_import_price`/
`economics_feed_in_price` sind reine Durchreichungen des aktuellen Tarifs
und unabhängig vom Bilanz-Bootstrap immer aktuell -
`SaxTariffProvider.feed_in_price_eur_kwh` validiert dafür selbst den
Wertebereich (`is_valid_feed_in_price`), weil `validate_tariff()` nur die
Quote-Erzeugung schützt, nicht diese separat gelesene Property.

Persistenz: `infrastructure/economics_store.py` (`EconomicsStateStore`,
eigener STORAGE_VERSION, eigenes Bootstrap-Fenster analog zu
`EnergyStateStore`). Anders als die monoton steigenden Energiezähler dürfen
die drei Geldsummen wegen negativer Strompreise sinken - "kleiner als der
alte Wert" ist dort deshalb bewusst KEIN Ablehnungsgrund, nur
NaN/Inf/Fremdtypen sind es. `unpriced_charge_kwh`/`unpriced_discharge_kwh`
bleiben dagegen echte monotone Summen, `unvalued_inventory_kwh` ist ein
Bestand (Gauge) ohne Monotonieprüfung. `economics_started_at` ist wie
`origin_accounting_started_at` (02/06) einmalig gesetzt und danach
unveränderlich; ein unvollständiges Sieben-Felder-Bündel wird beim Laden
komplett neu gebootstrapped, und die interne Monotonie-Baseline wird in
diesem Fall ebenfalls komplett bereinigt (siehe
`EnergyStateStore._origin_baseline` für dasselbe, aus einem Review-Befund
gelernte Muster). `notify_tariff_revision()` (aufgerufen aus
`__init__.async_update_options`) merkt sich nur einen rein diagnostischen
Zeitpunkt der letzten Options-Änderung - eine Tarifänderung wirkt ohnehin
ausschließlich prospektiv, weil jedes künftige Delta einfach den dann
aktuellen Preis verwendet; nichts wird rückwirkend neu berechnet.

Scheitert `EconomicsStateStore.async_load()` selbst (I/O-Fehler, unbekannte
künftige Storage-Hauptversion), setzt `async_load_economics_state`
`_economics_store_write_blocked` - Rechnung und Bootstrap laufen normal im
Arbeitsspeicher weiter (analog zu `ControlConfigLoadStatus.FAILED`), aber
`_async_schedule_economics_save`/`_async_flush_economics_state` verweigern
jeden Schreibversuch, bis ein Neuladen des Config Entry eine frische
Coordinator-Instanz erzeugt. Ohne diese Sperre würde eine aus lauter Nullen
neu gebootstrappte Bilanz den eigentlich vorhandenen, nur unlesbaren Store
überschreiben und dessen Inhalt endgültig verlieren.

### ROI und Amortisationsprognose (REQ-ECONOMICS-AMORTIZATION)

Baut ausschließlich auf dem bereits bilanzierten `operating_result` oben
auf. Die reine Rechnung liegt in `domain/economics_amortization.py`, ohne
jeden Home-Assistant-Bezug:

- `compute_roi_percent`/`compute_amortization_progress_percent`/
  `compute_remaining_to_payback_eur` sind einzeilige, unabhängig
  testbare Formeln - `roi_percent` bleibt bewusst unklemmt (negativ oder
  über 100 %), nur der Fortschritt ist auf 0..100 begrenzt.
- `DayEconomicsResult` ist ein abgeschlossener Kalendertag (operatives
  Ergebnis plus vier Energiemengen); `price_coverage_percent` bildet daraus
  die Preisabdeckung, ohne einen Betrag durch einen möglicherweise
  negativen oder 0 Preis zurückzurechnen. `observed_seconds`/
  `day_length_seconds` tragen eine davon unabhängige zweite
  Qualitätsdimension: `time_coverage_percent` misst, wie viel des Tages
  überhaupt beobachtet wurde. Beide Felder sind absichernd vorbelegt (0
  beobachtete Sekunden) - ein Aufrufer, der sie vergisst, erzeugt einen als
  unvollständig geltenden Tag, nie einen fälschlich vollwertigen.
- `compute_amortization_forecast` ist eine reine 30-Tage-Prognose. Das
  Fenster ist exakt der lückenlose Kalenderbereich von `today_local - 30`
  bis `today_local - 1` (`FORECAST_WINDOW_DAYS`) - fehlt auch nur einer
  dieser 30 konkreten Tage in der Historie (z. B. nach einer längeren
  HA-Ausfallzeit), ist das `INSUFFICIENT_HISTORY`, statt stattdessen
  ältere, außerhalb des Fensters liegende Tage als Lückenfüller zu
  verwenden (30 vorhandene, aber lückenhafte Buckets sind KEIN gültiges
  Fenster). Verwirft die GESAMTE Prognose (nicht nur einzelne Tage),
  sobald auch nur ein Tag `DAY_COVERAGE_THRESHOLD_PERCENT` (95 %)
  unterschreitet; `average_price_coverage_percent` bleibt dabei als
  Diagnosewert gesetzt. Dieselbe harte Regel gilt für die Zeitabdeckung
  (`DAY_TIME_COVERAGE_THRESHOLD_PERCENT`, 95 %): ein nur teilweise
  beobachteter Tag - HA war aus, Update, Stromausfall - besteht die
  Preisprüfung typischerweise mühelos, enthält aber nur einen Teil seines
  Ergebnisses und macht Durchschnitt, Hochrechnung und Rückzahlungsdatum
  systematisch zu pessimistisch (Issue #131), deshalb `INCOMPLETE_DAYS` für
  das GESAMTE Fenster. Diese Prüfung läuft vor der Preisabdeckung, weil die
  Preisabdeckung eines halb beobachteten Tages nur den beobachteten
  Ausschnitt misst - `unavailable_reason` benennt so die Ursache, nicht die
  Folge. Das Rückzahlungsdatum entfällt nicht nur bei einem
  nicht positiven Durchschnitt, sondern auch jenseits von
  `MAX_FORECAST_PAYBACK_DAYS` (~100 Jahre): ein winziger, aber positiver
  Durchschnitt ergäbe sonst ein von `date`/`timedelta` nicht mehr
  darstellbares Datum, und dieser `OverflowError` würde über
  `_async_update_data` sämtliche Entities unavailable machen - `payback_days`
  bleibt als Diagnosewert erhalten und wird vom Coordinator als Attribut
  von `economics_average_daily_result_30d` veröffentlicht, weil
  `unavailable_reason` in diesem Fall `None` bleibt (Durchschnitt und
  Hochrechnung sind gültig) und der Horizontfall sonst unsichtbar wäre.

Tageswechsel-Erkennung ohne eigenen Timer, in
`SaxPowerCoordinator._advance_economics_day` (aufgerufen aus
`_accumulate_economics`, bei jedem Poll-Tick, VOR der Anwendung des
aktuellen Deltas auf die Gesamt-/Tagessummen - siehe unten): vergleicht
`dt_util.now().date()` (Home-Assistant-Zeitzone) mit dem zuletzt gesehenen
Tag. Die beobachtete Zeit des laufenden Tages wächst dabei aus derselben
Riemann-Summe wie die Energie (`_accumulate_energy` reicht die Dauer des
gerade verbuchten Intervalls durch, keine zweite Uhr): Genau die
Intervalle, die nicht verbucht werden - der erste Tick nach einem Neustart,
jede Phase ohne Leistungswert, die Zeit nach einem fehlgeschlagenen Update
(`_async_update_data` verwirft dafür `_energy_last_ts`) - zählen auch nicht
als beobachtet. Gespeichert wird sie nur beim Überschreiten des nächsten
Rasterschritts (`OBSERVED_TIME_SAVE_GRANULARITY_SECONDS`, 15 min), weil sie
sich sonst als einziger Wert bei jedem Tick bewegte und den Store auch auf
einem ruhenden System dauerhaft alle `ECONOMICS_SAVE_DELAY` Sekunden
schreiben ließe. Beim
Abschluss schreibt `_close_economics_day` die tatsächliche Tageslänge fest
(`dt_util.start_of_local_day`, Differenz bewusst über UTC gerechnet: bei
zwei `datetime`-Objekten mit demselben `tzinfo` ignoriert Python den
Offset und käme für jeden DST-Tag auf exakt 24 h).
Ein 23h/25h-DST-Tag wird nicht auf 24h normiert - reiner
Kalenderdatumsvergleich, keine verstrichene Zeit. Bei einem Wechsel
schließt `_close_economics_day` den bisherigen Tag ab (angehängt an
`day_results`, gekappt auf `MAX_STORED_DAYS`) und ruft
`_maybe_mark_payback_achieved` auf; `_start_economics_day` beginnt den
neuen Tag bei 0. Idempotent gegenüber Neustart (`current_day` plus seine
vier Zähler sind als eigenes Fünfer-Bündel persistiert) und doppelter
Tick-Verarbeitung (nur ein tatsächlicher Datumswechsel schließt ab).

Die Reihenfolge in `_accumulate_economics` ist bewusst: erst
`_advance_economics_day()` (Tagesabschluss inkl. Payback-Check), DANACH
erst die Anwendung des aktuellen Deltas auf Gesamt- und Tagessummen. Würde
stattdessen zuerst das Delta angewendet, sähe ein beim selben Tick
abgeschlossener Vortag bereits das erste Delta des NEUEN Tages - ein
Payback, der erst durch dieses neue Delta erreicht wird, würde dadurch
fälschlich auf die vorherige Tagesgrenze zurückdatiert. Der `changed`-Flag,
der das verzögerte Speichern auslöst, berücksichtigt neben den sechs
ursprünglichen Delta-Feldern auch `priced_charge_kwh_delta`/
`priced_discharge_kwh_delta` - eine Bewegung zu einem gültigen Preis von
exakt 0 EUR/kWh bewegt nur diese beiden, keine der drei Geldsummen.

`_maybe_mark_payback_achieved` setzt `payback_achieved_at` (UTC) genau
einmal, sobald das kumulierte operative Ergebnis die konfigurierten
Investitionskosten an einer Tagesgrenze erstmals erreicht, und danach nie
wieder - unabhängig von einer späteren Änderung der Investitionskosten.
`_estimated_payback_date` liefert dieses fixe Datum, sobald gesetzt, statt
der laufenden Projektion aus `compute_amortization_forecast`; für den
`device_class: date`-Sensor wird der intern UTC-genaue Zeitpunkt dafür auf
den lokalen Kalendertag abgebildet (`dt_util.as_local(...).date()`).

`_publish_amortization` leitet ROI/Fortschritt/Restbetrag/Tagesergebnis aus
demselben `operating_result` wie `_publish_economics_balance` ab und
blendet sie bei deaktiviertem Tarif ebenso aus - anders als die
30-Tage-Prognose selbst, die ausschließlich auf bereits abgeschlossenen
Tagen und den Investitionskosten beruht, deshalb den tatsächlichen,
UNMASKIERTEN Restbetrag braucht (nicht den während einer Pause
ausgeblendeten) und während einer Tarifpause sichtbar bleibt. Fehlen
gültige Investitionskosten, liefert die Methode dagegen für ALLE SIEBEN
Sensoren `None` (früher Rückgabepfad) - auch für `economics_result_today`
und einen bereits intern erreichten, weiterhin persistierten
`payback_achieved_at`, der erst wieder veröffentlicht wird, sobald erneut
Investitionskosten hinterlegt sind.

Persistenz: `EconomicsStateStore` um `STORAGE_MINOR_VERSION` 2 erweitert
(statt einer Hauptversion, aus demselben Grund wie beim
`STORAGE_VERSION`-Kommentar in `energy_store.py`). Drei unabhängige Bündel:
das ursprüngliche Sieben-Felder-Bündel oben (unverändert), `day_results`
(jeder Tag einzeln validiert, `_validated_day_result`) sowie `current_day`
plus seine vier Zähler als eigenes Fünfer-Bündel (`_validated_current_day`)
- fehlt/ist auch nur eines ungültig, gilt der ganze angefangene Tag als
nicht aussagekräftig, ohne die abgeschlossene Historie zu berühren.
`payback_achieved_at` ist wie `economics_started_at` einmalig gesetzt und
danach unveränderlich.

### Datenqualität, Diagnose und Bilanzneustart (REQ-ECONOMICS-OBSERVABILITY)

Macht sichtbar, ob und warum die Bilanz gerade vertrauenswürdig ist, ohne
selbst neue Geldwerte zu berechnen. Die reine Ableitung liegt in
`domain/economics_status.py`:

- `EconomicsStatus` (sieben Werte) und `compute_economics_status(...)`
  bilden eine feste Prioritätsreihenfolge aus mehreren, ggf. gleichzeitig
  zutreffenden Booleans ab: `disabled` > `storage_error` >
  `waiting_for_initial_state` > `price_unavailable` >
  `origin_unavailable` > `partial_price_coverage` > `active`. `disabled`
  gilt ausschließlich bei deaktiviertem Tarif und schlägt dabei jeden
  anderen Zustand.
- `compute_price_coverage_percent(priced_kwh, unpriced_kwh)` ist
  energiebasiert (nicht tickbasiert) und liefert bei Nenner 0 100 % -
  dieselbe Formel wie `DayEconomicsResult.price_coverage_percent` (04/06)
  und `_energy_origin_coverage()` (02/06).

`SaxPowerCoordinator._publish_economics_status` (aufgerufen am Ende von
`_accumulate_economics`, unabhängig vom `frozen`-Zweig, damit auch
`waiting_for_initial_state`/`storage_error` sichtbar werden, bevor die
Bilanz je gestartet ist) setzt das zusammen:

- Zwei neue Lifetime-Zähler `_economics_priced_charge_kwh`/
  `_economics_priced_discharge_kwh` (Gegenstück zu den bestehenden
  `unpriced_*`-Zählern, aus denselben `EconomicsDelta.priced_charge_kwh_delta`/
  `priced_discharge_kwh_delta` wie die Tages-Buckets) ergeben
  `charge_price_coverage_percent`/`discharge_price_coverage_percent`.
  `origin_unavailable` ist wahr, wenn `_energy_origin_coverage()` (02/06)
  `None` liefert.
- `_update_economics_price_availability` verfolgt monotonic, seit wann
  ununterbrochen kein gültiger Preis mehr vorlag.
  `QuoteUnavailable.TARIFF_INCOMPLETE` (ungültig gespeicherter Fest-/
  Zeitfenstertarif) ist ein sofortiger Konfigurationsfehler ohne
  Karenzzeit; jeder andere Grund braucht
  `ECONOMICS_PRICE_UNAVAILABLE_GRACE_PERIOD` (6h, wie beim
  preisoptimierten Laden). Das Ergebnis (`_economics_price_unavailable`)
  ist die alleinige Quelle sowohl für den Status-Sensor als auch für das
  Repair-Issue `economics_price_unavailable`
  (`SelfDiagnostics._check_economics_price_unavailable`, keine doppelte
  Karenzzeit-Logik). Die Löschung prüft dabei zusätzlich zum lokalen
  In-Memory-Flag den tatsächlichen Issue-Registry-Zustand
  (`ir.async_get_issue`): Das Flag lebt nur im Arbeitsspeicher der
  jeweiligen `SelfDiagnostics`-Instanz und startet nach jedem Neuladen
  des Config Entry wieder bei `False`, während ein zuvor angelegtes
  Issue in der Registry weiterbestehen kann - ohne die zusätzliche
  Registry-Prüfung bliebe ein solches Issue nach einem Reload dauerhaft
  bestehen, selbst wenn der Preis inzwischen wieder gültig ist.
- Ein Speicherfehler (`_economics_store_write_blocked`) ergibt
  `storage_error` UND verhindert - Abweichung von REQ-ECONOMICS-
  ACCOUNTING - sowohl einen frischen 0-Bootstrap im Arbeitsspeicher
  (`_bootstrap_economics_if_ready`) als auch jede weitere Akkumulation
  (`_accumulate_economics` wickelt den gesamten Mutationsblock in
  `if not frozen:`). Die Energiezähler/Herkunftsaufteilung aus 02/06
  laufen davon unberührt weiter.

Kontrollierter Bilanzneustart
(`SaxPowerCoordinator.async_restart_economics_accounting`, Service
`sax_power.restart_economics_accounting`, `confirm` muss exakt `true`
sein): setzt ausschließlich die drei Geldsummen, die vier
Preisabdeckungszähler, die Tages-Buckets und den Aktivierungs-/
Payback-Zeitpunkt zurück, initialisiert den Anfangsbestand erneut wie bei
der erstmaligen Aktivierung - rührt niemals `energy_charged`/
`energy_discharged` oder die Herkunftszähler an. Speichert atomar über
`EconomicsStateStore.async_reset` VOR jeder In-Memory-Änderung: dessen
`_valid_snapshot` prüft weiterhin Endlichkeit/Wertebereich, überspringt
aber bewusst die Monotonie-/Unveränderlichkeits-Baseline aus `_accept` -
ein gewollter Reset auf 0 ist kein Korruptionsindiz. Schlägt das
Speichern fehl, bleibt der bisherige Zustand vollständig unverändert
(kein halb angewendeter Neustart). Zeitpunkt (UTC) und optionaler
freier Grund dieses Neustarts werden zusätzlich als
`last_restart_at`/`last_restart_reason` persistiert und erscheinen im
Diagnose-Download - rein informativ, ohne Rückwirkung auf die
Berechnung.

Persistenz: `EconomicsStateStore` um `STORAGE_MINOR_VERSION` 3 erweitert.
`priced_charge_kwh`/`priced_discharge_kwh` sind wie die bestehenden
`unpriced_*`-Zähler echte monotone Summen und unabhängig vom
Sieben-Felder-Bündel - ein älterer Store beginnt ihre Zählung transparent
bei 0 ab jetzt. `STORAGE_MINOR_VERSION` 4 ergänzt zusätzlich
`last_restart_at`/`last_restart_reason` (Zeitpunkt und optionaler
Freitext-Grund des zuletzt ausgeführten `restart_economics_accounting`) -
rein diagnostisch, ohne Einfluss auf eine Berechnung, siehe unten.
`STORAGE_MINOR_VERSION` 5 trägt die Zeitabdeckung: `observed_seconds`/
`day_length_seconds` je abgeschlossenem Tag sowie
`current_day_observed_seconds` im Bündel des laufenden Tages. Ein
FEHLENDES Feld eines abgeschlossenen Tages stammt aus einem älteren Store
und macht den Tag nur unvollständig (er bleibt als Historie erhalten); ein
vorhandener, aber ungültiger Wert bleibt ein Korruptionsindiz und verwirft
den Tageseintrag. Beim laufenden Tag gilt diese Nachsicht bewusst nicht -
ohne bekannte Beobachtungsdauer ließe er sich nur mit einer erfundenen
Abdeckung abschließen, und verloren geht dabei nur der ohnehin
unvollständige laufende Tag.

Ein von `EconomicsStateStore._accept`/`_valid_snapshot` abgelehnter oder ein
technisch fehlgeschlagener Schreibversuch (verzögert wie beim finalen
Speichern beim Entladen) setzt `SaxPowerCoordinator.
_economics_store_write_blocked` - die Bilanz friert daraufhin ein (Status
`storage_error`) statt unbemerkt weiter zu akkumulieren, bis der Config
Entry neu geladen wird.

Home Assistants `Store` fängt eine echte `WriteError`/`SerializationError`
beim Schreiben intern ab und kehrt regulär zurück
(`Store._async_handle_write_data`), ohne sie an den Aufrufer
weiterzureichen - weder `Store.async_save()` noch der über
`Store.async_delay_save()` verzögerte Pfad melden einen solchen Fehler
zurück, ein synchron abgelehnter Snapshot allein deckt diesen Fall also
nicht ab. `EconomicsStateStore` verzichtet deshalb bewusst auf
`Store.async_delay_save()` und verwaltet die Verzögerung selbst
(`async_call_later`, mit einem `EVENT_HOMEASSISTANT_FINAL_WRITE`-
Sicherheitsnetz analog zu `Store._async_ensure_final_write_listener`, damit
weder ein letzter Schreibvorgang bei einem Home-Assistant-Shutdown verloren
geht noch ein über das Programmende hinaus offener Timer bestehen bleibt):
`_write_and_verify` liest nach jedem Schreibversuch den soeben
geschriebenen Schlüssel über die öffentliche `Store.async_load()`-API
zurück und vergleicht ihn mit den beabsichtigten Daten - eine schweigend
verschluckte `WriteError` lässt die Datei unverändert und wird dadurch als
Abweichung sichtbar. Beim sofortigen Pfad (`async_save`/`async_reset`)
fließt das Ergebnis direkt in den Rückgabewert ein (ein so erkannter
stiller Fehlschlag lässt `restart_economics_accounting` deshalb korrekt
mit `HomeAssistantError` fehlschlagen, statt fälschlich Erfolg zu melden
und den bisherigen Zustand unverändert zu lassen); beim zeitversetzten
Pfad, der keinen wartenden Aufrufer mehr hat, über den optionalen
`on_persist_failed`-Callback
(`SaxPowerCoordinator._on_economics_persist_failed`).

### Dashboard-Tab "Wirtschaftlichkeit" (REQ-ECONOMICS-DASHBOARD)

Fünfter View in `dashboard.async_build_dashboard_config`, direkt nach
"Dynamisches Laden" - baut ausschließlich auf bereits bestehenden Entities
und Bausteinen der ganzen Wirtschaftlichkeits-Reihe auf, führt selbst
keine neue Berechnung ein:

- `_resolved_row` faktorisiert die bisher in `_entities_card` inline
  liegende Entity-Auflösung + Namensermittlung, damit sie auch außerhalb
  einer vollständigen `_entities_card` wiederverwendbar ist (Karte "Status
  und Preise" mischt normale Entity-Zeilen mit Attribut-Zeilen).
- `_attribute_row` baut eine `type: attribute`-Kartenzeile - zeigt ein
  Attribut einer Entity (hier: `charge_price_coverage_percent`/
  `discharge_price_coverage_percent`/`economics_started_at` von
  `economics_status`, siehe REQ-ECONOMICS-OBSERVABILITY) wie einen
  eigenen Sensor, ohne dass dafür ein eigener Sensor existieren müsste.
- `_statistics_graph_card` baut eine Core-`statistics-graph`-Karte
  (Balkendiagramm, `stat_types: ["change"]`, `period: "day"`,
  `days_to_show: 30`) für die vier Geldsensoren - keine Custom-Card,
  keine private Statistik-API.
- `_stack_card` bündelt mehrere Karten zu einer Core-`vertical-stack`, wenn
  eine fachlich zusammengehörige Gruppe als EINE Karte im View erscheinen
  muss, obwohl eine `entities`-Karte selbst keine Gauge/Markdown einbetten
  kann. Zwei Verwendungen:
  - Karte "Herkunft der Ladeenergie": die entities-Karte plus eine
    `markdown`-Karte mit dem Hinweis, dass die Herkunftsaufteilung eine
    konservative Schätzung am Netzanschlusspunkt ist, keine physikalische
    Einzelstromverfolgung (REQ-ENERGY-ORIGIN). Fehlt, wenn keine der
    Herkunfts-Entities registriert ist.
  - Karte "Investition und Amortisation": eine entities-Zeile mit
    `economics_roi`, dann die `economics_amortization_progress`-Gauge,
    dann eine zweite entities-Karte mit den übrigen vier ROI-/
    Amortisationssensoren, in genau dieser Reihenfolge.
- Die sieben ROI-/Amortisationssensoren sind anders als z. B. die
  netzdienlichen Entities IMMER registriert (statische
  `SENSOR_DESCRIPTIONS`), unabhängig davon, ob Investitionskosten
  konfiguriert sind; `economics_roi` liefert in diesem Fall `None`
  (Sensorzustand "unknown"). Die ganze vertical-stack "Investition und
  Amortisation" ist deshalb in eine Core-`type: conditional`-Karte
  eingebettet (`conditions: [{entity: <economics_roi-Entity-ID>,
  state_not: "unknown"}]`) statt build-time über die Config-Entry-Options
  ausgelassen zu werden: `async_build_dashboard_config` braucht dafür
  keine Options mehr, nur `hass`/`entry_id`. Eine Options-Prüfung beim
  Dashboardbau wäre nach einer späteren Options-Änderung veraltet, da
  `__init__.async_update_options` das gespeicherte Dashboard nie neu baut
  (nur den Coordinator aktualisiert, siehe unten) - die "conditional"-
  Karte blendet sich dagegen automatisch ein/aus, sobald der Coordinator
  nach einer Options-Änderung neu rechnet und der Sensorzustand wechselt,
  ganz ohne Dashboard-Neubau.

Alles andere folgt exakt dem bestehenden Muster der vier älteren Tabs:
`_entities_card`/`_gauge_card` lassen fehlende Entities/Karten still aus,
`async_create_dashboard` bleibt idempotent, `force=True`
(`sax_power.reinstall_dashboard`) überschreibt inklusive des neuen Tabs,
ein Fehler beim Dashboardbau blockiert nie das Setup.

## Datenfluss

`config_flow.py` sammelt Host/Port/Slave-IDs/Intervall und validiert die
Verbindung mit einem Testlesen. `__init__.py` baut daraus einen
`AsyncModbusTcpClient` und einen `SaxPowerCoordinator` (`coordinator.py`),
lädt anschließend die Plattformen `sensor`, `number`, `switch` und `time`
und registriert die beiden Services. Jede Entität (`entity.py` als
Basisklasse) liest ihren Zustand ausschließlich aus `coordinator.data` und
schreibt Änderungen über `coordinator.async_write_register(...)` bzw.
`coordinator.async_write_extended_register(...)` (SunSpec-Modus, Slave-ID
`self.slave_id_extended`).

**Max-SOC-Sperre, zeitgesteuertes Laden, netzdienliches Laden &
preisoptimiertes Laden:** Kein natives Max-SOC-Register. Alle vier teilen
sich eine zentrale Auswertung (`SaxPowerCoordinator._async_enforce_grid_
charge`, bei jedem Poll-Zyklus sowie bei jeder Einstellungsänderung neu
ausgewertet) und denselben Hintergrund-Task (`SaxPowerCoordinator._async_
sun_charge_loop`), der über den SunSpec-Modus schreibt: erst Register 40051
(Steuermodus) auf Sollwertvorgabe, dann Register 40049 (Leistungsvorgabe %).
Vor dieser Auswertung ermittelt `application/calibration.py` aus dem realen
SOC und dem persistenten letzten Vollladezeitpunkt den effektiven Ziel-SOC.
Bei einem Benutzerwert unter 100 % ist dieser nach sieben Tagen bis zur
nächsten real gemessenen Volladung 100 %. `infrastructure/calibration_store.py`
speichert Zeitstempel und Voll-SOC-Flanke pro Config Entry; `__init__.py` lädt
sie vor dem ersten Refresh. Die Number-Entity behält stets den konfigurierten
Wert, während Coordinator und Preisplaner den effektiven Wert verwenden.
Reihenfolge/Priorität in `_async_enforce_grid_charge`:

1. **SOC ≥ "Max. SOC"** (`soc_reached`): Leistungsvorgabe wird auf 0 %
   gehalten - unabhängig davon, ob zeitgesteuertes oder netzdienliches Laden
   aktiviert ist (z. B. auch bei einem durch PV-Überschuss vollen Speicher).
   Verhindert dauerhaftes Volladen auf 100 % (Batterie-Lebensdauer); der
   Speicher entlädt sich währenddessen nicht automatisch zur
   Eigenverbrauchsdeckung.
2. **Sonst, falls zeitgesteuertes Laden aktiviert + im Zeitfenster + im
   aktiven Monat + kein PV-Überschuss** (`timed_should_charge`):
   Leistungsvorgabe = `MIN_SETPOINT_POWER` (sättigt in
   `_watts_to_ic_setpoint_raw` auf -100 %, maximal mögliche Ladeleistung -
   eine frühere, konfigurierbare "Max. Netzladeleistung" wurde entfernt,
   weil der eingestellte Watt-Wert in der Praxis keinen Einfluss auf die
   tatsächliche Ladeleistung hatte).
3. **Sonst, falls netzdienliches Laden aktiviert + im eigenen Zeitfenster +
   im eigenen aktiven Monat + optionale Mindest-PV-Prognose erfüllt + nicht
   bereits durch zeitgesteuertes Laden
   beansprucht** (`grid_serving_eligible`): eigene Zustandsmaschine
   (`SaxPowerCoordinator._async_step_grid_serving`), NICHT über einen aus
   dem PV-Überschuss berechneten Sollwert - es wird nie ein Sollwert > 0
   geschrieben:
   - **Schritt a** (ohne aktiven Sollwertvorgabemodus): Erreicht die
     tatsächliche Ladeleistung des SAX (negativer Anteil von
     `data["storage_power_active"]`) `SMARTMETER_PV_SURPLUS_THRESHOLD_WATT`
     (Beweis, dass die geräteeigene SmartMeter-Nullregelung bereits mit
     Überschuss lädt), wechselt der Speicher in einem Aufruf in den
     Sollwertvorgabemodus UND die Ladung wird auf 0 % gestoppt
     (`async_start_sun_charge(0)`), danach zwei Wartezyklen
     (`_grid_serving_wait_cycles`).
   - **Schritt b** (mit aktivem Sollwertvorgabemodus, nach Ablauf der
     Wartezyklen): Fällt die am Smart Meter gemessene Netzeinspeisung
     (`data["smartmeter_power"]`) unter denselben Schwellwert, wird der
     Speicher aktiv zurück in die SmartMeter-Nullregelung gesetzt
     (`async_stop_sun_charge`). Bleibt sie mindestens beim Schwellwert (oder
     fehlt der Messwert), bleibt die Ladung bewusst bei 0 % gehalten - und
     zwar selbstheilend: sowohl im Wartezyklen- als auch im Halte-Zweig ruft
     die Methode zusätzlich `async_start_sun_charge(0)` erneut auf (No-Op bei
     unverändertem, weiterhin laufendem Task), damit ein unerwartet
     gestorbener Schreib-Task (z. B. nach einem einzelnen transienten
     Modbus-Fehler) noch im selben Zyklus neu gestartet wird - siehe
     `anforderung.yaml`, REQ-GRID-SERVING-CHARGE, für den ursprünglich
     gemeldeten Bug ohne diese Selbstheilung.

   Schließt sich mit Schritt 2 bereits strukturell über
   `not timed_should_charge` aus.
4. **Sonst, falls preisoptimiertes Laden aktiviert + Ladeplan meldet
   ausgewähltes Preisfenster** (`price_should_charge`, siehe
   `price_optimizer.py`): Leistungsvorgabe = `MIN_SETPOINT_POWER`, gleicher
   Schreibpfad wie Schritt 2. `price_should_charge` schließt zusätzlich
   das effektive `grid_serving_window_active` aus (inklusive der optionalen
   Prognosefreigabe) - **netzdienliches Laden hat also
   Vorrang vor preisoptimiertem Laden, nicht umgekehrt** (Regression, die
   behoben wurde: vorher blockierte preisoptimiertes Laden stattdessen
   netzdienliches Laden, was dazu führte, dass sich beide Automatiken
   gegenseitig ein- und ausschalten konnten, sobald ihre Bedingungen
   gleichzeitig erfüllt waren). Dieselbe Ausschlussregel gilt für die
   Neutralpreis-Pausezone (`price_should_pause`, Sollwert 0 statt
   Nullregelung zwischen Preisgrenze und Neutralpreis).
5. **Sonst**: Task wird gestoppt, Register 40051 zurück auf 0
   (SmartMeter-Nullregelung), Zustandsmaschine zurückgesetzt.

**Aktive Monate:** Beide Features haben zusätzlich je 12 Monats-Schalter
(`switch.SaxPowerMonthSwitch`, eine generische Klasse für beide Features und
alle 12 Monate, parametrisiert über `is_month_active`/`async_set_month_active`
-Callables), die in `SaxPowerCoordinator._timed_charge_months`/
`_grid_serving_months` (je ein `set[int]`, Default alle 12 Monate) verwaltet
werden. `_async_enforce_grid_charge` prüft zusätzlich `now.month in
self._timed_charge_months` bzw. `self._grid_serving_months`.

**Zeitfenster-Überlappung (Tageszeit UND Monat):**
`SaxPowerCoordinator._assert_windows_dont_overlap` (aufgerufen aus den vier
Zeit-Settern `async_set_timed_charge_start/-end`/`async_set_grid_serving_
start/-end` sowie den beiden Monats-Settern `async_set_timed_charge_month`/
`async_set_grid_serving_month`) lehnt eine Änderung, die zu einer
Überschneidung der beiden Zeitfenster führen würde, mit
`HomeAssistantError` ab - aber NUR, wenn sich sowohl die Tageszeiten
(`coordinator.windows_overlap`, modulweite Funktion, zerlegt beide Fenster
in Sekunden-Intervalle seit Mitternacht via `_window_intervals`, unterstützt
über Mitternacht laufende Fenster analog zu `_is_time_in_window`) ALS AUCH
die aktiven Monate (einfache Set-Schnittmenge) überschneiden. Die beiden
Monats-Setter akzeptieren zusätzlich `validate: bool = True` -
`SaxPowerMonthSwitch.async_added_to_hass` ruft sie beim Restaurieren mit
`validate=False` auf (vermeidet False-Positives durch sequentielles
Restaurieren mehrerer Monats-Entities, die beide bei "alle Monate"
starten), Live-Änderungen über den Schalter validieren immer.

Beide Register werden periodisch neu geschrieben (Intervall aus dem
geräteseitig gemeldeten Timeout, Register 40050, abgeleitet via
`_sun_ic_write_interval`, gedeckelt auf 30s), da das Gerät den Sollwert
sonst verwirft. Beim Stoppen wird Register 40051 aktiv auf 0 zurückgesetzt
statt nur passiv auf den Timeout zu warten (siehe
`SaxPowerCoordinator.async_stop_sun_charge`) - dabei werden sowohl
`asyncio.CancelledError` als auch `HomeAssistantError` beim Awaiten des
abgebrochenen Tasks abgefangen, da pymodbus eine Cancellation, die einen
laufenden Write trifft, als `ModbusIOException` (und damit als
`HomeAssistantError`) statt als reine `CancelledError` durchreicht.

Der ältere Basic-Mode-P-Sollwert-Pfad (Register 41,
`_async_grid_charge_loop`, alle 30s fest) bleibt ausschließlich für den
manuellen `start_grid_charge`/`stop_grid_charge`-Service in Verwendung; die
Integration liest/schreibt die Basic-Mode-Register 43/44 (Ent-/Ladeleistungs-
grenzwert) nicht mehr - eine frühere Software-Einstellung "Max.
Netzladeleistung" (`SaxPowerChargeLimitNumber`), die Register 44 einmalig
als Vorgabewert gelesen hat, wurde entfernt (siehe unten).

**"Max. SOC"** (`SaxPowerMaxSocNumber`) kommt beim Start aus dem
Konfigurations-Store (siehe
[Startreihenfolge und Persistenz der Ladeeinstellungen](#startreihenfolge-und-persistenz-der-ladeeinstellungen))
und setzt sich nur bei fehlendem Store UND fehlendem Vorzustand (z. B.
direkt nach der Ersteinrichtung) explizit auf `MAX_SOC` (100) statt
"unbekannt"/0 zu bleiben.

**Vorbelegung von Zeitfenster/Aktiviert-Status:** `SaxPowerTimedChargeSwitch`
sowie `SaxPowerTimedChargeStartTime`/`SaxPowerTimedChargeEndTime` (jeweils
`RestoreEntity`) fragen beim Start in dieser Reihenfolge: (0) stammt der
Wert bereits aus dem Konfigurations-Store? Dann ist er maßgeblich und die
folgenden Stufen entfallen (siehe
[Startreihenfolge und Persistenz der Ladeeinstellungen](#startreihenfolge-und-persistenz-der-ladeeinstellungen)).
(1) hat der Coordinator bereits einen Wert (z. B. durch eine andere Entity
in dieser Session)? (2) gibt es einen über RestoreEntity gespeicherten
Vorzustand aus einem früheren Lauf? (3) steht ein Wert aus dem zweiten
Ersteinrichtungs-Schritt im Config Entry (`entity.initial_config_value`)? (4)
sonst der Hard-Default aus `const.py`. Stufe 3 kommt dadurch effektiv nur
beim allerersten Start eines neuen Eintrags zum Tragen - sobald einmal ein
echter Zustand über RestoreEntity gespeichert wurde, hat der stets Vorrang,
auch nach einem späteren `Reconfigure` (der die Netzladung-Schlüssel nicht
im Config Entry aktualisiert).

## Startreihenfolge und Persistenz der Ladeeinstellungen

Siehe `anforderung.yaml`, REQ-CONTROL-CONFIG-BOOTSTRAP.

Alle softwareseitigen Steuerwerte (Max. SOC, beide Zeitfenster mit ihren
Monats-Sets, Min. SOC, PV-Prognose-Mindestwert, die drei Automatik-Schalter,
Ladestrategie und Preisparameter) liegen als ein Snapshot in einem
versionierten Store: `infrastructure/control_store.py`
(`ControlConfig`/`ControlConfigStore`, Schlüssel
`sax_power.control.<entry_id>`). Mehrere Config Entries haben dadurch
getrennte Stores.

`__init__.async_setup_entry` hält eine verbindliche Reihenfolge ein:

1. `async_load_calibration_state()` / `async_load_energy_state()` /
   `async_load_control_state()` - alle drei Stores werden geladen, bevor
   irgendetwas das Gerät steuert. `async_load_control_state()` öffnet
   zusätzlich das **Bootstrap-Fenster**.
2. `async_config_entry_first_refresh()` - liest die Register ganz normal,
   überspringt aber `_async_enforce_grid_charge`. Reads sind im
   Bootstrap-Fenster erlaubt, steuernde Writes nicht.
3. `async_forward_entry_setups(...)` - die Plattformen legen ihre Entities
   an. Deren Setter laufen ebenfalls ins gesperrte
   `_async_apply_grid_charge_change` und wenden daher keine
   Teilkonfiguration an.
4. `price_planner.async_setup()`, danach `async_finish_bootstrap()` -
   schließt das Fenster, schreibt den vollständigen Snapshot fest und wendet
   unter dem vorhandenen Control-Lock **genau eine** Ladeentscheidung an.

Ohne diese Reihenfolge wertete der erste Refresh reine Defaults aus
(Automatiken aus, Max-SOC 100 %) und konnte Register 40051 auf Modus 0
setzen, obwohl ein gespeichertes Ladefenster gerade aktiv war - der
Ladevorgang wurde also beim Neustart kurz freigegeben und anschließend aus
Zwischenzuständen der nacheinander restaurierenden Entities wieder
aufgebaut.

**Drei Ladeergebnisse:** `ControlConfigStore.async_load()` liefert einen
`ControlConfigLoadStatus`, weil sich nur einer der drei Fälle migrieren
lässt:

| Status | Bedeutung | Migration erlaubt? | Automatischer Store-Write? |
| --- | --- | --- | --- |
| `LOADED` | lesbarer Store | nein | nur wenn `sanitized()` korrigiert hat |
| `MISSING` | noch kein Store | **ja** | ja, sofort nach der Migration |
| `FAILED` | Store da, aber unbrauchbar | nein | **nein, dauerhaft** |

`FAILED` entsteht bei einem I/O-Fehler, einem Payload, der kein Objekt ist,
oder einer Storage-Hauptversion, die diese Version nicht kennt (Home
Assistant meldet das per `NotImplementedError`). Dann gelten sichere
Defaults, es wird nicht migriert, und der vorhandene Store bleibt
unangetastet - er kann die einzige Kopie einer korrekten Konfiguration sein
oder von einer neueren Version stammen.

`_control_store_write_blocked` bleibt dabei für die **gesamte
Lebensdauer dieser Coordinator-Instanz** gesetzt - auch eine danach bewusst
geänderte Einstellung hebt sie nicht mehr auf
(`_async_schedule_control_save` bricht früh ab, statt wie in einer früheren
Fassung dieses Fixes den kompletten aktuellen Snapshot zu schreiben). Der
Grund: Diese Instanz kennt den zuvor gespeicherten Gesamtzustand nicht
(Netzladung, Zeitfenster, Preisparameter, ...) - würde eine einzelne
Änderung (z. B. nur "Max. SOC" auf 65 %) den vollständigen, aus lauter
Initialwerten bestehenden Snapshot schreiben, gingen alle anderen,
tatsächlich noch im Store stehenden Einstellungen verloren. Die Änderung
wirkt deshalb nur im Arbeitsspeicher; erst ein Neuladen des Config Entry
(frische Instanz, neuer Ladeversuch über `async_load_control_state`) kann
wieder lesen und damit die Sperre aufheben. Ein reparierbares Issue
(`ISSUE_CONTROL_CONFIG_UNREADABLE`,
`SaxPowerCoordinator._async_sync_unreadable_store_issue`) macht diesen
Zustand für den Anwender sichtbar, statt es nur zu loggen.

**Migration:** Die `RestoreEntity`-Zustände von `number.py`, `switch.py`,
`select.py` und `time.py` sind nur noch der einmalige Migrationspfad für
Einträge ohne Store. Nur solange `coordinator.control_config_migration_pending`
gilt (also bei `MISSING`), laufen sie überhaupt - und auch dann übernehmen
sie ausschließlich fachlich verwertbare Zustände: `restorable_bool` (nur
`on`/`off`), `restorable_number` (nur endliche Zahlen) und
`restorable_time` (nur parsebare Uhrzeiten) in `entity.py`, bei der
Strategie nur ein bekannter Wert. Beim allerersten Start eines neuen
Eintrags (gar kein Vorzustand) greift weiter die bekannte Kaskade
(Coordinator-Wert, `entity.initial_config_value`, Hard-Default aus
`const.py`); `async_finish_bootstrap()` schreibt das Ergebnis anschließend
sofort in den Store.

Ein `unknown`/`unavailable` oder sonst unbrauchbarer Altzustand ruft **gar
keinen Setter** auf, wird über `log_unmigratable_state` protokolliert, und
die Einstellung bleibt auf ihrem sicheren Vorgabewert (`sanitized()`) -
sonst würde etwa ein `unavailable` gewordener Monats-Schalter den Monat aus
dem Default "alle Monate" entfernen und die Automatik dort dauerhaft
stilllegen. Ein sicherer Vorgabewert allein wäre von einer echten,
bestätigten Einstellung aber nicht mehr unterscheidbar - deshalb merkt der
Coordinator sich das betroffene Feld zusätzlich namentlich
(`mark_control_field_unresolved`, `ControlConfig.unresolved_fields`,
mitgespeichert im Store). Diese Markierung:

- **übersteht Neustarts unverändert** - bei `LOADED` läuft für dieses Feld
  keine erneute RestoreEntity-Migration mehr (ein zweiter automatischer
  Versuch könnte einen inzwischen nur zufällig plausibel aussehenden
  Altzustand fälschlich als "jetzt doch aufgelöst" durchwinken, siehe
  `test_unresolved_fields_survive_a_restart_and_stay_flagged`);
- wird **ausschließlich durch eine spätere, ausdrückliche Änderung** der
  betroffenen Einstellung gelöscht (`clear_control_field_unresolved`, in
  jedem betroffenen `async_set_*`-Setter verdrahtet - bei den beiden
  Monats-Feldern nur bei einer echten Live-Änderung, `validate=True`, nicht
  während der eigenen 12-Schalter-Migration);
- löst, solange mindestens ein Feld betroffen ist, ein reparierbares Issue
  aus (`ISSUE_CONTROL_CONFIG_UNRESOLVED`, mit den deutschen Anzeigenamen
  der betroffenen Einstellungen als Platzhalter,
  `_CONTROL_FIELD_LABELS` in `coordinator.py`), das automatisch
  verschwindet, sobald keins mehr übrig ist.

**Verfügbarkeit:** Diese Entities erben von `entity.SaxPowerConfigEntity`,
das `available` fest auf `True` setzt. Ihre Werte stammen aus keinem
Register, deshalb dürfen sie nicht an `coordinator.last_update_success`
hängen - ein reiner Basic-Mode-Ausfall macht sie sonst sichtbar
"nicht verfügbar" und hinterlässt einen Restore-State-Dump in genau diesem
Zustand.

**Validierung:** Beim Laden wird jedes Feld einzeln gegen seinen
Wertebereich geprüft. Ein ungültiger Wert wird verworfen und in
`ControlConfig.sanitized()` durch den Hard-Default ersetzt, ohne die
übrigen gespeicherten Werte zu verlieren. Ein leeres Monats-Set und ein
wegen Überschneidung geleertes Zeitfenster sind dagegen gültige
Anwenderzustände und bleiben leer.

`sanitized()` prüft zusätzlich die **fachlichen Invarianten der
Gesamtkonfiguration**. Ein korrupter oder von Hand bearbeiteter Store kann
aus lauter einzeln gültigen Werten bestehen und trotzdem eine Kombination
enthalten, die kein Setter je erzeugt hätte - man darf hier also gerade
nicht annehmen, der Store enthalte nur von Settern akzeptierte Zustände:

- Netzladung und preisoptimiertes Laden gleichzeitig aktiv → preisoptimiertes
  Laden bleibt aus.
- Die beiden Zeitfenster überschneiden sich in Tageszeit **und** aktiven
  Monaten → das Netzladefenster wird geleert. Bewusst dieses und nicht das
  andere: Nur die Netzladung zieht aktiv Strom aus dem Netz, netzdienliches
  Laden unterbricht lediglich eine PV-Ladung.

Deshalb überspringt `_apply_control_config` die Überlappungsprüfung - sie
ist an dieser Stelle bereits gelaufen.

**Schreiben:** Nach dem Bootstrap merkt jede Einstellungsänderung über den
gemeinsamen Endpunkt `_async_apply_grid_charge_change` den aktuellen
Snapshot zum gebündelten Schreiben vor; ein unveränderter Snapshot löst
keinen Schreibvorgang aus. `async_shutdown` flusht den neuesten Stand
zusätzlich best-effort sofort.

## Register-Mapping

Der Coordinator liest drei Register-Teilblöcke mit jeweils eigenem
Aktualisierungsintervall (siehe anforderung.yaml,
REQ-LOW-INTERVAL-REGISTERS/REQ-HIGH-INTERVAL-REGISTERS):

- **NORMAL** (`READ_BLOCK_START`/`READ_BLOCK_COUNT`, Slave-ID 64, Register
  41–46, Adress-Offset `-40001`): Basic Mode – SOC, Schaltzustand,
  P-/cos(phi)-Sollwert. Folgt dem über das Config-Flow-Feld
  "Aktualisierungsintervall" einstellbaren `scan_interval`
  (`CONF_SCAN_INTERVAL`/`DEFAULT_SCAN_INTERVAL`, Default 10s, min. 5s,
  max. 3600s).
- **HIGH** (`READ_BLOCK_EXT_START`/`READ_BLOCK_EXT_COUNT`, Slave-ID 100,
  Register 40017–40109, 93 Register, Adress-Offset `-40000`): SunSpec-Modus
  – dynamische Mess-/Zustandswerte (Ströme, Spannungen, Leistungen,
  Battery-SOC, Fehlercodes, Smart-Meter-Leistung). Fest
  `READ_BLOCK_EXT_HIGH_INTERVAL` (2s), unabhängig vom NORMAL-Intervall –
  u. a. relevant für eine zügige Reaktion des netzdienlichen Ladens auf
  die tatsächliche Ladeleistung (`storage_power_active`,
  `smartmeter_power`, siehe REQ-GRID-SERVING-CHARGE).
- **LOW1**/**LOW2** (`READ_BLOCK_EXT_LOW1_START`/`READ_BLOCK_EXT_LOW1_COUNT`,
  Register 40000–40016, 17 Register – bzw.
  `READ_BLOCK_EXT_LOW2_START`/`READ_BLOCK_EXT_LOW2_COUNT`, Register
  40110–40114, 5 Register): SunSpec Common Model + Modellkopf "3Ph
  Inverter" (Hersteller, Gerätemodell, Firmware-Version, Seriennummer)
  bzw. Battery-Skalierungsfaktoren. Fest `READ_BLOCK_EXT_LOW_INTERVAL`
  (1 Stunde), da laut `modbus_llm.yaml` ausschließlich "wellknown" fixe
  bzw. sich im laufenden Betrieb praktisch nie ändernde Werte.

Der interne Coordinator-Timer (`update_interval`, `SaxPowerCoordinator.
__init__`) läuft mit `min(scan_interval, READ_BLOCK_EXT_HIGH_INTERVAL)` –
da das config_flow-Minimum für `scan_interval` (5s) immer über
`READ_BLOCK_EXT_HIGH_INTERVAL` (2s) liegt, ist das faktisch immer 2s.
`SaxPowerCoordinator._async_read_basic` (NORMAL), `_async_read_high_block`
(HIGH) und `_async_read_low_block` (LOW1/LOW2) prüfen bei jedem Tick
jeweils eigenständig per Zeitstempel-Cache, ob ihr Teilblock tatsächlich
fällig ist, und liefern sonst den zuletzt gelesenen Wert zurück – nur ein
fälliger Teilblock löst einen echten `read_holding_registers`-Aufruf aus.
Ein Schreibzugriff auf ein Basic-Mode-Register
(`SaxPowerCoordinator.async_write_register`) invalidiert den NORMAL-Cache
explizit, damit ein direkt danach ausgelöster `coordinator.async_refresh()`
(siehe Storage-On/Off-Schalter, Abschnitt "Refresh-Verhalten" unten) nicht
kurzzeitig noch den alten, gecachten Wert liefert.

Für den HIGH-Block gilt "alles oder nichts": Scheitert ein fälliger
NORMAL-Read, schlägt das gesamte Update fehl (`UpdateFailed`), da Basic
Mode die Mindestanforderung für jede Funktion der Integration ist.
Scheitert dagegen ein fälliger HIGH-Read (z. B. weil Slave-ID 100 auf dem
SAX-Gateway nicht erreichbar ist oder die Firmware zu alt ist), bleiben die
Basic-Mode-Sensoren unverändert verfügbar und lediglich die
SunSpec-HIGH-Sensoren zeigen "unbekannt", bis der Block wieder lesbar ist
(`SaxPowerCoordinator._async_read_high_block`). Ein LOW-Read-Fehler lässt
das Update ebenfalls nicht fehlschlagen – die betroffenen
Diagnose-Sensoren behalten ihren letzten Wert. Ein dauerhafter
HIGH-Ausfall wird zusätzlich als Home-Assistant-Repair-Issue angezeigt.

Die genaue Zuordnung Protokolladresse ↔ interne Adresse ↔ Bedeutung steht in
`modbus_llm.yaml`; `const.py` referenziert nur die intern verwendeten
Adressen. Die vollständigen, aktuell gültigen Anforderungen an die
Integration stehen in `anforderung.yaml`.

Der P-Sollwert (Register 41) wird als vorzeichenbehafteter 16-Bit-Wert im
Zweierkomplement übertragen: negative Werte (Laden) werden vor dem
Schreiben als `65536 + Sollwert` codiert
(`coordinator.to_unsigned16`/`to_signed16`). Positive Werte sollten laut
Encoding-Konvention Entladung bedeuten, haben gegen echte Hardware getestet
aber keine Wirkung gezeigt - siehe Kommentar bei `REG_SETPOINT_POWER`
(const.py) sowie anforderung.yaml REQ-MANUAL-DISCHARGE.

## SunSpec-Skalierung und Datentypen

`domain/registers.py` stellt reine Decoder je SunSpec-Datentyp bereit -
`decode_int16`/`decode_uint16` (auch für enum16/bitfield16) erkennen den
jeweiligen "not implemented"-Sentinel (0x8000 bzw. 0xFFFF, SunSpec Device
Information Model Specification V1.1, Abschnitt 6.4) und liefern dafür
`None` statt eines falschen Zahlenwerts, `decode_bool16` ergänzt das für
0/1-Register. `apply_typed_sunssf(raw_value, raw_scale_factor, *,
signed=True)` decodiert Wert und Skalierungsfaktor getrennt (`signed` muss
zum in `modbus_llm.yaml` dokumentierten Datentyp des Werteregisters passen)
und wendet erst danach `Wert × 10^sunssf` an - liefert `float | None`.
`decode_ascii_registers` decodiert die als ASCII-Zeichenpaare codierten
`str`-Register. Siehe anforderung.yaml, REQ-SUNSPEC-DATATYPES.

### Grenze: Registerblock → Decoder → Coordinator-Daten

Die vollständige Protokollübersetzung liegt in `domain/sunspec.py` und ist
frei von Home Assistant und pymodbus. Der Datenfluss ist einbahnig:

```
read_holding_registers          domain/sunspec.py                coordinator
────────────────────────        ─────────────────────────        ─────────────
LOW1  ab Adresse 0    ─┐
                       ├──►  decode_low_blocks(low1, low2)  ──►  data["sun_*"]
LOW2  ab Adresse 110  ─┘         └► BatteryScaleFactors  ──┐     (LOW-Cache)
                                                           │
HIGH  ab Adresse 17   ──►  decode_high_block(high, sf) ◄────┘──►  data["storage_*"],
                                 └► ic_power_setpoint_sf_raw       ["grid_*"], …
                                                                   (HIGH-Cache)
```

Die Decoder nehmen ausschließlich `Sequence[int]` entgegen - keine
Coordinator-Callbacks - und rechnen intern über Blockstart + Offset. Ist ein
Block kürzer als das dokumentierte Layout, fällt das als
`SunSpecDecodeError` auf statt als IndexError mitten in der Feldzuordnung.

Die Feldzuordnung des HIGH-Blocks steht als deklarative Tabelle
`HIGH_BLOCK_FIELDS` (`ScaledField`/`EnumField`/`RawField`/`BoolField`) im
Modul. Dadurch lässt sich jede Adresse und jede Signed/Unsigned-Entscheidung
in `tests/test_sunspec_mapping.py` parametrisch gegen `modbus_llm.yaml`
prüfen, ohne die YAML-Datei zur Laufzeit zu laden.

Beim Coordinator bleiben Transport, Poll-Intervalle und Caches, Resilienz-
und Repair-Verhalten, die Cache-Invalidierung nach Writes, die Abbildung auf
`UpdateFailed`/`ConfigEntryNotReady` sowie die Entscheidung, wann die zuletzt
erfolgreich gelesenen LOW-Skalierungsfaktoren weiterverwendet werden. Auch
`config_flow.py` nutzt für die Einrichtungs-Zusammenfassung denselben
`decode_identity`, statt die Geräteidentität ein zweites Mal zu
implementieren.

## Refresh-Verhalten

Nutzerausgelöste Schreibaktionen (Switch, Number) rufen nach dem Schreiben
`coordinator.async_refresh()` auf – das ist die *ungedebouncte*
Coordinator-Methode. `async_request_refresh()` (debounced) wird bewusst
vermieden, da bei schnell aufeinanderfolgenden Aktionen sonst ein
verzögerter/verworfener Refresh dazu führen kann, dass die UI kurzzeitig
einen veralteten Wert zeigt.

Der einzige Fall, in dem eine Entity direkt nach einem Write auf einen per
`async_refresh()` sofort aktualisierten Zustand angewiesen ist, ist der
Storage-On/Off-Schalter (Basic-Mode-Register 45). Da der NORMAL-Block seit
REQ-HIGH-INTERVAL-REGISTERS eigenständig gecacht wird (siehe
Register-Mapping oben), invalidiert `async_write_register` den NORMAL-Cache
explizit - ohne das würde der direkt danach ausgelöste `async_refresh()`
sonst innerhalb des `scan_interval`-Fensters den alten, gecachten Wert
liefern statt den soeben geschriebenen.

## Tests

```
tests/
├── conftest.py                  Aktiviert das Laden von custom_components in Tests
├── test_calibration.py           Reine 7-Tage-/Voll-SOC-Policy und versionierte
│                                  UTC-Persistenz einschließlich ungültiger Daten
├── test_sunspec_decoder.py       Reine Decodertests für domain/sunspec.py (ohne
│                                  Coordinator/HA/pymodbus): alle vier SunSpec-Modelle,
│                                  Signed/Unsigned/Sentinelwerte, ASCII-Register, unbekannte
│                                  Enums, ungültige Blocklänge sowie LOW-alt/HIGH-neu
├── test_sunspec_mapping.py       Parametrische Prüfung der Feldzuordnung und aller
│                                  REG_SUN_*-Konstanten gegen modbus_llm.yaml als Quelle -
│                                  die YAML-Datei wird nur im Test geladen, nie zur Laufzeit
├── test_coordinator.py           Unit-Tests: signed/unsigned16-Konvertierung, typisierte
│                                  SunSpec-Decoder + Not-Implemented-Sentinels,
│                                  Fehlerbehandlung bei Modbus-Schreibfehlern, Wire-/Adapter-
│                                  Nachweis für die drei SunSpec-Teilblöcke (gemockt), inkl.
│                                  Weiterverwendung der letzten LOW-Skalierungsfaktoren bei
│                                  fehlgeschlagenem LOW-Refresh, Zeitfenster-Logik +
│                                  Enforcement für zeitgesteuertes Laden, netzdienliches Laden
│                                  und die Max-SOC-Sperre (alle über SunSpec-Modus-Register
│                                  40049/40051, auch unabhängig voneinander), Watt-zu-Prozent-
│                                  Umrechnung, Schreibintervall aus Register 40050,
│                                  Zeitfenster-Überlappungsprüfung (windows_overlap,
│                                  Ablehnung überlappender Änderungen), aktive Monate
│                                  (Enforcement, Default "alle Monate", Überlappungsprüfung
│                                  inkl. erlaubter Zeitfenster-Überlappung bei disjunkten Monaten)
├── test_config_flow.py            Unit-Tests: erfolgreicher vierstufiger Config Flow
│                                  (Verbindung, optionale Netzladung-/Dashboard-Vorbelegung
│                                  inkl. Defaults bei leeren Schritten, Abschlussseite mit
│                                  Firmware/Seriennummer/SunSpec-Status/Entity-Anzahl als
│                                  description_placeholders - auch bei nicht erreichbarem
│                                  SunSpec-Modus), "cannot_connect"-Fehler (gemockter
│                                  AsyncModbusTcpClient)
├── test_sensor_descriptions.py     Konsistenz-Tests über alle ~56 Sensor-Beschreibungen:
│                                  eindeutige Keys, vollständige DE/EN-Übersetzungen,
│                                  value_fn wirft für keinen Sensor eine Exception
├── test_integration_live.py        End-to-End-Tests gegen einen echten, lokal gestarteten
│                                  Modbus-TCP-Server (kein Mock) – prüft den kompletten Weg
│                                  Config Entry → Coordinator → Entities → echtes Wire-Protokoll,
│                                  inkl. Regressionstest für den Resilienz-Fall (SunSpec-Modus
│                                  nicht erreichbar → Basic-Mode-Sensoren bleiben da), einen
│                                  End-to-End-Test für zeitgesteuertes Laden (SunSpec-Modus-
│                                  Register 40049/40051) sowie Tests für die Vorbelegung aus
│                                  dem Config Entry beim allerersten Start (mit und ohne im
│                                  Entry hinterlegte Netzladung-Werte)
├── test_price_optimizer.py         Preisoptimiertes Laden: Einlesen der Attributformate
│                                  verbreiteter Strompreis-Integrationen, Planberechnung je
│                                  Strategie (inkl. Planungshorizont und PV-Prognose im
│                                  Smart-Modus), Schreibpfad und Abbruchgründe im Coordinator,
│                                  Vorrang des zeitgesteuerten Ladens sowie der
│                                  Bestätigungsdialog beim Konflikt der beiden netzladenden
│                                  Automatiken (repairs.py)
├── test_tariff.py                  Tarifmodell der Wirtschaftlichkeitsauswertung
│                                  (REQ-ECONOMICS-TARIFFS): Festpreis, Grundpreis und acht
│                                  Zeitfenster (halboffen, über Mitternacht, angrenzend,
│                                  überlappend), beide Sommerzeitwechsel, Abbildung der
│                                  Options auf das Domänenmodell (inkl. einer vorhandenen,
│                                  aber unvollständigen/unlesbaren Zeitfenstergruppe, die
│                                  TARIFF_INCOMPLETE auslösen muss statt stillschweigend
│                                  zu verschwinden), dynamischer Tarif am gemeinsamen
│                                  Preis-Sensor samt aller Gründe für einen fehlenden
│                                  Preis sowie der Lebenszyklus der Zustandsbeobachter
├── test_energy_accounting.py        Reine Bilanzregel der Ladeenergie-Herkunft
│                                  (REQ-ENERGY-ORIGIN, domain/energy_accounting.py):
│                                  reine PV-/Netzladung, gemischte Ladung, Einspeisung
│                                  während des Ladens, Netzbezug größer/kleiner als die
│                                  Ladeleistung, unbekannter Smartmeter-Wert sowie die
│                                  Delta-Invariante (grid + pv + unknown == charged) über
│                                  viele zufällige Intervalle ohne kumulative Drift
├── test_energy_persistence.py       Persistenz der Energiezähler inkl. Herkunft
│                                  (REQ-ENERGY-DASHBOARD/REQ-ENERGY-ORIGIN):
│                                  Store-Round-Trip, unabhängige Feldvalidierung
│                                  (auch für die drei neuen Zähler und den
│                                  Startzeitpunkt), Drosselung/Sofort-Flush, rückläufige
│                                  Snapshots, RestoreEntity-Migrationspfad von
│                                  energy_charged/-discharged, Version-1-Migration ohne
│                                  erfundene Historie (inkl. eines echten, unentpackten
│                                  Store-Envelopes über die hass_storage-Fixture -
│                                  Regressionstest gegen einen versehentlichen
│                                  Hauptversionssprung, der Home Assistants
│                                  NotImplementedError-Migrationsverhalten unbemerkt
│                                  ausgelöst hätte), bereits initialisierter Store,
│                                  Store-Ladefehler lässt die Herkunft uninitialisiert,
│                                  Wiederanlauf nach einem unvollständigen
│                                  Herkunfts-Quartett ohne an der alten Teil-Baseline zu
│                                  scheitern, zwei getrennte Config Entries sowie die
│                                  Coordinator-Verdrahtung (Rundung, Diagnosewert
│                                  energy_origin_coverage, Entladung und SunSpec-Ausfall
│                                  bleiben unverändert) in test_coordinator.py
├── test_economics_accounting.py     Reine Geldbilanz (REQ-ECONOMICS-ACCOUNTING,
│                                  domain/economics_accounting.py): Netz-/PV-/gemischte
│                                  Ladung, unbekannte Herkunft nie bepreist, fehlender
│                                  Netzbezugs-/Einspeisepreis macht Ladung unbepreist statt
│                                  erfunden, negative Preise ohne Clamping, Entladung aus
│                                  unbewertetem Bestand ohne vermiedenen Geldwert (Regression
│                                  zum verworfenen Issue #42), teilweise/vollständig
│                                  monetarisierbare Entladung, fehlender Preis bei
│                                  Entladung wird nicht rückwirkend bewertet,
│                                  Ladeverlust-Sichtbarkeit ohne angenommenen
│                                  Wirkungsgradfaktor, Anfangsbestand sowie
│                                  SOC-Minimum-Korrektur
├── test_economics_persistence.py    Persistenz der Wirtschaftlichkeitsbilanz
│                                  (REQ-ECONOMICS-ACCOUNTING): Store-Round-Trip, negative
│                                  Geldsummen ausdrücklich erlaubt (keine
│                                  Monotonieprüfung), unabhängige Feldvalidierung,
│                                  rückläufige unpriced-Zähler abgelehnt, der
│                                  unvalued_inventory-Bestand darf dagegen sinken,
│                                  unveränderlicher Aktivierungszeitpunkt, Wiederanlauf
│                                  nach einem unvollständigen Sieben-Felder-Bündel ohne an
│                                  der alten Teil-Baseline zu scheitern, zwei getrennte
│                                  Config Entries, Drosselung/Sofort-Flush sowie der
│                                  Coordinator-Bootstrap (wartet auf Kapazität/SOC,
│                                  deaktivierter Tarif bootstrapped nicht, Shutdown-Flush,
│                                  Tarifrevisions-Zeitstempel); zusätzlich die
│                                  Tages-Buckets/Payback-Erweiterung (REQ-ECONOMICS-
│                                  AMORTIZATION): Round-Trip von day_results/current_day/
│                                  payback_achieved_at, ein kaputter Tageseintrag verwirft
│                                  nur sich selbst, das Fünfer-Bündel des laufenden Tages
│                                  wird als Ganzes verworfen, Kappung auf MAX_STORED_DAYS
│                                  sowie der unveränderliche Payback-Zeitpunkt
├── test_economics_amortization.py   Reine ROI-/Amortisationsprognose
│                                  (REQ-ECONOMICS-AMORTIZATION,
│                                  domain/economics_amortization.py): ROI unklemmt
│                                  (negativ, über 100 %), Fortschritts-Klemmung auf
│                                  0..100, Restbetrag auf 0 gefloort, Tagesabdeckung an
│                                  der 95-%-Schwelle, ausgeschlossener laufender Tag,
│                                  29/30/31-Tage-Fenster (31 verwendet nur die jüngsten
│                                  30), ein einzelner schlechter Tag macht die gesamte
│                                  Prognose unavailable, Durchschnitt/Hochrechnung sowie
│                                  das aufgerundete Rückzahlungsdatum inkl. eines nicht
│                                  positiven Durchschnitts (Datum bleibt unbekannt) und
│                                  eines bereits erreichten Paybacks; die
│                                  Coordinator-seitige Verdrahtung (Tageswechsel-
│                                  Erkennung inkl. DST/Neustart/Doppelverarbeitung,
│                                  ROI-/Restbetrags-/Tagesergebnis-Sensoren samt
│                                  Tarifpause-Maskierung, Payback-Erkennung,
│                                  Investitionskostenänderung ohne Rückwirkung) liegt in
│                                  test_coordinator.py
├── test_economics_status.py         Reine Status-/Abdeckungsableitung
│                                  (REQ-ECONOMICS-OBSERVABILITY,
│                                  domain/economics_status.py): jeder der sieben Status
│                                  einzeln sowie kombinierte, gleichzeitig zutreffende
│                                  Probleme (Priorität), Preisabdeckung energiebasiert mit
│                                  100 % bei Nenner 0; die Coordinator-seitige Verdrahtung
│                                  (Preisausfall-Karenzzeit vs. sofortiger
│                                  Konfigurationsfehler, Herkunfts-/Preisabdeckung aus
│                                  echten Zählern, Speicherfehler-Freeze, kontrollierter
│                                  Bilanzneustart inkl. Atomarität) liegt in
│                                  test_coordinator.py/test_init.py
├── test_control_persistence.py     Persistenz und Startreihenfolge der Ladeeinstellungen
│                                  (REQ-CONTROL-CONFIG-BOOTSTRAP): Store-Round-Trip, korrupter/
│                                  unvollständiger/unlesbarer Store (inkl. dauerhafter
│                                  Schreibsperre über eine einzelne spätere Änderung hinweg und
│                                  Reparaturhinweis), unbekannte künftige Storage-Version,
│                                  überlappende Zeitfenster im Store, getrennte Stores je Config
│                                  Entry, gesperrte Writes während des Bootstraps, Migration ohne
│                                  Store, Basic-Mode-Ausfall, unknown/unavailable in allen vier
│                                  Plattformen inkl. persistenter unresolved_fields-Markierung
│                                  über einen simulierten Neustart hinweg samt Issue-Lebenszyklus,
│                                  Max-SOC-Hold über den Neustart und Verfügbarkeit der
│                                  Konfigurations-Entities
├── test_repairs.py                 Sechs Selbstdiagnose-Issues (coordinator.
│                                  _async_check_self_diagnostics): Auslösen nach Karenzzeit,
│                                  Idempotenz (kein erneutes Anlegen bei unverändertem
│                                  Problemzustand), Selbstheilung sobald die Ursache behoben
│                                  ist - fünf davon siehe anforderung.yaml
│                                  REQ-SELF-DIAGNOSIS-REPAIRS, das sechste
│                                  (economics_price_unavailable) REQ-ECONOMICS-OBSERVABILITY
├── test_dashboard.py                Mitgeliefertes Lovelace-Dashboard (REQ-BUNDLED-DASHBOARD/
│                                  REQ-ECONOMICS-DASHBOARD): Entity-Auflösung/-Auslassung je
│                                  Tab, Gauge-Karten, geräteprefix-freie Labels für alle fünf
│                                  Views inkl. des Tabs "Wirtschaftlichkeit" (Karten-/Entity-
│                                  Reihenfolge, Attribut-Zeilen für Preisabdeckung/
│                                  Bilanzbeginn, Amortisationsfortschritt als Gauge,
│                                  statistics-graph-Verlaufskarte, nicht-leerer View auch ohne
│                                  jede registrierte Entity), create_dashboard-Idempotenz und
│                                  reinstall_dashboard-Service
├── test_economics_dashboard_e2e.py  Ende-zu-Ende über die gesamte Wirtschaftlichkeits-Reihe
│                                  (REQ-ECONOMICS-DASHBOARD-Akzeptanzkriterium): je ein PV-Lade-,
│                                  Netzlade- und Entladeabschnitt von der Tarifauflösung über die
│                                  Herkunftsaufteilung und die Geldsensoren bis zur
│                                  Dashboard-Entityauflösung
├── test_real_hardware.py           Optionaler Live-Hardware-Test gegen einen *echten* SAX
│                                  Speicher (siehe Abschnitt "Test gegen echte Hardware" unten)
└── real_device.yaml                Verbindungsdaten (IP etc.) für test_real_hardware.py
```

`test_coordinator.py`, `test_config_flow.py` und `test_sensor_descriptions.py`
mocken den `pymodbus`-Client bzw. arbeiten rein auf Python-Ebene und prüfen
die Programmlogik. `test_integration_live.py` geht einen Schritt weiter: Er
startet mit `pymodbus.server.ModbusTcpServer` einen echten Modbus-TCP-Server
auf `127.0.0.1` mit simulierten Geräten (Slave-ID 64 Basic Mode, Slave-ID 100
SunSpec-Modus), befüllt sie mit Registerwerten aus `modbus_llm.yaml` und lässt
die Integration real darüber kommunizieren. Geprüft werden u. a.:

- korrektes Lesen von SOC über echtes TCP
- Entlade-/Ladeleistung und Smart-Meter-Leistung aus dem SunSpec-Modus
  (Register 40029/40072) über echtes TCP
- SunSpec-Skalierung (z. B. Netzfrequenz, Zelltemperatur) über echtes TCP
- Speicher-Switch aus/an inkl. Rücklesen des geschriebenen Werts
- Max-SOC-Sperre (SOC über Zielwert → Register 40051/40049 über den
  SunSpec-Modus geschrieben, unabhängig von zeitgesteuertem Laden)
- Netzladung: periodischer Sollwert-Write auf Register 41, verifiziert über
  einen unabhängigen zweiten Modbus-Client
- Fehlt der SunSpec-Modus-Server (Slave-ID 100) komplett: Config Entry lädt
  trotzdem erfolgreich, Basic-Mode-Sensoren liefern echte Werte,
  SunSpec-Sensoren zeigen "unbekannt" statt die Integration am Start zu
  hindern
- Neustart in einem gespeicherten, gerade aktiven Ladefenster: Register
  40051 wird zu keinem Zeitpunkt auf 0 geschrieben, die gespeicherte
  Konfiguration ist vollständig sichtbar zurück (siehe
  [Startreihenfolge und Persistenz der Ladeeinstellungen](#startreihenfolge-und-persistenz-der-ladeeinstellungen))

Alle Tests laufen auch ohne echte Hardware und ohne Internetzugriff (der
Live-Test bindet nur an `127.0.0.1`) – der Live-Hardware-Test
(`test_real_hardware.py`) wird ohne hinterlegte IP automatisch
übersprungen, siehe Abschnitt "Test gegen echte Hardware" unten.

### Manuelle Testausführung

Die Tests laufen außerhalb des DevContainers in einer eigenen Python-
Umgebung (venv), damit `homeassistant` & Co. nicht die System-Python-
Installation zumüllen:

```bash
cd sax-ha

# Einmalig: virtuelle Umgebung anlegen und Abhängigkeiten installieren
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements_test.txt

# Alle Tests ausführen
pytest -v
```

Bei künftigen Läufen genügt (ggf. nach erneutem `pip install`, falls sich
`requirements_test.txt` geändert hat):

```bash
source .venv/bin/activate
pytest -v
```

Nützliche Varianten:

| Befehl | Zweck |
| --- | --- |
| `pytest` | Alle Tests, kompakte Ausgabe |
| `pytest -v` | Alle Tests, ein Ergebnis pro Testfall |
| `pytest -rs` | Zusätzlich Grund für übersprungene (`SKIPPED`) Tests anzeigen |
| `pytest tests/test_coordinator.py -v` | Nur eine Testdatei |
| `pytest -k max_soc -v` | Nur Tests, deren Name "max_soc" enthält |
| `pytest tests/test_real_hardware.py -v` | Nur der Live-Hardware-Test (siehe unten) |

Im **DevContainer** (`.devcontainer/`) sind `homeassistant`, `pytest` etc.
bereits vorinstalliert – dort reicht direkt `pytest -v` ohne eigenes venv.

**Mögliche Probleme und Lösungen:**

| Problem | Ursache | Lösung |
| --- | --- | --- |
| `command not found: pip` | Auf macOS/Linux ist `pip` oft nicht direkt im `PATH`, nur `pip3`/`python3 -m pip`. | Venv aktivieren (`source .venv/bin/activate`) – darin heißt der Befehl wieder schlicht `pip`. Alternativ `python3 -m pip install -r requirements_test.txt`. |
| `ModuleNotFoundError: No module named 'homeassistant'` (o. Ä.) | venv nicht aktiviert oder `pip install -r requirements_test.txt` noch nicht/nicht erneut ausgeführt. | `source .venv/bin/activate` prüfen (Prompt zeigt `(.venv)`), danach `pip install -r requirements_test.txt` (erneut) ausführen. |
| Installation von `homeassistant` dauert sehr lange / bricht ab | `homeassistant` hat viele Abhängigkeiten; instabile Internetverbindung. | Erneut versuchen, ggf. `pip install -r requirements_test.txt -v` für Fortschrittsanzeige. Reiner Installationsvorgang, kein Testproblem. |
| `pytest_homeassistant_custom_component...SocketBlockedError` / `Socket opened during test` bei eigenen neuen Tests | pytest-homeassistant-custom-component sperrt Socket-Erstellung standardmäßig komplett (bis auf `127.0.0.1`). Die `socket_enabled`-Fixture aus pytest-socket **reicht dafür allein nicht aus** – sie hebt zwar die Socket-Sperre auf, wird aber vom Setup-Hook des HA-Test-Plugins wieder auf `127.0.0.1` zurückgesetzt, sobald eine echte externe IP angesprochen wird. | Für Verbindungen zu einer echten externen IP explizit `pytest_socket.enable_socket()` gefolgt von `pytest_socket.socket_allow_hosts([host, "127.0.0.1"], allow_unix_socket=True)` aufrufen (siehe `real_client`-Fixture in `test_real_hardware.py`). Für Verbindungen nur zu `127.0.0.1` (wie in `test_integration_live.py`) genügt weiterhin die `socket_enabled`-Fixture. |
| `tests/test_real_hardware.py` wird übersprungen (`SKIPPED`) | Kein `host` in `tests/real_device.yaml` hinterlegt, oder der Speicher ist gerade nicht erreichbar. | Mit `pytest -rs` den genauen Skip-Grund anzeigen lassen. `host` in `tests/real_device.yaml` eintragen (siehe Abschnitt unten) bzw. Erreichbarkeit prüfen (siehe nächste Zeile). |
| Live-Hardware-Test bricht mit Verbindungsfehler ab statt zu überspringen | Der erste Verbindungsversuch (`connect()`) klappt kurzzeitig, ein späterer Read schlägt dann fehl (Netzwerk instabil, falscher Port/Slave-ID). | IP/Port in `tests/real_device.yaml` prüfen (`ping <IP>`, `nc -vz <IP> 502`). Prüfen, ob eine andere Anwendung (z. B. eine bereits laufende Home-Assistant-Instanz) parallel denselben Modbus-Port belegt – SAX-Geräte erlauben oft nur eine aktive Verbindung gleichzeitig. |
| `test_read_real_sunspec_mode_values` wird übersprungen, `test_read_real_basic_mode_values` läuft durch | Der SunSpec-Modus (Slave-ID 100) ist auf diesem Gerät nicht erreichbar – z. B. zu alte Firmware (Master V61/Gateway V54 oder neuer nötig). Das Gerät antwortet dann entweder mit einer Modbus-Fehlerantwort oder mit Modbus-Exception-Code 11 "Gateway Target Device Failed to Respond", was pymodbus als `ModbusIOException` auswirft. | Erwartetes, dokumentiertes Verhalten – kein Fehler, entspricht der Fehlerbehandlung im produktiven Coordinator. Falls der SunSpec-Modus erwartet wird: Firmware-Version beim Hersteller/Installateur klären. |
| `ruff`/`black` melden Formatierungsfehler bei eigenen Änderungen | Code entspricht nicht dem Projektstil (Zeilenlänge 88, Formatierung). | `pip install ruff black` (falls nicht vorhanden), dann `black custom_components scripts tests` zum automatischen Formatieren und `ruff check custom_components scripts tests` zur Kontrolle. |
| Tests schlagen nach einem `git pull` plötzlich fehl | `requirements_test.txt` hat sich geändert (neue/aktualisierte Abhängigkeit), venv ist veraltet. | `source .venv/bin/activate && pip install -r requirements_test.txt` erneut ausführen. |

### Test gegen echte Hardware

`tests/test_real_hardware.py` liest – anders als `test_integration_live.py`
(simulierter Server) – Werte direkt von einem echten SAX Power Home (Plus)
im lokalen Netz. Rein lesend, kein Schreibzugriff.

> Frühere Versionen dieser Datei enthielten zusätzlich schreibende Live-
> Tests für eine "manuelle Entladung" (positiver Sollwert auf Register
> 40049 bzw. dem älteren Basic-Mode-Register 41). Damit wurde live
> nachgewiesen, dass beide Wege die Register zwar korrekt schreiben, der
> reale Speicher aber in keinem Fall tatsächlich entladen hat - der
> Hersteller hat auf Rückfrage bestätigt, dass eine ferngesteuerte manuelle
> Entladung nicht vorgesehen ist. Die Funktion (Entities, Coordinator-Logik,
> Tests) wurde deshalb wieder entfernt, siehe anforderung.yaml
> REQ-MANUAL-DISCHARGE sowie die Kommentare bei REG_SETPOINT_POWER/
> REG_SUN_IC_POWER_SETPOINT_PCT in const.py.

Die Ziel-IP steht in `tests/real_device.yaml` (im Repository abgelegt):

```yaml
host: null   # <- echte IP eintragen, z. B. "192.168.1.50"
port: 502
slave_id_basic: 64
slave_id_extended: 100
connect_timeout: 3
```

Solange `host: null` (Auslieferungszustand) oder der Speicher nicht
erreichbar ist, werden die beiden Tests automatisch übersprungen (kein
Fehlschlag) – der Test läuft also weder in CI noch bei Entwicklern ohne
physischen Zugriff auf die Hardware. Nach Eintragen einer echten IP:

```bash
pytest tests/test_real_hardware.py -v
```

## Releaseprozess

`custom_components/sax_power/manifest.json` ist die ausgelieferte
Versionsquelle. Jeder Pull Request trägt genau eines der Labels
`release:major`, `release:minor`, `release:patch` oder `release:snapshot`.
Stabile Pull Requests setzen die Manifest-Version auf den daraus berechneten
nächsten stabilen SemVer-Tag. Ausgehend vom letzten stabilen Tag `1.2.3` sind
das beispielsweise `2.0.0`, `1.3.0` oder `1.2.4`. Prerelease- und
Snapshot-Tags verändern diese stabile Versionslinie nicht.

`release:snapshot` ist für größere oder aufeinander aufbauende Entwicklungen
vorgesehen, die vor einem Produktiv-Release realitätsnah erprobt werden
müssen. Ein solcher PR behält die aktuelle stabile Manifest-Version. Nach
erfolgreicher CI erzeugt `.github/workflows/snapshot-release.yaml` aus dem
exakt getesteten PR-Commit eine installierbare ZIP-Datei, eine SHA-256-Prüfsumme
und eine als Vorabversion markierte GitHub-Veröffentlichung. Tag und gepackte
Manifest-Version enthalten PR-Nummer und Commit-Kürzel und sind dadurch
unveränderlich und eindeutig.

Der privilegierte Snapshot-Workflow führt keinen Code aus dem PR aus. Er lädt
das Packprogramm separat aus dem vertrauenswürdigen Standardbranch, behandelt
den PR-Checkout nur als Daten und verweigert unter anderem Fork-PRs,
mehrdeutige PR-Zuordnungen und Symlinks. Snapshot-Dateien sind ausschließlich
für eine getrennte Home-Assistant-Testinstanz bestimmt. Ein Snapshot-PR darf
nicht gemergt werden. Nach erfolgreichem Test werden das Snapshot-Label durch
genau ein stabiles Release-Label ersetzt, die Manifest-Version erhöht und die
vollständige CI erneut ausgeführt. Als zweite Sicherung erzeugt der stabile
Release-Workflow bei einem versehentlichen Snapshot-Merge weder Tag noch
Produktiv-Release.

Die Prüfung lässt sich vor dem Push lokal ausführen (Label anpassen):

```bash
python scripts/release_metadata.py --labels-json '["release:patch"]'
# oder ohne Manifest-Bump für einen Snapshot-PR:
python scripts/release_metadata.py --labels-json '["release:snapshot"]'
```

Im Pull Request prüft CI dieselbe Logik und führt zusätzlich die HACS-Action
sowie hassfest aus. Null oder mehrere Release-Labels, eine ungültige oder
abweichende Manifest-Version und ein bereits existierender Ziel-Tag brechen
die Prüfung ab. `hacs.json.homeassistant` entspricht dabei exakt der in
`requirements_test.txt` fixierten und in CI getesteten Home-Assistant-Version;
damit bietet HACS die Integration keiner unbelegten älteren Python-/HA-Laufzeit
an.

Nach dem Merge testet der `push`-Lauf der Continuous Integration den neuen
`main`-Commit. Erst dessen erfolgreicher Abschluss startet den
Release-Workflow. Dieser checkt exakt den in CI getesteten SHA aus, liest das
eine Release-Label des zugehörigen gemergten Pull Requests und wiederholt alle
Metadatenprüfungen, bevor er den Manifest-Wert als Tag schreibt. Erst danach
wird der GitHub Release erzeugt. Schlägt eine Prüfung fehl, existieren weder
neuer Tag noch neuer Release.

## Lokale Entwicklung (DevContainer)

Das Repo enthält einen VS Code DevContainer für die lokale Entwicklung/Tests:

1. Repo in VS Code öffnen, "Reopen in Container" wählen
2. Im Container: `hass -c config` startet eine lokale Home Assistant Instanz
   auf Port 8123 mit bereits verlinkter Custom Component
3. Tests ausführen: `pytest -v`
4. Linting/Formatierung: `ruff check custom_components scripts tests` bzw. `black custom_components scripts tests`

## Quellen

Die Anforderungen stammen aus `anforderung.yaml`. Das Modbus-Register-Mapping
in `modbus_llm.yaml` ist für den Basic-Mode-Block (Slave-ID 64) sowie den
SunSpec-Modus-Block (Slave-ID 100) gegen `modbus.pdf` – die offizielle
sax-power.net-Dokumentation ("SAX Power Home/Home Plus Modbus-TCP
Dokumentation (SUNSPEC-Mode)") – sowie byte-genau gegen echte Hardware
verifiziert.
