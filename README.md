# SAX Power Home – Home Assistant Integration

Custom Component für die Anbindung eines **SAX Power Home (Plus)** Heimspeichers
an Home Assistant über die Modbus-TCP-Schnittstelle.

## Funktionen

### Sensoren (`sensor.py`)

Alle in `modbus_llm.yaml` dokumentierten Register sind als Sensor lesbar
(siehe `anforderung.yaml`, Anforderung `REQ-ALL-REGISTERS-READABLE`) – mit
deutschen, fachlich verständlichen Namen. Ausgenommen sind nur Register ohne
definierte Bedeutung ("N.A." laut Hersteller-Doku) und "Immediate Controls"
(Slave-ID 123), das auf aktueller Hardware noch nicht verfügbar ist.

**Basic Mode (Slave-ID 64):**

| Entität | Quelle | Beschreibung |
| --- | --- | --- |
| Ladezustand | Register 46 | SOC des Speichers in % |
| Entladeleistung | Register 47 (positiver Anteil) | Leistung, die aktuell ins Hausnetz abgegeben wird, in W |
| Ladeleistung | Register 47 (negativer Anteil, invertiert) | Leistung, die aktuell in den Speicher geladen wird, in W |
| Smart Meter Leistung (Basic Mode) | Register 48 | Leistung am Smart Meter, in W |
| Speicher Schaltzustand (Text) | Register 45 | "Aus" / "Ein" / "Verbunden" als Klartext (Diagnose) |
| Sollwert Leistung P | Register 41 | Aktuell gesetzter P-Sollwert, in W (Diagnose) |
| Sollwert cos(phi) | Register 42 | Aktuell gesetzter cos(phi)-Sollwert (Diagnose) |

Register 47 liefert einen einzelnen vorzeichenbehafteten Wert für Lade-/
Entladeleistung. Die Integration liest ihn einmal und leitet daraus zwei
Sensoren ab: ist der Wert positiv, wird er als Entladeleistung angezeigt
(Ladeleistung = 0), ist er negativ, als Ladeleistung (Entladeleistung = 0).

**Extended Mode – Speicher (Slave-ID 40, Register 40071–40094):**

SunSpec-Rohwerte (Ströme, Spannungen, Leistungen, Frequenz, Leistungsfaktor)
werden über die zugehörigen `sunssf`-Skalierungsregister in physikalische
Einheiten umgerechnet (`Wert × 10^sunssf`, siehe `coordinator.apply_sunssf`).
Jedes Skalierungsregister ist zusätzlich als eigener Diagnose-Sensor
sichtbar, damit wirklich jedes Register lesbar bleibt.

| Entität | Beschreibung |
| --- | --- |
| SunSpec ID / SunSpec Länge | Diagnose-Werte des SunSpec-Blocks |
| Phasenstrom Summe (Herstellerwert) | Herstellerseitig bereits summierter Wert (Register 40073) |
| Phasenstrom L1/L2/L3 | Einzelne Phasenströme, in A |
| **Phasenstrom Summe (L1+L2+L3, berechnet)** | Von der Integration berechnete Summe der drei Phasen |
| Spannung L1/L2/L3 | Einzelne Phasenspannungen, in V |
| **Spannung Summe (L1+L2+L3, berechnet)** | Von der Integration berechnete Summe der drei Phasen |
| Wirkleistung Summe (AC) / Scheinleistung Summe (AC) / Blindleistung Summe (AC) | in W / VA / var |
| Netzfrequenz | in Hz |
| Leistungsfaktor | in % |

**Extended Mode – Smart Meter (Slave-ID 40, Register 40095–40110):**

