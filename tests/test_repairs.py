"""Tests für die Selbstdiagnose-Prüfungen aus repairs.py/coordinator.py
(anforderung.yaml, REQ-SELF-DIAGNOSIS-REPAIRS).

Der Ladekonflikt-Bestätigungsdialog (repairs.ChargeConflictRepairFlow) wird
bereits in tests/test_price_optimizer.py abgedeckt - hier geht es nur um
die zusätzlichen, rein informativen (nicht fixierbaren)
Selbstdiagnose-Issues aus SaxPowerCoordinator._async_check_self_diagnostics.
Jede Prüfung wird auf drei Arten getestet: Auslösen (nach Ablauf der
jeweiligen Karenzzeit, sofern vorhanden), Idempotenz (kein wiederholtes
Anlegen bei unverändertem Problemzustand) und Selbstheilung (Issue
verschwindet automatisch, sobald die Ursache behoben ist)."""

from __future__ import annotations

from dataclasses import replace
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers import issue_registry as ir

from custom_components.sax_power.const import (
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_PRICE_SENSOR,
    DATA_COORDINATOR,
    DOMAIN,
    ISSUE_ECONOMICS_PRICE_UNAVAILABLE,
    ISSUE_EMPTY_CHARGE_WINDOW,
    ISSUE_MAX_SOC_BELOW_MIN_SOC,
    ISSUE_NO_ACTIVE_MONTHS,
    ISSUE_PRICE_CHARGE_CONFLICT,
    ISSUE_PRICE_NEUTRAL_BELOW_LIMIT,
    ISSUE_PRICE_SENSOR_MISSING,
    ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE,
    ISSUE_VUE_DASHBOARD_UPDATE,
    MAX_SOC,
    PRICE_SENSOR_MISSING_GRACE_PERIOD,
    PRICE_STATUS_NO_PRICE_DATA,
    PRICE_STATUS_WAITING,
    PRICE_STRATEGY_ABSOLUTE,
    PRICE_STRATEGY_OFF,
    PRICE_STRATEGY_RELATIVE,
    PRICE_STRATEGY_SMART,
    SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.infrastructure.self_diagnostics import (
    DiagnosticSnapshot,
    SelfDiagnostics,
)
from custom_components.sax_power.price_optimizer import PricePlan
from custom_components.sax_power.repairs import (
    ChargeConflictRepairFlow,
    VueDashboardRepairFlow,
    async_create_fix_flow,
)


def _make_client() -> MagicMock:
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    return client


def _make_coordinator(hass) -> SaxPowerCoordinator:
    coordinator = SaxPowerCoordinator(
        hass,
        _make_client(),
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="test_entry_id",
    )
    coordinator._timed_charge_min_soc = MAX_SOC
    return coordinator


def _get_issue(hass, key: str):
    return ir.async_get(hass).async_get_issue(DOMAIN, f"{key}_test_entry_id")


@pytest.mark.parametrize(
    ("issue_key", "changes"),
    [
        (
            ISSUE_PRICE_SENSOR_MISSING,
            {"price_status": PRICE_STATUS_NO_PRICE_DATA},
        ),
        (
            ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE,
            {"extended_available": False, "extended_unavailable_since": 0.0},
        ),
        (ISSUE_MAX_SOC_BELOW_MIN_SOC, {"timed_max_soc": 10}),
        (ISSUE_PRICE_NEUTRAL_BELOW_LIMIT, {"neutral_price": 0.1}),
        (
            f"{ISSUE_EMPTY_CHARGE_WINDOW}_timed_charge",
            {"timed_enabled": True, "timed_end": dt_time(1)},
        ),
        (
            f"{ISSUE_EMPTY_CHARGE_WINDOW}_grid_serving",
            {"grid_serving_enabled": True, "grid_serving_end": dt_time(1)},
        ),
        (
            f"{ISSUE_NO_ACTIVE_MONTHS}_timed_charge",
            {"timed_enabled": True, "timed_months": frozenset()},
        ),
        (
            f"{ISSUE_NO_ACTIVE_MONTHS}_grid_serving",
            {"grid_serving_enabled": True, "grid_serving_months": frozenset()},
        ),
        (
            ISSUE_ECONOMICS_PRICE_UNAVAILABLE,
            {"economics_price_unavailable": True},
        ),
    ],
)
@pytest.mark.parametrize("problem_persists_after_reload", [False, True])
async def test_self_diagnostic_issue_clears_after_reload(
    hass,
    issue_key: str,
    changes: dict[str, object],
    problem_persists_after_reload: bool,
) -> None:
    """REQ-SELF-DIAGNOSIS-REPAIRS/REQ-ECONOMICS-OBSERVABILITY: Reload heilt."""
    healthy = DiagnosticSnapshot(
        price_status=PRICE_STATUS_WAITING,
        price_entity_id="sensor.strompreis",
        extended_available=True,
        extended_unavailable_since=None,
        slave_id_extended=100,
        timed_max_soc=100,
        timed_min_soc=20,
        price_limit=0.2,
        neutral_price=0.3,
        price_strategy=PRICE_STRATEGY_ABSOLUTE,
        timed_enabled=True,
        timed_start=dt_time(1),
        timed_end=dt_time(5),
        timed_months=frozenset(range(1, 13)),
        grid_serving_enabled=True,
        grid_serving_start=dt_time(1),
        grid_serving_end=dt_time(5),
        grid_serving_months=frozenset(range(1, 13)),
        economics_tariff_enabled=True,
    )
    problem = replace(healthy, **changes)
    diagnostics = SelfDiagnostics(hass, "test_entry_id")
    diagnostics.check(problem, 0.0)
    after_grace = max(
        PRICE_SENSOR_MISSING_GRACE_PERIOD,
        SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD,
    )
    diagnostics.check(problem, after_grace)
    issue = _get_issue(hass, issue_key)
    assert issue is not None and issue.active

    reloaded = SelfDiagnostics(hass, "test_entry_id")
    if problem_persists_after_reload:
        reloaded.check(problem, after_grace + 1)
        assert _get_issue(hass, issue_key) is not None
    reloaded.check(healthy, after_grace + 2)

    assert _get_issue(hass, issue_key) is None


# ===========================================================================
# 1. Preis-Sensor liefert keine Daten
# ===========================================================================
async def test_price_sensor_missing_issue_after_grace_period(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.options = {CONF_PRICE_SENSOR: "sensor.strompreis"}
    coordinator.price_planner.plan = PricePlan(status=PRICE_STATUS_NO_PRICE_DATA)

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_PRICE_SENSOR_MISSING) is None

    with patch(
        "custom_components.sax_power.coordinator.monotonic",
        return_value=1000.0 + PRICE_SENSOR_MISSING_GRACE_PERIOD,
    ):
        coordinator._async_check_self_diagnostics()
    issue = _get_issue(hass, ISSUE_PRICE_SENSOR_MISSING)
    assert issue is not None
    assert issue.translation_placeholders == {"price_sensor": "sensor.strompreis"}


async def test_price_sensor_missing_issue_not_recreated_every_cycle(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.price_planner.plan = PricePlan(status=PRICE_STATUS_NO_PRICE_DATA)
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._async_check_self_diagnostics()

    with (
        patch(
            "custom_components.sax_power.coordinator.monotonic",
            return_value=1000.0 + PRICE_SENSOR_MISSING_GRACE_PERIOD,
        ),
        patch(
            "custom_components.sax_power.coordinator.ir.async_create_issue"
        ) as mock_create,
    ):
        coordinator._async_check_self_diagnostics()
        coordinator._async_check_self_diagnostics()
        coordinator._async_check_self_diagnostics()

    assert mock_create.call_count == 1


async def test_price_sensor_missing_issue_clears_once_data_returns(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.price_planner.plan = PricePlan(status=PRICE_STATUS_NO_PRICE_DATA)
    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._async_check_self_diagnostics()
    with patch(
        "custom_components.sax_power.coordinator.monotonic",
        return_value=1000.0 + PRICE_SENSOR_MISSING_GRACE_PERIOD,
    ):
        coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_PRICE_SENSOR_MISSING) is not None

    coordinator.price_planner.plan = PricePlan(status=PRICE_STATUS_WAITING)
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_PRICE_SENSOR_MISSING) is None


# ===========================================================================
# 2. SunSpec-Modus dauerhaft nicht erreichbar
# ===========================================================================
async def test_sunspec_persistently_unavailable_issue_after_grace_period(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._extended_available = False

    with patch(
        "custom_components.sax_power.coordinator.monotonic", return_value=1000.0
    ):
        coordinator._extended_unavailable_since = 1000.0
        coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE) is None

    with patch(
        "custom_components.sax_power.coordinator.monotonic",
        return_value=1000.0 + SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD,
    ):
        coordinator._async_check_self_diagnostics()
    issue = _get_issue(hass, ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE)
    assert issue is not None
    assert issue.translation_placeholders == {"slave_id": "100"}


async def test_sunspec_persistently_unavailable_issue_not_recreated_every_cycle(
    hass,
) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._extended_available = False
    coordinator._extended_unavailable_since = 1000.0

    with (
        patch(
            "custom_components.sax_power.coordinator.monotonic",
            return_value=1000.0 + SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD,
        ),
        patch(
            "custom_components.sax_power.coordinator.ir.async_create_issue"
        ) as mock_create,
    ):
        coordinator._async_check_self_diagnostics()
        coordinator._async_check_self_diagnostics()

    assert mock_create.call_count == 1


async def test_sunspec_persistently_unavailable_issue_clears_on_recovery(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._extended_available = False
    coordinator._extended_unavailable_since = 1000.0
    with patch(
        "custom_components.sax_power.coordinator.monotonic",
        return_value=1000.0 + SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD,
    ):
        coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE) is not None

    coordinator._extended_available = True
    coordinator._extended_unavailable_since = None
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE) is None


