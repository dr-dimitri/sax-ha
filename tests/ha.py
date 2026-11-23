"""Shared test helpers across the HA test package rename in November 2026."""

from importlib.util import find_spec

if find_spec("pytest_homeassistant") is not None:
    from pytest_homeassistant import common, typing
    from pytest_homeassistant.components.recorder import common as recorder
else:
    from pytest_homeassistant_custom_component import common, typing
    from pytest_homeassistant_custom_component.components.recorder import (
        common as recorder,
    )

MockConfigEntry = common.MockConfigEntry
MockEntityPlatform = common.MockEntityPlatform
MockUser = common.MockUser
MockHAClientWebSocket = typing.MockHAClientWebSocket
WebSocketGenerator = typing.WebSocketGenerator
async_capture_events = common.async_capture_events
async_fire_time_changed = common.async_fire_time_changed
async_test_home_assistant = common.async_test_home_assistant
async_recorder_block_till_done = recorder.async_recorder_block_till_done
mock_device_registry = common.mock_device_registry