| Entität | Beschreibung |
| --- | --- |
| Smart Meter Energie eingespeist / bezogen | in kWh |
| Smart Meter Schaltzustand Speicher | Klartext-Spiegel des Basic-Mode-Schaltzustands (Diagnose) |
| Smart Meter Strom L1/L2/L3 | in A (fester Faktor 10⁻², nicht über ein sunssf-Register) |
| **Smart Meter Strom Summe (L1+L2+L3, berechnet)** | Berechnete Summe der drei Phasen |
| Smart Meter Wirkleistung L1/L2/L3 | in W (in `modbus_llm.yaml` fälschlich als L1/L12/L13 statt L1/L2/L3 benannt) |
| **Smart Meter Wirkleistung Summe (L1+L2+L3, berechnet)** | Berechnete Summe der drei Phasen |
| Smart Meter Spannung L1/L2/L3 | in V (laut Doku unskaliert) |
| **Smart Meter Spannung Summe (L1+L2+L3, berechnet)** | Berechnete Summe der drei Phasen |
| Smart Meter Wirkleistung Gesamt | Herstellerseitig bereits summierter Wert (Register 40110) |

Für jede Gruppe von drei Phasenregistern (L1/L2/L3) wird zusätzlich ein
eigener, berechneter Summensensor bereitgestellt – auch dort, wo der
Hersteller bereits einen eigenen Summenwert liefert (dieser bleibt als
separater, klar gekennzeichneter Sensor erhalten). Betroffene Gruppen:
Phasenströme und -spannungen im Speicher-Block sowie Phasenströme,
-wirkleistung und -spannungen im Smart-Meter-Block.

### Zahlenfelder (`number.py`)

| Entität | Register | Beschreibung |
| --- | --- | --- |
| Maximaler Lade-SOC | – (Software-Logik) | Ziel-SOC (0–100 %), ab dem die Ladung gestoppt wird |
| Ladeleistungsgrenzwert | Register 44 | Direkt schreibbares Leistungslimit für die Ladung (W) |
| Entladeleistungsgrenzwert | Register 43 | Direkt schreibbares Leistungslimit für die Entladung (W) |

**Maximaler Lade-SOC** ist kein natives Geräteregister. Der `DataUpdateCoordinator`
vergleicht bei jedem Poll den aktuellen SOC (Register 46) mit dem gesetzten
Zielwert: wird er erreicht/überschritten, schreibt der Coordinator `0` in das
Ladelimit-Register (44) und merkt sich den zuvor gelesenen Wert; sinkt der
SOC wieder darunter, wird der ursprüngliche Wert zurückgeschrieben. Siehe
`SaxPowerCoordinator._async_enforce_max_soc` in `coordinator.py`.

### Schalter (`switch.py`)

| Entität | Register | Beschreibung |
| --- | --- | --- |
| Speicher | Register 45 | Schaltet den Speicher ein/aus. Aus = 1, Ein = 2; beim Lesen gilt zusätzlich 3 = "Verbunden" als "an" |

### Services (`__init__.py`, `services.yaml`)

- **`sax_power.start_grid_charge`** – versetzt den Speicher implizit in den
  P-Sollwert-Modus (Schreiben von Register 41/40042) und wiederholt den
  Schreibvorgang alle 30 Sekunden im Hintergrund, solange der Service aktiv
  ist. Das ist nötig, weil der Speicher laut Dokumentation den Sollwert nach
  einem Timeout verwirft, wenn er nicht periodisch aufgefrischt wird.

  | Feld | Beschreibung |
  | --- | --- |
  | `device_id` | SAX Power Gerät |
  | `power` | Sollwert in Watt (-32768 bis 32767) |

- **`sax_power.stop_grid_charge`** – bricht den Hintergrund-Task ab.

  | Feld | Beschreibung |
  | --- | --- |
  | `device_id` | SAX Power Gerät |

Beide Services werden über einen `device_id`-Parameter an das jeweilige SAX
Power Gerät adressiert (relevant, falls mehrere Speicher eingerichtet sind).

### Sonstiges

- GUI-Einrichtung über den Home Assistant Config Flow (keine YAML-Konfiguration nötig)
- Asynchrone Anbindung via `pymodbus` (`AsyncModbusTcpClient`), ein zentraler
  `DataUpdateCoordinator` pro Config Entry bündelt alle Reads/Writes und
  verhindert parallele/kollidierende Modbus-Zugriffe (`asyncio.Lock`)

### IP-Adresse nachträglich ändern