# ===========================================================================
# 3. Max-SOC unter Netzladung Min. SOC
# ===========================================================================
async def test_max_soc_below_min_soc_issue_triggers_immediately(hass) -> None:
    """Anders als die beiden Prüfungen oben ist das eine statische
    Einstellungskombination, kein transienter Zustand - kein
    Karenzzeit-Timer nötig."""
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._max_soc = 50
    coordinator._timed_charge_min_soc = 60

    coordinator._async_check_self_diagnostics()

    issue = _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC)
    assert issue is not None
    assert issue.translation_placeholders == {"max_soc": "50", "min_soc": "60"}


async def test_max_soc_below_min_soc_issue_not_recreated_every_cycle(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(1)
    coordinator._timed_charge_end = dt_time(5)
    coordinator._max_soc = 50
    coordinator._timed_charge_min_soc = 60

    with patch(
        "custom_components.sax_power.coordinator.ir.async_create_issue"
    ) as mock_create:
        coordinator._async_check_self_diagnostics()
        coordinator._async_check_self_diagnostics()

    assert mock_create.call_count == 1


async def test_max_soc_below_min_soc_issue_clears_once_raised(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._max_soc = 50
    coordinator._timed_charge_min_soc = 60
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC) is not None

    coordinator._max_soc = 80
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC) is None


