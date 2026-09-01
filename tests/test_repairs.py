"""Tests für die Selbstdiagnose-Prüfungen aus repairs.py/coordinator.py
(anforderung.yaml, REQ-SELF-DIAGNOSIS-REPAIRS).

Der Ladekonflikt-Bestätigungsdialog (repairs.ChargeConflictRepairFlow) wird
bereits in tests/test_price_optimizer.py abgedeckt - hier geht es nur um
die fünf zusätzlichen, rein informativen (nicht fixierbaren)
Selbstdiagnose-Issues aus SaxPowerCoordinator._async_check_self_diagnostics.
Jede Prüfung wird auf drei Arten getestet: Auslösen (nach Ablauf der
jeweiligen Karenzzeit, sofern vorhanden), Idempotenz (kein wiederholtes
Anlegen bei unverändertem Problemzustand) und Selbstheilung (Issue
verschwindet automatisch, sobald die Ursache behoben ist)."""

from __future__ import annotations

from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.const import (
    CONF_DASHBOARD_UPDATE_DISMISSED,
    CONF_ECONOMICS_TARIFF_TYPE,
    CONF_PRICE_SENSOR,
    DOMAIN,
    ISSUE_DASHBOARD_OUTDATED,
    ISSUE_ECONOMICS_PRICE_UNAVAILABLE,
    ISSUE_EMPTY_CHARGE_WINDOW,
    ISSUE_MAX_SOC_BELOW_MIN_SOC,
    ISSUE_NO_ACTIVE_MONTHS,
    ISSUE_PRICE_CHARGE_CONFLICT,
    ISSUE_PRICE_NEUTRAL_BELOW_LIMIT,
    ISSUE_PRICE_SENSOR_MISSING,
    ISSUE_SUNSPEC_PERSISTENTLY_UNAVAILABLE,
    MAX_SOC,
    PRICE_SENSOR_MISSING_GRACE_PERIOD,
    PRICE_STATUS_NO_PRICE_DATA,
    PRICE_STATUS_WAITING,
    SUNSPEC_PERSISTENTLY_UNAVAILABLE_GRACE_PERIOD,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.price_optimizer import PricePlan
from custom_components.sax_power.repairs import (
    ChargeConflictRepairFlow,
    DashboardOutdatedRepairFlow,
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
    coordinator._max_soc = 50
    coordinator._timed_charge_min_soc = 60

    coordinator._async_check_self_diagnostics()

    issue = _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC)
    assert issue is not None
    assert issue.translation_placeholders == {"max_soc": "50", "min_soc": "60"}


async def test_max_soc_below_min_soc_issue_not_recreated_every_cycle(hass) -> None:
    coordinator = _make_coordinator(hass)
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
    coordinator._max_soc = 50
    coordinator._timed_charge_min_soc = 60
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC) is not None

    coordinator._max_soc = 80
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_MAX_SOC_BELOW_MIN_SOC) is None


# ===========================================================================
# 3b. Neutralpreis nicht über der Preisgrenze (REQ-DYNAMIC-PRICE-CHARGE)
# ===========================================================================
async def test_price_neutral_below_limit_issue_triggers_immediately(hass) -> None:
    """Statische Einstellungskombination wie Prüfung 3 - kein
    Karenzzeit-Timer nötig."""
    coordinator = _make_coordinator(hass)
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
    coordinator._price_charge_max_price = 0.30
    coordinator._price_charge_neutral_price = 0.30

    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_PRICE_NEUTRAL_BELOW_LIMIT) is not None


async def test_price_neutral_below_limit_issue_not_recreated_every_cycle(hass) -> None:
    coordinator = _make_coordinator(hass)
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
    coordinator._price_charge_max_price = 0.30
    coordinator._price_charge_neutral_price = 0.20
    coordinator._async_check_self_diagnostics()
    assert _get_issue(hass, ISSUE_PRICE_NEUTRAL_BELOW_LIMIT) is not None

    coordinator._price_charge_neutral_price = 0.40
    coordinator._async_check_self_diagnostics()

    assert _get_issue(hass, ISSUE_PRICE_NEUTRAL_BELOW_LIMIT) is None