Die Verbindungsdaten (IP-Adresse, Port, Slave-IDs, Aktualisierungsintervall)
werden bei der Ersteinrichtung im Home-Assistant-Config-Entry gespeichert und
lassen sich jederzeit über die Oberfläche ändern, z. B. wenn sich die IP des
SAX Speichers ändert:

**Einstellungen → Geräte & Dienste → SAX Power Home → ⋮ (Gerät) → Neu konfigurieren**

Das Formular ist mit den aktuell gespeicherten Werten vorbelegt. Die neue
Verbindung wird vor dem Speichern geprüft (derselbe Testread wie bei der
Ersteinrichtung); bei Erfolg werden die Werte persistiert und die Integration
lädt automatisch mit den neuen Daten neu. Siehe `anforderung.yaml`,
Anforderung `REQ-IP-CONFIGURABLE-UI`.

## Aufbau

```
custom_components/sax_power/
├── manifest.json      Metadaten, Requirements (pymodbus>=3.10.0), Domain
├── const.py            Register-/Konfigurationskonstanten, Defaults
├── config_flow.py       GUI-Einrichtung, Verbindungsvalidierung
├── coordinator.py       DataUpdateCoordinator: Reads (Basic+Extended), Writes,
│                          SunSpec-Skalierung, Phasensummen, Max-SOC-Logik, Netzladung
├── entity.py             Basisklasse mit gemeinsamer DeviceInfo
├── __init__.py            Setup/Teardown des Config Entry, Service-Registrierung
├── sensor.py              ~48 Sensoren, beschreibungsbasiert (eine Klasse, eine Liste)
├── number.py              Max-SOC, Lade-/Entladeleistungsgrenzwert
├── switch.py              Speicher ein/aus
├── services.yaml           Service-Schema für die UI
└── translations/            DE/EN-Übersetzungen (strings.json ist die Vorlage)

tests/                Siehe Abschnitt "Tests"
.devcontainer/         VS Code DevContainer für lokale Entwicklung
```

**Verbindungsdaten ändern:** `config_flow.py` implementiert sowohl
`async_step_user` (Ersteinrichtung) als auch `async_step_reconfigure`
(spätere Änderung, z. B. der IP-Adresse) über eine gemeinsame Methode
(`_async_step_connection`). Beide validieren die Verbindung mit demselben
Testread, bevor die Daten gespeichert werden. Siehe Abschnitt "IP-Adresse
nachträglich ändern" oben.

**Datenfluss:** `config_flow.py` sammelt Host/Port/Slave-IDs/Intervall und
validiert die Verbindung mit einem Testlesen. `__init__.py` baut daraus einen
`AsyncModbusTcpClient` und einen `SaxPowerCoordinator` (`coordinator.py`),
lädt anschließend die Plattformen `sensor`, `number`, `switch` und
registriert die beiden Services. Jede Entität (`entity.py` als Basisklasse)
liest ihren Zustand ausschließlich aus `coordinator.data` und schreibt
Änderungen über `coordinator.async_write_register(...)`.

**Register-Mapping:** Der Coordinator liest pro Poll-Intervall zwei
zusammenhängende Register-Blöcke mit je einem `read_holding_registers`-
Aufruf: Basic Mode (Slave-ID 64, Register 41–48, `READ_BLOCK_START`/
`READ_BLOCK_COUNT`) und Extended Mode (Slave-ID 40, Register 70–109 –
Speicher- und Smart-Meter-Teilblock sind zusammenhängend,
`READ_BLOCK_EXT_START`/`READ_BLOCK_EXT_COUNT`). Innerhalb eines Blocks gilt
weiterhin "alles oder nichts": Schlägt der Basic-Mode-Read fehl, schlägt das
gesamte Update fehl (`UpdateFailed`), da Basic Mode die Mindestanforderung
für jede Funktion der Integration ist. Schlägt dagegen nur der
Extended-Mode-Read fehl (z. B. weil Extended Mode auf dem SAX-Gateway nicht
freigeschaltet ist), bleiben die Basic-Mode-Sensoren unverändert verfügbar
und lediglich die Extended-Mode-Sensoren zeigen "unbekannt", bis der Block
wieder lesbar ist (`SaxPowerCoordinator._async_read_extended`, siehe
anforderung.yaml `REQ-EXTENDED-MODE-RESILIENCE`). Ein dauerhafter
Extended-Mode-Ausfall wird zusätzlich als Home-Assistant-Repair-Issue
angezeigt. Die genaue Zuordnung Protokolladresse ↔ interne Adresse ↔
Bedeutung steht in `modbus_llm.yaml`; `const.py` referenziert nur die
intern verwendeten Adressen.

