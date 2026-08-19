# Entwicklerdokumentation

Interna zur Implementierung der SAX-Power-Home-Integration. Für die
Benutzerdokumentation siehe [README.md](README.md).

## Inhaltsverzeichnis

- [Aufbau](#aufbau)
- [Datenfluss](#datenfluss)
- [Register-Mapping](#register-mapping)
- [SunSpec-Skalierung](#sunspec-skalierung)
- [Refresh-Verhalten](#refresh-verhalten)
- [Tests](#tests)
  - [Manuelle Testausführung](#manuelle-testausführung)
  - [Test gegen echte Hardware](#test-gegen-echte-hardware)
- [Lokale Entwicklung (DevContainer)](#lokale-entwicklung-devcontainer)
- [Quellen](#quellen)

## Aufbau

```
custom_components/sax_power/
├── manifest.json      Metadaten, Requirements (pymodbus>=3.10.0), Domain
├── const.py            Register-/Konfigurationskonstanten, Defaults
├── config_flow.py       GUI-Einrichtung, Verbindungsvalidierung
├── coordinator.py       DataUpdateCoordinator: Reads (Basic+SunSpec), Writes,
│                          SunSpec-Skalierung, Max-SOC-Logik, Netzladung,
│                          zeitgesteuertes Laden
├── entity.py             Basisklasse mit gemeinsamer DeviceInfo
├── __init__.py            Setup/Teardown des Config Entry, Service-Registrierung
├── sensor.py              ~56 Sensoren, beschreibungsbasiert (eine Klasse, eine Liste)
├── number.py              Max. SOC (auch Ziel-SOC für Zeitfenster), Max. Lade-/Entladeleistung
├── switch.py              Speicher ein/aus, zeitgesteuertes Laden ein/aus
├── time.py                Zeitfenster-Start/-Ende für zeitgesteuertes Laden
├── services.yaml           Service-Schema für die UI
└── translations/            DE/EN-Übersetzungen (strings.json ist die Vorlage)

tests/                Siehe Abschnitt "Tests"
.devcontainer/         VS Code DevContainer für lokale Entwicklung
```

`config_flow.py` implementiert sowohl `async_step_user` (Ersteinrichtung) als
auch `async_step_reconfigure` (spätere Änderung, z. B. der IP-Adresse) über
eine gemeinsame Methode (`_async_step_connection`). Beide validieren die
Verbindung mit demselben Testread, bevor die Daten gespeichert werden.

## Datenfluss

`config_flow.py` sammelt Host/Port/Slave-IDs/Intervall und validiert die
Verbindung mit einem Testlesen. `__init__.py` baut daraus einen
`AsyncModbusTcpClient` und einen `SaxPowerCoordinator` (`coordinator.py`),
lädt anschließend die Plattformen `sensor`, `number`, `switch` und `time`
und registriert die beiden Services. Jede Entität (`entity.py` als
Basisklasse) liest ihren Zustand ausschließlich aus `coordinator.data` und
schreibt Änderungen über `coordinator.async_write_register(...)` bzw.
`coordinator.async_write_extended_register(...)` (SunSpec-Modus, Slave-ID
`self.slave_id_extended`).

**Max. SOC:** Kein natives Geräteregister. Der
`DataUpdateCoordinator` vergleicht bei jedem Poll den aktuellen SOC
(Register 46) mit dem gesetzten Zielwert: wird er erreicht/überschritten,
schreibt der Coordinator `0` in das Ladelimit-Register (44) und merkt sich
den zuvor gelesenen Wert; sinkt der SOC wieder darunter, wird der
ursprüngliche Wert zurückgeschrieben. Siehe
`SaxPowerCoordinator._async_enforce_max_soc`.

**Zeitgesteuertes Laden:** Reine Software-Logik, umgesetzt in
`SaxPowerCoordinator._async_enforce_timed_charge`, bei jedem Poll-Zyklus
sowie bei jeder Einstellungsänderung neu ausgewertet. Nutzt einen
Hintergrund-Task (`SaxPowerCoordinator._async_sun_charge_loop`), der über
den SunSpec-Modus schreibt: erst Register 40051 (Steuermodus) auf
Sollwertvorgabe, dann Register 40049 (Leistungsvorgabe %, aus "Max.
Ladeleistung" in Watt umgerechnet über `_watts_to_ic_setpoint_raw`). Das
Wiederholungsintervall (`_sun_ic_write_interval`) leitet sich aus dem vom
Gerät gemeldeten Timeout (Register 40050) ab, gedeckelt auf 30s. Beim
Stoppen wird Register 40051 aktiv auf 0 zurückgesetzt statt nur passiv auf
den Timeout zu warten (siehe `SaxPowerCoordinator.async_stop_sun_charge`).

Der ältere Basic-Mode-P-Sollwert-Pfad (Register 41,
`_async_grid_charge_loop`, alle 30s fest) bleibt ausschließlich für den
manuellen `start_grid_charge`/`stop_grid_charge`-Service in Verwendung.

## Register-Mapping

Der Coordinator liest pro Poll-Intervall zwei zusammenhängende
Register-Blöcke auf zwei unterschiedlichen Slave-IDs mit je einem
`read_holding_registers`-Aufruf: Basic Mode (Slave-ID 64, Register 41–46,
`READ_BLOCK_START`/`READ_BLOCK_COUNT`, Adress-Offset `-40001`) und
SunSpec-Modus (Slave-ID 100, Register 40000–40114,
`READ_BLOCK_EXT_START`/`READ_BLOCK_EXT_COUNT`, Adress-Offset `-40000` –
anderer Offset als Basic Mode).

Innerhalb eines Blocks gilt "alles oder nichts": Schlägt der
Basic-Mode-Read fehl, schlägt das gesamte Update fehl (`UpdateFailed`), da
Basic Mode die Mindestanforderung für jede Funktion der Integration ist.
Schlägt dagegen nur der SunSpec-Modus-Read fehl (z. B. weil Slave-ID 100 auf
dem SAX-Gateway nicht erreichbar ist oder die Firmware zu alt ist), bleiben
die Basic-Mode-Sensoren unverändert verfügbar und lediglich die
SunSpec-Sensoren zeigen "unbekannt", bis der Block wieder lesbar ist
(`SaxPowerCoordinator._async_read_extended`). Ein dauerhafter Ausfall wird
zusätzlich als Home-Assistant-Repair-Issue angezeigt.

Die genaue Zuordnung Protokolladresse ↔ interne Adresse ↔ Bedeutung steht in
`modbus_llm.yaml`; `const.py` referenziert nur die intern verwendeten
Adressen. Die vollständigen, aktuell gültigen Anforderungen an die
Integration stehen in `anforderung.yaml`.

Der P-Sollwert (Register 41) wird als vorzeichenbehafteter 16-Bit-Wert im
Zweierkomplement übertragen: positive Werte entsprechen Entladung (Watt
direkt als Ganzzahl), negative Werte (Laden) werden vor dem Schreiben als
`65536 + Sollwert` codiert (`coordinator.to_unsigned16`/`to_signed16`).

## SunSpec-Skalierung

`coordinator.apply_sunssf(raw_value, raw_scale_factor)` wendet
`Wert × 10^sunssf` an (beide Rohwerte signed 16-Bit).
`SaxPowerCoordinator._parse_extended` wertet damit den kompletten
SunSpec-Modus-Block aus (Common/Inverter/Immediate Controls/Meter/Battery)
und dekodiert zusätzlich die als ASCII-Zeichenpaare codierten
Hersteller-/Modell-Register (`coordinator.decode_ascii_registers`).

## Refresh-Verhalten

Nutzerausgelöste Schreibaktionen (Switch, Number) rufen nach dem Schreiben
`coordinator.async_refresh()` auf – das ist die *ungedebouncte*
Coordinator-Methode. `async_request_refresh()` (debounced) wird bewusst
vermieden, da bei schnell aufeinanderfolgenden Aktionen sonst ein
verzögerter/verworfener Refresh dazu führen kann, dass die UI kurzzeitig
einen veralteten Wert zeigt.

## Tests

```
tests/
├── conftest.py                  Aktiviert das Laden von custom_components in Tests
├── test_coordinator.py           Unit-Tests: signed/unsigned16-Konvertierung, apply_sunssf,
│                                  Max-SOC-Klemmung, Fehlerbehandlung bei Modbus-Schreibfehlern,
│                                  Parsing des kompletten SunSpec-Modus-Blocks (gemockt),
│                                  Zeitfenster-Logik + Enforcement für zeitgesteuertes Laden
│                                  (SunSpec-Modus-Register 40049/40051), Watt-zu-Prozent-
│                                  Umrechnung, Schreibintervall aus Register 40050
├── test_config_flow.py            Unit-Tests: erfolgreicher Config Flow, "cannot_connect"-Fehler
│                                  (gemockter AsyncModbusTcpClient)
├── test_sensor_descriptions.py     Konsistenz-Tests über alle ~56 Sensor-Beschreibungen:
│                                  eindeutige Keys, vollständige DE/EN-Übersetzungen,
│                                  value_fn wirft für keinen Sensor eine Exception
├── test_integration_live.py        End-to-End-Tests gegen einen echten, lokal gestarteten
│                                  Modbus-TCP-Server (kein Mock) – prüft den kompletten Weg
│                                  Config Entry → Coordinator → Entities → echtes Wire-Protokoll,
│                                  inkl. Regressionstest für den Resilienz-Fall (SunSpec-Modus
│                                  nicht erreichbar → Basic-Mode-Sensoren bleiben da) sowie
│                                  einen End-to-End-Test für zeitgesteuertes Laden
│                                  (SunSpec-Modus-Register 40049/40051)
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
| `test_read_real_sunspec_mode_values` wird übersprungen, `test_read_real_basic_mode_values` läuft durch | Der SunSpec-Modus (Slave-ID 100) ist auf diesem Gerät nicht erreichbar – z. B. zu alte Firmware (Master V61/Gateway V54 oder neuer nötig). Das Gerät antwortet dann entweder mit einer Modbus-Fehlerantwort oder mit Modbus-Exception-Code 11 "Gateway Target Device Failed to Respond", was pymodbus als `ModbusIOException` auswirft. | Erwartetes, dokumentiertes Verhalten – kein Fehler, entspricht der Fehlerbehandlung im produktiven Coordinator. Falls der SunSpec-Modus erwartet wird: Firmware-Version beim Hersteller/Installateur klären. |
| `ruff`/`black` melden Formatierungsfehler bei eigenen Änderungen | Code entspricht nicht dem Projektstil (Zeilenlänge 88, Formatierung). | `pip install ruff black` (falls nicht vorhanden), dann `black custom_components tests` zum automatischen Formatieren und `ruff check custom_components tests` zur Kontrolle. |
| Tests schlagen nach einem `git pull` plötzlich fehl | `requirements_test.txt` hat sich geändert (neue/aktualisierte Abhängigkeit), venv ist veraltet. | `source .venv/bin/activate && pip install -r requirements_test.txt` erneut ausführen. |

### Test gegen echte Hardware

`tests/test_real_hardware.py` liest – anders als `test_integration_live.py`
(simulierter Server) – Werte direkt von einem echten SAX Power Home (Plus)
im lokalen Netz. Rein lesend, kein Schreibzugriff.

Die Ziel-IP steht in `tests/real_device.yaml` (im Repository abgelegt):

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
verifiziert.
