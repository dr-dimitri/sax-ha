# HEMS-Nachtladung: Referenzen und Abnahme

Diese Erweiterung verwendet die SAX-Entladeenergie als Nachtverbrauchsmodell.
Sie misst damit keine vollständige Hauslast und verspricht keine garantierte
Einsparung. Die erste Stufe endet spätestens vier reale Stunden nach Sonnenaufgang.
Alle Szenarien laufen lokal mit deterministischen Prognosen und simuliertem SAX.

## Referenzmengen

`E_at_delivery` bezeichnet bereits die chronologisch berechnete Speicherenergie
an der Bereitstellungsgrenze. Vorherige Entladung darf nicht übergangen werden.

| Kapazität | SOC dort | Reserve | AC-Last danach | eta Laden/Entladen | Netzladung | Ziel |
| --- | --- | --- | --- | --- | --- | --- |
| 10 kWh | 20 % | 10 % | 3 kWh | 1 / 1 | 2 kWh | 40 % |
| 10 kWh | 50 % | 10 % | 3 kWh | 1 / 1 | 0 kWh | kein Ladeauftrag |
| 10 kWh | 0 % | 10 % | 1,5 kWh | 1 / 1 | 2,5 kWh | 25 % |
| 10 kWh | 20 % | 10 % | 3 kWh | 0,95 / 0,95 | 2,271468 kWh | 41,578947 % |

Kommt tragfähige PV bei leerem Speicher noch **vor** Ende desselben günstigen
Fensters, entfällt die Batterie-Netzladung. Tragfähig bedeutet mindestens
60 vollständig belegte Minuten mit durchgehend ausreichender positiver Leistung;
dieser Nachweis darf über das günstige Fensterende hinausreichen. Eine einzelne
PV-Spitze genügt nicht. Kommt die PV danach, wird die Brücke plus Reserve geladen.
Auch das Ende des 60-Minuten-Nachweises muss spätestens vier reale Stunden
nach Sonnenaufgang liegen. Benötigt wird lückenlose Coverage von jetzt bis
zu diesem Ende; spätere fehlende Randstunden erzwingen keinen Fallback.

## Öffentliche PV-Schnittstellen

| Quelle | Verwendeter Vertrag | Frische und Einschränkung |
| --- | --- | --- |
| pv_forecast | `pv_forecast.get_forecast`, Schema 1, ganze Anlage als AC-kWh-Intervalle | Echter `fetched_at`, höchstens 60 Minuten alt; letzter Abruf erfolgreich, einzelne Intervalle vollständig ohne Ersatzwerte |
| Solcast | `solcast_solar.query_forecast_data`, ganze Anlage, gedämpfter `pv_estimate` in mittleren kW je 30 Minuten | „API Last Polled“ desselben Eintrags über die Registry; Vergleich vor/nach dem Read. Maximalalter 1–24 h, initial 24 h als SAX-Annahme; Erfolgsstatus kann unbekannt sein. Mehrere geladene Solcast-Einträge sind wegen fehlender öffentlicher Serviceauswahl nicht eindeutig unterstützbar. |
| Forecast.Solar / HA-Energy | Native Energy-Konvention `wh_hours` | Energy-kompatibel, hier kein vollwertiger HEMS-Adapter: ausreichende öffentliche Frische-/Qualitätsmetadaten fehlen. Keine privaten Imports oder Diagnosedaten als Umgehung. |