**SunSpec-Skalierung & Phasensummen:** `coordinator.apply_sunssf(raw_value,
raw_scale_factor)` wendet `Wert × 10^sunssf` an (beide Rohwerte signed
16-Bit). `SaxPowerCoordinator._parse_extended` wertet damit alle
Extended-Mode-Register aus und berechnet für jede Phasen-Trio-Gruppe
(L1/L2/L3) zusätzlich eine Summe – unabhängig davon, ob der Hersteller
bereits einen eigenen Summenwert liefert.

**Refresh-Verhalten:** Nutzerausgelöste Schreibaktionen (Switch, Number)
rufen nach dem Schreiben `coordinator.async_refresh()` auf – das ist die
*ungedebouncte* Coordinator-Methode. `async_request_refresh()` (debounced)
wird bewusst vermieden, da bei schnell aufeinanderfolgenden Aktionen sonst
ein verzögerter/verworfener Refresh dazu führen kann, dass die UI kurzzeitig
einen veralteten Wert zeigt.

## Tests

```
tests/
├── conftest.py                  Aktiviert das Laden von custom_components in Tests
├── test_coordinator.py           Unit-Tests: signed/unsigned16-Konvertierung, apply_sunssf,
│                                  Max-SOC-Klemmung, Fehlerbehandlung bei Modbus-Schreibfehlern,
│                                  Parsing des Extended-Mode-Blocks inkl. Phasensummen (gemockt)
├── test_config_flow.py            Unit-Tests: erfolgreicher Config Flow, "cannot_connect"-Fehler
│                                  (gemockter AsyncModbusTcpClient)
├── test_sensor_descriptions.py     Konsistenz-Tests über alle ~48 Sensor-Beschreibungen:
│                                  eindeutige Keys, vollständige DE/EN-Übersetzungen,
│                                  value_fn wirft für keinen Sensor eine Exception
├── test_integration_live.py        End-to-End-Tests gegen einen echten, lokal gestarteten
│                                  Modbus-TCP-Server (kein Mock) – prüft den kompletten Weg
│                                  Config Entry → Coordinator → Entities → echtes Wire-Protokoll,
│                                  inkl. Regressionstest für REQ-EXTENDED-MODE-RESILIENCE
│                                  (Extended Mode nicht erreichbar → Basic-Mode-Sensoren bleiben da)
├── test_real_hardware.py           Optionaler Live-Hardware-Test gegen einen *echten* SAX
│                                  Speicher (siehe Abschnitt "Test gegen echte Hardware" unten)
└── real_device.yaml                Verbindungsdaten (IP etc.) für test_real_hardware.py
```

`test_coordinator.py`, `test_config_flow.py` und `test_sensor_descriptions.py`
mocken den `pymodbus`-Client bzw. arbeiten rein auf Python-Ebene und prüfen
die Programmlogik. `test_integration_live.py` geht einen Schritt weiter: Er
startet mit `pymodbus.server.ModbusTcpServer` einen echten Modbus-TCP-Server
auf `127.0.0.1` mit simulierten Geräten (Slave-ID 64 Basic Mode, Slave-ID 40
Extended Mode), befüllt sie mit Registerwerten aus `modbus_llm.yaml` und lässt
die Integration real darüber kommunizieren. Geprüft werden u. a.:

- korrektes Lesen von SOC/Lade-/Entladeleistung über echtes TCP
- Extended-Mode-Register mit SunSpec-Skalierung (z. B. Netzfrequenz,
  Leistungsfaktor) über echtes TCP
- berechnete Phasensummen unterscheiden sich korrekt vom parallel
  exponierten Herstellerwert
