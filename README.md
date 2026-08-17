# SAX Power Home – Home Assistant Integration

Custom Component für die Anbindung eines **SAX Power Home (Plus)** Heimspeichers
an Home Assistant über die Modbus-TCP-Schnittstelle.

## Funktionsumfang

- Sensoren: Ladezustand (SOC) in %, Entladeleistung (W), Ladeleistung (W)
- Schalter: Speicher ein-/ausschalten
- Zahlenfelder: Maximaler Lade-SOC, Ladeleistungsgrenzwert, Entladeleistungsgrenzwert
- Services `sax_power.start_grid_charge` / `sax_power.stop_grid_charge` für die
  manuelle Netzladung (periodisches Schreiben des P-Sollwerts)
- GUI-Einrichtung über den Home Assistant Config Flow (keine YAML-Konfiguration nötig)
- Asynchrone Anbindung via `pymodbus`, zentraler `DataUpdateCoordinator`

### Bekannte Lücken / Annahmen

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

## Services

### `sax_power.start_grid_charge`

| Feld | Beschreibung |
| --- | --- |
| `device_id` | SAX Power Gerät |
| `power` | Sollwert in Watt (-32768 bis 32767) |

### `sax_power.stop_grid_charge`

| Feld | Beschreibung |
| --- | --- |
| `device_id` | SAX Power Gerät |

## Quellen

Die Anforderungen und das Modbus-Register-Mapping stammen aus
`anforderung.yaml` bzw. `modbus_llm.yaml` in diesem Repository.
