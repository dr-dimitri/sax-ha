"""REQ-GRID-ENERGY / REQ-ECONOMICS-OBSERVABILITY: stable published attributes."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import Event, HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.const import (
    CONF_ECONOMICS_FEED_IN_PRICE,
    CONF_ECONOMICS_FIXED_IMPORT_PRICE,
    CONF_ECONOMICS_TARIFF_TYPE,
    DATA_COORDINATOR,
    DOMAIN,
    READ_BLOCK_COUNT,
    READ_BLOCK_START,
    REG_SOC,
    REG_SUN_IC_MAX_POWER_REFERENCE,
    REG_SUN_METER_POWER_ACTIVE_SUM,
)
from custom_components.sax_power.coordinator import SaxPowerCoordinator
from custom_components.sax_power.domain.tariff import (
    PriceQuote,
    QuoteResult,
    QuoteSource,
    QuoteUnavailable,
)

STARTED = datetime(2026, 9, 11, 12, tzinfo=UTC)
CLOCK = "custom_components.sax_power.coordinator.monotonic"
UTC_CLOCK = "custom_components.sax_power.coordinator.dt_util.utcnow"
FIXED_TARIFF = {
    CONF_ECONOMICS_TARIFF_TYPE: "fixed",
    CONF_ECONOMICS_FIXED_IMPORT_PRICE: 0.30,
    CONF_ECONOMICS_FEED_IN_PRICE: 0.08,
}


@pytest.mark.parametrize("options", [{}, FIXED_TARIFF], ids=["default", "fixed-tariff"])
async def test_constant_measurements_do_not_emit_state_changes(
    hass: HomeAssistant, freezer: Any, options: dict[str, Any]
) -> None:
    """REQ-GRID-ENERGY: 20 unchanged polls create no extra recorder state rows."""
    freezer.move_to(STARTED)
    client = MagicMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    response = MagicMock()
    response.isError.return_value = False
    client.write_register = AsyncMock(return_value=response)
    grid_power = 0

    async def read(*, address: int, count: int, device_id: int) -> MagicMock:
        registers = [0] * count
        if device_id == 64:
            assert count == READ_BLOCK_COUNT
            registers[REG_SOC - READ_BLOCK_START] = 60
            registers[45 - READ_BLOCK_START] = 2
        else:
            for register, value in (
                (REG_SUN_IC_MAX_POWER_REFERENCE, 4600),
                (REG_SUN_METER_POWER_ACTIVE_SUM, grid_power & 0xFFFF),
            ):
                if address <= register < address + count:
                    registers[register - address] = value
        result = MagicMock()
        result.isError.return_value = False
        result.registers = registers
        return result

    client.read_holding_registers = AsyncMock(side_effect=read)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.1.50",
            "port": 502,
            "slave_id_basic": 64,
            "slave_id_extended": 100,
            "scan_interval": 10,
        },
        options=options,
        entry_id="churn",
    )
    entry.add_to_hass(hass)
    with (
        patch("custom_components.sax_power.AsyncModbusTcpClient", return_value=client),
        patch(CLOCK, return_value=1000),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    async def tick(seconds: int) -> None:
        freezer.move_to(STARTED + timedelta(seconds=seconds))
        with patch(CLOCK, return_value=1000 + seconds):
            await coordinator.async_refresh()
        await hass.async_block_till_done()

    counts: Counter[str] = Counter()

    def state_changed(event: Event) -> None:
        counts.update([event.data["entity_id"]])

    try:
        await tick(2)
        stop_listening = hass.bus.async_listen(EVENT_STATE_CHANGED, state_changed)
        for seconds in range(4, 44, 2):
            await tick(seconds)
        assert not counts, dict(counts)
        for direction in ("imported_from_grid", "exported_to_grid"):
            state = hass.states.get(f"sensor.sax_power_energy_{direction}")
            assert state is not None
            assert not any(key.startswith("co2saver_") for key in state.attributes)
            assert state.attributes["integration_method"] == "left_riemann_sum"

        # A real meter change must still reach both live states and recorder events.
        grid_power = -1800
        await tick(44)
        await tick(46)
        imported = "sensor.sax_power_energy_imported_from_grid"
        assert counts[imported] == 1
        assert float(hass.states.get(imported).state) == pytest.approx(0.001)
        assert counts["sensor.sax_power_energy_exported_to_grid"] == 0
        stop_listening()
    finally:
        await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize(
    "reason",
    [QuoteUnavailable.PRICE_SENSOR_UNAVAILABLE, QuoteUnavailable.TARIFF_INCOMPLETE],
)
def test_quote_timestamp_marks_start_of_successful_phase(
    hass: HomeAssistant, reason: QuoteUnavailable
) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: success time changes only after a price gap."""
    coordinator = SaxPowerCoordinator(hass, MagicMock(), 64, 100, 10, "quote-phase")
    success = QuoteResult(quote=PriceQuote(0.30, QuoteSource.FIXED))
    with patch(UTC_CLOCK, return_value=STARTED):
        coordinator._update_economics_price_availability(success, 0.30, 1000)
    with patch(UTC_CLOCK, return_value=STARTED + timedelta(seconds=2)):
        coordinator._update_economics_price_availability(success, 0.30, 1002)
    assert coordinator._economics_last_successful_quote_at == STARTED

    coordinator._update_economics_price_availability(
        QuoteResult(reason=reason), None, 1004
    )
    assert coordinator._economics_last_successful_quote_at == STARTED
    with patch(UTC_CLOCK, return_value=STARTED + timedelta(seconds=6)):
        coordinator._update_economics_price_availability(success, 0.30, 1006)
    assert coordinator._economics_last_successful_quote_at == STARTED + timedelta(
        seconds=6
    )


def test_tariff_reactivation_starts_a_new_successful_price_phase(
    hass: HomeAssistant,
) -> None:
    """REQ-ECONOMICS-OBSERVABILITY: a deliberate tariff pause ends the phase."""
    coordinator = SaxPowerCoordinator(hass, MagicMock(), 64, 100, 10, "quote-phase")
    coordinator.options = FIXED_TARIFF
    data: dict[str, Any] = {}
    with patch(UTC_CLOCK, return_value=STARTED):
        coordinator._accumulate_economics(data, None, 0.0, 0.0)
    coordinator.options = {}
    coordinator._accumulate_economics(data, None, 0.0, 0.0)
    assert coordinator._economics_last_successful_quote_at == STARTED
    coordinator.options = FIXED_TARIFF
    with patch(UTC_CLOCK, return_value=STARTED + timedelta(seconds=10)):
        coordinator._accumulate_economics(data, None, 0.0, 0.0)
    assert (
        data["economics_status_attributes"]["last_successful_quote_at"]
        == (STARTED + timedelta(seconds=10)).isoformat()
    )