async def test_timed_max_soc_below_min_soc_uses_own_target(hass) -> None:
    """REQ-TIMED-SOC-CHARGE: Ein hohes globales Limit verdeckt keinen Konflikt."""
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._max_soc = 90
    coordinator._timed_charge_max_soc = 30
    coordinator._timed_charge_min_soc = 40

    coordinator._async_check_self_diagnostics()

    issue = _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC)
    assert issue is not None
    assert issue.translation_placeholders == {"max_soc": "30", "min_soc": "40"}

    await coordinator.async_set_timed_charge_max_soc(60)
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC) is None


@pytest.mark.parametrize("global_max_soc", [15, 90])
async def test_disabled_timed_charge_has_no_soc_conflict_issue(
    hass, global_max_soc: int
) -> None:
    """REQ-SELF-DIAGNOSIS-REPAIRS: Ungenutzte SOC-Grenzen warnen nicht (#215)."""
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = False
    coordinator._max_soc = global_max_soc
    coordinator._timed_charge_max_soc = 50
    coordinator._timed_charge_min_soc = 60

    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC) is None


@pytest.mark.parametrize("reload_diagnostics", [False, True])
async def test_soc_conflict_issue_follows_timed_charge_enabled(
    hass, reload_diagnostics: bool
) -> None:
    """REQ-SELF-DIAGNOSIS-REPAIRS: Abschalten heilt auch bestehende Issues."""
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_max_soc = 50
    coordinator._timed_charge_min_soc = 60
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC) is not None

    if reload_diagnostics:
        coordinator._self_diagnostics = SelfDiagnostics(hass, "test_entry_id")
    coordinator._timed_charge_enabled = False
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC) is None

    coordinator._timed_charge_enabled = True
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC) is not None


