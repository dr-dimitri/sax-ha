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

## Inhaltsverzeichnis

- [Funktionen](#funktionen)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Einrichtung](#einrichtung)
- [Wichtige Entitäten](#wichtige-entitäten)
- [Max-SOC-Sperre](#max-soc-sperre)
- [Ladefunktionen](#ladefunktionen)
  - [Zeitgesteuerte Netzladung](#zeitgesteuerte-netzladung)
  - [Netzdienliches Laden](#netzdienliches-laden)
  - [Preisoptimiertes Laden](#preisoptimiertes-laden)
- [Zeitfenster und Überschneidungen](#zeitfenster-und-überschneidungen)
- [Tarifmodell für die Wirtschaftlichkeit](#tarifmodell-für-die-wirtschaftlichkeit)
- [Herkunft der Ladeenergie](#herkunft-der-ladeenergie)
- [Wirtschaftlichkeitsbilanz](#wirtschaftlichkeitsbilanz)
- [Ersparnisübersicht](#ersparnisübersicht)
- [ROI und Amortisationsprognose](#roi-und-amortisationsprognose)
- [Datenqualität, Diagnose und Bilanzneustart](#datenqualität-diagnose-und-bilanzneustart)
- [Energy-Dashboard](#energy-dashboard)
- [Aktionen für Automationen](#aktionen-für-automationen)
- [Verbindung nachträglich ändern](#verbindung-nachträglich-ändern)
- [Diagnose und Fehlersuche](#diagnose-und-fehlersuche)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)
- [Hilfe und Entwicklung](#hilfe-und-entwicklung)

## Funktionen

- Ladezustand, Lade- und Entladeleistung, Netzleistung, PV-Leistung sowie
  weitere Geräte- und Akkudaten anzeigen
- Lade- und Entladeenergie im Home-Assistant-Energy-Dashboard erfassen
- geladene Energie zusätzlich nach Netz, PV und unbekannter Herkunft
  aufteilen
- Speicher ein- und ausschalten
- maximalen Ladezustand festlegen
- zeitgesteuert aus dem Netz laden
- PV-Ladung für eine bessere Nutzung der Mittagsspitze verschieben
- bei dynamischen Stromtarifen in günstigen Zeiträumen laden
- optional einen Stromtarif hinterlegen, an dem sich die Wirtschaftlichkeit
  bemisst
- daraus Netzladekosten, entgangene Einspeisevergütung, vermiedene
  Netzkosten und eine nichtnegative Netto-Ersparnis bilanzieren
- optional aus Investitionskosten ROI, Amortisationsfortschritt und eine
  30-Tage-Amortisationsprognose berechnen
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
- netzdienliches Laden,
- dynamisches Laden,
- Wirtschaftlichkeit (Status/Preise, beim tageszeitabhängigen Tarif der
  hinterlegte Tarifplan mit Hervorhebung des gerade geltenden Zeitfensters,
  Herkunft der Ladeenergie, operative Geldbilanz, Investition/Amortisation
  samt Fortschritts-Gauge sowie ein 30-Tage-Verlaufsdiagramm - referenziert
  ausschließlich bereits bestehende Entities, siehe
  [Tarifmodell für die Wirtschaftlichkeit](#tarifmodell-für-die-wirtschaftlichkeit),
  [ROI und Amortisationsprognose](#roi-und-amortisationsprognose)
  und [Datenqualität, Diagnose und Bilanzneustart](#datenqualität-diagnose-und-bilanzneustart))
  sowie
- Ersparnis (kompakte Netto-Ergebnisse für heute, diese Woche, diesen Monat,
  dieses Jahr und insgesamt seit Bilanzbeginn; ausschließlich aus der
  vorhandenen Wirtschaftlichkeitsbilanz).

![Dashboard mit allgemeinen Informationen zum SAX-Power-Speicher](docs/images/dashboard/allgemeine_information.png)

*Allgemeine Informationen mit Ladezustand, Leistung, Energie und Gerätedaten.*

Das Dashboard erscheint in der Seitenleiste und kann wie jedes andere
Home-Assistant-Dashboard angepasst oder entfernt werden.

Falls es später angelegt werden soll, steht unter **Entwicklertools → Aktionen**
die Aktion `sax_power.create_dashboard` zur Verfügung. Mit
`sax_power.reinstall_dashboard` lässt es sich auf den aktuellen
Auslieferungszustand zurücksetzen. Dabei werden eigene Änderungen am Dashboard
überschrieben.

Das Dashboard wird **nur bei der Ersteinrichtung** angelegt und danach nicht
mehr verändert – eigene Anpassungen bleiben dadurch erhalten. Bringt ein
Update der Integration einen neuen Tab oder eine fachlich notwendige
Aktualisierung der Ersparnisbereiche mit, fehlt diese einem bestehenden
Dashboard deshalb. Home Assistant meldet das unter **Einstellungen → System →
Reparaturen** und bietet dort an, das Dashboard neu aufzubauen; wer das
ablehnt, wird nicht erneut gefragt.

## Wichtige Entitäten

Home Assistant ordnet die Entitäten automatisch dem SAX-Power-Gerät zu. Weniger
häufig benötigte Detailwerte befinden sich im Bereich **Diagnose** der
Geräteseite.

### Messwerte

Zu den wichtigsten Messwerten gehören:

- Ladezustand des Speichers
- getrennte Lade- und Entladeleistung sowie eine kombinierte Leistung
- Netzbezug und Netzeinspeisung
- PV-Leistung, sofern sie vom verwendeten Smart Meter bereitgestellt wird
- Zelltemperatur
- verfügbare Lade- und Entladeleistung
- Geräte-, Firmware- und Akkustatus

Bei der **Netzleistung** gilt die in Home Assistant übliche Darstellung:
Positive Werte stehen für Netzbezug, negative Werte für Einspeisung.

Die **Lade-/Entladeleistung** bildet beide Flussrichtungen in einer Entität
ab: Positive Werte stehen für Entladung, negative Werte für Ladung.

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

![Dashboard für die zeitgesteuerte Netzladung](docs/images/dashboard/netzladen.png)

*Zeitfenster, Startschwelle und aktive Monate der Netzladung.*

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

![Dashboard für das netzdienliche Laden](docs/images/dashboard/netzdienliches_laden.png)

*Ladepause, PV-Prognose und aktive Monate des netzdienlichen Ladens.*

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

![Dashboard für das preisoptimierte Laden](docs/images/dashboard/preisoptimiertes_laden.png)

*Strategie, Preisgrenzen, Status und Planung des preisoptimierten Ladens.*

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

## Tarifmodell für die Wirtschaftlichkeit

Damit die Integration bewerten kann, was eine Kilowattstunde aus dem Netz
tatsächlich kostet, lässt sich unter **Einstellungen → Geräte & Dienste →
SAX Power Home → Konfigurieren** ein Tarifmodell hinterlegen. Die
Konfiguration ist vollständig optional: Solange **Deaktiviert** eingestellt
ist, arbeitet die Integration exakt wie bisher. Bestehende Installationen
werden nicht automatisch umgestellt.

| Tarifmodell | Bedeutung |
| --- | --- |
| Deaktiviert | Keine Wirtschaftlichkeitsauswertung (Vorgabe) |
| Festpreis | Ein ganztägig konstanter Arbeitspreis |
| Tageszeitabhängig | Ein Grundpreis und bis zu acht abweichende Zeitfenster |
| Dynamisch | Der aktuelle Preis aus dem bereits ausgewählten Strompreis-Sensor |

Bei jedem aktivierten Tarif ist zusätzlich die **Einspeisevergütung**
erforderlich. Sie ist der entgangene Erlös und damit der Beschaffungspreis
jeder PV-Kilowattstunde, die in den Speicher statt ins Netz fließt – PV-Strom
gilt in dieser Rechnung nie als kostenlos.

Alle Preise sind variable Brutto-Arbeitspreise in EUR/kWh. Monatlicher
Grundpreis, Boni, außerhalb des Arbeitspreises ausgewiesene Steuern und
sonstige Fixkosten gehören ausdrücklich nicht dazu.

### Tageszeitabhängige Zeitfenster

- Ein Zeitfenster beginnt einschließlich seiner Startzeit und endet
  ausschließlich seiner Endzeit.
- Start und Ende dürfen nicht gleich sein; das ergibt kein Zeitfenster und
  bedeutet auch nicht „ganzer Tag“.
- Ein Zeitfenster darf über Mitternacht gehen.
- Zwei Zeitfenster dürfen sich nicht überschneiden. Angrenzende Grenzen
  (Ende des einen = Beginn des nächsten) sind erlaubt.
- Außerhalb aller Zeitfenster gilt der Grundpreis.
- Maßgeblich ist die in Home Assistant eingestellte Zeitzone. In der Nacht
  der Sommerzeitumstellung gilt die Ortszeit: die im Frühjahr übersprungene
  Stunde tritt nicht auf, die im Herbst doppelte Stunde wird beide Male
  gleich bewertet.
- Jede der acht Gruppen wird entweder vollständig ausgefüllt oder bleibt
  ganz leer.

Der **Strompreis-Sensor** auf der ersten Seite wird für dieses Tarifmodell
ausdrücklich **nicht** verwendet und muss dafür auch nicht gesetzt sein: Ein
dynamischer Preis-Sensor liefert eine Zeitreihe für die nächsten Stunden,
hier wird dagegen ein täglich wiederkehrendes Preisprofil hinterlegt – beide
Formate lassen sich nicht ineinander überführen. Für das preisoptimierte
Laden bleibt der Sensor unabhängig vom Tarifmodell die Quelle; für die
Wirtschaftlichkeit ist er es nur beim Tarifmodell **Dynamisch**.

Der hinterlegte Tarifplan ist im Dashboard-Tab **Wirtschaftlichkeit**
sichtbar: eine Tabelle aus Beginn, Ende und Arbeitspreis, sortiert nach
Beginn, mit dem Grundpreis als letzter Zeile. Die gerade geltende Zeile ist
mit **jetzt** markiert, darunter steht der nächste Preiswechsel. Damit lässt
sich ohne Umweg über den Konfigurationsdialog prüfen, ob die Zeitfenster so
angekommen sind wie eingegeben. Dieselben Angaben stehen als Attribute am
Sensor **Aktueller Netzbezugspreis** (`tariff_type`, `quote_source`,
`active_window`, `next_price_change_at`, `base_price_eur_kwh`, `windows`) und
sind damit auch in eigenen Automatisierungen und Vorlagen nutzbar.

Der dynamische Tarif nutzt bewusst denselben Strompreis-Sensor samt dessen
Attribut- und Einheiteneinstellung wie das preisoptimierte Laden – es gibt
keine zweite Preisquelle. Ohne ausgewählten Sensor lässt sich dieses
Tarifmodell nicht speichern. Liefert der Sensor keinen brauchbaren Wert
(unbekannt, nicht verfügbar, keine Zahl, fremde Einheit, ein Preis außerhalb
von -2 bis 5 EUR/kWh oder eine Preisvorschau, die unlesbar ist oder den
aktuellen Zeitpunkt nicht abdeckt), gilt der Preis als unbekannt; er wird nie
durch 0 EUR/kWh ersetzt. Der Grund steht im Diagnose-Download.

Bringt der Sensor eine Preisvorschau mit, ist sie verbindlich – der
Sensorzustand wird nur dann als aktueller Preis verwendet, wenn gar keine
Vorschau vorliegt. Ein im Feld **Attribut mit der Preisvorschau** ausdrücklich
angegebenes Attribut gilt dabei bereits als Vorschau, sobald es überhaupt
einen Wert enthält.

Änderungen am Tarifmodell wirken sofort und ohne Neustart der Integration –
allerdings nur für zukünftige Messintervalle. Bereits erfasste Geldbeträge
werden nie rückwirkend neu bewertet.

Unabhängig von der gewählten Tarifart lassen sich auf derselben Seite
optional die Felder **Investitionskosten (EUR)** und **Bereits
erwirtschafteter Ertrag (EUR)** ausfüllen. Die Investitionskosten schalten
die in [ROI und Amortisationsprognose](#roi-und-amortisationsprognose)
beschriebenen Sensoren frei; ein Wechsel des Tarifmodells löscht keinen der
beiden Werte.

### Beispiele je Tarifart

Alle drei Beispiele gehen von derselben Einspeisevergütung (0,08 EUR/kWh)
sowie von 1 kWh Netzladung, 1 kWh PV-Ladung und 1 kWh späterer Entladung
aus - nur der zum jeweiligen Zeitpunkt gültige Netzbezugspreis
unterscheidet sich:

- **Festpreis** (0,30 EUR/kWh ganztägig): Netzladekosten = 1 kWh × 0,30
  EUR/kWh = 0,30 EUR. PV-Opportunitätskosten = 1 kWh × 0,08 EUR/kWh = 0,08
  EUR. Vermiedene Netzkosten (Entladung um 0,30 EUR/kWh) = 1 kWh × 0,30
  EUR/kWh = 0,30 EUR. Der operative Roh-Cashflow beträgt 0,30 − 0,30 −
  0,08 = **−0,08 EUR**; die sichtbare Netto-Ersparnis bleibt bei **0 EUR**.
- **Tageszeitabhängig** (Grundpreis 0,25 EUR/kWh, Zeitfenster 17:00–20:00
  Uhr zu 0,40 EUR/kWh): Lädt die Netzladung innerhalb des Zeitfensters,
  kosten die 1 kWh 0,40 EUR statt 0,25 EUR - außerhalb des Fensters gilt
  durchgehend der Grundpreis. PV-Opportunitätskosten und die Bewertung
  einer späteren Entladung folgen exakt derselben Formel wie beim
  Festpreis, nur mit dem zum jeweiligen Zeitpunkt gültigen Preis.
- **Dynamisch** (Strompreis-Sensor liefert z. B. 0,22 EUR/kWh zum
  Ladezeitpunkt, 0,35 EUR/kWh zum späteren Entladezeitpunkt):
  Netzladekosten = 1 kWh × 0,22 EUR/kWh = 0,22 EUR, vermiedene Netzkosten
  = 1 kWh × 0,35 EUR/kWh = 0,35 EUR - Laden und Entladen werden bewusst
  mit dem jeweils zu ihrem eigenen Zeitpunkt gültigen Preis bewertet, nie
  mit einem einzigen "aktuellen" Preis für beide Vorgänge.

### Formeln im Überblick

```
Netzladekosten          = geladene Netzenergie (kWh) × Netzbezugspreis zum Ladezeitpunkt
PV-Opportunitätskosten  = geladene PV-Energie (kWh) × Einspeisevergütung
Vermiedene Netzkosten   = monetarisierbare Entladung (kWh) × Netzbezugspreis zum Entladezeitpunkt
Operativer Roh-Cashflow = Vermiedene Netzkosten − Netzladekosten − PV-Opportunitätskosten
Netto-Ersparnis         = max(bisherige Netto-Ersparnis, operativer Roh-Cashflow, 0)
Amortisationsstand      = Netto-Ersparnis + Bereits erwirtschafteter Ertrag
ROI (%)                 = Amortisationsstand ÷ Investitionskosten × 100
Amortisationsfortschritt (%) = ROI, auf 0 bis 100 % begrenzt
Restbetrag              = max(Investitionskosten − Amortisationsstand, 0)
30-Tage-Prognose        = Durchschnitt der Netto-Ersparnis-Zuwächse der letzten 30 Tage
Jahreshochrechnung      = 30-Tage-Durchschnitt × 365,2425
```

### Grenzen der Wirtschaftlichkeitsauswertung

- Die Herkunftsaufteilung (Netz/PV) ist eine **Schätzung am
  Netzanschlusspunkt** (siehe [Herkunft der Ladeenergie](#herkunft-der-ladeenergie)),
  keine physikalische Einzelstromverfolgung.
- Monatlicher Grundpreis, Finanzierungskosten, Wartung und
  Batteriealterung sind **nicht Bestandteil** dieser Rechnung - der
  operative Roh-Cashflow bildet ausschließlich die reinen Arbeitspreis-
  Zahlungsströme ab. Die sichtbare Netto-Ersparnis ist dessen historischer
  Höchststand und fällt deshalb durch spätere Kosten nicht zurück.
- Die 30-Tage-Prognose und das geschätzte Amortisationsdatum sind
  **keine Garantie**: Sie schreiben die letzten 30 Tage unverändert fort
  und reagieren nicht auf künftige Preis-, Verbrauchs- oder
  Nutzungsänderungen.
- Eine Änderung des Tarifmodells oder der Investitionskosten wirkt
  ausschließlich prospektiv - bereits verbuchte Beträge und eine bereits
  erreichte Amortisation werden nie rückwirkend neu berechnet.

## Herkunft der Ladeenergie

Zusätzlich zu **Geladene Energie (gesamt)** zeigen zwei weitere Sensoren, wie
viel der geladenen Energie rechnerisch aus dem Netz und wie viel aus PV
stammt:

- **Geladene Energie aus dem Netz**
- **Geladene Energie aus PV**

Beide zusammen ergeben immer die Gesamtladung - eine dritte Kategorie gibt
es nicht, denn physikalisch speist entweder die PV-Anlage oder das Netz.

Diese Aufteilung funktioniert unabhängig davon, ob unter
[Tarifmodell für die Wirtschaftlichkeit](#tarifmodell-für-die-wirtschaftlichkeit)
eine Geldbewertung aktiviert ist, und ist eine **Schätzung anhand des
Netzanschlusspunktes**, keine physikalisch eindeutige Zuordnung: Bei
gleichzeitigem Hausverbrauch lässt sich aus Ladeleistung und Netzleistung
allein nicht herleiten, welcher Anteil der PV-Erzeugung tatsächlich in den
Speicher statt in den Hausverbrauch geflossen ist. Netzbezug, der die
aktuelle Ladeleistung übersteigt (er deckt dann zusätzlich laufenden
Hausverbrauch), zählt deshalb konservativ vollständig als Netzladung. Ist der
Netzwert selbst gerade nicht bekannt, zählt die Ladeenergie dieses Zeitraums
ebenfalls vollständig als Netzladung - das ist die teurere der beiden
Deutungen (Netzbezugspreis statt der niedrigeren Einspeisevergütung), ein
Messausfall rechnet die Bilanz also nie schön.

Die Herkunftszählung beginnt mit der ersten Installation dieser Funktion bei
0 kWh - bereits vorher geladene Energie wird nicht nachträglich einer Quelle
zugeordnet, der bestehende Gesamtzähler **Geladene Energie (gesamt)** bleibt
davon unberührt. Beide Herkunftssensoren führen diesen Startzeitpunkt als
Attribut `origin_accounting_started_at` mit; im Dashboard steht er als Zeile
**Beginn der Herkunftszählung**.

Dieser Zeitpunkt ist wichtig, sobald daneben eine
[Wirtschaftlichkeitsbilanz](#wirtschaftlichkeitsbilanz) läuft: Sie beginnt
erst mit dem ersten vollständig gespeicherten Tarif und damit in aller Regel
später als die Herkunftszählung. **Die Zähler der beiden Abschnitte sind
deshalb nicht gegeneinander verrechenbar** - 2,44 kWh geladene PV-Energie
neben 0,0084 EUR PV-Opportunitätskosten ist kein Widerspruch, wenn die
Bilanz von diesen 2,44 kWh nur die letzten 0,112 kWh erlebt hat. Vergleichbar
sind die Beträge ausschließlich mit den Zeilen **Bewertete Ladung**/
**Bewertete Entladung** derselben Karte.

## Wirtschaftlichkeitsbilanz

Ist unter [Tarifmodell für die Wirtschaftlichkeit](#tarifmodell-für-die-wirtschaftlichkeit)
ein Tarif aktiviert, bilanziert die Integration zusätzlich zur reinen
[Herkunft der Ladeenergie](#herkunft-der-ladeenergie) einen fortlaufenden
Geldwert. Bewertet wird ausschließlich tatsächlich gemessene Lade-/
Entladeenergie, nie ein Sollwert:

- **Netzladekosten**: geladene Netzenergie zum jeweils zum Ladezeitpunkt
  gültigen Netzbezugspreis.
- **PV-Opportunitätskosten**: geladene PV-Energie zur eingestellten
  Einspeisevergütung - PV-Strom gilt nie als kostenlos, weil er statt in den
  Speicher auch hätte eingespeist werden können.
- **Vermiedene Netzkosten**: entladene Energie zum jeweils zum
  Entladezeitpunkt gültigen Netzbezugspreis, also der Betrag, den der
  Hausverbrauch dadurch nicht aus dem Netz decken musste.
- **Operativer Roh-Cashflow**: vermiedene Netzkosten abzüglich
  Netzladekosten und PV-Opportunitätskosten. Dieser technische Wert kann
  durch spätere Kosten sinken und auch negativ sein.
- **Netto-Ersparnis**: ein gespeicherter Höchststand aus
  dem operativen Roh-Cashflow. Sie beginnt bei 0 und fällt nie zurück: Sind
  bereits 100 EUR erreicht, bleiben 100 EUR sichtbar, auch wenn spätere
  Kosten den operativen Roh-Cashflow auf 80 EUR senken. Erst ein neuer
  Höchststand erhöht die Ersparnis. Bei einem bisherigen Höchststand von 0
  wird ein negativer Rohwert nicht per Absolutwert positiv umgedeutet,
  sondern bleibt 0 EUR; ein früherer positiver Höchststand bleibt stehen.
  Ladeverluste bleiben in den Kostenpositionen und im Diagnose-Rohwert
  sichtbar.

Zusätzlich zeigen zwei Diagnosesensoren, welcher Anteil der Ladeenergie
(noch) nicht bewertet werden konnte: **Unbepreiste Ladeenergie**/
**Unbepreiste Entladeenergie** (z. B. weil der dynamische Preis-Sensor
kurzzeitig ausgefallen war) sowie der **Unbewertete Energiebestand**
(Herkunft-unbekannt- und unbepreist geladene Energie, die noch im Speicher
liegt). Die Sensoren **Aktueller Netzbezugspreis** und
**Einspeisevergütung** zeigen den gerade angewendeten Tarif.

**Ehrlicher Start:** Bereits vor der Aktivierung im Speicher liegende
Energie ist unbekannter Herkunft. Damit ihr späteres Entladen keinen
kostenlosen Scheingewinn erzeugt, initialisiert die Integration beim
erstmaligen Aktivieren den unbewerteten Energiebestand aus der aktuellen
Kapazität und dem aktuellen Ladezustand - jede Entladung verbraucht zuerst
diesen Bestand, ohne dabei vermiedene Netzkosten zu erzeugen. Erst danach
gilt eine Entladung als vermiedener Netzbezug. Eine spätere Tarifänderung
wirkt ausschließlich auf künftige Beträge; bereits verbuchte Werte bleiben
unverändert.

Monetäre Sensoren zeigen "unbekannt" statt 0, solange kein Tarif aktiviert
ist oder die Bilanz noch auf Kapazität/Ladezustand wartet - ein
deaktivierter Tarif soll keinen falschen Nullgewinn suggerieren.

Beim ersten Start nach einem Update von einem älteren Bilanzspeicher ist nur
der aktuelle Roh-Cashflow sicher bekannt. Die Netto-Ersparnis beginnt deshalb
ehrlich bei `max(0, aktueller Roh-Cashflow)`; ein früherer, damals noch nicht
gespeicherter Höchststand kann nicht rückwirkend erfunden werden. Weil alte
Tageswerte noch Roh-Cashflows statt Höchststandszuwächsen enthalten, startet
die 30-Tage-Prognose dabei mit neuen Tagen neu. Geldsummen und Bilanzbeginn
bleiben erhalten. Gesamt- und Tages-Netto-Ersparnis sind außerdem neue
Entities mit jeweils eigener Recorder-Historie: Bereits gespeicherte negative
oder rückläufige Gesamt- und Tagesänderungen des technischen Roh-Cashflows
werden nicht übernommen. Bei einer aktualisierten Installation kann die
Zeitraumhistorie der Netto-Ersparnis deshalb jünger sein als der weiterhin
angezeigte Bilanzbeginn.

## Ersparnisübersicht

Der sechste Tab **Ersparnis** fasst die **Netto-Ersparnis** bewusst kompakt
zusammen. Grundlage sind vermiedene Netzbezugskosten abzüglich
Netzladekosten und entgangener Einspeisevergütung. Angezeigt wird ein
gespeicherter, nichtnegativer Höchststand. Spätere Kosten verringern eine
bereits festgehaltene Ersparnis nicht; ein echtes Ergebnis von 0 bleibt als
0 EUR sichtbar. Die unmittelbar darüber erläuterte Upgrade-Grenze gilt auch
für diese Darstellung.

Die dauerhaft gleichbleibenden Erläuterungen zur Berechnung, zur
Recorder-Datenbasis und zur freien Zeitraumauswahl sind am Anfang des Tabs
unter **Hinweise zur Berechnung und Datenbasis** zusammengefasst und
standardmäßig eingeklappt. Ein Antippen öffnet sie bei Bedarf. Aktuelle
Warnungen sowie Erklärungen zu Anfangsbestand und Prognose bleiben unabhängig
davon sichtbar, weil sich ihr Inhalt mit dem Anlagenzustand ändert.

Vier Karten zeigen die Zunahme der Netto-Ersparnis im laufenden
Kalendertag, in der laufenden Kalenderwoche, im laufenden Kalendermonat und im
laufenden Kalenderjahr. Die Zeitgrenzen und Werte stammen unmittelbar aus
Home Assistants Recorder-Langzeitstatistik, nicht aus rollierenden
24-/7-/30-/365-Stunden-Fenstern. Fehlt für einen Zeitraum noch eine Statistik
oder ist die Entity vom Recorder ausgeschlossen, bleibt der Core-Zustand
`unknown`/`unavailable`; die Integration ersetzt fehlende Daten nicht durch
0 EUR.

**Gesamt seit Bilanzbeginn** zeigt ganz oben den blauen
**Amortisationsfortschritt** von 0 bis 100 %. Darunter stehen der aktuelle
Zustand des fortlaufenden Sensors `economics_net_savings` - keine
Recorder-Differenz - und der sichtbare **Bilanzbeginn** der aktuellen Bilanz.
Die Kalenderwerte umfassen die Zuwächse seit Beginn der Recorder-Aufzeichnung
und können deshalb bei einem Zeitraum über einen manuellen Bilanzneustart
durch den expliziten `last_reset` positive Zuwächse des vorherigen und des
aktuellen Bilanzabschnitts zusammenfassen. Sie dürfen dadurch vor dem
sichtbaren Bilanzbeginn beginnen, rekonstruieren aber keine Daten vor dem
Recorder-Start.
Ein optional eingetragener, bereits vor dem Bilanzbeginn erwirtschafteter
Ertrag bleibt zeitlich nicht zuordenbar und wird deshalb ausschließlich in der
ROI-/Amortisationsdarstellung berücksichtigt, nicht in Tag, Woche, Monat oder
Jahr.

### Status und unbewerteter Anfangsbestand

Im gesunden Zustand `active` bleibt der Tab ruhig: Der Statushinweis blendet
sich vollständig aus. Nur wenn Handlungsbedarf besteht oder ein Wert ohne
Kontext missverständlich wäre, erscheint am Anfang genau ein kurzer Hinweis.
Er erklärt einen deaktivierten Tarif, das Warten auf Kapazität und
Ladezustand, einen fehlenden Strompreis, unbekannte Ladeenergieherkunft,
teilweise Preisabdeckung oder einen angehaltenen Bilanz-Store. Unbekannte oder
noch nicht verfügbare Statusdaten werden neutral benannt. Jeder Hinweis
verlinkt für technische Details auf den bestehenden Tab
`/sax-power/wirtschaftlichkeit`, statt dessen Tabellen zu wiederholen.

Als letzte Karte unten rechts erklärt ein zweiter, ebenfalls nur bei Bedarf
sichtbarer Hinweis den unbewerteten Anfangsbestand. Ist dessen vorhandener
Sensorzustand positiv, lautet die Aussage mit dem aktuellen, auf drei
Dezimalstellen formatierten kWh-Wert: Beim Start der Bilanz waren bereits
**X,XXX kWh** im Speicher; Herkunft und Preis dieser Energie sind unbekannt,
deshalb wird ihre Entladung korrekt mit **0 €** bewertet. Sobald dieser
Bestand abgebaut ist, kann weitere bepreiste Entladung in die Netto-Ersparnis
eingehen. Das ist kein Messfehler. Bei 0, einem negativen oder unbekannten
Zustand sowie einer fehlenden Entity bleibt die Karte ausgeblendet. Sie
schätzt weder Restdauer noch Ladezyklen oder künftige Ersparnis.

0 ist ein echtes berechnetes Netto-Ergebnis; negative Netto-Ersparnisse sind
durch den Höchststand ausgeschlossen und `unknown`/`unavailable` werden nicht
als 0 ausgegeben. Der Gesamtwert gilt ausdrücklich **seit Bilanzbeginn**.

### Wann ist der Speicher abbezahlt?

Direkt unter den Ersparniswerten beantwortet ein kompakter Block die zentrale
Investitionsfrage. Ist ein Datum prognostizierbar, steht der vorhandene Wert
**Voraussichtlich abbezahlt am** an erster Stelle. Darunter folgen der
Restbetrag, die Jahreshochrechnung und optional das durchschnittliche
Tagesergebnis der letzten 30 vollständigen Tage. Der Amortisationsfortschritt
steht bereits ganz oben in **Gesamt seit Bilanzbeginn**. Ein eingetragener
Vorlauf-Ertrag erscheint
getrennt als **Bereits vor Bilanzbeginn berücksichtigt** und wird keinem Tag,
Monat oder Jahr zugerechnet.

Ohne hinterlegte Investitionskosten bleibt die Gauge in **Gesamt seit
Bilanzbeginn** ausgeblendet. Der Prognoseblock zeigt keine unbekannten
Detailwerte, sondern verweist auf **Geräte & Dienste → SAX Power Home →
Konfigurieren → Wirtschaftlichkeit**. Diese Anzeige reagiert direkt auf den
Zustand der vorhandenen Entity `economics_investment_configured`; ein
Dashboard-Neubau ist nach dem Hinterlegen oder Entfernen der Kosten nicht
nötig.

Ist noch kein Datum verfügbar, übersetzt der Tab die bereits vorhandenen
Prognoseinformationen in einen kurzen Grund: Es fehlen noch 30 vollständige
Tage, mindestens ein Tag wurde nicht vollständig beobachtet, die
Preisabdeckung war unzureichend, das 30-Tage-Ergebnis ist nicht positiv oder
die Prognose liegt außerhalb des unterstützten Zeithorizonts. Hat allein ein
manuell eingetragener Vorlauf den Fortschritt bereits auf 100 % gebracht,
weist der Text stattdessen auf die rechnerische Amortisation hin, ohne ein
historisches Datum zu erfinden. Für unbekannte Zustände lautet der neutrale
Hinweis: **Derzeit kann noch keine Prognose erstellt werden.** Alle Beträge,
Gründe und das Datum stammen unverändert aus den bestehenden Entities; der Tab
berechnet keine zweite Prognose.

### Freier Zeitraum

Unter den festen Werten lässt sich ein beliebiger Datumsbereich auswählen -
zum Beispiel die letzten drei, sechs oder zwölf Monate. Datumswähler,
Netto-Ergebnis und Balkendiagramm sind über den eigenen Schlüssel
`energy_sax_power_savings` miteinander verbunden und beeinflussen dadurch
keine Energy-Karten in anderen Ansichten. Die Vergleichsfunktion bleibt
deaktiviert, solange der Tab keinen gesondert beschrifteten Vergleichswert
ausgibt.

Auch diese Auswertung verwendet ausschließlich die Recorder-Langzeitstatistik
von `economics_net_savings`: Der Einzelwert ist dessen Änderung im
gewählten Zeitraum, das Diagramm enthält keine zusätzlichen Kosten- oder
Ertragsreihen. Home Assistant wählt abhängig von der Zeitspanne selbst die
passende Stunden-, Tages- oder Monatsauflösung. Der neue Sensor trennt diese
Historie vom technischen Roh-Cashflow; eine zweite Berechnung im Dashboard
gibt es nicht.

Eine Auswahl vor dem sichtbaren Bilanzbeginn erfindet keine rückwirkenden
Werte. Existiert dort Recorder-Historie aus einem früheren Bilanzabschnitt,
kann sie jedoch angezeigt werden; schneidet die Auswahl den manuellen
Neustart, kann die dargestellte Änderung positive Zuwächse aus beiden
Bilanzabschnitten enthalten. Fehlt Recorder-Historie oder ist die
Ergebnis-Entity vom Recorder ausgeschlossen, bleiben Wert und Diagramm
unbekannt beziehungsweise leer; ein mathematisches Ergebnis von 0 bleibt
davon unterscheidbar.

## ROI und Amortisationsprognose

Wird zusätzlich zum Tarif ein Feld **Investitionskosten (EUR)** ausgefüllt
(siehe [Tarifmodell für die Wirtschaftlichkeit](#tarifmodell-für-die-wirtschaftlichkeit)),
setzt die Integration die [Netto-Ersparnis](#wirtschaftlichkeitsbilanz) in
Bezug zu dieser Investition:

- **ROI**: Amortisationsstand in Prozent der Investitionskosten - durch die
  nichtnegative Netto-Ersparnis nie negativ, aber weiterhin über 100 %
  möglich (bereits mehrfach amortisiert).
- **Amortisationsfortschritt**: derselbe Wert, aber auf 0 bis 100 %
  begrenzt - für eine Fortschrittsanzeige.
- **Restbetrag bis Amortisation**: Investitionskosten abzüglich
  Amortisationsstand, nie unter 0 EUR.
- **Netto-Ersparnis heute**: nur der im laufenden Kalendertag neu erreichte
  Zuwachs des Höchststands; spätere Kosten machen ihn nicht rückläufig.

### Speicher, die schon vor der Integration liefen

Läuft die Anlage bereits seit Jahren, hat sie einen Teil der Investition
längst erwirtschaftet - die Integration kennt davon aber nichts und stünde
bei 0 % Fortschritt. Dafür gibt es das optionale Feld **Bereits
erwirtschafteter Ertrag (EUR)** auf derselben Optionsseite wie die
Investitionskosten. Der eingetragene Betrag zählt als Vorlauf zur laufend
gemessenen Netto-Ersparnis; die Summe aus beidem ist der oben verwendete
**Amortisationsstand**.

Der Wert wirkt ausschließlich auf ROI, Amortisationsfortschritt und
Restbetrag. Beim ROI weisen die Attribute **prior_result_eur** und
**measured_operating_result_eur** aus, wie sich der Wert zusammensetzt; im
Dashboard steht der Vorlauf als eigene Zeile direkt unter dem ROI.

Das **Voraussichtliche Amortisationsdatum** setzt der Vorlauf dagegen nicht:
Trägt erst er die Amortisation, dann lag der tatsächliche Zeitpunkt in einer
Vergangenheit, die diese Integration nie beobachtet hat - ein Datum von heute
wäre erfunden. Amortisationsfortschritt (100 %) und Restbetrag (0 EUR) zeigen
die erreichte Amortisation trotzdem an. **Netto-Ersparnis** und
**Netto-Ersparnis heute** zeigen weiterhin nur, was die Integration selbst
gemessen hat - sonst erschiene der eingetragene Betrag in der
30-Tage-Verlaufsgrafik als Tagesertrag. Solange die Bilanz noch nicht läuft
(kein Tarif, oder noch auf
Kapazität/Ladezustand wartend), bleiben die Amortisationssensoren
"unbekannt", auch wenn ein Vorlauf hinterlegt ist.

Alle sieben Sensoren dieses Abschnitts zeigen "unbekannt", solange keine
Investitionskosten hinterlegt sind. Von den vier oben genannten Sensoren
blenden zusätzlich bei deaktiviertem Tarif auf "unbekannt" wie die Sensoren
der Wirtschaftlichkeitsbilanz - der interne Stand läuft in beiden Fällen
unverändert weiter.

Zusätzlich berechnet die Integration eine **30-Tage-Prognose** aus genau
den jüngsten 30 zusammenhängenden, vollständig abgeschlossenen
Kalendertagen (der laufende Tag zählt nie mit): **Durchschnittliche tägliche
Netto-Ersparnis (30 Tage)** und die daraus berechnete **Hochgerechnete
jährliche Netto-Ersparnis** (Durchschnitt × 365,2425 Tage). Ist bereits ein
ausreichend positiver Durchschnitt und ein offener Restbetrag bekannt,
zeigt **Voraussichtliches Amortisationsdatum** das daraus abgeleitete
Datum. Die Prognose braucht lückenlos genau diese 30 aufeinanderfolgenden
Kalendertage - fehlt auch nur einer davon (etwa nach einem längeren
Ausfall von Home Assistant), bleibt sie "unbekannt", statt ältere Tage als
Lückenfüller zu verwenden. Sie verlangt außerdem von jedem einzelnen
dieser 30 Tage eine Preisabdeckung von mindestens 95 % - fehlt einem
einzigen Tag ausreichend Preisinformation, bleibt die gesamte Prognose
"unbekannt" statt einen verzerrten Wert zu zeigen. Genauso muss jeder
dieser 30 Tage zu mindestens 95 % tatsächlich beobachtet worden sein: War
Home Assistant an einem Tag längere Zeit aus (Neustart, Update,
Stromausfall), enthält dieser Tag nur einen Teil seines Ergebnisses und
würde Durchschnitt, Hochrechnung und Amortisationsdatum zu pessimistisch
machen - auch dann bleibt die Prognose lieber "unbekannt". Kurze
Neustarts von wenigen Minuten sind davon nicht betroffen. Beim Update von
einer Version ohne gespeicherten Netto-Ersparnis-Höchststand werden die alten
Tageswerte verworfen, weil sie noch rückläufige Roh-Cashflows enthalten und
nicht korrekt in Höchststandszuwächse umgerechnet werden können. Die
30-Tage-Prognose bleibt deshalb einmalig so lange "unbekannt", bis 30 neue,
vollständig beobachtete Kalendertage vorliegen. Die übrigen Sensoren
(Bilanz, ROI, Fortschritt, Restbetrag, Tagesergebnis) sind davon nicht
betroffen. Ein nicht positiver
Durchschnitt lässt nur das Rückzahlungsdatum unbekannt; Durchschnitt und
Hochrechnung werden trotzdem angezeigt, nie ein erfundenes Datum. Anders
als die vier "aktuellen" Sensoren bleibt diese Prognose - einschließlich
des Rückzahlungsdatums - während einer Tarifpause sichtbar, weil sie
ausschließlich auf bereits abgeschlossenen Tagen beruht.

Ist die Investition einmal tatsächlich amortisiert, bleibt das
Amortisationsdatum dauerhaft auf diesem historischen Kalendertag stehen -
eine spätere Änderung der Investitionskosten verschiebt es nicht mehr
rückwirkend.

## Datenqualität, Diagnose und Bilanzneustart

Eine Geldzahl ohne Aussage zur Datenqualität ist irreführend. Der Sensor
**Wirtschaftlichkeit Status** zeigt deshalb auf einen Blick, ob und warum
der Wirtschaftlichkeitsbilanz gerade zu trauen ist:

| Status | Bedeutung |
| --- | --- |
| Deaktiviert | Kein Tarif konfiguriert (siehe [Tarifmodell für die Wirtschaftlichkeit](#tarifmodell-für-die-wirtschaftlichkeit)) |
| Wartet auf Initialwerte | Tarif aktiv, aber Speicherkapazität/Ladezustand noch nicht bekannt |
| Speicherfehler | Der interne Bilanz-Speicher ist unlesbar - die Bilanz pausiert, bis die Integration neu geladen wird |
| Preis nicht verfügbar | Seit über 6 Stunden kein gültiger Netzbezugspreis (bei einem Fest-/Zeitfenstertarif sofort, wenn die gespeicherte Konfiguration selbst ungültig ist) |
| Herkunft nicht verfügbar | Die Herkunftsaufteilung aus [Herkunft der Ladeenergie](#herkunft-der-ladeenergie) läuft gerade nicht |
| Teilweise Preisabdeckung | Mehr als 5 % der heute geladenen oder entladenen Energie konnte nicht bepreist werden |
| Aktiv | Alles vollständig - die Bilanz ist ohne Einschränkung aussagekräftig |

Bei mehreren gleichzeitig zutreffenden Problemen zeigt der Sensor immer
das dringendste in dieser Reihenfolge. Seine Attribute liefern zusätzlich
die aktuellen Preise, den Aktivierungszeitpunkt, kumulierte bepreiste/
unbepreiste Energiemengen sowie die genauen Abdeckungsprozentsätze (die
des laufenden Tages, die den Zustand bestimmen, und die kumulierten seit
Beginn der Bilanz) - für
Dashboards und Automationen, die feiner reagieren wollen als der reine
Status.

Bleibt der interne Bilanz-Speicher länger als 6 Stunden unlesbar oder
liegt ebenso lange kein gültiger Netzbezugspreis vor, erscheint zusätzlich
ein Reparaturhinweis unter **Einstellungen → System → Reparaturen**, der
sich automatisch wieder auflöst, sobald die Ursache behoben ist.

Bei einer fehlerhaften Konfiguration (z. B. einem versehentlich falsch
eingegebenen Tarif) lässt sich über den Service **Wirtschaftlichkeitsbilanz
neu starten** (`sax_power.restart_economics_accounting`) eine neue,
prospektive Bilanz beginnen: Alle bisherigen Geldsummen, Preisabdeckungs-
zähler und die Amortisationshistorie werden zurückgesetzt, der unbekannte
Anfangsbestand wird wie bei der erstmaligen Aktivierung neu ermittelt. Der
Aufruf verlangt zur Sicherheit das Feld **Bestätigen** exakt auf „wahr“
gesetzt und akzeptiert optional einen freien **Grund**-Text, der
ausschließlich im Diagnose-Download erscheint. Die Energiezähler
(**Geladene/Entladene Energie**) und die Herkunftsaufteilung aus
[Herkunft der Ladeenergie](#herkunft-der-ladeenergie) bleiben davon
vollständig unberührt - es gibt keine rückwirkende Neuberechnung.

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
| `sax_power.start_grid_charge` | Manuelle Netzladung mit einem strikt negativen Leistungssollwert starten oder sofort aktualisieren |
| `sax_power.stop_grid_charge` | Manuelle Netzladung kontrolliert beenden und die SmartMeter-Regelung wieder freigeben |
| `sax_power.set_timed_charge_window` | Start und Ende der zeitgesteuerten Netzladung gemeinsam setzen |
| `sax_power.set_grid_serving_window` | Start und Ende des netzdienlichen Ladens gemeinsam setzen |
| `sax_power.refresh_price_plan` | Ladeplan nach aktualisierten Preisdaten sofort neu berechnen |
| `sax_power.set_price_charge_enabled` | Preisoptimiertes Laden per Automation schalten |
| `sax_power.create_dashboard` | Mitgeliefertes Dashboard nachträglich anlegen |
| `sax_power.reinstall_dashboard` | Dashboard auf den Auslieferungszustand zurücksetzen |

Die für eine Aktion verfügbaren Felder und Beschreibungen zeigt Home Assistant
direkt im Aktionseditor an. Für den normalen Betrieb werden die manuellen
Aktionen zum Starten und Stoppen einer Netzladung nicht benötigt.

`sax_power.start_grid_charge` akzeptiert ausschließlich ganzzahlige
Ladesollwerte von **-32768 bis -1 W**. Null, positive Werte und damit eine
manuelle Entladung werden abgelehnt. Der Aufruf verwendet denselben zentralen
SunSpec-Steuerpfad wie die Ladeautomatiken und wartet, bis der erste wirksame
Schreibvorgang vom Speicher quittiert wurde. Eine erneute Start-Aktion ändert
den Sollwert sofort. Es gilt stets die Priorität **Max-SOC-Sperre → manuelle
Netzladung → zeitgesteuertes Laden → netzdienliches Laden → preisoptimiertes
Laden**. `sax_power.stop_grid_charge` wartet das Ende des gemeinsamen
Schreib-Tasks ab, versucht aktiv zur SmartMeter-Nullregelung zurückzukehren und
gibt danach weiterhin berechtigte Automatiken wieder frei.

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
