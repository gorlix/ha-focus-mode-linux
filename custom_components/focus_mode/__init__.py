"""The Focus Mode integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOST, CONF_TOKEN, DOMAIN

from .api import FocusModeApiClient
from .coordinator import FocusModeCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Focus Mode from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data.get(CONF_HOST, "")
    token = entry.data.get(CONF_TOKEN, "")

    # Strict Async Requirement: Using `async_get_clientsession` across the component to talk to aiohttp.
    session = async_get_clientsession(hass)

    # Architectural execution: Instantiate the API Client with raw credentials, then inject
    # it into the DataUpdateCoordinator. This cleanly decouples HTTP logic from HA polling logic.
    client = FocusModeApiClient(host=host, token=token, session=session)
    coordinator = FocusModeCoordinator(hass, client=client)

    # We await the very first refresh during setup. If the backend is currently down
    # (raising an UpdateFailed), Home Assistant will cleanly abort the setup and move
    # the integration into a `Retrying Setup` state, rather than booting with broken entities.
    await coordinator.async_config_entry_first_refresh()

    # Store the initialized coordinator globally so platforms (switch.py, sensor.py) can access it.
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
