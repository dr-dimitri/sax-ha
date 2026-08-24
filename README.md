<p align="center">
  <img src="custom_components/sax_power/brand/logo.png" alt="SAX Power Home Logo" width="192">
</p>

<h1 align="center">SAX Power Home für Home Assistant</h1>

<p align="center">
  Lokale Einbindung und intelligente Ladesteuerung für SAX Power Home und
  SAX Power Home Plus.
</p>

Die Integration verbindet einen SAX Power Heimspeicher direkt über das lokale
Netzwerk mit Home Assistant. Messwerte, Einstellungen und Ladefunktionen stehen
als Entitäten zur Verfügung und lassen sich in Dashboards und Automationen
verwenden. Ein Cloud-Konto oder eine YAML-Konfiguration ist nicht erforderlich.

## Funktionen

- Ladezustand, Lade- und Entladeleistung, Netzleistung, PV-Leistung sowie
  weitere Geräte- und Akkudaten anzeigen
- Lade- und Entladeenergie im Home-Assistant-Energy-Dashboard erfassen
- Speicher ein- und ausschalten
- maximalen Ladezustand festlegen
- zeitgesteuert aus dem Netz laden
- PV-Ladung für eine bessere Nutzung der Mittagsspitze verschieben
- bei dynamischen Stromtarifen in günstigen Zeiträumen laden
- optional ein vorbereitetes SAX-Power-Dashboard anlegen
- alle Funktionen vollständig lokal im eigenen Netzwerk nutzen

## Voraussetzungen

- Home Assistant mit HACS oder Zugriff auf das Verzeichnis
  `custom_components`
- SAX Power Home oder SAX Power Home Plus im selben Netzwerk wie Home Assistant
- aktivierte Modbus-TCP-Verbindung am Speicher
- für erweiterte Messwerte und Ladefunktionen eine kompatible Firmware
  (Master V61/Gateway V54 oder neuer empfohlen)

## Installation

### Installation über HACS

1. In Home Assistant **HACS → Integrationen** öffnen.
2. Über das Menü oben rechts **Benutzerdefinierte Repositories** auswählen.
3. `https://github.com/dr-dimitri/sax-ha` als Repository eintragen und als
   Kategorie **Integration** wählen.
4. Nach **SAX Power Home** suchen und die Integration installieren.
5. Home Assistant neu starten.

### Manuelle Installation

1. Das Verzeichnis `custom_components/sax_power` in das Verzeichnis
   `custom_components` der Home-Assistant-Konfiguration kopieren.
2. Home Assistant neu starten.

## Einrichtung

Die Einrichtung erfolgt unter **Einstellungen → Geräte & Dienste → Integration
hinzufügen**. Dort nach **SAX Power** suchen und den Anweisungen folgen.

### Verbindung zum Speicher

| Feld | Beschreibung | Standard |
| --- | --- | --- |
| IP-Adresse | Lokale IP-Adresse des Speichers | – |
| Port | Modbus-TCP-Port | 502 |
| Slave-ID (Basic Mode) | Verbindung für Grundfunktionen | 64 |
| Slave-ID (SunSpec-Modus) | Verbindung für erweiterte Mess- und Ladefunktionen | 100 |
| Aktualisierungsintervall | Intervall für grundlegende Messwerte | 10 Sekunden |

Home Assistant prüft die Verbindung vor dem Abschluss der Einrichtung. Falls
die Prüfung fehlschlägt, zunächst IP-Adresse, Port und Erreichbarkeit des
Speichers kontrollieren. Bei einem Modbus-Fehler sind meist die Slave-IDs oder
die Firmware des Speichers die Ursache.

### Netzladung vorbelegen

Im nächsten Schritt können der Schalter sowie Start- und Endzeit der
zeitgesteuerten Netzladung vorbelegt werden. Diese Angaben sind optional und
lassen sich später jederzeit über die Entitäten des Geräts ändern.

Das preisoptimierte Laden wird nach der Einrichtung über **Konfigurieren** bei
der Integration eingerichtet. So kann dort direkt der bereits vorhandene
Strompreis-Sensor ausgewählt werden.

### Mitgeliefertes Dashboard

Auf Wunsch legt die Integration bei der Einrichtung ein Dashboard namens
**SAX Power** an. Es enthält Übersichten für:

- allgemeine Informationen,
- zeitgesteuertes Laden,
- netzdienliches Laden und
- dynamisches Laden.

