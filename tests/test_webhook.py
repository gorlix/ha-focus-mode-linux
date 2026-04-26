"""Tests for the webhook handler."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator
from custom_components.linux_focus_mode.webhook import async_register_webhook

from .conftest import mock_client


async def _make_coordinator(hass: HomeAssistant, mock_client: AsyncMock) -> FocusModeCoordinator:
    coordinator = FocusModeCoordinator(hass, client=mock_client)
    await coordinator.async_refresh()
    return coordinator


async def test_webhook_state_event_triggers_refresh(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """Any non-dying-gasp event triggers coordinator refresh."""
    coordinator = await _make_coordinator(hass, mock_client)
    coordinator.async_request_refresh = AsyncMock()

    with patch("custom_components.linux_focus_mode.webhook.async_register") as mock_reg:
        await async_register_webhook(hass, coordinator, "test_webhook_id")
        handler = mock_reg.call_args[1]["handler"]

    request = AsyncMock()
    request.json.return_value = {"event": "focus_toggled", "active": True}
    await handler(hass, "test_webhook_id", request)
    coordinator.async_request_refresh.assert_awaited_once()


async def test_webhook_dying_gasp_sets_unavailable(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """dying_gasp event calls set_unavailable immediately."""
    coordinator = await _make_coordinator(hass, mock_client)
    coordinator.set_unavailable = MagicMock()
    coordinator.async_request_refresh = AsyncMock()

    with patch("custom_components.linux_focus_mode.webhook.async_register") as mock_reg:
        await async_register_webhook(hass, coordinator, "test_webhook_id")
        handler = mock_reg.call_args[1]["handler"]

    request = AsyncMock()
    request.json.return_value = {"event": "dying_gasp", "status": "offline"}
    await handler(hass, "test_webhook_id", request)

    coordinator.set_unavailable.assert_called_once()
    coordinator.async_request_refresh.assert_not_awaited()


async def test_webhook_malformed_payload_no_crash(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """Malformed (non-JSON) webhook payload is silently ignored."""
    coordinator = await _make_coordinator(hass, mock_client)
    coordinator.async_request_refresh = AsyncMock()

    with patch("custom_components.linux_focus_mode.webhook.async_register") as mock_reg:
        await async_register_webhook(hass, coordinator, "test_webhook_id")
        handler = mock_reg.call_args[1]["handler"]

    request = AsyncMock()
    request.json.side_effect = ValueError("not json")
    await handler(hass, "test_webhook_id", request)

    coordinator.async_request_refresh.assert_not_awaited()
