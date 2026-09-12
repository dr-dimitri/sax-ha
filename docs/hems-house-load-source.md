# Optionale Hausverbrauchsquelle: Konzept und Quellenvertrag

Dieses Konzept erfüllt #235. Es aktiviert keine neue Quelle. Weiterhin verwendet
HEMS ausschließlich SAX-Entladeenergie; Nacht, höchstens vier Stunden Dämmerung,
Min-SOC-Reserve, Tarif-/Monatsfenster, dynamische Preisgrenze und Ladebudget bleiben
verbindlich. Eine spätere Umsetzung benötigt die konkrete bestätigte Quelle und
einen eigenen Auftrag.

## Messgröße und vorhandene Quellen

Gesucht ist der gesamte AC-Hausverbrauch ohne Batterieladung, unabhängig davon,
welcher Anteil aus PV, Speicher oder Netz stammt. Er wird in AC-kWh je eindeutigem
UTC-Intervall beschrieben. Ein bloßes Energiedefizit nach Abzug von PV ist eine
andere Größe und darf nicht als Hausverbrauch verwendet werden.

| Quelle | Tatsächliche Größe | Eignung und Grenzen |
| --- | --- | --- |
| SAX `storage_power_active` | AC-Speicherleistung, positiv Entladen, negativ Laden | Heute verfügbare Quelle; bei leerem/gesperrtem Speicher fehlt damit der Hausbedarf. |
| SAX `energy_discharged` | Aus gemessener Speicherleistung integrierte Entladeenergie | Bestehende Nachtbasis, kein unabhängiger Hauszähler; bestehende Qualität und Messlücken bleiben relevant. |
| SAX `smartmeter_power` | AC-Netzleistung, positiv Bezug, negativ Einspeisung | SunSpec-Rohregister 40072 wird bereits beim Dekodieren negiert. Keine zweite Vorzeichenumkehr. Allein kein Hausverbrauch. |
| SAX-/SunSpec-Batteriegrenzen | SOC, verfügbare Lade-/Entladeleistung | Qualitäts- und Sicherheitsnachweis; keine gemessene Hauslast oder PV-Erzeugung. |
| Unabhängiger AC-Hausverbrauchszähler | Gesamte Verbraucher hinter dem definierten Messpunkt | Bevorzugte spätere Quelle, wenn Batterieladung ausgeschlossen und Messgrenze nachgewiesen ist. |
| Vorhandene HA-Energie-Entity | Vom Anwender zu bestätigender Zähler in Wh/kWh | Herstellerunabhängig möglich; `device_class` und `state_class` allein beweisen nicht die Messgrenze. |
| HA-Leistungs-Entity | Momentan- oder Intervallleistung in W/kW | Nur mit bekannter Zeitsemantik, Vorzeichenkonvention, Abtastung und expliziter Integration. |
| Bilanz aus Netz, SAX und AC-PV | Rechnerischer Hausverbrauch | Nur bei synchroner, nachgewiesener gemeinsamer AC-Topologie und ohne Doppelzählung zulässig. |

Register und tatsächliche Vorzeichen sind in [modbus_llm.yaml](../modbus_llm.yaml)
und im zentralen SunSpec-Dekodierpfad dokumentiert. Es wird keine beim Anwender
vorhandene Entity vorausgesetzt. Eine PV-Vorhersage ersetzt keine PV-Istmessung.

## Nachgewiesene Energiebilanz

Für ein gemeinsames AC-Netz mit separatem PV-Wechselrichter, separatem SAX und
Verbrauchern gilt bei gleichen Messzeiten und Messgrenzen:

`Hausleistung = Netzleistung + SAX-Leistung + tatsächliche AC-PV-Leistung`

Die SAX-Leistung ist bereits vorzeichenbehaftet. Bei Netzladen zieht ihr negativer
Wert die Batterieladung vom Netzbezug ab. Wirkungsgrade werden hier nicht nochmals
auf AC-Messungen angewendet. Eigenverluste außerhalb der bestätigten Messgrenze
werden nicht geschätzt. Bei DC-gekoppeltem Hybridwechselrichter darf dessen
AC-Leistung nicht gleichzeitig als reine PV und als separat bereits enthaltene
Speicherleistung gezählt werden; ohne auflösbare Messgrenze bleibt die Bilanz
ungeeignet.

Die folgenden Zahlen sind synthetische Prüffälle in kW, keine Anwenderdaten:

| Situation | Netz | SAX | AC-PV | Haus |
| --- | ---: | ---: | ---: | ---: |
| Nacht, Speicher deckt Last | 0 | 0,6 | 0 | 0,6 |
| Nacht, Speicher leer | 0,6 | 0 | 0 | 0,6 |
| Netzladen | 2,6 | −2 | 0 | 0,6 |
| Entladung gesperrt | 0,8 | 0 | 0 | 0,8 |
| PV und SAX decken Last gemeinsam | 0 | 0,4 | 0,6 | 1,0 |
| PV lädt Batterie | 0 | −1,5 | 2,5 | 1,0 |
| PV-Überschuss ins Netz | −2 | 0 | 3 | 1,0 |