# ===========================================================================
# 3b. Neutralpreis nicht über der Preisgrenze (REQ-DYNAMIC-PRICE-CHARGE)
# ===========================================================================
async def test_price_neutral_below_limit_issue_triggers_immediately(hass) -> None:
    """Statische Einstellungskombination wie Prüfung 3 - kein
    Karenzzeit-Timer nötig."""
    coordinator = _make_coordinator(hass)
    coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    coordinator._price_charge_max_price = 0.30
    coordinator._price_charge_neutral_price = 0.20

    coordinator._async_check_self_diagnostics()

    issue = _get_issue(hass, ISSUE_PRICE_NEUTRAL_BELOW_LIMIT)
    assert issue is not None
    assert issue.translation_placeholders == {
        "max_price": "0.3",
        "neutral_price": "0.2",
    }


async def test_price_neutral_below_limit_issue_triggers_on_equal_values(hass) -> None:
    """Gleichheit zählt ebenfalls als Problem - die Pause-Zone braucht ein
    echtes Preisband zwischen den beiden Werten."""
    coordinator = _make_coordinator(hass)
    coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    coordinator._price_charge_max_price = 0.30
    coordinator._price_charge_neutral_price = 0.30

    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_PRICE_NEUTRAL_BELOW_LIMIT) is not None


async def test_price_neutral_below_limit_issue_not_recreated_every_cycle(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    coordinator._price_charge_max_price = 0.30
    coordinator._price_charge_neutral_price = 0.20

    with patch(
        "custom_components.sax_power.coordinator.ir.async_create_issue"
    ) as mock_create:
        coordinator._async_check_self_diagnostics()
        coordinator._async_check_self_diagnostics()

    assert mock_create.call_count == 1


async def test_price_neutral_below_limit_issue_clears_once_raised(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    coordinator._price_charge_max_price = 0.30
    coordinator._price_charge_neutral_price = 0.20
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_PRICE_NEUTRAL_BELOW_LIMIT) is not None

    coordinator._price_charge_neutral_price = 0.40
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_PRICE_NEUTRAL_BELOW_LIMIT) is None


@pytest.mark.parametrize(
    "strategy", [PRICE_STRATEGY_RELATIVE, PRICE_STRATEGY_SMART, PRICE_STRATEGY_OFF]
)
async def test_neutral_price_issue_clears_when_leaving_absolute_strategy(
    hass, strategy: str
) -> None:
    """REQ-DYNAMIC-PRICE-CHARGE: Die Preisgrenze begrenzt nur Absoluter Preis."""
    coordinator = _make_coordinator(hass)
    coordinator._price_charge_strategy = PRICE_STRATEGY_ABSOLUTE
    coordinator._price_charge_max_price = 0.30
    coordinator._price_charge_neutral_price = 0.20
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_PRICE_NEUTRAL_BELOW_LIMIT) is not None

    coordinator._self_diagnostics = SelfDiagnostics(hass, "test_entry_id")
    coordinator._price_charge_strategy = strategy
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_PRICE_NEUTRAL_BELOW_LIMIT) is None


