"""Tests for the coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.linux_focus_mode.api import (
    FocusModeApiAuthenticationError,
    FocusModeApiCommunicationError,
)
from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator

from .conftest import MOCK_STATE, mock_client


async def test_coordinator_successful_poll(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """Successful poll sets available=True and stores data."""
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()

    assert coordinator.available is True
    assert coordinator.data == MOCK_STATE


async def test_coordinator_communication_error(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """Communication failure sets available=False and raises UpdateFailed."""
    from homeassistant.helpers.update_coordinator import UpdateFailed

    mock_client.async_get_state.side_effect = FocusModeApiCommunicationError("timeout")
    coordinator = FocusModeCoordinator(hass, client=mock_client)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator.available is False


async def test_coordinator_auth_error(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """Auth failure sets available=False."""
    from homeassistant.exceptions import ConfigEntryAuthFailed

    mock_client.async_get_state.side_effect = FocusModeApiAuthenticationError("bad token")
    coordinator = FocusModeCoordinator(hass, client=mock_client)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()

    assert coordinator.available is False


async def test_coordinator_set_unavailable(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """set_unavailable() marks available=False and pushes update to listeners."""
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    assert coordinator.available is True

    coordinator.set_unavailable()
    assert coordinator.available is False


async def test_coordinator_recovers_after_failure(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """After a failure, a successful poll sets available=True again."""
    from homeassistant.helpers.update_coordinator import UpdateFailed

    mock_client.async_get_state.side_effect = FocusModeApiCommunicationError("down")
    coordinator = FocusModeCoordinator(hass, client=mock_client)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    assert coordinator.available is False

    mock_client.async_get_state.side_effect = None
    mock_client.async_get_state.return_value = MOCK_STATE
    await coordinator._async_update_data()
    assert coordinator.available is True
