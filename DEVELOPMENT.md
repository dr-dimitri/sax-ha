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
│                          (economics_accounting.py) sowie den ROI-/
│                          Amortisationsstand darüber
│                          (economics_amortization.py), Entladeprognose
│                          (discharge_forecast.py) und PV-Überbrückungsplanung
│                          (bridge_charge.py)
├── application/         Use-Case-Policies für Ladeprioritäten und periodische
│                          Vollkalibrierung, die Abbildung der Tarif-Options auf
│                          das Domänenmodell (economics.py), getrennte
│                          Tarifprofile (tariff_profiles.py), explizite PV-/
│                          Zeitfenstereingaben und begrenzte Ladeaufträge
│                          (bridge_inputs.py, bridge_session.py) sowie der
│                          injizierbare Modbus-Client-Port
├── infrastructure/      Home-Assistant-Adapter für zustandsbasierte
│                          Repair-Issues sowie versionierte Stores
│                          (Kalibrierung, Energiezähler inkl. Herkunft der
│                          Ladeenergie, Wirtschaftlichkeitsbilanz,
│                          Ladeeinstellungen und fensterbezogene Laufzeitzustände)
├── config_flow.py       GUI-Einrichtung (Verbindung + optionale
│                          Netzladung-Vorbelegung), Verbindungsvalidierung,
│                          Options Flow (preisoptimiertes Laden + getrennte
│                          PV-Prognosequellen)
├── coordinator.py       DataUpdateCoordinator: Reads (Basic+SunSpec), Writes,
│                          Poll-Intervalle/Caches, Max-SOC-Logik, Netzladung,
│                          zeitgesteuertes Laden, netzdienliches Laden,
│                          preisoptimiertes Laden (Anwendung des Ladeplans),
│                          Zeitfenster-Überlappungsprüfung
├── price_optimizer.py    Preisoptimiertes Laden: Einlesen der Preisdaten aus
│                          einer beliebigen Preis-Sensor-Entity, Ladeplanung je
│                          Strategie, getrennte PV-Prognosequellen,
│                          60-Sekunden-Takt - ohne Modbus-Zugriff
├── economics.py          Home-Assistant-Adapter des Tarifmodells
│                          (SaxTariffProvider): liest Options und Preis-Sensor
│                          und liefert den geltenden Netzbezugspreis als Quote
│                          sowie beobachtete Preisintervalle für die Geldbilanz,
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
├── number.py              Max. SOC (geräteweite Grenze und Ziel-SOC für
│                          preisoptimiertes Laden), Netzladen Max. SOC und
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
│                          + coordinator.data + Ladeplan + Roh-/Startwerte der
│                          Energie- und Geldzähler, IP-Adresse redigiert
├── vue_dashboard.py        Dashboard SAX Power als integriertes Vue-Panel, siehe
│                          REQ-VUE-DASHBOARD; Registrierung und Asset-Auslieferung
├── dashboard_api.py        Berechtigungsgefiltertes Entity-Metadatenabo für Vue,
│                          siehe REQ-VUE-ENTITY-BINDING
├── dashboard_tariff.py     Tarifprofile, Tarifwechsel und Netzladefreigabe
├── dashboard_price_series.py Vollständige Tagespreise mit Zeitzone und Lücken
├── dashboard_statistics.py Authentifizierter Recorder-Adapter für Kalenderwerte
│                          und freie Zeiträume, siehe REQ-VUE-SAVINGS
├── frontend/              Eingechecktes Vue-Bundle für HACS und Snapshots
├── services.yaml           Service-Schema für die UI
└── translations/            DE/EN-Übersetzungen (strings.json ist die Vorlage)

