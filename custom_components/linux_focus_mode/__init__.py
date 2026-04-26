"""The Linux Focus Mode integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FocusModeApiCommunicationError, FocusModeApiError
from .config_flow import CONF_WEBHOOK_ID
from .const import CONF_HOST, CONF_PORT, CONF_TOKEN, DOMAIN
from .coordinator import FocusModeCoordinator
from .api import FocusModeApiClient
from .webhook import async_register_webhook, async_unregister_webhook

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Linux Focus Mode from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    client = FocusModeApiClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        token=entry.data[CONF_TOKEN],
        session=session,
    )
    coordinator = FocusModeCoordinator(hass, client=client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register webhook for push events from the daemon.
    webhook_id = entry.data.get(CONF_WEBHOOK_ID, "")
    if webhook_id:
        await async_register_webhook(hass, coordinator, webhook_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass, coordinator)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    webhook_id = entry.data.get(CONF_WEBHOOK_ID, "")
    if webhook_id:
        async_unregister_webhook(hass, webhook_id)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    # Remove services when the last entry is unloaded.
    if not hass.data[DOMAIN]:
        for service in (
            "focus_on", "focus_off",
            "lock_timer", "lock_target", "lock_ha", "unlock",
            "restore_on", "restore_off",
        ):
            hass.services.async_remove(DOMAIN, service)

    return unload_ok


def _register_services(hass: HomeAssistant, coordinator: FocusModeCoordinator) -> None:
    """Register all 8 control services (idempotent — safe to call multiple times)."""

    async def _call(coro_factory, call: ServiceCall) -> None:  # noqa: ANN001
        try:
            await coro_factory()
            await coordinator.async_request_refresh()
        except (FocusModeApiCommunicationError, FocusModeApiError) as err:
            raise HomeAssistantError(str(err)) from err

    async def svc_focus_on(call: ServiceCall) -> None:
        await _call(lambda: coordinator.client.async_toggle_blocker(True), call)

    async def svc_focus_off(call: ServiceCall) -> None:
        await _call(lambda: coordinator.client.async_toggle_blocker(False), call)

    async def svc_lock_timer(call: ServiceCall) -> None:
        minutes: int = call.data["minutes"]
        await _call(lambda: coordinator.client.async_lock_timer(minutes), call)

    async def svc_lock_target(call: ServiceCall) -> None:
        hour: int = call.data["hour"]
        minute: int = call.data["minute"]
        await _call(lambda: coordinator.client.async_lock_target(hour, minute), call)

    async def svc_lock_ha(call: ServiceCall) -> None:
        await _call(lambda: coordinator.client.async_lock_ha(), call)

    async def svc_unlock(call: ServiceCall) -> None:
        await _call(lambda: coordinator.client.async_unlock(), call)

    async def svc_restore_on(call: ServiceCall) -> None:
        await _call(lambda: coordinator.client.async_toggle_restore(True), call)

    async def svc_restore_off(call: ServiceCall) -> None:
        await _call(lambda: coordinator.client.async_toggle_restore(False), call)

    hass.services.async_register(DOMAIN, "focus_on", svc_focus_on)
    hass.services.async_register(DOMAIN, "focus_off", svc_focus_off)
    hass.services.async_register(
        DOMAIN, "lock_timer", svc_lock_timer,
        schema=vol.Schema({vol.Required("minutes"): vol.All(cv.positive_int)}),
    )
    hass.services.async_register(
        DOMAIN, "lock_target", svc_lock_target,
        schema=vol.Schema({
            vol.Required("hour"): vol.All(int, vol.Range(min=0, max=23)),
            vol.Required("minute"): vol.All(int, vol.Range(min=0, max=59)),
        }),
    )
    hass.services.async_register(DOMAIN, "lock_ha", svc_lock_ha)
    hass.services.async_register(DOMAIN, "unlock", svc_unlock)
    hass.services.async_register(DOMAIN, "restore_on", svc_restore_on)
    hass.services.async_register(DOMAIN, "restore_off", svc_restore_off)
