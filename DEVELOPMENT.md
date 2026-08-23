# Entwicklerdokumentation

Interna zur Implementierung der SAX-Power-Home-Integration. Für die
Benutzerdokumentation siehe [README.md](README.md). Für KI-Coding-Agenten
siehe [AGENTS.md](AGENTS.md) (Setup-/Test-/Lint-Befehle, Code-Stil,
Git-Workflow) sowie [anforderung.yaml](anforderung.yaml) (feature-bezogene
Ist-Zustand-Anforderungen je REQ-ID).

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
├── manifest.json      Metadaten, Requirements (pymodbus==3.15.0), Domain
├── const.py            Register-/Konfigurationskonstanten, Defaults
├── domain/              Reine, frameworkunabhängige Regeln: Register-Codecs,
│                          Zeitfenster und Wertevalidierung
├── application/         Use-Case-Policy für die Ladeprioritäten sowie der
│                          injizierbare Modbus-Client-Port
├── infrastructure/      Home-Assistant-Adapter für zustandsbasierte
│                          Repair-Issues
├── config_flow.py       GUI-Einrichtung (Verbindung + optionale
│                          Netzladung-Vorbelegung), Verbindungsvalidierung,
│                          Options Flow (preisoptimiertes Laden)
├── coordinator.py       DataUpdateCoordinator: Reads (Basic+SunSpec), Writes,
│                          SunSpec-Skalierung, Max-SOC-Logik, Netzladung,
│                          zeitgesteuertes Laden, netzdienliches Laden,
│                          preisoptimiertes Laden (Anwendung des Ladeplans),
│                          Zeitfenster-Überlappungsprüfung
├── price_optimizer.py    Preisoptimiertes Laden: Einlesen der Preisdaten aus
│                          einer beliebigen Preis-Sensor-Entity, Ladeplanung je
│                          Strategie, 60-Sekunden-Takt - ohne Modbus-Zugriff
├── entity.py             Basisklasse mit gemeinsamer DeviceInfo,
│                          _assign_ids() (unique_id + vom Gerätenamen
│                          unabhängige entity_id, siehe
│                          REQ-STABLE-DEVICE-IDENTITY),
│                          initial_config_value() (Config-Entry-Fallback)
├── __init__.py            Setup/Teardown des Config Entry, Service-Registrierung
├── sensor.py              ~60 Sensoren, beschreibungsbasiert (eine Klasse, eine Liste),
│                          plus zwei RestoreEntity-Energiezähler (energy_charged/
│                          energy_discharged) fürs Energy-Dashboard
├── number.py              Max. SOC (einzige SOC-Einstellung, auch Ziel-SOC für
│                          Zeitfenster- und preisoptimiertes Laden), Netzladung
│                          Min. SOC, Preisgrenze/Anzahl Stunden
│                          (preisoptimiertes Laden)
├── select.py              Strategie des preisoptimierten Ladens
├── switch.py              Speicher ein/aus, zeitgesteuertes Laden ein/aus,
│                          netzdienliches Laden ein/aus, preisoptimiertes Laden ein/aus
├── time.py                Zeitfenster-Start/-Ende für zeitgesteuertes und
│                          netzdienliches Laden
├── repairs.py             Bestätigungsdialog für den Konflikt zwischen Netzladung
│                          und preisoptimiertem Laden
├── diagnostics.py          Diagnose-Download (Geräteseite): Coordinator-Zustand
│                          + coordinator.data + Ladeplan, IP-Adresse redigiert
├── dashboard.py            Mitgeliefertes Lovelace-Dashboard (4 Tabs), optional in
│                          der Ersteinrichtung anlegbar, siehe anforderung.yaml
│                          REQ-BUNDLED-DASHBOARD
├── services.yaml           Service-Schema für die UI
└── translations/            DE/EN-Übersetzungen (strings.json ist die Vorlage)

