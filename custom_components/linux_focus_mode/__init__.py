"""The Linux Focus Mode integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import CONF_WEBHOOK_ID, DOMAIN
from .coordinator import FocusModeCoordinator
from .webhook import async_register_webhook, async_unregister_webhook

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]

_LOGGER = logging.getLogger(__name__)

_EVENT = "linux_focus_mode_command"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Linux Focus Mode from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = FocusModeCoordinator(hass)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    webhook_id = entry.data[CONF_WEBHOOK_ID]
    await async_register_webhook(hass, coordinator, webhook_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    webhook_id = entry.data.get(CONF_WEBHOOK_ID, "")
    if webhook_id:
        async_unregister_webhook(hass, webhook_id)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    if not hass.data[DOMAIN]:
        for service in (
            "focus_on",
            "focus_off",
            "lock_timer",
            "lock_target",
            "lock_ha",
            "unlock",
            "restore_on",
            "restore_off",
        ):
            hass.services.async_remove(DOMAIN, service)

    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    """Register all 8 control services (idempotent — safe to call multiple times)."""

    def _fire(action: str, **kwargs: object) -> None:
        hass.bus.async_fire(_EVENT, {"action": action, **kwargs})

    async def svc_focus_on(call: ServiceCall) -> None:
        _fire("focus_on")

    async def svc_focus_off(call: ServiceCall) -> None:
        _fire("focus_off")

    async def svc_lock_timer(call: ServiceCall) -> None:
        _fire("lock_timer", minutes=call.data["minutes"])

    async def svc_lock_target(call: ServiceCall) -> None:
        _fire("lock_target", hour=call.data["hour"], minute=call.data["minute"])

    async def svc_lock_ha(call: ServiceCall) -> None:
        _fire("lock_ha")

    async def svc_unlock(call: ServiceCall) -> None:
        _fire("unlock")

    async def svc_restore_on(call: ServiceCall) -> None:
        _fire("restore_on")

    async def svc_restore_off(call: ServiceCall) -> None:
        _fire("restore_off")

    hass.services.async_register(DOMAIN, "focus_on", svc_focus_on)
    hass.services.async_register(DOMAIN, "focus_off", svc_focus_off)
    hass.services.async_register(
        DOMAIN,
        "lock_timer",
        svc_lock_timer,
        schema=vol.Schema({vol.Required("minutes"): vol.All(cv.positive_int)}),
    )
    hass.services.async_register(
        DOMAIN,
        "lock_target",
        svc_lock_target,
        schema=vol.Schema(
            {
                vol.Required("hour"): vol.All(int, vol.Range(min=0, max=23)),
                vol.Required("minute"): vol.All(int, vol.Range(min=0, max=59)),
            }
        ),
    )
    hass.services.async_register(DOMAIN, "lock_ha", svc_lock_ha)
    hass.services.async_register(DOMAIN, "unlock", svc_unlock)
    hass.services.async_register(DOMAIN, "restore_on", svc_restore_on)
    hass.services.async_register(DOMAIN, "restore_off", svc_restore_off)
