# Entwicklerdokumentation

Interna zur Implementierung der SAX-Power-Home-Integration. Für die
Benutzerdokumentation siehe [README.md](README.md).

## Inhaltsverzeichnis

- [Aufbau](#aufbau)
- [Datenfluss](#datenfluss)
- [Register-Mapping](#register-mapping)
- [SunSpec-Skalierung](#sunspec-skalierung)
- [Intervalltypen & Modbus-Lock](#intervalltypen--modbus-lock)
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
├── const.py            Register-/Konfigurationskonstanten, Defaults,
│                          IntervalType (HIGH/NORMAL/LOW)
├── intervals.py         Zuordnung periodischer Tasks zu Intervalltypen
│                          (TASK_INTERVALS), Auflösung in Sekunden
├── config_flow.py       GUI-Einrichtung (Verbindung + optionale
│                          Netzladung-Vorbelegung), Verbindungsvalidierung
├── coordinator.py       DataUpdateCoordinator: Reads (Basic+SunSpec), Writes,
│                          gemeinsamer Modbus-Lock für Reads+Writes,
│                          SunSpec-Skalierung, Max-SOC-Logik, Netzladung,
│                          zeitgesteuertes Laden, netzdienliches Laden,
│                          Zeitfenster-Überlappungsprüfung
├── entity.py             Basisklasse mit gemeinsamer DeviceInfo,
│                          initial_config_value() (Config-Entry-Fallback)
├── __init__.py            Setup/Teardown des Config Entry, Service-Registrierung
├── sensor.py              ~56 Sensoren, beschreibungsbasiert (eine Klasse, eine Liste)
├── number.py              Max. SOC (auch Ziel-SOC für Zeitfenster), Max. Netzladeleistung
├── switch.py              Speicher ein/aus, zeitgesteuertes Laden ein/aus,
│                          netzdienliches Laden ein/aus
├── time.py                Zeitfenster-Start/-Ende für zeitgesteuertes und
│                          netzdienliches Laden
├── services.yaml           Service-Schema für die UI
└── translations/            DE/EN-Übersetzungen (strings.json ist die Vorlage)

tests/                Siehe Abschnitt "Tests"
.devcontainer/         VS Code DevContainer für lokale Entwicklung
```

`config_flow.py` implementiert sowohl `async_step_user` (Ersteinrichtung) als
auch `async_step_reconfigure` (spätere Änderung, z. B. der IP-Adresse) über
eine gemeinsame Methode (`_async_step_connection`). Beide validieren die
Verbindung mit demselben Testread, bevor die Daten gespeichert werden. Nur
`async_step_user` verzweigt bei Erfolg zusätzlich in einen zweiten,
optionalen Schritt (`async_step_grid_charge`, siehe `STEP_GRID_CHARGE_SCHEMA`)
für die Vorbelegung des zeitgesteuerten Ladens, bevor der Eintrag angelegt
wird - `async_step_reconfigure` überspringt diesen Schritt.

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

**Max-SOC-Sperre, zeitgesteuertes Laden & netzdienliches Laden:** Kein
natives Max-SOC-Register. Alle drei teilen sich eine zentrale Auswertung
(`SaxPowerCoordinator._async_enforce_grid_charge`, bei jedem Poll-Zyklus
sowie bei jeder Einstellungsänderung neu ausgewertet) und denselben
Hintergrund-Task (`SaxPowerCoordinator._async_sun_charge_loop`), der über
den SunSpec-Modus schreibt: erst Register 40051 (Steuermodus) auf
Sollwertvorgabe, dann Register 40049 (Leistungsvorgabe %). Reihenfolge/
Priorität in `_async_enforce_grid_charge`:

1. **SOC ≥ "Max. SOC"** (`soc_reached`): Leistungsvorgabe wird auf 0 %
   gehalten - unabhängig davon, ob zeitgesteuertes oder netzdienliches Laden
   aktiviert ist (z. B. auch bei einem durch PV-Überschuss vollen Speicher).
   Verhindert dauerhaftes Volladen auf 100 % (Batterie-Lebensdauer); der
   Speicher entlädt sich währenddessen nicht automatisch zur
   Eigenverbrauchsdeckung.
2. **Sonst, falls zeitgesteuertes Laden aktiviert + im Zeitfenster + im
   aktiven Monat + kein PV-Überschuss + "Max. Netzladeleistung" gesetzt**
   (`timed_should_charge`): Leistungsvorgabe = `-max_charge_power` (negativ
   = Laden).
3. **Sonst, falls netzdienliches Laden aktiviert + im eigenen Zeitfenster +
   im eigenen aktiven Monat + nicht bereits durch zeitgesteuertes Laden
   beansprucht** (`grid_serving_eligible`): eigene Zustandsmaschine
   (`SaxPowerCoordinator._async_step_grid_serving`), NICHT über einen aus
   dem PV-Überschuss berechneten Sollwert. "Max. Netzladeleistung" wird
   dafür nicht benötigt, es wird nie ein Sollwert > 0 geschrieben:
   - **Schritt a** (ohne aktiven Sollwertvorgabemodus): Erreicht die
     tatsächliche Ladeleistung des SAX (negativer Anteil von
     `data["storage_power_active"]`) `SMARTMETER_PV_SURPLUS_THRESHOLD_WATT`
     (Beweis, dass die geräteeigene SmartMeter-Nullregelung bereits mit
     Überschuss lädt), wechselt der Speicher in einem Aufruf in den
     Sollwertvorgabemodus UND die Ladung wird auf 0 % gestoppt
     (`async_start_sun_charge(0)`), danach zwei Wartezyklen
     (`_grid_serving_wait_cycles`).
   - **Schritt b** (mit aktivem Sollwertvorgabemodus, nach Ablauf der
     Wartezyklen): Fällt die am Smart Meter gemessene Netzeinspeisung
     (`data["smartmeter_power"]`) unter denselben Schwellwert, wird der
     Speicher aktiv zurück in die SmartMeter-Nullregelung gesetzt
     (`async_stop_sun_charge`). Bleibt sie mindestens beim Schwellwert (oder
     fehlt der Messwert), bleibt die Ladung bewusst bei 0 % gehalten.

   Schließt sich mit Schritt 2 bereits strukturell über
   `not timed_should_charge` aus.
4. **Sonst**: Task wird gestoppt, Register 40051 zurück auf 0
   (SmartMeter-Nullregelung), Zustandsmaschine zurückgesetzt.

**Aktive Monate:** Beide Features haben zusätzlich je 12 Monats-Schalter
(`switch.SaxPowerMonthSwitch`, eine generische Klasse für beide Features und
alle 12 Monate, parametrisiert über `is_month_active`/`async_set_month_active`
-Callables), die in `SaxPowerCoordinator._timed_charge_months`/
`_grid_serving_months` (je ein `set[int]`, Default alle 12 Monate) verwaltet
werden. `_async_enforce_grid_charge` prüft zusätzlich `now.month in
self._timed_charge_months` bzw. `self._grid_serving_months`.

**Zeitfenster-Überlappung (Tageszeit UND Monat):**
`SaxPowerCoordinator._assert_windows_dont_overlap` (aufgerufen aus den vier
Zeit-Settern `async_set_timed_charge_start/-end`/`async_set_grid_serving_
start/-end` sowie den beiden Monats-Settern `async_set_timed_charge_month`/
`async_set_grid_serving_month`) lehnt eine Änderung, die zu einer
Überschneidung der beiden Zeitfenster führen würde, mit
`HomeAssistantError` ab - aber NUR, wenn sich sowohl die Tageszeiten
(`coordinator.windows_overlap`, modulweite Funktion, zerlegt beide Fenster
in Sekunden-Intervalle seit Mitternacht via `_window_intervals`, unterstützt
über Mitternacht laufende Fenster analog zu `_is_time_in_window`) ALS AUCH
die aktiven Monate (einfache Set-Schnittmenge) überschneiden. Die beiden
Monats-Setter akzeptieren zusätzlich `validate: bool = True` -
`SaxPowerMonthSwitch.async_added_to_hass` ruft sie beim Restaurieren mit
`validate=False` auf (vermeidet False-Positives durch sequentielles
Restaurieren mehrerer Monats-Entities, die beide bei "alle Monate"
starten), Live-Änderungen über den Schalter validieren immer.

Beide Register werden periodisch neu geschrieben (Intervall aus dem
geräteseitig gemeldeten Timeout, Register 40050, abgeleitet via
`_sun_ic_write_interval`, gedeckelt auf das über `TASK_WRITE_SUN_CHARGE`
aufgelöste Intervall - siehe Abschnitt "Intervalltypen & Modbus-Lock"),
da das Gerät den Sollwert sonst verwirft. Beim Stoppen wird Register 40051
aktiv auf 0 zurückgesetzt statt nur passiv auf den Timeout zu warten (siehe
`SaxPowerCoordinator.async_stop_sun_charge`) - dabei werden sowohl
`asyncio.CancelledError` als auch `HomeAssistantError` beim Awaiten des
abgebrochenen Tasks abgefangen, da pymodbus eine Cancellation, die einen
laufenden Write trifft, als `ModbusIOException` (und damit als
`HomeAssistantError`) statt als reine `CancelledError` durchreicht.

Der ältere Basic-Mode-P-Sollwert-Pfad (Register 41,
`_async_grid_charge_loop`, Intervall über `TASK_WRITE_GRID_CHARGE`
aufgelöst) bleibt ausschließlich für den manuellen
`start_grid_charge`/`stop_grid_charge`-Service in Verwendung; die
Integration schreibt die Basic-Mode-Register 43/44 (Ent-/Ladeleistungs-
grenzwert) nicht mehr.

**"Max. SOC" und "Max. Netzladeleistung"** (`SaxPowerMaxSocNumber`/
`SaxPowerChargeLimitNumber`, jeweils `RestoreEntity`) setzen sich bei
fehlendem Vorzustand (z. B. direkt nach der Ersteinrichtung) explizit auf
einen Vorgabewert statt "unbekannt"/0 zu bleiben: "Max. SOC" auf `MAX_SOC`
(100), "Max. Netzladeleistung" auf den beim Start einmalig gelesenen Wert
von Basic-Mode-Register 44 (`coordinator.data["charge_limit"]`, danach nur
noch Software-Zustand, kein weiterer Register-Write).

**Vorbelegung von Zeitfenster/Aktiviert-Status:** `SaxPowerTimedChargeSwitch`
sowie `SaxPowerTimedChargeStartTime`/`SaxPowerTimedChargeEndTime` (jeweils
`RestoreEntity`) fragen beim Start in dieser Reihenfolge: (1) hat der
Coordinator bereits einen Wert (z. B. durch eine andere Entity in dieser
Session)? (2) gibt es einen über RestoreEntity gespeicherten Vorzustand aus
einem früheren Lauf? (3) steht ein Wert aus dem zweiten
Ersteinrichtungs-Schritt im Config Entry (`entity.initial_config_value`)? (4)
sonst der Hard-Default aus `const.py`. Stufe 3 kommt dadurch effektiv nur
beim allerersten Start eines neuen Eintrags zum Tragen - sobald einmal ein
echter Zustand über RestoreEntity gespeichert wurde, hat der stets Vorrang,
auch nach einem späteren `Reconfigure` (der die Netzladung-Schlüssel nicht
im Config Entry aktualisiert).

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
Zweierkomplement übertragen: negative Werte (Laden) werden vor dem
Schreiben als `65536 + Sollwert` codiert
(`coordinator.to_unsigned16`/`to_signed16`). Positive Werte sollten laut
Encoding-Konvention Entladung bedeuten, haben gegen echte Hardware getestet
aber keine Wirkung gezeigt - siehe Kommentar bei `REG_SETPOINT_POWER`
(const.py) sowie anforderung.yaml REQ-MANUAL-DISCHARGE.

## SunSpec-Skalierung

`coordinator.apply_sunssf(raw_value, raw_scale_factor)` wendet
`Wert × 10^sunssf` an (beide Rohwerte signed 16-Bit).
`SaxPowerCoordinator._parse_extended` wertet damit den kompletten
SunSpec-Modus-Block aus (Common/Inverter/Immediate Controls/Meter/Battery)
und dekodiert zusätzlich die als ASCII-Zeichenpaare codierten
Hersteller-/Modell-Register (`coordinator.decode_ascii_registers`).

## Intervalltypen & Modbus-Lock

`intervals.py` ordnet jedem periodischen Lese-/Schreib-Task einen von drei
Intervalltypen (`const.IntervalType`) zu:

- **HIGH** – fest, 2 Sekunden. Für künftige dringende Tasks (z. B. ein
  Pilot-Modus-Zählerwert-Push) vorgesehen, aktuell keinem Task zugeordnet.
- **NORMAL** – bei der Einrichtung konfigurierbar (`CONF_SCAN_INTERVAL`,
  Default 10s). Bestimmt sowohl den Poll-Timer des Coordinators
  (`update_interval`, über `TASK_READ_BASIC` aufgelöst) als auch die Basis
  für die periodischen Schreib-Tasks.
- **LOW** – fest, 10 Minuten. Trägt den Task `TASK_READ_SLOW_DATA` (siehe
  `intervals.SLOW_DATA_KEYS`): Hersteller, Gerätemodell, Softwareversion
  Master/Gateway, Seriennummer, Referenzwert Maximalleistung,
  Speicherkapazität, Entladetiefe, Ladestatus Akku und Durchschnittliche
  Zellspannung – Werte, die sich praktisch nie/nur sehr selten ändern.

`TASK_INTERVALS` (`intervals.py`) ist die einzige Stelle, die einem Task
seinen Intervalltyp zuordnet. Ein Task fragt sein Intervall nie direkt aus
`TASK_INTERVALS`, sondern über `intervals.task_interval_seconds()` bzw.
`SaxPowerCoordinator._resolved_write_interval()` ab; eine Umstufung
erfordert deshalb nur eine Änderung der Zuordnung, keine Änderung am
Task-Code. `_resolved_write_interval()` deckelt das aufgelöste Intervall
zusätzlich auf `[SUN_IC_MIN_WRITE_INTERVAL, GRID_CHARGE_WRITE_INTERVAL]`
(Hersteller-Doku: "alle 5s bis 5min"), damit ein sehr klein oder sehr groß
konfiguriertes NORMAL-Intervall nicht zu einem für den Speicher unsicheren
Schreibrhythmus der beiden Netzladung-Pfade führt.

Die `TASK_READ_SLOW_DATA`-Felder liegen im selben zusammenhängenden
SunSpec-Modus-Block wie die schnell benötigten Werte (Register 4–14, 53,
97–109) und werden deshalb physisch weiterhin bei jedem NORMAL-Zyklus
mitgelesen – eine separate, selteneres Lesen dieser Register würde
zusätzliche Modbus-Anfragen erfordern. Stattdessen drosselt
`SaxPowerCoordinator._apply_slow_data_throttle` (aufgerufen aus
`_async_read_extended`) ausschließlich die *Übernahme* dieser Felder in
`coordinator.data` auf das LOW-Intervall: Der zuletzt übernommene Wert
bleibt zwischen zwei Übernahmen erhalten, selbst wenn der frisch gelesene
Rohwert bereits abweicht. Beim allerersten erfolgreichen SunSpec-Modus-Read
wird sofort der frisch gelesene Wert übernommen, damit die betroffenen
Sensoren nicht erst nach 10 Minuten einen Wert zeigen.

Sämtliche Zugriffe auf den gemeinsam genutzten `AsyncModbusTcpClient` -
Reads (`_async_update_data`, `_async_read_extended`) UND Writes
(`_async_write_register`) - laufen durch denselben
`SaxPowerCoordinator._modbus_lock` (`asyncio.Lock`). Ohne diesen Schutz auf
der Lese-Seite konnten ein periodischer Coordinator-Poll und ein paralleler
Hintergrund-Schreib-Task (Netzladung/SunSpec-Netzladung) gleichzeitig
Anfragen an den Speicher senden, was auf echter Hardware zu "Connection
Refused" führen kann.

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
│                                  Fehlerbehandlung bei Modbus-Schreibfehlern, Parsing des
│                                  kompletten SunSpec-Modus-Blocks (gemockt), Zeitfenster-Logik +
│                                  Enforcement für zeitgesteuertes Laden, netzdienliches Laden
│                                  und die Max-SOC-Sperre (alle über SunSpec-Modus-Register
│                                  40049/40051, auch unabhängig voneinander), Watt-zu-Prozent-
│                                  Umrechnung, Schreibintervall aus Register 40050,
│                                  Zeitfenster-Überlappungsprüfung (windows_overlap,
│                                  Ablehnung überlappender Änderungen), aktive Monate
│                                  (Enforcement, Default "alle Monate", Überlappungsprüfung
│                                  inkl. erlaubter Zeitfenster-Überlappung bei disjunkten Monaten),
│                                  Intervalltyp-Auflösung inkl. Deckelung bei sehr klein/groß
│                                  konfiguriertem scan_interval, Regressionstest für den
│                                  Modbus-Lock (gleichzeitiger Read/Write greift nie überlappend
│                                  auf den Client zu), Drosselverhalten der trägen SunSpec-Felder
│                                  (sofortige Übernahme beim ersten Read, unveränderter Wert vor
│                                  Ablauf des LOW-Intervalls, Übernahme nach Ablauf)
├── test_intervals.py               Unit-Tests für intervals.py: HIGH/LOW sind fest, NORMAL folgt
│                                  dem konfigurierten Intervall, unbekannte Tasks gelten als
│                                  NORMAL, NORMAL-/LOW-Zuordnung der vorhandenen Tasks,
│                                  SLOW_DATA_KEYS deckt genau die neun trägen Felder ab
├── test_config_flow.py            Unit-Tests: erfolgreicher zweistufiger Config Flow
│                                  (Verbindung + optionale Netzladung-Vorbelegung inkl.
│                                  Defaults bei leerem zweiten Schritt), "cannot_connect"-Fehler
│                                  (gemockter AsyncModbusTcpClient)
├── test_sensor_descriptions.py     Konsistenz-Tests über alle ~56 Sensor-Beschreibungen:
│                                  eindeutige Keys, vollständige DE/EN-Übersetzungen,
│                                  value_fn wirft für keinen Sensor eine Exception
├── test_integration_live.py        End-to-End-Tests gegen einen echten, lokal gestarteten
│                                  Modbus-TCP-Server (kein Mock) – prüft den kompletten Weg
│                                  Config Entry → Coordinator → Entities → echtes Wire-Protokoll,
│                                  inkl. Regressionstest für den Resilienz-Fall (SunSpec-Modus
│                                  nicht erreichbar → Basic-Mode-Sensoren bleiben da), einen
│                                  End-to-End-Test für zeitgesteuertes Laden (SunSpec-Modus-
│                                  Register 40049/40051) sowie Tests für die Vorbelegung aus
│                                  dem Config Entry beim allerersten Start (mit und ohne im
│                                  Entry hinterlegte Netzladung-Werte)
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
- Max-SOC-Sperre (SOC über Zielwert → Register 40051/40049 über den
  SunSpec-Modus geschrieben, unabhängig von zeitgesteuertem Laden)
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

> Frühere Versionen dieser Datei enthielten zusätzlich schreibende Live-
> Tests für eine "manuelle Entladung" (positiver Sollwert auf Register
> 40049 bzw. dem älteren Basic-Mode-Register 41). Damit wurde live
> nachgewiesen, dass beide Wege die Register zwar korrekt schreiben, der
> reale Speicher aber in keinem Fall tatsächlich entladen hat - der
> Hersteller hat auf Rückfrage bestätigt, dass eine ferngesteuerte manuelle
> Entladung nicht vorgesehen ist. Die Funktion (Entities, Coordinator-Logik,
> Tests) wurde deshalb wieder entfernt, siehe anforderung.yaml
> REQ-MANUAL-DISCHARGE sowie die Kommentare bei REG_SETPOINT_POWER/
> REG_SUN_IC_POWER_SETPOINT_PCT in const.py.

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