Das Dashboard erscheint in der Seitenleiste und kann wie jedes andere
Home-Assistant-Dashboard angepasst oder entfernt werden.

Falls es später angelegt werden soll, steht unter **Entwicklertools → Aktionen**
die Aktion `sax_power.create_dashboard` zur Verfügung. Mit
`sax_power.reinstall_dashboard` lässt es sich auf den aktuellen
Auslieferungszustand zurücksetzen. Dabei werden eigene Änderungen am Dashboard
überschrieben.

## Wichtige Entitäten

Home Assistant ordnet die Entitäten automatisch dem SAX-Power-Gerät zu. Weniger
häufig benötigte Detailwerte befinden sich im Bereich **Diagnose** der
Geräteseite.

### Messwerte

Zu den wichtigsten Messwerten gehören:

- Ladezustand des Speichers
- Lade- und Entladeleistung
- Netzbezug und Netzeinspeisung
- PV-Leistung, sofern sie vom verwendeten Smart Meter bereitgestellt wird
- Zelltemperatur
- verfügbare Lade- und Entladeleistung
- Geräte-, Firmware- und Akkustatus

Bei der **Netzleistung** gilt die in Home Assistant übliche Darstellung:
Positive Werte stehen für Netzbezug, negative Werte für Einspeisung.

Die PV-Leistung ist laut Hersteller nur mit dem Smart Meter ADW200 vollständig
verfügbar. Bei anderen Smart-Meter-Modellen kann dieser Wert dauerhaft 0 W
anzeigen, obwohl die übrigen Netzwerte korrekt vorliegen.

### Einstellungen und Schalter

| Entität | Funktion |
| --- | --- |
| Max. SOC | Obergrenze für den Ladezustand und gemeinsames Ladeziel |
| Netzladung Min. SOC | Ladezustand, unterhalb dessen die zeitgesteuerte Netzladung startet |
| Speicher On/Off | Speicher ein- oder ausschalten |
| Netzladung aktiv | Zeitgesteuerte Netzladung ein- oder ausschalten |
| Netzdienliches Laden aktiv | Verschieben der PV-Ladung ein- oder ausschalten |
| Preisoptimiertes Laden aktiv | Laden nach Strompreis ein- oder ausschalten |
| Start / Ende | Zeitfenster für Netzladung und netzdienliches Laden |
| Januar bis Dezember | Monate auswählen, in denen das jeweilige Zeitfenster gilt |

Alle Einstellungen bleiben nach einem Neustart von Home Assistant erhalten.

## Max-SOC-Sperre

Mit **Max. SOC** wird der gewünschte maximale Ladezustand festgelegt. Sobald
dieser Wert erreicht ist, beendet die Integration den Ladevorgang. Die Grenze
gilt sowohl für die Ladefunktionen der Integration als auch beim Laden mit
PV-Überschuss. Bei 100 % ist die Begrenzung praktisch deaktiviert.

Beispiel: Mit **Max. SOC = 80 %** lädt der Speicher bis höchstens 80 %. Das
schafft eine Reserve und kann dabei helfen, den Akku im Alltag zu schonen.

### Regelmäßige Zellkalibrierung

Ist Max. SOC kleiner als 100 %, erlaubt die Integration alle sieben Tage eine
vollständige Ladung zur Zellkalibrierung. Die eingestellte Grenze bleibt dabei
unverändert; nur für diesen Kalibrierungsvorgang darf der Speicher 100 %
erreichen. Die Funktion startet keine zusätzliche Netzladung, sondern nutzt
die nächste reguläre Lademöglichkeit.

Die Diagnose-Entitäten **Zellkalibrierung aktiv** und **Nächste
Zellkalibrierung** zeigen den aktuellen Zustand und den nächsten Termin.

## Ladefunktionen

Die Integration bietet drei unabhängig konfigurierbare Ladefunktionen:

