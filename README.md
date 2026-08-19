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
  - [Zeitgesteuertes Laden](#zeitgesteuertes-laden)
  - [Netzdienliches Laden](#netzdienliches-laden)
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
4. Danach folgt ein zweiter, **optionaler** Schritt "Netzladung": Vorbelegung
   für "Netzladung aktiv", "Netzladung Start" und "Netzladung Ende" (siehe
   [Zeitgesteuertes Laden](#zeitgesteuertes-laden)). Ohne Änderungen gelten
   die Defaults – deaktiviert, Zeitfenster 00:00–00:05. Alle drei Werte
   lassen sich später jederzeit über die entsprechenden Entitäten ändern.

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
| Leistungsvorgabe / Timeout / Steuermodus / Referenzwert Maximalleistung | Nur-Lese-Diagnosewerte – Leistungsvorgabe und Steuermodus werden intern auch von "Netzladung aktiv" und der Max-SOC-Sperre geschrieben, siehe [unten](#zeitgesteuertes-laden) |
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
| Max. SOC | Ziel-SOC (0–100 %) – siehe [unten](#zeitgesteuertes-laden). Ohne vorherige Einstellung 100 % (nicht 0), bleibt über Neustarts hinweg erhalten |
| Max. Netzladeleistung | Ziel-Leistung für die Netzladung (W) – siehe [unten](#zeitgesteuertes-laden). Ohne vorherige Einstellung einmalig mit dem beim Start gelesenen Ladeleistungsgrenzwert (Register 44) vorbelegt |

Es gibt bewusst keine eigene Ziel-SOC-/Leistungseinstellung für
zeitgesteuertes Laden: Es nutzt die zentralen Einstellungen oben.

### Schalter

| Entität | Beschreibung |
| --- | --- |
| Speicher On/Off | Schaltet den Speicher ein/aus |
| Netzladung aktiv | Aktiviert/deaktiviert das zeitgesteuerte Laden, siehe [unten](#zeitgesteuertes-laden) |
| Netzdienliches Laden aktiv | Aktiviert/deaktiviert das netzdienliche Laden, siehe [unten](#netzdienliches-laden) |

### Zeitgesteuertes Laden

Lädt den Speicher innerhalb eines konfigurierbaren Zeitfensters aktiv aus
dem Netz auf einen Ziel-SOC – unabhängig von PV-Überschuss, z. B. für
günstige Nachtstromtarife ("Lade auf 90 %, wenn es zwischen 1 und 5 Uhr
ist").

Schreibt über den SunSpec-Modus (Slave-ID 100, "Immediate Controls"):
Register 40051 (Steuermodus) auf Sollwertvorgabe, danach Register 40049
(Leistungsvorgabe in Prozent der Referenz-Maximalleistung, umgerechnet aus
"Max. Netzladeleistung"). Beide Register werden periodisch neu geschrieben
(Intervall aus dem geräteseitig gemeldeten Timeout, Register 40050,
abgeleitet), da das Gerät den Sollwert sonst verwirft.

**Entitäten** (unter "Steuerung" am Gerät):

| Entität | Beschreibung |
| --- | --- |
| Netzladung aktiv | Ein-/Ausschalten des Features |
| Netzladung Start | Startzeit (HH:MM) |
| Netzladung Ende | Endzeit (HH:MM) |
| Netzladung aktiv im Januar … Dezember | 12 Schalter, legen fest, in welchen Kalendermonaten das Zeitfenster überhaupt wirksam ist (siehe unten) |
| Zeitgesteuertes Laden aktiv | Diagnose-Sensor, zeigt ob gerade aktiv nachgeladen wird |

Genutzt wird der bereits vorhandene "Max. SOC" als Ziel (siehe
[Zahlenfelder](#zahlenfelder)) sowie "Max. Netzladeleistung" als
Ladeleistung – es gibt keine eigenen Einstellungen dafür.

Das Zeitfenster darf über Mitternacht laufen (z. B. Start 23:00, Ende
05:00). Ist Start = Ende (oder eines von beiden nicht gesetzt), gilt das
Fenster als leer – es wird dann nie geladen.

**Aktive Monate:** Zusätzlich zum Zeitfenster legen 12 Schalter ("Netzladung
aktiv im Januar" … "im Dezember") fest, in welchen Kalendermonaten die
Netzladung überhaupt wirksam ist – z. B. nur in den Monaten November,
Dezember und Januar zwischen 1 und 5 Uhr, für eine im Winter günstige
Nachtstromzeit. Default: alle 12 Monate aktiv, sodass sich bestehende
Konfigurationen nach einem Update unverändert verhalten. Ist kein einziger
Monat ausgewählt, ist das Feature ganzjährig inaktiv (analog zu einem
leeren Zeitfenster).

Vorbelegt werden können alle drei Werte optional bereits im zweiten Schritt
der Ersteinrichtung (siehe [Einrichtung](#einrichtung)); ohne Angabe gelten
die Defaults (deaktiviert, 00:00–00:05). Das wirkt sich nur auf den
allerersten Start eines neu eingerichteten Eintrags aus – danach gilt
ausschließlich der zuletzt über die Entitäten gesetzte Wert.

**PV-Überschuss-Abbruch:** Neben dem Fensterende beendet der Coordinator die
Netzladung auch aktiv, sobald am Smart Meter mehr als 200 W PV-Überschuss
gemessen werden (Konstante `SMARTMETER_PV_SURPLUS_THRESHOLD_WATT` in
`const.py`) – mitten im Zeitfenster, sobald das beim nächsten Poll-Zyklus
erkannt wird, nicht erst am konfigurierten Ende. Grundlage ist der Sensor
"Smart Meter Leistung" (`smartmeter_power`, Register 40072): ein **positiver**
Anzeigewert bedeutet Überschuss aus der Dachphotovoltaik, ein negativer Wert
Netzbezug – das Vorzeichen des rohen Modbus-Registers kann davon abweichen,
maßgeblich ist der bereits umgerechnete Anzeigewert. Ist der Wert (noch)
nicht verfügbar, z. B. weil der SunSpec-Modus gerade nicht erreichbar ist,
blockiert das die Netzladung nicht.

**Max-SOC-Sperre:** Unabhängig davon, ob zeitgesteuertes Laden aktiviert
ist, hält der Coordinator den Speicher aktiv auf 0 % Leistungsvorgabe
(Register 40051 weiterhin Sollwertvorgabe, Register 40049 = 0 %), sobald
der SOC "Max. SOC" erreicht oder überschreitet – auch wenn er z. B. durch
PV-Überschuss vollgeladen wurde. Das verhindert dauerhaftes Volladen auf
100 % (Batterie-Lebensdauer) und geht über die reine Ladebegrenzung hinaus:
Solange die Sperre aktiv ist, entlädt sich der Speicher nicht automatisch
zur Eigenverbrauchsdeckung. Erst wenn der SOC wieder unter den Zielwert
fällt, wird Register 40051 zurück auf 0 (SmartMeter-Nullregelung) gesetzt
und die normale Automatik (bzw. zeitgesteuertes Laden, falls zutreffend)
übernimmt wieder.

Aktiviert-Zustand sowie Start-/Endzeit bleiben über Neustarts hinweg
erhalten, ein einmal eingerichteter Zeitplan muss also nicht nach jedem
Home-Assistant-Neustart neu gesetzt werden.

**Wichtig:** Der manuelle `start_grid_charge`/`stop_grid_charge`-Service
schreibt weiterhin über den älteren Basic-Mode-Weg (Register 41, absoluter
Watt-Sollwert, freie Vorzeichenwahl) und läuft unabhängig vom
zeitgesteuerten Laden, mit eigenem Hintergrund-Task.

### Netzdienliches Laden

Eigenständiges Feature, das den Speicher innerhalb eines **eigenen**
Zeitfensters lädt – im Unterschied zur Netzladung aber **ausschließlich mit
PV-Überschuss**, nie aus dem Netz. Gedacht für Zeiträume, in denen der
Speicher netzdienlich (d. h. Einspeisung ins Netz reduzierend) geladen
werden soll, ohne dafür Netzstrom zu beziehen.

**Entitäten** (unter "Steuerung" am Gerät):

| Entität | Beschreibung |
| --- | --- |
| Netzdienliches Laden aktiv | Ein-/Ausschalten des Features |
| Netzdienliches Laden Start | Startzeit (HH:MM) |
| Netzdienliches Laden Ende | Endzeit (HH:MM) |
| Netzdienliches Laden aktiv im Januar … Dezember | 12 Schalter, legen fest, in welchen Kalendermonaten das Zeitfenster überhaupt wirksam ist (siehe unten) |
| Netzdienliches Laden aktiv (Sensor) | Diagnose-Sensor, zeigt ob gerade aktiv netzdienlich geladen wird |

Genutzt werden dieselben zentralen Einstellungen wie beim zeitgesteuerten
Laden – "Max. SOC" als Ziel-SOC und "Max. Netzladeleistung" als
Leistungsobergrenze; es gibt keine eigene Leistungseinstellung. Der
tatsächlich geschriebene Sollwert wird zusätzlich auf den gerade am Smart
Meter gemessenen PV-Überschuss gedeckelt (`min(Max. Netzladeleistung,
PV-Überschuss)`) und sinkt mit fallendem Überschuss im selben
Poll-Zyklus mit – es wird also nie mehr geladen, als gerade an Überschuss
zur Verfügung steht. Ist kein Smart-Meter-Wert bekannt (z. B. SunSpec-Modus
nicht erreichbar) oder liegt der gemessene Wert nicht über 200 W
Überschuss (`SMARTMETER_PV_SURPLUS_THRESHOLD_WATT`), startet netzdienliches
Laden nicht – im Gegensatz zur Netzladung, die in diesem Fall unbeeinflusst
weiterläuft.

Die Max-SOC-Sperre (siehe [oben](#zeitgesteuertes-laden)) gilt unverändert
auch für netzdienliches Laden. Zeitgesteuertes und netzdienliches Laden
schließen sich bereits über die entgegengesetzte PV-Überschuss-Bedingung
gegenseitig aus und können nie gleichzeitig einen Ladesollwert schreiben.

**Aktive Monate:** Wie bei der Netzladung legen 12 Schalter ("Netzdienliches
Laden aktiv im Januar" … "im Dezember") fest, in welchen Kalendermonaten
das Zeitfenster wirksam ist – z. B. nur in den Monaten Mai, Juni, Juli und
August zwischen 11 und 14 Uhr. Default: alle 12 Monate aktiv.

**Zeitfenster dürfen sich nicht überschneiden:** Das Zeitfenster des
netzdienlichen Ladens darf sich nicht mit dem Zeitfenster der Netzladung
überlappen – dabei zählen Tageszeit UND aktive Monate zusammen: Laufen
beide Zeitfenster nur in disjunkten Monaten (wie im Beispiel oben –
Netzladung nur November/Dezember/Januar, netzdienliches Laden nur
Mai–August), dürfen sich die Tageszeiten beliebig überlappen, da die
Fenster nie im selben Monat aktiv sind.

- Ein Änderungsversuch an einer der beiden **Monats-Auswahlen**, der zu
  einer echten Überschneidung (gleiche Tageszeit UND gemeinsamer Monat)
  führen würde, wird abgelehnt und im Frontend als Fehler angezeigt – die
  bisherige Monats-Auswahl bleibt dabei unverändert bestehen.
- Ein Änderungsversuch an einer der beiden **Start-/Endzeit-Entitäten**
  ("Netzladung Start"/"Ende" bzw. "Netzdienliches Laden Start"/"Ende"), der
  zu einer echten Überschneidung führen würde, wird dagegen NICHT
  abgelehnt: Stattdessen erscheint eine Benachrichtigung (Home Assistant →
  Einstellungen → Benachrichtigungen bzw. im Benachrichtigungs-Verlauf) mit
  beiden betroffenen Zeitfenstern (Tageszeit + aktive Monate), und die
  soeben geänderte Zeit (nur Start ODER nur Ende, je nachdem welche
  Entität geändert wurde) wird geleert. Eine leere Start- oder Endzeit
  bewirkt immer, dass das jeweilige Feature nicht ausgeführt wird (siehe
  oben, "leeres Zeitfenster") – ein geleertes Feld muss also anschließend
  bewusst neu gesetzt werden, damit das Feature wieder aktiv wird.

  Hintergrund: Start und Ende sind zwei getrennte Entitäten. Ändert man ein
  Zeitfenster in zwei Schritten (z. B. erst Start, dann Ende), validiert
  Home Assistant jeden Schritt einzeln gegen den zu diesem Zeitpunkt noch
  alten Wert der jeweils anderen Grenze – ein rein durch diese Zwischenzeit
  entstehender, in Wahrheit gar nicht beabsichtigter Zwischenzustand könnte
  sonst fälschlich als Überschneidung erkannt und die Änderung dauerhaft
  mit dem alten (möglicherweise ebenfalls nicht mehr gewollten) Wert
  blockiert werden. Das Leeren statt Zurücksetzen auf den alten Wert
  vermeidet diese Verwirrung. Um ein komplettes Zeitfenster ohne
  Zwischenschritt zu verschieben, siehe die Services
  `sax_power.set_timed_charge_window` / `sax_power.set_grid_serving_window`
  unten – sie setzen Start und Ende atomar in einem Aufruf und prüfen dabei
  ausschließlich das tatsächliche Ziel-Fenster.

  Aus einem verwandten Grund empfiehlt es sich, beim nachträglichen
  Umstellen auf disjunkte Monate bei bereits überlappenden Zeitfenstern
  zunächst die Monate beider Features anzupassen und erst danach die Zeiten
  zu ändern (oder umgekehrt), statt beides gleichzeitig schrittweise zu
  verschieben.

Aktiviert-Zustand, Start-/Endzeit sowie die aktiven Monate bleiben über
Neustarts hinweg erhalten (analog zum zeitgesteuerten Laden). Es gibt dafür
keinen Vorbelegungsschritt im Config Flow – das Feature wird ausschließlich über
die Entitäten nach der Ersteinrichtung konfiguriert und ist per Default
deaktiviert.

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

- **`sax_power.set_timed_charge_window`** – setzt Start- und Endzeit des
  Netzladung-Zeitfensters atomar in einem Aufruf, statt über die einzelnen
  Start-/Ende-Entitäten (siehe ["Zeitfenster dürfen sich nicht
  überschneiden"](#netzdienliches-laden) oben für den Hintergrund).

  | Feld | Beschreibung |
  | --- | --- |
  | `device_id` | SAX Power Gerät |
  | `start` | Startzeit des Zeitfensters |
  | `end` | Endzeit des Zeitfensters |

- **`sax_power.set_grid_serving_window`** – analog zu
  `set_timed_charge_window`, für das netzdienliche Laden.

  | Feld | Beschreibung |
  | --- | --- |
  | `device_id` | SAX Power Gerät |
  | `start` | Startzeit des Zeitfensters |
  | `end` | Endzeit des Zeitfensters |

Alle vier Services werden über einen `device_id`-Parameter an das jeweilige
SAX Power Gerät adressiert (relevant, falls mehrere Speicher eingerichtet
sind).

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
- **Max. SOC** ist kein natives Geräteregister, sondern eine
  Software-Logik: Beim Erreichen des Zielwerts hält der Coordinator den
  Speicher über den SunSpec-Modus aktiv auf 0 % Leistungsvorgabe, siehe
  [Max-SOC-Sperre](#zeitgesteuertes-laden).
- **Der `start_grid_charge`-Service** schreibt einen absoluten Watt-Sollwert
  auf Basic-Mode-Register 41. Ob dieses Register auf einem gegebenen Gerät
  aktiv nutzbar ("freigeschaltet") ist, ist geräte-/firmwareabhängig und
  sollte vor dem produktiven Einsatz am eigenen Gerät geprüft werden.
- **Vorzeichenkonvention** von Register 40049 (Leistungsvorgabe,
  zeitgesteuertes Laden/Max-SOC-Sperre) ist herstellerseitig ebenfalls nicht
  dokumentiert. Die Integration geht in Analogie zu Register 40029 davon
  aus: negativ = Laden (die Integration schreibt hier bewusst nur negative
  Sollwerte). Eine frühere "manuelle Entladung" mit positiven Sollwerten auf
  diesem Register bzw. auf Register 41 wurde gegen echte Hardware getestet
  und zeigte keine Wirkung - der Hersteller hat bestätigt, dass eine
  ferngesteuerte manuelle Entladung nicht vorgesehen ist.
- **SunSpec-Modus ist optional**: Ist er nicht erreichbar (z. B. zu alte
  Firmware – Master V61/Gateway V54 oder neuer erforderlich), bleiben die
  Basic-Mode-Sensoren (SOC, Schalter) trotzdem verfügbar; nur die
  SunSpec-Sensoren zeigen "unbekannt", bis der Block wieder lesbar ist.
  Zeitgesteuertes Laden und die Max-SOC-Sperre benötigen den SunSpec-Modus
  zwingend (Schreibpfad) und können in diesem Zustand nicht greifen. Ein
  dauerhafter Ausfall wird zusätzlich als Home-Assistant-Repair-Issue
  angezeigt.

## Weiterführende Dokumentation

Interna wie Datenfluss, Register-Mapping, Testausführung und lokale
Entwicklung (DevContainer) sind in [DEVELOPMENT.md](DEVELOPMENT.md)
beschrieben. Die vollständigen, aktuell gültigen Anforderungen an die
Integration stehen in [anforderung.yaml](anforderung.yaml).