tests/                Siehe Abschnitt "Tests"
.devcontainer/         VS Code DevContainer für lokale Entwicklung
```

Die Abhängigkeiten zeigen von den Home-Assistant-Entrypoints nach innen:
`sensor.py`/`number.py`/`switch.py`/`time.py` verwenden den Coordinator, der
die Use-Case-Policy aus `application/` orchestriert; diese Policy verwendet
nur die reinen Regeln aus `domain/`. Die Domain importiert weder Home
Assistant noch pymodbus. Der konkrete `AsyncModbusTcpClient` wird beim Setup
erzeugt und über den `application.ports.ModbusClient`-Port in den Coordinator
injiziert. Dadurch bleibt der Coordinator der einzige Besitzer aller
Modbus-I/O-Operationen, während die Entscheidungslogik isoliert testbar ist.

Die Ladeprioritäten in `application/charge_policy.py` sind bewusst reine
Berechnung. Hysterese-Zähler, asynchrone Zustandsübergänge, periodische
Sollwert-Writes und Fehlerabbildung verbleiben im Coordinator, weil sie den
laufenden Use Case und die physische Gerätekommunikation orchestrieren. Das
erhält die extern sichtbare Funktionalität und schafft zugleich eine klare
Naht für weitere schrittweise Extraktionen.

`config_flow.py` implementiert sowohl `async_step_user` (Ersteinrichtung) als
auch `async_step_reconfigure` (spätere Änderung, z. B. der IP-Adresse) über
eine gemeinsame Methode (`_async_step_connection`). Beide validieren die
Verbindung mit demselben Testread, bevor die Daten gespeichert werden. Nur
`async_step_user` verzweigt bei Erfolg zusätzlich in drei weitere, optionale
Schritte, bevor der Eintrag angelegt wird - `async_step_reconfigure`
überspringt sie alle: `async_step_grid_charge` (Vorbelegung für das
zeitgesteuerte Laden, siehe `STEP_GRID_CHARGE_SCHEMA`), `async_step_dashboard`
(Dashboard anlegen ja/nein, siehe `STEP_DASHBOARD_SCHEMA` und
REQ-BUNDLED-DASHBOARD) und zuletzt `async_step_finish` - eine reine
Zusammenfassungsseite ohne eigene Eingabefelder (Firmware, Seriennummer,
SunSpec-Erreichbarkeit, Anzahl angelegter Entities als
`description_placeholders`, per Testread über `_async_read_finish_summary`
ermittelt), siehe anforderung.yaml REQ-SETUP-FINISH-SUMMARY. Der Config Entry
wird erst hier angelegt.

Zusätzlich gibt es einen Options Flow (`SaxPowerOptionsFlow`) für das
preisoptimierte Laden. Dort stehen nur die Dinge, die sich nicht sinnvoll als
Entity abbilden lassen (Auswahl der Quell-Sensoren und deren Interpretation);
die im Alltag veränderlichen Stellgrößen sind echte Entities am SAX-Gerät.
Eine Änderung wendet `async_update_options` direkt auf den laufenden
Coordinator an (`coordinator.options` ersetzen + `price_planner.async_setup()`
erneut aufrufen, idempotent) - bewusst **kein** Config-Entry-Reload mehr: Ein
Reload hätte über `SaxPowerCoordinator.async_shutdown`/`async_stop_sun_charge`
ein gerade aktiv gehaltenes netzdienliches Laden (Register 40051 zurück auf
SmartMeter-Nullregelung) unterbrochen und einen kurzen, ungewollten
Ladevorgang ausgelöst, bis die neu erzeugte Instanz die
`PV_SURPLUS_HYSTERESIS_CYCLES`-Bestätigung erneut durchlaufen hätte -
ursprünglich gemeldeter Bug, siehe `anforderung.yaml`,
REQ-DYNAMIC-PRICE-CHARGE.

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

**Max-SOC-Sperre, zeitgesteuertes Laden, netzdienliches Laden &
preisoptimiertes Laden:** Kein natives Max-SOC-Register. Alle vier teilen
sich eine zentrale Auswertung (`SaxPowerCoordinator._async_enforce_grid_
charge`, bei jedem Poll-Zyklus sowie bei jeder Einstellungsänderung neu
ausgewertet) und denselben Hintergrund-Task (`SaxPowerCoordinator._async_
sun_charge_loop`), der über den SunSpec-Modus schreibt: erst Register 40051
(Steuermodus) auf Sollwertvorgabe, dann Register 40049 (Leistungsvorgabe %).
Reihenfolge/Priorität in `_async_enforce_grid_charge`:

1. **SOC ≥ "Max. SOC"** (`soc_reached`): Leistungsvorgabe wird auf 0 %
   gehalten - unabhängig davon, ob zeitgesteuertes oder netzdienliches Laden
   aktiviert ist (z. B. auch bei einem durch PV-Überschuss vollen Speicher).
   Verhindert dauerhaftes Volladen auf 100 % (Batterie-Lebensdauer); der
   Speicher entlädt sich währenddessen nicht automatisch zur
   Eigenverbrauchsdeckung.
2. **Sonst, falls zeitgesteuertes Laden aktiviert + im Zeitfenster + im
   aktiven Monat + kein PV-Überschuss** (`timed_should_charge`):
   Leistungsvorgabe = `MIN_SETPOINT_POWER` (sättigt in
   `_watts_to_ic_setpoint_raw` auf -100 %, maximal mögliche Ladeleistung -
   eine frühere, konfigurierbare "Max. Netzladeleistung" wurde entfernt,
   weil der eingestellte Watt-Wert in der Praxis keinen Einfluss auf die
   tatsächliche Ladeleistung hatte).
3. **Sonst, falls netzdienliches Laden aktiviert + im eigenen Zeitfenster +
   im eigenen aktiven Monat + nicht bereits durch zeitgesteuertes Laden
   beansprucht** (`grid_serving_eligible`): eigene Zustandsmaschine
   (`SaxPowerCoordinator._async_step_grid_serving`), NICHT über einen aus
   dem PV-Überschuss berechneten Sollwert - es wird nie ein Sollwert > 0
   geschrieben:
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
     fehlt der Messwert), bleibt die Ladung bewusst bei 0 % gehalten - und
     zwar selbstheilend: sowohl im Wartezyklen- als auch im Halte-Zweig ruft
     die Methode zusätzlich `async_start_sun_charge(0)` erneut auf (No-Op bei
     unverändertem, weiterhin laufendem Task), damit ein unerwartet
     gestorbener Schreib-Task (z. B. nach einem einzelnen transienten
     Modbus-Fehler) noch im selben Zyklus neu gestartet wird - siehe
     `anforderung.yaml`, REQ-GRID-SERVING-CHARGE, für den ursprünglich
     gemeldeten Bug ohne diese Selbstheilung.

   Schließt sich mit Schritt 2 bereits strukturell über
   `not timed_should_charge` aus.
4. **Sonst, falls preisoptimiertes Laden aktiviert + Ladeplan meldet
   ausgewähltes Preisfenster** (`price_should_charge`, siehe
   `price_optimizer.py`): Leistungsvorgabe = `MIN_SETPOINT_POWER`, gleicher
   Schreibpfad wie Schritt 2. `price_should_charge` schließt zusätzlich
   `grid_serving_window_active` aus - **netzdienliches Laden hat also
   Vorrang vor preisoptimiertem Laden, nicht umgekehrt** (Regression, die
   behoben wurde: vorher blockierte preisoptimiertes Laden stattdessen
   netzdienliches Laden, was dazu führte, dass sich beide Automatiken
   gegenseitig ein- und ausschalten konnten, sobald ihre Bedingungen
   gleichzeitig erfüllt waren). Dieselbe Ausschlussregel gilt für die
   Neutralpreis-Pausezone (`price_should_pause`, Sollwert 0 statt
   Nullregelung zwischen Preisgrenze und Neutralpreis).
5. **Sonst**: Task wird gestoppt, Register 40051 zurück auf 0
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
`_sun_ic_write_interval`, gedeckelt auf 30s), da das Gerät den Sollwert
sonst verwirft. Beim Stoppen wird Register 40051 aktiv auf 0 zurückgesetzt
statt nur passiv auf den Timeout zu warten (siehe
`SaxPowerCoordinator.async_stop_sun_charge`) - dabei werden sowohl
`asyncio.CancelledError` als auch `HomeAssistantError` beim Awaiten des
abgebrochenen Tasks abgefangen, da pymodbus eine Cancellation, die einen
laufenden Write trifft, als `ModbusIOException` (und damit als
`HomeAssistantError`) statt als reine `CancelledError` durchreicht.

Der ältere Basic-Mode-P-Sollwert-Pfad (Register 41,
`_async_grid_charge_loop`, alle 30s fest) bleibt ausschließlich für den
manuellen `start_grid_charge`/`stop_grid_charge`-Service in Verwendung; die
Integration liest/schreibt die Basic-Mode-Register 43/44 (Ent-/Ladeleistungs-
grenzwert) nicht mehr - eine frühere Software-Einstellung "Max.
Netzladeleistung" (`SaxPowerChargeLimitNumber`), die Register 44 einmalig
als Vorgabewert gelesen hat, wurde entfernt (siehe unten).

**"Max. SOC"** (`SaxPowerMaxSocNumber`, `RestoreEntity`) setzt sich bei
fehlendem Vorzustand (z. B. direkt nach der Ersteinrichtung) explizit auf
`MAX_SOC` (100) statt "unbekannt"/0 zu bleiben.

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

Der Coordinator liest drei Register-Teilblöcke mit jeweils eigenem
Aktualisierungsintervall (siehe anforderung.yaml,
REQ-LOW-INTERVAL-REGISTERS/REQ-HIGH-INTERVAL-REGISTERS):

- **NORMAL** (`READ_BLOCK_START`/`READ_BLOCK_COUNT`, Slave-ID 64, Register
  41–46, Adress-Offset `-40001`): Basic Mode – SOC, Schaltzustand,
  P-/cos(phi)-Sollwert. Folgt dem über das Config-Flow-Feld
  "Aktualisierungsintervall" einstellbaren `scan_interval`
  (`CONF_SCAN_INTERVAL`/`DEFAULT_SCAN_INTERVAL`, Default 10s, min. 5s,
  max. 3600s).
- **HIGH** (`READ_BLOCK_EXT_START`/`READ_BLOCK_EXT_COUNT`, Slave-ID 100,
  Register 40017–40109, 93 Register, Adress-Offset `-40000`): SunSpec-Modus
  – dynamische Mess-/Zustandswerte (Ströme, Spannungen, Leistungen,
  Battery-SOC, Fehlercodes, Smart-Meter-Leistung). Fest
  `READ_BLOCK_EXT_HIGH_INTERVAL` (2s), unabhängig vom NORMAL-Intervall –
  u. a. relevant für eine zügige Reaktion des netzdienlichen Ladens auf
  die tatsächliche Ladeleistung (`storage_power_active`,
  `smartmeter_power`, siehe REQ-GRID-SERVING-CHARGE).
- **LOW1**/**LOW2** (`READ_BLOCK_EXT_LOW1_START`/`READ_BLOCK_EXT_LOW1_COUNT`,
  Register 40000–40016, 17 Register – bzw.
  `READ_BLOCK_EXT_LOW2_START`/`READ_BLOCK_EXT_LOW2_COUNT`, Register
  40110–40114, 5 Register): SunSpec Common Model + Modellkopf "3Ph
  Inverter" (Hersteller, Gerätemodell, Firmware-Version, Seriennummer)
  bzw. Battery-Skalierungsfaktoren. Fest `READ_BLOCK_EXT_LOW_INTERVAL`
  (1 Stunde), da laut `modbus_llm.yaml` ausschließlich "wellknown" fixe
  bzw. sich im laufenden Betrieb praktisch nie ändernde Werte.

Der interne Coordinator-Timer (`update_interval`, `SaxPowerCoordinator.
__init__`) läuft mit `min(scan_interval, READ_BLOCK_EXT_HIGH_INTERVAL)` –
da das config_flow-Minimum für `scan_interval` (5s) immer über
`READ_BLOCK_EXT_HIGH_INTERVAL` (2s) liegt, ist das faktisch immer 2s.
`SaxPowerCoordinator._async_read_basic` (NORMAL), `_async_read_high_block`
(HIGH) und `_async_read_low_block` (LOW1/LOW2) prüfen bei jedem Tick
jeweils eigenständig per Zeitstempel-Cache, ob ihr Teilblock tatsächlich
fällig ist, und liefern sonst den zuletzt gelesenen Wert zurück – nur ein
fälliger Teilblock löst einen echten `read_holding_registers`-Aufruf aus.
Ein Schreibzugriff auf ein Basic-Mode-Register
(`SaxPowerCoordinator.async_write_register`) invalidiert den NORMAL-Cache
explizit, damit ein direkt danach ausgelöster `coordinator.async_refresh()`
(siehe Storage-On/Off-Schalter, Abschnitt "Refresh-Verhalten" unten) nicht
kurzzeitig noch den alten, gecachten Wert liefert.

Für den HIGH-Block gilt "alles oder nichts": Scheitert ein fälliger
NORMAL-Read, schlägt das gesamte Update fehl (`UpdateFailed`), da Basic
Mode die Mindestanforderung für jede Funktion der Integration ist.
Scheitert dagegen ein fälliger HIGH-Read (z. B. weil Slave-ID 100 auf dem
SAX-Gateway nicht erreichbar ist oder die Firmware zu alt ist), bleiben die
Basic-Mode-Sensoren unverändert verfügbar und lediglich die
SunSpec-HIGH-Sensoren zeigen "unbekannt", bis der Block wieder lesbar ist
(`SaxPowerCoordinator._async_read_high_block`). Ein LOW-Read-Fehler lässt
das Update ebenfalls nicht fehlschlagen – die betroffenen
Diagnose-Sensoren behalten ihren letzten Wert. Ein dauerhafter
HIGH-Ausfall wird zusätzlich als Home-Assistant-Repair-Issue angezeigt.

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
`SaxPowerCoordinator._parse_extended` wertet damit den HIGH-Block aus
(Inverter/Immediate Controls/Meter/Battery), `_parse_low_block` den LOW1-/
LOW2-Block (Common Model, Battery-Skalierungsfaktoren) - siehe
Register-Mapping oben. `_parse_low_block` dekodiert außerdem die als
ASCII-Zeichenpaare codierten Hersteller-/Modell-Register
(`coordinator.decode_ascii_registers`).

## Refresh-Verhalten

Nutzerausgelöste Schreibaktionen (Switch, Number) rufen nach dem Schreiben
`coordinator.async_refresh()` auf – das ist die *ungedebouncte*
Coordinator-Methode. `async_request_refresh()` (debounced) wird bewusst
vermieden, da bei schnell aufeinanderfolgenden Aktionen sonst ein
verzögerter/verworfener Refresh dazu führen kann, dass die UI kurzzeitig
einen veralteten Wert zeigt.

Der einzige Fall, in dem eine Entity direkt nach einem Write auf einen per
`async_refresh()` sofort aktualisierten Zustand angewiesen ist, ist der
Storage-On/Off-Schalter (Basic-Mode-Register 45). Da der NORMAL-Block seit
REQ-HIGH-INTERVAL-REGISTERS eigenständig gecacht wird (siehe
Register-Mapping oben), invalidiert `async_write_register` den NORMAL-Cache
explizit - ohne das würde der direkt danach ausgelöste `async_refresh()`
sonst innerhalb des `scan_interval`-Fensters den alten, gecachten Wert
liefern statt den soeben geschriebenen.

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
│                                  inkl. erlaubter Zeitfenster-Überlappung bei disjunkten Monaten)
├── test_config_flow.py            Unit-Tests: erfolgreicher vierstufiger Config Flow
│                                  (Verbindung, optionale Netzladung-/Dashboard-Vorbelegung
│                                  inkl. Defaults bei leeren Schritten, Abschlussseite mit
│                                  Firmware/Seriennummer/SunSpec-Status/Entity-Anzahl als
│                                  description_placeholders - auch bei nicht erreichbarem
│                                  SunSpec-Modus), "cannot_connect"-Fehler (gemockter
│                                  AsyncModbusTcpClient)
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
├── test_price_optimizer.py         Preisoptimiertes Laden: Einlesen der Attributformate
│                                  verbreiteter Strompreis-Integrationen, Planberechnung je
│                                  Strategie (inkl. Planungshorizont und PV-Prognose im
│                                  Smart-Modus), Schreibpfad und Abbruchgründe im Coordinator,
│                                  Vorrang des zeitgesteuerten Ladens sowie der
│                                  Bestätigungsdialog beim Konflikt der beiden netzladenden
│                                  Automatiken (repairs.py)
├── test_repairs.py                 Fünf Selbstdiagnose-Issues (coordinator.
│                                  _async_check_self_diagnostics): Auslösen nach Karenzzeit,
│                                  Idempotenz (kein erneutes Anlegen bei unverändertem
│                                  Problemzustand), Selbstheilung sobald die Ursache behoben
│                                  ist - siehe anforderung.yaml REQ-SELF-DIAGNOSIS-REPAIRS
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
