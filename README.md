# SAX Power Home – Home Assistant Integration

Custom Component für die Anbindung eines **SAX Power Home (Plus)** Heimspeichers
an Home Assistant über die Modbus-TCP-Schnittstelle.

## Funktionen

### Sensoren (`sensor.py`)

| Entität | Quelle | Beschreibung |
| --- | --- | --- |
| Ladezustand | Register 46 | SOC des Speichers in % |
| Entladeleistung | Register 47 (positiver Anteil) | Leistung, die aktuell ins Hausnetz abgegeben wird, in W |
| Ladeleistung | Register 47 (negativer Anteil, invertiert) | Leistung, die aktuell in den Speicher geladen wird, in W |

Register 47 liefert einen einzelnen vorzeichenbehafteten Wert für Lade-/
Entladeleistung. Die Integration liest ihn einmal und leitet daraus zwei
Sensoren ab: ist der Wert positiv, wird er als Entladeleistung angezeigt
(Ladeleistung = 0), ist er negativ, als Ladeleistung (Entladeleistung = 0).

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

## Aufbau

```
custom_components/sax_power/
├── manifest.json      Metadaten, Requirements (pymodbus>=3.10.0), Domain
├── const.py            Register-/Konfigurationskonstanten, Defaults
├── config_flow.py       GUI-Einrichtung, Verbindungsvalidierung
├── coordinator.py       DataUpdateCoordinator: Reads, Writes, Max-SOC-Logik, Netzladung
├── entity.py             Basisklasse mit gemeinsamer DeviceInfo
├── __init__.py            Setup/Teardown des Config Entry, Service-Registrierung
├── sensor.py              SOC-, Entlade-, Ladeleistungs-Sensoren
├── number.py              Max-SOC, Lade-/Entladeleistungsgrenzwert
├── switch.py              Speicher ein/aus
├── services.yaml           Service-Schema für die UI
└── translations/            DE/EN-Übersetzungen (strings.json ist die Vorlage)

tests/                Siehe Abschnitt "Tests"
.devcontainer/         VS Code DevContainer für lokale Entwicklung
```

**Datenfluss:** `config_flow.py` sammelt Host/Port/Slave-IDs/Intervall und
validiert die Verbindung mit einem Testlesen. `__init__.py` baut daraus einen
`AsyncModbusTcpClient` und einen `SaxPowerCoordinator` (`coordinator.py`),
lädt anschließend die Plattformen `sensor`, `number`, `switch` und
registriert die beiden Services. Jede Entität (`entity.py` als Basisklasse)
liest ihren Zustand ausschließlich aus `coordinator.data` und schreibt
Änderungen über `coordinator.async_write_register(...)`.

**Register-Mapping:** Alle Basic-Mode-Register (Slave-ID 64) liegen
zusammenhängend im Bereich 41–48 (`READ_BLOCK_START`/`READ_BLOCK_COUNT` in
`const.py`), sodass der Coordinator sie mit einem einzigen
`read_holding_registers`-Aufruf pro Poll-Intervall abfragt. Die genaue
Zuordnung Protokolladresse ↔ interne Adresse ↔ Bedeutung steht in
`modbus_llm.yaml`; `const.py` referenziert nur die intern verwendeten
Adressen 41–48.

**Refresh-Verhalten:** Nutzerausgelöste Schreibaktionen (Switch, Number)
rufen nach dem Schreiben `coordinator.async_refresh()` auf – das ist die
*ungedebouncte* Coordinator-Methode. `async_request_refresh()` (debounced)
wird bewusst vermieden, da bei schnell aufeinanderfolgenden Aktionen sonst
ein verzögerter/verworfener Refresh dazu führen kann, dass die UI kurzzeitig
einen veralteten Wert zeigt.

## Tests

```
tests/
├── conftest.py             Aktiviert das Laden von custom_components in Tests
├── test_coordinator.py      Unit-Tests: signed/unsigned16-Konvertierung, Max-SOC-Klemmung,
│                             Fehlerbehandlung bei Modbus-Schreibfehlern (gemockter Client)
├── test_config_flow.py       Unit-Tests: erfolgreicher Config Flow, "cannot_connect"-Fehler
│                             (gemockter AsyncModbusTcpClient)
└── test_integration_live.py  End-to-End-Test gegen einen echten, lokal gestarteten
                              Modbus-TCP-Server (kein Mock) – prüft den kompletten Weg
                              Config Entry → Coordinator → Entities → echtes Wire-Protokoll
```

`test_coordinator.py` und `test_config_flow.py` mocken den `pymodbus`-Client
und prüfen die reine Programmlogik. `test_integration_live.py` geht einen
Schritt weiter: Er startet mit `pymodbus.server.ModbusTcpServer` einen
echten Modbus-TCP-Server auf `127.0.0.1`, befüllt ihn mit den Registerwerten
aus `modbus_llm.yaml` und lässt die Integration real darüber kommunizieren.
Geprüft werden u. a.:

- korrektes Lesen von SOC/Lade-/Entladeleistung über echtes TCP
- Speicher-Switch aus/an inkl. Rücklesen des geschriebenen Werts
- Max-SOC-Klemmung (SOC über Zielwert → Ladelimit-Register wird auf 0 geschrieben)
- Netzladung: periodischer Sollwert-Write auf Register 41, verifiziert über
  einen unabhängigen zweiten Modbus-Client

Dieser Live-Test hat einen echten Bug aufgedeckt (debounced Refresh, siehe
oben) – ein reiner Mock-Test hätte das nicht sichtbar gemacht, da er die
zeitliche Reihenfolge realer Schreibvorgänge nicht abbildet.

**Ausführen:**

```bash
pip install -r requirements_test.txt
pytest -v
```

Alle Tests laufen auch ohne echte Hardware und ohne Internetzugriff (der
Live-Test bindet nur an `127.0.0.1`).

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
