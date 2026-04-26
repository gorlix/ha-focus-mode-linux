"""Tests for the binary sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.linux_focus_mode.binary_sensor import (
    FocusModeAvailableBinarySensor,
    FocusModeLockedBinarySensor,
)
from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator

from .conftest import MOCK_STATE, MOCK_STATE_HA_LOCK, MOCK_STATE_TIMER_LOCK, mock_client


def _make_entry():
    entry = AsyncMock()
    entry.entry_id = "test_entry_id"
    return entry


async def test_locked_sensor_false_when_unlocked(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sensor = FocusModeLockedBinarySensor(coordinator, _make_entry())
    assert sensor.is_on is False


async def test_locked_sensor_true_with_ha_lock(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    mock_client.async_get_state.return_value = MOCK_STATE_HA_LOCK
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sensor = FocusModeLockedBinarySensor(coordinator, _make_entry())
    assert sensor.is_on is True


async def test_locked_sensor_true_with_timer_lock(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    mock_client.async_get_state.return_value = MOCK_STATE_TIMER_LOCK
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sensor = FocusModeLockedBinarySensor(coordinator, _make_entry())
    assert sensor.is_on is True


async def test_app_online_sensor_true_when_available(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sensor = FocusModeAvailableBinarySensor(coordinator, _make_entry())
    assert sensor.is_on is True
    assert sensor.available is True


async def test_app_online_sensor_false_after_dying_gasp(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    coordinator.set_unavailable()
    sensor = FocusModeAvailableBinarySensor(coordinator, _make_entry())
    assert sensor.is_on is False
    # App Online sensor stays available=True so HA shows it (not greyed out)
    assert sensor.available is True
