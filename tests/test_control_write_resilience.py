"""REQ-EXTENDED-MODE-RESILIENCE: control failures preserve measurement updates."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from functools import partial
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import UpdateFailed
from pymodbus.exceptions import ModbusException

from custom_components.sax_power.const import (
    DOMAIN,
    ISSUE_MAX_SOC_BELOW_MIN_SOC,
    REG_SOC,
    REG_SUN_IC_CONTROL_MODE,
    REG_SUN_IC_MAX_POWER_REFERENCE,
    REG_SUN_IC_POWER_SETPOINT_PCT,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator


def _read_response(
    *, address: int, count: int, device_id: int, soc: int = 85, reference: int = 4600
) -> MagicMock:
    result = MagicMock()
    result.isError.return_value = False
    result.registers = [0] * count
    register = REG_SOC if device_id == 64 else REG_SUN_IC_MAX_POWER_REFERENCE
    if address <= register < address + count:
        result.registers[register - address] = soc if device_id == 64 else reference
    return result


@pytest.fixture
async def coordinator(hass: HomeAssistant) -> AsyncIterator[SaxPowerCoordinator]:
    client = MagicMock()
    client.connected = True
    client.read_holding_registers = AsyncMock(side_effect=_read_response)
    success = MagicMock()
    success.isError.return_value = False
    client.write_register = AsyncMock(return_value=success)
    coordinator = SaxPowerCoordinator(
        hass,
        client,
        slave_id=64,
        slave_id_extended=100,
        scan_interval=10,
        entry_id="control_write_resilience",
    )
    coordinator.data = {"soc": 50, "ic_max_power_reference": 4600}
    coordinator._max_soc = 80
    yield coordinator
    await coordinator.async_shutdown(reset_device=False)


@pytest.mark.parametrize(
    "failed_register", [REG_SUN_IC_CONTROL_MODE, REG_SUN_IC_POWER_SETPOINT_PCT]
)
async def test_poll_write_failure_publishes_measurements_and_retries(
    coordinator: SaxPowerCoordinator,
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    failed_register: int,
) -> None:
    """REQ-TIMED-SOC-CHARGE: fehlender Write verwirft weder Daten noch Diagnose."""
    success = MagicMock()
    success.isError.return_value = False

    async def write(*, address: int, value: int, device_id: int) -> MagicMock:
        if address == failed_register:
            raise ModbusException("Gerät lehnt den Steuerbefehl ab")
        return success

    coordinator.client.write_register.side_effect = write
    coordinator._timed_charge_min_soc = 90
    caplog.set_level(logging.WARNING)

    for _ in range(2):
        caplog.clear()
        await coordinator.async_refresh()

        assert coordinator.last_update_success is True
        assert coordinator.data["soc"] == 85
        assert coordinator.data["timed_charge_active"] is False
        assert coordinator.max_soc_clamped is False
        assert coordinator.sun_charge_active is False
        assert len(caplog.records) == 1
        assert "Gerät lehnt den Steuerbefehl ab" in caplog.records[0].getMessage()
        assert caplog.records[0].exc_info is None

    assert (
        ir.async_get(hass).async_get_issue(
            DOMAIN, f"{ISSUE_MAX_SOC_BELOW_MIN_SOC}_{coordinator.entry_id}"
        )
        is not None
    )

    coordinator.client.write_register.side_effect = None
    coordinator.client.read_holding_registers.side_effect = partial(
        _read_response, soc=86
    )
    coordinator._basic_last_read = None
    caplog.clear()
    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert coordinator.data["soc"] == 86
    assert coordinator.max_soc_clamped is True
    assert coordinator.sun_charge_active is True
    assert not caplog.records


async def test_poll_validation_failure_is_logged_without_losing_measurements(
    coordinator: SaxPowerCoordinator, caplog: pytest.LogCaptureFixture
) -> None:
    """REQ-EXTENDED-MODE-RESILIENCE: auch Fehler vor dem Write bleiben sichtbar."""
    coordinator._max_soc = 100
    coordinator._grid_charge_power = -1000
    coordinator.data["ic_max_power_reference"] = 0
    coordinator.client.read_holding_registers.side_effect = partial(
        _read_response, reference=0
    )
    caplog.set_level(logging.WARNING)

    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert coordinator.data["soc"] == 85
    assert coordinator.sun_charge_active is False
    coordinator.client.write_register.assert_not_awaited()
    assert len(caplog.records) == 1
    assert "Referenzwert Maximalleistung" in caplog.records[0].getMessage()
    assert caplog.records[0].exc_info is None


async def test_failed_basic_read_still_fails_measurement_update(
    coordinator: SaxPowerCoordinator,
) -> None:
    """REQ-EXTENDED-MODE-RESILIENCE: Basic-Read bleibt Mindestvoraussetzung."""
    coordinator.client.read_holding_registers.side_effect = ModbusException(
        "Basic-Read fehlgeschlagen"
    )

    await coordinator.async_refresh()

    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)
    assert coordinator.data["soc"] == 50
    assert coordinator.sun_charge_active is False


@pytest.mark.parametrize("source", ["service", "entity_setter"])
async def test_explicit_control_write_failure_reaches_caller(
    coordinator: SaxPowerCoordinator, source: str
) -> None:
    """REQ-MANUAL-GRID-CHARGE: Fehler bleiben bei Anwenderaktionen sichtbar."""
    coordinator.client.write_register.side_effect = ModbusException(
        "Steuerbefehl fehlgeschlagen"
    )

    with pytest.raises(HomeAssistantError, match="Steuerbefehl fehlgeschlagen"):
        if source == "service":
            await coordinator.async_start_grid_charge(-1000)
        else:
            await coordinator.async_set_max_soc(40)

    assert coordinator.sun_charge_active is False
    assert coordinator.grid_charge_active is False
