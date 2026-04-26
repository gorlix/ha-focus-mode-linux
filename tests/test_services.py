"""Tests for the registered HA services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from custom_components.linux_focus_mode import _register_services
from custom_components.linux_focus_mode.api import FocusModeApiCommunicationError
from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator
from custom_components.linux_focus_mode.const import DOMAIN

from .conftest import mock_client


async def _setup(hass: HomeAssistant, mock_client: AsyncMock) -> FocusModeCoordinator:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    coordinator.async_request_refresh = AsyncMock()
    _register_services(hass, coordinator)
    return coordinator


def _call(data: dict | None = None) -> ServiceCall:
    sc = MagicMock(spec=ServiceCall)
    sc.data = data or {}
    return sc


async def test_service_focus_on(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    coordinator = await _setup(hass, mock_client)
    await hass.services.async_call(DOMAIN, "focus_on", {}, blocking=True)
    mock_client.async_toggle_blocker.assert_awaited_with(True)


async def test_service_focus_off(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    coordinator = await _setup(hass, mock_client)
    await hass.services.async_call(DOMAIN, "focus_off", {}, blocking=True)
    mock_client.async_toggle_blocker.assert_awaited_with(False)


async def test_service_lock_timer(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    await _setup(hass, mock_client)
    await hass.services.async_call(DOMAIN, "lock_timer", {"minutes": 25}, blocking=True)
    mock_client.async_lock_timer.assert_awaited_with(25)


async def test_service_lock_target(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    await _setup(hass, mock_client)
    await hass.services.async_call(
        DOMAIN, "lock_target", {"hour": 14, "minute": 30}, blocking=True
    )
    mock_client.async_lock_target.assert_awaited_with(14, 30)


async def test_service_lock_ha(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    await _setup(hass, mock_client)
    await hass.services.async_call(DOMAIN, "lock_ha", {}, blocking=True)
    mock_client.async_lock_ha.assert_awaited_once()


async def test_service_unlock(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    await _setup(hass, mock_client)
    await hass.services.async_call(DOMAIN, "unlock", {}, blocking=True)
    mock_client.async_unlock.assert_awaited_once()


async def test_service_restore_on(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    await _setup(hass, mock_client)
    await hass.services.async_call(DOMAIN, "restore_on", {}, blocking=True)
    mock_client.async_toggle_restore.assert_awaited_with(True)


async def test_service_restore_off(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    await _setup(hass, mock_client)
    await hass.services.async_call(DOMAIN, "restore_off", {}, blocking=True)
    mock_client.async_toggle_restore.assert_awaited_with(False)


async def test_service_api_error_raises_ha_error(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """API failure in a service call raises HomeAssistantError."""
    coordinator = await _setup(hass, mock_client)
    mock_client.async_toggle_blocker.side_effect = FocusModeApiCommunicationError("down")

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "focus_on", {}, blocking=True)