| Funktion | Zweck |
| --- | --- |
| [Zeitgesteuerte Netzladung](#zeitgesteuerte-netzladung) | Zu festgelegten Zeiten bis zum gewünschten Ladezustand aus dem Netz laden |
| [Netzdienliches Laden](#netzdienliches-laden) | PV-Ladung in ertragreiche Tageszeiten verschieben |
| [Preisoptimiertes Laden](#preisoptimiertes-laden) | Bei dynamischen Tarifen günstige Zeiträume nutzen |

Max. SOC gilt als gemeinsame Obergrenze für alle Ladefunktionen. Die
zeitgesteuerte und die preisoptimierte Netzladung können nicht gleichzeitig
aktiv sein. Home Assistant zeigt beim Wechsel eine Bestätigung an und schaltet
die bisher aktive Funktion erst nach Zustimmung aus.

Das netzdienliche Laden hat in seinem wirksamen Zeitfenster Vorrang vor dem
preisoptimierten Laden. Außerhalb dieses Zeitfensters läuft die
Preisoptimierung wie gewohnt weiter.

### Zeitgesteuerte Netzladung

Die zeitgesteuerte Netzladung lädt den Speicher in einem festgelegten
Zeitfenster aus dem Netz. Sie eignet sich beispielsweise für einen günstigen
Nachttarif oder zur Vorbereitung auf einen erwarteten hohen Verbrauch.

Benötigte Einstellungen:

- **Netzladung aktiv**
- **Start** und **Ende**
- gewünschte Monate
- **Netzladung Min. SOC** als Startschwelle
- **Max. SOC** als Ladeziel

Beispiel: Bei einem Zeitfenster von 01:00 bis 05:00 Uhr, Min. SOC von 40 % und
Max. SOC von 90 % startet die Netzladung nur, wenn der Ladezustand unter 40 %
liegt. Anschließend lädt sie bis 90 % oder bis zum Ende des Zeitfensters.

Zeitfenster über Mitternacht, etwa 23:00 bis 05:00 Uhr, werden unterstützt.
Sind Start und Ende identisch oder ist eine Zeit nicht gesetzt, bleibt die
Funktion inaktiv. Wenn ausreichend eigener PV-Strom zur Verfügung steht, wird
die Netzladung beendet und der Speicher nutzt die Sonnenenergie.

### Netzdienliches Laden

Das netzdienliche Laden verschiebt die Aufnahme von PV-Überschuss in ein
späteres Zeitfenster. Dadurch bleibt morgens mehr freie Speicherkapazität für
die ertragreiche Mittagszeit und Einspeisespitzen können reduziert werden.

Typische Einstellungen sind beispielsweise die Monate Mai bis August und eine
Ladepause am Vormittag. Außerhalb der ausgewählten Monate und Zeiten arbeitet
der Speicher normal.

Benötigte Einstellungen:

- **Netzdienliches Laden aktiv**
- **Start** und **Ende** der Ladepause
- gewünschte Monate
- optional **Mindest-PV-Prognose**

#### Mindest-PV-Prognose

Über **Einstellungen → Geräte & Dienste → SAX Power Home → Konfigurieren** kann
ein PV-Prognose-Sensor ausgewählt werden. Die Einstellung **Netzdienliches
Laden Mindest-PV-Prognose** bestimmt anschließend, ab welcher erwarteten
PV-Energie die Ladepause gilt.

- **0 kWh:** Die Prognoseprüfung ist ausgeschaltet.
- Prognose erreicht den Mindestwert: Die Ladepause wird angewendet.
- Prognose liegt darunter oder ist nicht verfügbar: Der Speicher darf bereits
  früher laden.

Beispiel: Für eine Ladepause von 08:00 bis 13:00 Uhr und einen Mindestwert von
8 kWh greift die Pause nur an Tagen, an denen mindestens 8 kWh PV-Ertrag
prognostiziert werden.

### Preisoptimiertes Laden

Das preisoptimierte Laden verwendet einen bereits in Home Assistant
vorhandenen Strompreis-Sensor. Die Integration selbst ruft keine Strompreise
von einem Anbieter ab. Geeignet sind beispielsweise Sensoren von Tibber,
Nordpool, EPEX Spot, ENTSO-E oder aWATTar sowie entsprechend aufgebaute
Template-Sensoren.

#### Einrichtung

Unter **Einstellungen → Geräte & Dienste → SAX Power Home → Konfigurieren**
stehen folgende Angaben zur Verfügung:

| Feld | Beschreibung |
| --- | --- |
| Strompreis-Sensor | Sensor mit aktuellem Preis und, je nach Strategie, zukünftigen Preisen |
| Attribut mit der Preisvorschau | Optionaler Attributname, falls die automatische Erkennung nicht passt |
| Preis-Einheit | Automatische Erkennung oder feste Auswahl von EUR/kWh beziehungsweise ct/kWh |
| PV-Prognose-Sensor | Optional für die Strategie „Smart“ und das netzdienliche Laden |
| Nutzbarer Anteil der PV-Prognose | Erwarteter Anteil der Prognose, der zum Laden verfügbar ist |

Anschließend die gewünschte **Strategie** wählen und den Schalter
**Preisoptimiertes Laden aktiv** einschalten.

#### Strategien

| Strategie | Verhalten |
| --- | --- |
| Manuell / Aus | Preisautomatik ist ausgeschaltet, Einstellungen bleiben erhalten |
| Absoluter Preis | Lädt, solange der aktuelle Preis die festgelegte Preisgrenze nicht überschreitet |
| Relativ / Günstigste Stunden | Nutzt die eingestellte Anzahl der günstigsten Stunden im verfügbaren Vorschauzeitraum |
| Smart / PV-optimiert | Berücksichtigt zusätzlich Ladezustand, Speicherkapazität und PV-Prognose |

Für **Relativ** und **Smart** wird ein Preis-Sensor mit zukünftigen Preisen
benötigt. Die Planung betrachtet die bekannten Preise der kommenden 24
Stunden. Sind noch keine Preise für den nächsten Tag verfügbar, plant die
Integration mit den bereits bekannten Zeiträumen.

Bei der Smart-Strategie reduziert eine erwartete PV-Erzeugung den aus dem Netz
zu ladenden Energiebedarf. Deckt die Prognose den Bedarf vollständig, findet
keine Netzladung statt. Die Einstellung **Anzahl Stunden** bleibt die maximale
zulässige Ladedauer.

#### Preisgrenze und Neutralpreis

Die beiden Preiswerte teilen den Tarif in drei Bereiche:

| Preisbereich | Verhalten |
| --- | --- |
| Geplanter günstiger Zeitraum | Speicher wird aus dem Netz geladen |
| Preis zwischen Preisgrenze und Neutralpreis | Speicher pausiert; der Hausverbrauch wird aus dem Netz gedeckt |
| Preis ab Neutralpreis | Speicher steht wieder für den normalen Betrieb zur Verfügung |

Der Neutralpreis muss über der Preisgrenze liegen. Andernfalls weist Home
Assistant unter **Einstellungen → Geräte & Dienste → Reparaturen** darauf hin.

Der Sensor **Preisoptimiertes Laden Status** erklärt den aktuellen Zustand,
beispielsweise **Lade aus Netz**, **Warten auf Preisabfall**, **Keine
Preisdaten** oder **PV-Prognose deckt Bedarf**. Der Sensor **Nächster Start**
zeigt das nächste geplante Ladefenster.

## Zeitfenster und Überschneidungen

Die Zeitfenster der zeitgesteuerten Netzladung und des netzdienlichen Ladens
dürfen sich in denselben Monaten nicht überschneiden. Die Integration prüft
dies automatisch.

- Bei einer unzulässigen Monatsauswahl wird die Änderung abgelehnt.
- Bei einer unzulässigen Änderung von Start oder Ende wird die geänderte Zeit
  geleert und Home Assistant zeigt eine Benachrichtigung an.

Zeitlich identische Fenster sind zulässig, wenn sie ausschließlich in
verschiedenen Monaten aktiv sind. Für Automationen können Start und Ende mit
den Aktionen `sax_power.set_timed_charge_window` und
`sax_power.set_grid_serving_window` gemeinsam gesetzt werden.

## Energy-Dashboard

Die Sensoren **Geladene Energie (gesamt)** und **Entladene Energie (gesamt)**
lassen sich direkt als Batteriesystem verwenden:

**Einstellungen → Dashboards → Energie → Batteriesysteme**

Dort den ersten Sensor für die in den Speicher geladene und den zweiten für
die aus dem Speicher entladene Energie auswählen. Die Zählerstände bleiben
über Neustarts hinweg erhalten.

## Aktionen für Automationen

Alle Aktionen werden unter **Entwicklertools → Aktionen** ausgeführt und über
das Feld `device_id` dem gewünschten SAX-Power-Gerät zugeordnet.

| Aktion | Verwendung |
| --- | --- |
| `sax_power.start_grid_charge` | Manuelle Netzladung mit einem Leistungssollwert starten |
| `sax_power.stop_grid_charge` | Manuelle Netzladung beenden |
| `sax_power.set_timed_charge_window` | Start und Ende der zeitgesteuerten Netzladung gemeinsam setzen |
| `sax_power.set_grid_serving_window` | Start und Ende des netzdienlichen Ladens gemeinsam setzen |
| `sax_power.refresh_price_plan` | Ladeplan nach aktualisierten Preisdaten sofort neu berechnen |
| `sax_power.set_price_charge_enabled` | Preisoptimiertes Laden per Automation schalten |
| `sax_power.create_dashboard` | Mitgeliefertes Dashboard nachträglich anlegen |
| `sax_power.reinstall_dashboard` | Dashboard auf den Auslieferungszustand zurücksetzen |

Die für eine Aktion verfügbaren Felder und Beschreibungen zeigt Home Assistant
direkt im Aktionseditor an. Für den normalen Betrieb werden die manuellen
Aktionen zum Starten und Stoppen einer Netzladung nicht benötigt.

## Verbindung nachträglich ändern

IP-Adresse, Port, Slave-IDs und Aktualisierungsintervall lassen sich jederzeit
anpassen:

**Einstellungen → Geräte & Dienste → SAX Power Home → Neu konfigurieren**

Die neuen Verbindungsdaten werden vor dem Speichern geprüft. Nach erfolgreicher
Prüfung lädt Home Assistant die Integration automatisch neu.

## Diagnose und Fehlersuche

| Problem | Mögliche Ursache und Lösung |
| --- | --- |
| Verbindung kann nicht hergestellt werden | IP-Adresse und Port prüfen und sicherstellen, dass Home Assistant den Speicher im lokalen Netzwerk erreicht |
| Modbus-Fehler bei der Einrichtung | Slave-IDs prüfen; die Standardwerte sind 64 und 100 |
| Viele Detailwerte sind unbekannt | SunSpec-Slave-ID und Firmware prüfen; empfohlen werden Master V61/Gateway V54 oder neuer |
| Ladefunktionen reagieren nicht | Erreichbarkeit des SunSpec-Modus sowie Statussensoren und ausgewählte Monate prüfen |
| Netzladung startet nicht | Zeitfenster, aktive Monate, Min. SOC und Max. SOC kontrollieren |
| Preisoptimiertes Laden zeigt „Keine Preisdaten“ | Preis-Sensor, Vorschauattribut und Preis-Einheit unter **Konfigurieren** prüfen |
| Zeitangabe wurde geleert | Zeitfenster von Netzladung und netzdienlichem Laden überschneiden sich |
| PV-Leistung zeigt dauerhaft 0 W | Der verwendete Smart Meter stellt diesen Wert möglicherweise nicht bereit |

Unter **Einstellungen → Geräte & Dienste → SAX Power Home → Diagnose
herunterladen** kann eine Diagnosedatei erstellt werden. Sie enthält die für
die Fehlersuche relevanten Zustände; die IP-Adresse wird dabei unkenntlich
gemacht. Die Datei kann einem Fehlerbericht auf GitHub beigefügt werden.

## Bekannte Einschränkungen

- Eine ferngesteuerte manuelle Entladung wird vom Speicher nicht unterstützt.
- Erweiterte Messwerte und Ladefunktionen benötigen den SunSpec-Modus. Die
  grundlegenden Messwerte bleiben auch dann verfügbar, wenn dieser Modus nicht
  erreichbar ist.
- Die Strategien **Relativ** und **Smart** benötigen zukünftige Preisdaten. Mit
  einem Sensor, der nur den aktuellen Preis liefert, steht weiterhin die
  Strategie **Absoluter Preis** zur Verfügung.
- Die Strategie **Smart** benötigt zusätzlich Speicherkapazität und
  PV-Prognose. Fehlen diese Angaben, verhält sie sich wie **Relativ**.

## Hilfe und Entwicklung

Fehler und Verbesserungsvorschläge können über die
[GitHub-Issues](https://github.com/dr-dimitri/sax-ha/issues) gemeldet werden.
Für eine zügige Analyse bitte die Home-Assistant-Version, die Firmware des
Speichers, eine kurze Beschreibung des beobachteten Verhaltens und nach
Möglichkeit die Diagnosedatei angeben.

Technische Informationen für Mitwirkende befinden sich in:

- [DEVELOPMENT.md](DEVELOPMENT.md) – Architektur, lokale Entwicklung und Tests
- [anforderung.yaml](anforderung.yaml) – vollständige Verhaltensanforderungen
- [AGENTS.md](AGENTS.md) – Arbeitsregeln für Coding-Agenten