# ===========================================================================
# 4. Leeres Zeitfenster (je Automatik: zeitgesteuertes/netzdienliches Laden)
# ===========================================================================
@pytest.mark.parametrize("feature", ["timed_charge", "grid_serving"])
@pytest.mark.parametrize(
    ("start", "end"),
    [(None, dt_time(6)), (dt_time(22), None), (None, None)],
)
@pytest.mark.parametrize("resolution", ["complete", "disable"])
async def test_incomplete_window_issue_lifecycle(
    hass, feature: str, start: dt_time | None, end: dt_time | None, resolution: str
) -> None:
    """REQ-SELF-DIAGNOSIS-REPAIRS: Fehlende Grenzen auch nach Reload melden."""
    coordinator = _make_coordinator(hass)
    setattr(coordinator, f"_{feature}_start", start)
    setattr(coordinator, f"_{feature}_end", end)
    issue_id = f"{ISSUE_EMPTY_CHARGE_WINDOW}_{feature}"
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, issue_id) is None

    setattr(coordinator, f"_{feature}_enabled", True)
    with patch(
        "custom_components.sax_power.infrastructure.self_diagnostics.ir."
        "async_create_issue",
        wraps=ir.async_create_issue,
    ) as create_issue:
        coordinator._async_check_self_diagnostics()
        coordinator._async_check_self_diagnostics()
    assert create_issue.call_count == 1
    assert _get_issue(hass, issue_id) is not None

    coordinator._self_diagnostics = SelfDiagnostics(hass, "test_entry_id")
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, issue_id) is not None

    if resolution == "complete":
        setattr(coordinator, f"_{feature}_start", dt_time(22))
        setattr(coordinator, f"_{feature}_end", dt_time(6))
    else:
        setattr(coordinator, f"_{feature}_enabled", False)
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, issue_id) is None


async def test_overlap_cleared_window_creates_repair_issue(hass) -> None:
    """REQ-SELF-DIAGNOSIS-REPAIRS: Geleerte Zeit nach Überschneidung melden."""
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(10)
    coordinator._timed_charge_end = dt_time(16)
    coordinator._grid_serving_enabled = True
    coordinator._grid_serving_start = dt_time(2)
    coordinator._grid_serving_end = dt_time(4)

    await coordinator.async_set_timed_charge_start(dt_time(20))
    await coordinator.async_set_timed_charge_end(dt_time(1))
    assert coordinator.timed_charge_start is None
    assert coordinator.timed_charge_end == dt_time(1)
    assert coordinator.timed_charge_enabled is True
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, f"{ISSUE_EMPTY_CHARGE_WINDOW}_timed_charge") is not None


