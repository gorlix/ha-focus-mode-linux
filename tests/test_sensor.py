"""Tests for the sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator
from custom_components.linux_focus_mode.sensor import (
    FocusModeBlockedCountSensor,
    FocusModeLockRemainingSensor,
)

from .conftest import MOCK_STATE, MOCK_STATE_TIMER_LOCK, mock_client


def _make_entry():
    entry = AsyncMock()
    entry.entry_id = "test_entry_id"
    return entry


async def test_blocked_count_sensor(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sensor = FocusModeBlockedCountSensor(coordinator, _make_entry())
    assert sensor.native_value == 2  # MOCK_STATE has 2 blocked items


async def test_blocked_count_sensor_attributes(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sensor = FocusModeBlockedCountSensor(coordinator, _make_entry())
    attrs = sensor.extra_state_attributes
    assert "blocked_items" in attrs
    assert len(attrs["blocked_items"]) == 2


async def test_blocked_count_sensor_no_data(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    coordinator.data = None
    sensor = FocusModeBlockedCountSensor(coordinator, _make_entry())
    assert sensor.native_value is None


async def test_lock_remaining_sensor_no_lock(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sensor = FocusModeLockRemainingSensor(coordinator, _make_entry())
    assert sensor.native_value == "—"


async def test_lock_remaining_sensor_with_lock(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    mock_client.async_get_state.return_value = MOCK_STATE_TIMER_LOCK
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sensor = FocusModeLockRemainingSensor(coordinator, _make_entry())
    assert sensor.native_value == "22m 14s"


async def test_sensor_unavailable_when_coordinator_offline(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    coordinator.set_unavailable()
    sensor = FocusModeBlockedCountSensor(coordinator, _make_entry())
    assert sensor.available is False
