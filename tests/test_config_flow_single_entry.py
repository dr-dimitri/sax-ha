"""Regressionen für die Beschränkung auf einen eingerichteten SAX-Speicher."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sax_power.const import CONF_PRICE_SENSOR, DOMAIN

CONNECTION_DATA = {
    "host": "192.168.1.50",
    "port": 502,
    "slave_id_basic": 64,
    "slave_id_extended": 100,
    "scan_interval": 10,
}
SUMMARY = {"sunspec_available": False}


async def _open_flow_at_step(
    hass: HomeAssistant, step_id: str, *, host: str = "192.168.1.77"
) -> str:
    """Öffne einen echten mehrstufigen Flow bis zum gewünschten Formular."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    for expected_step in ("user", "grid_charge", "finish"):
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == expected_step
        if expected_step == step_id:
            return result["flow_id"]
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**CONNECTION_DATA, "host": host} if expected_step == "user" else {},
        )
    raise AssertionError(f"Unbekannter Einrichtungsschritt: {step_id}")


async def test_dhcp_rejects_another_storage_without_touching_existing_entry(
    hass: HomeAssistant,
) -> None:
    """REQ-IP-CONFIGURABLE-UI/REQ-DHCP-DISCOVERY: Zweiter Speicher bricht früh ab."""
    options = {CONF_PRICE_SENSOR: "sensor.strompreis"}
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONNECTION_DATA,
        options=options,
        source=config_entries.SOURCE_DHCP,
        unique_id="11:22:33:44:55:66",
    )
    entry.add_to_hass(hass)

    with (
        patch("custom_components.sax_power.config_flow.AsyncModbusTcpClient") as client,
        patch.object(hass.config_entries, "async_schedule_reload") as reload_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="192.168.1.77",
                hostname="sax-another",
                macaddress="aabbccddeeff",
            ),
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
    client.assert_not_called()
    reload_entry.assert_not_called()
    assert hass.config_entries.async_entries(DOMAIN) == [entry]
    assert entry.data == CONNECTION_DATA
    assert entry.options == options
    assert entry.unique_id == "11:22:33:44:55:66"
    assert entry.source == config_entries.SOURCE_DHCP


@pytest.mark.parametrize("step_id", ["grid_charge", "finish"])
async def test_open_onboarding_stops_when_an_entry_was_added(
    hass: HomeAssistant, step_id: str
) -> None:
    """REQ-IP-CONFIGURABLE-UI: Ein früher geöffneter Flow darf nicht weiterlaufen."""
    with (
        patch("custom_components.sax_power.config_flow._async_validate_connection"),
        patch(
            "custom_components.sax_power.config_flow._async_read_finish_summary",
            return_value=SUMMARY,
        ),
    ):
        flow_id = await _open_flow_at_step(hass, step_id)

    entry = MockConfigEntry(
        domain=DOMAIN, data=CONNECTION_DATA, unique_id="192.168.1.50:502"
    )
    entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.sax_power.config_flow._async_validate_connection"
        ) as validate,
        patch(
            "custom_components.sax_power.config_flow._async_read_finish_summary"
        ) as summary,
        patch("custom_components.sax_power.config_flow.AsyncModbusTcpClient") as client,
    ):
        result = await hass.config_entries.flow.async_configure(flow_id, {})

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
    validate.assert_not_awaited()
    summary.assert_not_awaited()
    client.assert_not_called()
    assert hass.config_entries.async_entries(DOMAIN) == [entry]


