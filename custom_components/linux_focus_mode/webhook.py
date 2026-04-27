"""Webhook listener for push events from the Linux Focus Mode daemon."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiohttp.web import Request
from homeassistant.components.webhook import (
    async_register,
    async_unregister,
)
from homeassistant.core import HomeAssistant

if TYPE_CHECKING:
    from .coordinator import FocusModeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_register_webhook(
    hass: HomeAssistant,
    coordinator: FocusModeCoordinator,
    webhook_id: str,
) -> None:
    """Register the HA webhook that receives push events from the daemon.

    Both state_event_url and dying_gasp_url in the Linux app should point to
    the same URL — this handler distinguishes them via the event field.

    Accepted payload shapes:
    - Native app: {"type": "update_sensor_states", "data": [...]}
    - Legacy:     {"event": "focus_toggled", "active": true}
    - Dying gasp: {"event": "dying_gasp", "status": "offline"}
    """

    async def _handle_webhook(
        hass: HomeAssistant, webhook_id: str, request: Request
    ) -> None:
        try:
            data = await request.json()
        except Exception:
            _LOGGER.warning("Received malformed webhook payload (not valid JSON)")
            return

        _LOGGER.debug("Webhook received: %s", data)

        event = data.get("event", "")

        if event == "dying_gasp":
            coordinator.set_unavailable()
        else:
            coordinator.update_from_webhook(data)

    async_register(
        hass,
        domain="linux_focus_mode",
        name="Linux Focus Mode events",
        webhook_id=webhook_id,
        handler=_handle_webhook,
    )
    _LOGGER.debug("Webhook registered: %s", webhook_id)


def async_unregister_webhook(hass: HomeAssistant, webhook_id: str) -> None:
    """Unregister the webhook on integration unload."""
    async_unregister(hass, webhook_id)
    _LOGGER.debug("Webhook unregistered: %s", webhook_id)
