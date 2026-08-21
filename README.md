# SAX Power Home – Home Assistant Integration

Bindet einen **SAX Power Home (Plus)** Heimspeicher über Modbus TCP in Home
Assistant ein: alle Messwerte als Sensoren, dazu drei Lade-Automatiken
(Netzladung nach Zeitplan, netzdienliches Laden, preisoptimiertes Laden nach
dynamischem Strompreis).

Die Einrichtung läuft vollständig über die Oberfläche – keine YAML-Konfiguration,
kein Cloud-Zugang, keine Zugangsdaten. Die Integration spricht ausschließlich
lokal mit dem Speicher.

## Inhaltsverzeichnis

- [Was die Integration kann](#was-die-integration-kann)
- [Installation](#installation)
- [Einrichtung](#einrichtung)
- [Entitäten im Überblick](#entitäten-im-überblick)
  - [Messwerte (Sensoren)](#messwerte-sensoren)
  - [Energiezähler fürs Energy-Dashboard](#energiezähler-fürs-energy-dashboard)
  - [Statusanzeigen der Lade-Automatiken](#statusanzeigen-der-lade-automatiken)
  - [Einstellungen und Schalter](#einstellungen-und-schalter)
- [Die drei Lade-Automatiken](#die-drei-lade-automatiken)
- [Max-SOC-Sperre](#max-soc-sperre)
- [Netzladung (zeitgesteuertes Laden)](#netzladung-zeitgesteuertes-laden)
- [Netzdienliches Laden](#netzdienliches-laden)
- [Preisoptimiertes Laden](#preisoptimiertes-laden)
- [Zeitfenster dürfen sich nicht überschneiden](#zeitfenster-dürfen-sich-nicht-überschneiden)
- [Services (für Automationen)](#services-für-automationen)
- [Verbindungsdaten nachträglich ändern](#verbindungsdaten-nachträglich-ändern)
- [Diagnose und Fehlersuche](#diagnose-und-fehlersuche)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)
- [Weiterführende Dokumentation](#weiterführende-dokumentation)

## Was die Integration kann

- **Alles ablesen:** Ladezustand, Lade-/Entladeleistung, Smart-Meter- und
  Netzwerte, Ströme, Spannungen, Zell- und Akkudaten – rund 60 Sensoren.
- **Energy-Dashboard:** zwei kWh-Zähler (geladen/entladen), die sich direkt als
  Batteriesystem eintragen lassen.
- **Speicher steuern:** ein/aus, Ladeleistungsgrenze, Ziel-Ladestand.
- **Automatisch laden:** drei getrennt einstellbare Automatiken – nach Zeitplan,
  netzdienlich (Laden bewusst in die Mittagsspitze verschieben) oder nach
  dynamischem Strompreis.
- **Akku schonen:** eine geräteunabhängige Max-SOC-Sperre, die auch dann greift,
  wenn der Speicher von selbst mit PV-Überschuss volllädt.
- **Fertiges Dashboard:** optional in der Ersteinrichtung anlegbar, mit den
  wichtigsten Informationen in drei Tabs (siehe
  [Schritt 3: Dashboard anlegen](#schritt-3-dashboard-anlegen-optional)).

## Installation

### Über HACS (empfohlen)

1. In Home Assistant: **HACS → Integrationen → ⋮ (oben rechts) →
   Benutzerdefinierte Repositories**
2. Repository-URL eintragen: `https://github.com/dr-dimitri/sax-ha`,
   Kategorie: **Integration**
3. **Hinzufügen**, danach "SAX Power Home" in HACS suchen und installieren
4. Home Assistant neu starten
5. Weiter mit [Einrichtung](#einrichtung)

### Manuell

1. Ordner `custom_components/sax_power` in das `custom_components`-Verzeichnis
   der Home-Assistant-Konfiguration kopieren
2. Home Assistant neu starten
3. Weiter mit [Einrichtung](#einrichtung)

## Einrichtung

**Einstellungen → Geräte & Dienste → Integration hinzufügen →** nach "SAX Power"
suchen.

### Schritt 1: Verbindung

| Feld | Bedeutung | Standard |
| --- | --- | --- |
| IP-Adresse | IP des SAX Speichers im lokalen Netz | – |
| Port | Modbus-TCP-Port | 502 |
| Slave-ID (Basic Mode) | Registerkarte mit den Grundfunktionen (Ladezustand, Schalter, Leistungslimits) | 64 |
| Slave-ID (SunSpec-Modus) | Registerkarte mit den erweiterten Mess- und Diagnosewerten | 100 |
| Aktualisierungsintervall | Abfragetakt der Basic-Mode-Sensoren in Sekunden. Die SunSpec-Messwerte werden davon unabhängig alle 2 Sekunden gelesen (siehe [Hinweis](#wie-oft-wird-abgefragt)) | 10 |

Die Verbindung wird geprüft, bevor der Eintrag angelegt wird. Schlägt das fehl:
IP-Adresse, Port und Erreichbarkeit im Netz prüfen. Meldet der Speicher einen
Modbus-Fehler, obwohl die Verbindung steht, stimmt in der Regel die Slave-ID
nicht.

### Schritt 2: Netzladung vorbelegen (optional)

Der zweite Schritt belegt die Netzladung vor: "Netzladung aktiv", "Netzladung
Start" und "Netzladung Ende". Ohne Änderung gelten die Standardwerte
(deaktiviert, Zeitfenster 00:00–00:05). Diese Vorgaben wirken nur beim
allerersten Start – danach zählt ausschließlich das, was an den Entitäten
eingestellt ist.

Das preisoptimierte Laden wird **nicht** hier, sondern später über
**Konfigurieren** eingerichtet (siehe
[Preisoptimiertes Laden](#preisoptimiertes-laden)) – ein passender
Strompreis-Sensor existiert bei einer frischen Installation oft noch gar nicht.

### Schritt 3: Dashboard anlegen (optional)

Der dritte Schritt bietet an, ein vorbereitetes Dashboard **"SAX Power"**
anzulegen – mit den wichtigsten Sensoren und Einstellungen, gegliedert in drei
Tabs: **Allgemeine Informationen**, **Ladeautomatik** (Netzladung und
netzdienliches Laden) sowie **Dynamisches Laden** (preisoptimiertes Laden).
Der Ladezustand erscheint dabei als Gauge (grün ab 50 % SOC, orange ab 20 %,
darunter rot), die wichtigsten Ein/Aus-Schalter als große Kacheln. Die
Checkbox ist standardmäßig aktiv; das Dashboard erscheint danach sofort in
der Sidebar und lässt sich jederzeit unter **Einstellungen → Dashboards**
anpassen oder wieder entfernen.

Wurde die Checkbox abgewählt, das Dashboard später gelöscht, oder wurde die
Integration schon vor Einführung dieses Features eingerichtet: Der Service
**`sax_power.create_dashboard`** (siehe [Services](#services-für-automationen))
legt es jederzeit nachträglich an – aufrufbar unter **Entwicklertools →
Aktionen**. Existiert das Dashboard bereits, passiert nichts.

Um ein bereits vorhandenes Dashboard auf diesen Auslieferungszustand
zurückzusetzen (z. B. nach eigenen Anpassungen), gibt es zusätzlich den
Button **"Dashboard neu installieren"** auf der Geräteseite der Integration
(**Einstellungen → Geräte & Dienste → SAX Power Home**, dieselbe Seite wie
der Diagnose-Export, siehe [Diagnose und
Fehlersuche](#diagnose-und-fehlersuche)) – im Unterschied zum Service
überschreibt er auch ein bereits bestehendes Dashboard.

## Entitäten im Überblick

### Messwerte (Sensoren)

Die Messwerte stammen aus zwei Registerkarten des Speichers mit
unterschiedlicher Slave-ID.

**Basic Mode (Slave-ID 64):**

| Entität | Beschreibung |
| --- | --- |
| Ladezustand | Ladestand (SOC) des Speichers in % |
| Speicher Schaltzustand (Text) | "Aus" / "Ein" / "Verbunden" als Klartext (Diagnose) |
| Sollwert Leistung P | Aktuell gesetzter P-Sollwert in W (Diagnose) |
| Sollwert cos(phi) | Aktuell gesetzter cos(phi)-Sollwert (Diagnose) |

**SunSpec-Modus (Slave-ID 100):**

| Entität | Beschreibung |
| --- | --- |
| Hersteller / Gerätemodell / Softwareversion Master und Gateway / Seriennummer | Geräteidentität (Diagnose) |
| **Ladeleistung / Entladeleistung** | Aktuelle Lade- bzw. Entladeleistung des Speichers in W |
| **Smart Meter Leistung** | Leistung am Netzanschlusspunkt. Positiv = Einspeisung/PV-Überschuss, negativ = Netzbezug |
| Speicher Stromsumme / Strom A, B, C | in A |
| Speicher Spannung A, B, C | in V |
| Wirk-, Schein-, Blindleistung Speicher Summe | in W / VA / var (Diagnose) |
| Leistungsfaktor Speicher Summe | dimensionslos |
| Netzfrequenz (Speicher) | in Hz |
| Maximale Zelltemperatur | in °C |
| Speicher Zustand / Speicher Ereignis | Klartext (Diagnose) |
| PV-Leistung | in W – nur mit Smartmeter ADW200 verfügbar (siehe Hinweis unten) |
| Leistungsvorgabe / Timeout Leistungsvorgabe / Steuermodus / Referenzwert Maximalleistung | Nur-Lese-Diagnosewerte. Leistungsvorgabe und Steuermodus werden von den Lade-Automatiken auch selbst geschrieben |
| Netz Stromsumme / Strom L1, L2, L3 | in A |
| Netzspannung Durchschnitt (L-N) / L1, L2, L3 | in V |
| Netzfrequenz | in Hz |
| Netzleistung L1, L2, L3 | in W |
| Schein-, Blindleistung, Leistungsfaktor Netz Summe | in VA / var / dimensionslos |
| Speicherkapazität / Verfügbare Lade- und Entladeleistung | in Wh / W (Diagnose) |
| Maximaler und Minimaler SoC / Akku SoC (SunSpec) / Entladetiefe | in % (Diagnose) |
| Ladestatus Akku / Akku Ereignis | Klartext (Diagnose) |
| Durchschnittliche Zellspannung | in mV (Diagnose) |

**Warum "var"?** Blindleistung wird korrekt in **var** (Volt-Ampere reaktiv)
angegeben, Scheinleistung in **VA** – dieselbe Konvention wie bei jedem
Energiemessgerät.

**Smartmeter-Modell:** PV-Leistung und einzelne Werte des Meter-Modells sind
laut Herstellerdokumentation nur mit dem Smartmeter **ADW200** vollständig
verfügbar. Mit anderen Modellen (z. B. ADL400) sind die Netzwerte (Ströme,
Spannungen, Leistungen) in der Regel trotzdem plausibel befüllt; nur die
PV-Leistung bleibt dann dauerhaft 0.

#### Wie oft wird abgefragt?

| Werte | Takt |
| --- | --- |
| Basic-Mode-Sensoren (Ladezustand, Schaltzustand, Sollwerte) | Aktualisierungsintervall aus der Einrichtung (Standard 10 s) |
| Dynamische SunSpec-Werte (Leistungen, Ströme, Spannungen, Zustände) | fest alle 2 s – damit die Lade-Automatiken zügig auf die tatsächliche Leistung reagieren |
| Geräteidentität und interne Skalierungsfaktoren | einmal pro Stunde – sie ändern sich im Betrieb praktisch nie |

Ist der SunSpec-Modus nicht erreichbar (siehe
[Bekannte Einschränkungen](#bekannte-einschränkungen)), zeigen die Sensoren aus
der SunSpec-Tabelle "unbekannt". Die Basic-Mode-Sensoren laufen unbeeindruckt
weiter.

### Energiezähler fürs Energy-Dashboard

| Entität | Beschreibung |
| --- | --- |
| Geladene Energie (gesamt) | Kumulierte, in den Speicher geladene Energie in kWh |
| Entladene Energie (gesamt) | Kumulierte, aus dem Speicher entladene Energie in kWh |

Der SAX Speicher liefert selbst keine Energiezähler, sondern nur die
Momentanleistung. Die Integration rechnet die beiden kWh-Zähler deshalb selbst
hoch (Aufsummierung bei jedem Abfragezyklus, also etwa alle 2 Sekunden) und
behält den Stand über Neustarts hinweg.

Beide Sensoren lassen sich direkt unter **Einstellungen → Dashboards → Energie
→ Batteriesysteme** als Ladung/Entladung eintragen – ohne Template-Sensoren oder
Zusatzkonfiguration.

Ist der SunSpec-Modus zwischenzeitlich nicht erreichbar, **pausiert** die
Hochrechnung für diese Zeit, statt sie später fälschlich nachzuholen.

### Statusanzeigen der Lade-Automatiken

| Entität | Beschreibung |
| --- | --- |
| Zeitgesteuertes Laden aktiv | Zeigt, ob die Netzladung gerade aktiv nachlädt |
| Netzdienliches Laden aktiv | Zeigt, ob das Laden gerade aktiv blockiert wird |
| Preisoptimiertes Laden aktiv | Zeigt, ob gerade preisoptimiert aus dem Netz geladen wird |
| Preisoptimiertes Laden Status | Klartext-Status mit dem *Grund* – siehe [Statusanzeige](#statusanzeige) |
| Preisoptimiertes Laden nächster Start | Zeitstempel des nächsten geplanten Ladefensters (bzw. Beginn des laufenden) |
| Aktueller Strompreis | Preis des aktuellen Zeitfensters in EUR/kWh |

### Einstellungen und Schalter

**Zahlenwerte:**

| Entität | Bereich | Beschreibung |
| --- | --- | --- |
| Max. SOC | 0–100 % | Ziel-Ladestand für die [Max-SOC-Sperre](#max-soc-sperre); gleichzeitig oberes Ziel der Netzladung. Ohne vorherige Einstellung 100 % (nicht 0) |
| Max. Netzladeleistung | 0–10 000 W (Schritt 50 W) | Ladeleistung für Netzladung und preisoptimiertes Laden. Beim allerersten Start mit dem Ladeleistungsgrenzwert des Geräts (Register 44) vorbelegt |
| Netzladung Min. SOC | 0–100 % | Untere Schwelle, ab der die Netzladung startet. Ohne vorherige Einstellung 100 % |
| Preisoptimiertes Laden Preisgrenze | −1,00 bis 2,00 EUR/kWh (Schritt 0,001) | Preis, bis zu dem in der Strategie "Absoluter Preis" geladen wird. Negative Preise sind zulässig. Standard 0,20 EUR/kWh |
| Preisoptimiertes Laden Anzahl Stunden | 1–24 h | Wie viele der günstigsten Stunden in den Strategien "Relativ" und "Smart" genutzt werden. Standard 3 |

Alle Werte bleiben über Neustarts hinweg erhalten.

**Schalter:**

| Entität | Beschreibung |
| --- | --- |
| Speicher On/Off | Schaltet den Speicher ein/aus |
| Netzladung aktiv | Hauptschalter der [Netzladung](#netzladung-zeitgesteuertes-laden) |
| Netzdienliches Laden aktiv | Hauptschalter des [netzdienlichen Ladens](#netzdienliches-laden) |
| Preisoptimiertes Laden aktiv | Hauptschalter des [preisoptimierten Ladens](#preisoptimiertes-laden) |
| Netzladung aktiv im Januar … Dezember | 12 Schalter: in welchen Monaten das Netzladungs-Zeitfenster gilt |
| Netzdienliches Laden aktiv im Januar … Dezember | 12 Schalter, analog für das netzdienliche Laden |

**Zeiten:** "Netzladung Start/Ende" und "Netzdienliches Laden Start/Ende"
(jeweils HH:MM).

**Auswahl:** "Preisoptimiertes Laden Strategie" mit den Optionen
"Manuell / Aus", "Absoluter Preis", "Relativ / Günstigste Stunden" und
"Smart / PV-optimiert".

**Warum gibt es nicht für jede Automatik eigene Werte?** "Max. SOC" und
"Max. Netzladeleistung" werden bewusst geteilt, damit es keine zwei
konkurrierenden Obergrenzen gibt - "Max. SOC" ist die einzige SOC-Einstellung
der Integration und damit auch das Ziel des preisoptimierten Ladens. Nur
dort, wo eine Automatik wirklich etwas Eigenes braucht, gibt es eine eigene
Einstellung: "Netzladung Min. SOC" (nur die Netzladung braucht eine
Startschwelle).

## Die drei Lade-Automatiken

| Automatik | Was sie tut | Wofür |
| --- | --- | --- |
| **[Netzladung](#netzladung-zeitgesteuertes-laden)** | Lädt im Zeitfenster **aktiv aus dem Netz** bis "Max. SOC" | Günstiger Nachtstromtarif, feste Zeiten |
| **[Netzdienliches Laden](#netzdienliches-laden)** | **Verhindert** im Zeitfenster, dass der Speicher PV-Überschuss einlädt | Laden in die Mittagsspitze verschieben, Einspeisespitzen glätten |
| **[Preisoptimiertes Laden](#preisoptimiertes-laden)** | Lädt aus dem Netz, **wenn der Strom günstig ist** | Dynamische Tarife (Tibber, Nordpool, aWATTar …) |

Wichtig zum Zusammenspiel:

- **Netzladung und preisoptimiertes Laden schließen sich aus** – beide laden
  aktiv aus dem Netz. Beim Einschalten des einen bei laufendem anderen kommt
  eine Rückfrage, siehe
  [Netzladung und preisoptimiertes Laden schließen sich aus](#netzladung-und-preisoptimiertes-laden-schließen-sich-aus).
- **Netzladung hat Vorrang vor preisoptimiertem Laden**, falls doch beides
  gleichzeitig zutrifft.
- **Netzladung und netzdienliches Laden dürfen sich zeitlich nicht
  überschneiden** – die Integration prüft das, siehe
  [Zeitfenster](#zeitfenster-dürfen-sich-nicht-überschneiden).
- Die **[Max-SOC-Sperre](#max-soc-sperre)** steht über allen dreien.

Alle drei Automatiken brauchen den SunSpec-Modus, weil sie über dessen Register
schreiben. Ist er nicht erreichbar, greift keine von ihnen.

### Der 50-W-Schwellwert

An mehreren Stellen wird gegen denselben Schwellwert von **50 W** geprüft
(`SMARTMETER_PV_SURPLUS_THRESHOLD_WATT` in `const.py`):

- PV-Überschuss am Smart Meter (Einspeisung > 50 W) → Netzladung und
  preisoptimiertes Laden brechen ab, die eigene Sonne ist günstiger.
- Netzbezug am Smart Meter (> 50 W) → die Max-SOC-Sperre wird freigegeben.
- Tatsächliche Ladeleistung des Speichers (≥ 50 W) → das netzdienliche Laden
  greift ein.

Damit kurze Lastspitzen oder Messausreißer nichts auslösen, zählt jede
Über- oder Unterschreitung erst, wenn sie **zwei Abfragezyklen in Folge**
(also etwa 4 Sekunden) besteht. Ein einzelner Wert auf der anderen Seite der
Schwelle setzt die Zählung sofort zurück.

## Max-SOC-Sperre

Die Sperre gilt **immer** – unabhängig davon, ob eine der Lade-Automatiken
eingeschaltet ist.

Sobald der Ladestand "Max. SOC" erreicht oder überschreitet, hält die
Integration den Speicher aktiv bei 0 % Leistungsvorgabe. Das verhindert
dauerhaftes Volladen auf 100 % und schont den Akku – auch dann, wenn der
Speicher gar nicht von der Integration, sondern durch PV-Überschuss über die
geräteeigene Nullregelung vollgeladen wurde.

**Achtung, das geht über eine reine Ladebegrenzung hinaus:** Solange die Sperre
aktiv ist, entlädt sich der Speicher auch nicht zur Deckung des Eigenverbrauchs.
0 % Leistungsvorgabe heißt: weder laden noch entladen.

Damit die Sperre nicht ewig bestehen bleibt – bei 0 % fällt der Ladestand ja von
selbst kaum –, gibt es drei Wege heraus:

1. **Ladestand fällt unter "Max. SOC"** (z. B. durch Selbstentladung): Der
   Speicher geht sofort zurück in die geräteeigene SmartMeter-Nullregelung.
2. **Netzbezug über 50 W** am Smart Meter, bestätigt über zwei Zyklen: Die
   Sperre wird aufgehoben, damit der Speicher den Hausverbrauch wieder deckt,
   statt ihn dauerhaft aus dem Netz beziehen zu lassen.
3. **Ende des Zeitfensters:** Wurde "Max. SOC" *innerhalb* eines Netzladungs-
   oder netzdienlich-Zeitfensters erreicht, bleibt die Sperre an dieses Fenster
   gebunden und wird spätestens an dessen Ende aufgehoben.

Danach übernimmt wieder die normale Automatik des Geräts (bzw. die Netzladung,
falls deren Bedingungen erfüllt sind).

> **Technischer Hintergrund:** "Max. SOC" ist kein Register des Geräts, sondern
> Software-Logik der Integration. Geschrieben wird über den SunSpec-Modus:
> Register 40051 (Steuermodus) auf Sollwertvorgabe, Register 40049
> (Leistungsvorgabe) auf 0 %. Zum Aufheben geht Register 40051 zurück auf 0
> (SmartMeter-Nullregelung).

## Netzladung (zeitgesteuertes Laden)

Lädt den Speicher innerhalb eines Zeitfensters aktiv aus dem Netz – unabhängig
von PV-Überschuss. Typischer Anwendungsfall: *"Lade auf 90 %, wenn es zwischen
1 und 5 Uhr ist und der Ladestand unter 40 % liegt."*

### Einstellungen

| Entität | Beschreibung |
| --- | --- |
| Netzladung aktiv | Ein-/Ausschalten |
| Netzladung Start / Ende | Zeitfenster (HH:MM) |
| Netzladung Min. SOC | Startschwelle: erst unterhalb dieses Ladestands wird geladen |
| Netzladung aktiv im Januar … Dezember | In welchen Monaten das Zeitfenster gilt |
| Max. SOC | Ziel, bis zu dem geladen wird (geteilte Einstellung) |
| Max. Netzladeleistung | Ladeleistung (geteilte Einstellung) |

Alle Werte bleiben über Neustarts hinweg erhalten; ein eingerichteter Zeitplan
muss also nicht nach jedem Neustart neu gesetzt werden.

### Wann geladen wird

Geladen wird nur, wenn **alle** Bedingungen zutreffen:

- "Netzladung aktiv" ist eingeschaltet,
- der aktuelle Monat ist ausgewählt,
- die Uhrzeit liegt im Zeitfenster,
- der Ladestand liegt unter "Netzladung Min. SOC" (siehe Hysterese unten),
- "Max. SOC" ist noch nicht erreicht,
- am Smart Meter liegt kein PV-Überschuss über 50 W an,
- "Max. Netzladeleistung" ist gesetzt.

**Zeitfenster über Mitternacht** sind erlaubt (z. B. 23:00–05:00). Sind Start
und Ende gleich – oder ist eines von beiden leer –, gilt das Fenster als leer
und es wird nie geladen. Ist kein einziger Monat ausgewählt, ist die Netzladung
ganzjährig inaktiv.

**Hysterese bei "Min. SOC":** Ist die Schwelle einmal unterschritten, lädt die
Netzladung durch bis "Max. SOC" – auch wenn der Ladestand zwischendurch wieder
über "Min. SOC" steigt. Erst "Max. SOC" beendet den Vorgang.

Der Standardwert von "Netzladung Min. SOC" ist 100 %. Da der Ladestand
praktisch immer darunter liegt, blockiert die Schwelle zunächst nichts – die
Netzladung verhält sich also wie ohne diese Einstellung, bis bewusst ein
niedrigerer Wert gesetzt wird.

### Wann abgebrochen wird

- **"Max. SOC" erreicht** → zusätzlich greift die
  [Max-SOC-Sperre](#max-soc-sperre).
- **PV-Überschuss über 50 W** am Smart Meter (bestätigt über zwei Zyklen) →
  Abbruch mitten im Zeitfenster, nicht erst an dessen Ende. Der Speicher lädt
  dann ohnehin über die geräteeigene Nullregelung mit der eigenen Sonne.
  Ist der Messwert gerade nicht verfügbar (z. B. SunSpec-Modus nicht
  erreichbar), blockiert das die Netzladung nicht.
- **Ende des Zeitfensters.**

> **Technischer Hintergrund:** Geschrieben wird über den SunSpec-Modus
> ("Immediate Controls"): Register 40051 auf Sollwertvorgabe, dann Register
> 40049 mit der aus "Max. Netzladeleistung" errechneten Leistung in Prozent der
> Referenz-Maximalleistung. Beide Register werden periodisch neu geschrieben
> (abgeleitet aus dem geräteseitig gemeldeten Timeout, Register 40050), weil das
> Gerät einen alten Sollwert sonst verwirft.
>
> Der manuelle Service `start_grid_charge`/`stop_grid_charge` benutzt einen
> **anderen** Weg (Basic-Mode-Register 41, absoluter Watt-Sollwert) und läuft
> unabhängig von dieser Automatik.

## Netzdienliches Laden

Diese Automatik **lädt nicht selbst** – sie hindert den Speicher innerhalb eines
eigenen Zeitfensters gezielt **am Laden**. Gedacht für Zeiträume, in denen der
Speicher den PV-Überschuss noch nicht einsammeln soll, damit das Laden in die
Zeit mit dem höchsten PV-Ertrag rutscht (Mittagsspitze) und die Einspeisespitze
geglättet wird.

Ablauf im Zeitfenster:

1. Der Speicher beginnt über die geräteeigene Nullregelung von selbst zu laden.
   Erreicht seine **tatsächliche Ladeleistung mindestens 50 W** (über zwei
   Zyklen bestätigt), übernimmt die Integration: Sie schaltet in den
   Sollwertvorgabemodus und stoppt die Ladung auf 0 %.
2. Solange die **Netzeinspeisung** am Smart Meter danach mindestens 50 W
   beträgt, bleibt die Ladung bewusst bei 0 % – genau das ist der Zweck.
3. Fällt die Netzeinspeisung unter 50 W (ebenfalls über zwei Zyklen bestätigt),
   geht der Speicher zurück in die SmartMeter-Nullregelung und darf wieder von
   selbst laden. Steigt seine Ladeleistung erneut über 50 W, beginnt der Ablauf
   von vorn.

Ist die Ladeleistung des Speichers noch unbekannt, kann Schritt 1 nicht
auslösen. Ist die Netzeinspeisung nach dem Eingriff unbekannt, bleibt die Ladung
sicherheitshalber gestoppt (anders als bei der Netzladung, die bei fehlendem
Messwert weiterläuft).

### Einstellungen

| Entität | Beschreibung |
| --- | --- |
| Netzdienliches Laden aktiv | Ein-/Ausschalten |
| Netzdienliches Laden Start / Ende | Zeitfenster (HH:MM) |
| Netzdienliches Laden aktiv im Januar … Dezember | In welchen Monaten das Zeitfenster gilt – z. B. nur Mai bis August, 11–14 Uhr |
| Max. SOC | Ziel für die Max-SOC-Sperre (geteilte Einstellung) |

"Max. Netzladeleistung" wird hier **nicht** gebraucht, weil netzdienliches Laden
nie einen Sollwert größer 0 schreibt.

Es gibt keinen Vorbelegungsschritt bei der Ersteinrichtung – die Automatik ist
ab Werk aus und wird ausschließlich über diese Entitäten konfiguriert. Alle
Werte bleiben über Neustarts hinweg erhalten.

## Preisoptimiertes Laden

Lädt den Speicher dann aus dem Netz, wenn der Strom günstig ist, und lässt ihn
in teuren Phasen den Hausverbrauch decken – vergleichbar mit dem, was EVCC oder
cleverPV für dynamische Tarife machen.

Die Integration ruft **keine Strompreise selbst ab**. Sie wertet einen Sensor
aus, den es in deinem Home Assistant bereits gibt: Tibber, Nordpool, EPEX Spot,
ENTSO-e, aWATTar oder ein eigener Template-Sensor.

Erkannt werden die üblichen Vorschau-Attribute (`raw_today`/`raw_tomorrow`,
`today`/`tomorrow`, `data`, `forecast`, `prices`) – sowohl als Liste von
Zeitfenstern als auch als reine Zahlenliste für einen Kalendertag, stündlich wie
viertelstündlich. Preise in ct/kWh werden anhand der Einheit des Sensors
automatisch in EUR/kWh umgerechnet.

### Einrichtung

**Einstellungen → Geräte & Dienste → SAX Power Home → Konfigurieren**

| Feld | Beschreibung |
| --- | --- |
| Strompreis-Sensor | Sensor mit dem aktuellen Arbeitspreis. Aus seinen Vorschau-Attributen entstehen die Ladefenster der Strategien "Relativ" und "Smart" |
| Attribut mit der Preisvorschau | Optional. Nur nötig, wenn die automatische Erkennung bei deinem Sensor danebenliegt – dann den Attributnamen eintragen (z. B. `raw_today`) |
| Preis-Einheit | "Automatisch" leitet sie aus dem Sensor ab. EUR/kWh bzw. ct/kWh erzwingen die Interpretation, falls der Sensor keine oder eine irreführende Einheit meldet |
| Vorgabe-Strategie | Gilt nur beim allerersten Start. Danach zählt das Auswahlfeld "Preisoptimiertes Laden Strategie" |
| PV-Prognose-Sensor | Optional, nur für "Smart". Erwartet die erwartete Erzeugung als Energie, z. B. `sensor.energy_production_tomorrow` (Forecast.Solar) oder das Solcast-Pendant |
| Nutzbarer Anteil der PV-Prognose | Wie viel der Prognose tatsächlich im Speicher landen dürfte (Standard 80 %) – deckt Eigenverbrauch, Wetterunsicherheit und Wandlungsverluste ab |

Alles Weitere läuft über Entitäten am Gerät und ist damit automatisierbar und in
Dashboards nutzbar. Der Hauptschalter **"Preisoptimiertes Laden aktiv"** schaltet
die Automatik ein; ab Werk ist sie aus.

### Strategien

| Strategie | Verhalten |
| --- | --- |
| **Manuell / Aus** | Automatik stillgelegt, ohne die übrigen Einstellungen zu verlieren |
| **Absoluter Preis** | Lädt, solange der Preis die "Preisgrenze" nicht überschreitet – *"lade, wenn Strom unter 15 ct/kWh kostet"* |
| **Relativ / Günstigste Stunden** | Lädt in den X günstigsten Stunden – *"lade in den 3 billigsten Stunden"*. Die Auswahl erfolgt vorausschauend über die bekannten Preise |
| **Smart / PV-optimiert** | Wie "Relativ", ermittelt die Stundenzahl aber aus dem tatsächlichen Bedarf abzüglich PV-Prognose |

Der Planungshorizont ist ein gleitendes **24-Stunden-Fenster** über die bekannten
Preise (Rest von heute plus – sobald veröffentlicht – morgen), nicht der
Kalendertag. "Die 3 günstigsten Stunden" heißt also: die drei günstigsten der
nächsten 24 Stunden.

**So rechnet "Smart":**

1. Fehlende Energie = ("Max. SOC" − aktueller Ladestand) × Speicherkapazität
2. minus nutzbarer Anteil der PV-Prognose
3. Rest geteilt durch "Max. Netzladeleistung" = benötigte Ladestunden
4. Genau so viele der günstigsten Stunden werden eingeplant

Deckt die Prognose den Bedarf vollständig, wird gar kein Netzstrom eingekauft
(Status "PV-Prognose deckt Bedarf"). "Anzahl Stunden" bleibt dabei die
**Obergrenze** – es wird nie mehr eingekauft, als du zugelassen hast. Sind
Kapazität, Ladestand oder Ladeleistung gerade unbekannt (z. B. SunSpec-Modus
nicht erreichbar), verhält sich "Smart" wie "Relativ".

> **Beispiel:** "Max. SOC" 80 %, aktuell 40 %, 10 kWh Speicher → 4 kWh fehlen.
> Die Prognose meldet für morgen 8 kWh, davon gelten 80 % als nutzbar → 6,4 kWh.
> Der Bedarf ist gedeckt, es wird nachts nichts zugekauft.

### Leistung, Ziel-SOC und Abbruchgründe

Geladen wird mit **"Max. Netzladeleistung"** – derselben Einstellung wie bei der
Netzladung, damit es keine zwei konkurrierenden Leistungswerte gibt.

Der **Ziel-SOC ist derselbe Wert wie "Max. SOC"** – keine eigene Einstellung.
Ist er erreicht, endet die Netzladung UND zusätzlich greift die
[Max-SOC-Sperre](#max-soc-sperre), der Speicher wird bei 0 % gehalten – genau
wie bei der Netzladung.

Weitere Abbruchgründe, jeweils sofort wirksam (nicht erst im nächsten
60-Sekunden-Takt):

- **PV-Überschuss** über 50 W am Smart Meter – die eigene Sonne ist immer
  günstiger als Netzstrom.
- **Netzladung aktiv** – das zeitgesteuerte Laden hat Vorrang.
- **"Max. Netzladeleistung" steht auf 0** – ohne Leistung gibt es keinen
  Sollwert zu schreiben.

Der Ladeplan wird **alle 60 Sekunden** neu berechnet, zusätzlich sofort bei jeder
Einstellungsänderung und bei jedem Zustandswechsel des Preis- oder
Prognose-Sensors. Die oben genannten Abbruchgründe werden dagegen bei **jedem**
Abfragezyklus geprüft, greifen also ohne Verzögerung.

> **Technischer Hintergrund:** Geladen wird über denselben SunSpec-Schreibpfad
> wie bei der Netzladung (Register 40051 auf Sollwertvorgabe, Register 40049 auf
> die gewünschte Ladeleistung). Ist die Bedingung nicht erfüllt, geht der
> Speicher in die SmartMeter-Nullregelung zurück.

### Statusanzeige

Der Sensor **"Preisoptimiertes Laden Status"** nennt in Klartext den Grund für
das aktuelle Verhalten:

| Status | Bedeutung |
| --- | --- |
| Aus | Hauptschalter aus oder Strategie "Manuell / Aus" |
| Keine Preisdaten | Kein Sensor konfiguriert, oder seine Attribute lassen sich nicht auswerten |
| Warten auf Preisabfall | Alles bereit, aber der aktuelle Zeitraum gehört nicht zu den ausgewählten Fenstern |
| Lade aus Netz | Die Zwangsladung läuft |
| PV-Prognose deckt Bedarf | Strategie "Smart": morgen kommt genug Sonne, es wird nichts zugekauft |
| Pausiert (PV-Überschuss) | Am Smart Meter wird Einspeisung gemessen |
| Pausiert (Max. SOC) | Die übergeordnete Max-SOC-Sperre greift |
| Pausiert (Max. Netzladeleistung fehlt) | "Max. Netzladeleistung" steht auf 0 |
| Pausiert (Netzladung aktiv) | Das zeitgesteuerte Laden hat gerade Vorrang |

Die Attribute dieses Sensors zeigen zusätzlich Strategie, aktuellen Preis,
wirksame Preisgrenze, benötigte Stunden, eingerechnete PV-Prognose, die
konfigurierten Quell-Sensoren und alle geplanten Zeitfenster – hilfreich, wenn
eine Entscheidung einmal nicht nachvollziehbar erscheint.

### Netzladung und preisoptimiertes Laden schließen sich aus

Netzladung und preisoptimiertes Laden benutzen denselben Schreibpfad und dürfen
deshalb nicht gleichzeitig laufen. Schaltest du eines ein, während das andere
aktiv ist, passiert **zunächst nichts**: Der Schalter springt zurück, und du
bekommst eine Rückfrage – als Benachrichtigung und als Eintrag unter
**Einstellungen → Geräte & Dienste → Reparaturen**.

- **Bestätigen** – das jeweils andere Feature wird abgeschaltet, das gewünschte
  aktiviert.
- **Abbrechen** – es ändert sich nichts.

Das gilt in beide Richtungen.

Für **Automationen**, die keinen Dialog beantworten können, gibt es den Service
`sax_power.set_price_charge_enabled` mit dem Feld `force` – damit wird die
Netzladung ohne Rückfrage abgeschaltet.

## Zeitfenster dürfen sich nicht überschneiden

Das Zeitfenster des netzdienlichen Ladens darf sich nicht mit dem der Netzladung
überlappen. Dabei zählen **Tageszeit UND aktive Monate zusammen**: Laufen beide
Fenster in verschiedenen Monaten (z. B. Netzladung nur November–Januar,
netzdienliches Laden nur Mai–August), dürfen sich die Uhrzeiten beliebig
überlappen – sie sind ja nie gleichzeitig aktiv.

Was passiert bei einer echten Überschneidung (gleiche Tageszeit **und**
gemeinsamer Monat)?

| Geänderte Einstellung | Reaktion |
| --- | --- |
| **Monats-Schalter** | Die Änderung wird abgelehnt und im Frontend als Fehler angezeigt. Die bisherige Auswahl bleibt bestehen |
| **Start- oder Endzeit** | Die Änderung wird angenommen, aber die gerade geänderte Zeit wird **geleert** – dazu kommt eine Benachrichtigung mit beiden betroffenen Zeitfenstern |

Eine leere Start- oder Endzeit bedeutet immer: Das Feature läuft nicht. Ein
geleertes Feld muss also bewusst neu gesetzt werden.

**Warum wird geleert statt zurückgesetzt?** Start und Ende sind zwei getrennte
Entitäten. Verschiebt man ein Fenster in zwei Schritten (erst Start, dann Ende),
prüft Home Assistant jeden Schritt einzeln gegen den noch alten Wert der anderen
Grenze. Ein rein dadurch entstehender Zwischenzustand könnte sonst fälschlich als
Überschneidung gelten und die Änderung dauerhaft mit dem alten Wert blockieren.

**Praxistipps:**

- Ein ganzes Zeitfenster in einem Rutsch verschieben: die Services
  `sax_power.set_timed_charge_window` bzw. `sax_power.set_grid_serving_window`
  benutzen – sie setzen Start und Ende **atomar** und prüfen nur das tatsächliche
  Ziel-Fenster.
- Beim Umstellen auf verschiedene Monate bei bereits überlappenden Zeiten: erst
  die Monate beider Features anpassen, dann die Zeiten (oder umgekehrt) – nicht
  beides gleichzeitig schrittweise verschieben.

## Services (für Automationen)

Alle Services werden über `device_id` an das jeweilige SAX-Gerät adressiert –
relevant, wenn mehrere Speicher eingerichtet sind.

**`sax_power.start_grid_charge`** – startet eine Netzladung mit festem
Leistungssollwert und wiederholt den Schreibvorgang periodisch im Hintergrund,
solange sie aktiv ist. Läuft unabhängig von der Netzladungs-Automatik.

| Feld | Beschreibung |
| --- | --- |
| `device_id` | SAX Power Gerät |
| `power` | Sollwert in Watt (−32768 bis 32767) |

**`sax_power.stop_grid_charge`** – beendet diese manuelle Netzladung.

| Feld | Beschreibung |
| --- | --- |
| `device_id` | SAX Power Gerät |

**`sax_power.set_timed_charge_window`** – setzt Start- und Endzeit der
Netzladung atomar in einem Aufruf (siehe
[Zeitfenster](#zeitfenster-dürfen-sich-nicht-überschneiden)).

| Feld | Beschreibung |
| --- | --- |
| `device_id` | SAX Power Gerät |
| `start` | Startzeit |
| `end` | Endzeit |

**`sax_power.set_grid_serving_window`** – dasselbe für das netzdienliche Laden.

| Feld | Beschreibung |
| --- | --- |
| `device_id` | SAX Power Gerät |
| `start` | Startzeit |
| `end` | Endzeit |

**`sax_power.refresh_price_plan`** – berechnet den Ladeplan des preisoptimierten
Ladens sofort neu und wendet ihn an, statt auf die nächste reguläre Prüfung
(alle 60 s) zu warten.

| Feld | Beschreibung |
| --- | --- |
| `device_id` | SAX Power Gerät |

**`sax_power.set_price_charge_enabled`** – schaltet das preisoptimierte Laden
ein oder aus. Nicht-interaktiver Gegenpart zum Schalter: Steht die Netzladung im
Weg, schlägt der Aufruf mit einem Fehler fehl – mit `force: true` wird sie
stattdessen ohne Rückfrage abgeschaltet.

| Feld | Beschreibung |
| --- | --- |
| `device_id` | SAX Power Gerät |
| `enabled` | Ein- (`true`) oder ausschalten (`false`) |
| `force` | Optional, Standard `false`. Schaltet eine aktive Netzladung ohne Rückfrage ab |

**`sax_power.create_dashboard`** – legt das mitgelieferte Dashboard "SAX Power"
nachträglich an (siehe [Schritt 3](#schritt-3-dashboard-anlegen-optional)) –
z. B. wenn es bei der Ersteinrichtung abgewählt oder später gelöscht wurde.
Existiert es bereits, passiert nichts.

| Feld | Beschreibung |
| --- | --- |
| `device_id` | SAX Power Gerät |

## Verbindungsdaten nachträglich ändern

IP-Adresse, Port, Slave-IDs und Aktualisierungsintervall lassen sich jederzeit
ändern, z. B. wenn der Speicher eine neue IP bekommen hat:

**Einstellungen → Geräte & Dienste → SAX Power Home → ⋮ (Gerät) →
Neu konfigurieren**

Das Formular ist mit den gespeicherten Werten vorbelegt. Die neue Verbindung
wird vor dem Speichern geprüft; bei Erfolg lädt die Integration automatisch mit
den neuen Daten neu.

## Diagnose und Fehlersuche

**Diagnose-Export:** **Einstellungen → Geräte & Dienste → SAX Power Home →
⋮ (Gerät) → Diagnose herunterladen**

Die Datei enthält den kompletten internen Zustand (alle Messwerte, Max-SOC-
Sperre, Zustand der drei Lade-Automatiken, ausgewerteter Ladeplan,
Erreichbarkeit des SunSpec-Modus). Die IP-Adresse wird automatisch unkenntlich
gemacht – die Datei kann also gefahrlos geteilt werden.

| Symptom | Wahrscheinliche Ursache | Was tun |
| --- | --- | --- |
| Verbindung schlägt bei der Einrichtung fehl | IP/Port falsch oder Speicher nicht erreichbar | IP im Router prüfen, Erreichbarkeit testen |
| Verbindung steht, aber Modbus-Fehler | Falsche Slave-ID | Slave-ID (Basic Mode) prüfen, Standard 64 |
| Viele Sensoren zeigen "unbekannt" | SunSpec-Modus nicht erreichbar | Slave-ID (SunSpec, Standard 100) und Firmware prüfen (Master V61/Gateway V54 oder neuer). Wird zusätzlich als Reparatur-Hinweis angezeigt |
| Lade-Automatiken tun nichts | SunSpec-Modus nicht erreichbar – alle drei brauchen ihn zum Schreiben | wie oben |
| Netzladung startet nicht | "Netzladung Min. SOC" zu niedrig, Monat nicht ausgewählt, Zeitfenster leer, oder PV-Überschuss über 50 W | Einstellungen prüfen, Sensor "Zeitgesteuertes Laden aktiv" beobachten |
| Preisoptimiertes Laden meldet "Keine Preisdaten" | Der Sensor liefert keine auswertbare Vorschau | Attributnamen im Options-Dialog fest vorgeben; Diagnose-Export zeigt den ausgewerteten Plan |
| Speicher lädt und entlädt gar nicht mehr | Die [Max-SOC-Sperre](#max-soc-sperre) hält ihn bei 0 % | "Max. SOC" höher setzen oder Netzbezug abwarten |
| Zeit lässt sich nicht setzen / wurde geleert | Überschneidung der Zeitfenster | Siehe [Zeitfenster](#zeitfenster-dürfen-sich-nicht-überschneiden) |
| "Ladestatus Akku" (oder andere Klartext-Sensoren) erzeugt viele Einträge im Protokoll/in der Aktivität | Der Wert wird alle 2 s abgefragt und kann entsprechend oft wechseln; Home Assistant blendet nur Sensoren mit Einheit/state_class automatisch aus dem Logbuch aus – für reine Klartext-Sensoren geht das nicht, ohne sie kaputt zu machen | Entity-ID in Entwicklertools → Zustände nachschlagen und gezielt ausschließen: `logbook:` → `exclude:` → `entities:` in der `configuration.yaml` (siehe [Logbuch-Dokumentation](https://www.home-assistant.io/integrations/logbook/#exclude)) |

## Bekannte Einschränkungen

- **Vorzeichenkonvention von Register 40029** (Wirkleistung Speicher Summe) ist
  herstellerseitig nicht dokumentiert. Die Integration nimmt an:
  positiv = Entladung/Einspeisung.
- **Vorzeichenkonvention von Register 40049** (Leistungsvorgabe) ist ebenfalls
  nicht dokumentiert. In Analogie zu 40029 gilt: negativ = Laden. Die
  Integration schreibt hier bewusst nur negative Sollwerte.
- **Keine ferngesteuerte manuelle Entladung.** Positive Sollwerte auf Register
  40049 bzw. Register 41 wurden gegen echte Hardware getestet und zeigten keine
  Wirkung; der Hersteller hat bestätigt, dass das nicht vorgesehen ist.
- **"Max. SOC" ist kein Geräteregister**, sondern Software-Logik – siehe
  [Max-SOC-Sperre](#max-soc-sperre). Solange sie greift, entlädt sich der
  Speicher auch nicht zur Eigenverbrauchsdeckung.
- **Der Service `start_grid_charge`** schreibt einen absoluten Watt-Sollwert auf
  Basic-Mode-Register 41. Ob dieses Register auf einem konkreten Gerät
  freigeschaltet ist, hängt von Gerät und Firmware ab und sollte vor dem
  produktiven Einsatz geprüft werden.
- **SunSpec-Modus ist optional**, aber für alles Schreibende nötig. Ist er nicht
  erreichbar (z. B. zu alte Firmware – Master V61/Gateway V54 oder neuer
  erforderlich), bleiben die Basic-Mode-Sensoren verfügbar; die SunSpec-Sensoren
  zeigen "unbekannt", und die drei Lade-Automatiken sowie die Max-SOC-Sperre
  können nicht greifen. Ein dauerhafter Ausfall wird als Reparatur-Hinweis
  angezeigt.
- **Preisoptimiertes Laden hängt an der Datenqualität des Preis-Sensors.**
  Liefert er nur den aktuellen Preis ohne Vorschau, funktioniert "Absoluter
  Preis" weiterhin; "Relativ" und "Smart" können mangels Zukunftsdaten keine
  Fenster planen (Status "Keine Preisdaten").
- **Die Strategie "Smart" braucht die Speicherkapazität** (SunSpec-Register
  40097) und einen PV-Prognose-Sensor. Fehlt eines davon, verhält sie sich wie
  "Relativ".

## Weiterführende Dokumentation

- [DEVELOPMENT.md](DEVELOPMENT.md) – Interna: Datenfluss, Register-Mapping,
  Tests, lokale Entwicklung (DevContainer).
- [anforderung.yaml](anforderung.yaml) – die vollständigen, aktuell gültigen
  Anforderungen an die Integration.
- [AGENTS.md](AGENTS.md) – für KI-Coding-Agenten: Setup-, Test- und
  Lint-Befehle, Code-Stil, Git-Workflow.
