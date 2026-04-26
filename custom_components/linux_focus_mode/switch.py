"""Switch platform for the Linux Focus Mode integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
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
    """Set up all switches from the config entry."""
    coordinator: FocusModeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FocusModeActiveSwitch(coordinator, entry),
            FocusModeHaLockSwitch(coordinator, entry),
            FocusModeRestoreSwitch(coordinator, entry),
        ]
    )


class _FocusModeBaseSwitchEntity(CoordinatorEntity[FocusModeCoordinator], SwitchEntity):
    """Common base for all Linux Focus Mode switches."""

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


class FocusModeActiveSwitch(_FocusModeBaseSwitchEntity):
    """Toggle the process blocker (Focus Mode Active)."""

    _attr_translation_key = "active"
    _attr_icon = "mdi:shield-lock"

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_active"

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("active", False))

    def _ha_lock_active(self) -> bool:
        if not self.coordinator.data:
            return False
        lock = self.coordinator.data.get("focus_lock", {})
        return bool(lock.get("locked")) and lock.get("remaining_time") is None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_toggle_blocker(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self._ha_lock_active():
            raise HomeAssistantError(
                "Cannot disable Focus Mode while HA Lock is active"
            )
        await self.coordinator.client.async_toggle_blocker(False)
        await self.coordinator.async_request_refresh()


class FocusModeHaLockSwitch(_FocusModeBaseSwitchEntity):
    """Indefinite HA lock — only removable via DELETE /api/lock."""

    _attr_translation_key = "ha_lock"
    _attr_icon = "mdi:lock"

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ha_lock"

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data:
            return False
        lock = self.coordinator.data.get("focus_lock", {})
        return bool(lock.get("locked")) and lock.get("remaining_time") is None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_lock_ha()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_unlock()
        await self.coordinator.async_request_refresh()


class FocusModeRestoreSwitch(_FocusModeBaseSwitchEntity):
    """Auto-Restore — relaunch blocked apps when blocking ends."""

    _attr_translation_key = "restore"
    _attr_icon = "mdi:restore"

    def __init__(self, coordinator: FocusModeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_restore"

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("restore_enabled", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_toggle_restore(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_toggle_restore(False)
        await self.coordinator.async_request_refresh()