@pytest.mark.parametrize(
    ("disabled_by", "state"),
    [
        (
            config_entries.ConfigEntryDisabler.USER,
            config_entries.ConfigEntryState.NOT_LOADED,
        ),
        (None, config_entries.ConfigEntryState.SETUP_ERROR),
    ],
)
async def test_unavailable_entry_still_blocks_another_setup(
    hass: HomeAssistant,
    disabled_by: config_entries.ConfigEntryDisabler | None,
    state: config_entries.ConfigEntryState,
) -> None:
    """REQ-IP-CONFIGURABLE-UI: Deaktivierte und fehlgeschlagene Einträge zählen mit."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONNECTION_DATA,
        unique_id="192.168.1.50:502",
        disabled_by=disabled_by,
        state=state,
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.sax_power.config_flow.AsyncModbusTcpClient"
    ) as client:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
    client.assert_not_called()
    assert entry.disabled_by == disabled_by
    assert entry.state == state
    assert hass.config_entries.async_entries(DOMAIN) == [entry]


@pytest.mark.parametrize(
    "source", [config_entries.SOURCE_USER, config_entries.SOURCE_DHCP]
)
async def test_ignored_discovery_does_not_block_first_storage(
    hass: HomeAssistant, source: str
) -> None:
    """REQ-IP-CONFIGURABLE-UI/REQ-DHCP-DISCOVERY: Ignorierte Geräte zählen nicht."""
    ignored = MockConfigEntry(
        domain=DOMAIN,
        data={},
        unique_id="11:22:33:44:55:66",
        source=config_entries.SOURCE_IGNORE,
    )
    ignored.add_to_hass(hass)

    with (
        patch("custom_components.sax_power.config_flow._async_validate_connection"),
        patch(
            "custom_components.sax_power.config_flow._async_read_finish_summary",
            return_value=SUMMARY,
        ),
        patch.object(hass.config_entries, "async_setup", return_value=True) as setup,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=(
                DhcpServiceInfo(
                    ip="192.168.1.50",
                    hostname="sax-first",
                    macaddress="aabbccddeeff",
                )
                if source == config_entries.SOURCE_DHCP
                else None
            ),
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        for user_input in (CONNECTION_DATA, {}, {}):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input
            )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["result"].data["host"] == "192.168.1.50"
    assert hass.config_entries.async_entries(DOMAIN, include_ignore=False) == [
        result["result"]
    ]
    assert hass.config_entries.async_entries(DOMAIN, include_ignore=True) == [
        ignored,
        result["result"],
    ]
    assert ignored.source == config_entries.SOURCE_IGNORE
    assert ignored.data == {}
    setup.assert_awaited_once_with(result["result"].entry_id)


async def test_concurrent_finishes_create_exactly_one_entry(
    hass: HomeAssistant,
) -> None:
    """REQ-IP-CONFIGURABLE-UI: Gleichzeitige Abschlüsse starten nur einen Speicher."""
    with (
        patch("custom_components.sax_power.config_flow._async_validate_connection"),
        patch(
            "custom_components.sax_power.config_flow._async_read_finish_summary",
            return_value=SUMMARY,
        ),
    ):
        first_flow = await _open_flow_at_step(hass, "finish", host="192.168.1.77")
        second_flow = await _open_flow_at_step(hass, "finish", host="192.168.1.78")

    setup_started = asyncio.Event()
    finish_setup = asyncio.Event()

    async def delayed_setup(entry_id: str) -> bool:
        assert hass.config_entries.async_get_entry(entry_id) is not None
        setup_started.set()
        await finish_setup.wait()
        return True

    with patch.object(
        hass.config_entries, "async_setup", side_effect=delayed_setup
    ) as setup:
        tasks = [
            asyncio.create_task(hass.config_entries.flow.async_configure(flow_id, {}))
            for flow_id in (first_flow, second_flow)
        ]
        try:
            async with asyncio.timeout(5):
                await setup_started.wait()
                done, pending = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED
                )
                assert len(done) == 1
                assert len(pending) == 1
                rejected = next(iter(done)).result()
                assert rejected["type"] == FlowResultType.ABORT
                assert rejected["reason"] == "single_instance_allowed"
                assert len(hass.config_entries.async_entries(DOMAIN)) == 1
        finally:
            finish_setup.set()
            results = await asyncio.gather(*tasks)

    assert [result["type"] for result in results].count(
        FlowResultType.CREATE_ENTRY
    ) == 1
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    setup.assert_awaited_once()
