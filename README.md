# SAX Power Home – Home Assistant Integration

Custom Component für die Anbindung eines **SAX Power Home (Plus)** Heimspeichers
an Home Assistant über die Modbus-TCP-Schnittstelle.

## Inhaltsverzeichnis

- [Über diese Integration](#über-diese-integration)
- [Installation](#installation)
  - [Installation über HACS (empfohlen)](#installation-über-hacs-empfohlen)
  - [Manuelle Installation](#manuelle-installation)
- [Einrichtung](#einrichtung)
- [Funktionen](#funktionen)
  - [Sensoren](#sensoren)
  - [Zahlenfelder](#zahlenfelder)
  - [Schalter](#schalter)
  - [Schaltflächen](#schaltflächen)
  - [Zeitgesteuertes Laden](#zeitgesteuertes-laden)
  - [Services](#services)
- [IP-Adresse nachträglich ändern](#ip-adresse-nachträglich-ändern)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)
- [Weiterführende Dokumentation](#weiterführende-dokumentation)

## Über diese Integration

Die Integration verbindet sich per Modbus TCP mit dem SAX Power Home (Plus)
und stellt dessen Messwerte sowie Steuermöglichkeiten (Lade-/Entladelimits,
Ein/Aus, zeitgesteuertes Laden) als Home-Assistant-Entitäten bereit. Die
Einrichtung erfolgt vollständig über die grafische Oberfläche, es ist keine
YAML-Konfiguration nötig.

## Installation

### Installation über HACS (empfohlen)

1. In Home Assistant: **HACS → Integrationen → ⋮ (oben rechts) → Benutzerdefinierte Repositories**
2. Repository-URL eintragen: `https://github.com/dr-dimitri/sax-ha`
   Kategorie: **Integration**
3. Auf **Hinzufügen** klicken, danach die Integration "SAX Power Home" in HACS suchen und installieren
4. Home Assistant neu starten
5. Weiter mit [Einrichtung](#einrichtung)

### Manuelle Installation

1. Ordner `custom_components/sax_power` in das `custom_components`-Verzeichnis
   deiner Home Assistant Konfiguration kopieren
2. Home Assistant neu starten
3. Weiter mit [Einrichtung](#einrichtung)

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → nach "SAX Power" suchen
2. Folgende Daten eingeben:

   | Feld | Beschreibung | Standardwert |
   | --- | --- | --- |
   | IP-Adresse | IP des SAX Speichers im lokalen Netz | – |
   | Port | Modbus-TCP-Port | 502 |
   | Slave-ID (Basic Mode) | Slave-ID für Grundfunktionen (SOC, Schalter, Leistungslimits) | 64 |
   | Slave-ID (SunSpec-Modus) | Slave-ID für erweiterte Mess- und Diagnosewerte | 100 |
   | Aktualisierungsintervall | Abfrageintervall in Sekunden | 10 |

3. Die Verbindung wird vor dem Abschluss geprüft. Bei Verbindungsfehlern
   IP-Adresse, Port und Netzwerkerreichbarkeit prüfen.

## Funktionen

### Sensoren

Die Sensoren stammen aus zwei Registerkarten mit unterschiedlicher Slave-ID:

**Basic Mode (Slave-ID 64):**

| Entität | Beschreibung |
| --- | --- |
| Ladezustand | SOC des Speichers in % |
| Speicher Schaltzustand (Text) | "Aus" / "Ein" / "Verbunden" als Klartext (Diagnose) |
| Sollwert Leistung P | Aktuell gesetzter P-Sollwert in W (Diagnose) |
| Sollwert cos(phi) | Aktuell gesetzter cos(phi)-Sollwert (Diagnose) |

**SunSpec-Modus (Slave-ID 100):**

| Entität | Beschreibung |
| --- | --- |
| Hersteller / Gerätemodell / Softwareversion Master/Gateway / Seriennummer | Geräteidentität (Diagnose) |
| **Entladeleistung / Ladeleistung** | Aktuelle Lade-/Entladeleistung des Speichers |
| Speicher Stromsumme / -Strom A/B/C | in A |
| Speicher Spannung A/B/C | in V |
| Wirkleistung/Scheinleistung/Blindleistung Speicher Summe | in W / VA / var (Diagnose) |
| Leistungsfaktor Speicher Summe | dimensionslos |
| Netzfrequenz (Speicher) | in Hz |
| Maximale Zelltemperatur | in °C |
| Speicher Zustand / Speicher Ereignis | Klartext (Diagnose) |
| PV-Leistung | in W – nur mit Smartmeter ADW200 verfügbar (siehe Hinweis unten) |
| Leistungsvorgabe / Timeout / Steuermodus / Referenzwert Maximalleistung | Nur-Lese-Diagnosewerte |
| Netz Stromsumme / -Strom L1/L2/L3 | in A |
| Netzspannung Durchschnitt (L-N) / L1/L2/L3 | in V |
| Netzfrequenz | in Hz |
| **Smart Meter Leistung** | Aktuelle Netzleistung (Bezug/Einspeisung) |
| Netzleistung L1/L2/L3 | in W |
| Scheinleistung/Blindleistung/Leistungsfaktor Netz Summe | in VA / var / dimensionslos |
| Speicherkapazität / Verfügbare Lade-/Entladeleistung | in Wh / W (Diagnose) |
| Maximaler/Minimaler SoC / Akku SoC (SunSpec) / Entladetiefe | in % (Diagnose) |
| Ladestatus Akku / Akku Ereignis | Klartext (Diagnose) |
| Durchschnittliche Zellspannung | in mV (Diagnose) |

**Hinweis Einheit "var":** Blindleistung (reaktive Leistung) wird korrekt in
**var** (Volt-Ampere reaktiv) angegeben, nicht in Watt – analog zu
Scheinleistung in VA. Das ist dieselbe Konvention wie bei jedem anderen
Energiemessgerät.

**Hinweis Smartmeter-Modell:** PV-Leistung und einzelne Werte des
Meter-Modells sind laut Hersteller-Dokumentation nur mit dem Smartmeter
ADW200 vollständig verfügbar. Mit anderen Smartmetern (z. B. ADL400) sind
die Netz-Register (Ströme, Spannungen, Leistungen) in der Regel dennoch
plausibel befüllt; PV-Leistung kann dann dauerhaft 0 bleiben.

Ist der SunSpec-Modus nicht erreichbar (siehe
[Bekannte Einschränkungen](#bekannte-einschränkungen)), zeigen alle Sensoren
aus dieser Tabelle "unbekannt"; die Basic-Mode-Sensoren bleiben davon
unberührt.

### Zahlenfelder

| Entität | Beschreibung |
| --- | --- |
| Maximaler Lade-SOC | Ziel-SOC (0–100 %), ab dem die Ladung gestoppt wird – zentrale Einstellung, auch als Ziel-SOC für zeitgesteuertes Laden |
| Ladeleistungsgrenzwert | Direkt schreibbares Leistungslimit für die Ladung (W) – zentrale Einstellung, auch für zeitgesteuertes Laden |
| Entladeleistungsgrenzwert | Direkt schreibbares Leistungslimit für die Entladung (W) – zentrale Einstellung, auch für "Entladung starten" |

Es gibt bewusst keine eigenen Ziel-SOC-/Leistungseinstellungen für
zeitgesteuertes Laden oder den "Entladung starten"-Button: Beide nutzen die
zentralen Einstellungen oben. Ist "Maximaler Lade-SOC" nicht gesetzt, gilt
für zeitgesteuertes Laden ersatzweise 100 % als Ziel.

### Schalter

| Entität | Beschreibung |
| --- | --- |
| Speicher | Schaltet den Speicher ein/aus |
| Zeitgesteuertes Laden | Aktiviert/deaktiviert das zeitgesteuerte Laden, siehe [unten](#zeitgesteuertes-laden) |

### Schaltflächen

| Entität | Beschreibung |
| --- | --- |
| Entladung starten | Startet die Entladung mit dem zentralen Entladeleistungsgrenzwert als Sollwert; erneutes Drücken stoppt sie wieder |

Erster Druck startet die Entladung in Höhe des aktuell gesetzten
Entladeleistungsgrenzwerts, ein zweiter Druck stoppt sie wieder. Ist der
Entladeleistungsgrenzwert 0 W, meldet der Button einen Fehler statt einen
wirkungslosen Sollwert von 0 zu schreiben. Da die Schaltfläche technisch
zustandslos ist, zeigt sie selbst keinen Ein-/Aus-Zustand an – der aktuelle
Zustand lässt sich am Sensor "Sollwert Leistung P" ablesen.

### Zeitgesteuertes Laden

Lädt den Speicher innerhalb eines konfigurierbaren Zeitfensters aktiv auf
einen Ziel-SOC – unabhängig von PV-Überschuss, z. B. für günstige
Nachtstromtarife ("Lade auf 90 %, wenn es zwischen 1 und 5 Uhr ist").

**Entitäten** (unter "Steuerung" am Gerät):

| Entität | Beschreibung |
| --- | --- |
| Zeitgesteuertes Laden | Ein-/Ausschalten des Features |
| Beginn Zeitfenster | Startzeit (HH:MM) |
| Ende Zeitfenster | Endzeit (HH:MM) |
| Zeitgesteuertes Laden aktiv | Diagnose-Sensor, zeigt ob gerade aktiv nachgeladen wird |

Genutzt wird der bereits vorhandene "Maximaler Lade-SOC" als Ziel (siehe
[Zahlenfelder](#zahlenfelder)) sowie der zentrale Ladeleistungsgrenzwert als
Ladeleistung – es gibt keine eigenen Einstellungen dafür.

Das Zeitfenster darf über Mitternacht laufen (z. B. Start 23:00, Ende
05:00). Ist Start = Ende (oder eines von beiden nicht gesetzt), gilt das
Fenster als leer – es wird dann nie geladen.

Aktiviert-Zustand sowie Start-/Endzeit bleiben über Neustarts hinweg
erhalten, ein einmal eingerichteter Zeitplan muss also nicht nach jedem
Home-Assistant-Neustart neu gesetzt werden.

**Wichtig:** Zeitgesteuertes Laden, der "Entladung starten"-Button und der
manuelle `start_grid_charge`/`stop_grid_charge`-Service teilen sich denselben
Hintergrund-Mechanismus. Werden mehrere davon gleichzeitig verwendet, gewinnt
der zuletzt schreibende Aufruf – es gibt keine eigene Priorisierung
zwischen ihnen.

### Services

- **`sax_power.start_grid_charge`** – startet die Netzladung mit einem
  festen Leistungssollwert und wiederholt den Schreibvorgang periodisch im
  Hintergrund, solange der Service aktiv ist.

  | Feld | Beschreibung |
  | --- | --- |
  | `device_id` | SAX Power Gerät |
  | `power` | Sollwert in Watt (-32768 bis 32767) |

- **`sax_power.stop_grid_charge`** – beendet die Netzladung wieder.

  | Feld | Beschreibung |
  | --- | --- |
  | `device_id` | SAX Power Gerät |

Beide Services werden über einen `device_id`-Parameter an das jeweilige SAX
Power Gerät adressiert (relevant, falls mehrere Speicher eingerichtet sind).

## IP-Adresse nachträglich ändern

Die Verbindungsdaten (IP-Adresse, Port, Slave-IDs, Aktualisierungsintervall)
lassen sich jederzeit über die Oberfläche ändern, z. B. wenn sich die IP des
SAX Speichers ändert:

**Einstellungen → Geräte & Dienste → SAX Power Home → ⋮ (Gerät) → Neu konfigurieren**

Das Formular ist mit den aktuell gespeicherten Werten vorbelegt. Die neue
Verbindung wird vor dem Speichern geprüft; bei Erfolg werden die Werte
gespeichert und die Integration lädt automatisch mit den neuen Daten neu.

## Bekannte Einschränkungen

- **Vorzeichenkonvention** von Register 40029 (Wirkleistung Speicher Summe)
  ist herstellerseitig nicht dokumentiert. Die Integration geht davon aus:
  positiv = Entladung/Einspeisung.
- **Maximaler Lade-SOC** ist kein natives Geräteregister, sondern eine
  Software-Logik: Beim Erreichen des Zielwerts wird das Ladelimit-Register
  auf 0 gesetzt und beim Unterschreiten wieder freigegeben.
- **Netzladung, zeitgesteuertes Laden und "Entladung starten"** schreiben
  einen absoluten Watt-Sollwert auf Basic-Mode-Register 41. Ob dieses
  Register auf einem gegebenen Gerät aktiv nutzbar ("freigeschaltet") ist,
  ist geräte-/firmwareabhängig und sollte vor dem produktiven Einsatz am
  eigenen Gerät geprüft werden.
- **SunSpec-Modus ist optional**: Ist er nicht erreichbar (z. B. zu alte
  Firmware – Master V61/Gateway V54 oder neuer erforderlich), bleiben die
  Basic-Mode-Sensoren (SOC, Schalter, Leistungsgrenzwerte) trotzdem
  verfügbar; nur die SunSpec-Sensoren zeigen "unbekannt", bis der Block
  wieder lesbar ist. Ein dauerhafter Ausfall wird zusätzlich als
  Home-Assistant-Repair-Issue angezeigt.

## Weiterführende Dokumentation

Interna wie Datenfluss, Register-Mapping, Testausführung und lokale
Entwicklung (DevContainer) sind in [DEVELOPMENT.md](DEVELOPMENT.md)
beschrieben. Die vollständigen, aktuell gültigen Anforderungen an die
Integration stehen in [anforderung.yaml](anforderung.yaml).