- Speicher-Switch aus/an inkl. Rücklesen des geschriebenen Werts
- Max-SOC-Klemmung (SOC über Zielwert → Ladelimit-Register wird auf 0 geschrieben)
- Netzladung: periodischer Sollwert-Write auf Register 41, verifiziert über
  einen unabhängigen zweiten Modbus-Client
- Fehlt der Extended-Mode-Server (Slave-ID 40) komplett: Config Entry lädt
  trotzdem erfolgreich, Basic-Mode-Sensoren liefern echte Werte,
  Extended-Mode-Sensoren zeigen "unbekannt" statt die Integration am Start
  zu hindern

Dieser Live-Test hat einen echten Bug aufgedeckt (debounced Refresh, siehe
oben) – ein reiner Mock-Test hätte das nicht sichtbar gemacht, da er die
zeitliche Reihenfolge realer Schreibvorgänge nicht abbildet.

Alle Tests laufen auch ohne echte Hardware und ohne Internetzugriff (der
Live-Test bindet nur an `127.0.0.1`) – der Live-Hardware-Test
(`test_real_hardware.py`) wird ohne hinterlegte IP automatisch
übersprungen, siehe Abschnitt "Test gegen echte Hardware" unten.

### Manuelle Testausführung

Die Tests laufen außerhalb des DevContainers in einer eigenen Python-
Umgebung (venv), damit `homeassistant` & Co. nicht die System-Python-
Installation zumüllen:

```bash
cd sax-ha

# Einmalig: virtuelle Umgebung anlegen und Abhängigkeiten installieren
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements_test.txt

# Alle Tests ausführen
pytest -v
```

Bei künftigen Läufen genügt (ggf. nach erneutem `pip install`, falls sich
`requirements_test.txt` geändert hat):

```bash
source .venv/bin/activate
pytest -v
```

Nützliche Varianten:

| Befehl | Zweck |
| --- | --- |
| `pytest` | Alle Tests, kompakte Ausgabe |
| `pytest -v` | Alle Tests, ein Ergebnis pro Testfall |
| `pytest -rs` | Zusätzlich Grund für übersprungene (`SKIPPED`) Tests anzeigen |
| `pytest tests/test_coordinator.py -v` | Nur eine Testdatei |
| `pytest -k max_soc -v` | Nur Tests, deren Name "max_soc" enthält |
| `pytest tests/test_real_hardware.py -v` | Nur der Live-Hardware-Test (siehe unten) |

Im **DevContainer** (`.devcontainer/`) sind `homeassistant`, `pytest` etc.
bereits vorinstalliert – dort reicht direkt `pytest -v` ohne eigenes venv.

**Mögliche Probleme und Lösungen:**

