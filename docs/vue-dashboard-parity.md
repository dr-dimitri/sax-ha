# Dashboard SAX Power: Funktionen und Prüfnachweise

Das optionale Panel **SAX Power** unter `/sax-power-vue` ist das einzige
mitgelieferte Dashboard. Es verwendet Vue; der kompatible URL-Pfad und die
technischen Schlüssel bleiben erhalten. Die Aktivierungsoption ist
standardmäßig ausgeschaltet. Die Anforderungen stehen in
[anforderung.yaml](../anforderung.yaml), die Views unter
[frontend/src/views](../frontend/src/views).

Die folgende Matrix beschreibt die aktuelle Implementierung der Issues
[#196](https://github.com/dr-dimitri/sax-ha/issues/196) bis
[#203](https://github.com/dr-dimitri/sax-ha/issues/203) sowie die
Dashboard-Reparatur [#205](https://github.com/dr-dimitri/sax-ha/issues/205).
Die Lovelace-Anforderungen sind abgelöst; bereits in Home Assistant gespeicherte
Dashboards und Karten bleiben beim Upgrade erhalten. Die Entfernung des alten
Builders verändert keine Geräte-Entitäten, Services zur Gerätesteuerung oder
Tarifkonfiguration.

Die Navigation verwendet folgende Reihenfolge und Namen:

| Deutsch | Englisch | Pfad unter `/sax-power-vue` |
| --- | --- | --- |
| Allgemeine Informationen | General information | `allgemein` |
| Zeitvariabler Tarif | Time-of-use tariff | `ladeautomatik` |
| Dynamischer Tarif | Dynamic tariff | `dynamisches-laden` |
| Netzdienliches Laden | Grid-serving charging | `netzdienliches-laden` |
| Amortisation | Amortization | `ersparnis` |

Die folgenden Schlüssel sind **Entity-Domain und Registry-Suffix**, keine
fest programmierten Entity-IDs. Die tatsächliche ID wird aus dem SAX-Config-Entry
und der Entity Registry aufgelöst. Umbenennungen, deaktivierte optionale
Entitäten und Lese-/Bedienberechtigungen werden dadurch berücksichtigt.

## Gemeinsame Daten- und Bedienregeln

Breite Ansichten verwenden ein kompaktes Layout anhand der tatsächlich
verfügbaren Panelbreite: zwei Kartenspalten ab 860 px Inhaltsbreite.
Die Monatsauswahl startet als kompakte Zusammenfassung. Aufgeklappt stehen
vier Quartalsgruppen auf dem Smartphone in einer Spalte und bei ausreichendem
Platz in zwei Spalten, mit mindestens 14 px großen Namen und 44 × 44 px großen
Bedienflächen. Die sichtbare native Checkbox misst nur 22 × 22 px; ihr
zugeordnetes Label macht auch den umgebenden Bereich anklickbar. Die Reihenfolge
Januar bis Dezember bleibt im DOM und bei Tastaturbedienung unverändert. Die Geräteübersicht ordnet Skalen
und Leistung links neben den Gerätedaten an. Amortisation gruppiert Fortschritt
und Kalenderwerte neben dem Tarif; die freie Auswertung nutzt die volle Breite.
Die Darstellung passt sich der verfügbaren Breite an. Beschriftungen und Werte
werden nicht abgeschnitten, die Bedienflächen von Eingaben und Schaltflächen
bleiben mindestens 44 px hoch.

Gültige Softwarekonfiguration bestätigt Serviceantwort und HA-Zustand ohne
Warten auf die Geräteauswertung. Das gilt für die drei Ladehauptschalter,
Monate, Max-SOC, Netzladeziel/Min-SOC, Preisgrenzen, Anzahl Stunden, Strategie,
Prognoseschwelle sowie einzelne und atomare Zeitfenster. Der Coordinator
merkt die Konfiguration sofort zum Speichern vor und wertet den neuesten
Stand im gemeinsamen Worker unter dem Control-Lock aus. Eine bestätigte
Konfiguration beschreibt den angenommenen Anwenderwert; Aktivitäts- und
Gerätezustände folgen weiterhin der quittierten Steuersequenz.
Implementierungsgrenzen und Ablauf stehen in `REQ-VUE-ENTITY-BINDING` und
[DEVELOPMENT.md](../DEVELOPMENT.md).

In den beiden Tarif-Tabs entfällt „Bestätigter Wert:“ (EN: „Confirmed value:“)
vor den bestätigten Bedienwerten. Die Werte bleiben auch beim Bearbeiten und
bis zur HA-Bestätigung sichtbar und zugänglich. Die gemeinsame Zeitfenster-Zeile
„Bestätigt:“ sowie die Beschriftungen anderer Ansichten bleiben erhalten.

| Funktion | Verhalten | Automatisierte Prüfung |
| --- | --- | --- |
| Zugehörigkeit und Berechtigung | `sax_power/dashboard/subscribe` liefert nur aktive, lesbare SAX-Entitäten des angeforderten Eintrags mit `entity_id`, `device_id`, `domain`, `key`, `name`, `states` und `can_control`. | [Metadaten-API][metadata-tests] |
| Live-Zustände | `hass.states` ist die gemeinsame Datenquelle. HA formatiert Werte; Sprach-/Zeitzoneneinstellungen werden beim Fallback beachtet. | [HA-Kontext][ha-tests], [Allgemein][general-tests] |
| Fehlende Werte | Fehlende Metadaten lassen normale Entity-Zeilen und leere Karten entfallen. In der Monatsauswahl bleiben fehlende Monate ausdrücklich erkennbar. Registrierte `unknown`-/`unavailable`-Zustände bleiben erkennbar; es entsteht keine Ersatz-Null. | [Controls][control-tests], alle View-Tests |
| Schalter | `switch.turn_on`/`turn_off` senden den ausdrücklich gewählten Zustand an die aufgelöste ID. | [HA-Kontext][ha-tests], [Controls][control-tests], [Ladeansichten][charging-tests] |
| Zahlen | `number.set_value`; endlicher Wert innerhalb der aktuellen Attribute `min`, `max`, `step`. Eingabe bleibt bis zur Übernahme lokal. | [Controls][control-tests], [Ladeansichten][charging-tests] |
| Uhrzeiten | Eingabe `HH:MM` mit `step=60`, explizite Übernahme als `HH:MM:00`, ohne eigene Zeitplanberechnung. Beide produktiven Zeitfenster übernehmen ihr vollständiges Paar über `sax_power.set_timed_charge_window` beziehungsweise `sax_power.set_grid_serving_window`; die allgemeine Einzelzeit-Komponente verwendet weiterhin `time.set_value`. | [HA-Kontext][ha-tests], [Ladeansichten][charging-tests] |
| Auswahlfelder | `select.select_option`; erlaubte Werte aus `options`, Beschriftung aus den übersetzten Enum-Metadaten. | [Controls][control-tests], [Ladeansichten][charging-tests] |
| Bestätigung und Fehler | Ein laufender Aufruf sperrt alle Bedienelemente derselben Entität; eine gemeinsame Zeitfensteraktion sperrt beide Grenzen. Serviceantworten ersetzen keinen HA-Zustand. Fehler werden angezeigt; es gibt keinen automatischen erneuten Schreibversuch. | [Controls][control-tests], [HA-Kontext][ha-tests], [Ladeansichten][charging-tests] |
| Softwarekonfiguration | HA bestätigt angenommene Einstellungen unabhängig von Control-Lock und Modbus; Geräteaktivität erfordert weiterhin die quittierte Steuersequenz. | [Konfigurationsantworten][control-response-tests], [HA-E2E][ha-e2e-tests] |
| Beschriftung der Tarifwerte | Beide Tarif-Tabs zeigen bestätigte Werte ohne „Bestätigter Wert:“/„Confirmed value:“; lokale Entwürfe ersetzen diese nicht. Gemeinsame Zeitfenster-Bestätigung und andere Ansichten bleiben erhalten. | [Controls][control-tests], [Ladeansichten][charging-tests] |
| Verbindung und Navigation | Ein gemeinsames Metadatenabo, Aufräumen bei Unmount, erneutes Abonnieren nach Reconnect, kein Schreiben bei Mount, Tabwechsel oder Reconnect. | [Panel][panel-tests], [HA-Kontext][ha-tests], [Browser][browser-tests] |

Die bestätigten Hauptschalter `timed_charge_enabled` und
`price_charge_enabled` steuern die Tarifnavigation: `on/off` zeigt nur
Zeitvariabler Tarif, `off/on` nur Dynamischer Tarif und `off/off` beide.
Fehlende, unbekannte, nicht verfügbare oder widersprüchlich beide aktive
Schalter erhalten beide Zugänge. Verborgene Routen werden ohne Serviceaufruf
zum sichtbaren Tarif ersetzt; dies gilt auch für Benutzer mit reinen
Leserechten. [Paneltests](../frontend/tests/panel.test.ts) prüfen die Zustände und Navigation.

## Allgemeine Informationen

`GeneralView.vue`, Pfad `allgemein`, Anforderung `REQ-VUE-GENERAL`.
Die Tabellenreihenfolge entspricht der Anzeige. Die Gerätekarte fasst
Energiezähler und Speicherschalter mit den Gerätedaten zusammen.

| Bereich | Domain und Schlüssel | Attribute, Grenzen und Sichtbarkeit | Prüfung |
| --- | --- | --- | --- |
| Ladezustand | `sensor.soc` | Skala 0–100 %, unter 20 rot, ab 20 gelb, ab 50 grün; tatsächlicher Wert und Bereich zusätzlich als Text. | [Allgemein][general-tests]: Grenzwerte, ungültige Zustände, zugänglicher Meter |
| Zelltemperatur | `sensor.storage_max_cell_temp` | Skala 0–40 °C, unter 5 rot, 5 bis unter 32 grün, ab 32 rot. Außerhalb der Skala wird nur der Zeiger begrenzt, der tatsächliche Wert bleibt sichtbar. | [Allgemein][general-tests]: 5-/32-°C-Grenzen und Werte außerhalb der Skala |
| Leistung | `number.max_soc`, `sensor.charge_power`, `sensor.discharge_power`, `sensor.smartmeter_power` | Globaler Max-SOC mit HA-Grenzen; Leistungswerte mit ihren Einheiten. Label für `smartmeter_power`: Netzleistung. | [Allgemein][general-tests], [Ladeansichten][charging-tests]: gemeinsamer Max-SOC |
| Gerät, erste Zeilen | `sensor.energy_charged`, `sensor.energy_discharged` | Vorhandene Energiezähler und ihre Einheiten; keine Frontend-Akkumulation und keine eigene Energie-Karte. | [Allgemein][general-tests]: Anordnung und fehlende optionale Zeilen |
| Gerät | `sensor.sun_version_master`, `sensor.sun_version_gateway`, `sensor.sun_serial_number` | Optionale SunSpec-Daten; fehlende Zeilen und leere Karte werden ausgelassen. | [Allgemein][general-tests]: optionale Geräteinformationen |
| Gerät, Fortsetzung | `sensor.storage_event_text`, `sensor.ic_control_mode_text`, `binary_sensor.cell_calibration_active`, `sensor.next_cell_calibration` | HA-Zustände/Enum-Texte, Steuermodus, Kalibrierstatus und lokalisiertes Datum ohne Uhrzeit. Hersteller, Modell und entfernte Statuskarten werden nicht wieder eingeführt. | [Allgemein][general-tests]: vollständige Reihenfolge, Live-Werte und Zeitformat |
| Gerät, letzte Zeile | `switch.storage_switch` | Übersetzungsschlüssel `storage`; Bestätigungsdialog vor EIN und AUS. Abbrechen/Escape sowie Änderungen von Zustand, ID, Bedienrecht oder Verbindung verwerfen die Auswahl ohne Schreiben; Bestätigung sendet genau einen vorhandenen HA-Service. | [Allgemein][general-tests], [Controls][control-tests], [Browser][browser-tests] |

## Zeitvariabler Tarif

`TimedChargingView.vue`, Pfad `ladeautomatik`, Anforderung `REQ-VUE-CHARGING`.

| Reihenfolge | Domain und Schlüssel | Darstellung und Verhalten | Prüfung |
| --- | --- | --- | --- |
| Hauptschalter | `switch.timed_charge_enabled` | Übersetzter Name „Netzladung aktiv“. | [Ladeansichten][charging-tests]: vollständige Reihenfolge |
| Zeitfenster | `time.timed_charge_start`, `time.timed_charge_end` | Gemeinsame 24-Stunden-Leiste mit Start-/Endmarken, Minutenfelder und eine atomare Übernahme. Die bestätigte Zeitspanne zeigt nur auf Deutsch „ Uhr“, etwa „22:00–06:00 Uhr“; kein Suffix bei EN, `unknown` oder `unavailable`. | [Zeitfenster-Bedienung](#gemeinsame-zeitfenster-bedienung), [Ladeansichten][charging-tests] |
| Direkt danach: Entladestatus | `sensor.timed_charge_discharge_status` | `normal` → Normalbetrieb, `discharge_blocked` → Entladung wg. Netzladen gestoppt, `grid_charging` → Netzladen. | [Ladeansichten][charging-tests]: alle drei Live-Statuswechsel |
| Einstellungen | `number.timed_charge_max_soc`, danach `number.timed_charge_min_soc` | Netzladeziel und Startschwelle. Die Obergrenze des Ziels folgt dessen HA-`max`-Attribut; kein zusätzlicher globaler Max-SOC in diesem Tab. | [Ladeansichten][charging-tests]: geänderte Grenze, ungültiger und gültiger Zielwert |
| Aktive Monate | `switch.timed_charge_month_1` bis `switch.timed_charge_month_12` | Kompakte Zusammenfassung mit einzeln ausgewählten Monaten und getrennten Spannen; „Ändern“ öffnet vier Quartalsgruppen. Nur HA-bestätigte Zustände; Fehler und fehlende Werte bleiben auch eingeklappt sichtbar. | [Ladeansichten][charging-tests]: zwölf Namen DE/EN, getrennte Auswahlbereiche, HA-Bestätigung, Fehler/Verfügbarkeit und Kalenderwechsel ohne Frontend-Aktion |

Vue entscheidet weder über Ladeberechtigung noch über die laufende
Sollwertwiederholung. Beides verbleibt bei `REQ-TIMED-SOC-CHARGE` im Backend.

## Dynamischer Tarif

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
| 5 | `number.max_soc` | Derselbe globale Max-SOC wie unter Allgemein und in den HA-Entitäten. | [Ladeansichten][charging-tests]: gemeinsamer Zustand und laufender Aufruf in beiden Vue-Views; [HA-E2E][ha-e2e-tests] |
| 6 | `sensor.price_charge_active_text` | Aktiv; bestehender HA-Text. | [Ladeansichten][charging-tests]: Reihenfolge und Zustände |
| 7 | `sensor.price_charge_status_text` | Status, einschließlich deaktivierter Automatik. | [Ladeansichten][charging-tests]: deaktivierter Zustand |
| 8 | `sensor.grid_serving_forecast` | Dynamischer Tagesname und kWh. | [Ladeansichten][charging-tests]: Live-Name und HA-Formatierung |
| 9 | `sensor.price_charge_next_start` | Nächster Start; HA-Zeitzone, Sprache und Zeitformat. `unknown` bleibt unbekannt. | [Ladeansichten][charging-tests]: lokaler Zeitstempel und unbekannter Start |
| 10 | `sensor.price_charge_current_price` | Aktueller Strompreis mit tatsächlicher Einheit; fehlender Preis bleibt nicht verfügbar. | [Ladeansichten][charging-tests]: negativer und fehlender Preis |

Der Frontend-Test prüft diese zehn Schlüssel und ihre Reihenfolge ausdrücklich.
Vue ermittelt keine Strategie oder Ladezeiten; `REQ-DYNAMIC-PRICE-CHARGE`
bleibt die fachliche Implementierung. Diese Ansicht enthält keine Monatsschalter.

## Netzdienliches Laden

`GridServingView.vue`, Pfad `netzdienliches-laden`, Anforderung `REQ-VUE-CHARGING`.

| Reihenfolge | Domain und Schlüssel | Darstellung und Verhalten | Prüfung |
| --- | --- | --- | --- |
| Hauptschalter | `switch.grid_serving_enabled` | „Netzdienliches Laden aktiv“. | [Ladeansichten][charging-tests] |
| Ladepause, Beginn/Ende | `time.grid_serving_start`, `time.grid_serving_end` | Dieselbe Zeitfenster-Komponente mit verschiebbaren Start-/Endmarken, Minutenfeldern und gemeinsamer Übernahme innerhalb der Karte Ladepause. Die bestätigte Zeitspanne zeigt auf Deutsch ebenfalls „ Uhr“. | [Zeitfenster-Bedienung](#gemeinsame-zeitfenster-bedienung), [Ladeansichten][charging-tests] |
| Ladepause, Prognose | `sensor.grid_serving_forecast` | Dynamischer `friendly_name` mit Tagesbezug und Einheit kWh; keine Berechnung in Vue. | [Ladeansichten][charging-tests]: Namenswechsel und nicht verfügbare Prognose |
| Ladepause, Schwelle | `number.grid_serving_forecast_threshold` | „Mindest PV-Prognose“ mit HA-`min`/`max`/`step` und kWh. | [Ladeansichten][charging-tests], [Controls][control-tests] |
| Ladepause, Status | `sensor.grid_serving_pause_status` | Bestehender HA-Statustext. | [Ladeansichten][charging-tests]: Live-Status |
| Aktive Monate | `switch.grid_serving_month_1` bis `switch.grid_serving_month_12` | Dieselbe kompakte Zusammenfassung und aufklappbare Quartalsauswahl mit zwölf Monaten in numerischer Reihenfolge. Nur HA-bestätigte Zustände; Fehler und fehlende Werte bleiben sichtbar. | [Ladeansichten][charging-tests]: Namen, getrennte Auswahlbereiche, Bedienung, Fehler/Verfügbarkeit, Kalenderwechsel |

Es gibt weder eine zusätzliche Einstellungen-Karte noch einen globalen
Max-SOC-Regler. Die Pausenentscheidung bleibt bei `REQ-GRID-SERVING-CHARGE`.

### Gemeinsame Monatsauswahl

Die gemeinsame
[`MonthSelection.vue`](../frontend/src/components/MonthSelection.vue)
startet eingeklappt. Die Zusammenfassung zeigt bestätigte
aktive Monate samt Anzahl und fasst ausschließlich zusammenhängende Bereiche
zusammen, etwa „Januar, März–Mai, Oktober“. Auch Dezember und Januar bleiben
getrennt. Alle zwölf aktiven Monate ergeben „Ganzjährig“ (EN: „All year“).
„Keine Monate ausgewählt · Ganzjährig inaktiv“ setzt zwölf bekannte,
bestätigte `off`-Zustände voraus. Fehlende
Metadaten oder Zustände sowie `unknown` und `unavailable` werden ausdrücklich
markiert und niemals als abgewählte Monate gezählt.

„Ändern“ öffnet vier Quartalsgruppen mit jeweils drei frei schaltbaren Monaten.
„Schließen“ klappt die Auswahl wieder ein. Beides sendet keinen Service;
jeder Monat verwendet unmittelbar den vorhandenen einzelnen HA-Schalterservice.
Es gibt keinen zusätzlichen Speicherschritt. Zusammenfassung und Checkboxen
folgen ausschließlich bestätigten HA-Zuständen. Ausstehende Aktionen,
Servicefehler, fehlende Verbindung und Bedienbeschränkungen bleiben auch
eingeklappt erkennbar; eine zusätzliche Zeile „Bestätigter Wert“ entfällt.
Zusammenfassung, Quartale und Bedienung sind deutsch und englisch übersetzt.

### Gemeinsame Zeitfenster-Bedienung

`TimeWindowControl.vue` ersetzt die getrennten Zeitfelder genau dieser beiden
produktiven Paare. Start und Ende bilden einen lokalen Entwurf. Die beiden
Marken auf einer 24-Stunden-Leiste lassen sich mit Maus, Touch und Tastatur
verschieben; Ziehen, Tastatur und Eingaben verwenden Minuten (HH:MM,
`step=60`, maximal 23:59). Alte Sekunden bleiben bis zur ersten Bearbeitung
in Bestätigung, Dauer und Fläche erhalten, ohne automatischen Schreibzugriff.
Nach einer Bearbeitung übernimmt der Service beide Grenzen als HH:MM:00. Tagesfenster bilden einen Abschnitt, Fenster
über Mitternacht zwei Abschnitte. Gleiche Grenzen bedeuten **leer**, nicht
ganztägig; beide Marken bleiben einzeln erreichbar.

**Übernehmen** sendet genau einen bestehenden Zeitfenster-Service mit
`device_id`, `start` und `end`. Beide Time-Entitäten müssen zum selben Gerät
gehören und bedienbar sein. Auch der Service prüft bei Benutzeraufrufen die
Rechte für beide Entitäten. Es gibt keine Zwischenprüfung aus einer neuen und
einer alten Grenze. Eine tatsächliche Überschneidung mit dem anderen Fenster
in gemeinsamen aktiven Monaten leert nach bestehender Backend-Regel beide
Grenzen und erzeugt eine HA-Benachrichtigung.

Die gemeinsame Bestätigungszeile stammt aus `hass.states`; die erfolgreiche
Serviceantwort allein ersetzt keinen bestätigten Wert. Ändert HA eine Grenze,
etwa durch eine Automation, wird das gesamte Entwurfspaar auf den aktuellen
HA-Stand gesetzt. Andere Telemetrie erhält die Eingabe. Ausstehende Aktionen
und Fehler werden mit beiden Entitäten geteilt. Ungültige Eingaben, fehlende
oder nicht verfügbare Grenzen, Rechteentzug und Verbindungsverlust sperren die
Übernahme. Eine vorhandene gültige Grenze bleibt in der Bestätigungszeile
sichtbar. Geleerte oder unbekannte Zeiten können über die nativen
HA-Time-Entitäten korrigiert werden. Fehler lösen keinen automatischen
Schreibversuch aus.

| Vorhandener Zeitbezug | Umfang der Umstellung |
| --- | --- |
| Zeitvariabler Tarif: `timed_charge_start` / `timed_charge_end` | Gemeinsame Leiste und atomare Übernahme über `set_timed_charge_window`. |
| Netzdienliche Ladepause: `grid_serving_start` / `grid_serving_end` | Dieselbe Komponente, Übernahme über `set_grid_serving_window`. |
| Dynamischer Tarif: geplanter nächster Start; Amortisation: Tarifzeitfenster | Nur Anzeigen aus HA; keine editierbaren Zeitpaare. |
| Amortisation: Anfangs- und Enddatum | Recorder-Datumsfilter, weiterhin Datumseingaben. |
| Bis zu acht TOU-Fenster im HA-Optionsflow | Außerhalb des Vue-Panels; keine Umstellung. |
| Einzelzeit in der Controls-Entwicklungsvorschau | Komponentendemonstration, kein weiteres produktives Zeitfenster. |

Zur Abnahme gehören Tages-, Mitternachts- und leere Fenster, vorhandene Altsekunden ohne Schreibaktion,
Maus-/Touch-/Tastaturbedienung, Fokus und einzeln erreichbare Marken sowie
DE/EN und helle/dunkle Themes auf Smartphone und Desktop. Der HA-Kontext muss
atomare Payloads, gemeinsame Aktionssperren, verzögerte HA-Bestätigung und
Änderungen von Entitäten, Geräten, Rechten oder Verbindung abdecken. Native
HA-Servicetests prüfen die Rechte beider Grenzen und die bestehende
Überschneidungsreaktion. Die unten aufgeführten historischen CI-Ergebnisse
und Screenshots belegen diese neue Bedienung noch nicht; der neue
Abschlussnachweis wird erst nach dem zugehörigen Testlauf ergänzt.

## Amortisation

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

## Lebenszyklus, Migration und Reparaturen

| Fall | Erwartetes Verhalten | Prüfung |
| --- | --- | --- |
| Neuinstallation und Bestandsinstallation | Die einzige Dashboard-Auswahl bleibt ein Opt-in mit Standard `False`. Optionen haben Vorrang vor Setup-Daten, auch bei explizitem `False`. | [Config Flow](../tests/test_config_flow.py), [Initialisierung](../tests/test_init.py) |
| Aktivieren, Deaktivieren, Reload, Unload, Neustart | Ein Panel SAX Power, einmalige statische Route pro HA-Lauf; Abschalten entfernt nur den eigenen Eintrag. | [Panel-Lebenszyklus][lifecycle-tests], [Dashboard-Reparaturen][repair-tests], [Neustart][restart-tests] |
| HA-Zustände und Bedienung | Zwei echte HA-WebSocket-Clients prüfen Dashboard-Metadaten und reguläre HA-Services. Das Öffnen liest/schreibt keine zusätzlichen Register; eine Aktion verursacht genau ihren bestehenden Geräteaufruf. | [HA-E2E mit Modbus-Simulator][ha-e2e-tests] |
| Legacy-Migration | `create_dashboard` und `dashboard_update_dismissed` werden aus Entry-Daten und Optionen entfernt; `dashboard_outdated_<entry_id>` wird aus der Issue Registry entfernt. Dashboard-Opt-in und gespeicherte HA-/Lovelace-Dashboards samt Karten bleiben erhalten. | [Initialisierung](../tests/test_init.py), [Config Flow](../tests/test_config_flow.py) |
| Entfernte Implementierung | Kein Lovelace-Builder, keine Create-/Reinstall-Services, kein Veraltet-Reparaturflow und keine Lovelace-Abhängigkeit. Die aktuelle Oberfläche zeigt keinen parallelen Dashboard-Einstieg. | [HA-E2E][ha-e2e-tests], [Panel][panel-tests], [Browser][browser-tests], [Paket-Worker][package-worker] |
| Bundlewechsel | SHA-256 erkennt neue Inhalte auch bei unveränderter Manifestversion; registriert erst bei Bestätigung den aktuellen Stand. Anschließendes vollständiges Browser-Neuladen ist ein eigener Dialogschritt. | [Dashboard-Reparaturen][repair-tests], [Paket-Worker][package-worker] |
| Ablehnen, Fehler, alter Dialog | Ablehnen unterdrückt nur denselben Stand. Fehler sind wiederholbar; ein alter Dialog quittiert kein neues Update. Fremde Panels, deaktivierte/entfernte Einträge und Reconfigure sind berücksichtigt. | [Dashboard-Reparaturen][repair-tests], [Panel-Lebenszyklus][lifecycle-tests] |

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
Funktionslauf; sie werden hier nicht pauschal als geprüft bezeichnet.

| Prüfung | Umfang und Ausführung |
| --- | --- |
| Python | `pytest -v`, `ruff check custom_components scripts tests`, `black --check custom_components scripts tests`; reale Hardwaretests werden ohne verfügbares Testgerät übersprungen. |
| Frontend | Im Verzeichnis `frontend`: `npm ci`, `npm run check`, `npm test`, `npm run build`; Build enthält den Test des echten ES-Moduls ohne Node-Laufzeitglobals im Browser. |
| Chromium | `npx playwright install chromium`, dann `npm run test:browser`; [Konfiguration](../frontend/playwright.config.ts) und [Testfälle][browser-tests]. Vier Projekte: Desktop 1440×1000 und Smartphone 390×844, jeweils DE/hell und EN/dunkel. |
| Browserdaten | `browser/server.mjs` liefert das **Produktionsbundle** unter `127.0.0.1:5190`; eine ausdrücklich als Simulation gekennzeichnete HA-Fixture liefert die Testzustände. Geprüft werden alle Tabs, Bedienung, Fokus/Tastatur, History/Reload, Fehler, Reconnect, Zeitfenster und Datumswahl. |
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

### Minutenfelder, Tarifnavigation und Zellkalibrierung vom 12.09.2026

Die aktuelle Ergänzung bestand lokal mit **278 Frontendtests** und
**1.801 Python-Tests, zwei erwarteten Hardware-Skips**. TypeScript, Prettier,
Produktionsbuild samt Modultest, Ruff, Black und Release-Metadaten waren
erfolgreich. Die lokale Browserprobe am Produktionsbundle prüfte HH:MM ohne
Sekundenfeld, minutengenaue gemeinsame Übernahme, die 22×22-Pixel-Speichercheckbox
mit 44×44-Pixel-Klickfläche, das reine Kalibrierungsdatum sowie Tarifwechsel
und verborgene Direktlinks ohne Serviceaktion. Desktop und eine dunkle
390-Pixel-Ansicht wurden visuell kontrolliert.

Der unabhängige Review gegen die Anforderungen fand einen zusätzlichen
PV-Regelpfad, der vor seiner Leistungsentscheidung ebenfalls die Fälligkeit
aktualisieren muss. Der Fehler wurde behoben und einschließlich Basic-Ausfall
und Bootstrap durch Regressionstests abgesichert; das erneute Review ergab
keine offenen materiellen Codebefunde. Die Kalibrierung gilt ab Tagesbeginn
am dritten HA-lokalen Kalendertag, verwendet keine eigene Netzladung und
belässt die gespeicherten Benutzergrenzen. Die späteren CI- und Paketnachweise
zum veröffentlichten Commit stehen in PR #204.

### Gemeinsame Zeitfenster-Leisten vom 12.09.2026

Die Umstellung beider editierbaren Zeitfenster wurde lokal mit **255
Frontend-Tests**, Typprüfung, Prettier und dem Produktionsmodultest geprüft.
Die vollständige Python-Suite bestand mit **1.780 Tests und zwei erwarteten
Hardware-Skips**; Ruff und Black waren erfolgreich. Die neuen nativen
HA-WebSocket-Fälle prüfen beide atomaren Fenster mit umbenannten Entitäten,
sekundengenauen Zuständen und Kontrollrechten auf beide Grenzen.

Die lokale Browserprobe am gebauten Modul prüfte Mausziehen, Pfeiltasten,
Tagesgrenzen, genaue Zeiteingaben, Servicefehler und erneute Übernahme.
Desktop sowie dunkle Ansichten mit 390 und 320 Pixeln wurden visuell geprüft.
Bei 320 Pixeln standen in diesem historischen Stand die vollständigen
Sekundenfelder untereinander; die
Skalenbeschriftungen überlappen nicht. Der unabhängige Review führte zu einem
zusätzlichen Regressionstest für gemeinsam geänderte Registry-Geräte-IDs.

Die CI-Browserfälle prüfen beide Fenster zusätzlich mit echten Touch-Ereignissen
in den mobilen Chromium-Projekten, getrennten Markenzielen bei gleichen
Uhrzeiten und genau einem atomaren Serviceaufruf je Übernahme. Die Ergebnisse
des veröffentlichten Commits stehen in den Checks von PR #204; die folgenden
älteren Nachweise beziehen sich jeweils auf ihre ausdrücklich genannten Stände.

### Frühere Frontend-Abnahme vom 12.09.2026

Dieser Nachweis betrifft den Stand vor der gemeinsamen Zeitfenster-Leiste
und der aufklappbaren Monatsauswahl mit Quartalsgruppen. Er ist kein
Prüfnachweis für diese Erweiterungen.

Der vollständige
[CI-Lauf 34688788120](https://github.com/dr-dimitri/sax-ha/actions/runs/34688788120)
prüfte den Code aus
[Commit f50e9e69ae0d](https://github.com/dr-dimitri/sax-ha/commit/f50e9e69ae0d9310385d48a314c52e911fc90811)
im zugehörigen PR-Testmerge erfolgreich. Der Browserbericht zeigt:
**28 von 28 Browserfällen bestanden,
keine Fehler, keine erst nach Wiederholung bestandenen Fälle und keine Skips**.
Die Prüfung umfasst das einzige Dashboard **SAX Power**, alle fünf Ansichten,
die kompakten Monatsraster mit kleineren sichtbaren Kästchen und das Entfernen
des zweiten Dashboard-Einstiegs. Die Browserfälle prüfen zusätzlich, dass
Randklick und Leertaste jeweils genau einen HA-Serviceaufruf auslösen.
Das Produktionsmodul verwendet in diesen Browserprüfungen simulierte HA-Daten.

Für diesen Stand bestanden **202 Komponententests**, Typprüfung, Prettier und
der reproduzierbare Build. Die lokale Python-Gesamtsuite bestand mit
**1.748 Tests und zwei erwarteten Hardware-Skips**; Ruff und Black waren grün.

Die damalige lokale Browserprüfung über CUA maß für beide Monatsraster:

| Verfügbarer Platz | Monatsspalten | Rasterhöhe |
| --- | --- | --- |
| 1110 px Panelbreite | 6 | 116 px |
| 390 px Browserbreite | 2 | 364 px |

Die Messwerte gelten für die damaligen Monatsraster mit den geprüften
Beispieldaten, nicht für die aktuelle Quartalsauswahl. Fehler und ausstehende
Aktionen dürfen die Kacheln vergrößern. Alle zwölf Monatsnamen bleiben lesbar
und die Bedienflächen mindestens 44 × 44 px groß, während die sichtbaren
Checkboxen nur 22 × 22 px messen. Die lokale Maus- und Tastaturprüfung zeigte
jeweils genau eine simulierte Aktion. Gespeicherte HA-Dashboards werden durch
die Legacy-Migration nicht gelöscht. Es fand kein
Test an einer physischen Batterie statt. Die finale isolierte Paketprüfung
wird mit dem tatsächlichen Commit und den Prüfsummen in
[PR #204](https://github.com/dr-dimitri/sax-ha/pull/204) festgehalten.

### Bestätigung der Softwarekonfiguration

[test_control_response.py](../tests/test_control_response.py) und
[test_vue_dashboard_e2e.py](../tests/test_vue_dashboard_e2e.py) prüfen die
Software-Entity- und Software-Serviceaufrufe bei blockierter Geräteauswertung:
Serviceantwort und HA-Zustandsereignis müssen vor Freigabe der Sperre eintreffen.
Die Tests sichern auch die gemeinsame Auswertung aufeinanderfolgender
Änderungen, Speicherung, getrennte Aktivitätsbestätigung und die Ablehnung
nach Shutdown vor einer Mutation ab. Der Hinweis auf eine ausstehende
Serviceantwort bleibt dadurch nicht wegen eines Modbus-Zugriffs stehen.

### Frühere Korrektur der Monatsbestätigung

Der HA-WebSocket-Test in [test_vue_dashboard_e2e.py](../tests/test_vue_dashboard_e2e.py)
bestätigt alle zwölf Monatsschalter beider Gruppen bereits bei absichtlich
gehaltener Geräte-Steuerungssperre. Mit der früheren Implementierung blieb
die erste Serviceantwort aus; die korrigierte Implementierung liefert
Serviceantwort und HA-Zustandsereignis, bevor die Sperre freigegeben wird.
Danach läuft die reguläre Geräteauswertung weiter.
[test_month_switch_response.py](../tests/test_month_switch_response.py)
sichert Folgeänderungen, abgelehnte Überschneidungen, Speichervormerkung,
Gerätefehler sowie Bootstrap und Shutdown ab. Das Frontend zeigt weiterhin
den bestätigten HA-Zustand. Diese Korrektur veränderte die Darstellung nicht;
die spätere Zeitfenster-Umstellung und aufklappbare Quartalsauswahl sind in
den Screenshots unten noch nicht enthalten. Der zugehörige CI- und Paketnachweis steht in
[PR #204](https://github.com/dr-dimitri/sax-ha/pull/204).

### Historische Prüfnachweise vom 12.09.2026

Die folgenden Ergebnisse betreffen den jeweiligen früheren Code- und
Paketstand. Sie belegen noch nicht die Entfernung des Lovelace-Dashboards,
das Branding **SAX Power** oder die weitere Verdichtung der Monatsraster.
Die Browserläufe verwenden simulierte HA-Daten; physische Hardware wurde
nicht getestet. Die damaligen Python-Gesamtsuiten umfassten 1.813 bestandene
Tests und zwei erwartete Hardware-Skips.

| Historischer Stand | Code und CI | Ergebnis |
| --- | --- | --- |
| Tarif-Tabnamen, Reihenfolge und Uhr-Suffix | [936eaeae6c97](https://github.com/dr-dimitri/sax-ha/commit/936eaeae6c972fe99e53f2f6d40af58ded6a80ab), [CI 34685941171](https://github.com/dr-dimitri/sax-ha/actions/runs/34685941171) | Vollständige CI erfolgreich; 202 Komponententests und 28 Browserfälle ohne Wiederholung oder Skips. |
| Kompakte Desktopansichten | [e6cf1672d17b](https://github.com/dr-dimitri/sax-ha/commit/e6cf1672d17b35ffd586bb85b4dec12d567cb089), [CI 34684553344](https://github.com/dr-dimitri/sax-ha/actions/runs/34684553344) | 199 Komponenten- und 28 Browserfälle; Prüfung mehrerer verfügbarer Panelbreiten. |
| Gerätekarte und Schaltbestätigung | [639695e5e347](https://github.com/dr-dimitri/sax-ha/commit/639695e5e3479f802c568704f3ae34f3e5bd473c), [CI 34683284222](https://github.com/dr-dimitri/sax-ha/actions/runs/34683284222) | 199 Komponenten- und 24 Browserfälle; beide Schaltrichtungen und Abbruch geprüft. |
| Erste vollständige Paketabnahme | [acb49d089767](https://github.com/dr-dimitri/sax-ha/commit/acb49d089767f45bc25cbaa41c47728f083a1a84), [CI 34681752310](https://github.com/dr-dimitri/sax-ha/actions/runs/34681752310) | 186 Komponenten- und 20 Browserfälle; isolierte Installation von Snapshot und Quellarchiv samt HA-HTTP-Route und Reparatur. |

Das historisch geprüfte Paket `snapshot-pr-204-acb49d089767` enthielt 57 Dateien,
Manifest `2.0.3-snapshot.pr204.shaacb49d089767`, ZIP-SHA-256
`d0f406fd06d367dbf82b30cd197e0f0e4dbde5521e26f1b77c9756fbbfd72ac3` und
Bundle-SHA-256 `dc3d1df0032f8e6d8ba500c2ffb942e8f463188c016202932fbdcb1d419ac1dd`.
Der Tag bezeichnet einen historischen Prüfgegenstand, keine dauerhaft
bereitgehaltene Snapshot-Veröffentlichung. Weitere Paketnachweise sind mit
Commit und Prüfsummen in [PR #204](https://github.com/dr-dimitri/sax-ha/pull/204)
zugeordnet.

### Screenshots vor der Zeitfenster- und Monatsauswahl-Umstellung

Die 14 Bilder stammen aus dem Browserbericht von
[CI-Lauf 34688788120](https://github.com/dr-dimitri/sax-ha/actions/runs/34688788120)
vom 12.09.2026. Sie zeigen das einzige Dashboard **SAX Power** ohne
Vue-/Vorschaukennzeichnung oder Einstieg zum alten Dashboard, die verdichteten
Monatsraster mit 22-px-Kästchen und die Schalterbestätigung. Die Umgebung mit
simulierten HA-Daten ist ausdrücklich als Testansicht gekennzeichnet.
Die neuen gemeinsamen Zeitfenster mit verschiebbaren Marken und die
aufklappbare Monatsauswahl mit Quartalsgruppen sind darin noch nicht enthalten.

| Ansicht | Desktop, Deutsch, hell | Smartphone, Englisch, dunkel |
| --- | --- | --- |
| Allgemeine Informationen | [Screenshot](images/vue-allgemein-desktop-light-de.png) | [Screenshot](images/vue-allgemein-mobile-dark-en.png) |
| Speicher ausschalten – Bestätigung | [Screenshot](images/vue-storage-confirm-off-desktop-light-de.png) | [Screenshot](images/vue-storage-confirm-off-mobile-dark-en.png) |
| Speicher einschalten – Bestätigung | [Screenshot](images/vue-storage-confirm-on-desktop-light-de.png) | [Screenshot](images/vue-storage-confirm-on-mobile-dark-en.png) |
| Zeitvariabler Tarif | [Screenshot](images/vue-ladeautomatik-desktop-light-de.png) | [Screenshot](images/vue-ladeautomatik-mobile-dark-en.png) |
| Dynamischer Tarif | [Screenshot](images/vue-dynamisches-laden-desktop-light-de.png) | [Screenshot](images/vue-dynamisches-laden-mobile-dark-en.png) |
| Netzdienliches Laden | [Screenshot](images/vue-netzdienliches-laden-desktop-light-de.png) | [Screenshot](images/vue-netzdienliches-laden-mobile-dark-en.png) |
| Amortisation | [Screenshot](images/vue-ersparnis-desktop-light-de.png) | [Screenshot](images/vue-ersparnis-mobile-dark-en.png) |

<details>
<summary>Alle fünf Desktopansichten anzeigen</summary>

![Allgemeine Informationen mit simulierten HA-Daten](images/vue-allgemein-desktop-light-de.png)

![Zeitvariabler Tarif mit simulierten HA-Daten](images/vue-ladeautomatik-desktop-light-de.png)

![Dynamischer Tarif mit simulierten HA-Daten](images/vue-dynamisches-laden-desktop-light-de.png)

![Netzdienliches Laden mit simulierten HA-Daten](images/vue-netzdienliches-laden-desktop-light-de.png)

![Ersparnis mit simulierten HA-Daten](images/vue-ersparnis-desktop-light-de.png)

</details>

[metadata-tests]: ../tests/test_dashboard_api.py
[ha-tests]: ../frontend/tests/ha.test.ts
[control-tests]: ../frontend/tests/controls.test.ts
[control-response-tests]: ../tests/test_control_response.py
[general-tests]: ../frontend/tests/general.test.ts
[charging-tests]: ../frontend/tests/charging.test.ts
[savings-tests]: ../frontend/tests/savings.test.ts
[panel-tests]: ../frontend/tests/panel.test.ts
[browser-tests]: ../frontend/browser/dashboard.spec.ts
[statistics-tests]: ../tests/test_dashboard_statistics.py
[ha-e2e-tests]: ../tests/test_vue_dashboard_e2e.py
[lifecycle-tests]: ../tests/test_vue_dashboard.py
[repair-tests]: ../tests/test_vue_dashboard_repairs.py
[package-tests]: ../tests/test_frontend_package.py
[package-worker]: ../scripts/dashboard_package_smoke.py
[restart-tests]: ../tests/test_vue_dashboard_restart.py
