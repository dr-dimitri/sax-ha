# SAX Power Home – Home Assistant Integration

Custom Component für die Anbindung eines **SAX Power Home (Plus)** Heimspeichers
an Home Assistant über die Modbus-TCP-Schnittstelle.

## Funktionen

### Sensoren (`sensor.py`)

Die Sensoren stammen aus zwei unterschiedlichen Modbus-Registerkarten mit
unterschiedlicher Slave-ID (siehe `modbus_llm.yaml` und `modbus.pdf`, die
offizielle sax-power.net-Dokumentation im Repo-Root):

**Basic Mode (Slave-ID 64):**

| Entität | Quelle | Beschreibung |
| --- | --- | --- |
| Ladezustand | Register 46 | SOC des Speichers in % |
| Speicher Schaltzustand (Text) | Register 45 | "Aus" / "Ein" / "Verbunden" als Klartext (Diagnose) |
| Sollwert Leistung P | Register 41 | Aktuell gesetzter P-Sollwert, in W (Diagnose) |
| Sollwert cos(phi) | Register 42 | Aktuell gesetzter cos(phi)-Sollwert (Diagnose) |

Die früher hier ebenfalls gelesenen Register 47 ("Leistung P des
Speichers") und 48 ("Leistung des Smart Meters") wurden entfernt – ein
Live-Test gegen echte Hardware ergab dort wiederholt physikalisch
unplausible Werte (~16000W bei einem 4600W-Gerät im Leerlauf, vermutlich
ein Firmware-Bug). Entlade-/Ladeleistung sowie Smart-Meter-Leistung kommen
seitdem zuverlässig aus dem SunSpec-Modus, siehe unten
(`anforderung.yaml`, `REQ-SUNSPEC-MODE-CORRECTION`).

**SunSpec-Modus (Slave-ID 100, Register 40000–40114, siehe `modbus.pdf`):**

Ein einzelner zusammenhängender Registerblock mit fünf SunSpec-Modellen:
Common (Geräteidentität), "3Ph Inverter" (103, Speicherelektronik),
"Immediate Controls" (123, Sollwertvorgabe), "WYE Connect 3Ph Meter" (203,
Netz/Smart Meter) und "Battery Base" (802, Akkuzellen). SunSpec-Rohwerte
werden über die zugehörigen `sunssf`-Skalierungsregister in physikalische
Einheiten umgerechnet (`Wert × 10^sunssf`, siehe `coordinator.apply_sunssf`).

| Entität | Beschreibung |
| --- | --- |
| Hersteller / Gerätemodell / Softwareversion Master/Gateway / Seriennummer | Geräteidentität (Diagnose) |
| **Entladeleistung / Ladeleistung** | Aus Register 40029 ("Wirkleistung Speicher Summe") abgeleitet – ersetzt das defekte Basic-Mode-Register 47 |
| Speicher Stromsumme / -Strom A/B/C | in A |
| Speicher Spannung A/B/C | in V |
| Wirkleistung/Scheinleistung/Blindleistung Speicher Summe | in W / VA / var (Diagnose) |
| Leistungsfaktor Speicher Summe | dimensionslos |
| Netzfrequenz (Speicher) | in Hz |
| Maximale Zelltemperatur | in °C |
| Speicher Zustand / Speicher Ereignis | Klartext (Diagnose) |
| PV-Leistung | in W – laut Doku nur mit Smartmeter ADW200 verfügbar (siehe Hinweis unten) |
| Leistungsvorgabe / Timeout / Steuermodus / Referenzwert Maximalleistung | Immediate-Controls-Werte, nur lesend (Diagnose) |
| Netz Stromsumme / -Strom L1/L2/L3 | in A |
| Netzspannung Durchschnitt (L-N) / L1/L2/L3 | in V |
| Netzfrequenz | in Hz |
| **Smart Meter Leistung** | Aus Register 40072 ("Summenwirkleistung Netz") – ersetzt das defekte Basic-Mode-Register 48 |
| Netzleistung L1/L2/L3 | in W |
| Scheinleistung/Blindleistung/Leistungsfaktor Netz Summe | in VA / var / dimensionslos |
| Speicherkapazität / Verfügbare Lade-/Entladeleistung | in Wh / W (Diagnose) |
| Maximaler/Minimaler SoC / Akku SoC (SunSpec) / Entladetiefe | in % (Diagnose) |
| Ladestatus Akku / Akku Ereignis | Klartext (Diagnose) |
| Durchschnittliche Zellspannung | in mV (Diagnose) |

**Hinweis Einheit "var":** Blindleistung (reaktive Leistung) wird
physikalisch korrekt in **var** (Volt-Ampere reaktiv) angegeben, nicht in
Watt – analog zu Scheinleistung in VA. Das ist keine falsche Einheit,
sondern dieselbe Konvention wie bei jedem anderen Energiemessgerät (W nur
für Wirkleistung, VA für Scheinleistung, var für Blindleistung).

**Hinweis ADL400 vs. ADW200:** `modbus.pdf` dokumentiert, dass PV-Leistung
und das komplette Meter-Modell 203 nur mit dem Smartmeter ADW200 verfügbar
seien. Auf einem mit **ADL400** verifizierten Gerät waren die
Netz-Register (Ströme, Spannungen, Leistungen) dennoch plausibel befüllt –
nur PV-Leistung war durchgehend 0. Falls dein Speicher ein anderes
Smartmeter nutzt, können einzelne Werte abweichen oder 0 bleiben.

Ist der SunSpec-Modus nicht erreichbar (siehe Abschnitt "Bekannte Lücken"),
zeigen alle Sensoren aus dieser Tabelle "unbekannt"; die Basic-Mode-Sensoren
bleiben davon unberührt.

### Zahlenfelder (`number.py`)

| Entität | Register | Beschreibung |
| --- | --- | --- |
| Maximaler Lade-SOC | – (Software-Logik) | Ziel-SOC (0–100 %), ab dem die Ladung gestoppt wird |
| Ladeleistungsgrenzwert | Register 44 | Direkt schreibbares Leistungslimit für die Ladung (W) |
| Entladeleistungsgrenzwert | Register 43 | Direkt schreibbares Leistungslimit für die Entladung (W) |
| Ziel-SOC (Zeitfenster) | – (Software-Logik) | Für zeitgesteuertes Laden, siehe Abschnitt unten |
| Ladeleistung (Zeitfenster) | – (Software-Logik) | Für zeitgesteuertes Laden, siehe Abschnitt unten |

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
| Zeitgesteuertes Laden | – (Software-Logik) | Aktiviert/deaktiviert das zeitgesteuerte Laden, siehe unten |

### Zeitgesteuertes Laden

Lädt den Speicher innerhalb eines konfigurierbaren Zeitfensters aktiv auf
einen Ziel-SOC – unabhängig von PV-Überschuss, z. B. für günstige
Nachtstromtarife ("Lade auf 90 %, wenn es zwischen 1 und 5 Uhr ist"). Reine
Software-Logik (kein natives Geräteregister), umgesetzt in
`SaxPowerCoordinator._async_enforce_timed_charge` (`coordinator.py`) und
bei jedem Poll-Zyklus neu ausgewertet.

**Neue Entitäten** (unter "Steuerung" am Gerät):

| Entität | Plattform | Beschreibung |
| --- | --- | --- |
| Zeitgesteuertes Laden | `switch.py` | Ein-/Ausschalten des Features |
| Ziel-SOC (Zeitfenster) | `number.py` | Ziel-Ladezustand in % (0–100) |
| Ladeleistung (Zeitfenster) | `number.py` | Leistung, mit der geladen wird, in W |
| Beginn Zeitfenster | `time.py` | Startzeit (HH:MM) |
| Ende Zeitfenster | `time.py` | Endzeit (HH:MM) |
| Zeitgesteuertes Laden aktiv | `sensor.py` (Diagnose) | Zeigt, ob gerade aktiv nachgeladen wird |

**Funktionsweise:** Ist das Feature aktiviert, die aktuelle Uhrzeit
innerhalb des Zeitfensters und der SOC unter dem Ziel-SOC, schreibt der
Coordinator einen negativen P-Sollwert (Ladeleistung) auf Register 41 –
technisch derselbe Mechanismus wie der `start_grid_charge`-Service
(periodischer Write alle 30s, siehe unten). Wird der Ziel-SOC erreicht,
das Zeitfenster verlassen oder das Feature deaktiviert, stoppt der
periodische Write automatisch wieder.

Das Zeitfenster darf über Mitternacht laufen (z. B. Start 23:00, Ende
05:00). Ist Start = Ende (oder eines von beiden nicht gesetzt), gilt das
Fenster als leer statt als "ganztägig" – es wird dann nie geladen.

Alle fünf Werte werden über Neustarts hinweg persistiert
(`RestoreEntity`), damit ein einmal eingerichteter Zeitplan nicht bei
jedem Home-Assistant-Neustart neu gesetzt werden muss.

**Wichtig:** Zeitgesteuertes Laden und der manuelle
`start_grid_charge`/`stop_grid_charge`-Service (siehe unten) teilen sich
denselben Hintergrund-Task. Werden beide gleichzeitig verwendet, gewinnt
der zuletzt schreibende Aufruf – es gibt keine eigene Arbitrierung
zwischen den beiden.

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
│                          SunSpec-Skalierung, Max-SOC-Logik, Netzladung,
│                          zeitgesteuertes Laden
├── entity.py             Basisklasse mit gemeinsamer DeviceInfo
├── __init__.py            Setup/Teardown des Config Entry, Service-Registrierung
├── sensor.py              ~56 Sensoren, beschreibungsbasiert (eine Klasse, eine Liste)
├── number.py              Max-SOC, Lade-/Entladeleistungsgrenzwert, Zeitfenster-Ziel-SOC/-Leistung
├── switch.py              Speicher ein/aus, zeitgesteuertes Laden ein/aus
├── time.py                Zeitfenster-Start/-Ende für zeitgesteuertes Laden
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
zusammenhängende Register-Blöcke auf zwei unterschiedlichen Slave-IDs mit je
einem `read_holding_registers`-Aufruf: Basic Mode (Slave-ID 64, Register
41–46, `READ_BLOCK_START`/`READ_BLOCK_COUNT`, Adress-Offset `-40001`) und
SunSpec-Modus (Slave-ID 100, Register 40000–40114, `READ_BLOCK_EXT_START`/
`READ_BLOCK_EXT_COUNT`, Adress-Offset `-40000` – **anderer Offset als Basic
Mode!**, siehe `modbus_llm.yaml`). Innerhalb eines Blocks gilt "alles oder
nichts": Schlägt der Basic-Mode-Read fehl, schlägt das gesamte Update fehl
(`UpdateFailed`), da Basic Mode die Mindestanforderung für jede Funktion der
Integration ist. Schlägt dagegen nur der SunSpec-Modus-Read fehl (z. B. weil
Slave-ID 100 auf dem SAX-Gateway nicht erreichbar ist oder die Firmware zu
alt ist, siehe `modbus.pdf` "Verfügbarkeit"), bleiben die Basic-Mode-Sensoren
unverändert verfügbar und lediglich die SunSpec-Sensoren zeigen "unbekannt",
bis der Block wieder lesbar ist (`SaxPowerCoordinator._async_read_extended`,
siehe anforderung.yaml `REQ-EXTENDED-MODE-RESILIENCE`). Ein dauerhafter
Ausfall wird zusätzlich als Home-Assistant-Repair-Issue angezeigt. Die genaue
Zuordnung Protokolladresse ↔ interne Adresse ↔ Bedeutung steht in
`modbus_llm.yaml`; `const.py` referenziert nur die intern verwendeten
Adressen.

**SunSpec-Skalierung:** `coordinator.apply_sunssf(raw_value,
raw_scale_factor)` wendet `Wert × 10^sunssf` an (beide Rohwerte signed
16-Bit). `SaxPowerCoordinator._parse_extended` wertet damit den kompletten
SunSpec-Modus-Block aus (Common/Inverter/Immediate Controls/Meter/Battery,
siehe `modbus.pdf`) und dekodiert zusätzlich die als ASCII-Zeichenpaare
codierten Hersteller-/Modell-Register (`coordinator.decode_ascii_registers`).

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
│                                  Parsing des kompletten SunSpec-Modus-Blocks (gemockt),
│                                  Zeitfenster-Logik + Enforcement für zeitgesteuertes Laden
├── test_config_flow.py            Unit-Tests: erfolgreicher Config Flow, "cannot_connect"-Fehler
│                                  (gemockter AsyncModbusTcpClient)
├── test_sensor_descriptions.py     Konsistenz-Tests über alle ~56 Sensor-Beschreibungen:
│                                  eindeutige Keys, vollständige DE/EN-Übersetzungen,
│                                  value_fn wirft für keinen Sensor eine Exception
├── test_integration_live.py        End-to-End-Tests gegen einen echten, lokal gestarteten
│                                  Modbus-TCP-Server (kein Mock) – prüft den kompletten Weg
│                                  Config Entry → Coordinator → Entities → echtes Wire-Protokoll,
│                                  inkl. Regressionstest für REQ-EXTENDED-MODE-RESILIENCE
│                                  (SunSpec-Modus nicht erreichbar → Basic-Mode-Sensoren bleiben da)
│                                  sowie End-to-End-Test für zeitgesteuertes Laden
├── test_real_hardware.py           Optionaler Live-Hardware-Test gegen einen *echten* SAX
│                                  Speicher (siehe Abschnitt "Test gegen echte Hardware" unten)
└── real_device.yaml                Verbindungsdaten (IP etc.) für test_real_hardware.py
```

`test_coordinator.py`, `test_config_flow.py` und `test_sensor_descriptions.py`
mocken den `pymodbus`-Client bzw. arbeiten rein auf Python-Ebene und prüfen
die Programmlogik. `test_integration_live.py` geht einen Schritt weiter: Er
startet mit `pymodbus.server.ModbusTcpServer` einen echten Modbus-TCP-Server
auf `127.0.0.1` mit simulierten Geräten (Slave-ID 64 Basic Mode, Slave-ID 100
SunSpec-Modus), befüllt sie mit Registerwerten aus `modbus_llm.yaml` und lässt
die Integration real darüber kommunizieren. Geprüft werden u. a.:

- korrektes Lesen von SOC über echtes TCP
- Entlade-/Ladeleistung und Smart-Meter-Leistung aus dem SunSpec-Modus
  (Register 40029/40072) über echtes TCP
- SunSpec-Skalierung (z. B. Netzfrequenz, Zelltemperatur) über echtes TCP
- Speicher-Switch aus/an inkl. Rücklesen des geschriebenen Werts
- Max-SOC-Klemmung (SOC über Zielwert → Ladelimit-Register wird auf 0 geschrieben)
- Netzladung: periodischer Sollwert-Write auf Register 41, verifiziert über
  einen unabhängigen zweiten Modbus-Client
- Fehlt der SunSpec-Modus-Server (Slave-ID 100) komplett: Config Entry lädt
  trotzdem erfolgreich, Basic-Mode-Sensoren liefern echte Werte,
  SunSpec-Sensoren zeigen "unbekannt" statt die Integration am Start zu
  hindern

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
| `test_read_real_sunspec_mode_values` wird übersprungen, `test_read_real_basic_mode_values` läuft durch | Der SunSpec-Modus (Slave-ID 100) ist auf diesem Gerät nicht erreichbar – z. B. zu alte Firmware (siehe `modbus.pdf` "Verfügbarkeit": Master V61/Gateway V54 oder neuer nötig). Das Gerät antwortet dann entweder mit einer Modbus-Fehlerantwort oder mit Modbus-Exception-Code 11 "Gateway Target Device Failed to Respond", was pymodbus als `ModbusIOException` auswirft. | Erwartetes, dokumentiertes Verhalten (siehe `REQ-EXTENDED-MODE-RESILIENCE`) – kein Fehler, entspricht der Fehlerbehandlung im produktiven Coordinator. Falls der SunSpec-Modus erwartet wird: Firmware-Version beim Hersteller/Installateur klären. |
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
slave_id_extended: 100
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

- **Registerkarte korrigiert (`REQ-SUNSPEC-MODE-CORRECTION`)**: Eine frühere
  Version dokumentierte "Extended Mode" mit Slave-ID 40 und Adress-Offset
  `-40001`. Beides war nachweislich falsch – Slave-ID 40 existiert auf
  echter Hardware nicht (Modbus-Exception "Gateway Target Device Failed to
  Respond"). Anhand der offiziellen sax-power.net-Dokumentation
  (`modbus.pdf` im Repo-Root) sowie byte-genauer Verifikation gegen ein
  echtes Gerät wurde das korrigiert: die tatsächliche Schnittstelle heißt
  "SunSpec-Modus", liegt auf **Slave-ID 100** mit Offset `-40000` und
  enthält u. a. auch "Immediate Controls" (vorher fälschlich als eigene,
  "noch nicht verfügbare" Slave-ID 123 dokumentiert – tatsächlich eine
  SunSpec-Modell-Nummer innerhalb desselben Blocks, aktiv nutzbar).
- **Basic-Mode-Register 47/48 entfernt**: Lieferten im Live-Test gegen
  echte Hardware wiederholt physikalisch unplausible Werte (~16000W bei
  einem 4600W-Gerät im Leerlauf) – vermutlich ein Firmware-Bug. Entlade-/
  Ladeleistung sowie Smart-Meter-Leistung kommen seitdem aus dem
  SunSpec-Modus (Register 40029 bzw. 40072).
- **PV-Leistung/Meter-Modell 203 und ADW200 vs. ADL400**: `modbus.pdf`
  dokumentiert diese Register als nur mit dem Smartmeter ADW200 verfügbar.
  Mit einem ADL400 waren die Netz-Register in Tests dennoch plausibel
  befüllt, PV-Leistung blieb 0. Bei anderen Smartmeter-Modellen können
  einzelne Werte abweichen.
- **Vorzeichenkonvention** von Register 40029 (Wirkleistung Speicher Summe)
  und dem P-Sollwert-Register 41 ist herstellerseitig nicht dokumentiert.
  Die Integration geht davon aus: positiv = Entladung/Einspeisung. Bitte am
  realen Gerät verifizieren und ggf. in `coordinator.py`/`sensor.py` anpassen.
- **Max-SOC** ist kein natives Geräteregister, sondern eine Software-Logik:
  Beim Erreichen des Zielwerts wird das Ladelimit-Register (44) auf 0
  gesetzt und beim Unterschreiten wieder freigegeben. Der SunSpec-Modus
  liefert zwar native "Maximaler SoC"/"Minimaler SoC"-Register
  (40100/40101), diese sind laut `modbus.pdf` aber nur lesbar (`R`), nicht
  schreibbar – die Software-Logik bleibt daher der einzige Weg, ein
  Ladelimit durchzusetzen.
- **Netzladung-Service nutzt weiterhin Basic Mode**: `sax_power.start_grid_charge`
  schreibt unverändert einen absoluten Watt-Sollwert auf Register 41 (Slave
  64). Der SunSpec-Modus böte dafür offiziell einen prozentualen Weg
  ("Immediate Controls", Register 40049–40051) – die zugehörigen Werte sind
  bereits als Nur-Lese-Sensoren sichtbar, ein Wechsel des Schreibpfads
  wurde aber bewusst nicht vorgenommen (siehe `REQ-SUNSPEC-MODE-CORRECTION`
  in `anforderung.yaml`), da das Ändern eines aktiven Schreibpfads für ein
  Gerät, das reale Leistungsflüsse in ein Haus steuert, eine eigene,
  gezielte Abstimmung verdient.
- **Registerbenennung Smart-Meter-Wirkleistung** (Basic Mode,
  `modbus_llm.yaml`): historisch benannte die Doku dort drei
  Phasenwirkleistungs-Register als "L1"/"L12"/"L13" statt "L1"/"L2"/"L3" –
  betrifft nicht mehr aktiv gelesene Register, nur noch als Hinweis
  relevant, falls diese Register künftig wieder verwendet werden.
- **SunSpec-Modus ist optional** (`REQ-EXTENDED-MODE-RESILIENCE`): Ist
  Slave-ID 100 nicht erreichbar (z. B. zu alte Firmware, siehe
  `modbus.pdf` "Verfügbarkeit": Master V61/Gateway V54 oder neuer nötig),
  bleiben die Basic-Mode-Sensoren (SOC, Schalter, Leistungsgrenzwerte)
  trotzdem verfügbar; nur die SunSpec-Sensoren (inkl. Entlade-/Ladeleistung
  und Smart-Meter-Leistung) zeigen "unbekannt", bis der Block wieder lesbar
  ist. Vorher führte ein nicht erreichbarer Extended-Mode-Block dazu, dass
  die gesamte Integration mit `ConfigEntryNotReady` scheiterte und **gar
  keine** Entities angelegt wurden – das war die ursprüngliche Ursache für
  den Fehlerbericht "es werden keine Sensoren angeboten".

## Installation über HACS (empfohlen)

1. In Home Assistant: **HACS → Integrationen → ⋮ (oben rechts) → Benutzerdefinierte Repositories**
2. Repository-URL eintragen: `https://github.com/dr-dimitri/sax-ha`
   Kategorie: **Integration**
3. Auf **Hinzufügen** klicken, danach die Integration "SAX Power Home" in HACS suchen und installieren
4. Home Assistant neu starten
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → nach "SAX Power" suchen
6. IP-Adresse, Port (Standard 502), Slave-IDs (Standard 64 & 100) und Aktualisierungsintervall eingeben

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

Die Anforderungen stammen aus `anforderung.yaml`. Das Modbus-Register-Mapping
in `modbus_llm.yaml` ist für den Basic-Mode-Block (Slave-ID 64) sowie den
SunSpec-Modus-Block (Slave-ID 100) gegen `modbus.pdf` – die offizielle
sax-power.net-Dokumentation ("SAX Power Home/Home Plus Modbus-TCP
Dokumentation (SUNSPEC-Mode)") – sowie byte-genau gegen echte Hardware
verifiziert (siehe `anforderung.yaml`, `REQ-SUNSPEC-MODE-CORRECTION`).