| Problem | Ursache | Lösung |
| --- | --- | --- |
| `command not found: pip` | Auf macOS/Linux ist `pip` oft nicht direkt im `PATH`, nur `pip3`/`python3 -m pip`. | Venv aktivieren (`source .venv/bin/activate`) – darin heißt der Befehl wieder schlicht `pip`. Alternativ `python3 -m pip install -r requirements_test.txt`. |
| `ModuleNotFoundError: No module named 'homeassistant'` (o. Ä.) | venv nicht aktiviert oder `pip install -r requirements_test.txt` noch nicht/nicht erneut ausgeführt. | `source .venv/bin/activate` prüfen (Prompt zeigt `(.venv)`), danach `pip install -r requirements_test.txt` (erneut) ausführen. |
| Installation von `homeassistant` dauert sehr lange / bricht ab | `homeassistant` hat viele Abhängigkeiten; instabile Internetverbindung. | Erneut versuchen, ggf. `pip install -r requirements_test.txt -v` für Fortschrittsanzeige. Reiner Installationsvorgang, kein Testproblem. |
| `pytest_homeassistant_custom_component...SocketBlockedError` / `Socket opened during test` bei eigenen neuen Tests | pytest-homeassistant-custom-component sperrt Socket-Erstellung standardmäßig komplett (bis auf `127.0.0.1`). Die `socket_enabled`-Fixture aus pytest-socket **reicht dafür allein nicht aus** – sie hebt zwar die Socket-Sperre auf, wird aber vom Setup-Hook des HA-Test-Plugins wieder auf `127.0.0.1` zurückgesetzt, sobald eine echte externe IP angesprochen wird. | Für Verbindungen zu einer echten externen IP explizit `pytest_socket.enable_socket()` gefolgt von `pytest_socket.socket_allow_hosts([host, "127.0.0.1"], allow_unix_socket=True)` aufrufen (siehe `real_client`-Fixture in `test_real_hardware.py`). Für Verbindungen nur zu `127.0.0.1` (wie in `test_integration_live.py`) genügt weiterhin die `socket_enabled`-Fixture. |
| `tests/test_real_hardware.py` wird übersprungen (`SKIPPED`) | Kein `host` in `tests/real_device.yaml` hinterlegt, oder der Speicher ist gerade nicht erreichbar. | Mit `pytest -rs` den genauen Skip-Grund anzeigen lassen. `host` in `tests/real_device.yaml` eintragen (siehe Abschnitt unten) bzw. Erreichbarkeit prüfen (siehe nächste Zeile). |
| Live-Hardware-Test bricht mit Verbindungsfehler ab statt zu überspringen | Der erste Verbindungsversuch (`connect()`) klappt kurzzeitig, ein späterer Read schlägt dann fehl (Netzwerk instabil, falscher Port/Slave-ID). | IP/Port in `tests/real_device.yaml` prüfen (`ping <IP>`, `nc -vz <IP> 502`). Prüfen, ob eine andere Anwendung (z. B. eine bereits laufende Home-Assistant-Instanz) parallel denselben Modbus-Port belegt – SAX-Geräte erlauben oft nur eine aktive Verbindung gleichzeitig. |
| `test_read_real_extended_mode_values` wird übersprungen, `test_read_real_basic_mode_values` läuft durch | Extended Mode (Slave-ID 40) ist auf dem SAX-Gateway nicht freigeschaltet/erreichbar – das Gerät antwortet dann entweder mit einer Modbus-Fehlerantwort oder (häufiger) mit Modbus-Exception-Code 11 "Gateway Target Device Failed to Respond", was pymodbus als `ModbusIOException` auswirft. | Erwartetes, dokumentiertes Verhalten (siehe `REQ-EXTENDED-MODE-RESILIENCE`) – kein Fehler, entspricht der Fehlerbehandlung im produktiven Coordinator. Falls Extended Mode erwartet wird: Freischaltung beim Hersteller/Installateur klären. |
| `ruff`/`black` melden Formatierungsfehler bei eigenen Änderungen | Code entspricht nicht dem Projektstil (Zeilenlänge 88, Formatierung). | `pip install ruff black` (falls nicht vorhanden), dann `black custom_components tests` zum automatischen Formatieren und `ruff check custom_components tests` zur Kontrolle. |
| Tests schlagen nach einem `git pull` plötzlich fehl | `requirements_test.txt` hat sich geändert (neue/aktualisierte Abhängigkeit), venv ist veraltet. | `source .venv/bin/activate && pip install -r requirements_test.txt` erneut ausführen. |

### Test gegen echte Hardware

`tests/test_real_hardware.py` liest – anders als `test_integration_live.py`
(simulierter Server) – Werte direkt von einem echten SAX Power Home (Plus)
im lokalen Netz. Rein lesend, kein Schreibzugriff.

Die Ziel-IP steht in `tests/real_device.yaml` (im Repository abgelegt,
siehe `anforderung.yaml` `REQ-REAL-HARDWARE-TESTS`):

```yaml
host: null   # <- echte IP eintragen, z. B. "192.168.1.50"
port: 502
slave_id_basic: 64
slave_id_extended: 40
connect_timeout: 3
```

Solange `host: null` (Auslieferungszustand) oder der Speicher nicht
erreichbar ist, werden die beiden Tests automatisch übersprungen (kein
Fehlschlag) – der Test läuft also weder in CI noch bei Entwicklern ohne
physischen Zugriff auf die Hardware. Nach Eintragen einer echten IP:

```bash
pytest tests/test_real_hardware.py -v
```