async def test_empty_timed_charge_window_issue_triggers(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(22, 0)
    coordinator._timed_charge_end = dt_time(22, 0)

    coordinator._async_check_self_diagnostics()

    issue = _get_issue(hass, f"{ISSUE_EMPTY_CHARGE_WINDOW}_timed_charge")
    assert issue is not None
    assert issue.translation_placeholders == {
        "feature": "Netzladung (zeitgesteuertes Laden)"
    }


async def test_empty_grid_serving_window_issue_triggers(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._grid_serving_enabled = True
    coordinator._grid_serving_start = dt_time(10, 0)
    coordinator._grid_serving_end = dt_time(10, 0)

    coordinator._async_check_self_diagnostics()

    issue = _get_issue(hass, f"{ISSUE_EMPTY_CHARGE_WINDOW}_grid_serving")
    assert issue is not None
    assert issue.translation_placeholders == {"feature": "Netzdienliches Laden"}


async def test_empty_window_issue_not_recreated_every_cycle(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(22, 0)
    coordinator._timed_charge_end = dt_time(22, 0)

    with patch(
        "custom_components.sax_power.coordinator.ir.async_create_issue"
    ) as mock_create:
        coordinator._async_check_self_diagnostics()
        coordinator._async_check_self_diagnostics()

    assert mock_create.call_count == 1


async def test_empty_window_issue_clears_once_window_is_set(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(22, 0)
    coordinator._timed_charge_end = dt_time(22, 0)
    coordinator._async_check_self_diagnostics()
    issue_id = f"{ISSUE_EMPTY_CHARGE_WINDOW}_timed_charge"
    assert _get_issue(hass, issue_id) is not None

    coordinator._timed_charge_end = dt_time(6, 0)
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, issue_id) is None


async def test_empty_window_issue_clears_once_feature_disabled(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(22, 0)
    coordinator._timed_charge_end = dt_time(22, 0)
    coordinator._async_check_self_diagnostics()
    issue_id = f"{ISSUE_EMPTY_CHARGE_WINDOW}_timed_charge"
    assert _get_issue(hass, issue_id) is not None

    coordinator._timed_charge_enabled = False
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, issue_id) is None


# ===========================================================================
# 5. Kein aktiver Monat (je Automatik)
# ===========================================================================
async def test_no_active_months_issue_triggers_for_timed_charge(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_months = frozenset()

    coordinator._async_check_self_diagnostics()

    issue = _get_issue(hass, f"{ISSUE_NO_ACTIVE_MONTHS}_timed_charge")
    assert issue is not None
    assert issue.translation_placeholders == {
        "feature": "Netzladung (zeitgesteuertes Laden)"
    }


async def test_no_active_months_issue_triggers_for_grid_serving(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._grid_serving_enabled = True
    coordinator._grid_serving_months = frozenset()

    coordinator._async_check_self_diagnostics()

    issue = _get_issue(hass, f"{ISSUE_NO_ACTIVE_MONTHS}_grid_serving")
    assert issue is not None


async def test_no_active_months_issue_not_recreated_every_cycle(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_start = dt_time(22)
    coordinator._timed_charge_end = dt_time(6)
    coordinator._timed_charge_months = frozenset()

    with patch(
        "custom_components.sax_power.coordinator.ir.async_create_issue"
    ) as mock_create:
        coordinator._async_check_self_diagnostics()
        coordinator._async_check_self_diagnostics()

    assert mock_create.call_count == 1


async def test_no_active_months_issue_clears_once_a_month_is_selected(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator._timed_charge_enabled = True
    coordinator._timed_charge_months = frozenset()
    coordinator._async_check_self_diagnostics()
    issue_id = f"{ISSUE_NO_ACTIVE_MONTHS}_timed_charge"
    assert _get_issue(hass, issue_id) is not None

    coordinator._timed_charge_months = frozenset({1})
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, issue_id) is None


# ===========================================================================
# 6. Wirtschaftlichkeit: Netzbezugspreis nicht verfügbar
# (REQ-ECONOMICS-OBSERVABILITY) - die Karenzzeit/Sofortfehler-Logik selbst
# sitzt bereits im Coordinator (_update_economics_price_availability, siehe
# tests/test_coordinator.py); hier nur die Zustandsflanke der Issue-
# Erzeugung/-Löschung anhand des bereits fertig ausgewerteten Flags.
# ===========================================================================
async def test_economics_price_unavailable_issue_triggers_when_flagged(hass) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.options = {CONF_ECONOMICS_TARIFF_TYPE: "fixed"}
    coordinator._economics_price_unavailable = True

    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_ECONOMICS_PRICE_UNAVAILABLE) is not None


async def test_economics_price_unavailable_issue_not_recreated_every_cycle(
    hass,
) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.options = {CONF_ECONOMICS_TARIFF_TYPE: "fixed"}
    coordinator._economics_price_unavailable = True

    with patch(
        "custom_components.sax_power.coordinator.ir.async_create_issue"
    ) as mock_create:
        coordinator._async_check_self_diagnostics()
        coordinator._async_check_self_diagnostics()

    assert mock_create.call_count == 1


async def test_economics_price_unavailable_issue_clears_once_price_returns(
    hass,
) -> None:
    coordinator = _make_coordinator(hass)
    coordinator.options = {CONF_ECONOMICS_TARIFF_TYPE: "fixed"}
    coordinator._economics_price_unavailable = True
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_ECONOMICS_PRICE_UNAVAILABLE) is not None

    coordinator._economics_price_unavailable = False
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_ECONOMICS_PRICE_UNAVAILABLE) is None


async def test_economics_price_unavailable_issue_clears_after_a_reload(hass) -> None:
    """Ein Neuladen des Config Entry erzeugt eine frische SelfDiagnostics-
    Instanz mit zurückgesetztem In-Memory-Flag - ein davor angelegtes,
    in der Registry noch vorhandenes Issue muss trotzdem gelöscht werden,
    sobald der Preis wieder gültig ist (nicht erst nach einem erneuten
    Sichtbarwerden des Problems)."""
    coordinator = _make_coordinator(hass)
    coordinator.options = {CONF_ECONOMICS_TARIFF_TYPE: "fixed"}
    coordinator._economics_price_unavailable = True
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_ECONOMICS_PRICE_UNAVAILABLE) is not None

    # Simuliert den Neustart der SelfDiagnostics-Instanz bei einem Neuladen
    # des Config Entry - das Issue bleibt in der Registry bestehen.
    coordinator._self_diagnostics = SelfDiagnostics(hass, coordinator.entry_id)
    coordinator._economics_price_unavailable = False

    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_ECONOMICS_PRICE_UNAVAILABLE) is None


async def test_economics_price_unavailable_issue_not_triggered_when_disabled(
    hass,
) -> None:
    """Ein deaktivierter Tarif zeigt keinen Preis-Issue, selbst wenn das
    Flag aus einer früheren Aktivierung noch True wäre."""
    coordinator = _make_coordinator(hass)
    coordinator.options = {}
    coordinator._economics_price_unavailable = True

    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_ECONOMICS_PRICE_UNAVAILABLE) is None