Ein negatives Bilanzresultat außerhalb dokumentierter Messungenauigkeit ist ein
Qualitätsfehler, kein still auf null geklemmter Verbrauch. Unsynchrone Werte werden
nicht einfach addiert. Auch „nachts ist PV null“ muss durch Messung oder einen
ausdrücklich abgegrenzten, belegten Nachtvertrag begründet sein.

## Normalisierter Quellenvertrag

Ein HA-Adapter liefert immutable Intervalle mit:

- `basis = house_load_ac`, `source_version`, stabiler Registry-Identität,
  bestätigter Messgrenzen-/Topologiekennung und Konfigurationsgeneration;
- timezone-aware `start`, `end`, tatsächlicher Beobachtungszeit und getrenntem
  HA-Meldezeitpunkt; interne Berechnung erfolgt in UTC und mit realer Dauer;
- nichtnegativer endlicher `energy_kwh` nur bei belegtem Intervall,
  `observed_seconds`, Messmethode und Qualitätsgründen;
- Kennzeichnung direkt gemessen, aus Leistung integriert oder durch eine
  bestätigte AC-Bilanz abgeleitet; unbekannte Werte bleiben `null`.

Fortlaufende Energiezähler sind bevorzugt. Wh wird einmal in kWh umgerechnet.
Zählerreset, Tageswechsel, Überlauf und Identitätswechsel beginnen einen neuen
Abschnitt. Eine positive Zählerdifferenz über eine unbekannte Lücke wird nicht
willkürlich auf Viertelstunden verteilt. Die Leistungsmethode benötigt eine
vorab festgelegte maximale Lücke und Integrationsregel; länger fehlende Daten
werden weder fortgeschrieben noch durch null ersetzt. Recorder-Daten benötigen
dieselben Qualitätsnachweise wie Live-Daten.

Vor einer Implementierung sind Entity, Einheit, Messpunkt, Vorzeichen,
Zeitsemantik, maximale zulässige Meldepause und AC/DC-Topologie zu dokumentieren.
Ohne diese Angaben bleibt die Option unkonfiguriert. Ein generischer HA-Adapter
benötigt keine private API eines PV-Anbieters.

## Opt-in, Neuaufbau und Ausfallzustände

Die spätere Konfiguration wählt ausdrücklich `sax_discharge_ac` oder
`house_load_ac`. Die beiden Quellen besitzen eigene Historie, Profilkennungen,
Archivsegmente, Live-Anker und Unsicherheitsnachweise. Alte SAX-Daten werden nie
rückwirkend in Hausverbrauch umbenannt. Ein Wechsel verwirft inkompatible
Freigaben und baut eine neue qualitätsbelegte Historie auf. Die bisherigen
SAX-Daten dürfen separat bis zu ihrer Aufbewahrungsgrenze erhalten bleiben.

Als eindeutigen ersten Ausfallvertrag sieht dieses Konzept vor: Bei Ausfall der
ausgewählten Hausquelle gilt der bestehende sichere Min-/Max-SOC-Fallback, unter
allen geltenden Tarif- und Preisgrenzen. Es werden keine einzelnen SAX-Werte in
das Hausprofil eingefügt. Ein später gewünschter automatischer Wechsel zu einem
separat qualifizierten SAX-Modell wäre eine eigene sichtbare Zustandsänderung
mit eigenem Gütenachweis, nicht Teil des ersten Quellenadapters.

Bei Rückkehr der Quelle werden frische Messungen und Kontinuität neu geprüft;
eine Lücke wird nicht rückgefüllt. Entladen oder Löschen beendet Listener und
verhindert nachlaufende Schreibungen. Keine neuen Modbus-Lese-/Schreibpfade:
vorhandene SAX-Messungen stammen weiterhin allein vom Coordinator.

## Auswirkungen und Nachweis

Das Lastprofil kann später auch während SAX-Leere, Laden und Entladesperre
unabhängigen Bedarf beobachten. Der Live-Abgleich muss seine Zensierung dann an
die neue Quelle anpassen: Eine SAX-Sperre macht eine gute unabhängige Hausmessung
nicht ungültig. Archiv und Bandbreite dürfen deren Fehler jedoch nicht mit alten
SAX-Fehlern mischen. Im Planer wird vollständige Hauslast verwendet und passende
PV genau einmal abgezogen. Eine allgemeine 24-Stunden-Regelung ist nicht
automatisch mitbeauftragt.

Abnahme verlangt die obigen Energiebilanzen sowie Tests für Vorzeichen,
Zeitsynchronität, Zählerreset, positive Energie über Lücken, Mehrfachzählung bei
Hybridtopologien, DST, Quellenwechsel, Neustart und identitätsgleichen
Entity-Namenswechsel. Ein technischer Nachweis vergleicht zuerst die zusätzlich
beobachtete Dauer; anschließend Prognosefehler auf vorab archivierten gemeinsamen
Zielen. Höhere Abdeckung und geringere Fehler sind getrennte Ergebnisse.
Einsparungen und Autarkie werden daraus nicht ohne eigenen Nachweis abgeleitet.

Dieses Konzept wird zusammen mit dem finalen Änderungsstand unabhängig geprüft.
Erst eine bestätigte konkrete Quelle und ein separater Implementierungsauftrag
führen zur produktiven Quellenwahl.
