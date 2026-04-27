"""Tests for the sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator
from custom_components.linux_focus_mode.sensor import (
    FocusModeBlockedCountSensor,
    FocusModeLockRemainingSensor,
)

from .conftest import MOCK_STATE, MOCK_STATE_TIMER_LOCK


def _make_entry():
    entry = AsyncMock()
    entry.entry_id = "test_entry_id"
    return entry


def _make_coordinator(hass: HomeAssistant, state: dict | None, available: bool = True):
    coordinator = FocusModeCoordinator(hass)
    coordinator.data = state
    coordinator.available = available
    return coordinator


async def test_blocked_count_sensor(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE)
    sensor = FocusModeBlockedCountSensor(coordinator, _make_entry())
    assert sensor.native_value == 2  # MOCK_STATE has 2 blocked items


async def test_blocked_count_sensor_attributes(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE)
    sensor = FocusModeBlockedCountSensor(coordinator, _make_entry())
    attrs = sensor.extra_state_attributes
    assert "blocked_items" in attrs
    assert len(attrs["blocked_items"]) == 2


async def test_blocked_count_sensor_no_data(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, None, available=False)
    sensor = FocusModeBlockedCountSensor(coordinator, _make_entry())
    assert sensor.native_value is None


async def test_lock_remaining_sensor_no_lock(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE)
    sensor = FocusModeLockRemainingSensor(coordinator, _make_entry())
    assert sensor.native_value == "—"


async def test_lock_remaining_sensor_with_lock(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE_TIMER_LOCK)
    sensor = FocusModeLockRemainingSensor(coordinator, _make_entry())
    assert sensor.native_value == "22m 14s"


async def test_sensor_unavailable_when_coordinator_offline(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE, available=True)
    coordinator.set_unavailable()
    sensor = FocusModeBlockedCountSensor(coordinator, _make_entry())
    assert sensor.available is False
