# AGENTS.md

Context file for AI coding agents (Claude Code, Codex, Cursor, ...) working
in this repository. Keep this file short and pointer-heavy: detailed,
feature-by-feature behavior specs live in [anforderung.yaml](anforderung.yaml)
(German, one `requirement_*` block per `REQ-*` id - see its index at the
top), and a narrative architecture walkthrough lives in
[DEVELOPMENT.md](DEVELOPMENT.md). Don't duplicate their content here; update
them instead when behavior changes.

## Project overview

`sax_power` is a Home Assistant custom integration (HACS) that talks Modbus
TCP to a SAX Power home battery storage system. It reads ~56 registers
(Basic Mode + optional SunSpec Mode) into sensors and exposes writable
limits/switches/time windows for charge control logic (timed charging to a
target SOC, grid-serving charging, a device-independent max-SOC lock).
We will create the best SAX Integration for Homeassistant ever. 
Always talk in german to the user
## Tech stack

- Python 3.14, `pymodbus==3.13.1` (`AsyncModbusTcpClient`), fully async I/O.
- Home Assistant custom component (`custom_components/sax_power/`):
  `DataUpdateCoordinator` + `SensorEntity`/`NumberEntity`/`SwitchEntity`/
  `TimeEntity` platforms, GUI-only `config_flow.py` (no YAML configuration).
- Tests: `pytest` + `pytest-homeassistant-custom-component`, `ruff`, `black`
  (line length 88, see `pyproject.toml`).

## Setup / test / lint commands

Outside the devcontainer, use the repo's `.venv`:

```
source .venv/bin/activate
pip install -r requirements_test.txt   # first time only
pytest -v                              # all tests
pytest tests/test_coordinator.py -v    # one file
pytest -k max_soc -v                   # filter by test name
pytest -rs                             # show skip reasons (e.g. real-hardware test)
ruff check custom_components scripts tests
black --check custom_components scripts tests
```

Inside `.devcontainer/` (see `devcontainer.json`), `homeassistant`, `pytest`,
`ruff`, `black` are already installed - run the same commands directly,
no venv activation needed. A local Home Assistant instance is available via
`hass -c config` (port 8123).

`tests/test_real_hardware.py` needs a real device (`tests/real_device.yaml`
with a `host` entry); it's skipped automatically otherwise - that's expected,
not a failure.

Every change must leave `pytest -v`, `ruff check`, and `black --check` clean
before it's considered done.

## Code style

- All I/O is async (`async`/`await`) - never block the event loop.
- One central `SaxPowerCoordinator` (`coordinator.py`) owns every Modbus
  read/write; entities only ever read `coordinator.data` and call
  `coordinator.async_write_register(...)` - no per-entity polling.
- Keep `domain/` framework-independent. Charging eligibility belongs in
  `application/charge_policy.py`; Home Assistant and pymodbus details stay at
  the outer boundary and reach the coordinator through application ports.
- Full type hints (PEP 484); code must stay Ruff/Black/PEP 8 clean.
- Validate register value ranges before every write (security: no
  unchecked writes to the device).
- Catch `ModbusException`/`asyncio.TimeoutError` and map to
  `UpdateFailed`/`ConfigEntryNotReady` - don't let them propagate raw.
- Comments explain *why* (non-obvious constraints, device quirks, prior
  incidents), never *what* - the code already says what. Point to the
  relevant `REQ-*` id in `anforderung.yaml` instead of re-explaining
  behavior inline.

## Architecture notes

- Register offsets: Basic Mode (slave id 64) = protocol address - 40001;
  SunSpec Mode (slave id 100) = protocol address - 40000 (different
  offset). SunSpec scale factors: `value * 10**sunssf`
  (`coordinator.apply_sunssf`).
- Full register mapping (protocol address ↔ internal address ↔ meaning),
  verified against the vendor's `modbus.pdf`: `modbus_llm.yaml`.
- Setpoint writes are repeated periodically while the mechanism is active,
  because the device drops a stale setpoint after its own timeout - see
  `anforderung.yaml`, REQ-TIMED-SOC-CHARGE / REQ-GRID-SERVING-CHARGE for the
  exact intervals.
- Folder layout: see [DEVELOPMENT.md](DEVELOPMENT.md#aufbau) for the full,
  narrated breakdown of `custom_components/sax_power/`.

## Git workflow

- Never commit directly to `main`. Every change goes on its own branch,
  opened as a pull request against `main`.
- Before creating a new branch, update `main` first (`git fetch && git pull
  origin main --ff-only`) so the new branch starts from the current state.
- Always create commits/branches/PRs.
- After the pull request change to the main branch and delete the local feature Branche
- Before every commit and pull request, inspect
  `.github/workflows/release.yaml`. Apply exactly one matching release label
  (`release:major`, `release:minor`, or `release:patch`) to every pull request;
  use `release:patch` for documentation-only changes.
- Set `custom_components/sax_power/manifest.json` in every pull request to the
  next stable version calculated from the latest stable SemVer tag and that
  one release label. Run `python scripts/release_metadata.py --labels-json
  '["release:patch"]'` (adjust the label) before committing; CI rejects a
  missing/ambiguous label, a mismatching manifest version, or an existing tag.
- Commit messages: German, imperative/descriptive summary line, focused on
  *why*; 
  when written by an agent (see recent `git log` for examples).

## Testing instructions

- `tests/test_coordinator.py` is the core suite (coordinator logic: reads,
  writes, timed/grid-serving charge state machines, window overlap, month
  handling). Most feature tests link back to their `REQ-*` id in
  `anforderung.yaml` in their docstring - when behavior changes, update
  both the test and the linked `anforderung.yaml` block together.
- `tests/test_integration_live.py` runs against a local, mocked Modbus TCP
  server (`127.0.0.1`), not real hardware - safe to run always.
- `tests/test_real_hardware.py` needs a real SAX device and is skipped
  without one (see Setup section above).
- `tests/test_config_flow.py`, `tests/test_number.py`,
  `tests/test_sensor_descriptions.py` cover their respective platforms.
- New behavior needs a test AND, if it changes what's described there, an
  `anforderung.yaml` update in the same change - they must not drift apart.

## Security considerations

- No secrets/credentials in this codebase (local Modbus TCP only, no cloud
  auth) - don't introduce any without asking first.
- Validate/clamp every value before writing it to a Modbus register
  (existing pattern: range checks + percentage clamping in `coordinator.py`).
- Treat the physical device as something that can be damaged by bad writes
  (e.g. a stuck non-zero setpoint) - prefer explicit, tested state
  transitions over "should be fine" assumptions when touching write paths.
