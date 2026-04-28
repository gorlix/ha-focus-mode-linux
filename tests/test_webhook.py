"""Tests for the webhook handler."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator
from custom_components.linux_focus_mode.webhook import async_register_webhook


def _make_coordinator(hass: HomeAssistant) -> FocusModeCoordinator:
    return FocusModeCoordinator(hass)


async def _get_handler(hass, coordinator):
    with patch("custom_components.linux_focus_mode.webhook.async_register") as mock_reg:
        await async_register_webhook(hass, coordinator, "test_webhook_id")
        return mock_reg.call_args[1]["handler"]


def _request(payload):
    req = MagicMock()
    req.json = AsyncMock(return_value=payload)
    return req


async def test_webhook_focus_event_calls_update_from_webhook(
    hass: HomeAssistant,
) -> None:
    """Non-dying-gasp event triggers coordinator.update_from_webhook."""
    coordinator = _make_coordinator(hass)
    coordinator.update_from_webhook = MagicMock()
    handler = await _get_handler(hass, coordinator)

    payload = {"event": "focus_toggled", "active": True}
    await handler(hass, "test_webhook_id", _request(payload))

    coordinator.update_from_webhook.assert_called_once_with(payload)


async def test_webhook_native_app_format_calls_update_from_webhook(
    hass: HomeAssistant,
) -> None:
    """Native app update_sensor_states payload triggers update_from_webhook."""
    coordinator = _make_coordinator(hass)
    coordinator.update_from_webhook = MagicMock()
    handler = await _get_handler(hass, coordinator)

    payload = {
        "type": "update_sensor_states",
        "data": [{"unique_id": "focus_active", "state": True, "type": "binary_sensor"}],
    }
    await handler(hass, "test_webhook_id", _request(payload))

    coordinator.update_from_webhook.assert_called_once_with(payload)


async def test_webhook_dying_gasp_sets_unavailable(hass: HomeAssistant) -> None:
    """dying_gasp event calls set_unavailable, not update_from_webhook."""
    coordinator = _make_coordinator(hass)
    coordinator.set_unavailable = MagicMock()
    coordinator.update_from_webhook = MagicMock()
    handler = await _get_handler(hass, coordinator)

    await handler(
        hass, "test_webhook_id", _request({"event": "dying_gasp", "status": "offline"})
    )

    coordinator.set_unavailable.assert_called_once()
    coordinator.update_from_webhook.assert_not_called()


async def test_webhook_malformed_payload_no_crash(hass: HomeAssistant) -> None:
    """Malformed (non-JSON) webhook payload is silently ignored."""
    coordinator = _make_coordinator(hass)
    coordinator.update_from_webhook = MagicMock()
    handler = await _get_handler(hass, coordinator)

    req = MagicMock()
    req.json = AsyncMock(side_effect=ValueError("not json"))
    await handler(hass, "test_webhook_id", req)

    coordinator.update_from_webhook.assert_not_called()