## Bekannte Lücken / Annahmen

- **Temperatursensor**: Im vorliegenden Register-Mapping (`modbus_llm.yaml`)
  ist kein Temperaturregister dokumentiert. Der Sensor ist daher noch nicht
  implementiert. Sobald die Registeradresse bekannt ist, kann sie einfach in
  `custom_components/sax_power/const.py` und `sensor.py` ergänzt werden.
- **Vorzeichenkonvention** von Register 47 (Leistung P des Speichers) und dem
  P-Sollwert-Register 41 ist herstellerseitig nicht dokumentiert. Die
  Integration geht davon aus: positiv = Entladung/Einspeisung. Bitte am
  realen Gerät verifizieren und ggf. in `coordinator.py`/`sensor.py` anpassen.
- **Max-SOC** ist kein natives Geräteregister, sondern eine Software-Logik:
  Beim Erreichen des Zielwerts wird das Ladelimit-Register (44) auf 0
  gesetzt und beim Unterschreiten wieder freigegeben.
- **"Immediate Controls" (Slave-ID 123)** ist laut `modbus_llm.yaml` "Future
  Release / Experimental (Stand 03/25 noch nicht verfügbar)" und existiert
  auf aktueller Hardware nicht – daher bewusst nicht implementiert.
- **Registerbenennung Smart-Meter-Wirkleistung**: `modbus_llm.yaml` benennt
  die drei Phasenwirkleistungs-Register als "L1"/"L12"/"L13" statt
  "L1"/"L2"/"L3". Die Integration behandelt dies als Tippfehler in der
  Quelldokumentation und interpretiert sie als L1/L2/L3.
- **Extended Mode ist optional** (seit `REQ-EXTENDED-MODE-RESILIENCE`): Der
  Coordinator fragt seit `REQ-ALL-REGISTERS-READABLE` zusätzlich den
  Extended-Mode-Block (Slave-ID 40) ab. Ist dieser nicht erreichbar (z. B.
  weil Extended Mode auf dem SAX-Gateway nicht freigeschaltet ist), bleiben
  die Basic-Mode-Sensoren (SOC, Lade-/Entladeleistung, Schalter) trotzdem
  verfügbar; nur die Extended-Mode-Sensoren zeigen "unbekannt", bis der
  Block wieder lesbar ist. Vorher führte ein nicht erreichbarer
  Extended-Mode-Block dazu, dass die gesamte Integration mit
  `ConfigEntryNotReady` scheiterte und **gar keine** Entities angelegt
  wurden – das war die Ursache für den Fehlerbericht "es werden keine
  Sensoren angeboten".

## Installation über HACS (empfohlen)

1. In Home Assistant: **HACS → Integrationen → ⋮ (oben rechts) → Benutzerdefinierte Repositories**
2. Repository-URL eintragen: `https://github.com/dr-dimitri/sax-ha`
   Kategorie: **Integration**
3. Auf **Hinzufügen** klicken, danach die Integration "SAX Power Home" in HACS suchen und installieren
4. Home Assistant neu starten
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → nach "SAX Power" suchen
6. IP-Adresse, Port (Standard 502), Slave-IDs (Standard 64 & 40) und Aktualisierungsintervall eingeben

## Manuelle Installation

1. Ordner `custom_components/sax_power` in das `custom_components`-Verzeichnis
   deiner Home Assistant Konfiguration kopieren
2. Home Assistant neu starten
3. Integration wie oben über die UI hinzufügen

## Lokale Entwicklung (DevContainer)

Das Repo enthält einen VS Code DevContainer für die lokale Entwicklung/Tests:

1. Repo in VS Code öffnen, "Reopen in Container" wählen
2. Im Container: `hass -c config` startet eine lokale Home Assistant Instanz
   auf Port 8123 mit bereits verlinkter Custom Component
3. Tests ausführen: `pytest -v`
4. Linting/Formatierung: `ruff check custom_components tests` bzw. `black custom_components tests`

## Quellen

Die Anforderungen und das Modbus-Register-Mapping stammen aus
`anforderung.yaml` bzw. `modbus_llm.yaml` in diesem Repository.