# ===========================================================================
# Kein falsch-positives Issue bei unauffälliger Konfiguration
# ===========================================================================
async def test_no_issues_created_for_a_healthy_default_configuration(hass) -> None:
    coordinator = _make_coordinator(hass)

    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_PRICE_SENSOR_MISSING) is None
    assert _get_issue(hass, ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE) is None
    assert _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC) is None
    assert _get_issue(hass, ISSUE_PRICE_NEUTRAL_BELOW_LIMIT) is None
    assert _get_issue(hass, f"{ISSUE_EMPTY_CHARGE_WINDOW}_timed_charge") is None
    assert _get_issue(hass, f"{ISSUE_EMPTY_CHARGE_WINDOW}_grid_serving") is None
    assert _get_issue(hass, f"{ISSUE_NO_ACTIVE_MONTHS}_timed_charge") is None
    assert _get_issue(hass, f"{ISSUE_NO_ACTIVE_MONTHS}_grid_serving") is None
    assert _get_issue(hass, ISSUE_ECONOMICS_PRICE_UNAVAILABLE) is None


async def test_fix_flow_is_chosen_by_issue_key(hass) -> None:
    """Dashboard-Updates und Ladekonflikte öffnen den passenden Reparaturdialog."""
    dashboard_flow = await async_create_fix_flow(
        hass,
        f"{ISSUE_VUE_DASHBOARD_UPDATE}_entry",
        {"entry_id": "entry", "issue_key": ISSUE_VUE_DASHBOARD_UPDATE},
    )
    conflict_flow = await async_create_fix_flow(
        hass,
        f"{ISSUE_PRICE_CHARGE_CONFLICT}_entry",
        {"entry_id": "entry", "issue_key": ISSUE_PRICE_CHARGE_CONFLICT},
    )
    assert isinstance(dashboard_flow, VueDashboardRepairFlow)
    assert isinstance(conflict_flow, ChargeConflictRepairFlow)


@pytest.mark.parametrize("issue_key", ["dashboard_outdated", "unknown_issue"])
async def test_obsolete_or_unknown_repair_cannot_change_charging(
    hass, issue_key: str
) -> None:
    """Alte Dialoge lösen weder Ladewechsel noch Konfliktquittierung aus."""
    coordinator = MagicMock(spec=SaxPowerCoordinator)
    hass.data[DOMAIN] = {"entry": {DATA_COORDINATOR: coordinator}}
    flow = await async_create_fix_flow(
        hass,
        f"{issue_key}_entry",
        {"entry_id": "entry", "issue_key": issue_key},
    )
    flow.hass = hass
    assert (await flow.async_step_confirm())["type"] == "create_entry"
    assert (await flow.async_step_cancel())["type"] == "create_entry"
    assert not coordinator.mock_calls
