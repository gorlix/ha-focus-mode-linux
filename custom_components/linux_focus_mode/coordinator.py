"""Data coordinator for the Linux Focus Mode integration.

State arrives exclusively via push webhooks from the Linux app.
There is no polling: update_interval=None.

Flow:
  Linux app state change
    → POST /api/webhook/<webhook_id>  (native app update_sensor_states)
    → webhook.py calls coordinator.async_set_updated_data(parsed_state)
    → all subscribed entities re-render

  dying_gasp webhook
    → webhook.py calls coordinator.set_unavailable()
    → entities show unavailable until next push
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_EMPTY_STATE: dict[str, Any] = {
    "active": False,
    "restore_enabled": True,
    "blocked_items": [],
    "focus_lock": {"locked": False, "remaining_time": None, "target_time": None},
}


class FocusModeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Event-driven coordinator — no polling, state comes from webhooks."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=None,   # no polling
        )
        self.available: bool = False

    def update_from_webhook(self, data: dict[str, Any]) -> None:
        """Update state from a push webhook payload and notify entities.

        Called by webhook.py when the Linux app pushes a state update.
        Accepts both the native app sensor format and the legacy event format.
        """
        parsed = _parse_webhook_payload(data, self.data or dict(_EMPTY_STATE))
        self.available = True
        self.async_set_updated_data(parsed)

    def set_unavailable(self) -> None:
        """Mark the daemon offline (dying_gasp) and notify all entities."""
        self.available = False
        self.async_set_updated_data(self.data or dict(_EMPTY_STATE))


def _parse_webhook_payload(
    payload: dict[str, Any], current: dict[str, Any]
) -> dict[str, Any]:
    """Convert a webhook payload to coordinator data format.

    Supports two payload shapes:
    1. Native app:  {"type": "update_sensor_states", "data": [...]}
    2. Legacy event: {"event": "focus_toggled", "active": true}
    """
    data = dict(current)
    data["focus_lock"] = dict(current.get("focus_lock", {}))

    payload_type = payload.get("type")

    if payload_type == "update_sensor_states":
        for sensor in payload.get("data", []):
            uid = sensor.get("unique_id", "")
            state = sensor.get("state")
            _apply_sensor(data, uid, state)
        return data

    # Legacy event format
    event = payload.get("event", "")
    if event == "focus_toggled":
        data["active"] = bool(payload.get("active", data.get("active")))
    elif event == "restore_changed":
        data["restore_enabled"] = bool(payload.get("enabled", data.get("restore_enabled")))
    elif event in ("lock_activated", "lock_cancelled"):
        # Delegate to a full refresh — we don't have enough info here.
        # The app should follow up with an update_sensor_states push.
        pass

    return data


def _apply_sensor(data: dict[str, Any], uid: str, state: Any) -> None:
    if uid == "focus_active":
        data["active"] = bool(state)
    elif uid == "restore_enabled":
        data["restore_enabled"] = bool(state)
    elif uid == "focus_locked":
        data["focus_lock"]["locked"] = bool(state)
    elif uid == "ha_lock_active":
        if bool(state):
            data["focus_lock"]["locked"] = True
            data["focus_lock"]["remaining_time"] = None
    elif uid == "lock_remaining":
        data["focus_lock"]["remaining_time"] = state if state and state != "—" else None
    elif uid == "blocked_count":
        pass  # count only; blocked_items list not available via native app sensors
