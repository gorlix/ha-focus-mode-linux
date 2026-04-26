"""Switch platform for the Focus Mode integration.

This module provides a toggleable entity within Home Assistant, allowing the user
to turn Focus Mode blocking on and off. It is deeply integrated with the
`FocusModeCoordinator` for immediate UI feedback.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
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
    """Set up the Focus Mode switch platform from a ConfigEntry.

    This function is dynamically loaded by Home Assistant during the integration boot sequence.

    Args:
        hass: The core instance.
        entry: The configuration entry holding our instantiated coordinator in `hass.data`.
        async_add_entities: A callback to register our initialized entities.
    """
    coordinator: FocusModeCoordinator = hass.data[DOMAIN][entry.entry_id]

    # We pass the coordinator to the entity so it knows where to get its state
    # and when to re-render in the UI.
    async_add_entities([FocusModeSwitch(coordinator, entry)])


class FocusModeSwitch(CoordinatorEntity[FocusModeCoordinator], SwitchEntity):
    """Representation of the Focus Mode toggle switch.

    Inheriting from `CoordinatorEntity` ensures that this entity's `self.data` is automatically
    updated whenever the coordinator completes a polling cycle, and that `self.async_write_ha_state()`
    is called to refresh the UI immediately.
    """

    _attr_has_entity_name = True
    _attr_name = "Blocker"
    _attr_icon = "mdi:shield-lock"  # Intuitive visual indicator for a blocking service.
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        """Initialize the Focus Mode switch.

        Args:
            coordinator: The central data manager.
            entry: The config entry this entity belongs to. We use its ID for uniqueness.
        """
        super().__init__(coordinator)

        # A stable, unique ID is mandatory for Home Assistant to track UI customizations,
        # history, and assignments to areas.
        self._attr_unique_id = f"{entry.entry_id}_switch"

        # We group this entity under a device representing the whole Focus Mode service.
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Focus Mode Server",
            "manufacturer": "Focus Mode",
            "model": "Local API Backend",
        }

    @property
    def is_on(self) -> bool:
        """Return True if the entity is on.

        The coordinator stores the raw JSON dictionary in `self.coordinator.data`.
        We dynamically derive our state from the `active` boolean in that payload.
        """
        if self.coordinator.data is None:
            return False
        return bool(self.coordinator.data.get("active", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the Focus Mode blocker on.

        This method triggers an immediate POST to the backend. Because we want the UI
        to reflect the change instantly (rather than waiting 30 seconds for the next poll),
        we explicitly request a data refresh right after the API call succeeds.
        """
        try:
            await self.coordinator.client.async_toggle_blocker(True)
            # Architectural Choice: Awaiting a forced refresh guarantees that all entities
            # (including the sensor) sync their attributes (like `blocked_items`) immediately
            # with the backend's new state.
            await self.coordinator.async_request_refresh()
        except Exception as err:
            # We catch generic errors here to log them; Home Assistant handles
            # marking the entity as unavailable if the coordinator refresh fails.
            _LOGGER.error("Failed to turn on Focus Mode: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the Focus Mode blocker off."""
        try:
            await self.coordinator.client.async_toggle_blocker(False)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off Focus Mode: %s", err)
