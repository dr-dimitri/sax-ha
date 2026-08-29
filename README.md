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
- [ROI und Amortisationsstand](#roi-und-amortisationsstand)
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
  Netzkosten und ein signiertes Nettoergebnis bilanzieren
- optional aus Investitionskosten ROI, Amortisationsfortschritt und den
  verbleibenden Restbetrag berechnen
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
- Ersparnis (kompakte Netto-Ergebnisse für heute, diese Woche, diesen Monat,
  dieses Jahr und insgesamt seit Bilanzbeginn, Tarifinformation,
  Amortisationsstand und verständliche Statushinweise; ausschließlich aus
  der vorhandenen Wirtschaftlichkeitsbilanz).

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
| Preis-Einheit | Automatische Erkennung oder feste Auswahl von EUR/kWh, ct/kWh, EUR/MWh beziehungsweise ct/MWh |
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

Der hinterlegte Tarifplan ist im Dashboard-Tab **Ersparnis**
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
die in [ROI und Amortisationsstand](#roi-und-amortisationsstand)
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
Netto-Ersparnis         = operativer Roh-Cashflow
Amortisationsstand      = Netto-Ersparnis + Bereits erwirtschafteter Ertrag
ROI (%)                 = Amortisationsstand ÷ Investitionskosten × 100
Amortisationsfortschritt (%) = ROI, auf 0 bis 100 % begrenzt
Restbetrag              = max(Investitionskosten − Amortisationsstand, 0)
```

### Grenzen der Wirtschaftlichkeitsauswertung

- Die Herkunftsaufteilung (Netz/PV) ist eine **Schätzung am
  Netzanschlusspunkt** (siehe [Herkunft der Ladeenergie](#herkunft-der-ladeenergie)),
  keine physikalische Einzelstromverfolgung.
- Monatlicher Grundpreis, Finanzierungskosten, Wartung und
  Batteriealterung sind **nicht Bestandteil** dieser Rechnung - der
  operative Nettoergebnis bildet ausschließlich die reinen Arbeitspreis-
  Zahlungsströme ab und sinkt deshalb auch durch spätere Kosten.
- Eine Änderung des Tarifmodells oder der Investitionskosten wirkt
  ausschließlich prospektiv - bereits verbuchte Beträge werden nie
  rückwirkend neu berechnet.

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
ebenfalls vollständig als Netzladung. Diese Zuordnung hält die beiden
öffentlichen Herkunftszähler vollständig, ist aber ausdrücklich keine
gemessene Herkunft: Die Wirtschaftlichkeitsbilanz bepreist das Intervall
deshalb nicht. Stattdessen erscheint die Energiemenge als unbewerteter
Bestand und reduziert die angezeigte Preisabdeckung.

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
- **Operatives Nettoergebnis**: vermiedene Netzkosten abzüglich
  Netzladekosten und PV-Opportunitätskosten. Es wird identisch als
  **Operativer Roh-Cashflow** und **Netto-Ersparnis** veröffentlicht, kann
  durch spätere Kosten sinken und auch negativ sein. Ladeverluste bleiben
  dadurch unmittelbar im Ergebnis sichtbar.

Die Sensoren **Aktueller Netzbezugspreis** und **Einspeisevergütung** zeigen
den gerade angewendeten Tarif. Beim erstmaligen Aktivieren setzt die
Integration die bereits im Speicher vorhandene Energie mit 0 EUR an. Sie wird
nicht als unbekannte Energiemenge nachgeführt; bei maximal 7 kWh ist ihr
einmaliger Einfluss auf die Amortisationsrechnung vernachlässigbar. Eine
spätere Tarifänderung wirkt ausschließlich auf künftige Beträge; bereits
verbuchte Werte bleiben unverändert.

Fehlt während einer Ladung der Smartmeter-Wert, bleibt deren genaue Herkunft
unbekannt. Obwohl der öffentliche Herkunftszähler diese Energie aus
Kompatibilitätsgründen konservativ unter Netzladung führt, entstehen weder
Netzladekosten noch PV-Opportunitätskosten. Die Ladung zählt stattdessen als
unbepreist; eine spätere Entladung dieses Bestands erzeugt keinen erfundenen
vermiedenen Geldwert. Der Status und der Diagnose-Download machen diese
fehlende Abdeckung über die unbepreisten Energiemengen sichtbar.

Monetäre Sensoren zeigen "unbekannt" statt 0, solange kein Tarif aktiviert
ist - ein deaktivierter Tarif soll keinen falschen Nullgewinn suggerieren.

Beim ersten Start nach einem Update von einem älteren Bilanzspeicher wird das
aktuelle Nettoergebnis verlustfrei aus den drei Geldsummen rekonstruiert.
Geldsummen und Bilanzbeginn bleiben erhalten. Gesamt- und Tages-Nettoergebnis
besitzen jeweils eine eigene Recorder-Historie; bei einer aktualisierten
Installation kann diese deshalb jünger sein als der weiterhin angezeigte
Bilanzbeginn.
Alle fünf kumulativen Geldsensoren melden denselben Bilanzbeginn als
`last_reset`. Ein bestätigter Bilanzneustart beginnt damit für Home Assistants
Langzeitstatistik einen neuen Abschnitt, statt den Sprung auf 0 als
künstliche Kosten- oder Ertragsänderung zu verbuchen. Normale Rückgänge durch
negative Preise oder spätere Kosten ändern diesen Zeitpunkt nicht.

## Ersparnisübersicht

Der fünfte Tab **Ersparnis** fasst das **Nettoergebnis** bewusst kompakt
zusammen. Grundlage sind vermiedene Netzbezugskosten abzüglich
Netzladekosten und entgangener Einspeisevergütung. Spätere Kosten reduzieren
den Wert; Mehrkosten werden negativ angezeigt. Ein echtes Ergebnis von 0
bleibt als 0 EUR sichtbar.

Die Erläuterungen zur Berechnung, zur Recorder-Datenbasis und zur freien
Zeitraumauswahl sind nach
den Zeitraumwerten unter **Hinweise zur Berechnung und Datenbasis**
zusammengefasst und
standardmäßig eingeklappt. Ein Antippen öffnet sie bei Bedarf. Aktuelle
Warnungen bleiben davon unabhängig.

Zwischen den festen Kalenderwerten und diesen Erläuterungen zeigt der Tab
die dynamische Tarifinformation. Sie
liest den tageszeitabhängigen Tarifplan aus der aktuellen Preis-Entity und
reagiert deshalb ohne Dashboard-Neubau auf Tarifänderungen.

Vier Karten zeigen die Änderung des Nettoergebnisses im laufenden
Kalendertag, in der laufenden Kalenderwoche, im laufenden Kalendermonat und im
laufenden Kalenderjahr. Die Zeitgrenzen und Werte stammen unmittelbar aus
Home Assistants Recorder-Langzeitstatistik, nicht aus rollierenden
24-/7-/30-/365-Stunden-Fenstern. Fehlt für einen Zeitraum noch eine Statistik
oder ist die Entity vom Recorder ausgeschlossen, bleibt der Core-Zustand
`unknown`/`unavailable`; die Integration ersetzt fehlende Daten nicht durch
0 EUR.

Der aktuelle Zustand des fortlaufenden Sensors `economics_net_savings` und
der sichtbare **Bilanzbeginn** stehen im Amortisationsblock direkt unter dem
Restbetrag. Der Gesamtwert ist keine Recorder-Differenz. Die
Kalenderwerte umfassen die Zuwächse seit Beginn der Recorder-Aufzeichnung und
können deshalb bei einem Zeitraum über einen manuellen Bilanzneustart durch
den expliziten `last_reset` positive Zuwächse des vorherigen und des aktuellen
Bilanzabschnitts zusammenfassen. Sie dürfen dadurch vor dem sichtbaren
Bilanzbeginn beginnen, rekonstruieren aber keine Daten vor dem Recorder-Start.
Ein optional eingetragener, bereits vor dem Bilanzbeginn erwirtschafteter
Ertrag bleibt zeitlich nicht zuordenbar und wird deshalb ausschließlich in der
ROI-/Amortisationsdarstellung berücksichtigt, nicht in Tag, Woche, Monat oder
Jahr.

### Status

Im gesunden Zustand `active` bleibt der Tab ruhig: Der Statushinweis am Ende
des Tabs blendet sich vollständig aus. Nur wenn Handlungsbedarf besteht oder
ein Wert ohne Kontext missverständlich wäre, erscheint genau ein kurzer
Hinweis. Er erklärt einen deaktivierten Tarif, einen fehlenden Strompreis,
unbekannte Ladeenergieherkunft,
teilweise Preisabdeckung oder einen angehaltenen Bilanz-Store. Unbekannte oder
noch nicht verfügbare Statusdaten werden neutral benannt. Einen separaten
technischen Wirtschaftlichkeits-Tab oder einen Link auf einen solchen Pfad
gibt es nicht.

0 ist ein echtes berechnetes Netto-Ergebnis; ein negativer Wert weist reale
Mehrkosten seit Bilanzbeginn aus. `unknown`/`unavailable` werden nicht als 0
ausgegeben.

### Amortisation

Der erste Block zeigt bei hinterlegten Investitionskosten den blauen
Amortisationsfortschritt und darunter in einer gemeinsamen Liste den
**Restbetrag bis Amortisation**. Direkt danach folgt der optionale
Vorlauf-Ertrag als **Bereits vor Bilanzbeginn berücksichtigt** mit der Einheit
**€** und exakt zwei Nachkommastellen, anschließend **Netto-Ersparnis** und
**Bilanzbeginn**. Alle Währungsangaben im Ersparnis-Tab erscheinen mit zwei
Nachkommastellen; intern und im Recorder bleibt die höhere Rechengenauigkeit
erhalten. Eine separate sichtbare Überschrift **Amortisation** besitzt dieser
Block nicht.

Ohne Investitionskosten verweist der Block auf **Geräte & Dienste → SAX Power
Home → Konfigurieren → Wirtschaftlichkeit**. Die Anzeige reagiert direkt auf
den Zustand von `economics_investment_configured`; ein Dashboard-Neubau ist
nach dem Hinterlegen oder Entfernen der Kosten nicht nötig.

Eine künftige Amortisation wird nicht mehr hochgerechnet. Das frühere
voraussichtliche Datum, der 30-Tage-Durchschnitt, die Jahreshochrechnung und
die zugehörigen Prognosehinweise entfallen.
### Freier Zeitraum

Unter den festen Werten lässt sich ein beliebiger Datumsbereich auswählen -
zum Beispiel die letzten drei, sechs oder zwölf Monate. Datumswähler,
Netto-Ergebnis und Balkendiagramm sind über den eigenen Schlüssel
`energy_sax_power_savings` miteinander verbunden und beeinflussen dadurch
keine Energy-Karten in anderen Ansichten. Die Vergleichsfunktion bleibt
deaktiviert, solange der Tab keinen gesondert beschrifteten Vergleichswert
ausgibt. Der Block beginnt direkt mit dem Datumswähler und besitzt keine
separate sichtbare Überschrift **Freier Zeitraum**.

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

## ROI und Amortisationsstand

Mit hinterlegten **Investitionskosten (EUR)** setzt die Integration das
[Nettoergebnis](#wirtschaftlichkeitsbilanz) in Bezug zur Investition:

- **ROI**: Amortisationsstand in Prozent der Investitionskosten, über 100 %
  möglich.
- **Amortisationsfortschritt**: derselbe Wert, auf 0 bis 100 % begrenzt.
- **Restbetrag bis Amortisation**: Investitionskosten abzüglich
  Amortisationsstand, nie unter 0 EUR.
- **Netto-Ersparnis heute**: das signierte Ergebnis des laufenden
  Kalendertags.

Für Anlagen, die schon vor Einrichtung der Integration liefen, kann
**Bereits erwirtschafteter Ertrag (EUR)** hinterlegt werden. Dieser Vorlauf
zählt nur zu ROI, Fortschritt und Restbetrag. Netto-Ersparnis und
Netto-Ersparnis heute bleiben reine Messwerte, damit Recorder-Auswertungen
keinen künstlichen Tagesertrag erhalten.

Ohne Investitionskosten oder ohne laufende Bilanz bleiben die vier Sensoren
unbekannt. Eine künftige Amortisation, ein geschätztes Datum, ein
30-Tage-Durchschnitt und eine Jahreshochrechnung werden bewusst nicht
berechnet.
## Datenqualität, Diagnose und Bilanzneustart

Eine Geldzahl ohne Aussage zur Datenqualität ist irreführend. Der Sensor
**Wirtschaftlichkeit Status** zeigt deshalb auf einen Blick, ob und warum
der Wirtschaftlichkeitsbilanz gerade zu trauen ist:

| Status | Bedeutung |
| --- | --- |
| Deaktiviert | Kein Tarif konfiguriert (siehe [Tarifmodell für die Wirtschaftlichkeit](#tarifmodell-für-die-wirtschaftlichkeit)) |
| Speicherfehler | Der interne Bilanz-Speicher ist unlesbar - die Bilanz bleibt bis zur Wiederherstellung eingefroren; bloßes Neuladen setzt sie nicht zurück |
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
Hat Home Assistant eine beschädigte Datei als `.corrupt.*` gesichert, wird
diese Sicherung niemals automatisch durch eine neue Nullbilanz ersetzt.
Spiele einen gültigen Store aus einem Backup an den ursprünglichen Pfad
zurück und lade die Integration danach neu. Ein bloßer Config-Entry-Reload
gilt weder als Reparatur noch als Zustimmung zu einer neuen Nullbilanz.

Bei einer fehlerhaften Konfiguration (z. B. einem versehentlich falsch
eingegebenen Tarif) lässt sich über den Service **Wirtschaftlichkeitsbilanz
neu starten** (`sax_power.restart_economics_accounting`) eine neue,
prospektive Bilanz beginnen: Alle bisherigen Geldsummen, Preisabdeckungs-
zähler und die Amortisationshistorie werden zurückgesetzt, der interne
unbewertete Bestand wird wie bei der erstmaligen Aktivierung auf 0 gesetzt. Der
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