tests/                Siehe Abschnitt "Tests"
frontend/             Vue-/TypeScript-Quellen, Build, Komponenten-/Browser-Tests
.devcontainer/         VS Code DevContainer für lokale Entwicklung
```

### Dashboard SAX Power

`vue_dashboard.py` bindet das Custom Element `sax-power-vue-panel` über
Home Assistants `panel_custom` unter `/sax-power-vue` ein. Grundlage ist die
in `requirements_test.txt` unterstützte HA-Version. Der Panel-Adapter erhält
`hass`, `narrow`, `panel` und `route` vom HA-Frontend; `panel.config.entry_id`
ordnet die Entity-Anbindung dem Config Entry zu. Die fünf navigierbaren Views
unter `frontend/src/views/` bilden das einzige mitgelieferte Dashboard **SAX Power**.
Der technische Pfad `/sax-power-vue`, das Custom Element und die bestehenden
Config-Schlüssel bleiben kompatibel; UI-Name und Aktivierungsoption tragen
keine Vue-/Vorschaukennzeichnung.

| View | Anforderungen | Aufgabe |
| --- | --- | --- |
| `GeneralView.vue` | `REQ-VUE-GENERAL` | Skalen, Live-Messwerte, Speicherschalter, Max-SOC und optionale Gerätedaten. |
| `ElectricityTariffView.vue` | `REQ-VUE-ELECTRICITY-TARIFF` | Gemeinsame Tarifwahl, Tagespreiskurve und kompakt bearbeitbare Tarif-/Ladeeinstellungen für zeitvariablen und dynamischen Tarif. |
| `TimedChargingView.vue` | `REQ-VUE-CHARGING`, `REQ-TIME-OF-USE-CHARGE-SOURCE`, `REQ-BRIDGE-CHARGE` | Tarifpreisfenster, bei anderen Tarifarten Netzladezeitfenster, Entladestatus, Netzladeziel/Startschwelle, Monatsschalter und begründete Verbrauchsplanung bis zum PV-Start. |
| `GridServingView.vue` | `REQ-VUE-CHARGING` | Ladepause, dynamisch benannte PV-Prognose, Schwelle, Status und Monate. |
| `SavingsView.vue` | `REQ-VUE-SAVINGS` | Amortisation, gemeinsame Tarifpreisfenster, Kalenderwerte und freie Recorder-Auswertung. |

Die Vue-Navigation folgt dieser Reihenfolge: Allgemeine Informationen,
Stromtarif (EN: Electricity tariff), Zeitvariabler Tarif (EN: Time-of-use tariff),
Netzdienliches Laden, Amortisation. `stromtarif` ersetzt den dynamischen Einstieg;
`dynamisches-laden` wird ohne Schreibaktion dorthin weitergeleitet. Der alte
Tab unter `ladeautomatik` bleibt als Fallback immer sichtbar. Entity-Schlüssel
und bestehende Steuerparameter bleiben erhalten.

`ChargingLayout.vue` hält die Kartenstruktur der bisherigen Ladeansichten
gemeinsam.
Es filtert leere Karten und verwendet die gleichen `EntityControl`- und
`EntityValue`-Komponenten wie die allgemeine Ansicht sowie `TimeWindowControl`
für beide Zeitfenster. Die gemeinsame
[`components/MonthSelection.vue`](frontend/src/components/MonthSelection.vue)
kapselt Zusammenfassung und Quartalsauswahl beider Monatsgruppen.
`hideConfirmedLabel` in Layout und Bedienkomponente entfernt in
Stromtarif und Zeitvariabler Tarif den Präfix
„Bestätigter Wert:“ (EN: „Confirmed value:“) bei Zahlen und Auswahllisten.
Bestätigte HA-Werte bleiben auch während lokaler Entwürfe sichtbar und über
`aria-describedby` zugeordnet.
Die gemeinsame Zeitfenster-Zeile „Bestätigt:“ bleibt erhalten.
Schalter zeigen ihren bestätigten Zustand in allen Ansichten ausschließlich
am Haken; die zusätzliche Ein-/Aus-Zeile entfällt. Ihre `aria-describedby`-
Zuordnung verweist auf die weiterhin sichtbaren Status- und Fehlerhinweise.
Das Layout berechnet keine Ladeberechtigungen oder
Preisstrategien. Alle Entity-Suffixe,
Attribute, Sichtbarkeitsregeln und zugehörigen Tests stehen in der
[Funktionsmatrix](docs/vue-dashboard-parity.md) (`REQ-VUE-PARITY`).

Die Monatsauswahl in `TimedChargingView.vue` und `GridServingView.vue` zeigt
zunächst eine kompakte Zusammenfassung der bestätigten HA-Zustände. Nur
zusammenhängend ausgewählte Monate bilden eine Spanne, etwa „Januar,
März–Mai, Oktober“. Alle zwölf bestätigten Monate ergeben „Ganzjährig“
(EN: „All year“). „Keine Monate ausgewählt · Ganzjährig inaktiv“ erscheint
nur, wenn alle zwölf Zustände bekannt und aus sind. Fehlende, unbekannte und
nicht verfügbare Monate werden ausdrücklich
kenntlich gemacht. „Ändern“ öffnet vier Quartalsgruppen mit je drei unabhängig
bedienbaren Monaten; „Schließen“ klappt sie ohne Speicheraktion wieder zu.
Jede Änderung verwendet weiterhin einen einzelnen HA-Schalterservice.
Kontrollkästchen und Zusammenfassung folgen ausschließlich dem bestätigten
HA-Zustand, ohne zusätzliche Zeile „Bestätigter Wert“. Servicefehler,
ausstehende Aktionen, fehlende Verbindung und Einschränkungen bleiben auch
eingeklappt sichtbar. Die Bedienung und Zusammenfassung sind deutsch und
englisch übersetzt. Die gemeinsame bestätigte Zeitspanne in
beiden Zeitfenstern erhält in deutscher Sprache das Suffix ` Uhr`.
Unbekannte/nicht verfügbare Zustände, englische Werte, Eingabefelder und
Service-Payloads erhalten keinen Sprachzusatz. Der dynamische Tarif enthält
keine Monatsschalter.

`GeneralView.vue` ordnet nach den Skalen die Karten Leistung und Gerät an.
`Panel.ce.vue` stellt die CSS-Container `sax-panel` und `sax-content` bereit.
Die Ansichten wechseln ab 860 px Inhaltsbreite in ihr kompaktes Desktoplayout;
die HA-Seitenleiste zählt deshalb nicht als nutzbarer Kartenplatz. Normale
Schriftgrößen, mindestens 44 px hohe Bedienflächen und natürliche Kartenhöhen
bleiben erhalten. Die aufgeklappte Monatsauswahl zeigt auf dem Smartphone
eine Quartalsgruppe pro Zeile, bei ausreichendem Platz zwei nebeneinander.
Ihre Beschriftungen bleiben mindestens 14 px groß und die Bedienflächen
mindestens 44 × 44 px. Alle nativen Checkboxen im Dashboard sind einheitlich
22 × 22 px groß, einschließlich Speicher- und Ladehauptschaltern;
ein zugeordnetes Label stellt eine mindestens 44 × 44 px große Klickfläche
bereit, ohne die Tastaturbedienung oder die HA-Serviceaufrufe zu verändern.
DOM- und Tastaturreihenfolge bleiben Januar bis Dezember.
Die Gerätekarte beginnt mit `energy_charged`/`energy_discharged` und endet mit
`storage_switch`; es gibt keine separate Energie-Karte. Nur der
Speicherschalter verlangt vor beiden Zielzuständen eine Dialogbestätigung.
Abbrechen/Escape sowie Änderungen an Ausgangszustand, aufgelöster Entity-ID,
Bedienberechtigung oder Verbindung verwerfen die offene Auswahl ohne Service.
Eine gültige Bestätigung verwendet einmal den bestehenden HA-Schalterservice.
Die übrigen Schalter benötigen diesen zusätzlichen Dialog nicht.

`dashboard_api.py` registriert mit dem integrierten Panel den WebSocket-Befehl
`sax_power/dashboard/subscribe`. Er liefert für den angeforderten SAX-Config-Entry
die tatsächlichen Entity- und Device-IDs, Domains, stabilen Schlüssel,
übersetzten Namen und Enum-Texte sowie die Bedienberechtigung.
Registry-Änderungen aktualisieren das Abo, deaktivierte oder nicht lesbare
Entitäten fehlen. Die bestehende
HA-Verbindung übernimmt Anmeldung und Abmeldung; der Befehl liest keine
Geräteregister und stellt keine eigene Schreibschnittstelle bereit.

`frontend/src/ha.ts` verbindet diese Metadaten mit den reaktiven `hass.states`
und stellt einen gemeinsamen Kontext für alle fünf Ansichten bereit. HA
formatiert Zustände; fehlende, unbekannte und nicht verfügbare Werte erhalten
keine erfundenen Ersatzwerte. Verbindungswechsel melden Metadaten erneut an,
ohne Schreibaktionen zu wiederholen. `EntityValue.vue` zeigt bestätigte Werte;
`EntityControl.vue` bedient Schalter, Zahlen, Zeiten und Auswahlfelder über
`hass.callService`. Zahlen und Zeiten werden ausdrücklich übernommen.
Wertebereiche, Schritte und Auswahloptionen stammen aus den aktuellen
Entity-Attributen; HA bleibt für die Autorisierung der Services zuständig.
Alle Darstellungen einer Entität teilen ausstehende Aktionen und Fehler.
Ein erfolgreich beantworteter Serviceaufruf verändert den angezeigten Zustand
erst, wenn HA ihn tatsächlich meldet.

Der aktive Stromtarif folgt `economics_tariff_type`, unabhängig von den
Ladeschaltern. „Automatische Netzladung“ schaltet nur die passende Automatik;
Preiskurve und Wirtschaftlichkeit verwenden den ausgewählten Tarif auch bei
`off`. „Tarif wechseln“ bleibt bis „Tarif übernehmen“ ein lokaler Entwurf.
Die Navigation bleibt unverändert sichtbar; nur die alte Route
`dynamisches-laden` wird per `replaceState` nach `stromtarif` umgeleitet.
Der Tab Amortisation (EN: Amortization) behält den Pfad `ersparnis`.

Im dynamischen Tarif erklärt die Ladebedienung die Wirkung jeder Ladeweise
und zeigt nur deren relevante Eingaben. Die einfachen Bezeichnungen bilden
weiterhin `smart`, `relative`, `absolute` und `off` ab; Planung, Grenzwerte
und Services bleiben im Backend. Die Zusammenfassung verwendet bestätigte
Werte. Preisquellen-Sonderoptionen und die Speicherpause durch den Neutralpreis
bleiben in erweiterten Einstellungen erreichbar, ohne vorhandene Werte zu
überschreiben. Ladeziel und Preis-/Stundenregler verwenden weiterhin die
gemeinsamen HA-Entitäten.

Die Preisprüfung benennt das tatsächlich betroffene Feld: fehlender/gelöschter
Preissensor, nicht unterstützte Einheit, Einspeisevergütung, PV-Quelle,
PV-Anteil oder Preisattribut. Sie markiert und fokussiert das Feld, öffnet
bei Bedarf die erweiterten Einstellungen und erhält sämtliche Eingaben.
Eine fehlende Einspeisevergütung wird nicht durch einen erfundenen Wert ersetzt;
der Hinweis erklärt die bewusste Eingabe von 0 bei fehlender Vergütung.
`tests/test_epex_price_source.py` sichert EPEX `€/kWh` mit
`data[{start_time,end_time,price_per_kwh}]` sowie das ältere Cent-Format durch
WebSocket-Speicherung, Preisplan, Tageskurve und gemeinsamen Bewertungspreis ab,
auch bei negativen Preisen. Die bereits unterstützte Einheit wird nicht neu interpretiert.

Der Tarif-Zeitfenstereditor verwendet Textfelder mit sichtbarem Formathinweis
(24 Stunden, `12:30` oder mobil `1230`) statt segmentierter Browser-Zeitfelder.
Safari kann bei letzteren Platzhalter-Minuten anzeigen, obwohl der tatsächliche
Wert leer ist. Textfelder zeigen ausschließlich die eingegebenen Zeichen;
unvollständige Eingaben werden nicht ergänzt. Vollständige vierstellige Zeiten
werden bei `change` und beim Speichern in `HH:MM` überführt. Vorhandene Sekunden
bleiben erhalten. Beim Speichern liest der Editor die sichtbaren Werte und prüft
vollständige Zeiten und Überschneidungen. Ein Zeitfehler benennt Fenster und
Start-/Endfeld, markiert es mit `aria-invalid` und setzt den Fokus dorthin.
Die Browserabnahme prüft 00:00–04:59 und 12:30–15:30 per Tastatur während
HA-Zustandsupdates, unvollständige Stunden, vierstellige Eingabe, Fehlversuch mit
anschließender Wiederholung sowie getrennte change-/Submit-Übernahmen.
Sie läuft in Chromium und zusätzlich in WebKit auf macOS. Diese Prüfung ist
kein Nachweis für eine bestimmte Safari-Version auf einem anderen Gerät.

Reines Umschalten von „Automatische Netzladung“ wird als validierte
Softwareänderung unmittelbar bestätigt und zur Persistenz vorgemerkt.
Dieser Weg wartet nicht auf `_charge_control_lock`, verändert keine
Tarif-Options und startet keine Preisquelle neu. Der bestehende gemeinsame
Worker setzt den jeweils aktuellen Steuerstand unter dem Lock um;
Geräteaktivität wird weiterhin erst nach Gerätebestätigung gemeldet.
Auch tatsächliche Tarif-/Quellenwechsel werden ohne Geräte-Lock atomar angenommen.
Eine Quellenrevision sperrt alte Ladesollwerte; der gemeinsame Worker übernimmt
den sicheren Geräteübergang nach laufenden Quittierungssequenzen unter den
Geräte-Locks. Die Oberfläche markiert die ausstehende Schalterantwort sofort
und sperrt doppelte Aufrufe, ohne den bestätigten Zustand vorwegzunehmen.

Die Reaktionsprüfung umfasst alle Aktionswege, nicht nur sichtbare Schalter:

| Aktion | Rückmeldung und notwendige Wartezeit | Regressionstests |
| --- | --- | --- |
| Ladefreigaben, SOC-/Preis-/Stundenwerte, Strategie, Monate, Zeitfenster | Sofortige Softwarebestätigung; gemeinsamer Geräte-Worker | `tests/test_control_response.py`, `tests/test_month_switch_response.py`, `tests/test_vue_dashboard_e2e.py` |
| Automatische Netzladung im Tarifdashboard | Sofortige WebSocket-Antwort auch bei belegtem Geräte-Lock | `tests/test_dashboard_tariff_response.py` |
| Verbrauchsplanung und Preisplan aktualisieren | Sofortige Bestätigung; Geräteauswertung nachgelagert | `tests/test_bridge_switch.py`, `tests/test_control_response.py`, `tests/test_vue_dashboard_e2e.py` |
| Tarif-/Quellenwechsel und vollständige Profilübernahme | Sofortige Softwarebestätigung; Quellenrevision sperrt alte Ladesollwerte, Worker übernimmt den sicheren Geräteübergang | `tests/test_dashboard_tariff_transition_response.py`, `frontend/browser/dynamic-tariff.spec.ts` |
| Speicher Ein/Aus, manuelles Laden Start/Stop | Sofortiger ausstehender Zustand; Erfolg erst nach Gerätequittierung | `frontend/tests/controls.test.ts`, `tests/test_coordinator.py` |
| Bilanzneustart und Statistikabruf | Asynchrone lokale Speicherung bzw. Recorder-Lesen, kein Warten auf Geräte-Lock | `tests/test_economics_persistence.py`, `frontend/tests/savings.test.ts` |
| Navigation, Details, Abbrechen, Diagrammtag und Monatsübersicht | Lokale UI-Aktion; nachgeladene Preise zeigen Fortschritt, ältere Antworten werden verworfen | `frontend/tests/panel.test.ts`, `frontend/tests/electricity-tariff.test.ts` |

Die gemeinsamen Controls und Tarifeditoren testen verzögerte und fehlgeschlagene
Antworten, sofortige zugängliche Fortschrittsmeldungen, erhaltene Entwürfe und
gesperrte doppelte Schreibaufträge. Ein neuer Statistikzeitraum darf einen
laufenden Leseauftrag ersetzen; dessen verspätetes Ergebnis wird ignoriert.
Diese Prüfung ist für neue oder geänderte Aktionswege in `AGENTS.md` verbindlich.
Die Übergangstests halten zusätzlich beide Quittierungsphasen von Startsequenz
und periodischem Writer an. Sie prüfen echte Profil-/Sensoränderungen,
Rücksetzfehler mit erneutem Versuch und den Erhalt globaler SOC-Sperren.
Ein manueller Ladebefehl bewertet bei einem gleichzeitigen Quellenwechsel den
aktuellen Stand erneut, bevor er Erfolg nach Gerätebestätigung meldet.

`TimeWindowControl.vue` ersetzt in den Ansichten Zeitvariabler Tarif und
Netzdienliches Laden die getrennten Zeit-Bedienelemente. Es gibt genau zwei
Paare: `time.timed_charge_start`/`time.timed_charge_end` und
`time.grid_serving_start`/`time.grid_serving_end`. Das erste ist nur ohne
`TIME_OF_USE`-Tarif und ohne Verbrauchsplanung bearbeitbar; im Tarifmodus
gelten die Tarifpreisfenster nach `REQ-TIME-OF-USE-CHARGE-SOURCE`.
Eine 24-Stunden-Leiste mit
verschiebbaren Start-/Endmarken und Eingaben im Format HH:MM bearbeiten
dasselbe lokale Entwurfspaar. Eingaben verwenden `step=60`, Ziehen und
Tastatur ein Minutenraster bis 23:59. Vorhandene Sekunden lösen beim Laden
keine Änderung aus; bestätigte Spanne, Dauer und Fläche erhalten diese
Präzision bis zur ersten Bearbeitung. Nach ausdrücklicher Übernahme werden
beide Grenzen als HH:MM:00 gesendet. Ein Start nach dem Ende erzeugt zwei
markierte Abschnitte über Mitternacht; identische Grenzen ergeben ein leeres
Fenster. Die Darstellung berechnet keine Ladeberechtigung.

Eine gemeinsame Übernahme ruft über `ha.ts` genau einmal den vorhandenen
Service `sax_power.set_timed_charge_window` beziehungsweise
`sax_power.set_grid_serving_window` mit `device_id`, `start` und `end` auf.
Beide aufgelösten Time-Entitäten müssen bedienbar sein und zum selben Gerät
gehören. Auch die Services prüfen bei Benutzeraufrufen die Rechte für beide
Time-Entitäten. Der gemeinsame Kontext sperrt während des Aufrufs beide
Grenzen und teilt Fehler auch mit anderen Darstellungen dieser Entitäten.
Die bestehende Backend-Prüfung betrachtet das fertige Zielpaar atomar;
bei Überschneidung leert sie beide Grenzen und erzeugt die vorhandene
HA-Benachrichtigung. Es gibt keine zwei aufeinanderfolgenden `time.set_value`-
Aufrufe und keine neue Geräte-Schreibschnittstelle.

Die Bestätigungszeile zeigt ausschließlich HA-Zustände. Eine Serviceantwort
bestätigt noch keine neue Zeitspanne. Eine echte Änderung einer HA-Zeitgrenze
setzt das gesamte Entwurfspaar auf den aktuellen HA-Stand; andere
Telemetrieänderungen erhalten den Entwurf. Ungültige Eingaben, fehlende
Berechtigungen und Nichtverfügbarkeit sperren die Übernahme; Fehler führen
zu keiner automatischen Wiederholung. Bei nur einer verfügbaren Grenze bleibt
diese in der Bestätigungszeile sichtbar. Geleerte oder unbekannte Zeitwerte
lassen sich weiterhin über die nativen HA-Time-Entitäten korrigieren.
Maus-, Touch- und Tastaturbedienung
verwenden denselben Entwurf. Beide Fenster unterstützen DE/EN, helle und
dunkle HA-Themes sowie mobile Ansichten und zeigen auf Deutsch den
Uhr-Zusatz nur an der bestätigten Zeitspanne.

Die geplanten Zeiten im dynamischen Tarif bleiben reine Anzeigen. Die
Tarifpreisfenster unter Zeitvariabler Tarif und Amortisation besitzen den
gemeinsamen ausklappbaren Editor nach REQ-VUE-TARIFF-EDITOR. Die
Recorder-Datumsfilter bleiben Datumseingaben; die separate Controls-Vorschau
ist keine produktive Ansicht.

`dashboard_statistics.py` ergänzt den ausschließlich lesenden WebSocket-Befehl
`sax_power/dashboard/statistics`. Die Anfrage enthält `entry_id`, optional das
gemeinsame Paar `start_date`/`end_date` im Format `YYYY-MM-DD` sowie
`first_weekday` (`mon` bis `sun`, HA-Benutzereinstellung). Der Adapter löst nur
die `economics_net_savings`-Entität dieses Eintrags auf und prüft deren
Leseberechtigung vor der Datenbankabfrage und erneut vor der Antwort. Fehlende
Entität und fehlender Recorder werden ausdrücklich gemeldet. Recorder bleibt
optional; SQL-Abhängigkeiten und Abfragen laufen erst mit einer vorhandenen
Recorder-Instanz in deren Executor.

Die Kalenderwerte verwenden die nativen HA-Funktionen `resolve_period` und
`statistic_during_period(..., {"change"}, ...)`. Freie Zeiträume beginnen um
Mitternacht des gewählten Anfangstags und enden exklusiv um Mitternacht nach
dem Endtag in der HA-Zeitzone. Für den Graphen bleibt die native
Energy-Endgrenze `23:59:59.999` erhalten. Stunden-/Tages-/Monatsauflösung verwendet
die Heuristik von `getSuggestedPeriod` des gepinnten HA-Frontends, angewendet
auf die gewählten Kalendertage in der konfigurierten HA-Zeitzone. Das native
Frontend kann hierfür die Browser-Zeitzone heranziehen; bei davon abweichender
Browser-Zeitzone wird keine identische Auflösungswahl behauptet. Der Zeitraumwert
wird separat mit `statistic_during_period` gelesen und nicht aus
Diagrammbalken summiert. Er kann bereits eine neuere Fünf-Minuten-Randperiode
enthalten, während der native stündliche Graph diese noch nicht enthält.
`tests/test_dashboard_statistics.py` vergleicht Wert und Balken direkt mit
derselben echten Recorder-Datenbasis, einschließlich 23-/25-Stunden-Tagen,
signierten Änderungen und einem `last_reset`-Bilanzneustart.

`frontend/src/savings.ts` fragt diese Ergebnisse über `hass.callWS` ab.
`recorder_5min_statistics_generated`, Reconnect und die explizite
Aktualisieren-Schaltfläche lösen eine neue Abfrage aus; es gibt kein weiteres
Polling der Batterie. Ein Generationszähler verwirft Antworten einer alten
Auswahl, eines früheren Eintrags oder einer beendeten Verbindung. Datumseingaben
bleiben Entwürfe bis zum Absenden. Geld wird erst zur Anzeige auf zwei,
Tarifpreise in ct/kWh auf zwei Nachkommastellen formatiert; der Vorlaufbetrag beeinflusst
keine Statistik. Fehlende Historie wird nicht durch Live-Sensorwerte ersetzt.

Das Dashboard ist integraler Bestandteil der Integration. Setup und
Options-Listener registrieren das Panel idempotent, ohne Auswahl im Config-
oder Options Flow. Alte Werte von `vue_dashboard_enabled` beeinflussen die
Verfügbarkeit nicht mehr. Deaktivierung der Integration und Unload entfernen
das eigene Panel. Frontendfehler blockieren die Batterieintegration nicht.

Der Lovelace-Builder, dessen Anlageoption, Create-/Reinstall-Services,
Veraltet-Reparatur und Lovelace-Abhängigkeit sind entfernt. Die Migration
bereinigt `create_dashboard`, `dashboard_update_dismissed` und
`vue_dashboard_enabled` in `entry.data`
und `entry.options` sowie `dashboard_outdated_<entry_id>` in der Issue Registry.
Sie schreibt weder in den Lovelace-Storage noch löscht sie gespeicherte
Dashboards oder Karten. Frühere Dashboard-Abwahlen entfallen. Die aktive
Implementierung benötigt keine Lovelace-Konfiguration oder parallelen
Dashboard-Einstieg.

`REQ-VUE-DASHBOARD-REPAIR` ergänzt einen eigenen Reparaturablauf für Vue.
Der SHA-256-Hash des lokalen Bundles identifiziert den Stand auch zwischen
Snapshots mit derselben Manifest-Version. `vue_dashboard_version` hält den
bestätigten Stand; `vue_dashboard_dismissed_version` unterdrückt nur den
konkret abgelehnten Hinweis. Neue Aktivierungen beginnen mit einer Baseline;
bereits aktivierte ältere Dashboardstände ohne Marker erhalten einen neutralen
einmaligen Hinweis zum Neuladen. Ein Fehler bei der Registrierung kann auch
für einen schon bestätigten Bundle-Stand eine Reparatur auslösen.

Der Vue-Reparaturflow registriert ausschließlich das eigene Panel mit der
aktuellen Hash-URL erneut. Da ein bereits definiertes Custom Element im
Browser nicht durch erneuten Modulimport ersetzt wird, enthält der Dialog
einen ausdrücklichen Schritt zum Neuladen der HA-Seite. Fehlgeschlagene oder
inzwischen überholte Reparaturen quittieren keinen neueren Stand. Die Marker
liegen in `entry.data`; Änderungen daran bleiben über den bestehenden
Options-Listener ohne zusätzliche Ladesteuerungsaktion.

Das JavaScript-Bundle liegt unter
`custom_components/sax_power/frontend/sax-power-vue.js` im Git-Repository.
Vue und die Shadow-DOM-Styles sind darin enthalten; zur Laufzeit gibt es
keinen Node-Prozess und keine CDN-Abhängigkeit. Die statische Route wird
pro HA-Lauf einmal registriert und bleibt beim Panel-Unload bestehen, da
Home Assistant keine Abmeldung statischer Routen anbietet. Ein Hash der
Asset-Datei in der Modul-URL vermeidet veraltete Browser-Caches nach Updates.

Für die Frontend-Entwicklung wird zusätzlich Node.js 22 ab 22.22.2 benötigt
(CI: Node 22); alternativ Node 24 ab 24.15 oder Node 26 und neuer, entsprechend
`frontend/package.json`. Frontend-Prüfungen laufen aus dem Verzeichnis `frontend/`:

```sh
npm ci
npm run check
npm test
npm run build
npx playwright install chromium
npm run test:browser
```

Nach Quellenänderungen das neu gebaute Bundle mit einchecken. CI baut aus dem
Lockfile erneut und vergleicht die ausgelieferten Assets mit dem Git-Stand.
HACS erhält diese Dateien aus dem getaggten Integrationsverzeichnis; das
vorhandene Snapshot-Packprogramm übernimmt dieselben Bytes. Der privilegierte
Snapshot-Workflow führt weiterhin keinen Frontend-Build aus PR-Code aus.
`tests/test_frontend_package.py` prüft Source- und Snapshot-Paketierung,
`tests/test_vue_dashboard.py` den Panel-Lebenszyklus und
`tests/test_config_flow.py` das Entfallen der Dashboard-Auswahl; `tests/test_init.py`
prüft die Bereinigung alter Metadaten ohne Änderung gespeicherter Dashboards.
`tests/test_dashboard_api.py` prüft das echte WebSocket-Protokoll einschließlich
Berechtigungen und Registry-Änderungen. Die Frontend-Tests decken Live-Zustände,
Bedienvalidierung, ausstehende Aktionen und den Abo-Lebenszyklus ab.
`tests/test_vue_dashboard_e2e.py` startet die Integration mit einem lokalen
Modbus-TCP-Simulator und zwei echten HA-WebSocket-Clients: Änderungen über
Dashboard und reguläre HA-Services sind gegenseitig sichtbar und verursachen
weder einen zweiten Modbus-Client noch zusätzliche Geräteabfragen durch das
Öffnen der Oberfläche. Die genaue Abgrenzung zu Browser- und Hardwareprüfungen
steht in der Funktionsmatrix. `tests/test_vue_dashboard_restart.py` ergänzt zwei getrennte
HA-Läufe mit tatsächlich über HA-Storage gespeicherten Optionen und Bundle-Hash.

Ein heruntergeladenes Stable-Quellarchiv oder Snapshot-ZIP kann aus dem
Repository-Root mit der vorhandenen Python-Testumgebung geprüft werden:

```sh
.venv/bin/python -I scripts/verify_dashboard_package.py /tmp/sax-power-paket.zip
```

Der Helper installiert ausschließlich das Integrationsverzeichnis in einem
neuen temporären Baum. Ein separater `python -I -m pytest`-Prozess ohne
Repository-Konfiguration prüft die Herkunft aller importierten SAX-Module,
Manifest, Lizenz und Übersetzungen sowie die echte lokale HA-HTTP-Route gegen
den SHA-256-Hash der Paketdatei. Der native Reparaturmanager registriert dort
auch einen simulierten Bundlewechsel; die neue URL muss die neuen Bytes
liefern. Der Worker startet keinen Coordinator, verwendet keine Batterie und
benötigt weder Node noch einen Build. Er setzt die Abhängigkeiten aus
`requirements_test.txt` auf dem Testrechner voraus. Das JSON-Ergebnis benennt
Paketversion, ZIP-Hash, Asset-Hash und Dateianzahl. Die Browserausführung des
JavaScripts wird zusätzlich durch Komponenten-, Produktionsmodul- und
Browsertests geprüft.

Für eine lokale Bedienprobe ohne Batterie `npm run dev -- --host 127.0.0.1`
starten und `/controls-preview.html` öffnen. Die ausdrücklich als Demo markierte
Seite verwendet simulierte HA-Zustände und Serviceantworten; sie ist kein
zusätzlicher produktiver Dashboard-Bereich.

`/general-preview.html` verwendet dieselbe allgemeine Ansicht mit simulierten
HA-Entitäten für die visuelle Prüfung. Produktive Views lesen ausschließlich
den gemeinsamen Kontext; Demowerte werden nicht in das ausgelieferte Panel
übernommen.

`/charging-preview.html` enthält alle drei Ladeansichten samt DE/EN,
Themewechsel, nicht verfügbarer Prognose und simuliertem Schreibfehler.
`/savings-preview.html` stellt die Ersparnisansicht mit simulierten
HA-/Recorder-Antworten bereit. Diese Entwicklungsvorschauen werden nicht ins
Integrationspaket übernommen. Die unterstützte und lokal geprüfte HA-Basis ist
**2026.8.2** mit **home-assistant-frontend 20260729.7**; CI installiert dieselben
Pins aus `requirements_test.txt`, HACS verwendet denselben Mindeststand.

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
`async_step_user` verzweigt bei Erfolg zusätzlich in zwei weitere
Schritte, bevor der Eintrag angelegt wird - `async_step_reconfigure`
überspringt sie alle: `async_step_grid_charge` (Vorbelegung für das
zeitgesteuerte Laden, siehe `STEP_GRID_CHARGE_SCHEMA`) und
`async_step_finish` – eine reine
Zusammenfassungsseite ohne eigene Eingabefelder (Firmware, Seriennummer,
SunSpec-Erreichbarkeit, Anzahl angelegter Entities als
`description_placeholders`, per Testread über `_async_read_finish_summary`
ermittelt), siehe anforderung.yaml REQ-SETUP-FINISH-SUMMARY. Der Config Entry
wird erst hier angelegt.

Die Integration unterstützt derzeit einen Speicher pro Installation von
Home Assistant (REQ-IP-CONFIGURABLE-UI). Deshalb prüfen alle Schritte der
Ersteinrichtung auf eingerichtete Config Entries und brechen mit
`single_instance_allowed` ab, auch wenn ein parallel gestarteter Flow seinen
Eintrag zwischenzeitlich angelegt hat. Ignorierte Discovery-Merker zählen
dabei nicht als Speicher; deaktivierte oder fehlerhaft geladene Einträge
zählen weiterhin. Der Hinweis verweist für
Verbindungsänderungen auf **Neu konfigurieren**. Reconfigure und Options
bleiben nutzbar; bereits gespeicherte Mehrfacheinträge werden nicht verändert.
Die Begrenzung passt zum globalen Dashboard unter `sax-power`, das keine
getrennten Dashboards je Speicher bereitstellt.

Ein durch DHCP entdeckter Speicher verwendet seine normierte MAC-Adresse
dauerhaft als `unique_id` des Config Entry. Ein späterer Lease derselben MAC kann
dadurch die geänderte IP im vorhandenen Eintrag nachführen und einen Reload
auslösen, ohne einen zweiten Eintrag anzulegen. Beim Reconfigure bleibt diese
MAC-ID erhalten; nur manuell angelegte Einträge führen ihre `host:port`-ID mit.
DHCP prüft bekannte Hosts und MAC-Adressen vor der Einrichtungsbegrenzung,
damit solche IP-Updates weiterhin möglich sind. Aus demselben Grund setzt das
Manifest nicht `single_config_entry`: Home Assistant würde sonst weitere
Discovery-Flows bereits vor diesem Abgleich blockieren. Die eigene Prüfung
im Config Flow verhindert dagegen nur zusätzliche Einträge.

Zusätzlich gibt es einen Options Flow (`SaxPowerOptionsFlow`) für das
preisoptimierte Laden. Dort stehen nur die Dinge, die sich nicht sinnvoll als
Entity abbilden lassen (Auswahl der Quell-Sensoren und deren Interpretation);
die im Alltag veränderlichen Stellgrößen sind echte Entities am SAX-Gerät.
Eine Änderung wendet `async_update_options` über
`coordinator.async_apply_tariff_options` auf den laufenden Coordinator an.
Tarifquelle und exklusive Automatik wechseln unter `_charge_control_lock`;
Planner und Tarifprovider werden idempotent aktualisiert, der gemeinsame
Control-Worker übernimmt den Geräteabgleich. Ein Config-Entry-Reload hätte über `SaxPowerCoordinator.async_shutdown`/`async_stop_sun_charge`
ein gerade aktiv gehaltenes netzdienliches Laden (Register 40051 zurück auf
SmartMeter-Nullregelung) unterbrochen und einen kurzen, ungewollten
Ladevorgang ausgelöst, bis die neu erzeugte Instanz die
`PV_SURPLUS_HYSTERESIS_CYCLES`-Bestätigung erneut durchlaufen hätte -
ursprünglich gemeldeter Bug, siehe `anforderung.yaml`,
REQ-DYNAMIC-PRICE-CHARGE.

Derselbe Options Flow wählt das Tarifmodell der Wirtschaftlichkeitsauswertung
(REQ-ECONOMICS-TARIFFS). Die Tarifart steht als `economics_tariff_type` auf der
ersten Seite; Festpreis und dynamischer Tarif haben die Folgeschritte
`economics_fixed` und `economics_dynamic` mit Preiseingaben in ct/kWh.
`disabled` und `time_of_use` speichern sofort. Standardpreis, Einspeisevergütung
und Zeitfenster des tageszeitabhängigen Tarifs werden ausschließlich im
Dashboard bearbeitet (REQ-VUE-TARIFF-EDITOR). Das Dashboard steht ohne
zusätzliche Aktivierung bereit (REQ-VUE-DASHBOARD); eine frühere Abwahl
blockiert die Tarifauswahl nicht. Bleibt die Tarifart gleich,
übernimmt der Flow das aktuell gespeicherte TOU-Profil; bei erstmaliger
Auswahl bleiben fehlende Pflichtpreise unbekannt, bis der Anwender das Profil
im Dashboard vervollständigt. Inaktive Profile bleiben unter
`dashboard_tariff_profiles` erhalten; die flachen aktiven Options bleiben
verbindlich. Auch ein späterer Optionsflow erhält die Profile und kann ein
bereits gespeichertes TOU-Profil wiederherstellen.

Der dynamische Dashboard-Editor prüft den PV-Anteil vor dem WebSocket-Aufruf
auf ganze Prozentwerte zwischen 0 und 100 und erhält ungültige Entwürfe mit
einer konkreten Fehlermeldung. `price_planner.has_unsupported_price_unit`
meldet fremde Preiseinheiten an die Selbstdiagnose. Bei aktiver Planung ohne
Preisdaten entsteht sofort `price_unit_unsupported`; der allgemeine Hinweis
nach sechs Stunden wird für diesen Fehler unterdrückt. Die Einheitenkorrektur
ersetzt keine Währungsumrechnung.

Die persistierten Schlüssel
und die acht verschachtelten Fenster-Mappings in `entry.options` bleiben in EUR/kWh,
damit bestehende Konfigurationen und die interne Bilanz unverändert weiterlaufen.

`TariffPlan.vue` stellt diese Preisfenster in `TimedChargingView.vue` und
`SavingsView.vue` unter „Dein Stromtarif“ (EN: „Your electricity tariff“) dar.
Im gemeinsamen Stromtarif ist sie Schritt 1 „Wann ist dein Strom günstig?“.
Die kompakte Ansicht zeigt gespeicherte tägliche Preiszeiten; günstige Fenster
und gültige Standardpreislücken werden nur aus übereinstimmenden Backenddaten
markiert. Ein Profil-/Telemetrievergleich über den bestehenden Fingerprint
verhindert alte Niedertarifmarkierungen direkt nach dem Speichern. Sonst bleiben
aktueller Preis und günstigste Zeit sichtbar; die ganze Tabelle und die
Preisregeln stehen in nativen Details-Elementen.
Die reaktive Quelle für Tarifstatus und Preisbewertung ist in beiden Ansichten der vorhandene
Sensor `economics_current_import_price` mit `tariff_type`, `windows`,
`active_window`, `base_price_eur_kwh`, `feed_in_price_eur_kwh`,
`next_price_change_at` und `unavailable_reason`. Die Karte erscheint nur bei
`time_of_use` und übernimmt alle bis zu acht Fenster in der vom Sensor
gelieferten Planreihenfolge, einschließlich Mitternacht und angrenzender
Zeitgrenzen. Der Sensor sortiert den Plan nach Startzeit; die Eingabegruppen
in den Options bleiben dabei unverändert.
Die gemeinsame Komponente erhält HA-Änderungen ohne Dashboard-Neubau; sie
formatiert Preise in ct/kWh mit zwei Nachkommastellen und berechnet weder
Tarifpreise noch aktive Fenster. Auch ohne Preisfenster bleiben vorhandene Standardpreis- und
Tarifinformationen sichtbar. Ein fehlender Preis wird nicht als aktiver
Standardpreis markiert. Bei `TIME_OF_USE` entfällt die separate Karte
„Netzladezeitfenster“ (EN: „Grid charging window“); nur bei anderen Tarifarten
ohne Verbrauchsplanung bedient sie `timed_charge_start` und `timed_charge_end`.
„Bearbeiten“ öffnet Standardpreis, vorhandene Fenster und Einspeisevergütung
in derselben Karte. Nur „Speichern“ schreibt das vollständige Profil;
„Abbrechen“ verwirft den lokalen Entwurf. Die kompakte Übersicht und
einklappbare Erläuterungen halten den Platzbedarf nach dem Speichern gering.
`dashboard_tariff.py` stellt dafür die authentifizierten WebSocket-Befehle
`sax_power/dashboard/tariff/get` und `sax_power/dashboard/tariff/save` bereit.
Fehlen Preis-Entity oder Tarifattribute, lädt die Karte das Profil einmalig
über die API. Ein bestätigter TOU-Tarif bleibt damit auch ohne gültigen
Preissensor bearbeitbar; der gemeinsame Kontext unterdrückt zugleich die
hier unwirksamen separaten Netzladezeiten. Ein Anlagenwechsel remountet die
Ansicht und verwirft Entwürfe der vorherigen Anlage; verspätete Antworten
werden über die Generation der Verbindung und des Eintrags verworfen.
Die Schreibseite verlangt einen aktiven Administrator, einen SAX-Eintrag
mit TOU-Tarif und die beim Laden erhaltene Revision. Eine veraltete Revision
wird als Konflikt abgelehnt. Die Validierung prüft das vollständige Profil
einschließlich Wertebereichen, endlichen Preisen und zyklischen Überlappungen;
die Options werden atomar aktualisiert und über `async_update_options` live
angewendet. Die API verwendet ausdrücklich `*_ct_kwh`, während gespeicherte
Options und bestehende Sensorattribute `*_eur_kwh` in Euro bleiben.

Der gemeinsame Tab `ElectricityTariffView.vue` ergänzt diese Fallback-Karte
um die kompakte Ansicht „Tarif & Preise“. Zeitvariabler und dynamischer Tarif
verwenden dieselbe `TariffPriceChart.vue`: vollständiger heutiger Preistag,
beim dynamischen Tarif zusätzlich morgen, aktuelle Preisangabe und Ladezustand.
UTC-Intervallgrenzen erhalten 23-/25-Stunden-Tage; negative Preise liegen unter
der Nulllinie, fehlende oder widersprüchliche Preise bleiben Lücken. Antippen,
Pfeiltasten und eine aufklappbare Tabelle erschließen die einzelnen Werte.
Die Kurve zeigt die Preisquelle, nicht nur ausgewählte Ladezeiten. Eine Quelle
mit ausschließlich aktuellem Sensorzustand liefert keine erfundene Tageskurve.

`tariff/get` liefert neben den bisherigen TOU-Feldern beide Profile,
`can_configure` und `automation_enabled`. `tariff/configure` übernimmt
`entry_id`, `revision`, die Ziel-`tariff_type`, optional ein vollständiges
`profile` und optional `automation_enabled`. Ohne Profil wird das gespeicherte
Zielprofil aktiviert; fehlende Pflichtdaten verhindern eine Netzladefreigabe.
`async_apply_dashboard_tariff` prüft die aktuellen Options und übernimmt Options
und passende Freigabe gemeinsam ohne asynchrone Unterbrechung oder Geräte-Lock.
Bei einem Quellenwechsel verhindert eine Revision alte negative Sollwerte.
Der gemeinsame Worker wartet eine laufende Modbussequenz unter dem Schreib-Lock
ab und beendet danach alte periodische Writer. Eine inzwischen veraltete
Start-/Schreibsequenz setzt kontrolliert zurück; Rücksetzfehler bleiben bis zum
erfolgreichen erneuten Versuch vorgemerkt. Der ausgeschaltete Hauptschalter erhält
den Tarif; beim Start wird eine widersprüchliche alte Automatik ausgeschaltet.
Reine Profilarchive lösen keine Quellenrevision aus. Schreibzugriff erfordert
einen aktiven Administrator; Revisionskonflikte erhalten den lokalen Entwurf.
Die API-Bestätigung beschreibt angenommene Konfiguration, Geräteaktivität folgt
weiterhin erst auf die quittierte Steuersequenz.

`bridge_configuration_error` prüft die fertig projizierten aktiven Options:
Eine eingeschaltete verbrauchsbasierte Ladeplanung erfordert weiterhin ihre
PV-Quelle und `time_of_use` (Issue #244). `tariff/configure` prüft das auch beim
Wiederherstellen eines archivierten Profils ohne explizites `profile`; der
Coordinator wiederholt die Prüfung unmittelbar vor jeder atomaren Softwareänderung.
Eine fehlende Quelle liefert `bridge_pv_start_required`, auch wenn die
automatische Netzladung aus ist. Der Dashboardeditor erklärt die Voraussetzung
und erhält den Entwurf. Erst nach bewusstem Abschalten der Ladeplanung darf
ihre Quelle entfernt werden. Ein konfigurierter, vorübergehend unverfügbarer
Sensor bleibt zulässig; beim dynamischen Tarif bleibt die PV-Quelle optional.

`tariff/series` nimmt `entry_id` und `day` (`today`/`tomorrow`) an. Die Antwort
enthält `date`, `time_zone`, `start`, `end`, `now`, `current_price_ct_kwh`,
`slots` mit Start/Ende/Preis, `gaps`, `status`, `reason` und `revision`.
Lesende Benutzer benötigen auch Zugriff auf die dynamische Preisquelle.
`ha.ts` teilt Profilabfragen und verwirft Antworten alter Einträge/Verbindungen;
der Tab aktualisiert bei Quellen-/Tarifänderung und alle 60 Sekunden nur die
Dashboard-Daten, ohne zusätzliche Modbus-Abfrage.

„Tarif & Preise“ bearbeitet beim zeitvariablen Tarif Standardpreis,
Einspeisevergütung, bis zu acht Fenster und die PV-Start-Prognosequelle. Beim
dynamischen Tarif bleiben Preisquelle, optionales Attribut, Quelleneinheit
(`auto`, `eur_kwh`, `ct_kwh`, `eur_mwh`, `ct_mwh`), Einspeisevergütung sowie
Smart-PV-Sensor und anrechenbarer PV-Anteil erhalten. Beide Profile speichern
getrennte PV-Quellen. Preiseingaben erfolgen in ct/kWh; die Quelleneinheit dient
nur der Umrechnung und ergänzt keine Steuern oder Zuschläge.
Im zeitvariablen Tarif ordnet `ElectricityTariffView.vue` die Bedienung als
„1. Wann ist dein Strom günstig?“, „2. Wie viel möchtest du laden?“ und
„3. Automatik einschalten“. Der Hauptschalter verwendet weiterhin denselben
`tariff/configure`-Aufruf. Aktueller Preis und Entladestatus bleiben sichtbar;
die Tageskurve ist nachgeordnet unter „Preisverlauf anzeigen“ erreichbar.
`TimeOfUseChargingSettings.vue` zeigt bestätigte Ladeweise, Ladeziel,
Startschwelle und Monatsauswahl. Die zwei beschriebenen Auswahlflächen bilden
nur `switch.bridge_charge_enabled` auf festes Ziel beziehungsweise Bedarf bis
Solarstrom ab. Sie setzen keine Standardwerte und aktivieren keine Netzladung.
Unbekannte Zustände markieren keine Auswahl. Globale Ladegrenze, Startschwelle
(nur bei fester Ladeweise) und MonthSelection stehen unter „Weitere Einstellungen“.
Zahlen verwenden weiterhin `EntityControl`; dessen Entwürfe bleiben durch
`v-show` beim Einklappen erhalten. „Fertig“ klappt nur zu. Fehler und Pending
bleiben auch bei geschlossenem Editor sichtbar. Die spezielle HA-Service-
Fehlerübersetzung in `ha.ts` berücksichtigt nur passende SAX-Fehlerschlüssel
für den Verbrauchsplanungsschalter. Komponenten- und Browsertests stehen in
`time-of-use-charging.test.ts` und `time-of-use-usability.spec.ts`.
Globaler Max-SOC und zeitvariables Ladeziel bleiben unterschiedliche Grenzen.
Ein sichtbarer Hinweis erklärt die bestehende Kalibrierungsausnahme bis 100 %;
die feste Ladeweise erläutert zusätzlich ihre Entladesperre bis Fensterende.
Dynamisch erscheint die absolute Preisgrenze nur bei `absolute`, das
Stundenbudget bei `relative`/`smart`; der Neutralpreis bleibt verfügbar und
wirkt in diesen aktiven Strategien. Smart verwendet das Stundenbudget als
Obergrenze seines festen 24-Stunden-Planungszyklus. „Ladeplan & Prognose“ zeigt
weiterhin ausschließlich Backend-Ergebnisse.

Die drei aktuellen Preis-Sensoren veröffentlichen ihre Zustände in ct/kWh.
Preisgrenze und Neutralpreis wandeln native Centwerte beim Lesen und Schreiben
an der Entity-Grenze um; der Steuerungs-Store bleibt in EUR/kWh. Der einmalige
Restore-Pfad unterscheidet alte Euro- und neue Centzustände anhand der Einheit.
`infrastructure/price_statistics.py` migriert bestehende Kurz- und
Langzeitstatistiken dieser drei Sensoren auf ct/kWh. Ein `RecorderTask` skaliert
Werte mit Faktor 100 und ändert die Metadaten in derselben Transaktion;
die alte Einheit ist zugleich der Schutz vor doppelter Migration. Die
Registry-Auflösung berücksichtigt umbenannte Entities und deren Config Entry.
Diese gezielte Migration ist nötig, weil HA keinen Tarifpreis-UnitConverter
für EUR/kWh und ct/kWh besitzt. Rohzustände behalten ihre historische Einheit;
ein gemischtes Übergangsintervall kann bei der Statistikbildung entfallen.
Das Backend verwendet den gespeicherten Tarif sowohl für feste SOC-Ladung
als auch für `REQ-BRIDGE-CHARGE` als alleinige Quelle erlaubter Ladezeiten
(siehe `REQ-TIME-OF-USE-CHARGE-SOURCE`).

Der **Strompreis-Sensor** (`price_sensor`, erste Seite) hat zwei getrennte
Aufgaben, die sich leicht verwechseln lassen:

| Tarifmodell | Preisquelle der Wirtschaftlichkeit | Strompreis-Sensor |
|---|---|---|
| `disabled` | keine | nur preisoptimiertes Laden |
| `fixed` | ein fester Arbeitspreis aus dem Options Flow | nur preisoptimiertes Laden |
| `time_of_use` | Standardpreis + bis zu acht Zeitfenster aus dem Dashboard | inaktives dynamisches Profil; keine parallele Preisautomatik |
| `dynamic` | der Strompreis-Sensor | Pflichtfeld |

Für das preisoptimierte Laden ist der Sensor immer die Quelle. Bei
`time_of_use` kann dieser Ladepfad nicht parallel aktiviert werden. Für die
Wirtschaftlichkeit ist er es nur beim dynamischen Tarif.
Beim tageszeitabhängigen Tarif ist er ausdrücklich unbrauchbar: Ein
dynamischer Preis-Sensor liefert eine Zeitreihe für die nächsten Stunden, das
Tarifmodell dagegen ein täglich wiederkehrendes Profil - die beiden Formate
lassen sich nicht ineinander überführen. Weil beide Felder auf derselben Seite
untereinanderstehen, sagen die `data_description`-Texte in `strings.json` das
ausdrücklich (Anwenderbericht zu #135/#137).

Explizit zeitgestempelte Preis-Slots werden für Identität, Sortierung,
Dauer, Überlappung, Horizont und Auswahl ausschließlich als UTC-Instants
verglichen. Die lokale Zeitzone bleibt Darstellung; dadurch bleiben die
beiden realen 02-Uhr-Slots der herbstlichen Zeitumstellung getrennt. Naive
Anbieter-Zeitstempel werden weiterhin als lokale Home-Assistant-Zeit
interpretiert (Issue #149).

Numerische Preisarrays für `today`/`tomorrow` werden zwischen zwei lokalen
Mitternachten über die reale UTC-Tagesdauer verteilt. Dadurch behalten auch
23/25-Stunden- und 92/100-Viertelstundenlisten an Zeitumstellungstagen ihre
Tarifintervalle. Jede Slotgrenze wird direkt aus Tagesdauer und Index
berechnet; bei anderen Arraylängen verschiebt kumulierte Rundung deshalb
nicht die letzte Grenze über Mitternacht hinaus (Issue #105). Relative Listen
werden am lokalen `state.last_updated` verankert: alte heutige Preise wandern
nach Mitternacht nicht auf den Folgetag. Unverfügbare Quellen, fremde Einheiten
und nicht endliche Preise erzeugen keine gültigen Slots. Widersprüchliche
Überlappungen bleiben in der Preisquelle erkennbar und werden für die
Ladeauswahl ausgespart; identische Wiederholungen werden entdoppelt.

Kein Formularschema darf einen Validator enthalten, den
`voluptuous_serialize` nicht für das Frontend übersetzen kann - eine
gewöhnliche Python-Funktion in einem `vol.All` gehört dazu. Der Fehler fliegt
erst *nach* dem Flow-Schritt in der Websocket-Schicht, der Dialog zeigt
deshalb nur „Unknown error occurred", und der Schritt ist überhaupt nicht
erreichbar (#135). Die Preisfelder sind deshalb nackte `NumberSelector` (die
prüfen den Wertebereich selbst). Eingaben in ct/kWh werden beim Speichern
in EUR/kWh umgerechnet; die Rundung auf 0,0001 EUR/kWh erfolgt
im Schritt (`_round_price_fields`). `tests/test_config_flow.py` führt die
Serialisierung für jeden Schritt beider Flows und für jedes Modulschema aus;
die übrigen Tests rufen den Flow über die Python-API auf und überspringen
diese Schicht.

Die Preisfelder der Folgeseiten sind im Schema `vol.Optional` und werden
erst im Schritt selbst geprüft (`_missing_prices` → Feldfehler
`economics_price_required`): Ein `vol.Required` scheitert schon in der
Schema-Validierung von Home Assistant, also *vor* dem Schritt, und zeigt die
unübersetzte Rohmeldung `required key not provided`. Pflicht bleiben die
Preise dadurch unverändert. Aus demselben Grund lassen die Folgeseiten
fremde Schlüssel zu (`vol.ALLOW_EXTRA`) und behandeln eine erneut
abgeschickte erste Seite als Wiederholung genau dieser Seite
(`_async_repeat_init`) - schickt das Frontend die erste Seite zweimal ab
(Doppelklick, oder Enter im Eingabefeld plus Klick auf „Absenden"), prüft
Home Assistant deren Werte gegen das Schema der bereits erreichten
Folgeseite, was sonst als Wand aus `extra keys not allowed @ data[...]` im
Dialog landet. Die wiederholte erste Seite prüft `_async_repeat_init` dabei
selbst gegen `STEP_OPTIONS_SCHEMA` (auf diesem Weg wendet Home Assistant es
nicht mehr an); was nicht passt, gilt als unvollständige Eingabe der
Folgeseite. `add_suggested_values_to_schema` baut das Schema neu auf und
verliert dabei `extra`; `_suggested` setzt es deshalb wieder.

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

### Entladeprognose (REQ-DISCHARGE-FORECAST)

Die unabhängige Entladeprognose (`REQ-DISCHARGE-FORECAST`) liegt in
`domain/discharge_forecast.py`. Der Coordinator übergibt pro neuer, frischer
HIGH-Messung Speicherleistung, Kapazität, SunSpec-SOC und Geräte-Minimal-SOC.
Die Domain hält höchstens 60 Minuten Verlauf, integriert die positive Leistung
zeitgewichtet mit dem jeweils vorherigen Messwert und liefert nach mindestens
60 Sekunden die verbleibende Zeit. Kurzes Laden und Leerlauf zählen mit 0 W;
60 Sekunden ununterbrochenes Laden löschen den Verlauf. Messlücken über zwei
HIGH-Intervalle sowie ungültige Eingaben verwerfen die Historie. Es gibt keine
Persistenz. Der Coordinator wandelt die Restzeit in einen UTC-Zeitpunkt um und
veröffentlicht ihn als `discharge_forecast` für den gleichnamigen Timestamp-Sensor.
Cache-Refreshs übernehmen den zuletzt berechneten Zeitpunkt unverändert.
Die Attribute `observation_minutes`, `average_discharge_w` und `observed_at`
veröffentlichen die zugehörige Beobachtungsdauer, mittlere Leistung und den
Zeitpunkt der letzten ausgewerteten Messung. Sie werden zusammen mit einer
ungültigen oder zurückgesetzten Prognose verworfen; ein Cache-Refresh erzeugt
keinen neuen Messzeitpunkt.

### Verbrauchsabhängige Netzladung bis PV-Start (REQ-BRIDGE-CHARGE)

`domain/bridge_charge.py` berechnet ausschließlich aus Zeitpunkt, PV-Start,
mittlerer Entladeleistung, Kapazität, SOC-Grenzen, Ladeleistung und ausdrücklich
erlaubten `ChargeWindow`-Intervallen einen `BridgeChargePlan`. Die Domain kennt
weder Home Assistant noch den zeitvariablen Tarif und schreibt keine Register.
Damit kann eine spätere Tarifquelle dieselbe Berechnung mit eigenen Intervallen
verwenden. Die bestehende dynamische Preissteuerung ist nicht daran angebunden.

Der Bedarf ergibt sich aus dem Verbrauch bis PV-Start abzüglich der nutzbaren
Batterieenergie oberhalb der Geräte-SOC-Untergrenze. Während Netzladung wird
Hausverbrauch aus dem Netz gedeckt; deshalb berücksichtigt die Berechnung sowohl
den Energiezuwachs im Speicher als auch die in dieser Zeit vermiedene Entladung.
Das Ladeziel bleibt unter dem effektiven Netzlade-Max-SOC. Geplant wird jeweils
ein zusammenhängender Auftrag: unter ausreichenden Kandidaten zuerst der
günstigste, bei gleichem Preis der späteste mögliche Start. Reicht keiner aus,
wählt die Domain die größte mögliche Bedarfsdeckung und weist den verbleibenden
Fehlbetrag aus. Ein solcher Teilplan verspricht keine vollständige Überbrückung.

`application/bridge_inputs.py` adaptiert ausschließlich die tatsächlich
vorkommenden billigsten Preisstufen des gespeicherten `TIME_OF_USE`-Tarifs auf
UTC-Intervalle, einschließlich des Basispreises. Ein teureres verbleibendes
Fenster ersetzt keinen bereits verpassten Niedertarif. Aktive Monate werden an
lokalen Tagesgrenzen geprüft. Das separate Netzladezeitfenster ist kein Eingang
der Verbrauchsplanung und begrenzt oder erweitert deren Tarifintervalle nicht.
Dieselbe Tarifauflösung versorgt die feste SOC-Ladung nach
`REQ-TIME-OF-USE-CHARGE-SOURCE`; damit ist
[Issue #237](https://github.com/dr-dimitri/sax-ha/issues/237) umgesetzt.
Die niedrigste Preisstufe wird über den vollständigen täglich vorkommenden
Plan bestimmt. Basispreisabschnitte zählen nur in tatsächlichen Lücken,
alle gleich günstigen Abschnitte sind erlaubt. Ungültige Tarifdaten ergeben
keine Freigabe und keinen Rückfall auf `timed_charge_start`/`timed_charge_end`.
`application/tariff_charge.py::tariff_charge_state` adaptiert
`domain/tariff.py::low_tariff_window` zu einem `TimedChargeState` für die
feste SOC-Ladung. Ist der Folgemonat deaktiviert, begrenzt der Adapter den
Abschnitt am lokalen Monatswechsel. Die persistierte `source` bindet
Ladehysterese und Entladesperre über eine SHA256-Identität des vollständigen
Tarifs und des absoluten Abschnitts an genau diesen Tarifstand und Zeitraum.
Laufzeitzustände ohne `source` werden beim Wechsel zu `TIME_OF_USE` verworfen,
auch bei zufällig gleichen Uhrzeiten; eine erneute Min.-SOC-Auswertung ist
erforderlich. Neue Zustände dürfen nur bei exakt passender Identität gelten.

Die alten Konfigurationswerte bleiben für andere Tarifarten unverändert
gespeichert. Im `TIME_OF_USE`-Modus sind sie unwirksam und nicht bearbeitbar;
Start/Ende werden beim Update nicht zu Preisfenstern migriert. Der Tarif gilt
bereits vor der ersten steuernden Auswertung nach Neustart und nach einer
Optionsänderung. Beim Rückwechsel auf andere Tarifarten prüft
`reconcile_charge_time_source` vor jeder neuen Ladeentscheidung die bisherigen
Überschneidungsregeln erneut; ein inzwischen mit der Ladepause überlappendes
Legacy-Netzladefenster wird wie beim Start geleert.

Die PV-Quelle ist der bereits konfigurierte `CONF_PV_FORECAST_SENSOR`. Über die
Entity Registry wird dessen `config_entry_id` der Integration `pv_forecast`
zugeordnet. Der geprüfte Service `pv_forecast.get_forecast` liefert die
15-Minuten-Prognose der Gesamtanlage mit `mean_ac_power_kw`. Der Adapter
validiert diese Zeitreihe und bestimmt den ersten ausreichend langen Zeitraum:
Die prognostizierte mittlere PV-Leistung muss in mindestens zwei
aufeinanderfolgenden Intervallen den gemessenen Entladedurchschnitt erreichen,
also den Verbrauch mindestens 30 Minuten lang decken. Serviceergebnisse werden
60 Sekunden zwischengespeichert. Es gibt keine zusätzliche Startzeit-Entity,
manuelle PV-Uhrzeit oder Ableitung aus der Tagesenergiesumme. Fehlende oder
ungültige Prognosedaten geben keine geplante Netzladung frei.

Die Option `bridge_charge_enabled` schaltet die Betriebsart ein.
`SaxPowerBridgeChargeSwitch` stellt dieselbe Config-Entry-Option als Schalter
in der Dashboard-Karte `ChargePlan.vue` bereit. Einschalten prüft wie der
Optionsdialog den zeitvariablen Tarif und die ausgewählte PV-Quelle; Ausschalten
bleibt ohne diese Voraussetzungen möglich. Der bestehende Options-Listener
wendet Änderungen live auf die Planung an. Ein eigener Entity-Listener meldet
Optionsänderungen auch bei Geräteausfall zurück, ohne Geräte-I/O abzuwarten.
Es gibt keinen zweiten Restore-State für diese Einstellung. Der vorhandene
Hauptschalter `timed_charge_enabled` und die Monatsfreigabe bleiben erforderlich;
`timed_charge_min_soc` wird durch die Bedarfsentscheidung ersetzt. Fehlende oder
veraltete Messwerte und fehlender PV-Start geben keinen Ladeauftrag frei.
`application/bridge_session.py` bindet den Auftrag an seine Konfiguration und
hält nach dem bestätigten Start die Verbrauchsbasis fest. So kann die normale
Entladeprognose nach einer Minute Ladung zurückgesetzt werden, ohne den aktiven
Auftrag zu verlieren. Festes Ende oder erreichtes Ziel beenden den Auftrag;
eine Neuplanung benötigt mindestens eine Minute nach Abschluss und wieder
gültige Beobachtungen. Es gibt keine Auftragspersistenz und keine Wiederaufnahme
ohne neue Messungen nach einem Neustart.

Der Coordinator bleibt alleiniger Besitzer des vorhandenen SunSpec-Schreibpfads.
Die bisherige fenstergebundene Entladesperre aus `timed_discharge` wird in dieser
Betriebsart nicht aufgebaut: Nach dem begrenzten Laden wird normale Entladung
wieder möglich. Die bestehenden Schutz- und Prioritätsregeln für manuelle
Ladung, PV-Überschuss und Max-SOC gelten weiterhin. Bei fälliger Zellkalibrierung
steigen `effective_max_soc` und `effective_timed_charge_max_soc` auf 100 %;
dies erweitert lediglich die Obergrenzen der Verbrauchsplanung. Bedarf,
PV-Zeitpunkt und erlaubte Tarifintervalle bestimmen weiterhin den begrenzten
Auftrag. Es gibt weder einen Rückfall auf das ausgeblendete Netzladezeitfenster
oder Min-SOC noch eine zusätzliche ungeplante Netzladung bis 100 %. PV oder ein
entsprechend hoher Überbrückungsbedarf können 100 % erreichen. Außerhalb dieser
Betriebsart bleibt die bestehende Kalibrierungssteuerung unverändert.

Der Enum-Sensor `bridge_charge_plan` veröffentlicht `off`, `waiting_for_data`,
`planned`, `charging`, `not_needed`, `insufficient`, `paused` oder `complete`.
Strukturierte Attribute liefern `observation_minutes`, `average_discharge_w`,
`discharge_at`, `charge_start`, `charge_end`, `pv_start`, `target_soc`,
`shortfall_kwh` und gegebenenfalls `reason`. `ChargePlan.vue` verwendet diese
Daten für die deutsch-/englischsprachige Meldung im zeitvariablen Tab. Die
Komponente formatiert Datum und Uhrzeit in der HA-Zeitzone, erklärt bekannte
Fehlergründe und behält einen Fehlbetrag auch während einer laufenden Teilladung
sichtbar. Sie plant nicht selbst und ruft keine Services auf.
Bei `bridge_charge_plan.attributes.enabled=true` blendet der zeitvariable Tab
das separate Netzladezeitfenster und `timed_charge_min_soc` aus, da beide die
Verbrauchsplanung nicht steuern. Netzlade-Max-SOC und Monatsfreigaben bleiben
bedienbar. Die bestätigte Backend-Option bestimmt die Sichtbarkeit auch bei
einem wartenden oder pausierten Plan.

### Gesamte Netzenergie (REQ-GRID-ENERGY)

`energy_imported_from_grid` und `energy_exported_to_grid` integrieren die
normalisierte `smartmeter_power` am gesamten Netzanschlusspunkt. Positiv
bedeutet Bezug, negativ Einspeisung. Direkter Hausverbrauch ist enthalten;
die Batterieladeleistung und die Tarifkonfiguration beeinflussen diese
Zähler nicht. `energy_charged_from_grid` behält seine bisherige Bedeutung
als geschätzter Netzstromanteil der Batterieladung.

Der Coordinator hält zwischen zwei frischen SunSpec-HIGH-Messpunkten die
vorherige Leistung (linke Riemannsumme). Der erste gültige Messpunkt setzt
die Baseline; gecachte Refreshes zählen nicht erneut. Ungültige, fehlende
oder veraltete Werte sowie Poll-Ausfälle verwerfen die Baseline. Das Alter
einer Messung und der Abstand zweier Messpunkte dürfen jeweils höchstens
`2 * READ_BLOCK_EXT_HIGH_INTERVAL` (derzeit vier Sekunden) betragen,
unabhängig vom Basic-Mode-Intervall. Größere Lücken werden übersprungen.
Erst ein neuer gültiger Messpunkt startet die nächste Messstrecke; keine
verlorene Zeit wird nachgeholt. Die Schätzung bildet deshalb ausschließlich
die beobachteten Zeiträume ab.

Die beiden kWh-Sensoren nutzen `device_class: energy` und
`state_class: total_increasing` und lesen unmittelbar aus
`coordinator.data`. Die gemeinsamen `grid_energy_attributes` liefern
`accounting_started_at` und `integration_method: left_riemann_sum`. Ihre
Persistenz liegt in `EnergyStateStore` (Hauptversion 1, Minor-Version 4):
`grid_imported_kwh`, `grid_exported_kwh` und
`grid_accounting_started_at` bilden eine gemeinsam validierte Gruppe mit
eigenem UTC-Zählbeginn. Vorhandene Summen bleiben bei einem Neustart
erhalten, die Messbaseline wird neu begonnen. Offline-Zeit zählt nicht.

Neue Einträge, ältere Snapshots ohne Netzenergiegruppe und teilweise
korrupte Gruppen starten bei 0 kWh mit aktuellem UTC-Zählbeginn. Bei einer
unvollständigen Gruppe wird auch deren interne Monotonie-Baseline
verworfen, damit der neue Nullstand gespeichert werden kann. Die übrigen
Energiezähler bleiben erhalten. Derselbe gedrosselte Schreibpfad und
Shutdown-Flush speichern alle Energiezähler. Ein Store-Lesefehler lässt
die Netzzähler unbekannt und sperrt Store-Schreibvorgänge bis zum
erfolgreichen Reload. So kann eine Batterie-RestoreEntity keine
unvollständigen Daten über eine möglicherweise noch lesbare Netz-Historie
schreiben; numerische Batterie-Altzustände dürfen weiterhin angezeigt
werden.

### Wirtschaftlichkeitsbilanz (REQ-ECONOMICS-ACCOUNTING)

Läuft in `SaxPowerCoordinator._accumulate_economics`, aufgerufen am Ende von
`_accumulate_energy` mit demselben `EnergyDelta` (02/06) und demselben
rohen, ungerundeten Entladezuwachs dieses Intervalls - keine zweite Uhr,
keine zweite Riemann-Summe. Die reine Rechnung liegt in
`domain/economics_accounting.py`:

- `compute_economics_interval` teilt die gemessene Energie proportional zur
  Dauer entlang der tatsächlich beobachteten Preis-/Tarifgrenzen.
  `SaxTariffProvider.accounting_segments` hält dazu begrenzte Snapshots von
  Tarif und dynamischer Quelle bis zur nächsten Messung vor. Verspätete
  Prognosen füllen frühere Lücken nicht nachträglich; Zeit vor der ersten
  Beobachtung und verworfene Historie bleiben unbewertet.
  `compute_economics_delta` bewertet jeweils ein solches Teilintervall:
  Netzladung kostet den Netzbezugspreis, PV-Ladung die Einspeisevergütung. Fehlt der jeweilige
  Preis, wird nichts erfunden - die Energie erhöht stattdessen
  `unvalued_inventory_kwh` (unbewerteter Bestand) und einen
  `unpriced_charge`-Zähler. Dasselbe gilt bei fehlendem Smartmeter:
  `EnergyDelta.origin_known=False` erhält die Qualitätslücke trotz des
  kompatiblen physischen Netz-Fallbacks bis zur Geldbilanz. Jede Entladung
  verbraucht zuerst aus
  diesem Bestand (`min(discharged_kwh, unvalued_inventory_kwh)`) - dieser
  Anteil erzeugt AUSDRÜCKLICH keinen vermiedenen Geldwert (sonst würde eine
  vorausgegangene Preislücke einen kostenlosen Scheingewinn erzeugen). Nur
  der danach verbleibende,
  monetarisierbare Rest (bepreist geladen oder beim Bilanzstart mit 0 EUR
  angesetzt) ist den aktuellen Netzbezugspreis wert.
- `_bootstrap_economics_if_ready` setzt den unbewerteten Bestand unabhängig
  von Kapazität und SOC auf 0: Der beim erstmaligen Aktivieren bereits
  vorhandene Speicherinhalt wird mit 0 EUR angesetzt. Am geräteseitig
  gemeldeten SOC-Minimum verwirft `min_soc_inventory_correction` einen Rest
  erst nach echter Entladung und zwei frischen Stillstands-Ticks. Aktuelle
  Ladedeltas werden dadurch nie anhand eines noch unveränderten SOC gelöscht
  (Issue #145).
- `capacity_inventory_correction` deckelt den Bestand nach demselben
  bestätigten Stillstand auf den konservativen oberen Rand der SOC-Stufe
  (`capacity_kwh * (battery_soc + Messquantum) / 100`). Das Messquantum kommt
  aus dem SunSpec-SOC-Skalierungsfaktor, bei ungültigem Faktor aus einem
  konservativen Prozentpunkt. Ohne
  diesen Deckel bliebe die
  Ladeverlust-Differenz jedes *unbepreisten* Zyklus (geladen > entladen)
  dauerhaft im Bestand liegen und würde später bepreist geladene Entladung
  als unbewertet abbuchen (Issue #132). Ist Kapazität oder SOC gerade
  unbekannt, wird nicht gedeckelt - als unbekannt gilt (wie in
  `price_optimizer._context`) auch eine gemeldete Kapazität von 0. Geloggt
  wird höchstens einmal je
  `INVENTORY_CAP_LOG_INTERVAL_SECONDS`; die insgesamt verworfene Menge steht
  als `inventory_capped_kwh` im Diagnose-Download.

Das operative Nettoergebnis (vermiedene Netzkosten − Netzladekosten −
PV-Opportunitätskosten) bleibt jederzeit aus den drei ungerundeten Teilsummen
ableitbar und wird identisch als `economics_operating_result` und
`economics_net_savings` veröffentlicht. Es darf durch spätere Kosten sinken
und negativ werden; ROI, Restbetrag und Tageswert verwenden denselben
aktuellen Wert. `_economics_operating_result_high_water_eur` bleibt nur als
abwärtskompatibler Diagnose-Peak im Store und beeinflusst keine finanzielle
Kennzahl (Issue #144).

Veröffentlicht werden alle Geld-/Prozentwerte über `coordinator._rounded`,
das zusätzlich zur Rundung die negative Null auf `0.0` normalisiert:
`round(-0.0001, 2)` ergibt `-0.0`, und Home Assistant zeigt das als „−0,0"
an - ein Vorzeichen, das die gerundete Zahl selbst gar nicht mehr ausweist.
Die durchgereichten Preise bleiben
bewusst außen vor: Dort ist ein negatives Vorzeichen eine Aussage über den
Tarif.

Die batteriebezogenen Zählungen beginnen zu drei Startzeitpunkten:
`energy_charged` läuft seit der
Installation, die Herkunftszähler seit `_bootstrap_energy_origin`, die
Geldbilanz erst seit dem ersten vollständig gespeicherten Tarif. Ihre Werte
sind deshalb NICHT gegeneinander verrechenbar, obwohl das Dashboard sie
untereinander zeigt - ein Anwenderbericht las 2,44 kWh PV-Ladung neben
0,0084 EUR PV-Opportunitätskosten (= 0,112 kWh bei 0,075 EUR/kWh) als
Rechenfehler, obwohl beide Werte korrekt waren. Sichtbar gemacht wird das
über `origin_accounting_started_at` (Attribut beider Herkunftssensoren,
`coordinator._energy_origin_attributes`, plus Abschnitt `energy` im
Diagnose-Download) neben dem längst vorhandenen `economics_started_at`
sowie über die bewertete Menge `priced_charge_kwh`/`priced_discharge_kwh`
in der Geldkarte, aus der sich jeder Betrag zurückrechnen lässt.

Der einmalige Bootstrap läuft nur, solange `SaxTariffProvider.config.enabled`
wahr ist. Nach dem Bootstrap akkumuliert `_accumulate_economics` aber AUCH
während einer späteren Tarifpause unverändert weiter: `current_price`/
`feed_in_price` sind während der Pause bereits `None` (der Tarif-Adapter
liefert das für einen deaktivierten Tarif von sich aus), pausenweise
geladene Energie landet dadurch automatisch im unbewerteten Bestand statt
unbeobachtet zu bleiben - andernfalls würde eine nach dem Reaktivieren
erfolgende Entladung dieser Energie fälschlich vollständig als vermiedenen
Netzbezug monetarisieren (derselbe Scheingewinn-Fehler wie bei #42, nur
über den Umweg einer Pause). Nur die
VERÖFFENTLICHTEN fünf monetären Sensoren blenden während einer Pause auf
`None` (`_publish_economics_balance(..., monetary_available=...)`) statt
auf die weiter mitlaufenden internen Summen. `unvalued_inventory_kwh`,
`unpriced_charge_kwh` (fehlender Preis oder fehlende Herkunftsmessung) und
`unpriced_discharge_kwh` bleiben rein intern und
werden nicht als Entities veröffentlicht. `economics_current_import_price`/
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
NaN/Inf/Fremdtypen sind es. Der nur diagnostische
`operating_result_high_water_eur` sowie
`unpriced_charge_kwh`/`unpriced_discharge_kwh` bleiben dagegen monotone,
nichtnegative Summen; nur `async_reset` darf sie auf 0 setzen.
`unvalued_inventory_kwh` ist ein
Bestand (Gauge) ohne Monotonieprüfung. `economics_started_at` ist wie
`origin_accounting_started_at` (02/06) einmalig gesetzt und danach
unveränderlich; ein unvollständiges Sieben-Felder-Bündel wird beim Laden
komplett neu gebootstrapped, und die interne Monotonie-Baseline wird in
diesem Fall ebenfalls komplett bereinigt (siehe
`EnergyStateStore._origin_baseline` für dasselbe, aus einem Review-Befund
gelernte Muster). Tageshistorie, laufender Tag und Payback-Zeitpunkt werden
dann ebenfalls verworfen: Sie gehören zur alten Bilanz und dürfen nicht mit
dem neuen Nullstand kombiniert werden. Das Höchststandsfeld gehört aus
Migrationsgründen nicht zum
alten Sieben-Felder-Kernbündel: Fehlt es in einem Store bis Minor-Version 5,
startet es mit `max(0, aktueller Roh-Cashflow)`. Die alten `day_results` und
der laufende Tageswert werden wegen ihrer damaligen abweichenden
Store-Semantik verworfen. `economics_net_savings` und
`economics_net_savings_today` besitzen jeweils eine eigene Recorder-Historie.
Ihr Recorder-Beginn kann nach einem Update deshalb jünger als
`economics_started_at` sein. `_async_remove_stale_entities` entfernt den in
früheren Snapshot-Ständen bereits angelegten Registry-Eintrag
`economics_result_today` über seinen exakt benannten Suffix; die neue Unique-ID
bleibt davon unberührt.
Minor-Version 7 hatte zeitweise vorgesehen, einen geladenen
`unvalued_inventory_kwh` auf 0 zu setzen. Diese Migration wird bewusst nicht
mehr ausgeführt: Der Bestand kann aus realen Preis- oder Herkunftslücken nach
dem Bilanzstart stammen und muss deshalb auch aus älteren Snapshot-Ständen
unverändert übernommen werden (Issue #147).
Minor-Version 8 startet nur `day_results` und den laufenden Tages-Bucket neu,
weil ältere Snapshot-Stände dort Peak-Zuwächse statt signierter Ergebnisse
gespeichert haben. Das Gesamtergebnis bleibt aus den drei Geldsummen erhalten.
`notify_tariff_revision()` wird beim zentralen Anwenden geänderter Quellen
aufgerufen und hält einen diagnostischen Revisionszeitpunkt fest. Die
Geldbewertung verwendet die beobachteten Preisintervalle; ein Tarifwechsel
ändert weder vorherige Intervalle noch bereits gebuchte Beträge. Die
Amortisation und Recorder-Kalenderwerte übernehmen diese fortlaufende Bilanz.

Scheitert `EconomicsStateStore.async_load()` selbst (I/O-Fehler, unbekannte
künftige Storage-Hauptversion), setzt `async_load_economics_state`
`_economics_store_write_blocked` - Rechnung und Bootstrap laufen normal im
Arbeitsspeicher weiter (analog zu `ControlConfigLoadStatus.FAILED`), aber
`_async_schedule_economics_save`/`_async_flush_economics_state` verweigern
jeden Schreibversuch, bis ein Neuladen des Config Entry eine frische
Coordinator-Instanz erzeugt. Ohne diese Sperre würde eine aus lauter Nullen
neu gebootstrappte Bilanz den eigentlich vorhandenen, nur unlesbaren Store
überschreiben und dessen Inhalt endgültig verlieren.

### ROI und Amortisationsstand (REQ-ECONOMICS-AMORTIZATION)

`domain/economics_amortization.py` enthält nur noch die reinen Formeln für
ROI, den auf 0..100 geklemmten Fortschritt und den bei 0 gefloorten
Restbetrag. `SaxPowerCoordinator._publish_amortization` addiert den optionalen
Vorlauf-Ertrag ausschließlich für diese drei Werte und veröffentlicht daneben
das signierte Nettoergebnis des laufenden Tages.

Die frühere 30-Tage-Amortisationsprognose ist entfernt:
`compute_amortization_forecast` wird nicht mehr angeboten, und
`economics_average_daily_result_30d`,
`economics_projected_annual_result` sowie
`economics_estimated_payback_date` werden weder berechnet noch als Entities
registriert. Historische Tages-Buckets und `payback_achieved_at` bleiben im
Store-Format, damit bestehende gespeicherte Zustände ohne Datenverlust geladen
werden können; der Coordinator schreibt den Payback-Zeitpunkt nicht weiter
fort.

`economics_net_savings` und `economics_net_savings_today` behalten intern
vier Nachkommastellen. Ihre Sensorbeschreibungen setzen
`suggested_display_precision=2`, sodass Home Assistant Währungswerte mit zwei
Nachkommastellen darstellt, ohne Recorder- oder Rechengenauigkeit zu verlieren.
Das ROI-Attribut `prior_result_eur` bleibt numerisch; Dashboardzeilen ergänzen
dafür eine separate, auf exakt zwei Nachkommastellen festgelegte Anzeigeform
und explizit das Suffix `€`.
### Datenqualität, Diagnose und Bilanzneustart (REQ-ECONOMICS-OBSERVABILITY)

Macht sichtbar, ob und warum die Bilanz gerade vertrauenswürdig ist, ohne
selbst neue Geldwerte zu berechnen. Die reine Ableitung liegt in
`domain/economics_status.py`:

- `EconomicsStatus` (sechs Werte) und `compute_economics_status(...)`
  bilden eine feste Prioritätsreihenfolge aus mehreren, ggf. gleichzeitig
  zutreffenden Booleans ab: `disabled` > `storage_error` > `price_unavailable` >
  `origin_unavailable` > `partial_price_coverage` > `active`. `disabled`
  gilt ausschließlich bei deaktiviertem Tarif und schlägt dabei jeden
  anderen Zustand.
- `compute_price_coverage_percent(priced_kwh, unpriced_kwh)` ist
  energiebasiert (nicht tickbasiert) und liefert bei Nenner 0 100 % -
  dieselbe Formel wie `DayEconomicsResult.price_coverage_percent` (04/06).
- `partial_price_coverage` bewertet nur den LAUFENDEN Kalendertag (die
  Tages-Buckets aus 04/06) und erst, wenn die Lücke sowohl absolut
  (`MIN_UNPRICED_KWH_FOR_PARTIAL`) als auch relativ
  (`PRICE_COVERAGE_THRESHOLD_PERCENT`, 95 %) ins Gewicht fällt -
  `is_price_coverage_partial`. Die relative Schwelle allein genügt nicht:
  kurz nach Mitternacht ist der Tagesbucket leer, ein einziges
  unbepreistes Intervall stünde dort auf 0 % Abdeckung. Aus den Lifetime-Zählern
  abgeleitet, die nie zurückgehen, kippte sonst eine einzige unbepreiste
  Kilowattstunde den Sensor dauerhaft - `active` wäre nur noch über einen
  Bilanzneustart erreichbar, der die gesamte Geldbilanz verwirft
  (Issue #134). Die Lifetime-Quoten bleiben Attribute, sind aber kein
  Zustandsauslöser.

`SaxPowerCoordinator._publish_economics_status` (aufgerufen am Ende von
`_accumulate_economics`, unabhängig vom `frozen`-Zweig, damit auch
`storage_error` sichtbar wird, bevor die Bilanz je gestartet ist) setzt das
zusammen:

- Zwei neue Lifetime-Zähler `_economics_priced_charge_kwh`/
  `_economics_priced_discharge_kwh` (Gegenstück zu den bestehenden
  `unpriced_*`-Zählern, aus denselben `EconomicsDelta.priced_charge_kwh_delta`/
  `priced_discharge_kwh_delta` wie die Tages-Buckets) ergeben
  `charge_price_coverage_percent`/`discharge_price_coverage_percent`.
  `origin_unavailable` ist wahr, wenn `_energy_origin_initialized()`
  (02/06) falsch liefert.
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
Payback-Zeitpunkt zurück, setzt den unbewerteten Bestand wie bei der
erstmaligen Aktivierung auf 0 - rührt niemals `energy_charged`/
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
Berechnung. Alle fünf kumulativen Geldsensoren verwenden den neuen
Aktivierungszeitpunkt als gemeinsames `last_reset`; so trennt der Recorder
den Bilanzabschnitt für jede Rohsumme sowie Ergebnis und Netto-Ersparnis,
ohne den gewollten Sprung auf 0 als Geldänderung zu verbuchen. Normale
Preis- und Ergebnisbewegungen oder ein Reload ändern diesen Zeitpunkt nicht
(Issue #151).

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

Ein Bilanzneustart und sämtliche Schreib-/Leseprüfungen sind über den
Store-Lock serialisiert (Issue #168). Normale Polls dürfen während der
Reset-Dateizugriffe weiterhin die bisherige Bilanz fortschreiben. Erst
nach erfolgreicher Persistierung räumt der Reset deren ausstehende
Snapshots, Timer und Final-Write-Listener auf. Bei einem Fehler bleiben
auch die währenddessen hinzugekommenen Beträge und ihre geplante
Persistierung erhalten. Verzögerte Writes entnehmen ihren Snapshot erst
unter dem Lock; wartende Sofort-Writes erkennen über eine beim Aufruf
erfasste Laufzeitgeneration, ob ein erfolgreicher Reset sie bereits
abgelöst hat, und werden dann ohne Speicherfehler übersprungen. Damit
kann auch ein gleichzeitig angeforderter Shutdown-Flush keinen Altstand
zurückschreiben. Mehrere Service-Aufrufe serialisiert zusätzlich der
Coordinator über seinen Reset-Lock. Die In-Memory-Umstellung nach einem
erfolgreichen Store-Reset enthält keinen weiteren `await`, damit kein
Poll einen alten Coordinator-Stand unter der neuen Generation vormerkt.

### Dashboard-Tab "Amortisation" (REQ-VUE-SAVINGS)

`SavingsView.vue` verwendet `economics_net_savings` für alle Kalender- und
freien Zeitraumwerte. Amortisation, Kalenderwerte, die mit Zeitvariabler Tarif
gemeinsame `TariffPlan.vue`-Karte, freie Auswertung, eingeklappte Hinweise und
Statushinweis folgen der oben beschriebenen Funktionsmatrix. Daten kommen aus den vorhandenen HA-Entitäten
und dem nativen Recorder-Adapter; Darstellung und Datumswahl sind in Vue
implementiert. Es gibt keine generierten Lovelace-Karten oder gespeicherten
Dashboard-Templates.

Fehlt `economics_net_savings`, entfallen Kalenderwerte, dessen Detailzeile
und die freie Auswertung. Fehlende optionale Entitäten erzeugen keine leeren
Karten. Die abgelöste REQ-ECONOMICS-SAVINGS-DASHBOARD verweist auf diese
aktuelle Implementierung.

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
Bei einem Benutzerwert unter 100 % gilt am dritten lokalen Kalendertag
nach der letzten Volladung ab 00:00 HA-Zeit bis zur nächsten real gemessenen
Volladung das Ziel 100 %. Die zentrale Ladeauswertung aktualisiert die
Fälligkeit vor jeder Entscheidung, auch bei Timer- und Serviceaufrufen vor
dem nächsten Poll. Auch die laufende PV-Regelung prüft vor jedem neuen
Sollwert. SOC-Fehler, Bootstrap und Shutdown bleiben gesperrt.
`next_cell_calibration` ist ein nativer DATE-Sensor; sein lokales Datum wird
im Dashboard ohne Uhrzeit und ohne Browser-Zeitzonenverschiebung angezeigt.
Der Diagnosewert `next_cell_calibration_at` bleibt der zugehörige UTC-Zeitpunkt.
`infrastructure/calibration_store.py`
speichert Zeitstempel und Voll-SOC-Flanke pro Config Entry; `__init__.py` lädt
sie vor dem ersten Refresh. Die Number-Entity behält stets den konfigurierten
Wert, während Coordinator und Preisplaner den effektiven Wert verwenden.
Auch das eigene Netzladeziel erhält während der Kalibrierung einen
effektiven Wert von 100 %, bei unverändertem Benutzerwert und unveränderter
Slidergrenze. Die Kalibrierung startet dabei weiterhin keine eigene
Netzladung; die regulären Startbedingungen bleiben erforderlich.
Bei `REQ-BRIDGE-CHARGE` ist 100 % ausschließlich die wirksame Obergrenze;
der berechnete Bedarf bis PV-Start bestimmt weiterhin das Ziel. Die
Tarifpreisfenster bleiben verbindlich, auch während Kalibrierungsfälligkeit.
Reihenfolge/Priorität in `_async_enforce_grid_charge`:

1. **SOC ≥ "Max. SOC"** (`soc_reached`): Leistungsvorgabe wird auf 0 %
   gehalten - unabhängig davon, ob zeitgesteuertes oder netzdienliches Laden
   aktiviert ist (z. B. auch bei einem durch PV-Überschuss vollen Speicher).
   Verhindert dauerhaftes Volladen auf 100 % (Batterie-Lebensdauer); der
   Speicher entlädt sich währenddessen nicht automatisch zur
   Eigenverbrauchsdeckung. Wird der Zielwert in einem ausgewählten
   Preis-Ladeslot erreicht, hält `_max_soc_hold_is_price_slot_bound` diesen
   Zustand auch bei einem kleinen SOC-Abfall bis `price_plan.charge_now`
   wieder `False` wird. So kann derselbe Slot keinen zweiten Ladezyklus
   starten; am Slotende folgt aktiv die SmartMeter-Nullregelung. Endet eine
   gebundene Sperre bei weiterhin erreichtem SOC, hält der vorhandene
   Freigabe-Latch die Nullregelung beim Entladen stabil - auch nach
   zeitgesteuerten und netzdienlichen Fenstern. Erneute Batterieladung ab
   50 W oder Netzeinspeisung über 50 W über zwei Auswertungen hebt diese
   Freigabe wieder auf und hält erneut 0 %. Steigender SOC löst die Sperre
   auch ohne Leistungsbestätigung sofort aus, damit fehlende SunSpec-Werte
   oder kleine Ladeleistungen kein Volladen ermöglichen. Ein unveränderter
   oder fallender SOC allein sperrt die Entladung weiterhin nicht; unterhalb
   des Zielwerts wird der Freigabe-Latch wie bisher zurückgesetzt.
2. **Sonst, falls zeitgesteuertes Laden aktiviert + im Zeitfenster + im
   aktiven Monat + unter Netzladeziel + im selben unveränderten aktiven
   Fenster zuvor unter Min. SOC + kein
   PV-Überschuss** (`timed_should_charge`):
   Leistungsvorgabe = `MIN_SETPOINT_POWER` (sättigt in
   `_watts_to_ic_setpoint_raw` auf -100 %, maximal mögliche Ladeleistung -
   eine frühere, konfigurierbare "Max. Netzladeleistung" wurde entfernt,
   weil der eingestellte Watt-Wert in der Praxis keinen Einfluss auf die
   tatsächliche Ladeleistung hatte).
   Nach tatsächlich gemessener Netzladung merkt die Integration die feste
   Ablaufzeit dieses Fensters. Endet/pausiert die Netzladung vorher, hält
   der gemeinsame Writer die Entladung gesperrt und erlaubt über
   `min(0, storage_power_active + smartmeter_power)` weiterhin PV-Laden.
   Dieser Haltezustand greift vor der netzdienlichen Regelung; er ist bei
   aktiviertem preisoptimiertem Laden immer inaktiv und wird verworfen.
   Bei aktivierter Verbrauchsplanung (`REQ-BRIDGE-CHARGE`) ersetzt deren
   begrenzter Auftrag die feste Startschwellenentscheidung. Nach diesem Auftrag
   wird keine fenstergebundene Entladesperre gehalten. Bei Kalibrierungsfälligkeit
   steigt nur die wirksame SOC-Obergrenze auf 100 %; die Bedarfsentscheidung
   erhält keinen Rückfall auf Startschwelle oder separates Netzladezeitfenster.
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
   Nullregelung unterhalb des Neutralpreises; nur Absoluter Preis begrenzt
   das Band zusätzlich durch die Preisgrenze).
5. **Sonst**: Task wird gestoppt, Register 40051 zurück auf 0
   (SmartMeter-Nullregelung), Zustandsmaschine zurückgesetzt.

**Aktive Monate:** Beide Features haben zusätzlich je 12 Monats-Schalter
(`switch.SaxPowerMonthSwitch`, eine generische Klasse für beide Features und
alle 12 Monate, parametrisiert über `is_month_active`/`async_set_month_active`
-Callables), die in `SaxPowerCoordinator._timed_charge_months`/
`_grid_serving_months` (je ein `set[int]`, Default alle 12 Monate) verwaltet
werden. `_async_enforce_grid_charge` prüft zusätzlich `now.month in
self._timed_charge_months` bzw. `self._grid_serving_months`.

**Bestätigung der Softwarekonfiguration:** Monatsänderungen und die übrigen
Software-Entity-/Serviceaufrufe bestätigen die angenommene HA-Konfiguration
sofort über die Zustandslistener und merken ihren Snapshot zum Speichern vor.
Die Entity- und Software-Serviceadapter verwenden `defer_device_update=True`;
damit warten weder Serviceantwort noch Konfigurationszustand auf
`_charge_control_lock` oder Modbus. Das betrifft die drei Ladehauptschalter,
Max-SOC, Netzladeziel/Min-SOC, Preisgrenzen, Anzahl Stunden, Strategie,
Prognoseschwelle sowie einzelne und atomare Zeitfenster.

Alle verwenden denselben nachverfolgten, endlichen Worker wie die Monate.
Er fasst Änderungen zusammen; eine neuere Revision während einer Auswertung
führt danach zu einer weiteren Auswertung des aktuellen Stands unter dem
Control-Lock. Quittierungspflichtige Aktivitätsflags bleiben an die bestehende
Geräteschreibsequenz gebunden. Interne Coordinator-Aufrufe, Bootstrap und
manuelle physische Steuerbefehle bleiben synchron. Bootstrap startet keinen
Worker; Shutdown sperrt neue Änderungen vor der Mutation und wartet einen
laufenden Task vor Store-Flush und abschließendem Reset ab. Verhalten und
Prüfnachweise: `REQ-VUE-ENTITY-BINDING`,
[`tests/test_control_response.py`](tests/test_control_response.py) und
[`tests/test_vue_dashboard_e2e.py`](tests/test_vue_dashboard_e2e.py).

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

**"Netzladen Max. SOC"** (`SaxPowerTimedChargeMaxSocNumber`) begrenzt nur
die zeitgesteuerte Netzladung, einschließlich des berechneten Ziels der optionalen
Verbrauchsplanung nach `REQ-BRIDGE-CHARGE`. Ohne diese Betriebsart beginnt sie
bei eingeschalteter Netzladung
im aktiven Fenster eines freigegebenen Monats unterhalb von "Netzladung
Min. SOC" und lädt dank `_timed_charge_armed` innerhalb desselben
unveränderten Fensters bis zum eigenen Ziel weiter. Ein SOC unter der
Startschwelle außerhalb eines freigegebenen Fensters erzeugt keine Freigabe
für das nächste Fenster. Am Ziel setzt die Auswertung den Latch zurück und
beendet die Netzladung;
nach gemessener Netzladung bleibt die Entladung bis zum Fensterende gesperrt,
während PV weiterhin bis zum globalen Ziel laden kann. Ohne bestätigte
Netzladung wird unterhalb des globalen Maximums die SmartMeter-Nullregelung
freigegeben. Der globale
"Max. SOC" bleibt führend: Er bestimmt dynamisch die Obergrenze des
Netzladeziel-Sliders. Eine globale Absenkung reduziert sofort auch einen
höheren Netzladezielwert und persistiert beide zusammen. Eine globale
Erhöhung erweitert nur den Sliderbereich und verändert den gewählten
Netzladezielwert nicht. Das Dashboard zeigt den Regler unter
"Zeitvariabler Tarif" → "Einstellungen" direkt über "Netzladung Min. SOC".
Seine Grenzen und der bestätigte Wert kommen aus der vorhandenen Number-Entity.

`infrastructure/timed_charge_store.py` speichert die offene Hysterese
unabhängig von Konfiguration und Entladeschutznachweis. Start-/Enduhrzeit
und konkretes UTC-Fensterende binden sowohl RAM-Zustand als auch Persistenz
an dieselbe unveränderte lokale Fensterinstanz. Fensterende, eine andere
Fensterinstanz, geänderte Start-/Enduhrzeiten, Deaktivierung oder Entzug der
Freigabe des aktuellen Monats verwerfen beide Zustände, auch bei fehlendem
SOC. Die Prüfung erkennt einen Fensterwechsel auch ohne Poll zwischen den
beiden Fenstern. Bei Min. SOC 20 % und Ziel 80 % startet daher eine in
Nacht 1 von 18 % auf 60 % geladene Batterie in Nacht 2 bei 60 % nicht
erneut und speichert keine Freigabe für Nacht 2. Erst ein aktuell unter
20 % liegender SOC im aktiven freigegebenen Fenster erlaubt einen neuen
Start. PV-Pausen und temporär ungültige SOC-Messungen erhalten eine offene
Freigabe nur innerhalb desselben weiterhin freigegebenen Fensters.
Der Bootstrap lädt den Zustand vor dem ersten Refresh. Sobald die
Konfiguration vollständig ist, prüft die Steuerung Fensteridentität,
aktive Monate und Freigabe. Die Wiederaufnahme benötigt zusätzlich einen
gültigen SOC. So setzt
eine unter Min. SOC gestartete Ladung auch nach einem Neustart oberhalb
dieser Schwelle bis zum Ziel fort. Zustandsänderungen werden sofort
gespeichert; Shutdown löscht die offene Hysterese nicht. Fehlende oder
ungültige Daten liefern keine Ladeberechtigung. Eine wiederhergestellte
Hysterese ist kein Nachweis gemessener Netzladung. Der Store schreibt
atomar und bestätigt Änderungen durch Rücklesen, da Home Assistant
Schreibfehler intern abfangen kann. Ein atomarer inaktiver Datensatz
setzt die gespeicherte Hysterese logisch zurück. Nicht bestätigte Schreibversuche
werden protokolliert und bei der nächsten gültigen Auswertung erneut
versucht; die laufende Steuerung bleibt wirksam. Bei einem Neustart vor
erfolgreicher Persistenz ist nur der lesbare gespeicherte Stand verfügbar.

**Entladestatus nach Netzladung:** `application/timed_discharge.py` bestimmt
die konkrete UTC-Ablaufzeit des aktiven lokalen Fensters (auch über
Mitternacht und bei Zeitumstellung). Zwei frische HIGH-Messungen mit
Netzbezug über 50 W und Batterieladung über 50 W setzen den Nachweis; beide
müssen nach dem bestätigten zeitgesteuerten Start begonnen haben und den
Steuermodus 1 melden. Eigene Messrevisionen, Messbeginn/-alter und die
unveränderte Modusrückmeldung verhindern Nachweise durch wiederverwendete
Setter-Daten oder optimistische Register-Updates. Ein reiner Ladeauftrag,
PV-Laden oder preisoptimiertes/manuelles Laden setzt keinen Nachweis.

`infrastructure/timed_discharge_store.py` speichert die bestätigte Ablaufzeit
je Config Entry, bei Tarifladung zusätzlich die `source`-Identität. Vor dem
ersten Steuerlauf werden ungültige Zustände verworfen. Die 25-Stunden-Grenze
gilt für Legacy-Fenster; Tarifzustände werden gegen die exakte Quelle und
Ablaufzeit geprüft. Eine durch übersprungene teure Abschnitte bei der
Sommerzeitumstellung verlängerte Niedertarifphase darf länger gültig sein.
Eine abgelaufene Frist aktiviert keine Sperre; bis zu 25 Stunden alte
Fristen bleiben lediglich als Endmarker bekannt, damit ein nachträglich
verlängertes Fenster denselben Ladezyklus auch nach Neustart nicht neu
startet oder erneut an die globale Max-SOC-Sperre bindet. Das nächste
reguläre Fenster bleibt möglich. Geänderte Uhrzeiten oder Monatsauswahlen
verlängern diese Frist nicht. Ausschalten der Netzladung und Wechsel zum
preisoptimierten Laden verwerfen den Nachweis und geben diese Sperre frei.
Die Preisplanung, Neutralpreiszone und Preis-Slot-Bindung nutzen weiterhin
ihre eigene Logik und die bisherige Writer-Kadenz.

Im Haltezustand berechnet `application/charge_policy.py` aus Batterie- und
Netzleistung einen ausschließlich nichtpositiven PV-Sollwert. Fehlende,
ungültige oder über vier Sekunden alte Messwerte ergeben 0 W, ebenso ein
erreichtes globales SOC-Ziel. Der Halte-Writer prüft alle zwei Sekunden
zusätzlich die absolute Frist, auch wenn Basic-Lesefehler die normale
Steuerentscheidung verhindern. Sein 0-%-Fallback bleibt ohne gelesene
Leistungsreferenz/Skalierung schreibbar; der validierte SunSpec-Pfad und
dessen Modus-Rollback bleiben erhalten. Die Regelung kann auf schnelle
Last-/PV-Änderungen erst beim nächsten Mess-/Steuertakt reagieren.

Das Dashboard zeigt im Tab „Zeitvariabler Tarif“ unmittelbar unter
„Netzladezeitfenster“ die Karte „Entladestatus“. Der Enum-Sensor
`timed_charge_discharge_status` zeigt „Normalbetrieb“, „Netzladen“ oder „Entladung wg. Netzladen gestoppt“.
„Normalbetrieb“ beschreibt ausschließlich diesen Mechanismus. Nach einem
Schreibfehler wird kein erfolgreich gehaltener Zustand behauptet.

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
Monats-Sets, Netzladen Max. SOC und Min. SOC, PV-Prognose-Mindestwert,
die drei Automatik-Schalter, Ladestrategie und Preisparameter) liegen als
ein Snapshot in einem
versionierten Store: `infrastructure/control_store.py`
(`ControlConfig`/`ControlConfigStore`, Schlüssel
`sax_power.control.<entry_id>`). Mehrere Config Entries haben dadurch
getrennte Stores.

Der eigene Netzladezielwert `timed_charge_max_soc` übernimmt beim Upgrade
eines älteren Stores ohne dieses Feld den validierten globalen `max_soc`.
Bei einer einmaligen Migration ohne Store wird er erst am Bootstrap-Ende
initialisiert, nachdem die vorhandene globale Einstellung wiederhergestellt
ist. Die Entity-Reihenfolge beeinflusst den Anfangswert dadurch nicht;
ein eigener RestoreEntity-Pfad ist für die neue Number-Entity überflüssig.
Gespeicherte Netzladezielwerte werden auf den globalen Max. SOC begrenzt.

`__init__.async_setup_entry` hält eine verbindliche Reihenfolge ein:

1. `async_load_calibration_state()` / `async_load_energy_state()` /
   `async_load_control_state()` - alle drei Stores werden geladen, bevor
   irgendetwas das Gerät steuert. `async_load_control_state()` öffnet
   zusätzlich das **Bootstrap-Fenster**.
2. `async_config_entry_first_refresh()` - liest die Register ganz normal,
   überspringt aber `_async_enforce_grid_charge`. Reads sind im
   Bootstrap-Fenster erlaubt, steuernde Writes nicht.
3. `async_forward_entry_setups(...)` - die Plattformen legen ihre Entities
   an. Deren Setter wenden keine Teilkonfiguration an:
   `_async_apply_grid_charge_change` bleibt gesperrt und Monatssetter
   starten keinen Auswertungstask.
4. `price_planner.async_setup()`, danach `async_finish_bootstrap()` -
   schließt das Fenster, schreibt den vollständigen Snapshot fest und wendet
   unter dem vorhandenen Control-Lock **genau eine** Ladeentscheidung an.

Jeder Fehler innerhalb dieser Sequenz läuft durch
`__init__._async_rollback_failed_setup` (REQ-SETUP-ROLLBACK). Nach bereits
begonnenem Plattform-Forwarding werden zuerst die Plattformen entladen;
danach beendet der Coordinator Timer, Planner-/Tarif-Listener und ausstehende
Store-Writes, `hass.data` wird bereinigt und der Modbus-Client geschlossen.
Dieser Fehlerpfad verwendet `coordinator.async_shutdown(reset_device=False)`:
ein unvollständiger Bootstrap darf keinen zusätzlichen Gerätesteuer-Write aus
noch unbestätigten Einstellungen ableiten. Nur der reguläre Unload verwendet
den Standard `reset_device=True` und gibt das Gerät aktiv auf Modus 0 frei.

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

`FAILED` entsteht bei einem I/O-Fehler, syntaktisch defektem JSON, einem
Payload, der kein Objekt ist, oder einer Storage-Hauptversion, die diese
Version nicht kennt (Home Assistant meldet das per `NotImplementedError`).
Dann gelten sichere Defaults, es wird nicht migriert, und der vorhandene Store bleibt
unangetastet - er kann die einzige Kopie einer korrekten Konfiguration sein
oder von einer neueren Version stammen.

Home Assistant verschiebt defektes JSON in eine `.corrupt.*`-Datei und
liefert dafür denselben Leerwert wie bei einer fehlenden Datei. Der
Ladeguard für Steuer- und Energiezustände unterscheidet diese Fälle anhand
der vorhandenen Store- und Quarantänedateien. Damit bleibt der Fehlerschutz
auch nach einem weiteren Reload wirksam; eine wiederhergestellte gültige
Store-Datei hebt ihn trotz vorhandener Quarantänekopie auf.

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

**Schreiben:** Nach dem Bootstrap merkt jede Einstellungsänderung den aktuellen
Snapshot zum gebündelten Schreiben vor: Entity- und Software-Serviceänderungen
bereits bei Annahme der Konfiguration, unabhängig von der nachgelagerten
Geräteauswertung (siehe oben und `REQ-VUE-ENTITY-BINDING`); direkte interne
Änderungen im gemeinsamen Endpunkt `_async_apply_grid_charge_change`.
Ein unveränderter Snapshot löst
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
`decode_sunssf` akzeptiert ausschließlich Exponenten von −10 bis +10
einschließlich beider Grenzen (`SUNSSF_MIN`/`SUNSSF_MAX`); ungültige Faktoren
liefern wie der Sentinel `None`. Auch Sollwertschreiben und SOC-Auflösung
verwenden diesen Decoder. `decode_high_block` gibt ungültige Faktoren aus
HIGH und LOW2 mit ihrer Registeradresse zurück. Der Coordinator protokolliert
pro betroffenem Register einmal während seiner Laufzeit eine Warnung;
Not-Implemented-Sentinels bleiben ohne Warnung. So bleiben Energie- und
Geldzähler bei ungültiger Speicherleistung unverändert, während gültige
Register weiter aktualisiert werden (Issue #194).
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
Der Coordinator behandelt diesen Fehler wie einen gescheiterten Read des
jeweiligen Blocks: HIGH-Werte werden unbekannt, während ein vorhandener
LOW-Cache erhalten bleibt. Der Basic-Read prüft zusätzlich Blocklänge und
SOC (ganzzahlig, 0–100), bevor er seinen Cache erneuert; Fehler entziehen
die Freigabe für weiteres Netzladen.

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

Preisplan-Timer und Änderungen reiner Steuerwerte veröffentlichen ihre
Ergebnisse mit `async_update_listeners()`. Sie ersetzen keinen erfolgreichen
Messdaten-Refresh und verändern dessen Verfügbarkeit nicht. Nach einem
Basic-Lesefehler sperrt der Coordinator negative Sollwerte bis zur erneuten
Auswertung eines erfolgreich gelesenen SOC unter dem Steuer-Lock. Der
Schreibpfad prüft dieselbe Sperre; ein bestätigter zeitgesteuerter
Netzladenachweis darf währenddessen nur mit 0 W gehalten werden. Auch eine
bereits angewendete Max-SOC-Sperre bleibt bei 0 W; bekannte Fenster- und
Preis-Slotgrenzen gelten weiterhin, alte Leistungsmessungen lösen keine
neue Freigabe aus (Details: REQ-TIMED-SOC-CHARGE, Issue #167).

## Tests

```
tests/
├── conftest.py                  Aktiviert das Laden von custom_components in Tests
├── test_calibration.py           Reine 3-Kalendertage-/Voll-SOC-Policy und versionierte
│                                  UTC-Persistenz einschließlich ungültiger Daten
├── test_charge_soc_availability.py Basic-Ausfall: Writer-Stopp, Timer/Services,
│                                  SOC-gesteuerte Wiederaufnahme und Verfügbarkeit
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
│                                  Strategie (inkl. persistentem 24-h-Zeitbudget,
│                                  Teilslots, Planungshorizont und PV-Prognose im Smart-Modus),
│                                  Schreibpfad und Abbruchgründe im Coordinator,
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
│                                  Ladeleistung, fehlender Smartmeter-Wert (zählt
│                                  konservativ als Netzladung) sowie die
│                                  Delta-Invariante (grid + pv == charged) über
│                                  viele zufällige Intervalle ohne kumulative Drift
├── test_energy_persistence.py       Persistenz der Energiezähler inkl. Herkunft
│                                  (REQ-ENERGY-DASHBOARD/REQ-ENERGY-ORIGIN):
│                                  Store-Round-Trip, unabhängige Feldvalidierung
│                                  (auch für die beiden Herkunftszähler und den
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
│                                  Herkunfts-Bündel ohne an der alten Teil-Baseline zu
│                                  scheitern, Migration eines Minor-Version-2-Snapshots
│                                  (Restbestand "Herkunft unbekannt" wandert auf den
│                                  Netzzähler), zwei getrennte Config Entries sowie die
│                                  Coordinator-Verdrahtung (Rundung, Entladung und
│                                  SunSpec-Ausfall bleiben unverändert) in
│                                  test_coordinator.py
├── test_economics_accounting.py     Reine Geldbilanz (REQ-ECONOMICS-ACCOUNTING,
│                                  domain/economics_accounting.py): Netz-/PV-/gemischte
│                                  Ladung, fehlender
│                                  Netzbezugs-/Einspeisepreis macht Ladung unbepreist statt
│                                  erfunden, negative Preise ohne Clamping, Entladung aus
│                                  unbewertetem Bestand ohne vermiedenen Geldwert (Regression
│                                  zum verworfenen Issue #42), teilweise/vollständig
│                                  monetarisierbare Entladung, fehlender Preis bei
│                                  Entladung wird nicht rückwirkend bewertet,
│                                  Ladeverlust-Sichtbarkeit ohne angenommenen
│                                  Wirkungsgradfaktor sowie
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
│                                  Coordinator-Bootstrap (Anfangsbestand 0 ohne
│                                  Kapazität/SOC, deaktivierter Tarif bootstrapped nicht, Shutdown-Flush,
│                                  Tarifrevisions-Zeitstempel); zusätzlich die
│                                  Tages-Buckets/Payback-Erweiterung (REQ-ECONOMICS-
│                                  AMORTIZATION): Round-Trip von day_results/current_day/
│                                  payback_achieved_at, ein kaputter Tageseintrag verwirft
│                                  nur sich selbst, das Sieben-Felder-Bündel des laufenden Tages
│                                  wird als Ganzes verworfen, Kappung auf MAX_STORED_DAYS
│                                  sowie der unveränderliche Payback-Zeitpunkt
├── test_economics_amortization.py   Reine ROI-/Amortisationsberechnung
│                                  (REQ-ECONOMICS-AMORTIZATION,
│                                  domain/economics_amortization.py): ROI unklemmt
│                                  (negativ, über 100 %), Fortschritts-Klemmung auf
│                                  0..100 und Restbetrag auf 0 gefloort; die
│                                  Coordinator-seitige Verdrahtung von ROI-/Restbetrags-/
│                                  Tagesergebnis-Sensoren samt Tarifpause-Maskierung und
│                                  Investitionskostenänderung liegt in
│                                  test_coordinator.py
├── test_economics_status.py         Reine Status-/Abdeckungsableitung
│                                  (REQ-ECONOMICS-OBSERVABILITY,
│                                  domain/economics_status.py): jeder der sechs Status
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
├── test_dashboard_api.py            Entity-Metadaten, Rechte und Registry-Änderungen
├── test_vue_dashboard.py            Panel-Lebenszyklus und Hash-Assets
├── test_vue_dashboard_repairs.py    Dashboard-Update und Registrierung über HA-Reparaturen
├── test_vue_dashboard_e2e.py        Zwei native HA-Clients gegen lokalen Modbus-Simulator
├── test_economics_dashboard_e2e.py  Ende-zu-Ende bis zum Dashboard: je ein PV-Lade-,
│                                  Netzlade- und Entladeabschnitt von der Tarifauflösung über die
│                                  Herkunftsaufteilung und die Geldsensoren bis zur
│                                  Dashboard-Metadatenauflösung; ein, zwei und acht Tarifpreisfenster
│                                  vom Dashboard-Editor über Tarifmodell und Sensorattribute bis zu den
│                                  Dashboard-States, samt Mitternacht und angrenzenden Grenzen
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
