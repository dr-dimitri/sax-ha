# Vue-Dashboard: Funktionsparität und Prüfnachweise

Das optionale Panel **SAX Power (Vue)** unter `/sax-power-vue` bildet die
fünf Ansichten des mitgelieferten Lovelace-Dashboards `/sax-power` ab. Maßstab
ist deren fachliche Funktion, nicht eine identische Kartenimplementierung.
Die Anforderungen stehen in [anforderung.yaml](../anforderung.yaml), die
Referenzansichten in [dashboard.py](../custom_components/sax_power/dashboard.py).
Die Zuordnung deckt die Issues [#196](https://github.com/dr-dimitri/sax-ha/issues/196)
bis [#203](https://github.com/dr-dimitri/sax-ha/issues/203) sowie die
Vue-Reparatur [#205](https://github.com/dr-dimitri/sax-ha/issues/205) ab.

Die folgenden Schlüssel sind **Entity-Domain und Registry-Suffix**, keine
fest programmierten Entity-IDs. Die tatsächliche ID wird aus dem SAX-Config-Entry
und der Entity Registry aufgelöst. Umbenennungen, deaktivierte optionale
Entitäten und Lese-/Bedienberechtigungen werden dadurch berücksichtigt.

## Gemeinsame Daten- und Bedienregeln

| Funktion | Verhalten | Automatisierte Prüfung |
| --- | --- | --- |
| Zugehörigkeit und Berechtigung | `sax_power/dashboard/subscribe` liefert nur aktive, lesbare SAX-Entitäten des angeforderten Eintrags mit `entity_id`, `domain`, `key`, `name`, `states` und `can_control`. | [Metadaten-API][metadata-tests] |
| Live-Zustände | `hass.states` ist die gemeinsame Datenquelle. HA formatiert Werte; Sprach-/Zeitzoneneinstellungen werden beim Fallback beachtet. | [HA-Kontext][ha-tests], [Allgemein][general-tests] |
| Fehlende Werte | Fehlende Metadaten lassen Zeilen und leere Karten entfallen. Registrierte `unknown`-/`unavailable`-Zustände bleiben erkennbar; es entsteht keine Ersatz-Null. | [Controls][control-tests], alle View-Tests |
| Schalter | `switch.turn_on`/`turn_off` senden den ausdrücklich gewählten Zustand an die aufgelöste ID. | [HA-Kontext][ha-tests], [Controls][control-tests], [Ladeansichten][charging-tests] |
| Zahlen | `number.set_value`; endlicher Wert innerhalb der aktuellen Attribute `min`, `max`, `step`. Eingabe bleibt bis zur Übernahme lokal. | [Controls][control-tests], [Ladeansichten][charging-tests] |
| Uhrzeiten | `time.set_value`; gültiges `HH:MM[:SS]`, ohne eigene Zeitplanberechnung. | [HA-Kontext][ha-tests], [Ladeansichten][charging-tests] |
| Auswahlfelder | `select.select_option`; erlaubte Werte aus `options`, Beschriftung aus den übersetzten Enum-Metadaten. | [Controls][control-tests], [Ladeansichten][charging-tests] |
| Bestätigung und Fehler | Ein laufender Aufruf sperrt alle Bedienelemente derselben Entität. Serviceantworten ersetzen keinen HA-Zustand. Fehler werden angezeigt; es gibt keinen automatischen erneuten Schreibversuch. | [Controls][control-tests], [HA-Kontext][ha-tests], [Ladeansichten][charging-tests] |
| Verbindung und Navigation | Ein gemeinsames Metadatenabo, Aufräumen bei Unmount, erneutes Abonnieren nach Reconnect, kein Schreiben bei Mount, Tabwechsel oder Reconnect. | [Panel][panel-tests], [HA-Kontext][ha-tests], [Browser][browser-tests] |

## Allgemeine Informationen

`GeneralView.vue`, Pfad `allgemein`, Anforderung `REQ-VUE-GENERAL`.
Die Tabellenreihenfolge entspricht der Vue-Anzeige. Ihre Gerätekarte fasst
Energiezähler und Speicherschalter mit den Gerätedaten zusammen; das bestehende
Lovelace-Layout bleibt unverändert.

| Bereich | Domain und Schlüssel | Attribute, Grenzen und Sichtbarkeit | Prüfung |
| --- | --- | --- | --- |
| Ladezustand | `sensor.soc` | Skala 0–100 %, unter 20 rot, ab 20 gelb, ab 50 grün; tatsächlicher Wert und Bereich zusätzlich als Text. | [Allgemein][general-tests]: Grenzwerte, ungültige Zustände, zugänglicher Meter |
| Zelltemperatur | `sensor.storage_max_cell_temp` | Skala 0–40 °C, unter 5 rot, 5 bis unter 32 grün, ab 32 rot. Außerhalb der Skala wird nur der Zeiger begrenzt, der tatsächliche Wert bleibt sichtbar. | [Allgemein][general-tests]: 5-/32-°C-Grenzen und Werte außerhalb der Skala |
| Leistung | `number.max_soc`, `sensor.charge_power`, `sensor.discharge_power`, `sensor.smartmeter_power` | Globaler Max-SOC mit HA-Grenzen; Leistungswerte mit ihren Einheiten. Label für `smartmeter_power`: Netzleistung. | [Allgemein][general-tests], [Ladeansichten][charging-tests]: gemeinsamer Max-SOC |
| Gerät, erste Zeilen | `sensor.energy_charged`, `sensor.energy_discharged` | Vorhandene Energiezähler und ihre Einheiten; keine Frontend-Akkumulation und keine eigene Energie-Karte. | [Allgemein][general-tests]: Anordnung und fehlende optionale Zeilen |
| Gerät | `sensor.sun_version_master`, `sensor.sun_version_gateway`, `sensor.sun_serial_number` | Optionale SunSpec-Daten; fehlende Zeilen und leere Karte werden ausgelassen. | [Allgemein][general-tests]: optionale Geräteinformationen |
| Gerät, Fortsetzung | `sensor.storage_event_text`, `sensor.ic_control_mode_text`, `binary_sensor.cell_calibration_active`, `sensor.next_cell_calibration` | HA-Zustände/Enum-Texte, Steuermodus, Kalibrierstatus und lokalisierter Zeitpunkt. Hersteller, Modell und entfernte Statuskarten werden nicht wieder eingeführt. | [Allgemein][general-tests]: vollständige Reihenfolge, Live-Werte und Zeitformat |
| Gerät, letzte Zeile | `switch.storage_switch` | Übersetzungsschlüssel `storage`; Bestätigungsdialog vor EIN und AUS. Abbrechen/Escape sowie Änderungen von Zustand, ID, Bedienrecht oder Verbindung verwerfen die Auswahl ohne Schreiben; Bestätigung sendet genau einen vorhandenen HA-Service. | [Allgemein][general-tests], [Controls][control-tests], [Browser][browser-tests] |

## Ladeautomatik

`TimedChargingView.vue`, Pfad `ladeautomatik`, Anforderung `REQ-VUE-CHARGING`.

| Reihenfolge | Domain und Schlüssel | Darstellung und Verhalten | Prüfung |
| --- | --- | --- | --- |
| Hauptschalter | `switch.timed_charge_enabled` | Übersetzter Name „Netzladung aktiv“. | [Ladeansichten][charging-tests]: vollständige Reihenfolge |
| Zeitfenster | `time.timed_charge_start`, `time.timed_charge_end` | Start und Ende; auch 22:00 bis 06:00 wird ausschließlich an die beiden Time-Entities übergeben. | [Ladeansichten][charging-tests]: Zeitfenster über Mitternacht |
| Direkt danach: Entladestatus | `sensor.timed_charge_discharge_status` | `normal` → Normalbetrieb, `discharge_blocked` → Entladung wg. Netzladen gestoppt, `grid_charging` → Netzladen. | [Ladeansichten][charging-tests]: alle drei Live-Statuswechsel |
| Einstellungen | `number.timed_charge_max_soc`, danach `number.timed_charge_min_soc` | Netzladeziel und Startschwelle. Die Obergrenze des Ziels folgt dessen HA-`max`-Attribut; kein zusätzlicher globaler Max-SOC in diesem Tab. | [Ladeansichten][charging-tests]: geänderte Grenze, ungültiger und gültiger Zielwert |
| Aktive Monate | `switch.timed_charge_month_1` bis `switch.timed_charge_month_12` | Januar, Februar, März, April, Mai, Juni, Juli, August, September, Oktober, November, Dezember; Namen aus Metadaten. | [Ladeansichten][charging-tests]: zwölf Namen DE/EN, HA-bestätigte Monatsänderung und Kalenderwechsel ohne Frontend-Aktion |

Vue entscheidet weder über Ladeberechtigung noch über die laufende
Sollwertwiederholung. Beides verbleibt bei `REQ-TIMED-SOC-CHARGE` im Backend.

## Netzdienliches Laden

`GridServingView.vue`, Pfad `netzdienliches-laden`, Anforderung `REQ-VUE-CHARGING`.

| Reihenfolge | Domain und Schlüssel | Darstellung und Verhalten | Prüfung |
| --- | --- | --- | --- |
| Hauptschalter | `switch.grid_serving_enabled` | „Netzdienliches Laden aktiv“. | [Ladeansichten][charging-tests] |
| Ladepause, Beginn/Ende | `time.grid_serving_start`, `time.grid_serving_end` | „Start“ und „Ende“ innerhalb der ausdrücklich als Ladepause bezeichneten Karte. | [Ladeansichten][charging-tests]: Label, Reihenfolge und Mitternacht |
| Ladepause, Prognose | `sensor.grid_serving_forecast` | Dynamischer `friendly_name` mit Tagesbezug und Einheit kWh; keine Berechnung in Vue. | [Ladeansichten][charging-tests]: Namenswechsel und nicht verfügbare Prognose |
| Ladepause, Schwelle | `number.grid_serving_forecast_threshold` | „Mindest PV-Prognose“ mit HA-`min`/`max`/`step` und kWh. | [Ladeansichten][charging-tests], [Controls][control-tests] |
| Ladepause, Status | `sensor.grid_serving_pause_status` | Bestehender HA-Statustext. | [Ladeansichten][charging-tests]: Live-Status |
| Aktive Monate | `switch.grid_serving_month_1` bis `switch.grid_serving_month_12` | Dieselben zwölf übersetzten Kalendermonate in numerischer Reihenfolge. | [Ladeansichten][charging-tests]: Namen, Bedienung, Kalenderwechsel |

Es gibt weder eine zusätzliche Einstellungen-Karte noch einen globalen
Max-SOC-Regler. Die Pausenentscheidung bleibt bei `REQ-GRID-SERVING-CHARGE`.

## Dynamisches Laden

`DynamicChargingView.vue`, Pfad `dynamisches-laden`, Anforderung
`REQ-VUE-DYNAMIC-CHARGING`. Vor der Karte steht
`switch.price_charge_enabled` mit dem vollständigen Namen
„Preisoptimiertes Laden aktiv“. Die Karte „Preisoptimiertes Laden“ enthält:

| Nr. | Domain und Schlüssel | Label und Datenquelle | Prüfung |
| --- | --- | --- | --- |
| 1 | `select.price_charge_strategy` | Strategie; `options` und übersetzte Werte für `off`, `absolute`, `relative`, `smart`. | [Ladeansichten][charging-tests]: alle Strategien und tatsächliches Serviceziel |
| 2 | `number.price_charge_max_price` | Netzbezug und Laden bis; negative Preise innerhalb der HA-Grenzen, aktuelle Einheit. | [Ladeansichten][charging-tests]: negative Eingabe, geänderte Einheit, Grenzen/Schrittweite |
| 3 | `number.price_charge_neutral_price` | Netzbezug ohne Laden bis; gleiche gemeinsame Validierung. | [Ladeansichten][charging-tests]: Fehler, expliziter Wiederholungsversuch, bestätigter Altwert |
| 4 | `number.price_charge_hours` | Anzahl Stunden; aktuelle HA-Grenzen und Einheit. | [Ladeansichten][charging-tests], [Controls][control-tests] |
| 5 | `number.max_soc` | Derselbe globale Max-SOC wie unter Allgemein und in Lovelace. | [Ladeansichten][charging-tests]: gemeinsamer Zustand und laufender Aufruf in beiden Vue-Views; [HA-E2E][parallel-tests] |
| 6 | `sensor.price_charge_active_text` | Aktiv; bestehender HA-Text. | [Ladeansichten][charging-tests]: Reihenfolge und Zustände |
| 7 | `sensor.price_charge_status_text` | Status, einschließlich deaktivierter Automatik. | [Ladeansichten][charging-tests]: deaktivierter Zustand |
| 8 | `sensor.grid_serving_forecast` | Dynamischer Tagesname und kWh. | [Ladeansichten][charging-tests]: Live-Name und HA-Formatierung |
| 9 | `sensor.price_charge_next_start` | Nächster Start; HA-Zeitzone, Sprache und Zeitformat. `unknown` bleibt unbekannt. | [Ladeansichten][charging-tests]: lokaler Zeitstempel und unbekannter Start |
| 10 | `sensor.price_charge_current_price` | Aktueller Strompreis mit tatsächlicher Einheit; fehlender Preis bleibt nicht verfügbar. | [Ladeansichten][charging-tests]: negativer und fehlender Preis |

Der Frontend-Test vergleicht diese zehn Schlüssel direkt mit `dashboard.py`.
Vue ermittelt keine Strategie oder Ladezeiten; `REQ-DYNAMIC-PRICE-CHARGE`
bleibt die fachliche Implementierung.

## Ersparnis

`SavingsView.vue`, Pfad `ersparnis`, Anforderung `REQ-VUE-SAVINGS`.
Alle Geldbeträge haben zwei Nachkommastellen, Tarifpreise vier; gerundet wird
erst für die Anzeige. Die interne Bilanz bleibt unverändert.

| Block, Reihenfolge | Domain/Schlüssel bzw. Attribute | Sichtbarkeit und Bedeutung | Prüfung |
| --- | --- | --- | --- |
| 1. Amortisation | `binary_sensor.economics_investment_configured` | `off`: Konfigurationshinweis; `on`: vorhandene Amortisationsdaten. Ein fehlender/unbekannter Zustand erfindet weder Kosten noch Fortschritt. | [Ersparnis][savings-tests]: fehlende Investition und fehlende optionale Entitäten |
| Fortschritt | `sensor.economics_amortization_progress` | Blaue Anzeige mit Text und zugänglichem Meter; nur die grafische Breite wird auf 0–100 % begrenzt. | [Ersparnis][savings-tests]: Genauigkeit und fehlender Wert |
| Restbetrag | `sensor.economics_remaining_to_payback` | Eigene Zeile, wenn die Entity existiert. | [Ersparnis][savings-tests]: Blockreihenfolge und Geldformat |
| Vorlaufbetrag | `sensor.economics_roi`, Attribut `prior_result_eur`, Fallback `prior_result_eur_formatted` | „Bereits vor Bilanzbeginn berücksichtigt“; verändert keine Kalender-/Zeitraumstatistik. | [Ersparnis][savings-tests], [Recorder-Adapter][statistics-tests] |
| Netto-Ergebnis | `sensor.economics_net_savings` | Bilanzierter, auch negativer Wert. Fehlt die Entity, entfallen ihre Detailzeile, Kalenderwerte, freie Auswertung und sämtliche Statistikabfragen. | [Ersparnis][savings-tests]: negative Werte und fehlende Ergebnis-Entity |
| Bilanzbeginn | `sensor.economics_status`, Attribut `economics_started_at` | Lokalisierter Zeitpunkt; Recorder-Historie kann später beginnen. | [Ersparnis][savings-tests]: lokale Zeit und optionale Zeile |
| 2. Kalenderwerte | Recorder von `economics_net_savings`: `change` für Tag, Woche, Monat, Jahr | Heute/Woche/Monat/Jahr bisher; HA-Kalendergrenzen und konfigurierter Wochenbeginn. Keine rollierende Bilanz und keine Differenz eigener Live-Werte. | [Recorder-Adapter][statistics-tests]: Vergleich mit denselben nativen Recorder-Abfragen |
| 3. Tarifplan | `sensor.economics_current_import_price`, Attribut `tariff_type` | Nur bei `time_of_use`, reagiert auf Tarifwechsel ohne Dashboard-Neubau. | [Ersparnis][savings-tests]: Live-Tarifwechsel |
| Tarifzeitfenster | `windows[].start`, `windows[].end`, `windows[].price_eur_kwh`, `active_window` | Planreihenfolge und aktive Markierung aus HA. Zeiten werden dargestellt, nicht neu bewertet. | [Ersparnis][savings-tests]: Fensterwechsel und Preisformat |
| Weitere Tarifdaten | `base_price_eur_kwh`, `feed_in_price_eur_kwh`, `next_price_change_at`, `unavailable_reason` | Grundpreis, Einspeisevergütung, nächster Wechsel oder Nichtverfügbarkeitsgrund. Fehlender Preis wird nicht als gültiger aktiver Grundpreis markiert. | [Ersparnis][savings-tests]: fehlender Preis/Grundpreis, vier Nachkommastellen |
| 4. Freier Zeitraum | Ein Paar `start_date`/`end_date`, Recorder-`change` derselben Netto-Entity | Beide Tage vollständig in HA-Zeitzone; ausdrücklich übernehmen. Ein Zeitraum steuert Kennzahl und Balkendiagramm, inklusive negativer Werte und Datenlücken. | [Ersparnis][savings-tests], [Recorder-Adapter][statistics-tests], [Browser][browser-tests] |
| Diagramm | Native `statistics_during_period`-Buckets mit `start`, `end`, `change` | Stunden/Tage/Monate entsprechend der Auswahl; reale zeitliche Positionen auch bei DST/Lücken; beschriftetes SVG plus aufklappbare Tabelle. | [Ersparnis][savings-tests], [Recorder-Adapter][statistics-tests], [Browser][browser-tests] |
| 5. Erklärung | „Hinweise zur Berechnung und Datenbasis“ | Anfangs eingeklappt; erklärt Netto-Bilanz, Aufzeichnungsbeginn, negative Werte, fehlende Historie und Bilanzneustart. | [Ersparnis][savings-tests] |
| 6. Wirtschaftsstatus | `sensor.economics_status` | `active`: kein Hinweis. `disabled`, `price_unavailable`, `origin_unavailable`, `partial_price_coverage`, `storage_error`: je ein passender Hinweis. Fehlend/unknown/unavailable/unbekannter Status: ein Verfügbarkeitshinweis. | [Ersparnis][savings-tests]: alle Statuszweige |

### Native Recorder-Semantik

Der authentifizierte Befehl `sax_power/dashboard/statistics` löst ausschließlich
die Netto-Ersparnis des angefragten SAX-Eintrags auf. Er prüft Leseberechtigung
und Zuordnung vor und nach der asynchronen Datenbankabfrage. Er verwendet den
Recorder-Executor und folgende native HA-Auswertungen:

| Auswertung | Native Funktion und Grenzen | Nachweis |
| --- | --- | --- |
| Kalenderkennzahlen | `resolve_period` für Tag/Woche/Monat/Jahr, dann `statistic_during_period(..., {"change"}, ...)`; `first_weekday` aus HA-Einstellung beziehungsweise Sprache. | [Recorder-Adapter][statistics-tests]: Kalenderdaten und Wochenbeginn |
| Freie Kennzahl | `statistic_during_period`; lokale Mitternacht am Anfang, exklusives Ende am Folgetag. | [Recorder-Adapter][statistics-tests]: exakt dieselbe Datenbank und dieselben Grenzen |
| Freier Graph | `statistics_during_period`; native Energy-Endgrenze eine Millisekunde vor der Folgemitternacht, Auflösungsheuristik aus HA-`getSuggestedPeriod` auf den gewählten HA-lokalen Kalendertagen. | [Recorder-Adapter][statistics-tests]: Stunden-, Tages- und Monatsauswahl |
| Sommerzeit | Europa/Berlin, 29.03.2026 mit 23 Stunden, 25.10.2026 mit 25 Stunden; auch mehrtägige Auswahl über den Wechsel. | [Recorder-Adapter][statistics-tests]: parametrisierte echte Recorder-Fixtures |
| Negatives Ergebnis und Neustart | Signierte `change`-Werte einschließlich `state_class=total` und geändertem `last_reset`. | [Recorder-Adapter][statistics-tests]: echte Sensor-/Recorder-Kompilierung |
| Fehlende Daten und Sicherheit | Kein Ersatz aus dem Live-Sensor; explizite leere Ergebnisse, fehlender Recorder, Rechteentzug, umbenannte/entfernte Entity und Fehler. | [Recorder-Adapter][statistics-tests], [Ersparnis][savings-tests] |
| Aktualisierung | `recorder_5min_statistics_generated`, Reconnect oder manuell. Verspätete Antworten einer alten Auswahl bzw. Verbindung werden verworfen. | [Ersparnis][savings-tests]: Race-, Abmelde- und Reconnect-Fälle |

Eine Kennzahl kann bereits eine jüngere Fünf-Minuten-Randperiode enthalten,
während im Graphen nur die abgeschlossenen Stunden sichtbar sind. Das entspricht
den nativen HA-Karten. Die Kennzahl wird daher **nicht aus Balken summiert**.
Vorlaufbeträge erzeugen keine Recorder-Vorgeschichte. Ohne Aufzeichnung, etwa
bei ausgeschlossenem Sensor, bleibt die Auswertung leer beziehungsweise nicht
verfügbar. Ein kontrollierter Bilanzneustart kann signierte Änderungen beider
Bilanzabschnitte innerhalb derselben Auswahl ergeben.

Die Kalendergrenzen und Auflösungsentscheidung des Adapters verwenden bewusst
die konfigurierte **HA-Zeitzone**. Das native HA-Frontend kann bei der
Auflösungsentscheidung die Browser-Zeitzone berücksichtigen. Bei davon
abweichender Browser-Zeitzone wird daher keine identische Wahl der
Balkenauflösung behauptet. Die Recorder-Tests belegen die gleichen Ergebnisse
für dieselben Grenzen und dieselbe angeforderte Auflösung, einschließlich
der Sommerzeitfälle in Europa/Berlin.

## Parallelbetrieb, Lebenszyklus und Reparaturen

| Fall | Erwartetes Verhalten | Prüfung |
| --- | --- | --- |
| Neuinstallation und Bestandsinstallation | Vue bleibt ein unabhängiges Opt-in; alle Kombinationen mit der Lovelace-Einmalanlage sind gültig. Optionen haben Vorrang vor Setup-Daten. | [Config Flow](../tests/test_config_flow.py), [Initialisierung](../tests/test_init.py) |
| Aktivieren, Deaktivieren, Reload, Unload, Neustart | Ein eigenes Panel, einmalige statische Route pro HA-Lauf; Abschalten entfernt nur den eigenen Vue-Eintrag. | [Panel-Lebenszyklus][lifecycle-tests], [Vue-Reparaturen][repair-tests], [Neustart][restart-tests] |
| Zwei Oberflächen | Zwei echte HA-WebSocket-Clients sehen Änderungen aus beiden Richtungen. Das Öffnen liest/schreibt keine zusätzlichen Register; eine Aktion verursacht genau ihren bestehenden Geräteaufruf. | [HA-E2E mit Modbus-Simulator][parallel-tests] |
| Lovelace-Erstellung/-Neuinstallation | `sax_power.create_dashboard` und `sax_power.reinstall_dashboard` erhalten Bedeutung und Ziel. Eigene Lovelace-Anpassungen werden nur bei ausdrücklichem Neuaufbau ersetzt. | [Lovelace-Dashboard](../tests/test_dashboard.py), [HA-E2E][parallel-tests] |
| Lovelace-Veraltet-Reparatur | Betrifft das vorhandene Storage-Dashboard; der Vue-Panelstand bleibt unabhängig. | [Lovelace-Reparaturen](../tests/test_repairs.py), [HA-E2E][parallel-tests] |
| Vue-Bundlewechsel | SHA-256 erkennt neue Inhalte auch bei unveränderter Manifestversion; registriert erst bei Bestätigung den aktuellen Stand. Anschließendes vollständiges Browser-Neuladen ist ein eigener Dialogschritt. | [Vue-Reparaturen][repair-tests], [Paket-Worker][package-worker] |
| Ablehnen, Fehler, alter Dialog | Ablehnen unterdrückt nur denselben Stand. Fehler sind wiederholbar; ein alter Dialog quittiert kein neues Update. Fremde Panels, deaktivierte/entfernte Einträge und Reconfigure sind berücksichtigt. | [Vue-Reparaturen][repair-tests], [Panel-Lebenszyklus][lifecycle-tests] |

Der native HA-E2E-Test verwendet einen **lokalen Modbus-TCP-Simulator**, keine
physische Batterie. Die Browserprüfungen verwenden einen simulierten HA-Kontext.
Zusammen prüfen sie Darstellung/Bedienung und deren echte HA-Protokoll- und
Integrationsgrenze; ein vollständiger Browserlauf gegen eine produktive
HA-Installation wird dadurch nicht behauptet.

## Build-, Browser- und Paketprüfungen

Die Testbasis ist **Home Assistant 2026.8.2**,
**home-assistant-frontend 20260729.7**, **Python 3.14**. Die verbindlichen Pins
stehen in [requirements_test.txt](../requirements_test.txt), der HA-Mindeststand
in [hacs.json](../hacs.json). CI verwendet diese Versionen. Neue HA-Versionen
benötigen insbesondere bei Änderungen an Recorder-/Frontend-APIs einen erneuten
Paritätslauf; sie werden hier nicht pauschal als geprüft bezeichnet.

| Prüfung | Umfang und Ausführung |
| --- | --- |
| Python | `pytest -v`, `ruff check custom_components scripts tests`, `black --check custom_components scripts tests`; reale Hardwaretests werden ohne verfügbares Testgerät übersprungen. |
| Frontend | Im Verzeichnis `frontend`: `npm ci`, `npm run check`, `npm test`, `npm run build`; Build enthält den Test des echten ES-Moduls ohne Node-Laufzeitglobals im Browser. |
| Chromium | `npx playwright install chromium`, dann `npm run test:browser`; [Konfiguration](../frontend/playwright.config.ts) und [Testfälle][browser-tests]. Vier Projekte: Desktop 1440×1000 und Smartphone 390×844, jeweils DE/hell und EN/dunkel. |
| Browserdaten | `browser/server.mjs` liefert das **Produktionsbundle** unter `127.0.0.1:5190`; eine ausdrücklich als Vorschau gekennzeichnete HA-Fixture liefert die Testzustände. Geprüft werden alle Tabs, Bedienung, Fokus/Tastatur, History/Reload, Fehler, Reconnect, Zeitfenster und Datumswahl. |
| CI-Artefakte | Der Browserlauf erzeugt Screenshots aller fünf Ansichten je Projekt sowie Berichte und Fehlertraces im Artefakt `vue-dashboard-browser-report`. Das Vorhandensein einer Testdefinition allein belegt noch keinen erfolgreichen Lauf. |
| Reproduzierbarkeit | CI baut aus `package-lock.json` und vergleicht das komplette Verzeichnis `custom_components/sax_power/frontend` mit Git. Keine nicht eingecheckten Zusatzassets; Vue und Styles sind im lokalen Modul enthalten. |
| Saubere Installation | [Pakettests][package-tests] installieren ein GitHub-Stable-Quellarchiv mit Wurzelpräfix sowie ein Snapshot-ZIP in getrennte temporäre Bäume und starten isolierte Python-Prozesse. |

Ein tatsächlich heruntergeladenes Paket wird vom Repository-Root aus geprüft:

```sh
.venv/bin/python -I scripts/verify_dashboard_package.py /tmp/sax-power-paket.zip
```

[Der Helper](../scripts/verify_dashboard_package.py) benötigt die Python-
Testabhängigkeiten auf dem Testrechner. Sein [Worker][package-worker] prüft
Paketimporte ohne Repository-Fallback, Manifest, Lizenz, DE/EN-Übersetzungen,
die echte lokale HA-HTTP-Auslieferung des Bundles und den nativen
Reparaturablauf nach einem Bundlewechsel. Die neuen HTTP-Bytes müssen zur
neuen Hash-URL passen. Node, Entwicklungsserver, CDN und Modbus werden dabei
nicht benötigt. Das JSON-Ergebnis enthält Manifestversion, ZIP-SHA-256,
Asset-SHA-256, Dateianzahl und Ergebnis. Die JS-Ausführung selbst wird separat
im Produktionsmodul- und Browserlauf geprüft.

### Abnahme der Gerätekarte und Schaltbestätigung

[Commit 639695e5e347](https://github.com/dr-dimitri/sax-ha/commit/639695e5e3479f802c568704f3ae34f3e5bd473c)
bestand am 12.09.2026 den vollständigen
[CI-Lauf 34683284222](https://github.com/dr-dimitri/sax-ha/actions/runs/34683284222):
Python, Ruff/Black, Release-Metadaten, HACS, hassfest, Frontend-Typen und
Formatierung, **199 Komponententests**, Produktionsmodul-Smoke und
reproduzierbarer Build. Lokal bestanden **1.813 Python-Tests** bei zwei
erwarteten Hardware-Skips; es fand kein Test an einer echten Batterie statt.

Alle **24 Browserfälle** bestanden ohne Wiederholung oder übersprungene Fälle.
Die zusätzliche Prüfung bestätigt in allen vier Browserprojekten beide
Schaltrichtungen, Abbrechen, Escape und Enter auf der vorausgewählten
Abbruchaktion. Vor ausdrücklicher Bestätigung bleibt der HA-Zustand erhalten
und es wird kein Service aufgerufen. Die neuen Screenshots unten stammen aus
diesem Browserbericht und zeigen das gebaute Produktionsmodul mit simuliertem
HA-Kontext. Die 13 zusätzlichen Komponententests prüfen außerdem ungültig
gewordene Dialoge und doppelte Bestätigungen.

### Frühere Paketabnahme vom 12.09.2026

Der folgende Nachweis betrifft den Stand vor der geänderten allgemeinen
Gerätekarte und deren Schalterbestätigung. Er ist keine Abnahme dieser
anschließenden Änderungen.

Am 12.09.2026 wurde
[Commit acb49d089767](https://github.com/dr-dimitri/sax-ha/commit/acb49d089767f45bc25cbaa41c47728f083a1a84)
in [CI-Lauf 34681752310](https://github.com/dr-dimitri/sax-ha/actions/runs/34681752310)
erfolgreich geprüft: Python, Ruff/Black, HACS, hassfest, Frontend-Typen und
Formatierung, 186 Komponententests, Produktionsmodul-Smoke, reproduzierbarer
Build sowie alle **20 Browserfälle ohne Wiederholung oder übersprungene Fälle**.
Die Browserabnahme verwendet Chromium mit simulierten HA-Antworten; echte
HA-WebSockets, Recorder, Storage und Modbus-Simulator werden separat geprüft.
Ein Test an einer echten Batterie fand nicht statt; die zwei Hardwaretests
wurden erwartungsgemäß übersprungen.

Das damalige Paket `snapshot-pr-204-acb49d089767` wurde heruntergeladen und
mit `verify_dashboard_package.py` in einer frischen
HA-Umgebung installiert. **Ergebnis: bestanden**, einschließlich vollständigem
Reparaturablauf, neuer Bundle-Hash-URL und identischen ausgelieferten HTTP-Bytes.
Der Helper bestätigte 57 installierte Dateien ohne Rückgriff auf das Repository.
Tag und Prüfsummen bezeichnen den historischen Prüfgegenstand; sie sind kein
Verweis auf eine dauerhaft bereitgehaltene Snapshot-Veröffentlichung. Der
Commit- und CI-Nachweis bleibt davon unabhängig.

| Nachweis | Wert |
| --- | --- |
| Manifest des getesteten Snapshots | `2.0.3-snapshot.pr204.shaacb49d089767` |
| SHA-256 des heruntergeladenen Snapshot-ZIPs | `d0f406fd06d367dbf82b30cd197e0f0e4dbde5521e26f1b77c9756fbbfd72ac3` |
| SHA-256 des getesteten Vue-Bundles | `dc3d1df0032f8e6d8ba500c2ffb942e8f463188c016202932fbdcb1d419ac1dd` |
| GitHub-Quellarchiv, ebenfalls isoliert bestanden | [Commit c6563461ee36](https://github.com/dr-dimitri/sax-ha/commit/c6563461ee3662c858ca318f41ab20462f71bf5f), Manifest `2.0.3`, identisches Vue-Bundle |
| SHA-256 dieses Quellarchivs | `f5cfcf7904db9681f25d52a872ad0d75c47872866784ea1f97ee1a62bf4f037b` |

Die drei zusätzlichen [Neustarttests][restart-tests] schreiben Config-Entry-Daten
und Optionen über den regulären HA-Final-Write und laden sie in einer zweiten
HA-Instanz erneut aus dem Storage. Sie prüfen Aktivierung, Vorrang einer späteren
Deaktivierung und ein während des Stillstands installiertes Bundle samt neuem
Reparaturhinweis. Geräte- und Plattformgrenzen sind dabei gemockt; Storage,
Config-Entry-Laden, Panel und Issue Registry sind echt. Die anschließend erneut
ausgeführte lokale Gesamtsuite ergab **1.813 bestandene Tests und zwei erwartete
Hardware-Skips**; Ruff und Black sind erfolgreich.

### Screenshots

Die Bilder der allgemeinen Informationen und der Schaltbestätigung stammen aus
CI-Lauf 34683284222. Die übrigen Ansichten stammen aus dem früheren Lauf
34681752310 und bleiben unverändert. Der
hell abgesetzte Testbereich kennzeichnet simulierte Daten und zeigt beide
Dashboard-Einstiege; der Link innerhalb des Vue-Panels führt ebenfalls zu
Lovelace. Die native Darstellung von Zeit- und Datumsfeldern folgt dem Browser,
während Beschriftungen und bestätigte Werte die HA-Sprache verwenden.

| Ansicht | Desktop, Deutsch, hell | Smartphone, Englisch, dunkel |
| --- | --- | --- |
| Allgemeine Informationen | [Screenshot](images/vue-allgemein-desktop-light-de.png) | [Screenshot](images/vue-allgemein-mobile-dark-en.png) |
| Speicher ausschalten – Bestätigung | [Screenshot](images/vue-storage-confirm-off-desktop-light-de.png) | [Screenshot](images/vue-storage-confirm-off-mobile-dark-en.png) |
| Speicher einschalten – Bestätigung | [Screenshot](images/vue-storage-confirm-on-desktop-light-de.png) | [Screenshot](images/vue-storage-confirm-on-mobile-dark-en.png) |
| Ladeautomatik | [Screenshot](images/vue-ladeautomatik-desktop-light-de.png) | [Screenshot](images/vue-ladeautomatik-mobile-dark-en.png) |
| Netzdienliches Laden | [Screenshot](images/vue-netzdienliches-laden-desktop-light-de.png) | [Screenshot](images/vue-netzdienliches-laden-mobile-dark-en.png) |
| Dynamisches Laden | [Screenshot](images/vue-dynamisches-laden-desktop-light-de.png) | [Screenshot](images/vue-dynamisches-laden-mobile-dark-en.png) |
| Ersparnis | [Screenshot](images/vue-ersparnis-desktop-light-de.png) | [Screenshot](images/vue-ersparnis-mobile-dark-en.png) |

<details>
<summary>Alle fünf Desktopansichten anzeigen</summary>

![Allgemeine Informationen mit simulierten HA-Daten](images/vue-allgemein-desktop-light-de.png)

![Ladeautomatik mit simulierten HA-Daten](images/vue-ladeautomatik-desktop-light-de.png)

![Netzdienliches Laden mit simulierten HA-Daten](images/vue-netzdienliches-laden-desktop-light-de.png)

![Dynamisches Laden mit simulierten HA-Daten](images/vue-dynamisches-laden-desktop-light-de.png)

![Ersparnis mit simulierten HA-Daten](images/vue-ersparnis-desktop-light-de.png)

</details>

[metadata-tests]: ../tests/test_dashboard_api.py
[ha-tests]: ../frontend/tests/ha.test.ts
[control-tests]: ../frontend/tests/controls.test.ts
[general-tests]: ../frontend/tests/general.test.ts
[charging-tests]: ../frontend/tests/charging.test.ts
[savings-tests]: ../frontend/tests/savings.test.ts
[panel-tests]: ../frontend/tests/panel.test.ts
[browser-tests]: ../frontend/browser/dashboard.spec.ts
[statistics-tests]: ../tests/test_dashboard_statistics.py
[parallel-tests]: ../tests/test_vue_dashboard_e2e.py
[lifecycle-tests]: ../tests/test_vue_dashboard.py
[repair-tests]: ../tests/test_vue_dashboard_repairs.py
[package-tests]: ../tests/test_frontend_package.py
[package-worker]: ../scripts/dashboard_package_smoke.py
[restart-tests]: ../tests/test_vue_dashboard_restart.py