# ===========================================================================
# 4. Leeres Zeitfenster (je Automatik: zeitgesteuertes/netzdienliches Laden)
# ===========================================================================
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
    from custom_components.sax_power.infrastructure.self_diagnostics import (
        SelfDiagnostics,
    )

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


# --------------------------------------------------------------------------
# Hinweis auf ein veraltetes Dashboard (#138)
# --------------------------------------------------------------------------
async def test_fix_flow_is_chosen_by_issue_key(hass) -> None:
    """Die issue_id trägt die Entry-ID als Suffix und taugt deshalb nicht
    zum Vergleich - verzweigt wird über den issue_key aus den Issue-Daten.
    Ohne diese Verzweigung bekäme jedes künftige fixierbare Issue den
    Ladekonflikt-Dialog."""
    dashboard_flow = await async_create_fix_flow(
        hass,
        f"{ISSUE_DASHBOARD_OUTDATED}_entry",
        {"entry_id": "entry", "issue_key": ISSUE_DASHBOARD_OUTDATED},
    )
    conflict_flow = await async_create_fix_flow(
        hass,
        f"{ISSUE_PRICE_CHARGE_CONFLICT}_entry",
        {"entry_id": "entry", "issue_key": ISSUE_PRICE_CHARGE_CONFLICT},
    )

    assert isinstance(dashboard_flow, DashboardOutdatedRepairFlow)
    assert isinstance(conflict_flow, ChargeConflictRepairFlow)


async def test_dashboard_repair_rebuilds_on_confirm(hass) -> None:
    """Bestätigen baut das Dashboard neu - mit force, weil ein vorhandenes
    Dashboard sonst unangetastet bliebe (genau der gemeldete Zustand)."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="dash_entry", data={})
    entry.add_to_hass(hass)
    flow = DashboardOutdatedRepairFlow(
        {"entry_id": entry.entry_id, "issue_key": ISSUE_DASHBOARD_OUTDATED}
    )
    flow.hass = hass

    with patch(
        "custom_components.sax_power.repairs.async_create_dashboard",
        new=AsyncMock(),
    ) as rebuild:
        result = await flow.async_step_confirm()

    assert result["type"] == "create_entry"
    assert rebuild.await_args.args[1] is entry
    assert rebuild.await_args.kwargs["force"] is True
    assert not entry.data.get(CONF_DASHBOARD_UPDATE_DISMISSED)


async def test_dashboard_repair_remembers_a_declined_hint(hass) -> None:
    """Abbrechen ändert nichts am Dashboard und merkt sich das dauerhaft -
    ein bewusst umgebautes Dashboard ist ein legitimer Zustand."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="dash_entry", data={})
    entry.add_to_hass(hass)
    flow = DashboardOutdatedRepairFlow(
        {"entry_id": entry.entry_id, "issue_key": ISSUE_DASHBOARD_OUTDATED}
    )
    flow.hass = hass

    with patch(
        "custom_components.sax_power.repairs.async_create_dashboard",
        new=AsyncMock(),
    ) as rebuild:
        result = await flow.async_step_cancel()
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    rebuild.assert_not_awaited()
    assert entry.data[CONF_DASHBOARD_UPDATE_DISMISSED] is True


async def test_dashboard_repair_survives_a_removed_entry(hass) -> None:
    """Der Config Entry kann zwischen Anlegen des Issues und Öffnen des
    Dialogs entfernt worden sein - der Flow darf daran nicht scheitern."""
    flow = DashboardOutdatedRepairFlow(
        {"entry_id": "gibt_es_nicht", "issue_key": ISSUE_DASHBOARD_OUTDATED}
    )
    flow.hass = hass

    assert (await flow.async_step_confirm())["type"] == "create_entry"
    assert (await flow.async_step_cancel())["type"] == "create_entry"
