"""Binary sensor platform for the Linux Focus Mode integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FocusModeCoordinator

_DEVICE_INFO_BASE = {
    "manufacturer": "Linux Focus Mode",
    "model": "Focus Mode Daemon",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all binary sensors from the config entry."""
    coordinator: FocusModeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FocusModeLockedBinarySensor(coordinator, entry),
            FocusModeAvailableBinarySensor(coordinator, entry),
        ]
    )


class _FocusModeBaseBinarySensorEntity(
    CoordinatorEntity[FocusModeCoordinator], BinarySensorEntity
):
    """Common base for Linux Focus Mode binary sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = {
            **_DEVICE_INFO_BASE,
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Linux Focus Mode",
        }


class FocusModeLockedBinarySensor(_FocusModeBaseBinarySensorEntity):
    """True when any focus lock (timer, target, or HA) is active."""

    _attr_translation_key = "locked"
    _attr_icon = "mdi:lock-outline"

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_locked"

    @property
    def available(self) -> bool:
        return self.coordinator.available

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("focus_lock", {}).get("locked", False))


class FocusModeAvailableBinarySensor(_FocusModeBaseBinarySensorEntity):
    """True when the Linux app is reachable and the last poll succeeded."""

    _attr_translation_key = "app_online"
    _attr_icon = "mdi:desktop-classic"

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_app_online"

    @property
    def available(self) -> bool:
        # This sensor is always "available" in HA; its is_on value carries the meaning.
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.available