pv-forecast-ha implementiert den nativen HA-Energy-Vertrag bereits. Sein
bestehendes [Issue #171](https://github.com/dr-dimitri/pv-forecast-ha/issues/171)
zur Energy-Frische bleibt separat; diese Serie benötigt keinen erfundenen
neuen Standardsensor und löst keine zusätzlichen Wetterabrufe aus.

## Konsistenzmatrix

| Anforderung / Issue | Umsetzung | Verifikation / Anzeige |
| --- | --- | --- |
| REQ-HEMS-LOAD-PROFILE / #221 | `domain/hems_load.py`, `infrastructure/hems_history.py` | `test_hems_load.py`, `test_hems_history.py`; Nächte, Beobachtungsstunden, Quellenqualität |
| REQ-HEMS-PV-INPUT / #222 | `domain/hems_pv.py`, `infrastructure/hems_pv.py` | `test_hems_pv.py`; Provider, echter Abrufzeitpunkt, getrennte Frischepolitik |
| REQ-HEMS-ENERGY-PLANNER / #223 | `domain/hems.py`, `domain/hems_planner.py` | `test_hems_planner.py`; Bedarf, Ziel, PV-Beginn, Unterdeckung |
| REQ-HEMS-RUNTIME / #224 | `application/hems_runtime.py`, `domain/hems_progress.py`, zentraler Coordinator | `test_hems_runtime.py`, `test_hems_progress.py`; Plan-Lease, tatsächliche nächste Prüfung, ACK getrennt, quantisierter SOC |
| REQ-HEMS-TIMED-CHARGE / #224 | `application/hems_tariffs.py`, ChargePolicy, ControlStore | Runtime-/Konfigurationstests; Monate und Fenster, MinSOC als Reserve bzw. Fallback-Start |
| REQ-HEMS-DYNAMIC / #225 | `price_optimizer.py`, PricePlanCycleStore, gemeinsamer Planer | `test_hems_dynamic.py`, Runtime; Preisgrenze, Restbudget und Neutralpreispause |
| REQ-HEMS-CONFIGURATION / #226 | OptionsFlow, Select, ControlStore | `test_hems_configuration.py`, `frontend/tests/charging.test.ts`; Upgrade, Quellenzuordnung und gemeinsame Ladegrenzen |
| REQ-HEMS-OBSERVABILITY / #226 | Sensoren, `frontend/src/components/HemsCard.vue`, `frontend/src/hems.ts` | `frontend/tests/hems.test.ts`, `frontend/browser/hems.spec.ts`; DE/EN, unbekannte Daten, Plan vs. quittierter Ladebefehl |
| REQ-HEMS-ACCEPTANCE / #227 | gemeinsamer Branch und Snapshot-PR | `test_hems_acceptance.py`, vollständige Prüfungen und unabhängiges Review im PR |

Modulpfade ohne Präfix beziehen sich auf `custom_components/sax_power/`,
Python-Testnamen auf `tests/`. Die tatsächlich ausgeführten Testzahlen und
das Review des endgültigen Commits stehen im PR-Prüfprotokoll.

## Bewusste Grenzen

- Alte Recorder-Zähler allein belegen keine freie Entladung. Nach Installation
  muss deshalb gegebenenfalls erst genügend SAX-Qualitätshistorie entstehen.
  Bis dahin gilt nachts der ausdrücklich erklärte klassische Ersatzbetrieb.
- Eine fällige Kalibrierung zensiert freie Entladung nicht. Nur tatsächlich
  beeinflusste Intervalle sind ungeeignet zum Lernen.
- Die PV-Integrationen liefern unterschiedliche Frischegarantien. `wh_hours`
  aus dem HA-Energy-Dashboard reicht ohne Aktualitätsnachweis nicht aus. Vorerst
  stehen die öffentlichen pv_forecast- und Solcast-Response-Schnittstellen bereit.
- Energieherkunft am Netzanschlusspunkt ist eine konservative Schätzung.
  Messlücken werden nicht als präzise erfüllte Ladung verbucht; Ziel- und
  Zeitgrenzen bleiben zusätzlich wirksam. Die reale SOC-Auflösung begrenzt die
  Genauigkeit, die mathematischen Referenzen sind keine Hardwaregarantie.
- Ein eigener Live-Ledger erhält bekannte Einspeicherung über Quellenwechsel,
  kurze Ladestopps und Neuplanungen trotz unveränderter SOC-Stufe. Tatsächliche
  Entladung reduziert diesen Rest; PV-Ladung verändert den Speicherzustand,
  erfüllt aber kein Netzladebudget. Die SOC-Korrektur beträgt höchstens einen
  Prozentpunkt. Unbekannte Messungen, Lücken über 30 Sekunden oder geänderte
  Modellannahmen verwerfen den Rest. Ein höchstens 30 Sekunden alter
  Wiederanlaufnachweis berücksichtigt mögliche Entladung konservativ und ist
  keine Ladefreigabe; der erste neue Leistungssample wird einmalig übernommen.
- Kalibrierungsenergie wird gesondert ausgeführt und erklärt. Sie darf nur nach
  einem regulären Ladeanlass über den normalen Bedarf hinausgehen; auch dann
  bleiben Preis-, Stunden-, Modell- und Sicherheitsgrenzen verbindlich.
- Die bestehenden Strategien `off`, `absolute`, `relative` und `smart` behalten
  ihre eigenen Regeln. Insbesondere ersetzt diese Serie nicht die getrennten
  Altstrategie-Issues #214, #216 und #217.

## Prüfprotokoll

Die endgültigen Testzahlen, der geprüfte Commit, das Review-Ergebnis und der
Link zum daraus erzeugten Snapshot werden im zugehörigen PR festgehalten.
Der Snapshot bleibt als Vorabversion vom stabilen Release getrennt und wird
nicht mit dem Label `release:snapshot` gemergt.
