"""Sensor platform for the Focus Mode integration.

This module provides a read-only entity that displays secondary statistics from the backend,
specifically the count of blocked items and detailed JSON attributes for automation use cases.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FocusModeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Focus Mode sensor platform from a ConfigEntry."""
    coordinator: FocusModeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FocusModeSensor(coordinator, entry)])


class FocusModeSensor(CoordinatorEntity[FocusModeCoordinator], SensorEntity):
    """Representation of the Focus Mode statistics sensor.

    This entity's primary state is an integer (the count of blocked items).
    However, its real power lies in the `extra_state_attributes`, which expose complex
    nested data models for advanced Jinja2 templating or Node-RED logic.
    """

    _attr_has_entity_name = True
    _attr_name = "Blocked Items"
    _attr_icon = "mdi:format-list-bulleted"

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        """Initialize the Focus Mode statistics sensor."""
        super().__init__(coordinator)

        # Suffixing the entry ID prevents collisions with the switch entity.
        self._attr_unique_id = f"{entry.entry_id}_blocked_items"

        # Tie this sensor to the exact same device as the switch in the UI.
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Focus Mode Server",
            "manufacturer": "Focus Mode",
            "model": "Local API Backend",
        }

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor.

        Architectural Choice: Home Assistant states must be strings under the hood,
        and have a 255-character limit. We expose the *length* of the list as the
        primary state, because shoving a massive JSON array into the main state
        would truncate and break database history limits.
        """
        if self.coordinator.data is None:
            return None

        blocked_items = self.coordinator.data.get("blocked_items", [])
        return len(blocked_items)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return raw nested dictionaries as state attributes.

        These attributes bypass the 255-character limit of the primary state and
        are exposed to the HA event bus. Users can write automations like:
        `{{ state_attr('sensor.focus_mode_blocked_items', 'focus_lock').enabled }}`
        """
        if self.coordinator.data is None:
            return {}

        return {
            "blocked_items": self.coordinator.data.get("blocked_items", []),
            "focus_lock": self.coordinator.data.get("focus_lock", {}),
        }
