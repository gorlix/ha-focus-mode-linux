"""Tests for the binary sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.linux_focus_mode.binary_sensor import (
    FocusModeAvailableBinarySensor,
    FocusModeLockedBinarySensor,
)
from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator

from .conftest import MOCK_STATE, MOCK_STATE_HA_LOCK, MOCK_STATE_TIMER_LOCK


def _make_entry():
    entry = AsyncMock()
    entry.entry_id = "test_entry_id"
    return entry


def _make_coordinator(hass: HomeAssistant, state: dict, available: bool = True):
    coordinator = FocusModeCoordinator(hass)
    coordinator.data = state
    coordinator.available = available
    return coordinator


async def test_locked_sensor_false_when_unlocked(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE)
    sensor = FocusModeLockedBinarySensor(coordinator, _make_entry())
    assert sensor.is_on is False


async def test_locked_sensor_true_with_ha_lock(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE_HA_LOCK)
    sensor = FocusModeLockedBinarySensor(coordinator, _make_entry())
    assert sensor.is_on is True


async def test_locked_sensor_true_with_timer_lock(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE_TIMER_LOCK)
    sensor = FocusModeLockedBinarySensor(coordinator, _make_entry())
    assert sensor.is_on is True


async def test_app_online_sensor_true_when_available(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE, available=True)
    sensor = FocusModeAvailableBinarySensor(coordinator, _make_entry())
    assert sensor.is_on is True
    assert sensor.available is True


async def test_app_online_sensor_false_after_dying_gasp(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE, available=True)
    coordinator.set_unavailable()
    sensor = FocusModeAvailableBinarySensor(coordinator, _make_entry())
    assert sensor.is_on is False
    assert sensor.available is True  # App Online stays available (not greyed out)
