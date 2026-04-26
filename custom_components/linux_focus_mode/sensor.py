"""Sensor platform for the Linux Focus Mode integration."""

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

_DEVICE_INFO_BASE = {
    "manufacturer": "Linux Focus Mode",
    "model": "Focus Mode Daemon",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all sensors from the config entry."""
    coordinator: FocusModeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FocusModeBlockedCountSensor(coordinator, entry),
            FocusModeLockRemainingSensor(coordinator, entry),
        ]
    )


class _FocusModeBaseSensorEntity(CoordinatorEntity[FocusModeCoordinator], SensorEntity):
    """Common base for Linux Focus Mode sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = {
            **_DEVICE_INFO_BASE,
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Linux Focus Mode",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.available


class FocusModeBlockedCountSensor(_FocusModeBaseSensorEntity):
    """Number of currently configured blocked items (apps + webapps)."""

    _attr_translation_key = "blocked_count"
    _attr_icon = "mdi:format-list-bulleted"

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_blocked_count"

    @property
    def native_value(self) -> int | None:
        if not self.coordinator.data:
            return None
        return len(self.coordinator.data.get("blocked_items", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        return {"blocked_items": self.coordinator.data.get("blocked_items", [])}


class FocusModeLockRemainingSensor(_FocusModeBaseSensorEntity):
    """Human-readable remaining time for the active lock, or '—' when none."""

    _attr_translation_key = "lock_remaining"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_lock_remaining"

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "—"
        lock = self.coordinator.data.get("focus_lock", {})
        return lock.get("remaining_time") or "—"
