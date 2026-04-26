"""Tests for the switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator
from custom_components.linux_focus_mode.switch import (
    FocusModeActiveSwitch,
    FocusModeHaLockSwitch,
    FocusModeRestoreSwitch,
)

from .conftest import MOCK_STATE, MOCK_STATE_HA_LOCK, MOCK_STATE_TIMER_LOCK, mock_client


def _make_entry():
    entry = AsyncMock()
    entry.entry_id = "test_entry_id"
    return entry


async def test_active_switch_is_on(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeActiveSwitch(coordinator, _make_entry())
    assert sw.is_on is True


async def test_active_switch_is_off(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    mock_client.async_get_state.return_value = {**MOCK_STATE, "active": False}
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeActiveSwitch(coordinator, _make_entry())
    assert sw.is_on is False


async def test_active_switch_turn_on(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeActiveSwitch(coordinator, _make_entry())
    await sw.async_turn_on()
    mock_client.async_toggle_blocker.assert_awaited_once_with(True)


async def test_active_switch_turn_off_blocked_by_ha_lock(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """turn_off must raise HomeAssistantError when HA Lock is active."""
    mock_client.async_get_state.return_value = MOCK_STATE_HA_LOCK
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeActiveSwitch(coordinator, _make_entry())

    with pytest.raises(HomeAssistantError):
        await sw.async_turn_off()

    mock_client.async_toggle_blocker.assert_not_awaited()


async def test_active_switch_turn_off_allowed_with_timer_lock(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """turn_off is allowed when lock has remaining_time (not HA lock)."""
    mock_client.async_get_state.return_value = MOCK_STATE_TIMER_LOCK
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeActiveSwitch(coordinator, _make_entry())
    await sw.async_turn_off()
    mock_client.async_toggle_blocker.assert_awaited_once_with(False)


async def test_ha_lock_switch_is_on(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    mock_client.async_get_state.return_value = MOCK_STATE_HA_LOCK
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeHaLockSwitch(coordinator, _make_entry())
    assert sw.is_on is True


async def test_ha_lock_switch_off_with_timer_lock(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """HA Lock switch is OFF when lock has remaining_time (timer/target lock)."""
    mock_client.async_get_state.return_value = MOCK_STATE_TIMER_LOCK
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeHaLockSwitch(coordinator, _make_entry())
    assert sw.is_on is False


async def test_ha_lock_turn_on(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeHaLockSwitch(coordinator, _make_entry())
    await sw.async_turn_on()
    mock_client.async_lock_ha.assert_awaited_once()


async def test_ha_lock_turn_off(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeHaLockSwitch(coordinator, _make_entry())
    await sw.async_turn_off()
    mock_client.async_unlock.assert_awaited_once()


async def test_restore_switch_is_on(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeRestoreSwitch(coordinator, _make_entry())
    assert sw.is_on is True  # MOCK_STATE has restore_enabled=True


async def test_restore_switch_turn_off(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    sw = FocusModeRestoreSwitch(coordinator, _make_entry())
    await sw.async_turn_off()
    mock_client.async_toggle_restore.assert_awaited_once_with(False)


async def test_switch_unavailable_when_coordinator_offline(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    coordinator.set_unavailable()
    sw = FocusModeActiveSwitch(coordinator, _make_entry())
    assert sw.available is False
